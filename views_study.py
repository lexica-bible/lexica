#!/usr/bin/env python3
"""Study modules — admin-authored study content (the "engine").

Two kinds of entry, one row each: a study TOPIC (a subject broken into subtopic SECTIONS
of verses) and an argument GRAPH (a pool of CLAIMS joined by per-tradition LINKS, each
tagged with provenance + strength so the conclusion can be stress-tested — see argmap.py).
Build the entry once here; the reader views render it.

Storage: study.db (core.study_db), kept OUT of bible.db (the corpus is rebuilt;
authored content must survive that) and OUT of git (*.db is gitignored), exactly
like notes.db. One row per entry.

Gating: WRITING is always admin-only (the owner authors content). READING is split
(go-live 2026-06-16): published TOPICS — including the metaV name-topics — are PUBLIC,
readable by anyone with no login. Argument graphs stay admin-only (they take
positions, unlike the rest of the Berean app), as do all DRAFTS and the editor's
verse-autofill. Non-admins get a 404 for anything they may not see, and private notes
are never sent to a reader.

Verses are stored as plain REFERENCES only ("Romans 10:17"); the ABP PROSE text is
resolved live from bible.db on read and for the editor's auto-fill (KJV fallback
when ABP lacks the verse), so a long verse list costs a few keystrokes and the text
never drifts from the corpus.

Endpoints (all admin-only):
  GET  /api/study/entries?type=        -> {entries:[{id,type,title,n,status,updated}]}
  GET  /api/study/entry/<id>           -> full entry (verses resolved to text)
  POST /api/study/entry                -> create/update (mints id if absent) -> {id}
  POST /api/study/entry/<id>/delete    -> soft delete -> {ok}
  GET  /api/study/verse?ref=Rom+10:17  -> {ref, verses:[{ref,text}]}  (auto-fill)
"""
import json
import logging
import re
import secrets
import time
from collections import defaultdict

from flask import Blueprint, jsonify, request

import argmap
from core import study_db, db_ro, limiter, _anthropic, _KJV_BOOK_ID, _KJV_BOOK_ID_REV
from views_notes import is_admin

bp = Blueprint("study", __name__)
log = logging.getLogger("study")

_TYPES = ("topic", "graph", "name")   # "name" = a metaV person/place name-topic (sectioned like a topic; not shown in the browser list)
_MAX_ENTRY_BYTES = 200_000     # one whole entry's JSON (long notes + many refs)
_MAX_VERSES = 300              # verse refs per topic section
_MAX_RANGE = 60                # verses a single reference range may expand to


def _ensure_tables():
    conn = study_db()
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS entries ("
            " id TEXT PRIMARY KEY, type TEXT NOT NULL, title TEXT NOT NULL,"
            " json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft',"
            " created TEXT NOT NULL, updated TEXT NOT NULL,"
            " deleted INTEGER NOT NULL DEFAULT 0)"
        )
        conn.commit()
    finally:
        conn.close()


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _slug(s):
    """Match the loader's slugify so a person/place name maps to its name-topic id
    ('metavn_' + slug). Keep in sync with scripts/load_study_topics.slugify."""
    s = re.sub(r"[^a-z0-9]+", "_", (s or "").strip().lower()).strip("_")
    return s or "topic"


