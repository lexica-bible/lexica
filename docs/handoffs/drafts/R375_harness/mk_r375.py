import os, sqlite3, sys, shutil
H, plant = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "none")
os.makedirs(H + "/bible-db/tests/fixtures/corrections", exist_ok=True); os.makedirs(H + "/edition_upgrade_runs", exist_ok=True)
dst = H + "/bible-db/tests/fixtures/corrections/abp_corrections_active_built_20261106.txt"   # the clone's own committed file (d34d6723)
F = dst
if plant == "oldfile":
    open(dst, "a").write("Gen\t1\t1\t1\tenglish\tX\n")
keys = [l.rstrip("\n").split("\t") for l in open(F, encoding="utf-8") if l.strip()]
keys.append(["Joh", "19", "18", "10", "english_head", "EU-Joh19:18"])
if plant == "extra":
    keys.append(["Gen", "1", "1", "2", "english", "ZZ"])
b = H + "/bible-db/bible_edupg_test_built_20261102.db"
c = sqlite3.connect(b)
c.execute("CREATE TABLE abp_corrections (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, position INT, field TEXT, source_value TEXT, corrected_value TEXT, reason TEXT, ledger_ref TEXT, applied_at TEXT, status TEXT, created TEXT)")
for i, k in enumerate(keys):
    c.execute("INSERT INTO abp_corrections VALUES (NULL,?,?,?,?,?,'s','c','r',?,'ingest','active','2026')", (k[0], int(k[1]), int(k[2]), int(k[3]), k[4], k[5]))
for i in range(23 if plant != "retired" else 22):
    c.execute("INSERT INTO abp_corrections VALUES (NULL,'Exo',1,?,1,'english','s','c','r','R','ingest','retired','2026')", (i,))
for i in range(6):
    c.execute("INSERT INTO abp_corrections VALUES (NULL,'2Sa',18,?,1,'strongs_base','s','c','r','C','ingest','superseded','2026')", (i,))
c.commit(); c.close()
