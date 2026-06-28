#!/usr/bin/env python3
"""
build_words_from_abp.py

Rebuilds the words table using ABP text files for word order and glosses,
with BH scrape as a metadata overlay (italic_words, smcap_words, greek_pos).

Bracket groups and word order within brackets are derived from ABP position
numbers ([1word 2word 3word]) — not from BH greek_pos, which is unreliable
for this purpose.

Run on PythonAnywhere:
    python scripts/build_words_from_abp.py [bible.db] [bh_scrape.db]
    python scripts/build_words_from_abp.py --test [--book Gen] [--chapter 1] [--verse 1]
"""

import re
import sys
import shutil
import sqlite3
import zipfile
from pathlib import Path

try:
    sys.path.insert(0, str(Path(__file__).parent))
    from parse_abp import _head_word, _FUNCTION_WORDS, _HEAD_STOP
except ImportError:
    _ARTICLES = frozenset({"the", "a", "an"})
    _FUNCTION_WORDS = frozenset()
    _HEAD_STOP = frozenset()

    def _head_word(text, italic_words=None):
        if not text:
            return None
        skip = {w.strip().lower() for w in italic_words} if italic_words else set()
        words = re.sub(r"[^\w]", " ", text).split()

        def pick(drop):
            for w in words:
                lw = w.lower()
                if lw in _ARTICLES:
                    continue
                if drop and lw in skip:
                    continue
                return w
            return None
        if skip:
            h = pick(True)
            if h is not None:
                return h
        return pick(False) or (words[0] if words else None)


try:
    from lxx_align import RahlfsLXX, TAGNTSource, correct_verse
    # _EN_BUCKET (gloss-person table) + _last_en_word power the g1473-gloss fold below
    from lxx_align import _EN_BUCKET as _G1473_BUCKET, _last_en_word as _g1473_last
except ImportError:
    RahlfsLXX = TAGNTSource = None
    _G1473_BUCKET = _g1473_last = None

try:
    # The 5 ABP words ABP left with a blank "G." number — filled as a finishing step so a
    # rebuild reproduces the fix (see fill_blank_strongs.py for the table + rationale).
    from fill_blank_strongs import apply_blank_strongs_fills
except ImportError:
    apply_blank_strongs_fills = None

try:
    # Subject NAMES merged onto their verb's cell ("David took" on λαμβάνω, the name's
    # own G* slot left empty) — split back out so the name is its own clickable word.
    # Folded as a finishing step (needs the tipnr roster + G-prefixed bases, both present
    # after copy-first) so a rebuild reproduces it. See fix_pn_subject_merge.py.
    from fix_pn_subject_merge import run as apply_pn_subject_split
except ImportError:
    apply_pn_subject_split = None

BASE_DIR    = Path(__file__).parent.parent
ABP_OT_ZIP  = BASE_DIR / "abp_ot_texts.zip"
ABP_NT_ZIP  = BASE_DIR / "abp_nt_texts.zip"
ABP_OT_DIR  = BASE_DIR / "abp_texts" / "abp_ot_texts"
ABP_NT_DIR  = BASE_DIR / "abp_texts" / "abp_nt_texts"
RAHLFS_DIR  = Path.home() / "LXX-Rahlfs-1935"   # 4 data files fetched separately on PA; not in git
TAGNT_FILES = [Path.home() / "TAGNT_Mat-Jhn.txt",
               Path.home() / "TAGNT_Act-Rev.txt"]  # STEPBible TAGNT (CC-BY); fetched on PA, not in git

ABBREV_TO_SLUG = {
    "Gen": "genesis",        "Exo": "exodus",          "Lev": "leviticus",
    "Num": "numbers",        "Deu": "deuteronomy",      "Jos": "joshua",
    "Jdg": "judges",         "Rth": "ruth",             "1Sa": "1_samuel",
    "2Sa": "2_samuel",       "1Ki": "1_kings",          "2Ki": "2_kings",
    "1Ch": "1_chronicles",   "2Ch": "2_chronicles",     "Ezr": "ezra",
    "Neh": "nehemiah",       "Est": "esther",           "Job": "job",
    "Psa": "psalms",         "Pro": "proverbs",         "Ecc": "ecclesiastes",
    "Son": "songs",          "Isa": "isaiah",           "Jer": "jeremiah",
    "Lam": "lamentations",   "Eze": "ezekiel",          "Dan": "daniel",
    "Hos": "hosea",          "Joe": "joel",             "Amo": "amos",
    "Oba": "obadiah",        "Jon": "jonah",            "Mic": "micah",
    "Nah": "nahum",          "Hab": "habakkuk",         "Zep": "zephaniah",
    "Hag": "haggai",         "Zec": "zechariah",        "Mal": "malachi",
    "Mat": "matthew",        "Mar": "mark",             "Luk": "luke",
    "Joh": "john",           "Act": "acts",             "Rom": "romans",
    "1Co": "1_corinthians",  "2Co": "2_corinthians",    "Gal": "galatians",
    "Eph": "ephesians",      "Php": "philippians",      "Col": "colossians",
    "1Th": "1_thessalonians","2Th": "2_thessalonians",  "1Ti": "1_timothy",
    "2Ti": "2_timothy",      "Tit": "titus",            "Phm": "philemon",
    "Heb": "hebrews",        "Jas": "james",            "1Pe": "1_peter",
    "2Pe": "2_peter",        "1Jn": "1_john",           "2Jn": "2_john",
    "3Jn": "3_john",         "Jud": "jude",             "Rev": "revelation",
}

_STRONGS_RE  = re.compile(r"(G\*|G\d+(?:\.\d+)*)")
_VERSE_RE    = re.compile(r"^\((\w+)\s+(\d+):(\d+)\)\s+(.*)")
_STRIP_PUNCT = re.compile(r"[^\w\s]")
_WORD_NUM    = re.compile(r"(?<!\w)\d+")
_LEAD_NUM    = re.compile(r"^\d+")
_NUM_PIECE   = re.compile(r"(?<![\w.])\d+(?=[A-Za-z])")  # an ABP position number leading a word


# ── Parsing ───────────────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    return _STRIP_PUNCT.sub("", text or "").lower().strip()


def clean_english(text: str) -> str:
    """Strip ABP bracket chars and position numbers from a gloss token."""
    t = text.strip()
    t = t.replace("[", "").replace("]", "")
    t = _WORD_NUM.sub("", t)
    return t.strip()


def bracket_info(raw: str):
    """
    Extract bracket metadata from a raw (pre-clean) token text.
    Returns (abp_pos, opens_bracket, closes_bracket).

    '[2was not'  → (2, True,  False)
    '1That one]' → (1, False, True)
    ' 3light'    → (3, False, False)
    'God made'   → (None, False, False)
    ''           → (None, False, False)
    """
    opens  = "[" in raw
    closes = "]" in raw
    # Strip surrounding whitespace, brackets, and trailing punctuation so the
    # leading position number (e.g. "1 the second]." → "1") is always reachable.
    s = re.sub(r"[^\w\s]", "", raw.strip().lstrip("[")).strip()
    m = _LEAD_NUM.match(s)
    abp_pos = int(m.group()) if m else None
    return abp_pos, opens, closes


def _split_numbered(mid: str):
    """Split a bracket-interior gloss that carries MORE THAN ONE ABP position number
    into one piece per number — so a single Greek word whose English is spread across
    two reorder slots ('1Was 5justified]' for ἐδικαιώθη; '1let 3have]' for ἐχέτω)
    keeps BOTH slot numbers instead of collapsing onto the first.

    Returns [mid] unchanged when there are 0 or 1 position numbers, so every
    unaffected verse parses byte-for-byte as before. Any text before the first number
    (a leading '[' or a peeled-off helper) rides along on the first piece; the '['/']'
    markers stay on whichever piece holds them.
        "1Was 5justified],"  -> ["1Was ", "5justified],"]
        "[2let 6boast"       -> ["[2let ", "6boast"]
        "1may 5search 7out"  -> ["1may ", "5search ", "7out"]
    (Jas 2:21 / Job 3:4 class — 321 spots canon-wide where ABP wraps one verb's
    English around the subject; the old single-number read dropped the later slot.)
    """
    cuts = [m.start() for m in _NUM_PIECE.finditer(mid)][1:]  # split BEFORE each number after the 1st
    if not cuts:
        return [mid]
    pieces, prev = [], 0
    for c in cuts:
        pieces.append(mid[prev:c]); prev = c
    pieces.append(mid[prev:])
    return pieces


