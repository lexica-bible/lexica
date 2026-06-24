#!/usr/bin/env python3
"""Lexica Flask entry point.

Thin app shell: builds the Flask app, wires the rate limiter, registers the
domain blueprints (metav, crossref, lsj, kjv, lexicon, library, search, ai), and
runs schema migration up front and warms the rest (function-word cache, AI cache
load) in a background thread so a cold worker can serve the page immediately. All
route logic lives in the views_*/ai modules over the shared core.

The function-word classifier (_build_function_strongs_cache + its LSJ POS helpers)
stays here because it's a startup step that populates core._FUNCTION_STRONGS IN
PLACE — keeping it out of the view modules avoids an import cycle.

PA wsgi is UNCHANGED — `app` is still importable from this module.
"""
import json
import os
import re
import sqlite3
import threading

from flask import Flask, jsonify, render_template, request, url_for, redirect, send_from_directory

from core import log, DB, HEB_DB, db, limiter, _FUNCTION_STRONGS, _HEB_NAME_STRONGS, heb_db, ai_cache_drop_legacy


_CACHE_DIR = os.path.dirname(os.path.abspath(__file__))


def _disk_cached_set(name, source_db, compute):
    """Load a precomputed Strong's set from a small JSON file next to the app,
    keyed to source_db's modified-time. Recompute + rewrite ONLY when the DB
    changed (or the file is missing/unreadable) — otherwise just read the file.
    The two startup scans below (lexicon×LSJ function-word classify, heb_words
    name classify) are the heavy part of a cold worker's warm-up; turning each
    into a fast file read stops a freshly recycled PA worker from stealing CPU
    from the page request sitting behind it. Auto-refreshes on any data rebuild
    (the DB mtime moves), so it can't go stale."""
    path = os.path.join(_CACHE_DIR, name)
    try:
        src_mtime = int(os.path.getmtime(source_db))
    except OSError:
        src_mtime = 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            blob = json.load(f)
        if blob.get("mtime") == src_mtime:
            return blob["items"]
    except (OSError, ValueError, KeyError):
        pass
    items = sorted(compute())
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"mtime": src_mtime, "items": items}, f)
    except OSError:
        pass
    return items

# LSJ part-of-speech detection for function words.
# LSJ def_html has two POS patterns:
#   Short entries: <b>WORD</b>, Conj., …
#   Long entries:  <b>WORD</b>, (many variant forms) … <b>PREP.</b> WITH DAT. …
# We check both: plain-text POS near the headword AND bold POS section headers.
_LSJ_FUNC_WORD_RE = re.compile(
    r'\b(?:'
    r'Prep(?:osition)?[.,\s]|Conj(?:unction)?[.,\s]|Part(?:icle)?[.,\s]|'
    r'Art(?:icle)?[.,\s]|definite\s+article\b|'
    r'preposition\b|conjunction\b|particle\b|article\b'
    r')',
    re.IGNORECASE,
)
_LSJ_FUNC_BOLD_RE = re.compile(
    r'<b>(?:PREP(?:OSITION)?|CONJ(?:UNCTION)?|PART(?:ICLE)?|ART(?:ICLE)?)[.,\s<]',
    re.IGNORECASE,
)


def _is_lsj_function_word(def_html: str) -> bool:
    """Return True if the LSJ entry is a grammatical function word (not a content word)."""
    html = def_html or ''
    # Fast path: bold POS section header anywhere in the entry (e.g. <b>PREP.</b>)
    if _LSJ_FUNC_BOLD_RE.search(html[:3000]):
        return True
    # Slow path: strip the opening headword, then look for POS in plain text
    tail = re.sub(r'^\s*<b>[^<]*</b>', '', html.strip())
    text = re.sub(r'<[^>]+>', ' ', tail[:300]).strip()
    return bool(_LSJ_FUNC_WORD_RE.search(text[:200]))


