import io
import json

from assistantos.jev import Jev, route, social
from assistantos.models import Triage
from assistantos.store import Store


class Opener:
    def __init__(self, answer=None, fail=False):
        self.answer, self.fail, self.bodies = answer, fail, []

    def __call__(self, req, timeout):
        self.bodies.append(json.loads(req.data))
        if self.fail:
            raise OSError("down")
        return io.BytesIO(json.dumps({"model": "jev-x", "answers": {"q": self.answer}}).encode())


def jev(tmp_path, opener, key="k"):
    store = Store(tmp_path / "aos.db")
    return Jev(store, owner="Ana", key=key, opener=opener), store


def test_triage_uses_owner_name_and_logs(tmp_path):
    op = Opener({"choice": "sessao", "probabilities": {"sessao": 0.7}})
    j, store = jev(tmp_path, op)
    assert j.triage("migra o banco", "Projeto X") == Triage(label="sessao", p=0.7)
    body = op.bodies[0]
    assert body["model"] == "jev-latest" and "Ana" in body["state"] and "Ian" not in json.dumps(body)
    assert store.db.execute("select job, backend, ok from runs").fetchall() == [("triage", "jev", 1)]


def test_failure_returns_none_and_logs(tmp_path):
    j, store = jev(tmp_path, Opener(fail=True))
    assert j.needs_owner("oi") is None
    assert store.db.execute("select ok from runs").fetchall() == [(0,)]


def test_no_key_no_call(tmp_path, monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    op = Opener({"noul": 0.9})
    store = Store(tmp_path / "aos.db")
    assert Jev(store, owner="Ana", opener=op).needs_owner("oi") is None
    assert op.bodies == [] and store.db.execute("select count(*) from runs").fetchone() == (0,)


def test_route_thresholds():
    assert route(Triage(label="sessao", p=0.60)) == "session"
    assert route(Triage(label="sessao", p=0.59)) == "llm"
    assert route(Triage(label="enviar", p=0.80)) == "send"
    assert route(Triage(label="enviar", p=0.79)) == "llm"
    assert route(None) == "llm"


def test_social_is_a_label_threshold():
    assert social(0.39) and not social(0.40) and not social(None)
