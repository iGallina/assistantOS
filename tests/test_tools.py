import hashlib
import io
import sys
import tarfile
import zipfile

import pytest

from assistantos import tools


def zip_with(name, data=b"bin"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(f"dir/{name}", data)
    return buf.getvalue()


def tgz_with(name, data=b"bin"):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        info = tarfile.TarInfo(name)
        info.size = len(data)
        t.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def manifest(archive, kind):
    return {"demo": {"key": ("https://example/demo." + kind, hashlib.sha256(archive).hexdigest())}}


@pytest.mark.parametrize("kind, make", [("zip", zip_with), ("tar.gz", tgz_with)])
def test_installs_verified_binary(tmp_path, monkeypatch, kind, make):
    exe = "demo.exe" if sys.platform == "win32" else "demo"
    archive = make(exe)
    monkeypatch.setattr(tools, "TOOLS", manifest(archive, kind))
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    lines = tools.install_tools(tmp_path / "bin", "key", fetch=lambda url: archive)
    assert (tmp_path / "bin" / exe).read_bytes() == b"bin"
    assert lines and "demo" in lines[0]


def test_hash_mismatch_writes_nothing(tmp_path, monkeypatch):
    archive = zip_with("demo")
    monkeypatch.setattr(tools, "TOOLS", {"demo": {"key": ("https://example/demo.zip", "0" * 64)}})
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    with pytest.raises(tools.ToolError, match="sha256"):
        tools.install_tools(tmp_path / "bin", "key", fetch=lambda url: archive)
    assert not (tmp_path / "bin").exists() or not any((tmp_path / "bin").iterdir())


def test_tool_on_path_is_not_downloaded(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "TOOLS", manifest(b"x", "zip"))
    monkeypatch.setattr(tools.shutil, "which", lambda name, **kw: "/opt/homebrew/bin/demo")
    assert tools.install_tools(tmp_path / "bin", "key", fetch=lambda url: pytest.fail("downloaded")) == []


def test_platform_key():
    assert tools.platform_key("win32", "AMD64") == "windows_amd64"
    assert tools.platform_key("win32", "ARM64") == "windows_amd64"   # x64 emulation on Windows on ARM
    assert tools.platform_key("darwin", "arm64") == "darwin_arm64"
    assert tools.platform_key("darwin", "x86_64") == "darwin_amd64"


def test_manifest_covers_every_platform():
    for name, per in tools.TOOLS.items():
        assert set(per) == {"windows_amd64", "darwin_arm64", "darwin_amd64"}, name
        assert all(len(sha) == 64 for _, sha in per.values()), name
