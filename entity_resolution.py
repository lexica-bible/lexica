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


# ── TIPNR rich parse ─────────────────────────────────────────────────────────
# Ported faithfully from probe_tipnr_fullset.parse_tipnr (the parse that produced
# the committed Issue-2 numbers) so the build path and the probe agree. Each entity
# keeps: headword name, ALL spellings (headword + sub UniqueNames + ESV/KJV/NIV
# translated tokens + Greek/Aramaic forms), ALL base Strong's, section, parents/
# offspring names, and the exhaustive reference set. `uniq` (Name@FirstRef) is the
# stable entity id.
def parse_tipnr(lines):
    ents = []
    section = "other"
    cur = None

    def close(c):
        if c:
            ents.append(c)

    for line in lines:
        if line.startswith("$=========="):
            close(cur); cur = None
            low = line.lower()
            section = "person" if "person" in low else "place" if "place" in low else "other"
            continue
        if not line.strip():
            continue
        stripped = line.lstrip()
        if stripped[:1] in ("=", "‖", "#", "*", "@") or stripped.startswith("UnifiedName") \
                or stripped.startswith("UniqueName"):
            continue
        is_sub = line[0] in (" ", "\t") or stripped.startswith("–")
        parts = line.split("\t")

        if not is_sub:
            close(cur); cur = None
            f0 = parts[0].strip()
            if "@" not in f0:
                continue
            head = norm_name(f0.split("@")[0])
            if not head:
                continue
            cur = {
                "head": head, "uniq": f0.split("=")[0].strip(), "section": section,
                "spellings": {head}, "bases": set(), "refs": set(),
                "parents": parts[2].strip() if len(parts) > 2 else "",
                "offspring": parts[5].strip() if len(parts) > 5 else "",
            }
            b = norm_base(f0.split("=", 1)[1]) if "=" in f0 else ""
            if b:
                cur["bases"].add(b)
        else:
            if not cur:
                continue
            # sub-record: col1 = UniqueName (AltName@..), col2 = dStrong«eStrong,
            # col3 = translated name (ESV,KJV,NIV). Mine spellings + base + refs.
            if len(parts) > 1 and "@" in parts[1]:
                cur["spellings"].add(norm_name(parts[1].split("@")[0]))
            if len(parts) > 2 and "«" in parts[2]:
                b = norm_base(parts[2].split("«")[0])
                if b:
                    cur["bases"].add(b)
            if len(parts) > 3 and parts[3].strip():
                for tok in re.split(r"[,/()]", parts[3]):
                    w = norm_name(tok)
                    if w and re.match(r"^[a-z][a-z' -]+$", w):
                        cur["spellings"].add(w)
            ref_blob = None
            for i, f in enumerate(parts):
                if "reference=" in f:
                    ref_blob = parts[i + 1] if i + 1 < len(parts) else f.split("reference=", 1)[1]
                    break
            if ref_blob:
                for tok in ref_blob.split(";"):
                    r = parse_ref(tok)
                    if r:
                        cur["refs"].add(r)
    close(cur)
    return ents


def build_indexes(ents):
    """spelling -> {entity idx}, base Strong's -> {entity idx}."""
    from collections import defaultdict
    name_idx, base_idx = defaultdict(set), defaultdict(set)
    for i, e in enumerate(ents):
        for s in e["spellings"]:
            name_idx[s].add(i)
        for b in e["bases"]:
            base_idx[b].add(i)
    return name_idx, base_idx


# ── The binder + global render rule ──────────────────────────────────────────
# Objective: rendered-and-correct with ZERO confident-wrong. The render rule is the
# spine — a bind RENDERS only when the clicked verse corroborates it (the verse is in
# the bound entity's reference list, after the versification map). Otherwise it FLOORS
# (Fix A handles the floor). A number-only link (no name match) is the confident-wrong
# path and NEVER renders; ≥2 same-name entities at one verse FLOOR as HOT (hand-check).
class Bind:
    __slots__ = ("entity", "kind", "rule", "render", "hot", "candidates")

    def __init__(self, entity=None, kind="none", rule="", render=False, hot=False,
                 candidates=None):
        self.entity = entity            # bound entity idx, or None when floored
        self.kind = kind                # exact|fuzzy|versification|multi|number_only|none
        self.rule = rule                # versification rule name, when kind=versification
        self.render = render            # True = render the bound entity; False = floor
        self.hot = hot                  # flagged for hand-verification
        self.candidates = candidates or []   # colliding entity idxs (multi / number_only)

    def __repr__(self):
        return (f"Bind(entity={self.entity}, kind={self.kind!r}, rule={self.rule!r}, "
                f"render={self.render}, hot={self.hot}, candidates={self.candidates})")


def _verse_in_entity(ent, bk, ch, vs):
    """(True, '') if the entity lists this verse directly; (True, rule) if it lists a
    DOCUMENTED versification remap of it (WS1 — serves every tier); (False, None) else.
    The remap is a pure correct-bind recovery: the entity is already the right one,
    only the verse number moved."""
    if (bk, ch, vs) in ent["refs"]:
        return True, ""
    for (b2, c2, v2, rule) in documented_remaps(bk, ch, vs):
        if (b2, c2, v2) in ent["refs"]:
            return True, rule
    return False, None


def bind_occurrence(ents, name_idx, base_idx, name, bk, ch, vs, base):
    """Decide the bind for one proper-noun occurrence. Verse-primary, name-first.

    name : the printed surface label (will be norm_name'd)
    bk/ch/vs : canonical book number + chapter + verse of the click
    base : the stored strongs_base (metadata behind the name link)

    Returns a Bind. render=True only on a single corroborated name match (exact, or
    fuzzy WITH number agreement, possibly via a documented versification offset)."""
    n = norm_name(name)
    B = norm_base(base)
    if bk is None:
        return Bind(kind="none")

    # 1. EXACT name + verse (number is just metadata here). Versification serves it.
    exact, exact_rule = [], ""
    for i in name_idx.get(n, ()):
        ok, rule = _verse_in_entity(ents[i], bk, ch, vs)
        if ok:
            exact.append(i)
            if rule and not exact_rule:
                exact_rule = rule
    if exact:
        if len(set(exact)) == 1:
            kind = "versification" if exact_rule else "exact"
            return Bind(entity=exact[0], kind=kind, rule=exact_rule, render=True)
        # ≥2 distinct same-name entities list this verse -> never guess. Floor, HOT.
        return Bind(kind="multi", hot=True, candidates=sorted(set(exact)))

    # 2. FUZZY name + verse — only with the SECOND key (stored number agrees), since
    #    normalization can over-match.
    fuzzy = set()
    for cand in name_variants(n):
        for i in name_idx.get(cand, ()):
            ok, _ = _verse_in_entity(ents[i], bk, ch, vs)
            if ok and B and B in ents[i]["bases"]:
                fuzzy.add(i)
    if fuzzy:
        if len(fuzzy) == 1:
            return Bind(entity=next(iter(fuzzy)), kind="fuzzy", render=True)
        return Bind(kind="multi", hot=True, candidates=sorted(fuzzy))

    # 3. NUMBER-only (base matches a verse, but no name link at all) -> the
    #    confident-wrong path. Floor; surface for the residual hand-check.
    if B:
        numonly = sorted(i for i in base_idx.get(B, ()) if (bk, ch, vs) in ents[i]["refs"])
        if numonly:
            return Bind(kind="number_only", candidates=numonly)

    # 4. nothing corroborates -> floor (referent-known / genuine miss).
    return Bind(kind="none")
