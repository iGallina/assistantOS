"""WhatsApp through the wacli store, read-only. Scope is the owner's own list of chats (whatsapp.json): code decides
what is read, never a model. Audio shows as "[audio]" until transcription lands (step 3c).
Each pass first runs `wacli sync --once`, so the store is current without a daemon on any OS."""
import shutil
import sqlite3
import subprocess
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from pydantic import Field

from ..models import Event, Item, Strict


SYNC_TIMEOUT = 180


class WhatsAppConfig(Strict):
    store: str = "~/.wacli/wacli.db"
    chats: list[str]                     # the owner's open loops: chat ids to follow
    floor_days: int = Field(7, ge=1)     # first run and groups: never reach further back than this


class WhatsApp:
    name = "whatsapp"
    Config = WhatsAppConfig

    def _db(self, cfg: WhatsAppConfig) -> sqlite3.Connection:
        # a read-only URI: the plugin can never write the store wacli owns
        return sqlite3.connect(Path(cfg.store).expanduser().resolve().as_uri() + "?mode=ro", uri=True, timeout=10)

    def describe(self, cfg: WhatsAppConfig) -> str:
        return f"{len(cfg.chats)} chats"

    def check(self, cfg: WhatsAppConfig) -> str | None:
        if not cfg.chats:
            return None  # fresh install: nothing to read yet, nothing to check
        try:
            with closing(self._db(cfg)) as c:
                c.execute("SELECT 1 FROM messages LIMIT 1").fetchall()
        except sqlite3.Error as e:
            return f"wacli store {cfg.store}: {e}"
        return None

    def refresh(self, cfg: WhatsAppConfig, run=subprocess.run) -> str | None:
        """Pull new messages into the store; None = fine. A locked store means another wacli (a --follow daemon)
        already keeps it current. Any problem is reported and the pass still reads what the store has."""
        if not cfg.chats:
            return None
        exe = shutil.which("wacli")
        if not exe:
            return "wacli não encontrado: rode `aos setup`"
        try:
            r = run([exe, "sync", "--once", "--idle-exit", "15s", "--store", str(Path(cfg.store).expanduser().parent)],
                    capture_output=True, text=True, timeout=SYNC_TIMEOUT)
        except subprocess.TimeoutExpired:
            return f"wacli sync: sem resposta em {SYNC_TIMEOUT} s"
        if r.returncode == 0 or "store is locked" in r.stderr:
            return None
        return "wacli sync: " + ((r.stderr or r.stdout).strip().splitlines() or [f"exit {r.returncode}"])[-1]

    def poll(self, cfg: WhatsAppConfig, since: datetime | None) -> tuple[list[Item], list[Event]]:
        if not cfg.chats:
            return [], []
        start = max(time.time() - cfg.floor_days * 86400, since.timestamp() if since else 0)
        q = ",".join("?" * len(cfg.chats))
        with closing(self._db(cfg)) as c:
            names = dict(c.execute(f"SELECT jid, name FROM chats WHERE jid IN ({q})", cfg.chats))
            rows = c.execute(
                f"SELECT chat_jid, msg_id, ts, from_me, coalesce(media_type, ''), "
                f"coalesce(nullif(text, ''), media_caption, '') FROM messages "
                f"WHERE chat_jid IN ({q}) AND ts >= ? ORDER BY ts", (*cfg.chats, start)).fetchall()
        items = [Item(id=f"wa:{j}", source="whatsapp", title=names.get(j) or j) for j in cfg.chats]
        events = []
        for jid, mid, ts, me, kind, text in rows:
            text = text.strip() or (f"[{kind}]" if kind else "")
            if text:  # reactions and system rows carry no text
                events.append(Event(item_id=f"wa:{jid}", at=datetime.fromtimestamp(ts, timezone.utc),
                                    direction="out" if me else "in", text=text, ext_id=f"wa:{mid}"))
        return items, events
