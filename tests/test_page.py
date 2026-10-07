import json
import threading
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone

import pytest

from assistantos.models import Brief, Event, Item, Mark, Status
from assistantos.page.state import build_state
from assistantos.store import Store

T0 = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)
TODAY = date(2026, 9, 30)
BRIEF = Brief(mudou="m", decisao="d", opcoes=["a"], proximo_passo="p", rascunho="r", urgencia="hoje")


def seed(path):
    s = Store(path)
    for k in range(6):
        s.upsert_item(Item(id=f"wa:55610000000{k}@s.whatsapp.net", source="whatsapp", title=f"C{k}"))
        s.add_event(Event(item_id=f"wa:55610000000{k}@s.whatsapp.net", at=T0 + timedelta(minutes=k), direction="in",
                          text=f"msg {k}"))
    ids = [i.id for i in s.items()]
    s.set_brief(ids[0], BRIEF, T0)                                                       # aberto + current brief
    s.set_mark(Mark(item_id=ids[2], status=Status.FEITO, at=T0 - timedelta(hours=1)))    # reaberto
    s.set_mark(Mark(item_id=ids[3], status=Status.AGUARDANDO, at=T0 + timedelta(hours=1), who="Kat",
                    until=date(2026, 10, 2)))
    s.set_mark(Mark(item_id=ids[4], status=Status.DEPOIS, at=T0 + timedelta(hours=1), until=date(2026, 10, 1)))
    s.set_mark(Mark(item_id=ids[5], status=Status.IGNORADO, at=T0 + timedelta(hours=1)))
    return s, ids


def test_sections_and_order(tmp_path):
    s, ids = seed(tmp_path / "aos.db")
    st = build_state(s, TODAY)
    by = {i["id"]: i for i in st["items"]}
    assert [by[i]["section"] for i in ids] == ["decidir", "abertos", "decidir", "aguardando", "depois", "resolvidos"]
    assert [i["id"] for i in st["items"]][:2] == [ids[2], ids[0]]          # decidir: newest event first
    assert st["counts"] == {"decidir": 2, "abertos": 1, "aguardando": 1, "depois": 1, "resolvidos": 1}
    assert by[ids[0]]["brief"]["decisao"] == "d" and by[ids[0]]["brief_current"] is True
    assert by[ids[3]]["mark"] == {"who": "Kat", "until": "2026-10-02"}
    assert by[ids[0]]["wa"] == "556100000000"


def test_brief_goes_stale_and_social_tag(tmp_path):
    s, ids = seed(tmp_path / "aos.db")
    s.add_event(Event(item_id=ids[0], at=T0 + timedelta(hours=2), direction="in", text="nova"))
    s.set_label(ids[2], T0 + timedelta(minutes=2), 0.1)
    by = {i["id"]: i for i in build_state(s, TODAY)["items"]}
    assert by[ids[0]]["brief_current"] is False and by[ids[0]]["section"] == "abertos"
    assert by[ids[2]]["social"] is True and by[ids[2]]["section"] == "decidir"   # a label, never hidden


@pytest.fixture
def server(tmp_path):
    from assistantos.page.server import make_server
    s, ids = seed(tmp_path / "aos.db")
    s.close()
    srv = make_server(tmp_path / "aos.db", port=0, lang="pt-BR", today=lambda: TODAY)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", ids
    srv.shutdown()


def call(url, body=None):
    req = urllib.request.Request(url, json.dumps(body).encode() if body is not None else None,
                                 {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def test_http(server):
    base, ids = server
    code, html = call(base + "/")
    assert code == 200 and "Decidir agora" in html
    assert json.loads(call(base + "/api/state")[1])["counts"]["decidir"] == 2
    assert json.loads(call(base + f"/api/events?id={ids[0]}")[1])[0]["text"] == "msg 0"
    assert call(base + "/api/mark", {"item_id": ids[1], "status": "feito"})[0] == 200
    by = {i["id"]: i for i in json.loads(call(base + "/api/state")[1])["items"]}
    assert by[ids[1]]["section"] == "resolvidos"
    code, err = call(base + "/api/mark", {"item_id": ids[1], "status": "aguardando"})
    assert code == 400 and "who and until" in err
    assert call(base + "/api/mark", {"item_id": "nope", "status": "feito"})[0] == 404
    assert call(base + "/api/mark", {"item_id": ids[1], "status": "reaberto"})[0] == 400


def test_ask_queues_a_request_and_state_shows_it(server, tmp_path):
    base, ids = server
    code, body = call(base + "/api/ask", {"item_id": ids[0], "ask": "responde que sim"})
    rid = json.loads(body)["id"]
    assert code == 200
    code, body = call(base + "/api/ask", {"item_id": ids[0], "ask": "e o prazo?"})
    s = Store(tmp_path / "aos.db")
    assert s.request(json.loads(body)["id"])["parent"] == rid                 # a new ask follows up the last one
    s.answer_request(rid, "answered", "Feito: novo rascunho.")
    s.set_draft(ids[0], "Oi, sim!")
    s.close()
    by = {i["id"]: i for i in json.loads(call(base + "/api/state")[1])["items"]}
    assert [r["ask"] for r in by[ids[0]]["requests"]] == ["e o prazo?", "responde que sim"]
    assert by[ids[0]]["requests"][1]["reply"] == "Feito: novo rascunho." and by[ids[0]]["draft"] == "Oi, sim!"
    assert call(base + "/api/ask", {"item_id": ids[0], "ask": "  "})[0] == 400
    assert call(base + "/api/ask", {"item_id": "nope", "ask": "x"})[0] == 404