def _emit_words(raw: str, strongs):
    """
    Expand ONE (gloss, strongs) chunk into 1-3 words, peeling gloss text the SOURCE
    places OUTSIDE the bracket markers so '[' / ']' land on the right word.

    A helper word that shares the bracketed verb's single Strong's number (nothing
    separates them) lands in the SAME chunk as the verb — e.g. "May [2be found" or
    "1may] be found". Left whole, the '[' swallows "May" and the source's position
    number is lost. Peel it back out, keeping the SAME Strong's (it is the same
    Greek word) and sitting OUTSIDE the bracket:
        "May [2be found"  -> "May" (outside)        + "[2be found" (opens, pos 2)
        "1may] be found"  -> "1may]" (closes, pos 1) + "be found"  (outside)
    A chunk with no straddling text is returned unchanged, so every unaffected verse
    parses byte-for-byte as before. (Psa 21:8 lesson — the helper-word/bracket
    problem; ~943 verses across the canon. The peeled word's abp_pos is None and it
    opens/closes nothing, so the bracket state machine leaves it outside; the bracket
    word keeps the source position number via bracket_info.)
    """
    lead = trail = None
    mid = raw
    if "[" in mid:
        k = mid.index("[")
        if re.search(r"[A-Za-z]", mid[:k]):          # real words BEFORE the '['
            lead, mid = mid[:k], mid[k:]
    if "]" in mid:
        k = mid.index("]")
        if re.search(r"[A-Za-z]", mid[k + 1:]):      # real words AFTER the ']'
            trail, mid = mid[k + 1:], mid[:k + 1]

    out = []
    if lead is not None:                             # outside, before the bracket
        out.append((clean_english(lead), strongs, None, False, False))
    for piece in _split_numbered(mid):               # one word per ABP slot (verb split over 2+ slots)
        ap, ob, cb = bracket_info(piece)             # each piece keeps its own marker + number
        out.append((clean_english(piece), strongs, ap, ob, cb))
    if trail is not None:                            # outside, after the bracket
        out.append((clean_english(trail), strongs, None, False, False))
    return out


def parse_abp_line(line: str):
    """
    Returns (abbrev, chapter, verse, words) or None.
    words = [(english, strongs_raw, abp_pos, opens_bracket, closes_bracket), ...]

    Each (gloss, strongs) chunk goes through _emit_words, which peels a helper word
    glued onto a bracketed verb back outside the bracket (Psa 21:8 lesson).
    """
    m = _VERSE_RE.match(line.strip())
    if not m:
        return None
    book    = m.group(1)
    chapter = int(m.group(2))
    verse   = int(m.group(3))
    text    = m.group(4)

    parts = _STRONGS_RE.split(text)
    words = []
    i = 0
    while i < len(parts) - 1:
        words.extend(_emit_words(parts[i], parts[i + 1]))
        i += 2
    if parts and parts[-1].strip():
        words.extend(_emit_words(parts[-1], None))
    return book, chapter, verse, words


def iter_source_tokens(text):
    """Canonical PEELED source tokenization, shared with the bracket audits so they
    can never drift from the build's bracket boundaries. Mirrors parse_abp_line
    exactly (same _emit_words helper-peel + bracket state machine). Yields one dict
    per source word:
        eng     clean_english'd gloss (may be '')
        sbase   source Strong's in strongs_base form ('G2962'/'G1249'/'*'/'')
        abp_pos source position number (None outside a numbered slot)
        br      1-based source bracket index the word sits in (None = outside)
        src_i   0-based source reading-order index
    """
    parts = _STRONGS_RE.split(text)
    pairs = []
    i = 0
    while i < len(parts) - 1:
        pairs.append((parts[i], parts[i + 1]))
        i += 2
    if parts and parts[-1].strip():
        pairs.append((parts[-1], None))

    in_bracket = False
    br = src_i = 0
    for raw, strongs in pairs:
        for eng, st, abp_pos, opens, closes in _emit_words(raw, strongs):
            if opens and not in_bracket:
                br += 1
                in_bracket = True
            cur_br = br if in_bracket else None
            if closes:
                in_bracket = False
            if not st:
                sbase = ""
            elif st == "G*":
                sbase = "*"
            else:
                sbase = st.split(".")[0]
            yield {"eng": eng, "sbase": sbase, "abp_pos": abp_pos,
                   "br": cur_br, "src_i": src_i}
            src_i += 1


def _abp_sources():
    """Return directory paths if present, otherwise fall back to zip files."""
    ot = ABP_OT_DIR if ABP_OT_DIR.is_dir() else ABP_OT_ZIP
    nt = ABP_NT_DIR if ABP_NT_DIR.is_dir() else ABP_NT_ZIP
    return ot, nt


def iter_verses(*sources):
    """Accept zip file paths or directory paths interchangeably."""
    for src in sources:
        src = Path(src)
        if src.is_dir():
            for txt in sorted(src.glob("*.txt")):
                with txt.open(encoding="utf-8", errors="replace") as f:
                    for raw in f:
                        parsed = parse_abp_line(raw)
                        if parsed:
                            yield parsed
        else:
            with zipfile.ZipFile(src) as z:
                for name in sorted(z.namelist()):
                    if not name.endswith(".txt"):
                        continue
                    with z.open(name) as f:
                        for raw in f:
                            parsed = parse_abp_line(raw.decode("utf-8", errors="replace"))
                            if parsed:
                                yield parsed


# ── BH index ──────────────────────────────────────────────────────────────────

def load_bh_verse_index(scrape: sqlite3.Connection) -> dict:
    index: dict = {}
    cur_key = None
    cur_rows: list = []
    for slug, ch, vs, strongs, english, iw, sw, gpos in scrape.execute(
        "SELECT book, chapter, verse, strongs, english, italic_words, smcap_words, greek_pos"
        " FROM bh_words ORDER BY book, chapter, verse, position"
    ):
        key = (slug, ch, vs)
        if key != cur_key:
            if cur_key is not None:
                index[cur_key] = cur_rows
            cur_key = key
            cur_rows = []
        base = strongs.split("-")[0].split(".")[0] if strongs else "*"
        cur_rows.append((base, normalize(english or ""), gpos, iw or "", sw or ""))
    if cur_key is not None:
        index[cur_key] = cur_rows
    return index


def bh_lookup(bh_rows: list, used: set, abp_base: str, abp_norm: str):
    for i, (base, norm, gpos, iw, sw) in enumerate(bh_rows):
        if i not in used and base == abp_base and norm == abp_norm:
            used.add(i)
            return gpos, iw, sw
    for i, (base, norm, gpos, iw, sw) in enumerate(bh_rows):
        if i not in used and base == abp_base:
            used.add(i)
            return gpos, iw, sw
    return None, "", ""


# ── Lexicon helpers ───────────────────────────────────────────────────────────

def load_lexicon(conn: sqlite3.Connection) -> dict:
    lex: dict = {}
    for strongs, kjv_def, strongs_def in conn.execute(
        "SELECT strongs, kjv_def, strongs_def FROM lexicon"
    ):
        base = strongs.lstrip("GH").split(".")[0]
        text = " ".join(filter(None, [kjv_def, strongs_def]))
        lex[base] = set(re.sub(r"[^\w\s]", " ", text).lower().split())
    return lex


# ── Compound splitting ────────────────────────────────────────────────────────

# Leading subject pronouns / auxiliaries that never carry a lexical sense, so the
# def-match below can't place them. Used ONLY when carry=True (see _split_compounds).
_CARRY_FW = frozenset({
    "i", "you", "ye", "thou", "thee", "we", "they", "he", "she", "it", "who",
    "do", "did", "does", "shall", "will", "would", "should",
    "may", "might", "can", "could", "must", "let", "have", "has", "had",
})


