from ..models import Backend as BackendCfg
from ..store import Store
from .base import Backend, BackendError, QuotaExceeded
from .claude_cli import ClaudeCLI
from .codex_cli import CodexCLI

BACKENDS = {"claude": ClaudeCLI, "codex": CodexCLI}

__all__ = ["Backend", "BackendError", "QuotaExceeded", "make_backend"]


def make_backend(cfg: BackendCfg, store: Store, **kw) -> Backend:
    if cfg.kind not in BACKENDS:
        raise BackendError(f"{cfg.kind}: not supported yet")
    return BACKENDS[cfg.kind](cfg, store, **kw)
