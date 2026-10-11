import sqlite3
import subprocess

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
