import os, sqlite3, sys
H, plant = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "none")
os.makedirs(H + "/bible-db", exist_ok=True); os.makedirs(H + "/edition_upgrade_runs/p4_live_tables_20261121", exist_ok=True)
SCH = ("CREATE TABLE abp_corrections (id INTEGER PRIMARY KEY, book TEXT NOT NULL, chapter INTEGER NOT NULL, verse INTEGER NOT NULL,"
       " position INTEGER NOT NULL, field TEXT NOT NULL, source_value TEXT, corrected_value TEXT, reason TEXT NOT NULL, ledger_ref TEXT,"
       " applied_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active', created TEXT NOT NULL)")
def mk(p, rows, sch=SCH):
    if os.path.exists(p): os.remove(p)
    c = sqlite3.connect(p); c.execute(sch)
    for r in rows: c.execute("INSERT INTO abp_corrections VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", r)
    c.commit(); c.close()
def row(i, st): return (i, "Gen", 1, i, 2, "english", "SECRET-SRC", "SECRET-COR", "SECRET-REASON", "L%d" % i, "ingest", st, "2026")
live = [row(i, "active") for i in range(1, 6)]
src = [row(1, "active"), row(2, "retired"), row(3, "retired"), row(4, "active"), row(5, "active")] + [row(i, "active") for i in (6, 7, 8)]
mk(H + "/edition_upgrade_runs/p4_live_tables_20261121/live_copy_20261121.db", live)
mk(H + "/bible-db/bible_edupg_test_20261101.db", src)
if plant == "nocol":
    mk(H + "/bible-db/bible_edupg_test_built_20261102.db", [], "CREATE TABLE abp_corrections (id INTEGER PRIMARY KEY, book TEXT)")
else:
    mk(H + "/bible-db/bible_edupg_test_built_20261102.db", src + [row(9, "active")])
