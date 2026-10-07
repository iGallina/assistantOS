# assistantOS

**O seu assistente para não deixar nenhuma conversa importante cair.**

Você combina um prazo no WhatsApp, um cliente pede um orçamento, um fornecedor fica de responder… e, no meio do dia,
alguma coisa se perde. O assistantOS acompanha as conversas que você escolher e, a cada 5 minutos, mostra numa
única página o que precisa da sua decisão, com um resumo e uma resposta já rascunhada no seu tom. Você lê, ajusta se
quiser e envia.

## O que ele faz por você

- **Lê só as conversas que você escolher** no WhatsApp: clientes, fornecedores, equipe. O resto ele não lê.
- **Passa pelas suas conversas a cada 5 minutos.** Cada uma dessas rodadas se chama **passada**.
- **Prepara um resumo de decisão** para cada conversa que pede você: o que mudou, qual decisão é sua, 2 ou 3 opções,
  o próximo passo e um **rascunho de resposta**.
- **Lembra do que você deixou para depois** e do que você está esperando de alguém. Se a pessoa responde ou o prazo
  vence, a conversa volta para a sua frente.
- **Avisa quando um assunto encerrado volta**: você marcou como feito, o cliente escreveu de novo, e a conversa reaparece.
- **Faz um relatório do dia**: o que chegou, o que falta decidir e sugestões do que pedir em seguida.
- **Mostra tudo no celular**, se você usar o Fizzy (um quadro de cartões no celular).

## O que ele nunca faz

- **Nunca envia mensagem em seu nome.** Ele rascunha; quem aperta "enviar" é sempre você.
- **Nunca esconde uma conversa.** Ele pode marcar algo como "provavelmente conversa social", mas a conversa continua
  na sua lista.
- **Não guarda seus dados em nenhum servidor nosso.** Tudo fica no seu computador (veja "Seus dados", abaixo).

## Um dia com o assistantOS

1. **De manhã**, abra a página (veja "Abrir a página") ou o relatório do dia. Comece por **Decidir agora**.
2. Em cada conversa, leia o resumo, clique em **Copiar rascunho**, depois em **Abrir no WhatsApp**, cole, ajuste e envie.
3. Marque o que fez: **Feito**, **Amanhã**, **Aguardando…** (quem e até quando) ou **Ignorar**.
4. **Durante o dia**, o assistente continua olhando a cada 5 minutos. O que chegar de novo aparece na página e no Fizzy.
5. Precisa de ajuda com uma resposta? Escreva em **Pedir ao assistente**, por exemplo "responde que entrego sexta",
   e em até 5 minutos aparece um rascunho novo.

## Do que você precisa

| Item | Detalhe |
|---|---|
| **Computador** | Windows 10 ou 11 (ou Mac). Ele trabalha enquanto o computador está **ligado e com a sua sessão do Windows aberta**. |
| **Inteligência artificial** | Uma assinatura **Claude** (Pro ou superior) ou **ChatGPT** (Plus ou superior). É ela que escreve os resumos. **Não precisa de chave de API**: não há cobrança por uso além da sua assinatura. |
| **WhatsApp** | O seu celular, para ler um QR code uma única vez (como no WhatsApp Web). |
| **Fizzy** (opcional) | Uma conta no Fizzy, se quiser os cartões no celular. |
| **Tempo** | Uns 40 minutos na instalação, de preferência junto com quem vai instalar para você. |

## Instalação

A primeira instalação é feita **junto com você**: quem instala cuida da parte técnica, e há três momentos em que só
você pode agir. Se algum comando abaixo parecer estranho, é normal: é só copiar e colar.

**Antes de começar**, no Windows, abra o **PowerShell** (menu Iniciar → digite "PowerShell" → Enter).

1. **Instale o Git** (se ainda não tiver):
   ```
   winget install --id Git.Git -e
   ```
   Feche o PowerShell e abra de novo.

2. **Baixe o seu assistantOS** (quem instala passa para você o endereço do **seu** repositório privado):
   ```
   git clone https://github.com/SEU-USUARIO/assistantOS.git
   cd assistantOS
   ```

3. **Rode o instalador.** Ele instala o que falta, cria as suas configurações e agenda o assistente a cada 5 minutos:
   ```
   powershell -ExecutionPolicy Bypass -File install\install.ps1
   ```
   Pode rodar de novo quando quiser: ele nunca apaga nada seu.

4. **Só você: entre na sua assinatura de IA.** Digite `claude`, escolha entrar com a sua conta Claude, conclua no
   navegador e depois digite `/exit`.

