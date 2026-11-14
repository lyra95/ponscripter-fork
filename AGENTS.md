# Yomigana fork handoff

The active branch `feat/japanese-ruby` is the Windows engine used for both
EP1–4 and EP5–8. It is based on `e06c6a2f298f2e1036e7c5b8fd4b2571808f8f71`,
with the original EP1–4 ruby changes replayed and rendering fixes added.
It was formerly named `feat/japanese-ruby-ep5-8`.
The earlier EP1–4 line, based on `mod:ba457e4261f9876a707d12ee03fd22dc6b0a2478`,
is preserved as `backup/feat/japanese-ruby` locally and on origin.
Read `docs/YOMIGANA.md` and `tools/yomigana/AGENTS.md` before continuing.

The installed answer script calls `simul_*` commands implemented at `e06c6a2`
but absent at `ba457e4`. This supports keeping those command implementations;
it does not identify the source repository of the installed executable or prove
that the resulting engine cannot run EP1–4. On 2026-11-15 this engine was also
installed for EP1–4; startup was observed and the user reported it working.

## Engine behavior

- Ruby notation is `｜漢字《かんじ》`. Parsing, drawing, width calculation,
  text-buffer/backlog preservation, skip/timing and page measurement are supported.
- Ruby line spacing stays consistent across wait/voice segments and restored text;
  ordinary menus keep normal line spacing.
- `rubyguard *clear_text_and_save_backlog` measures the next segment and calls
  the script callback if an existing page would overflow. It does not split
  an arbitrarily long single segment.
- Current `getSavePath()` gives `STEAM` priority. `Steam_GetSavePath()` reads
  `saveloc.txt`, otherwise tries the Steam install directory and script's
  `local_savedir`, with a local fallback. `;localsave mysav` IS parsed.
- macOS CMake defines `LOCAL_SAVEDIR`, but this branch does NOT force `saves/`
  or give that define priority over `STEAM`. Do not describe the historical Mac
  save-path fix as current code. That fix belongs to the earlier EP1–4 branch
  and published Mac release. The current base has not been validated on macOS.
- The Mac SDK dylib path is `osx/libsteam_api.dylib`.

## Build and installation

Windows x86 builds succeeded in MSYS2 MINGW32. The current base was installed
for both games. See `docs/WINDOWS_BUILD.md` for toolchain, DLL pairing and the
limits of runtime validation. Build binaries once for this source revision;
each game still needs its own script, assets, App ID and save configuration.

Preserve Korean dialogue, language switching and current save progress. Work on
copies for automated runtime tests. Before installing, back up the executable,
matching DLL, active script, save-location configuration and CURRENT saves.
Do not replace a running game, terminate it automatically, or overwrite newer
saves with historical backups. User authorization in the session takes precedence.
Recheck the active save directory; Windows installations currently use `mysav`.

Do not commit personal paths, game dialogue/assets, saves, virtualenvs, SDK
binaries or engine binaries. Portable tools live in `tools/yomigana/`.
The only intended game screenshots in Git are the two requested README images.
Local backups and build caches are not portable dependencies.

## Historical Mac release and validation limits

The published `v0.1.0-macos-arm64` release came from the earlier EP1–4 line
(source recorded as `63b0e989eafebc91f0dbda0a97ec2df90fdaf754`). Its recorded
minimum OS is macOS 26.0, architecture arm64, with ad-hoc signing. Earlier
handoff records report seven Python tests, parser checks, full-script conversion,
Mac existing-save loading, restart/backlog and typing/immediate-output checks.
Those are historical results, not validation of the current base on macOS.

Preserve `libSDL3.dylib` when bundling SDL2-compat; it is loaded with dlopen.
The bundler signs dylibs and the executable outside the template app before
copying them back. Measure minimum OS from the packaged binaries.

Full-game completion and exhaustive compatibility testing remain outstanding.
Do not claim ruby caused an overflow solely from historical long-dialogue
comparisons: the original already clipped in the recorded case. Static candidate
counts are not confirmed incident counts. Avoid unnecessary story spoilers.
