import http.client
import json
import socket
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
    threading.Thread(target=srv.serve_forever, args=(0.01,), daemon=True).start()  # a fast shutdown
    yield f"http://127.0.0.1:{srv.server_address[1]}", ids
    srv.shutdown()
    srv.server_close()


def call(url, body=None):
    """As the page's own buttons do: a browser sends Origin on every fetch POST."""
    origin = url.split("/api/")[0] if body is not None else None
    req = urllib.request.Request(url, json.dumps(body).encode() if body is not None else None,
                                 {"Content-Type": "application/json", **({"Origin": origin} if origin else {})})
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


# --- The page refuses other websites (docs/changes/page-refuses-other-websites, AC-ORIGIN-01..04) ---

ROUTES = [("GET", "/", None), ("GET", "/api/state", None), ("GET", "/api/events?id={id}", None),
          ("POST", "/api/mark", {"status": "feito"}), ("POST", "/api/ask", {"ask": "responde que sim"})]
FRAME_HEADERS = {"content-security-policy": "frame-ancestors 'none'", "x-frame-options": "DENY",
                 "x-content-type-options": "nosniff"}


def raw(port, method, path, headers, body=None):
    """One request with exactly these headers: no Host or Origin unless given."""
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    c.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
    data = json.dumps(body).encode() if body is not None else b""
    for k, v in {**headers, **({"Content-Type": "application/json", "Content-Length": str(len(data))}
                               if method == "POST" else {})}.items():
        c.putheader(k, v)
    c.endheaders(data or None)
    r = c.getresponse()
    out = r.status, {k.lower(): v for k, v in r.getheaders()}, r.read().decode()
    c.close()
    return out


def snapshot(db, ids):
    s = Store(db)
    try:
        return [(s.mark(i), s.requests(i)) for i in ids]
    finally:
        s.close()


@pytest.fixture
def page(server, tmp_path):
    base, ids = server
    return int(base.rsplit(":", 1)[1]), ids, tmp_path / "aos.db"


def _route(method, path, body, ids, item=1):
    return method, path.format(id=ids[item]), body and {**body, "item_id": ids[item]}


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "LocalHost"])
@pytest.mark.parametrize("method,path,body", ROUTES)
def test_the_page_itself_is_answered_at_both_addresses(page, host, method, path, body):
    port, ids, _ = page
    method, path, body = _route(method, path, body, ids)
    origin = {"Origin": f"http://{host.lower()}:{port}"} if method == "POST" else {}
    code, headers, text = raw(port, method, path, {"Host": f"{host}:{port}", **origin}, body)
    assert code == 200, text
    assert {k: headers.get(k) for k in FRAME_HEADERS} == FRAME_HEADERS
    assert "access-control-allow-origin" not in headers                   # CORS would hand other sites the reads


@pytest.mark.parametrize("method,path,body", ROUTES)
@pytest.mark.parametrize("headers", [
    {"Host": "evil.example:{port}", "Origin": "http://evil.example:{port}"},   # DNS rebinding: the attacker's name
    {"Host": "evil.example:{port}", "Origin": "http://127.0.0.1:{port}"},
    {"Host": "127.0.0.1", "Origin": "http://127.0.0.1:{port}"},               # right host, no port
    {"Host": "127.0.0.1:8422", "Origin": "http://127.0.0.1:8422"},            # not the port this server bound
    {"Origin": "http://127.0.0.1:{port}"},                                     # no Host at all
], ids=["rebinding", "foreign-host", "host-without-port", "other-port", "no-host"])
def test_a_foreign_host_is_refused_on_every_route_and_changes_nothing(page, method, path, body, headers):
    port, ids, db = page
    method, path, body = _route(method, path, body, ids)
    before = snapshot(db, ids)
    code, got, text = raw(port, method, path, {k: v.format(port=port) for k, v in headers.items()}, body)
    assert (code, json.loads(text)) == (403, {"error": "forbidden"})
    assert {k: got.get(k) for k in FRAME_HEADERS} == FRAME_HEADERS
    assert snapshot(db, ids) == before