# Hardcoded function words the LSJ POS detector misses (pronouns, negative particles,
# and common conjunctions/prepositions whose LSJ entries don't join the lsj table).
_FUNCTION_STRONGS_OVERRIDE: frozenset[str] = frozenset({
    # Negative particles
    "3361",   # μή
    "3756",   # οὐ / οὐκ / οὐχ
    "3761",   # οὐδέ
    "3762",   # οὐδείς / οὐδεμία / οὐδέν
    "3763",   # οὐδέποτε
    "3777",   # οὔτε
    "3780",   # οὐχί
    "3364",   # οὐ μή (emphatic negation)
    # Personal pronouns
    "1473",   # ἐγώ
    "4771",   # σύ
    "846",    # αὐτός / αὐτή / αὐτό
    "2249",   # ἡμεῖς
    "5210",   # ὑμεῖς
    "1438",   # ἑαυτοῦ / ἑαυτῆς (reflexive)
    # Demonstrative pronouns
    "3778",   # οὗτος / αὕτη / τοῦτο
    "1565",   # ἐκεῖνος
    "3592",   # ὅδε / ἥδε / τόδε
    # Definite article
    "3588",   # ὁ / ἡ / τό
    # Relative / interrogative / indefinite pronouns
    "3739",   # ὅς / ἥ / ὅ
    "3748",   # ὅστις / ἥτις / ὅτι
    "5101",   # τίς / τί (interrogative)
    "5100",   # τις / τι (indefinite)
    # Common conjunctions / particles (lsj join fails for these)
    "2532",   # καί
    "1161",   # δέ
    "3767",   # οὖν
    "235",    # ἀλλά
    "1063",   # γάρ
    "3754",   # ὅτι
    "2443",   # ἵνα
    "1487",   # εἰ
    "5613",   # ὡς
    "1437",   # ἐάν
    "3303",   # μέν
    "2228",   # ἤ
    "686",    # ἄρα
    "3303",   # μέν
    "1065",   # γε
    "4458",   # πως / πώς
    # Common prepositions (lsj join fails for most)
    "1722",   # ἐν
    "1519",   # εἰς
    "1537",   # ἐκ / ἐξ
    "575",    # ἀπό
    "4314",   # πρός
    "2596",   # κατά
    "3326",   # μετά
    "1223",   # διά
    "1909",   # ἐπί
    "4012",   # περί
    "5228",   # ὑπέρ
    "5259",   # ὑπό
    "4253",   # πρό
    "473",    # ἀντί
    "1722",   # ἐν (dupe, harmless)
    "303",    # ἀνά
    "1537",   # ἐκ (dupe, harmless)
})


def _compute_function_strongs_from_db() -> set[str]:
    """The heavy step: classify lexicon entries content/function via LSJ def_html.
    Returns the DB-derived set only (the code-defined OVERRIDE set is folded in by
    the caller, so editing it takes effect immediately without busting the file
    cache, which is keyed to the DB's mtime — not the code)."""
    conn = db()
    rows = conn.execute(
        """SELECT l.strongs, lsj.def_html
           FROM lexicon l
           JOIN lsj ON lsj.plain = lower(strip_accents(l.lemma))"""
    ).fetchall()
    conn.close()
    func: set[str] = set()
    for row in rows:
        if _is_lsj_function_word(row["def_html"]):
            func.add(row["strongs"])
    return func


def _build_function_strongs_cache() -> None:
    """Populate core._FUNCTION_STRONGS IN PLACE (clear+update, never reassign) so
    `from core import _FUNCTION_STRONGS` references in the view modules stay valid.
    The heavy DB classify is disk-cached; the OVERRIDE set is unioned in fresh each
    time so a code edit to it lands without a data rebuild."""
    try:
        items = _disk_cached_set("cache_funcwords.json", DB, _compute_function_strongs_from_db)
        _FUNCTION_STRONGS.clear()
        _FUNCTION_STRONGS.update(items)
        _FUNCTION_STRONGS.update(_FUNCTION_STRONGS_OVERRIDE)
        log.info("Function word cache: %d function words (LSJ + overrides)", len(_FUNCTION_STRONGS))
    except Exception as e:
        log.warning("Could not build function word cache (LSJ table may not exist yet): %s", e)


