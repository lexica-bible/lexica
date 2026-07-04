#!/usr/bin/env python3
"""
lint_split_wrong_slot.py — full-corpus wrong-slot certification for _split_compounds.

The 60-verse spread said FREEZE (0 content-word wrong-slot). This lint proves the
other ~12,632 split-affected verses the sample didn't touch: after the REAL split
runs, every content slot's english_head must sit on a Greek word whose meaning
matches. A content word landing on the wrong Strong's number is the phrase-boundary
poison class — it corrupts the "renders as" data every consumer reads. This flags
exactly that, corpus-wide.

READ-ONLY: opens bible.db read-only (reference glosses only), reads the ABP source +
bh_scrape.db, writes nothing to any table. Reuses build_words_from_abp's real split
(no re-implementation, can't drift).

── Reference gloss + its circularity limit (design requirement #1) ──
The split PLACES a gloss word on a slot when that word is in the slot's lexicon
definition (kjv_def + strongs_def). Checking english_head against that SAME lexicon
therefore passes every slot the split matched — INCLUDING a loose ("leaky") match
that placed the wrong word. So this lint is NOT fully independent: it certifies the
non-leaky bulk trivially and CATCHES the leaky-path failures — a word that drifted
onto a slot via the fingerprint passes (_fix_backwards_pairing, _funcword_noun_relocate,
_split_pn_article_lump), the front-swap order, or a def that only loosely contained it.
That IS the known failure class, so the lint is not worthless; the limit is stated so
no one reads a clean run as full independence.

Fuller independence would use Strong's/Dodson glosses (word_gloss table) as the
reference instead. Evaluated and REJECTED as not-cheap: Dodson glosses are LEMMA-form
English ("bear", "say", "give") while english_head is the INFLECTED rendering ("bore",
"said", "gives"), so a direct match false-positives on nearly every verb — it would
drown the real signal. The split's own KJV-rendering-rich lexicon is inflection-aware,
which is why it's the usable reference here.

The of-on-pronoun softness (a bare function word on a pronoun/article slot) is an
ACCEPTED limit (parse_abp.SPLIT_FUNCWORD_SLOT_CAVEAT), and it is invisible to this
lint by construction: english_head is None for an all-function gloss, and this lint
only checks slots that HAVE a content english_head.

Run on PA:
    python3 scripts/lint_split_wrong_slot.py bible.db bh_scrape.db --control   # must pass
    python3 scripts/lint_split_wrong_slot.py bible.db bh_scrape.db             # full pass
"""
import argparse
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_words_from_abp as B

_PUNCT = re.compile(r"[^\w]")


def _fold(w):
    """lowercase, strip punctuation, singularize — match english_head to a gloss word."""
    w = _PUNCT.sub("", (w or "").lower())
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _folded_lex(lex):
    """{bare_base: set(folded gloss words)} from the split's own lexicon reference."""
    return {base: {_fold(w) for w in words if w} for base, words in lex.items()}


def _explained(head, base, lexf):
    """None = no reference gloss for this number (can't judge). True = english_head is in
    the number's gloss. False = it is NOT (a wrong-slot candidate)."""
    words = lexf.get(base)
    if not words:
        return None
    hf = _fold(head)
    if not hf:
        return None
    if hf in words:
        return True
    # stem tolerance for compounds/inflection ("garment(s)", "wilder(ness)")
    for w in words:
        if len(hf) >= 4 and len(w) >= 4 and (w.startswith(hf) or hf.startswith(w)):
            return True
    return False


def check_verse(rows, lexf, ref):
    """Flag every content slot whose english_head does NOT match its Greek word.
    rows = build_verse_words output (12-wide): [2]=english_head, [4]=strongs_base (BARE)."""
    flags, unref = [], 0
    for r in rows:
        head, base = r[2], r[4]
        if not head:                                   # function-only slot → no head, skip
            continue
        if not base or not base[0].isdigit():          # '*' / '' / already excluded
            continue
        verdict = _explained(head, base, lexf)
        if verdict is None:
            unref += 1
        elif verdict is False:
            flags.append((ref, r[0], head, base))
    return flags, unref


def _build_one(abbrev, ch, vs, bh_index, lex, rahlfs, tagnt):
    """Run the real per-verse pipeline for ONE verse; return its post-split rows."""
    for a, c, v, abp_words in B.iter_verses(*B._abp_sources()):
        if (a, c, v) != (abbrev, ch, vs):
            continue
        slug = B.ABBREV_TO_SLUG.get(a)
        bh_rows = bh_index.get((slug, c, v), []) if slug else []
        src = bnum = None
        if rahlfs and rahlfs.booknum(a):
            src, bnum = rahlfs, rahlfs.booknum(a)
        elif tagnt and tagnt.booknum(a):
            src, bnum = tagnt, tagnt.booknum(a)
        if src:
            corrs = B.correct_verse([w[1] for w in abp_words],
                                    src.verse(bnum, c, v), [w[0] for w in abp_words])
            abp_words = B.apply_pronoun_corrections(abp_words, corrs, [], f"{a} {c}:{v}")
        return B.build_verse_words(abp_words, bh_rows, lex)
    return None


