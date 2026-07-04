#!/usr/bin/env python3
"""fix_emdash.py — swap ABP's literal double-hyphen "--" for a proper em-dash "—" in the
ABP word glosses (words.english) and the ABP prose (verses.text).

ABP writes its clause dashes as "--", which reads like a typo in the reader. This replaces
every "--" with "—", keeping the surrounding spaces ("wonder -- above" -> "wonder — above").
Only the DOUBLE hyphen is touched — single hyphens inside words (Beer-sheba, self-control)
are left alone. Touches ONLY words.english + verses.text; fully reversible (— back to --).

  python scripts/fix_emdash.py [db]            # DRY RUN: counts + samples, writes nothing
  python scripts/fix_emdash.py [db] --apply    # do the swap

PA-only (bible.db lives there). Runs as step 5 of finish_rebuild.sh, so a rebuild
reproduces it — no manual re-run needed. It is the LAST english-TEXT edit in the tail:
split_merge_fixes.json carries a "--" precondition ("you think not --") that would
stop matching if the swap ran before fix_split_merges. The two steps after it
(fix_split_flip, apply_abp_corrections) are position/field-scoped and depend on the
dashes already being swapped (the flip detector compares words to verses.text).
"""
import os
import sqlite3
import sys

DB = os.path.expanduser("~/bible-db/bible.db")


def main():
    do_apply = "--apply" in sys.argv
    db = next((a for a in sys.argv[1:] if not a.startswith("--")), DB)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    w = conn.execute("SELECT COUNT(*) FROM words  WHERE english LIKE '%--%'").fetchone()[0]
    v = conn.execute("SELECT COUNT(*) FROM verses WHERE text    LIKE '%--%'").fetchone()[0]
    print(f"words.english with '--': {w}    verses.text with '--': {v}")

    if not do_apply:
        print("\nsamples (words.english):")
        for r in conn.execute("SELECT english FROM words WHERE english LIKE '%--%' LIMIT 12"):
            print("   " + (r["english"] or ""))
        print("\n[dry-run] nothing written. Re-run with --apply to swap '--' -> '—'.")
        conn.close()
        return

    conn.execute("UPDATE words  SET english = REPLACE(english, '--', '—') WHERE english LIKE '%--%'")
    conn.execute("UPDATE verses SET text    = REPLACE(text,    '--', '—') WHERE text    LIKE '%--%'")
    conn.commit()
    w2 = conn.execute("SELECT COUNT(*) FROM words  WHERE english LIKE '%--%'").fetchone()[0]
    v2 = conn.execute("SELECT COUNT(*) FROM verses WHERE text    LIKE '%--%'").fetchone()[0]
    conn.close()
    print(f"Done. Remaining '--' (should be 0): words {w2}, verses {v2}.")


if __name__ == "__main__":
    main()
