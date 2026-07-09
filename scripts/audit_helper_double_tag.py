#!/usr/bin/env python3
"""
Read-only finder for the helper-word double-tag defect class (splitter ticket,
CHARTER_splitter_fix.md). WRITES NOTHING. Sorts every candidate into three
buckets and dry-runs the classification so JP can eyeball it before any fix.

The defect (two polarities, one root = ABP multi-word English spanning slots):

  A  TAG-DUPLICATION  (Jud 1:9 "May", Job 18:13 "And may", Job 3:4 "may"):
     A helper word peeled OUTSIDE a bracket keeps the same Strong's as the
     bracketed verb it fronts -> two rows, same tag. Structural fingerprint:
     row R has NO bracket_id and NO greek_pos, the NEXT row has the SAME
     strongs and DOES open a bracket. (A legit reorder-split -- Jas 2:21
     "Was..justified", Job 3:4 "may search out" -- has every piece INSIDE the
     bracket with its own greek_pos, so it never matches.)
     FIX = blank the helper row's strongs + strongs_base (english stays; it
     renders as plain text, no tag, no count, no highlight). One 2008 row left.

  B  ENGLISH-POOLED  (Rth 2:16 "you shall not reproach" | ""):
     ABP itself parked the whole English on the function-word row and left the
     content verb's row blank -- faithfully stored, not a builder bug. Signal:
     a BLANK-english row whose Strong's is a content word, immediately preceded
     by a MULTI-word phrase whose TAIL word is a rendering this verb carries
     ELSEWHERE in the corpus (ABP's own renderings, not a lexicon gloss).
     FIX = re-align: move the tail word onto the blank verb row. LEXICAL ->
     every B case is listed for hand-review, never auto-applied here.

Usage (PA, read-only):
    python3 scripts/audit_helper_double_tag.py            # full dry-run report
    python3 scripts/audit_helper_double_tag.py --strongs 2008,977   # focus dump
"""
import argparse
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.db")

# Secondary sanity guard on polarity A: the peeled leading word should read as an
# auxiliary / modal / subject scaffold. Structural matches whose head is NOT in this
# set are surfaced separately (possible third class) rather than silently stripped.
HELPER_HEADS = {
    "may", "might", "shall", "should", "will", "would", "let", "did", "do", "does",
    "was", "were", "be", "been", "is", "are", "am", "had", "has", "have",
    "can", "could", "must", "and", "but", "then", "so", "that", "when",
}

_PUNCT = re.compile(r"[^\w\s]")


def norm(s):
    return _PUNCT.sub("", (s or "")).lower().strip()


def load_words(conn):
    """All word rows grouped by verse, in reading order."""
    verses = defaultdict(list)
    ref = {}
    for vid, book, ch, vs, pos, eng, head, st, sb, gpos, bid in conn.execute(
        "SELECT v.id, v.book, v.chapter, v.verse, w.position, w.english, w.english_head,"
        "       w.strongs, w.strongs_base, w.greek_pos, w.bracket_id"
        "  FROM words w JOIN verses v ON v.id = w.verse_id"
        " ORDER BY v.id, w.position"
    ):
        verses[vid].append((pos, eng, head, st, sb, gpos, bid))
        ref[vid] = f"{book} {ch}:{vs}"
    return verses, ref


def build_rendering_sets(verses):
    """strongs -> set of english_heads ABP uses for it across the corpus."""
    ren = defaultdict(set)
    for rows in verses.values():
        for (_pos, _eng, head, st, _sb, _gp, _bid) in rows:
            if st and st not in ("*", "") and head:
                ren[st].add(norm(head))
    return ren


def is_real_tag(st, sb):
    return bool(st) and st not in ("*", "") and bool(sb) and sb not in ("*", "")


