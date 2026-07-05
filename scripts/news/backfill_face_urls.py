#!/usr/bin/env python3
"""backfill_face_urls.py — pre-resolve each cluster FACE's Google News wrapper.

Copy shortlist emits the face article's URL (the headline shown on the card).
For clusters whose face is still a Google News wrapper, this resolves the real
URL once and caches it in items.resolved_url so the copy is instant + clean.

FACES ONLY — not the ~7,200 source rows. The face is defined by app logic
(_group -> _split_by_window -> _pick_face) and one `event` can split into
several clusters, so SQL can't pick these rows. We import the SAME functions
the live serializer uses (views_news._group / _pick_face) — zero drift.

Run on PA:
  DRY RUN (writes nothing, default):
      python3 scripts/news/backfill_face_urls.py ~/bible-db/news.db
  WRITE (after the dry run looks right):
      python3 scripts/news/backfill_face_urls.py ~/bible-db/news.db --apply

Resumable: keyed off resolved_url IS NULL. Kill it and re-run — it skips the
faces already cached and picks up where it stopped. Fails soft on every
wrapper it can't resolve (leaves NULL, moves on).

One-time schema step (Jonathan, not this script):
    ALTER TABLE items ADD COLUMN resolved_url TEXT;
"""
import os
import sys
import time
import sqlite3

# import the live clustering path so the faces we pick are byte-identical to
# what the news surface serializes (repo root on sys.path)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from views_news import _group, _pick_face                       # noqa: E402
from scripts.news.gnews_resolve import resolve, is_wrapper      # noqa: E402

# polite spacing between network calls, and backoff when one fails (looks like
# a 429 / timeout). A few hundred faces at this pace is ~15-30 min, not a war.
BASE_SLEEP = 2.0
RETRIES = 2
BACKOFF = [5.0, 15.0]


def _has_col(conn, table, col):
    return any(r[1] == col for r in conn.execute(f"PRAGMA table_info({table})"))


def _pick_faces(conn, has_event):
    """Run the real assembly path and return the face row of every cluster,
    deduped by id (the exact rows whose url the copy emits)."""
    cols = "i.id, i.url, i.title, i.source, i.published, i.score, i.ai_thread"
    if has_event:
        cols += ", i.event"
    rows = conn.execute(
        f"SELECT {cols} FROM items i WHERE i.score IS NOT NULL "
        f"ORDER BY i.score DESC, i.published DESC"
    ).fetchall()
    faces, seen = [], set()
    for c in _group(rows, has_event):
        arts = c["arts"]
        newest = max((a["published"] or "" for a in arts), default="")
        face = _pick_face(arts, newest)
        if face["id"] not in seen:
            seen.add(face["id"])
            faces.append(face)
    return faces


def _resolve_with_backoff(url):
    """Resolve one wrapper, retrying with growing sleeps on failure. Returns a
    clean URL or None. Never raises."""
    clean = resolve(url)
    if clean:
        return clean
    for wait in BACKOFF[:RETRIES]:
        time.sleep(wait)
        clean = resolve(url)
        if clean:
            return clean
    return None


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 backfill_face_urls.py /path/to/news.db [--apply]")
    db = sys.argv[1]
    apply = "--apply" in sys.argv[2:]

    # read-only for the dry run; writable only when applying
    if apply:
        conn = sqlite3.connect(db)
        conn.execute("PRAGMA journal_mode=DELETE")   # NFS-safe, not WAL (2026-07-05 corruption)
        conn.execute("PRAGMA busy_timeout=5000")
    else:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    has_event = _has_col(conn, "items", "event")
    has_resolved = _has_col(conn, "items", "resolved_url")
    if apply and not has_resolved:
        conn.close()
        sys.exit("items.resolved_url is missing — run the ALTER TABLE first "
                 "(see the header), then re-run with --apply.")

    faces = _pick_faces(conn, has_event)
    # only the faces that are still wrappers and not already cached
    todo = []
    for f in faces:
        if not is_wrapper(f["url"]):
            continue
        if has_resolved:
            cur = conn.execute("SELECT resolved_url FROM items WHERE id = ?",
                               (f["id"],)).fetchone()
            if cur and cur["resolved_url"]:
                continue
        todo.append(f)

    print(f"clusters (faces): {len(faces)}")
    print(f"faces that are Google News wrappers, not yet resolved: {len(todo)}")
    print(f"mode: {'APPLY (writing resolved_url)' if apply else 'DRY RUN (no writes)'}")
    print("-" * 60)

    ok = fail = 0
    for i, f in enumerate(todo, 1):
        clean = _resolve_with_backoff(f["url"])
        title = (f["title"] or "")[:70]
        if clean:
            ok += 1
            print(f"[{i}/{len(todo)}] {title}")
            print(f"    wrapper : {f['url'][:90]}")
            print(f"    resolved: {clean}")
            if apply:
                conn.execute("UPDATE items SET resolved_url = ? WHERE id = ?",
                             (clean, f["id"]))
                conn.commit()
        else:
            fail += 1
            print(f"[{i}/{len(todo)}] {title}")
            print(f"    wrapper : {f['url'][:90]}")
            print(f"    resolved: FAILED (left NULL, will retry on a later run)")
        time.sleep(BASE_SLEEP)

    print("-" * 60)
    print(f"resolved ok: {ok}   failed (left NULL): {fail}")
    if not apply:
        print("dry run — nothing written. Re-run with --apply to cache these.")
    conn.close()


if __name__ == "__main__":
    main()
