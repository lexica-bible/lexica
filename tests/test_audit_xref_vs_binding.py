#!/usr/bin/env python3
"""Locked test — scripts/audit_xref_vs_binding.py (read-only census, JP ruling
2026-10-24). Drives the real script on a real-shape fixture db:

  * POSITIVE FIRST: the two known faults — Gen 25:15 (xref H1908, bound to the
    H2301/H2316 man) and 1Ch 1:30 (same) — are reported and the CONTROL passes
  * an agreeing slot (stored number IS one of the entity's bases) is not reported
  * a kept-Hebrew slot (number on the word, 'none' class) is checked too
  * a slot with no render=1 binding is not reported (counted as no_binding)
  * KJV's number resolves by name (Gen 25:15 -> H2316) and by bases
    (1Ch 1:30, KJV word spelled differently -> H2301)
  * the database is never changed (byte-identical before/after)
  * a db missing one control -> exit 2, COUNT VOID printed

Pure stdlib + temp on-disk SQLite. Run:  python tests/test_audit_xref_vs_binding.py
"""
import contextlib
import hashlib
import io
import os
import sqlite3
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))
sys.path.insert(0, _ROOT)


def _make_db(path, with_1ch=True):
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT);
        CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT,
                            english TEXT, english_head TEXT, strongs_base TEXT,
                            strongs TEXT, is_pn INT);
        CREATE TABLE pn_hebrew_xref (verse_id INTEGER NOT NULL, position INTEGER NOT NULL,
                                     hebrew_base TEXT, class TEXT NOT NULL,
                                     PRIMARY KEY (verse_id, position));
        CREATE TABLE pn_greek_identity (verse_id INT, position INT, greek_strongs TEXT,
                                        greek_lemma TEXT, source TEXT, hebrew_base TEXT,
                                        PRIMARY KEY (verse_id, position));
        CREATE TABLE pn_binding (book INTEGER, chapter INTEGER, verse INTEGER, name TEXT,
                                 entity_uniq TEXT, kind TEXT, rule TEXT, render INTEGER,
                                 hot INTEGER, tier INTEGER);
        CREATE TABLE tipnr_entities (uniq TEXT PRIMARY KEY, head TEXT, section TEXT,
                                     gender TEXT, area TEXT, descr TEXT, summary TEXT,
                                     bases TEXT, parents TEXT, offspring TEXT);
        CREATE TABLE kjv_words (word_id INT, book_id INT, chapter INT, verse_num INT,
                                verse_pos INT, word TEXT);
        CREATE TABLE kjv_strongs (strongs_id TEXT, word_id INT);

        INSERT INTO verses VALUES (1,'Gen',25,15),(2,'1Ch',1,30),(3,'1Ki',11,14),
                                  (4,'1Ki',11,18),(5,'Gen',36,35);
        INSERT INTO words VALUES
            (1,1,1,'Hadar,','Hadar','*','*',1),       -- KNOWN FAULT (xref-only)
            (2,1,3,'Tema,','Tema','*','*',1),         -- agrees
            (3,2,4,'Hadad','Hadad','*','*',1),        -- KNOWN FAULT (xref-only)
            (4,3,7,'Hadad','Hadad','*','*',1),        -- agrees (Edomite Hadad)
            (5,4,21,'Hadad','Hadad','H1908','*',1),   -- kept-Hebrew, agrees
            (6,5,7,'Hadad','Hadad','*','*',1),        -- no render=1 binding
            (7,4,2,'and','and','G2532','2532',0);     -- not a name, no number
        INSERT INTO pn_hebrew_xref VALUES
            (1,1,'H1908','lemma-only'), (1,3,'H8485','lemma-only'),
            (2,4,'H1908','lemma-only'), (3,7,'H1908','lemma-only'),
            (4,21,'H1908','none'),      (5,7,'H1908','lemma-only');
        INSERT INTO pn_greek_identity VALUES
            (1,1,NULL,'Χολδάδ','surface','H1908'),
            (2,4,NULL,'Αδάδ','lemma-only','H1908');
        INSERT INTO tipnr_entities (uniq, head, section, bases) VALUES
            ('Hadad@Gen.25.15-1Ch','hadad','person','H2301,H2316'),
            ('Hadad@1Ki.11.14-','hadad','person','H111,H1908'),
            ('Tema@Gen.25.15-1Ch','tema','person','H8485');
        INSERT INTO pn_binding VALUES
            (1,25,15,'hadar','Hadad@Gen.25.15-1Ch','ruled','spelling-equiv',1,0,1),
            (1,25,15,'tema','Tema@Gen.25.15-1Ch','exact','',1,0,1),
            (11,11,14,'hadad','Hadad@1Ki.11.14-','exact','',1,0,1),
            (11,11,18,'hadad','Hadad@1Ki.11.14-','exact','',1,0,1),
            (1,36,35,'hadad','Hadad@1Ki.11.14-','exact','',0,0,1);  -- render=0
        INSERT INTO kjv_words VALUES
            (1,1,25,15,0,'Hadar'), (2,1,25,15,2,'Tema'),
            (3,13,1,30,4,'Hadadd');   -- spelled differently: resolves by bases
        INSERT INTO kjv_strongs VALUES ('H2316',1), ('H8485',2), ('H2301',3);
    """)
    if with_1ch:
        c.execute("INSERT INTO pn_binding VALUES "
                  "(13,1,30,'hadad','Hadad@Gen.25.15-1Ch','exact','',1,0,1)")
    c.commit()
    c.close()


def _md5(p):
    with open(p, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _run(dbp, tsv):
    import audit_xref_vs_binding as a
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = a.main(["audit", dbp, "--tsv", tsv])
    return rc, buf.getvalue()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    fails = []

    def check(desc, got, want):
        if got != want:
            fails.append(f"  FAIL: {desc}\n        got {got!r}, want {want!r}")
        else:
            print(f"  ok: {desc}")

    tmp = tempfile.mkdtemp()
    dbp, tsv = os.path.join(tmp, "a.db"), os.path.join(tmp, "a.tsv")
    _make_db(dbp)
    before = _md5(dbp)
    rc, out = _run(dbp, tsv)
    check("control found -> exit 0", rc, 0)
    check("CONTROL OK printed", "CONTROL OK — count valid." in out, True)
    check("both controls FOUND", out.count("  FOUND   "), 2)

    with open(tsv, encoding="utf-8") as f:
        lines = f.read().splitlines()
    rows = [dict(zip(lines[0].split("\t"), ln.split("\t"))) for ln in lines[1:]]
    got = sorted((r["book"], r["chapter"], r["verse"], r["position"], r["stored_h"],
                  r["entity"], r["kjv_h"], r["kjv_how"], r["frozen_h"]) for r in rows)
    check("exactly the two faults reported, KJV resolved both ways, frozen copy shown", got, [
        ("1Ch", "1", "30", "4", "H1908", "Hadad@Gen.25.15-1Ch", "H2301", "bases", "H1908"),
        ("Gen", "25", "15", "1", "H1908", "Hadad@Gen.25.15-1Ch", "H2316", "name", "H1908"),
    ])
    check("summary: mismatched 2", "MISMATCHED                    : 2" in out, True)
    check("summary: agree 3 (Tema, 1Ki 11:14, kept-Hebrew 1Ki 11:18)",
          "agree (stored in bases)       : 3" in out, True)
    check("summary: no binding 1 (render=0 row ignored)",
          "no binding                      : 1" in out, True)
    check("summary: distinct entities 1", "distinct entities                 : 1" in out, True)
    check("top-20 line names the pair", "H1908   -> Hadad@Gen.25.15-1Ch" in out, True)
    check("database unchanged (read-only)", _md5(dbp), before)

    # control missing -> VOID
    dbp2, tsv2 = os.path.join(tmp, "b.db"), os.path.join(tmp, "b.tsv")
    _make_db(dbp2, with_1ch=False)
    rc, out = _run(dbp2, tsv2)
    check("control missing -> exit 2", rc, 2)
    check("COUNT VOID printed", "COUNT VOID" in out, True)
    check("missing control named", "MISSING 1Ch 1:30" in out, True)

    # required table absent -> exit 3
    dbp3 = os.path.join(tmp, "c.db")
    sqlite3.connect(dbp3).close()
    rc, out = _run(dbp3, os.path.join(tmp, "c.tsv"))
    check("tables absent -> exit 3", rc, 3)

    if fails:
        print("\n".join(fails))
        print(f"\n{len(fails)} FAILURE(S)")
        return 1
    print("\nAll audit_xref_vs_binding checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
