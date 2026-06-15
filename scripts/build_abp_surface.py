#!/usr/bin/env python3
"""
build_abp_surface.py — side table of the PRINTED (inflected) Greek word for each
ABP word, feeding the word-study side-card "in this verse" line.

WHY a side table (not a words-table column):
  ABP's own source is English+Strong's only — it has NO Greek surface words. This
  script gets the printed Greek from a source, aligns it to each ABP word in the
  LIVE words table by Strong's number, and records the printed form where the match
  is confident. It NEVER writes words/verses — only a separate table
  abp_surface(verse_id, position, form, translit), joined at serve time like the
  lexicon lemma. Drop that table to undo, with zero risk to the corpus.

TWO SURFACE SOURCES:
  --bh  bh_scrape.db (BibleHub ABP scrape, bh_words.greek) = ABP's OWN printed Greek,
        whole Bible, near-complete. PREFERRED: it's the exact text ABP prints (same
        text as our words, so it matches almost perfectly). Its Greek is accent-only
        (no breathing marks) — that's how ABP prints. It expands compound cells
        ("3588-1161"/"η δε" -> two tokens) and bridges ABP's raw G1473 pronoun
        mis-tag to the live corrected numbers (αὐτός 846, σύ 4771 …).
  --rahlfs / --tagnt  the Rahlfs-1935 (OT) / TAGNT (NT) critical editions. Polished
        polytonic Greek but a DIFFERENT edition and lower coverage (~75% OT). TAGNT
        also carries a vetted transliteration (captured, not shown yet).

TRANSLIT: not displayed yet either way (both testaments show the printed form alone),
  pending the real Greek->Latin transliterator the transliteration-search feature will
  build. See memory project_bsb_words (the ABP section).

READ-ONLY on bible.db except the one new table it creates/replaces. Run on PA.
--dry-run reports coverage and writes nothing.

Usage (on PA) — ABP's own Greek (preferred):
  python3 scripts/build_abp_surface.py ~/bible-db/bible.db --bh ~/bible-db/bh_scrape.db --dry-run
  # then drop --dry-run to write the table.
Or the critical editions:
  python3 scripts/build_abp_surface.py ~/bible-db/bible.db --rahlfs ~/LXX-Rahlfs-1935 \
      --tagnt ~/TAGNT_Mat-Jhn.txt ~/TAGNT_Act-Rev.txt --dry-run
"""
import argparse
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # find lxx_align
from lxx_align import RahlfsLXX, TAGNTSource, align, base, RESOLVE


# ABP abbrev -> BibleHub scrape book slug (bh_words.book). Inlined from
# build_words_from_bh.SLUG_TO_ABBREV (stable, 66 books) to avoid importing the
# scraper module here.
SLUG_TO_ABBREV = {
    "genesis": "Gen", "exodus": "Exo", "leviticus": "Lev", "numbers": "Num",
    "deuteronomy": "Deu", "joshua": "Jos", "judges": "Jdg", "ruth": "Rth",
    "1_samuel": "1Sa", "2_samuel": "2Sa", "1_kings": "1Ki", "2_kings": "2Ki",
    "1_chronicles": "1Ch", "2_chronicles": "2Ch", "ezra": "Ezr", "nehemiah": "Neh",
    "esther": "Est", "job": "Job", "psalms": "Psa", "proverbs": "Pro",
    "ecclesiastes": "Ecc", "songs": "Son", "isaiah": "Isa",
    "jeremiah": "Jer", "lamentations": "Lam", "ezekiel": "Eze", "daniel": "Dan",
    "hosea": "Hos", "joel": "Joe", "amos": "Amo", "obadiah": "Oba",
    "jonah": "Jon", "micah": "Mic", "nahum": "Nah", "habakkuk": "Hab",
    "zephaniah": "Zep", "haggai": "Hag", "zechariah": "Zec", "malachi": "Mal",
    "matthew": "Mat", "mark": "Mar", "luke": "Luk", "john": "Joh",
    "acts": "Act", "romans": "Rom", "1_corinthians": "1Co", "2_corinthians": "2Co",
    "galatians": "Gal", "ephesians": "Eph", "philippians": "Php", "colossians": "Col",
    "1_thessalonians": "1Th", "2_thessalonians": "2Th", "1_timothy": "1Ti",
    "2_timothy": "2Ti", "titus": "Tit", "philemon": "Phm", "hebrews": "Heb",
    "james": "Jas", "1_peter": "1Pe", "2_peter": "2Pe", "1_john": "1Jn",
    "2_john": "2Jn", "3_john": "3Jn", "jude": "Jud", "revelation": "Rev",
}
ABBREV_TO_SLUG = {v: k for k, v in SLUG_TO_ABBREV.items()}

_NT = {"Mat", "Mar", "Luk", "Joh", "Act", "Rom", "1Co", "2Co", "Gal", "Eph", "Php",
       "Col", "1Th", "2Th", "1Ti", "2Ti", "Tit", "Phm", "Heb", "Jas", "1Pe", "2Pe",
       "1Jn", "2Jn", "3Jn", "Jud", "Rev"}

_DASH = re.compile(r"-(?=\d)")   # compound separator: a dash followed by a digit


def _norm(b):
    """Fold every pronoun Strong's to one bucket ('1473') so ABP's raw mis-tagged
    pronouns (all G1473 in the scrape) match the live table's corrected numbers
    (αὐτός 846, σύ 4771 …). Content numbers are untouched (the pronoun set is
    pronoun-only). Used for the bh source only."""
    return "1473" if b in RESOLVE else b


