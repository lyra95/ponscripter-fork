# Portable Yomigana tools

This directory is portable source, intended to work after cloning the fork on
another computer. Do not add personal absolute paths, game scripts, saves,
screenshots, compiled binaries or virtual environments to Git.

The supported game script is the 07th-Mod bilingual EP1–4 `0.u` with
`langjp`/`langen`, `rubyon 17,17` and `*clear_text_and_save_backlog`.
Generate annotations from an unmodified script into a separate output file.
Preserve Korean lines, commands, line count and line endings. Automatic readings
are imperfect; keep the name overrides and conversion report.

Windows continuation is authorized, but a Windows build has NOT been produced or
validated. Follow `docs/YOMIGANA.md` and upstream `INSTALL.md`. macOS binaries
cannot run on Windows. Verify the Windows installation's actual save directory
before adding any platform-specific save path behavior.

On macOS, the original script's `;localsave mysav` is a parsed header directive,
not an ordinary ignored comment. This fork's Mac CMake build intentionally uses
the existing `saves/` beside the app. A previous version read the wrong directory.
Test default launches without `--root`, `--save` or `--script`, from cwd `/`, using
a copied app layout with the real header and copied saves. Never run such tests
against a user's live game directory.

Keep backups of the current engine, original script and current saves before
applying changes. Do not restore historical saves over new progress during an
engine update. Do not replace a running game or terminate it automatically.

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

Earlier validation covered bilingual captures, existing saves, restart/backlog,
typing vs immediate output, and page-guard text preservation. The user confirmed
successful save loading and normal play after the Mac save path fix. Full-game
and Windows validation remain outstanding. Do not call static overflow estimates
confirmed incidents; one captured long-dialogue case already clipped in the
original engine while the ruby engine paginated earlier even without the guard.
