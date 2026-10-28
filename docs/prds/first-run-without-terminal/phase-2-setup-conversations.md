# Phase 2: Setup screens for the owner's name and conversations

**Parent PRD:** [first-run-without-terminal-prd.md](first-run-without-terminal-prd.md)
**Technical design:** [technical-design.md](technical-design.md) — relevant sections: "Setup", "Who the owner is", "Conversations", "Interfaces", "Data Models" (`SetupState`, `Chat`, `followed`)

## Summary
The owner opens setup on their computer, says who they are, and ticks the WhatsApp conversations to follow by name.
From the next look on, the assistant, the page and the Hermes chat app follow exactly those conversations.

## Acceptance criteria covered
AC-SETUP-05, AC-CHATS-01, AC-CHATS-02, AC-CHATS-03, AC-CHATS-04, AC-SETUP-06, AC-SETUP-08,
AC-SETUP-07 (also applies to this phase's work)

## Out of scope for this phase
WhatsApp pairing, the AI step's test, the final check and the installer link (Phase 3); the first-look rule and the
page redesign (Phase 4); the AI sign-in (Phase 5).

## Phase dependencies
1 (the pass record and the problem catalog that `no_chats` and `wa_chat_gone` use).

## Phase-specific notes
The origin guard comes from the change on local branch `page-refuses-other-websites`; it must be merged into this
branch before setup's routes are built.
