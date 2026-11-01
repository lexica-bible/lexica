#!/usr/bin/env python3
"""
census_feed_markup.py — READ-ONLY full scan of the pinned ABP app feed's ENGLISH column for
markup and other non-English content (DESIGN_q2_build.md §9.37; charter §4.6). Opens no
database. Reads the feed through abp_app_feed (sha + size pin checked first).

Marker classes (one output row per (cell, class); a cell can carry several):
  backslash:<Code>   a typesetting code "\\Gr", "\\Scap", "\\dagger", "\\cvnote", "\\Engsevenbd" …
                     — the code is named in the class
  backslash:&        "\\&"
  backslash:'        "\\'" (accent code inside a transliteration)
  backslash:bare     any other backslash
  strongs_translit   the cell STARTS with a Strong's number (3+ digits, dash/dot parts allowed)
                     then a space — the number and its Latin transliteration typed into the
                     English ("2532 kaiAnd")
  camel_glue         a lower-case letter directly followed by a capital ("manifestationsUrim")
                     — two renderings glued together
  double_period      ".." anywhere ("Satanthe adversary..") — the app's glued-note marker
  non_ascii:U+XXXX   any non-ASCII character, named by code point
  greek_letter       any Greek letter (charter §4.6 expects 0)
Output = keys + class only, no English text.

Usage:  python3 scripts/census_feed_markup.py --out tests/fixtures/edition_upgrade/feed_markup_census_<date>.tsv
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import abp_app_feed as F  # noqa: E402

BS = "\\"
_BS_CODE = re.compile(re.escape(BS) + r"([A-Za-z]+)")
_STRONGS_LEAD = re.compile(r"^\d{3,}(?:[-.]\d+)*\s")
_CAMEL = re.compile(r"[a-z][A-Z]")
_GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")


def classes(cell):
    """Set of marker classes in one English cell."""
    out = set()
    i = 0
    while True:
        i = cell.find(BS, i)
        if i < 0:
            break
        m = _BS_CODE.match(cell, i)
        nxt = cell[i + 1] if i + 1 < len(cell) else ""
        if m:
            out.add("backslash:" + m.group(1))
            i = m.end()
            continue
        if nxt == "&":
            out.add("backslash:&")
        elif nxt == "'":
            out.add("backslash:'")
        else:
            out.add("backslash:bare")
        i += 1
    if _STRONGS_LEAD.match(cell):
        out.add("strongs_translit")
    if _CAMEL.search(cell):
        out.add("camel_glue")
    if ".." in cell:
        out.add("double_period")
    if _GREEK.search(cell):
        out.add("greek_letter")
    for ch in cell:
        if not ch.isascii() and not _GREEK.match(ch):
            out.add(f"non_ascii:U+{ord(ch):04X}")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read-only markup census of the feed's English column.")
    ap.add_argument("--out", help="write the member TSV (keys + class) here")
    a = ap.parse_args(argv)
    try:
        slots = F.read_slots()
    except F.FeedError as e:
        print(f"STOP: {e}")
        return 1
    rows, ct, cells, verses = [], Counter(), 0, set()
    for s in slots:
        cl = classes(s["english"])
        if not cl:
            continue
        cells += 1
        verses.add((s["abbrev"], s["chapter"], s["verse"]))
        for x in sorted(cl):
            rows.append((s["abbrev"], s["chapter"], s["verse"], s["slot_index"], x))
            ct[x] += 1
    print(f"English cells scanned {len(slots):,} - cells with any marker {cells} - verses {len(verses)}")
    for x in sorted(ct):
        print(f"  {x:22} {ct[x]:5}")
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write("book\tchapter\tverse\tslot_index\tclass\n")
            for r in rows:
                f.write("\t".join(str(x) for x in r) + "\n")
        print(f"wrote {len(rows)} rows -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
