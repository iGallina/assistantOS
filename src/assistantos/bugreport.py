"""Bug reports to the upstream repo, masked on this machine first. Deterministic patterns and the owner's contacts —
no model, no network: the report is saved and shown, and only the owner's own click on GitHub's form sends it."""
import platform
import re
from functools import cache
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from . import __version__
from .config import ConfigError, load_config
from .store import Store

UPSTREAM = "iGallina/assistantOS"
URL_MAX = 8000  # GitHub rejects longer issue URLs; the full report stays in the local file
CUT = "\n\n(cortado: o relatório completo está no arquivo local)"
ERRORS_TAIL = 40
# order matters: secrets and ids that contain digits or "@" go before e-mails, phones before cards
PATTERNS = [(re.compile(p), label) for p, label in (
    (r"\bBearer\s+\S+", "[chave]"),
    (r"\b(?:sk|pk|rk)-[\w-]{8,}|\b(?:ghp|gho|ghs|ghu|github_pat|xox[abpr])_[\w-]{8,}|\bAKIA[0-9A-Z]{12,}|\bAIza[\w-]{20,}",
     "[chave]"),
    (r"\b(?=[\w-]*\d)(?=[\w-]*[A-Za-z])[\w-]{32,}\b", "[chave]"),           # long tokens and hashes
    (r"\b\d[\d-]{5,}@(?:s\.whatsapp\.net|g\.us|lid|c\.us|broadcast)\b", "[whatsapp]"),
    (r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "[email]"),
    (r"(?<![\d.])\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}(?!\d)", "[cnpj]"),
    (r"(?<![\d.])\d{3}\.\d{3}\.\d{3}-\d{2}(?!\d)", "[cpf]"),                 # unformatted CPFs fall to the phone rule
    (r"(?<![\w-])(?:\+?55[\s-]?)?\(?\d{2}\)?[\s-]?9?\d{4}[\s-]?\d{4}(?![\w-])", "[telefone]"),
    (r"(?<!\w)\+\d{1,3}(?:[\s-]?\d){7,12}(?!\d)", "[telefone]"),
    (r"(?<!\d)(?:\d{4}[ -]?){3}\d{1,7}(?!\d)", "[cartão]"),
    # whatever is left with 8+ digits: unformatted CPFs, CEPs, phones without area code, order numbers, IPs
    (r"(?<!\d)\d(?:[\s.\-/()]?\d){7,}(?!\d)", "[número]"),  # also glued to letters: URL ids, "PO12345678"
)]
# dates and times are kept: protected before the patterns run, put back after
D, M, Y = r"(?:0?[1-9]|[12]\d|3[01])", r"(?:0?[1-9]|1[0-2])", r"(?:19|20)\d\d"   # real dates only: phones must not pass
SAFE = re.compile(rf"(?<![\d/.-])(?:{Y}-{M}-{D}(?:[ T]\d{{2}}:\d{{2}}(?::\d{{2}}(?:\.\d+)?)?(?:[+-]\d{{2}}:\d{{2}}|Z)?)?"
                  rf"|{D}[/.-]{M}[/.-]{Y}|{Y}/{M}/{D}|\d{{1,2}}:\d{{2}}(?::\d{{2}})?)(?![/.-]?\d)")


@cache
def _names(names: tuple[str, ...]) -> re.Pattern | None:
    """One alternation, longest first, so "Kat Souza" wins over "Kat"."""
    keep = sorted({n.strip() for n in names if len(n.strip()) >= 2}, key=len, reverse=True)
    return re.compile(rf"(?<!\w)(?:{'|'.join(map(re.escape, keep))})(?!\w)", re.IGNORECASE) if keep else None


def mask(text: str, names: list[str]) -> str:
    home = str(Path.home())
    for h in {home, home.replace("\\", "/")}:
        text = text.replace(h, "~")
    kept: list[str] = []
    text = SAFE.sub(lambda m: kept.append(m.group()) or f"\x00{len(kept) - 1}\x00", text)
    for rx, label in PATTERNS:
        text = rx.sub(label, text)
    rx = _names(tuple(names))
    text = rx.sub("[contato]", text) if rx else text
    return re.sub(r"\x00(\d+)\x00", lambda m: kept[int(m.group(1))], text)


def build_report(home: Path, description: str, doctor: str) -> tuple[str, str]:
    """(issue title, report body), both already masked with the same contacts."""
    names, calls, schema = [], [], "—"
    try:
        names.append(load_config(home / "local" / "config").owner.name)
    except ConfigError:
        pass
    db = home / "local" / "state" / "aos.db"
    if db.exists():
        s = Store(db)
        now = datetime.now(timezone.utc)
        names += [i.title for i in s.items()]
        counts: dict[tuple, list[int]] = {}
        for job, backend, *_, ok in s.runs_between(now - timedelta(days=7), now):
            c = counts.setdefault((job, backend), [0, 0])
            c[0], c[1] = c[0] + 1, c[1] + (not ok)
        calls = [f"- {j} · {b}: {n} calls, {f} failed" for (j, b), (n, f) in sorted(counts.items())]
        schema = str(s.version())
        s.close()
    log = home / "local" / "state" / "errors.log"
    errors = log.read_text(encoding="utf-8", errors="replace").splitlines()[-ERRORS_TAIL:] if log.exists() else []
    body = f"""## What happened
{description}

## Environment
- aos {__version__} · {platform.platform()} · Python {platform.python_version()} · store schema {schema}

## aos doctor
```
{doctor.strip()}
```

## AI calls, last 7 days
{chr(10).join(calls) or "- none"}

## Last errors (local/state/errors.log)
```
{chr(10).join(errors) or "none"}
```
"""
    return mask("bug: " + (description.splitlines() or [""])[0][:80], names), mask(body, names)


def issue_url(title: str, body: str) -> str:
    base, n = f"https://github.com/{UPSTREAM}/issues/new?", len(body)
    while True:
        url = base + urlencode({"title": title, "body": body if n == len(body) else body[:n] + CUT})
        if len(url) <= URL_MAX:
            return url
        n = int(n * 0.9)
