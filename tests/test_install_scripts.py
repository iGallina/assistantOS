from pathlib import Path

BOM = b"\xef\xbb\xbf"


def test_powershell_scripts_with_accents_carry_a_bom():
    """Windows PowerShell 5.1 (the only one on a fresh Windows) reads a BOM-less file as Windows-1252: an em dash or a
    "não" in a string then breaks the parser. Measured in the test VM, 2026-10-08."""
    for f in Path(__file__).parents[1].glob("install/*.ps1"):
        data = f.read_bytes()
        if not data.isascii():
            assert data.startswith(BOM), f"{f.name}: non-ASCII without a UTF-8 BOM"


def test_inno_script_carries_a_bom():
    """Inno Setup 6 reads a script as UTF-8 only with a BOM; otherwise every Portuguese message comes out garbled."""
    iss = Path(__file__).parents[1] / "install" / "assistantOS.iss"
    assert iss.read_bytes().startswith(BOM)