def _split_compounds(rows: list, lex: dict, carry: bool = False) -> None:
    """
    Redistribute words from compound ABP glosses to subsequent empty-english slots
    using lexicon evidence, then swap position numbers so redistributed words
    display before the verb/head word.

    carry=False (DEFAULT, used by the build): original behavior, unchanged — a
    rebuild produces exactly the same output it always has.

    carry=True (used ONLY by scripts/_gen_split_candidates.py): also lets a leading
    subject/aux word ("I", "do", "shall") ride to the verb it fronts, which fixes
    the reorder-merge garbles ("I see magistrates" -> "I see" | "magistrates"). This
    is NOT on by default because corpus-wide it also regresses ~85 verses
    (article/copula garbles the leaky lexicon match can't avoid); instead the
    PROVABLY-clean subset is frozen in split_merge_fixes.json and applied as a
    pinned data-patch by fix_split_merges.py. Leave carry=False here.

    Row tuple indices (11 elements while processing):
      0:pos  1:english  2:english_head  3:strongs  4:sbase  5:gpos
      6:bracket_id  7:italic  8:iw  9:sw  10:abp_pos
    """
    _NORM = re.compile(r"[^\w]")

    for i in range(len(rows)):
        pos_i, eng, head, strongs, sbase, gpos, bid, italic, iw, sw, abp_pos_i = rows[i][:11]
        morph_i, lemma_i = rows[i][11], rows[i][12]     # slot i's own morph/lemma (carried along)
        if not eng or " " not in eng:
            continue
        if not sbase or sbase in ("*", ""):
            continue
        # Bracketed slots are left exactly as the source orders them. ee84aa0 ("Keep
        # Greek word order within brackets") set bracket rendering to Greek/source order,
        # with the gpos superscripts conveying the English reading order. The
        # redistribution + front-swap below was only ever safe under the _sort_brackets
        # re-sort that ee84aa0 removed — so inside a bracket the swap silently garbled the
        # word order (audit_bracket_order.py: 374 cases, e.g. 1Ch 15:13 "the and LORD").
        # Splitting still runs for NON-bracketed glosses ("God made" → a separate
        # θεός/G2316 chip), where there are no source numbers to order by.
        if bid is not None:
            continue

        own_def = lex.get(sbase, set())
        gloss_words = eng.split()

        ahead = []
        for j in range(i + 1, len(rows)):
            if rows[j][1]:
                break
            slot_base = rows[j][4]
            if slot_base and slot_base not in ("*", ""):
                # facet (a): never redistribute a gloss word INTO the copula slot
                # (εἰμί, every conjugation → base 1510). Extracting e.g. "is" from
                # "he is a prophet" and fronting it (the swap below) renders
                # "is he a prophet"; leaving the copula slot empty keeps the
                # predicate gloss whole → "...for he is a prophet,".
                # (A broader morph-POS gate to also block this/that-into-demonstrative
                # over-reach was tried + REVERTED — it bundled "the LORD"/"their X"
                # corpus-wide, 11k verses. See TODO "_split_compounds demonstrative fix".)
                if slot_base == "1510":
                    continue
                ahead.append((j, slot_base, lex.get(slot_base, set())))

        if not ahead:
            continue

        # Leading-run rule (only non-bracketed slots reach here now): front a
        # redistributed gloss word only when no kept "own" word precedes it — so a
        # leading determiner ("the LORD", "their X") still splits, but a word sitting
        # after a kept word ("of this possession", "he is a prophet") stays put.
        apply_leading_run = True
        taken: dict = {}          # slot index -> [gloss words] in reading order
        own = []
        seen_own = False
        pending = []              # held leading subject/aux words awaiting a verb slot

        for word in gloss_words:
            norm = _NORM.sub("", word).lower()
            if not norm:
                if pending:
                    own.extend(pending); pending = []
                own.append(word)
                seen_own = True
                continue
            if norm in own_def:
                if pending:
                    own.extend(pending); pending = []
                own.append(word)
                seen_own = True
                continue
            # Once a kept "own" word has appeared, a non-bracketed slot stops
            # fronting (leading-run): a determiner at the head ("the LORD",
            # "their X") still fronts; one sitting AFTER a kept word ("of THIS
            # possession", "of THE LORD") stays put. Keys on gloss word-order,
            # not target POS (the POS gate of attempt 1 regressed every leading
            # determiner corpus-wide).
            if apply_leading_run and seen_own:
                own.append(word)
                continue
            placed = False
            for j, slot_base, slot_def in ahead:
                if j in taken:
                    continue
                if slot_def and norm in slot_def:
                    # held leading pronouns/aux ride to the verb's slot ("I see")
                    taken[j] = pending + [word]
                    pending = []
                    placed = True
                    break
            if placed:
                continue
            # Unmatched word. A leading subject/aux ("I", "do", "shall") matches no
            # definition; hold it so it travels with the verb it fronts instead of
            # poisoning the leading run and stranding the verb's gloss (1Sa 28:13).
            if carry and norm in _CARRY_FW and not seen_own:
                pending.append(word)
            else:
                if pending:
                    own.extend(pending); pending = []
                own.append(word)
                seen_own = True

        if pending:
            own.extend(pending); pending = []

        if not taken:
            continue

        # Assign english + inherit bracket_id, abp_pos, and gpos from source.
        # gpos (the position number superscript) moves to the first chip of the
        # compound so it displays before the first visible word.
        src_gpos    = rows[i][5]
        src_bid     = rows[i][6]
        src_abp_pos = rows[i][10]
        for j, words in taken.items():
            r = rows[j]
            eng = " ".join(words)
            # slot j keeps its OWN morph/lemma (r[11]/r[12]) — only the english moved in
            rows[j] = (r[0], eng, _head_word(eng), r[3], r[4], src_gpos, src_bid, r[7], r[8], r[9],
                       src_abp_pos, r[11], r[12])

        new_eng = " ".join(own) if own else None
        rows[i] = (pos_i, new_eng, _head_word(new_eng) if new_eng else None,
                   strongs, sbase, None, bid, italic, iw, sw, abp_pos_i, morph_i, lemma_i)

        for j in sorted(taken.keys()):
            p_i, p_j = rows[i][0], rows[j][0]
            rows[i] = (p_j,) + rows[i][1:]
            rows[j] = (p_i,) + rows[j][1:]

    rows.sort(key=lambda r: r[0])


# ── Backwards-pairing correction (number-reversal repair) ──────────────────────
# ABP writes a multi-word gloss with its Greek numbers tacked on the end
# ("of God  G3588 G2316"). _split_compounds hands the words to the empty slots by
# lexicon evidence, and for a [connector + content-noun] lump on a FUNCTION word
# (article ὁ/G3588 or a preposition) it can pair them BACKWARDS — the noun's tag
# landing on the function word and the connector's on the real noun (1Sa 5:2,
# Rom 8:34, the "a <noun>" prep cases). The English reads fine; only the
# clickable Strong's tag under each word ends up on the wrong slot.
#
# This pass corrects exactly that fingerprint — the same one scan_strongs_cross.py
# detects — by swapping the two slots' Greek identity (strongs, strongs_base,
# morph, lemma). It REPLACES the per-verse fix_article_noun_swaps.py band-aid:
# evidence-driven, no hardcoded verse list, re-applies on every rebuild. English
# text and word positions are untouched, so the verse reads identically.
_ARTICLE_FW   = "3588"
_PREP_FW = frozenset({
    "1722", "1519", "1537", "575", "4314", "1909", "2596", "3326", "1223",
    "5259", "5228", "3844", "4012", "1799", "1715", "3694", "561", "1726",
    "630", "3936",
})
_FUNCTION_FW  = frozenset({_ARTICLE_FW}) | _PREP_FW
_CONNECTOR_FW = frozenset({
    "of", "the", "a", "an", "to", "in", "by", "with", "for", "from", "at", "on",
    "into", "unto", "upon", "over", "under", "through", "s",
})
_SKIP_HEAD_FW = frozenset({
    "the", "a", "an", "this", "that", "these", "those", "of", "in", "by", "to",
    "with", "for", "from", "at", "on", "into", "unto", "and", "or", "not",
    "he", "she", "it", "they", "we", "i", "you", "me", "him", "her", "them",
    "us", "one", "ones", "thing", "things", "who", "which", "what", "both",
    "all", "any", "some", "each", "every", "other", "same", "is", "are", "was",
    "were", "be", "been", "being", "because", "therefore", "so", "then", "lest",
    "though", "while", "when", "where", "why", "how", "as", "than", "if",
})
_DET_FW = frozenset({
    "the", "a", "an", "this", "that", "these", "those", "my", "your", "his",
    "her", "our", "their", "its", "all", "of", "some", "any", "each", "every",
    "no", "which", "what", "one", "ones",
})


def _bare_fw(s):
    return re.sub(r"[^\w]", "", s or "").lower()


def _singular_fw(w):
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _fix_backwards_pairing(rows: list, lex: dict) -> None:
    """Swap the Greek tag on the two slots of a backwards number-pairing (see note
    above). Acts only on the high-precision fingerprint: a function-word slot
    (article/prep) carrying a real content noun whose meaning is found in an
    ADJACENT content slot that itself shows only a connector. Touches strongs,
    strongs_base, morph, lemma — never english/position — so the verse reads the
    same; only the tag under each word is corrected."""
    by_pos = {r[0]: i for i, r in enumerate(rows)}
    for idx, r in enumerate(rows):
        pos, eng, head, sbase = r[0], r[1], r[2], r[4]
        if sbase not in _FUNCTION_FW or not head:
            continue
        h = _bare_fw(head)
        if not h or h in _SKIP_HEAD_FW:
            continue
        toks = (eng or "").split()
        if toks and _bare_fw(toks[0]) in _DET_FW:        # substantival "the X" = legit
            continue
        for delta in (1, -1):
            nidx = by_pos.get(pos + delta)
            if nidx is None:
                continue
            nb  = rows[nidx]
            nsb = nb[4]
            if not nsb or nsb in _FUNCTION_FW or nsb in ("*", ""):
                continue
            neng = (nb[1] or "").strip().lower().strip(".,;:")
            d    = lex.get(nsb, set())
            if neng in _CONNECTOR_FW and (h in d or _singular_fw(h) in d):
                a, b = rows[idx], rows[nidx]
                # swap Greek identity (strongs=3, sbase=4, morph=11, lemma=12)
                rows[idx]  = (a[0], a[1], a[2], b[3], b[4], a[5], a[6], a[7],
                              a[8], a[9], a[10], b[11], b[12])
                rows[nidx] = (b[0], b[1], b[2], a[3], a[4], b[5], b[6], b[7],
                              b[8], b[9], b[10], a[11], a[12])
                break


