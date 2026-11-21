"""P7 check program (edition-upgrade step 8, plan P7; DESIGN 9.213 Q9, 9.222 (5), 9.223). READ-ONLY on both files.

Run by block P7 through the read-once launcher (DESIGN 9.190 (5)(b)), arguments KEY=value:
  LIVE=<bible.db, the swapped-in file>  RB=<the rollback file = live as it was just before the swap>  REPO=<checkout>
Both are opened mode=ro + query_only (eu_step.ro, and mode=ro ATTACH). It writes nothing.
The log gets table names, row counts, digests, verse references, positions and the class / source labels only.

  (1) the lane's tables on live now: rows + digest (eu_step.digest). Gated where the record holds built's value:
      words 626309 / d95acb5d4be4 and abp_corrections 404 / d97d928ca7f5 (DESIGN 9.212), abp_surface 395014 /
      219a3ebe7075 (DESIGN 9.130; P4's line, DR "### P4 RULED" item (7)). The rest are read-outs.
  (2) G5, the rollback file -> live (DESIGN 9.222 (5): P4's figures "live copy -> built", accepted as P7's expected
      figures, with "surface" where P4 printed "other", DESIGN 9.223): pn_hebrew_xref, pn_greek_identity, name-slot
      strongs_base. A figure that differs is a FINDING.
  (3) the pn_hebrew_xref rows whose class moved, by key, set against DESIGN 9.95's six verses (DESIGN 9.223):
      a different member is a FINDING. The keys on one side only are printed as read-outs beside REKEY's record
      (DR "REKEY ... ACCEPTED").
Exit 0 = READ (every gated figure held), 3 = FINDINGS (listed), 2 = STOP (could not read).
"""
import os
import re
import sqlite3
import sys
from collections import Counter

args = dict(a.split("=", 1) for a in sys.argv[1:])
LIVE, RB, REPO = args["LIVE"], args["RB"], args["REPO"]
sys.path.insert(0, os.path.join(REPO, "scripts"))
import eu_step as E  # noqa: E402  (the lane's own reader + digest; never a copy)

BUILT = {"words": (626309, "d95acb5d4be4"), "abp_corrections": (404, "d97d928ca7f5"), "abp_surface": (395014, "219a3ebe7075")}
READOUT = ("verses", "pn_hebrew_xref", "pn_greek_identity", "pn_binding", "pn_slot_binding", "tipnr_metav_link", "word_gloss")
CLASS = ("abp-tag", "tipnr", "lemma-only", "surface", "none")   # build_pn_greek_identity.py :410, :496 (the five labels)
G5 = {   # DESIGN 9.222 (5); the seven source moves from P4's log with "surface" for "other" (DESIGN 9.223)
    "pn_hebrew_xref": {"changed": 6, "bycol": {"class": 6}, "moves": {"none -> lemma-only": 6}, "before": 6, "after": 6},
    "pn_greek_identity": {"changed": 57, "bycol": {"greek_lemma": 9, "greek_strongs": 9, "source": 57},
                          "moves": {"surface -> lemma-only": 33, "lemma-only -> surface": 6, "none -> surface": 6,
                                    "surface -> tipnr": 6, "lemma-only -> tipnr": 3, "none -> lemma-only": 2,
                                    "lemma-only -> none": 1}, "before": 6, "after": 6},
}
SLOT = {"n": 18, "shapes": {"* -> G": 3, "G -> *": 3, "G -> G": 6, "H -> *": 6}}                # DESIGN 9.222 (5)
SIX = {("Num", 21, 25), ("1Sa", 20, 37), ("2Sa", 15, 6), ("Jer", 48, 15), ("Jer", 48, 20), ("Jer", 49, 3)}   # DESIGN 9.95, 9.223
REKEY = {("2Ki", 23, 35, 6), ("Est", 5, 9, 12), ("Gen", 5, 25, 1), ("Gen", 5, 26, 1), ("Gen", 34, 4, 1), ("Jos", 5, 15, 27)}  # DR REKEY
findings = []


def lab(v):
    return v if v in CLASS else ("NULL" if v is None else "other")


