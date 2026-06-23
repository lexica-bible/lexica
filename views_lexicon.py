#!/usr/bin/env python3
"""Lexicon word-study routes.

The Lexicon tab's flow: smart lookup (Strong's/Greek/Hebrew/English) → word
profile → book distribution → per-book verse list. ABP Greek comes from the
words table; HEBREW words now source their occurrences from the real Hebrew OT
interlinear (heb.db → heb_words, STEP TAHOT) — the KJV's Strong's tagging is kept
only as an explicit fallback/secondary text. Gloss renderings are collapsed via
_normalize_gloss so case/whitespace/punct variants merge.
"""
import re
import sqlite3

from flask import Blueprint, jsonify, request

from core import db_ro, heb_db, _KJV_BOOK_ID, _FUNCTION_STRONGS, _strip_accents

bp = Blueprint("lexicon", __name__)

# Hebrew grammar-glue particles to drop from the English-word FINDER, the Hebrew analog
# of the Greek function-word drop (_FUNCTION_STRONGS). Bare H-numbers, kept DELIBERATELY
# tiny — only the untranslatable object marker אֵת (H853, the sign of a definite direct
# object), which a single stray KJV content-word tag was surfacing as junk (e.g.
# "created" → H853, total 10,944). NOT real prepositions like H854 "with" / H413 "to".
# Caveat: et's pronoun-suffix forms (ʼôtô "him", ʼôtām "them") carry the SAME number
# H853, so they drop from the finder too — still reachable by number, and other pronoun
# words cover "him/them". Only the finder is affected; the word page for H853 is unchanged.
_HEB_FUNCTION_STRONGS = frozenset({"853"})


def _word_gloss(conn, key):
    """Plain-meaning gloss from the word_gloss side table (scripts/build_word_gloss.py) for
    a full Strong's key ('G4151', 'G4521.2'). This is the plain sense that REPLACES the
    KJV-ized lexicon.kjv_def as the word-study card's dictionary meaning — the same source
    the reader word card reads. '' when the table isn't built or has no row, so every caller
    falls back to kjv_def and a deploy before the data is safe."""
    try:
        r = conn.execute("SELECT gloss FROM word_gloss WHERE strongs = ?", (key,)).fetchone()
    except sqlite3.OperationalError:
        return ""
    return (r["gloss"] or "").strip() if r else ""


def _greek_cognates(conn, snum, derivation):
    """Same-root family for a Greek word, derived on the fly from the lexicon's
    `derivation` text (no extra table): parent(s) = the G-numbers THIS word comes
    from; children = words whose derivation points back at this one. Returns up
    to 8 {strongs, lemma, translit, gloss}. Semantic (meaning-only) relatives are
    NOT covered — they aren't in the data."""
    out, seen = [], {snum}

    def add(sn):
        if sn in seen or len(out) >= 8:
            return
        seen.add(sn)
        r = conn.execute(
            "SELECT lemma, translit, kjv_def, strongs_def FROM lexicon WHERE strongs = ?", (sn,)
        ).fetchone()
        if not r or not r["lemma"]:
            return
        g = (_word_gloss(conn, f"G{sn}") or r["kjv_def"] or r["strongs_def"] or "").strip()
        g = re.split(r"[;,]", g)[0][:36] if g else ""
        out.append({"strongs": f"G{sn}", "lemma": r["lemma"], "translit": r["translit"] or "", "gloss": g})

    for pn in re.findall(r"G(\d+)", derivation or ""):   # parent(s)
        add(pn)
    if len(out) < 8:                                       # children
        for r in conn.execute(
            "SELECT strongs, derivation FROM lexicon WHERE derivation LIKE ?", (f"%G{snum}%",)
        ).fetchall():
            if re.search(rf"G{snum}(?!\d)", r["derivation"] or ""):
                add(r["strongs"])
                if len(out) >= 8:
                    break
    return out


_GLOSS_FUNC = {
    'a','an','the','my','his','her','your','their','our','its',
    'of','in','by','as','to','with','for','from','at','on','into',
    'is','are','was','were','be','been',
    'there','this','that','these','those',
    'and','or','not','no',
    'i','he','she','we','they','it',
    'up','out','off','over','under',
}

# For function-word renderings the meaningful label is the connector inside the
# phrase, not the content word. STRONG = prepositions / negatives / conjunctions
# (the actual sense of ἐν, οὐ, καί…); WEAK = articles / copulas / pronouns, used
# only when no strong connector is present.
_GLOSS_STRONG = {
    'in', 'into', 'by', 'with', 'to', 'unto', 'for', 'from', 'at', 'on', 'upon',
    'over', 'under', 'through', 'throughout', 'within', 'against', 'among',
    'amongst', 'near', 'onto', 'toward', 'towards', 'before', 'after', 'behind',
    'beside', 'about', 'concerning', 'during', 'of', 'off', 'out', 'around',
    'between', 'up', 'down',
    'not', 'no', 'nor', 'and', 'or', 'but', 'if', 'that', 'because', 'when',
    'while', 'as', 'than', 'so', 'then', 'therefore', 'lest', 'until', 'though',
    'yet',
}
_GLOSS_WEAK = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'am',
    'he', 'she', 'it', 'they', 'we', 'i', 'you', 'me', 'him', 'her', 'them', 'us',
    'this', 'these', 'those', 'my', 'his', 'your', 'their', 'our', 'its',
}


def _normalize_gloss(raw, is_func=False):
    import re
    # STEP TAHOT wraps SUPPLIED English words (added for sense, no standalone
    # Hebrew word behind them — KJV-italics style) in [ ]. They aren't the
    # rendering, so drop the whole [..] span and keep the real word ("mighty
    # [one]" -> "mighty", not "one"; also fixes the stray-bracket split where
    # "[men of]" used to leak a broken "[men"). Fall back to the de-bracketed
    # gloss only when dropping the supplied words leaves no content word at all
    # ("[men]" -> "men", "the [mighty]" -> "mighty").
    _drop = _GLOSS_FUNC | _GLOSS_STRONG | _GLOSS_WEAK
    core = re.sub(r'\[[^\]]*\]', ' ', raw)
    if not any(w not in _drop for w in re.findall(r"[a-z']+", core.lower())):
        core = raw.replace('[', ' ').replace(']', ' ')
    raw = core
    s = re.sub(r"'s\b", '', re.sub(r'^[^\w]+|[^\w]+$', '', raw.strip()).lower())
    words = s.split()
    if not words:
        return ''
    if is_func:
        # ABP lumps extra English onto a function word ("baked in", "in the way",
        # "shall not be"). The real rendering is the connector, not the content
        # word english_head would pick. Prefer a strong connector, then a weak
        # one; fall back to the first word only when the phrase has no connector
        # at all (a rare genuine ABP mis-alignment, dropped later as a singleton).
        for w in words:
            if w in _GLOSS_STRONG:
                return w
        for w in words:
            if w in _GLOSS_WEAK:
                return w
        return words[0]
    # Content word: trim connector/copula/pronoun/article words off BOTH ends so
    # an ABP lump like "God so" / "God and the" / "God, and" collapses to the
    # content head ("god"). _GLOSS_FUNC alone missed adverb/conjunction trailers
    # ("so", "then", "yet"), which then won the "last word" tie-break and leaked
    # as bogus renderings (Luk 12:28 "God so" -> "so"). Punctuation is stripped
    # per-token so a mid-phrase comma ("God, and") can't survive either.
    drop = _GLOSS_FUNC | _GLOSS_STRONG | _GLOSS_WEAK
    words = [w.strip(".,;:!?'\"") for w in words]
    words = [w for w in words if w]
    if not words:
        return ''
    while len(words) > 1 and words[0] in drop:
        words.pop(0)
    while len(words) > 1 and words[-1] in drop:
        words.pop()
    if len(words) > 1:
        words = [words[-1]]
    return words[0]


