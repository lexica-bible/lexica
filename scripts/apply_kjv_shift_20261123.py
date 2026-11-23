#!/usr/bin/env python3
"""apply_kjv_shift_20261123.py - the 21 long KJV tag-shift verses (DESIGN 9.257, 9.258).

Writes the cleared rows to kjv_strongs only. The rows are the sha-pinned file the ruling chat cleared
(405 rows) plus a sha-pinned file of the two Act 26:12 rows it asked about, which replace the cleared
after-values on those two words.

  python3 scripts/apply_kjv_shift_20261123.py check   READ-ONLY: every before-value + every gate
  python3 scripts/apply_kjv_shift_20261123.py apply   the write: one all-or-nothing database step
  python3 scripts/apply_kjv_shift_20261123.py after   READ-ONLY: every after-value + the detector
  python3 scripts/apply_kjv_shift_20261123.py undo    the way back, from the before-values

apply and undo each refuse 13:00-14:30 UTC, take the write hold, re-read every starting value, write,
read every result back, count the changes, and save only if all of that held. Any miss = nothing saved.
No copy of the database is made: the row files hold every before-value.

No words rebuild touches kjv_strongs (this batch and the 11/22 one are the only writers in the repo),
so nothing here needs a frozen file for a rebuild to re-apply.
"""
import argparse
import csv
import hashlib
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

BATCH = ROOT / "docs" / "handoffs" / "drafts" / "KJV_SHIFT"
CLEARED = BATCH / "rows_long_20261123.tsv"
CLEARED_SHA = "c24637591278bdeec6b8819c2abeb680be00def23777a7f941451958eed1a0ba"
CHANGED = BATCH / "rows_long_changed_20261123.tsv"
CHANGED_SHA = "c34b6d97bab74665747f7cd882a96623eaec29efd26aaf8c5aacf53f581f159e"
LIVE = Path("~/bible-db/bible.db").expanduser()

ROWS, VERSE_COUNT = 405, 21
CHANGED_IDS = 2
WORDS, VERSES = 626309, 31237
BOOK = {"Psa": 19, "Mat": 40, "Luk": 42, "Joh": 43, "Act": 44, "Rom": 45, "1Co": 46, "Rev": 66}


class Stop(Exception):
    """Any miss: nothing is saved."""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def _cell(cell, wid):
    m = re.fullmatch(r"(\S+): ([GH]\d+(?:\+[GH]\d+)*|\(none\))", cell)
    if not m:
        raise Stop(f"word {wid}: cannot read the cell {cell!r}")
    return m.group(1), [] if m.group(2) == "(none)" else m.group(2).split("+")


def _ref(v):
    m = re.fullmatch(r"(\S+) (\d+):(\d+) \(KJV\)", v)
    if not m or m.group(1) not in BOOK:
        raise Stop(f"cannot read the verse {v!r}")
    return BOOK[m.group(1)], int(m.group(2)), int(m.group(3))


def load_plan():
    for p, want in ((CLEARED, CLEARED_SHA), (CHANGED, CHANGED_SHA)):
        got = sha(p)
        if got != want:
            raise Stop(f"{p.name}: sha {got}, cleared {want}")
    rows = _rows(CLEARED)
    changed = {r["position_or_word_id"]: r for r in _rows(CHANGED)}
    if len(rows) != ROWS or len(changed) != CHANGED_IDS:
        raise Stop(f"{len(rows)} rows + {len(changed)} changed, expected {ROWS} + {CHANGED_IDS}")
    plan, seen = [], set()
    for r in rows:
        wid = r["position_or_word_id"]
        if r["cell"] != "kjv_strongs.strongs_id" or wid in seen:
            raise Stop(f"row for word {wid}: wrong cell or a second row")
        seen.add(wid)
        after = r["after"]
        if wid in changed:
            c = changed[wid]
            if c["before"] != r["before"] or c["verse"] != r["verse"]:
                raise Stop(f"changed row {wid}: its verse or before-value is not the cleared one")
            after = c["after"]
        word, before_tags = _cell(r["before"], wid)
        word2, after_tags = _cell(after, wid)
        if word != word2 or sorted(before_tags) == sorted(after_tags):
            raise Stop(f"word {wid}: {r['before']!r} -> {after!r}")
        plan.append({"id": int(wid), "word": word, "key": _ref(r["verse"]), "before": before_tags, "after": after_tags})
    if set(changed) - seen:
        raise Stop("a changed row is not in the cleared file")
    if len({p["key"] for p in plan}) != VERSE_COUNT:
        raise Stop("the rows do not cover 21 verses")
    return plan


def in_window():
    t = datetime.now(timezone.utc)
    return 13 * 60 <= t.hour * 60 + t.minute < 14 * 60 + 30


def check_structure(conn):
    cols = sorted(r[1] for r in conn.execute("PRAGMA table_info(kjv_strongs)"))
    if cols != ["strongs_id", "word_id"]:
        raise Stop(f"kjv_strongs columns are {cols}, expected word_id + strongs_id")
    trig = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='kjv_strongs'")]
    if trig:
        raise Stop(f"triggers on kjv_strongs: {trig}")
    mode = (conn.execute("PRAGMA journal_mode").fetchone()[0] or "").lower()
    if mode != "delete":
        raise Stop(f"journal_mode is {mode!r}, must be delete")
    w, v = (conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("words", "verses"))
    if (w, v) != (WORDS, VERSES):
        raise Stop(f"words {w:,} / verses {v:,}, expected {WORDS:,} / {VERSES:,}")
    print(f"structure: kjv_strongs = word_id + strongs_id; no triggers; journal delete; words {w:,}; verses {v:,}")


