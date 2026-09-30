"""One status per item, computed from the owner's mark and the item's events (AIS-OS em-aberto.status, 2026-09-26).
fresh = their side moved after the owner's mark: a marked item with a newer inbound message comes back."""
from datetime import date

from .models import Mark, Status
from .store import Store


def status(mark: Mark | None, fresh: bool, today: date) -> Status:
    if mark is None or mark.status == Status.ABERTO:
        return Status.ABERTO
    if fresh:
        return Status.REABERTO
    if mark.status == Status.AGUARDANDO:
        return Status.VENCIDO if mark.until <= today else Status.AGUARDANDO
    if mark.status == Status.DEPOIS and mark.until and mark.until <= today:
        return Status.ABERTO
    return mark.status


def is_fresh(store: Store, item_id: str, mark: Mark | None) -> bool:
    last_in = store.last_event(item_id, "in")
    return bool(mark and last_in and last_in.at > mark.at)


def statuses(store: Store, today: date) -> dict[str, Status]:
    out = {}
    for item in store.items():
        mark = store.mark(item.id)
        out[item.id] = status(mark, is_fresh(store, item.id, mark), today)
    return out
