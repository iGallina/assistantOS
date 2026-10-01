"""What the page shows, built from the store. Pure: no HTTP, no clock (today is passed in)."""
from datetime import date, datetime

from ..jev import social
from ..models import Status
from ..reconcile import statuses
from ..store import Store

SECTIONS = ("decidir", "abertos", "aguardando", "depois", "resolvidos")


def _section(st: Status, brief_current: bool) -> str:
    if st in (Status.REABERTO, Status.VENCIDO) or (st == Status.ABERTO and brief_current):
        return "decidir"
    return {Status.ABERTO: "abertos", Status.AGUARDANDO: "aguardando", Status.DEPOIS: "depois"}.get(st, "resolvidos")


def build_state(store: Store, today: date) -> dict:
    items = []
    for item, st in ((store.item(i), s) for i, s in statuses(store, today).items()):
        last, last_in = store.last_event(item.id), store.last_event(item.id, "in")
        brief, lab, mark = store.brief(item.id), store.label(item.id), store.mark(item.id)
        current = bool(brief and last and brief[1] >= last.at)
        jid = item.id.removeprefix("wa:")
        items.append({
            "id": item.id, "title": item.title, "source": item.source, "status": st.value,
            "section": _section(st, current),
            "last": last and {"at": last.at.isoformat(), "direction": last.direction, "text": last.text},
            "brief": brief[0].model_dump() if brief else None, "brief_current": current,
            "social": bool(lab and last_in and lab[0] == last_in.at and social(lab[1])),
            "mark": {"who": mark.who, "until": mark.until and mark.until.isoformat()} if mark else None,
            "wa": jid.split("@")[0] if jid.endswith("@s.whatsapp.net") else None,
        })
    newest = lambda i: -datetime.fromisoformat(i["last"]["at"]).timestamp() if i["last"] else 0  # noqa: E731
    items.sort(key=lambda i: (SECTIONS.index(i["section"]), newest(i)))
    return {"items": items, "counts": {s: sum(i["section"] == s for i in items) for s in SECTIONS}}
