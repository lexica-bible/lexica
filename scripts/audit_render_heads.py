#!/usr/bin/env python3
"""Read-only guard for the phrase-boundary render class (PA-only; reads live bible.db).

Background: ABP parks a whole multi-word phrase gloss on one token slot ("Jesus to them,"
on the autos/G846 pronoun). The word-study "renders as" list now COUNTS the token's own
head (english_head), not the parked phrase, so a pronoun can no longer surface a phantom
proper-noun render. See parse_abp.HEAD_WORD_TAIL_CAVEAT + tests/test_render_head_no_phantom.py.

This audit re-checks the live pronoun/function numbers most exposed to the parked-phrase
convention. It reuses the PRODUCTION fold (views_lexicon._normalize_gloss) — never a second
copy — so it can't pass while the real panel regresses.

  HARD FAIL  — any live render on these numbers is a proper-noun-class word (a name leaking
               onto a pronoun). This is the defect the fix exists to kill.
  WARN       — a render appears that isn't in the frozen post-fix snapshot below (a new one to
               eyeball), or a frozen render has vanished. Warnings don't fail the run: a words
               rebuild shifts counts, and a c=1 residue crossing to c=2 is drift, not a bug.

  --refreeze   print the CURRENT folded render sets (paste back into FROZEN after a rebuild).

Run on PA:  python3 scripts/audit_render_heads.py [path-to-bible.db]
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from views_lexicon import _normalize_gloss, _FUNCTION_STRONGS  # production fold — reused, not copied

NUMS = ("846", "3778", "1473", "1438")  # the pronoun/function numbers most exposed to phrase-parking

# Frozen post-fix snapshot (folded renders with count > 1), captured 2026-07-03 from the live db.
# Not a serving-path list — a drift baseline for this on-demand audit. Re-freeze with --refreeze
# after a words rebuild.
FROZEN = {
    "846": {"him", "them", "their", "her", "of", "it", "he", "his", "they", "himself", "same",
            "she", "your", "my", "themselves", "in", "with", "yourselves", "theirs", "its",
            "myself", "itself", "herself", "things", "these", "away", "this", "thing", "than",
            "ourselves", "by", "saying", "hers", "that", "place", "on", "own", "to", "time",
            "the", "down", "at", "while", "concerning", "yourself", "what", "way", "let",
            "during", "did", "any", "and"},
    "3778": {"this", "these", "things", "one", "she", "he", "thing", "do", "than", "man", "side",
             "woman", "will", "which", "thus", "did", "they", "others", "let", "it", "does",
             "women", "with", "who", "way", "time", "those", "themselves", "that", "speaking",
             "some", "people", "doing"},
    "1473": {"i", "me", "you", "us", "himself", "your", "my", "do", "we", "same", "themselves",
             "this", "myself", "shall", "these", "yourselves", "yourself", "will", "our", "mine",
             "itself", "him", "did", "yours", "indeed", "away", "things", "the", "house", "have",
             "go", "but", "both", "berate", "and"},
    "1438": {"himself", "themselves", "own", "yourselves", "ourselves", "herself", "itself",
             "his", "their", "yourself", "her", "him", "them", "of", "other"},
}


def _live_renders(conn, num):
    """{folded_render: count} for one base number, exactly as the panel counts it."""
    sid = "G" + num
    is_func = num in _FUNCTION_STRONGS
    rows = conn.execute("""
        SELECT COALESCE(NULLIF(english_head,''), english) AS g, COUNT(*) AS c
        FROM words
        WHERE strongs_base = ? AND english IS NOT NULL AND english != '' AND english != '*'
        GROUP BY COALESCE(NULLIF(english_head,''), english)
    """, (sid,)).fetchall()
    out = {}
    for g, c in rows:
        k = _normalize_gloss(g or "", is_func=is_func)
        if k:
            out[k] = out.get(k, 0) + c
    return {k: c for k, c in out.items() if c > 1}  # panel drops singletons


def _proper_noun_renders(conn):
    """Folded render set used by REAL proper-noun tokens (jesus, moses, …) — the leak signal."""
    out = set()
    for (eng,) in conn.execute(
            "SELECT DISTINCT english FROM words WHERE is_pn=1 AND english NOT IN ('','*')"):
        k = _normalize_gloss(eng or "", is_func=False)
        if k:
            out.add(k)
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    db = sys.argv[-1] if len(sys.argv) > 1 and sys.argv[-1].endswith(".db") \
        else os.path.expanduser("~/bible-db/bible.db")
    refreeze = "--refreeze" in sys.argv
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    if refreeze:
        for num in NUMS:
            live = sorted(_live_renders(conn, num))
            print(f'    "{num}": {{' + ", ".join(f'"{r}"' for r in live) + "},")
        conn.close()
        return 0

    pn = _proper_noun_renders(conn)
    hard_fail, warns = [], []
    for num in NUMS:
        live = _live_renders(conn, num)
        names = sorted(set(live) & pn)
        if names:
            hard_fail.append(f"G{num}: proper-noun render(s) leaked -> {', '.join(names)}")
        new = sorted(set(live) - FROZEN.get(num, set()))
        gone = sorted(FROZEN.get(num, set()) - set(live))
        if new:
            warns.append(f"G{num}: new render(s) not in frozen set -> {', '.join(new)}")
        if gone:
            warns.append(f"G{num}: frozen render(s) now absent -> {', '.join(gone)}")
    conn.close()

    for w in warns:
        print("  warn: " + w)
    if hard_fail:
        for f in hard_fail:
            print("  FAIL: " + f)
        print(f"\n{len(hard_fail)} FAILED — a name is rendering on a pronoun/function number.")
        return 1
    print("\nRender-head guard: no proper-noun leak on G846/G3778/G1473/G1438." +
          (" (see warnings above)" if warns else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
