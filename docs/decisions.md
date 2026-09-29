# Decisions

Append-only. Newest at the bottom. Lessons carried from Ian's AIS-OS are marked *(from AIS-OS)* with the date they were learned.

## 2026-09-28 — The project exists

**Decision (Ian):** turn the personal AIOS into an installable product, `assistant-os`. First customer: owner-operators on Windows + phone. Core: Rust installer/supervisor + Claude Code or Codex CLI as the agent runtime + Jev for classification. Open source; revenue from education and services on top. Private repo until the first real Windows install works.

**Why not build the agent from scratch:** open Rust agents already exist (Codex CLI, goose); the value is the loop, the integrations and the teaching, not another agent runtime. **Why not Mac-first:** the target users are on Windows and phones; most of AIS-OS's macOS glue (Mail.app, Reminders, launchd) has to be replaced anyway.

## 2026-09-28 — Jev for classification, a small LLM for writing *(from AIS-OS)*

Bake-off on real data (151 WhatsApp turns, 42 items, 23 requests; labels from the owner's own behaviour):

| | "Needs a reply" (balanced acc.) | Tagging (9 classes) | Request triage (4) | Time/call |
|---|---|---|---|---|
| Jev (hosted) | 0.71 (AUC 0.79) | 0.64 | 0.96 | ~0.3 s |
| Claude Haiku | 0.75 | 0.64 | 0.96 | ~13 s |
| CLM-8B local (Mac, GGUF encoder) | 0.50 | 0.43 | 0.35 | ~0.45 s |

Jev ties Haiku on quality, is ~40× faster and returns tunable probabilities → classification goes to Jev; anything that writes goes to a Haiku-class model. Use "needs a reply" as a **label** (score < 0.40 = probably small talk), never as a filter that hides messages: at the cut-off that keeps 95 % of real messages it removes only 31 % of noise. Local CLM paused (reassess 2026-12-28): on Apple Silicon the official vLLM encoder does not run; the GGUF substitute did not discriminate.

## Lessons carried *(from AIS-OS)*

- **Sweeps are code, the model drafts** (2026-09-21). What the user sees is decided by deterministic code; models write briefs and drafts, never select.
- **Nothing sends without the human** (2026-09-23). Drafts open as a ready compose window / prefilled chat; the person presses Send.
- **Background AI is logged and visible** — one line per call (`job`, model, duration, cost) and a notification per pass.
- **Per-user config, committed templates** (2026-09-28). Real contacts and rules in git-ignored files; `*.example.json` committed with readable placeholders (not fake numbers — a history scrub rewrote fake numbers too). Scrub history *before* the first push; a later scrub needs a force-push.
- **Confine agents with `--tools`, not `--allowedTools`** (2026-09-28). `--allowedTools` only pre-approves; a test agent still ran Bash. `--tools <list>` limits what exists; add `--disallowedTools Bash` as a second fence; verify from the run's transcript, not its reply (the reply quoted a git-status snapshot the runtime injects).
- **One local model at a time** (2026-09-28). Runtimes stay installed; weights are a cache; switching = stop, delete weights, fetch the next.
- **Fetching e-mail bodies is the slow part** (2026-09-26). Mail.app `content` cost ~5 s/message; read list fields first, fetch bodies only for human mail, once, cached.
- **A tool's silence is not evidence.** Prove a search on a known match before trusting a zero (a `\b` regex returned 0 phone numbers when there were 991).
- **Reopen must be real** (2026-09-26). A done item with a new message must come back visibly, and marking it done again must not toggle it open.
- **Follow-ups need an owner and a date** (2026-09-26). "Waiting on X until D" → answered first = the owner's turn; date reached = overdue with the chase drafted.

## 2026-09-28 — Operating assumptions (Ian)

1. **Upstream-first.** Every installation reports bugs and improvements to the CORE back to the main repo.
2. **One repo per installation**, because each needs its own optimisations. *Adjustment pending (see below): a GitHub fork of a public repo is always public, so the per-install repo is a private repo created from the template with `upstream` = the main repo, not a GitHub fork.*
3. **Secrets live in Bitwarden** — passwords, tokens, API keys. A skill installs and maintains Bitwarden. *Pending: `bw` (human vault, needs an unlock) vs `bws` (Secrets Manager, machine access tokens — works unattended).*
4. **Rust as much as possible**; Rust and Python are both installed. A skill knows how to install and update both on every OS.
5. **Superpowers** drives every piece of code (brainstorm → plan → deterministic implementation), under the **Karpathy principles** (github.com/multica-ai/andrej-karpathy-skills) as the coding motto.
6. **Fizzy is the main kanban** and the user's visual feedback.
7. **A daily run** generates/updates an **HTML report** (persisted) that proposes the best prompts for the next step/action.
8. **No SOUL.md / HEARTBEAT.md.** Onboarding teaches each skill and when to use it instead.
9. **Onboarding builds the first script with the user**: pick a source of repetitive work (e-mail, Slack, WhatsApp, …) → a monitor built with the skills → an HTML report → tune it for missing information → next-action buttons → schedule the sweep so the agent runs it periodically.

## Open items raised 2026-09-28 (to decide)

- Per-install repo: template + `upstream` remote (private) instead of a GitHub fork — forks of public repos cannot be private.
- Upstream reporting: redaction before anything leaves an install (logs hold client messages); the owner approves each report; Jev can pre-classify "core bug vs local tweak".
- Updates: versioned core + changelog + migration scripts + CI tests, so `git pull upstream` doesn't break a customised install.
- Bitwarden: `bws` machine token for scheduled runs vs `bw` unlock.
- Rust on owners' PCs: ship prebuilt signed binaries; compiling Rust on Windows needs the MSVC Build Tools (several GB) — keep the toolchain on the dev side unless an install truly needs it.
- Windows trust: unsigned `.exe` triggers SmartScreen/antivirus — code-signing certificate.
- Privacy/LGPD: client messages flow to the chosen LLM and Jev; consent, retention and export/delete per install.
- Cost guard: per-install LLM/Jev budget cap and the call log shown in the daily report.
- Support access for the services revenue: opt-in remote access (e.g. Tailscale) and an opt-in health ping.
- Backups of local state (SQLite, config) and a clean uninstall/export.
- Language: pt-BR first for Brazilian owners.
- WhatsApp: unofficial client (`wacli`) risk on customers' numbers vs the official Business API.

## 2026-09-29 — Answers to the open items (Ian)

- **Per-install repo:** the user's own private repo created from the main one, `upstream` = main repo; a skill guides GitHub account creation and the repo setup.
- **Secrets:** Bitwarden — `bws` for the agent's unattended runs, `bw` for the owner's vault.
- **No Rust for now, no executables.** Python everywhere (small scripts) + PowerShell on Windows. Rust later only for tools shipped or run online, never compiled on the user's PC. → No code-signing certificate needed: SmartScreen flags unsigned *executables* from any source; scripts fetched with git or `irm | iex` are not flagged (the install script handles PowerShell's execution policy).
- **Upstream reports:** a local anonymizer before anything leaves: deterministic patterns (e-mails, phones, CPF/CNPJ, cards, keys/tokens) + the user's contacts list first; Jev only on the already-masked text (Jev is a hosted API — sending raw logs to it would leak what we are hiding); the owner reviews every report.
- **Privacy law:** the software runs on the user's own computer with no server of ours; compliance is the user's responsibility — stated plainly in the docs.
- **Costs:** a skill estimates and reports the daily cost of the whole setup per provider (OpenRouter, OpenAI, Anthropic, Jev); the daily report shows spend.
- **Updates:** `core/` vs `local/` split; tagged releases, changelog, numbered migrations, self-test, rollback — via an `update` skill; CI on Windows + macOS from the first release.
- **WhatsApp:** keep the current skills/client for now; the official Business API is being worked on separately.

