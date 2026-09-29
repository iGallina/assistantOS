from datetime import date, datetime, timedelta, timezone

from assistantos.models import Event, Item, Mark, Status
from assistantos.store import SCHEMA_VERSION, Store

BRT = timezone(timedelta(hours=-3))


def test_migrates_once(tmp_path):
    s = Store(tmp_path / "state" / "aos.db")
    assert s.version() == SCHEMA_VERSION
    s.close()
    assert Store(tmp_path / "state" / "aos.db").version() == SCHEMA_VERSION


def test_items_events_marks_roundtrip(tmp_path):
    s = Store(tmp_path / "aos.db")
    s.upsert_item(Item(id="wa:1", source="whatsapp", title="Kat"))
    s.upsert_item(Item(id="wa:1", source="whatsapp", title="Kat (COPA)", tag="copa"))
    assert s.item("wa:1").title == "Kat (COPA)"
    # 10:00 BRT (= 13:00 UTC) is later than 12:30 UTC, though "10:00-03:00" sorts first as raw text
    s.add_event(Event(item_id="wa:1", at=datetime(2026, 9, 29, 10, 0, tzinfo=BRT), direction="out", text="b"))
    s.add_event(Event(item_id="wa:1", at=datetime(2026, 9, 29, 12, 30, tzinfo=timezone.utc), direction="in", text="a"))
    assert [e.text for e in s.events("wa:1")] == ["a", "b"]
    m = Mark(item_id="wa:1", status=Status.AGUARDANDO, at=datetime.now(timezone.utc), who="Kat", until=date(2026, 10, 1))
    s.set_mark(m)
    assert s.mark("wa:1") == m
    assert s.item("nope") is None and s.mark("nope") is None


def test_log_run(tmp_path):
    s = Store(tmp_path / "aos.db")
    s.log_run("brief", "claude", "haiku", 9.9, True)
    assert s.db.execute("select job, ok from runs").fetchall() == [("brief", 1)]
