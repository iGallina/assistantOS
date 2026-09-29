"""SQLite state. Schema changes are appended to MIGRATIONS; PRAGMA user_version tracks what ran."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import Event, Item, Mark

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
]
SCHEMA_VERSION = len(MIGRATIONS)


def utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


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

    def add_event(self, e: Event) -> None:
        with self.db:
            self.db.execute("INSERT INTO events(item_id, at, direction, text) VALUES (?,?,?,?)",
                            (e.item_id, utc(e.at), e.direction, e.text))

    def events(self, item_id: str) -> list[Event]:
        rows = self.db.execute("SELECT item_id, at, direction, text FROM events WHERE item_id=? ORDER BY at",
                               (item_id,))
        return [Event(item_id=a, at=b, direction=c, text=d) for a, b, c, d in rows]

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
