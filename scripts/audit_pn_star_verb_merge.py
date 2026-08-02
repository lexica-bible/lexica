#!/usr/bin/env python3
"""
audit_pn_star_verb_merge.py — PN-star merged-verb class, BOTH orientations.

READ-ONLY. Reads the ABP source under abp_texts/ (diagnosis-grade: pre-build,
brackets unreordered). Touches no database.

WHY THIS SCRIPT EXISTS
----------------------
The 2026-07-31 issue-log session scoped this class at 145 spots but its sweep was
never committed — only the hit list in docs/audits/AUDIT_pn_star_verb_merge.md survived. That
list is anchored on "star-slot English" (the doc's own column header), so it can
only ever represent the orientation where the STAR chunk carries the merged
English. JP found Mat 26:1 ("Jesus finishedG5055 G3588 G*"), where the merge runs
the other way: the name rides the VERB's number and the star slot is left empty.
No shape of that verse is expressible in the old list's tuple, so it could not be
reported. See docs/tickets/TICKET_detector_gap.md.

The old 145 is NOT reproducible: its structural core yields ~247 rows here, and
the 100+ it silently dropped are structurally identical to rows it kept ("this
Moses" out, "these Galileans" in). The count below therefore SUPERSEDES 145
rather than adjusting it, and the predicate is written down so the next session
can argue with it.

THE PREDICATE (structural, stated in full)
------------------------------------------
Within one verse's canonical source tokens (iter_source_tokens — the same peel
the build uses, so this can't drift from the build's slot boundaries):

  Class A — STAR CARRIES (the catalogued orientation)
    A star slot ('G*') whose English is MULTI-WORD, with at least one immediately
    adjacent slot that holds a real number and has EMPTY English.
    e.g. Mat 27:26  "scourging Jesus,G* G5417"  -> G5417 blank

  Class B — NUMBER CARRIES (the Mat 26:1 orientation, the blind spot)
    A star slot with EMPTY English, where the nearest slot with English on one
    side (walking across any run of blank slots between) is MULTI-WORD. That
    neighbour is the carrier; the name has no printed English of its own.
    e.g. Mat 26:1  "Jesus finishedG5055 G3588 G*"  -> carrier G5055, star blank

Both are one mechanism mirrored: a name and a content word share one cell and the
other slot is left blank. _split_compounds skips star slots, so neither is
redistributed at build time.

The MULTI-WORD requirement on the carrier is a guard, not decoration: it is what
separates a real merge from an ordinary extra star (1Ch 20:4 "[4struckG3960 G*
1SibbechaiG* ...]" — that star's name IS printed, on its own slot).

CONTROLS (certification rule — a zero is worthless without a fired positive)
---------------------------------------------------------------------------
--controls asserts, and any full run re-checks, that:
    Mat 26:1  fires as class B    (the gap case)
    Mat 27:26 fires as class A    (original positive, G5417)
    Mat 27:47 fires as class A    (original positive, G5455)
A run that loses any control HALTS instead of reporting a count.

Numbers are reported in FULL DOTTED form (G1510.6, not G1510) per the standing
dotted-number audit rule.

  python3 scripts/audit_pn_star_verb_merge.py            # full sweep
  python3 scripts/audit_pn_star_verb_merge.py --controls # controls only
  python3 scripts/audit_pn_star_verb_merge.py --class B  # one orientation
"""
import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

from build_words_from_abp import (  # noqa: E402
    _STRONGS_RE, _VERSE_RE, _emit_words, iter_source_tokens, load_name_roster,
)
from entity_resolution import norm_name  # noqa: E402


def name_roster():
    """The pinned TIPNR roster — owned by the BUILD since the lane-② fix landed
    (load_name_roster in build_words_from_abp); imported, never copied, so the
    detector's B1/B2 split and the fix pass can't drift apart (ruling 4)."""
    return load_name_roster()


def holds_a_name(eng, names):
    return any(norm_name(t) in names
               for t in re.findall(r"[A-Za-z][A-Za-z'\-]*", eng))

ABP_DIRS = [os.path.join(ROOT, "abp_texts", "abp_nt_texts"),
            os.path.join(ROOT, "abp_texts", "abp_ot_texts")]


def _raw_numbers(text):
    """Full dotted Strong's per emitted token, in iter_source_tokens order.

    Built from the same _STRONGS_RE split + _emit_words peel that
    iter_source_tokens uses, so the two lists are index-aligned by construction.
    iter_source_tokens deliberately truncates the dotted suffix into `sbase`;
    the audit rule wants the dotted number, so we carry it alongside.
    """
    parts = _STRONGS_RE.split(text)
    pairs = []
    i = 0
    while i < len(parts) - 1:
        pairs.append((parts[i], parts[i + 1]))
        i += 2
    if parts and parts[-1].strip():
        pairs.append((parts[-1], None))
    out = []
    for raw, strongs in pairs:
        for _eng, st, _pos, _o, _c in _emit_words(raw, strongs):
            out.append(st or "")
    return out


def iter_source_verses(dirs=None):
    """Yield (filename, abbrev, chapter, verse, tokens) for every ABP source line.

    Each token is the iter_source_tokens dict plus 'num' = the full dotted
    Strong's ('G1510.6' / 'G*' / '').
    """
    for d in (dirs or ABP_DIRS):
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".txt"):
                continue
            path = os.path.join(d, fn)
            with io.open(path, encoding="utf-8", errors="replace") as f:
                for line in f:
                    m = _VERSE_RE.match(line.strip())
                    if not m:
                        continue
                    toks = list(iter_source_tokens(m.group(4)))
                    nums = _raw_numbers(m.group(4))
                    assert len(toks) == len(nums), \
                        "token/number misalignment at %s %s:%s" % (
                            m.group(1), m.group(2), m.group(3))
                    for t, n in zip(toks, nums):
                        t["num"] = n
                    yield fn, m.group(1), int(m.group(2)), int(m.group(3)), toks


