"""Explicit Mac integration test for old-save migration; not unittest discovery.

Run with --app and --fonts, optionally --offline-library (test-only Steam shim).
All scripts/saves are synthetic temporary copies. No installed game is changed.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from annotate import convert
from save_offsets import migrate_directory


SCRIPT = """;value2500,modew540@2x@umineko
;gameid SaveMigrationTest
;localsave mysav
*define
nsa
h_mapfont 0,"fonts/adv/face0.otf"
rubyon 17,17
game
*start
goto *make
*unused
langjp漢字漢字漢字漢字漢字
end
*make
bg black,1
showlangjp
setwindow 95,368,32,17,24,24,0,0,0,1,1,#444444,47,315,912,525
for %7 = 1 to 1
gosub *scene
next
bg white,1
getscreenshot 1920,1080
savescreenshot "returned.bmp"
end
*scene
langjp漢字漢字漢字漢字漢字/
savegame 1
return
*load
loadgame 1
end
*clear_text_and_save_backlog
textclear
return
"""


def run(app, fonts, offline_library=None):
    with tempfile.TemporaryDirectory(prefix="yomigana-save-migration-") as d:
        game = Path(d)
        shutil.copytree(app, game / "Umineko1to4.app", symlinks=True)
        (game / "fonts").symlink_to(fonts.resolve(), target_is_directory=True)
        original, converted = game / "original.u", game / "converted.u"
        original.write_bytes(SCRIPT.replace("\n", "\r\n").encode("utf-8"))
        convert(original, converted, game / "conversion.json")
        env = os.environ.copy()
        if offline_library:
            env["DYLD_INSERT_LIBRARIES"] = str(offline_library.resolve())
        exe = game / "Umineko1to4.app/Contents/MacOS/umineko4"

        def launch(source, loading):
            data = source.read_bytes()
            if loading:
                data = data.replace(b"goto *make", b"goto *load", 1)
            (game / "0.u").write_bytes(data)
            marker = game / "saves/returned.bmp"
            if marker.exists():
                marker.unlink()
            result = subprocess.run([str(exe)], cwd="/", env=env,
                                    capture_output=True, timeout=20)
            if result.returncode or not marker.exists():
                raise AssertionError("Save did not return through gosub/FOR: " +
                                     result.stderr.decode("utf-8", errors="replace"))
            return marker.read_bytes()

        expected = launch(original, False)
        assert launch(original, True) == expected
        for source, target in [(original, converted), (converted, original)]:
            output = game / "relocated"
            report = migrate_directory(source, target, game / "saves", output)
            assert len(report["save1.dat"]) == 2, "Expected gosub and FOR address migration"
            shutil.rmtree(game / "saves")
            output.rename(game / "saves")
            assert launch(target, True) == expected
        print("PASS: original save -> ruby script -> original script; gosub and FOR return correctly")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--app", type=Path, required=True)
    p.add_argument("--fonts", type=Path, required=True)
    p.add_argument("--offline-library", type=Path)
    args = p.parse_args()
    run(args.app.resolve(), args.fonts, args.offline_library)
