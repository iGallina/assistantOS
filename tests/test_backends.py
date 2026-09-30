import json
import sys
from pathlib import Path

import pytest

from assistantos.backends import BackendError, QuotaExceeded, make_backend
from assistantos.models import Backend as BackendCfg, Brief
from assistantos.store import Store

FAKE = Path(__file__).with_name("fake_cli.py")
BRIEF = {"mudou": "m", "decisao": "d", "opcoes": ["a"], "proximo_passo": "p", "rascunho": "r", "urgencia": "hoje"}


def backend(kind, tmp_path, **cfg):
    store = Store(tmp_path / "aos.db")
    b = make_backend(BackendCfg(kind=kind, **cfg), store, cmd=[sys.executable, str(FAKE), kind])
    return b, store


def runs(store):
    return store.db.execute("select job, backend, model, ok from runs").fetchall()


@pytest.mark.parametrize("kind", ["claude", "codex"])
def test_ask_returns_validated_model_and_logs(kind, tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_REPLY", json.dumps(BRIEF))
    b, store = backend(kind, tmp_path, model="m1")
    assert b.ask("oi", Brief, "brief") == Brief(**BRIEF)
    assert runs(store) == [("brief", kind, "m1", 1)]


def test_claude_command_carries_the_schema(tmp_path, monkeypatch):
    argv = tmp_path / "argv.json"
    monkeypatch.setenv("FAKE_REPLY", json.dumps(BRIEF))
    monkeypatch.setenv("FAKE_ARGV", str(argv))
    b, store = backend("claude", tmp_path)
    b.ask("oi", Brief, "brief")
    a = json.loads(argv.read_text())
    assert a[a.index("--model") + 1] == "haiku" and runs(store)[0][2] == "haiku"  # default used and logged
    assert json.loads(a[a.index("--json-schema") + 1]) == Brief.model_json_schema()
    assert a[a.index("--tools") + 1] == ""


def test_codex_schema_goes_by_file(tmp_path, monkeypatch):
    argv = tmp_path / "argv.json"
    monkeypatch.setenv("FAKE_REPLY", json.dumps(BRIEF))
    monkeypatch.setenv("FAKE_ARGV", str(argv))
    backend("codex", tmp_path)[0].ask("oi", Brief, "brief")
    a = json.loads(argv.read_text())
    assert "--output-schema" in a and "-s" in a and a[a.index("-s") + 1] == "read-only"
    assert "-m" not in a  # no model configured → the CLI's default


@pytest.mark.parametrize("kind", ["claude", "codex"])
def test_quota_is_its_own_error(kind, tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_REPLY", "quota")
    b, store = backend(kind, tmp_path)
    with pytest.raises(QuotaExceeded):
        b.ask("oi", Brief, "brief")
    assert runs(store)[0][3] == 0


def test_wrong_shape_is_backend_error(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_REPLY", json.dumps({"mudou": "só isso"}))
    b, store = backend("codex", tmp_path)
    with pytest.raises(BackendError, match="Brief"):
        b.ask("oi", Brief, "brief")
    assert runs(store)[0][3] == 0


def test_unreadable_output_is_backend_error(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_REPLY", "garbage")
    with pytest.raises(BackendError):
        backend("claude", tmp_path)[0].ask("oi", Brief, "brief")


def test_not_installed(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))
    b = make_backend(BackendCfg(kind="codex"), Store(tmp_path / "aos.db"))
    with pytest.raises(BackendError, match="not installed"):
        b.ask("oi", Brief, "brief")


def test_gemini_not_yet(tmp_path):
    with pytest.raises(BackendError, match="not supported yet"):
        make_backend(BackendCfg(kind="gemini"), Store(tmp_path / "aos.db"))
