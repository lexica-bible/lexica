"""Adjudicate the Concordance verse-list diff: buckets (b) and (d). Read-only, local.

Witnesses (nothing touches a database):
  * the ABP app slot file (abp_helps/abp_app_slots_full.tsv = PA's abp_app_html/abp_app_slots.tsv):
    ABP's own Greek + number per slot. Loaded, folded and Psalm-shifted with the SAME code the
    lane-(a) audit uses (scripts/audit_abp_app_vs_surface.py: load_app, fold(mapped=True),
    our Psalm verse v = app verse v+1 where our chapter has a title verse 0).
  * the Analytical Lexicon (abp_helps/analytical_lexicon.tsv): number -> lemma, gloss, FORMS.
  * our side: the PA words export + the Concordance parse (abp_helps/concordance_*.tsv).

(b) number-label pairs: a Concordance-only verse (Concordance number N) paired with the ONE number
    M of ours in that verse the Concordance does not account for there. Per verse: the app's Greek
    form at the slot carrying N or M -> is that form in the Lexicon's form list for N, for M?
    Pair ruling (Lexicon decides; the app's own number is reported beside it):
      concordance-right  every checked verse's form is in Lexicon[N] and not in Lexicon[M]
      ours-right         every checked verse's form is in Lexicon[M] and not in Lexicon[N]
      hold               anything else (both lists, neither, mixed, no app slot)
(d) residue rows, each classified by evidence (app = the ABP source witness):
      concordance print: verse offset   Conc-only verse; the same number sits unclaimed in ours one
                                        or two verses away (same chapter) — the book printed the
                                        wrong verse
      concordance print: not in source  Conc-only verse; neither the app nor ours has the number there
      concordance omission              ours-only verse; the app has the number there too
      concordance star error            *-once with the app also once / 2+ no-* with the app 2+
      number disagreement (missed by b) Conc-only/ours-only where the app has the number and ours
                                        carries a different number in that verse (or vice versa)
      split rendering (missed by a)     2+ no-*: ours AND abp_texts 2+, the app has ONE slot
      our side differs from the app     ours-only with the app lacking it / *-once with the app 2+
      versification                     rows in chapters whose verse numbering the app orders
                                        differently (Pro 16, Pro 24, Jer 10, Hab 3 — JP-ruled)
      unexplained                       none of the above, listed in full

Usage:  python scripts/adjudicate_concordance_diff.py
Out:    abp_helps/adj_b_pairs.tsv · adj_b_verses.tsv · adj_d_rows.tsv
"""
import csv
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, os.pardir)
H = os.path.join(REPO, "abp_helps")
sys.path.insert(0, HERE)
from audit_abp_app_vs_surface import load_app, fold, eng_words   # noqa: E402  the lane-(a) code
from build_abp_surface import _norm                         # noqa: E402  pronoun fold -> '1473'
from diff_concordance_verses import load_abp_texts          # noqa: E402
from parse_abp_concordance import RANK                      # noqa: E402

VERSIFICATION = {("Pro", 16), ("Pro", 24), ("Jer", 10), ("Hab", 3)}