# ── Lumped proper-noun + article split (Problem 2) ─────────────────────────────
_TRAIL_ARTICLE = frozenset({"the", "a", "an"})
_LEAD_SKIP = _DET_FW | _SKIP_HEAD_FW | frozenset({
    "for", "but", "yet", "nor", "indeed", "now", "also", "therefore",
    "moreover", "wherefore", "thus", "even",
})


def _split_pn_article_lump(rows: list) -> None:
    """ABP lumps a proper noun and a trailing article into ONE chip on the article
    slot ("Jesus the" on ὁ/G3588) and leaves the proper-noun slot (G* → '*') empty.
    Split into two plain, separately-clickable chips that read in English order
    "Jesus the" — NO bracket, NO reorder superscripts (matches eSword: "Jesus the
    Christ"). The EARLIER position takes the proper noun ("Jesus", '*' tag for
    import_tipnr to fill); the later position takes the article ("the", G3588). Only
    the pair's english/head/strongs/strongs_base/morph/lemma move; greek_pos and
    bracket_id are cleared so it renders inline with no [ ] markers. Rare (Act 19:4
    is the only corpus case) but built-in, not a per-verse patch. Runs last."""
    by_pos = {r[0]: i for i, r in enumerate(rows)}

    for idx, r in enumerate(rows):
        if r[4] != _ARTICLE_FW or r[6] is not None:        # article slot, unbracketed
            continue
        toks = (r[1] or "").split()
        if len(toks) < 2 or _bare_fw(toks[-1]) not in _TRAIL_ARTICLE:
            continue
        if _bare_fw(toks[0]) in _LEAD_SKIP:
            continue
        nidx = by_pos.get(r[0] + 1)
        if nidx is None:
            nidx = by_pos.get(r[0] - 1)
        if nidx is None:
            continue
        nb = rows[nidx]
        if (nb[1] and nb[1].strip()) or nb[4] != "*" or nb[6] is not None:
            continue
        art_eng = toks[-1]                  # "the"
        pn_eng  = " ".join(toks[:-1])       # "Jesus"
        art, pn = rows[idx], rows[nidx]     # article identity vs '*' identity
        early, late = (idx, nidx) if art[0] <= pn[0] else (nidx, idx)
        e, l = rows[early], rows[late]
        # earlier position -> proper noun ("Jesus"): '*' tag + its morph/lemma
        rows[early] = (e[0], pn_eng, _head_word(pn_eng), pn[3], pn[4], None, None,
                       e[7], e[8], e[9], e[10], pn[11], pn[12])
        # later position -> article ("the"): G3588 tag + its morph/lemma
        rows[late]  = (l[0], art_eng, _head_word(art_eng), art[3], art[4], None, None,
                       l[7], l[8], l[9], l[10], art[11], art[12])


# ── Bracket sorting ───────────────────────────────────────────────────────────

def _sort_brackets(rows: list) -> None:
    """
    Within each bracket group (same non-None bracket_id), sort words by
    abp_pos (element 10) so they display in ABP English reading order.
    Words with no abp_pos (ghost slots) sort last within their group.
    Reassigns sequential position numbers after sorting.
    """
    i = 0
    while i < len(rows):
        bid = rows[i][6]
        if bid is None:
            i += 1
            continue
        # Find extent of this bracket group
        j = i
        while j + 1 < len(rows) and rows[j + 1][6] == bid:
            j += 1
        # Sort by (abp_pos or ∞, original_pos)
        group = rows[i:j + 1]
        group.sort(key=lambda r: (r[10] if r[10] is not None else 9999, r[0]))
        # Reassign positions sequentially from base
        base = rows[i][0]
        for k, r in enumerate(group):
            rows[i + k] = (base + k,) + r[1:]
        i = j + 1


# ── Verse builder ─────────────────────────────────────────────────────────────

def apply_pronoun_corrections(abp_words: list, corrections: list,
                              flag_log: list, ref: str) -> list:
    """Pre-pass: rewrite raw_strongs for G1473 slots that confidently align to a
    Rahlfs pronoun (correct_verse → action 'fix'/'keep'). SURGICAL — only those
    slots change; everything else (incl. '*' proper-noun placeholders) passes
    through untouched. Flagged slots are logged and left as G1473. Returns a NEW
    list so the downstream reorder logic in build_verse_words is unaffected.

    Each output tuple is widened to 7 elements — (eng, raw, abp_pos, opens, closes,
    morph, lemma) — carrying the per-word morph + lemma the alignment found
    (None where it didn't anchor-match) on into build_verse_words."""
    out = []
    for (eng, raw, ap, ob, cb), c in zip(abp_words, corrections):
        if c.action in ("fix", "keep") and c.new_strong:
            out.append((eng, "G" + c.new_strong, ap, ob, cb, c.morph, c.lemma))
        else:
            if c.action == "flag":
                flag_log.append(f"{ref}\t{eng}\t{c.reason}")
            out.append((eng, raw, ap, ob, cb, c.morph, c.lemma))
    return out


# ── Pronoun-compound redistribution (symptom #2) ───────────────────────────────

_PRONOUN_BASES = frozenset({
    "846", "4675", "4771", "4571", "4674", "4671",
    "5210", "5216", "5213", "5209", "2249", "2257", "2254", "2248",
})
_ARTICLE_BASE = "3588"

# English pronoun words ABP uses — so we can tell the pronoun's OWN word from the
# verb phrase bundled onto it. (The lexicon def is KJV-style "thee/thy" and won't
# match ABP's "you/your", so an explicit set is used instead.)
_ENGLISH_PRONOUN_WORDS = frozenset({
    "i", "me", "my", "mine", "myself",
    "you", "your", "yours", "yourself", "yourselves", "thou", "thee", "thy", "thine", "ye",
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "it", "its", "itself",
    "we", "us", "our", "ours", "ourselves",
    "they", "them", "their", "theirs", "themselves", "same",
})


def _redistribute_pronoun_compounds(rows: list) -> None:
    """Symptom #2: ABP bundles a verb's English onto a PRONOUN slot, leaving the
    verb's own slot glossless — e.g. Gen 3:15 "will give heed to your" sits on
    σου/G4675 while τηρέω/G5083 is empty. Keep the pronoun's own word ("your") on
    the pronoun; move the rest ("will give heed to") to the adjacent empty slot;
    put the two into a NEW 2-word bracket so PROSE reads verb-then-pronoun
    (greek_pos order) while CHIP keeps Greek/source order (position order).

    SURGICAL: fires only for a known-pronoun slot with a multi-word gloss whose
    very next slot is empty, real-Strong's, non-article, and (like the pronoun)
    currently bracket-free. Touches english/english_head/greek_pos/bracket_id
    ONLY — never strongs/strongs_base/is_pn. Runs BEFORE _split_compounds so it
    sees the original bundled gloss (split's one-word-per-slot pass mangles it).

    Row tuple (11 elts): 0:pos 1:eng 2:head 3:strongs 4:sbase 5:gpos 6:bid
                         7:italic 8:iw 9:sw 10:abp_pos
    """
    _NORM = re.compile(r"[^\w]")
    existing = [r[6] for r in rows if r[6] is not None]
    next_bid = (max(existing) + 1) if existing else 1

    for i in range(len(rows) - 1):
        eng, sbase = rows[i][1], rows[i][4]
        if sbase not in _PRONOUN_BASES or not eng or " " not in eng:
            continue
        if rows[i][6] is not None:                 # pronoun already bracketed → defer
            continue
        j = i + 1
        if rows[j][1]:                             # next slot must be empty
            continue
        sbj = rows[j][4]
        if not sbj or sbj in ("*", "") or sbj == _ARTICLE_BASE or rows[j][6] is not None:
            continue

        keep, move = [], []
        for word in eng.split():
            norm = _NORM.sub("", word).lower()
            (keep if norm in _ENGLISH_PRONOUN_WORDS else move).append(word)
        if not keep or not move:
            continue

        keep_eng, move_eng = " ".join(keep), " ".join(move)
        bid = next_bid
        next_bid += 1

        ri, rj = rows[i], rows[j]
        # pronoun keeps its word, English-SECOND (greek_pos 2); joins the bracket
        rows[i] = (ri[0], keep_eng, _head_word(keep_eng), ri[3], ri[4],
                   2, bid, ri[7], ri[8], ri[9], ri[10], ri[11], ri[12])
        # verb gets the moved phrase, English-FIRST (greek_pos 1); joins the bracket
        rows[j] = (rj[0], move_eng, _head_word(move_eng), rj[3], rj[4],
                   1, bid, rj[7], rj[8], rj[9], rj[10], rj[11], rj[12])


