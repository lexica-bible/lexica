#!/usr/bin/env python3
"""
dump_lexica_entry.py — READ-ONLY diagnostic for lexica_def entries.

Why: a stray line (dikaioō's sense-3 text) showed up in Χριστός G5547's gloss_notes after the
split3 re-split. The split3 matcher only reads the SENSES section and is inert on bold words, so it
cannot have written gloss_notes — which means the stray text is baked into the stored RAW. This tool
shows where: it dumps one entry's stored fields vs what the current splitter re-derives, annotates
the raw by section (flagging any numbered line that sits OUTSIDE the senses section), and scans every
entry for that bleed class + an optional text search — so we find every contaminated raw before
cleaning any of them.

PA-ONLY (lexica_def is in bible.db). READ-ONLY (?mode=ro): no model, no writes.

  workon bible-env
  python scripts/dump_lexica_entry.py --word G5547            # full dump of one entry
  python scripts/dump_lexica_entry.py --scan --grep vindicate # find the bleed + where the text lives
"""

import argparse, os, sys, json, re, sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_lexica_def as B

_NUMBERED = re.compile(r'^\s*\d+[.)]\s')


def sections_of(raw):
    """[(section_name|None, line)] per raw line, using the splitter's OWN _SECTION_RE."""
    out, cur = [], None
    for ln in (raw or "").splitlines():
        m = B._SECTION_RE.match(ln)
        if m:
            cur = m.group(1).lower()
        out.append((cur, ln))
    return out


def outside_senses_numbered(raw):
    """Numbered lines that sit in range/gloss notes/coverage (NOT senses) — the bleed class."""
    return [(sec, ln) for sec, ln in sections_of(raw)
            if _NUMBERED.match(ln) and sec not in ("senses", None)]


def dump_word(conn, sid):
    r = conn.execute("SELECT lemma, def_json FROM lexica_def WHERE strongs=?", (sid,)).fetchone()
    if not r:
        print(f"{sid}: not in lexica_def")
        return
    d = json.loads(r["def_json"])
    raw = d.get("raw", "")
    new = B.split_definition(raw)
    print(f"=== {sid} {r['lemma']} ===")
    print(f"  split_ver stored: {d.get('split_ver','?')}")
    for f in ("sense_headlines", "gloss_notes", "range", "coverage"):
        old, nw = d.get(f), new.get(f)
        same = (old == nw)
        print(f"\n[{f}]  stored-vs-rederived: {'SAME' if same else 'DIFF !!'}")
        if f == "sense_headlines":
            print("  stored :", old)
            print("  rederiv:", nw)
        else:
            print("  stored :", repr((old or '')[:500]))
            if not same:
                print("  rederiv:", repr((nw or '')[:500]))
    print("\n--- RAW annotated by section (<<< marks a numbered line outside 'senses') ---")
    for sec, ln in sections_of(raw):
        if ln.strip():
            mark = "   <<< NUMBERED-OUTSIDE-SENSES" if (_NUMBERED.match(ln)
                                                        and sec not in ("senses", None)) else ""
            print(f"  [{(sec or '—'):<11}] {ln.rstrip()}{mark}")


def scan_all(conn, grep):
    rows = conn.execute("SELECT strongs, lemma, def_json FROM lexica_def ORDER BY strongs").fetchall()
    print("=== SCAN: numbered lines sitting OUTSIDE the senses section (the bleed class) ===")
    hits = 0
    for r in rows:
        raw = json.loads(r["def_json"]).get("raw", "")
        for sec, ln in outside_senses_numbered(raw):
            print(f"  {r['strongs']:<7} {r['lemma']:<10} [{sec}]  {ln.strip()[:80]}")
            hits += 1
    print(f"  -> {hits} such line(s) across {len(rows)} entries"
          + ("  (none — nothing bleeding)" if not hits else ""))
    if grep:
        print(f"\n=== SCAN: raws containing {grep!r} ===")
        for r in rows:
            raw = json.loads(r["def_json"]).get("raw", "")
            for sec, ln in sections_of(raw):
                if grep.lower() in ln.lower():
                    print(f"  {r['strongs']:<7} {r['lemma']:<10} [{sec or '—'}]  {ln.strip()[:90]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"))
    ap.add_argument("--word", help="dump one entry (G-number)")
    ap.add_argument("--scan", action="store_true", help="scan all entries for the bleed class")
    ap.add_argument("--grep", help="also scan all raws for this text")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    if args.word:
        dump_word(conn, args.word.upper())
        print()
    if args.scan or args.grep:
        scan_all(conn, args.grep)
    if not args.word and not args.scan and not args.grep:
        ap.error("pass --word G#### and/or --scan [--grep TEXT]")
    conn.close()


if __name__ == "__main__":
    main()
