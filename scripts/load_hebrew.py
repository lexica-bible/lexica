#!/usr/bin/env python3
"""
load_hebrew.py — build the Hebrew OT interlinear into its OWN database (heb.db),
from the STEP Bible TAHOT data (Translators Amalgamated Hebrew OT, CC BY 4.0).

TAHOT is one source carrying everything per word: the Westminster/Leningrad Hebrew,
the SURFACE transliteration (the actual inflected pronunciation, e.g. "be.re.Shit"),
a clean contextual English gloss, the disambiguated Strong's number, and ETCBC
morphology. So this replaces BOTH the old morphhb text AND the trimmed Strong's-
definition glosses — clean glosses, real pronunciation, and grammar in one pass.

Writes two tables — heb_words + heb_verses — into a SEPARATE heb.db. NEVER touches
bible.db. Safe to re-run: it clears and refills only the book(s) present in the files
you give it.

Data (download on PythonAnywhere, CC BY — 4 files because one is too big for GitHub):
    mkdir -p ~/tahot
    base="https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/Translators%20Amalgamated%20OT%2BNT"
    wget -O ~/tahot/gen-deu.txt "$base/TAHOT%20Gen-Deu%20-%20Translators%20Amalgamated%20Hebrew%20OT%20-%20STEPBible.org%20CC%20BY.txt"
    ... (jos-est, job-sng, isa-mal likewise)

Run (one file first to check, then all four):
    python3 scripts/load_hebrew.py --out ~/bible-db/heb.db ~/tahot/gen-deu.txt
    python3 scripts/load_hebrew.py --out ~/bible-db/heb.db ~/tahot          # a dir = all *.txt

The data row layout (tab-separated), confirmed from the file header + Gen.1.1:
  0 Ref+Type      Gen.1.1#01=L        (English versification; book.ch.vs#word=source)
  1 Hebrew        בְּ/רֵאשִׁ֖ית         ("/" splits prefixes/suffixes, "\\" precedes punctuation)
  2 Translit      be./re.Shit         (caps = stressed syllable; "/" mirrors the prefixes)
  3 Gloss         in/ beginning       ("<x>" = in Hebrew, skip in English; "[x]" = implied)
  4 dStrongs      H9003/{H7225G}      (the ROOT word's Strong's is in {curly braces})
  5 Grammar       HR/Ncfsa            (ETCBC/OpenScriptures morphology; root = last "/" part)
  ... (variant / instance / expanded-tag columns we don't need)
"""
import argparse
import re
import sqlite3
from pathlib import Path

# TAHOT 3-letter book code -> the book id the app uses (BOOK_ORDER in 00-core.jsx).
# A few extra aliases so whichever spelling TAHOT uses still maps.
TAHOT_BOOK = {
    "Gen": "Gen", "Exo": "Exo", "Lev": "Lev", "Num": "Num", "Deu": "Deu",
    "Jos": "Jos", "Jdg": "Jdg", "Rut": "Rth", "Rth": "Rth",
    "1Sa": "1Sa", "2Sa": "2Sa", "1Ki": "1Ki", "2Ki": "2Ki",
    "1Ch": "1Ch", "2Ch": "2Ch", "Ezr": "Ezr", "Neh": "Neh", "Est": "Est",
    "Job": "Job", "Psa": "Psa", "Pro": "Pro", "Ecc": "Ecc",
    "Sng": "Son", "Sol": "Son", "Son": "Son",
    "Isa": "Isa", "Jer": "Jer", "Lam": "Lam", "Ezk": "Eze", "Eze": "Eze",
    "Dan": "Dan", "Hos": "Hos", "Joe": "Joe", "Jol": "Joe", "Amo": "Amo",
    "Oba": "Oba", "Jon": "Jon", "Mic": "Mic", "Nah": "Nah", "Hab": "Hab",
    "Zep": "Zep", "Hag": "Hag", "Zec": "Zec", "Mal": "Mal",
}

# A data row starts with  Book.chap.verse#word  (an optional "(HebRef)" may sit before "#").
ROW_RE = re.compile(r"^([A-Za-z0-9]+)\.(\d+)\.(\d+)(?:\([^)]*\))?#(\d+)")

# Cantillation (chant) accents + structural marks to DROP. KEEP the niqqud (vowel
# points U+05B0-05BC, shin/sin dots U+05C1/05C2, qamats-qatan U+05C7).
_DROP = set(range(0x0591, 0x05B0))
_DROP |= {0x05BD, 0x05BF, 0x05C0, 0x05C3, 0x05C4, 0x05C5, 0x05C6}


