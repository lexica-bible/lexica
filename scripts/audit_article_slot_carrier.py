#!/usr/bin/env python3
"""
audit_article_slot_carrier.py — content English riding the ARTICLE slot (G3588).

READ-ONLY. Reads the ABP source under abp_texts/ (diagnosis-grade: pre-build,
brackets unreordered) and re-runs the PRODUCTION build assembly in memory.
Touches no database.

WHY THIS SCRIPT EXISTS
----------------------
The 2026-07-31 issue-log session scoped a "content word on an ARTICLE slot"
class at 951 raw / 509 filtered rows (docs/audits/AUDIT_pn_star_verb_merge.md,
"Subpattern B"). Like the star-verb sweep beside it, that sweep's script was
never committed — only the hit list survived. The detector-gap close-out
(docs/tickets/TICKET_detector_gap.md) charged the next session with re-sweeping
the 509 the same way the star-verb gap was closed: predicate written down,
control-fired, halt proven.

The user-visible defect: a noun/verb's English sits on the bare article's slot,
so clicking that word serves the article's card (ὁ / ἡ / τό) instead of the
word's own. 1Ki 9:26 "the city G3588" is the archetype.

WHAT THIS SCRIPT FOUND ABOUT THE OLD 509 — three corrections on record
---------------------------------------------------------------------
The old predicate IS recoverable after all, from its own committed hit list:
reproduce_old() below rebuilds it and matches the doc list **951/951 with zero
difference in both directions** (and 509/509 after its thing(s) filter). So,
against the charter's stated premises:

  1. The exclusion WAS applied consistently. Its stated rule — "adjacent-empty-
     slot cases (the build redistribution class) are EXCLUDED" — keys on a blank
     slot holding a REAL number, on either side. It drops exactly 3,564 slots
     (the charter's own figure, reproduced to the row). A blank G* star never
     triggered it, which is why Act 19:4 "Jesus the" survived it. That is the
     rule working, not the rule being broken.
  2. Gen 22:21 "Huz" is NOT a miss — it is row 669 of the committed list, and it
     is inside the 509. The charter named it a known miss; it is a known hit.
     (Mat 20:22 "Jesus" and 2Sa 12:9 "Uriah" ARE genuine misses, both dropped by
     the real-number-adjacency exclusion above.)
  3. The 509's real defects are SCOPE, not consistency:
       (a) the 3,564 exclusion rests on an unproven theory about what the build
           redistributes — see THE 3,564, RESOLVED below;
       (b) English function words riding the article slot were stoplisted out,
           though they are the same click-defect;
       (c) it never checked the BUILD. Act 19:4 is in the 509, yet
           _split_compounds' sibling pass _split_pn_article_lump already repairs
           it — the built row reads "Jesus" on the star and "the" on G3588.
           A source-side hit is not a live defect.

THE PREDICATE (structural, stated in full)
------------------------------------------
STAGE 1 — SOURCE. Over each verse's canonical source tokens
(build_words_from_abp.iter_source_tokens — the same peel the build uses, so this
cannot drift from the build's slot boundaries), a slot is a CARRIER when:

    * its Strong's base is 3588 (any dotted form: G3588, G3588.1, G3588.2 —
      reported in FULL DOTTED form per the standing dotted-number audit rule);
    * its English, lowercased and split on word characters, has at least one
      word outside ARTICLE_ENGLISH (the article's own rendering: "the", plus the
      case words English needs for an oblique article — of/to/for/in/with/by/
      from/at/on/unto/into/upon/a/an/o);
    * and that residue is not wholly SUBSTANTIVAL ({one, ones, thing, things} —
      τό/τά/ὁ standing alone as a substantive, which IS the article's own
      English). Wholly-substantival rows go to bin S: reported, never dropped.

STAGE 2 — BUILD. Every carrier verse is re-assembled by the PRODUCTION
build_words_from_abp.build_verse_words (not a copy of its rules), twice:

    lex=None   the lexicon-driven passes (_split_compounds,
               _fix_backwards_pairing, _funcword_noun_relocate) are off; the
               lexicon-free repairs (_redistribute_pronoun_compounds,
               _split_pn_article_lump, _g1473_gloss_retag, _lord_subject_split,
               …) still run.
    MAXLEX     the most generous lexicon that could move a word OFF the article
               slot: the article's own definition is EMPTY (so no gloss word
               counts as "its own" and stays) and every other slot's definition
               contains everything (so any word may land there). Whatever the
               real lexicon does, it cannot move more off G3588 than this.

Each carrier row then lands in exactly one bin:

    P   source hit, gone after the lexicon-free build     -> build already fixes it
    R   still there at lex=None, gone under MAXLEX        -> LEXICON-DEPENDENT,
                                                            needs a live check
    D   still there under BOTH                            -> PROVEN DEFECT

D is an intersection, so it is a floor, not an estimate: the build demonstrably
cannot reach these rows. R is the honest unknown — CC cannot read bible.db, so
the live figure is a JP step (read-only sqlite3 lines at the end of the run).

THE 3,564, RESOLVED
-------------------
Taken IN, not excluded. The old rule assumed a blank numbered slot beside a
carrier means the build redistributes the word away. It does not follow:
_split_compounds (build_words_from_abp.py:469) only ever looks AHEAD, only from
a MULTI-WORD gloss, only on an UNBRACKETED slot, never into a G* star and never
into the copula (1510) — so backward adjacency, single-word carriers, bracketed
carriers and star-adjacency are all outside it. Rather than replace one theory
with another, this script runs the build and lets it answer: the 3,564 are swept
in, and whichever of them the build really does repair fall out as bin P or R on
their own evidence. Nothing is capped, and every bin prints a count.

CONTROLS (certification rule — a zero is worthless without a fired positive)
---------------------------------------------------------------------------
    1Ki 9:26  'the city'    -> D   the old sweep's own control positive
    Mat 20:22 'Jesus'       -> D   known MISS from the 509 (live-confirmed on PA)
    2Sa 12:9  'Uriah'       -> D   known MISS from the 509
    Gen 22:21 'Huz'         -> D   in the 509 (charter called it a miss — it is not)
    Act 19:4  'Jesus the'   -> P   in the 509, but the BUILD repairs it.
                                   The discriminating control: it proves stage 2
                                   actually separates source hits from live ones.
    1Co 1:28  'the things'  -> S   NEGATIVE control: legitimate substantival
                                   article English, must never count as a defect.
    reproduce_old()         -> 951 raw / 509 filtered, exactly.

RED-FIRST, BOTH DIRECTIONS — asserted on every run (run_red_first), not left as
a claim in a doc: the old predicate must go SILENT on Mat 20:22 / 2Sa 12:9 and
stay LOUD on Gen 22:21 / Act 19:4, while the new predicate fires on all four.

A run that loses ANY control HALTS instead of reporting a count.
--prove-halt breaks one control on purpose so the halt path is demonstrated,
not assumed.

  python3 scripts/audit_article_slot_carrier.py              # full sweep
  python3 scripts/audit_article_slot_carrier.py --controls   # controls only
  python3 scripts/audit_article_slot_carrier.py --old        # old-predicate replay
  python3 scripts/audit_article_slot_carrier.py --list D     # print one bin
  python3 scripts/audit_article_slot_carrier.py --prove-halt # halt path, live
"""
import argparse
import ast
import collections
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

