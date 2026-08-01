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

REPAIR LANES (--lanes; ruling recorded 2026-07-31, ticket §6a/§6b)
-----------------------------------------------------------------
The fix session's lane split is derived HERE, from the same token walk that
produces the bins, so a re-sweep re-derives lane membership instead of trusting
a list that has gone stale. The lane question is structural:

    LANE A  a blank slot sits beside the carrier already holding this word's
            number (or a blank star) -> the build can hand the English back to
            it. Mechanical redistribution. 1,325 rows: all 1,049 of bin R plus
            276 of bin D.
    LANE B  nothing blank either side -> there is no slot to fill, so no pass
            runs. Each row closes by RULING (ABP supplied English, no Greek word
            exists) or by a curated write (the number is absent from the source).
            1,363 rows, all bin D.

Word class is NOT the discriminator and a lane keyed on it would put a fill and
a no-op through the same pass: Act 20:15 'and' (function) is a fill while 1Co
4:20 'is the' (function) has no Greek copula to write, and Num 7:25 'brought'
(content) is a write while Luk 6:15 'son of' (content) is supplied. Those four
are LANE_CONTROLS, chosen to cross the word-class line in both directions, so
the classifier breaks loudly if it ever drifts back onto word class.

The lane-B family table is REPORTING ONLY - a class-level expectation checked
against the source on six rows, never a per-row proof. No row closes on it.

  python3 scripts/audit_article_slot_carrier.py              # full sweep
  python3 scripts/audit_article_slot_carrier.py --controls   # controls only
  python3 scripts/audit_article_slot_carrier.py --lanes      # + the A/B split
  python3 scripts/audit_article_slot_carrier.py --old        # old-predicate replay
  python3 scripts/audit_article_slot_carrier.py --list D     # print one bin
  python3 scripts/audit_article_slot_carrier.py --manifest A # one lane's rows + hash
  python3 scripts/audit_article_slot_carrier.py --plan       # ruling-10 write/refusal sizing
  python3 scripts/audit_article_slot_carrier.py --prove-halt # halt path, live
  python3 scripts/audit_article_slot_carrier.py --prove-halt-lanes  # ditto, lanes
