# Spike: LangGraph on the user's subscription (no API key) — YES for Claude and Codex

**Question:** can a LangGraph graph run its model calls through the subscription CLIs instead of pay-per-token API keys, with Pydantic outputs?
**Evidence (2026-09-29, this Mac):** `2026-09-29-langgraph-on-subscription.py` (throwaway): a LangChain `BaseChatModel` whose `_generate` shells out to `claude -p --model haiku --tools "" --strict-mcp-config --output-format json --json-schema <Brief.model_json_schema()>`, called from a LangGraph node, run with `ANTHROPIC_API_KEY` unset → a validated `Brief` in 9.9 s.

| Backend | Structured output | Status |
|---|---|---|
| Claude Code `claude -p` | `--json-schema` → `structured_output` | **proven** |
| Codex `codex exec` | `--output-schema <file>` + `-o <file>`; schema must be strict (`extra="forbid"`) | **proven** — 28.4 s, ChatGPT login, `OPENAI_API_KEY` unset (`…-codex.py`) |
| Gemini CLI `gemini -p` | JSON output mode, schema flag unknown | not installed here — unverified. (Antigravity is an IDE; the subscription CLI is Gemini CLI.) |

**Constraints this sets**
- Call the **official CLI** in headless mode, never reuse its login token in another client — reusing the token is the pattern providers have blocked in third-party tools.
- ~10 s per call (process start + auth): fine for the background loop, wrong for per-message classification → Jev keeps classification.
- Subscription usage limits (5-hour / weekly windows) replace per-token cost: the cost skill reports quota use per backend, not dollars.
- Wrapper fields must not reuse LangChain attribute names: `schema` warned, `output_schema` was silently replaced by a class and crashed. Use `response_schema`.
- Codex is ~3x slower per call than `claude -p` (28 s vs 10 s): budget the loop per backend.
