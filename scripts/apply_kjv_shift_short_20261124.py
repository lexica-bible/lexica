#!/usr/bin/env python3
"""apply_kjv_shift_short_20261124.py - the KJV tag-shift rows after the long batch (DESIGN 9.259, 9.260).

Three batches, each its own sha-pinned rows file, each cleared and run on its own:
  short  the 31 short verses, 107 rows (cleared, 9.259)
  psa    Psa 7:1, 6 rows (cleared and run, 9.261)
  two    1Co 5:13 and Mar 7:11, 4 rows (brought for clearance, 9.261)

  python3 scripts/apply_kjv_shift_short_20261124.py check short   READ-ONLY: every before-value
  python3 scripts/apply_kjv_shift_short_20261124.py apply short   the write: one all-or-nothing step
  python3 scripts/apply_kjv_shift_short_20261124.py after short   READ-ONLY: every after-value
  python3 scripts/apply_kjv_shift_short_20261124.py undo  short   the way back, from the before-values

The read-back decides whether a run is clean (ruled 9.259). The detector is a rough guide, so `check`
and `after` only NAME the batch's verses it flags; it can never stop a run or turn a clean one into CHECK.
Writes kjv_strongs only, through the long batch's own write and read-back code.
"""
import argparse
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_kjv_shift_20261123 as K                                    # noqa: E402
from read_kjv_firing_20261124 import BOOKS, ref as verse_name           # noqa: E402
from read_leftovers_20261122 import Fit, kjv_key, shift_runs            # noqa: E402

BATCHES = {
    "short": ("rows_short_20261123.tsv", "58454d7405e05867616e8b2a7a7fe3c3215ed0414deb355454fbfdd1daee44ca", 107, 31),
    "psa": ("rows_psa7_1_20261124.tsv", "c6b043a6341348c154dbcea0a8ae514ff4aa3e8f4237eebefb058ea79c98c9f2", 6, 1),
    "two": ("rows_two_verses_20261124.tsv", "d1ca037e3ed82aeaa62b692720eff00af7630f24141f1c45e3aa1505dc477b38", 4, 2),
}
BOOK_ID = {v: k for k, v in BOOKS.items()}


def load_plan(batch):
    name, want, n_rows, n_verses = BATCHES[batch]
    path = K.BATCH / name
    got = K.sha(path)
    if got != want:
        raise K.Stop(f"{name}: sha {got}, cleared {want}")
    plan, seen = [], set()
    for r in K._rows(path):
        wid = r["position_or_word_id"]
        m = re.fullmatch(r"(\S+) (\d+):(\d+) \(KJV\)", r["verse"])
        if r["cell"] != "kjv_strongs.strongs_id" or wid in seen or not m or m.group(1) not in BOOK_ID:
            raise K.Stop(f"row for word {wid}: wrong cell, a second row, or an unreadable verse")
        seen.add(wid)
        word, before = K._cell(r["before"], wid)
        word2, after = K._cell(r["after"], wid)
        if word != word2 or sorted(before) == sorted(after):
            raise K.Stop(f"word {wid}: {r['before']!r} -> {r['after']!r}")
        plan.append({"id": int(wid), "word": word, "key": (BOOK_ID[m.group(1)], int(m.group(2)), int(m.group(3))),
                     "before": before, "after": after})
    if len(plan) != n_rows or len({p["key"] for p in plan}) != n_verses:
        raise K.Stop(f"{len(plan)} rows in {len({p['key'] for p in plan})} verses, expected {n_rows} in {n_verses}")
    return plan


def flagged(conn, plan):
    """Which of the batch's verses the production detector flags. Information only."""
    fit, verses = Fit(), {}
    keys = {p["key"] for p in plan}
    for b, c, v, w, t in conn.execute("""SELECT w.book_id, w.chapter, w.verse_num, w.word, GROUP_CONCAT(s.strongs_id)
                                         FROM kjv_words w LEFT JOIN kjv_strongs s ON s.word_id = w.word_id
                                         GROUP BY w.word_id ORDER BY w.book_id, w.chapter, w.verse_num, w.verse_pos"""):
        tags = t.split(",") if t else []
        k = kjv_key(w)
        if tags:
            fit.add(k, tags)
        if (b, c, v) in keys:
            verses.setdefault((b, c, v), []).append((k, tags))
    return sorted(verse_name(x) for x, toks in verses.items() if shift_runs(toks, fit))


def do_read(db, batch, side, scan=True):
    plan = load_plan(batch)
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        K.check_structure(conn)
        bad = K.verify(conn, plan, side)
        if bad:
            raise K.Stop(f"{len(bad)} {side}-value(s) differ from live:\n  " + "\n  ".join(bad[:40]))
        print(f"{side}-values: all {len(plan)} rows match live, {len({p['key'] for p in plan})} verses")
        if scan:
            try:
                names = flagged(conn, plan)
                print(f"detector, for information only (any run of 2+ tags): flags {len(names)} of these verses {names}")
            except sqlite3.Error as e:      # the read-back above decides; a failed scan never stops a run
                print(f"detector, for information only: did not run ({e})")
    finally:
        conn.close()
    print("CHECK DONE" if side == "before" else "AFTER DONE")


def do_write(db, batch, forward):
    if K.in_window():
        raise K.Stop("13:00-14:30 UTC: not started (the nightly health check and backup)")
    plan = load_plan(batch)
    src, dst = ("before", "after") if forward else ("after", "before")
    want = sum(len(p["before"]) + len(p["after"]) for p in plan)
    net = sum(len(p[dst]) - len(p[src]) for p in plan)
    conn = sqlite3.connect(str(db), isolation_level=None)
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        K.check_structure(conn)
        conn.execute("BEGIN IMMEDIATE")
        try:
            bad = K.verify(conn, plan, src)
            if bad:
                raise K.Stop(f"{len(bad)} starting value(s) differ:\n  " + "\n  ".join(bad[:40]))
            total = conn.execute("SELECT count(*) FROM kjv_strongs").fetchone()[0]
            start = conn.total_changes
            K._write(conn, plan, forward)
            n = conn.total_changes - start
            if n != want:
                raise K.Stop(f"{n} changes, expected {want}")
            bad = K.verify(conn, plan, dst)
            if bad:
                raise K.Stop(f"{len(bad)} result(s) differ:\n  " + "\n  ".join(bad[:40]))
            now = conn.execute("SELECT count(*) FROM kjv_strongs").fetchone()[0]
            if now != total + net:
                raise K.Stop(f"kjv_strongs {now:,}, expected {total + net:,}")
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()
    print(f"{'written' if forward else 'put back'}: {want} changes on {len(plan)} words, every result read back; kjv_strongs {total:,} -> {now:,}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("check", "apply", "after", "undo"))
    ap.add_argument("batch", choices=tuple(BATCHES))
    ap.add_argument("--db", default=str(K.LIVE))
    a = ap.parse_args()
    try:
        if a.mode == "check":
            do_read(a.db, a.batch, "before")
        elif a.mode == "after":
            do_read(a.db, a.batch, "after")
        else:
            do_write(a.db, a.batch, a.mode == "apply")
    except K.Stop as e:
        print(f"STOP: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
