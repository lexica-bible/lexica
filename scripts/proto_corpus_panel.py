#!/usr/bin/env python3
"""
proto_corpus_panel.py — READ-ONLY proving artifact for the "Ask the corpus" enrichment.

WHAT THIS IS
  Step ONE of the corpus-enrichment work (chat design 2026-06-29): the deterministic
  "lexical-texture" panel that would eventually bolt ABOVE the existing grounded note —
  WITHOUT touching ai.py, _CURATION_SYSTEM, or anything live. It just COUNTS and PRINTS,
  so we can judge — on real numbers — whether the buckets read as TEXT-DERIVED or as a
  received theology grid.

  Parameterised by --query so we can prove TWO things on the same cheap script:
    fire     — the MULTI-WORD case: proves the panel surfaces real structure when several
               distinct words exist (proved 2026-06-29: only "purification" had a carrier
               word; judgment/presence/protection were grid-over-esh — exactly as suspected).
    sabbath  — the SINGLE-FAMILY / FLAT case: proves the panel does NOT manufacture lexical
               structure when the concept is carried by ONE word-family (sabbaton + sabbatismos
               + shabbat — near-synonyms, one root each language). The honest output is FLAT:
               one dominant word per language, near-hapax relatives, near-identical ranges.
               If sabbath comes back artificially rich, that's a bug to find BEFORE building.

THE DISCIPLINE IT ENFORCES (the whole reason we do it cheap first)
  * The ONLY no-grid-possible axis is the LEMMA. Every occurrence IS one Strong's number —
    that is computed fact, zero classification. So this panel buckets BY WORD, labels each
    word with its OWN attested range (word_gloss), and STOPS. It does NOT sub-sort a word's
    hits into presence / judgment / purification — that is the model-judgment-as-count trap.
    No theological category is ever defined here.
  * The count runs on the FULL occurrence set (a direct count over the words table by
    Strong's), NEVER on ai.py's _spread_sample (which flattens distribution by design) or
    even its LIMIT-500 result pool.
  * Computed vs generated line is hard: everything printed is COUNT or DICTIONARY GLOSS —
    fact. Not one word of synthesis.

HOW THE FAMILY IS HANDLED (search wide, show the boundary)
  Each query's family is SEEDED by hand below — candidate Strong's numbers, each tagged
  core / derived / peripheral. They are CANDIDATES: the script self-verifies every one by
  printing its lemma + gloss + count, so a wrong/irrelevant seed is obvious on the first run
  (count 0 / no gloss → drop it; 'isheh H801 "food offering" was dropped this way). Honest
  seeds EXCLUDE different-root thematic relatives (e.g. sabbath EXCLUDES katapausis/anapausis/
  menuchah) — pulling those in would be the manufacture-structure move this script exists to
  catch. Auto-assembling the family for arbitrary queries is the NEXT step, and it must carry
  the same visible boundary (state the inclusion rule, surface the borderline words).

THE LXX SEAM (the differentiator)
  ABP's OT half is the Septuagint (Greek), heb.db is the Hebrew MT — same verses, two
  languages. The seam asks, verse-level: where the Hebrew core word occurs, does the ABP
  Greek put its core word there? VERSE-LEVEL co-occurrence, NOT word alignment (a later
  refinement) — it proves the WORD maps across, NOT that the SENSE does.

RUN IT (on PythonAnywhere — bible.db + heb.db are PA-only):
    workon bible-env
    python scripts/proto_corpus_panel.py --query sabbath     # the flat-case floor check
    python scripts/proto_corpus_panel.py --query fire        # the multi-word case
    python scripts/proto_corpus_panel.py --query fire --scope corpus
    python scripts/proto_corpus_panel.py --query sabbath --seam-examples 15

Read-only: opens both DBs read-only and only SELECTs. Touches nothing, writes nothing.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core


# ── the prophets (ABP abbrevs) — fire's scope. Latter Prophets + Lamentations + Daniel.
# A JUDGMENT CALL, deliberately visible/editable. The whole-corpus column sits beside it.
PROPHETS = {
    "Isa", "Jer", "Lam", "Eze", "Dan",
    "Hos", "Joe", "Amo", "Oba", "Jon", "Mic", "Nah", "Hab", "Zep", "Hag", "Zec", "Mal",
}

# ── QUERY PROFILES — each is a SEEDED family (candidates the script verifies), a scope,
# and a Hebrew↔Greek core pair for the seam. tier is the hand-marked boundary: core = the
# concept's own noun; derived = a verb/agent-noun on the same root; peripheral = a relative
# or near-hapax. "why" is a human note for reading the output, NEVER a computed bucket.
PROFILES = {
    "fire": {
        "scope": PROPHETS,
        "scope_label": "the prophets",
        "family": [
            ("H", "784",  "core",       "esh — fire (the OT workhorse noun)"),
            ("H", "8313", "derived",    "saraph — to burn (verb)"),
            ("H", "3852", "peripheral", "lehabah — flame"),
            ("H", "181",  "peripheral", "ud — firebrand, brand"),
            ("G", "4442", "core",       "pyr — fire (the Greek workhorse noun)"),
            ("G", "4448", "derived",    "pyroo — to burn; refine/test by fire (verb)"),
            ("G", "4451", "derived",    "pyrosis — a burning"),
            ("G", "4447", "peripheral", "pyrinos — fiery (adj.)"),
            ("G", "4443", "peripheral", "pyra — a fire (heap/pile lit)"),
            ("G", "329",  "peripheral", "anazopyreo — to rekindle (near-hapax, NT-only)"),
            ("G", "5395", "peripheral", "phlox — flame"),
        ],
        # ('isheh H801 "food offering" dropped 2026-06-29 — stem-matched in, not a fire word.)
        "seam": ("784", "4442", "esh", "pyr"),
    },
    "sabbath": {
        # Whole corpus — a sabbath query isn't scoped to a corner of the canon.
        "scope": None,
        "scope_label": "whole corpus",
        "family": [
            # Hebrew — the shabat root ONLY (no different-root rest words).
            ("H", "7676", "core",       "shabbat — sabbath (the day / rest, OT noun)"),
            ("H", "7673", "derived",    "shabath — to cease, desist, rest (verb)"),
            ("H", "7677", "derived",    "shabbathon — solemn rest, sabbath-observance"),
            ("H", "4868", "peripheral", "mishbath — cessation (rare)"),
            # Greek — the sabbaton root ONLY.
            ("G", "4521", "core",       "sabbaton — sabbath; also the seven-day week"),
            ("G", "4520", "derived",    "sabbatismos — a sabbath-rest / keeping (Heb 4:9)"),
            ("G", "4315", "peripheral", "prosabbaton — the day before the sabbath (1x)"),
        ],
        # DELIBERATELY EXCLUDED (different root — including them would FAKE multi-word texture):
        #   katapausis G2663 / anapausis G372 "rest"; menuchah H4496 / noach H5117 "rest".
        "seam": ("7676", "4521", "shabbat", "sabbaton"),
    },
}


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
    Counts by strongs_base (prefixed 'G####'), folding dotted variants into the base — right
    for a concept count. Independent of any sampling."""
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


