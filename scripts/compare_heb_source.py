#!/usr/bin/env python3
"""compare_heb_source.py — READ-ONLY sanity check before switching the Hebrew-word
source from the KJV Strong's bridge (kjv_strongs/kjv_words) to the real Hebrew OT
interlinear (heb.db -> heb_words).

It NEVER writes anything. Run it on PythonAnywhere where bible.db + heb.db live:

    python3 scripts/compare_heb_source.py
    python3 scripts/compare_heb_source.py --bible ~/bible-db/bible.db --heb ~/bible-db/heb.db

What it checks (the landmines from the swap brief):
  1. KEY FORMAT — what heb_words.strongs actually looks like (H-prefixed? zero-
     stripped? any trailing letters?), so the join matches exactly.
  2. OCCURRENCE COUNTS — KJV-bridge vs heb.db verse/word counts for four sample
     words (ruach H7307, chesed H2617, shabbat H7676, dabar H1697), plus how many
     verses each finds that the other misses (a big miss = versification drift).
  3. VERSIFICATION — dumps the first words of two superscription Psalms (Psa 3,
     Psa 51) from heb.db next to the KJV verse-1 text, so you can eyeball whether
     heb.db verse numbers line up with KJV/ABP (English) or are offset (Hebrew).
  4. COVERAGE — H-numbers used in the KJV OT (and in bdb) but MISSING from
     heb_words, and vice-versa, so we know what would lose/gain occurrences.

Everything is opened read-only (mode=ro); a missing heb.db just aborts cleanly.
"""
import argparse
import os
import sqlite3

# (H-number, transliteration, gloss) — the brief's four spot-check words.
SAMPLES = [
    ("H7307", "ruach", "spirit / wind / breath"),
    ("H2617", "chesed", "lovingkindness / mercy"),
    ("H7676", "shabbat", "sabbath"),
    ("H1697", "dabar", "word / thing"),
]

# Superscription Psalms — KJV folds the superscription into an unnumbered heading,
# Hebrew (BHS) counts it as verse 1. If heb.db uses Hebrew versification the body
# text lands one/two verses LATE versus KJV. We dump these to eyeball it.
SUPERSCRIPT_PSALMS = [3, 51]


