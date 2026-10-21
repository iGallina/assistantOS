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

**Last Updated**: 2026-10-21
**Status**: DRAFT - Pending business validation

**Document Purpose**: This document lists the business assumptions we're making to proceed with the
[First Run Without a Terminal PRD](first-run-without-terminal-prd.md). We're not waiting for answers. We're proceeding
with these assumptions and need business validation to confirm or correct any that are wrong.

---

## Scope Assumptions

### SCOPE-001. Promise the screen-based setup on Windows only, leaving the Mac on today's steps?

**Assumption**: Setup through screens is **promised and tested on Windows only**. A Mac install is not promised it and
keeps today's terminal steps, run by whoever installs.

**Evidence**: The first customers are owner-operators on Windows and a phone (`docs/decisions.md`, 2026-09-28). The
only real install so far was on Windows. The Mac path today is `install/install.sh`, run from a copy of the repository
by whoever installs.

**Confirm or Correct**:
- [ ] Correct — Windows only
- [ ] Wrong — Mac owners need it in the same release
- [ ] Wrong — different approach: _______________

**Confidence**: 80% | **Impact if Wrong**: 🟡 MEDIUM

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

**Assumption**: On the decision list, each conversation shows up to three actions: **Copiar rascunho** (when it has a
draft; which draft: AC-PAGE-05), **Abrir no WhatsApp** (for a person, not a group) and **Feito**. **Amanhã**,
**Aguardando…**, **Ignorar**, **Desfazer** and **Pedir ao assistente** are behind one "Mais opções" click on that
conversation, which also shows the full conversation (AC-PAGE-04).

**Example**: A group with a summary shows **Copiar rascunho** and **Feito**. A person whose wait ran out, with no
summary yet, shows **Abrir no WhatsApp** and **Feito**.

**Evidence**: Today, each conversation shows up to eight buttons (Desfazer only once it is marked) and a request box.
The usual path on a conversation that needs a decision is to copy the draft, open WhatsApp to send it, and mark it done.
The page already shows **Abrir no WhatsApp** only for a person (the link opens a chat by phone number, which a group
lacks) and **Copiar rascunho** only when there is a summary; a draft written on request has its own copy button.

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

### UI-004. Take a conversation off the page and out of Hermes when the owner unticks it?

**Assumption**: When the owner unticks a conversation, it **leaves every list on the page and in Hermes** from the next
pass on, including "Decidir agora", even if a decision was pending. **Nothing is deleted**: ticking it again brings it
back as it was.

**Evidence**: An owner unticks a conversation to stop the assistant following it, typically a noisy group. Keeping it
on the first screen works against the debrief's complaint that the page shows too much. Today the page, and Hermes
through the same list, show every conversation the assistant has ever read, whatever the current list says.

**Confirm or Correct**:
- [ ] Correct — an unticked conversation leaves the page and Hermes and returns if ticked again
- [ ] Wrong — it stays listed until the owner marks it (Feito, Ignorar…)
- [ ] Wrong — different approach: _______________

**Confidence**: 75% | **Impact if Wrong**: 🟢 LOW

---

## Validated Assumptions

| ID | Assumption | Validated | Notes |
|----|------------|-----------|-------|
| SCOPE-002 | Setup connects **Claude only**; switching an installation to ChatGPT stays a support step by whoever installs, sign-in included | ✅ 2026-10-21 | Per the stakeholder (2026-10-21): "quem instala troca a instalação para o ChatGPT à mão, login incluído". In the PRD: Summary, AC-SETUP-02, AC-STATUS-01, Out of Scope |
| AUTH-001 | The owner signs in to the AI **twice** for now: in Hermes's first launch and in assistantOS setup for the summaries | ✅ 2026-10-20 | Per the stakeholder (2026-10-20): two sign-ins for now; one sign-in through Hermes's one-shot mode waits for a VM spike proving the run gets zero tools. In the PRD: Out of Scope, "Hermes's own first launch" |
