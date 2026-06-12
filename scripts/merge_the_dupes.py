#!/usr/bin/env python3
"""Merge the "X, the" duplicate topics into their plain "X" twin — Nave's index quirk
("Amorites" + "Amorites, the" are the same subject). ONLY touches exact "X, the" pairs
(and a couple of confirmed concept pairs below); facet topics like "X, Eternal" or
"X, the King" are left alone.

DRY-RUN by default (prints what it would do). --apply actually merges: it backs up
study.db first, folds the "X, the" topic's verses into "X" (same-heading sections are
combined, verse refs de-duped), and SOFT-deletes the absorbed one (recoverable).

  python3 scripts/merge_the_dupes.py            # show what would merge
  python3 scripts/merge_the_dupes.py --apply    # do it (backs up to study.db.bak first)
"""
import json
import os
import re
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import study_db   # noqa: E402
try:
    from core import STUDY_DB as _DB_PATH   # noqa: E402
except Exception:
    _DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "study.db")

# Same-subject pairs that AREN'T "X, the" but are confirmed duplicates. (absorb_id, keeper_id)
_EXTRA = [
    ("metav_trinity_the_holy", "metav_trinity_the"),   # "The Holy Trinity" -> "The Trinity"
]

_THE_RE = re.compile(r"^(.*?),\s*the$", re.IGNORECASE)


def _norm(t):
    return (t or "").strip().lower()


def _vcount(js):
    try:
        d = json.loads(js) or {}
    except (ValueError, TypeError):
        return 0
    return sum(len((s or {}).get("verses") or []) for s in (d.get("sections") or []))


def _merge_sections(ksecs, asecs):
    """Fold asecs into ksecs: same-heading sections share a list, verse refs de-duped."""
    out = [dict(s, verses=list((s or {}).get("verses") or [])) for s in (ksecs or [])]
    idx = {(_norm(s.get("heading"))): s for s in out}
    for s in (asecs or []):
        h = _norm((s or {}).get("heading"))
        verses = (s or {}).get("verses") or []
        if h in idx:
            cur = idx[h]["verses"]
            seen = set(cur)
            for v in verses:
                if v not in seen:
                    cur.append(v)
                    seen.add(v)
        else:
            ns = {"heading": (s or {}).get("heading", ""), "verses": list(verses)}
            out.append(ns)
            idx[h] = ns
    return out


def main():
    apply = "--apply" in sys.argv
    conn = study_db()
    rows = conn.execute(
        "SELECT id, title, json FROM entries WHERE type='topic' AND deleted=0"
    ).fetchall()
    by_title = {_norm(r["title"]): r for r in rows}
    by_id = {r["id"]: r for r in rows}

    pairs, used = [], set()
    for r in rows:
        m = _THE_RE.match((r["title"] or "").strip())
        if not m:
            continue
        keeper = by_title.get(_norm(m.group(1)))
        if keeper and keeper["id"] != r["id"] and r["id"] not in used:
            pairs.append((r, keeper))
            used.add(r["id"])
    for aid, kid in _EXTRA:
        if aid in by_id and kid in by_id and aid not in used:
            pairs.append((by_id[aid], by_id[kid]))
            used.add(aid)

    if not pairs:
        print("No 'X, the' duplicates to merge.")
        conn.close()
        return

    print("Would merge {} pair(s):".format(len(pairs)))
    for absorb, keeper in pairs:
        print("    {:<34} ({:>3}v)  ->  {:<24} ({:>3}v)".format(
            absorb["title"], _vcount(absorb["json"]), keeper["title"], _vcount(keeper["json"])))

    if not apply:
        print("\nDry run — nothing changed. Re-run with --apply to merge.")
        conn.close()
        return

    shutil.copy(_DB_PATH, _DB_PATH + ".bak")
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for absorb, keeper in pairs:
        kj = json.loads(keeper["json"]) or {}
        aj = json.loads(absorb["json"]) or {}
        kj["sections"] = _merge_sections(kj.get("sections"), aj.get("sections"))
        conn.execute("UPDATE entries SET json=?, updated=? WHERE id=?",
                     (json.dumps(kj, ensure_ascii=False), now, keeper["id"]))
        conn.execute("UPDATE entries SET deleted=1, updated=? WHERE id=?", (now, absorb["id"]))
        keeper["json"] = json.dumps(kj, ensure_ascii=False)   # in case a keeper is also a later keeper
    conn.commit()
    conn.close()
    print("\nMerged {} pair(s). Backup at {}.bak".format(len(pairs), _DB_PATH))


if __name__ == "__main__":
    main()
