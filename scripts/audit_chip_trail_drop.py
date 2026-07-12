#!/usr/bin/env python3
"""
audit_chip_trail_drop.py — READ-ONLY. Size the Jer 46:15 class: chip-mode bracket
groups whose lifted trailing punctuation lands on a chip that never renders.

MECHANISM (59c-library-render.jsx, chip mode): a bracket group's trailing clause
mark (".,;:!?" etc.) is stripped off every member in source order, accumulated,
then re-emitted after the group's LAST member post-reorder (wi === length-1).
But `bracketChip` returns null for a member with no English label — and an
empty-gloss token (folded pronoun/article) has no order digit, so it sorts LAST
(greek_pos null -> 999). The mark is pinned to a chip that is never drawn, and
silently disappears from the reading pane. Prose mode already walks back to the
last member WITH text (getEnglishOrderWords in 56-library-order-logic.jsx); chip
mode does not.

DETECTION — replicates the chip pipeline exactly, per verse:
  1. member filter, same as render line 317: english OR kjv_def(word_gloss,
     dotted-aware) OR strongs_base='*'
  2. group runs of equal bracket_id in position order (groupForGreekMode)
  3. TRAIL lift, same regex + m.index>0 rule as the render
  4. stable reorder by greek_pos (missing -> 999)
  5. FLAG when trail is non-empty AND the reordered-last member's chip label
     (english, else english_head) is empty — that chip returns null, mark lost.

CONTROL: the detector's numbers are only trustable once proven it CAN fire —
  python3 scripts/audit_chip_trail_drop.py bible.db --control
must FIRE on Jer 46:15 ('?') AND Jer 46:16 group 1 (','), and must stay QUIET on
Jer 46:16 group 2 ("of the Grecian." -> last member 'sword' has text, mark shows).
Aborts loudly if any control fails.

READ-ONLY (opens the DB mode=ro). Run on PA from the repo root:
  python3 scripts/audit_chip_trail_drop.py bible.db            # counts
  python3 scripts/audit_chip_trail_drop.py bible.db --list     # per-verse detail
"""
import argparse
import re
import sqlite3
import sys

# Same trailing-mark pattern as the chip render's TRAIL (59c line 337).
TRAIL = re.compile(r"\s*(?:--|—|–|[.,;:!?·)])+$")


def open_ro(path):
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def load_words(conn):
    """All ABP words with the same kjv_def the chapter endpoint serves, keyed by verse."""
    has_gloss = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='word_gloss'").fetchone()
    has_dotted = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='dotted_lexicon'").fetchone()
    if has_gloss and has_dotted:
        gloss = "COALESCE(wgd.gloss, wgb.gloss)"
        joins = ("LEFT JOIN dotted_lexicon dl ON dl.strongs = 'G' || w.strongs "
                 "LEFT JOIN word_gloss wgd ON wgd.strongs = 'G' || w.strongs "
                 "LEFT JOIN word_gloss wgb ON wgb.strongs = w.strongs_base "
                 "AND dl.strongs IS NULL")
    elif has_gloss:
        gloss = "COALESCE(wgd.gloss, wgb.gloss)"
        joins = ("LEFT JOIN word_gloss wgd ON wgd.strongs = 'G' || w.strongs "
                 "LEFT JOIN word_gloss wgb ON wgb.strongs = w.strongs_base")
    else:
        gloss = "l.kjv_def"
        joins = "LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base"
    rows = conn.execute(
        f"SELECT v.book, v.chapter, v.verse, w.position, w.english, w.english_head, "
        f"w.strongs_base, w.bracket_id, w.greek_pos, {gloss} AS kjv_def "
        f"FROM words w JOIN verses v ON w.verse_id = v.id {joins} "
        f"ORDER BY v.id, w.position")
    verses = {}
    for bk, ch, vs, pos, eng, head, base, bid, gp, kdef in rows:
        verses.setdefault((bk, ch, vs), []).append({
            "position": pos, "english": eng or "", "english_head": head or "",
            "strongs_base": base or "", "bracket_id": bid, "greek_pos": gp,
            "kjv_def": kdef or "",
        })
    return verses


