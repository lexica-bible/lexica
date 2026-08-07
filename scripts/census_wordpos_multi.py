#!/usr/bin/env python3
"""census_wordpos_multi.py — READ-ONLY census of the word-position binding lane:
same-verse same-name multi slots (the ~118 class from the 2026-07-30 Jacob-class
census close, TODO_ARCHIVE; re-derived against the LIVE table because the charter
predates the 8/5 PN-star rebuild + the 8/7 lane-3 hand repairs).

CLASS PREDICATE (mirrors the census pipeline, not a new definition):
a slot is a member when
  - it is an identity slot (pn_greek_identity row with a words row),
  - its chip-order clicked name (english_head-first, production mirror) is
    non-empty and multi-referent (metaV+TIPNR test — the Jacob-class membership
    test from audit_pn_card_census.py / audit_pn_lanes.py), and
  - it is UNBOUND (no render bind for the name at the verse, exact or unique
    compact — classify() below is the same mirror as audit_pn_lanes.py), and
  - the SAME normalized name occupies >= 2 such slots in the SAME verse.
These are un-partitionable at the (book,ch,vs,name) bind key BY CONSTRUCTION.

SEPARATE BUCKET (reported, not counted in the lane figure): verses where 2+
slots carry the same name AND a render bind EXISTS for that name — the one bind
paints every same-name slot in the verse, which may be wrong for one of them.
The charter's ~118 were unbound-only; this bucket is sizing input for the
mechanism design, kept apart.

CONTROLS (fail-first rule): the known positive malchiah Ezr 10:25 (two
Malchiahs in the verse — DRILL_witness_divergence demotion record) must appear,
and the known-bound jesus Mat 8:5 must NOT. Either failing => exit 2, stop and
look.

Mirror functions copied from scripts/audit_pn_lanes.py (itself mirroring
audit_pn_card_census.py, commit 8bdda27d). READ-ONLY.
Usage: python3 scripts/census_wordpos_multi.py [bible.db]
"""
import sys, os, re, sqlite3
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import entity_resolution as er

DB = sys.argv[1] if len(sys.argv) > 1 else "bible.db"
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

# ── production mirrors (verbatim from audit_pn_lanes.py) ─────────────────────
_PN_STOP = {"And","But","Or","The","A","An","In","Of","To","For","With","From",
            "By","At","His","Her","Its","Their","My","Your","Our","O"}
_DIVINE_SKIP = {"LORD","Lord","YHWH","Yahweh","Jehovah","Holy"}

def pn_click_name(raw):
    raw = raw or ""
    if raw and " " not in raw:
        raw = raw[0].upper() + raw[1:]
    return raw

def extract_proper_name(gloss):
    if not gloss:
        return ""
    clean = re.sub(r"[^a-zA-Z\s'\-]", "", gloss).strip()
    for w in re.split(r"\s+", clean):
        if w and w[0].isupper() and w not in _PN_STOP:
            return w
    return ""

def compact(s):
    return (s or "").replace("-", "").replace(" ", "")

bound = set()
verse_binds = defaultdict(list)
for r in conn.execute("SELECT book, chapter, verse, name FROM pn_binding WHERE render=1"):
    k = (r["book"], r["chapter"], r["verse"])
    bound.add(k + (r["name"],))
    verse_binds[k].append(r["name"])

