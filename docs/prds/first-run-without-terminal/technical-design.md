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
| Where choices are kept | Name, language and time zone in `owner.json`; ticked conversations in `whatsapp.json` `chats`. Written whole and atomically (write beside, then replace), validated by the existing models, keeping the file's other keys. The temp file beside has a unique name. A `PermissionError` on the replace is tried again with short, growing waits for about 2 seconds. If it still fails, the temp file is removed, the old file stays as it was, the raw error goes to `errors.log`, and the POST answers `{"problem": "unknown"}` | One source of truth: the pass, `aos doctor` and a support person editing by hand all read these files today. The page server handles requests on threads, so two saves can overlap; a unique temp name keeps them apart. On Windows, a replace fails while another process holds the file; antivirus and the search indexer do this briefly, so a short retry absorbs them. A failure that lasts 2 seconds is not brief, so it goes to whoever installed |
| Progress (AC-SETUP-06) | `meta` key `setup:<step>` holds the time the step first showed as working. Setup never clears it; redoing a step that then fails shows the failure without clearing it. Setup opens at the first step in order `ai, whatsapp, owner, chats, check` without the key | Matches "finished = has ever shown as working". Survives closing the browser and restarting, since it is in the store |
| Moving between steps (AC-SETUP-01, 06, 07, AC-CHATS-03) | One HTML page. A row of the five steps, each marked done from `done_at`, is always shown, and any step opens at any time; none is locked. The step shown comes from the address fragment (`/setup#chats`), else `next_step`, else, once setup is finished, the conversations step with the current ticks. It changes only when the owner opens setup or follows a link, never on a poll. A step that works shows "Continuar", a link to the next step in order; on the check step that link goes to the page (UI-001). The page's "Configuração" link opens `/setup`; the AC-STATUS-03 link and each problem message that names a step open `/setup#<step>`. A step whose prerequisite is missing shows that problem with a link to the step that fixes it: the conversations step shows `wa_unlinked` and a link to the WhatsApp step | The fragment never reaches the server: no new route, parameter or validation, and the back button works. After setup the conversations screen is the one the owner comes back to (AC-CHATS-03); the row reaches the others in one click. Opening a step only reads its status and never starts a sign-in, so a link from another website to `/setup#whatsapp` starts nothing (AC-SETUP-08). Locking steps would repeat what the problem codes already say |
| What "works now" means per step | ai: the configured AI answers a test request. whatsapp: wacli's read-only auth status reports linked, and the store can be read. owner: a name was saved from setup (the example file's placeholder never counts). chats: at least one ticked. check: all four checks pass | Each is cheap and checked when its screen opens; only the AI test costs a model call, and only when the owner asks for it |
| Installs from before this change | No inferred progress. The page shows "setup not finished" until the owner clicks through setup once; each already-working step turns done as soon as its screen opens. A Mac install is the same: whoever installs it opens `/setup` at the end and clicks through it. `aos setup` and `aos doctor` write no `setup:*` keys | One install exists today. Inferring progress from files means guessing; clicking through costs the owner a minute. A Mac keeps today's terminal steps (SCOPE-001), so its progress has the same one writer as Windows: setup |
| Long-running sign-ins | The page server starts the CLI with a fixed argument list, reads its output on a thread, and keeps one job per kind (`ai`, `whatsapp`) in memory. Starting again ends the previous job; a job still waiting after 10 minutes is ended and shown as failed. The AI test request has a 2-minute limit. The screens poll every 2 s | No queue or daemon, and no process left behind by an owner who walked away. A job lost when the page server restarts is restarted with one click; finished sign-ins are on disk with each CLI |
| Child processes on Windows | The page server runs windowless (`pythonw`), so every program it starts (both sign-ins, wacli's status, the AI test request) is started with no console window (`CREATE_NO_WINDOW`). A sign-in left running by a page restart (an update, a logoff) is accepted: the new page server does not know it; a leftover `wacli auth` holds the store lock until it exits, which setup shows as `wa_busy` | Without the flag, Windows opens a console window for each console program a windowless process starts: a black window on the owner's screen at every step. Tying children to the page server's life (a job object) costs more code than the rare leftover costs the owner |
| What the sign-ins never write | The QR payload and a code the owner pastes are kept only in the job's memory: never in `errors.log`, the store or any other file. A failed sign-in logs only wacli's `error` event text or the CLI's exit code | The pairing code is what AC-SETUP-08 protects from other devices and websites; a copy on disk is one more place to read it, and `aos bug-report` attaches `errors.log` |

### The two sign-ins

| Decision | Choice | Rationale |
|---|---|---|
| WhatsApp pairing (AC-SETUP-03) | `wacli auth --qr-format text --events --idle-exit 30s --store <whatsapp.json store dir>`. Each `qr_code` event on its stderr replaces the QR; the server turns the payload into an SVG with `segno`. Done when `wacli --read-only --json auth status` reports `authenticated`; the phone number shown is its `phone` | Both flags exist in the pinned v0.19.0 and are wacli's documented way to feed an external renderer. With `--read-only`, status reads the session file without taking the store lock, so it answers while `auth` is still running. WhatsApp rotates the code; polling picks up the new one |
| WhatsApp already linked (AC-SETUP-04, AC-SETUP-06) | Opening the step again re-checks `wacli --read-only --json auth status` and shows the linked phone; no new pairing starts. The connect button shows only while status reports not linked. Linking a different phone stays a support step for whoever installed | Linking another phone needs `wacli logout`, which changes the owner's WhatsApp account (AC-SETUP-04) and is outside setup's allowlist |
| Nothing sent while connecting (AC-SETUP-04) | Setup runs only `wacli auth …` and `wacli --read-only --json auth status`; the conversation list is read from the store file read-only. A test asserts every wacli command setup can start against that allowlist | Pairing adds the linked device; nothing else in that list writes to WhatsApp. The read-only file access is the one the pass already uses |
| Passkey or pairing errors | wacli's `error` event becomes a problem code (below) with one next step ("Tente de novo e escaneie em até 1 minuto", or contact whoever installed) | AC-SETUP-07: no raw output on screen |
| AI sign-in (AC-SETUP-02) | `claude auth login --claudeai`. Any `https://` link the CLI prints is shown as a button; if the CLI asks for a code, a field sends the pasted code to its input. Status from `claude auth status --json`: exit code 0 when signed in, `authMethod` `claude.ai` for a subscription. The step is done only when a test request through the installation's backend returns a valid answer | Covers both ways the CLI can finish (the browser returning to it, or a code to paste); spike S1 says which happens from a windowless process. Both flags are listed by `claude auth login --help` and `claude auth status --help` (CLI 2.1.304) and only restate today's defaults; passing them keeps a future default change from moving the owner to API billing or to text output. The test request is the PRD's definition of done |
| Installation switched to ChatGPT (SCOPE-002) | When `backend.json` is not `claude`, the AI step shows no sign-in, only the test request; a failure sends the owner to whoever installed | Switching and its sign-in are a support step |

### Who the owner is

| Decision | Choice | Rationale |
|---|---|---|
| Language and time zone (AC-SETUP-05) | Until the owner step is saved, setup and the page use the language in `owner.json`: `pt-BR` from the example file `aos init` copies, which both installers run. No Accept-Language rule. The owner screen is prefilled from the browser while the owner step has no `done_at`: `navigator.language` (`pt*` → `pt-BR`, else `en`) and `Intl.DateTimeFormat().resolvedOptions().timeZone`. Afterwards it shows the saved values. The owner can change both; the server checks the zone exists before saving | The server already chooses strings from `owner.json`, so this needs no new code. The installer is Portuguese only, and the PRD shows English to an owner who chose it. The browser reports the computer's settings as an IANA zone, with no Windows-zone mapping code or package |
| Applying a change | The page server reads `owner.json` on each request instead of once at start | A new language or time zone shows at once, with no restart. The file is small |

### Conversations

| Decision | Choice | Rationale |
|---|---|---|
| The list (AC-CHATS-01, AC-CHATS-03) | Read from the wacli store, read-only: people and groups only (`kind` `dm` or `group`; no broadcast, newsletter, status, or the owner's own chat), named by the rule in "A conversation's name"; newest activity first. Search filters in the browser. Ticks come from `whatsapp.json`, so after setup the same screen, reached from "Configuração", shows the current choices | Same access path as the pass, and it works while the pairing's first sync still holds wacli's lock. The pinned v0.19.0 schema has every column used: `chats` (`jid`, `kind`, `name`, `last_message_ts`) and `contacts` (`full_name`, `first_name`, `business_name`, `push_name`). Hundreds of names are small to send whole |
| A conversation's name (AC-CHATS-01, AC-PAGE-04) | One rule in the WhatsApp plugin, used by the setup list and by each pass for the item's title: the chat's name, unless it is empty, `-` or the id itself; else the contact's `full_name`, `first_name`, `business_name`, then `push_name` (not `-`); else, for a phone id (`@s.whatsapp.net`), the number as a phone (`55` + 10 or 11 digits → "+55 61 99999-9999", any other → "+" and the digits); else "Contato sem nome". A ticked id that wacli's `chats` lacks gets no item from the pass, so its stored title stays | wacli writes the id itself as the chat name when it knows none, so "name or id" still shows codes on the page and in Hermes. The contact order is wacli's own (`BestContactName`). `contacts.phone` is the id's number part, so for a hidden id it is not a phone. Nothing keys on a title: Fizzy keys cards by item id and updates a renamed card once, and MCP keeps its fields. Keeping a gone id's title lets the setup list name the conversation the owner must tick again |
| "Still bringing names in" | Shown while the pairing job is still syncing, or while the store's chat count changed in the last 30 s; the list refreshes on each poll | Names arrive after pairing in the first sync; both signals are local and cheap |
| Who is followed (AC-CHATS-02, UI-004) | When collecting finishes, each pass writes to `meta` `followed` the item ids every plugin's poll returned; a pass that stops during collecting leaves the previous list. `build_state` keeps only those; until a pass has written it, everything shows as today. The pass also briefs only followed conversations. An open request on an unticked conversation stays open, with no model call and no Jev call, and the first pass after it is ticked again answers it. A request already answered keeps its reply, shown again when re-ticked. Until a pass has written `followed`, the pass answers every open request, as today | Applies "from the next pass", as the PRD says. The page and `aos mcp` both use `build_state`, so they list the same conversations. Today the pass briefs every conversation in the store, so an unticked one could still cost model calls. Requests have no per-pass or per-day limit, so each open request on an unticked conversation would cost one model call. Its answer would show on no surface, because the page, the report and `aos mcp` all read `build_state`. Nothing is deleted, so re-ticking brings marks, briefs and drafts back |
| A newly ticked conversation | Its first pass reads it back to the plugin's floor window (7 days) instead of from the shared cursor | Today a conversation added after the first pass gets nothing older than the last pass, so the first look would be empty. A message already stored in the same conversation is ignored; one already stored under a hidden id moves its conversation (see "A conversation that moved to its phone id") |
| A ticked conversation wacli no longer has | A ticked id missing from wacli's `chats` is the problem `wa_chat_gone` (fixed on the conversations screen), reported by the pass and by the final check | wacli v0.19.0 moves a chat from its hidden id (`@lid`) to its phone id when it learns the number (`MigrateLIDToPN`: the new row is inserted, the old one deleted). A tick on the old id would then read nothing, with no error, against AC-CHATS-02. The owner ticks it again under the same name, and it comes back as it was (see "A conversation that moved to its phone id") |
| A conversation that moved to its phone id | When the pass reads, under a phone id, a message whose id the store already holds under a hidden-id item (`wa:…@lid`), it moves that whole item to the new id in one transaction: messages, requests, mark, brief, label, draft and Fizzy card. A row the new id already has is kept, and nothing is deleted. It moves only from a hidden id, so a message id seen under two phone ids never merges two conversations. Limit: a conversation with no message in the floor window (7 days) has nothing to match and starts fresh under the new id | wacli v0.19.0 keeps the message id when it moves a chat (`MigrateLIDToPN` changes only the chat id), and the store keeps one row per message id. Without the move, the re-ticked conversation would get nothing back, and UI-004's "brings it back as it was" would fail. The move also avoids a second brief and a second Fizzy card |
| Suggestion (AC-CHATS-04) | A line above the list; no limit on the number ticked | Copy, not a rule |

### Status and problems

| Decision | Choice | Rationale |
|---|---|---|
| Pass record (AC-STATUS-02) | Every `aos run`, including one that stops on a configuration problem or crashes (problem `unknown`), writes `meta` `pass:last` (below). The page words the time in the owner's time zone: today "às 14:35", yesterday "ontem às 22:10", otherwise the date | The page can only say when the last look happened if every pass, failed or not, leaves a record |
| Failed pass (AC-STATUS-02) | `ok` is false when the pass records any problem code. These codes fail a pass, each stopping the whole pass, a whole source, every remaining model call, or a ticked conversation: `config_unreadable`, `wa_unlinked`, `wa_sync_failed`, `wa_chat_gone`, `no_chats`, `ai_signed_out`, `ai_unreachable`, `ai_limit`, `unknown`. `ai_unreachable` means the CLI is missing, or every model call of the pass failed with no answer. One conversation whose brief or request fails on its own (an answer that does not match the schema, a timeout, an error the backend does not recognize) is not a problem: it goes to `errors.log`, the next pass tries it again, and `caught_up` stays false | The page says "worked" only when the owner has nothing to fix or wait for (UI-005). After setup, a failed pass is the only place a problem shows (AC-SETUP-07), so every code the owner must act on or wait out fails it. A single bad answer clears itself on the next pass. Without the "every call failed" rule, an outage the backend does not recognize would show as working forever |
| First look done (AC-PAGE-03) | A pass is caught up when it read every followed conversation and left no brief undone, whether held back by the per-pass and per-day limits or failed on its own (see "Failed pass"). Each caught-up pass writes `pass:looked`, the ids it followed. The first look is done when every conversation ticked in `whatsapp.json` is in `pass:looked`. Only the pass writes the key | "Nada esperando você agora" must not show while briefs are still waiting their turn. Comparing with the ticks themselves, not clearing a flag when the owner ticks, means a pass that started before the tick cannot mark the new conversation as looked at, and a support person's hand edit counts too |
| Next look | Last pass time + the pass interval (5 min), one constant shared with the scheduler | The page says when the assistant will look again without asking Task Scheduler |
| Problems (AC-SETUP-07) | Errors become a problem code where they arise; one catalog in the locale files maps each code to a message and its one next step, plus the setup step that fixes it, if any. The raw text still goes to `errors.log` for `aos bug-report` | One place to write owner-facing text in both languages. The backend recognizes a signed-out CLI by its message, as it already does for usage limits |
| Which problem shows | `problems` keeps every code; the page shows the first in catalog order (Data Models): problems for whoever installed, then those a setup step fixes, in setup order, then the waits, then `unknown` | AC-SETUP-07 gives one thing to try next. A problem the owner can fix comes before a wait, and the setup order matches AC-STATUS-03 |
| Final check (AC-STATUS-01) | Runs the four checks of the PRD's table, each returning working or a problem code | Same codes and messages as a failed pass |

### The page

| Decision | Choice | Rationale |
|---|---|---|
| First screen (AC-PAGE-01, 02) | A row of five section tabs with counts; "Decidir agora" selected on every open (UI-003); the selected section's list below | One click reaches each section and the counts are always visible |
| Each conversation (AC-PAGE-04) | Closed: name, why it is on the list, newest draft, up to three actions (UI-002), and what the PRD's table adds. "Mais opções" opens the rest: full summary, conversation, other actions, "Pedir ao assistente" | The PRD's table, as written |
| Why it is on the list | A reason code from the status: replied after the owner's mark, wait ran out, summary ready | Computed in `build_state` from data it already has |
| Newest draft (AC-PAGE-05) | The later, by the time each was written, of the summary's draft and the last draft written on request. The summary's draft is out of date exactly when the summary is (it does not cover the last message); a draft written on request is out of date when written before the last message's time. "Copiar rascunho" copies it | One draft on the first screen, and it is always the latest. The summary and its draft never disagree about being out of date. A draft on request records no coverage, so a message that reaches the store after the draft but carries an earlier time is the one case it misses |
| Setup unfinished (AC-STATUS-03) | `state.setup.next_step` set → the first screen shows "setup not finished" with a link to that step, in place of the empty-list message and the last-check line | The page reads progress from the same `meta` keys setup writes |

## Interfaces

All routes are on the page server and behind its origin guard. Every `POST` answers `200` with `{"ok": true}` or
`{"problem": "<code>"}` unless shown otherwise; a body that fails validation (an empty name, an unknown time zone, a
conversation id wacli does not have) answers `400` with `{"problem": "invalid_input", "field": "<name>"}`, and the
screen marks that field. `GET /api/setup/chats` answers `{"problem": "wa_unlinked"}` while WhatsApp is not linked.

```
GET  /setup                      setup screens (HTML); the browser-side fragment #ai|#whatsapp|#owner|#chats|#check picks the step
GET  /api/setup                  → SetupState
POST /api/setup/ai/start         start (or restart) the AI sign-in
POST /api/setup/ai/code          {"code": "…"}   the code the CLI asked for
POST /api/setup/ai/test          → {"ok": bool, "problem": code|null}; marks setup:ai on success
POST /api/setup/whatsapp/start   start (or restart) the pairing; {"ok": true} without one when already linked
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
  pass:looked      JSON list of the item ids the last caught-up pass followed; absent = no pass caught up yet

/api/state additions:
  setup: {next_step: step|null}
  pass: {last: pass:last|null, next_at: iso|null, first_look_done: bool}
  items[].reason: "reaberto"|"vencido"|"pronto"|null
  items[].newest_draft: {text, at: iso, from: "brief"|"request", out_of_date: bool}|null

Problem codes (message and next step per language in the locale files; step = the setup step that fixes it):
Order = display priority.
  config_unreadable → none (contact whoever installed)
  store_unreadable → none (contact whoever installed)
  ai_signed_out → ai
  ai_unreachable → ai
  wa_unlinked → whatsapp
  wa_pairing_failed → whatsapp
  wa_busy → whatsapp (a pass holds wacli's store; try again in a minute)
  wa_chat_gone → chats (a ticked conversation moved to a new id; tick it again)
  no_chats → chats
  invalid_input → none (shown on the field)
  wa_sync_failed → none (retry)
  ai_limit → none (wait)
  unknown → none (contact whoever installed)
store_unreadable is found by the page server when it opens the store; it is never in pass:last, which lives in
that store.
```

## Integration Points

- **wacli** (pinned in `tools.py`): `auth --qr-format text --events`, `--read-only --json auth status`; its store file
  read-only.
- **Claude Code CLI**: `auth login --claudeai`, `auth status --json`; the existing `claude -p` call for the test request.
- **Installer** (`install/assistantOS.iss`): the final link points to `/setup`.
- **Hermes**: unchanged; through `aos mcp` it lists only the followed conversations.

## Testing

- Unit: setup progress and next step; config writes keep other keys and reject invalid input; a save retries when the
  replace is refused and succeeds once the file is free; a save that stays refused answers `unknown`, leaves the old
  file unchanged and no temp file behind; two saves at once both leave a valid file; the conversation list
  from a fixture wacli store (kinds, names, order); `followed` filtering in `build_state` (page and MCP agree);
  requests: an open request on an item that is not in `followed` gets no model call and no Jev call, and stays
  `open` with `tries` 0; after the item is in `followed` again, the next pass answers it; with no `followed` key,
  every open request is answered;
  newly ticked conversations read back to the floor; a ticked id missing from the store gives `wa_chat_gone`;
  the name rule from a fixture wacli store with a `contacts` table: chat name; a chat name equal to the id or `-`
  skipped; `full_name`, `first_name`, `business_name`, `push_name` in order (`-` skipped); a Brazilian phone id with
  13 and 12 digits; a non-Brazilian phone id; a `@lid` id with no name gives "Contato sem nome" and never its number;
  `poll` titles equal the setup list's names for the same store; `poll` returns no item for a ticked id missing from
  `chats`, and after a pass its stored title is unchanged and it is in `followed`; in `tests/test_whatsapp.py`, BOB's
  title becomes "+55 61 0000-0002" (the fixture's `wacli_store` gains `contacts` with wacli's column names);
  a re-ticked conversation that moved from its hidden id brings its messages, mark, brief and draft back, and a
  message id seen under two phone ids merges nothing;
  with `owner.json` copied from the example and no `setup:owner`, `GET /setup` with `Accept-Language: en-US` returns
  `<html lang="pt-BR">` and the pt-BR `setup.` strings; after `POST /api/setup/owner` with `"language": "en"`, the
  next `GET /setup` and `GET /` return `lang="en"` and English strings, with no server restart;
  `pass:last` on success, failure and config errors; which codes fail a pass, and the one shown; first-look rules
  under the per-pass limit, after a brief that failed on its own, and for a tick made while a pass runs; newest draft
  and reason; every problem code has text in both languages; the wacli command allowlist; no pairing starts when
  WhatsApp is already linked; every setup step the problem catalog names is one of the five step ids, so each
  `/setup#<step>` link opens a step; opening setup (`GET /setup`, `GET /api/setup`, `GET /api/setup/chats`) starts no
  sign-in job; every child process starts without a console window.
  Sign-in jobs run against fake CLIs that print the real event and prompt shapes, and a test asserts neither the QR
  payload nor a pasted code reaches `errors.log`.
- Windows CI runner: a save succeeds while the target is really held open by a second handle that is released after
  200 ms.
- Windows VM, by hand, once per release candidate: a clean install from `assistantOS-Setup.exe` through every setup
  step with a real phone and a Claude subscription, then restart mid-setup and confirm it resumes at the right
  step. After setup, "Configuração" opens the conversations step with the current ticks, and with WhatsApp unlinked
  that step's link opens the WhatsApp step.

## Open Questions

1. **Spike S1, Windows VM: how `claude auth login` finishes from a windowless background process.** Either the
   browser returns to the CLI by itself, or the CLI prints a link and waits for a pasted code. The design handles
   both; the spike says which screen the owner actually sees, and whether the CLI needs a console at all. It runs in
   the VM, never on Ian's machine. It also confirms `claude auth login --claudeai` and `claude auth status --json` behave as
   their `--help` says on the installed version. **Not run yet:** the VM was unavailable. It must run before the AI step is
   built; the rest of the build does not wait on it.
2. **Fizzy keeps unticked conversations.** The PRD limits the change to the page and Hermes (AC-CHATS-02), so the
   Fizzy surface still syncs every conversation the assistant has read. Left as is; Fizzy is out of scope.