def vkey(r):
    return (r["book"], int(r["chapter"]), int(r["verse"]))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    # ---- our side
    X = defaultdict(dict)
    byv = defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(H, "abp_words_by_verse_20261025.csv"), encoding="utf-8")):
        X[r["strongs"]][vkey(r)] = int(r["occurrences"])
        byv[vkey(r)][r["strongs"]] = int(r["occurrences"])
    ents = list(csv.DictReader(open(os.path.join(H, "concordance_entries.tsv"), encoding="utf-8"), delimiter="\t"))
    E = {e["num"]: e for e in ents}
    key2ent = {k: e for e in ents for k in e["keys"].split() + e["alt_keys"].split()}
    C = defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(H, "concordance_refs.tsv"), encoding="utf-8"), delimiter="\t"):
        if r["src"] != "footnote":
            C[r["num"]][vkey(r)] = max(C[r["num"]].get(vkey(r), 0), int(r["star"]))
    rows = list(csv.DictReader(open(os.path.join(H, "concordance_diff_live20261025_rows.tsv"), encoding="utf-8"),
                               delimiter="\t"))
    A_txt = load_abp_texts()
    TXT = {}
    for sub in ("abp_ot_texts", "abp_nt_texts"):
        root = os.path.join(REPO, "abp_texts", sub)
        for fn in os.listdir(root):
            for line in open(os.path.join(root, fn), encoding="utf-8"):
                m = re.match(r"\((\w+) (\d+):(\d+)\)\s*(.*)", line)
                if m:
                    TXT[(m.group(1), int(m.group(2)), int(m.group(3)))] = m.group(4)

    # ---- Lexicon
    LEX = defaultdict(lambda: {"lemma": "", "gloss": "", "forms": set(), "shown": []})
    for r in csv.DictReader(open(os.path.join(H, "analytical_lexicon.tsv"), encoding="utf-8"), delimiter="\t"):
        nums = [n.strip() for n in r["ab_number"].split(",")]
        if len(nums) == 2 and len(nums[1]) < len(nums[0]):            # "5484, 85"
            nums[1] = nums[0][: len(nums[0]) - len(nums[1])] + nums[1]
        for n in nums:
            d = LEX[n]
            d["lemma"], d["gloss"] = d["lemma"] or r["lemma"], d["gloss"] or r["gloss"]
            f = fold(r["form"])
            if f and f not in d["forms"]:
                d["forms"].add(f); d["shown"].append(r["form"])
            if fold(r["lemma"]):
                d["forms"].add(fold(r["lemma"]))

    # ---- app witness, keyed to OUR verse numbers (Psalm title shift, as the lane-(a) audit)
    app_raw, _eng = load_app(os.path.join(H, "abp_app_slots_full.tsv"))
    psa_shift = {(b, c) for (b, c, v) in byv if b == "Psa" and v == 0}
    APP = {}
    for (b, c, v), slots in app_raw.items():
        k = (b, c, v - 1) if (b, c) in psa_shift else (b, c, v)
        APP[k] = slots

    def app_slots(v, nums):
        want = {n for n in nums} | {_norm(n) for n in nums}
        return [s for s in APP.get(v, []) if s["s"] in want]

    def app_count(v, n):
        return len(app_slots(v, [n]))

    def app_words(v, nums):
        """App occurrences of the number(s), counting an app SPLIT RENDERING once: neighbouring
        slots with the same number and the same Greek but different English pieces are one word
        (the bucket-(a) shape, which the app has too). A true repeat ("holy, holy") keeps its count
        because its English pieces are the same."""
        sl = sorted(app_slots(v, nums), key=lambda s: s["td"])
        n, prev = 0, None
        for s in sl:
            if (prev is not None and s["td"] == prev["td"] + 1 and s["s"] == prev["s"]
                    and fold(s["g"] or "", mapped=True) == fold(prev["g"] or "", mapped=True)
                    and s["eng"] != prev["eng"]):
                prev = s; continue
            n += 1; prev = s
        return n

    STOP = {"the", "a", "an", "of", "and", "to", "in", "on", "for", "by", "with", "from", "his", "her",
            "their", "he", "she", "it", "they", "is", "was", "be", "shall", "will", "not", "as", "that",
            "this", "which", "who", "you", "your", "i", "me", "my", "we", "us", "our", "o"}

    def our_text_has(v, slots):
        """Does OUR source verse (abp_texts English) contain the app slot's content words?"""
        t = eng_words(re.sub(r"G\d+(?:\.\d+)*|G\*", " ", TXT.get(v, "")))
        want = [w for s in slots for w in eng_words(s["eng"]) if w not in STOP]
        return bool(want) and all(w in t for w in want)

    def app_nums(v):
        return {s["s"] for s in APP.get(v, [])}

    def ours_not_in_app(v, skip):
        """Our numbers in verse v the app does not carry there (pronouns folded to 1473)."""
        a = app_nums(v)
        return sorted(n for n in byv.get(v, {}) if n not in skip and n not in a and _norm(n) not in a)

    def app_not_in_ours(v, skip):
        ours = set(byv.get(v, {})) | {_norm(n) for n in byv.get(v, {})}
        return sorted(n for n in app_nums(v) if n and n != "*" and n not in skip and n not in ours)

    # ======================= (b) label pairs =======================
    co = [r for r in rows if r["kind"] == "concordance_only"]
    xo = [r for r in rows if r["kind"] == "export_only"]

    def unclaimed(v, N):
        out = []
        for M in byv.get(v, {}):
            e = key2ent.get(M)
            if e is None:
                out.append(M)
            elif e["class"] == "has verses" and e["num"] != N and v not in C[e["num"]]:
                out.append(M)
        return out

    pair_verses = defaultdict(list)
    co_used, xo_used = set(), set()
    amb = []
    for r in co:
        v = vkey(r)
        if v not in byv:
            continue
        u = unclaimed(v, r["num"])
        if len(u) == 1:
            pair_verses[(r["num"], u[0])].append(v)
            co_used.add((r["num"], v))
            M = u[0]
            Me = key2ent.get(M)
            if Me is not None:
                xo_used.add((Me["num"], v))
        elif len(u) > 1:
            amb.append((r["num"], v, u))

    vrows, prow = [], []
    verdicts = Counter()
    for (N, M), vs in sorted(pair_verses.items(), key=lambda x: (-len(x[1]), x[0])):
        ln, lm = LEX.get(N), LEX.get(M)
        checks = []
        for v in sorted(vs, key=lambda v: (RANK[v[0]], v[1], v[2])):
            sl = app_slots(v, [N, M])
            if not sl:
                checks.append((v, None, None, None, None)); continue
            s = sl[0]
            f = fold(s["g"], mapped=True) if s["g"] else None
            inN = bool(f and ln and f in ln["forms"])
            inM = bool(f and lm and f in lm["forms"])
            checks.append((v, s["s"], s["g"], inN, inM))
        if checks and all(c[1] is not None and c[3] and not c[4] for c in checks):
            verdict = "concordance-right"
        elif checks and all(c[1] is not None and c[4] and not c[3] for c in checks):
            verdict = "ours-right"
        else:
            verdict = "hold"
        app_side = Counter("N" if c[1] in (N, _norm(N)) else ("M" if c[1] in (M, _norm(M)) else "-")
                           for c in checks)
        settled = verdict != "hold"
        if len(vs) == 1 and not settled:
            verdict = "single-verse, unsettled"
        verdicts[(verdict, "repeating" if len(vs) >= 2 else "single")] += len(vs)
        prow.append([N, M, len(vs), verdict, f"app N {app_side['N']} / M {app_side['M']} / neither {app_side['-']}",
                     E[N]["headword"] if N in E else "", (ln or {}).get("lemma", "") if ln else "(no Lexicon entry)",
                     (ln or {}).get("gloss", "") if ln else "",
                     " ".join((ln or {}).get("shown", [])[:8]) if ln else "",
                     (lm or {}).get("lemma", "") if lm else "(no Lexicon entry)", (lm or {}).get("gloss", "") if lm else "",
                     " ".join((lm or {}).get("shown", [])[:8]) if lm else ""])
        for c in checks:
            vrows.append([N, M, f"{c[0][0]} {c[0][1]}:{c[0][2]}", c[1] or "", c[2] or "",
                          "" if c[3] is None else int(c[3]), "" if c[4] is None else int(c[4])])

    with open(os.path.join(H, "adj_b_pairs.tsv"), "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["conc_num", "our_num", "verses", "verdict", "app_number_at_slot", "conc_headword",
                    "lex_lemma_N", "lex_gloss_N", "lex_forms_N", "lex_lemma_M", "lex_gloss_M", "lex_forms_M"])
        w.writerows(prow)
    with open(os.path.join(H, "adj_b_verses.tsv"), "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["conc_num", "our_num", "verse", "app_number", "app_greek", "form_in_lex_N", "form_in_lex_M"])
        w.writerows(vrows)

    print(f"(b) pairs: {len(pair_verses)} covering {sum(len(v) for v in pair_verses.values())} Concordance-only "
          f"verses · ambiguous (2+ candidates) {len(amb)}")
    for (vd, kind), n in sorted(verdicts.items()):
        print(f"    {kind:9} {vd:24} {n} verses")
    print("  repeating pairs (2+ verses):")
    for p in prow:
        if p[2] >= 2:
            print(f"    {p[0]:>9} vs ours {p[1]:<9} {p[2]:>3}  {p[3]:<18} {p[4]}")
    print("  three sample verses per repeating pair:")
    by = defaultdict(list)
    for vr in vrows:
        by[(vr[0], vr[1])].append(vr)
    for p in prow:
        if p[2] >= 2:
            print(f"    {p[0]} [{p[6]} — {p[7][:40]}] vs {p[1]} [{p[9]} — {p[10][:40]}]")
            for vr in by[(p[0], p[1])][:3]:
                print(f"        {vr[2]:<12} app {vr[3] or '-':<9} {vr[4] or '-':<16} in Lex N {vr[5]} · in Lex M {vr[6]}")

    # ======================= (d) residue =======================
    a628 = {(r["book"], int(r["chapter"]), int(r["verse"]), r["strongs"])
            for r in csv.DictReader(open(os.path.join(H, "split_rendering_628.tsv"), encoding="utf-8"), delimiter="\t")}
    cls = []
    co_left = [r for r in co if (r["num"], vkey(r)) not in co_used and vkey(r) in byv]
    xo_left = [r for r in xo if (r["num"], vkey(r)) not in xo_used]
    xo_by_num = defaultdict(set)
    for r in xo_left:
        xo_by_num[r["num"]].add(vkey(r))
    offset_used = set()
    for r in co_left:
        v = vkey(r); N = r["num"]; ks = E[N]["keys"].split() + E[N]["alt_keys"].split()
        if (v[0], v[1]) in VERSIFICATION:
            cls.append((r, "versification")); continue
        near = sorted(w for w in xo_by_num[N] if w[0] == v[0] and w[1] == v[1] and 0 < abs(w[2] - v[2]) <= 2
                      and (N, w) not in offset_used)
        if near and sum(app_count(v, k) for k in ks) == 0:
            offset_used.add((N, near[0]))
            cls.append((r, "concordance print: verse offset")); continue
        ac = sum(app_count(v, k) for k in ks)
        if ac == 0:
            cls.append((r, "concordance print: not in source")); continue
        alt = ours_not_in_app(v, set(ks))
        if alt:
            cls.append((r, "number disagreement (missed by b)"))
        elif our_text_has(v, app_slots(v, ks)):
            cls.append((r, "our slot error (word in our text, number missing)"))
        else:
            cls.append((r, "verse-text difference (app has the word, our text does not)"))
        r["_alt"] = " ".join(alt)
    for r in xo_left:
        v = vkey(r); N = r["num"]; ks = E[N]["keys"].split() + E[N]["alt_keys"].split()
        if (N, v) in offset_used:
            cls.append((r, "concordance print: verse offset")); continue
        if (v[0], v[1]) in VERSIFICATION:
            cls.append((r, "versification")); continue
        ac = sum(app_count(v, k) for k in ks)
        if ac >= 1:
            cls.append((r, "concordance omission")); continue
        alt = app_not_in_ours(v, set(ks))
        cls.append((r, "number disagreement (missed by b)" if alt
                    else "verse-text difference (ours has the word, the app does not)"))
        r["_alt"] = " ".join(alt)
    for r in rows:
        v = vkey(r); N = r["num"]; ks = E[N]["keys"].split() + E[N]["alt_keys"].split()
        if r["kind"] == "star_but_once":
            nb = [w for w in X.get(N, {}) if w[0] == v[0] and w[1] == v[1] and abs(w[2] - v[2]) == 1
                  and w not in C[N]]
            if nb:
                cls.append((r, "concordance print: verse merge (2nd occurrence in our next/previous verse)"))
                r["_alt"] = " ".join(f"{w[0]} {w[1]}:{w[2]}" for w in nb)
                continue
            aw = app_words(v, ks)
            cls.append((r, "our slot error (app has it 2+)" if aw >= 2 else "concordance star error"))
        elif r["kind"] == "twice_no_star" and (v[0], v[1], v[2], ks[0]) not in a628:
            aw = app_words(v, ks)
            if aw >= 2:
                cls.append((r, "concordance star error"))
            elif aw == 1:
                cls.append((r, "split rendering (missed by a)"))
            else:
                cls.append((r, "unexplained"))
    tot = Counter((r["kind"], c) for r, c in cls)
    with open(os.path.join(H, "adj_d_rows.tsv"), "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["kind", "cause", "num", "headword", "book", "chapter", "verse", "conc_star", "our_occurrences",
                    "app_count", "app_greek", "other_number"])
        for r, c in cls:
            v = vkey(r); ks = E[r["num"]]["keys"].split() + E[r["num"]]["alt_keys"].split()
            sl = app_slots(v, ks)
            w.writerow([r["kind"], c, r["num"], r["headword"], *v, r["conc_star"], r["our_occurrences"],
                        len(sl), " ".join(s["g"] or "" for s in sl), r.get("_alt", "")])
    print(f"(d) residue rows classified: {len(cls)}  (Conc-only {len(co_left)} · ours-only {len(xo_left)} · "
          f"*-once {sum(1 for r in rows if r['kind'] == 'star_but_once')} · true 2+ no-* "
          f"{sum(1 for r, c in cls if r['kind'] == 'twice_no_star')})")
    for (k, c), n in sorted(tot.items()):
        print(f"    {k:17} {c:36} {n}")
    print("  unexplained rows:")
    for r, c in cls:
        if c == "unexplained":
            v = vkey(r)
            print(f"    {r['kind']:17} {r['num']:>9} {r['headword']:<14} {v[0]} {v[1]}:{v[2]}  conc* {r['conc_star']!s:2} "
                  f"ours {r['our_occurrences']!s:3} abp_texts {A_txt.get((r['num'], *v), 0)}")


if __name__ == "__main__":
    main()
