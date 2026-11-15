# Portable Yomigana tools

This directory is portable source, intended to work after cloning the fork on
another computer. Do not add personal absolute paths, game scripts, saves,
screenshots, compiled binaries or virtual environments to Git.

The conversion targets are compatible 07th-Mod-based bilingual EP1–4 and EP5–8
UTF-8 `0.u` scripts with
`langjp`/`langen`, `rubyon 17,17` and `*clear_text_and_save_backlog`.
Generate annotations from an unmodified script into a separate output file.
Preserve Korean lines, commands, line count and line endings. Automatic readings
are imperfect; keep the name overrides and conversion report.

Windows x86 builds and local installations for both games have been performed.
Read `docs/YOMIGANA.md` and `docs/WINDOWS_BUILD.md` for the current branch and
validation limits. macOS binaries cannot run on Windows. Verify each game's
actual save directory before installing or changing save-path behavior.

The script's `;localsave mysav` is a parsed header directive. Mac CMake defines
`LOCAL_SAVEDIR`, which takes priority over Steam and forces `saves/` beside the
app. The original Mac override is restored in the current branch to preserve
existing progress and match the observed Steam Auto-Cloud path. Windows Steam
save handling is unchanged; keep each installation's actual save configuration.
Test default launches without `--root`, `--save` or `--script`, from cwd `/`, using
a copied app layout with the real header and copied saves. Never run such tests
against a user's live game directory.

PNS version 2.7 alone does not identify its sprite count: legacy engines wrote
1000 or 1001 entries. The current loader validates both complete layouts and
new saves carry an optional count tag. Never reintroduce a fixed-count legacy
load or migration. `save_offsets.py` needs `--legacy-sprites` for untagged files;
do not guess for a mixed-origin save directory. An engine-only update leaves
save bytes intact. Test actual old-format loading, variable values and backlog
pixels, not just a save produced by the same engine being tested.

Keep backups of the current engine, original script and current saves before
applying changes. Do not restore historical saves over new progress during an
engine update. Do not replace a running game or terminate it automatically.

`fix_answer_backlog.py` corrects a pre-existing wrong Korean page-index reference
in the answer script's two Japanese logsp calls. It preserves individual line
lengths and all subsequent offsets by consuming two indentation spaces. Apply
on a copy; no save migration for this correction alone. When combined with a
ruby script migration, use equivalently patched source/target copies so the
strict canonical comparison still permits only ruby/guard differences.
`test_answer_backlog_runtime.py` explicitly tests the real copied script in
both languages and ADV/NVL, with fresh empty saves and no loadgame call.

Only engine binaries/libraries and portable tools belong in Mac release assets.
Retain the user's app icon and game data locally through the installer. The Mac
payload is arm64, ad-hoc signed, and requires the minimum macOS version recorded
in `BUILD_INFO.json`. SDL2-compat dynamically loads SDL3: preserve the
`libSDL3.dylib` symlink in addition to the linked libraries.

Parser test (from repo root; Python tools run through the locked uv environment):

```sh
c++ -std=c++11 -I src tools/yomigana/tests/ruby_parser.cpp -o ruby-parser-test
./ruby-parser-test
uv run --locked python -m unittest discover -s tools/yomigana/tests -v
```

Historical Mac validation covered bilingual captures, existing saves, restart/backlog,
typing vs immediate output, and page-guard text preservation. The user confirmed
successful save loading and normal play after the Mac save path fix. Full-game
and exhaustive Windows compatibility validation remain outstanding. Do not call static overflow estimates
confirmed incidents; one captured long-dialogue case already clipped in the
original engine while the ruby engine paginated earlier even without the guard.
