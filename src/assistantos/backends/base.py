"""The one contract every model backend keeps: schema out, validated Pydantic model back, one runs row per call."""
import re
import shutil
import subprocess
import time
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ..models import Backend as BackendCfg
from ..store import Store

M = TypeVar("M", bound=BaseModel)
# ponytail: keyword match on the CLI's error text; tighten once real limit messages are in the runs log
LIMIT = re.compile(r"(?i)usage limit|rate limit|limit reached|quota")


class BackendError(Exception):
    pass


class QuotaExceeded(BackendError):
    pass


class Backend:
    kind = ""
    default_model: str | None = None  # used when the config leaves model empty

    def __init__(self, cfg: BackendCfg, store: Store, cmd: list[str] | None = None, timeout: float = 600):
        self.cfg, self.store, self.cmd, self.timeout = cfg, store, cmd, timeout
        self.model = cfg.model or self.default_model

    def ask(self, prompt: str, output: type[M], job: str) -> M:
        t0, ok = time.monotonic(), False
        try:
            raw = self._call(prompt, output.model_json_schema())
            try:
                result = output.model_validate_json(raw)
            except ValidationError as e:
                raise BackendError(f"{self.kind}: answer does not match {output.__name__} ({e.error_count()} errors)") from e
            ok = True
            return result
        finally:
            self.store.log_run(job, self.kind, self.model, time.monotonic() - t0, ok)

    def _call(self, prompt: str, schema: dict) -> str:
        raise NotImplementedError

    def _fail(self, msg: str) -> BackendError:
        return (QuotaExceeded if LIMIT.search(msg) else BackendError)(f"{self.kind}: {msg}")

    def _run(self, args: list[str], prompt: str) -> subprocess.CompletedProcess:
        exe = self.cmd or [shutil.which(self.kind) or ""]
        if not exe[0]:
            raise BackendError(f"{self.kind}: not installed")
        try:
            p = subprocess.run(exe + args, input=prompt, capture_output=True, text=True,
                               encoding="utf-8", timeout=self.timeout)
        except subprocess.TimeoutExpired as e:
            raise BackendError(f"{self.kind}: no answer in {self.timeout:.0f}s") from e
        if p.returncode != 0:
            raise self._fail((p.stderr or p.stdout).strip()[-500:])
        return p
