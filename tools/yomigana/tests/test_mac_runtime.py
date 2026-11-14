"""Explicit Mac integration test; needs a bundled app and local game fonts.

Not run by unittest discovery. No game scripts, saves or images are distributed.
"""
import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile


SCRIPT = """;value2500,modew540@2x@umineko
;gameid YomiganaRuntimeTest
;localsave mysav
*define
nsa
h_mapfont 0,"fonts/adv/face0.otf"
rubyon 17,17
game
*start
goto *paint
*paint
bg black,1
showlangjp
setwindow 95,368,32,17,24,24,0,0,0,1,1,#444444,47,315,912,525
langjp　｜夏妃《なつひ》と｜絵羽《えば》の｜言葉《ことば》。
savegame 1
textshow:texton:repaint
getscreenshot 1920,1080
savescreenshot "runtime.bmp"
end
"""


def run(app, fonts):
    if platform.system() != "Darwin":
        raise RuntimeError("This integration test requires macOS; Python unit tests are separate")
    with tempfile.TemporaryDirectory(prefix="yomigana-runtime-") as temp:
        game = Path(temp)
        shutil.copytree(app, game / "Umineko1to4.app", symlinks=True)
        (game / "fonts").symlink_to(fonts.resolve(), target_is_directory=True)
        exe = game / "Umineko1to4.app/Contents/MacOS/umineko4"
        env = os.environ.copy()
        env["SteamAppId"] = "406550"
        first = None
        for loading in [False, True]:
            script = SCRIPT.replace("goto *paint", "showlangjp:loadgame 1", 1) if loading else SCRIPT
            (game / "0.u").write_text(script, encoding="utf-8")
            result = subprocess.run([str(exe)], cwd="/", env=env,
                                    capture_output=True, timeout=30)
            if result.returncode:
                raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
            if (game / "mysav").exists():
                raise AssertionError("Default launch followed the legacy mysav header")
            save, image = game / "saves/save1.dat", game / "saves/runtime.bmp"
            if not save.exists() or not image.exists():
                raise AssertionError("Default saves/ path or scripted render failed")
            if first is None:
                first = image.read_bytes()
            elif first != image.read_bytes():
                raise AssertionError("Save/load changed the rendered frame")
        print("PASS: legacy header + no arguments + cwd / uses saves/; restart/load frame matches")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--app", type=Path, required=True)
    p.add_argument("--fonts", type=Path, required=True)
    args = p.parse_args()
    run(args.app.resolve(), args.fonts.resolve())
