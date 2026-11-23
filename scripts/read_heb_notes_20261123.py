#!/usr/bin/env python3
"""Read-only: how many Strong's Hebrew definitions carry a source editor's note (DESIGN 9.258).

Runs the site's own clean_heb_definition over every row of the `bdb` table, lists what it strips,
and lists any definition that still holds a word typical of an editor's note, so another shape of
note cannot hide behind a clean count.

  python3 -u scripts/read_heb_notes_20261123.py --out DIR

Opens the database read-only. Writes only heb_notes.tsv and heb_notes_left.tsv in --out.
Exit 0 = the control passed; 2 = it failed.
"""
import argparse
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from core import clean_heb_definition  # noqa: E402

LOOKS_LIKE_A_NOTE = re.compile(r"(?<![A-Za-z])(?:lemma|corrected|dagesh|typo|misprint|vowel|qamets|qamats|pointing|"
                               r"maqqef|holem|shureq|patah|segol|tsere|hireq|sheva|shewa|consonant|sic|emend\w*)(?![A-Za-z])", re.I)
GLUED = re.compile(r"[֐-׿][A-Za-z]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(ROOT, "bible.db"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    rows = conn.execute("SELECT strongs_id, description FROM bdb ORDER BY strongs_id").fetchall()
    conn.close()
    changed, left = [], []
    for sid, d in rows:
        d = d or ""
        c = clean_heb_definition(d)
        if c != d.strip():
            changed.append((sid, d, c))
        hit = sorted({m.group(0).lower() for m in LOOKS_LIKE_A_NOTE.finditer(c)})
        if GLUED.search(c):
            hit.append("hebrew-glued-to-english")
        if hit:
            left.append((sid, ",".join(hit), c))
    for name, data in (("heb_notes.tsv", changed), ("heb_notes_left.tsv", left)):
        with open(os.path.join(a.out, name), "w", encoding="utf-8", newline="\n") as f:
            for x in data:
                f.write("\t".join(str(v).replace("\t", " ").replace("\n", " ") for v in x) + "\n")
    ok = any(s == "H5113" and "corrected" not in c and "corrected" in d for s, d, c in changed)
    print(f"Strong's Hebrew entries: {len(rows):,}")
    print(f"  control, H5113 is cleaned: {'PASS' if ok else 'FAILED'}")
    print(f"entries with an editor's note stripped: {len(changed)}")
    print(f"entries still holding a note-like word, to read: {len(left)}")
    print(f"HEBREW NOTES CONTROL: {'PASS' if ok else 'FAILED - do not trust the count'}")
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
