#!/usr/bin/env python3
"""
census_feed_brackets.py — READ-ONLY full scan of the pinned ABP app feed for bracket-shape
defects, per FEED verse (edition-upgrade charter §4.6 second bullet; DESIGN_q2_build.md §9.53).
Opens no database. Reads the feed through abp_app_feed (sha + size pin checked first). A verse's
English cells are joined with one space (brackets span cells) and checked as one text.

Classes (one output row per (verse, class)):
  close_without_open   a ']' with no open '['            (the S9 (f) class)
  open_while_open      a '[' while a bracket is already open
  unclosed             a '[' still open at verse end
  digit_outside        an ABP position digit glued to a word OUTSIDE any bracket
  item_without_digit   a bracket whose content does not start with a position digit
                       (load_abp_prose.reorder_bracket would DROP that leading text)
  duplicate_digit      the same position digit twice in one bracket
  digit_gap            a bracket's digits are not exactly 1..n
Output = keys + class only, no English text.

CONTROL (--control): the same detector over committed abp_texts/ (Strong's tags blanked) must
flag the four known source-side malformed brackets (Mat 21:19, 1Ch 22:15, Job 24:19 — the
pre-registered three — and Zec 10:3) as close_without_open. A detector that cannot fire on a
known positive is not trusted on a zero.

Usage:
  python3 scripts/census_feed_brackets.py --control
  python3 scripts/census_feed_brackets.py --out tests/fixtures/edition_upgrade/feed_bracket_census_<date>.tsv
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import abp_app_feed as F  # noqa: E402

CLASSES = ["close_without_open", "open_while_open", "unclosed", "digit_outside",
           "item_without_digit", "duplicate_digit", "digit_gap"]
_LEAK = re.compile(r"(?<!\w)\d+(?=[A-Za-z])")          # load_abp_prose.py:59's leaked-digit shape
_ITEM_DIGIT = re.compile(r"(?:^|(?<=\s))(\d+)(?=\s*[A-Za-z])")
_TAG = re.compile(r"G(?:[\d]+[\d.]*\*?|\*)")            # load_abp_prose.G_NUM_RE
CONTROL_POSITIVES = {("Mat", 21, 19), ("1Ch", 22, 15), ("Job", 24, 19), ("Zec", 10, 3)}


def shapes(text):
    """Set of bracket-shape classes in one verse's English."""
    out, groups, outside = set(), [], []
    cur = None
    for ch in text:
        if ch == "[":
            if cur is not None:
                out.add("open_while_open")
            cur = []
            groups.append(cur)
        elif ch == "]":
            if cur is None:
                out.add("close_without_open")
            cur = None
            outside.append(" ")
        elif cur is not None:
            cur.append(ch)
        else:
            outside.append(ch)
    if cur is not None:
        out.add("unclosed")
    if _LEAK.search("".join(outside)):
        out.add("digit_outside")
    for g in groups:
        c = "".join(g).strip()
        if not c:
            continue
        if not re.match(r"\d", c):
            out.add("item_without_digit")
        ds = [int(x) for x in _ITEM_DIGIT.findall(c)]
        if len(ds) != len(set(ds)):
            out.add("duplicate_digit")
        elif ds and sorted(ds) != list(range(1, len(ds) + 1)):
            out.add("digit_gap")
    return out


def control():
    from build_words_from_abp import abp_source_texts
    hits = {k for k, t in abp_source_texts().items()
            if "close_without_open" in shapes(_TAG.sub(" ", t))}
    missing = CONTROL_POSITIVES - hits
    print(f"control: close_without_open on abp_texts = {len(hits)} verse(s); "
          f"known positives fired {len(CONTROL_POSITIVES - missing)}/{len(CONTROL_POSITIVES)}")
    if missing:
        print(f"CONTROL FAILED: did not fire on {sorted(missing)}")
        return 1
    print("CONTROL: FIRED")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read-only bracket-shape census of the feed.")
    ap.add_argument("--out", help="write the member TSV (keys + class) here")
    ap.add_argument("--control", action="store_true", help="fire on the known abp_texts positives")
    a = ap.parse_args(argv)
    if a.control:
        return control()
    try:
        verses = F.group_verses(F.read_slots())
    except F.FeedError as e:
        print(f"STOP: {e}")
        return 1
    rows, ct = [], Counter()
    for k, slots in verses.items():
        for x in sorted(shapes(" ".join(s["english"] for s in slots)), key=CLASSES.index):
            rows.append((k[0], k[1], k[2], x))
            ct[x] += 1
    print(f"feed verses scanned {len(verses):,} - verses with any bracket defect "
          f"{len({r[:3] for r in rows})}")
    for x in CLASSES:
        print(f"  {x:20} {ct[x]:4}")
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write("book\tchapter\tverse\tclass\n")
            for r in rows:
                f.write("\t".join(str(x) for x in r) + "\n")
        print(f"wrote {len(rows)} rows -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
