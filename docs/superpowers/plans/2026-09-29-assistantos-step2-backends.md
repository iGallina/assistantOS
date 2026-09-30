# assistantOS build step 2 — backends, Jev, run logging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `Backend.ask(prompt, OutputModel, job) -> OutputModel` over the Claude and Codex subscription CLIs, a Jev client, and one `runs` row per model call — all tested without touching a real subscription.

**Architecture:** `backends/base.py` owns the contract (schema out, validated model back, run logged, errors typed); `claude_cli.py` / `codex_cli.py` only build the command and read the answer. Tests replace the CLI with `tests/fake_cli.py` run by the current Python, so CI needs no subscription. `jev.py` ports AIS-OS `scripts/jev.py` with the owner's name instead of "Ian" and the key from `TYPESAFE_API_KEY`.

**Tech Stack:** Python 3.12 stdlib (`subprocess`, `urllib`), Pydantic 2, pytest.

**Spec:** `docs/superpowers/specs/2026-09-29-assistantos-core-design.md` (Backends; decision 2026-09-29 option A).

## Global Constraints

- No LangChain model classes; the method is `Backend.ask`.
- Every model call writes exactly one `runs` row (job, backend, model, seconds, ok), success or failure.
- Quota exhaustion raises `QuotaExceeded` (caller stops model calls for the pass); anything else raises `BackendError`. Never retried here.
- Executables are resolved with `shutil.which` (finds `codex.cmd` on Windows); prompts go through stdin; the Codex schema goes through a file (no JSON on a `.cmd` command line).
- Jev failures return `None`, never raise; a missing key means no call and no run row.
- Deferred to step 5 (install): `aos doctor` checking that the backend CLI is installed and logged in — CI runners do not have them.

## Files

| File | Responsibility |
|---|---|
| `src/assistantos/backends/__init__.py` | `make_backend(cfg, store, **kw)`, re-exports |
| `src/assistantos/backends/base.py` | `Backend`, `BackendError`, `QuotaExceeded` |
| `src/assistantos/backends/claude_cli.py`, `codex_cli.py` | command + answer per CLI |
| `src/assistantos/jev.py` | `Jev` client, `route`, `social` |
| `tests/fake_cli.py` | stand-in CLI driven by env vars |
| `tests/test_backends.py`, `tests/test_jev.py` | behaviour |

---

### Task 1: Backend contract + Claude + Codex

**Interfaces:** Consumes `models.Backend` (config), `Store.log_run`. Produces `Backend(cfg, store, cmd: list[str] | None = None, timeout: float = 600).ask(prompt: str, output: type[M], job: str) -> M`; `BackendError`, `QuotaExceeded(BackendError)`; `make_backend(cfg, store, **kw) -> Backend`.

- [ ] **Step 1: fake CLI + failing tests**

```python
# tests/fake_cli.py
"""Stands in for `claude` / `codex` in tests. FAKE_REPLY = answer JSON | "quota" | "garbage"; FAKE_ARGV = file to record argv."""
import json, os, sys

kind, args = sys.argv[1], sys.argv[2:]
sys.stdin.read()
if os.environ.get("FAKE_ARGV"):
    open(os.environ["FAKE_ARGV"], "w", encoding="utf-8").write(json.dumps(args))
reply = os.environ["FAKE_REPLY"]
if reply == "quota":
    print("You've hit your usage limit. Try again later.", file=sys.stderr)
    sys.exit(1)
if kind == "claude":
    print(reply if reply == "garbage" else json.dumps({"is_error": False, "structured_output": json.loads(reply)}))
else:
    open(args[args.index("-o") + 1], "w", encoding="utf-8").write(reply)
```

