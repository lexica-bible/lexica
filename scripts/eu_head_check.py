#!/usr/bin/env python3
"""eu_head_check.py - edition upgrade step 4, the HEAD-CONSISTENCY CHECK (DESIGN 9.144 (5) / 9.145 (2)).
READ-ONLY on both databases (mode=ro + query_only); writes only into --out, which must exist and be empty.

  python3 scripts/eu_head_check.py --a <src.db> --b <built.db> --out <empty folder> [--show "Isa 48:5@4"]...

english_head is not a pure function of english (DESIGN 9.145 (1)). This check recomputes only the BASE
rule the build applies to every row, with the build's own function (parse_abp._head_word), in the
build's order:
  1. head = _head_word(english)                                  (english empty -> None)
  2. italic re-pick, as _strip_italic_heads: if english has a space and italic_words names words,
     head = _head_word(english, {those words, lower-cased})
  3. name re-pick, as _star_name_heads (last in the verse pass): if strongs == '*' and english has a
     space, head = _head_word(english, prefer_name=True) when that is not empty
  4. the italic re-clean the full build runs after writing the rows (fix_italic_heads.run,
     build_words_from_abp.py :2784-2790): on EVERY row with a space and italic_words, head =
     _head_word(english, italic set) when that is not empty - so on a star row with italics the
     italic pick wins (reviewer finding, 11/15)
For each copy every row whose STORED english_head differs from this recomputed head is listed. Rows that
the build's other passes set by their own rules (function-word relocation, oath heads, merge pairs / edge
splits keeping the OLD head, EU head corrections) show up as mismatches on BOTH copies; they are not
candidates.

STALE-HEAD CANDIDATE: a (book, chapter, verse, position) that mismatches on --b (built) and NOT on --a
(src), with english, italic_words and strongs equal on both copies.
LIMIT (recorded, DESIGN 9.145 (2)): a row whose english, italic_words or strongs differs between the
copies cannot be judged here - it is counted as "built-only, inputs differ" and answered elsewhere
(the A english_head output + the EU head rows). A candidate is a candidate, read by member.

OUTPUT (--out): mismatch_a.tsv, mismatch_b.tsv (every mismatching row of each copy), candidates.tsv,
both_differ.tsv (rows mismatching on BOTH copies whose two stored heads differ - also outside this
check, listed so they are seen), summary.txt; values with repr(); counts and each file's sha256 printed. --show prints the full detail
of named rows (the two known cases are the block's control). Exit 0 = ran; 1 = STOP.
"""
import argparse
import hashlib
import os
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from parse_abp import _head_word  # noqa: E402  (the build imports the same function)


class Stop(Exception):
    pass


def ro(path):
    if not (os.path.isfile(path) and os.path.getsize(path) > 0):
        raise Stop("missing or empty: %s" % path)
    c = sqlite3.connect("%s?mode=ro" % Path(path).resolve().as_uri(), uri=True)
    c.text_factory = lambda b: b.decode("utf-8", "surrogateescape")
    c.execute("PRAGMA query_only=1")
    return c


def recompute(english, italic_words, strongs):
    """The base rule, in the full build's order (see the module text)."""
    head = _head_word(english) if english else None
    italic_set = set()
    if english and " " in english and italic_words:
        italic_set = {w.strip().lower() for w in italic_words.split(",") if w.strip()}
        if italic_set:                                     # _strip_italic_heads (in the verse pass)
            head = _head_word(english, italic_set)
    if strongs == "*" and english and " " in english:     # _star_name_heads (last in the verse pass)
        named = _head_word(english, prefer_name=True)
        if named:
            head = named
    if italic_set:                                         # fix_italic_heads re-clean after the build
        again = _head_word(english, italic_set)            # (build_words_from_abp.py :2784-2790;
        if again:                                          #  fix_italic_heads.py :44-73: every row,
            head = again                                   #  only when the pick is not empty)
    return head


def load(c):
    """{(book, ch, v, pos): (english, english_head, italic_words, strongs)}"""
    have = {r[1] for r in c.execute("PRAGMA table_info(words)")}
    for need in ("verse_id", "position", "english", "english_head", "italic_words", "strongs"):
        if need not in have:
            raise Stop("words has no %s column" % need)
    out = {}
    for b, ch, v, pos, e, h, iw, s in c.execute(
            "SELECT v.book, v.chapter, v.verse, w.position, w.english, w.english_head, w.italic_words, w.strongs "
            "FROM words w JOIN verses v ON v.id = w.verse_id"):
        k = (b, ch, v, pos)
        if k in out:
            raise Stop("word %s %s:%s position %s appears twice" % k)
        out[k] = (e, h, iw, s)
    n = c.execute("SELECT count(*) FROM words").fetchone()[0]
    if n != len(out):
        raise Stop("%d word rows, %d joined to a verse - a word with no verse row" % (n, len(out)))
    return out


def parse_show(s):
    m = re.fullmatch(r"\s*(\S+)\s+(\d+):(\d+)\s*@\s*(\d+)\s*", s)
    if not m:
        raise Stop("--show wants 'Book C:V@P', got %r" % s)
    return (m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)))