def _fold_glosses(pairs, is_func=False, drop_singletons=False, limit=None):
    """Normalize + merge (gloss, count) pairs into a sorted rendering list.

    Shared by the search list and the word page. `pairs` is any iterable of
    (raw_gloss, count). `is_func` routes function-word normalization;
    `drop_singletons` trims one-off filler renderings (word page only — see the
    inline notes); `limit` caps the list (search list shows a preview, the word
    page shows all).
    """
    counts = {}
    for gloss, cnt in pairs:
        key = _normalize_gloss(gloss, is_func=is_func)
        if key:
            counts[key] = counts.get(key, 0) + cnt
    items = sorted(counts.items(), key=lambda x: -x[1])
    if drop_singletons:
        if is_func:
            # Function word used thousands of times: a one-off rendering is noise.
            items = [(g, c) for g, c in items if c > 1]
        else:
            # Content word: drop a one-off that is ITSELF only a filler word
            # (a mis-tagged row with no content English to fall back to); keep
            # genuine rare content renderings.
            _filler = _GLOSS_FUNC | _GLOSS_STRONG | _GLOSS_WEAK
            items = [(g, c) for g, c in items if not (c == 1 and g in _filler)]
    if limit is not None:
        items = items[:limit]
    return [{"gloss": g, "count": c} for g, c in items]


def _dotted_ready(conn):
    """True when the ABP dotted-different-word side table is built (deploy-safe guard)."""
    try:
        return conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='dotted_lexicon'"
        ).fetchone() is not None
    except Exception:
        return False


def _dotted_diff_row(conn, num):
    """The dotted_lexicon row (lemma, translit) for a FULL dotted ABP number that is a
    genuinely DIFFERENT word from its base (e.g. '4521.2' σαβέκ "thicket" vs base σάββατον
    "sabbath"), else None. `num` is the bare number; dotted_lexicon is keyed by the
    G-prefixed full number ('G4521.2')."""
    if "." not in num or not _dotted_ready(conn):
        return None
    try:
        return conn.execute(
            "SELECT lemma, translit FROM dotted_lexicon WHERE strongs = ?", ("G" + num,)
        ).fetchone()
    except Exception:
        return None


def _abp_strongs_filter(conn, num, sid):
    """WHERE-predicate (sql, params) picking the ABP `words` rows for a lexicon key, aware
    of the dotted different-words side table:

      • a FULL dotted different-word (in dotted_lexicon) → ONLY its own rows, matched on
        the full bare `strongs` ('4521.2' → just σαβέκ);
      • a BASE number → `strongs_base`, but EXCLUDING the dotted different-words parked
        under it (so σαβέκ/G4521.2 stops counting under σάββατον/G4521; the εἰμί-family
        form-notes, which are NOT in dotted_lexicon, correctly stay on the base).

    Uses the `w` table alias and only the `words` table, so every ABP query here can drop
    it straight into its WHERE. Deploy-safe: with no dotted_lexicon a dotted key falls back
    to the base and the exclude is dropped. `num` = bare full number; `sid` = 'G'+base."""
    ready = _dotted_ready(conn)
    if ready and "." in num and conn.execute(
            "SELECT 1 FROM dotted_lexicon WHERE strongs = ?", ("G" + num,)).fetchone():
        return "w.strongs = ?", [num]
    if ready:
        return ("w.strongs_base = ? AND 'G' || w.strongs NOT IN (SELECT strongs FROM dotted_lexicon)", [sid])
    return "w.strongs_base = ?", [sid]


# ── Hebrew OT interlinear source (heb.db) ─────────────────────────────────────
# A Hebrew word's occurrences come from the REAL Hebrew text (heb_words, STEP
# TAHOT) rather than the KJV's Strong's tagging. heb_words.strongs is H-prefixed,
# zero-stripped ("H7307"); a few homograph forms carry a trailing letter, matched
# defensively the way views_seo.py does. Every read is deploy-safe: a missing or
# older heb.db raises OperationalError, which callers treat as "no Hebrew source"
# and fall back to KJV (so the route never 500s and an un-loaded heb.db is fine).
def _heb_ready():
    """True when heb.db is loaded (heb_words exists)."""
    try:
        c = heb_db()
        try:
            return c.execute("SELECT 1 FROM heb_words LIMIT 1").fetchone() is not None
        finally:
            c.close()
    except sqlite3.OperationalError:
        return False


def _heb_match(sid):
    """(predicate, params) selecting heb_words rows for an H-number, matching the
    exact key OR a trailing-letter homograph form (H1254a)."""
    return "(strongs = ? OR strongs GLOB ?)", (sid, sid + "[A-Za-z]")


def _heb_book_counts(hconn, sid):
    """{book abbrev: occurrence count} for an H-number across the Hebrew OT."""
    pred, params = _heb_match(sid)
    rows = hconn.execute(
        f"SELECT book, COUNT(*) AS cnt FROM heb_words WHERE {pred} GROUP BY book", params
    ).fetchall()
    return {r["book"]: r["cnt"] for r in rows}


def _heb_gloss_rows(hconn, sid):
    """Raw (gloss, cnt) rows — the contextual English glosses TAHOT gives the word."""
    pred, params = _heb_match(sid)
    return hconn.execute(
        f"SELECT gloss, COUNT(*) AS cnt FROM heb_words WHERE {pred} "
        f"AND gloss IS NOT NULL AND gloss != '' GROUP BY gloss", params
    ).fetchall()


def _bsb_ready(conn):
    """True when the BSB word tables are present (deploy-safe — older DBs lack them)."""
    try:
        return conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='bsb_strongs'"
        ).fetchone() is not None
    except Exception:
        return False


