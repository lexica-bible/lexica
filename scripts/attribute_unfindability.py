#!/usr/bin/env python3
"""Lane-② ride instrument: attribute audit_unfindability's AFTER failures.

The 2026-08-05 ride's unfindability gate keys findability by (verse_id,
position) — the BEFORE db's layout. The PN-star pass legitimately moved names
to their own slots, so every moved member fails positionally even when the
name is perfectly findable at its new slot. This walks EVERY failure:

  leg 1 — the verse is in the plan's write record (or a Cushi verse);
  leg 2 — the name text that sat at the BEFORE slot is now on an is_pn slot
          in the SAME verse of the AFTER db, with a pn_hebrew_xref row.

Both legs -> MOVED-FOUND (geometry-superseded, not a real loss). Anything
else prints in full — real-failure material, HALT.

Usage: python3 scripts/attribute_unfindability.py <before-db> <after-db> \
           <audit-log> plan_pn_star_corrected.txt
Read-only.
"""
import re, sqlite3, sys, collections

NORM = re.compile(r"[^\w]")


def toks(s):
    return [t for t in (NORM.sub("", w).lower() for w in (s or "").split()) if t]


def main():
    before_db, after_db, log, plan = sys.argv[1:5]

    fail_re = re.compile(r"^\s*AFTER \((\d+),(\d+)\):")
    fails = []
    with open(log, encoding="utf-8", errors="replace") as f:
        for ln in f:
            m = fail_re.match(ln)
            if m:
                fails.append((int(m.group(1)), int(m.group(2))))
    print(f"failures parsed from the audit log: {len(fails)}")

    wline = re.compile(r"^\s+([AB])\s+(\S+)\s+(\d+):(\d+)\s+slot\s+(\d+)\s+G\S+\s+.+$")
    plan_verses = set()
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
                    plan_verses.add((m.group(2), int(m.group(3)), int(m.group(4))))

    b = sqlite3.connect("file:%s?mode=ro" % before_db, uri=True)
    a = sqlite3.connect("file:%s?mode=ro" % after_db, uri=True)
    ref = {vid: (bk, ch, vs) for vid, bk, ch, vs in
           a.execute("SELECT id, book, chapter, verse FROM verses")}

    # Identity-level findability (v2 — the position-blind form): a name that
    # was findable BEFORE carried a Hebrew number in the old record; it stays
    # findable iff that number exists somewhere in the SAME verse's NEW record
    # (class A keeps its slot, class B moves — both covered; blank before-
    # cells too, since the match is by number not by text). A before-row with
    # no number never had a findable Hebrew identity — nothing to lose.
    before_heb = {}
    for vid, pos, hb in b.execute(
            "SELECT verse_id, position, hebrew_base FROM pn_greek_identity"):
        before_heb[(vid, pos)] = hb
    after_hebs = collections.defaultdict(set)
    for vid, hb in a.execute(
            "SELECT verse_id, hebrew_base FROM pn_hebrew_xref "
            "WHERE hebrew_base IS NOT NULL"):
        after_hebs[vid].add(hb)

    buckets = collections.Counter()
    residue = []
    for vid, pos in fails:
        vref = ref.get(vid)
        in_plan = vref in plan_verses
        cushi = vref and vref[0] == "2Sa" and vref[1] == 18
        hb = before_heb.get((vid, pos))
        if hb is None:
            found, why = True, "no-number-before"
        elif cushi and hb in ("H3569", "H3570"):
            found, why = ("H3569" in after_hebs.get(vid, set())), "cushi"
        else:
            found, why = (hb in after_hebs.get(vid, set())), "number-in-verse"
        if (in_plan or cushi) and found:
            buckets["MOVED-FOUND (%s)" % why] += 1
        elif in_plan or cushi:
            buckets["MOVED-BUT-NOT-FOUND"] += 1
            residue.append((vid, pos, vref, hb, "not-found"))
        else:
            buckets["OUTSIDE-WRITE-SET"] += 1
            residue.append((vid, pos, vref, hb, "no-plan-verse"))

    print("\nattribution:")
    for k, n in buckets.most_common():
        print("  %6d  %s" % (n, k))
    if residue:
        print("\nRESIDUE (full list — HALT material):")
        for vid, pos, vref, eng, why in residue:
            print("  (%d,%d) %s %r [%s]" % (vid, pos, vref, eng, why))
    sys.exit(1 if residue else 0)


if __name__ == "__main__":
    main()
