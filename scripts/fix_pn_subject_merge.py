#!/usr/bin/env python3
"""
fix_pn_subject_merge.py — split a subject NAME back off the verb it was merged
onto, corpus-wide, so the name is its own clickable word carrying its own number.

THE DEFECT (diagnosis: memory project_pn_subject_verb_fold). Where ABP writes a
subject name right after its verb, its source reads, flat and unbracketed, e.g.
    David tookG2983 G*
ABP put the English in reading order ("David took"), tagged the verb with its
number (G2983), and floated the name's OWN Greek word as a trailing bare "G*"
(a proper-noun placeholder, no English of its own). Our build glued the whole
"David took" onto the verb's cell and left the G* slot empty:

    pos P  : english "David took"   strongs G2983   is_pn 0   <- name on the verb
    pos P+1: english ""             strongs '*'     is_pn 1   <- David's empty slot

So clicking "David took" opens the verb (G2983), and the name is untagged —
import_tipnr never resolves the empty slot (it only fills '*' words that already
have English).

THE FIX. The two slots are adjacent (audit_pn_placeholder proved it: an empty '*'
sits at P+1, or P-1 in a few). Put the name on the LOWER position and the verb on
the HIGHER one, so both reading modes show "David took" (name first), exactly as
the ABP source prints it:

    lower  pos: english "David"   strongs '*'    is_pn 1   <- import_tipnr fills the number
    higher pos: english "took"    strongs G2983  is_pn 0   <- verb keeps its number/lemma

Positions never shift (two in-place rewrites, no inserts), so nothing downstream
moves. No bracket is added: the source itself is unbracketed, and with both slots
bracket-free, chip mode (Greek/position order) and prose (English order) both read
"David took". The verb's printed-Greek "in this verse" line re-attaches by Strong's
on the next build_abp_surface run, and the name slot is a '*' (surface skips those).

WHY this differs from the LORD-oath / pronoun folds (which leave the verb FIRST in
chip): those mirror ABP's OWN bracket-reordered cases. These flat cells are NOT
reordered in the source — ABP prints them name-first — so we keep name-first.

SCOPE / SAFETY:
  - Detection is identical to scripts/audit_pn_placeholder.py (tipnr name roster,
    is_pn=0 multi-word real-number cell whose first word is a name, with an
    adjacent empty '*' slot) — so the count matches that audit (~2,300).
  - A merged cell (or its empty slot) that sits INSIDE a bracket is SKIPPED and
    reported — reordering a bracket member is delicate and handled separately.
  - The 634 no-slot cases are never touched (no adjacent empty slot to fill).
  - Read-only by default; --apply writes. Each fix only fires while the cell still
    looks merged, so re-running is safe (already-split rows are skipped).

AFTER --apply, on PA, re-run in order:
  python3 scripts/import_tipnr.py bible.db            # resolve the new '*' name slots
  python3 scripts/build_abp_surface.py bible.db --bh bh_scrape.db   # re-align Greek forms
  python3 scripts/build_abp_translit.py bible.db                    # and their translit

  python3 scripts/fix_pn_subject_merge.py bible.db            # dry run (default)
  python3 scripts/fix_pn_subject_merge.py bible.db --apply    # write changes
"""
import argparse
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_abp import _head_word


def _first_word(eng):
    """First real word of a gloss, ignoring leading brackets/quotes/spaces."""
    if not eng:
        return None
    s = eng.lstrip("[(\"'“‘ \t")
    m = re.match(r"[A-Za-z][A-Za-z'\-]*", s)
    return m.group(0) if m else None


# Roster names that LEAD a cell but are NOT a verb-subject here — a place/gentilic
# heading a non-verb phrase ("On account of this" = the preposition διά; "Hebrew
# servant" = adjective+noun). Excluded so we don't mint a bogus clickable name.
_NOT_SUBJECT = {"on", "hebrew"}


def _peel_name(eng, names):
    """Split a merged cell into (name_part, verb_part). Peels the LONGEST leading
    run of words that forms a roster name (most names are one word), leaving at
    least one word for the verb. Returns None if it can't split cleanly."""
    toks = eng.split()
    if len(toks) < 2:
        return None
    best = 0
    for k in range(1, len(toks)):                      # keep >=1 word for the verb
        cand = " ".join(toks[:k]).lower().strip(".,;:!?'\"")
        if cand in names:
            best = k
    if best == 0:
        fw = _first_word(eng)
        if not (fw and fw.lower() in names):
            return None
        best = 1
    # Trim trailing punctuation off the name so it matches the metaV name lookup
    # ("Moses," -> "Moses"); the canonical prose keeps the real punctuation.
    name_part = " ".join(toks[:best]).rstrip(".,;:!?'\"")
    verb_part = " ".join(toks[best:])
    if not name_part.strip() or not verb_part.strip():
        return None
    if name_part.lower() in _NOT_SUBJECT:
        return None
    return name_part, verb_part


def _empty_star_pos(conn, vid, pos):
    """Return the adjacent empty '*' slot's (position, bracket_id): try pos+1 then
    pos-1. None if neither is an empty proper-noun placeholder."""
    for p in (pos + 1, pos - 1):
        r = conn.execute(
            "SELECT position, bracket_id FROM words"
            " WHERE verse_id=? AND position=? AND strongs_base='*'"
            "   AND (english IS NULL OR trim(english)='')",
            (vid, p),
        ).fetchone()
        if r:
            return r[0], r[1]
    return None