## 2026-09-29 — Remaining open items (Ian: "follow your recommendations")

- **Support access:** none in v1 — the client shares their screen when needed. No always-on way in (every open door is a liability carried per client). Revisit when a paying client asks.
- **Backups + clean uninstall/export:** in the MVP. The first failed install must not cost the client their data.
- **Language:** pt-BR first; every user-facing string in separate files so English is a translation, not a rewrite.
- **Phase 1 order:** Windows spikes first (cheap yes/no; a "no" on wacli or the agent runtime changes the pitch), interviews after.

## 2026-09-29 — Name, Pydantic, LangChain (Ian)

- **Renamed** `assistant-os` → **assistantOS**: folder `~/Projetos/assistantOS`, repo `iGallina/assistantOS` (private). Entries above keep the old name as written.
- **Pydantic (adopted):** the engine stops being stdlib-only. Pydantic models define every per-user config file (contacts, tags, providers) and every LLM output (brief, request plan, triage), and `model_json_schema()` generates the schema sent to the model — one definition validates both what the user writes and what the model returns. Installed by uv; Windows wheels exist.
- **LangChain (proposed, pending Ian's scope call):** see the scoring in the 2026-09-29 conversation. Question: does LangChain carry only the model calls (brief, triage writing, request planning; `init_chat_model` + `with_structured_output(PydanticModel)` over the user's provider), or also replace Claude Code/Codex for the tool-using agent runs?

