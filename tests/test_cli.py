import json

import pytest

from assistantos import __version__
from assistantos.cli import main
from assistantos.i18n import _strings, t


def test_version(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    assert capsys.readouterr().out.strip() == f"aos {__version__}"


def test_locales_have_the_same_keys():
    assert _strings("pt-BR").keys() == _strings("en").keys()


def test_init_then_doctor_ok(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AOS_HOME", str(tmp_path))
    assert main(["init"]) == 0
    assert main(["init"]) == 0  # idempotent: never overwrites
    assert main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert t("doctor.config_ok") in out and "✗" not in out


def test_doctor_names_the_bad_field(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AOS_HOME", str(tmp_path))
    main(["init"])
    (tmp_path / "local" / "config" / "backend.json").write_text(json.dumps({"kind": "gpt"}), encoding="utf-8")
    assert main(["doctor"]) == 1
    assert "backend.json: kind:" in capsys.readouterr().out


def test_doctor_before_init(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AOS_HOME", str(tmp_path))
    assert main(["doctor"]) == 1
    assert "owner.json: missing" in capsys.readouterr().out
