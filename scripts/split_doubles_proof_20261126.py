#!/usr/bin/env python3
"""The split double rows copy proof, part 1 (DESIGN 9.281 (3), 9.282): two small tools the proof block
calls on a WHOLE-FILE COPY of live. Neither ever writes the database it reads.

  save  <db> <out.db>
        Copy <db>'s abp_surface table, row for row, into a NEW file <out.db> holding only that table (the shape
        of the standing pre-fill table ~/abp_surface_prefill_20261115.db: verse_id, position, form, translit,
        keyed on (verse_id, position)). <db> is opened read-only; <out.db> must not exist. Prints the row count
        and a digest of the rows for both sides; they must be equal or it stops.

  compare <new.db> <old.db> --verses <db> --out <list.tsv>
        Compare two abp_surface tables by (verse_id, position): same / only in new / only in old / form or
        spelling differs, counted INSIDE the 485 verses the split double rows plan touches and OUTSIDE them.
        Verse ids and each differing slot's word come from --verses (the copy). Writes every slot that is not
        the same to --out (TSV). All three databases are opened read-only; --out must not exist.

Refuses live (~/bible-db/bible.db) and any file named bible.db, for every database argument.

  python3 scripts/split_doubles_proof_20261126.py save ~/run/proof.db ~/run/builder.db
  python3 scripts/split_doubles_proof_20261126.py compare ~/run/builder.db ~/abp_surface_prefill_20261115.db \\
      --verses ~/run/proof.db --out ~/run/builder_vs_prefill.tsv
"""
import argparse
import hashlib
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_bible_text_batch_20261122 as B           # noqa: E402  LIVE
import apply_split_doubles_20261126 as A              # noqa: E402  the plan

COLS = "verse_id, position, form, translit"


class Stop(Exception):
    pass


def _not_live(p):
    p = Path(p).expanduser()
    if p.name == "bible.db" or (B.LIVE.exists() and p.exists() and p.resolve() == B.LIVE.resolve()):
        raise Stop(f"{p} is live or named bible.db; this tool runs on copies only")
    return p


def _ro(p):
    p = _not_live(p)
    if not p.is_file():
        raise Stop(f"no database at {p}")
    return sqlite3.connect(f"file:{p}?mode=ro", uri=True)


def _rows(conn):
    return conn.execute(f"SELECT {COLS} FROM abp_surface ORDER BY verse_id, position").fetchall()


def _digest(rows):
    h = hashlib.sha256()
    for r in rows:
        h.update(repr(r).encode("utf-8"))
    return h.hexdigest()


def save(src, out):
    out = _not_live(out)
    if out.exists():
        raise Stop(f"{out} already exists")
    s = _ro(src)
    rows = _rows(s)
    s.close()
    d = sqlite3.connect(out)
    d.execute("PRAGMA journal_mode=DELETE")
    d.execute("CREATE TABLE abp_surface (verse_id INTEGER, position INTEGER, form TEXT, translit TEXT, "
              "PRIMARY KEY (verse_id, position))")
    d.executemany("INSERT INTO abp_surface VALUES (?,?,?,?)", rows)
    d.commit()
    d.close()
    c = _ro(out)
    back = _rows(c)
    c.close()
    a, b = _digest(rows), _digest(back)
    print(f"saved abp_surface: {len(rows):,} rows, digest {a[:16]}; read back {len(back):,} rows, digest {b[:16]}")
    if (len(rows), a) != (len(back), b):
        raise Stop("the saved table does not read back the same")


def compare(new, old, verses, out):
    out = _not_live(out)
    if out.exists():
        raise Stop(f"{out} already exists")
    plan = A.load_plan()
    v = _ro(verses)
    vid = A.verse_ids(v, plan)
    inside = set(vid.values())
    ref = {i: f"{b} {c}:{s}" for i, b, c, s in v.execute("SELECT id, book, chapter, verse FROM verses")}
    n, o = _ro(new), _ro(old)
    a = {(r[0], r[1]): r[2:] for r in _rows(n)}
    b = {(r[0], r[1]): r[2:] for r in _rows(o)}
    n.close()
    o.close()
    count = {(w, k): 0 for w in ("inside", "outside") for k in ("same", "only new", "only old", "differs")}
    listed = []
    for key in sorted(set(a) | set(b)):
        x, y = a.get(key), b.get(key)
        k = "same" if x == y else "only new" if y is None else "only old" if x is None else "differs"
        w = "inside" if key[0] in inside else "outside"
        count[(w, k)] += 1
        if k != "same":
            listed.append((w, k, key, x, y))
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("where\tkind\tverse\tposition\tenglish\tstrongs\tnew_form\tnew_translit\told_form\told_translit\n")
        for w, k, (vi, pos), x, y in listed:
            word = v.execute("SELECT english, strongs FROM words WHERE verse_id=? AND position=?", (vi, pos)).fetchone()
            cells = [w, k, ref.get(vi, f"verse_id {vi}"), str(pos), *(word or ("(no word row)", ""))]
            cells += [*(x or ("", "")), *(y or ("", ""))]
            f.write("\t".join("" if c is None else str(c) for c in cells) + "\n")
    v.close()
    print(f"new {len(a):,} rows / old {len(b):,} rows; the plan's verses: {len(inside):,}")
    for w in ("inside", "outside"):
        print(f"  {w:7} the plan's verses: " + " / ".join(f"{k} {count[(w, k)]:,}" for k in
                                                         ("same", "only new", "only old", "differs")))
    print(f"every slot not the same listed in {out} ({len(listed):,} rows)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Split double rows copy proof tools (DESIGN 9.281).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("save")
    s.add_argument("db")
    s.add_argument("out")
    c = sub.add_parser("compare")
    c.add_argument("new")
    c.add_argument("old")
    c.add_argument("--verses", required=True)
    c.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "save":
            save(a.db, a.out)
        else:
            compare(a.new, a.old, a.verses, a.out)
    except (Stop, A.Stop) as e:
        print(f"PROOF {a.cmd.upper()} RESULT: STOP - {e}")
        return 1
    print(f"PROOF {a.cmd.upper()} RESULT: DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