"""
import argparse
import ast
import collections
import hashlib
import io
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

from build_words_from_abp import (  # noqa: E402
    ARTICLE_OWN_ENGLISH, ARTICLE_SUBSTANTIVAL,
    _VERSE_RE, build_attestation_map, build_verse_words, iter_source_tokens,
    parse_abp_line,
)

ABP_DIRS = [os.path.join(ROOT, "abp_texts", "abp_nt_texts"),
            os.path.join(ROOT, "abp_texts", "abp_ot_texts")]
AUDIT_DOC = os.path.join(ROOT, "docs", "audits", "AUDIT_pn_star_verb_merge.md")

ARTICLE_BASE = "3588"

# The article's own English. RULING 4 (2026-07-31): ONE definition, owned by the
# BUILD and imported here — this file used to carry its own copy, and it disagreed
# with the bin-S predicate two lines below about whether "one/ones/thing(s)" counts.
# A fix built on the narrower set would have manufactured 226 new defects.
ARTICLE_ENGLISH = ARTICLE_OWN_ENGLISH

# τό / τά / ὁ standing alone as a substantive. ABP's own rendering, not a drop.
SUBSTANTIVAL = ARTICLE_SUBSTANTIVAL      # ruling 4: same one definition, from the build

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


# ── repair lanes (RULING 1, 2026-07-31) ───────────────────────────────────────
#
# The lane a carrier row falls in is decided by ONE structural question: is there
# an empty slot beside it that already holds the word's own number? That is the
# thing that decides the repair. Word class (function vs content) does NOT: see
# the four source-verified rows in LANE_CONTROLS below, where both classes appear
# on both sides.

LANE_A = "A"   # a blank slot sits beside it -> mechanical redistribution
LANE_B = "B"   # nothing to fill -> per-row triage, ruling or curated write


def lane_of(toks, i):
    """(lane, why) for the carrier slot at token index i.

    A blank neighbour holding a REAL number is lane A - the word's number is
    already in the verse with an empty slot, so the build can hand the English
    back to it. A blank star neighbour is also lane A (same shape, star target).
    Nothing blank either side is lane B: there is no slot to fill, so the row
    closes by ruling (ABP supplied English) or by a curated write (the number is
    genuinely absent from the source). Never by a pass.
    """
    star = False
    for j in (i - 1, i + 1):
        if not (0 <= j < len(toks)):
            continue
        t = toks[j]
        if (t["eng"] or "").strip():
            continue
        sb = t["sbase"] or ""
        if sb == "G" + ARTICLE_BASE:
            # A blank slot that is ITSELF an article is not this word's own number.
            # Handing "words" from one G3588 to the next G3588 relocates the defect
            # instead of repairing it — the reader still gets the article's card.
            # These rows were MIS-LANED, not correctly-laned-then-refused, so the
            # lane definition is corrected here rather than left to the pass to
            # decline. _redistribute_article_slot still refuses them too; the pass
            # is not allowed to depend on the lane split being right.
            continue
        if sb not in ("*", ""):
            return LANE_A, "blank numbered slot adjacent"
        star = True
    if star:
        return LANE_A, "blank star slot adjacent"
    return LANE_B, "no blank slot adjacent"


def source_carriers(raw):
    """Carrier + substantival rows of one verse, from the source tokens.

    Returns (carriers, substantival): carriers as (english, lane, why),
    substantival as english. The lane AND its reason are read off the SAME token
    walk the carrier itself came from, so lane membership can never drift from
    the predicate that produced it. The reason rides along so the manifest can
    separate the numbered-slot rows from the star rows without a second pass
    over the tokens (a second pass would be a copy of the predicate, not it).
    """
    carriers, subst = [], []
    toks = list(iter_source_tokens(raw))
    for i, t in enumerate(toks):
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
            carriers.append((i, eng) + lane_of(toks, i))
    return carriers, subst


def built_carriers(line, lex, ren=None, refusals=None):
    """Carrier English still on an article slot AFTER the build, KEYED BY SLOT.

    Returns {slot position -> english}. Position, never English text: a verse can
    carry the same article-slot English twice (Mar 14:24 'the blood', Rom 3:1
    'is the', Psa 40:5 'concerning'), and matching on text cannot tell the two
    apart. That ambiguity made a WORKING pass look like it had eaten three lane-B
    rows — the repair was credited to the wrong copy. (verse, English) was never a
    row identity. Certified safe: over all 27,266 verses holding an article slot,
    the build returns exactly one row per source token, so row k IS source token k.
    The row's NUMBER may legitimately change at build time (the pronoun retag
    rewrites G1473 -> 846 in 10,046 places), which is the second reason to key on
    position rather than on anything the build is entitled to rewrite.
    """
    parsed = parse_abp_line(line)
    if not parsed:
        return {}
    _bk, _ch, _vs, abp_words = parsed
    out = {}
    for k, row in enumerate(build_verse_words(list(abp_words), [], lex,
                                              ren=ren, article_refusals=refusals)):
        # row: pos, english, english_head, strongs, strongs_base, ...
        if row[4] != ARTICLE_BASE:
            continue
        eng = (row[1] or "").strip()
        if not eng:
            continue
        r = residue(eng)
        if r and not set(r) <= SUBSTANTIVAL:
            out[k] = eng
    return out


def sweep(dirs=None):
    """Full sweep. Returns (bins, lanes, whys, subst_count, slot_totals).

    bins  maps 'P'/'R'/'D' -> list of (fn, bk, ch, vs, english, dotted_number,
    slot) - slot being the SOURCE TOKEN INDEX, which is the row's only real
    identity: (verse, English) repeats within a verse and cannot be matched back.
    lanes maps the same keys -> list of 'A'/'B', INDEX-ALIGNED with bins. Kept
    parallel rather than widened into the row tuple so the controls, the
    containment count and --list keep reading the same 6-field row they always
    did; alignment is by construction (both appended in the same step), never by
    re-matching rows afterwards.
    whys  maps the same keys -> lane_of's own reason string, same alignment and
    for the same reason: --manifest needs the numbered/star distinction, and it
    has to be the predicate's own answer rather than a re-derivation of it.
    """
    bins = {"P": [], "R": [], "D": []}
    lanes = {"P": [], "R": [], "D": []}
    whys = {"P": [], "R": [], "D": []}
    subst_total = 0
    totals = collections.Counter()
    maxlex = MaxLex()
    # RULING 10: the build's own attestation map — the pass writes only what it
    # vets, so the audit must re-assemble with the same map or its bins describe
    # a pass that does not exist. Imported builder, never a copy.
    ren = build_attestation_map(dirs)

    for fn, bk, ch, vs, raw in iter_source_lines(dirs):
        carriers, subst = source_carriers(raw)
        subst_total += len(subst)
        totals["carrier"] += len(carriers)
        if not carriers:
            continue

        line = "(%s %d:%d)  %s" % (bk, ch, vs, raw)
        plain = built_carriers(line, None, ren)   # slot position -> english
        maxed = built_carriers(line, maxlex, ren)

        # Matched SLOT BY SLOT. The old multiset match on English text credited a
        # repair to whichever copy came first, which is how a correct pass read as
        # a lane-B breach on Mar 14:24 / Rom 3:1 / Psa 40:5.
        for slot, eng, lane, why in carriers:
            dotted = "G" + ARTICLE_BASE
            if slot in plain:
                b = "D" if slot in maxed else "R"
            else:
                b = "P"
            bins[b].append((fn, bk, ch, vs, eng, dotted, slot))
            lanes[b].append(lane)
            whys[b].append(why)
    return bins, lanes, whys, subst_total, totals


# ── lane-B families (RULING 2, 2026-07-31) ────────────────────────────────────
#
# Reporting only, and a CLASS-LEVEL expectation, not a per-row proof. The first
# three families are supplied-by-construction: the Greek has no copula, no "son",
# no possessive pronoun for the English to have fallen off. Spot-checked against
# the source on 1Co 4:20, 1Co 10:26, Act 12:7, Joh 5:5, Luk 6:15, Mar 1:19 only.
# Every other family needs eyes on the row. NOTHING here closes a row.

_FAM_IGNORE = ARTICLE_ENGLISH | SUBSTANTIVAL
_COPULA = frozenset("is are was were be am being been".split())
_POSSESS = frozenset("his her their its your my our him them".split())
_SONOF = frozenset("son sons daughter daughters".split())
_PREP = frozenset("""against concerning about during among belonging than
throughout toward towards over after before according beside around through
within without""".split())
_CONJ = frozenset("""and but or also even then so if that which who when
because indeed yet this these those there what as not no some all both""".split())

FAMILIES = [
    ("copula supplied (is/was/are/be)", _COPULA),
    ("possessive supplied (his/their/...)", _POSSESS),
    ("genealogy supplied (son/daughter of)", _SONOF),
    ("preposition - MIXED, needs eyes", _PREP),
    ("conjunction/pronoun - MIXED, needs eyes", _CONJ),
]
SUPPLIED_FAMILIES = frozenset(f[0] for f in FAMILIES[:3])


def family_of(eng):
    """Which lane-B family this English falls in. Reporting only."""
    r = set(residue(eng, _FAM_IGNORE))
    if not r:
        return "article's own English"
    for name, words in FAMILIES:
        if r <= words:
            return name
    if r <= (_COPULA | _POSSESS | _PREP | _CONJ):
        return "mixed function words - needs eyes"
    return "content word (noun/verb) - needs eyes"


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

# THE TWO P-FLIPS OF §6f ARE WITHDRAWN — they were the HALT witnesses (§6i).
# Mat 20:22 'Jesus' and 2Sa 12:9 'Uriah' did leave the article slot, but landed
# on numbers that are NOT the word's own (G1161/δέ, G846/αὐτός) — bin P counted
# departures, not landings. Under RULING 10 (§6j) the pass refuses both: 'jesus'
# is not an attested rendering of G1161 nor 'uriah' of G846, and their star
# neighbours are refused by ruling 6. Both controls return to D, and D is the
# CORRECT verdict — an unrepaired defect honestly reported beats a wrong card.
# The branch-level proof (each refusal logged BY the branch that refused, plus
# the red-first showing a permissive map WOULD write) lives in
# tests/test_article_slot_attestation.py.
#
# Gen 22:21 'Huz' stays D, but it is NOT the ruling-6 control (§6i): it sits at
# slot 0 with no second neighbour, so it refused for want of an alternative.
# 2Sa 12:9 — blank star one side, blank real number the other — is the shape
# that actually exercises the star branch, and its typed refusal log proves it.
CONTROLS = [
    # (book, ch, vs, english on the article slot, expected bin, why)
    ("1Ki", 9, 26, "the city", "D", "lane B - nothing to fill, the pass must not touch it"),
    ("Mat", 20, 22, "Jesus", "D", "HALT witness - ruling 10 refuses G1161, ruling 6 the star"),
    ("2Sa", 12, 9, "Uriah", "D", "HALT witness - ruling 10 refuses G846, ruling 6 the star"),
    ("Gen", 22, 21, "Huz", "D", "star-adjacent at slot 0 - refused, but NOT ruling 6's proof"),
    ("Act", 19, 4, "Jesus the", "P", "in the 509, but the build repairs it"),
    ("1Co", 1, 28, "the things", "S", "NEGATIVE control: legitimate substantival"),
]


def run_controls(bins, controls=CONTROLS, verbose=True):
    """Every control must land in its declared bin. True only if all do."""
    placed = {}
    for b, rows in bins.items():
        for _fn, bk, ch, vs, eng, _n, _slot in rows:
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
        for _fn, bk, ch, vs, eng, _n, _slot in rows:
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


# The lane split gets its own controls, same rule as the bins: a classifier that
# has never been fired on a known positive certifies nothing. These four are the
# rows the lane ruling was decided on, read out of the ABP source by hand, and
# they are chosen to CROSS the word-class line in both directions - two function
# words landing in different lanes, two content words landing in different lanes.
# If word class ever became the discriminator again, this set breaks.
LANE_CONTROLS = [
    # (book, ch, vs, english, expected lane, why)
    ("Act", 20, 15, "and", LANE_A,
     "FUNCTION word, G1161 present and BLANK beside it -> fill it"),
    ("1Co", 4, 20, "is the", LANE_B,
     "FUNCTION word, no Greek copula anywhere -> nothing to write"),
    ("Num", 7, 25, "brought", LANE_B,
     "CONTENT word, verb number absent from the source -> curated write"),
    ("Luk", 6, 15, "son of", LANE_B,
     "CONTENT word, 'son of' is supplied English -> nothing to write"),
    ("Gen", 22, 21, "Huz", LANE_A,
     "the star sub-case: blank G* beside it, not a numbered slot"),
    ("1Ki", 9, 26, "the city", LANE_B,
     "the archetype: 'city' is supplied, no slot to fill"),
    ("1Ti", 6, 3, "the words", LANE_B,
     "blank slot beside it is ANOTHER G3588 - not this word's own number"),
]


def run_lane_controls(bins, lanes, controls=LANE_CONTROLS, verbose=True):
    """Every lane control must land in its declared lane. True only if all do."""
    placed = {}
    for b, rows in bins.items():
        for idx, (_fn, bk, ch, vs, eng, _n, _slot) in enumerate(rows):
            placed.setdefault((bk, ch, vs, eng), set()).add(lanes[b][idx])

    ok = True
    for bk, ch, vs, eng, want, why in controls:
        got = placed.get((bk, ch, vs, eng), set())
        fired = want in got
        if verbose:
            print("  lane    %-3s %3d:%-3d %-12r want %s  %-26s %s"
                  % (bk, ch, vs, eng, want,
                     ("lane " + ",".join(sorted(got))) if got else "NOT FOUND",
                     "FIRED " if fired else "SILENT"))
            print("      %s" % why)
        if not fired:
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
    the article's OWN (article-only or substantival).

    Generated from the same residue() call the sweep uses — NOT from OLD_STOP, which
    only ever serves reproduce_old() and the D reporting split. So the live query
    cannot drift from the predicate that produced the counts.

    Collected from the SOURCE tokens *and* from the BUILT rows under both lexicon
    settings. Source alone is not enough: the build's repair passes mint article-own
    renderings the source never shows ('things,', 'things.', 'the one in' — 11 rows
    corpus-wide), and every one of those missing from the list would be miscounted as
    a defect by the live query.
    """
    seen = set()

    def keep(eng):
        eng = (eng or "").strip()
        if not eng:
            return
        r = residue(eng)
        if not r or set(r) <= SUBSTANTIVAL:
            seen.add(eng.lower())

    maxlex = MaxLex()
    ren = build_attestation_map(dirs)     # ruling 10: mirror the real pass
    for _fn, bk, ch, vs, raw in iter_source_lines(dirs):
        for t in iter_source_tokens(raw):
            if t["sbase"] == "G" + ARTICLE_BASE:
                keep(t["eng"])
        parsed = parse_abp_line("(%s %d:%d)  %s" % (bk, ch, vs, raw))
        if not parsed:
            continue
        for lex in (None, maxlex):
            for row in build_verse_words(list(parsed[3]), [], lex, ren=ren):
                if row[4] == ARTICLE_BASE:
                    keep(row[1])
    return sorted(seen)


