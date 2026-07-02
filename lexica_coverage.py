#!/usr/bin/env python3
"""
lexica_coverage.py — coverage/collocation detection for the Lexica dictionary engine.

Two gap classes surface in built lexica_def entries, and this module makes the engine catch
them structurally instead of by eyeball:

  PIECE A — collocation pre-check (this file, LIVE).  Before (or after) the model draw, scan
  ALL of a word's real occurrences — not just the fed sample — for a repeated adjacent-lemma
  pattern (a fixed collocation). A pair is RANKED by tightness (token-level PMI) and FLAGGED only
  when it clears the count floor AND the tightness threshold AND has ZERO representatives in the
  fed draw. Pure SQL, no model cost. `scan_collocations` is the detector; the driver computes the
  draw with the SAME `select_spread` the build uses, so "in the draw" means exactly what the model
  saw. A catches only SMALL tight collocations the draw missed ENTIRELY — a big collocation (~5% of
  a word's uses) is essentially never 0-in-draw, so those are B's job, not A's.

  PIECE B — coverage-with-teeth: post-build, check the finished ENTRY (not the draw) — do the
  senses actually cite the top collocations/renderings, and is any contested sense circular?
  This is the real guarantee that catches the son-of-man-class miss. (schema approved; building next.)

The stop-list mirrors the app's own function-word classifier (app.py `_build_function_strongs_cache`
= LSJ POS classify + the hardcoded override set) so the scan never floods on article/kai/prepositions.

ACCEPTANCE (updated after the live calibration run):
  - Piece A: (1) the offline fixture tests (a tight pair flags, a loose one of the same count does
    not); (2) no flood on a real high-frequency word (single-digit flags, not 65–89); (3) it flags
    a TRULY-ABSENT tight collocation (0 in draw). A does NOT own the G5207 known miss — see below.
  - The G5207 "son of man" known-miss validation belongs to PIECE B, not A: the draw already
    contains a son-of-man verse (in-draw 1), so A's "0 in draw" rule correctly does not fire; the
    pre-sense-6 ENTRY cited zero son-of-man verses, which B flags (thin/uncited), and the current
    entry passes. B is the finished-entry check; A is the draw-composition check.

PIECE C — stratified sampling: DEFERRED, not built. First evidence entry for why it may eventually be
  needed: G5207 huios+anthrōpos conflates OT generic "sons of men" with the NT title "the Son of Man"
  — indistinguishable by adjacency, so no collocation/coverage check separates the missed titular
  sense from the generic one; only a draw stratified by corpus layer (LXX vs Gospels) would surface
  it. Recording the case, not building the fix.

PURE / READ-ONLY: every function takes an open sqlite connection and only SELECTs. No writes, no
model calls. Imported by scripts/audit_lexica_coverage.py (standalone) and, warn-only, by
scripts/build_lexica_def.py.
"""

import re
import unicodedata


# ── Tunables ────────────────────────────────────────────────────────────────────────────────
COLLOC_FLOOR  = 10   # a collocation must appear in at least this many distinct verses to matter.
                     # Below it, an adjacency is noise, not a fixed pattern worth a sense. This is a
                     # FLOOR kept ALONGSIDE the tightness score (below), not replaced by it: pure
                     # association overweights rare pairs (a neighbor seen twice can out-score "son
                     # of man"), so we score only among pairs that also clear this count floor.
COLLOC_WINDOW = 2    # ordinal half-window: a neighbor within this many tokens of the target counts
                     # as adjacent. 2 spans the article-genitive ("son [of] man" = huios tou anthrōpou,
                     # proven live: huios+anthrōpos adjacent in 257 ABP verses at window 2),
                     # tight enough not to sweep the whole verse.
MAX_EXAMPLES  = 6    # example refs shown per flagged collocation.

