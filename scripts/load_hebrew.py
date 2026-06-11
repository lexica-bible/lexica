#!/usr/bin/env python3
"""
load_hebrew.py — build the Hebrew OT interlinear into its OWN database (heb.db).

Reads the OpenScriptures morphhb Westminster Leningrad Codex (OSIS XML, public
domain) and writes two tables — heb_words and heb_verses — into a SEPARATE heb.db
file. It NEVER reads or writes bible.db. Safe to re-run: it clears and refills only
the book(s) you name.

Each Hebrew word keeps its vowel points but has the cantillation (chanting) accents
stripped, and carries its Strong's H-number, its grammar code, and a short English
gloss. The gloss comes from the public-domain Strong's Hebrew dictionary (morphhb
itself has no English). The H-number is what the reader already uses to open the BDB
lexicon sidebar, so word-clicks light up for free.

Run on PythonAnywhere after cloning the data:
    git clone https://github.com/openscriptures/morphhb ~/morphhb
    # short English glosses (public domain) — openscriptures Strong's Hebrew dict:
    wget -O ~/strongs-hebrew.js \
      https://raw.githubusercontent.com/openscriptures/strongs/master/hebrew/strongs-hebrew-dictionary.js
    python3 scripts/load_hebrew.py \
        --morphhb ~/morphhb/wlc \
        --glosses ~/strongs-hebrew.js \
        --out ~/bible-db/heb.db \
        Jonah                 # load ONE book first; omit the name to load all 39

Columns mirror the non-canon <book>_words pattern so the reader can eat the same shape.
"""
import argparse
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

OSIS_NS = "http://www.bibletechnologies.net/2003/OSIS/namespace"

# morphhb file / osisID name  ->  the book id the app already uses (BOOK_ORDER, 00-core.jsx)
OSIS_TO_APP = {
    "Gen": "Gen", "Exod": "Exo", "Lev": "Lev", "Num": "Num", "Deut": "Deu",
    "Josh": "Jos", "Judg": "Jdg", "Ruth": "Rth", "1Sam": "1Sa", "2Sam": "2Sa",
    "1Kgs": "1Ki", "2Kgs": "2Ki", "1Chr": "1Ch", "2Chr": "2Ch", "Ezra": "Ezr",
    "Neh": "Neh", "Esth": "Est", "Job": "Job", "Ps": "Psa", "Prov": "Pro",
    "Eccl": "Ecc", "Song": "Son", "Isa": "Isa", "Jer": "Jer", "Lam": "Lam",
    "Ezek": "Eze", "Dan": "Dan", "Hos": "Hos", "Joel": "Joe", "Amos": "Amo",
    "Obad": "Oba", "Jonah": "Jon", "Mic": "Mic", "Nah": "Nah", "Hab": "Hab",
    "Zeph": "Zep", "Hag": "Hag", "Zech": "Zec", "Mal": "Mal",
}

# Cantillation (chanting) accents + structural marks we DROP. We KEEP the niqqud
# (vowel points U+05B0-05BC, the shin/sin dots U+05C1/05C2, qamats-qatan U+05C7).
_DROP = set(range(0x0591, 0x05B0))  # te'amim / cantillation accents
_DROP |= {0x05BD, 0x05BF, 0x05C0, 0x05C3, 0x05C4, 0x05C5, 0x05C6}  # meteg/rafe/paseq/sof-pasuq/...


def clean_hebrew(text):
    # morphhb splits prefixes/suffixes with "/" inside the word — join them, drop accents.
    text = text.replace("/", "")
    return "".join(ch for ch in text if ord(ch) not in _DROP).strip()


def main_strongs(lemma):
    # lemma looks like "c/1961", "1121 a", "d/5892 b", "m/l/6440", or just "b".
    # The single letters are prefix particles; the content word is the number.
    if not lemma:
        return None
    first = lemma.split()[0]                       # drop the " a"/" b" homonym marker
    nums = [p for p in first.split("/") if p.isdigit()]
    return ("H" + nums[-1]) if nums else None      # content piece is the last number


