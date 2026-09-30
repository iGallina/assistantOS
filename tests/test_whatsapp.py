import sqlite3
import time
from datetime import datetime, timezone

import pytest

from assistantos.config import ConfigError
from assistantos.plugins import load_plugins
from assistantos.plugins.whatsapp import WhatsApp, WhatsAppConfig

NOW = int(time.time())
KAT, BOB, GROUP = "5561000000001@s.whatsapp.net", "5561000000002@s.whatsapp.net", "123@g.us"


def wacli_store(path, rows, chats=((KAT, "Kat"), (BOB, None), (GROUP, "Escola"))):
    """A store with wacli's column names for the two tables the plugin reads."""
    c = sqlite3.connect(path)
    c.execute("create table chats(jid text primary key, kind text, name text)")
    c.execute("create table messages(chat_jid text, msg_id text, ts integer, from_me integer, "
              "media_type text, text text, media_caption text)")
    c.executemany("insert into chats(jid, name) values (?,?)", chats)
    c.executemany("insert into messages values (?,?,?,?,?,?,?)", rows)
    c.commit()
    c.close()
    return path


def test_poll_items_and_events(tmp_path):
    store = wacli_store(tmp_path / "wacli.db", [
        (KAT, "m1", NOW - 60, 0, None, "oi, tudo bem?", None),
        (KAT, "m2", NOW - 30, 1, None, "tudo, e você?", None),
        (KAT, "m3", NOW - 20, 0, "audio", None, None),
        (KAT, "m4", NOW - 10, 0, None, "", None),                       # reaction/system row: no text
        (BOB, "m5", NOW - 5, 0, "image", None, "foto do canteiro"),
        (GROUP, "m6", NOW - 5, 0, None, "não configurado", None),
    ])
    items, events = WhatsApp().poll(WhatsAppConfig(store=str(store), chats=[KAT, BOB]), None)
    assert [(i.id, i.title) for i in items] == [(f"wa:{KAT}", "Kat"), (f"wa:{BOB}", BOB)]
    assert [(e.ext_id, e.direction, e.text) for e in events] == [
        ("wa:m1", "in", "oi, tudo bem?"), ("wa:m2", "out", "tudo, e você?"),
        ("wa:m3", "in", "[audio]"), ("wa:m5", "in", "foto do canteiro")]
    assert events[0].at == datetime.fromtimestamp(NOW - 60, timezone.utc)


def test_floor_and_since(tmp_path):
    store = wacli_store(tmp_path / "wacli.db", [
        (KAT, "old", NOW - 8 * 86400, 0, None, "velha", None),
        (KAT, "mid", NOW - 100, 0, None, "meio", None),
        (KAT, "new", NOW - 10, 0, None, "nova", None),
    ])
    cfg = WhatsAppConfig(store=str(store), chats=[KAT])
    assert [e.text for e in WhatsApp().poll(cfg, None)[1]] == ["meio", "nova"]
    since = datetime.fromtimestamp(NOW - 50, timezone.utc)
    assert [e.text for e in WhatsApp().poll(cfg, since)[1]] == ["nova"]


def test_store_is_never_written(tmp_path):
    store = wacli_store(tmp_path / "wacli.db", [(KAT, "m1", NOW, 0, None, "oi", None)])
    before = (store.read_bytes(), store.stat().st_mtime_ns)
    WhatsApp().poll(WhatsAppConfig(store=str(store), chats=[KAT]), None)
    assert (store.read_bytes(), store.stat().st_mtime_ns) == before


def test_check(tmp_path):
    good = wacli_store(tmp_path / "wacli.db", [])
    assert WhatsApp().check(WhatsAppConfig(store=str(good), chats=[KAT])) is None
    assert "wacli" in WhatsApp().check(WhatsAppConfig(store=str(tmp_path / "missing.db"), chats=[KAT]))


def test_load_plugins(tmp_path):
    assert load_plugins(tmp_path) == []
    (tmp_path / "whatsapp.json").write_text('{"_about": "x", "chats": ["a@s.whatsapp.net"]}', encoding="utf-8")
    [(plugin, cfg)] = load_plugins(tmp_path)
    assert plugin.name == "whatsapp" and cfg.chats == ["a@s.whatsapp.net"]
    (tmp_path / "whatsapp.json").write_text('{"chats": "not a list"}', encoding="utf-8")
    with pytest.raises(ConfigError, match="whatsapp.json: chats"):
        load_plugins(tmp_path)
