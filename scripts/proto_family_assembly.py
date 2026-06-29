#!/usr/bin/env python3
"""
proto_family_assembly.py — READ-ONLY proving artifact: auto-assemble a query's lexeme family
with a VISIBLE BOUNDARY (the forward step after the panel floor-checks, chat design 2026-06-29).

THE PROBLEM IT SOLVES
  Hand-seeding the fire/sabbath families proved the panel, but doesn't scale — and the real
  honesty seam in retrieval is "who decided pyroo counts as fire?". Auto-assembly carries the
  SAME imported-structure risk one level up: whatever picks the family is making an in/out call.
  Two false friends already showed the danger, both root-matched but meaning-mismatched:
     'isheh   (H801, "food offering")  rode in on esh (H784, "fire")
     mishbath (H4868, "cessation")     rode in on shabbat (H7676)
  Only the human eye caught them. Auto-assembly will hit this constantly.

THE RULE (STEM proposes, GLOSS disposes — the DISAGREEMENT between them surfaces a false friend)
  Membership is ROOT-ANCHORED. Candidates are proposed by ONE signal only:
     STEM   — shares the head's stem (Greek translit prefix) or root (Hebrew lemma consonants)
  then the second signal CONFIRMS or DENIES each one — it never discovers on its own:
     GLOSS  — its dictionary gloss shares a meaning-word with the head's gloss (literal word
              overlap, NOT semantic — "cessation" never equals "cease", so no thesaurus leak)
  Tiers:
     CORE       — the query's own head word(s).
     INCLUDE    — stem-proposed AND gloss confirms.
     BORDERLINE — stem-proposed but gloss does NOT confirm → SURFACED for review (never silent).
  'isheh / mishbath / pyretos("fever") share the stem but not the meaning → BORDERLINE: the
  visible boundary, computed. A real member glossed differently from its root lands here too —
  visible, not lost. A pure synonym of a DIFFERENT root (phil- "love" under agape-) is absent
  ENTIRELY — not even borderline — because nothing root-anchors it; gloss alone never adds it.
  The engine does NOT auto-decide the borderline pile; it surfaces it with evidence for a human.

WHY THIS IS HONEST, NOT CLEAN
  The deliverable is deliberately NOT a tidy auto-list. It is a family WITH its inclusion rule
  stated and the marginal words shown with the evidence (which signals fired, the matched word,
  occurrence count). Same discipline as the panel: show the boundary, don't hide it. Hebrew is
  weaker than Greek (no root field): we APPROXIMATE the root by stripping a trailing affix and match
  by containment; a SHORT root (≤2 consonants, e.g. esh אש) is too ambiguous to propose on its own,
  so it gloss-anchors instead of dumping an unreviewable pile. This is stated in the output, never
  papered over as "Hebrew just runs fatter". The robust long-term Hebrew bridge is full triliteral
  derivation and/or the LXX seam (separate views) — both later refinements.

RUN IT (on PythonAnywhere — bible.db + heb.db are PA-only):
    workon bible-env
    python scripts/proto_family_assembly.py --query fire
    python scripts/proto_family_assembly.py --query sabbath
    python scripts/proto_family_assembly.py --head G26,H160      # love (a fresh, un-seeded query)

Read-only: opens both DBs read-only and only SELECTs. The heads are what ai.py's term-extraction
already returns (key_strongs) — assembly's job is the within-language expansion + the boundary.
"""
import argparse
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core

# Heads the model's term-extraction would supply (so we can run without a live model call).
PROFILE_HEADS = {
    "fire":    ["G4442", "H784"],
    "sabbath": ["G4521", "H7676"],
}

_STOP = {"a", "an", "the", "of", "to", "by", "am", "is", "be", "or", "and", "in", "on",
         "for", "with", "from", "as", "at", "it", "that", "this", "one", "esp", "fig",
         "lit", "etc", "all", "any", "his", "her", "its"}


