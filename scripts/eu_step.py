#!/usr/bin/env python3
"""eu_step.py - edition upgrade: the shared pre / prep / dry-delta / same / check steps every stage-D
one-off helper repeated (8B2A, 8B3, 8B3b, 8B3c, SLOT3). One committed script instead of a pasted,
sha-checked heredoc per block: the block's REF guard pins this file like any other script.

It never writes the db it checks. The step's own builder still runs from the block (bash); this
script only guards, saves the before-state, makes the THROWAWAY copy the dry run writes, reads out
the row-level differences, and proves the after-state.

  pre    --tag T --ref REF --dir DIR [--db PATH]... [--keep PATH]... [--repo DIR]
         repo guards (REF pulled, an ancestor of HEAD, scripts/ + tests/ = REF, no uncommitted
         changes there); each --db present, no -journal beside it, no triggers; each --keep
         (rollback copy) present and non-empty; DIR must not exist - made last.

  prep   --tag T --built PATH --dir DIR --copy T1,T2.. [--save TABLE[:col+col]]...
         read-only on built. Writes DIR/state.json (every table's row count + content digest,
         the whole schema), DIR/before.db (each --save table, or just rowid + the named
         columns: a restore source) and DIR/dry.db (the THROWAWAY copy: each --copy table with
         its indexes, row ids kept) - then proves each copied table = built's by digest.

  same   --tag T --built PATH --dir DIR
         built's schema + every table's digest = state.json (built untouched since prep).

  delta  --tag T --a PATH --b PATH --table TABLE[:key+key]... --out TSV [--show N]
         [--zero] [--expect-sha SHA]
         every row-level difference a -> b on the named tables, written IN FULL to TSV (no cap),
         printed by changed column + the first N. Default key = the row id. --zero: any
         difference fails. --expect-sha: the TSV must hash to SHA.

  check  --tag T --built PATH --dir DIR --written T1,T2..
         after the apply: tables NOT in --written = their prep digest; each --written table =
         the dry copy's (digest; on a mismatch the row-level differences are printed); schema =
         prep's outside the written tables, = the dry copy's for them; no -journal beside built;
         scripts/ + tests/ clean.

Every line that ends a mode reads "<TAG> <MODE>: OK" or "<TAG> <MODE>: STOP - why" (FAIL for
check). Exit 0 = OK / 1 = STOP or FAIL / 2 = bad arguments. The block owns the RESULT line.
"""
import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
M256 = 1 << 256


class Stop(Exception):
    pass


def text(b):
    return b.decode("utf-8", "surrogateescape")


def ro(path):
    if not (os.path.isfile(path) and os.path.getsize(path) > 0):
        raise Stop("missing or empty: %s" % path)
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=60)
    c.text_factory = text
    c.execute("PRAGMA query_only=1")
    return c


def q(name):
    return '"%s"' % name.replace('"', '""')


def schema(c):
    """Every schema entry except sqlite's own auto-indexes' NULL sql, sorted."""
    return sorted([list(r) for r in c.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_autoindex_%'")],
        key=repr)


def plain_tables(c):
    """Tables whose rows we digest: every ordinary table (a virtual table's rows live in its shadow
    tables, which are ordinary and digested)."""
    out, virt = [], []
    for name, sql in c.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"):
        (virt if (sql or "").upper().startswith("CREATE VIRTUAL") else out).append(name)
    return out, virt


def cols(c, t, db="main"):
    return [r[1] for r in c.execute("PRAGMA %s.table_info(%s)" % (db, q(t)))]


def rowid_alias(c, t, db="main"):
    """The INTEGER PRIMARY KEY column (the row id itself), or None."""
    pk = [r for r in c.execute("PRAGMA %s.table_info(%s)" % (db, q(t))) if r[5]]
    if len(pk) == 1 and (pk[0][2] or "").upper() == "INTEGER":
        return pk[0][1]
    return None


def digest(c, t):
    """Row count + an order-free content digest (sum of sha256 of each row's repr, mod 2^256)."""
    n, s = 0, 0
    for r in c.execute("SELECT * FROM %s" % q(t)):
        s += int.from_bytes(hashlib.sha256(repr(tuple(r)).encode("utf-8", "surrogateescape")).digest(), "big")
        n += 1
    return [n, "%064x" % (s % M256)]


def state_of(c):
    tabs, virt = plain_tables(c)
    return {"schema": schema(c), "tables": {t: digest(c, t) for t in tabs}, "virtual": virt}


def tag_line(tag, mode, msg):
    print("%s %s: %s" % (tag, mode, msg))


# ---------------------------------------------------------------- pre

def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo)] + list(args), capture_output=True, text=True)