@bp.route("/api/lexicon/lookup")
def lexicon_lookup():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    conn = db_ro()
    try:
        m = re.match(r'^([GgHh]?)(\d+(?:\.\d+)?)$', q)
        if m:
            prefix = m.group(1).upper()
            num = m.group(2)
            snum = num.split('.')[0]
            is_heb = prefix == 'H' or (not prefix and int(snum) > 5624)
            if is_heb:
                row = conn.execute(
                    "SELECT strongs_id, lemma, xlit, description FROM bdb WHERE strongs_id = ?",
                    (f"H{snum}",)
                ).fetchone()
                if row:
                    return jsonify([{"strongs": row["strongs_id"], "lemma": row["lemma"] or "", "translit": row["xlit"] or "", "gloss": row["description"] or ""}])
            else:
                dl = _dotted_diff_row(conn, num)
                if dl:
                    # A dotted ABP number that's its own word (σαβέκ, not base σάββατον).
                    return jsonify([{"strongs": f"G{num}", "lemma": dl["lemma"] or "",
                                     "translit": dl["translit"] or "", "gloss": ""}])
                row = conn.execute(
                    "SELECT strongs, lemma, translit, kjv_def, derivation, strongs_def FROM lexicon WHERE strongs = ?",
                    (snum,)
                ).fetchone()
                if row:
                    # Plain-meaning gloss (word_gloss) leads; then the text-first chain
                    # (KJV rendering → derivation → Strong's paraphrase) so Strong's
                    # interpretive wording (e.g. G5020 "eternal torment") never leads.
                    gloss = (_word_gloss(conn, f"G{row['strongs']}")
                             or row["kjv_def"] or row["derivation"] or row["strongs_def"] or "")
                    return jsonify([{"strongs": f"G{row['strongs']}", "lemma": row["lemma"] or "", "translit": row["translit"] or "", "gloss": gloss}])
            return jsonify([])
        # English/transliteration search — Greek lexicon + Hebrew BDB. The
        # lemma/translit/xlit matches are accent-insensitive (strip_accents on
        # both sides) so a Latin transliteration ("pneuma") matches the stored
        # accented form ("pneûma"), and Greek/Hebrew typed without accents/points
        # still matches. Definition matches keep the raw query.
        qn = (_strip_accents(q) or q).lower()
        grk = conn.execute(
            """SELECT strongs, lemma, translit, kjv_def, derivation, strongs_def FROM lexicon
               WHERE strongs_def LIKE ? OR kjv_def LIKE ?
                  OR strip_accents(lower(translit)) LIKE ?
                  OR strip_accents(lower(lemma)) LIKE ?
               LIMIT 15""",
            (f"%{q}%", f"%{q}%", f"%{qn}%", f"%{qn}%")
        ).fetchall()
        heb = conn.execute(
            """SELECT strongs_id, lemma, xlit, description FROM bdb
               WHERE description LIKE ?
                  OR strip_accents(lower(lemma)) LIKE ?
                  OR strip_accents(lower(xlit)) LIKE ?
               LIMIT 10""",
            (f"%{q}%", f"%{qn}%", f"%{qn}%")
        ).fetchall()
        # ABP dotted different-words (σαβέκ, εφούδ…) live only in dotted_lexicon, not the
        # Greek lexicon, so search them by their own lemma/romanization too. Gloss = their
        # most-common ABP rendering.
        dot = []
        if _dotted_ready(conn):
            try:
                dot = conn.execute(
                    """SELECT dl.strongs, dl.lemma, dl.translit,
                              (SELECT w.english_head FROM words w
                                WHERE 'G' || w.strongs = dl.strongs
                                  AND w.english_head IS NOT NULL AND w.english_head != ''
                                GROUP BY w.english_head ORDER BY COUNT(*) DESC LIMIT 1) AS gloss
                       FROM dotted_lexicon dl
                       WHERE strip_accents(lower(dl.lemma)) LIKE ?
                          OR strip_accents(lower(dl.translit)) LIKE ?
                       LIMIT 10""",
                    (f"%{qn}%", f"%{qn}%")
                ).fetchall()
            except Exception:
                dot = []
        results = [{"strongs": f"G{r['strongs']}", "lemma": r["lemma"] or "", "translit": r["translit"] or "",
                    "gloss": _word_gloss(conn, f"G{r['strongs']}") or r["kjv_def"] or r["derivation"] or r["strongs_def"] or ""} for r in grk]
        results += [{"strongs": r["strongs_id"], "lemma": r["lemma"] or "", "translit": r["xlit"] or "", "gloss": r["description"] or ""} for r in heb]
        results += [{"strongs": r["strongs"], "lemma": r["lemma"] or "", "translit": r["translit"] or "", "gloss": r["gloss"] or ""} for r in dot]
        return jsonify(results[:20])
    finally:
        conn.close()