# ── Reference parsing ────────────────────────────────────────────────────────
# Map every reasonable spelling of a book to the app's 3-char abbreviation (the
# keys of core._KJV_BOOK_ID), plus a clean display name. The leading-number books
# (1/2/3 Samuel…) carry their digit and roman/word forms as aliases.
_BOOKS = [
    ("Gen", "Genesis", ["genesis", "gen", "ge", "gn"]),
    ("Exo", "Exodus", ["exodus", "exo", "exod", "ex"]),
    ("Lev", "Leviticus", ["leviticus", "lev", "lv"]),
    ("Num", "Numbers", ["numbers", "num", "nm", "nu"]),
    ("Deu", "Deuteronomy", ["deuteronomy", "deut", "deu", "dt"]),
    ("Jos", "Joshua", ["joshua", "josh", "jos", "jsh"]),
    ("Jdg", "Judges", ["judges", "judg", "jdg", "jg"]),
    ("Rth", "Ruth", ["ruth", "rth", "ru"]),
    ("1Sa", "1 Samuel", ["1 samuel", "1samuel", "1 sam", "1sam", "1sa", "i samuel", "first samuel"]),
    ("2Sa", "2 Samuel", ["2 samuel", "2samuel", "2 sam", "2sam", "2sa", "ii samuel", "second samuel"]),
    ("1Ki", "1 Kings", ["1 kings", "1kings", "1 kgs", "1kgs", "1ki", "i kings", "first kings"]),
    ("2Ki", "2 Kings", ["2 kings", "2kings", "2 kgs", "2kgs", "2ki", "ii kings", "second kings"]),
    ("1Ch", "1 Chronicles", ["1 chronicles", "1chronicles", "1 chron", "1chron", "1 chr", "1chr", "1ch", "i chronicles"]),
    ("2Ch", "2 Chronicles", ["2 chronicles", "2chronicles", "2 chron", "2chron", "2 chr", "2chr", "2ch", "ii chronicles"]),
    ("Ezr", "Ezra", ["ezra", "ezr"]),
    ("Neh", "Nehemiah", ["nehemiah", "neh", "ne"]),
    ("Est", "Esther", ["esther", "esth", "est"]),
    ("Job", "Job", ["job", "jb"]),
    ("Psa", "Psalms", ["psalms", "psalm", "psa", "ps", "pss"]),
    ("Pro", "Proverbs", ["proverbs", "prov", "pro", "prv", "pr"]),
    ("Ecc", "Ecclesiastes", ["ecclesiastes", "eccl", "ecc", "ec", "qoh"]),
    ("Son", "Song of Solomon", ["song of solomon", "song of songs", "song", "songs", "sos", "son", "canticles", "cant"]),
    ("Isa", "Isaiah", ["isaiah", "isa", "is"]),
    ("Jer", "Jeremiah", ["jeremiah", "jer", "je"]),
    ("Lam", "Lamentations", ["lamentations", "lam", "la"]),
    ("Eze", "Ezekiel", ["ezekiel", "ezek", "eze", "ezk"]),
    ("Dan", "Daniel", ["daniel", "dan", "dn"]),
    ("Hos", "Hosea", ["hosea", "hos", "ho"]),
    ("Joe", "Joel", ["joel", "joe", "jl"]),
    ("Amo", "Amos", ["amos", "amo", "am"]),
    ("Oba", "Obadiah", ["obadiah", "obad", "oba", "ob"]),
    ("Jon", "Jonah", ["jonah", "jon", "jnh"]),
    ("Mic", "Micah", ["micah", "mic", "mc"]),
    ("Nah", "Nahum", ["nahum", "nah", "na"]),
    ("Hab", "Habakkuk", ["habakkuk", "hab", "hb"]),
    ("Zep", "Zephaniah", ["zephaniah", "zeph", "zep", "zp"]),
    ("Hag", "Haggai", ["haggai", "hag", "hg"]),
    ("Zec", "Zechariah", ["zechariah", "zech", "zec", "zc"]),
    ("Mal", "Malachi", ["malachi", "mal", "ml"]),
    ("Mat", "Matthew", ["matthew", "matt", "mat", "mt"]),
    ("Mar", "Mark", ["mark", "mar", "mrk", "mk"]),
    ("Luk", "Luke", ["luke", "luk", "lk"]),
    ("Joh", "John", ["john", "joh", "jhn", "jn"]),
    ("Act", "Acts", ["acts", "act", "ac"]),
    ("Rom", "Romans", ["romans", "rom", "ro", "rm"]),
    ("1Co", "1 Corinthians", ["1 corinthians", "1corinthians", "1 cor", "1cor", "1co", "i corinthians", "first corinthians"]),
    ("2Co", "2 Corinthians", ["2 corinthians", "2corinthians", "2 cor", "2cor", "2co", "ii corinthians", "second corinthians"]),
    ("Gal", "Galatians", ["galatians", "gal", "ga"]),
    ("Eph", "Ephesians", ["ephesians", "eph", "ephes"]),
    ("Php", "Philippians", ["philippians", "phil", "php", "philip", "pp"]),
    ("Col", "Colossians", ["colossians", "col", "cl"]),
    ("1Th", "1 Thessalonians", ["1 thessalonians", "1thessalonians", "1 thess", "1thess", "1 th", "1th", "i thessalonians"]),
    ("2Th", "2 Thessalonians", ["2 thessalonians", "2thessalonians", "2 thess", "2thess", "2 th", "2th", "ii thessalonians"]),
    ("1Ti", "1 Timothy", ["1 timothy", "1timothy", "1 tim", "1tim", "1ti", "i timothy", "first timothy"]),
    ("2Ti", "2 Timothy", ["2 timothy", "2timothy", "2 tim", "2tim", "2ti", "ii timothy", "second timothy"]),
    ("Tit", "Titus", ["titus", "tit", "ti"]),
    ("Phm", "Philemon", ["philemon", "philem", "phm", "phlm", "pm"]),
    ("Heb", "Hebrews", ["hebrews", "heb", "hbr"]),
    ("Jas", "James", ["james", "jas", "jam", "jm"]),
    ("1Pe", "1 Peter", ["1 peter", "1peter", "1 pet", "1pet", "1pe", "i peter", "first peter"]),
    ("2Pe", "2 Peter", ["2 peter", "2peter", "2 pet", "2pet", "2pe", "ii peter", "second peter"]),
    ("1Jn", "1 John", ["1 john", "1john", "1 jn", "1jn", "1jo", "i john", "first john"]),
    ("2Jn", "2 John", ["2 john", "2john", "2 jn", "2jn", "2jo", "ii john", "second john"]),
    ("3Jn", "3 John", ["3 john", "3john", "3 jn", "3jn", "3jo", "iii john", "third john"]),
    ("Jud", "Jude", ["jude", "jud", "jd"]),
    ("Rev", "Revelation", ["revelation", "revelations", "rev", "rv", "apocalypse"]),
]
_BOOK_DISPLAY = {abbr: disp for abbr, disp, _ in _BOOKS}


def _norm_book(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace(".", " ")).strip().lower()


# alias (spaced + de-spaced) -> abbrev
_BOOK_LOOKUP: dict[str, str] = {}
for _abbr, _disp, _aliases in _BOOKS:
    for _a in _aliases:
        n = _norm_book(_a)
        _BOOK_LOOKUP.setdefault(n, _abbr)
        _BOOK_LOOKUP.setdefault(n.replace(" ", ""), _abbr)

