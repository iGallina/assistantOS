# Engine inventory — what AIS-OS has, and what it takes to run it for a Windows owner

Source: `~/Projetos/AIS-OS/scripts/` (27 files, 2026-09-28) + `tools/`. Classes: **portable** (runs as-is or with config), **macOS-bound** (needs a Windows replacement), **Ian-specific** (his clients or personal apps — the *pattern* may be reusable, the file is not). Client-named files are listed by role.

## The loop (the product core)

| AIS-OS file | Class | What it does | Windows plan |
|---|---|---|---|
| `em-aberto.py` | portable* | local server: items, one status, events, briefs, requests, agents tab, loops | keep; replace its Mac bits: `open_compose` (osascript Mail → `mailto:`/Outlook draft/Graph draft), notifications (osascript → Windows toast + Fizzy), `launchctl kickstart` of the WhatsApp daemon (→ service restart), `pgrep` (→ process check) |
| `em-aberto.local.html` | portable | the page (two tabs, light/dark) | keep |
| `tasks-page.py` | portable* | deterministic item builder (loops, reminders, projects, e-mail) | keep; drop Reminders/agenda via `mac.sh` → Fizzy tasks + calendar API |
| `wa-listener.py` | portable* | WhatsApp listener + local audio transcription | keep if `wacli` runs on Windows (spike); whisper.cpp has Windows builds — make the binary path configurable |
| `brief.py` | portable | Haiku-class decision briefs, no tools | keep; runtime CLI path configurable (Claude Code / Codex) |
| `request-worker.py` | portable* | Jev triage → LLM → allowlisted actions; click-to-run agents | keep; Reminder/event actions via `mac.sh` → Fizzy card + calendar API |
| `jev.py` | portable | Jev client (stdlib HTTP) | keep as-is |
| `fizzy-sync.py` | portable* | two-way mirror to Fizzy; comments → requests | keep (Fizzy CLI is cross-platform — spike); drop the Reminders completion path |
| `contacts.py` | portable | per-user contacts from `config/contacts.json` | keep |
| `mail-inbox.py` | macOS-bound | e-mail via Mail.app (two passes, body cache) | replace: IMAP app-password or Gmail API / Microsoft Graph (spike) — keep the two-pass + cache design |
| `mail-send.sh` | macOS-bound | send via Mail.app | replace: open a draft only (never send on its own) |
| `mac.sh` | macOS-bound | Calendar (icalBuddy), Reminders, Mail counts | replace: calendar API; tasks = Fizzy |
| `aios-status.sh` | macOS-bound | what runs in the background (launchd) | replace: `assistantOS doctor` (Task Scheduler status) |
| `my-tasks.sh` | macOS-bound | one-screen aggregator | superseded by the page + Fizzy |
| `em-aberto.template.html` | legacy | old artifact version of the page | drop |

## Weekly review and WhatsApp hygiene

| AIS-OS file | Class | Windows plan |
|---|---|---|
| `wa-open-loops.sh` | portable (shell + sqlite) | port to Python |
| `wa-review.sh`, `wa-review-rows.py`, `wa-review-apply.py` | portable | keep the Friday "keep / archive" review; the review UI moves into the page or Fizzy |
| `wa-archive-batch.sh` | Ian-specific ops (launchctl) | defer — archive writes are blocked by a WhatsApp app-state issue in AIS-OS anyway |

## Patterns worth productising (files are Ian-specific)

| AIS-OS file (by role) | Pattern |
|---|---|
| PA agent (`pa-inbox.py`) | a trusted contact writes on the business number → drafted reply → owner approves by quoting |
| Client guide agent (client B `…-agent.py`) | a client asks about a delivered guide → answers only from the guide → owner approves |
| Morning sheet for a contract (client A `…-daily-prep.sh`) | a dated prep sheet before a recurring meeting, from the project's own notes |
| Round report (client A `…-report.sh`) | deterministic status report the owner pastes |

## Ian-only (not part of the product)

`mindmap.py` (MindNode), `wispr-meeting.sh` (Wispr Flow meeting capture; revisit if a Windows capture tool is chosen), `sync-codex-skills.sh` (kit maintenance).

## Tools and scheduling

| AIS-OS | Class | Windows plan |
|---|---|---|
| `tools/broker/` (event inbox → Fizzy, dedup, reopen) | portable | keep — runs on any always-on machine or a small VPS |
| `tools/menubar/` (Swift menu-bar icon) | macOS-bound | deferred — Fizzy on the phone is the v1 surface; later a tray icon in Python |
| `launchd/*.plist` (09:30 sheet, 5-min loop, sync daemons) | macOS-bound | replace: Windows Task Scheduler entries / a service registered by the installer |

\* portable with the listed Mac-specific calls swapped out.
