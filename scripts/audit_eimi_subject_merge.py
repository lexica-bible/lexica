#!/usr/bin/env python3
"""
audit_eimi_subject_merge.py — READ-ONLY. Find the εἰμί ("to be") subject merges the
PN-subject fold missed.

THE SHAPE (memory project_pn_subject_verb_fold is the parent fix). ABP writes a
subject right after its copula and the build glued the whole English onto the verb's
cell, leaving the subject's OWN Greek word as a trailing empty '*' placeholder:

    pos P  : english "Crete shall be"   strongs_base G1510   is_pn 0   <- subject on the verb
    pos P+1: english ""                 strongs_base '*'     is_pn 1   <- the subject's empty slot

The corpus-wide PN-subject fold (fix_pn_subject_merge.py) already split every cell
whose first word is a known tipnr NAME. These εἰμί cells slipped through because the
subject ISN'T in the tipnr roster — but the empty '*' slot is ABP's own proof that a
proper-noun Greek word belongs there. (TODO Issue 4: "David was / Jonah was / Crete
shall be", ~47 in the ABP source. This gets the LIVE still-merged count.)

DETECTION (mirrors fix_pn_subject_merge / audit_pn_placeholder):
  - strongs_base = 'G1510' (every εἰμί form folds to this base), is_pn = 0
  - english is multi-word and its first real word is Capitalized
  - an empty '*' slot sits adjacent (pos+1, or pos-1)
For each it reports the verse, the merged English, whether the empty slot is AFTER
(pos+1, the clean case) or BEFORE, whether the cell is BRACKETED, and whether the
lead word is already a tipnr name (should be ~0 — those were fixed) or a likely
sentence-initial function word (There/And/Then…), which an εἰμί peel must NOT mint
as a name. Writes nothing.

  python3 scripts/audit_eimi_subject_merge.py bible.db
  python3 scripts/audit_eimi_subject_merge.py bible.db --context   # dump a verse window each
"""
import argparse
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fix_pn_subject_merge import _first_word, _empty_star_pos

# Capitalized leads that are sentence-initial English, not proper nouns. An εἰμί peel
# must skip these — they'd mint a bogus clickable "name". Flagged, not silently dropped.
_FUNCTION_LEAD = {
    "the", "a", "an", "and", "then", "but", "so", "now", "for", "yet", "or", "nor",
    "there", "here", "this", "that", "these", "those", "such", "all", "both", "each",
    "he", "she", "it", "they", "we", "you", "i", "who", "what", "when", "where",
    "which", "while", "whose", "him", "her", "his", "their", "its", "my", "your",
    "if", "behold", "yes", "no", "not", "in", "on", "at", "by", "to", "of", "as",
    "how", "why", "thus", "also", "even", "still", "let", "do", "did", "shall",
    "will", "may", "thou", "thee", "ye",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--context", action="store_true",
                    help="print a verse window (positions/greek_pos/bracket_id) per hit")
    args = ap.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    names = set()
    for r in conn.execute("SELECT name FROM tipnr"):
        nm = (r["name"] or "").strip().lower()
        if len(nm) > 1:
            names.add(nm)

    has_is_pn = any(r[1] == "is_pn" for r in conn.execute("PRAGMA table_info(words)"))
    pn_where = " AND w.is_pn = 0" if has_is_pn else ""
    rows = conn.execute(
        f"""SELECT w.verse_id, w.position, v.book, v.chapter, v.verse,
                  w.english, w.strongs, w.strongs_base, w.greek_pos, w.bracket_id
           FROM words w JOIN verses v ON v.id = w.verse_id
           WHERE w.strongs_base = 'G1510' AND w.english LIKE '% %'{pn_where}
           ORDER BY v.id, w.position"""
    ).fetchall()

    hits = []
    for r in rows:
        fw = _first_word(r["english"])
        if not (fw and fw[0].isupper()):
            continue
        slot = _empty_star_pos(conn, r["verse_id"], r["position"])
        if slot is None:
            continue
        epos, ebid = slot
        lead = fw.lower()
        hits.append({
            "ref": f'{r["book"]} {r["chapter"]}:{r["verse"]}',
            "vid": r["verse_id"], "mpos": r["position"], "epos": epos,
            "english": r["english"], "sb": r["strongs_base"],
            "after": epos == r["position"] + 1,
            "bracketed": (r["bracket_id"] is not None or ebid is not None),
            "in_roster": lead in names,
            "func_lead": lead in _FUNCTION_LEAD,
            "lead": fw,
        })

    real = [h for h in hits if not h["func_lead"] and not h["in_roster"]]
    func = [h for h in hits if h["func_lead"]]
    roster = [h for h in hits if h["in_roster"] and not h["func_lead"]]
    bracketed = [h for h in real if h["bracketed"]]
    before = [h for h in real if not h["after"]]

    print(f"εἰμί (G1510) merged cells with an adjacent empty '*' slot: {len(hits)}")
    print(f"  likely REAL non-roster subjects (the Issue-4 scope): {len(real)}")
    print(f"     of those bracketed         : {len(bracketed)}   (need the bracket-aware path)")
    print(f"     of those slot-BEFORE shape : {len(before)}   (rarer; verify before peeling)")
    print(f"  lead already a tipnr name     : {len(roster)}   (should be ~0 — PN fold handled these)")
    print(f"  sentence-initial function lead: {len(func)}   (NOT names — must be skipped)")
    print()

    def dump(title, group):
        if not group:
            return
        print(f"== {title} ({len(group)}) ==")
        for h in sorted(group, key=lambda x: x["ref"]):
            flags = []
            if h["bracketed"]:
                flags.append("BRACKETED")
            if not h["after"]:
                flags.append("slot-BEFORE")
            tag = ("  [" + ",".join(flags) + "]") if flags else ""
            print(f'  {h["ref"]:<14} {h["english"]!r}  lead={h["lead"]!r}{tag}')
            if args.context:
                lo, hi = min(h["mpos"], h["epos"]) - 1, max(h["mpos"], h["epos"]) + 1
                for g in conn.execute(
                        "SELECT position, greek_pos, bracket_id, english, strongs_base"
                        " FROM words WHERE verse_id=? AND position BETWEEN ? AND ?"
                        " ORDER BY position", (h["vid"], lo, hi)):
                    mark = " <- εἰμί cell" if g["position"] == h["mpos"] else (
                           " <- empty * slot" if g["position"] == h["epos"] else "")
                    print(f'       pos {g["position"]:>3}  gpos {str(g["greek_pos"]):>4}  '
                          f'bid {str(g["bracket_id"]):>4}  {g["strongs_base"]:<7} '
                          f'{g["english"]!r}{mark}')
        print()

    dump("REAL non-roster εἰμί subjects — Issue-4 scope", real)
    dump("function-word leads — SKIP these", func)
    dump("lead already a roster name — investigate (PN fold should have caught)", roster)

    conn.close()


if __name__ == "__main__":
    main()
