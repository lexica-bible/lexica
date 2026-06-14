#!/usr/bin/env python3
"""
One-off: thread the big undatable WISDOM blocks (Psalms / Proverbs / Ecclesiastes /
Song) through the surrounding narrative so the plan doesn't hit walls of psalm-only
reading days.

The standard one-year arrangement already places the *datable* psalms next to their
events (Psalm 51 after Bathsheba, etc.) — those are short interleaved runs and we LEAVE
THEM PUT. What it dumps in walls are the undatable ones: ~30 of David's remaining psalms
at his death, all of Proverbs in Solomon's reign, and Psalms 42-150 in one ~56-long pile.
Those have no historical hook, so spreading them is editorial (for reading flow), same as
the smoother published plans (e.g. Crossway's ESV) do.

What it does, per era:
  - find maximal runs of >= 3 consecutive wisdom passages (the "walls");
  - leave short interleaved wisdom (runs of 1-2) exactly where it is;
  - re-thread each wall's passages evenly across the NARRATIVE passages of that era
    that originally preceded the wall, so they stay within their era and reading window.

Job and Lamentations are NOT touched (coherent books read in sequence, not wisdom piles).

Rewrites source_oneyear.txt in place (git is the backup). Then run build_chronological.py.
"""
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source_oneyear.txt")

WISDOM_FIRST = {"Psalm", "Psalms", "Proverbs", "Ecclesiastes",
                "SongOfSongs", "Song", "SongOfSolomon"}
WALL = 3   # a run of this many consecutive wisdom passages or more = a wall to spread


def is_wisdom(line):
    return line.split()[0] in WISDOM_FIRST


def redistribute(passages):
    n = len(passages)
    wis = [is_wisdom(p) for p in passages]
    # maximal consecutive wisdom runs
    runs, j = [], 0
    while j < n:
        if wis[j]:
            k = j
            while k < n and wis[k]:
                k += 1
            runs.append((j, k))
            j = k
        else:
            j += 1
    walls = [(s, e) for (s, e) in runs if e - s >= WALL]
    if not walls:
        return passages[:]
    wall_idx = {i for (s, e) in walls for i in range(s, e)}
    # base = everything that stays anchored (narrative + short interleaved wisdom),
    # tagged with its original index; floaters get None.
    result = [(i, passages[i]) for i in range(n) if i not in wall_idx]
    for (s, e) in walls:
        floaters = [passages[i] for i in range(s, e)]
        anchors = [pi for pi, (oi, _) in enumerate(result) if oi is not None and oi < s]
        if not anchors:   # nothing precedes it in-era → spread across all anchors
            anchors = [pi for pi, (oi, _) in enumerate(result) if oi is not None]
        A, F = len(anchors), len(floaters)
        ins = defaultdict(list)
        for f in range(F):
            a = max(0, min(A - 1, round((f + 1) * A / (F + 1)) - 1))
            ins[anchors[a]].append(floaters[f])
        rebuilt = []
        for pi, item in enumerate(result):
            rebuilt.append(item)
            for fl in ins.get(pi, ()):
                rebuilt.append((None, fl))
        result = rebuilt
    return [line for (_, line) in result]


def main():
    lines = open(SRC, encoding="utf-8").read().splitlines()
    header, eras, cur = [], [], None
    for raw in lines:
        s = raw.rstrip()
        if s.startswith("# ERA:"):
            cur = {"header": s, "passages": []}
            eras.append(cur)
        elif cur is None:
            header.append(raw)            # top comment block, verbatim
        elif not s.strip() or s.lstrip().startswith("#"):
            continue                      # drop blanks / stray comments inside eras
        else:
            cur["passages"].append(s.strip())

    moved = 0
    out = list(header)
    if out and out[-1].strip():
        out.append("")
    for era in eras:
        before = era["passages"]
        after = redistribute(before)
        # count how many wisdom passages shifted position
        moved += sum(1 for i, p in enumerate(after)
                     if is_wisdom(p) and (i >= len(before) or before[i] != p))
        out.append(era["header"])
        out.extend(after)
        out.append("")
    open(SRC, "w", encoding="utf-8").write("\n".join(out).rstrip() + "\n")
    total = sum(len(e["passages"]) for e in eras)
    print(f"rewrote source_oneyear.txt — {len(eras)} eras, {total} passages, "
          f"~{moved} wisdom passages re-threaded")


if __name__ == "__main__":
    main()
