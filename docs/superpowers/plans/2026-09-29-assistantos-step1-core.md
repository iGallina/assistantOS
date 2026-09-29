# assistantOS build step 1 — core package skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** an installable `assistantos` package with Pydantic models, a SQLite store, and `aos init` / `aos doctor` (config only), green in CI on Windows and macOS.

**Architecture:** src-layout package managed by uv. `models.py` holds every Pydantic model (config, domain, LLM outputs); `config.py` loads `local/config/*.json` and reports problems by file and field; `store.py` is SQLite with numbered migrations tracked in `PRAGMA user_version`; `cli.py` is argparse; user-facing strings come from `locales/*.json`.

**Tech Stack:** Python ≥ 3.12, uv (`uv_build` backend), Pydantic 2, pytest, GitHub Actions (`windows-latest`, `macos-latest`).

**Spec:** `docs/superpowers/specs/2026-09-29-assistantos-core-design.md`

## Global Constraints

- Nothing sends on the owner's behalf; no executables of ours; no API key for the model layer.
- Per-user files live in `local/` and are git-ignored; templates are committed.
- Every user-facing string lives in `src/assistantos/locales/{pt-BR,en}.json`; pt-BR is the default.
- LLM output models: `extra="forbid"`, every field required, no free-form dicts (Codex strict schema — spike 2026-09-29).
- Model field names must not shadow LangChain/Pydantic attributes (`schema`, `output_schema`, `json`).
- Datetimes are timezone-aware and stored in UTC.
- Deviation from the spec, recorded here: config templates ship **inside the package** (`src/assistantos/examples/`) so `aos init` works from any home; store migrations live in `store.py` (schema), while repo-level `migrations/` stays reserved for `aos update` file migrations (step 5).

## Files

| File | Responsibility |
|---|---|
| `pyproject.toml`, `.python-version`, `uv.lock` | package `assistantos`, script `aos`, deps pydantic; dev dep pytest |
| `.gitignore` | add `local/config/*.json`, `local/state/`, `.venv/` |
| `src/assistantos/__init__.py` | `__version__` |
| `src/assistantos/models.py` | all Pydantic models |
| `src/assistantos/config.py` | `load_config(dir) -> Config`, `ConfigError(problems)` |
| `src/assistantos/examples/*.example.json` | templates copied by `aos init` |
| `src/assistantos/store.py` | `Store`: migrations, items, events, marks, runs |
| `src/assistantos/i18n.py`, `locales/*.json` | `t(key, lang, **kw)` |
| `src/assistantos/cli.py` | `main(argv) -> int`: `init`, `doctor`, `--version` |
| `tests/test_models.py`, `test_config.py`, `test_store.py`, `test_cli.py` | one per module |
| `.github/workflows/ci.yml` | pytest + init/doctor smoke on Windows + macOS |

---

### Task 1: Package skeleton + CLI version

**Files:** Create `pyproject.toml`, `.python-version`, `src/assistantos/__init__.py`, `src/assistantos/cli.py`, `tests/test_cli.py`; Modify `.gitignore`.

**Interfaces:** Produces `assistantos.__version__: str`, `assistantos.cli.main(argv: list[str] | None = None) -> int`.

- [ ] **Step 1: pyproject + ignore rules**

```toml
[project]
name = "assistantos"
version = "0.1.0"
description = "Personal AI assistant for owner-operators"
requires-python = ">=3.12"
dependencies = ["pydantic>=2.9"]

[project.scripts]
aos = "assistantos.cli:main"

[dependency-groups]
dev = ["pytest>=8"]

[build-system]
requires = ["uv_build>=0.8,<0.13"]
build-backend = "uv_build"
```

`.python-version`: `3.12`. Append to `.gitignore`: `local/config/*.json`, `!local/config/*.example.json`, `local/state/`, `.venv/`, `.pytest_cache/`.

- [ ] **Step 2: failing test**

```python
# tests/test_cli.py
import pytest
from assistantos import __version__
from assistantos.cli import main


def test_version(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    assert capsys.readouterr().out.strip() == f"aos {__version__}"
```

- [ ] **Step 3:** `uv run pytest tests/test_cli.py -q` → FAIL (module missing).
- [ ] **Step 4: implement**

```python
# src/assistantos/__init__.py
__version__ = "0.1.0"
```

