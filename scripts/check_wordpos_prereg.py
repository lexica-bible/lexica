#!/usr/bin/env python3
"""check_wordpos_prereg.py — READ-ONLY control harness for the word-position
binding lane (DESIGN_wordpos_binding.md section 3, controls (a)-(c); design
ratified 2026-08-07, codicils C1-C3).

WHAT THE AUTOMATED GATES ARE (Codicil 2, verbatim intent): POSITION-INTEGRITY
gates only. They catch a quote at the wrong slot, a stale name, a duplicate
entity, a broken bracket — they can NEVER certify the entity is the right man.
Entity correctness has exactly one gate: the reviewer's per-row verdict.

Checks per TSV row (the future scripts/pn_slot_rulings.tsv format:
name book chapter verse position entity_uniq referent_kind evidence_class
evidence_quote rationale flags — tab-separated, # comments):
  R1 verse row exists; a words row exists at (verse, position)
  R2 STALE-NAME gate (control (b)): printed english_head at the slot
     compact-matches the row's name — mismatch REFUSES the row
  R3 entity_uniq exists in tipnr_entities; its section agrees with
     referent_kind (person->person; place|place/gentilic->place; group->
     person or other) — the rider-2 kind check
  R4 QUOTE gate (control (a), position-integrity half): the quote's tokens,
     ellipses removed, appear IN ORDER in the verse — in the storage word
     stream OR in verses.text prose (quotes are verbatim ABP prose; storage
     order can differ, e.g. "did obeisance to Cushi" stores verb-first) —
     AND the slot's own printed head appears among the quote's tokens; a
     quote that never touches the ruled slot REFUSES the row
  R5 DUPLICATE gate (control (a)): two rows in one verse proposing the SAME
     entity must both carry the same-referent flag, else REFUSED
Per verse:
  R6 BRACKET CONTIGUITY (control (c)): bracket_gaps() — imported from
     scripts/bracket_contiguity.py, THE classifier fix_lane3_star_merges.py
     itself uses — must return no gaps; also REPORTS which ruled slots sit
     inside or adjacent (+/-1) to a bracket span (the per-mode display-oracle
     work list for the render-modeling checks).

RED-FIRST (--controls): runs built-in control rows with pinned expectations —
deliberately wrong rows MUST fail their named gate, good rows must pass.
Any control landing off-expectation => exit 2. Run this and see it red/green
BEFORE trusting a clean sweep on the real TSV.

Usage (PA, JP runs; both read-only):
  cd ~/bible-db && PYTHONIOENCODING=utf-8 python3 scripts/check_wordpos_prereg.py bible.db --controls
  cd ~/bible-db && PYTHONIOENCODING=utf-8 python3 scripts/check_wordpos_prereg.py bible.db scripts/pn_slot_rulings.tsv
"""
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bracket_contiguity import bracket_gaps

DB = sys.argv[1] if len(sys.argv) > 1 else "bible.db"
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

compact = lambda s: re.sub(r"[^a-z]", "", (s or "").lower())


def tokens(s):
    return [t for t in re.findall(r"[a-z']+", (s or "").lower()) if t]


def subsequence(needle, hay):
    it = iter(hay)
    return all(t in it for t in needle)


COLS = ["name", "book", "chapter", "verse", "position", "entity_uniq",
        "referent_kind", "evidence_class", "evidence_quote", "rationale", "flags"]

# kind agreement map (rider 2: never assume person)
KIND_OK = {"person": {"person"}, "place": {"place"},
           "place/gentilic": {"place"}, "group": {"person", "other"}}


