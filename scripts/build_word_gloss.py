#!/usr/bin/env python3
"""build_word_gloss.py — plain-meaning lemma gloss for the word card (GREEK + HEBREW).

GREEK (settled 2026-06-22 after a plain-meaning quality pass):
  Dodson's brief (short RANGES like "grace, favor, kindness") is the base; TBESG fills
  only the LXX-extended numbers Dodson lacks; a small OVERRIDES list fixes the handful
  of loaded words where even Dodson's range LEADS with the church term once the card trims
  to two terms. Dodson's first-person verbs ("I dip") and leading articles ("a cross") are
  normalized away. Dotted ABP numbers (G####.N) are glossed by their OWN lemma (from
  dotted_lexicon), looked up in a TBESG Greek-lemma index — a base match can't fix them.

HEBREW (settled 2026-06-22):
  TBESH's clean dictionary form is the base ("spirit", "instruction", "God") + a few
  plain-meaning overrides (sheol != hell, olam != forever, chesed = loyal love). heb.db's
  OWN gloss is contextual ("self my", "God your"), so it is NOT the lemma source — it shows
  on the card's in-verse line instead. TBESH covers every Hebrew number the app shows.

Writes ONE side table, word_gloss(strongs, gloss, source). Touches NOTHING else (not words,
lexicon, dotted_lexicon, heb.db). Deploy-safe: the /api/* joins read it only if present.

  python3 scripts/build_word_gloss.py            # DRY RUN: coverage + residue, writes nothing
  python3 scripts/build_word_gloss.py --summary  # dry-run + the loaded-word review (Greek + Hebrew)
  python3 scripts/build_word_gloss.py --apply    # (re)build word_gloss (that table only)

Re-run after a words rebuild (run build_dotted_lexicon first). Reads heb.db read-only.
"""
import html
import os
import re
import sqlite3
import sys
import unicodedata

DB = next((a for a in sys.argv[1:] if not a.startswith("--")),
          os.path.expanduser("~/bible-db/bible.db"))

_LEX = "https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/Lexicons/"
DEFAULT_TBESG_URL = (_LEX + "TBESG%20-%20Translators%20Brief%20lexicon%20of%20Extended%20Strongs%20"
                     "for%20Greek%20-%20STEPBible.org%20CC%20BY.txt")
DEFAULT_TBESH_URL = (_LEX + "TBESH%20-%20Translators%20Brief%20lexicon%20of%20Extended%20Strongs%20"
                     "for%20Hebrew%20-%20STEPBible.org%20CC%20BY.txt")


def _opt(name, default=None):
    pre = f"--{name}="
    for a in sys.argv:
        if a.startswith(pre):
            return a[len(pre):]
    if f"--{name}" in sys.argv:
        i = sys.argv.index(f"--{name}")
        if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
            return sys.argv[i + 1]
    return default


TBESG = _opt("tbesg", DEFAULT_TBESG_URL)
TBESH = _opt("tbesh", DEFAULT_TBESH_URL)
DODSON = _opt("dodson", os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "apfathers", "raw", "dodson.csv"))
HEB = _opt("heb", os.path.expanduser("~/bible-db/heb.db"))

# GREEK plain-meaning hand fixes — ONLY the loaded words where the chosen source still leads
# with the traditional/church term after normalization (CLAUDE.md "PLAIN MEANING, NOT
# TRADITION"): lead with the plain sense, keep the range. Keyed by base G-number.
OVERRIDES = {
    # ABP tags grace/favor as G5484 (charin, 238x), NOT the dictionary's G5485 (charis,
    # which ABP never uses) — and G5484's source gloss is the preposition "for the sake of",
    # wrong for the noun. Override both: G5484 is what shows; G5485 is future-proofing.
    "G5484": "favor, kindness, goodwill",   # charis/charin — NOT "grace", NOT "for the sake of"
    "G5485": "favor, kindness, goodwill",   # charis (noun) — unused in ABP, kept for a future rebuild
    "G4151": "spirit, breath, wind",        # pneuma — lead the primary sense; NOT "Ghost"
    "G166":  "age-long, lasting",           # aionios — from aion (an age); neither source plain
    "G1228": "slanderer, accuser",          # diabolos — the literal noun; "slanderous" is the adj
    "G3341": "change of mind, repentance",  # metanoia — lead the plain sense, not the church term
}

