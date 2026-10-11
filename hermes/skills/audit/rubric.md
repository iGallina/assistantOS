# Rubric v1 — confiabilidade verificada

## Scoring rules

Five criteria per dimension, 5 points each. Use **0, 1, 3 or 5 only**: the highest anchor fully supported by evidence.
**0** = absent, contradicted, or not evidenced even at 1. Higher anchors include the checks below them. Never
interpolate, start from full and deduct, reward irrelevant infrastructure, or replace missing evidence with optimism.

Multi-part anchors need every part. A bounded sample proves the sample, not the whole system: name it. With no
relevant workflow or connection identified, the criteria that depend on them score 0. Documentation can earn 1 where
stated; it is not a working result.

## Contexto — can a fresh session understand the owner and find things? (25)

| ID | Criterion | 1 | 3 | 5 |
|---|---|---|---|---|
| C1 | Owner context | Real (non-template) identity and purpose exist | Identity, customers/people, priorities and preferences have specific usable sources | All of those agree across sampled sources, with concrete priorities and clear expectations |
| C2 | Routing | `local/context/index.md` gives at least one usable route | 3 of the 5 probes succeed through declared routes; needed indexes exist | All 5 succeed through declared routes; no unexplained important omission or broken sampled route |
| C3 | Freshness | Changing facts carry a source or as-of date | Sampled changing facts have refresh rules and current evidence, or are marked historical with a route to the current source | All sampled current facts verified within their interval; no stale copy presented as current |
| C4 | Source authority | At least one canonical source is named | Stable context, current status and original records are told apart; sampled claims link to sources | All sampled authority chains resolve; duplicates have explicit roles; no unresolved conflict |
| C5 | Continuity | A real decision or project-state record exists | The sampled active project has a current deliverable, rationale and next step reachable from its entry | A second project or thread can also be resumed from durable records |

## Conexões — can it reach what it needs? (25)

List the owner's applicable areas first (money, customers/WhatsApp, calendar, team, tasks, meetings, documents); mark
irrelevant ones with a reason from the owner's real work. No reward for tools the owner does not need.

| ID | Criterion | 1 | 3 | 5 |
|---|---|---|---|---|
| N1 | Area access | At least one applicable area has a successful-read record, but fewer than half | At least half, not all, have one | Every applicable area has a successful read within its expected interval |
| N2 | Useful retrieval | A specific query and expected answer are documented | One real priority-related query returns the right record, period and source | Two distinct priority queries return adequate, complete results |
| N3 | Reproducible routes | One connection has its tool and purpose documented | Every area has a route or an explicit "não conectado"; connected routes have safe auth notes and query examples | A sampled route is reproduced without hidden chat context |
| N4 | Action boundaries | Read/write scopes and approval rules are documented | A needed write workflow has an authorised prior success, or the read-only scope is documented and verified | Sampled operations respect permissions with verified duplicate/failure safeguards; nothing sends without the owner's click |
| N5 | Freshness and failure visibility | Freshness expectations are documented | Sampled reads are within them and failures are shown, not replaced by unlabelled old data | Every area has recent success plus demonstrated stale/expired handling for one connection (e.g. WhatsApp disconnected shows in the daily report) |

## Capacidades — do the workflows produce usable results? (25)

Up to three priority workflows, chosen before looking at their outputs. A missing workflow a priority needs stays a gap.

| ID | Criterion | 1 | 3 | 5 |
|---|---|---|---|---|
| P1 | Fit and invocation | A workflow has a clear trigger tied to a need | One sampled workflow ran successfully with the intended inputs | All sampled workflows have successful runs; overlapping triggers are clearly bounded |
| P2 | Output quality | An example output and acceptance criteria exist | One real output was checked against meaningful criteria | All sampled workflows have usable outputs verified against criteria |
| P3 | Failure handling | Missing-input/error cases are documented | One relevant failure case was tested and handled | Every sampled workflow has a boundary-case result and respects its limits |
| P4 | Discoverability | Dependencies and how to invoke are documented | Entry points and references resolve; Hermes lists the skills | A clean-session run reproduces the workflow without hidden context |
| P5 | Repeated real use | One dated real use | One workflow with two distinct real uses | All sampled workflows have repeated real use; corrections were folded back and revalidated |

Skill count and file recency score zero by themselves. A fixed script can score as high as a complex skill. Running a
new skill twice in a test is not repeated real use.

## Rotina — does useful work happen reliably over time? (25)

| ID | Criterion | 1 | 3 | 5 |
|---|---|---|---|---|
| D1 | Real trigger | A human ritual or a scheduler configuration exists | At least one enabled trigger with a verified host and expected output | That trigger demonstrably ran unattended where it is meant to run |
| D2 | Due runs | A dated manual completion or failed automatic attempt | One due automatic run completed with its output | Two distinct due runs completed; no unexplained missed runs in the period |
| D3 | Observability | Run status and failure reporting are documented | Runs have durable timestamps and outcomes; failure reporting path verified | A real or safely simulated failure reached the owner (daily report / errors.log) and recovery is evidenced |
| D4 | Control and recovery | Stop, owner and recovery instructions exist | Controls confirmed, plus protection against overlapping runs | A prior or isolated test shows stop/recovery and no duplicate actions |
| D5 | Maintenance | Review frequency is defined | One review fixed a real issue or confirmed none was needed | Two review cycles recorded, with follow-up checks |

Never trigger jobs, change schedules or send test alerts during an audit. A manual-only setup scores at most **10/25 in
Rotina**. A routine enabled today must wait for due-run evidence.

## Caps and stages

1. If the five probes cannot recover the owner's main purpose or any authoritative priority source, **Contexto ≤ 10**.
2. No verified enabled automatic trigger → **Rotina ≤ 10**.
3. Raw total = sum of the four.
4. Total caps (lowest wins): any dimension < 10 → **49**; any < 15, or fewer than two verified due automatic runs →
   **69**; any < 20, or an unresolved routing/authority conflict → **84**.
5. Final = min(raw, caps). Report every cap and why.

| Final | Stage |
|---|---|
| 0–24 | Não comprovado |
| 25–49 | Base |
| 50–69 | Funcionando, com lacunas |
| 70–84 | Confiável no escopo verificado |
| 85–100 | Mantido e comprovado |

Never call a high score fully autonomous or safe. State what was sampled.

## Calibration

- Fresh install, skills listed, keys configured, recent timestamps, no runs → Não comprovado, not 70+.
- Strong context and many skills but no observed outputs or runs → no full Capacidades or Rotina.
- Contexto, Conexões, Capacidades 25 each, Rotina manual-only at 10 → raw 85, final 69.
- All dimensions 21 with two due successes and no conflicts → 84; all 23 → 92.
- A weekly routine with two due runs earns repeat credit; a daily job created today earns none.