def verify(conn, plan, side):
    bad = []
    for p in plan:
        rows = conn.execute("SELECT word, book_id, chapter, verse_num FROM kjv_words WHERE word_id=?", (p["id"],)).fetchall()
        if len(rows) != 1 or rows[0] != (p["word"], *p["key"]):
            bad.append(f"word {p['id']}: {rows} is not {p['word']} at {p['key']}")
            continue
        got = sorted(r[0] for r in conn.execute("SELECT strongs_id FROM kjv_strongs WHERE word_id=?", (p["id"],)))
        if got != sorted(p[side]):
            bad.append(f"word {p['id']} ({p['word']}): tags {got}, expected {sorted(p[side])}")
    return bad


def detector(conn, plan):
    """The production detector over the whole KJV. -> (of the 21, how many fire; all verses firing)."""
    from read_leftovers_20261122 import Fit, STRONG_RUN, kjv_key, shift_runs
    sql = """SELECT w.book_id, w.chapter, w.verse_num, w.word, GROUP_CONCAT(s.strongs_id)
             FROM kjv_words w LEFT JOIN kjv_strongs s ON s.word_id = w.word_id
             GROUP BY w.word_id ORDER BY w.book_id, w.chapter, w.verse_num, w.verse_pos"""
    fit, verses = Fit(), {}
    for b, c, v, w, t in conn.execute(sql):
        tags = t.split(",") if t else []
        k = kjv_key(w)
        if tags:
            fit.add(k, tags)
        verses.setdefault((b, c, v), []).append((k, tags))
    firing = {key for key, toks in verses.items() if any(n >= STRONG_RUN for _d, n, _a, _b in shift_runs(toks, fit))}
    return len(firing & {p["key"] for p in plan}), firing


def do_check(db, scan=True):
    plan = load_plan()
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        check_structure(conn)
        bad = verify(conn, plan, "before")
        if bad:
            raise Stop(f"{len(bad)} before-value(s) differ from live:\n  " + "\n  ".join(bad[:40]))
        print(f"before-values: all {len(plan)} rows match live, {VERSE_COUNT} verses")
        if scan:
            hit, firing = detector(conn, plan)
            print(f"CONTROL: the detector fires on {hit} of the {VERSE_COUNT} verses before the write ({len(firing)} long-shift verses in the KJV)")
            if hit != VERSE_COUNT:
                raise Stop("the detector does not fire on every verse this batch repairs")
    finally:
        conn.close()
    n = sum(len(p["before"]) + len(p["after"]) for p in plan)
    print(f"plan: {len(plan)} words; {sum(map(lambda p: len(p['before']), plan))} tags off, {sum(map(lambda p: len(p['after']), plan))} tags on ({n} changes)")
    print("CHECK DONE")


def _write(conn, plan, forward):
    src, dst = ("before", "after") if forward else ("after", "before")
    for p in plan:
        c = conn.execute("DELETE FROM kjv_strongs WHERE word_id=?", (p["id"],))
        if c.rowcount != len(p[src]):
            raise Stop(f"word {p['id']}: {c.rowcount} tags removed, expected {len(p[src])}")
        for t in p[dst]:
            conn.execute("INSERT INTO kjv_strongs (word_id, strongs_id) VALUES (?, ?)", (p["id"], t))


def do_write(db, forward):
    if in_window():
        raise Stop("13:00-14:30 UTC: not started (the nightly health check and backup)")
    plan = load_plan()
    src, dst = ("before", "after") if forward else ("after", "before")
    want = sum(len(p["before"]) + len(p["after"]) for p in plan)
    net = sum(len(p[dst]) - len(p[src]) for p in plan)
    conn = sqlite3.connect(str(db), isolation_level=None)
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        check_structure(conn)
        conn.execute("BEGIN IMMEDIATE")
        try:
            bad = verify(conn, plan, src)
            if bad:
                raise Stop(f"{len(bad)} starting value(s) differ:\n  " + "\n  ".join(bad[:40]))
            total = conn.execute("SELECT count(*) FROM kjv_strongs").fetchone()[0]
            start = conn.total_changes
            _write(conn, plan, forward)
            n = conn.total_changes - start
            if n != want:
                raise Stop(f"{n} changes, expected {want}")
            bad = verify(conn, plan, dst)
            if bad:
                raise Stop(f"{len(bad)} result(s) differ:\n  " + "\n  ".join(bad[:40]))
            now = conn.execute("SELECT count(*) FROM kjv_strongs").fetchone()[0]
            if now != total + net:
                raise Stop(f"kjv_strongs {now:,}, expected {total + net:,}")
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()
    print(f"{'written' if forward else 'put back'}: {want} changes on {len(plan)} words, every result read back; kjv_strongs {total:,} -> {now:,}")


def do_after(db, scan=True):
    plan = load_plan()
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        check_structure(conn)
        bad = verify(conn, plan, "after")
        if bad:
            raise Stop(f"{len(bad)} after-value(s) differ:\n  " + "\n  ".join(bad[:40]))
        print(f"after-values: all {len(plan)} rows read back from live")
        if scan:
            hit, firing = detector(conn, plan)
            print(f"the detector fires on {hit} of the {VERSE_COUNT} repaired verses; long-shift verses left in the KJV: {len(firing)}")
            if hit:
                raise Stop("a repaired verse still reads as shifted")
    finally:
        conn.close()
    print("AFTER DONE")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("check", "apply", "after", "undo"))
    ap.add_argument("--db", default=str(LIVE))
    a = ap.parse_args()
    try:
        if a.mode == "check":
            do_check(a.db)
        elif a.mode == "after":
            do_after(a.db)
        else:
            do_write(a.db, a.mode == "apply")
    except Stop as e:
        print(f"STOP: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
