# Phase 1: Pass record and problem messages

**Parent PRD:** [first-run-without-terminal-prd.md](first-run-without-terminal-prd.md)
**Technical design:** [technical-design.md](technical-design.md) — relevant sections: "Status and problems" (Pass record, Failed pass, Next look, Problems, WhatsApp problems in a pass, AI problems in a pass, Pass time limit, Which problem shows), "The two sign-ins" (Which Claude account runs), "Data Models" (`pass:last`, problem codes), "Integration Points"

## Summary
Every 5-minute look records when it ran and whether it worked, and the assistantOS page says so in words. When a
look fails, the page explains in the owner's language what went wrong and the one thing to try next.

## Acceptance criteria covered
AC-STATUS-02, AC-SETUP-07

## Out of scope for this phase
Setup screens (Phases 2, 3, 5); which conversations a look follows and the problems tied to ticks, `no_chats` and
`wa_chat_gone` (Phase 2); the redesigned first screen and the first-look rule (Phase 4).

## Phase dependencies
None.
