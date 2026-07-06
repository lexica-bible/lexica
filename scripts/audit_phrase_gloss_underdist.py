#!/usr/bin/env python3
"""
audit_phrase_gloss_underdist.py — READ-ONLY. The S9 fix-(g) detector: a MULTI-WORD
English gloss parked WHOLE on a FUNCTION-WORD slot while the adjacent CONTENT-word
slot that owns part of the phrase sits EMPTY. The UNDER-distribution twin of the
_split_compounds OVER-reach (the charter's "one leaky gate misfires both ways").

CONTROL POSITIVE (must FIRE before any zero is trusted): Psa 39:1 — "to not sin"
parked entirely on G3361 (μή), neighbour G264 (ἁμαρτάνειν, "sin") blank. The script
asserts Psa 39:1 is in the FLAGGED set and prints CONTROL: FIRED / MISSED. A MISSED
control means the count is untrustworthy — do NOT read the zero as clean.

A candidate must clear ALL of:
  1. the slot's own Strong's is a FUNCTION word (LSJ-classified ∪ the app's override
     set — same notion core._FUNCTION_STRONGS uses, rebuilt here self-contained).
  2. its english gloss is MULTI-WORD (has a space) — a phrase, not the func word's
     own one-word render.
  3. the gloss's CONTENT head (last word not in the func/stop/pronoun sets) is a real
     content word — i.e. the phrase carries a word that is NOT the func word's own.
  4. an ADJACENT slot (±1) is EMPTY yet carries a real content Strong's (not a func
     word, not '*', not '') — the orphaned word's own slot.
  5. that orphan slot's LEXICON definition CONTAINS the head (evidence the parked
     content word belongs to the empty neighbour) — the same kjv_def/strongs_def test
     _split_compounds uses to DISTRIBUTE. This is what makes it under-distribution.

BUCKETS:
  FLAGGED        all 5 clear — the under-distribution class (Psa 39:1 lives here)
  NO-EVIDENCE    blank content neighbour but its def does NOT contain the head — review
  (candidates failing 1-4 are simply not counted)

READ-ONLY (mode=ro). Run on PA from the repo root (needs bible.db only):
  python3 scripts/audit_phrase_gloss_underdist.py bible.db
  python3 scripts/audit_phrase_gloss_underdist.py bible.db --dump-all
  python3 scripts/audit_phrase_gloss_underdist.py bible.db --book Psa
"""
import os
import re
import sqlite3
import sys
import unicodedata
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from parse_abp import _FUNCTION_WORDS, _HEAD_STOP
except Exception:                                       # pragma: no cover
    _FUNCTION_WORDS, _HEAD_STOP = frozenset(), frozenset()

ARGS = sys.argv[1:]
DB = next((a for a in ARGS if not a.startswith("--")), "bible.db")
DUMP_ALL = "--dump-all" in ARGS
BOOK_FILTER = ARGS[ARGS.index("--book") + 1] if "--book" in ARGS else None

# ── function-word set: LSJ classification ∪ override (mirrors app._build_function_strongs_cache) ──
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


def _is_lsj_function_word(def_html):
    html = def_html or ''
    if _LSJ_FUNC_BOLD_RE.search(html[:3000]):
        return True
    tail = re.sub(r'^\s*<b>[^<]*</b>', '', html.strip())
    text = re.sub(r'<[^>]+>', ' ', tail[:300]).strip()
    return bool(_LSJ_FUNC_WORD_RE.search(text[:200]))


# The app's hardcoded override (bare numbers) — negatives/pronouns/article/conj/prep/particles.
_FUNCTION_STRONGS_OVERRIDE = {
    "3361", "3756", "3761", "3762", "3763", "3777", "3780", "3364",
    "1473", "4771", "846", "2249", "5210", "1438",
    "3778", "1565", "3592", "3588",
    "3739", "3748", "5101", "5100",
    "2532", "1161", "3767", "235", "1063", "3754", "2443", "1487", "5613",
    "1437", "3303", "2228", "686", "1065", "4458",
    "1722", "1519", "1537", "575", "4314", "2596", "3326", "1223", "1909",
    "4012", "5228", "5259", "4253", "473", "303",
}


def _strip_accents(s):
    if not s:
        return s
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def bare(s):
    return re.sub(r"[^\w]", "", s or "").lower()


def base_of(strongs_base):
    """words.strongs_base 'G3361' -> bare '3361' (drop prefix + dotted tail)."""
    return (strongs_base or "").lstrip("GH").split(".")[0]


def singular(w):
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith(("ses", "xes", "zes", "ches", "shes")):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


_EXTRA_FUNC = {
    "me", "him", "them", "us", "thee", "thy", "thine", "mine", "whom", "whose",
    "one", "ones", "thing", "things", "both", "who", "which", "what", "all",
    "any", "some", "each", "every", "other", "others", "same", "such",
    "whoever", "whatever", "anyone", "none", "not", "no",
}
SKIP_HEADS = set(_FUNCTION_WORDS) | set(_HEAD_STOP) | _EXTRA_FUNC


def derive_head(english):
    for tok in reversed((english or "").split()):
        b = bare(tok)
        if b and b not in SKIP_HEADS:
            return b
    return None


conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

# lexicon: bare strongs -> def word-set (for the evidence test) and function classification
lex = {}
strip = None
try:
    conn.create_function("strip_accents", 1, _strip_accents)
    strip = True
except Exception:
    pass

FUNC = set(_FUNCTION_STRONGS_OVERRIDE)
lex_rows = conn.execute("SELECT strongs, kjv_def, strongs_def FROM lexicon").fetchall()
for row in lex_rows:
    b = base_of("G" + (row["strongs"] or ""))
    text = " ".join(filter(None, [row["kjv_def"], row["strongs_def"]]))
    lex[b] = set(re.sub(r"[^\w\s]", " ", text).lower().split())

# LSJ-derived function words (join lexicon.lemma -> lsj.def_html), if the lsj table exists
try:
    q = ("SELECT l.strongs, lsj.def_html FROM lexicon l "
         "JOIN lsj ON lsj.plain = lower(strip_accents(l.lemma))"
         if strip else
         "SELECT l.strongs, lsj.def_html FROM lexicon l "
         "JOIN lsj ON lsj.plain = lower(l.lemma)")
    for row in conn.execute(q):
        if _is_lsj_function_word(row["def_html"]):
            FUNC.add((row["strongs"] or "").split(".")[0])
except Exception as e:
    print(f"  (note: LSJ classification skipped: {e}; using override set only)", file=sys.stderr)


def gloss_has(head, base):
    d = lex.get(base, set())
    return head in d or singular(head) in d


def neighbour(verse_id, position, delta):
    return conn.execute(
        "SELECT english, strongs_base FROM words WHERE verse_id=? AND position=?",
        (verse_id, position + delta)).fetchone()


def find_blank_content_neighbour(verse_id, position, head):
    """Adjacent EMPTY slot with a real content Strong's whose def contains the head."""
    for delta in (1, -1):
        nb = neighbour(verse_id, position, delta)
        if nb and (nb["english"] or "").strip() == "":
            nbase = base_of(nb["strongs_base"])
            if nbase and nbase not in ("", "*") and nbase not in FUNC:
                return nb, nbase, delta
    return None, None, None


# candidate slots: a function-word host carrying a MULTI-WORD gloss
cands = conn.execute(
    "SELECT w.verse_id, w.position, w.english, w.strongs_base, v.book, v.chapter, v.verse "
    "FROM words w JOIN verses v ON v.id = w.verse_id "
    "WHERE w.english LIKE '% %' AND w.english IS NOT NULL "
    "ORDER BY w.verse_id, w.position").fetchall()

buckets = Counter()
flagged, no_evidence = [], []
for c in cands:
    if BOOK_FILTER and c["book"] != BOOK_FILTER:
        continue
    hbase = base_of(c["strongs_base"])
    if hbase not in FUNC:                    # 1: host must be a function word
        continue
    head = derive_head(c["english"])         # 3: a content head in the phrase
    if not head:
        continue
    nb, nbase, delta = find_blank_content_neighbour(c["verse_id"], c["position"], head)
    if nb is None:                           # 4: adjacent blank content slot
        continue
    ref = f"{c['book']} {c['chapter']}:{c['verse']}"
    rec = (ref, c["strongs_base"], head, c["english"], f"orphan[{delta:+d}]={nb['strongs_base']}")
    if gloss_has(head, nbase):               # 5: the head belongs to the empty neighbour
        buckets["FLAGGED"] += 1
        flagged.append(rec)
    else:
        buckets["NO-EVIDENCE"] += 1
        no_evidence.append(rec)

conn.close()

# ── control-fire check (before any zero is trusted) ──────────────────────────
control = next((r for r in flagged if r[0] == "Psa 39:1"), None)
control_ne = next((r for r in no_evidence if r[0] == "Psa 39:1"), None)

print(f"READ-ONLY phrase-gloss UNDER-distribution audit -> {DB}")
print(f"  function-word set: {len(FUNC):,} (LSJ ∪ override)")
print(f"  FLAGGED (under-distribution class): {buckets['FLAGGED']:6,}")
print(f"  NO-EVIDENCE (blank neighbour, def-miss): {buckets['NO-EVIDENCE']:6,}")
print()
if control:
    print("  CONTROL Psa 39:1: FIRED  ✓  -> the zero/count is trustworthy")
    print(f"    {control[0]:10} | host {control[1]} | head {control[2]!r} | "
          f"gloss {control[3]!r} | {control[4]}")
elif control_ne:
    print("  CONTROL Psa 39:1: in NO-EVIDENCE, not FLAGGED  ⚠  -> tune the evidence test before trusting")
else:
    print("  CONTROL Psa 39:1: MISSED  ✗  -> DETECTOR IS BROKEN, do NOT trust the count")
print()

for name, rows in (("FLAGGED", flagged), ("NO-EVIDENCE", no_evidence)):
    show = rows if DUMP_ALL else rows[:20]
    if show:
        print(f"  --- {name} ({len(rows)}) — ref | host | head | gloss | orphan ---")
        for ref, sb, head, eng, det in show:
            print(f"      {ref:12} | {sb:7} | {head!r:12} | {(eng or '')!r:26} | {det}")
        print()
