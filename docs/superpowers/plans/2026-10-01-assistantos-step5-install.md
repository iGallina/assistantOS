# assistantOS build step 5 — install, schedule, doctor checks

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans.

**Goal:** on a clean Windows PC (and macOS), one script turns a clone of the owner's repo into a running assistant:
Python + dependencies, the tools (wacli, fizzy, bws via release zips; Claude Code via its own script), `aos init`, the
5-minute pass registered with the OS scheduler, and `aos doctor` green except for the logins only the owner can do.

**Architecture:** the shell scripts stay tiny — they bootstrap `uv` and hand over to Python (`aos setup`), because only
Python is testable on both OSes. `platform/` holds the four OS-specific actions (spec): register/remove the scheduled
pass, notify, open a draft, check a process — step 5 does the first. `aos doctor` gains the check deferred from step 2:
the backend CLI is installed (login is reported, not tested, until a live doctor exists).

**Constraints:** no executables of ours; Windows scheduled task runs `powershell -NoProfile -ExecutionPolicy Bypass`
(so the machine's script policy is never changed); the task uses the scheduler's default "don't start a new instance"
(why `aos run` has no lock); every tool download is pinned to a version and checked against the release's SHA-256;
`aos setup` is idempotent; nothing asks for a password — logins are listed for the owner as next steps.

## Tasks

1. **`platform/` scheduler** — `schedule_install(home, minutes=5)`, `schedule_remove()`, `schedule_status()`; Windows:
   `Register-ScheduledTask` (task name `assistantOS`), macOS: a LaunchAgent plist (`me.assistantos.run`), Linux: a
   crontab line. Unit tests build the exact command/plist without running it; CI runs install → status → remove on
   both OSes for real.
2. **`aos setup`** — `init` if needed, tools check (which ones are missing, with the install command), schedule
   install, `doctor`. **`aos doctor`** — backend CLI on PATH (`claude`/`codex`), wacli/fizzy present when their plugin
   is on.
3. **`install/install.ps1`, `install/install.sh`** — install uv (official script), `uv sync`, download the pinned tool
   zips (hash-checked) into `local/bin`, Claude Code via `irm https://claude.ai/install.ps1 | iex` / `curl … | bash`,
   then `uv run aos setup`. CI: a fresh `windows-latest` and `macos-latest` run the script end to end and finish with
   `aos doctor` showing only the owner-login items.
4. Docs: `README.md` "Install" (pt-BR first) — three commands and the logins that follow.
