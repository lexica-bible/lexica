"""Concordance verse lists vs our words-table verse lists (read-only, local).

Inputs (all local; nothing touches a database):
  abp_helps/concordance_entries.tsv + concordance_refs.tsv   (scripts/parse_abp_concordance.py)
  the PA export  strongs,book,chapter,verse,occurrences      (one row per number per verse,
                 words joined to verses, name rows excluded, exact stored dotted number)
  abp_texts/     only for the row-gap breakdown (export vs the pre-build source text)

Matching is on the FULL number exactly as printed/stored (dotted-number rule); an entry with a
bracketed second number ("39 (40)") or two numbers (Levi "3017,18") is compared against the
export rows of ALL its numbers together. '*' in the Concordance = 2+ occurrences in our verse.

Usage:  python scripts/diff_concordance_verses.py <export.csv> [--label NAME]
Out:    abp_helps/concordance_diff_<label>_numbers.tsv · _rows.tsv · _gap.tsv
"""
import argparse
import csv
import os
import re
import sys
from collections import Counter, defaultdict

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
H = os.path.join(REPO, "abp_helps")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_abp_concordance import CANON, RANK  # noqa: E402


def load_abp_texts():
    pairs = Counter()
    root = os.path.join(REPO, "abp_texts")
    for sub in ("abp_ot_texts", "abp_nt_texts"):
        for fn in os.listdir(os.path.join(root, sub)):
            for line in open(os.path.join(root, sub, fn), encoding="utf-8"):
                m = re.match(r"\((\w+) (\d+):(\d+)\)\s*(.*)", line)
                if m:
                    for n, c in Counter(re.findall(r"G(\d+(?:\.\d+)*)", m.group(4))).items():
                        pairs[(n, m.group(1), int(m.group(2)), int(m.group(3)))] = c
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export")
    ap.add_argument("--label", default="live")
    args = ap.parse_args()

    # ---- our side
    X = {}
    with open(args.export, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            X[(r["strongs"], r["book"], int(r["chapter"]), int(r["verse"]))] = int(r["occurrences"])
    print(f"export rows: {len(X)}")

    # ---- Concordance side
    ents = list(csv.DictReader(open(os.path.join(H, "concordance_entries.tsv"), encoding="utf-8"), delimiter="\t"))
    allkeys = {k for e in ents for k in (e["keys"].split() + e["alt_keys"].split())}
    listkeys = {k for e in ents if e["class"] == "has verses" for k in (e["keys"].split() + e["alt_keys"].split())}
    def where(n):
        return "list" if n in listkeys else ("nolist" if n in allkeys else "notin")
    C = defaultdict(dict)        # entry num -> {(book,ch,vs): star}
    foot = defaultdict(set)
    for r in csv.DictReader(open(os.path.join(H, "concordance_refs.tsv"), encoding="utf-8"), delimiter="\t"):
        v = (r["book"], int(r["chapter"]), int(r["verse"]))
        if r["src"] == "footnote":
            foot[r["num"]].add(v); continue
        C[r["num"]][v] = max(C[r["num"]].get(v, 0), int(r["star"]))

    # ---- 1. row gap: export vs abp_texts
    A = load_abp_texts()
    gap = defaultdict(Counter)
    for k in X.keys() - A.keys():
        gap[k[1]]["export_only_" + where(k[0])] += 1
    for k in A.keys() - X.keys():
        gap[k[1]]["abp_only_" + where(k[0])] += 1
    nb = Counter(k[1] for k in X); na = Counter(k[1] for k in A)
    with open(os.path.join(H, f"concordance_diff_{args.label}_gap.tsv"), "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        cols = ["export_only_list", "export_only_nolist", "export_only_notin",
                "abp_only_list", "abp_only_nolist", "abp_only_notin"]
        w.writerow(["book", "export_rows", "abp_texts_rows", "net"] + cols)
        tot = Counter()
        for b in CANON:
            row = [b, nb[b], na[b], nb[b] - na[b]] + [gap[b][c] for c in cols]
            w.writerow(row)
            for c, val in zip(["export_rows", "abp_texts_rows", "net"] + cols, row[1:]):
                tot[c] += val
        w.writerow(["TOTAL"] + [tot[c] for c in ["export_rows", "abp_texts_rows", "net"] + cols])
    print(f"gap: export {len(X)} - abp_texts {len(A)} = {len(X) - len(A)} · "
          + " · ".join(f"{c} {tot[c]}" for c in cols))
    top = sorted(CANON, key=lambda b: -abs(nb[b] - na[b]))[:15]
    print("   book   net | export-only: list/nolist/notin | abp-only: list/nolist/notin")
    for b in top:
        g = gap[b]
        print(f"   {b:4} {nb[b]-na[b]:+6} | {g['export_only_list']:5} {g['export_only_nolist']:6} {g['export_only_notin']:3} "
              f"| {g['abp_only_list']:5} {g['abp_only_nolist']:6} {g['abp_only_notin']:3}")
    # which numbers carry the no-list gap
    nl = Counter(k[0] for k in X.keys() - A.keys() if where(k[0]) == "nolist")
    nl2 = Counter(k[0] for k in A.keys() - X.keys() if where(k[0]) == "nolist")
    hw = {k: e["headword"] for e in ents for k in e["keys"].split()}
    print("   top no-list numbers, export-only:", [(n, hw.get(n), c) for n, c in nl.most_common(8)])
    print("   top no-list numbers, abp-only:   ", [(n, hw.get(n), c) for n, c in nl2.most_common(8)])

    # ---- 3. the diff
    Xn = defaultdict(dict)
    for (n, b, c, v), occ in X.items():
        Xn[n][(b, c, v)] = occ
    rows, per = [], []
    tot = Counter()
    used_keys = set()
    for e in ents:
        if e["class"] != "has verses":
            continue
        ks = e["keys"].split() + e["alt_keys"].split()
        used_keys.update(ks)
        ours = {}
        for k in ks:
            for v, occ in Xn.get(k, {}).items():
                ours[v] = ours.get(v, 0) + occ
        cv = C.get(e["num"], {})
        c_only = sorted(set(cv) - set(ours), key=lambda v: (RANK[v[0]], v[1], v[2]))
        x_only = sorted(set(ours) - set(cv), key=lambda v: (RANK[v[0]], v[1], v[2]))
        star_missing = sorted(v for v in set(cv) & set(ours) if cv[v] and ours[v] < 2)
        star_extra = sorted(v for v in set(cv) & set(ours) if not cv[v] and ours[v] >= 2)
        for kind, vs in (("concordance_only", c_only), ("export_only", x_only),
                         ("star_but_once", star_missing), ("twice_no_star", star_extra)):
            for v in vs:
                rows.append([e["num"], e["headword"], kind, v[0], v[1], v[2], cv.get(v, ""), ours.get(v, "")])
        per.append([e["num"], e["headword"], len(cv), len(ours), len(set(cv) & set(ours)), len(c_only),
                    len(x_only), len(star_missing), len(star_extra), len(foot.get(e["num"], ()))])
        tot.update(entries=1, conc_verses=len(cv), our_verses=len(ours), shared=len(set(cv) & set(ours)),
                   conc_only=len(c_only), export_only=len(x_only), star_but_once=len(star_missing),
                   twice_no_star=len(star_extra), footnote=len(foot.get(e["num"], ())),
                   clean=int(not (c_only or x_only or star_missing or star_extra)))
    with open(os.path.join(H, f"concordance_diff_{args.label}_rows.tsv"), "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["num", "headword", "kind", "book", "chapter", "verse", "conc_star", "our_occurrences"])
        w.writerows(rows)
    per.sort(key=lambda r: -(r[5] + r[6] + r[7] + r[8]))
    with open(os.path.join(H, f"concordance_diff_{args.label}_numbers.tsv"), "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["num", "headword", "conc_verses", "our_verses", "shared", "conc_only", "export_only",
                    "star_but_once", "twice_no_star", "footnote_refs"])
        w.writerows(per)
    print("diff totals:", dict(tot))
    nolist = Counter()
    for (n, b, c, v) in X:
        if n not in used_keys:
            nolist["number has a Concordance entry but no verse list" if n in allkeys else "number not in the Concordance"] += 1
    print("export rows outside the compared entries:", dict(nolist))
    print("top 20 entries by disagreement (num headword | conc ours shared | conc_only export_only star_but_once twice_no_star):")
    for r in per[:20]:
        print(f"   {r[0]:>9} {r[1]:<16} | {r[2]:5} {r[3]:5} {r[4]:5} | {r[5]:4} {r[6]:4} {r[7]:4} {r[8]:4}")

    # ---- 4. known star exception
    k = ("2588", "Ecc", 7, 22)
    print(f"Ecc 7:22 καρδία 2588: Concordance star = {C.get('2588', {}).get(k[1:], 'not listed')} · "
          f"our occurrences = {X.get(k, 'no row')}")


if __name__ == "__main__":
    main()
