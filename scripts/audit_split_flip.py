#!/usr/bin/env python3
"""
audit_split_flip.py — READ-ONLY. Find every verse where the build's compound-gloss
split (_split_compounds in build_words_from_abp.py) baked a "the/a + noun" pair into
the words table in the WRONG order — a determiner left sitting AFTER its noun
("LORD the") when the clean verse text reads the other way ("the LORD").

This is the Psa 42:8 class. ABP attaches a whole phrase ("the LORD gives charge to")
to one Greek word with blank Greek slots after it; the build spreads the extra words
onto those slots and fronts them, but lines them up in GREEK order — so the article
lands after its noun. The clean prose in verses.text keeps the right order, which is
why the in-text search (which reads verses.text) can never surface "LORD the".

DETECTION (no source files needed — measures what's actually baked in now):
  walk adjacent NON-bracketed word slots a,b in reading order. Flag when
    - b is a bare determiner slot (the/a/an/his/her/its/their/my/your/our), real number
    - a is a single content word (a name/noun, not itself a determiner/function word)
    - i.e. stored order is "<noun> <determiner>"
    - AND the clean verses.text has "<determiner> <noun>" (correct) and NOT the flip.
  Bracketed slots are skipped — those are ABP's own reorders (a separate decision).

READ-ONLY (opens the DB mode=ro). Never writes. Run on PA from the repo root:
  python3 scripts/audit_split_flip.py bible.db
  python3 scripts/audit_split_flip.py bible.db --list      # full per-verse list

Re-run after the build fix: the count must drop to 0.
"""
import argparse
import re
import sqlite3
from collections import defaultdict

DETERMINERS = {
    "the", "a", "an",
    "his", "her", "its", "their", "my", "your", "our",
}
# Words that are never the "noun" half of a flipped pair (so we don't flag "to the",
# "of a", "and the" — a determiner after one of these is normal English, not a flip).
_NOT_NOUN = {
    "the", "a", "an", "his", "her", "its", "their", "my", "your", "our",
    "of", "to", "in", "by", "for", "with", "from", "at", "on", "and", "or",
    "but", "as", "so", "not", "is", "are", "was", "were", "be", "o", "i",
}

_W = re.compile(r"[A-Za-z]+")


def norm(s):
    return (s or "").strip().lower()


def first_tok(s):
    m = _W.search(s or "")
    return m.group(0) if m else None


def find_flips(conn):
    """READ-ONLY detection, shared by the audit CLI here AND scripts/fix_split_flip.py
    so the two can never drift. Returns one dict per stranded determiner:
        {vid, ref, noun_pos, det_pos, noun, det, stored, clean_has}
    noun_pos / det_pos are the words.position values of the two slots to swap."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT v.id AS vid, v.book, v.chapter, v.verse, v.text AS clean,
                  w.position, w.english, w.strongs_base, w.bracket_id
           FROM verses v JOIN words w ON w.verse_id = v.id
           ORDER BY v.id, w.position"""
    ).fetchall()

    by_verse = defaultdict(list)
    meta = {}
    for r in rows:
        by_verse[r["vid"]].append(r)
        meta.setdefault(r["vid"], (r["book"], r["chapter"], r["verse"], r["clean"]))

    flips = []
    for vid, slots in by_verse.items():
        book, ch, vs, clean = meta[vid]
        clean_l = (clean or "").lower()
        for i in range(len(slots) - 1):
            a, b = slots[i], slots[i + 1]
            # both must be plain (non-bracketed) and carry real glosses
            if a["bracket_id"] is not None or b["bracket_id"] is not None:
                continue
            ae, be = a["english"], b["english"]
            if not ae or not be:
                continue
            det = norm(be)
            if det not in DETERMINERS:
                continue
            # the determiner slot should be a single bare word with a real number
            if " " in be.strip() or not b["strongs_base"] or b["strongs_base"] in ("*", ""):
                continue
            noun = first_tok(ae)
            # noun half: a single content token, not itself a determiner/function word
            if not noun or " " in ae.strip() or noun.lower() in _NOT_NOUN:
                continue
            nl = noun.lower()
            # clean text must read "<det> <noun>" (correct) and not "<noun> <det>"
            good = re.search(rf"\b{det}\s+{nl}\b", clean_l)
            bad = re.search(rf"\b{nl}\s+{det}\b", clean_l)
            if good and not bad:
                flips.append({
                    "vid": vid, "ref": f"{book} {ch}:{vs}",
                    "noun_pos": a["position"], "det_pos": b["position"],
                    "noun": noun, "det": det,
                    "stored": f"{ae} {be}", "clean_has": f"{det} {noun}",
                })
    return flips


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--list", action="store_true", help="print every flipped verse")
    args = ap.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    flips = find_flips(conn)
    conn.close()

    print(f"READ-ONLY split-flip audit -> {args.db}")
    print(f"  flipped 'the/a + noun' pairs baked in the words table: {len(flips)}")
    by_pair = defaultdict(int)
    for f in flips:
        by_pair[(f["det"], f["noun"])] += 1
    print(f"  distinct verses: {len(set(f['ref'] for f in flips))}\n")
    print("  top flipped pairs (stored order):")
    for (det, noun), n in sorted(by_pair.items(), key=lambda kv: -kv[1])[:25]:
        print(f"    {n:>4}  '{noun} {det}'  (clean: '{det} {noun}')")
    if args.list:
        print("\n  --- every flipped verse ---")
        for f in sorted(flips, key=lambda f: f["ref"]):
            print(f'    {f["ref"]:<14} stored "{f["stored"]}"  clean has "{f["clean_has"]}"')
    else:
        print("\n  (run with --list for the full per-verse list)")


if __name__ == "__main__":
    main()
