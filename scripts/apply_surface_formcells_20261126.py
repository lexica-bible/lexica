#!/usr/bin/env python3
"""apply_surface_formcells_20261126.py - the 10 printed-form cells (DESIGN 9.266 rows 4-8, 9.269).

Writes live abp_surface only, in one all-or-nothing step: 6 rows added (Psa 2:0 @1 τω; 1Jn 5:8 @2,3,4,6,7),
2 changed (1Sa 7:13 @9 ψου -> του; 1Ki 8:44 @25 οφ ης -> ης), 2 removed (Zec 3:5 @0 ανδ; Mat 6:13 @12
ότιδαγγερ). The rows are rows 4-8 of the cleared rows_20261124.tsv plus the five rows of
rows_1jn5_8_20261126.tsv, each sha-pinned.

  python3 scripts/apply_surface_formcells_20261126.py check   READ-ONLY: every before-value + every gate
  python3 scripts/apply_surface_formcells_20261126.py apply   the write: one all-or-nothing step
  python3 scripts/apply_surface_formcells_20261126.py after   READ-ONLY: every after-value + every gate
  python3 scripts/apply_surface_formcells_20261126.py undo    the way back, from the before-values

apply and undo each: refuse 13:00-14:30 UTC; take the write hold; re-read every starting value; write; read
every result back; count the changes (10); check every other abp_surface row is unchanged; save only if all
of that held.

What the write moves: abp_surface 395,014 -> 395,018 rows (read by `after`). The health floor (395,014) is
never crossed (the count only goes up); it moves to 395,018 in the pin commit after the re-freeze.
What a rebuild needs to put these back: the fill is re-frozen from a copy of live after this write, with
snapshot_surface_fill.py --from-restore <the 11/15 report> --amend tests/fixtures/surface_amend/
abp_surface_amend_20261126.tsv; `check` proves the amendment file names exactly these 10 slots and forms, and
that the pre-fill table holds what the freeze will compare against.
Each new Latin spelling is build_abp_translit's rule on the slot's dictionary word (lexicon by strongs_base),
the same rule the restore and the translit gate use; `check` stops if a cleared spelling differs from it.
"""
import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import apply_bible_text_batch_20261122 as B       # noqa: E402  (_rows, _ref, sha, in_window, Stop)

Stop = B.Stop
DRAFTS = ROOT / "docs" / "handoffs" / "drafts" / "ABP_CORRECTIONS"
ROWS = DRAFTS / "rows_20261124.tsv"
ROWS_SHA = "47a8bd83b789514f0ab310443db35a12d2fbf81791ef2daa768609d124eec64f"      # cleared, DESIGN 9.266
ROWS_1JN = DRAFTS / "rows_1jn5_8_20261126.tsv"
ROWS_1JN_SHA = "7c5ac81231939a383387b087d86233808c16120467047ce85a146f380665b9c0"  # brought for clearance, DESIGN 9.269
AMEND = ROOT / "tests" / "fixtures" / "surface_amend" / "abp_surface_amend_20261126.tsv"
AMEND_SHA = "acf9342309e043a806e25f0faf1cf35aa0cf935aec25b68a1400eb41429a7cd8"
PREFILL = Path("~/abp_surface_prefill_20261115.db").expanduser()                    # DESIGN 9.128, 9.134
LIVE = Path("~/bible-db/bible.db").expanduser()
SURFACE_BEFORE, SURFACE_AFTER = 395014, 395018
CHANGES = 10
CELL = "abp_surface.form | translit"
# the word each slot sits on (read off live 11/24-11/25); a different number there stops the run
STRONGS = {("Psa", 2, 0, 1): "3588", ("1Sa", 7, 13, 9): "3588", ("1Ki", 8, 44, 25): "3739",
           ("Zec", 3, 5, 0): "2532", ("Mat", 6, 13, 12): "3754", ("1Jn", 5, 8, 2): "1510.2.6",
           ("1Jn", 5, 8, 3): "3588", ("1Jn", 5, 8, 4): "3140", ("1Jn", 5, 8, 6): "3588", ("1Jn", 5, 8, 7): "1093"}
