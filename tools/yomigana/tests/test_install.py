import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apply_macos import apply, restore, replace_targets
from test_save_offsets import make_save
from save_offsets import ScriptOffsets, stack_fields


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
        self.current_save = make_save()
        (self.game / "saves/save1.dat").write_bytes(self.current_save)
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
            newer_save = self.current_save + b"newer progress"
            (self.game / "saves/save1.dat").write_bytes(newer_save)
            restore(self.game, backup, self.root / "recoveries")
            self.assertEqual((self.game / "0.u").read_bytes(), self.original)
            self.assertEqual((self.game / "saves/save1.dat").read_bytes(), newer_save)

    def test_corrupt_release_does_not_modify_game(self):
        (self.release / "engine/MacOS/umineko4").write_bytes(b"corrupt")
        with patch("apply_macos.ensure_stopped"), patch("apply_macos.platform.machine", return_value="arm64"), \
                patch("apply_macos.platform.mac_ver", return_value=("26.0", (), "")):
            with self.assertRaisesRegex(RuntimeError, "checksum"):
                apply(self.game, self.release, self.root / "backups")
        self.assertEqual((self.game / "0.u").read_bytes(), self.original)
        self.assertFalse((self.root / "backups").exists())

    def test_apply_and_restore_relocate_current_callstack(self):
        address = ScriptOffsets(self.original).raw.index(b"langen")
        original_save = make_save([(0, address, ())])
        slot = self.game / "saves/save1.dat"
        slot.write_bytes(original_save)
        with patch("apply_macos.ensure_stopped"), patch("apply_macos.platform.machine", return_value="arm64"), \
                patch("apply_macos.platform.mac_ver", return_value=("26.0", (), "")):
            apply(self.game, self.release, self.root / "backups")
            target = ScriptOffsets((self.game / "0.u").read_bytes())
            mapped = stack_fields(slot.read_bytes(), 200)[0][1]
            self.assertEqual(target.raw[mapped:mapped + 6], b"langen")
            self.assertNotEqual(mapped, address)
            # Current progress after installation must survive restoring the
            # original script, while its stack address moves back.
            slot.write_bytes(slot.read_bytes() + b"newer progress")
            backup = next((self.root / "backups").iterdir())
            restore(self.game, backup, self.root / "recoveries")
            self.assertEqual(slot.read_bytes(), original_save + b"newer progress")

    def test_unsupported_save_aborts_before_replacing_app_or_script(self):
        (self.game / "saves/save1.dat").write_bytes(b"unsupported save")
        with patch("apply_macos.ensure_stopped"), patch("apply_macos.platform.machine", return_value="arm64"), \
                patch("apply_macos.platform.mac_ver", return_value=("26.0", (), "")):
            with self.assertRaisesRegex(ValueError, "PNS 2.7"):
                apply(self.game, self.release, self.root / "backups")
        self.assertEqual((self.game / "0.u").read_bytes(), self.original)
        self.assertEqual((self.app / "Contents/MacOS/umineko4").read_bytes(), b"original engine")

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
