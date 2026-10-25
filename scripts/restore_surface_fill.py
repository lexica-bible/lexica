#!/usr/bin/env python3
"""
restore_surface_fill.py — rebuild-trap fix, parts (a) second half + (b) + G1
(CHARTER_rebuild_trap_fix.md §2): re-apply the frozen 2026-10-25 abp_surface fill AFTER
/rebuild-words step 9 (builder + both backfills + translit), re-keyed onto the rebuilt words.

THIS LANE: COPIES ONLY. It refuses the live database and any file named bible.db. Landing it on
live (step 9 runs on live after the swap, charter §1) is a later, separately ruled change.

Without --apply it is a DRY RUN: every database is opened read-only and the only file written is
the --report TSV. With --apply it writes ONLY abp_surface, in one transaction, and only if every
gate passes — otherwise nothing at all is written (all or nothing; never a partial fill).

Inputs: <db> (the rebuilt copy, step 9 done) · --snapshot (snapshot_surface_fill.py's TSV; its
.sha256 must match) · --lexicon (abp_helps/analytical_lexicon.tsv) · --report (per-slot TSV) ·
--prefill (optional: the pre-fill copy; on a same-code rebuild the builder output must equal it).

Per slot (JP rulings 2026-10-26; THE key rules are dryrun_rekey_fill.key2_at / key1_at / decide):
  key 2 (primary)  verse_id + full strongs + the snapshot's ordinal k
  key 1 (check)    verse_id + full strongs + the snapshot's old English (exact bytes)
  placed = key 2 one slot, key 1 confirms: agree-strong (key 1 = that slot) or agree-weak (key 1
  several, key 2's among them) — agree-weak rows are LISTED, never silently picked.
  Then, at the new slot:
    update  the builder's form there must equal the recorded old form   (else reason 3)
    insert  the slot must be empty                                       (else reason 4)
    Lexicon-backed class: number + form agree (apply's own rule)         (else reason 5)
Reasons (closed list, charter §2b): 1 no slot · 2 ambiguous · 3 update precondition · 4 insert
target filled · 5 number + form disagree · 6 key 1 none / several without key 2's slot · 7 key
conflict. Placed + unplaced = 4,411.

Gates (STOP before any write):
  S    snapshot = 4,411 rows (3,873 insert + 538 update), distinct slots, checksum matches
  V    every snapshot verse_id names the same book/chapter/verse in <db>
  G1a  the builder chain's table = 391,130 rows exactly (the base the fill was laid on)
  G1b  (--prefill given) builder table = the pre-fill copy row for row (same-code rebuild only)
  G2   every slot placed (unplaced = 0)
  G1   after the writes, before COMMIT: abp_surface = 395,003 rows exactly; the 4,411 written
       rows = snapshot form + romanize(form, lemma of the NEW slot); every other row unchanged;
       new rows = exactly the insert slots
  T    after COMMIT: build_abp_translit.py's rule would change 0 rows; quick_check ok
A table already at 395,003 with every slot holding its form reads ALREADY RESTORED (no write,
exit 0); any other table count is a G1a STOP; a mix of restored and not-restored slots fails.

  PYTHONIOENCODING=utf-8 python3 scripts/restore_surface_fill.py ~/rekey/built3.db \\
      --snapshot tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv \\
      --lexicon abp_helps/analytical_lexicon.tsv --prefill ~/bible.db.pre-surface-fill-20261025 \\
      --report ~/rekey/restore_dry.tsv            # add --apply to write (copies only)
"""
import argparse
import os
import sqlite3
import sys
from collections import Counter
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dryrun_rekey_fill as dr                     # noqa: E402  the key rules + the live gate
import snapshot_surface_fill as snap               # noqa: E402  the file format

ROWS_BASE, ROWS_AFTER = 391130, 395003
N_ROWS, N_INSERT, N_UPDATE = 4411, 3873, 538
# Pinned after the first PA snapshot (2026-10-26 lane); until then the .sha256 file alone vouches.
SNAPSHOT_SHA256 = None

REASONS = {1: "no slot (key 2 found none)", 2: "ambiguous",
           3: "update precondition (builder form != recorded old form)",
           4: "insert target not empty", 5: "number + form disagree at the new slot",
           6: "key 1 none / several without key 2's slot", 7: "key conflict"}