# HEBREW base = TBESH's clean dictionary form; these 3 are the loaded ones it still gets
# wrong. Keyed by base H-number (heb.db's own contextual gloss feeds the in-verse line).
HEBREW_OVERRIDES = {
    "H7585": "grave, realm of the dead",   # sheol — NOT "hell"
    "H5769": "age, long duration",         # olam — NOT "forever/everlasting"
    "H2617": "loyal love, kindness",       # chesed — richer than TBESH's bare "kindness"
    "H853":  "marks the direct object",    # et — TBESH's "[Obj.]" is cryptic (no parens: card strips them)
}

# Dotted ABP numbers whose lemma is a particle/numeral with no TBESG headword, glossed by
# hand because they're definitional, not guesses (verifiable from the abp_ext entry): the
# spelled-out numbers + a few standard particles. Everything else dotted comes from the
# TBESG lemma index or ABP's own gloss (abp_gloss); the rest fall back to the LSJ section.
DOTTED_OVERRIDES = {
    "G1501.1": "twenty-two", "G1768.1": "ninety-eight", "G1768.3": "ninety-five",
    "G3589.4": "eighty-three", "G3589.5": "eightieth", "G5144.9": "thirty-three",
    "G4001.3": "fivefold", "G4004.4": "fifty years old", "G1835.4": "sixty years old",
    "G2193.2": "six",                          # the numeral letter stigma (ϛ) = 6
    "G3766.2": "by no means, certainly not",   # ou me
    "G438.1": "instead of, for", "G446.2": "instead of, for",   # anti (elided)
    "G1758.1": "there, where", "G3748.1": "anything whatever",
}

_ARTICLE = re.compile(r"^(?:a|an|the)\s+", re.I)


def _read_source(src):
    if re.match(r"^https?://", src):
        import urllib.request
        req = urllib.request.Request(src, headers={"User-Agent": "bible-db/1.0"})
        with urllib.request.urlopen(req) as r:
            return r.read().decode("utf-8")
    with open(src, encoding="utf-8") as f:
        return f.read()


def canon(s):
    """Fold a Strong's number for matching: strip the G/H zero-pad (G0026 -> G26)."""
    m = re.match(r"^([GH])0*(\d+)", s or "")
    return f"{m.group(1)}{m.group(2)}" if m else (s or "")


def norm_h(s):
    """Fold a Hebrew number to its base (H1234a -> H1234): KJV/BSB use base numbers,
    heb.db adds byform letters to split homographs."""
    m = re.match(r"^(H\d+)[a-z]?$", s or "")
    return m.group(1) if m else (s or "")


def bare(s):
    """A Greek lemma stripped to base letters, lowercased — for matching across accent/
    breathing differences (dotted_lexicon lemma vs TBESG's Greek column)."""
    d = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in d if not unicodedata.combining(c)).lower().strip()


def clean_text(def_html):
    """Drop tags + decode entities from an abp_ext definition (same as audit_dotted_lemmas)."""
    return html.unescape(re.sub(r"<[^>]+>", "", def_html or ""))


def abp_gloss(clean):
    """ABP's OWN short gloss from a cleaned abp_ext entry, but ONLY the clean
    '[ABP] <lemma>, <gloss>' form (authoritative + short, e.g. 'prance', 'seraphim').
    Returns '' for the [MLSJ]/[LSJ]/[GEL] prose entries — pulling a 2-word sense from
    those risks junk, so they fall back to the LSJ section on the card."""
    if not clean or not clean.lstrip().startswith("[ABP]"):
        return ""
    after = clean.split("]", 1)[1]              # drop the [ABP] tag
    if "," not in after:
        return ""
    after = after.split(",", 1)[1]              # text after "lemma,"
    after = re.split(r"\s{2,}|See also|\[", after, 1)[0]   # stop at refs / cross-link / next tag
    g = normalize(after)
    return g if g and len(g) <= 40 and re.search(r"[a-z]", g) else ""