# ── Folded post-build repairs (the former fix_*.py chain) ──────────────────────
# These six transforms used to run as standalone scripts AFTER the rebuild (see the
# CLAUDE.md "Words rebuild checklist"). Each is a per-verse, shape-keyed, re-runnable
# repair, so it folds into the single build pass here — applied in the SAME relative
# order the checklist used. The standalone scripts are kept as idempotent re-appliers
# and read-only audit twins; on a fresh build they now find 0 rows to change (that 0
# is itself the faithfulness check). strongs_base is still BARE at this stage (the 'G'
# prefix is added by _prefix_base at INSERT), so these match on bare numbers.
#
# Row tuple (13 elements here): 0:pos 1:english 2:english_head 3:strongs 4:strongs_base
#   5:greek_pos 6:bracket_id 7:italic 8:italic_words 9:smcap_words 10:abp_pos 11:morph 12:lemma

_TRAIL_PUNCT = re.compile(r"[.,;:!?·]+$")


def _italic_flag(head, iw_str):
    """italic=1 iff the head/display word is in the italic_words set (mirrors
    build_verse_words + fix_lord_subject.italic_flag)."""
    iset = {x for x in (iw_str or "").split(",") if x}
    return 1 if head and head.lower() in iset else 0


def _bracket_punct_float(rows: list) -> None:
    """Fold of fix_bracket_punct.py — float trailing clause punctuation within each
    bracket group onto the group's position-last displayed word, so chip mode reads
    cleanly ('[you? scrutinizes]' -> 'you scrutinizes?'). english column only."""
    by_bid: dict = {}
    for r in rows:
        if r[6] is not None:
            by_bid.setdefault(r[6], []).append(r[0])
    pos_to_idx = {r[0]: i for i, r in enumerate(rows)}
    for positions in by_bid.values():
        members = [rows[pos_to_idx[p]] for p in sorted(positions)]
        ti = None
        for k in range(len(members) - 1, -1, -1):
            t = (members[k][1] or "").strip()
            if t and _TRAIL_PUNCT.sub("", t) != "":
                ti = k
                break
        if ti is None:
            continue
        trailing = ""
        pending: dict = {}                 # position -> new english
        for k, w in enumerate(members):
            if k == ti:
                continue
            t = (w[1] or "").strip()
            if not t:
                continue
            if _TRAIL_PUNCT.sub("", t) == "":           # standalone punct token
                trailing += t
                pending[w[0]] = ""
                continue
            m = _TRAIL_PUNCT.search(t)
            if m:
                trailing += m.group()
                pending[w[0]] = t[: m.start()].rstrip()
        if not trailing:
            continue
        tw = members[ti]
        pending[tw[0]] = (tw[1] or "").rstrip() + trailing
        for p, new_eng in pending.items():
            i = pos_to_idx[p]
            rows[i] = (rows[i][0], new_eng) + rows[i][2:]


# ── g1473-gloss retag (fold of fix_g1473_gloss.py) ─────────────────────────────
_SU_SING = {"N": "4771", "V": "4771", "G": "4675", "D": "4671", "A": "4571"}   # σύ
_SU_PLUR = {"N": "5210", "G": "5216", "D": "5213", "A": "5209"}                # ὑμεῖς
_HEMEIS  = {"N": "2249", "G": "2257", "D": "2254", "A": "2248"}                # ἡμεῖς


def _g1473_case_num(morph):
    """(case, number) from a pronoun morph — CATSS 'RP.GS' / Robinson 'P-2GS'."""
    if not morph:
        return (None, None)
    m = morph.strip()
    if "." in m:
        tail = m.split(".", 1)[1]
    elif "-" in m:
        seg = m.split("-")
        tail = seg[1] if len(seg) > 1 else ""
        if tail[:1] in "123":
            tail = tail[1:]
    else:
        return (None, None)
    case = tail[0] if tail and tail[0] in "NVGDA" else None
    num = tail[1] if len(tail) > 1 and tail[1] in "SPD" else None
    return (case, num)


def _g1473_is_pron_morph(morph):
    """True/False if the morph denotes a pronoun (CATSS R*, Robinson P-/F-/S-);
    None if unknown."""
    if not morph:
        return None
    m = morph.strip()
    if "." in m:
        return m[0] == "R"
    if "-" in m:
        return m[0] in "PFS"
    return m and m[0] in "RPFS"


def _g1473_target(gloss_bucket, morph):
    """ABP gloss person (contradicting 1st-singular) + morph case/number -> the
    case-split (new_bare_base, lemma) or (None, None)."""
    case, num = _g1473_case_num(morph)
    if gloss_bucket == "3P":                            # αὐτός, all cases
        return ("846", "αὐτός")
    if gloss_bucket == "2P":                            # σύ (sing) / ὑμεῖς (plur)
        if case is None or num is None:
            return (None, None)
        n = (_SU_PLUR if num == "P" else _SU_SING).get(case)
        return (n, "σύ") if n else (None, None)
    if gloss_bucket == "1P":                            # ἡμεῖς
        if case is None:
            return (None, None)
        n = _HEMEIS.get(case)
        return (n, "ἐγώ") if n else (None, None)
    return (None, None)


def _g1473_gloss_retag(rows: list) -> None:
    """Fold of fix_g1473_gloss.py — residual ἐγώ/1473 slots whose ABP gloss is a
    DIFFERENT person (he/you/we) get the correct case-split number from gloss+morph
    (the un-fixed tail of pronoun correction). A consistent 'I/me/my', a reflexive
    '-self', or a 1P/2P slot with no parseable morph case+number is left untouched —
    never guessed. Touches strongs / strongs_base / lemma only."""
    if _G1473_BUCKET is None:                           # lxx_align unavailable
        return
    for i, r in enumerate(rows):
        if r[4] != "1473":
            continue
        gw = _g1473_last(r[1] or "")
        if gw.endswith("self") or gw.endswith("selves"):
            continue
        eb = _G1473_BUCKET.get(gw)
        if eb is None or eb == "1S":                    # no cue, or consistent → leave
            continue
        if _g1473_is_pron_morph(r[11]) is False:        # morph says not a pronoun → suspect
            continue
        new_base, lemma = _g1473_target(eb, r[11])
        if new_base is None:
            continue
        # strongs (3) + strongs_base (4) -> bare new number; lemma (12) -> new lemma
        rows[i] = r[:3] + (new_base, new_base) + r[5:12] + (lemma,)


# ── LORD-subject dual-ordering (fold of fix_lord_subject.py) ───────────────────
_LS_ARTICLES = ("the", "a", "an")


def _ls_bare(s):
    return re.sub(r"[^\w]", "", s or "").lower()


def _ls_prefix_split(eng):
    """'(the) LORD <rest...>' (LORD at the head, >=1 word after) -> (move, keep);
    else None (incl. wrapped 'May the LORD add' — a word before LORD)."""
    parts = eng.split()
    i = 0
    while i < len(parts) and _ls_bare(parts[i]) in _LS_ARTICLES:
        i += 1
    if i >= len(parts) or _ls_bare(parts[i]) != "lord":
        return None
    move, keep = parts[: i + 1], parts[i + 1:]
    if not keep:
        return None
    return " ".join(move), " ".join(keep)


def _lord_subject_split(rows: list) -> None:
    """Fold of fix_lord_subject.py (dual-ordering pilot #1) — '(the) LORD <verb...>'
    bundled on the verb with an adjacent EMPTY, bracket-free κύριος/2962 slot: move
    'the LORD' to the κύριος slot (greek_pos 1, reads first), keep the verb on its
    slot (greek_pos 2), bind both in a NEW per-verse bracket. Positions never move,
    so CHIP = verb · the LORD (source order, LORD clickable -> 2962) and PROSE =
    the LORD verb. Mirrors _redistribute_pronoun_compounds. Touches english / head /
    greek_pos / bracket_id / italic / italic_words only."""
    pos_to_idx = {r[0]: i for i, r in enumerate(rows)}
    existing = [r[6] for r in rows if r[6] is not None]
    next_bid = (max(existing) + 1) if existing else 1
    for i, r in enumerate(rows):
        eng = r[1] or ""
        if r[6] is not None or " " not in eng or "lord" not in eng.lower():
            continue
        if r[4] == "2962":
            continue
        split = _ls_prefix_split(eng)
        if not split:
            continue
        move, keep = split
        bj = pos_to_idx.get(r[0] + 1)                   # adjacent next slot
        if bj is None:
            continue
        b = rows[bj]
        if (b[1] or "").strip() != "" or b[4] != "2962" or b[6] is not None:
            continue
        src_iw = {_ls_bare(x) for x in (r[8] or "").split(",") if x}
        b_iw = ",".join(w for w in move.split() if _ls_bare(w) in src_iw)   # "the" rides w/ LORD
        a_iw = ",".join(w for w in keep.split() if _ls_bare(w) in src_iw)
        b_head, a_head = _head_word(move), _head_word(keep)
        bid = next_bid
        next_bid += 1
        # κύριος slot (b): "the LORD", reads first
        rows[bj] = (b[0], move, b_head, b[3], b[4], 1, bid,
                    _italic_flag(b_head, b_iw), b_iw) + b[9:]
        # verb slot (r): keeps the verb gloss, reads second
        rows[i] = (r[0], keep, a_head, r[3], r[4], 2, bid,
                   _italic_flag(a_head, a_iw), a_iw) + r[9:]


