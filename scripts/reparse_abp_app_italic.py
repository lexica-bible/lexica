#!/usr/bin/env python3
"""
reparse_abp_app_italic.py — add the translator-addition (italic) flag to the ABP app
slot TSV by RE-PARSING THE CACHED PAGES. NO NETWORK. READ-ONLY toward every database
(it opens none). Edition-upgrade charter §0.6 Q3 (JP ruling 2026-10-30: "re-parse cached
HTML on PA for the <i> flag, add an italic column to the TSV before 0b; no refetch").

WHAT IT DOES
  Reads every cached chapter page under abp_app_html/ ("<Book> <n>.html", written by
  fetch_abp_app.py on 2026-10-24), runs the SAME parser (fetch_abp_app.ChapterParser,
  subclassed only to notice <i>…</i> inside the English cell .e), and writes a NEW TSV
  with the original seven columns plus two:
      italic        1 if any part of the English cell was inside <i>…</i>, else 0
      italic_words  the italic text itself, verbatim (e.g. "the", "was"); '' when 0
  The English column is produced exactly as before (<i> tags were already transparent
  to the fetch parser), so the first seven columns are IDENTICAL to the 10/24 TSV.

SELF-CHECK (the script refuses to write unless all pass):
  1. every (book, chapter, verse, slot_index) in the 10/24 TSV is re-parsed, with the
     same strongs / greek / english bytes, and nothing extra — a page missing from the
     cache or a parser drift = exit non-zero, no output file.
  2. controls, read from the cached pages themselves (checked 2026-10-30 in the local
     copies of the same pages):
       Gen 25:1  "was Keturah."   -> italic=1, italic_words="was"
       Gen 25:3  "the Asshurim,"  -> italic=1, italic_words="the"
       Psa 3     at least one "<i>to</i>" slot (the dative articles) -> italic=1
       Gen 25:15 the "Hadar," slot (Latin-C control of the fetch) -> italic=0
  3. the italic flag never appears on a slot whose English is empty.
  4. every cached page's own <title> equals its file name (a stale spell-corrected page = STOP).

Usage (on PA, from ~/bible-db):
  python3 scripts/reparse_abp_app_italic.py \
      --tsv abp_app_html/abp_app_slots.tsv \
      --out abp_app_html/abp_app_slots_italic.tsv
Prints: pages read, slots, italic slots (count + % + per-testament), control results,
and the self-check verdict. Writes ONLY --out (and refuses to overwrite it).
"""
import argparse
import csv
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from fetch_abp_app import CACHE, ChapterParser, REF_RE, clean   # the ONE parser

PAGE_RE = re.compile(r"^(.*\S) (\d+)\.html$")

# Output order = the app's own book order (chapters.js), read from the cache's copy of it.
def _book_order():
    try:
        with open(os.path.join(CACHE, "chapters.js"), encoding="utf-8") as f:
            names = re.findall(r"\['[^']*',\s*'([^']*)',\s*\d+\]", f.read())
        return {n: i for i, n in enumerate(names)}
    except OSError:
        return {}


BOOK_ORDER = _book_order()


class ItalicParser(ChapterParser):
    """Same slots as ChapterParser; additionally records the <i> text inside .e."""

    def __init__(self):
        super().__init__()
        self.i_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "i" and self.cell is not None and self.field == "e":
            self.i_depth += 1
            self.cell.setdefault("i", []).append("")
            return
        super().handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "i" and self.i_depth:
            self.i_depth -= 1
            return
        super().handle_endtag(tag)

    def handle_data(self, data):
        if self.i_depth and self.cell is not None and self.field == "e":
            self.cell["i"][-1] += data
        super().handle_data(data)

    def _close_cell(self):
        # Capture the italic pieces BEFORE the parent consumes the cell.
        ital = list(self.cell.get("i", [])) if self.cell is not None else []
        before = len(self.row[1]) if self.row is not None else 0
        super()._close_cell()
        if self.row is not None and len(self.row[1]) == before + 1:
            s, g, e, n = self.row[1][-1]
            self.row[1][-1] = (s, g, e, n, [clean(x) for x in ital if clean(x)])
        self.i_depth = 0


def page_title(body):
    m = re.search(rb"<title>([^<]*)</title>", body)
    return m.group(1).decode("utf-8", "replace").strip() if m else ""


def parse_cached_page(book, ch, path):
    with open(path, "rb") as f:
        body = f.read()
    # A cached file whose own <title> is not "<Book> <n>" is NOT that chapter (2026-10-30: four
    # stale Genesis 52-55 files held Genesis 25/35/45/5 — spell-corrected pages cached by an early
    # test fetch before the title check existed). Such a file is a STOP, never parsed into rows.
    if page_title(body) != f"{book} {ch}":
        raise SystemExit(f"STOP: cached {os.path.basename(path)} has title {page_title(body)!r} — "
                         f"not this chapter; move the stale file aside and re-run")
    p = ItalicParser()
    p.feed(body.decode("utf-8-sig"))
    p.close()
    rows = []
    for ref, slots in p.verses:
        m = REF_RE.search(ref)
        if not m:
            continue
        vs = int(m.group(2))
        for i, slot in enumerate(slots):
            sparts, g, e, _n = slot[:4]
            ital = slot[4] if len(slot) > 4 else []
            rows.append((book, int(m.group(1)), vs, i, "-".join(sparts), clean(g), clean(e),
                         1 if ital else 0, " ".join(ital)))
    return rows, p.anomalies


