#!/usr/bin/env python3
"""
apply_abp_surface_fill.py — APPLY the approved abp_surface fill (lane 1). WRITES bible.db.
Record: docs/handoffs/CENSUS_abp_surface_fill.md (dry run APPROVED by JP 2026-10-25:
4,411 writes, ἡ->ή for the fill, no lemma write, 3,823 fill total).

One run, stops at the FIRST failure; nothing is written before step 3, and step 3 commits only
if every check passes (otherwise the database is left exactly as it was):
  0  preflight: journal mode must be DELETE (never WAL on PA) · abp_surface = 391,130 (not yet
     applied) · disk quota has room for one more copy
  1  rollback copy  ~/bible.db.pre-surface-fill-20261025  via SQLite's own copy (backup API —
     never a plain cp of a live db: a write mid-copy tears it) · size = source · integrity_check ok.
     An existing copy is reused only if it verifies AND its abp_surface equals live's.
  2  re-run the dry run against live: report must equal the approved one (output-path line aside)
     and the CSV must be byte-identical. 2b: every CURRENT row's translit already equals what
     build_abp_translit.py would write (so step 4 can change nothing outside the fill).
  3  ONE transaction (write lock held): live abp_surface == the copy's · 538 updates (old form must
     match) + 3,873 inserts (slot must be empty), translit computed by build_abp_translit.romanize
     in the same write · checks before COMMIT: 395,003 rows · the 4,411 rows = the CSV, byte for
     byte · every other row = the copy · G1–G6 re-checked on the written rows · C1/C2/C3 read back.
  4  run scripts/build_abp_translit.py · assert it changed NOTHING and no written row lacks translit.
  5  summary (the approved dry-run block + what happened) + the rollback command.

ROLLBACK (puts abp_surface back exactly as in the copy; touches no other table):
  PYTHONIOENCODING=utf-8 python3 scripts/apply_abp_surface_fill.py ~/bible-db/bible.db --rollback

Run on PA from ~/bible-db:
  PYTHONIOENCODING=utf-8 python3 scripts/apply_abp_surface_fill.py ~/bible-db/bible.db 2>&1 | tee ~/abp_surface_fill_apply.txt
"""
import argparse
import csv
import os
import sqlite3
import subprocess
import sys
import unicodedata
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from backup_db import _online_backup                      # the one safe-copy routine
from build_abp_translit import romanize                   # the one romanizer
from census_abp_surface_glued import NB, Lexicon, agree   # the one matching rule set
from dryrun_abp_surface_fill import app_to_ours, style_problems

REPO = os.path.join(HERE, os.pardir)
HOME = os.path.expanduser("~")
COPY = os.path.join(HOME, "bible.db.pre-surface-fill-20261025")
DISK_ROOT = HOME
ROWS_BEFORE, ROWS_AFTER = 391130, 395003
N_INSERT, N_UPDATE = 3873, 538
CONTROLS = ((("1Sa", 17, 57, 22), "χειρί αυτού"), (("Gen", 4, 8, 1), "είπε"), (("Gen", 5, 32, 1), "ην"))
LEXICON_CLASSES = {"fill_resolved": ("full", "pron"), "fill_pronoun": ("full", "pron"),
                   "split_receive": ("full", "pron"), "split_receive_name": ("name",),
                   "split_keep": ("full", "pron", "name"), "split_trim": ("full", "pron", "name")}


class Stop(Exception):
    pass


def say(msg=""):
    print(msg, flush=True)


def check(ok, msg):
    say(f"   {'PASS' if ok else 'FAIL'}  {msg}")
    if not ok:
        raise Stop(msg)


def rollback_cmd(db):
    extra = "" if COPY == os.path.join(HOME, "bible.db.pre-surface-fill-20261025") else f" --copy {COPY}"
    return f"PYTHONIOENCODING=utf-8 python3 scripts/apply_abp_surface_fill.py {db} --rollback{extra}"


