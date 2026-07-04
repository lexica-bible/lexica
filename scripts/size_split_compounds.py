#!/usr/bin/env python3
"""
size_split_compounds.py — READ-ONLY sizing of the _split_compounds build pass.

Session 1 decision #1: is _split_compounds' gloss redistribution frozen as a
declared overlay, or do we retreat to ABP-native (leave the compound whole on
one slot)? To decide, we need two numbers the live db CANNOT give — the split
happens during the build and leaves no marker, so nothing in `words` tells you a
slot was filled by it. This script runs the REAL production pass over the source
and counts what it moves.

It reuses build_words_from_abp's own functions (no re-implementation, can't drift):
imports the real _split_compounds, runs the same per-verse pipeline the build uses,
and measures the split in isolation by wrapping it — every recipient slot the split
fills is counted, with before->after samples for eyeballing accuracy.

READ-ONLY: opens bible.db in read-only mode (lexicon only); reads the ABP source
files + bh_scrape.db; writes ONLY a scratch samples TSV. Touches no table.

Run on PA:
    python3 scripts/size_split_compounds.py ~/bible-db/bible.db ~/bible-db/bh_scrape.db

Optional: --samples 60  (how many affected verses to print; all go to the TSV)
"""
import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_words_from_abp as B


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bible_db", nargs="?", default="bible.db")
    ap.add_argument("scrape_db", nargs="?", default="bh_scrape.db")
    ap.add_argument("--samples", type=int, default=50, help="affected verses to print")
    ap.add_argument("--out", default="split_compounds_samples.tsv")
    args = ap.parse_args()

    # lexicon from a READ-ONLY handle on the live db
    ro = sqlite3.connect(f"file:{args.bible_db}?mode=ro", uri=True)
    lex = B.load_lexicon(ro)
    ro.close()
    print(f"lexicon entries: {len(lex):,}")

    scrape = sqlite3.connect(args.scrape_db)
    bh_index = B.load_bh_verse_index(scrape)
    scrape.close()
    print(f"bh verse keys:   {len(bh_index):,}")

    # mirror the build's pronoun-correction feeds if present (they change which
    # slots are empty before the split runs, so the input must match production)
    rahlfs = tagnt = None
    if B.RahlfsLXX and B.RAHLFS_DIR.is_dir():
        rahlfs = B.RahlfsLXX(B.RAHLFS_DIR); print("Rahlfs: loaded")
    else:
        print("Rahlfs: NOT found — OT input will differ from production")
    if B.TAGNTSource and all(p.is_file() for p in B.TAGNT_FILES):
        tagnt = B.TAGNTSource([str(p) for p in B.TAGNT_FILES]); print("TAGNT: loaded")
    else:
        print("TAGNT: NOT found — NT input will differ from production")

    # ── wrap the REAL split so we count only what IT does ──
    real_split = B._split_compounds
    state = {"moved": 0, "verses": 0, "ref": "", "ot": 0, "nt": 0}
    samples = []
    NT = set(B.ABBREV_TO_SLUG) - set(list(B.ABBREV_TO_SLUG)[:39])  # NT abbrevs (last 27)

    def wrapped(rows, lexicon, carry=False):
        # split conserves words but spreads a compound gloss across empty slots, so
        # (non-empty slots after) - (before) = recipient slots the split filled.
        before_ne = sum(1 for r in rows if (r[1] or "").strip())
        before_glosses = [r[1] for r in rows if (r[1] or "").strip()]
        real_split(rows, lexicon, carry)
        after_ne = sum(1 for r in rows if (r[1] or "").strip())
        d = after_ne - before_ne
        if d > 0:
            state["moved"] += d
            state["verses"] += 1
            # tag each after-slot with the Greek word it attached to (strongs_base +
            # lemma) so wrong-slot is VISIBLE — english alone can't show it. rows here
            # are pre-return (13 wide): r[4]=strongs_base (bare), r[12]=lemma.
            after_tagged = []
            for r in sorted(rows, key=lambda r: r[0]):
                eng = (r[1] or "").strip()
                if not eng:
                    continue
                tag = r[4] or "-"
                if r[12]:
                    tag += "/" + r[12]
                after_tagged.append(f"{eng}<{tag}>")
            samples.append((state["ref"], " | ".join(before_glosses),
                            " | ".join(after_tagged)))
    B._split_compounds = wrapped

    flag_log = []
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
                                    src.verse(bnum, ch, vs),
                                    [w[0] for w in abp_words])
            abp_words = B.apply_pronoun_corrections(
                abp_words, corrs, flag_log, f"{abbrev} {ch}:{vs}")
        state["ref"] = f"{abbrev} {ch}:{vs}"
        n0 = state["verses"]
        B.build_verse_words(abp_words, bh_rows, lex)   # runs the wrapped split
        if state["verses"] > n0:
            state["nt" if abbrev in NT else "ot"] += 1

    print("\n── _split_compounds sizing ──────────────────────────")
    print(f"  recipient slots filled by split: {state['moved']:,}")
    print(f"  verses affected:                 {state['verses']:,}")
    print(f"    OT verses: {state['ot']:,}   NT verses: {state['nt']:,}")

    Path(args.out).write_text(
        "ref\tbefore (source slots)\tafter (split result)\n" +
        "\n".join("\t".join(s) for s in samples), encoding="utf-8")
    print(f"\n  {len(samples):,} samples -> {args.out}")

    print(f"\n── {min(args.samples, len(samples))} samples for accuracy ──")
    step = max(1, len(samples) // args.samples)   # even spread, not just the first
    for ref, before, after in samples[::step][:args.samples]:
        print(f"  {ref}")
        print(f"    before: {before}")
        print(f"    after:  {after}")


if __name__ == "__main__":
    main()
