#!/usr/bin/env python3
"""check_draw_citations.py — READ-ONLY. Do any shipped definition citations quote a
verse the reassembly-diff flagged?

The draw cache (draws/G####.json, the reviewed-verbatim store the Lexica entries
render from) and the lexica_def table cite verses. If a cited verse is one of the
reassembly-diff hits, that entry may be showing users a mis-ordered reading or baked
apparatus (`1let`, `AndG.`) — so it needs a redraw after the corpus is fixed. This
finds every such collision so the redraw scope is known, not guessed.

Hits come from BOTH v1 (bag) and v2 (order-aware) so nothing is missed. Refs are
matched whether the store writes "Genesis 1:1" or "Gen 1:1".

Usage (on PA, from ~/bible-db):
  python3 scripts/check_draw_citations.py bible.db --draws ~/bible-db/draws
  python3 scripts/check_draw_citations.py bible.db --draws <dir> --list   # every collision

READ ONLY: opens bible.db mode=ro, only reads the draw files.
"""
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit_reassembly_diff import reassembly_hits, reassembly_hits_v2

_ABBREVS = [
    "Gen","Exo","Lev","Num","Deu","Jos","Jdg","Rth","1Sa","2Sa","1Ki","2Ki","1Ch","2Ch",
    "Ezr","Neh","Est","Job","Psa","Pro","Ecc","Son","Isa","Jer","Lam","Eze","Dan","Hos",
    "Joe","Amo","Oba","Jon","Mic","Nah","Hab","Zep","Hag","Zec","Mal","Mat","Mar","Luk",
    "Joh","Act","Rom","1Co","2Co","Gal","Eph","Php","Col","1Th","2Th","1Ti","2Ti","Tit",
    "Phm","Heb","Jas","1Pe","2Pe","1Jn","2Jn","3Jn","Jud","Rev",
]
_FULL = {
    "Gen":"Genesis","Exo":"Exodus","Lev":"Leviticus","Num":"Numbers","Deu":"Deuteronomy",
    "Jos":"Joshua","Jdg":"Judges","Rth":"Ruth","1Sa":"1 Samuel","2Sa":"2 Samuel","1Ki":"1 Kings",
    "2Ki":"2 Kings","1Ch":"1 Chronicles","2Ch":"2 Chronicles","Ezr":"Ezra","Neh":"Nehemiah",
    "Est":"Esther","Job":"Job","Psa":"Psalms","Pro":"Proverbs","Ecc":"Ecclesiastes",
    "Son":"Song of Solomon","Isa":"Isaiah","Jer":"Jeremiah","Lam":"Lamentations","Eze":"Ezekiel",
    "Dan":"Daniel","Hos":"Hosea","Joe":"Joel","Amo":"Amos","Oba":"Obadiah","Jon":"Jonah",
    "Mic":"Micah","Nah":"Nahum","Hab":"Habakkuk","Zep":"Zephaniah","Hag":"Haggai","Zec":"Zechariah",
    "Mal":"Malachi","Mat":"Matthew","Mar":"Mark","Luk":"Luke","Joh":"John","Act":"Acts",
    "Rom":"Romans","1Co":"1 Corinthians","2Co":"2 Corinthians","Gal":"Galatians","Eph":"Ephesians",
    "Php":"Philippians","Col":"Colossians","1Th":"1 Thessalonians","2Th":"2 Thessalonians",
    "1Ti":"1 Timothy","2Ti":"2 Timothy","Tit":"Titus","Phm":"Philemon","Heb":"Hebrews","Jas":"James",
    "1Pe":"1 Peter","2Pe":"2 Peter","1Jn":"1 John","2Jn":"2 John","3Jn":"3 John","Jud":"Jude",
    "Rev":"Revelation",
}
# name (full OR abbrev, also "Song"/"Canticles"-free) -> abbrev
_NAME2ABBR = {}
for ab in _ABBREVS:
    _NAME2ABBR[ab.lower()] = ab
    _NAME2ABBR[_FULL[ab].lower()] = ab
# common alternates a store might use instead of our abbrev/full name
_NAME2ABBR["ps"] = "Psa"
_NAME2ABBR["song"] = "Son"
_NAME2ABBR["song of songs"] = "Son"
# longest names first so "1 Corinthians" beats a stray "1"
_NAMES_SORTED = sorted(_NAME2ABBR, key=len, reverse=True)
_REF_RE = re.compile(r"\b(" + "|".join(re.escape(n) for n in _NAMES_SORTED) +
                     r")\.?\s+(\d+):(\d+)\b", re.IGNORECASE)


