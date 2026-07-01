#!/usr/bin/env python3
"""Deprecate the imported Nave's/MetaV CONCEPT topics (PA-only, study.db).

The ~1817 concept topics (Faith, Grace, Trinity, …) were bulk-imported from Nave's/MetaV
and are no longer used. This SOFT-DELETES them (sets deleted=1) so they vanish from every
view — including the admin Topics list, whose query filters deleted=0 (verified) — while the
rows survive in study.db, so it's fully undoable.

SURGICAL TARGET: type='topic' AND the json body's source == 'metav'.
  - Divine Council (type='topic', source='' blank, id 'divine_council') is NOT caught. KEPT.
  - Name-topics (type='name', ids 'metavn_*') are NOT caught. KEPT (they feed the Library
    Nave's sidebar block).
  - Graphs / Seams are a different type. Untouched.

Backs up study.db first (SQLite online .backup — safe on a live db). Dry-run by default.

    workon bible-env
    python scripts/deprecate_concept_topics.py            # DRY RUN: show what would go, write nothing
    python scripts/deprecate_concept_topics.py --apply    # back up, then soft-delete
    python scripts/deprecate_concept_topics.py --undo --apply   # bring them all back (deleted=0)

After --apply, reload the site: touch /var/www/www_lexica_bible_wsgi.py
"""
import argparse
import json
import os
import sqlite3
import sys
import time

# scripts/ live one level below the app root, where core.py sits.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import STUDY_DB, study_db


def _is_concept(row):
    """True for an imported concept topic: type='topic' AND json source == 'metav'."""
    if row["type"] != "topic":
        return False
    try:
        data = json.loads(row["json"]) or {}
    except (ValueError, TypeError):
        data = {}
    return (data.get("source") or "").strip().lower() == "metav"


def _backup():
    """Timestamped online snapshot of study.db beside it. Safe while the app runs."""
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    dest_path = STUDY_DB + ".pre-deprecate-" + stamp + ".bak"
    src = sqlite3.connect(STUDY_DB)
    dst = sqlite3.connect(dest_path)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    return dest_path


def main():
    ap = argparse.ArgumentParser(description="Soft-delete the imported Nave's concept topics.")
    ap.add_argument("--apply", action="store_true", help="write the change (default is dry-run)")
    ap.add_argument("--undo", action="store_true", help="reverse: bring the concept topics back (deleted=0)")
    args = ap.parse_args()

    conn = study_db()
    try:
        # Look at BOTH live and already-soft-deleted rows so --undo can see them.
        rows = conn.execute(
            "SELECT id, type, title, json, status, deleted FROM entries WHERE type='topic'"
        ).fetchall()
        concept = [r for r in rows if _is_concept(r)]
        kept = [r for r in rows if not _is_concept(r)]        # hand-authored topics (Divine Council etc.)

        if args.undo:
            targets = [r for r in concept if r["deleted"]]
            action, new_deleted = "RESTORE", 0
        else:
            targets = [r for r in concept if not r["deleted"]]
            action, new_deleted = "SOFT-DELETE", 1

        print("Concept topics (type='topic', source='metav'): %d total" % len(concept))
        print("Hand-authored topics KEPT (blank source): %d" % len(kept))
        for r in kept[:20]:
            print("    KEEP  %-28s  %s" % (r["id"], r["title"]))
        print("\n%s target rows: %d" % (action, len(targets)))
        for r in targets[:15]:
            print("    %s  %-28s  %s" % (action[:4], r["id"], r["title"]))
        if len(targets) > 15:
            print("    … and %d more" % (len(targets) - 15))

        if not targets:
            print("\nNothing to do.")
            return
        if not args.apply:
            print("\nDRY RUN — nothing written. Re-run with --apply to proceed.")
            return

        if not args.undo:
            path = _backup()
            print("\nBacked up study.db -> %s" % path)

        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        ids = [r["id"] for r in targets]
        for chunk_start in range(0, len(ids), 400):
            chunk = ids[chunk_start:chunk_start + 400]
            q = ("UPDATE entries SET deleted=?, updated=? WHERE id IN (%s)"
                 % ",".join("?" * len(chunk)))
            conn.execute(q, [new_deleted, now, *chunk])
        conn.commit()
        print("%s applied to %d rows." % (action, len(targets)))
        print("Reload the site: touch /var/www/www_lexica_bible_wsgi.py")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