def live_sizing_sql(dirs=None, db="~/bible-db/bible.db"):
    """A read-only one-liner JP can run on PA to size the class in a words table."""
    vals = ", ".join("'%s'" % s.replace("'", "''")
                     for s in article_only_renderings(dirs))
    return ("  sqlite3 %s \"SELECT count(*) FROM words "
            "WHERE strongs_base='G3588' AND english IS NOT NULL "
            "AND trim(lower(english)) NOT IN (%s);\"" % (db, vals))


def predict_vs(copydb, dirs=None):
    """THE SWAP CONDITION (2026-08-01, replaces the count window as the ruling
    check — the window's bins were measured on the bare layer and mispredicted
    live by ~770 rows; fourth layer-drift figure of the ride).

    Re-derives the expected leftover defect set on the TRUE layer — pronoun
    corrections + real lexicon + BH rows, exactly the build's inputs — keyed
    (book, chapter, verse, position), then requires MEMBER EQUALITY against
    the rebuilt copy's actual article-slot rows. Membership uses the same
    residue()/SUBSTANTIVAL predicate on both sides (no SQL NOT-IN list layer).
    PA only; read-only on every input."""
    import sqlite3 as _sq
    from build_words_from_abp import (RahlfsLXX, TAGNTSource, correct_verse,
                                      apply_pronoun_corrections,
                                      RAHLFS_DIR, TAGNT_FILES,
                                      load_lexicon, load_bh_verse_index,
                                      ABBREV_TO_SLUG)
    rahlfs = RahlfsLXX(RAHLFS_DIR) if (RahlfsLXX and RAHLFS_DIR.is_dir()) else None
    tagnt = (TAGNTSource([str(p) for p in TAGNT_FILES])
             if (TAGNTSource and all(p.is_file() for p in TAGNT_FILES)) else None)
    if not (rahlfs and tagnt):
        print("HALT: needs Rahlfs + TAGNT (PA only).")
        sys.exit(1)
    cc = _sq.connect("file:%s?mode=ro" % os.path.expanduser(copydb), uri=True)
    corr_lex = load_lexicon(cc)
    bs = _sq.connect("file:%s?mode=ro" % os.path.expanduser("~/bible-db/bh_scrape.db"), uri=True)
    bh_index = load_bh_verse_index(bs)
    bs.close()
    ren = build_attestation_map(dirs)
    print("inputs: lexicon %d · BH keys %d · attested numbers %d\n"
          % (len(corr_lex), len(bh_index), len(ren)))

    def is_defect(eng):
        eng = (eng or "").strip()
        if not eng:
            return False
        r = residue(eng)
        return bool(r) and not set(r) <= SUBSTANTIVAL

    predicted = set()
    _flag = []
    for _fn, bk, ch, vs, raw in iter_source_lines(dirs):
        parsed = parse_abp_line("(%s %d:%d)  %s" % (bk, ch, vs, raw))
        if not parsed:
            continue
        abp_words = parsed[3]
        src = bnum = None
        if rahlfs.booknum(bk):
            src, bnum = rahlfs, rahlfs.booknum(bk)
        elif tagnt.booknum(bk):
            src, bnum = tagnt, tagnt.booknum(bk)
        if src:
            corrs = correct_verse([w[1] for w in abp_words],
                                  src.verse(bnum, ch, vs),
                                  [w[0] for w in abp_words])
            abp_words = apply_pronoun_corrections(abp_words, corrs, _flag,
                                                  f"{bk} {ch}:{vs}")
        slug = ABBREV_TO_SLUG.get(bk)
        bh_rows = bh_index.get((slug, ch, vs), []) if slug else []
        for row in build_verse_words(list(abp_words), bh_rows, corr_lex, ren=ren):
            if row[4] == ARTICLE_BASE and is_defect(row[1]):
                predicted.add((bk, ch, vs, row[0]))

    # The SQL-list predicate (what the sizing one-liner counts) reproduced in
    # the same pass, so its count and the residue-predicate count are BRIDGED
    # by named members, never left as two unexplained figures (JP ruling).
    own_list = set(article_only_renderings(dirs))
    actual = set()
    sql_cnt = 0
    bridge = []
    for bk, ch, vs, pos, eng in cc.execute(
            "SELECT v.book, v.chapter, v.verse, w.position, w.english "
            "FROM words w JOIN verses v ON v.id = w.verse_id "
            "WHERE w.strongs_base = ?", ("G" + ARTICLE_BASE,)):  # DB stores the G prefix; build rows are bare
        d = is_defect(eng)
        if d:
            actual.add((bk, ch, vs, pos))
        if eng is not None and (eng or "").strip().lower() not in own_list:
            sql_cnt += 1
            if not d:
                bridge.append((bk, ch, vs, pos, (eng or "").strip()))
    cc.close()
    print("sizing-SQL count reproduced on the copy: %d "
          "(residue-predicate count below; the difference is the rows the "
          "bare-derived NOT-IN list never enumerated)" % sql_cnt)
    for m in bridge[:20]:
        print("   BRIDGE %-4s %3d:%-3d pos %-3d  %r  (article-own by residue, "
              "absent from the list)" % m)

    # DECLARED ALLOWANCE (2026-08-01 ride, every member attributed to a named
    # pinned step the per-verse prediction deliberately does not model):
    # fix_idios_own (finish-tail patch — relocates the 'own' phrase onto the
    # empty ἴδιος slot; these are exactly the G2398-unattested refusals the
    # ruling-10 pass correctly declined, repaired by the hand patch instead)
    # + apply_blank_strongs_fills (the documented 5-row numberless-"G." fill:
    # Act 24:8 'bidding'→G2753 splits its slot; Mat 12:14 'And the'→G3588
    # MINTS an article slot carrying non-own English). A residue differing
    # from this list BY ONE MEMBER is a FAIL.
    ALLOWED_MISS = {
        ("1Co", 3, 8, 10): "fix_idios_own",
        ("1Co", 4, 12, 3): "fix_idios_own",
        ("1Co", 7, 4, 15): "fix_idios_own",
        ("1Co", 11, 21, 2): "fix_idios_own",
        ("1Co", 14, 35, 7): "fix_idios_own",
        ("1Co", 15, 38, 12): "fix_idios_own",
        ("1Ti", 3, 5, 3): "fix_idios_own",
        ("1Ti", 4, 2, 4): "fix_idios_own",
        ("1Ti", 6, 1, 6): "fix_idios_own",
        ("2Pe", 2, 22, 10): "fix_idios_own",
        ("2Ti", 4, 3, 13): "fix_idios_own",
        ("Heb", 4, 10, 16): "fix_idios_own",
        ("Heb", 7, 27, 11): "fix_idios_own",
        ("Act", 24, 8, 0): "blank-G. fill (bidding->G2753 slot split)",
    }
    ALLOWED_EXTRA = {
        ("Mat", 12, 14, 0): "blank-G. fill (And the->G3588, minted slot)",
    }

    print("predicted leftover defect rows (true layer): %d" % len(predicted))
    print("actual rows in the rebuilt copy            : %d" % len(actual))
    miss = sorted(predicted - actual)
    extra = sorted(actual - predicted)
    print("predicted but ABSENT from the copy: %d (declared allowance %d)"
          % (len(miss), len(ALLOWED_MISS)))
    for m in miss[:40]:
        print("   MISS  %-4s %3d:%-3d pos %-3d  %s"
              % (m + (ALLOWED_MISS.get(m, "*** NOT IN THE ALLOWANCE ***"),)))
    print("in the copy but NOT predicted: %d (declared allowance %d)"
          % (len(extra), len(ALLOWED_EXTRA)))
    for m in extra[:40]:
        print("   EXTRA %-4s %3d:%-3d pos %-3d  %s"
              % (m + (ALLOWED_EXTRA.get(m, "*** NOT IN THE ALLOWANCE ***"),)))
    if set(miss) != set(ALLOWED_MISS) or set(extra) != set(ALLOWED_EXTRA):
        print("\nSET-EQUALITY: FAIL — the residue is not the declared allowance, "
              "member for member; do not swap.")
        sys.exit(1)
    print("\nSET-EQUALITY: PASS — the copy's defect set is the predicted set "
          "plus exactly the declared 15-member tail allowance.")


