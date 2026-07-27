#!/usr/bin/env python3
"""Locked test for scripts/retire_hebrew_identity.py (R-2 candidate 3 rewrite
site of record — reviewer ruling 2026-07-25).

Fixture mirrors the real table shapes. Covers:
  * dry-run: verifies + plans, writes NOTHING
  * apply: rewrites per class (tipnr -> Greek, lemma-only -> '*', none kept,
    abp-tag untouched), fills pn_hebrew_xref (NULL hebrew_base exactly on
    abp-tag, no empty strings), GLOB invariant clean
  * HALT detectors control-tested on known positives (certification rule —
    a detector that never fired proves nothing): class-split mismatch,
    words-vs-snapshot disagreement, second run on the same copy
Run:  python tests/test_retire_builder.py
"""
import os
import sqlite3
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "retire_hebrew_identity.py")
SPLIT = "--expect-split"


def _make_db(path):
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT,
                             verse INT, text TEXT);
        CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT,
                            english TEXT, english_head TEXT, strongs_base TEXT,
                            strongs TEXT, is_pn INT);
        CREATE TABLE pn_greek_identity (
            verse_id INTEGER NOT NULL, position INTEGER NOT NULL,
            greek_strongs TEXT, greek_lemma TEXT, source TEXT NOT NULL,
            hebrew_base TEXT, PRIMARY KEY (verse_id, position));
        INSERT INTO verses VALUES (1,'1Sa',15,8,''),(2,'1Sa',15,7,''),
                                  (3,'1Sa',15,6,''),(4,'Mat',1,6,'');
        INSERT INTO words (id, verse_id, position, english, english_head,
                           strongs_base, strongs, is_pn) VALUES
            (1,1,3,'Agag','Agag','H90','*',1),        -- tipnr (from H)
            (2,2,4,'Havilah','Havilah','H2341','*',1),-- lemma-only (from H)
            (3,3,5,'Kenite','Kenite','H7017','*',1),  -- none (Hebrew kept)
            (4,4,5,'David','David','G1138','1138',1), -- abp-tag
            (5,1,5,'seized','seized','G4815','4815',0),
            -- the always-'*' sub-shapes the 2026-07-25 trial halt surfaced:
            (6,2,6,'Bougaion','Bougaion','*','*',1),  -- tipnr, never had Hebrew
            (7,3,7,'Chous','Chous','*','*',1),        -- lemma-only, already '*'
            (8,4,8,'Nod','Nod','*','*',1);            -- none, always '*'
        INSERT INTO pn_greek_identity VALUES
            (1,3,'G9826',NULL,'tipnr','H90'),
            (2,4,NULL,'Euilat','lemma-only','H2341'),
            (3,5,NULL,NULL,'none','H7017'),
            (4,5,'G1138',NULL,'abp-tag',NULL),
            (2,6,'G9917',NULL,'tipnr',NULL),
            (3,7,NULL,'Xous','lemma-only',NULL),
            (4,8,NULL,NULL,'none',NULL);
    """)
    c.commit()
    c.close()


# The builder prints em-dashes; on Windows a piped child defaults to cp1252,
# so force its output to UTF-8 to match the encoding we read with.
_ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def _run(dbp, *extra):
    return subprocess.run(
        [sys.executable, SCRIPT, dbp, SPLIT, "1,2,2,2", *extra],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT, env=_ENV)


def main() -> int:
    fails = []

    def check(desc, got, want):
        if got != want:
            fails.append(f"  FAIL: {desc}\n        got {got!r}, want {want!r}")
        else:
            print(f"  ok: {desc}")

    tmp = tempfile.mkdtemp()
    dbp = os.path.join(tmp, "retire.db")
    _make_db(dbp)

    # dry-run: verifies, writes nothing
    r = _run(dbp)
    check("dry-run exits 0", r.returncode, 0)
    check("dry-run announces no writes", "[DRY RUN] No changes written" in r.stdout, True)
    c = sqlite3.connect(dbp)
    check("dry-run wrote no xref table", c.execute(
        "SELECT count(*) FROM sqlite_master WHERE name='pn_hebrew_xref'").fetchone()[0], 0)
    check("dry-run left words untouched", c.execute(
        "SELECT strongs_base FROM words WHERE id=1").fetchone()[0], "H90")
    c.close()

    # apply: the full write set
    r = _run(dbp, "--apply")
    check("apply exits 0", r.returncode, 0)
    c = sqlite3.connect(dbp)
    got = {i: s for i, s in c.execute("SELECT id, strongs_base FROM words")}
    check("tipnr row -> Greek", got[1], "G9826")
    check("lemma-only row -> '*'", got[2], "*")
    check("'none' row keeps Hebrew (C3-Q1)", got[3], "H7017")
    check("abp-tag row untouched", got[4], "G1138")
    check("non-PN word untouched", got[5], "G4815")
    check("always-'*' tipnr row -> Greek (gain)", got[6], "G9917")
    check("always-'*' lemma-only row stays '*'", got[7], "*")
    check("always-'*' none row stays '*'", got[8], "*")
    xref = {(v, p): (h, cl) for v, p, h, cl in c.execute(
        "SELECT verse_id, position, hebrew_base, class FROM pn_hebrew_xref")}
    check("xref row count", len(xref), 7)
    check("xref none-class marker queryable", xref[(3, 5)], ("H7017", "none"))
    check("abp-tag hebrew_base is NULL (declared)", xref[(4, 5)], (None, "abp-tag"))
    check("always-'*' rows carry NULL hebrew_base",
          [xref[(2, 6)], xref[(3, 7)], xref[(4, 8)]],
          [(None, "tipnr"), (None, "lemma-only"), (None, "none")])
    check("GLOB invariant clean", c.execute(
        "SELECT count(*) FROM words WHERE strongs_base GLOB '[0-9]*'").fetchone()[0], 0)
    c.close()

    # Binder xref-sourced guard (reviewer ruling 2026-07-25): the PRODUCTION
    # occ_base_parts, both branches. Post-apply, every word must present its
    # PRE-retirement guard number byte-for-byte.
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import build_entity_binding as beb

    def _guard_numbers(dbpath):
        c2 = sqlite3.connect(dbpath)
        base_col, xref_join, has_xref = beb.occ_base_parts(c2)
        got = {i: b for i, b in c2.execute(
            f"SELECT w.id, {base_col} FROM words w {xref_join} WHERE w.is_pn = 1")}
        c2.close()
        return got, has_xref

    pre = os.path.join(tmp, "retire_pre.db")
    _make_db(pre)                     # a fresh pre-retirement copy
    pre_nums, pre_x = _guard_numbers(pre)
    check("binder guard: table absent -> stored numbers, no join", pre_x, False)
    post_nums, post_x = _guard_numbers(dbp)   # the applied copy
    check("binder guard: table present -> xref branch", post_x, True)
    check("binder guard numbers byte-identical pre vs post (all PN words)",
          post_nums, pre_nums)

    # HALT controls — each detector fired on a known positive
    r = _run(dbp, "--apply")
    check("second run on same copy HALTS", r.returncode != 0, True)
    check("...naming the single-shot rule", "single-shot" in r.stdout, True)

    dbp2 = os.path.join(tmp, "retire_split.db")
    _make_db(dbp2)
    r = subprocess.run([sys.executable, SCRIPT, dbp2, SPLIT, "9,9,9,9"],
                       capture_output=True, text=True, encoding="utf-8", cwd=ROOT, env=_ENV)
    check("wrong class split HALTS", r.returncode != 0, True)

    dbp3 = os.path.join(tmp, "retire_drift.db")
    _make_db(dbp3)
    c = sqlite3.connect(dbp3)
    c.execute("UPDATE words SET strongs_base='H99' WHERE id=1")  # drift vs snapshot
    c.commit(); c.close()
    r = _run(dbp3)
    check("words-vs-snapshot disagreement HALTS (dry-run too)", r.returncode != 0, True)
    check("...naming the moved column", "moved since stage 1" in r.stdout, True)

    if fails:
        print("\n".join(fails))
        print(f"\n{len(fails)} FAILURE(S)")
        return 1
    print("\nAll retirement-builder checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