# ── Tightness (association) threshold. WHY: a raw count can't tell a FIXED phrase ("son of man")
# from a merely FREQUENT one ("God said") — both clear a count floor. And with a 40-verse draw over
# a ~5,000-occurrence word, "absent from the draw" is the expected state for almost every pair, so
# 0-in-draw alone carries no signal (it flagged 65–89 pairs per word). The fix is to measure how
# much MORE the neighbor sits ADJACENT to the target than its overall commonness predicts (pointwise
# mutual information, in bits) — TOKEN-level, not verse-level:
#   PMI = log2( co * N_tok / (t_occ * w_tok) )
#     co    = verses where target+neighbor are adjacent   t_occ = target occurrences (tokens)
#     w_tok = neighbor's total tokens in the corpus       N_tok = total word tokens
# TOKEN not verse is the whole fix: two common words ("son", "man") land in the same VERSE by chance
# far more often than they land ADJACENT, so verse-level marginals scored "son of man" at ~0.5 (noise).
# Against the neighbor's token share, huios+anthrōpos is many times more adjacent than chance → high.
# PMI = 0 means chance; each +1 bit means twice as tight. A fixed phrase scores high (the neighbor
# rarely appears except beside the target); a common verb scores near 0 (it's everywhere).
# CALIBRATION: 4.0 is a provisional start — re-tune from the --show-all score column when new words
# are built. Raise it if the flagged list runs past single digits; lower it if a real fixed phrase
# falls below the noise. The TRIP condition is: above the count floor AND PMI >= this AND 0 in draw.
# NOTE: a BIG collocation (huios+anthrōpos, 257 verses ≈ 5% of huios) is basically never 0-in-draw,
# so A catches only SMALL tight collocations the draw missed entirely; the son-of-man-class miss is a
# piece-B (finished-entry coverage) catch, not an A catch. See ACCEPTANCE below.
PMI_MIN = 4.0


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
    # OBLIQUE personal-pronoun FORMS — beyond app.py's set. σοῦ/μοῦ/σοί/μέ/σέ carry their OWN
    # Strong's numbers, separate from the base pronoun (σύ 4771, ἐγώ 1473) already listed. They
    # were the top of the flood on G5207/G2316 ("your son", "my God") — pure grammar, not a sense.
    "3450", "3427", "3165", "1700", "1698", "1691",   # ἐμοῦ/μου, ἐμοί/μοι, ἐμέ/με (1st sing.)
    "4675", "4671", "4571", "4572",                    # σοῦ/σου, σοί/σοι, σέ/σε, σεαυτοῦ (2nd sing.)
    "2257", "2254", "2248",                            # ἡμῶν, ἡμῖν, ἡμᾶς (1st plur.)
    "5216", "5213", "5209",                            # ὑμῶν, ὑμῖν, ὑμᾶς (2nd plur.)
    "1683", "848",                                     # ἐμαυτοῦ, αὑτοῦ (reflexives)
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


import weakref
_CORPUS_COUNTS = weakref.WeakKeyDictionary()   # conn -> (N_tok, {base: token-count})
def _corpus_token_counts(conn):
    """(N_tok, {strongs_base: how-many-TOKENS carry it}) for the whole word table — the TOKEN-level
    marginals the tightness score needs. TOKEN, not verse: the score measures how often a neighbor
    sits NEXT TO the target vs. how common the neighbor is overall, so the baseline must be the
    neighbor's share of all word tokens — verse-level counts wash out adjacency (two common words
    land in the same verse by chance far more often than they land adjacent, so verse marginals made
    'son of man' score ~0.5). One GROUP BY over `words`; cached per LIVE connection (weak-keyed, so a
    freed connection's id can't hand back stale counts)."""
    try:
        cached = _CORPUS_COUNTS.get(conn)
    except TypeError:
        cached = None                          # connection not weak-referenceable → just recompute
    if cached is not None:
        return cached
    n_tok = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0] or 0
    counts = {}
    for r in conn.execute(
            "SELECT strongs_base AS b, COUNT(*) AS c FROM words "
            "WHERE strongs_base IS NOT NULL AND strongs_base != '' GROUP BY strongs_base"):
        counts[r["b"]] = r["c"]
    result = (n_tok, counts)
    try:
        _CORPUS_COUNTS[conn] = result
    except TypeError:
        pass
    return result


