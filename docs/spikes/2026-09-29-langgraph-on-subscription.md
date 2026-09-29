# Spike: LangGraph on the user's subscription (no API key) — YES for Claude

**Question:** can a LangGraph graph run its model calls through the subscription CLIs instead of pay-per-token API keys, with Pydantic outputs?
**Evidence (2026-09-29, this Mac):** `2026-09-29-langgraph-on-subscription.py` (throwaway): a LangChain `BaseChatModel` whose `_generate` shells out to `claude -p --model haiku --tools "" --strict-mcp-config --output-format json --json-schema <Brief.model_json_schema()>`, called from a LangGraph node, run with `ANTHROPIC_API_KEY` unset → a validated `Brief` in 9.9 s.

| Backend | Structured output | Status |
|---|---|---|
| Claude Code `claude -p` | `--json-schema` → `structured_output` | **proven** |
| Codex `codex exec` | `--output-schema <file>` (in `--help`, v0.157.1) | flag exists, not run |
| Gemini CLI `gemini -p` | JSON output mode, schema flag unknown | not installed here — unverified. (Antigravity is an IDE; the subscription CLI is Gemini CLI.) |

**Constraints this sets**
- Call the **official CLI** in headless mode, never reuse its login token in another client — reusing the token is the pattern providers have blocked in third-party tools.
- ~10 s per call (process start + auth): fine for the background loop, wrong for per-message classification → Jev keeps classification.
- Subscription usage limits (5-hour / weekly windows) replace per-token cost: the cost skill reports quota use per backend, not dollars.
- Rename the wrapper's `schema` field (it shadows a `BaseChatModel` attribute — warning in the run).
