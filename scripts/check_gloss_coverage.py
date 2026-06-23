#!/usr/bin/env python3
"""
check_gloss_coverage.py — READ-ONLY audit of word-card lemma-gloss coverage.

The word side-card shows a short dictionary gloss beside the lemma. Greek/ABP pulls
it from lexicon.kjv_def; Hebrew has none yet. This script answers, completely and
without writing anything: which Strong's numbers the reader actually uses, and which
have NO clean short gloss — so we can fill every gap to 100%.

It reads bible.db (Greek + KJV/BSB Strong's, lexicon, bdb) and, if given, heb.db
(the real Hebrew OT glosses). It prints a summary and writes the FULL gap lists to
two .tsv files next to where you run it, so nothing is sampled away.

Usage (on PythonAnywhere, where the databases live):
  python3 scripts/check_gloss_coverage.py ~/bible-db/bible.db --heb ~/bible-db/heb.db

Never modifies a database. Safe to run anytime.
"""
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict

DB = next((a for a in sys.argv[1:] if not a.startswith("--")), "bible.db")
HEB = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--heb=")), None)
if not HEB and "--heb" in sys.argv:                     # allow "--heb path" too
    i = sys.argv.index("--heb")
    if i + 1 < len(sys.argv):
        HEB = sys.argv[i + 1]


def has_table(conn, name):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def norm_h(s):
    """Fold a Hebrew number to its base for matching: H1234a -> H1234 (the byform
    letters TAHOT keeps to split homographs aren't in the KJV/BSB Strong's tables)."""
    m = re.match(r"^(H\d+)[a-z]?$", s or "")
    return m.group(1) if m else (s or "")


def pct(a, b):
    return f"{(100.0 * a / b):.1f}%" if b else "—"


conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
out_lines = []   # mirror summary to a file too


def say(s=""):
    print(s)
    out_lines.append(s)


# ===========================================================================
# PART A — GREEK lemma gloss (ABP reader, lexicon.kjv_def) — already shipped
# ===========================================================================
say("=" * 70)
say("PART A — GREEK lemma gloss  (ABP words -> lexicon.kjv_def)")
say("=" * 70)

# every distinct Greek number used in the ABP text + how many times
greek_occ = Counter()
for r in conn.execute("SELECT strongs_base, COUNT(*) n FROM words "
                      "WHERE strongs_base GLOB 'G*' GROUP BY strongs_base"):
    greek_occ[r["strongs_base"]] = r["n"]

# lexicon kjv_def + lemma, keyed by the G-prefixed join key
lex = {}
for r in conn.execute("SELECT strongs_g, lemma, kjv_def FROM lexicon WHERE strongs_g GLOB 'G*'"):
    lex[r["strongs_g"]] = (r["lemma"] or "", (r["kjv_def"] or "").strip())

# which Greek numbers ever appear WITH an inflected surface form (so the top gloss
# line is actually visible right now — that's the user-facing blank if it's missing)
surf = set()
if has_table(conn, "abp_surface"):
    for (sb,) in conn.execute(
        "SELECT DISTINCT w.strongs_base FROM words w "
        "JOIN abp_surface s ON s.verse_id=w.verse_id AND s.position=w.position "
        "WHERE w.strongs_base GLOB 'G*'"):
        surf.add(sb)

g_gap = []          # (number, occurrences, lemma, reason, visible_now)
for num, occ in greek_occ.items():
    lemma, kdef = lex.get(num, (None, None))
    if kdef:
        continue
    reason = "no lexicon row" if lemma is None else "row present, kjv_def empty"
    g_gap.append((num, occ, lemma or "", reason, num in surf))

g_total = len(greek_occ)
g_have = g_total - len(g_gap)
g_visible_gap = sum(1 for x in g_gap if x[4])
say(f"distinct Greek numbers in ABP text : {g_total}")
say(f"  have a kjv_def gloss             : {g_have}  ({pct(g_have, g_total)})")
say(f"  BLANK (no usable gloss)          : {len(g_gap)}")
say(f"    of those, visible now (have an inflected form line): {g_visible_gap}")

# dotted-number QUALITY flag: a dotted word that's a DIFFERENT word than its base
# shows the base's kjv_def (the join drops the dot). Coverage is fine; the gloss may
# just be the neighbour's. Count them so we know the accuracy ceiling.
dotted_diff = 0
if has_table(conn, "dotted_lexicon"):
    dotted_diff = conn.execute(
        "SELECT COUNT(DISTINCT w.strongs) FROM words w "
        "JOIN dotted_lexicon dl ON dl.strongs='G'||w.strongs "
        "WHERE w.strongs LIKE '%.%'").fetchone()[0]
    say(f"  dotted words shown with their BASE number's gloss (accuracy watch): {dotted_diff}")

