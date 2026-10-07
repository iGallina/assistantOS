# assistantOS

Seu assistente pessoal: acompanha seus loops abertos no WhatsApp (e em breve e-mail e Google), prepara o que precisa
de decisão com o modelo da **sua assinatura** (Claude ou ChatGPT/Codex — sem chave de API) e mostra tudo numa página
local e no Fizzy, no celular. Nada é enviado em seu nome: você sempre aperta o enviar.

## Instalar

Clone o **seu repositório privado** do assistantOS e, dentro da pasta:

- **Windows** (PowerShell): `powershell -ExecutionPolicy Bypass -File install\install.ps1`
- **macOS** (Terminal): `sh install/install.sh`

O script instala o `uv` e o Claude Code se faltarem, as ferramentas (wacli, fizzy, bws — versões fixas, conferidas
pelo SHA-256 publicado por cada projeto), cria `local/config/` e agenda uma passada a cada 5 minutos. Pode rodar de
novo quando quiser: ele não sobrescreve nada seu.

Depois, só você pode fazer:

1. `claude` → faça login com a sua assinatura (ou `codex login`, se escolher Codex em `local/config/backend.json`).
2. `wacli auth` → escaneie o QR com o WhatsApp do celular; liste os chats que importam em `local/config/whatsapp.json`.
3. Fizzy (opcional): ponha o ID do quadro em `local/config/fizzy.json` e o token em `FIZZY_TOKEN`.
4. `uv run aos doctor` → tudo com ✓.

A página: `uv run aos page` → http://127.0.0.1:8422

## Comandos

`aos init` · `aos doctor` · `aos run` (uma passada; reescreve o relatório do dia em `local/reports/`) · `aos page` · `aos report` (abre o relatório do dia) · `aos bug-report "o que aconteceu"` (relatório de erro mascarado no seu computador; você revisa e envia) · `aos setup` · `aos schedule install|remove|status` · `aos update` (instala a versão mais nova; se falhar, volta sozinho) · `aos export` (um .zip com tudo que é seu) · `aos uninstall` (faz a cópia, tira o agendamento; seus arquivos ficam)

Novidades de cada versão: `CHANGELOG.md`.
