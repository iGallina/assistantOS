# 3D Brain skill (assistantOS)

Builds a named, interactive 3D globe from the owner's files in this Hermes profile (`local/` plus Hermes's `memories/`
and `skills/`). The app is generated in `local/apps/3d-brain/` and runs locally with `node serve.mjs` — no npm install,
no online service.

Package validation: `node scripts/test-package.mjs` (add `--keep --demo --out <scratch-folder>` for a larger fictional
fixture). See [SKILL.md](SKILL.md), [the portable spec](references/portable-spec.md) and
[the config guide](references/config.md). The bundled renderer's third-party licences are in
`assets/template/THIRD-PARTY-NOTICES.txt`.
