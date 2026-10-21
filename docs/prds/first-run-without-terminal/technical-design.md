# Technical Design: First Run Without a Terminal

**PRD:** [first-run-without-terminal-prd.md](first-run-without-terminal-prd.md) · **Assumptions:** [assumptions.md](assumptions.md)
**Builds on:** [the page refuses other websites](../../changes/page-refuses-other-websites/technical-design.md), built first

## Overview

Three pieces, all inside the existing Python package and the page server that already runs from logon:

1. **Setup screens** at `/setup` on the page server. Five steps: AI, WhatsApp, who you are, conversations, check. The
   two sign-ins run the official CLIs (`claude auth login`, `wacli auth`) as child processes of the page server; the
   screens poll their state. What the owner chooses is written to the same config files the terminal path uses.
2. **What the assistant follows and how it went**, recorded by each pass in the store: the conversations it followed,
   when it ran, whether it worked, and whether it has finished its first look. The page and Hermes read the same
   record, so they list the same conversations.
3. **The page's first screen** rebuilt around "Decidir agora", with the other sections one click away and each
   conversation reduced to its essentials until opened.

## Existing Code

- **Posture: Preserve.** Installs are in production (v0.3.0); the pass, the config files, `aos mcp` and the terminal
  commands keep working. A Mac keeps today's steps (SCOPE-001): nothing here is Windows-only code, but only Windows is
  tested.
- Reused: the page server, its origin guard, and the page restart at the end of `aos update` (all from the change
  design, so updated installs get `/setup` without a reboot); the store's `meta` table; the config files and their models
  (`owner.json`, `whatsapp.json`); the backend's `ask` for the AI test request (logged in `runs` like every call); the
  WhatsApp plugin's read-only access to the wacli store; `build_state`, shared by the page and `aos mcp`; the locale
  files.
- Kept: the MCP tools' names and fields (`rascunho_novo`, `brief`, `secao`…); new state fields are added beside the
  existing ones, never in their place. `aos setup` and `aos doctor` stay for support and the Mac. Setup never runs a
  wacli command that sends or changes anything in WhatsApp (AC-SETUP-04).

## Architecture

- **Workload:** the existing local web server (`aos page`, one process per owner, started at logon). No new process,
  port or service. Sign-ins are child processes it starts and watches.
- **Data:** the owner's choices in `local/config/*.json` (where the pass and `aos doctor` already read them); setup
  progress and the pass record in the store's `meta` table (no schema migration).
- **Dependencies:** wacli (pinned in `tools.py`), Claude Code's CLI, and one new Python package, `segno` (pure Python,
  BSD, no dependencies of its own), to draw the WhatsApp QR code as SVG on the computer, so the pairing code never
  leaves it. Rejected: wacli's own terminal QR in a `<pre>` (scanning depends on the font), and a QR library vendored
  into the page (more code to keep than one locked package; `aos update` installs it through `uv run --locked`).

## Design Decisions

### Setup

| Decision | Choice | Rationale |
|---|---|---|
| Where setup lives | `/setup` on the page server: its own HTML file, its own `setup.` locale strings, and `/api/setup/…` routes | The server already runs from logon on the owner's computer only, and the origin guard covers every route it serves, which is all AC-SETUP-08 asks. No new process to install or keep alive |
| Opening by itself (AC-SETUP-01) | The installer's final link (ticked by default) opens `http://127.0.0.1:8422/setup` instead of `/`. While setup is unfinished the page shows a link to it (AC-STATUS-03); the page header always has a "Configuração" link | The installer already opens the page this way and the page task has started by then. A failed install keeps hiding the link (existing behavior) |
| Where choices are kept | Name, language and time zone in `owner.json`; ticked conversations in `whatsapp.json` `chats`. Written whole and atomically (write beside, then replace), validated by the existing models, keeping the file's other keys | One source of truth: the pass, `aos doctor` and a support person editing by hand all read these files today |
| Progress (AC-SETUP-06) | `meta` key `setup:<step>` holds the time the step first showed as working. Setup never clears it; redoing a step that then fails shows the failure without clearing it. Setup opens at the first step in order `ai, whatsapp, owner, chats, check` without the key | Matches "finished = has ever shown as working". Survives closing the browser and restarting, since it is in the store |
| What "works now" means per step | ai: the configured AI answers a test request. whatsapp: wacli's read-only auth status reports linked, and the store can be read. owner: a name was saved from setup (the example file's placeholder never counts). chats: at least one ticked. check: all four checks pass | Each is cheap and checked when its screen opens; only the AI test costs a model call, and only when the owner asks for it |
| Installs from before this change | No inferred progress. The page shows "setup not finished" until the owner clicks through setup once; each already-working step turns done as soon as its screen opens | One install exists today. Inferring progress from files means guessing; clicking through costs the owner a minute |
| Long-running sign-ins | The page server starts the CLI with a fixed argument list, reads its output on a thread, and keeps one job per kind (`ai`, `whatsapp`) in memory. Starting again ends the previous job; a job still waiting after 10 minutes is ended and shown as failed. The AI test request has a 2-minute limit. The screens poll every 2 s | No queue or daemon, and no process left behind by an owner who walked away. A job lost when the page server restarts is restarted with one click; finished sign-ins are on disk with each CLI |
### The two sign-ins

