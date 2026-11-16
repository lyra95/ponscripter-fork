#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_rel="src/extlib/src/smpeg-2.0.0"
prefix="${SMPEG2_PATH:-/opt/ponscripter-deps}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# Export tracked source from Git so Windows checkout line endings and ignored
# compiler outputs never enter the Linux dependency build.
git config --global --add safe.directory "$repo_root"
git -C "$repo_root" archive HEAD "$source_rel" | tar -xf - -C "$work"
smpeg_source="$work/$source_rel"

if ! (
    cd "$smpeg_source"
    chmod +x config.sub config.guess install-sh 2>/dev/null || true
    bash ./autogen.sh
    chmod +x config.sub config.guess install-sh missing compile depcomp 2>/dev/null || true
    ./configure --prefix="$prefix" --disable-debug --disable-rpath
    make --jobs=2
    make install
) >"$work/build.log" 2>&1; then
    tail -n 80 "$work/build.log" >&2
    exit 1
fi

printf 'Built bundled SMPEG and installed it at %s.\n' "$prefix"