```python
# src/assistantos/cli.py
import argparse
import sys

from . import __version__


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")  # Windows pipes default to cp1252
    p = argparse.ArgumentParser(prog="aos")
    p.add_argument("--version", action="version", version=f"aos {__version__}")
    p.parse_args(argv)
    return 0
```

- [ ] **Step 5:** `uv run pytest -q` → PASS; `uv run aos --version` → `aos 0.1.0`.
- [ ] **Step 6:** commit `feat: package skeleton and aos --version`.

---

### Task 2: Models

**Files:** Create `src/assistantos/models.py`, `tests/test_models.py`.

**Interfaces:** Produces `Owner, Backend, Contacts, TagRule, Tags, Config, Status, Item, Event, Mark, Brief, RequestPlan, Triage, LLM_OUTPUTS: tuple[type[BaseModel], ...]`.

- [ ] **Step 1: failing tests**

```python
# tests/test_models.py
from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from assistantos.models import LLM_OUTPUTS, Event, Mark, Status, TagRule, Tags

NOW = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)


def test_llm_outputs_are_strict_for_codex():
    for m in LLM_OUTPUTS:
        s = m.model_json_schema()
        assert s["additionalProperties"] is False, m
        assert set(s["required"]) == set(s["properties"]), m


def test_bad_regex_is_rejected():
    with pytest.raises(ValidationError, match="pattern"):
        TagRule(field="title", pattern="(", tag="x")


def test_tags_must_be_in_order():
    with pytest.raises(ValidationError, match="not in order"):
        Tags(order=["pessoal"], default="pessoal", rules=[TagRule(field="title", pattern="x", tag="outro")])


def test_event_needs_timezone():
    with pytest.raises(ValidationError):
        Event(item_id="a", at=datetime(2026, 9, 29, 12, 0), direction="in")


def test_aguardando_needs_who_and_until():
    with pytest.raises(ValidationError, match="who and until"):
        Mark(item_id="a", status=Status.AGUARDANDO, at=NOW)
    Mark(item_id="a", status=Status.AGUARDANDO, at=NOW, who="Kat", until=date(2026, 10, 1))


@pytest.mark.parametrize("computed", [Status.REABERTO, Status.VENCIDO])
def test_computed_statuses_cannot_be_marked(computed):
    with pytest.raises(ValidationError, match="computed"):
        Mark(item_id="a", status=computed, at=NOW)
```

- [ ] **Step 2:** `uv run pytest tests/test_models.py -q` → FAIL (import error).
- [ ] **Step 3: implement**

```python
# src/assistantos/models.py
"""Every Pydantic model: per-user config, domain records, and each LLM output."""
import re
from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- config (local/config/*.json) ---

class Owner(Strict):
    name: str
    language: Literal["pt-BR", "en"] = "pt-BR"
    timezone: str = "America/Sao_Paulo"


class Backend(Strict):
    kind: Literal["claude", "codex", "gemini"]
    model: str | None = None
    per_pass_cap: int = Field(6, ge=0)
    per_day_cap: int = Field(60, ge=0)


class Contacts(Strict):
    owner_self: str | None = None
    count_only: list[str] = []
    never_list: list[str] = []


class TagRule(Strict):
    field: Literal["group", "id", "source", "title"]
    pattern: str
    tag: str

    @field_validator("pattern")
    @classmethod
    def _compiles(cls, v: str) -> str:
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"invalid regex: {e}") from e
        return v


class Tags(Strict):
    order: list[str]
    default: str = "pessoal"
    rules: list[TagRule] = []
    descriptions: dict[str, str] = {}

    @model_validator(mode="after")
    def _known_tags(self) -> "Tags":
        unknown = {self.default, *(r.tag for r in self.rules)} - set(self.order)
        if unknown:
            raise ValueError(f"tags not in order: {sorted(unknown)}")
        return self


class Config(Strict):
    owner: Owner
    backend: Backend
    contacts: Contacts
    tags: Tags


# --- domain ---

class Status(StrEnum):
    ABERTO = "aberto"
    REABERTO = "reaberto"
    DEPOIS = "depois"
    FEITO = "feito"
    IGNORADO = "ignorado"
    AGUARDANDO = "aguardando"
    VENCIDO = "vencido"


COMPUTED = {Status.REABERTO, Status.VENCIDO}


class Item(Strict):
    id: str
    source: str
    title: str
    tag: str | None = None
    link: str | None = None


class Event(Strict):
    item_id: str
    at: AwareDatetime
    direction: Literal["in", "out"]
    text: str = ""


class Mark(Strict):
    item_id: str
    status: Status
    at: AwareDatetime
    who: str | None = None
    until: date | None = None

    @model_validator(mode="after")
    def _rules(self) -> "Mark":
        if self.status in COMPUTED:
            raise ValueError(f"{self.status} is computed, never set by the owner")
        if self.status == Status.AGUARDANDO and not (self.who and self.until):
            raise ValueError("aguardando needs who and until")
        return self


# --- LLM outputs: every field required, no defaults, no free dicts (Codex strict schema) ---

class Brief(Strict):
    mudou: str
    decisao: str
    opcoes: list[str]
    proximo_passo: str
    rascunho: str
    urgencia: Literal["hoje", "semana", "sem pressa"]  # as AIS-OS brief.py


class RequestPlan(Strict):
    action: Literal["reply", "draft", "task", "event", "session"]
    text: str
    when: str  # ISO date-time for task/event, "" otherwise


class Triage(Strict):
    label: str
    p: float = Field(ge=0, le=1)


LLM_OUTPUTS = (Brief, RequestPlan)
```

