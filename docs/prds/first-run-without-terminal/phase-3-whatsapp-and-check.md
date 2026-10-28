# Phase 3: WhatsApp pairing, AI test and final check

**Parent PRD:** [first-run-without-terminal-prd.md](first-run-without-terminal-prd.md)
**Technical design:** [technical-design.md](technical-design.md) — relevant sections: "Setup" (Opening by itself, Long-running sign-ins, Child processes on Windows, What the sign-ins never write), "The two sign-ins" (all WhatsApp rows, Installation switched to ChatGPT), "Status and problems" (AI test request, Final check), "Interfaces", "Integration Points"

## Summary
Setup opens by itself when the installer finishes. The owner links WhatsApp by scanning a code shown on screen,
checks that the installation's AI answers, and ends with a check that lists what works and what to fix.

## Acceptance criteria covered
AC-SETUP-01, AC-SETUP-03, AC-SETUP-04, AC-STATUS-01,
AC-SETUP-06, AC-SETUP-07, AC-SETUP-08 (also apply to this phase's work)

## Out of scope for this phase
Signing in to Claude from setup (Phase 5): until then the AI step offers only the test request. The page redesign
and the "setup not finished" first screen (Phase 4).

## Phase dependencies
1 (the AI failure classification the test request reuses); 2 (the setup screens, progress keys and conversations
step that the final check reads).

## Phase-specific notes
The README "Install" text changes with AC-SETUP-01; until Phase 5 it still names the AI sign-in as a step for whoever
installs.
