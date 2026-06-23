#!/usr/bin/env python3
"""build_word_gloss.py — plain-meaning lemma gloss for the word card (GREEK).

Source strategy (settled 2026-06-22 after a plain-meaning quality pass):
  Dodson's brief (short RANGES like "grace, favor, kindness") is the base; TBESG fills
  only the LXX-extended numbers Dodson lacks; a small OVERRIDES list fixes the handful
  of loaded words where even Dodson's range LEADS with the church term (xaris -> "grace,
  favor" once the card trims to two terms). Dodson's first-person verbs ("I dip") and
  leading articles ("a cross") are normalized away.

Dotted ABP numbers (G####.N) are glossed by their OWN lemma (from dotted_lexicon),
looked up in a Greek-lemma index built from TBESG — a base-number match can't fix them
(the dot is dropped, so the base is the alphabetical neighbour).

Writes ONE side table, word_gloss(strongs, gloss, source). Touches NOTHING else (not
words, lexicon, dotted_lexicon). Deploy-safe: the /api/* joins read it only if present.

  python3 scripts/build_word_gloss.py            # DRY RUN: coverage + residue, writes nothing
  python3 scripts/build_word_gloss.py --summary  # dry-run + the loaded-word glosses for review
  python3 scripts/build_word_gloss.py --apply    # (re)build word_gloss (that table only)

Greek only for now; the Hebrew gloss is a separate source decision (heb.db + TBESH).
Never modifies words/lexicon. Re-run after a words rebuild (re-run build_dotted_lexicon first).
"""
import os
import re
import sqlite3
import sys
import unicodedata

DB = next((a for a in sys.argv[1:] if not a.startswith("--")),
          os.path.expanduser("~/bible-db/bible.db"))

DEFAULT_TBESG_URL = ("https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/Lexicons/"
                     "TBESG%20-%20Translators%20Brief%20lexicon%20of%20Extended%20Strongs%20for%20"
                     "Greek%20-%20STEPBible.org%20CC%20BY.txt")


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
DODSON = _opt("dodson", os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "apfathers", "raw", "dodson.csv"))

# Plain-meaning hand fixes — ONLY the loaded words where the chosen source still leads
# with the traditional/church term after normalization. Each is the plain attested sense
# (CLAUDE.md "PLAIN MEANING, NOT TRADITION"): lead with the plain sense, keep the range.
# Proposed — eyeball on --summary and add/remove freely. Keyed by base G-number.
OVERRIDES = {
    # ABP tags grace/favor as G5484 (charin, 238x), NOT the dictionary's G5485 (charis,
    # which ABP never uses) — and G5484's source gloss is the preposition "for the sake of",
    # wrong for the noun. Override both: G5484 is what actually shows; G5485 is future-proofing.
    "G5484": "favor, kindness, goodwill",   # charis/charin — NOT "grace", NOT "for the sake of"
    "G5485": "favor, kindness, goodwill",   # charis (noun) — unused in ABP, kept in case a rebuild uses it
    "G4151": "spirit, breath, wind",        # pneuma — lead the primary sense; NOT "Ghost"
    "G166":  "age-long, lasting",           # aionios — from aion (an age); neither source plain
    "G1228": "slanderer, accuser",          # diabolos — the literal noun; "slanderous" is the adj
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


def bare(s):
    """A Greek lemma stripped to base letters, lowercased — for matching across accent/
    breathing differences (dotted_lexicon lemma vs TBESG's Greek column)."""
    d = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in d if not unicodedata.combining(c)).lower().strip()


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


def tbesg_sense(g):
    """TBESG glosses use 'base: subsense' (e.g. 'spirit/breath: spirit'); take the base."""
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


def parse_tbesg(src):
    """({canon(G#) -> base-sense gloss}, {bare(Greek lemma) -> base-sense gloss}). The
    file is base-sense-first, so the first row for a number/lemma is its primary sense."""
    lines = _read_source(src).splitlines()
    start = next((i + 1 for i, ln in enumerate(lines)
                  if ln.split("\t")[0].strip().rstrip("#") == "eStrong" and "Gloss" in ln), None)
    if start is None:
        raise SystemExit("could not find the TBESG data header")
    by_num, by_lemma = {}, {}
    for ln in lines[start:]:
        if not ln.strip() or ln.startswith("$"):
            continue
        c = ln.split("\t")
        if len(c) < 7 or not c[0].startswith("G"):
            continue
        gloss = tbesg_sense(c[6].strip())
        if not gloss:
            continue
        by_num.setdefault(canon(c[0].strip()), gloss)
        lem = bare(c[3])
        if lem:
            by_lemma.setdefault(lem, gloss)
    return by_num, by_lemma


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
    """Gloss + source for a dotted G####.N number: its own lemma looked up in TBESG."""
    if full_num in OVERRIDES:
        return OVERRIDES[full_num], "override"
    g = tbesg_lemma.get(bare(lemma))
    return (normalize(g), "dotted-lemma") if g else ("", "")


