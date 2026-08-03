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
  python3 scripts/audit_pn_star_verb_merge.py --plan     # FIX-PASS sizing (raw layer)
  python3 scripts/audit_pn_star_verb_merge.py --plan --corrected   # PA only: the
      build's real layer (Rahlfs/TAGNT corrections + lexicon + BH) — the mode the
      pre-registered expected picture derives from (the 8/1 four-casualty trap)
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
    pn_star_split,
)


def name_roster():
    """The pinned TIPNR roster — owned by the BUILD since the lane-② fix landed
    (load_name_roster in build_words_from_abp); imported, never copied, so the
    detector's B1/B2 split and the fix pass can't drift apart (ruling 4)."""
    return load_name_roster()


def holds_a_name(eng, names):
    """SHARED SPLITTER since 2026-08-02 (reviewer follow-up at the reconciliation
    receipt): the old raw-roster check here was fooled by the exact collision
    the fix pass gates against — 'the Jews killed' counted B1 via 'the', and
    hyphenated 'Bath-sheba' missed a real roster name. Classify with the fix
    pass's own three-leg splitter so the B1/B2 reporting split can't overstate
    or understate the class again. B1/B2 figures BEFORE this change (2,668/91)
    are superseded; the lane-③ eyeball list stays the member-pinned 98."""
    return bool(pn_star_split(eng, names)[0])

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


def iter_raw_lines(dirs=None):
    """(filename, abbrev, chapter, verse, raw_text) per ABP source line."""
    for d in (dirs or ABP_DIRS):
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".txt"):
                continue
            with io.open(os.path.join(d, fn), encoding="utf-8",
                         errors="replace") as f:
                for line in f:
                    m = _VERSE_RE.match(line.strip())
                    if m:
                        yield (fn, m.group(1), int(m.group(2)),
                               int(m.group(3)), m.group(4))


# Plan-mode controls: the three known rows must REACH the pass and log the
# right class (any typed reason — whether they write is the real map's call,
# asserted by the unit tests on hand maps, not hardcoded here).
_PLAN_CONTROLS = {("Mat", 26, 1): "B", ("Mat", 27, 26): "A", ("Mat", 27, 47): "A"}


