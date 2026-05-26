import sqlite3

src = sqlite3.connect('APBStrongs.dcti')
dst = sqlite3.connect('bible.db')

dst.execute('''CREATE TABLE IF NOT EXISTS abp_ext (
    strongs TEXT PRIMARY KEY,
    def_html TEXT,
    summary_json TEXT,
    abp_summary_v INTEGER
)''')

rows = src.execute("SELECT Topic, Definition FROM Dictionary WHERE Topic LIKE 'G%'").fetchall()
dst.executemany("INSERT OR REPLACE INTO abp_ext(strongs, def_html) VALUES (?,?)", rows)
dst.commit()

print(f"Loaded {len(rows)} ABP extended Strong's entries")
src.close()
dst.close()