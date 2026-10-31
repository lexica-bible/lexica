#!/usr/bin/env python3
"""
census_count_differs.py — READ-ONLY census of the verses where the ABP app has a DIFFERENT
number of slots than our words table (edition-upgrade charter §3 "the real scope risk").
Opens the db mode=ro; reuses audit_abp_app_vs_surface.py's own loaders, book map, Psalm-title
pairing and verse aligner (no second copy of any of them).

Prints: count-differs verses (total / OT / NT), the slot delta distribution (app sub-slots
minus our rows), how many of those verses are ALSO in the English-words-differ set (and how
many are not — a count difference with the same words = a split/merge, not an edition change),
and the per-book table. Writes the member list to --out (TSV) if given.

Usage (on PA, from ~/bible-db):
  python3 scripts/census_count_differs.py ~/bible-db/bible.db abp_app_html/abp_app_slots.tsv \
      --out ~/count_differs_members.tsv
"""
import argparse
import os
import sqlite3
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from audit_abp_app_vs_surface import (load_app, load_ours, align_verse, eng_words,  # noqa: E402
                                      rank, region, BOOK_ORDER)


def main():
    ap = argparse.ArgumentParser(description="Read-only count-differs census (app vs our slots).")
    ap.add_argument("db")
    ap.add_argument("tsv")
    ap.add_argument("--out", help="write the member list (one verse per row) to this TSV")
    a = ap.parse_args()
    con = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    app, app_eng = load_app(a.tsv)
    ours = load_ours(con)

    psa_shift = {(b, ch) for (b, ch, v) in ours if b == "Psa" and v == 0}
    members, delta_dist, per_book = [], Counter(), Counter()
    tot = Counter()
    for k in sorted(ours, key=lambda k: (rank(k[0]), k[1], k[2])):
        b, ch, v = k
        ka = (b, ch, v + 1) if (b, ch) in psa_shift else k
        a_slots = app.get(ka)
        if a_slots is None:
            tot["ours_only"] += 1
            continue
        rows = ours[k]["rows"]
        tot["paired"] += 1
        pairs, same, left_a, left_o = align_verse(a_slots, rows)
        aw, ow = eng_words(" ".join(app_eng[ka])), eng_words(" ".join(r["eng"] for r in rows))
        words_differ = Counter(aw) != Counter(ow)
        if words_differ:
            tot["eng_words_differ"] += 1
        if same:
            continue
        d = len(a_slots) - len(rows)
        tot["count_differs"] += 1
        tot[f"count_differs_{region(b)}"] += 1
        tot["count_differs_AND_words_differ" if words_differ else "count_differs_SAME_words"] += 1
        delta_dist[d] += 1
        per_book[b] += 1
        members.append((b, ch, v, ka[2], len(rows), len(a_slots), d, len(left_o), len(left_a),
                        "words-differ" if words_differ else "same-words"))

    print(f"paired verses {tot['paired']:,} · ours-only {tot['ours_only']} · "
          f"English words differ {tot['eng_words_differ']:,}")
    print(f"COUNT-DIFFERS verses: {tot['count_differs']:,}  (OT {tot['count_differs_OT']:,} · "
          f"NT {tot['count_differs_NT']:,})")
    print(f"   of which English words also differ: {tot['count_differs_AND_words_differ']:,}"
          f" · same words (split/merge shape, not wording): {tot['count_differs_SAME_words']:,}")
    print("   slot delta (app minus ours): " + "  ".join(
        f"{d:+d}:{n}" for d, n in sorted(delta_dist.items())))
    print(f"   our slots left unpaired in these verses: {sum(m[7] for m in members):,} · "
          f"app sub-slots left unpaired: {sum(m[8] for m in members):,}")
    print(f"\n   {'book':5} {'count≠':>7}")
    for b in BOOK_ORDER:
        if per_book.get(b):
            print(f"   {b:5} {per_book[b]:7}")
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write("book\tchapter\tverse\tapp_verse\tour_slots\tapp_subslots\tdelta\t"
                    "our_unpaired\tapp_unpaired\tenglish\n")
            for m in members:
                f.write("\t".join(str(x) for x in m) + "\n")
        print(f"\nwrote {len(members):,} member rows -> {a.out}")


if __name__ == "__main__":
    main()
