"""One pass of the loop as a LangGraph graph. Every node is plain code except `brief`: sweeps are code, the model
drafts. collect → reconcile → classify (Jev label, never a filter) → select (caps) → brief → surface (Fizzy)."""
from datetime import date, datetime
from typing import TypedDict
from zoneinfo import ZoneInfo

from langgraph.graph import END, StateGraph

from .backends import BackendError, QuotaExceeded
from .jev import social
from .models import Brief, Config, Status
from .reconcile import statuses
from .store import Store

OPEN = (Status.REABERTO, Status.VENCIDO, Status.ABERTO)  # also the brief order: reopened first
HISTORY = 15

PROMPT = """Você prepara um brief de decisão para {owner}. Leia a conversa e diga o que mudou, qual decisão {owner}
precisa tomar agora, 2 ou 3 opções (sem numerar: a lista já é numerada na tela), o próximo passo e um rascunho de resposta no tom de {owner}: cordial, direto,
sem emoji, sem enrolação. Não invente fatos que não estão na conversa.

Item: {title}
Status: {status}{mark}
Conversa (mais antiga primeiro; horário de {tz}):
{history}

Brief anterior: {previous}"""


class PassState(TypedDict, total=False):
    new_events: int
    statuses: dict[str, Status]
    to_brief: list[str]
    briefed: list[str]
    errors: list[str]
    surfaced: list[str]


def _prompt(store: Store, cfg: Config, item_id: str, st: Status) -> str:
    tz = ZoneInfo(cfg.owner.timezone)
    item, mark, prev = store.item(item_id), store.mark(item_id), store.brief(item_id)
    lines = [f"[{e.at.astimezone(tz):%d/%m %H:%M}] {cfg.owner.name if e.direction == 'out' else 'Contato'}: {e.text}"
             for e in store.events(item_id)[-HISTORY:]]
    mark_txt = f" (marcado '{mark.status}' em {mark.at.astimezone(tz):%d/%m %H:%M})" if mark else ""
    return PROMPT.format(owner=cfg.owner.name, title=item.title, status=st, mark=mark_txt, tz=cfg.owner.timezone,
                         history="\n".join(lines), previous=prev[0].model_dump_json() if prev else "nenhum")


def run_pass(store: Store, plugins: list, backend, jev, cfg: Config, today: date, surfaces: list = ()) -> PassState:
    def collect(s: PassState) -> PassState:
        new = 0
        for plugin, pcfg in plugins:
            key = f"cursor:{plugin.name}"
            since = store.get_meta(key)
            items, events = plugin.poll(pcfg, datetime.fromisoformat(since) if since else None)
            for i in items:
                store.upsert_item(i)
            new += sum(store.add_event(e) for e in events)
            if events:
                store.set_meta(key, max(e.at for e in events).isoformat())
        return {"new_events": new}

    def reconcile(s: PassState) -> PassState:
        return {"statuses": statuses(store, today)}

    def classify(s: PassState) -> PassState:
        if jev is None:
            return {}
        for item_id, st in s["statuses"].items():
            last_in = store.last_event(item_id, "in")
            lab = store.label(item_id)
            if st != Status.REABERTO or not last_in or (lab and lab[0] == last_in.at):
                continue
            mark = store.mark(item_id)
            new = [e.text for e in store.events(item_id) if e.direction == "in" and (not mark or e.at > mark.at)]
            store.set_label(item_id, last_in.at, jev.needs_owner("\n".join(new)))
        return {}

    def select(s: PassState) -> PassState:
        room = min(cfg.backend.per_pass_cap, cfg.backend.per_day_cap - store.runs_today("brief"))
        due = []
        for item_id, st in s["statuses"].items():
            last, last_in, prev, lab = (store.last_event(item_id), store.last_event(item_id, "in"),
                                        store.brief(item_id), store.label(item_id))
            if st not in OPEN or not last or (prev and prev[1] >= last.at):
                continue
            if last_in and lab and lab[0] == last_in.at and social(lab[1]):
                continue  # labelled small talk: stays visible, gets no brief
            due.append((OPEN.index(st), -last.at.timestamp(), item_id))
        return {"to_brief": [i for *_, i in sorted(due)][:max(room, 0)]}

    def brief(s: PassState) -> PassState:
        done, errors = [], []
        for item_id in s["to_brief"]:
            try:
                b = backend.ask(_prompt(store, cfg, item_id, s["statuses"][item_id]), Brief, "brief")
            except QuotaExceeded as e:
                errors.append(str(e))
                break  # the subscription is out for now: stop model calls for the rest of the pass
            except BackendError as e:
                errors.append(f"{item_id}: {e}")
                continue
            store.set_brief(item_id, b, store.last_event(item_id).at)
            done.append(item_id)
        return {"briefed": done, "errors": errors}

    def surface(s: PassState) -> PassState:
        return {"surfaced": [line for sf, scfg in surfaces for line in sf.sync(store, scfg, today, cfg.owner.language)]}

    g = StateGraph(PassState)
    steps = (("collect", collect), ("reconcile", reconcile), ("classify", classify), ("select", select),
             ("brief", brief), ("surface", surface))
    for name, fn in steps:
        g.add_node(name, fn)
    g.set_entry_point("collect")
    for (a, _), (b, _) in zip(steps, steps[1:]):
        g.add_edge(a, b)
    g.add_edge("surface", END)
    return g.compile().invoke({})