- [ ] **Step 4:** `uv run pytest -q` → PASS.
- [ ] **Step 5:** commit `feat: Pydantic models for config, domain and LLM outputs`.

---

### Task 3: Config loading + templates

**Files:** Create `src/assistantos/config.py`, `src/assistantos/examples/{owner,backend,contacts,tags}.example.json`, `tests/test_config.py`.

**Interfaces:** Consumes `Config, Owner, Backend, Contacts, Tags`. Produces `load_config(d: Path) -> Config`, `ConfigError.problems: list[str]`, `EXAMPLES: Path`.

- [ ] **Step 1: failing tests**

```python
# tests/test_config.py
import json
import shutil

import pytest

from assistantos.config import EXAMPLES, ConfigError, load_config


def init(d):
    for ex in EXAMPLES.glob("*.example.json"):
        shutil.copyfile(ex, d / ex.name.replace(".example", ""))


def test_templates_validate(tmp_path):
    init(tmp_path)
    assert load_config(tmp_path).backend.kind == "claude"


def test_problem_names_file_and_field(tmp_path):
    init(tmp_path)
    (tmp_path / "backend.json").write_text(json.dumps({"kind": "gpt"}), encoding="utf-8")
    with pytest.raises(ConfigError) as e:
        load_config(tmp_path)
    assert any(p.startswith("backend.json: kind:") for p in e.value.problems)


def test_missing_and_broken_files_all_reported(tmp_path):
    init(tmp_path)
    (tmp_path / "owner.json").unlink()
    (tmp_path / "tags.json").write_text("{", encoding="utf-8")
    with pytest.raises(ConfigError) as e:
        load_config(tmp_path)
    assert "owner.json: missing" in e.value.problems
    assert any(p.startswith("tags.json: invalid JSON") for p in e.value.problems)
```

- [ ] **Step 2:** run → FAIL.
- [ ] **Step 3: implement**

```python
# src/assistantos/config.py
"""Load local/config/*.json into Config; report every problem by file and field."""
import json
from pathlib import Path

from pydantic import ValidationError

from .models import Backend, Config, Contacts, Owner, Tags

EXAMPLES = Path(__file__).parent / "examples"
FILES = {"owner": Owner, "backend": Backend, "contacts": Contacts, "tags": Tags}


class ConfigError(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


def load_config(d: Path) -> Config:
    parts, problems = {}, []
    for name, model in FILES.items():
        f = d / f"{name}.json"
        if not f.exists():
            problems.append(f"{f.name}: missing")
            continue
        try:
            raw = json.loads(f.read_text(encoding="utf-8"))
            parts[name] = model.model_validate({k: v for k, v in raw.items() if not k.startswith("_")})
        except json.JSONDecodeError as e:
            problems.append(f"{f.name}: invalid JSON (line {e.lineno})")
        except ValidationError as e:
            problems += [f"{f.name}: {'.'.join(map(str, x['loc'])) or '(root)'}: {x['msg']}" for x in e.errors()]
    if problems:
        raise ConfigError(problems)
    return Config(**parts)
```

