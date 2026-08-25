#!/usr/bin/env python3
"""gate_greek_header.py — pre-swap gate for the Greek-header backfill lane
(DRILL_greek_header_backfill.md, JP-ruled 2026-07-30). READ-ONLY on both files.

This lane touches PRESENTATION only (the pn_greek_identity table). The gates:
  gate A  identity untouched: pn_binding, tipnr_entities byte-identical;
          words/verses/abp_surface row counts unchanged (translit byte-check is
          implied by abp_surface identity). ANY identity delta = automatic stop.
  gate B  pn_greek_identity delta is EXACTLY the ruled shape (ruling (b),
          JP 2026-07-30): same keys; every greek_strongs unchanged; per-row
          allowed changes only:
            unchanged row
            breathing repair (new == fix_detached_breathing(old), old != new)
            -> surface     (a new disciplined per-name headword, any prior source
                            except abp-tag/tipnr)
            a lemma value that EQUALS the verse's own abp_surface form (breathing-
              repaired) — the (b) page-attested fallback; source may become
              lemma-only from none, or stay put
            lemma-only -> none  (gentilic-class drop — counted, JP eyeballs the total)
          Anything else (a strongs change, an abp-tag/tipnr source change, a
          header that matches neither the page nor the repair) = FAIL.
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
sys.path.insert(0, os.path.join(_HERE, ".."))
from build_pn_greek_identity import fix_detached_breathing   # the ONE transform
import entity_resolution as er   # is_people_group — the build's OWN people-word
                                 # check (one classifier, never a second copy)

args = sys.argv[1:]
dump_path = None
if "--dump" in args:
    i = args.index("--dump")
    dump_path = args[i + 1]
    del args[i:i + 2]
if len(args) != 2:
    sys.exit("usage: gate_greek_header.py <live.db> <scratch.db> [--dump <out.tsv>]")
live = sqlite3.connect(f"file:{args[0]}?mode=ro", uri=True)
scr = sqlite3.connect(f"file:{args[1]}?mode=ro", uri=True)
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
# AMENDED BY RULING 2026-08-24 (HANDOFF_gateB_enumeration.md — the 8/23 abort
# enumerated; reviewer approved three changes):
#   1. two PINNED per-member lists with an expected outcome per member — the
#      form lane's 8 enumerated bridge-fail slots (6 were the visible violators;
#      Samaria left via the old gentilic door; Est 1:21 improved through the
#      ->surface headword class, now pinned to that exact outcome) and the 8
#      ruled no-form blanks (5 bridge-claimed blank slots from the charter's −1
#      accounting + 3 star slots with no form and no dictionary entry, incl.
#      Num 21:25/9 whose live value was a verb — defective, cure).
#   2. a glued-cure class keyed to the NBSP probe, sub-buckets PINNED for this
#      landing: live glued 144 = 30 kept (27 compounds + 3 parked) + 20 blanked
#      + 94 replaced with real values. Re-pin on any future lane.
#   3. the gentilic-drop door re-keyed to er.is_people_group — the old door was
#      shape-only and passed a place-name and 7 glued defects unflagged.
PINNED_BRIDGE_FAIL = {
    ("Gen", 39, 17, 14): "blank",   # "hebrew" people-word — refusal ruled correct
    ("Gen", 41, 12, 7):  "blank",   # "hebrew" people-word — refusal ruled correct
    ("Mar", 2, 8, 4):    "blank",   # unaccented Ιησους — no attestation
    ("Mat", 9, 35, 3):   "blank",   # Ισηούς scrape letter-swap typo — corrections lane
    ("Mar", 14, 66, 3):  "blank",   # Πέτρου declined form unattested — hand-table door
    ("Act", 18, 14, 9):  "blank",   # Γαλλίων — no standalone attestation in-book
    ("Act", 8, 14, 9):   "blank",   # Σαμάρεια form variant unattested — hand-table door
    ("Est", 1, 21, 16):  ("Μεμουχάν", "surface"),  # bridge repair IMPROVED it
}
PINNED_NOFORM_BLANK = {             # ruled losses: slot has no form in the
    ("1Ch", 10, 13, 22): "blank",   # repaired table and no dictionary entry —
    ("1Ki", 19, 6, 2):   "blank",   # 5 bridge-claimed blank slots (one-claim
    ("Exo", 35, 4, 14):  "blank",   # rule, charter's −1 accounting; the 6th,
    ("Gen", 11, 21, 6):  "blank",   # 2Ch 15:8/34, was already blank both sides)
    ("Jdg", 11, 16, 3):  "blank",
    ("1Sa", 14, 50, 4):  "blank",   # "of Saul's" star slot, NO-FORM
    ("Heb", 11, 24, 8):  "blank",   # "of Pharaoh's" star slot, NO-FORM
    ("Num", 21, 25, 9):  "blank",   # live value was κατώκησεν (a verb) — cure
    ("Num", 25, 15, 5):  "blank",   # "of the Midianitish" — a people-word to the
                                    # eye but NOT to er.is_people_group, so the
                                    # build blanked it via the no-form path, not
                                    # the gentilic one; NO-FORM slot. Predicate
                                    # gap flagged to the gentilic follow-up —
                                    # never widened mid-lane (shared with build).
}
q = "SELECT verse_id, position, greek_strongs, greek_lemma, source FROM pn_greek_identity"
lrows = {(r[0], r[1]): (r[2], r[3], r[4]) for r in live.execute(q)}
srows = {(r[0], r[1]): (r[2], r[3], r[4]) for r in scr.execute(q)}
surf = {(r[0], r[1]): r[2] for r in scr.execute(
    "SELECT verse_id, position, form FROM abp_surface")}
vref = {r[0]: (r[1], r[2], r[3]) for r in
        live.execute("SELECT id, book, chapter, verse FROM verses")}
bad = []
counts = {"unchanged": 0, "pinned ruled loss": 0, "glued cure (blanked)": 0,
          "glued cure (replaced)": 0, "breathing": 0, "->surface (headword)": 0,
          "page-attested fallback": 0, "gentilic drop": 0}
glued_kept = 0
if set(lrows) != set(srows):
    bad.append(("KEYSET", len(set(lrows) ^ set(srows)), "keys added/removed"))
counts["bind-derived number"] = 0
for k in set(lrows) & set(srows):
    (lg, ll, ls), (sg, sl, ss) = lrows[k], srows[k]
    if lg != sg:
        # A number may APPEAR (never change or vanish) when it is bind-derived:
        # gate A proves pn_binding identical in both files, so a None->G row is
        # the stale live header table catching up with an already-shipped bind
        # (2026-07-30: 8× Saul from Lane C + 1× Zacharias from Lane B).
        if lg is None and sg and ss == "tipnr":
            counts["bind-derived number"] += 1; continue
        bad.append((k, f"{lg}->{sg}", "greek_strongs CHANGED")); continue
    if (ll, ls) == (sl, ss):
        counts["unchanged"] += 1
        if ll and "\xa0" in ll:
            glued_kept += 1
        continue
    refk = (*vref.get(k[0], ("?", 0, 0)), k[1])
    pin = PINNED_BRIDGE_FAIL.get(refk, PINNED_NOFORM_BLANK.get(refk))
    if pin is not None:
        ok_pin = (not sl) if pin == "blank" else ((sl, ss) == pin)
        if ok_pin:
            counts["pinned ruled loss"] += 1; continue
        bad.append((k, f"{ls}->{ss}",
                    f"PINNED member {refk} deviated: expected {pin!r}, "
                    f"got {sl!r}/{ss!r}"))
        continue
    if ll and "\xa0" in ll:                       # glued live value — cure class
        if not sl:
            counts["glued cure (blanked)"] += 1; continue
        if "\xa0" not in sl:
            counts["glued cure (replaced)"] += 1; continue
        bad.append((k, f"{ls}->{ss}",
                    f"glued value {ll!r} changed to ANOTHER glued value {sl!r}"))
        continue
    if ls == ss and ll and sl == fix_detached_breathing(ll) and sl != ll:
        counts["breathing"] += 1; continue
    page = fix_detached_breathing(surf.get(k) or "")
    if ss == "surface" and ls not in ("abp-tag", "tipnr") and sl:
        counts["->surface (headword)"] += 1; continue
    if sl and sl == page and ss in ("lemma-only", "abp-tag", "tipnr") and ls != "surface":
        counts["page-attested fallback"] += 1; continue
    if ss == "none" and not sl and ls == "lemma-only":
        lblrow = live.execute(
            "SELECT COALESCE(NULLIF(english_head,''), english) FROM words "
            "WHERE verse_id=? AND position=?", k).fetchone()
        lbl = (lblrow[0] if lblrow else "") or ""
        if er.is_people_group(er.norm_name(lbl)) or er.is_people_group(lbl):
            counts["gentilic drop"] += 1; continue
        bad.append((k, f"{ls}->{ss}",
                    f"dropped to none but label {lbl!r} is not a people-word"))
        continue
    bad.append((k, f"{ls}->{ss}", f"lemma {ll!r} -> {sl!r} outside the ruled classes"))
# Numeric pins (ruling 3) — armed only on a real transition run (a live-vs-live
# control has zero changed rows and must still PASS). Baseline pins for the
# 2026-08 header landing; re-pin on any future lane.
n_changed = len(set(lrows) & set(srows)) - counts["unchanged"]
if n_changed:
    for label, got, exp in (("pinned ruled loss", counts["pinned ruled loss"], 17),
                            ("glued cure (blanked)", counts["glued cure (blanked)"], 20),
                            ("glued cure (replaced)", counts["glued cure (replaced)"], 94),
                            ("glued kept as-is", glued_kept, 30)):
        if got != exp:
            bad.append(("PIN", label, f"expected {exp}, got {got}"))
okB = not bad
print(f"gate B: {'PASS' if okB else 'FAIL'} — " +
      ", ".join(f"{k} {v:,}" for k, v in counts.items())
      + (f"; VIOLATIONS {len(bad)}" if bad else ""))
print(f"    glued kept as-is (inside unchanged): {glued_kept}")
for b in bad[:8]:
    print(f"    problem: {b}")
if not okB:
    fails.append("B")

# ── optional gate-B full enumeration (HANDOFF_gateB_enumeration.md) ──────────
# Dumps EVERY problem row from the gate's own classifier (never a second copy),
# tagged with the NBSP glued-value probe on the LIVE lemma. Read-only.
if dump_path is not None:
    # CONTROL FIRST (audit-tools-must-fail): the NBSP probe must FIRE on the
    # known glued row (1Ki 11:17 slot 2) before any per-row flag is trusted.
    ctrl = live.execute(
        "SELECT g.greek_lemma FROM pn_greek_identity g "
        "JOIN verses v ON v.id=g.verse_id "
        "WHERE v.book='1Ki' AND v.chapter=11 AND v.verse=17 AND g.position=2"
    ).fetchone()
    ctrl_ok = bool(ctrl and ctrl[0] and "\xa0" in ctrl[0])
    print(f"dump control 1Ki 11:17 slot 2: live lemma = {ctrl[0] if ctrl else None!r} — "
          f"NBSP probe {'FIRED' if ctrl_ok else 'DID NOT FIRE — dump VOID'}")
    ref = vref
    n_nbsp = n_clean = 0
    with open(dump_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("# gate-B full problem dump (gate_greek_header.py --dump) — "
                "live_nbsp NBSP = glued live value (class-a candidate), "
                "CLEAN = class-b candidate, adjudicate before anything moves\n")
        f.write("ref\tpos\tenglish\tlive_lemma\tlive_source\t"
                "scr_lemma\tscr_source\tlive_nbsp\tnote\n")
        for only, keys in (("only-in-live", set(lrows) - set(srows)),
                           ("only-in-scratch", set(srows) - set(lrows))):
            for k in sorted(keys):
                b_, c_, v_ = ref.get(k[0], ("?", 0, 0))
                f.write(f"{b_} {c_}:{v_}\t{k[1]}\t\t\t\t\t\t\tKEYSET {only}\n")
        for k, trans, msg in bad:
            if not isinstance(k, tuple):
                continue                      # keyset summary — enumerated above
            lg, ll, ls = lrows[k]
            sg, sl, ss = srows.get(k, (None, None, None))
            eng = live.execute(
                "SELECT COALESCE(NULLIF(english_head,''), english) FROM words "
                "WHERE verse_id=? AND position=?", k).fetchone()
            b_, c_, v_ = ref.get(k[0], ("?", 0, 0))
            glued = bool(ll and "\xa0" in ll)
            n_nbsp += glued
            n_clean += not glued
            f.write(f"{b_} {c_}:{v_}\t{k[1]}\t{eng[0] if eng else ''}\t"
                    f"{ll or ''}\t{ls or ''}\t{sl or ''}\t{ss or ''}\t"
                    f"{'NBSP' if glued else 'CLEAN'}\t{msg}\n")
    print(f"dump: {len(bad)} problem rows -> {dump_path}; "
          f"live-NBSP (glued) {n_nbsp}, live-CLEAN {n_clean}"
          + ("" if ctrl_ok else "  [VOID — control did not fire]"))

# ── gate C — controls + pinned exact forms ───────────────────────────────────
okC = True
# The founding specimen. Receipt 2026-07-30 proved hadad is NOT uniform (5 ABP
# spellings), so under ruling (b) its correct outcome is the VERSE-FORM class:
# every hadad row Greek-headed (no 'none' left), each header = its own page form.
# A hadad row may stay English ONLY where the page itself prints no Greek form
# at that position (the honest no-data state, ruling 4). Rows WITH a page form
# must all be Greek-headed.
had = scr.execute(
    "SELECT sum(CASE WHEN (g.source='none' OR g.greek_lemma IS NULL OR g.greek_lemma='') "
    "           AND s.form IS NOT NULL AND s.form != '' THEN 1 ELSE 0 END), "
    "       sum(CASE WHEN g.source!='none' AND g.greek_lemma IS NOT NULL "
    "           AND g.greek_lemma != '' THEN 1 ELSE 0 END), count(*) "
    "FROM pn_greek_identity g "
    "JOIN words w ON w.verse_id=g.verse_id AND w.position=g.position "
    "JOIN verses v ON v.id=g.verse_id "
    "LEFT JOIN abp_surface s ON s.verse_id=g.verse_id AND s.position=g.position "
    "WHERE v.book='1Ki' AND v.chapter=11 AND w.is_pn=1 "
    "AND lower(COALESCE(NULLIF(w.english_head,''), w.english)) LIKE '%hadad%'").fetchone()
ok_had = had and had[2] and had[1] and had[0] == 0
print(f"gate C: hadad 1Ki 11 — Greek-headed {had[1]}/{had[2]}, "
      f"English-despite-page-form {had[0]} (must be 0): {'PASS' if ok_had else 'FAIL'}")
okC &= bool(ok_had)

pins = os.path.join(_HERE, "..", "docs", "tickets", "greek_header_pins.txt")
if os.path.isfile(pins):
    # Pin kinds (one per line):
    #   uniform|<name>|<exact form>   every source='surface' row for the name
    #                                 carries exactly this headword
    #   verse-form|<name>             every fallback row for the name equals its
    #                                 verse's own printed form (ruling (b))
    for ln in open(pins, encoding="utf-8"):
        if ln.startswith("#") or not ln.strip():
            continue
        parts = ln.rstrip("\n").split("|")
        kind, nm = parts[0], parts[1]
        rows_q = scr.execute(
            "SELECT g.verse_id, g.position, g.greek_lemma, g.source "
            "FROM pn_greek_identity g "
            "JOIN words w ON w.verse_id=g.verse_id AND w.position=g.position "
            "WHERE lower(COALESCE(NULLIF(w.english_head,''), w.english)) = ?",
            (nm.lower(),)).fetchall()
        if kind == "uniform":
            expect = parts[2]
            vals = sorted({r[2] for r in rows_q if r[3] == "surface"})
            ok = vals == [expect]
            print(f"gate C: pin uniform {nm} = {expect!r}: "
                  f"{'PASS' if ok else f'FAIL (got {vals})'}")
        elif kind == "verse-form":
            fb = [r for r in rows_q if r[3] == "lemma-only"]
            miss = [r for r in fb
                    if r[2] != fix_detached_breathing(surf.get((r[0], r[1])) or "")]
            ok = bool(fb) and not miss
            print(f"gate C: pin verse-form {nm}: {len(fb)} fallback rows, "
                  f"{'PASS' if ok else f'FAIL ({len(miss)} mismatch / none found)'}")
        else:
            ok = False
            print(f"gate C: pin UNKNOWN KIND {kind!r}: FAIL")
        okC &= ok
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