def surface_rows(con, schema="main"):
    return {(v, p): (f, t) for v, p, f, t in con.execute(
        f"SELECT verse_id, position, form, translit FROM {schema}.abp_surface")}


def counts(con, schema):
    return {t: con.execute(f"SELECT count(*) FROM {schema}.{t}").fetchone()[0]
            for t in ("verses", "words", "pn_greek_identity", "abp_surface")}


def master(con, schema):
    return sorted(con.execute(f"SELECT type, name, sql FROM {schema}.sqlite_master").fetchall(),
                  key=lambda r: (r[0] or "", r[1] or ""))


def lemma_for(con, keys):
    """The lemma build_abp_translit.py romanizes with (lexicon by strongs_base)."""
    out = {}
    for v, p in keys:
        r = con.execute("SELECT COALESCE(l.lemma,'') FROM words w LEFT JOIN lexicon l "
                        "ON l.strongs_g = w.strongs_base WHERE w.verse_id=? AND w.position=?",
                        (v, p)).fetchone()
        out[(v, p)] = r[0] if r else None
    return out


# ── step 0 + 1 ───────────────────────────────────────────────────────────────
def preflight(db):
    say("0  PREFLIGHT")
    ro = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    jm = ro.execute("PRAGMA journal_mode").fetchone()[0].lower()
    check(jm == "delete", f"journal mode is {jm!r} (must be 'delete'; never WAL on PA)")
    n = ro.execute("SELECT count(*) FROM abp_surface").fetchone()[0]
    check(n == ROWS_BEFORE, f"abp_surface = {n} rows (expect {ROWS_BEFORE} = not yet applied)")
    ro.close()
    size = os.path.getsize(db)
    quota = float(os.environ.get("DISK_QUOTA_GB", 10)) * 1024 ** 3     # same quota as health_check
    used = int(subprocess.check_output(["du", "-sb", DISK_ROOT], stderr=subprocess.DEVNULL).split()[0])
    need = 0 if os.path.exists(COPY) else size
    pct = (used + need) / quota * 100
    check(pct < 95, f"disk: {used / 1024**3:.2f} GB used + {need / 1024**3:.2f} GB copy = "
                    f"{pct:.0f}% of {quota / 1024**3:.0f} GB quota (must stay < 95%)")


def make_copy(db):
    say("1  ROLLBACK COPY  " + COPY)
    if os.path.exists(COPY):
        say("   a copy already exists — verifying it is a PRE-fill copy before reusing it")
    else:
        _online_backup(Path(db), Path(COPY))
    c = sqlite3.connect(f"file:{COPY}?mode=ro", uri=True)
    ic = c.execute("PRAGMA integrity_check").fetchall()
    check(ic == [("ok",)], f"integrity_check on the copy: {ic[:3]}")
    n = c.execute("SELECT count(*) FROM abp_surface").fetchone()[0]
    check(n == ROWS_BEFORE, f"copy abp_surface = {n} (expect {ROWS_BEFORE})")
    c.close()
    a, b = os.path.getsize(db), os.path.getsize(COPY)
    check(a == b, f"copy size {b} = live size {a} bytes")
    live = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    live.execute(f"ATTACH DATABASE 'file:{COPY}?mode=ro' AS cp")
    diff = live.execute("SELECT (SELECT count(*) FROM (SELECT * FROM main.abp_surface EXCEPT "
                        "SELECT * FROM cp.abp_surface)) + (SELECT count(*) FROM (SELECT * FROM "
                        "cp.abp_surface EXCEPT SELECT * FROM main.abp_surface))").fetchone()[0]
    live.close()
    check(diff == 0, f"copy's abp_surface = live's ({diff} rows differ)")


