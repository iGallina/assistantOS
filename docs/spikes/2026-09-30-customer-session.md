# Customer session 2026-09-30 — Google bridge test on a real account

Replaces the "throwaway test account" plan (Ian, 2026-09-29): run the Apps Script bridge spike with the customer, on their account, in their presence. Bundle: `docs/spikes/apps-script-bridge/`. What it must prove: `docs/decisions.md` → "Plugins, and connecting Google…".

## Before starting (tell the customer)

- A small script goes into **their** Google account and runs as them. It can read mail and create drafts, Sheets and Docs — it has no send action. Google will ask for broad Gmail permission (Apps Script's Gmail access normally includes send at the permission level); note exactly what the consent screen lists.
- Nothing of their mail is printed or saved: the test shows counts and field names only.
- Everything the test creates is removed at the end.

## Steps (≈ 15 min)

| # | Who | Action | Record |
|---|---|---|---|
| 1 | customer | logged into their Google account: script.google.com/home/usersettings → Apps Script API **on** | seconds it took, any confusion |
| 2 | customer | `docs/spikes/apps-script-bridge/spike.sh login` → approve in the browser | |
| 3 | Ian | `spike.sh deploy` | web app URL created (yes/no) |
| 4 | customer | `spike.sh authorize` → editor opens → function `authorize` → Run → accept, incl. "Google hasn't verified this app" → Advanced → Go to … | **screenshot of the consent screen**; did they hesitate at the warning? |
| 5 | Ian | `spike.sh test` | no-secret / wrong secret / GET all `unauthorized`; gmail.search ok; draft id; Sheet row `["ok",42]`; Doc text |
| 6 | Ian | `spike.sh cleanup keep` | draft deleted, Sheet + Doc trashed, clasp logged out; web app still up for step 7 |
| 7 | Ian, 2026-10-08 | `spike.sh check` | `ok: true` → no 7-day expiry. Then the customer deletes the project at script.google.com (or keeps it, if it becomes their install) |

## Result

Write the outcome into `docs/spikes/2026-09-29-apps-script-bridge.md` (YES/NO + evidence) and update the decision entry. The consent-screen scopes decide whether the plugin must switch to the Gmail advanced service (narrower read + draft scopes).