def _ascii(s):
    """Lowercase, accents stripped, non-letters dropped: 'pŷr'->'pyr', 'sabbatismós'->'sabbatismos'."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", s.lower())


_HEB_FINALS = {"ך": "כ", "ם": "מ", "ן": "נ",
               "ף": "פ", "ץ": "צ"}  # final kaf/mem/nun/pe/tsadi -> medial


def _heb_root(s):
    """Consonant skeleton of a Hebrew lemma: drop niqqud/cantillation, keep only Hebrew
    letters, fold final forms to medial. 'אֵשׁ'->'אש', 'מִשְׁבָּת'->'משבת'. Robust without the
    lemma_plain column (which this bdb build lacks — the consonants are what root-match needs)."""
    if not s:
        return ""
    out = []
    for ch in unicodedata.normalize("NFKD", s):
        if unicodedata.combining(ch):
            continue
        if "א" <= ch <= "ת":
            out.append(_HEB_FINALS.get(ch, ch))
    return "".join(out)


def _heb_rootify(cons):
    """Approximate the triliteral root from a lemma's consonant skeleton by stripping ONE common
    trailing affix (feminine -ה, plural -ות/-ים): 'אהבה'->'אהב' so the verb 'אהב' matches its noun.
    NOT a full morphological analyzer — Hebrew morphology is nasty (weak/hollow/geminate roots,
    preformatives). Matching uses CONTAINMENT, which already absorbs a leading preformative
    (mishbath משבת ⊃ שבת) without a risky leading strip, so only the trailing affix is handled here."""
    if len(cons) >= 4 and cons.endswith(("ות", "ים")):
        return cons[:-2]
    if len(cons) >= 4 and cons.endswith("ה"):
        return cons[:-1]
    return cons


def _norm_word(w):
    """Lowercase + a light plural fold so 'trials' matches 'trial'. NOT a stemmer: it does NOT
    bridge spelling variants like fire/fiery (the letters swap, fir-e vs fie-ry) — those are a
    semantic call the eye makes in the borderline tier, never auto-merged here."""
    w = w.lower()
    if len(w) > 3 and w.endswith("s"):
        w = w[:-1]
    return w


def _gloss_terms(gloss):
    """The head gloss's meaning-words, whole-word + plural-folded: 'fire, trials' -> {'fire','trial'}.
    Whole-word, NOT a 3-char stem — the old stem matched 'tri'->tribe/trio and split fire/fiery by luck."""
    out = set()
    for w in re.findall(r"[A-Za-z]+", gloss or ""):
        if len(w) >= 3 and w.lower() not in _STOP:
            out.add(_norm_word(w))
    return out


def _gloss_hits(gloss, terms):
    """The actual gloss words that match a head term (for showing the evidence)."""
    hits = []
    for w in re.findall(r"[A-Za-z]+", gloss or ""):
        if len(w) >= 3 and _norm_word(w) in terms:
            hits.append(w.lower())
    return sorted(set(hits))


# ── lexicon / gloss lookups ─────────────────────────────────────────────────
def _has_table(conn, name):
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())


def _wg(conn, prefixed):
    if not _has_table(conn, "word_gloss"):
        return ""
    r = conn.execute("SELECT gloss FROM word_gloss WHERE strongs=?", (prefixed,)).fetchone()
    return (r["gloss"] or "").strip() if r else ""


def _greek_head(conn, num):
    r = conn.execute(
        "SELECT lemma, translit, strongs_def, kjv_def FROM lexicon WHERE strongs_g=? OR strongs=?",
        (f"G{num}", num)).fetchone()
    lemma = (r["lemma"] if r else "") or ""
    translit = (r["translit"] if r else "") or ""
    gloss = _wg(conn, f"G{num}") or (r["kjv_def"] if r else "") or (r["strongs_def"] if r else "") or ""
    return lemma, translit, gloss


def _heb_head(conn, num):
    r = conn.execute(
        "SELECT lemma, xlit, description FROM bdb WHERE strongs_id=?",
        (f"H{num}",)).fetchone()
    lemma = (r["lemma"] if r else "") or ""
    xlit = (r["xlit"] if r else "") or ""
    plain = _heb_root(lemma)
    gloss = _wg(conn, f"H{num}") or (r["description"] if r else "") or ""
    return lemma, xlit, plain, gloss


def _greek_occ(conn, num):
    return conn.execute("SELECT count(*) c FROM words WHERE strongs_base=?", (f"G{num}",)).fetchone()["c"]


def _heb_occ(hconn, num):
    if hconn is None:
        return 0
    try:
        return hconn.execute(
            "SELECT count(*) c FROM heb_words WHERE strongs=? OR strongs GLOB ?",
            (f"H{num}", f"H{num}[A-Za-z]")).fetchone()["c"]
    except Exception:
        return 0


# ── discovery ───────────────────────────────────────────────────────────────
def assemble_greek(conn, num, stem, terms):
    """Candidates near a Greek head: translit-prefix (STEM) ∪ gloss-term (GLOSS). Each scored on both."""
    cand = {}   # base -> {translit}.  STEM-proposed ONLY — gloss confirms below, never discovers.
    for r in conn.execute("SELECT strongs_g, strongs, translit FROM lexicon"):
        t = _ascii(r["translit"])
        if t and stem and t.startswith(stem):
            base = (r["strongs_g"] or ("G" + (r["strongs"] or ""))).lstrip("G")
            cand.setdefault(base, {})["translit"] = r["translit"] or ""
    rows = []
    for base, d in cand.items():
        if base == num:
            continue
        gloss = _wg(conn, f"G{base}")
        ghit = _gloss_hits(gloss, terms)
        rows.append({
            "lang": "G", "num": base, "translit": d.get("translit") or "",
            "gloss": gloss, "occ": _greek_occ(conn, base),
            "stem_ok": True, "gloss_ok": bool(ghit), "ghit": ghit,
        })
    return rows


def assemble_hebrew(conn, hconn, num, root, terms):
    """Candidates near a Hebrew head, root-anchored. The head root is the affix-stripped consonant
    skeleton; a candidate is proposed when that root is CONTAINED in its skeleton (containment, not
    prefix — containment absorbs a leading preformative, so mishbath משבת ⊃ שבת is caught). A SHORT
    root (≤2 consonants, e.g. esh אש) is contained in a huge slice of a consonantal lexicon ("which",
    "Assyria", "woman"...), so it is too weak to propose on its own — there we additionally REQUIRE
    the gloss to confirm (gloss-anchored), stated in the output. Gloss confirms; it never discovers."""
    short = len(root) < 3
    cand = {}
    for r in conn.execute("SELECT strongs_id, xlit, lemma FROM bdb"):
        sk = _heb_root(r["lemma"])
        if not sk or not root:
            continue
        if root in sk:
            base = (r["strongs_id"] or "").lstrip("H")
            if base:
                cand.setdefault(base, {})["xlit"] = r["xlit"] or ""
    rows = []
    for base, d in cand.items():
        if base == num:
            continue
        gloss = _wg(conn, f"H{base}")
        ghit = _gloss_hits(gloss, terms)
        if short and not ghit:
            continue   # short root: the root signal alone is near-meaningless → require the gloss
        rows.append({
            "lang": "H", "num": base, "translit": d.get("xlit") or "",
            "gloss": gloss, "occ": _heb_occ(hconn, base),
            "stem_ok": True, "gloss_ok": bool(ghit), "ghit": ghit,
        })
    return rows


# ── print ────────────────────────────────────────────────────────────────────
def print_head(lang, num, translit, gloss, stem, terms):
    s = translit or "?"
    print(f"\n  HEAD  {lang}{num}  {s}  —  \"{gloss or '(no gloss)'}\"")
    label = "stem (translit prefix)" if lang == "G" else "root (affix-stripped)"
    print(f"        {label}: '{stem}'    gloss-terms: {sorted(terms) or '—'}")


def print_tier(name, rows, note=""):
    print(f"\n   {name} ({len(rows)}){('  — ' + note) if note else ''}")
    if not rows:
        print("      (none)")
        return
    rows.sort(key=lambda r: -r["occ"])
    for r in rows[:30]:
        sig = ("S" if r["stem_ok"] else "·") + ("G" if r["gloss_ok"] else "·")
        ev = (" gloss~" + "/".join(r["ghit"])) if r["ghit"] else ""
        name_ = f"{r['translit'] or '?'} ({r['lang']}{r['num']})"
        g = (r["gloss"] or "—")[:42]
        print(f"      [{sig}] {name_:<24} occ {r['occ']:>5}   {g}{ev}")
    if len(rows) > 30:
        print(f"      … +{len(rows) - 30} more (occ-sorted; tighten the stem to narrow)")


def run_head(conn, hconn, head):
    lang = head[0].upper()
    num = head[1:]
    if lang == "G":
        lemma, translit, gloss = _greek_head(conn, num)
        stem = _ascii(translit)[:4] or _ascii(translit)
        terms = _gloss_terms(gloss)
        print_head("G", num, translit, gloss, stem, terms)
        rows = assemble_greek(conn, num, stem, terms)
    else:
        lemma, xlit, plain, gloss = _heb_head(conn, num)
        # Hebrew "root" = affix-stripped consonant skeleton (no root field in the data — a heuristic).
        root = _heb_rootify((plain or "").strip())
        terms = _gloss_terms(gloss)
        print_head("H", num, xlit, gloss, root, terms)
        print("        NOTE: Hebrew root is APPROXIMATE (affix-stripped consonants, matched by")
        print("        containment) — there is no root field in the data, so this is a heuristic.")
        if len(root) < 3:
            print(f"        SHORT ROOT '{root}' (≤2 consonants) → GLOSS-ANCHORED: root-only matches are")
            print("        suppressed (a 2-consonant root nets junk like asher 'which', Asshur 'Assyria').")
        rows = assemble_hebrew(conn, hconn, num, root, terms)

    # Stem proposes every candidate (stem_ok always True); gloss confirms. Drop dead (0 occ).
    live = [r for r in rows if r["occ"] > 0]
    dead = len(rows) - len(live)
    include = [r for r in live if r["gloss_ok"]]
    border = [r for r in live if not r["gloss_ok"]]
    print_tier("INCLUDE    (stem-proposed, gloss confirms)", include)
    print_tier("BORDERLINE (stem-proposed, gloss did NOT confirm — REVIEW, the boundary)", border,
               note="[S·] = root/stem match, meaning didn't line up. False friends ('isheh/mishbath/"
                    "fever) AND legit-but-differently-glossed members both live here — by design")
    if dead:
        print(f"\n   (dropped {dead} candidate(s) with zero occurrences — never chipped)")


def main():
    ap = argparse.ArgumentParser(description="Read-only lexeme-family assembly with a visible boundary.")
    ap.add_argument("--query", choices=sorted(PROFILE_HEADS), help="a seeded query (fire/sabbath)")
    ap.add_argument("--head", help="comma-separated head Strong's, e.g. G4442,H784 (overrides --query)")
    args = ap.parse_args()

    if args.head:
        heads = [h.strip() for h in args.head.split(",") if h.strip()]
    elif args.query:
        heads = PROFILE_HEADS[args.query]
    else:
        ap.error("give --query fire|sabbath or --head G####,H####")

    conn = core.db_ro()
    try:
        hconn = core.heb_db()
    except Exception:
        hconn = None

    print("=" * 78)
    print("  FAMILY ASSEMBLY (read-only) — inclusion rule:")
    print("    CORE = the query head;  INCLUDE = stem AND gloss agree;")
    print("    BORDERLINE = one signal only → surfaced for review (never silently in/out).")
    print("=" * 78)
    try:
        for h in heads:
            run_head(conn, hconn, h)
    finally:
        conn.close()
        if hconn is not None:
            hconn.close()
    print()


if __name__ == "__main__":
    main()
