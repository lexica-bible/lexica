#!/usr/bin/env python3
"""
eu_retired_check.py — the edition upgrade's post-build check on RETIRED correction rows
(docs/handoffs/DESIGN_q2_build.md §9.61, amended §9.63; script approved §9.81).

Why: a retired row drops out of cert_invariants check 4, so nothing else would notice if the cure
it stood for did not land on the built copy. For every retired abp_corrections row, the built cell
must equal the row's corrected_value. For EXACTLY five prose rows (ids 51, 25, 27, 24, 45 — §9.63)
the built text may instead equal B's feed text for that verse. B's text is derived HERE through B's
own code (build_prose_from_app.feed_text over the pinned feed, via AppTransplant's own feed read),
then put through finish_rebuild step 5's em-dash swap (build_prose_from_app.emdash) — never retyped
from the DESIGN record, never read from the copy.

  PYTHONIOENCODING=utf-8 python3 scripts/eu_retired_check.py <built>

READ-ONLY: opens the copy mode=ro; refuses the live path (~/bible-db/bible.db) and a missing or
empty path. Any failing row prints its FULL source / corrected / feed / built text.

Summary line (grep this label): "RETIRED-ROW CHECK:"
  RETIRED-ROW CHECK: PASS 23/23 HOLD (corrected_value N - feed text N) ...   exit 0
  RETIRED-ROW CHECK: FAIL k of 23 ...                                          exit 1
  RETIRED-ROW CHECK: STOP <reason>                                             exit 2
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_prose_from_app as BP                     # noqa: E402  (B's own code + LIVE_DB)
from apply_abp_corrections import cellmatch           # noqa: E402  (the ONE cell compare)

LABEL = "RETIRED-ROW CHECK:"
EXPECTED_RETIRED = 23                                 # §9.59 retire set, PA 11/1
FEED_OK = {                                           # §9.63: id -> verse, and no others
    51: ("2Sa", 16, 18),
    25: ("1Ch", 22, 15),
    27: ("Job", 24, 19),
    24: ("Mat", 21, 19),
    45: ("Mar", 16, 17),
}


class Stop(Exception):
    pass


def check_target(path):
    if not path:
        raise Stop("a copy db path is required (no default)")
    p = Path(path).expanduser()
    if not p.is_file():
        raise Stop(f"copy db not found: {p}")
    if BP.LIVE_DB.is_file() and p.resolve() == BP.LIVE_DB.resolve():
        raise Stop(f"refusing the LIVE db {BP.LIVE_DB} - this check runs on the built copy only")
    return p


def check(db, feed_text, expected=EXPECTED_RETIRED, feed_ok=FEED_OK):
    """-> (results, failures). feed_text(key) = B's text for a verse key, before the em-dash swap;
    it is called only for the feed_ok verses."""
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                           "AND name='abp_corrections'").fetchone():
            raise Stop("no abp_corrections table on the copy")
        rows = con.execute(
            "SELECT id, book, chapter, verse, position, field, source_value, corrected_value, "
            "ledger_ref FROM abp_corrections WHERE status='retired' ORDER BY id").fetchall()
        if len(rows) != expected:
            raise Stop(f"{len(rows)} retired row(s) on the copy, expected {expected}")
        by_id = {r["id"]: r for r in rows}
        for i, key in feed_ok.items():
            r = by_id.get(i)
            if r is None or (r["book"], r["chapter"], r["verse"]) != key or r["field"] != "verses.text":
                raise Stop(f"feed-text id {i} is not the retired verses.text row for "
                           f"{key[0]} {key[1]}:{key[2]} on this copy")
        word_cols = {c[1] for c in con.execute("PRAGMA table_info(words)")}
        results, failures = [], []
        for r in rows:
            key = (r["book"], r["chapter"], r["verse"])
            ref = f"{key[0]} {key[1]}:{key[2]}"
            if r["field"] == "verses.text":
                hits = con.execute("SELECT text FROM verses WHERE book=? AND chapter=? AND verse=?",
                                   key).fetchall()
                where = "[verses.text]"
            else:
                if r["field"] not in word_cols:
                    raise Stop(f"id {r['id']}: '{r['field']}' is not a words column")
                hits = con.execute(
                    f'SELECT w."{r["field"]}" FROM words w JOIN verses v ON v.id = w.verse_id '
                    "WHERE v.book=? AND v.chapter=? AND v.verse=? AND w.position=?",
                    key + (r["position"],)).fetchall()
                where = f"pos {r['position']} {r['field']}"
            feed = BP.emdash(feed_text(key)) if r["id"] in feed_ok else None
            item = {"id": r["id"], "ref": ref, "where": where, "ledger": r["ledger_ref"],
                    "source": r["source_value"], "corrected": r["corrected_value"], "feed": feed}
            if len(hits) != 1:
                item.update(built=None, fail=True,
                            outcome=f"{len(hits)} matching cell(s), expected exactly 1")
                failures.append(item)
            else:
                built = hits[0][0]
                item["built"] = built
                if cellmatch(built, r["corrected_value"]):
                    item["outcome"] = "corrected_value"
                elif feed is not None and built == feed:
                    item["outcome"] = "feed text"
                else:
                    item.update(outcome="MATCHES NEITHER", fail=True)
                    failures.append(item)
            results.append(item)
        return results, failures
    finally:
        con.close()


def report(db, results, failures, expected=EXPECTED_RETIRED):
    print(f"== retired-row check (sec 9.61 / 9.63) on {db} (READ-ONLY) ==")
    for it in results:
        mark = "!!" if it.get("fail") else "ok"
        print(f"  {mark} id {it['id']:>3}  {it['ref']:<12} {it['where']:<24} [{it['ledger']}]  {it['outcome']}")
    for it in failures:
        print(f"\n  !! FAIL id {it['id']} {it['ref']} {it['where']} [{it['ledger']}] - {it['outcome']}")
        print(f"     source    : {it['source']!r}")
        print(f"     corrected : {it['corrected']!r}")
        if it["feed"] is not None:
            print(f"     feed text : {it['feed']!r}")
        print(f"     built     : {it['built']!r}")
    n_cor = sum(1 for it in results if it.get("outcome") == "corrected_value")
    n_feed = sum(1 for it in results if it.get("outcome") == "feed text")
    print()
    if failures:
        print(f"{LABEL} FAIL {len(failures)} of {expected} - see the FAIL lines above")
        return 1
    print(f"{LABEL} PASS {len(results)}/{expected} HOLD (corrected_value {n_cor} - feed text {n_feed})")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        if len(argv) != 1:
            raise Stop("usage: eu_retired_check.py <built copy db>")
        db = check_target(argv[0])
        app = BP.AppTransplant(BP.abp_source_texts())       # the pinned feed, B's own reader
        results, failures = check(db, lambda key: BP.feed_text(app, key))
    except (Stop, BP.FeedError, KeyError) as e:
        print(f"{LABEL} STOP {e}")
        return 2
    return report(db, results, failures)


if __name__ == "__main__":
    sys.exit(main())
