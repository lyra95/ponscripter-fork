import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fix_answer_backlog import patch


class AnswerBacklogTest(unittest.TestCase):
    def script(self, ending=b"\r\n"):
        return ending.join([
            b"*text_cw_lookback2", b"   if %advMode == 0 logsp backlogtext,$%backloglook,274,32,#FFFFaa",
            b"*text_cw_lookback2_jp", b"itoa $Free1,%jpbackloglook",
            b"   if %advMode == 0 logsp backlogtext,$%backloglook,274,32,#FFFFaa",
            b"   if %advMode != 0 logsp backlogtext,$%backloglook,190,736,#FFFFaa",
            b"   *backlogbtn_jp", b"btnwait2 %BtnRes", b"*text_cw_lookback3", b"return", b""])

    def test_both_languages_offsets_and_idempotence(self):
        for ending in [b"\r\n", b"\n"]:
            before = self.script(ending)
            after, changes = patch(before)
            self.assertEqual(changes, 2)
            self.assertEqual(len(before), len(after))
            for old, new in zip(before.splitlines(keepends=True), after.splitlines(keepends=True)):
                self.assertEqual(len(old), len(new))
                if old != new:
                    self.assertEqual(new, old[2:].replace(b"$%backloglook,", b"$%jpbackloglook,"))
            self.assertEqual(before.split(b"*text_cw_lookback2_jp")[0],
                             after.split(b"*text_cw_lookback2_jp")[0])
            self.assertEqual(patch(after), (after, 0))

    def test_reject_unrecognized_layout(self):
        for data in [b"", self.script().replace(b"   if", b" if"),
                     self.script().replace(b"logsp backlogtext,", b"logsp othertext,")]:
            with self.assertRaises(ValueError):
                patch(data)


if __name__ == "__main__":
    unittest.main()
