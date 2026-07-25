#!/usr/bin/env python3
"""Shared core for the Lexica Flask app.

App-independent layer that the view modules import: DB connections, the rate
limiter (created WITHOUT an app — app.py calls limiter.init_app(app)), the
Anthropic client, small shared helpers, and the function-word set. This module
imports NOTHING from the view modules or app.py, so there are no circular imports.

The `_FUNCTION_STRONGS` set is declared here but POPULATED IN PLACE at startup by
app.py's `_build_function_strongs_cache` (clear()+update(), never reassigned) so
that `from core import _FUNCTION_STRONGS` references stay valid after the rebuild.
"""
import hashlib
import json
import logging
import os
import re
import sqlite3
import time

import anthropic
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

_log_level = getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
logging.basicConfig(level=_log_level, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bible")

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bible.db")

# R-2 stage 2 reader flip — the SINGLE named switch (docs/PLAN_r2_stage2.md, S2-Q1).
# Set READER_GREEK_IDENTITY=1 in the WSGI env to turn the Greek-identity proper-noun
# card ON. Default OFF: the identity endpoint answers "not found" and every card
# renders exactly as before (the OFF-proof gate, control C7). Rollback = flip the
# env line back and reload — no code revert.
READER_GREEK_IDENTITY = os.environ.get("READER_GREEK_IDENTITY", "") == "1"

# R-2 stage 3 flips (docs/PLAN_r2_stage3.md) — the SECOND switch, deliberately
# separate from READER_GREEK_IDENTITY so rolling back a new flip never rolls back
# the shipped, receipted stage-2 card (reviewer rollback-grouping ruling).
# Covers: #2 reader ABP Strong's tags Greek-keyed for backfilled proper nouns,
# then #1 Word study ABP branch. Default OFF: the chapter/verse word feeds are
# byte-identical to today (the G1 OFF-proof gate). Rollback = delete the env
# line + reload.
READER_GREEK_FLIPS = os.environ.get("READER_GREEK_FLIPS", "") == "1"

_anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
if not _anthropic_key:
    log.warning("ANTHROPIC_API_KEY not set — AI search will be unavailable")
_anthropic = anthropic.Anthropic(api_key=_anthropic_key) if _anthropic_key else None

# Created without an app; app.py wires it with limiter.init_app(app).
# default_limits is a per-endpoint, per-IP backstop against flooding the DB/SQLite
# routes (a flood is thousands/min, so 300/min stops abuse with huge headroom for
# real use — even many users behind one shared/NAT IP). The paid AI endpoints set
# their own tighter @limiter.limit("200 per hour"), which overrides this default;
# static asset loads are exempted in app.py so a normal page view never trips it.
limiter = Limiter(get_remote_address, default_limits=["300 per minute"], storage_uri="memory://")

# strongs_base values that are function words. Declared empty here; populated IN
# PLACE at startup by app.py's _build_function_strongs_cache (see module docstring).
_FUNCTION_STRONGS: set[str] = set()

# Bare H-numbers (no prefix, no byform suffix) whose Hebrew word is a NAME — a proper
# noun or a gentilic clan — per heb.db's own OT grammar. Declared empty here; populated
# IN PLACE at startup by app.py's _build_heb_name_cache. Gates the KJV/BSB reader's metaV
# name lookup (views_kjv / views_bsb) so a common word capitalized mid-verse never pops a
# bogus place/person card, while real names + gentilics still do.
_HEB_NAME_STRONGS: set[str] = set()

# In-memory L1 cache for AI-derived payloads (ai-search queries + xref synthesis/
# curation). Shared by the AI and cross-reference blueprints; mutated IN PLACE
# (cache[key] = payload), never reassigned, so `from core import _ai_cache`
# references stay valid. Startup loads only the AI-search entries into it.
_ai_cache: dict = {}

# ABP abbreviation → KJV CSV BookID (standard Protestant 1-66). The books table
# uses ABP auto-increment IDs that include apocrypha, so they don't match KJV
# BookIDs; we bypass the join entirely. Shared by the kjv/crossref/lexicon/search
# blueprints, so it lives in core.
_KJV_BOOK_ID: dict[str, int] = {
    "Gen":  1, "Exo":  2, "Lev":  3, "Num":  4, "Deu":  5,
    "Jos":  6, "Jdg":  7, "Rth":  8, "1Sa":  9, "2Sa": 10,
    "1Ki": 11, "2Ki": 12, "1Ch": 13, "2Ch": 14, "Ezr": 15,
    "Neh": 16, "Est": 17, "Job": 18, "Psa": 19, "Pro": 20,
    "Ecc": 21, "Son": 22, "Isa": 23, "Jer": 24, "Lam": 25,
    "Eze": 26, "Dan": 27, "Hos": 28, "Joe": 29, "Amo": 30,
    "Oba": 31, "Jon": 32, "Mic": 33, "Nah": 34, "Hab": 35,
    "Zep": 36, "Hag": 37, "Zec": 38, "Mal": 39,
    "Mat": 40, "Mar": 41, "Luk": 42, "Joh": 43, "Act": 44,
    "Rom": 45, "1Co": 46, "2Co": 47, "Gal": 48, "Eph": 49,
    "Php": 50, "Col": 51, "1Th": 52, "2Th": 53, "1Ti": 54,
    "2Ti": 55, "Tit": 56, "Phm": 57, "Heb": 58, "Jas": 59,
    "1Pe": 60, "2Pe": 61, "1Jn": 62, "2Jn": 63, "3Jn": 64,
    "Jud": 65, "Rev": 66,
}
_KJV_BOOK_ID_REV: dict[int, str] = {v: k for k, v in _KJV_BOOK_ID.items()}

# App book-abbrev -> standard USFM 3-char code. Used by the audio features:
# FCBH wants it UPPERCASE (ESV audio); openbible.com's public-domain BSB files
# want it title-cased (BSB_<NN>_<Mrk>_<CCC>.mp3). Both derive from this one map.
_USFM_BOOK: dict[str, str] = {
    "Gen": "GEN", "Exo": "EXO", "Lev": "LEV", "Num": "NUM", "Deu": "DEU",
    "Jos": "JOS", "Jdg": "JDG", "Rth": "RUT", "1Sa": "1SA", "2Sa": "2SA",
    "1Ki": "1KI", "2Ki": "2KI", "1Ch": "1CH", "2Ch": "2CH", "Ezr": "EZR",
    "Neh": "NEH", "Est": "EST", "Job": "JOB", "Psa": "PSA", "Pro": "PRO",
    "Ecc": "ECC", "Son": "SNG", "Isa": "ISA", "Jer": "JER", "Lam": "LAM",
    "Eze": "EZK", "Dan": "DAN", "Hos": "HOS", "Joe": "JOL", "Amo": "AMO",
    "Oba": "OBA", "Jon": "JON", "Mic": "MIC", "Nah": "NAM", "Hab": "HAB",
    "Zep": "ZEP", "Hag": "HAG", "Zec": "ZEC", "Mal": "MAL", "Mat": "MAT",
    "Mar": "MRK", "Luk": "LUK", "Joh": "JHN", "Act": "ACT", "Rom": "ROM",
    "1Co": "1CO", "2Co": "2CO", "Gal": "GAL", "Eph": "EPH", "Php": "PHP",
    "Col": "COL", "1Th": "1TH", "2Th": "2TH", "1Ti": "1TI", "2Ti": "2TI",
    "Tit": "TIT", "Phm": "PHM", "Heb": "HEB", "Jas": "JAS", "1Pe": "1PE",
    "2Pe": "2PE", "1Jn": "1JN", "2Jn": "2JN", "3Jn": "3JN", "Jud": "JUD",
    "Rev": "REV",
}


def usfm_titlecase(usfm: str) -> str:
    """USFM code -> openbible.com's filename form: first letter capital, the rest
    lower, digits kept. 'MRK'->'Mrk', '1SA'->'1Sa', '3JN'->'3Jn'."""
    out, seen_alpha = [], False
    for c in usfm:
        if c.isalpha():
            out.append(c.upper() if not seen_alpha else c.lower())
            seen_alpha = True
        else:
            out.append(c)
    return "".join(out)

_STRONGS_RE = re.compile(r'^[GH]?(\d+(?:\.\d+)*)$', re.IGNORECASE)
_WORD_BOUNDARY_RE_CACHE: dict[str, re.Pattern] = {}


def _strip_accents(s: str | None) -> str | None:
    """Remove combining diacritical marks so 'pneuma' matches 'pneûma'."""
    if not s:
        return s
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


# Vowel-LENGTH marks only — macron (U+0304) and breve (U+0306). Stripping JUST these
# (and keeping the accent/breathing) lets a plain-vowel lexicon lemma match an LSJ
# headword that carries a length mark — θυμός -> θῡμός — WITHOUT collapsing a true
# accent homograph like θύμος "thyme" onto it (its accent sits on the other vowel).
# This is the middle tier in the LSJ lookup, inserted between the exact-key match and
# the broad strip_accents fallback (views_lsj). See scripts/audit_lsj_tier_diff.py.
_LENGTH_MARKS = frozenset({"̄", "̆"})


def _strip_length_marks(s: str | None) -> str | None:
    """Remove only vowel-length marks (macron/breve); keep accents & breathings."""
    if not s:
        return s
    import unicodedata
    return unicodedata.normalize(
        "NFC",
        "".join(c for c in unicodedata.normalize("NFD", s) if c not in _LENGTH_MARKS),
    )


def _word_boundary_match(haystack: str | None, needle: str | None) -> bool:
    """SQLite custom function: True if needle appears as a complete word in haystack."""
    if not haystack or not needle:
        return False
    pat = _WORD_BOUNDARY_RE_CACHE.get(needle)
    if pat is None:
        pat = re.compile(r'(?<!\w)' + re.escape(needle) + r'(?!\w)', re.IGNORECASE)
        _WORD_BOUNDARY_RE_CACHE[needle] = pat
    return bool(pat.search(haystack))


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    # Several PA workers can touch bible.db at once (e.g. the startup cache cleanup),
    # so wait up to 5s for another worker's write to finish rather than failing with
    # "database is locked". Python's driver already defaults to ~5s; set it explicitly
    # so the intent is visible and the read-only connection below gets it too.
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.create_function("strip_accents", 1, _strip_accents)
    conn.create_function("strip_length", 1, _strip_length_marks)
    conn.create_function("word_boundary", 2, _word_boundary_match)
    return conn


def db_ro():
    """Read-only connection for executing AI-generated SQL."""
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")  # wait out a writer, don't error (see db())
    conn.create_function("strip_accents", 1, _strip_accents)
    conn.create_function("strip_length", 1, _strip_length_marks)
    conn.create_function("word_boundary", 2, _word_boundary_match)
    return conn


# User study notes live in their OWN file, NOT bible.db — bible.db is the corpus
# (rebuilt/regenerated) and stays read-only-ish; user data must survive a rebuild
# and stay isolated. This is the ONLY place the site stores visitor-created data.
NOTES_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes.db")


def notes_db():
    conn = sqlite3.connect(NOTES_DB)
    conn.row_factory = sqlite3.Row
    return conn


# Admin-authored "study modules" content (guided topics, denomination chart,
# arguments) lives in its OWN file, study.db — kept OUT of bible.db (the corpus
# is rebuilt; authored study content must survive that) and OUT of git (*.db is
# gitignored), like notes.db. Only the admin (owner) writes here; reading may open
# up later. The admin gate in views_study.py decides who can touch it.
STUDY_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "study.db")


