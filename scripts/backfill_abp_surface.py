#!/usr/bin/env python3
"""
backfill_abp_surface.py — recover printed-Greek forms the strict aligner missed.

WHAT: build_abp_surface.py aligns our word slots (stored in ABP's printed
ENGLISH order) against the scrape (Greek order) strictly left-to-right, so it
fails wherever ABP reorders words. This pass recovers those: within each verse,
pair the FAILED slots with the scrape tokens NOT consumed by a successful
match, grouped by Strong's number, in order — and REFUSE whenever the two
sides' counts for that number differ (ambiguity refusal; measured at only 62
slots corpus-wide). Measured by scripts/audit_surface_coverage.py 2026-07-11:
13,851 real forms + 4,736 same-as-dictionary (skipped, builder policy) out of
a 53,742-slot gap.

WRITES: new rows ONLY into abp_surface (INSERT OR IGNORE keyed on
verse_id+position — an existing row is never touched). words/verses untouched.
Undo: nothing to undo beyond the added rows; a full build_abp_surface.py re-run
rebuilds the table from scratch (then re-run THIS script after it).

Dry-run (default) prints the counts and samples, writes nothing. --apply writes.
After --apply, re-run scripts/build_abp_translit.py to fill the new rows'
romanizations.

Run on PA:
  PYTHONIOENCODING=utf-8 python3 ~/bible-db/scripts/backfill_abp_surface.py \
      ~/bible-db/bible.db --bh ~/bible-db/bh_scrape.db            # dry-run
  ... same + --apply                                              # write
"""
import argparse
import os
import sqlite3
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_abp_surface import BHSource, iter_db_verses, strip_marks, _norm
from lxx_align import align


def main():
    ap = argparse.ArgumentParser(description="Pairing-rule recovery for abp_surface (new rows only).")
    ap.add_argument("db", help="path to bible.db (on PA)")
    ap.add_argument("--bh", required=True, help="bh_scrape.db (same source the builder used)")
    ap.add_argument("--apply", action="store_true", help="write the rows (default: dry-run)")
    args = ap.parse_args()

    bh = BHSource(args.bh)
    con = sqlite3.connect(args.db)
    con.execute("PRAGMA journal_mode=DELETE")
    con.execute("PRAGMA busy_timeout=30000")

    if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='abp_surface'").fetchone():
        sys.exit("abp_surface table missing — run build_abp_surface.py first.")

    from lxx_align import base
    lemmas = {base(sg): (lem or "") for sg, lem in con.execute(
        "SELECT strongs_g, lemma FROM lexicon") if sg}
    dotted = {}
    if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='dotted_lexicon'").fetchone():
        dotted = {s: (lem or "") for s, lem in con.execute("SELECT strongs, lemma FROM dotted_lexicon")}

    existing = set(con.execute("SELECT verse_id, position FROM abp_surface"))
    before = len(existing)

    new_rows = []          # (verse_id, position, form, '')
    echo_skipped = clash = 0

    for vid, book, ch, vs, words in iter_db_verses(con):
        slug = bh.slug(book)
        if not slug:
            continue
        toks = bh.tokens(slug, ch, vs)
        if not toks:
            continue
        a_al = [_norm(sb) for _p, sb, _f in words]
        b_al = [_norm(b) for b, _g in toks]
        pairs = align(a_al, b_al, [False] * len(b_al))
        amap = {ai: bj for ai, bj in pairs if ai >= 0}

        # Replay the builder's own outcome per slot to find fails + consumed tokens.
        used_bj = set()
        fails = []
        for i, (pos, sb, full) in enumerate(words):
            if sb in ("", "*") or sb.startswith("H"):
                continue                        # PN / blank — the PN backfill's bucket
            bj = amap.get(i, -1)
            if bj is None or bj < 0 or bj >= len(b_al):
                fails.append(i)
            elif a_al[i] != b_al[bj]:
                fails.append(i)
            elif toks[bj][1]:
                used_bj.add(bj)                 # matched (stored or echo) — token consumed
            else:
                used_bj.add(bj)                 # matched but blank cell — still consumed
        if not fails:
            continue

        left = defaultdict(list)
        for bj, (b, g) in enumerate(toks):
            if bj not in used_bj:
                left[_norm(b)].append(bj)
        fail_by_num = defaultdict(list)
        for i in fails:
            fail_by_num[a_al[i]].append(i)
        for num, idxs in fail_by_num.items():
            partners = left.get(num, [])
            if not partners:
                continue
            if len(partners) != len(idxs):
                clash += len(idxs)
                continue                        # ambiguity refusal — never guess
            for i, bj in zip(idxs, partners):
                pos, sb, full = words[i]
                form = toks[bj][1] or ""
                if not form or (vid, pos) in existing:
                    continue
                lem = dotted.get("G" + full) or lemmas.get(sb, "")
                if lem and strip_marks(form) == strip_marks(lem):
                    echo_skipped += 1           # same as dictionary word — builder policy: no row
                    continue
                new_rows.append((vid, pos, form, ""))

    print("\n== backfill_abp_surface (pairing-rule recovery) ==")
    print(f"  existing rows            : {before}")
    print(f"  NEW rows to add          : {len(new_rows)}   (audit predicted 13,851)")
    print(f"  same-as-dictionary skips : {echo_skipped}   (audit predicted 4,736)")
    print(f"  ambiguity refusals       : {clash}   (audit predicted 62)")
    print("  samples:")
    for vid, pos, form, _ in new_rows[:10]:
        print(f"    v{vid} pos{pos}  {form}")

    if not args.apply:
        print("\n  DRY RUN — nothing written. Add --apply to write.\n")
        con.close()
        return

    con.executemany("INSERT OR IGNORE INTO abp_surface VALUES (?,?,?,?)", new_rows)
    con.commit()
    after = con.execute("SELECT count(*) FROM abp_surface").fetchone()[0]
    con.close()
    print(f"\n  Wrote. Row count {before} -> {after} (delta {after - before}; must equal NEW rows above).")
    print("  Next: python3 scripts/build_abp_translit.py to fill the new rows' romanizations.\n")


if __name__ == "__main__":
    main()
