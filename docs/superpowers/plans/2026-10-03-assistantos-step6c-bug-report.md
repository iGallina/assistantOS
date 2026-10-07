# assistantOS build step 6c — bug report with a local anonymizer

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans.

**Goal:** an owner reports a core bug upstream in one command, and nothing private leaves the machine: the report is
masked locally, saved, shown, and only the owner's own click on GitHub's form sends it.

**Architecture:** `bugreport.py` — `mask(text, names) -> str` (deterministic: keys/tokens, WhatsApp ids, e-mails,
CNPJ, CPF, cards, phones, then the contacts list = item titles + owner name, then the home folder) and
`build_report(home, description) -> str` (description, versions, OS, `aos doctor` output, AI calls of the last 7
days, tail of `local/state/errors.log`), `issue_url(title, body)` (prefilled `issues/new`, cut to fit a URL).
`aos bug-report "<o que aconteceu>"` saves `local/reports/bug-<stamp>.md`, prints it, asks `[s/N]`, and only on
"s" opens the form. The CLI now appends every pass error and any crash traceback to `local/state/errors.log` —
Windows had no log at all.

**Constraints:** mask before anything is written or shown; dates, times, versions and durations survive; no
network call before the owner says yes, and then only the browser; a non-interactive run never opens anything.
Jev pre-classification is not built: allowed by the decision, not needed for the report to work.

**Tests:** each pattern masked (BR phones in all common shapes, international, JID, e-mail, CPF, CNPJ, card, keys,
contact names case-insensitively, home path); dates/versions/durations untouched; report carries doctor output and
errors masked; URL stays under the limit; `aos run` errors land in errors.log; `aos bug-report` answers "n" → no
browser, "s" → browser with the masked body, no tty → no browser.