def check_row(row, verse_rows_cache):
    """Returns (ok, reason). Position-integrity only (Codicil 2)."""
    key = (row["book"], int(row["chapter"]), int(row["verse"]))
    if key not in verse_rows_cache:
        v = conn.execute(
            "SELECT id, text FROM verses WHERE book=? AND chapter=? AND verse=?",
            key).fetchone()
        rows = conn.execute(
            "SELECT position, english_head, english, bracket_id "
            "FROM words WHERE verse_id=? ORDER BY position",
            (v["id"],)).fetchall() if v else []
        verse_rows_cache[key] = (v, rows)
    v, rows = verse_rows_cache[key]
    if not v:
        return False, "R1 verse row missing"
    pos = int(row["position"])
    slot = next((r for r in rows if r["position"] == pos), None)
    if slot is None:
        return False, f"R1 no words row at position {pos}"
    # R2 stale-name gate
    if compact(slot["english_head"]) != compact(row["name"]):
        return False, (f"R2 STALE-NAME: printed head "
                       f"'{slot['english_head']}' != ruled name '{row['name']}'")
    # R3 entity + kind
    e = conn.execute("SELECT section FROM tipnr_entities WHERE uniq=?",
                     (row["entity_uniq"],)).fetchone()
    if not e:
        return False, f"R3 entity '{row['entity_uniq']}' not in tipnr_entities"
    want = KIND_OK.get(row["referent_kind"])
    if want is None:
        return False, f"R3 unknown referent_kind '{row['referent_kind']}'"
    if (e["section"] or "") not in want:
        return False, (f"R3 KIND MISMATCH: referent_kind '{row['referent_kind']}'"
                       f" vs entity section '{e['section']}'")
    # R4 quote gate
    q = re.sub(r"\.\.\.|…", " ", row["evidence_quote"])
    qtok = tokens(q)
    vtok = [t for r in rows for t in tokens(r["english"])]
    ptok = tokens(v["text"])
    if not qtok:
        return False, "R4 empty quote"
    if not (subsequence(qtok, vtok) or subsequence(qtok, ptok)):
        return False, ("R4 QUOTE: tokens not found in order in either the "
                       "word stream or the prose")
    head = compact(slot["english_head"])
    if head and head not in [compact(t) for t in qtok]:
        return False, (f"R4 QUOTE-ADJACENCY: slot's own word "
                       f"'{slot['english_head']}' absent from the quote")
    return True, "ok"


def check_file(rows):
    cache, failures = {}, 0
    by_verse = {}
    for row in rows:
        ok, reason = check_row(row, cache)
        # R5 duplicate gate
        if ok:
            key = (row["book"], row["chapter"], row["verse"], row["entity_uniq"])
            prev = by_verse.get(key)
            same = "same-referent" in (row["flags"] or "")
            if prev is not None and not (same and prev):
                ok, reason = False, ("R5 DUPLICATE: entity proposed twice in "
                                     "verse without same-referent flag on both")
            by_verse[key] = same
        tag = "PASS" if ok else "REFUSED"
        print(f"  {row['book']} {row['chapter']}:{row['verse']} p{row['position']}"
              f" {row['name']} -> {row['entity_uniq']}: {tag} ({reason})")
        failures += 0 if ok else 1
    # R6 per-verse contiguity + bracket-adjacency report
    for key, (v, wrows) in cache.items():
        if not v:
            continue
        gaps = bracket_gaps(wrows)
        print(f"  {key[0]} {key[1]}:{key[2]} contiguity: "
              f"{'PASS' if not gaps else 'FAIL ' + str(gaps)}")
        if gaps:
            failures += 1
        ruled = [int(r["position"]) for r in rows
                 if (r["book"], int(r["chapter"]), int(r["verse"])) == key]
        spans = {}
        for r in wrows:
            if r["bracket_id"] is not None:
                lo, hi = spans.get(r["bracket_id"], (r["position"], r["position"]))
                spans[r["bracket_id"]] = (min(lo, r["position"]), max(hi, r["position"]))
        touch = sorted({p for p in ruled for lo, hi in spans.values()
                        if lo - 1 <= p <= hi + 1})
        if touch:
            print(f"    bracket-adjacent ruled slots (render-modeling work list): {touch}")
    return failures