_REF_RE = re.compile(
    r"^\s*([1-3]?\s*[A-Za-z][A-Za-z. ]*?)\s*"   # book (optional leading 1-3)
    r"(\d+):(\d+)"                                # chapter:verse
    r"(?:\s*[-–—]\s*(\d+)(?::(\d+))?)?" # optional -end  or  -endCh:endVerse
    r"\s*$"
)


def _parse_ref(ref: str):
    """'Romans 10:17' / 'Eph 2:8-9' / 'John 3:16-4:2' -> (book_id, start_ch,
    start_v, end_ch, end_v) or None. A bare end number is an end-VERSE in the same
    chapter; 'end:v' is a cross-chapter end."""
    if not ref or not isinstance(ref, str):
        return None
    m = _REF_RE.match(ref.strip())
    if not m:
        return None
    book_raw, ch, v, e1, e2 = m.groups()
    abbr = _BOOK_LOOKUP.get(_norm_book(book_raw)) or _BOOK_LOOKUP.get(_norm_book(book_raw).replace(" ", ""))
    if not abbr:
        return None
    book_id = _KJV_BOOK_ID.get(abbr)
    if book_id is None:
        return None
    start_ch, start_v = int(ch), int(v)
    if e1 is None:                       # single verse
        end_ch, end_v = start_ch, start_v
    elif e2 is None:                     # same-chapter range (8-9)
        end_ch, end_v = start_ch, int(e1)
    else:                                # cross-chapter range (3:16-4:2)
        end_ch, end_v = int(e1), int(e2)
    return book_id, start_ch, start_v, end_ch, end_v


def _canonical_ref(ref):
    """'gen 1:1' -> 'Genesis 1:1' — full book name, range preserved. Falls back to the
    text as given if it can't be parsed, so the editor stores a tidy reference."""
    parsed = _parse_ref(ref)
    if not parsed:
        return ref
    book_id, sc, sv, ec, ev = parsed
    disp = _BOOK_DISPLAY.get(_KJV_BOOK_ID_REV.get(book_id, ""), "")
    if not disp:
        return ref
    if sc == ec and sv == ev:
        return "%s %d:%d" % (disp, sc, sv)
    if sc == ec:
        return "%s %d:%d-%d" % (disp, sc, sv, ev)
    return "%s %d:%d-%d:%d" % (disp, sc, sv, ec, ev)


def _join_prose(tokens):
    """Join word glosses into prose, attaching trailing punctuation with no space —
    the same rule the reader's ABP Prose mode uses (joinProse in 60-library.jsx)."""
    out = ""
    for i, tok in enumerate(tokens):
        if i == 0:
            out = tok
        elif re.match(r"^[.,;:?!—)]", tok):
            out += tok
        else:
            out += " " + tok
    return out


def _abp_prose(conn, abbr, chapter, verse):
    """ABP prose English for one verse — its words' english joined in order, the same
    text the reader's Prose mode shows. None if ABP has no matching verse (e.g. the
    versification differs from the KJV reference), so the caller can fall back."""
    row = conn.execute(
        "SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
        (abbr, chapter, verse),
    ).fetchone()
    if not row:
        return None
    ws = conn.execute(
        "SELECT english FROM words WHERE verse_id=? AND english IS NOT NULL ORDER BY position",
        (row["id"],),
    ).fetchall()
    toks = [w["english"] for w in ws if w["english"]]
    return _join_prose(toks) if toks else None


def _resolve_ref(ref, conn=None):
    """Resolve a reference to a list of {ref, text}. Text is the ABP PROSE English
    (the app's primary text, in its readable running-prose form); when ABP has no
    matching verse we fall back to the KJV verse text so the editor still shows
    something. KJV's canonical verse order is used only to enumerate a range.

    Pass a shared `conn` to reuse one db handle across many refs (a whole topic);
    without one it opens and closes its own."""
    parsed = _parse_ref(ref)
    if not parsed:
        return []
    book_id, sc, sv, ec, ev = parsed
    own = conn is None
    if own:
        conn = db_ro()
    try:
        start = conn.execute(
            "SELECT verse_id FROM kjv_verses WHERE book_id=? AND chapter=? AND verse_num=?",
            (book_id, sc, sv),
        ).fetchone()
        end = conn.execute(
            "SELECT verse_id FROM kjv_verses WHERE book_id=? AND chapter=? AND verse_num=?",
            (book_id, ec, ev),
        ).fetchone()
        if not start:
            return []
        start_id = start["verse_id"]
        end_id = end["verse_id"] if end else start_id
        if end_id < start_id:
            end_id = start_id
        if end_id - start_id + 1 > _MAX_RANGE:
            end_id = start_id + _MAX_RANGE - 1
        rows = conn.execute(
            "SELECT book_id, chapter, verse_num, verse_text FROM kjv_verses"
            " WHERE verse_id BETWEEN ? AND ? ORDER BY verse_id",
            (start_id, end_id),
        ).fetchall()
        out = []
        for r in rows:
            abbr = _KJV_BOOK_ID_REV.get(r["book_id"], "")
            disp = _BOOK_DISPLAY.get(abbr, "")
            abp = _abp_prose(conn, abbr, r["chapter"], r["verse_num"])
            out.append({
                "ref": f"{disp} {r['chapter']}:{r['verse_num']}".strip(),
                "text": abp or r["verse_text"],
            })
    except Exception:
        return []
    finally:
        if own:
            conn.close()
    return out