def study_db():
    conn = sqlite3.connect(STUDY_DB)
    conn.row_factory = sqlite3.Row
    return conn


# Admin-only "news watch" articles — the end-times news gatherer's output. They
# live in their OWN file, news.db, gathered + AI-scored by scripts/news/, kept OUT
# of bible.db and OUT of git (*.db is gitignored), PythonAnywhere only. The admin
# gate in views_news.py decides who may read it; this helper just opens the file.
# Read-write (the tab marks stories keep/dismiss), like notes.db.
NEWS_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "news.db")


def news_db():
    conn = sqlite3.connect(NEWS_DB)
    conn.row_factory = sqlite3.Row
    # NFS-safe journaling: news.db lives on PA's NFS home. WAL needs a shared-memory
    # sidecar + mmap that NFS can't do reliably (it corrupted news.db 2026-07-05 —
    # lost page-1 write during a WAL fold-back). DELETE = plain rollback journal, and
    # busy_timeout waits-and-retries instead of erroring when the nightly scripts write.
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


# The ESV is a PERSONAL, owner-only reading text (Crossway-copyrighted — it is
# NEVER a public corpus like KJV/BSB). Its text lives in its OWN file, esv.db,
# kept OUT of bible.db and OUT of git (*.db is gitignored), and loaded on
# PythonAnywhere only by scripts/load_esv.py. The owner gate in views_esv.py
# decides who is allowed to read it; this helper just opens the file read-only.
ESV_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "esv.db")


