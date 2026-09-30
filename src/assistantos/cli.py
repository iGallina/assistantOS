import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from . import __version__
from .backends import BackendError, make_backend
from .config import EXAMPLES, ConfigError, load_config
from .graph import run_pass
from .i18n import t
from .jev import Jev
from .plugins import load_plugins
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
        plugins = load_plugins(h / "local" / "config")
        print("✓ " + t("doctor.config_ok", lang))
    except ConfigError as e:
        ok, plugins = False, []
        print("✗ " + t("doctor.config_bad", lang))
        for p in e.problems:
            print("    " + p)
    for plugin, pcfg in plugins:
        problem = plugin.check(pcfg)
        ok = ok and problem is None
        print(f"✗ {t('doctor.plugin_bad', lang, name=plugin.name, problem=problem)}" if problem
              else f"✓ {t('doctor.plugin_ok', lang, name=plugin.name, detail=plugin.describe(pcfg))}")
    try:
        s = Store(h / "local" / "state" / "aos.db")
        print("✓ " + t("doctor.store_ok", lang, version=s.version()))
        s.close()
    except sqlite3.Error as e:
        ok = False
        print("✗ " + t("doctor.store_bad", lang, error=e))
    return 0 if ok else 1


def cmd_run(h: Path) -> int:
    lang = "pt-BR"
    try:
        cfg = load_config(h / "local" / "config")
        lang = cfg.owner.language
        plugins = load_plugins(h / "local" / "config")
    except ConfigError as e:
        print("✗ " + t("doctor.config_bad", lang))
        for p in e.problems:
            print("    " + p)
        return 1
    store = Store(h / "local" / "state" / "aos.db")
    try:
        backend = make_backend(cfg.backend, store)
    except BackendError as e:
        print("✗ " + t("run.backend_bad", lang, error=e))
        return 1
    today = datetime.now(ZoneInfo(cfg.owner.timezone)).date()
    r = run_pass(store, plugins, backend, Jev(store, owner=cfg.owner.name), cfg, today)
    print(t("run.summary", lang, new=r["new_events"], briefed=len(r["briefed"]), errors=len(r["errors"])))
    for e in r["errors"]:
        print("    " + e)
    return 0


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")  # Windows pipes default to cp1252
    p = argparse.ArgumentParser(prog="aos")
    p.add_argument("--version", action="version", version=f"aos {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("doctor")
    sub.add_parser("run")
    a = p.parse_args(argv)
    return {"init": cmd_init, "doctor": cmd_doctor, "run": cmd_run}[a.cmd](home())