```python
# tests/test_backends.py
import json
import sys
from pathlib import Path

import pytest

from assistantos.backends import BackendError, QuotaExceeded, make_backend
from assistantos.models import Backend as BackendCfg, Brief
from assistantos.store import Store

FAKE = Path(__file__).with_name("fake_cli.py")
BRIEF = {"mudou": "m", "decisao": "d", "opcoes": ["a"], "proximo_passo": "p", "rascunho": "r", "urgencia": "hoje"}


def backend(kind, tmp_path, **cfg):
    store = Store(tmp_path / "aos.db")
    b = make_backend(BackendCfg(kind=kind, **cfg), store, cmd=[sys.executable, str(FAKE), kind])
    return b, store


def runs(store):
    return store.db.execute("select job, backend, model, ok from runs").fetchall()


@pytest.mark.parametrize("kind", ["claude", "codex"])
def test_ask_returns_validated_model_and_logs(kind, tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_REPLY", json.dumps(BRIEF))
    b, store = backend(kind, tmp_path, model="m1")
    assert b.ask("oi", Brief, "brief") == Brief(**BRIEF)
    assert runs(store) == [("brief", kind, "m1", 1)]


def test_claude_command_carries_the_schema(tmp_path, monkeypatch):
    argv = tmp_path / "argv.json"
    monkeypatch.setenv("FAKE_REPLY", json.dumps(BRIEF))
    monkeypatch.setenv("FAKE_ARGV", str(argv))
    backend("claude", tmp_path)[0].ask("oi", Brief, "brief")
    a = json.loads(argv.read_text())
    assert a[a.index("--model") + 1] == "haiku"
    assert json.loads(a[a.index("--json-schema") + 1]) == Brief.model_json_schema()
    assert a[a.index("--tools") + 1] == ""


def test_codex_schema_goes_by_file(tmp_path, monkeypatch):
    argv = tmp_path / "argv.json"
    monkeypatch.setenv("FAKE_REPLY", json.dumps(BRIEF))
    monkeypatch.setenv("FAKE_ARGV", str(argv))
    backend("codex", tmp_path)[0].ask("oi", Brief, "brief")
    a = json.loads(argv.read_text())
    assert "--output-schema" in a and "-s" in a and a[a.index("-s") + 1] == "read-only"
    assert "-m" not in a  # no model configured → the CLI's default


@pytest.mark.parametrize("kind", ["claude", "codex"])
def test_quota_is_its_own_error(kind, tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_REPLY", "quota")
    b, store = backend(kind, tmp_path)
    with pytest.raises(QuotaExceeded):
        b.ask("oi", Brief, "brief")
    assert runs(store)[0][3] == 0


def test_wrong_shape_is_backend_error(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_REPLY", json.dumps({"mudou": "só isso"}))
    b, store = backend("codex", tmp_path)
    with pytest.raises(BackendError, match="Brief"):
        b.ask("oi", Brief, "brief")
    assert runs(store)[0][3] == 0


def test_unreadable_output_is_backend_error(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_REPLY", "garbage")
    with pytest.raises(BackendError):
        backend("claude", tmp_path)[0].ask("oi", Brief, "brief")


def test_not_installed(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))
    b = make_backend(BackendCfg(kind="codex"), Store(tmp_path / "aos.db"))
    with pytest.raises(BackendError, match="not installed"):
        b.ask("oi", Brief, "brief")


def test_gemini_not_yet(tmp_path):
    with pytest.raises(BackendError, match="not supported yet"):
        make_backend(BackendCfg(kind="gemini"), Store(tmp_path / "aos.db"))
```

- [ ] **Step 2:** `uv run pytest tests/test_backends.py -q` → FAIL (no `assistantos.backends`).
- [ ] **Step 3: implement**

```python
# src/assistantos/backends/base.py
"""The one contract every model backend keeps: schema out, validated Pydantic model back, one runs row per call."""
import re
import shutil
import subprocess
import time
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ..models import Backend as BackendCfg
from ..store import Store

M = TypeVar("M", bound=BaseModel)
# ponytail: keyword match on the CLI's error text; tighten once real limit messages are in the runs log
LIMIT = re.compile(r"(?i)usage limit|rate limit|limit reached|quota")


class BackendError(Exception):
    pass


class QuotaExceeded(BackendError):
    pass


class Backend:
    kind = ""
    default_model: str | None = None  # used when the config leaves model empty

    def __init__(self, cfg: BackendCfg, store: Store, cmd: list[str] | None = None, timeout: float = 600):
        self.cfg, self.store, self.cmd, self.timeout = cfg, store, cmd, timeout
        self.model = cfg.model or self.default_model

    def ask(self, prompt: str, output: type[M], job: str) -> M:
        t0, ok = time.monotonic(), False
        try:
            raw = self._call(prompt, output.model_json_schema())
            try:
                result = output.model_validate_json(raw)
            except ValidationError as e:
                raise BackendError(f"{self.kind}: answer does not match {output.__name__} ({e.error_count()} errors)") from e
            ok = True
            return result
        finally:
            self.store.log_run(job, self.kind, self.model, time.monotonic() - t0, ok)

    def _call(self, prompt: str, schema: dict) -> str:
        raise NotImplementedError

    def _fail(self, msg: str) -> BackendError:
        return (QuotaExceeded if LIMIT.search(msg) else BackendError)(f"{self.kind}: {msg}")

    def _run(self, args: list[str], prompt: str) -> subprocess.CompletedProcess:
        exe = self.cmd or [shutil.which(self.kind) or ""]
        if not exe[0]:
            raise BackendError(f"{self.kind}: not installed")
        try:
            p = subprocess.run(exe + args, input=prompt, capture_output=True, text=True,
                               encoding="utf-8", timeout=self.timeout)
        except subprocess.TimeoutExpired as e:
            raise BackendError(f"{self.kind}: no answer in {self.timeout:.0f}s") from e
        if p.returncode != 0:
            raise self._fail((p.stderr or p.stdout).strip()[-500:])
        return p
```

```python
# src/assistantos/backends/claude_cli.py
import json

from .base import Backend, BackendError


class ClaudeCLI(Backend):
    kind = "claude"
    default_model = "haiku"

    def _call(self, prompt: str, schema: dict) -> str:
        args = ["-p", "--model", self.model, "--tools", "", "--strict-mcp-config",
                "--output-format", "json", "--json-schema", json.dumps(schema)]
        try:
            out = json.loads(self._run(args, prompt).stdout)
        except json.JSONDecodeError as e:
            raise BackendError("claude: output is not JSON") from e
        if out.get("is_error"):
            raise self._fail(str(out.get("result", "")))
        if "structured_output" not in out:
            raise BackendError(f"claude: no structured_output ({out.get('subtype')})")
        return json.dumps(out["structured_output"])
```

