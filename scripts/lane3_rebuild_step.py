#!/usr/bin/env python3
"""
lane3_rebuild_step.py — /rebuild-words step 8b.2a: re-apply the lane-3 hand repairs on a rebuild
copy and judge the result (CHARTER_rebuild_trap_fix.md G4; JP rulings 2026-10-26).

WHY: the lane-3 repairs (the PN-star merged rows the build's own pass refuses) live only as three
frozen per-row files. A words rebuild does not re-create them, so without this step it silently
REVERTS 16 verses on live (proven 2026-10-26 on a test rebuild: 35 english + 38 greek_pos cells,
plus the gapfix bracket marks).

WHERE: after 8b.2 (retire_hebrew_identity) — Mat 27:26's name number G2424 only returns there, and
fixes2 is pinned to it — and before 8b.3, so the identity and binding builds see the repaired words
(live's identity rows for these slots were built after the repairs).

WHAT: runs scripts/fix_lane3_star_merges.py --apply on the three files in the ledger's order
(docs/audits/LANE3_b2_dispositions.md) and judges each run from its own output:
  lane3_star_fixes.json   9 verses   contiguity FAIL tolerated ONLY on a slot listed in
                                     lane3_star_gapfix.json (same verse, same position, the
                                     bracket gapfix sets there) — read at run time
  lane3_star_gapfix.json  6 verses   must then PASS contiguity on every verse fixes failed
                                     (4 lane-3 verses + 2Sa 18:31/32, added 2026-10-26)
  lane3_star_fixes2.json  7 verses   strict
Each file passes only when: its count line shows all N patched (first run) or all N already
applied (re-run), 0 skipped; no SKIP line; every render check PASS; contiguity as above. A mix
of patched and already-applied fails. Prints "LANE-3 STEP: PASS" or "LANE-3 STEP: FAIL" and exits
0 / 1. Refuses the live database — it runs on rebuild copies only.

  python3 scripts/lane3_rebuild_step.py ~/bible-db/bible_test.db
"""
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

FILES = (("lane3_star_fixes.json", 9), ("lane3_star_gapfix.json", 6), ("lane3_star_fixes2.json", 7))
FIXES, GAPFIX, FIXES2 = (f for f, _ in FILES)

_VERSE = re.compile(r"^=== (.+?) === \(")
_RENDER = re.compile(r"render check: .* -> (PASS|FAIL)")
_CONTIG = re.compile(r"contiguity check: (PASS|FAIL (\[.*\]))")
_ALREADY = re.compile(r"^ALREADY (.+?): already applied")
_SKIP = re.compile(r"^SKIP (.+?):")
_COUNT = re.compile(r"^APPLIED — (\d+) verse\(s\) patched, (\d+) already applied, (\d+) skipped")


def gapfix_slots(path=HERE / GAPFIX):
    """verse -> {(bracket_id, position)} the gapfix file sets — the only contiguity gaps the
    fixes file may leave behind."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    d.pop("_comment", None)
    return {v: {(op["new_bid"], op["pos"]) for op in s["ops"]} for v, s in d.items()}


def parse(out):
    """The script's output -> dict(count=(patched, already, skipped) or None, skips, already,
    render_fail, contig: {verse: [(bid, pos), ...] (empty = PASS)})."""
    res = dict(count=None, skips=[], already=[], render_fail=[], contig={})
    verse = None
    for line in out.splitlines():
        m = _VERSE.match(line)
        if m:
            verse = m.group(1)
            continue
        m = _ALREADY.match(line)
        if m:
            res["already"].append(m.group(1))
            continue
        m = _SKIP.match(line)
        if m:
            res["skips"].append(m.group(1))
            continue
        m = _RENDER.search(line)
        if m and m.group(1) == "FAIL":
            res["render_fail"].append(verse)
        m = _CONTIG.search(line)
        if m:
            res["contig"][verse] = [] if m.group(1) == "PASS" else \
                [tuple(t) for t in ast.literal_eval(m.group(2))]
        m = _COUNT.match(line)
        if m:
            res["count"] = tuple(int(x) for x in m.groups())
    return res


def judge(outputs, gaps):
    """outputs: {file: script output}; gaps: gapfix_slots(). -> (ok, [problem lines])."""
    probs = []
    parsed = {f: parse(outputs.get(f, "")) for f, _ in FILES}
    for f, n in FILES:
        p = parsed[f]
        if p["count"] is None:
            probs.append(f"{f}: no APPLIED count line (did it run with --apply?)")
            continue
        patched, already, skipped = p["count"]
        if skipped or p["skips"]:
            probs.append(f"{f}: {skipped} skipped {p['skips']}")
        if (patched, already) not in ((n, 0), (0, n)):
            probs.append(f"{f}: {patched} patched + {already} already applied — need all {n} "
                         f"patched OR all {n} already applied (a mix fails)")
        if p["render_fail"]:
            probs.append(f"{f}: render check FAIL in {p['render_fail']}")
    tolerated = set()
    for verse, bad in parsed[FIXES]["contig"].items():
        for slot in bad:
            if slot in gaps.get(verse, set()):
                tolerated.add(verse)
            else:
                probs.append(f"{FIXES}: contiguity FAIL {verse} {slot} is not a gapfix slot")
    gap_contig = parsed[GAPFIX]["contig"]
    for verse in sorted(tolerated):
        if gap_contig.get(verse) != []:
            probs.append(f"{GAPFIX}: {verse} must PASS contiguity after fixes failed it "
                         f"(got {gap_contig.get(verse, 'no check printed')})")
    for verse, bad in gap_contig.items():
        if bad and verse not in tolerated:
            probs.append(f"{GAPFIX}: contiguity FAIL {verse} {bad}")
    for verse, bad in parsed[FIXES2]["contig"].items():
        if bad:
            probs.append(f"{FIXES2}: contiguity FAIL {verse} {bad} (strict)")
    return not probs, probs


def main(argv=None):
    from dryrun_rekey_fill import is_live          # the ONE live-path gate
    args = argv if argv is not None else sys.argv[1:]
    dbs = [a for a in args if not a.startswith("--")]
    if len(dbs) != 1:
        sys.exit("usage: lane3_rebuild_step.py <rebuild-copy.db>")
    db = dbs[0]
    if is_live(db):
        print(f"LANE-3 STEP: REFUSED — {db} is the live database (or a file named bible.db). "
              "This step runs on rebuild copies only.")
        return 1
    outputs = {}
    for f, _ in FILES:
        p = subprocess.run([sys.executable, str(HERE / "fix_lane3_star_merges.py"), db, "--apply",
                            "--fixes", f], capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        print(f"\n── fix_lane3_star_merges.py --fixes {f} ──")
        print(p.stdout.rstrip())
        if p.returncode:
            print(p.stderr.rstrip())
            print(f"LANE-3 STEP: FAIL — {f} exited {p.returncode}")
            return 1
        outputs[f] = p.stdout
    ok, probs = judge(outputs, gapfix_slots())
    print()
    for line in probs:
        print(f"  !! {line}")
    counts = " · ".join(f"{f.replace('lane3_star_', '').replace('.json', '')} "
                        f"{parse(outputs[f])['count']}" for f, _ in FILES)
    print(f"LANE-3 STEP: {'PASS' if ok else 'FAIL'}  (patched, already, skipped per file: {counts})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
