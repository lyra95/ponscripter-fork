"""The production C++ layout probe must distinguish same-version sprite tables."""
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

from test_save_offsets import make_save


def complete_save(sprites, tagged=False, arrays=3):
    def ints(*v):
        return struct.pack("<" + "i" * len(v), *v)
    prefix = make_save([(0, 32, ())], sprites=sprites, tagged=tagged)
    prefix = prefix[:-len(b"opaque remaining progress bytes")]
    tail = (ints(0, 0, 0, 0, 0) + b"\0\0" + ints(-1, 0, 0, 0, 0, 0) +
            b"\0" + ints(1, 1) + b"\0" * (100 * 28 + 100 * 24) +
            ints(1, 0, 1) + b"\0" + ints(*range(arrays)) + ints(0) +
            b"\0" * 4 + b"\0\0" + ints(0) +
            (b"\0" + ints(*([0] * 8))) * 256 + ints(*([0] * 6)) +
            ints(1) + b"older page\0" + ints(1) + b"ruby page\0" +
            ints(0, 0, 0, 0, 0, 0, 15, 0))
    return prefix + tail


class SaveLayoutTest(unittest.TestCase):
    def test_full_probe_legacy_and_tagged_counts(self):
        compiler = shutil.which("c++") or shutil.which("g++")
        if compiler is None:
            self.skipTest("C++ compiler required")
        root = Path(__file__).resolve().parents[3]
        harness = r'''
#include "SaveLayout.h"
#include <fstream>
#include <iterator>
#include <vector>
#include <cassert>
#include <cstdlib>
int main(int argc, char** argv) {
    std::ifstream f(argv[1], std::ios::binary);
    std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(f)), {});
    int expected=std::atoi(argv[2]);
    size_t arrays=std::atoi(argv[3]);
    assert(PnsLayout::spriteCount(bytes.data(), bytes.size(), 200, arrays) == expected);
    if (expected) {
        for (size_t n=0; n<bytes.size(); n += bytes.size()/23+1)
            assert(PnsLayout::spriteCount(bytes.data(), n, 200, arrays)==0);
    }
}
'''
        with tempfile.TemporaryDirectory(prefix="yomigana-save-layout-") as d:
            p = Path(d); cpp, exe = p / "probe.cpp", p / "probe"
            cpp.write_text(harness, encoding="utf-8")
            subprocess.run([compiler, "-std=c++11", "-I", str(root / "src"), str(cpp), "-o", str(exe)],
                           check=True, capture_output=True)
            cases = [(complete_save(n, tagged), n, 3)
                     for n in [1000, 1001] for tagged in [False, True]]
            cases += [(complete_save(1000) + b'"description"*', 1000, 3),
                      (complete_save(1001), 0, 0),
                      (complete_save(1001)[:-3], 0, 3)]
            wrong_tag = bytearray(complete_save(1001, True))
            struct.pack_into("<i", wrong_tag, 21, 1000)
            cases.append((wrong_tag, 0, 3))
            for i, (data, expected, arrays) in enumerate(cases):
                fixture = p / (str(i) + ".dat"); fixture.write_bytes(data)
                subprocess.run([str(exe), str(fixture), str(expected), str(arrays)],
                               check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
