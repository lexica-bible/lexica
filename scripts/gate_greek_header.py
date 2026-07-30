#!/usr/bin/env python3
"""gate_greek_header.py — pre-swap gate for the Greek-header backfill lane
(DRILL_greek_header_backfill.md, JP-ruled 2026-07-30). READ-ONLY on both files.

This lane touches PRESENTATION only (the pn_greek_identity table). The gates:
  gate A  identity untouched: pn_binding, tipnr_entities byte-identical;
          words/verses/abp_surface row counts unchanged (translit byte-check is
          implied by abp_surface identity). ANY identity delta = automatic stop.
  gate B  pn_greek_identity delta is EXACTLY the ruled shape: same keys; every
          greek_strongs unchanged; per-row allowed changes only:
            unchanged row
            breathing repair (old value has the detached mark+space prefix and
              new == fix_detached_breathing(old))
            none       -> surface   (a new disciplined headword)
            lemma-only -> surface   (surface-derived value re-disciplined)
            lemma-only -> none      (bent/unresolvable form honestly dropped)
          Anything else (a strongs change, abp-tag/tipnr source change, a
          none -> lemma-only, a changed headword outside the classes) = FAIL.
  gate C  controls: hadad must FLIP to source='surface' in the scratch copy
          (the founding specimen), and every pin in
          docs/tickets/greek_header_pins.txt (name|expected-form, filled at
          verdict time from the receipt) must match the scratch value exactly.

CONTROL FIRST (audit-tools-must-fail): run with the LIVE file as both arguments —
gate C must FAIL (hadad still English), gates A/B must PASS. Only then run
live vs scratch.

Usage: python3 scripts/gate_greek_header.py <live.db> <scratch.db>
"""
import os
import sqlite3
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from build_pn_greek_identity import fix_detached_breathing   # the ONE transform

if len(sys.argv) != 3:
    sys.exit("usage: gate_greek_header.py <live.db> <scratch.db>")
live = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
scr = sqlite3.connect(f"file:{sys.argv[2]}?mode=ro", uri=True)
fails = []

# ── gate A — identity layer untouched ────────────────────────────────────────
okA = True
for tbl, cols in (("pn_binding", "book,chapter,verse,name,entity_uniq,kind,rule,render,hot,tier"),
                  ("tipnr_entities", "uniq,head,section,gender,area,descr,summary,bases,parents,offspring"),
                  ("abp_surface", "verse_id,position,form,translit")):
    l = list(live.execute(f"SELECT {cols} FROM {tbl} ORDER BY 1,2,3,4"))
    s = list(scr.execute(f"SELECT {cols} FROM {tbl} ORDER BY 1,2,3,4"))
    same = l == s
    okA &= same
    print(f"gate A: {tbl:15} {len(l):,} vs {len(s):,} rows — "
          + ("byte-identical" if same else "DIFFER"))
for tbl in ("words", "verses"):
    lc = live.execute(f"SELECT count(*) FROM {tbl}").fetchone()[0]
    sc = scr.execute(f"SELECT count(*) FROM {tbl}").fetchone()[0]
    okA &= lc == sc
    print(f"gate A: {tbl:15} count {lc:,} vs {sc:,}" + ("" if lc == sc else " — DIFFER"))
print(f"gate A: {'PASS' if okA else 'FAIL'} — identity layer "
      + ("untouched" if okA else "CHANGED — automatic stop"))
if not okA:
    fails.append("A")

# ── gate B — the pn_greek_identity delta shape ───────────────────────────────
q = "SELECT verse_id, position, greek_strongs, greek_lemma, source FROM pn_greek_identity"
lrows = {(r[0], r[1]): (r[2], r[3], r[4]) for r in live.execute(q)}
srows = {(r[0], r[1]): (r[2], r[3], r[4]) for r in scr.execute(q)}
bad = []
counts = {"unchanged": 0, "breathing": 0, "none->surface": 0,
          "lemma-only->surface": 0, "lemma-only->none": 0}
if set(lrows) != set(srows):
    bad.append(("KEYSET", len(set(lrows) ^ set(srows)), "keys added/removed"))
for k in set(lrows) & set(srows):
    (lg, ll, ls), (sg, sl, ss) = lrows[k], srows[k]
    if lg != sg:
        bad.append((k, f"{lg}->{sg}", "greek_strongs CHANGED")); continue
    if (ll, ls) == (sl, ss):
        counts["unchanged"] += 1; continue
    if ls == ss and ll and sl == fix_detached_breathing(ll) and sl != ll:
        counts["breathing"] += 1; continue
    tr = f"{ls}->{ss}"
    if tr in ("none->surface", "lemma-only->surface") and sl:
        counts[tr] += 1; continue
    if tr == "lemma-only->none" and not sl:
        counts[tr] += 1; continue
    bad.append((k, tr, f"lemma {ll!r} -> {sl!r} outside the ruled classes"))
okB = not bad
print(f"gate B: {'PASS' if okB else 'FAIL'} — " +
      ", ".join(f"{k} {v:,}" for k, v in counts.items())
      + (f"; VIOLATIONS {len(bad)}" if bad else ""))
for b in bad[:8]:
    print(f"    problem: {b}")
if not okB:
    fails.append("B")

# ── gate C — controls + pinned exact forms ───────────────────────────────────
okC = True
hadad = scr.execute(
    "SELECT g.source, g.greek_lemma FROM pn_greek_identity g "
    "JOIN words w ON w.verse_id=g.verse_id AND w.position=g.position "
    "JOIN verses v ON v.id=g.verse_id "
    "WHERE v.book='1Ki' AND v.chapter=11 AND w.is_pn=1 "
    "AND lower(COALESCE(NULLIF(w.english_head,''), w.english)) LIKE '%hadad%' "
    "AND g.source='surface' LIMIT 1").fetchone()
print(f"gate C: hadad 1Ki 11 flips to source='surface': {'YES' if hadad else 'NO'}"
      + (f" ({hadad[1]})" if hadad else ""))
okC &= hadad is not None

pins = os.path.join(_HERE, "..", "docs", "tickets", "greek_header_pins.txt")
if os.path.isfile(pins):
    for ln in open(pins, encoding="utf-8"):
        if ln.startswith("#") or not ln.strip():
            continue
        nm, expect = ln.rstrip("\n").split("|")[:2]
        got = scr.execute(
            "SELECT DISTINCT g.greek_lemma FROM pn_greek_identity g "
            "JOIN words w ON w.verse_id=g.verse_id AND w.position=g.position "
            "WHERE g.source='surface' "
            "AND lower(COALESCE(NULLIF(w.english_head,''), w.english)) = ?",
            (nm.lower(),)).fetchall()
        vals = sorted({r[0] for r in got})
        ok = vals == [expect]
        okC &= ok
        print(f"gate C: pin {nm} = {expect!r}: {'PASS' if ok else f'FAIL (got {vals})'}")
else:
    print("gate C: no pins file yet (docs/tickets/greek_header_pins.txt) — "
          "pins land at verdict time from the receipt")
print(f"gate C: {'PASS' if okC else 'FAIL'}")
if not okC:
    fails.append("C")

print()
if fails:
    print(f"FAILED gates: {fails} — ABORT, discard the scratch copy.")
    sys.exit(1)
print("Gates A/B/C all PASS. Swap on verdict, reload, then served-layer spot checks.")