## 2026-09-29 — Subscription-first, a hard-coded core, LangGraph on the CLIs (Ian)

- **Each customer:** clones the repo (code + skills), signs up for a subscription (Claude, ChatGPT/Codex, Gemini) and runs everything on it — no API keys required for the model layer. Jev stays an API key (classification).
- **The core is a real Python package**, not loose scripts: `assistantos` (Pydantic models, LangGraph graph for the loop, a CLI entry point, tests), versioned and updated as `core/`. Skills become thin: they explain when to use a capability and call the package's commands; behaviour lives in code.
- **LangChain/LangGraph run on the subscription CLIs**: one LangChain chat model per backend (`claude -p`, `codex exec`, `gemini -p`), selected by the user's config. Resolves the pending LangChain question (neither A nor B: LangChain everywhere, but the model behind it is the subscription CLI). Evidence: `docs/spikes/2026-09-29-langgraph-on-subscription.md`.

## 2026-09-29 — Plugins, and connecting Google without a Google Cloud project (Ian)

- **Requirement:** integrations ship as plugins (WhatsApp, Gmail, Google Docs, Google Sheets, more). Connecting one must be as easy as possible — owners cannot be expected to create an OAuth app in their own Google Cloud project (AIS-OS lesson: a "Testing" OAuth app logged `gog` out every 7 days; retired 2026-09-23).
- **Plugin shape (in the core package):** one module per plugin = Pydantic config + `connect` (guided setup) + `doctor` (a read that proves access) + the actions the graph may call.
- **Google route (proposed, spike pending):** an **Apps Script bridge** in the user's own account — pushed with `clasp`, deployed as a private web app ("execute as me"), called by the local agent with a shared secret kept in Bitwarden. Built-in Gmail/Docs/Sheets/Drive/Calendar access, no Cloud project, one settings toggle + one consent. Scored 86 vs own-Cloud-project wizard 72, shared verified app 65 (restricted Gmail scopes → paid yearly assessment), IMAP app password 76 (mail only).
- **Spike must prove:** consent flow incl. the unverified-app screen; no 7-day expiry; read + draft in Gmail, read/write a Sheet and a Doc; consumer quotas; that the web-app URL is useless without the secret.

## 2026-09-29 — LangGraph yes, LangChain model wrappers no (proposed, pending Ian)

Question (Ian): do we need LangChain and LangGraph, given agents must carry the heavy load, grow on top of current features and work across every technology?

| Option | Viability /30 | Scalability /30 | Zero cost /20 | Maintenance /20 | Total |
|---|---|---|---|---|---|
| **A. LangGraph for jobs + our own thin backends** | 27 | 27 | 20 | 15 | **89** |
| B. LangChain chat-model wrappers + LangGraph (spec as written) | 25 | 27 | 20 | 11 | 83 |
| C. Neither: plain loop (AIS-OS style) | 28 | 18 | 20 | 16 | 82 |
| D. PydanticAI / pydantic-graph | 20 | 24 | 18 | 14 | 76 |

- **LangGraph earns its place** (evidence: `docs/spikes/2026-09-29-langgraph-durable-approval.py`): fan-out of one worker per item (`Send`), a pause for the owner's approval (`interrupt`) that survives the process exiting, and resume from the local SQLite checkpoint in a new process (`Command(resume=...)`). That is "nothing sends without the owner" as a durable, resumable workflow — and heavy jobs become graphs of small resumable steps. Runs locally, no server.
- **LangChain's model layer does not:** the providers here are CLIs we wrap ourselves, so its integrations don't apply; the wrapper class broke twice on attribute shadowing in the spikes. Our own `Backend.ask(prompt, output_model) -> model` (one small class per CLI) is simpler and testable. `langchain-core` still arrives as LangGraph's dependency; an API-key backend can later wrap a LangChain model behind the same interface.
- **Any technology:** a graph node calls a backend (Claude, Codex, Gemini, a future API) or a plugin through our own interfaces, so new tech is a new backend/plugin, not a graph change. Heavy tool work stays in the CLIs' own agent modes, run as nodes.