def live_diff(copydb, livedb, dirs=None):
    """MEMBER-level defect-set comparison (the swap's set-equality instrument,
    2026-08-01). The sizing COUNT is only the tripwire — this names every row
    that entered or left the defect set between live and the rebuilt copy, and
    shows what number live holds at each new entrant (a correction that moves
    a slot's number onto G3588 pulls the row INTO the count without any new
    defect existing — the third face of the corrected-layer drift this ride
    already paid for twice). Read-only on both databases."""
    own = set(article_only_renderings(dirs))

    def defects(path):
        c = sqlite3.connect("file:%s?mode=ro" % os.path.expanduser(path), uri=True)
        rows = {(v, p): e for v, p, e in c.execute(
            "SELECT verse_id, position, english FROM words "
            "WHERE strongs_base='G3588' AND english IS NOT NULL")
            if (e or "").strip().lower() not in own}
        return c, rows

    ca, A = defects(copydb)    # rebuilt copy
    cb, B = defects(livedb)    # live
    print("defect-set sizes: copy %d · live %d" % (len(A), len(B)))
    only_copy = sorted(A.keys() - B.keys())
    only_live = sorted(B.keys() - A.keys())
    print("rows only in the COPY's set (new entrants): %d" % len(only_copy))
    print("rows only in LIVE's set (left the set / repaired): %d" % len(only_live))

    ent = collections.Counter()
    for v, p in only_copy:
        lw = cb.execute("SELECT strongs_base, english FROM words "
                        "WHERE verse_id=? AND position=?", (v, p)).fetchone()
        ent[(lw[0] if lw else "NO-ROW", A[(v, p)].strip().lower())] += 1
    print("\nNEW ENTRANTS grouped by (live's number at that slot, english), top 40:")
    for (base, eng), n in ent.most_common(40):
        print("  %6d  live=%-8s %r" % (n, base, eng))

    left = collections.Counter(B[k].strip().lower() for k in only_live)
    print("\nLEFT THE SET (live english), top 40:")
    for eng, n in left.most_common(40):
        print("  %6d  %r" % (n, eng))
    ca.close(); cb.close()


