#!/usr/bin/env python3
"""
audit_lsj_homograph.py — READ-ONLY. Find every Strong's number whose LSJ word-study
lookup lands on the WRONG headword because of an accent-collapse homograph trap.

THE TRAP (G2372 θυμός is the worked example):
  The lexicon lemma is plain `θυμός` (plain upsilon). LSJ stores the real "rage/spirit"
  entry under `θῡμός` (upsilon + a vowel-LENGTH mark). Those two letters aren't equal, so
  the lookup's EXACT match (`key = lemma`) misses. It falls to the accent-stripped
  fallback (`lower(strip_accents(key)) = lower(strip_accents(lemma))`), which removes the
  length mark AND the accent — collapsing `θῡμός` (rage), `θύμος` (thyme, accent on the
  first vowel) and `θύμος (2)` (warty excrescence) all to `θυμος`. The fallback then takes
  the FIRST row by table order, which is the thyme stub → it follows "see θύμον" and
  returns "Cretan thyme".

  The fix lever: the marks that differ between the lemma and the right key are vowel-LENGTH
  marks (macron U+0304 / breve U+0306), not accents. Folding ONLY those (keeping the
  accent) splits the homographs apart again:
      lemma θυμός  -> θυμός
      rage  θῡμός  -> θυμός   (unique match)
      thyme θύμος  -> θύμος   (accent on the other vowel, no longer collides)

DETECTION (mirrors the live lookup in views_lsj.py, lsj_lookup / lsj_summary):
  For each Greek lexicon lemma with no EXACT lsj key match:
    - plain = strip_all_marks(lemma)              (what the live fallback compares on)
    - matches = all lsj keys (not '-...' suffix headwords) that strip to the same plain
    - the live pick = the FIRST of those by rowid (what .fetchone() returns)
    - the DESIRED pick = the match whose LENGTH-folded key (accents kept) equals the
      length-folded lemma, when that is unique
  A row is a TRAP when matches >= 2 AND the live pick != the desired pick (i.e. the
  fallback grabs a different-accent homograph / stub instead of the right entry).

  Also reports a softer bucket: SINGLE wrong match — no exact key, exactly one fallback
  match, but its length-folded form differs from the lemma's (the lookup returns a
  word that isn't really the lemma).

READ-ONLY (opens the DB mode=ro). Never writes. Run on PA from the repo root:
  python3 scripts/audit_lsj_homograph.py bible.db
  python3 scripts/audit_lsj_homograph.py bible.db --list        # full per-number list
  python3 scripts/audit_lsj_homograph.py bible.db --corpus-only  # only Strong's used in words

Re-run after the fix: the TRAP count must drop to 0.
"""
import argparse
import re
import sqlite3
import sys
import unicodedata

# Vowel-LENGTH marks only — macron (U+0304) and breve (U+0306). Folding just these,
# keeping the accents/breathings, is the disambiguating key the fix will use.
_LEN_MARKS = {"̄", "̆"}


def strip_all_marks(s):
    """Drop EVERY combining mark — matches core._strip_accents (the live fallback key)."""
    if not s:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def fold_length(s):
    """Drop ONLY vowel-length marks, keep accents/breathings. The disambiguating key."""
    if not s:
        return ""
    return unicodedata.normalize(
        "NFC",
        "".join(c for c in unicodedata.normalize("NFD", s) if c not in _LEN_MARKS),
    )


