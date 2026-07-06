#!/usr/bin/env python3
"""cert_invariants.py — the ABP certification invariant suite (cert Session 3).

Re-proves the certified state of live bible.db on demand: pinned row counts,
zero split-flips, zero leftover '--' dashes, the Tier B correction overlay
intact, feed baseline unchanged, nightly backup alive. ALL READ-ONLY.

Usage (on PA, from ~/bible-db):
  python3 scripts/cert_invariants.py [bible.db]   # run the 7 checks; exit 1 on any FAIL
  python3 scripts/cert_invariants.py --controls   # prove checks 1-4 + 7 FIRE on seeded bad
                                                  # input (temp scratch db; live untouched)

CONTROL RULE (standing): a green from a check that has never fired is void.
Checks 1-4 + 7 prove themselves via --controls on every run of that mode; checks 5-6
reuse cert_manifest.py, whose detections both fired on live incidents (the Rahlfs
pin-gap 2026-07-04; the missing backup stamp 2026-07-04).

RE-PIN RULE for PINS below: these numbers change ONLY in the same commit as a
deliberate rebuild + swap, after the compare_words gate passed — never edited to
"make the suite green". A red here after an intentional rebuild means "update the
pin in that rebuild's commit", not "the suite is broken".
FEED-level pinning (the 75 source files, incl. TIPNR since Session 5) is cert_manifest.json — hash-exact,
strictly stronger than any row-count floor, so feeds are not re-counted here.

NO second copies of detection logic: the flip check imports the production
find_flips (audit_split_flip.py); the backup check imports the one guard in
cert_manifest.py (WARN-only there, a hard FAIL here — a cert gate needs a
same-day-restorable backup, verify only needs to nag).
"""
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit_split_flip import find_flips           # the ONE flip detector
from cert_manifest import backup_guard_message    # the ONE backup guard

# Certified 2026-07-04 (Session 3 swap; compare_words gate: 110 cells / 11
# pre-registered live-stale verses, 626,305 = 626,305 rows).
PINS = {
    "words": 626309,  # S11: +4 vs Session-3 pin = the (P2) _split_numbered splits (Dan 4:1, Isa 10:23, Luk 8:28, Pro 3:15), verified by per-verse word-count diff vs live
    "verses": 31237,  # read from live at suite landing 2026-07-04
    "abp_corrections_active": 28,  # Cushi x6 + Jer 49:13 x2 + L2 (1Sa 6:11) x4 + L10 (Mal 3:6) x4 + L5 (Dan 4:33) x2 + S9-f prose x5 + Mat 20:29 greek_pos x1 + Act 7:3 x4  (S11 rebuild)
}


def _ro(db: str) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ── the checks — each returns a list of problem strings (empty = pass) ────────

def check_row_pins(conn, pins=None) -> list:
    pins = pins or PINS
    problems = []
    for table in ("words", "verses"):
        want = pins.get(table)
        if want is None:
            problems.append(f"{table}: pin NOT SET — fill PINS before trusting this suite")
            continue
        got = conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        if got != want:
            problems.append(f"{table}: {got:,} rows, pinned {want:,}")
    return problems


def check_split_flip(conn) -> list:
    flips = find_flips(conn)
    return [f"{len(flips)} flipped pair(s), e.g. {flips[0]['ref']} "
            f"stored '{flips[0]['stored']}'"] if flips else []


def check_emdash(conn) -> list:
    problems = []
    w = conn.execute("SELECT count(*) FROM words WHERE english LIKE '%--%'").fetchone()[0]
    v = conn.execute("SELECT count(*) FROM verses WHERE text LIKE '%--%'").fetchone()[0]
    if w:
        problems.append(f"{w} words cell(s) still carry literal '--'")
    if v:
        problems.append(f"{v} verse text(s) still carry literal '--'")
    return problems


def check_corrections(conn, expected_active=None) -> list:
    """Every active ingest-time correction must HOLD its corrected value on live.
    Failures NAME the row (book ch:vs pos field) — a reconciliation red is only
    actionable if it says which correction broke."""
    if expected_active is None:
        expected_active = PINS["abp_corrections_active"]
    problems = []
    has = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                       "AND name='abp_corrections'").fetchone()
    if not has:
        return [f"abp_corrections table MISSING (expected {expected_active} active rows)"]
    rows = conn.execute("SELECT * FROM abp_corrections "
                        "WHERE status='active' AND applied_at='ingest'").fetchall()
    if len(rows) != expected_active:
        problems.append(f"{len(rows)} active correction row(s), pinned {expected_active} "
                        "(an emptied/edited table would otherwise pass this check silently)")
    for c in rows:
        key = f"{c['book']} {c['chapter']}:{c['verse']} pos {c['position']} {c['field']}"
        if c["field"] == "verses.text":              # S9 (f) prose row: check verses.text, not a words column
            hits = conn.execute(
                "SELECT text AS val FROM verses WHERE book=? AND chapter=? AND verse=?",
                (c["book"], c["chapter"], c["verse"])).fetchall()
        else:
            hits = conn.execute(
                f"""SELECT w."{c['field']}" AS val FROM words w
                    JOIN verses v ON v.id = w.verse_id
                    WHERE v.book=? AND v.chapter=? AND v.verse=? AND w.position=?""",
                (c["book"], c["chapter"], c["verse"], c["position"])).fetchall()
        if len(hits) != 1:
            problems.append(f"{key}: {len(hits)} matching slot(s), expected exactly 1")
        elif hits[0]["val"] != c["corrected_value"]:
            problems.append(f"{key}: reads {hits[0]['val']!r}, certified value is "
                            f"{c['corrected_value']!r} (source was {c['source_value']!r})")
    return problems


