"""Book-aware parsing of model-written verse picks (ai._BOOK_PARSE_RE + ai._norm_book).

The pass-2 curation returns verse refs as "Book Ch:V" strings the model writes from
memory — and it favors FULL names, especially in additional_verses (the curate prompt
itself models "1 Jn 3:1" style). The old crude parse (a bare word token +
title-case truncation) mis-attributed numbered full names: "1 John 3:1" was fetched and shown
as **John 3:1** — wrong evidence for the claim — and "Philippians"/"James"/"1
Corinthians"/"Song of Solomon" silently dropped. These lock the book-aware parse
(static patterns, no bible.db — runs in CI + pre-commit).
"""
import ai


def _parse(ref):
    """Mirror the pick-parse in ai._assemble_payload: scan, then normalize the book."""
    m = ai._BOOK_PARSE_RE.search(str(ref).strip())
    if not m:
        return None
    return (ai._norm_book(m.group(1)), int(m.group(2)), int(m.group(3)))


# ── the P1 misattribution: a numbered full name must NEVER become its base gospel ──

def test_numbered_full_name_not_misattributed():
    # The bug: "1 John 3:1" → John 3:1. Must resolve to 1 John (1Jn), never Joh.
    assert _parse("1 John 3:1") == ("1Jn", 3, 1)
    assert _parse("1 John 3:1")[0] != "Joh"


def test_numbered_abbreviated_forms():
    assert _parse("1 Jn 3:1") == ("1Jn", 3, 1)
    assert _parse("2 John 1:7") == ("2Jn", 1, 7)
    assert _parse("3 Jn 1:9") == ("3Jn", 1, 9)


# ── full names the title()[:3] guess mangled (Phi≠Php, Jam≠Jas) or dropped ──

def test_full_names_that_broke_normalization():
    assert _parse("Philippians 4:13") == ("Php", 4, 13)
    assert _parse("James 2:24") == ("Jas", 2, 24)
    assert _parse("1 Corinthians 16:2") == ("1Co", 16, 2)
    assert _parse("Song of Solomon 2:1") == ("Son", 2, 1)


def test_common_refs_still_parse():
    assert _parse("Gen 6:2") == ("Gen", 6, 2)
    assert _parse("Genesis 1:26") == ("Gen", 1, 26)
    assert _parse("Rom 8:14") == ("Rom", 8, 14)
    assert _parse("Mar 2:27") == ("Mar", 2, 27)
    assert _parse("John 1:1") == ("Joh", 1, 1)
    assert _parse("Psalms 82:6") == ("Psa", 82, 6)


def test_ref_embedded_in_prose():
    assert _parse("see 1 Corinthians 13:4 for love") == ("1Co", 13, 4)


# ── malformed / non-book refs return nothing (never a garbage fetch) ──

def test_malformed_returns_none():
    assert _parse("notabook 3:1") is None
    assert _parse("just some prose") is None
    assert _parse("") is None
    assert _parse("Gen 6") is None          # no verse
    assert _parse("3:1") is None            # no book


def test_norm_book_disambiguation_preserved():
    # Bare "Jud" stays Judges (the pre-existing _BOOK_NORM override), not Jude.
    assert ai._norm_book("Jud") == "Jdg"
    assert ai._norm_book("Judges") == "Jdg"
    assert ai._norm_book("Jude") == "Jud"
