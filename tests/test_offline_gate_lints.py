"""offline_gate_check.py must run the WRITE PATH's checks, or NAME each one it skips
(ENGINE_LESSONS #69(i); scope ruled (b) by reviewer 2026-07-14: all ten runnable checks +
four named skips, not the two lints the ticket happened to name).

THE GAP (measured before the fix, session record 2026-07-14): the harness ran ONE production
detector — probe1_verbatim (plus a verdict-neutral score walk). The write path runs ELEVEN:
run_citation_gate · dangling_book_refs · noncanon_book_refs · double_shelved ·
gloss_note_claims · hedged_citations · subuse_overload · registry_verse_hits (assemble's audit
block) + probe1_verbatim · probe2_names · scan3_identity (validate_entry). So a readiness pass
could certify a card on 1-of-11 and read as covered — which is how the Eph 4:8 rendering-claim
fire reached a LIVE row (#69(a)).

FOUR CHECKS CANNOT RUN OFFLINE and are OUTPUT CONTRACT, not comments (reviewer condition 2):
the coverage gate (needs the fed sample — only the call site has it), floor-match, the #30
membership guard and the #55 sense-count guard (need the floor/roster). They must be PRINTED as
SKIPPED-with-reason on every run: the reader of a readiness report has to see them, not the
reader of the source. Silence reads as covered.

FIXTURE PROVENANCE — REAL BYTES, dumped read-only from PA by JP 2026-07-14 (the rendering-claim
case could NOT be reconstructed from the AUDIT's prose description without violating #70:
"seed a fixture from emitted bytes, never a hand-recalled string" — a hand-built claim would be
shaped to fire, so its green would prove only that the author can trip their own lint):
  · G1390 gloss_notes  = lexica_def def_json '$.gloss_notes' (both bullets, verbatim)
  · Eph 4:8 G1390 slot = words english_head 'gifts' | english 'gifts' | italic_words '' (empty)
  · Eph 4:8 verse text = verses.text
This is the live blemish of record: the card labels the gloss *gift*; the corpus renders "gifts".

SCOPE NOTE — Psa 68:18 (stated, not hidden). Bullet 2's head names Psa 68:18 as well as Eph 4:8,
so ref_spans returns both. Its verse TEXT is included (real bytes, banked in test_v11_probes.py)
so probe 1 can resolve the bullet's quote; its WORDS row is deliberately ABSENT because its
english_head was not dumped, and inventing one is exactly what #70 bans. The absence does NOT
change the verdict under _claim_fires' set semantics: the claimed gloss "gift" is clean at NO
ref either way ("gift" != "gifts"), so the bullet reports exactly ONE fire, at the first ref —
Eph 4:8 — with or without Psa 68:18 present. gloss_note_claims skips refs that carry no
rendering row for the lemma.
Bullet 1 (*presents*, Num 28:2 / 2Ch 32:23) contributes NOTHING here: those verses are absent
from the fixture, so the wrapper skips them. Its clean-in-production status rests on the AUDIT
record, and is NOT re-proven by this file.

KNOWN FIXTURE ARTIFACT (stated, so nobody reads it as a finding): the citation gate reports
1/4 pass — real 1 / no-verse 2 — because the fixture carries only Eph 4:8's data. Num 28:2 and
2Ch 32:23 are not seeded (no-verse), and Psa 68:18 has no words row (real miss, per the SCOPE
NOTE above). The LIVE card's citation gate is clean on the record. No assertion here depends on
the gate's numbers; the gate is exercised only to prove it RUNS offline.

RED-FIRST: run BEFORE the extension — the harness printed no lint section and no skip lines at
all (session record 2026-07-14).
"""
import json
import os
import subprocess
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "scripts", "offline_gate_check.py")
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import build_lexica_def as B  # noqa: E402  (production book table — never a hand-typed copy)

# ── REAL BYTES (PA read-only dump, 2026-07-14) ───────────────────────────────────────────────
GLOSS_NOTES = (
    "- *presents* (Num 28:2; 2Ch 32:23): both occurrences are fully covered by the plain sense "
    "of material gifts given or offered; the gloss introduces no distortion but adds a "
    "suggestion of ceremony or tribute that the word itself does not require.\n"
    "- *gift* in Eph 4:8: the translation renders a downward-bestowing sense, which that verse's "
    "wording supports. The gloss note on Psa 68:18, the source psalm, is that the direction "
    "there is upward reception (\"you received gifts by men\"), not the downward grant the NT "
    "verse describes; the same English gloss covers both, but the texts' own verbs diverge.\n"
)
VT_EPH_4_8 = ("Therefore he says, Having ascended into the height he captured the captivity, "
              "and he gave gifts to men.")
# banked in tests/test_v11_probes.py (same 2026-07-12 read-only PA consult)
VT_PSA_68_18 = ("You ascended into the height; you captured captivity; you received gifts "
                "by men; for even to encamp among the ones resisting persuasion.")

RAW = (
    "**Senses:**\n"
    "\n"
    "**1. a gift given, a present** — what is handed over to another (Eph 4:8).\n"
    "\n"
    "**Gloss notes:**\n"
    + GLOSS_NOTES
)

