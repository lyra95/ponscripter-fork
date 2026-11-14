# Windows continuation notes

This is the Windows build guide for `feat/japanese-ruby-ep5-8`. The branch
starts from `e06c6a2f298f2e1036e7c5b8fd4b2571808f8f71`, replays the EP1–4 ruby
commits from `feat/japanese-ruby`, then adds EP5–8 fixes. EP1–4 remains on
`feat/japanese-ruby`, based on `mod:ba457e4261f9876a707d12ee03fd22dc6b0a2478`.

Why keep the EP5–8 base: the installed answer script calls custom commands such
as `simul_lipall`, `simul_multfont`, `simul_nextld` and `simul_nextvoice`.
`e06c6a2` registers and implements these; `ba457e4` does not. This demonstrates
script-engine compatibility needs, not the provenance of the installed game
executable.

## Local toolchain and pinned Python dependencies

| Component | Version / source |
| --- | --- |
| uv | 0.13.8 (`x86_64-pc-windows-msvc`) |
| Python | CPython 3.12.10, selected by uv |
| fugashi | 1.5.2, pinned in `pyproject.toml` and `uv.lock` |
| unidic-lite | 1.0.8, pinned in `pyproject.toml` and `uv.lock` |
| Steamworks headers and Win32 redistributable | `rlabrecque/SteamworksSDK` commit `df2baabf574a738ef1ea90a7e89339107fc0a279`; fetched with `tools/yomigana/fetch_steam_sdk.py --platform win32` |
| MSYS2 | Installed with winget package `MSYS2.MSYS2`, installer version `20260927` |
| MINGW32 GCC | `mingw-w64-i686-gcc` 16.2.0-4 |
| MINGW32 make | `make` 4.4.1-3 |
| Autoconf tooling | `autoconf-wrapper` 20260320-1; `automake-wrapper` 20260320-1 |

The repository's Python tooling is a non-package uv project. Recreate it with
`uv sync --locked`; keep `.venv/` local and commit `uv.lock`. The standalone Mac
release continues to include `tools/yomigana/requirements.txt`.

The installed Steam game executable is PE machine `0x014C` (x86). Use the MSYS2
MINGW32 environment to match it. The repo's CI uses these build packages:

```sh
pacman --sync --noconfirm --needed \
  mingw-w64-i686-gcc make autoconf automake-wrapper
```

The project `INSTALL.md` calls for `./configure --steam` followed by `make`.
In the Windows CI this is run in MINGW32 with `make -j2`. The pinned SDK
redistributable is staged by `configure` into `src/extlib/lib/steam_api.dll`;
do not copy the Mac dylib or a Win64 DLL into this x86 build. This engine
imports `SteamInternal_SteamAPI_Init`, which the installed game's older
186,560-byte `steam_api.dll` does not export. Deploy the matching pinned
280,728-byte Win32 SDK DLL with the new engine. Back up and restore the old
engine and DLL as a pair; the old engine imports a different Steam API ABI.

## Installed game state observed for this continuation

- Steam game directory: `<SteamLibrary>\steamapps\common\Umineko` (use the
  local Steam library path; do not hard-code a personal path into the repo).
- The current script is the Korean review patch dated 2026-08-10. It contains
  `langjp`, `langen`, `rubyon 17,17`, `simul_*` custom commands, and
  `*clear_text_and_save_backlog`; the header selects `mysav` with
  `;localsave mysav`.
- `saveloc.txt` points to the game's `mysav` directory. `mysav` had saves
  written on 2026-11-14, while `saves` contains older files and
  `steam_autocloud.vdf`. Recheck this before installing or testing; do not
  assume the two directories are interchangeable.
- The game was running during read-only inspection, then closed before backup.
  The current executable, Steam API DLL, script, `saveloc.txt`, `mysav`, and
  `saves` have been copied to a date-stamped backup outside the Git repo. Never
  replace a running game or restore older saves over newer progress; preserve
  both save directories.

The full-game conversion was run to an ignored validation path inside `.venv/`
without modifying the installed script. Its report showed 375,656 lines,
229,479 ruby groups, Korean dialogue unchanged, and a byte-identical round trip.
Automatic readings still need contextual review.

## Previous 2026-11-14 local result

- `./configure --steam && make -j2` succeeded in MSYS2 MINGW32. The resulting
  `src/ponscr.exe` is PE i386; its matching SDK DLL was staged alongside it.
- The seven Python tests passed under `uv run --locked`; the C++ ruby parser
  smoke test also exited successfully.
- A game copy using the converted script and matching engine/DLL opened and
  remained responsive. The installed game was then updated with those same
  three files and launched; its window remained responsive. The current saves
  were backed up before replacement, and no save-file timestamps changed on
  launch.

## Rebuild after branch replay

On 2026-11-14 the replayed EP1–4 ruby commits plus EP5–8 fixes built successfully
again in MSYS2 MINGW32 with `./configure --steam && make -j2`. The output is PE
i386 and the matching Win32 Steam SDK DLL was staged. The rebuilt executable was
installed to the answer game folder after backing up its prior executable, DLL,
and `0.u`. The existing DLL already had the expected SHA256, and `0.u` remained
unchanged. Runtime behavior after this rebuild has not yet been checked.
