import asyncio
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone

from assistantos.models import Brief, Event, Item, Mark, Status
from assistantos.store import Store

T0 = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)
TODAY = date(2026, 9, 30)
BRIEF = Brief(mudou="pediu prazo", decisao="Aceitar sexta?", opcoes=["sim", "não"], proximo_passo="responder",
              rascunho="Oi, entrego sexta.", urgencia="hoje")
TOOLS = {"o_que_decidir", "listar_itens", "ver_conversa", "marcar", "salvar_rascunho", "relatorio_do_dia"}


def seed(path):
    s = Store(path)
    for k, title in enumerate(["Kat", "Zé"]):
        s.upsert_item(Item(id=f"wa:{k}", source="whatsapp", title=title))
        s.add_event(Event(item_id=f"wa:{k}", at=T0 + timedelta(minutes=k), direction="in", text=f"msg {k}"))
    s.set_brief("wa:0", BRIEF, T0)
    s.close()
    return path


def server(tmp_path):
    from assistantos.mcp_server import make_server
    from assistantos.models import Backend, Config, Contacts, Owner, Tags
    cfg = Config(owner=Owner(name="Ana"), backend=Backend(kind="claude"), contacts=Contacts(), tags=Tags(order=["pessoal"]))
    return make_server(seed(tmp_path / "aos.db"), lambda: TODAY, cfg)


def payload(r):
    return r.structured_content or json.loads(r.content[0].text)


def call(srv, name, args=None):
    """In process a tool error raises; over the protocol (Hermes) it becomes an is_error result."""
    try:
        r = asyncio.run(srv.call_tool(name, args or {}))
    except Exception as e:  # noqa: BLE001
        return True, str(e)
    return (True, r.content[0].text) if r.is_error else (False, payload(r))


def test_tools_read_draft_and_mark_but_never_send(tmp_path):
    tools = {t.name: t for t in asyncio.run(server(tmp_path).list_tools())}
    assert set(tools) == TOOLS
    assert not any(w in n for n in tools for w in ("send", "envi", "post"))
    for n in ("o_que_decidir", "listar_itens", "ver_conversa", "relatorio_do_dia"):
        assert tools[n].annotations.read_only_hint is True


def test_o_que_decidir_brings_the_brief(tmp_path):
    err, out = call(server(tmp_path), "o_que_decidir")
    assert not err and [i["id"] for i in out["itens"]] == ["wa:0"]
    assert out["itens"][0]["brief"]["decisao"] == "Aceitar sexta?" and out["itens"][0]["titulo"] == "Kat"


def test_ver_conversa_and_unknown_item(tmp_path):
    srv = server(tmp_path)
    err, out = call(srv, "ver_conversa", {"item_id": "wa:1"})
    assert not err and out["titulo"] == "Zé" and out["mensagens"][-1]["texto"] == "msg 1"
    err, msg = call(srv, "ver_conversa", {"item_id": "nope"})
    assert err and "nope" in msg


def test_marcar_and_salvar_rascunho(tmp_path):
    srv = server(tmp_path)
    assert not call(srv, "marcar", {"item_id": "wa:1", "status": "feito"})[0]
    err, msg = call(srv, "marcar", {"item_id": "wa:1", "status": "aguardando"})
    assert err and "who and until" in msg
    assert not call(srv, "salvar_rascunho", {"item_id": "wa:0", "texto": "Combinado, sexta."})[0]
    s = Store(tmp_path / "aos.db")
    assert s.mark("wa:1").status == Status.FEITO and s.draft("wa:0") == "Combinado, sexta."
    _, out = call(srv, "listar_itens")
    assert {i["id"]: i["secao"] for i in out["itens"]}["wa:1"] == "resolvidos"


def test_relatorio_do_dia(tmp_path):
    err, out = call(server(tmp_path), "relatorio_do_dia")
    assert not err and {"decide", "requests", "came_in", "spend", "prompts", "problems"} <= set(out)


def test_aos_mcp_over_stdio(tmp_path):
    """The way Hermes runs it: a child process speaking MCP on stdin/stdout."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    seed((tmp_path / "local" / "state").mkdir(parents=True) or tmp_path / "local" / "state" / "aos.db")
    env = {k: v for k, v in os.environ.items() if k != "AOS_HOME"}   # --home must be enough on its own
    params = StdioServerParameters(command=sys.executable, args=["-m", "assistantos", "mcp", "--home", str(tmp_path)], env=env)

    async def go():
        async with stdio_client(params) as (r, w), ClientSession(r, w) as session:
            await session.initialize()
            names = {t.name for t in (await session.list_tools()).tools}
            bad = await session.call_tool("ver_conversa", {"item_id": "nope"})
            res = await session.call_tool("listar_itens", {})
            return names, payload(res), bad
    names, out, bad = asyncio.run(go())
    assert bad.is_error and "nope" in bad.content[0].text   # over the protocol an error is a result, not a crash
    assert names == TOOLS and {i["id"] for i in out["itens"]} == {"wa:0", "wa:1"}
