# Spike: the stack on a clean Windows machine, scripts only — YES

**Question:** can every piece install and run on Windows from PowerShell/Python scripts, with no installer executable of ours?
**Evidence:** GitHub Actions `windows-latest` (Windows Server 2025 Datacenter), workflow `.github/workflows/windows-spike.yml`, runs 36587831405 and 36588664040 (2026-09-29).

| Piece | How it was installed | Result |
|---|---|---|
| Python | `irm https://astral.sh/uv/install.ps1 \| iex` → `uv python install 3.12` | 3.12.14, sqlite 3.53.1 — stdlib engine runs as is |
| Claude Code | `irm https://claude.ai/install.ps1 \| iex` (native build) | 2.1.284 |
| Codex CLI | `npm install -g @openai/codex` | codex-cli 0.159.0 |
| wacli | release zip fetched by `Invoke-WebRequest` | 0.19.0 runs; empty store opens (`chats list` rc=0) |
| Fizzy CLI | release zip fetched by `Invoke-WebRequest` | 4.0.1 |
| Bitwarden `bws` | release zip fetched by `Invoke-WebRequest` | 2.1.0 |
| Bitwarden `bw` | `npm install -g @bitwarden/cli` | 2026.9.0 |
| Scheduled loop | `Register-ScheduledTask`, 1-min repetition, `powershell -ExecutionPolicy Bypass` | 3 ticks in 150 s |

**Findings**
- Third-party `.exe` files fetched by a script carry **no Mark-of-the-Web** → no SmartScreen prompt. Confirms: no code-signing certificate while we ship no executables.
- The version checks in run 36588664040 reported `FAIL rc=` with an empty exit code. That was a bug in the spike script: `Select-Object -First 1` stopped the program early, so no exit code was recorded. Each tool printed its version, which proves it ran; the script is fixed.

**Not proven here (next spikes, need a real consumer PC or accounts):**
- Windows 11 Home defaults: script policy `Restricted` (the runner is `RemoteSigned`), Defender/SmartScreen on a personal machine, a non-admin user.
- wacli pairing (QR) and a long-running `sync --follow` on Windows.
- Claude Code / Codex login, and Codex with a non-OpenAI provider (OpenRouter).
- E-mail: IMAP app password vs Gmail API vs Microsoft Graph.
- Windows toast notifications; Fizzy hosted vs self-hosted.
