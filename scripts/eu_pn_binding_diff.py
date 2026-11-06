#!/usr/bin/env python3
"""eu_pn_binding_diff.py - edition upgrade, gate 2 companion dump (DESIGN sec 9.92 G1).
READ-ONLY on both files.

Lists EVERY pn_binding row that differs between <src> and <built> (no cap - the
gate itself prints at most 20 problems), keyed on the gate's tight key
(book NUMBER, chapter, verse, name). For each row: both copies' values, and the
word slots that row binds on each copy (the binder's own selection: is_pn rows
in that verse whose norm_name(label) == name, build_entity_binding.py:140-166)
with strongs AND strongs_base, and a key column H / G read from the
strongs_base prefix (words.strongs is bare by design; strongs_base carries the
prefix). Sorted by (book, chapter, verse, name).

Status per row: CHANGED (both copies, values differ) / ONLY-SRC / ONLY-BUILT.

Usage: python3 scripts/eu_pn_binding_diff.py <src.db> <built.db>
Exit: 0 = read done (the rows are for ruling, not a pass/fail) / 2 = STOP.
"""
import os
import sqlite3
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
import entity_resolution as er   # norm_name + book_num: the binder's own helpers

COLS = ("book", "chapter", "verse", "name", "entity_uniq", "kind", "rule",
        "render", "hot", "tier")
VALS = COLS[4:]


def stop(msg):
    print("PN-BINDING DIFF: STOP - " + msg)
    sys.exit(2)


def ro(path):
    if not os.path.isfile(path):
        stop("missing: " + path)
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def bindings(conn):
    return {r[:4]: r for r in conn.execute(f"SELECT {','.join(COLS)} FROM pn_binding")}


def verse_index(conn):
    """(book NUMBER, chapter, verse) -> (verse_id, book abbrev)."""
    out = {}
    for vid, bk, ch, vs in conn.execute("SELECT id, book, chapter, verse FROM verses"):
        n = er.book_num(bk)
        if n is not None:
            out[(n, ch, vs)] = (vid, bk)
    return out


def slot_reader(conn):
    has_pn = "is_pn" in {r[1] for r in conn.execute("PRAGMA table_info(words)")}
    pn_where = "is_pn = 1" if has_pn else "strongs_base = '*'"
    q = ("SELECT position, COALESCE(NULLIF(english_head,''), english), strongs, strongs_base "
         f"FROM words WHERE verse_id = ? AND {pn_where} ORDER BY position")

    def slots(vid, name):
        if vid is None:
            return []
        return [(pos, s, sb) for pos, lbl, s, sb in conn.execute(q, (vid,))
                if er.norm_name(lbl or "") == name]
    return slots


def key_of(sb):
    sb = (sb or "").strip()
    if sb[:1] in ("H", "G"):
        return sb[:1]
    return sb if sb else "-"


def fmt_slots(sl):
    if not sl:
        return "(no slot)", "-"
    txt = "; ".join(f"pos {p} strongs={s!r} strongs_base={sb!r} key={key_of(sb)}"
                    for p, s, sb in sl)
    keys = "+".join(sorted({key_of(sb) for _p, _s, sb in sl}))
    return txt, keys


def fmt_row(r):
    if r is None:
        return "(no row)"
    return " ".join(f"{c}={v!r}" for c, v in zip(VALS, r[4:]))


def main():
    if len(sys.argv) != 3:
        stop("usage: eu_pn_binding_diff.py <src.db> <built.db>")
    src_p, blt_p = sys.argv[1], sys.argv[2]
    if os.path.realpath(src_p) == os.path.realpath(blt_p):
        stop("src and built are the same file")
    src, blt = ro(src_p), ro(blt_p)
    print(f"PN-BINDING DIFF (read-only): src {src_p} vs built {blt_p}")
    sb, bb = bindings(src), bindings(blt)
    print(f"pn_binding rows: src {len(sb):,} - built {len(bb):,}")
    sv, bv = verse_index(src), verse_index(blt)
    s_slots, b_slots = slot_reader(src), slot_reader(blt)

    diff = sorted(k for k in set(sb) | set(bb) if sb.get(k) != bb.get(k))
    counts = {"CHANGED": 0, "ONLY-SRC": 0, "ONLY-BUILT": 0}
    for k in diff:
        bk, ch, vs, name = k
        rs, rb = sb.get(k), bb.get(k)
        status = "CHANGED" if rs and rb else ("ONLY-SRC" if rs else "ONLY-BUILT")
        counts[status] += 1
        vid_s, abbr = sv.get((bk, ch, vs), (None, None))
        vid_b, abbr_b = bv.get((bk, ch, vs), (None, None))
        abbr = abbr or abbr_b or "?"
        sl_s, key_s = fmt_slots(s_slots(vid_s, name))
        sl_b, key_b = fmt_slots(b_slots(vid_b, name))
        cols = [c for c in VALS if rs and rb and rs[COLS.index(c)] != rb[COLS.index(c)]]
        print(f"\n{status}  {abbr} {ch}:{vs} [book {bk}] name={name!r}"
              f"  key src {key_s} / built {key_b}"
              + (f"  cols changed: {', '.join(cols)}" if cols else ""))
        print(f"   src  : {fmt_row(rs)}")
        print(f"   built: {fmt_row(rb)}")
        print(f"   slots src  : {sl_s}")
        print(f"   slots built: {sl_b}")
    print()
    print(f"PN-BINDING DIFF: READ - differing {len(diff)} - changed {counts['CHANGED']} - "
          f"only-src {counts['ONLY-SRC']} - only-built {counts['ONLY-BUILT']}")


if __name__ == "__main__":
    main()
