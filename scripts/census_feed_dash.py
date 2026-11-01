#!/usr/bin/env python3
"""
census_feed_dash.py — READ-ONLY full scan of the pinned ABP app feed's ENGLISH column for
dash shapes (edition-upgrade charter §4.6 dash check; DESIGN_q2_build.md §9.35 (a)).
Opens no database. Reads the feed through abp_app_feed (sha + size pin checked first).

Every '-', '–' (en dash) and '—' (em dash) in an English cell is classified; a hyphen
with a letter or digit on BOTH sides ("four-footed") is an ordinary word hyphen and is
not listed. Shapes:
  end_space_hyphen   cell ends in " -"                (the ABP clause dash, one hyphen lost)
  mid_space_hyphen   " - " inside the cell
  double_hyphen      "--" anywhere
  en_dash / em_dash  "–" / "—" anywhere
  other_hyphen       any other '-' not between two letters/digits (listed, never guessed)
One output row per (cell, shape). Output = keys + shape only, no English text.

Usage:  python3 scripts/census_feed_dash.py --out tests/fixtures/edition_upgrade/feed_dash_census_<date>.tsv
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import abp_app_feed as F  # noqa: E402

SHAPES = ["end_space_hyphen", "mid_space_hyphen", "double_hyphen", "en_dash", "em_dash",
          "other_hyphen"]


def shapes(cell):
    """Set of dash shapes in one English cell."""
    out = set()
    if cell.endswith(" -") and not cell.endswith("--"):
        out.add("end_space_hyphen")
    if " - " in cell:
        out.add("mid_space_hyphen")
    if "--" in cell:
        out.add("double_hyphen")
    if "–" in cell:
        out.add("en_dash")
    if "—" in cell:
        out.add("em_dash")
    body = cell[:-2] if "end_space_hyphen" in out else cell
    body = body.replace(" - ", "   ").replace("--", "  ")
    for m in re.finditer("-", body):
        i = m.start()
        left = body[i - 1] if i > 0 else ""
        right = body[i + 1] if i + 1 < len(body) else ""
        if not (left.isalnum() and right.isalnum()):
            out.add("other_hyphen")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read-only dash-shape census of the feed's English column.")
    ap.add_argument("--out", help="write the member TSV (keys + shape) here")
    a = ap.parse_args(argv)
    try:
        slots = F.read_slots()
    except F.FeedError as e:
        print(f"STOP: {e}")
        return 1
    rows, ct, cells = [], Counter(), Counter()
    for s in slots:
        sh = shapes(s["english"])
        for x in sorted(sh, key=SHAPES.index):
            rows.append((s["abbrev"], s["chapter"], s["verse"], s["slot_index"], x))
            ct[x] += 1
        if sh:
            cells["any"] += 1
            if sh == {"end_space_hyphen"}:
                cells["end_space_hyphen_only"] += 1
    print(f"English cells scanned {len(slots):,} · cells with any dash shape {cells['any']:,}"
          f" · cells whose ONLY shape is end_space_hyphen {cells['end_space_hyphen_only']:,}")
    for x in SHAPES:
        print(f"  {x:18} {ct[x]:6,}")
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write("book\tchapter\tverse\tslot_index\tshape\n")
            for r in rows:
                f.write("\t".join(str(x) for x in r) + "\n")
        print(f"wrote {len(rows):,} rows -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