@pytest.mark.parametrize("path,body", [r[1:] for r in ROUTES if r[0] == "POST"])
@pytest.mark.parametrize("origin", ["http://evil.example", "null", None, "http://127.0.0.1:1",
                                    "https://127.0.0.1:{port}", "http://127.0.0.1:{port}.evil.example"],
                         ids=["foreign", "null", "missing", "other-port", "https", "suffix"])
def test_a_post_from_any_other_website_is_refused_and_changes_nothing(page, path, body, origin):
    port, ids, db = page
    _, path, body = _route("POST", path, body, ids)
    before = snapshot(db, ids)
    headers = {"Host": f"127.0.0.1:{port}", **({"Origin": origin.format(port=port)} if origin else {})}
    code, _, text = raw(port, "POST", path, headers, body)
    assert (code, json.loads(text)) == (403, {"error": "forbidden"})
    assert snapshot(db, ids) == before


def test_a_refusal_never_opens_the_store(page, monkeypatch):
    port, ids, _ = page

    def no_store(*a):
        raise AssertionError("a refused request opened the store")
    monkeypatch.setattr("assistantos.page.server.Store", no_store)
    for method, path, body in ROUTES:
        method, path, body = _route(method, path, body, ids)
        assert raw(port, method, path, {"Host": f"evil.example:{port}"}, body)[0] == 403
    assert raw(port, "POST", "/api/mark", {"Host": f"127.0.0.1:{port}", "Origin": "null"},
               {"item_id": ids[1], "status": "feito"})[0] == 403


def test_every_response_carries_the_frame_and_sniff_headers_and_never_cors(page):
    port, ids, _ = page
    ok = {"Host": f"127.0.0.1:{port}", "Origin": f"http://127.0.0.1:{port}"}
    answers = [raw(port, "GET", "/nope", ok),                                           # 404
               raw(port, "POST", "/api/mark", ok, {"item_id": "nope", "status": "feito"}),  # 404 unknown item
               raw(port, "POST", "/api/ask", ok, {"item_id": ids[0], "ask": " "}),        # 400 from the handler
               raw(port, "OPTIONS", "/api/mark", ok),                                    # 501 from send_error
               raw(port, "PUT", "/api/mark", ok, None)]                                  # 501 from send_error
    with socket.create_connection(("127.0.0.1", port), timeout=5) as sock:              # 400 from send_error
        sock.sendall(b"GET / x HTTP/1.0\r\n\r\n")          # bad syntax, after the version is known
        head = sock.makefile("rb").read().decode("latin-1").split("\r\n\r\n")[0].lower()
    assert [a[0] for a in answers] == [404, 404, 400, 501, 501] and head.startswith("http/1.0 400")
    for _, headers, _ in answers:
        assert {k: headers.get(k) for k in FRAME_HEADERS} == FRAME_HEADERS
        assert "access-control-allow-origin" not in headers
    for k, v in FRAME_HEADERS.items():
        assert f"{k}: {v.lower()}" in head


def test_another_port_works_at_both_addresses_and_8422_is_foreign_there(tmp_path):
    """`aos page --port N`: the page itself is whatever port the server actually bound, with no setting."""
    from assistantos.page.server import make_server
    seed(tmp_path / "aos.db")[0].close()
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    srv = make_server(tmp_path / "aos.db", port=port, lang="pt-BR", today=lambda: TODAY)
    threading.Thread(target=srv.serve_forever, args=(0.01,), daemon=True).start()  # a fast shutdown
    try:
        for host in ("127.0.0.1", "localhost"):
            assert raw(port, "GET", "/api/state", {"Host": f"{host}:{port}"})[0] == 200
            item = json.loads(raw(port, "GET", "/api/state", {"Host": f"{host}:{port}"})[2])["items"][0]["id"]
            assert raw(port, "POST", "/api/mark", {"Host": f"{host}:{port}", "Origin": f"http://{host}:{port}"},
                       {"item_id": item, "status": "feito"})[0] == 200
        assert raw(port, "GET", "/api/state", {"Host": "127.0.0.1:8422"})[0] == 403
    finally:
        srv.shutdown()
        srv.server_close()
