"""Explicit copied-app test for archived ruby and plain menu sprite layout."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


BASE = """;value2500,modew540@2x@umineko
;gameid RubyBacklogTest
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
langjp｜漢字《かんじ》
gettext $100
textclear
"""
END = """textoff
print 1
getscreenshot 1920,1080
savescreenshot "sprite.bmp"
end
"""


def run(app, fonts, offline_library=None):
    images = {}
    with tempfile.TemporaryDirectory(prefix="yomigana-backlog-") as d:
        game = Path(d)
        shutil.copytree(app, game / "Umineko1to4.app", symlinks=True)
        (game / "fonts").symlink_to(fonts.resolve(), target_is_directory=True)
        env = os.environ.copy()
        if offline_library:
            env["DYLD_INSERT_LIBRARIES"] = str(offline_library.resolve())
        for history in ["ruby", "plain"]:
            prior = "langjpかなかな\ntextclear\n" if history == "plain" else ""
            for kind in ["archived", "menu", "rubyoff"]:
                sprite = 'logsp 0,$100,190,738,#ffffaa\n'
                if kind == "menu":
                    sprite = 'logsp 0,"漢字",190,738,#ffffaa\n'
                if kind == "rubyoff":
                    sprite = "rubyoff\n" + sprite
                (game / "0.u").write_text(BASE + prior + sprite + END, encoding="utf-8")
                result = subprocess.run(
                    [str(game / "Umineko1to4.app/Contents/MacOS/umineko4")],
                    cwd="/", env=env, capture_output=True, timeout=20)
                if result.returncode:
                    raise AssertionError(result.stderr.decode("utf-8", errors="replace"))
                images[kind, history] = (game / "saves/sprite.bmp").read_bytes()
        for kind in ["archived", "menu", "rubyoff"]:
            assert images[kind, "ruby"] == images[kind, "plain"], (
                kind + " layout depends on previous dialogue")
        assert images["archived", "ruby"] != images["menu", "ruby"], "Reading was not rendered"
        assert images["rubyoff", "ruby"] == images["menu", "ruby"], "Ruby-off changed plain layout"
    print("PASS: gettext/logsp readings and plain menu layout are independent of prior dialogue; rubyoff matches plain")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--app", type=Path, required=True)
    p.add_argument("--fonts", type=Path, required=True)
    p.add_argument("--offline-library", type=Path)
    args = p.parse_args()
    run(args.app.resolve(), args.fonts, args.offline_library)
