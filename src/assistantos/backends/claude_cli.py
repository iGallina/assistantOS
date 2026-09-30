import json

from .base import Backend, BackendError


class ClaudeCLI(Backend):
    kind = "claude"
    default_model = "haiku"

    def _call(self, prompt: str, schema: dict) -> str:
        args = ["-p", "--model", self.model, "--tools", "", "--strict-mcp-config",
                "--output-format", "json", "--json-schema", json.dumps(schema)]
        try:
            out = json.loads(self._run(args, prompt).stdout)
        except json.JSONDecodeError as e:
            raise BackendError("claude: output is not JSON") from e
        if out.get("is_error"):
            raise self._fail(str(out.get("result", "")))
        if "structured_output" not in out:
            raise BackendError(f"claude: no structured_output ({out.get('subtype')})")
        return json.dumps(out["structured_output"])
