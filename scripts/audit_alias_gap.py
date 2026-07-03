#!/usr/bin/env python3
"""
audit_alias_gap.py — READ-ONLY hunt for split-lemma Strong's pairs like charis/charin.

THE DISEASE (Batch D confirmed it on charis): the dictionary treats a Strong's number as
a real head word worth defining (it's in `lexicon`/`bdb`), and the parallel corpora
(KJV + BSB) tag it heavily — so the app "believes" it's a common word — BUT the primary
study corpus tags ~zero occurrences under it, because those occurrences actually live on a
NEIGHBOURING number. charis: dictionary + KJV/BSB use the textbook G5485; ABP parks every
occurrence on G5484 (the form charin). A retrieval / count / highlight keyed on G5485 then
finds nothing. LEXICA_ALIASES fixes each such pair by hand — this script finds candidates.

  Greek  primary corpus = ABP `words` (bible.db)          parallel = KJV + BSB
  Hebrew primary corpus = `heb_words` (heb.db, TAHOT OT)   parallel = KJV + BSB

THE SIGNATURE (a suspect):
  1. head exists in lexicon (Greek) / bdb (Hebrew), AND
  2. primary-corpus occurrence count <= NEAR_ZERO, AND
  3. NOT genuine rarity — the parallel corpora say it should be common
     (kjv+bsb count >= FREQ_FLOOR). A true hapax (parallel also ~0) is uninteresting.

NEIGHBOUR DETECTION (best-effort): for each suspect, look at adjacent numbers (±1..±3) for
one with an unexpectedly high primary-corpus count and a related transliteration/lemma stem
— that's probably where the occurrences went. No stem/adjacent hit → "destination unknown".

SANITY CHECK built in: charis (G5485) MUST appear, flagged `already-aliased` (it's in
LEXICA_ALIASES). If it doesn't, the detection is wrong — the script says so at the end.

Read-only: only SELECTs, never writes. Output feeds a human review; JP decides which rows
enter LEXICA_ALIASES. NOTHING here edits the map, the register, or any table.

  workon bible-env
  python scripts/audit_alias_gap.py                       # both testaments, writes CSV
  python scripts/audit_alias_gap.py --greek-only
  python scripts/audit_alias_gap.py --floor 20 --out /tmp/gap.csv
"""
import argparse, csv, os, sys, unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3

try:
    from contested_register import LEXICA_ALIASES
except Exception:
    LEXICA_ALIASES = {}

NEAR_ZERO   = 1     # primary-corpus count at or below this = "absent from the study corpus"
FREQ_FLOOR  = 10    # parallel (kjv+bsb) count at or above this = "the app thinks it's common"
NEIGHBOUR   = 3     # scan ±1..±this for the destination number
STEM_LEN    = 3     # transliteration prefix length for a stem match
HEB_CAP     = 30    # Hebrew is noisy (construct/plural variants) — cap the report, note the total


def strip(s):
    """lowercase, drop accents/breathing/macrons — so 'cháris' and 'charis' compare equal."""
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


# ── count helpers (each returns an int; missing table → 0, so a DB without BSB still runs) ──

def _has_table(conn, name):
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())


def abp_count(conn, num):
    return conn.execute(
        "SELECT count(*) FROM words WHERE strongs_base=?", (num,)).fetchone()[0]


def kjv_count(conn, num):
    if not _has_table(conn, "kjv_strongs"):
        return 0
    return conn.execute(
        "SELECT count(*) FROM kjv_strongs WHERE strongs_id=?", (num,)).fetchone()[0]


def bsb_count(conn, num):
    if not _has_table(conn, "bsb_strongs"):
        return 0
    return conn.execute(
        "SELECT count(*) FROM bsb_strongs WHERE strongs_id=?", (num,)).fetchone()[0]


def heb_count(hconn, num):
    if hconn is None:
        return 0
    # heb_words.strongs is prefixed 'H####'; suffix-lettered variants (H1234a) share the base.
    return hconn.execute(
        "SELECT count(*) FROM heb_words WHERE strongs=? OR strongs GLOB ?",
        (num, num + "[A-Za-z]")).fetchone()[0]


# ── neighbour search: where did the occurrences go? ──