@bp.route("/api/lexicon/english")
def lexicon_english():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    corpus = request.args.get("corpus", "all")
    testament = request.args.get("testament", "all")  # all | ot | nt
    _NT = {"Mat","Mar","Luk","Joh","Act","Rom","1Co","2Co","Gal","Eph","Php","Col",
           "1Th","2Th","1Ti","2Ti","Tit","Phm","Heb","Jas","1Pe","2Pe","1Jn","2Jn","3Jn","Jud","Rev"}
    # Testament filters. ABP: join words→verses and test book membership in the
    # NT set. KJV: book_id >= 40 is the NT. Empty strings when no filter active.
    if testament in ("nt", "ot"):
        _nt_ph = ",".join("?" * len(_NT))
        _op = "IN" if testament == "nt" else "NOT IN"
        _abp_join = "JOIN verses v ON v.id = w.verse_id"
        _abp_where = f"AND v.book {_op} ({_nt_ph})"
        _abp_params = sorted(_NT)
        _kjv_where = "AND kw.book_id >= 40" if testament == "nt" else "AND kw.book_id < 40"
        _bsb_where = "AND bw.book_id >= 40" if testament == "nt" else "AND bw.book_id < 40"
    else:
        _abp_join = _abp_where = _kjv_where = _bsb_where = ""
        _abp_params = []
    conn = db_ro()

    def _top_glosses_abp(snums):
        if not snums:
            return {}
        # snums are GROUPING keys: a base 'G4521' or a dotted different-word 'G4521.2'.
        # Filter the (indexed) strongs_base by the BASE of each key, then GROUP BY the
        # gkey so a dotted different-word's renderings split off from its base's.
        bases = sorted({sn.split(".")[0] for sn in snums})
        placeholders = ",".join("?" * len(bases))
        ready = _dotted_ready(conn)
        dl_join = "LEFT JOIN dotted_lexicon dl ON dl.strongs = 'G' || w.strongs" if ready else ""
        gkey = "COALESCE(dl.strongs, w.strongs_base)" if ready else "w.strongs_base"
        rows = conn.execute(f"""
            SELECT {gkey} AS gkey, w.english_head, COUNT(*) AS cnt
            FROM words w {dl_join} {_abp_join}
            WHERE w.strongs_base IN ({placeholders})
              AND w.english_head IS NOT NULL AND w.english_head != ''
              {_abp_where}
            GROUP BY {gkey}, w.english_head
            ORDER BY {gkey}, cnt DESC
        """, (*bases, *_abp_params)).fetchall()
        out = {}
        for r in rows:
            sn = r["gkey"]
            g = r["english_head"]
            if " " in g:
                continue
            if sn not in out:
                out[sn] = []
            if len(out[sn]) < 8:
                out[sn].append({"gloss": g, "count": r["cnt"]})
        return out

    def _top_glosses_heb(snums):
        if not snums:
            return {}
        placeholders = ",".join("?" * len(snums))
        rows = conn.execute(f"""
            SELECT ks.strongs_id, kw.word, COUNT(*) AS cnt
            FROM kjv_words kw
            JOIN kjv_strongs ks ON ks.word_id = kw.word_id
            WHERE ks.strongs_id IN ({placeholders})
              AND (kw.italic IS NULL OR kw.italic = 0)
              {_kjv_where}
            GROUP BY ks.strongs_id, kw.word
            ORDER BY ks.strongs_id, cnt DESC
        """, snums).fetchall()
        out = {}
        for r in rows:
            sn = r["strongs_id"]
            if sn not in out:
                out[sn] = []
            if len(out[sn]) < 8:
                out[sn].append({"gloss": r["word"], "count": r["cnt"]})
        return out

    def _top_glosses_hebdb(snums):
        # Real Hebrew OT (heb.db) renderings per H-number — the "Hebrew renders as" line.
        h_sids = [s for s in snums if s.startswith("H")]
        if not h_sids or not _heb_ready():
            return {}
        out = {}
        try:
            hconn = heb_db()
            try:
                ph = ",".join("?" * len(h_sids))
                rows = hconn.execute(
                    f"SELECT strongs, gloss, COUNT(*) AS cnt FROM heb_words "
                    f"WHERE strongs IN ({ph}) AND gloss IS NOT NULL AND gloss != '' "
                    f"GROUP BY strongs, gloss ORDER BY strongs, cnt DESC", h_sids).fetchall()
            finally:
                hconn.close()
        except sqlite3.OperationalError:
            return {}
        for r in rows:
            out.setdefault(r["strongs"], [])
            if len(out[r["strongs"]]) < 8:
                out[r["strongs"]].append({"gloss": r["gloss"], "count": r["cnt"]})
        return out

    def _top_glosses_bsb(snums):
        # BSB renderings per Strong's number — the "BSB renders as" line.
        if not snums or not _bsb_ready(conn):
            return {}
        ph = ",".join("?" * len(snums))
        rows = conn.execute(f"""
            SELECT bs.strongs_id, bw.word, COUNT(*) AS cnt
            FROM bsb_words bw JOIN bsb_strongs bs ON bs.word_id = bw.word_id
            WHERE bs.strongs_id IN ({ph})
              AND (bw.italic IS NULL OR bw.italic = 0)
              {_bsb_where}
            GROUP BY bs.strongs_id, bw.word
            ORDER BY bs.strongs_id, cnt DESC
        """, snums).fetchall()
        out = {}
        for r in rows:
            sn = r["strongs_id"]
            if sn not in out:
                out[sn] = []
            if len(out[sn]) < 8:
                out[sn].append({"gloss": r["word"], "count": r["cnt"]})
        return out

    # TOTAL occurrences of each found number, PER source — the count shown on each
    # "renders as" line. These count EVERY occurrence (not just the ones rendered as
    # the search word), and they count the SAME way the Word-study profile does
    # (lexicon_profile's *_book_counts), so the finder's per-source number matches the
    # number you see when you open that word. The OT/NT filter is honored (same WHERE
    # as the gloss helpers); heb.db is OT-only so it takes no testament filter.
    def _totals_abp(snums):
        bases = sorted({sn.split(".")[0] for sn in snums if sn.startswith("G")})
        if not bases:
            return {}
        ph = ",".join("?" * len(bases))
        ready = _dotted_ready(conn)
        dl_join = "LEFT JOIN dotted_lexicon dl ON dl.strongs = 'G' || w.strongs" if ready else ""
        gkey = "COALESCE(dl.strongs, w.strongs_base)" if ready else "w.strongs_base"
        rows = conn.execute(f"""
            SELECT {gkey} AS gkey, COUNT(*) AS cnt
            FROM words w {dl_join} {_abp_join}
            WHERE w.strongs_base IN ({ph}) {_abp_where}
            GROUP BY {gkey}
        """, (*bases, *_abp_params)).fetchall()
        return {r["gkey"]: r["cnt"] for r in rows}

    def _totals_kjv(snums):
        if not snums:
            return {}
        ph = ",".join("?" * len(snums))
        rows = conn.execute(f"""
            SELECT ks.strongs_id AS sid, COUNT(*) AS cnt
            FROM kjv_words kw JOIN kjv_strongs ks ON ks.word_id = kw.word_id
            WHERE ks.strongs_id IN ({ph}) {_kjv_where}
            GROUP BY ks.strongs_id
        """, snums).fetchall()
        return {r["sid"]: r["cnt"] for r in rows}

    def _totals_bsb(snums):
        if not snums or not _bsb_ready(conn):
            return {}
        ph = ",".join("?" * len(snums))
        rows = conn.execute(f"""
            SELECT bs.strongs_id AS sid, COUNT(*) AS cnt
            FROM bsb_words bw JOIN bsb_strongs bs ON bs.word_id = bw.word_id
            WHERE bs.strongs_id IN ({ph}) {_bsb_where}
            GROUP BY bs.strongs_id
        """, snums).fetchall()
        return {r["sid"]: r["cnt"] for r in rows}

    def _totals_hebdb(snums):
        h_sids = [s for s in snums if s.startswith("H")]
        if not h_sids or not _heb_ready():
            return {}
        out = {}
        try:
            hconn = heb_db()
            try:
                for sid in h_sids:
                    # Count the SAME way lexicon_profile does (_heb_match: exact number OR a
                    # trailing-letter homograph like H1254a), so the finder's HEB number
                    # equals the count on that word's own study page.
                    pred, params = _heb_match(sid)
                    row = hconn.execute(
                        f"SELECT COUNT(*) AS cnt FROM heb_words WHERE {pred}", params).fetchone()
                    if row and row["cnt"]:
                        out[sid] = row["cnt"]
            finally:
                hconn.close()
        except sqlite3.OperationalError:
            return {}
        return out

    try:
        abp_rows, heb_rows = [], []

        if corpus in ("abp", "all"):
            # ABP Greek: match by english_head. A dotted different-word (e.g. σαβέκ G4521.2,
            # parked under σάββατον G4521) groups under its OWN full number via
            # dotted_lexicon — own lemma/romanization, not folded into the base.
            ready = _dotted_ready(conn)
            dl_join = "LEFT JOIN dotted_lexicon dl ON dl.strongs = 'G' || w.strongs" if ready else ""
            gkey = "COALESCE(dl.strongs, w.strongs_base)" if ready else "w.strongs_base"
            lem  = "COALESCE(dl.lemma, l.lemma)"          if ready else "l.lemma"
            tr   = "COALESCE(dl.translit, l.translit)"    if ready else "l.translit"
            abp_rows = conn.execute(f"""
                SELECT {gkey} AS sbase,
                       {lem} AS lemma, {tr} AS translit,
                       COUNT(*) AS cnt
                FROM words w
                LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base
                {dl_join}
                {_abp_join}
                WHERE w.english_head = ? COLLATE NOCASE
                  AND w.strongs_base IS NOT NULL
                  AND w.strongs_base != '*'
                  AND w.strongs_base LIKE 'G%'
                  {_abp_where}
                GROUP BY {gkey}
                ORDER BY cnt DESC
                LIMIT 20
            """, (q, *_abp_params)).fetchall()
            # Drop function-word Strong's (ἐν, the article, conjunctions…). They
            # only reach an English-text lookup via a stray phrase-gloss whose
            # english_head borrowed a content noun ("in blessing" → head
            # "blessing"), so a content search like "blessing" would otherwise
            # surface them as junk hits. The Search tab filters them the same way.
            abp_rows = [r for r in abp_rows
                        if r["sbase"][1:] not in _FUNCTION_STRONGS]

        if corpus in ("kjv", "all"):
            # KJV words → strongs: BOTH NT Greek (G) and OT Hebrew (H).
            heb_rows = conn.execute(f"""
                SELECT ks.strongs_id AS sbase,
                       COALESCE(l.lemma, b.lemma)   AS lemma,
                       COALESCE(l.translit, b.xlit) AS translit,
                       COUNT(*) AS cnt
                FROM kjv_words kw
                JOIN kjv_strongs ks ON ks.word_id = kw.word_id
                LEFT JOIN lexicon l ON l.strongs_g = ks.strongs_id
                LEFT JOIN bdb b ON b.strongs_id = ks.strongs_id AND ks.strongs_id LIKE 'H%'
                WHERE kw.word = ? COLLATE NOCASE
                  AND (kw.italic IS NULL OR kw.italic = 0)
                  {_kjv_where}
                GROUP BY ks.strongs_id
                ORDER BY cnt DESC
                LIMIT 10
            """, (q,)).fetchall()
            # Drop Greek function words (δέ, the article, conjunctions…) the same
            # way the ABP branch does — whether KJV is viewed alone or via 'all'. A
            # lone stray-tagged KJV token (e.g. one "spirit" mistagged G1161 δέ)
            # shouldn't surface as a rendering.
            heb_rows = [r for r in heb_rows
                        if not (r["sbase"].startswith("G")
                                and r["sbase"][1:] in _FUNCTION_STRONGS)]
            if corpus == "all":
                # ABP already carries Greek via its own english_head (LXX OT + NT,
                # counted natively). Drop KJV Greek numbers ABP already listed so a
                # word never appears twice, but KEEP KJV Greek whose ABP gloss
                # differs (e.g. G4352 προσκυνέω — ABP head isn't "worship") so 'All'
                # is a true superset.
                abp_set = {r["sbase"] for r in abp_rows}
                heb_rows = [r for r in heb_rows if r["sbase"] not in abp_set]

        if corpus == "heb" and _heb_ready():
            # Hebrew OT discovery (heb.db): H-numbers whose real contextual gloss uses q
            # as a whole word — the actual Hebrew source, not the KJV's tagging, so the
            # found set + counts are a true reflection. ('All' stays ABP+KJV above.)
            rx = re.compile(r"\b" + re.escape(q) + r"\b", re.I)
            hconn = heb_db()
            try:
                grows = hconn.execute(
                    "SELECT strongs, gloss, COUNT(*) AS cnt FROM heb_words "
                    "WHERE strongs LIKE 'H%' AND gloss LIKE ? COLLATE NOCASE "
                    "GROUP BY strongs, gloss", (f"%{q}%",)).fetchall()
            finally:
                hconn.close()
            agg = {}
            for r in grows:
                if rx.search(r["gloss"] or ""):
                    agg[r["strongs"]] = agg.get(r["strongs"], 0) + r["cnt"]
            if agg:
                ph = ",".join("?" * len(agg))
                meta = {m["strongs_id"]: m for m in conn.execute(
                    f"SELECT strongs_id, lemma, xlit FROM bdb WHERE strongs_id IN ({ph})",
                    list(agg.keys())).fetchall()}
                for hsid, cnt in sorted(agg.items(), key=lambda x: -x[1])[:20]:
                    m = meta.get(hsid)
                    heb_rows.append({"sbase": hsid,
                                     "lemma": (m["lemma"] if m else "") or "",
                                     "translit": (m["xlit"] if m else "") or "",
                                     "cnt": cnt})

        if corpus == "bsb" and _bsb_ready(conn):
            # BSB discovery: the G+H numbers BSB renders as q (mirrors the KJV branch).
            brows = conn.execute(f"""
                SELECT bs.strongs_id AS sbase,
                       COALESCE(l.lemma, b.lemma)   AS lemma,
                       COALESCE(l.translit, b.xlit) AS translit,
                       COUNT(*) AS cnt
                FROM bsb_words bw
                JOIN bsb_strongs bs ON bs.word_id = bw.word_id
                LEFT JOIN lexicon l ON l.strongs_g = bs.strongs_id
                LEFT JOIN bdb b ON b.strongs_id = bs.strongs_id AND bs.strongs_id LIKE 'H%'
                WHERE bw.word = ? COLLATE NOCASE
                  AND (bw.italic IS NULL OR bw.italic = 0)
                  {_bsb_where}
                GROUP BY bs.strongs_id
                ORDER BY cnt DESC
                LIMIT 10
            """, (q,)).fetchall()
            heb_rows = heb_rows + [r for r in brows
                                   if not (r["sbase"].startswith("G") and r["sbase"][1:] in _FUNCTION_STRONGS)]

        # Drop Hebrew grammar-glue particles (the object marker H853) — the Hebrew analog
        # of the Greek function-word drop above. A stray KJV content-word tag shouldn't
        # surface the object marker as a "word rendered <X>".
        heb_rows = [r for r in heb_rows
                    if not (r["sbase"].startswith("H") and r["sbase"][1:] in _HEB_FUNCTION_STRONGS)]
        all_snums = [r["sbase"] for r in abp_rows] + [r["sbase"] for r in heb_rows]
        # Each row carries BOTH Bibles' renderings as SEPARATE lists (the UI shows
        # an ABP line + a KJV line). Row COUNT stays native-per-corpus (Greek from
        # ABP, Hebrew from KJV — not summed; summing double-counts the shared Greek
        # NT). The ABP/KJV filters gate which lists fill; 'all' fills both.
        # All four Bibles' renderings for every found word, so each row shows the full
        # ABP / Hebrew OT / KJV / BSB comparison regardless of which corpus filter found it.
        abp_gmap = _top_glosses_abp(all_snums)
        kjv_gmap = _top_glosses_heb(all_snums)
        hebdb_gmap = _top_glosses_hebdb(all_snums)
        bsb_gmap = _top_glosses_bsb(all_snums)
        abp_tot = _totals_abp(all_snums)
        kjv_tot = _totals_kjv(all_snums)
        hebdb_tot = _totals_hebdb(all_snums)
        bsb_tot = _totals_bsb(all_snums)

        def _fold(gmap, sbase):
            return _fold_glosses(((g["gloss"], g["count"]) for g in gmap.get(sbase, [])), limit=8)

        results = []
        def _emit(rows):
            for r in rows:
                results.append({"strongs": r["sbase"], "lemma": r["lemma"] or "",
                                "translit": r["translit"] or "", "count": r["cnt"],
                                "abp_glosses": _fold(abp_gmap, r["sbase"]),
                                "heb_glosses": _fold(hebdb_gmap, r["sbase"]),
                                "kjv_glosses": _fold(kjv_gmap, r["sbase"]),
                                "bsb_glosses": _fold(bsb_gmap, r["sbase"]),
                                "abp_total": abp_tot.get(r["sbase"]),
                                "heb_total": hebdb_tot.get(r["sbase"]),
                                "kjv_total": kjv_tot.get(r["sbase"]),
                                "bsb_total": bsb_tot.get(r["sbase"])})
        _emit(abp_rows)
        _emit(heb_rows)
        results.sort(key=lambda x: -x["count"])
        return jsonify(results)
    finally:
        conn.close()


