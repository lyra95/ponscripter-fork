# Linux / Steam Deck development environment

This devcontainer uses Valve's Steam Runtime 3 (Sniper) SDK for Linux x86_64.
It is the same runtime family installed on the Steam Deck inspected on
2026-11-17. The base image is pinned by digest so rebuilds use the same SDK
snapshot. Updating that digest is an explicit toolchain update.

## Open the container on Windows

Requirements:

- Podman 5 or newer, with a running Podman machine.
- VS Code and the Dev Containers extension.
- This repository checked out on a filesystem shared with Podman Machine.

VS Code's Dev Containers extension uses the Docker-compatible command line.
For Podman, set VS Code **Settings → Dev Containers: Docker Path**
(`dev.containers.dockerPath`) to the path of `podman.exe`. Then open this
repository, run **Dev Containers: Reopen in Container**, and wait for the
first setup to finish. On the Windows machine used to validate this setup,
the executable is `C:\Users\<user>\AppData\Local\Programs\Podman\podman.exe`;
use the actual path on each computer.

The first setup builds the repository's tracked SMPEG source into the
container, downloads the pinned Linux Steam API library and headers to
`/opt/steamworks-sdk`, and runs `uv sync --locked` into a container-only
virtual environment. It does not write SDK binaries or Python environments
into the Windows checkout. Build output goes under the ignored `build/`
directory in the checkout.

## Configure and build

From the VS Code terminal inside the container:

```sh
cmake -S . -B build/linux -G Ninja \
  -Wno-dev \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_CXX_STANDARD=11 \
  -DCMAKE_CXX_FLAGS=-Wno-narrowing \
  -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON \
  -DCMAKE_INSTALL_RPATH='$ORIGIN/lib64' \
  -DSMPEG2_PATH=/opt/ponscripter-deps \
  -DSTEAM_SDK_ROOT=/opt/steamworks-sdk \
  -DUSE_CPU_GFX=OFF \
  -DUSE_STEAM=ON
cmake --build build/linux --parallel 2
```

The same settings are prefilled in CMake Tools. `USE_CPU_GFX=OFF` avoids the
old architecture-specific graphics assembly while bringing up this Linux
build. Linux builds use `saves/` beside the game executable, matching the
Steam Deck installation's existing save location and ignoring the script's
legacy `;localsave mysav` directive.

## Package for Steam Deck

The Steam Linux Runtime supplies SDL2, FreeType, Vorbis and the other system
libraries. Bundle the dependencies built or fetched by this container and give
the engine a relative runtime search path:

```sh
mkdir -p build/linux/deck-package/lib64
cp build/linux/src/ponscr build/linux/deck-package/Umineko5to8
cp -L /opt/ponscripter-deps/lib/libsmpeg2-2.0.so.0 build/linux/deck-package/lib64/
cp -L /opt/steamworks-sdk/redistributable_bin/linux64/libsteam_api.so build/linux/deck-package/lib64/
```

Copy `Umineko5to8` and the two libraries into the matching answer game's
installation folder and its `lib64/` directory. The executable searches
`$ORIGIN/lib64`; do not copy Windows `.exe` or `.dll` files over the Linux
engine or libraries. The script loader prefers `0.u`, so a compatible 07th-Mod
Korean script and its matching assets must already be installed.

## Scope and known follow-up work

This prepares a reproducible Linux build environment. The answer engine and
matching libraries have been installed on one Steam Deck; dynamic dependencies
resolve there, but full game runtime behavior has not been verified. Test launch,
audio/video, input, saves, and script language switching on Deck.

The container image is Valve's Steam Runtime Sniper SDK
([image project](https://gitlab.steamos.cloud/steamrt/sniper/sdk)); VS Code's
Podman CLI setting is described in its
[container engine guidance](https://code.visualstudio.com/remote/advancedcontainers/docker-options).
