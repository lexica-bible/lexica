"""
test_lexica_draw_cache.py — the DRAW CACHE (review-what-ships) for build_lexica_def.py.

Proves the whole point of the cache: the prose a human reviews in the --dry-run pass is the prose
--apply ships, byte-for-byte, and every write-time gate still fires on the cached content. Builds
its own tiny on-disk word/verse fixture (no bible.db) and drives build_lexica_def.main() end to end.

The model is never called: model_prose is stubbed to return canned prose and make_client is stubbed
away, so the suite adds NO anthropic / API-key dependency (that's exactly the property the lazy
client gives us — applying a cached draw touches no model).
"""
import contextlib
import functools
import io
import json
import os
import sqlite3
import sys
import tempfile
from unittest import mock

_SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, _SCRIPTS)
import build_lexica_def as B


# ── fixture corpus: ἀγαπάω G25 tagged at three NT verses (>= OCC_MIN), plus a Rev verse with NO G25
# so a citation to it is a REAL gate miss. Book codes Joh/Rom/Rev are all valid verses.book codes.
G25, FILLER = "G25", "G9999"

CANNED_GOOD = (
    "**Senses**\n\n"
    "**1. to love, hold dear** — steady regard a subject has for an object, from ordinary "
    "affection to covenant loyalty (Joh 3:16; Joh 13:34; Rom 5:8).\n\n"
    "**Range:** from plain affection to steadfast covenant loyalty."
)
# same shape, but cites Rev 1:1 where G25 is NOT tagged → the citation gate must reject it.
CANNED_BAD = (
    "**Senses**\n\n"
    "**1. to love** — regard for an object (Joh 3:16; Rev 1:1).\n\n"
    "**Range:** affection to loyalty."
)


