#!/usr/bin/env python3
"""
audit_abp_tab_bridge.py — READ-ONLY census for the ABP-tab routing lane
(docs/handoffs/HANDOFF_abp_tab_routing.md, charter docs/tickets/CHARTER_abp_tab_routing.md).

THE QUESTION: for every Greek Strong's number whose Word-study ABP tab greys today
(the production `has_abp` predicate finds no words row), is there a FOLDED Greek
header in pn_greek_identity that the number's dictionary lemma reaches — so the
tab can honestly open the name's ABP occurrences with the FULL count?

Bridge key = the lexicon's `lemma_plain` fold (production `_norm_lemma`) applied
to the stored header. Classes, per greyed number:

  BRIDGE-SURFACE   the fold reaches rows whose source is 'surface' (one disciplined
                   header per name — the folding the header arc landed). Routable.
                   Reported with the count and the number of DISTINCT stored values
                   that fold to the key (>1 = the 13-of-73 trap is still live there).
  LEMMA-ONLY-ONLY  the fold reaches ONLY 'lemma-only' rows (per-verse printed forms:
                   UNRESOLVED names, or a real dictionary lemma). A one-form count
                   here is the trap the lane exists to avoid — NOT routable as a total.
  NONE             nothing folds to the key — the tab stays grey, honestly.

Cross-checks (each a finding if non-zero, never silently absorbed):
  MIXED      numbers whose ABP tab already OPENS but which ALSO own numberless
             surface rows folding to their lemma — today's count is a short count.
  COLLISION  one folded header key reached by MORE THAN ONE lexicon number
             (homographs) — the bridge must not hand two numbers the same rows
             without saying so.

CONTROLS (detector-must-fire, feedback_audit_tools_must_fail):
  * live db: G1056 galilee must land BRIDGE-SURFACE, 1 stored value, 73 rows.
  * pre-fold db (the 9/6 pre-swap backup, header NOT yet folded): G1056 must land
    LEMMA-ONLY-ONLY with 6 stored values (13 under Γαλιλαία). Same script, both
    runs — if the pre-fold run does not fire, the classifier is not measuring
    what it claims.
  * Hebrew-keyed names route through h_abp_predicate already (no G-number):
    H1908 hadad and H52 abishai counts are printed for the served check set.

READ-ONLY. Run on PA (venv):
  PYTHONIOENCODING=utf-8 python3 ~/bible-db/scripts/audit_abp_tab_bridge.py ~/bible-db/bible.db
  PYTHONIOENCODING=utf-8 python3 ~/bible-db/scripts/audit_abp_tab_bridge.py <pre-fold copy>
Options: --show N  (members listed per class, default 12)  --number G1056 (one number, full detail)
"""
import argparse
import os
import sqlite3
import sys
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from views_lexicon import _abp_strongs_filter, _norm_lemma  # production code, never a copy
from core import h_abp_predicate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--show", type=int, default=12)
    ap.add_argument("--number", default=None, help="one G-number (e.g. G1056): full detail only")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    have = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for t in ("lexicon", "words", "pn_greek_identity", "verses", "kjv_strongs"):
        if t not in have:
            print(f"ABORT: table {t} missing — not the db this audit expects")
            return 2
    has_lp = "lemma_plain" in {r[1] for r in conn.execute("PRAGMA table_info(lexicon)")}
    print(f"db: {a.db}   lexicon.lemma_plain column: {'present' if has_lp else 'ABSENT (folding in Python)'}")

    # ── numberless identity rows, grouped by folded key → {stored value: {source: count}}
    fold = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    n_null = 0
    for r in conn.execute("SELECT greek_lemma, source, count(*) AS c FROM pn_greek_identity "
                          "WHERE greek_strongs IS NULL AND greek_lemma IS NOT NULL AND greek_lemma != '' "
                          "GROUP BY greek_lemma, source"):
        fold[_norm_lemma(r["greek_lemma"])][r["greek_lemma"]][r["source"]] += r["c"]
        n_null += r["c"]
    print(f"numberless identity rows with a Greek header: {n_null:,}  distinct folded keys: {len(fold):,}")

    def describe(key):
        vals = fold.get(key, {})
        surf = sum(c for v in vals.values() for s, c in v.items() if s == "surface")
        lo = sum(c for v in vals.values() for s, c in v.items() if s == "lemma-only")
        n_vals = len(vals)
        return surf, lo, n_vals, vals

    # ── every lexicon G-number: greyed or not under the PRODUCTION predicate
    rows = conn.execute("SELECT strongs, lemma" + (", lemma_plain" if has_lp else "") +
                        " FROM lexicon WHERE lemma IS NOT NULL AND lemma != ''").fetchall()
    numbers = []
    if a.number:
        want = a.number.upper().lstrip("G")
        rows = [r for r in rows if r["strongs"] == want]
        if not rows:
            print(f"{a.number}: not in lexicon"); return 1
    classes = defaultdict(list)
    mixed, key_owner = [], defaultdict(list)
    for r in rows:
        num = r["strongs"]; sid = f"G{num}"
        key = (r["lemma_plain"] if has_lp and r["lemma_plain"] else _norm_lemma(r["lemma"]))
        pred, params = _abp_strongs_filter(conn, num, sid)
        opens = conn.execute(f"SELECT 1 FROM words w WHERE {pred} LIMIT 1", params).fetchone() is not None
        surf, lo, n_vals, vals = describe(key)
        in_kjv = conn.execute("SELECT 1 FROM kjv_strongs WHERE strongs_id = ? LIMIT 1", (sid,)).fetchone() is not None
        rec = (sid, r["lemma"], key, surf, lo, n_vals, in_kjv, vals)
        if surf or lo:
            key_owner[key].append(sid)
        if opens:
            if surf:
                mixed.append(rec)
            continue
        if surf:
            classes["BRIDGE-SURFACE"].append(rec)
        elif lo:
            classes["LEMMA-ONLY-ONLY"].append(rec)
        else:
            classes["NONE"].append(rec)

    def line(rec, full=False):
        sid, lemma, key, surf, lo, n_vals, in_kjv, vals = rec
        s = (f"  {sid:7} {lemma:18} surface={surf:<5} lemma-only={lo:<5} stored-values={n_vals} "
             f"{'kjv' if in_kjv else 'no-kjv'}")
        if full or n_vals > 1:
            s += "\n" + "\n".join(f"      {v!r}: " + ", ".join(f"{src}×{c}" for src, c in srcs.items())
                                  for v, srcs in vals.items())
        return s

    if a.number:
        rec = (classes["BRIDGE-SURFACE"] + classes["LEMMA-ONLY-ONLY"] + classes["NONE"] + mixed)
        print(("OPENS today" if rec and rec[0] in mixed else "") )
        for c, lst in classes.items():
            if lst: print(f"class: {c}")
        for x in rec: print(line(x, full=True))
        return 0

    n_grey = sum(len(v) for v in classes.values())
    print(f"\nGreek numbers in lexicon: {len(rows):,}   greyed ABP tab today: {n_grey:,}   "
          f"(of which KJV-tagged, i.e. reachable from a KJV click: "
          f"{sum(1 for v in classes.values() for x in v if x[6]):,})")
    for c in ("BRIDGE-SURFACE", "LEMMA-ONLY-ONLY", "NONE"):
        lst = classes[c]
        multi = sum(1 for x in lst if x[5] > 1)
        print(f"\n== {c}: {len(lst):,} numbers" + (f"  (stored-values>1: {multi})" if c != "NONE" else ""))
        for x in sorted(lst, key=lambda t: -(t[3] + t[4]))[:a.show]:
            print(line(x))
    print(f"\n== MIXED (tab opens today but numberless surface rows also fold to its lemma): {len(mixed):,}")
    for x in sorted(mixed, key=lambda t: -t[3])[:a.show]:
        print(line(x))
    coll = {k: v for k, v in key_owner.items() if len(v) > 1}
    print(f"\n== COLLISION (one folded header key, >1 lexicon number): {len(coll):,}")
    for k, v in list(coll.items())[:a.show]:
        print(f"  {k!r}: {' '.join(v)}")

    # ── controls
    print("\n== CONTROLS")
    g = [x for x in classes["BRIDGE-SURFACE"] if x[0] == "G1056"]
    l = [x for x in classes["LEMMA-ONLY-ONLY"] if x[0] == "G1056"]
    if g:
        print(f"  G1056 galilee: BRIDGE-SURFACE surface={g[0][3]} stored-values={g[0][5]}  "
              f"{'PIN OK (73, 1)' if (g[0][3], g[0][5]) == (73, 1) else 'PIN FAIL — STOP'}")
    elif l:
        print(f"  G1056 galilee: LEMMA-ONLY-ONLY lemma-only={l[0][4]} stored-values={l[0][5]}  "
              f"(pre-fold picture: expect 73 rows across 6 values; on LIVE this is a STOP)")
        print(line(l[0], full=True))
    else:
        print("  G1056 galilee: NOT FOUND in any greyed class — classifier did not fire; STOP")
    for sid, nm in (("G4622", "zion"),):
        for c, lst in classes.items():
            for x in lst:
                if x[0] == sid: print(f"  {sid} {nm}: {c} " + line(x).strip())
        for x in mixed:
            if x[0] == sid: print(f"  {sid} {nm}: MIXED " + line(x).strip())
    for hid, nm in (("H1908", "hadad"), ("H52", "abishai")):
        p, pp = h_abp_predicate(conn, hid)
        n = conn.execute(f"SELECT count(*) FROM words w WHERE {p}", pp).fetchone()[0]
        print(f"  {hid} {nm}: ABP rows via the production Hebrew predicate = {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