def shape(v):
    if v is None:
        return "NULL"
    if v == "*":
        return "*"
    if re.fullmatch(r"H\d+(\.\d+)?", v):
        return "H"
    if re.fullmatch(r"G\d+(\.\d+)?", v):
        return "G"
    return "other"


def cnt(d):
    return ", ".join("%s %d" % kv for kv in sorted(d.items())) or "none"


def gate(what, got, want):
    ok = got == want
    print("    %s: %s" % (what, "as expected" if ok else "NOT AS EXPECTED - expected %s" % (want,)))
    if not ok:
        findings.append("%s: got %s, expected %s" % (what, got, want))


try:
    live, rb = E.ro(LIVE), E.ro(RB)
except E.Stop as e:
    print("P7 STOP: %s" % e)
    sys.exit(2)

print("=== (1) the lane's tables on live now: rows / digest (first 12) ===")
tabs = E.plain_tables(live)[0]
for t in list(BUILT) + list(READOUT):
    if t not in tabs:
        print("  %-20s MISSING on live" % t)
        findings.append("table %s missing on live" % t)
        continue
    n, d = E.digest(live, t)
    if t in BUILT:
        ok = (n, d[:12]) == BUILT[t]
        print("  %-20s %d / %s (expect %d / %s, built's value on record): %s" % (t, n, d[:12], BUILT[t][0], BUILT[t][1], "yes" if ok else "NO"))
        if not ok:
            findings.append("live %s is %d / %s, built's on record is %d / %s" % (t, n, d[:12], BUILT[t][0], BUILT[t][1]))
    else:
        print("  %-20s %d / %s (a read-out)" % (t, n, d[:12]))
rb.close()

mem = sqlite3.connect("file::memory:", uri=True, timeout=60)   # wait up to 60 s on a site worker's write (eu_step.ro waits the same)
mem.text_factory = E.text
mem.execute("ATTACH DATABASE ? AS o", ("file:%s?mode=ro" % RB,))     # o = the rollback file (old live)
mem.execute("ATTACH DATABASE ? AS n", ("file:%s?mode=ro" % LIVE,))   # n = live now
mem.execute("PRAGMA query_only=1")


def ref(vid, db):
    r = mem.execute("SELECT book, chapter, verse FROM %s.verses WHERE id = ?" % db, (vid,)).fetchone()
    return tuple(r) if r else ("?", vid, 0)


def fmt(k):
    return "%s %s:%s @%s" % k


print("=== (2) G5 - the rollback file -> live (expected: DESIGN 9.222 (5), labels per 9.223) ===")
vo = mem.execute("SELECT count(*) FROM o.verses").fetchone()[0]
vn = mem.execute("SELECT count(*) FROM n.verses").fetchone()[0]
vm = mem.execute("SELECT count(*) FROM o.verses x JOIN n.verses y ON x.id = y.id AND x.book IS y.book AND x.chapter IS y.chapter "
                 "AND x.verse IS y.verse").fetchone()[0]
print("  every verse id names the same (book, chapter, verse) on both files: old %d, live %d, matched %d: %s"
      % (vo, vn, vm, "yes" if vo == vn == vm else "NO"))
if not vo == vn == vm:
    findings.append("verse ids do not all name the same verse on the rollback file and live: %d / %d / %d" % (vo, vn, vm))