@bp.route("/api/lexicon/profile/<strongs>")
def lexicon_profile(strongs):
    m = re.match(r'^([GgHh]?)(\d+(?:\.\d+)?)$', strongs.strip())
    if not m:
        return jsonify({"error": "invalid"}), 400
    prefix = m.group(1).upper()
    num = m.group(2)
    snum = num.split('.')[0]
    is_heb = prefix == 'H' or (not prefix and int(snum) > 5624)
    _deriv_raw = ""
    is_diff = False   # set True below for an ABP dotted number that's its own word
    conn = db_ro()
    try:
        if is_heb:
            strongs_id = f"H{snum}"
            row = conn.execute(
                "SELECT lemma, xlit, description FROM bdb WHERE strongs_id = ?", (strongs_id,)
            ).fetchone()
            if not row:
                return jsonify({"error": "not found"}), 404
            lemma, translit, definition = row["lemma"] or "", row["xlit"] or "", row["description"] or ""
            derivation = ""   # BDB has no separate etymology column
        else:
            dl = _dotted_diff_row(conn, num)
            if dl:
                # A dotted ABP number that is a genuinely DIFFERENT word from its base
                # (e.g. G4521.2 σαβέκ "thicket", not base σάββατον "sabbath"). Its own
                # lemma/romanization come from dotted_lexicon; the Definition section is
                # filled client-side by /api/lsj's abp_ext lookup on the full dotted number,
                # so we don't borrow the base lexicon entry — that's a different word. KJV
                # has no such word (it's an LXX-only added word), so its side stays empty.
                is_diff = True
                strongs_id = f"G{num}"
                lemma = dl["lemma"] or ""
                translit = dl["translit"] or ""
                # Its own plain gloss by the FULL dotted key (word_gloss glosses dotted-
                # different words by their own lemma); else "" and the client LSJ/abp_ext
                # lookup fills the Definition section.
                definition = _word_gloss(conn, f"G{num}")
                derivation = ""
            else:
                strongs_id = f"G{snum}"
                row = conn.execute(
                    "SELECT lemma, translit, kjv_def, derivation, strongs_def FROM lexicon WHERE strongs = ?", (snum,)
                ).fetchone()
                if not row:
                    return jsonify({"error": "not found"}), 404
                lemma = row["lemma"] or ""
                translit = row["translit"] or ""
                # Plain-meaning gloss (word_gloss) leads — same dictionary sense the reader
                # card shows — then the text-first chain (KJV rendering → derivation →
                # Strong's paraphrase) so Strong's interpretive wording never leads.
                definition = (_word_gloss(conn, strongs_id)
                              or row["kjv_def"] or row["derivation"] or row["strongs_def"] or "")
                _deriv_raw = row["derivation"] or ""
                # Etymology for the card's Derivation section (only when it adds
                # something the definition line isn't already showing).
                derivation = _deriv_raw if (row["kjv_def"] or "").strip() else ""
        sid = f"H{snum}" if is_heb else f"G{snum}"   # base lexicon key (Hebrew sources from heb.db below)
        # Hebrew words source occurrences from the real Hebrew OT (heb.db), not the
        # KJV's Strong's tagging. KJV stays as an explicit toggle (KJV-as-text). A few
        # H-numbers TAHOT files under a parent lemma (byforms like H3212→H1980, Aramaic,
        # name-compounds) aren't in heb.db → has_heb False, and the word falls back to KJV.
        heb_counts, heb_gloss_rows, has_heb = {}, [], False
        if is_heb and _heb_ready():
            hconn = heb_db()
            try:
                heb_counts = _heb_book_counts(hconn, sid)
                heb_gloss_rows = _heb_gloss_rows(hconn, sid)
            finally:
                hconn.close()
            has_heb = bool(heb_counts)
        # Corpus: default H→heb (KJV fallback when heb.db lacks the number), G→abp; ?corpus= overrides
        _heb_default = "heb" if has_heb else "kjv"
        corpus = request.args.get("corpus", _heb_default if is_heb else "abp")
        if corpus == "all":  # profile is single-corpus; 'all' would double-count NT
            corpus = _heb_default if is_heb else "abp"
        if corpus == "heb" and not has_heb:  # asked for heb but heb.db lacks this number
            corpus = "kjv"
        if is_diff:          # ABP-only added word — no KJV side to toggle to
            corpus = "abp"
        _NT = {"Mat","Mar","Luk","Joh","Act","Rom","1Co","2Co","Gal","Eph","Php","Col",
               "1Th","2Th","1Ti","2Ti","Tit","Phm","Heb","Jas","1Pe","2Pe","1Jn","2Jn","3Jn","Jud","Rev"}
        book_meta = {r["abbrev"]: {"name": r["name"], "testament": "NT" if r["abbrev"] in _NT else "OT"}
                     for r in conn.execute("SELECT abbrev, name FROM books").fetchall()}
        abbrev_by_id = {v: k for k, v in _KJV_BOOK_ID.items()}

        def _abp_book_counts():  # ABP interlinear: strongs_base in words→verses
            pred, params = _abp_strongs_filter(conn, num, sid)
            rows = conn.execute(f"""
                SELECT v.book AS book, COUNT(*) AS cnt
                FROM words w JOIN verses v ON w.verse_id = v.id
                WHERE {pred} GROUP BY v.book
            """, params).fetchall()
            return {r["book"]: r["cnt"] for r in rows}

        def _kjv_book_counts():  # KJV text: strongs_id in kjv_strongs→kjv_words
            rows = conn.execute("""
                SELECT kw.book_id AS book_id, COUNT(*) AS cnt
                FROM kjv_strongs ks JOIN kjv_words kw ON kw.word_id = ks.word_id
                WHERE ks.strongs_id = ? GROUP BY kw.book_id
            """, (sid,)).fetchall()
            out = {}
            for r in rows:
                abbrev = abbrev_by_id.get(r["book_id"], "")
                if abbrev:
                    out[abbrev] = out.get(abbrev, 0) + r["cnt"]
            return out

        def _abp_gloss_rows():
            pred, params = _abp_strongs_filter(conn, num, sid)
            return conn.execute(f"""
                SELECT w.english AS gloss, COUNT(*) AS cnt FROM words w
                WHERE {pred} AND w.english IS NOT NULL AND w.english != '' AND w.english != '*'
                GROUP BY w.english
            """, params).fetchall()

        def _kjv_gloss_rows():
            return conn.execute("""
                SELECT kw.word AS gloss, COUNT(*) AS cnt
                FROM kjv_strongs ks JOIN kjv_words kw ON kw.word_id = ks.word_id
                WHERE ks.strongs_id = ? GROUP BY kw.word
            """, (sid,)).fetchall()

        def _bsb_book_counts():  # BSB text: strongs_id in bsb_strongs→bsb_words
            if not _bsb_ready(conn):
                return {}
            rows = conn.execute("""
                SELECT bw.book_id AS book_id, COUNT(*) AS cnt
                FROM bsb_strongs bs JOIN bsb_words bw ON bw.word_id = bs.word_id
                WHERE bs.strongs_id = ? GROUP BY bw.book_id
            """, (sid,)).fetchall()
            out = {}
            for r in rows:
                abbrev = abbrev_by_id.get(r["book_id"], "")
                if abbrev:
                    out[abbrev] = out.get(abbrev, 0) + r["cnt"]
            return out

        def _bsb_gloss_rows():
            if not _bsb_ready(conn):
                return []
            return conn.execute("""
                SELECT bw.word AS gloss, COUNT(*) AS cnt
                FROM bsb_strongs bs JOIN bsb_words bw ON bw.word_id = bs.word_id
                WHERE bs.strongs_id = ? GROUP BY bw.word
            """, (sid,)).fetchall()

        # corpus=all merges the ABP + KJV distributions/glosses by book/rendering.
        book_counts = {}
        if corpus in ("abp", "all"):
            for b, c in _abp_book_counts().items():
                book_counts[b] = book_counts.get(b, 0) + c
        if corpus == "heb":
            for b, c in heb_counts.items():
                book_counts[b] = book_counts.get(b, 0) + c
        if corpus == "bsb":
            for b, c in _bsb_book_counts().items():
                book_counts[b] = book_counts.get(b, 0) + c
        if corpus in ("kjv", "all"):
            for b, c in _kjv_book_counts().items():
                book_counts[b] = book_counts.get(b, 0) + c
        books = [{"book": b, "name": book_meta.get(b, {}).get("name", b),
                  "testament": book_meta.get(b, {}).get("testament", ""), "count": c}
                 for b, c in sorted(book_counts.items(), key=lambda x: -x[1])]
        total = sum(b["count"] for b in books)

        # Function-word Strong's (ἐν, the article, οὐ, καί…): label by the
        # connector inside the phrase, not the content word english_head picked.
        is_func = (not is_heb) and (not is_diff) and snum in _FUNCTION_STRONGS

        # Each Bible's own renderings, so the word page can show both at once
        # (ABP says "phantom", KJV says "spirit"). The active toggle still drives
        # `glosses` (the interactive list). Profile corpus is only ever abp/kjv.
        def _fold(rows):
            return _fold_glosses(((r["gloss"], r["cnt"]) for r in rows),
                                 is_func=is_func, drop_singletons=True)
        abp_glosses = _fold(_abp_gloss_rows())
        kjv_glosses = [] if is_diff else _fold(_kjv_gloss_rows())
        heb_glosses = _fold(heb_gloss_rows) if has_heb else []
        bsb_glosses = [] if is_diff else _fold(_bsb_gloss_rows())
        glosses = (heb_glosses if corpus == "heb"
                   else bsb_glosses if corpus == "bsb"
                   else abp_glosses if corpus == "abp" else kjv_glosses)
        # Which corpora actually have this strongs (so the UI can gray unavailable
        # toggles). Checks real data — so backfilled proper-noun Hebrew (which DO
        # have ABP/words rows) keep ABP enabled. A dotted different-word is ABP-only.
        _hp, _hpar = _abp_strongs_filter(conn, num, sid)
        has_abp = conn.execute(f"SELECT 1 FROM words w WHERE {_hp} LIMIT 1", _hpar).fetchone() is not None
        has_kjv = False if is_diff else (conn.execute("SELECT 1 FROM kjv_strongs WHERE strongs_id = ? LIMIT 1", (sid,)).fetchone() is not None)
        has_bsb = False if is_diff else (_bsb_ready(conn) and conn.execute("SELECT 1 FROM bsb_strongs WHERE strongs_id = ? LIMIT 1", (sid,)).fetchone() is not None)
        related = [] if is_diff else (_greek_cognates(conn, snum, _deriv_raw) if not is_heb else [])
        return jsonify({"strongs": strongs_id, "lemma": lemma, "translit": translit, "definition": definition, "derivation": derivation, "related": related, "total": total, "books": books, "corpus": corpus, "glosses": glosses, "abp_glosses": abp_glosses, "kjv_glosses": kjv_glosses, "heb_glosses": heb_glosses, "bsb_glosses": bsb_glosses, "has_abp": has_abp, "has_kjv": has_kjv, "has_heb": has_heb, "has_bsb": has_bsb})
    except Exception:
        return jsonify({"error": "Server error"}), 500
    finally:
        conn.close()


