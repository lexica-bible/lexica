#!/usr/bin/env python3
"""
audit_lsj_tier_diff.py — READ-ONLY. Prove the proposed length-mark lookup tier is
SURGICAL before it is written into views_lsj.py.

It runs TWO resolvers across the whole Greek lexicon and diffs the final resolved
LSJ headword:

  OLD (current live behavior, views_lsj.lsj_lookup):
    1. exact:  key == lemma
    2. else:   first-by-rowid where strip_ALL_marks(key) == strip_ALL_marks(lemma)
    3. then follow a 'v. <i>X</i>' cross-ref stub / drop a non-xref stub

  NEW (proposed — INSERT a tier, do not replace):
    1. exact:  key == lemma
    2. NEW:    first-by-rowid where fold_LENGTH(key) == fold_LENGTH(lemma)
               (drops ONLY vowel-length marks ῡ/ῠ, keeps the accent — this is the
                tier that uniquely resolves θῡμός and leaves θύμος "thyme" alone)
    3. else:   first-by-rowid where strip_ALL_marks(key) == strip_ALL_marks(lemma)
    4. then the same stub/cross-ref follow

Both paths share the EXACT and FULL-STRIP tiers, so the only entries that can move
are ones the new middle tier catches. The diff tells you exactly which, and a
length-fold "desired" heuristic labels each move wrong->right / right->wrong / review.

SAFE TO COMMIT THE FIX iff: every changed row is θῡμός-class and wrong->right (or a
correct stay-put). ANY right->wrong row must be read before writing.

READ-ONLY (mode=ro). Run on PA from the repo root:
  python3 scripts/audit_lsj_tier_diff.py bible.db
  python3 scripts/audit_lsj_tier_diff.py bible.db --corpus-only
"""
import argparse
import re
import sqlite3
import unicodedata

_LEN_MARKS = {"̄", "̆"}          # macron, breve = vowel-length marks
_GREEK_RE = re.compile(r"[Ͱ-Ͽἀ-῿]")
_XREF_RE = re.compile(r"\bv\.\s*<i>([^<]+)</i>")


def strip_all_marks(s):
    if not s:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    ).lower()


def fold_length(s):
    if not s:
        return ""
    return unicodedata.normalize(
        "NFC",
        "".join(c for c in unicodedata.normalize("NFD", s) if c not in _LEN_MARKS),
    ).lower()


def _untag(html):
    return re.sub(r"<[^>]+>", "", html or "").strip()


def _gloss(html, n=42):
    return _untag(html)[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--corpus-only", action="store_true")
    ap.add_argument("--list", action="store_true", help="also dump unchanged-but-resolved")
    args = ap.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT rowid AS rid, key, def_html FROM lsj WHERE key NOT LIKE '-%' ORDER BY rowid"
    ).fetchall()

    # Index the LSJ table the way each resolver tier needs it.
    keys = []                 # rowid order
    exact = {}                # key -> def_html
    by_strip = {}             # strip_all -> [keys] rowid order
    by_fold = {}              # fold_length -> [keys] rowid order
    by_strip_nohyph = {}      # strip_all(no hyphen) -> first key (for xref follow)
    for r in rows:
        k = r["key"]
        keys.append(k)
        exact[k] = r["def_html"]
        s = strip_all_marks(k.replace("-", ""))
        f = fold_length(k.replace("-", ""))
        by_strip.setdefault(s, []).append(k)
        by_fold.setdefault(f, []).append(k)
        by_strip_nohyph.setdefault(s, k)

    def follow_stub(key):
        """Mirror _resolve_lsj_xref + _is_lsj_stub: follow a 'v. X' pointer, drop a dead stub."""
        d = exact.get(key)
        if not d:
            return key
        text = _untag(d)
        if len(text) > 150:
            return key
        m = _XREF_RE.search(d)
        if not m:
            return key  # short but not a stub -> kept as-is by live code
        after = d[m.end():].lstrip()
        if after.startswith("("):
            return key  # ambiguous (A)/(B) -> not followed
        ref = m.group(1).strip()
        ref_plain = strip_all_marks(ref.replace("-", ""))
        if ref in exact:
            return ref
        tgt = by_strip_nohyph.get(ref_plain)
        return tgt if tgt else None   # _is_lsj_stub: dead stub -> None

    def resolve(lemma, new):
        if lemma in exact:
            picked = lemma
        else:
            picked = None
            if new:
                cand = by_fold.get(fold_length(lemma.replace("-", "")), [])
                if cand:
                    picked = cand[0]
            if picked is None:
                cand = by_strip.get(strip_all_marks(lemma.replace("-", "")), [])
                if cand:
                    picked = cand[0]
        if picked is None:
            return None
        return follow_stub(picked)

    used = None
    if args.corpus_only:
        used = {x[0] for x in conn.execute(
            "SELECT DISTINCT strongs_base FROM words WHERE strongs_base GLOB 'G*'"
        ).fetchall()}

    lex = conn.execute(
        "SELECT strongs, lemma FROM lexicon WHERE lemma IS NOT NULL AND lemma != ''"
    ).fetchall()
    conn.close()

    changed, scanned = [], 0
    for lr in lex:
        lemma = lr["lemma"].strip()
        if not _GREEK_RE.search(lemma):
            continue
        if used is not None and ("G" + str(lr["strongs"])) not in used:
            continue
        scanned += 1
        old = resolve(lemma, new=False)
        new = resolve(lemma, new=True)
        if old == new:
            continue
        # length-fold "desired" = the entry whose accents match the lemma's, uniquely
        df = [k for k in by_fold.get(fold_length(lemma.replace("-", "")), [])]
        desired = df[0] if len(df) == 1 else None
        if desired is not None:
            if new == desired and old != desired:
                verdict = "wrong->right"
            elif old == desired and new != desired:
                verdict = "RIGHT->WRONG"
            else:
                verdict = "review"
        else:
            verdict = "review(no-unique)"
        changed.append({
            "strongs": lr["strongs"], "lemma": lemma,
            "old": old, "new": new, "verdict": verdict,
            "old_g": _gloss(exact.get(old)) if old else "(strongs-fallback/none)",
            "new_g": _gloss(exact.get(new)) if new else "(strongs-fallback/none)",
        })

    scope = "in-corpus" if args.corpus_only else "all-lexicon"
    w2r = sum(1 for c in changed if c["verdict"] == "wrong->right")
    r2w = sum(1 for c in changed if c["verdict"] == "RIGHT->WRONG")
    rev = len(changed) - w2r - r2w
    print(f"Scanned {scanned} Greek lexicon lemmas ({scope}).")
    print(f"Resolution CHANGES under the new tier: {len(changed)}")
    print(f"   wrong->right : {w2r}")
    print(f"   RIGHT->WRONG : {r2w}   <-- must be 0 to commit safely")
    print(f"   review       : {rev}")
    print()
    for c in sorted(changed, key=lambda x: int(re.sub(r'\D', '', x['strongs']) or 0)):
        print(f"  G{c['strongs']:<6} {c['lemma']:<16} [{c['verdict']}]")
        print(f"       old {c['old']!r:<18} {c['old_g']}")
        print(f"       new {c['new']!r:<18} {c['new_g']}")


if __name__ == "__main__":
    main()
