"""Explicit copied-app load/re-save regression for 1000/1001 PNS 2.7 files."""
import argparse
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from save_offsets import saved_sprite_count, resize_sprite_table


SCRIPT = """;value2500,modew540@2x@umineko
;gameid SpriteLayoutTest
;localsave mysav
*define
nsa
h_mapfont 0,"fonts/adv/face0.otf"
rubyon 17,17
game
*start
showlangjp
goto *make
*make
bg black,1
setwindow 95,368,32,17,24,24,0,0,0,1,1,#444444,47,315,912,525
mov %58,123
mov $483,"｜漢字《かんじ》"
for %7 = 1 to 1
gosub *scene
next
logsp 0,$483,190,738,#ffffaa
textoff
print 1
getscreenshot 1920,1080
if %58 == 123 && $483 == "｜漢字《かんじ》" savescreenshot "variables-ok.bmp"
end
*scene
langjp｜言葉《ことば》/
savegame 1
return
*load
loadgame 1
end
"""


def untag(data):
    assert struct.unpack_from("<i", data, 9)[0] == 3
    return data[:9] + struct.pack("<i", 1) + data[13:17] + data[25:]


def run(app, fonts, offline_library=None):
    with tempfile.TemporaryDirectory(prefix="yomigana-sprite-layout-") as d:
        game = Path(d)
        shutil.copytree(app, game / "Umineko1to4.app", symlinks=True)
        (game / "fonts").symlink_to(fonts.resolve(), target_is_directory=True)
        env = os.environ.copy()
        if offline_library:
            env["DYLD_INSERT_LIBRARIES"] = str(offline_library.resolve())
        exe = game / "Umineko1to4.app/Contents/MacOS/umineko4"

        def launch(loading):
            script = SCRIPT.replace("goto *make", "goto *load", 1) if loading else SCRIPT
            (game / "0.u").write_text(script, encoding="utf-8")
            marker = game / "saves/variables-ok.bmp"
            if marker.exists():
                marker.unlink()
            r = subprocess.run([str(exe)], cwd="/", env=env, capture_output=True, timeout=20)
            if r.returncode or not marker.exists():
                raise AssertionError(r.stderr.decode("utf-8", errors="replace"))
            return marker.read_bytes()

        expected = launch(False)
        slot = game / "saves/save1.dat"
        current = slot.read_bytes()
        assert saved_sprite_count(current) == 1001
        old = resize_sprite_table(current, 1000)
        for name, data in [("tagged1001", current), ("untagged1001", untag(current)),
                           ("tagged1000", old), ("untagged1000", untag(old))]:
            slot.write_bytes(data)
            assert launch(True) == expected, name
            assert saved_sprite_count(slot.read_bytes()) == 1001, "Re-save lacks explicit format"
        print("PASS: 1000/1001 tagged and untagged saves preserve variables, backlog pixels and gosub/FOR; re-save is tagged")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--app", type=Path, required=True)
    p.add_argument("--fonts", type=Path, required=True)
    p.add_argument("--offline-library", type=Path)
    args = p.parse_args()
    run(args.app.resolve(), args.fonts, args.offline_library)
