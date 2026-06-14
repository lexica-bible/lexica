#!/usr/bin/env python3
"""
PREVIEW ONLY — reads the ABP source .txt files and shows, for every verse the
"bracket helper" rule would change, the bracket display BEFORE vs AFTER.

No database. No writes to the build. Nothing here ships. It exists purely so we
can eyeball all the affected verses before deciding to touch anything.

The bug: a helper word (May / Let / shall / were ...) that shares the bracketed
verb's single Strong's number gets glued into the same chunk as the verb, so the
'[' swallows it and the source's position number is lost.

The rule: peel the leading text off before the '[' (and trailing text after the
']') into its own word that stays OUTSIDE the bracket, keeping the same Strong's;
the bracket then opens on the verb and uses the source's own number.

Run:  python scripts/preview_bracket_split.py
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ABP_DIRS = [Path("abp_texts/abp_ot_texts"), Path("abp_texts/abp_nt_texts")]
OUT_FILE = Path("scripts/_bracket_split_preview.txt")

_STRONGS_RE = re.compile(r"(G\*|G\d+(?:\.\d+)*)")
_VERSE_RE   = re.compile(r"^\((\w+)\s+(\d+):(\d+)\)\s+(.*)")
_WORD_NUM   = re.compile(r"(?<!\w)\d+")
_LEAD_NUM   = re.compile(r"^\d+")
_SUP        = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def clean_english(text: str) -> str:
    t = text.strip().replace("[", "").replace("]", "")
    return _WORD_NUM.sub("", t).strip()


def lead_num(s: str):
    """Leading ABP position number, reading past a leading '[' (the OLD behaviour)."""
    s2 = re.sub(r"[^\w\s]", "", s.strip().lstrip("[")).strip()
    m = _LEAD_NUM.match(s2)
    return int(m.group()) if m else None


def _chunks(text: str):
    """Split a verse body into (raw_gloss, strongs) chunks, last strongs may be None."""
    parts = _STRONGS_RE.split(text)
    out, i = [], 0
    while i < len(parts) - 1:
        out.append((parts[i], parts[i + 1]))
        i += 2
    if parts and parts[-1].strip():
        out.append((parts[-1], None))
    return out


# ── OLD: each chunk becomes exactly one word (this is what ships today) ──────────
def parse_old(text: str):
    return [(clean_english(raw), strongs, lead_num(raw), "[" in raw, "]" in raw)
            for raw, strongs in _chunks(text)]


# ── NEW: peel a leading helper before '[' / a trailing word after ']' ───────────
def split_token(raw: str, strongs):
    lead = trail = None
    mid = raw
    if "[" in mid:
        i = mid.index("[")
        if re.search(r"[A-Za-z]", mid[:i]):          # real words before the '['
            lead, mid = mid[:i], mid[i:]
    if "]" in mid:
        j = mid.index("]")
        if re.search(r"[A-Za-z]", mid[j + 1:]):      # real words after the ']'
            trail, mid = mid[j + 1:], mid[:j + 1]
    opens, closes, num = "[" in mid, "]" in mid, lead_num(mid)
    out = []
    if lead is not None:
        out.append((clean_english(lead), strongs, None, False, False))   # OUTSIDE, before
    out.append((clean_english(mid), strongs, num, opens, closes))        # the bracket word
    if trail is not None:
        out.append((clean_english(trail), strongs, None, False, False))  # OUTSIDE, after
    return out


def parse_new(text: str):
    words = []
    for raw, strongs in _chunks(text):
        words.extend(split_token(raw, strongs))
    return words


# ── render chip-mode display (source order + bracket markers + numbers) ─────────
def render(words):
    s, inb = "", False
    for eng, _strongs, num, opens, closes in words:
        eng = (eng or "").strip()
        open_here = opens and not inb
        if open_here:
            inb = True
        close_here = closes and inb
        if close_here:
            inb = False
        if not eng:
            continue
        piece = "[" if open_here else ""
        if (inb or close_here) and num is not None:
            piece += str(num).translate(_SUP)
        piece += eng
        if close_here:
            piece += "]"
        s += ("" if (s == "" or s.endswith("[")) else " ") + piece
    return s


def main():
    diffs = []          # (ref, old, new, book)
    by_book = {}
    for d in ABP_DIRS:
        for txt in sorted(d.glob("*.txt")):
            for line in txt.open(encoding="utf-8", errors="replace"):
                m = _VERSE_RE.match(line.strip())
                if not m:
                    continue
                ref = f"{m.group(1)} {m.group(2)}:{m.group(3)}"
                body = m.group(4)
                old, new = render(parse_old(body)), render(parse_new(body))
                if old != new:
                    diffs.append((ref, old, new, txt.stem))
                    by_book[txt.stem] = by_book.get(txt.stem, 0) + 1

    nt_books = {p.stem for p in ABP_DIRS[1].glob("*.txt")}
    nt = sum(1 for _r, _o, _n, b in diffs if b in nt_books)
    ot = len(diffs) - nt

    print(f"Verses the rule changes: {len(diffs)}   (OT {ot}, NT {nt})")
    print("Top books:")
    for b, n in sorted(by_book.items(), key=lambda kv: -kv[1])[:10]:
        print(f"   {n:4d}  {b.replace('abp_', '')}")
    print()

    wanted = ["Psa 21:8", "Psa 2:10", "Psa 17:2", "Psa 37:15",
              "Gen 1:9", "Mat 4:4", "Mat 6:10", "Mat 9:11"]
    shown = set()
    print("=== sample before / after ===")
    for ref, old, new, _b in diffs:
        if ref in wanted and ref not in shown:
            shown.add(ref)
            print(f"\n({ref})")
            print(f"   now:   {old}")
            print(f"   fixed: {new}")
    print(f"\n... full list of all {len(diffs)} written to {OUT_FILE}")

    with OUT_FILE.open("w", encoding="utf-8") as f:
        for ref, old, new, _b in diffs:
            f.write(f"({ref})\n   now:   {old}\n   fixed: {new}\n\n")


if __name__ == "__main__":
    main()
