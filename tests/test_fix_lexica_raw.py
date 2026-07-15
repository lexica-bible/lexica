"""fix_lexica_raw.py — the SURGICAL-EDIT WRITE PATH must run every check the main write
path runs (ENGINE_LESSONS #69, third instance; ticket scope amended 2->3 gaps by reviewer
ruling 2026-07-14).

THE THREE GAPS this file pins (all three verified at byte level before the fix, session
record 2026-07-14):
  1. PROBES NOT RUN — fix_lexica_raw.py:95 called `B.validate_entry(entry)` with NO conn;
     build_lexica_def.py:3525 (the main path) passes it. With conn=None validate_entry
     prints "V11 prose probes NOT RUN" and SKIPS the verbatim-quote gate, the named-subject
     probe and the identity scanner (build_lexica_def.py:2876). The quote gate BLOCKS on the
     main path; on the fix path it simply never happened.
  2. ADJUDICATION SILENTLY STRIPPED — assemble() rebuilds `audit` fresh from the prose every
     time (build_lexica_def.py:2047) and `warns_adjudicated` is not among the keys it
     rebuilds. A surgical fix to an adjudicated row erased the reviewer ruling AND the warns
     it covered, leaving the row reading "clean, no warns ever" = a FALSIFIED RECORD.
  3. NO OPEN-WARN REFUSAL — the main path calls open_probe_warns() and refuses the write
     (build_lexica_def.py:3558); fix_lexica_raw never called it. This gap is CREATED BY
     FIXING #1: once the probes actually run here, they emit warns, and with no refusal the
     fix tool would write exactly the rows the main path refuses. Fixing 1+2 alone makes the
     tool WORSE than it is today — hence one change, three gaps.

CARRY RULE (reviewer-ruled 2026-07-14, standing for this tool): a prior adjudication may be
carried across a surgical edit ONLY when the new warn set is identical to the old one over
the CANONICALIZED set (stable ordering + stable serialization) — NOT raw string equality of
whatever the audit block happens to emit. Canonicalization is REQUIRED, not cosmetic: warns
are plain strings appended in SCAN ORDER (build_lexica_def.py:2728), never sorted, so a
surgical edit that moves text reorders identical warns and raw equality would force a
spurious refusal — which is what invites a "just carry it" workaround later. If the set
CHANGED, the old ruling never saw the new items: do not carry, refuse, require a fresh
--adjudicate-warns. SILENT CARRY-FORWARD IS BANNED.

FIXTURE PROVENANCE (zero spend, no PA read, no network — reviewer constraint):
card + verse bytes are the REAL G1390 δόμα bytes already banked in tests/test_v11_probes.py
(card snippet = the `raw_d1` probe-2 defect-1 fixture, bank bda7de94; verse texts = verses.text
bytes from the sanctioned one-time read-only PA consult 2026-07-12). The synthetic DB carries
only what assemble() reads. The adjudication NOTE text is fixture text, not a real reviewer
ruling — nothing here is a receipt.

Red-first: run BEFORE the fix, all three cases FAIL (session record 2026-07-14).
"""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "scripts", "fix_lexica_raw.py")

# ── Real G1390 bytes (banked; see FIXTURE PROVENANCE) ────────────────────────────────────
VT_2CH_21_3 = ("And their father gave to them many gifts — silver, and gold, and shields, "
               "with cities being walled in Judah. But the kingdom he gave to Jehoram, for "
               "he was the first-born.")
VT_PSA_68_18 = ("You ascended into the height; you captured captivity; you received gifts "
                "by men; for even to encamp among the ones resisting persuasion.")

# The card. Sense body opens with the REAL raw_d1 bytes — "Jehoiada" is absent from
# 2Ch 21:3's stored text, so probe 2 fires exactly one named-subject warn.
RAW = (
    "**Senses:**\n"
    "\n"
    "**1. a gift given, a present** — Jehoiada's father distributing silver, gold, and "
    "shields to his sons (2Ch 21:3); gifts received among men (Psa 68:18).\n"
    "\n"
    "**Range:** one party grants another something of material value; the giving may be "
    "freely offered.\n"
)

ADJUDICATION = "fixture ruling: probe-2 over-firing, passage owner not named in verse"


