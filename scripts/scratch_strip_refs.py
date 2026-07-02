#!/usr/bin/env python3
"""
scratch_strip_refs.py — remove named citations from a word's stored entry in a THROWAWAY copy of
bible.db, so the coverage check can be validated against a reconstructed "before" state.

Use for the pre-splice theos acceptance test: strip Deu 32:8 (the independent support spliced into
sense 3) from a scratch copy, then run the coverage audit on that copy — sense 3 should come back
CIRCULAR (its only remaining support is Psa 82 itself).

  # 1. make a throwaway copy (never edit the live db)
  cp ~/bible-db/bible.db /tmp/scratch.db
  # 2. see what would be stripped (dry-run, no write)
  python scripts/scratch_strip_refs.py --db /tmp/scratch.db --word G2316 --strip "Deu 32:8"
  # 3. strip it in the copy
  python scripts/scratch_strip_refs.py --db /tmp/scratch.db --word G2316 --strip "Deu 32:8" --apply
  # 4. run the read-only coverage check on the copy
  python scripts/audit_lexica_coverage.py --coverage --db /tmp/scratch.db --word G2316

  # Reconstruct pre-sense-6 G5207 WITHOUT a backup: strip every son-of-man (huios+anthrōpos)
  # citation, so the entry no longer cites the collocation:
  python scripts/scratch_strip_refs.py --db /tmp/scratch5207.db --word G5207 --strip-collocation G444 --apply
  python scripts/audit_lexica_coverage.py --coverage --db /tmp/scratch5207.db --word G5207

REFUSES to touch the live ~/bible-db/bible.db (guards against editing the real corpus). It edits
ONLY the `raw` + `senses_block` text of the entry (what the coverage audit reads), nothing else.
"""

import argparse, json, os, re, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LIVE = os.path.realpath(os.path.expanduser("~/bible-db/bible.db"))


def strip_refs(text, refs):
    """Remove each 'Book ch:vs' from prose — plus a now-empty '()' or a dangling '; ' it leaves."""
    for r in refs:
        text = text.replace(r, "")
    text = re.sub(r"\(\s*[;,]\s*", "(", text)      # "(; Psa 82:6)" -> "(Psa 82:6)"
    text = re.sub(r"[;,]\s*\)", ")", text)          # "(Psa 82:6; )" -> "(Psa 82:6)"
    text = re.sub(r"\(\s*\)", "", text)             # "()" -> ""
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="path to a THROWAWAY copy of bible.db")
    ap.add_argument("--word", required=True)
    ap.add_argument("--strip", action="append", default=[], metavar="REF",
                    help="a citation to remove, e.g. 'Deu 32:8' (repeatable)")
    ap.add_argument("--strip-collocation", action="append", default=[], metavar="NEIGHBOR",
                    help="remove EVERY citation where the word sits adjacent to this neighbor "
                         "(e.g. G444 for son-of-man) — reconstructs 'entry doesn't cite the "
                         "collocation'. Repeatable.")
    ap.add_argument("--apply", action="store_true", help="write the edit into the copy")
    args = ap.parse_args()

    if not args.strip and not args.strip_collocation:
        sys.exit("give at least one --strip REF or --strip-collocation NEIGHBOR.")
    if os.path.realpath(args.db) == LIVE:
        sys.exit("REFUSED: that is the live bible.db. Copy it first (cp ~/bible-db/bible.db /tmp/scratch.db).")

    sid = args.word.upper()
    sid = "G" + sid if sid[:1] not in ("G", "H") else sid
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT def_json FROM lexica_def WHERE strongs=?", (sid,)).fetchone()
    if not row:
        sys.exit(f"{sid}: no stored entry in {args.db}.")
    entry = json.loads(row["def_json"])

    # expand any --strip-collocation into the concrete verse refs to remove
    refs = list(args.strip)
    if args.strip_collocation:
        import build_lexica_def as B
        import lexica_coverage as C
        pred, params = B.abp_filter(conn, sid)
        occs = B.occurrences(conn, pred, params)
        colloc = C.collocation_map(conn, sid, occs)
        for neigh in args.strip_collocation:
            neigh = neigh.upper()
            neigh = "G" + neigh if neigh[:1] not in ("G", "H") else neigh
            vids = colloc.get(neigh) or set()
            added = 0
            for vid in vids:
                v = conn.execute("SELECT book, chapter, verse FROM verses WHERE id=?", (vid,)).fetchone()
                if v:
                    refs.append(f"{v['book']} {v['chapter']}:{v['verse']}")
                    added += 1
            print(f"  --strip-collocation {neigh}: {added} adjacency verse(s) to remove")

    before_raw, before_sb = entry.get("raw", ""), entry.get("senses_block", "")
    after_raw = strip_refs(before_raw, refs)
    after_sb = strip_refs(before_sb, refs)
    hit = (after_raw != before_raw) or (after_sb != before_sb)

    print(f"{sid}: stripping {len(refs)} ref(s)  — {'found + would change' if hit else 'NOT FOUND (no change)'}")
    if not hit:
        sys.exit("nothing to strip — check the exact ref text (must match how the prose wrote it).")

    if args.apply:
        entry["raw"], entry["senses_block"] = after_raw, after_sb
        conn.execute("UPDATE lexica_def SET def_json=? WHERE strongs=?",
                     (json.dumps(entry, ensure_ascii=False), sid))
        conn.commit()
        print(f"  → written into {args.db}. Now run: "
              f"python scripts/audit_lexica_coverage.py --coverage --db {args.db} --word {sid}")
    else:
        print("  [dry run — not written]  re-run with --apply to edit the copy.")
    conn.close()


if __name__ == "__main__":
    main()
