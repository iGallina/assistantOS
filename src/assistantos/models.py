"""Every Pydantic model: per-user config, domain records, and each LLM output."""
import re
from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- config (local/config/*.json) ---

class Owner(Strict):
    name: str
    language: Literal["pt-BR", "en"] = "pt-BR"
    timezone: str = "America/Sao_Paulo"


class Backend(Strict):
    kind: Literal["claude", "codex", "gemini"]
    model: str | None = None
    per_pass_cap: int = Field(6, ge=0)
    per_day_cap: int = Field(60, ge=0)


class Contacts(Strict):
    owner_self: str | None = None
    count_only: list[str] = []
    never_list: list[str] = []


class TagRule(Strict):
    field: Literal["group", "id", "source", "title"]
    pattern: str
    tag: str

    @field_validator("pattern")
    @classmethod
    def _compiles(cls, v: str) -> str:
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"invalid regex: {e}") from e
        return v


class Tags(Strict):
    order: list[str]
    default: str = "pessoal"
    rules: list[TagRule] = []
    descriptions: dict[str, str] = {}

    @model_validator(mode="after")
    def _known_tags(self) -> "Tags":
        unknown = {self.default, *(r.tag for r in self.rules)} - set(self.order)
        if unknown:
            raise ValueError(f"tags not in order: {sorted(unknown)}")
        return self


class Config(Strict):
    owner: Owner
    backend: Backend
    contacts: Contacts
    tags: Tags


# --- domain ---

class Status(StrEnum):
    ABERTO = "aberto"
    REABERTO = "reaberto"
    DEPOIS = "depois"
    FEITO = "feito"
    IGNORADO = "ignorado"
    AGUARDANDO = "aguardando"
    VENCIDO = "vencido"


COMPUTED = {Status.REABERTO, Status.VENCIDO}


class Item(Strict):
    id: str
    source: str
    title: str
    tag: str | None = None
    link: str | None = None


class Event(Strict):
    item_id: str
    at: AwareDatetime
    direction: Literal["in", "out"]
    text: str = ""


class Mark(Strict):
    item_id: str
    status: Status
    at: AwareDatetime
    who: str | None = None
    until: date | None = None

    @model_validator(mode="after")
    def _rules(self) -> "Mark":
        if self.status in COMPUTED:
            raise ValueError(f"{self.status} is computed, never set by the owner")
        if self.status == Status.AGUARDANDO and not (self.who and self.until):
            raise ValueError("aguardando needs who and until")
        return self


# --- LLM outputs: every field required, no defaults, no free dicts (Codex strict schema) ---

class Brief(Strict):
    mudou: str
    decisao: str
    opcoes: list[str]
    proximo_passo: str
    rascunho: str
    urgencia: Literal["hoje", "semana", "sem pressa"]  # as AIS-OS brief.py


class RequestPlan(Strict):
    action: Literal["reply", "draft", "task", "event", "session"]
    text: str
    when: str  # ISO date-time for task/event, "" otherwise


class Triage(Strict):
    label: str
    p: float = Field(ge=0, le=1)


LLM_OUTPUTS = (Brief, RequestPlan)
