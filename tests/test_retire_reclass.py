#!/usr/bin/env python3
"""Locks the 2026-08-01 re-declaration of the Hebrew-retirement step (the 7/30
reclassification catch-up — receipt docs/tickets/RECLASS_catchup_declaration.md).

What is locked, each on a synthetic fixture db (no live data):
  T1  five-class handling: tipnr -> Greek, lemma-only/surface -> '*', none
      kept, abp-tag untouched; the xref records 'surface' rows as class
      'lemma-only' (G707 ship precedent) and never invents a 'surface' class.
  T2  RED — a sixth identity class HALTS before any row is processed (the
      door 'surface' walked in through is closed).
  T3  RED — --fresh-rebuild with an xref that disagrees with the identity
      table's frozen Hebrew record HALTS and drops nothing (the xref would be
      the sole carrier of the frozen record).
  T4  --fresh-rebuild with a clean oracle drops the stale xref and rebuilds it.
  T5  restore_frozen_pn puts drifted slots back to the frozen record and
      HALTS (red) when the count is not the declared one.

Run:  python tests/test_retire_reclass.py
"""
import os
import sqlite3
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RETIRE = os.path.join(HERE, "..", "scripts", "retire_hebrew_identity.py")
RESTORE = os.path.join(HERE, "..", "scripts", "restore_frozen_pn.py")

# (verse_id, position, greek_strongs, source, hebrew_base, words_value)
FIXTURE = [
    (1, 1, "G2424", "abp-tag",    None,   "G2424"),
    (1, 2, "G4549", "tipnr",      "H7586", "H7586"),
    (1, 3, None,    "lemma-only", "H1",   "H1"),
    (1, 4, None,    "lemma-only", None,   "*"),
    (1, 5, None,    "surface",    "H2",   "H2"),
    (1, 6, None,    "surface",    None,   "*"),
    (1, 7, None,    "none",       "H3",   "H3"),
    (1, 8, None,    "none",       None,   "*"),
]
SPLIT = "1,1,2,2,2"   # abp-tag, tipnr, lemma-only, surface, none


def make_db(path, rows=FIXTURE, with_xref=False, xref_break=False):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE words (verse_id INT, position INT, "
                 "strongs_base TEXT, english_head TEXT, is_pn INT DEFAULT 1)")
    conn.execute("CREATE TABLE pn_greek_identity (verse_id INT, position INT, "
                 "greek_strongs TEXT, greek_lemma TEXT, source TEXT, "
                 "hebrew_base TEXT, PRIMARY KEY (verse_id, position))")
    for vid, pos, g, src, heb, wval in rows:
        conn.execute("INSERT INTO pn_greek_identity VALUES (?,?,?,?,?,?)",
                     (vid, pos, g, None, src, heb))
        conn.execute("INSERT INTO words (verse_id, position, strongs_base, "
                     "english_head) VALUES (?,?,?,?)", (vid, pos, wval, src))
    if with_xref:
        conn.execute("CREATE TABLE pn_hebrew_xref (verse_id INT, position INT, "
                     "hebrew_base TEXT, class TEXT, "
                     "PRIMARY KEY (verse_id, position))")
        for vid, pos, g, src, heb, wval in rows:
            hb = "H999" if (xref_break and (vid, pos) == (1, 3)) else heb
            conn.execute("INSERT INTO pn_hebrew_xref VALUES (?,?,?,?)",
                         (vid, pos, hb, src))
    conn.commit()
    conn.close()


def run(script, db, *flags):
    return subprocess.run(
        [sys.executable, script, db, "--expect-split", SPLIT, *flags]
        if script == RETIRE else [sys.executable, script, db, *flags],
        capture_output=True, text=True)


def words_val(db, vid, pos):
    conn = sqlite3.connect(db)
    v = conn.execute("SELECT strongs_base FROM words WHERE verse_id=? AND "
                     "position=?", (vid, pos)).fetchone()[0]
    conn.close()
    return v