Stop, say, real = dr.Stop, dr.say, dr.real


def check(ok, msg):
    say(f"   {'PASS' if ok else 'FAIL'}  {msg}")
    if not ok:
        raise Stop(msg)


def check_paths(a, live):
    if dr.is_live(a.db, live):
        raise Stop(f"{a.db} is the live database (or a file named bible.db) — refused. "
                   "This lane restores onto COPIES only.")
    if not os.path.isfile(real(a.db)):
        raise Stop(f"{a.db}: no such file")
    if a.prefill:
        if dr.is_live(a.prefill, live) or not os.path.isfile(real(a.prefill)):
            raise Stop(f"--prefill {a.prefill}: missing, or the live database")
        if real(a.prefill) == real(a.db):
            raise Stop("--prefill and <db> must be two different files")
    if not os.path.isfile(real(a.lexicon)):
        raise Stop(f"--lexicon {a.lexicon}: no such file")
    rep = real(a.report)
    if rep.endswith(".db") or rep in {real(a.db), real(a.snapshot), real(a.lexicon)} \
            or (a.prefill and rep == real(a.prefill)) or dr.is_live(a.report, live):
        raise Stop(f"--report {a.report} must be a new report file, not a database or an input")


def load_snapshot(path):
    say("S   the frozen snapshot")
    rows, hexd = snap.read_snapshot(path)
    say(f"    sha256 {hexd}")
    if SNAPSHOT_SHA256 is not None:
        check(hexd == SNAPSHOT_SHA256, f"checksum = the pinned {SNAPSHOT_SHA256[:16]}…")
    keys = {(r["verse_id"], r["position"]) for r in rows}
    acts = Counter(r["action"] for r in rows)
    check(len(rows) == N_ROWS and len(keys) == N_ROWS,
          f"{len(rows):,} rows, {len(keys):,} distinct slots (expect {N_ROWS:,})")
    check((acts["insert"], acts["update"]) == (N_INSERT, N_UPDATE) and len(acts) == 2,
          f"insert {acts['insert']:,} / update {acts['update']:,} (expect {N_INSERT:,} / {N_UPDATE:,})")
    bad = [r for r in rows if not r["form"] or (r["action"] == "update") != (r["old_form"] is not None)]
    check(not bad, f"every row has a form; old form present exactly on updates ({len(bad)} bad)")
    return rows, hexd


def lemmas(con, keys):
    """(verse_id, position) -> the lemma build_abp_translit.py romanizes with (one query)."""
    want = set(keys)
    out = {}
    for v, p, lem in con.execute(
            "SELECT w.verse_id, w.position, COALESCE(l.lemma,'') FROM words w "
            "LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base"):
        if (v, p) in want:
            out[(v, p)] = lem
    return out


def translit_would_change(con):
    """Rows whose stored translit != what build_abp_translit.py would write — same SQL as
    build_abp_translit.py:85-91 (and apply_abp_surface_fill.translit_stale_outside)."""
    from build_abp_translit import romanize
    return [(v, p) for v, p, f, t, lem in con.execute(
        "SELECT s.verse_id, s.position, s.form, s.translit, COALESCE(l.lemma,'') FROM abp_surface s "
        "JOIN words w ON w.verse_id=s.verse_id AND w.position=s.position "
        "LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base WHERE s.form IS NOT NULL AND s.form <> ''")
        if romanize(f, lem) != (t or "")]


