#!/usr/bin/env python3
"""
check_gate5_sweep.py — gate 5 of the head-word rebuild charter: the double-star
sweep. Read-only.

Re-dumps the remaining named-but-unresolved rows (strongs_base='*', English
present) from the given db, head-word level — the same shape as the pinned live
dump double_star_names.txt — and requires every head to land in a DOCUMENTED
bucket:

  LEAVE      — pile B / hand-check rejects / cautions (the 221 documented leaves;
               docs/tickets/alias_leave_list.txt + alias_decisions.txt)
  RESOLVES   — the bare head is a known name key (roster / hand ALIASES /
               VARIANT_ALIASES / DIRECT): the rows are multi-word cells the
               matcher can't take whole ("Jesus said") — pre-existing shape class
  PILE-A     — a pile-A common-word head still present: RC-1 was supposed to
               re-head these rows; each one is itemized for an eyeball
  STOP       — anything else. Undocumented residue fails the gate.

Exit 1 if any STOP head exists.
Usage: python3 scripts/check_gate5_sweep.py <db>
"""
import ast
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

# The five PRE-EXISTING empty-head rows, pinned BY REF (reviewer ruling
# 2026-07-16): these exact rows pass, ANY other empty head is STOP. A
# class-level allowance would have swallowed the Isa 41:14 vocative mispeel.
DOCUMENTED_EMPTY_HEADS = {
    ("1Sa 9:9", 27), ("2Sa 19:22", 22), ("2Sa 3:33", 15),
    ("Neh 8:7", 22), ("Num 27:13", 18),
}


def load_name_keys():
    """Every bare key the resolution ladder can hit exactly: parsed roster +
    the three hand maps (extracted from the production sources, not copied)."""
    sys.argv = [sys.argv[0], "--dry-run"]
    import import_tipnr
    lines = (ROOT / "tipnr" / "TIPNR.txt").read_text(encoding="utf-8").splitlines()
    lookup, _ = import_tipnr.parse_tipnr(lines)
    keys = set(lookup)
    tree = ast.parse((ROOT / "scripts" / "import_tipnr.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") in ("ALIASES", "DIRECT"):
            keys |= {ast.literal_eval(k) for k in node.value.keys}
    from tipnr_alias_variants import VARIANT_ALIASES
    keys |= set(VARIANT_ALIASES)
    return keys


def load_documented():
    pile_a, leave = set(), set()
    for line in (ROOT / "docs" / "tickets" / "alias_leave_list.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or "|" not in line:
            continue
        pile, key = [p.strip() for p in line.split("|")[:2]]
        (pile_a if pile == "A" else leave).add(key.lower())
    for line in (ROOT / "docs" / "tickets" / "alias_decisions.txt").read_text(encoding="utf-8").splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 5 and parts[4] in ("REJECT", "CAUTION"):
            leave.add(parts[0].lower())
    return pile_a, leave


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    db = sys.argv[1]
    keys = load_name_keys()
    pile_a, leave = load_documented()
    live_heads = set()
    for line in (ROOT / "double_star_names.txt").read_text(encoding="utf-8").splitlines():
        h = line.split("|")[0].strip().lower()
        if h:
            live_heads.add(h)

    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = con.execute(
        "SELECT lower(coalesce(english_head,'')), count(*),"
        " min(v.book || ' ' || v.chapter || ':' || v.verse)"
        " FROM words w JOIN verses v ON v.id = w.verse_id"
        " WHERE w.strongs_base='*' AND trim(coalesce(w.english,'')) <> ''"
        " GROUP BY 1 ORDER BY 2 DESC").fetchall()
    # Empty heads are judged ROW BY ROW against the pinned five, never as a class.
    empty_rows = con.execute(
        "SELECT v.book || ' ' || v.chapter || ':' || v.verse, w.position, w.english"
        " FROM words w JOIN verses v ON v.id = w.verse_id"
        " WHERE w.strongs_base='*' AND trim(coalesce(w.english,'')) <> ''"
        " AND trim(coalesce(w.english_head,'')) = ''").fetchall()
    con.close()

    buckets = {"LEAVE": 0, "RESOLVES": 0, "PILE-A": [], "STOP": []}
    total_rows = 0
    documented_empty = 0
    for ref, pos, eng in empty_rows:
        if (ref, pos) in DOCUMENTED_EMPTY_HEADS:
            documented_empty += 1
        else:
            buckets["STOP"].append(
                ("", 1, f"{ref} | {pos}", f"UNDOCUMENTED empty head (english {eng!r})"))
    for head, cnt, ref in rows:
        total_rows += cnt
        if not head:
            continue  # handled row-by-row above
        elif head in leave:
            buckets["LEAVE"] += 1
        elif head in pile_a:
            buckets["PILE-A"].append((head, cnt, ref, "pile-A common word still a head"))
        elif head in keys:
            buckets["RESOLVES"] += 1
        elif head in live_heads:
            buckets["STOP"].append((head, cnt, ref, "live-dump head neither documented nor resolvable"))
        else:
            buckets["STOP"].append((head, cnt, ref, "BRAND-NEW undocumented head"))

    print(f"db: {db}")
    print(f"named unresolved rows: {total_rows} across {len(rows)} distinct heads")
    print(f"  documented leaves present : {buckets['LEAVE']}")
    print(f"  documented empty-head rows: {documented_empty} (of the pinned 5)")
    print(f"  head-resolves (multi-word row shapes, pre-existing class): {buckets['RESOLVES']}")
    print(f"  pile-A heads still present: {len(buckets['PILE-A'])} (each needs an eyeball)")
    for head, cnt, ref, why in buckets["PILE-A"]:
        print(f"     {head} | {cnt} | {ref}")
    print(f"  STOP heads: {len(buckets['STOP'])} (must be 0)")
    for head, cnt, ref, why in buckets["STOP"]:
        print(f"     {head!r} | {cnt} | {ref} | {why}")
    if buckets["STOP"]:
        sys.exit(1)
    print("gate-5 sweep: no undocumented residue.")


if __name__ == "__main__":
    main()
