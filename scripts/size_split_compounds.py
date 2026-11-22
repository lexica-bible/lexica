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


def size_app(app, bh_index, lex, rahlfs, tagnt, ren, names, verse_keys):
    """--app-feed: replay the build's per-verse path (build_words_from_abp.run :2772-2793: OLD rows
    with ren= and names=, then app.apply, which builds the FEED rows - a second split - and
    composes). Each build_verse_words call records the slots ITS split filled (empty before the
    split, text after; keyed by the position value the split leaves, it permutes them) and its
    final cells (followed through the split by the row's Greek side, never its list index). A
    composed cell belongs to the FEED call when it equals that call's final cell,
    else to the OLD call when it equals that one's (a merge-pair restore, §9.73, or an edge
    split's blank row, §9.75, whose piece IS the old English), else to neither (an edge split's
    neighbour left with a new rest); when apply kept the OLD set (rows IS old_rows) only the OLD call
    counts. A filled slot is counted when its own call owns the composed cell. Coded apart from
    lint_split_wrong_slot.py's capture on purpose: the two counts must agree (charter §4.2).
    -> (moved, verses, samples, ambiguous Greek-side groups)."""
    real_split, real_bvw = B._split_compounds, B.build_verse_words
    runs, amb = [], [0]

    def wrapped(rows, lexicon, carry=False):
        # the split permutes positions and sorts the list (build :623-627): follow each row by
        # its Greek side (idx 3, 4, 7, 8, 9, 11, 12), which the split never changes, pairing
        # before and after rows of one Greek side in position order
        greek = lambda r: (r[3], r[4], r[7], r[8], r[9], r[11], r[12])   # noqa: E731
        was = {}
        for r in sorted(rows, key=lambda r: r[0]):
            was.setdefault(greek(r), []).append(not (r[1] or "").strip())
        before = list(rows)
        real_split(rows, lexicon, carry)
        # a Greek side shared by rows the split CHANGED, some empty before and some not: the pairing
        # below is by position order, not certain - counted (the lint counts the same and skips them)
        changed = [r for r in before if r not in rows]
        mixed = {}
        for r in changed:
            mixed.setdefault(greek(r), set()).add(not (r[1] or "").strip())
        amb[0] += sum(1 for s in mixed.values() if len(s) > 1)
        filled, k = [], {}
        for r in sorted(rows, key=lambda r: r[0]):
            g = greek(r)
            i = k.get(g, 0)
            k[g] = i + 1
            if was[g][i] and (r[1] or "").strip():
                filled.append(r[0])
        runs[-1]["filled"] = filled

    def wrapped_bvw(*a, **k):
        runs.append({"filled": []})
        me = runs[-1]
        out = real_bvw(*a, **k)
        me["final"] = {r[0]: (r[1], r[2]) for r in out}
        return out

    moved = verses = 0
    samples = []
    B._split_compounds, B.build_verse_words = wrapped, wrapped_bvw
    try:
        for abbrev, ch, vs, raw_words in B.iter_verses(*B._abp_sources()):
            if (abbrev, ch, vs) not in verse_keys:
                continue
            slug = B.ABBREV_TO_SLUG.get(abbrev)
            bh_rows = bh_index.get((slug, ch, vs), []) if slug else []
            words, corrs = B._pronoun_corrections(abbrev, ch, vs, raw_words, rahlfs, tagnt, [])
            runs.clear()
            old_rows = B.build_verse_words(words, bh_rows, lex, ren=ren, article_refusals=[],
                                           names=names, pn_star_refusals=[])
            rows = app.apply((abbrev, ch, vs), raw_words, corrs, old_rows, bh_rows, lex,
                             ren=ren, names=names)
            if rows is old_rows:
                old, feed = runs[0], None
            elif len(runs) == 2:
                old, feed = runs
            else:
                raise RuntimeError(f"{abbrev} {ch}:{vs}: composed with {len(runs)} build calls (expected 2)")
            counted = set()
            for r in rows:
                cell = (r[1], r[2])
                if feed is not None and feed["final"].get(r[0]) == cell:
                    owner = feed
                elif old["final"].get(r[0]) == cell:
                    owner = old
                else:
                    continue
                if r[0] in owner["filled"]:
                    counted.add(r[0])
            if counted:
                moved += len(counted)
                verses += 1
                # composed rows are 12 wide (build :2440-2441): idx 4 strongs_base, idx 11 lemma
                # (the default mode reads lemma at idx 12 of the 13-wide split-time rows)
                samples.append((f"{abbrev} {ch}:{vs}", " | ".join(
                    f"{'*' if r[0] in counted else ''}{(r[1] or '').strip()}<{r[4] or '-'}"
                    f"{'/' + r[11] if r[11] else ''}>"
                    for r in sorted(rows, key=lambda r: r[0]) if (r[1] or "").strip())))
    finally:
        B._split_compounds, B.build_verse_words = real_split, real_bvw
    return moved, verses, samples, amb[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bible_db", nargs="?", default="bible.db")
    ap.add_argument("scrape_db", nargs="?", default="bh_scrape.db")
    ap.add_argument("--samples", type=int, default=50, help="affected verses to print")
    ap.add_argument("--out", default="split_compounds_samples.tsv")
    ap.add_argument("--app-feed", action="store_true",
                    help="size the split in the app-edition build: the build's transplant replayed, "
                         "slots counted from the COMPOSED rows (DESIGN 9.214, 9.239)")
    ap.add_argument("--count-differs", default=str(B.APP_COUNT_DIFFERS),
                    help="with --app-feed: the frozen chunk-level count-differs file (as the build)")
    args = ap.parse_args()

    if args.app_feed:
        # the samples file goes to the CURRENT folder: say which, never write over an earlier run's
        print(f"output folder: {Path.cwd()}")
        if Path(args.out).exists():
            print(f"STOP: {args.out} already in this folder, not overwritten")
            sys.exit(1)

    # lexicon from a READ-ONLY handle on the live db
    ro = sqlite3.connect(f"file:{args.bible_db}?mode=ro", uri=True)
    lex = B.load_lexicon(ro)
    verse_keys = ({(b, c, v) for b, c, v in ro.execute("SELECT book, chapter, verse FROM verses")}
                  if args.app_feed else None)
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

    if args.app_feed:
        from abp_app_feed import FeedError
        try:
            app = B.AppTransplant(B.abp_source_texts(), count_differs=args.count_differs)
        except FeedError as e:
            print(f"STOP: {e}")
            sys.exit(1)
        moved, verses, samples, n_amb = size_app(app, bh_index, lex, rahlfs, tagnt, B.build_attestation_map(),
                                          B.load_name_roster(), verse_keys)
        print("\n── _split_compounds sizing, --app-feed (slots counted from the COMPOSED rows) ──")
        print(f"  recipient slots filled by split: {moved:,}")
        print(f"  verses affected:                 {verses:,}")
        print(f"  AMBIGUOUS Greek-side groups:     {n_amb:,}   (expected 0; the lint prints its own count)")
        print("  transplant tally: " + ", ".join(f"{k} {v:,}" for k, v in sorted(app.tally.items())))
        try:
            app.check_merge_pairs("build")
        except FeedError as e:
            print(f"STOP: the replay is not the build's transplant - {e}")
            sys.exit(1)
        Path(args.out).write_text(
            "ref\tafter (composed rows; * = a slot the split filled)\n" +
            "\n".join("\t".join(s) for s in samples), encoding="utf-8")
        print(f"  {len(samples):,} samples -> {args.out}")
        return

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
