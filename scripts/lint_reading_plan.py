#!/usr/bin/env python3
"""Lint the chronological reading plan against the ABP corpus.

READ-ONLY. Checks EVERY day of static/chronological.json:

  1. every day's `pos` entries point at a real passage,
  2. every passage's book abbrev is a canonical Bible book,
  3. every passage's verse window resolves to >= 1 verse in bible.db `verses`
     (the ABP anchor text the reader + day-intro read).

A passage that resolves to zero verses is why a day "fails to open" — the reader
lands on a chapter the corpus has no rows for. The classic case is ABP following
the Septuagint order: Jeremiah's oracles-against-the-nations (Masoretic ch. 46-51)
are renumbered/relocated, so a plan row that says "Jeremiah 47-48" finds nothing.

Usage (on PA, where bible.db lives):
    python3 scripts/lint_reading_plan.py                 # default db path
    python3 scripts/lint_reading_plan.py /path/bible.db

Exit code 0 = clean, 1 = at least one broken passage/day (so it can gate CI later).
"""
import json
import os
import sqlite3
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CHRONO_JSON = os.path.join(_HERE, "..", "static", "chronological.json")
_DEFAULT_DB = os.path.expanduser("~/bible-db/bible.db")

# The canonical Bible book abbreviations the app uses (00-core.jsx BOOK_ORDER).
CANON = set(
    "Gen Exo Lev Num Deu Jos Jdg Rth 1Sa 2Sa 1Ki 2Ki 1Ch 2Ch Ezr Neh Est Job "
    "Psa Pro Ecc Son Isa Jer Lam Eze Dan Hos Joe Amo Oba Jon Mic Nah Hab Zep "
    "Hag Zec Mal Mat Mar Luk Joh Act Rom 1Co 2Co Gal Eph Php Col 1Th 2Th 1Ti "
    "2Ti Tit Phm Heb Jas 1Pe 2Pe 1Jn 2Jn 3Jn Jud Rev".split()
)


def window_count(conn, p):
    """Verses in bible.db `verses` for one passage's window (same predicate the
    reader/day-intro use)."""
    row = conn.execute(
        """SELECT count(*) FROM verses
           WHERE book = ?
             AND (chapter > ? OR (chapter = ? AND verse >= ?))
             AND (chapter < ? OR (chapter = ? AND verse <= ?))""",
        (p["book"], p["start_ch"], p["start_ch"], p["start_v"],
         p["end_ch"], p["end_ch"], p["end_v"]),
    ).fetchone()
    return row[0]


def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_DB
    with open(_CHRONO_JSON, encoding="utf-8") as f:
        data = json.load(f)
    passages = data.get("passages", [])
    days = data.get("days", [])

    if not os.path.exists(db_path):
        print("ERROR: db not found: %s" % db_path)
        print("(run this on PythonAnywhere where bible.db lives)")
        return 2
    conn = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
    conn.row_factory = sqlite3.Row

    problems = []   # (day, pos, label, reason)
    for d in days:
        day = d["day"]
        pos_list = d.get("pos", [])
        for q in pos_list:
            if not (1 <= q <= len(passages)):
                problems.append((day, q, "<none>", "pos out of range"))
                continue
            p = passages[q - 1]
            if p["book"] not in CANON:
                problems.append((day, q, p.get("label", ""), "unknown book '%s'" % p["book"]))
                continue
            try:
                n = window_count(conn, p)
            except Exception as exc:
                problems.append((day, q, p.get("label", ""), "query error: %s" % exc))
                continue
            if n == 0:
                problems.append((day, q, p.get("label", ""),
                                 "0 verses in corpus (book=%s ch %s:%s-%s:%s)"
                                 % (p["book"], p["start_ch"], p["start_v"], p["end_ch"], p["end_v"])))
    conn.close()

    print("Reading-plan lint  —  %d days / %d passages  —  db: %s"
          % (len(days), len(passages), db_path))
    if not problems:
        print("CLEAN: every day resolves to >= 1 verse in the corpus.")
        return 0

    bad_days = sorted({d for d, *_ in problems})
    print("FOUND %d broken passage(s) across %d day(s): %s\n"
          % (len(problems), len(bad_days), ", ".join(str(x) for x in bad_days)))
    for day, pos, label, reason in problems:
        print("  Day %-3d  pos %-4s  %-28s  -> %s" % (day, pos, label, reason))
    return 1


if __name__ == "__main__":
    sys.exit(main())
