# Throwaway: does a LangGraph job survive a process exit while waiting for the owner, and fan out work?
import sys, sqlite3, operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command, Send
from langgraph.checkpoint.sqlite import SqliteSaver

class S(TypedDict):
    items: list[str]
    drafts: Annotated[list[str], operator.add]
    approved: bool

def fan_out(s): return [Send("draft", {"item": i}) for i in s["items"]]          # heavy load: one worker per item
def draft(w): return {"drafts": [f"rascunho para {w['item']}"]}                   # a CLI agent call in the real thing
def approve(s): return {"approved": interrupt({"drafts": s["drafts"]}) == "aprovado"}  # pauses; process may exit

g = StateGraph(S)
g.add_node("draft", draft); g.add_node("approve", approve)
g.add_conditional_edges(START, fan_out, ["draft"]); g.add_edge("draft", "approve"); g.add_edge("approve", END)
app = g.compile(checkpointer=SqliteSaver(sqlite3.connect(sys.argv[1], check_same_thread=False)))
cfg = {"configurable": {"thread_id": "job-1"}}
if sys.argv[2] == "start":
    r = app.invoke({"items": ["Kat", "Aline", "Bruna"], "drafts": [], "approved": False}, cfg)
    print("paused, waiting for owner:", r["__interrupt__"][0].value)
else:
    print("resumed in a new process:", app.invoke(Command(resume="aprovado"), cfg))