# what the pre-fill table (the builder chain's own table, before the fill) holds at each slot
PREFILL_AT = {("1Sa", 7, 13, 9): "ψου", ("Zec", 3, 5, 0): "ανδ", ("1Ki", 8, 44, 25): "οφ ης"}


def _cell(s, where):
    if s == "(no row)":
        return None
    parts = s.split(" | ")
    if len(parts) != 2 or not all(parts):
        raise Stop(f"{where}: cannot read {s!r}")
    return tuple(parts)


def load_plan():
    for p, want in ((ROWS, ROWS_SHA), (ROWS_1JN, ROWS_1JN_SHA), (AMEND, AMEND_SHA)):
        got = B.sha(p)
        if got != want:
            raise Stop(f"{p.name}: sha {got}, pinned {want}")
    rows = B._rows(ROWS)
    if len(rows) != 8:
        raise Stop(f"{ROWS.name}: {len(rows)} rows, the cleared file has 8")
    mine = rows[3:] + B._rows(ROWS_1JN)
    plan = []
    for r in mine:
        if r["cell"] != CELL:
            raise Stop(f"{r['verse']}: cell {r['cell']!r}, expected {CELL!r}")
        key = (*B._ref(r["verse"]), int(r["position_or_word_id"]))
        before, after = _cell(r["before"], key), _cell(r["after"], key)
        if before == after:
            raise Stop(f"{key}: before = after")
        plan.append({"key": key, "before": before, "after": after})
    if sorted(p["key"] for p in plan) != sorted(STRONGS):
        raise Stop("the rows are not the 10 ruled slots")
    return plan


def check_amend(plan):
    """The amendment file the re-freeze uses must name exactly these slots, with these forms."""
    import snapshot_surface_fill as sn
    am = {(a["book"], a["chapter"], a["verse"], a["position"]): a for a in sn.read_amend(AMEND)}
    if set(am) != {p["key"] for p in plan}:
        raise Stop("the amendment file does not name exactly the 10 slots")
    for p in plan:
        a, want = am[p["key"]], (p["after"][0] if p["after"] else "")
        old = p["before"][0] if p["before"] else ""
        act = {(False, True): ("insert",), (True, True): ("update", "change"),
               (True, False): ("remove", "drop")}[(bool(p["before"]), bool(p["after"]))]
        if a["action"] not in act or a["form"] != want or (a["action"] in ("change", "drop") and a["old_form"] != old):
            raise Stop(f"amendment row {p['key']}: {a['action']} {a['form']!r} / {a['old_form']!r} does not fit "
                       f"{p['before']} -> {p['after']}")
    print(f"amendment file: {AMEND.name}, the same 10 slots and forms as the write")


def _vid(conn, key):
    hit = conn.execute("SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?", key[:3]).fetchall()
    if len(hit) != 1:
        raise Stop(f"verse {key[:3]}: {len(hit)} rows")
    return hit[0][0]


def slots(conn, plan):
    """key -> (verse_id, position, strongs, strongs_base, lexicon lemma)."""
    out = {}
    for p in plan:
        vid, pos = _vid(conn, p["key"]), p["key"][3]
        w = conn.execute("""SELECT w.strongs, w.strongs_base, COALESCE(l.lemma, '') FROM words w
                            LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base
                            WHERE w.verse_id=? AND w.position=?""", (vid, pos)).fetchall()
        if len(w) != 1 or w[0][0] != STRONGS[p["key"]]:
            raise Stop(f"{p['key']}: word row {w!r}, expected one on {STRONGS[p['key']]}")
        out[p["key"]] = (vid, pos, *w[0])
    return out