# ── Entry shape helpers ──────────────────────────────────────────────────────
def _clean_refs(items):
    """Keep a list of reference strings, trimmed, capped, de-duped (order kept)."""
    out, seen = [], set()
    if not isinstance(items, list):
        return out
    for it in items:
        ref = (it.get("ref") if isinstance(it, dict) else it) or ""
        ref = str(ref).strip()
        if ref and ref not in seen:
            seen.add(ref)
            out.append(ref)
            if len(out) >= _MAX_VERSES:
                break
    return out


_MAX_SECTIONS = 120


def _clean_sections(items):
    """Topic subtopic sections: [{heading, verses:[ref,...]}], trimmed and capped."""
    out = []
    if not isinstance(items, list):
        return out
    for s in items:
        if not isinstance(s, dict):
            continue
        heading = str(s.get("heading") or "").strip()[:300]
        verses = _clean_refs(s.get("verses"))
        if heading or verses:
            out.append({"heading": heading, "verses": verses})
            if len(out) >= _MAX_SECTIONS:
                break
    return out


_MAX_CLAIMS = 200
_MAX_OVERLAYS = 8
_MAX_LINKS = 400


def _clean_claims(obj):
    """Graph claim pool: {id: {text, provenance, ref?}}, trimmed + capped. An unknown
    provenance is parked at 'conjecture' (clearly not grounded) so the stress test stays honest."""
    out = {}
    if not isinstance(obj, dict):
        return out
    for cid, c in obj.items():
        cid = str(cid).strip()
        if not cid or not isinstance(c, dict):
            continue
        prov = str(c.get("provenance") or "").strip().lower()
        if prov not in argmap.PROVENANCE:
            prov = "conjecture"
        item = {"text": str(c.get("text") or "").strip()[:600], "provenance": prov}
        ref = str(c.get("ref") or "").strip()
        if ref:
            item["ref"] = ref[:80]
        out[cid] = item
        if len(out) >= _MAX_CLAIMS:
            break
    return out


def _clean_overlays(obj, claim_ids):
    """Per-tradition overlays: [{tradition, thesis, links:[{from,to,relation,strength,note?}]}].
    Links pointing at a claim that isn't in the pool are dropped; an unknown relation/strength
    snaps to a safe default."""
    out = []
    if not isinstance(obj, list):
        return out
    for ov in obj:
        if not isinstance(ov, dict):
            continue
        links = []
        for l in (ov.get("links") or []):
            if not isinstance(l, dict):
                continue
            f, t = str(l.get("from") or "").strip(), str(l.get("to") or "").strip()
            if f not in claim_ids or t not in claim_ids:
                continue
            rel = str(l.get("relation") or "").strip().lower()
            strg = str(l.get("strength") or "").strip().lower()
            link = {
                "from": f, "to": t,
                "relation": rel if rel in argmap.RELATIONS else "supports",
                "strength": strg if strg in argmap.STRENGTHS else "contested",
            }
            note = str(l.get("note") or "").strip()
            if note:
                link["note"] = note[:300]
            links.append(link)
            if len(links) >= _MAX_LINKS:
                break
        thesis = str(ov.get("thesis") or "").strip()
        out.append({
            "tradition": str(ov.get("tradition") or "").strip()[:200],
            "thesis": thesis if thesis in claim_ids else "",
            "links": links,
        })
        if len(out) >= _MAX_OVERLAYS:
            break
    return out


def _body_from_request(etype: str, body: dict) -> dict:
    """Normalize the incoming entry into its stored JSON shape (only fields we keep, so a
    client can't smuggle extra keys in). A TOPIC carries subtopic SECTIONS; a GRAPH carries
    the claim pool + per-tradition overlays (see argmap.py)."""
    related = body.get("related") if isinstance(body.get("related"), list) else []
    related = [str(x).strip() for x in related if str(x).strip()][:100]
    if etype in ("topic", "name"):
        return {
            "intro": str(body.get("intro") or "").strip()[:4000],
            "sections": _clean_sections(body.get("sections")),
            "related": related,
            "source": str(body.get("source") or "").strip()[:40],
        }
    # graph
    claims = _clean_claims(body.get("claims"))
    return {
        "intro": str(body.get("intro") or "").strip()[:2000],
        "claims": claims,
        "overlays": _clean_overlays(body.get("overlays"), set(claims.keys())),
        "notes": str(body.get("notes") or "").strip()[:20000],
        "related": related,
    }