def run(a_path, b_path, out, show=()):
    out = Path(out)
    if not out.is_dir():
        raise Stop("--out must be an existing folder: %s" % out)
    if any(out.iterdir()):
        raise Stop("--out must be empty: %s" % out)
    if Path(a_path).resolve() == Path(b_path).resolve():
        raise Stop("--a and --b are the same file")
    shows = [parse_show(s) for s in show]
    ca, cb = ro(a_path), ro(b_path)
    A, B = load(ca), load(cb)
    ca.close()
    cb.close()
    say = []

    def p(msg=""):
        print(msg)
        say.append(msg)

    p("eu_head_check - READ-ONLY on both databases; writes only %s" % out)
    p("  a (src):   %s - %d word rows" % (a_path, len(A)))
    p("  b (built): %s - %d word rows" % (b_path, len(B)))
    mis = {}
    for name, rows in (("a", A), ("b", B)):
        m = {}
        for k, (e, h, iw, s) in rows.items():
            r = recompute(e, iw, s)
            if r != h:
                m[k] = (e, h, iw, s, r)
        mis[name] = m
        with open(out / ("mismatch_%s.tsv" % name), "w", encoding="utf-8", errors="surrogateescape", newline="\n") as f:
            f.write("book\tchapter\tverse\tposition\tenglish\tstored_head\titalic_words\tstrongs\trecomputed\n")
            for k in sorted(m, key=lambda k: (str(k[0]), k[1], k[2], k[3])):
                f.write("\t".join([str(x) for x in k] + [repr(x) for x in m[k]]) + "\n")
    ma, mb = mis["a"], mis["b"]
    both = set(ma) & set(mb)
    both_differ = sorted((k for k in both if ma[k][1] != mb[k][1]), key=lambda k: (str(k[0]), k[1], k[2], k[3]))
    with open(out / "both_differ.tsv", "w", encoding="utf-8", errors="surrogateescape", newline="\n") as f:
        f.write("book\tchapter\tverse\tposition\tenglish_src\tstored_head_src\tenglish_built\tstored_head_built\t"
                "recomputed_src\trecomputed_built\n")
        for k in both_differ:
            f.write("\t".join([str(x) for x in k] + [repr(ma[k][0]), repr(ma[k][1]), repr(mb[k][0]), repr(mb[k][1]),
                                                     repr(ma[k][4]), repr(mb[k][4])]) + "\n")
    a_only = set(ma) - set(mb)
    b_only = set(mb) - set(ma)
    cands, differ = [], []
    for k in sorted(b_only, key=lambda k: (str(k[0]), k[1], k[2], k[3])):
        if k in A and A[k][0] == B[k][0] and A[k][2] == B[k][2] and A[k][3] == B[k][3]:
            cands.append(k)
        else:
            differ.append(k)
    with open(out / "candidates.tsv", "w", encoding="utf-8", errors="surrogateescape", newline="\n") as f:
        f.write("book\tchapter\tverse\tposition\tenglish\tstored_head_src\tstored_head_built\trecomputed\titalic_words\tstrongs\n")
        for k in cands:
            e, hb, iw, s, r = mb[k]
            f.write("\t".join([str(x) for x in k] + [repr(e), repr(A[k][1]), repr(hb), repr(r), repr(iw), repr(s)]) + "\n")
    p("")
    p("COUNTS (none is a gate)")
    p("  rows whose stored head differs from the base rule: src %d / built %d" % (len(ma), len(mb)))
    p("  mismatching on both copies   %d (of which the two stored heads differ: %d - both_differ.tsv;"
      " outside this check like the inputs-differ rows)" % (len(both), len(both_differ)))
    p("  on src only                  %d" % len(a_only))
    p("  on built only                %d = stale-head CANDIDATES %d + inputs differ %d (english / italic_words /"
      " strongs not equal - outside this check, DESIGN 9.145 (2))" % (len(b_only), len(cands), len(differ)))
    p("")
    for k in shows:
        def side(rows, m):
            if k not in rows:
                return "no such row"
            e, h, iw, s = rows[k]
            return "english %r - stored head %r - italic_words %r - strongs %r - recomputed %r - %s" % (
                e, h, iw, s, recompute(e, iw, s), "MISMATCH" if k in m else "matches")
        p("SHOW %s %s:%s@%s - candidate: %s" % (k + ("yes" if k in cands else "NO",)))
        p("  src:   " + side(A, ma))
        p("  built: " + side(B, mb))
    p("")
    for n in ("mismatch_a.tsv", "mismatch_b.tsv", "candidates.tsv", "both_differ.tsv"):
        data = (out / n).read_bytes()
        p("  %-16s %7d lines + header  sha256 %s" % (n, data.count(b"\n") - 1, hashlib.sha256(data).hexdigest()))
    p("RESULT: HEAD CHECK WRITTEN - no database was written")
    with open(out / "summary.txt", "w", encoding="utf-8", errors="surrogateescape", newline="\n") as f:
        f.write("\n".join(say) + "\n")
    return cands


def main(argv=None):
    ap = argparse.ArgumentParser(description="Step-4 head-consistency check (read-only).")
    ap.add_argument("--a", required=True, help="src")
    ap.add_argument("--b", required=True, help="built")
    ap.add_argument("--out", required=True, help="an existing EMPTY folder")
    ap.add_argument("--show", action="append", default=[], help="'Book C:V@P' - print that row's detail")
    a = ap.parse_args(argv)
    try:
        run(a.a, a.b, a.out, a.show)
    except (Stop, sqlite3.Error, OSError) as e:
        print("STOPPED: %s%s" % ("" if isinstance(e, Stop) else type(e).__name__ + ": ", e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
