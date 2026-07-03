"""Standing-trap fixture for the lexica-def build's book-label table (build_lexica_def._BOOK_CODE
+ _REF_RE + _norm_book). Locks the exact-match, no-fallback rule that the Judges/Jude collision
makes a correctness requirement: nobody touches that table later without these passing.

The traps come from the 2026-07-03 rollout: "Ruth" (code Rth) was hard-rejected because the old
catcher only took 3-letter codes. Static — builds its own labels, needs no bible.db (runs in CI +
pre-commit). Import is stdlib-only (build_lexica_def pulls in contested_register + lexica_coverage,
both stdlib; anthropic is imported lazily inside main()).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import build_lexica_def as B

_VALID = set(B._BOOK_CODE.values())


def _pick(ref):
    """Mirror cited_refs: catch a ref, normalize its book. None if nothing caught."""
    m = B._REF_RE.search(ref)
    if not m:
        return None
    return (B._norm_book(m.group(1)), int(m.group(2)), int(m.group(3)))


# ── the six hazard rows named at the checkpoint ──

def test_hazard_rows_resolve():
    assert _pick("Judges 6:12") == ("Jdg", 6, 12)
    assert _pick("Jude 1:4") == ("Jud", 1, 4)
    assert _pick("Ruth 1:16") == ("Rth", 1, 16)      # the one that bit us
    assert _pick("Ps 2:7") == ("Psa", 2, 7)
    assert _pick("Philemon 1:6") == ("Phm", 1, 6)


def test_bare_phil_is_rejected():
    # bare "Phil" is deliberately unmapped (Philippians vs Philemon) — not caught, not resolved.
    assert _pick("Phil 1:6") is None
    assert B._norm_book("Phil") not in _VALID


def test_judges_jude_no_prefix_leak():
    # THE collision that forces exact-match: bare "Jud" is Jude, NEVER Judges.
    assert B._norm_book("Jud") == "Jud"
    assert B._norm_book("Judges") == "Jdg"
    assert B._norm_book("Jude") == "Jud"


# ── nothing already-passing moves: every code maps to itself ──

def test_all_66_codes_pass_through():
    codes = set(B._BOOK_CODE.values())
    assert len(codes) == 66
    for code in codes:
        assert B._norm_book(code) == code


def test_full_and_abbrev_names():
    assert _pick("Gen 1:1") == ("Gen", 1, 1)
    assert _pick("Genesis 1:26") == ("Gen", 1, 26)
    assert _pick("1 Corinthians 16:2") == ("1Co", 16, 2)
    assert _pick("Song of Solomon 2:1") == ("Son", 2, 1)
    assert _pick("James 2:24") == ("Jas", 2, 24)
    assert _pick("Mt 5:17") == ("Mat", 5, 17)


def test_ref_embedded_in_prose():
    assert _pick("as in 1 John 3:1, the love") == ("1Jn", 3, 1)


def test_lowercase_prose_not_caught():
    # case-sensitive catcher: a lowercase word is never a citation.
    assert _pick("the act 3:4 of") is None
    assert _pick("no book here 3:1") is None


# ── the dangling-lint soft set: words not codes, with exactly two named exceptions ──

def test_dangling_soft_is_words_not_codes():
    code_keys = {c.lower() for c in set(B._BOOK_CODE.values())}
    # only Job and Song(=Son) may appear on both sides — the two codes that are also English words.
    assert B._DANGLING_SOFT & code_keys == {"job", "son"}
