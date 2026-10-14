# PRD: First Run Without a Terminal

**Source:** the first customer install and its debrief, 2026-10-08.
**Assumptions:** [assumptions.md](assumptions.md)

## Summary

A new Windows owner finishes setting up assistantOS from screens on their own computer: connecting their Claude
subscription, connecting WhatsApp, saying who they are, and choosing which conversations to follow. They never open a
terminal or edit a file. Once set up, the assistant looks at the chosen conversations every 5 minutes (each look is a
"pass"), and the page opens on the one list that matters on day one: the conversations that need the owner now.

## Business Context

The first real install, on a Windows 11 laptop, showed that the installer is no longer where owners struggle. Five
steps still run in PowerShell:

- the AI sign-in;
- the WhatsApp pairing;
- typing the owner's name into a settings file;
- finding each conversation's code with a command and pasting it into another file;
- running a check command to confirm it all works.

The debrief was blunt: once the terminal opens, everything after it is new to the owner, and adoption drops. The page
then showed five sections and, on every conversation, up to eight buttons and a request box. That was before the owner
knew what any of it was for.

Owner-operators are the audience, and they work on Windows and a phone, not in a terminal (`docs/decisions.md`). As
long as the first run needs someone sitting beside the owner, every install is a done-with-you session, which caps how
many owners can start.

## Acceptance Criteria

Screen text quoted below is the Portuguese (pt-BR) version. An owner who chose English (AC-SETUP-05) sees the same
text in English.

### Finish Setup From Screens, Not Commands

After the installer, the owner completes every remaining setup step by clicking through screens on their computer:
connect their Claude subscription, connect WhatsApp, say who they are, choose conversations, and a final check. Nothing
asks them to type a command or open a file.

- [ ] **AC-SETUP-01 — Setup opens by itself.** When the installer finishes, setup opens on the owner's screen with no
  further action. The owner can reopen it at any time from the assistantOS page.
- [ ] **AC-SETUP-02 — The AI subscription connects without a command.** Following on-screen steps, the owner signs in
  through the browser to Claude, the AI that writes the summaries (SCOPE-002). The step shows as done only when the
  installation's AI answers a test request.
- [ ] **AC-SETUP-03 — WhatsApp connects by scanning a code on screen.** Setup shows a QR code on screen. The owner
  scans it from WhatsApp → Aparelhos conectados on their phone. The step then shows as done, with the connected phone
  number.
- [ ] **AC-SETUP-04 — Connecting never sends anything.** Apart from adding this computer as a linked device, no setup
  step sends a message, changes a chat, or changes anything in the owner's WhatsApp account.
- [ ] **AC-SETUP-05 — The owner says who they are once.** The owner types their name. The time zone and language come
  from the computer's settings and are shown so the owner can change them.
- [ ] **AC-SETUP-06 — Each step shows what works now, and progress survives leaving.** Each step shows whether what
  it set up works now, and the owner can do any step again. Closing setup or restarting the computer never undoes a
  finished step (one that has ever shown as working); setup reopens at the first step never finished.
- [ ] **AC-SETUP-07 — Every problem is explained in plain words.** Wherever the owner sees a problem (a setup step,
  the final check, or a failed pass on the page), the message says in the owner's language what went wrong and the one
  thing to try next. It shows no technical output and never asks the owner to type a command or open a file. When a
  setup step fixes the problem, the message links to that step.
- [ ] **AC-SETUP-08 — No other device or website can see or change setup.** No other device on the network can
  open the setup screens, which show the WhatsApp pairing code, and no website open in the owner's browser can read or
  change anything setup holds.

### Choose Conversations by Name

Today the owner looks up a code for each conversation and pastes it into a file. Instead, they see their conversations
by name and tick the ones the assistant should follow.

- [ ] **AC-CHATS-01 — Conversations appear by name.** The owner sees their WhatsApp conversations, people and groups,
  under the names their phone shows, most recently active first, and can search by name. No conversation code is
  shown. While WhatsApp is still bringing conversations and names in after pairing, the screen says so and the list
  fills in by itself.
- [ ] **AC-CHATS-02 — The ticked conversations are the ones followed.** The owner ticks and unticks conversations.
  From the next pass on, the assistant reads exactly the ticked conversations, and the page and the Hermes chat app list
  only them. Unticking deletes nothing: ticking a conversation again brings it back as it was (UI-004).