@bp.route("/api/lexicon/books/<strongs>")
def lexicon_books(strongs):
    m = re.match(r'^([GgHh]?)(\d+(?:\.\d+)?)$', strongs.strip())
    if not m:
        return jsonify({"error": "invalid"}), 400
    prefix, num = m.group(1).upper(), m.group(2)
    snum = num.split('.')[0]
    is_heb = prefix == "H"
    corpus = request.args.get("corpus", "kjv" if is_heb else "abp")
    if corpus == "all":
        corpus = "kjv" if is_heb else "abp"
    gloss = request.args.get("gloss", "").strip().lower()
    conn = db_ro()
    try:
        _NT = {"Mat","Mar","Luk","Joh","Act","Rom","1Co","2Co","Gal","Eph","Php","Col",
               "1Th","2Th","1Ti","2Ti","Tit","Phm","Heb","Jas","1Pe","2Pe","1Jn","2Jn","3Jn","Jud","Rev"}
        book_meta = {r["abbrev"]: {"name": r["name"], "testament": "NT" if r["abbrev"] in _NT else "OT"}
                     for r in conn.execute("SELECT abbrev, name FROM books").fetchall()}
        abbrev_by_id = {v: k for k, v in _KJV_BOOK_ID.items()}
        sid = f"H{snum}" if is_heb else f"G{snum}"
        is_func = (not is_heb) and snum in _FUNCTION_STRONGS
        book_counts = {}  # corpus=all merges ABP + KJV per book (gloss-filtered)
        if corpus in ("abp", "all"):
            _bp, _bpar = _abp_strongs_filter(conn, num, sid)
            for r in conn.execute(f"""
                SELECT v.book, w.english, COUNT(*) AS cnt
                FROM words w JOIN verses v ON w.verse_id = v.id
                WHERE {_bp}
                GROUP BY v.book, w.english
            """, _bpar).fetchall():
                if gloss and _normalize_gloss(r["english"] or "", is_func=is_func) != gloss:
                    continue
                book_counts[r["book"]] = book_counts.get(r["book"], 0) + r["cnt"]
        if corpus == "heb" and _heb_ready():
            hconn = heb_db()
            try:
                pred, hp = _heb_match(sid)
                for r in hconn.execute(
                    f"SELECT book, gloss, COUNT(*) AS cnt FROM heb_words WHERE {pred} "
                    f"GROUP BY book, gloss", hp).fetchall():
                    if gloss and _normalize_gloss(r["gloss"] or "") != gloss:
                        continue
                    book_counts[r["book"]] = book_counts.get(r["book"], 0) + r["cnt"]
            finally:
                hconn.close()
        if corpus in ("kjv", "all"):
            for r in conn.execute("""
                SELECT kw.book_id, kw.word AS english, COUNT(*) AS cnt
                FROM kjv_strongs ks JOIN kjv_words kw ON kw.word_id = ks.word_id
                WHERE ks.strongs_id = ?
                GROUP BY kw.book_id, kw.word
            """, (sid,)).fetchall():
                if gloss and _normalize_gloss(r["english"] or "", is_func=is_func) != gloss:
                    continue
                abbrev = abbrev_by_id.get(r["book_id"], "")
                if abbrev:
                    book_counts[abbrev] = book_counts.get(abbrev, 0) + r["cnt"]
        if corpus == "bsb" and _bsb_ready(conn):
            for r in conn.execute("""
                SELECT bw.book_id, bw.word AS english, COUNT(*) AS cnt
                FROM bsb_strongs bs JOIN bsb_words bw ON bw.word_id = bs.word_id
                WHERE bs.strongs_id = ?
                GROUP BY bw.book_id, bw.word
            """, (sid,)).fetchall():
                if gloss and _normalize_gloss(r["english"] or "", is_func=is_func) != gloss:
                    continue
                abbrev = abbrev_by_id.get(r["book_id"], "")
                if abbrev:
                    book_counts[abbrev] = book_counts.get(abbrev, 0) + r["cnt"]
        books = [{"book": b, "name": book_meta.get(b, {}).get("name", b),
                  "testament": book_meta.get(b, {}).get("testament", ""), "count": c}
                 for b, c in sorted(book_counts.items(), key=lambda x: -x[1])]
        return jsonify({"books": books})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@bp.route("/api/lexicon/verses/<strongs>/<book>")
