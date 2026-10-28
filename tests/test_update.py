import sqlite3
import subprocess

import pytest

from assistantos.update import update

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "init.defaultBranch=main"]


def git(cwd, *args):
    return subprocess.run([*GIT, *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def release(repo, version):
    (repo / "VERSION").write_text(version)
    git(repo, "commit", "-qam", version)
    git(repo, "tag", version)


def setup(tmp_path):
    up = tmp_path / "up"
    up.mkdir()
    git(up, "init", "-q")
    (up / ".gitignore").write_text("local/\n")
    (up / "VERSION").write_text("v0.1.0")
    git(up, "add", ".")
    git(up, "commit", "-qm", "v0.1.0")
    git(up, "tag", "v0.1.0")
    home = tmp_path / "home"
    git(tmp_path, "clone", "-q", str(up), str(home))
    git(home, "remote", "rename", "origin", "upstream")
    (home / "local" / "state").mkdir(parents=True)
    db = sqlite3.connect(home / "local" / "state" / "aos.db")
    db.execute("create table t(v)")
    db.execute("insert into t values ('before')")
    db.commit()
    db.close()
    return up, home


@pytest.fixture(autouse=True)
def _no_real_powershell(monkeypatch):
    """On a Windows dev machine the default restart_page would restart the owner's real page task."""
    from assistantos.platform import windows
    monkeypatch.setattr(windows, "_ps", lambda s: subprocess.CompletedProcess([], 0, "", ""))


@pytest.fixture(autouse=True)
def _no_real_hermes(monkeypatch, tmp_path):
    """A dev machine's own Hermes is never touched: only a fake `hermes` a test puts under tmp_path is found."""
    import shutil
    real = shutil.which
    monkeypatch.setattr("assistantos.update.shutil.which",
                        lambda name: None if name == "hermes" and not str(real(name) or "").startswith(str(tmp_path))
                        else real(name))


def ok(home, doctor_was_ok):
    return None


def test_merges_the_newest_tag_and_keeps_local(tmp_path):
    up, home = setup(tmp_path)
    release(up, "v0.1.1")
    release(up, "v0.2.0")
    rc, msg = update(home, self_test=ok)
    assert rc == 0 and "v0.2.0" in msg and (home / "VERSION").read_text() == "v0.2.0"
    assert (home / "local" / "state" / "aos.db").exists()
    assert update(home, self_test=ok)[0] == 0                         # already current: nothing to do


def test_a_failing_self_test_puts_code_and_store_back(tmp_path):
    up, home = setup(tmp_path)
    before = git(home, "rev-parse", "HEAD")
    release(up, "v0.2.0")

    def broken(home, doctor_was_ok):
        db = sqlite3.connect(home / "local" / "state" / "aos.db")   # the new code migrated the store, then broke
        db.execute("update t set v='migrated'")
        db.commit()
        db.close()
        return "aos --version: ImportError"
    rc, msg = update(home, self_test=broken)
    assert rc == 1 and "ImportError" in msg and git(home, "rev-parse", "HEAD") == before
    assert sqlite3.connect(home / "local" / "state" / "aos.db").execute("select v from t").fetchone() == ("before",)


def test_refuses_edited_code_and_names_a_missing_upstream(tmp_path):
    up, home = setup(tmp_path)
    (home / "VERSION").write_text("mexi")
    assert update(home, self_test=ok)[0] == 1
    git(home, "checkout", "--", "VERSION")
    git(home, "remote", "remove", "upstream")
    rc, msg = update(home, self_test=ok)
    assert rc == 1 and "git remote add upstream" in msg


def test_a_successful_update_refreshes_the_hermes_profile(tmp_path, monkeypatch):
    """New skills reach the owner's Hermes only through `hermes profile update` (it re-reads core/hermes/)."""
    import os
    import stat
    import sys
    up, home = setup(tmp_path)
    release(up, "v0.2.0")
    calls = tmp_path / "hermes-calls.txt"
    bindir = tmp_path / "bin"
    bindir.mkdir()
    if sys.platform == "win32":
        (bindir / "hermes.cmd").write_text(f'@echo %* >> "{calls}"\n')
    else:
        exe = bindir / "hermes"
        exe.write_text(f'#!/bin/sh\necho "$@" >> "{calls}"\n')
        exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", str(bindir) + os.pathsep + os.environ["PATH"])
    rc, msg = update(home, self_test=ok)
    assert rc == 0 and calls.read_text().split() == ["profile", "update", "assistantos", "-y"]


def test_update_without_hermes_still_succeeds(tmp_path, monkeypatch):
    up, home = setup(tmp_path)
    release(up, "v0.2.0")
    monkeypatch.setattr("assistantos.update.shutil.which", lambda name: None if name == "hermes" else "/usr/bin/" + name)
    assert update(home, self_test=ok)[0] == 0


def test_a_successful_update_restarts_the_page_so_it_runs_the_new_code(tmp_path, monkeypatch):
    """The page process keeps the old code until restarted (docs/changes/page-refuses-other-websites)."""
    monkeypatch.setattr("assistantos.update.shutil.which", lambda name: None if name == "hermes" else "/usr/bin/" + name)
    up, home = setup(tmp_path)
    restarts = []
    assert update(home, self_test=ok, restart_page=lambda: restarts.append(1))[0] == 0     # already current
    release(up, "v0.2.0")

    def broken(home, doctor_was_ok):
        return "aos --version: ImportError"
    assert update(home, self_test=broken, restart_page=lambda: restarts.append(1))[0] == 1  # rolled back
    assert restarts == []
    rc, msg = update(home, self_test=ok, restart_page=lambda: restarts.append(1))
    assert rc == 0 and msg == "atualizado para v0.2.0" and restarts == [1]


def test_a_page_that_does_not_restart_keeps_the_update_and_says_what_to_do(tmp_path, monkeypatch):
    up, home = setup(tmp_path)
    release(up, "v0.2.0")
    monkeypatch.setattr("assistantos.update.shutil.which", lambda name: None if name == "hermes" else "/usr/bin/" + name)
    rc, msg = update(home, self_test=ok, restart_page=lambda: "Access denied")
    assert rc == 0 and (home / "VERSION").read_text() == "v0.2.0"
    assert "v0.2.0" in msg and "Access denied" in msg and "saia e entre no Windows" in msg


def test_restart_page_runs_the_windows_task_only_on_windows(monkeypatch):
    from types import SimpleNamespace

    from assistantos import update as u
    from assistantos.platform import windows
    scripts = []
    monkeypatch.setattr(windows, "_ps", lambda s: scripts.append(s) or subprocess.CompletedProcess([], 0, "", ""))
    monkeypatch.setattr(u, "sys", SimpleNamespace(platform="darwin"))
    assert u._restart_page() is None and scripts == []                    # macOS: no page task to restart
    monkeypatch.setattr(u, "sys", SimpleNamespace(platform="win32"))
    assert u._restart_page() is None and scripts == [windows.restart_page_script()]


@pytest.mark.parametrize("ps,problem", [
    (subprocess.CompletedProcess([], 1, "", "a tarefa da página não parou\nAt line:1 char:9\n+ CategoryInfo ...\n"),
     "a tarefa da página não parou"),                                     # one line, not PowerShell's whole trace
    (subprocess.CompletedProcess([], 1, "", ""), "exit 1"),                # a failure with no output is still one
    (subprocess.TimeoutExpired(["powershell"], 120), "timed out"),
    (FileNotFoundError("powershell"), "powershell"),
])
def test_a_failed_page_restart_is_one_line_and_never_a_crash(monkeypatch, ps, problem):
    from assistantos.platform import windows

    def fake(script):
        if isinstance(ps, BaseException):
            raise ps
        return ps
    monkeypatch.setattr(windows, "_ps", fake)
    got = windows.restart_page()
    assert got and problem in got and "\n" not in got
