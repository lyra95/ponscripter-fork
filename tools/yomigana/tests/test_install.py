import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apply_macos import apply, restore, replace_targets


class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / "Steam Library/steamapps/common/Umineko"
        self.app = self.game / "Umineko1to4.app"
        (self.app / "Contents/MacOS").mkdir(parents=True)
        (self.app / "Contents/MacOS/umineko4").write_bytes(b"original engine")
        (self.game / "saves").mkdir()
        (self.game / "saves/save1.dat").write_bytes(b"current progress")
        self.original = (";localsave mysav\r\n*define\r\nrubyon 17,17\r\n"
                         "game\r\n*start\r\nlangjp 夏妃の言葉。@\r\n"
                         "langen^한글 대사는 유지.^@\r\n"
                         "*clear_text_and_save_backlog\r\nreturn\r\n").encode("utf-8")
        (self.game / "0.u").write_bytes(self.original)
        self.release = self.root / "release"
        for name, data in {"engine/MacOS/umineko4": b"new engine",
                           "engine/Frameworks/library.dylib": b"library"}.items():
            p = self.release / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        info = {"minimum_macos": "26.0", "payload_sha256": {
            p.relative_to(self.release).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in self.release.rglob("*") if p.is_file()}}
        (self.release / "BUILD_INFO.json").write_text(json.dumps(info), encoding="utf-8")

    def test_apply_restore_and_keep_new_progress(self):
        with patch("apply_macos.ensure_stopped"), patch("apply_macos.platform.machine", return_value="arm64"), \
                patch("apply_macos.platform.mac_ver", return_value=("26.0", (), "")):
            apply(self.game, self.release, self.root / "backups")
            self.assertEqual((self.app / "Contents/MacOS/umineko4").read_bytes(), b"new engine")
            self.assertIn("｜夏妃《なつひ》".encode(), (self.game / "0.u").read_bytes())
            self.assertIn("langen^한글 대사는 유지.^@\r\n".encode(), (self.game / "0.u").read_bytes())
            backup = next((self.root / "backups").iterdir())
            self.assertEqual((backup / "0.u").read_bytes(), self.original)
            (self.game / "saves/save1.dat").write_bytes(b"newer progress")
            restore(self.game, backup, self.root / "recoveries")
            self.assertEqual((self.game / "0.u").read_bytes(), self.original)
            self.assertEqual((self.game / "saves/save1.dat").read_bytes(), b"newer progress")

    def test_corrupt_release_does_not_modify_game(self):
        (self.release / "engine/MacOS/umineko4").write_bytes(b"corrupt")
        with patch("apply_macos.ensure_stopped"), patch("apply_macos.platform.machine", return_value="arm64"), \
                patch("apply_macos.platform.mac_ver", return_value=("26.0", (), "")):
            with self.assertRaisesRegex(RuntimeError, "checksum"):
                apply(self.game, self.release, self.root / "backups")
        self.assertEqual((self.game / "0.u").read_bytes(), self.original)
        self.assertFalse((self.root / "backups").exists())

    def test_partial_swap_rolls_back(self):
        import os
        source = self.root / "new.u"
        source.write_bytes(b"new script")
        original_replace = os.replace
        failed = False

        def fail_once(src, dest):
            nonlocal failed
            if Path(src).name == "0.u" and Path(dest) == self.game / "0.u" and not failed:
                failed = True
                raise OSError("simulated write failure")
            return original_replace(src, dest)

        with patch("apply_macos.os.replace", side_effect=fail_once):
            with self.assertRaises(OSError):
                replace_targets(self.game, {"0.u": source})
        self.assertEqual((self.game / "0.u").read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()
