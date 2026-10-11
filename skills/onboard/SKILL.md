---
name: onboard
description: Use on the owner's first day, or when they say "vamos começar", "me configura", "onboard", "set me up", or the profile has no local/context/ yet. Runs the 7-question intake and writes the owner's context files in one pass. Idempotent — re-run after editing local/context/intake.md.
version: 1.0.0
author: assistantOS
license: MIT
metadata:
  hermes:
    tags: [assistantOS, onboarding, context]
    related_skills: [grill-me, link, level-up]
---

# Onboard — the first meeting

One combined flow: read or fill `local/context/intake.md` (seven questions), then write the owner's context files at
the end. Everything lives in the profile's `local/` folder, which Hermes never overwrites on update.

## When to use

- First day, or `local/context/` is missing.
- The owner edited `local/context/intake.md` and wants the context refreshed.
- Not for adding a connection or a tool later: that is `/level-up`.

## Procedure

### 1. Read the intake

Open `local/context/intake.md`. If it does not exist, create it from [the template](assets/intake.md). Check which of
Q1–Q7 still hold the placeholder `[Sua resposta aqui]`.

- All answered → go to step 3.
- Some answered → ask: "Vejo que Q1, Q3 e Q4 já estão respondidas. Quer responder o resto agora ou eu monto o contexto
  com o que já tem?" The owner decides.
- None answered → step 2, as a conversation.

### 2. The interview (seven questions, hard cap)

One question at a time, in the owner's language. Write each answer into `local/context/intake.md` right after it is
given, so nothing is lost if the conversation stops.

1. **Quem é você, o que você vende e para quem?** Identity, offer, ideal customer. A paragraph each is enough.
2. **Cole uma ou duas coisas que você escreveu recentemente, sem editar.** A WhatsApp message to a client, an e-mail,
   a post. *The one hard rule:* samples must be pasted, never typed now. If the owner starts typing fresh text, stop
   them: "Cole o texto original, do jeito que foi enviado. Se você escrever agora, conversando comigo, a amostra já sai
   no meu tom e não no seu."
3. **Quais são as duas ou três prioridades dos próximos 90 dias?** If the answer is vague ("crescer"), ask for a number,
   a date or a deliverable.
4. **Onde o dinheiro entra e onde você acompanha isso?** Bank, card machine, spreadsheet, system — several are fine.
5. **Onde você conversa com clientes, equipe e fornecedores no dia a dia?** WhatsApp (which number), e-mail, Instagram,
   phone.
6. **Onde ficam as anotações de reunião e os documentos importantes?** Google Drive, a notebook, a desktop folder.
7. **Qual tarefa come a sua semana, e onde você controla o que precisa fazer?** The biggest recurring drudgery, plus
   where tasks live today (paper, a notes app, a system).

### 3. Write the context (one batch)

When the intake is complete, write all files in one go. If any already exists, copy the old versions to
`local/context/archive/intake-{YYYY-MM-DD-HHMM}/` first.

| File | From | Content |
|---|---|---|
| `local/context/about-me.md` | Q1, Q7 | who the owner is; the task that eats the week |
| `local/context/about-business.md` | Q1, Q4 | offer, customer, how money comes in |
| `local/context/priorities.md` | Q3 | numbered list, one line each |
| `local/context/voice.md` | Q2 | the samples verbatim, under: "Escreva neste tom ao rascunhar. Nunca use este tom em algo público sem mostrar antes." |
| `local/context/connections.md` | Q4–Q7 | one row per area (money, customers, calendar, team, tasks, meetings, documents): where it lives, `ainda não conectado` |
| `local/context/index.md` | all | one line per file above: when to read it → path |

Then save a short owner profile with the memory tool (`user` target), under 600 characters: name, business in one
line, the top priority, one line on tone, and "Contexto completo em local/context/". Do not copy the samples or the
full intake into memory: it has a 1,375-character limit.

### 4. Close (three lines)

```
✓ Pronto. Agora eu sei quem você é, o que você vende, o que importa neste trimestre e como você escreve.
Hoje: me pergunte "no que eu deveria focar esta semana?"
Amanhã: escolha as conversas do WhatsApp que eu vou acompanhar.
```

When the owner asks "no que eu deveria focar esta semana?", answer only from the new context files: three bullets in
the owner's tone, each tied to a 90-day priority, ending with: "Se eu tivesse que escolher uma coisa para segunda,
seria [X], porque [motivo]. Quer que eu prepare o primeiro passo? E onde eu poderia fazer parte desse trabalho por
você?"

## Rules

1. Seven questions, never an eighth.
2. The voice samples are pasted, never typed in the conversation.
3. One batch of writes at the end; the owner iterates by editing the intake and running `/onboard` again.
4. Idempotent: a re-run backs up and refreshes only what changed.
5. No passwords, API keys or logins on the first day.
6. Only `local/context/` and the memory tool are written. Nothing is sent to anyone.

## Verification

- Fresh profile: answer the seven questions → the six files exist and `index.md` lists them; the memory tool shows the
  owner profile. Then "no que eu deveria focar esta semana?" cites Q1, Q3 and Q7 specifically. A generic answer fails.
- Re-run with one Q3 priority changed → only `priorities.md` and `index.md` change, and a backup appears in
  `local/context/archive/`.
- Type a sample instead of pasting → the skill refuses and asks for the original text.
