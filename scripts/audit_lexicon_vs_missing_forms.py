#!/usr/bin/env python3
"""
audit_lexicon_vs_missing_forms.py — READ-ONLY join of the parsed ABP Analytical
Lexicon (scripts/parse_abp_analytical_lexicon.py -> abp_helps/analytical_lexicon.tsv)
against the audit's missing-printed-form list (scripts/audit_abp_app_vs_surface.py
-> abp_app_html/missing_printed_forms.tsv, written on PA). Opens no database.

QUESTION: of the slots where abp_surface has no printed form and the app prints one
(είπε where we show ἔπω), how many does the Analytical Lexicon resolve to a lemma?

MATCHING (all compares FOLDED — the lexicon's text layer has no accents/breathings;
the app's Greek first goes through the audit's DEFECT_MAP, the one copy):
  A  same number, form listed            -> RESOLVED
  B  same number, form = the headword    -> RESOLVED (headword), counted apart
  C  same base, other dotted suffix (our 2036 vs lexicon 2036.1), form listed there
     -> dotted neighbour (dotted-number rule: never merged into A)
  D  form listed only under another number -> "form found, other number" (pairs shown)
  E  number in the lexicon, form not listed
  F  number not in the lexicon (incl. our '*' / H-number name slots)
Lexicon numbers like "5484, 85" mean 5484 AND 5485.

Writes every row with its level to abp_helps/missing_forms_resolved.tsv.
Run locally:
  python scripts/audit_lexicon_vs_missing_forms.py \
      abp_helps/analytical_lexicon.tsv abp_app_html/missing_printed_forms.tsv
"""
import argparse
import csv
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_abp_app_vs_surface import DEFECT_MAP, fold as app_fold   # the one defect map + fold

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)


def fold(s):
    return app_fold(s, mapped=True)


def expand_nums(num):
    """'5484, 85' -> ['5484', '5485']; '70.4' -> ['70.4']."""
    parts = [p.strip() for p in num.split(",") if p.strip()]
    out = []
    for p in parts:
        if out and "." not in p and len(p) < len(out[0].split(".")[0]):
            first = out[0].split(".")[0]
            p = first[: len(first) - len(p)] + p
        out.append(p)
    return out


def base(n):
    return n.split(".")[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lexicon")
    ap.add_argument("missing")
    ap.add_argument("--out", default=os.path.join(REPO, "abp_helps", "missing_forms_resolved.tsv"))
    args = ap.parse_args()

    forms_by_num = defaultdict(set)
    head_by_num = {}
    lemma_by_num = {}
    nums_by_form = defaultdict(set)
    nums_by_base = defaultdict(set)
    dup_nums = set()
    with open(args.lexicon, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            for n in expand_nums(r["ab_number"]):
                # a number the book prints on two entries (2004 ζέω + ἐπιτάσσω) keeps both
                if n in lemma_by_num and r["lemma"] not in lemma_by_num[n].split(" / "):
                    lemma_by_num[n] += " / " + r["lemma"]
                    dup_nums.add(n)
                else:
                    lemma_by_num.setdefault(n, r["lemma"])
                head_by_num.setdefault(n, set()).add(fold(r["lemma"]))
                nums_by_base[base(n)].add(n)
                if r["form"]:
                    fo = fold(r["form"])
                    forms_by_num[n].add(fo)
                    nums_by_form[fo].add(n)

    with open(args.missing, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))

    lvl = Counter()
    by_type = defaultdict(Counter)
    ex = defaultdict(Counter)
    out = []
    for r in rows:
        num = (r["strongs"] or "").strip()
        num = num[1:] if num.startswith("G") else num
        fa = fold(r["app_printed_form"])
        lemma = ""
        if num in forms_by_num and fa in forms_by_num[num]:
            L, lemma = "A", lemma_by_num[num]
        elif num in head_by_num and fa in head_by_num[num]:
            L, lemma = "B", lemma_by_num[num]
        else:
            neigh = [n for n in nums_by_base.get(base(num), ()) if n != num and fa in forms_by_num[n]]
            if num and neigh:
                L, lemma = "C", f"{lemma_by_num[neigh[0]]} ({','.join(sorted(neigh))})"
            elif fa in nums_by_form:
                L = "D"
                lemma = "; ".join(f"{n} {lemma_by_num[n]}" for n in sorted(nums_by_form[fa])[:3])
            elif num in lemma_by_num:
                L = "E"
            else:
                L = "F"
        lvl[L] += 1
        by_type[r["word_type"]][L] += 1
        ex[L][(r["app_printed_form"], r["dictionary_word"], num, lemma)] += 1
        out.append({**r, "level": L, "lexicon_lemma": lemma})

    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        cols = list(rows[0].keys()) + ["level", "lexicon_lemma"] if rows else []
        f.write("\t".join(cols) + "\n")
        for r in out:
            f.write("\t".join(str(r[c]).replace("\t", " ") for c in cols) + "\n")

    n = len(rows)
    label = {"A": "RESOLVED: same number, form listed",
             "B": "RESOLVED: same number, form = headword",
             "C": "dotted neighbour: same base, other suffix, form listed there",
             "D": "form found, but only under another number",
             "E": "number in lexicon, form not listed",
             "F": "number not in lexicon (incl. '*' / H-number name slots)"}
    print(f"lexicon: {len(lemma_by_num)} numbers · {sum(len(v) for v in forms_by_num.values())} distinct folded forms")
    print(f"numbers printed on two entries in the book (kept as printed): "
          + "  ".join(f"{d} {lemma_by_num[d]}" for d in sorted(dup_nums)))
    print(f"missing printed forms: {n}")
    res = lvl["A"] + lvl["B"]
    print(f"RESOLVE RATE (A+B): {res}/{n} = {100.0 * res / n:.2f}%" if n else "no rows")
    for L in "ABCDEF":
        print(f"   {L} {label[L]:62} {lvl[L]:6}  ({100.0 * lvl[L] / n:.2f}%)" if n else "")
    print("\n   by word type        total   A+B    rate     C     D     E     F")
    for t, c in sorted(by_type.items(), key=lambda kv: -sum(kv[1].values())):
        tot = sum(c.values())
        ab = c["A"] + c["B"]
        print(f"   {t:18} {tot:6} {ab:6} {100.0 * ab / tot:6.1f}% {c['C']:5} {c['D']:5} {c['E']:5} {c['F']:5}")
    for L in "CDEF":
        if not ex[L]:
            continue
        print(f"\n   top {L} ({label[L]}):")
        for (af, dw, num, lem), k in ex[L].most_common(12):
            print(f"     {k:5}  app {af!r:18} ours {num:>8} {dw!r:16} {('-> ' + lem) if lem else ''}")
    print(f"\nwrote {len(out)} rows -> {args.out}")


if __name__ == "__main__":
    main()