# ── the re-key (read-only) ───────────────────────────────────────────────────
def evaluate(con, rows, lex, restoring):
    """One pass over the snapshot -> list of result dicts. `restoring` = the table is at the
    builder base (preconditions 3/4 apply); else the ALREADY check (each placed slot must
    already hold its form)."""
    from apply_abp_surface_fill import LEXICON_CLASSES        # the ONE class list
    from census_abp_surface_glued import agree                # the ONE number + form rule
    vids = {r["verse_id"] for r in rows}
    new_w = dr.words_for(con, vids)
    surface = dr.surface(con)
    out = []
    for r in rows:
        vid = r["verse_id"]
        new_rows = new_w.get(vid, [])
        k2 = dr.key2_at(r["strongs"], r["k2_ordinal"], new_rows)
        k1 = dr.key1_at(r["strongs"], r["english"], new_rows)
        reason, detail = dr.decide(k2, k1)
        np = k2[1] if reason == 0 else None
        state, lexres = "", "uncovered"
        if reason == 0:
            cur = surface.get((vid, np))
            if not restoring:
                state = "already" if cur and cur[0] == r["form"] else "missing"
            elif r["action"] == "update" and (cur is None or cur[0] != r["old_form"]):
                reason, detail = 3, f"builder form {cur[0] if cur else None!r} != old {r['old_form']!r}"
            elif r["action"] == "insert" and cur is not None:
                reason, detail = 4, f"slot holds {cur[0]!r}"
        want = LEXICON_CLASSES.get(r["cls"])
        if reason == 0 and want:
            s = next(x[1] for x in new_rows if x[0] == np)
            ag = agree(lex, s, r["form"])
            lexres = "pass" if ag in want else "fail"
            if lexres == "fail":
                reason, detail = 5, f"agree() -> {ag}"
        out.append(dict(row=r, k2=k2, k1=k1, reason=reason, detail=detail, lex=lexres,
                        new_pos=np if reason == 0 else None, state=state))
    return out


def write_report(path, res):
    with open(real(path), "w", encoding="utf-8", newline="\n") as f:
        f.write("book\tchapter\tverse\told_position\tnew_position\taction\tcls\tis_pn\tform\t"
                "key2\tkey1\tresult\treason\tdetail\tlexicon\n")
        for x in res:
            r = x["row"]
            f.write("\t".join(str(v) for v in (
                r["book"], r["chapter"], r["verse"], r["position"],
                "" if x["new_pos"] is None else x["new_pos"], r["action"], r["cls"], r["is_pn"],
                r["form"], f"{x['k2'][0]}:{x['k2'][1]}", f"{x['k1'][0]}:{x['k1'][1]}",
                "placed" if not x["reason"] else "unplaced", x["reason"] or "", x["detail"],
                x["lex"])) + "\n")


def table_diff(con, other):
    """(rows only in <db>, rows only in other) for abp_surface, whole rows."""
    con.execute(f"ATTACH DATABASE '{Path(real(other)).as_uri()}?mode=ro' AS pf")
    try:
        a = con.execute("SELECT count(*) FROM (SELECT * FROM main.abp_surface EXCEPT "
                        "SELECT * FROM pf.abp_surface)").fetchone()[0]
        b = con.execute("SELECT count(*) FROM (SELECT * FROM pf.abp_surface EXCEPT "
                        "SELECT * FROM main.abp_surface)").fetchone()[0]
    finally:
        con.execute("DETACH DATABASE pf")
    return a, b