def expand_bh(strongs, greek):
    """One bh_words cell -> [(base_strongs, surface_greek), ...]. A compound cell
    ('3588-1161' / 'η δε') splits into its parts; a single cell (incl. dotted ABP
    numbers like '1510.7.3') stays whole. base() strips the dot for matching."""
    s = (strongs or "").strip()
    g = (greek or "").strip()
    if not s:
        return [("", g)]
    parts = _DASH.split(s)
    if len(parts) <= 1:
        return [(base(s), g)]
    gws = g.split()
    return [(base(p), gws[i] if i < len(gws) else "") for i, p in enumerate(parts)]


class BHSource:
    """ABP's own printed Greek from a BibleHub scrape (bh_scrape.db / bh_words)."""

    def __init__(self, bh_db):
        self.con = sqlite3.connect(bh_db)

    def slug(self, abbrev):
        return ABBREV_TO_SLUG.get(abbrev)

    def tokens(self, slug, ch, vs):
        """[(base_strongs, surface_greek), ...] for the verse, compounds expanded,
        in scrape (= reading) order."""
        rows = self.con.execute(
            "SELECT strongs, greek FROM bh_words WHERE book=? AND chapter=? AND verse=? ORDER BY position",
            (slug, ch, vs),
        ).fetchall()
        out = []
        for strongs, greek in rows:
            out.extend(expand_bh(strongs, greek))
        return out


def iter_db_verses(con):
    """Yield (verse_id, book_abbrev, chapter, verse, [(position, base_strongs), ...])
    per ABP verse, words in position order."""
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


def pct(a, b):
    return f"{(100.0 * a / b):.1f}" if b else "0.0"


def build(db_path, rahlfs_dir, tagnt_paths, bh_db, dry_run):
    rx = RahlfsLXX(rahlfs_dir) if rahlfs_dir else None
    tx = TAGNTSource(tagnt_paths) if tagnt_paths else None
    bh = BHSource(bh_db) if bh_db else None
    use_bh = bh is not None

    con = sqlite3.connect(db_path)
    rows = []                                   # (verse_id, position, form, translit)
    st = {"ot_w": 0, "ot_s": 0, "nt_w": 0, "nt_s": 0}
    skipped_books = set()

    for vid, book, ch, vs, words in iter_db_verses(con):
        is_nt = book in _NT
        a_raw = [sb for _pos, sb in words]

        if use_bh:
            slug = bh.slug(book)
            if not slug:
                skipped_books.add(book)
                continue
            toks = bh.tokens(slug, ch, vs)      # [(base, surface)]
            if not toks:
                continue
            b_bases = [t[0] for t in toks]
            surfs   = [(t[1], "") for t in toks]
            # Bridge ABP's raw G1473 pronouns -> the live corrected numbers, both
            # for the alignment scoring AND the anchor check. Same text + order, so
            # the fold is safe (the pronoun at a slot is the same word on both sides).
            a_al = [_norm(b) for b in a_raw]
            b_al = [_norm(b) for b in b_bases]
            pairs = align(a_al, b_al, [False] * len(b_al))
            amap = {ai: bj for ai, bj in pairs if ai >= 0}
            for i, (pos, sb) in enumerate(words):
                if is_nt:
                    st["nt_w"] += 1
                else:
                    st["ot_w"] += 1
                if sb in ("", "*"):             # no anchor / proper noun
                    continue
                bj = amap.get(i, -1)
                if bj is None or bj < 0 or bj >= len(b_al):
                    continue
                if a_al[i] != b_al[bj]:         # normalized anchor must match
                    continue
                form = surfs[bj][0] or ""
                if not form:
                    continue
                rows.append((vid, pos, form, ""))
                if is_nt:
                    st["nt_s"] += 1
                else:
                    st["ot_s"] += 1
            continue

        # ── critical-edition path (Rahlfs OT / TAGNT NT) ──────────────────────
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
        pairs = align(a_raw, b_bases, b_pron)
        amap = {ai: bj for ai, bj in pairs if ai >= 0}
        for i, (pos, sb) in enumerate(words):
            if kind == "ot":
                st["ot_w"] += 1
            else:
                st["nt_w"] += 1
            if sb in ("", "*", "1473"):
                continue
            bj = amap.get(i, -1)
            if bj is None or bj < 0 or bj >= len(b_bases):
                continue
            if b_bases[bj] != sb:
                continue
            if kind == "ot":
                form, translit = (ssurf[bj] if bj < len(ssurf) else "") or "", ""
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

    tot_w = st["ot_w"] + st["nt_w"]
    tot_s = st["ot_s"] + st["nt_s"]
    print("\n== build_abp_surface (%s) ==" % ("bh_scrape = ABP's own" if use_bh else "Rahlfs/TAGNT"))
    print(f"  OT : {st['ot_s']}/{st['ot_w']}  ({pct(st['ot_s'], st['ot_w'])}%)")
    print(f"  NT : {st['nt_s']}/{st['nt_w']}  ({pct(st['nt_s'], st['nt_w'])}%)")
    print(f"  ALL: {tot_s}/{tot_w}  ({pct(tot_s, tot_w)}%)   rows={len(rows)}")
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
    ap.add_argument("--bh", help="bh_scrape.db (ABP's own printed Greek — preferred source)")
    ap.add_argument("--rahlfs", help="LXX-Rahlfs-1935 dir (OT, critical edition)")
    ap.add_argument("--tagnt", nargs="+", default=[], help="TAGNT .txt file(s) (NT, critical edition)")
    ap.add_argument("--dry-run", action="store_true", help="report coverage, write nothing")
    args = ap.parse_args()
    if not args.bh and not args.rahlfs and not args.tagnt:
        ap.error("give --bh (preferred), and/or --rahlfs/--tagnt")
    build(args.db, args.rahlfs, args.tagnt, args.bh, args.dry_run)


if __name__ == "__main__":
    main()