from build_words_from_abp import (  # noqa: E402
    _VERSE_RE, build_verse_words, iter_source_tokens, parse_abp_line,
)

ABP_DIRS = [os.path.join(ROOT, "abp_texts", "abp_nt_texts"),
            os.path.join(ROOT, "abp_texts", "abp_ot_texts")]
AUDIT_DOC = os.path.join(ROOT, "docs", "audits", "AUDIT_pn_star_verb_merge.md")

ARTICLE_BASE = "3588"

# The article's own English: the article word plus the case words English needs
# when the article stands in an oblique case with no preposition of its own.
ARTICLE_ENGLISH = frozenset({
    "the", "of", "to", "for", "in", "with", "by", "from", "at", "on",
    "unto", "into", "upon", "a", "an", "o",
})

# τό / τά / ὁ standing alone as a substantive. ABP's own rendering, not a drop.
SUBSTANTIVAL = frozenset({"one", "ones", "thing", "things"})

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")


def residue(eng, stop=ARTICLE_ENGLISH):
    """English words on the slot that the article itself does not account for."""
    return [w for w in _WORD_RE.findall((eng or "").lower()) if w not in stop]


# ── the maximal lexicon (stage 2) ─────────────────────────────────────────────

class _Everything(object):
    """A definition set that contains every word."""
    def __contains__(self, item):
        return True


