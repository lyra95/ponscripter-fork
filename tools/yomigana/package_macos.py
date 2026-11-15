#!/usr/bin/env python3
"""Archive a verified Mac app's engine and libraries, excluding game-owned assets."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def run(*args):
    return subprocess.check_output(list(map(str, args)), text=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(app, output, version, library_sources=None):
    name = f"yomigana-{version}-macos-arm64"
    stage, archive = output / name, output / (name + ".zip")
    if stage.exists() or archive.exists():
        raise ValueError("Release output already exists; choose a fresh output directory")
    stage.mkdir(parents=True)
    engine = stage / "engine"
    (engine / "MacOS").mkdir(parents=True)
    shutil.copy2(app / "Contents/MacOS/umineko4", engine / "MacOS/umineko4")
    shutil.copytree(app / "Contents/Frameworks", engine / "Frameworks", symlinks=True)
    if not (engine / "Frameworks/libSDL3.dylib").exists():
        raise RuntimeError("Missing SDL3 loader-relative alias")
    minimums, payload, architectures = [], {}, set()
    for path in engine.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        arches = run("lipo", "-archs", path).strip().split()
        if "arm64" not in arches:
            raise RuntimeError("Library lacks arm64: " + path.name)
        architectures.update(arches)
        run("codesign", "--verify", "--strict", path)
        load = run("otool", "-l", path)
        minimums.extend(re.findall(r"\bminos\s+([\d.]+)", load))
        deps = run("otool", "-L", path)
        if "/opt/homebrew/" in deps or str(ROOT) in deps:
            raise RuntimeError("Unbundled local dependency: " + path.name)
        payload[path.relative_to(stage).as_posix()] = sha(path)
    minimum = max(minimums, key=lambda s: tuple(map(int, s.split("."))))
    portable = stage / "tools/yomigana"
    portable.mkdir(parents=True)
    for filename in ["annotate.py", "apply_macos.py", "save_offsets.py",
                     "fix_answer_backlog.py", "requirements.txt"]:
        shutil.copy2(ROOT / "tools/yomigana" / filename, portable / filename)
    shutil.copy2(ROOT / "COPYING", stage / "COPYING")
    shutil.copy2(ROOT / "docs/YOMIGANA.md", stage / "README.md")
    libraries = []
    if library_sources:
        licenses = stage / "licenses"
        for filename, source in json.loads(library_sources.read_text()).items():
            source = Path(source)
            parts = source.parts
            if "Cellar" not in parts:
                libraries.append({"library": filename, "provider": "Steamworks redistributable"})
                continue
            i = parts.index("Cellar")
            formula, revision = parts[i + 1:i + 3]
            libraries.append({"library": filename, "provider": formula, "version": revision})
            cellar = Path(*parts[:i + 3])
            for license_path in cellar.rglob("*"):
                if not license_path.is_file() or license_path.is_symlink():
                    continue
                basename = license_path.name.lower()
                if any(t in basename for t in ["copying", "license", "copyright", "ftl.txt", "gpl.txt"]):
                    dest = licenses / formula / license_path.relative_to(cellar)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(license_path, dest)
    info = {"version": version, "platform": "macOS", "architecture": "arm64",
            "minimum_macos": minimum, "signing": "ad-hoc (not notarized)",
            "source_repository": "https://github.com/lyra95/ponscripter-fork",
            "source_commit": run("git", "-C", ROOT, "rev-parse", "HEAD").strip(),
            "engine_src_tree": run("git", "-C", ROOT, "rev-parse", "HEAD:src").strip(),
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "payload_sha256": payload, "libraries": libraries,
            "game_data_included": False, "windows_build_included": False}
    (stage / "BUILD_INFO.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    (stage / "THIRD_PARTY_NOTICES.txt").write_text(
        "Engine: GPL-2.0-or-later; see COPYING and the source repository in BUILD_INFO.json.\n"
        "Bundled library providers/versions are listed in BUILD_INFO.json. License files\n"
        "provided by their installed packages are collected in licenses/.\n"
        "libsteam_api.dylib is the Steamworks SDK redistributable, copyright Valve.\n"
        "Steam SDK source reference: rlabrecque/SteamworksSDK@df2baabf574a738ef1ea90a7e89339107fc0a279.\n",
        encoding="utf-8")
    # ditto preserves the SDL3 symlink and executable permissions for Finder.
    run("ditto", "-c", "-k", "--keepParent", stage, archive)
    (output / "SHA256SUMS.txt").write_text(sha(archive) + "  " + archive.name + "\n", encoding="utf-8")
    print(json.dumps({"archive": str(archive), "minimum_macos": minimum,
                      "sha256": sha(archive), "bytes": archive.stat().st_size}))
    return archive


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--app", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--version", required=True)
    p.add_argument("--library-sources", type=Path)
    args = p.parse_args()
    package(args.app, args.output, args.version, args.library_sources)
