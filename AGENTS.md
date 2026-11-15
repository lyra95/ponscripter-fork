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
- Text sprites, including `logsp` backlog pages, determine ruby headroom from
  their own string. Do not inherit the live dialogue's ruby state: that clips
  old-log readings after a plain page and shifts ordinary menu labels after a
  ruby page. `test_backlog_runtime.py` compares both histories and ruby-off.
- Ruby remains one output/skip unit, but character-based auto-mode timing
  counts the base glyphs with the existing encoding/ligature rules. The reading
  does not add to the wait. Fixed positive auto times are unchanged. The explicit
  `test_auto_mode_runtime.py` checks negative and positive timing modes.
- `rubyguard *clear_text_and_save_backlog` measures the next segment and calls
  the script callback if an existing page would overflow. It does not split
  an arbitrarily long single segment.
- `getSavePath()` prioritizes `LOCAL_SAVEDIR`. macOS CMake defines it, so Mac
  builds use `saves/` beside the app even with Steam enabled and a parsed
  `;localsave mysav` header. This preserves existing saves and matches the
  Mac Auto-Cloud rule observed in Steam logs. Do not create `saveloc.txt` here.
- Windows Steam builds still use `Steam_GetSavePath()`: `saveloc.txt`, otherwise
  the Steam install directory and script's `local_savedir`, with a local fallback.
- The original Mac save-path override has been restored in the unified branch.
  On 2026-11-15 the restored source built on arm64 Mac. A copied-app test
  with Steam forced offline, the legacy header, no arguments and cwd `/` used
  `saves/`; save/restart/load rendered identical frames. This is not a
  Steam-connected or cross-computer sync test. Full-game validation remains
  outstanding.
- The Mac SDK dylib path is `osx/libsteam_api.dylib`.
- The bilingual answer script has a separate, pre-ruby bug: Japanese NVL/ADV
  backlog logsp calls read the Korean page index. `fix_answer_backlog.py` fixes
  only those two calls, consuming indentation to preserve every line length and
  subsequent byte offset. No engine rebuild or save migration is needed for
  this script-only correction. Full-script copied-app tests start with empty
  saves: both Japanese modes recover and both Korean modes remain pixel-identical.
  Migration normalizes only this recognized equal-byte correction in its
  comparison view; raw script/backup bytes and ruby offset maps are untouched.
  Other command differences and changed-line TEXTGOSUB remain rejected. Include
  fix_answer_backlog.py with save_offsets.py in portable release tools.
- PNS 2.7 exists with both 1000 and 1001 serialized sprites. The upstream
  `7656bf49` capacity change did not version the format; using runtime capacity
  as the old save count silently shifts variables/backlogs. `SaveLayout.h`
  validates the entire structure against the script's array size before loading
  an untagged file, and rejects ambiguous/malformed files before state changes.
  New files record the sprite count in the existing optional Pons extension.
  Keep runtime capacity 1001; reading a 1000-entry file resets the absent slot.
  This preserves intact old saves; it cannot reconstruct variables already
  misread and re-saved by the broken loader. Keep those slots and reload an
  intact earlier slot instead of overwriting progress automatically.

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

Ruby conversion changes absolute script byte offsets even if line count and
stripped text match. When replacing a script, use `tools/yomigana/save_offsets.py`
with the exact script that produced the saves and the target script. It copies
PNS 2.7 saves and relocates gosub/FOR stack addresses without changing progress
or the save version. Mac apply/restore now performs this step transactionally.
Do not remigrate saves already written against the target script. Mixed-origin
legacy slots require identifying their source scripts separately; do not guess.
Unsupported formats and TEXTGOSUB continuations on changed lines are rejected.
The migration tool uses the count tag, or requires explicit `--legacy-sprites`
for untagged saves: it cannot infer the writing engine from the PNS version.
Do not assume all legacy files have 1001 entries. Restoring a 1000-sprite engine
can use `--restore-sprites 1000` (CLI migration: `--target-sprites 1000`); it
refuses to discard a nonempty extra slot. Loading old saves in the new engine
does not require rewriting the old files or changing dialogue.
The initial published Mac ZIP predates this fix. Engine-only updates with an
unchanged script do not require save migration. See the explicit copied-app
regression in `tools/yomigana/tests/test_save_migration_runtime.py`.

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
