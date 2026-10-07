from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from assistantos.bugreport import URL_MAX, issue_url, mask

LEAKS = {
    "+55 61 99999-8888": "[telefone]", "(61) 99999-8888": "[telefone]", "61 3333-4444": "[telefone]",
    "5561999998888": "[telefone]", "+1 415 555 0100": "[telefone]",
    "5561999998888@s.whatsapp.net": "[whatsapp]", "120363025@g.us": "[whatsapp]",
    "kat.souza+x@empresa.com.br": "[email]",
    "123.456.789-09": "[cpf]", "12.345.678/0001-95": "[cnpj]", "4111 1111 1111 1111": "[cartão]",
    "sk-ant-api03-AbCdEf123456": "[chave]", "Bearer eyJhbGciOiJIUzI1NiJ9.x.y": "[chave]",
    "ghp_0123456789abcdefABCDEF0123456789abcd": "[chave]", "a3f9c0d1e2b4a5f6c7d8e9f0a1b2c3d4e5f6a7b8": "[chave]",
    # residue measured on a real WhatsApp store (2026-10-03): 1,053 digit runs survived the labelled patterns
    "12345678909": "[número]", "70000-000": "[número]", "33334444": "[número]", "99999-8888": "[número]",
    "113-1234567-1234567": "[número]", "415-555-0100": "[número]", "9 9999-8888": "[número]", "10.20.30.40": "[número]",
    "pedido PO12345678": "[número]", "/p/abc1234567890?x": "[número]", "_9999999999_": "[número]",
    "11-22-33-4444": "[número]",
}


@pytest.mark.parametrize("leak,label", LEAKS.items())
def test_each_pattern_is_masked(leak, label):
    out = mask(f"antes {leak} depois", [])
    assert leak not in out and label in out and out.startswith("antes ") and out.endswith(" depois")


def test_contacts_and_home_are_masked():
    home = str(Path.home())
    out = mask(f"Kat Souza respondeu; KAT SOUZA de novo; Zé; arquivo {home}/x.db", ["Kat Souza", "Zé", "A"])
    assert "Kat" not in out and "KAT" not in out and "Zé" not in out and home not in out
    assert out.count("[contato]") == 3 and "~/x.db" in out.replace("\\", "/")


def test_safe_text_survives():
    safe = ("2026-10-03 21:56:12 · aos 0.1.0 · schema 4 · 12.3 s · Python 3.12.7 · #12: claude: exit 1 · 0x41303 · "
            "2026-10-03T21:56:12.5+00:00 · 03/10/2026 · 2026/10/03 · 21:56 · 03-10-2026 · 10 de 60")
    assert mask(safe, []) == safe


def test_issue_url_fits():
    url = issue_url("bug: x", "linha\n" * 5000)
    q = parse_qs(urlparse(url).query)
    assert len(url) <= URL_MAX and q["title"] == ["bug: x"] and q["body"][0].startswith("linha")
    assert urlparse(url).path == "/iGallina/assistantOS/issues/new"
