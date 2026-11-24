#!/usr/bin/env python3
"""Read-only: which KJV verse the shift detector still fires on after the 11/24 write, and why
(DESIGN 9.260). Uses the production detector. For every tagged word in a flagged run it prints how
often the whole KJV puts that tag on this word, on the word before, and on the word after, plus the
words that carry the tag most.

  python3 -u scripts/read_kjv_firing_20261124.py --out DIR

Opens the database and the rollback copy read-only. Writes only firing_detail.tsv in --out.
Exit 0 = the control passed; 2 = it failed.
"""
import argparse
import os
import sqlite3
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from read_leftovers_20261122 import Fit, JOH_7_1, STRONG_RUN, kjv_key, shift_runs, verse_tokens  # noqa: E402

ROOT = os.path.dirname(HERE)
BOOKS = {1: "Gen", 2: "Exo", 3: "Lev", 4: "Num", 5: "Deu", 6: "Jos", 7: "Jdg", 8: "Rth", 9: "1Sa", 10: "2Sa", 11: "1Ki", 12: "2Ki",
         13: "1Ch", 14: "2Ch", 15: "Ezr", 16: "Neh", 17: "Est", 18: "Job", 19: "Psa", 20: "Pro", 21: "Ecc", 22: "Son", 23: "Isa",
         24: "Jer", 25: "Lam", 26: "Eze", 27: "Dan", 28: "Hos", 29: "Joe", 30: "Amo", 31: "Oba", 32: "Jon", 33: "Mic", 34: "Nah",
         35: "Hab", 36: "Zep", 37: "Hag", 38: "Zec", 39: "Mal", 40: "Mat", 41: "Mar", 42: "Luk", 43: "Joh", 44: "Act", 45: "Rom",
         46: "1Co", 47: "2Co", 48: "Gal", 49: "Eph", 50: "Php", 51: "Col", 52: "1Th", 53: "2Th", 54: "1Ti", 55: "2Ti", 56: "Tit",
         57: "Phm", 58: "Heb", 59: "Jas", 60: "1Pe", 61: "2Pe", 62: "1Jn", 63: "2Jn", 64: "3Jn", 65: "Jud", 66: "Rev"}


def ref(key):
    return f"{BOOKS.get(key[0], key[0])} {key[1]}:{key[2]}"


def detail(toks, run, fit, top):
    """One line per tagged word in the run."""
    out = []
    _d, _n, a, b = run
    for i in range(a, b + 1):
        w, tags = toks[i]
        for t in tags:
            before = toks[i - 1][0] if i > 0 else ""
            after = toks[i + 1][0] if i + 1 < len(toks) else ""
            out.append((i, w, t, fit.pair.get((w, t), 0), fit.tag[t], before, fit.pair.get((before, t), 0),
                        after, fit.pair.get((after, t), 0), " ".join(f"{x}:{c}" for x, c in top[t].most_common(4))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(ROOT, "bible.db"))
    ap.add_argument("--old", default=os.path.join(ROOT, "bible_pre_edition_upgrade_20261121.db"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    conn.execute("PRAGMA busy_timeout=30000")
    sql = """SELECT w.book_id, w.chapter, w.verse_num, w.word, GROUP_CONCAT(s.strongs_id)
             FROM kjv_words w LEFT JOIN kjv_strongs s ON s.word_id = w.word_id
             GROUP BY w.word_id ORDER BY w.book_id, w.chapter, w.verse_num, w.verse_pos"""
    fit, verses, top = Fit(), {}, defaultdict(Counter)
    for b, c, v, w, t in conn.execute(sql):
        tags = t.split(",") if t else []
        k = kjv_key(w)
        if tags:
            fit.add(k, tags)
            for x in tags:
                top[x][k] += 1
        verses.setdefault((b, c, v), []).append((k, tags))
    print(f"KJV verses: {len(verses):,}; tagged pairs: {len(fit.pair):,}", flush=True)

    ok = True
    if os.path.exists(a.old):
        oc = sqlite3.connect(f"file:{a.old}?mode=ro", uri=True)
        fired = any(d == "late" and n >= 10 for d, n, _x, _y in shift_runs(verse_tokens(oc, JOH_7_1), fit))
        oc.close()
    else:
        fired = False
    quiet = not shift_runs(verses.get(JOH_7_1, []), fit)
    print(f"  control, Joh 7:1 before its fix fires: {fired}; today quiet: {quiet}")
    ok = fired and quiet

    strong, weak = [], []
    with open(os.path.join(a.out, "firing_detail.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("verse\ttier\tdirection\ttags_in_run\tword_index\tword\ttag\ton_this_word\ttag_total\tword_before\ton_word_before\tword_after\ton_word_after\ttag_most_on\n")
        for key, toks in verses.items():
            for run in shift_runs(toks, fit):
                tier = "strong" if run[1] >= STRONG_RUN else "weak"
                (strong if tier == "strong" else weak).append(key)
                for row in detail(toks, run, fit, top):
                    f.write("\t".join(str(x) for x in (ref(key), tier, run[0], run[1]) + row) + "\n")
    strong = sorted(set(strong))
    print(f"long-shift verses (3+ tags): {len(strong)}: {[ref(k) for k in strong]}")
    print(f"verses with only a 2-tag run: {len(set(weak) - set(strong))}")
    for key in strong:
        toks = verses[key]
        print(f"\n{ref(key)}: " + " ".join(f"{w}[{'+'.join(t)}]" if t else w for w, t in toks))
        for run in shift_runs(toks, fit):
            if run[1] < STRONG_RUN:
                continue
            print(f"  run: {run[0]}, {run[1]} tags, words {run[2]} to {run[3]}")
            for i, w, t, n, total, bw, bn, aw, an, most in detail(toks, run, fit, top):
                print(f"  {i} {w} {t}: on this word {n} of {total}; on the word before ({bw}) {bn}; on the word after ({aw}) {an}; most on: {most}")
    conn.close()
    print(f"\nKJV FIRING CONTROL: {'PASS' if ok else 'FAILED - do not trust this read'}")
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
