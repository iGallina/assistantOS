import json
from functools import cache
from importlib.resources import files


@cache
def _strings(lang: str) -> dict[str, str]:
    return json.loads(files("assistantos").joinpath(f"locales/{lang}.json").read_text(encoding="utf-8"))


def t(key: str, lang: str = "pt-BR", **kw) -> str:
    return _strings(lang)[key].format(**kw)
