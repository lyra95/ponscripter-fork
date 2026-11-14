#!/usr/bin/env python3
"""Package the local engine with its non-system dylibs and ad-hoc signatures."""
from pathlib import Path
import json
import shutil
import subprocess
import argparse

ROOT = Path(__file__).resolve().parents[2]
APP_TEMPLATE = None
BINARY = None
APP = None
PREFIX = Path("/opt/homebrew")
MANIFEST = None
STEAM = ROOT / "src/extlib/src/steam-sdk/redistributable_bin/osx/libsteam_api.dylib"


def run(*args):
    return subprocess.check_output(list(map(str, args)), text=True, stderr=subprocess.PIPE)


def dependencies(path):
    return [line.strip().split(" (", 1)[0] for line in run("otool", "-L", path).splitlines()[1:]]


def resolve(dep, owner):
    if dep.startswith(("/usr/lib/", "/System/")):
        return None
    if dep.endswith("/libsteam_api.dylib"):
        return STEAM.resolve()
    if dep.startswith("@loader_path/"):
        return (owner.parent / dep[len("@loader_path/"):]).resolve()
    if dep.startswith("@rpath/"):
        for base in [owner.parent, PREFIX / "lib"]:
            p = base / dep[len("@rpath/"):]
            if p.exists():
                return p.resolve()
        raise RuntimeError("Unresolved dependency: " + dep)
    p = Path(dep)
    if p.is_absolute() and p.is_file():
        return p.resolve()
    raise RuntimeError("Unresolved dependency: " + dep)


def bundle():
    if APP.exists():
        raise ValueError("Choose a new output app path; existing paths are not overwritten")
    if APP_TEMPLATE.resolve() in APP.resolve().parents:
        raise ValueError("Output must be outside the template app")
    APP.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(APP_TEMPLATE, APP, symlinks=True)
    exe = APP / "Contents/MacOS/umineko4"
    shutil.copy2(BINARY, exe)
    frameworks = APP / "Contents/Frameworks"
    if frameworks.exists():
        shutil.rmtree(frameworks)
    frameworks.mkdir()
    # Homebrew's SDL2 compatibility library opens SDL3 with dlopen(), so it
    # is not listed by otool -L. Include its loader-relative filename too.
    sdl3 = (PREFIX / "lib/libSDL3.dylib").resolve()
    owners, queue = {sdl3.name: sdl3}, [exe, sdl3]
    shutil.copy2(sdl3, frameworks / sdl3.name)
    (frameworks / "libSDL3.dylib").symlink_to(sdl3.name)
    while queue:
        owner = queue.pop()
        dest_owner = owner if owner == exe else frameworks / owner.name
        deps = dependencies(owner)
        for dep in deps:
            source = resolve(dep, owner)
            if source is None or source == owner:
                continue
            if source.name in owners and owners[source.name] != source:
                raise RuntimeError("Conflicting dylib names: " + source.name)
            if source.name not in owners:
                owners[source.name] = source
                shutil.copy2(source, frameworks / source.name)
                queue.append(source)
            run("install_name_tool", "-change", dep,
                "@executable_path/../Frameworks/" + source.name, dest_owner)
        if owner != exe:
            run("install_name_tool", "-id", "@rpath/" + owner.name, dest_owner)
    for name in owners:
        run("codesign", "--force", "--sign", "-", frameworks / name)
    # The old Intel Steam dylib is superseded by the bundled universal library.
    legacy = APP / "Contents/MacOS/libsteam_api.dylib"
    if legacy.exists():
        legacy.unlink()
    # Steam's original bundle has an installscript at its root and is unsigned.
    # Keep that layout; sign the executable and every modified Mach-O directly.
    signed = APP.parent / (APP.stem + "-signed-engine")
    shutil.copy2(exe, signed)
    run("codesign", "--force", "--sign", "-", signed)
    run("codesign", "--verify", "--strict", signed)
    shutil.copy2(signed, exe)
    for p in [exe] + list(frameworks.iterdir()):
        assert all(not d.startswith("/opt/homebrew/") for d in dependencies(p)), p
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(
        {name: str(source) for name, source in owners.items()}, indent=2), encoding="utf-8")
    print("Packaged", APP, "libraries", len(owners),
          "bytes", sum(p.stat().st_size for p in APP.rglob('*') if p.is_file()))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--app-template", type=Path, required=True)
    p.add_argument("--binary", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--library-prefix", type=Path, default=PREFIX)
    args = p.parse_args()
    APP_TEMPLATE, BINARY, APP = args.app_template, args.binary, args.output
    PREFIX, MANIFEST = args.library_prefix, args.manifest
    bundle()