| Decision | Choice | Rationale |
|---|---|---|
| WhatsApp pairing (AC-SETUP-03) | `wacli auth --qr-format text --events --idle-exit 30s --store <whatsapp.json store dir>`. Each `qr_code` event on its stderr replaces the QR; the server turns the payload into an SVG with `segno`. Done when `wacli --read-only --json auth status` reports `authenticated`; the phone number shown is its `phone` | Both flags exist in the pinned v0.19.0 and are wacli's documented way to feed an external renderer. With `--read-only`, status reads the session file without taking the store lock, so it answers while `auth` is still running. WhatsApp rotates the code; polling picks up the new one |
| Nothing sent while connecting (AC-SETUP-04) | Setup runs only `wacli auth …` and `wacli --read-only --json auth status`; the conversation list is read from the store file read-only. A test asserts every wacli command setup can start against that allowlist | Pairing adds the linked device; nothing else in that list writes to WhatsApp. The read-only file access is the one the pass already uses |
| Passkey or pairing errors | wacli's `error` event becomes a problem code (below) with one next step ("Tente de novo e escaneie em até 1 minuto", or contact whoever installed) | AC-SETUP-07: no raw output on screen |
| AI sign-in (AC-SETUP-02) | `claude auth login --claudeai`. Any `https://` link the CLI prints is shown as a button; if the CLI asks for a code, a field sends the pasted code to its input. Status from `claude auth status --json`. The step is done only when a test request through the installation's backend returns a valid answer | Covers both ways the CLI can finish (the browser returning to it, or a code to paste); spike S1 says which happens from a windowless process. The test request is the PRD's definition of done |
| Installation switched to ChatGPT (SCOPE-002) | When `backend.json` is not `claude`, the AI step shows no sign-in, only the test request; a failure sends the owner to whoever installed | Switching and its sign-in are a support step |

### Who the owner is

| Decision | Choice | Rationale |
|---|---|---|
| Language and time zone (AC-SETUP-05) | Prefilled from the browser: `navigator.language` (`pt*` → `pt-BR`, else `en`) and `Intl.DateTimeFormat().resolvedOptions().timeZone`. The owner can change both; the server checks the zone exists before saving | The browser reports the computer's settings as an IANA zone, with no Windows-zone mapping code or package |
| Applying a change | The page server reads `owner.json` on each request instead of once at start | A new language or time zone shows at once, with no restart. The file is small |

### Conversations

