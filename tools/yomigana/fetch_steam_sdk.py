#!/usr/bin/env python3
"""Fetch the pinned Steam headers and optional redistributable for a local build."""
import argparse
import concurrent.futures
import json
from pathlib import Path
import urllib.request

REPOSITORY = "rlabrecque/SteamworksSDK"
REVISION = "df2baabf574a738ef1ea90a7e89339107fc0a279"
BINARIES = {"macos": "osx/libsteam_api.dylib", "win32": "steam_api.dll",
            "win64": "win64/steam_api64.dll",
            "linux64": "linux64/libsteam_api.so"}


def fetch(destination, target):
    url = f"https://api.github.com/repos/{REPOSITORY}/git/trees/{REVISION}?recursive=1"
    with urllib.request.urlopen(url, timeout=30) as response:
        tree = json.load(response)["tree"]
    paths = [x["path"] for x in tree if x["type"] == "blob" and
             x["path"].startswith("public/steam/") and x["path"].endswith((".h", ".hpp"))]
    if target != "headers":
        paths.append("redistributable_bin/" + BINARIES[target])

    def download(path):
        dest = destination / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(
                f"https://raw.githubusercontent.com/{REPOSITORY}/{REVISION}/{path}", timeout=30) as response:
            data = response.read()
        if dest.exists() and dest.read_bytes() != data:
            raise RuntimeError("Existing SDK file differs; choose a fresh destination: " + str(dest))
        dest.write_bytes(data)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(download, paths))
    print(f"Fetched {len(paths)} files from {REPOSITORY}@{REVISION}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--platform", choices=["headers", "macos", "win32", "win64", "linux64"], default="headers")
    p.add_argument("--destination", type=Path,
                   default=Path(__file__).resolve().parents[2] / "src/extlib/src/steam-sdk")
    args = p.parse_args()
    fetch(args.destination, args.platform)
