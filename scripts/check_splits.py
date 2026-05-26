import sqlite3

conn = sqlite3.connect('bible.db')

NT_BOOKS = {'Mat','Mar','Luk','Joh','Act','Rom','1Co','2Co','Gal','Eph','Php',
            'Col','1Th','2Th','1Ti','2Ti','Tit','Phm','Heb','Jas','1Pe','2Pe',
            '1Jn','2Jn','3Jn','Jud','Rev'}

nt_list = list(NT_BOOKS)
placeholders = ','.join('?' * len(nt_list))

rows = conn.execute(f"""
    SELECT w.strongs_base, l.lemma, l.translit,
           COUNT(CASE WHEN v.book IN ({placeholders}) THEN 1 END) as nt_count,
           COUNT(CASE WHEN v.book NOT IN ({placeholders}) THEN 1 END) as ot_count
    FROM words w
    JOIN verses v ON w.verse_id = v.id
    LEFT JOIN lexicon l ON l.strongs = w.strongs_base
    WHERE w.strongs_base != '*' AND w.strongs_base NOT LIKE '%.%'
    GROUP BY w.strongs_base
    HAVING nt_count > 0 AND ot_count > 0
""", nt_list + nt_list).fetchall()

conn.close()

by_num = {}
for r in rows:
    try:
        n = int(r[0])
        by_num[n] = {'lemma': r[1], 'translit': r[2], 'nt': r[3], 'ot': r[4]}
    except Exception:
        pass

print(f"{'N':>6}  {'translit':14}  OT / NT   |  {'N+1':>6}  {'translit':14}  OT / NT")
print('-' * 72)
for n in sorted(by_num):
    m = n + 1
    if m not in by_num:
        continue
    a, b = by_num[n], by_num[m]
    a_ot = a['ot'] / max(a['nt'], 1)
    b_nt = b['nt'] / max(b['ot'], 1)
    a_nt = a['nt'] / max(a['ot'], 1)
    b_ot = b['ot'] / max(b['nt'], 1)
    if (a_ot > 3 and b_nt > 3) or (a_nt > 3 and b_ot > 3):
        at = (a['translit'] or '').encode('ascii', 'replace').decode()[:14]
        bt = (b['translit'] or '').encode('ascii', 'replace').decode()[:14]
        print(f"G{n:>5}  {at:14}  {a['ot']:4} / {a['nt']:4}  |  G{m:>5}  {bt:14}  {b['ot']:4} / {b['nt']:4}")