5. **Só você: conecte o WhatsApp.**
   ```
   .\local\bin\wacli.exe auth
   ```
   No celular: WhatsApp → **Aparelhos conectados** → **Conectar um aparelho** → leia o QR code que apareceu na tela.

6. **Só você: diga quem você é.** Abra o arquivo e troque `SEU NOME` pelo seu nome:
   ```
   notepad local\config\owner.json
   ```

7. **Escolha as conversas** (próxima seção) e confira se está tudo certo:
   ```
   uv run aos doctor
   ```
   Se tudo aparecer com ✓, está pronto. Se aparecer um ✗, ele diz o que falta.

No Mac é igual, só muda o instalador (`sh install/install.sh`) e o WhatsApp (`local/bin/wacli auth`).

## Escolher as conversas

O assistente só lê as conversas da sua lista. Para achar o código de uma conversa, procure pelo nome:

```
.\local\bin\wacli.exe chats list --query "Maria"
```

Copie o código que aparece (algo como `5561999999999@s.whatsapp.net`, ou terminado em `@g.us` se for um grupo) e
coloque na lista:

```
notepad local\config\whatsapp.json
```

```json
"chats": [
  "5561999999999@s.whatsapp.net",
  "5511988887777@s.whatsapp.net"
]
```

Cada código entre aspas, separados por vírgula. Salve e rode `uv run aos doctor` de novo. Comece com as 5 a 10
conversas que mais pesam no seu dia; dá para aumentar depois.

## Abrir a página

No PowerShell, dentro da pasta `assistantOS`:

```
uv run aos page
```

Abra **http://127.0.0.1:8422** no navegador e deixe o PowerShell aberto enquanto usa a página. A página fica só no
seu computador: ninguém mais acessa.

### As seções

| Seção | O que está ali |
|---|---|
| **Decidir agora** | Conversas com resumo pronto, conversas que voltaram e esperas vencidas. Comece por aqui. |
| **Em aberto** | Conversas abertas ainda sem resumo: a próxima passada prepara. |
| **Aguardando** | O que você está esperando de alguém, com o nome e a data. |
| **Depois** | O que você adiou. Volta sozinho na data. |
| **Resolvidos** | O que você marcou como feito ou ignorado. |

### Os botões

| Botão | O que faz |
|---|---|
| **Copiar rascunho** | Copia a resposta sugerida, para você colar no WhatsApp. |
| **Abrir no WhatsApp** | Abre a conversa no WhatsApp. Você cola, ajusta e envia. |
| **Contexto completo** | Mostra as últimas mensagens da conversa. |
| **Feito** | Resolvido. Se a pessoa escrever de novo, a conversa volta. |
| **Amanhã** | Adia para amanhã. |
| **Aguardando…** | Você está esperando alguém: diga quem e até quando. Se a pessoa responder, ou a data chegar, a conversa volta para **Decidir agora**. |
| **Ignorar** | Tira da frente. Se a pessoa escrever de novo, a conversa volta. |
| **Desfazer** | Desfaz a marcação. |

### Pedir ao assistente

Dentro de cada conversa há um campo **Pedir ao assistente**. Escreva como falaria com um assistente de verdade:

- "responde que entrego sexta"
- "resume o que ela pediu"
- "deixa a resposta mais curta e mais formal"

Em até 5 minutos aparece a resposta ou um **Rascunho novo**, com o botão para copiar.

Alguns pedidos ele não faz sozinho, como anexar um arquivo ou mexer em outro sistema. Nesse caso, a resposta começa
com **"Precisa de sessão"**. O relatório do dia traz um texto pronto para você colar no Claude e terminar o trabalho.

## No celular (Fizzy)

Se você usa o Fizzy, cada conversa aberta vira um cartão no seu quadro, com o resumo. Fechar o cartão no celular é o
mesmo que marcar **Feito**; apagar o cartão é **Ignorar**. Quem instala configura o quadro para você.

## Relatório do dia