def ro(path):
    if not os.path.exists(path):
        raise SystemExit(f"NOT FOUND: {path}")
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def hbar(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def heb_verse_keys(heb, sid):
    """Set of (book, chapter, verse) where heb_words tags this H-number, plus the
    raw word count. Matches the exact number OR a trailing-letter homograph form
    (H1254a) defensively, the way views_seo.py does."""
    rows = heb.execute(
        "SELECT book, chapter, verse FROM heb_words "
        "WHERE strongs = ? OR strongs GLOB ?",
        (sid, sid + "[A-Za-z]"),
    ).fetchall()
    keys = {(r["book"], r["chapter"], r["verse"]) for r in rows}
    return keys, len(rows)


def kjv_verse_keys(bible, sid, id2ab):
    """Set of (abbrev, chapter, verse) where the KJV bridge tags this H-number,
    plus the raw word count."""
    rows = bible.execute(
        "SELECT kw.book_id AS bid, kw.chapter AS ch, kw.verse_num AS v "
        "FROM kjv_strongs ks JOIN kjv_words kw ON kw.word_id = ks.word_id "
        "WHERE ks.strongs_id = ?",
        (sid,),
    ).fetchall()
    keys = {(id2ab.get(r["bid"], f"?{r['bid']}"), r["ch"], r["v"]) for r in rows}
    return keys, len(rows)


def main():
    ap = argparse.ArgumentParser()
    home = os.path.expanduser("~")
    ap.add_argument("--bible", default=os.path.join(home, "bible-db", "bible.db"))
    ap.add_argument("--heb", default=os.path.join(home, "bible-db", "heb.db"))
    args = ap.parse_args()

    bible = ro(args.bible)
    heb = ro(args.heb)

    # books: id <-> abbrev (KJV uses 1-66 book ids; heb_words uses the abbrev)
    id2ab = {r["id"]: r["abbrev"] for r in bible.execute("SELECT id, abbrev FROM books")}

    # ── 1. KEY FORMAT ────────────────────────────────────────────────────────
    hbar("1. heb_words.strongs KEY FORMAT")
    total_words = heb.execute("SELECT COUNT(*) AS c FROM heb_words").fetchone()["c"]
    distinct_h = heb.execute("SELECT COUNT(DISTINCT strongs) AS c FROM heb_words").fetchone()["c"]
    nulls = heb.execute("SELECT COUNT(*) AS c FROM heb_words WHERE strongs IS NULL").fetchone()["c"]
    print(f"heb_words rows: {total_words:,}   distinct strongs: {distinct_h:,}   NULL strongs: {nulls:,}")
    sample_keys = heb.execute(
        "SELECT DISTINCT strongs FROM heb_words WHERE strongs IS NOT NULL "
        "ORDER BY strongs LIMIT 12"
    ).fetchall()
    print("sample keys:", ", ".join(r["strongs"] for r in sample_keys))
    # any NOT of the form H<digits> ?  (e.g. bare digits, trailing letters, lowercase)
    odd = heb.execute(
        "SELECT DISTINCT strongs FROM heb_words "
        "WHERE strongs IS NOT NULL AND strongs NOT GLOB 'H[0-9]*' LIMIT 12"
    ).fetchall()
    print("non 'H<digits>' keys:", ", ".join(r["strongs"] for r in odd) if odd else "(none — all H<digits>)")
    lettered = heb.execute(
        "SELECT DISTINCT strongs FROM heb_words "
        "WHERE strongs GLOB 'H[0-9]*[A-Za-z]' LIMIT 12"
    ).fetchall()
    print("trailing-letter keys:", ", ".join(r["strongs"] for r in lettered) if lettered else "(none)")
    leading_zero = heb.execute(
        "SELECT DISTINCT strongs FROM heb_words WHERE strongs GLOB 'H0*' LIMIT 12"
    ).fetchall()
    print("leading-zero keys:", ", ".join(r["strongs"] for r in leading_zero) if leading_zero else "(none — zeros stripped)")

    # ── 2. OCCURRENCE COUNTS: KJV bridge vs heb.db ───────────────────────────
    hbar("2. OCCURRENCE COUNTS — KJV bridge  vs  heb.db")
    print(f"{'word':<22}{'KJV verses':>11}{'heb verses':>11}{'KJV words':>10}{'heb words':>10}"
          f"{'only-KJV':>9}{'only-heb':>9}")
    for sid, xlit, _gloss in SAMPLES:
        hkeys, hwords = heb_verse_keys(heb, sid)
        kkeys, kwords = kjv_verse_keys(bible, sid, id2ab)
        only_kjv = len(kkeys - hkeys)
        only_heb = len(hkeys - kkeys)
        label = f"{sid} {xlit}"
        print(f"{label:<22}{len(kkeys):>11}{len(hkeys):>11}{kwords:>10}{hwords:>10}"
              f"{only_kjv:>9}{only_heb:>9}")
    print("\n(only-KJV = verses the bridge finds that heb.db doesn't; only-heb = the reverse.")
    print(" A handful is normal — KJV double-tags, heb.db splits prefixes. Dozens = a versification or coverage problem.)")

    # show a few divergent verses for ruach so drift is visible by eye
    hbar("2b. SAMPLE DIVERGENT VERSES for H7307 (ruach)")
    hkeys, _ = heb_verse_keys(heb, "H7307")
    kkeys, _ = kjv_verse_keys(bible, "H7307", id2ab)
    only_kjv = sorted(kkeys - hkeys)[:15]
    only_heb = sorted(hkeys - kkeys)[:15]
    print("only in KJV bridge:", ", ".join(f"{b} {c}:{v}" for b, c, v in only_kjv) or "(none)")
    print("only in heb.db   :", ", ".join(f"{b} {c}:{v}" for b, c, v in only_heb) or "(none)")

    # ── 3. VERSIFICATION — superscription Psalms ─────────────────────────────
    hbar("3. VERSIFICATION CHECK — superscription Psalms (Psa 3, Psa 51)")
    print("If heb.db v1 reads like the SUPERSCRIPTION ('to the chief musician / of David'),")
    print("it uses HEBREW versification (offset). If it reads like the BODY, it matches KJV/ABP.\n")
    for ch in SUPERSCRIPT_PSALMS:
        print(f"--- Psalm {ch} ---")
        for v in (1, 2, 3):
            words = heb.execute(
                "SELECT gloss FROM heb_words WHERE book='Psa' AND chapter=? AND verse=? "
                "ORDER BY position LIMIT 10",
                (ch, v),
            ).fetchall()
            glosses = " ".join((w["gloss"] or "").strip() for w in words if (w["gloss"] or "").strip())
            print(f"  heb.db Psa {ch}:{v}  {glosses[:90]}")
        krow = bible.execute(
            "SELECT verse_text FROM kjv_verses kv JOIN books b ON b.id = kv.book_id "
            "WHERE b.abbrev='Psa' AND kv.chapter=? AND kv.verse_num=1",
            (ch,),
        ).fetchone()
        print(f"  KJV    Psa {ch}:1  {(krow['verse_text'] if krow else '')[:90]}")
        print()

    # ── 4. COVERAGE — H-numbers in one source but not the other ──────────────
    hbar("4. COVERAGE — H-numbers in the KJV OT / bdb but MISSING from heb.db")
    kjv_h = {r["s"] for r in bible.execute(
        "SELECT DISTINCT strongs_id AS s FROM kjv_strongs WHERE strongs_id LIKE 'H%'")}
    heb_h = {r["s"] for r in heb.execute(
        "SELECT DISTINCT strongs AS s FROM heb_words WHERE strongs LIKE 'H%'")}
    bdb_h = {r["s"] for r in bible.execute("SELECT DISTINCT strongs_id AS s FROM bdb")}
    miss_from_heb = kjv_h - heb_h
    new_in_heb = heb_h - kjv_h
    bdb_miss = bdb_h - heb_h
    print(f"distinct H-numbers — KJV OT: {len(kjv_h):,}   heb.db: {len(heb_h):,}   bdb: {len(bdb_h):,}")
    print(f"in KJV OT but NOT in heb.db: {len(miss_from_heb):,}  "
          f"e.g. {', '.join(sorted(miss_from_heb)[:15])}")
    print(f"in heb.db but NOT in KJV OT: {len(new_in_heb):,}  "
          f"e.g. {', '.join(sorted(new_in_heb)[:15])}")
    print(f"in bdb (lexicon) but NOT in heb.db: {len(bdb_miss):,}  (these are dictionary-only entries)")

    bible.close()
    heb.close()
    print("\nDone — read-only, nothing was modified.")


if __name__ == "__main__":
    main()
