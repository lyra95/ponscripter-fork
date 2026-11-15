from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from save_offsets import (SaveMigration, ScriptOffsets, migrate_directory,
                          stack_fields, SPRITE_TAG, saved_sprite_count, resize_sprite_table,
                          sprite_block_reader)


def make_save(entries=(), border=200, sprites=1001, tagged=True):
    def ints(*values):
        return struct.pack("<" + "i" * len(values), *values)
    extension = ints(3, 0, SPRITE_TAG, sprites) if tagged else ints(1, 0)
    data = (b"PNS\x02\x07" + ints(1) + extension + ints(*([0] * 7)) + b"\0\0" +
            ints(0, 0) + b"\0" + ints(*([0] * 8)) + b"\0" * 4 +
            ints(*([0] * 5)) + b"\0" + ints(*([0] * 6)) + b"\0" * 4 +
            ints(*([0] * 12)) + (b"\0" + ints(0, 0, 0, 0, 0)) * sprites +
            (ints(0) + b"\0") * border + ints(-len(entries)))
    for mode, address, extra in entries:
        data += ints(mode, address, *extra)
    return data + b"opaque remaining progress bytes"


class SaveOffsetTest(unittest.TestCase):
    def setUp(self):
        self.original = "\ufeff;value200,modew540\r\n*define\r\nrubyon 17,17\r\ngame\r\n*start\r\nlangjp漢字\r\ngosub *scene\r\nend\r\n*scene\r\nreturn\r\n".encode()
        self.annotated = self.original.replace(b"rubyon 17,17", b"rubyon 17,17:rubyguard *clear_text_and_save_backlog").replace("langjp漢字".encode(), "langjp｜漢字《かんじ》".encode())

    def test_gosub_and_for_offsets_round_trip_without_touching_other_bytes(self):
        source, target = ScriptOffsets(self.original), ScriptOffsets(self.annotated)
        address = source.raw.index(b"end\n")
        data = make_save([(0, address, ()), (1, address, (3, 10, 1))])
        migration = SaveMigration(self.original, self.annotated)
        result, changes = migration.migrate(data)
        self.assertEqual(len(changes), 2)
        for position, mapped, mode in stack_fields(result, 200):
            self.assertEqual(target.raw[mapped:mapped + 4], b"end\n")
        changed = {i for c in changes for i in range(c["field"], c["field"] + 4)}
        self.assertTrue(all(a == b for i, (a, b) in enumerate(zip(data, result)) if i not in changed))
        self.assertEqual(SaveMigration(self.annotated, self.original).migrate(result)[0], data)

    def test_textgosub_on_unchanged_line_is_supported(self):
        address = ScriptOffsets(self.original).raw.index(b"end\n")
        result, changes = SaveMigration(self.original, self.annotated).migrate(make_save([(2, address, (17,))]))
        self.assertEqual(len(changes), 1)
        pos = stack_fields(result, 200)[0][0]
        self.assertEqual(struct.unpack_from("<i", result, pos + 4)[0], 17)

    def test_ambiguous_textgosub_and_non_ruby_edits_are_rejected(self):
        address = ScriptOffsets(self.original).raw.index("漢字".encode())
        with self.assertRaisesRegex(ValueError, "TEXTGOSUB"):
            SaveMigration(self.original, self.annotated).migrate(make_save([(2, address, (3,))]))
        with self.assertRaisesRegex(ValueError, "more than ruby"):
            SaveMigration(self.original, self.annotated.replace(b"gosub", b"goto"))

    def test_ruby_boundaries_map_to_whole_notation(self):
        a = ScriptOffsets("漢字次".encode())
        b = ScriptOffsets("｜漢字《かんじ》次".encode())
        self.assertEqual(b.from_canonical(0), 0)
        self.assertEqual(b.raw[b.from_canonical(len("漢字".encode())):], "次\n".encode())
        self.assertEqual(b.to_canonical(b.raw.index("次".encode())), a.raw.index("次".encode()))

    def test_copy_preserves_progress_and_rejects_all_before_output(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); saves = p / "saves"; saves.mkdir()
            old, new = p / "old.u", p / "new.u"
            old.write_bytes(self.original); new.write_bytes(self.annotated)
            data = make_save([(0, ScriptOffsets(self.original).raw.index(b"end\n"), ())])
            (saves / "save1.dat").write_bytes(data)
            (saves / "global.sav").write_bytes(b"current progress")
            (saves / "sav").mkdir(); (saves / "sav/save1.dat").write_bytes(data[5:])
            report = migrate_directory(old, new, saves, p / "converted")
            self.assertTrue(report["save1.dat"])
            self.assertEqual((saves / "save1.dat").read_bytes(), data)
            self.assertEqual((p / "converted/global.sav").read_bytes(), b"current progress")
            self.assertEqual((p / "converted/sav/save1.dat").read_bytes(), (p / "converted/save1.dat").read_bytes()[5:])
            (saves / "save2.dat").write_bytes(b"unknown format")
            with self.assertRaises(ValueError):
                migrate_directory(old, new, saves, p / "rejected")
            self.assertFalse((p / "rejected").exists())

    def test_truncated_saves_and_slot_symlinks_are_rejected(self):
        migration = SaveMigration(self.original, self.annotated)
        with self.assertRaises(ValueError):
            migration.migrate(make_save()[:100])
        with tempfile.TemporaryDirectory() as d:
            p = Path(d); saves = p / "saves"; saves.mkdir()
            old, new = p / "old.u", p / "new.u"
            old.write_bytes(self.original); new.write_bytes(self.annotated)
            outside = p / "outside.dat"; outside.write_bytes(make_save())
            try:
                (saves / "save1.dat").symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("Symbolic links unavailable")
            with self.assertRaisesRegex(ValueError, "symbolic"):
                migrate_directory(old, new, saves, p / "output")
            self.assertEqual(outside.read_bytes(), make_save())

    def test_old_sprite_counts_require_explicit_provenance(self):
        address = ScriptOffsets(self.original).raw.index(b"end\n")
        for count in [1000, 1001]:
            data = make_save([(0, address, ())], sprites=count, tagged=False)
            with self.assertRaisesRegex(ValueError, "legacy-sprites"):
                SaveMigration(self.original, self.annotated).migrate(data)
            result, changes = SaveMigration(self.original, self.annotated, count).migrate(data)
            self.assertTrue(changes)
            mapped = stack_fields(result, 200, count)[0][1]
            self.assertEqual(ScriptOffsets(self.annotated).raw[mapped:mapped+4], b"end\n")

    def test_resize_preserves_variables_and_stack_and_rejects_nonempty_extra(self):
        address = ScriptOffsets(self.original).raw.index(b"end\n")
        original = make_save([(0, address, ())], sprites=1000, tagged=False)
        expanded = resize_sprite_table(original, 1001, 1000)
        self.assertEqual(saved_sprite_count(expanded), 1001)
        self.assertEqual(stack_fields(expanded, 200)[0][1], address)
        restored = resize_sprite_table(expanded, 1000)
        self.assertEqual(saved_sprite_count(restored), 1000)
        # Only the optional descriptor differs from the original after a round trip.
        self.assertEqual(restored[:9] + struct.pack("<i", 1) + restored[13:17] + restored[25:], original)
        r = sprite_block_reader(expanded)
        for _ in range(1000):
            r.string(); r.skip(20)
        nonempty = expanded[:r.pos] + b"image.png" + expanded[r.pos:]
        with self.assertRaisesRegex(ValueError, "cannot discard"):
            resize_sprite_table(nonempty, 1000)


if __name__ == "__main__":
    unittest.main()