def _pmi(co, t_occ, w_tok, n_tok):
    """Pointwise mutual information in bits, TOKEN-level: how much more the neighbor sits adjacent to
    the target than its overall commonness predicts.
        observed rate = co / t_occ            (share of target occurrences with the neighbor adjacent)
        baseline rate = w_tok / n_tok         (the neighbor's share of ALL word tokens)
        PMI = log2(observed / baseline) = log2(co * n_tok / (t_occ * w_tok))
    0 = no more than chance; +1 bit = twice as tight. None if any marginal is 0."""
    if co <= 0 or t_occ <= 0 or w_tok <= 0 or n_tok <= 0:
        return None
    import math
    return math.log2((co * n_tok) / (t_occ * w_tok))


def scan_collocations(conn, sid, occs, sample_vids, stop=None,
                      floor=COLLOC_FLOOR, window=COLLOC_WINDOW, pmi_min=PMI_MIN):
    """PIECE A — report the at/above-floor collocations, scored by tightness, and flag the ones the
    fed draw (`sample_vids`) missed. Returns findings sorted by score desc, each:
      {neighbor, lemma, translit, verses, score, in_draw, missed, flagged, examples[]}
    `flagged` is the TRIP: verses >= floor (already) AND score >= pmi_min AND in_draw == 0 — a
    TIGHT collocation the draw never saw. `missed` (0 in draw, any tightness) is kept for context."""
    sample_vids = set(sample_vids or ())
    colloc = collocation_map(conn, sid, occs, stop=stop, floor=floor, window=window)
    ref = _ref_map(occs)
    n_tok, counts = _corpus_token_counts(conn)
    t_occ = len(occs)                          # target occurrence tokens (baseline denominator)
    findings = []
    for base, vids in colloc.items():
        co = len(vids)
        in_draw = len(vids & sample_vids)
        score = _pmi(co, t_occ, counts.get(base, 0), n_tok)
        lemma, translit = _neighbor_head(conn, base)
        findings.append({
            "neighbor": base, "lemma": lemma, "translit": translit,
            "verses": co, "score": score, "in_draw": in_draw, "missed": in_draw == 0,
            "flagged": (score is not None and score >= pmi_min and in_draw == 0),
            "examples": [ref[v] for v in sorted(vids) if v in ref][:MAX_EXAMPLES],
        })
    findings.sort(key=lambda f: (-(f["score"] if f["score"] is not None else -99), -f["verses"]))
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
    """Just the trips — TIGHT collocations (above the score threshold) the draw missed."""
    return [f for f in findings if f["flagged"]]


# ══════════════════════════════════════════════════════════════════════════════════════════════
# PIECE B — coverage-with-teeth. Post-build, check the FINISHED ENTRY (not the draw): do the senses
# actually cite the tight collocations + the top renderings, and is any contested sense circular?
# Pure derivation from the stored entry — no model. This is the guarantee that catches the
# son-of-man-class miss (the draw held a son-of-man verse, but the pre-sense-6 ENTRY cited none).
# ══════════════════════════════════════════════════════════════════════════════════════════════
_CV_RE = re.compile(r'^\s*(\d?\s*[A-Za-z]+)\s+(\d+)(?::(\d+)(?:-(\d+))?)?\s*$')

def _parse_contest(entries):
    """contest_verses strings -> (verse_set{(book,ch,vs)}, chapter_set{(book,ch)}). Accepts a
    verse 'Rom 10:13', a range 'Php 2:9-11' (expanded), or a chapter 'Jas 2' (whole-chapter match).
    Books are canonical verses.book codes already (the register authors them that way)."""
    vset, cset = set(), set()
    for e in entries or []:
        m = _CV_RE.match(e or "")
        if not m:
            continue
        book = m.group(1).replace(" ", "")
        ch = int(m.group(2))
        if m.group(3) is None:
            cset.add((book, ch))                       # chapter-level
        else:
            lo, hi = int(m.group(3)), int(m.group(4) or m.group(3))
            for v in range(lo, hi + 1):
                vset.add((book, ch, v))
    return vset, cset


