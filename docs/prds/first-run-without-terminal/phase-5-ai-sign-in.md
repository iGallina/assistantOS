# Phase 5: Claude sign-in from setup

**Parent PRD:** [first-run-without-terminal-prd.md](first-run-without-terminal-prd.md)
**Technical design:** [technical-design.md](technical-design.md) — relevant sections: "The two sign-ins" (AI sign-in, Which Claude account runs), "Setup" (Long-running sign-ins, What the sign-ins never write), "Interfaces" (`ai/start`, `ai/code`), "Open Questions" (1)

## Summary
The owner connects their Claude subscription from the setup screen by signing in through the browser, with no
command. The AI step shows as done once the installation's AI answers the test request.

## Acceptance criteria covered
AC-SETUP-02,
AC-SETUP-06, AC-SETUP-07, AC-SETUP-08 (also apply to this phase's work)

## Out of scope for this phase
Hermes's own AI sign-in (PRD Out of Scope, AUTH-001).

## Phase dependencies
3 (the AI step screen and its test request).

## Phase-specific notes
Waits on spike S1 (technical design, Open Question 1): it runs in the Windows VM before this phase is built. No other
phase waits on it.