Templates (`_about` keys are documentation; the loader drops keys starting with `_`):

```json
// owner.example.json
{"_about": "Quem usa o assistente. language: pt-BR | en.", "name": "SEU NOME", "language": "pt-BR", "timezone": "America/Sao_Paulo"}
// backend.example.json
{"_about": "Assinatura usada pelo modelo. kind: claude | codex | gemini. Limites de chamadas por passada e por dia.", "kind": "claude", "model": "haiku", "per_pass_cap": 6, "per_day_cap": 60}
// contacts.example.json
{"_about": "IDs do WhatsApp: número com DDI e DDD + @s.whatsapp.net; grupos <id>@g.us. count_only: só contar; never_list: nunca listar.", "owner_self": null, "count_only": [], "never_list": []}
// tags.example.json
{"_about": "Regras em ordem, a primeira que casa define a tag. field: group | id | source | title; pattern = regex.", "order": ["pessoal", "avulsos"], "default": "pessoal", "rules": [{"field": "group", "pattern": "^email$", "tag": "avulsos"}], "descriptions": {"pessoal": "Pessoal: contas, bancos, saúde, compras.", "avulsos": "Pontas soltas: e-mails sem projeto."}}
```

- [ ] **Step 4:** `uv run pytest -q` → PASS.
- [ ] **Step 5:** commit `feat: config loading with per-field problems; pt-BR templates`.

---

### Task 4: Store

**Files:** Create `src/assistantos/store.py`, `tests/test_store.py`.

**Interfaces:** Consumes `Item, Event, Mark`. Produces `Store(path: Path)` with `version() -> int`, `upsert_item(Item)`, `item(id) -> Item | None`, `add_event(Event)`, `events(item_id) -> list[Event]`, `set_mark(Mark)`, `mark(item_id) -> Mark | None`, `log_run(job: str, backend: str, model: str | None, seconds: float, ok: bool)`, `close()`; `SCHEMA_VERSION: int`.

- [ ] **Step 1: failing tests**

```python
# tests/test_store.py
from datetime import date, datetime, timedelta, timezone

from assistantos.models import Event, Item, Mark, Status
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
    # 12:30 UTC is later than 09:00 BRT (= 12:00 UTC) even though "09" sorts first as text
    s.add_event(Event(item_id="wa:1", at=datetime(2026, 9, 29, 12, 30, tzinfo=timezone.utc), direction="in", text="b"))
    s.add_event(Event(item_id="wa:1", at=datetime(2026, 9, 29, 9, 0, tzinfo=BRT), direction="out", text="a"))
    assert [e.text for e in s.events("wa:1")] == ["a", "b"]
    m = Mark(item_id="wa:1", status=Status.AGUARDANDO, at=datetime.now(timezone.utc), who="Kat", until=date(2026, 10, 1))
    s.set_mark(m)
    assert s.mark("wa:1") == m.model_copy(update={"at": m.at.astimezone(timezone.utc)})
    assert s.item("nope") is None and s.mark("nope") is None


def test_log_run(tmp_path):
    s = Store(tmp_path / "aos.db")
    s.log_run("brief", "claude", "haiku", 9.9, True)
    assert s.db.execute("select job, ok from runs").fetchall() == [("brief", 1)]
```

- [ ] **Step 2:** run → FAIL.
- [ ] **Step 3: implement**

