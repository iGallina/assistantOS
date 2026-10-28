# Design Refinement State — first-run-without-terminal

Started: 2026-10-28   Current pass: 5   Status: In progress
Branch: prd-first-run
Existing code posture: Preserve (source: TD §Existing Code)
PRD words: at start 1699 · growth baseline 1699
Last updated: 2026-10-28 12:21

## Documents
| Document | Path |
|---|---|
| PRD | docs/prds/first-run-without-terminal/first-run-without-terminal-prd.md |
| Technical Design | docs/prds/first-run-without-terminal/technical-design.md |
| Assumptions | docs/prds/first-run-without-terminal/assumptions.md |
| Exploration evidence | Claude Code 2.1.312 npm bundle grepped read-only (deleted after): `auth status` exits `loggedIn ? 0 : 1`; no-credential `-p` result = `is_error: true`, no `api_error_status`, "Not logged in · Please run /login"; server 401 → `api_error_status: 401`; limit = 429 "You've hit your session limit" |
| Supporting | docs/changes/page-refuses-other-websites/ (PRD + technical-design.md); its code on local branch `page-refuses-other-websites` (2d2838d, ae5b738), read with `git show`, not checked out |

## Passes
| Pass | Surfaced (new) | Taken | Resolved | Assumptions | Deferred | Blocked | Dropped |
|---|---|---|---|---|---|---|---|
| 1 | 12 | 12 | 8 | 1 | 2 | 0 | 1 |
| 2 | 5 | 12 | 10 | 1 | 1 | 0 | 0 |
| 3 | 3 | 10 | 7 | 0 | 3 | 0 | 0 |
| 4 | 1 | 6 | 5 | 0 | 1 | 0 | 0 |

## Questions
| ID | Pass | Question (one line) | Type | Impact | Conf. start → now | Status | Landed in |
|---|---|---|---|---|---|---|---|
| Q1 | 1 | Ticked ids the conversations list would not show (gone from wacli, or filtered kind): shown? saved? | Technical | HIGH | 55 → 92 | Resolved | TD §Conversations ("The list"; row "Ticked conversations the list would not show"), Interfaces validation, `Chat.problem`, Testing |
| Q2 | 1 | Chat moved `@lid`→phone id and re-ticked: how does its history come back (events.ext_id UNIQUE, INSERT OR IGNORE)? | Technical | MEDIUM | 55 → 90 | Resolved | TD §Conversations (row "A conversation that moved to its phone id"; "newly ticked" row), Testing |
| Q3 | 1 | Which problems make `pass:last.ok` false; does a per-item brief failure fail the pass? | Business | MEDIUM | 55 → 80 | Assumption | UI-005; TD §Status and problems (rows "Failed pass", "Which problem shows"), Data Models code order, Testing |
| Q4 | 1 | How the pass tells `wa_unlinked` from `wa_sync_failed`, and which claude output means `ai_signed_out` | Technical | MEDIUM | 65 → 95 | Resolved | TD §Status and problems (rows "WhatsApp problems in a pass", "AI problems in a pass", "Failed pass"), Integration Points, Testing, Open Question 1 note |
| Q5 | 1 | Signed in but `authMethod` ≠ `claude.ai` (API key/Console): is the AI step done? | Business | MEDIUM | 70 → 85 | Dropped (reframed → Q15) | — |
| Q6 | 1 | Pass item title uses `chats.name or jid`; share the setup list's name rule? | Technical | MEDIUM | 85 → 95 | Resolved | TD §Conversations ("The list" naming; row "A conversation's name"), Testing |
| Q7 | 1 | Open "Pedir ao assistente" request on an unfollowed conversation: answered or left open? | Technical | LOW | 60 → 92 | Resolved | TD §Conversations row "Who is followed", Testing |
| Q8 | 1 | WhatsApp step redone while already linked: re-pair or re-check only? | Technical | LOW | 70 → 95 | Resolved | TD §The two sign-ins (row "WhatsApp already linked"), Interfaces, Testing |
| Q9 | 1 | Setup language before the owner step is saved | Technical | LOW | 65 → 90 | Resolved | TD §Who the owner is row "Language and time zone", Testing |
| Q10 | 1 | `/setup` navigation, incl. after setup is finished | Technical | LOW | 70 → 90 | Resolved | TD §Setup row "Moving between steps", Interfaces `GET /setup`, Testing |
| Q11 | 1 | Mac install: page shows "setup not finished" until `/setup` is clicked through — acceptable? | Technical | LOW | 70 → 95 | Resolved | TD §Setup row "Installs from before this change" |
| Q12 | 1 | Atomic config write on Windows: retry `os.replace` on PermissionError? | Technical | LOW | 80 → 95 | Resolved | TD §Setup row "Where choices are kept", Testing (unit + Windows CI) |

