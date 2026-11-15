#!/usr/bin/env python3
"""eu_words_delta.py - edition upgrade step 4, the RAW DELTA (DESIGN 9.138 (2), 9.139): every difference
between two copies' `words` and `verses` tables, written IN FULL to files, with counts per column.
No gate: it reports, it does not judge. READ-ONLY on both databases (opened mode=ro; it never writes a
database it reads). Writes only into --out, which must exist and be empty.

  python3 scripts/eu_words_delta.py --a <src.db> --b <built.db> --out <empty folder>

KEYS. A verse is (book, chapter, verse). A word is (book, chapter, verse, position) - the verse row's id
and the word row's id are NOT compared (they differ between independent builds). Every other column of
`words` that both copies have is compared, value for value (sqlite values, so 1 and '1' differ).
bracket_id is compared as a per-verse RANK (the order a bracket first appears in the verse, by position;
None outside a bracket) - the same normalisation as compare_words.py - because the raw number is an
internal counter; a real grouping change still shows as a rank change. Every `verses` column but `id`
is compared per verse.

MOVED WORDS - the pairing rule (DESIGN 9.138 condition: stated here and in the record; never forced):
  A word's IDENTITY is (strongs, morph, lemma) - the key of the 11/6 STRONGS-POS census v2.
  In one verse, the a-side CANDIDATES are the positions that exist only on a, or whose identity differs
  from b's at the same position; the b-side candidates likewise. An a-candidate p and a b-candidate q
  (q != p) are a MOVED PAIR only when the identity at a:p equals the identity at b:q AND no other
  candidate on either side carries that identity in that verse (unique both ways). Every candidate left
  over is UNPAIRED and listed as such (side, position, identity) - never guessed into a pair.
  A pair is a reading aid: its positions still appear in words_cells.tsv / words_only.tsv as they are.

OUTPUT (--out), each TSV with a header; values written with repr() so None, '' and tabs stay exact:
  words_cells.tsv     book chapter verse position column a b moved   (same key, a column differs)
  words_only.tsv      side book chapter verse position row           (the word key exists on one side)
  words_moved.tsv     book chapter verse a_position b_position identity other_columns_differing
  words_unpaired.tsv  side book chapter verse position identity
  verses_cells.tsv    book chapter verse column a b
  verses_only.tsv     side book chapter verse row
  summary.txt         the printed summary
Each file's sha256 is printed. Exit 0 = ran (differences or not); 1 = STOP (bad input, nothing judged).
"""
import argparse
import hashlib
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

IDENTITY = ("strongs", "morph", "lemma")


class Stop(Exception):
    pass


def ro(path):
    if not (os.path.isfile(path) and os.path.getsize(path) > 0):
        raise Stop("missing or empty: %s" % path)
    c = sqlite3.connect("%s?mode=ro" % Path(path).resolve().as_uri(), uri=True)   # as_uri escapes ? # %
    c.text_factory = lambda b: b.decode("utf-8", "surrogateescape")
    c.execute("PRAGMA query_only=1")
    return c


def cols(c, t):
    return [r[1] for r in c.execute("PRAGMA table_info(%s)" % t)]


def load_verses(c, vcols):
    out, ids = {}, {}
    sel = ", ".join(vcols)
    for row in c.execute("SELECT id, book, chapter, verse%s FROM verses" % ((", " + sel) if sel else "")):
        k = (row[1], row[2], row[3])
        if k in out:
            raise Stop("verse %s %s:%s appears twice" % k)
        out[k] = row[4:]
        ids[row[0]] = k
    return out, ids


def load_words(c, ids, wcols):
    """{(book, ch, v): {pos: tuple of the wcols values}}, bracket_id as a per-verse rank. One
    structure per side (no second copy), to keep memory down on PA."""
    out = defaultdict(dict)
    sel = ", ".join(wcols)
    bi = wcols.index("bracket_id") if "bracket_id" in wcols else None
    rows = c.execute("SELECT verse_id, position, %s FROM words ORDER BY verse_id, position" % sel)
    rank, last = {}, None
    for row in rows:
        vid, pos = row[0], row[1]
        if vid not in ids:
            raise Stop("a word row names verse_id %s, which has no verses row" % vid)
        if vid != last:
            rank, last = {}, vid
        vals = list(row[2:])
        if bi is not None and vals[bi] is not None:
            vals[bi] = rank.setdefault(vals[bi], len(rank) + 1)
        vk = ids[vid]
        if pos in out[vk]:
            raise Stop("word %s %s:%s position %s appears twice" % (vk + (pos,)))
        out[vk][pos] = tuple(vals)
    return out


IX = ()          # where IDENTITY's columns sit inside a row tuple; set by run()


