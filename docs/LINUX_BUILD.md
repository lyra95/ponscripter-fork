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
  -DSMPEG2_PATH=/opt/ponscripter-deps \
  -DSTEAM_SDK_ROOT=/opt/steamworks-sdk \
  -DUSE_CPU_GFX=OFF \
  -DUSE_STEAM=ON
cmake --build build/linux --parallel 2
```

The same settings are prefilled in CMake Tools. `USE_CPU_GFX=OFF` avoids the
old architecture-specific graphics assembly while bringing up this Linux
build. The game source is still the same source; this container does not
apply Linux engine fixes.

## Scope and known follow-up work

This prepares a reproducible Linux build environment and verifies CMake/build
tool availability. It does not install or modify anything on the Steam Deck,
package an engine for the game folders, or verify game runtime behavior.
Before using a Linux engine on Deck, remaining work includes fixing and
reviewing Linux-specific save paths, packaging the matching `libsmpeg2` and
Steam runtime dependencies, then testing launch, audio/video, input, saves,
and script language switching on Deck. The Windows-style save path in the
current engine remains unchanged by this setup.

The container image is Valve's Steam Runtime Sniper SDK
([image project](https://gitlab.steamos.cloud/steamrt/sniper/sdk)); VS Code's
Podman CLI setting is described in its
[container engine guidance](https://code.visualstudio.com/remote/advancedcontainers/docker-options).
