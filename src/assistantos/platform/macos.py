"""macOS: the 5-minute pass as a LaunchAgent. launchd starts jobs with a bare PATH, so the plist carries the PATH of
the install (plus local/bin first) — otherwise `claude`/`wacli` would look "not installed" on every pass."""
import os
import plistlib
import subprocess
from pathlib import Path

LABEL = "me.assistantos.run"
PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def plist(home: Path, uv: str, minutes: int = 5, path: str | None = None) -> bytes:
    log = str(home / "local" / "state" / "run.log")
    return plistlib.dumps({
        "Label": LABEL, "ProgramArguments": [uv, "run", "aos", "run"], "WorkingDirectory": str(home),
        "StartInterval": minutes * 60, "RunAtLoad": True, "StandardOutPath": log, "StandardErrorPath": log,
        "EnvironmentVariables": {"PATH": f"{home / 'local' / 'bin'}:{path or os.environ.get('PATH', '')}"},
    })


def _domain() -> str:
    return f"gui/{os.getuid()}"


def install(home: Path, uv: str, minutes: int = 5) -> str | None:
    (home / "local" / "state").mkdir(parents=True, exist_ok=True)
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["launchctl", "bootout", f"{_domain()}/{LABEL}"], capture_output=True)  # idempotent re-install
    PLIST.write_bytes(plist(home, uv, minutes))
    r = subprocess.run(["launchctl", "bootstrap", _domain(), str(PLIST)], capture_output=True, text=True)
    return None if r.returncode == 0 else (r.stderr or r.stdout).strip()


def remove() -> str | None:
    subprocess.run(["launchctl", "bootout", f"{_domain()}/{LABEL}"], capture_output=True)
    PLIST.unlink(missing_ok=True)   # our own file, written by install()
    return None


def status() -> str | None:
    r = subprocess.run(["launchctl", "print", f"{_domain()}/{LABEL}"], capture_output=True, text=True)
    if r.returncode:
        return None
    keep = ("state =", "last exit code", "runs =")
    return "; ".join(l.strip() for l in r.stdout.splitlines() if l.strip().startswith(keep))