def run(conn, apply=False, log=print):
    # Self-contained for both callers (the CLI here AND the build fold in
    # build_words_from_abp.py): set our own row mode, and only write is_pn if the
    # column exists yet (a fresh rebuild adds it later, in import_tipnr).
    conn.row_factory = sqlite3.Row
    has_is_pn = any(r[1] == "is_pn" for r in conn.execute("PRAGMA table_info(words)"))
    pn1 = ", is_pn=1" if has_is_pn else ""
    pn0 = ", is_pn=0" if has_is_pn else ""

    names = set()
    for r in conn.execute("SELECT name FROM tipnr"):
        nm = (r["name"] or "").strip().lower()
        if len(nm) > 1:
            names.add(nm)
    log(f"Known proper-noun names: {len(names):,}\n")

    # On a fresh rebuild is_pn doesn't exist yet (import_tipnr adds it after); the
    # real-number + name checks already exclude resolved names, so drop the filter then.
    pn_where = " AND w.is_pn = 0" if has_is_pn else ""
    rows = conn.execute(
        f"""SELECT w.verse_id, w.position, v.book, v.chapter, v.verse,
                  w.english, w.strongs, w.strongs_base, w.greek_pos, w.bracket_id,
                  w.italic, w.italic_words, w.smcap_words, w.morph, w.lemma
           FROM words w JOIN verses v ON v.id = w.verse_id
           WHERE w.english LIKE '% %'
             AND w.strongs_base GLOB '[GH][0-9]*'{pn_where}
           ORDER BY v.id, w.position"""
    ).fetchall()

    fixed = 0
    skipped_bracket = 0
    skipped_split = 0
    no_slot = 0
    by_name = {}

    for r in rows:
        fw = _first_word(r["english"])
        if not (fw and fw[0].isupper() and fw.lower() in names):
            continue
        vid, mpos = r["verse_id"], r["position"]
        slot = _empty_star_pos(conn, vid, mpos)
        if slot is None:
            no_slot += 1
            continue
        epos, ebid = slot
        # Both the merged cell and its empty slot must be bracket-free — a bracket
        # member needs its greek_pos relationships preserved (handled separately).
        if r["bracket_id"] is not None or ebid is not None:
            skipped_bracket += 1
            continue
        split = _peel_name(r["english"], names)
        if split is None:
            skipped_split += 1
            continue
        name_part, verb_part = split

        lower_pos, higher_pos = sorted((mpos, epos))
        ref = f'{r["book"]} {r["chapter"]}:{r["verse"]}'
        by_name.setdefault(name_part, []).append(
            f'   {ref:<14} {r["strongs_base"]:<7} {r["english"]!r}'
            f'  ->  {name_part!r} (*) + {verb_part!r}')

        if apply:
            # name -> the LOWER position: a fresh '*' proper-noun slot for import_tipnr
            conn.execute(
                "UPDATE words SET english=?, english_head=?, strongs='*', strongs_base='*',"
                " greek_pos=NULL, bracket_id=NULL, italic=0, italic_words='', smcap_words='',"
                f" morph=NULL, lemma=NULL{pn1} WHERE verse_id=? AND position=?",
                (name_part, _head_word(name_part), vid, lower_pos),
            )
            # verb -> the HIGHER position: keeps the merged cell's number + lemma/morph
            conn.execute(
                "UPDATE words SET english=?, english_head=?, strongs=?, strongs_base=?,"
                " greek_pos=?, bracket_id=?, italic=?, italic_words=?, smcap_words=?,"
                f" morph=?, lemma=?{pn0} WHERE verse_id=? AND position=?",
                (verb_part, _head_word(verb_part), r["strongs"], r["strongs_base"],
                 r["greek_pos"], r["bracket_id"], r["italic"], r["italic_words"],
                 r["smcap_words"], r["morph"], r["lemma"], vid, higher_pos),
            )
        fixed += 1

    for nm in sorted(by_name, key=lambda n: (-len(by_name[n]), n)):
        items = by_name[nm]
        log(f"── {nm}  ({len(items)})")
        for line in items:
            log(line)

    log(f"\nWould split {fixed:,} merged name(s) across {len(by_name):,} names.")
    log(f"  skipped (bracketed cell/slot): {skipped_bracket:,}  <- handled separately")
    log(f"  skipped (couldn't peel name) : {skipped_split:,}")
    log(f"  no adjacent empty slot       : {no_slot:,}  <- left alone (correct as-is)")
    return fixed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--apply", action="store_true", help="write changes (default = dry run)")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    n = run(conn, apply=args.apply)
    if args.apply:
        conn.commit()
        print(f"\nApplied: split {n:,} merged name(s).")
        print("Now re-run on PA: import_tipnr.py, then build_abp_surface.py + build_abp_translit.py.")
    else:
        print("\nDRY RUN — nothing written. Re-run with --apply once the splits look right.")
    conn.close()


if __name__ == "__main__":
    main()