def ident(row):
    return tuple(row[i] for i in IX)


def pair_moves(va, vb):
    """va / vb: {position: row dict} of one verse. -> (pairs [(p, q)], unpaired_a, unpaired_b)."""
    ca = [p for p in va if p not in vb or ident(va[p]) != ident(vb[p])]
    cb = [q for q in vb if q not in va or ident(vb[q]) != ident(va[q])]
    by_a, by_b = defaultdict(list), defaultdict(list)
    for p in ca:
        by_a[ident(va[p])].append(p)
    for q in cb:
        by_b[ident(vb[q])].append(q)
    pairs, used_a, used_b = [], set(), set()
    for i, ps in by_a.items():
        qs = by_b.get(i, [])
        if len(ps) == 1 and len(qs) == 1 and ps[0] != qs[0]:
            pairs.append((ps[0], qs[0]))
            used_a.add(ps[0])
            used_b.add(qs[0])
    return (sorted(pairs), sorted(p for p in ca if p not in used_a), sorted(q for q in cb if q not in used_b))


def writer(path, header):
    f = open(path, "w", encoding="utf-8", errors="surrogateescape", newline="\n")
    f.write("\t".join(header) + "\n")
    return f


def tsv(f, keyvals, vals):
    """key fields written plainly (book, ints), value fields with repr()."""
    f.write("\t".join([str(x) for x in keyvals] + [repr(v) for v in vals]) + "\n")


