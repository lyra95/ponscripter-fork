// PNS 2.7 layout discrimination. Older engines serialized 1000 sprites,
// newer bases serialized 1001, without changing the save version.
// Probe the entire structure without changing any game/rendering state.
#ifndef YOMIGANA_SAVE_LAYOUT_H
#define YOMIGANA_SAVE_LAYOUT_H
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace PnsLayout {
const int SpriteTag = 0x53505254; // "SPRT", optional Ponscripter extension.

struct Reader {
    const unsigned char* data;
    size_t length, pos;
    bool ok;
    Reader(const unsigned char* d, size_t n) : data(d), length(n), pos(0), ok(true) {}
    void skip(size_t n) {
        if (!ok || n > length - pos) { ok = false; return; }
        pos += n;
    }
    int integer() {
        size_t start = pos;
        skip(4);
        if (!ok) return 0;
        uint32_t v = uint32_t(data[start]) | uint32_t(data[start+1]) << 8 |
                     uint32_t(data[start+2]) << 16 | uint32_t(data[start+3]) << 24;
        return int32_t(v);
    }
    void expect(int n) { if (integer() != n) ok = false; }
    void boolean() { int n = integer(); if (n != 0 && n != 1) ok = false; }
    void string() {
        if (!ok) return;
        const void* end = std::memchr(data + pos, 0, length - pos);
        if (!end) { ok = false; return; }
        pos = static_cast<const unsigned char*>(end) - data + 1;
    }
};

// Returns the tagged count, 0 for an untagged old file, -1 if malformed.
inline int taggedCount(const unsigned char* data, size_t length) {
    if (length < 17 || std::memcmp(data, "PNS\x02\x07", 5)) return -1;
    Reader r(data, length); r.skip(5); r.expect(1);
    int extras = r.integer();
    if (!r.ok || extras < 1 || extras > 1024 || size_t(extras) > (length-r.pos)/4) return -1;
    r.integer(); // default encoding
    if (extras >= 3 && r.integer() == SpriteTag) {
        int count = r.integer();
        return r.ok && (count == 1000 || count == 1001) ? count : -1;
    }
    return 0;
}

inline bool valid(const unsigned char* data, size_t length, int sprites,
                  size_t variables, size_t array_values) {
    int tag = taggedCount(data, length);
    if (tag < 0 || (tag && tag != sprites) || variables > 4096) return false;
    Reader r(data, length); r.skip(5); r.expect(1);
    int extras = r.integer(); r.skip(size_t(extras) * 4);
    r.boolean(); r.boolean(); r.expect(0); r.boolean();
    for (int i=0; i<3; ++i) { int c=r.integer(); if (c<0 || c>255) r.ok=false; }
    r.string(); r.string(); r.skip(8); r.string();
    r.skip(8*4 + 4 + 5*4); r.string(); r.skip(6*4);
    for (int i=0; i<4; ++i) r.string();
    r.skip(12*4);
    for (int i=0; i<sprites && r.ok; ++i) { r.string(); r.skip(5*4); }
    for (size_t i=0; i<variables && r.ok; ++i) { r.skip(4); r.string(); }
    int count = r.integer();
    if (count < -100000 || count > 100000) return false;
    if (count >= 0) r.skip(size_t(count)*4); // Legacy nesting representation.
    else for (int i=0; i < -count && r.ok; ++i) {
        int mode=r.integer();
        if (r.integer() < 0) r.ok=false;
        if (mode==1) r.skip(12);
        else if (mode==2) r.skip(4);
        else if (mode!=0) r.ok=false;
    }
    r.boolean();
    for (int i=0; i<3; ++i) { int c=r.integer(); if (c<0 || c>255) r.ok=false; }
    r.skip(4); // nega
    r.string(); r.string(); r.expect(-1);
    r.boolean(); r.boolean(); r.expect(0); r.boolean(); r.boolean();
    r.string(); r.skip(4); r.expect(1);
    r.skip(100*28 + 100*24); // Bars and printed numbers: fixed-size records.
    r.expect(1); r.expect(0); r.expect(1); r.string();
    if (array_values > (length-r.pos)/4) return false;
    r.skip(array_values*4);
    r.expect(0); r.skip(4); r.string(); r.string(); r.expect(0);
    for (int i=0; i<256 && r.ok; ++i) { r.string(); r.skip(8*4); }
    for (int i=0; i<6; ++i) r.expect(0);
    for (int language=0; language<2 && r.ok; ++language) {
        int pages=r.integer();
        if (pages<0 || pages>100000) return false;
        for (int i=0; i<pages && r.ok; ++i) r.string();
    }
    r.expect(0); r.expect(0); r.skip(4*4); // Human positions and underline.
    if (r.integer()<0 || r.integer()<0) r.ok=false; // Script line/colon position.
    if (!r.ok) return false;
    if (r.pos == length) return true;
    // Optional savegame2 description, appended as "text"*.
    return length-r.pos >= 3 && data[r.pos]=='"' && data[length-2]=='"' && data[length-1]=='*';
}

inline int spriteCount(const unsigned char* data, size_t length,
                       size_t variables, size_t array_values) {
    int tagged=taggedCount(data,length);
    if (tagged<0) return 0;
    if (tagged) return valid(data,length,tagged,variables,array_values) ? tagged : 0;
    bool old=valid(data,length,1000,variables,array_values);
    bool current=valid(data,length,1001,variables,array_values);
    return old != current ? (old ? 1000 : 1001) : 0;
}
}
#endif
