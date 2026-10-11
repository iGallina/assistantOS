---
name: preparar-reuniao
description: Use before a meeting or a recurring check-in ("prepara a reunião com…", "o que eu levo para a daily", "pauta para amanhã") to build a one-page prep sheet, and after it ("resume a reunião", "manda um relatório para…") to draft a status report to someone in the owner's voice. Saves to local/meetings/. Never sends.
version: 1.0.0
author: assistantOS
license: MIT
metadata:
  hermes:
    tags: [assistantOS, meetings, reports]
    related_skills: [decidir, grill-me]
---

# Preparar reunião — before and after

Two modes. Both read only what the owner points to or what is routed in `local/context/index.md`, and write only to
`local/meetings/`.

## Before: the prep sheet

1. Ask, if not given: which meeting, when, with whom, and the goal in one line. Recurring meeting → reuse the last
   sheet in `local/meetings/` for that meeting as the starting point.
2. Gather, citing each source:
   - the owner's priorities (`local/context/priorities.md`) that touch this meeting;
   - from assistantOS, conversations with these people that need a decision or are waiting (`o_que_decidir`,
     `listar_itens` with `aguardando`), with the open question of each;
   - what was promised at the last meeting with them (the previous sheet's "Combinados") and whether it happened;
   - documents or notes the owner names. If something is not reachable, write "não consegui ver: {o quê}".
3. Write `local/meetings/{AAAA-MM-DD}-{reuniao}.md`, one page:
   - **Objetivo** (one line) · **O que mudou desde a última** · **Decisões para levar** (each with a suggested answer
     marked as suggestion) · **Perguntas** · **Combinados da última** (feito / pendente) · **Fontes**.
4. Show it and link the file. Five minutes of reading, at most.

## After: the report to someone

1. Ask who it is for, what period, and where the results are (notes, a sheet, the prep sheet's decisions). Never invent
   a number, a date or a result: what is not in the material stays out, or is marked "a confirmar".
2. Draft it in the owner's tone (`local/context/voice.md`): what was done, what changed, what is next, what is needed
   from the recipient. Short.
3. Add a **Combinados** section to that meeting's sheet with what was agreed, so the next prep picks it up.
4. Show the draft. The owner sends it. If it goes by WhatsApp and the number is known, offer the `wa.me` link with the
   text ready.

## Rules

- Only the owner's own work: never list other people's tasks unless the owner is waiting on them.
- No invented facts; every number cites its source.
- Nothing is sent; nothing outside `local/meetings/` is written.
