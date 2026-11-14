#include "Ruby.h"
#include <cassert>
int main() {
    RubySpan r = parseRuby(u8"｜夏妃《なつひ》に");
    assert(r.base == u8"夏妃" && r.reading == u8"なつひ");
    assert(r.bytes == int(std::strlen(u8"｜夏妃《なつひ》")));
    const char* invalid[] = {"", "|", u8"｜夏妃", u8"｜《なつひ》",
        u8"｜夏妃《》", u8"｜夏妃《なつひ\n》", u8"｜言葉@《ことば》",
        u8"｜夏妃《なつひ《なつひ》", u8"｜夏妃｜夏妃《なつひ》"};
    for (auto s : invalid) assert(!parseRuby(s).bytes);

    // A wait/voice boundary must not change the layout within a dialogue line.
    const char* script = u8"plain menu\nlangjp:plain@:voice 1:｜文字《もじ》@:voice 2:plain\\\nnext menu\n";
    const char* ruby = std::strstr(script, u8"｜文字");
    const char* first = std::strstr(script, "plain@");
    const char* last = std::strstr(script, "plain\\");
    assert(scriptLineContainsRuby(first, script));
    assert(scriptLineContainsRuby(ruby, script));
    assert(scriptLineContainsRuby(last, script));
    assert(!scriptLineContainsRuby(script, script));
    assert(!scriptLineContainsRuby(std::strstr(script, "next menu"), script));
    // Restoring a page must find ruby after a stored newline, too.
    assert(containsRuby(u8"plain\n｜文字《もじ》\nplain"));
    assert(!containsRuby(u8"plain\n｜文字《もじ》", true));
    assert(!containsRuby("plain menu@plain"));
}
