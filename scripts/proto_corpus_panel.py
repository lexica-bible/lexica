#!/usr/bin/env python3
"""
proto_corpus_panel.py — READ-ONLY proving artifact for the "Ask the corpus" enrichment.

WHAT THIS IS
  Step ONE of the corpus-enrichment work (chat design 2026-06-29): the deterministic
  "lexical-texture" panel that would eventually bolt ABOVE the existing grounded note —
  WITHOUT touching ai.py, _CURATION_SYSTEM, or anything live. It just COUNTS and PRINTS,
  so we can judge — on real numbers, on the proving query "fire across the prophets" —
  whether the buckets read as TEXT-DERIVED or as a received theology grid.

THE DISCIPLINE IT ENFORCES (the whole reason we do it cheap first)
  * The ONLY no-grid-possible axis is the LEMMA. Every occurrence IS one Strong's number —
    that is computed fact, zero classification. So this panel buckets BY WORD, labels each
    word with its OWN attested range (word_gloss), and STOPS. It does NOT sub-sort esh's
    hundreds of hits into presence / judgment / purification — that is the model-judgment-
    as-count trap. No theological category is ever defined here.
  * The count runs on the FULL occurrence set (a direct count over the words table by
    Strong's), NEVER on ai.py's _spread_sample (which flattens distribution by design) or
    even its LIMIT-500 result pool.
  * Computed vs generated line is hard: everything this script prints is COUNT or DICTIONARY
    GLOSS — fact. Not one word of synthesis. The "these N mean X" step stays the model's job,
    later, and only if the panel proves the substrate is honest.

HOW THE FAMILY IS HANDLED (search wide, show the boundary)
  The fire family is SEEDED by hand below (FIRE_FAMILY) — candidate Strong's numbers, each
  tagged core / derived / peripheral. They are CANDIDATES: the script self-verifies every one
  by printing its lemma + gloss + count, so a wrong seed number is obvious on the first run
  (count 0 / no gloss → drop it). Auto-assembling the family for ARBITRARY queries is a later
  step; "fire" is cross-lingual (esh and pyr are translation-equivalents, not cognates), which
  is exactly why the generic cognate expander in ai.py would NOT build this family correctly.

THE LXX SEAM (the differentiator)
  ABP's OT half is the Septuagint (Greek), heb.db is the Hebrew MT — same verses, two
  languages. The seam section asks, verse-level: where Hebrew esh (H784) occurs, does the
  ABP Greek put pyr (G4442) there? It is VERSE-LEVEL co-occurrence, NOT word alignment (a
  later refinement) — labelled as such, never overstated.

RUN IT (on PythonAnywhere — bible.db + heb.db are PA-only):
    workon bible-env
    python scripts/proto_corpus_panel.py                 # fire across the prophets
    python scripts/proto_corpus_panel.py --scope corpus  # whole Bible, not just the prophets
    python scripts/proto_corpus_panel.py --seam-examples 15

Read-only: opens both DBs read-only and only SELECTs. Touches nothing, writes nothing.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core


# ── the prophets (ABP abbrevs) — the query's scope. Latter Prophets + Lamentations + Daniel.
# This is a JUDGMENT CALL and deliberately visible/editable: trim Lam/Dan if you mean the
# Latter Prophets strictly. The whole-corpus column is always shown beside the scoped one.
PROPHETS = {
    "Isa", "Jer", "Lam", "Eze", "Dan",
    "Hos", "Joe", "Amo", "Oba", "Jon", "Mic", "Nah", "Hab", "Zep", "Hag", "Zec", "Mal",
}

NT_BOOKS = {
    "Mat", "Mar", "Luk", "Joh", "Act", "Rom", "1Co", "2Co", "Gal", "Eph", "Php", "Col",
    "1Th", "2Th", "1Ti", "2Ti", "Tit", "Phm", "Heb", "Jas", "1Pe", "2Pe", "1Jn", "2Jn",
    "3Jn", "Jud", "Rev",
}

# ── SEEDED fire family — CANDIDATES (the script verifies each). tier is the hand-marked
# boundary: core = the fire noun itself; derived = a verb/agent-noun on the same root;
# peripheral = a flame/firebrand relative or a near-hapax metaphor. "why" is just a human
# note for reading the output — it is NEVER used as a computed bucket.
FIRE_FAMILY = [
    # lang  strongs  tier         why (human note, not a computed category)
    ("H", "784",  "core",       "esh — fire (the OT workhorse noun)"),
    ("H", "8313", "derived",    "saraph — to burn (verb)"),
    ("H", "3852", "peripheral", "lehabah — flame"),
    ("H", "801",  "derived",    "ishsheh — offering made by fire"),
    ("H", "181",  "peripheral", "ud — firebrand, brand"),
    ("G", "4442", "core",       "pyr — fire (the Greek workhorse noun)"),
    ("G", "4448", "derived",    "pyroo — to burn; refine/test by fire (verb)"),
    ("G", "4451", "derived",    "pyrosis — a burning"),
    ("G", "4447", "peripheral", "pyrinos — fiery (adj.)"),
    ("G", "4443", "peripheral", "pyra — a fire (heap/pile lit)"),
    ("G", "329",  "peripheral", "anazopyreo — to rekindle, stir up (near-hapax)"),
    ("G", "5395", "peripheral", "phlox — flame"),
]


def _has_table(conn, name):
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone())


def _cols(conn, table):
    try:
        return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
    except Exception:
        return set()


def _word_gloss(conn, prefixed):
    """Plain attested range for a fully-prefixed Strong's ('G4442' / 'H784') from word_gloss;
    '' if the table or the row is absent. This is the lemma's OWN range — the bucket label."""
    if not _has_table(conn, "word_gloss"):
        return ""
    r = conn.execute("SELECT gloss FROM word_gloss WHERE strongs=?", (prefixed,)).fetchone()
    return (r["gloss"] or "").strip() if r else ""


