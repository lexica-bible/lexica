#!/usr/bin/env python3
"""Lane-② ride instrument: name the split_merges skips and show both states.

fix_split_merges applied 208/237 on the ride copy — 29 verses skipped because
the PN-star pass changed their wording before the patch looked. This names
ALL 29 (not the 10 printed samples) and prints each verse's word cells from
LIVE (patch applied) beside the RIDE copy (pass applied instead), so every
one can be adjudicated by content.

A verse counts as APPLIED when every entry's (new_pos, new_eng) matches the
copy; otherwise it is a skip and both sides print.

Usage: python3 scripts/list_split_merge_skips.py <live-db> <ride-db>
Read-only.
"""
import json
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXES = json.load(open(os.path.join(HERE, "split_merge_fixes.json"),
                       encoding="utf-8"))


def verse_rows(conn, book, ch, vs):
    return conn.execute(
        "SELECT w.position, w.english, w.strongs_base, w.bracket_id,"
        " w.greek_pos FROM words w "
        "JOIN verses v ON v.id = w.verse_id "
        "WHERE v.book=? AND v.chapter=? AND v.verse=? ORDER BY w.position",
        (book, ch, vs)).fetchall()


TRAIL_RE = re.compile(r"[.,;:!?·)]+$")


def display_seq(rows):
    """The reader's FULL prose render (getEnglishOrderWords,
    56-library-order-logic.jsx): within a bracket group, strip trailing
    clause punctuation from every member (position order), reorder by
    greek_pos ascending (missing -> end), then re-attach the collected
    punctuation to the display-last English-carrying chip. Non-bracket words
    keep position order. Modeling the reorder WITHOUT the punctuation float
    manufactured a phantom 626-member class — the float is part of the
    render."""
    out, i, n = [], 0, len(rows)
    while i < n:
        pos, eng, _sb, bid, _gp = rows[i]
        if bid is None:
            if eng:
                out.append(eng)
            i += 1
            continue
        j = i
        group = []
        while j < n and rows[j][3] == bid:
            group.append(rows[j])
            j += 1
        trailing = ""
        cleaned = []
        for r in group:
            e = (r[1] or "").strip()
            if e and TRAIL_RE.sub("", e) == "":
                trailing += e
                continue
            m = TRAIL_RE.search(e)
            if m:
                trailing += m.group()
                e = e[:m.start()].rstrip()
            cleaned.append((r[0], e, r[2], r[3], r[4]))
        cleaned.sort(key=lambda r: r[4] if r[4] is not None else 999)
        if trailing and cleaned:
            li = len(cleaned) - 1
            while li > 0 and not (cleaned[li][1] or "").strip():
                li -= 1
            cleaned[li] = cleaned[li][:1] + ((cleaned[li][1] or "") + trailing,) \
                + cleaned[li][2:]
        out.extend(r[1] for r in cleaned if r[1])
        i = j
    return out


def main():
    live, ride = sys.argv[1], sys.argv[2]
    lc = sqlite3.connect("file:%s?mode=ro" % live, uri=True)
    rc = sqlite3.connect("file:%s?mode=ro" % ride, uri=True)

    skips = []
    for key, entries in FIXES.items():
        book, rest = key.split(" ", 1)
        ch, vs = (int(x) for x in rest.split(":"))
        rows = {r[0]: (r[1] or "") for r in verse_rows(rc, book, ch, vs)}
        applied = all(
            (en.get("new_eng") or "") == rows.get(en["new_pos"], "\0")
            for en in entries)
        if not applied:
            skips.append((book, ch, vs, entries))

    print(f"skipped verses: {len(skips)} of {len(FIXES)}")
    same = diff = 0
    for book, ch, vs, entries in skips:
        lrows = verse_rows(lc, book, ch, vs)
        rrows = verse_rows(rc, book, ch, vs)
        lseq, rseq = display_seq(lrows), display_seq(rrows)
        # verdict on the RENDERED STRING — live may carve the same words into
        # different cells (Mat 1:2), which is not a display difference
        lseq, rseq = " ".join(lseq).split(), " ".join(rseq).split()
        verdict = "DISPLAY-EQUAL" if lseq == rseq else "DISPLAY-DIFFERS"
        if lseq == rseq:
            same += 1
        else:
            diff += 1
        print(f"\n== {book} {ch}:{vs}  {verdict}")
        if lseq != rseq:
            print(f"  LIVE renders: {' '.join(lseq)}")
            print(f"  RIDE renders: {' '.join(rseq)}")
            print(f"  RIDE cells: " + " · ".join(
                f"{p}:{e!r}(b{b},g{g})" for p, e, _s, b, g in rrows if e))
    print(f"\nverdicts: DISPLAY-EQUAL {same} · DISPLAY-DIFFERS {diff}")


if __name__ == "__main__":
    main()