def normalize(g):
    """Raw brief gloss -> card-ready short sense: drop Dodson's leading first-person 'I '
    ('I dip' -> 'dip'), drop a leading article ('a cross' -> 'cross'), and drop a
    case-insensitive duplicate term ('lord, Lord, master' -> 'lord, master')."""
    if not g:
        return ""
    g = re.sub(r"^I (?=[a-z])", "", g.strip())
    g = _ARTICLE.sub("", g).strip()
    parts, seen = [], set()
    for p in re.split(r"[,;]", g):
        p = p.strip()
        if p and p.lower() not in seen:
            seen.add(p.lower())
            parts.append(p)
    return ", ".join(parts).rstrip(" ,;:.-")


def sense(g):
    """STEPBible glosses use 'base: subsense' (e.g. 'spirit/breath: spirit'); take the base."""
    return (g or "").split(":")[0].strip()


def load_dodson(src):
    """{canon('G'+number) -> brief gloss} from Dodson (tab-delimited, quoted; col 0 =
    zero-padded Strong's, col 3 = the brief gloss). NT-only standard Strong's."""
    import csv
    out = {}
    rdr = csv.reader(_read_source(src).splitlines(), delimiter="\t", quotechar='"')
    for i, row in enumerate(rdr):
        if i == 0 or len(row) < 4:
            continue
        num, brief = (row[0] or "").strip(), (row[3] or "").strip()
        if num.isdigit() and brief:
            out.setdefault(canon("G" + num), brief)
    return out


def _brief_lines(src):
    """Iterate a STEPBible brief lexicon's data rows (skips the preamble + $ section blocks)."""
    lines = _read_source(src).splitlines()
    start = next((i + 1 for i, ln in enumerate(lines)
                  if ln.split("\t")[0].strip().rstrip("#") == "eStrong" and "Gloss" in ln), None)
    if start is None:
        raise SystemExit(f"could not find the data header in {src}")
    for ln in lines[start:]:
        if ln.strip() and not ln.startswith("$"):
            yield ln.split("\t")


def parse_tbesg(src):
    """({canon(G#) -> base-sense gloss}, {bare(Greek lemma) -> base-sense gloss}). The
    file is base-sense-first, so the first row for a number/lemma is its primary sense."""
    by_num, by_lemma = {}, {}
    for c in _brief_lines(src):
        if len(c) < 7 or not c[0].startswith("G"):
            continue
        g = sense(c[6].strip())
        if not g:
            continue
        by_num.setdefault(canon(c[0].strip()), g)
        lem = bare(c[3])
        if lem:
            by_lemma.setdefault(lem, g)
    return by_num, by_lemma


def load_tbesh(src):
    """{canon(H#) -> primary base-sense gloss} from TBESH. canon folds byforms
    (H2617a/b -> H2617), and the first row wins = the primary sense."""
    out = {}
    for c in _brief_lines(src):
        if len(c) >= 7 and c[0].startswith("H"):
            g = sense(c[6].strip())
            if g:
                out.setdefault(canon(c[0].strip()), g)
    return out


def pick_base(num, dod, tbesg_num):
    """Gloss + source for a base G-number: override, else Dodson, else TBESG fill."""
    if num in OVERRIDES:
        return OVERRIDES[num], "override"
    c = canon(num)
    if c in dod:
        return normalize(dod[c]), "dodson"
    if c in tbesg_num:
        return normalize(tbesg_num[c]), "tbesg"
    return "", ""


