#!/usr/bin/env python3
"""BASELINE READ: how many LIVE lexica cards contain a written verse range?

WHY: the reviewer deferred the anti-range LINT question to this number (ruling 2026-07-15).
Pre-committed decision rule, so the number cannot be argued after it lands:
    0   -> the lint is DEAD, closed.
  > 0   -> the only admissible form is a NON-BLOCKING count on the existing gate report.
           A blocking pre-gate lint stays rejected regardless of the number (it duplicates
           the citation gate's teeth and false-fires on ranges whose interior is true).

READ-ONLY. This never writes. It opens the db read-only and only prints.

The range shape is NOT hand-rolled here — that is the banned copy. It comes from the
production walker: _TAIL_UNIT_RE's dash arm (the same regex ref_spans uses to expand a range
into the citations the gate then checks) and refused_tails (the loud channel for ranges the
walker refused: backwards, or wider than 30 verses). If the production shape ever changes,
this read changes with it.

Run on PA (db path is an argument, same shape as audit_range_tails.py):
    python scripts/audit_range_baseline.py ~/bible-db/bible.db
"""
import sys, os, json, sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from build_lexica_def import _REF_RE, _TAIL_UNIT_RE, refused_tails   # noqa: E402


def ranges_in(text):
    """Every written verse range in this prose, via the PRODUCTION walker's own dash arm.
    Mirrors ref_spans' walk exactly: find a ref, then step the tail units after it; report the
    units that are ranges. Never a second copy of the range shape."""
    found = []
    for m in _REF_RE.finditer(text or ""):
        pos = m.end()
        ch, vs = int(m.group(2)), int(m.group(3))
        while True:
            t = _TAIL_UNIT_RE.match(text, pos)
            if not t:
                break
            if t.group("end") is not None:
                found.append(f"{m.group(1)} {ch}:{vs}{t.group('dash')}{t.group('end')}")
                vs = int(t.group("end"))
            elif t.group("tch") is not None:
                ch, vs = int(t.group("tch")), int(t.group("tvs"))
            else:
                vs = int(t.group("tv"))
            pos = t.end()
    return found


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    db = os.path.expanduser(sys.argv[1])
    if not os.path.exists(db):
        sys.exit(f"no db at {db}")
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    # columns READ from the production writer's CREATE (build_lexica_def.py:3153), not recalled:
    # strongs / lemma / translit / def_json / synth_ver / updated. The key is `strongs`.
    rows = conn.execute("SELECT strongs, lemma, def_json FROM lexica_def ORDER BY strongs").fetchall()

    cards_with = 0
    total_ranges = 0
    print(f"live cards read: {len(rows)}\n")
    for sid, lemma, dj in rows:
        try:
            d = json.loads(dj or "{}")
        except Exception:
            print(f"{sid:8s} UNREADABLE def_json -- flagging, not skipping silently")
            continue
        # READ `raw` ONLY -- the SAME field the production gate reads (build_lexica_def.py:3242,
        # `refused_tails(entry.get("raw", ""))`). raw is the model's full prose; senses/range/
        # gloss_notes/coverage are SPLIT OUT OF IT and stored alongside (":2222 -- kept so an
        # improved splitter can re-split"). A first pass joined every text field and counted every
        # range TWICE (once in raw, once in its section) -- 100 ranges reported where there were
        # ~50. Caught on the live output: every card's list was its own ranges duplicated.
        prose = d.get("raw") or ""
        if not prose:
            print(f"{sid:8s} NO raw FIELD -- flagging, not skipping silently")
            continue
        hits = ranges_in(prose)
        refused = refused_tails(prose)
        if hits or refused:
            cards_with += 1
            total_ranges += len(hits)
            print(f"{sid:8s} ranges={len(hits)}  {', '.join(hits) if hits else ''}")
            for r in refused:
                print(f"{'':8s}   REFUSED-TAIL (never expanded): {r}")

    print("\n" + "=" * 64)
    print(f"BASELINE: {cards_with} of {len(rows)} live cards contain a written verse range")
    print(f"          {total_ranges} ranges total")
    print("=" * 64)
    print("DECISION (pre-committed, reviewer 2026-07-15):")
    print("  0   -> lint DEAD, closed.")
    print("  >0  -> non-blocking count on the gate report ONLY; blocking lint stays rejected.")
    conn.close()


if __name__ == "__main__":
    main()
