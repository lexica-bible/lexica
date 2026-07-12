#!/usr/bin/env python3
"""audit_pn_fallback_size.py — READ-ONLY sizing of the 'Jacob class':
proper-noun word occurrences with NO verse-bound entity whose name is
ambiguous in metaV (several people share it), so the reader gets only the
AI-summary fallback card (Gen 29:32 'Jacob' being the found case).

Uses the SAME normalization as the binding build (entity_resolution.norm_name
/ book_num), so word rows and pn_binding rows actually line up.

Control (certification rule): Judah @ Jer 36:1 is a KNOWN bound occurrence —
if the matcher doesn't see it as covered, the tool aborts instead of reporting.

Usage: python3 scripts/audit_pn_fallback_size.py [bible.db]
"""
import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import entity_resolution as er

DB = sys.argv[1] if len(sys.argv) > 1 else "bible.db"
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

# bound (book,ch,vs,name) set, render rows only
bound = {(r["book"], r["chapter"], r["verse"], r["name"]) for r in
         conn.execute("SELECT book, chapter, verse, name FROM pn_binding WHERE render=1")}

# ambiguous person names, normalized like the build (incl. aliases)
from collections import defaultdict
person_ids = defaultdict(set)
for r in conn.execute("SELECT person_id, name FROM metav_people WHERE name IS NOT NULL"):
    person_ids[er.norm_name(r["name"])].add(r["person_id"])
for r in conn.execute("SELECT person_id, alias FROM metav_people_aliases WHERE alias IS NOT NULL"):
    person_ids[er.norm_name(r["alias"])].add(r["person_id"])
ambiguous = {n for n, ids in person_ids.items() if len(ids) > 1}

total = covered = jacob_class = 0
jacob_names = defaultdict(int)
control_hit = False
for r in conn.execute("""
    SELECT v.book AS book, v.chapter AS ch, v.verse AS vs,
           COALESCE(NULLIF(w.english_head,''), w.english) AS label
    FROM words w JOIN verses v ON v.id = w.verse_id
    WHERE w.is_pn = 1"""):
    nm = er.norm_name(r["label"])
    bk = er.book_num(r["book"])
    if not nm or bk is None:
        continue
    total += 1
    if (bk, r["ch"], r["vs"], nm) in bound:
        covered += 1
        if nm == "judah" and bk == er.book_num("Jer") and r["ch"] == 36 and r["vs"] == 1:
            control_hit = True
    elif nm in ambiguous:
        jacob_class += 1
        jacob_names[nm] += 1

if not control_hit:
    print("CONTROL FAILED: Judah @ Jer 36:1 not seen as covered - matcher is broken, numbers below NOT trustworthy.")
    sys.exit(1)

print(f"control OK (Judah @ Jer 36:1 covered)")
print(f"name-word occurrences : {total:,}")
print(f"covered by a bind     : {covered:,}")
print(f"jacob-class (unbound + ambiguous name -> AI-only card): {jacob_class:,}")
print("\ntop 20 jacob-class names:")
for nm, n in sorted(jacob_names.items(), key=lambda kv: -kv[1])[:20]:
    print(f"  {nm:20s} {n:,}")
