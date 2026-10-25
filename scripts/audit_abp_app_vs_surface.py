#!/usr/bin/env python3
"""
audit_abp_app_vs_surface.py — READ-ONLY slot-by-slot diff of the official ABP app
(the witness) against our words table (the spine), abp_surface and
pn_greek_identity. Lane (a) of docs/handoffs/HANDOFF_abp_source_material.md.

INPUT: the TSV written by scripts/fetch_abp_app.py
  (book, chapter, verse, slot_index, strongs, greek, english — app book names).

ALIGNMENT (our words rows are the spine; position order within each verse):
  1. Each app slot is EXPANDED to one sub-slot per Strong's part ("2036-*" ->
     2036, *), because our build makes one row per Strong's tag. The Greek is
     split on whitespace when the word count equals the part count; otherwise the
     sub-slots carry no Greek ("compound-unsplit", counted, never guessed).
     An inline English note typed in the Greek font ("εποίησε - σερvεδ.") is cut
     off at " - " before splitting and counted.
  2. Verse with the SAME slot count -> paired by slot order (the asked-for
     alignment). A pair counts as ALIGNED only when its numbers agree:
       full  identical number (full dotted, e.g. 590.2 = 590.2)
       name  app '*' vs our proper-noun slot (is_pn, '*', or an H-number)
       base  same base, different dotted suffix (dotted-number audit rule: shown)
       pron  both in the pronoun family (our build retags ABP's raw G1473)
     Pairs whose numbers disagree are "same slot, different number" (patterns shown).
  3. Verse with a DIFFERENT count -> longest-common-sequence alignment under the
     same agreement test ("aligned by sequence", reported separately).

GREEK DIFF (aligned pairs whose app sub-slot has Greek), against each target that
has a value at that (verse_id, position), reported separately:
  surface   abp_surface.form
  identity  pn_greek_identity.greek_lemma (split by its source class — a header /
            dictionary-form name will differ from a printed inflected form BY DESIGN)
  lemma     the dictionary word (dotted_lexicon over lexicon) — ONLY where there is
            no abp_surface row, i.e. what the interlinear's Greek line falls back to
Cascade per compare: exact bytes -> same after NFC -> same after FOLD (marks off,
lower-case, final sigma, non-letters dropped incl. NBSP/space) -> same after fold
with the Latin look-alikes C->Χ Q->Θ (counted separately) -> mismatch.
Mismatches are split: app cell holds another Latin letter (census, never mapped) /
app cell carried an inline note / our value is a two-word NBSP value / other.

EDITION DRIFT (printed FIRST): per verse, app English joined vs our words.english
joined, both folded (digits, brackets, punctuation off, lower-case). "words differ"
= the bag of words differs (edition-drift candidate); "order only" = same words,
different order (a build reorder, not an edition change). Plus verses present on
one side only, and verses whose slot counts differ.

CONTROLS (hard stop, nothing else printed if one fails):
  C1 Gen 25:15 "Hadar," slot: app Greek 'Cολδάδ' with a LATIN C, aligned to our row,
     flagged by the Latin census.
  C2 1Ki 11:14 our position 7 aligned to the app's 'Αδάρ', and our surface/identity
     value there folds to Αδάρ.
  C3 NBSP detector fires on 1Ki 11:17 position 2 (pn_greek_identity value holds
     U+00A0) and the table-wide NBSP count is > 0.

READ-ONLY (sqlite opened mode=ro). Run on PA from ~/bible-db:
  PYTHONIOENCODING=utf-8 python3 scripts/audit_abp_app_vs_surface.py \\
      ~/bible-db/bible.db abp_app_html/abp_app_slots.tsv > ~/abp_app_audit.txt
Optional --dump FILE writes every compared slot (one TSV row each) for follow-up.
"""
import argparse
import csv
import os
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_abp_surface import _norm   # the production pronoun fold (-> '1473')