- [ ] **AC-CHATS-03 — The choice can change at any time.** The same screen stays available after setup, showing the
  current choices. Changes made there apply from the next pass.
- [ ] **AC-CHATS-04 — Setup suggests where to start.** The screen suggests starting with the 5 to 10 conversations
  that weigh most on the owner's day. It does not stop them from choosing more or fewer.

### Show That the Assistant Is Working

An owner needs to see that the assistant works without running a check command, and must never be told it works
while setup is unfinished.

- [ ] **AC-STATUS-01 — Setup ends with a plain check.** The last setup step checks each item below and lists it as
  working or not. Each problem is explained as AC-SETUP-07 says, sending the owner where the table says.

  | What is checked | When it fails, the owner is sent to |
  |---|---|
  | The AI subscription is signed in and answers a test request | The AI step (AC-SETUP-02), or whoever installed when the installation was switched to ChatGPT (SCOPE-002) |
  | WhatsApp is linked to this computer and its messages can be read | The WhatsApp step (AC-SETUP-03) |
  | At least one conversation is ticked | The conversations screen (AC-CHATS-02) |
  | The assistant's own settings and its record of conversations can be read | No setup step: the message asks the owner to contact whoever installed |

- [ ] **AC-STATUS-02 — The page says when the assistant last looked.** The page says in words when the last pass ran
  and whether it worked ("Última verificação às 14:35", "Última verificação ontem às 22:10"). When a pass failed, the
  page explains it as AC-SETUP-07 says.
- [ ] **AC-STATUS-03 — Unfinished setup is never shown as working.** While a setup step has never been finished
  (AC-SETUP-06), the page's first screen says setup is not finished and links to the first step never finished, in place
  of the empty-list message (AC-PAGE-03) and the last-check line (AC-STATUS-02). A connection lost after setup is a
  failed pass, explained as AC-STATUS-02 says.

### Open on What Needs the Owner Now

On day one the owner does not yet know what "Aguardando" or "Depois" are for. The page opens on the conversations that
need a decision and keeps everything else one click away.

- [ ] **AC-PAGE-01 — The first screen is the decision list.** Opening the page shows the "Decidir agora" list and
  its conversations (what each shows: AC-PAGE-04). No other section's conversations are on the first screen.
- [ ] **AC-PAGE-02 — Everything else is one click away.** One click on the first screen reaches each of "Em aberto",
  "Aguardando", "Depois" and "Resolvidos", and the first screen shows how many conversations each one holds.
- [ ] **AC-PAGE-03 — An empty list says so.** When nothing needs a decision, the first screen says when the assistant
  will look again, and "Nada esperando você agora" only once it has finished its first look at the ticked
  conversations; before that, it says it is still looking at them for the first time.
- [ ] **AC-PAGE-04 — Each conversation shows only the essentials at first sight.** On the decision list, each
  conversation shows without a click its name, why it is on the list, its newest draft if it has one (AC-PAGE-05), at
  most three actions (which: UI-002), and what the table adds. Everything else is one click away on that same
  conversation: the rest of its summary, the full conversation, the other actions and the "Pedir ao assistente" box.

  | The conversation | Also at first sight |
  |---|---|
  | Its summary covers its last message | What changed and the decision |
  | Its summary is older than its last message | What changed and the decision, marked out of date ("brief anterior à última mensagem"), and that last message |
  | It has no summary yet | Its last message |

- [ ] **AC-PAGE-05 — The draft shown is the newest one.** A conversation's newest draft is the latest one written for
  it, in its summary or on request. It is the one "Copiar rascunho" copies, and it is marked out of date when written
  before the conversation's last message.

## Out of Scope

- **Hermes's own first launch.** Hermes, the chat app installed alongside assistantOS where the owner talks to the
  assistant, asks the owner to connect its AI subscription on its own screens. This PRD does not change that.
- **macOS.** Setup through screens is not promised or tested on a Mac; a Mac setup keeps today's steps (SCOPE-001).
- **The phone surface (Fizzy).**
- **Signing the installer.** The Windows SmartScreen warning stays.
- **ChatGPT instead of Claude.** The installer sets up Claude. Switching an installation to ChatGPT stays a support
  step done by whoever installs, its sign-in included (SCOPE-002).
