"""Load local/config/*.json into Config; report every problem by file and field."""
import json
from pathlib import Path

from pydantic import ValidationError

from .models import Backend, Config, Contacts, Owner, Tags

EXAMPLES = Path(__file__).parent / "examples"
FILES = {"owner": Owner, "backend": Backend, "contacts": Contacts, "tags": Tags}


class ConfigError(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


def load_config(d: Path) -> Config:
    parts, problems = {}, []
    for name, model in FILES.items():
        f = d / f"{name}.json"
        if not f.exists():
            problems.append(f"{f.name}: missing")
            continue
        try:
            raw = json.loads(f.read_text(encoding="utf-8"))
            parts[name] = model.model_validate({k: v for k, v in raw.items() if not k.startswith("_")})
        except json.JSONDecodeError as e:
            problems.append(f"{f.name}: invalid JSON (line {e.lineno})")
        except ValidationError as e:
            problems += [f"{f.name}: {'.'.join(map(str, x['loc'])) or '(root)'}: {x['msg']}" for x in e.errors()]
    if problems:
        raise ConfigError(problems)
    return Config(**parts)