g_gap.sort(key=lambda x: -x[1])
if g_gap:
    say("  top blanks by use:")
    for num, occ, lemma, reason, vis in g_gap[:25]:
        say(f"    {num:10} {occ:6}x  {lemma:20} {reason}{'   <-- visible' if vis else ''}")
    with open("gloss_gap_greek.tsv", "w", encoding="utf-8") as f:
        f.write("number\toccurrences\tlemma\treason\tvisible_now\n")
        for num, occ, lemma, reason, vis in g_gap:
            f.write(f"{num}\t{occ}\t{lemma}\t{reason}\t{'yes' if vis else 'no'}\n")
    say(f"  -> full list ({len(g_gap)}) written to gloss_gap_greek.tsv")

# ===========================================================================
# PART B — HEBREW lemma gloss (the gap to fill)
# ===========================================================================
say("")
say("=" * 70)
say("PART B — HEBREW lemma gloss  (heb.db gloss / BDB / nothing)")
say("=" * 70)

# the universe of Hebrew numbers the app can show a word card for: the Hebrew OT
# reader (heb.db) + KJV + BSB Hebrew words. Folded to base numbers for matching.
heb_universe = Counter()        # base H-number -> total occurrences across all texts
for tbl, col in (("kjv_strongs", "strongs_id"), ("bsb_strongs", "strongs_id")):
    if has_table(conn, tbl):
        for r in conn.execute(f"SELECT {col} s, COUNT(*) n FROM {tbl} "
                              f"WHERE {col} GLOB 'H*' GROUP BY {col}"):
            heb_universe[norm_h(r["s"])] += r["n"]

# what BDB covers (long description only — not a clean short gloss, but a fill source)
bdb_have = set()
if has_table(conn, "bdb"):
    for (sid,) in conn.execute("SELECT strongs_id FROM bdb WHERE description IS NOT NULL AND description<>''"):
        bdb_have.add(norm_h(sid))

# heb.db: real Hebrew OT glosses. most-common gloss per base number = a fine lemma gloss.
heb_gloss = {}          # base H-number -> best (most common) short gloss
heb_occ = Counter()
if HEB and os.path.exists(HEB):
    hc = sqlite3.connect(HEB)
    counts = defaultdict(Counter)
    for r in hc.execute("SELECT strongs, gloss FROM heb_words WHERE strongs IS NOT NULL AND strongs<>''"):
        base = norm_h(r["strongs"])
        if not base.startswith("H"):
            continue
        heb_occ[base] += 1
        heb_universe[base] += 1
        g = (r["gloss"] or "").strip()
        if g:
            counts[base][g] += 1
    for base, c in counts.items():
        heb_gloss[base] = c.most_common(1)[0][0]
    hc.close()
else:
    say("(no heb.db given — pass --heb ~/bible-db/heb.db for the Hebrew picture)")

h_total = len(heb_universe)
from_heb = sum(1 for n in heb_universe if n in heb_gloss)
only_bdb = sum(1 for n in heb_universe if n not in heb_gloss and n in bdb_have)
bare = sum(1 for n in heb_universe if n not in heb_gloss and n not in bdb_have)
say(f"distinct Hebrew numbers the app can show : {h_total}")
say(f"  short gloss available in heb.db        : {from_heb}  ({pct(from_heb, h_total)})")
say(f"  only a long BDB definition (no short)  : {only_bdb}")
say(f"  no gloss anywhere (must import)        : {bare}")

# the numbers heb.db can't gloss — the ones a source like OpenScriptures would need
need = [(n, heb_universe[n], (n in bdb_have)) for n in heb_universe if n not in heb_gloss]
need.sort(key=lambda x: -x[1])
if need:
    say("  top Hebrew numbers with no short gloss:")
    for num, occ, in_bdb in need[:25]:
        say(f"    {num:8} {occ:6}x   {'BDB long def only' if in_bdb else 'BARE - nothing'}")
    with open("gloss_gap_hebrew.tsv", "w", encoding="utf-8") as f:
        f.write("number\toccurrences\tbdb_has_long_def\n")
        for num, occ, in_bdb in need:
            f.write(f"{num}\t{occ}\t{'yes' if in_bdb else 'no'}\n")
    say(f"  -> full list ({len(need)}) written to gloss_gap_hebrew.tsv")

conn.close()
with open("gloss_coverage_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines) + "\n")
say("")
say("summary also saved to gloss_coverage_report.txt")
