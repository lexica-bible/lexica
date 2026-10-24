#!/usr/bin/env python3
"""Locked test — scripts/correct_xref_vs_binding.py (JP rulings 2026-10-24).
Real-shape fixture db + the REAL pinned tipnr/TIPNR.txt; drives the real script.

  * HARD GUARD fires on a Cushi-shaped row (Zep 1:1: stored H3570 = KJV H3570,
    TIPNR says H3569) -> LEAVE, never changed — and the guard is checked FIRST
  * one fixture row per rule, each gets its own decision:
      R1 REMOVE (Paul, NT and a kept-Hebrew OT word) · R2 LEAVE (Esther Artaxerxes)
      · R3 SWAP same-name (Gen 25:15 -> H2316, 1Ch 1:30 -> H2301, Shechem kept-Hebrew
      word), compound (son of Hadad -> H1130), variant (Jehohanan), printed-name
      spelling mix-up (Gen 46:13 "Job" -> H3102) · R4 SWAP third number (Psa 87:4
      Rahab -> H7294) · R5 HOLD (class 7) · R6 LEAVE (variant, no KJV) · R7 HOLD
      (no KJV witness) · SAFETY HOLD (frozen copy disagrees)
  * an agreeing slot is not in the plan
  * dry run writes nothing (db byte-identical)
  * --apply on a copy: xref + frozen copy + (kept-Hebrew) word all changed, row kept
    on REMOVE with an empty number; Hadad H1908 loses exactly the two Ishmael slots
    and the Ben-hadad slot (4 -> 1); every count matches the plan; a second run
    finds nothing left to change
  * a plan row that no longer matches the db -> whole apply rolled back, db unchanged
  * a broken control (guard row's KJV witness gone) -> exit 2, PLAN VOID
  * --rebuild-step: reads + writes the WORD only; xref untouched

Run:  python tests/test_correct_xref_vs_binding.py
"""
import contextlib
import hashlib
import io
import os
import shutil
import sqlite3
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))
sys.path.insert(0, _ROOT)

from test_audit_xref_vs_binding import _SCHEMA   # same real-shape tables

