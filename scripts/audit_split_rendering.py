#!/usr/bin/env python3
"""Read-only: one Greek word carrying two word rows ("split renderings", TODO; JP ruled a counting
defect 10/25). The helper audit sees the shape with the first piece outside the bracket. This sees
the other shape, both pieces inside it, which had no detector (454 of the 628 listed on 10/25).

A pair = two neighbouring rows, the same full Strong's number, each with a bracket and a Greek
position, the same printed Greek form on both, and different English.

It also re-reads the 10/25 figures on today's table: how many of the 628 still have 2+ rows, and
whether any printed form in abp_surface is English typed in the Greek font.

  python3 -u scripts/audit_split_rendering.py --out DIR

Opens the database read-only. Writes only pairs.tsv and list_628_today.tsv in --out.
Exit 0 = every control passed; 2 = a control failed, do not trust the counts.
"""
import argparse
import csv
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from audit_abp_app_vs_surface import english_font  # noqa: E402

DB = os.path.join(os.path.dirname(HERE), "bible.db")
FROZEN = os.path.join(os.path.dirname(HERE), "tests", "fixtures", "split_rendering", "list_628_20261025.tsv")

# The ten both-inside verses read row by row on 10/25 (CENSUS_abp_concordance_diff.md section 5).
CONTROLS = ("Gen 24:41", "Deu 4:10", "Ezr 6:3", "Est 2:17", "Psa 115:17", "Jer 49:14", "2Co 2:11",
            "Joh 11:50", "Mar 14:4", "Rom 15:2")
FONT_CONTROLS = ("δαγγερ και", "- Φορ τηε ενδ.λἡμμα")
FONT_QUIET = ("και", "το", "Δαν", "πνεύμα")

_PUNCT = re.compile(r"[^\w\s]")


def norm(s):
    return _PUNCT.sub("", s or "").lower().strip()


def real(st):
    return bool(st) and st not in ("*", "")


def pairs_in_verse(rows):
    """rows = [(position, english, strongs, greek_pos, bracket_id, form)] in position order.
    -> [(i, j, kind)]; kind is 'same-form', or 'form-missing' when a row has no printed form."""
    out = []
    for i in range(len(rows) - 1):
        a, b = rows[i], rows[i + 1]
        if b[0] != a[0] + 1 or not real(a[2]) or a[2] != b[2]:
            continue
        if a[3] is None or b[3] is None or a[4] is None or b[4] is None:
            continue
        if not norm(a[1]) or not norm(b[1]) or norm(a[1]) == norm(b[1]):
            continue
        fa, fb = (a[5] or "").strip(), (b[5] or "").strip()
        if fa and fb:
            if fa == fb:
                out.append((i, i + 1, "same-form"))
        else:
            out.append((i, i + 1, "form-missing"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB)
    ap.add_argument("--out", required=True)
    ap.add_argument("--frozen", default=FROZEN)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    forms = {(v, p): f for v, p, f in conn.execute("SELECT verse_id, position, form FROM abp_surface")}
    verses, ref = defaultdict(list), {}
    for vid, book, ch, vs, pos, eng, st, gpos, bid in conn.execute(
            "SELECT v.id, v.book, v.chapter, v.verse, w.position, w.english, w.strongs, w.greek_pos, w.bracket_id"
            " FROM words w JOIN verses v ON v.id = w.verse_id ORDER BY v.id, w.position"):
        verses[vid].append((pos, eng, st, gpos, bid, forms.get((vid, pos))))
        ref[vid] = f"{book} {ch}:{vs}"
    print(f"word rows: {sum(len(r) for r in verses.values()):,}; printed forms: {len(forms):,}", flush=True)

    found, kinds, lines = set(), Counter(), []
    for vid, rows in verses.items():
        for i, j, kind in pairs_in_verse(rows):
            a, b = rows[i], rows[j]
            kinds[kind] += 1
            found.add((ref[vid], a[2]))
            lines.append((ref[vid], a[2], a[0], a[1], b[1], a[5] or "", b[5] or "", kind))
    with open(os.path.join(args.out, "pairs.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("verse\tstrongs\tposition\tenglish_1\tenglish_2\tform_1\tform_2\tkind\n")
        for x in lines:
            f.write("\t".join(str(c).replace("\t", " ") for c in x) + "\n")
    print(f"both-inside pairs today: {len(lines):,} ({dict(kinds)}) in {len({x[0] for x in lines}):,} verses", flush=True)

    bad = 0
    found_refs = {r for r, _s in found}
    miss = [c for c in CONTROLS if c not in found_refs]
    print(f"  control, the ten verses read on 10/25: {len(CONTROLS) - len(miss)} of {len(CONTROLS)} fire; missing {miss}")
    bad += bool(miss)

    live = defaultdict(Counter)
    for vid, rows in verses.items():
        for r in rows:
            if real(r[2]):
                live[ref[vid]][r[2]] += 1
    with open(args.frozen, encoding="utf-8", newline="") as f:
        frozen = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    tally = Counter()
    with open(os.path.join(args.out, "list_628_today.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("verse\tstrongs\tshape_1025\trows_today\tdetector_fires\n")
        for x in frozen:
            k = f"{x['book']} {x['chapter']}:{x['verse']}"
            n = live[k][x["strongs"]]
            hit = (k, x["strongs"]) in found
            state = "still 2+" if n >= 2 else ("now 1" if n == 1 else "now 0")
            tally[(x["shape"], state)] += 1
            if x["shape"] == "both-inside-bracket" and n >= 2:
                tally["inside, still 2+, detector fires" if hit else "inside, still 2+, detector misses"] += 1
            f.write(f"{k}\t{x['strongs']}\t{x['shape']}\t{n}\t{'yes' if hit else 'no'}\n")
    print(f"the 10/25 list: {len(frozen)} entries")
    for k in sorted(tally, key=str):
        print(f"  {k}: {tally[k]}")
    listed = {(f"{x['book']} {x['chapter']}:{x['verse']}", x["strongs"]) for x in frozen}
    print(f"pairs today that are not on the 10/25 list: {len(found - listed):,}", flush=True)

    font_ok = all(english_font(s) for s in FONT_CONTROLS) and not any(english_font(s) for s in FONT_QUIET)
    print(f"  control, English-in-Greek check: {'PASS' if font_ok else 'FAILED'}")
    bad += not font_ok
    hits = [(k, f) for k, f in forms.items() if english_font(f)]
    print(f"printed forms on the site that are English in the Greek font: {len(hits)}")
    id_ref = {k: v for k, v in ref.items()}
    for (vid, pos), f in hits[:40]:
        print(f"  {id_ref.get(vid, vid)} @{pos}: {f}")
    conn.close()
    print(f"SPLIT AUDIT CONTROLS: {'PASS' if not bad else 'FAILED - do not trust the counts'}")
    sys.exit(2 if bad else 0)


if __name__ == "__main__":
    main()
