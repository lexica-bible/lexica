#!/usr/bin/env python3
"""
stress_rare_survey.py — STEP 1 of the rare-word stress test: survey the thin end of the Greek
corpus so we can pick the test set BEFORE building anything.

WHY (read once). Before building the verse-grounded dictionary (lexica_def) out top-down by
frequency, we need the frequency CUTOFF: the point below which the engine stops being honestly
short on a starved word and starts MANUFACTURING senses to fill the template. This script does
not answer that — it picks the words we will test. It lists rare Greek lemmas (1..N occurrences),
excluding proper nouns and anything already built into lexica_def, with the two signals that help
choose a good spread: the occurrence count (how starved) and the rendering count (how much a
translation already disambiguated it — a 2-occurrence word rendered two different ways is a
better split-temptation than one rendered identically).

It counts a word the SAME way the engine feeds it: by strongs_base, dotted variants excluded
(mirrors build_lexica_def.abp_filter exactly), over the verses-join so every counted occurrence
is one the engine could actually put in front of the model. So "occ" here == the number of
occurrences select_spread would sample for that word.

PA-ONLY (bible.db lives there). READ-ONLY: opens bible.db ?mode=ro — it cannot write anything.
No model, no API key needed.

  workon bible-env
  python scripts/stress_rare_survey.py                 # full survey: distribution + candidate buckets
  python scripts/stress_rare_survey.py --max-occ 8     # widen the tail shown
  python scripts/stress_rare_survey.py --per-bucket 60 # show more candidates per occurrence count
"""

import argparse, os, sqlite3, sys
from collections import defaultdict, Counter

# reuse the frozen helpers / constants (NT_BOOKS, table_exists) so nothing drifts from the engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_lexica_def as B


def strip_accents_lower(s):
    return B.strip_accents(s or "").lower()