def esv_db():
    """Read-only connection to esv.db. Raises sqlite3.OperationalError if the file
    isn't there yet (esv.db not loaded) — callers catch that and return empty."""
    conn = sqlite3.connect(f"file:{ESV_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# The NIV is a PERSONAL, owner-only reading text too (Biblica/Zondervan-
# copyrighted — NEVER a public corpus like KJV/BSB). Same setup as the ESV above:
# its text lives in its OWN file, niv.db, kept OUT of bible.db and OUT of git, and
# loaded on PythonAnywhere only by scripts/load_niv.py. The owner gate in
# views_niv.py decides who may read it; this helper just opens the file read-only.
NIV_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "niv.db")


def niv_db():
    """Read-only connection to niv.db. Raises sqlite3.OperationalError if the file
    isn't there yet (niv.db not loaded) — callers catch that and return empty."""
    conn = sqlite3.connect(f"file:{NIV_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# The Hebrew OT interlinear (Westminster Leningrad Codex via OpenScriptures morphhb)
# is PUBLIC DOMAIN — unlike the ESV/NIV above it is NOT owner-gated; it's meant to be
# a public study text like ABP/KJV/BSB. It still lives in its OWN file, heb.db, kept
# OUT of bible.db (the corpus is rebuilt; this text isn't) and OUT of git (*.db is
# gitignored), loaded on PythonAnywhere only by scripts/load_hebrew.py.
HEB_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heb.db")


def heb_db():
    """Read-only connection to heb.db. Raises sqlite3.OperationalError if the file
    isn't there yet (heb.db not loaded) — callers catch that and return empty."""
    conn = sqlite3.connect(f"file:{HEB_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ── Unified AI-synthesis result cache ────────────────────────────────────────
# Every Haiku-backed synthesis (search, summary, xref, metav person/place) stores
# its rows in ai_search_cache with ver_key = "<category>:<fingerprint>", the
# fingerprint being a hash of THAT synthesis's own prompt text. Editing a prompt
# changes only its category's fingerprint, so only that cache lazily refreshes, and
# each category prunes only its own stale rows. The row KEY (`query`) stays stable,
# so a regenerate OVERWRITES the stale row in place (it's the PRIMARY KEY) instead
# of leaving parallel old/new rows behind.

def ai_fingerprint(category: str, *parts) -> str:
    """'<category>:<16-hex sha1 of parts>'. `parts` = the prompt material that, when
    edited, should invalidate this category's cache (system prompt + instruction
    templates, plus any manual code-version salt for non-prompt logic changes)."""
    raw = "|".join(str(p) for p in parts)
    return f"{category}:{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:16]}"


def ai_cache_get(query: str, ver_key: str):
    """Cached payload for (query, ver_key), or None. A row written under a DIFFERENT
    ver_key (an older prompt) deliberately misses here so it regenerates."""
    conn = db_ro()
    try:
        row = conn.execute(
            "SELECT result_json FROM ai_search_cache WHERE query=? AND ver_key=?",
            (query, ver_key),
        ).fetchone()
    finally:
        conn.close()
    if row:
        try:
            return json.loads(row["result_json"])
        except Exception:
            return None
    return None


def ai_cache_put(query: str, payload: dict, ver_key: str) -> None:
    """Write one cache row (fire-and-forget; errors are logged only)."""
    try:
        conn = db()
        conn.execute(
            "INSERT OR REPLACE INTO ai_search_cache"
            " (query, result_json, ver_key, created_at) VALUES (?,?,?,?)",
            (query, json.dumps(payload), ver_key, time.time()),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        log.warning("Could not persist %s cache entry: %s", ver_key.split(":", 1)[0], exc)


def ai_cache_prune(category: str, keep_prefix: str) -> int:
    """Delete this category's STALE rows — ver_key starting '<category>:' but not
    under `keep_prefix` — and nothing else. `keep_prefix` is the current ver_key for
    a single-version category (search/xref/pn), or the shared template prefix
    'summary:<tpl>' for summaries (whose rows carry a per-book author suffix)."""
    try:
        conn = db()
        n = conn.execute(
            "DELETE FROM ai_search_cache"
            " WHERE ver_key LIKE ? AND ver_key NOT LIKE ?",
            (f"{category}:%", f"{keep_prefix}%"),
        ).rowcount
        conn.commit()
        conn.close()
        return n
    except Exception as exc:
        log.warning("Could not prune %s cache: %s", category, exc)
        return 0


def ai_cache_drop_legacy() -> int:
    """One-time sweep of pre-unification rows. Every legacy ver_key is colonless
    (bare-hex search hashes + the literals 'summary'/'xref'/'pn'); every new ver_key
    is '<category>:<hash>'. So 'has no colon' cleanly identifies all old rows. They
    would otherwise linger forever — get() filters on the new ver_key so they're
    never served, and ai_cache_prune only matches '<category>:%'. Harmless to re-run
    once they're gone (matches nothing)."""
    try:
        conn = db()
        n = conn.execute(
            "DELETE FROM ai_search_cache WHERE ver_key NOT LIKE '%:%'"
        ).rowcount
        conn.commit()
        conn.close()
        return n
    except Exception as exc:
        log.warning("Could not drop legacy cache rows: %s", exc)
        return 0


def _strongs_num(q: str):
    """Return the numeric portion if q looks like a Strong's ref, else None."""
    m = _STRONGS_RE.match(q.strip())
    return m.group(1) if m else None


def _serialize_word_core(row) -> dict:
    """Canonical core fields for an ABP words+lexicon row, built ONE way so the
    three word serializers (chapter_text / verse_words / _fetch_verse_words) can't
    drift — drift is what caused the is_pn-in-chapter bug. Each caller spreads this
    and adds its own extras (position, morph, pn_type, smcap_words, strongs_def,
    derivation, gloss, is_function/is_content, and italic's int-vs-bool form).
    Requires the row to expose: english, english_head, strongs, strongs_base,
    greek_pos, bracket_id, italic_words, lemma, translit, kjv_def, is_pn."""
    return {
        "english":      row["english"],
        "english_head": row["english_head"],
        "strongs":      row["strongs"],
        "strongs_base": row["strongs_base"],
        "greek_pos":    row["greek_pos"],
        "bracket_id":   row["bracket_id"],
        "italic_words": row["italic_words"],
        "lemma":        row["lemma"],
        "translit":     row["translit"],
        "kjv_def":      row["kjv_def"],
        "is_pn":        bool(row["is_pn"] or 0),
    }


def dotted_lexicon_cols(conn, base_lemma="l.lemma", base_translit="l.translit", strongs_col="w.strongs"):
    """ABP dotted Strong's (G###.N) whose word differs from their base keep their correct
    lemma/translit in the `dotted_lexicon` side table (full number -> own word). Returns
    (lemma_expr, translit_expr, join_clause) that COALESCE it over the base lexicon columns,
    or the base columns + '' when the table isn't built (deploy-safe). The caller selects the
    exprs `AS lemma`/`AS translit` and drops the join into its FROM. Per-word/per-occurrence
    queries only — NOT for queries that GROUP BY the base number (the dotted word would be
    ambiguous across the group)."""
    have = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='dotted_lexicon'"
    ).fetchone()
    if not have:
        return base_lemma, base_translit, ""
    return (f"COALESCE(dl.lemma, {base_lemma})",
            f"COALESCE(dl.translit, {base_translit})",
            f"LEFT JOIN dotted_lexicon dl ON dl.strongs = 'G' || {strongs_col}")


def word_gloss_cols(conn, strongs_col="w.strongs", base_col="w.strongs_base",
                    dotted_alias="dl", fallback="l.kjv_def"):
    """Plain-meaning lemma gloss from the `word_gloss` side table (scripts/build_word_gloss.py).
    Mirrors the dotted_lexicon lemma logic so the gloss tracks the SAME word as the headword:
    a dotted-different word (one present in dotted_lexicon, alias `dotted_alias`) shows its OWN
    gloss and NEVER its base's — if it has none, NULL, so the card falls back to its LSJ section;
    a base or εἰμί-form word shows the base number's gloss. Returns (gloss_expr, joins). The
    caller selects `{gloss_expr} AS kjv_def` and drops `{joins}` into FROM (per-word queries only).
    Deploy-safe: before the table is built, returns the fallback column + no join, so the reader's
    gloss is unchanged. Pass dotted_alias=None when dotted_lexicon isn't joined."""
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='word_gloss'"
    ).fetchone():
        return fallback, ""
    own = f"LEFT JOIN word_gloss wgd ON wgd.strongs = 'G' || {strongs_col}"
    if dotted_alias:                                   # suppress the base gloss for a dotted-DIFFERENT word
        base = (f"LEFT JOIN word_gloss wgb ON wgb.strongs = {base_col} "
                f"AND {dotted_alias}.strongs IS NULL")
    else:
        base = f"LEFT JOIN word_gloss wgb ON wgb.strongs = {base_col}"
    return "COALESCE(wgd.gloss, wgb.gloss)", f"{own} {base}"


def word_gloss_join(conn, strongs_col, alias="wg"):
    """Plain-meaning lemma gloss (scripts/build_word_gloss.py) for the KJV/BSB chapter
    endpoints — any per-word query that GROUP_CONCATs a single fully-prefixed Strong's
    column (e.g. 'ks.strongs_id'). Returns (select_fragment, join_fragment): the caller
    appends `{select_fragment}` to its SELECT list (it starts with a comma and yields
    `lemma_gloss`) and drops `{join_fragment}` into FROM. A Hebrew byform suffix (H1234a)
    folds to the base word_gloss key (which stores byforms collapsed); a no-op for Greek
    and base numbers. Deploy-safe: before word_gloss is built, returns ('', '') so the
    query is unchanged. word_gloss has no dotted Greek (KJV/BSB never use dotted), so a
    plain key match is right here — unlike the ABP-only word_gloss_cols."""
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='word_gloss'"
    ).fetchone():
        return "", ""
    sel = f", MAX({alias}.gloss) AS lemma_gloss"
    join = (f"LEFT JOIN word_gloss {alias} ON {alias}.strongs = "
            f"(CASE WHEN {strongs_col} GLOB 'H*[a-z]' "
            f"THEN substr({strongs_col}, 1, length({strongs_col}) - 1) "
            f"ELSE {strongs_col} END)")
    return sel, join