CARD = {"strongs": "G1390", "lemma": "δόμα", "translit": "doma", "raw": RAW,
        "sig": "bda7de94" + "0" * 4, "created": "2026-07-14T00:00:00"}


def build_db(path):
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
    # THE VALID-BOOK SET COMES FROM THE verses TABLE ITSELF (_valid_books: SELECT DISTINCT book
    # FROM verses), so dangling_book_refs / noncanon_book_refs behave differently against a thin
    # fixture: with only Eph+Psa seeded, canonical "Num"/"2Ch" read as NON-canonical and a bare
    # "Rev" reads as unknown-and-ignored. Both are fixture artifacts, not findings. Seed one
    # placeholder row per canonical code, derived from the PRODUCTION table (_BOOK_CODE) — a
    # hand-typed book list here would be the #70 mistake again.
    for i, code in enumerate(sorted(set(B._BOOK_CODE.values())), start=100):
        conn.execute("INSERT INTO verses VALUES (?,?,1,1,'')", (i, code))
    conn.execute("INSERT INTO verses VALUES (1,'Eph',4,8,?)", (VT_EPH_4_8,))
    conn.execute("INSERT INTO verses VALUES (2,'Psa',68,18,?)", (VT_PSA_68_18,))
    # Eph 4:8's REAL dumped slot. Psa 68:18 carries no words row on purpose — see SCOPE NOTE.
    conn.execute("INSERT INTO words VALUES (1,9,'1390','G1390','gifts','gifts','',0)")
    conn.commit()
    conn.close()


def run_tool(db, card_path, expect):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, TOOL, "--card", card_path, "--expect", expect,
                           "--db", db], capture_output=True, text=True, encoding="utf-8", env=env)


def main():
    tmp = tempfile.mkdtemp()
    db = os.path.join(tmp, "fixture.db")
    card_path = os.path.join(tmp, "G1390_card.json")
    build_db(db)
    with open(card_path, "w", encoding="utf-8") as f:
        json.dump(CARD, f, ensure_ascii=False)

    r = run_tool(db, card_path, "*gift* in Eph 4:8")
    out = r.stdout + r.stderr
    assert r.returncode == 0, "harness did not complete:\n" + out

    # ═══ 1. THE RENDERING-CLAIM LINT MUST FIRE OFFLINE (the live blemish of record) ═══
    # Exactly the fire that reached a live row: claimed gloss "gift", real rendering "gifts",
    # at Eph 4:8. gift != gifts, and gift is CONTAINED in gifts -> kind 'rendering-mismatch'
    # (containment must never pass — the archived ἁμαρτία 'sin' vs 'sin offering' rule).
    assert "rendering-mismatch" in out, (
        "the rendering-claim lint did NOT fire offline — this is the Eph 4:8 blemish that "
        "reached a LIVE row because the readiness harness never ran this check (#69(a)).\n" + out)
    assert "Eph 4:8" in out and "gift" in out, ("the fire did not name the ref/gloss:\n" + out)

    # ═══ 2. THE DANGLING-REF LINT MUST RUN (the ticket's other named lint) ═══
    # SYNTHETIC red case, labelled as such: no banked dangling-ref card byte exists for G1390.
    # A bare canonical CODE anchored to no number flags; bare English names are soft-skipped.
    card2 = dict(CARD)
    card2["raw"] = RAW + "\nSee also Rev for the wider picture.\n"
    p2 = os.path.join(tmp, "dangling.json")
    with open(p2, "w", encoding="utf-8") as f:
        json.dump(card2, f, ensure_ascii=False)
    o2 = run_tool(db, p2, "*gift* in Eph 4:8")
    assert "Rev" in (o2.stdout + o2.stderr), (
        "the dangling-ref lint did not run/report offline:\n" + o2.stdout + o2.stderr)

    # ═══ 3. EVERY WRITE-PATH CHECK IS NAMED IN THE OUTPUT ═══
    # #69(i): enumerate and run, or NAME the skip. Silence reads as covered.
    for name in ("citation gate", "dangling", "noncanon", "double_shelved", "gloss_claims",
                 "hedged", "subuse_overload", "registry_verses", "probe1", "probe2", "scan3"):
        assert name in out, (f"write-path check {name!r} is not named in the harness output — "
                             f"a reader cannot tell whether it ran.\n" + out)

    # ═══ 4. THE FOUR OFFLINE-IMPOSSIBLE CHECKS ARE PRINTED AS SKIPPED-WITH-REASON ═══
    # Reviewer condition 2: output contract, not comments.
    assert out.count("SKIPPED") >= 4, (
        "the offline-impossible checks must be PRINTED as SKIPPED-with-reason on every run — "
        "the reader of a readiness report must see them, not the reader of the source.\n" + out)
    for name in ("coverage gate", "floor-match", "#30", "#55"):
        assert name in out, (f"offline-impossible check {name!r} is not declared skipped.\n" + out)

    print("test_offline_gate_lints: all assertions passed")


if __name__ == "__main__":
    main()
