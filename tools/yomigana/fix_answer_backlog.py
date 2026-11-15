#!/usr/bin/env python3
"""Fix the bilingual answer script's Japanese backlog references on a copy.

The original script reads the Korean page index in two Japanese logsp calls.
Consume two indentation spaces for the added 'jp', preserving every subsequent
byte offset and every line ending so existing save return addresses stay valid.
"""
import argparse
from pathlib import Path
import re


def patch(data):
    start = re.search(rb"(?m)^\*text_cw_lookback2_jp\r?$", data)
    if start is None:
        raise ValueError("Japanese backlog label missing")
    end = re.search(rb"(?m)^\*text_cw_lookback3\r?$", data[start.end():])
    if end is None:
        raise ValueError("Backlog section boundary missing")
    stop = start.end() + end.start()
    lines = data[start.start():stop].splitlines(keepends=True)
    found = []
    changes = 0
    for i, line in enumerate(lines):
        if b"logsp backlogtext," not in line:
            continue
        m = re.match(rb"^( +)(if %advMode (?:==|!=) 0 logsp backlogtext,\$%)(jp)?(backloglook,.*)", line)
        if m is None:
            raise ValueError("Unexpected Japanese backlog display command")
        found.append(m.group(2))
        if m.group(3):
            continue
        if len(m.group(1)) < 2:
            raise ValueError("Insufficient indentation to preserve script offsets")
        lines[i] = line[2:].replace(b"$%backloglook,", b"$%jpbackloglook,", 1)
        assert len(lines[i]) == len(line)
        changes += 1
    if len(found) != 2 or not any(b"==" in x for x in found) or not any(b"!=" in x for x in found):
        raise ValueError("Expected exactly one NVL and one ADV Japanese logsp call")
    result = data[:start.start()] + b"".join(lines) + data[stop:]
    assert len(result) == len(data)
    return result, changes


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--script", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or args.script.resolve() == args.output.resolve():
        p.error("Choose a new output file; the original script is never overwritten")
    result, changes = patch(args.script.read_bytes())
    args.output.write_bytes(result)
    print("Corrected", changes, "Japanese backlog calls; file length and subsequent offsets unchanged")
