#!/usr/bin/env python3
"""apply_abp_corrections_exo2_11_20261124.py - Exo 2:11 "old er" -> "older" (DESIGN 9.266, rows 1-3).

Writes the three cleared cells (the verse text, word 8's English, word 8's head word) and registers each in
abp_corrections, so the next words rebuild re-applies them (prose at finish step 4b, word cells at step 7).
The rows are rows 1-3 of the sha-pinned rows_20261124.tsv the ruling chat cleared; rows 4-8 (printed forms)
are not part of this write (DESIGN 9.266 (4)).

  python3 scripts/apply_abp_corrections_exo2_11_20261124.py check   READ-ONLY: every before-value + every gate
  python3 scripts/apply_abp_corrections_exo2_11_20261124.py apply   the write: one all-or-nothing step
  python3 scripts/apply_abp_corrections_exo2_11_20261124.py after   READ-ONLY: every after-value + every gate
  python3 scripts/apply_abp_corrections_exo2_11_20261124.py undo    the way back, from the before-values

apply and undo each: refuse 13:00-14:30 UTC; take the write hold; re-read every starting value; write; read
every result back; count the changes (6); save only if all of that held.

What this write moves, each read by `after`:
  cert pin abp_corrections_active 403 -> 406
    (members abp_corrections_active_live_20261122.txt -> abp_corrections_active_live_20261124.txt)
What it does not move, each read by `check` and `after`: words 626,309 and verses 31,237; the frozen punct
list (punct_members_live_20261122.txt, 601 members, word-order check clean); the phrase-gloss gate (<= 747);
the frozen abp_surface fill (Exo 2:11 @8 is not a fill slot).
The pin in cert_invariants.py moves in its own commit AFTER `after` passes, so the code never claims 406
while live holds 403. Reuses the 11/22 batch's checks (apply_bible_text_batch_20261122.py) unchanged.
"""
import argparse
import collections
import contextlib
import io
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import apply_bible_text_batch_20261122 as B      # noqa: E402

Stop = B.Stop
ROWS = ROOT / "docs" / "handoffs" / "drafts" / "ABP_CORRECTIONS" / "rows_20261124.tsv"
ROWS_SHA = "47a8bd83b789514f0ab310443db35a12d2fbf81791ef2daa768609d124eec64f"   # cleared, DESIGN 9.266
ACTIVE_OLD, ACTIVE_OLD_SHA = B.ACTIVE_NEW, B.ACTIVE_NEW_SHA                       # the 403 on live since 11/22
ACTIVE_NEW = ROOT / "tests" / "fixtures" / "corrections" / "abp_corrections_active_live_20261124.txt"
ACTIVE_NEW_SHA = "1f5cec8fbae5b8326c289b8d272a912fcff77f29375c9368d76ac825b42b54f0"     # 403 + the 3 Exo 2:11 rows
ACTIVE_BEFORE, ACTIVE_AFTER = 403, 406
PUNCT, PUNCT_SHA, PUNCT_N = B.PUNCT_NEW, B.PUNCT_NEW_SHA, B.PUNCT_AFTER          # 601, frozen 11/22
KEY = ("Exo", 2, 11)
LEDGER = "EU-Exo2:11"
CREATED = "2026-11-24"
CHANGES = 6      # 1 verse + 2 word cells + 3 new correction rows
WORD_FIELDS = {"words.english": "english", "words.english_head": "english_head"}


def load_plan():
    got = B.sha(ROWS)
    if got != ROWS_SHA:
        raise Stop(f"{ROWS.name}: sha {got}, cleared {ROWS_SHA}")
    rows = B._rows(ROWS)
    if len(rows) != 8:
        raise Stop(f"{ROWS.name}: {len(rows)} rows, the cleared file has 8")
    mine = rows[:3]
    if [r["cell"] for r in mine] != ["verses.text", "words.english", "words.english_head"] \
            or any(B._ref(r["verse"]) != KEY for r in mine) or any(r["cell"].startswith("words") for r in rows[3:]) \
            or any(r["cell"] == "verses.text" for r in rows[3:]):
        raise Stop("rows 1-3 are not Exo 2:11's verse text, English and head word")
    prose = {"before": mine[0]["before"], "after": mine[0]["after"], "read": mine[0]["read"]}
    words = [{"pos": int(r["position_or_word_id"]), "field": WORD_FIELDS[r["cell"]],
              "before": r["before"], "after": r["after"], "read": r["read"]} for r in mine[1:]]
    if prose["before"].count("old er") != 1 or prose["before"].replace("old er", "older") != prose["after"] \
            or [(w["pos"], w["before"], w["after"]) for w in words] != [(8, "old er", "older"), (8, "er", "older")]:
        raise Stop("rows 1-3 are not the cleared old er -> older cells")
    return {"prose": prose, "words": words}


