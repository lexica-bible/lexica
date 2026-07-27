#!/usr/bin/env python3
"""
backfill_pn_surface.py — Phase-6: printed Greek for PROPER-NOUN slots (the last
all-English gap on the interlinear Greek line).

WHAT: abp_surface has no rows for name slots (census 2026-07-27: 32,479 is_pn
words, 32,479 missing — the whole class), because the strict aligner works by
Strong's number and name slots carry '*'/identity numbers, not in-verse tags
(Emmanuel carries Jesus' G2424 — number-pairing would mis-pair; see the ticket).
This pass pairs each name slot to the scrape's NAME rows (blank Strong's, Greek
form present) by the name token within the verse — the same pairing
build_pn_greek_identity.py proved (its refuse-on-doubt behavior sized the
'none' bucket) — extended with two safe rules for the genealogy shape the
strict one-to-one rule would refuse (Mat 1:2 has two Isaacs):

  1 candidate                       -> take it
  N candidates, ALL the same form   -> take the form (nothing to mis-assign)
  N candidates = N same-name slots  -> pair in printed order, k-th to k-th
  anything else                     -> REFUSE, counted, never guessed

WRITES: new rows ONLY into abp_surface (INSERT OR IGNORE on verse_id+position —
an existing row is never touched; guard also skips them up front and counts).
words/verses untouched. Undo = delete the added rows (they are exactly the
is_pn keys); a full build_abp_surface.py re-run also rebuilds from scratch
(re-run backfill_abp_surface.py AND this script after it).

After --apply: re-run scripts/build_abp_translit.py for the new rows'
romanizations, then the standard reload.

Run on PA:
  PYTHONIOENCODING=utf-8 python3 ~/bible-db/scripts/backfill_pn_surface.py \
      ~/bible-db/bible.db --bh ~/bible-db/bh_scrape.db            # dry-run
  ... same + --apply                                              # write
"""
import argparse
import os
import sqlite3
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_abp_surface import ABBREV_TO_SLUG
from build_pn_greek_identity import _name_token


def pair_verse(slots, hits):
    """slots = [(position, token)] in position order; hits = [(token, form)] in
    printed order. Returns ({position: form}, refused_count, cause_counts)."""
    out, causes = {}, defaultdict(int)
    by_tok_slots = defaultdict(list)
    for pos, tok in slots:
        by_tok_slots[tok].append(pos)
    by_tok_hits = defaultdict(list)
    for tok, form in hits:
        by_tok_hits[tok].append(form)
    refused = 0
    for tok, positions in by_tok_slots.items():
        forms = by_tok_hits.get(tok, [])
        if not forms:
            refused += len(positions)
            causes["no-match"] += len(positions)
        elif len(set(forms)) == 1:
            for pos in positions:
                out[pos] = forms[0]
        elif len(forms) == len(positions):
            for pos, form in zip(positions, forms):
                out[pos] = form
        else:
            refused += len(positions)
            causes["ambiguous"] += len(positions)
    return out, refused, causes


def main():
    ap = argparse.ArgumentParser(description="Printed Greek for proper-noun slots (new rows only).")
    ap.add_argument("db", help="path to bible.db (on PA)")
    ap.add_argument("--bh", required=True, help="bh_scrape.db (same source the identity build used)")
    ap.add_argument("--apply", action="store_true", help="write the rows (default: dry-run)")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=DELETE")
    con.execute("PRAGMA busy_timeout=30000")
    if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='abp_surface'").fetchone():
        sys.exit("abp_surface table missing — run build_abp_surface.py first.")

    existing = set((r[0], r[1]) for r in con.execute("SELECT verse_id, position FROM abp_surface"))
    before = len(existing)

    # Scrape NAME rows: blank Strong's + Greek present, printed order preserved.
    scrape = defaultdict(list)
    bh = sqlite3.connect(f"file:{args.bh}?mode=ro", uri=True)
    for b, c, v, greek, english in bh.execute(
            "SELECT book, chapter, verse, greek, english FROM bh_words "
            "WHERE (strongs IS NULL OR strongs='') AND greek IS NOT NULL AND greek != '' "
            "ORDER BY rowid"):
        scrape[(b, c, v)].append((_name_token(english), greek))
    bh.close()
    print(f"scrape name-slot rows: {sum(len(v) for v in scrape.values()):,} "
          f"across {len(scrape):,} verses")

    # Every proper-noun slot, grouped per verse, position order.
    verses = defaultdict(list)
    meta = {}
    for r in con.execute("""
        SELECT w.verse_id, w.position,
               COALESCE(NULLIF(w.english_head,''), w.english) AS label,
               v.book, v.chapter, v.verse
        FROM words w JOIN verses v ON v.id = w.verse_id
        WHERE w.is_pn = 1
        ORDER BY w.verse_id, w.position"""):
        verses[r["verse_id"]].append((r["position"], _name_token(r["label"])))
        meta[r["verse_id"]] = (r["book"], r["chapter"], r["verse"])
    total_pn = sum(len(v) for v in verses.values())
    print(f"proper-noun slots: {total_pn:,} across {len(verses):,} verses\n")

    new_rows, already, refused_total = [], 0, 0
    causes_total = defaultdict(int)
    per_book_new = defaultdict(int)
    per_book_refused = defaultdict(int)
    mat1_sample = []

    for vid, slots in verses.items():
        book, ch, vs = meta[vid]
        slug = ABBREV_TO_SLUG.get(book)
        hits = scrape.get((slug, ch, vs), []) if slug else []
        paired, refused, causes = pair_verse(slots, hits)
        refused_total += refused
        per_book_refused[book] += refused
        for k, n in causes.items():
            causes_total[k] += n
        for pos, form in paired.items():
            if (vid, pos) in existing:
                already += 1
                continue
            new_rows.append((vid, pos, form, ""))
            per_book_new[book] += 1
            if book == "Mat" and ch == 1 and len(mat1_sample) < 120:
                mat1_sample.append((vs, pos, form))

    print("== backfill_pn_surface ==")
    print(f"  existing abp_surface rows : {before:,}")
    print(f"  NEW rows to add           : {len(new_rows):,}")
    print(f"  already-present skips     : {already:,}   (guard; census said 0 expected)")
    print(f"  refusals                  : {refused_total:,}")
    for k in sorted(causes_total):
        print(f"      {k:10}: {causes_total[k]:,}")
    print(f"  arithmetic: new + refused + already = "
          f"{len(new_rows) + refused_total + already:,} (must equal {total_pn:,})")
    print("\n  coverage by book (new / refused):")
    for bk in sorted(set(per_book_new) | set(per_book_refused),
                     key=lambda b: -(per_book_new[b] + per_book_refused[b])):
        print(f"    {bk:4} {per_book_new[bk]:6,} / {per_book_refused[bk]:,}")
    print("\n  Matthew 1 spot-check (verse, position, form):")
    for vs, pos, form in mat1_sample:
        print(f"    1:{vs:<3} pos {pos:<3} {form}")

    if not args.apply:
        print("\n  DRY RUN — nothing written. Add --apply to write.\n")
        con.close()
        return

    con.executemany("INSERT OR IGNORE INTO abp_surface VALUES (?,?,?,?)", new_rows)
    con.commit()
    after = con.execute("SELECT count(*) FROM abp_surface").fetchone()[0]
    con.close()
    print(f"\n  Wrote. Row count {before:,} -> {after:,} "
          f"(delta {after - before:,}; must equal NEW rows above).")
    print("  Next: python3 scripts/build_abp_translit.py for the new rows' romanizations.\n")


if __name__ == "__main__":
    main()
