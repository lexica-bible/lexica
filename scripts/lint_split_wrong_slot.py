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
it, across the WHOLE corpus}. A wrong-slot word is a RARE rendering of an otherwise
FREQUENT number — "kissed" on 3744 (rendered "scent" everywhere else) stands out;
"scent" on 3744 does not, because it is the number's normal rendering. This speaks
ABP's vocabulary because it IS ABP's vocabulary.

SELF-VALIDATION GUARD (frequency floor). The reference counts the very row under test,
so a mere "does this rendering exist for this number" check would pass every leak by
construction — a wrong "scent" landing once enters 3744's profile and validates itself.
Worse, a leak that fired TWICE would look like a recurring rendering. So a rendering
must recur at least VALIDATE_MIN=3 times on a number to VALIDATE a slot; 1 or 2
occurrences FLAG. A per-verse leak is idiosyncratic (rare on that number); a legit
rendering recurs. This catches the one-off AND the fired-twice leak.

CIRCULARITY LIMIT (stated so a clean run isn't misread): a mis-placement repeated
>= VALIDATE_MIN times would make its wrong rendering look legit and hide it — a
SYSTEMATIC error is a different audit. The independent leg is the 60-verse BibleHub
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

VALIDATE_MIN = 3   # a rendering must recur >= this many times on a number to validate a slot
MIN_FREQ     = 8   # ...and only numbers used at least this often are judged (else rare != wrong)


def _fold(w):
    """One rendering key per english_head: lowercase, strip punctuation, and collapse regular
    inflections (plural + verb tense) so a Greek word's varied renderings share a key —
    smell/smelled/smelling -> "smell". Without this a frequent verb's renderings fragment
    across tenses and NONE reaches the frequency floor, so a correct rare spelling ('smelled',
    2x) gets flagged. Short words are guarded (bed/led/was keep their -ed/-s). A wrong word
    still stems to a form the number never renders (kissed->kiss on αὐτός = 0)."""
    w = _PUNCT.sub("", (w or "").lower())
    if not w:
        return w
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3 and not w.endswith("ss"):
            return w[:-len(suf)]
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
        if totals.get(base, 0) >= MIN_FREQ and counts[base].get(hf, 0) < VALIDATE_MIN:
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
    for f in good_flags:                                 # show WHY: usage + top renderings
        b = f[3]
        top = ", ".join(f"{k}:{v}" for k, v in counts[b].most_common(5))
        print(f"      unexpected flag: pos {f[1]} {f[2]!r} on {b}  "
              f"(number used {totals[b]}x; renderings {top})")

    # hand-break the ACTUAL failure class: put a content word onto a FREQUENT number that
    # never renders it (a content word landing on the wrong Greek word). NOT a same-word
    # swap — that can be a no-op (two 'him'/846 slots) and proves nothing.
    freq_targets = [b for b, t in totals.most_common() if t >= MIN_FREQ]
    victim = None
    for i, r in enumerate(rows):
        if not (r[2] and r[4] and r[4][0].isdigit()):
            continue
        h = _fold(r[2])
        if not h:
            continue
        for T in freq_targets:
            if T != r[4] and counts[T].get(h, 0) == 0:      # a number that never renders h
                victim = (i, r, T, h)
                break
        if victim:
            break
    if not victim:
        print("CONTROL ERROR: no content slot to mis-place"); return False
    vi, vr, T, h = victim
    broken = list(rows)
    lr = list(vr); lr[4] = T                                 # move the word onto the wrong number
    broken[vi] = tuple(lr)
    bad_flags = _flag_slots(broken, counts, totals, ref + " [BROKEN]")
    print(f"  hand-broken {ref}: put {vr[2]!r} onto {T} (renders it 0x, used {totals[T]}x)  "
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
    unadj_slots, unadj_nums = 0, set()          # content slots on numbers below the >= MIN_FREQ gate
    for ref, rows in affected:
        flags.extend(_flag_slots(rows, counts, totals, ref))
        for _pos, _hf, base in _content_slots(rows):
            if totals.get(base, 0) < MIN_FREQ:
                unadj_slots += 1
                unadj_nums.add(base)

    print("\n── wrong-slot certification (split-affected verses) ──")
    print(f"  verses checked:      {len(affected):,}")
    print(f"  UNADJUDICATED:       {unadj_slots:,} content slots on {len(unadj_nums):,} rare "
          f"(< {MIN_FREQ}-use) numbers — not judged here; covered by the 60-sample + BibleHub leg")
    print(f"  WRONG-SLOT FLAGS:    {len(flags):,}  (rendering used < {VALIDATE_MIN}x on a >= {MIN_FREQ}-use number)")

    Path(args.out).write_text(
        "ref\tposition\trendering\tstrongs_base\n" +
        "\n".join(f"{r}\t{p}\t{h}\t{b}" for r, p, h, b in flags), encoding="utf-8")
    print(f"  full flag list -> {args.out}")

    if flags:
        print("\n  first 40 (rendering that this number almost never otherwise carries):")
        for r, p, h, b in flags[:40]:
            print(f"    {r}  pos {p}  {h!r} on {b}")
    else:
        print("\n  CLEAN — no content word is a rare (< 3x) rendering of a well-attested number.")
        print("  Freeze-as-overlay CERTIFIED corpus-wide (within the frequency-floor limit above).")


if __name__ == "__main__":
    main()