# ── red-first controls: pinned expectations, off-expectation => exit 2 ───────
def ctl(name, book, ch, vs, pos, uniq, kind, cls, quote, flags=""):
    return dict(zip(COLS, [name, book, ch, vs, pos, uniq, kind, cls, quote, "control", flags]))

CONTROLS = [
    # good rows — must PASS
    (ctl("mary", "Mat", 27, 61, 3, "Mary_Magdalene@Mat.27.56-Jhn", "person",
         "epithet-in-verse", "Mary the Magdalene,"), True,
     "good Magdalene row"),
    (ctl("joash", "2Ki", 14, 1, 3, "Joash@2Ki.13.9-Amo", "person",
         "kin-in-verse", "of Joash son of Jehoahaz king of Israel,"), True,
     "good Joash row"),
    # (a) duplicate without same-referent flag — second row MUST be REFUSED
    (ctl("mary", "Mat", 27, 61, 9, "Mary_Magdalene@Mat.27.56-Jhn", "person",
         "epithet-in-verse", "and the other Mary,"), False,
     "wrong-referent: Magdalene proposed at BOTH Marys (R5 duplicate)"),
    # (a) quote that never touches the ruled slot — MUST be REFUSED
    (ctl("mary", "Mat", 27, 61, 3, "Mary_Magdalene@Mat.27.56-Jhn", "person",
         "epithet-in-verse", "sitting down before the tomb."), False,
     "quote-at-wrong-position (R4 adjacency)"),
    # (b) stale name: ruled name is not what the slot prints — MUST be REFUSED
    (ctl("joash", "2Ki", 14, 1, 10, "Joash@2Ki.11.2-2Ch", "person",
         "kin-in-verse", "Amaziah son of Joash king of Judah"), False,
     "stale-name: position 10 prints 'amaziah' (R2)"),
    # rider-2 kind check: person kind against a place entity — MUST be REFUSED
    (ctl("haran", "Gen", 11, 31, 43, "Haran@Gen.11.31-Act", "person",
         "kin-in-verse", "they came unto Haran and dwelt there."), False,
     "kind mismatch: place entity declared person (R3)"),
]

if "--controls" in sys.argv:
    print("RED-FIRST CONTROLS (expected vs actual, per row):")
    bad = 0
    cache = {}
    seen = {}
    for row, expect_pass, label in CONTROLS:
        ok, reason = check_row(row, cache)
        if ok:  # apply R5 across control rows too
            key = (row["book"], row["chapter"], row["verse"], row["entity_uniq"])
            same = "same-referent" in (row["flags"] or "")
            if key in seen and not (same and seen[key]):
                ok, reason = False, "R5 DUPLICATE"
            seen[key] = same
        verdict = "PASS" if ok else "REFUSED"
        expected = "PASS" if expect_pass else "REFUSED"
        state = "OK" if ok == expect_pass else "** CONTROL FAILED **"
        print(f"  [{state}] {label}\n"
              f"    expected {expected} / actual {verdict} ({reason})")
        bad += 0 if ok == expect_pass else 1
    print(f"controls: {len(CONTROLS) - bad}/{len(CONTROLS)} behaved as pinned")
    sys.exit(2 if bad else 0)

# normal mode: check a TSV
tsv = sys.argv[2] if len(sys.argv) > 2 else "scripts/pn_slot_rulings.tsv"
rows = []
for ln in open(tsv, encoding="utf-8"):
    ln = ln.rstrip("\n")
    if not ln or ln.startswith("#") or ln.startswith("name\t"):
        continue
    parts = ln.split("\t")
    if len(parts) < len(COLS):
        parts += [""] * (len(COLS) - len(parts))
    rows.append(dict(zip(COLS, parts)))
print(f"checking {len(rows)} slot rulings from {tsv}:")
failures = check_file(rows)
print(f"{'ALL PASS' if not failures else str(failures) + ' FAILURES'} "
      f"(position-integrity gates only — entity correctness is the reviewer's"
      f" per-row verdict, Codicil 2)")
sys.exit(1 if failures else 0)