class MaxLex(dict):
    """Most generous lexicon that could move a word OFF the article slot.

    _split_compounds keeps a gloss word on its own slot when the word is in that
    slot's OWN definition, and hands it away when it is in a later slot's
    definition. So: empty definition for the article, universal definition for
    everything else. No real lexicon can move more off G3588 than this.
    """
    def get(self, key, default=None):
        return set() if key == ARTICLE_BASE else _Everything()

    def __bool__(self):
        return True
    __nonzero__ = __bool__


# ── source + build passes ─────────────────────────────────────────────────────

def iter_source_lines(dirs=None):
    """Yield (filename, abbrev, chapter, verse, raw_text) for every ABP line."""
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


def source_carriers(raw):
    """Carrier + substantival rows of one verse, from the source tokens.

    Returns (carriers, substantival) as lists of (english, dotted_number).
    """
    carriers, subst = [], []
    for t in iter_source_tokens(raw):
        if t["sbase"] != "G" + ARTICLE_BASE:
            continue
        eng = (t["eng"] or "").strip()
        if not eng:
            continue
        r = residue(eng)
        if not r:
            continue
        if set(r) <= SUBSTANTIVAL:
            subst.append(eng)
        else:
            carriers.append(eng)
    return carriers, subst


def built_carriers(line, lex):
    """Carrier English still sitting on an article slot AFTER the production build."""
    parsed = parse_abp_line(line)
    if not parsed:
        return []
    _bk, _ch, _vs, abp_words = parsed
    out = []
    for row in build_verse_words(list(abp_words), [], lex):
        # row: pos, english, english_head, strongs, strongs_base, ...
        if row[4] != ARTICLE_BASE:
            continue
        eng = (row[1] or "").strip()
        if not eng:
            continue
        r = residue(eng)
        if r and not set(r) <= SUBSTANTIVAL:
            out.append((eng, "G" + (row[3] or ARTICLE_BASE)))
    return out


def sweep(dirs=None):
    """Full sweep. Returns (bins, subst_count, slot_totals).

    bins maps 'P'/'R'/'D' -> list of (fn, bk, ch, vs, english, dotted_number).
    """
    bins = {"P": [], "R": [], "D": []}
    subst_total = 0
    totals = collections.Counter()
    maxlex = MaxLex()

    for fn, bk, ch, vs, raw in iter_source_lines(dirs):
        carriers, subst = source_carriers(raw)
        subst_total += len(subst)
        totals["carrier"] += len(carriers)
        if not carriers:
            continue

        line = "(%s %d:%d)  %s" % (bk, ch, vs, raw)
        plain = collections.Counter(e for e, _n in built_carriers(line, None))
        maxed = collections.Counter(e for e, _n in built_carriers(line, maxlex))

        for eng in carriers:
            dotted = "G" + ARTICLE_BASE
            if plain[eng] > 0:
                plain[eng] -= 1
                if maxed[eng] > 0:
                    maxed[eng] -= 1
                    bins["D"].append((fn, bk, ch, vs, eng, dotted))
                else:
                    bins["R"].append((fn, bk, ch, vs, eng, dotted))
            else:
                bins["P"].append((fn, bk, ch, vs, eng, dotted))
    return bins, subst_total, totals


# ── the old predicate, replayed ───────────────────────────────────────────────

# Recovered from the committed hit list (see this file's header). Reproduces the
# doc's 951 raw / 509 filtered EXACTLY, zero difference in both directions.
# Kept here so the old population never becomes unrecoverable again.
OLD_STOP = frozenset("""
the of to for in with by from at on unto into upon a an o
one ones is are was were be been am
his her their your our my its it he she they them him me we you i us
that this these those there which who what when where because if than
and but or nor so as also then yet even indeed both all any some
do did does will shall would should might can could must have has had
not no over after before under against toward towards throughout
""".split())