def main():
    ap = argparse.ArgumentParser(description="Add the italic column to the app slot TSV from cached pages.")
    ap.add_argument("--tsv", default=os.path.join(CACHE, "abp_app_slots.tsv"),
                    help="the 2026-10-24 slot TSV to match against (never written)")
    ap.add_argument("--out", default=os.path.join(CACHE, "abp_app_slots_italic.tsv"))
    ap.add_argument("--cache", default=CACHE, help="folder of cached '<Book> <n>.html' pages")
    args = ap.parse_args()
    if os.path.exists(args.out):
        sys.exit(f"refusing to overwrite {args.out} — move it aside first")

    # 1. the 10/24 TSV, keyed
    old = {}
    with open(args.tsv, encoding="utf-8", newline="") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            k = (row["book"], int(row["chapter"]), int(row["verse"]), int(row["slot_index"]))
            old[k] = (row["strongs"], row["greek"], row["english"])
    print(f"10/24 TSV: {len(old):,} slots")

    # 2. re-parse every cached page
    new, pages, anomalies = {}, 0, []
    for fn in sorted(os.listdir(args.cache)):
        m = PAGE_RE.match(fn)
        if not m:
            continue
        book, ch = m.group(1), int(m.group(2))
        rows, an = parse_cached_page(book, ch, os.path.join(args.cache, fn))
        anomalies.extend(f"{book} {ch}: {a}" for a in an)
        pages += 1
        for b, c, v, i, s, g, e, fl, iw in rows:
            new[(b, c, v, i)] = (s, g, e, fl, iw)
    print(f"cached pages re-parsed: {pages:,} · slots: {len(new):,} · parser anomalies: {len(anomalies)}")
    for a in anomalies[:10]:
        print("   anomaly:", a)

    # 3. self-check 1 — same keys, same seven columns
    problems = []
    missing = sorted(set(old) - set(new))
    extra = sorted(set(new) - set(old))
    if missing:
        problems.append(f"{len(missing)} slots of the 10/24 TSV not re-parsed (first: {missing[0]})")
    if extra:
        problems.append(f"{len(extra)} re-parsed slots not in the 10/24 TSV (first: {extra[0]})")
    drift = [k for k in old if k in new and old[k] != new[k][:3]]
    if drift:
        k = drift[0]
        problems.append(f"{len(drift)} slots differ in strongs/greek/english (first {k}: "
                        f"old={old[k]} new={new[k][:3]})")

    # 4. self-check 2 — controls
    def ctl(name, key, want_flag, want_words=None):
        got = new.get(key)
        ok = got is not None and got[3] == want_flag and (want_words is None or got[4] == want_words)
        print(f"control {name}: {'PASS' if ok else 'FAIL'} — {got[2:] if got else 'slot missing'}")
        if not ok:
            problems.append(f"control {name} failed")

    def find(book, ch, vs, english_startswith):
        for (b, c, v, i), val in new.items():
            if b == book and c == ch and v == vs and val[2].startswith(english_startswith):
                return (b, c, v, i)
        return None

    ctl("Gen 25:1 'was Keturah.'", find("Genesis", 25, 1, "was Keturah"), 1, "was")
    ctl("Gen 25:3 'the Asshurim,'", find("Genesis", 25, 3, "the Asshurim"), 1, "the")
    ctl("Gen 25:15 'Hadar,' (Latin-C slot)", find("Genesis", 25, 15, "Hadar"), 0, "")
    psa3_to = [k for k, v in new.items() if k[0] == "Psalms" and k[1] == 3 and v[2].strip() == "to"]
    ok = bool(psa3_to) and all(new[k][3] == 1 and new[k][4] == "to" for k in psa3_to)
    print(f"control Psa 3 '<i>to</i>' slots: {'PASS' if ok else 'FAIL'} — {len(psa3_to)} slot(s)")
    if not ok:
        problems.append("control Psa 3 failed")

    # 5. self-check 3 — no flag on an empty English cell
    bad_empty = [k for k, v in new.items() if v[3] == 1 and not v[2].strip()]
    if bad_empty:
        problems.append(f"{len(bad_empty)} italic flags on EMPTY English cells (first: {bad_empty[0]})")

    # 6. report
    n_it = sum(1 for v in new.values() if v[3] == 1)
    print(f"\nitalic slots: {n_it:,} / {len(new):,} ({100.0 * n_it / max(1, len(new)):.2f}%)")
    if problems:
        print("\nSELF-CHECK FAILED — nothing written:")
        for p in problems:
            print("  -", p)
        sys.exit(1)

    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write("book\tchapter\tverse\tslot_index\tstrongs\tgreek\tenglish\titalic\titalic_words\n")
        for k in sorted(new, key=lambda k: (BOOK_ORDER.get(k[0], 99), k[1], k[2], k[3])):
            s, g, e, fl, iw = new[k]
            f.write("\t".join(str(x) for x in (*k, s, g, e, fl, iw)) + "\n")
    print(f"SELF-CHECK PASS — wrote {len(new):,} rows -> {args.out}")


if __name__ == "__main__":
    main()
