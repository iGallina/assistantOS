# assistantOS core package — design

Status: approved by Ian 2026-09-29. Decisions it rests on: `docs/decisions.md` (2026-09-28 → 2026-09-29). Evidence: `docs/spikes/`.

## Goal

A customer clones their private copy of the repo, signs up for a subscription (Claude, ChatGPT/Codex, later Gemini), runs one install script, and gets the AIS-OS loop — their open loops on WhatsApp and e-mail classified, briefed and surfaced on the phone (Fizzy) and a local page, with drafts they send themselves. The behaviour lives in a tested Python package (`assistantos`), not in loose scripts or prompts.

## Non-goals (v1)

No executables of ours; no server of ours; nothing sent on the owner's behalf; no API key required for the model layer (Jev is the only key); no remote support access; no LangGraph tool-calling agents (tool work stays in the CLIs' own agent mode, see Agent runs).

## Repository layout

```
assistantOS/
  pyproject.toml                  # package `assistantos`, entry point `aos`; deps: pydantic, langgraph, langgraph-checkpoint-sqlite
  src/assistantos/
    models.py                     # Pydantic: config + domain + every LLM output
    store.py                      # SQLite: items, events, marks, briefs, requests, runs
    reconcile.py                  # status rules (ported from AIS-OS em-aberto.status)
    graph.py                      # the LangGraph loop (one pass per scheduler tick)
    backends/                     # our own thin wrappers over subscription CLIs
      base.py  claude_cli.py  codex_cli.py  gemini_cli.py
    jev.py                        # classification client (ported as-is)
    plugins/                      # one module per integration
      base.py  whatsapp.py  fizzy.py  google.py
    page/  server.py  page.html   # local page (ported from em-aberto.py / .local.html)
    platform/  windows.py  macos.py   # scheduler, notification, open-a-draft, process checks
    locales/  pt-BR.json  en.json # every user-facing string
    cli.py                        # `aos` commands
  migrations/  0001_initial.py    # numbered; run by `aos update`
  skills/                         # thin SKILL.md files: when to use a command, never the logic
  install/  install.ps1  install.sh
  local/                          # the owner's: config/*.json, own plugins, own skills — git-ignored
    config/*.example.json         # committed templates
  tests/
```

`src/` and everything outside `local/` is **core**: replaced by updates. `local/` is **the owner's**: never touched by an update. Updates are a `git merge` of an upstream tag; because owners only change `local/`, the merge never conflicts.

## Models (Pydantic)

- **Config** (`local/config/*.json`, validated on every load; a bad file fails `aos doctor` with the field named): `Owner` (name, language, timezone), `Backend` (`kind: claude|codex|gemini`, `model`, `per_pass_cap`, `per_day_cap`), `Contacts` (roles as in AIS-OS `contacts.py`), `Tags` (rules + descriptions), one `Config` model per plugin.
- **Domain:** `Item` (id, source, title, tag, links), `Event` (item id, time, direction in/out, text, attachments), `Mark` (status set by the owner + who/until for *aguardando*), `Status` = `aberto | reaberto | depois | feito | ignorado | aguardando | vencido` (AIS-OS semantics, unchanged).
- **LLM outputs** (`extra="forbid"`, so the same schema is strict enough for Codex): `Brief` (mudou, decisao, opcoes, proximo_passo, rascunho, urgencia), `RequestPlan` (one allowlisted action + args), `Triage` (label + probability, from Jev).

`Model.model_json_schema()` is what the backend enforces; `Model.model_validate_json()` is what the graph accepts. One definition, both ends.

## The loop (`graph.py`)

One pass per tick (default every 5 min, Task Scheduler / launchd). Deterministic nodes are plain code; only two nodes call a model.

```
collect  → each enabled plugin's poll(since) → Events           (code)
reconcile→ status per item from events + marks                   (code)
classify → Jev: needs-the-owner score, tag suggestion            (API, falls back to "no label")
select   → items whose brief is missing or older than last event (code; caps per pass/day)
brief    → backend.ask(prompt, Brief)                            (subscription CLI)
surface  → page data, Fizzy cards, one notification per pass     (code)
requests → Jev triage → backend.ask(prompt, RequestPlan) → execute only allowlisted actions (code)
```

Rules carried from AIS-OS: sweeps are code, the model drafts; a Jev label never hides an item; every model call writes one `runs` row (job, backend, model, seconds, ok) shown in the page and the daily report; a failed model call leaves the item unbriefed and visible, never dropped.

