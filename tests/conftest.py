import os

import pytest


@pytest.fixture(autouse=True)
def _restore_path(monkeypatch):
    """`aos` prepends local/bin to PATH in-process; restore it after every test."""
    monkeypatch.setenv("PATH", os.environ.get("PATH", ""))
