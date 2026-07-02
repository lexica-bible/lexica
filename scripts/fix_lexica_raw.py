#!/usr/bin/env python3
"""
fix_lexica_raw.py — surgical correction of a stored Lexica entry's RAW model prose, then
re-assemble the entry from the corrected text (NO model call).

For one-off artifacts in the model's own output — a doubled reference, a malformed citation —
that aren't worth a full re-generation, and that we explicitly do NOT want to re-generate
because regenerating would replace proven, reviewed prose with a fresh (unreviewed) draft.

It does an EXACT string replacement on the stored raw (the text must occur exactly once, or it
aborts), then runs the canonical assemble() from build_lexica_def — which re-splits the display
fields, rebuilds verses[], and re-runs the citation gate — shows the result, and on --apply
writes the one row back. The engine stamp (synth_ver) is preserved: a surgical edit of the raw
is not a new generation, so the entry's identity is unchanged.

PA-ONLY (bible.db lives on PA). Reads words / verses for the citation gate; WRITES ONLY its own
row in lexica_def. --dry-run is the DEFAULT — pass --apply to write.

  # charis G5484 sense-6: the model wrote "1Ti—" (no verse) for 1 Timothy's grace+peace greeting,
  # which is 1Ti 1:2; it also used a comma where the list uses semicolons.
  python scripts/fix_lexica_raw.py --word G5484 \
      --old "2Th 1:2; 1Ti—, Gal 1:3" --new "2Th 1:2; 1Ti 1:2; Gal 1:3"            # show, no write
  python scripts/fix_lexica_raw.py --word G5484 \
      --old "2Th 1:2; 1Ti—, Gal 1:3" --new "2Th 1:2; 1Ti 1:2; Gal 1:3" --apply    # write
"""
import argparse, datetime, json, os, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_lexica_def as B


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"))
    ap.add_argument("--word", required=True, help="G/H number, e.g. G5484")
    ap.add_argument("--old", help="exact text in the stored raw to replace (must occur once)")
    ap.add_argument("--new", help="replacement text")
    ap.add_argument("--show-raw", action="store_true", dest="show_raw",
                    help="print the stored raw prose and exit — to craft an exact --old/--new edit")
    ap.add_argument("--apply", action="store_true", help="write the row (default: dry-run, show only)")
    args = ap.parse_args()

    sid = args.word.upper()
    if sid[:1] not in ("G", "H"):
        sid = "G" + sid

    # Read-only unless we're actually writing the row (--apply); a dry-run / --show-raw must never
    # be able to touch the live file (audit C3, 2026-07-01 — same invariant as build_lexica_def.py).
    if args.apply:
        conn = sqlite3.connect(args.db)
    else:
        conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.create_function("strip_accents", 1, B.strip_accents)

    row = conn.execute("SELECT def_json, synth_ver FROM lexica_def WHERE strongs=?", (sid,)).fetchone()
    if not row or not row["def_json"]:
        sys.exit(f"no stored Lexica row for {sid}")
    e = json.loads(row["def_json"])
    raw = e.get("raw", "")
    if args.show_raw:
        print(f"\n===== {sid}  {e.get('lemma','')} — stored raw prose =====\n")
        print(raw)
        conn.close()
        return
    if args.old is None or args.new is None:
        sys.exit("pass --old AND --new (exact text to replace), or --show-raw to dump the raw.")
    # --new "" is a legitimate CUT (delete the matched text), not a missing arg — so test for
    # None, not falsiness. The exact-once guard below still protects against a bad --old.
    n = raw.count(args.old)
    if n != 1:
        sys.exit(f"--old must match the stored raw EXACTLY ONCE; found {n}. Aborting (nothing changed).")

    raw2 = raw.replace(args.old, args.new)
    print(f"\n{sid}  {e.get('lemma','')}")
    print(f"  -  {args.old}")
    print(f"  +  {args.new}")

    entry = B.assemble(conn, sid, e.get("lemma") or sid, e.get("translit") or "", raw2)
    entry["synth_ver"] = row["synth_ver"] or B.synth_ver()   # surgical edit ≠ new generation: keep the stamp
    B.show_entry(entry)

    problems = B.validate_entry(entry)
    if problems:
        print("  ✗ PARSE FAILURE — not written:")
        for p in problems:
            print("     - " + p)
        sys.exit(1)

    if args.apply:
        conn.execute(
            "INSERT OR REPLACE INTO lexica_def (strongs, lemma, translit, def_json, synth_ver, updated) "
            "VALUES (?,?,?,?,?,?)",
            (sid, entry["lemma"], entry["translit"], json.dumps(entry, ensure_ascii=False),
             entry["synth_ver"],
             datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")))
        conn.commit()
        print("  → written to lexica_def.")
    else:
        print("  [dry run — not written]")
    conn.close()


if __name__ == "__main__":
    main()