# app book name (chapters.js) -> our verses.book abbreviation
APP_TO_ABBREV = {
    "Genesis": "Gen", "Exodus": "Exo", "Leviticus": "Lev", "Numbers": "Num",
    "Deuteronomy": "Deu", "Joshua": "Jos", "Judges": "Jdg", "Ruth": "Rth",
    "1 Samuel": "1Sa", "2 Samuel": "2Sa", "1 Kings": "1Ki", "2 Kings": "2Ki",
    "1 Chronicles": "1Ch", "2 Chronicles": "2Ch", "Ezra": "Ezr", "Nehemiah": "Neh",
    "Esther": "Est", "Job": "Job", "Psalms": "Psa", "Proverbs": "Pro",
    "Ecclesiastes": "Ecc", "Song of Songs": "Son", "Isaiah": "Isa", "Jeremiah": "Jer",
    "Lamentations": "Lam", "Ezekiel": "Eze", "Daniel": "Dan", "Hosea": "Hos",
    "Joel": "Joe", "Amos": "Amo", "Obadiah": "Oba", "Jonah": "Jon", "Micah": "Mic",
    "Nahum": "Nah", "Habakkuk": "Hab", "Zephaniah": "Zep", "Haggai": "Hag",
    "Zechariah": "Zec", "Malachi": "Mal",
    "Matthew": "Mat", "Mark": "Mar", "Luke": "Luk", "John": "Joh", "Acts": "Act",
    "Romans": "Rom", "1 Corinthians": "1Co", "2 Corinthians": "2Co",
    "Galatians": "Gal", "Ephesians": "Eph", "Philippians": "Php", "Colossians": "Col",
    "1 Thessalonians": "1Th", "2 Thessalonians": "2Th", "1 Timothy": "1Ti",
    "2 Timothy": "2Ti", "Titus": "Tit", "Philemon": "Phm", "Hebrews": "Heb",
    "James": "Jas", "1 Peter": "1Pe", "2 Peter": "2Pe", "1 John": "1Jn",
    "2 John": "2Jn", "3 John": "3Jn", "Jude": "Jud", "Revelation": "Rev",
}
BOOK_ORDER = list(APP_TO_ABBREV.values())
NT = set(BOOK_ORDER[39:])

LATIN_MAP = {"C": "Χ", "Q": "Θ"}            # JP-specified; nothing else is mapped
NBSP = " "
NOTE_RE = re.compile(r"\s+-\s+(\S.*)$")      # "εποίησε - σερvεδ." inline note


# ── folding ──────────────────────────────────────────────────────────────────
def strip_marks(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "")
                   if not unicodedata.combining(c))


def fold(s, latin=False):
    """Compare-only key: marks off, lower-case, final sigma -> σ, every non-letter
    (space, NBSP, apostrophe, punctuation, digit) dropped. Latin letters are KEPT
    (lower-cased) so an unmapped Latin letter can never fake a Greek match."""
    if s is None:
        return None
    if latin:
        s = "".join(LATIN_MAP.get(c, c) for c in s)
    s = strip_marks(s).lower().replace("ς", "σ").replace("ϲ", "σ")
    return "".join(c for c in s if c.isalpha())


def latin_letters(s):
    return re.findall(r"[A-Za-z]", s or "")