Todo dia o assistente monta um relatório em `local\reports\` (um arquivo por dia). Para abrir o de hoje:

```
uv run aos report
```

Ele mostra:

- os problemas do dia, se houver;
- o que decidir e os pedidos pendentes;
- o que chegou hoje;
- **sugestões do que pedir em seguida**, com textos prontos para copiar;
- quantas vezes a inteligência artificial trabalhou para você hoje.

## Quando algo não funciona

1. Abra o relatório do dia (`uv run aos report`). Se algo falhou hoje, ele começa por **Problemas nas passadas de
   hoje**. Depois rode `uv run aos doctor`: ele confere a instalação e diz o que falta.
2. Problemas comuns:
   - **WhatsApp desconectado** (o problema fala em "wacli" ou "not authenticated"): rode
     `.\local\bin\wacli.exe auth` e leia o QR code de novo.
   - **Nada novo aparece**: o computador estava desligado ou em suspensão? O assistente só trabalha com ele ligado e
     com a sua sessão aberta (tela bloqueada não atrapalha).
   - **Limite da assinatura**: se a sua assinatura de IA chegou ao limite do período, os resumos param e voltam
     sozinhos quando o limite renova. As conversas continuam aparecendo, só sem resumo.
3. **Avise quem mantém o assistantOS** com:
   ```
   uv run aos bug-report "o que aconteceu, com as suas palavras"
   ```
   Antes de qualquer coisa sair do seu computador, ele **apaga os dados pessoais** do relatório: telefones, CPF,
   CNPJ, e-mails, nomes dos seus contatos e senhas. Depois mostra o resultado e pergunta se você quer abrir no GitHub.
   Lá você revisa e só envia se quiser.

## Atualizar, guardar uma cópia, parar

| Comando | O que faz |
|---|---|
| `uv run aos update` | Instala a versão mais nova. Se algo der errado, volta sozinho para a versão anterior, sem perder nada. |
| `uv run aos export` | Cria um arquivo `.zip` com tudo que é seu: configurações, histórico e relatórios. |
| `uv run aos uninstall` | Faz a cópia acima e para o assistente. Seus arquivos ficam no computador até você apagar a pasta. |

As novidades de cada versão estão em `CHANGELOG.md`.

## Seus dados

- O assistantOS roda **no seu computador**. Não existe servidor nosso guardando as suas conversas.
- Para escrever os resumos, o texto das **conversas que você escolheu** é enviado à empresa da sua assinatura de IA
  (Anthropic, se for Claude; OpenAI, se for ChatGPT), conforme as regras da sua conta.
- Se você ativar o **Jev** (opcional, um classificador que separa conversa social de pedido), trechos curtos dos
  pedidos vão para a TypeSafe, empresa que oferece esse serviço.
- Cada vez que a inteligência artificial trabalha, fica um registro que você pode ver no relatório do dia.
- Como os dados ficam com você, **a responsabilidade por eles também é sua**, inclusive pela LGPD em relação aos seus
  clientes. Escolha com cuidado as conversas que entram na lista.

---

## Para quem instala

- **Repositório do cliente:** um repositório **privado** na conta GitHub do cliente, criado a partir do principal
  (não um fork: fork de repositório público é público). Depois do clone, aponte o `upstream`:
  `git remote add upstream https://github.com/iGallina/assistantOS.git`. Enquanto o principal for privado, a conta do
  cliente precisa de **acesso de leitura** a ele, senão `aos update` e `aos bug-report` não funcionam.
- **O instalador** (`install\install.ps1` / `install/install.sh`) instala o `uv` e o Claude Code se faltarem, roda
  `uv sync --locked` e `aos setup`: ferramentas com versão fixa e SHA-256 conferido (wacli, fizzy, bws) em
  `local\bin`, configurações em `local\config` (a partir dos `*.example.json`) e a passada agendada (Agendador de
  Tarefas no Windows, launchd no macOS).
- **Codex em vez de Claude:** `"kind": "codex"` em `local\config\backend.json`, instalar o Codex CLI e `codex login`.
- **Fizzy:** o ID do quadro em `local\config\fizzy.json` e o token no ambiente do usuário (Windows:
  `setx FIZZY_TOKEN "..."` e `setx FIZZY_ACCOUNT "..."`; abra um PowerShell novo depois).
- **Jev:** `setx TYPESAFE_API_KEY "..."`. Sem a chave, tudo funciona; só não há a etiqueta de conversa social nem a
  triagem rápida de pedidos.
- **Limites de IA:** `per_pass_cap` e `per_day_cap` em `local\config\backend.json` (padrão 6 resumos por passada e
  60 por dia).
- **Comandos:** `aos init` · `aos doctor` · `aos run` (uma passada agora; reescreve o relatório do dia) · `aos page` ·
  `aos report` · `aos bug-report "..."` · `aos setup` · `aos schedule install|remove|status` · `aos update` ·
  `aos export` · `aos uninstall`. Sempre com `uv run` na frente, dentro da pasta.
- **Erros das passadas:** `local\state\errors.log`.
