#!/usr/bin/env python3
"""census_abp_surface_glued.py — READ-ONLY census B + D for the abp_surface fill
(docs/handoffs/CENSUS_abp_surface_fill.md). Opens no database. Run locally from the repo root:
  python scripts/census_abp_surface_glued.py .
Also the ONE copy of the fill's matching rules: scripts/dryrun_abp_surface_fill.py imports
load_lexicon / agree / resolve_level / plan_glued from here.

Inputs (PA exports, gitignored):
  abp_app_html/nbsp_surface_rows.tsv  every abp_surface form holding an NBSP + both neighbour slots
  abp_app_html/nbsp_544.tsv           audit dump rows, surface target, class mm_ours_nbsp
  abp_helps/analytical_lexicon.tsv, abp_helps/missing_forms_resolved.tsv
JP ruling 1: split ONLY where the glued tokens map onto EXISTING adjacent slots; no new word
rows; otherwise normalize NBSP -> plain space on the one slot. Ruling 2: match = number + form.
A token "agrees" with a slot only through the Lexicon on that slot's number (full dotted number;
pronoun family via ABP's 1473; other-dotted-suffix reported apart). Name slots ('*'/H) cannot be
Lexicon-proven: a token not in the Lexicon at all agrees with a name slot as 'name' (unproven).
Positions follow ABP's ENGLISH order, so a receiving slot may sit on either side of the glued
slot whatever the Greek order of its two words: all four pairings are tried.
"""
import csv, os, re, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_abp_app_vs_surface import fold as f0, NT
from audit_lexicon_vs_missing_forms import expand_nums, base
from build_abp_surface import _norm

NB = " "


def fold(s):
    return f0(s or "", mapped=True)


