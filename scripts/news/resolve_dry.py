#!/usr/bin/env python3
"""resolve_dry.py — confirm the resolve-on-copy write shape WITHOUT writing.

Pulls a handful of real KEPT-shortlist face URLs straight from news.db, resolves
each through gnews_resolve (the same module the live endpoint uses), and prints
title -> wrapper vs title -> resolved. Writes NOTHING (opens the DB read-only).

Use it to eyeball that the resolved URLs are real articles before turning live
caching on. Then run the ALTER and reload.

Run on PA:
  python3 scripts/news/resolve_dry.py ~/bible-db/news.db          # 8 kept faces
  python3 scripts/news/resolve_dry.py ~/bible-db/news.db --limit 15

Faces are picked by the SAME clustering path the copy uses (views_news._group /
_pick_face) — so these are the exact URLs Copy shortlist would emit.
"""
import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from views_news import _group, _pick_face                       # noqa: E402
from scripts.news.gnews_resolve import resolve, is_wrapper      # noqa: E402


def _has_col(conn, table, col):
    return any(r[1] == col for r in conn.execute(f"PRAGMA table_info({table})"))


def _has_table(conn, name):
    return conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (name,)).fetchone() is not None


def _faces(conn, has_event):
    """Every cluster's face, with the ids of its members (so we can tell which
    clusters are 'kept'). Mirrors the live serializer's face pick exactly."""
    cols = "i.id, i.url, i.title, i.source, i.published, i.score, i.ai_thread"
    if has_event:
        cols += ", i.event"
    rows = conn.execute(
        f"SELECT {cols} FROM items i WHERE i.score IS NOT NULL "
        f"ORDER BY i.score DESC, i.published DESC").fetchall()
    out = []
    for c in _group(rows, has_event):
        arts = c["arts"]
        newest = max((a["published"] or "" for a in arts), default="")
        face = _pick_face(arts, newest)
        out.append((face, {a["id"] for a in arts}))
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 resolve_dry.py /path/to/news.db [--limit N]")
    db = sys.argv[1]
    limit = 8
    if "--limit" in sys.argv:
        try:
            limit = max(1, int(sys.argv[sys.argv.index("--limit") + 1]))
        except (IndexError, ValueError):
            pass

    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    has_event = _has_col(conn, "items", "event")

    faces = _faces(conn, has_event)
    wrapper_faces = [(f, ids) for (f, ids) in faces if is_wrapper(f["url"])]

    # which clusters are 'kept' — any member marked keep by any reviewer
    kept_item_ids = set()
    if _has_table(conn, "reviews"):
        kept_item_ids = {r["item_id"] for r in conn.execute(
            "SELECT item_id FROM reviews WHERE status = 'keep'")}
    kept_wrappers = [(f, ids) for (f, ids) in wrapper_faces
                     if ids & kept_item_ids] if kept_item_ids else []

    # sample the kept shortlist; fall back to any wrapper-faces if nothing kept yet
    pool = kept_wrappers if kept_wrappers else wrapper_faces
    sample = pool[:limit]

    print(f"clusters: {len(faces)}   wrapper-faces: {len(wrapper_faces)}   "
          f"kept wrapper-faces: {len(kept_wrappers)}   sampling: {len(sample)}"
          f"{'' if kept_wrappers else '  (no kept yet -> sampling any faces)'}")
    print("=" * 70)

    ok = fail = 0
    for i, (f, _ids) in enumerate(sample, 1):
        clean = resolve(f["url"])
        title = (f["title"] or "")[:70]
        print(f"[{i}] {title}")
        print(f"    wrapper : {f['url'][:95]}")
        if clean:
            ok += 1
            print(f"    resolved: {clean}")
        else:
            fail += 1
            print(f"    resolved: FAILED (would keep the wrapper)")
    print("=" * 70)
    print(f"resolved ok: {ok}   failed: {fail}   (nothing written — read-only)")

    # ---- dup check: a wrapper URL that sits in 2+ item rows across clusters ----
    # Proves the endpoint's UPDATE ... WHERE url caches EVERY row sharing that URL.
    dup = conn.execute(
        "SELECT url, COUNT(*) n FROM items "
        "WHERE url LIKE '%news.google.com/rss/articles/%' "
        "GROUP BY url HAVING n > 1 ORDER BY n DESC LIMIT 1").fetchone()
    print("-" * 70)
    if dup:
        clean = resolve(dup["url"])
        print(f"dup check: this wrapper appears in {dup['n']} item rows — one resolve")
        print(f"           caches all {dup['n']} (UPDATE ... WHERE url).")
        print(f"    wrapper : {dup['url'][:95]}")
        print(f"    resolved: {clean if clean else 'FAILED'}")
    else:
        print("dup check: no wrapper URL is shared across rows — every face is a "
              "unique row, so per-URL caching maps 1:1.")
    conn.close()


if __name__ == "__main__":
    main()