# (vid, book, ch, vs, pos, english, head, word strongs_base, xref H, class, uniq,
#  kjv word or None, kjv H or None, frozen H override or None)
_SLOTS = [
    (1, "Gen", 25, 15, 1, "Hadar,", "Hadar", "*", "H1908", "lemma-only",
     "Hadad@Gen.25.15-1Ch", "Hadar", "H2316", None),               # R3 -> H2316
    (2, "1Ch", 1, 30, 4, "Hadad", "Hadad", "*", "H1908", "lemma-only",
     "Hadad@Gen.25.15-1Ch", "Hadadd", "H2301", None),              # R3 -> H2301 (bases)
    (3, "1Ki", 11, 14, 7, "Hadad", "Hadad", "*", "H1908", "lemma-only",
     "Hadad@1Ki.11.14-", None, None, None),                        # agrees
    (4, "1Ki", 15, 18, 40, "of Hadad,", "Hadad", "*", "H1908", "lemma-only",
     "Ben-hadad@1Ki.15.18-Jer", "Benhadad", "H1130", None),        # R3 compound
    (5, "Zep", 1, 1, 8, "Cushi,", "Cushi", "*", "H3570", "lemma-only",
     "Cushi@Zep.1.1", "Cushi", "H3570", None),                     # GUARD
    (6, "Act", 9, 1, 2, "Saul", "Saul", "*", "H7586", "tipnr",
     "Paul@Act.7.58-2Pe", None, None, None),                       # R1 remove (NT)
    (7, "1Sa", 9, 2, 3, "Paul", "Paul", "H7586", "H7586", "none",
     "Paul@Act.7.58-2Pe", None, None, None),                       # R1 remove, word too
    (8, "Est", 1, 1, 8, "Artaxerxes", "Artaxerxes", "*", "H783", "lemma-only",
     "Ahasuerus@Ezr.4.6-Dan", "Ahasuerus", "H325", None),          # R2 leave
    (9, "Gen", 33, 18, 6, "Shechem", "Shechem", "H7928", "H7928", "none",
     "Shechem@Gen.12.6-Act", "Shechem", "H7927", None),            # R3, word too
    (10, "1Ch", 26, 3, 5, "Jehohanan", "Jehohanan", "*", "H3110", "lemma-only",
     "Jehohanan@1Ch.26.3", "Jehohanan", "H3076", None),            # R3 variant
    (11, "Gen", 46, 13, 7, "Job,", "Job", "*", "H347", "lemma-only",
     "Jashub@Gen.46.13-1Ch", "Job", "H3102", None),                # R3 spelling mix-up
    (12, "Psa", 87, 4, 1, "of Rahab", "Rahab", "*", "H7343", "lemma-only",
     "Egypt@Gen.12.10-Rev", "Rahab", "H7294", None),               # R4 third number
    (13, "Gen", 14, 13, 8, "Hebrew", "Hebrew", "*", "H3066", "lemma-only",
     "Hebrews@Gen.14.13-Heb", "Hebrew", "H5680", None),            # R5 hold
    (14, "1Ch", 26, 4, 5, "Jehohanan", "Jehohanan", "*", "H3110", "lemma-only",
     "Jehohanan@1Ch.26.3", None, None, None),                      # R6 leave
    (15, "Gen", 12, 6, 4, "Shechem.", "Shechem", "*", "H7928", "lemma-only",
     "Shechem@Gen.12.6-Act", None, None, None),                    # R7 hold
    (16, "Num", 26, 46, 5, "Sarah.", "Sarah", "*", "H8283", "lemma-only",
     "Serah@Gen.46.17-1Ch", "Sarah", "H8294", "H9999"),            # SAFETY hold
    (17, "Gen", 35, 5, 4, "Shechem.", "Shechem", "*", "H7928", "lemma-only",
     "Shechem@Gen.12.6-Act", None, None, None),                    # R0 ruled swap
    (18, "Mat", 4, 18, 8, "Galilee,", "Galilee", "*", "H1551", "lemma-only",
     "Chinnereth@Num.34.11-Jhn", None, None, None),                # R0 ruled leave
    (19, "1Ch", 5, 23, 13, "Baal", "Baal", "*", "H1168", "lemma-only",
     "Hermon_Mount@Deu.3.8-Ezk", None, None, None),                # R0 ruled hold
]
_ENTS = [
    ("Hadad@Gen.25.15-1Ch", "hadad", "H2301,H2316"), ("Hadad@1Ki.11.14-", "hadad", "H111,H1908"),
    ("Ben-hadad@1Ki.15.18-Jer", "ben-hadad", "H1130"), ("Cushi@Zep.1.1", "cushi", "H3569"),
    ("Paul@Act.7.58-2Pe", "paul", "G3972,G4549,G4569"), ("Ahasuerus@Ezr.4.6-Dan", "ahasuerus", "H325"),
    ("Shechem@Gen.12.6-Act", "shechem", "G4966,H7927"), ("Jehohanan@1Ch.26.3", "jehohanan", "H3076"),
    ("Jashub@Gen.46.13-1Ch", "jashub", "H3102"),
    ("Egypt@Gen.12.10-Rev", "egypt", "G124,G125,H2526,H4693,H4713,H4714,H4805,H7293"),
    ("Hebrews@Gen.14.13-Heb", "hebrews", "G1445,H5680"), ("Serah@Gen.46.17-1Ch", "serah", "H8294"),
    ("Chinnereth@Num.34.11-Jhn", "chinnereth", "G1056,G5085,H3672"),
    ("Hermon_Mount@Deu.3.8-Ezk", "hermon",
     "H1171,H1174,H1179,H2768,H2769,H7704,H7865,H8149,H8303"),
]

# (book, ch, vs) -> (decision, new, rule prefix)
EXPECT = {
    ("Gen", 25, 15): ("SWAP", "H2316", "R3"), ("1Ch", 1, 30): ("SWAP", "H2301", "R3"),
    ("1Ki", 15, 18): ("SWAP", "H1130", "R3"), ("Zep", 1, 1): ("LEAVE", "", "GUARD"),
    ("Act", 9, 1): ("REMOVE", "", "R1"), ("1Sa", 9, 2): ("REMOVE", "", "R1"),
    ("Est", 1, 1): ("LEAVE", "", "R2"), ("Gen", 33, 18): ("SWAP", "H7927", "R3"),
    ("1Ch", 26, 3): ("SWAP", "H3076", "R3"), ("Gen", 46, 13): ("SWAP", "H3102", "R3"),
    ("Psa", 87, 4): ("SWAP", "H7294", "R4"), ("Gen", 14, 13): ("HOLD", "", "R5"),
    ("1Ch", 26, 4): ("LEAVE", "", "R6"), ("Gen", 12, 6): ("HOLD", "", "R7"),
    ("Num", 26, 46): ("HOLD", "", "SAFETY"),
    ("Gen", 35, 5): ("SWAP", "H7927", "R0"), ("Mat", 4, 18): ("LEAVE", "", "R0"),
    ("1Ch", 5, 23): ("HOLD", "", "R0"),
}