def clean_hebrew(s):
    s = s.split("\\")[0]                # drop a trailing "\punctuation" (e.g. the verse-end mark)
    s = s.replace("/", "")              # join prefix/suffix morphemes into the written word
    return "".join(ch for ch in s if ord(ch) not in _DROP).strip()


def clean_translit(s):
    return s.split("\\")[0].replace("/", "").strip()   # "be./re.Shit" -> "be.re.Shit"


def clean_gloss(s):
    s = s.split("\\")[0].replace("/", " ")             # "in/ beginning" -> "in beginning"
    s = s.replace("<", "").replace(">", "")            # "<obj.>" -> "obj."
    return re.sub(r"\s+", " ", s).strip()


def root_strongs(dstrongs):
    # "H9003/{H7225G}" -> H7225 ; "{H1254A}" -> H1254 ; "{H0853}" -> H853.
    # The content word is in {curly braces}; H9xxx codes are prefixes/punctuation.
    m = re.search(r"\{H0*(\d+)[A-Za-z]?\}", dstrongs)
    if m:
        return "H" + m.group(1)
    nums = [n for n in re.findall(r"H0*(\d+)[A-Za-z]?", dstrongs) if not n.startswith("90")]
    return ("H" + nums[-1]) if nums else None


def root_morph(grammar):
    # "HR/Ncfsa" -> "Ncfsa" ; "HVqp3ms" -> "Vqp3ms" ; "HC/To" -> "To".
    if not grammar:
        return ""
    root = grammar.split("\\")[0].split("/")[-1]       # last "/" segment = the root word's morph
    if len(root) > 1 and root[0] in ("H", "A") and root[1].isupper():
        root = root[1:]                                # strip the leading language letter if present
    return root


# ── ETCBC / OpenScriptures morphology -> plain English ───────────────────────
_POS = {"A": "adjective", "C": "conjunction", "D": "adverb", "N": "noun",
        "P": "pronoun", "R": "preposition", "S": "suffix", "T": "particle", "V": "verb"}
_VSTEM = {"q": "qal", "N": "niphal", "p": "piel", "P": "pual", "h": "hiphil", "H": "hophal",
          "t": "hithpael", "o": "polel", "O": "polal", "r": "poel", "R": "poal", "f": "hithpolel",
          "D": "pilpel", "j": "polpal", "i": "hithpalpel", "u": "hothpaal", "c": "tiphil", "v": "hishtaphel"}
_VCONJ = {"p": "perfect", "q": "sequential perfect", "i": "imperfect", "w": "sequential imperfect",
          "h": "cohortative", "j": "jussive", "v": "imperative", "r": "active participle",
          "s": "passive participle", "a": "infinitive absolute", "c": "infinitive construct"}
_PERSON = {"1": "1st person", "2": "2nd person", "3": "3rd person"}
_GENDER = {"m": "masculine", "f": "feminine", "b": "both", "c": "common"}
_NUMBER = {"s": "singular", "p": "plural", "d": "dual"}
_STATE = {"a": "absolute", "c": "construct", "d": "determined"}
_NTYPE = {"c": "common", "g": "gentilic", "p": "proper", "x": "" }
_ATYPE = {"a": "", "c": "cardinal number", "g": "gentilic", "o": "ordinal number", "x": ""}
_PTYPE = {"d": "demonstrative", "f": "indefinite", "i": "interrogative", "p": "personal", "r": "relative"}
_TTYPE = {"a": "affirmation", "d": "definite article", "e": "exhortation", "i": "interrogative",
          "j": "interjection", "m": "demonstrative", "n": "negative", "o": "direct object marker",
          "r": "relative"}
_STYPE = {"d": "directional he", "h": "paragogic he", "n": "paragogic nun", "p": "pronominal"}


def _pgn(s):
    # person / gender / number tail, e.g. "3ms" -> ["3rd person","masculine","singular"]
    out = []
    if s[:1] in _PERSON: out.append(_PERSON[s[0]]); s = s[1:]
    if s[:1] in _GENDER: out.append(_GENDER[s[0]]); s = s[1:]
    if s[:1] in _NUMBER: out.append(_NUMBER[s[0]])
    return out