def build_rows(conn, hconn, scope_books, family):
    """One row per seeded family member: lang, num, tier, translit, lemma, scoped, total, range."""
    rows = []
    for lang, num, tier, why in family:
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


def print_distribution(query, rows, scope_label):
    print("\n" + "=" * 78)
    print(f"  LEXICAL-TEXTURE PANEL — {query} — scope: {scope_label}")
    print("=" * 78)
    print("  Each row is a real word with a real count and its OWN dictionary range.")
    print("  No theological category was imposed. Bucketing = the lemma itself (fact).\n")

    for lang, title in (("H", "HEBREW (heb.db — Hebrew MT)"), ("G", "GREEK (ABP — LXX/NT)")):
        grp = [r for r in rows if r["lang"] == lang]
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
    print("   • A putative function is TEXT-DERIVED only if a DISTINCT word above carries it,")
    print("     with its OWN distinct range. Near-identical ranges across rows = ONE family (flat),")
    print("     NOT a multi-word texture — do not let a near-synonym pose as a separate sense.")
    print("   • A function with NO row carrying it is core-word-IN-CONTEXT — a grid laid over the")
    print("     workhorse noun, not a lexical fact. The panel cannot and does NOT count it.")
    print("   • Dominance ('mostly X') is CONTEXTUAL, not lexical — by design it does not appear")
    print("     here. If you want it, it is a reading, and it crosses the computed/generated line.")


