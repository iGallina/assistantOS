# PRD: First Run Without a Terminal

**Source:** the first customer install and its debrief, 2026-10-08.
**Assumptions:** [assumptions.md](assumptions.md)

## Summary

A new owner finishes setting up assistantOS from screens on their own computer: connecting the AI subscription,
connecting WhatsApp, saying who they are, and choosing which conversations to follow. They never open a terminal or
edit a file. Once set up, the page opens on the one list that matters on day one: the conversations that need the
owner now.

## Business Context

The first real install, on a Windows 11 laptop, showed that the installer is no longer where owners struggle. Four
steps still run in PowerShell:

- the AI sign-in;
- the WhatsApp pairing;
- typing the owner's name into a settings file;
- finding each conversation's code with a command and pasting it into another file.

The debrief was blunt: once the terminal opens, everything after it is new to the owner, and adoption drops. The page
then showed five sections and a row of seven buttons on every conversation. That was before the owner knew what any of
it was for.

Owner-operators are the audience, and they work on Windows and a phone, not in a terminal (`docs/decisions.md`). As
long as the first run needs someone sitting beside the owner, every install is a done-with-you session, which caps how
many owners can start.

## Acceptance Criteria

### Finish Setup From Screens, Not Commands

After the installer, the owner completes every remaining setup step by clicking through screens on their computer.
Nothing asks them to type a command or open a file.

- [ ] **AC-SETUP-01 — Setup opens by itself.** When the installer finishes, setup opens on the owner's screen with no
  further action. The owner can reopen it at any time from the assistantOS page.
- [ ] **AC-SETUP-02 — The AI subscription connects without a command.** The owner connects the AI subscription that
  the background summaries use by following on-screen steps and signing in through the browser. The step shows as
  done only once that subscription has answered a test request.
- [ ] **AC-SETUP-03 — WhatsApp connects by scanning a code on screen.** Setup shows a QR code on screen. The owner
  scans it from WhatsApp → Aparelhos conectados on their phone. The step then shows as done, with the connected phone
  number.
- [ ] **AC-SETUP-04 — Connecting never sends anything.** No setup step sends a message, changes a chat, or writes
  anything to the owner's WhatsApp account.
- [ ] **AC-SETUP-05 — The owner says who they are once.** The owner types their name. The time zone and language come
  from the computer's settings and are shown so the owner can change them.
- [ ] **AC-SETUP-06 — Progress survives leaving.** Each step shows whether it is done. If the owner closes setup and
  reopens it, even after restarting the computer, finished steps stay finished and setup resumes at the first
  unfinished one.
- [ ] **AC-SETUP-07 — Problems are explained in plain Portuguese.** When a step fails, the owner sees in pt-BR what
  went wrong and the one thing to try next, with no technical output. The same failure appears in the daily report's
  problems section.
- [ ] **AC-SETUP-08 — Only the owner's computer can open setup.** No other device on the network can open the setup
  screens, which show the WhatsApp pairing code.

### Choose Conversations by Name

Today the owner looks up a code for each conversation and pastes it into a file. Instead, they see their conversations
by name and tick the ones the assistant should follow.

- [ ] **AC-CHATS-01 — Conversations appear by name.** The owner sees their WhatsApp conversations, people and groups,
  under the names their phone shows, most recently active first, and can search by name. No conversation code is
  shown.
- [ ] **AC-CHATS-02 — Ticking a conversation starts following it.** The owner ticks and unticks conversations. From
  the next pass on, the assistant reads exactly the ticked conversations and no others.
- [ ] **AC-CHATS-03 — The choice can change at any time.** The same screen stays available after setup, showing the
  current choices. Changes made there apply from the next pass.
- [ ] **AC-CHATS-04 — Setup suggests where to start.** The screen suggests starting with the 5 to 10 conversations
  that weigh most on the owner's day. It does not stop them from choosing more or fewer.

### Show That the Assistant Is Working

An owner who has just finished setup needs to see that it worked, without running a check command.

- [ ] **AC-STATUS-01 — Setup ends with a plain check.** The last step runs every check the installation check
  (`aos doctor`) runs today. It lists each one as working or not, and for each problem it names the setup step that
  fixes it.
- [ ] **AC-STATUS-02 — The page says when the assistant last looked.** The page says in words when the last pass ran
  and whether it worked ("Última verificação às 14:35"). When a pass failed, the page says what is wrong.

### Open on What Needs the Owner Now

On day one the owner does not yet know what "Aguardando" or "Depois" are for. The page opens on the conversations that
need a decision and keeps everything else one click away.

- [ ] **AC-PAGE-01 — The first screen is the decision list.** Opening the page shows only "Decidir agora": each
  conversation with what changed, the decision, and the draft. No other section is on the first screen.
- [ ] **AC-PAGE-02 — Everything else is one click away.** One click on the first screen reaches each of "Em aberto",
  "Aguardando", "Depois" and "Resolvidos", and the first screen shows how many conversations each one holds.
- [ ] **AC-PAGE-03 — An empty list says so.** When nothing needs a decision, the first screen says "Nada esperando você
  agora" and when the assistant will look again.
- [ ] **AC-PAGE-04 — Each conversation shows few actions at first sight.** On the decision list, each conversation
  shows at most three actions (which three: UI-002). The other actions are one click away on that same conversation.

## Out of Scope

- **Hermes's own first launch.** Hermes asks the owner to connect its AI subscription on its own screens. This PRD
  does not change that.
- **macOS.** A Mac setup keeps today's steps (SCOPE-001).
- **The phone surface (Fizzy).**
- **Signing the installer.** The Windows SmartScreen warning stays.
- **Choosing a different AI provider** (Codex, Gemini). Claude stays the default; changing it is still done by whoever
  installs.
