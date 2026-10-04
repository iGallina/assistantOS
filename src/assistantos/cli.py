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
from .platform import scheduler
from .store import Store
from .surfaces import load_surfaces
from .tools import ToolError, install_tools


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
        cfg = load_config(h / "local" / "config")
        lang = cfg.owner.language
        plugins = load_plugins(h / "local" / "config") + load_surfaces(h / "local" / "config")
        print("✓ " + t("doctor.config_ok", lang))
        exe = shutil.which(cfg.backend.kind)
        ok = ok and exe is not None
        print(f"✓ {t('doctor.backend_ok', lang, kind=cfg.backend.kind, path=exe)}" if exe
              else f"✗ {t('doctor.backend_bad', lang, kind=cfg.backend.kind)}")
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
        surfaces = load_surfaces(h / "local" / "config")
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
    r = run_pass(store, plugins, backend, Jev(store, owner=cfg.owner.name), cfg, today, surfaces)
    print(t("run.summary", lang, new=r["new_events"], briefed=len(r["briefed"]), requests=len(r["requests"]), errors=len(r["errors"])))
    for line in r["errors"] + r["surfaced"]:
        print("    " + line)
    return 0


def cmd_page(h: Path, port: int) -> int:
    from .page.server import make_server
    lang, tz = "pt-BR", "America/Sao_Paulo"
    try:
        o = load_config(h / "local" / "config").owner
        lang, tz = o.language, o.timezone
    except ConfigError:
        pass  # the page still opens; `aos doctor` names the config problem
    srv = make_server(h / "local" / "state" / "aos.db", port, lang, lambda: datetime.now(ZoneInfo(tz)).date())
    print(f"http://127.0.0.1:{srv.server_address[1]}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def cmd_schedule(h: Path, action: str) -> int:
    sch = scheduler()
    if action == "install":
        problem = sch.install(h, shutil.which("uv") or "uv")
    elif action == "remove":
        problem = sch.remove()
    else:
        st = sch.status()
        print(st or t("schedule.none"))
        return 0 if st else 1
    print(f"✗ {problem}" if problem else f"✓ {t('schedule.' + action)}")
    return 1 if problem else 0


def cmd_setup(h: Path) -> int:
    """Idempotent: init (never overwrites), schedule the pass, then doctor says what is still missing."""
    cmd_init(h)
    rc = 0
    try:
        for line in install_tools(h / "local" / "bin"):
            print("✓ " + line)
    except ToolError as e:
        print(f"✗ {e}")
        rc = 1
    rc = cmd_schedule(h, "install") or rc
    return cmd_doctor(h) or rc


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
    sub.add_parser("page").add_argument("--port", type=int, default=8422)
    sub.add_parser("setup")
    sub.add_parser("schedule").add_argument("action", choices=["install", "remove", "status"])
    a = p.parse_args(argv)
    h = home()
    os.environ["PATH"] = str(h / "local" / "bin") + os.pathsep + os.environ.get("PATH", "")  # tools `aos setup` installed
    if a.cmd == "schedule":
        return cmd_schedule(h, a.action)
    if a.cmd == "page":
        return cmd_page(h, a.port)
    return {"init": cmd_init, "doctor": cmd_doctor, "run": cmd_run, "setup": cmd_setup}[a.cmd](h)
