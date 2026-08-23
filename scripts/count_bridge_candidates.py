#!/usr/bin/env python3
"""
count_bridge_candidates.py — READ-ONLY pre-registration instrument for the form
lane's bridge rule (CHARTER_form_table_rebuild.md, 2026-08-13).

WHAT: before the amended backfill_pn_surface.py dry-run runs, derive the number
it must land on. Takes the refused-slot dump of the UNAMENDED pass (the 2,543
rows in ~/db_evidence/formlane_refused.tsv) and re-pairs ONLY those verses with
the production pair_verse + load_scrape (imported — never a copy), with and
without the bridge. Reports how many of the dumped refusals the rule converts
to adds, how the remaining refusals re-classify (bridge-fail vs bridge-ambiguous
vs no-match), and which of the 172 arrivals are covered — all by member.

The full dry-run must then report "bridge adds" EQUAL to this script's figure;
any other number is a STOP (the instrument and the pass share one engine, so a
difference means the dump or the data moved, not the rule).

Run on PA (reads bible_formlane.db / bh_scrape.db / the dump; writes nothing
but the optional member list):
  PYTHONIOENCODING=utf-8 python3 ~/bible-db/scripts/count_bridge_candidates.py \
      ~/bible-db/bible_formlane.db --bh ~/bible-db/bh_scrape.db \
      --refused ~/db_evidence/formlane_refused.tsv \
      --arrivals ~/db_evidence/formlane_arrivals.tsv \
      --out ~/db_evidence/formlane_bridge_predicted.tsv
"""
import argparse
import os
import sqlite3
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backfill_pn_surface import load_scrape, pair_verse, _name_token   # production engine
from build_abp_surface import ABBREV_TO_SLUG


def main():
    ap = argparse.ArgumentParser(description="Pre-register the bridge rule's add count (read-only).")
    ap.add_argument("db")
    ap.add_argument("--bh", required=True)
    ap.add_argument("--refused", required=True, help="refused dump of the UNAMENDED pass")
    ap.add_argument("--arrivals", help="certified arrivals TSV (172 rows) to cross-check")
    ap.add_argument("--out", help="write the predicted adds (TSV)")
    args = ap.parse_args()

    refused_keys = set()
    with open(args.refused, encoding="utf-8") as f:
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) >= 4:
                refused_keys.add((c[0], int(c[1]), int(c[2]), int(c[3])))
    verses_wanted = {(b, ch, vs) for b, ch, vs, _ in refused_keys}
    print(f"refused dump: {len(refused_keys):,} slots across {len(verses_wanted):,} verses")

    scrape, numbered, starred, bridge, _ = load_scrape(args.bh)

    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    slots_by_verse, meta = defaultdict(list), {}
    for r in con.execute("""
        SELECT w.verse_id, w.position,
               COALESCE(NULLIF(w.english_head,''), w.english) AS label,
               v.book, v.chapter, v.verse
        FROM words w JOIN verses v ON v.id = w.verse_id
        WHERE w.is_pn = 1 ORDER BY w.verse_id, w.position"""):
        key = (r["book"], r["chapter"], r["verse"])
        if key in verses_wanted:
            slots_by_verse[key].append((r["position"], _name_token(r["label"])))
            meta[key] = r["verse_id"]
    con.close()

    adds, causes_after = [], defaultdict(int)
    for key in sorted(slots_by_verse):
        book, ch, vs = key
        slug = ABBREV_TO_SLUG.get(book)
        hits = scrape.get((slug, ch, vs), [])
        nhits = numbered.get((slug, ch, vs), [])
        shits = starred.get((slug, ch, vs), [])
        paired, _, causes, refused_slots, bpos = pair_verse(
            slots_by_verse[key], hits, nhits, shits, bridge.get(slug, {}))
        for pos in bpos:
            if (book, ch, vs, pos) in refused_keys:
                adds.append((book, ch, vs, pos, paired[pos]))
        for pos, tok, cause in refused_slots:
            if (book, ch, vs, pos) in refused_keys:
                causes_after[cause] += 1

    print(f"\nPRE-REGISTERED: bridge adds among the dumped refusals = {len(adds):,}")
    print("remaining refusals re-classified:")
    for k in sorted(causes_after):
        print(f"  {k:18}: {causes_after[k]:,}")
    print(f"  (sum check: {len(adds) + sum(causes_after.values()):,} of {len(refused_keys):,} "
          f"dumped slots accounted for)")

    if args.arrivals:
        arr = set()
        with open(args.arrivals, encoding="utf-8") as f:
            next(f)
            for line in f:
                c = line.rstrip("\n").split("\t")
                arr.add((c[0], int(c[1]), int(c[2]), int(c[4])))
        hit = sum(1 for b, ch, vs, pos, _ in adds if (b, ch, vs, pos) in arr)
        print(f"\narrivals covered by the bridge: {hit:,} of {len(arr):,}")
        miss = sorted(k for k in arr if k not in {(b, ch, vs, pos) for b, ch, vs, pos, _ in adds})
        for b, ch, vs, pos in miss[:20]:
            print(f"  NOT covered: {b} {ch}:{vs} slot {pos}")

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write("book\tchapter\tverse\tposition\tform\n")
            for row in adds:
                f.write("\t".join(str(x) for x in row) + "\n")
        print(f"\npredicted adds written: {args.out}")


if __name__ == "__main__":
    main()
