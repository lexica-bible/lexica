#!/usr/bin/env python3
"""Locked test for the candidate-3 INSTRUMENT updates (reviewer ruling
2026-07-25: an audit tool that silently reads the wrong home is worse than a
builder that does). Both branches of both instruments:

  audit_two_derivations.py (via subprocess, the real script):
    * pre-retirement fixture  -> Hebrew-keyed counts from words, controls
      assert the single-home state, exit 0
    * post-retirement fixture (produced by the REAL retire_hebrew_identity.py)
      -> counts from pn_hebrew_xref, N1/N5 assert the ruled dual-home state
      (Maacah '*'+H4601-in-xref, Abijah G7+H29-in-xref), exit 0
    * CONTROL: a sabotaged xref (Maacah's Hebrew number deleted) FAILS N1

  cert_invariants.check_corrections (direct call, the real function):
    * correction holding in words -> no problems (both branches)
    * value moved to the xref (lemma-only, words '*') -> no problems
    * CONTROLS fire on known positives: missing xref row; kept-Hebrew ('none')
      row with a wrong cell gets NO exemption

Run:  python tests/test_c3_instruments.py
"""
import os
import sqlite3
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, ROOT)


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
        CREATE TABLE pn_binding (book INT, chapter INT, verse INT, name TEXT,
                                 entity_uniq TEXT, render INT);
        INSERT INTO verses VALUES
            (1,'2Ch',11,21,''),(2,'Ezr',5,3,''),(3,'Jos',19,14,''),
            (4,'1Ch',3,10,''),(5,'Mat',1,6,'');
        INSERT INTO words (id, verse_id, position, english, english_head,
                           strongs_base, strongs, is_pn) VALUES
            (1,1,2,'Maacha','Maacha','H4601','*',1),
            (2,2,3,'Shetharboznai','Shetharboznai','H8370','*',1),
            (3,3,4,'Jiphthahel','Jiphthahel','H3317','*',1),
            (4,4,5,'Abia','Abia','H29','*',1),
            (5,5,6,'David','David','G1138','1138',1);
        -- Classes mirror the 7/30 reclassification as re-pinned 2026-08-01
        -- (RECLASS_catchup_declaration.md): shetharboznai none->surface,
        -- jiphthahel none->lemma-only; the audit's N2/N3 controls now expect
        -- the retired '*' state for both.
        INSERT INTO pn_greek_identity VALUES
            (1,2,NULL,'Mocha','lemma-only','H4601'),
            (2,3,NULL,'Sathrabouzane','surface','H8370'),
            (3,4,NULL,'Iephthael','lemma-only','H3317'),
            (4,5,'G7',NULL,'tipnr','H29'),
            (5,6,'G1138',NULL,'abp-tag',NULL);
        -- book_num('2Ch') = 14 (KJV numbering used by the binder)
        INSERT INTO pn_binding VALUES (14,11,21,'maacha','Maacah@1Ki.15.2',1);
    """)
    c.commit()
    c.close()


# Spawned scripts print em-dashes; on Windows a piped child defaults to cp1252,
# so force its output to UTF-8 to match the encoding we read with.
_ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def _audit(dbp):
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "audit_two_derivations.py"), dbp],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT, env=_ENV)


def main() -> int:
    fails = []

    def check(desc, got, want):
        if got != want:
            fails.append(f"  FAIL: {desc}\n        got {got!r}, want {want!r}")
        else:
            print(f"  ok: {desc}")

    tmp = tempfile.mkdtemp()

    # ── two-derivations: pre-retirement branch ──────────────────────────────
    pre = os.path.join(tmp, "pre.db")
    _make_db(pre)
    r = _audit(pre)
    check("audit pre: exit 0 (all controls pass)", r.returncode, 0)
    check("audit pre: single-home N1", "found 'Maacha' base=H4601" in r.stdout, True)
    check("audit pre: agreement clean", "disagree: 0" in r.stdout, True)

    # ── two-derivations: post-retirement branch (real retirement applied) ───
    post = os.path.join(tmp, "post.db")
    _make_db(post)
    rr = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "retire_hebrew_identity.py"),
         post, "--expect-split", "1,1,2,1,0", "--apply"],  # 5-class order (2026-08-01): abp-tag,tipnr,lemma-only,surface,none
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT, env=_ENV)
    check("retirement applied on the instrument fixture", rr.returncode, 0)
    r = _audit(post)
    check("audit post: exit 0 (dual-home controls pass)", r.returncode, 0)
    check("audit post: N1 dual-home (words '*', xref H4601)",
          "found 'Maacha' words=* xref=H4601" in r.stdout, True)
    check("audit post: N5 dual-home (words G7, xref H29)",
          "found 'Abia' words=G7 xref=H29" in r.stdout, True)
    check("audit post: agreement reproduced from the xref home",
          "disagree: 0" in r.stdout, True)

    # CONTROL: sabotage the xref -> N1 must FAIL and the audit exit 1
    c = sqlite3.connect(post)
    c.execute("UPDATE pn_hebrew_xref SET hebrew_base = NULL WHERE verse_id=1")
    c.commit(); c.close()
    r = _audit(post)
    check("audit CONTROL: sabotaged xref fails (exit 1)", r.returncode, 1)
    check("audit CONTROL: N1 named as the failure", "[FAIL] N1" in r.stdout, True)

    # ── cert check #4: both branches + controls ─────────────────────────────
    from cert_invariants import check_corrections

    def _cert_db(path, cell, xref_row):
        cc = sqlite3.connect(path)
        cc.executescript("""
            CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT,
                                 verse INT, text TEXT);
            CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT,
                                english TEXT, strongs_base TEXT);
            CREATE TABLE abp_corrections (book TEXT, chapter INT, verse INT,
                position INT, field TEXT, corrected_value TEXT, source_value TEXT,
                status TEXT, applied_at TEXT);
            INSERT INTO verses VALUES (1,'2Sa',18,21,'');
            INSERT INTO abp_corrections VALUES
                ('2Sa',18,21,4,'strongs_base','H3569','H3570','active','ingest');
        """)
        cc.execute("INSERT INTO words VALUES (1,1,4,'Cushi',?)", (cell,))
        if xref_row:
            cc.execute("""CREATE TABLE pn_hebrew_xref (verse_id INT, position INT,
                          hebrew_base TEXT, class TEXT)""")
            cc.execute("INSERT INTO pn_hebrew_xref VALUES (1,4,?,?)", xref_row)
        cc.commit()
        cc.row_factory = sqlite3.Row
        return cc

    cc = _cert_db(os.path.join(tmp, "c1.db"), "H3569", None)
    check("cert pre: holding correction -> no problems",
          check_corrections(cc, expected_active=1), [])
    cc.close()
    cc = _cert_db(os.path.join(tmp, "c2.db"), "*", ("H3569", "lemma-only"))
    check("cert post: moved-to-xref correction -> no problems",
          check_corrections(cc, expected_active=1), [])
    cc.close()
    cc = _cert_db(os.path.join(tmp, "c3.db"), "*", None)
    check("cert CONTROL: '*' with NO xref table still FAILS",
          len(check_corrections(cc, expected_active=1)), 1)
    cc.close()
    cc = _cert_db(os.path.join(tmp, "c4.db"), "*", ("H3569", "none"))
    check("cert CONTROL: kept-Hebrew class gets NO exemption",
          len(check_corrections(cc, expected_active=1)), 1)
    cc.close()

    if fails:
        print("\n".join(fails))
        print(f"\n{len(fails)} FAILURE(S)")
        return 1
    print("\nAll candidate-3 instrument checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
