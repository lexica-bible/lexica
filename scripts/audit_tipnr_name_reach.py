#!/usr/bin/env python3
"""audit_tipnr_name_reach.py — READ-ONLY diagnosis (Part 1 of the slim-card build):
why does a by-name TIPNR person lookup find Elijah (4 entities) but not Elisha (0)?

For each top-20 bio-bar name (the slim-card population) this prints every
tipnr_entities row reachable under three widening match tiers:
    T1 exact   head = name OR uniq LIKE 'name@%'   (the current lookup)
    T2 compact same, hyphen/space-blind on both sides
    T3 loose   uniq LIKE 'name%' (catches 'Elisha_1@…' / suffixed keys)
plus, if all three miss, a substring probe (uniq LIKE '%name%') so a differently-
spelled head still surfaces for the eyeball.

Output per name: tier that first hits, entity count at that tier, and each row's
uniq | section | descr (first 60 chars). The fix design reads straight off which
tier is needed and whether the hit is unique.

Control: Elijah must hit at T1 with >0 rows (tonight's known positive), and Paul
must hit at T1 with exactly 1 — aborts otherwise.

READ-ONLY. Usage: python3 scripts/audit_tipnr_name_reach.py [bible.db]
"""
import sys, sqlite3

DB = sys.argv[1] if len(sys.argv) > 1 else "bible.db"
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

NAMES = ["Paul", "Elisha", "Nebuchadnezzar", "Balaam", "Balak", "Pilate",
         "Esther", "Sihon", "Jephthah", "Jonah", "Nabal", "Timothy", "Cyrus",
         "Hazael", "Achish", "Og", "Ahithophel", "Naboth", "Manoah", "Silas",
         "Elijah"]   # Elijah rides along as the T1 control

def rows_at(sql, params):
    return conn.execute(sql, params).fetchall()

def probe(name):
    cn = name.replace("-", "").replace(" ", "")
    tiers = [
        ("T1-exact", "SELECT uniq, section, descr FROM tipnr_entities "
                     "WHERE head = ? COLLATE NOCASE OR uniq LIKE ?",
         (name, name + "@%")),
        ("T2-compact", "SELECT uniq, section, descr FROM tipnr_entities "
                       "WHERE REPLACE(REPLACE(head,'-',''),' ','') = ? COLLATE NOCASE "
                       "OR REPLACE(REPLACE(uniq,'-',''),' ','') LIKE ?",
         (cn, cn + "@%")),
        ("T3-loose", "SELECT uniq, section, descr FROM tipnr_entities "
                     "WHERE uniq LIKE ? COLLATE NOCASE", (name + "%",)),
        ("T4-substring", "SELECT uniq, section, descr FROM tipnr_entities "
                         "WHERE uniq LIKE ? COLLATE NOCASE LIMIT 8", ("%" + name + "%",)),
    ]
    for tier, sql, params in tiers:
        got = rows_at(sql, params)
        if got:
            return tier, got
    return "MISS", []

results = {}
for nm in NAMES:
    results[nm] = probe(nm)

t, got = results["Elijah"]
ok1 = t == "T1-exact" and len(got) > 0
t, got = results["Paul"]
ok2 = t == "T1-exact" and len(got) == 1
if not (ok1 and ok2):
    print(f"CONTROL FAILED: Elijah T1>0 ({ok1}) / Paul T1==1 ({ok2}) — probe logic wrong, output untrustworthy.")
    sys.exit(1)
print("controls OK (Elijah hits T1 with rows; Paul hits T1 with exactly 1)\n")

print(f"{'name':16s} {'first-hit tier':14s} {'rows':>4s}")
for nm in NAMES:
    tier, got = results[nm]
    print(f"{nm:16s} {tier:14s} {len(got):4d}")
    for g in got[:6]:
        d = (g["descr"] or "").replace("\n", " ")[:60]
        print(f"    {g['uniq']} | {g['section']} | {d}")
