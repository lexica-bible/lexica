#!/usr/bin/env python3
"""Server-rendered, crawlable reading pages (SEO).

Lexica's main app is a single-page React app — a search engine that loads the
homepage sees an empty shell, and there are no per-passage URLs to rank. These
plain HTML pages fix that: they expose the ACTUAL Bible text at real web
addresses so Google (and a human landing from a search) gets readable content,
each with a clear link into the interactive reader.

PUBLIC-DOMAIN TEXTS ONLY — ABP (Greek LXX + NT interlinear), KJV, BSB, and the
Hebrew OT. ESV and NIV are copyrighted and are NEVER rendered here.

URLs:
  /read/                      index of all 66 books
  /read/<slug>                book page (chapter list)
  /read/<slug>/<ch>           ABP chapter (the primary text)
  /read/<slug>/<ch>/<text>    same chapter as kjv | bsb | heb
  /sitemap.xml                generated sitemap listing every page above

All queries are read-only and reuse the same SQL the JSON API endpoints use, so
these pages can't drift from the app's own data.
"""
import re
import sqlite3
from xml.sax.saxutils import escape

from flask import Blueprint, render_template, abort, redirect, Response

from core import db_ro, heb_db, _KJV_BOOK_ID

bp = Blueprint("seo", __name__)

CANON = "https://www.lexica.bible"

# abbrev -> (display name, url slug), in canonical order. Testament is read from
# _KJV_BOOK_ID (1-39 OT, 40-66 NT). The abbreviations match the ABP `verses.book`
# column and heb_words.book; KJV/BSB map through _KJV_BOOK_ID to their 1-66 ids.
_BOOKS: dict[str, tuple[str, str]] = {
    "Gen": ("Genesis", "genesis"),            "Exo": ("Exodus", "exodus"),
    "Lev": ("Leviticus", "leviticus"),        "Num": ("Numbers", "numbers"),
    "Deu": ("Deuteronomy", "deuteronomy"),    "Jos": ("Joshua", "joshua"),
    "Jdg": ("Judges", "judges"),              "Rth": ("Ruth", "ruth"),
    "1Sa": ("1 Samuel", "1-samuel"),          "2Sa": ("2 Samuel", "2-samuel"),
    "1Ki": ("1 Kings", "1-kings"),            "2Ki": ("2 Kings", "2-kings"),
    "1Ch": ("1 Chronicles", "1-chronicles"),  "2Ch": ("2 Chronicles", "2-chronicles"),
    "Ezr": ("Ezra", "ezra"),                  "Neh": ("Nehemiah", "nehemiah"),
    "Est": ("Esther", "esther"),              "Job": ("Job", "job"),
    "Psa": ("Psalms", "psalms"),              "Pro": ("Proverbs", "proverbs"),
    "Ecc": ("Ecclesiastes", "ecclesiastes"),  "Son": ("Song of Solomon", "song-of-solomon"),
    "Isa": ("Isaiah", "isaiah"),              "Jer": ("Jeremiah", "jeremiah"),
    "Lam": ("Lamentations", "lamentations"),  "Eze": ("Ezekiel", "ezekiel"),
    "Dan": ("Daniel", "daniel"),              "Hos": ("Hosea", "hosea"),
    "Joe": ("Joel", "joel"),                  "Amo": ("Amos", "amos"),
    "Oba": ("Obadiah", "obadiah"),            "Jon": ("Jonah", "jonah"),
    "Mic": ("Micah", "micah"),                "Nah": ("Nahum", "nahum"),
    "Hab": ("Habakkuk", "habakkuk"),          "Zep": ("Zephaniah", "zephaniah"),
    "Hag": ("Haggai", "haggai"),              "Zec": ("Zechariah", "zechariah"),
    "Mal": ("Malachi", "malachi"),            "Mat": ("Matthew", "matthew"),
    "Mar": ("Mark", "mark"),                  "Luk": ("Luke", "luke"),
    "Joh": ("John", "john"),                  "Act": ("Acts", "acts"),
    "Rom": ("Romans", "romans"),              "1Co": ("1 Corinthians", "1-corinthians"),
    "2Co": ("2 Corinthians", "2-corinthians"),"Gal": ("Galatians", "galatians"),
    "Eph": ("Ephesians", "ephesians"),        "Php": ("Philippians", "philippians"),
    "Col": ("Colossians", "colossians"),      "1Th": ("1 Thessalonians", "1-thessalonians"),
    "2Th": ("2 Thessalonians", "2-thessalonians"), "1Ti": ("1 Timothy", "1-timothy"),
    "2Ti": ("2 Timothy", "2-timothy"),        "Tit": ("Titus", "titus"),
    "Phm": ("Philemon", "philemon"),          "Heb": ("Hebrews", "hebrews"),
    "Jas": ("James", "james"),                "1Pe": ("1 Peter", "1-peter"),
    "2Pe": ("2 Peter", "2-peter"),            "1Jn": ("1 John", "1-john"),
    "2Jn": ("2 John", "2-john"),              "3Jn": ("3 John", "3-john"),
    "Jud": ("Jude", "jude"),                  "Rev": ("Revelation", "revelation"),
}
_SLUG = {slug: abbrev for abbrev, (_n, slug) in _BOOKS.items()}