def decode_morph(code):
    """ETCBC code -> readable grammar, e.g. 'Vqp3ms' -> 'verb · qal · perfect · 3rd person masculine singular'."""
    if not code:
        return ""
    p, rest = code[0], code[1:]
    parts = []
    if p == "V":
        parts = ["verb", _VSTEM.get(rest[:1], ""), _VCONJ.get(rest[1:2], "")] + _pgn(rest[2:])
    elif p == "N":
        parts = ["noun", _NTYPE.get(rest[:1], ""), _GENDER.get(rest[1:2], ""),
                 _NUMBER.get(rest[2:3], ""), _STATE.get(rest[3:4], "")]
    elif p == "A":
        parts = ["adjective", _ATYPE.get(rest[:1], ""), _GENDER.get(rest[1:2], ""),
                 _NUMBER.get(rest[2:3], ""), _STATE.get(rest[3:4], "")]
    elif p == "P":
        parts = ["pronoun", _PTYPE.get(rest[:1], "")] + _pgn(rest[1:])
    elif p == "T":
        parts = ["particle", _TTYPE.get(rest[:1], "")]
    elif p == "S":
        parts = ["suffix", _STYPE.get(rest[:1], "")] + _pgn(rest[1:])
    elif p in _POS:
        parts = [_POS[p]]
    else:
        return code
    return " · ".join(x for x in parts if x)


def parse_file(path):
    wrows, vrows = [], []
    cur_key, pos, seen, words = None, 0, set(), []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        m = ROW_RE.match(raw)
        if not m:
            continue                                   # header, #-comment or column-title line
        bk, ch, vs, wordnum = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
        app_book = TAHOT_BOOK.get(bk)
        if not app_book:
            continue
        f = raw.split("\t")
        if len(f) < 6:
            continue
        key = (app_book, ch, vs)
        if key != cur_key:
            if cur_key:
                vrows.append((cur_key[0], cur_key[1], cur_key[2], " ".join(words)))
            cur_key, pos, seen, words = key, 0, set(), []
        if wordnum in seen:                            # a variant row sharing a word slot — skip the dup
            continue
        seen.add(wordnum)
        heb = clean_hebrew(f[1])
        if not heb:
            continue
        sn = root_strongs(f[4])
        morph = root_morph(f[5])
        wrows.append((app_book, ch, vs, pos, heb, sn, morph,
                      clean_gloss(f[3]), clean_translit(f[2]), decode_morph(morph)))
        words.append(heb)
        pos += 1
    if cur_key:
        vrows.append((cur_key[0], cur_key[1], cur_key[2], " ".join(words)))
    return wrows, vrows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="output heb.db path")
    ap.add_argument("paths", nargs="+", help="TAHOT .txt files (or a directory of them)")
    args = ap.parse_args()

    files = []
    for p in args.paths:
        pp = Path(p)
        files.extend(sorted(pp.glob("*.txt")) if pp.is_dir() else [pp])

    conn = sqlite3.connect(args.out)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS heb_words (
            book TEXT, chapter INTEGER, verse INTEGER, position INTEGER,
            hebrew TEXT, strongs TEXT, morph TEXT, gloss TEXT, translit TEXT, grammar TEXT
        );
        CREATE TABLE IF NOT EXISTS heb_verses (
            book TEXT, chapter INTEGER, verse INTEGER, hebrew TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_heb_words_bcv  ON heb_words(book, chapter, verse);
        CREATE INDEX IF NOT EXISTS idx_heb_verses_bcv ON heb_verses(book, chapter, verse);
    """)
    # bring an older heb.db up to the current columns (so re-running upgrades in place)
    have = [r[1] for r in cur.execute("PRAGMA table_info(heb_words)")]
    for col in ("translit", "grammar"):
        if col not in have:
            cur.execute(f"ALTER TABLE heb_words ADD COLUMN {col} TEXT")

    total = 0
    for fp in files:
        wrows, vrows = parse_file(fp)
        books = sorted({r[0] for r in wrows})
        for b in books:                                # clear each book this file touches, then refill
            cur.execute("DELETE FROM heb_words  WHERE book=?", (b,))
            cur.execute("DELETE FROM heb_verses WHERE book=?", (b,))
        cur.executemany("INSERT INTO heb_words  VALUES (?,?,?,?,?,?,?,?,?,?)", wrows)
        cur.executemany("INSERT INTO heb_verses VALUES (?,?,?,?)", vrows)
        total += len(wrows)
        print(f"{fp.name:24} {len(wrows):7} words  ({', '.join(books)})")

    conn.commit()
    nomatch = cur.execute("SELECT count(*) FROM heb_words WHERE strongs IS NULL").fetchone()[0]
    conn.close()
    print(f"done: {total} Hebrew words; {nomatch} with no Strong's (prefix/suffix-only — expected)")


if __name__ == "__main__":
    main()