def run_control(lexf, bh_index, lex, rahlfs, tagnt):
    """Per the control-test rule: fire the lint at a known-GOOD verse (must pass) and a
    hand-BROKEN one (must flag). The zero isn't trusted until the pattern draws blood."""
    ref = ("Gen", 27, 27)                              # all content slots matched in the spread
    rows = _build_one(*ref, bh_index, lex, rahlfs, tagnt)
    if not rows:
        print("CONTROL ERROR: could not build Gen 27:27"); return False
    tag = f"{ref[0]} {ref[1]}:{ref[2]}"

    good_flags, _ = check_verse(rows, lexf, tag)
    print(f"  known-good {tag}: {len(good_flags)} flag(s)  (expect 0)")
    for f in good_flags:
        print(f"      unexpected flag: pos {f[1]} {f[2]!r} on {f[3]}")

    # hand-break: swap the english+head of two content slots that sit on DIFFERENT numbers
    content = [i for i, r in enumerate(rows)
               if r[2] and r[4] and r[4][0].isdigit() and _explained(r[2], r[4], lexf) is True]
    if len(content) < 2:
        print("CONTROL ERROR: fewer than 2 checkable content slots to swap"); return False
    a, b = content[0], content[1]
    broken = list(rows)
    ra, rb = list(broken[a]), list(broken[b])
    ra[1], ra[2], rb[1], rb[2] = rb[1], rb[2], ra[1], ra[2]   # swap english + english_head
    broken[a], broken[b] = tuple(ra), tuple(rb)
    bad_flags, _ = check_verse(broken, lexf, tag + " [BROKEN]")
    print(f"  hand-broken {tag}: swapped {rows[a][2]!r}<{rows[a][4]}> <-> "
          f"{rows[b][2]!r}<{rows[b][4]}>  -> {len(bad_flags)} flag(s)  (expect >=1)")

    ok = (len(good_flags) == 0 and len(bad_flags) >= 1)
    print(f"\n  CONTROL {'PASSED' if ok else 'FAILED'}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bible_db", nargs="?", default="bible.db")
    ap.add_argument("scrape_db", nargs="?", default="bh_scrape.db")
    ap.add_argument("--control", action="store_true", help="run the control test and exit")
    ap.add_argument("--out", default="split_wrong_slot_flags.tsv")
    args = ap.parse_args()

    ro = sqlite3.connect(f"file:{args.bible_db}?mode=ro", uri=True)
    lex = B.load_lexicon(ro)
    ro.close()
    lexf = _folded_lex(lex)
    print(f"reference gloss numbers: {len(lexf):,}")

    scrape = sqlite3.connect(args.scrape_db)
    bh_index = B.load_bh_verse_index(scrape)
    scrape.close()

    rahlfs = tagnt = None
    if B.RahlfsLXX and B.RAHLFS_DIR.is_dir():
        rahlfs = B.RahlfsLXX(B.RAHLFS_DIR); print("Rahlfs: loaded")
    else:
        print("Rahlfs: NOT found — OT input will differ from production")
    if B.TAGNTSource and all(p.is_file() for p in B.TAGNT_FILES):
        tagnt = B.TAGNTSource([str(p) for p in B.TAGNT_FILES]); print("TAGNT: loaded")
    else:
        print("TAGNT: NOT found — NT input will differ from production")

    if args.control:
        sys.exit(0 if run_control(lexf, bh_index, lex, rahlfs, tagnt) else 1)

    # ── full pass: check only split-AFFECTED verses (scope the verdict to the split) ──
    real_split = B._split_compounds
    affected = {"hit": False}

    def wrapped(rows, lexicon, carry=False):
        before = sum(1 for r in rows if (r[1] or "").strip())
        real_split(rows, lexicon, carry)
        after = sum(1 for r in rows if (r[1] or "").strip())
        affected["hit"] = affected["hit"] or (after > before)
    B._split_compounds = wrapped

    flags, checked_verses, unref_total = [], 0, 0
    for abbrev, ch, vs, abp_words in B.iter_verses(*B._abp_sources()):
        slug = B.ABBREV_TO_SLUG.get(abbrev)
        bh_rows = bh_index.get((slug, ch, vs), []) if slug else []
        src = bnum = None
        if rahlfs and rahlfs.booknum(abbrev):
            src, bnum = rahlfs, rahlfs.booknum(abbrev)
        elif tagnt and tagnt.booknum(abbrev):
            src, bnum = tagnt, tagnt.booknum(abbrev)
        if src:
            corrs = B.correct_verse([w[1] for w in abp_words],
                                    src.verse(bnum, ch, vs), [w[0] for w in abp_words])
            abp_words = B.apply_pronoun_corrections(abp_words, corrs, [], f"{abbrev} {ch}:{vs}")
        affected["hit"] = False
        rows = B.build_verse_words(abp_words, bh_rows, lex)
        if not affected["hit"]:
            continue
        checked_verses += 1
        f, unref = check_verse(rows, lexf, f"{abbrev} {ch}:{vs}")
        flags.extend(f)
        unref_total += unref

    print("\n── wrong-slot certification (split-affected verses) ──")
    print(f"  verses checked:        {checked_verses:,}")
    print(f"  content slots unref:   {unref_total:,}  (no reference gloss — not judged)")
    print(f"  WRONG-SLOT FLAGS:      {len(flags):,}")

    Path(args.out).write_text(
        "ref\tposition\tenglish_head\tstrongs_base\n" +
        "\n".join(f"{r}\t{p}\t{h}\t{b}" for r, p, h, b in flags), encoding="utf-8")
    print(f"  full flag list -> {args.out}")

    if flags:
        print("\n  first 40 flags (english_head on a number whose gloss doesn't contain it):")
        for r, p, h, b in flags[:40]:
            print(f"    {r}  pos {p}  {h!r} on {b}")
    else:
        print("\n  CLEAN — every content slot's english_head matches its Greek word.")
        print("  Freeze-as-overlay is CERTIFIED corpus-wide (within the reference's circularity limit).")


if __name__ == "__main__":
    main()