def surface_row(conn, vid, pos):
    hit = conn.execute("SELECT form, translit FROM abp_surface WHERE verse_id=? AND position=?", (vid, pos)).fetchall()
    if len(hit) > 1:
        raise Stop(f"abp_surface ({vid}, {pos}): {len(hit)} rows")
    return tuple(hit[0]) if hit else None


def verify(conn, plan, side):
    bad = []
    try:
        where = slots(conn, plan)
        for p in plan:
            vid, pos = where[p["key"]][:2]
            got = surface_row(conn, vid, pos)
            if got != p[side]:
                bad.append(f"{p['key']}: reads {got!r}, expected {p[side]!r}")
        n = conn.execute("SELECT count(*) FROM abp_surface").fetchone()[0]
        want = SURFACE_BEFORE if side == "before" else SURFACE_AFTER
        if n != want:
            bad.append(f"abp_surface {n:,} rows, expected {want:,}")
    except Stop as e:
        bad.append(str(e))
    return bad


def check_translit(conn, plan):
    from build_abp_translit import romanize
    where = slots(conn, plan)
    for p in plan:
        if p["after"]:
            lem = where[p["key"]][4]
            want = romanize(p["after"][0], lem)
            if want != p["after"][1]:
                raise Stop(f"{p['key']}: cleared spelling {p['after'][1]!r}, the rule on {lem!r} gives {want!r}")
    print("new spellings: each = build_abp_translit's rule on the slot's dictionary word")


def check_structure(conn):
    trig = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='abp_surface'")]
    if trig:
        raise Stop(f"triggers on abp_surface: {trig}")
    mode = (conn.execute("PRAGMA journal_mode").fetchone()[0] or "").lower()
    if mode != "delete":
        raise Stop(f"journal_mode is {mode!r}, must be delete")
    w, v = (conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("words", "verses"))
    if (w, v) != (B.WORDS, B.VERSES):
        raise Stop(f"words {w:,} / verses {v:,}, expected {B.WORDS:,} / {B.VERSES:,}")
    print(f"structure: no triggers on abp_surface; journal delete; words {w:,}; verses {v:,}")


def check_prefill(plan, prefill):
    """The pre-fill table the re-freeze compares against: the builder's own rows at these slots."""
    if not prefill.is_file():
        raise Stop(f"no pre-fill table at {prefill}")
    conn = sqlite3.connect(f"file:{prefill}?mode=ro", uri=True)
    try:
        bad = []
        for p in plan:
            vid = _vid(conn, p["key"])
            got = surface_row(conn, vid, p["key"][3])
            want = PREFILL_AT.get(p["key"])
            if (got[0] if got else None) != want:
                bad.append(f"{p['key']}: pre-fill holds {got!r}, expected form {want!r}")
        if bad:
            raise Stop("pre-fill table:\n  " + "\n  ".join(bad))
    finally:
        conn.close()
    print(f"pre-fill table: ψου at 1Sa 7:13 @9, ανδ at Zec 3:5 @0, οφ ης at 1Ki 8:44 @25, none at the other 7")


def translit_gate(conn):
    import restore_surface_fill as rs
    n = len(rs.translit_would_change(conn))
    if n:
        raise Stop(f"build_abp_translit.py's rule would change {n} row(s) (expect 0)")
    print("translit rule over the whole table: 0 rows would change")


def _ro(db):
    return sqlite3.connect(f"file:{db}?mode=ro", uri=True)


def do_read(db, side, prefill):
    plan = load_plan()
    check_amend(plan)
    conn = _ro(db)
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        check_structure(conn)
        bad = verify(conn, plan, side)
        if bad:
            raise Stop(f"{len(bad)} {side}-value(s) differ:\n  " + "\n  ".join(bad))
        n = SURFACE_BEFORE if side == "before" else SURFACE_AFTER
        print(f"{side}-values: all 10 slots as cleared; abp_surface {n:,} rows")
        check_translit(conn, plan)
        translit_gate(conn)
    finally:
        conn.close()
    if side == "before":
        check_prefill(plan, prefill)
        print(f"plan: 6 added + 2 changed + 2 removed = {CHANGES} changes; abp_surface {SURFACE_BEFORE:,} -> {SURFACE_AFTER:,}")