# ── report ────────────────────────────────────────────────────────────────────

def print_lanes(bins, lanes):
    """The A/B repair-lane split (RULING 1) and the lane-B families (RULING 2)."""
    per = collections.Counter()
    for b in ("P", "R", "D"):
        for lane in lanes[b]:
            per[(b, lane)] += 1
    a_total = sum(n for (b, lane), n in per.items() if lane == LANE_A and b != "P")
    b_total = sum(n for (b, lane), n in per.items() if lane == LANE_B and b != "P")

    print("REPAIR LANES (ruling 2026-07-31 - the lane is 'is there a blank slot")
    print("beside it holding this word's number?', NOT function-vs-content)")
    print("  LANE A  blank slot adjacent - mechanical redistribution : %5d"
          % a_total)
    print("            of which bin D                               : %5d"
          % per[("D", LANE_A)])
    print("            of which bin R                               : %5d"
          % per[("R", LANE_A)])
    print("  LANE B  no blank slot - per-row triage, NO pass         : %5d"
          % b_total)
    print("            of which bin D                               : %5d"
          % per[("D", LANE_B)])
    print("            of which bin R                               : %5d"
          % per[("R", LANE_B)])
    if per[("P", LANE_A)] or per[("P", LANE_B)]:
        print("  (bin P is excluded from both - the build already repaired it: "
              "A %d / B %d)" % (per[("P", LANE_A)], per[("P", LANE_B)]))
    print()
    print("  DECLARED SPLIT: ~%d close by WRITING (lane A), ~%d by RULING or a"
          % (a_total, b_total))
    print("  curated write (lane B). A ship ABOVE %d means lane-B rows were"
          % a_total)
    print("  written without the row-level review - that is the alarm, not "
          "progress.")
    print()

    fam = collections.Counter()
    for b in ("D", "R"):
        for idx, lane in enumerate(lanes[b]):
            if lane == LANE_B:
                fam[family_of(bins[b][idx][4])] += 1
    supplied = sum(n for k, n in fam.items() if k in SUPPLIED_FAMILIES)
    print("  LANE B families (reporting only - a CLASS expectation spot-checked")
    print("  on 6 source rows, NEVER a per-row proof; nothing here closes a row):")
    for k, n in fam.most_common():
        print("     %5d  %s" % (n, k))
    print("     -----")
    print("     %5d  supplied-by-construction (the top three families)"
          % supplied)
    print("     %5d  need eyes on the row before any call" % (b_total - supplied))
    print()


