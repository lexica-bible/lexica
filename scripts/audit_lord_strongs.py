#!/usr/bin/env python3
"""audit_lord_strongs.py — READ-ONLY. Why does the word "LORD" (κύριος/G2962)
sometimes render without its G2962 Strong's in chip mode? This quantifies it and
buckets the cause.

It replicates the frontend `strongsAnchorIndex` (static/app.jsx) to predict which
word of a multi-word gloss actually shows the Strong's, then checks whether the
"LORD" word lands on a G2962 row AND is that anchor word.

Buckets (per "LORD"/"lord" word occurrence):
  OK            "LORD" sits on a G2962 row and IS the displayed anchor → shows G2962 ✓
  ANCHOR-MORPH  "LORD" on a G2962 row but NOT the anchor — the anchor fell to the first
                word because the row has no morph (isContent=false). FRONTEND-fixable:
                anchor on english_head even when morph is null.
  WRONG-SLOT    the "LORD" text sits on a NON-G2962 row (bundled onto a sibling, e.g. the
                article) — the κύριος slot is elsewhere/empty. DATA class (tier1 C1).
                Sub-bucketed for the dual-ordering pilot #1:
                  REPAIRABLE  a multi-word non-bracketed slot holding "...LORD..." whose
                              ADJACENT next slot is an EMPTY, non-bracketed κύριος/G2962
                              (1Ch 13:10 shape). Fixable by a surgical UPDATE — the target
                              slot already exists, no INSERT. THIS is the pilot target set.
                  OTHER       any other WRONG-SLOT shape (no adjacent empty G2962) — out of
                              pilot scope (would need an inserted row / different handling).

READ-ONLY (mode=ro). Run on PA:  python3 scripts/audit_lord_strongs.py bible.db
"""
import re
import sqlite3
import sys
from collections import Counter

DB = next((a for a in sys.argv[1:] if not a.startswith("-")), "bible.db")


def bare(s):
    return re.sub(r"[^\w]", "", s or "").lower()


def anchor_index(parts, italic_set, morph, head):
    """Mirror of strongsAnchorIndex(parts, italicSet, w) in app.jsx (post-2026-06-05:
    anchors on english_head whenever present, no longer gated on morph)."""
    first_non_italic = next((i for i, w in enumerate(parts)
                             if bare(w) not in italic_set), 0)
    if head:
        hb = bare(head)
        for i, w in enumerate(parts):
            if bare(w) == hb and bare(w) not in italic_set:
                return i
    return first_non_italic


conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row


def next_slot(verse_id, position):
    """The slot immediately after (verse_id, position), or None."""
    return conn.execute(
        "SELECT english, strongs_base, bracket_id FROM words "
        "WHERE verse_id=? AND position=?",
        (verse_id, position + 1)).fetchone()


def lord_prefix_split(eng):
    """If `eng` is '(the) LORD <rest...>' — i.e. an optional leading article then
    LORD at the HEAD, with ≥1 word after — return (move='the LORD', keep='<rest>').
    Else None. The keep is the clean verb gloss; prose can then read move(gpos1)
    then keep(gpos2) = the original. A gloss with a word BEFORE 'LORD' ('May the
    LORD add') is WRAPPED — returns None (it needs the use-case #3 inserted row, not
    this 2-slot move)."""
    parts = eng.split()
    i = 0
    while i < len(parts) and bare(parts[i]) in ("the", "a", "an"):
        i += 1
    if i >= len(parts) or bare(parts[i]) != "lord":
        return None                     # LORD not at the head → wrapped / other shape
    move, keep = parts[:i + 1], parts[i + 1:]
    if not keep:
        return None                     # nothing left to keep on the verb
    return " ".join(move), " ".join(keep)


def repair_shape(r):
    """Returns (move, keep) when r is the clean pilot #1 shape, else None.
    Clean = multi-word, non-bracketed, gloss '(the) LORD <verb...>' (LORD at head),
    AND the ADJACENT next slot is an EMPTY, non-bracketed κύριος/G2962 (1Ch 13:10).
    Keyed on the slot-pair SHAPE, not absolute position → idempotent / pos-independent."""
    eng = r["english"] or ""
    if " " not in eng or r["bracket_id"] is not None:
        return None
    split = lord_prefix_split(eng)
    if not split:
        return None
    nxt = next_slot(r["verse_id"], r["position"])
    if (nxt and (nxt["english"] or "").strip() == ""
            and nxt["strongs_base"] == "G2962"
            and nxt["bracket_id"] is None):
        return split
    return None