def _build_heb_name_cache() -> None:
    """Build core._HEB_NAME_STRONGS from heb.db's own morphology: the bare H-numbers whose
    Hebrew word is a NAME (proper noun or gentilic clan), by DOMINANT use across the OT.
    Gates the KJV/BSB reader's metaV name lookup so a common word capitalized mid-verse
    ('Wilderness of Sinai') never pops a place card, while real names + gentilic clans still
    do. Populated IN PLACE (clear+update) so `from core import _HEB_NAME_STRONGS` references
    stay valid. Empty when heb.db isn't loaded — the endpoints then omit the flag and the
    frontend falls back to the capital-letter heuristic."""
    def _compute() -> set[str]:
        conn = heb_db()
        rows = conn.execute(
            "SELECT strongs, morph, COUNT(*) AS n FROM heb_words "
            "WHERE strongs GLOB 'H*' GROUP BY strongs, morph"
        ).fetchall()
        conn.close()
        name_ct: dict[str, int] = {}
        other_ct: dict[str, int] = {}
        for r in rows:
            num = "".join(c for c in (r["strongs"] or "") if c.isdigit())
            code = r["morph"] or ""
            if not num or not code:                       # no number / no grammar tag → no vote
                continue
            is_name = (code[0] == "N" and code[1:2] in ("p", "g")) or \
                      (code[0] == "A" and code[1:2] == "g")     # noun proper/gentilic, adj gentilic
            tgt = name_ct if is_name else other_ct
            tgt[num] = tgt.get(num, 0) + (r["n"] or 0)
        return {num for num in (name_ct.keys() | other_ct.keys())
                if name_ct.get(num, 0) > other_ct.get(num, 0)}
    try:
        items = _disk_cached_set("cache_hebnames.json", HEB_DB, _compute)
        _HEB_NAME_STRONGS.clear()
        _HEB_NAME_STRONGS.update(items)
        log.info("Hebrew name cache: %d proper-noun/gentilic Strong's from heb.db", len(_HEB_NAME_STRONGS))
    except Exception as e:
        log.warning("Could not build Hebrew name cache (heb.db may not be loaded yet): %s", e)


from views_metav import bp as metav_bp, prune_cache as _prune_metav_cache
from views_crossref import bp as crossref_bp, prune_cache as _prune_xref_cache
from views_lsj import bp as lsj_bp
from views_kjv import bp as kjv_bp
from views_bsb import bp as bsb_bp
from views_esv import bp as esv_bp
from views_niv import bp as niv_bp
from views_heb import bp as heb_bp
from views_stats import bp as stats_bp
from views_news import bp as news_bp
from views_lexicon import bp as lexicon_bp
from views_library import bp as library_bp
from views_search import bp as search_bp
from views_summary import bp as summary_bp, prune_cache as _prune_summary_cache
from views_chrono import bp as chrono_bp, prune_cache as _prune_chrono_cache
from views_notes import bp as notes_bp
from views_study import bp as study_bp
from views_seo import bp as seo_bp
from ai import bp as ai_bp, _load_ai_cache_from_db

app = Flask(__name__)
limiter.init_app(app)


@app.before_request
def _force_canonical_domain():
    # Anyone landing on the old *.pythonanywhere.com address gets sent
    # to the real domain, same path, permanently (301).
    host = request.host.split(":")[0]
    if host.endswith(".pythonanywhere.com"):
        return redirect("https://www.lexica.bible" + request.full_path.rstrip("?"), code=301)


# Static assets (app.js, self-hosted React, CSS) load several per page view —
# exempt them so the site-wide default limit only guards the dynamic DB + AI
# routes and never trips on a normal page load (incl. shared/NAT IPs).
@limiter.request_filter
def _exempt_static():
    # Static assets AND the crawlable SEO pages (seo.*) + the root files crawlers
    # auto-fetch: a search bot sweeping many chapter pages must never hit the
    # per-IP DB-route backstop. The dynamic JSON/AI routes keep their limits.
    ep = request.endpoint or ""
    return ep == "static" or ep.startswith("seo.") or ep in {"favicon", "apple_touch_icon", "robots_txt"}


