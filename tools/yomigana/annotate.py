#!/usr/bin/env python3
"""Annotate only Japanese dialogue, preserving every command and line ending."""
import argparse
import collections
import json
import re
from pathlib import Path

from fugashi import Tagger

KANJI = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff々〆]")
JAPANESE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff々〆ぁ-ゖァ-ヺーゝゞヽヾ、。！？…「」『』（）・　〜～０-９0-9]+")
RUBY = re.compile(r"｜([^｜《》\r\n]+)《([^｜《》\r\n]+)》")
NAMES = {
    "右代宮": "うしろみや", "六軒島": "ろっけんじま",
    "戦人": "ばとら", "朱志香": "じぇしか", "譲治": "じょうじ",
    "真里亞": "まりあ", "真里亜": "まりあ", "紗音": "しゃのん",
    "嘉音": "かのん", "金蔵": "きんぞう", "蔵臼": "くらうす",
    "夏妃": "なつひ", "絵羽": "えば", "秀吉": "ひでよし",
    "留弗夫": "るどるふ", "霧江": "きりえ", "楼座": "ろーざ",
    "郷田": "ごうだ", "源次": "げんじ", "南條": "なんじょう",
    "熊沢": "くまさわ", "熊澤": "くまさわ",
}
NAME_RE = re.compile("(" + "|".join(map(re.escape, sorted(NAMES, key=len, reverse=True))) + ")")


def hiragana(text):
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in text)


def wrap(surface, reading):
    if not reading or reading == "*" or not KANJI.search(surface):
        return surface
    # Keep okurigana on the baseline rather than repeating it in the ruby.
    left = 0
    while left < len(surface) and not KANJI.match(surface[left]):
        left += 1
    right = len(surface)
    while right > left and not KANJI.match(surface[right - 1]):
        right -= 1
    prefix, suffix = surface[:left], surface[right:]
    if prefix and reading.startswith(hiragana(prefix)):
        reading = reading[len(prefix):]
    elif prefix:
        left, prefix = 0, ""
    if suffix and reading.endswith(hiragana(suffix)):
        reading = reading[:-len(suffix)]
    elif suffix:
        right, suffix = len(surface), ""
    if not reading or not re.fullmatch(r"[ぁ-ゖーゝゞ]+", reading):
        return surface
    return prefix + "｜" + surface[left:right] + "《" + reading + "》" + suffix


class Annotator:
    def __init__(self):
        self.tagger = Tagger()
        self.unknown = collections.Counter()
        self.cache = {}

    def words(self, text):
        result, pos = [], 0
        for node in self.tagger(text):
            start = text.find(node.surface, pos)
            assert start >= pos
            result.append(text[pos:start])
            reading = hiragana(node.feature.kana or "")
            annotated = wrap(node.surface, reading)
            if KANJI.search(node.surface) and annotated == node.surface:
                self.unknown[node.surface] += 1
            result.append(annotated)
            pos = start + len(node.surface)
        result.append(text[pos:])
        return "".join(result)

    def japanese(self, text):
        if text in self.cache:
            return self.cache[text]
        pieces = NAME_RE.split(text)
        result = "".join(wrap(p, NAMES[p]) if p in NAMES else self.words(p) for p in pieces if p)
        assert strip_ruby(result) == text
        self.cache[text] = result
        return result

    def dialogue(self, text):
        return JAPANESE.sub(lambda m: self.japanese(m[0]), text)

    def line(self, line):
        if not line.startswith("langjp") or (len(line) > 6 and line[6].isascii() and
                                              (line[6].isalnum() or line[6] == "_")):
            return line
        # Colons separate commands except inside quoted string arguments.
        parts = re.split(r'("[^"\r\n]*")', line[6:])
        out = ["langjp"]
        for i, part in enumerate(parts):
            if i % 2:
                out.append(part)  # Never alter filenames or string arguments.
                continue
            for chunk in re.split("(:)", part):
                s = chunk.lstrip(" \t")
                # Unquoted Japanese text or caret-delimited Ponscripter text.
                if s and (ord(s[0]) >= 128 or s[0] in "^@\\#!'~"):
                    out.append(self.dialogue(chunk))
                else:
                    out.append(chunk)
        result = "".join(out)
        assert strip_ruby(result) == line
        return result


def strip_ruby(text):
    return RUBY.sub(lambda m: m[1], text)


def convert(source, destination, report):
    if source.resolve() == destination.resolve():
        raise ValueError("Choose a separate output file; preserve the original script")
    original = source.read_bytes().decode("utf-8")
    if not re.search(r"(?m)^\*clear_text_and_save_backlog\b", original):
        raise ValueError("This script lacks the required 07th-Mod page-clear callback")
    if RUBY.search(original):
        raise ValueError("Input already contains ruby; use the original backup")
    annotator = Annotator()
    before = original.splitlines(keepends=True)
    after = [annotator.line(line) for line in before]
    directive = "rubyon 17,17:rubyguard *clear_text_and_save_backlog"
    assert original.count("rubyon 17,17") == 1
    for i, line in enumerate(after):
        if line.strip() == "rubyon 17,17":
            after[i] = line.replace("rubyon 17,17", directive)
    converted = "".join(after)
    restored = strip_ruby(converted).replace(directive, "rubyon 17,17", 1)
    assert restored == original, "Lossless round-trip failed"
    assert len(before) == len(after)
    assert all(a == b for a, b in zip(before, after)
               if not a.startswith("langjp") and a.strip() != "rubyon 17,17")
    changed = sum(a != b for a, b in zip(before, after) if a.startswith("langjp"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(converted.encode("utf-8"))
    stats = {
        "source": str(source), "destination": str(destination),
        "lines": len(before), "japanese_lines": sum(l.startswith("langjp") for l in before),
        "changed_japanese_lines": changed, "ruby_groups": len(RUBY.findall(converted)),
        "korean_dialogue_unchanged": True, "round_trip_identical": True,
        "engine_directive_added": directive,
        "other_changes": "Only Japanese dialogue and the single rubyguard directive",
        "dictionary": "fugashi 1.5.2 / unidic-lite 1.0.8; character names overridden",
        "unannotated_tokens": annotator.unknown.most_common(),
        "note": "Automatic readings require review for contextual readings and wordplay.",
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in stats.items() if k != "unannotated_tokens"}, ensure_ascii=True))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("destination", type=Path)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    convert(args.source, args.destination, args.report or args.destination.with_suffix(".report.json"))