def greek_neighbour(conn, base, translit):
    """Return (dest_num, dest_count, basis) for the ±NEIGHBOUR number with the highest ABP
    count (and, when possible, a shared translit stem). '' if nothing plausible."""
    stem = strip(translit)[:STEM_LEN]
    best = None
    for d in range(1, NEIGHBOUR + 1):
        for cand in (base - d, base + d):
            if cand <= 0:
                continue
            num = f"G{cand}"
            c = abp_count(conn, num)
            if c < FREQ_FLOOR:
                continue
            row = conn.execute(
                "SELECT translit FROM lexicon WHERE strongs_g=?", (num,)).fetchone()
            cand_stem = strip(row["translit"])[:STEM_LEN] if row and row["translit"] else ""
            match = bool(stem) and stem == cand_stem
            score = (1 if match else 0, c)
            if best is None or score > best[0]:
                best = (score, num, c, "adjacent+stem" if match else "adjacent")
    return (best[1], best[2], best[3]) if best else ("", 0, "unknown")


def heb_neighbour(conn, hconn, base, xlit):
    stem = strip(xlit)[:STEM_LEN]
    best = None
    for d in range(1, NEIGHBOUR + 1):
        for cand in (base - d, base + d):
            if cand <= 0:
                continue
            num = f"H{cand}"
            c = heb_count(hconn, num)
            if c < FREQ_FLOOR:
                continue
            row = conn.execute(
                "SELECT xlit FROM bdb WHERE strongs_id=?", (num,)).fetchone()
            cand_stem = strip(row["xlit"])[:STEM_LEN] if row and row["xlit"] else ""
            match = bool(stem) and stem == cand_stem
            score = (1 if match else 0, c)
            if best is None or score > best[0]:
                best = (score, num, c, "adjacent+stem" if match else "adjacent")
    return (best[1], best[2], best[3]) if best else ("", 0, "unknown")


def scan_greek(conn):
    rows = []
    heads = conn.execute(
        "SELECT strongs_g, strongs, lemma, translit FROM lexicon "
        "WHERE strongs_g IS NOT NULL AND strongs_g LIKE 'G%'").fetchall()
    for h in heads:
        num = h["strongs_g"]
        try:
            base = int(num[1:])
        except ValueError:
            continue
        a = abp_count(conn, num)
        if a > NEAR_ZERO:
            continue
        para = kjv_count(conn, num) + bsb_count(conn, num)
        if para < FREQ_FLOOR:
            continue                     # genuinely rare — uninteresting
        dest, dcount, basis = greek_neighbour(conn, base, h["translit"])
        rows.append({
            "corpus": "G/ABP",
            "suspect_number": num,
            "lemma": h["lemma"] or "",
            "translit": h["translit"] or "",
            "dict_expected_signal": f"kjv+bsb={para}",
            "gap": para - a,
            "abp_count": a,
            "probable_destination": dest,
            "destination_count": dcount,
            "match_basis": basis,
            "already_aliased": "yes" if num in LEXICA_ALIASES else "",
        })
    return rows


def scan_hebrew(conn, hconn):
    rows = []
    heads = conn.execute(
        "SELECT strongs_id, lemma, xlit FROM bdb "
        "WHERE strongs_id IS NOT NULL AND strongs_id LIKE 'H%'").fetchall()
    for h in heads:
        num = h["strongs_id"]
        try:
            base = int(num[1:])
        except ValueError:
            continue
        primary = heb_count(hconn, num)
        if primary > NEAR_ZERO:
            continue
        para = kjv_count(conn, num) + bsb_count(conn, num)
        if para < FREQ_FLOOR:
            continue
        dest, dcount, basis = heb_neighbour(conn, hconn, base, h["xlit"])
        rows.append({
            "corpus": "H/heb",
            "suspect_number": num,
            "lemma": h["lemma"] or "",
            "translit": h["xlit"] or "",
            "dict_expected_signal": f"kjv+bsb={para}",
            "gap": para - primary,
            "abp_count": primary,        # primary-corpus (heb.db) count for Hebrew rows
            "probable_destination": dest,
            "destination_count": dcount,
            "match_basis": basis,
            "already_aliased": "yes" if num in LEXICA_ALIASES else "",
        })
    return rows


