# assistantOS build step 3b — the local page (`aos page`)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Checkbox steps.

**Goal:** the owner opens `http://127.0.0.1:8422`, sees what needs a decision first (with the brief), and marks items
done / later / waiting / ignored — the same store `aos run` writes. Nothing is ever sent: drafts are copied and the
WhatsApp chat is opened for the owner to send.

**Architecture:** `page/state.py` builds the page data from the store (pure, tested); `page/server.py` is a stdlib
`ThreadingHTTPServer` bound to 127.0.0.1 with one SQLite connection per request; `page/page.html` is one file
(tokens, light/dark, strings from `locales/*.json` injected at serve time). Ported in spirit from AIS-OS
`scripts/em-aberto.py` + `em-aberto.local.html`, not line by line (that page carries Ian-only features).

**Spec:** `docs/superpowers/specs/2026-09-29-assistantos-core-design.md` (CLI `page`, surfaces).

## Global Constraints

- Port 8422 by default (8421 is the AIS-OS page on Ian's Mac); `--port` overrides. Bound to 127.0.0.1 only.
- Sections, in order: **decidir** (reaberto, vencido, and aberto with a current brief) · **abertos** · **aguardando** ·
  **depois** · **resolvidos** (feito, ignorado — collapsed). Inside a section: newest event first.
- A mark is a `Mark` (validated: aguardando needs who + until; computed statuses refused → HTTP 400). Unknown item → 404.
- A Jev "social" label shows as a tag on the item; it never hides it.
- Every visible string comes from the locale files; the page has no hard-coded Portuguese.

## Tasks

1. **`page/state.py`** — `build_state(store, today) -> {"items": [...], "counts": {section: n}}`; item = id, title,
   source, status, section, last event (at, direction, text), brief (or null), `brief_current`, `social`, mark
   (who, until), `wa` (digits, WhatsApp items only). Tests: section per status, `brief_current` false after a newer
   event, social flag only for the current inbound, ordering.
2. **`page/server.py` + `aos page`** — `GET /` (html + strings), `GET /api/state`, `GET /api/events?id=`,
   `POST /api/mark {item_id, status, who?, until?}`. Tests over real HTTP on an ephemeral port: state JSON, mark
   feito → item in resolvidos, aguardando without who → 400, unknown item → 404, `/` contains a pt-BR string.
3. **`page/page.html`** — render sections, expand an item to its brief (decisão, opções, próximo passo, rascunho with
   *Copiar*), *Contexto* (events), *Abrir no WhatsApp* (`whatsapp://send?phone=<digits>`), buttons Feito · Amanhã ·
   Aguardando (who + date, default +3 working days) · Ignorar · Desfazer. Checked in a real browser on the live-check
   data (screenshot), light and dark.
4. CI green on Windows + macOS → merge.
