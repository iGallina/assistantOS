import argparse
import os
import shutil
import sqlite3
import sys
import tempfile
import traceback
import zipfile
from contextlib import closing, redirect_stdout
from datetime import datetime
from io import StringIO
from pathlib import Path
from zoneinfo import ZoneInfo

from . import __version__
from .backends import BackendError, make_backend
from .bugreport import build_report, issue_url
from .config import EXAMPLES, ConfigError, load_config
from .graph import run_pass
from .i18n import t
from .jev import Jev
from .plugins import load_plugins
from .report import write_report
from .platform import scheduler
from .store import Store
from .surfaces import load_surfaces
from .tools import ToolError, install_tools


def home() -> Path:
    return Path(os.environ.get("AOS_HOME") or Path.cwd())


def log_error(h: Path, text: str) -> None:
    """local/state/errors.log: what `aos bug-report` attaches. The scheduled pass on Windows has no other log."""
    p = h / "local" / "state" / "errors.log"  # ponytail: never rotated; rotate when a real install shows it growing
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {text.rstrip()}\n")


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
    for e in r["errors"]:
        log_error(h, "run: " + e)
    write_report(store, cfg, today, h / "local" / "reports")
    return 0


def cmd_report(h: Path) -> int:
    import webbrowser
    try:
        cfg = load_config(h / "local" / "config")
    except ConfigError as e:
        print("✗ " + t("doctor.config_bad"))
        for p in e.problems:
            print("    " + p)
        return 1
    path = write_report(Store(h / "local" / "state" / "aos.db"), cfg, datetime.now(ZoneInfo(cfg.owner.timezone)).date(),
                        h / "local" / "reports")
    print(path)
    webbrowser.open(path.as_uri())
    return 0


def _lang(h: Path) -> str:
    try:
        return load_config(h / "local" / "config").owner.language
    except ConfigError:
        return "pt-BR"


def cmd_export(h: Path) -> int:
    """Everything the owner has (config, store, reports, logs) in one zip; local/bin is only downloaded tools."""
    path = h / f"assistantos-export-{datetime.now():%Y%m%d-%H%M%S}.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z, tempfile.TemporaryDirectory() as tmp:
        for f in sorted((h / "local").rglob("*")):
            rel = f.relative_to(h).as_posix()
            if not f.is_file() or rel.startswith("local/bin/") or f.name.endswith(("-wal", "-shm", "-journal")):
                continue
            if f.suffix == ".db":  # a consistent copy even if a pass is writing right now
                snap, src = Path(tmp) / f.name, sqlite3.connect(f)
                with closing(sqlite3.connect(snap)) as dst:
                    src.backup(dst)
                src.close()
                f = snap
            z.write(f, rel)
    print(t("export.done", _lang(h), path=path))
    return 0


def cmd_uninstall(h: Path) -> int:
    """Copy first, then stop the scheduled pass. Files stay: the owner deletes them, never us."""
    cmd_export(h)
    problem = scheduler().remove()
    print(f"✗ {problem}" if problem else "✓ " + t("schedule.remove", _lang(h)))
    print(t("uninstall.kept", _lang(h), local=h / "local"))
    return 1 if problem else 0


def cmd_bug_report(h: Path, description: str) -> int:
    import webbrowser
    lang = "pt-BR"
    try:
        lang = load_config(h / "local" / "config").owner.language
    except ConfigError:
        pass
    doctor = StringIO()
    with redirect_stdout(doctor):
        cmd_doctor(h)
    title, body = build_report(h, description, doctor.getvalue())
    path = h / "local" / "reports" / f"bug-{datetime.now():%Y%m%d-%H%M%S}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    print(body)
    print(t("bug.saved", lang, path=path))
    try:
        yes = input(t("bug.confirm", lang)).strip().lower() in ("s", "sim", "y", "yes")
    except EOFError:  # not interactive: never opens anything
        yes = False
    if yes:
        webbrowser.open(issue_url(title, body))
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
    sub.add_parser("report")
    sub.add_parser("export")
    sub.add_parser("uninstall")
    sub.add_parser("bug-report").add_argument("description")
    sub.add_parser("page").add_argument("--port", type=int, default=8422)
    sub.add_parser("setup")
    sub.add_parser("schedule").add_argument("action", choices=["install", "remove", "status"])
    a = p.parse_args(argv)
    h = home()
    os.environ["PATH"] = str(h / "local" / "bin") + os.pathsep + os.environ.get("PATH", "")  # tools `aos setup` installed
    if a.cmd == "schedule":
        return cmd_schedule(h, a.action)
    try:
        if a.cmd == "page":
            return cmd_page(h, a.port)
        if a.cmd == "bug-report":
            return cmd_bug_report(h, a.description)
        return {"init": cmd_init, "doctor": cmd_doctor, "run": cmd_run, "report": cmd_report, "setup": cmd_setup,
                "export": cmd_export, "uninstall": cmd_uninstall}[a.cmd](h)
    except Exception:
        log_error(h, f"aos {a.cmd} crashed:\n" + traceback.format_exc())
        raise