def check_person_place_binding(conn) -> list:
    """No proper-noun name may render a fuzzy match to one section AND an exact match
    to the other. BOTH directions (the fuzzy path is symmetric):
      - fuzzy-PLACE + exact-PERSON = person-as-place (the Cushi shape, cert Session 4)
      - fuzzy-PERSON + exact-PLACE = place-as-person (the mirror, cert Session 6 — the
        8 mixed-block places lived in this shape's blind spot before the parser fix).
    Binding tables are PA-only + deploy-safe: absent -> nothing can mis-render -> pass."""
    has = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                       "AND name='pn_binding'").fetchone()
    if not has:
        return []
    rows = conn.execute("""
        WITH r AS (SELECT b.name, b.kind, e.section
                   FROM pn_binding b JOIN tipnr_entities e ON e.uniq = b.entity_uniq
                   WHERE b.render = 1)
        SELECT name,
               SUM(kind='fuzzy' AND section='place')  AS fp,
               SUM(kind='exact' AND section='person') AS ep,
               SUM(kind='fuzzy' AND section='person') AS fpe,
               SUM(kind='exact' AND section='place')  AS epl
        FROM r GROUP BY name
        HAVING (fp > 0 AND ep > 0) OR (fpe > 0 AND epl > 0)
    """).fetchall()
    out = []
    for r in rows:
        if r["fp"] and r["ep"]:
            out.append(f"{r['name']}: {r['fp']} fuzzy-place AND {r['ep']} exact-person "
                       f"render(s) (person-as-place mis-bind, the Cushi shape)")
        if r["fpe"] and r["epl"]:
            out.append(f"{r['name']}: {r['fpe']} fuzzy-person AND {r['epl']} exact-place "
                       f"render(s) (place-as-person mis-bind, the mirror shape)")
    return out


def check_manifest() -> list:
    r = subprocess.run([sys.executable, str(Path(__file__).parent / "cert_manifest.py"),
                        "verify"], capture_output=True, text=True)
    if r.returncode != 0:
        tail = (r.stdout + r.stderr).strip().splitlines()
        return ["cert_manifest verify FAILED: " + (tail[-1] if tail else "(no output)")]
    return []


def check_backup() -> list:
    msg = backup_guard_message()
    return [msg] if msg else []


CHECKS = [
    ("1 row pins (words/verses)", lambda conn: check_row_pins(conn)),
    ("2 split-flip = 0",          check_split_flip),
    ("3 em-dash '--' = 0",        check_emdash),
    ("4 corrections intact",      lambda conn: check_corrections(conn)),
    ("5 feed manifest",           lambda conn: check_manifest()),
    ("6 backup freshness",        lambda conn: check_backup()),
    ("7 person/place binding",    check_person_place_binding),
]


def run_suite(db: str) -> int:
    conn = _ro(db)
    failed = 0
    print(f"== cert_invariants on {db} (read-only) ==")
    for name, fn in CHECKS:
        problems = fn(conn)
        if problems:
            failed += 1
            print(f"  [FAIL] {name}")
            for p in problems:
                print(f"         - {p}")
        else:
            print(f"  [OK  ] {name}")
    conn.close()
    print(f"\n{'CERTIFIED STATE HOLDS' if not failed else f'{failed} CHECK(S) FAILED'} "
          f"({len(CHECKS) - failed}/{len(CHECKS)} green)")
    return 1 if failed else 0


# ── controls — prove checks 1-4 can fail (seeded bad input, throwaway db) ─────

