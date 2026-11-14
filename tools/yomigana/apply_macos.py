#!/usr/bin/env python3
"""Apply a Mac release to an explicit game directory, or restore its backup."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_stopped(game):
    executable = str(game / "Umineko1to4.app/Contents/MacOS/umineko4")
    procs = subprocess.check_output(["ps", "-axo", "args="], text=True).splitlines()
    if any(line.strip().startswith(executable) for line in procs):
        raise RuntimeError("Quit the game before applying or restoring a patch")


def copy(source, destination):
    if source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    else:
        shutil.copy2(source, destination)


def replace_targets(game, sources):
    """Stage every replacement and roll back if one of the swaps fails."""
    with tempfile.TemporaryDirectory(prefix=".yomigana-stage-", dir=game) as temp:
        stage = Path(temp)
        for name, source in sources.items():
            copy(source, stage / name)
        replaced = []
        try:
            for name in sources:
                os.replace(game / name, stage / ("old-" + name))
                replaced.append(name)
                os.replace(stage / name, game / name)
        except BaseException:
            for name in reversed(replaced):
                dest = game / name
                if dest.is_dir():
                    shutil.rmtree(dest)
                elif dest.exists():
                    dest.unlink()
                os.replace(stage / ("old-" + name), dest)
            raise


def backup_game(game, backup_parent):
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = backup_parent / (game.name + "-" + stamp)
    backup.mkdir(parents=True)
    records = []
    for name in ["Umineko1to4.app", "0.u", "saves"]:
        source = game / name
        if not source.exists():
            continue
        copy(source, backup / name)
        for p in ([source] if source.is_file() else source.rglob("*")):
            if p.is_file() and not p.is_symlink():
                rel = p.relative_to(game)
                digest = sha(p)
                if sha(backup / rel) != digest:
                    raise RuntimeError("Backup verification failed: " + str(rel))
                records.append({"path": str(rel), "sha256": digest})
    (backup / "manifest.json").write_text(json.dumps({
        "game": str(game), "files": records,
        "restore_default": ["Umineko1to4.app", "0.u"],
    }, indent=2), encoding="utf-8")
    return backup


def apply(game, release, backup_parent):
    game, release = game.resolve(), release.resolve()
    ensure_stopped(game)
    app = game / "Umineko1to4.app"
    if not app.is_dir() or not (game / "0.u").is_file():
        raise ValueError("Select the game folder containing Umineko1to4.app and 0.u")
    info = json.loads((release / "BUILD_INFO.json").read_text(encoding="utf-8"))
    if platform.machine() != "arm64":
        raise RuntimeError("This release requires an Apple Silicon Mac")
    version = tuple(map(int, platform.mac_ver()[0].split(".")))
    if version < tuple(map(int, info["minimum_macos"].split("."))):
        raise RuntimeError("This release requires macOS " + info["minimum_macos"] + " or newer")
    for name, digest in info["payload_sha256"].items():
        if sha(release / name) != digest:
            raise RuntimeError("Release checksum mismatch: " + name)
    # Import lazily so restoring a backup needs only the Python standard library.
    from annotate import convert
    from save_offsets import migrate_directory
    with tempfile.TemporaryDirectory(prefix="yomigana-convert-") as temp:
        temp = Path(temp)
        converted = temp / "0.u"
        report = temp / "conversion.report.json"
        convert(game / "0.u", converted, report)
        sources = {"0.u": converted}
        save_report = {}
        if (game / "saves").exists():
            save_report = migrate_directory(game / "0.u", converted, game / "saves", temp / "saves")
            sources["saves"] = temp / "saves"
        ensure_stopped(game)
        backup = backup_game(game, backup_parent)
        staged_app = temp / "Umineko1to4.app"
        copy(app, staged_app)
        shutil.copy2(release / "engine/MacOS/umineko4", staged_app / "Contents/MacOS/umineko4")
        frameworks = staged_app / "Contents/Frameworks"
        if frameworks.exists():
            shutil.rmtree(frameworks)
        copy(release / "engine/Frameworks", frameworks)
        ensure_stopped(game)
        replace_targets(game, {"Umineko1to4.app": staged_app, **sources})
        shutil.copy2(report, backup / "conversion.report.json")
        shutil.copy2(release / "BUILD_INFO.json", backup / "release-build-info.json")
        (backup / "save-offset-migration.json").write_text(json.dumps(save_report, indent=2), encoding="utf-8")
    print("Applied. Current save progress retained; stack offsets relocated. Backup:", backup)


def restore(game, backup, backup_parent):
    game, backup = game.resolve(), backup.resolve()
    ensure_stopped(game)
    manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        if sha(backup / entry["path"]) != entry["sha256"]:
            raise RuntimeError("Backup checksum mismatch: " + entry["path"])
    from save_offsets import migrate_directory
    with tempfile.TemporaryDirectory(prefix="yomigana-restore-") as temp:
        sources = {name: backup / name for name in manifest["restore_default"]}
        save_report = {}
        if (game / "saves").exists():
            save_report = migrate_directory(game / "0.u", backup / "0.u", game / "saves", Path(temp) / "saves")
            sources["saves"] = Path(temp) / "saves"
        ensure_stopped(game)
        recovery = backup_game(game, backup_parent)
        ensure_stopped(game)
        replace_targets(game, sources)
        (recovery / "save-offset-migration.json").write_text(json.dumps(save_report, indent=2), encoding="utf-8")
    print("Engine and script restored; CURRENT saves/ preserved. Previous version:", recovery)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--release-dir", type=Path)
    parser.add_argument("--backup-dir", type=Path)
    parser.add_argument("--restore", type=Path, help="Restore this backup, keeping current saves")
    args = parser.parse_args()
    if platform.system() != "Darwin":
        parser.error("This installer is for macOS; use annotate.py for Windows preparation")
    parent = args.backup_dir or args.game_dir.resolve().parent / "yomigana-backups"
    if args.restore:
        restore(args.game_dir, args.restore, parent)
    else:
        if not args.release_dir:
            parser.error("--release-dir is required when applying a release")
        apply(args.game_dir, args.release_dir, parent)