def _heb_keys(hconn, num):
    return {
        (r["book"], r["chapter"], r["verse"])
        for r in hconn.execute(
            "SELECT book, chapter, verse FROM heb_words WHERE strongs=? OR strongs GLOB ?",
            (f"H{num}", f"H{num}[A-Za-z]"),
        )
    }


def _greek_keys(conn, num):
    return {
        (r["book"], r["chapter"], r["verse"])
        for r in conn.execute(
            "SELECT v.book, v.chapter, v.verse FROM words w JOIN verses v ON w.verse_id=v.id "
            "WHERE w.strongs_base=?",
            (f"G{num}",),
        )
    }


def print_seam(conn, hconn, scope_books, scope_label, seam, n_examples):
    heb_num, grk_num, heb_lbl, grk_lbl = seam
    print("\n" + "=" * 78)
    print(f"  LXX SEAM — Hebrew {heb_lbl} (H{heb_num}) vs ABP Greek {grk_lbl} (G{grk_num}), verse-level")
    print("=" * 78)
    if hconn is None:
        print("  heb.db not available — seam skipped.\n")
        return
    heb = _heb_keys(hconn, heb_num)
    grk = _greek_keys(conn, grk_num)
    if not heb:
        print(f"  No {heb_lbl} occurrences found — check the H{heb_num} seed.\n")
        return
    print("  (verse-level co-occurrence, NOT word alignment — proves the WORD maps, not the SENSE)\n")

    def report(label, books):
        h = {k for k in heb if (books is None or k[0] in books)}
        g = {k for k in grk if (books is None or k[0] in books)}
        both = h & g
        only_h = h - g
        pct = (100 * len(both) / len(h)) if h else 0
        print(f"  {label}:")
        print(f"     {heb_lbl} verses: {len(h):>4}   of those with {grk_lbl} in ABP: {len(both):>4}  ({pct:.0f}%)")
        print(f"     {heb_lbl} verses where ABP did NOT use {grk_lbl} (rendered otherwise): {len(only_h)}")
        return only_h

    report("Whole OT", None)
    only_scope = None
    if scope_books is not None:
        print()
        only_scope = report(f"Scope ({scope_label})", scope_books)

    sample = sorted(only_scope if only_scope is not None else (heb - grk))
    if sample and n_examples:
        print(f"\n  Sample verses where {heb_lbl} is present but ABP has no {grk_lbl} (the divergence to inspect):")
        for k in sample[:n_examples]:
            print(f"     {k[0]} {k[1]}:{k[2]}")
    print()


def main():
    ap = argparse.ArgumentParser(description="Read-only lexical-texture panel proving artifact.")
    ap.add_argument("--query", choices=sorted(PROFILES), default="fire",
                    help="which seeded query to run (default: fire)")
    ap.add_argument("--scope", choices=["auto", "prophets", "corpus"], default="auto",
                    help="count window: the profile default (auto), the prophets, or whole Bible")
    ap.add_argument("--seam-examples", type=int, default=10,
                    help="how many core-Hebrew-without-core-Greek verses to list (0 = none)")
    args = ap.parse_args()

    prof = PROFILES[args.query]
    if args.scope == "corpus":
        scope_books, scope_label = None, "whole corpus"
    elif args.scope == "prophets":
        scope_books, scope_label = PROPHETS, "the prophets"
    else:
        scope_books, scope_label = prof["scope"], prof["scope_label"]

    conn = core.db_ro()
    try:
        hconn = core.heb_db()
    except Exception:
        hconn = None

    try:
        rows = build_rows(conn, hconn, scope_books, prof["family"])
        print_distribution(args.query, rows, scope_label)
        print_seam(conn, hconn, scope_books, scope_label, prof["seam"], args.seam_examples)
    finally:
        conn.close()
        if hconn is not None:
            hconn.close()


if __name__ == "__main__":
    main()
