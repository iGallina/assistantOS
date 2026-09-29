# Throwaway spike: the same LangGraph node on `codex exec` (ChatGPT subscription).
import json, subprocess, tempfile, time, os
from typing import TypedDict
from pydantic import BaseModel, ConfigDict
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.graph import StateGraph, END


class CodexCLI(BaseChatModel):
    response_schema: dict | None = None

    @property
    def _llm_type(self) -> str:
        return "codex-cli"

    def _generate(self, messages, stop=None, run_manager=None, **kw):
        prompt = "\n\n".join(m.content for m in messages)
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "out.txt")
            cmd = ["codex", "exec", "--skip-git-repo-check", "--ephemeral", "-s", "read-only", "-C", d, "-o", out]
            if self.response_schema:
                sp = os.path.join(d, "schema.json")
                json.dump(self.response_schema, open(sp, "w"))
                cmd += ["--output-schema", sp]
            subprocess.run(cmd + ["-"], input=prompt, capture_output=True, text=True, check=True)
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=open(out).read()))])


class Brief(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decisao: str
    opcoes: list[str]
    urgencia: str


class S(TypedDict):
    msg: str
    brief: Brief | None


llm = CodexCLI(response_schema=Brief.model_json_schema())


def brief_node(s: S) -> S:
    raw = llm.invoke([HumanMessage(f"Mensagem de um cliente: {s['msg']!r}. Escreva o brief de decisão em português. Não use ferramentas.")])
    return {"msg": s["msg"], "brief": Brief.model_validate_json(raw.content)}


g = StateGraph(S)
g.add_node("brief", brief_node)
g.set_entry_point("brief")
g.add_edge("brief", END)
t = time.time()
r = g.compile().invoke({"msg": "Oi, conseguimos adiantar a entrega para sexta? O evento mudou de data.", "brief": None})
print(type(r["brief"]).__name__, r["brief"].model_dump(), f"{time.time()-t:.1f}s")
