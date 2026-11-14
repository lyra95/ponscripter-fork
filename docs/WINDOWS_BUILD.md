# Windows build and installation notes

The active `feat/japanese-ruby` branch is based on
`e06c6a2f298f2e1036e7c5b8fd4b2571808f8f71` and is used locally for EP1–4 and
EP5–8. Its former name was `feat/japanese-ruby-ep5-8`.
The earlier EP1–4 branch based on `mod:ba457e4` is preserved as
`backup/feat/japanese-ruby` on origin and locally.

The answer script calls custom commands such as `simul_lipall`,
`simul_multfont`, `simul_nextld` and `simul_nextvoice`. `e06c6a2` implements them;
`ba457e4` does not. This explains retaining that base, not the provenance of the
installed executable. It does not imply that this engine cannot run EP1–4.

## Local toolchain and pinned Python dependencies

These are versions recorded for the local Windows work, not minimum versions
or a promise that the same packages remain available from package repositories.

| Component | Recorded version / source |
| --- | --- |
| uv | 0.13.8 (`x86_64-pc-windows-msvc`) |
| Python | CPython 3.12.10, selected by `.python-version` |
| fugashi | 1.5.2, pinned in `pyproject.toml` and `uv.lock` |
| unidic-lite | 1.0.8, pinned in `pyproject.toml` and `uv.lock` |
| Steamworks headers and Win32 redistributable | `rlabrecque/SteamworksSDK` commit `df2baabf574a738ef1ea90a7e89339107fc0a279` |
| MSYS2 | Installed with winget package `MSYS2.MSYS2`, installer version recorded as `20260927` |
| MINGW32 GCC | 16.2.0-4 (`mingw-w64-i686-gcc`) |
| make | 4.4.1-3 (MSYS2 package `make`) |
| Autoconf tooling | `autoconf-wrapper` 20260320-1; `automake-wrapper` 20260320-1 |

The Python tooling is a non-package uv project. Run `uv sync --locked` from
the repository root; keep `.venv/` local. The standalone Mac release also
contains `tools/yomigana/requirements.txt`. Python does not build the C++ engine.

## Windows x86 build

Use MSYS2 MINGW32 to match the installed PE i386 (`0x014C`) executables.
The historical CI scripts use these packages and `make -j2`; local builds
have succeeded with this environment. This is not a claim that the old hosted
CI runner configuration still works today.

```sh
pacman --sync --noconfirm --needed \
  mingw-w64-i686-gcc make autoconf automake-wrapper
```

In PowerShell, from the repository root, prepare the SDK:

```powershell
uv sync --locked
uv run --locked python tools/yomigana/fetch_steam_sdk.py --platform win32
```

In an MSYS2 **MINGW32** shell, from the repository root:

```sh
./configure --steam
make -j2
```

The engine is `src/ponscr.exe`; its matching SDK DLL is staged at
`src/extlib/lib/steam_api.dll`. This DLL is the unmodified pinned Win32 SDK
redistributable, not an engine-specific shim. The new engine imports
`SteamInternal_SteamAPI_Init`; an older 186,560-byte DLL observed during the
initial installation did not export it. The pinned DLL is 280,728 bytes, SHA256
`1cb8b7cb77923762d4e49b27e44295369a79e93b5d4282c5e840b268d28fe771`.
Match by architecture and hash, not size alone. An installation already using
this DLL does not need a second copy. Back up the old engine and its DLL as a
pair before changing either one.

## Per-game installation

| Game | Observed Steam directory name | Executable name |
| --- | --- | --- |
| EP1–4, Question Arcs | `Umineko` | `Umineko1to4.exe` |
| EP5–8, Answer Arcs | `Umineko Chiru` | `Umineko5to8.exe` |

Locate each directory through Steam; library paths vary. Both installed scripts
have a Korean review patch caption dated 2026-08-10, bilingual `langjp`/`langen`,
`rubyon 17,17` and `*clear_text_and_save_backlog`. The installed converted scripts
also contain ruby notation and the single `rubyguard` directive. Steam's original
unmodified script is not the conversion target. Prepare each game's compatible
script separately; do not copy the answer script or game assets into EP1–4.

The observed `saveloc.txt` in each game points to that game's `mysav` directory.
The header contains `;localsave mysav`. `saves` also exists and must not be assumed
to contain current progress. Recheck these settings and current saves before
each installation. Keep each game's own `steam_appid.txt` and configuration.

1. Close the game. Back up its current executable, DLL, active `0.u`,
   `saveloc.txt`, App ID file, and current save directories outside the repo.
2. For a first ruby conversion, run `annotate.py` on that game's unconverted
   compatible `0.u` into a separate output file. Review the report. For an engine
   update with an already converted script, keep the script as-is.
3. Copy `src/ponscr.exe` over that game's executable using the name in the table.
   Deploy the matching DLL if needed. One build can be used for both games;
   their scripts, assets and save directories remain separate.
4. Launch normally and check existing-save loading, Korean/Japanese switching,
   ruby layout, backlog, and saving/restarting. Compare script and save hashes
   around an engine-only update; startup alone does not establish all of these.

## Recorded validation and limits

The initial Windows handoff records report a successful build, seven Python
tests, a standalone C++ parser check and a responsive copied game installation.
Those are historical results, not tests rerun for every subsequent revision.

Earlier notes mixed the Question Arcs directory and conversion statistics into
an Answer Arcs section. On 2026-11-15 the installed converted scripts were
rechecked separately:

| Script | Lines | Ruby groups |
| --- | ---: | ---: |
| EP1–4 | 375,656 | 229,479 |
| EP5–8 | 365,085 | 211,130 |

These are observations of the local scripts, not required counts for every patch
version. Both contain one `rubyguard` directive. The converter's own checks
require an identical round trip after removing ruby and that directive, and
preserve non-Japanese lines. The installed-file counts alone do not prove that
historical conversion validation was performed for either script.

The answer engine was rebuilt and installed after the ruby layout and redraw
fixes, with its script and current saves backed up. On 2026-11-15 the source at
`dce5664` was rebuilt in MINGW32 and installed as `Umineko1to4.exe` for EP1–4.
The installed engine SHA256 was
`964431200dcebe17d4a94fdf4327bc9e9de46261b83c15e8c6fac5df5acb3c28`.
The problem game opened and played its opening video. Its script and pre-existing
save files were byte-identical to the backup after startup. The user then reported
that it appeared to work; the branch was renamed to `feat/japanese-ruby`.
The answer installation still had the earlier build hash
`915fd7e1987f2243f45e5576cf295c19f88acf2fa833aec9a091e8b8fcd2752c` when inspected.
Different build hashes do not by themselves establish different engine behavior.

The user previously reported answer-game play and rendering issues that prompted
the fixes. This does not establish complete post-fix coverage. Full EP1–8 play,
all save/load and language-switch paths, and the current source on macOS remain
unverified. The historical Mac release uses the earlier EP1–4 source line.
Its `LOCAL_SAVEDIR` priority and `saves/` override have been restored in the
current source; this does not change Windows Steam save handling.
See `YOMIGANA.md` before building for Mac.
