#!/usr/bin/env python3
"""Lane-② ride instrument: verify the PN-star pass's writes BY MEMBER.

Parses the WRITES section of plan_pn_star_corrected.txt (the pre-registered
member record, regenerated at the ride) and checks every member against the
BUILT copy's words table. Read-only. Counts are tripwires; the member set
rules — every miss is printed with the verse's actual rows so it can be
attributed to its owning step (the fresh-derived tail allowance) or HALT.

For a class-A member (star carried, moved run -> numbered neighbour):
  MOVE-IN : some slot with strongs_base G<base> whose normalized english
            equals (or contains, flagged 'loose') the moved run.
For a class-B member (carrier at G<base>, name -> the empty star):
  MOVE-OUT: no G<base> slot in the verse still carries the moved name token(s).
  MOVE-IN : some OTHER slot carries exactly/at-least the moved name token(s)
            (pre-tipnr that slot reads '*'; post-tipnr it holds the PN number,
            so the check keys on content, not on '*').

Usage:  python3 scripts/check_pn_star_members.py <db> [plan_file]
"""
import ast, re, sqlite3, sys, collections

NORM = re.compile(r"[^\w]")

def norm_tokens(eng):
    return [t for t in (NORM.sub("", w).lower() for w in (eng or "").split()) if t]

def parse_plan(path):
    members = []
    in_writes = False
    line_re = re.compile(r"^\s+([AB])\s+(\S+)\s+(\d+):(\d+)\s+slot\s+(\d+)\s+G(\S+)\s+(.+)$")
    with open(path, encoding="utf-8", errors="replace") as f:
        for ln in f:
            if "WRITES (the full decision record):" in ln:
                in_writes = True
                continue
            if in_writes:
                if ln.strip().startswith("TOTAL WRITES:"):
                    break
                m = line_re.match(ln.rstrip("\n"))
                if not m:
                    if ln.strip():
                        print("  UNPARSED write line: %r" % ln.rstrip())
                    continue
                cls, bk, ch, vs, slot, base, movedrepr = m.groups()
                moved = ast.literal_eval(movedrepr.strip())
                members.append((cls, bk, int(ch), int(vs), int(slot),
                                base.strip(), moved))
    return members

def main():
    db = sys.argv[1]
    plan = sys.argv[2] if len(sys.argv) > 2 else "plan_pn_star_corrected.txt"
    members = parse_plan(plan)
    by_cls = collections.Counter(m[0] for m in members)
    print("plan members parsed: %d (A %d + B %d)"
          % (len(members), by_cls["A"], by_cls["B"]))

    conn = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    verses = collections.defaultdict(list)
    books = set()
    for bk, ch, vs, pos, eng, sb in conn.execute(
            "SELECT v.book, v.chapter, v.verse, w.position, w.english,"
            " w.strongs_base FROM words w JOIN verses v ON v.id = w.verse_id"):
        verses[(bk, ch, vs)].append((pos, eng, sb, norm_tokens(eng)))
        books.add(bk)
    conn.close()

    exact = loose = 0
    misses, no_verse = [], []
    for cls, bk, ch, vs, slot, base, moved in members:
        rows = verses.get((bk, ch, vs))
        if rows is None:
            no_verse.append((cls, bk, ch, vs, base, moved))
            continue
        mtoks = moved.split()
        gbase = "G" + base
        # A verse can hold the same number twice (Jdg 11:17 G649 x2), so every
        # leg keys on the PLAN'S SLOT (+/- a small window for the blank-slot
        # walk), never on the number alone — the repeated-key trap.
        near = [r for r in rows if abs(r[0] - slot) <= 6]
        if cls == "A":
            hit = [r for r in near if r[2] == gbase and r[3] == mtoks]
            sub = [r for r in near if r[2] == gbase and
                   all(t in r[3] for t in mtoks)]
        else:
            still = [r for r in near if r[2] == gbase and r[0] == slot and
                     all(t in r[3] for t in mtoks)]
            landed = [r for r in near if r[2] != gbase and r[3] == mtoks]
            landed_sub = [r for r in near if r[2] != gbase and
                          all(t in r[3] for t in mtoks)]
            hit = landed if not still else []
            sub = landed_sub if not still else []
        if hit:
            exact += 1
        elif sub:
            loose += 1
        else:
            misses.append((cls, bk, ch, vs, slot, base, moved, rows))

    print("exact %d · loose(contains) %d · MISS %d · verse-not-found %d"
          % (exact, loose, len(misses), len(no_verse)))
    if no_verse:
        nb = collections.Counter(m[1] for m in no_verse)
        print("\nVERSE-NOT-FOUND (abbrev mismatch? books in db: %d):" % len(books))
        for bk, n in nb.most_common():
            print("  %-4s %d member(s)" % (bk, n))
    if misses:
        print("\nMISSES (each named for attribution):")
        for cls, bk, ch, vs, slot, base, moved, rows in misses:
            print("  %s %-4s %d:%-3d slot %-3d G%-6s moved=%r" %
                  (cls, bk, ch, vs, slot, base, moved))
            for pos, eng, sb, _t in sorted(rows):
                if eng:
                    print("      pos %-3d %-8s %r" % (pos, sb, eng))
    sys.exit(1 if (misses or no_verse) else 0)

if __name__ == "__main__":
    main()
