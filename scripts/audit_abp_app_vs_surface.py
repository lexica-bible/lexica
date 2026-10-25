#!/usr/bin/env python3
"""
audit_abp_app_vs_surface.py — READ-ONLY slot-by-slot diff of the official ABP app
(the witness) against our words table (the spine), abp_surface and
pn_greek_identity. Lane (a) of docs/handoffs/HANDOFF_abp_source_material.md.
v2 (2026-10-24, JP ruling on the v1 numbers): defect map, Psalms shift pass,
swapped-order group, missing-printed-form list, OT/NT headline.

INPUT: the TSV written by scripts/fetch_abp_app.py
  (book, chapter, verse, slot_index, strongs, greek, english — app book names).

VERSE PAIRING: plain (book, chapter, verse) key, EXCEPT Psalms chapters where our
side has a verse 0 (the title): there our verse v pairs with the app's verse v+1
(the app numbers the title as verse 1). Psalms are also reported on their own lines.
Other chapters with verses on one side only (Pro 16/24, Jer 10, Hab 3 …) keep the
plain key and are listed in the versification section with the best whole-chapter
shift (-3..+3) and, per one-sided verse, its best-matching verse on the other side.

ALIGNMENT within a verse (our words rows are the spine; position order):
  1. Each app slot is EXPANDED to one sub-slot per Strong's part ("2036-*" ->
     2036, *). The Greek is split on whitespace when the word count equals the part
     count; otherwise the sub-slots carry no Greek ("compound-unsplit", counted).
     An inline English note in the Greek cell ("εποίησε - σερvεδ.") is cut at " - ".
  2. Same slot count -> paired by slot order. ALIGNED only when numbers agree:
       full  identical number (full dotted)   name  app '*' vs our proper-noun slot
       base  same base, other dotted suffix   pron  both in the pronoun family
  3. Different count -> longest-common-sequence alignment, same agreement test.
  4. SWAPPED ORDER: slots left over by 2/3 are matched to an agreeing leftover slot
     on the other side, nearest first. In a SAME-count verse that is a swap — JP
     ruling 2026-10-24: our build's split-flip reorder, NOT a mismatch; reported as
     its own group (with the places moved); per-row cause not checked. In a
     count-DIFFERS verse the same match is reported apart as "out-of-sequence"
     (often a repeated word) and is not covered by the ruling. Both take part in
     the Greek diff (same word, same number).
     What is still left in a same-count verse = "same slot, different number".

GREEK DIFF (aligned pairs with app Greek), per target, reported separately:
  surface   abp_surface.form            (the HEADLINE target)
  identity  pn_greek_identity.greek_lemma (header/dictionary name forms differ by design)
  lemma     dictionary word (dotted_lexicon over lexicon), ONLY where there is no
            abp_surface row = what the interlinear shows instead of a printed form
Cascade: exact bytes -> same after NFC -> same after accents off (fold) -> same after
the DEFECT MAP -> mismatch.
DEFECT MAP (JP ruling 2026-10-24; app font defects, evidence = our letter at the same
spot in v1): C->Χ Q->Θ H->Η O->Ο U->Υ R->Π П(Cyrillic U+041F)->Π '+'->ϊ.
Each letter is counted on its own line. Cells holding any lower-case Latin letter are
ENGLISH TYPED IN THE GREEK FONT ("τηε λιvινγ") — excluded from the Greek diff and
counted separately. Any other non-Greek letter is "unmapped foreign letter".

MISSING PRINTED FORM: lemma-target mismatches = slots where abp_surface has no row and
the app prints a form that is not the dictionary word (είπε vs ἔπω). Counted on its
own line, broken down by word type (words.morph) and written to a TSV
(--missing-out) — the list the Analytical Lexicon lane will fill.

EDITION DRIFT: per paired verse, app English vs our words.english, both folded
(digits, brackets, punctuation off). "words differ" = the bag of words differs;
"order only" = same words, different order.

CONTROLS (hard stop if one fails):
  C1 Gen 25:15 "Hadar," slot: app 'Cολδάδ' (LATIN C), aligned, mapped by the defect map.
  C2 1Ki 11:14 our position 7 aligned to the app's 'Αδάρ'; our surface/identity fold to it.
  C3 NBSP detector catches all 27 pinned compound names
     (docs/tickets/compound_names_allowlist.tsv, byte-exact) — SQL char(160) AND script.
  C4 Psalms shift: Psa 3 (our verse 0 = app verse 1) aligns >= 90% under the shift.

READ-ONLY (sqlite opened mode=ro). Run on PA from ~/bible-db:
  PYTHONIOENCODING=utf-8 python3 scripts/audit_abp_app_vs_surface.py \\
      ~/bible-db/bible.db abp_app_html/abp_app_slots.tsv > ~/abp_app_audit.txt
--missing-out (default abp_app_html/missing_printed_forms.tsv) · --dump FILE optional.
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

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)

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

# App font defects -> the Greek letter they stand for (JP ruling 2026-10-24).
DEFECT_MAP = {"C": "Χ", "Q": "Θ", "H": "Η", "O": "Ο", "U": "Υ", "R": "Π",
              "П": "Π", "+": "ϊ"}
DEFECT_LABEL = {"C": "C  -> Χ", "Q": "Q  -> Θ", "H": "H  -> Η", "O": "O  -> Ο",
                "U": "U  -> Υ", "R": "R  -> Π", "П": "П (Cyrillic) -> Π", "+": "+  -> ϊ"}
NBSP = " "
NOTE_RE = re.compile(r"\s+-\s+(\S.*)$")      # "εποίησε - σερvεδ." inline note
ALLOWLIST = os.path.join(REPO, "docs", "tickets", "compound_names_allowlist.tsv")


def rank(b):
    return BOOK_ORDER.index(b) if b in BOOK_ORDER else 999


def region(b):
    return "NT" if b in NT else "OT"


# ── folding ──────────────────────────────────────────────────────────────────
def strip_marks(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "")
                   if not unicodedata.combining(c))


def fold(s, mapped=False):
    """Compare-only key: (defect map), marks off, lower-case, final sigma -> σ,
    every non-letter dropped (space, NBSP, apostrophe, '+', digits). Non-Greek
    letters are KEPT so an unmapped one can never fake a Greek match."""
    if s is None:
        return None
    if mapped:
        s = "".join(DEFECT_MAP.get(c, c) for c in s)
    s = strip_marks(s).lower().replace("ς", "σ").replace("ϲ", "σ")
    return "".join(c for c in s if c.isalpha())


def is_greek_letter(c):
    return "Ͱ" <= c <= "Ͽ" or "ἀ" <= c <= "῿"


def english_font(g):
    """Lower-case Latin anywhere = English typed in the Greek font."""
    return bool(re.search(r"[a-z]", g or ""))


def foreign_unmapped(g):
    return sorted({c for c in (g or "") if c.isalpha() and not is_greek_letter(c)
                   and c not in DEFECT_MAP})


def eng_words(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = re.sub(r"[\d\[\]]", " ", s)
    s = s.replace("—", " ").replace("--", " ")
    return [w for w in re.split(r"[^a-z']+", s.lower().replace("’", "'")) if w.strip("'")]


# ── word type from words.morph (labels only; mirrors decodeMorph's code tables in
#    static/src/00-core.jsx: CATSS "V.AAI3S" (OT), Robinson "V-AAI-3S" (NT)) ────────
_PRON_CATSS = {"RP", "RD", "RR", "RI", "RX"}
_PRON_ROB = {"P", "R", "D", "K", "I", "X", "Q", "F", "S", "C"}


def word_type(morph, is_pn):
    if is_pn:
        return "name"
    m = (morph or "").strip()
    if not m:
        return "no morph"
    if "." in m:
        pos = m.split(".", 1)[0]
        if pos == "V":
            return "verb"
        if pos == "RA":
            return "article"
        if pos in _PRON_CATSS:
            return "pronoun"
    elif "-" in m:
        pos = m.split("-", 1)[0]
        if pos == "V":
            return "verb"
        if pos == "T":
            return "article"
        if pos in _PRON_ROB:
            return "pronoun"
    else:
        pos = m
    return {"N": "noun", "A": "adjective"}.get(pos, "other")


# ── app side ─────────────────────────────────────────────────────────────────
STRAY_NUM = Counter()


def clean_num(s):
    """App number cells sometimes carry stray characters ("> 2532", Oba 1:18)."""
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
                              "kind": kind, "eng": r["english"]})
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


def align_verse(a_slots, rows):
    """-> (pairs [(i, j, how)], same_count, leftover_app_idx, leftover_our_idx).
    how is full/name/base/pron, or 'reorder:<distance>' for swapped-order slots."""
    same = len(a_slots) == len(rows)
    if same:
        pairs = []
        for i, r in enumerate(rows):
            h = agree(a_slots[i]["s"], r["s"], r["pn"])
            if h:
                pairs.append((i, i, h))
    else:
        pairs = lcs_pairs(a_slots, rows)
    used_a = {p[0] for p in pairs}
    used_o = {p[1] for p in pairs}
    left_a = [i for i in range(len(a_slots)) if i not in used_a]
    for j in [j for j in range(len(rows)) if j not in used_o]:
        best = None
        for i in left_a:
            if agree(a_slots[i]["s"], rows[j]["s"], rows[j]["pn"]):
                if best is None or abs(i - j) < abs(best - j):
                    best = i
        if best is not None:
            pairs.append((best, j, f"reorder:{abs(best - j)}"))
            left_a.remove(best)
            used_o.add(j)
    left_o = [j for j in range(len(rows)) if j not in used_o]
    return pairs, same, left_a, left_o


# ── greek compare ────────────────────────────────────────────────────────────
def classify(app_g, ours, note):
    """-> (class, defect letters used). English-font cells never reach here."""
    if app_g == ours:
        return "exact", ()
    if unicodedata.normalize("NFC", app_g) == unicodedata.normalize("NFC", ours):
        return "nfc", ()
    if fold(app_g) == fold(ours):
        return "fold", ()
    used = tuple(sorted({c for c in app_g if c in DEFECT_MAP}))
    if used and fold(app_g, mapped=True) == fold(ours):
        return "defect", used
    if foreign_unmapped(app_g):
        return "mm_foreign", used
    if used:
        return "mm_defect_left", used
    if NBSP in ours:
        return "mm_ours_nbsp", ()
    if note:
        return "mm_note", ()
    return "mm_other", ()


CLASSES = ["exact", "nfc", "fold", "defect", "mm_foreign", "mm_defect_left",
           "mm_ours_nbsp", "mm_note", "mm_other"]
CLASS_LABEL = {
    "exact": "exact bytes", "nfc": "same after NFC only", "fold": "same after accents off",
    "defect": "same after the defect map",
    "mm_foreign": "MISMATCH: app has an unmapped foreign letter",
    "mm_defect_left": "MISMATCH: defect letter mapped, still differs",
    "mm_ours_nbsp": "MISMATCH: our value is a two-word NBSP value",
    "mm_note": "MISMATCH: app cell carried an inline ' - ' note", "mm_other": "MISMATCH: other",
}


def pct(a, b):
    return f"{100.0 * a / b:6.2f}%" if b else "    — "


def ladder(g):
    """(n, exact, after accents, after defect map) for a class counter."""
    n = sum(g.values())
    ex = g["exact"]
    acc = ex + g["nfc"] + g["fold"]
    return n, ex, acc, acc + g["defect"]


# ── database (read-only) ─────────────────────────────────────────────────────
def load_ours(con):
    out = {}
    cur = con.execute(
        "SELECT v.id, v.book, v.chapter, v.verse, w.position, w.strongs, w.strongs_base, "
        "COALESCE(w.is_pn,0), COALESCE(w.english,''), COALESCE(w.morph,'') "
        "FROM verses v JOIN words w ON w.verse_id = v.id ORDER BY v.id, w.position")
    for vid, book, ch, vs, pos, s, sb, pn, eng, morph in cur:
        k = (book, ch, vs)
        if k not in out:
            out[k] = {"vid": vid, "rows": []}
        out[k]["rows"].append({"pos": pos, "s": (s or "").strip(), "sb": sb or "",
                               "pn": pn, "eng": eng, "morph": morph})
    return out


def table_exists(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                       (name,)).fetchone() is not None


def main():
    ap = argparse.ArgumentParser(description="Read-only ABP app vs our tables diff (v2).")
    ap.add_argument("db")
    ap.add_argument("tsv")
    ap.add_argument("--missing-out", default=os.path.join(REPO, "abp_app_html",
                                                          "missing_printed_forms.tsv"))
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

    # ── verse pairing (Psalms title shift) ───────────────────────────────────
    psa_shift = {(b, ch) for (b, ch, v) in ours if b == "Psa" and v == 0}
    pair_of = {}
    for k in ours:
        b, ch, v = k
        pair_of[k] = (b, ch, v + 1) if (b, ch) in psa_shift else k
    used_app = {pair_of[k] for k in ours if pair_of[k] in app}

    # ── per-verse pass ───────────────────────────────────────────────────────
    B = defaultdict(Counter)                  # book -> counters
    CH = defaultdict(Counter)                 # (book, ch) -> our_slots / aligned
    how_ct = Counter()
    reorder_dist = Counter()
    slot_disagree = Counter()
    G = defaultdict(Counter)                  # (region, target) -> class counter
    gsrc = defaultdict(Counter)               # identity source -> class counter
    defect_ok, defect_left = Counter(), Counter()
    defect_ex = defaultdict(list)
    foreign_ct, foreign_ex = Counter(), defaultdict(list)
    engfont_ex = []
    mm_top, mm_ref = Counter(), {}
    missing, miss_type, miss_top, miss_ref = [], Counter(), Counter(), {}
    drift_samples = []
    aligned_at = {}
    dump = []

    for k in sorted(ours, key=lambda k: (rank(k[0]), k[1], k[2])):
        b = k[0]
        o = ours[k]
        rows = o["rows"]
        ka = pair_of[k]
        a_slots = app.get(ka)
        B[b]["our_slots"] += len(rows)
        CH[(b, k[1])]["our_slots"] += len(rows)
        if a_slots is None:
            B[b]["ours_only_verses"] += 1
            B[b]["ours_only_slots"] += len(rows)
            continue
        B[b]["verses"] += 1
        B[b]["app_subslots"] += len(a_slots)
        if ka != k:
            B[b]["shifted_verses"] += 1

        aw = eng_words(" ".join(app_eng[ka]))
        ow = eng_words(" ".join(r["eng"] for r in rows))
        if aw == ow:
            B[b]["eng_same"] += 1
        elif Counter(aw) == Counter(ow):
            B[b]["eng_order_only"] += 1
        else:
            B[b]["eng_words_differ"] += 1
            if len(drift_samples) < 400:
                drift_samples.append((k, Counter(ow) - Counter(aw), Counter(aw) - Counter(ow)))

        pairs, same, left_a, left_o = align_verse(a_slots, rows)
        B[b]["count_equal_verses" if same else "count_diff_verses"] += 1
        if same:
            for j in left_o:
                B[b]["slot_disagree"] += 1
                slot_disagree[(a_slots[j]["s"] or "''", rows[j]["s"] or "''")] += 1
        B[b]["our_unaligned"] += len(left_o)
        CH[(b, k[1])]["aligned"] += len(pairs)

        for i, j, h in pairs:
            a, r = a_slots[i], rows[j]
            if h.startswith("reorder") and same:
                B[b]["reorder"] += 1
                reorder_dist[int(h.split(":")[1])] += 1
                how_ct["reorder"] += 1
            elif h.startswith("reorder"):
                B[b]["oos"] += 1
                how_ct["out-of-seq"] += 1
            else:
                B[b]["aligned_pos" if same else "aligned_seq"] += 1
                how_ct[h] += 1
            aligned_at[(k[0], k[1], k[2], r["pos"])] = (a, h)
            if a["kind"] == "unsplit":
                B[b]["unsplit"] += 1
                continue
            if a["note"]:
                B[b]["notes"] += 1
            if not a["g"]:
                B[b]["app_no_greek"] += 1
                continue
            if english_font(a["g"]):
                B[b]["english_font"] += 1
                if len(engfont_ex) < 12:
                    engfont_ex.append(f"{b} {k[1]}:{k[2]} {a['g']!r} ({a['eng']})")
                continue
            for c in foreign_unmapped(a["g"]):
                foreign_ct[c] += 1
                if len(foreign_ex[c]) < 4:
                    foreign_ex[c].append(f"{b} {k[1]}:{k[2]} {a['g']!r} ({a['eng']})")
            vid, pos = o["vid"], r["pos"]
            targets = []
            if (vid, pos) in surface:
                targets.append(("surface", surface[(vid, pos)], None))
            if (vid, pos) in ident:
                g_, src = ident[(vid, pos)]
                targets.append(("identity", g_, src))
            if (vid, pos) not in surface:
                dw = dict_word(r)
                if dw:
                    targets.append(("lemma", dw, None))
            for t, val, src in targets:
                c, used = classify(a["g"], val, a["note"])
                G[(region(b), t)][c] += 1
                if b == "Psa":
                    G[("PSA", t)][c] += 1
                if t == "identity":
                    gsrc[src][c] += 1
                if t in ("surface", "identity"):
                    for L in used:
                        if c == "defect":
                            defect_ok[L] += 1
                            if len(defect_ex[L]) < 2:
                                defect_ex[L].append(f"{b} {k[1]}:{k[2]} {a['g']} = {val}")
                        else:
                            defect_left[L] += 1
                if c.startswith("mm_") and t == "lemma":
                    wt = word_type(r["morph"], r["pn"])
                    miss_type[wt] += 1
                    key = (a["g"], val)
                    miss_top[key] += 1
                    miss_ref.setdefault(key, f"{b} {k[1]}:{k[2]} pos {pos}")
                    missing.append((b, k[1], k[2], pos, r["s"], wt, r["morph"], val,
                                    a["g"], a["eng"], c))
                elif c.startswith("mm_") and c != "mm_foreign":
                    key = (t, a["g"], val)
                    mm_top[key] += 1
                    mm_ref.setdefault(key, f"{b} {k[1]}:{k[2]} pos {pos}")
                if args.dump:
                    dump.append((b, k[1], k[2], pos, r["s"], a["s"], h, a["g"], t,
                                 src or "", val, c))

    for ka in app:
        if ka not in used_app:
            B[ka[0]]["app_only_verses"] += 1

    # ── CONTROLS ─────────────────────────────────────────────────────────────
    print("=" * 78)
    print("ABP APP vs OUR TABLES — read-only diff v2 (app = witness, words = spine)")
    print("=" * 78)
    fails = []

    c1 = [a for a in app.get(("Gen", 25, 15), []) if a["eng"].startswith("Hadar")]
    hit = None
    if c1:
        for (bk, ch, vs, pos), (a, h) in aligned_at.items():
            if (bk, ch, vs) == ("Gen", 25, 15) and a is c1[0]:
                hit = (pos, h)
    ok1 = bool(c1) and c1[0]["g"] == "Cολδάδ" and hit is not None and defect_ok["C"] > 0
    res1 = []
    if ok1:
        vid = ours[("Gen", 25, 15)]["vid"]
        for t, d in (("surface", surface), ("identity", ident)):
            v = d.get((vid, hit[0]))
            v = v[0] if isinstance(v, tuple) else v
            if v:
                res1.append(f"{t}={v!r} -> {classify(c1[0]['g'], v, None)[0]}")
        ok1 = bool(res1) and all(x.endswith("-> defect") for x in res1)
    print(f"C1 Gen 25:15 Hadar: app={c1[0]['g'] if c1 else None!r} "
          f"{'aligned to our pos %d' % hit[0] if hit else 'NOT aligned'}; "
          f"{'; '.join(res1) or 'no our value'} -> {'PASS' if ok1 else 'FAIL'}")
    if not ok1:
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

    allow = []
    with open(ALLOWLIST, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or line.startswith("hex\t") or not line.strip():
                continue
            hx, _g, bk, ch, vs, en = line.rstrip("\n").split("\t")[:6]
            allow.append((bytes.fromhex(hx).decode("utf-8"), bk, int(ch), int(vs), en))
    sql_nbsp = con.execute(
        "SELECT v.book, v.chapter, v.verse, p.position, p.greek_lemma "
        "FROM pn_greek_identity p JOIN verses v ON v.id = p.verse_id "
        "WHERE p.greek_lemma LIKE '%'||char(160)||'%'").fetchall()
    live = {(bk, ch, vs, g) for bk, ch, vs, pos, g in sql_nbsp}
    missing_pin = [a for a in allow if (a[1], a[2], a[3], a[0]) not in live]
    py_hits = sum(1 for a in allow if (a[1], a[2], a[3], a[0]) in live and NBSP in a[0])
    pinned = {(a[1], a[2], a[3], a[0]) for a in allow}
    ok3 = len(allow) == 27 and not missing_pin and py_hits == 27
    print(f"C3 NBSP detector on the {len(allow)} pinned compound names: SQL "
          f"{len(allow) - len(missing_pin)}/{len(allow)} · script {py_hits}/{len(allow)} · "
          f"table-wide {len(sql_nbsp)} -> {'PASS' if ok3 else 'FAIL'}")
    for a in missing_pin:
        print(f"     MISSING pinned: {a[1]} {a[2]}:{a[3]} {a[0]!r} ({a[4]})")
    for bk, ch, vs, pos, g in sql_nbsp:
        if (bk, ch, vs, g) not in pinned:
            print(f"     NBSP row beyond the pinned list: {bk} {ch}:{vs} pos {pos} {g!r}")
    if not ok3:
        fails.append("C3")

    p3 = CH.get(("Psa", 3), Counter())
    ok4 = ("Psa", 3) in psa_shift and p3["our_slots"] and p3["aligned"] >= 0.9 * p3["our_slots"]
    print(f"C4 Psalms shift: Psa 3 shifted={('Psa', 3) in psa_shift} aligned "
          f"{pct(p3['aligned'], p3['our_slots']).strip()} -> {'PASS' if ok4 else 'FAIL'}")
    if not ok4:
        fails.append("C4")
    if fails:
        print(f"\nCONTROL FAILURE ({', '.join(fails)}) — the numbers are not trusted; stopping.")
        sys.exit(1)
    print("controls PASS\n")

    # ── HEADLINE ─────────────────────────────────────────────────────────────
    print("HEADLINE — app Greek vs our printed form (abp_surface), aligned slots:")
    for rg in ("OT", "NT"):
        n, ex, acc, dm = ladder(G[(rg, "surface")])
        print(f"   {rg}  exact {pct(ex, n)}  · after accents {pct(acc, n)}  · "
              f"after defect map {pct(dm, n)}   (of {n}{', Psalms incl. shifted' if rg == 'OT' else ''})")
    for rg in ("OT", "NT"):
        n, ex, acc, dm = ladder(G[(rg, "identity")])
        print(f"   names {rg} (pn_greek_identity)  exact {pct(ex, n)}  · after accents "
              f"{pct(acc, n)}  · after defect map {pct(dm, n)}   (of {n})")
    print()

    T = Counter()
    for b in B:
        T.update(B[b])
    OTc, NTc = Counter(), Counter()
    for b in B:
        (NTc if b in NT else OTc).update(B[b])

    # ── 1. EDITION DRIFT ─────────────────────────────────────────────────────
    print("1. EDITION DRIFT  (English per paired verse, folded)")
    print(f"   verses paired {T['verses']} (Psalms shifted {T['shifted_verses']})  · "
          f"app-only {T['app_only_verses']}  · ours-only {T['ours_only_verses']}")
    for lbl, S in (("ALL", T), ("OT", OTc), ("NT", NTc)):
        print(f"   {lbl:3} words differ {S['eng_words_differ']:6} ({pct(S['eng_words_differ'], S['verses']).strip()})"
              f"  · order only {S['eng_order_only']:5}  · same {S['eng_same']:6}  of {S['verses']}")
    print(f"\n   {'book':5} {'verses':>6} {'differ':>7} {'%':>8} {'order':>6} {'cnt≠':>5}"
          f" {'app-only':>8} {'ours-only':>9}")
    for b in BOOK_ORDER:
        c = B.get(b)
        if not c:
            continue
        print(f"   {b:5} {c['verses']:6} {c['eng_words_differ']:7} "
              f"{pct(c['eng_words_differ'], c['verses'])} {c['eng_order_only']:6}"
              f" {c['count_diff_verses']:5} {c['app_only_verses']:8} {c['ours_only_verses']:9}")
    print("   words-differ samples (first 25; '-' only in ours, '+' only in app):")
    for (b, c, v), mine, theirs in drift_samples[:25]:
        print(f"     {b} {c}:{v}  -{' '.join(sorted(mine.elements()))[:70]}"
              f"  +{' '.join(sorted(theirs.elements()))[:70]}")

    # ── 2. VERSIFICATION ─────────────────────────────────────────────────────
    print("\n2. VERSIFICATION")
    PS = B.get("Psa", Counter())
    psa_al = PS["aligned_pos"] + PS["aligned_seq"] + PS["reorder"]
    print(f"   PSALMS (own lines): {len(psa_shift)} chapters shifted (our v = app v+1), "
          f"{PS['shifted_verses']} verses; aligned {psa_al}/{PS['our_slots']} "
          f"({pct(psa_al, PS['our_slots']).strip()}); app-only {PS['app_only_verses']}, "
          f"ours-only {PS['ours_only_verses']}")
    n, ex, acc, dm = ladder(G[("PSA", "surface")])
    print(f"     Psalms printed form: exact {pct(ex, n)} · after accents {pct(acc, n)} · "
          f"after defect map {pct(dm, n)} (of {n})")
    print(f"     Psalms English: words differ {PS['eng_words_differ']} "
          f"({pct(PS['eng_words_differ'], PS['verses']).strip()}) · order only {PS['eng_order_only']}")
    low = sorted((c for c, v in CH.items() if c[0] == "Psa" and v["our_slots"]
                  and v["aligned"] < 0.85 * v["our_slots"]), key=lambda c: c[1])
    print(f"     Psalms chapters still under 85% aligned: {len(low)}"
          + (" -> " + ", ".join(f"{c[1]}{'s' if c in psa_shift else ''} "
                                f"{pct(CH[c]['aligned'], CH[c]['our_slots']).strip()}" for c in low[:40])
             if low else "") + ("  ('s' = shifted)" if low else ""))

    ours_by_ch, app_by_ch = defaultdict(dict), defaultdict(dict)
    for (bb, cc, vv), o in ours.items():
        ours_by_ch[(bb, cc)][vv] = o
    for (bb, cc, vv), a in app.items():
        app_by_ch[(bb, cc)][vv] = a
    odd = set()
    for k in ours:
        if k[0] != "Psa" and pair_of[k] not in app:
            odd.add((k[0], k[1]))
    for ka in app:
        if ka[0] != "Psa" and ka not in used_app:
            odd.add((ka[0], ka[1]))
    print(f"   OTHER CHAPTERS with one-sided verses: {len(odd)}")
    for b, ch in sorted(odd, key=lambda c: (rank(c[0]), c[1])):
        tot = CH[(b, ch)]["our_slots"]
        scores = {}
        for s in range(-3, 4):
            n_ = 0
            for vv, o in ours_by_ch[(b, ch)].items():
                if vv + s in app_by_ch[(b, ch)]:
                    n_ += len(align_verse(app_by_ch[(b, ch)][vv + s], o["rows"])[0])
            scores[s] = n_
        best = max(scores, key=lambda s: (scores[s], -abs(s)))
        if best != 0 and tot and scores[best] >= 0.9 * tot:
            fits = f"SHIFT FITS: app verse = ours {best:+d}"
        elif scores[0] and tot and scores[0] >= 0.9 * tot:
            fits = "plain numbering already fits; only the one-sided verses below differ"
        else:
            fits = "no whole-chapter shift fits — verses are numbered/ordered differently (per-verse lines)"
        weakv = sum(1 for vv, o in ours_by_ch[(b, ch)].items() if vv in app_by_ch[(b, ch)]
                    and len(align_verse(app_by_ch[(b, ch)][vv], o["rows"])[0]) < 0.5 * len(o["rows"]))
        print(f"     {b} {ch}: plain {pct(scores[0], tot).strip()} · best shift app v{best:+d} "
              f"{pct(scores[best], tot).strip()} — {fits}; same-numbered verses under 50% matched: {weakv}")
        for vv in sorted(v for v in ours_by_ch[(b, ch)] if v not in app_by_ch[(b, ch)]):
            rows = ours_by_ch[(b, ch)][vv]["rows"]
            cand = [(len(align_verse(a_, rows)[0]) / max(1, len(rows)), av)
                    for av, a_ in app_by_ch[(b, ch)].items()]
            sc, av = max(cand) if cand else (0, None)
            print(f"        ours {b} {ch}:{vv} ≈ app {ch}:{av} ({100 * sc:.0f}% of its slots)")
        for av in sorted(v for v in app_by_ch[(b, ch)] if v not in ours_by_ch[(b, ch)]):
            a_ = app_by_ch[(b, ch)][av]
            cand = [(len(align_verse(a_, o["rows"])[0]) / max(1, len(a_)), vv)
                    for vv, o in ours_by_ch[(b, ch)].items()]
            sc, vv = max(cand) if cand else (0, None)
            print(f"        app  {b} {ch}:{av} ≈ ours {ch}:{vv} ({100 * sc:.0f}% of its slots)")

    # ── 3. ALIGNMENT ─────────────────────────────────────────────────────────
    print("\n3. ALIGNMENT  (our slots paired with an app sub-slot whose number agrees)")
    al = T["aligned_pos"] + T["aligned_seq"]
    print(f"   our slots {T['our_slots']}  · app sub-slots {T['app_subslots']}")
    print(f"   aligned in place {al} ({pct(al, T['our_slots']).strip()})"
          f"  [slot order {T['aligned_pos']} · sequence {T['aligned_seq']}]")
    print(f"   SWAPPED ORDER {T['reorder']} ({pct(T['reorder'], T['our_slots']).strip()}) — "
          f"JP ruling: our build's split-flip reorder, NOT a mismatch (per-row cause not checked)")
    print("     (verses with the SAME slot set on both sides) places moved: " + "  ".join(
        f"{d}:{n}" for d, n in sorted(reorder_dist.items()) if d <= 6)
        + (f"  7+:{sum(n for d, n in reorder_dist.items() if d > 6)}" if any(d > 6 for d in reorder_dist) else ""))
    print(f"   OUT-OF-SEQUENCE MATCH {T['oos']} — in verses whose slot counts DIFFER, a leftover slot"
          f" matched an agreeing leftover elsewhere in the verse (often a repeated word; NOT covered"
          f" by the split-flip ruling, reported only)")
    tot = al + T['reorder'] + T['oos']
    print(f"   aligned incl. swapped + out-of-sequence {tot} ({pct(tot, T['our_slots']).strip()})"
          f"  · left unaligned {T['our_unaligned']} in paired verses"
          f" + {T['ours_only_slots']} in ours-only verses")
    print(f"   same slot, different number (after swaps): {T['slot_disagree']}")
    print(f"   agreement kind: " + "  ".join(f"{h}={how_ct[h]}" for h in ("full", "name", "base", "pron", "reorder", "out-of-seq")))
    print(f"   compound-unsplit sub-slots {T['unsplit']} · inline notes {T['notes']} · "
          f"app number cells with stray characters {sum(STRAY_NUM.values())}")
    print(f"\n   {'book':5} {'ourSlots':>8} {'inPlace':>8} {'swapped':>8} {'oos':>6} {'total%':>8} {'slot≠':>6}")
    for b in BOOK_ORDER:
        c = B.get(b)
        if not c:
            continue
        ip = c["aligned_pos"] + c["aligned_seq"]
        print(f"   {b:5} {c['our_slots']:8} {ip:8} {c['reorder']:8} {c['oos']:6} "
              f"{pct(ip + c['reorder'] + c['oos'], c['our_slots'])} {c['slot_disagree']:6}")
    print("   top same-slot number disagreements left (app -> ours):")
    for (a_, o_), n in slot_disagree.most_common(15):
        print(f"     {n:6}  app {a_:>10}  ours {o_}")

    # ── 4. GREEK DIFF ────────────────────────────────────────────────────────
    print("\n4. GREEK DIFF  (aligned + swapped slots with app Greek; English-font cells excluded)")
    print(f"   ENGLISH TYPED IN THE GREEK FONT (lower-case Latin) — excluded: {T['english_font']}")
    for e in engfont_ex[:6]:
        print(f"        e.g. {e}")
    for t, lbl in (("surface", "abp_surface.form"),
                   ("identity", "pn_greek_identity.greek_lemma"),
                   ("lemma", "dictionary word (no abp_surface row only)")):
        g = G[("OT", t)] + G[("NT", t)]
        n, ex, acc, dm = ladder(g)
        print(f"   {lbl}: compared {n} — exact {pct(ex, n).strip()} · after accents "
              f"{pct(acc, n).strip()} · after defect map {pct(dm, n).strip()}")
        for c in CLASSES:
            print(f"       {CLASS_LABEL[c]:48} {g[c]:8}")
    print("   identity by source class (after defect map / compared):")
    for src, g in sorted(gsrc.items()):
        n, ex, acc, dm = ladder(g)
        print(f"     {src:12} {dm:7}/{n:<7} {pct(dm, n)}   ours-NBSP {g['mm_ours_nbsp']}")

    # ── 5. DEFECT MAP ────────────────────────────────────────────────────────
    print("\n5. APP FONT DEFECTS  (surface + identity compares; a slot counts once per letter)")
    for L in DEFECT_MAP:
        ex_ = defect_ex[L][0] if defect_ex[L] else ""
        print(f"   {DEFECT_LABEL[L]:20} matched {defect_ok[L]:6}   still differs {defect_left[L]:5}"
              f"   {ex_}")
    print(f"   unmapped foreign letters: {sum(foreign_ct.values())} "
          + " ".join(f"{c!r}(U+{ord(c):04X})×{n}" for c, n in foreign_ct.most_common()))
    for c, _ in foreign_ct.most_common(6):
        for e in foreign_ex[c][:2]:
            print(f"        e.g. {e}")

    # ── 6. MISSING PRINTED FORM ──────────────────────────────────────────────
    print(f"\n6. MISSING PRINTED FORM — no abp_surface row, app prints a form that is not the "
          f"dictionary word: {len(missing)} slots")
    print("   by word type (words.morph): " + "  ".join(f"{k}={v}" for k, v in miss_type.most_common()))
    print("   top 20 (app printed form vs our dictionary word):")
    for (ag, dw), n in miss_top.most_common(20):
        print(f"     {n:6}  app {ag!r:22} dictionary {dw!r:20} e.g. {miss_ref[(ag, dw)]}")
    with open(args.missing_out, "w", encoding="utf-8", newline="\n") as f:
        f.write("book\tchapter\tverse\tposition\tstrongs\tword_type\tmorph\tdictionary_word\t"
                "app_printed_form\tapp_english\tclass\n")
        for r in missing:
            f.write("\t".join(str(x).replace("\t", " ") for x in r) + "\n")
    print(f"   wrote {len(missing)} rows -> {args.missing_out}")

    # ── 7. TOP 50 REMAINING MISMATCHES ───────────────────────────────────────
    print("\n7. TOP 50 REMAINING MISMATCHES (surface + identity; foreign-letter cells in 5)")
    for (t, ag, ov), n in mm_top.most_common(50):
        print(f"   {n:6}  {t:8}  app {ag!r:26} ours {ov!r:26} e.g. {mm_ref[(t, ag, ov)]}")
    print(f"   distinct pairs {len(mm_top)} · slots {sum(mm_top.values())}")

    if args.dump:
        with open(args.dump, "w", encoding="utf-8", newline="\n") as f:
            f.write("book\tchapter\tverse\tposition\tour_strongs\tapp_strongs\tagree\t"
                    "app_greek\ttarget\tsource\tour_value\tclass\n")
            for r in dump:
                f.write("\t".join(str(x) for x in r) + "\n")
        print(f"\nwrote {len(dump)} compared slots -> {args.dump}")


if __name__ == "__main__":
    main()