def _greek_lemma(conn, num):
    """(lemma, translit) for a bare Greek number from the lexicon, robust to whichever key
    column this build has (strongs_g 'G4442' indexed key, or the bare strongs PK)."""
    lc = _cols(conn, "lexicon")
    try:
        if "strongs_g" in lc:
            r = conn.execute(
                "SELECT lemma, translit FROM lexicon WHERE strongs_g=?", (f"G{num}",)
            ).fetchone()
            if r:
                return r["lemma"] or "", r["translit"] or ""
        r = conn.execute(
            "SELECT lemma, translit FROM lexicon WHERE strongs=?", (num,)
        ).fetchone()
        if r:
            return r["lemma"] or "", r["translit"] or ""
    except Exception:
        pass
    return "", ""


def _greek_count(conn, num, scope_books):
    """FULL occurrence count of a Greek base number in ABP words (corpus, then within scope).
    Counts by strongs_base (prefixed 'G####'), which folds dotted variants into the base —
    right for a concept count. Independent of any sampling."""
    total = conn.execute(
        "SELECT count(*) c FROM words WHERE strongs_base=?", (f"G{num}",)
    ).fetchone()["c"]
    if scope_books:
        qmarks = ",".join("?" for _ in scope_books)
        scoped = conn.execute(
            f"""SELECT count(*) c FROM words w JOIN verses v ON w.verse_id=v.id
                WHERE w.strongs_base=? AND v.book IN ({qmarks})""",
            (f"G{num}", *sorted(scope_books)),
        ).fetchone()["c"]
    else:
        scoped = total
    return scoped, total


