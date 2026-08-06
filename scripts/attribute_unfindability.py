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

    # AFTER-side name slots: is_pn words joined to their xref rows, per verse
    after_names = collections.defaultdict(list)
    for vid, pos, eng in a.execute(
            "SELECT w.verse_id, w.position, w.english FROM words w "
            "JOIN pn_hebrew_xref x ON x.verse_id = w.verse_id "
            "AND x.position = w.position WHERE w.is_pn = 1"):
        after_names[vid].append((pos, toks(eng)))

    before_eng = {}
    for vid, pos in fails:
        r = b.execute("SELECT english FROM words WHERE verse_id=? AND position=?",
                      (vid, pos)).fetchone()
        before_eng[(vid, pos)] = r[0] if r else None

    buckets = collections.Counter()
    residue = []
    for vid, pos in fails:
        vref = ref.get(vid)
        in_plan = vref in plan_verses
        cushi = vref and vref[0] == "2Sa" and vref[1] == 18
        name_toks = toks(before_eng.get((vid, pos)))
        found = False
        for apos, atoks in after_names.get(vid, ()):
            if apos != pos and name_toks and all(
                    t in name_toks for t in atoks) and atoks:
                found = True
                break
            # the name may have been merged with a verb BEFORE ('died Saul'):
            # accept when the after-slot's tokens are a subset of the before cell
            if apos != pos and atoks and set(atoks) <= set(name_toks):
                found = True
                break
        if (in_plan or cushi) and found:
            buckets["MOVED-FOUND"] += 1
        elif in_plan or cushi:
            buckets["MOVED-BUT-NOT-FOUND"] += 1
            residue.append((vid, pos, vref, before_eng.get((vid, pos)), "not-found"))
        else:
            buckets["OUTSIDE-WRITE-SET"] += 1
            residue.append((vid, pos, vref, before_eng.get((vid, pos)), "no-plan-verse"))

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