def eng_words(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = re.sub(r"[\d\[\]]", " ", s)
    s = s.replace("—", " ").replace("--", " ")
    return [w for w in re.split(r"[^a-z']+", s.lower().replace("’", "'")) if w.strip("'")]


# ── app side ─────────────────────────────────────────────────────────────────
STRAY_NUM = Counter()                         # raw app number cell -> times cleaned


def clean_num(s):
    """App number cells sometimes carry stray characters ("> 2532", Oba 1:18).
    Keep only digits, '.', '*'; count every cell that needed it (reported)."""
    c = re.sub(r"[^0-9.*]", "", s)
    if c != s.strip():
        STRAY_NUM[s] += 1
    return c


def expand_app(strongs, greek):
    """One app slot -> [(strongs_part, greek_or_None, note, kind)]."""
    note = None
    g = greek or ""
    m = NOTE_RE.search(g)
    if m:
        note, g = m.group(1), g[:m.start()]
    parts = [clean_num(p) for p in strongs.split("-")] if strongs else [""]
    if len(parts) == 1:
        return [(parts[0].strip(), g.strip(), note, "single")]
    gws = g.split()
    if len(gws) == len(parts):
        return [(p.strip(), gws[i], note, "split") for i, p in enumerate(parts)]
    return [(p.strip(), None, note, "unsplit") for p in parts]


def load_app(tsv):
    """{(abbrev, ch, vs): [ {td, s, g, note, kind, eng} ... ]}, plus td-level English."""
    verses, eng, unknown = defaultdict(list), defaultdict(list), Counter()
    with open(tsv, encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        rows = sorted(rd, key=lambda r: (r["book"], int(r["chapter"]), int(r["verse"]),
                                         int(r["slot_index"])))
    for r in rows:
        ab = APP_TO_ABBREV.get(r["book"])
        if ab is None:
            unknown[r["book"]] += 1
            continue
        k = (ab, int(r["chapter"]), int(r["verse"]))
        eng[k].append(r["english"])
        for s, g, note, kind in expand_app(r["strongs"], r["greek"]):
            verses[k].append({"td": int(r["slot_index"]), "s": s, "g": g, "note": note,
                              "kind": kind, "graw": r["greek"], "eng": r["english"]})
    if unknown:
        sys.exit(f"FATAL: app book names with no mapping: {dict(unknown)}")
    return verses, eng


# ── agreement + alignment ────────────────────────────────────────────────────
def agree(app_s, our_s, our_pn):
    a = (app_s or "").strip()
    o = (our_s or "").strip()
    if o.startswith("G"):
        o = o[1:]
    if a == o:
        return "full"
    o_name = bool(our_pn) or o == "*" or o.startswith("H")
    if a == "*":
        return "name" if o_name else None
    if not a or not o or o == "*" or o.startswith("H"):
        return None
    ab, ob = a.split(".")[0], o.split(".")[0]
    if ab == ob:
        return "base"
    if _norm(ab) == "1473" and _norm(ob) == "1473":
        return "pron"
    return None


def lcs_pairs(app, ours):
    """Longest common subsequence under agree(); returns [(i_app, j_ours, how)]."""
    n, m = len(app), len(ours)
    ok = [[agree(app[i]["s"], ours[j]["s"], ours[j]["pn"]) for j in range(m)] for i in range(n)]
    L = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            L[i][j] = L[i + 1][j + 1] + 1 if ok[i][j] else max(L[i + 1][j], L[i][j + 1])
    out, i, j = [], 0, 0
    while i < n and j < m:
        if ok[i][j] and L[i][j] == L[i + 1][j + 1] + 1:
            out.append((i, j, ok[i][j]))
            i, j = i + 1, j + 1
        elif L[i + 1][j] >= L[i][j + 1]:
            i += 1
        else:
            j += 1
    return out


# ── greek compare ────────────────────────────────────────────────────────────
def classify(app_g, ours, note):
    """-> exact | nfc | fold | latin | mm_latin_other | mm_note | mm_ours_nbsp | mm_other"""
    if app_g == ours:
        return "exact"
    if unicodedata.normalize("NFC", app_g) == unicodedata.normalize("NFC", ours):
        return "nfc"
    if fold(app_g) == fold(ours):
        return "fold"
    if any(c in LATIN_MAP for c in app_g) and fold(app_g, latin=True) == fold(ours):
        return "latin"
    if any(c not in LATIN_MAP for c in latin_letters(app_g)):
        return "mm_latin_other"
    if NBSP in ours:
        return "mm_ours_nbsp"
    if note:
        return "mm_note"
    return "mm_other"


CLASSES = ["exact", "nfc", "fold", "latin", "mm_latin_other", "mm_ours_nbsp", "mm_note", "mm_other"]
CLASS_LABEL = {
    "exact": "exact bytes", "nfc": "same after NFC only", "fold": "same after fold",
    "latin": "same after fold + C->Χ/Q->Θ", "mm_latin_other": "MISMATCH: app has another Latin letter",
    "mm_ours_nbsp": "MISMATCH: our value is a two-word NBSP value",
    "mm_note": "MISMATCH: app cell carried an inline ' - ' note", "mm_other": "MISMATCH: other",
}


def pct(a, b):
    return f"{100.0 * a / b:6.2f}%" if b else "    — "


# ── database (read-only) ─────────────────────────────────────────────────────
def load_ours(con):
    """{(abbrev, ch, vs): {'vid':…, 'rows': [ {pos, s, pn, eng, sb} ... ]}}"""
    out = {}
    cur = con.execute(
        "SELECT v.id, v.book, v.chapter, v.verse, w.position, w.strongs, w.strongs_base, "
        "COALESCE(w.is_pn,0), COALESCE(w.english,'') "
        "FROM verses v JOIN words w ON w.verse_id = v.id ORDER BY v.id, w.position")
    for vid, book, ch, vs, pos, s, sb, pn, eng in cur:
        k = (book, ch, vs)
        if k not in out:
            out[k] = {"vid": vid, "rows": []}
        out[k]["rows"].append({"pos": pos, "s": (s or "").strip(), "sb": sb or "",
                               "pn": pn, "eng": eng})
    return out


def table_exists(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                       (name,)).fetchone() is not None


def main():
    ap = argparse.ArgumentParser(description="Read-only ABP app vs our tables diff.")
    ap.add_argument("db")
    ap.add_argument("tsv")
    ap.add_argument("--dump", help="write every compared slot to this TSV")
    args = ap.parse_args()

    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    con.execute("PRAGMA busy_timeout=30000")
    for t in ("verses", "words", "abp_surface", "pn_greek_identity", "lexicon"):
        if not table_exists(con, t):
            sys.exit(f"FATAL: table {t} missing")

    app, app_eng = load_app(args.tsv)
    ours = load_ours(con)
    surface = {(v, p): f for v, p, f in con.execute(
        "SELECT verse_id, position, form FROM abp_surface") if f}
    ident = {(v, p): (g, src) for v, p, g, src in con.execute(
        "SELECT verse_id, position, greek_lemma, source FROM pn_greek_identity") if g}
    lex = {sg: l for sg, l in con.execute("SELECT strongs_g, lemma FROM lexicon") if sg and l}
    dotted = {}
    if table_exists(con, "dotted_lexicon"):
        dotted = {s: l for s, l in con.execute("SELECT strongs, lemma FROM dotted_lexicon") if s and l}

    def dict_word(r):
        s = r["s"]
        if "." in s:
            d = dotted.get("G" + s.lstrip("G"))
            if d:
                return d
        return lex.get(r["sb"]) if r["sb"].startswith("G") else None

    # ── per-verse pass ───────────────────────────────────────────────────────
    B = defaultdict(Counter)          # book -> counters
    how_ct = Counter()
    slot_disagree = Counter()
    gres = {t: Counter() for t in ("surface", "identity", "lemma")}
    gres_src = defaultdict(Counter)   # identity source -> class counter
    mm_top = Counter()
    mm_ref = {}
    latin_census = defaultdict(Counter)   # letter -> class-of-slot counter
    latin_evidence = defaultdict(Counter)  # lower-case letter -> our letter at same index
    latin_examples = defaultdict(list)
    drift_samples = []
    aligned_at = {}                   # (abbrev,ch,vs,pos) -> (app sub-slot, how)
    CH = defaultdict(Counter)         # (book, chapter) -> our_slots / aligned
    dump = []

    keys = set(app) | set(ours)
    for k in sorted(keys, key=lambda k: (BOOK_ORDER.index(k[0]) if k[0] in BOOK_ORDER else 999, k[1], k[2])):
        b = k[0]
        a_slots, o = app.get(k), ours.get(k)
        if a_slots is None:
            B[b]["ours_only_verses"] += 1
            B[b]["our_slots"] += len(o["rows"])
            CH[(b, k[1])]["our_slots"] += len(o["rows"])
            continue
        if o is None:
            B[b]["app_only_verses"] += 1
            continue
        rows = o["rows"]
        B[b]["verses"] += 1
        B[b]["our_slots"] += len(rows)
        B[b]["app_subslots"] += len(a_slots)

        # edition drift: English
        aw = eng_words(" ".join(app_eng[k]))
        ow = eng_words(" ".join(r["eng"] for r in rows))
        if aw == ow:
            B[b]["eng_same"] += 1
        elif Counter(aw) == Counter(ow):
            B[b]["eng_order_only"] += 1
        else:
            B[b]["eng_words_differ"] += 1
            if len(drift_samples) < 400:
                drift_samples.append((k, Counter(ow) - Counter(aw), Counter(aw) - Counter(ow)))

        # alignment
        if len(a_slots) == len(rows):
            B[b]["count_equal_verses"] += 1
            pairs = []
            for i, r in enumerate(rows):
                h = agree(a_slots[i]["s"], r["s"], r["pn"])
                if h:
                    pairs.append((i, i, h))
                else:
                    B[b]["slot_disagree"] += 1
                    slot_disagree[(a_slots[i]["s"] or "''", r["s"] or "''")] += 1
            B[b]["aligned_pos"] += len(pairs)
        else:
            B[b]["count_diff_verses"] += 1
            pairs = lcs_pairs(a_slots, rows)
            B[b]["aligned_seq"] += len(pairs)
        CH[(b, k[1])]["our_slots"] += len(rows)
        CH[(b, k[1])]["aligned"] += len(pairs)

        for i, j, h in pairs:
            how_ct[h] += 1
            a, r = a_slots[i], rows[j]
            aligned_at[(k[0], k[1], k[2], r["pos"])] = (a, h)
            if a["kind"] == "unsplit":
                B[b]["unsplit"] += 1
                continue
            if a["note"]:
                B[b]["notes"] += 1
            if not a["g"]:
                B[b]["app_no_greek"] += 1
                continue
            vid, pos = o["vid"], r["pos"]
            targets = []
            if (vid, pos) in surface:
                targets.append(("surface", surface[(vid, pos)], None))
            if (vid, pos) in ident:
                g, src = ident[(vid, pos)]
                targets.append(("identity", g, src))
            if (vid, pos) not in surface:
                dw = dict_word(r)
                if dw:
                    targets.append(("lemma", dw, None))
            lat = latin_letters(a["g"])
            for t, val, src in targets:
                c = classify(a["g"], val, a["note"])
                gres[t][c] += 1
                if t == "identity":
                    gres_src[src][c] += 1
                if c.startswith("mm_") and c != "mm_latin_other":
                    key = (t, a["g"], val)
                    mm_top[key] += 1
                    mm_ref.setdefault(key, f"{k[0]} {k[1]}:{k[2]} pos {pos}")
                if lat and t in ("surface", "identity"):
                    fa, fo = fold(a["g"]), fold(val)
                    if len(fa) == len(fo):        # same length -> letter-for-letter evidence
                        for x, y in zip(fa, fo):
                            if "a" <= x <= "z":
                                latin_evidence[x][y] += 1
                dump.append((k[0], k[1], k[2], pos, r["s"], a["s"], h, a["g"], t, src or "", val, c))
            for L in set(lat):
                latin_census[L]["slots"] += 1
                if len(latin_examples[L]) < 6:
                    latin_examples[L].append(f"{k[0]} {k[1]}:{k[2]} {a['g']} ({a['eng']})")

    # ── CONTROLS ─────────────────────────────────────────────────────────────
    print("=" * 78)
    print("ABP APP vs OUR TABLES — read-only diff (app = witness, words = spine)")
    print("=" * 78)
    fails = []

    c1 = [a for a in app.get(("Gen", 25, 15), []) if a["eng"].startswith("Hadar")]
    hit = None
    if c1:
        for (bk, ch, vs, pos), (a, h) in aligned_at.items():
            if (bk, ch, vs) == ("Gen", 25, 15) and a is c1[0]:
                hit = (pos, h)
    ok1 = bool(c1) and c1[0]["g"] == "Cολδάδ" and c1[0]["g"][0] == "C" and hit is not None \
        and latin_census["C"]["slots"] > 0
    print(f"C1 Gen 25:15 Hadar slot: app greek={c1[0]['g'] if c1 else None!r} "
          f"(first char U+{ord(c1[0]['g'][0]):04X})" if c1 and c1[0]['g'] else "C1 Gen 25:15: slot missing",
          f"aligned to our pos {hit[0]} ({hit[1]})" if hit else "NOT aligned",
          f"Latin-C slots corpus-wide={latin_census['C']['slots']}", "->", "PASS" if ok1 else "FAIL")
    if ok1:
        vid = ours[("Gen", 25, 15)]["vid"]
        for t, d in (("surface", surface), ("identity", ident)):
            v = d.get((vid, hit[0]))
            v = v[0] if isinstance(v, tuple) else v
            if v:
                print(f"     our {t}={v!r} -> {classify(c1[0]['g'], v, None)}")
    else:
        fails.append("C1")

    o14 = ours.get(("1Ki", 11, 14))
    a14 = aligned_at.get(("1Ki", 11, 14, 7))
    vals = []
    if o14:
        vid = o14["vid"]
        if (vid, 7) in surface:
            vals.append(("surface", surface[(vid, 7)]))
        if (vid, 7) in ident:
            vals.append(("identity", ident[(vid, 7)][0]))
    ok2 = a14 is not None and a14[0]["g"] == "Αδάρ" and bool(vals) and \
        all(fold(v) == fold("Αδάρ") for _, v in vals)
    print(f"C2 1Ki 11:14 our pos 7: app={a14[0]['g'] if a14 else None!r} "
          f"({a14[1] if a14 else 'NOT aligned'}); ours={vals} -> {'PASS' if ok2 else 'FAIL'}")
    if not ok2:
        fails.append("C2")

    o17 = ours.get(("1Ki", 11, 17))
    v17 = ident.get((o17["vid"], 2)) if o17 else None
    n_nbsp = con.execute("SELECT count(*) FROM pn_greek_identity "
                         "WHERE greek_lemma LIKE '%'||char(160)||'%'").fetchone()[0]
    ok3 = bool(v17) and NBSP in v17[0] and n_nbsp > 0
    a17 = aligned_at.get(("1Ki", 11, 17, 2))
    print(f"C3 NBSP detector: 1Ki 11:17 pos 2 identity={v17[0] if v17 else None!r} "
          f"codepoints={[f'U+{ord(c):04X}' for c in v17[0]] if v17 else None}; "
          f"table-wide NBSP rows={n_nbsp}; app there={a17[0]['g'] if a17 else None!r} "
          f"-> {'PASS' if ok3 else 'FAIL'}")
    if not ok3:
        fails.append("C3")
    if fails:
        print(f"\nCONTROL FAILURE ({', '.join(fails)}) — the numbers are not trusted; stopping.")
        sys.exit(1)
    print("controls PASS\n")

    # ── 1. EDITION DRIFT ─────────────────────────────────────────────────────
    T = Counter()
    for b in B:
        T.update(B[b])
    print("1. EDITION DRIFT  (English per verse, folded: digits/brackets/punctuation off)")
    print(f"   verses on both sides {T['verses']}  · app-only {T['app_only_verses']}"
          f"  · ours-only {T['ours_only_verses']}")
    print(f"   English same {T['eng_same']} ({pct(T['eng_same'], T['verses']).strip()})"
          f"  · order-only {T['eng_order_only']}  · WORDS DIFFER {T['eng_words_differ']}"
          f" ({pct(T['eng_words_differ'], T['verses']).strip()})")
    print(f"   slot-count differs (after compound split): {T['count_diff_verses']} verses")
    for lbl, sel in (("OT", lambda b: b not in NT), ("NT", lambda b: b in NT)):
        S = Counter()
        for b in B:
            if sel(b):
                S.update(B[b])
        print(f"   {lbl}: verses {S['verses']}  words-differ {S['eng_words_differ']} "
              f"({pct(S['eng_words_differ'], S['verses']).strip()})  order-only {S['eng_order_only']}"
              f"  count-differs {S['count_diff_verses']}  app-only {S['app_only_verses']}"
              f"  ours-only {S['ours_only_verses']}")
    print(f"\n   {'book':5} {'verses':>6} {'differ':>7} {'%':>8} {'order':>6} {'cnt≠':>5}"
          f" {'app-only':>8} {'ours-only':>9}")
    for b in BOOK_ORDER:
        c = B.get(b)
        if not c:
            print(f"   {b:5} (absent on both sides)")
            continue
        print(f"   {b:5} {c['verses']:6} {c['eng_words_differ']:7} "
              f"{pct(c['eng_words_differ'], c['verses'])} {c['eng_order_only']:6}"
              f" {c['count_diff_verses']:5} {c['app_only_verses']:8} {c['ours_only_verses']:9}")
    only_app = sorted(k for k in app if k not in ours)
    only_ours = sorted(k for k in ours if k not in app)
    if only_app:
        print(f"   app-only verses (first 30): " + ", ".join(f"{b} {c}:{v}" for b, c, v in only_app[:30]))
    if only_ours:
        print(f"   ours-only verses (first 30): " + ", ".join(f"{b} {c}:{v}" for b, c, v in only_ours[:30]))
    # versification probe: chapters aligning under 50% by verse number, retried
    # with the app's verse numbers shifted by one (Psalm titles = our verse 0).
    # Diagnostic only — the main numbers above/below use the plain verse key.
    weak = sorted((c for c, v in CH.items() if v["our_slots"] and v["aligned"] < 0.5 * v["our_slots"]),
                  key=lambda c: (BOOK_ORDER.index(c[0]) if c[0] in BOOK_ORDER else 999, c[1]))
    print(f"   VERSIFICATION PROBE: chapters aligning < 50% by verse number: {len(weak)}")
    by_shift = Counter()
    lines = []
    ours_by_ch = defaultdict(list)
    for (bb, cc, vv), o in ours.items():
        ours_by_ch[(bb, cc)].append((vv, o))
    for b, ch in weak:
        best = (CH[(b, ch)]["aligned"], 0)
        for s in (-1, 1):
            n = 0
            for vv, o in ours_by_ch[(b, ch)]:
                if (b, ch, vv + s) in app:
                    n += len(lcs_pairs(app[(b, ch, vv + s)], o["rows"]))
            best = max(best, (n, s))
        by_shift[best[1]] += 1
        lines.append(f"{b} {ch}: {pct(CH[(b, ch)]['aligned'], CH[(b, ch)]['our_slots']).strip()}"
                     f" -> app v{best[1]:+d}: {pct(best[0], CH[(b, ch)]['our_slots']).strip()}")
    if weak:
        print(f"     best shift: app verse = ours {by_shift[1]}× +1 · {by_shift[-1]}× -1 · "
              f"{by_shift[0]}× no shift helps")
        for i in range(0, min(len(lines), 60), 3):
            print("     " + "   ".join(f"{x:34}" for x in lines[i:i + 3]))
        if len(lines) > 60:
            print(f"     … {len(lines) - 60} more")
    print("   words-differ samples (first 25; '-' only in ours, '+' only in app):")
    for (b, c, v), mine, theirs in drift_samples[:25]:
        print(f"     {b} {c}:{v}  -{' '.join(sorted(mine.elements()))[:70]}"
              f"  +{' '.join(sorted(theirs.elements()))[:70]}")

    # ── 2. ALIGNMENT ─────────────────────────────────────────────────────────
    print("\n2. ALIGNMENT  (our slots paired with an app sub-slot whose number agrees)")
    al = T["aligned_pos"] + T["aligned_seq"]
    print(f"   our slots {T['our_slots']}  · app sub-slots {T['app_subslots']}"
          f"  · ALIGNED {al} ({pct(al, T['our_slots']).strip()})"
          f"  [by slot order {T['aligned_pos']} · by sequence {T['aligned_seq']}]")
    print(f"   agreement kind: " + "  ".join(f"{h}={how_ct[h]}" for h in ("full", "name", "base", "pron")))
    print(f"   same slot, different number: {T['slot_disagree']}  · compound-unsplit sub-slots "
          f"{T['unsplit']}  · aligned with no app Greek {T['app_no_greek']}  · inline notes {T['notes']}")
    print(f"   app number cells with stray characters (cleaned before compare): "
          f"{sum(STRAY_NUM.values())}" + (f"  e.g. {', '.join(repr(x) for x, _ in STRAY_NUM.most_common(5))}"
                                          if STRAY_NUM else ""))
    print(f"\n   {'book':5} {'ourSlots':>8} {'aligned':>8} {'%':>8} {'cnt=vs':>7} {'slot≠':>6}")
    for b in BOOK_ORDER:
        c = B.get(b)
        if not c:
            continue
        a_ = c["aligned_pos"] + c["aligned_seq"]
        print(f"   {b:5} {c['our_slots']:8} {a_:8} {pct(a_, c['our_slots'])}"
              f" {pct(c['count_equal_verses'], c['verses'])[:-1]:>7} {c['slot_disagree']:6}")
    print("   top same-slot number disagreements (app -> ours):")
    for (a_, o_), n in slot_disagree.most_common(20):
        print(f"     {n:6}  app {a_:>10}  ours {o_}")

    # ── 3. GREEK DIFF ────────────────────────────────────────────────────────
    print("\n3. GREEK DIFF  (aligned slots with app Greek; each target separately)")
    for t, lbl in (("surface", "abp_surface.form"),
                   ("identity", "pn_greek_identity.greek_lemma"),
                   ("lemma", "dictionary word (no abp_surface row only)")):
        g = gres[t]
        n = sum(g.values())
        ex = g["exact"]
        aft = ex + g["nfc"] + g["fold"]
        print(f"   {lbl}: compared {n}")
        print(f"     exact {pct(ex, n)}   match-after-fold {pct(aft, n)}"
              f"   + Latin C/Q {g['latin']} ({pct(g['latin'], n).strip()})")
        for c in CLASSES:
            print(f"       {CLASS_LABEL[c]:46} {g[c]:8}")
    print("   (dictionary-word rows: a mismatch there = the app prints a form our interlinear\n"
          "    does not show — no abp_surface row — or drift; the article 'ὁ' family dominates)")
    print("   identity split by source class (match-after-fold incl. Latin / compared):")
    for src, g in sorted(gres_src.items()):
        n = sum(g.values())
        m = g["exact"] + g["nfc"] + g["fold"] + g["latin"]
        print(f"     {src:12} {m:7}/{n:<7} {pct(m, n)}   ours-NBSP {g['mm_ours_nbsp']}"
              f"   other-Latin {g['mm_latin_other']}")

    # ── 4. LATIN LETTERS ─────────────────────────────────────────────────────
    print("\n4. LATIN LETTERS IN APP GREEK  (aligned slots; C->Χ, Q->Θ mapped, all others NOT)")
    for L in sorted(latin_census, key=lambda L: -latin_census[L]["slots"]):
        ev = latin_evidence.get(L.lower(), Counter())
        evs = ", ".join(f"{y}×{n}" for y, n in ev.most_common(4)) or "—"
        print(f"   {L}: {latin_census[L]['slots']:6} slots   our letter at that spot: {evs}")
        for e in latin_examples[L][:3]:
            print(f"        e.g. {e}")

    # ── 5. TOP 50 REMAINING MISMATCHES ───────────────────────────────────────
    print("\n5. TOP 50 REMAINING MISMATCHES by frequency  (other-Latin cells excluded — see 4)")
    for (t, ag, ov), n in mm_top.most_common(50):
        print(f"   {n:6}  {t:8}  app {ag!r:28} ours {ov!r:28} e.g. {mm_ref[(t, ag, ov)]}")
    print(f"   distinct mismatch pairs: {len(mm_top)}  · slots: {sum(mm_top.values())}")

    if args.dump:
        with open(args.dump, "w", encoding="utf-8", newline="\n") as f:
            f.write("book\tchapter\tverse\tposition\tour_strongs\tapp_strongs\tagree\t"
                    "app_greek\ttarget\tsource\tour_value\tclass\n")
            for r in dump:
                f.write("\t".join(str(x) for x in r) + "\n")
        print(f"\nwrote {len(dump)} compared slots -> {args.dump}")


if __name__ == "__main__":
    main()
