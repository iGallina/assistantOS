---
name: level-up
description: Use when the owner wants to improve one workflow, find what to automate next, fix a gap an audit found, or says "o que dá pra automatizar", "melhorar uma tarefa", "level up". One run = one interview = one delivered improvement (a saved prompt, a skill, a scheduled job, or a verified repair).
version: 1.0.0
author: assistantOS
license: MIT
metadata:
  hermes:
    tags: [assistantOS, automation, improvement]
    related_skills: [onboard, grill-me, link]
---

# Level up — one improvement per run

Each run finds one piece of repetitive work and ships one improvement for it. Run it weekly (Friday works well: look at
the week, ship on Monday) or whenever a manual task starts to itch. Over a few runs the owner starts spotting
opportunities on their own; that is the point.

It is not a planner with ten ideas and not a coach. The owner does the thinking; you run the interview and build.

## Read first

`local/context/index.md`, then `priorities.md`, `about-me.md` (the task that eats the week) and `connections.md` from
`local/context/`; `local/decisions.md` for what was already decided or shipped; the skills and scheduled jobs that
already exist in this profile; the latest report in `local/audits/` if there is one. Ask only for what is not there.

**Coming from an audit or a known gap:** take its evidence and its completion check as the first candidate and skip
the generic interview. If the fix is just "where does this live", that is `/link`. If an existing workflow is broken,
repair it instead of building a duplicate; a verified repair counts as this run's improvement.

## 1. Find the candidate (conversation)

Ask in order, one at a time:

1. "Me conta a sua semana. O que você fez três vezes ou mais?" (frequency)
2. "O que foi braçal, chato, copiar e colar?" (drudgery)
3. "Onde você pensou 'um estagiário esperto faria isso'?" (delegation)
4. "Se amanhã chegassem o dobro de clientes, o que quebraria primeiro?" (bottleneck)
5. "O que traria o dobro de clientes?" (growth lever)

When it helps, ask plainly: "Até onde a IA poderia fazer isso por você?" and "Dá para automatizar só um pedaço, em vez
do trabalho inteiro?"

Output: one to three candidates, ranked, one line each on why it matters. "Escolha uma."

## 2. Scope the chosen one

1. **Bottleneck:** which problem does it solve, or which growth does it open? Tie to the answers above.
2. **Eliminate, then automate, then delegate.**
   - "E se a gente simplesmente parar de fazer isso?" If nothing breaks, the improvement is to stop. Record it in
     `local/decisions.md` and finish; that is a win.
   - Automate what follows clear rules; let the AI draft or classify only the part that needs judgment; keep the rest
     manual.
   - If it is too variable or needs a person's judgment, suggest delegating it to someone and record that.
3. **Map it:** trigger (what starts it), sources (where the information comes from), changes (how it is transformed),
   decisions (where it branches), destination (where the result goes). If the owner cannot describe all five, stop:
   "Se não dá para explicar para uma pessoa, não dá para explicar para a IA. Rascunhe no papel e a gente volta."
4. **How much autonomy:** suggest only → draft for review → run with periodic checks → run alone. **Default to the
   lowest level that solves it.** Push back on "run alone" for a first build. Nothing that sends a message runs alone:
   the owner always presses send.
5. **The number:** more customers, more value per customer, or less cost — plus one metric (response time, minutes per
   week, errors). If there is no number, stop: "Se não mexe em nenhum número, por que construir?"

Write the scope to `local/decisions.md` as a dated entry with all five answers.

## 3. Build it

"Como você quer usar isso?" — offer, simplest first:

1. **A saved prompt** the owner runs by hand. No infrastructure.
2. **A skill that runs a fixed procedure** (a script, no model call) — best for clear rules.
3. **A skill with one model step** — drafting, classifying, summarising.
4. **A scheduled job** (Hermes cron) for something that must happen on a cadence.

Default to the simplest option that works; more autonomy only when the owner asks for it. Create skills and jobs with
Hermes's own skill and cron tools so they live in this profile. Every new artifact starts **supervised**: the owner
runs or reviews it by hand for a week before it runs on its own, and its description says so.

## Output (every run)

1. One dated entry in `local/decisions.md`.
2. One delivered improvement — or a recorded decision to stop or delegate.
3. A short close: what was scoped, what was built, and the reminder that it starts supervised.

## Rules

- One interview, one improvement. Never scope several in parallel.
- The conversation in step 1 always runs, even when the owner arrives with an idea.
- Eliminate before automating; the simplest build before a smarter one; the lowest autonomy that works.
- No number, no build.
- Only `local/decisions.md` and the new artifact are written (or the existing workflow, for a selected repair).
- Nothing is ever sent to anyone on the owner's behalf.

## Verification

- An obviously useless task → the skill suggests stopping it, records the decision and ends.
- "Responder clientes sozinho" on a first build → the skill insists on drafts for review first.
- A task solvable with a fixed rule → the default offered is a skill without a model step.