def find_drops(words):
    """Return [(bracket_id, lost_mark, group_english)] for one verse's word list."""
    # 1. render's member filter (59c line 317)
    members = [w for w in sorted(words, key=lambda w: w["position"])
               if w["english"] or w["kjv_def"] or w["strongs_base"] == "*"]
    # 2. runs of equal bracket_id (groupForGreekMode)
    groups, cur = [], None
    for w in members:
        bid = w["bracket_id"]
        if bid is None:
            cur = None
            continue
        if cur is None or cur[0] != bid:
            cur = (bid, [])
            groups.append(cur)
        cur[1].append(w)
    hits = []
    for bid, gw in groups:
        # 3. TRAIL lift in source order, same rules as the render
        trail, cleaned = "", []
        for w in gw:
            eng = w["english"].strip()
            if eng and TRAIL.sub("", eng) == "":          # pure-punctuation token
                trail += eng
                continue
            m = TRAIL.search(eng)
            if m and m.start() > 0:                       # keep a real word before the mark
                trail += m.group(0).strip()
                cleaned.append(dict(w, english=eng[:m.start()].rstrip()))
            else:
                cleaned.append(dict(w, english=eng))
        if not (trail and cleaned):
            continue
        # 4. stable reorder by greek_pos, missing -> 999
        ordered = sorted(cleaned, key=lambda w: w["greek_pos"] if w["greek_pos"] is not None else 999)
        # 5. the render pins the trail to the LAST member; no label -> chip is null -> mark lost
        last = ordered[-1]
        label = last["english"] or last["english_head"]
        if not label.strip():
            text = " ".join(w["english"] for w in ordered if w["english"])
            hits.append((bid, trail, text))
    return hits


CONTROLS = [
    # (book, chapter, verse, must_fire, expected_mark_or_None)
    ("Jer", 46, 15, True,  "?"),   # known positive: '?' pinned to the empty pos-5 chip
    ("Jer", 46, 16, True,  ","),   # known positive: ',' from "said," lost the same way
]


def run_control(verses):
    ok = True
    for bk, ch, vs, must_fire, mark in CONTROLS:
        hits = find_drops(verses.get((bk, ch, vs), []))
        marks = [h[1] for h in hits]
        if must_fire and mark not in marks:
            print(f"CONTROL FAIL: {bk} {ch}:{vs} expected a lost '{mark}', got {marks or 'nothing'}")
            ok = False
        else:
            print(f"control ok: {bk} {ch}:{vs} -> lost {marks}")
    # negative control: Jer 46:16 group 2 ("of the Grecian." -> "sword.") must NOT flag,
    # i.e. exactly ONE hit in that verse (the comma), never two.
    n16 = len(find_drops(verses.get(("Jer", 46, 16), [])))
    if n16 != 1:
        print(f"CONTROL FAIL: Jer 46:16 expected exactly 1 hit (the comma), got {n16}")
        ok = False
    else:
        print("control ok: Jer 46:16 group 2 (Grecian sword.) correctly quiet")
    if not ok:
        print("ABORT: detector cannot be trusted; do not read the corpus numbers.")
        sys.exit(1)
    print("controls passed\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--list", action="store_true", help="print every flagged verse")
    ap.add_argument("--control", action="store_true", help="run controls only")
    args = ap.parse_args()

    conn = open_ro(args.db)
    verses = load_words(conn)
    conn.close()

    run_control(verses)
    if args.control:
        return

    total_verses, total_marks, by_mark = 0, 0, {}
    flagged = []
    for key in sorted(verses):
        hits = find_drops(verses[key])
        if hits:
            total_verses += 1
            total_marks += len(hits)
            for _, mark, text in hits:
                by_mark[mark] = by_mark.get(mark, 0) + 1
            flagged.append((key, hits))
    print(f"verses affected: {total_verses}")
    print(f"marks lost:      {total_marks}")
    for mark, n in sorted(by_mark.items(), key=lambda kv: -kv[1]):
        print(f"  {mark!r}: {n}")
    if args.list:
        print()
        for (bk, ch, vs), hits in flagged:
            for bid, mark, text in hits:
                print(f"{bk} {ch}:{vs}  lost {mark!r} after \"{text}\"")


if __name__ == "__main__":
    main()