def _make_db(path, rebuild_shape=False, drop_guard_kjv=False):
    import entity_resolution as er
    c = sqlite3.connect(path)
    c.executescript(_SCHEMA)
    wid = 0
    for (vid, book, ch, vs, pos, eng, head, sb, xh, xcls, uniq, kw, kh, fz) in _SLOTS:
        c.execute("INSERT INTO verses VALUES (?,?,?,?)", (vid, book, ch, vs))
        word_sb = xh if rebuild_shape else sb      # import_tipnr writes the H on the word
        c.execute("INSERT INTO words (verse_id, position, english, english_head, "
                  "strongs_base, strongs, is_pn) VALUES (?,?,?,?,?,'*',1)",
                  (vid, pos, eng, head, word_sb))
        # rebuild copy: live's xref rides along STALE ('H0' marks it) — must be ignored
        c.execute("INSERT INTO pn_hebrew_xref VALUES (?,?,?,?)",
                  (vid, pos, "H0" if rebuild_shape else xh, xcls))
        c.execute("INSERT INTO pn_greek_identity VALUES (?,?,NULL,'x','lemma-only',?)",
                  (vid, pos, fz or xh))
        c.execute("INSERT INTO pn_binding VALUES (?,?,?,?,?,'exact','',1,0,1)",
                  (er.book_num(book), ch, vs, er.norm_name(head), uniq))
        if kw and not (drop_guard_kjv and book == "Zep"):
            wid += 1
            c.execute("INSERT INTO kjv_words VALUES (?,?,?,?,0,?)",
                      (wid, er.book_num(book), ch, vs, kw))
            c.execute("INSERT INTO kjv_strongs VALUES (?,?)", (kh, wid))
    c.executemany("INSERT INTO tipnr_entities (uniq, head, section, bases) "
                  "VALUES (?,?,'person',?)", _ENTS)
    c.commit()
    c.close()