def _fixture_db(path):
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE verses  (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);
        CREATE TABLE words   (verse_id INT, position INT, strongs TEXT, strongs_base TEXT, english_head TEXT,
                              english TEXT, italic_words TEXT, is_pn INT DEFAULT 0);
        CREATE TABLE lexicon (strongs_g TEXT, lemma TEXT, translit TEXT);
    """)
    conn.execute("INSERT INTO lexicon VALUES (?,?,?)", (G25, "ἀγαπάω", "agapao"))
    rows = [
        (1, "Joh", 3, 16, "For God so loved the world",      [(G25, "loved"), (FILLER, "world")]),
        (2, "Joh", 13, 34, "that you love one another",       [(G25, "love"),  (FILLER, "another")]),
        (3, "Rom", 5, 8,  "God loves us in that Christ died", [(G25, "loves"), (FILLER, "Christ")]),
        (4, "Rev", 1, 1,  "The revelation of Jesus Christ",   [(FILLER, "revelation")]),
    ]
    for vid, bk, ch, vs, text, toks in rows:
        conn.execute("INSERT INTO verses VALUES (?,?,?,?,?)", (vid, bk, ch, vs, text))
        for pos, (base, head) in enumerate(toks):
            conn.execute("INSERT INTO words VALUES (?,?,?,?,?,?,?,0)", (vid, pos, base[1:], base, head, head, ""))
    conn.commit()
    conn.close()


def _read_row(db, sid):
    conn = sqlite3.connect(db)
    r = conn.execute("SELECT def_json FROM lexica_def WHERE strongs=?", (sid,)).fetchone() \
        if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='lexica_def'").fetchone() \
        else None
    conn.close()
    return r[0] if r else None


def _run(argv):
    """Drive main() with a patched argv; return the SystemExit code (None = clean exit).
    Its output is captured (Greek must not hit a cp1252 console); stderr lands in _run.err."""
    old = sys.argv
    sys.argv = argv
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            B.main()
        return None
    except SystemExit as e:
        return e.code
    finally:
        sys.argv = old
        _run.err = err.getvalue()
        _run.out = out.getvalue()


def with_env(fn):
    """Run a test on its own throwaway fixture db + draws folder (stdlib only, so
    tests/run_plain_tests.py can call it with no arguments). model_prose is restored after."""
    @functools.wraps(fn)
    def wrapped():
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            draws = os.path.join(tmp, "draws")
            with mock.patch.object(B, "DRAWS_DIR", draws), \
                 mock.patch.object(B, "make_client", lambda: None), \
                 mock.patch.object(B, "model_prose", B.model_prose):
                B._VALID_BOOKS = None                  # reset the module-cached book set between tests
                B._P2_PN_CACHE.clear()                 # keyed by id(conn); a reused id must not carry over
                db = os.path.join(tmp, "bible.db").replace(os.sep, "/")  # valid RO file: URI on Windows
                _fixture_db(db)
                return fn({"db": db, "draws": draws})
    return wrapped


def _draw_file(env):
    return os.path.join(env["draws"], "G25.json")


def _no_model(*a, **k):
    raise AssertionError("model_prose was called on a cache HIT — the cache was bypassed")


# ── helper-level unit tests ─────────────────────────────────────────────────────────────────────
@with_env
def test_signature_status_and_roundtrip(env):
    gset = [("loved", 3)]
    ctx = [("Joh", 3, 16, "loved", "", "For God so loved", "", "", [])]
    sig = B.draw_signature("G25", "agapao", gset, ctx)

    B.save_draw("G25", "ἀγαπάω", "agapao", gset, ctx, "PROSE")
    rec = B.load_draw("G25")
    assert rec["raw"] == "PROSE"
    assert B.draw_status(rec, sig) == "hit"

    # a different input (gloss count moved) → the signature moves → stale
    assert B.draw_status(rec, B.draw_signature("G25", "agapao", [("loved", 4)], ctx)) == "stale"
    # prose bytes changed but signature still matches → edited
    tampered = dict(rec, raw="CHANGED")
    assert B.draw_status(tampered, sig) == "edited"


# ── the five required end-to-end proofs ───────────────────────────────────────────────────────
@with_env
def test_apply_ships_cached_draw_verbatim(env):
    """dry-run saves the draw; apply writes it byte-for-byte, with NO model call."""
    B.model_prose = lambda *a, **k: CANNED_GOOD
    assert _run(["b", "--dry-run", "--word", "G25", "--db", env["db"]]) is None
    assert os.path.exists(_draw_file(env)), "dry-run must save the reviewed draw"

    B.model_prose = _no_model                                 # prove apply never calls the model
    assert _run(["b", "--apply", "--word", "G25", "--db", env["db"]]) is None
    entry = json.loads(_read_row(env["db"], "G25"))
    assert entry["raw"] == CANNED_GOOD                        # shipped bytes == reviewed bytes


@with_env
def test_stale_input_invalidates(env):
    """A words/verse change moves the signature; --require-cache refuses rather than ship a stale draw."""
    B.model_prose = lambda *a, **k: CANNED_GOOD
    _run(["b", "--dry-run", "--word", "G25", "--db", env["db"]])

    conn = sqlite3.connect(env["db"])                         # move a fed verse's prose → new signature
    conn.execute("UPDATE verses SET text = text || ' (edited)' WHERE book='Joh'")
    conn.commit()
    conn.close()
    B._VALID_BOOKS = None

    B.model_prose = _no_model                                 # require-cache refuses before any model call
    code = _run(["b", "--apply", "--require-cache", "--word", "G25", "--db", env["db"]])
    assert code is not None, "a stale draw under --require-cache must refuse"
    assert _read_row(env["db"], "G25") is None, "nothing may be written"


@with_env
def test_apply_on_miss_flags_unreviewed(env):
    """Permissive single-word apply with no draw: writes, but loudly, and leaves NO draw file."""
    B.model_prose = lambda *a, **k: CANNED_GOOD
    assert _run(["b", "--apply", "--word", "G25", "--db", env["db"]]) is None
    entry = json.loads(_read_row(env["db"], "G25"))
    assert entry["raw"] == CANNED_GOOD
    assert "UNREVIEWED" in _run.err
    assert not os.path.exists(_draw_file(env)), \
        "an unreviewed fresh apply must not leave a draw file that later looks reviewed"


@with_env
def test_gate_fires_on_cached_content(env):
    """A cached draw with a bad citation still hits the citation gate at apply — no write."""
    B.model_prose = lambda *a, **k: CANNED_BAD
    _run(["b", "--dry-run", "--word", "G25", "--db", env["db"]])   # saves the (bad) draw file
    assert os.path.exists(_draw_file(env))

    B.model_prose = _no_model
    code = _run(["b", "--apply", "--word", "G25", "--db", env["db"]])
    assert code is not None, "the citation gate must reject the cached bad draw"
    assert "citation gate FAILED" in (_run.out + _run.err), "refused, but not by the citation gate"
    assert _read_row(env["db"], "G25") is None


@with_env
def test_edited_draw_hard_refused(env):
    """Same input, but the draw file's prose was changed between review and apply → hard refuse."""
    B.model_prose = lambda *a, **k: CANNED_GOOD
    _run(["b", "--dry-run", "--word", "G25", "--db", env["db"]])

    p = _draw_file(env)
    with open(p, encoding="utf-8") as f:
        rec = json.load(f)
    rec["raw"] = CANNED_GOOD + "\n\n**2. tampered sense**"     # edit prose, leave prose_sha stale
    with open(p, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False)

    B.model_prose = _no_model                                  # must NOT fall through to a fresh draw
    code = _run(["b", "--apply", "--word", "G25", "--db", env["db"]])
    assert code is not None, "an edited draw must be refused, not silently redrawn"
    assert _read_row(env["db"], "G25") is None
