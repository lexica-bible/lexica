#!/usr/bin/env python3
"""audit_two_derivations.py — R-2 stage 1's ruled audit instrument + control panel.

Read-only. Two independent derivations of "how often does this name-entity occur in
ABP": the Hebrew-keyed count (words.strongs_base, the live stopgap) vs the Greek-keyed
count (pn_greek_identity.greek_strongs, the stage-1 addition). Their diff is the
truth-finder — every Hebrew number is listed with the Greek number(s) its words mapped
to and the two counts; disagreement rows are the review set, resolved against
TIPNR/ABP, never by preference.

Ends with a labeled CONTROL PANEL (reviewer condition): named pass/fail per control so
a pasted run shows the verdicts without grepping — number controls, binder-side
controls, and Greek-identity spots. Every detector here fires on a known positive
before any zero is trusted (the maacha/shetharboznai/jiphthahel rows were number-only
before this batch — they are the known positives).

Usage (PA):
  python3 scripts/audit_two_derivations.py ~/bible-db/bible_test.db > ~/r2s1_deriv_diff.txt
"""
import os
import sqlite3
import sys
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
import entity_resolution as er

DB = next((a for a in sys.argv[1:] if not a.startswith("--")),
          os.path.expanduser("~/bible-db/bible.db"))

conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

# Candidate-3 (reviewer ruling 2026-07-25, docs/PLAN_r2_c3_rebuild.md battery
# block): post-retirement the Hebrew-keyed derivation lives in pn_hebrew_xref,
# not words.strongs_base — reading the retired column would measure the
# retirement itself, not disagreement (the 2026-07-25 battery run proved it:
# 353 false DIFFs). xref rows with a Hebrew number correspond one-to-one to the
# pre-retirement Hebrew-keyed words, so the derivation is unchanged in meaning.
# Table absent -> today's read exactly (the wave's dormancy pattern).
HAS_XREF = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                        "AND name='pn_hebrew_xref'").fetchone() is not None

# ── Part 1: the two derivations, diffed ─────────────────────────────────────
if HAS_XREF:
    heb_counts = {r["hebrew_base"]: r["n"] for r in conn.execute(
        "SELECT hebrew_base, count(*) AS n FROM pn_hebrew_xref "
        "WHERE hebrew_base IS NOT NULL GROUP BY hebrew_base")}
else:
    heb_counts = {r["strongs_base"]: r["n"] for r in conn.execute(
        "SELECT strongs_base, count(*) AS n FROM words "
        "WHERE is_pn=1 AND strongs_base LIKE 'H%' GROUP BY strongs_base")}

pair_counts = defaultdict(int)   # (hebrew_base, greek_strongs) -> words
greek_counts = defaultdict(int)  # greek_strongs -> words
for r in conn.execute(
        "SELECT hebrew_base, greek_strongs, count(*) AS n FROM pn_greek_identity "
        "GROUP BY hebrew_base, greek_strongs"):
    pair_counts[(r["hebrew_base"], r["greek_strongs"])] = r["n"]
    if r["greek_strongs"]:
        greek_counts[r["greek_strongs"]] += r["n"]

print(f"two-derivations audit — {DB}")
print(f"Hebrew-keyed PN numbers: {len(heb_counts):,}   "
      f"Greek-keyed numbers: {len(greek_counts):,}\n")

agree = disagree = 0
print("hebrew_base | words(Hebrew-keyed) | greek mapping(s) [words] | verdict")
lines = []
for hb in sorted(heb_counts, key=lambda s: int(s[1:])):
    hn = heb_counts[hb]
    gmaps = {g: n for (h, g), n in pair_counts.items() if h == hb}
    mapped = sum(gmaps.values())
    ok = (mapped == hn)
    agree += ok
    disagree += (not ok)
    gtxt = ", ".join(f"{g or 'NO-NUMBER'}[{n}]" for g, n in sorted(
        gmaps.items(), key=lambda kv: -kv[1])) or "UNMAPPED"
    verdict = "agree" if ok else f"DIFF ({hn} vs {mapped})"
    line = f"{hb} | {hn} | {gtxt} | {verdict}"
    lines.append(line)
    if not ok:
        print(line)                      # disagreements up top, the review set
print(f"\nagree: {agree:,}   disagree: {disagree:,}")
print("\n---- full listing ----")
for line in lines:
    print(line)

# ── Part 2: CONTROL PANEL (labeled; reviewer condition) ─────────────────────
results = []


def control(label, ok, detail):
    results.append((label, bool(ok), detail))


def word_base(book, ch, vs, like):
    """(words value, xref hebrew_base or None, label) for one control word."""
    xsel = ", x.hebrew_base AS xh" if HAS_XREF else ", NULL AS xh"
    xjoin = ("LEFT JOIN pn_hebrew_xref x ON x.verse_id = w.verse_id "
             "AND x.position = w.position" if HAS_XREF else "")
    row = conn.execute(f"""
        SELECT w.strongs_base AS b,
               COALESCE(NULLIF(w.english_head,''), w.english) AS label{xsel}
        FROM words w JOIN verses v ON v.id = w.verse_id
        {xjoin}
        WHERE v.book=? AND v.chapter=? AND v.verse=? AND w.is_pn=1
          AND lower(COALESCE(NULLIF(w.english_head,''), w.english)) LIKE ?
    """, (book, ch, vs, like)).fetchone()
    return (row["b"], row["xh"], row["label"]) if row else (None, None, None)


