#!/usr/bin/env python3
"""fix_lane3_star_merges.py — lane-3 hand repairs for the PN-star merged rows the
subject-name fold cannot reach (docs/audits/LANE3_b2_dispositions.md, live-state
re-scope 2026-08-06; ticket docs/tickets/TICKET_pn_star_fix.md).

Applies exactly the reviewer-approved per-row edits frozen in
scripts/lane3_star_fixes.json. Each op is pinned to verse + position +
strongs_base + current english/greek_pos/bracket_id, so it only acts when the
known-bad state is present — safe to re-run, and it joins the post-rebuild
repair chain (split_merge_fixes precedent). Writes english / english_head /
greek_pos / bracket_id ONLY; number columns and positions never move.

Dry-run prints, per verse, every word row BEFORE and AFTER (position, english,
greek_pos, bracket_id) so bracket state is fully visible (reviewer requirement
for the inside-bracket rows 2Sa 14:4 and Lev 24:10).

Usage (PA, JP runs):
  python3 scripts/fix_lane3_star_merges.py ~/bible-db/bible.db            # dry-run
  python3 scripts/fix_lane3_star_merges.py ~/bible-db/bible.db --apply
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

_TRAIL = re.compile(r"[.,;:!?·)]+$")


def prose(rows):
    """Faithful port of the reader's getEnglishOrderWords
    (static/src/56-library-order-logic.jsx lines 33-87): bracket members are
    grouped by id ACROSS gaps, trailing clause punctuation floats to the
    group's display-last English-carrying word, groups reorder by greek_pos
    (stable, missing -> end) and render at the first member's spot. NOTE:
    list_split_merge_skips.display_seq walks brackets contiguously and would
    MIS-model a bracket with a blank slot inside its span; this port follows
    the production function. Cross-proven against the real Node module on the
    lane-3 after-states (see the lane-3 session record)."""
    groups = {}
    for r in rows:
        b = r["bracket_id"]
        if b is not None:
            groups.setdefault(b, []).append(
                {"english": r["english"], "greek_pos": r["greek_pos"]})
    for b, ws in groups.items():
        trailing, cleaned = "", []
        for w in ws:
            e = (w["english"] or "").strip()
            if e and _TRAIL.sub("", e) == "":
                trailing += e
                continue
            m = _TRAIL.search(e)
            if m:
                cleaned.append({**w, "english": e[:m.start()].rstrip()})
                trailing += m.group()
            else:
                cleaned.append(w)
        cleaned.sort(key=lambda w: w["greek_pos"] if w["greek_pos"] is not None else 999)
        if trailing and cleaned:
            li = len(cleaned) - 1
            while li > 0 and not (cleaned[li]["english"] or "").strip():
                li -= 1
            cleaned[li] = {**cleaned[li],
                           "english": (cleaned[li]["english"] or "") + trailing}
        groups[b] = cleaned
    out, seen = [], set()
    for r in rows:
        b = r["bracket_id"]
        if b is None:
            if (r["english"] or "").strip():
                out.append(r["english"].strip())
        elif b not in seen:
            seen.add(b)
            out.extend(w["english"] for w in groups[b] if (w["english"] or "").strip())
    return " ".join(out)

DB = next((a for a in sys.argv[1:] if not a.startswith("--")), "bible.db")
APPLY = "--apply" in sys.argv
FIXES_FILE = "lane3_star_fixes.json"
if "--fixes" in sys.argv:
    FIXES_FILE = sys.argv[sys.argv.index("--fixes") + 1]
FIXES = json.loads((Path(__file__).parent / FIXES_FILE).read_text(encoding="utf-8"))
FIXES.pop("_comment", None)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row


def fmt(rows):
    out = []
    for r in rows:
        out.append("    pos %-3s eng %-28r gpos %-4s bid %-4s [%s]" % (
            r["position"], r["english"],
            r["greek_pos"] if r["greek_pos"] is not None else "-",
            r["bracket_id"] if r["bracket_id"] is not None else "-",
            r["strongs_base"]))
    return "\n".join(out)


applied = skipped = 0
for verse, spec in FIXES.items():
    book, rest = verse.rsplit(" ", 1)
    ch, vs = rest.split(":")
    v = conn.execute("SELECT id, text FROM verses WHERE book=? AND chapter=? AND verse=?",
                     (book, int(ch), int(vs))).fetchone()
    if v is None:
        print(f"SKIP {verse}: verse not found"); skipped += 1; continue
    rows = conn.execute(
        "SELECT id, position, english, english_head, strongs_base, greek_pos,"
        " bracket_id FROM words WHERE verse_id=? ORDER BY position",
        (v["id"],)).fetchall()
    by_pos = {r["position"]: r for r in rows}
    bids = {r["bracket_id"] for r in rows if r["bracket_id"] is not None}

    # guards — all-or-nothing per verse
    reason = None
    for nb in spec["new_bids"]:
        if nb in bids:
            reason = f"new bracket id {nb} already in use"; break
    for jb in spec["join_bids"]:
        if reason is None and jb not in bids:
            reason = f"bracket id {jb} to join does not exist"
    plan = []
    if reason is None:
        for op in spec["ops"]:
            r = by_pos.get(op["pos"])
            if r is None:
                reason = f"no row at pos {op['pos']}"; break
            if r["strongs_base"] != op["sbase"]:
                reason = f"strongs mismatch pos {op['pos']} ({r['strongs_base']} != {op['sbase']})"; break
            if (r["english"] or None) != op["old_eng"]:
                reason = f"english mismatch pos {op['pos']} ({r['english']!r})"; break
            if r["greek_pos"] != op["old_gpos"] or r["bracket_id"] != op["old_bid"]:
                reason = (f"gpos/bracket mismatch pos {op['pos']} "
                          f"({r['greek_pos']},{r['bracket_id']})"); break
            plan.append((r["id"], op))
    if reason is not None:
        print(f"SKIP {verse}: {reason}  (already fixed, or state changed)")
        skipped += 1
        continue

    after = []
    op_by_pos = {op["pos"]: op for op in spec["ops"]}
    for r in rows:
        op = op_by_pos.get(r["position"])
        if op:
            after.append({"position": r["position"], "english": op["new_eng"],
                          "greek_pos": op["new_gpos"], "bracket_id": op["new_bid"],
                          "strongs_base": r["strongs_base"]})
        else:
            after.append(r)

    print(f"\n=== {verse} === ({len(plan)} cell edits)")
    print("  BEFORE:"); print(fmt(rows))
    print("  AFTER:");  print(fmt(after))
    p_before, p_after = prose(rows), prose(after)
    print(f"  PROSE BEFORE: {p_before}")
    print(f"  PROSE AFTER:  {p_after}")
    print(f"  verses.text:  {v['text']}")
    print(f"  render check: prose unchanged by the edit -> "
          f"{'PASS' if p_before == p_after else 'FAIL'}")
    # Contiguity check (chip/interlinear trap, 2026-08-07): groupForGreekMode
    # walks CONSECUTIVE same-bracket runs, so every slot inside a bracket's
    # position span must carry that bracket's mark — the build's own shape
    # (blank members, no reading number). A gap splits the run and chip /
    # interlinear reorder each fragment alone.
    spans = {}
    for r in after:
        if r["bracket_id"] is not None:
            lo, hi = spans.get(r["bracket_id"], (r["position"], r["position"]))
            spans[r["bracket_id"]] = (min(lo, r["position"]), max(hi, r["position"]))
    gaps = [(b, r["position"]) for b, (lo, hi) in spans.items()
            for r in after if lo < r["position"] < hi and r["bracket_id"] != b]
    print(f"  contiguity check: "
          f"{'PASS' if not gaps else 'FAIL ' + str(gaps)}")

    if APPLY:
        for rid, op in plan:
            conn.execute(
                "UPDATE words SET english=?, english_head=?, greek_pos=?, bracket_id=?"
                " WHERE id=?",
                (op["new_eng"], op["new_head"], op["new_gpos"], op["new_bid"], rid))
    applied += 1

if APPLY:
    conn.commit()
conn.close()
print(f"\n{'APPLIED' if APPLY else 'DRY-RUN'} — {applied} verse(s) "
      f"{'patched' if APPLY else 'ready'}, {skipped} skipped  [DB: {DB}]")
if not APPLY:
    print("(dry-run — nothing written; re-run with --apply after the verdict)")