_GREEK_RE = re.compile(r"[Ͱ-Ͽἀ-῿]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--list", action="store_true", help="print every flagged number")
    ap.add_argument("--corpus-only", action="store_true",
                    help="only Strong's numbers actually used in the words table")
    args = ap.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    # All LSJ keys in table (rowid) order — this is the order .fetchone() walks.
    # Skip suffix headwords ('-σε', '-θεν'…) exactly like the live query's
    # "AND key NOT LIKE '-%'".
    key_rows = conn.execute(
        "SELECT rowid AS rid, key, def_html FROM lsj WHERE key NOT LIKE '-%' ORDER BY rowid"
    ).fetchall()

    exact_keys = set()
    by_plain = {}   # stripped-all -> list of dicts (in rowid order)
    for r in key_rows:
        k = r["key"]
        exact_keys.add(k)
        plain = strip_all_marks(k.replace("-", "")).lower()
        by_plain.setdefault(plain, []).append({
            "rid": r["rid"],
            "key": k,
            "foldlen": fold_length(k.replace("-", "")).lower(),
            "is_xref_stub": _is_xref_stub(r["def_html"]),
        })

    used = None
    if args.corpus_only:
        used = {row[0] for row in conn.execute(
            "SELECT DISTINCT strongs_base FROM words WHERE strongs_base GLOB 'G*'"
        ).fetchall()}

    lex_rows = conn.execute(
        "SELECT strongs, lemma FROM lexicon WHERE lemma IS NOT NULL AND lemma != ''"
    ).fetchall()
    conn.close()

    traps = []        # >=2 matches, live pick != desired
    single_wrong = [] # 1 match, accent (length-fold) differs from lemma
    scanned = 0

    for lr in lex_rows:
        lemma = lr["lemma"].strip()
        if not _GREEK_RE.search(lemma):
            continue
        if used is not None and ("G" + str(lr["strongs"])) not in used:
            continue
        scanned += 1

        if lemma in exact_keys:
            continue  # exact match works, no fallback

        plain = strip_all_marks(lemma.replace("-", "")).lower()
        matches = by_plain.get(plain, [])
        if not matches:
            continue  # no LSJ entry at all -> falls through to Strong's gloss (not this bug)

        live = matches[0]  # .fetchone() order
        lem_fold = fold_length(lemma.replace("-", "")).lower()
        desired = [m for m in matches if m["foldlen"] == lem_fold]

        if len(matches) >= 2:
            # The trap: a unique length-fold match exists and it's NOT the one live picks.
            if len(desired) == 1 and desired[0]["key"] != live["key"]:
                traps.append({
                    "strongs": lr["strongs"], "lemma": lemma,
                    "live": live["key"], "live_stub": live["is_xref_stub"],
                    "desired": desired[0]["key"], "n": len(matches),
                })
        else:
            # Exactly one fallback match; if its accent pattern differs from the lemma's,
            # the lookup is returning a different word than asked for.
            if live["foldlen"] != lem_fold:
                single_wrong.append({
                    "strongs": lr["strongs"], "lemma": lemma,
                    "live": live["key"], "live_stub": live["is_xref_stub"],
                })

    scope = "in-corpus" if args.corpus_only else "all-lexicon"
    print(f"Scanned {scanned} Greek lexicon lemmas ({scope}).")
    print(f"TRAPS (homograph collision, live pick is WRONG): {len(traps)}")
    print(f"SINGLE wrong-accent matches (softer bucket):      {len(single_wrong)}")

    if args.list or len(traps) <= 40:
        print("\n-- TRAPS --")
        for t in sorted(traps, key=lambda x: int(re.sub(r"\D", "", x['strongs']) or 0)):
            stub = " [stub->xref]" if t["live_stub"] else ""
            print(f"  G{t['strongs']:<6} {t['lemma']:<16} live={t['live']!r}{stub}"
                  f"  -> should be {t['desired']!r}  (of {t['n']} collisions)")

    if args.list:
        print("\n-- SINGLE wrong-accent --")
        for t in sorted(single_wrong, key=lambda x: int(re.sub(r"\D", "", x['strongs']) or 0)):
            stub = " [stub->xref]" if t["live_stub"] else ""
            print(f"  G{t['strongs']:<6} {t['lemma']:<16} live={t['live']!r}{stub}")


_XREF_RE = re.compile(r"\bv\.\s*<i>([^<]+)</i>")


def _is_xref_stub(def_html):
    """A bare 'v. <i>word</i>' cross-reference stub (the thyme-pointer class)."""
    if not def_html:
        return False
    text = re.sub(r"<[^>]+>", "", def_html).strip()
    return len(text) <= 150 and bool(_XREF_RE.search(def_html))


if __name__ == "__main__":
    main()
