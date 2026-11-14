"""Compile the production counter with deterministic encoding/ligature stubs."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


class CharacterCountTest(unittest.TestCase):
    def test_base_characters_not_reading_or_span_count(self):
        compiler = shutil.which("c++") or shutil.which("g++")
        if not compiler:
            self.skipTest("C++ compiler required")
        root = Path(__file__).resolve().parents[3]
        source = (root / "src/PonscripterLabel_text.cpp").read_text(encoding="utf-8")
        method = re.search(r"int PonscripterLabel::textCharacterCount\(.*?\n\}\n", source, re.S).group(0)
        harness = r'''
#include "Ruby.h"
#include <cassert>
struct Fontinfo {};
struct Encoding {
    int NextCharSizeWithLigatures(const char* p, const Fontinfo*) {
        if (p[0]=='f' && p[1]=='i') return 2; // One existing display ligature.
        unsigned char c=*p;
        return c<128 ? 1 : c<224 ? 2 : c<240 ? 3 : 4;
    }
};
static Encoding encoding;
static Encoding* file_encoding = &encoding;
class PonscripterLabel {
public:
    Fontinfo sentence_font;
    int textCharacterCount(const char*);
};
'''
        checks = r'''
int main() {
    PonscripterLabel p;
    assert(p.textCharacterCount(u8"漢字") == 1); // Ordinary output consumes one glyph.
    assert(p.textCharacterCount(u8"｜漢字《かんじ》") == 2);
    assert(p.textCharacterCount(u8"｜漢字漢字漢字漢字漢字《かんじ》") == 10);
    assert(p.textCharacterCount(u8"｜漢《とてもながいよみかた》") == 1);
    assert(p.textCharacterCount(u8"｜fi漢《かん》") == 2); // Preserve ligature counting.
}
'''
        with tempfile.TemporaryDirectory(prefix="yomigana-character-count-") as d:
            cpp, exe = Path(d) / "count.cpp", Path(d) / "count"
            cpp.write_text(harness + method + checks, encoding="utf-8")
            subprocess.run([compiler, "-std=c++11", "-I", str(root / "src"), str(cpp), "-o", str(exe)],
                           check=True, capture_output=True)
            subprocess.run([str(exe)], check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
