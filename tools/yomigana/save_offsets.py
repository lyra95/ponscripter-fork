"""Relocate PNS 2.7 stack addresses when adding/removing ruby annotations.

Source saves must belong to source_script. Never guess the script of a legacy
save: the format records absolute offsets but no script identity. Outputs are
separate copies; the installer backs up originals before swapping them in.
"""
import argparse
from bisect import bisect_right
import json
from pathlib import Path
import re
import shutil
import struct


GUARD = b":rubyguard *clear_text_and_save_backlog"
RUBY = re.compile("｜([^\\r\\n]*?)《([^\\r\\n]*?)》".encode())
SPRITES = 1001  # PonscripterLabel.h, this fork's PNS 2.7 layout.


class ScriptOffsets:
    def __init__(self, data):
        # Match ScriptHandler::readScriptSub: UTF-8 BOM removed, CR/CRLF -> LF,
        # followed by the extra newline appended for this one script file.
        self.raw = data.removeprefix(b"\xef\xbb\xbf").replace(b"\r\n", b"\n").replace(b"\r", b"\n") + b"\n"
        self.raw.decode("utf-8")
        self.spans, self.raw_starts, self.canonical_starts = [], [], []
        pieces, previous, canonical = [], 0, 0
        edits = []
        for m in RUBY.finditer(self.raw):
            if (any(c in m[1].decode("utf-8") for c in "｜《》") or
                    not re.fullmatch(r"[ぁ-ゖーゝゞ]+", m[2].decode("utf-8"))):
                raise ValueError("Unsupported ruby notation in script")
            edits.append((m.start(), m.end(), m.start(1), m.end(1)))
        guards = [m for m in re.finditer(re.escape(GUARD), self.raw)]
        if len(guards) > 1:
            raise ValueError("Multiple rubyguard directives; unsupported script")
        edits += [(m.start(), m.end(), m.end(), m.end()) for m in guards]
        for start, end, base_start, base_end in sorted(edits):
            if start < previous:
                raise ValueError("Overlapping ruby edits")
            pieces.append(self.raw[previous:start])
            canonical += start - previous
            self.spans.append((start, end, base_start, base_end, canonical))
            self.raw_starts.append(start)
            self.canonical_starts.append(canonical)
            pieces.append(self.raw[base_start:base_end])
            canonical += base_end - base_start
            previous = end
        pieces.append(self.raw[previous:])
        self.canonical = b"".join(pieces)

    def to_canonical(self, offset):
        if not 0 <= offset < len(self.raw):
            raise ValueError("Saved stack address is outside the source script")
        i = bisect_right(self.raw_starts, offset) - 1
        if i < 0:
            return offset
        start, end, base_start, base_end, canonical = self.spans[i]
        if offset < end:
            return canonical + min(max(offset - base_start, 0), base_end - base_start)
        return canonical + base_end - base_start + offset - end

    def from_canonical(self, offset):
        i = bisect_right(self.canonical_starts, offset) - 1
        if i < 0:
            return offset
        start, end, base_start, base_end, canonical = self.spans[i]
        delta = offset - canonical
        if base_end > base_start and delta == 0:
            return start  # Resume at the ruby marker, not inside its base.
        if delta < base_end - base_start:
            return base_start + delta
        return end + delta - (base_end - base_start)

    def line(self, offset):
        return self.raw[self.raw.rfind(b"\n", 0, offset) + 1:self.raw.find(b"\n", offset)]


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def skip(self, size):
        if size < 0 or self.pos + size > len(self.data):
            raise ValueError("Truncated or unsupported PNS save")
        self.pos += size

    def integer(self):
        self.skip(4)
        return struct.unpack_from("<i", self.data, self.pos - 4)[0]

    def string(self):
        end = self.data.find(b"\0", self.pos)
        if end < 0:
            raise ValueError("Unterminated string in PNS save")
        self.pos = end + 1


