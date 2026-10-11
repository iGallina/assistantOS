---
name: audit
description: Use when the owner (or whoever set up the assistant) asks to audit the assistant, check whether it really works, score it, find broken routes or missing connections, or says "audita", "está funcionando?", "audit". Scores context, connections, capabilities and routine from evidence only, saves a dated report and tracks findings across runs.
version: 1.0.0
author: assistantOS
license: MIT
metadata:
  hermes:
    tags: [assistantOS, audit, reliability]
    related_skills: [level-up, link, grill-me]
---

# Audit — does the assistant really work?

Check whether this assistant finds the right information and does useful work reliably, and name the changes that
would help the owner most. Score **Contexto, Conexões, Capacidades e Rotina**, 25 points each, with
[rubric.md](rubric.md). Call the number **confiabilidade verificada**: it measures evidence, not how useful the
assistant feels. A folder, an installed skill, a configured key or a confident claim is not proof that something works.

Read-only toward everything it inspects. Its one default write is a new report in `local/audits/` (see
[history.md](history.md)); saving it is part of the skill. An explicit "não salva" from the owner wins.

## 1. Scope and evidence

- Date, profile, and the assistantOS core folder (Windows: `%LOCALAPPDATA%\assistantOS\core`).
- Load the latest comparable report and its finding ledger from `local/audits/` before choosing what to probe
  ([history.md](history.md)). Recheck important earlier findings; never assume they still hold.
- Read `SOUL.md`, `local/context/index.md` and the pages it routes to. Identify the owner's role, main goal, current
  priorities and up to three important workflows from real context. Unfilled templates count for nothing.
- Collect, read-only: `hermes -p assistantos skills list`, `hermes -p assistantos mcp list` and `mcp test` for the
  assistantOS server, `hermes -p assistantos cron list` / `cron runs` / `cron doctor`, `hermes status`. From the core:
  `uv run aos doctor`, the scheduled pass (`uv run aos schedule status`), `local/state/errors.log`, and the daily
  report in `local/reports/`. **Never** run `doctor --fix`, a cron job, a pass, or anything that sends or repairs.
- Label each finding **verificado**, **documentado mas não verificado**, **ausente**, **desatualizado** or
  **conflitante**, with a file/line, command output or dated run as evidence. A file's modification time is not proof a
  refresh ran. Out of time → mark unverified; never award points for what was not checked.

## 2. Routing and context

Map **need → index → source → freshness rule** for the owner's real needs: the business, people, priorities and
commitments, original records, project deliverables, external systems. Then follow the declared routes for five
questions adapted to the owner's work:

1. What does the owner do, for whom, and what matters now?
2. Where is the current priority or commitment, and how would I verify it?
3. Where is the latest deliverable and next step of an important active project?
4. Where is an earlier decision or lesson, and its source?
5. Where is a commonly needed external record or document, and how is it reached?

For each: question, route tried, source, result, and whether it was found **diretamente**, only by **busca ampla**, or
**não encontrado**. A broad search that finds the answer does not prove the route works.

Check freshness and authority: changing facts (prices, balances, deadlines) must resolve to a live source or a dated
export, not to a copy in the context. Flag stale numbers presented as current, duplicated sources with no clear owner,
and anything a fresh session could not resume without this conversation.

## 3. Hermes and assistantOS checks

- **Skills:** every skill `SOUL.md` mentions is listed by Hermes and enabled; their support files resolve.
- **Context routes:** every path in `local/context/index.md` exists (or is marked as an external link).
- **Connections:** the assistantOS MCP server answers `mcp test`; each area in `local/context/connections.md` has a
  real successful read with a date, or is honestly "não conectado". A configured key is not a working connection.
- **Routine:** the 5-minute pass is scheduled and its recent runs succeeded (daily report, `errors.log`); Hermes cron
  jobs show successful due runs (`cron runs`, `cron doctor`). Configuration alone is not a run.
- **Boundaries:** nothing in the skills, cron jobs or gateway can send a message on the owner's behalf without their
  click; the gateway answers only the owner.

## 4. Score and prioritise

Read the full [rubric.md](rubric.md); assign all 20 criteria, apply its caps, and show the four subtotals, raw total,
caps with reasons, final score and stage. Unverified is not broken — say which.

Rank gaps by effect on the owner's work: wrong or stale answers and missing access first, tidiness last. Up to three
concrete actions, each labelled **reparo**, **verificar** or **melhoria opcional**, with evidence, the exact next step
and the check that proves it done. Never invent three faults in a healthy setup. Give each underlying issue one stable
ID and reuse it; never count one problem twice.

## 5. Report

Write the report with [templates/report.md](templates/report.md), save it in `local/audits/` without overwriting, read
it back, and link the saved file. In the chat, in the owner's language and short:

1. Conclusion: what works, the most consequential problem, what was and was not checked.
2. The five routing probes.
3. What works (up to three, with evidence).
4. The score: four rows `/25`, raw total, caps, final `/100`, stage.
5. Progress since the last audit (or "primeira linha de base").
6. Up to three actions, and a ready `/level-up` prompt for the highest-value gap (`/link` for a routing-only fix).

Suggest re-running after the chosen fix, weekly while setting up, monthly after. Never promise a higher score from
another run alone.
