# PRD: The Page Refuses Other Websites

**Source:** noticed during the refinement of `docs/prds/first-run-without-terminal/` (2026-10-13); opened as its own
change by Ian, 2026-10-14.

## Summary

The assistantOS page runs on the owner's own computer and shows their WhatsApp conversations, the summaries and the
drafts. Today any website open in the owner's browser can make the page change things, and a website that tricks the
browser can also read what the page shows. After this change, only the page itself can read or change anything, and
no other website can act through it, read it, or show it inside its own.

## Business Context

The page only listens on the owner's own computer, so other devices on the network cannot reach it. A website open in
the owner's browser is different: the browser runs that site's code on the owner's computer, where the page is
reachable. The page runs from the moment the owner logs in, so any site visited at any time can try.

- **Changing things.** A website can send the page the same requests its buttons send. Knowing a conversation's
  identifier (for a person, built from their phone number), it can mark that conversation done, push it to later, or
  queue a request to the assistant. The assistant treats that request as the owner's own: the next pass sends it to
  the AI with the conversation, and the answer can replace the draft the owner later copies to the client.
- **Reading and changing everything.** A website can point one of its own addresses at the owner's computer ("DNS
  rebinding"), after which the browser treats the page as part of that site. The site can then read everything the
  page shows (conversations, summaries, drafts) and use every button.
- **Borrowing the owner's clicks.** A website can show the real page inside its own, hidden under something else, so
  that the owner's clicks land on "Feito" or "Ignorar".

Browsers have started to ask before a website reaches the owner's own computer, but not all of them do, and the owner
may click "allow" without knowing what it means. The owner's conversations include clients' personal data, and the
owner is responsible for protecting it (`docs/decisions.md`, Privacy). The first-run PRD sets the same rule for the new
setup screens (AC-SETUP-08 in `docs/prds/first-run-without-terminal/`); this change applies it to the page that exists
today.

## Acceptance Criteria

"The page itself" means the page as the browser opens it at one of its own addresses (AC-ORIGIN-03). Any other website
is refused, including one served by another program on the owner's own computer.

### Only the Page Itself Can Change Anything

The page's buttons and its "Pedir ao assistente" box keep working. The same requests coming from any other website are
refused and change nothing.

- [x] **AC-ORIGIN-01 — Other websites cannot act through the page.** A request to mark a conversation, defer it, set
  a wait, undo a mark, or queue a request to the assistant is carried out only when it comes from the page itself. The
  same request from any other website, including one that has pointed its own address at the owner's computer,
  changes nothing and queues nothing.
- [x] **AC-ORIGIN-04 — Other websites cannot show the page inside their own.** The page refuses to appear inside
  another website, so no site can place the page's buttons under the owner's clicks.

### Only the Page Itself Can Read What It Shows

The conversations, summaries and drafts the page shows stay readable only by the page.

- [x] **AC-ORIGIN-02 — Other websites cannot read the page.** No other website can read the page or anything it shows,
  including a website that has pointed one of its own addresses at the owner's computer.

### Nothing Changes for the Owner

The owner opens and uses the page exactly as today.

- [ ] **AC-ORIGIN-03 — Every way of opening the page still works.** These all open a page that works fully: the
  desktop shortcut, the link at the end of the installer, the link on a Fizzy card, and typing
  `http://127.0.0.1:8422` or `http://localhost:8422` in the browser. When whoever installs runs the page on another
  port, typing either address with that port works the same way.

## Out of Scope

- **Other devices on the network.** They already cannot reach the page; this change keeps that as it is.
- **Programs on the owner's computer that are not a browser.** They can already read the assistant's files directly;
  protecting against them is the computer's own security, not the page's.
- **Hermes.** Hermes reaches assistantOS through its own connection, not through the page, and is not affected.
- **The setup screens.** They do not exist yet; AC-SETUP-08 of the first-run PRD covers them.