def lexicon_verses(strongs, book):
    m = re.match(r'^([GgHh]?)(\d+(?:\.\d+)?)$', strongs.strip())
    if not m:
        return jsonify([])
    prefix = m.group(1).upper()
    num = m.group(2)
    snum = num.split('.')[0]
    is_heb = prefix == 'H' or (not prefix and int(snum) > 5624)
    corpus = request.args.get("corpus", "kjv" if is_heb else "abp")
    gloss = request.args.get("gloss", "").strip()
    is_func = (not is_heb) and snum in _FUNCTION_STRONGS
    conn = db_ro()
    try:
        sid = f"H{snum}" if is_heb else f"G{snum}"
        if corpus == "all":  # verse text is single-corpus; show the word's native text
            corpus = "kjv" if is_heb else "abp"
        if corpus == "heb":
            # Real Hebrew OT: which verses in this book carry the word (the frontend's
            # VerseRow re-fetches each verse's Hebrew words from /api/hebrew to display
            # + highlight, so we only return the verse keys + the rendering breakdown).
            if not _heb_ready():
                conn.close()
                return jsonify({"verses": [], "glosses": []})
            hconn = heb_db()
            try:
                pred, hp = _heb_match(sid)
                occ = hconn.execute(
                    f"SELECT chapter, verse, gloss FROM heb_words "
                    f"WHERE book = ? AND {pred} ORDER BY chapter, verse",
                    (book, *hp)).fetchall()
            finally:
                hconn.close()
            conn.close()
            gloss_counts, seen, vout = {}, set(), []
            for r in occ:
                norm = _normalize_gloss(r["gloss"] or "")
                if norm:
                    gloss_counts[norm] = gloss_counts.get(norm, 0) + 1
                if gloss and norm != gloss:
                    continue
                key = (r["chapter"], r["verse"])
                if key in seen:
                    continue
                seen.add(key)
                vout.append({"chapter": r["chapter"], "verse": r["verse"]})
            result_glosses = sorted([{"gloss": g, "count": c} for g, c in gloss_counts.items()],
                                    key=lambda x: -x["count"])
            return jsonify({"verses": vout, "glosses": result_glosses})
        if corpus == "bsb":
            # BSB occurrences: which verses in this book carry the word (VerseRow
            # re-fetches each verse's BSB words from /api/bsb to display + highlight,
            # so we only return the verse keys + the rendering breakdown).
            if not _bsb_ready(conn):
                conn.close()
                return jsonify({"verses": [], "glosses": []})
            book_id = _KJV_BOOK_ID.get(book)
            if not book_id:
                conn.close()
                return jsonify({"verses": [], "glosses": []})
            occ = conn.execute("""
                SELECT bw.chapter, bw.verse_num AS verse, bw.word
                FROM bsb_strongs bs JOIN bsb_words bw ON bw.word_id = bs.word_id
                WHERE bs.strongs_id = ? AND bw.book_id = ?
                ORDER BY bw.chapter, bw.verse_num, bw.verse_pos
            """, (sid, book_id)).fetchall()
            conn.close()
            gloss_counts, seen, vout = {}, set(), []
            for r in occ:
                norm = _normalize_gloss(r["word"] or "", is_func=is_func)
                if norm:
                    gloss_counts[norm] = gloss_counts.get(norm, 0) + 1
                if gloss and norm != gloss:
                    continue
                key = (r["chapter"], r["verse"])
                if key in seen:
                    continue
                seen.add(key)
                vout.append({"chapter": r["chapter"], "verse": r["verse"]})
            result_glosses = sorted([{"gloss": g, "count": c} for g, c in gloss_counts.items()],
                                    key=lambda x: -x["count"])
            return jsonify({"verses": vout, "glosses": result_glosses})
        if corpus == "kjv":
            book_id = _KJV_BOOK_ID.get(book)
            if not book_id:
                conn.close()
                return jsonify({"verses": [], "glosses": []})
            # Render full verses from positioned tokens; highlight ONLY the words
            # actually tagged with the target strongs (exact, not by gloss match).
            # The matching verses are found ONCE via the IN list below — the old
            # correlated EXISTS re-ran a join for every word in the book (slow on
            # big books); this resolves the verse set a single time, like the ABP
            # branch.
            word_rows = conn.execute("""
                SELECT kw.chapter, kw.verse_num AS verse, kw.verse_pos,
                       kw.word, kw.italic, kw.punc,
                       MAX(CASE WHEN ks.strongs_id = ? THEN 1 ELSE 0 END) AS hl
                FROM kjv_words kw
                LEFT JOIN kjv_strongs ks ON ks.word_id = kw.word_id
                WHERE kw.book_id = ?
                  AND (kw.chapter, kw.verse_num) IN (
                      SELECT kw2.chapter, kw2.verse_num
                      FROM kjv_words kw2
                      JOIN kjv_strongs ks2 ON ks2.word_id = kw2.word_id
                      WHERE kw2.book_id = ?
                        AND ks2.strongs_id = ?
                  )
                GROUP BY kw.word_id
                ORDER BY kw.chapter, kw.verse_num, kw.verse_pos
            """, (sid, book_id, book_id, sid)).fetchall()
        else:
            pred, pparams = _abp_strongs_filter(conn, num, sid)
            word_rows = conn.execute(f"""
                SELECT v.chapter, v.verse, v.text AS prose, w.english AS word, w.italic,
                       CASE WHEN {pred} THEN 1 ELSE 0 END AS hl
                FROM verses v
                JOIN words w ON w.verse_id = v.id
                WHERE v.book = ? AND v.id IN (
                    SELECT w.verse_id FROM words w WHERE {pred}
                )
                ORDER BY v.chapter, v.verse, w.position
            """, (*pparams, book, *pparams)).fetchall()
        verse_prose = {}
        verse_order = []
        gloss_counts = {}
        if corpus == "kjv":
            verses = {}
            for r in word_rows:
                key = (r["chapter"], r["verse"])
                if key not in verses:
                    verses[key] = []
                    verse_order.append(key)
                word = r["word"] or ""
                hl = bool(r["hl"])
                verses[key].append({"w": word, "h": hl,
                                    "i": 1 if r["italic"] else 0,
                                    "punc": r["punc"] or ""})
                if hl and word:
                    norm = _normalize_gloss(word, is_func=is_func)
                    if norm:
                        gloss_counts[norm] = gloss_counts.get(norm, 0) + 1
            if gloss:
                verse_order = [k for k in verse_order
                               if any(e["h"] and _normalize_gloss(e["w"], is_func=is_func) == gloss for e in verses[k])]
            result_verses = [{"chapter": k[0], "verse": k[1], "words": verses[k]} for k in verse_order]
        else:
            verses = {}
            for r in word_rows:
                key = (r["chapter"], r["verse"])
                word = r["word"] or ""
                hl = bool(r["hl"])
                if key not in verses:
                    verses[key] = []
                    verse_prose[key] = r["prose"]
                    verse_order.append(key)
                verses[key].append({"w": word, "h": hl, "i": r["italic"] or 0})
                if hl and word:
                    norm = _normalize_gloss(word, is_func=is_func)
                    if norm:
                        gloss_counts[norm] = gloss_counts.get(norm, 0) + 1
            if gloss:
                verse_order = [k for k in verse_order
                               if any(e["h"] and _normalize_gloss(e["w"], is_func=is_func) == gloss for e in verses[k])]
            result_verses = [{"chapter": k[0], "verse": k[1], "words": verses[k], "text": verse_prose.get(k)} for k in verse_order]
        result_glosses = sorted([{"gloss": g, "count": c} for g, c in gloss_counts.items()], key=lambda x: -x["count"])
        conn.close()
        return jsonify({"verses": result_verses, "glosses": result_glosses})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500
