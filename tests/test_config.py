import json
import shutil

import pytest

from assistantos.config import EXAMPLES, ConfigError, load_config


def init(d):
    for ex in EXAMPLES.glob("*.example.json"):
        shutil.copyfile(ex, d / ex.name.replace(".example", ""))


def test_templates_validate(tmp_path):
    init(tmp_path)
    assert load_config(tmp_path).backend.kind == "claude"


def test_problem_names_file_and_field(tmp_path):
    init(tmp_path)
    (tmp_path / "backend.json").write_text(json.dumps({"kind": "gpt"}), encoding="utf-8")
    with pytest.raises(ConfigError) as e:
        load_config(tmp_path)
    assert any(p.startswith("backend.json: kind:") for p in e.value.problems)


def test_missing_and_broken_files_all_reported(tmp_path):
    init(tmp_path)
    (tmp_path / "owner.json").unlink()
    (tmp_path / "tags.json").write_text("{", encoding="utf-8")
    with pytest.raises(ConfigError) as e:
        load_config(tmp_path)
    assert "owner.json: missing" in e.value.problems
    assert any(p.startswith("tags.json: invalid JSON") for p in e.value.problems)