def run(a_path, b_path, out):
    out = Path(out)
    if not out.is_dir():
        raise Stop("--out must be an existing folder: %s" % out)
    if any(out.iterdir()):
        raise Stop("--out must be empty: %s" % out)
    if Path(a_path).resolve() == Path(b_path).resolve():
        raise Stop("--a and --b are the same file")
    ca, cb = ro(a_path), ro(b_path)
    say = []

    def p(msg=""):
        print(msg)
        say.append(msg)

    p("eu_words_delta - READ-ONLY on both databases; writes only %s" % out)
    p("  a: %s (%d bytes)" % (a_path, os.path.getsize(a_path)))
    p("  b: %s (%d bytes)" % (b_path, os.path.getsize(b_path)))
    # columns
    wa, wb = cols(ca, "words"), cols(cb, "words")
    va_cols, vb_cols = cols(ca, "verses"), cols(cb, "verses")
    for need in ("verse_id", "position"):
        if need not in wa or need not in wb:
            raise Stop("words has no %s column on one side" % need)
    for need in ("id", "book", "chapter", "verse"):
        if need not in va_cols or need not in vb_cols:
            raise Stop("verses has no %s column on one side" % need)
    wcols = [x for x in wa if x in wb and x not in ("id", "verse_id", "position")]
    vcols = [x for x in va_cols if x in vb_cols and x not in ("id", "book", "chapter", "verse")]
    p("words columns compared (%d): %s" % (len(wcols), ", ".join(wcols)))
    p("words columns on one side only: a %s - b %s" % (sorted(set(wa) - set(wb)) or "none",
                                                       sorted(set(wb) - set(wa)) or "none"))
    p("verses columns compared (%d): %s" % (len(vcols), ", ".join(vcols)))
    p("verses columns on one side only: a %s - b %s" % (sorted(set(va_cols) - set(vb_cols)) or "none",
                                                        sorted(set(vb_cols) - set(va_cols)) or "none"))
    missing = [x for x in IDENTITY if x not in wcols]
    if missing:
        raise Stop("the pairing identity needs words column(s) %s on both sides" % missing)
    global IX
    IX = tuple(wcols.index(x) for x in IDENTITY)
    # verses
    vA, idsA = load_verses(ca, vcols)
    vB, idsB = load_verses(cb, vcols)
    byA = load_words(ca, idsA, wcols)
    byB = load_words(cb, idsB, wcols)
    ca.close()
    cb.close()
    p("rows: verses a %d / b %d - words a %d / b %d" % (len(vA), len(vB), sum(len(v) for v in byA.values()),
                                                       sum(len(v) for v in byB.values())))

    counts = Counter()
    f_vc = writer(out / "verses_cells.tsv", ["book", "chapter", "verse", "column", "a", "b"])
    f_vo = writer(out / "verses_only.tsv", ["side", "book", "chapter", "verse", "row"])
    for k in sorted(set(vA) | set(vB), key=lambda k: (str(k[0]), k[1], k[2])):
        if k not in vB:
            tsv(f_vo, ("a",) + k, [dict(zip(vcols, vA[k]))])
            counts["verses only a"] += 1
        elif k not in vA:
            tsv(f_vo, ("b",) + k, [dict(zip(vcols, vB[k]))])
            counts["verses only b"] += 1
        else:
            for col, x, y in zip(vcols, vA[k], vB[k]):
                if x != y or type(x) is not type(y):
                    tsv(f_vc, k + (col,), [x, y])
                    counts["verses." + col] += 1
    f_vc.close()
    f_vo.close()

    # words, verse by verse
    f_wc = writer(out / "words_cells.tsv", ["book", "chapter", "verse", "position", "column", "a", "b", "moved"])
    f_wo = writer(out / "words_only.tsv", ["side", "book", "chapter", "verse", "position", "row"])
    f_wm = writer(out / "words_moved.tsv", ["book", "chapter", "verse", "a_position", "b_position", "identity",
                                            "other_columns_differing"])
    f_wu = writer(out / "words_unpaired.tsv", ["side", "book", "chapter", "verse", "position", "identity"])
    moved_verses = set()
    for vk in sorted(set(byA) | set(byB), key=lambda k: (str(k[0]), k[1], k[2])):
        va, vb = byA.get(vk, {}), byB.get(vk, {})
        pairs, ua, ub = pair_moves(va, vb)
        in_pair = {x for x, _ in pairs} | {y for _, y in pairs}
        for pa, pb in pairs:
            other = [c for i, c in enumerate(wcols) if c not in IDENTITY and va[pa][i] != vb[pb][i]]
            tsv(f_wm, vk + (pa, pb), [ident(va[pa]), ",".join(other)])
            counts["moved pairs"] += 1
            moved_verses.add(vk)
        for q in ua:
            tsv(f_wu, ("a",) + vk + (q,), [ident(va[q])])
            counts["unpaired a"] += 1
        for q in ub:
            tsv(f_wu, ("b",) + vk + (q,), [ident(vb[q])])
            counts["unpaired b"] += 1
        for pos in sorted(set(va) | set(vb)):
            if pos not in vb:
                tsv(f_wo, ("a",) + vk + (pos,), [dict(zip(wcols, va[pos]))])
                counts["words only a"] += 1
            elif pos not in va:
                tsv(f_wo, ("b",) + vk + (pos,), [dict(zip(wcols, vb[pos]))])
                counts["words only b"] += 1
            else:
                for col, x, y in zip(wcols, va[pos], vb[pos]):
                    if x != y or type(x) is not type(y):
                        f_wc.write("\t".join([str(vk[0]), str(vk[1]), str(vk[2]), str(pos), col, repr(x), repr(y),
                                              "yes" if pos in in_pair else "no"]) + "\n")
                        counts["words." + col] += 1
    for f in (f_wc, f_wo, f_wm, f_wu):
        f.close()
    counts["moved verses"] = len(moved_verses)

    p("")
    p("COUNTS (every member is in the files below)")
    for col in wcols:
        p("  words.%-22s %d" % (col, counts["words." + col]))
    p("  words only a / only b       %d / %d" % (counts["words only a"], counts["words only b"]))
    p("  moved pairs                 %d (in %d verses) - unpaired a %d / b %d"
      % (counts["moved pairs"], counts["moved verses"], counts["unpaired a"], counts["unpaired b"]))
    for col in vcols:
        p("  verses.%-21s %d" % (col, counts["verses." + col]))
    p("  verses only a / only b      %d / %d" % (counts["verses only a"], counts["verses only b"]))
    p("")
    names = ["words_cells.tsv", "words_only.tsv", "words_moved.tsv", "words_unpaired.tsv",
             "verses_cells.tsv", "verses_only.tsv"]
    for n in names:
        data = (out / n).read_bytes()
        p("  %-20s %8d lines + header  sha256 %s" % (n, data.count(b"\n") - 1, hashlib.sha256(data).hexdigest()))
    try:
        import resource                                   # Linux (PA); absent on Windows
        p("  peak memory (max resident) %d MB" % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024))
    except ImportError:
        p("  peak memory: not measured on this system")
    p("RESULT: DELTA WRITTEN - no database was written")
    with open(out / "summary.txt", "w", encoding="utf-8", errors="surrogateescape", newline="\n") as f:
        f.write("\n".join(say) + "\n")
    return counts


def main(argv=None):
    ap = argparse.ArgumentParser(description="Step-4 raw delta between two copies (read-only).")
    ap.add_argument("--a", required=True, help="the before copy (src)")
    ap.add_argument("--b", required=True, help="the after copy (built)")
    ap.add_argument("--out", required=True, help="an existing EMPTY folder")
    a = ap.parse_args(argv)
    try:
        run(a.a, a.b, a.out)
    except (Stop, sqlite3.Error, OSError) as e:
        print("STOPPED: %s%s" % ("" if isinstance(e, Stop) else type(e).__name__ + ": ", e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