def lane_manifest(bins, lanes, whys, lane):
    """The rows of one repair lane, in a fixed order, plus the hash pinning them.

    WHY THIS EXISTS: the lane split is a COUNT, and a count has no identity. The
    build-side fix reclassifies the rows it repairs (lane A -> bin P), so the
    pre-fix membership of lane A exists only BEFORE the fix lands and cannot be
    reconstructed after. Pinning the sorted row list and its hash turns the
    post-fix check into set identity - 'the build touched exactly these rows' -
    instead of arithmetic that a compensating pair of errors could satisfy.

    Bin P is excluded, matching print_lanes: the build already repaired those, so
    they are in no repair lane. Each row carries its SOURCE SLOT INDEX, which is
    what makes this a manifest rather than a tally: a verse can carry the same
    article-slot English twice (Mar 14:24 'the blood'), and without the slot those
    two rows are indistinguishable — the first pinned hash had exactly that hole.
    """
    rows = []
    for b in ("R", "D"):
        for idx, ln in enumerate(lanes[b]):
            if ln != lane:
                continue
            _fn, bk, ch, vs, eng, dotted, slot = bins[b][idx]
            rows.append((bk, int(ch), int(vs), slot, eng, dotted, b, whys[b][idx]))
    rows.sort()
    lines = ["%-4s %3d:%-3d slot %-3d  %-28s  %-10s  bin %s  %s" % r for r in rows]
    digest = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    return rows, lines, digest


def print_manifest(bins, lanes, whys, lane):
    """Print one lane's manifest: every row, the per-bin tally, and the hash."""
    rows, lines, digest = lane_manifest(bins, lanes, whys, lane)
    per_bin = collections.Counter(r[6] for r in rows)
    per_why = collections.Counter(r[7] for r in rows)

    print("LANE %s MANIFEST - the pinned row list, not a count" % lane)
    print("  book  ch:vs   slot     english                       number      bin  why")
    for ln in lines:
        print("  " + ln)
    print()
    print("  rows in lane %s                  : %5d" % (lane, len(rows)))
    for b in sorted(per_bin):
        print("    of which bin %s                : %5d" % (b, per_bin[b]))
    for w in sorted(per_why):
        print("    %-30s: %5d" % (w, per_why[w]))
    print()
    print("  SHA-256 of the sorted list        : %s" % digest)
    print("  Pin this hash BEFORE the fix. After the fix, a lane-%s row that is"
          % lane)
    print("  still in lane %s must be in this list, and the rows that left must"
          % lane)
    print("  be exactly the ones the build now reports in bin P.")
    print()


