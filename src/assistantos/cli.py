import argparse
import sys

from . import __version__


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")  # Windows pipes default to cp1252
    p = argparse.ArgumentParser(prog="aos")
    p.add_argument("--version", action="version", version=f"aos {__version__}")
    p.parse_args(argv)
    return 0