The pass holds a file lock (one pass at a time, as launchd guaranteed on the Mac). LangGraph checkpoints to `local/state/graph.db` (SqliteSaver): anything that needs the owner is an `interrupt` that survives the process exiting and resumes with `Command(resume=…)` when the owner acts (page, Fizzy); heavy jobs fan out one worker per item with `Send` (proven: `docs/spikes/2026-09-29-langgraph-durable-approval.py`). Decision 2026-09-29: LangGraph yes, LangChain model wrappers no.

## Backends

`backends/base.py`: `Backend.ask(prompt, output: type[M], job) -> M` — sends the prompt with `output.model_json_schema()`, validates the answer with `output.model_validate_json`, logs one `runs` row either way. No LangChain base class (its attribute names collided twice in the spikes); an API-key backend can later wrap a LangChain model behind the same method. Subclasses only build the command and read the result:

| Backend | Command | Result |
|---|---|---|
| Claude | `claude -p --model <m> --tools "" --strict-mcp-config --output-format json --json-schema <s>` | `structured_output` |
| Codex | `codex exec --skip-git-repo-check --ephemeral -s read-only -C <tmp> -o <file> --output-schema <file> -` | contents of `-o` file |
| Gemini | `gemini -p` (headless) | unverified — built after its spike |

Measured: Claude ~10 s, Codex ~28 s per call. Caps are per backend. Quota exhaustion (non-zero exit with a limit message) stops model calls for the rest of the pass and is reported, not retried.

**Agent runs** (the page's "Executar agora"): launch the CLI's own agent in the item's project folder with its native confinement — Claude `--tools <list> --disallowedTools Bash` (AIS-OS lesson), Codex `-s workspace-write` — and store the session id for "Continuar". LangGraph does not orchestrate tools in v1.

## Plugins

```python
class Plugin(Protocol):
    name: str
    Config: type[BaseModel]
    def connect(self, cfg) -> None: ...          # guided setup, idempotent
    def doctor(self, cfg) -> Check: ...          # one real read proving access
    def poll(self, cfg, since) -> list[Event]: ...
    actions: dict[str, Action]                   # each with risk: read | draft | write — never "send"
```

v1 plugins: **whatsapp** (wacli: QR pairing in `connect`, `sync --follow` kept alive by the scheduler, audio transcription path configurable), **fizzy** (two-way mirror + comments → requests, ported from `fizzy-sync.py`), **google** (Apps Script bridge — built only after its spike passes; covers Gmail, Docs, Sheets, Drive, Calendar). Owner plugins in `local/plugins/` load the same way.

## CLI (`aos`)

`init` (write `local/config` from examples, ask the few questions) · `connect <plugin>` · `doctor` (config valid, backends logged in, each plugin's read, scheduler registered, last pass age) · `run` (one pass) · `page` (serve the local page) · `report` (daily HTML report: what came in, what needs a decision, spend/quota, suggested next prompts) · `update` (fetch upstream tag → merge → `uv sync` → migrations → `doctor`; on failure reset to the previous tag) · `export` / `uninstall` (zip of `local/` + store; remove scheduled tasks; files kept until the owner deletes them) · `bug-report` (anonymize → owner reviews → open an issue on upstream).

## Platform layer

Only four things differ per OS: register/remove the scheduled pass, show a notification, open a draft (`mailto:` / `whatsapp://send`), check a process. Windows: Task Scheduler via PowerShell (proven in the Windows spike), toast via PowerShell (to prove). macOS: launchd + `osascript` (from AIS-OS). Tray/menu-bar icon: deferred; Fizzy on the phone is the v1 surface.

## Porting, not rewriting

Status rules, brief selection, request allowlist, Jev client, Fizzy sync and the page come from AIS-OS files listed in `docs/engine-inventory.md`, ported into modules with their existing tests (`tests/test_em_aberto.py`) as the first tests. AIS-OS keeps running unchanged.

## Testing

TDD per module. Unit tests: models (bad config names the field), reconcile (every status transition from AIS-OS), select/caps, allowlist (a plan outside it is refused), plugin contract with a fake plugin, backend with a fake CLI on PATH (command built right, result parsed, quota error handled). CI: `windows-latest` + `macos-latest` on every push; the Windows spike workflow becomes the install smoke test. Real-subscription calls stay in a manual `aos doctor --live`.

## Build order

1. Package skeleton, models, store, `aos doctor` (config only) — CI green on Windows + macOS.
2. Backends (Claude, Codex) + Jev + `runs` logging.
3. Graph with the WhatsApp plugin + the page.
4. Fizzy plugin.
5. Install scripts (`install.ps1`, `install.sh`), `update`, `export`, `uninstall`.
6. Google plugin (after its spike), Gemini backend (after its spike), daily report, bug-report with anonymizer.

## Open

Gemini headless structured output; Apps Script bridge (spike prepared); Windows toast without extra modules; e-mail for Outlook owners (Microsoft Graph has the same app-registration problem as Google).
