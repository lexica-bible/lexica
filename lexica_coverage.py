#!/usr/bin/env python3
"""
lexica_coverage.py — coverage/collocation detection for the Lexica dictionary engine.

Two gap classes surface in built lexica_def entries, and this module makes the engine catch
them structurally instead of by eyeball:

  PIECE A — collocation pre-check (this file, LIVE).  Before (or after) the model draw, scan
  ALL of a word's real occurrences — not just the fed sample — for a repeated adjacent-lemma
  pattern (a fixed collocation, e.g. huios+anthrōpos "son of man" under G5207). If a collocation
  above a floor has ZERO representatives in the fed draw, that draw has a blind spot: the model
  never saw the pattern, so a whole sense can go missing (G5207 sense 6 was absent until hand-added).
  Pure SQL, no model cost. `scan_collocations` is the detector; the driver computes the draw with
  the SAME `select_spread` the build uses, so "in the draw" means exactly what the model saw.

  PIECE B — coverage field with teeth (schema pending JP review; NOT built here yet).

The stop-list mirrors the app's own function-word classifier (app.py `_build_function_strongs_cache`
= LSJ POS classify + the hardcoded override set) so the scan never floods on article/kai/prepositions.

PURE / READ-ONLY: every function takes an open sqlite connection and only SELECTs. No writes, no
model calls. Imported by scripts/audit_lexica_coverage.py (standalone) and, warn-only, by
scripts/build_lexica_def.py.
"""

import re
import unicodedata


# ── Tunables ────────────────────────────────────────────────────────────────────────────────
COLLOC_FLOOR  = 10   # a collocation must appear in at least this many distinct verses to matter.
                     # Below it, an adjacency is noise, not a fixed pattern worth a sense.
COLLOC_WINDOW = 2    # ordinal half-window: a neighbor within this many tokens of the target counts
                     # as adjacent. 2 spans the article-genitive ("son [of] man" = huios tou anthrōpou),
                     # tight enough not to sweep the whole verse.
MAX_EXAMPLES  = 6    # example refs shown per flagged collocation.


# ── Function-word stop-list — mirror of app.py's classifier, self-contained ──────────────────
# The BARE (un-prefixed) Strong's numbers the app hardcodes because the LSJ POS detector misses
# them (pronouns, negatives, the common conjunctions/particles/prepositions whose LSJ entries
# don't join). Copied VERBATIM from app.py `_FUNCTION_STRONGS_OVERRIDE` — keep in sync if that
# set changes (they are both the same fact: "this number is a function word").
_OVERRIDE_BARE = frozenset({
    # negatives
    "3361", "3756", "3761", "3762", "3763", "3777", "3780", "3364",
    # personal / reflexive pronouns
    "1473", "4771", "846", "2249", "5210", "1438",
    # demonstratives
    "3778", "1565", "3592",
    # article
    "3588",
    # relative / interrogative / indefinite
    "3739", "3748", "5101", "5100",
    # conjunctions / particles
    "2532", "1161", "3767", "235", "1063", "3754", "2443", "1487", "5613", "1437",
    "3303", "2228", "686", "1065", "4458",
    # prepositions
    "1722", "1519", "1537", "575", "4314", "2596", "3326", "1223", "1909", "4012",
    "5228", "5259", "4253", "473", "303",
})

# LSJ POS detectors — verbatim from app.py so a standalone run classifies the same way the live
# site does (a bold POS section header, or a POS word near the headword).
_LSJ_FUNC_WORD_RE = re.compile(
    r'\b(?:'
    r'Prep(?:osition)?[.,\s]|Conj(?:unction)?[.,\s]|Part(?:icle)?[.,\s]|'
    r'Art(?:icle)?[.,\s]|definite\s+article\b|'
    r'preposition\b|conjunction\b|particle\b|article\b'
    r')', re.IGNORECASE)
_LSJ_FUNC_BOLD_RE = re.compile(
    r'<b>(?:PREP(?:OSITION)?|CONJ(?:UNCTION)?|PART(?:ICLE)?|ART(?:ICLE)?)[.,\s<]', re.IGNORECASE)


def _strip_accents(s):
    if s is None:
        return s
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _is_lsj_function_word(def_html):
    html = def_html or ""
    if _LSJ_FUNC_BOLD_RE.search(html[:3000]):
        return True
    tail = re.sub(r'^\s*<b>[^<]*</b>', '', html.strip())
    text = re.sub(r'<[^>]+>', ' ', tail[:300]).strip()
    return bool(_LSJ_FUNC_WORD_RE.search(text[:200]))


def _table_exists(conn, name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (name,)).fetchone() is not None


def function_bare_strongs(conn):
    """The stop-list as BARE numbers ('444', not 'G444'): the hardcoded override union the
    LSJ-classified function words — the same union the live app builds. If the lsj/lexicon tables
    aren't present, falls back to the override set alone (still covers every flooder: article, kai,
    de, the prepositions and particles)."""
    stop = set(_OVERRIDE_BARE)
    if _table_exists(conn, "lsj") and _table_exists(conn, "lexicon"):
        try:
            conn.create_function("strip_accents", 1, _strip_accents)
            rows = conn.execute(
                "SELECT l.strongs AS s, lsj.def_html AS d "
                "FROM lexicon l JOIN lsj ON lsj.plain = lower(strip_accents(l.lemma))").fetchall()
            for r in rows:
                if _is_lsj_function_word(r["d"] if hasattr(r, "keys") else r[1]):
                    stop.add(str(r["s"] if hasattr(r, "keys") else r[0]))
        except Exception:
            pass   # override-only fallback; never let a classifier hiccup break the scan
    return stop


