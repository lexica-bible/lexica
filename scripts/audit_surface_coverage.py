#!/usr/bin/env python3
"""
audit_surface_coverage.py — READ-ONLY characterization of the abp_surface gap.

WHY: abp_surface only stores a printed form when it DIFFERS from the dictionary
word, so an absent row is ambiguous — "same as dictionary" (fine) or "never
matched" (the real gap, where mode-three interlinear silently shows the
dictionary form as if it were the printed text). Only re-running the builder's
own alignment against bh_scrape.db can tell those apart. This script reuses the
production matching code (imports from build_abp_surface / lxx_align — never a
copy) and classifies EVERY word slot:

  stored           form found, differs from dictionary word -> row in abp_surface (fine)
  echo             form found, identical bar accents (no row needed — fine)
  pn_blank         proper noun / numberless slot ('*' or empty) — counted separately,
                   NEVER mixed into the mismatch read (the planned PN backfill owns these)
  verse_missing    the whole verse has no scrape tokens
  unaligned        alignment produced no partner token for this slot
  anchor_mismatch  a partner exists but its Strong's number disagrees
  empty_form       partner matched but its Greek cell is blank
  book_skipped     book absent from the scrape map

The GAP = verse_missing + unaligned + anchor_mismatch + empty_form.

Outputs: totals, per-book split (gap-heaviest first), and N samples per gap
class with enough context to classify by eye (ref, slot, Strong's, dictionary
word, ABP English, and the verse's scrape tokens).

CONTROL: the 'stored' count is cross-checked against the live abp_surface row
count — if they disagree, the audit is not measuring what the builder built,
and it says so loudly.

READ-ONLY on both databases. Run on PA:
  PYTHONIOENCODING=utf-8 python3 ~/bible-db/scripts/audit_surface_coverage.py \
      ~/bible-db/bible.db --bh ~/bible-db/bh_scrape.db
"""
import argparse
import os
import sqlite3
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_abp_surface import BHSource, iter_db_verses, strip_marks, _norm, _NT
from lxx_align import align, base

GAP_CLASSES = ("verse_missing", "unaligned", "anchor_mismatch", "empty_form")


