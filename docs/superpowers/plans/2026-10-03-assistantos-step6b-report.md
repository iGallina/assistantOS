# assistantOS build step 6b — daily report

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans.

**Goal:** one self-contained HTML page per day that tells the owner what came in, what needs a decision, what the
background AI did and cost in calls, and the next prompts worth running — so nothing that needs the owner is lost
even when the page and Fizzy were not opened.

**Architecture:** `report.py` — `build_report(store, cfg, today) -> dict` (pure: reuses the page's `build_state` for
sections) and `write_report(store, cfg, today, dir) -> Path` (renders with `html.escape`, writes
`local/reports/YYYY-MM-DD.html`, rewriting today's file). `aos run` rewrites it after every pass; `aos report` writes
it and opens it. Store gains `runs_between(start, end)`.

**Constraints:** no model call — sweeps are code; the suggested prompts are built from text the model already
wrote (briefs' next step, "needs a session" replies). Today = the owner's local day. Every message text is escaped.
Strings from the locale files. `local/reports/` is git-ignored (it holds client messages).

**Tests:** only today's incoming messages count; decide list matches the page; open and needs-session requests
listed; runs aggregated per job/backend for today only, brief cap shown; a session prompt carries the ask and the
reply; contact text is escaped; today's file is rewritten; `aos run` writes it; `aos report` prints its path.
