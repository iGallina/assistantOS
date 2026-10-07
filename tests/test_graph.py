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
    for at in (T0, T0, T0, T0 - timedelta(days=1)):                  # the cap counts the owner's day only
        s2.db.execute("INSERT INTO runs(at, job, backend, model, seconds, ok) VALUES (?, 'brief', 'claude', 'haiku', 1, 1)",
                      (at.isoformat(),))
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


class FakeSurface:
    name = "fake-surface"

    def __init__(self):
        self.seen = []

    def sync(self, store, cfg, today, lang):
        self.seen.append([i.id for i in store.items() if store.brief(i.id)])
        return ["#1 +x"]


def test_surface_runs_after_briefs(tmp_path):
    s, surf = Store(tmp_path / "aos.db"), FakeSurface()
    r = run_pass(s, [(FakePlugin(1), None)], FakeBackend(), None, cfg(), TODAY, surfaces=[(surf, None)])
    assert surf.seen == [["i0"]] and r["surfaced"] == ["#1 +x"]


from assistantos.models import RequestPlan, Triage


class PlanBackend(FakeBackend):
    def __init__(self, plan=None, fail=None):
        super().__init__(fail)
        self.plan = plan

    def ask(self, prompt, output, job):
        if output is RequestPlan:
            self.prompts.append(prompt)
            if err := self.fail.get(len(self.prompts)):
                raise err
            return self.plan
        return super().ask(prompt, output, job)


class TriageJev(FakeJev):
    def __init__(self, label=None, p=0.0):
        super().__init__(0.9)
        self.t = label and Triage(label=label, p=p)

    def triage(self, ask_text, title=""):
        return self.t


def ask_on_fresh_item(tmp_path, backend, jev=None):
    s, plugin = Store(tmp_path / "aos.db"), FakePlugin(1)
    run(s, plugin, FakeBackend())
    rid = s.add_request("i0", "responde dizendo que entrego sexta", "page")
    r = run(s, plugin, backend, jev=jev)
    return s, rid, r


def test_request_draft_is_saved_and_answered(tmp_path):
    b = PlanBackend(RequestPlan(action="draft", text="Oi! Entrego na sexta."))
    s, rid, r = ask_on_fresh_item(tmp_path, b)
    assert s.draft("i0") == "Oi! Entrego na sexta." and s.request(rid)["state"] == "answered"
    assert "entrego sexta" in b.prompts[-1] and "pedido 0" in b.prompts[-1]
    assert r["requests"] == [rid]


def test_request_reply_and_session(tmp_path):
    s, rid, _ = ask_on_fresh_item(tmp_path, PlanBackend(RequestPlan(action="reply", text="Ela pediu orçamento.")))
    assert s.request(rid)["reply"] == "Ela pediu orçamento." and s.draft("i0") is None
    s2, rid2, _ = ask_on_fresh_item(tmp_path / "b", PlanBackend(RequestPlan(action="session", text="precisa do PDF")))
    assert s2.request(rid2)["state"] == "needs_session" and "precisa do PDF" in s2.request(rid2)["reply"]


def test_confident_jev_session_skips_the_model(tmp_path):
    b = PlanBackend(RequestPlan(action="reply", text="x"))
    s, rid, _ = ask_on_fresh_item(tmp_path, b, jev=TriageJev("sessao", 0.7))
    assert s.request(rid)["state"] == "needs_session" and not any("entrego sexta" in p for p in b.prompts)


def test_failed_request_stays_open(tmp_path):
    b = PlanBackend(RequestPlan(action="reply", text="x"), fail={1: BackendError("claude: down")})
    s, plugin = Store(tmp_path / "aos.db"), FakePlugin(1)
    run(s, plugin, FakeBackend())
    rid = s.add_request("i0", "resume", "page")
    r = run(s, plugin, b)
    assert s.request(rid)["state"] == "open" and r["errors"]


def test_request_failing_twice_goes_to_a_session(tmp_path):
    b = PlanBackend(RequestPlan(action="reply", text="x"), fail={1: BackendError("bad json"), 2: BackendError("bad json")})
    s, plugin = Store(tmp_path / "aos.db"), FakePlugin(1)
    run(s, plugin, FakeBackend())
    rid = s.add_request("i0", "resume", "page")
    run(s, plugin, b)
    run(s, plugin, b)
    assert s.request(rid)["state"] == "needs_session" and "bad json" in s.request(rid)["reply"]
    assert len(b.prompts) == 2


def test_follow_up_carries_the_earlier_exchange(tmp_path):
    b = PlanBackend(RequestPlan(action="reply", text="Ela pediu orçamento."))
    s, rid, _ = ask_on_fresh_item(tmp_path, b)
    s.add_request("i0", "e o valor?", "page", parent=rid)
    run(s, FakePlugin(1), b)
    assert "entrego sexta" in b.prompts[-1] and "Ela pediu orçamento." in b.prompts[-1] and "e o valor?" in b.prompts[-1]


class RefreshPlugin(FakePlugin):
    def refresh(self, cfg):
        return "wacli sync: offline"


def test_a_failing_refresh_is_reported_and_the_pass_goes_on(tmp_path):
    r = run(Store(tmp_path / "aos.db"), RefreshPlugin(1), FakeBackend())
    assert r["briefed"] == ["i0"] and r["errors"] == ["fake: wacli sync: offline"]
