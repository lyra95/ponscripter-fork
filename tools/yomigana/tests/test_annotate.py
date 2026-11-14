import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from annotate import Annotator, strip_ruby


class ConversionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = Annotator()

    def test_inline_voice_and_color(self):
        line = 'langjp:dwave_jp 0, nat_1e6:「夏妃は#ff0000言葉を選ばない。@」\\\r\n'
        result = self.a.line(line)
        self.assertIn('｜夏妃《なつひ》', result)
        self.assertIn('｜選《えら》ばない', result)
        self.assertEqual(strip_ruby(result), line)
        self.assertIn(':dwave_jp 0, nat_1e6:', result)
        self.assertIn('#ff0000', result)

    def test_korean_and_commands_untouched(self):
        for line in ['langen^에바는 日本을 본다.^@\r\n',
                     'langjp:lsp 1,"bmp/日本.png",0,0\r\n',
                     ';langjp 日本\n', 'caption "日本"\n']:
            self.assertEqual(self.a.line(line), line)

    def test_names(self):
        result = self.a.line('langjp　右代宮戦人と朱志香、夏妃、絵羽。@\n')
        for surface, reading in [('右代宮', 'うしろみや'), ('戦人', 'ばとら'),
                                  ('朱志香', 'じぇしか'), ('夏妃', 'なつひ'), ('絵羽', 'えば')]:
            self.assertIn(f'｜{surface}《{reading}》', result)

    def test_line_endings_and_tags(self):
        line = 'langjp^~b~言葉~b~を選ぶ。^/\r\n'
        self.assertEqual(strip_ruby(self.a.line(line)), line)
        for line in ["langjp'「言葉を選ぶ。」@\n", "langjp~ib~^言葉^@\n"]:
            result = self.a.line(line)
            self.assertIn('｜言葉《ことば》', result)
            self.assertEqual(strip_ruby(result), line)


if __name__ == '__main__':
    unittest.main()
