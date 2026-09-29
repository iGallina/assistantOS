# Throwaway spike: LangGraph node -> LangChain chat model -> `claude -p` (subscription) -> Pydantic.
import json, subprocess, time
from typing import TypedDict
from pydantic import BaseModel
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.graph import StateGraph, END


class ClaudeCLI(BaseChatModel):
    model: str = "haiku"
    schema: dict | None = None

    @property
    def _llm_type(self) -> str:
        return "claude-cli"

    def _generate(self, messages, stop=None, run_manager=None, **kw):
        prompt = "\n\n".join(m.content for m in messages)
        cmd = ["claude", "-p", "--model", self.model, "--tools", "", "--strict-mcp-config",
               "--output-format", "json"]
        if self.schema:
            cmd += ["--json-schema", json.dumps(self.schema)]
        out = json.loads(subprocess.run(cmd, input=prompt, capture_output=True, text=True, check=True).stdout)
        content = json.dumps(out["structured_output"]) if self.schema else out["result"]
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])


class Brief(BaseModel):
    decisao: str
    opcoes: list[str]
    urgencia: str


class S(TypedDict):
    msg: str
    brief: Brief | None


llm = ClaudeCLI(schema=Brief.model_json_schema())


def brief_node(s: S) -> S:
    raw = llm.invoke([HumanMessage(f"Mensagem de um cliente: {s['msg']!r}. Escreva o brief de decisão em português.")])
    return {"msg": s["msg"], "brief": Brief.model_validate_json(raw.content)}


g = StateGraph(S)
g.add_node("brief", brief_node)
g.set_entry_point("brief")
g.add_edge("brief", END)
t = time.time()
r = g.compile().invoke({"msg": "Oi, conseguimos adiantar a entrega para sexta? O evento mudou de data.", "brief": None})
print(type(r["brief"]).__name__, r["brief"].model_dump(), f"{time.time()-t:.1f}s")