app.register_blueprint(metav_bp)
app.register_blueprint(crossref_bp)
app.register_blueprint(lsj_bp)
app.register_blueprint(kjv_bp)
app.register_blueprint(bsb_bp)
app.register_blueprint(esv_bp)
app.register_blueprint(niv_bp)
app.register_blueprint(heb_bp)
app.register_blueprint(stats_bp)
app.register_blueprint(news_bp)
app.register_blueprint(lexicon_bp)
app.register_blueprint(library_bp)
app.register_blueprint(search_bp)
app.register_blueprint(summary_bp)
app.register_blueprint(chrono_bp)
app.register_blueprint(notes_bp)
app.register_blueprint(study_bp)
app.register_blueprint(seo_bp)
app.register_blueprint(ai_bp)


@app.context_processor
def _asset_helpers():
    """Cache-busting static URLs: append each file's mtime as ?v=<mtime> so a
    deploy (git pull bumps the mtime) forces browsers to refetch. Brave/Chrome
    cache app.jsx + styles.css aggressively; a stale app.jsx served against a
    fresh styles.css broke the mobile nav layout (both bars stacked at top)."""
    def asset_url(filename):
        try:
            mtime = int(os.path.getmtime(os.path.join(app.static_folder, filename)))
        except OSError:
            mtime = 0
        return url_for("static", filename=filename, v=mtime)
    return {"asset_url": asset_url}


