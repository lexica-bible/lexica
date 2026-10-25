#!/usr/bin/env python3
"""
fetch_abp_app.py — pull the official ABP app's chapter pages and flatten them to
one slot-per-row TSV. READ-ONLY toward every database (it never opens one).

WHY: apostolicbibleapp.com is the ABP's own app — a machine-readable copy of the
source we settle word-order / Strong's / name-slot questions against. Its Greek
is printed per word. This script makes that witness diffable; the companion
audit_abp_app_vs_surface.py diffs it against our tables (lane (a) of
docs/handoffs/HANDOFF_abp_source_material.md).

SOURCE LAYOUT (checked 2026-10-24 on Gen 25, 1Ki 11, Oba 1):
  /chapters.js           chaptersInBook = [['Gen','Genesis',50], ...]; the five
                         one-chapter books are listed with 0 — their page is
                         still "<Book> 1.html" (Oba 1 = 200, "Obadiah.html" = 404).
  /Chapters/<Book> <n>.html
      one <table class="tbl"> per verse, one <tr>; the first <td class="d"> holds
      <span class="verse">1 Ki 11:14</span>; every later <td class="d"> is one
      word slot with .s (Strong's; '*' for names), .g (Greek), .e (English).
      Compound slots come two ways — several <span class="s"> joined by a '-'
      text node, or ONE .s whose text already reads "590.2-*". Both come out
      dash-joined. .e may hold <i>…</i> (italic = translator addition) and ABP's
      bracket-order digits ("[3added", "1And") — kept verbatim here.

OUTPUT TSV columns (UTF-8, LF, header row):
  book  chapter  verse  slot_index  strongs  greek  english
  book = the app's own book name ("1 Kings"); slot_index = 0-based td order within
  the verse (the verse-label cell is not a slot). Text is verbatim apart from
  tabs/newlines folded to a space and outer whitespace trimmed (inner spacing,
  e.g. the double space in "έτεκε  δε", is kept).

CONTROLS (script exits non-zero if either misses — the parser is not trusted otherwise):
  Gen 25:15  the "Hadar," slot reads strongs='*', greek='Cολδάδ' with a LATIN C
             (U+0043) — the known source defect, must survive verbatim.
  1Ki 11:14  the "Hadad" slot reads greek='Αδάρ'.
Also non-zero on ANY failed chapter fetch (an incomplete TSV must not look complete).

COMPLETENESS PROBE: after each book's listed chapters, chapter N+1 is requested
and must 404; if it exists it is fetched and the probe walks on, and the count
gap is reported (chapters.js undercounts would otherwise drop text silently).

POLITENESS: one request at a time, >= --delay seconds apart (default 1.0), a
User-Agent naming lexica.bible. Raw pages are cached under abp_app_html/
(gitignored); a cached page is never re-requested unless --refresh.

Usage (on PA, from ~/bible-db; full run is ~1,200 pages ≈ 25 min):
  python3 scripts/fetch_abp_app.py
  # -> abp_app_html/*.html  +  abp_app_html/abp_app_slots.tsv
Test a few chapters only (controls are always included):
  python3 scripts/fetch_abp_app.py --only "Psalms 3" --only "Obadiah 1"
"""
import argparse
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from html.parser import HTMLParser

BASE = "https://www.apostolicbibleapp.com/"
UA = "lexica.bible ABP witness check (https://lexica.bible; 1 request/sec)"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "abp_app_html")

CONTROL_CHAPTERS = [("Genesis", 25), ("1 Kings", 11)]

