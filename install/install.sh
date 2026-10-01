#!/bin/sh
# assistantOS — install on macOS. From the repo folder:  sh install/install.sh   (safe to run again)
set -eu
cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"
command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
command -v claude >/dev/null 2>&1 || curl -fsSL https://claude.ai/install.sh | bash
uv sync --locked
uv run aos setup
