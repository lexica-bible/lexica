#!/usr/bin/env python3
"""Precompute the number-neutral form of every English rendering, for the Word-study
English finder (/api/lexicon/english).

Adds an indexed `*_norm` column to each rendering table, filled with
number_fold.normalize(rendering). The finder then matches
    <col>_norm = ? COLLATE NOCASE   with param normalize(query)
so the query and the stored rendering pass through the IDENTICAL function — no inverse,
no candidate generation. See number_fold.py + tests/test_number_fold.py.

  words.english_head   -> words.english_head_norm
  kjv_words.word       -> kjv_words.word_norm
  bsb_words.word       -> bsb_words.word_norm

Idempotent + additive: creates the column/index only if missing, then recomputes it.
Safe to re-run any time; the live search is unaffected until the endpoint is wired to
the new columns. Reversible: `ALTER TABLE <t> DROP COLUMN <c>` undoes it.

PA-only data step (bible.db is not local). Usage:
    python3 scripts/build_rendering_norm.py ~/bible-db/bible.db
    python3 scripts/build_rendering_norm.py ~/bible-db/bible.db --stats   # report only
"""
import argparse
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from number_fold import normalize

# (table, source rendering column, new norm column, index name)
TARGETS = [
    ("words",     "english_head", "english_head_norm", "idx_words_ehnorm"),
    ("kjv_words", "word",         "word_norm",         "idx_kjvwords_norm"),
    ("bsb_words", "word",         "word_norm",         "idx_bsbwords_norm"),
]


def _table_exists(conn, table):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def _has_column(conn, table, col):
    return any(r[1] == col for r in conn.execute(f"PRAGMA table_info({table})").fetchall())


def _norm_or_none(s):
    # UDF wrapper: normalize() only for real single renderings; leave blanks alone.
    if s is None:
        return None
    s = s.strip()
    return normalize(s) if s else None


def recompute_norms(conn, only=None, log=print):
    """Create (if missing) and refill the norm column(s). `only` = a table name to do
    just one (used by the per-loader recompute); None = all three. Returns a dict of
    per-table row counts touched. Caller commits."""
    conn.create_function("rnorm", 1, _norm_or_none)
    counts = {}
    for table, src, norm_col, idx in TARGETS:
        if only and table != only:
            continue
        if not _table_exists(conn, table):
            log(f"  {table}: not present — skipped.")
            continue
        if not _has_column(conn, table, norm_col):
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {norm_col} TEXT")
            log(f"  {table}: added column {norm_col}.")
        # COLLATE NOCASE index so `{norm_col} = ? COLLATE NOCASE` in the finder is indexed.
        conn.execute(f"CREATE INDEX IF NOT EXISTS {idx} ON {table}({norm_col} COLLATE NOCASE)")
        n = conn.execute(
            f"UPDATE {table} SET {norm_col} = rnorm({src}) "
            f"WHERE {src} IS NOT NULL AND {src} != ''"
        ).rowcount
        counts[table] = n
        log(f"  {table}: recomputed {n:,} {norm_col} value(s).")
    return counts


def stats(conn, log=print):
    for table, src, norm_col, _ in TARGETS:
        if not _table_exists(conn, table) or not _has_column(conn, table, norm_col):
            log(f"  {table}: {norm_col} not built yet.")
            continue
        total = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {norm_col} IS NOT NULL").fetchone()[0]
        keys = conn.execute(f"SELECT COUNT(DISTINCT {norm_col}) FROM {table} WHERE {norm_col} IS NOT NULL").fetchone()[0]
        forms = conn.execute(f"SELECT COUNT(DISTINCT {src}) FROM {table} WHERE {src} IS NOT NULL AND {src} != ''").fetchone()[0]
        log(f"  {table}: {total:,} rows normed · {forms:,} distinct renderings -> {keys:,} distinct keys")


def main():
    ap = argparse.ArgumentParser(description="Backfill *_norm rendering columns for the Word-study finder")
    ap.add_argument("db", nargs="?", default="bible.db")
    ap.add_argument("--stats", action="store_true", help="report only, no writes")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        if args.stats:
            print("── Rendering-norm stats ──")
            stats(conn)
        else:
            print(f"Backfilling rendering-norm columns in {args.db} …")
            recompute_norms(conn)
            conn.commit()
            print("── After ──")
            stats(conn)
            print("Done. Reversible with: ALTER TABLE <t> DROP COLUMN <norm_col>.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