| Q13 | 2 | List filter `kind IN (dm, group)` hides unresolved `@lid` chats (wacli kind `unknown`) that hold messages, against TD's own "Contato sem nome (`@lid`)" clause; filter by jid server + has messages instead? | Technical | MEDIUM | 70 → 92 | Resolved | TD §Conversations \"The list\", Testing |
| Q14 | 2 | How is "the owner's own chat" identified for exclusion from the list (phone from `auth status`?) | Technical | LOW | 75 → 90 | Resolved | TD §Conversations "The list" (own chat = `linked_jid`; a ticked own chat stays listed), Testing |

| Q15 | 2 | Claude backend starts `claude` (pass, test request, `auth login`/`status`) without `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN`/`CLAUDE_CODE_USE_BEDROCK|VERTEX|FOUNDRY`, so the subscription is always what runs; done = test request (AC-SETUP-02 unchanged, no `authMethod` rule)? (reframed from Q5) | Business | MEDIUM | 85 → 85 | Assumption | AUTH-002; TD §The two sign-ins row "Which Claude account runs", Testing |

| Q16 | 2 | What `followed` holds for a ticked id wacli no longer has (TD "Who is followed" + Data Models say only ids the poll returned; Q6 test says a gone ticked id stays in `followed`) — decides whether the page keeps showing it and whether `caught_up`/first look can ever become true; fold with Q1/Q13 | Technical | MEDIUM | 60 → 93 | Resolved | TD §Conversations ("Who is followed", "A conversation's name", "A ticked conversation wacli no longer has"), Data Models `followed`/`wa_chat_gone`, Testing |
| Q17 | 2 | TD §Status "Problems" row states "the backend recognizes a signed-out CLI by its message, as it already does for usage limits" as fact; Q4 evidence says likely wrong — rewrite when folding Q4 | Technical | LOW | 70 → 95 | Resolved | TD §Status and problems \"Problems\" row |

