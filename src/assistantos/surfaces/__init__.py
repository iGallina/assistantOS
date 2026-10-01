"""Where the owner sees and acts on items, besides the local page. Enabled by local/config/<name>.json."""
from pathlib import Path

from ..config import load_file
from .fizzy import Fizzy

SURFACES = {s.name: s for s in (Fizzy(),)}


def load_surfaces(config_dir: Path) -> list[tuple[object, object]]:
    return [(s, load_file(config_dir / f"{name}.json", s.Config))
            for name, s in SURFACES.items() if (config_dir / f"{name}.json").exists()]
