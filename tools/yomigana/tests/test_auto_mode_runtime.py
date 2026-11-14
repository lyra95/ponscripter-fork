"""Explicit copied-app regression for base-character auto-mode timing."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


BASE = """;value2500,modew540@2x@umineko
;gameid RubyAutoModeTest
;localsave mysav
*define
nsa
h_mapfont 0,"fonts/adv/face0.otf"
rubyon 17,17
game
*start
bg black,1
showlangjp
setwindow 95,368,32,17,24,24,0,0,0,1,1,#444444,47,315,912,525
"""


def run(app, fonts, offline_library=None):
    with tempfile.TemporaryDirectory(prefix="yomigana-auto-mode-") as d:
        game = Path(d)
        shutil.copytree(app, game / "Umineko1to4.app", symlinks=True)
        (game / "fonts").symlink_to(fonts.resolve(), target_is_directory=True)
        env = os.environ.copy()
        if offline_library:
            env["DYLD_INSERT_LIBRARIES"] = str(offline_library.resolve())
        for automatic_time, lower, upper in [(-100, 950, 1500), (200, 180, 700)]:
            for ruby in [False, True]:
                body = "漢字" * 5
                if ruby:
                    body = "｜" + body + "《かんじ》"
                script = (BASE + f"automode_time {automatic_time}\nmenu_automode\nresettimer\n"
                          + "langjp" + body + "@\ngettimer %10\n"
                          + "getscreenshot 1920,1080\n"
                          + f'if %10 >= {lower} && %10 < {upper} savescreenshot "timing-ok.bmp"\nend\n')
                (game / "0.u").write_text(script, encoding="utf-8")
                marker = game / "saves/timing-ok.bmp"
                if marker.exists():
                    marker.unlink()
                result = subprocess.run(
                    [str(game / "Umineko1to4.app/Contents/MacOS/umineko4")],
                    cwd="/", env=env, capture_output=True, timeout=20)
                if result.returncode or not marker.exists():
                    raise AssertionError(f"Auto timing failed for {automatic_time}, ruby={ruby}: " +
                                         result.stderr.decode("utf-8", errors="replace"))
    print("PASS: ten base characters wait about 1s with or without ruby; fixed 200ms mode unchanged")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--app", type=Path, required=True)
    p.add_argument("--fonts", type=Path, required=True)
    p.add_argument("--offline-library", type=Path)
    args = p.parse_args()
    run(args.app.resolve(), args.fonts, args.offline_library)