```python
# src/assistantos/backends/codex_cli.py
import json
import tempfile
from pathlib import Path

from .base import Backend, BackendError


class CodexCLI(Backend):
    kind = "codex"

    def _call(self, prompt: str, schema: dict) -> str:
        with tempfile.TemporaryDirectory() as d:
            schema_file, out_file = Path(d) / "schema.json", Path(d) / "out.txt"
            schema_file.write_text(json.dumps(schema), encoding="utf-8")
            args = ["exec", "--skip-git-repo-check", "--ephemeral", "-s", "read-only", "-C", d,
                    "-o", str(out_file), "--output-schema", str(schema_file)]
            if self.model:
                args += ["-m", self.model]
            self._run(args + ["-"], prompt)
            if not out_file.exists():
                raise BackendError("codex: no answer written")
            return out_file.read_text(encoding="utf-8")
```

```python
# src/assistantos/backends/__init__.py
from ..models import Backend as BackendCfg
from ..store import Store
from .base import Backend, BackendError, QuotaExceeded
from .claude_cli import ClaudeCLI
from .codex_cli import CodexCLI

BACKENDS = {"claude": ClaudeCLI, "codex": CodexCLI}

__all__ = ["Backend", "BackendError", "QuotaExceeded", "make_backend"]


def make_backend(cfg: BackendCfg, store: Store, **kw) -> Backend:
    if cfg.kind not in BACKENDS:
        raise BackendError(f"{cfg.kind}: not supported yet")
    return BACKENDS[cfg.kind](cfg, store, **kw)
```

- [ ] **Step 4:** `uv run pytest -q` → PASS.
- [ ] **Step 5:** commit `feat: Claude and Codex backends behind Backend.ask`.

---

### Task 2: Jev client

**Interfaces:** Consumes `Store.log_run`, `models.Triage`. Produces `Jev(store, owner: str, key: str | None = None, opener=urllib.request.urlopen)` with `ask(state, question, job) -> dict | None`, `triage(ask_text, title="") -> Triage | None`, `needs_owner(state) -> float | None`, `suggest_tag(state, descriptions) -> Triage | None`; `route(t: Triage | None) -> "session" | "send" | "llm"`; `social(p: float | None) -> bool`.

- [ ] **Step 1: failing tests**

```python
# tests/test_jev.py
import io
import json

from assistantos.jev import Jev, route, social
from assistantos.models import Triage
from assistantos.store import Store


class Opener:
    def __init__(self, answer=None, fail=False):
        self.answer, self.fail, self.bodies = answer, fail, []

    def __call__(self, req, timeout):
        self.bodies.append(json.loads(req.data))
        if self.fail:
            raise OSError("down")
        return io.BytesIO(json.dumps({"model": "jev-x", "answers": {"q": self.answer}}).encode())


def jev(tmp_path, opener, key="k"):
    store = Store(tmp_path / "aos.db")
    return Jev(store, owner="Ana", key=key, opener=opener), store


def test_triage_uses_owner_name_and_logs(tmp_path):
    op = Opener({"choice": "sessao", "probabilities": {"sessao": 0.7}})
    j, store = jev(tmp_path, op)
    assert j.triage("migra o banco", "Projeto X") == Triage(label="sessao", p=0.7)
    body = op.bodies[0]
    assert body["model"] == "jev-latest" and "Ana" in body["state"] and "Ian" not in json.dumps(body)
    assert store.db.execute("select job, backend, ok from runs").fetchall() == [("triage", "jev", 1)]


def test_failure_returns_none_and_logs(tmp_path):
    j, store = jev(tmp_path, Opener(fail=True))
    assert j.needs_owner("oi") is None
    assert store.db.execute("select ok from runs").fetchall() == [(0,)]


def test_no_key_no_call(tmp_path, monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    op = Opener({"noul": 0.9})
    store = Store(tmp_path / "aos.db")
    assert Jev(store, owner="Ana", opener=op).needs_owner("oi") is None
    assert op.bodies == [] and store.db.execute("select count(*) from runs").fetchone() == (0,)


def test_route_thresholds():
    assert route(Triage(label="sessao", p=0.60)) == "session"
    assert route(Triage(label="sessao", p=0.59)) == "llm"
    assert route(Triage(label="enviar", p=0.80)) == "send"
    assert route(Triage(label="enviar", p=0.79)) == "llm"
    assert route(None) == "llm"


def test_social_is_a_label_threshold():
    assert social(0.39) and not social(0.40) and not social(None)
```

- [ ] **Step 2:** run → FAIL.
- [ ] **Step 3: implement**

```python
# src/assistantos/jev.py
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
```

- [ ] **Step 4:** `uv run pytest -q` → PASS; push, CI green on Windows + macOS.
- [ ] **Step 5:** commit `feat: Jev client (owner-neutral), routes and social label`; merge to `main` after green.
