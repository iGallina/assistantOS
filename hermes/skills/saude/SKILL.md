---
name: saude
description: Use only when the owner asks about their own health log — "como está minha saúde", "anota meu peso 91,2", "bebi água", "/saude". A private, on-request log of weight, water and habits kept in local/saude/; never shown anywhere else.
version: 1.0.0
author: assistantOS
license: MIT
metadata:
  hermes:
    tags: [assistantOS, health, private]
---

# Saúde — private, on request

A small private log the owner chooses to keep. Everything lives in `local/saude/`. It is shown **only when the owner
asks**, and never appears in `/decidir`, the daily report, meeting sheets, audits, memory or any other output.

## Setup (first use)

Ask what the owner wants to track — any of: peso, água, um hábito (caminhar, remédio, sono) — and the daily goal for
each (e.g. água: 4 × 650 ml). Write `local/saude/metas.md`. If the owner already exports data from a phone app (a CSV
from a scale or a health app), ask where the file is and record the path in `metas.md`; read it only when asked.

## Logging

| The owner says | Do |
|---|---|
| "peso 91,2" | append `{AAAA-MM-DD},{kg}` to `local/saude/peso.csv` |
| "bebi água" / "mais um copo" | append `{AAAA-MM-DD HH:MM},{ml}` to `local/saude/agua.csv` (default size from `metas.md`) |
| "fiz {hábito}" | append `{AAAA-MM-DD},{hábito}` to `local/saude/habitos.csv` |

Confirm in one line with today's total for that item. Read back the line you wrote; never claim a write that failed.

## Viewing ("como está minha saúde?")

From the files only: today against the goals, the last 30 days (weight trend in kg and the direction, water days that
hit the goal, habit streaks), and the last export's date if one is configured. No advice beyond restating the owner's
own goals; no diagnosis. Numbers come from the files — if a file is missing or empty, say so.

## Rules

- Private: nothing from `local/saude/` is copied into context files, memory, reports, briefs or logs.
- Only on request: never bring it up on your own.
- Nothing is sent to anyone.