# ── step 2 ───────────────────────────────────────────────────────────────────
def rerun_dry_run(db, a):
    say("2  DRY RUN RE-RUN against live (must equal the approved run)")
    tmp_csv = os.path.join(os.path.dirname(os.path.abspath(a.approved_csv)), "abp_surface_fill_dryrun.rerun.csv")
    p = subprocess.run([sys.executable, os.path.join(HERE, "dryrun_abp_surface_fill.py"), db,
                        "--lexicon", a.lexicon, "--missing", a.missing,
                        "--dump", a.dump, "--out", tmp_csv], capture_output=True, text=True,
                       encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    check(p.returncode == 0, f"dry run exit {p.returncode} (0 = ALL PASS)"
                             + ("" if p.returncode == 0 else "\n" + p.stdout[-3000:] + p.stderr[-2000:]))
    approved = open(a.approved_txt, encoding="utf-8").read()
    norm = lambda s, path: s.replace(path, "<OUT>")
    same_txt = norm(p.stdout, tmp_csv) == norm(approved, a.approved_csv)
    if not same_txt:
        import difflib
        for line in list(difflib.unified_diff(norm(approved, a.approved_csv).splitlines(),
                                              norm(p.stdout, tmp_csv).splitlines(), lineterm=""))[:40]:
            say("      " + line)
    check(same_txt, "report identical to the approved run (output-path line aside)")
    same_csv = open(tmp_csv, "rb").read() == open(a.approved_csv, "rb").read()
    check(same_csv, "CSV byte-identical to the approved CSV")
    os.remove(tmp_csv)
    return approved


def translit_stale_outside(db):
    say("2b TRANSLIT preflight: current rows already match build_abp_translit.py")
    ro = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    bad = []
    for v, p, f, t, lem in ro.execute(
            "SELECT s.verse_id, s.position, s.form, s.translit, COALESCE(l.lemma,'') FROM abp_surface s "
            "JOIN words w ON w.verse_id=s.verse_id AND w.position=s.position "
            "LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base WHERE s.form IS NOT NULL AND s.form <> ''"):
        if romanize(f, lem) != (t or ""):
            bad.append((v, p, f, t))
    ro.close()
    for b in bad[:8]:
        say(f"      would change: verse_id {b[0]} pos {b[1]} {b[2]!r} stored {b[3]!r}")
    check(not bad, f"{len(bad)} current row(s) would get a different translit from the builder "
                   "(must be 0, or step 4 would rewrite rows outside the fill)")


# ── step 3 ───────────────────────────────────────────────────────────────────
def load_writes(con, path):
    vkey = {(b, str(c), str(v)): i for i, b, c, v in con.execute("SELECT id, book, chapter, verse FROM verses")}
    writes, holds = [], []
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            vid = vkey.get((r["book"], r["chapter"], r["verse"]))
            r["key"] = (vid, int(r["position"]))
            r["old_form"] = r["old_form"].replace("␣", NB)      # the CSV marks NBSP as ␣
            if r["action"] in ("insert", "update"):
                if vid is None:
                    raise Stop(f"verse not found live: {r['book']} {r['chapter']}:{r['verse']}")
                writes.append(r)
            elif r["action"] == "hold" and vid is not None:
                holds.append(r)
    return writes, holds


def apply(db, a):
    say("3  APPLY — one transaction")
    lex = Lexicon(a.lexicon)
    con = sqlite3.connect(f"file:{db}", uri=True, isolation_level=None)
    con.execute("PRAGMA busy_timeout=60000")
    jm = con.execute("PRAGMA journal_mode").fetchone()[0].lower()
    check(jm == "delete", f"journal mode {jm!r} on the writing connection")
    con.execute(f"ATTACH DATABASE 'file:{COPY}?mode=ro' AS cp")
    writes, holds = load_writes(con, a.approved_csv)
    keys = [w["key"] for w in writes]
    check(len(writes) == N_INSERT + N_UPDATE and len(set(keys)) == len(keys),
          f"write list: {len(writes)} rows, {len(set(keys))} distinct slots (expect {N_INSERT + N_UPDATE})")
    ins = [w for w in writes if w["action"] == "insert"]
    upd = [w for w in writes if w["action"] == "update"]
    check(len(ins) == N_INSERT and len(upd) == N_UPDATE, f"insert {len(ins)} / update {len(upd)}")
    missing_app = {}
    with open(a.missing, encoding="utf-8", newline="") as f:
        vkey = {(b, str(c), str(v)): i for i, b, c, v in con.execute("SELECT id, book, chapter, verse FROM verses")}
        for m in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            missing_app[(vkey.get((m["book"], m["chapter"], m["verse"])), int(m["position"]))] = m["app_printed_form"]

    con.execute("BEGIN IMMEDIATE")
    try:
        before = surface_rows(con)
        copy_rows = surface_rows(con, "cp")
        check(before == copy_rows, f"live abp_surface unchanged since the copy ({len(before)} rows)")
        lem = lemma_for(con, keys)
        tl = {}
        for w in writes:
            k = w["key"]
            if lem[k] is None:
                raise Stop(f"no word row for {w['book']} {w['chapter']}:{w['verse']} pos {w['position']}")
            tl[k] = romanize(w["new_form"], lem[k])
        for w in upd:
            v, p = w["key"]
            cur = con.execute("UPDATE abp_surface SET form=?, translit=? WHERE verse_id=? AND position=? "
                              "AND form=?", (w["new_form"], tl[w["key"]], v, p, w["old_form"]))
            if cur.rowcount != 1:
                raise Stop(f"update {w['book']} {w['chapter']}:{w['verse']} pos {p}: old form not as approved")
        for w in ins:
            v, p = w["key"]
            con.execute("INSERT INTO abp_surface (verse_id, position, form, translit) VALUES (?,?,?,?)",
                        (v, p, w["new_form"], tl[w["key"]]))        # a filled slot raises: no overwrite

        say("   post-write checks (before COMMIT):")
        n = con.execute("SELECT count(*) FROM abp_surface").fetchone()[0]
        check(n == ROWS_AFTER, f"abp_surface = {n} rows (expect {ROWS_AFTER})")
        after = surface_rows(con)
        wk = set(keys)
        bad = [w for w in writes if after.get(w["key"]) != (w["new_form"], tl[w["key"]])]
        check(not bad, f"the {len(writes)} written rows = the approved CSV, byte for byte ({len(bad)} differ)")
        other = [k for k in set(after) | set(copy_rows) if k not in wk and after.get(k) != copy_rows.get(k)]
        check(not other, f"every other row = the copy ({len(other)} differ)")
        check(set(after) - set(copy_rows) == {w["key"] for w in ins}, "new rows = exactly the insert list")
        # G1 number + form (live number) on every Lexicon-backed write
        g1 = []
        for w in writes:
            want = LEXICON_CLASSES.get(w["cls"])
            if want:
                s = con.execute("SELECT strongs FROM words WHERE verse_id=? AND position=?", w["key"]).fetchone()[0]
                if agree(lex, s, w["new_form"]) not in want:
                    g1.append(w)
        check(not g1, f"G1 number + form on {sum(1 for w in writes if w['cls'] in LEXICON_CLASSES)} "
                      f"Lexicon-backed writes ({len(g1)} fail)")
        # G2 D rows: a split receiver that is also on the A list = the app's form, byte for byte
        d = [w for w in writes if w["cls"].startswith("split_receive") and w["key"] in missing_app]
        d_bad = [w for w in d if app_to_ours(missing_app[w["key"]]) != w["new_form"]]
        check(len(d) == 44 and not d_bad, f"G2 {len(d)} written D rows (expect 44), {len(d_bad)} disagree")
        # G3 / G4
        check(len(wk) == len(writes), "G3 no slot written twice")
        held_hit = [h for h in holds if h["key"] in wk or after.get(h["key"]) != copy_rows.get(h["key"])]
        check(not held_hit, f"G4 {len(holds)} held rows untouched ({len(held_hit)} touched)")
        # G5 other tables + structure unchanged
        c_live, c_copy = counts(con, "main"), counts(con, "cp")
        c_copy["abp_surface"] = ROWS_AFTER
        check(c_live == c_copy, f"G5 verses/words/pn_greek_identity unchanged: {c_live}")
        check(master(con, "main") == master(con, "cp"), "G5 no table/index added or changed")
        # G6 letter style
        g6 = [w for w in writes if NB in w["new_form"] or "ἡ" in w["new_form"]
              or style_problems(w["new_form"]) or not w["new_form"]]
        check(not g6, f"G6 written forms: no NBSP, no ἡ, monotonic Greek ({len(g6)} fail)")
        for (b, c, v, p), want in CONTROLS:
            got = con.execute("SELECT s.form FROM abp_surface s JOIN verses x ON x.id=s.verse_id "
                              "WHERE x.book=? AND x.chapter=? AND x.verse=? AND s.position=?",
                              (b, c, v, p)).fetchone()
            check(got and got[0] == want, f"control {b} {c}:{v} pos {p} reads {got[0] if got else None!r} "
                                          f"(expect {want!r})")
        con.execute("COMMIT")
        say("   COMMITTED")
    except BaseException:
        if con.in_transaction:
            con.execute("ROLLBACK")
            say("   ROLLED BACK — the database is exactly as it was before this step")
        raise
    finally:
        con.close()
    q = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    qc = q.execute("PRAGMA quick_check").fetchall()
    q.close()
    check(qc == [("ok",)], f"quick_check on live after commit: {qc[:3]}")
    return writes


# ── step 4 ───────────────────────────────────────────────────────────────────
def translit_step(db, writes):
    say("4  build_abp_translit.py")
    ro = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    snap = surface_rows(ro)
    ro.close()
    p = subprocess.run([sys.executable, os.path.join(HERE, "build_abp_translit.py"), db],
                       capture_output=True, text=True, encoding="utf-8",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    say("   " + (p.stdout.strip() or p.stderr.strip()[-500:]))
    check(p.returncode == 0, f"build_abp_translit.py exit {p.returncode}")
    ro = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    after = surface_rows(ro)
    ro.close()
    changed = [k for k in after if after[k] != snap.get(k)]
    check(not changed, f"the builder changed {len(changed)} row(s) (expect 0 — translit was written with the fill)")
    empty = [w for w in writes if not (after.get(w["key"]) or ("", ""))[1]]
    check(not empty, f"no written row without translit ({len(empty)} empty)")


def do_rollback(db):
    say(f"ROLLBACK: restore abp_surface from {COPY}")
    c = sqlite3.connect(f"file:{COPY}?mode=ro", uri=True)
    qc = c.execute("PRAGMA quick_check").fetchall()
    n = c.execute("SELECT count(*) FROM abp_surface").fetchone()[0]
    c.close()
    check(qc == [("ok",)] and n == ROWS_BEFORE, f"copy quick_check {qc[:1]} · copy abp_surface {n}")
    con = sqlite3.connect(f"file:{db}", uri=True, isolation_level=None)
    con.execute("PRAGMA busy_timeout=60000")
    jm = con.execute("PRAGMA journal_mode").fetchone()[0].lower()
    check(jm == "delete", f"journal mode {jm!r}")
    con.execute(f"ATTACH DATABASE 'file:{COPY}?mode=ro' AS cp")
    con.execute("BEGIN IMMEDIATE")
    try:
        say(f"   live abp_surface now {con.execute('SELECT count(*) FROM abp_surface').fetchone()[0]} rows")
        con.execute("DELETE FROM main.abp_surface")
        con.execute("INSERT INTO main.abp_surface (verse_id, position, form, translit) "
                    "SELECT verse_id, position, form, translit FROM cp.abp_surface")
        n = con.execute("SELECT count(*) FROM main.abp_surface").fetchone()[0]
        diff = con.execute("SELECT (SELECT count(*) FROM (SELECT * FROM main.abp_surface EXCEPT "
                           "SELECT * FROM cp.abp_surface)) + (SELECT count(*) FROM (SELECT * FROM "
                           "cp.abp_surface EXCEPT SELECT * FROM main.abp_surface))").fetchone()[0]
        check(n == ROWS_BEFORE and diff == 0, f"restored {n} rows, {diff} differ from the copy")
        con.execute("COMMIT")
        say("   COMMITTED — abp_surface is back to the pre-fill copy")
    except BaseException:
        if con.in_transaction:
            con.execute("ROLLBACK")
            say("   ROLLED BACK — nothing changed")
        raise
    finally:
        con.close()


def main():
    global COPY, DISK_ROOT
    ap = argparse.ArgumentParser(description="APPLY the approved abp_surface fill (writes bible.db).")
    ap.add_argument("db")
    ap.add_argument("--rollback", action="store_true", help="restore abp_surface from the pre-fill copy")
    ap.add_argument("--dump", default=os.path.join(HOME, "abp_app_dump.tsv"))
    ap.add_argument("--approved-txt", default=os.path.join(HOME, "abp_surface_fill_dryrun.txt"))
    ap.add_argument("--approved-csv", default=os.path.join(HOME, "abp_surface_fill_dryrun.csv"))
    ap.add_argument("--lexicon", default=os.path.join(REPO, "abp_helps", "analytical_lexicon.tsv"))
    ap.add_argument("--missing", default=os.path.join(REPO, "abp_app_html", "missing_printed_forms.tsv"))
    ap.add_argument("--copy", default=COPY, help="rollback copy path (default %(default)s)")
    ap.add_argument("--disk-root", default=HOME, help="folder measured against the quota")
    a = ap.parse_args()
    COPY, DISK_ROOT = os.path.abspath(os.path.expanduser(a.copy)), a.disk_root
    db = os.path.abspath(os.path.expanduser(a.db))
    say("=" * 78)
    say(("abp_surface FILL — ROLLBACK" if a.rollback else "abp_surface FILL — APPLY") + f"  ({db})")
    say("=" * 78)
    try:
        if a.rollback:
            do_rollback(db)
            return 0
        for p in (a.dump, a.approved_txt, a.approved_csv, a.lexicon, a.missing):
            check(os.path.exists(p), f"input present: {p}")
        preflight(db)
        make_copy(db)
        approved = rerun_dry_run(db, a)
        translit_stale_outside(db)
        writes = apply(db, a)
        translit_step(db, writes)
    except Stop as e:
        say(f"\nSTOPPED: {str(e).splitlines()[0]}")
        say(f"Rollback copy: {COPY if os.path.exists(COPY) else '(none made)'}")
        say(f"If anything was committed, roll back with:\n  {rollback_cmd(a.db)}")
        return 1
    say("\n5  SUMMARY — the approved dry-run block, now applied")
    start = approved.find("COUNTS (expected | actual)")
    end = approved.find("wrote ")
    say(approved[start:end].rstrip())
    say(f"\nAPPLIED: {N_INSERT + N_UPDATE} writes ({N_INSERT} insert · {N_UPDATE} update) · abp_surface "
        f"{ROWS_BEFORE} -> {ROWS_AFTER} · translit written with the fill; builder changed 0 rows")
    say(f"Rollback copy: {COPY}  (keep until a nightly bible.db backup is stamped after this run)")
    say(f"Rollback command:\n  {rollback_cmd(a.db)}")
    say("~/bible.db.pre-xref-fix-20261024 was not touched.")
    say("\nRESULT: APPLIED, ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
