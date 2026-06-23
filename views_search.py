#!/usr/bin/env python3
"""Library plain-text search route.

/api/text-search — eSword-style verse search over a single reading text
(ABP / KJV / BSB, or a non-canonical book): a coarse SQL net refined in Python
(whole-word / case / exclude / book range), results cached in-memory
(_text_cache) keyed by the request params.

(The old study-mode /api/search lexicon endpoint was removed once the Library
in-text search + Word study + Ask the corpus replaced it — it had no caller.)
"""
import re
import sqlite3

from flask import Blueprint, jsonify, request

from core import db_ro, _KJV_BOOK_ID, _KJV_BOOK_ID_REV

bp = Blueprint("search", __name__)

_text_cache: dict = {}          # in-memory Library plain-text search cache (params → payload)
_TEXT_CACHE_CAP = 256           # keep the last N distinct searches; oldest drops out

# Per-corpus verse-text tables for the Library plain-text search. All three hold
# the readable ENGLISH verse text: ABP's `verses.text` is the clean English prose
# (populated by scripts/load_abp_prose.py), keyed by book abbreviation; KJV/BSB
# keep their English verse text keyed by the 1-66 book_id.
_TEXT_CORPORA = {
    # corpus: (table, book_col, chapter_col, verse_col, text_col, book_is_id)
    "abp": ("verses",     "book",    "chapter", "verse",     "text",       False),
    "kjv": ("kjv_verses", "book_id", "chapter", "verse_num", "verse_text", True),
    "bsb": ("bsb_verses", "book_id", "chapter", "verse_num", "verse_text", True),
}

# Non-canonical texts live in their own <id>_verses(chapter, verse, english)
# tables. This guard keeps the dynamic table name safe to interpolate.
_EXTRA_BOOK_RE = re.compile(r"^[a-z0-9_]+$")

# ABP's verse table keys books by their text abbreviation ("Gen", "Mar"), so a
# plain ORDER BY book sorts ALPHABETICALLY. This rank maps each abbreviation to
# its Bible-order number (1-66) so ABP results sort and range-filter in canonical
# order like KJV/BSB (which already key by the numeric book_id). Built from a
# trusted constant — the abbreviations are safe to interpolate.
_ABP_RANK_SQL = "CASE book " + " ".join(
    f"WHEN '{ab}' THEN {oid}" for ab, oid in _KJV_BOOK_ID.items()
) + " ELSE 999 END"

# Max candidate verses pulled from the DB before refining/counting in Python. A
# realistic word search returns far fewer; this just caps a pathological one.
_SEARCH_COARSE_CAP = 20000


def _compile_search_terms(words, partial, case):
    """Compile each search word into a match pattern.

    partial → substring match; otherwise the word must stand alone (whole word).
    case    → case-sensitive; otherwise case is ignored.
    """
    flags = 0 if case else re.IGNORECASE
    out = []
    for w in words:
        body = re.escape(w)
        if not partial:
            body = r"(?<!\w)" + body + r"(?!\w)"
        out.append(re.compile(body, flags))
    return out