_multi_cache = {}
def name_is_multi_referent(name):
    if name not in _multi_cache:
        n = conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT person_id FROM metav_people        WHERE name  = ? COLLATE NOCASE
                UNION
                SELECT person_id FROM metav_people_aliases WHERE alias = ? COLLATE NOCASE
            )""", (name, name)).fetchone()[0]
        multi = n > 1
        if not multi:
            multi = conn.execute(
                "SELECT COUNT(*) FROM tipnr_entities WHERE section='person' "
                "AND (head = ? COLLATE NOCASE OR uniq LIKE ?)",
                (name, name + "@%")).fetchone()[0] > 1
        _multi_cache[name] = multi
    return _multi_cache[name]

def bind_state(nm, bk, ch, vs):
    """'bound' per the audit_pn_lanes classify() bind test, else 'unbound'."""
    bkey = er.norm_name(nm)
    k = (bk, ch, vs)
    if k + (bkey,) in bound:
        return "bound"
    cn = compact(bkey)
    hits = [x for x in verse_binds.get(k, ()) if compact(x) == cn]
    return "bound" if len(hits) == 1 else "unbound"

# ── walk the identity slots ─────────────────────────────────────────────────
rows = conn.execute("""
    SELECT g.verse_id, g.position, v.book AS book, v.chapter AS ch,
           v.verse AS vs, w.english, w.english_head
    FROM pn_greek_identity g
    JOIN verses v ON v.id = g.verse_id
    JOIN words w ON w.verse_id = g.verse_id AND w.position = g.position
""").fetchall()

groups = defaultdict(list)   # (abbrev, bk_num, ch, vs, norm_name) -> slot rows
for r in rows:
    bk = er.book_num(r["book"])
    if bk is None:
        continue
    n1 = extract_proper_name(pn_click_name(r["english_head"] or r["english"] or ""))
    if not n1 or len(n1) < 2 or n1 in _DIVINE_SKIP:
        continue
    if not name_is_multi_referent(n1):
        continue
    nm = er.norm_name(n1)
    if not nm:
        continue
    groups[(r["book"], bk, r["ch"], r["vs"], nm)].append(r["position"])

lane, painted = [], []       # unbound multi-groups / bound-painted multi-groups
for key, positions in sorted(groups.items()):
    if len(positions) < 2:
        continue
    ab, bk, ch, vs, nm = key
    state = bind_state(nm, bk, ch, vs)
    (lane if state == "unbound" else painted).append((ab, ch, vs, nm, sorted(positions)))

# ── report ──────────────────────────────────────────────────────────────────
n_slots = sum(len(p) for *_, p in lane)
n_verses = len({(a, c, v) for a, c, v, *_ in lane})
n_names = len({nm for *_, nm, _ in lane})
print("═══ WORD-POSITION LANE CENSUS — same-verse same-name multi (UNBOUND) ═══")
print(f"lane figure: {n_slots} slots / {len(lane)} (verse,name) groups / "
      f"{n_verses} verses / {n_names} names")
roll = Counter()
for *_, nm, p in lane:
    roll[nm] += len(p)
print("\nper-name rollup (name: slots):")
for nm, n in roll.most_common():
    print(f"  {nm:20s} {n:4d}")
print("\nfull member list (book ch:vs  name  positions):")
for ab, ch, vs, nm, p in lane:
    print(f"  {ab} {ch}:{vs}  {nm:20s} p{p}")

pn_slots = sum(len(p) for *_, p in painted)
print(f"\n═══ SEPARATE BUCKET — bound-PAINTED same-name multi (not in the lane figure) ═══")
print(f"{pn_slots} slots / {len(painted)} groups — a render bind exists and paints "
      f"every same-name slot in the verse")
for ab, ch, vs, nm, p in painted:
    print(f"  {ab} {ch}:{vs}  {nm:20s} p{p}")

# ── controls (fail-first) ───────────────────────────────────────────────────
pos_ok = any(ab == "Ezr" and ch == 10 and vs == 25 and nm == "malchiah"
             for ab, ch, vs, nm, _ in lane)
neg_ok = not any(ab == "Mat" and ch == 8 and vs == 5 and nm == "jesus"
                 for ab, ch, vs, nm, _ in lane + painted)
print("\n═══ CONTROLS ═══")
print(f"known positive malchiah Ezr 10:25 present : {'OK' if pos_ok else 'CONTROL FAIL'}")
print(f"known negative jesus Mat 8:5 absent       : {'OK' if neg_ok else 'CONTROL FAIL'}")
if not (pos_ok and neg_ok):
    print("CONTROL FAIL — census output is NOT trustworthy; stop and look.")
    sys.exit(2)