# Number controls — the three known positives + the must-not + the no-change.
# Post-retirement (HAS_XREF) each asserts the ruled DUAL-HOME state: the Hebrew
# number intact in the xref, the words cell at its class's declared value.
# CLASSES RE-PINNED 2026-08-01 per the 7/30 reclassification (declaration:
# docs/tickets/RECLASS_catchup_declaration.md; verified per-row on the 8/1
# rebuild copy): maacha lemma-only→surface (post '*', unchanged value),
# shetharboznai none→surface (post H8370→'*'), jiphthahel none→lemma-only
# (post H3317→'*'); abia stays tipnr (G7). A future class churn updates these
# DELIBERATELY, with the new declaration cited — never by loosening the check.
# Pre-retirement: today's single-home assertion exactly.
for label, bk, ch, vs, like, want, post in [
    ("N1 maacha @ 2Ch 11:21 -> H4601",        "2Ch", 11, 21, "maacha%", "H4601", "*"),
    ("N2 shetharboznai @ Ezr 5:3 -> H8370",   "Ezr",  5,  3, "shethar%", "H8370", "*"),
    ("N3 jiphthahel @ Jos 19:14 -> H3317",    "Jos", 19, 14, "jiphthah%", "H3317", "*"),
    ("N5 NO-CHANGE abia @ 1Ch 3:10 -> H29",   "1Ch",  3, 10, "abia%", "H29", "G7"),
]:
    b, xh, lab = word_base(bk, ch, vs, like)
    if HAS_XREF:
        ok = (b == post and xh == want)
        detail = f"found {lab!r} words={b} xref={xh}" if lab else "WORD NOT FOUND at verse"
    else:
        ok = (b == want)
        detail = f"found {lab!r} base={b}" if lab else "WORD NOT FOUND at verse"
    control(label, ok, detail)

bad = conn.execute("""
    SELECT count(*) FROM words
    WHERE is_pn=1 AND strongs_base='H758'
      AND lower(COALESCE(NULLIF(english_head,''), english)) LIKE 'syrian%'
""").fetchone()[0]
control("N4 NEGATIVE: no 'syrian' word carries the place number H758", bad == 0,
        f"{bad} offending row(s)")

# Binder-side controls (reviewer condition 4): a pair that MUST now produce a card,
# and 'syrian' as the must-not.
have_binding = conn.execute(
    "SELECT count(*) FROM sqlite_master WHERE name='pn_binding'").fetchone()[0]
if have_binding:
    bk = er.book_num("2Ch")
    hit = conn.execute(
        "SELECT entity_uniq FROM pn_binding WHERE book=? AND chapter=11 AND verse=21 "
        "AND name LIKE 'maacha%' AND render=1", (bk,)).fetchone()
    control("B1 BIND-POSITIVE: maacha @ 2Ch 11:21 has a rendered bind",
            hit is not None, f"entity={hit['entity_uniq']}" if hit else "no rendered bind row")
    n = conn.execute("SELECT count(*) FROM pn_binding "
                     "WHERE name LIKE 'syrian%' AND render=1").fetchone()[0]
    control("B2 BIND-NEGATIVE: 'syrian' has NO rendered bind", n == 0,
            f"{n} rendered row(s)")
else:
    control("B1/B2 binder controls", False, "pn_binding table ABSENT — run build_entity_binding first")

# Greek-identity spots.
row = conn.execute("""
    SELECT g.greek_strongs AS gs, g.source AS src
    FROM pn_greek_identity g
    JOIN words w ON w.verse_id=g.verse_id AND w.position=g.position
    JOIN verses v ON v.id=w.verse_id
    WHERE v.book='Mat' AND v.chapter=1 AND v.verse=6
      AND lower(COALESCE(NULLIF(w.english_head,''), w.english)) LIKE 'david%'
""").fetchone()
control("G1 David @ Mat 1:6 carries a real Greek identity",
        row is not None and row["gs"] == "G1138",
        f"greek={row['gs']} source={row['src']}" if row else "no identity row")

n_lemma = conn.execute("SELECT count(*) FROM pn_greek_identity "
                       "WHERE source='lemma-only'").fetchone()[0]
control("G2 LXX-only pile carries the honest lemma-only state (count > 0)",
        n_lemma > 0, f"{n_lemma:,} lemma-only rows")
n_none = conn.execute("SELECT count(*) FROM pn_greek_identity "
                      "WHERE source='none'").fetchone()[0]
control("G3 'none' bucket is COUNTED, not hidden", True, f"{n_none:,} rows with no number and no lemma")

print("\n==================== CONTROL PANEL ====================")
fails = 0
for label, ok, detail in results:
    mark = "PASS" if ok else "FAIL"
    fails += (not ok)
    print(f"[{mark}] {label} — {detail}")
print("========================================================")
print(f"controls: {len(results)}  failed: {fails}")
if fails:
    sys.exit(1)
