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
}
