#!/usr/bin/env python3
"""
entity_resolution.py — the shared proper-noun / entity-resolution engine (Issue 2).

ONE source of truth for the rebuild, so the build script, the read-only probes, and
any future caller can't drift apart. Pure logic, no database (like argmap.py): it is
fed TIPNR entities + a list of proper-noun occurrences and decides, per occurrence,
which TIPNR entity it binds to and whether that bind may RENDER.

Design is fixed by entity_resolution_rebuild.md (Issue 2) — do not re-open here.
Objective: rendered-and-correct with ZERO confident-wrong. A wrong bind (real bio
under the wrong entity) is weighted a LOSS, so the engine floors rather than guesses.

Pieces, in build order (the brief's last section):
  WS1  documented_remaps()   — versification map (THIS file, below). Standalone.
  WS2  name normalization    — gentilic + KJV/LXX transliteration  (added next)
  WS3  residual verification — hand-check step, not code
  ---  parse_tipnr / binder  — added with step 3

This module currently implements the shared book/name helpers + the WS1 map.
"""

import re

# ── Canonical book number for EVERY abbreviation we might see ────────────────
# ABP's verses.book (Eze/Joe/Mar/Joh/Son/Rth) AND TIPNR's (Ezk/Jol/Mrk/Jhn/Sng/Rut)
# both map here, so a reference compares by NUMBER and a spelling difference never
# looks like a miss. Lifted verbatim from the probes (probe_tipnr_fullset.py /
# probe_tipnr_binding.py) so the production path and the validation probes agree.
_BOOK_VARIANTS = [
    (1, "gen"), (2, "exo exod"), (3, "lev"), (4, "num"), (5, "deu deut"),
    (6, "jos josh"), (7, "jdg judg"), (8, "rth rut ruth"), (9, "1sa 1sam"),
    (10, "2sa 2sam"), (11, "1ki 1kgs"), (12, "2ki 2kgs"), (13, "1ch 1chr"),
    (14, "2ch 2chr"), (15, "ezr ezra"), (16, "neh"), (17, "est esth"), (18, "job"),
    (19, "psa psalm pss"), (20, "pro prov"), (21, "ecc eccl"), (22, "son sng sos song"),
    (23, "isa"), (24, "jer"), (25, "lam"), (26, "eze ezk ezek"), (27, "dan"),
    (28, "hos"), (29, "joe jol joel"), (30, "amo amos"), (31, "oba obad"),
    (32, "jon jonah"), (33, "mic"), (34, "nah nam nahum"), (35, "hab"), (36, "zep zeph"),
    (37, "hag"), (38, "zec zech"), (39, "mal"), (40, "mat matt"), (41, "mar mrk mark"),
    (42, "luk luke"), (43, "joh jhn john"), (44, "act acts"), (45, "rom"),
    (46, "1co 1cor"), (47, "2co 2cor"), (48, "gal"), (49, "eph"), (50, "php phil"),
    (51, "col"), (52, "1th 1thess"), (53, "2th 2thess"), (54, "1ti 1tim"),
    (55, "2ti 2tim"), (56, "tit titus"), (57, "phm phlm"), (58, "heb"),
    (59, "jas james"), (60, "1pe 1pet"), (61, "2pe 2pet"), (62, "1jn 1jo 1john"),
    (63, "2jn 2jo"), (64, "3jn 3jo"), (65, "jud jude"), (66, "rev"),
]
BOOKNUM = {}
for _n, _abbrs in _BOOK_VARIANTS:
    for _a in _abbrs.split():
        BOOKNUM[_a] = _n


def book_num(abbrev):
    """ABP/TIPNR book abbreviation -> canonical 1..66, or None if unknown."""
    return BOOKNUM.get((abbrev or "").strip().lower())


# ── Name + Strong's normalization (shared) ──────────────────────────────────
def norm_name(s):
    """Lower-case, strip trailing punctuation/dashes. Matches the probes + the
    app's clickable-label cleanup (extractProperName)."""
    if not s:
        return ""
    return re.sub(r"[\s,.:;!?'\"–\-]+$", "", s.strip()).lower()


