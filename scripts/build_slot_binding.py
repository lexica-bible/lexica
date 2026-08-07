#!/usr/bin/env python3
"""build_slot_binding.py — land the word-position slot binds (pn_slot_binding).

The word-position binding lane's writer (DESIGN_wordpos_binding.md §1, design
+ prereg reviewer-ratified 2026-08-07). Reads scripts/pn_slot_rulings.tsv (the
1:1 image of the FROZEN prereg) and writes ONLY the pn_slot_binding side table
— never words, verses, or pn_binding. Dry-run by default; --apply writes.

LANDING GUARDS (every row, refuse-and-report — a refused row simply does not
land, leaving that slot on today's honest Fix-A floor):
  G1 verse + words row exist; printed english_head at (verse, position)
     compact-matches the ruled name (the staleness tripwire — a rebuild that
     moves positions kills the row instead of serving a wrong identity)
  G2 entity exists in tipnr_entities and its section agrees with the row's
     referent_kind (person / place / place|gentilic / group) — rider 2
  G3 PRECEDENCE: no render=1 pn_binding row may exist for (book, ch, vs,
     name) — slot grain lands only where verse grain declines. A collision is
     a STOP-AND-LOOK (the gate_pn_rulings hot-row rule applied here).
  G4 duplicate entity within one verse requires the same-referent flag on
     every such row.
Any refusal prints the row + reason; --apply REFUSES TO WRITE if any guard
fired (all-or-nothing — no partial landings).

Re-land after a words rebuild: build_entity_binding.py --apply calls land()
automatically at the end of its run (the design's same-run promise), so slot
binds re-derive from the repo TSV exactly like pn_hand_rulings.tsv rows do.

Usage (PA, JP runs):
  cd ~/bible-db && PYTHONIOENCODING=utf-8 python3 scripts/build_slot_binding.py bible.db            # dry-run
  cd ~/bible-db && PYTHONIOENCODING=utf-8 python3 scripts/build_slot_binding.py bible.db --apply
"""
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from entity_resolution import book_num

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "pn_slot_rulings.tsv")
COLS = ["name", "book", "chapter", "verse", "position", "entity_uniq",
        "referent_kind", "evidence_class", "evidence_quote", "rationale", "flags"]
KIND_OK = {"person": {"person"}, "place": {"place"},
           "place/gentilic": {"place"}, "group": {"person", "other"}}

compact = lambda s: re.sub(r"[^a-z]", "", (s or "").lower())


def read_tsv(path=TSV):
    rows = []
    for ln in open(path, encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln or ln.startswith("#") or ln.startswith("name\t"):
            continue
        parts = ln.split("\t")
        parts += [""] * (len(COLS) - len(parts))
        rows.append(dict(zip(COLS, parts)))
    return rows


def land(db_path, apply=False, tsv=TSV, strict=True):
    """Validate every TSV row against the live db; write pn_slot_binding.
    strict=True (manual --apply): ALL-OR-NOTHING — any guard refusal blocks
    the whole write (the first-landing bar).
    strict=False (the build_entity_binding rebuild hook): PER-ROW — good rows
    land, refused rows are LOUDLY reported in the rebuild log and stay on the
    Fix-A floor (reviewer codicil at apply authorization, 2026-08-07: rebuild
    refusals must be loud, never silent). Returns (landed, refused)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = read_tsv(tsv)
        have_pn = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND"
            " name='pn_binding'").fetchone() is not None
        refused, plan, seen = [], [], {}
        for r in rows:
            bk = book_num(r["book"])
            ch, vs, pos = int(r["chapter"]), int(r["verse"]), int(r["position"])
            v = conn.execute(
                "SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
                (r["book"], ch, vs)).fetchone()
            w = conn.execute(
                "SELECT english_head FROM words WHERE verse_id=? AND position=?",
                (v["id"], pos)).fetchone() if v else None
            if not v or not w:
                refused.append((r, "G1 verse/words row missing")); continue
            if compact(w["english_head"]) != compact(r["name"]):
                refused.append((r, f"G1 STALE-NAME: printed "
                                   f"'{w['english_head']}' != '{r['name']}'")); continue
            e = conn.execute("SELECT section FROM tipnr_entities WHERE uniq=?",
                             (r["entity_uniq"],)).fetchone()
            if not e:
                refused.append((r, "G2 entity missing")); continue
            if (e["section"] or "") not in KIND_OK.get(r["referent_kind"], set()):
                refused.append((r, f"G2 KIND: {r['referent_kind']} vs "
                                   f"{e['section']}")); continue
            hits = conn.execute(
                "SELECT name, entity_uniq FROM pn_binding WHERE book=? AND"
                " chapter=? AND verse=? AND render=1",
                (bk, ch, vs)).fetchall() if have_pn else []
            hit = next((h for h in hits
                        if compact(h["name"]) == compact(r["name"])), None)
            if hit:
                refused.append((r, f"G3 PRECEDENCE: verse-grain render bind "
                                   f"exists ({hit['entity_uniq']}) — STOP-AND-LOOK")); continue
            key = (bk, ch, vs, r["entity_uniq"])
            same = "same-referent" in (r["flags"] or "")
            if key in seen and not (same and seen[key]):
                refused.append((r, "G4 DUPLICATE without same-referent flag")); continue
            seen[key] = same
            plan.append((bk, ch, vs, pos, r["name"].lower(), r["entity_uniq"],
                         "slot-ruled", r["evidence_class"], 1, r["flags"]))
        for r, why in refused:
            print(f"  !! REFUSED {r['book']} {r['chapter']}:{r['verse']} "
                  f"p{r['position']} {r['name']}: {why}")
        print(f"slot rulings: {len(plan)} landable, {len(refused)} refused"
              f" of {len(rows)}")
        if not apply:
            print("dry-run only — no write.")
            return len(plan), len(refused)
        if refused and strict:
            print("APPLY REFUSED: guards fired — fix or re-freeze first "
                  "(all-or-nothing at first landing).")
            return 0, len(refused)
        if refused:
            print(f"  !! {len(refused)} slot ruling(s) REFUSED on this rebuild "
                  f"— those slots are back on the Fix-A floor. Open a catch-up "
                  f"ticket; do NOT ignore this.")
        conn.execute("DROP TABLE IF EXISTS pn_slot_binding")
        conn.execute("""CREATE TABLE pn_slot_binding(
            book INTEGER, chapter INTEGER, verse INTEGER, position INTEGER,
            name TEXT, entity_uniq TEXT, kind TEXT, evidence_class TEXT,
            render INTEGER, flags TEXT,
            PRIMARY KEY (book, chapter, verse, position))""")
        conn.executemany(
            "INSERT INTO pn_slot_binding VALUES(?,?,?,?,?,?,?,?,?,?)", plan)
        conn.commit()
        print(f"pn_slot_binding written: {len(plan)} rows.")
        return len(plan), 0
    finally:
        conn.close()


if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else "bible.db"
    land(db, apply="--apply" in sys.argv)
