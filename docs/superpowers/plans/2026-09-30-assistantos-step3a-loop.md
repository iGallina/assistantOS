# assistantOS build step 3a — the loop: status rules, WhatsApp plugin, LangGraph pass, `aos run`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `aos run` does one pass — collect WhatsApp messages from the owner's chosen chats, compute each item's status, label reopened items with Jev, pick what needs a brief (code), and brief it with the owner's subscription model — all state in SQLite.

**Architecture:** `reconcile.py` ports AIS-OS `em-aberto.status` onto `Mark`; `plugins/whatsapp.py` reads the wacli store read-only; `graph.py` is a LangGraph `StateGraph` of plain-code nodes plus one model node (`brief`); `cli.py` wires config → plugins → store → backend → Jev → pass. Step 3b adds the local page.

**Tech Stack:** Python 3.12, Pydantic 2, LangGraph, SQLite, pytest.

**Spec:** `docs/superpowers/specs/2026-09-29-assistantos-core-design.md` (The loop, Plugins); AIS-OS sources `scripts/em-aberto.py` (`status`), `scripts/wa-listener.py` (`pending`, `history`), `scripts/brief.py`.

## Global Constraints

- Sweeps are code: which items are briefed is decided in `select`, never by a model. A Jev label never hides an item; a "social" reopen only skips the brief.
- Every model/Jev call is one `runs` row (step 2 contract). A failed brief leaves the item visible and unbriefed. `QuotaExceeded` stops briefs for the rest of the pass.
- Caps: `per_pass_cap` briefs per pass, `per_day_cap` brief calls per UTC day (counted from `runs`).
- The wacli store is opened read-only (`mode=ro` URI); the plugin never writes it.
- Times stored in UTC; shown to the model in the owner's timezone (`zoneinfo`; `tzdata` dependency so Windows has the IANA database).
- Deferred with reason: audio transcription (3c, platform binaries); LangGraph checkpointer (first `interrupt` arrives with owner requests — nothing to resume in a pass yet); a run lock (Task Scheduler's default `IgnoreNew` and launchd both refuse a second concurrent instance); `count_only`/`never_list` enforcement in the plugin (the owner lists chats explicitly in `whatsapp.json`).

## Files

| File | Responsibility |
|---|---|
| `pyproject.toml` | + `langgraph`, `tzdata` |
| `src/assistantos/models.py` | `Event.ext_id` |
| `src/assistantos/store.py` | migration 2: `events.ext_id` unique, `briefs`, `labels`, `meta`; methods below |
| `src/assistantos/reconcile.py` | `status`, `is_fresh`, `statuses` |
| `src/assistantos/plugins/__init__.py` | `PLUGINS`, `load_plugins` |
| `src/assistantos/plugins/whatsapp.py` | `WhatsAppConfig`, `WhatsApp.poll`, `WhatsApp.check` |
| `src/assistantos/graph.py` | `run_pass(...) -> dict` |
| `src/assistantos/cli.py`, `locales/*.json` | `aos run`; plugin checks in `aos doctor` |
| `src/assistantos/examples/whatsapp.example.json` | template (`init` copies it) |
| `tests/test_reconcile.py`, `test_whatsapp.py`, `test_graph.py`, `test_store.py`, `test_cli.py` | behaviour |

---

### Task 1: Store migration 2 + `Event.ext_id`

**Interfaces:** Produces on `Store`: `add_event(e) -> bool` (False when `ext_id` already stored), `items() -> list[Item]`, `last_event(item_id, direction=None) -> Event | None`, `set_brief(item_id, brief: Brief, event_at: datetime)`, `brief(item_id) -> tuple[Brief, datetime] | None`, `set_label(item_id, event_at, p: float | None)`, `label(item_id) -> tuple[datetime, float | None] | None`, `get_meta(key) -> str | None`, `set_meta(key, value)`, `runs_today(job) -> int`.

- [ ] Tests (append to `tests/test_store.py`):

```python
from assistantos.models import Brief

BRIEF = Brief(mudou="m", decisao="d", opcoes=["a"], proximo_passo="p", rascunho="r", urgencia="hoje")
T0 = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)


def test_ext_id_dedupes(tmp_path):
    s = Store(tmp_path / "aos.db")
    s.upsert_item(Item(id="wa:1", source="whatsapp", title="Kat"))
    e = Event(item_id="wa:1", at=T0, direction="in", text="oi", ext_id="wa:m1")
    assert s.add_event(e) is True and s.add_event(e) is False
    assert len(s.events("wa:1")) == 1


def test_last_event_brief_label_meta_runs(tmp_path):
    s = Store(tmp_path / "aos.db")
    s.upsert_item(Item(id="wa:1", source="whatsapp", title="Kat"))
    s.add_event(Event(item_id="wa:1", at=T0, direction="in", text="a"))
    s.add_event(Event(item_id="wa:1", at=T0 + timedelta(minutes=5), direction="out", text="b"))
    assert s.last_event("wa:1").text == "b" and s.last_event("wa:1", "in").text == "a"
    assert s.last_event("nope") is None
    s.set_brief("wa:1", BRIEF, T0)
    assert s.brief("wa:1") == (BRIEF, T0)
    s.set_label("wa:1", T0, 0.2)
    assert s.label("wa:1") == (T0, 0.2)
    s.set_meta("cursor:whatsapp", "x")
    assert s.get_meta("cursor:whatsapp") == "x" and s.get_meta("nope") is None
    s.log_run("brief", "claude", "haiku", 1.0, False)
    assert s.runs_today("brief") == 1 and s.runs_today("tag") == 0
    assert [i.id for i in s.items()] == ["wa:1"]
```

- [ ] Implement: `Event.ext_id: str | None = None`; append to `MIGRATIONS`:

```python
    """
    ALTER TABLE events ADD COLUMN ext_id TEXT;
    CREATE UNIQUE INDEX events_ext ON events(ext_id) WHERE ext_id IS NOT NULL;
    CREATE TABLE briefs(item_id TEXT PRIMARY KEY REFERENCES items(id), at TEXT NOT NULL, event_at TEXT NOT NULL, body TEXT NOT NULL);
    CREATE TABLE labels(item_id TEXT PRIMARY KEY REFERENCES items(id), event_at TEXT NOT NULL, p REAL);
    CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    """,
```

and the methods (full code in the commit; `add_event` uses `INSERT OR IGNORE` and returns `cursor.rowcount == 1`; `runs_today` counts rows whose `at` starts with today's UTC date).
- [ ] `uv run pytest -q` green → commit `feat(store): migration 2 — event ids, briefs, labels, meta`.

### Task 2: Status rules (`reconcile.py`)

**Interfaces:** `status(mark: Mark | None, fresh: bool, today: date) -> Status`; `is_fresh(store, item_id, mark) -> bool` (an inbound event after the mark); `statuses(store, today) -> dict[str, Status]`.

- [ ] Tests (`tests/test_reconcile.py`) — the AIS-OS table:

```python
from datetime import date, datetime, timezone

import pytest

from assistantos.models import Mark, Status as S
from assistantos.reconcile import status

T = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)
TODAY = date(2026, 9, 30)


def m(s, **kw):
    return Mark(item_id="i", status=s, at=T, **kw)


@pytest.mark.parametrize("mark, fresh, expected", [
    (None, False, S.ABERTO),
    (None, True, S.ABERTO),
    (m(S.ABERTO), True, S.ABERTO),                      # "desfazer" = no mark
    (m(S.FEITO), False, S.FEITO),
    (m(S.FEITO), True, S.REABERTO),                     # their side moved after the owner's mark
    (m(S.IGNORADO), True, S.REABERTO),
    (m(S.DEPOIS, until=date(2026, 10, 2)), False, S.DEPOIS),
    (m(S.DEPOIS, until=date(2026, 9, 30)), False, S.ABERTO),   # "amanhã" arrived
    (m(S.DEPOIS), True, S.REABERTO),
    (m(S.AGUARDANDO, who="Kat", until=date(2026, 10, 1)), False, S.AGUARDANDO),
    (m(S.AGUARDANDO, who="Kat", until=date(2026, 9, 30)), False, S.VENCIDO),
    (m(S.AGUARDANDO, who="Kat", until=date(2026, 10, 1)), True, S.REABERTO),   # answered before the date
])
def test_status(mark, fresh, expected):
    assert status(mark, fresh, TODAY) == expected
```

- [ ] Implement:

```python
def status(mark: Mark | None, fresh: bool, today: date) -> Status:
    if mark is None or mark.status == Status.ABERTO:
        return Status.ABERTO
    if fresh:
        return Status.REABERTO
    if mark.status == Status.AGUARDANDO:
        return Status.VENCIDO if mark.until <= today else Status.AGUARDANDO
    if mark.status == Status.DEPOIS and mark.until and mark.until <= today:
        return Status.ABERTO
    return mark.status
```

- [ ] Green → commit `feat: status rules ported from AIS-OS`.

### Task 3: WhatsApp plugin

**Interfaces:** `WhatsAppConfig(store: str = "~/.wacli/wacli.db", chats: list[str], floor_days: int = 7)`; `WhatsApp().poll(cfg, since: datetime | None) -> tuple[list[Item], list[Event]]`; `WhatsApp().check(cfg) -> str | None`; `plugins.load_plugins(config_dir) -> list[tuple[plugin, cfg]]` (a plugin is enabled by its `<name>.json`; bad file → `ConfigError`).

- [ ] Tests build a fixture store with wacli's columns (`chats(jid, name)`, `messages(chat_jid, msg_id, ts, from_me, media_type, text, media_caption)`) and assert: items for every configured chat (title = chat name, jid when unnamed); events both ways with `ext_id="wa:<msg_id>"`; unconfigured chats ignored; the floor excludes old messages; `since` excludes earlier messages; empty text skipped, media without caption becomes `[audio]`; `check` returns a problem for a missing store and `None` for a good one; the store file is not modified (mtime + bytes).
- [ ] Implement with `sqlite3.connect(Path(cfg.store).expanduser().as_uri() + "?mode=ro", uri=True)` (correct on Windows paths too); `ts >= start` (duplicates are dropped by `ext_id`).
- [ ] Green → commit `feat(plugins): WhatsApp plugin over the wacli store (read-only)`.

### Task 4: The pass (`graph.py`) + `aos run`

**Interfaces:** `run_pass(store, plugins, backend, jev, cfg: Config, today: date) -> dict` with keys `new_events`, `briefed: list[str]`, `errors: list[str]`; `aos run` prints `t("run.summary")` and exits 0 (1 on config/backend setup errors).

- [ ] Tests (`tests/test_graph.py`) with a fake plugin (returns fixed items/events), a `FakeBackend` (records prompts; returns a `Brief`; can raise `QuotaExceeded`), `jev=None`:
  - first pass briefs every open item (newest event first), respects `per_pass_cap`;
  - a second pass with no new events briefs nothing;
  - `feito` mark then a new inbound event → `reaberto` → briefed again, and the prompt contains the new text and the previous brief;
  - `QuotaExceeded` stops the pass after the first failure and is reported in `errors`; a `BackendError` on one item does not stop the others;
  - `per_day_cap` counts earlier `brief` runs of the day;
  - with a Jev stub scoring a reopen 0.2, the item is labelled and not briefed; at 0.9 it is briefed.
- [ ] `tests/test_cli.py`: `aos init` copies `whatsapp.json`; `aos run` with a fixture wacli store and `make_backend` monkeypatched to the fake → exit 0 and the summary line; `aos doctor` reports the WhatsApp store problem when the path is wrong.
- [ ] Implement `graph.py` as a `StateGraph` `collect → reconcile → classify → select → brief → END` and the CLI command; add `run.*` and `doctor.plugin_*` strings to both locales.
- [ ] Green locally and in CI (Windows + macOS) → merge to `main`.
- [ ] Manual check (not CI): `aos run` against a **copy** of the real wacli store with one real chat, Claude backend → one real brief; the live AIS-OS loop is untouched.
