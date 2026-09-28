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
