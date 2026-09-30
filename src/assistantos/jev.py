"""Jev — TypeSafe's hosted System One — for classification only (bake-off 2026-09-28: docs/decisions.md).
Jev scores, it never writes. Code decides what to ask and what to do with the answer. Failures return None:
callers fall back to their behaviour without Jev. Every call is one `runs` row."""
import json
import os
import time
import urllib.request

from .models import Triage
from .store import Store

URL, MODEL = "https://api.typesafe.ai/v1/systemone", "jev-latest"
SOCIAL_BELOW = 0.40  # a label, never a filter: at this cut small talk is flagged, nothing is hidden
SESSION_AT, SEND_AT = 0.60, 0.80

REOPEN_Q = "Esta nova mensagem do contato exige uma resposta ou uma decisão de {owner}."
REOPEN_TRUE = "Sim: o contato pergunta algo, relata um problema ou bloqueio, pede uma ação ou uma decisão de {owner}."
REOPEN_FALSE = "Não: é agradecimento, cumprimento, confirmação, emoji ou conversa social; nada a fazer."
TRIAGE = {
    "enviar": "{owner} aprova enviar a mensagem que já está pronta ('pode enviar').",
    "lembrete_evento": "{owner} pede um lembrete ou um evento na agenda para uma data ou hora.",
    "resposta_rascunho": "{owner} pede para ler o contexto e responder, analisar, ou escrever/ajustar uma mensagem.",
    "sessao": "Trabalho que exige ferramentas: código, arquivos, repositórios, migração, anexar ou enviar documentos, várias etapas.",
}


class Jev:
    def __init__(self, store: Store, owner: str, key: str | None = None, opener=urllib.request.urlopen):
        self.store, self.owner, self.opener = store, owner, opener
        self.key = key if key is not None else os.environ.get("TYPESAFE_API_KEY")

    def ask(self, state: str, question: dict, job: str) -> dict | None:
        if not self.key:
            return None
        body = json.dumps({"model": MODEL, "state": state, "questions": {"q": question}}).encode()
        req = urllib.request.Request(URL, body, {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        t0, answer = time.monotonic(), None
        try:
            answer = json.load(self.opener(req, timeout=20))["answers"]["q"]
        except Exception:  # any failure → None, the caller falls back
            answer = None
        self.store.log_run(job, "jev", MODEL, time.monotonic() - t0, answer is not None)
        return answer

    def _choice(self, a: dict | None) -> Triage | None:
        if not a or not a.get("choice"):
            return None
        return Triage(label=a["choice"], p=float((a.get("probabilities") or {}).get(a["choice"], 0)))

    def triage(self, ask_text: str, title: str = "") -> Triage | None:
        criteria = {k: v.format(owner=self.owner) for k, v in TRIAGE.items()}
        return self._choice(self.ask(f"Pedido de {self.owner} sobre o item \"{title}\": {ask_text}",
                                     {"type": "choice", "instructions": "O que este pedido precisa?", "criteria": criteria},
                                     "triage"))

    def needs_owner(self, state: str) -> float | None:
        a = self.ask(state, {"type": "noul", "instructions": REOPEN_Q.format(owner=self.owner),
                             "criteria": {"true": REOPEN_TRUE.format(owner=self.owner), "false": REOPEN_FALSE}}, "reopen")
        return float(a["noul"]) if a and a.get("noul") is not None else None

    def suggest_tag(self, state: str, descriptions: dict[str, str]) -> Triage | None:
        if not descriptions:
            return None
        return self._choice(self.ask(state, {"type": "choice", "instructions": "Qual categoria?", "criteria": descriptions}, "tag"))


def route(t: Triage | None) -> str:
    """Only confident answers skip the model."""
    if t and t.label == "sessao" and t.p >= SESSION_AT:
        return "session"
    if t and t.label == "enviar" and t.p >= SEND_AT:
        return "send"
    return "llm"


def social(p: float | None) -> bool:
    return p is not None and p < SOCIAL_BELOW
