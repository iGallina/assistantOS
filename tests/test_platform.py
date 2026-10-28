import plistlib
import subprocess
import sys
from pathlib import Path

import pytest

from assistantos.platform import macos, windows

HOME = Path("/Users/ana/assistantOS")


def test_windows_script_runs_uv_directly_every_5_minutes():
    ps = windows.install_script(HOME, uv="C:\\Users\\Ana's PC\\.local\\bin\\uv.exe", minutes=5)
    assert "-Execute 'C:\\Users\\Ana''s PC\\.local\\bin\\uv.exe'" in ps          # single quotes escaped
    assert "-Argument 'run aos run'" in ps and f"-WorkingDirectory '{HOME}'" in ps
    assert "-At (Get-Date).AddMinutes(1)" in ps and "(New-TimeSpan -Minutes 5)" in ps and "-MultipleInstances IgnoreNew" in ps
    assert "Register-ScheduledTask -TaskName 'assistantOS'" in ps and "-Force" in ps
    assert "ExecutionPolicy" not in ps                                             # no script, no policy change
    assert "Unregister-ScheduledTask -TaskName 'assistantOS' -Confirm:$false" in windows.remove_script()


def test_macos_plist_carries_path_and_logs():
    p = plistlib.loads(macos.plist(HOME, uv="/Users/ana/.local/bin/uv", minutes=5, path="/opt/homebrew/bin:/usr/bin"))
    assert p["Label"] == "me.assistantos.run"
    assert p["ProgramArguments"] == ["/Users/ana/.local/bin/uv", "run", "aos", "run"]
    assert p["WorkingDirectory"] == str(HOME) and p["StartInterval"] == 300
    assert p["EnvironmentVariables"]["PATH"].startswith(str(HOME / "local" / "bin"))   # tools aos installed come first
    assert p["StandardOutPath"] == str(HOME / "local" / "state" / "run.log")


def test_windows_restarts_the_page_task_only_if_installed():
    ps = windows.restart_page_script()
    assert ps.startswith("if (Get-ScheduledTask -TaskName 'assistantOS-pagina' -ErrorAction SilentlyContinue)")
    stop, start = ps.index("Stop-ScheduledTask -TaskName 'assistantOS-pagina'"), ps.index("Start-ScheduledTask -TaskName 'assistantOS-pagina'")
    assert stop < ps.index(".State -eq 'Running'") < start                      # IgnoreNew drops a start while still running
    assert stop < ps.index("throw 'a tarefa da página não parou'") < start     # still running: say so, never a silent no-op


@pytest.mark.skipif(sys.platform != "win32", reason="the PowerShell parser exists only on Windows")
def test_windows_restart_page_script_parses_as_powershell():
    """Parses only, never runs: CI on Windows catches a syntax slip without restarting anything."""
    check = ("$e = $null; [void][System.Management.Automation.Language.Parser]::ParseInput($env:AOS_PS, [ref]$null, [ref]$e); "
             "if ($e) { $e | ForEach-Object { $_.Message }; exit 1 }")
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", check], capture_output=True, text=True,
                       timeout=120, env={**__import__("os").environ, "AOS_PS": windows.restart_page_script()})
    assert r.returncode == 0, r.stdout + r.stderr
