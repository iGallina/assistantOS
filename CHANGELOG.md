# Changelog

Versões marcadas com tags `vX.Y.Z`. `aos update` instala a mais nova; mudanças no banco rodam sozinhas (migrações
numeradas) e uma versão que falha no teste é desfeita.

## v0.1.0 — 2026-10-04

Primeira versão.

- **Passada a cada 5 minutos** (Agendador de Tarefas no Windows, launchd no macOS): sincroniza o WhatsApp
  (`wacli sync --once`), lê só os chats que você listou, calcula o status de cada loop e prepara um brief de
  decisão com o modelo da sua assinatura (Claude ou Codex — sem chave de API). Limites por passada e por dia.
- **Jev** (opcional, `TYPESAFE_API_KEY`): marca conversa social e faz a triagem dos pedidos. Só rótulo: nunca
  esconde nada.
- **Página local** (`aos page`): decidir agora, em aberto, aguardando, depois, resolvidos; marcar, adiar,
  aguardar alguém; pedir ao assistente (responder, novo rascunho, ou "precisa de sessão").
- **Fizzy**: cada loop aberto vira um cartão no seu quadro, nos dois sentidos.
- **Relatório do dia** (`local/reports/`): problemas das passadas de hoje (ex.: WhatsApp desconectado), o que
  chegou, o que decidir, pedidos pendentes, prompts sugeridos e o uso de IA em segundo plano.
- **`aos bug-report`**: relatório de erro mascarado no seu computador (telefones, CPF/CNPJ, e-mails, chaves,
  contatos…); você revisa e envia pelo GitHub.
- **`aos update`**, **`aos export`**, **`aos uninstall`**; erros de cada passada em `local/state/errors.log`.
- Nada é enviado em seu nome: o assistente rascunha, você aperta enviar.
