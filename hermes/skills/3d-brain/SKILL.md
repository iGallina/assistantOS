---
name: 3d-brain
description: Use when the owner asks to see their assistant's knowledge as a 3D brain, visualize what the assistant knows, turn their notes into an interactive globe, or says "cérebro 3D", "3D brain", /3d-brain. Builds a local, named, interactive 3D globe from the profile's real files.
version: 1.0.0
author: assistantOS
license: MIT
metadata:
  hermes:
    tags: [assistantOS, visualization, knowledge]
    related_skills: [onboard, link]
---

# 3D Brain

Turn the owner's actual files in this Hermes profile into a personalized, local 3D knowledge globe. Use the bundled
working application, not a new interpretation of its appearance. Preserve its spherical composition, coloured
categories, central orb, restrained connection particles, Cinema mode and interactive growth replay. No external
services, keys, paid assets or deployment.

## 1. Find the profile and the package

The root is this Hermes profile folder (`$HERMES_HOME`). Owner data lives in `local/` (context, interviews, meetings,
contact agents, audits); Hermes keeps its own `memories/` and `skills/`. Read `local/context/index.md` for any custom
folders the owner routed. Never scan outside the profile unless the owner names a folder. All package paths below are
relative to this skill's folder.

Read [the portable spec](references/portable-spec.md) and [the config guide](references/config.md). Check Node.js 22
or newer (Hermes installs Node). If it is missing, say so plainly.

Run the path-only discovery helper:

```text
node <skill-folder>/scripts/discover.mjs --root <profile-folder>
```

It lists candidate folders, not their contents.

## 2. Ask for the name and categories

One question at a time, in the owner's language. Reuse what was already said.

1. **Nome:** "Que nome você quer dar ao seu cérebro 3D?" Use the exact name given. Never choose a name or brand for
   them.
2. **Categorias:** "Quais categorias você quer ver?" Offer the categories actually found, each beside its folder:
   Contexto do negócio, Entrevistas, Reuniões, Agentes de contato, Auditorias, Memória do assistente, Skills. Let the
   owner rename, drop or add. Suggest three to seven; support one to twelve.

The answer also approves those folders. For a custom category with an unknown folder, ask where it is. Show the
name/category/folder mapping, then build without another generic confirmation.

## 3. Scaffold the exact experience

Default output: `local/apps/3d-brain/` inside the profile (Hermes never touches `local/`). If it already exists, inspect its `brain.config.json` and reuse the app. Do not overwrite it blindly. For a requested replacement, archive the existing version first within the same project. If unrelated files occupy the destination, choose a new folder or ask the user.

Create a setup JSON file in `local/apps/.scratch/`, using the schema in [config.md](references/config.md). Do not include actual note bodies. Use relative paths for sources inside the profile and explicit approved paths for outside sources. Give each category a unique ID, label, color, adapter, and one or more real paths.

```text
node <skill-folder>/scripts/scaffold.mjs --root <profile-folder> --config <setup-json> --out local/apps/3d-brain
```

This copies an explicit allowlist of application files and writes the personalized local config. It refuses an existing destination. The renderer is prebuilt: `node serve.mjs` works without npm installation. Do not copy `node_modules`, another user's config, a graph snapshot, screenshots, memory files, or session logs into the app or skill.

In the generated app folder:

```text
node build.mjs
node serve.mjs
```

Start the server through the host's normal background/launch mechanism. On Windows, background launches must be hidden. Default port is 4640. If occupied, pick an available port, update this app's config, and start there. Never stop an unrelated service. Keep the bind address at `127.0.0.1`.

Read the build's real counts and warnings. A missing folder is a configuration issue to resolve, not a reason to invent nodes. Empty categories are allowed and shown honestly. For an entirely empty profile, explain that it needs saved notes; do not inflate it with synthetic content unless the user separately asks for a labeled example.

## 4. Preserve behavior and honest connections

The supplied renderer is the visual contract. Retain:

- A stable spherical layout, distinct source colors, dark background, glowing central orb, and quiet orbital accents.
- Real explicit Markdown links and wikilinks, with exact-title mentions distinguished from explicit relationships. Ambiguous links remain unresolved.
- Search, source solo/toggle, inventory, health flags, note reading, and local file reveal.
- **Play demo:** one central idea, the first real connection, branches springing from parent nodes, accelerating growth, and the full brain after about 29 seconds. Disconnected notes join without invented edges. This is a connectivity replay, not a historical chronology.
- The central orb is visible from the first frame. Dragging, zooming, or clicking the canvas does not stop growth. Camera input takes over from automatic pullback. Replay resets cleanly.
- **Cinema:** clean presentation with the growth counter beside the scene. Pause motion, reduced-motion support, responsive source controls, and no stale labels after replay.

All name-bearing UI comes from `brain.config.json`. Do not regenerate the visuals with an image model or replace the scene with a generic force graph. If code changes are needed, use `npm ci`, edit `src/`, and run `npm run build:js`. Keep dependency license notices with the bundle.

The default adapter reads Markdown/text, which covers the profile's `local/` folders and Hermes's `memories/`. For Google Drive, Notion, raw meeting JSON, databases, PDFs, or another unsupported source, explain the gap and use an explicitly approved local export or build and test an adapter. Do not claim those systems are connected merely because their names appear in a category.

## 5. Verify and deliver

Follow [the acceptance checklist](references/acceptance.md). Check the actual generated app, not just the template:

1. Graph API has the requested name/categories, unique IDs, valid endpoints, and counts matching the source scan.
2. Read at least one real note from each nonempty category. Originals remain unchanged.
3. Confirm the personal name on the page and test search, a source solo filter, restoration, and the inventory.
4. Watch early, middle, and complete growth. Drag and zoom while the count increases. Check the initial orb, clean labels, complete final count, and replay reset. Test Cinema and pause/resume.
5. Inspect desktop and a narrow viewport. Do not manipulate the user's physical mouse; native Pointer Lock is disabled in the supplied app. Browser automation must remain virtual/headless.
6. Check console errors. If browser verification is unavailable, say exactly which checks remain unverified rather than claiming a visual pass.

Add one route to `local/context/index.md`: "cérebro 3D → local/apps/3d-brain/ (abrir com node serve.mjs)". Avoid storing private configs, graph data, or note content in a public repository. Do not deploy or push without the user's authorization.

Finish with the brain name, local link, app folder, actual note/category counts, and the shortest useful instructions: **Play demo**, **Cinema**, drag to orbit, scroll to zoom. Mention source gaps if present. Never promise virality.