def _blank(t):
    """A slot holding a real number with no English of its own."""
    return not t["eng"].strip() and t["sbase"] not in ("*", "")


def scan_verse(fn, bk, ch, vs, toks):
    """Return the class-A and class-B hits in one verse."""
    hits = []
    for i, t in enumerate(toks):
        if t["sbase"] != "*":
            continue
        eng = t["eng"].strip()

        if eng:
            # Class A — the star chunk carries the merged English.
            if " " not in eng:
                continue
            blanks = [toks[j]["num"] for j in (i + 1, i - 1)
                      if 0 <= j < len(toks) and _blank(toks[j])]
            if blanks:
                hits.append(("A", fn, bk, ch, vs, eng, ",".join(blanks)))
            continue

        # Class B — the star is empty; find the carrier across any blank run.
        left = i - 1
        while left >= 0 and not toks[left]["eng"].strip():
            left -= 1
        right = i + 1
        while right < len(toks) and not toks[right]["eng"].strip():
            right += 1

        carrier = None
        if left >= 0 and " " in toks[left]["eng"].strip():
            carrier, span = toks[left], range(left + 1, i)
        elif right < len(toks) and " " in toks[right]["eng"].strip():
            carrier, span = toks[right], range(i + 1, right)
        if carrier is None:
            continue

        # Numbers left blank by the merge: the star itself plus any blank slots
        # sitting between the carrier and the star.
        blanks = [toks[j]["num"] for j in span if _blank(toks[j])]
        hits.append(("B", fn, bk, ch, vs, carrier["eng"].strip(),
                     ",".join([carrier["num"]] + blanks)))
    return hits


def sweep(dirs=None):
    hits = []
    for fn, bk, ch, vs, toks in iter_source_verses(dirs):
        hits.extend(scan_verse(fn, bk, ch, vs, toks))
    return hits


# ── controls ──────────────────────────────────────────────────────────────────

CONTROLS = [
    # (book, ch, vs, expected class, English that must appear on the carrier)
    ("Mat", 26, 1, "B", "Jesus finished"),   # the gap case JP found
    ("Mat", 27, 26, "A", "scourging Jesus"),  # original positive, G5417
    ("Mat", 27, 47, "A", "calls Elijah"),     # original positive, G5455
]


def run_controls(hits, verbose=True):
    """Every control must fire. Returns True only if all of them do."""
    by_ref = {}
    for cls, fn, bk, ch, vs, eng, nums in hits:
        by_ref.setdefault((bk, ch, vs), []).append((cls, eng, nums))
    ok = True
    for bk, ch, vs, want_cls, want_eng in CONTROLS:
        got = by_ref.get((bk, ch, vs), [])
        fired = [g for g in got if g[0] == want_cls and want_eng in g[1]]
        if verbose:
            mark = "FIRED " if fired else "SILENT"
            print("  control %-3s %2d:%-3d class %s  %-20r %s"
                  % (bk, ch, vs, want_cls, want_eng, mark))
            for g in fired:
                print("      -> class %s  %r  blanks %s" % g)
        if not fired:
            ok = False
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--controls", action="store_true",
                    help="run the controls only, print nothing else")
    ap.add_argument("--class", dest="cls", choices=["A", "B"],
                    help="report one orientation only")
    ap.add_argument("--list", action="store_true", help="print every hit row")
    args = ap.parse_args()

    hits = sweep()

    print("CONTROLS (a count is void unless all three fire)")
    ok = run_controls(hits)
    print()
    if not ok:
        print("HALT: a control went silent — the predicate changed. "
              "Do not trust any count from this run.")
        return 1
    if args.controls:
        print("controls only: all fired.")
        return 0

    a = [h for h in hits if h[0] == "A"]
    b = [h for h in hits if h[0] == "B"]

    # Class B residue split. The carrier must actually HOLD a name for a merge to
    # have happened; a carrier with no name is usually a bracket-position
    # placeholder whose name IS printed on its own star (1Sa 25:42 "rose upG450
    # G* 1Abigail],G*"). The roster is the pinned TIPNR, so it has misses of its
    # own (Bath-sheba, Bezaleel, gentilics like Sadducees) — the residue is
    # REPORTED, never silently dropped.
    names = name_roster()
    b1 = [h for h in b if holds_a_name(h[5], names)]
    b2 = [h for h in b if h not in b1]

    print("Class A   star carries the merged English      : %5d" % len(a))
    print("Class B   number carries, star left empty      : %5d" % len(b))
    print("   B1     carrier holds a roster name          : %5d" % len(b1))
    print("   B2     roster-silent residue (needs eyeball): %5d" % len(b2))
    print("TOTAL (A + B)                                  : %5d" % len(hits))
    print()
    print("(The 2026-07-31 figure of 145 is SUPERSEDED, not adjusted: that "
          "sweep's predicate\n was never committed and is not reproducible — "
          "see this file's header. All 145\n documented rows ARE contained in "
          "class A above.)")
    if args.list:
        print("\n--- B2 residue (mixed: real merges the roster missed + "
              "placeholder artifacts) ---")
        for h in b2:
            print("(%r, %d, %d, %r, %r)" % (h[2], h[3], h[4], h[5], h[6]))

    if args.list or args.cls:
        print()
        show = [h for h in hits if not args.cls or h[0] == args.cls]
        for cls, fn, bk, ch, vs, eng, nums in show:
            print("(%r, %r, %r, %d, %d, %r, %r)" % (cls, fn, bk, ch, vs, eng, nums))
    return 0


if __name__ == "__main__":
    sys.exit(main())
