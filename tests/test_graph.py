from datetime import date, datetime, timedelta, timezone

from assistantos.backends import BackendError, QuotaExceeded
from assistantos.graph import run_pass
from assistantos.models import Backend, Brief, Config, Contacts, Event, Item, Mark, Owner, Status, Tags
from assistantos.store import Store

T0 = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
TODAY = date(2026, 9, 30)


def cfg(per_pass=6, per_day=60):
    return Config(owner=Owner(name="Ana"), backend=Backend(kind="claude", per_pass_cap=per_pass, per_day_cap=per_day),
                  contacts=Contacts(), tags=Tags(order=["pessoal"]))


class FakePlugin:
    name = "fake"

    def __init__(self, n=2):
        self.items = [Item(id=f"i{k}", source="fake", title=f"Contato {k}") for k in range(n)]
        self.events = [Event(item_id=f"i{k}", at=T0 + timedelta(minutes=k), direction="in", text=f"pedido {k}",
                             ext_id=f"e{k}") for k in range(n)]

    def poll(self, cfg, since):
        return self.items, [e for e in self.events if since is None or e.at >= since]


class FakeBackend:
    def __init__(self, fail=None):
        self.prompts, self.fail = [], fail or {}

    def ask(self, prompt, output, job):
        self.prompts.append(prompt)
        err = self.fail.get(len(self.prompts))
        if err:
            raise err
        return Brief(mudou="m", decisao="d", opcoes=["a"], proximo_passo="p", rascunho="r", urgencia="hoje")


class FakeJev:
    def __init__(self, p):
        self.p, self.calls = p, 0

    def needs_owner(self, state):
        self.calls += 1
        return self.p


def run(store, plugin, backend, config=None, jev=None):
    return run_pass(store, [(plugin, None)], backend, jev, config or cfg(), TODAY)


def test_first_pass_briefs_open_items_newest_first(tmp_path):
    s, b = Store(tmp_path / "aos.db"), FakeBackend()
    r = run(s, FakePlugin(3), b)
    assert r["new_events"] == 3 and r["briefed"] == ["i2", "i1", "i0"] and r["errors"] == []
    assert "pedido 2" in b.prompts[0] and "Ana" in b.prompts[0] and "sem numerar" in b.prompts[0]
    assert s.brief("i0") is not None


def test_nothing_new_nothing_briefed(tmp_path):
    s, plugin = Store(tmp_path / "aos.db"), FakePlugin(2)
    run(s, plugin, FakeBackend())
    r = run(s, plugin, FakeBackend())
    assert r["new_events"] == 0 and r["briefed"] == []


def test_reopened_item_is_briefed_with_the_new_message_and_previous_brief(tmp_path):
    s, plugin = Store(tmp_path / "aos.db"), FakePlugin(1)
    run(s, plugin, FakeBackend())
    s.set_mark(Mark(item_id="i0", status=Status.FEITO, at=T0 + timedelta(minutes=5)))
    assert run(s, plugin, FakeBackend())["briefed"] == []            # marked done, nothing new
    plugin.events.append(Event(item_id="i0", at=T0 + timedelta(minutes=10), direction="in", text="e agora?",
                               ext_id="e-new"))
    b = FakeBackend()
    assert run(s, plugin, b)["briefed"] == ["i0"]
    assert "e agora?" in b.prompts[0] and "reaberto" in b.prompts[0] and "Brief anterior" in b.prompts[0]


def test_caps(tmp_path):
    s = Store(tmp_path / "aos.db")
    assert len(run(s, FakePlugin(5), FakeBackend(), cfg(per_pass=2))["briefed"]) == 2
    s2 = Store(tmp_path / "b.db")
    for _ in range(3):
        s2.log_run("brief", "claude", "haiku", 1.0, True)
    assert len(run(s2, FakePlugin(5), FakeBackend(), cfg(per_day=4))["briefed"]) == 1


def test_quota_stops_the_pass_other_errors_do_not(tmp_path):
    s = Store(tmp_path / "aos.db")
    r = run(s, FakePlugin(3), FakeBackend(fail={1: BackendError("claude: x")}))
    assert r["briefed"] == ["i1", "i0"] and len(r["errors"]) == 1
    s2 = Store(tmp_path / "b.db")
    b = FakeBackend(fail={1: QuotaExceeded("claude: usage limit")})
    r = run(s2, FakePlugin(3), b)
    assert r["briefed"] == [] and len(b.prompts) == 1 and "usage limit" in r["errors"][0]


def test_social_reopen_is_labelled_not_briefed(tmp_path):
    for p, briefed in ((0.2, []), (0.9, ["i0"])):
        s, plugin = Store(tmp_path / f"{p}.db"), FakePlugin(1)
        run(s, plugin, FakeBackend())
        s.set_mark(Mark(item_id="i0", status=Status.FEITO, at=T0 + timedelta(minutes=5)))
        plugin.events.append(Event(item_id="i0", at=T0 + timedelta(minutes=10), direction="in", text="valeu!",
                                   ext_id="e-new"))
        jev = FakeJev(p)
        assert run(s, plugin, FakeBackend(), jev=jev)["briefed"] == briefed
        assert s.label("i0")[1] == p
        run(s, plugin, FakeBackend(), jev=jev)
        assert jev.calls == 1                                         # labelled once per new message