COLS = ["corpus", "suspect_number", "lemma", "translit", "dict_expected_signal",
        "abp_count", "probable_destination", "destination_count", "match_basis",
        "already_aliased"]


def print_table(rows, title):
    print(f"\n=== {title} ({len(rows)} rows) ===")
    if not rows:
        print("  (none)")
        return
    hdr = f'{"suspect":>8} {"lemma":<14} {"translit":<14} {"signal":<12} {"prim":>4} ' \
          f'{"->dest":>7} {"dcount":>6}  {"basis":<14} alias'
    print(hdr)
    for r in rows:
        print(f'{r["suspect_number"]:>8} {(r["lemma"] or "")[:13]:<14} '
              f'{(r["translit"] or "")[:13]:<14} {r["dict_expected_signal"]:<12} '
              f'{r["abp_count"]:>4} {r["probable_destination"]:>7} {r["destination_count"]:>6}  '
              f'{r["match_basis"]:<14} {r["already_aliased"]}')


def main():
    global FREQ_FLOOR
    ap = argparse.ArgumentParser(description="Find split-lemma alias-gap Strong's pairs (read-only).")
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--db", default=os.path.join(here, "bible.db"))
    ap.add_argument("--heb", default=os.path.join(here, "heb.db"))
    ap.add_argument("--out", default=os.path.join(os.getcwd(), "alias_gap_audit.csv"))
    ap.add_argument("--floor", type=int, default=FREQ_FLOOR,
                    help="parallel-corpus (kjv+bsb) count that counts as 'should be common'")
    ap.add_argument("--greek-only", action="store_true")
    ap.add_argument("--hebrew-only", action="store_true")
    args = ap.parse_args()

    FREQ_FLOOR = args.floor

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    hconn = None
    if os.path.exists(args.heb) and not args.greek_only:
        hconn = sqlite3.connect(f"file:{args.heb}?mode=ro", uri=True)
        hconn.row_factory = sqlite3.Row

    n_greek_heads = conn.execute("SELECT count(*) FROM lexicon WHERE strongs_g LIKE 'G%'").fetchone()[0]

    greek = [] if args.hebrew_only else scan_greek(conn)
    greek.sort(key=lambda r: r["gap"], reverse=True)

    hebrew = []
    heb_total = 0
    if not args.greek_only and hconn is not None:
        hebrew = scan_hebrew(conn, hconn)
        hebrew.sort(key=lambda r: r["gap"], reverse=True)
        heb_total = len(hebrew)
        hebrew_report = hebrew[:HEB_CAP]
    else:
        hebrew_report = []

    print_table(greek, "GREEK alias-gap suspects (ABP)")
    print_table(hebrew_report, f"HEBREW alias-gap suspects (heb.db) — top {HEB_CAP} by gap")
    if heb_total > HEB_CAP:
        print(f"  … {heb_total - HEB_CAP} more Hebrew suspects not shown (see CSV).")

    # write full CSV (all Hebrew rows, not just the capped display)
    allrows = greek + hebrew
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        for r in allrows:
            w.writerow(r)

    # ── summary + the built-in sanity check ──
    aliased_hits = [r for r in allrows if r["already_aliased"]]
    print("\n=== summary ===")
    print(f"  Greek heads scanned:        {n_greek_heads}")
    print(f"  Greek suspects:             {len(greek)}")
    if not args.greek_only:
        print(f"  Hebrew suspects:            {heb_total}  (report capped at {HEB_CAP})")
    print(f"  already in LEXICA_ALIASES:  {len(aliased_hits)} -> "
          f"{', '.join(r['suspect_number'] for r in aliased_hits) or '(none)'}")
    print(f"  thresholds: primary<= {NEAR_ZERO}, parallel>= {FREQ_FLOOR}")
    print(f"  CSV written: {args.out}")

    charis_ok = any(r["suspect_number"] == "G5485" for r in greek)
    if charis_ok:
        print("\n  SANITY CHECK PASSED: charis G5485 surfaced (already-aliased). Detection is sound.")
    elif not args.hebrew_only:
        print("\n  *** SANITY CHECK FAILED: charis G5485 did NOT surface. Detection is WRONG — "
              "do not trust this report. ***")

    conn.close()
    if hconn is not None:
        hconn.close()


if __name__ == "__main__":
    main()