def _migrate_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        try:
            conn.execute("ALTER TABLE lsj ADD COLUMN summary_json TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists
        # One-time: clear v1 summaries that contained markdown artifacts.
        # The presence of summary_v column marks this migration as done.
        try:
            conn.execute("ALTER TABLE lsj ADD COLUMN summary_v INTEGER DEFAULT 0")
            conn.execute("UPDATE lsj SET summary_json = NULL WHERE summary_json IS NOT NULL")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # already migrated
        try:
            conn.execute("ALTER TABLE abp_ext ADD COLUMN summary_json TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists
        # One-time: clear any abp_ext summaries generated before the G-prefix OR-clause
        # fix was deployed (they may have been generated from LSJ content instead of ABP).
        # The presence of abp_summary_v column marks this migration as done.
        try:
            conn.execute("ALTER TABLE abp_ext ADD COLUMN abp_summary_v INTEGER DEFAULT 0")
            conn.execute("UPDATE abp_ext SET summary_json = NULL WHERE summary_json IS NOT NULL")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # already migrated
        try:
            conn.execute("ALTER TABLE books ADD COLUMN sort_order INTEGER")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists
        # Persistent AI search result cache (survives restarts).
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS ai_search_cache (
                query      TEXT PRIMARY KEY,
                result_json TEXT NOT NULL,
                ver_key    TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_ai_cache_ver ON ai_search_cache(ver_key);
        """)
        conn.commit()
        # Indexed join key for the lexicon: strongs_g = 'G'||strongs (e.g. 'G4151').
        # Replaces the fragile SUBSTR(strongs_base,2) joins with equality on a real,
        # indexable key that can NEVER shave a digit off a bare number (the 592k
        # break) and inherently won't match a Hebrew H-number. Idempotent.
        try:
            conn.execute("ALTER TABLE lexicon ADD COLUMN strongs_g TEXT")
            conn.execute("UPDATE lexicon SET strongs_g = 'G' || strongs")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_lexicon_strongs_g ON lexicon(strongs_g)")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # already migrated
        # Phase 6 (backlog #5): tipnr.strongs is a PRIMARY KEY, so a name that is
        # BOTH a person AND a place under one Strong's number (e.g. Adam H121)
        # collapsed to whichever row imported LAST → entity_type/pn_type lied.
        # The fix keeps a type-SET per strongs in a new `entity_types` column
        # (e.g. 'person,place'). ONE row per strongs is preserved so the
        # `LEFT JOIN tipnr ON t.strongs = w.strongs_base` stays 1:1 (a composite
        # key would multiply word rows). This ALTER only makes the column EXIST so
        # the deployed code can SELECT it BEFORE import_tipnr.py is re-run on PA —
        # it stays NULL until then, so the frontend falls back to the old heuristic
        # and the deploy order is safe. Re-running import_tipnr.py populates it.
        # Additive + idempotent; never touches the words table / is_pn.
        try:
            conn.execute("ALTER TABLE tipnr ADD COLUMN entity_types TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # column already exists, or tipnr not present yet
        # The deployed DB already has kjv_* location/strongs_id indexes (created
        # directly on PA, not in git). Two were genuinely missing and made every
        # KJV/English match a scan: kjv_strongs.word_id (the join key into
        # kjv_words — only strongs_id was indexed) and the word text itself.
        # Idempotent; wrapped in case a partial DB lacks the tables.
        try:
            conn.executescript("""
                CREATE INDEX IF NOT EXISTS idx_kjv_strongs_word ON kjv_strongs(word_id);
                CREATE INDEX IF NOT EXISTS idx_kjv_words_word    ON kjv_words(word COLLATE NOCASE);
            """)
            conn.commit()
        except sqlite3.OperationalError:
            pass  # KJV tables not present in this DB
        # Same gap on BSB once it became a word-study source: bsb_strongs had only a
        # word_id index, so every lookup by Strong's number scanned the whole table.
        # (heb.db needs the twin index on heb_words.strongs, but startup never opens
        # heb.db, so that one is created by load_hebrew.py / by hand on PA.)
        try:
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_bsb_strongs_id ON bsb_strongs(strongs_id)"
            )
            conn.commit()
        except sqlite3.OperationalError:
            pass  # BSB tables not present in this DB
    finally:
        conn.close()

@app.errorhandler(429)
def rate_limit_handler(e):
    return jsonify({"error": f"Rate limit exceeded — {e.description}"}), 429


# Schema migration must finish before any request touches the DB, so it stays
# synchronous — but it's a no-op on an already-migrated database, so it's cheap.
_migrate_db()


# Everything below is heavy startup work the PAGE itself does NOT need: classifying
# function words (a big lexicon×LSJ read) and loading/cleaning the saved AI answers
# (several writes to bible.db). A freshly restarted PA worker used to run all of it
# BEFORE it would answer even the first request — so a hard-refresh right after a
# deploy could land on a still-booting worker and just sit there spinning. Run it in
# a background thread, kicked off once per worker on that worker's first request (so
# it works whatever PA's worker model is), and the worker hands back the page
# immediately while these fill in over the next few seconds. Each step already logs
# and swallows its own errors.
def _warm_caches():
    _build_function_strongs_cache()
    _build_heb_name_cache()
    # AI result cache (ai_search_cache): one-time sweep of pre-unification rows, then
    # each synthesis category loads/prunes only its own. _load_ai_cache_from_db handles
    # the 'search' category (bulk preload + prune); the others just prune their stale rows.
    ai_cache_drop_legacy()
    _load_ai_cache_from_db()
    _prune_summary_cache()
    _prune_chrono_cache()
    _prune_xref_cache()
    _prune_metav_cache()
    log.info("Startup cache warm-up finished.")


_warm_lock = threading.Lock()
_warm_started = False


@app.before_request
def _kick_cache_warm():
    """Spawn the one-time background cache warm-up on this worker's first request."""
    global _warm_started
    if _warm_started:
        return
    with _warm_lock:
        if not _warm_started:
            _warm_started = True
            threading.Thread(target=_warm_caches, name="warm-caches", daemon=True).start()


@app.route("/")
def index():
    return render_template("index.html")


# Conventional root-level files browsers and crawlers auto-request. The actual
# files live in static/; these routes just expose them at the paths clients
# expect (e.g. a browser always asks for /favicon.ico, iOS for the touch icon).
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(app.static_folder, "favicon.ico", mimetype="image/x-icon")


@app.route("/apple-touch-icon.png")
@app.route("/apple-touch-icon-precomposed.png")
def apple_touch_icon():
    return send_from_directory(app.static_folder, "apple-touch-icon.png", mimetype="image/png")


@app.route("/robots.txt")
def robots_txt():
    return send_from_directory(app.static_folder, "robots.txt", mimetype="text/plain")


# /sitemap.xml is generated by the seo blueprint (views_seo.py) — it lists every
# crawlable /read/ page, so it can't go stale as books/chapters change.


if __name__ == "__main__":
    app.run(debug=True)
