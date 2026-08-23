#!/usr/bin/env python3
"""
gate_form_lane.py — READ-ONLY gate F reads F3 (form-keyed arrivals) and F4
(compound allowlist survival) for the form-table rebuild
(docs/tickets/CHARTER_form_table_rebuild.md).

INDEPENDENCE: this is the check that shares NO code with backfill_pn_surface.py —
it compares the rebuilt table's stored forms, by bytes, against two pinned
evidence files produced before the rule existed (the certified arrivals list with
its baseline forms, and the allowlist captured from live via hex). A pass here is
evidence about the data, not about the pass agreeing with itself.

  F3: for every verse in the arrivals list, each form in missing_forms_at_verse
      must appear among the copy's covered forms at that verse (byte-equal).
      Misses are printed per member; the pre-ruled expectation is EXACTLY the 8
      enumerated bridge-fail verses (reviewer, 2026-08-13) — anything else fails.
  F4: every allowlist row's Greek value (decoded from its hex column, NBSP and
      all) must exist as a stored form in the copy at its verse.

Run on PA:
  PYTHONIOENCODING=utf-8 python3 ~/bible-db/scripts/gate_form_lane.py \
      ~/bible-db/bible_formlane.db \
      --arrivals ~/db_evidence/formlane_arrivals.tsv \
      --allowlist ~/bible-db/docs/tickets/compound_names_allowlist.tsv
"""
import argparse
import sqlite3
from collections import Counter, defaultdict

EXPECTED_F3_MISS_VERSES = {
    ("Gen", 39, 17), ("Gen", 41, 12), ("Est", 1, 21), ("Act", 8, 14),
    ("Act", 18, 14), ("Mar", 2, 8), ("Mar", 14, 66), ("Mat", 9, 35),
}


def main():
    ap = argparse.ArgumentParser(description="Gate F reads F3/F4 (read-only).")
    ap.add_argument("db")
    ap.add_argument("--arrivals", required=True)
    ap.add_argument("--allowlist", required=True)
    args = ap.parse_args()

    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)

    def verse_forms(book, ch, vs):
        return Counter(f for (f,) in con.execute(
            "SELECT s.form FROM abp_surface s JOIN verses v ON v.id=s.verse_id "
            "WHERE v.book=? AND v.chapter=? AND v.verse=?", (book, ch, vs)))

    # F3 — the same form returns, byte-compared, per verse.
    need = defaultdict(Counter)
    with open(args.arrivals, encoding="utf-8") as f:
        next(f)
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) >= 8 and c[7]:
                key = (c[0], int(c[1]), int(c[2]))
                if not need[key]:
                    need[key] = Counter(c[7].split("|"))
    misses = []
    for (book, ch, vs), want in sorted(need.items()):
        gap = want - verse_forms(book, ch, vs)
        for form, n in sorted(gap.items()):
            misses.append((book, ch, vs, form, n))
    print(f"F3: {len(need):,} arrival verses checked; forms missing at "
          f"{len({(m[0], m[1], m[2]) for m in misses})} verses:")
    for book, ch, vs, form, n in misses:
        tag = "expected (enumerated)" if (book, ch, vs) in EXPECTED_F3_MISS_VERSES \
            else "UNEXPECTED — FAIL"
        print(f"  {book} {ch}:{vs}  {form} x{n}   [{tag}]")
    f3_ok = {(m[0], m[1], m[2]) for m in misses} == EXPECTED_F3_MISS_VERSES

    # F4 — allowlist byte-survival (Greek decoded from the hex column).
    f4_miss = []
    with open(args.allowlist, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or line.startswith("hex\t"):
                continue
            c = line.rstrip("\n").split("\t")
            greek = bytes.fromhex(c[0]).decode("utf-8")
            book, ch, vs = c[2], int(c[3]), int(c[4])
            if verse_forms(book, ch, vs).get(greek, 0) == 0:
                f4_miss.append((book, ch, vs, greek))
    print(f"\nF4: allowlist rows missing as stored forms: {len(f4_miss)}")
    for book, ch, vs, greek in f4_miss:
        print(f"  {book} {ch}:{vs}  {greek!r}")

    print(f"\nF3 {'PASS' if f3_ok else 'FAIL'} (misses must be exactly the 8 enumerated)"
          f"\nF4 {'PASS' if not f4_miss else 'READ — adjudicate the members above'}")
    con.close()


if __name__ == "__main__":
    main()