def _scratch_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.executescript("""
      CREATE TABLE verses(id INTEGER PRIMARY KEY, book TEXT, chapter INT,
                          verse INT, text TEXT);
      CREATE TABLE words(verse_id INT, position INT, english TEXT,
                         english_head TEXT, strongs TEXT, strongs_base TEXT,
                         bracket_id INT);
      CREATE TABLE abp_corrections(book TEXT, chapter INT, verse INT, position INT,
                                   field TEXT, source_value TEXT, corrected_value TEXT,
                                   status TEXT, applied_at TEXT, ledger_ref TEXT,
                                   reason TEXT);
    """)
    # one clean verse so the scratch db isn't empty
    conn.execute("INSERT INTO verses VALUES (1,'Gen',1,1,'the LORD gives charge')")
    conn.execute("INSERT INTO words VALUES (1,0,'the',NULL,'3588','G3588',NULL)")
    conn.execute("INSERT INTO words VALUES (1,1,'LORD',NULL,'2962','G2962',NULL)")
    conn.commit()
    return conn


def run_controls() -> int:
    """Each control seeds ONE bad input and requires the check to FAIL on it.
    A control that comes back green is itself a failure (void-zero rule)."""
    results = []
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "control.db"
        conn = _scratch_db(db)

        # control 1: pin says 3 words, scratch has 2 -> must fail
        bad = check_row_pins(conn, pins={"words": 3, "verses": 1})
        results.append(("1 row pins", bool(bad), bad))

        # control 2: seed a genuinely flipped pair ("LORD the" vs clean "the LORD")
        conn.execute("INSERT INTO verses VALUES (2,'Psa',42,8,'the LORD gives charge')")
        conn.execute("INSERT INTO words VALUES (2,0,'LORD',NULL,'2962','G2962',NULL)")
        conn.execute("INSERT INTO words VALUES (2,1,'the',NULL,'3588','G3588',NULL)")
        conn.commit()
        bad = check_split_flip(conn)
        results.append(("2 split-flip", bool(bad), bad))

        # control 3: seed a literal '--' in both a word cell and a verse text
        conn.execute("INSERT INTO verses VALUES (3,'Luk',12,51,'you think not -- no')")
        conn.execute("INSERT INTO words VALUES (3,0,'you think not --',NULL,"
                     "'1380','G1380',NULL)")
        conn.commit()
        bad = check_emdash(conn)
        results.append(("3 em-dash", len(bad) == 2, bad))  # BOTH sides must trip

        # control 4: a correction whose cell was flipped back to the source value —
        # the check must fail AND name the exact row
        conn.execute("INSERT INTO verses VALUES (4,'2Sa',18,21,'And Joab said to Cushi')")
        conn.execute("INSERT INTO words VALUES (4,4,'Cushi,',NULL,'*','H3570',NULL)")
        conn.execute("INSERT INTO abp_corrections VALUES "
                     "('2Sa',18,21,4,'strongs_base','H3570','H3569',"
                     "'active','ingest','Class2-cushi','control seed')")
        conn.commit()
        bad = check_corrections(conn, expected_active=1)
        named = any("2Sa 18:21 pos 4 strongs_base" in p for p in bad)
        results.append(("4 corrections (must NAME the row)", bool(bad) and named, bad))

        # control 7: BOTH directions must fire — the Cushi shape (fuzzy-place +
        # exact-person) AND the mirror (fuzzy-person + exact-place, cert Session 6).
        conn.executescript("""
          CREATE TABLE pn_binding(name TEXT, entity_uniq TEXT, kind TEXT, render INT);
          CREATE TABLE tipnr_entities(uniq TEXT, section TEXT);
          INSERT INTO tipnr_entities VALUES ('Cush@x','place'),('Cushi@y','person'),
                                            ('Zorah@p','person'),('Zorah@q','place');
          INSERT INTO pn_binding VALUES ('cushi','Cush@x','fuzzy',1),
                                        ('cushi','Cushi@y','exact',1),
                                        ('zorahite','Zorah@p','fuzzy',1),
                                        ('zorahite','Zorah@q','exact',1);
        """)
        conn.commit()
        bad = check_person_place_binding(conn)
        both = any("Cushi shape" in b for b in bad) and any("mirror shape" in b for b in bad)
        results.append(("7 person/place binding (both directions)", both, bad))
        conn.close()

    print("== cert_invariants CONTROLS (each check must FIRE on seeded bad input) ==")
    ok = True
    for name, fired, detail in results:
        print(f"  [{'FIRED' if fired else 'DID NOT FIRE -> VOID'}] {name}")
        for d in detail:
            print(f"         - {d}")
        ok = ok and fired
    print("\n  checks 5-6 (manifest, backup): controls fired on LIVE incidents "
          "2026-07-04 (Rahlfs pin-gap; missing backup stamp) - see cert_manifest.py.")
    print(f"\n{'ALL CONTROLS FIRED - the suite can fail, its greens mean something.' if ok else 'CONTROL FAILURE - do NOT trust this suite until fixed.'}")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--controls" in sys.argv[1:]:
        sys.exit(run_controls())
    db = next((a for a in sys.argv[1:] if not a.startswith("--")), "bible.db")
    sys.exit(run_suite(db))
