#!/usr/bin/env python3
"""
rank_lexica_candidates.py — build the frequency-ranked candidate list for the Lexica
definition-engine rollout. READ-ONLY (opens bible.db mode=ro; touches nothing).

Counts each Greek base Strong's number the SAME way build_lexica_def feeds it — base
number, dotted variants excluded (abp_filter) — then:
  • folds the alias map (contested_register.LEXICA_ALIASES) so an aliased number counts
    under its canonical number, never separately;
  • drops anything in the CONTESTED register (primary numbers AND their aliases);
  • drops the structural-card closed-class lemmas (structural._STRUCTURAL keys);
  • flags likely names (is_pn majority) and known pronoun/interrogative numbers, which
    probably want a different card type than a verse-grounded definition — flagged, not
    dropped (JP's call).

Prints the top N (default 40) so the batch's top-20 can be read off with the flags visible.

  workon bible-env
  python scripts/rank_lexica_candidates.py            # top 40
  python scripts/rank_lexica_candidates.py --top 60
"""
import argparse, os, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from contested_register import CONTESTED_BY_SID, LEXICA_ALIASES
import structural

# Known function-ish Greek numbers NOT in structural.py (pronouns / interrogatives / relatives)
# — they carry no verse-grounded sense range; flag if they surface high. Not an exclusion.
PRONOUN_NUMS = {
    "G1473": "egō (I / we — personal pronoun)",
    "G4771": "sy (you — personal pronoun)",
    "G3739": "hos (who / which — relative pronoun)",
    "G5100": "tis (someone / anyone — indefinite)",
    "G5101": "tis (who? what? — interrogative)",
    "G1438": "heautou (himself — reflexive)",
    "G3778": "houtos (this — demonstrative)",   # also structural, belt-and-suspenders
    "G1565": "ekeinos (that — demonstrative)",
    "G4572": "seautou (yourself — reflexive)",
    "G1683": "emautou (myself — reflexive)",
    "G240": "allēlōn (one another — reciprocal)",
    "G3956": "pas (all / every — quantifier)",
    "G3745": "hosos (as much as — relative quantifier)",
    "G5127": "toutou (of this — houtos oblique)",
}


def table_exists(conn, name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (name,)).fetchone() is not None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"))
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--occ-min", type=int, default=2)
    args = ap.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    have_dotted = table_exists(conn, "dotted_lexicon")
    dotted_pred = (" AND 'G' || w.strongs NOT IN (SELECT strongs FROM dotted_lexicon)"
                   if have_dotted else "")

    # Per-base occurrence count, Greek only, engine's counting rule (dotted excluded).
    rows = conn.execute(f"""
        SELECT w.strongs_base AS base, COUNT(*) AS c,
               SUM(CASE WHEN w.is_pn = 1 THEN 1 ELSE 0 END) AS pn
        FROM words w
        WHERE w.strongs_base LIKE 'G%'{dotted_pred}
        GROUP BY w.strongs_base
    """).fetchall()

    # Fold aliases: an aliased (textbook) number's count moves onto its canonical (ABP) number.
    counts, pn = {}, {}
    for r in rows:
        base = LEXICA_ALIASES.get(r["base"], r["base"])
        counts[base] = counts.get(base, 0) + r["c"]
        pn[base] = pn.get(base, 0) + (r["pn"] or 0)

    structural_nums = set(structural._STRUCTURAL.keys())
    excluded = set(CONTESTED_BY_SID.keys()) | structural_nums

    have_wg = table_exists(conn, "word_gloss")

    def head(base):
        lx = conn.execute("SELECT lemma, translit FROM lexicon WHERE strongs_g=?", (base,)).fetchone()
        lemma = (lx["lemma"] if lx else "") or ""
        translit = (lx["translit"] if lx else "") or ""
        gloss = ""
        if have_wg:
            g = conn.execute("SELECT gloss FROM word_gloss WHERE strongs=?", (base,)).fetchone()
            gloss = (g["gloss"] if g else "") or ""
        return lemma, translit, gloss

    ranked = sorted(((b, c) for b, c in counts.items() if c >= args.occ_min),
                    key=lambda bc: -bc[1])

    print(f"# Lexica definition-engine — frequency-ranked candidates (occ >= {args.occ_min})")
    print(f"# aliases folded ({len(LEXICA_ALIASES)} pairs); excluded {len(set(CONTESTED_BY_SID))} "
          f"contested + {len(structural_nums)} structural = {len(excluded)} numbers")
    print(f"# flags: [NAME]=is_pn majority  [FUNC]=pronoun/quantifier not in structural.py\n")
    print(f"{'rank':>4}  {'strongs':<8} {'occ':>6}  {'lemma':<16} {'translit':<16} flag  gloss")

    shown = 0
    for base, c in ranked:
        if base in excluded:
            continue
        shown += 1
        if shown > args.top:
            break
        lemma, translit, gloss = head(base)
        flag = ""
        if pn.get(base, 0) * 2 >= c:
            flag = "NAME"
        elif base in PRONOUN_NUMS:
            flag = "FUNC"
        print(f"{shown:>4}  {base:<8} {c:>6}  {lemma:<16} {translit:<16} {flag:<5} {gloss[:48]}")

    conn.close()


if __name__ == "__main__":
    main()
