#!/usr/bin/env python3
"""Lane-② ride instrument: attribute restore_frozen_pn's dry-run members.

The 2026-08-05 ride HALTed restore_frozen_pn at 2,528 vs the declared 6: the
frozen PN record is keyed by (verse_id, position) from the PRE-lane-② geometry,
and the PN-star pass moved name text onto star slots. This joins the dry-run's
member list against the plan's write record and splits it:

  B-WRITE VERSE   — the frozen row sits in a verse where the pass moved a name
                    (expected stale-by-design; restoring would stamp a name
                    number on the verb slot)
  A-WRITE VERSE   — same, class-A side
  CUSHI CLASS     — the declared-6 2Sa 18 members (H3569/H3570)
  UNATTRIBUTED    — none of the above: HALT material, list in full

Usage: python3 scripts/cross_restore_vs_plan.py <db> restore_dry.log \
           plan_pn_star_corrected.txt
Read-only.
"""
import re, sqlite3, sys, collections

def main():
    db, dry_log, plan = sys.argv[1], sys.argv[2], sys.argv[3]

    entry = re.compile(r"^\s*\((\d+),(\d+)\)\s+(.*?): '([^']*)' -> '([^']*)'")
    members = []
    with open(dry_log, encoding="utf-8", errors="replace") as f:
        for ln in f:
            m = entry.match(ln)
            if m:
                members.append((int(m.group(1)), int(m.group(2)),
                                m.group(3), m.group(4), m.group(5)))
    print("dry-run members parsed: %d" % len(members))

    wline = re.compile(r"^\s+([AB])\s+(\S+)\s+(\d+):(\d+)\s+slot\s+(\d+)\s+G(\S+)\s+(.+)$")
    plan_verses = {}          # (bk,ch,vs) -> set of classes
    in_writes = False
    with open(plan, encoding="utf-8", errors="replace") as f:
        for ln in f:
            if "WRITES (the full decision record):" in ln:
                in_writes = True
                continue
            if in_writes:
                if ln.strip().startswith("TOTAL WRITES:"):
                    break
                m = wline.match(ln.rstrip("\n"))
                if m:
                    key = (m.group(2), int(m.group(3)), int(m.group(4)))
                    plan_verses.setdefault(key, set()).add(m.group(1))

    conn = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    ref = {vid: (bk, ch, vs) for vid, bk, ch, vs in
           conn.execute("SELECT id, book, chapter, verse FROM verses")}
    conn.close()

    buckets = collections.Counter()
    unattributed = []
    for vid, pos, word, old, new in members:
        r = ref.get(vid)
        if r is None:
            buckets["NO-SUCH-VERSE"] += 1
            unattributed.append((vid, pos, word, old, new, "?"))
            continue
        if new in ("H3569", "H3570") or old in ("H3569", "H3570"):
            buckets["CUSHI CLASS"] += 1
            continue
        classes = plan_verses.get(r, set())
        if "B" in classes:
            buckets["B-WRITE VERSE"] += 1
        elif "A" in classes:
            buckets["A-WRITE VERSE"] += 1
        else:
            buckets["UNATTRIBUTED"] += 1
            unattributed.append((vid, pos, word, old, new,
                                 "%s %d:%d" % r))

    print("\nattribution:")
    for k, n in buckets.most_common():
        print("  %6d  %s" % (n, k))
    if unattributed:
        print("\nUNATTRIBUTED members (full list — HALT material):")
        for vid, pos, word, old, new, r in unattributed:
            print("  (%d,%d) %s %r: %s -> %s" % (vid, pos, r, word, old, new))
    sys.exit(1 if unattributed else 0)

if __name__ == "__main__":
    main()
