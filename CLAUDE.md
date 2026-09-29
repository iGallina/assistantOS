# assistant-os

An installable personal AI assistant for owner-operators: **Python + PowerShell install scripts** that set up **Claude Code or Codex CLI** with the user's LLM of preference, **Jev** (TypeSafe System One) for fast classification, and open-source tooling (**Fizzy** as the phone surface, WhatsApp via `wacli`, e-mail, a scheduled loop) — so the messages and tasks that need the owner never get lost.

Born from Ian Gallina's personal AIOS (`~/Projetos/AIS-OS`, private), which runs this loop for him every day. This repo is the product; AIS-OS stays his working system and the proving ground.

`AGENTS.md` and `CLAUDE.md` are identical — edit both together.

## Decisions (2026-09-28 — details and reasons in `docs/decisions.md`)

| Topic | Decision |
|---|---|
| First customer | Owner-operators (InsightLab's base) who work on **Windows + phone**, not Mac |
| Core | Python (all OSes) + PowerShell (Windows) scripts — no executables, no Rust for now (Rust only later, for tools shipped or run online, never compiled on the user's PC). Agent runtime = Claude Code or Codex CLI (user's provider: OpenRouter, OpenAI, Anthropic…); Jev via its HTTP API for classification |
| Engine | Stays Python stdlib (portable, already proven in AIS-OS) until a measured reason to rewrite |
| Business | Open source (MIT). Ian's revenue = education and services on top (courses, guides, cohorts, done-with-you setup) |
| Licence | Kit-derived files keep Nate Herk's MIT notice (`NOTICE`); the "Three Ms of AI™" name/branding is not used here |
| Repo | Private `iGallina/assistant-os` until the first install works on a real Windows machine, then public. Each installation = the user's own **private** repo created from it with `upstream` = the main repo (not a GitHub fork: forks of a public repo are public); a skill walks the user through the GitHub account + repo |
| Secrets | Bitwarden: `bws` (Secrets Manager, machine token) for the agent's unattended runs, `bw` for the owner's own vault; a skill installs and maintains both |
| Upstream reports | Bugs/improvements to the core go back to the main repo only after a **local anonymizer** (deterministic patterns + contacts list first; Jev only on already-masked text) and the owner's review |
| Updates | `core/` (replaced on update) vs `local/` (owner's scripts + config, never touched); tagged releases + changelog + numbered migrations + self-test + rollback, via an `update` skill |
| Privacy | Runs on the user's own computer, no server of ours: data protection is the user's responsibility; the docs say so plainly |
| Costs | A skill estimates and reports what the whole setup costs per day by provider; the daily report shows spend |
| Coding | Superpowers (brainstorm → plan → deterministic implementation) under the Karpathy principles for every script |
| Surfaces | Fizzy = the kanban and visual feedback; a daily HTML report proposes the next best prompts |

## Where things live

- `docs/vision.md` — who, why, the wedge, the model.
- `docs/decisions.md` — append-only decisions + lessons carried from AIS-OS.
- `docs/engine-inventory.md` — every AIS-OS component: portable / macOS-bound / Ian-specific, and its Windows plan.
- `docs/spikes/` — one file per feasibility spike (yes/no + evidence).
- `docs/discovery.md` — owner-operator interviews (Phase 1).

## Phases

0. Project + context (done 2026-09-28). 1. Validate the wedge with 3–5 owner-operators + Windows spikes. 2. Install MVP — PowerShell/Python scripts (Windows first). 3. Education layer from the build itself. Plan: `docs/vision.md` § Roadmap.

## Rules

- Karpathy principles (`~/.claude/CODING.md`): think first, simplest thing, surgical changes, verify before claiming done, root cause.
- **Nothing sends on the user's behalf without their click.** The assistant drafts and opens; the human sends.
- **No personal data in git**: per-user config lives in git-ignored files with committed `*.example.json` templates; no phone numbers, keys or client names in the repo.
- Background AI is logged (one line per call) and visible to the user.
- Sweeps are code; the model drafts. A model never decides what the user gets to see.