# ── function-word noun-relocate (fold of fix_funcword_subject.py, all rounds) ──
_FW_PREP = {
    "1722", "1519", "1537", "575", "4314", "1909", "2596", "3326", "1223",
    "5259", "5228", "3844", "4012", "1799", "1715", "3694", "561", "1726",
    "630", "1838", "3936",
}
_FW_HOSTS = {"3588"} | _FW_PREP
_FW_IDIOM_ORPHANS = {"4383", "5034"}      # πρόσωπον "in front", τάχος "quickly"
_FW_EXTRA = {
    "me", "him", "them", "us", "thee", "thy", "thine", "mine", "whom", "whose",
    "one", "ones", "thing", "things", "both", "who", "which", "what", "all",
    "any", "some", "each", "every", "other", "others", "same", "such",
    "whoever", "whatever", "anyone", "none",
}
_FW_SKIP_HEADS = set(_FUNCTION_WORDS) | set(_HEAD_STOP) | _FW_EXTRA


def _fw_singular(w):
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith(("ses", "xes", "zes", "ches", "shes")):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _fw_derive_head(english):
    for tok in reversed((english or "").split()):
        b = _ls_bare(tok)
        if b and b not in _FW_SKIP_HEADS:
            return b
    return None


def _fw_pos(morph):
    if not morph:
        return None
    c = morph.lstrip("-")[:1].upper()
    return c if c.isalpha() else None


def _funcword_noun_relocate(rows: list, lex: dict) -> None:
    """Fold of fix_funcword_subject.py (rounds 1-3: --include-idioms
    --include-bracketed) — a real noun's English bundled onto an adjacent
    function-word slot (article/preposition) while the noun's OWN slot sits empty:
    relocate the English onto the noun slot, blank the function word. One of the two
    adjacent slots is always empty, so the visible word sequence is unchanged — only
    WHICH Strong's each word attaches to. In a shared bracket, carry the host's
    greek_pos to the noun so prose order holds. english / head / italic /
    italic_words (+ greek_pos in-bracket) only.

    NOTE vs the standalone script: at build time a proper-noun orphan is still '*'
    (import_tipnr runs later), so the script's is_pn fallback can never fire here —
    its concrete-noun targets are morph POS=N, so the morph test alone is faithful."""
    pos_to_idx = {r[0]: i for i, r in enumerate(rows)}

    def orphan_base(nb, host_bid):
        if not nb or (nb[1] or "").strip() != "":       # must be empty
            return None
        if nb[6] != host_bid:                            # same bracket context
            return None
        sb = nb[4]
        if not sb or sb in ("*", "", "3588") or sb in _FW_HOSTS:
            return None
        base = sb.split(".")[0]
        if base in _FW_IDIOM_ORPHANS:                    # known nouns (morph gate redundant)
            return base
        if _fw_pos(nb[11]) == "N":
            return base
        return None

    for i, r in enumerate(rows):
        if r[4] not in _FW_HOSTS or not (r[1] and r[1].strip()):
            continue
        head = _fw_derive_head(r[1])
        if not head:
            continue
        host_bid = r[6]
        chosen = None
        for delta in (1, -1):
            nj = pos_to_idx.get(r[0] + delta)
            if nj is None:
                continue
            nb = rows[nj]
            base = orphan_base(nb, host_bid)
            d = lex.get(base, set()) if base else set()
            if base and (head in d or _fw_singular(head) in d):
                chosen = (nj, nb)
                break
        if not chosen:
            continue
        nj, nb = chosen
        moved = r[1]
        new_head = _head_word(moved)
        if not new_head or _ls_bare(new_head) in _FW_SKIP_HEADS:
            new_head = head
        if host_bid is not None:                         # in-bracket: carry host greek_pos
            rows[nj] = (nb[0], moved, new_head, nb[3], nb[4], r[5], nb[6],
                        r[7], r[8]) + nb[9:]
        else:
            rows[nj] = (nb[0], moved, new_head, nb[3], nb[4], nb[5], nb[6],
                        r[7], r[8]) + nb[9:]
        # function-word slot goes empty (keeps its OWN strongs + greek_pos + bracket_id)
        rows[i] = (r[0], None, None, r[3], r[4], r[5], r[6], 0, "") + r[9:]


# ── LORD-oath formula (fold of fix_lord_oath.py) ───────────────────────────────
_OATH_RE = re.compile(r"^(the [Ll][Oo][Rr][Dd])\s+(.*)$")


def _oath_head(eng):
    for w in re.sub(r"[^\w ]", " ", eng or "").split():
        if w.lower() not in ("the", "a", "an", "as"):
            return w
    return (eng or "").split()[0] if eng else None


def _lord_oath_fix(rows: list) -> None:
    """Fold of fix_lord_oath.py — 'As the LORD lives' oath (chay-YHWH): the reorder
    put 'As' on κύριος/2962 and 'the LORD lives' on ζάω/2198. Move 'the LORD' onto
    the κύριος chip -> 'As the LORD' | 'lives,'. Reading order + positions unchanged.
    english / head only."""
    pos_to_idx = {r[0]: i for i, r in enumerate(rows)}
    for i, r in enumerate(rows):
        if r[4] != "2962" or (r[1] or "").strip().lower() != "as":
            continue
        nj = pos_to_idx.get(r[0] + 1)
        if nj is None:
            continue
        nb = rows[nj]
        if nb[4] != "2198":
            continue
        m = _OATH_RE.match(nb[1] or "")
        if not m:
            continue
        det, remainder = m.group(1), m.group(2)          # "the LORD", "lives,"
        new_kyrios = f"{r[1].strip()} {det}"               # "As the LORD"
        rows[i] = (r[0], new_kyrios, det.split()[1]) + r[3:]
        rows[nj] = (nb[0], remainder, _oath_head(remainder)) + nb[3:]


# ── Greek-numeral gloss fill (fold of fix_abp_numerals.py) ─────────────────────
# ABP spells some numbers as Greek numeral LETTERS (χ ξ ϛ = 600 60 6, e.g. 666 in
# Rev 13:18), each parked at a dotted Strong's whose base is an unrelated word. The
# numeric gloss came across blank, so the reader dropped those words and the number
# vanished. These dotted codes mean the same numeral wherever they occur, so fill the
# digit by code (english only; leaves a real gloss alone). Greek letter side: pinned
# in build_dotted_lexicon.py so the chip's Greek line shows χ/ξ/ϛ.
_NUMERAL_GLOSS = {
    "5462.1": "600",   # χ
    "3577.2": "60",    # ξ
    "2193.2": "6",     # ϛ
}


def _numeral_gloss_fill(rows: list) -> None:
    """Fold of fix_abp_numerals.py — fill the digit for ABP's Greek-numeral words
    when their gloss is blank or bare punctuation. strongs (idx 3) is the shape key;
    english (idx 1) / head (idx 2) only. Re-runnable: a filled gloss won't re-fill."""
    for i, r in enumerate(rows):
        digit = _NUMERAL_GLOSS.get(r[3])
        if digit and not (r[1] or "").strip(" .,:;·"):
            rows[i] = (r[0], digit, digit) + r[3:]


# ── greek_pos backfill (fold of fix_greek_pos_gaps.py) ─────────────────────────
def _greek_pos_backfill(rows: list) -> None:
    """Fold of fix_greek_pos_gaps.py — a bracketed gloss word with NULL greek_pos
    inherits the nearest PRECEDING numbered word's greek_pos (else the next), so
    prose keeps it next to the word it was split from. greek_pos column only."""
    by_bid: dict = {}
    pos_to_idx = {r[0]: i for i, r in enumerate(rows)}
    for r in rows:
        if r[6] is not None:
            by_bid.setdefault(r[6], []).append(r[0])
    updates: dict = {}                     # position -> new greek_pos
    for positions in by_bid.values():
        members = [rows[pos_to_idx[p]] for p in sorted(positions)]
        last = None
        for w in members:
            if w[5] is not None:
                last = w[5]
            elif (w[1] or "").strip() and last is not None:
                updates[w[0]] = last
        nxt = None
        for w in reversed(members):
            if w[5] is not None:
                nxt = w[5]
            elif (w[1] or "").strip() and w[0] not in updates and nxt is not None:
                updates[w[0]] = nxt
    for p, gp in updates.items():
        i = pos_to_idx[p]
        rows[i] = rows[i][:5] + (gp,) + rows[i][6:]