keys = {}
for t, f in (("pn_hebrew_xref", "class"), ("pn_greek_identity", "source")):
    if not all(mem.execute("SELECT 1 FROM %s.sqlite_master WHERE type='table' AND name=?" % z, (t,)).fetchone() for z in ("o", "n")):
        print("  %s: missing on a side" % t)
        findings.append("%s missing on a side" % t)
        continue
    before = mem.execute("SELECT p.verse_id, p.position FROM o.%s p LEFT JOIN n.%s q ON p.verse_id = q.verse_id AND p.position = q.position "
                         "WHERE q.verse_id IS NULL ORDER BY 1, 2" % (t, t)).fetchall()
    after = mem.execute("SELECT q.verse_id, q.position FROM n.%s q LEFT JOIN o.%s p ON p.verse_id = q.verse_id AND p.position = q.position "
                        "WHERE p.verse_id IS NULL ORDER BY 1, 2" % (t, t)).fetchall()
    cols_ = [c for c in E.cols(live, t) if c not in ("verse_id", "position")]
    ch = mem.execute("SELECT p.verse_id, p.position, %s FROM o.%s p JOIN n.%s q ON p.verse_id = q.verse_id AND p.position = q.position "
                     "WHERE %s ORDER BY 1, 2" % (", ".join("p.%s, q.%s" % (E.q(c), E.q(c)) for c in cols_), t, t,
                                                 " OR ".join("p.%s IS NOT q.%s" % (E.q(c), E.q(c)) for c in cols_))).fetchall()
    bycol, tr, moved = Counter(), Counter(), []
    fi = cols_.index(f)
    for r in ch:
        v = r[2:]
        for i, c in enumerate(cols_):
            if v[2 * i] != v[2 * i + 1]:
                bycol[c] += 1
        if v[2 * fi] != v[2 * fi + 1]:
            tr["%s -> %s" % (lab(v[2 * fi]), lab(v[2 * fi + 1]))] += 1
            moved.append((r[0], r[1], lab(v[2 * fi]), lab(v[2 * fi + 1])))
    print("  %s: rows changed %d (by column: %s); %s -> %s: %s; keys only before %d, only after %d"
          % (t, len(ch), cnt(bycol), f, f, cnt(tr), len(before), len(after)))
    x = G5[t]
    gate("%s rows changed" % t, len(ch), x["changed"])
    gate("%s by column" % t, dict(bycol), x["bycol"])
    gate("%s %s moves" % (t, f), dict(tr), x["moves"])
    gate("%s keys only before / only after" % t, (len(before), len(after)), (x["before"], x["after"]))
    keys[t] = (before, after, moved)
rows = mem.execute("SELECT p.strongs_base, q.strongs_base FROM o.words p JOIN n.words q ON p.verse_id = q.verse_id "
                   "AND p.position = q.position WHERE p.strongs_base IS NOT q.strongs_base AND (p.is_pn = 1 OR q.is_pn = 1)").fetchall()
sh = Counter("%s -> %s" % (shape(a), shape(b)) for a, b in rows)
print("  name-slot strongs_base (is_pn = 1 on either side) changed: %d (%s)" % (len(rows), cnt(sh)))
gate("name-slot strongs_base changed", len(rows), SLOT["n"])
gate("name-slot strongs_base by shape", dict(sh), SLOT["shapes"])

print("=== (3) the keys (DESIGN 9.223) ===")
if "pn_hebrew_xref" in keys:
    before, after, moved = keys["pn_hebrew_xref"]
    print("  pn_hebrew_xref rows whose class moved (%d), verse @position, old -> new:" % len(moved))
    got = set()
    for vid, pos, a, b in moved:
        r = ref(vid, "n")
        got.add(r)
        print("    %s: %s -> %s" % (fmt(r + (pos,)), a, b))
    print("  DESIGN 9.95's six verses: %s" % ", ".join("%s %s:%s" % k for k in sorted(SIX)))
    gate("the class-moved rows' verses = 9.95's six", sorted(got), sorted(SIX))
for t in ("pn_hebrew_xref", "pn_greek_identity"):
    if t not in keys:
        continue
    before, after, _ = keys[t]
    b_ = [ref(v, "o") + (p,) for v, p in before]
    a_ = [ref(v, "n") + (p,) for v, p in after]
    print("  %s keys only on the rollback file (a read-out): %s" % (t, "; ".join(fmt(k) for k in b_) or "none"))
    print("  %s keys only on live (a read-out): %s" % (t, "; ".join(fmt(k) for k in a_) or "none"))
    print("    = the six places REKEY's record names (2Ki 23:35 @6, Est 5:9 @12, Gen 5:25 @1, Gen 5:26 @1, Gen 34:4 @1, Jos 5:15 @27):"
          " %s (a read-out, not gated)" % ("yes" if set(a_) == REKEY else "no"))
mem.close()
live.close()

print("=== findings ===")
for x in findings:
    print("  FINDING: %s" % x)
print("P7 CHECK: %s - findings %d" % ("READ" if not findings else "FINDINGS", len(findings)))
sys.exit(3 if findings else 0)
