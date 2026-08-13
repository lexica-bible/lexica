#!/usr/bin/env python3
"""
diff_form_coverage.py — READ-ONLY, verse-keyed compare of name-slot printed-form
coverage between two databases. Produces the form lane's arrivals list (gate F3 of
docs/tickets/CHARTER_form_table_rebuild.md).

WHY VERSE-KEYED, NEVER POSITION-KEYED (pinned 2026-08-13): the 8/8 words rebuild
renumbered word slots, so slot N in one file is not slot N in the other. A
position-keyed diff between live and the pre-8/5 baseline read 264 lost / 395
gained — a NET GAIN of 131 — while the two files' own totals (2,528 vs 2,361
uncovered name slots) prove a net LOSS of 167. The join key was meaningless in
both columns. This script keys on (book, chapter, verse, name token) instead,
using the SAME _name_token the production PN passes use (imported, never copied).

REGISTRATIONS (reviewer 2026-08-13 — all four must hold before the list feeds F3):
 1. CONTROL FIRST: run with --candidates, hand-verify ONE lost member by two direct
    reads, then re-run with --control Book:ch:vs:token — the run FAILS unless that
    row is in its lost list. The full count means nothing before the control passes.
 2. Key = verse + name identity. Position is used only WITHIN a file (to test
    whether a slot has its own abp_surface row), never across files.
 3. EXPECTED NET: lost - gained (incl. roster churn) must equal the difference of
    the two files' own uncovered totals, and that difference must be 167 exactly.
    Any other net prints STOP and exits nonzero.
 4. AMBIGUITY BUCKETED: a (verse, token) group holding more than one slot, or with
    different slot counts in the two files, is counted at GROUP level (coverage is
    a count; no cross-file pairing is ever guessed) and labeled 'multi' /
    'roster_changed' so those members can be hand-adjudicated or enumerated as a
    named F3 gap.

READ-ONLY on both files. Run on PA:
  PYTHONIOENCODING=utf-8 python3 ~/bible-db/scripts/diff_form_coverage.py \
      ~/bible-db/bible.db ~/bible-db/bible_pre_pnstar_swap_20260805.db \
      --candidates 5                       # step 1: pick a control, verify by hand
  ... same + --control 1Sa:20:1:david      # step 2: the certified full run
  ... same + --out /tmp/formlane_arrivals.tsv   # step 3: write the arrivals list
"""
import argparse
import os
import sqlite3
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_pn_greek_identity import _name_token


def load(path):
    """(book, ch, vs, token) -> list of (position, covered, english_label)."""
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.execute("PRAGMA busy_timeout=30000")
    groups = defaultdict(list)
    for book, ch, vs, pos, label, cov in con.execute("""
        SELECT v.book, v.chapter, v.verse, w.position,
               COALESCE(NULLIF(w.english_head,''), w.english),
               EXISTS(SELECT 1 FROM abp_surface s
                      WHERE s.verse_id=w.verse_id AND s.position=w.position)
        FROM words w JOIN verses v ON v.id = w.verse_id
        WHERE w.is_pn = 1"""):
        groups[(book, ch, vs, _name_token(label))].append((pos, bool(cov), label or ""))
    con.close()
    return groups


def pre_form(path, book, ch, vs, token):
    """Evidence for hand-verification: the baseline's stored forms on this group."""
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    out = []
    for pos, label, form in con.execute("""
        SELECT w.position, COALESCE(NULLIF(w.english_head,''), w.english), s.form
        FROM words w JOIN verses v ON v.id = w.verse_id
        LEFT JOIN abp_surface s ON s.verse_id = w.verse_id AND s.position = w.position
        WHERE w.is_pn = 1 AND v.book=? AND v.chapter=? AND v.verse=?""",
                                        (book, ch, vs)):
        if _name_token(label) == token:
            out.append((pos, label, form))
    con.close()
    return out