def _is_ot(abbrev: str) -> bool:
    return _KJV_BOOK_ID.get(abbrev, 99) <= 39


def _parts(label: str, italic_words: str = "", smcap_words: str = "", whole_italic: bool = False):
    """Split a gloss into display tokens, flagging which are italic (translator
    additions) or small-caps. Mirrors the app's englishParts: `italic_words` /
    `smcap_words` mark which sub-words inside the gloss get styled."""
    if not label:
        return []
    iset = {x for x in (italic_words or "").split(",") if x}
    sset = {x for x in (smcap_words or "").split(",") if x}
    out = []
    for tok in label.split(" "):
        bare = re.sub(r"[^\w]", "", tok).lower()
        out.append({"t": tok, "it": whole_italic or (bare in iset), "sc": bare in sset})
    return out


def _word(parts, lemma="", translit="", strongs=""):
    """One interlinear chip. num/brk_* default off (set only on ABP bracket groups)."""
    return {"parts": parts, "lemma": lemma, "translit": translit, "strongs": strongs,
            "num": None, "brk_open": False, "brk_close": False, "brk_trail": ""}


_TRAIL = re.compile(r"[.,;:!?·]+$")


def _mark_brackets(words):
    """Port of the reader's groupForGreekMode + bracketChip: consecutive words
    sharing a bracket id are a group — draw '[' before the first, ']' after the
    last, show each word's greek position number (suppressing a repeat), and lift
    the group's trailing clause punctuation outside the ']'. Words carry a
    temporary `_bid` (bracket id) and `_gp` (greek position)."""
    i, n = 0, len(words)
    while i < n:
        bid = words[i]["_bid"]
        if bid is None:
            i += 1
            continue
        j = i
        while j < n and words[j]["_bid"] == bid:
            j += 1
        group = words[i:j]
        last_gp = None
        for w in group:
            gp = w["_gp"]
            if gp is not None and gp == last_gp:
                w["num"] = None
            else:
                w["num"] = gp
                if gp is not None:
                    last_gp = gp
        for k, w in enumerate(group):
            w["brk_open"] = (k == 0)
            w["brk_close"] = (k == len(group) - 1)
        last = group[-1]
        if last["parts"]:
            tail = last["parts"][-1]["t"]
            m = _TRAIL.search(tail)
            if m:
                last["brk_trail"] = m.group(0)
                trimmed = tail[:m.start()]
                if trimmed:
                    last["parts"][-1]["t"] = trimmed
                else:
                    last["parts"] = last["parts"][:-1]
        i = j
    return words


# ── per-text fetchers ────────────────────────────────────────────────────────
# Each returns a uniform list: [{verse, heading, prose, words:[{en,lemma,
# translit,strongs,italic}]}], in reading order. `prose` is a clean readable
# line (for the meta description); `words` feeds the interlinear render.

