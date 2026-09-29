import argparse
import os
import shutil
import sqlite3
import sys
from pathlib import Path

from . import __version__
from .config import EXAMPLES, ConfigError, load_config
from .i18n import t
from .store import Store


def home() -> Path:
    return Path(os.environ.get("AOS_HOME") or Path.cwd())


def cmd_init(h: Path) -> int:
    d = h / "local" / "config"
    d.mkdir(parents=True, exist_ok=True)
    created = []
    for ex in sorted(EXAMPLES.glob("*.example.json")):
        target = d / ex.name.replace(".example", "")
        if not target.exists():
            shutil.copyfile(ex, target)
            created.append(target.name)
    print(t("init.created", dir=d, files=", ".join(created)) if created else t("init.nothing", dir=d))
    return 0


def cmd_doctor(h: Path) -> int:
    ok, lang = True, "pt-BR"
    try:
        lang = load_config(h / "local" / "config").owner.language
        print("✓ " + t("doctor.config_ok", lang))
    except ConfigError as e:
        ok = False
        print("✗ " + t("doctor.config_bad", lang))
        for p in e.problems:
            print("    " + p)
    try:
        s = Store(h / "local" / "state" / "aos.db")
        print("✓ " + t("doctor.store_ok", lang, version=s.version()))
        s.close()
    except sqlite3.Error as e:
        ok = False
        print("✗ " + t("doctor.store_bad", lang, error=e))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")  # Windows pipes default to cp1252
    p = argparse.ArgumentParser(prog="aos")
    p.add_argument("--version", action="version", version=f"aos {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("doctor")
    a = p.parse_args(argv)
    return {"init": cmd_init, "doctor": cmd_doctor}[a.cmd](home())
