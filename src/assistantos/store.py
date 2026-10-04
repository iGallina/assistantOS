"""SQLite state. Schema changes are appended to MIGRATIONS; PRAGMA user_version tracks what ran."""
import sqlite3
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .models import Brief, Event, Item, Mark

MIGRATIONS = [
    """
    CREATE TABLE items(id TEXT PRIMARY KEY, source TEXT NOT NULL, title TEXT NOT NULL, tag TEXT, link TEXT);
    CREATE TABLE events(id INTEGER PRIMARY KEY, item_id TEXT NOT NULL REFERENCES items(id),
                        at TEXT NOT NULL, direction TEXT NOT NULL, text TEXT NOT NULL);
    CREATE INDEX events_item_at ON events(item_id, at);
    CREATE TABLE marks(item_id TEXT PRIMARY KEY REFERENCES items(id), status TEXT NOT NULL,
                       at TEXT NOT NULL, who TEXT, until TEXT);
    CREATE TABLE runs(id INTEGER PRIMARY KEY, at TEXT NOT NULL, job TEXT NOT NULL, backend TEXT NOT NULL,
                      model TEXT, seconds REAL NOT NULL, ok INTEGER NOT NULL);
    """,
    """
    ALTER TABLE events ADD COLUMN ext_id TEXT;
    CREATE UNIQUE INDEX events_ext ON events(ext_id) WHERE ext_id IS NOT NULL;
    CREATE TABLE briefs(item_id TEXT PRIMARY KEY REFERENCES items(id), at TEXT NOT NULL,
                        event_at TEXT NOT NULL, body TEXT NOT NULL);
    CREATE TABLE labels(item_id TEXT PRIMARY KEY REFERENCES items(id), event_at TEXT NOT NULL, p REAL);
    CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    """,
    """
    CREATE TABLE cards(item_id TEXT PRIMARY KEY REFERENCES items(id), card INTEGER NOT NULL,
                       closed INTEGER NOT NULL, hash TEXT NOT NULL, at TEXT NOT NULL);
    """,
    """
    CREATE TABLE requests(id INTEGER PRIMARY KEY, item_id TEXT NOT NULL REFERENCES items(id), at TEXT NOT NULL,
                          ask TEXT NOT NULL, via TEXT NOT NULL, parent INTEGER REFERENCES requests(id),
                          state TEXT NOT NULL DEFAULT 'open', reply TEXT, tries INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE drafts(item_id TEXT PRIMARY KEY REFERENCES items(id), at TEXT NOT NULL, text TEXT NOT NULL);
    """,
]
SCHEMA_VERSION = len(MIGRATIONS)
REQUEST = ("id", "item_id", "at", "ask", "via", "parent", "state", "reply", "tries")  # state: open · answered · needs_session


def utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def local_day(day: date, tz: str) -> tuple[datetime, datetime]:
    """The owner's calendar day as a UTC [start, end) range — caps and the report count the same day."""
    start = datetime.combine(day, time(), ZoneInfo(tz))
    return start.astimezone(timezone.utc), (start + timedelta(days=1)).astimezone(timezone.utc)


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA foreign_keys = ON")
        v = self.version()
        for i, sql in enumerate(MIGRATIONS[v:], start=v + 1):
            self.db.executescript(f"BEGIN; {sql} PRAGMA user_version = {i}; COMMIT;")

    def version(self) -> int:
        return self.db.execute("PRAGMA user_version").fetchone()[0]

    def close(self) -> None:
        self.db.close()

    def upsert_item(self, i: Item) -> None:
        with self.db:
            self.db.execute(
                "INSERT INTO items VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                "source=excluded.source, title=excluded.title, tag=excluded.tag, link=excluded.link",
                (i.id, i.source, i.title, i.tag, i.link))

    def item(self, item_id: str) -> Item | None:
        r = self.db.execute("SELECT id, source, title, tag, link FROM items WHERE id=?", (item_id,)).fetchone()
        return Item(**dict(zip(("id", "source", "title", "tag", "link"), r))) if r else None

    def items(self) -> list[Item]:
        rows = self.db.execute("SELECT id, source, title, tag, link FROM items ORDER BY id")
        return [Item(**dict(zip(("id", "source", "title", "tag", "link"), r))) for r in rows]

    def add_event(self, e: Event) -> bool:
        """False when an event with the same ext_id is already stored."""
        with self.db:
            c = self.db.execute("INSERT OR IGNORE INTO events(item_id, at, direction, text, ext_id) VALUES (?,?,?,?,?)",
                                (e.item_id, utc(e.at), e.direction, e.text, e.ext_id))
        return c.rowcount == 1

    def events(self, item_id: str) -> list[Event]:
        rows = self.db.execute("SELECT item_id, at, direction, text, ext_id FROM events WHERE item_id=? ORDER BY at, id",
                               (item_id,))
        return [Event(item_id=a, at=b, direction=c, text=d, ext_id=x) for a, b, c, d, x in rows]

    def last_event(self, item_id: str, direction: str | None = None) -> Event | None:
        q = "SELECT item_id, at, direction, text, ext_id FROM events WHERE item_id=?"
        args: tuple = (item_id,)
        if direction:
            q, args = q + " AND direction=?", (item_id, direction)
        r = self.db.execute(q + " ORDER BY at DESC, id DESC LIMIT 1", args).fetchone()
        return Event(item_id=r[0], at=r[1], direction=r[2], text=r[3], ext_id=r[4]) if r else None

    def set_mark(self, m: Mark) -> None:
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO marks VALUES (?,?,?,?,?)",
                            (m.item_id, m.status.value, utc(m.at), m.who, m.until and m.until.isoformat()))

    def mark(self, item_id: str) -> Mark | None:
        r = self.db.execute("SELECT item_id, status, at, who, until FROM marks WHERE item_id=?", (item_id,)).fetchone()
        return Mark(**dict(zip(("item_id", "status", "at", "who", "until"), r))) if r else None

    def log_run(self, job: str, backend: str, model: str | None, seconds: float, ok: bool) -> None:
        with self.db:
            self.db.execute("INSERT INTO runs(at, job, backend, model, seconds, ok) VALUES (?,?,?,?,?,?)",
                            (utc(datetime.now(timezone.utc)), job, backend, model, seconds, int(ok)))

    def set_brief(self, item_id: str, brief: Brief, event_at: datetime) -> None:
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO briefs VALUES (?,?,?,?)",
                            (item_id, utc(datetime.now(timezone.utc)), utc(event_at), brief.model_dump_json()))

    def brief(self, item_id: str) -> tuple[Brief, datetime] | None:
        r = self.db.execute("SELECT body, event_at FROM briefs WHERE item_id=?", (item_id,)).fetchone()
        return (Brief.model_validate_json(r[0]), datetime.fromisoformat(r[1])) if r else None

    def set_label(self, item_id: str, event_at: datetime, p: float | None) -> None:
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO labels VALUES (?,?,?)", (item_id, utc(event_at), p))

    def label(self, item_id: str) -> tuple[datetime, float | None] | None:
        r = self.db.execute("SELECT event_at, p FROM labels WHERE item_id=?", (item_id,)).fetchone()
        return (datetime.fromisoformat(r[0]), r[1]) if r else None

    def get_meta(self, key: str) -> str | None:
        r = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return r[0] if r else None

    def set_meta(self, key: str, value: str) -> None:
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (key, value))

    def runs_between(self, start: datetime, end: datetime, job: str | None = None) -> list[tuple]:
        """(job, backend, model, seconds, ok) rows in [start, end). Stored as UTC ISO text, so text order is time order."""
        q, args = "SELECT job, backend, model, seconds, ok FROM runs WHERE at >= ? AND at < ?", (utc(start), utc(end))
        if job:
            q, args = q + " AND job=?", (*args, job)
        return self.db.execute(q + " ORDER BY id", args).fetchall()

    def add_request(self, item_id: str, ask: str, via: str, parent: int | None = None) -> int:
        with self.db:
            return self.db.execute("INSERT INTO requests(item_id, at, ask, via, parent) VALUES (?,?,?,?,?)",
                                   (item_id, utc(datetime.now(timezone.utc)), ask, via, parent)).lastrowid

    def _requests(self, where: str, args: tuple) -> list[dict]:
        return [dict(zip(REQUEST, r)) for r in self.db.execute(f"SELECT {', '.join(REQUEST)} FROM requests {where}", args)]

    def request(self, rid: int) -> dict | None:
        return next(iter(self._requests("WHERE id=?", (rid,))), None)

    def requests(self, item_id: str) -> list[dict]:
        return self._requests("WHERE item_id=? ORDER BY id DESC", (item_id,))

    def open_requests(self) -> list[dict]:
        return self._requests("WHERE state='open' ORDER BY id", ())

    def answer_request(self, rid: int, state: str, reply: str) -> None:
        with self.db:
            self.db.execute("UPDATE requests SET state=?, reply=? WHERE id=?", (state, reply, rid))

    def fail_request(self, rid: int) -> int:
        """Counts one failed attempt; returns the attempts so far."""
        with self.db:
            self.db.execute("UPDATE requests SET tries=tries+1 WHERE id=?", (rid,))
        return self.request(rid)["tries"]

    def set_draft(self, item_id: str, text: str) -> None:
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO drafts VALUES (?,?,?)", (item_id, utc(datetime.now(timezone.utc)), text))

    def draft(self, item_id: str) -> str | None:
        r = self.db.execute("SELECT text FROM drafts WHERE item_id=?", (item_id,)).fetchone()
        return r[0] if r else None