class Lexicon:
    """Folded index of abp_helps/analytical_lexicon.tsv (forms AND headwords per number)."""
    def __init__(self, path):
        self.forms = defaultdict(set)      # number -> folded forms + headwords (agree())
        self.anyform = set()
        self.bybase = defaultdict(set)
        # resolve_level() mirrors scripts/audit_lexicon_vs_missing_forms.py exactly:
        self.lv_forms = defaultdict(set)   # number -> folded forms only
        self.lv_heads = {}                 # number -> folded headwords
        self.lemma = {}                    # number -> lemma (" / " joined when printed twice)
        self.lv_byform = defaultdict(set)
        with open(path, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
                for n in expand_nums(r["ab_number"]):
                    self.bybase[base(n)].add(n)
                    if n in self.lemma and r["lemma"] not in self.lemma[n].split(" / "):
                        self.lemma[n] += " / " + r["lemma"]
                    else:
                        self.lemma.setdefault(n, r["lemma"])
                    self.lv_heads.setdefault(n, set()).add(fold(r["lemma"]))
                    for x in (r["form"], r["lemma"]):
                        if x:
                            self.forms[n].add(fold(x))
                            self.anyform.add(fold(x))
                    if r["form"]:
                        self.lv_forms[n].add(fold(r["form"]))
                        self.lv_byform[fold(r["form"])].add(n)


def load_lexicon(repo):
    return Lexicon(os.path.join(repo, "abp_helps", "analytical_lexicon.tsv"))


def clean(n):
    n = (n or "").strip()
    return n[1:] if n.startswith("G") else n


def is_name(n):
    return n == "*" or n.startswith("H")


def agree(lex, num, tok):
    """-> 'full' | 'pron' | 'dotted' | 'name' | None   (number + form, never form alone)"""
    n, t = clean(num), fold(tok)
    if not n:
        return None
    if is_name(n):
        return "name" if t not in lex.anyform else None
    if t in lex.forms.get(n, ()):
        return "full"
    if _norm(base(n)) == "1473" and t in lex.forms.get("1473", ()):
        return "pron"
    if any(t in lex.forms[m] for m in lex.bybase.get(base(n), ()) if m != n):
        return "dotted"
    return None


def resolve_level(lex, num, app_form):
    """A missing-form row's level, same rules + order as audit_lexicon_vs_missing_forms.py:
    A form listed · B form = headword · P pronoun via 1473 · C dotted neighbour ·
    D form only under another number · E clean word not listed · E2 note/glued · F no number."""
    num = clean(num)
    fa = fold(app_form)
    if num in lex.lv_forms and fa in lex.lv_forms[num]:
        return "A", lex.lemma[num]
    if num in lex.lv_heads and fa in lex.lv_heads[num]:
        return "B", lex.lemma[num]
    if num and _norm(base(num)) == "1473" and fa in lex.lv_forms.get("1473", ()):
        return "P", lex.lemma["1473"]
    neigh = [n for n in lex.bybase.get(base(num), ()) if n != num and fa in lex.lv_forms[n]]
    if num and neigh:
        return "C", lex.lemma[neigh[0]]
    if fa in lex.lv_byform:
        return "D", ""
    if num in lex.lemma:
        clean_word = re.fullmatch(r"[^\W\d_]+", app_form.strip()) is not None
        return ("E" if clean_word else "E2"), ""
    return "F", ""


def in_lex(lex, tok):
    return fold(tok) in lex.anyform


def plan_glued(lex, r):
    """One glued abp_surface row (form + both neighbours) -> the census decision.
    r keys: strongs, form, prev_strongs, prev_form, next_strongs, next_form, position."""
    toks = [t for t in r["form"].split(NB) if t]          # a doubled NBSP leaves an empty piece
    own = r["strongs"]
    plans = []
    if len(toks) == 2:
        for side, rn, rf in (("next", r["next_strongs"], r["next_form"]),
                             ("prev", r["prev_strongs"], r["prev_form"])):
            for o, x in ((toks[0], toks[1]), (toks[1], toks[0])):
                ao, ax = agree(lex, own, o), agree(lex, rn, x) if rn else None
                if ao and ax:
                    if not rf:
                        st = "receiver empty"
                    elif fold(rf) == fold(x):
                        st = "receiver already holds it"
                    else:
                        st = "receiver holds a different form"
                    same = (side == "next") == (x == toks[1])
                    plans.append((side, o, x, rn, rf, ao, ax, st,
                                  "same as Greek" if same else "crossed"))
    whole = agree(lex, own, r["form"]) in ("full", "pron")   # the glued value IS one entry
    if whole:
        part, why = "normalize-only", ("whole value is one Lexicon entry on its number"
                                       + (" (a split was also possible)" if plans else ""))
        plans = []
    elif len(toks) != 2:
        part, why = "normalize-only", (f"{len(toks)} tokens (only ±1 neighbours checked)"
                                       if len(toks) > 2 else "1 token")
    elif len(plans) == 1:
        part, why = "split-eligible", plans[0][7]
    elif len(plans) >= 2:
        part, why = "split-ambiguous", "more than one neighbour/token pairing agrees"
    else:
        part, why = "normalize-only", "no adjacent slot agrees with the extra token"
    p = plans[0] if len(plans) == 1 else None
    if part == "split-eligible" and p[7] == "receiver holds a different form":
        part = "split-conflict"
    pos = int(r["position"])
    return dict(toks=toks, part=part, why=why, plan=p,
                recv_pos=(None if not p else pos + (1 if p[0] == "next" else -1)))


def main():
    REPO = sys.argv[1]
    SURF = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "abp_app_html/nbsp_surface_rows.tsv")
    D544 = sys.argv[3] if len(sys.argv) > 3 else os.path.join(REPO, "abp_app_html/nbsp_544.tsv")
    OUT = sys.argv[4] if len(sys.argv) > 4 else os.path.join(REPO, "docs/handoffs/abp_surface_fill_census_glued.csv")
    lex = load_lexicon(REPO)

    rows = list(csv.DictReader(open(SURF, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
    d544 = {}
    for line in open(D544, encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) >= 12 and p[0] != "book":
            d544[(p[0], p[1], p[2], p[3])] = p
    missing = {}
    for r in csv.DictReader(open(os.path.join(REPO, "abp_helps/missing_forms_resolved.tsv"), encoding="utf-8"),
                            delimiter="\t", quoting=csv.QUOTE_NONE):
        missing[(r["book"], r["chapter"], r["verse"], r["position"])] = r

    keys = {(r["book"], r["chapter"], r["verse"], r["position"]) for r in rows}
    print(f"NBSP rows table-wide: {len(rows)} (distinct slots {len(keys)}) · 544 list: {len(d544)} · "
          f"544 not in table-wide list: {len(set(d544) - keys)}")

    res = []
    DBL = Counter()
    for r in rows:
        k = (r["book"], r["chapter"], r["verse"], r["position"])
        DBL[r["book"] in NT] += (NB + NB) in r["form"]
        g = plan_glued(lex, r)
        toks, part, why, p = g["toks"], g["part"], g["why"], g["plan"]
        own = r["strongs"]
        lexc = "all tokens in Lexicon" if all(in_lex(lex, t) for t in toks) else \
               ("name token(s), rest in Lexicon" if all(in_lex(lex, t) or agree(lex, own, t) == "name" or
                                                         (p and t == p[2] and p[6] == "name") for t in toks)
                else "≥1 token not in Lexicon")
        app = d544.get(k)
        app_own_ok = ""
        if app and p:
            app_own_ok = "yes" if fold(app[7]) == fold(p[1]) else "NO"
        recv_pos = "" if not p else str(g["recv_pos"])
        in_a = bool(p) and (k[0], k[1], k[2], recv_pos) in missing
        res.append(dict(book=k[0], chapter=k[1], verse=k[2], position=k[3], strongs=own,
                        english=r["english"], stored_form=r["form"].replace(NB, " + "),
                        in_544="yes" if app else "no", app_strongs=app[5] if app else "",
                        app_greek=app[7] if app else "", partition=part, detail=why, lexicon=lexc,
                        own_token=p[1] if p else "", own_agree=p[5] if p else "",
                        receiver_pos=recv_pos, receiver_strongs=p[3] if p else "",
                        receiver_form=p[4] if p else "", extra_token=p[2] if p else "",
                        receiver_agree=p[6] if p else "", receiver_in_A="yes" if in_a else "",
                        app_agrees_own_token=app_own_ok, slot_order=p[8] if p else "",
                        prev=f"{r['prev_strongs']} {r['prev_form']}".strip(),
                        next=f"{r['next_strongs']} {r['next_form']}".strip()))

    for scope, sel in (("544", lambda x: x["in_544"] == "yes"), ("other glued (not in 544)", lambda x: x["in_544"] == "no")):
        s = [x for x in res if sel(x)]
        print(f"\n== {scope}: {len(s)}")
        for k_, v in sorted(Counter(x["partition"] for x in s).items()):
            print(f"   {k_:18} {v}")
        print("   split-eligible detail:", dict(Counter(x["detail"] for x in s if x["partition"] == "split-eligible")))
        print("   receiver agreement:", dict(Counter(x["receiver_agree"] for x in s if x["partition"].startswith("split-") and x["receiver_agree"])))
        print("   normalize-only detail:", dict(Counter(x["detail"] for x in s if x["partition"] == "normalize-only")))
        print("   token/Lexicon:", dict(Counter((x["partition"], x["lexicon"]) for x in s)))
        print("   D (split receiver is an A row):", sum(1 for x in s if x["receiver_in_A"]))
        print("   app's Greek on our slot = the token we keep:", dict(Counter(x["app_agrees_own_token"] for x in s if x["own_token"])))
        print("   slot order vs Greek order (splits):", dict(Counter(x["slot_order"] for x in s if x["slot_order"])))
        print("   by testament:", dict(Counter(("NT" if x["book"] in NT else "OT", x["partition"]) for x in s)))

    print("\ndoubled NBSP (OT, NT):", DBL[False], DBL[True])
    for x in res:
        if x["partition"] == "split-ambiguous":
            print("   AMBIGUOUS:", x["book"], x["chapter"] + ":" + x["verse"], "pos", x["position"],
                  x["strongs"], x["stored_form"], "| prev", x["prev"], "| next", x["next"])
    c1 = [x for x in res if (x["book"], x["chapter"], x["verse"], x["position"]) == ("1Sa", "17", "57", "22")]
    print("\nC1 1Sa 17:57 pos 22:", c1[0] if c1 else "NOT FOUND")
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(res[0].keys()), lineterminator="\n")
        w.writeheader(); w.writerows(res)
    print("wrote", len(res), "->", OUT)


if __name__ == "__main__":
    main()