# ── the write (copies only) ──────────────────────────────────────────────────
def apply(db, res):
    from build_abp_translit import romanize
    from census_abp_surface_glued import NB
    say("W   APPLY — one transaction, abp_surface only")
    con = sqlite3.connect(f"file:{real(db)}", uri=True, isolation_level=None)
    con.execute("PRAGMA busy_timeout=60000")
    try:
        jm = con.execute("PRAGMA journal_mode").fetchone()[0].lower()
        check(jm == "delete", f"journal mode {jm!r} (must be 'delete'; never WAL on PA)")
        con.execute("BEGIN IMMEDIATE")
        try:
            before = dr.surface(con)
            check(len(before) == ROWS_BASE, f"table still {len(before):,} rows under the write lock")
            todo = [(x["row"], (x["row"]["verse_id"], x["new_pos"])) for x in res]
            lem = lemmas(con, [k for _, k in todo])
            tl = {}
            for r, k in todo:
                if k not in lem:
                    raise Stop(f"no word row at new slot {k}")
                tl[k] = romanize(r["form"], lem[k])
            for r, (v, p) in todo:
                if r["action"] == "update":
                    cur = con.execute("UPDATE abp_surface SET form=?, translit=? WHERE verse_id=? "
                                      "AND position=? AND form=?", (r["form"], tl[(v, p)], v, p,
                                                                     r["old_form"]))
                    if cur.rowcount != 1:
                        raise Stop(f"update {r['book']} {r['chapter']}:{r['verse']} pos {p}: "
                                   "old form not as recorded")
                else:                                       # a filled slot raises: no overwrite
                    con.execute("INSERT INTO abp_surface (verse_id, position, form, translit) "
                                "VALUES (?,?,?,?)", (v, p, r["form"], tl[(v, p)]))
            say("   post-write checks (before COMMIT):")
            n = con.execute("SELECT count(*) FROM abp_surface").fetchone()[0]
            check(n == ROWS_AFTER, f"G1 abp_surface = {n:,} rows (expect {ROWS_AFTER:,} exactly)")
            after = dr.surface(con)
            wk = {k for _, k in todo}
            bad = [k for r, k in todo if after.get(k) != (r["form"], tl[k])]
            check(not bad, f"the {len(todo):,} written rows = snapshot form + new-slot translit "
                           f"({len(bad)} differ)")
            other = [k for k in set(after) | set(before) if k not in wk and after.get(k) != before.get(k)]
            check(not other, f"every other row unchanged ({len(other)} differ)")
            ins = {k for r, k in todo if r["action"] == "insert"}
            check(set(after) - set(before) == ins, "new rows = exactly the insert slots")
            g6 = [k for r, k in todo if NB in r["form"] or "ἡ" in r["form"]]
            check(not g6, f"written forms carry no NBSP and no ἡ ({len(g6)} fail)")
            con.execute("COMMIT")
            say("   COMMITTED")
        except BaseException:
            if con.in_transaction:
                con.execute("ROLLBACK")
                say("   ROLLED BACK — the copy is exactly as it was before this step")
            raise
        say("T   after the write")
        stale = translit_would_change(con)
        check(not stale, f"build_abp_translit.py's rule would change {len(stale)} row(s) (expect 0)")
        qc = con.execute("PRAGMA quick_check").fetchall()
        check(qc == [("ok",)], f"quick_check {qc[:3]}")
        return n
    finally:
        con.close()


