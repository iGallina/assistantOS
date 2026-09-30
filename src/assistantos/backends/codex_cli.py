import json
import tempfile
from pathlib import Path

from .base import Backend, BackendError


class CodexCLI(Backend):
    kind = "codex"

    def _call(self, prompt: str, schema: dict) -> str:
        with tempfile.TemporaryDirectory() as d:
            schema_file, out_file = Path(d) / "schema.json", Path(d) / "out.txt"
            schema_file.write_text(json.dumps(schema), encoding="utf-8")
            args = ["exec", "--skip-git-repo-check", "--ephemeral", "-s", "read-only", "-C", d,
                    "-o", str(out_file), "--output-schema", str(schema_file)]
            if self.model:
                args += ["-m", self.model]
            self._run(args + ["-"], prompt)
            if not out_file.exists():
                raise BackendError("codex: no answer written")
            return out_file.read_text(encoding="utf-8")