# ── R-2 candidate 3 (Hebrew retirement) — dormant serving repoints ────────────
# The rebuild moves a backfilled proper noun's Hebrew number OUT of
# words.strongs_base (which then carries the Greek identity, incl. STEP G9xxx)
# and INTO the cross-ref home `pn_hebrew_xref` (one row per PN word):
#   pn_hebrew_xref(verse_id, position, hebrew_base, class)
#     hebrew_base: the moved Hebrew number; NULL (declared, never '') for the
#                  3,518 always-Greek abp-tag rows, which never had one.
#     class:       abp-tag | tipnr | lemma-only | none. 'none' IS the ruled
#                  machine-visible kept-Hebrew exception (C3-Q1): those rows
#                  ALSO still carry Hebrew in words.strongs_base, until the
#                  gentilic/people-class Greek backfill candidate retires them.
# Everything below gates on the table EXISTING (the G1 table-existence guard
# pattern, per the charter's code-first run-shape ruling): before the rebuild
# lands, each helper returns today's exact SQL — the code ships dormant and
# self-activates at the swap. docs/PLAN_r2_stage3.md, candidate-3 charter.


def pn_xref_ready(conn) -> bool:
    """True once the Hebrew-retirement rebuild's cross-ref home exists."""
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='pn_hebrew_xref'"
    ).fetchone() is not None