def main():
    ap = argparse.ArgumentParser(description="Read-only abp_surface coverage audit.")
    ap.add_argument("db", help="path to bible.db (on PA)")
    ap.add_argument("--bh", required=True, help="bh_scrape.db (same source the builder used)")
    ap.add_argument("--samples", type=int, default=8, help="samples printed per gap class")
    args = ap.parse_args()

    bh = BHSource(args.bh)
    # Read-only + wait up to 30s if the live site is mid-write, instead of dying.
    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    con.execute("PRAGMA busy_timeout=30000")

    lemmas = {base(sg): (lem or "") for sg, lem in con.execute(
        "SELECT strongs_g, lemma FROM lexicon") if sg}
    dotted = {}
    if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='dotted_lexicon'").fetchone():
        dotted = {s: (lem or "") for s, lem in con.execute("SELECT strongs, lemma FROM dotted_lexicon")}

    # english per (verse_id, position) for readable samples
    eng = {}
    for vid, pos, e in con.execute("SELECT verse_id, position, COALESCE(english_head, english) FROM words"):
        eng[(vid, pos)] = e or ""

    total = Counter()                     # class -> count (all books)
    by_book = defaultdict(Counter)        # book -> class counter
    samples = defaultdict(list)           # gap class -> sample lines
    skipped_books = set()

    # ── recovery hypothesis counters ─────────────────────────────────────────
    # For each gap slot: could a leftover-pairing pass recover it? Within the
    # verse, pool the FAILED slots and the scrape tokens NOT consumed by a
    # successful match, group both sides by Strong's number, and pair in order —
    # but ONLY when the two sides have the SAME count for that number (the
    # ambiguity refusal). Also: would the paired form be a real line or an echo?
    rec = Counter()        # recover_stored / recover_echo / no_partner / count_clash
    vm_near = Counter()    # verse_missing: neighbor verse in the scrape has tokens?
    rec_samples = []

    for vid, book, ch, vs, words in iter_db_verses(con):
        slug = bh.slug(book)
        if not slug:
            skipped_books.add(book)
            for pos, sb, full in words:
                total["book_skipped"] += 1
                by_book[book]["book_skipped"] += 1
            continue
        toks = bh.tokens(slug, ch, vs)
        b_bases = [t[0] for t in toks]
        a_al = [_norm(sb) for _p, sb, _f in words]
        b_al = [_norm(b) for b in b_bases]
        amap = {}
        if toks:
            pairs = align(a_al, b_al, [False] * len(b_al))
            amap = {ai: bj for ai, bj in pairs if ai >= 0}

        cls_of = {}                       # word index -> class (for the recovery pass)
        used_bj = set()                   # scrape token indexes consumed by a real match
        for i, (pos, sb, full) in enumerate(words):
            if sb in ("", "*"):
                cls = "pn_blank"
            elif not toks:
                cls = "verse_missing"
            else:
                bj = amap.get(i, -1)
                if bj is None or bj < 0 or bj >= len(b_al):
                    cls = "unaligned"
                elif a_al[i] != b_al[bj]:
                    cls = "anchor_mismatch"
                else:
                    form = toks[bj][1] or ""
                    if not form:
                        cls = "empty_form"
                    else:
                        lem = dotted.get("G" + full) or lemmas.get(sb, "")
                        cls = "echo" if (lem and strip_marks(form) == strip_marks(lem)) else "stored"
                if cls in ("stored", "echo", "empty_form"):
                    used_bj.add(bj)
            cls_of[i] = cls
            total[cls] += 1
            by_book[book][cls] += 1
            if cls in GAP_CLASSES and len(samples[cls]) < args.samples:
                lem = dotted.get("G" + full) or lemmas.get(sb, "")
                bh_line = " ".join(f"{g or '·'}({b or '?'})" for b, g in toks[:14]) or "(no tokens)"
                samples[cls].append(
                    f"{book} {ch}:{vs} slot {pos}  G{full or sb}  dict={lem or '?'}  "
                    f"eng=\"{eng.get((vid, pos), '')}\"\n"
                    f"      scrape verse: {bh_line}{' …' if len(toks) > 14 else ''}")

        # ── recovery pass (measure-only) over this verse's failed slots ──────
        fails = [i for i, c in cls_of.items() if c in ("unaligned", "anchor_mismatch")]
        if fails and toks:
            left = defaultdict(list)      # number -> leftover scrape token indexes, in order
            for bj, (b, g) in enumerate(toks):
                if bj not in used_bj:
                    left[_norm(b)].append(bj)
            fail_by_num = defaultdict(list)
            for i in fails:
                fail_by_num[a_al[i]].append(i)
            for num, idxs in fail_by_num.items():
                partners = left.get(num, [])
                if not partners:
                    rec["no_partner"] += len(idxs)
                elif len(partners) != len(idxs):
                    rec["count_clash"] += len(idxs)
                else:
                    for i, bj in zip(idxs, partners):
                        pos, sb, full = words[i]
                        form = toks[bj][1] or ""
                        lem = dotted.get("G" + full) or lemmas.get(sb, "")
                        if not form:
                            rec["no_partner"] += 1
                        elif lem and strip_marks(form) == strip_marks(lem):
                            rec["recover_echo"] += 1
                        else:
                            rec["recover_stored"] += 1
                            if len(rec_samples) < args.samples:
                                rec_samples.append(
                                    f"{book} {ch}:{vs} slot {pos}  G{full or sb}  dict={lem or '?'}  "
                                    f"eng=\"{eng.get((vid, pos), '')}\"  -> would store: {form}")
        elif fails:
            rec["no_partner"] += len(fails)

        # verse_missing: does a NEIGHBOR verse key hold tokens? (off-by-one maps)
        if any(c == "verse_missing" for c in cls_of.values()):
            near = any(bh.tokens(slug, c2, v2)
                       for c2, v2 in ((ch, vs - 1), (ch, vs + 1), (ch + 1, 1)))
            vm_near["neighbor_has_tokens" if near else "no_neighbor"] += 1

    # ── control: does 'stored' match the live table? ──────────────────────────
    live = 0
    if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='abp_surface'").fetchone():
        live = con.execute("SELECT count(*) FROM abp_surface").fetchone()[0]
    con.close()

    grand = sum(total.values())
    content = grand - total["pn_blank"] - total["book_skipped"]
    gap = sum(total[c] for c in GAP_CLASSES)

    def p(n, d):
        return f"{100.0 * n / d:.1f}%" if d else "-"

    print("\n== abp_surface coverage audit (read-only) ==")
    print(f"  all word slots        : {grand}")
    print(f"  proper-noun/blank ('*'): {total['pn_blank']}   (separate bucket — PN backfill owns these)")
    if total["book_skipped"]:
        print(f"  book_skipped          : {total['book_skipped']}  books={sorted(skipped_books)}")
    print(f"  content slots         : {content}")
    print(f"    stored (real form)  : {total['stored']}  ({p(total['stored'], content)})")
    print(f"    echo (same as dict) : {total['echo']}  ({p(total['echo'], content)})")
    print(f"    GAP                 : {gap}  ({p(gap, content)})")
    for c in GAP_CLASSES:
        print(f"      {c:<15}: {total[c]}  ({p(total[c], content)})")

    print(f"\n  CONTROL: audit 'stored' = {total['stored']}  vs live abp_surface rows = {live}"
          + ("   OK" if total["stored"] == live else "   ** MISMATCH — audit not aligned with the built table; do NOT trust the numbers **"))

    print("\n== per-book (gap-heaviest first; gap% of the book's content slots) ==")
    rows = []
    for bk, c in by_book.items():
        bc = sum(c.values()) - c["pn_blank"] - c["book_skipped"]
        bg = sum(c[x] for x in GAP_CLASSES)
        rows.append((bk, bc, c["stored"], c["echo"], bg, c["pn_blank"]))
    rows.sort(key=lambda r: (r[4] / r[1] if r[1] else 0), reverse=True)
    print(f"  {'book':<5} {'content':>8} {'stored':>7} {'echo':>7} {'gap':>6} {'gap%':>6} {'pn':>6}")
    for bk, bc, s, e, g, pn in rows:
        print(f"  {bk:<5} {bc:>8} {s:>7} {e:>7} {g:>6} {p(g, bc):>6} {pn:>6}")

    # ── recovery hypothesis report ────────────────────────────────────────────
    fixable = rec["recover_stored"] + rec["recover_echo"]
    pool = sum(rec.values())
    print("\n== recovery pass (measure-only — nothing written) ==")
    print("  Rule tested: within the verse, pair failed slots with leftover scrape")
    print("  tokens by Strong's number, in order; REFUSE when the counts differ.")
    print(f"  failed slots examined  : {pool}")
    print(f"    recoverable -> real form stored : {rec['recover_stored']}")
    print(f"    recoverable -> same as dict     : {rec['recover_echo']}")
    print(f"    refused (count clash)           : {rec['count_clash']}")
    print(f"    no partner in verse             : {rec['no_partner']}")
    print(f"  would resolve {fixable} of {pool} ({p(fixable, pool)}) — residual gap would be "
          f"{p(gap - fixable, content)} of content slots")
    if vm_near:
        print(f"\n  verse_missing verses: {vm_near['neighbor_has_tokens']} have a neighboring "
              f"verse with scrape tokens (off-by-one suspects), {vm_near['no_neighbor']} truly absent nearby")
    if rec_samples:
        print("\n  sample recoveries (what the pairing rule would store):")
        for s in rec_samples:
            print(f"    {s}")

    print("\n== gap samples ==")
    for c in GAP_CLASSES:
        if not samples[c]:
            continue
        print(f"\n  -- {c} ({total[c]} total) --")
        for s in samples[c]:
            print(f"    {s}")
    print()


if __name__ == "__main__":
    main()
