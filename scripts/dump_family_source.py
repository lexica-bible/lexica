#!/usr/bin/env python3
"""dump_family_source.py — READ-ONLY. The ABP SOURCE line is the arbiter.

For each exemplar verse, print four lines side by side so you can read off which
parser deviated (not judge taste):
  1. SOURCE  — the raw abp_texts line, brackets + order digits + G-numbers as stored
  2. PROSE   — verses.text (what load_abp_prose.clean_verse produced) [the trusted side]
  3. RECHECK — clean_verse(SOURCE) recomputed here, to CONFIRM verses.text == the parser
  4. WORDS   — the reader's reassembly (reorder_english port over the word rows)

A family self-adjudicates when the source is unambiguous (each bracket has distinct
digits, no nesting). AMBIGUOUS is flagged when a bracket repeats a digit or nests —
those need a printed-ABP tiebreak.

Usage (on PA, from ~/bible-db — needs abp_texts/ + bible.db):
  python3 scripts/dump_family_source.py bible.db
  python3 scripts/dump_family_source.py bible.db "Jer 48:1" "Mat 21:19"   # custom refs
"""
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_abp_prose import VERSE_RE, clean_verse, ABP_DIRS
from reorder_english import get_english_order_words

# one exemplar per family (from the v2 --list), + the two named verses
DEFAULT = [
    ("Jer 48:1",  "forces + doubled-the (the arbiter case)"),
    ("Jer 19:15", "forces family"),
    ("Mat 16:16", "the-Christ family"),
    ("Rom 9:17",  "same family"),
    ("Gen 7:1",   "pronoun-fronting family"),
    ("Mat 26:16", "verb-particle 'up X' family"),
    ("Heb 10:8",  "paren-edge family"),
    ("Mat 21:19", "content-other apparatus leak (cited by G1096)"),
]

_DIGIT = re.compile(r"^\s*(\d+)")


def source_line(book, ch, vs):
    """Return the raw abp_texts text for a ref (the part after '(Book ch:v) '), or None."""
    for d in ABP_DIRS:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.txt")):
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    m = VERSE_RE.match(line.strip())
                    if m and m.group(1) == book and int(m.group(2)) == ch and int(m.group(3)) == vs:
                        return m.group(4)
    return None


def ambiguity(raw):
    """Flag a bracket group whose source notation can't self-adjudicate."""
    flags = []
    for grp in re.findall(r"\[([^\]]*)\]", raw or ""):
        if "[" in grp:
            flags.append("nested bracket")
        digits = [int(d.group(1)) for it in re.split(r"\s+(?=\d)", grp.strip())
                  if (d := _DIGIT.match(it))]
        dup = {x for x in digits if digits.count(x) > 1}
        if dup:
            flags.append(f"duplicate digit {sorted(dup)}")
    return flags


def words_reassembly(conn, book, ch, vs):
    row = conn.execute("SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
                       (book, ch, vs)).fetchone()
    if not row:
        return None
    words = [dict(r) for r in conn.execute(
        "SELECT english, bracket_id, greek_pos, position FROM words "
        "WHERE verse_id=? ORDER BY position", (row[0],))]
    seq = " ".join((w.get("english") or "") for w in get_english_order_words(words))
    return re.sub(r"\s+", " ", seq).strip()


def scan_brackets():
    """READ-ONLY. Every abp_texts source line whose brackets don't balance — an
    unmatched ']' is the malformed shape that leaks order digits into verses.text
    (Mat 21:19 class). Reports ref + the raw line so the leak class is fully known."""
    print("== unmatched-bracket scan of abp_texts (READ-ONLY) ==\n")
    n = 0
    for d in ABP_DIRS:
        if not d.exists():
            print(f"  ({d} not found)")
            continue
        for f in sorted(d.glob("*.txt")):
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    m = VERSE_RE.match(line.strip())
                    if not m:
                        continue
                    raw = m.group(4)
                    if raw.count("[") != raw.count("]"):
                        n += 1
                        print(f"  {m.group(1)} {m.group(2)}:{m.group(3)}  "
                              f"([={raw.count('[')} ]={raw.count(']')})")
                        print(f"    {raw}")
    print(f"\n  {n} verses with unmatched brackets.")


def main():
    args = sys.argv[1:]
    if "--scan-brackets" in args:
        scan_brackets()
        return
    db = next((a for a in args if not a.startswith("--")), "bible.db")
    custom = [a for a in args[1:] if not a.startswith("--")]
    refs = [(r, "custom") for r in custom] if custom else DEFAULT

    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    print("== family source dump (READ-ONLY) — SOURCE line is the arbiter ==\n")
    for ref, label in refs:
        parts = ref.split()
        book = " ".join(parts[:-1])
        ch, vs = (int(x) for x in parts[-1].split(":"))
        raw = source_line(book, ch, vs)
        vt = conn.execute("SELECT text FROM verses WHERE book=? AND chapter=? AND verse=?",
                          (book, ch, vs)).fetchone()
        vt = vt[0] if vt else None
        print(f"=== {ref}   [{label}] ===")
        if raw is None:
            print("  SOURCE : (not found in abp_texts — check book abbrev / versification)\n")
            continue
        print(f"  SOURCE : {raw}")
        print(f"  PROSE  : {vt}")
        recheck = clean_verse(raw)
        flag = " (differs from verses.text!)" if recheck != vt else ""
        print(f"  RECHECK: {recheck}{flag}")
        print(f"  WORDS  : {words_reassembly(conn, book, ch, vs)}")
        amb = ambiguity(raw)
        print(f"  ARBITER: {'AMBIGUOUS -> printed-ABP tiebreak: ' + '; '.join(amb) if amb else 'self-adjudicates (unambiguous source)'}")
        print()
    conn.close()


if __name__ == "__main__":
    main()
