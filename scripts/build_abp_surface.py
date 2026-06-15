#!/usr/bin/env python3
"""
build_abp_surface.py — side table of the PRINTED (inflected) Greek word for each
ABP word, feeding the word-study side-card "in this verse" line.

WHY a side table (not a words-table column):
  ABP's own source is English+Strong's only — it has NO Greek surface words. The
  printed Greek lives in the Rahlfs-1935 (OT) and TAGNT (NT) sources. This script
  aligns each ABP word in the LIVE words table to those sources by Strong's number
  (the same proven alignment the pronoun fix uses) and records the printed form
  where the match is confident. It NEVER writes words/verses — only a separate
  table  abp_surface(verse_id, position, form, translit)  that /api/chapter joins
  at serve time like the lexicon lemma. Drop that table to undo, with zero risk to
  the corpus.

COVERAGE: ~the same anchored-slot rate as the morph/lemma columns (~78%). An ABP
  word that doesn't anchor simply gets no row → no "in this verse" line (graceful,
  like a Hebrew/BSB word that lacks one). Proper nouns ('*') and pronoun slots are
  skipped on purpose.

TRANSLIT: captured for the NT (TAGNT carries a vetted transliteration for free) and
  left blank for the OT. The frontend does NOT display the ABP translit yet — both
  testaments show the printed form ALONE, kept consistent — so the NT translit is
  just stored now, ready for the eventual backfill from the real Greek->Latin
  transliterator the transliteration-search feature will build (only the OT is left
  then). See memory project_bsb_words (the ABP section) for the rationale.

READ-ONLY on bible.db except the one new table it creates/replaces. Run on PA, where
the Rahlfs/TAGNT sources live.  --dry-run reports coverage and writes nothing.

Usage (on PA):
  python3 scripts/build_abp_surface.py ~/bible-db/bible.db \
      --rahlfs ~/LXX-Rahlfs-1935 \
      --tagnt ~/TAGNT_Mat-Jhn.txt ~/TAGNT_Act-Rev.txt --dry-run
  # then the same line WITHOUT --dry-run to write the table.
"""
import argparse
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # find lxx_align
from lxx_align import RahlfsLXX, TAGNTSource, align, base


def iter_db_verses(con):
    """Yield (verse_id, book_abbrev, chapter, verse, [(position, base_strongs), ...])
    per ABP verse, words in position order. base_strongs '' / '*' pass through so the
    aligner sees every slot (they just never anchor)."""
    cur = con.execute(
        "SELECT v.id, v.book, v.chapter, v.verse, w.position, w.strongs_base "
        "FROM verses v JOIN words w ON w.verse_id = v.id "
        "ORDER BY v.id, w.position"
    )
    cur_id, rec = None, None
    for vid, book, ch, vs, pos, sb in cur:
        if vid != cur_id:
            if rec:
                yield rec
            cur_id, rec = vid, (vid, book, ch, vs, [])
        rec[4].append((pos, base(sb or "")))
    if rec:
        yield rec


def build(db_path, rahlfs_dir, tagnt_paths, dry_run):
    rx = RahlfsLXX(rahlfs_dir) if rahlfs_dir else None
    tx = TAGNTSource(tagnt_paths) if tagnt_paths else None

    con = sqlite3.connect(db_path)
    rows = []                       # (verse_id, position, form, translit)
    st = {"ot_w": 0, "ot_s": 0, "nt_w": 0, "nt_s": 0}
    skipped_books = set()

    for vid, book, ch, vs, words in iter_db_verses(con):
        # Pick the source for this book (OT -> Rahlfs, NT -> TAGNT). A book in
        # neither scope (none should be left, but be safe) is recorded + skipped.
        if rx is not None and rx.booknum(book) is not None:
            src, bnum, kind = rx, rx.booknum(book), "ot"
        elif tx is not None and tx.booknum(book) is not None:
            src, bnum, kind = tx, tx.booknum(book), "nt"
        else:
            skipped_books.add(book)
            continue

        sverse = src.verse(bnum, ch, vs)            # [(strong, morph, is_pron, lemma)]
        ssurf  = src.surface_verse(bnum, ch, vs)    # OT: [greek]   NT: [(greek, translit)]
        if not sverse:
            continue
        b_bases = [t[0] for t in sverse]
        b_pron  = [t[2] for t in sverse]
        a_bases = [sb for _pos, sb in words]
        pairs = align(a_bases, b_bases, b_pron)
        amap = {ai: bj for ai, bj in pairs if ai >= 0}

        for i, (pos, sb) in enumerate(words):
            if kind == "ot":
                st["ot_w"] += 1
            else:
                st["nt_w"] += 1
            if sb in ("", "*", "1473"):             # no anchor / proper noun / pronoun slot
                continue
            bj = amap.get(i, -1)
            if bj is None or bj < 0 or bj >= len(b_bases):
                continue
            if b_bases[bj] != sb:                   # anchor must match (same safe rule as morph/lemma)
                continue
            if kind == "ot":
                form = (ssurf[bj] if bj < len(ssurf) else "") or ""
                translit = ""
            else:
                pair = ssurf[bj] if bj < len(ssurf) else ("", "")
                form, translit = (pair[0] or ""), (pair[1] or "")
            if not form:
                continue
            rows.append((vid, pos, form, translit))
            if kind == "ot":
                st["ot_s"] += 1
            else:
                st["nt_s"] += 1

    def pct(a, b):
        return f"{(100.0 * a / b):.1f}" if b else "0.0"

    print("\n== build_abp_surface ==")
    print(f"  OT (Rahlfs) : {st['ot_s']}/{st['ot_w']} words got a printed form  ({pct(st['ot_s'], st['ot_w'])}%)")
    print(f"  NT (TAGNT)  : {st['nt_s']}/{st['nt_w']}  ({pct(st['nt_s'], st['nt_w'])}%)   [+ translit captured]")
    print(f"  total rows  : {len(rows)}")
    if skipped_books:
        print(f"  books with no source (skipped): {sorted(skipped_books)}")
    print("  samples:")
    for r in rows[:10]:
        print(f"    v{r[0]} pos{r[1]}  {r[2]}" + (f"  ({r[3]})" if r[3] else ""))

    if dry_run:
        print("\n  DRY RUN — nothing written.\n")
        con.close()
        return

    con.execute("DROP TABLE IF EXISTS abp_surface")
    con.execute(
        "CREATE TABLE abp_surface ("
        "  verse_id INTEGER, position INTEGER, form TEXT, translit TEXT,"
        "  PRIMARY KEY (verse_id, position))"
    )
    con.executemany("INSERT OR REPLACE INTO abp_surface VALUES (?,?,?,?)", rows)
    con.commit()
    con.close()
    print(f"\n  Wrote {len(rows)} rows to abp_surface (read-only side table; words/verses untouched).\n")


def main():
    ap = argparse.ArgumentParser(description="Build the ABP printed-form side table (read-only on words/verses).")
    ap.add_argument("db", help="path to bible.db (on PA)")
    ap.add_argument("--rahlfs", help="LXX-Rahlfs-1935 dir (OT printed forms)")
    ap.add_argument("--tagnt", nargs="+", default=[], help="TAGNT .txt file(s) (NT printed forms + translit)")
    ap.add_argument("--dry-run", action="store_true", help="report coverage, write nothing")
    args = ap.parse_args()
    if not args.rahlfs and not args.tagnt:
        ap.error("give --rahlfs and/or --tagnt")
    build(args.db, args.rahlfs, args.tagnt, args.dry_run)


if __name__ == "__main__":
    main()