_last_request = [0.0]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow a redirect. The server spell-corrects missing names: a request
    for "Genesis 51.html" is 301-redirected to "Genesis 15.html" (and "Genesis
    56.html" gets 300 Multiple Choices) — following it would file chapter 15 under
    51. A 3xx is returned as its status instead (2026-10-24 PA run)."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def http_get(path, delay):
    """GET BASE+path. Returns (status, bytes); any 3xx/4xx comes back as
    (status, b'') with no retry. Waits so two requests are never closer than
    `delay` seconds. Retries only server errors (5xx) and network failures."""
    url = BASE + urllib.parse.quote(path)
    for attempt, backoff in enumerate((0, 5, 15, 45)):
        if backoff:
            time.sleep(backoff)
        wait = delay - (time.time() - _last_request[0])
        if wait > 0:
            time.sleep(wait)
        _last_request[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with _OPENER.open(req, timeout=60) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code < 500:
                return e.code, b""
            err = f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            err = str(e)
        print(f"  ! {path}: {err} (attempt {attempt + 1})", file=sys.stderr)
    return None, b""


def load_book_list(delay, refresh):
    """[(abbrev, full_name, listed_chapters), ...] from chapters.js (cached)."""
    p = os.path.join(CACHE, "chapters.js")
    if refresh or not os.path.exists(p):
        st, body = http_get("chapters.js", delay)
        if st != 200:
            sys.exit(f"FATAL: chapters.js fetch failed ({st})")
        with open(p, "wb") as f:
            f.write(body)
    txt = open(p, encoding="utf-8-sig").read()
    m = re.search(r"chaptersInBook\s*=\s*\[(.*?)\]\s*;", txt, re.S)
    if not m:
        sys.exit("FATAL: chaptersInBook not found in chapters.js")
    books = [(a, n, int(c)) for a, n, c in
             re.findall(r"\[\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*(\d+)\s*\]", m.group(1))]
    if len(books) != 66:
        sys.exit(f"FATAL: expected 66 books in chapters.js, parsed {len(books)}")
    return books


def page_name(book, ch):
    return f"{book} {ch}.html"


TITLE_RE = re.compile(rb"<title>\s*(.*?)\s*</title>", re.S | re.I)


def page_title(body):
    m = TITLE_RE.search(body or b"")
    return m.group(1).decode("utf-8", "replace").strip() if m else None


def get_chapter(book, ch, delay, refresh):
    """-> (status, body). status 200 = the page exists AND its own <title> reads
    "<Book> <n>" (checked on cached pages too — a cached page whose title is
    wrong is deleted and re-requested). Any other status = no such page."""
    p = os.path.join(CACHE, page_name(book, ch))
    want = f"{book} {ch}"
    if not refresh and os.path.exists(p) and os.path.getsize(p) > 0:
        with open(p, "rb") as f:
            body = f.read()
        if page_title(body) == want:
            return 200, body
        print(f"  ! cached {page_name(book, ch)} has title {page_title(body)!r} — "
              f"discarded, re-requesting", file=sys.stderr)
        os.remove(p)
    st, body = http_get("Chapters/" + page_name(book, ch), delay)
    if st != 200:
        return st, b""
    if not body:
        raise RuntimeError(f"fetch failed: {book} {ch} (empty 200)")
    if page_title(body) != want:
        raise RuntimeError(f"fetch failed: {book} {ch} page title reads "
                           f"{page_title(body)!r}")
    with open(p, "wb") as f:
        f.write(body)
    return 200, body


class ChapterParser(HTMLParser):
    """Collect verses: [(ref_text, [(strongs_parts, greek, english), ...]), ...]."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.verses = []
        self.anomalies = []
        self.in_tbl = 0            # depth of open table.tbl
        self.row = None            # current verse: [ref_text, slots]
        self.cell = None           # current td.d: {'s': [...], 'g': [...], 'e': [...], 'ref': [...]}
        self.td_depth = 0
        self.field = None          # 's' | 'g' | 'e' | 'ref' while inside that element
        self.field_tag = None
        self.field_depth = 0

    def handle_starttag(self, tag, attrs):
        cls = (dict(attrs).get("class") or "").split()
        if tag == "table" and "tbl" in cls:
            self.in_tbl += 1
            return
        if not self.in_tbl:
            return
        if tag == "tr":
            self.row = [None, []]
        elif tag == "td" and "d" in cls and self.row is not None and self.cell is None:
            self.cell = {"s": [], "g": [], "e": [], "ref": [], "n": []}
            self.td_depth = 1
        elif tag == "td" and self.cell is not None:
            self.td_depth += 1
        elif self.cell is not None and self.field is None:
            title = dict(attrs).get("title")
            if ("g" in cls or "e" in cls) and title is not None:
                # footnote: <span class="g"|"e" title="…">†</span> — a marker + hover
                # note (variant: Phm 1:6; cross-ref/alt: Jas 2:3 "i.e. please."),
                # NOT a word. Kept in the notes file, out of the Greek/English columns.
                self.cell["n"].append(title)
                self.field, self.field_tag, self.field_depth = "skip", tag, 1
                return
            for k in ("s", "g", "e"):
                if k in cls:
                    self.field, self.field_tag, self.field_depth = k, tag, 1
                    self.cell[k].append("")
                    return
            if "verse" in cls:
                self.field, self.field_tag, self.field_depth = "ref", tag, 1
                self.cell["ref"].append("")
        elif self.field is not None and tag == self.field_tag:
            self.field_depth += 1

    def handle_endtag(self, tag):
        if not self.in_tbl:
            return
        if self.field is not None and tag == self.field_tag:
            self.field_depth -= 1
            if self.field_depth == 0:
                self.field = None
            return
        if tag == "td" and self.cell is not None:
            self.td_depth -= 1
            if self.td_depth == 0:
                self._close_cell()
        elif tag == "tr" and self.row is not None:
            if self.row[0] is None:
                self.anomalies.append(f"row with no verse label ({len(self.row[1])} slots) dropped")
            else:
                self.verses.append((self.row[0], self.row[1]))
            self.row = None
        elif tag == "table":
            self.in_tbl -= 1

    def handle_data(self, data):
        if self.cell is not None and self.field not in (None, "skip"):
            self.cell[self.field][-1] += data

    def _close_cell(self):
        c, self.cell = self.cell, None
        if c["ref"]:
            if self.row[0] is not None:
                self.anomalies.append(f"second verse label in one row: {c['ref']}")
            self.row[0] = " ".join(x.strip() for x in c["ref"])
            return
        if not (c["s"] or c["g"] or c["e"]):
            self.anomalies.append(f"empty slot cell in {self.row[0]}")
        if len(c["g"]) > 1 or len(c["e"]) > 1:
            self.anomalies.append(f"multiple .g/.e in one slot in {self.row[0]}")
        self.row[1].append((
            [s.strip() for s in c["s"]],
            " ".join(c["g"]),
            " ".join(c["e"]),
            c["n"],
        ))


def clean(s):
    return re.sub(r"[\t\r\n]+", " ", s).strip()


REF_RE = re.compile(r"(\d+):(\d+)\s*$")


def parse_page(book, ch, body):
    """-> (rows, notes, anomalies).
    rows  = (book, ch, vs, slot_index, strongs, greek, english)
    notes = (book, ch, vs, slot_index, note) — the † variant footnotes' hover text."""
    p = ChapterParser()
    p.feed(body.decode("utf-8-sig"))
    p.close()
    rows, notes, anomalies = [], [], [f"{book} {ch}: {a}" for a in p.anomalies]
    seen = set()
    for ref, slots in p.verses:
        m = REF_RE.search(ref)
        if not m:
            anomalies.append(f"{book} {ch}: unparseable verse label {ref!r}")
            continue
        rch, vs = int(m.group(1)), int(m.group(2))
        if rch != ch:
            anomalies.append(f"{book} {ch}: verse label {ref!r} names chapter {rch}")
        if vs in seen:
            anomalies.append(f"{book} {ch}: verse {vs} appears twice")
        seen.add(vs)
        if not slots:
            anomalies.append(f"{book} {ch}:{vs}: verse with no slots")
        for i, (sparts, g, e, ns) in enumerate(slots):
            rows.append((book, rch, vs, i, "-".join(sparts), clean(g), clean(e)))
            notes.extend((book, rch, vs, i, clean(n)) for n in ns)
    if not p.verses:
        anomalies.append(f"{book} {ch}: NO verses parsed")
    return rows, notes, anomalies


def check_controls(rows):
    """Return a list of failure strings (empty = both controls hit)."""
    fails = []
    by = {}
    for r in rows:
        by.setdefault((r[0], r[1], r[2]), []).append(r)

    g = [r for r in by.get(("Genesis", 25, 15), []) if r[6].startswith("Hadar")]
    if len(g) != 1:
        fails.append(f"Gen 25:15: expected 1 'Hadar' slot, found {len(g)}")
    else:
        r = g[0]
        ok = r[4] == "*" and r[5] == "Cολδάδ" and r[5][:1] == "C"
        print(f"CONTROL Gen 25:15 slot {r[3]}: strongs={r[4]!r} greek={r[5]!r} "
              f"first-char=U+{ord(r[5][0]):04X} english={r[6]!r} -> {'PASS' if ok else 'FAIL'}"
              if r[5] else f"CONTROL Gen 25:15: empty greek -> FAIL")
        if not ok:
            fails.append("Gen 25:15 Hadar slot does not read strongs='*' greek='Cολδάδ' (Latin C)")

    k = [r for r in by.get(("1 Kings", 11, 14), []) if re.search(r"\bHadad\b", r[6])]
    if len(k) != 1:
        fails.append(f"1Ki 11:14: expected 1 'Hadad' slot, found {len(k)}")
    else:
        r = k[0]
        ok = r[5] == "Αδάρ"
        print(f"CONTROL 1Ki 11:14 slot {r[3]}: strongs={r[4]!r} greek={r[5]!r} "
              f"english={r[6]!r} -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            fails.append("1Ki 11:14 Hadad slot does not read greek='Αδάρ'")
    return fails


def main():
    ap = argparse.ArgumentParser(description="Fetch + flatten the ABP app's chapter pages.")
    ap.add_argument("--out", default=os.path.join(CACHE, "abp_app_slots.tsv"))
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between requests (min 1.0)")
    ap.add_argument("--refresh", action="store_true", help="re-request pages already cached")
    ap.add_argument("--only", action="append", default=[],
                    help='test mode: just this chapter, e.g. "Psalms 3" (repeatable; '
                         'controls always included; no completeness probe)')
    args = ap.parse_args()
    delay = max(1.0, args.delay)
    os.makedirs(CACHE, exist_ok=True)

    books = load_book_list(delay, args.refresh)
    names = [n for _, n, _ in books]

    if args.only:
        plan = list(CONTROL_CHAPTERS)
        for o in args.only:
            m = re.match(r"^(.*\S)\s+(\d+)$", o.strip())
            if not m or m.group(1) not in names:
                sys.exit(f"--only {o!r}: not '<Book> <n>' with a book from chapters.js")
            if (m.group(1), int(m.group(2))) not in plan:
                plan.append((m.group(1), int(m.group(2))))
        plan.sort(key=lambda bc: (names.index(bc[0]), bc[1]))
        probe = False
    else:
        plan = [(n, c) for _, n, cnt in books for c in range(1, max(cnt, 1) + 1)]
        probe = True

    rows, notes, anomalies, failures, extra = [], [], [], [], []
    probe_end = Counter()
    zero_listed = [n for _, n, cnt in books if cnt == 0]
    done_pages = 0

    t0 = time.time()
    for name in names:
        chs = [c for b, c in plan if b == name]
        if not chs:
            continue
        for c in chs:
            try:
                st, body = get_chapter(name, c, delay, args.refresh)
            except RuntimeError as e:
                failures.append(str(e))
                continue
            if st != 200:
                failures.append(f"HTTP {st}: {name} {c} (listed in chapters.js)")
                continue
            r, nt, a = parse_page(name, c, body)
            rows.extend(r)
            notes.extend(nt)
            anomalies.extend(a)
            done_pages += 1
        if probe:
            nxt = max(chs) + 1
            while True:
                try:
                    st, body = get_chapter(name, nxt, delay, args.refresh)
                except RuntimeError as e:
                    failures.append(f"probe {e}")
                    break
                if st is None or st >= 500:
                    failures.append(f"probe {name} {nxt}: no answer (status {st})")
                    break
                if st != 200:
                    probe_end[st] += 1      # 404 / 300 / 301 = no such chapter
                    break
                extra.append(f"{name} {nxt}")
                r, nt, a = parse_page(name, nxt, body)
                rows.extend(r)
                notes.extend(nt)
                anomalies.extend(a)
                done_pages += 1
                nxt += 1
        print(f"  {name}: {len(chs)} chapter(s)  [{done_pages} pages, "
              f"{int(time.time() - t0)}s]", flush=True)

    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write("book\tchapter\tverse\tslot_index\tstrongs\tgreek\tenglish\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    notes_out = os.path.splitext(args.out)[0] + "_notes.tsv"
    with open(notes_out, "w", encoding="utf-8", newline="\n") as f:
        f.write("book\tchapter\tverse\tslot_index\tnote\n")
        for r in notes:
            f.write("\t".join(str(x) for x in r) + "\n")

    verses = {(r[0], r[1], r[2]) for r in rows}
    latin = sum(1 for r in rows if re.search(r"[A-Za-z]", r[5]))
    print()
    print(f"pages parsed: {done_pages}   verses: {len(verses)}   slots: {len(rows)}")
    print(f"footnotes (†, kept out of the Greek/English columns): {len(notes)} -> {notes_out}")
    print(f"slots whose Greek holds a Latin letter: {latin}")
    per_letter = {}
    for r in rows:
        for ch_ in set(re.findall(r"[A-Za-z]", r[5])):
            per_letter[ch_] = per_letter.get(ch_, 0) + 1
    if per_letter:
        print("  by letter (slots): " + "  ".join(
            f"{k}={v}" for k, v in sorted(per_letter.items(), key=lambda kv: -kv[1])))
    if zero_listed:
        print(f"listed with 0 chapters in chapters.js (fetched as chapter 1): {', '.join(zero_listed)}")
    if probe:
        print(f"chapters beyond the chapters.js count that EXIST: {len(extra)}"
              + (f" -> {', '.join(extra)}" if extra else ""))
        print("end-of-book probe answers (no such chapter): "
              + "  ".join(f"HTTP {k}×{v}" for k, v in sorted(probe_end.items())))
    print(f"parser anomalies: {len(anomalies)}")
    for a in anomalies[:40]:
        print(f"  {a}")
    if len(anomalies) > 40:
        print(f"  … {len(anomalies) - 40} more")
    print(f"wrote {args.out}")
    print()

    ctl = check_controls(rows)
    bad = False
    if failures:
        bad = True
        print(f"FETCH FAILURES: {len(failures)} — TSV is INCOMPLETE")
        for x in failures:
            print(f"  {x}")
    if ctl:
        bad = True
        print("CONTROL FAILURE — parser not trusted:")
        for x in ctl:
            print(f"  {x}")
    if bad:
        sys.exit(1)
    print("controls PASS" + ("" if probe else "  (test mode: partial fetch, not the full corpus)"))


if __name__ == "__main__":
    main()
