from datetime import date, datetime, timedelta, timezone

from assistantos.models import Backend, Brief, Config, Contacts, Event, Item, Owner, Tags
from assistantos.report import build_report, write_report
from assistantos.store import Store

TODAY = date(2026, 9, 30)
T0 = datetime(2026, 9, 30, 15, tzinfo=timezone.utc)          # 12:00 in São Paulo
BRIEF = Brief(mudou="m", decisao="Aceitar o prazo?", opcoes=["a"], proximo_passo="confirmar sexta", rascunho="r",
              urgencia="hoje")


def cfg():
    return Config(owner=Owner(name="Ana"), backend=Backend(kind="claude", per_day_cap=60), contacts=Contacts(),
                  tags=Tags(order=["pessoal"]))


def seed(tmp_path):
    s = Store(tmp_path / "aos.db")
    for k, title in enumerate(["Kat", "<b>Zé</b>"]):
        s.upsert_item(Item(id=f"i{k}", source="whatsapp", title=title))
    s.add_event(Event(item_id="i0", at=T0 - timedelta(days=1), direction="in", text="ontem"))
    s.add_event(Event(item_id="i0", at=T0, direction="in", text="entrega sexta?"))
    s.add_event(Event(item_id="i0", at=T0 + timedelta(minutes=1), direction="in", text="<script>x</script>"))
    s.add_event(Event(item_id="i1", at=T0 - timedelta(days=1), direction="in", text="velho"))
    s.set_brief("i0", BRIEF, T0 + timedelta(minutes=1))
    r1 = s.add_request("i0", "anexa o PDF", "page")
    s.answer_request(r1, "needs_session", "Precisa de sessão: achar o PDF")
    s.add_request("i1", "resume", "page")
    for at, job, ok in ((T0, "brief", 1), (T0, "brief", 0), (T0, "request", 1), (T0 - timedelta(days=1), "brief", 1)):
        s.db.execute("INSERT INTO runs(at, job, backend, model, seconds, ok) VALUES (?,?,?,?,?,?)",
                     (at.isoformat(), job, "claude", "haiku", 10.0, ok))
    s.db.commit()
    return s


def test_build_report(tmp_path):
    r = build_report(seed(tmp_path), cfg(), TODAY)
    assert [(c["title"], c["n"]) for c in r["came_in"]] == [("Kat", 2)]
    assert [d["title"] for d in r["decide"]] == ["Kat"] and r["decide"][0]["decisao"] == "Aceitar o prazo?"
    assert [q["ask"] for q in r["requests"]] == ["resume", "anexa o PDF"]
    assert r["spend"] == [{"job": "brief", "backend": "claude", "calls": 2, "failed": 1, "seconds": 20.0},
                          {"job": "request", "backend": "claude", "calls": 1, "failed": 0, "seconds": 10.0}]
    assert r["brief_cap"] == {"used": 2, "cap": 60}
    session = r["prompts"][0]
    assert "anexa o PDF" in session and "achar o PDF" in session and "Kat" in session
    assert any("confirmar sexta" in p for p in r["prompts"][1:])


def test_write_report_escapes_and_rewrites(tmp_path):
    s = seed(tmp_path)
    path = write_report(s, cfg(), TODAY, tmp_path / "reports")
    assert path == tmp_path / "reports" / "2026-09-30.html"
    html = path.read_text(encoding="utf-8")
    assert "<script>x</script>" not in html and "&lt;script&gt;" in html and "&lt;b&gt;Zé" in html
    assert "Aceitar o prazo?" in html and "<html lang=\"pt-BR\">" in html
    s.add_request("i0", "novo pedido", "page")
    assert "novo pedido" in write_report(s, cfg(), TODAY, tmp_path / "reports").read_text(encoding="utf-8")
