"""Mirror open items to the owner's Fizzy board, both ways (AIS-OS scripts/fizzy-sync.py, 2026-09-26). Deterministic:
  open item without a card   → card created (tag = item tag)      item resolved here      → card closed
  card closed in Fizzy       → item feito                          item open again         → card reopened + comment
  card gone from every list  → item ignorado                       brief/title changed     → card updated
A card exists if it is open, closed or postponed — the CLI lists each separately (measured 2026-10-01: a postponed
card is in none of the other lists, and would otherwise look deleted). Cards made by hand are never touched."""
import hashlib
import json
import shutil
import subprocess
from datetime import date, datetime, timezone

from ..i18n import t
from ..models import Mark, Status, Strict
from ..reconcile import statuses
from ..store import Store

PREFIX = "assistantOS · "   # every comment the assistant writes starts with this
OPEN = {Status.ABERTO, Status.REABERTO, Status.DEPOIS, Status.AGUARDANDO, Status.VENCIDO}


class FizzyConfig(Strict):
    board: str = ""                          # board id; empty = not set up yet
    page_url: str = "http://127.0.0.1:8422"
    default_tag: str = "pessoal"


class FizzyError(Exception):
    pass


def fizzy_cli(*args):
    """The fizzy binary → parsed JSON. Credentials come from its own env (FIZZY_TOKEN, FIZZY_ACCOUNT)."""
    exe = shutil.which("fizzy")
    if not exe:
        raise FizzyError("fizzy CLI not installed")
    r = subprocess.run([exe, *map(str, args), "--quiet"], capture_output=True, text=True, encoding="utf-8", timeout=60)
    if r.returncode:
        raise FizzyError((r.stderr or r.stdout).strip()[:200])
    return json.loads(r.stdout, strict=False) if r.stdout.strip() else None


def _body(store: Store, item_id: str, st: Status, cfg: FizzyConfig, lang: str) -> str:
    b, m = store.brief(item_id), store.mark(item_id)
    parts = []
    if st in (Status.AGUARDANDO, Status.VENCIDO) and m and m.who:
        parts.append(f"**{t('fizzy.waiting', lang, who=m.who, until=m.until)}**"
                     + (f" — **{t('fizzy.overdue', lang)}**" if st == Status.VENCIDO else ""))
    if b:
        parts += [f"**{t('page.mudou', lang)}:** {b[0].mudou}", f"**{t('page.decisao', lang)}:** {b[0].decisao}",
                  f"**{t('page.proximo', lang)}:** {b[0].proximo_passo}"]
    parts.append(f"{cfg.page_url} · `{item_id}`")
    return "\n\n".join(parts)


def sync(store: Store, cfg: FizzyConfig, fz, today: date, lang: str = "pt-BR") -> list[str]:
    sts = statuses(store, today)
    if not sts or not cfg.board:
        return []   # an empty store must never close every card
    now = datetime.now(timezone.utc)
    log = []
    try:
        closed = {c["number"] for c in fz("board", "closed", "--board", cfg.board, "--all") or []}
        exists = closed | {c["number"] for c in fz("card", "list", "--board", cfg.board, "--all") or []} \
            | {c["number"] for c in fz("board", "postponed", "--board", cfg.board, "--all") or []}
    except FizzyError as e:
        return [f"fizzy: {e}"]
    rows = {r[0]: {"card": r[1], "closed": bool(r[2]), "hash": r[3]}
            for r in store.db.execute("SELECT item_id, card, closed, hash FROM cards")}

    def save(item_id, **kw):
        with store.db:
            store.db.execute(f"UPDATE cards SET {', '.join(k + '=?' for k in kw)}, at=? WHERE item_id=?",
                             (*kw.values(), now.isoformat(), item_id))

    for item_id, st in sts.items():
        item, row = store.item(item_id), rows.get(item_id)
        body = _body(store, item_id, st, cfg, lang)
        digest = hashlib.sha1((item.title + body).encode()).hexdigest()[:12]
        want = st in OPEN
        try:
            if row is None:
                if want:
                    card = fz("card", "create", "--board", cfg.board, "--title", item.title[:250],
                              "--description", body)["number"]
                    fz("card", "tag", card, "--tag", item.tag or cfg.default_tag)  # tag toggles: only on a new card
                    with store.db:
                        store.db.execute("INSERT INTO cards VALUES (?,?,?,?,?)", (item_id, card, 0, digest, now.isoformat()))
                    log.append(f"#{card} +{item.title[:40]}")
                continue
            card = row["card"]
            if card not in exists:                                   # the owner deleted it: not a task for them
                store.set_mark(Mark(item_id=item_id, status=Status.IGNORADO, at=now))
                with store.db:
                    store.db.execute("DELETE FROM cards WHERE item_id=?", (item_id,))
                log.append(f"#{card} → ignorado")
            elif not row["closed"] and card in closed:               # closed on the phone → done everywhere
                store.set_mark(Mark(item_id=item_id, status=Status.FEITO, at=now))
                save(item_id, closed=1)
                log.append(f"#{card} → feito")
            elif want and row["closed"]:
                fz("card", "reopen", card)
                b = store.brief(item_id)
                fz("comment", "create", "--card", card, "--body",
                   PREFIX + (t("fizzy.reopened", lang, mudou=b[0].mudou) if b else t("fizzy.reopened_generic", lang)))
                save(item_id, closed=0)
                log.append(f"#{card} reaberto")
            elif not want and not row["closed"]:
                fz("card", "close", card)
                save(item_id, closed=1)
                log.append(f"#{card} fechado")
            elif want and row["hash"] != digest:
                fz("card", "update", card, "--title", item.title[:250], "--description", body)
                save(item_id, hash=digest)
        except FizzyError as e:
            log.append(f"#{row['card'] if row else item_id}: {e}")
    return log


class Fizzy:
    """The surface as the loop and `aos doctor` see it."""
    name = "fizzy"
    Config = FizzyConfig

    def __init__(self, fz=fizzy_cli):
        self.fz = fz

    def describe(self, cfg: FizzyConfig) -> str:
        return f"board {cfg.board}" if cfg.board else "board —"

    def check(self, cfg: FizzyConfig) -> str | None:
        if not cfg.board:
            return None  # fresh install: not set up yet
        try:
            self.fz("board", "show", cfg.board)
        except FizzyError as e:
            return f"fizzy board {cfg.board}: {e}"
        return None

    def sync(self, store: Store, cfg: FizzyConfig, today: date, lang: str) -> list[str]:
        return sync(store, cfg, self.fz, today, lang)
