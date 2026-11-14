// UTF-8 ruby notation: fullwidth vertical bar + base + 《reading》.
// Independent of SDL so parsing can be tested without opening a window.
#ifndef YOMIGANA_RUBY_H
#define YOMIGANA_RUBY_H
#include <string>
#include <cstring>

struct RubySpan {
    std::string base, reading;
    int bytes;
    RubySpan() : bytes(0) {}
};

inline RubySpan parseRuby(const char* text)
{
    RubySpan span;
    if (std::strncmp(text, "\xef\xbd\x9c", 3)) return span;
    const char* start = text + 3;
    const char* separator = NULL;
    for (const char* p = start; *p && p - start < 1024; ++p) {
        unsigned char c = *p;
        if (c < 0x20 || c == '@' || c == '\\' || c == '^' ||
            c == ':' || c == '#' || c == '!' || c == ';') return RubySpan();
        if (!std::strncmp(p, "\xe3\x80\x8a", 3)) {
            if (separator || p == start) return RubySpan();
            separator = p;
            p += 2;
        } else if (!std::strncmp(p, "\xe3\x80\x8b", 3)) {
            if (!separator || p == separator + 3) return RubySpan();
            span.base.assign(start, separator - start);
            span.reading.assign(separator + 3, p - separator - 3);
            span.bytes = int(p + 3 - text);
            return span;
        } else if (!std::strncmp(p, "\xef\xbd\x9c", 3)) return RubySpan();
    }
    return span;
}
// Layout belongs to a dialogue/page, not to an individual @ wait segment.
inline bool containsRuby(const char* text, bool stop_at_newline = false)
{
    for (const char* p = text; *p; ++p) {
        if (stop_at_newline && *p == '\n') break;
        if (parseRuby(p).bytes) return true;
    }
    return false;
}

inline bool scriptLineContainsRuby(const char* current, const char* script_begin)
{
    while (current > script_begin && current[-1] != '\n') --current;
    return containsRuby(current, true);
}
#endif