def main():
    ap = argparse.ArgumentParser(description="Verse-keyed name-slot coverage diff (read-only).")
    ap.add_argument("live", help="path to live bible.db")
    ap.add_argument("baseline", help="path to the pinned pre-8/5 baseline copy")
    ap.add_argument("--expect-net", type=int, default=167,
                    help="pre-registered net loss; any other net is a STOP (default 167)")
    ap.add_argument("--candidates", type=int, default=0,
                    help="print N lost members with baseline evidence for hand-verification")
    ap.add_argument("--control", help="Book:ch:vs:token — a hand-verified lost row that MUST "
                                      "appear in the lost list, or the run FAILS")
    ap.add_argument("--out", help="write the arrivals list (TSV) here")
    args = ap.parse_args()

    live = load(args.live)
    base = load(args.baseline)

    # Internal totals control: recompute each file's own uncovered count the same way
    # the charter's 0a read does, so the banked figures are re-derived, not inherited.
    unc_live = sum(1 for g in live.values() for _, cov, _ in g if not cov)
    unc_base = sum(1 for g in base.values() for _, cov, _ in g if not cov)
    total_net = unc_live - unc_base
    print(f"uncovered name slots: live={unc_live:,}  baseline={unc_base:,}  "
          f"net={total_net:+,} (totals-derived, method-independent)")

    # VERSE-FIRST accounting (redesigned 2026-08-13 after the first field run):
    # name labels themselves DRIFTED between the files — the wordpos lane filled
    # ~211 blank labels (340 -> 129), so a token that reads '' in the baseline
    # reads 'saul' live and token-keyed groups leak (first run: +168 vs +167).
    # A verse cannot drift, so LOST/GAINED are counted per verse (coverage is a
    # count; no cross-file pairing needed) and reconcile with the totals by
    # construction. Tokens are used only to ATTRIBUTE members within a lost
    # verse; whatever tokens can't cleanly attribute lands in 'label_drift' as
    # CANDIDATES (every uncovered live name slot of that verse), never guessed.
    by_verse_live = defaultdict(list)
    by_verse_base = defaultdict(list)
    for (bk, ch, vs, tok), slots in live.items():
        by_verse_live[(bk, ch, vs)].append((tok, slots))
    for (bk, ch, vs, tok), slots in base.items():
        by_verse_base[(bk, ch, vs)].append((tok, slots))

    lost_members = []          # (book, ch, vs, token, live_pos, english, bucket)
    lost = gained = 0
    buckets = defaultdict(int)
    for vkey in sorted(set(by_verse_live) | set(by_verse_base)):
        a = dict(by_verse_base.get(vkey, []))   # token -> slots (baseline)
        b = dict(by_verse_live.get(vkey, []))   # token -> slots (live)
        ca = sum(1 for s in a.values() for _, c, _ in s if c)
        cb = sum(1 for s in b.values() for _, c, _ in s if c)
        d = ca - cb
        if d == 0:
            continue
        if d < 0:
            gained += -d
            buckets["gained_verses"] += 1
            continue
        lost += d
        # attribute within the verse: only tokens present on BOTH sides with the
        # same slot count are clean; '' (label-less) is never clean.
        attributed = set()
        for tok in sorted(set(a) & set(b)):
            if not tok or len(a[tok]) != len(b[tok]):
                continue
            dt = (sum(1 for _, c, _ in a[tok] if c)
                  - sum(1 for _, c, _ in b[tok] if c))
            if dt <= 0:
                continue
            uncov = [(p, e) for p, c, e in b[tok] if not c]
            bucket = "token" if len(b[tok]) == 1 else "token_multi"
            for p, e in uncov[:dt]:
                lost_members.append((*vkey, tok, p, e, bucket))
                attributed.add(p)
                buckets["attributed_" + bucket] += 1
        residue = d - sum(1 for m in lost_members
                          if (m[0], m[1], m[2]) == vkey and m[6].startswith("token"))
        if residue > 0:
            buckets["label_drift"] += residue
            for tok, slots in b.items():
                for p, c, e in slots:
                    if not c and p not in attributed:
                        lost_members.append((*vkey, tok, p, e, "drift_candidate"))
            buckets["drift_candidate_rows"] = \
                sum(1 for m in lost_members if m[6] == "drift_candidate")

    print(f"\nlost coverage (verse-level): {lost:,}   gained: {gained:,}   "
          f"diff-net: {lost - gained:+,}")
    for k in sorted(buckets):
        print(f"  {k:22s}: {buckets[k]:,}")

    ok = True
    if lost - gained != total_net:
        print("\nSTOP: the verse-level diff does not reconcile with the files' own "
              f"totals ({lost - gained:+,} vs {total_net:+,}) — the key is leaking.")
        ok = False
    if total_net != args.expect_net:
        print(f"\nSTOP: totals net {total_net:+,} != pre-registered {args.expect_net:+,}.")
        ok = False

    if args.control:
        bk, ch, vs, tok = args.control.split(":")
        want = (bk, int(ch), int(vs), tok)
        hit = any((m[0], m[1], m[2], m[3]) == want for m in lost_members)
        print(f"\nCONTROL {args.control}: {'FOUND in lost list' if hit else 'MISSING — FAIL'}")
        if not hit:
            ok = False
    else:
        print("\nNO CONTROL SUPPLIED — this run is a candidate scan only; "
              "its counts are not certified.")
        ok = False

    if args.candidates:
        print(f"\ncandidates for hand-verification (baseline evidence attached):")
        for m in lost_members[:args.candidates]:
            bk, ch, vs, tok, pos, eng, bucket = m
            print(f"  {bk} {ch}:{vs} token={tok!r} live_slot={pos} eng={eng!r} [{bucket}]")
            for p, lab, form in pre_form(args.baseline, bk, ch, vs, tok):
                print(f"    baseline slot {p}: {lab!r} form={form!r}")

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write("book\tchapter\tverse\ttoken\tlive_position\tenglish\tbucket\n")
            for m in lost_members:
                f.write("\t".join(str(x) for x in m) + "\n")
        print(f"\narrivals list written: {args.out} ({len(lost_members):,} rows)")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
