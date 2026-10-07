"""The daily report: one self-contained HTML page per day in local/reports/, rewritten after every pass. Pure code, no
model call: the suggested prompts are built from text the model already wrote (briefs' next step, session replies)."""
from collections import Counter, defaultdict
from datetime import date
from html import escape
from pathlib import Path

from .i18n import t
from .models import Config
from .page.state import build_state
from .store import Store, local_day


def _problems(errors_log: Path | None, today: date) -> list[tuple[str, int]]:
    """Today's pass errors, one line each, repeats counted: the same failure every 5 minutes is one problem."""
    if not errors_log or not errors_log.exists():
        return []
    day = today.isoformat()
    lines = [l[20:] for l in errors_log.read_text(encoding="utf-8", errors="replace").splitlines() if l.startswith(day)]
    return list(Counter(lines).items())


def build_report(store: Store, cfg: Config, today: date, errors_log: Path | None = None) -> dict:
    start, end = local_day(today, cfg.owner.timezone)
    items, lang = build_state(store, today)["items"], cfg.owner.language
    came_in = []
    for i in items:
        new = [e for e in store.events(i["id"]) if e.direction == "in" and start <= e.at < end]
        if new:
            came_in.append({"title": i["title"], "n": len(new), "last": new[-1].text})
    decide = [{"title": i["title"], "decisao": i["brief"] and i["brief"]["decisao"],
               "proximo": i["brief"] and i["brief"]["proximo_passo"]} for i in items if i["section"] == "decidir"]
    requests = sorted(({"id": r["id"], "title": i["title"], "ask": r["ask"], "state": r["state"], "reply": r["reply"]}
                       for i in items if i["section"] != "resolvidos"   # marking the item done clears its requests
                       for r in i["requests"] if r["state"] != "answered"), key=lambda r: -r["id"])
    spend = defaultdict(lambda: {"calls": 0, "failed": 0, "seconds": 0.0})
    for job, backend, _model, seconds, ok in store.runs_between(start, end):
        row = spend[job, backend]
        row["calls"], row["failed"], row["seconds"] = row["calls"] + 1, row["failed"] + (not ok), row["seconds"] + seconds
    prompts = [t("report.prompt_session", lang, owner=cfg.owner.name, **r) for r in requests if r["state"] == "needs_session"]
    prompts += [t("report.prompt_step", lang, title=d["title"], step=d["proximo"]) for d in decide if d["proximo"]]
    return {"day": today.isoformat(), "came_in": came_in, "decide": decide, "requests": requests,
            "spend": [{"job": j, "backend": b, **v, "seconds": round(v["seconds"], 1)} for (j, b), v in sorted(spend.items())],
            "brief_cap": {"used": sum(r[0] == "brief" for r in store.runs_between(start, end)), "cap": cfg.backend.per_day_cap},
            "prompts": prompts, "problems": _problems(errors_log, today)}


def _render(r: dict, lang: str) -> str:
    T = lambda key, **kw: escape(t("report." + key, lang, **kw))  # noqa: E731
    e = lambda v: escape(str(v)) if v is not None else "—"        # noqa: E731

    def section(key: str, rows: list[str]) -> str:
        return f"<h2>{T(key)} <span>{len(rows)}</span></h2>" + (f"<ul>{''.join(rows)}</ul>" if rows else f"<p>{T('empty')}</p>")

    return f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{T('title', day=r['day'])}</title>
<style>
body {{ font: 16px/1.5 system-ui, sans-serif; max-width: 760px; margin: 0 auto; padding: 16px; color: #1d1d1f; }}
h2 span {{ color: #6e6e73; font-weight: 400; }} li {{ margin: 6px 0; }} small {{ color: #6e6e73; }}
pre {{ white-space: pre-wrap; background: #f5f5f7; border-radius: 8px; padding: 10px; }}
table {{ border-collapse: collapse; }} td, th {{ padding: 4px 12px 4px 0; text-align: left; }}
</style></head><body>
<h1>{T('title', day=r['day'])}</h1>
{section('problems', [f"<li>{e(p)}" + (f" ({n}×)" if n > 1 else "") + "</li>" for p, n in r['problems']]) if r['problems'] else ''}
{section('decide', [f"<li><b>{e(d['title'])}</b>: {e(d['decisao'] or t('page.no_brief', lang))}</li>" for d in r['decide']])}
{section('requests', [f"<li><b>{e(q['title'])}</b>: {e(q['ask'])}<br><small>{e(q['reply'] or t('page.ask_queued', lang))}</small></li>"
                      for q in r['requests']])}
{section('came_in', [f"<li><b>{e(c['title'])}</b> ({c['n']}): {e(c['last'])}</li>" for c in r['came_in']])}
{section('prompts', [f"<li><pre>{e(p)}</pre></li>" for p in r['prompts']])}
<h2>{T('spend')}</h2>
<p>{T('cap', used=r['brief_cap']['used'], cap=r['brief_cap']['cap'])}</p>
<table><tr><th>{T('job')}</th><th>{T('backend')}</th><th>{T('calls')}</th><th>{T('failed')}</th><th>{T('seconds')}</th></tr>
{''.join(f"<tr><td>{e(s['job'])}</td><td>{e(s['backend'])}</td><td>{s['calls']}</td><td>{s['failed']}</td><td>{s['seconds']}</td></tr>"
         for s in r['spend'])}</table>
</body></html>
"""


def write_report(store: Store, cfg: Config, today: date, folder: Path, errors_log: Path | None = None) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{today.isoformat()}.html"
    path.write_text(_render(build_report(store, cfg, today, errors_log), cfg.owner.language), encoding="utf-8")
    return path