def pick_dotted(full_num, lemma, tbesg_lemma):
    """Gloss + source for a dotted G####.N number: hand override, else its own lemma
    looked up in TBESG. (ABP's own gloss is tried after this, in build_greek_rows.)"""
    if full_num in DOTTED_OVERRIDES:
        return DOTTED_OVERRIDES[full_num], "override"
    g = tbesg_lemma.get(bare(lemma))
    return (normalize(g), "dotted-lemma") if g else ("", "")


def build_greek_rows(conn, dod, tbesg_num, tbesg_lemma):
    """Greek (strongs, gloss, source) rows + the blank residue, read-only from the DB."""
    rows, blank_base, blank_dotted = [], [], []
    for r in conn.execute("SELECT DISTINCT strongs_base FROM words WHERE strongs_base GLOB 'G*'"):
        num = r[0]
        gloss, src = pick_base(num, dod, tbesg_num)
        (rows.append((num, gloss, src)) if gloss else blank_base.append(num))

    dotted_lemma = {}
    if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='dotted_lexicon'").fetchone():
        dotted_lemma = {r[0]: r[1] for r in conn.execute("SELECT strongs, lemma FROM dotted_lexicon")}
    abp = {}                                               # dotted ABP dict entries, both key forms
    if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='abp_ext'").fetchone():
        for r in conn.execute("SELECT trim(strongs) s, def_html FROM abp_ext WHERE strongs LIKE '%.%'"):
            abp[r[0]] = r[1]
    for full_num, lemma in dotted_lemma.items():           # keys already "G####.N"
        gloss, src = pick_dotted(full_num, lemma, tbesg_lemma)
        if not gloss:                                      # ABP's own gloss before giving up
            raw = abp.get(full_num) or abp.get(full_num.lstrip("G"))
            g = abp_gloss(clean_text(raw)) if raw else ""
            if g:
                gloss, src = g, "abp-ext"
        (rows.append((full_num, gloss, src)) if gloss else blank_dotted.append((full_num, lemma)))
    return rows, blank_base, blank_dotted


def build_hebrew_rows(conn, heb_path, tbesh):
    """Hebrew rows + blanks for every base H-number the app can show a card for: KJV + BSB
    Hebrew Strong's + the heb.db OT reader, folded to base numbers (norm_h)."""
    universe = set()
    for tbl, col in (("kjv_strongs", "strongs_id"), ("bsb_strongs", "strongs_id")):
        if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (tbl,)).fetchone():
            for r in conn.execute(f"SELECT DISTINCT {col} FROM {tbl} WHERE {col} GLOB 'H*'"):
                universe.add(norm_h(r[0]))
    if heb_path and os.path.exists(heb_path):
        hc = sqlite3.connect(heb_path)
        for r in hc.execute("SELECT DISTINCT strongs FROM heb_words WHERE strongs GLOB 'H*'"):
            universe.add(norm_h(r[0]))
        hc.close()
    rows, blank = [], []
    for num in universe:
        if num in HEBREW_OVERRIDES:
            rows.append((num, HEBREW_OVERRIDES[num], "override"))
            continue
        g = normalize(tbesh.get(canon(num), ""))
        (rows.append((num, g, "tbesh")) if g else blank.append(num))
    return rows, blank


def _review(gmap, items, label):
    print(f"\n{label} loaded-word review — stored gloss -> card shows:")
    for num, name in items:
        stored = gmap.get(num, "—")
        shown = ", ".join([p.strip() for p in re.split(r"[,;]", stored)][:2])
        print(f"  {num:6} {name:11} {stored:30.30} -> {shown}")


