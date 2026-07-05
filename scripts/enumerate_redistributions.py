#!/usr/bin/env python3
"""enumerate_redistributions.py — READ-ONLY. Every verse `_redistribute_pronoun_compounds`
fires on, with the reader reading it produces. The control set for the S9 (P) fix.

WHY: (P) re-aims at `_redistribute_pronoun_compounds` (it hard-codes moved-verb-first /
kept-pronoun-second, which flips a pronoun that precedes its verb — "his hand" -> "hand his",
"I beheld you" -> "beheld I you"). The fix must drive the 208 survivors to zero AND leave every
OTHER firing byte-identical. This tool lists all firings + their readings so a plain `diff` of
pre-fix vs post-fix shows ONLY the 208 changing.

Replays the REAL build per verse (Path-C pronoun correction THEN build_verse_words), wrapping the
pass to record which verses it changes — so it can't drift from the build. Reads bible.db.new +
bh_scrape.db read-only; writes only the output list. Run on PA (needs the Rahlfs/TAGNT dirs so the
post-Path-C pronoun numbers exist — the pass never fires on the raw 1473).

CONTROL RULE (obeys the same rule it enforces): --controls (default on) proves the enumerator
FIRES before its list is trusted — Gen 3:15 (a known CORRECT fire) and Gen 7:1 (a known WRONG fire
that only appears if Path-C ran) must BOTH be in the firing set. If either is missing the tool is
broken, not the corpus: it prints FAIL and exits 1 without trusting the output.

  python3 scripts/enumerate_redistributions.py bible.db.new bh_scrape.db [--out FILE]
"""
import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_words_from_abp as B
from reorder_english import get_english_order_words

_CONTROL_MUST_FIRE = ["Gen 3:15", "Gen 7:1"]   # correct-fire + Path-C-only wrong-fire


def _reading(word_rows):
    """Final reader reading of a verse's built rows (english in reader order)."""
    wd = [{"english": r[1], "greek_pos": r[5], "bracket_id": r[6]} for r in word_rows]
    return " ".join((w["english"] or "") for w in get_english_order_words(wd)).strip()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    bible_db  = args[0] if len(args) > 0 else "bible.db.new"
    scrape_db = args[1] if len(args) > 1 else "bh_scrape.db"
    out_path = "redistribution_firings.tsv"
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]

    conn = sqlite3.connect(f"file:{bible_db}?mode=ro", uri=True)
    lex = B.load_lexicon(conn)
    conn.close()
    sc = sqlite3.connect(f"file:{scrape_db}?mode=ro", uri=True)
    bh = B.load_bh_verse_index(sc)
    sc.close()

    # Path-C aligners — the pass only fires on post-correction pronoun numbers.
    rahlfs = tagnt = None
    if B.RahlfsLXX and B.RAHLFS_DIR.is_dir():
        rahlfs = B.RahlfsLXX(B.RAHLFS_DIR)
    else:
        print("⚠️  Rahlfs dir not found — OT pronoun correction SKIPPED "
              "(Gen 7:1 control will fail, as designed).", file=sys.stderr)
    if B.TAGNTSource and all(p.is_file() for p in B.TAGNT_FILES):
        tagnt = B.TAGNTSource([str(p) for p in B.TAGNT_FILES])
    else:
        print("⚠️  TAGNT files not found — NT pronoun correction SKIPPED.", file=sys.stderr)

    # Wrap the pass: mark the current verse if it CHANGES anything.
    cur = {"ref": None}
    fired = set()
    _orig = B._redistribute_pronoun_compounds

    def _wrap(rows):
        before = [(r[0], r[1], r[5], r[6]) for r in rows]
        _orig(rows)
        if [(r[0], r[1], r[5], r[6]) for r in rows] != before:
            fired.add(cur["ref"])

    B._redistribute_pronoun_compounds = _wrap

    order = {}          # ref -> feed sequence index (deterministic canonical-ish order)
    reading = {}        # ref -> final reader reading
    seq = 0
    for abbrev, chapter, verse, abp_words in B.iter_verses(*B._abp_sources()):
        ref = f"{abbrev} {chapter}:{verse}"
        cur["ref"] = ref
        order[ref] = seq
        seq += 1
        slug = B.ABBREV_TO_SLUG.get(abbrev)
        bh_rows = bh.get((slug, chapter, verse), []) if slug else []
        src = bnum = None
        if rahlfs and rahlfs.booknum(abbrev):
            src, bnum = rahlfs, rahlfs.booknum(abbrev)
        elif tagnt and tagnt.booknum(abbrev):
            src, bnum = tagnt, tagnt.booknum(abbrev)
        if src:
            corrs = B.correct_verse([w[1] for w in abp_words],
                                    src.verse(bnum, chapter, verse),
                                    [w[0] for w in abp_words])
            abp_words = B.apply_pronoun_corrections(abp_words, corrs, [], ref)
        word_rows = B.build_verse_words(abp_words, bh_rows, lex)
        if ref in fired:
            reading[ref] = _reading(word_rows)

    # --- controls: the enumerator must fire on both knowns before its zero is trusted ---
    print(f"verses replayed : {seq:,}")
    print(f"firings         : {len(fired):,}")
    ok = True
    for ctl in _CONTROL_MUST_FIRE:
        hit = ctl in fired
        ok = ok and hit
        print(f"  [{'FIRED' if hit else 'MISS '}] control {ctl}")
    if not ok:
        print("CONTROLS FAILED — enumerator did not fire on a known case; output NOT trusted "
              "(check Path-C dirs). Exiting without writing.")
        sys.exit(1)
    print("CONTROLS PASSED.")

    # deterministic, sorted by feed order → stable for a plain `diff`
    rows_out = sorted(reading.items(), key=lambda kv: order[kv[0]])
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        for ref, rd in rows_out:
            fh.write(f"{ref}\t{rd}\n")
    print(f"wrote {len(rows_out):,} firing readings -> {out_path}")


if __name__ == "__main__":
    main()