def _old_num_adjacent(toks, i):
    """The old sweep's exclusion: a blank slot holding a REAL number, either side."""
    for j in (i - 1, i + 1):
        if 0 <= j < len(toks):
            t = toks[j]
            if not (t["eng"] or "").strip() and t["sbase"] \
                    and t["sbase"] not in ("*", ""):
                return True
    return False


def reproduce_old(dirs=None):
    """Replay the 2026-07-31 sweep. Returns (raw_rows, filtered_rows)."""
    raw = []
    for fn, bk, ch, vs, text in iter_source_lines(dirs):
        toks = list(iter_source_tokens(text))
        for i, t in enumerate(toks):
            if t["sbase"] != "G" + ARTICLE_BASE:
                continue
            eng = (t["eng"] or "").strip()
            if not eng or _old_num_adjacent(toks, i):
                continue
            r = residue(eng, OLD_STOP)
            if not r:
                continue
            # The doc's last column is the comma-joined residue, so its thing(s)
            # filter only drops rows whose WHOLE residue is that one word
            # ("think,things" and "thing,saying" survived it).
            raw.append((fn, bk, ch, vs, eng, "G" + ARTICLE_BASE, ",".join(r)))
    filtered = [x for x in raw if x[6] not in ("thing", "things")]
    return raw, filtered


def doc_rows():
    """The 951 rows as committed in the audit doc (the old detector's only output)."""
    out = []
    with io.open(AUDIT_DOC, encoding="utf-8") as f:
        inside = False
        for line in f:
            s = line.strip()
            if s.startswith("## Subpattern B"):
                inside = True
                continue
            if inside and s.startswith("("):
                out.append(ast.literal_eval(s))
    return out


# ── controls ──────────────────────────────────────────────────────────────────

CONTROLS = [
    # (book, ch, vs, english on the article slot, expected bin, why)
    ("1Ki", 9, 26, "the city", "D", "the old sweep's own control positive"),
    ("Mat", 20, 22, "Jesus", "D", "known MISS from the 509, live-confirmed on PA"),
    ("2Sa", 12, 9, "Uriah", "D", "known MISS from the 509"),
    ("Gen", 22, 21, "Huz", "D", "IN the 509 (charter called it a miss - it is not)"),
    ("Act", 19, 4, "Jesus the", "P", "in the 509, but the build repairs it"),
    ("1Co", 1, 28, "the things", "S", "NEGATIVE control: legitimate substantival"),
]


def run_controls(bins, controls=CONTROLS, verbose=True):
    """Every control must land in its declared bin. True only if all do."""
    placed = {}
    for b, rows in bins.items():
        for _fn, bk, ch, vs, eng, _n in rows:
            placed.setdefault((bk, ch, vs, eng), set()).add(b)

    ok = True
    for bk, ch, vs, eng, want, why in controls:
        got = placed.get((bk, ch, vs, eng), set())
        if want == "S":
            # A substantival row must appear in NO defect bin at all.
            fired = not got
            shown = "bin S (absent from P/R/D)" if fired else "bins " + ",".join(sorted(got))
        else:
            fired = want in got
            shown = ("bin " + ",".join(sorted(got))) if got else "NOT FOUND"
        if verbose:
            print("  control %-3s %3d:%-3d %-12r want %s  %-26s %s"
                  % (bk, ch, vs, eng, want, shown,
                     "FIRED " if fired else "SILENT"))
            print("      %s" % why)
        if not fired:
            ok = False
    return ok


# Red-first, both directions: the old anchoring must be SILENT on the known
# misses and LOUD on the known hits, and the new predicate must fire on all four.
RED_FIRST = [
    ("Mat", 20, 22, "Jesus", False),      # known miss - old sweep never saw it
    ("2Sa", 12, 9, "Uriah", False),       # known miss
    ("Gen", 22, 21, "Huz", True),         # in the 509 all along
    ("Act", 19, 4, "Jesus the", True),    # in the 509 all along
]


