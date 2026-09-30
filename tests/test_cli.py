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
