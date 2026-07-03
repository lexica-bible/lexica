#!/usr/bin/env python3
"""
audit_dangling_context.py — READ-ONLY. For every built lexica_def entry, run the build's OWN
dangling-book detector over its stored raw prose and print each flagged book together with the
sentence it came from, so a genuine botched citation (a real "Ruth" reference with no ch:vs) can
be told apart from a prose collision (the English word "son", the person "Job").

Reuses build_lexica_def._REF_RE / _DANGLING_BOOK_RE / _norm_book — same detector as the build, so
this shows precisely what the lint flags. Touches nothing (mode=ro).

  workon bible-env
  python scripts/audit_dangling_context.py
"""
import json, os, re, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # scripts/ — for build_lexica_def
import build_lexica_def as B


def contexts(conn, raw):
    """[(code, surface, sentence)] for each surface the dangling lint would flag. MIRRORS
    build_lexica_def.dangling_book_refs step-for-step (chapter-strip + soft-skip) so the reporter
    can't drift from the real lint."""
    stripped = B._CHAP_ONLY_RE.sub("  ", B._REF_RE.sub("  ", raw or ""))   # ch:vs AND chapter refs
    valid = B._valid_books(conn)
    out = []
    for m in B._DANGLING_BOOK_RE.finditer(stripped):
        surface = m.group(1)
        if re.sub(r"\s+", "", surface).lower() in B._DANGLING_SOFT:        # bare English/name surface
            continue
        code = B._norm_book(surface)
        if code not in valid:
            continue
        s, e = m.start(), m.end()
        left = stripped[max(0, s - 55):s].replace("\n", " ")
        right = stripped[e:e + 55].replace("\n", " ")
        out.append((code, surface, f"…{left}[{surface}]{right}…"))
    return out


def main():
    db = os.path.expanduser("~/bible-db/bible.db")
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT strongs, lemma, def_json FROM lexica_def ORDER BY strongs").fetchall()
    total = 0
    for r in rows:
        try:
            raw = json.loads(r["def_json"]).get("raw", "")
        except Exception:
            continue
        hits = contexts(conn, raw)
        if not hits:
            continue
        print(f"\n{r['strongs']}  {r['lemma']}  ({len(hits)} flag(s)):")
        for code, surface, ctx in hits:
            total += 1
            print(f"    {code:<5} via '{surface}':  {ctx}")
    print(f"\n{total} dangling flag(s) across {len(rows)} entries.")
    conn.close()


if __name__ == "__main__":
    main()
