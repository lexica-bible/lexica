#!/usr/bin/env python3
"""Locked test — scripts/audit_xref_vs_binding.py (read-only census + class column,
JP rulings 2026-10-24). Drives the real script on a real-shape fixture db, with the
REAL pinned tipnr/TIPNR.txt (the production parse the classes read):

  * POSITIVE FIRST: the two known faults — Gen 25:15 (xref H1908, bound to the
    H2301/H2316 man) and 1Ch 1:30 (same) — are reported, land in class 4, and the
    CONTROL passes
  * one fixture row per class, each lands in its class and no other:
      1 NT-SLOT (Act 9:1 Saul on Paul) · 2 NO-HEBREW-ENTITY (OT slot on Paul) ·
      3 COMPOUND one-slot (Obed-edom carrying Obed's H5744) and split (Hadad in
      "son of Hadad" on Ben-hadad) · 4 SAME-NAME (the controls + Shechem the man's
      H7928 on the town) · 5 VARIANT (Jehohanan carrying Johanan's H3110) ·
      6 PRINTED-NAME-DIFFERS (Artaxerxes printed, Ahasuerus bound) · 7 OTHER
      (Hebrews carrying H3066, which no TIPNR entity owns)
  * agreeing slots and slots with no render=1 binding are not reported
  * KJV's number resolves by name (Gen 25:15 -> H2316) and by bases (1Ch 1:30)
  * both lists written (first-run columns unchanged; classed list adds the class)
  * the database is never changed (byte-identical before/after)
  * a missing control -> exit 2, COUNT VOID; a control in the wrong class -> exit 2

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

_SCHEMA = """
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
    CREATE TABLE abp_surface (verse_id INTEGER, position INTEGER, form TEXT,
                              translit TEXT, PRIMARY KEY (verse_id, position));
    CREATE TABLE pn_binding (book INTEGER, chapter INTEGER, verse INTEGER, name TEXT,
                             entity_uniq TEXT, kind TEXT, rule TEXT, render INTEGER,
                             hot INTEGER, tier INTEGER);
    CREATE TABLE tipnr_entities (uniq TEXT PRIMARY KEY, head TEXT, section TEXT,
                                 gender TEXT, area TEXT, descr TEXT, summary TEXT,
                                 bases TEXT, parents TEXT, offspring TEXT);
    CREATE TABLE kjv_words (word_id INT, book_id INT, chapter INT, verse_num INT,
                            verse_pos INT, word TEXT);
    CREATE TABLE kjv_strongs (strongs_id TEXT, word_id INT);
