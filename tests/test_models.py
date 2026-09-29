from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from assistantos.models import LLM_OUTPUTS, Event, Mark, Status, TagRule, Tags

NOW = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)


def test_llm_outputs_are_strict_for_codex():
    for m in LLM_OUTPUTS:
        s = m.model_json_schema()
        assert s["additionalProperties"] is False, m
        assert set(s["required"]) == set(s["properties"]), m


def test_bad_regex_is_rejected():
    with pytest.raises(ValidationError, match="pattern"):
        TagRule(field="title", pattern="(", tag="x")


def test_tags_must_be_in_order():
    with pytest.raises(ValidationError, match="not in order"):
        Tags(order=["pessoal"], default="pessoal", rules=[TagRule(field="title", pattern="x", tag="outro")])


def test_event_needs_timezone():
    with pytest.raises(ValidationError):
        Event(item_id="a", at=datetime(2026, 9, 29, 12, 0), direction="in")


def test_aguardando_needs_who_and_until():
    with pytest.raises(ValidationError, match="who and until"):
        Mark(item_id="a", status=Status.AGUARDANDO, at=NOW)
    Mark(item_id="a", status=Status.AGUARDANDO, at=NOW, who="Kat", until=date(2026, 10, 1))


@pytest.mark.parametrize("computed", [Status.REABERTO, Status.VENCIDO])
def test_computed_statuses_cannot_be_marked(computed):
    with pytest.raises(ValidationError, match="computed"):
        Mark(item_id="a", status=computed, at=NOW)