def _bare(strongs_base):
    """'G444' / 'H430' -> '444' / '430'. Digits only, so a dotted 'G444.2' folds to '444.2'? no —
    the scan works on strongs_base, which already drops the dot. Just strip a leading letter."""
    if not strongs_base:
        return ""
    return strongs_base[1:] if strongs_base[:1] in ("G", "H") else strongs_base


def _fetch_verse_tokens(conn, vids):
    """vid -> [(position, strongs_base)] for every target verse, ordered by position. Chunked IN."""
    out = {}
    vids = list(vids)
    for i in range(0, len(vids), 400):
        chunk = vids[i:i + 400]
        q = "SELECT verse_id AS vid, position AS pos, strongs_base AS base FROM words " \
            "WHERE verse_id IN (%s) ORDER BY verse_id, position" % ",".join("?" * len(chunk))
        for r in conn.execute(q, chunk):
            out.setdefault(r["vid"], []).append((r["pos"], r["base"]))
    return out


def _ref_map(occs):
    """vid -> 'Book ch:vs' from the target's own occurrence rows."""
    ref = {}
    for o in occs:
        ref.setdefault(o["vid"], f'{o["book"]} {o["ch"]}:{o["vs"]}')
    return ref


def collocation_map(conn, sid, occs, stop=None, floor=COLLOC_FLOOR, window=COLLOC_WINDOW):
    """The core scan, shared by A (draw audit) and B (coverage). Returns
    {neighbor_base: set(vids)} for every content-word neighbor sitting within `window` ordinal
    tokens of a target occurrence, filtered to neighbors at/above `floor` distinct verses. Function
    words are stop-listed so it never floods on article/kai/prepositions."""
    if stop is None:
        stop = function_bare_strongs(conn)
    tgt_pos, tgt_vids = {}, set()
    for o in occs:
        tgt_vids.add(o["vid"])
        tgt_pos.setdefault(o["vid"], set()).add(o["pos"])
    tokens = _fetch_verse_tokens(conn, tgt_vids)

    colloc = {}
    for vid, toks in tokens.items():
        idx_of = {pos: i for i, (pos, _b) in enumerate(toks)}   # ordinal index (robust to pos gaps)
        tgt_idxs = [idx_of[p] for p in (tgt_pos.get(vid) or set()) if p in idx_of]
        n = len(toks)
        for ti in tgt_idxs:
            for j in range(max(0, ti - window), min(n, ti + window + 1)):
                if j == ti:
                    continue
                base = toks[j][1]
                if not base or base == sid or base[:1] != "G":   # Greek content neighbors only
                    continue
                if _bare(base) in stop:
                    continue
                colloc.setdefault(base, set()).add(vid)
    return {b: vids for b, vids in colloc.items() if len(vids) >= floor}


def scan_collocations(conn, sid, occs, sample_vids, stop=None,
                      floor=COLLOC_FLOOR, window=COLLOC_WINDOW):
    """PIECE A — report which at/above-floor collocations the fed draw (`sample_vids`) failed to
    represent. Returns findings sorted by verse-count desc, each:
      {neighbor, lemma, translit, verses, in_draw, missed, examples[]}
    `missed` (in_draw == 0) is the trip: a real collocation the draw never saw."""
    sample_vids = set(sample_vids or ())
    colloc = collocation_map(conn, sid, occs, stop=stop, floor=floor, window=window)
    ref = _ref_map(occs)
    findings = []
    for base, vids in colloc.items():
        in_draw = len(vids & sample_vids)
        lemma, translit = _neighbor_head(conn, base)
        findings.append({
            "neighbor": base, "lemma": lemma, "translit": translit,
            "verses": len(vids), "in_draw": in_draw, "missed": in_draw == 0,
            "examples": [ref[v] for v in sorted(vids) if v in ref][:MAX_EXAMPLES],
        })
    findings.sort(key=lambda f: (-f["verses"], f["neighbor"]))
    return findings


def rendering_sets(occs):
    """gloss(lowercased) -> set(vids) from the target's occurrences, using each occurrence's
    english_head (rend). The 'renders as' distribution, as verse sets so B can test 'cited'."""
    out = {}
    for o in occs:
        g = (o["rend"] or "").strip().lower()
        if g:
            out.setdefault(g, set()).add(o["vid"])
    return out


def refs_to_vids(conn, refs):
    """[(book, ch, vs)] -> set of verse-ids that exist in `verses`. Refs ABP lacks are dropped."""
    vids = set()
    for book, ch, vs in refs:
        r = conn.execute("SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
                         (book, ch, vs)).fetchone()
        if r:
            vids.add(r["id"])
    return vids


_HEAD_CACHE = {}
def _neighbor_head(conn, base):
    if base in _HEAD_CACHE:
        return _HEAD_CACHE[base]
    lemma, translit = base, ""
    try:
        r = conn.execute("SELECT lemma, translit FROM lexicon WHERE strongs_g = ?", (base,)).fetchone()
        if r:
            lemma = (r["lemma"] or base)
            translit = (r["translit"] or "")
    except Exception:
        pass
    _HEAD_CACHE[base] = (lemma, translit)
    return _HEAD_CACHE[base]


def missed_collocations(findings):
    """Just the trips — collocations at/above floor with zero draw representation."""
    return [f for f in findings if f["missed"]]