def coverage_audit(conn, sid, occs, entry_refs, sense_specs, contest_verses=None,
                   is_contested=False, floor=COLLOC_FLOOR, window=COLLOC_WINDOW,
                   pmi_min=PMI_MIN, top_renderings=10, max_colloc=20, thin_max=1):
    """Build the coverage_audit block for one entry (no model call).

      entry_refs   the (book,ch,vs) refs the entry actually cites  (build: cited_refs(raw))
      sense_specs  [{headline, refs:[(book,ch,vs)]}] per sense, in order (build parses these — it
                   owns the sense splitter; keeping it there avoids duplicating that logic here)

    Returns {collocations, renderings, senses, thin_senses, contested, flags}:
      collocations  the TIGHT corpus phrases (PMI >= pmi_min), each cited-or-not by the entry
      renderings    the top renderings by frequency, each cited-or-not
      senses        EVERY sense with its support-ref count + self_only  (kept as piece-C evidence)
      thin_senses   the subset flagged: support_refs <= thin_max OR self_only (circular)
      self_only     a sense whose every cited support ref sits inside the word's contest_verses —
                    circular: it never corroborates from outside the disputed passage. Fires only on
                    a contested word with a contest_verses locus; inert (False) otherwise.
    """
    entry_vids = refs_to_vids(conn, entry_refs)

    # collocations — the tight phrases, cited-or-not
    colloc = collocation_map(conn, sid, occs, floor=floor, window=window)
    n_tok, counts = _corpus_token_counts(conn)
    t_occ = len(occs)
    colls = []
    for base, vids in colloc.items():
        score = _pmi(len(vids), t_occ, counts.get(base, 0), n_tok)
        if score is None or score < pmi_min:
            continue
        lemma, translit = _neighbor_head(conn, base)
        colls.append({"neighbor": base, "lemma": lemma, "translit": translit,
                      "verses": len(vids), "score": round(score, 2),
                      "cited": bool(vids & entry_vids)})
    colls.sort(key=lambda c: -c["score"])
    colls = colls[:max_colloc]

    # renderings — top-N by frequency, cited-or-not
    rsets = rendering_sets(occs)
    top = sorted(rsets.items(), key=lambda kv: -len(kv[1]))[:top_renderings]
    rendings = [{"gloss": g, "count": len(v), "cited": bool(v & entry_vids)} for g, v in top]

    # senses — support count + circular flag
    vset, cset = _parse_contest(contest_verses)
    has_locus = bool(vset or cset)
    senses, thin = [], []
    for i, spec in enumerate(sense_specs or [], 1):
        refs = spec.get("refs") or []
        sup = len(refs)
        self_only = bool(is_contested and has_locus and sup > 0 and
                         all(((b, c, v) in vset) or ((b, c) in cset) for (b, c, v) in refs))
        rec = {"sense": i, "headline": spec.get("headline", ""),
               "support_refs": sup, "self_only": self_only}
        senses.append(rec)
        if sup <= thin_max or self_only:
            thin.append(rec)

    # short rollup for the card / audit print
    flags = []
    for c in colls:
        if not c["cited"]:
            flags.append(f"collocation {c['translit'] or c['neighbor']} uncited ({c['verses']}v)")
    for r in rendings:
        if not r["cited"] and r["count"] >= floor:
            flags.append(f"rendering '{r['gloss']}' uncited ({r['count']}x)")
    if is_contested:
        for t in thin:
            flags.append(f"sense {t['sense']} " + ("circular" if t["self_only"] else "thin"))

    return {"collocations": colls, "renderings": rendings, "senses": senses,
            "thin_senses": thin, "contested": bool(is_contested), "flags": flags}