def build_rows(conn, dod, tbesg_num, tbesg_lemma):
    """All (strongs, gloss, source) rows + the blank residue, read-only from the DB."""
    rows, blank_base, blank_dotted = [], [], []

    base_nums = [r[0] for r in conn.execute(
        "SELECT DISTINCT strongs_base FROM words WHERE strongs_base GLOB 'G*'")]
    for num in base_nums:
        gloss, src = pick_base(num, dod, tbesg_num)
        if gloss:
            rows.append((num, gloss, src))
        else:
            blank_base.append(num)

    # dotted numbers that are a genuinely-different word get their gloss by their OWN lemma
    dotted_lemma = {}
    if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='dotted_lexicon'").fetchone():
        dotted_lemma = {r[0]: r[1] for r in conn.execute("SELECT strongs, lemma FROM dotted_lexicon")}
    for full_num, lemma in dotted_lemma.items():           # keys already "G####.N"
        gloss, src = pick_dotted(full_num, lemma, tbesg_lemma)
        if gloss:
            rows.append((full_num, gloss, src))
        else:
            blank_dotted.append((full_num, lemma))
    return rows, blank_base, blank_dotted


def main():
    apply = "--apply" in sys.argv
    summary = "--summary" in sys.argv
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    dod = load_dodson(DODSON)
    tbesg_num, tbesg_lemma = parse_tbesg(TBESG)
    print(f"sources: Dodson {len(dod)} numbers, TBESG {len(tbesg_num)} numbers / "
          f"{len(tbesg_lemma)} lemmas")

    rows, blank_base, blank_dotted = build_rows(conn, dod, tbesg_num, tbesg_lemma)
    by_src = {}
    for _, _, s in rows:
        by_src[s] = by_src.get(s, 0) + 1
    n_base = sum(1 for r in rows if "." not in r[0])
    n_dot = len(rows) - n_base
    print(f"base G-numbers glossed : {n_base}  (blank: {len(blank_base)})")
    print(f"dotted G-numbers glossed: {n_dot}  (blank: {len(blank_dotted)})")
    print(f"by source: {by_src}")

    if blank_base:
        blank_base_sorted = sorted(blank_base)
        print(f"  base numbers with NO gloss (hand-fill): {len(blank_base_sorted)} "
              f"e.g. {blank_base_sorted[:12]}")

    if blank_dotted:
        with open("gloss_dotted_blank.tsv", "w", encoding="utf-8") as f:
            f.write("dotted_number\tlemma\n")
            for num, lemma in sorted(blank_dotted):
                f.write(f"{num}\t{lemma}\n")
        print(f"  dotted with no lemma match: {len(blank_dotted)} -> gloss_dotted_blank.tsv "
              f"e.g. {[n for n, _ in blank_dotted[:8]]}")

    if summary:
        lex = {r["strongs_g"]: r["lemma"] for r in
               conn.execute("SELECT strongs_g, lemma FROM lexicon WHERE strongs_g GLOB 'G*'")}
        gmap = {n: g for n, g, _ in rows}
        check = ["G5484", "G5590", "G4561", "G1577", "G2435", "G86", "G1067", "G4151",
                 "G26", "G907", "G3341", "G166", "G2851", "G4716", "G3875", "G3466",
                 "G2098", "G266", "G1343", "G2962", "G1228", "G3107"]
        print("\nloaded-word review — stored gloss (and what the card SHOWS via first-two-terms):")
        for n in check:
            stored = gmap.get(n, "—")
            shown = ", ".join([p.strip() for p in re.split(r"[,;]", stored)][:2])
            print(f"  {n:6} {lex.get(n,''):14} {stored:30.30} -> card shows: {shown}")

    if not apply:
        print("\n[dry-run] nothing written. Re-run with --apply to (re)build word_gloss.")
        conn.close()
        return

    conn.execute("DROP TABLE IF EXISTS word_gloss")
    conn.execute("CREATE TABLE word_gloss (strongs TEXT PRIMARY KEY, gloss TEXT, source TEXT)")
    conn.executemany("INSERT OR REPLACE INTO word_gloss(strongs, gloss, source) VALUES (?,?,?)", rows)
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM word_gloss").fetchone()[0]
    conn.close()
    print(f"\nFilled word_gloss with {n} Greek glosses (that table only; nothing else touched).")


if __name__ == "__main__":
    main()