def _heb_lemma(hconn, num):
    """A representative surface form + translit for a Hebrew number, from heb_words (the most
    frequent translit among its occurrences). Honest label = a common SURFACE form, NOT a
    dictionary headword (heb.db carries inflected surface, not lemmas)."""
    try:
        r = hconn.execute(
            "SELECT hebrew, translit, count(*) c FROM heb_words "
            "WHERE strongs=? OR strongs GLOB ? GROUP BY translit ORDER BY c DESC LIMIT 1",
            (f"H{num}", f"H{num}[A-Za-z]"),
        ).fetchone()
        if r:
            return r["hebrew"] or "", r["translit"] or ""
    except Exception:
        pass
    return "", ""


def _heb_count(hconn, num, scope_books):
    """FULL occurrence count of a Hebrew number in heb.db (corpus, then within scope), byforms
    folded in via the GLOB. Independent of any sampling."""
    try:
        total = hconn.execute(
            "SELECT count(*) c FROM heb_words WHERE strongs=? OR strongs GLOB ?",
            (f"H{num}", f"H{num}[A-Za-z]"),
        ).fetchone()["c"]
    except Exception:
        return 0, 0
    if scope_books:
        qmarks = ",".join("?" for _ in scope_books)
        scoped = hconn.execute(
            f"""SELECT count(*) c FROM heb_words
                WHERE (strongs=? OR strongs GLOB ?) AND book IN ({qmarks})""",
            (f"H{num}", f"H{num}[A-Za-z]", *sorted(scope_books)),
        ).fetchone()["c"]
    else:
        scoped = total
    return scoped, total


def build_rows(conn, hconn, scope_books):
    """One row per seeded family member: (lang, num, tier, translit, lemma, scoped, total, range)."""
    rows = []
    for lang, num, tier, why in FIRE_FAMILY:
        if lang == "G":
            lemma, translit = _greek_lemma(conn, num)
            scoped, total = _greek_count(conn, num, scope_books)
            rng = _word_gloss(conn, f"G{num}")
        else:
            lemma, translit = (_heb_lemma(hconn, num) if hconn else ("", ""))
            scoped, total = (_heb_count(hconn, num, scope_books) if hconn else (0, 0))
            rng = _word_gloss(conn, f"H{num}")
        rows.append({
            "lang": lang, "num": num, "tier": tier, "why": why,
            "translit": translit, "lemma": lemma,
            "scoped": scoped, "total": total, "range": rng,
        })
    return rows


def print_distribution(rows, scope_label, scope_books):
    print("\n" + "=" * 78)
    print(f"  LEXICAL-TEXTURE PANEL — fire — scope: {scope_label}")
    print("=" * 78)
    print("  Each row is a real word with a real count and its OWN dictionary range.")
    print("  No theological category was imposed. Bucketing = the lemma itself (fact).\n")

    for lang, title in (("H", "HEBREW (heb.db — Hebrew MT)"), ("G", "GREEK (ABP — LXX/NT)")):
        grp = [r for r in rows if r["lang"] == lang]
        # order: tier (core→derived→peripheral), then by the scoped count desc — the finding.
        tier_rank = {"core": 0, "derived": 1, "peripheral": 2}
        grp.sort(key=lambda r: (tier_rank.get(r["tier"], 9), -r["scoped"]))
        live = sum(r["scoped"] for r in grp)
        print(f"  ── {title} — {live} occurrence(s) in scope ──")
        print(f"     {'word':<22} {'tier':<11} {'in-scope':>9} {'corpus':>8}   attested range")
        print(f"     {'-'*22} {'-'*11} {'-'*9} {'-'*8}   {'-'*30}")
        for r in grp:
            tag = f"{r['lang']}{r['num']}"
            label = (r["translit"] or r["lemma"] or "?")
            name = f"{label} ({tag})"
            rng = r["range"] or "— no word_gloss row —"
            flag = "  ⚠seed?" if (r["scoped"] == 0 and r["total"] == 0 and not r["range"]) else ""
            print(f"     {name:<22} {r['tier']:<11} {r['scoped']:>9} {r['total']:>8}   {rng}{flag}")
        print()

    print("  HOW TO READ THIS (the text-derived vs grid audit):")
    print("   • A putative function is TEXT-DERIVED only if a DISTINCT word above carries it.")
    print("     e.g. 'purification' → look for a row whose range names refine/test-by-fire (pyroo).")
    print("   • A function with NO row carrying it (no distinct fire-word) is esh/pyr-IN-CONTEXT —")
    print("     i.e. a grid laid over the workhorse noun, not a lexical fact. The panel cannot and")
    print("     does NOT count it; that split would be the model talking, marked as generated.")
    print("   • Dominance ('mostly judgment') is CONTEXTUAL, not lexical — by design it does not")
    print("     appear here. If you want it, it is a reading, and it crosses the computed/generated line.")