def print_plan(dirs=None, corrected=False):
    """RULING-10 SIZING — what the rewritten pass writes and refuses, per carrier,
    on the real attestation map. Run and PINNED BEFORE any rebuild (verdict-gate
    discipline: the expected picture exists before the build that must match it).

    Outcomes are per CARRIER (a carrier can log refusals for both neighbours);
    'unattested (threshold-only)' itemizes carriers whose moved words are all
    attested at min_verses=1 but not at 2 — the data that would revisit the
    threshold, per §6j point 2.

    TWO COUNTING BASES, both printed (2026-08-01 build-line reconciliation):
    the per-carrier view above, AND a per-ENTRY tally matching the build's own
    counters exactly (the build counts every logged decision — a carrier that
    writes one neighbour and refuses the other is 1 write + 1 refusal there,
    and 'star+unattested' entries land in their separate reason lines).

    corrected=True (PA ONLY — needs the Rahlfs/TAGNT files): applies the SAME
    pronoun corrections the real build applies before the pass, mirroring
    run()'s flow line for line. The 2026-08-01 build-line mismatch (923 written
    vs the pinned 929) is layer drift: this sizing measured the pass on RAW
    source lines while the build runs it on corrected verses. Corrected mode
    exists to reproduce the build's numbers member-by-member, read-only.
    """
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
            print("HALT: --corrected needs the Rahlfs + TAGNT files "
                  "(~/LXX-Rahlfs-1935, ~/TAGNT_*.txt — PA only). Without both, "
                  "this mode would silently measure the uncorrected layer again.")
            sys.exit(1)
        # The real build also runs with the lexicon + the scrape rows loaded —
        # 2 refusal entries proved lexicon/scrape-dependent on the 8/1
        # reconciliation run (409/386 bare vs the build's 411/388). Read-only.
        db_path = os.path.expanduser("~/bible-db/bible.db")
        bh_path = os.path.expanduser("~/bible-db/bh_scrape.db")
        for p in (db_path, bh_path):
            if not os.path.exists(p):
                print("HALT: --corrected needs %s (read-only) to mirror the "
                      "build's inputs." % p)
                sys.exit(1)
        _c = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
        corr_lex = load_lexicon(_c)
        _c.close()
        _s = sqlite3.connect("file:%s?mode=ro" % bh_path, uri=True)
        bh_index = load_bh_verse_index(_s)
        _s.close()
        slug_of = ABBREV_TO_SLUG
        print("corrected mode: Rahlfs + TAGNT + lexicon (%d) + BH index (%d) "
              "loaded — pass measured on the SAME layer, same inputs, as the "
              "real build.\n" % (len(corr_lex), len(bh_index)))
    ren = build_attestation_map(dirs)
    ren1 = build_attestation_map(dirs, min_verses=1)
    print("  attestation map: %d attested numbers\n" % len(ren))
    outcomes = collections.Counter()
    entry_writes = 0
    entry_refusals = collections.Counter()
    target_bases = collections.Counter()
    thresh_only = []
    writes = []
    refused = []
    _flag_log = []
    for _fn, bk, ch, vs, raw in iter_source_lines(dirs):
        carriers, _subst = source_carriers(raw)
        # The carriers-only skip is a SPEED shortcut valid on the raw layer
        # only: a pronoun correction can create a pass candidate on a verse
        # the raw scan sees no carrier in, so corrected mode walks every
        # verse (the 8/1 reconciliation's last-2-entries hypothesis).
        if not carriers and not corrected:
            continue
        line = "(%s %d:%d)  %s" % (bk, ch, vs, raw)
        log = []
        if corrected:
            parsed = parse_abp_line(line)
            if not parsed:
                continue
            abp_words = parsed[3]
            src = bnum = None
            if rahlfs.booknum(bk):                    # OT → Rahlfs
                src, bnum = rahlfs, rahlfs.booknum(bk)
            elif tagnt.booknum(bk):                   # NT → TAGNT
                src, bnum = tagnt, tagnt.booknum(bk)
            if src:
                corrs = correct_verse([w[1] for w in abp_words],
                                      src.verse(bnum, ch, vs),
                                      [w[0] for w in abp_words])
                abp_words = apply_pronoun_corrections(
                    abp_words, corrs, _flag_log, f"{bk} {ch}:{vs}")
            slug = slug_of.get(bk)
            bh_rows = bh_index.get((slug, ch, vs), []) if slug else []
            for _row in build_verse_words(list(abp_words), bh_rows, corr_lex,
                                          ren=ren, article_refusals=log):
                pass
        else:
            built_carriers(line, None, ren, log)
        for _c, _n, _b, reason, _m in log:
            if reason == "WRITTEN":
                entry_writes += 1
            else:
                entry_refusals[reason] += 1
        per = {}
        for cpos, npos, nbase, reason, moved in log:
            per.setdefault(cpos, []).append((npos, nbase, reason, moved))
        for cpos, entries in sorted(per.items()):
            reasons = {e[2] for e in entries}
            if "WRITTEN" in reasons:
                outcomes["WRITTEN"] += 1
                for npos, nbase, reason, moved in entries:
                    if reason == "WRITTEN":
                        target_bases[nbase] += 1
                        writes.append((bk, ch, vs, cpos, nbase,
                                       " ".join(moved)))
                continue
            outcomes["+".join(sorted(reasons))] += 1
            for npos, nbase, reason, moved in entries:
                refused.append((bk, ch, vs, cpos, reason, nbase or "*",
                                " ".join(moved)))
                if reason == "unattested" and moved and \
                        all(w in ren1.get(nbase, ()) for w in moved):
                    thresh_only.append((bk, ch, vs, cpos, nbase,
                                        " ".join(moved)))

    print("RULING-10 PLAN — the pass's decision record on the real map%s"
          % (" (CORRECTED layer)" if corrected else ""))
    print("  (per carrier slot that reached the neighbour test; a carrier")
    print("   with no blank candidate logs nothing and appears in no line)")
    for k, n in outcomes.most_common():
        print("    %6d  %s" % (n, k))
    print()
    print("  PER-ENTRY tally (the build's own counting basis — its Results")
    print("  line must match THESE numbers, not the per-carrier view):")
    print("    %6d  written" % entry_writes)
    print("    %6d  refusals (%s)" % (
        sum(entry_refusals.values()),
        ", ".join("%s %d" % (r, n) for r, n in entry_refusals.most_common())))
    print()
    print("  WRITE TARGETS (base -> writes):")
    for base, n in target_bases.most_common(15):
        print("    %6d  G%s" % (n, base))
    print()
    print("  THRESHOLD-ONLY refusals (single-token attested, but below the >=5")
    print("  distinct-verse floor — the threshold's own revisit list, §6j): %d"
          % len(thresh_only))
    for row in thresh_only:
        print("    %-4s %3d:%-3d slot %-3d  -> G%-6s  %r" % row)
    print()
    # FULL lists, deliberately — a capped sample is a silent cap on a receipt.
    print("  REFUSALS (every candidate the pass vetoed): %d" % len(refused))
    for row in refused:
        print("    %-4s %3d:%-3d slot %-3d  %-10s  G%-6s  %r" % row)
    print()
    print("  WRITES (the full decision record): %d" % len(writes))
    for row in writes:
        print("    %-4s %3d:%-3d slot %-3d  -> G%-6s  %r" % row)
    print()
    print("  TOTAL WRITES: %d" % len(writes))
    return writes, outcomes, thresh_only


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--controls", action="store_true",
                    help="run the controls only, print nothing else")
    ap.add_argument("--old", action="store_true",
                    help="replay the old predicate and show where its rows land")
    ap.add_argument("--list", dest="bin", choices=["P", "R", "D"],
                    help="print every row of one bin")
    ap.add_argument("--lanes", action="store_true",
                    help="print the A/B repair-lane split and the lane-B families")
    ap.add_argument("--manifest", choices=[LANE_A, LANE_B],
                    help="print one lane's full row list + the hash that pins it")
    ap.add_argument("--plan", action="store_true",
                    help="ruling-10 sizing: the pass's writes + typed refusals "
                         "on the real attestation map (pre-register BEFORE a rebuild)")
    ap.add_argument("--predict-vs", metavar="COPYDB",
                    help="THE SWAP CONDITION: re-derive the expected leftover "
                         "set on the true layer (corrections + lexicon + BH) "
                         "and require member equality with COPYDB (PA only)")
    ap.add_argument("--live-diff", nargs=2, metavar=("COPYDB", "LIVEDB"),
                    help="member-level defect-set diff between a rebuilt copy "
                         "and live (the swap's set-equality instrument); "
                         "read-only, then exit — no sweep")
    ap.add_argument("--sizing-sql", metavar="DBPATH",
                    help="print ONLY the read-only sizing one-liner targeting "
                         "DBPATH (list regenerated from this code's predicate), "
                         "then exit — no sweep")
    ap.add_argument("--corrected", action="store_true",
                    help="with --plan: apply the build's Rahlfs/TAGNT pronoun "
                         "corrections before the pass (PA only — reproduces the "
                         "real build line, read-only)")
    ap.add_argument("--prove-halt", action="store_true",
                    help="break a bin control on purpose and show the run halt")
    ap.add_argument("--prove-halt-lanes", action="store_true",
                    help="break a LANE control on purpose and show the run halt")
    args = ap.parse_args()

    if args.sizing_sql:
        print(live_sizing_sql(db=args.sizing_sql))
        return 0
    if args.live_diff:
        live_diff(args.live_diff[0], args.live_diff[1])
        return 0
    if args.predict_vs:
        predict_vs(args.predict_vs)
        return 0

    bins, lanes, whys, subst, totals = sweep()

    lane_controls = LANE_CONTROLS
    if args.prove_halt_lanes:
        # Re-declare the Act 20:15 'and' control as lane B. Its G1161 neighbour is
        # blank and present, so a working classifier MUST refuse.
        lane_controls = [c if not (c[0] == "Act" and c[4] == LANE_A)
                         else ("Act", 20, 15, "and", LANE_B,
                               "DELIBERATELY BROKEN (--prove-halt-lanes)")
                         for c in LANE_CONTROLS]
        print("--prove-halt-lanes: Act 20:15 'and' re-declared lane B. "
              "Expect a HALT.\n")

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
    ok = run_lane_controls(bins, lanes, lane_controls) and ok
    print()
    if not ok:
        print("HALT: a control went silent - the predicate changed. "
              "Do not trust any count from this run.")
        return 1
    if args.prove_halt or args.prove_halt_lanes:
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

    if args.lanes:
        print_lanes(bins, lanes)

    if args.manifest:
        print_manifest(bins, lanes, whys, args.manifest)

    if args.plan:
        print_plan(corrected=args.corrected)

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
        for fn, bk, ch, vs, eng, n, slot in bins[args.bin]:
            print("(%r, %r, %d, %d, %r, %r, %d)" % (fn, bk, ch, vs, eng, n, slot))
    return 0


if __name__ == "__main__":
    sys.exit(main())
