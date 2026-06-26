#!/usr/bin/env python3
"""
add_lemma_plain.py — add an indexed, accent-stripped lemma column to lexicon + bdb so
the Word-study search can match a word EXACTLY and FAST.

Why: /api/lexicon/lookup matched a typed Greek/Hebrew word with a substring LIKE on the
accent-stripped lemma (`strip_accents(lower(lemma)) LIKE '%ινα%'`). A leading-wildcard
LIKE can't use an index, so every search was a full scan calling a Python function on
every row — AND it over-matched (ἵνα pulled in γάγγραινα, εἶναι, Σινᾶ …, anything
CONTAINING "ινα", unranked). This stores the normalized form ONCE in `lemma_plain` and
indexes it, so the lookup can do `WHERE lemma_plain = ?` — instant and exact.

`lemma_plain` = the lemma with combining accents/points stripped, lowercased, hyphens
removed, final sigma ς folded to σ. Same normalization as views_lexicon._norm_lemma and
the lsj.plain precedent, so a word typed with or without accents matches by equality.

Additive + re-runnable: only ADDS a column + index and recomputes values; never drops or
edits existing data. Read-only by default; pass --apply to write. PA-only (bible.db is on
PA). The lexicon side is also folded into scripts/load_lexicon.py, so a lexicon reload
reproduces it; bdb has no in-repo loader, so RE-RUN this after any bdb reload.

  python3 scripts/add_lemma_plain.py bible.db            # dry run (counts only)
  python3 scripts/add_lemma_plain.py bible.db --apply    # write column + index
"""
import argparse
import sqlite3
import unicodedata

# (table, lemma column, primary-key column)
TARGETS = [("lexicon", "lemma", "strongs"), ("bdb", "lemma", "strongs_id")]


def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s or "")
                if unicodedata.category(c) != "Mn")
    return s.lower().replace("-", "").replace("ς", "σ")


def build(conn, table, lemma_col, key_col, apply=False, log=print):
    cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if not cols:
        log(f"  {table}: table not found — skipped")
        return 0
    rows = conn.execute(f"SELECT {key_col}, {lemma_col} FROM {table}").fetchall()
    nonblank = sum(1 for r in rows if norm(r[1]))
    log(f"  {table}: {len(rows):,} rows, {nonblank:,} with a non-blank lemma"
        f"{'' if 'lemma_plain' in cols else '  (column will be ADDED)'}")
    if apply:
        if "lemma_plain" not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN lemma_plain TEXT")
        conn.executemany(
            f"UPDATE {table} SET lemma_plain=? WHERE {key_col}=?",
            [(norm(r[1]), r[0]) for r in rows],
        )
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{table}_lemma_plain ON {table}(lemma_plain)")
    return nonblank


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--apply", action="store_true", help="write the column + index (default = dry run)")
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    print(f"{'' if args.apply else '[DRY RUN] '}add_lemma_plain → {args.db}")
    for table, lemma_col, key_col in TARGETS:
        build(conn, table, lemma_col, key_col, apply=args.apply)
    if args.apply:
        conn.commit()
        print("Done — lemma_plain built + indexed.")
    else:
        print("DRY RUN: re-run with --apply to write.")
    conn.close()


if __name__ == "__main__":
    main()
