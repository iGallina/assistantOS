"""WhatsApp through the wacli store, read-only. Scope is the owner's own list of chats (whatsapp.json): code decides
what is read, never a model. Audio shows as "[audio]" until transcription lands (step 3c)."""
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from pydantic import Field

from ..models import Event, Item, Strict


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

    def check(self, cfg: WhatsAppConfig) -> str | None:
        try:
            with closing(self._db(cfg)) as c:
                c.execute("SELECT 1 FROM messages LIMIT 1").fetchall()
        except sqlite3.Error as e:
            return f"wacli store {cfg.store}: {e}"
        return None

    def poll(self, cfg: WhatsAppConfig, since: datetime | None) -> tuple[list[Item], list[Event]]:
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