```python
# src/assistantos/store.py
"""SQLite state. Schema changes are appended to MIGRATIONS; PRAGMA user_version tracks what ran."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import Event, Item, Mark

MIGRATIONS = [
    """
    CREATE TABLE items(id TEXT PRIMARY KEY, source TEXT NOT NULL, title TEXT NOT NULL, tag TEXT, link TEXT);
    CREATE TABLE events(id INTEGER PRIMARY KEY, item_id TEXT NOT NULL REFERENCES items(id),
                        at TEXT NOT NULL, direction TEXT NOT NULL, text TEXT NOT NULL);
    CREATE INDEX events_item_at ON events(item_id, at);
    CREATE TABLE marks(item_id TEXT PRIMARY KEY REFERENCES items(id), status TEXT NOT NULL,
                       at TEXT NOT NULL, who TEXT, until TEXT);
    CREATE TABLE runs(id INTEGER PRIMARY KEY, at TEXT NOT NULL, job TEXT NOT NULL, backend TEXT NOT NULL,
                      model TEXT, seconds REAL NOT NULL, ok INTEGER NOT NULL);
    """,
]
SCHEMA_VERSION = len(MIGRATIONS)


def utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA foreign_keys = ON")
        v = self.version()
        for i, sql in enumerate(MIGRATIONS[v:], start=v + 1):
            self.db.executescript(f"BEGIN; {sql} PRAGMA user_version = {i}; COMMIT;")

    def version(self) -> int:
        return self.db.execute("PRAGMA user_version").fetchone()[0]

    def close(self) -> None:
        self.db.close()

    def upsert_item(self, i: Item) -> None:
        with self.db:
            self.db.execute(
                "INSERT INTO items VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                "source=excluded.source, title=excluded.title, tag=excluded.tag, link=excluded.link",
                (i.id, i.source, i.title, i.tag, i.link))

    def item(self, item_id: str) -> Item | None:
        r = self.db.execute("SELECT id, source, title, tag, link FROM items WHERE id=?", (item_id,)).fetchone()
        return Item(**dict(zip(("id", "source", "title", "tag", "link"), r))) if r else None

    def add_event(self, e: Event) -> None:
        with self.db:
            self.db.execute("INSERT INTO events(item_id, at, direction, text) VALUES (?,?,?,?)",
                            (e.item_id, utc(e.at), e.direction, e.text))

    def events(self, item_id: str) -> list[Event]:
        rows = self.db.execute("SELECT item_id, at, direction, text FROM events WHERE item_id=? ORDER BY at",
                               (item_id,))
        return [Event(item_id=a, at=b, direction=c, text=d) for a, b, c, d in rows]

    def set_mark(self, m: Mark) -> None:
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO marks VALUES (?,?,?,?,?)",
                            (m.item_id, m.status.value, utc(m.at), m.who, m.until and m.until.isoformat()))

    def mark(self, item_id: str) -> Mark | None:
        r = self.db.execute("SELECT item_id, status, at, who, until FROM marks WHERE item_id=?", (item_id,)).fetchone()
        return Mark(**dict(zip(("item_id", "status", "at", "who", "until"), r))) if r else None

    def log_run(self, job: str, backend: str, model: str | None, seconds: float, ok: bool) -> None:
        with self.db:
            self.db.execute("INSERT INTO runs(at, job, backend, model, seconds, ok) VALUES (?,?,?,?,?,?)",
                            (utc(datetime.now(timezone.utc)), job, backend, model, seconds, int(ok)))
```

- [ ] **Step 4:** `uv run pytest -q` → PASS.
- [ ] **Step 5:** commit `feat: SQLite store with numbered migrations`.

---

### Task 5: `aos init` and `aos doctor` (config only), with locales

**Files:** Create `src/assistantos/i18n.py`, `src/assistantos/locales/{pt-BR,en}.json`; Modify `src/assistantos/cli.py`, `tests/test_cli.py`.

**Interfaces:** Consumes `EXAMPLES, load_config, ConfigError, Store`. Produces `t(key: str, lang: str = "pt-BR", **kw) -> str`; `aos init`, `aos doctor` (exit 0 all good, 1 otherwise); home = `$AOS_HOME` or the current directory; config at `<home>/local/config`, store at `<home>/local/state/aos.db`.

- [ ] **Step 1: failing tests** (append to `tests/test_cli.py`)

```python
import json

from assistantos.i18n import t


def test_locales_have_the_same_keys():
    from assistantos.i18n import _strings
    assert _strings("pt-BR").keys() == _strings("en").keys()


def test_init_then_doctor_ok(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AOS_HOME", str(tmp_path))
    assert main(["init"]) == 0
    assert main(["init"]) == 0  # idempotent: never overwrites
    assert main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert t("doctor.config_ok") in out and "✗" not in out


def test_doctor_names_the_bad_field(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AOS_HOME", str(tmp_path))
    main(["init"])
    (tmp_path / "local" / "config" / "backend.json").write_text(json.dumps({"kind": "gpt"}), encoding="utf-8")
    assert main(["doctor"]) == 1
    assert "backend.json: kind:" in capsys.readouterr().out


def test_doctor_before_init(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AOS_HOME", str(tmp_path))
    assert main(["doctor"]) == 1
    assert "owner.json: missing" in capsys.readouterr().out
```