rows = conn.execute(
    "SELECT w.verse_id, w.position, w.english, w.english_head, w.strongs_base, "
    "       w.morph, w.italic_words, w.bracket_id, v.book, v.chapter, v.verse "
    "FROM words w JOIN verses v ON v.id = w.verse_id "
    "WHERE w.english LIKE '%lord%'"
).fetchall()

buckets = Counter()
upper_only = Counter()          # restrict to capital "LORD" (divine name)
wrong_sub = Counter()           # REPAIRABLE vs OTHER within WRONG-SLOT
wrong_sub_upper = Counter()
samples = {"ANCHOR-MORPH": [], "WRONG-SLOT/REPAIRABLE": [], "WRONG-SLOT/OTHER": []}
_UNSET = object()                   # per-row cache sentinel for repair_shape

for r in rows:
    eng = r["english"] or ""
    parts = eng.split()
    italic_set = set((r["italic_words"] or "").split(",")) if r["italic_words"] else set()
    lord_idxs = [i for i, w in enumerate(parts) if bare(w) == "lord"]
    if not lord_idxs:
        continue
    single = " " not in eng
    ai = None if single else anchor_index(parts, italic_set, r["morph"], r["english_head"])
    ref = f"{r['book']} {r['chapter']}:{r['verse']}"
    rshape = _UNSET                 # (move, keep) | None — computed once per row, lazily
    for li in lord_idxs:
        is_upper = parts[li].replace(",", "").replace(".", "").isupper()
        # single-word rows show their own Strong's directly (no anchor logic)
        if single:
            tag = "OK" if r["strongs_base"] == "G2962" else "WRONG-SLOT"
        elif r["strongs_base"] != "G2962":
            tag = "WRONG-SLOT"
        elif li == ai:
            tag = "OK"
        else:
            tag = "ANCHOR-MORPH"
        buckets[tag] += 1
        if is_upper:
            upper_only[tag] += 1
        if tag == "WRONG-SLOT":
            if rshape is _UNSET:
                rshape = repair_shape(r)
            sub = "REPAIRABLE" if rshape else "OTHER"
            wrong_sub[sub] += 1
            if is_upper:
                wrong_sub_upper[sub] += 1
            skey = f"WRONG-SLOT/{sub}"
            if len(samples[skey]) < 15:
                if rshape:
                    detail = f"move={rshape[0]!r} keep={rshape[1]!r}"
                else:
                    nxt = next_slot(r["verse_id"], r["position"])
                    detail = (f"next[{r['position']+1}]={nxt['strongs_base'] or '-'}"
                              f" eng={(nxt['english'] or '∅')!r}") if nxt else "next=∅"
                samples[skey].append((ref, r["strongs_base"], r["morph"] or "∅", eng, detail))
        elif tag == "ANCHOR-MORPH" and len(samples["ANCHOR-MORPH"]) < 12:
            samples["ANCHOR-MORPH"].append((ref, r["strongs_base"], r["morph"] or "∅", eng, ""))
conn.close()

total = sum(buckets.values())
print(f"READ-ONLY 'LORD'/κύριος Strong's-display audit -> {DB}")
print(f"  total 'LORD'/'lord' word occurrences: {total:,}  (capital 'LORD' only: {sum(upper_only.values()):,})\n")
for tag in ("OK", "ANCHOR-MORPH", "WRONG-SLOT"):
    print(f"  {tag:13}: {buckets[tag]:6,}   (capital LORD: {upper_only[tag]:,})")
print()
print("  WRONG-SLOT breakdown (dual-ordering pilot #1 target = REPAIRABLE):")
for sub in ("REPAIRABLE", "OTHER"):
    print(f"    {sub:10}: {wrong_sub[sub]:6,}   (capital LORD: {wrong_sub_upper[sub]:,})")
print()
print("  REPAIRABLE   = adjacent EMPTY κύριος/G2962 slot exists → surgical UPDATE, no INSERT (PILOT #1 SET)")
print("  OTHER        = no adjacent empty G2962 slot (different shape; out of pilot scope)")
print("  ANCHOR-MORPH = frontend strongsAnchorIndex residual (should be ~0 post-4652aa4)\n")
for skey in ("WRONG-SLOT/REPAIRABLE", "WRONG-SLOT/OTHER", "ANCHOR-MORPH"):
    if samples[skey]:
        col = "move/keep split" if skey.endswith("REPAIRABLE") else "next slot"
        print(f"  --- {skey} samples (ref | strongs_base | morph | english | {col}) ---")
        for ref, sb, m, eng, detail in samples[skey]:
            print(f"      {ref:12} | {sb:7} | {m:8} | {eng!r:40} | {detail}")
        print()
