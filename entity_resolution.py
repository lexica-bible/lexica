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


def clean_summary(s):
    """TIPNR #Summary -> plain text. Unwraps <ref=..>X</ref> / <strong=..>X</strong>
    to their inner text, drops <br> and the leading '#', collapses whitespace."""
    if not s:
        return ""
    s = re.sub(r"<(?:ref|strong)[^>]*>(.*?)</(?:ref|strong)>", r"\1", s)
    s = re.sub(r"<br\s*/?>", " ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.lstrip("#").strip()
    return re.sub(r"\s+", " ", s)


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

# variant (already norm_name'd) -> canonical TIPNR name. Number-guarded downstream,
# so an imperfect entry can only floor, never mis-bind. Sourced from import_tipnr.py's
# curated ALIASES (its proven name-match knowledge) PLUS a hand-verified batch closing
# the residual the hand-check turned up (sor->tyre, libna->libnah, ...); every target
# was confirmed to exist in TIPNR. import_tipnr's DIRECT (name->Strong's) was NOT
# auto-folded — resolving a shared number to one entity head mis-fires (baalpeor->baal,
# bashemath->adah), and the hyphen compounds are handled by _compact instead. Keep this
# in step with import_tipnr.ALIASES on a future unification (tracked).
VARIANT_ALIASES = {
    'abijam': 'abijah',  'aholibamah': 'oholibamah',  'ajalon': 'aijalon',
    'aminadab': 'amminadab',  'ammonite': 'ammon',  'ammonites': 'ammon',
    'amorites': 'amorite',  'arabian': 'arabia',  'arabians': 'arabia',
    'ashdodite': 'ashdod',  'ashdodites': 'ashdod',  'assyrian': 'assyria',
    'assyrians': 'assyria',  'baalim': 'baal',  'babylonians': 'babylon',
    'baldad': 'bildad',  'bezaleel': 'bezalel',  'canaanite': 'canaan',
    'canaanites': 'canaan',  'carmelite': 'carmel',  'carmelites': 'carmel',
    'chaldean': 'chaldea',  'chaldeans': 'chaldea',  'cherethite': 'cherethites',
    'chittim': 'kittim',  'coniah': 'jehoiachin',  'cushite': 'cush',
    'cushites': 'cush',  'edomite': 'edom',  'edomites': 'edom',
    'egyptian': 'egypt',  'egyptians': 'egypt',  'elamite': 'elam',
    'elamites': 'elam',  'elias': 'elijah',  'elisaios': 'elisha',
    'enos': 'enosh',  'esaias': 'isaiah',  'esrom': 'hezron',
    'ethiopia': 'cush',  'ethiopian': 'cush',  'ethiopians': 'cush',
    'ezechias': 'hezekiah',  'ezion': 'ezion-geber',  'gadite': 'gad',
    'gadites': 'gad',  'gileadite': 'gilead',  'gileadites': 'gilead',
    'gittite': 'gath',  'gittites': 'gath',  'hadarezer': 'hadadezer',
    'hashub': 'hasshub',  'helkiah': 'hilkiah',  'hittite': 'heth',
    'hittites': 'heth',  'hivites': 'hivite',  'hodijah': 'hodiah',
    'israelite': 'israel',  'israelites': 'israel',  'jabish': 'jabesh',
    'jechoniah': 'jehoiachin',  'jechonias': 'jehoiachin',  'jeconiah': 'jehoiachin',
    'jeremias': 'jeremiah',  'jew': 'judah',  'jews': 'judah',
    'jezreelite': 'jezreel',  'jezreelites': 'jezreel',  'joatham': 'jotham',
    'josedech': 'jehozadak',  'josias': 'josiah',  'juda': 'judah',
    'kirjathaim': 'kiriathaim',  'kirjathjearim': 'kiriath-jearim',  'levite': 'levi',
    'levites': 'levi',  'libna': 'libnah',  'maachah': 'maacah',
    'maachathite': 'maacah',  'maachathites': 'maacah',  'mede': 'media',
    'medes': 'media',  'median': 'media',  'melchisedek': 'melchizedek',
    'michaiah': 'micaiah',  'midianite': 'midian',  'midianites': 'midian',
    'mizpeh': 'mizpah',  'mizraim': 'egypt',  'moabite': 'moab',  'moabites': 'moab',
    'naasson': 'nahshon',  'nabuzar-adan': 'nebuzaradan',  'nabuzar-ardan': 'nebuzaradan',
    'nabuzaradan': 'nebuzaradan',  'nabuzarardan': 'nebuzaradan',  'nazarene': 'nazareth',
    'negev': 'negeb',  'nethaneel': 'nethanel',  'netophathite': 'netophah',
    'netophathites': 'netophah',  'ozias': 'uzziah',  'pashur': 'pashhur',
    'persian': 'persia',  'persians': 'persia',  'pharez': 'perez',
    'pharisees': 'pharisee',  'philistine': 'philistia',  'philistines': 'philistia',
    'rama': 'ramah',  'sadducees': 'sadducee',  'salathiel': 'shealtiel',
    'sephela': 'shephelah',  'shilonite': 'shiloh',  'sidonian': 'sidon',
    'sidonians': 'sidon',  'sophar': 'zophar',  'sor': 'tyre',
    'tanis': 'zoan',  'tizrah': 'tirzah',  'urijah': 'uriah',
    'zachariah': 'zechariah',  'zacharias': 'zechariah',  'zara': 'zerah',
    'zarah': 'zerah',  'ziglag': 'ziklag',
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
    mixed_hdr = False   # current block header names BOTH person AND place (PERSON+PLACE)
    excluded = False    # current block is an EXCLUDED region (languages/titles/monsters)
    cur = None

    def close(c):
        if c:
            ents.append(c)

    for line in lines:
        if line.startswith("$=========="):
            close(cur); cur = None
            low = line.lower()
            excluded = "excluded" in low                          # F2: not real entities
            has_p, has_pl = "person" in low, "place" in low
            mixed_hdr = has_p and has_pl                          # F1: type must come from the row
            section = "person" if has_p else "place" if has_pl else "other"
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
            if excluded:                          # F2: EXCLUDED blocks are not bindable entities
                continue
            f0 = parts[0].strip()
            if "@" not in f0:
                continue
            head = norm_name(f0.split("@")[0])
            if not head or " " in head:           # F3: a name with a space is documentation prose
                continue
            # Main-record columns (legend lines 76 / 226):
            #   PERSON: 0 Name=uStrong | 1 Description | 2 Parents | 3 Siblings |
            #           4 Partners | 5 Offspring | 6 Tribe/Nation | 7 #Summary | 8 Type
            #   PLACE : 0 Name=uStrong | 1 OpenBible-near | 2 Founder | 3 People-there |
            #           4 GoogleMap | 5 Palopenmaps | 6 Geo-area | 7 #Summary | 8 Type
            # Binding uses ONLY spellings/bases/refs; desc/area/summary/gender are
            # card-display ENRICHMENT (the entity's own identity content).
            def _col(i):
                return parts[i].strip() if len(parts) > i else ""
            col8 = _col(8)                        # Type/gender field
            # F1: an entity's OWN row type beats the block header. A PERSON+PLACE header
            # names both, so header-first ("person") mislabeled every entity under it;
            # every such row carries "Place" in col 8. Fall back to the header only when
            # the row type is unrecognized — and if THAT happens inside a mixed block, we
            # cannot tell person from place, so STOP the build (the bug this closes).
            if col8 == "Place":
                row_section = "place"
            elif col8 in ("Male", "Female"):
                row_section = "person"
            else:
                if mixed_hdr:
                    raise ValueError(
                        "parse_tipnr: entity %r under a PERSON+PLACE header has "
                        "unrecognized type %r -- cannot resolve person/place from the "
                        "row. Fix the TIPNR source or extend the type map before building."
                        % (f0.split("=")[0].strip(), col8))
                row_section = section
            cur = {
                "head": head, "uniq": f0.split("=")[0].strip(), "section": row_section,
                "spellings": {head}, "bases": set(), "refs": set(),
                "parents": _col(2), "offspring": _col(5),
                "desc": _col(1),                 # person: human label; place: geo-near
                "area": _col(6),                 # Tribe/Nation (person) | Geo-area (place)
                "summary": clean_summary(_col(7)),
                "gender": col8 if col8 in ("Male", "Female") else "",
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


def _compact(s):
    """Hyphen/space-insensitive form: 'beth-shemesh' / 'beth shemesh' -> 'bethshemesh'.
    The corpus often writes a compound name solid where TIPNR hyphenates it."""
    return norm_name(s).replace("-", "").replace(" ", "")


def build_indexes(ents):
    """spelling -> {entity idx}; base Strong's -> {entity idx}; AND a compact
    (hyphen/space-stripped) index of the spellings that CARRY a hyphen/space — used
    only on the number-guarded fuzzy path, never the exact one (compacting can
    collide, e.g. 'baal-peor' the place vs 'baal' the god)."""
    from collections import defaultdict
    name_idx, base_idx, compact_idx = defaultdict(set), defaultdict(set), defaultdict(set)
    for i, e in enumerate(ents):
        for s in e["spellings"]:
            name_idx[s].add(i)
            c = _compact(s)
            if c and c != s:
                compact_idx[c].add(i)
        for b in e["bases"]:
            base_idx[b].add(i)
    return name_idx, base_idx, compact_idx


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


def bind_occurrence(ents, name_idx, base_idx, compact_idx, name, bk, ch, vs, base):
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
    #    normalization can over-match. Candidates = alias/gentilic variants AND the
    #    hyphen/space-insensitive (compact) match.
    fuzzy = set()
    cands = {i for cand in name_variants(n) for i in name_idx.get(cand, ())}
    cands |= compact_idx.get(_compact(n), set())
    # Skip a PLACE fuzzy-candidate when an exact-spelling PERSON entity carries the
    # SAME stored number. 'Cushi' (2Sa 18, a man) stems to the region 'Cush', which
    # lists the verse AND carries the gentilic number H3569 -> both guards pass and it
    # wrongly renders a PLACE card for a person. A same-name+same-number person exists
    # (Cushi@Zep.1.1, H3569), so this is a person-as-place mis-bind: floor it (Fix A).
    # Number-matched + exact-name-scoped -> can only floor, never mis-bind.
    person_same_num = bool(B) and any(
        ents[j]["section"] == "person" and B in ents[j]["bases"]
        for j in name_idx.get(n, ()))
    for i in cands:
        if person_same_num and ents[i]["section"] == "place":
            continue
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