def main():
    do_apply = "--apply" in sys.argv
    summary = "--summary" in sys.argv
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    dod = load_dodson(DODSON)
    tbesg_num, tbesg_lemma = parse_tbesg(TBESG)
    tbesh = load_tbesh(TBESH)
    print(f"sources: Dodson {len(dod)}, TBESG {len(tbesg_num)} nums/{len(tbesg_lemma)} lemmas, "
          f"TBESH {len(tbesh)}")

    rows, blank_base, blank_dotted = build_greek_rows(conn, dod, tbesg_num, tbesg_lemma)
    heb_rows, blank_heb = build_hebrew_rows(conn, HEB, tbesh)
    rows += heb_rows

    by_src = {}
    for _, _, s in rows:
        by_src[s] = by_src.get(s, 0) + 1
    n_base = sum(1 for r in rows if r[0][0] == "G" and "." not in r[0])
    n_dot = sum(1 for r in rows if r[0][0] == "G" and "." in r[0])
    n_heb = sum(1 for r in rows if r[0][0] == "H")
    print(f"Greek base   : {n_base}  (blank: {len(blank_base)})")
    print(f"Greek dotted : {n_dot}  (blank: {len(blank_dotted)})")
    print(f"Hebrew       : {n_heb}  (blank: {len(blank_heb)})")
    print(f"by source: {by_src}")

    if blank_base:
        print(f"  Greek base with NO gloss (hand-fill): {len(blank_base)} e.g. {sorted(blank_base)[:12]}")
    if blank_heb:
        print(f"  Hebrew with NO gloss (hand-fill): {len(blank_heb)} e.g. {sorted(blank_heb)[:12]}")
    if blank_dotted:
        with open("gloss_dotted_blank.tsv", "w", encoding="utf-8") as f:
            f.write("dotted_number\tlemma\n")
            for num, lemma in sorted(blank_dotted):
                f.write(f"{num}\t{lemma}\n")
        print(f"  dotted with NO gloss (show LSJ section instead): {len(blank_dotted)} -> "
              f"gloss_dotted_blank.tsv e.g. {[n for n, _ in blank_dotted[:8]]}")

    abp_rows = sorted((n, g) for n, g, s in rows if s == "abp-ext")
    if abp_rows:
        with open("gloss_dotted_abp.tsv", "w", encoding="utf-8") as f:
            f.write("dotted_number\tgloss\n")
            for n, g in abp_rows:
                f.write(f"{n}\t{g}\n")
        print(f"  dotted glossed from ABP's own dict: {len(abp_rows)} -> gloss_dotted_abp.tsv (eyeball these)")

    if summary:
        gmap = {n: g for n, g, _ in rows}
        lexg = {r["strongs_g"]: r["lemma"] for r in
                conn.execute("SELECT strongs_g, lemma FROM lexicon WHERE strongs_g GLOB 'G*'")}
        _review(gmap, [(n, lexg.get(n, "")) for n in (
            "G5484", "G5590", "G4561", "G1577", "G2435", "G86", "G1067", "G4151", "G26", "G907",
            "G3341", "G166", "G2851", "G4716", "G3875", "G3466", "G2098", "G266", "G1343",
            "G2962", "G1228", "G3107")], "GREEK")
        _review(gmap, [("H7307", "ruach"), ("H5315", "nephesh"), ("H2617", "chesed"),
                       ("H7585", "sheol"), ("H8451", "torah"), ("H3722", "kaphar"),
                       ("H5769", "olam"), ("H6664", "tsedeq"), ("H6918", "qadosh"),
                       ("H1285", "berith"), ("H4899", "mashiach"), ("H1350", "gaal"),
                       ("H3519", "kavod"), ("H430", "elohim")], "HEBREW")

    if not do_apply:
        print("\n[dry-run] nothing written. Re-run with --apply to (re)build word_gloss.")
        conn.close()
        return

    conn.execute("DROP TABLE IF EXISTS word_gloss")
    conn.execute("CREATE TABLE word_gloss (strongs TEXT PRIMARY KEY, gloss TEXT, source TEXT)")
    conn.executemany("INSERT OR REPLACE INTO word_gloss(strongs, gloss, source) VALUES (?,?,?)", rows)
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM word_gloss").fetchone()[0]
    conn.close()
    print(f"\nFilled word_gloss with {n} glosses ({n_base} Greek base + {n_dot} dotted + "
          f"{n_heb} Hebrew; that table only, nothing else touched).")


if __name__ == "__main__":
    main()