| Q18 | 2 | Which call checks `works` and writes `setup:whatsapp`/`setup:chats`? Fragment navigation means the server can't see which screen opened (contradicts "turns done when its screen opens") | Technical | MEDIUM | 70 → 90 | Resolved | TD §Setup (Progress, What works now, Installs from before, Moving between steps), Language and time zone row, Interfaces (`POST /api/setup`), Data Models `works`, Testing |
| Q19 | 2 | "Failed pass" row: "every call failed → `ai_unreachable`" vs "one brief failing alone is not a problem" collide on a one-call pass; zero-call pass reads literally as failed | Technical | MEDIUM | 55 → 95 | Resolved | TD §Status and problems \"Failed pass\" row (four-condition `ai_unreachable`) |
| Q20 | 2 | A brief failing on every pass (no retry cap) keeps `caught_up` false forever → first look never done, "Nada esperando" never shows | Technical | MEDIUM | 60 → 90 | Resolved | TD §Status "First look done", "Failed pass" last clause, `pass:last.caught_up`, Testing |
| Q21 | 2 | Nothing syncs WhatsApp between pairing-job exit and the first tick (`refresh` returns early with no ticks, whatsapp.py:50-51) → list frozen at pairing time vs AC-CHATS-01 "fills in by itself" | Technical | MEDIUM | 60 → 93 | Resolved | TD §Conversations (row \"The list keeps filling after pairing\", \"A conversation's name\", \"Still bringing names in\", \"The list\"), \"Failed pass\", Integration Points, Testing |
| Q22 | 2 | `pass:last.at` = start or end of the pass; what the page shows when `next_at` is past | Technical | LOW | 75 → 90 | Resolved | TD §Status "Pass record", "Next look", Testing |

| Q23 | 3 | After a remote logout `wacli sync` exits 0 (wacli docs/sync.md), and "WhatsApp problems in a pass" checks auth status only after a FAILED sync → a revoked session is never `wa_unlinked` (AC-STATUS-03) | Technical | MEDIUM | 60 → 92 | Resolved | TD §Status \"WhatsApp problems in a pass\", Integration Points wacli, Testing |

| Q24 | 3 | Interfaces: `GET /api/setup/chats` answers `wa_unlinked` while unlinked, but the list row/test serve the list then; how does the GET know the link state without running wacli on a poll? (AC-CHATS-03: ticks visible after an unlink) | Technical | MEDIUM | 60 → 90 | Resolved | TD Interfaces (intro, chats route), §Conversations "The list", §Setup "Moving between steps", Testing |
| Q25 | 3 | Missing Claude CLI → `ai_unreachable` sends the owner to the AI step, which can't fix it (missing wacli → `unknown`, whoever installed) | Technical | LOW | 70 → 90 | Resolved | TD §Status \"AI problems in a pass\", Testing |
| Q26 | 3 | Chats step `works` = "at least one ticked": shows working while every tick is gone and every pass fails `wa_chat_gone` | Technical | LOW | 70 → 92 | Resolved | TD §Setup \"What works now\", \"Progress\", §Conversations (gone-tick rule), §Status \"Final check\", Interfaces, Testing |
| Q27 | 3 | `POST /api/setup/owner` marks the owner step even when the name is still the example placeholder, against the owner works rule | Technical | LOW | 80 → 95 | Resolved | TD §Setup \"What works now\", Language and time zone rationale, Interfaces, Testing |

| Q28 | 3 | `ai_unreachable` "last model call before the pass in `runs`" picks up Jev rows (`backend`=`jev`, jev.py:42); count only the configured backend's rows? (+ a Claude result exit 0 with no `is_error` and no `structured_output`, claude_cli.py:19-20, is unclassified; + `make_backend` raising → which `pass:last` code, cli.py:98-102) | Technical | MEDIUM | 85 → 92 | Resolved | TD §Status \"Failed pass\", \"AI problems in a pass\", \"Pass record\", Testing |
| Q29 | 3 | No failure-to-code mapping for the setup test request (`ai/test`, check `ai` item): never-signed-in → no `api_error_status` → `NoAnswer` → literal `ai_unreachable`, not the sign-in TD/AUTH-002 promise; classify via `signed_in()` | Technical | MEDIUM | 75 → 94 | Resolved | TD §Status row \"AI test request\", SCOPE-002 row, Integration Points, Data Models `SetupTest`, Testing |
| Q30 | 3 | A pass whose 2+ calls all get no answer, after a good call before it, shows as worked and caught up (first look completes during an outage), against UI-005 "one conversation's summary fails once" | Technical | MEDIUM | 65 → 90 | Resolved | TD §Status \"Failed pass\" (single `ai_unreachable` rule, UI-005), Integration Points, Testing |

| Q31 | 3 | Re-link after a removal from the phone: in a narrow race the dead device row survives, the first `wacli auth` ends with no QR; pairing job retries `wacli auth` once by itself, then `wa_pairing_failed`; setup never runs `logout` | Technical | LOW | 85 → 93 | Resolved | TD §The two sign-ins (re-pair restart row), Testing |

| Q32 | 4 | `SetupState.whatsapp.syncing` has no named reader (chats GET has its own, wider `syncing`): drop it or name the screen that shows it | Technical | LOW | 75 → 92 | Resolved | TD Data Models `SetupState.whatsapp`, \"Still bringing names in\", Testing |
| Q33 | 4 | List before the first pairing with ticks already in `whatsapp.json`: Interfaces says empty list; "The list" says every ticked id is listed (would show `wa_chat_gone`) — fold with Q26 ("gone only when the store was read") | Technical | LOW | 75 → 92 | Resolved | TD §Conversations \"The list\", \"Ticked conversations the list would not show\", Interfaces, Testing |

| Q34 | 4 | `NoAnswer` doesn't stop remaining calls (600 s each, base.py:30); Windows kills the pass at 30 min (windows.py:19) and a killed pass writes no `pass:last` → in a hanging outage a pass with 3+ due calls dies silently; stop remaining calls after the second `NoAnswer`? | Technical | MEDIUM | 75 → 88 | Deferred | — |

| Q35 | 5 | Gone-tick "Limit" claims the next pass clears a pre-pairing tick shown gone right after the first pairing (unverified: a DM with no synced history may never arrive) and conflicts with the empty-`chats` rationale; hold `wa_chat_gone` while `syncing`, or keep as a limit with a corrected claim? | Technical | LOW | 70 → 70 | Pending | — |

Status values: Pending · Investigating · Answered, not folded · Resolved · Assumption · Deferred (carried to next pass) · Blocked · Dropped (failed the scope gate on closer look; reason in notes). A Reframed question is replaced by a new row marked Pending with "reframed from Qn" in its notes.

## Question notes

### Q1
Deferred at 85 (residual: the one production install's `whatsapp.json` is on the client's machine, unseen). Proposed answer + document-ready row, Interfaces wording, `Chat.problem`, tests: ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q1.md. Summary: the list also includes every ticked id of any kind (`kind IN ('dm','group') OR jid IN (<ticked>)`); a ticked id missing from wacli `chats` is shown ticked with `wa_chat_gone`, named from the store title unless it equals the id, else "Conversa que não existe mais"; problem rows first; POST accepts ids listed or already ticked, else 400. wacli v0.19.0 kinds: `internal/app/sync.go:371-384` (`@lid`/`@bot`/`@call` → unknown); LID migration turns unknown → dm (`lid_migration.go:173`). Fold together with Q13 (same list filter). Note: investigator ran one read-only aggregate count on Ian's own wacli store (1,697 `@lid` unknown rows, 2 with messages).

### Q5 → Q15
Reframed. In `-p` mode `ANTHROPIC_API_KEY` is always used when present, ahead of the subscription login (Claude Code auth docs); `backends/base.py:58` runs `subprocess.run` with no `env=`, so a key in the owner's env bills the API on every pass. A setup-time `authMethod` check can't protect scheduled passes (different env: launchd PATH only `platform/macos.py:17`; Task Scheduler = user env), and `authMethod == claude.ai` would reject `oauth_token` (CLAUDE_CODE_OAUTH_TOKEN, a subscription). Proposed: strip those vars from every `claude` child; done = test request answers. Business residue: "never use an API key or cloud account, even one the owner set" (`decisions.md:89` says "no API keys required", not "never used"). Preserve impact: a v0.3.0 install running passes on an API key would start failing as signed out → changelog line. Not covered: `apiKeyHelper`/settings.json `env`; `ANTHROPIC_BASE_URL` stays. Evidence: ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q5.md.

### Q12
Resolved 95, waiting for the writer slot. Amend TD §Setup "Where choices are kept": temp file with a unique name (ThreadingHTTPServer, `page/server.py:75`: concurrent saves); on `PermissionError` retry `os.replace` with short growing waits for ~2 s; still failing → remove temp, keep old file, raw error to `errors.log`, POST answers `{"problem": "unknown"}` (existing catalog). Test incl. a real held-handle test on Windows CI. Evidence (bpo-46003; `config.py:27` read-and-close): ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q12.md.

### Q4
Deferred at 88. Document-ready text (2 Status rows, Problems row edit, Integration Points, tests): ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q4.md. wacli: on failed sync (not locked store) run `wacli --read-only --json auth status --store <dir>`; envelope `{success,data,error}` → `data.authenticated` false = `wa_unlinked`; true or status failed = `wa_sync_failed`; timeout = `wa_sync_failed`; missing wacli = `unknown`; `poll` can't read store → WhatsApp source stops, keeps sync-check code else `wa_sync_failed`; phone-side unlink → `SESSION_REVOKED` file → status not linked. Claude: `-p --output-format json` sign-in failure exits 1, JSON on stdout with `is_error: true`, `api_error_status: 401` (anthropics/claude-code#73067, SDK typings) → new `SignedOut` error → `ai_signed_out`, stops remaining calls like `QuotaExceeded`; if every call failed with no 401/limit, run `claude auth status --json` once: non-zero → `ai_signed_out`, else `ai_unreachable` (`auth status` alone can report signed in while server refuses token, #80075). Prerequisite: `Backend._run` raises on non-zero exit before `ClaudeCLI` parses JSON (base.py:62-63, claude_cli.py:14-18) → parse stdout on non-zero exit. Likely existing bug: Claude's "You've hit your session limit" matches none of `usage limit|rate limit|limit reached|quota` and the check reads only last 500 chars → use `api_error_status` 429 / `result`. Residual (why <90): `claude auth status` exit code from `--help` only (spike S1 confirms); JSON shape of "Not logged in" unconfirmed.

### Q9
Resolved 90, waiting for the writer slot. Before the owner step is saved, screens use `owner.json`'s language (`pt-BR`, copied from the example by `aos init`, which both installers run: `cli.py:243-244`); server renders strings into HTML (`page/server.py:37-40`) and reads `owner.json` each request → no Accept-Language rule. Owner screen prefills language/time zone from the browser while the owner step has no `done_at`; afterwards shows saved values. Test: `GET /setup` with `Accept-Language: en-US` and no `setup:owner` → `lang="pt-BR"`; after saving English, next load is English with no restart. Replacement text for TD §Who the owner is "Language and time zone" row: ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q9.md.

### Q10
Resolved 90, waiting for the writer slot. After setup `/setup` opens the conversations step (the five-step row always shows each done); deep links by fragment `/setup#<step>` (no route/param; server routes on path); "Configuração" opens `/setup`; AC-STATUS-03 link and step-naming problem messages open `/setup#<step>`; no step locked, each shows its own problem with the catalog link (chats step shows `wa_unlinked` → WhatsApp step); opening a step only reads status, so a foreign link to `/setup#whatsapp` starts no pairing (AC-SETUP-08); check step's "Continuar" goes to the page (UI-001). Text for TD §Setup row "Moving between steps", Interfaces `GET /setup` line, tests: ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q10.md.

### Q14
Resolved 90; fold with Q1/Q13/Q16 (same "The list" row). Own chat = `data.linked_jid` from `wacli --read-only --json auth status` (`<digits>@s.whatsapp.net`; no LID returned; whatsmeow stores own LID→PN at pairing `pair.go:231`, so the self chat exists only under the phone id, kind `dm`). Don't read `session.db` (holds keys). Exclusion justified: all self-chat messages are `from_me` → "out" (`plugins/whatsapp.py:80`); requests only from "in" (`graph.py:121`). Text + test: ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q14.md. Side finding agrees with Q13 (unresolved `@lid` people stored as kind `unknown`; suggested people = `dm` or `unknown` with `@lid` id).

### Q16
Deferred at 87. Proposed: `followed` = `wa:<id>` for every ticked id, including a gone one (matches the existing Testing line); the gone conversation stays on the page (summary, pending decision) until unticked — only unticking removes (UI-004); after a move to the phone id the old id has no item, so nothing shows twice; `caught_up` counts only followed conversations wacli still has, so a pass can be caught up and still fail with `wa_chat_gone` (`ok` and `caught_up` independent); otherwise one gone tick shows "still looking for the first time" (AC-PAGE-03) forever; `wa_chat_gone` next step must say to untick the old row. Replacement text for "Who is followed", "First look done", Data Models `followed` and `wa_chat_gone`, locale string, tests: ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q1-13-16.md.

### Q16 + Q20 (pass 2)
Resolved 93 / 90, waiting for the writer slot. Replacement text for Conversations rows "Who is followed", "A conversation's name", "A ticked conversation wacli no longer has"; Status rows "Failed pass" (last sentence), "First look done" (whole row); Data Models `followed`, `pass:last.caught_up`, `wa_chat_gone` + one locale string; Testing first-look line + 4 Q16 tests: ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q16-20.md. Rule: caught up = no problem except `wa_chat_gone` AND every due brief tried (left to per-pass/per-day limit = not tried; failed on its own = tried). New: v0.3.0 stored titles can equal the jid (whatsapp.py:76, store.py:68-73) → the pass replaces a stored title equal to the id with "Conversa que não existe mais" once, creates no item for a gone id.

### Q22
Resolved 90, waiting for the writer slot. `pass:last.at` = pass start (taken before reading config), written at the end; crash still records start + `unknown`; killed pass writes nothing. `next_at` = `at` + 5 min, null with no record; null or past → "Próxima verificação em instantes" / "Next check shortly"; else "Próxima verificação às 14:40". Start is truthful (collect reads WhatsApp first, graph.py:94-107; schedulers count between starts, windows.py:17-19, macos.py:16). Replacement rows "Pass record", "Next look" + test: ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q22.md.

### Q21
Deferred at 85 (names via `--refresh-contacts` at 70). Proposed: delete `refresh`'s "no chats" early return, no "not linked" check (unlinked `sync` fails <1 s "not authenticated", app.go:236 → `wa_unlinked` via "WhatsApp problems in a pass"); add `--refresh-contacts` to the pass's sync (`wacli auth` copies contacts once right after connect, sync.go:203; otherwise a name arrives only with a new message, sync.go:404-441; the flag reads only the local session store, upsert never blanks a name); "Still bringing names in" = while the pairing job runs, after it ends until a pass finishes after that end, and 30 s after the list's ids or names change. `wacli auth` ends after 30 s idle (QR wait not counted): remaining history arrives at next connect, handled by `sync --once`. `sync --once` sends no message/receipt/chat-state; sends presence and deletes downloaded history blobs (as every pass today). No-tick pass: no model/Jev call; `no_chats` recorded after the sync. Document-ready rows + tests: ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q21.md.

### Q23
Resolved 92, waiting for writer slot. Run read-only `auth status` after EVERY sync: `authenticated` false → `wa_unlinked` whatever sync did (incl. locked store); a status failure alone doesn't fail a pass that synced. Revocation during sync: exit 0, stderr "Logged out of WhatsApp…", writes `<store>/SESSION_REVOKED`; whatsmeow deletes the device row (rare race keeps it). Re-pair from the WhatsApp step works (status not linked → connect button; first attempt in the race may show no QR → `wa_pairing_failed` "Tente de novo"). Replacement row, Integration Points bullet, tests: ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q23.md.

### Q31
Deferred at 85 (from inv-q23 follow-up). whatsmeow sends LoggedOut then deletes the device row on both revocation paths; wacli can exit before the delete only in a narrow race (hence `SESSION_REVOKED`). Usual: next `wacli auth` shows a QR; pairing deletes `SESSION_REVOKED`. Race: first `wacli auth` connects with dead creds, is refused, whatsmeow deletes the row, run ends with no QR (exit 0 or 1 unconfirmed); second shows the QR. `wacli auth logout`: useless on revoked (exits 1 before sending) and unlinks a live session if status was wrong → keep out of allowlist. Proposed row in §The two sign-ins + test (fake wacli: first auth exits 0 `logged_out` no QR, second prints QR → step shows QR, two `auth` calls, no `logout`; two no-QR runs → `wa_pairing_failed`): ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q23.md (second part).

### Q25
Resolved 90; fold together with Q28–Q30 (same rows). Missing `claude` → `unknown` (like missing wacli; installer installs both: bootstrap.ps1:91-94, `aos setup` → `tools.install_tools`). Backend already detects it via `shutil.which` (base.py:53-56); that branch raises new `NotInstalled` (a `BackendError`) → pass records `unknown` on first call, stops remaining model calls; Codex same. AI test, `ai/start`, check's ai item → `unknown`. Text: ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q25-27.md.

### Q26
Deferred at 85. Proposed: chats `works` = at least one tick AND no tick gone (a tick counts as gone only when the wacli store was read); one rule for the step, the final check's chats item (carries `wa_chat_gone`; PRD row unchanged — one more failure reason routed to the same screen) and the pass; `setup:chats` marked only when saved ticks work. Edits: "What works now", "A ticked conversation wacli no longer has", "Final check", Interfaces `POST /api/setup/chats`, "Progress" writers. Text: inv-q25-27.md.

### Q29
Deferred at 88. Setup test request is one call, classified alone (no two-in-a-row rule): 401 → `ai_signed_out`; 429 → `ai_limit`; not installed → `unknown`; kind this version can't run → `config_unreadable`; `NoAnswer` → `signed_in()`: false → `ai_signed_out`, true/None → `ai_unreachable`; schema mismatch → `ai_unreachable`. The test writes a `runs` row with job `setup` (a working test resets the count; a failed one counts as the first failure). Proposed new TD row "AI test request": ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q28-30.md. Note: ChatGPT (SCOPE-002) row says a failed test sends the owner to whoever installed, but `ai_unreachable` points to the `ai` step — for a non-Claude backend that step's screen must say it.

### Q30
Investigator rated 85 because it rests on pending UI-005; recorded as 90: the rule implements UI-005 as written (an implementable assumption counts as dispositioned); if UI-005 changes, this rule changes with it.

### Q32
Resolved 92, waiting for writer slot. Drop `SetupState.whatsapp.syncing` (no reader; AC-CHATS-01's "the screen" is the conversations screen, which reads `GET /api/setup/chats` `syncing`). Data Models line → `whatsapp: {job: Job|null, phone: string|null}`; "Still bringing names in" names the conversations step and says it polls `GET /api/setup/chats` every 2 s; drop "In `GET /api/setup/chats` only" and the "uses (1) and (2)" sentence; Testing `syncing` clause targets the chats GET only. Text: ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q32.md.

### Q31 (pass 4)
Resolved 93, waiting for writer slot. Rule: a pairing job whose `wacli auth` ends without ever emitting `qr_code`, while read-only status still says not linked and the store was not locked, restarts `wacli auth` once (counted in job memory); a second no-QR run → `wa_pairing_failed`; a lock (error event "store is locked…") → `wa_busy`, no restart; no restart after a shown QR or a server-ended job; setup never runs `auth logout`. (Dead device row: `auth` opens no QR channel, WhatsApp refuses, whatsmeow deletes the row, `auth` exits 0 "Authenticated. Messages stored: 0".) Row after "WhatsApp already linked" + tests: ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q31b.md. Don't copy wacli's "auth logout, then auth --phone" hint into locale text.

### Q34
Deferred at 88. Stop rule: two `NoAnswer` IN A ROW (not in total) stops every remaining model call (briefs and requests, same path as `QuotaExceeded`); any answer (incl. off-schema) resets; count carries from `brief` to `requests` node; consistent with the `ai_unreachable` rule (first two no-answer → pass ends with 2 calls, fails; answer then two no-answers → stops, "worked" under mixed rule, not caught up). Stop alone insufficient: each hung call costs 600 s (base.py:30; Claude Code itself waits 600 s per API attempt, retries up to 10: `API_TIMEOUT_MS`, `CLAUDE_CODE_MAX_RETRIES`); Windows ends the task at 30 min (windows.py:19-20). Proposed new row "Pass time limit": a model call starts only in the first 15 min of a pass; work left by the limit is not tried, records no code, not a failed try; `signed_in()` gets a 30 s limit (timeout = `None`). macOS launchd doesn't end a pass (late record, not lost; untested). Full outage ≈ 23 min max (2 calls + 180 s sync). Text: amendments to "AI problems in a pass", new "Pass time limit" row, "First look done" sentence, "Failed pass" rationale line, 9 tests: ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q34.md. Residual (why 88): Claude CLI retry duration unmeasured; 15-min budget is a judgment.

### Q2
Proposed answer (fold into TD §Conversations): new row "A conversation that moved to its phone id": trigger = a message whose id is already stored under a `wa:…@lid` item arrives under a phone id; the pass moves the whole item (messages, requests, mark, brief, label, draft, Fizzy card) to the new id in one transaction, keeps rows the new id already has, deletes nothing; moves only from a hidden id (never merges two phone ids). Correct "Duplicates are already ignored by message id" in the "newly ticked" row; limit: a conversation with no messages in the last 7 days starts fresh under the new id. Tests: the move, and the two-phone-ids case. Evidence + sketch: ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q2.md (wacli v0.19.0 `internal/store/lid_migration.go` keeps msg_id; migration runs each sync, `internal/app/sync.go:197`; store.py:21-22, 83-88).

### Q3
Assumption UI-005 (80%) + TD rows. Open overlap: "every model call failed → `ai_unreachable`" depends on Q4's classification. Evidence: ~/.claude/deliveries/a2ebee1a-beda-4c0f-be5d-819f57da31c1/inv-q3.md.

## Conformance
For next conformance (discovery-p4 nits): TD:84 still has pre-Q33 text; TD:103 repeats TD:105; TD:297 stray line break.
For next conformance: `SetupState.whatsapp.syncing` and `GET /api/setup/chats` `syncing` carry the same flag twice; `wa_sync_failed` "stops a whole source" wording.
Pass 1: fixed AC-STATUS-02 UI-005 citation; `caught_up` definition aligned with Failed pass row (+ test); heading spacing; Testing reflow. Raised Q16, Q17. Minor: `invalid_input` outside display order in catalog (harmless, never in `pass:last`). TD/PRD word ratio 2.86.

Pass 2: fixed "Installs from before" (final check also writes `setup:ai`); Integration Points Claude line (JSON read on every pass call; AUTH-002 env strip). Raised Q24–Q27. Repeats left for consolidation (gone-id rules in three rows; `ai_unreachable` definition in two). TD 7954 words = 4.36× PRD (1823): consolidation must cut.

Pass 3: Failed pass row's "stops a whole source…" clause removed (false for `wa_sync_failed`/`wa_unlinked`/`ai_unreachable`; each code's own row states it); Problems rationale aligned with `ai_unreachable` wording; Testing name-rule order (person contact names first). `syncing` not a pure duplicate (chats GET uses 3 cases, SetupState 2). Raised Q32, Q33. TD 9536 words = 5.23× PRD (1823): consolidation must cut.

Pass 4: "WhatsApp already linked" `wacli logout` → `wacli auth logout`; Interfaces/Testing reflow. Repeats for consolidation: Problems rationale vs "AI problems in a pass"; "AI test request" rationale vs "AI problems"/SCOPE-002; gone-tick "one rule for step, check and pass" ×3; "empty `chats` before pairing" ×3 + Interfaces; "test counts in two-in-a-row" in "Failed pass" and "AI test request". Raised Q35. TD 11,014 words = 6.0× PRD (1,823).

## Exploration scripts
| Script | Question | Finding |
|---|---|---|

## Conflict check
Pass 1: 2026-10-28 · 5 earlier criteria changed · 5 Replaces lines written (AC-SETUP-01 ×2, AC-SETUP-05, AC-PAGE-01, AC-PAGE-04) · 0 raised as questions. Build notes: README "Install" text changes with AC-SETUP-01; `Superseded in part by:` goes on AC-ORIGIN-03 only when AC-SETUP-01 is built
Changed after pass 1: AC-STATUS-02 (citation of UI-005 only, conformance pass 1)
Completion: pending

## Noticed, out of scope
- An outage can turn an owner's request into `needs_session`: `NoAnswer` counts toward `MAX_TRIES` (graph.py:171)
- Windows: if `claude` is a `.cmd` shim, `subprocess.run`'s timeout may not kill the real process; a process left holding the pipes can block the pass
- Fizzy surface sync has no total time limit and runs before the pass record is written
- `MAX_TRIES = 2` closes an open owner request for good after two no-answer passes during an outage (graph.py:60, 168-171)
- TD wording: `wa_sync_failed` listed among codes that "stop a whole source", but the pass still reads the store after it (conformance)
- Every pass syncs with `--presence-mode normal`; wacli docs say this can mute the phone's notifications and recommend `quiet` for personal numbers (existing behavior; worth one decision)
- A stopped scheduler would show "em instantes" forever (the last-check line still shows how old the last pass is; no criterion asks to detect it)
- A brief failing on every pass costs one model call per pass and counts toward the 60-call daily cap (graph.py:132): one bad conversation can use the day's budget in ~5 h; a brief retry cap would be its own question
- English owners still get Portuguese briefs and drafts
- `gemini` is listed in config but not supported as a backend
- Failed briefs have no retry cap: each costs a model call on every pass
- Task Scheduler's 30-minute limit can kill a long pass; a killed pass records no `pass:last`
- Groups the owner left keep kind `group` in wacli, so they stay in the setup list
- If a moved conversation has no message in the 7-day window, old and new items show under one name until the old one is unticked
- API-key strip (AUTH-002) does not cover Claude `apiKeyHelper`, an `env` block in Claude's settings.json, or `ANTHROPIC_BASE_URL`; Codex has the same pattern with `OPENAI_API_KEY` (ChatGPT is a support step, SCOPE-002)
- `load_file` does not catch `OSError` on read, so a locked config escapes as a raw error, not `config_unreadable` (existing behavior)
- MCP `ver_conversa` and page `/api/ask`, `/api/mark` accept any stored item id, incl. unticked ones (harmless: no surface lists them)
- Daily report "problems" section prints raw `errors.log` lines (AC-SETUP-07 does not cover the report)
- `contacts.json` `never_list`, `count_only`, `owner_self` are read by no code
- Pass task runs `uv.exe` (console program) from Task Scheduler; may flash a console every 5 min (unverified)
- After its first brief an ABERTO item goes to "Decidir agora" even when the owner sent the last message; day one may show every ticked chat there (existing section rule)
- Branch `page-refuses-other-websites` deletes 9 lines of `docs/decisions.md` vs `prd-first-run`; check at merge
- Hermes speaks the language in `SOUL.md` (pt-BR default); setup writes language only to `owner.json`, so an English owner gets an English page and pt-BR Hermes (pre-existing; `aos init` never set `SOUL.md`)
- Fizzy keeps cards for unticked conversations (`surfaces/fizzy.py` `sync()` reads `statuses(store)`); already TD Open Question 2, Fizzy out of scope

## Blockers
| Blocker | Questions affected | What unblocks it |
|---|---|---|
| Windows VM unavailable; spike S1 not run (TD Open Question 1) | any question on how `claude auth login` finishes from a windowless process | VM back (A139 USB SSD `aos-vm`) |
| No `claude auth`, wacli, product install or run on this Mac (PM brief) | questions needing live CLI behavior | answer from docs, `--help` text already recorded, code and tests only |

## Next action
Pass 5: discovery + Q34 (2nd pass; below 90 again → design decision) + Q35.