def norm_base(s):
    """'H0175A' / 'G0002' -> 'H175' / 'G2'. '' if not parseable. The lexicon-join
    invariant form (strongs_base is fully G/H-prefixed)."""
    m = re.match(r"^([GH])0*(\d+)", (s or "").strip())
    return f"{m.group(1)}{int(m.group(2))}" if m else ""


def parse_ref(tok):
    """A TIPNR reference token 'Ezk.31.18a' -> (book_num, chap, verse), or None.
    Strips an 'LXX ' prefix and a verse-letter/range suffix (takes the start verse)."""
    tok = re.sub(r"^LXX\s*", "", (tok or "").strip())
    if not tok:
        return None
    parts = tok.split(".")
    if len(parts) < 3:
        return None
    bk = BOOKNUM.get(parts[0].strip().lower())
    if bk is None:
        return None
    cm = re.match(r"\d+", parts[1].strip())
    vm = re.match(r"\d+", parts[2].strip())
    if not cm or not vm:
        return None
    return (bk, int(cm.group()), int(vm.group()))


# ── WS1 — documented versification map ──────────────────────────────────────
# DERIVE the offset from DOCUMENTED Hebrew/Greek-vs-English numbering differences
# ONLY. The deltas seen in the data merely VALIDATE — a candidate remap counts only
# when it lands on a SAME-NAME entity's reference (the binder enforces that). A rule
# encoded wrong simply won't land -> the occurrence floors; it can never produce a
# false recovery. Everything with no NAMED documented rule floors as the
# "referent-known, not-named" class (Lev / Est / Lam / hidden-offset flags), by
# design — binding an unnamed word is the fabrication we kill.
#
# Recovered on the live corpus = 117 (probe_tipnr_fullset.py, re-run on PA to confirm):
#   Psa  superscription : 116  — Hebrew/LXX counts the title as v1, so an English
#                                body verse is the Hebrew verse + 1. Candidate +1.
#   Num  16/17          :   1  — English 16:36-50 == Hebrew 17:1-15 (the Korah
#                                section). ABP follows Hebrew numbering there.
#   Mal  3/4            :   0  — English 4:1-6 == Hebrew 3:19-24. Documented + valid,
#                                but no proper-noun lands on it; kept because it can
#                                only ever recover, never mis-bind.
#
# Kept byte-for-byte in step with probe_tipnr_fullset.doc_remaps so the production
# map and the validation probe never diverge. Adding a book here re-opens a CLOSED
# design decision — don't, unless the documented difference can be named AND landed.
def documented_remaps(bk, ch, vs):
    """Given a text reference (canonical book number `bk`, chapter, verse), return a
    list of candidate (bk, ch, vs, rule) the binder should also test against an
    entity's English-numbered reference list. Empty list = no documented offset
    (the occurrence floors unless it already binds at its own verse)."""
    out = []
    if bk == 19:            # Psalms
        out.append((19, ch, vs + 1, "Psa:superscription"))
    elif bk == 4:           # Numbers 16/17 (Korah)
        if ch == 17 and vs <= 15:
            out.append((4, 16, vs + 35, "Num16/17"))
        elif ch == 17:
            out.append((4, 17, vs - 15, "Num16/17"))
    elif bk == 39:          # Malachi 3/4
        if ch == 3 and vs >= 19:
            out.append((39, 4, vs - 18, "Mal3/4"))
    return out


# ── WS2 — name normalization (gentilic + KJV/LXX transliteration) ────────────
# ONE lever. A surface name the corpus prints ("Cushi", "Pharez", "Cushites") often
# isn't a TIPNR headword/spelling, so today it falls onto the polluted stored-number
# path. Normalization expands it to the entity's real name so it can bind by
# NAME+VERSE (robust) instead. These are FUZZY matches — the binder requires the
# stored number to ALSO sit in the entity's cluster before it renders one (fuzzy can
# over-match), so an over-broad stem here floors, never mis-binds.
#
# Two parts:
#   1. Algorithmic gentilic stemming  — strip the Hebrew/English gentilic endings
#      (-ites/-ite/-itess/-im/-i/-s) to reach the root place/person. General, so it
#      covers the long tail (cushite/cushites/cushi -> cush, moabite -> moab) without
#      a hand list.
#   2. VARIANT_ALIASES — the IRREGULAR cases stemming can't reach: KJV/LXX/Greek
#      spellings (pharez->perez, salathiel->shealtiel) and translated names
#      (mizraim->egypt). Seeded with the brief's named canaries + the clearly-valuable
#      spelling variants; import_tipnr.py keeps a fuller curated map for its own match
#      pass — reconcile the two when the binder is wired (a follow-up, tracked).

