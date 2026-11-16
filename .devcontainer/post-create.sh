#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

mkdir -p "$STEAM_SDK_ROOT" "$UV_PROJECT_ENVIRONMENT"

bash .devcontainer/build-smpeg.sh
python3 tools/yomigana/fetch_steam_sdk.py \
    --platform linux64 \
    --destination "$STEAM_SDK_ROOT"
uv sync --locked

printf '\nDev environment ready. Configure with docs/LINUX_BUILD.md.\n'
