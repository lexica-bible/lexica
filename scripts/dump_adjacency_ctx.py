#!/usr/bin/env python3
"""dump_adjacency_ctx.py — READ-ONLY slot dump for rulings batch 3 (adjacency
compounds, TICKET_supplied_subject_binds.md, pre-registered grain 2026-07-30).

For every slot in docs/tickets/class3_witness_slots.txt, tokenize the verse's
clean prose (verses.text — the ruled adjacency evidence source, NOT word rows
joined by position) and print one line per occurrence of the census name:

  name|book|ch|vs|occ/i-of-n|prev_tok|next_tok|prev_is_pn|next_is_pn

prev/next tokens are normalized (lowercase, punctuation-stripped); *_is_pn says
whether a words row in that verse with is_pn=1 carries that token as its label
(the Mary-class / chip-merge signal). '^' / '$' mark verse start/end.

Run on PA:  python3 ~/bible-db/scripts/dump_adjacency_ctx.py > ~/adjacency_ctx.txt
Read-only; opens the db mode=ro.
"""
import os, re, sys, sqlite3

DB = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/bible-db/bible.db")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


def norm_tok(t):
    # strip everything but letters at both edges, lowercase (matches er.norm_name
    # intent; leading strip added because prose tokens carry opening punctuation)
    return re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", t).lower()


missing = 0
for ln in open(os.path.join(HERE, "docs", "tickets", "class3_witness_slots.txt"), encoding="utf-8"):
    if ln.startswith("#") or not ln.strip():
        continue
    nm, bk, ch, vs = ln.strip().split("|")
    row = conn.execute(
        "SELECT id, text FROM verses WHERE book=? AND chapter=? AND verse=?",
        (bk, int(ch), int(vs))).fetchone()
    if not row:
        print(f"{nm}|{bk}|{ch}|{vs}|NO-VERSE-ROW")
        missing += 1
        continue
    vid, text = row
    pn_labels = {norm_tok(r[0] or "") for r in conn.execute(
        "SELECT COALESCE(NULLIF(english_head,''), english) FROM words "
        "WHERE verse_id=? AND is_pn=1", (vid,))}
    toks = [norm_tok(t) for t in text.split()]
    hits = [i for i, t in enumerate(toks) if t == nm]
    if not hits:
        print(f"{nm}|{bk}|{ch}|{vs}|NO-TOKEN-MATCH")
        missing += 1
        continue
    for k, i in enumerate(hits, 1):
        prev = toks[i - 1] if i > 0 else "^"
        nxt = toks[i + 1] if i + 1 < len(toks) else "$"
        print(f"{nm}|{bk}|{ch}|{vs}|{k}/{len(hits)}|{prev}|{nxt}"
              f"|{int(prev in pn_labels)}|{int(nxt in pn_labels)}")

print(f"# unmatched slots: {missing}", file=sys.stderr)
