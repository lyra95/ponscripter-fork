# Yomigana fork handoff

EP1–4 work uses branch `feat/japanese-ruby` in `lyra95/ponscripter-fork` and
the unchanged baseline is branch `mod`, commit
`ba457e4261f9876a707d12ee03fd22dc6b0a2478`. EP5–8 Windows integration uses
`feat/japanese-ruby-ep5-8`, based on Brotherq95's Korean patch engine `kr250501`
(`e06c6a2`).
Read `docs/YOMIGANA.md` and `tools/yomigana/AGENTS.md` before continuing.

## What is preserved here

- Engine changes: ruby notation `｜漢字《かんじ》`, ruby drawing/width calculation,
  Japanese-only line spacing, text-buffer/backlog and skip/timing support.
- `rubyguard *clear_text_and_save_backlog` measures the next segment and invokes
  the game's callback before a page overflows. It handles a non-empty page;
  it does not split an arbitrarily long single segment.
- macOS CMake uses `LOCAL_SAVEDIR` and explicitly selects `saves/`. The script
  header `;localsave mysav` IS parsed and previously caused a save-location bug.
  Do not regress this or test only with an explicit `--save` path.
- Universal Steam API dylib path on Mac is `osx/libsteam_api.dylib`.
- Portable conversion, backup/apply/restore, Mac bundling, SDK fetch and tests
  live in `tools/yomigana/`. Game scripts, saves, game assets and SDK binaries
  are not tracked here. Mac binaries belong in GitHub Releases.

Initial published binary: pre-release tag `v0.1.0-macos-arm64`, based on source
commit `63b0e989eafebc91f0dbda0a97ec2df90fdaf754`. It contains the engine/libraries
and portable tools, not an independent game or game assets. A fresh GitHub clone
with a fresh venv passed all seven Python tests and the parser. The extracted
release passed real full-script apply, bundled-app runtime, default save path,
restart/load and restore checks. Personal recovery materials were exported
outside the original workspace and are not in this repository.

## Development constraints

The user intends to continue from this fork on a Windows computer. Do not rely on
paths, backups, build caches or Python environments outside this repository. The
EP5–8 Windows engine has been built, but its in-game runtime and save loading are
not yet validated. Follow `docs/YOMIGANA.md` for the exact engine base and Windows
build process; do not substitute the EP1–4 binary in the answer game.

Preserve Korean dialogue, language switching and current save progress. Work on
copies for tests. Before installing a change, back up the current app/executable,
original script and CURRENT saves. Do not replace a running game, terminate it
automatically, or restore old saves over newer progress as part of an engine update.

Mac binary minimum OS is measured by the packager; the first shipped build is
arm64/macOS 26.0+. Preserve `libSDL3.dylib`: SDL2-compat loads SDL3 with dlopen,
so merely following `otool -L` misses it. The original Steam app root contains
an installscript that prevents whole-bundle codesigning. The bundler signs dylibs
and signs the executable outside the app before copying it back.

Do not commit personal paths, game dialogue, saves, virtualenvs, SDK downloads or
compiled binaries. GitHub README screenshots are the two explicitly requested,
same-scene before/after images under `docs/images/`.

## Evidence and limits

Earlier Mac validation covered existing saves, Korean capture byte equality,
restart/backlog, final output of timed/instant typing, parser sanitizers and
page-guard text preservation. After fixing the default save path, the user
confirmed successful save loading and normal play. Full-game validation remains
outstanding. See docs for repeatable tests, not the deleted workspace's fixtures.

Do not claim ruby newly caused an overflow based on the historical long-dialogue
comparison. The original already clipped; the ruby engine paginated earlier even
before adding the guard. A preliminary static candidate count was not a confirmed
incident count. Avoid adding unnecessary story spoilers to chat or documentation.
