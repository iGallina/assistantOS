from datetime import date, datetime, timezone

import pytest

from assistantos.models import Mark, Status as S
from assistantos.reconcile import status

T = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)
TODAY = date(2026, 9, 30)


def m(s, **kw):
    return Mark(item_id="i", status=s, at=T, **kw)


@pytest.mark.parametrize("mark, fresh, expected", [
    (None, False, S.ABERTO),
    (None, True, S.ABERTO),
    (m(S.ABERTO), True, S.ABERTO),                      # "desfazer" = no mark
    (m(S.FEITO), False, S.FEITO),
    (m(S.FEITO), True, S.REABERTO),                     # their side moved after the owner's mark
    (m(S.IGNORADO), True, S.REABERTO),
    (m(S.DEPOIS, until=date(2026, 10, 2)), False, S.DEPOIS),
    (m(S.DEPOIS, until=date(2026, 9, 30)), False, S.ABERTO),   # "amanhã" arrived
    (m(S.DEPOIS), True, S.REABERTO),
    (m(S.AGUARDANDO, who="Kat", until=date(2026, 10, 1)), False, S.AGUARDANDO),
    (m(S.AGUARDANDO, who="Kat", until=date(2026, 9, 30)), False, S.VENCIDO),
    (m(S.AGUARDANDO, who="Kat", until=date(2026, 10, 1)), True, S.REABERTO),   # answered before the date
])
def test_status(mark, fresh, expected):
    assert status(mark, fresh, TODAY) == expected


def test_statuses_from_store(tmp_path):
    from datetime import timedelta

    from assistantos.models import Event, Item
    from assistantos.reconcile import statuses
    from assistantos.store import Store

    s = Store(tmp_path / "aos.db")
    for i in ("a", "b", "c"):
        s.upsert_item(Item(id=i, source="whatsapp", title=i))
        s.add_event(Event(item_id=i, at=T, direction="in", text="oi"))
    s.set_mark(Mark(item_id="a", status=S.FEITO, at=T + timedelta(minutes=1)))   # marked after their message
    s.set_mark(Mark(item_id="b", status=S.FEITO, at=T - timedelta(minutes=1)))   # they wrote after the mark
    assert statuses(s, TODAY) == {"a": S.FEITO, "b": S.REABERTO, "c": S.ABERTO}
