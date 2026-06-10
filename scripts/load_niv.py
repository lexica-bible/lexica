#!/usr/bin/env python3
"""Load the NIV reading text into niv.db — PERSONAL, owner-only.

The NIV is Biblica/Zondervan-copyrighted; this is for the OWNER's private study,
gated to his account by views_niv.py (404 to everyone else). niv.db is kept OUT of
bible.db and OUT of git (*.db is gitignored), and lives on PythonAnywhere only —
NEVER commit it. Same deal as the ESV (scripts/load_esv.py); the only difference
is the SOURCE format (JSON instead of the ESV's markdown).

Source: the aruljohn/Bible-niv repo (https://github.com/aruljohn/Bible-niv) — 66
JSON files, one per book, named like "Genesis.json", "1 Samuel.json",
"Song Of Solomon.json", plus a Books.json index this loader ignores. Each book
file looks like:

    {
      "book": "Genesis",
      "count": "50",
      "chapters": [
        { "chapter": 1, "verses": [ { "verse": 1, "text": "In the beginning ..." } ] }
      ]
    }

This loader reads every *.json (skipping Books.json), maps each file's "book"
field to its 1-66 canonical number, and fills ONE table —
niv_verses(book_id, chapter, verse_num, verse_text). The 1-66 ids match
kjv_verses / bsb_verses / esv_verses, so the web app finds a chapter by the same
book id. It never touches any other file. Safe to re-run (INSERT OR REPLACE).

Usage (on PA, after cloning Bible-niv somewhere):
    python3 scripts/load_niv.py /path/to/Bible-niv [niv.db]

If the db path is omitted it writes ./niv.db next to where you run it — point it
at ~/bible-db/niv.db so the web app finds it (core.NIV_DB).
"""
import json
import os
import re
import sqlite3
import sys

# Standard 66-book canonical order — index+1 is the book id (Genesis=1 .. Revelation=66),
# matching kjv_verses / bsb_verses / esv_verses and app.py's _KJV_BOOK_ID.
_CANON = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges",
    "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles",
    "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations",
    "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
    "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi", "Matthew",
    "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians",
    "Galatians", "Ephesians", "Philippians", "Colossians", "1 Thessalonians",
    "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews",
    "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude",
    "Revelation",
]


def _norm(name):
    """Lowercase + strip everything but letters/digits, so 'Song Of Solomon',
    'Song of Solomon' and '1 Samuel'/'1Samuel' all match the same key."""
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


# normalized book name -> 1-66 id. Also map a couple of common alternate spellings.
_NAME_TO_ID = {_norm(n): i + 1 for i, n in enumerate(_CANON)}
_NAME_TO_ID.setdefault(_norm("Song of Songs"), _NAME_TO_ID[_norm("Song of Solomon")])
_NAME_TO_ID.setdefault(_norm("Psalm"), _NAME_TO_ID[_norm("Psalms")])
_NAME_TO_ID.setdefault(_norm("Revelation of John"), _NAME_TO_ID[_norm("Revelation")])


def load_file(path):
    """Yield (chapter, verse, text) from one Bible-niv book JSON file, using the
    file's own 'book' field for the id (returned alongside)."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    book_id = _NAME_TO_ID.get(_norm(data.get("book")))
    rows = []
    for chap in data.get("chapters", []):
        try:
            cnum = int(chap.get("chapter"))
        except (TypeError, ValueError):
            continue
        for v in chap.get("verses", []):
            try:
                vnum = int(v.get("verse"))
            except (TypeError, ValueError):
                continue
            # The aruljohn source uses a backtick (U+0060) where an apostrophe /
            # closing single-quote (U+2019) belongs ("God`s" -> "God's"). Fix that
            # one character so the reading text renders right; the source's curly
            # double-quotes and em-dashes are already correct, so leave them.
            text = (v.get("text") or "").strip().replace("`", "’")
            rows.append((cnum, vnum, text))
    return book_id, data.get("book"), rows


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src_dir = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else "niv.db"

    files = sorted(
        fn for fn in os.listdir(src_dir)
        if fn.lower().endswith(".json") and fn.lower() != "books.json"
    )
    if not files:
        print(f"No book *.json files found in {src_dir}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS niv_verses (
            book_id    INTEGER NOT NULL,
            chapter    INTEGER NOT NULL,
            verse_num  INTEGER NOT NULL,
            verse_text TEXT,
            PRIMARY KEY (book_id, chapter, verse_num)
        )
        """
    )

    inserted = 0
    for fn in files:
        book_id, book_name, rows = load_file(os.path.join(src_dir, fn))
        if book_id is None:
            print(f"  skip {fn}: book name {book_name!r} not in the 66-book canon")
            continue
        for cnum, vnum, text in rows:
            conn.execute(
                "INSERT OR REPLACE INTO niv_verses (book_id, chapter, verse_num, verse_text)"
                " VALUES (?, ?, ?, ?)",
                (book_id, cnum, vnum, text),
            )
        inserted += len(rows)
        print(f"  {fn}: book {book_id} ({book_name}), {len(rows)} verses")

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM niv_verses").fetchone()[0]
    books = conn.execute("SELECT COUNT(DISTINCT book_id) FROM niv_verses").fetchone()[0]
    conn.close()
    print(f"\nNIV verses loaded: {inserted}  (table now holds {total} across {books} books)")


if __name__ == "__main__":
    main()