def new_rows(plan):
    """The 3 abp_corrections rows. Prose source_value = the text the rebuild's prose step writes (live with
    em-dashes back as '--', checked by check_feed); word source_value = the live cell. (DESIGN 9.80.)"""
    p = plan["prose"]
    out = [(*KEY, -1, "verses.text", p["before"].replace("—", "--"), p["after"], p["read"])]
    out += [(*KEY, w["pos"], w["field"], w["before"], w["after"], w["read"]) for w in plan["words"]]
    return out


def verify(conn, plan, side):
    """Every cell must hold its `side` value ('before' / 'after'). Returns the problem list."""
    bad = []
    def cell(what, got, want):
        if got != want:
            bad.append(f"{what}: reads {got!r}, expected {want!r}")
    try:
        got = B._one(conn, "SELECT text FROM verses WHERE book=? AND chapter=? AND verse=?", KEY, "verse Exo 2:11")[0]
        cell("Exo 2:11 verses.text", got, plan["prose"][side])
        for w in plan["words"]:
            got = B._one(conn, f"""SELECT w."{w['field']}" FROM words w JOIN verses v ON v.id = w.verse_id
                                   WHERE v.book=? AND v.chapter=? AND v.verse=? AND w.position=?""",
                         (*KEY, w["pos"]), f"word Exo 2:11 @{w['pos']}")[0]
            cell(f"Exo 2:11 @{w['pos']} {w['field']}", got, w[side])
        n = conn.execute("SELECT count(*) FROM abp_corrections WHERE status='active' AND applied_at='ingest'").fetchone()[0]
        cell("active correction rows", n, ACTIVE_BEFORE if side == "before" else ACTIVE_AFTER)
        for b, c, v, pos, fld, src, cor, _read in new_rows(plan):
            hits = conn.execute("""SELECT source_value, corrected_value, status, applied_at, ledger_ref FROM abp_corrections
                                   WHERE book=? AND chapter=? AND verse=? AND position=? AND field=?""",
                                (b, c, v, pos, fld)).fetchall()
            what = f"correction row {b} {c}:{v} @{pos} {fld}"
            if side == "before":
                cell(what + " (any status)", len(hits), 0)
            elif len(hits) != 1:
                bad.append(f"{what}: {len(hits)} rows, expected 1")
            else:
                cell(what, tuple(hits[0]), (src, cor, "active", "ingest", LEDGER))
    except Stop as e:
        bad.append(str(e))
    return bad


def check_feed(plan):
    """The prose row's source_value must be EXACTLY what the rebuild's prose step writes for Exo 2:11."""
    import build_prose_from_app as BP
    from build_words_from_abp import AppTransplant, abp_source_texts
    with contextlib.redirect_stdout(io.StringIO()):
        app = AppTransplant(abp_source_texts())
    src = new_rows(plan)[0][5]
    if app.decide(KEY)[0] != "compose":
        raise Stop("Exo 2:11: the rebuild's prose step would not write this verse")
    got = BP.feed_text(app, KEY, collections.Counter())
    if got != src:
        raise Stop(f"Exo 2:11: the prose step writes {got!r}, not the row's source_value")
    print("prose source: = the rebuild's own prose text for Exo 2:11, byte for byte")


def check_fill(plan):
    B.check_fill({"words": [{"key": KEY, "pos": w["pos"]} for w in plan["words"]]})


def _pins():
    for p, want in ((ACTIVE_OLD, ACTIVE_OLD_SHA), (ACTIVE_NEW, ACTIVE_NEW_SHA), (PUNCT, PUNCT_SHA)):
        if B.sha(p) != want:
            raise Stop(f"{p.name} is not the pinned file")


def run_cert(db):
    import cert_invariants as C
    old = C.PINS["abp_corrections_active"]
    C.PINS["abp_corrections_active"] = ACTIVE_AFTER     # this read only; the code's pin moves after it passes
    try:
        rc = C.run_suite(str(db))
    finally:
        C.PINS["abp_corrections_active"] = old
    if rc:
        raise Stop(f"cert_invariants did not read all green at {ACTIVE_AFTER}")


def _gates(db, plan):
    check_fill(plan)
    B.check_members(db, PUNCT, [], PUNCT_N)
    B.phrase_gloss(db)


def do_check(db):
    plan = load_plan()
    _pins()
    conn = B._ro(db)
    try:
        B.check_structure(conn)
        bad = verify(conn, plan, "before")
        if bad:
            raise Stop(f"{len(bad)} before-value(s) differ:\n  " + "\n  ".join(bad))
        print(f"before-values: Exo 2:11 verse text + 2 word cells, {ACTIVE_BEFORE} active rows, no Exo 2:11 row yet: all as cleared")
        n, h = B.active_sha(conn)
        if (n, h) != (ACTIVE_BEFORE, ACTIVE_OLD_SHA):
            raise Stop(f"active row list {n} / {h} is not the pinned {ACTIVE_BEFORE}")
        print(f"active corrections: {n}, member list sha {h} (= {ACTIVE_OLD.name})")
        check_feed(plan)
    finally:
        conn.close()
    _gates(db, plan)
    print(f"plan: 1 verse + 2 word cells + 3 new correction rows ({LEDGER}) = {CHANGES} changes")


