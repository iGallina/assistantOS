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


def test_init_then_doctor_ok(tmp_path, monkeypatch, capsys, fake_claude):
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


import sqlite3
import time

from assistantos import cli
from assistantos.models import Brief

JID = "5561000000001@s.whatsapp.net"


class _Backend:
    def ask(self, prompt, output, job):
        return Brief(mudou="m", decisao="d", opcoes=["a"], proximo_passo="p", rascunho="r", urgencia="hoje")


def _wacli(path):
    c = sqlite3.connect(path)
    c.execute("create table chats(jid text, kind text, name text)")
    c.execute("create table messages(chat_jid text, msg_id text, ts integer, from_me integer, media_type text, "
              "text text, media_caption text)")
    c.execute("insert into chats(jid, name) values (?, 'Kat')", (JID,))
    c.execute("insert into messages values (?, 'm1', ?, 0, null, 'pode me mandar o orçamento?', null)", (JID, int(time.time())))
    c.commit()
    c.close()


def test_init_copies_the_whatsapp_template(tmp_path, monkeypatch):
    monkeypatch.setenv("AOS_HOME", str(tmp_path))
    main(["init"])
    assert (tmp_path / "local" / "config" / "whatsapp.json").exists()


def test_run_one_pass(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AOS_HOME", str(tmp_path))
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.setattr(cli, "make_backend", lambda cfg, store: _Backend())
    main(["init"])
    _wacli(tmp_path / "wacli.db")
    (tmp_path / "local" / "config" / "whatsapp.json").write_text(
        json.dumps({"store": str(tmp_path / "wacli.db"), "chats": [JID]}), encoding="utf-8")
    capsys.readouterr()
    assert main(["run"]) == 0
    assert capsys.readouterr().out.strip() == t("run.summary", new=1, briefed=1, errors=0)


def test_doctor_reports_a_broken_plugin(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AOS_HOME", str(tmp_path))
    main(["init"])
    (tmp_path / "local" / "config" / "whatsapp.json").write_text(
        json.dumps({"store": str(tmp_path / "nope.db"), "chats": [JID]}), encoding="utf-8")
    assert main(["doctor"]) == 1
    assert "plugin whatsapp: wacli store" in capsys.readouterr().out


def test_init_copies_fizzy_template_and_doctor_accepts_it_unset(tmp_path, monkeypatch, capsys, fake_claude):
    monkeypatch.setenv("AOS_HOME", str(tmp_path))
    main(["init"])
    assert (tmp_path / "local" / "config" / "fizzy.json").exists()
    assert main(["doctor"]) == 0
    assert "plugin fizzy:" in capsys.readouterr().out


import os
import sys as _sys

import pytest as _pytest


@_pytest.fixture
def fake_claude(tmp_path, monkeypatch):
    """A `claude` on PATH: a .cmd on Windows, an executable file elsewhere."""
    d = tmp_path / "fakebin"
    d.mkdir()
    exe = d / ("claude.cmd" if _sys.platform == "win32" else "claude")
    exe.write_text("@echo off\n" if _sys.platform == "win32" else "#!/bin/sh\n", encoding="utf-8")
    exe.chmod(0o755)
    monkeypatch.setenv("PATH", str(d) + os.pathsep + os.environ.get("PATH", ""))
    return exe


def test_doctor_checks_the_backend_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AOS_HOME", str(tmp_path))
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    main(["init"])
    capsys.readouterr()
    assert main(["doctor"]) == 1
    assert t("doctor.backend_bad", kind="claude") in capsys.readouterr().out


def test_doctor_finds_the_backend(tmp_path, monkeypatch, capsys, fake_claude):
    monkeypatch.setenv("AOS_HOME", str(tmp_path))
    main(["init"])
    assert main(["doctor"]) == 0
    assert "claude" in capsys.readouterr().out


def test_local_bin_comes_first_on_path(tmp_path, monkeypatch):
    monkeypatch.setenv("AOS_HOME", str(tmp_path))
    main(["init"])
    assert os.environ["PATH"].split(os.pathsep)[0] == str(tmp_path / "local" / "bin")


class _Sched:
    def __init__(self):
        self.calls = []

    def install(self, home, uv, minutes=5):
        self.calls.append(("install", home, uv, minutes))

    def remove(self):
        self.calls.append(("remove",))

    def status(self):
        return "Ready last=… result=0"


def test_setup_inits_schedules_and_checks(tmp_path, monkeypatch, capsys, fake_claude):
    sched = _Sched()
    monkeypatch.setenv("AOS_HOME", str(tmp_path))
    monkeypatch.setattr(cli, "scheduler", lambda: sched)
    assert main(["setup"]) == 0
    assert (tmp_path / "local" / "config" / "owner.json").exists()
    assert sched.calls[0][0] == "install" and sched.calls[0][1] == tmp_path
    assert main(["schedule", "status"]) == 0 and "Ready" in capsys.readouterr().out
    assert main(["schedule", "remove"]) == 0 and sched.calls[-1] == ("remove",)
