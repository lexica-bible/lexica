#!/usr/bin/env python3
"""screen_lane_c.py — Lane C hardened candidacy screen (reviewer-approved
2026-07-30, DRILL_lane_c.md). LOCAL, read-only, pinned-TIPNR only.

Emits the per-name census for the run audit. The screen produces CANDIDATES,
never identities (hardening 1): a slot only ever lands via the per-name audit.

Checks per slot:
  filter    exactly ONE of the name's candidates has coverage in the chapter
  compound  a TIPNR combined form contains the name as an element AND that
            compound's entity covers the verse or an adjacent verse -> routed
            OUT to the compound lane (hardening 2; kills the Gilboa shape)
  referent  any OTHER entity covers the exact verse -> flagged for the audit
  type      candidate's TIPNR section, printed as audit data
Per name: genre-crossing flag (slots span >1 canon group -> every-slot audit).

CONTROL (runs first, hard assert): gilead 1Ch 10:12 and 1Sa 31:11 must NOT
pass (Jabesh-gilead fragments in Mount-Gilboa chapters).

Usage: python scripts/screen_lane_c.py > docs/tickets/lane_c_census.txt
"""
import sys, os, re, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import entity_resolution as er

lines = open(os.path.join(HERE, "tipnr", "TIPNR.txt"), encoding="utf-8-sig").read().splitlines()
ents = er.parse_tipnr(lines)
name_idx, base_idx, compact_idx = er.build_indexes(ents)
cover = collections.defaultdict(list)
for e in ents:
    for ref in e["refs"]:
        cover[ref].append(e)

# combined forms: element token -> [(compound entity, form)]
def norm_tok(t):
    return re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", t).lower()

comp_elem = collections.defaultdict(list)
cur = None
for ln in lines:
    parts = ln.rstrip("\n").split("\t")
    if not parts[0].startswith("–"):
        m = re.match(r"^([^\t=]+@[^\t=]+)=", parts[0])
        cur = m.group(1).strip() if m else None
        continue
    if cur is None or len(parts) < 2:
        continue
    sig = parts[0].lstrip("–").strip().lower()
    unique = parts[1].strip()
    if "combined" in sig and "@" in unique:
        form = unique.split("|")[0].split("@")[0].strip()
        uniq = unique.split("|")[1].strip() if "|" in unique else cur
        for tok in re.split(r"[-\s/_]+", form):
            t = norm_tok(tok)
            if t:
                comp_elem[t].append((uniq, form))

byuniq = {e["uniq"]: e for e in ents}

GROUPS = [(1,5,"law"),(6,17,"history"),(18,22,"wisdom"),(23,39,"prophets"),
          (40,43,"gospels"),(44,44,"acts"),(45,65,"epistles"),(66,66,"rev")]
def group(bk):
    return next(g for lo,hi,g in GROUPS if lo<=bk<=hi)

def screen(nm, bk, ch, vs):
    """-> (status, detail). status: PASS-candidate / COMPOUND-ROUTE / MULTI / ZERO"""
    ref = (bk, ch, vs)
    # compound screen first (hardening 2)
    for uniq, form in comp_elem.get(er.norm_name(nm), []):
        e = byuniq.get(uniq)
        if e and any(r[0]==bk and r[1]==ch and abs(r[2]-vs)<=1 for r in e["refs"]):
            return ("COMPOUND-ROUTE", f"{form} ({uniq}) covers {bk}:{ch} within 1 verse")
    cs = [ents[i] for i in name_idx.get(er.norm_name(nm), set())]
    in_ch = [e for e in cs if any(r[0]==bk and r[1]==ch for r in e["refs"])]
    if len(in_ch) > 1:
        return ("MULTI", [e["uniq"] for e in in_ch])
    if not in_ch:
        return ("ZERO", None)
    e = in_ch[0]
    others = [o["uniq"] for o in cover.get(ref, []) if o["uniq"] != e["uniq"]]
    return ("PASS-candidate",
            f"{e['uniq']} [{e['section'] or '?'}]"
            + (f" | other-entities-at-verse: {others}" if others else ""))

# ── CONTROL: the Gilboa known-negatives must NOT pass ────────────────────────
for bk_s, ch, vs in (("1Ch",10,12), ("1Sa",31,11)):
    st, d = screen("gilead", er.book_num(bk_s), ch, vs)
    assert st != "PASS-candidate", f"CONTROL FAILED: gilead {bk_s} {ch}:{vs} passed ({d})"
    print(f"# CONTROL OK: gilead {bk_s} {ch}:{vs} -> {st} ({d})")

slots = collections.defaultdict(list)
for ln in open(os.path.join(HERE, "docs", "tickets", "witness_census_lanes.txt"), encoding="utf-8"):
    if ln.startswith("#") or not ln.strip():
        continue
    lane, nm, bk_s, ch, vs, detail = ln.rstrip("\n").split("|")[:6]
    if lane == "C":
        slots[nm].append((bk_s, er.book_num(bk_s), int(ch), int(vs)))

print(f"# Lane C hardened screen — {sum(len(v) for v in slots.values())} slots, "
      f"{len(slots)} names. PASS-candidate = audit input, NEVER a bind.")
tot = collections.Counter()
for nm in sorted(slots, key=lambda n: -len(slots[n])):
    rows = slots[nm]
    genres = {group(bk) for _, bk, _, _ in rows}
    flag = " GENRE-CROSSING(every-slot audit)" if len(genres) > 1 else ""
    print(f"\n== {nm} ({len(rows)} slots, genres: {'/'.join(sorted(genres))}){flag}")
    for bk_s, bk, ch, vs in sorted(rows, key=lambda r: (r[1], r[2], r[3])):
        st, d = screen(nm, bk, ch, vs)
        tot[st] += 1
        print(f"   {st:15s} {bk_s} {ch}:{vs}  {d if d else ''}")
print(f"\n# totals: {dict(tot)}")