def _chunked(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def _verse_ids_for(conn, endpoints):
    """{(book_id, ch, v)} -> {(book_id, ch, v): kjv verse_id}, one query per distinct
    book (indexed on book_id) instead of one lookup per verse."""
    out = {}
    by_book = defaultdict(set)
    for (b, c, v) in endpoints:
        by_book[b].add((c, v))
    for b, cvs in by_book.items():
        rows = conn.execute(
            "SELECT chapter, verse_num, verse_id FROM kjv_verses WHERE book_id=?", (b,)
        ).fetchall()
        m = {(r["chapter"], r["verse_num"]): r["verse_id"] for r in rows}
        for (c, v) in cvs:
            if (c, v) in m:
                out[(b, c, v)] = m[(c, v)]
    return out


def _abp_prose_bulk(conn, wants):
    """{(abbr, ch, v)} -> {(abbr, ch, v): ABP prose}. Batched: one verse-id pass per
    book, then the words in chunked reads — not two reads per verse."""
    if not wants:
        return {}
    by_book = defaultdict(set)
    for (abbr, c, v) in wants:
        by_book[abbr].add((c, v))
    vmap = {}                       # (abbr, ch, v) -> verses.id
    for abbr, cvs in by_book.items():
        rows = conn.execute(
            "SELECT id, chapter, verse FROM verses WHERE book=?", (abbr,)
        ).fetchall()
        m = {(r["chapter"], r["verse"]): r["id"] for r in rows}
        for (c, v) in cvs:
            if (c, v) in m:
                vmap[(abbr, c, v)] = m[(c, v)]
    if not vmap:
        return {}
    id_to_key = {vid: k for k, vid in vmap.items()}
    toks_by_id = defaultdict(list)  # verses.id -> [english, ...] in position order
    for chunk in _chunked(list(id_to_key), 800):
        q = ("SELECT verse_id, english FROM words"
             " WHERE english IS NOT NULL AND verse_id IN (%s)"
             " ORDER BY verse_id, position" % ",".join("?" * len(chunk)))
        for row in conn.execute(q, chunk):
            if row["english"]:
                toks_by_id[row["verse_id"]].append(row["english"])
    out = {}
    for vid, toks in toks_by_id.items():
        key = id_to_key.get(vid)
        if key and toks:
            out[key] = _join_prose(toks)
    return out


def _resolve_map(refs, conn):
    """{ref string: {text, book, chapter, verse}} for MANY references in a handful of
    queries — the same text _resolve_ref gives per ref (ABP prose, KJV fallback), batched
    so a big topic (~1000 verses) opens fast instead of ~5 reads per verse. book/chapter/
    verse are the ref's FIRST verse (the jump target when a reader clicks the reference)."""
    uniq = list(dict.fromkeys(r for r in (refs or []) if r))
    parsed = [(r, _parse_ref(r)) for r in uniq]
    endpoints = set()
    for _, p in parsed:
        if p:
            book_id, sc, sv, ec, ev = p
            endpoints.add((book_id, sc, sv))
            endpoints.add((book_id, ec, ev))
    if not endpoints:
        return {r: {"text": "", "book": "", "chapter": None, "verse": None} for r in uniq}
    vid = _verse_ids_for(conn, endpoints)
    ranges, need_ids, start = {}, set(), {}
    for ref, p in parsed:
        if not p:
            ranges[ref] = None
            start[ref] = ("", None, None)
            continue
        book_id, sc, sv, ec, ev = p
        start[ref] = (_KJV_BOOK_ID_REV.get(book_id, ""), sc, sv)   # jump target = the ref's first verse
        s = vid.get((book_id, sc, sv))
        if s is None:
            ranges[ref] = None
            continue
        e = vid.get((book_id, ec, ev), s)
        if e < s:
            e = s
        if e - s + 1 > _MAX_RANGE:
            e = s + _MAX_RANGE - 1
        ranges[ref] = (s, e)
        need_ids.update(range(s, e + 1))
    kjv = {}                        # verse_id -> (book_id, chapter, verse_num, verse_text)
    for chunk in _chunked(sorted(need_ids), 800):
        q = ("SELECT verse_id, book_id, chapter, verse_num, verse_text FROM kjv_verses"
             " WHERE verse_id IN (%s)" % ",".join("?" * len(chunk)))
        for r in conn.execute(q, chunk):
            kjv[r["verse_id"]] = (r["book_id"], r["chapter"], r["verse_num"], r["verse_text"])
    want_abp = set()
    for vid_ in need_ids:
        meta = kjv.get(vid_)
        if meta:
            abbr = _KJV_BOOK_ID_REV.get(meta[0], "")
            if abbr:
                want_abp.add((abbr, meta[1], meta[2]))
    abp = _abp_prose_bulk(conn, want_abp)
    out = {}
    for ref in uniq:
        b, c, v = start.get(ref, ("", None, None))
        rng = ranges.get(ref)
        if not rng:
            out[ref] = {"text": "", "book": b, "chapter": c, "verse": v}
            continue
        s, e = rng
        parts = []
        for i in range(s, e + 1):
            meta = kjv.get(i)
            if not meta:
                continue
            abbr = _KJV_BOOK_ID_REV.get(meta[0], "")
            t = abp.get((abbr, meta[1], meta[2])) or meta[3]
            if t:
                parts.append(t)
        out[ref] = {"text": " ".join(parts), "book": b, "chapter": c, "verse": v}
    return out


def _verses_payload(refs, tmap):
    """[ref,...] -> [{ref, text, book, chapter, verse}] using the resolved map (book/
    chapter/verse let a reader click the reference and jump into the Library)."""
    out = []
    for r in (refs or []):
        m = tmap.get(r) or {}
        out.append({"ref": r, "text": m.get("text", ""), "book": m.get("book", ""),
                    "chapter": m.get("chapter"), "verse": m.get("verse")})
    return out


def _resolve_body(etype: str, stored: dict) -> dict:
    """Expand stored refs into {ref, text, book, chapter, verse} for the client — inside
    each section for a topic, in the support/tension buckets for a claim. ALL of the
    entry's refs resolve in one batched pass (see _resolve_map), so even a 1000-verse
    topic is fast."""
    b = dict(stored)
    conn = db_ro()
    try:
        if etype in ("topic", "name"):
            secs = stored.get("sections") or []
            tmap = _resolve_map([r for s in secs for r in ((s or {}).get("verses") or [])], conn)
            b["sections"] = [
                {"heading": (s or {}).get("heading", ""), "verses": _verses_payload((s or {}).get("verses"), tmap)}
                for s in secs
            ]
        else:   # graph
            claims = stored.get("claims") or {}
            refs = [(c or {}).get("ref") for c in claims.values() if (c or {}).get("ref")]
            tmap = _resolve_map(refs, conn)
            rclaims = {}
            for cid, c in claims.items():
                c = dict(c or {})
                ref = c.get("ref")
                if ref:
                    m = tmap.get(ref) or {}
                    c["verse_text"] = m.get("text", "")
                    c["book"], c["chapter"], c["verse"] = m.get("book", ""), m.get("chapter"), m.get("verse")
                rclaims[cid] = c
            overlays = stored.get("overlays") or []
            b["claims"] = rclaims
            b["overlays"] = overlays
            b["analysis"] = argmap.analyze(rclaims, overlays)
    finally:
        conn.close()
    return b


# Resolving a topic's verses is the costly part (a big topic cites ~1000 verses), and
# the text never changes under a given entry — so cache each entry's RESOLVED body per
# process, keyed by its `updated` stamp (an edit bumps the stamp → auto-refresh). Bounded
# so it can't grow without limit; cleared whenever the worker reloads.
_RESOLVED_CACHE = {}            # id -> (updated, resolved_body_dict)
_RESOLVED_CACHE_MAX = 80


def _resolved_entry(r):
    """The resolved body (topic sections / graph claims+overlays) for an entries row — from
    the cache when the entry is unchanged, else resolved once and cached. Returns a fresh
    copy so the caller can add id/status/strip notes without touching the cache."""
    hit = _RESOLVED_CACHE.get(r["id"])
    if hit and hit[0] == r["updated"]:
        return dict(hit[1])
    try:
        stored = json.loads(r["json"]) or {}
    except (ValueError, TypeError):
        stored = {}
    body = _resolve_body(r["type"], stored)
    if r["id"] not in _RESOLVED_CACHE and len(_RESOLVED_CACHE) >= _RESOLVED_CACHE_MAX:
        _RESOLVED_CACHE.pop(next(iter(_RESOLVED_CACHE)))   # evict the oldest
    _RESOLVED_CACHE[r["id"]] = (r["updated"], dict(body))
    return dict(body)


# ── Verse -> studies (the reader's "In studies:" line) ───────────────────────
# A reverse lookup so the reader can ask "is this verse in a study?" cheaply. Built from
# the PUBLISHED CONCEPT topics only (type 'topic') — NOT the ~696 person/place name-topics,
# which already surface via the metaV sidebar and would otherwise light up nearly every
# verse. Keyed by the ref's FIRST verse (single-verse citations are the norm). Cached in
# memory and rebuilt only when the published-topic set actually changes (id+updated signature).
_VERSE_INDEX = None             # {(book_abbr, chapter, verse): [(id, title), ...]}
_VERSE_INDEX_SIG = None


def _verse_index():
    global _VERSE_INDEX, _VERSE_INDEX_SIG
    conn = study_db()
    try:
        rows = conn.execute(
            "SELECT id, title, json, updated FROM entries"
            " WHERE type='topic' AND status='published' AND deleted=0"
        ).fetchall()
    finally:
        conn.close()
    sig = tuple((r["id"], r["updated"]) for r in rows)
    if _VERSE_INDEX is not None and sig == _VERSE_INDEX_SIG:
        return _VERSE_INDEX
    idx = {}
    for r in rows:
        try:
            data = json.loads(r["json"]) or {}
        except (ValueError, TypeError):
            data = {}
        # Reader line = HAND-AUTHORED studies only. The Nave's auto-imports stamp
        # themselves source='metav' and cite ~1000 scattered verses each — they'd blanket
        # the text. They stay browsable in the Study tab; they just don't tag the reader.
        if (data.get("source") or "").strip().lower() == "metav":
            continue
        seen = set()                       # one entry per verse, even if cited twice in a topic
        for s in (data.get("sections") or []):
            for ref in ((s or {}).get("verses") or []):
                p = _parse_ref(ref)
                if not p:
                    continue
                book_id, sc, sv, ec, ev = p
                key = (_KJV_BOOK_ID_REV.get(book_id, ""), sc, sv)
                if not key[0] or key in seen:
                    continue
                seen.add(key)
                idx.setdefault(key, []).append((r["id"], r["title"]))
    _VERSE_INDEX, _VERSE_INDEX_SIG = idx, sig
    return idx


# ── AI: draft a topic intro (text-first, Berean) ─────────────────────────────
_INTRO_SYSTEM = (
    "You write a one- or two-sentence lead-in that sits above a set of Bible verses a "
    "reader is about to read on a topic. Berean and strictly text-first: ground it ONLY "
    "in what these gathered verses actually say — add no doctrine they don't state, and "
    "import no theological system or denominational position. If the verses pull in "
    "different directions or leave something open, say so plainly instead of resolving it "
    "for the reader. Describe and invite; do not conclude, moralize, or tell the reader "
    "what to do. Plain words, warm, concise. No markdown, no heading, no quotation marks."
)


def _intro_user_prompt(title, sections):
    """A compact prompt: the topic, its subtopic headings, and a few sample verses
    (capped, so a huge topic stays cheap)."""
    lines = ["Topic: " + (title or "").strip()]
    shown = 0
    for s in sections or []:
        if not isinstance(s, dict):
            continue
        h = (s.get("heading") or "").strip()
        if h:
            lines.append("Subtopic: " + h)
        for v in (s.get("verses") or []):
            if shown >= 14:
                break
            ref = str((v.get("ref") if isinstance(v, dict) else "") or "").strip()
            txt = str((v.get("text") if isinstance(v, dict) else "") or "").strip()
            if ref and txt:
                lines.append("  " + ref + " — " + txt[:200])
                shown += 1
            elif ref:
                lines.append("  " + ref)
        if shown >= 14:
            break
    lines.append("")
    lines.append("Write the 1-2 sentence intro for this topic.")
    return "\n".join(lines)


_INTRO_HAIKU = "claude-haiku-4-5-20251001"
_INTRO_SONNET = "claude-sonnet-4-6"


def _draft_intro(title, sections, model=None):
    """Text-first intro for a topic — Haiku by default, or Sonnet (model=_INTRO_SONNET)
    for the more careful public batch. Returns '' on any failure so the caller decides.
    Shared by the in-app button (Haiku) and the bulk script."""
    if not _anthropic:
        return ""
    try:
        msg = _anthropic.messages.create(
            model=model or _INTRO_HAIKU,
            max_tokens=180,
            temperature=0.5,
            system=_INTRO_SYSTEM,
            messages=[{"role": "user", "content": _intro_user_prompt(title, sections)}],
        )
        out = msg.content[0].text.strip() if msg.content else ""
    except Exception as e:
        log.error("draft intro failed for %r: %s", title, e)
        return ""
    if len(out) >= 2 and out[0] in "\"'“" and out[-1] in "\"'”":
        out = out[1:-1].strip()
    return out


def _guard():
    if not is_admin():
        return jsonify({"error": "not found"}), 404
    return None


# ── Routes ───────────────────────────────────────────────────────────────────
@bp.route("/api/study/entries", methods=["GET"])
def list_entries():
    _ensure_tables()
    admin = is_admin()
    wanted = (request.args.get("type") or "").strip().lower()
    conn = study_db()
    try:
        if not admin:
            # PUBLIC: published TOPICS only. Graphs stay private; name-topics aren't
            # browseable here (they open from the metaV sidebar).
            if wanted and wanted != "topic":
                rows = []
            else:
                rows = conn.execute(
                    "SELECT id, type, title, json, status, updated FROM entries"
                    " WHERE deleted=0 AND type='topic' AND status='published'"
                    " ORDER BY updated DESC"
                ).fetchall()
        elif wanted in _TYPES:
            rows = conn.execute(
                "SELECT id, type, title, json, status, updated FROM entries"
                " WHERE deleted=0 AND type=? ORDER BY updated DESC",
                (wanted,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, type, title, json, status, updated FROM entries"
                " WHERE deleted=0 ORDER BY updated DESC"
            ).fetchall()
    finally:
        conn.close()
    out = []
    for r in rows:
        try:
            data = json.loads(r["json"]) or {}
        except (ValueError, TypeError):
            data = {}
        if r["type"] in ("topic", "name"):
            n = sum(len((s or {}).get("verses") or []) for s in (data.get("sections") or []))
        elif r["type"] == "graph":
            n = len(data.get("claims") or {})
        else:
            n = 0
        out.append({
            "id": r["id"], "type": r["type"], "title": r["title"],
            "n": n, "status": r["status"], "updated": r["updated"],
        })
    return jsonify({"entries": out})


@bp.route("/api/study/entry/<entry_id>", methods=["GET"])
def get_entry(entry_id):
    _ensure_tables()
    admin = is_admin()
    conn = study_db()
    try:
        r = conn.execute(
            "SELECT id, type, title, json, status, created, updated FROM entries"
            " WHERE id=? AND deleted=0",
            (entry_id,),
        ).fetchone()
    finally:
        conn.close()
    if not r:
        return jsonify({"error": "not found"}), 404
    # PUBLIC: only published topic-like entries (topics + metaV name-topics).
    # Graphs and any draft stay admin-only.
    if not admin and not (r["type"] in ("topic", "name") and r["status"] == "published"):
        return jsonify({"error": "not found"}), 404
    out = _resolved_entry(r)
    if not admin:
        out.pop("notes", None)   # never send private notes to a reader
    out.update({
        "id": r["id"], "type": r["type"], "title": r["title"],
        "status": r["status"], "created": r["created"], "updated": r["updated"],
    })
    return jsonify(out)


@bp.route("/api/study/entry", methods=["POST"])
@limiter.limit("400 per hour")
def save_entry():
    g = _guard()
    if g:
        return g
    raw = request.get_data(cache=False) or b""
    if len(raw) > _MAX_ENTRY_BYTES:
        return jsonify({"error": "too large"}), 413
    try:
        body = json.loads(raw or b"{}")
    except (ValueError, TypeError):
        return jsonify({"error": "bad request"}), 400
    if not isinstance(body, dict):
        return jsonify({"error": "bad request"}), 400

    etype = (body.get("type") or "").strip().lower()
    if etype not in _TYPES:
        return jsonify({"error": "bad type"}), 400
    title = str(body.get("title") or "").strip()[:300]
    if not title:
        return jsonify({"error": "A title is required."}), 400
    status = (body.get("status") or "draft").strip().lower()
    if status not in ("draft", "published"):
        status = "draft"

    stored = _body_from_request(etype, body)
    payload = json.dumps(stored, ensure_ascii=False)
    now = _now()
    _ensure_tables()
    conn = study_db()
    try:
        entry_id = str(body.get("id") or "").strip()
        existing = None
        if entry_id:
            existing = conn.execute(
                "SELECT created FROM entries WHERE id=?", (entry_id,)
            ).fetchone()
        if existing:
            conn.execute(
                "UPDATE entries SET type=?, title=?, json=?, status=?, updated=?, deleted=0"
                " WHERE id=?",
                (etype, title, payload, status, now, entry_id),
            )
        else:
            if not entry_id:
                entry_id = "e_" + secrets.token_urlsafe(9)
            conn.execute(
                "INSERT INTO entries (id, type, title, json, status, created, updated, deleted)"
                " VALUES (?,?,?,?,?,?,?,0)",
                (entry_id, etype, title, payload, status, now, now),
            )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"id": entry_id, "updated": now})