def _write(conn, plan, forward):
    src, dst = ("before", "after") if forward else ("after", "before")
    p = plan["prose"]
    c = conn.execute("UPDATE verses SET text=? WHERE book=? AND chapter=? AND verse=? AND text=?", (p[dst], *KEY, p[src]))
    if c.rowcount != 1:
        raise Stop(f"verse Exo 2:11: {c.rowcount} rows written")
    for w in plan["words"]:
        c = conn.execute(f"""UPDATE words SET "{w['field']}"=? WHERE position=? AND "{w['field']}"=? AND verse_id=
                             (SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?)""",
                         (w[dst], w["pos"], w[src], *KEY))
        if c.rowcount != 1:
            raise Stop(f"word Exo 2:11 @{w['pos']} {w['field']}: {c.rowcount} rows written")
    for b, ch, v, pos, fld, s, cor, read in new_rows(plan):
        if forward:
            conn.execute("""INSERT INTO abp_corrections (book, chapter, verse, position, field, source_value, corrected_value,
                            reason, ledger_ref, applied_at, status, created) VALUES (?,?,?,?,?,?,?,?,?,'ingest','active',?)""",
                         (b, ch, v, pos, fld, s, cor, f"app-edition slip, DESIGN 9.266: {read}", LEDGER, CREATED))
        else:
            c = conn.execute("""DELETE FROM abp_corrections WHERE book=? AND chapter=? AND verse=? AND position=? AND field=?
                                AND source_value=? AND corrected_value=? AND created=? AND ledger_ref=? AND status='active'""",
                             (b, ch, v, pos, fld, s, cor, CREATED, LEDGER))
            if c.rowcount != 1:
                raise Stop(f"correction row {b} {ch}:{v} @{pos} {fld}: {c.rowcount} rows removed")


def do_write(db, forward):
    if B.in_window():
        raise Stop("13:00-14:30 UTC: not started (the nightly health check and backup)")
    plan = load_plan()
    _pins()
    src, dst = ("before", "after") if forward else ("after", "before")
    conn = sqlite3.connect(str(db), isolation_level=None)
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        B.check_structure(conn)
        if forward:
            check_feed(plan)
        conn.execute("BEGIN IMMEDIATE")
        try:
            bad = verify(conn, plan, src)
            if bad:
                raise Stop(f"{len(bad)} starting value(s) differ:\n  " + "\n  ".join(bad))
            start = conn.total_changes
            _write(conn, plan, forward)
            n = conn.total_changes - start
            if n != CHANGES:
                raise Stop(f"{n} changes, expected {CHANGES}")
            bad = verify(conn, plan, dst)
            if bad:
                raise Stop(f"{len(bad)} result(s) differ:\n  " + "\n  ".join(bad))
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()
    print(f"{'written' if forward else 'put back'}: {CHANGES} changes, every result read back")


def do_after(db):
    plan = load_plan()
    _pins()
    conn = B._ro(db)
    try:
        B.check_structure(conn)
        bad = verify(conn, plan, "after")
        if bad:
            raise Stop(f"{len(bad)} after-value(s) differ:\n  " + "\n  ".join(bad))
        print(f"after-values: Exo 2:11 verse text + 2 word cells + 3 new rows, {ACTIVE_AFTER} active rows: all as cleared")
        n, h = B.active_sha(conn)
        if (n, h) != (ACTIVE_AFTER, ACTIVE_NEW_SHA):
            raise Stop(f"active row list {n} / {h} is not the new pinned list")
        print(f"NEW PIN abp_corrections_active: {n}, member list sha {h} (= {ACTIVE_NEW.name})")
    finally:
        conn.close()
    _gates(db, plan)
    run_cert(db)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Exo 2:11 old er -> older (DESIGN 9.266).")
    ap.add_argument("mode", choices=["check", "apply", "after", "undo"])
    ap.add_argument("--db", default=str(B.LIVE))
    a = ap.parse_args(argv)
    db = Path(a.db).expanduser()
    label = a.mode.upper()
    try:
        if not db.is_file():
            raise Stop(f"no database at {db}")
        print(f"EXO211 {label} on {db} at {datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}")
        if a.mode == "check":
            do_check(db)
        elif a.mode == "apply":
            do_write(db, True)
        elif a.mode == "undo":
            do_write(db, False)
        else:
            do_after(db)
    except Stop as e:
        print(f"EXO211 {label} RESULT: STOP - {e}")
        print("Nothing was saved by this step." if a.mode in ("apply", "undo") else "This step only reads.")
        return 1
    print(f"EXO211 {label} RESULT: DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
