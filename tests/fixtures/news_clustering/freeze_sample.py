#!/usr/bin/env python3
"""freeze_sample.py — READ-ONLY. Copies the three clustering samples out of news.db into ONE
JSON file, so the clustering fixtures can be built from real rows without ever touching the
live database again. Opens news.db read-only (mode=ro); writes only the output file.

Run on PA (from ~/bible-db), then copy the file back with scp:
  ~/.virtualenvs/bible-env/bin/python tests/fixtures/news_clustering/freeze_sample.py
  (writes ~/news_clustering_freeze.json; --out PATH to change, --db PATH for another copy)

WHAT IT COPIES (score >= 5 only — the labeler never labels below 5, so lower rows aren't
part of the event-label layer these fixtures test):
  merge_encyclical  every row whose headline or event label mentions an encyclical or
                    "Magnifica Humanitas". Picked by CONTENT, not by label, on purpose: a
                    row about the encyclical that got some OTHER label is exactly the
                    merge failure the fixture has to be able to see.
  split_sunday      every row whose headline or label mentions Sunday / day of rest, plus
                    (if the June rollback copy news.db.pre-regroup still exists) every row
                    that copy had under "Sunday Rest Laws Debate" — the June bucket itself.
  cross_night       death-penalty / capital-punishment rows published 2026-10-01 or later
                    (the Pope Leo "inadmissible" pair of cards), plus the NewsNation
                    "Catholic AI task force" repeat pair (ids 26816 / 27449) — one of which
                    now lives in items_merged after the 10/25 merge, so that table is read too.

Never copied: Keep/Dismiss marks, the reviews table, items.status. That's human signal and
has no place in a clustering fixture. Also skipped: summaries and AI reasons (not inputs to
either layer).
"""
import datetime
import json
import os
import sqlite3
import sys

HOME = os.path.expanduser("~")
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
DB = os.path.join(REPO_ROOT, "news.db")
OUT = os.path.join(HOME, "news_clustering_freeze.json")
JUNE_COPY_NAME = "news.db.pre-regroup"     # the June rollback copy, beside news.db
JUNE_BUCKET = "Sunday Rest Laws Debate"
PAIR_IDS = (26816, 27449)

COLS = ["id", "title", "source", "published", "first_seen", "score", "event",
        "ai_thread", "url", "query"]


def _arg(flag, default):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def _ro(path):
    if not os.path.exists(path):          # never let sqlite create an empty decoy file
        sys.exit(f"not found: {path}")
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


def _rows(conn, table, where, args):
    have = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
    sel = ", ".join(c if c in have else f"NULL AS {c}" for c in COLS)
    extra = ", merged_into" if "merged_into" in have else ""
    out = []
    for r in conn.execute(f"SELECT {sel}{extra} FROM {table} WHERE {where} ORDER BY id", args):
        d = {c: r[c] for c in COLS}
        d["table"] = table
        if extra:
            d["merged_into"] = r["merged_into"]
        out.append(d)
    return out


def _has_table(conn, name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (name,)).fetchone() is not None


def main():
    db = _arg("--db", DB)
    out_path = _arg("--out", OUT)
    june_copy = os.path.join(os.path.dirname(os.path.abspath(db)), JUNE_COPY_NAME)
    conn = _ro(db)
    hay = "lower(COALESCE(title,'') || ' ' || COALESCE(event,''))"
    base = "score IS NOT NULL AND score >= 5"

    merge = _rows(conn, "items",
                  f"{base} AND ({hay} LIKE '%encyclical%' OR {hay} LIKE '%magnifica humanitas%')",
                  [])

    sunday = _rows(conn, "items",
                   f"{base} AND ({hay} LIKE '%sunday%' OR {hay} LIKE '%day of rest%')", [])
    june_note = "news.db.pre-regroup not found — June bucket membership not included"
    if os.path.exists(june_copy):
        jc = _ro(june_copy)
        june = {r["id"]: r["event"] for r in jc.execute(
            "SELECT id, event FROM items WHERE event = ?", (JUNE_BUCKET,))}
        jc.close()
        have = {r["id"] for r in sunday}
        missing = [i for i in june if i not in have]
        if missing:
            qs = ",".join("?" * len(missing))
            sunday += _rows(conn, "items", f"id IN ({qs})", missing)
        for r in sunday:
            r["june_event"] = june.get(r["id"])
        june_note = (f"{len(june)} rows were in '{JUNE_BUCKET}' in news.db.pre-regroup "
                     f"({len(missing)} of them added here by id; not all still score >= 5)")
        sunday.sort(key=lambda r: r["id"])

    cross = _rows(conn, "items",
                  f"{base} AND published >= '2026-10-01' AND "
                  f"({hay} LIKE '%death penalty%' OR {hay} LIKE '%capital punishment%')", [])
    qs = ",".join("?" * len(PAIR_IDS))
    cross += _rows(conn, "items", f"id IN ({qs})", list(PAIR_IDS))
    if _has_table(conn, "items_merged"):
        cross += _rows(conn, "items_merged", f"id IN ({qs})", list(PAIR_IDS))
    conn.close()

    data = {
        "_about": {
            "frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(
                timespec="seconds"),
            "source_db": db,
            "made_by": "tests/fixtures/news_clustering/freeze_sample.py (read-only)",
            "june_bucket": june_note,
        },
        "merge_encyclical": merge,
        "split_sunday": sunday,
        "cross_night": cross,
    }
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"wrote {out_path}")
    for k in ("merge_encyclical", "split_sunday", "cross_night"):
        rows = data[k]
        labels = {r["event"] for r in rows if r["event"]}
        print(f"  {k:17s} {len(rows):4d} rows, {len(labels):3d} distinct labels, "
              f"{sum(1 for r in rows if not r['event'])} unlabeled")
    print(f"  june bucket: {june_note}")


if __name__ == "__main__":
    main()
