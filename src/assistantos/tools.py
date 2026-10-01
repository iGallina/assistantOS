"""Third-party tools `aos setup` puts in local/bin: pinned versions, verified against each project's published SHA-256
(checksums.txt of each release, read 2026-10-01). A tool already on PATH is left alone. A hash mismatch writes nothing."""
import hashlib
import io
import platform
import shutil
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

W = "https://github.com/openclaw/wacli/releases/download/v0.19.0/wacli_0.19.0_"
F = "https://github.com/basecamp/fizzy-cli/releases/download/v4.0.1/fizzy_4.0.1_"
B = "https://github.com/bitwarden/sdk-sm/releases/download/bws-v2.1.0/bws-"
TOOLS = {
    "wacli": {
        "windows_amd64": (W + "windows_amd64.zip", "92d96c9d211844c30244b433cbc02e96f2088f4f3ce515becb0e51ed5e55fddd"),
        "darwin_arm64": (W + "darwin_arm64.tar.gz", "d033cd1ee2c62cb60a3aae9d1c9abab8f5ac13b72a3a423ddf40d23284bf3d70"),
        "darwin_amd64": (W + "darwin_amd64.tar.gz", "1cbe652438f88b830ebbae7e5e8caa9e8381c1cc16da10a8c25bed6c871a1669"),
    },
    "fizzy": {
        "windows_amd64": (F + "windows_amd64.zip", "abaf68c2a125c47e14e2c8f7d212a727775dd7135a938d97ec2fb048db657e26"),
        "darwin_arm64": (F + "darwin_arm64.tar.gz", "111b6bcb200b79b7bbfd075b80f0bb90541566e0d8cb12abb30b988dbba8fd64"),
        "darwin_amd64": (F + "darwin_amd64.tar.gz", "f6ac2f55c9b514bd50ef1b3f41bbcd6cf3873199b00914173b270d0ebdf6cf20"),
    },
    "bws": {
        "windows_amd64": (B + "x86_64-pc-windows-msvc-2.1.0.zip", "8d6f2b51beb6f992b5b1de8b85a98bdf18de74096b724d17fa06219fc23f2bd5"),
        "darwin_arm64": (B + "aarch64-apple-darwin-2.1.0.zip", "9cb1c1c6e6164d83b2e339883ba02b4cbb37188ce9a484b1ce8249443163e066"),
        "darwin_amd64": (B + "x86_64-apple-darwin-2.1.0.zip", "6f626b3971368902af1b9847c02791a1b4666969d7561e2047681cded7997537"),
    },
}


class ToolError(Exception):
    pass


def platform_key(system: str = sys.platform, machine: str = platform.machine()) -> str:
    if system == "win32":
        return "windows_amd64"   # Windows on ARM runs x64 binaries
    if system == "darwin":
        return "darwin_arm64" if machine == "arm64" else "darwin_amd64"
    raise ToolError(f"no pinned tools for {system}/{machine}")


def _download(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def _extract(archive: bytes, url: str, exe: str) -> bytes:
    if url.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            member = next((n for n in z.namelist() if Path(n).name == exe), None)
            return z.read(member) if member else b""
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as t:
        member = next((m for m in t.getmembers() if Path(m.name).name == exe), None)
        return t.extractfile(member).read() if member else b""


def install_tools(bin_dir: Path, key: str | None = None, fetch=_download) -> list[str]:
    key, done = key or platform_key(), []
    for name, per in TOOLS.items():
        exe = name + (".exe" if sys.platform == "win32" else "")
        if shutil.which(name) or (bin_dir / exe).exists():
            continue
        url, sha = per[key]
        archive = fetch(url)
        if hashlib.sha256(archive).hexdigest() != sha:
            raise ToolError(f"{name}: sha256 mismatch for {url} — refusing to install")
        data = _extract(archive, url, exe)
        if not data:
            raise ToolError(f"{name}: {exe} not found in {url}")
        bin_dir.mkdir(parents=True, exist_ok=True)
        (bin_dir / exe).write_bytes(data)
        (bin_dir / exe).chmod(0o755)
        done.append(f"{name} → {bin_dir / exe}")
    return done
