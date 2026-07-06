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

SCOPE (cert S10, 2026-07-06): the flagged "the" must belong to THIS noun, not the
FOLLOWING word. Two guards were added after the clean-text match (see find_flips):
proper-noun runs like Jer 48:1 ("…of the forces, the God…") read in CORRECT source
order, but the un-scoped detector paired (forces, the) because "the forces" appears
elsewhere — while that "the" is GOD's article. Cert Session 9's independent oracle
(v2 rows-vs-verses.text) caught the un-scoped detector corrupting 175 such verses.

CONTROL: this detector's 0 is only trustable once it is proven it CAN fire —
  python3 scripts/audit_split_flip.py --control
runs a built-in genuine "LORD the" positive (must FIRE) and the Jer 48:1 false
positive (must stay QUIET). Run it before trusting a 0 on the real corpus.

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
            if not (good and not bad):
                continue
            # SCOPE (cert S10, 2026-07-06): the determiner must belong to THIS noun,
            # not the FOLLOWING word. Without this the proper-noun run over-fires —
            # Jer 48:1 "…of the forces, the God…" is CORRECT source order, but the
            # detector paired (forces, the) because "the forces" appears elsewhere,
            # while that "the" is GOD's article. Two guards, either one skips:
            #   forward  — "the" forms "<det> <next word>" in the clean text (its
            #              real owner is the following slot)
            #   backward — the noun already has a determiner right in front of it, so
            #              its article is placed and this "the" isn't its
            nxt = slots[i + 2] if i + 2 < len(slots) else None
            if nxt is not None and nxt["english"]:
                nh = first_tok(nxt["english"])
                if nh and re.search(rf"\b{det}\s+{nh.lower()}\b", clean_l):
                    continue
            if i - 1 >= 0 and slots[i - 1]["english"]:
                ptoks = re.findall(r"[A-Za-z]+", slots[i - 1]["english"])
                if ptoks and ptoks[-1].lower() in DETERMINERS:
                    continue
            flips.append({
                "vid": vid, "ref": f"{book} {ch}:{vs}",
                "noun_pos": a["position"], "det_pos": b["position"],
                "noun": noun, "det": det,
                "stored": f"{ae} {be}", "clean_has": f"{det} {noun}",
            })
    return flips


def _control():
    """Prove the scoped detector CAN fire (and stays quiet on the Jer 48:1 false-
    positive class) BEFORE any 0 on the real corpus is trusted. Builds two in-memory
    fixtures — no bible.db. Returns True only if the positive fires AND the negative
    stays quiet."""
    def mk(text, words):
        c = sqlite3.connect(":memory:")
        c.execute("CREATE TABLE verses(id INTEGER, book TEXT, chapter INT, verse INT, text TEXT)")
        c.execute("CREATE TABLE words(verse_id INT, position INT, english TEXT, "
                  "strongs_base TEXT, bracket_id INT)")
        c.execute("INSERT INTO verses VALUES(1,'Ctl',1,1,?)", (text,))
        for p, e, sb, bid in words:
            c.execute("INSERT INTO words VALUES(1,?,?,?,?)", (p, e, sb, bid))
        c.commit()
        return c

    # POSITIVE — genuine strand: stored "LORD the", clean "the LORD" → MUST fire.
    pos = mk("the LORD will command his mercy in the day.",
             [(0, "LORD", "G2962", None), (1, "the", "G3588", None),
              (2, "will command", "G1781", None), (3, "his", "G846", None),
              (4, "mercy", "G1656", None)])
    # NEGATIVE — Jer 48:1 clean order "…of the forces, the God…" (the 'the' is God's)
    #            → MUST stay quiet.
    neg = mk("To Moab, thus said the LORD of the forces, the God of Israel.",
             [(4, "the LORD", "G2962", None), (5, "of the", "G3588", None),
              (6, "forces,", "G1411", None), (7, "the", "G3588", None),
              (8, "God", "G2316", None), (9, "of Israel.", "H3478", None)])
    fired = len(find_flips(pos)) > 0
    quiet = len(find_flips(neg)) == 0
    print("split-flip detector CONTROL:")
    print(f"  positive (genuine 'LORD the')       : {'FIRED' if fired else 'MISSED !!'}")
    print(f"  negative (Jer 48:1 forward 'the God'): {'QUIET' if quiet else 'FLAGGED !!'}")
    ok = fired and quiet
    print(f"  => {'PASS — a 0 on the corpus is trustable.' if ok else 'FAIL — do NOT trust a 0.'}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db", nargs="?", help="path to bible.db (omit with --control)")
    ap.add_argument("--list", action="store_true", help="print every flipped verse")
    ap.add_argument("--control", action="store_true",
                    help="run the built-in known-positive/negative control and exit")
    args = ap.parse_args()

    if args.control:
        raise SystemExit(0 if _control() else 1)
    if not args.db:
        ap.error("db is required unless --control is given")

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