def load_glosses(path):
    # Optional. Accepts the openscriptures file either way: a plain .json, or the .js
    # that wraps it as `var strongsHebrewDictionary = { ... };` (we just slice from the
    # first "{" to the last "}"). A missing or unreadable file is not fatal — the Hebrew
    # still loads, just with no English line for now.
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        print(f"note: gloss file '{path}' not found — loading Hebrew with no English glosses for now")
        return {}
    try:
        text = p.read_text(encoding="utf-8")
        i, j = text.find("{"), text.rfind("}")
        raw = json.loads(text[i:j + 1])
    except Exception as e:
        print(f"note: could not read glosses ({e}) — continuing without")
        return {}
    out = {}
    for key, entry in raw.items():                 # key = "H1", "H430", ...
        g = (entry.get("strongs_def") or entry.get("kjv_def") or "").strip()
        g = g.split(";")[0].strip()                # keep the core sense, drop the elaboration
        if len(g) > 32:                            # ...and trim a long definition to its head word(s)
            g = g.split(",")[0].strip()
        if g:
            out[key] = re.sub(r"\s+", " ", g)
    return out


def parse_book(xml_path, glosses):
    tree = ET.parse(xml_path)
    wtag, vtag = f"{{{OSIS_NS}}}w", f"{{{OSIS_NS}}}verse"
    wrows, vrows = [], []
    for verse in tree.iter(vtag):
        osis = verse.get("osisID")                 # "Jonah.1.1"
        if not osis:
            continue
        bk, ch, vs = osis.split(".")
        app_book = OSIS_TO_APP.get(bk)
        if not app_book:
            continue
        ch, vs = int(ch), int(vs)
        pos, words = 0, []
        for child in verse:
            if child.tag != wtag:                  # skip <seg> punctuation (maqaf, sof-pasuq)
                continue
            heb = clean_hebrew("".join(child.itertext()))
            if not heb:
                continue
            sn = main_strongs(child.get("lemma", ""))
            morph = child.get("morph", "")
            gloss = glosses.get(sn, "") if sn else ""
            wrows.append((app_book, ch, vs, pos, heb, sn, morph, gloss))
            words.append(heb)
            pos += 1
        vrows.append((app_book, ch, vs, " ".join(words)))
    return wrows, vrows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--morphhb", required=True, help="path to the morphhb wlc/ directory")
    ap.add_argument("--out", required=True, help="output heb.db path")
    ap.add_argument("--glosses", help="Strong's Hebrew dict, .js or .json (optional but recommended)")
    ap.add_argument("books", nargs="*", help="OSIS book names to load (default: all 39)")
    args = ap.parse_args()

    glosses = load_glosses(args.glosses)
    wlc = Path(args.morphhb)
    books = args.books or list(OSIS_TO_APP.keys())

    conn = sqlite3.connect(args.out)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS heb_words (
            book TEXT, chapter INTEGER, verse INTEGER, position INTEGER,
            hebrew TEXT, strongs TEXT, morph TEXT, gloss TEXT
        );
        CREATE TABLE IF NOT EXISTS heb_verses (
            book TEXT, chapter INTEGER, verse INTEGER, hebrew TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_heb_words_bcv  ON heb_words(book, chapter, verse);
        CREATE INDEX IF NOT EXISTS idx_heb_verses_bcv ON heb_verses(book, chapter, verse);
    """)

    total = 0
    for osis in books:
        app_book = OSIS_TO_APP.get(osis)
        if not app_book:
            print(f"skip unknown book '{osis}'")
            continue
        xml_path = wlc / f"{osis}.xml"
        if not xml_path.exists():
            print(f"missing {xml_path}")
            continue
        # clear just this book in this isolated db, then refill (so re-running is safe)
        cur.execute("DELETE FROM heb_words  WHERE book=?", (app_book,))
        cur.execute("DELETE FROM heb_verses WHERE book=?", (app_book,))
        wrows, vrows = parse_book(xml_path, glosses)
        cur.executemany("INSERT INTO heb_words  VALUES (?,?,?,?,?,?,?,?)", wrows)
        cur.executemany("INSERT INTO heb_verses VALUES (?,?,?,?)", vrows)
        total += len(wrows)
        print(f"{osis:6} -> {app_book:4}  {len(wrows):6} words  {len(vrows):4} verses")

    conn.commit()
    nomatch = cur.execute("SELECT count(*) FROM heb_words WHERE strongs IS NULL").fetchone()[0]
    conn.close()
    print(f"done: {total} Hebrew words; {nomatch} with no Strong's (prefix/suffix-only words — expected)")


if __name__ == "__main__":
    main()
