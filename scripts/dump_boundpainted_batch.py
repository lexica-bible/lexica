#!/usr/bin/env python3
"""dump_boundpainted_batch.py — READ-ONLY evidence dump for the bound-painted
audit lane (TICKET_bound_painted_audit.md). For each worklist group in the
requested batch, prints everything adjudication needs:

  - the verse's clean prose (verses.text),
  - each listed slot's words row (position, english, english_head, strongs) —
    the stale-name guard input,
  - every pn_binding render row at the verse whose name compact-matches the
    group name (the paint under audit) — with the bound entity + its TIPNR
    referent kind,
  - any existing pn_slot_binding rows at those positions (precedence guard),
  - the MANDATORY near-match candidate roster for the name:
    exact / prefix / SequenceMatcher ratio >= 0.80 over tipnr_entities
    (person AND place/other sections) and metav_people (+aliases) —
    never exact-only (the 4-miss lesson).

Usage: python3 scripts/dump_boundpainted_batch.py [bible.db] --batch 1 [--size 100]
Batch N = worklist lines (N-1)*size+1 .. N*size, in file order. READ-ONLY.
"""
import sys, os, re, sqlite3, argparse
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import entity_resolution as er

ap = argparse.ArgumentParser()
ap.add_argument("db", nargs="?", default="bible.db")
ap.add_argument("--batch", type=int, required=True)
ap.add_argument("--size", type=int, default=100)
args = ap.parse_args()

WORKLIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                        "docs", "tickets", "boundpainted_worklist_20260808.txt")
rows = []
with open(WORKLIST, encoding="utf-8") as f:
    for line in f:
        if line.startswith("#") or not line.strip():
            continue
        m = re.match(r"\s*(\S+)\s+(\d+):(\d+)\s+(\S+)\s+p\[([0-9, ]+)\]", line)
        if not m:
            print(f"UNPARSEABLE WORKLIST LINE (stop and look): {line.rstrip()}")
            sys.exit(2)
        ab, ch, vs, nm, ps = m.groups()
        rows.append((ab, int(ch), int(vs), nm, [int(x) for x in ps.split(",")]))

lo, hi = (args.batch - 1) * args.size, args.batch * args.size
batch = rows[lo:hi]
if not batch:
    print(f"batch {args.batch} empty (worklist has {len(rows)} groups)")
    sys.exit(2)

conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

def compact(s):
    return (s or "").replace("-", "").replace(" ", "")

def roster(name):
    """Near-match candidate roster: exact/prefix/ratio>=0.80, never exact-only."""
    out = []
    for r in conn.execute("SELECT uniq, head, section FROM tipnr_entities"):
        h = (r["head"] or "").lower()
        if not h:
            continue
        if h == name or h.startswith(name) or name.startswith(h) \
           or SequenceMatcher(None, h, name).ratio() >= 0.80:
            out.append(f"TIPNR {r['section']:6s} {r['uniq']}")
    for r in conn.execute("SELECT person_id, name FROM metav_people"):
        h = (r["name"] or "").lower()
        if h == name or h.startswith(name) or name.startswith(h) \
           or SequenceMatcher(None, h, name).ratio() >= 0.80:
            out.append(f"metav person {r['person_id']} {r['name']}")
    for r in conn.execute("SELECT person_id, alias FROM metav_people_aliases"):
        h = (r["alias"] or "").lower()
        if h == name or h.startswith(name) or name.startswith(h) \
           or SequenceMatcher(None, h, name).ratio() >= 0.80:
            out.append(f"metav alias  {r['person_id']} {r['alias']}")
    return out

print(f"═══ BOUND-PAINTED BATCH {args.batch} (groups {lo+1}-{lo+len(batch)} of {len(rows)}) ═══")
for ab, ch, vs, nm, ps in batch:
    bk = er.book_num(ab)
    v = conn.execute("SELECT id, text FROM verses WHERE book=? AND chapter=? AND verse=?",
                     (ab, ch, vs)).fetchone()
    print(f"\n── {ab} {ch}:{vs}  {nm}  p{ps} " + "─" * 30)
    if not v:
        print("  !! NO VERSE ROW (stop and look)")
        continue
    print(f"  prose: {v['text']}")
    for p in ps:
        w = conn.execute("SELECT position, english, english_head, strongs FROM words "
                         "WHERE verse_id=? AND position=?", (v["id"], p)).fetchone()
        if w:
            print(f"  slot p{w['position']:3d}: english={w['english']!r} "
                  f"head={w['english_head']!r} strongs={w['strongs']}")
        else:
            print(f"  slot p{p:3d}: !! NO WORDS ROW (stop and look)")
    cn = compact(nm)
    binds = [b for b in conn.execute(
        "SELECT name, entity_uniq, render FROM pn_binding WHERE book=? AND chapter=? AND verse=? AND render=1",
        (bk, ch, vs)) if compact(b["name"]) == cn]
    if not binds:
        print("  !! NO MATCHING RENDER BIND (census said one exists — stop and look)")
    for b in binds:
        kind = conn.execute("SELECT section FROM tipnr_entities WHERE uniq=?",
                            (b["entity_uniq"],)).fetchone()
        print(f"  PAINT: bind name={b['name']!r} -> {b['entity_uniq']} "
              f"(referent kind: {kind['section'] if kind else 'NOT IN TIPNR'})")
    for s in conn.execute(
        "SELECT position, entity_uniq, name FROM pn_slot_binding WHERE book=? AND chapter=? AND verse=?",
        (bk, ch, vs)):
        flag = " <== ON A LISTED SLOT (precedence!)" if s["position"] in ps else ""
        print(f"  slot-bind exists: p{s['position']} {s['name']} -> {s['entity_uniq']}{flag}")
    print("  roster:")
    for line in roster(nm) or ["  (EMPTY — stop and look, roster may not be empty)"]:
        print(f"    {line}")
