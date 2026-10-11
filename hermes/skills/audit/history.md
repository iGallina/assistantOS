# Audit history

The dated reports in `local/audits/` are the history; each new report carries the finding ledger forward. No separate
score database, no reliance on this conversation, no scheduling or repairs from here.

## 1. Choose prior evidence

1. List `local/audits/`; read report metadata first. Use `audit_kind: assistantos`, run timestamp, `report_status`,
   rubric version and scope. Other kinds of reports are not baselines.
2. Read the latest applicable report's ledger, plus the latest *complete comparable* one if different. At most two in
   full. Skip partial reports and examples as baselines.
3. Compare scores only for the same profile, rubric and materially the same scope (areas, workflows, probes).
   Otherwise findings can still be compared one by one, but say **pontuações não comparáveis**.
4. No eligible report → **primeira linha de base**.

## 2. Finding identity and status

Each underlying finding gets a stable ID, e.g. `AOS-<run-id>-01`, kept on later runs (match by affected route or
workflow and failure mode). Class (defect, verification gap, opportunity, intentional difference), confidence and
progress status are separate fields. Carry the whole previous ledger forward, including items outside today's sample.

| Status | Requires |
|---|---|
| Novo | First seen in this history ("detectado agora", not "introduzido agora") |
| Ainda aberto | Rechecked and still present |
| Resolvido | The original completion check passes with current evidence — a proposed edit or a claim is not enough |
| Reaberto | Was resolved; the same failure is shown again (same ID) |
| Não verificado | Not covered today; keep the last verified state |
| Não se aplica mais | Requirements or scope changed, with evidence — not a repair |

## 3. Explain progress honestly

Transition table: ID · prior state · this run · evidence · next check. Separate **reparos reais**, **evidência nova**,
**regressões** and **mudanças de escopo ou rubrica**. Show prior and current subtotals only when comparable. Never claim
improvement just because the score rose or the open count fell.

## 4. Save every run safely

1. Real UTC timestamp + random suffix as run ID; file `local/audits/audit-YYYY-MM-DD-HHMMSS-<suffix>.md` from
   [templates/report.md](templates/report.md).
2. Fill every section with evidence or an explicit "não verificado / parcial". No placeholders, no invented results.
3. Create without overwriting (retry with a new suffix on collision). Never rewrite an older report.
4. Read the saved report back (metadata, arithmetic, IDs, no secrets) and link it.
5. Early stop → save `report_status: partial` with `null` scores and reasons.
6. Cannot write → say **relatório não salvo**, give the report in the chat, name the blocker. Never claim it was saved.

Only the new report is written. Reports are point-in-time evidence, never the owner's current business facts.
