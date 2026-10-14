# First Run Without a Terminal - Business Assumptions

<!-- ⚠️ EDITING THIS FILE? LOAD THE `assumptions-document-writing` SKILL FIRST ⚠️
     It owns this document's format, and most edits here are made by sessions
     doing something else — recording a ruling while building a phase — which is
     exactly how the format drifts. Folding a stakeholder's answers? Load
     `assumptions-document-feedback` as well.

     Superseded entry text comes OUT — version control holds it, and each entry
     records its ruling date as the handle. Do not layer history under a live
     entry, do not start a history file, and keep ONE Last Updated line.

     ⚠️ ASSUMPTION IDs ARE PERMANENT - DO NOT RENUMBER ⚠️
     Stakeholders reference these IDs in email feedback.
     Gaps in numbering (e.g., DATA-001, DATA-003) are expected
     when assumptions are validated and moved. NEVER close gaps. -->

**Last Updated**: 2026-10-13
**Status**: DRAFT - Pending business validation

**Document Purpose**: This document lists the business assumptions we're making to proceed with the
[First Run Without a Terminal PRD](first-run-without-terminal-prd.md). We're not waiting for answers. We're proceeding
with these assumptions and need business validation to confirm or correct any that are wrong.

---

## Scope Assumptions

### SCOPE-001. Build the screen-based setup for Windows only, leaving the Mac on today's steps?

**Assumption**: Only Windows owners get setup through screens. A Mac install keeps today's terminal steps, run by
whoever installs.

**Evidence**: The first customers are owner-operators on Windows and a phone (`docs/decisions.md`, 2026-09-28). The
only real install so far was on Windows. The Mac path today is `install/install.sh`, run from a copy of the repository
by whoever installs.

**Confirm or Correct**:
- [ ] Correct — Windows only
- [ ] Wrong — Mac owners need it in the same release
- [ ] Wrong — different approach: _______________

**Confidence**: 80% | **Impact if Wrong**: 🟡 MEDIUM

---

## Sign-in Assumptions

### AUTH-001. Accept that an owner signs in to the AI twice, once in Hermes and once for the background summaries?

**Assumption**: The owner connects an AI subscription twice. The first time is in Hermes's own first-launch screens,
for chatting with the assistant. The second is in assistantOS setup, for the summaries and drafts the assistant
prepares every 5 minutes. An owner who uses Claude signs in to the same Claude account both times.

**Evidence**: Hermes manages its own subscription and its own sign-in. The 5-minute pass calls the owner's Claude Code
sign-in, which is separate. Using one sign-in for both would mean the pass runs through Hermes's connection instead:
the product would work the same, but the change is much larger.

**Confirm or Correct**:
- [ ] Correct — two sign-ins are acceptable for now
- [ ] Wrong — one sign-in only: the background summaries must use whatever Hermes is connected to
- [ ] Wrong — different approach: _______________

**Confidence**: 55% | **Impact if Wrong**: 🔴 HIGH

---

## Interface Assumptions

### UI-001. Make the assistantOS page, not Hermes, the place where a new owner makes their daily decisions?

**Assumption**: When setup finishes, it hands the owner to the assistantOS page, and the desktop shortcut keeps
pointing there. The page is where the owner decides about conversations every day. Hermes is where they talk to the
assistant: `/onboard`, meeting prep, questions.

**Evidence**: The page already shows every followed conversation with its draft and its buttons. In Hermes, `/decidir`
goes through the same list one conversation at a time, inside a chat. The debrief's complaint was about the amount of
information on the page, not about the page as the place for daily decisions.

**Confirm or Correct**:
- [ ] Correct — the page is where the owner decides; Hermes is for conversation
- [ ] Wrong — Hermes (`/decidir`) is where the owner decides; the page is secondary
- [ ] Wrong — different approach: _______________

**Confidence**: 60% | **Impact if Wrong**: 🟡 MEDIUM

### UI-002. Show "Copiar rascunho", "Abrir no WhatsApp" and "Feito" first, and put the other actions behind one click?

**Assumption**: On the decision list, each conversation shows three actions: **Copiar rascunho**, **Abrir no
WhatsApp** and **Feito**. **Amanhã**, **Aguardando…**, **Ignorar**, **Contexto completo** and **Pedir ao assistente**
are behind one "Mais opções" click on that conversation.

**Evidence**: Today, each conversation shows seven buttons and a request box. The usual path on a conversation that
needs a decision is to copy the draft, open WhatsApp to send it, and mark it done.

**Confirm or Correct**:
- [ ] Correct as stated
- [ ] Wrong — the three actions shown first should be: _______________

**Confidence**: 50% | **Impact if Wrong**: 🟢 LOW

### UI-003. Keep the page on the decision list for good, not only during the owner's first days?

**Assumption**: The page always opens on "Decidir agora", with the other sections one click away. There is no
switch to a fuller view after the first week.

**Evidence**: An owner who knows the product still starts the day with what needs them. A view that changes after a
date is one more thing to explain.

**Confirm or Correct**:
- [ ] Correct — always open on the decision list
- [ ] Wrong — show every section once the owner has used it for a week
- [ ] Wrong — different approach: _______________

**Confidence**: 65% | **Impact if Wrong**: 🟢 LOW

---

## Validated Assumptions

| ID | Assumption | Validated | Notes |
|----|------------|-----------|-------|
