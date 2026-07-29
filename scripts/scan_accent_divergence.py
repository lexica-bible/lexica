#!/usr/bin/env python3
"""scan_accent_divergence.py — class scan for the Νῶε/Νώε card defect (JP sighting
2026-07-29, 1Ch 1:4 G3575): the word card's "IN THIS VERSE" section fires whenever the
in-verse form (abp_surface, scraped source) differs from the dictionary headword
(lexicon lemma) by a raw character compare — so a mere ACCENT divergence between the
two sources triggers a section meant for real inflection (case endings).

Read-only. Buckets every ABP words row that has BOTH a lemma and an abp_surface form:
  identical      — no section fires (correct)
  ACCENT-ONLY    — differs only in accents/breathing/case/final-sigma → the FALSE-FIRE
                   class (an indeclinable name like Νῶε can never truly inflect)
  letter-differ  — real form difference (genuine inflection; the section is doing its job)
Split PN vs non-PN (answers whether non-name cards share the defect).

Control (fire-proof): 1Ch 1:4 G3575 must land in ACCENT-ONLY or the scan is not trusted.

Usage (on PA):
  python3 scripts/scan_accent_divergence.py ~/bible-db/bible.db
"""
import sqlite3
import sys
import unicodedata


def fold(s):
    """Accent-insensitive key: decompose, drop combining marks, lowercase,
    final sigma -> sigma. Letters only survive."""
    d = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in d if not unicodedata.combining(c)).lower().replace("ς", "σ")


def main():
    db = sys.argv[1]
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT v.book, v.chapter, v.verse, w.position, w.is_pn, w.strongs_base,
                  l.lemma AS lemma, s.form AS surface
           FROM words w
           JOIN verses v ON v.id = w.verse_id
           LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base
           JOIN abp_surface s ON s.verse_id = w.verse_id AND s.position = w.position
           WHERE l.lemma IS NOT NULL AND s.form IS NOT NULL AND s.form != ''"""
    ).fetchall()

    ident = accent_pn = accent_other = letter = 0
    samples = {"pn": [], "other": []}
    control_hit = None
    for r in rows:
        lem, sur = r["lemma"], r["surface"]
        if lem == sur:
            ident += 1
            continue
        if fold(lem) == fold(sur):
            key = "pn" if r["is_pn"] else "other"
            if r["is_pn"]:
                accent_pn += 1
            else:
                accent_other += 1
            if len(samples[key]) < 12:
                samples[key].append(f"{r['book']} {r['chapter']}:{r['verse']} pos {r['position']} "
                                    f"{r['strongs_base']}  {lem} vs {sur}")
            if (r["book"], r["chapter"], r["verse"], r["strongs_base"]) == ("1Ch", 1, 4, "G3575"):
                control_hit = f"{lem} vs {sur}"
        else:
            letter += 1

    print(f"rows compared (lemma + surface both present): {len(rows)}")
    print(f"  identical:      {ident}")
    print(f"  ACCENT-ONLY:    {accent_pn + accent_other}  (PN {accent_pn} / non-PN {accent_other})  <- false-fire class")
    print(f"  letter-differ:  {letter}  (real inflection, section legitimate)")
    print("\n  PN samples:");    [print("   ", s) for s in samples["pn"]]
    print("\n  non-PN samples:"); [print("   ", s) for s in samples["other"]]
    if control_hit:
        print(f"\nCONTROL PASS: 1Ch 1:4 G3575 in ACCENT-ONLY ({control_hit})")
        sys.exit(0)
    print("\nCONTROL FAIL: 1Ch 1:4 G3575 NOT flagged ACCENT-ONLY — do not trust this scan.")
    sys.exit(1)


if __name__ == "__main__":
    main()
