"""Integrations. A plugin is enabled by its own local/config/<name>.json."""
from pathlib import Path

from ..config import load_file
from .whatsapp import WhatsApp

PLUGINS = {p.name: p for p in (WhatsApp(),)}


def load_plugins(config_dir: Path) -> list[tuple[object, object]]:
    return [(p, load_file(config_dir / f"{name}.json", p.Config))
            for name, p in PLUGINS.items() if (config_dir / f"{name}.json").exists()]
