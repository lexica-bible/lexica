#!/usr/bin/env python3
"""
lint_split_wrong_slot.py — full-corpus wrong-slot certification for _split_compounds.

The 60-verse spread said FREEZE (0 content-word wrong-slot). This lint proves the
other ~12,632 split-affected verses the sample didn't touch: a content word landing
on the wrong Strong's number is the phrase-boundary poison class — it corrupts the
"renders as" data every consumer reads. This flags exactly that, corpus-wide.

READ-ONLY: opens bible.db read-only (unused beyond a handle check), reads the ABP
source + bh_scrape.db, writes nothing to any table. Reuses build_words_from_abp's
real split (no re-implementation, can't drift).

── Reference = the corpus's OWN attested renderings (not a lexicon) ──
First try used the split's KJV-based lexicon as the reference. Its CONTROL FAILED (4
false flags on a known-good verse): ABP does not speak KJV's vocabulary — ὀσμή/3744 is
"savour/odour" in KJV but ABP renders it "scent"; ἔπω/2036 is "say" but ABP renders
"said". A correctly-placed word was flagged just for being ABP's wording. Any external
lexicon (KJV or Dodson) has this vocabulary gap and drowns the signal.

So the reference is ABP itself: {strongs_base -> how often each english_head renders
it, across the WHOLE corpus}. A wrong-slot word is a ONE-OFF rendering of an otherwise
FREQUENT number — "kissed" appearing once on 3744 (rendered "scent" everywhere else)
stands out; "scent" on 3744 does not, because it is the number's normal rendering. This
speaks ABP's vocabulary because it IS ABP's vocabulary.

CIRCULARITY LIMIT (stated so a clean run isn't misread): the renderings are the split's
own output, so this catches only RARE, one-off misplacements (the leaky-path class). A
SYSTEMATIC mis-placement repeated on many verses would make its wrong rendering common
and hide it — that is a different audit. The independent leg is the 60-verse BibleHub
cross-check; this is the completeness leg over the ~12,632 the sample missed.

The of-on-pronoun softness (a bare function word on a pronoun/article slot) is an
ACCEPTED limit (parse_abp.SPLIT_FUNCWORD_SLOT_CAVEAT), invisible here by construction:
english_head is None for an all-function gloss, and only content-head slots are checked.

Run on PA:
    python3 scripts/lint_split_wrong_slot.py bible.db bh_scrape.db --control   # must pass
    python3 scripts/lint_split_wrong_slot.py bible.db bh_scrape.db             # full pass
"""
import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_words_from_abp as B

_PUNCT = re.compile(r"[^\w]")

SINGLETON = 1      # a rendering used this many times or fewer for a number = one-off
MIN_FREQ  = 8      # ...is only suspicious when the NUMBER itself is well-attested


def _fold(w):
    """lowercase, strip punctuation, singularize — one rendering key per english_head."""
    w = _PUNCT.sub("", (w or "").lower())
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _content_slots(rows):
    """Yield (position, english_head, strongs_base) for every content slot — a slot with a
    real content english_head on a numbered Greek word. Function-only slots (head None),
    '*' and blank bases are skipped, so the of-on-pronoun softness never reaches here."""
    for r in rows:
        head, base = r[2], r[4]
        if not head or not base or not base[0].isdigit():
            continue
        hf = _fold(head)
        if hf:
            yield r[0], hf, base


def _flag_slots(rows, counts, totals, ref):
    """Flag a content slot whose (number, rendering) is a one-off for a well-attested number."""
    out = []
    for pos, hf, base in _content_slots(rows):
        if totals.get(base, 0) >= MIN_FREQ and counts[base].get(hf, 0) <= SINGLETON:
            out.append((ref, pos, hf, base))
    return out


def _iter_built(bh_index, lex, rahlfs, tagnt, want_affected):
    """Run the real per-verse pipeline over the whole corpus. Yields (ref, rows, affected)
    for every verse; `affected` True when _split_compounds actually filled a slot there."""
    real_split = B._split_compounds
    flag = {"hit": False}

    def wrapped(rows, lexicon, carry=False):
        before = sum(1 for r in rows if (r[1] or "").strip())
        real_split(rows, lexicon, carry)
        flag["hit"] = flag["hit"] or (sum(1 for r in rows if (r[1] or "").strip()) > before)
    if want_affected:
        B._split_compounds = wrapped

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
        flag["hit"] = False
        rows = B.build_verse_words(abp_words, bh_rows, lex)
        yield f"{abbrev} {ch}:{vs}", rows, flag["hit"]


