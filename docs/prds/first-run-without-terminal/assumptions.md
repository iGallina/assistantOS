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

### SCOPE-002. Connect only Claude in setup, leaving a switch to ChatGPT as a support step?

**Assumption**: Setup connects **Claude only**, the subscription the installer sets up. An owner who pays for
**ChatGPT** instead still needs whoever installs to switch the installation to it, **sign-in included**, as today. That
owner does not finish setup alone in this release. On a switched installation, setup's AI step shows as done when
ChatGPT answers its test request.

**Evidence**: The Windows installer offers **no choice of AI**: its welcome screen and its steps name Claude Code only.
Today ChatGPT is a support step after install: change a setting, install the Codex CLI, sign in with `codex login`
(README, "Codex em vez de Claude"). Codex sign-in on Windows is **not proven** yet
(`docs/spikes/2026-09-29-windows-stack.md`). The first real install used Claude.

Against it: the README promises a Claude **or** ChatGPT subscription works, and `docs/decisions.md` (2026-09-29) has
each customer bring Claude, ChatGPT or Gemini. Offering ChatGPT here adds a choice to the installer, a Codex install
and a second sign-in in setup, each to be proven on Windows first.

**Confirm or Correct**:
- [ ] Correct — Claude only in this release; ChatGPT stays a support step
- [ ] Wrong — an owner who pays for ChatGPT must also finish setup without a terminal in this release
- [ ] Wrong — different approach: _______________

**Confidence**: 65% | **Impact if Wrong**: 🔴 HIGH

---

## Sign-in Assumptions

### AUTH-001. Accept that an owner signs in to the AI twice, once in Hermes and once for the background summaries?

**Assumption**: For now, the owner connects an AI subscription **twice**. The first time is in the first-launch
screens of Hermes (the chat app installed alongside assistantOS, where the owner talks to the assistant). The second
is in assistantOS setup, for the summaries and drafts the assistant prepares every 5 minutes (Claude, SCOPE-002). An
owner whose Hermes also uses Claude signs in to the same Claude account both times.

**Evidence**: The stakeholder's decision of 2026-10-11 (`docs/decisions.md`), whole: "The sweep stays in our Python and
reaches Hermes over MCP (`aos mcp`: read, draft, mark — no send tool); Hermes owns the model/subscription, chat, phone
gateway, skills and the distribution (`hermes/`)."

It can be read two ways. **Chat only**, as its first clause suggests and as the installer read it that same day:
updated for Hermes, it still sets up Claude Code for the summaries on its **own, separate sign-in**.

Against it: the same sentence **can be read to** cover **everything**, summaries included (the first Wrong option). The
2026-10-08 debrief's "Hermes handles subscription, not our business" fits either reading.

One sign-in would mean running the pass through Hermes's one-shot mode. By default that mode loads the assistant's
**tools, memory and rules** and **skips approvals**. Hermes has options to limit a run's tools and to skip its rules and
memory, but whether they reach **zero tools** is **not verified**. Our code checks the shape of every answer whatever
runs it; Hermes's free-form answers may only fail that check more often.

Today the pass gives the AI **no tools**. One sign-in first needs proof that a Hermes run also gets **zero tools**,
checked from the run's record (`docs/decisions.md`, 2026-09-28: "Confine agents with `--tools`, not
`--allowedTools`").

We still propose two sign-ins **until one is proven confined**.

**Confirm or Correct**:
- [ ] Correct — two sign-ins are acceptable for now
- [ ] Wrong — one sign-in only: the background summaries must use whatever Hermes is connected to
- [ ] Wrong — different approach: _______________

**Confidence**: 50% | **Impact if Wrong**: 🔴 HIGH

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