- [ ] **Step 2:** run → FAIL.
- [ ] **Step 3: implement**

```python
# src/assistantos/i18n.py
import json
from functools import cache
from importlib.resources import files


@cache
def _strings(lang: str) -> dict[str, str]:
    return json.loads(files("assistantos").joinpath(f"locales/{lang}.json").read_text(encoding="utf-8"))


def t(key: str, lang: str = "pt-BR", **kw) -> str:
    return _strings(lang)[key].format(**kw)
```

```json
// locales/pt-BR.json
{"init.created": "Criados em {dir}: {files}. Edite-os e rode `aos doctor`.",
 "init.nothing": "Configuração já existe em {dir} — nada foi alterado.",
 "doctor.config_ok": "configuração válida",
 "doctor.config_bad": "configuração com problemas:",
 "doctor.store_ok": "banco local pronto (versão {version})",
 "doctor.store_bad": "banco local com erro: {error}"}
// locales/en.json
{"init.created": "Created in {dir}: {files}. Edit them and run `aos doctor`.",
 "init.nothing": "Config already exists in {dir} — nothing changed.",
 "doctor.config_ok": "config is valid",
 "doctor.config_bad": "config has problems:",
 "doctor.store_ok": "local database ready (version {version})",
 "doctor.store_bad": "local database error: {error}"}
```

```python
# src/assistantos/cli.py
import argparse
import os
import shutil
import sqlite3
import sys
from pathlib import Path

from . import __version__
from .config import EXAMPLES, ConfigError, load_config
from .i18n import t
from .store import Store


def home() -> Path:
    return Path(os.environ.get("AOS_HOME") or Path.cwd())


def cmd_init(h: Path) -> int:
    d = h / "local" / "config"
    d.mkdir(parents=True, exist_ok=True)
    created = []
    for ex in sorted(EXAMPLES.glob("*.example.json")):
        target = d / ex.name.replace(".example", "")
        if not target.exists():
            shutil.copyfile(ex, target)
            created.append(target.name)
    print(t("init.created", dir=d, files=", ".join(created)) if created else t("init.nothing", dir=d))
    return 0


def cmd_doctor(h: Path) -> int:
    ok, lang = True, "pt-BR"
    try:
        lang = load_config(h / "local" / "config").owner.language
        print("✓ " + t("doctor.config_ok", lang))
    except ConfigError as e:
        ok = False
        print("✗ " + t("doctor.config_bad", lang))
        for p in e.problems:
            print("    " + p)
    try:
        s = Store(h / "local" / "state" / "aos.db")
        print("✓ " + t("doctor.store_ok", lang, version=s.version()))
        s.close()
    except sqlite3.Error as e:
        ok = False
        print("✗ " + t("doctor.store_bad", lang, error=e))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")  # Windows pipes default to cp1252
    p = argparse.ArgumentParser(prog="aos")
    p.add_argument("--version", action="version", version=f"aos {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("doctor")
    a = p.parse_args(argv)
    return {"init": cmd_init, "doctor": cmd_doctor}[a.cmd](home())
```

- [ ] **Step 4:** `uv run pytest -q` → PASS. Manual: `AOS_HOME=$(mktemp -d) uv run aos init && uv run aos doctor`.
- [ ] **Step 5:** commit `feat: aos init and aos doctor (config + store), pt-BR/en strings`.

---

### Task 6: CI on Windows + macOS

**Files:** Create `.github/workflows/ci.yml`.

- [ ] **Step 1:**

```yaml
name: ci
on:
  push:
  workflow_dispatch:
jobs:
  test:
    strategy:
      fail-fast: false
      matrix:
        os: [windows-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync --locked
      - run: uv run pytest -q
      - name: init + doctor smoke (piped, as a scheduler would run it)
        shell: bash
        run: |
          export AOS_HOME="$RUNNER_TEMP/aos"
          uv run aos init | cat
          uv run aos doctor | cat
```

- [ ] **Step 2:** push the branch; `gh run watch` → both jobs green. A red Windows job is fixed at its root, not skipped.
- [ ] **Step 3:** commit `ci: pytest + init/doctor smoke on Windows and macOS`; merge the branch into `main` after green.
