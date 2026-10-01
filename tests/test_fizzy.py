from datetime import date, datetime, timedelta, timezone

from assistantos.models import Brief, Event, Item, Mark, Status
from assistantos.store import Store
from assistantos.surfaces.fizzy import FizzyConfig, FizzyError, sync

T0 = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)
TODAY = date(2026, 9, 30)
CFG = FizzyConfig(board="b1")
BRIEF = Brief(mudou="pediu orçamento", decisao="d", opcoes=["a"], proximo_passo="responder hoje", rascunho="r",
              urgencia="hoje")


class FakeFizzy:
    """The board as the fizzy CLI would report it."""

    def __init__(self):
        self.cards, self.comments, self.calls, self.n, self.broken, self.postponed = {}, [], [], 100, set(), set()

    def __call__(self, *args):
        self.calls.append(args)
        cmd = args[:2]
        if cmd == ("board", "closed"):
            return [{"number": k} for k, c in self.cards.items() if c["closed"]]
        if cmd == ("board", "postponed"):
            return [{"number": k} for k in self.postponed if k in self.cards]
        if cmd == ("card", "list"):   # like the real CLI: neither closed nor postponed cards are listed here
            return [{"number": k} for k, c in self.cards.items() if not c["closed"] and k not in self.postponed]
        num = int(args[2]) if len(args) > 2 and str(args[2]).isdigit() else None
        if num is not None and (num not in self.cards or num in self.broken):
            raise FizzyError("not_found" if num not in self.cards else "server error")
        if cmd == ("card", "create"):
            self.n += 1
            self.cards[self.n] = {"title": args[args.index("--title") + 1],
                                  "description": args[args.index("--description") + 1], "closed": False, "tags": []}
            return {"number": self.n}
        if cmd == ("card", "tag"):
            self.cards[num]["tags"].append(args[args.index("--tag") + 1])
        elif cmd == ("card", "close"):
            self.cards[num]["closed"] = True
        elif cmd == ("card", "reopen"):
            self.cards[num]["closed"] = False
        elif cmd == ("card", "update"):
            self.cards[num]["description"] = args[args.index("--description") + 1]
        elif cmd == ("comment", "create"):
            self.comments.append((int(args[args.index("--card") + 1]), args[args.index("--body") + 1]))
        return None


def seed(tmp_path, n=2):
    s = Store(tmp_path / "aos.db")
    for k in range(n):
        s.upsert_item(Item(id=f"i{k}", source="whatsapp", title=f"Contato {k}", tag="clientes" if k == 0 else None))
        s.add_event(Event(item_id=f"i{k}", at=T0, direction="in", text="oi"))
    return s


def card_of(s, item_id):
    return s.db.execute("select card from cards where item_id=?", (item_id,)).fetchone()[0]


def test_creates_cards_once_with_tags(tmp_path):
    s, fz = seed(tmp_path), FakeFizzy()
    s.set_brief("i0", BRIEF, T0)
    sync(s, CFG, fz, TODAY)
    sync(s, CFG, fz, TODAY)
    assert len(fz.cards) == 2
    c0 = fz.cards[card_of(s, "i0")]
    assert c0["title"] == "Contato 0" and c0["tags"] == ["clientes"]
    assert "pediu orçamento" in c0["description"] and "http://127.0.0.1:8422" in c0["description"]
    assert fz.cards[card_of(s, "i1")]["tags"] == ["pessoal"]


def test_closed_in_fizzy_marks_done_deleted_marks_ignored(tmp_path):
    s, fz = seed(tmp_path), FakeFizzy()
    sync(s, CFG, fz, TODAY)
    fz.cards[card_of(s, "i0")]["closed"] = True
    del fz.cards[card_of(s, "i1")]
    sync(s, CFG, fz, TODAY)
    assert s.mark("i0").status == Status.FEITO and s.mark("i1").status == Status.IGNORADO
    assert s.db.execute("select count(*) from cards where item_id='i1'").fetchone() == (0,)


def test_resolved_here_closes_and_reopen_comments(tmp_path):
    s, fz = seed(tmp_path, 1), FakeFizzy()
    sync(s, CFG, fz, TODAY)
    s.set_mark(Mark(item_id="i0", status=Status.FEITO, at=T0 + timedelta(minutes=1)))
    sync(s, CFG, fz, TODAY)
    card = card_of(s, "i0")
    assert fz.cards[card]["closed"] is True
    s.add_event(Event(item_id="i0", at=T0 + timedelta(minutes=5), direction="in", text="e o orçamento?"))
    s.set_brief("i0", BRIEF, T0 + timedelta(minutes=5))
    sync(s, CFG, fz, TODAY)
    assert fz.cards[card]["closed"] is False
    assert fz.comments == [(card, "assistantOS · Reaberto: pediu orçamento")]


def test_changed_brief_updates_card(tmp_path):
    s, fz = seed(tmp_path, 1), FakeFizzy()
    sync(s, CFG, fz, TODAY)
    s.set_brief("i0", BRIEF, T0)
    sync(s, CFG, fz, TODAY)
    assert "responder hoje" in fz.cards[card_of(s, "i0")]["description"]


def test_one_failing_card_does_not_stop_the_rest(tmp_path):
    s, fz = seed(tmp_path), FakeFizzy()
    sync(s, CFG, fz, TODAY)
    fz.broken.add(card_of(s, "i0"))
    s.set_mark(Mark(item_id="i0", status=Status.FEITO, at=T0 + timedelta(minutes=1)))
    s.set_mark(Mark(item_id="i1", status=Status.FEITO, at=T0 + timedelta(minutes=1)))
    log = sync(s, CFG, fz, TODAY)
    assert fz.cards[card_of(s, "i1")]["closed"] is True
    assert any("server error" in line for line in log)
    assert s.mark("i0").status == Status.FEITO                       # a server error is not a deletion


def test_empty_store_touches_nothing(tmp_path):
    fz = FakeFizzy()
    assert sync(Store(tmp_path / "aos.db"), CFG, fz, TODAY) == [] and fz.calls == []


def test_postponed_card_is_not_a_deletion(tmp_path):
    s, fz = seed(tmp_path, 1), FakeFizzy()
    sync(s, CFG, fz, TODAY)
    fz.postponed.add(card_of(s, "i0"))
    sync(s, CFG, fz, TODAY)
    assert s.mark("i0") is None and card_of(s, "i0")
