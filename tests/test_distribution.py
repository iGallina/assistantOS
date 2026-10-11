"""hermes/ is a Hermes profile distribution: distribution.yaml, SOUL.md, skills/<name>/SKILL.md. A subfolder, because
`hermes profile install` copies the whole source folder into the profile (measured on a runner, 2026-10-11)."""
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parents[1] / "hermes"
SKILLS = sorted(p.parent for p in (ROOT / "skills").glob("*/SKILL.md"))
# kit-derived files keep the MIT notice (NOTICE); the "Three Ms of AI" name and branding are not used
BANNED = re.compile(r"three ms|\b3ms\b|nate herk|herk|default shift|bike method|four cs|bike-method|three-ms", re.I)


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path}: no YAML frontmatter"
    return yaml.safe_load(m.group(1))


def test_manifest_and_soul():
    manifest = yaml.safe_load((ROOT / "distribution.yaml").read_text(encoding="utf-8"))
    assert manifest["name"] == "assistantos" and manifest["license"] == "MIT"
    assert (ROOT / "SOUL.md").read_text(encoding="utf-8").strip()


def test_there_are_skills():
    assert {"onboard", "grill-me", "link", "level-up", "audit", "decidir", "preparar-reuniao"} <= {p.name for p in SKILLS}


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.name)
def test_skill_frontmatter(skill):
    fm = frontmatter(skill / "SKILL.md")
    assert fm["name"] == skill.name
    assert isinstance(fm["description"], str) and 40 <= len(fm["description"]) <= 600
    assert fm.get("license") == "MIT" and fm.get("version")


@pytest.mark.parametrize("path", [p for p in ROOT.joinpath("skills").rglob("*") if p.is_file()] + [ROOT / "SOUL.md"],
                         ids=lambda p: str(p.relative_to(ROOT)))
def test_no_three_ms_branding(path):
    assert not BANNED.search(path.read_text(encoding="utf-8", errors="ignore")), f"{path}: branding term"


def test_profile_config_connects_the_assistantos_mcp_server():
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    srv = cfg["mcp_servers"]["assistantos"]
    assert srv["command"] == "uv" and srv["args"][-3:] == ["mcp", "--home", "${AOS_HOME}"]
    assert set(cfg) == {"mcp_servers"}   # Hermes keeps config.yaml on update: ship nothing the owner might tune