def is_cap_lemma(lemma):
    """A proper-noun hint independent of is_pn: the accent-stripped lemma starts uppercase."""
    base = B.strip_accents(lemma or "")
    return bool(base) and base[0].isalpha() and base[0].isupper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"))
    ap.add_argument("--max-occ", type=int, default=6,
                    help="show candidate words with at most this many occurrences (default 6)")
    ap.add_argument("--per-bucket", type=int, default=45,
                    help="max candidate lines to print per occurrence-count bucket (default 45)")
    args = ap.parse_args()

    try:                                          # Greek/diacritics print on any console
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    has_dotted = B.table_exists(conn, "dotted_lexicon")
    has_lexica = B.table_exists(conn, "lexica_def")
    built = set()
    if has_lexica:
        built = {r["strongs"] for r in conn.execute("SELECT strongs FROM lexica_def")}

    nt = "(" + ",".join("'%s'" % b for b in sorted(B.NT_BOOKS)) + ")"
    dotted_excl = "AND 'G' || w.strongs NOT IN (SELECT strongs FROM dotted_lexicon)" if has_dotted else ""

    # ── pass 1: per Greek base — occurrence count, PN rows, OT/NT split, lemma/translit.
    # Counted over the verses-join (exactly what select_spread can feed), dotted variants excluded.
    agg = conn.execute(f"""
        SELECT w.strongs_base                                   AS base,
               COUNT(*)                                         AS occ,
               SUM(COALESCE(w.is_pn, 0))                        AS pn_rows,
               SUM(CASE WHEN v.book IN {nt} THEN 1 ELSE 0 END)  AS nt_occ,
               l.lemma                                          AS lemma,
               l.translit                                       AS translit
        FROM verses v
        JOIN words w        ON w.verse_id = v.id
        LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base
        WHERE w.strongs_base GLOB 'G[0-9]*'
          {dotted_excl}
        GROUP BY w.strongs_base
    """).fetchall()

    info = {}
    for r in agg:
        info[r["base"]] = {
            "occ": r["occ"], "pn_rows": r["pn_rows"] or 0, "nt_occ": r["nt_occ"] or 0,
            "lemma": r["lemma"] or "", "translit": r["translit"] or "",
        }

    # ── pass 2: renderings (single-word english_head, the engine's gloss_set shape) per base.
    rnd = conn.execute(f"""
        SELECT w.strongs_base AS base, w.english_head AS g, COUNT(*) AS c
        FROM verses v
        JOIN words w ON w.verse_id = v.id
        WHERE w.strongs_base GLOB 'G[0-9]*'
          {dotted_excl}
          AND w.english_head IS NOT NULL AND w.english_head != ''
        GROUP BY w.strongs_base, w.english_head
    """).fetchall()
    renders = defaultdict(list)
    for r in rnd:
        if " " in r["g"]:        # single-word renderings only — matches gloss_set()
            continue
        renders[r["base"]].append((r["g"], r["c"]))
    for b in renders:
        renders[b].sort(key=lambda gc: -gc[1])

    # ── classify. A CONTENT candidate = Greek base, not built, no PN rows, not a capitalized
    # (name-shaped) lemma. We keep the others only for the distribution counts / transparency.
    def is_content(base):
        d = info[base]
        return (base not in built) and d["pn_rows"] == 0 and not is_cap_lemma(d["lemma"])

    # distribution of CONTENT bases by occurrence count (the tail we'd build into)
    dist = Counter()
    dist_all = Counter()
    for base, d in info.items():
        dist_all[d["occ"]] += 1
        if is_content(base):
            dist[d["occ"]] += 1

    total_bases = len(info)
    total_content = sum(1 for b in info if is_content(b))

    print("=" * 96)
    print("RARE-WORD STRESS TEST — STEP 1 SURVEY (read-only)")
    print("=" * 96)
    print(f"Greek bases in corpus (dotted excluded):      {total_bases}")
    print(f"  already built into lexica_def:              {len(built & set(info))} "
          f"(of {len(built)} rows in lexica_def)")
    print(f"  content candidates (non-PN, not built):     {total_content}")
    print()
    print("DISTRIBUTION — how many CONTENT bases sit at each occurrence count (the build tail):")
    print(f"  {'occ':>4}  {'content':>8}  {'cum<=':>7}   {'all-bases':>9}")
    cum = 0
    upper = max(12, args.max_occ)
    for k in range(1, upper + 1):
        cum += dist.get(k, 0)
        print(f"  {k:>4}  {dist.get(k,0):>8}  {cum:>7}   {dist_all.get(k,0):>9}")
    tail = sum(v for k, v in dist.items() if k > upper)
    print(f"  >{upper:>3}  {tail:>8}  {total_content:>7}")
    print()
    print("Read: 'content' = the words a frequency cutoff would decide to build or leave on LSJ.")
    print("'cum<=' is how many words you'd ADD by setting the cutoff at that occurrence count.")
    print()

    # ── candidate buckets: occ = 1..max-occ, content only, sorted by rendering-count desc
    # (the split-temptation signal) then base. These are what we pick the ~15-20 test words from.
    by_occ = defaultdict(list)
    for base, d in info.items():
        if is_content(base) and 1 <= d["occ"] <= args.max_occ:
            by_occ[d["occ"]].append(base)

    print("=" * 96)
    print("CANDIDATES (content words; pick the test set from here)")
    print("  line = G####  occ=N rend=M  ot/nt  lemma (translit)  ::  top renderings(count)")
    print("  rend = # of distinct single-word renderings (a higher rend at low occ = more")
    print("         split-temptation; that's where manufacturing, if any, will show).")
    print("=" * 96)
    for k in range(1, args.max_occ + 1):
        bases = by_occ.get(k, [])
        if not bases:
            continue
        # sort: most renderings first (most interesting), then by base number
        bases.sort(key=lambda b: (-len(renders.get(b, [])), int(b[1:].split(".")[0])))
        print(f"\n--- occ = {k}   ({len(bases)} content candidates) ---")
        for base in bases[:args.per_bucket]:
            d = info[base]
            rs = renders.get(base, [])
            rend_n = len(rs)
            ot = d["occ"] - d["nt_occ"]
            top = ", ".join(f"{g}({c})" for g, c in rs[:6]) or "(no single-word rendering)"
            lem = d["lemma"] or "(no lexicon lemma)"
            tr = f" {d['translit']}" if d["translit"] else ""
            print(f"  {base:<9} occ={d['occ']} rend={rend_n}  {ot}/{d['nt_occ']}  "
                  f"{lem}{tr}  ::  {top}")
        if len(bases) > args.per_bucket:
            print(f"  … {len(bases) - args.per_bucket} more at occ={k} (raise --per-bucket to see all)")

    conn.close()
    print()
    print("Next: paste this output back. I'll pick ~15-20 words spread across occ 1/2/3/~5,")
    print("with a mix of high- and low-rendering words, and report the set for your confirmation")
    print("BEFORE any build runs.")


if __name__ == "__main__":
    main()
