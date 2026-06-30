#!/usr/bin/env python3
"""
fix_backref_why.py — one-time scrub of back-reference reasons in news.db.

Older scorer runs let Haiku prefix a reason with a pointer at another article
in the batch ("Same event as 986—police shelving blasphemy law is a setback...").
That id is meaningless to a reader and showed up in the card body (ai_why).

score_news.py now strips this at write time (_clean_why), so NEW rows are clean.
This script applies the SAME cleaner to rows already stored. It imports
_clean_why from score_news so the scrub and the live guard can never drift.

Reversible: --apply backs up every changed row's old ai_why into a side table
(backref_why_backup) first, so you can restore. Dry-run by default.

USAGE  (run on PA, where news.db lives)
  python3 scripts/news/fix_backref_why.py            # dry run: show what would change
  python3 scripts/news/fix_backref_why.py --apply    # back up + scrub
  python3 scripts/news/fix_backref_why.py --restore   # undo from the backup table
"""
import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score_news import _clean_why  # noqa: E402  (same cleaner the scorer uses)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB = os.path.join(REPO_ROOT, "news.db")

APPLY = "--apply" in sys.argv
RESTORE = "--restore" in sys.argv
DB_PATH = DEFAULT_DB
for a in sys.argv:
    if a.startswith("--db="):
        DB_PATH = a.split("=", 1)[1]


def restore(conn):
    have = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='backref_why_backup'"
    ).fetchone()
    if not have:
        print("no backref_why_backup table — nothing to restore.")
        return
    n = conn.execute(
        "UPDATE items SET ai_why=(SELECT ai_why FROM backref_why_backup b WHERE b.id=items.id) "
        "WHERE id IN (SELECT id FROM backref_why_backup)").rowcount
    conn.commit()
    print(f"restored {n} rows from backref_why_backup.")


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if RESTORE:
        restore(conn)
        conn.close()
        return

    rows = conn.execute("SELECT id, ai_why FROM items "
                        "WHERE ai_why IS NOT NULL AND ai_why <> ''").fetchall()
    changes = []
    for r in rows:
        new = _clean_why(r["ai_why"])
        if new != r["ai_why"]:
            changes.append((r["id"], r["ai_why"], new))

    print(f"{'APPLY' if APPLY else 'DRY RUN'} — {len(changes)} reason(s) to clean "
          f"in {DB_PATH}\n")
    for cid, old, new in changes:
        print(f"  id={cid}")
        print(f"    OLD: {old}")
        print(f"    NEW: {new or '(blank)'}")

    if not changes:
        print("nothing to clean.")
        conn.close()
        return

    if not APPLY:
        print("\n(dry run) re-run with --apply to back up + scrub.")
        conn.close()
        return

    # Back up the rows we're about to change, then scrub.
    conn.execute("DROP TABLE IF EXISTS backref_why_backup")
    conn.execute("CREATE TABLE backref_why_backup (id INTEGER PRIMARY KEY, ai_why TEXT)")
    conn.executemany("INSERT INTO backref_why_backup (id, ai_why) VALUES (?, ?)",
                     [(cid, old) for cid, old, _ in changes])
    conn.executemany("UPDATE items SET ai_why=? WHERE id=?",
                     [(new, cid) for cid, _, new in changes])
    conn.commit()
    conn.close()
    print(f"\nscrubbed {len(changes)} rows. Old values saved in backref_why_backup "
          "(--restore to undo). Refresh the News tab to rebuild the cards.")


if __name__ == "__main__":
    main()