def step_lemma_cols(conn, base_lemma, base_translit, base_gloss=None,
                    base_col="w.strongs_base"):
    """STEP-extended lemma/translit/gloss fallback for feeds that join the main
    lexicon on strongs_base: post-retirement that column carries G9xxx name
    numbers the main lexicon lacks (NULL lemma without this). Wraps the caller's
    existing column expressions in a COALESCE over step_lexicon and returns
    (lemma_expr, translit_expr, gloss_expr, join). One row per base via
    MIN(estrong) — same pick as Word study's _step_lexicon_row — so the LEFT
    JOIN can never duplicate word rows. Dormant (xref or step_lexicon absent):
    returns the inputs untouched + no join, SQL byte-identical to today."""
    if not pn_xref_ready(conn) or not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='step_lexicon'"
    ).fetchone():
        return base_lemma, base_translit, base_gloss, ""
    join = (f"LEFT JOIN (SELECT base, lemma, translit, gloss, MIN(estrong) "
            f"FROM step_lexicon GROUP BY base) sl "
            f"ON {base_col} GLOB 'G*' AND sl.base = CAST(substr({base_col}, 2) AS INTEGER)")
    return (f"COALESCE({base_lemma}, sl.lemma)",
            f"COALESCE({base_translit}, sl.translit)",
            (f"COALESCE({base_gloss}, sl.gloss)" if base_gloss else base_gloss),
            join)


