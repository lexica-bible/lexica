#!/usr/bin/env python3
"""Add a hand-authored Study TOPIC straight into study.db (PA-only).

For studies you write yourself (NOT the Nave's/MetaV import) — e.g. Divine Council.
You give it a title + sections of verse REFERENCES; it resolves each reference to ABP
prose (KJV fallback) exactly the way the Study tab does, so a dry run shows you the real
text before anything is written. Re-running REPLACES the same topic (stable id), so it's
safe to tweak the list and run again.

    workon bible-env                              # needs the app's packages
    python scripts/add_study_topic.py             # DRY RUN: resolve + print, write nothing
    python scripts/add_study_topic.py --apply     # write it to study.db (published)

It reuses the app's own resolver (views_study), so the dry-run text == what readers see.
To author the NEXT study, copy this file and edit TITLE / TOPIC_ID / SECTIONS.
"""
import argparse
import json
import sys
import time

from core import study_db
from views_study import _resolve_ref, _parse_ref

# ── The study to add — edit this block ───────────────────────────────────────
TOPIC_ID = "divine_council"          # stable id; re-running replaces this topic
TITLE = "Divine Council"
INTRO = ""                           # leave blank, or draft one in the app with "Draft with AI"
SECTIONS = [
    ("The plural “us” — God speaks among the council", [
        "Genesis 1:26", "Genesis 3:22", "Genesis 11:7",
    ]),
    ("Members of the council — sons of God, gods, holy ones", [
        "Psalm 82:1", "Psalm 82:6", "Psalm 89:5", "Psalm 89:7",
        "Psalm 29:1", "Psalm 58:1", "Deuteronomy 32:8", "Deuteronomy 32:43",
    ]),
    ("The council in session — throne-room scenes", [
        # NOTE: the Micaiah vision — confirm 1 Kings vs the 2 Chronicles 18:18-19 parallel
        "1 Kings 22:19", "1 Kings 22:20", "Job 1:6", "Job 2:1",
        "Isaiah 6:1", "Isaiah 6:8", "Zechariah 3:1", "Zechariah 3:2",
    ]),
    ("Sons of God and the Nephilim", [
        "Genesis 6:2", "Genesis 6:4",
    ]),
]
PUBLISHED = True                     # True = visible to everyone; False = draft (only you)
# ─────────────────────────────────────────────────────────────────────────────


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _build_json():
    return {
        "intro": INTRO,
        "sections": [{"heading": h, "verses": list(refs)} for h, refs in SECTIONS],
        "related": [],
        "source": "",
    }


def dry_run():
    """Resolve + print every reference; return True if all of them found text."""
    total, bad = 0, []
    for heading, refs in SECTIONS:
        print("\n== %s ==" % heading)
        for ref in refs:
            total += 1
            if not _parse_ref(ref):
                print("  [BAD REF]  %s" % ref)
                bad.append(ref)
                continue
            hits = _resolve_ref(ref)
            text = " ".join(h["text"] for h in hits) if hits else ""
            if not text:
                print("  [NO TEXT]  %s" % ref)
                bad.append(ref)
            else:
                print("  %s" % ref)
                print("      %s" % (text[:160] + ("..." if len(text) > 160 else "")))
    print("\n%d references, %d with a problem." % (total, len(bad)))
    if bad:
        print("Fix these before --apply: %s" % ", ".join(bad))
    return not bad


def apply():
    conn = study_db()
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS entries ("
            " id TEXT PRIMARY KEY, type TEXT NOT NULL, title TEXT NOT NULL,"
            " json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft',"
            " created TEXT NOT NULL, updated TEXT NOT NULL,"
            " deleted INTEGER NOT NULL DEFAULT 0)"
        )
        now = _now()
        status = "published" if PUBLISHED else "draft"
        payload = json.dumps(_build_json(), ensure_ascii=False)
        existing = conn.execute("SELECT created FROM entries WHERE id=?", (TOPIC_ID,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE entries SET type='topic', title=?, json=?, status=?, updated=?, deleted=0"
                " WHERE id=?",
                (TITLE, payload, status, now, TOPIC_ID),
            )
            print("Updated existing topic '%s' (%s)." % (TOPIC_ID, status))
        else:
            conn.execute(
                "INSERT INTO entries (id, type, title, json, status, created, updated, deleted)"
                " VALUES (?, 'topic', ?, ?, ?, ?, ?, 0)",
                (TOPIC_ID, TITLE, payload, status, now, now),
            )
            print("Inserted new topic '%s' (%s)." % (TOPIC_ID, status))
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Add a hand-authored Study topic to study.db.")
    ap.add_argument("--apply", action="store_true", help="write to study.db (default is a dry run only)")
    args = ap.parse_args()

    ok = dry_run()
    if not args.apply:
        print("\n(dry run only — re-run with --apply once the text looks right)")
        sys.exit(0)
    if not ok:
        print("\nRefusing to --apply while references have problems. Fix them first.")
        sys.exit(1)
    apply()
    print("\nDone. Open the Study tab -> Divine Council to see it.")