@bp.route("/api/study/entry/<entry_id>/delete", methods=["POST"])
@limiter.limit("200 per hour")
def delete_entry(entry_id):
    g = _guard()
    if g:
        return g
    _ensure_tables()
    conn = study_db()
    try:
        conn.execute(
            "UPDATE entries SET deleted=1, updated=? WHERE id=?", (_now(), entry_id)
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True})


@bp.route("/api/study/verse", methods=["GET", "POST"])
@limiter.limit("600 per hour")
def resolve_verse():
    """Auto-fill helper: look up one reference's ABP prose text as the editor adds it.
    Takes the reference from a POST JSON body (the editor's path — query params on this
    one were being dropped before the app, unlike the POST endpoints that always worked),
    falling back to a ?ref= query for compatibility."""
    g = _guard()
    if g:
        return g
    ref = (request.args.get("ref") or "").strip()
    if not ref and request.method == "POST":
        body = request.get_json(silent=True) or {}
        if isinstance(body, dict):
            ref = (body.get("ref") or "").strip()
    if not ref:
        # admin-only endpoint, so it's safe to echo what arrived — diagnostic if it ever recurs
        return jsonify({"error": "no reference", "saw": request.full_path}), 400
    verses = _resolve_ref(ref)
    if not verses:
        return jsonify({"ref": ref, "verses": [], "error": "Couldn't find that reference."}), 200
    return jsonify({"ref": ref, "canonical": _canonical_ref(ref), "verses": verses})


