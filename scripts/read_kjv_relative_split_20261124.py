#!/usr/bin/env python3
"""Read-only: the Mar 7:11 shape across the KJV (DESIGN 9.262). A relative word and its particle
(ὃ ἐάν, ὃς ἄν) belong on one English word ("whatsoever"), but here sit on two neighbours:
whatsoever[G1437] thou[G3739]. The shift detector cannot see one misplaced tag, so this looks for
the pair directly and lists every hit with its counts, to be read by eye.

  python3 -u scripts/read_kjv_relative_split_20261124.py --out DIR

Opens the database and the rollback copy read-only. Writes only relative_split.tsv in --out.
Exit 0 = every control passed; 2 = a control failed.
"""
import argparse
import os
import sqlite3
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from read_kjv_firing_20261124 import ref                                # noqa: E402
from read_leftovers_20261122 import Fit, kjv_key, verse_tokens          # noqa: E402

ROOT = os.path.dirname(HERE)
PARTICLES = {"G302", "G1437"}                               # ἄν, ἐάν
RELATIVES = {"G3739", "G3745", "G3748", "G3699", "G3757"}   # ὅς, ὅσος, ὅστις, ὅπου, οὗ
MAT_15_5, MAR_7_11 = (40, 15, 5), (41, 7, 11)


def pairs(toks):
    """toks = [(word, [tags])]. -> [(i, j, shape, gap)]: the two words carry the particle and the
    relative separately, side by side or with one untagged word between."""
    out = []
    for i in range(len(toks) - 1):
        for gap in (0, 1):
            j = i + 1 + gap
            if j >= len(toks) or (gap and toks[i + 1][1]):
                continue
            a, b = set(toks[i][1]), set(toks[j][1])
            if a & PARTICLES and not a & RELATIVES and b & RELATIVES and not b & PARTICLES:
                out.append((i, j, "particle-first", gap))
            elif a & RELATIVES and not a & PARTICLES and b & PARTICLES and not b & RELATIVES:
                out.append((i, j, "relative-first", gap))
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
    fit, verses = Fit(), {}
    for b, c, v, w, t in conn.execute("""SELECT w.book_id, w.chapter, w.verse_num, w.word, GROUP_CONCAT(s.strongs_id)
                                         FROM kjv_words w LEFT JOIN kjv_strongs s ON s.word_id = w.word_id
                                         GROUP BY w.word_id ORDER BY w.book_id, w.chapter, w.verse_num, w.verse_pos"""):
        tags = t.split(",") if t else []
        k = kjv_key(w)
        if tags:
            fit.add(k, tags)
        verses.setdefault((b, c, v), []).append((k, tags))
    print(f"KJV verses: {len(verses):,}", flush=True)

    mat = [p for p in pairs(verses.get(MAT_15_5, [])) if p[2] == "particle-first" and p[3] == 0]
    today = pairs(verses.get(MAR_7_11, []))
    old = []
    if os.path.exists(a.old):
        oc = sqlite3.connect(f"file:{a.old}?mode=ro", uri=True)
        old = [p for p in pairs(verse_tokens(oc, MAR_7_11)) if p[2] == "particle-first" and p[3] == 0]
        oc.close()
    ok = len(mat) == 2 and bool(old) and not [p for p in today if p[2] == "particle-first" and p[3] == 0]
    print(f"  control, Mat 15:5 fires twice: {len(mat)}; Mar 7:11 before its fix fires: {len(old)}; today: {len(today)}")

    tally, second = Counter(), defaultdict(Counter)
    hit_verses = set()
    with open(os.path.join(a.out, "relative_split.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("verse\tshape\tgap\tword_1\ttags_1\tword_2\ttags_2\ttag_counts\tverse_with_tags\n")
        for key, toks in verses.items():
            for i, j, shape, gap in pairs(toks):
                tally[(shape, gap)] += 1
                hit_verses.add(key)
                second[(shape, gap)][toks[j][0]] += 1
                counts = "; ".join(f"{w}/{t} {fit.pair.get((w, t), 0)} of {fit.tag[t]}"
                                   for w, ts in (toks[i], toks[j]) for t in ts if t in PARTICLES | RELATIVES)
                text = " ".join(f"{w}[{'+'.join(t)}]" if t else w for w, t in toks)
                f.write("\t".join((ref(key), shape, str(gap), toks[i][0], "+".join(toks[i][1]), toks[j][0], "+".join(toks[j][1]), counts, text)) + "\n")
    conn.close()
    print(f"hits: {sum(tally.values())} in {len(hit_verses)} verses")
    for k in sorted(tally):
        print(f"  {k[0]}, {'side by side' if k[1] == 0 else 'one untagged word between'}: {tally[k]}; second word most often: {second[k].most_common(8)}")
    print(f"RELATIVE SPLIT CONTROL: {'PASS' if ok else 'FAILED - do not trust this read'}")
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
