"""Grammatical-number fold for the Word-study English finder (/api/lexicon/english).

The finder matches an English query letter-for-letter against attested renderings
(words.english_head, kjv_words.word, bsb_words.word). That misses a rendering that
only exists in the OTHER number: theos G2316 is rendered "magistrates" (Exo 22:28),
so a singular "magistrate" query never reaches it.

normalize() collapses a word to a number-neutral KEY. Both the query AND the stored
rendering pass through the SAME function; the match becomes normalize(R)==normalize(Q).
There is no inverse function and no candidate generation to keep in sync — the stored
renderings carry a precomputed `*_norm` column (= normalize(rendering) at build time),
and the finder compares that column against normalize(query).

Resolution order inside normalize():  invariant(-ss) -> irregular map -> regular
singularizer -> exact (word maps to itself).

Scope: the irregular map holds ONLY forms attested as renderings in the corpus (probed
2026-07). Pairs with a single attested form (kine) or none (geese/goose) are excluded;
sheep/swine are inert under the regular rule and need no entry.
"""

# Many-to-one: every attested variant -> its canonical key. brethren/brothers/brother
# all collide on "brother"; cherub/cherubim/cherubims on "cherub" — the two-plurals /
# three-forms cases fall out for free.
IRREGULAR = {
    "child": "child",     "children": "child",
    "man": "man",         "men": "man",
    "woman": "woman",     "women": "woman",
    "foot": "foot",       "feet": "foot",
    "tooth": "tooth",     "teeth": "tooth",
    "mouse": "mouse",     "mice": "mouse",
    "ox": "ox",           "oxen": "ox",
    "brother": "brother", "brothers": "brother", "brethren": "brother",
    "cherub": "cherub",   "cherubim": "cherub",  "cherubims": "cherub",
}

# Attested -s-ending words that are NOT plurals — checked BEFORE the singularizer so its
# bare -s strip can't mangle them (the read caught news->new, does->doe, Heres->here;
# this/thus harmless today but fragile, closed now). Self-map = leave whole.
# Case-insensitive (normalize lowercases first), so "Heres" the place name is covered.
# NOTE: -ous words (precious, gracious…) are handled by the singularizer's -ous guard,
# not here — no need to list them.
INVARIANT = frozenset({"news", "does", "this", "thus", "heres"})

# Leading/trailing quotes + the possessive tail get stripped before matching, so a
# rendering like  "why / man's / “surely  reaches its bare word.
_QUOTES = "\"'“”‘’"   # straight " ' + curly “ ” ‘ ’

_VOWELS = frozenset("aeiou")
# -es strips only after a sibilant cluster that makes -es its own syllable, so
# "boxes"->"box" and "matches"->"match" but "houses"->"house" (falls to plain -s).
_ES_SUFFIXES = ("ches", "shes", "xes", "zes", "sses")


def singularize(w):
    """Regular English singularizer — a tested pure function. Only touches words >=4
    letters (so "as"/"is" survive). See the unit-test table in tests/test_number_fold."""
    if len(w) < 4:
        return w
    if w.endswith("ss"):                       # witness, grass — never strip
        return w
    if w.endswith("ous"):                      # gracious, righteous, precious — never a plural
        return w
    if w.endswith("ies") and w[-4] not in _VOWELS:   # cities->city (consonant + ies)
        return w[:-3] + "y"
    for suf in _ES_SUFFIXES:                    # boxes->box, matches->match, kisses->kiss
        if w.endswith(suf):
            return w[:-2]
    if w.endswith("s"):                         # houses->house, magistrates->magistrate
        return w[:-1]
    return w


def _depunct(w):
    """Strip leading/trailing quotes + a possessive tail (leading/trailing only — never
    touch a real internal hyphen/apostrophe beyond the possessive 's)."""
    w = w.strip(_QUOTES).strip()
    if len(w) > 2 and w[-1] == "s" and w[-2] in "'’":   # man's -> man, children's -> children
        w = w[:-2]
    return w


def _norm_token(w):
    """Number-neutral key for a SINGLE already-lowercased/depunctuated token."""
    if not w:
        return w
    if w.endswith("ss"):        # -ss guard: keep witness/grass/pass inert
        return w
    if w in INVARIANT:          # attested non-plural -s words: leave whole
        return w
    key = IRREGULAR.get(w)      # irregular / self-mapped variants -> canonical key
    if key is not None:
        return key
    return singularize(w)


def normalize(word):
    """Collapse a word to its number-neutral key. Used identically on both sides of the
    finder's match, so normalize(query)==normalize(rendering) is the whole contract.
    Multi-word renderings (ABP phrase heads like "the news") are normalized TOKEN BY
    TOKEN, so the invariant set protects a phrase's trailing word too ("the news" keeps
    "news" — never collapses to "the new")."""
    if not word:
        return word
    w = _depunct(word.strip().lower())
    if not w:
        return w
    return " ".join(_norm_token(t) for t in w.split())