def _fetch_abp(abbrev: str, chapter: int) -> list[dict]:
    conn = db_ro()
    try:
        rows = conn.execute(
            """SELECT v.verse, v.text AS prose, w.english, w.english_head, w.strongs_base,
                      l.lemma, l.translit, w.italic, w.bracket_id, w.greek_pos,
                      COALESCE(w.italic_words, '') AS italic_words,
                      COALESCE(w.smcap_words,  '') AS smcap_words,
                      p.heading
               FROM verses v
               JOIN words w ON w.verse_id = v.id
               LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base
               LEFT JOIN pericopes p ON p.book = v.book AND p.chapter = v.chapter AND p.verse = v.verse
               WHERE v.book = ? AND v.chapter = ?
               ORDER BY v.verse, w.position""",
            (abbrev, chapter),
        ).fetchall()
    finally:
        conn.close()
    out: dict[int, dict] = {}
    order: list[int] = []
    for r in rows:
        vn = r["verse"]
        if vn not in out:
            out[vn] = {"verse": vn, "heading": r["heading"], "prose": r["prose"] or "", "words": []}
            order.append(vn)
        wd = _word(
            _parts(r["english"] or r["english_head"] or "",
                   r["italic_words"], r["smcap_words"], bool(r["italic"])),
            r["lemma"] or "", r["translit"] or "", r["strongs_base"] or "")
        wd["_bid"] = r["bracket_id"]
        wd["_gp"] = r["greek_pos"]
        out[vn]["words"].append(wd)
    # Drop empty-gloss words (e.g. the merged article) BEFORE grouping — matches the
    # reader, which filters then groups — then apply the bracket/number marks.
    for v in order:
        out[v]["words"] = _mark_brackets([w for w in out[v]["words"] if w["parts"]])
    return [out[v] for v in order]


