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

from fix_answer_backlog import patch as patch_answer_backlog


GUARD = b":rubyguard *clear_text_and_save_backlog"
RUBY = re.compile("｜([^\\r\\n]*?)《([^\\r\\n]*?)》".encode())
SPRITES = 1001  # Current runtime capacity, not necessarily the saved count.
SPRITE_TAG = 0x53505254


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
        # Compare the recognized equal-byte backlog correction symmetrically.
        # Keep raw script bytes and the ruby offset map untouched: no caller or
        # backup is rewritten, and TEXTGOSUB still checks the actual source line.
        try:
            self.canonical, _ = patch_answer_backlog(self.canonical)
        except ValueError:
            # Other scripts/layouts retain the exact command comparison.
            pass

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


def saved_sprite_count(data, legacy_sprites=None):
    """Old PNS 2.7 has no count: require provenance instead of guessing."""
    if not data.startswith(b"PNS\x02\x07"):
        raise ValueError("Save migration supports this fork's PNS 2.7 files only")
    r = Reader(data)
    r.skip(5)
    if r.integer() != 1:
        raise ValueError("Unsupported PNS save header")
    extras = r.integer()
    if not 1 <= extras <= 1024:
        raise ValueError("Invalid PNS extension length")
    values = [r.integer() for _ in range(extras)]
    if extras >= 3 and values[1] == SPRITE_TAG:
        if values[2] not in (1000, 1001):
            raise ValueError("Unsupported tagged sprite count")
        return values[2]
    if legacy_sprites not in (1000, 1001):
        raise ValueError("Untagged PNS 2.7 save: specify --legacy-sprites 1000 or 1001 from its engine provenance")
    return legacy_sprites


def sprite_block_reader(data):
    r = Reader(data)
    r.skip(9)
    extras = r.integer()
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
    return r


def stack_fields(data, border, legacy_sprites=None):
    """Locate only stack fields; all other save bytes remain opaque/unchanged."""
    sprites = saved_sprite_count(data, legacy_sprites)
    r = sprite_block_reader(data)
    for _ in range(sprites):
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
    def __init__(self, source_script, target_script, legacy_sprites=None):
        self.legacy_sprites = legacy_sprites
        self.source, self.target = ScriptOffsets(source_script), ScriptOffsets(target_script)
        if self.source.canonical != self.target.canonical:
            raise ValueError("Scripts differ by more than ruby, rubyguard and the known backlog correction")
        header = self.source.raw.split(b"*define", 1)[0]
        value = re.search(rb"(?:^;|,)value(\d+)", header)
        self.border = int(value[1]) if value else 200
        if not 0 <= self.border <= 4096:
            raise ValueError("Unsupported global variable border")

    def migrate(self, data):
        result, changes = bytearray(data), []
        for position, address, mode in stack_fields(data, self.border, self.legacy_sprites):
            mapped = self.target.from_canonical(self.source.to_canonical(address))
            # Runtime text tokens can expand variables/tags. Do not guess their
            # within-token offsets when the containing source line changed.
            if mode == 2 and self.source.line(address) != self.target.line(mapped):
                raise ValueError("TEXTGOSUB continuation on an annotated line cannot be migrated safely")
            if mapped != address:
                struct.pack_into("<i", result, position, mapped)
                changes.append({"field": position, "before": address, "after": mapped})
        return bytes(result), changes


def resize_sprite_table(data, target, legacy_sprites=None):
    """Restore an older engine only when the extra slot is genuinely empty."""
    current = saved_sprite_count(data, legacy_sprites)
    if target not in (1000, 1001):
        raise ValueError("Unsupported target sprite count")
    if current == target:
        return data
    r = sprite_block_reader(data)
    for _ in range(1000):
        r.string(); r.skip(20)
    boundary = r.pos
    if target == 1000:
        name_start = r.pos; r.string()
        values = [r.integer() for _ in range(5)]
        if (data[name_start:r.pos-20] != b"\0" or values[:2] != [0, 0] or
                values[2] not in (0, 2) or values[3] != 0 or values[4] not in (-1, 0, 256)):
            raise ValueError("Sprite 1000 has saved state; cannot discard it for an older engine")
        result = bytearray(data[:boundary] + data[r.pos:])
    else:
        empty = b"\0" + struct.pack("<iiiii", 0, 0, 2, 0, -1)
        result = bytearray(data[:boundary] + empty + data[boundary:])
    extras = struct.unpack_from("<i", result, 9)[0]
    if extras >= 3 and struct.unpack_from("<i", result, 17)[0] == SPRITE_TAG:
        struct.pack_into("<i", result, 21, target)
    else:
        result[17:17] = struct.pack("<ii", SPRITE_TAG, target)
        struct.pack_into("<i", result, 9, extras + 2)
    return bytes(result)


def migrate_directory(source_script, target_script, saves, output, legacy_sprites=None, target_sprites=None):
    saves, output = Path(saves), Path(output)
    if output.exists() or saves.resolve() in output.resolve().parents:
        raise ValueError("Choose a new output directory outside the original saves")
    migration = SaveMigration(Path(source_script).read_bytes(), Path(target_script).read_bytes(), legacy_sprites)
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
        original = slot.read_bytes()
        converted[slot.name], report[slot.name] = migration.migrate(original)
        if target_sprites is not None:
            count = saved_sprite_count(original, legacy_sprites)
            converted[slot.name] = resize_sprite_table(converted[slot.name], target_sprites, legacy_sprites)
            if count != target_sprites:
                report[slot.name].append({"field": "sprite_count", "before": count, "after": target_sprites})
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
    p.add_argument("--legacy-sprites", type=int, choices=[1000, 1001],
                   help="Saved sprite count for old untagged files; identify the writing engine first")
    p.add_argument("--target-sprites", type=int, choices=[1000, 1001],
                   help="Optional target engine layout; removal rejects any nonempty extra slot")
    args = p.parse_args()
    print(json.dumps(migrate_directory(args.source_script, args.target_script, args.saves, args.output,
                                       args.legacy_sprites, args.target_sprites), indent=2))