def scan(verses, ref, ren):
    a_clean, a_review, b_cases = [], [], []
    for vid, rows in verses.items():
        for i, (pos, eng, head, st, sb, gpos, bid) in enumerate(rows):
            # ---- Polarity A: peeled helper sharing the next slot's bracketed tag ----
            if is_real_tag(st, sb) and gpos is None and bid is None and i + 1 < len(rows):
                npos, neng, nhead, nst, nsb, ngpos, nbid = rows[i + 1]
                if nst == st and nbid is not None:
                    rec = (ref[vid], pos, eng, head, st, npos, neng, ngpos, nbid)
                    if norm(head) in HELPER_HEADS:
                        a_clean.append(rec)
                    else:
                        a_review.append(rec)
            # ---- Polarity B: blank content verb pooled onto the preceding phrase ----
            if (not eng or not eng.strip()) and is_real_tag(st, sb) and i > 0:
                ppos, peng, phead, pst, psb, pgpos, pbid = rows[i - 1]
                if peng and " " in peng.strip():
                    tail = norm(peng.strip().split()[-1])
                    if tail and tail in ren.get(st, set()):
                        b_cases.append((ref[vid], ppos, peng, tail, pos, st, sb))
    return a_clean, a_review, b_cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB)
    ap.add_argument("--strongs", default="2008,977",
                    help="comma-list of bare strongs to dump in full (reconcile to targets)")
    ap.add_argument("--sample", type=int, default=40)
    args = ap.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)  # read-only, cannot write
    verses, ref = load_words(conn)
    ren = build_rendering_sets(verses)
    a_clean, a_review, b_cases = scan(verses, ref, ren)

    total_words = sum(len(r) for r in verses.values())
    # rows whose strongs_base is already an empty string (the shape the A-fix creates)
    blank_sb = sum(1 for rows in verses.values() for r in rows if (r[4] or "") == "")

    print(f"DB (read-only): {args.db}")
    print(f"Total word rows: {total_words:,}")
    print(f"Rows with an EMPTY strongs_base today (the shape the A-fix creates): {blank_sb:,}")
    print()

    # ---- Control test: the three charter exhibits MUST be caught (fail-loud) ----
    print("=== CONTROL TEST (detector must fire on known positives) ===")
    def caught_a(refstr):
        return any(r[0] == refstr for r in a_clean)
    def caught_b(refstr):
        return any(r[0] == refstr for r in b_cases)
    checks = [
        ("Jud 1:9  A (May)",        caught_a("Jud 1:9")),
        ("Job 18:13 A (And may)",   caught_a("Job 18:13")),
        ("Job 3:4  A (may/come)",   caught_a("Job 3:4")),
        ("Rth 2:16 B (blank verb)", caught_b("Rth 2:16")),
    ]
    ok = True
    for name, hit in checks:
        print(f"  [{'PASS' if hit else 'FAIL'}] {name}")
        ok = ok and hit
    print(f"  -> control {'PASSED' if ok else 'FAILED — do not trust the counts below'}")
    print()

    # ---- Polarity A summary ----
    print(f"=== POLARITY A (strip helper tag): {len(a_clean)} clean + {len(a_review)} review ===")
    heads = Counter(norm(r[3]) for r in a_clean)
    print(f"  head-word spread (clean): {dict(heads.most_common())}")
    print(f"  sample (ref | helperpos english[head] G{{st}}  ->  verbpos english gpos/bid):")
    for r in a_clean[:args.sample]:
        refstr, pos, eng, head, st, npos, neng, ngpos, nbid = r
        print(f"    {refstr:<12} {pos:>3} '{eng}'[{head}] G{st}  ->  {npos} '{neng}' g{ngpos}/b{nbid}")
    if len(a_clean) > args.sample:
        print(f"    ... +{len(a_clean) - args.sample} more")
    print()
    if a_review:
        print(f"  --- A-REVIEW: structural match, head NOT an auxiliary (possible 3rd class) ---")
        for r in a_review:
            refstr, pos, eng, head, st, npos, neng, ngpos, nbid = r
            print(f"    {refstr:<12} {pos:>3} '{eng}'[{head}] G{st}  ->  {npos} '{neng}'")
        print()

    # ---- Polarity B (full list, hand-review) ----
    print(f"=== POLARITY B (re-align blank verb) — {len(b_cases)} case(s), ALL hand-review ===")
    print(f"  (ref | pooled-phrase-pos 'phrase' -> tail-word -> blank verbpos G{{st}})")
    for r in b_cases:
        refstr, ppos, peng, tail, pos, st, sb = r
        print(f"    {refstr:<12} {ppos} '{peng}' -> '{tail}' -> {pos} G{st}")
    print()

    # ---- Focused dump for reconciliation to targets (e.g. G2008/G977) ----
    focus = [s.strip() for s in args.strongs.split(",") if s.strip()]
    a_refs = {r[0] for r in a_clean}
    for fs in focus:
        print(f"=== FULL DUMP G{fs} (every tagged row; A=helper to strip) ===")
        rows_out = []
        for vid, rows in verses.items():
            for i, (pos, eng, head, st, sb, gpos, bid) in enumerate(rows):
                if st == fs:
                    nxt = rows[i + 1] if i + 1 < len(rows) else None
                    is_a = (gpos is None and bid is None and nxt and nxt[3] == st and nxt[6] is not None
                            and norm(head) in HELPER_HEADS)
                    rows_out.append((ref[vid], pos, eng, head, gpos, bid, "  <-- A strip" if is_a else ""))
        vset = {r[0] for r in rows_out}
        strip_n = sum(1 for r in rows_out if r[6])
        print(f"  rows now: {len(rows_out)}  verses: {len(vset)}   would strip: {strip_n}"
              f"  -> after: {len(rows_out) - strip_n} rows")
        for refstr, pos, eng, head, gpos, bid, mark in rows_out:
            print(f"    {refstr:<12} {pos:>3} '{eng}'[{head}] g{gpos}/b{bid}{mark}")
        print()


if __name__ == "__main__":
    main()
