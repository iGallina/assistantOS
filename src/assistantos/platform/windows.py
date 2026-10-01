"""Windows: the 5-minute pass as a Task Scheduler task that runs uv.exe directly — no PowerShell script runs on a
schedule, so the machine's script policy is never involved. IgnoreNew = never two passes at once."""
import subprocess
from pathlib import Path

TASK = "assistantOS"


def _q(s) -> str:
    return "'" + str(s).replace("'", "''") + "'"   # PowerShell single-quoted literal


def install_script(home: Path, uv: str, minutes: int = 5) -> str:
    return (f"$a = New-ScheduledTaskAction -Execute {_q(uv)} -Argument 'run aos run' -WorkingDirectory {_q(home)}; "
            f"$t = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes {minutes}); "
            "$s = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable "
            "-ExecutionTimeLimit (New-TimeSpan -Minutes 30); "
            f"Register-ScheduledTask -TaskName {_q(TASK)} -Action $a -Trigger $t -Settings $s -Force | Out-Null")


def remove_script() -> str:
    return f"Unregister-ScheduledTask -TaskName {_q(TASK)} -Confirm:$false"


def status_script() -> str:
    return (f"$i = Get-ScheduledTaskInfo -TaskName {_q(TASK)} -ErrorAction Stop; "
            "'{0} last={1} result={2}' -f (Get-ScheduledTask -TaskName " + _q(TASK) + ").State, $i.LastRunTime, $i.LastTaskResult")


def _ps(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                          capture_output=True, text=True, timeout=120)


def install(home: Path, uv: str, minutes: int = 5) -> str | None:
    r = _ps(install_script(home, uv, minutes))
    return None if r.returncode == 0 else (r.stderr or r.stdout).strip()


def remove() -> str | None:
    r = _ps(remove_script())
    return None if r.returncode == 0 else (r.stderr or r.stdout).strip()


def status() -> str | None:
    r = _ps(status_script())
    return r.stdout.strip() if r.returncode == 0 else None