@bp.route("/api/study/for-name/<name>", methods=["GET"])
@limiter.limit("600 per hour")
def for_name(name):
    """The Nave's topical study for a person/place name (its subtopic sections +
    verses), shown on the metaV sidebar. Loaded as a 'name'-type entry by the
    topics loader; id = 'metavn_' + slug(name). Empty {sections:[]} if there's none."""
    _ensure_tables()
    admin = is_admin()
    entry_id = "metavn_" + _slug(name)
    conn = study_db()
    try:
        r = conn.execute(
            "SELECT title, json, status FROM entries WHERE id=? AND deleted=0", (entry_id,)
        ).fetchone()
    finally:
        conn.close()
    # PUBLIC: published name-topics only; drafts stay admin-only.
    if not r or (not admin and r["status"] != "published"):
        return jsonify({"name": name, "id": None, "sections": []})
    try:
        stored = json.loads(r["json"]) or {}
    except (ValueError, TypeError):
        stored = {}
    secs = [{"heading": (s or {}).get("heading", ""), "n": len((s or {}).get("verses") or [])}
            for s in (stored.get("sections") or [])]
    return jsonify({"name": r["title"], "id": entry_id, "sections": secs})


@bp.route("/api/study/for-verse/<book>/<int:chapter>/<int:verse>", methods=["GET"])
@limiter.limit("600 per hour")
def for_verse(book, chapter, verse):
    """PUBLIC: which published CONCEPT topics cite this verse — the reader's 'In studies:'
    line. {topics:[{id,title}]}, empty if none. Name-topics are deliberately excluded."""
    idx = _verse_index()
    hits = idx.get((book, chapter, verse), [])
    return jsonify({"topics": [{"id": i, "title": t} for i, t in hits]})


@bp.route("/api/study/draft-intro", methods=["POST"])
@limiter.limit("120 per hour")
def draft_intro_route():
    """Admin: draft a text-first intro for the topic being edited (title + sections in
    the body). Returns {intro}; the editor fills the field and the admin reviews + saves."""
    g = _guard()
    if g:
        return g
    if not _anthropic:
        return jsonify({"error": "AI not available"}), 503
    try:
        body = json.loads(request.get_data(cache=False) or b"{}")
    except (ValueError, TypeError):
        return jsonify({"error": "bad request"}), 400
    if not isinstance(body, dict):
        return jsonify({"error": "bad request"}), 400
    title = str(body.get("title") or "").strip()
    sections = body.get("sections") or []
    if not title and not sections:
        return jsonify({"error": "nothing to summarize"}), 400
    intro = _draft_intro(title, sections)
    if not intro:
        return jsonify({"error": "couldn't draft an intro"}), 500
    return jsonify({"intro": intro})