def mode_pre(a):
    repo = Path(a.repo)
    if not git(repo, "rev-parse", "--verify", "--quiet", a.ref + "^{commit}").returncode == 0:
        raise Stop("PA has not pulled %s (unknown revision)" % a.ref)
    head = git(repo, "log", "-1", "--format=%h").stdout.strip()
    print("repo %s - HEAD %s - REF %s" % (repo, head, a.ref))
    if not git(repo, "merge-base", "--is-ancestor", a.ref, "HEAD").returncode == 0:
        raise Stop("%s is not an ancestor of HEAD %s" % (a.ref, head))
    if not git(repo, "diff", "--quiet", a.ref, "HEAD", "--", "scripts", "tests").returncode == 0:
        raise Stop("scripts/tests differ from %s" % a.ref)
    if git(repo, "status", "--porcelain", "--untracked-files=no", "--", "scripts", "tests").stdout.strip():
        raise Stop("uncommitted changes in scripts/tests")
    print("repo guards: %s pulled, an ancestor of HEAD, scripts/tests = %s, nothing uncommitted there" % (a.ref, a.ref))
    for p in a.db:
        if os.path.exists(p + "-journal"):
            raise Stop("%s-journal present (move it aside, never delete; bring it back)" % p)
        c = ro(p)
        nt = c.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]
        c.close()
        if nt:
            raise Stop("%s has %d trigger(s)" % (p, nt))
        print("db %s: %d bytes - no -journal - triggers 0" % (p, os.path.getsize(p)))
    for p in a.keep:
        if not (os.path.isfile(p) and os.path.getsize(p) > 0):
            raise Stop("rollback copy missing or empty: %s" % p)
        print("rollback copy %s: %d bytes, %s" % (p, os.path.getsize(p),
                                                  time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(os.path.getmtime(p)))))
    d = Path(a.dir)
    if d.exists():
        raise Stop("run folder already exists (already ran?): %s" % d)
    if not d.parent.is_dir():
        raise Stop("parent folder missing: %s" % d.parent)
    d.mkdir()
    print("run folder made: %s" % d)


# ---------------------------------------------------------------- prep

def parse_save(specs):
    out = []
    for s in specs:
        t, _, cs = s.partition(":")
        out.append((t, [x for x in cs.split("+") if x] if cs else None))
    return out