def _strip_italic_heads(rows: list) -> None:
    """Final pass: a slot's search head must be its OWN word, never a translator-
    ADDED (italic) one. ABP marks added words italic; an added word has no Greek
    behind it, so letting it become the head mislabels the Greek word in the
    Word-study finder — 'take favor' (favor italic) made λαμβάνω/G2983 surface
    under a search for "favor". Recompute the head skipping italics for any
    multi-word gloss that carries italic markings; _head_word falls back to the
    plain pick when every content word is added, so bare article slots are left
    exactly as before. Touches english_head (idx 2) ONLY — never strongs/italic.
    Re-runnable: a row already on its own word won't change."""
    for i, r in enumerate(rows):
        eng, iw = r[1], r[8]
        if not eng or " " not in eng or not iw:
            continue
        italic_set = {w.strip().lower() for w in iw.split(",") if w.strip()}
        if not italic_set:
            continue
        new_head = _head_word(eng, italic_set)
        if new_head != r[2]:
            rows[i] = r[:2] + (new_head,) + r[3:]


def build_verse_words(abp_words: list, bh_rows: list, lex: dict = None) -> list:
    """
    Combine ABP word list with BH metadata.
    Bracket groups and reading order within brackets come from ABP position
    numbers ([1...2...3...]) — opens/closes bracket flags drive bracket_id.

    Row tuple (13 elements during processing, 12 returned):
      pos, english, english_head, strongs, strongs_base, greek_pos,
      bracket_id, italic, italic_words, smcap_words  [+ abp_pos (idx 10) stripped on
      return; morph (idx 11) + lemma (idx 12) kept as the final two columns].
      morph/lemma pin to the slot's OWN Greek word — they ride along by index
      through the reorder passes (which redistribute ENGLISH, never the Greek slot).

    abp_words tuples may be 5-wide (eng, raw, abp_pos, opens, closes) or 7-wide
    (… + morph, lemma) when apply_pronoun_corrections ran first; both are accepted.
    """
    used: set = set()
    rows: list = []
    pos = 0
    bid = 0
    in_bracket = False

    for w in abp_words:
        english, raw_strongs, abp_pos, opens_bracket, closes_bracket = w[:5]
        w_morph = w[5] if len(w) > 5 else None     # aligned morph (None if not anchor-matched)
        w_lemma = w[6] if len(w) > 6 else None     # aligned Greek lemma (None likewise)
        if raw_strongs is None:
            strongs = ""
            sbase   = ""
            gpos, iw, sw = None, "", ""
        elif raw_strongs == "G*":
            strongs = "*"
            sbase   = "*"
            gpos, iw, sw = None, "", ""
        else:
            # Keep strongs/sbase BARE here — bh_lookup() and the lexicon index
            # match on bare numbers. The 'G' prefix is re-applied to strongs_base
            # at INSERT time (see module-level _prefix_base). Do NOT prefix here or the
            # internal matching against lex/bh bare keys breaks.
            strongs = raw_strongs[1:]
            sbase   = strongs.split(".")[0]
            gpos, iw, sw = bh_lookup(bh_rows, used, sbase, normalize(english))

        # The bracket chip's superscript IS the source's ABP position number (ee84aa0:
        # "gpos superscripts show English reading order"). abp_pos is non-None only for
        # bracketed source tokens, so this makes the source number authoritative there
        # (fixing the cases where the BibleHub gpos disagreed with the source) while
        # non-bracketed words keep their BH gpos.
        if abp_pos is not None:
            gpos = abp_pos

        # Bracket state machine driven by ABP [/] markers
        if opens_bracket and not in_bracket:
            bid += 1
            in_bracket = True

        if in_bracket:
            bracket_id = bid
        else:
            bracket_id = None

        if closes_bracket:
            in_bracket = False

        english_head = _head_word(english) if english else None
        display      = english_head or (english if english and " " not in english else None)
        italic_set   = set(iw.split(",")) if iw else set()
        italic       = 1 if (display and display.lower() in italic_set) else 0

        # 11th element (abp_pos) is temporary — stripped before return
        rows.append((
            pos, english or None, english_head,
            strongs, sbase, gpos, bracket_id, italic,
            iw if iw else "", sw if sw else "",
            abp_pos, w_morph, w_lemma,
        ))
        pos += 1

    _redistribute_pronoun_compounds(rows)
    if lex:
        _split_compounds(rows, lex)
        _fix_backwards_pairing(rows, lex)
    _split_pn_article_lump(rows)

    # Folded post-build repairs (formerly the fix_*.py chain), in the CLAUDE.md
    # checklist's relative order: bracket_punct first, then g1473 -> LORD-subject ->
    # funcword, then LORD-oath, and greek_pos backfill LAST. Each is shape-keyed and
    # re-runnable; together they make the single pass self-correcting.
    _bracket_punct_float(rows)
    _g1473_gloss_retag(rows)
    _lord_subject_split(rows)
    if lex:
        _funcword_noun_relocate(rows, lex)
    _lord_oath_fix(rows)
    _numeral_gloss_fill(rows)
    _greek_pos_backfill(rows)
    _strip_italic_heads(rows)   # LAST: head must be the slot's own word, not an added (italic) one

    # Strip temporary abp_pos (idx 10); keep morph (11) + lemma (12) as the last two columns.
    return [r[:10] + (r[11], r[12]) for r in rows]


# ── Run / test ────────────────────────────────────────────────────────────────

def _prefix_base(w):
    """Restore the 'G' on strongs_base, and drop orphan greek_pos, at INSERT.

    Module-level + pure so it can be unit-tested (tests/test_build_invariants.py):
    these are the two guards that historically broke a rebuild.

    (1) The ABP source is Greek-only; the parser strips the 'G' so internal
    lex/BH matching can compare bare numbers. The DB invariant, however, is
    that words.strongs_base is fully G-prefixed (e.g. 'G2206') — a BARE base
    makes the lexicon join shave a *digit* and resolve the wrong lemma (the
    592k regression). The bare `strongs` column (idx 3) is intentionally left
    as-is (frontend renders it as G{strongs}). '*' (proper-noun placeholder)
    and '' (no strongs) pass through untouched.

    (2) greek_pos (idx 5) is an ABP reorder number meaningful only WITHIN a
    bracket. bh_lookup can hand one to a NON-bracket word (bracket_id, idx 6,
    is None); that orphan number renders as a stray superscript in the corpus
    view. Null it for non-bracket words.
    """
    w = list(w)
    if len(w) > 4 and w[4] and w[4][0].isdigit():
        w[4] = "G" + w[4]
    if len(w) > 6 and w[6] is None:
        w[5] = None
    return tuple(w)


