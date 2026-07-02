#!/usr/bin/env python3
"""
populate_coverage_audit.py — splice the piece-B coverage_audit field into built lexica_def entries,
touching NOTHING else.

WHY NOT --resplit: build_lexica_def --resplit rebuilds the WHOLE entry from stored raw against the
current code + register (sense splits, fork/pinned_core, provenance, the citation gate). Any drift
in that pipeline since an entry was hand-audited would silently rewrite audited content. The 18
entries are hand-audited; a field-population step must not put that at risk.

THIS script instead reads each stored entry, computes ONLY coverage_audit, and writes back
{**stored_entry, "coverage_audit": ...} — so the one and only key that can differ is coverage_audit.
It VERIFIES that (dry-run diff shows the changed keys per entry) and REFUSES to write any entry whose
diff is not exactly {coverage_audit}.

  workon bible-env
  python scripts/backup_db.py                                  # ALWAYS first
  python scripts/populate_coverage_audit.py                    # dry-run: per-entry key diff, no write
  python scripts/populate_coverage_audit.py --word G2316       # one word, dry-run
  python scripts/populate_coverage_audit.py --apply            # WRITE (only the coverage_audit key)

Reads words/verses/lexicon read-only for the evidence; writes ONLY the def_json column of lexica_def
(and bumps its `updated` stamp). bible.db is PA-only.
"""

import argparse, datetime, json, os, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_lexica_def as B
import lexica_coverage as C


def compute_coverage(conn, sid, entry):
    """The one field — computed from the STORED entry's raw + senses, no model, no rebuild."""
    raw = entry.get("raw", "")
    senses_block = entry.get("senses_block", "")
    pred, params = B.abp_filter(conn, sid)
    occs = B.occurrences(conn, pred, params)
    return C.coverage_audit(
        conn, sid, occs,
        entry_refs=B.cited_refs(raw),
        sense_specs=B.sense_specs(senses_block),
        contest_verses=B.contest_verses(sid),
        is_contested=(sid in B._CONTESTED_BY_SID))


def changed_keys(old, new):
    return sorted(k for k in (set(old) | set(new)) if old.get(k) != new.get(k))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"))
    ap.add_argument("--word", help="one G-number (default: every built entry)")
    ap.add_argument("--apply", action="store_true", help="write (only the coverage_audit key)")
    args = ap.parse_args()

    if args.apply:
        conn = sqlite3.connect(args.db)
    else:
        conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    if not C._table_exists(conn, "lexica_def"):
        sys.exit("no lexica_def table.")
    if args.word:
        w = args.word.upper()
        targets = ["G" + w if w[:1] not in ("G", "H") else w]
    else:
        targets = [r["strongs"] for r in
                   conn.execute("SELECT strongs FROM lexica_def ORDER BY strongs")]

    print(f"{'APPLY' if args.apply else 'DRY-RUN'} — {len(targets)} entr(y/ies). "
          f"Each write must diff to EXACTLY [coverage_audit].\n")
    wrote, refused = 0, 0
    for sid in targets:
        row = conn.execute("SELECT def_json, synth_ver FROM lexica_def WHERE strongs=?",
                           (sid,)).fetchone()
        if not row or not row["def_json"]:
            print(f"  {sid}: no stored entry — skip.")
            continue
        stored = json.loads(row["def_json"])
        cov = compute_coverage(conn, sid, stored)
        new = {**stored, "coverage_audit": cov}
        diff = changed_keys(stored, new)
        had = "coverage_audit" in stored
        flags = cov.get("flags") or []
        print(f"  {sid}: diff {diff}  ({'update' if had else 'add'} coverage_audit; "
              f"{len(flags)} flag(s){': ' + '; '.join(flags[:4]) if flags else ''})")

        if diff and diff != ["coverage_audit"]:
            print(f"    ✗ REFUSED — diff is not exactly [coverage_audit]: {diff}")
            refused += 1
            continue
        if args.apply:
            conn.execute(
                "UPDATE lexica_def SET def_json=?, updated=? WHERE strongs=?",
                (json.dumps(new, ensure_ascii=False),
                 datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds"),
                 sid))
            conn.commit()
            wrote += 1

    conn.close()
    if args.apply:
        print(f"\nDONE. wrote {wrote}, refused {refused}.")
    else:
        print(f"\nDRY-RUN done. {len(targets)} checked, {refused} would be refused. "
              f"Re-run with --apply to write (backup first).")
    if refused:
        sys.exit(f"{refused} entr(y/ies) refused — investigate before applying.")


if __name__ == "__main__":
    main()