# variant (already norm_name'd) -> canonical TIPNR name. Number-guarded downstream.
VARIANT_ALIASES = {
    # --- the brief's named canaries (WS2/WS3) ---
    "pharez": "perez",           # KJV -> Hebrew
    "jeconiah": "jehoiachin", "jechoniah": "jehoiachin", "jechonias": "jehoiachin",
    "coniah": "jehoiachin",
    "salathiel": "shealtiel",    # LXX/Greek -> Hebrew
    "mizraim": "egypt",          # Hebrew name -> English place
    # --- high-value non-gentilic spelling variants (KJV/LXX vs Hebrew) ---
    "juda": "judah", "esrom": "hezron", "zara": "zerah", "zarah": "zerah",
    "enos": "enosh", "sophar": "zophar", "rama": "ramah", "aminadab": "amminadab",
    "naasson": "nahshon", "urijah": "uriah", "michaiah": "micaiah",
    "nabuzaradan": "nebuzaradan", "helkiah": "hilkiah", "bezaleel": "bezalel",
    "josedech": "jehozadak", "baldad": "bildad", "nethaneel": "nethanel",
    "hadarezer": "hadadezer", "elias": "elijah", "esaias": "isaiah",
    "jeremias": "jeremiah", "ezechias": "hezekiah", "ozias": "uzziah",
    "josias": "josiah", "joatham": "jotham", "zacharias": "zechariah",
    "zachariah": "zechariah", "melchisedek": "melchizedek", "abijam": "abijah",
    # --- irregular gentilics stemming can't reach (root != stripped stem) ---
    "jew": "judah", "jews": "judah", "hittite": "heth", "hittites": "heth",
    "ethiopia": "cush", "ethiopian": "cush", "ethiopians": "cush",
    "levite": "levi", "levites": "levi", "mede": "media", "medes": "media",
}

# Ordered longest-first so '-itess'/'-ites' win before '-ite'/'-s', and the broad
# '-i'/'-s' fire last. Each yields ONE candidate root if the remainder is long enough.
_GENTILIC_SUFFIXES = ("itesses", "itess", "ites", "ite", "im", "i", "s")
_MIN_ROOT = 3   # don't stem down to a 1-2 char fragment that hits noise


def gentilic_roots(name):
    """Surface gentilic/plural -> candidate root name(s). 'cushites'->{'cush'},
    'cushi'->{'cush'}, 'moabite'->{'moab'}. A SET (a name can match >1 suffix)."""
    n = norm_name(name)
    roots = set()
    for suf in _GENTILIC_SUFFIXES:
        if n.endswith(suf) and len(n) - len(suf) >= _MIN_ROOT:
            roots.add(n[: -len(suf)])
    roots.discard(n)
    return roots


def name_variants(name):
    """All FUZZY canonical candidates for a surface name (the exact norm_name is NOT
    included — the binder tries that first, unguarded; everything here is number-
    guarded). Union of the alias map and gentilic stems, plus the alias of a stem
    (e.g. 'cushites' -> stem 'cush'; 'hittites' -> stem 'hittite' -> alias 'heth')."""
    n = norm_name(name)
    out = set()
    mapped = VARIANT_ALIASES.get(n)
    if mapped:
        out.add(mapped)
    for r in gentilic_roots(n):
        out.add(r)
        if r in VARIANT_ALIASES:
            out.add(VARIANT_ALIASES[r])
    out.discard(n)
    out.discard("")
    return out