def _greek_pyr_keys(conn):
    return {
        (r["book"], r["chapter"], r["verse"])
        for r in conn.execute(
            "SELECT v.book, v.chapter, v.verse FROM words w JOIN verses v ON w.verse_id=v.id "
            "WHERE w.strongs_base='G4442'"
        )
    }


def _heb_esh_keys(hconn):
    return {
        (r["book"], r["chapter"], r["verse"])
        for r in hconn.execute(
            "SELECT book, chapter, verse FROM heb_words WHERE strongs='H784' OR strongs GLOB 'H784[A-Za-z]'"
        )
    }


def print_seam(conn, hconn, scope_books, n_examples):
    print("\n" + "=" * 78)
    print("  LXX SEAM — Hebrew esh (H784) vs ABP Greek pyr (G4442), verse-level")
    print("=" * 78)
    if hconn is None:
        print("  heb.db not available — seam skipped.\n")
        return
    esh = _heb_esh_keys(hconn)
    pyr = _greek_pyr_keys(conn)
    if not esh:
        print("  No esh occurrences found — check the H784 seed.\n")
        return

    def report(label, books):
        e = {k for k in esh if (books is None or k[0] in books)}
        p = {k for k in pyr if (books is None or k[0] in books)}
        both = e & p
        only_e = e - p
        pct = (100 * len(both) / len(e)) if e else 0
        print(f"  {label}:")
        print(f"     esh verses: {len(e):>4}   of those with pyr in ABP: {len(both):>4}  ({pct:.0f}%)")
        print(f"     esh verses where ABP did NOT use pyr (Greek rendered it otherwise): {len(only_e)}")
        return only_e

    print("  (verse-level co-occurrence, NOT word alignment — a first-cut seam, honest about that)\n")
    report("Whole OT", None)
    print()
    only_e_scope = report("The prophets (scope)", scope_books)

    if only_e_scope and n_examples:
        print(f"\n  Sample prophet verses where esh is present but ABP has no pyr (the divergence to inspect):")
        for k in sorted(only_e_scope)[:n_examples]:
            print(f"     {k[0]} {k[1]}:{k[2]}")
    print()


def main():
    ap = argparse.ArgumentParser(description="Read-only lexical-texture panel proving artifact (fire).")
    ap.add_argument("--scope", choices=["prophets", "corpus"], default="prophets",
                    help="count window: the prophets (default) or the whole Bible")
    ap.add_argument("--seam-examples", type=int, default=10,
                    help="how many esh-without-pyr prophet verses to list (0 = none)")
    args = ap.parse_args()

    scope_books = None if args.scope == "corpus" else PROPHETS
    scope_label = "the prophets" if args.scope == "prophets" else "whole corpus"

    conn = core.db_ro()
    try:
        hconn = core.heb_db()
    except Exception:
        hconn = None

    try:
        rows = build_rows(conn, hconn, scope_books)
        print_distribution(rows, scope_label, scope_books)
        print_seam(conn, hconn, PROPHETS, args.seam_examples)
    finally:
        conn.close()
        if hconn is not None:
            hconn.close()


if __name__ == "__main__":
    main()