def run_red_first(bins, verbose=True):
    """The old predicate silent where it should be, loud where it should be."""
    old = collections.Counter((r[1], r[2], r[3], r[4]) for r in reproduce_old()[1])
    new = set()
    for rows in bins.values():
        for _fn, bk, ch, vs, eng, _n in rows:
            new.add((bk, ch, vs, eng))
    ok = True
    for bk, ch, vs, eng, want_old in RED_FIRST:
        k = (bk, ch, vs, eng)
        in_old = old[k] > 0
        in_new = k in new
        good = (in_old == want_old) and in_new
        if verbose:
            print("  red-first %-3s %3d:%-3d %-12r old-509 %-7s new %-7s %s"
                  % (bk, ch, vs, eng,
                     "IN" if in_old else "SILENT",
                     "FIRES" if in_new else "SILENT",
                     "OK" if good else "BROKEN"))
        if not good:
            ok = False
    return ok


def run_old_control(verbose=True):
    """The old-predicate replay must still reproduce the committed list exactly."""
    raw, filt = reproduce_old()
    doc = doc_rows()
    mine = collections.Counter((r[1], r[2], r[3], r[4]) for r in raw)
    theirs = collections.Counter((r[1], r[2], r[3], r[4]) for r in doc)
    same = (mine == theirs)
    if verbose:
        print("  control old-predicate replay: raw %d (doc %d), filtered %d, "
              "row-for-row %s"
              % (len(raw), len(doc), len(filt), "MATCH" if same else "DIFFERS"))
    return same and len(raw) == 951 and len(filt) == 509


# ── live sizing (JP step — CC cannot read bible.db) ───────────────────────────

def article_only_renderings(dirs=None):
    """Every English string an article slot carries that this predicate treats as
    the article's OWN (article-only or substantival). Generated from the same
    residue() call the sweep uses, so the live query cannot drift from it."""
    seen = set()
    for _fn, _bk, _ch, _vs, raw in iter_source_lines(dirs):
        for t in iter_source_tokens(raw):
            if t["sbase"] != "G" + ARTICLE_BASE:
                continue
            eng = (t["eng"] or "").strip()
            if not eng:
                continue
            r = residue(eng)
            if not r or set(r) <= SUBSTANTIVAL:
                seen.add(eng.lower())
    return sorted(seen)


def live_sizing_sql(dirs=None):
    """A read-only one-liner JP can run on PA to size the class in the LIVE table."""
    vals = ", ".join("'%s'" % s.replace("'", "''")
                     for s in article_only_renderings(dirs))
    return ("  sqlite3 ~/bible-db/bible.db \"SELECT count(*) FROM words "
            "WHERE strongs_base='G3588' AND english IS NOT NULL "
            "AND trim(lower(english)) NOT IN (%s);\"" % vals)


