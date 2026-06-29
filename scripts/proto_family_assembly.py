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

THE RULE (a single signal can't catch a false friend — the DISAGREEMENT between signals does)
  Two independent signals per candidate:
     STEM   — shares the head's stem (Greek translit prefix) or root (Hebrew lemma consonants)
     GLOSS  — its dictionary gloss shares a meaning-word with the head's gloss
  Tiers:
     CORE       — the query's own head word(s).
     INCLUDE    — BOTH signals fire (stem AND gloss agree).
     BORDERLINE — exactly ONE fires → SURFACED for review, never silently dropped or included.
  'isheh / mishbath fire STEM but not GLOSS → BORDERLINE. That is the visible boundary, computed.
  pyretos "fever" (from pyr) does the same on the Greek side. The engine does NOT decide the
  borderline cases — it surfaces them with their evidence and a human adjudicates.

WHY THIS IS HONEST, NOT CLEAN
  The deliverable is deliberately NOT a tidy auto-list. It is a family WITH its inclusion rule
  stated and the marginal words shown with the evidence (which signals fired, the matched word,
  occurrence count). Same discipline as the panel: show the boundary, don't hide it. Hebrew is
  weaker than Greek (no etymology, no root field) so it surfaces MORE as borderline — stated, not
  papered over. The robust Hebrew bridge is the LXX seam (separate view), a later refinement.

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


def _stem3(tok):
    return tok[:3]


def _gloss_terms(gloss):
    """The head gloss's meaning-words, 3-char stemmed: 'fire, trials' -> {'fir','tri'}."""
    out = set()
    for w in re.findall(r"[A-Za-z]+", gloss or ""):
        w = w.lower()
        if len(w) >= 3 and w not in _STOP:
            out.add(_stem3(w))
    return out


def _gloss_hits(gloss, terms):
    """The actual gloss words that match a head term (for showing the evidence)."""
    hits = []
    for w in re.findall(r"[A-Za-z]+", gloss or ""):
        if len(w) >= 3 and _stem3(w.lower()) in terms:
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
        "SELECT lemma, xlit, description, lemma_plain FROM bdb WHERE strongs_id=?",
        (f"H{num}",)).fetchone()
    lemma = (r["lemma"] if r else "") or ""
    xlit = (r["xlit"] if r else "") or ""
    plain = (r["lemma_plain"] if r else "") or (lemma)
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
    cand = {}   # base -> {translit, gloss, stem_ok, gloss_ok}
    # STEM pass: lexicon rows whose ascii translit starts with the head stem.
    for r in conn.execute("SELECT strongs_g, strongs, translit FROM lexicon"):
        t = _ascii(r["translit"])
        if t and stem and t.startswith(stem):
            base = (r["strongs_g"] or ("G" + (r["strongs"] or ""))).lstrip("G")
            cand.setdefault(base, {})["translit"] = r["translit"] or ""
            cand[base]["stem_ok"] = True
    # GLOSS pass: word_gloss Greek rows whose gloss shares a head term.
    if _has_table(conn, "word_gloss") and terms:
        for r in conn.execute("SELECT strongs, gloss FROM word_gloss WHERE strongs GLOB 'G*'"):
            if _gloss_hits(r["gloss"], terms):
                base = r["strongs"].lstrip("G").split(".")[0]
                cand.setdefault(base, {})["gloss_ok"] = True
    # fill gloss + flags + occ for every candidate
    rows = []
    for base, d in cand.items():
        if base == num:
            continue
        gloss = _wg(conn, f"G{base}")
        rows.append({
            "lang": "G", "num": base, "translit": d.get("translit") or "",
            "gloss": gloss, "occ": _greek_occ(conn, base),
            "stem_ok": bool(d.get("stem_ok")),
            "gloss_ok": bool(d.get("gloss_ok") or _gloss_hits(gloss, terms)),
            "ghit": _gloss_hits(gloss, terms),
        })
    return rows


def assemble_hebrew(conn, hconn, num, root, terms):
    """Candidates near a Hebrew head: lemma_plain prefix/substring (STEM) ∪ gloss-term (GLOSS).
    Substring only for roots of ≥3 letters (a 2-letter root matches half the lexicon)."""
    cand = {}
    use_sub = len(root) >= 3
    for r in conn.execute("SELECT strongs_id, xlit, lemma_plain FROM bdb"):
        lp = (r["lemma_plain"] or "")
        if not lp or not root:
            continue
        if lp.startswith(root) or (use_sub and root in lp):
            base = (r["strongs_id"] or "").lstrip("H")
            if base:
                cand.setdefault(base, {})["xlit"] = r["xlit"] or ""
                cand[base]["stem_ok"] = True
    if _has_table(conn, "word_gloss") and terms:
        for r in conn.execute("SELECT strongs, gloss FROM word_gloss WHERE strongs GLOB 'H*'"):
            if _gloss_hits(r["gloss"], terms):
                base = r["strongs"].lstrip("H").rstrip("abcdefgh")
                cand.setdefault(base, {})["gloss_ok"] = True
    rows = []
    for base, d in cand.items():
        if base == num:
            continue
        gloss = _wg(conn, f"H{base}")
        rows.append({
            "lang": "H", "num": base, "translit": d.get("xlit") or "",
            "gloss": gloss, "occ": _heb_occ(hconn, base),
            "stem_ok": bool(d.get("stem_ok")),
            "gloss_ok": bool(d.get("gloss_ok") or _gloss_hits(gloss, terms)),
            "ghit": _gloss_hits(gloss, terms),
        })
    return rows


# ── print ────────────────────────────────────────────────────────────────────
def print_head(lang, num, translit, gloss, stem, terms):
    s = translit or "?"
    print(f"\n  HEAD  {lang}{num}  {s}  —  \"{gloss or '(no gloss)'}\"")
    label = "stem (translit prefix)" if lang == "G" else "root (lemma consonants)"
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
        # Hebrew "root" = the head's consonant lemma (lemma_plain); 2-letter heads stay prefix-only.
        root = (plain or "").strip()
        terms = _gloss_terms(gloss)
        print_head("H", num, xlit, gloss, root, terms)
        rows = assemble_hebrew(conn, hconn, num, root, terms)

    # tier by signal agreement; drop dead (0 occ) candidates (no dead chips, same as the live engine).
    live = [r for r in rows if r["occ"] > 0]
    dead = len(rows) - len(live)
    include = [r for r in live if r["stem_ok"] and r["gloss_ok"]]
    border = [r for r in live if r["stem_ok"] != r["gloss_ok"]]
    print_tier("INCLUDE   (stem AND gloss agree)", include)
    print_tier("BORDERLINE (one signal only — REVIEW, this is the boundary)", border,
               note="[S·]=root-match only (false-friend risk: 'isheh/mishbath live here); [·G]=meaning-only")
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