@bp.route("/api/text-search")
def text_search():
    """eSword-style plain-text verse search over a single reading text.

    q        — the search text
    corpus   — 'bsb' (default) | 'kjv' | 'abp' (all search English verse text),
               OR a non-canonical text id (e.g. 'enoch') — its English line
    mode     — 'phrase' (default: words together) | 'all' (every word, any order)
               | 'any' (at least one word)
    partial  — '1' (default: substring match) | '0' (whole-word match only)
    case     — '1' case-sensitive | '0' (default: ignore case)
    exclude  — optional space-separated words; a verse with any of them is dropped
    from/to  — optional book abbreviations bounding a Bible-order range
               (e.g. from=Mat&to=Rev for the NT). Ignored for non-canonical texts.
    book     — legacy single-book filter (kept for back-compat; = from=to=book)

    Returns {results, verse_count, match_count, capped}. verse_count = verses with
    a hit; match_count = total word hits (a verse may hold several). results is
    capped at 1000 rows for display, but the counts cover the full match set.
    """
    q = request.args.get("q", "").strip()
    corpus = request.args.get("corpus", "bsb").lower()
    if not q:
        return jsonify({"results": [], "verse_count": 0, "match_count": 0, "capped": False})
    mode = request.args.get("mode", "phrase")
    partial = request.args.get("partial", "1") != "0"
    case = request.args.get("case", "0") == "1"
    exclude = request.args.get("exclude", "").strip()
    book = request.args.get("book", "").strip()
    book_from = request.args.get("from", "").strip()
    book_to = request.args.get("to", "").strip()

    if corpus in _TEXT_CORPORA:
        tbl, bcol, ccol, vcol, tcol, book_is_id = _TEXT_CORPORA[corpus]
        non_canon = False
    elif _EXTRA_BOOK_RE.match(corpus):
        # Non-canonical text: single book, readable text in the `english` column.
        tbl, bcol, ccol, vcol, tcol, book_is_id = f"{corpus}_verses", None, "chapter", "verse", "english", False
        non_canon = True
        book = book_from = book_to = ""
    else:
        return jsonify({"results": [], "verse_count": 0, "match_count": 0, "capped": False})

    # Canonical-order expression: ABP needs the abbrev→Bible-order map; KJV/BSB
    # already use the numeric book_id; a single-book non-canon text needs none.
    rank = "0" if non_canon else (_ABP_RANK_SQL if corpus == "abp" else bcol)

    where, params = [], []

    # Coarse text net: broad, case-insensitive substring — Python refines it below
    # (whole-word / case / exclude) so the heavy matching logic lives in one place.
    words = q.split()
    if mode == "phrase":
        where.append(f"{tcol} LIKE ? COLLATE NOCASE")
        params.append(f"%{q}%")
    elif words:
        where.append("(" + " OR ".join(f"{tcol} LIKE ? COLLATE NOCASE" for _ in words) + ")")
        params.extend(f"%{w}%" for w in words)

    # Book range (Bible texts only). Legacy single-book param folds into from=to.
    if book and not (book_from or book_to):
        book_from = book_to = book

    # Reuse an identical earlier search (the controls re-run on every toggle, so the
    # same params come back often). Same scan + Python tally → same answer.
    cache_key = (corpus, q, mode, partial, case, exclude, book_from, book_to)
    cached = _text_cache.get(cache_key)
    if cached is not None:
        return jsonify(cached)

    lo = _KJV_BOOK_ID.get(book_from)
    hi = _KJV_BOOK_ID.get(book_to)
    if not non_canon and lo:
        where.append(f"{rank} >= ?"); params.append(lo)
    if not non_canon and hi:
        where.append(f"{rank} <= ?"); params.append(hi)

    select_bk = f"{bcol} AS bk, " if bcol else ""
    sql = (
        f"SELECT {select_bk}{ccol} AS ch, {vcol} AS vs, {tcol} AS txt "
        f"FROM {tbl} WHERE " + " AND ".join(where) +
        f" ORDER BY {rank}, {ccol}, {vcol} LIMIT {_SEARCH_COARSE_CAP}"
    )
    conn = db_ro()
    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        return jsonify({"results": [], "verse_count": 0, "match_count": 0, "capped": False})
    finally:
        conn.close()

    # Refine + tally in Python: applies whole-word / case / exclude and counts hits.
    term_res = _compile_search_terms([q] if mode == "phrase" else words, partial, case)
    excl_res = _compile_search_terms(exclude.split(), partial, case) if exclude else []

    results, verse_count, match_count = [], 0, 0
    capped = len(rows) >= _SEARCH_COARSE_CAP
    for r in rows:
        txt = r["txt"] or ""
        counts = [len(p.findall(txt)) for p in term_res]
        if mode == "all":
            if not all(counts):
                continue
        elif not any(counts):   # phrase or any: need at least one hit
            continue
        if excl_res and any(p.search(txt) for p in excl_res):
            continue
        verse_count += 1
        match_count += sum(counts)
        if len(results) >= 1000:
            continue
        if non_canon:
            abbrev = corpus
        else:
            abbrev = r["bk"] if not book_is_id else _KJV_BOOK_ID_REV.get(r["bk"], "")
        results.append({
            "ref": f"{abbrev} {r['ch']}:{r['vs']}",
            "book": abbrev,
            "chapter": r["ch"],
            "verse": r["vs"],
            "text": txt,
        })
    payload = {
        "results": results,
        "verse_count": verse_count,
        "match_count": match_count,
        "capped": capped,
    }
    _text_cache[cache_key] = payload
    if len(_text_cache) > _TEXT_CACHE_CAP:
        del _text_cache[next(iter(_text_cache))]   # drop the oldest entry
    return jsonify(payload)