def run(bible_db: str, scrape_db: str) -> None:
    scrape = sqlite3.connect(scrape_db)

    cols = {r[1] for r in scrape.execute("PRAGMA table_info(bh_words)")}
    if "greek_pos" not in cols:
        print("ERROR: bh_words missing greek_pos — re-scrape first.")
        scrape.close()
        sys.exit(1)

    bh_wc = scrape.execute("SELECT COUNT(*) FROM bh_words").fetchone()[0]
    print(f"BH words: {bh_wc:,}")

    target = bible_db + ".new"
    print(
        "\nThis rebuilds the words table from ABP text + BH metadata.\n"
        f"  SAFE BY DESIGN: it builds into a COPY ({target}); the live {bible_db} is\n"
        "  NEVER touched. You swap the copy in by hand at the end (one reversible move),\n"
        "  so a crash or a bad rebuild can only ever damage the throwaway copy.\n"
    )
    ans = input("Type 'rebuild' to confirm: ").strip()
    if ans != "rebuild":
        print("Aborted.")
        scrape.close()
        return

    # Build into a throwaway copy, NEVER the live file. The copy is a CONSISTENT
    # online snapshot of the live db (folds in the WAL), not a raw cp that could tear.
    # Everything below — the DELETE FROM words included — runs on this copy only.
    for sidecar in (target, target + "-wal", target + "-shm"):
        if Path(sidecar).exists():
            Path(sidecar).unlink()
    print(f"Snapshotting live {bible_db} → {target} …")
    _live = sqlite3.connect(f"file:{bible_db}?mode=ro", uri=True)
    main = sqlite3.connect(target)
    try:
        _live.backup(main)
    finally:
        _live.close()
    print("Snapshot done — the live db is untouched from here on.")

    main_cols = {r[1] for r in main.execute("PRAGMA table_info(words)")}
    for col in ("italic_words", "smcap_words", "morph", "lemma"):
        if col not in main_cols:
            main.execute(f"ALTER TABLE words ADD COLUMN {col} TEXT")
            main.commit()

    verse_map = {(b, c, v): vid for vid, b, c, v in main.execute(
        "SELECT id, book, chapter, verse FROM verses"
    )}
    print(f"ABP verse map: {len(verse_map):,}")

    print("Loading lexicon …")
    lex = load_lexicon(main)
    print(f"Lexicon entries: {len(lex):,}")

    print("Loading BH index …")
    bh_index = load_bh_verse_index(scrape)
    print(f"BH verse keys: {len(bh_index):,}\n")

    rahlfs = None
    if RahlfsLXX and RAHLFS_DIR.is_dir():
        print("Loading Rahlfs-1935 for pronoun correction …")
        rahlfs = RahlfsLXX(RAHLFS_DIR)
        print("  Rahlfs loaded.\n")
    else:
        print("⚠️  Rahlfs dir not found — OT pronoun correction SKIPPED.\n")
    tagnt = None
    if TAGNTSource and all(p.is_file() for p in TAGNT_FILES):
        print("Loading TAGNT for NT pronoun correction …")
        tagnt = TAGNTSource([str(p) for p in TAGNT_FILES])
        print("  TAGNT loaded.\n")
    else:
        print("⚠️  TAGNT files not found — NT pronoun correction SKIPPED.\n")
    flag_log = []

    print("Clearing words table …")
    main.execute("DELETE FROM words")
    main.commit()

    inserted = skipped = 0

    for abbrev, chapter, verse, abp_words in iter_verses(*_abp_sources()):
        verse_id = verse_map.get((abbrev, chapter, verse))
        if not verse_id:
            skipped += 1
            continue

        slug      = ABBREV_TO_SLUG.get(abbrev)
        bh_rows   = bh_index.get((slug, chapter, verse), []) if slug else []

        src = bnum = None
        if rahlfs and rahlfs.booknum(abbrev):           # OT → Rahlfs
            src, bnum = rahlfs, rahlfs.booknum(abbrev)
        elif tagnt and tagnt.booknum(abbrev):           # NT → TAGNT
            src, bnum = tagnt, tagnt.booknum(abbrev)
        if src:
            corrs = correct_verse([w[1] for w in abp_words],
                                  src.verse(bnum, chapter, verse),
                                  [w[0] for w in abp_words])
            abp_words = apply_pronoun_corrections(
                abp_words, corrs, flag_log, f"{abbrev} {chapter}:{verse}")

        word_rows = build_verse_words(abp_words, bh_rows, lex)

        main.executemany(
            "INSERT INTO words"
            " (verse_id, position, english, english_head, strongs, strongs_base,"
            "  greek_pos, bracket_id, italic, italic_words, smcap_words, morph, lemma)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(verse_id, *_prefix_base(w)) for w in word_rows],
        )
        inserted += len(word_rows)

        if inserted % 50_000 == 0:
            main.commit()
            print(f"  {inserted:,} words inserted …", flush=True)

    main.commit()

    # Fill the 5 ABP words that carry a blank "G." number (Zec 9:11 etc.) — splits the merged
    # slot back out and assigns the right Strong's. Bounded + guarded; no-op if unavailable.
    if apply_blank_strongs_fills:
        n_fill = apply_blank_strongs_fills(main, apply=True, log=lambda _m: None)
        main.commit()
        print(f"  Filled {n_fill} blank-Strong's word(s) (Zec 9:11 class).")

    # Split subject names merged onto their verb back onto their own '*' slot, so the
    # name is clickable and import_tipnr (run next) resolves it. Same fix as the
    # standalone fix_pn_subject_merge.py. Needs the tipnr roster (present after a
    # copy-first rebuild); silent no-op if it's missing. Bracketed cases are skipped.
    if apply_pn_subject_split:
        try:
            n_pn = apply_pn_subject_split(main, apply=True, log=lambda *_a: None)
            main.commit()
            print(f"  Split {n_pn:,} merged subject-name(s) — run import_tipnr next to resolve them.")
        except Exception as e:                       # e.g. no tipnr table on a first-ever build
            print(f"  (subject-name split skipped: {e})")

    main.close()
    scrape.close()

    if flag_log:
        Path("pronoun_review.tsv").write_text("\n".join(flag_log), encoding="utf-8")
        print(f"\n  Flagged {len(flag_log):,} pronoun slots for review → pronoun_review.tsv")

    print(f"\n── Results ─────────────────────────────────────────────")
    print(f"  Words inserted: {inserted:,}")
    print(f"  Verses skipped: {skipped:,}")
    print(f"\n  Built into: {target}   (live {bible_db} untouched)")
    print(f"\n  NEXT — run the dependent builders against the COPY, then swap it in.")
    print(f"  This rebuild CLEARED is_pn / proper-noun Strong's, so import_tipnr is required:")
    print(f"      python3 scripts/import_tipnr.py {target}")
    print(f"      python3 scripts/build_abp_surface.py {target} --bh {scrape_db}")
    print(f"      python3 scripts/build_abp_translit.py {target}")
    print(f"      # + the rest of the /rebuild-words checklist (dotted, two-ending, word_gloss)")
    print(f"      python3 scripts/audit_split_flip.py {target}     # must read 0")
    print(f"\n  Then swap it in — REVERSIBLE, one mv undoes it:")
    print(f"      mv {bible_db} {bible_db}.bak-$(date +%F) && rm -f {bible_db}-wal {bible_db}-shm \\")
    print(f"        && mv {target} {bible_db} && touch /var/www/www_lexica_bible_wsgi.py")


def run_test(scrape_db: str, book_abbrev: str = "Gen", chapter: int = 1,
             verse: int = None, bible_db: str = None) -> None:
    scrape   = sqlite3.connect(scrape_db)
    bh_index = load_bh_verse_index(scrape)
    scrape.close()

    lex = None
    if bible_db and Path(bible_db).exists():
        conn = sqlite3.connect(bible_db)
        lex  = load_lexicon(conn)
        conn.close()
        print(f"Lexicon: {len(lex):,} entries\n")

    rahlfs = None
    if RahlfsLXX and RAHLFS_DIR.is_dir():
        rahlfs = RahlfsLXX(RAHLFS_DIR)
        print("Rahlfs: loaded for OT pronoun correction\n")
    tagnt = None
    if TAGNTSource and all(p.is_file() for p in TAGNT_FILES):
        tagnt = TAGNTSource([str(p) for p in TAGNT_FILES])
        print("TAGNT: loaded for NT pronoun correction\n")
    flag_log = []

    slug   = ABBREV_TO_SLUG.get(book_abbrev, book_abbrev.lower())
    verses = {}
    for abbrev, ch, vs, words in iter_verses(*_abp_sources()):
        if abbrev == book_abbrev and ch == chapter:
            verses[vs] = words

    if not verses:
        print(f"No ABP data for {book_abbrev} {chapter}.")
        return

    print(f"=== {book_abbrev} {chapter} ===\n")
    for vs in sorted(verses):
        if verse is not None and vs != verse:
            continue
        abp_words = verses[vs]
        bh_rows   = bh_index.get((slug, chapter, vs), [])
        src = bnum = None
        if rahlfs and rahlfs.booknum(book_abbrev):       # OT → Rahlfs
            src, bnum = rahlfs, rahlfs.booknum(book_abbrev)
        elif tagnt and tagnt.booknum(book_abbrev):       # NT → TAGNT
            src, bnum = tagnt, tagnt.booknum(book_abbrev)
        if src:
            corrs = correct_verse([w[1] for w in abp_words],
                                  src.verse(bnum, chapter, vs),
                                  [w[0] for w in abp_words])
            abp_words = apply_pronoun_corrections(
                abp_words, corrs, flag_log, f"{book_abbrev} {chapter}:{vs}")
        word_rows = build_verse_words(abp_words, bh_rows, lex)

        print(f"{book_abbrev} {chapter}:{vs}")
        for (p, eng, head, sn, sb, gpos, bid, italic, iw, sw, morph, lemma) in word_rows:
            flags = ""
            if bid  is not None: flags += f"  bid={bid}"
            if gpos is not None: flags += f"  gpos={gpos}"
            if iw:               flags += f"  iw={iw!r}"
            if morph:            flags += f"  m={morph}"
            if lemma:            flags += f"  lem={lemma}"
            print(
                f"  [{p:2}] {str(sn or '-'):12}  "
                f"eng={str(eng):22}  head={str(head):15}  italic={italic}{flags}"
            )
        print()


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Rebuild words table from ABP text files + BH scrape metadata"
    )
    parser.add_argument("bible_db",  nargs="?", default="bible.db")
    parser.add_argument("scrape_db", nargs="?", default="bh_scrape.db")
    parser.add_argument("--test",    action="store_true")
    parser.add_argument("--book",    default="Gen")
    parser.add_argument("--chapter", type=int, default=1)
    parser.add_argument("--verse",   type=int, default=None)
    args = parser.parse_args()

    if args.test:
        if not Path(args.scrape_db).exists():
            print(f"ERROR: {args.scrape_db} not found.")
            sys.exit(1)
        bible_db = args.bible_db if Path(args.bible_db).exists() else None
        run_test(args.scrape_db, args.book, args.chapter, args.verse, bible_db)
    else:
        for path in (args.bible_db, args.scrape_db):
            if not Path(path).exists():
                print(f"ERROR: {path} not found.")
                sys.exit(1)
        print(f"bible.db:  {args.bible_db}")
        print(f"scrape db: {args.scrape_db}\n")
        run(args.bible_db, args.scrape_db)


if __name__ == "__main__":
    main()
