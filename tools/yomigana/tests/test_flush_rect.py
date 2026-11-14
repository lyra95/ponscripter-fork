"""Exercise the real flushDirect method with deterministic SDL/simul stubs."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


class FlushRectangleTest(unittest.TestCase):
    def test_animation_expansion_and_upload_bounds(self):
        compiler = shutil.which("g++") or shutil.which("c++")
        if compiler is None:
            self.skipTest("C++ compiler required")
        root = Path(__file__).resolve().parents[3]
        source = (root / "src/PonscripterLabel.cpp").read_text(encoding="utf-8")
        method = re.search(
            r"void PonscripterLabel::flushDirect\(.*?\n\}\n", source, re.S
        ).group(0)
        harness = r'''
#include <cassert>
#include <cstdio>
#include <cstdint>
typedef uint64_t Uint64;
struct SDL_Rect { int x, y, w, h; };
struct Format { int BytesPerPixel; };
struct SDL_Surface { int w, h, pitch; void* pixels; Format* format; };
static SDL_Rect uploaded;
static int uploads;
static const void* upload_pixels;
static Uint64 SDL_GetPerformanceCounter() { return 0; }
static const char* SDL_GetError() { return "stub"; }
static int SDL_UpdateTexture(void*, SDL_Rect* r, const void* pixels, int pitch) {
    assert(pitch == 400);
    uploaded = *r; upload_pixels = pixels; ++uploads; return 0;
}
class PonscripterLabel {
public:
    SDL_Surface* accumulation_surface;
    void* screen_tex = nullptr;
    FILE* renderTimesFile = nullptr;
    float perfMultiplier = 1;
    unsigned long long frameNo = 0;
    SDL_Rect dirty_rect, refreshed;
    bool expand = false;
    int refreshes = 0;
    void refreshSurface(SDL_Surface*, SDL_Rect* r, int mode) {
        ++refreshes;
        if (mode && expand) dirty_rect = {0, 0, 100, 80};
        refreshed = *r;
    }
    void flushDirect(SDL_Rect&, int, bool = true);
};
'''
        checks = r'''
static bool equal(SDL_Rect a, SDL_Rect b) {
    return a.x==b.x && a.y==b.y && a.w==b.w && a.h==b.h;
}
int main() {
    char pixels[400*80] = {};
    Format format = {4}; SDL_Surface surface = {100,80,400,pixels,&format};
    PonscripterLabel p; p.accumulation_surface = &surface;
    // A simul tick expands the dirty bounding box during refresh.
    p.expand = true; p.dirty_rect = {10,20,4,5};
    p.flushDirect(p.dirty_rect, 1);
    assert(equal(p.refreshed, {0,0,100,80}));
    assert(equal(uploaded, {0,0,100,80}) && upload_pixels == pixels);
    // Even an empty incoming region can become visible during refresh.
    p.dirty_rect = {0,0,0,0}; int before = uploads;
    p.flushDirect(p.dirty_rect, 1); assert(uploads == before+1);
    p.expand = false;
    SDL_Rect r = {-10,-5,30,25}; p.flushDirect(r, 0);
    assert(equal(uploaded, {0,0,20,20}) && upload_pixels == pixels);
    r = {90,70,30,25}; p.flushDirect(r, 0);
    assert(equal(uploaded, {90,70,10,10}));
    assert(upload_pixels == pixels+70*400+90*4);
    r = {-10,0,5,5}; before = uploads; int calls = p.refreshes;
    p.flushDirect(r, 1);
    assert(uploads == before && p.refreshes == calls+1);
    r = {0,0,10,10}; p.flushDirect(r, 1, false);
    assert(uploads == before);
    // Arithmetic at the positive int limit must not wrap into the surface.
    r = {2147483640,0,100,10}; p.flushDirect(r, 0);
    assert(uploads == before);
    p.accumulation_surface = nullptr; p.flushDirect(r, 1);
}
'''
        with tempfile.TemporaryDirectory(prefix="yomigana-flush-test-") as tmp:
            cpp = Path(tmp) / "flush.cpp"
            exe = Path(tmp) / "flush-test.exe"
            cpp.write_text(harness + method + checks, encoding="utf-8")
            subprocess.run([compiler, "-std=c++11", str(cpp), "-o", str(exe)],
                           check=True, capture_output=True)
            subprocess.run([str(exe)], check=True, capture_output=True)
