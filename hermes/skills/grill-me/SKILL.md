---
name: grill-me
description: Interview the owner relentlessly about a plan, idea, decision or topic, saving every answer to a file so nothing is lost. Use when the owner wants to stress-test a plan, think a decision through, brainstorm, get what is in their head into writing, or says "grill me", "me entrevista", "me sabatina".
version: 1.0.0
author: assistantOS
license: MIT
metadata:
  hermes:
    tags: [assistantOS, interview, planning, context]
    related_skills: [onboard, link, level-up]
---

# Grill me

Interview the owner about every branch of the topic until you both understand it the same way. The real output is a
**durable, organised file** with what was said, so nothing is lost when the conversation gets long.

## The capture file is the whole point

Long interviews fill the context. Answers held only in your head get mixed up or dropped. So you **save to disk after
every single answer**. The file, not the conversation, is the source of truth. Never make the owner ask you to save.

## Before the first question

1. Read `local/context/index.md` and only the context pages relevant to the topic. Reuse what is already known; ask
   about gaps, changes, decisions and trade-offs.
2. Create the capture at `local/brainstorms/{YYYY-MM-DD}-{tema}.md` (create the folder if needed). Get today's date from
   the clock (`date +%F`, or `Get-Date -Format yyyy-MM-dd` on Windows).
   - Never overwrite a capture. Same date and topic → add a time or suffix. Resume an earlier capture only when the
     owner asks for it or clearly refers to it; read it first and continue its numbering.
   - No topic yet → create `{date}-sem-tema.md`, ask what to explore, and record the topic in that same file.
3. Write the header right away (title, date, goal, empty "Pendências" section), tell the owner where it is saved in one
   line, then ask Q1.

## After every answer (non-negotiable)

Before the next question:

- Append an entry: the question, the facts and decisions in the owner's words where wording matters, and any pending
  item (what they could not answer, and who can).
- If a later answer changes an earlier one, keep the original entry, mark it superseded, and link to the correction.
- Read the saved entry back. If the save failed, say so and keep the answer visible in the chat; never claim it was
  saved and never keep collecting answers without a working save.

One answer per write. Never batch.

## How to interview

- **One question at a time.** For decisions, offer a suggested answer from context and label it as a suggestion. For
  facts about the owner or the business, ask neutrally; never save your guess as their answer.
- Keep confirmed facts, tentative ideas, your suggestions and open questions clearly apart in the file.
- Settle upstream decisions before the ones that depend on them.
- If a file or document can answer it, read it instead of asking. If the owner hands you a document, bring up only
  what is new.
- When the owner cannot answer, record it as pending with an owner and move on.
- Stop immediately when the owner says stop. Near the end, ask: "Tem algo que a gente não tocou?"

## Capture file layout

```
# {Tema}: entrevista
Data: {data} · Objetivo: {uma linha}
Status: em andamento / pausada / concluída
Contexto usado: {páginas de local/context/ lidas}

## Resumo e decisões
(síntese corrente, atualizada a cada resposta)

## Perguntas e respostas
### P1 - {assunto}
- Pergunta: {pergunta}
- Resposta: {fatos e decisões confirmados, nas palavras do dono quando importa}
- Sugestões / ideias: {não confirmadas, marcadas como tal}
- Pendências: {item -> quem responde}

## Pendências
- {item} -> {quem}
```

## At the end or on a pause

- Read the capture for contradictions and gaps; mark conflicts, never choose a business fact for the owner. Update the
  status and where to resume.
- When the session was about the owner's context, merge only **confirmed** durable facts into the right page in
  `local/context/`, with a dated link back to the capture, and record meaningful decisions in `local/decisions.md`.
  Ideas, suggestions and unknowns stay in the capture until confirmed.
- For a plan or idea session, the capture is the output. Suggest `/link` to make a result easy to find, or
  `/level-up` to turn one opportunity into an improvement. Do not run either on your own.
- Give a short recap: where the capture is, which context pages changed, what is pending, the next step.

## Boundaries

Only the capture, the owner's context pages and the decisions log are written. No messages, no publishing, no changes
outside the profile. Never ask for or save passwords or keys.

## Verification

Check a fresh session, a same-day name collision, resuming, a correcting answer, a stop request and a failed write.
Only confirmed facts reach `local/context/`, and earlier answers stay traceable.
