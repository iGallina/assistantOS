from datetime import date, datetime, timedelta, timezone

from assistantos.models import Brief, Event, Item, Mark, Status
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


BRIEF = Brief(mudou="m", decisao="d", opcoes=["a"], proximo_passo="p", rascunho="r", urgencia="hoje")
T0 = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)


def test_ext_id_dedupes(tmp_path):
    s = Store(tmp_path / "aos.db")
    s.upsert_item(Item(id="wa:1", source="whatsapp", title="Kat"))
    e = Event(item_id="wa:1", at=T0, direction="in", text="oi", ext_id="wa:m1")
    assert s.add_event(e) is True and s.add_event(e) is False
    assert len(s.events("wa:1")) == 1


def test_last_event_brief_label_meta_runs(tmp_path):
    s = Store(tmp_path / "aos.db")
    s.upsert_item(Item(id="wa:1", source="whatsapp", title="Kat"))
    s.add_event(Event(item_id="wa:1", at=T0, direction="in", text="a"))
    s.add_event(Event(item_id="wa:1", at=T0 + timedelta(minutes=5), direction="out", text="b"))
    assert s.last_event("wa:1").text == "b" and s.last_event("wa:1", "in").text == "a"
    assert s.last_event("nope") is None
    s.set_brief("wa:1", BRIEF, T0)
    assert s.brief("wa:1") == (BRIEF, T0)
    s.set_label("wa:1", T0, 0.2)
    assert s.label("wa:1") == (T0, 0.2)
    s.set_meta("cursor:whatsapp", "x")
    assert s.get_meta("cursor:whatsapp") == "x" and s.get_meta("nope") is None
    s.log_run("brief", "claude", "haiku", 1.0, False)
    assert s.runs_today("brief") == 1 and s.runs_today("tag") == 0
    assert [i.id for i in s.items()] == ["wa:1"]


def test_v1_database_upgrades_with_its_data(tmp_path, monkeypatch):
    import assistantos.store as st
    monkeypatch.setattr(st, "MIGRATIONS", st.MIGRATIONS[:1])
    old = st.Store(tmp_path / "aos.db")
    old.upsert_item(Item(id="wa:1", source="whatsapp", title="Kat"))
    old.db.execute("INSERT INTO events(item_id, at, direction, text) VALUES ('wa:1', ?, 'in', 'antes')", (T0.isoformat(),))
    old.db.commit()
    old.close()
    monkeypatch.undo()
    s = Store(tmp_path / "aos.db")
    assert s.version() == SCHEMA_VERSION == 4
    assert [e.text for e in s.events("wa:1")] == ["antes"]


def test_requests_and_drafts(tmp_path):
    s = Store(tmp_path / "aos.db")
    s.upsert_item(Item(id="wa:1", source="whatsapp", title="Kat"))
    r1 = s.add_request("wa:1", "responde que sim", "page")
    r2 = s.add_request("wa:1", "e o prazo?", "page", parent=r1)
    assert [r["id"] for r in s.open_requests()] == [r1, r2]
    s.answer_request(r1, "answered", "Feito: novo rascunho.")
    assert [r["id"] for r in s.open_requests()] == [r2]
    assert s.request(r2)["parent"] == r1 and s.request(r1)["reply"] == "Feito: novo rascunho."
    assert [r["id"] for r in s.requests("wa:1")] == [r2, r1]          # newest first
    assert s.draft("wa:1") is None
    s.set_draft("wa:1", "Oi Kat, sim!")
    assert s.draft("wa:1") == "Oi Kat, sim!"
