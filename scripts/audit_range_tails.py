#!/usr/bin/env python3
"""audit_range_tails.py — READ-ONLY resweep for the #28 scanner fix (batch-5 s1, JP-ruled).

For every live lexica_def card (or a named subset), parses the stored prose with BOTH
scanners — the old bare Book-ch:vs catcher and the new tail-expanding ref_spans — and
prints the delta: every ref that was INVISIBLE to the old scanner. A card with a delta is
one whose citation counting was under-reporting; each such card gets a line in the TODO
ticket per the JP ruling.

Usage (on PA, from ~/bible-db):
  python3 scripts/audit_range_tails.py bible.db                      # all cards
  python3 scripts/audit_range_tails.py bible.db G5547 G227 G1119     # named cards only

READ ONLY: opens the database in read-only mode; writes nothing.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_lexica_def import _REF_RE, _norm_book, ref_spans, refused_tails   # noqa: E402


def _old(text):
    return [(_norm_book(bk), int(ch), int(vs)) for bk, ch, vs in _REF_RE.findall(text or "")]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    db, only = sys.argv[1], set(sys.argv[2:])
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = conn.execute("SELECT strongs, lemma, def_json FROM lexica_def ORDER BY strongs").fetchall()
    total, hit = 0, 0
    for sid, lemma, dj in rows:
        if only and sid not in only:
            continue
        total += 1
        d = json.loads(dj)
        text = "\n".join(str(d.get(k) or "") for k in ("senses_block", "range", "gloss_notes", "coverage"))
        old = _old(text)
        new = ref_spans(text)
        old_set, delta = set(old), []
        for key in new:
            if key not in old_set and key not in delta:
                delta.append(key)
        if delta:
            hit += 1
            refs = ", ".join(f"{b} {c}:{v}" for b, c, v in delta)
            print(f"{sid:8s} {lemma:12s} +{len(delta):2d} newly visible: {refs}")
        for rt in refused_tails(text):
            print(f"{sid:8s} {lemma:12s} REFUSED-TAIL: '{rt}' — not expanded, adjudicate by hand")
    print(f"\n{hit} of {total} cards checked carry refs the old scanner missed.")


if __name__ == "__main__":
    main()
