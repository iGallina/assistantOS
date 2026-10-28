# Phase 4: Page opens on the decision list

**Parent PRD:** [first-run-without-terminal-prd.md](first-run-without-terminal-prd.md)
**Technical design:** [technical-design.md](technical-design.md) — relevant sections: "The page", "Status and problems" (First look done, Next look), "Data Models" (`pass:looked`, `/api/state` additions)

## Summary
The page opens on the conversations that need a decision, with the other sections one click away. Each conversation
shows only what the owner needs at first sight, and the page says when setup is unfinished or nothing is waiting.

## Acceptance criteria covered
AC-PAGE-01, AC-PAGE-02, AC-PAGE-03, AC-PAGE-04, AC-PAGE-05, AC-STATUS-03

## Out of scope for this phase
The AI sign-in from setup (Phase 5).

## Phase dependencies
1 (the pass record behind the last-check and next-look lines); 2 (`followed`, which the first look and the lists
use, and the setup progress keys the "setup not finished" screen reads).
