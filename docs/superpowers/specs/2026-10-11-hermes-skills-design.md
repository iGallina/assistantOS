# assistantOS skills as a Hermes distribution — design (2026-10-11)

**Decisions (Ian, 2026-10-10):** Hermes Agent + Hermes Desktop replace Paseo. Engine split (a): the sweep stays in our
Python and is exposed to Hermes over MCP (`aos mcp`); Hermes owns the model/subscription, chat, phone gateway, skills
and distribution. The AIS-OS skills ship with the product, designed for the product, with AIS-OS as reference only.

## Where things live

- **`hermes/` is the Hermes distribution.** Measured on a runner: `hermes profile install` copies the *whole* source
  folder into the profile (not only distribution-owned files, despite the docs), so the repo root would put `src/`,
  tests and docs into every owner's profile. The installer installs from the local clone:
  `hermes profile install <core>/hermes -y`; `hermes profile update` re-reads that folder after `aos update`.
- **Owner data lives in the profile's `local/`** (Hermes never touches it on update, the same convention as our
  `local/`): `local/context/` (about-me, about-business, priorities, voice, connections, index), `local/brainstorms/`,
  `local/audits/`, `local/decisions.md`. `USER.md` (1,375-char limit) gets only a compact owner summary + pointers.
- **Skills:** `skills/<name>/SKILL.md`, Hermes format (`name`, `description`, `version`, `license`, optional
  `platforms`, `metadata.hermes`). Instructions in English; the agent talks to the owner in the owner's language
  (pt-BR by default, set in `SOUL.md`). Owner-facing templates are in pt-BR.

## Branding

Kit-derived files keep the MIT notice (`NOTICE`). The "Three Ms of AI" name and branding are not used: no "3Ms",
"Default Shift", "Bike Method", "Four Cs" or attribution blocks inside skills. The methods are written in our own
words. `tests/test_distribution.py` fails on those terms.

## Port map

| AIS-OS | Product skill | Batch | Notes |
|---|---|---|---|
| onboard | `onboard` | 1 | 7-question intake → `local/context/`; summary to USER.md |
| grill-me | `grill-me` | 1 | captures in `local/brainstorms/` |
| link | `link` | 1 | routes go into `local/context/index.md` (SOUL.md points there) |
| level-up | `level-up` | 1 | one improvement per run; unbranded method |
| audit | `audit` | 2 | four dimensions (context, connections, capabilities, routine); Hermes checks replace AGENTS/CLAUDE parity |
| my-tasks | `decidir` | 2 | "what needs me now" from `aos mcp` |
| daily | `preparar-reuniao` | 2 | meeting prep sheet pattern |
| pa, setepetalas | `agente-de-contato` | 3 | allowlisted drafts for one contact via the Hermes gateway; owner approves every reply |
| 3d-brain | `3d-brain` | 3 | bundled local app, paths adapted |
| health | `saude` | 3 | private log pattern; data source chosen by the owner |

## Verification

- `uv run pytest`: every skill's frontmatter is valid (`name` = folder, description present), no banned terms,
  `distribution.yaml` names the distribution.
- CI (later): install Hermes on a runner, `hermes profile install ./`, list skills, run one skill dry.