def stack_fields(data, border):
    """Locate only stack fields; all other save bytes remain opaque/unchanged."""
    if not data.startswith(b"PNS\x02\x07"):
        raise ValueError("Save migration supports this fork's PNS 2.7 files only")
    r = Reader(data)
    r.skip(5)
    if r.integer() != 1:
        raise ValueError("Unsupported PNS save header")
    extras = r.integer()
    if not 1 <= extras <= 1024:
        raise ValueError("Invalid PNS extension length")
    r.skip(extras * 4 + 7 * 4)
    r.string()  # Two cursor image names.
    r.string()
    r.skip(8)  # Window effect and duration.
    r.string()
    r.skip(8 * 4 + 4 + 5 * 4)  # Font, color, wait time, window rectangle.
    r.string()
    r.skip(6 * 4)  # Cursor flags/positions.
    for _ in range(4):
        r.string()  # Background + three standing images.
    r.skip(12 * 4)  # Standing positions and reserved fields.
    for _ in range(SPRITES):
        r.string()
        r.skip(5 * 4)
    for _ in range(border):
        r.skip(4)
        r.string()
    count = r.integer()
    if not -100000 <= count <= 0:
        raise ValueError("Unsupported legacy or invalid nesting stack")
    fields = []
    for _ in range(-count):
        mode = r.integer()
        position = r.pos
        address = r.integer()
        if mode == 0:
            pass
        elif mode == 1:
            r.skip(12)  # FOR variable, end, step.
        elif mode == 2:
            r.skip(4)  # TEXTGOSUB buffer offset.
        else:
            raise ValueError("Unknown PNS nesting mode")
        fields.append((position, address, mode))
    return fields


class SaveMigration:
    def __init__(self, source_script, target_script):
        self.source, self.target = ScriptOffsets(source_script), ScriptOffsets(target_script)
        if self.source.canonical != self.target.canonical:
            raise ValueError("Scripts differ by more than ruby and the rubyguard directive")
        header = self.source.raw.split(b"*define", 1)[0]
        value = re.search(rb"(?:^;|,)value(\d+)", header)
        self.border = int(value[1]) if value else 200
        if not 0 <= self.border <= 4096:
            raise ValueError("Unsupported global variable border")

    def migrate(self, data):
        result, changes = bytearray(data), []
        for position, address, mode in stack_fields(data, self.border):
            mapped = self.target.from_canonical(self.source.to_canonical(address))
            # Runtime text tokens can expand variables/tags. Do not guess their
            # within-token offsets when the containing source line changed.
            if mode == 2 and self.source.line(address) != self.target.line(mapped):
                raise ValueError("TEXTGOSUB continuation on an annotated line cannot be migrated safely")
            if mapped != address:
                struct.pack_into("<i", result, position, mapped)
                changes.append({"field": position, "before": address, "after": mapped})
        return bytes(result), changes


def migrate_directory(source_script, target_script, saves, output):
    saves, output = Path(saves), Path(output)
    if output.exists() or saves.resolve() in output.resolve().parents:
        raise ValueError("Choose a new output directory outside the original saves")
    migration = SaveMigration(Path(source_script).read_bytes(), Path(target_script).read_bytes())
    # Validate every slot before creating output. Source files are never changed.
    for slot in saves.rglob("save*.dat"):
        if (re.fullmatch(r"save\d+\.dat", slot.name) and
                slot.parent not in (saves, saves / "sav")):
            raise ValueError("Nested save slots require selecting their actual save directory")
    converted, report = {}, {}
    for slot in sorted(saves.glob("save*.dat")):
        if not re.fullmatch(r"save\d+\.dat", slot.name):
            continue
        if slot.is_symlink():
            raise ValueError("Save slots must not be symbolic links")
        converted[slot.name], report[slot.name] = migration.migrate(slot.read_bytes())
        secondary = saves / "sav" / slot.name
        if secondary.exists() and ((saves / "sav").is_symlink() or secondary.is_symlink() or
                                   secondary.read_bytes() != slot.read_bytes()[5:]):
            raise ValueError("Secondary save differs from primary; refusing to replace it")
    shutil.copytree(saves, output, symlinks=True)
    for name, data in converted.items():
        if report[name]:
            (output / name).write_bytes(data)
    # Legacy sav/saveN.dat files omit the magic header. Keep paired copies in
    # sync; never leave stale raw offsets in this engine's secondary save path.
    for name, data in converted.items():
        secondary = output / "sav" / name
        if secondary.exists() and report[name]:
            secondary.write_bytes(data[5:])
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-script", type=Path, required=True)
    p.add_argument("--target-script", type=Path, required=True)
    p.add_argument("--saves", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(migrate_directory(args.source_script, args.target_script, args.saves, args.output), indent=2))
