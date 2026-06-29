#!/usr/bin/env python3
"""
verify_resplit_glances.py — READ-ONLY regression check for the split3 sense-header fix.

For every row already in lexica_def it compares the STORED glance (sense_headlines, written by the
old splitter) against what the CURRENT splitter produces from the SAME stored raw prose. The fix is
additive (bold parsed exactly as before, plain accepted as a fallback), so every existing card — all
bold — must come back IDENTICAL. Any DIFF is drift and must be read before persisting.

Run this BEFORE `build_lexica_def.py --resplit --apply --all`, so you confirm no drift while the old
glance is still on disk to compare against.

PA-ONLY (lexica_def lives in bible.db). READ-ONLY: opens bible.db ?mode=ro, writes nothing. No model.
Exits non-zero if anything drifted.

  workon bible-env
  python scripts/verify_resplit_glances.py
"""

import os, sys, json, sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_lexica_def as B


def main():
    db = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/bible-db/bible.db")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT strongs, lemma, def_json FROM lexica_def ORDER BY strongs").fetchall()
    if not rows:
        sys.exit("no rows in lexica_def.")

    print(f"splitter version: {B.SPLIT_VER}   prompt stamp: {B.synth_ver()}")
    print(f"comparing stored glance vs the current splitter on {len(rows)} card(s)\n")
    print(f"  {'strongs':<8} {'lemma':<14} {'old→new':>8}  result")
    print("  " + "-" * 46)

    diffs = []
    for r in rows:
        d = json.loads(r["def_json"])
        old = d.get("sense_headlines", [])
        new = B.split_definition(d.get("raw", "")).get("sense_headlines", [])
        same = (old == new)
        if not same:
            diffs.append((r["strongs"], r["lemma"], old, new))
        print(f"  {r['strongs']:<8} {(r['lemma'] or ''):<14} {len(old):>3}→{len(new):<3}  "
              + ("SAME" if same else "DIFF  <<<<"))

    # show a couple of full before/afters so 'no drift' is visible, not just asserted
    print("\nsample before/after (first 2 cards):")
    for r in rows[:2]:
        d = json.loads(r["def_json"])
        old = d.get("sense_headlines", [])
        new = B.split_definition(d.get("raw", "")).get("sense_headlines", [])
        print(f"  {r['strongs']} {r['lemma']}")
        print(f"     OLD: {old}")
        print(f"     NEW: {new}")

    if diffs:
        print(f"\n!! {len(diffs)} card(s) DRIFTED — read before persisting:")
        for sid, lemma, old, new in diffs:
            print(f"  {sid} {lemma}\n     OLD: {old}\n     NEW: {new}")
        conn.close()
        sys.exit(1)

    print(f"\nALL {len(rows)} IDENTICAL — no drift. Safe to run "
          f"`build_lexica_def.py --resplit --apply --all`.")
    conn.close()


if __name__ == "__main__":
    main()