def _fetch_kjvlike(table_words: str, table_strongs: str, table_verses: str,
                   abbrev: str, chapter: int) -> list[dict]:
    """Shared KJV/BSB fetch — identical schema, different table names."""
    book_id = _KJV_BOOK_ID.get(abbrev)
    if book_id is None:
        return []
    conn = db_ro()
    try:
        try:
            rows = conn.execute(
                f"""SELECT kw.verse_num, kw.verse_pos, kw.word, kw.italic, kw.punc,
                           GROUP_CONCAT(ks.strongs_id) AS strongs_ids,
                           kv.verse_text,
                           MAX(COALESCE(bdb.lemma, lex.lemma))   AS lemma,
                           MAX(COALESCE(bdb.xlit,  lex.translit)) AS xlit
                    FROM {table_words} kw
                    LEFT JOIN {table_strongs} ks ON ks.word_id = kw.word_id
                    LEFT JOIN {table_verses} kv ON kv.book_id = kw.book_id
                        AND kv.chapter = kw.chapter AND kv.verse_num = kw.verse_num
                    LEFT JOIN bdb ON bdb.strongs_id = ks.strongs_id AND ks.strongs_id LIKE 'H%'
                    LEFT JOIN lexicon lex ON lex.strongs_g = ks.strongs_id
                    WHERE kw.book_id = ? AND kw.chapter = ?
                    GROUP BY kw.word_id, kw.verse_num, kw.verse_pos, kw.word, kw.italic, kw.punc, kv.verse_text
                    ORDER BY kw.verse_num, kw.verse_pos""",
                (book_id, chapter),
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []
        verse_rows = []
        if not rows:
            try:
                verse_rows = conn.execute(
                    f"SELECT verse_num, verse_text FROM {table_verses} "
                    "WHERE book_id = ? AND chapter = ? ORDER BY verse_num",
                    (book_id, chapter),
                ).fetchall()
            except sqlite3.OperationalError:
                return []
        pericopes = {r["verse"]: r["heading"] for r in conn.execute(
            "SELECT verse, heading FROM pericopes WHERE book = ? AND chapter = ?", (abbrev, chapter))}
    finally:
        conn.close()
    if not rows:
        return [{"verse": r["verse_num"], "heading": pericopes.get(r["verse_num"]),
                 "prose": r["verse_text"] or "", "words": []} for r in verse_rows]
    out: dict[int, dict] = {}
    order: list[int] = []
    for r in rows:
        vn = r["verse_num"]
        if vn not in out:
            out[vn] = {"verse": vn, "heading": pericopes.get(vn), "prose": r["verse_text"] or "", "words": []}
            order.append(vn)
        sids = [s.strip() for s in (r["strongs_ids"] or "").split(",") if s.strip()]
        out[vn]["words"].append(_word(
            _parts(r["word"] or "", whole_italic=bool(r["italic"])),
            r["lemma"] or "", r["xlit"] or "", sids[0] if sids else ""))
    return [out[v] for v in order]


def _fetch_kjv(abbrev, chapter):
    return _fetch_kjvlike("kjv_words", "kjv_strongs", "kjv_verses", abbrev, chapter)


def _fetch_bsb(abbrev, chapter):
    return _fetch_kjvlike("bsb_words", "bsb_strongs", "bsb_verses", abbrev, chapter)


def _fetch_heb(abbrev, chapter):
    if not _is_ot(abbrev):
        return []
    try:
        conn = heb_db()
    except sqlite3.OperationalError:
        return []
    try:
        try:
            rows = conn.execute(
                "SELECT verse, hebrew, strongs, gloss, translit"
                " FROM heb_words WHERE book = ? AND chapter = ? ORDER BY verse, position",
                (abbrev, chapter),
            ).fetchall()
        except sqlite3.OperationalError:
            rows = conn.execute(
                "SELECT verse, hebrew, strongs, gloss"
                " FROM heb_words WHERE book = ? AND chapter = ? ORDER BY verse, position",
                (abbrev, chapter),
            ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()
    headings = {}
    try:
        bconn = db_ro()
        try:
            for r in bconn.execute(
                "SELECT verse, heading FROM pericopes WHERE book = ? AND chapter = ?", (abbrev, chapter)):
                headings[r["verse"]] = r["heading"]
        finally:
            bconn.close()
    except sqlite3.OperationalError:
        pass
    out: dict[int, dict] = {}
    order: list[int] = []
    for r in rows:
        vn = r["verse"]
        if vn not in out:
            out[vn] = {"verse": vn, "heading": headings.get(vn), "prose": "", "words": []}
            order.append(vn)
        out[vn]["words"].append(_word(
            _parts(r["gloss"] or ""),
            r["hebrew"] or "",
            (r["translit"] if "translit" in r.keys() else "") or "",
            r["strongs"] or ""))
    for v in order:
        out[v]["prose"] = " ".join(p["t"] for w in out[v]["words"] for p in w["parts"])
    return [out[v] for v in order]


_TEXTS = {
    "abp": {"label": "ABP Greek Interlinear", "short": "ABP", "fetch": _fetch_abp, "ot_only": False},
    "kjv": {"label": "King James Version",    "short": "KJV", "fetch": _fetch_kjv, "ot_only": False},
    "bsb": {"label": "Berean Standard Bible", "short": "BSB", "fetch": _fetch_bsb, "ot_only": False},
    "heb": {"label": "Hebrew Interlinear",    "short": "HEB", "fetch": _fetch_heb, "ot_only": True},
}

# Lazily-cached facts (one DB pass each, then reused): per-book ABP chapter count
# and whether the optional BSB/Hebrew data is loaded (so the sitemap + nav don't
# advertise pages that 404).
_MAXCH: dict[str, int] = {}
_AVAIL: dict[str, bool] = {}


def _max_chapters(abbrev: str) -> int:
    if abbrev not in _MAXCH:
        conn = db_ro()
        try:
            row = conn.execute("SELECT MAX(chapter) AS m FROM verses WHERE book = ?", (abbrev,)).fetchone()
        finally:
            conn.close()
        _MAXCH[abbrev] = int(row["m"]) if row and row["m"] else 0
    return _MAXCH[abbrev]


def _text_available(text: str) -> bool:
    """abp/kjv are always in bible.db; bsb/heb are optional loads."""
    if text in ("abp", "kjv"):
        return True
    if text not in _AVAIL:
        ok = False
        try:
            if text == "bsb":
                conn = db_ro()
                try:
                    ok = conn.execute("SELECT 1 FROM bsb_verses LIMIT 1").fetchone() is not None
                finally:
                    conn.close()
            elif text == "heb":
                conn = heb_db()
                try:
                    ok = conn.execute("SELECT 1 FROM heb_words LIMIT 1").fetchone() is not None
                finally:
                    conn.close()
        except sqlite3.OperationalError:
            ok = False
        _AVAIL[text] = ok
    return _AVAIL[text]


def _reader_link(abbrev: str, chapter: int, text: str) -> str:
    """Deep link into the interactive app. (The app honours these params once the
    Phase-1b reader lands; until then it opens at the saved/default spot.)"""
    return f"/?b={abbrev}&c={chapter}&t={text}"


def _desc(name: str, chapter: int, label: str, verses: list[dict]) -> str:
    lead = " ".join(v["prose"] for v in verses[:2]).strip()
    if len(lead) > 150:
        lead = lead[:147].rsplit(" ", 1)[0] + "…"
    base = f"{name} chapter {chapter} — {label} with Strong's numbers on Lexica."
    return (base + " " + lead).strip() if lead else base


# ── routes ───────────────────────────────────────────────────────────────────
@bp.route("/read/")
def read_index():
    ot = [(slug, name) for ab, (name, slug) in _BOOKS.items() if _is_ot(ab)]
    nt = [(slug, name) for ab, (name, slug) in _BOOKS.items() if not _is_ot(ab)]
    return render_template("seo/index.html", ot=ot, nt=nt, canonical=f"{CANON}/read/")


@bp.route("/read/<slug>")
def read_book(slug):
    abbrev = _SLUG.get(slug)
    if not abbrev:
        abort(404)
    n = _max_chapters(abbrev)
    if not n:
        abort(404)
    name = _BOOKS[abbrev][0]
    texts = [(k, _TEXTS[k]["short"]) for k in ("abp", "kjv", "bsb", "heb")
             if _text_available(k) and not (_TEXTS[k]["ot_only"] and not _is_ot(abbrev))]
    return render_template("seo/book.html", slug=slug, name=name,
                           chapters=list(range(1, n + 1)), texts=texts,
                           testament="Old Testament" if _is_ot(abbrev) else "New Testament",
                           canonical=f"{CANON}/read/{slug}")


def _render_chapter(slug: str, chapter: int, text: str):
    abbrev = _SLUG.get(slug)
    if not abbrev or text not in _TEXTS:
        abort(404)
    if _TEXTS[text]["ot_only"] and not _is_ot(abbrev):
        abort(404)
    verses = _TEXTS[text]["fetch"](abbrev, chapter)
    if not verses:
        abort(404)
    name = _BOOKS[abbrev][0]
    label = _TEXTS[text]["label"]
    maxch = _max_chapters(abbrev)
    path = f"/read/{slug}/{chapter}" + ("" if text == "abp" else f"/{text}")
    # sibling texts for the same chapter (only the ones that apply + are loaded)
    others = []
    for k in ("abp", "kjv", "bsb", "heb"):
        if _TEXTS[k]["ot_only"] and not _is_ot(abbrev):
            continue
        if not _text_available(k):
            continue
        kpath = f"/read/{slug}/{chapter}" + ("" if k == "abp" else f"/{k}")
        others.append({"key": k, "short": _TEXTS[k]["short"], "url": kpath, "active": k == text})
    suffix = "" if text == "abp" else f"/{text}"
    return render_template(
        "seo/chapter.html",
        name=name, chapter=chapter, label=label, text=text, slug=slug,
        verses=verses, others=others,
        prev_url=(f"/read/{slug}/{chapter - 1}{suffix}" if chapter > 1 else None),
        next_url=(f"/read/{slug}/{chapter + 1}{suffix}" if chapter < maxch else None),
        book_url=f"/read/{slug}",
        reader_url=_reader_link(abbrev, chapter, text),
        title=f"{name} {chapter} — {label} | Lexica",
        description=_desc(name, chapter, label, verses),
        canonical=f"{CANON}{path}",
    )


@bp.route("/read/<slug>/<int:chapter>")
def read_chapter_abp(slug, chapter):
    return _render_chapter(slug, chapter, "abp")


@bp.route("/read/<slug>/<int:chapter>/<text>")
def read_chapter_text(slug, chapter, text):
    if text == "abp":  # keep the bare URL canonical
        return redirect(f"/read/{slug}/{chapter}", code=301)
    return _render_chapter(slug, chapter, text)


@bp.route("/sitemap.xml")
def sitemap():
    urls = [f"{CANON}/", f"{CANON}/read/"]
    extra = [t for t in ("kjv", "bsb", "heb") if _text_available(t)]
    for abbrev, (_n, slug) in _BOOKS.items():
        n = _max_chapters(abbrev)
        if not n:
            continue
        urls.append(f"{CANON}/read/{slug}")
        for c in range(1, n + 1):
            urls.append(f"{CANON}/read/{slug}/{c}")
            for t in extra:
                if t == "heb" and not _is_ot(abbrev):
                    continue
                urls.append(f"{CANON}/read/{slug}/{c}/{t}")
    body = "\n".join(f"  <url><loc>{escape(u)}</loc></url>" for u in urls)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           f"{body}\n</urlset>\n")
    return Response(xml, mimetype="application/xml")