def _build_counts_and_stash(bh_index, lex, rahlfs, tagnt):
    """One pass: tally every number's renderings across the WHOLE corpus (the reference),
    and stash the rows of split-AFFECTED verses (the ones we then certify)."""
    counts = defaultdict(Counter)
    totals = Counter()
    affected = []
    for ref, rows, is_aff in _iter_built(bh_index, lex, rahlfs, tagnt, want_affected=True):
        for _pos, hf, base in _content_slots(rows):
            counts[base][hf] += 1
            totals[base] += 1
        if is_aff:
            affected.append((ref, rows))
    return counts, totals, affected


def run_control(counts, totals, affected):
    """Control-test rule: fire at a known-GOOD verse (must pass) + a hand-BROKEN one (must
    flag). The zero isn't trusted until the pattern draws blood."""
    good = next((r for r in affected if r[0] == "Gen 27:27"), None)
    if not good:
        print("CONTROL ERROR: Gen 27:27 not in the affected set"); return False
    ref, rows = good

    good_flags = _flag_slots(rows, counts, totals, ref)
    print(f"  known-good {ref}: {len(good_flags)} flag(s)  (expect 0)")
    for f in good_flags:
        print(f"      unexpected flag: pos {f[1]} {f[2]!r} on {f[3]}")

    # hand-break: swap english+head of the two content slots on the MOST frequent numbers,
    # so both become never-before-seen renderings of well-attested numbers -> must flag.
    cont = sorted(((i, r) for i, r in enumerate(rows)
                   if r[2] and r[4] and r[4][0].isdigit() and totals.get(r[4], 0) >= MIN_FREQ),
                  key=lambda ir: -totals.get(ir[1][4], 0))
    if len(cont) < 2:
        print("CONTROL ERROR: fewer than 2 frequent-number content slots to swap"); return False
    (ia, ra), (ib, rb) = cont[0], cont[1]
    broken = list(rows)
    la, lb = list(ra), list(rb)
    la[1], la[2], lb[1], lb[2] = lb[1], lb[2], la[1], la[2]     # swap english + english_head
    broken[ia], broken[ib] = tuple(la), tuple(lb)
    bad_flags = _flag_slots(broken, counts, totals, ref + " [BROKEN]")
    print(f"  hand-broken {ref}: swapped {ra[2]!r}<{ra[4]}> <-> {rb[2]!r}<{rb[4]}>  "
          f"-> {len(bad_flags)} flag(s)  (expect >=1)")

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

    import sqlite3
    ro = sqlite3.connect(f"file:{args.bible_db}?mode=ro", uri=True)
    lex = B.load_lexicon(ro)                        # used by the split's own passes, not as reference
    ro.close()

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

    print("building corpus rendering reference + stashing affected verses …")
    counts, totals, affected = _build_counts_and_stash(bh_index, lex, rahlfs, tagnt)
    print(f"  numbers with renderings: {len(totals):,}   affected verses: {len(affected):,}")

    if args.control:
        sys.exit(0 if run_control(counts, totals, affected) else 1)

    flags = []
    for ref, rows in affected:
        flags.extend(_flag_slots(rows, counts, totals, ref))

    print("\n── wrong-slot certification (split-affected verses) ──")
    print(f"  verses checked:   {len(affected):,}")
    print(f"  WRONG-SLOT FLAGS: {len(flags):,}  (one-off rendering of a >= {MIN_FREQ}-use number)")

    Path(args.out).write_text(
        "ref\tposition\trendering\tstrongs_base\n" +
        "\n".join(f"{r}\t{p}\t{h}\t{b}" for r, p, h, b in flags), encoding="utf-8")
    print(f"  full flag list -> {args.out}")

    if flags:
        print("\n  first 40 (rendering that this number almost never otherwise carries):")
        for r, p, h, b in flags[:40]:
            print(f"    {r}  pos {p}  {h!r} on {b}")
    else:
        print("\n  CLEAN — no content word is a one-off rendering of a well-attested number.")
        print("  Freeze-as-overlay CERTIFIED corpus-wide (within the one-off-only limit above).")


if __name__ == "__main__":
    main()