def h_abp_predicate(conn, sid, alias="w"):
    """(pred, params) picking ABP `words` rows for an H-prefixed base.
    Post-retirement the backfilled PN rows no longer carry the Hebrew number in
    strongs_base, so an H-keyed ABP read unions the cross-ref home back in —
    the S2-Q4 bar (nothing findable becomes unfindable). rowid-IN keeps both
    arms on their indexes (the G2 perf shape); the peek skips the union for
    H-numbers with no name rows. Dormant: plain strongs_base match."""
    plain = (f"{alias}.strongs_base = ?", [sid])
    if not sid.startswith("H") or not pn_xref_ready(conn):
        return plain
    if conn.execute("SELECT 1 FROM pn_hebrew_xref WHERE hebrew_base = ? LIMIT 1",
                    (sid,)).fetchone() is None:
        return plain
    return (f"{alias}.rowid IN (SELECT w1.rowid FROM words w1 WHERE w1.strongs_base = ? "
            f"UNION SELECT w2.rowid FROM pn_hebrew_xref x JOIN words w2 "
            f"ON w2.verse_id = x.verse_id AND w2.position = x.position "
            f"WHERE x.hebrew_base = ?)", [sid, sid])


def pn_xref_parts(conn):
    """(join, tipnr_key) for the reader feeds' PN type-badge join: the `tipnr`
    table keys HEBREW numbers, so post-retirement the join goes through the
    cross-ref home (COALESCE keeps native-Hebrew and non-PN rows on the direct
    key). Dormant: no join, today's key."""
    if not pn_xref_ready(conn):
        return "", "w.strongs_base"
    return ("LEFT JOIN pn_hebrew_xref x ON x.verse_id = w.verse_id "
            "AND x.position = w.position",
            "COALESCE(x.hebrew_base, w.strongs_base)")


def _clean_gloss(s: str | None) -> str | None:
    """Strip trailing punctuation that ABP interlinear leaves on phrase-boundary words."""
    if not s:
        return s
    return s.strip(" ,;:.!?—-)(][")
