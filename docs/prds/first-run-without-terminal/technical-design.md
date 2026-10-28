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
| Progress (AC-SETUP-06) | `meta` key `setup:<step>` holds the time the step first showed as working. Whichever call shows a step working writes its key, only when absent (`INSERT OR IGNORE`, so two calls at once keep the first time). The writers are `POST /api/setup` (whatsapp, owner and chats); the pairing job, when status reports linked; `POST /api/setup/whatsapp/start`, when WhatsApp is already linked; `POST /api/setup/ai/test`; `POST /api/setup/owner`; `POST /api/setup/chats`, when the saved ticks work (the chats rule in "What works now"); and `POST /api/setup/check`, for each ai, whatsapp or chats item that passes and for the check step when all pass. No `GET` writes. Setup never clears a key; redoing a step that then fails shows the failure without clearing it. Setup opens at the first step in order `ai, whatsapp, owner, chats, check` without the key | Matches "finished = has ever shown as working". Survives closing the browser and restarting, since it is in the store. GETs stay read-only. The origin guard lets any website send a GET, because it checks only `Host` on reads. Only POSTs, held to the page's own origin, may write |
| Moving between steps (AC-SETUP-01, 06, 07, AC-CHATS-03) | One HTML page. A row of the five steps, each marked done from `done_at`, is always shown, and any step opens at any time; none is locked. The step shown comes from the address fragment (`/setup#chats`), else `next_step`, else, once setup is finished, the conversations step with the current ticks. It changes only when the owner opens setup or follows a link, never on a poll. A step that works shows "Continuar", a link to the next step in order; on the check step that link goes to the page (UI-001). The page's "Configuração" link opens `/setup`; the AC-STATUS-03 link and each problem message that names a step open `/setup#<step>`. A step whose prerequisite is missing shows that problem with a link to the step that fixes it: the conversations step shows `wa_unlinked`, from the whatsapp step's `problem` in `SetupState`, with a link to the WhatsApp step. The list stays below it, and the owner can change it | The fragment never reaches the server: no new route, parameter or validation, and the back button works. After setup the conversations screen is the one the owner comes back to (AC-CHATS-03); the row reaches the others in one click. Opening a step sends `POST /api/setup`, which checks status and never starts a sign-in. A link from another website to `/setup#whatsapp` therefore starts nothing (AC-SETUP-08). Locking steps would repeat what the problem codes already say |
| What "works now" means per step | ai: the configured AI answers a test request. whatsapp: wacli's read-only auth status reports linked, and the store can be read. owner: `owner.json` has a real name: after trimming outer spaces, not empty and not the example file's placeholder, ignoring case. One function decides this for the step and for `POST /api/setup/owner`. chats: at least one ticked, and none gone (the rule in "A ticked conversation wacli no longer has"). The step's `problem` is `no_chats` when nothing is ticked, else `wa_chat_gone`. When the store cannot be read, only the count is checked; the whatsapp step shows that problem. check: all four checks pass. `works` is the last result this page server saw for the step; it is `null` until the step is checked after the server starts | Opening a step sends `POST /api/setup`, which checks whatsapp, owner and chats. The AI test costs a model call, so ai and check are checked only when the owner clicks. wacli's status runs only when a step opens, on the check, every 2 s inside a running pairing job, when the pairing's `wacli auth` exits, and on `whatsapp/start`; a poll of `GET /api/setup` reads the last result and starts no process. A real name typed by whoever installed counts, so an older install is not asked for it again, and its owner screen shows the saved values. The conversations step, the final check's chats item and the pass use one rule, so the step never shows working while every pass fails on a gone tick (AC-SETUP-06, UI-005) |
| Installs from before this change | No progress is inferred at update. When setup opens, the whatsapp, owner and conversations steps each turn done if they already work. The AI and check steps each need a click; one click on the final check marks both. Until then the page shows "setup not finished" with a link to the AI step. A Mac install works the same way: whoever installs it opens `/setup` at the end and clicks through it. `aos setup` and `aos doctor` write no `setup:*` keys | One install exists today. Its files already hold a linked WhatsApp, a name and ticks. Checking them live is not a guess, so the owner clicks only where a check costs a model call. A Mac keeps today's terminal steps (SCOPE-001), so its progress has the same single writer as Windows: setup |
| Long-running sign-ins | The page server starts the CLI with a fixed argument list, reads its output on a thread, and keeps one job per kind (`ai`, `whatsapp`) in memory. Starting again ends the previous job; a job still waiting after 10 minutes is ended and shown as failed. Ending a job ends its whole process tree, as for a timed-out model call (Pass time limit). The AI test request has a 2-minute limit. The screens poll every 2 s | No queue or daemon, and no process left behind by an owner who walked away. A job lost when the page server restarts is restarted with one click; finished sign-ins are on disk with each CLI |
| Child processes on Windows | The page server runs windowless (`pythonw`), so every program it starts (both sign-ins, wacli's status, the AI test request) is started with no console window (`CREATE_NO_WINDOW`). A sign-in left running by a page restart (an update, a logoff) is accepted: the new page server does not know it; a leftover `wacli auth` holds the store lock until it exits, which setup shows as `wa_busy` | Without the flag, Windows opens a console window for each console program a windowless process starts: a black window on the owner's screen at every step. Tying children to the page server's life (a job object) costs more code than the rare leftover costs the owner |
| What the sign-ins never write | The QR payload and a code the owner pastes are kept only in the job's memory: never in `errors.log`, the store or any other file. A failed sign-in logs only wacli's `error` event text or the CLI's exit code | The pairing code is what AC-SETUP-08 protects from other devices and websites; a copy on disk is one more place to read it, and `aos bug-report` attaches `errors.log` |

### The two sign-ins

| Decision | Choice | Rationale |
|---|---|---|
| WhatsApp pairing (AC-SETUP-03) | `wacli auth --qr-format text --events --idle-exit 30s --store <whatsapp.json store dir>`. Each `qr_code` event on its stderr replaces the QR; the server turns the payload into an SVG with `segno`. Done when `wacli --read-only --json auth status` reports `authenticated`; the phone number shown is its `phone` | Both flags exist in the pinned v0.19.0 and are wacli's documented way to feed an external renderer. With `--read-only`, status reads the session file without taking the store lock, so it answers while `auth` is still running. WhatsApp rotates the code; polling picks up the new one |
| WhatsApp already linked (AC-SETUP-04, AC-SETUP-06) | Opening the step again re-checks `wacli --read-only --json auth status` and shows the linked phone; no new pairing starts. The connect button shows only while status reports not linked. Linking a different phone stays a support step for whoever installed | Linking another phone needs `wacli auth logout`, which changes the owner's WhatsApp account (AC-SETUP-04) and is outside setup's allowlist |
| Linking again after the phone removed the device (AC-SETUP-06, AC-SETUP-04) | When the pairing's `wacli auth` exits by itself, the job runs the read-only status. If status reports linked, the job is done. If wacli's `error` event says "store is locked", the step shows `wa_busy` and nothing restarts. Otherwise, a first run that emitted no `qr_code` event is started once more, in the same job, by itself (the count is kept in the job's memory); its QR is shown. If that second run also ends with no QR, the step shows `wa_pairing_failed`. The 10-minute limit counts from the job's start. A job the server ended is never restarted. Setup never runs `wacli auth logout` | If wacli stopped before whatsmeow deleted a removed device, the next `wacli auth` connects with dead credentials and shows no QR. WhatsApp refuses them, whatsmeow deletes the device, and wacli v0.19.0 emits `logged_out`, then exits 0 and prints "Authenticated". Exit code and stdout cannot show this; status can. The next run shows a QR. A locked store is a pass running, and a retry would only hide `wa_busy`. One restart per job, and a new job only on the owner's click, so it cannot loop. Logout adds nothing here and would unlink a device still linked (AC-SETUP-04) |
| Nothing sent while connecting (AC-SETUP-04) | Setup runs only `wacli auth …` and `wacli --read-only --json auth status`; the conversation list is read from the store file read-only. A test asserts every wacli command setup can start against that allowlist | Pairing adds the linked device; nothing else in that list writes to WhatsApp. The read-only file access is the one the pass already uses |
| Passkey or pairing errors | wacli's `error` event becomes a problem code (below) with one next step ("Tente de novo e escaneie em até 1 minuto", or contact whoever installed) | AC-SETUP-07: no raw output on screen |
| AI sign-in (AC-SETUP-02) | `claude auth login --claudeai`. Any `https://` link the CLI prints is shown as a button; if the CLI asks for a code, a field sends the pasted code to its input. Status from `claude auth status --json`: exit code 0 when signed in. The step is done only when a test request through the installation's backend returns a valid answer | Covers both ways the CLI can finish (the browser returning to it, or a code to paste); spike S1 says which happens from a windowless process. Both flags are listed by `claude auth login --help` and `claude auth status --help` (CLI 2.1.304) and only restate today's defaults; passing them keeps a future default change from moving the owner to API billing or to text output. The test request is the PRD's definition of done |
| Which Claude account runs (AC-SETUP-02, AUTH-002) | Every `claude` process the installation starts (each pass's calls, the test request, `claude auth login`, `claude auth status`) runs without `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX` and `CLAUDE_CODE_USE_FOUNDRY` in its environment. The AI step is done when the test request answers (AC-SETUP-02 as written); `authMethod` is not part of done | With `-p`, Claude Code always uses an API key in its environment, ahead of the subscription login. Removing these where `claude` is started covers the test request and every pass; a check at setup cannot, because the scheduled pass runs in its own environment. A CLI with no subscription login then fails the test request, and setup shows the sign-in. `CLAUDE_CODE_OAUTH_TOKEN` stays: it is a subscription token (`authMethod` `oauth_token`), which a `claude.ai`-only rule would wrongly reject. A v0.3.0 install whose passes run on an API key shows `ai_signed_out` after updating, until the owner signs in; the changelog says so |
| Installation switched to ChatGPT (SCOPE-002) | When `backend.json` is not `claude`, the AI step shows no sign-in, only the test request. When the test fails, the step shows the code's message and, as its next step, "contact whoever installed", for every code. A failed pass that links to `/setup#ai` opens this same screen | Switching and its sign-in are a support step |

### Who the owner is

| Decision | Choice | Rationale |
|---|---|---|
| Language and time zone (AC-SETUP-05) | Until the owner step is saved, setup and the page use the language in `owner.json`: `pt-BR` from the example file `aos init` copies, which both installers run. No Accept-Language rule. The owner screen is prefilled from the browser while the owner step does not work (the name in `owner.json` is still the example file's placeholder): `navigator.language` (`pt*` → `pt-BR`, else `en`) and `Intl.DateTimeFormat().resolvedOptions().timeZone`. Afterwards it shows the saved values. The owner can change both; the server checks the zone exists before saving | The server already chooses strings from `owner.json`, so this needs no new code. The installer is Portuguese only, and the PRD shows English to an owner who chose it. The browser reports the computer's settings as an IANA zone, with no Windows-zone mapping code or package. The name check is in the route, not in the `Owner` model, because a fresh install's `owner.json` holds the placeholder and every pass must still read it |
| Applying a change | The page server reads `owner.json` on each request instead of once at start | A new language or time zone shows at once, with no restart. The file is small |

### Conversations

| Decision | Choice | Rationale |
|---|---|---|
| The list (AC-CHATS-01, AC-CHATS-03) | Read from the wacli store, read-only: people and groups, which are rows of `kind` `dm` or `group`, plus a hidden id (`@lid`, `kind` `unknown`) with activity (`last_message_ts` set). Broadcast, newsletter, status, `@bot` and the owner's own chat are left out. The own chat is the row whose `jid` equals `data.linked_jid` from `wacli --read-only --json auth status`; when status reports no link, nothing is left out. The list uses the `linked_jid` from the last auth status the server saw (pairing job, step open, `whatsapp/start` or the check); when it has seen none yet, nothing is left out. Every id ticked in `whatsapp.json` is also listed, whatever its kind (see "Ticked conversations the list would not show"). Rows are named by the rule in "A conversation's name", newest activity first. Search filters in the browser. Ticks come from `whatsapp.json`, so after setup the same screen, reached from "Configuração", shows the current choices. The list is served whatever the link state, so after an unlink the owner still sees and changes their ticks. Before the first pairing, `chats` is empty, so the list holds only the ticked ids, if any, with no problem (see "Ticked conversations the list would not show") | Same access path as the pass, and it works while the pairing's first sync still holds wacli's lock. The pinned v0.19.0 schema has every column used: `chats` (`jid`, `kind`, `name`, `last_message_ts`) and `contacts` (`full_name`, `first_name`, `business_name`, `push_name`). Hundreds of names are small to send whole. wacli v0.19.0 stores a hidden id as `kind` `unknown` until it learns the number; it then moves the chat to the phone id as `dm`. Its archive, pin, mute and unread sync adds rows of `kind` `unknown` that never hold a message. So kind alone hides a person whose number wacli does not know, and "has activity" alone hides a joined group with no stored message, because `wacli auth` adds every joined group with no last message. The own chat is left out because every message in it is the owner's own, so it can never give a request. wacli stores it only under the phone id, in the exact form of `linked_jid`. The status command is already in setup's allowlist; the other source, wacli's session database, holds the WhatsApp keys, and setup never opens it. wacli keeps `chats`, `contacts` and messages in `wacli.db`. An unlink touches only the session: `wacli auth logout` deletes the device in `session.db`, and a removal from the phone writes the `SESSION_REVOKED` file. Nothing in v0.19.0 deletes `chats` on logout. `wacli auth` creates `wacli.db` when it starts. A pass's sync creates it even before any pairing, because it opens the store and only then fails "not authenticated". So the file usually exists, with an empty `chats`, before the first QR. The read-only status never opens it |
| The list keeps filling after pairing (AC-CHATS-01) | Every pass runs the WhatsApp sync, ticks or not: `wacli sync --once --idle-exit 15s --refresh-contacts --store <dir>`. The plugin's "no chats, no sync" early return goes. Before pairing, the sync fails in under a second, and "WhatsApp problems in a pass" records `wa_unlinked` | `wacli auth` stops 30 s after its last event, so history the phone sends later waits for the next connect. Before this change, nothing connected until the owner ticked. A name reaches wacli's `contacts` only with a stored message from that person, or through `--refresh-contacts`. Auth copies contacts once, right after the scan, before WhatsApp has sent any. The flag copies every name the local session holds: the phone's address book (sent after pairing) and push names. It makes no network call and never blanks a name. It runs right after connect, so a name that arrives during a pass lands at the next pass. The flag runs every pass and takes tens of milliseconds, but each run rewrites the whole `contacts` table; that is accepted over keeping pass state in the plugin to run it only while names arrive |
| Ticked conversations the list would not show | The list also includes every id ticked in `whatsapp.json`. A ticked id wacli has is named by the usual rule, with `kind` `group` for `@g.us` and `person` otherwise. A gone tick (see "A ticked conversation wacli no longer has") is shown ticked, with the `wa_chat_gone` message. Its name is the store item's title, unless that title is the id itself or no item exists; in that case it is "Conversa que não existe mais". While the store has no file or an empty `chats`, a tick is shown ticked with no problem. It is named by the store item's title, unless that title is the id itself or no item exists; then it gets the name rule's fallback for its id (the phone number, else "Contato sem nome"). Rows with a problem come first. A row stays ticked until the owner unticks it | AC-CHATS-03 shows the current choices, and the pass reads every ticked id whatever its kind. A hidden tick would be dropped at the next save without the owner unticking it. Before this change ticks were typed by hand from `wacli chats list`, so any kind, or a mistyped id, can be there. Such a dead id reads nothing, with no error, today; after the update each pass fails with `wa_chat_gone` until the owner unticks it, and the changelog says so. v0.3.0 rewrote the item title to the raw id once a chat was gone, so that title is never shown. Before pairing, an empty `chats` says nothing about any tick, so none is gone. After pairing, a missing tick is usually a moved or dead id; one that has not arrived yet is the limit in "A ticked conversation wacli no longer has" |
| A conversation's name (AC-CHATS-01, AC-PAGE-04) | One rule in the WhatsApp plugin, used by the setup list and by each pass for the item's title. For a person (any id but `@g.us`): the contact's `full_name`, `first_name`, `business_name`, then `push_name` (not `-`); else the chat's name, unless it is empty, `-` or the id itself. For a group: the chat's name, unless it is empty, `-` or the id itself. Else, for a phone id (`@s.whatsapp.net`), the number as a phone (`55` + 10 or 11 digits → "+55 61 99999-9999", any other → "+" and the digits); else "Contato sem nome". A ticked id that wacli's `chats` lacks gets no item from the pass, so its stored title stays. The exception is a title equal to the id itself, which v0.3.0 wrote for such an id. The pass replaces it once with "Conversa que não existe mais", in the owner's language. The pass creates no item for a gone id | wacli writes the id itself as the chat name when it knows none, so "name or id" still shows codes on the page and in Hermes. The contact order is wacli's own (`BestContactName`). `contacts.phone` is the id's number part, so for a hidden id it is not a phone. Nothing keys on a title: Fizzy keys cards by item id and updates a renamed card once, and MCP keeps its fields. Keeping a gone id's title lets the setup list name the conversation the owner must tick again. The page and `aos mcp` show the stored title, and an id is never displayed. wacli fixes a person's chat name when it stores a message, from what it knew then: often a push name or the id. The address-book name arrives later, and only the contact row gets it. Reading the contact first is wacli's own order (`ResolveChatName`, `BestContactName`) with newer data |
| "Still bringing names in" | The conversations step shows "WhatsApp is still bringing your conversations in" while `GET /api/setup/chats` answers `syncing` true. That step polls `GET /api/setup/chats` every 2 s, and the list refreshes on each poll. `syncing` is true in three cases. (1) The pairing's `wacli auth` process is still running. (2) That process ended after linking, and there is no `pass:last` whose `at` is at least one pass interval (5 min) after the end. (3) The set of ids and names differs from the set this server built for the previous GET, for 30 s after the change | Auth copies names before any arrive. The first pass after auth copies what auth received, and the second pass copies what arrived during the first. A failed pairing brings nothing in. The end time is kept in memory only, so after a page restart only (3) remains. A set, not an order, catches names that arrive for listed chats and ignores a message that only reorders. Every input is in memory or `meta`, so GETs stay read-only and start no process. Limit: between passes, the screen cannot know whether more is coming |
| Who is followed (AC-CHATS-02, UI-004) | When collecting finishes, each pass writes to `meta` `followed` the item id (`wa:<id>`) of every conversation ticked in `whatsapp.json`, including one wacli no longer has (`wa_chat_gone`); a pass that stops during collecting leaves the previous list. `build_state` keeps only those; until a pass has written it, everything shows as today. The pass also briefs only followed conversations. An open request on an unticked conversation stays open, with no model call and no Jev call, and the first pass after it is ticked again answers it. A request already answered keeps its reply, shown again when re-ticked. Until a pass has written `followed`, the pass answers every open request, as today | Applies "from the next pass", as the PRD says. The page and `aos mcp` both use `build_state`, so they list the same conversations. Today the pass briefs every conversation in the store, so an unticked one could still cost model calls. Requests have no per-pass or per-day limit, so each open request on an unticked conversation would cost one model call. Its answer would show on no surface, because the page, the report and `aos mcp` all read `build_state`. Nothing is deleted, so re-ticking brings marks, briefs and drafts back. Only unticking takes a conversation off the page (UI-004). A conversation that WhatsApp moved keeps its summary and pending decision on screen until the owner acts, and the failed pass says what to do. After the move, `wa:<hidden id>` has no item left, so nothing is listed twice |
| A newly ticked conversation | Its first pass reads it back to the plugin's floor window (7 days) instead of from the shared cursor | Today a conversation added after the first pass gets nothing older than the last pass, so the first look would be empty. A message already stored in the same conversation is ignored; one already stored under a hidden id moves its conversation (see "A conversation that moved to its phone id") |
| A ticked conversation wacli no longer has | A tick is gone when the wacli store was read, its `chats` has at least one row, and no row has the tick's id. That is the problem `wa_chat_gone`, fixed on the conversations screen. One function in the WhatsApp plugin decides it for the pass, the conversations list, the conversations step and the final check's chats item. A missing store file, a store that cannot be read, or an empty `chats` makes no tick gone. An empty `chats` is a store before pairing, which a pass's sync creates. It stays ticked and followed, so its summary and any pending decision stay on the page. Every pass fails with `wa_chat_gone` until the owner unticks it on the conversations screen, or wacli stores a row for its id. The pass can still be caught up (see "First look done") | wacli v0.19.0 moves a chat from its hidden id (`@lid`) to its phone id when it learns the number (`MigrateLIDToPN`: the new row is inserted, the old one deleted). A tick on the old id would then read nothing, with no error, against AC-CHATS-02. The owner ticks it again under the same name, and it comes back as it was (see "A conversation that moved to its phone id"). Every pass syncs, ticks or not, and an unlinked sync creates `wacli.db` with an empty `chats`. Judging ticks against it would fail every pass before pairing with `wa_chat_gone` on top of `wa_unlinked`. Limit: a tick typed before the first pairing shows as gone until wacli stores a row for its chat. A row comes from a message, the conversation's unread state in WhatsApp's history, an archive, pin or mute change, or, for a group, the pairing itself. A conversation the phone does not send in its history, such as a contact never written to, stays gone until a message arrives. The problem then clears with no action; the owner can untick it or wait. Holding the problem while setup shows "still bringing your conversations in" was rejected. That state lives only in the page server's memory, so the pass could not use the same rule, and the step would say working while every pass fails (AC-SETUP-06, UI-005) |
| A conversation that moved to its phone id | When the pass reads, under a phone id, a message whose id the store already holds under a hidden-id item (`wa:…@lid`), it moves that whole item to the new id in one transaction: messages, requests, mark, brief, label, draft and Fizzy card. A row the new id already has is kept, and nothing is deleted. It moves only from a hidden id, so a message id seen under two phone ids never merges two conversations. Limit: a conversation with no message in the floor window (7 days) has nothing to match and starts fresh under the new id | wacli v0.19.0 keeps the message id when it moves a chat (`MigrateLIDToPN` changes only the chat id), and the store keeps one row per message id. Without the move, the re-ticked conversation would get nothing back, and UI-004's "brings it back as it was" would fail. The move also avoids a second brief and a second Fizzy card |
| Suggestion (AC-CHATS-04) | A line above the list; no limit on the number ticked | Copy, not a rule |

### Status and problems

| Decision | Choice | Rationale |
|---|---|---|
| Pass record (AC-STATUS-02) | Every `aos run`, including one that stops on a configuration problem or crashes (problem `unknown`), writes `meta` `pass:last` (below) when it ends. `at` is the time the pass started, taken before it reads the configuration. A pass that is killed or loses power writes nothing, so the page keeps the previous record. The page words the time in the owner's time zone: today "às 14:35", yesterday "ontem às 22:10", otherwise the date. If the configured backend cannot be built (a `backend.json` kind this version cannot run, such as `gemini`), the pass records `config_unreadable` and makes no model call | The page can only say when the last look happened if every pass, failed or not, leaves a record. The pass reads the messages at its start, so a message that arrives while it writes briefs is not on the list. The start time never claims more than the pass saw. A kind this version cannot run is a configuration fault that only whoever installed can fix; `unknown` stays for crashes and a missing CLI |
| Failed pass (AC-STATUS-02) | `ok` is false when the pass records any problem code. These codes fail a pass: `config_unreadable`, `wa_unlinked`, `wa_sync_failed`, `wa_chat_gone`, `no_chats`, `ai_signed_out`, `ai_unreachable`, `ai_limit`, `unknown`. `ai_unreachable` means the pass made at least one model call, every call got no answer from the model (`NoAnswer`: the CLI timed out or ended in an error), the backend did not report itself signed out, and the configured backend's last two calls in `runs` both failed. With two or more calls in the pass, those are the pass's own calls. With one call, they are that call and the call before the pass: the configured backend's last `runs` row whose `at` is before the pass's start. Only rows whose `backend` is the configured kind count, the AI test request's included; Jev's rows (`backend` `jev`) never count. An answer that does not match the schema also writes `ok` 0 in `runs`. A pass with no model call never records an AI code. One conversation whose brief or request fails on its own (an answer that does not match the schema, or a call with no answer in a pass that does not record `ai_unreachable`) is not a problem: it goes to `errors.log`, and the next pass tries it again. For the first look, it counts as looked at (see "First look done"). `no_chats` is recorded while collecting, after the WhatsApp sync, when `whatsapp.json` `chats` is empty. It stops only the WhatsApp read, never the sync | The page says "worked" only when the owner has nothing to fix or wait for (UI-005). After setup, a failed pass is the only place a problem shows (AC-SETUP-07), so every code the owner must act on or wait out fails it. A single bad answer clears itself on the next pass. Without the no-answer rule, an outage the backend does not recognize would show as working forever. Two failures in a row of the configured backend mark an outage, whether they fall in one pass or across two (UI-005). A pass whose only call fails once worked; when the call before it failed too, the pass failed. A pass whose two or more calls all got no answer failed and is not caught up, so the first look waits. A pass where some calls answered worked. Jev is another service, so its rows say nothing about the model. A no-answer call right after an answer off the schema can record `ai_unreachable` once; telling the two apart in `runs` would need a new column. Counting only calls with no answer keeps one conversation whose answer never fits the schema from blaming the AI. A pass that stopped after an answer and then two calls with no answer still worked. The next pass makes at most two calls and records `ai_unreachable`, or `ai_signed_out` when `signed_in()` says so |
| First look done (AC-PAGE-03) | A pass is caught up when it records no problem other than `wa_chat_gone`, and it tried every due brief. A brief left to the per-pass or per-day limit, to the pass time limit, or to the stop after a 401, a 429 or two calls with no answer, was not tried. A brief that failed on its own was tried (see "Failed pass"). Each caught-up pass writes `pass:looked`, the ids it followed. The first look is done when every conversation ticked in `whatsapp.json` is in `pass:looked`. Only the pass writes the key | "Nada esperando você agora" must not show while briefs still wait their turn, or while the AI or WhatsApp kept the pass from looking. A brief that fails on its own in every pass has had its turn. Briefs have no retry cap, so counting it as not looked at would keep "still looking for the first time" on screen forever. Its conversation has no current brief. If never marked, it waits in "Em aberto"; if reopened or overdue, it stays in "Decidir agora". So the empty-list message never hides it. A gone tick has nothing to read and already fails the pass, so `ok` and `caught_up` are independent. Comparing with the ticks themselves, not clearing a flag when the owner ticks, means a pass that started before the tick cannot mark the new conversation as looked at. A support person's hand edit counts too |
| Next look (AC-PAGE-03) | `next_at` = `pass:last.at` + the pass interval (5 min), one constant shared with the scheduler; null when there is no `pass:last`. When `next_at` is null or past, the page says "Próxima verificação em instantes" ("Next check shortly"); otherwise it says "Próxima verificação às 14:40" ("Next check at 2:40 PM") | Both schedulers count the interval between start times, so start + 5 min is the next firing. A pass still running, a long pass, a sleeping computer or a skipped run only delays that firing. "Em instantes" is true in each of those cases, and a time already gone by is never shown |
| Problems (AC-SETUP-07) | Errors become a problem code where they arise; one catalog in the locale files maps each code to a message and its one next step, plus the setup step that fixes it, if any. The raw text still goes to `errors.log` for `aos bug-report` | One place to write owner-facing text in both languages. The backend recognizes a signed-out or limited CLI by the HTTP status in its JSON result. When every call gets no answer, `claude auth status` tells a sign-out apart (see "AI problems in a pass") |
| WhatsApp problems in a pass | After every sync, whatever its exit code, and also when the store is locked, the pass runs `wacli --read-only --json auth status --store <dir>`. If `data.authenticated` is false, the code is `wa_unlinked`, whatever the sync did. Otherwise: a sync that worked, or that found the store locked, records no code; a failed sync or a sync timeout records `wa_sync_failed`. If the status command itself fails, the sync result alone decides, and the failure goes to `errors.log`. If wacli is missing, the code is `unknown`, because only whoever installed can fix it. The raw last line still goes to `errors.log`. The pass then reads what the store has, as today. If `poll` cannot read the store, the WhatsApp source stops for this pass. It keeps the code the sync check already found, or else records `wa_sync_failed`. The rest of the pass goes on | When the phone removes the device during a sync, wacli v0.19.0 stops the sync, writes a `SESSION_REVOKED` file and exits 0 (docs/sync.md). A check made only after a failed sync would call that pass "worked". The status reads the file, and also a removed device row, as not linked, in JSON, without the store lock. One short local call per pass is cheap. A status failure alone does not fail a pass that synced |
| AI problems in a pass | The Claude backend reads its JSON result even when the CLI exits non-zero. If `api_error_status` is 401, it raises `SignedOut`, a `BackendError`; the code is `ai_signed_out`. If it is 429, it raises `QuotaExceeded`; the code is `ai_limit`. Both stop every remaining model call of the pass. The text match stays for Codex. A call that gets no reply from the model raises `NoAnswer`, a `BackendError`. That covers a timeout, a non-zero exit with no usable result, and any other `is_error` result. A CLI that is not on the path raises `NotInstalled`, a `BackendError`, before any process starts. The code is `unknown`, at the first call, and it stops every remaining model call of the pass. A missing wacli gives `unknown` too. A reply that does not match the schema is still an answer. So is a Claude result with subtype `error_max_structured_output_retries`, whatever its `is_error`, and one with `is_error` false and no `structured_output`: the model replied, but not in the schema. Sometimes the pass made model calls and every one raised `NoAnswer`. Then the pass asks the backend once whether it is signed in (`Backend.signed_in()`). For Claude, that runs `claude auth status --json`. Exit 1 gives `ai_signed_out`. Any other result, including `None` (Codex cannot tell), leaves it to the "Failed pass" rule. Two `NoAnswer` in a row in a pass also stop every remaining model call of the pass, briefs and requests alike. This is the same stop as a 401 or a 429. Any answer, one off the schema included, starts the count again. The count carries from the briefs to the requests. The pass then applies the "Failed pass" rule as usual. A brief or request left by this stop is not tried. A request left this way does not count as a failed try | Claude's sign-out and limit texts change with the cause and the version, so the code reads statuses, not words. The server refusing a token is a 401 in the result. With no credentials, or a session that could not be refreshed, the CLI never reaches the API: the status is empty, and the CLI clears the stored token. `auth status` then exits 1 (Claude Code 2.1.312: it exits 0 only when a usable credential is stored). A usage limit is a 429 whose text ("You've hit your session limit") no keyword list matches. A sign-out and a limit show at once, because the status is certain. An outage needs two failures in a row, so one failed call does not fail the pass (UI-005). The installer installs Claude Code, so a missing CLI is an install fault, not a sign-in. The backend finds it before it starts a process, so the code is certain at the first call. A call with no answer can take the full 10-minute limit, because Claude Code retries on its own. Windows ends a pass after 30 minutes, and a pass that is ended leaves no record. Two in a row is the outage signal (UI-005), so the stop agrees with "Failed pass". When the first two calls get no answer, the pass ends with two calls, all with no answer, and it fails. When an answer came first, the pass worked, and the next pass reports the outage. Two in total would stop an AI that only fails now and then |
| Pass time limit (AC-STATUS-02) | A model call or a Jev call starts only in the first 15 minutes of a pass, counted from its start (`pass:last.at`). Briefs, requests and labels left by this limit are not tried. They record no problem code and wait for the next pass. A request left this way does not count as a failed try. Each model call keeps its 10-minute limit. `signed_in()` has a 30-second limit, and when it runs out it counts as `None`. When a call runs out of time on Windows, its whole process tree is ended (`taskkill /F /T /PID`, started with no console window), then its output is read. The backend sets no Claude timeout or retry variable | Windows ends a pass after 30 minutes (`ExecutionTimeLimit`), and a pass that is ended writes no record. Slow answers, and calls that alternate between an answer and no answer, never meet the two-in-a-row stop. Requests have no cap, and each one can also cost a Jev call. A call started just before 15 minutes ends by 25 minutes, and the sign-in check by 25½. That leaves 4½ minutes for the report and the record. 15 minutes is a judgment: 30, less one 10-minute call, the sign-in check, and room for the record. On Windows, Python's timeout ends only the direct child and then waits for the pipes. An npm install of Claude Code, which the installer keeps, or Codex, runs through a `.cmd` file. Its real CLI would keep the pipes open through its own retries, up to about 10 minutes each. With the tree kill, our own 10-minute limit bounds each call whatever the CLI's own retries do. Claude's `API_TIMEOUT_MS` and `CLAUDE_CODE_MAX_RETRIES` add nothing: the first limits only the wait for headers, the second changed meaning between versions, and neither limits how many calls a pass makes. On macOS, launchd ends no pass, so the limit only keeps the next look from waiting |
| AI test request (AC-SETUP-02, AC-STATUS-01) | `POST /api/setup/ai/test` and the check's `ai` item run one function. It makes one call through the configured backend's `ask`, with job `setup`, a fixed short prompt and a one-field model (`SetupTest`, `ok: bool`), within the 2-minute limit. It classifies that call alone. Any answer that matches `SetupTest` is working, `{"ok": false}` included. A 401 gives `ai_signed_out`, and a 429 gives `ai_limit`. A CLI that is not installed gives `unknown`. A `backend.json` kind this version cannot run, or a configuration that cannot be read, gives `config_unreadable`, and no call is made. On `NoAnswer`, the server asks `signed_in()` once: false gives `ai_signed_out`, and true or `None` gives `ai_unreachable`. An answer that does not match the schema gives `ai_unreachable`. Like every call, it writes one `runs` row (job `setup`, `backend` the configured kind) | Done is a valid answer (AC-SETUP-02), so an answer off the schema fails the test. A CLI that was never signed in returns `is_error` with no `api_error_status`. Without `signed_in()`, setup would show "unreachable" in place of the sign-in the AI step offers. The pass's two-in-a-row rule needs a history that one click does not have. The test counts in that rule: a working test resets it, and a failed one is the first failure. The per-day brief cap counts only job `brief`, so the test never takes a brief's place, and the daily report shows its cost on its own line. Codex's `signed_in()` is `None`: `codex login status` says "Not logged in" for a provider key that works, and for a non-Claude backend both codes go to whoever installed |
| Which problem shows | `problems` keeps every code; the page shows the first in catalog order (Data Models): problems for whoever installed, then those a setup step fixes, in setup order, then the waits, then `unknown` | AC-SETUP-07 gives one thing to try next. A problem the owner can fix comes before a wait, and the setup order matches AC-STATUS-03 |
| Final check (AC-STATUS-01) | Runs the four checks of the PRD's table, each returning working or a problem code. The chats item uses the chats rule in "What works now": `no_chats` when nothing is ticked, `wa_chat_gone` when a tick is gone. Both send the owner to the conversations screen, the PRD table's destination for that item | Same codes and messages as a failed pass. The PRD row names only the count, but AC-SETUP-06 and UI-005 call for the stricter item: a check that said working while every pass fails on a gone tick would break both |

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
`{"problem": "<code>"}` unless shown otherwise; a body that fails validation (an empty name or the example file's placeholder, an unknown time zone, a
conversation id that is neither in the list nor already ticked in `whatsapp.json`) answers `400` with `{"problem": "invalid_input", "field": "<name>"}`, and the
screen marks that field. `GET /api/setup/chats` reads only and starts no process. It lists what the wacli store file
holds, whether WhatsApp is linked or not. When the file does not exist yet, or its `chats` is empty (before the first
pairing), the list holds only the ticked ids, with no problem; with no ticks it is empty. When the file exists but
cannot be read, it answers `{"problem": "wa_sync_failed"}`, and the raw error goes to `errors.log`.

```
GET  /setup                      setup screens (HTML); the browser-side fragment #ai|#whatsapp|#owner|#chats|#check picks the step
GET  /api/setup                  → SetupState; reads only (the screens poll it every 2 s)
POST /api/setup                  → SetupState; checks whatsapp, owner and chats; marks each that works (sent whenever a step opens)
POST /api/setup/ai/start         start (or restart) the AI sign-in
POST /api/setup/ai/code          {"code": "…"}   the code the CLI asked for
POST /api/setup/ai/test          → {"ok": bool, "problem": code|null}; marks setup:ai on success
POST /api/setup/whatsapp/start   start (or restart) the pairing; {"ok": true} without one when already linked, and marks setup:whatsapp
POST /api/setup/owner            {"name": "…", "language": "pt-BR"|"en", "timezone": "<IANA>"}; saves the trimmed name and
                                   marks setup:owner; a name the owner rule rejects answers 400 invalid_input, field name, and
                                   nothing is written
GET  /api/setup/chats            → {"syncing": bool, "chats": [Chat]}, or {"problem": "wa_sync_failed"} when the store file cannot be read
POST /api/setup/chats            {"ticked": ["<jid>", …]}; saves, then marks setup:chats when the saved ticks work
                                   (the chats rule)
POST /api/setup/check            → {"items": [{"id": "ai"|"whatsapp"|"chats"|"config", "ok": bool, "problem": code|null}]};
                                   marks setup:<id> for each ok ai|whatsapp|chats item, and setup:check when all are ok
GET  /api/state                  existing body + "setup", "pass" and per-item "reason", "newest_draft" (below)
```

## Data Models

```
SetupState:
  next_step: "ai"|"whatsapp"|"owner"|"chats"|"check"|null    null = setup finished
  steps: [{id, done_at: iso|null, works: bool|null, problem: code|null}]   works = the last result this page server saw; null = not checked since the server started
  owner: {name|null, language, timezone}
  ai: {kind: "claude"|"codex"|"gemini", job: Job|null}
  whatsapp: {job: Job|null, phone: string|null}

Job:
  state: "running"|"waiting_owner"|"done"|"failed"
  link: url|null          AI: the sign-in page to open
  needs_code: bool        AI: the CLI is waiting for a pasted code
  qr_svg: string|null     WhatsApp: the current QR, rendered on the server
  problem: code|null

Chat: {id: jid (never displayed), name, kind: "person"|"group", last_at: iso|null, ticked: bool, problem: "wa_chat_gone"|null}

SetupTest: {ok: bool}   the output model of the AI test request

meta keys (store):
  setup:<step>     iso time the step first showed working
  followed         JSON list of the item ids (wa:<id>) of every conversation ticked when the last pass collected,
                   including one wacli no longer has
  pass:last        JSON {at: iso, ok: bool, problems: [code], caught_up: bool}
                   at: when the pass started; caught_up: no problem but wa_chat_gone, and no due brief left to a
                   limit or a stop (First look done)
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
  wa_chat_gone → chats (a ticked conversation moved to a new id or no longer exists; untick it, and tick it again
                 under its name to keep following it)
  no_chats → chats
  invalid_input → none (shown on the field)
  wa_sync_failed → none (retry)
  ai_limit → none (wait)
  unknown → none (contact whoever installed)
store_unreadable is found by the page server when it opens the store; it is never in pass:last, which lives in
that store.
```

## Integration Points

- **wacli** (pinned in `tools.py`): `auth --qr-format text --events`, `--read-only --json auth status` (in setup, and
  in every pass after its sync; its output is `{"success", "data": {"authenticated", "phone"?, …}, "error"}`; a
  revoked session gives `authenticated` false even when `sync` exits 0); the pass: `sync --once --idle-exit 15s
  --refresh-contacts --store <dir>`, every pass, ticks or not; its store file read-only.
- **Claude Code CLI**: `auth login --claudeai`, `auth status --json` (exit 0 only when signed in; at most once per
  pass, when every model call got no answer, and once per test request that got no answer); the existing `claude -p`
  call, for each pass and for the test request, whose JSON result is read on any exit code (`is_error`,
  `api_error_status`, `result`). Every `claude` process starts
  without the API-key and cloud-account variables ("Which Claude account runs", AUTH-002).
- **Installer** (`install/assistantOS.iss`): the final link points to `/setup`.
- **Hermes**: unchanged; through `aos mcp` it lists only the followed conversations.

## Testing

- Unit: setup progress and next step; config writes keep other keys and reject invalid input; a save retries when the
  replace is refused and succeeds once the file is free; a save that stays refused answers `unknown`, leaves the old
  file unchanged and no temp file behind; two saves at once both leave a valid file; the conversation list
  from a fixture wacli store whose `chats` has `kind` and `last_message_ts`: a dm, a group with no
  `last_message_ts` and a `@lid` of kind `unknown` with activity are listed; a `@lid` without activity, a
  `@s.whatsapp.net` of kind `unknown` without activity, and a broadcast, a newsletter and a `@bot`, each with
  activity, are not; the row whose jid equals the fixture's `linked_jid` is not listed, and every row is kept when
  status reports not linked; a ticked broadcast and a ticked `@lid` without activity are listed and survive a save
  with no change; a ticked id missing from `chats` is listed first, with `wa_chat_gone`, named from its stored title,
  or "Conversa que não existe mais" when that title is the id or no item exists, and never with a jid; with no store
  file, and with a store file whose `chats` is empty, the ticks `5561999990001@s.whatsapp.net` and `x@g.us` with no
  stored item are listed ticked, with no problem, as "+55 61 99999-0001" and "Contato sem nome"; a tick with a stored
  item titled "Obra" is listed as "Obra"; no jid is shown; a POST with
  an id neither listed nor ticked answers `400`; `followed` filtering in `build_state` (page and MCP agree);
  requests: an open request on an item that is not in `followed` gets no model call and no Jev call, and stays
  `open` with `tries` 0; after the item is in `followed` again, the next pass answers it; with no `followed` key,
  every open request is answered;
  newly ticked conversations read back to the floor; a ticked id missing from a `chats` that has rows gives
  `wa_chat_gone`. With an empty `chats` and a fake wacli that reports not linked, a pass with two ticks records
  `wa_unlinked` and no `wa_chat_gone`;
  the name rule from a fixture wacli store with a `contacts` table: for a person, `full_name`, `first_name`,
  `business_name`, `push_name` in order (`-` skipped), then the chat name; a chat name equal to the id or `-` skipped; a Brazilian phone id with
  13 and 12 digits; a non-Brazilian phone id; a `@lid` id with no name gives "Contato sem nome" and never its number;
  a dm whose `chats.name` is "Zé" and whose `contacts.full_name` is "José Silva" gives "José Silva"; a dm with no
  contact row and `chats.name` "Zé" gives "Zé"; a `@lid` row whose chat name is the id and whose `push_name` is "Ana"
  gives "Ana"; a group whose `chats.name` is "Obra" gives "Obra";
  `poll` titles equal the setup list's names for the same store; `poll` returns no item for a ticked id missing from
  `chats`, and after a pass it is in `followed`; with a stored item, `build_state` (page and MCP) lists that item,
  a stored title equal to the id becomes "Conversa que não existe mais", and any other stored title is kept; a gone
  id with no stored item gets no item; after the owner unticks it, the next pass drops it from `followed` and from
  `build_state`; in `tests/test_whatsapp.py`, BOB's
  title becomes "+55 61 0000-0002" (the fixture's `wacli_store` gains `contacts` with wacli's column names);
  a re-ticked conversation that moved from its hidden id brings its messages, mark, brief and draft back, and a
  message id seen under two phone ids merges nothing;
  with `owner.json` copied from the example and no `setup:owner`, `GET /setup` with `Accept-Language: en-US` returns
  `<html lang="pt-BR">` and the pt-BR `setup.` strings; after `POST /api/setup/owner` with `"language": "en"`, the
  next `GET /setup` and `GET /` return `lang="en"` and English strings, with no server restart;
  `pass:last` on success, failure and config errors; which codes fail a pass, and the one shown;
  `pass:last.at` is the start of the pass: with a clock that moves from 14:35 to 14:42 during the pass, `at` is 14:35
  and `next_at` is 14:40; a pass that raises after it starts records `at` = its start time with `["unknown"]`; with
  the clock at 14:39 the page shows "Próxima verificação às 14:40"; at 14:41, or with no `pass:last`, it shows
  "Próxima verificação em instantes", and the English page shows "Next check shortly";
  first-look rules: a pass that leaves a due brief to the per-pass limit, or to the per-day limit, is not caught up;
  a brief whose answer does not match the schema in every pass does not block the first look: each pass logs it to
  `errors.log` and tries it again, the pass is caught up with `ok` true, `first_look_done` is true, and the
  conversation is in "Em aberto" when never marked and in "Decidir agora" when reopened, with `brief_current` false;
  a pass that records `ai_unreachable`, `ai_signed_out`, or `ai_limit` before a due brief is not caught up; a pass
  whose only problem is `wa_chat_gone` is caught up with `ok` false; a tick made while a pass runs is not in
  `pass:looked`; newest draft and reason; every problem code has text in both languages; the wacli command allowlist; no pairing starts when
  WhatsApp is already linked; every setup step the problem catalog names is one of the five step ids, so each
  `/setup#<step>` link opens a step; opening setup (`GET /setup`, `GET /api/setup`, `POST /api/setup`,
  `GET /api/setup/chats`) starts no sign-in job; every child process starts without a console window; every `claude` child process (pass calls, test
  request, `auth login`, `auth status`) has none of `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`,
  `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`, `CLAUDE_CODE_USE_FOUNDRY` in its environment when the parent
  has them all set, and keeps `CLAUDE_CODE_OAUTH_TOKEN`. No `claude` child gets `API_TIMEOUT_MS` or
  `CLAUDE_CODE_MAX_RETRIES` from the backend.
  `GET /api/setup` writes no `setup:*` key and starts no child process; a fake wacli records no call. `POST /api/setup`
  with a fake wacli that reports linked, a real name, one tick and no keys writes `setup:whatsapp`, `setup:owner` and
  `setup:chats`; `setup:ai` and `setup:check` stay absent, and `next_step` is `"ai"`. The same call with the example
  `owner.json` writes no `setup:owner`, and owner `works` is false. A second `POST /api/setup` keeps the first time;
  with wacli then unlinked, the key stays and whatsapp `works` is false. A pairing job whose fake status turns linked
  writes `setup:whatsapp` with no `POST /api/setup`. `POST /api/setup/check` with every item ok writes `setup:ai`,
  `setup:whatsapp`, `setup:chats` and `setup:check`. The placeholder the owner rule rejects equals the name in
  `owner.example.json`. `POST /api/setup/owner` with the name `""`, `"   "`, the example file's name, or the same name
  in lower case answers `400` with `field` `name`, writes no `setup:owner`, and leaves `owner.json` unchanged. With
  `" Ana Lima "`, it saves `"Ana Lima"` and writes `setup:owner`. `POST /api/setup` with a foreign `Origin` gets `403` and writes no key.
  With a fixture store and two ticks, one of them missing from `chats`, `POST /api/setup` gives chats `works` false
  and `problem` `wa_chat_gone`, and writes no `setup:chats`. `POST /api/setup/check` gives the chats item
  `{"ok": false, "problem": "wa_chat_gone"}` and writes neither `setup:chats` nor `setup:check`. `POST /api/setup/chats`
  that keeps the gone tick answers `{"ok": true}` and writes no `setup:chats`. After it drops the gone tick, chats
  `works` is true and `setup:chats` is written. With no tick, the problem is `no_chats`. With two ticks and a store file
  whose `chats` is empty, chats `works` is true and no tick is gone. With ticks and a store file that cannot be read,
  chats `works` is true and no tick is reported gone.
  With a fixture store, two ticks and a fake wacli whose status reports not linked, send `POST /api/setup`. Then
  `GET /api/setup` shows the whatsapp step with `works` false and `problem` `wa_unlinked`. `GET /api/setup/chats`
  answers no `problem` and lists the fixture's chats with both ticks. `POST /api/setup/chats` with one tick removed
  answers `{"ok": true}` and changes only `chats` in `whatsapp.json`. The fake wacli records no call from either GET.
  With no store file and `chats` `[]`, `GET /api/setup/chats` answers `{"syncing": false, "chats": []}`. With a store
  file that cannot be read, it answers `{"problem": "wa_sync_failed"}`.
  The fake Claude CLI prints its JSON result on stdout, exits 1 and leaves stderr empty, as the real one does on an
  error. With `api_error_status` 401, the code is `ai_signed_out` and no more calls run in the pass. With 429 and
  `result` "You've hit your session limit · resets 3pm", the code is `ai_limit` and no more calls run. Sometimes every
  call fails with a null status and the result "Not logged in · Please run /login". Then a fake `auth status` that
  exits 1 gives `ai_signed_out`. With a fake `auth status` that exits 0, a pass with one call and no answer gives
  `ai_unreachable` when the configured backend's last `runs` row before the pass has `ok` 0, and also after a failed
  AI test request row. It is not failed when that row has `ok` 1, or when there is no row. A newer `jev` row with the
  other `ok` value changes neither result. A pass with two calls, both with no answer, after a row with `ok` 1, gives
  `ai_unreachable`; its `caught_up` is false and `pass:looked` is unchanged. A pass with two calls, one answered and
  one with no answer, is not failed. A pass whose only call answers off-schema is not failed, even after a failed
  call. The same holds when the only call gets a Claude result with subtype `error_max_structured_output_retries`, or
  one with `is_error` false and no `structured_output`. A pass with no model call records no AI code. With no
  `claude` on the path, the first model call of a pass records `unknown` and no other AI code: `auth status` is not
  run, no more calls run in the pass, `ok` is false, and no earlier failed `runs` row is needed. With Codex not on
  the path, the result is the same. With `backend.json` kind `gemini`, `aos run` writes `pass:last` with `ok` false
  and `["config_unreadable"]`, and makes no model call. The existing Claude quota test uses this real shape instead
  of stderr text. The Codex quota test is unchanged.
  `POST /api/setup/ai/test` runs with the fake Claude CLI. A null status with "Not logged in · Please run /login",
  and a fake `auth status` that exits 1, gives `{"ok": false, "problem": "ai_signed_out"}`, and `setup:ai` is not
  written. The same result with `auth status` exiting 0 gives `ai_unreachable`. A timeout gives the same. A 401 gives
  `ai_signed_out`, and `auth status` is not run. A 429 gives `ai_limit`. An answer off the schema gives
  `ai_unreachable`. No `claude` on the path gives `unknown`. Kind `gemini` gives `config_unreadable`, and no call and
  no `runs` row are made. A valid answer gives `{"ok": true, "problem": null}` and writes `setup:ai`. A model answer of
  `{"ok": false}` gives the same. Each call adds
  one `runs` row with job `setup`, the configured `backend`, and `ok` 1 or 0. With `per_day_cap` 1 and one `setup` row
  today, the next pass still briefs one conversation. The check's `ai` item gives the same codes. With Codex and a
  result with no answer, the code is `ai_unreachable`, and no status command runs. The AI step for kind `codex` shows
  no sign-in button, and on any failed test it shows "contact whoever installed".
  The no-answer stop and the pass time limit use a fake Claude CLI that sleeps past a backend timeout of 1 s, and an
  injected clock. With 4 due briefs, every call timing out and `auth status` exiting 0, the pass writes 2 `runs` rows
  with job `brief` and `ok` 0, the fake records exactly 2 calls, the code is `ai_unreachable`, `caught_up` is false,
  `pass:looked` is unchanged, and `errors.log` gains 2 lines. With `auth status` exiting 1, the code is
  `ai_signed_out` after 2 calls. With 4 due briefs giving an answer, then no answer twice, the fake records 3 calls,
  `ok` is true with no AI code, and `caught_up` is false; a second pass where every call gets no answer makes 2 calls
  and records `ai_unreachable`. With 4 due briefs giving no answer, an answer, no answer, an answer, the fake records
  4 calls, nothing stops, and `ok` is true. With 5 due briefs giving no answer, an answer off the schema, then no
  answer twice, the fake records 4 calls and the fifth brief is not tried. With 2 due briefs, both with no answer, and
  1 open request that Jev does not route to a session, no `request` call runs, and the request stays open with its
  failed-try count unchanged. With no due brief and 3 open requests, all with no answer, the fake records 2 calls, the
  third request is untouched, and each tried request's count is 1. With 3 due briefs and a first answer that moves the
  clock to `at` + 16 min, the fake records 1 call, `pass:last` is written with `ok` true, and `caught_up` is false.
  With 3 open requests and a clock that passes `at` + 15 min after the first triage, Jev is called once, no model call
  runs for the other two, and their `tries` are unchanged. A `signed_in()` whose fake sleeps past its 30-second limit
  counts as `None`, which gives `ai_unreachable`. A fake CLI that is a shell script starting a child that sleeps 120 s
  with the pipes open, with a backend timeout of 1 s, makes `ask` raise `NoAnswer` in under 10 s.
  A fake wacli whose `sync` exits 0 and prints "Logged out of WhatsApp" on stderr, and whose status envelope has
  `authenticated` false, gives `wa_unlinked`, and the pass's `ok` is false. A sync that exits 0 with `authenticated`
  true records no WhatsApp code, and the fake records exactly one status call in the pass. A locked store with
  `authenticated` false gives `wa_unlinked`. A failed sync with `authenticated` false gives `wa_unlinked`. A failed
  sync with `authenticated` true, or with the status command failing, gives `wa_sync_failed`. A sync that exits 0
  while the status command fails records no code and writes one line to `errors.log`. A sync timeout gives
  `wa_sync_failed`, and a missing wacli gives `unknown`. A store that `poll` cannot read stops the WhatsApp source
  only: the pass keeps the sync check's code, else records `wa_sync_failed`.
  In `tests/test_whatsapp.py`, with `chats` `[]`, `refresh` runs the sync, and the argv is exactly
  `[exe, "sync", "--once", "--idle-exit", "15s", "--refresh-contacts", "--store", dir]`; this replaces
  `test_refresh_skips_without_chats…`. A pass with no ticks runs the sync once, `followed` is `[]`, the problems
  include `no_chats`, and the model and Jev are never called. The pass's wacli allowlist accepts only
  `sync --once --idle-exit 15s --refresh-contacts --store …` and `--read-only --json auth status …`.
  `syncing` in `GET /api/setup/chats`, with a fake clock and a fake job: it is true while the auth process runs, also
  after the job shows linked. After a linked end at T, it is true with no `pass:last`, and with `at` = T+1 min or
  T+4:59; it is false at T+5:00. A failed pairing's end gives false. A renamed or new id gives true for 30 s, then
  false; a change of order only gives false. The fake wacli records no call from the GET.
  A tick missing from a non-empty `chats` gives `wa_chat_gone`. After a row with that jid, kind `unknown`, no name and
  no `last_message_ts` is added, the list shows it ticked with no problem, and a pass records no `wa_chat_gone`. With
  a pairing job that ended linked 1 min ago and a non-empty `chats` without tick X, `GET /api/setup/chats` answers
  `syncing` true with X as `wa_chat_gone`, and `POST /api/setup` gives the chats step `wa_chat_gone`. Adding X's row
  clears it on the next GET.
  A pairing job against a fake wacli whose first `auth` prints `auth_starting`, `logged_out` and `stopping`, and
  "Authenticated. Messages stored: 0" on stdout, with no `qr_code`, and exits 0. Status reports not linked. The second
  `auth` prints a `qr_code`, and the step shows that QR. The fake records two `auth` calls and no `logout`. The same
  holds when the first `auth` exits 1 with an `error` event and no `qr_code`. When both runs end with no QR, the step
  shows `wa_pairing_failed`, and the fake records exactly two `auth` calls. When the first `auth` emits the `error`
  event "store is locked (another wacli is running?)…" and exits 1, the step shows `wa_busy`, and the fake records
  one `auth` call. When the second run hits the lock, the step shows `wa_busy`. A run that emitted a `qr_code` and
  then failed is not restarted. A job ended by `whatsapp/start` or by the 10-minute limit is not restarted. The
  allowlist test rejects `auth logout`.
  Sign-in jobs run against fake CLIs that print the real event and prompt shapes, and a test asserts neither the QR
  payload nor a pasted code reaches `errors.log`.
- Windows CI runner: a save succeeds while the target is really held open by a second handle that is released after
  200 ms. A fake CLI that is a `.cmd` file starting a child that sleeps 120 s with the pipes open, with a backend
  timeout of 1 s, makes `ask` raise `NoAnswer` in under 10 s, and the child is gone.
- Windows VM, by hand, once per release candidate: a clean install from `assistantOS-Setup.exe` through every setup
  step with a real phone and a Claude subscription, then restart mid-setup and confirm it resumes at the right
  step. After setup, "Configuração" opens the conversations step with the current ticks, and with WhatsApp unlinked
  that step's link opens the WhatsApp step.

## Open Questions

1. **Spike S1, Windows VM: how `claude auth login` finishes from a windowless background process.** Either the
   browser returns to the CLI by itself, or the CLI prints a link and waits for a pasted code. The design handles
   both; the spike says which screen the owner actually sees, and whether the CLI needs a console at all. It runs in
   the VM, never on Ian's machine. It also confirms `claude auth login --claudeai` behaves as its `--help` says on the
   installed version (the exit code of `auth status` is confirmed from the 2.1.312 source). **Not run yet:** the VM was unavailable. It must run before the AI step is
   built; the rest of the build does not wait on it.
2. **Fizzy keeps unticked conversations.** The PRD limits the change to the page and Hermes (AC-CHATS-02), so the
   Fizzy surface still syncs every conversation the assistant has read. Left as is; Fizzy is out of scope.
