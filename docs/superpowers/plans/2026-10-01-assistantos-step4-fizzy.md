# assistantOS build step 4 — Fizzy mirror

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans.

**Goal:** every open item is a card on the owner's Fizzy board, so the owner acts from the phone; closing a card marks
the item done, deleting it marks it ignored, an item that reopens reopens its card. Ported from AIS-OS
`scripts/fizzy-sync.py` (minus Reminders and comment requests — those arrive with the request worker).

**Architecture:** `surfaces/fizzy.py` — `FizzyConfig(board, page_url)`, `sync(store, cfg, fz, today) -> list[str]` (log),
`FizzyCLI` (the `fizzy` binary via `shutil.which`, `--quiet` JSON, errors as `FizzyError`); credentials come from the
environment the CLI already reads (`FIZZY_TOKEN`, `FIZZY_ACCOUNT`, later filled from Bitwarden). Store migration 3:
`cards(item_id, card, closed, hash, at)`. The graph gains a `surface` node after `brief`; `aos doctor` checks the board.

**Constraints:** the store is the source of truth; cards made by hand are never touched; a pass with no items touches
nothing; every comment the assistant writes starts with "assistantOS · "; strings from the locale files; a failing
card is logged and the rest continue; nothing is sent to anyone but the owner's own board.

**Tests (fake CLI with board state):** create for open items with tag; no duplicate on a second pass; card closed in
Fizzy → item feito; deleted → ignorado + row removed; item resolved here → card closed; reopened → card reopened +
comment; changed brief → card updated; one failing card does not stop the rest; empty store → no calls.