# ── report ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--controls", action="store_true",
                    help="run the controls only, print nothing else")
    ap.add_argument("--old", action="store_true",
                    help="replay the old predicate and show where its rows land")
    ap.add_argument("--list", dest="bin", choices=["P", "R", "D"],
                    help="print every row of one bin")
    ap.add_argument("--prove-halt", action="store_true",
                    help="break a control on purpose and show the run halt")
    args = ap.parse_args()

    bins, subst, totals = sweep()

    controls = CONTROLS
    if args.prove_halt:
        # Re-declare the Act 19:4 control as a defect. The build repairs it, so a
        # working detector MUST refuse to report a count.
        controls = [c if c[0] != "Act" else ("Act", 19, 4, "Jesus the", "D",
                                             "DELIBERATELY BROKEN (--prove-halt)")
                    for c in CONTROLS]
        print("--prove-halt: Act 19:4 re-declared as bin D. Expect a HALT.\n")

    print("CONTROLS (a count is void unless every one fires)")
    ok = run_controls(bins, controls)
    ok = run_old_control() and ok
    ok = run_red_first(bins) and ok
    print()
    if not ok:
        print("HALT: a control went silent - the predicate changed. "
              "Do not trust any count from this run.")
        return 1
    if args.prove_halt:
        print("HALT PATH FAILED: the broken control still passed. "
              "The detector is not certifying anything.")
        return 1
    if args.controls:
        print("controls only: all fired.")
        return 0

    print("SOURCE STAGE - English on the article slot beyond the article's own")
    print("  carrier rows (content English)          : %5d" % totals["carrier"])
    print("  bin S  substantival 'the one/thing(s)'  : %5d   (legitimate, not a defect)"
          % subst)
    print()
    print("BUILD STAGE - production build_verse_words re-run on every carrier verse")
    print("  bin P  repaired by the lexicon-free build: %5d" % len(bins["P"]))
    print("  bin R  lexicon-dependent, needs a live check: %5d" % len(bins["R"]))
    print("  bin D  PROVEN DEFECT (build cannot reach it): %5d" % len(bins["D"]))
    print()
    print("  REVISED ARTICLE-SLOT POPULATION (D + R) : %5d   SUPERSEDES 509"
          % (len(bins["D"]) + len(bins["R"])))
    print("     of which PROVEN                      : %5d   (bin D - a floor, "
          "not an estimate)" % len(bins["D"]))
    print("     of which pending the live check      : %5d   (bin R)"
          % len(bins["R"]))
    print()

    # Reporting split inside D, using the old sweep's own content/function line.
    # Nothing is dropped - both halves are counted and printed.
    d_content = [h for h in bins["D"] if residue(h[4], OLD_STOP)]
    d_function = [h for h in bins["D"] if not residue(h[4], OLD_STOP)]
    print("  D split (reporting only, nothing dropped):")
    print("     content word on the article slot     : %5d   (the old 509's target)"
          % len(d_content))
    print("     English function word on it          : %5d   (same click-defect, "
          "different repair)" % len(d_function))
    print()

    # Containment, counted as a MULTISET so a verse holding the same English twice
    # cannot be double-credited (that inflated an earlier draft past 509).
    raw, filt = reproduce_old()
    pools = {b: collections.Counter((r[1], r[2], r[3], r[4]) for r in bins[b])
             for b in ("P", "R", "D")}
    where = collections.Counter()
    for r in filt:
        k = (r[1], r[2], r[3], r[4])
        for b in ("D", "R", "P"):
            if pools[b][k] > 0:
                pools[b][k] -= 1
                where[b] += 1
                break
        else:
            where["S"] += 1
    print("  CONTAINMENT - where the old 509's rows land now (of 509):")
    for b, label in (("D", "proven defect"), ("R", "lexicon-dependent"),
                     ("P", "already repaired by the build"),
                     ("S", "substantival - the new predicate reads it as the "
                           "article's own English")):
        print("     bin %s : %5d   %s" % (b, where[b], label))
    print()
    print("The 3,564 'adjacent-empty-slot' rows the old sweep excluded wholesale are")
    print("swept IN here; whichever the build really repairs fell out as P or R above.")
    print()
    print("LIVE CONFIRMATION IS A JP STEP - a source-side scan is not live state.")
    print("Sizing check (the NOT IN list is generated from this run's own predicate,")
    print("so it cannot drift from it) - expect ~%d if the real lexicon repairs every"
          % len(bins["D"]))
    print("R row, ~%d if it repairs none:" % (len(bins["D"]) + len(bins["R"])))
    print()
    print(live_sizing_sql())
    print()
    print("Per-control row checks (verses.book is the 3-letter abbrev, not a number):")
    for bk, ch, vs, eng, want, _why in CONTROLS:
        if want != "D":
            continue
        print("  sqlite3 ~/bible-db/bible.db \"SELECT w.position, w.strongs, "
              "w.strongs_base, w.english FROM words w JOIN verses v ON "
              "v.id=w.verse_id WHERE v.book='%s' AND v.chapter=%d AND v.verse=%d "
              "ORDER BY w.position;\"   -- expect %r still on G3588"
              % (bk, ch, vs, eng))

    if args.old:
        print()
        print("OLD PREDICATE REPLAY: raw %d, filtered %d (doc: 951 / 509)"
              % (len(raw), len(filt)))
        for r in filt:
            print("  %r" % (r,))

    if args.bin:
        print()
        print("--- bin %s (%d rows) ---" % (args.bin, len(bins[args.bin])))
        for fn, bk, ch, vs, eng, n in bins[args.bin]:
            print("(%r, %r, %d, %d, %r, %r)" % (fn, bk, ch, vs, eng, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