def refs_in_text(s):
    """Every (abbrev, chapter, verse) verse ref in a blob of text."""
    out = set()
    for m in _REF_RE.finditer(s or ""):
        ab = _NAME2ABBR.get(m.group(1).lower())
        if ab:
            out.add((ab, int(m.group(2)), int(m.group(3))))
    return out


def hit_index(db):
    """All reassembly hits (v1 ∪ v2) keyed by (abbrev, ch, v) -> class."""
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    idx = {}
    for h in reassembly_hits(conn):          # v1 (bag) — has no 'klass' split, tag generically
        b, cv = h["ref"].rsplit(" ", 1)
        ch, v = cv.split(":")
        idx.setdefault((b, int(ch), int(v)), h["klass"])
    for h in reassembly_hits_v2(conn):       # v2 (order-aware) — authoritative class wins
        b, cv = h["ref"].rsplit(" ", 1)
        ch, v = cv.split(":")
        idx[(b, int(ch), int(v))] = h["klass"]
    conn.close()
    return idx


def scan_draws(draws_dir):
    """{ (abbrev,ch,v) -> set(source labels) } for every verse cited in a draw file."""
    cites = defaultdict(set)
    d = Path(draws_dir).expanduser()
    if not d.is_dir():
        print(f"  (draws dir not found: {d} — skipping draw cache)")
        return cites
    n = 0
    for f in sorted(d.glob("*.json")):
        n += 1
        try:
            blob = f.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  (unreadable: {f.name}: {e})")
            continue
        for ref in refs_in_text(blob):
            cites[ref].add(f.stem)
    print(f"  scanned {n} draw files in {d}")
    return cites


def scan_lexica_def(db):
    """Same, for any text columns in the lexica_def table (deploy-safe if absent)."""
    cites = defaultdict(set)
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    has = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='lexica_def'").fetchone()
    if not has:
        conn.close()
        print("  (no lexica_def table — skipping)")
        return cites
    cols = [r[1] for r in conn.execute("PRAGMA table_info(lexica_def)")]
    textcols = [c for c in cols if c not in ("id",)]
    key = "strongs" if "strongs" in cols else cols[0]
    n = 0
    for row in conn.execute(f"SELECT {key} AS k, {', '.join(textcols)} FROM lexica_def"):
        n += 1
        blob = " ".join(str(row[c]) for c in textcols if row[c] is not None)
        for ref in refs_in_text(blob):
            cites[ref].add(f"lexica_def:{row['k']}")
    conn.close()
    print(f"  scanned {n} lexica_def rows")
    return cites


def main():
    args = sys.argv[1:]
    db = next((a for a in args if not a.startswith("--")), "bible.db")
    draws = args[args.index("--draws") + 1] if "--draws" in args else "draws"
    list_all = "--list" in args

    print(f"== draw-citation collision check on {db} (READ-ONLY) ==")
    idx = hit_index(db)
    print(f"   reassembly hits (v1 ∪ v2): {len(idx):,}")
    cites = scan_draws(draws)
    for k, v in scan_lexica_def(db).items():
        cites[k] |= v

    collisions = []
    for ref, klass in idx.items():
        if ref in cites:
            collisions.append((ref, klass, sorted(cites[ref])))

    by_class = defaultdict(int)
    for _, klass, _ in collisions:
        by_class[klass] += 1

    print(f"\n   COLLISIONS (a flagged verse cited by a shipped entry): {len(collisions)}")
    for k in ("content-other", "word-order", "punct-position", "punct-shift", "dup-gloss"):
        if by_class.get(k):
            print(f"     {k:<15} {by_class[k]:>5}")
    if not collisions:
        print("     none — no shipped entry cites a flagged verse. No redraw needed.")
    else:
        show = collisions if list_all else collisions[:40]
        print(f"\n   {'(all)' if list_all else 'first 40'}:")
        for (b, ch, v), klass, srcs in sorted(show):
            print(f"     [{klass:<14}] {b} {ch}:{v:<4} <- {', '.join(srcs)}")
        if not list_all and len(collisions) > 40:
            print(f"     ... {len(collisions) - 40} more (--list for all)")


if __name__ == "__main__":
    main()
