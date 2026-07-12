#!/usr/bin/env python3
"""audit_range_tails.py — READ-ONLY resweep for the #28 scanner fix (batch-5 s1, JP-ruled).

For every live lexica_def card (or a named subset), parses the stored prose with BOTH
scanners — the old bare Book-ch:vs catcher and the new tail-expanding ref_spans — and
prints the delta: every ref that was INVISIBLE to the old scanner. A card with a delta is
one whose citation counting was under-reporting; each such card gets a line in the TODO
ticket per the JP ruling.

Usage (on PA, from ~/bible-db):
  python3 scripts/audit_range_tails.py bible.db                      # all cards
  python3 scripts/audit_range_tails.py bible.db --verify             # + classify each delta ref
  python3 scripts/audit_range_tails.py bible.db G5547 G227 G1119     # named cards only

--verify classifies every newly visible ref against the corpus (the UNSEEN taxonomy):
  OCC       the verse exists AND the card's word occurs in it — a clean legal citation
  NO-OCC    the verse exists but the word does NOT occur there — cross-reference or a
            problem; needs eyes (UNSEEN-REAL vs mention adjudication)
  NO-VERSE  no such verse in the corpus — hard problem, ticket + live-card bullet

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


def _classify(conn, sid, bk, ch, vs):
    """OCC / NO-OCC / NO-VERSE for one (book, ch, vs) against the card's word. Occurrence
    check uses the exact-or-dotted BOTH-clause on the bare words key (sid is G-prefixed)."""
    row = conn.execute("SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
                       (bk, ch, vs)).fetchone()
    if not row:
        return "NO-VERSE"
    num = sid.lstrip("G")
    occ = conn.execute(
        "SELECT 1 FROM words WHERE verse_id=? AND (strongs=? OR strongs LIKE ?) LIMIT 1",
        (row[0], num, num + ".%")).fetchone()
    return "OCC" if occ else "NO-OCC"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    args = [a for a in sys.argv[1:] if a != "--verify"]
    verify = "--verify" in sys.argv
    db, only = args[0], set(args[1:])
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
            if verify:
                parts = []
                for b, c, v in delta:
                    cls = _classify(conn, sid, b, c, v)
                    parts.append(f"{b} {c}:{v}" + ("" if cls == "OCC" else f" [{cls}]"))
                refs = ", ".join(parts)
            else:
                refs = ", ".join(f"{b} {c}:{v}" for b, c, v in delta)
            print(f"{sid:8s} {lemma:12s} +{len(delta):2d} newly visible: {refs}")
        for rt in refused_tails(text):
            print(f"{sid:8s} {lemma:12s} REFUSED-TAIL: '{rt}' — not expanded, adjudicate by hand")
    print(f"\n{hit} of {total} cards checked carry refs the old scanner missed.")


if __name__ == "__main__":
    main()
