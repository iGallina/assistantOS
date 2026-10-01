import plistlib
from pathlib import Path

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