def _md5(p):
    with open(p, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _run(args):
    import correct_xref_vs_binding as k
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = k.main(["correct"] + args)
    return rc, buf.getvalue()


def _plan(outdir):
    with open(os.path.join(outdir, "correct_xref_vs_binding_plan.tsv"), encoding="utf-8") as f:
        lines = f.read().splitlines()
    return [dict(zip(lines[0].split("\t"), ln.split("\t"))) for ln in lines[1:]]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    import core
    fails = []

    def check(desc, got, want):
        if got != want:
            fails.append(f"  FAIL: {desc}\n        got {got!r}, want {want!r}")
        else:
            print(f"  ok: {desc}")

    def h_count(dbp, sid):
        c = sqlite3.connect(dbp)
        pred, params = core.h_abp_predicate(c, sid)
        n = c.execute(f"SELECT count(*) FROM words w WHERE {pred}", params).fetchone()[0]
        c.close()
        return n

    tmp = tempfile.mkdtemp()
    dbp = os.path.join(tmp, "a.db")
    _make_db(dbp)
    before_md5 = _md5(dbp)

    # ---- dry run ----
    rc, out = _run([dbp, "--out", tmp])
    check("dry run: control holds -> exit 0", rc, 0)
    check("dry run says nothing written", "DRY RUN: nothing written." in out, True)
    check("database unchanged by the dry run", _md5(dbp), before_md5)
    plan = _plan(tmp)
    got = {(r["book"], int(r["chapter"]), int(r["verse"])):
           (r["decision"], r["new_h"], r["rule"].split(" ")[0].rstrip(":")) for r in plan}
    check("GUARD fires on the Cushi-shaped row (Zep 1:1 left alone)",
          got.get(("Zep", 1, 1)), ("LEAVE", "", "GUARD"))
    for key, want in EXPECT.items():
        check(f"{key[0]} {key[1]}:{key[2]} -> {want[0]} {want[1]} by {want[2]}", got.get(key), want)
    check("agreeing slot (1Ki 11:14) not in the plan", ("1Ki", 11, 14) in got, False)
    check("plan has exactly the expected rows", sorted(got), sorted(EXPECT))
    check("predicted Hadad count shown 4 → 1", "H1908         4 → 1" in out, True)

    # ---- apply on a copy ----
    dbc = os.path.join(tmp, "apply.db")
    shutil.copy(dbp, dbc)
    h_before = h_count(dbc, "H1908")
    rc, out = _run([dbc, "--apply", "--out", tmp])
    check("apply -> exit 0", rc, 0)
    check("apply reports one transaction", "changes in one transaction." in out, True)
    check("no count differs from the plan", "DIFFERS FROM PLAN" in out, False)
    c = sqlite3.connect(dbc)
    q = lambda sql, *a: c.execute(sql, a).fetchone()
    check("Gen 25:15 xref -> H2316", q("SELECT hebrew_base FROM pn_hebrew_xref WHERE verse_id=1")[0], "H2316")
    check("Gen 25:15 frozen copy -> H2316",
          q("SELECT hebrew_base FROM pn_greek_identity WHERE verse_id=1")[0], "H2316")
    check("Gen 25:15 word untouched ('*')", q("SELECT strongs_base FROM words WHERE verse_id=1")[0], "*")
    check("1Ch 1:30 -> H2301", q("SELECT hebrew_base FROM pn_hebrew_xref WHERE verse_id=2")[0], "H2301")
    check("Shechem kept-Hebrew WORD swapped too",
          q("SELECT strongs_base FROM words WHERE verse_id=9")[0], "H7927")
    check("REMOVE keeps the xref row, number emptied, class kept",
          q("SELECT hebrew_base, class FROM pn_hebrew_xref WHERE verse_id=6"), (None, "tipnr"))
    check("REMOVE empties the frozen copy",
          q("SELECT hebrew_base FROM pn_greek_identity WHERE verse_id=6")[0], None)
    check("REMOVE on a kept-Hebrew word sets the word to '*'",
          q("SELECT strongs_base FROM words WHERE verse_id=7")[0], "*")
    check("GUARD row untouched", q("SELECT hebrew_base FROM pn_hebrew_xref WHERE verse_id=5")[0], "H3570")
    check("Esther untouched", q("SELECT hebrew_base FROM pn_hebrew_xref WHERE verse_id=8")[0], "H783")
    check("SAFETY-held row untouched",
          q("SELECT hebrew_base FROM pn_hebrew_xref WHERE verse_id=16")[0], "H8283")
    c.close()
    check("Hadad H1908 loses the two Ishmael slots + the Ben-hadad slot (4 -> 1)",
          (h_before, h_count(dbc, "H1908")), (4, 1))
    check("H2316 gains Gen 25:15", h_count(dbc, "H2316"), 1)
    rc, out = _run([dbc, "--out", tmp])
    left = [r for r in _plan(tmp) if r["decision"] in ("SWAP", "REMOVE")]
    check("second run: nothing left to change", left, [])

    # ---- a stale plan row -> whole apply rolled back ----
    import correct_xref_vs_binding as k
    import audit_xref_vs_binding as audit
    import entity_resolution as er
    dbr = os.path.join(tmp, "rollback.db")
    shutil.copy(dbp, dbr)
    md5r = _md5(dbr)
    conn = sqlite3.connect(dbr, isolation_level=None)
    conn.execute("PRAGMA journal_mode=DELETE")
    with open(audit.TIPNR_PINNED, encoding="utf-8-sig") as f:
        tip = audit.Tipnr(er.parse_tipnr(f.read().splitlines()), {}, {})
    _b, plan_rows, _s = k.build_plan(conn, tip)
    victim = [r for r in plan_rows if r["decision"] == "SWAP"][-1]
    victim["stored_h"] = "H1"          # no longer matches the db
    n, err = k.apply_plan(conn, plan_rows, False)
    conn.close()
    check("stale row -> apply refused", (n, bool(err)), (0, True))
    check("rolled back: database byte-identical", _md5(dbr), md5r)

    # ---- broken control -> VOID ----
    dbv = os.path.join(tmp, "void.db")
    _make_db(dbv, drop_guard_kjv=True)
    rc, out = _run([dbv, "--out", tmp])
    check("guard control broken -> exit 2", rc, 2)
    check("PLAN VOID printed", "PLAN VOID" in out, True)
    rc, out = _run([dbv, "--apply", "--out", tmp])
    check("VOID plan never applies", (rc, "APPLIED" in out), (2, False))

    # ---- rebuild-step: words only ----
    dbw = os.path.join(tmp, "rebuild.db")
    _make_db(dbw, rebuild_shape=True)
    rc, out = _run([dbw, "--rebuild-step", "--apply", "--out", tmp])
    check("rebuild-step apply -> exit 0", rc, 0)
    c = sqlite3.connect(dbw)
    check("rebuild-step: Gen 25:15 WORD -> H2316",
          c.execute("SELECT strongs_base FROM words WHERE verse_id=1").fetchone()[0], "H2316")
    check("rebuild-step: guard word untouched",
          c.execute("SELECT strongs_base FROM words WHERE verse_id=5").fetchone()[0], "H3570")
    check("rebuild-step: REMOVE word -> '*'",
          c.execute("SELECT strongs_base FROM words WHERE verse_id=6").fetchone()[0], "*")
    check("rebuild-step: stale xref ignored and untouched (all still 'H0')",
          c.execute("SELECT count(*) FROM pn_hebrew_xref WHERE hebrew_base <> 'H0'").fetchone()[0], 0)
    check("rebuild-step: frozen copy untouched",
          c.execute("SELECT hebrew_base FROM pn_greek_identity WHERE verse_id=1").fetchone()[0], "H1908")
    c.close()

    if fails:
        print("\n".join(fails))
        print(f"\n{len(fails)} FAILURE(S)")
        return 1
    print("\nAll correct_xref_vs_binding checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