def _write(conn, plan, where, forward):
    src, dst = ("before", "after") if forward else ("after", "before")
    for p in plan:
        vid, pos = where[p["key"]][:2]
        s, d = p[src], p[dst]
        if s and d:
            c = conn.execute("UPDATE abp_surface SET form=?, translit=? WHERE verse_id=? AND position=? AND form=? AND translit=?",
                             (*d, vid, pos, *s))
        elif d:
            c = conn.execute("INSERT INTO abp_surface (verse_id, position, form, translit) VALUES (?,?,?,?)", (vid, pos, *d))
        else:
            c = conn.execute("DELETE FROM abp_surface WHERE verse_id=? AND position=? AND form=? AND translit=?", (vid, pos, *s))
        if c.rowcount != 1:
            raise Stop(f"{p['key']}: {c.rowcount} rows written")


def _table(conn):
    return {(v, p): (f, t) for v, p, f, t in conn.execute("SELECT verse_id, position, form, translit FROM abp_surface")}


def do_write(db, forward):
    if B.in_window():
        raise Stop("13:00-14:30 UTC: not started (the nightly health check and backup)")
    plan = load_plan()
    check_amend(plan)
    src, dst = ("before", "after") if forward else ("after", "before")
    conn = sqlite3.connect(str(db), isolation_level=None)
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        check_structure(conn)
        conn.execute("BEGIN IMMEDIATE")
        try:
            bad = verify(conn, plan, src)
            if bad:
                raise Stop(f"{len(bad)} starting value(s) differ:\n  " + "\n  ".join(bad))
            where = slots(conn, plan)
            t0 = _table(conn)
            start = conn.total_changes
            _write(conn, plan, where, forward)
            n = conn.total_changes - start
            if n != CHANGES:
                raise Stop(f"{n} changes, expected {CHANGES}")
            bad = verify(conn, plan, dst)
            if bad:
                raise Stop(f"{len(bad)} result(s) differ:\n  " + "\n  ".join(bad))
            t1 = _table(conn)
            mine = {where[p["key"]][:2] for p in plan}
            other = [k for k in set(t0) | set(t1) if k not in mine and t0.get(k) != t1.get(k)]
            if other:
                raise Stop(f"{len(other)} other abp_surface row(s) changed")
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()
    a, b = (SURFACE_BEFORE, SURFACE_AFTER) if forward else (SURFACE_AFTER, SURFACE_BEFORE)
    print(f"{'written' if forward else 'put back'}: {CHANGES} changes, every result read back, every other row "
          f"unchanged; abp_surface {a:,} -> {b:,}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="The 10 printed-form cells (DESIGN 9.266, 9.269).")
    ap.add_argument("mode", choices=["check", "apply", "after", "undo"])
    ap.add_argument("--db", default=str(LIVE))
    ap.add_argument("--prefill", default=str(PREFILL))
    a = ap.parse_args(argv)
    db = Path(a.db).expanduser()
    label = a.mode.upper()
    try:
        if not db.is_file():
            raise Stop(f"no database at {db}")
        print(f"FORMCELLS {label} on {db} at {datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}")
        if a.mode == "check":
            do_read(db, "before", Path(a.prefill).expanduser())
        elif a.mode == "after":
            do_read(db, "after", Path(a.prefill).expanduser())
        else:
            do_write(db, a.mode == "apply")
    except Stop as e:
        print(f"FORMCELLS {label} RESULT: STOP - {e}")
        print("Nothing was saved by this step." if a.mode in ("apply", "undo") else "This step only reads.")
        return 1
    print(f"FORMCELLS {label} RESULT: DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