def build_db(path):
    """Only what assemble() reads: verses / words / lexica_def. Starts from a clean file so each
    case seeds its own prior row with no carry-over from the case before it."""
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);
        CREATE TABLE words (verse_id INT, position INT, strongs TEXT, strongs_base TEXT,
                            english TEXT, english_head TEXT, italic_words TEXT, is_pn INT);
        CREATE TABLE lexica_def (strongs TEXT PRIMARY KEY, lemma TEXT, translit TEXT,
                                 def_json TEXT, synth_ver TEXT, updated TEXT);
    """)
    conn.execute("INSERT INTO verses VALUES (1,'2Ch',21,3,?)", (VT_2CH_21_3,))
    conn.execute("INSERT INTO verses VALUES (2,'Psa',68,18,?)", (VT_PSA_68_18,))
    # δόμα tagged in both cited verses, so the citation gate PASSES and the run reaches
    # the probe/adjudication logic under test (not blocked earlier for an unrelated reason).
    for vid in (1, 2):
        conn.execute("INSERT INTO words VALUES (?,5,'1390','G1390','gifts','gifts','',0)", (vid,))
    conn.commit()
    return conn


def seed_entry(conn, raw=RAW, adjudicated=True):
    """Store the prior row the way the MAIN path would have shipped it: probe-2 warn present
    AND adjudicated (the exact state G1390 ships in today)."""
    # The warn string is the probe's REAL emitted bytes (build_lexica_def.py:2728 format), not a
    # paraphrase — the carry test compares the SET, so an invented string here would read as a
    # changed set and the fixture would test nothing. (Caught by the first green run, 2026-07-14:
    # a hand-written '— adjudicate' tail was missing the real '(misattribution class)'.)
    audit = {"probe2_warns": ['named subject "Jehoiada" absent from cited text(s) 2Ch 21:3 '
                             '— adjudicate (misattribution class)'],
             "pass": 2, "total": 2, "tagging": 0, "real": 0, "noverse": 0, "misses": []}
    if adjudicated:
        audit["warns_adjudicated"] = ADJUDICATION
    entry = {"strongs": "G1390", "lemma": "δόμα", "translit": "doma",
             "raw": raw, "audit": audit}
    conn.execute("INSERT OR REPLACE INTO lexica_def VALUES ('G1390','δόμα','doma',?,'lexica:f27027b50754','2026-07-14T00:00:00')",
                 (json.dumps(entry, ensure_ascii=False),))
    conn.commit()


def run_tool(db, old, new, *extra):
    # The tool prints the Greek lemma (δόμα). A Windows console is cp1252, so the child would die
    # with UnicodeEncodeError under the pre-commit hook while CI (utf-8 Linux) passed — the test
    # sets its OWN encoding rather than depending on the caller's console. Caught by the hook on
    # the first commit attempt, 2026-07-14.
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, TOOL, "--db", db, "--word", "G1390",
                        "--old", old, "--new", new] + list(extra),
                       capture_output=True, text=True, encoding="utf-8", env=env)
    return r


def stored(db):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT def_json FROM lexica_def WHERE strongs='G1390'").fetchone()
    conn.close()
    return json.loads(row["def_json"])


def main():
    tmp = tempfile.mkdtemp()
    db = os.path.join(tmp, "fixture.db")

    # ═══ GAP 1 — the probes must RUN on the fix path ═══
    # A no-op-to-the-warn-set edit (Range wording only). The warn set is unchanged, so this
    # edit is the ALLOWED case: it must write, with the probes having actually run.
    conn = build_db(db)
    seed_entry(conn)
    conn.close()
    r = run_tool(db, "freely offered", "freely given", "--apply")
    assert "prose probes NOT RUN" not in r.stderr, (
        "GAP 1: the V11 prose probes were SKIPPED on the fix write path — validate_entry got "
        "no DB connection, so the verbatim-quote gate never ran on a row this tool WROTE.\n"
        + r.stderr)

    # ═══ GAP 2 — an unchanged warn set carries its adjudication across the edit ═══
    assert r.returncode == 0, ("the allowed edit (warn set unchanged) was refused:\n"
                               + r.stdout + r.stderr)
    e = stored(db)
    assert "freely given" in e["raw"], "the surgical edit did not land"
    assert e["audit"].get("warns_adjudicated") == ADJUDICATION, (
        "GAP 2: the reviewer adjudication was SILENTLY STRIPPED by the re-assemble — the row "
        "now reads 'clean, no warns ever'. That is a falsified record.\n"
        f"audit keys: {sorted(e['audit'])}")
    assert e["audit"].get("probe2_warns"), (
        "GAP 2: the warns the ruling COVERS are gone from the row — an adjudication stamp "
        "with no warns under it documents nothing.")

    # ═══ GAP 3 — a CHANGED warn set must NOT inherit the old ruling; the write is refused ═══
    # The edit introduces "Kore" — a name in no cited verse — so a NEW, unadjudicated warn
    # appears. The old ruling never saw it. Must refuse, and must not write.
    conn = build_db(db)
    seed_entry(conn)
    conn.close()
    before = stored(db)["raw"]
    r3 = run_tool(db, "his sons", "his sons and Kore", "--apply")
    assert r3.returncode != 0, (
        "GAP 3: a surgical edit that introduced a NEW un-adjudicated warn was WRITTEN — the "
        "main path refuses exactly this row (open_probe_warns, build_lexica_def.py:3558).\n"
        + r3.stdout + r3.stderr)
    assert stored(db)["raw"] == before, "GAP 3: refused, but the row was written anyway"
    e3 = stored(db)
    assert e3["audit"].get("warns_adjudicated") == ADJUDICATION, (
        "the refused run must leave the stored row untouched")

    print("test_fix_lexica_raw: all assertions passed")


if __name__ == "__main__":
    main()
