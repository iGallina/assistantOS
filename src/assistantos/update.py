"""aos update: the newest release tag from `upstream` merged into the owner's own repo. Owner files live in
git-ignored local/, so a merge never touches them. The store is copied first; the new code is tested in a fresh
process (this one still runs the old code); any failure puts code and store back. `uv run` re-syncs the
environment to whichever lockfile is checked out, so a rollback needs no reinstall."""
import shutil
import sqlite3
import subprocess
from collections.abc import Callable
from contextlib import closing, redirect_stdout
from io import StringIO
from pathlib import Path

from .bugreport import UPSTREAM

REMOTE = "upstream"


def _git(home: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=home, capture_output=True, text=True)


def _last(r: subprocess.CompletedProcess) -> str:
    return ((r.stderr or r.stdout).strip().splitlines() or [f"exit {r.returncode}"])[-1]


def _self_test(home: Path, doctor_was_ok: bool) -> str | None:
    uv = shutil.which("uv") or "uv"
    steps = [[uv, "run", "--locked", "aos", "--version"]] + ([[uv, "run", "aos", "doctor"]] if doctor_was_ok else [])
    for argv in steps:  # doctor only has to pass if it passed before: an unfinished setup must not block updates
        r = subprocess.run(argv, cwd=home, capture_output=True, text=True, timeout=600)
        if r.returncode:
            return f"{' '.join(argv[2:])}: {_last(r)}"
    return None


def _doctor_ok(home: Path) -> bool:
    from .cli import cmd_doctor
    with redirect_stdout(StringIO()):
        return cmd_doctor(home) == 0


def _copy_db(src: Path, dst: Path) -> None:
    with closing(sqlite3.connect(src)) as a, closing(sqlite3.connect(dst)) as b:
        a.backup(b)


def update(home: Path, self_test: Callable[[Path, bool], str | None] = _self_test) -> tuple[int, str]:
    if _git(home, "rev-parse", "--git-dir").returncode:
        return 1, f"{home} não é um repositório git: instale a partir do seu repositório do assistantOS"
    if _git(home, "remote", "get-url", REMOTE).returncode:
        return 1, f"sem o remoto '{REMOTE}': git remote add {REMOTE} https://github.com/{UPSTREAM}.git"
    if _git(home, "status", "--porcelain", "--untracked-files=no").stdout.strip():
        return 1, "há mudanças no código do assistantOS (fora de local/): faça commit ou desfaça antes de atualizar"
    if (r := _git(home, "fetch", "--quiet", "--tags", REMOTE)).returncode:
        return 1, f"git fetch {REMOTE}: {_last(r)}"
    tags = _git(home, "tag", "--list", "v*", "--sort=-v:refname").stdout.split()
    if not tags:
        return 0, "nenhuma versão publicada ainda"
    tag = tags[0]
    if _git(home, "merge-base", "--is-ancestor", tag, "HEAD").returncode == 0:
        return 0, f"já na versão mais nova ({tag})"
    doctor_was_ok = _doctor_ok(home)
    prev = _git(home, "rev-parse", "HEAD").stdout.strip()
    db = home / "local" / "state" / "aos.db"
    backup = db.with_name("aos.db.before-update")
    if db.exists():
        _copy_db(db, backup)
    who = [] if _git(home, "config", "user.email").stdout.strip() else ["-c", "user.name=assistantOS",
                                                                         "-c", "user.email=aos@localhost"]
    if (r := _git(home, *who, "merge", "--no-edit", "-m", f"update to {tag}", tag)).returncode:
        _git(home, "merge", "--abort")
        return 1, f"conflito ao juntar {tag} com as suas mudanças no código: {_last(r)}"
    if problem := self_test(home, doctor_was_ok):
        _git(home, "reset", "--hard", prev)  # safe: tracked code was clean before the merge, local/ is ignored
        if backup.exists():
            _copy_db(backup, db)
        return 1, f"a versão {tag} falhou no teste ({problem}); voltei para a anterior, nada foi perdido"
    return 0, f"atualizado para {tag}"
