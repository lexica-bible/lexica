#!/usr/bin/env python3
"""gate_stage2_counts.py — R-2 stage 2 count-trace GATE (ruling S2-Q4, control C6).

After the reader flip, some ABP proper-noun cards show a DIFFERENT occurrence
count: the line now counts what actually shares the Greek identity, not the
Hebrew stopgap number. That change is the feature — but ONLY when it traces to
the stage-1 two-derivations report. This script itemizes every changed count and
matches each against that report; any change the report does not explain is a
bug and the gate FAILS.

Read-only. Run on PA after the flip (and before the ON-receipt):

    python3 scripts/gate_stage2_counts.py ~/bible-db/bible.db ~/r2s1_deriv_diff.txt

Self-test (the audit-tools-must-fail rule — prove the detector fires before
trusting a zero):

    python3 scripts/gate_stage2_counts.py ~/bible-db/bible.db ~/r2s1_deriv_diff.txt --selftest
"""
import re
import sqlite3
import sys
from collections import defaultdict

if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(2)
DB, REPORT = sys.argv[1], sys.argv[2]
SELFTEST = "--selftest" in sys.argv[3:]

# ── the pre-declared expectation sheet: parse the stage-1 report ────────────
# Full-listing line shape (audit_two_derivations.py):
#   H8646 | 14 | G2291[12], NO-NUMBER[2] | agree
LINE = re.compile(r"^(H\d[\d.]*[a-z]?) \| (\d+) \| (.+) \| ")
TOK = re.compile(r"(G\d[\d.]*|NO-NUMBER)\[(\d+)\]")

expect = {}   # hebrew_base -> (hebrew_count, {greek_or_None: n})
with open(REPORT, encoding="utf-8", errors="replace") as fh:
    for raw in fh:
        m = LINE.match(raw.strip())
        if not m:
            continue
        hb, hn, gtxt = m.group(1), int(m.group(2)), m.group(3)
        gmaps = {(g if g != "NO-NUMBER" else None): int(n)
                 for g, n in TOK.findall(gtxt)}
        expect[hb] = (hn, gmaps)   # duplicate lines (top + full listing) agree
if not expect:
    print(f"GATE FAIL: no parsable lines in {REPORT} — wrong file?")
    sys.exit(1)
print(f"expectation sheet: {len(expect):,} Hebrew numbers from {REPORT}")

# ── the live derivations, recomputed the same two ways ──────────────────────
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
live_heb = {r["strongs_base"]: r["n"] for r in conn.execute(
    "SELECT strongs_base, count(*) AS n FROM words "
    "WHERE is_pn=1 AND strongs_base LIKE 'H%' GROUP BY strongs_base")}
live_pairs = defaultdict(dict)
for r in conn.execute(
        "SELECT hebrew_base, greek_strongs, count(*) AS n FROM pn_greek_identity "
        "WHERE hebrew_base IS NOT NULL GROUP BY hebrew_base, greek_strongs"):
    live_pairs[r["hebrew_base"]][r["greek_strongs"]] = r["n"]

if SELFTEST:
    # Known positive: perturb one live count in memory; the gate MUST flag it.
    victim = next(iter(live_pairs))
    k = next(iter(live_pairs[victim]))
    live_pairs[victim][k] += 1
    print(f"[selftest] perturbed {victim}/{k or 'NO-NUMBER'} by +1 — expecting FAIL")

# The count the flipped card actually SERVES for a numbered identity: the global
# by-Greek-number total (helper counts pn_greek_identity by greek_strongs alone —
# it legitimately includes NT abp-tag rows that carry no Hebrew base, e.g. Θάρα
# in Luke 3:34 joining Terah's OT rows).
served = defaultdict(int)
for r in conn.execute(
        "SELECT greek_strongs, count(*) AS n FROM pn_greek_identity "
        "WHERE greek_strongs IS NOT NULL GROUP BY greek_strongs"):
    served[r["greek_strongs"]] = r["n"]

# ── the trace ───────────────────────────────────────────────────────────────
# Two parts. (1) HARD MATCH: the live pair-level derivation must equal the report
# exactly — that proves the stage-1 certified state is what's serving. Any
# mismatch is unexplained -> FAIL. (2) ITEMIZED DIFF: every card whose count line
# changes (old Hebrew-keyed count -> served Greek-keyed count) is printed with
# its decomposition, so the reviewer reads the change against the report line.
changed, unexplained = [], []
for hb in sorted(set(live_heb) | set(live_pairs), key=lambda s: (len(s), s)):
    hn = live_heb.get(hb, 0)
    gmaps = live_pairs.get(hb, {})
    exp = expect.get(hb)
    if exp is None:
        unexplained.append(f"{hb}: live ({hn} heb / {gmaps}) — NOT IN the report")
        continue
    ehn, egmaps = exp
    if hn != ehn or gmaps != egmaps:
        unexplained.append(
            f"{hb}: live heb={hn} maps={gmaps}  vs report heb={ehn} maps={egmaps}")
        continue
    for g, n in sorted(gmaps.items(), key=lambda kv: -kv[1]):
        if g is None:
            continue
        if served[g] != hn:   # the card line changes for words riding this pair
            extra = served[g] - n
            changed.append(
                f"{hb}: card line {hn} -> {served[g]}  "
                f"({n} via this Hebrew number in the report line"
                + (f" + {extra} sharing {g} from elsewhere (NT/abp-tag or another base)"
                   if extra else "") + ")")

print(f"\ncards whose ABP count line changes under the flip: {len(changed):,} "
      f"— each itemized against its report line:")
for line in changed[:200]:
    print("  " + line)
if len(changed) > 200:
    print(f"  … {len(changed) - 200} more")
t = expect.get("H8646")
print(f"C6 exemplar Terah H8646: report says {t}" if t else
      "C6 exemplar Terah H8646: NOT in report — check before receipt")

if SELFTEST:
    if unexplained:
        print(f"\nSELFTEST PASS — the detector fired on the known positive "
              f"({len(unexplained)} flagged).")
        sys.exit(0)
    print("\nSELFTEST FAIL — the perturbation was NOT caught; the detector is "
          "blind. Do not trust a PASS from this gate until fixed.")
    sys.exit(1)
if unexplained:
    print(f"\nGATE FAIL — {len(unexplained)} unexplained count(s):")
    for line in unexplained[:50]:
        print("  " + line)
    if len(unexplained) > 50:
        print(f"  … {len(unexplained) - 50} more")
    sys.exit(1)
print("\nGATE PASS — zero unexplained changed counts.")
sys.exit(0)