"""

# (verse_id, book, ch, vs, pos, english, english_head, strongs_base, xref H or None,
#  xref class, bound uniq or None, render, expected class or None)
_SLOTS = [
    (1, "Gen", 25, 15, 1, "Hadar,", "Hadar", "*", "H1908", "lemma-only",
     "Hadad@Gen.25.15-1Ch", 1, "4 SAME-NAME-OTHER-REFERENT"),          # CONTROL
    (2, "1Ch", 1, 30, 4, "Hadad", "Hadad", "*", "H1908", "lemma-only",
     "Hadad@Gen.25.15-1Ch", 1, "4 SAME-NAME-OTHER-REFERENT"),          # CONTROL
    (3, "1Ki", 11, 14, 7, "Hadad", "Hadad", "*", "H1908", "lemma-only",
     "Hadad@1Ki.11.14-", 1, None),                                    # agrees
    (4, "1Ki", 11, 18, 21, "Hadad", "Hadad", "H1908", "H1908", "none",
     "Hadad@1Ki.11.14-", 1, None),                                    # kept-Hebrew, agrees
    (5, "Gen", 36, 35, 7, "Hadad", "Hadad", "*", "H1908", "lemma-only",
     "Hadad@1Ki.11.14-", 0, None),                                    # render=0 -> unbound
    (6, "Act", 9, 1, 2, "Saul", "Saul", "*", "H7586", "lemma-only",
     "Paul@Act.7.58-2Pe", 1, "1 NT-SLOT"),
    (7, "1Sa", 9, 2, 3, "Paul", "Paul", "*", "H7586", "lemma-only",
     "Paul@Act.7.58-2Pe", 1, "2 NO-HEBREW-ENTITY"),
    (8, "2Sa", 6, 10, 9, "Obed-edom", "Obed-edom", "*", "H5744", "lemma-only",
     "Obed-edom@2Sa.6.10-2Ch", 1, "3 COMPOUND"),
    (9, "1Ki", 15, 18, 40, "of Hadad,", "Hadad", "*", "H1908", "lemma-only",
     "Ben-hadad@1Ki.15.18-Jer", 1, "3 COMPOUND"),
    (10, "Gen", 33, 18, 6, "Shechem", "Shechem", "*", "H7928", "lemma-only",
     "Shechem@Gen.12.6-Act", 1, "4 SAME-NAME-OTHER-REFERENT"),
    (11, "1Ch", 26, 3, 5, "Jehohanan", "Jehohanan", "*", "H3110", "lemma-only",
     "Jehohanan@1Ch.26.3", 1, "5 VARIANT-NUMBER"),
    (12, "Est", 1, 1, 3, "Artaxerxes", "Artaxerxes", "*", "H783", "lemma-only",
     "Ahasuerus@Ezr.4.6-Dan", 1, "6 PRINTED-NAME-DIFFERS"),
    (13, "Gen", 14, 13, 8, "Hebrew", "Hebrew", "*", "H3066", "lemma-only",
     "Hebrews@Gen.14.13-Heb", 1, "7 OTHER"),
]
_ENTS = [   # tipnr_entities fixture rows: the REAL bases strings
    ("Hadad@Gen.25.15-1Ch", "hadad", "H2301,H2316"),
    ("Hadad@1Ki.11.14-", "hadad", "H111,H1908"),
    ("Paul@Act.7.58-2Pe", "paul", "G3972,G4549,G4569"),
    ("Obed-edom@2Sa.6.10-2Ch", "obed-edom", "H5654,H8096"),
    ("Ben-hadad@1Ki.15.18-Jer", "ben-hadad", "H1130"),
    ("Shechem@Gen.12.6-Act", "shechem", "G4966,H7927"),
    ("Jehohanan@1Ch.26.3", "jehohanan", "H3076"),
    ("Ahasuerus@Ezr.4.6-Dan", "ahasuerus", "H325"),
    ("Hebrews@Gen.14.13-Heb", "hebrews", "G1445,H5680"),
]


def _make_db(path, skip_control=None, control_bind=None):
    import entity_resolution as er
    c = sqlite3.connect(path)
    c.executescript(_SCHEMA)
    for (vid, book, ch, vs, pos, eng, head, sb, xh, xcls, uniq, render, _cls) in _SLOTS:
        c.execute("INSERT INTO verses VALUES (?,?,?,?)", (vid, book, ch, vs))
        c.execute("INSERT INTO words (verse_id, position, english, english_head, "
                  "strongs_base, strongs, is_pn) VALUES (?,?,?,?,?,?,1)",
                  (vid, pos, eng, head, sb, "*"))
        if xh:
            c.execute("INSERT INTO pn_hebrew_xref VALUES (?,?,?,?)", (vid, pos, xh, xcls))
            c.execute("INSERT INTO pn_greek_identity VALUES (?,?,NULL,'x','lemma-only',?)",
                      (vid, pos, xh))
        if uniq and (book, ch, vs) != skip_control:
            if (book, ch, vs) == (control_bind or (None,))[0:3]:
                uniq = control_bind[3]
            c.execute("INSERT INTO pn_binding VALUES (?,?,?,?,?,'exact','',?,0,1)",
                      (er.book_num(book), ch, vs, er.norm_name(head), uniq, render))
    c.executemany("INSERT INTO tipnr_entities (uniq, head, section, bases) "
                  "VALUES (?,?,'person',?)", _ENTS)
    c.execute("INSERT INTO abp_surface VALUES (1,1,'Χολδάδ','')")
    c.executescript("""
        INSERT INTO kjv_words VALUES (1,1,25,15,0,'Hadar'), (2,13,1,30,4,'Hadadd');
        INSERT INTO kjv_strongs VALUES ('H2316',1), ('H2301',2);
    """)
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


def _read(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    return [dict(zip(lines[0].split("\t"), ln.split("\t"))) for ln in lines[1:]], lines[0]


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
    check("control found in class 4 -> exit 0", rc, 0)
    check("CONTROL OK printed", "CONTROL OK — count valid." in out, True)
    check("both controls FOUND in class 4",
          out.count("  FOUND   [4 SAME-NAME-OTHER-REFERENT] "), 2)

    rows, hdr = _read(os.path.join(tmp, "a_classed.tsv"))
    got = {(r["book"], r["chapter"], r["verse"]): r["class"] for r in rows}
    want = {(b, str(ch), str(vs)): cls for (_v, b, ch, vs, _p, _e, _h, _sb, _x, _xc, _u,
                                             _r, cls) in _SLOTS if cls}
    check("every expected slot reported, each in its own class, nothing extra", got, want)
    check("every row classed exactly once",
          sorted(r["class"] for r in rows) == sorted(want.values()), True)
    pa = {(r["book"], r["chapter"]): r["printed_as"] for r in rows if r["class"] == "3 COMPOUND"}
    check("compound printed-as: Obed-edom one-slot, son-of-Hadad split",
          pa, {("2Sa", "6"): "one-slot", ("1Ki", "15"): "split"})
    kj = {(r["book"], r["chapter"]): (r["kjv_h"], r["kjv_how"], r["kjv_backed"])
          for r in rows if r["class"] == "4 SAME-NAME-OTHER-REFERENT"}
    check("KJV resolved by name / by bases on the controls, both KJV-backed",
          (kj.get(("Gen", "25")), kj.get(("1Ch", "1"))),
          (("H2316", "name", "yes"), ("H2301", "bases", "yes")))
    check("Greek form column carried", [r["greek_form"] for r in rows
                                        if r["book"] == "Gen" and r["chapter"] == "25"], ["Χολδάδ"])
    plain, phdr = _read(tsv)
    check("first-run list keeps its columns", phdr.split("\t")[-1], "frozen_h")
    check("first-run list has the same rows", len(plain), len(rows))
    check("summary: agree 2", "agree (stored in bases)       : 2" in out, True)
    check("summary: no binding 1 (render=0 row)", "no binding                      : 1" in out, True)
    check("summary: every row classed once line", "(every row classed once)        10 of 10" in out, True)
    check("summary: class 7 printed in full", "== CLASS 7 OTHER — all 1 in full ==" in out, True)
    check("database unchanged (read-only)", _md5(dbp), before)

    # control missing -> VOID
    dbp2 = os.path.join(tmp, "b.db")
    _make_db(dbp2, skip_control=("1Ch", 1, 30))
    rc, out = _run(dbp2, os.path.join(tmp, "b.tsv"))
    check("control missing -> exit 2", rc, 2)
    check("COUNT VOID printed", "COUNT VOID" in out, True)
    check("missing control named", "MISSING 1Ch 1:30" in out, True)

    # control bound to another entity -> not found -> VOID
    dbp3 = os.path.join(tmp, "c.db")
    _make_db(dbp3, control_bind=("1Ch", 1, 30, "Ben-hadad@1Ki.15.18-Jer"))
    rc, out = _run(dbp3, os.path.join(tmp, "c.tsv"))
    check("control re-bound elsewhere -> exit 2", rc, 2)
    check("re-bound control reported missing", "MISSING 1Ch 1:30" in out, True)

    # control FOUND but classed wrong -> VOID (the class gate itself must bite)
    import audit_xref_vs_binding as a
    real = a.classify
    a.classify = lambda r, tip: (a.OTHER if (r["book"], r["chapter"]) == ("1Ch", 1)
                                 else real(r, tip))
    try:
        rc, out = _run(dbp, os.path.join(tmp, "e.tsv"))
    finally:
        a.classify = real
    check("control misclassed -> exit 2", rc, 2)
    check("misclass named", "MISCLASSED [7 OTHER, want 4 SAME-NAME-OTHER-REFERENT]" in out, True)

    # required table absent -> exit 3
    dbp4 = os.path.join(tmp, "d.db")
    sqlite3.connect(dbp4).close()
    rc, out = _run(dbp4, os.path.join(tmp, "d.tsv"))
    check("tables absent -> exit 3", rc, 3)

    if fails:
        print("\n".join(fails))
        print(f"\n{len(fails)} FAILURE(S)")
        return 1
    print("\nAll audit_xref_vs_binding checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