def t1_five_class_handling(tmp):
    db = os.path.join(tmp, "t1.db")
    make_db(db)
    r = run(RETIRE, db)
    assert r.returncode == 0, f"dry-run failed:\n{r.stdout}{r.stderr}"
    assert "class surface: declared 2, handled 2, remaining 0" in r.stdout
    r = run(RETIRE, db, "--apply")
    assert r.returncode == 0, f"apply failed:\n{r.stdout}{r.stderr}"
    assert words_val(db, 1, 2) == "G4549"   # tipnr gains its Greek number
    assert words_val(db, 1, 3) == "*"       # lemma-only retired
    assert words_val(db, 1, 5) == "*"       # surface retired (typed branch)
    assert words_val(db, 1, 7) == "H3"      # none keeps Hebrew
    assert words_val(db, 1, 1) == "G2424"   # abp-tag untouched
    conn = sqlite3.connect(db)
    classes = {r[0] for r in conn.execute(
        "SELECT DISTINCT class FROM pn_hebrew_xref")}
    surf_cls = conn.execute("SELECT class FROM pn_hebrew_xref WHERE verse_id=1 "
                            "AND position=5").fetchone()[0]
    n = conn.execute("SELECT count(*) FROM pn_hebrew_xref").fetchone()[0]
    conn.close()
    assert "surface" not in classes, "xref must never carry a 'surface' class"
    assert surf_cls == "lemma-only"
    assert n == len(FIXTURE)
    print("T1 five-class handling: PASS")


def t2_sixth_class_halts(tmp):
    db = os.path.join(tmp, "t2.db")
    make_db(db, FIXTURE + [(1, 9, None, "weird", "H4", "H4")])
    r = run(RETIRE, db, "--apply")
    assert r.returncode != 0, "a sixth class must HALT"
    assert "unknown identity class" in r.stdout
    assert words_val(db, 1, 3) == "H1", "halt must write nothing"
    print("T2 sixth-class halt (red-first): PASS")


def t3_fresh_rebuild_broken_oracle_halts(tmp):
    db = os.path.join(tmp, "t3.db")
    make_db(db, with_xref=True, xref_break=True)
    r = run(RETIRE, db, "--fresh-rebuild", "--apply")
    assert r.returncode != 0, "oracle mismatch must HALT"
    assert "NOT a byte-for-byte carrier" in r.stdout
    conn = sqlite3.connect(db)
    kept = conn.execute("SELECT 1 FROM sqlite_master WHERE "
                        "name='pn_hebrew_xref'").fetchone()
    conn.close()
    assert kept, "the stale xref must survive a failed oracle gate"
    print("T3 fresh-rebuild broken-oracle halt (red-first): PASS")


def t4_fresh_rebuild_clean(tmp):
    db = os.path.join(tmp, "t4.db")
    make_db(db, with_xref=True)
    r = run(RETIRE, db)   # without the flag: must still halt on table-exists
    assert r.returncode != 0 and "already exists" in r.stdout
    r = run(RETIRE, db, "--fresh-rebuild", "--apply")
    assert r.returncode == 0, f"clean fresh-rebuild failed:\n{r.stdout}{r.stderr}"
    assert words_val(db, 1, 2) == "G4549"
    conn = sqlite3.connect(db)
    n = conn.execute("SELECT count(*) FROM pn_hebrew_xref").fetchone()[0]
    conn.close()
    assert n == len(FIXTURE), "xref must be rebuilt with every row"
    print("T4 fresh-rebuild clean path: PASS")


def t5_restore_frozen(tmp):
    db = os.path.join(tmp, "t5.db")
    drift = [(v, p, g, s, h,
              "H3570" if (v, p) == (1, 2) else ("*" if (v, p) == (1, 5) else w))
             for v, p, g, s, h, w in FIXTURE]
    make_db(db, drift)   # (1,2) hand-fix re-broken; (1,5) import missed it
    r = run(RESTORE, db, "--expect", "1")
    assert r.returncode != 0, "wrong declared count must HALT (red)"
    r = run(RESTORE, db, "--expect", "2", "--apply")
    assert r.returncode == 0, f"restore failed:\n{r.stdout}{r.stderr}"
    assert words_val(db, 1, 2) == "H7586"
    assert words_val(db, 1, 5) == "H2"
    r = run(RETIRE, db, "--apply")
    assert r.returncode == 0, "retire must run clean after the restore"
    print("T5 restore_frozen_pn + chain order: PASS")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        t1_five_class_handling(tmp)
        t2_sixth_class_halts(tmp)
        t3_fresh_rebuild_broken_oracle_halts(tmp)
        t4_fresh_rebuild_clean(tmp)
        t5_restore_frozen(tmp)
    print("\nall retire-reclass locks PASS (5/5)")


if __name__ == "__main__":
    main()