| Decision | Choice | Rationale |
|---|---|---|
| The list (AC-CHATS-01, AC-CHATS-03) | Read from the wacli store, read-only: people and groups only (no broadcast, newsletter, status, or the owner's own chat), name from the chat, else the contact's saved name, else the number formatted as a phone; newest activity first. Search filters in the browser. Ticks come from `whatsapp.json`, so after setup the same screen, reached from "Configuração", shows the current choices | Same access path as the pass, and it works while the pairing's first sync still holds wacli's lock. The pinned v0.19.0 schema has every column used: `chats` (`jid`, `kind`, `name`, `last_message_ts`) and `contacts` (`full_name`, `push_name`, `business_name`, `phone`). Hundreds of names are small to send whole |
| "Still bringing names in" | Shown while the pairing job is still syncing, or while the store's chat count changed in the last 30 s; the list refreshes on each poll | Names arrive after pairing in the first sync; both signals are local and cheap |
| Who is followed (AC-CHATS-02, UI-004) | At the end of collecting, each pass writes the followed conversation ids to `meta` `followed`. `build_state` keeps only those; until a pass has written it, everything shows as today. The pass also briefs only followed conversations; a request the owner already made on one stays answered | Applies "from the next pass", as the PRD says. The page and `aos mcp` both use `build_state`, so they list the same conversations. Today the pass briefs every conversation in the store, so an unticked one could still cost model calls. Nothing is deleted, so re-ticking brings marks, briefs and drafts back |
| A newly ticked conversation | Its first pass reads it back to the plugin's floor window (7 days) instead of from the shared cursor | Today a conversation added after the first pass gets nothing older than the last pass, so the first look would be empty. Duplicates are already ignored by message id |
| Suggestion (AC-CHATS-04) | A line above the list; no limit on the number ticked | Copy, not a rule |

### Status and problems

| Decision | Choice | Rationale |
|---|---|---|
| Pass record (AC-STATUS-02) | Every `aos run`, including one that stops on a configuration problem or crashes (problem `unknown`), writes `meta` `pass:last` (below). The page words the time in the owner's time zone: today "às 14:35", yesterday "ontem às 22:10", otherwise the date | The page can only say when the last look happened if every pass, failed or not, leaves a record |
| First look done (AC-PAGE-03) | A pass is caught up when it read every followed conversation and the per-pass and per-day limits left no brief undone. `pass:first_look` is the time of the first caught-up pass; ticking a new conversation clears it | "Nada esperando você agora" must not show while briefs are still waiting their turn |
| Next look | Last pass time + the pass interval (5 min), one constant shared with the scheduler | The page says when the assistant will look again without asking Task Scheduler |
| Problems (AC-SETUP-07) | Errors become a problem code where they arise; one catalog in the locale files maps each code to a message and its one next step, plus the setup step that fixes it, if any. The raw text still goes to `errors.log` for `aos bug-report` | One place to write owner-facing text in both languages. The backend recognizes a signed-out CLI by its message, as it already does for usage limits |
| Final check (AC-STATUS-01) | Runs the four checks of the PRD's table, each returning working or a problem code | Same codes and messages as a failed pass |

### The page

| Decision | Choice | Rationale |
|---|---|---|
| First screen (AC-PAGE-01, 02) | A row of five section tabs with counts; "Decidir agora" selected on every open (UI-003); the selected section's list below | One click reaches each section and the counts are always visible |
| Each conversation (AC-PAGE-04) | Closed: name, why it is on the list, newest draft, up to three actions (UI-002), and what the PRD's table adds. "Mais opções" opens the rest: full summary, conversation, other actions, "Pedir ao assistente" | The PRD's table, as written |
| Why it is on the list | A reason code from the status: replied after the owner's mark, wait ran out, summary ready | Computed in `build_state` from data it already has |
| Newest draft (AC-PAGE-05) | The later of the summary's draft and the last draft written on request; out of date when written before the conversation's last message. "Copiar rascunho" copies it | One draft on the first screen, and it is always the latest |
| Setup unfinished (AC-STATUS-03) | `state.setup.next_step` set → the first screen shows "setup not finished" with a link to that step, in place of the empty-list message and the last-check line | The page reads progress from the same `meta` keys setup writes |

## Interfaces

All routes are on the page server and behind its origin guard. Every `POST` answers `{"ok": true}` or
`{"problem": "<code>"}` unless shown otherwise.

```
GET  /setup                      setup screens (HTML)
GET  /api/setup                  → SetupState
POST /api/setup/ai/start         start (or restart) the AI sign-in
POST /api/setup/ai/code          {"code": "…"}   the code the CLI asked for
POST /api/setup/ai/test          → {"ok": bool, "problem": code|null}; marks setup:ai on success
POST /api/setup/whatsapp/start   start (or restart) the pairing
POST /api/setup/owner            {"name": "…", "language": "pt-BR"|"en", "timezone": "<IANA>"}; marks setup:owner
GET  /api/setup/chats            → {"syncing": bool, "chats": [Chat]}
POST /api/setup/chats            {"ticked": ["<jid>", …]}; marks setup:chats when non-empty
POST /api/setup/check            → {"items": [{"id": "ai"|"whatsapp"|"chats"|"config", "ok": bool, "problem": code|null}]};
                                   marks setup:check when all are ok
GET  /api/state                  existing body + "setup", "pass" and per-item "reason", "newest_draft" (below)
```

## Data Models

```
SetupState:
  next_step: "ai"|"whatsapp"|"owner"|"chats"|"check"|null    null = setup finished
  steps: [{id, done_at: iso|null, works: bool|null, problem: code|null}]   works null = not checked yet
  owner: {name|null, language, timezone}
  ai: {kind: "claude"|"codex"|"gemini", job: Job|null}
  whatsapp: {job: Job|null, phone: string|null, syncing: bool}

Job:
  state: "running"|"waiting_owner"|"done"|"failed"
  link: url|null          AI: the sign-in page to open
  needs_code: bool        AI: the CLI is waiting for a pasted code
  qr_svg: string|null     WhatsApp: the current QR, rendered on the server
  problem: code|null

Chat: {id: jid (never displayed), name, kind: "person"|"group", last_at: iso|null, ticked: bool}

meta keys (store):
  setup:<step>     iso time the step first showed working
  followed         JSON list of item ids the last pass read
  pass:last        JSON {at: iso, ok: bool, problems: [code], caught_up: bool}
  pass:first_look  iso time of the first caught-up pass since a conversation was last ticked; absent = not yet

/api/state additions:
  setup: {next_step: step|null}
  pass: {last: pass:last|null, next_at: iso|null, first_look_done: bool}
  items[].reason: "reaberto"|"vencido"|"pronto"|null
  items[].newest_draft: {text, at: iso, from: "brief"|"request", out_of_date: bool}|null

Problem codes (message and next step per language in the locale files; step = the setup step that fixes it):
  ai_signed_out → ai     ai_limit → none (wait)       ai_unreachable → ai
  wa_unlinked → whatsapp wa_sync_failed → none (retry) wa_pairing_failed → whatsapp
  wa_busy → whatsapp (a pass holds wacli's store; try again in a minute)
  no_chats → chats       config_unreadable → none (contact whoever installed)
  store_unreadable → none (contact whoever installed)  unknown → none (contact whoever installed)
```

## Integration Points

- **wacli** (pinned in `tools.py`): `auth --qr-format text --events`, `--read-only --json auth status`; its store file
  read-only.
- **Claude Code CLI**: `auth login --claudeai`, `auth status --json`; the existing `claude -p` call for the test request.
- **Installer** (`install/assistantOS.iss`): the final link points to `/setup`.
- **Hermes**: unchanged; through `aos mcp` it lists only the followed conversations.

## Testing

- Unit: setup progress and next step; config writes keep other keys and reject invalid input; the conversation list
  from a fixture wacli store (kinds, names, order); `followed` filtering in `build_state` (page and MCP agree);
  newly ticked conversations read back to the floor; `pass:last` on success, failure and config errors; first-look
  rules under the per-pass limit; newest draft and reason; every problem code has text in both languages; the wacli
  command allowlist. Sign-in jobs run against fake CLIs that print the real event and prompt shapes.
- Windows VM, by hand, once per release candidate: a clean install from `assistantOS-Setup.exe` through every setup
  step with a real phone and a Claude subscription, then restart mid-setup and confirm it resumes at the right step.

## Open Questions

1. **Spike S1, Windows VM: how `claude auth login` finishes from a windowless background process.** Either the
   browser returns to the CLI by itself, or the CLI prints a link and waits for a pasted code. The design handles
   both; the spike says which screen the owner actually sees, and whether the CLI needs a console at all. It runs in
   the VM, never on Ian's machine. **Not run yet (2026-10-21):** the VM was unavailable (no external disk attached, no
   VM registered in UTM). It must run before the AI step is built; the rest of the build does not wait on it.
2. **Fizzy keeps unticked conversations.** The PRD limits the change to the page and Hermes (AC-CHATS-02), so the
   Fizzy surface still syncs every conversation the assistant has read. Left as is; Fizzy is out of scope.