# ── main ─────────────────────────────────────────────────────────────────────
def run(a, live=dr.LIVE):
    check_paths(a, live)
    from census_abp_surface_glued import Lexicon
    say("=" * 78)
    say(f"restore_surface_fill — {'APPLY (copy only)' if a.apply else 'DRY RUN, read-only'}")
    say(f"  db        {real(a.db)}  ({os.path.getsize(real(a.db)):,} bytes)")
    say(f"  snapshot  {real(a.snapshot)}")
    say("=" * 78)
    rows, hexd = load_snapshot(a.snapshot)

    con = dr.ro(a.db)
    try:
        say("V   verse ids")
        vt = dr.verses(con)
        badv = [r for r in rows if vt.get(r["verse_id"]) != (r["book"], r["chapter"], r["verse"])]
        check(not badv, f"every snapshot verse_id names the same verse in <db> ({len(badv)} differ)")
        n0 = con.execute("SELECT count(*) FROM abp_surface").fetchone()[0]
        say("G1a builder chain's table")
        restoring = n0 == ROWS_BASE
        if not restoring and n0 != ROWS_AFTER:
            check(False, f"abp_surface = {n0:,} rows — expect {ROWS_BASE:,} (step 9 done, fill "
                         f"not yet restored) or {ROWS_AFTER:,} (already restored)")
        say(f"   {'PASS' if restoring else 'NOTE'}  abp_surface = {n0:,} rows "
            f"({'= the builder base' if restoring else '= the restored total: checking ALREADY'})")
        diff = None
        if a.prefill and restoring:
            say("G1b builder table vs the pre-fill copy (same-code rebuild)")
            diff = table_diff(con, a.prefill)
            say(f"   rows only in <db> {diff[0]:,} · only in the pre-fill copy {diff[1]:,} (expect 0 / 0)")
        say("    loading the Analytical Lexicon …")
        lex = Lexicon(real(a.lexicon))
        say("RE-KEY + preconditions")
        res = evaluate(con, rows, lex, restoring)
    finally:
        con.close()
    write_report(a.report, res)

    placed = [x for x in res if x["reason"] == 0]
    unplaced = [x for x in res if x["reason"]]
    agreement = Counter(x["detail"] for x in placed)
    weak = [x for x in placed if x["detail"] == "agree-weak"]
    moved = [x for x in placed if x["new_pos"] != x["row"]["position"]]
    by_reason = Counter(x["reason"] for x in unplaced)
    p_ins = sum(1 for x in placed if x["row"]["action"] == "insert")
    p_upd = len(placed) - p_ins

    if weak:
        say(f"\nAGREE-WEAK rows ({len(weak):,}): key 1 found several slots, key 2's among them "
            "(the verse repeats the same number + English) — verse · position · English · key-1 slots")
        for x in weak:
            r = x["row"]
            say(f"    {r['book']} {r['chapter']}:{r['verse']} · pos {r['position']}→{x['new_pos']} · "
                f"{r['english']!r} · {x['k1'][1]}")
    if unplaced:
        say(f"\nUNPLACED rows ({len(unplaced):,}): verse · old pos · action · reason")
        for x in unplaced:
            r = x["row"]
            say(f"    {r['book']} {r['chapter']}:{r['verse']} · pos {r['position']} · {r['action']} · "
                f"reason {x['reason']} {x['detail']}")
    if moved:
        say(f"\nPLACED rows that MOVED ({len(moved):,}): verse · old pos → new pos")
        for x in moved[:200]:
            r = x["row"]
            say(f"    {r['book']} {r['chapter']}:{r['verse']} · {r['position']} → {x['new_pos']}")

    say(f"\n  per-slot report: {real(a.report)} ({len(res):,} rows)")
    say("\nSUMMARY (expected | actual)")
    say(f"  snapshot rows             {N_ROWS:,} | {len(rows):,}   sha256 {hexd[:16]}…")
    say(f"  table before              {ROWS_BASE:,} | {n0:,}")
    if diff is not None:
        say(f"  vs pre-fill copy          0 / 0 | {diff[0]:,} / {diff[1]:,}")
    say(f"  placed                    {N_ROWS:,} | {len(placed):,}   (agree-strong "
        f"{agreement.get('agree-strong', 0):,} · agree-weak {agreement.get('agree-weak', 0):,})")
    say(f"  unplaced                  0 | {len(unplaced):,}   "
        + " · ".join(f"r{n} {by_reason[n]:,}" for n in sorted(by_reason)))
    say(f"  placed inserts / updates  {N_INSERT:,} / {N_UPDATE:,} | {p_ins:,} / {p_upd:,}")
    say(f"  placed rows that moved    — | {len(moved):,}")
    say(f"  Lexicon witness (placed)  — | {dict(sorted(Counter(x['lex'] for x in placed).items()))}")

    if not restoring:
        missing = [x for x in placed if x["state"] != "already"]
        ok = not unplaced and not missing
        say(f"  already holding its form  {N_ROWS:,} | {len(placed) - len(missing):,}")
        say("RESULT: " + ("ALREADY RESTORED — nothing to write" if ok else
                          "FAIL — table is at the restored total but not every slot holds its form"))
        return 0 if ok else 1

    gates_ok = not unplaced and len(placed) == N_ROWS and (diff is None or diff == (0, 0))
    if not a.apply:
        say("RESULT: DRY RUN COMPLETE — nothing written to any database · "
            + ("every gate PASSES (an --apply would write)" if gates_ok else
               "a gate FAILS (an --apply would write NOTHING)"))
        return 0 if gates_ok else 1
    if not gates_ok:
        say("RESULT: STOPPED before any write — " +
            ("G1b builder table != pre-fill copy" if diff not in (None, (0, 0)) else
             f"G2 {len(unplaced):,} slot(s) unplaced — G1 cannot reach {ROWS_AFTER:,}") +
            " · nothing written")
        return 1
    n1 = apply(a.db, res)
    say(f"  G1 table after            {ROWS_AFTER:,} | {n1:,}")
    say("RESULT: RESTORED, ALL CHECKS PASS (on a copy)")
    return 0


def main(argv=None, live=dr.LIVE):
    ap = argparse.ArgumentParser(description="Re-apply the frozen abp_surface fill (copies only).")
    ap.add_argument("db")
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--lexicon", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--prefill")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    try:
        return run(a, live)
    except Stop as e:
        say(f"\nSTOPPED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
