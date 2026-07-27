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
import unicodedata
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_abp_surface import ABBREV_TO_SLUG
from build_pn_greek_identity import _name_token


def clean_form(s):
    """Trim scrape dirt off the EDGES of a printed form (stray standalone accent
    marks, spaces — the '΄ Αχαζ' case, Mat 1:9 dry-run). Interior characters are
    kept untouched; a form with no letters at all comes back empty (refused)."""
    chars = list(s or "")
    while chars and not unicodedata.category(chars[0]).startswith("L"):
        chars.pop(0)
    while chars and not unicodedata.category(chars[-1]).startswith("L"):
        chars.pop()
    return "".join(chars)


def compact(tok):
    """Hyphen/apostrophe-blind token key ('tubalcain' == 'tubal-cain') — the
    binder's compact-compare lesson (entity_resolution), match-key only, the
    stored form is untouched."""
    return (tok or "").replace("-", "").replace("'", "")


def _resolve(positions, forms):
    """The three safe rules on one token group. None = ambiguous."""
    if len(set(forms)) == 1:
        return {pos: forms[0] for pos in positions}
    if len(forms) == len(positions):
        return dict(zip(positions, forms))
    return None


def pair_verse(slots, name_hits, num_hits=()):
    """slots = [(position, token)] in position order; name_hits = the scrape's
    NAME rows [(token, form)] in printed order; num_hits = the scrape's NUMBERED
    rows, tried ONLY when the name pool has nothing for a token (lane-#2 cause A:
    famous names carry their Strong's number on the scrape page, so they never
    appear as name rows). Token comparison is compact (hyphen-blind, cause C).
    Returns ({position: form}, refused_count, cause_counts, refused_slots)."""
    out, causes, refused_slots = {}, defaultdict(int), []
    by_tok_slots = defaultdict(list)
    blank = []
    for pos, tok in slots:
        if compact(tok):
            by_tok_slots[compact(tok)].append(pos)
        else:
            blank.append(pos)                      # cause B: no usable label
    if blank:
        causes["blank-label"] += len(blank)
        refused_slots += [(p, "", "blank-label") for p in blank]
    pool_name, pool_num = defaultdict(list), defaultdict(list)
    for tok, form in name_hits:
        pool_name[compact(tok)].append(form)
    for tok, form in num_hits:
        pool_num[compact(tok)].append(form)
    refused = len(blank)
    for tok, positions in by_tok_slots.items():
        forms = pool_name.get(tok, [])
        if forms:
            got = _resolve(positions, forms)
            if got is None:
                refused += len(positions)
                causes["ambiguous"] += len(positions)
                refused_slots += [(p, tok, "ambiguous") for p in positions]
            else:
                out.update(got)
            continue
        forms = pool_num.get(tok, [])
        if not forms:
            refused += len(positions)
            causes["no-match"] += len(positions)
            refused_slots += [(p, tok, "no-match") for p in positions]
            continue
        got = _resolve(positions, forms)
        if got is None:
            refused += len(positions)
            causes["ambiguous-numbered"] += len(positions)
            refused_slots += [(p, tok, "ambiguous-numbered") for p in positions]
        else:
            out.update(got)
    return out, refused, causes, refused_slots


def main():
    ap = argparse.ArgumentParser(description="Printed Greek for proper-noun slots (new rows only).")
    ap.add_argument("db", help="path to bible.db (on PA)")
    ap.add_argument("--bh", required=True, help="bh_scrape.db (same source the identity build used)")
    ap.add_argument("--apply", action="store_true", help="write the rows (default: dry-run)")
    ap.add_argument("--dump-refused", metavar="FILE",
                    help="write every refused slot (tab-separated: book ch vs pos cause "
                         "label token | the verse's scrape name-slots) for the lane-#2 "
                         "by-cause classification")
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
    numbered = defaultdict(list)
    cleaned = dropped_empty = 0
    bh = sqlite3.connect(f"file:{args.bh}?mode=ro", uri=True)
    for b, c, v, strongs, greek, english in bh.execute(
            "SELECT book, chapter, verse, strongs, greek, english FROM bh_words "
            "WHERE greek IS NOT NULL AND greek != '' ORDER BY rowid"):
        is_name_row = not strongs
        if not is_name_row:
            # NUMBERED rows (cause A: famous names carry their number on the
            # scrape page). Cheap prefilter: only rows whose English contains a
            # capitalized word can be a name — the token match still decides.
            if not english or not any(w[:1].isupper() for w in english.split()):
                continue
        form = clean_form(greek)
        if not form:
            dropped_empty += 1        # no letters left — never a usable form
            continue
        if form != greek:
            cleaned += 1
        (scrape if is_name_row else numbered)[(b, c, v)].append(
            (_name_token(english), form))
    bh.close()
    print(f"scrape name-slot rows: {sum(len(v) for v in scrape.values()):,} "
          f"across {len(scrape):,} verses; numbered capitalized rows: "
          f"{sum(len(v) for v in numbered.values()):,} "
          f"(edge-trimmed {cleaned:,}; dropped letterless {dropped_empty:,})")

    # Every proper-noun slot, grouped per verse, position order.
    verses = defaultdict(list)
    meta, labels = {}, {}
    for r in con.execute("""
        SELECT w.verse_id, w.position,
               COALESCE(NULLIF(w.english_head,''), w.english) AS label,
               v.book, v.chapter, v.verse
        FROM words w JOIN verses v ON v.id = w.verse_id
        WHERE w.is_pn = 1
        ORDER BY w.verse_id, w.position"""):
        verses[r["verse_id"]].append((r["position"], _name_token(r["label"])))
        meta[r["verse_id"]] = (r["book"], r["chapter"], r["verse"])
        labels[(r["verse_id"], r["position"])] = r["label"]
    total_pn = sum(len(v) for v in verses.values())
    print(f"proper-noun slots: {total_pn:,} across {len(verses):,} verses\n")

    new_rows, already, refused_total = [], 0, 0
    causes_total = defaultdict(int)
    per_book_new = defaultdict(int)
    per_book_refused = defaultdict(int)
    mat1_sample = []

    dump = open(args.dump_refused, "w", encoding="utf-8", newline="\n") \
        if args.dump_refused else None

    for vid, slots in verses.items():
        book, ch, vs = meta[vid]
        slug = ABBREV_TO_SLUG.get(book)
        hits = scrape.get((slug, ch, vs), []) if slug else []
        nhits = numbered.get((slug, ch, vs), []) if slug else []
        paired, refused, causes, refused_slots = pair_verse(slots, hits, nhits)
        refused_total += refused
        per_book_refused[book] += refused
        for k, n in causes.items():
            causes_total[k] += n
        if dump and refused_slots:
            scrape_side = (" ".join(f"{t}={f}" for t, f in hits) or "(no name rows)") \
                + " || " + (" ".join(f"{t}={f}" for t, f in nhits) or "(no numbered rows)")
            for pos, tok, cause in refused_slots:
                dump.write(f"{book}\t{ch}\t{vs}\t{pos}\t{cause}\t"
                           f"{labels.get((vid, pos), '')}\t{tok}\t{scrape_side}\n")
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
    if dump:
        dump.close()
        print(f"\n  refused-slot dump written: {args.dump_refused} "
              f"({refused_total:,} lines)")

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
