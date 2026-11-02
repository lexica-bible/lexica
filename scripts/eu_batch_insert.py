#!/usr/bin/env python3
"""eu_batch_insert.py — register the edition-upgrade corrections batch (DESIGN_q2_build §9.68,
§9.72, §9.74, §9.76) in abp_corrections on the build SOURCE copy, before stage B.

Input: the rows the read-only expansion wrote (scripts/eu_batch_expand.py ->
~/edition_upgrade_runs/eu_batch_20261102/eu_batch_rows.tsv). The file is pinned by --sha256
and its row count by --expect, so only the reviewed file can be inserted.

  dry run (default, writes nothing):   python3 scripts/eu_batch_insert.py <copy.db> --sha256 H --expect N
  apply:                               python3 scripts/eu_batch_insert.py <copy.db> --sha256 H --expect N --apply

Before anything is written it STOPs on: the live database (or any file named bible.db) · a
file whose sha256 or row count is not the pinned one · ANY existing abp_corrections row, of
any status, on the same (book, chapter, verse, position, field) — the table's own
no-resurrection rule (build_abp_corrections.py) · a duplicate key inside the batch · a
source_value equal to its corrected_value. It prints the table's counts by status before
and after, and every row it writes (or would write). Rows go in as status 'active',
applied_at 'ingest' (the post-build apply: verses.text at finish_rebuild step 4b, word
cells at step 7), ledger_ref EU-<verse>, created 2026-11-02.
"""
import argparse
import collections
import csv
import hashlib
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

ROWS = Path("~/edition_upgrade_runs/eu_batch_20261102/eu_batch_rows.tsv").expanduser()
CREATED = "2026-11-02"
REASON = {   # group -> (what the app edition got wrong, the ruling)
    "P5": ("app-edition misspelling of a name", "§9.72"),
    "C1": ("app-edition name form contradicts the Greek at the slot; old form restored", "§9.72"),
    "havee": ("app-edition split word 'ha ve'", "§9.72"),
    "glued": ("app-edition glued alternate gloss (escaped the glue census)", "§9.72"),
    "typo": ("app-edition typo", "§9.74"),
    "appended": ("app-edition appended second gloss; old wording restored", "§9.74"),
    "agape": ("app-edition transliteration 'agape' for ἀγάπη; old wording restored", "§9.74/§9.76"),
    "agape-DIFFERS": ("app-edition transliteration 'agape' for ἀγάπη; word-only fix, feed bracket kept", "§9.76"),
    "jeroboam": ("app-edition adds 'II' (not in the Greek)", "§9.74"),
    "call": ("app-edition 'affected' drops the sense of ὀπισθότονος", "§9.74"),
    "bebe": ("app-edition doubled 'be be'", "§9.74/§9.76"),
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def reason_for(group):
    parts = [REASON[g] for g in group.split("+")]
    what = "; ".join(dict.fromkeys(p[0] for p in parts))
    secs = ", ".join(dict.fromkeys(p[1] for p in parts))
    return f"edition upgrade: {what} (DESIGN_q2_build {secs})"


def load(path):
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    out = []
    for r in rows:
        out.append({"book": r["book"], "chapter": int(r["chapter"]), "verse": int(r["verse"]),
                    "position": int(r["position"]), "field": r["field"],
                    "source_value": r["source_value"] if r["source_value"] != "" else None,
                    "corrected_value": r["corrected_value"] if r["corrected_value"] != "" else None,
                    "ledger_ref": r["ledger_ref"], "reason": reason_for(r["group"]), "group": r["group"]})
    return out


def main(argv=None):
    from dryrun_rekey_fill import is_live          # the ONE live-path gate
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--rows", default=str(ROWS))
    ap.add_argument("--sha256", required=True, help="pinned sha256 of the reviewed rows file")
    ap.add_argument("--expect", type=int, required=True, help="pinned row count")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    if is_live(a.db):
        print(f"STOP: {a.db} is the live database (or a file named bible.db) - copies only.")
        return 1
    if not Path(a.db).is_file():
        print(f"STOP: {a.db} not found.")
        return 1
    got = sha256(a.rows)
    if got != a.sha256:
        print(f"STOP: {a.rows} sha256 {got} != pinned {a.sha256}")
        return 1
    rows = load(a.rows)
    if len(rows) != a.expect:
        print(f"STOP: {len(rows)} rows in the file != pinned {a.expect}")
        return 1
    keys = collections.Counter((r["book"], r["chapter"], r["verse"], r["position"], r["field"]) for r in rows)
    dups = [k for k, n in keys.items() if n > 1]
    same = [r for r in rows if r["source_value"] == r["corrected_value"]]
    if dups or same:
        print(f"STOP: duplicate keys in the batch {dups[:5]} / rows that change nothing {len(same)}")
        return 1

    con = sqlite3.connect(a.db)
    con.execute("PRAGMA journal_mode=DELETE")
    con.execute("PRAGMA busy_timeout=5000")
    def counts():
        return dict(con.execute("SELECT status, count(*) FROM abp_corrections GROUP BY status ORDER BY status"))
    before = counts()
    clash = []
    for k in keys:
        hit = con.execute("SELECT id, status, ledger_ref FROM abp_corrections WHERE book=? AND chapter=? "
                          "AND verse=? AND position=? AND field=?", k).fetchall()
        if hit:
            clash.append((k, hit))
    mode = "APPLY" if a.apply else "DRY RUN"
    print(f"[{mode}] edition-upgrade corrections batch -> {a.db}")
    print(f"  rows file {a.rows} (sha256 {got[:12]}..., {len(rows)} rows: "
          + ", ".join(f"{f} {n}" for f, n in sorted(collections.Counter(r['field'] for r in rows).items())) + ")")
    print(f"  abp_corrections before: {before}")
    if clash:
        print(f"STOP: {len(clash)} batch key(s) already have a row in abp_corrections (any status blocks):")
        for k, hit in clash[:20]:
            print(f"    {k} -> {hit}")
        con.close()
        return 1
    for r in rows:
        loc = "[verses.text]" if r["field"] == "verses.text" else f"pos {r['position']} {r['field']}"
        print(f"  {'+' if a.apply else '~'} {r['book']} {r['chapter']}:{r['verse']} {loc} [{r['ledger_ref']}]"
              f"  {(r['source_value'] or '')[:60]!r} -> {(r['corrected_value'] or '')[:60]!r}")
    if not a.apply:
        print(f"  DRY RUN - nothing written. Would insert {len(rows)}; active would become "
              f"{before.get('active', 0) + len(rows)}.")
        con.close()
        return 0
    con.executemany(
        """INSERT INTO abp_corrections (book, chapter, verse, position, field, source_value,
               corrected_value, reason, ledger_ref, applied_at, status, created)
           VALUES (?,?,?,?,?,?,?,?,?,'ingest','active',?)""",
        [(r["book"], r["chapter"], r["verse"], r["position"], r["field"], r["source_value"],
          r["corrected_value"], r["reason"], r["ledger_ref"], CREATED) for r in rows])
    con.commit()
    after = counts()
    n_new = con.execute("SELECT count(*) FROM abp_corrections WHERE ledger_ref LIKE 'EU-%'").fetchone()[0]
    con.close()
    print(f"  abp_corrections after: {after}")
    print(f"  EU- rows on the copy: {n_new} (expected {len(rows)})")
    ok = n_new == len(rows) and after.get("active", 0) == before.get("active", 0) + len(rows)
    print("RESULT: " + ("INSERTED - counts as expected" if ok else "MISMATCH - read the counts above"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
