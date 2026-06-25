#!/usr/bin/env python3
"""Batch publish / unpublish Study TOPICS in study.db (just flips the Draft/Published
flag — no AI, no key needed). Runs on PythonAnywhere. Reversible.

  python3 scripts/publish_topics.py             # publish topics that HAVE an intro (the "ready" ones)
  python3 scripts/publish_topics.py --all       # publish EVERY topic
  python3 scripts/publish_topics.py --names      # publish the metaV person/place NAME-topics (the Nave's blocks)
  python3 scripts/publish_topics.py --limit 50  # cap how many it flips
  python3 scripts/publish_topics.py --unpublish # set ALL topics back to Draft
  python3 scripts/publish_topics.py --unpublish --imported            # hide ONLY the Nave's/Torrey's imports
  python3 scripts/publish_topics.py --unpublish --imported --dry-run  # ...preview it first (writes nothing)

Published topics + name-topics are PUBLIC (visible to everyone). This just flips the
flag, so it's safe and reversible — re-run with --unpublish to undo.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import study_db   # noqa: E402
from generate_topic_intros import _COMMON   # noqa: E402  (the curated hot-topic list)


def main():
    ap = argparse.ArgumentParser(description="Batch publish/unpublish Study topics.")
    ap.add_argument("--all", action="store_true", help="publish every topic (default: only ones with an intro)")
    ap.add_argument("--names", action="store_true", help="target the metaV person/place NAME-topics (the Nave's sidebar blocks) instead of concept topics; publishes all of them (they have no intro)")
    ap.add_argument("--common", action="store_true", help="only the curated hot topics (same list the intro script uses)")
    ap.add_argument("--skip-first", type=int, default=0, metavar="N", help="when publishing, skip the first N topics alphabetically (the early test batch)")
    ap.add_argument("--unpublish", action="store_true", help="set topics back to Draft instead")
    ap.add_argument("--limit", type=int, default=0, help="stop after N changes (0 = no cap)")
    ap.add_argument("--imported", action="store_true", help="only the MetaV-imported concept topics (id starts with 'metav_') — the Nave's/Torrey's list; leaves hand-authored topics + person/place name-topics alone")
    ap.add_argument("--dry-run", action="store_true", help="show what would change, write nothing")
    args = ap.parse_args()

    target = "draft" if args.unpublish else "published"
    etype = "name" if args.names else "topic"
    conn = study_db()
    rows = conn.execute(
        "SELECT id, title, json, status FROM entries WHERE type=? AND deleted=0 ORDER BY title",
        (etype,),
    ).fetchall()
    if args.common:
        wanted = {t.lower() for t in _COMMON}
        rows = [r for r in rows if (r["title"] or "").strip().lower() in wanted]
    elif args.skip_first and not args.unpublish:
        rows = sorted(rows, key=lambda r: (r["title"] or "").lower())[args.skip_first:]
    if args.imported:
        # MetaV import ids are 'metav_<slug>' (concepts) and 'metavn_<slug>' (names);
        # 'metav_' startswith correctly excludes 'metavn_' and any hand-authored topic.
        rows = [r for r in rows if (r["id"] or "").startswith("metav_")]
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    changed = 0
    titles = []
    for r in rows:
        # default (publishing, not --all): only topics that already have an intro.
        # Name-topics have no intro, so --names publishes all of them.
        if not args.unpublish and not args.all and not args.names:
            try:
                stored = json.loads(r["json"]) or {}
            except (ValueError, TypeError):
                stored = {}
            if not (stored.get("intro") or "").strip():
                continue
        if r["status"] == target:
            continue   # already there
        if not args.dry_run:
            conn.execute("UPDATE entries SET status=?, updated=? WHERE id=?", (target, now, r["id"]))
        changed += 1
        titles.append(r["title"] or r["id"])
        if args.limit and changed >= args.limit:
            break

    if not args.dry_run:
        conn.commit()
    conn.close()
    if args.dry_run:
        print("DRY RUN — would set {} topic(s) to {}:".format(changed, target))
        for t in titles[:60]:
            print("  - {}".format(t))
        if len(titles) > 60:
            print("  ... and {} more".format(len(titles) - 60))
    else:
        print("Set {} topic(s) to {}.".format(changed, target))


if __name__ == "__main__":
    main()
