"""Load local/config/*.json into Config; report every problem by file and field."""
import json
from pathlib import Path

from typing import TypeVar

from pydantic import BaseModel, ValidationError

from .models import Backend, Config, Contacts, Owner, Tags

EXAMPLES = Path(__file__).parent / "examples"
M = TypeVar("M", bound=BaseModel)
FILES = {"owner": Owner, "backend": Backend, "contacts": Contacts, "tags": Tags}


class ConfigError(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


def load_file(f: Path, model: type[M]) -> M:
    """One config file → its model; keys starting with "_" are documentation. Problems name the file and field."""
    if not f.exists():
        raise ConfigError([f"{f.name}: missing"])
    try:
        raw = json.loads(f.read_text(encoding="utf-8"))
        return model.model_validate({k: v for k, v in raw.items() if not k.startswith("_")})
    except json.JSONDecodeError as e:
        raise ConfigError([f"{f.name}: invalid JSON (line {e.lineno})"]) from e
    except ValidationError as e:
        raise ConfigError([f"{f.name}: {'.'.join(map(str, x['loc'])) or '(root)'}: {x['msg']}" for x in e.errors()]) from e


def load_config(d: Path) -> Config:
    parts, problems = {}, []
    for name, model in FILES.items():
        try:
            parts[name] = load_file(d / f"{name}.json", model)
        except ConfigError as e:
            problems += e.problems
    if problems:
        raise ConfigError(problems)
    return Config(**parts)