def mode_prep(a):
    d = Path(a.dir)
    if not d.is_dir():
        raise Stop("run folder missing (pre makes it): %s" % d)
    for f in ("state.json", "before.db", "dry.db"):
        if (d / f).exists():
            raise Stop("already exists: %s" % (d / f))
    c = ro(a.built)
    tabs, virt = plain_tables(c)
    copy = [t for t in a.copy.split(",") if t]
    save = parse_save(a.save)
    for t in copy + [t for t, _ in save]:
        if t not in tabs:
            raise Stop("built has no table %s" % t)
    for t, cs in save:
        miss = [x for x in (cs or []) if x not in cols(c, t)]
        if miss:
            raise Stop("table %s has no column(s) %s" % (t, miss))
    t0 = time.time()
    st = state_of(c)
    st["built"] = os.path.abspath(a.built)
    st["copy"] = copy
    with open(d / "state.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(st, f, indent=1, sort_keys=True)
    print("state.json: %d tables digested (%d rows) + %d schema entries in %.0f s - virtual tables skipped (their "
          "shadow tables are digested): %s" % (len(st["tables"]), sum(v[0] for v in st["tables"].values()),
                                              len(st["schema"]), time.time() - t0, ", ".join(virt) or "none"))
    sql = {n: s for n, s in c.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")}
    c.close()

    def fill(path, plan):
        w = sqlite3.connect("file:%s?mode=rwc" % path, uri=True)   # URI mode: the ATTACH below is read-only
        w.execute("PRAGMA journal_mode=DELETE")
        w.execute("ATTACH DATABASE ? AS b", ("file:%s?mode=ro" % a.built,))
        for t, cs in plan:
            if cs is None:
                w.execute(sql[t])
                alias = rowid_alias(w, t, "b")
                cl = ", ".join(q(x) for x in cols(w, t, "b"))
                if alias:
                    w.execute("INSERT INTO main.%s SELECT * FROM b.%s" % (q(t), q(t)))
                else:
                    w.execute("INSERT INTO main.%s (rowid, %s) SELECT rowid, %s FROM b.%s" % (q(t), cl, cl, q(t)))
                for (isql,) in w.execute("SELECT sql FROM b.sqlite_master WHERE type='index' AND tbl_name=? "
                                         "AND sql IS NOT NULL", (t,)).fetchall():
                    w.execute(isql)
            else:
                cl = ", ".join(q(x) for x in cs)
                w.execute("CREATE TABLE main.%s (_rowid INTEGER PRIMARY KEY, %s)" % (q(t), cl))
                w.execute("INSERT INTO main.%s SELECT rowid, %s FROM b.%s" % (q(t), cl, q(t)))
        w.commit()
        w.execute("DETACH DATABASE b")
        w.close()

    fill(d / "before.db", save)
    b = ro(str(d / "before.db"))
    for t, cs in save:
        n = b.execute("SELECT count(*) FROM %s" % q(t)).fetchone()[0]
        if not n == st["tables"][t][0]:
            raise Stop("before.db %s: %d rows, built has %d" % (t, n, st["tables"][t][0]))
        print("before.db %s (%s): %d rows" % (t, "whole table" if cs is None else "row id + " + ", ".join(cs), n))
    b.close()
    print("before.db: %d bytes (restore source)" % os.path.getsize(d / "before.db"))
    fill(d / "dry.db", [(t, None) for t in copy])
    w = ro(str(d / "dry.db"))
    for t in copy:
        got = digest(w, t)
        print("dry.db %s: %d rows, digest %s - = built's: %s" % (t, got[0], got[1][:12], "yes" if got == st["tables"][t] else "NO"))
        if not got == st["tables"][t]:
            raise Stop("dry copy of %s differs from built" % t)
    w.close()
    print("dry.db: %d bytes (THROWAWAY copy; the dry run writes only this file)" % os.path.getsize(d / "dry.db"))


# ---------------------------------------------------------------- same

def compare_state(c, st, skip=()):
    """Lines describing every table/schema difference vs st, ignoring tables in skip."""
    bad = []
    tabs, _virt = plain_tables(c)
    for t in sorted(set(tabs) | set(st["tables"])):
        if t in skip:
            continue
        if t not in st["tables"]:
            bad.append("table %s is new" % t)
        elif t not in tabs:
            bad.append("table %s is gone" % t)
        else:
            got = digest(c, t)
            if not got == st["tables"][t]:
                bad.append("table %s: %d rows, digest %s - prep had %d, %s"
                           % (t, got[0], got[1][:12], st["tables"][t][0], st["tables"][t][1][:12]))
    now = [e for e in schema(c) if e[2] not in skip]
    was = [e for e in st["schema"] if e[2] not in skip]
    for e in now:
        if e not in was:
            bad.append("schema entry added/changed: %s" % (e,))
    for e in was:
        if e not in now:
            bad.append("schema entry gone/changed: %s" % (e,))
    return bad


def load_state(d):
    p = Path(d) / "state.json"
    if not p.is_file():
        raise Stop("no state.json in %s (prep did not run)" % d)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def mode_same(a):
    st = load_state(a.dir)
    if not os.path.abspath(a.built) == st["built"]:
        raise Stop("state.json was made from %s, not %s" % (st["built"], a.built))
    c = ro(a.built)
    bad = compare_state(c, st)
    c.close()
    print("built vs prep: %d tables + the schema - differences %d (expect 0)" % (len(st["tables"]), len(bad)))
    for x in bad:
        print("  " + x)
    if bad:
        raise Stop("built changed since prep")


# ---------------------------------------------------------------- delta

def skey(v):
    """Python order = sqlite's BINARY order: NULL < numbers < text < blob."""
    if v is None:
        return (0, 0)
    if isinstance(v, (int, float)):
        return (1, v)
    if isinstance(v, str):
        return (2, v)
    return (3, bytes(v))


def table_delta(con, t, keyspec, out, show, shown):
    """Row-level differences a.t -> b.t, streamed. Writes TSV lines; returns (counts, by-class, n)."""
    ca, cb = cols(con, t, "a"), cols(con, t, "b")
    if not ca == cb:
        print("  %s: columns differ %s -> %s" % (t, ca, cb))
        out.write("%s\tCOLUMNS\t-\t-\t%r\t%r\n" % (t, ca, cb))
        return {"COLUMNS": 1}, {}, 1
    if keyspec:
        key = keyspec
        miss = [k for k in key if k not in ca]
        if miss:
            raise Stop("%s has no key column(s) %s" % (t, miss))
        sel = list(ca)
    else:
        alias = rowid_alias(con, t, "a")
        if alias and alias == rowid_alias(con, t, "b"):
            key, sel = [alias], list(ca)
        else:
            key, sel = ["_rowid"], ["_rowid"] + list(ca)
    kix = [sel.index(k) for k in key]
    # COLLATE BINARY everywhere: a column declared NOCASE must not hide a case-only change
    exprs = ", ".join("rowid AS _rowid" if x == "_rowid" else "%s COLLATE BINARY AS %s" % (q(x), q(x)) for x in sel)
    grp = ", ".join("rowid" if x == "_rowid" else "%s COLLATE BINARY" % q(x) for x in sel)
    order = ", ".join("%s COLLATE BINARY" % q(sel[i]) for i in kix)
    # keyed by the row id, every key is one row: no grouping needed; otherwise rows are counted
    # per distinct value so a duplicated row is a difference too
    by_id = not keyspec

    def side(x, y):
        if by_id:
            s = ("SELECT * FROM (SELECT %s, 1 AS _n FROM %s.%s EXCEPT SELECT %s, 1 AS _n FROM %s.%s) ORDER BY %s"
                 % (exprs, x, q(t), exprs, y, q(t), order))
        else:
            s = ("SELECT * FROM (SELECT %s, count(*) AS _n FROM %s.%s GROUP BY %s "
                 "EXCEPT SELECT %s, count(*) AS _n FROM %s.%s GROUP BY %s) ORDER BY %s"
                 % (exprs, x, q(t), grp, exprs, y, q(t), grp, order))
        cur = con.cursor()
        cur.execute(s)
        return cur

    def groups(cur):
        prev, rows = None, []
        for r in cur:
            k = tuple(skey(r[i]) for i in kix)
            if rows and not k == prev:
                yield prev, rows
                rows = []
            prev = k
            rows.append(tuple(r))
        if rows:
            yield prev, rows

    na = con.execute("SELECT count(*) FROM a.%s" % q(t)).fetchone()[0]
    nb = con.execute("SELECT count(*) FROM b.%s" % q(t)).fetchone()[0]
    counts = {"CHANGED": 0, "ADDED": 0, "REMOVED": 0}
    classes = {}
    ga, gb = groups(side("a", "b")), groups(side("b", "a"))
    xa, xb = next(ga, None), next(gb, None)
    names = sel + ["_n"]

    def emit(kind, rows_a, rows_b):
        k = tuple((rows_a or rows_b)[0][i] for i in kix)
        if kind == "CHANGED" and len(rows_a) == 1 and len(rows_b) == 1:
            ra, rb = rows_a[0], rows_b[0]
            ch = [i for i in range(len(names)) if not ra[i] == rb[i]]
            cn = ",".join(names[i] for i in ch)
            before = tuple(ra[i] for i in ch)
            after = tuple(rb[i] for i in ch)
            cls = "changed " + cn
            for i in ch:
                tr = ("%s: NULL -> value" if ra[i] is None else "%s: value -> NULL" if rb[i] is None
                      else "%s: value -> other value") % names[i]
                classes[tr] = classes.get(tr, 0) + 1
        else:
            cn = "-" if kind != "CHANGED" else "rows"
            before, after = tuple(rows_a), tuple(rows_b)
            cls = kind.lower() if kind != "CHANGED" else "changed: %d row(s) -> %d row(s)" % (len(rows_a), len(rows_b))
        classes[cls] = classes.get(cls, 0) + 1
        counts[kind] += 1
        out.write("%s\t%s\t%r\t%s\t%r\t%r\n" % (t, kind, k, cn, before, after))
        if shown[0] < show:
            shown[0] += 1
            sample.append("    %s %s %r [%s]: %r -> %r" % (t, kind, k, cn, before, after))

    sample = []

    while xa is not None or xb is not None:
        if xb is None or (xa is not None and xa[0] < xb[0]):
            emit("REMOVED", xa[1], [])
            xa = next(ga, None)
        elif xa is None or xb[0] < xa[0]:
            emit("ADDED", [], xb[1])
            xb = next(gb, None)
        else:
            emit("CHANGED", xa[1], xb[1])
            xa, xb = next(ga, None), next(gb, None)
    n = sum(counts.values())
    print("  %s (key %s): rows %d -> %d - changed %d, added %d, removed %d"
          % (t, "+".join(key), na, nb, counts["CHANGED"], counts["ADDED"], counts["REMOVED"]))
    for cl, m in sorted(classes.items(), key=lambda kv: (-kv[1], kv[0])):
        print("    by class: %s %d" % (cl, m))
    for line in sample:
        print(line)
    return counts, classes, n


def run_delta(a_path, b_path, specs, out_path, show):
    for p in (a_path, b_path):
        ro(p).close()
    con = sqlite3.connect("file::memory:", uri=True)   # URI mode: both ATTACHes are read-only
    con.text_factory = text
    con.execute("ATTACH DATABASE ? AS a", ("file:%s?mode=ro" % a_path,))
    con.execute("ATTACH DATABASE ? AS b", ("file:%s?mode=ro" % b_path,))
    total = 0
    shown = [0]
    with open(out_path, "w", encoding="utf-8", errors="surrogateescape", newline="\n") as out:
        out.write("table\tkind\tkey\tcolumns\tbefore\tafter\n")
        for s in specs:
            t, _, ks = s.partition(":")
            for x in ("a", "b"):
                if not con.execute("SELECT 1 FROM %s.sqlite_master WHERE type='table' AND name=?" % x, (t,)).fetchone():
                    raise Stop("%s has no table %s" % (a_path if x == "a" else b_path, t))
            _counts, _classes, n = table_delta(con, t, [k for k in ks.split("+") if k] if ks else None, out, show, shown)
            total += n
    con.close()
    sha = hashlib.sha256(Path(out_path).read_bytes()).hexdigest()
    return total, sha


def mode_delta(a):
    if os.path.exists(a.out):
        raise Stop("exists: %s" % a.out)
    print("delta %s -> %s (every difference written to %s; first %d printed):" % (a.a, a.b, a.out, a.show))
    total, sha = run_delta(a.a, a.b, a.table, a.out, a.show)
    print("differences: %d - %s: %d lines + header, sha256 %s" % (total, a.out, total, sha))
    if a.zero and total:
        raise Stop("%d difference(s), expected 0" % total)
    if a.expect_sha and not sha == a.expect_sha:
        raise Stop("delta file sha256 %s, expected %s" % (sha, a.expect_sha))


# ---------------------------------------------------------------- check

def mode_check(a):
    st = load_state(a.dir)
    if not os.path.abspath(a.built) == st["built"]:
        raise Stop("state.json was made from %s, not %s" % (st["built"], a.built))
    written = [t for t in a.written.split(",") if t]
    miss = [t for t in written if t not in st.get("copy", [])]
    if miss:
        raise Stop("written table(s) %s were not in the dry copy" % miss)
    dry = str(Path(a.dir) / "dry.db")
    c, w = ro(a.built), ro(dry)
    bad = []
    other = compare_state(c, st, skip=written)
    print("tables NOT written (%d) + their schema vs prep: differences %d (expect 0)"
          % (len(st["tables"]) - len(written), len(other)))
    for x in other:
        print("  " + x)
    bad += other
    ws_c = [e for e in schema(c) if e[2] in written]
    ws_w = [e for e in schema(w) if e[2] in written]
    same_schema = ws_c == ws_w
    print("written tables' schema (table + indexes) = the dry copy's: %s" % ("yes" if same_schema else "NO"))
    if not same_schema:
        for e in ws_c:
            if e not in ws_w:
                print("  built only: %s" % (e,))
        for e in ws_w:
            if e not in ws_c:
                print("  dry only: %s" % (e,))
        bad.append("written tables' schema differs from the dry copy")
    for t in written:
        gc, gw = digest(c, t), digest(w, t)
        print("written table %s: built %d rows, %s - dry copy %d rows, %s - = the dry run: %s - vs prep %d rows, %s"
              % (t, gc[0], gc[1][:12], gw[0], gw[1][:12], "yes" if gc == gw else "NO",
                 st["tables"][t][0], st["tables"][t][1][:12]))
        if not gc == gw:
            bad.append("%s on built differs from the dry run" % t)
            p = Path(a.dir) / ("check_delta_%s.tsv" % t)
            if not p.exists():
                print("  row-level, dry copy -> built (all in %s):" % p)
                run_delta(dry, a.built, [t], str(p), 40)
    c.close()
    w.close()
    j = "PRESENT" if os.path.exists(a.built + "-journal") else "none"
    print("journal beside built: %s (expect none)" % j)
    if j != "none":
        bad.append("-journal beside built")
    gs = git(Path(a.repo), "status", "--porcelain", "--untracked-files=no", "--", "scripts", "tests").stdout.strip()
    print("repo scripts/tests: %s (expect clean)" % ("clean" if not gs else "DIRTY:\n" + gs))
    if gs:
        bad.append("scripts/tests dirty")
    if bad:
        raise Stop("; ".join(bad))


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("pre")
    p.add_argument("--ref", required=True)
    p.add_argument("--dir", required=True)
    p.add_argument("--db", action="append", default=[])
    p.add_argument("--keep", action="append", default=[])
    p = sub.add_parser("prep")
    p.add_argument("--built", required=True)
    p.add_argument("--dir", required=True)
    p.add_argument("--copy", required=True)
    p.add_argument("--save", action="append", default=[])
    p = sub.add_parser("same")
    p.add_argument("--built", required=True)
    p.add_argument("--dir", required=True)
    p = sub.add_parser("delta")
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.add_argument("--table", action="append", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--show", type=int, default=40)
    p.add_argument("--zero", action="store_true")
    p.add_argument("--expect-sha")
    p = sub.add_parser("check")
    p.add_argument("--built", required=True)
    p.add_argument("--dir", required=True)
    p.add_argument("--written", required=True)
    for sp in sub.choices.values():
        sp.add_argument("--tag", required=True)
        sp.add_argument("--repo", default=str(REPO))
    a = ap.parse_args(argv)
    name = a.mode.upper()
    try:
        {"pre": mode_pre, "prep": mode_prep, "same": mode_same, "delta": mode_delta, "check": mode_check}[a.mode](a)
    except (Stop, sqlite3.Error, OSError) as e:
        kind = "FAIL" if a.mode == "check" else "STOP"
        tag_line(a.tag, name, "%s - %s%s" % (kind, "" if isinstance(e, Stop) else type(e).__name__ + ": ", e))
        return 1
    tag_line(a.tag, name, "OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