def print_plan(dirs=None, corrected=False):
    """LANE-② SIZING — the fix pass's full decision record on the real
    attestation map + roster (TICKET_pn_star_fix.md "still owed" item 1).
    Runs _redistribute_pn_star_merge itself via build_verse_words — the audit
    reports on the REAL pass, never a model of it.

    TWO COUNTING BASES, both printed (the 8/1 build-line lesson): per DECISION
    (the build's own Results-line basis — every logged entry counts) and per
    SLOT (one line per star/carrier slot, refusal reasons joined).

    Verses with no 'G*' in the raw text are skipped in BOTH modes — stars come
    only from the source; the pronoun corrections retag G1473 numbers and can
    change a carrier's number or a gate result, but never mint or remove a
    star slot.

    corrected=True (PA ONLY): mirrors run()'s flow line for line —
    Rahlfs/TAGNT pronoun corrections + lexicon + BH rows — so every figure
    derives THROUGH the correction layer. HALTs if any input is missing
    rather than silently measuring the raw layer again. The pre-registered
    expected picture pins from THIS mode's output, member-level.
    """
    from build_words_from_abp import (build_attestation_map, build_verse_words,
                                      load_name_roster, parse_abp_line)
    rahlfs = tagnt = None
    corr_lex = None
    bh_index = {}
    slug_of = {}
    if corrected:
        import sqlite3
        from build_words_from_abp import (RahlfsLXX, TAGNTSource, correct_verse,
                                          apply_pronoun_corrections,
                                          RAHLFS_DIR, TAGNT_FILES,
                                          load_lexicon, load_bh_verse_index,
                                          ABBREV_TO_SLUG)
        if RahlfsLXX and RAHLFS_DIR.is_dir():
            rahlfs = RahlfsLXX(RAHLFS_DIR)
        if TAGNTSource and all(p.is_file() for p in TAGNT_FILES):
            tagnt = TAGNTSource([str(p) for p in TAGNT_FILES])
        if not (rahlfs and tagnt):
            print("HALT: --corrected needs the Rahlfs + TAGNT files (PA only). "
                  "Without both, this mode would silently measure the "
                  "uncorrected layer again.")
            return 1
        db_path = os.path.expanduser("~/bible-db/bible.db")
        bh_path = os.path.expanduser("~/bible-db/bh_scrape.db")
        for p in (db_path, bh_path):
            if not os.path.exists(p):
                print("HALT: --corrected needs %s (read-only) to mirror the "
                      "build's inputs." % p)
                return 1
        _c = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
        corr_lex = load_lexicon(_c)
        _c.close()
        _s = sqlite3.connect("file:%s?mode=ro" % bh_path, uri=True)
        bh_index = load_bh_verse_index(_s)
        _s.close()
        slug_of = ABBREV_TO_SLUG
        print("corrected mode: Rahlfs + TAGNT + lexicon (%d) + BH index (%d) "
              "loaded — same layer, same inputs as the real build.\n"
              % (len(corr_lex), len(bh_index)))
    import collections
    ren = build_attestation_map(dirs and None)
    ren1 = build_attestation_map(dirs and None, min_verses=1)
    names = load_name_roster()
    print("  attestation map: %d numbers · roster: %d tokens\n"
          % (len(ren), len(names)))

    entry_writes = collections.Counter()          # per class, per DECISION
    entry_refusals = collections.Counter()        # (class, reason)
    slot_outcomes = collections.Counter()         # per SLOT
    target_bases = collections.Counter()          # class-A write targets
    writes, refused, thresh_only, lex_backed = [], [], [], []
    control_seen = {}
    _flag_log = []

    for _fn, bk, ch, vs, raw in iter_raw_lines(dirs):
        if "G*" not in raw:
            continue
        line = "(%s %d:%d)  %s" % (bk, ch, vs, raw)
        parsed = parse_abp_line(line)
        if not parsed:
            continue
        abp_words = parsed[3]
        bh_rows = []
        lex = None
        if corrected:
            src = bnum = None
            if rahlfs.booknum(bk):
                src, bnum = rahlfs, rahlfs.booknum(bk)
            elif tagnt.booknum(bk):
                src, bnum = tagnt, tagnt.booknum(bk)
            if src:
                corrs = correct_verse([w[1] for w in abp_words],
                                      src.verse(bnum, ch, vs),
                                      [w[0] for w in abp_words])
                abp_words = apply_pronoun_corrections(
                    abp_words, corrs, _flag_log, f"{bk} {ch}:{vs}")
            slug = slug_of.get(bk)
            bh_rows = bh_index.get((slug, ch, vs), []) if slug else []
            lex = corr_lex
        log = []
        build_verse_words(list(abp_words), bh_rows, lex, ren=ren,
                          names=names, pn_star_refusals=log)
        if (bk, ch, vs) in _PLAN_CONTROLS and log:
            control_seen.setdefault((bk, ch, vs), set()).update(
                e[0] for e in log)
        for cls, cpos, npos, nbase, reason, moved in log:
            if reason == "WRITTEN":
                entry_writes[cls] += 1
                writes.append((cls, bk, ch, vs, cpos, nbase or "*",
                               " ".join(moved)))
                if cls == "A":
                    target_bases[nbase] += 1
            else:
                entry_refusals[(cls, reason)] += 1
                refused.append((cls, bk, ch, vs, cpos, reason, nbase or "*",
                                " ".join(moved)))
                if cls == "A" and reason == "unattested" and moved and \
                        all(w in ren1.get(nbase, ()) for w in moved):
                    thresh_only.append((bk, ch, vs, cpos, nbase,
                                        " ".join(moved)))
                if lex is not None and cls == "A" and reason == "unattested" \
                        and moved and \
                        all(w in lex.get(nbase, set()) for w in moved):
                    lex_backed.append((bk, ch, vs, cpos, nbase,
                                       " ".join(moved)))
        per = {}
        for cls, cpos, npos, nbase, reason, moved in log:
            per.setdefault((cls, cpos), set()).add(reason)
        for (cls, _cpos), reasons in per.items():
            slot_outcomes[(cls, "WRITTEN" if "WRITTEN" in reasons
                           else "+".join(sorted(reasons)))] += 1

    ok = True
    print("PLAN CONTROLS (each known row must reach the pass, right class):")
    for (bk, ch, vs), want in sorted(_PLAN_CONTROLS.items()):
        got = control_seen.get((bk, ch, vs), set())
        mark = "FIRED " if want in got else "SILENT"
        print("  %-3s %2d:%-3d want class %s  %s" % (bk, ch, vs, want, mark))
        if want not in got:
            ok = False
    if not ok:
        print("\nHALT: a plan control went silent — the pass or the peel "
              "changed. Do not trust any figure from this run.")
        return 1

    print("\nLANE-② PLAN — the fix pass's decision record%s"
          % (" (CORRECTED layer)" if corrected else " (RAW layer — sizing "
             "only; the pinned picture derives from --corrected on PA)"))
    print("\n  PER-DECISION tally (the build's Results-line basis):")
    print("    written   A %d · B %d" % (entry_writes["A"], entry_writes["B"]))
    print("    refusals  %d:" % sum(entry_refusals.values()))
    for (cls, reason), n in entry_refusals.most_common():
        print("      %6d  %s/%s" % (n, cls, reason))
    print("\n  PER-SLOT view (one line per star/carrier slot):")
    for (cls, outcome), n in slot_outcomes.most_common():
        print("    %6d  %s/%s" % (n, cls, outcome))
    print("\n  CLASS-A WRITE TARGETS (base -> writes):")
    for base, n in target_bases.most_common(15):
        print("    %6d  G%s" % (n, base))
    print("\n  THRESHOLD-ONLY class-A refusals (attested at 1 verse, below the")
    print("  >=5 floor — the threshold's revisit list): %d" % len(thresh_only))
    for row in thresh_only:
        print("    %-4s %3d:%-3d slot %-3d  -> G%-6s  %r" % row)
    print("\n  LEXICON-BACKED class-A 'unattested' rows (every moved word in the")
    print("  target's lexicon definition — the OTHER legal evidence source; the")
    print("  banked rare-number question's sizing, TICKET_pn_star_fix.md):")
    if lex is None:
        print("    n/a — lexicon is PA-only; run --plan --corrected there")
    else:
        print("    %d rows:" % len(lex_backed))
        for row in lex_backed:
            print("    %-4s %3d:%-3d slot %-3d  -> G%-6s  %r" % row)
    print("\n  REFUSALS (every decision the pass vetoed): %d" % len(refused))
    for row in refused:
        print("    %s %-4s %3d:%-3d slot %-3d  %-22s G%-6s  %r" % row)
    print("\n  WRITES (the full decision record): %d" % len(writes))
    for row in writes:
        print("    %s %-4s %3d:%-3d slot %-3d  G%-6s  %r" % row)
    print("\n  TOTAL WRITES: %d (A %d + B %d)"
          % (len(writes), entry_writes["A"], entry_writes["B"]))
    return 0


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
    ap.add_argument("--plan", action="store_true",
                    help="run the FIX PASS itself and print its full decision "
                         "record (both counting bases, every write/refusal)")
    ap.add_argument("--corrected", action="store_true",
                    help="with --plan: measure on the build's real layer "
                         "(Rahlfs/TAGNT + lexicon + BH — PA only)")
    args = ap.parse_args()

    if args.plan:
        return print_plan(corrected=args.corrected)

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
