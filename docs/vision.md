# Vision

## Who

Owner-operators — people who run a small business or practice themselves (clinics, local services, consultants, D2C founders). They work on a **Windows** PC and, above all, the **phone**. Their business happens in WhatsApp and e-mail; nobody on their side has time to maintain a system.

## The problem

Messages that need the owner get lost between channels. A client asks something on WhatsApp, a supplier replies by e-mail, something delegated never comes back — and nothing reminds the owner at the right moment. Generic chatbots answer questions; they don't keep the owner's open loops.

## What assistant-os does (the wedge — to validate in Phase 1)

One loop, measured:
1. **Listen** to the owner's open loops (WhatsApp via `wacli`, e-mail) — code decides the scope, never the model.
2. **Classify** each new message with **Jev** in ~0.3 s: does it need the owner? which project? what kind of request? (bake-off on real data: Jev 0.96 on request triage, 0.64 on 9-way tagging, AUC 0.79 on "needs a reply" — `docs/decisions.md`).
3. **Brief** what needs a decision with the user's LLM (Haiku-class by default): what changed, the decision, options, a draft in the owner's voice.
4. **Surface it on the phone** as a **Fizzy** card; the owner acts from the card (a comment becomes a request; closing the card closes the loop).
5. **Never send**: drafts open ready to send; the owner presses Send.
6. **Follow-ups with deadlines**: anything delegated gets "waiting on X until date" and comes back overdue with the chase drafted.

KPI: messages that needed the owner and went unanswered for more than 24 h.

## Model

- **Open source (MIT).** Anyone can install it.
- **Revenue = education and services on top**: the build log, decisions and bake-offs become courses and guides; cohorts; done-with-you setup for owners who won't install it themselves. Channels: the InsightLab audience and Skool group.

## Architecture (target)

- Install: a PowerShell script on Windows (`irm …/install.ps1 | iex`) and a shell script on macOS/Linux — no executables. They install Python (uv), git, the agent runtime (Claude Code or Codex + provider config), `wacli`, Bitwarden (`bw`, `bws`); pull secrets from Bitwarden; write per-user config from `*.example.json`; register the scheduled loop (Windows Task Scheduler; launchd/cron elsewhere); `doctor`, `update`, `uninstall`, self-test (one Jev call, one Fizzy card, one listener pass).
- Engine (Python stdlib, from AIS-OS): listener, classifier calls, briefs, request worker, Fizzy mirror, local page. Ported component by component per `docs/engine-inventory.md`.

## Roadmap

| Phase | Goal | Done when |
|---|---|---|
| 0 | Project + context | this repo exists with vision, decisions, inventory (2026-09-28) |
| 1 | Validate the wedge | 3–5 owner interviews in `docs/discovery.md`; Windows spikes answered in `docs/spikes/` |
| 2 | Install MVP (Windows, PowerShell + Python) | a clean Windows PC goes from download to a Fizzy card for a real WhatsApp message, without Ian touching it |
| 3 | Education layer | lesson 1 published from the Jev bake-off; every phase ships a lesson |

## Open questions (Phase 1)

Codex CLI / Claude Code on native Windows (and Codex with a non-OpenAI provider) · `wacli` on Windows · e-mail: IMAP app-password vs Gmail API vs Microsoft Graph · Fizzy hosted (fizzy.do) vs self-hosted · Windows Task Scheduler for a 5-min loop · WhatsApp policy risk of unofficial clients for customers (AIS-OS watch until 2026-10-16).
