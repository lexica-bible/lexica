#!/usr/bin/env python3
"""audit_pn_lanes.py — READ-ONLY dumps for the four PN-card cleanup lanes
(2026-07-29 session brief; follows audit_pn_card_census.py, commit 8bdda27d).

Lane 1  DUMP the sensitivity slots: identity slots whose card classification
        differs between the chip click path (english_head-first raw) and the
        prose click path (english-first raw). For each: both raws, both
        extracted names, both classifications, and WHICH order agrees with a
        live bind — the fix evidence.
Lane 2  DIAGNOSE the no-words-row slots: pn_greek_identity rows whose
        (verse_id, position) has no words row. Breakdown by book / identity
        source / cause bucket (verse has no words at all vs position beyond
        the verse's last word vs position-hole).
Lane 3  RANK the unknown names (bin b:no-match): top 50 by occurrence with a
        sample ref each, pre-classified: (a) compact/hyphen near-miss against
        a metaV name or alias (alias-gap candidate) · (g) gentilic/group form
        · (c) absent from metaV+TIPNR.
Lane 4  Jacob-class scope refresh: census multi-referent names with occurrence
        count, candidate count, books spanned, and an all-one-book flag (the
        zero-research-resolvable hint). Plus the 694-vs-624 reconciliation
        inputs: both definitions counted on tonight's data.

READ-ONLY. Usage: python3 scripts/audit_pn_lanes.py [bible.db]
"""
import sys, os, re, sqlite3
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import entity_resolution as er

DB = sys.argv[1] if len(sys.argv) > 1 else "bible.db"
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

# ── frontend mirrors (same as the census script) ─────────────────────────────
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

def person_exists_exact(name):
    return conn.execute("""
        SELECT 1 FROM metav_people WHERE name = ? COLLATE NOCASE
        UNION SELECT 1 FROM metav_people_aliases WHERE alias = ? COLLATE NOCASE
        LIMIT 1""", (name, name)).fetchone() is not None

def best_person_card(name):
    row = conn.execute("""
        SELECT * FROM (
            SELECT p.person_id, p.birth_year, p.death_year FROM metav_people p
            WHERE p.name = ? COLLATE NOCASE
            UNION
            SELECT p.person_id, p.birth_year, p.death_year FROM metav_people p
            JOIN metav_people_aliases a ON a.person_id = p.person_id
            WHERE a.alias = ? COLLATE NOCASE)
        ORDER BY (birth_year IS NOT NULL) DESC, (death_year IS NOT NULL) DESC
        LIMIT 1""", (name, name)).fetchone()
    if not row and len(name) >= 5:
        prefix = name[:max(5, len(name) - 2)]
        row = conn.execute("""
            SELECT * FROM (
                SELECT p.person_id, p.birth_year, p.death_year FROM metav_people p
                WHERE p.name LIKE ? COLLATE NOCASE AND length(p.name) BETWEEN ? AND ?
                UNION
                SELECT p.person_id, p.birth_year, p.death_year FROM metav_people p
                JOIN metav_people_aliases a ON a.person_id = p.person_id
                WHERE a.alias LIKE ? COLLATE NOCASE AND length(a.alias) BETWEEN ? AND ?)
            ORDER BY (birth_year IS NOT NULL) DESC, (death_year IS NOT NULL) DESC
            LIMIT 1""", (f"{prefix}%", len(name)-2, len(name)+2,
                         f"{prefix}%", len(name)-2, len(name)+2)).fetchone()
    return row

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

def person_candidates(name):
    n = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT person_id FROM metav_people        WHERE name  = ? COLLATE NOCASE
            UNION
            SELECT person_id FROM metav_people_aliases WHERE alias = ? COLLATE NOCASE
        )""", (name, name)).fetchone()[0]
    t = conn.execute(
        "SELECT COUNT(*) FROM tipnr_entities WHERE section='person' "
        "AND (head = ? COLLATE NOCASE OR uniq LIKE ?)",
        (name, name + "@%")).fetchone()[0]
    return n, t

def place_card_exists(name):
    return conn.execute("""
        SELECT 1 FROM metav_places p WHERE p.name = ? COLLATE NOCASE
        UNION
        SELECT 1 FROM metav_places p
        JOIN metav_place_aliases a ON a.place_id = p.place_id
        WHERE a.alias = ? COLLATE NOCASE LIMIT 1""", (name, name)).fetchone() is not None

def rel_count(pid):
    return conn.execute(
        "SELECT COUNT(*) FROM metav_people_relationships WHERE person_id=?",
        (pid,)).fetchone()[0]

_card_cache = {}
def name_card(name):
    if name in _card_cache:
        return _card_cache[name]
    out = ""
    if name and len(name) >= 2 and name not in _DIVINE_SKIP:
        prow = best_person_card(name)
        person_ok = False
        if prow is not None and not name_is_multi_referent(name):
            person_ok = bool(prow["birth_year"] or prow["death_year"]
                             or rel_count(prow["person_id"]) >= 2)
        if person_ok:
            out = "person"
        elif place_card_exists(name):
            out = "place"
    _card_cache[name] = out
    return out

def classify(nm, bk, ch, vs):
    if not nm or len(nm) < 2 or bk is None:
        return "b:no-name"
    bkey = er.norm_name(nm)
    k = (bk, ch, vs)
    if k + (bkey,) in bound:
        return "bound"
    cn = compact(bkey)
    hits = [x for x in verse_binds.get(k, ()) if compact(x) == cn]
    if len(hits) == 1:
        return "bound"
    card = name_card(nm)
    if card:
        return "a:" + card
    return "b:divine" if nm in _DIVINE_SKIP else "b:no-match"

rows = conn.execute("""
    SELECT g.verse_id, g.position, g.source, v.book AS book, v.chapter AS ch,
           v.verse AS vs, w.english, w.english_head
    FROM pn_greek_identity g
    JOIN verses v ON v.id = g.verse_id
    LEFT JOIN words w ON w.verse_id = g.verse_id AND w.position = g.position
""").fetchall()

# ═══ LANE 1 — chip-vs-prose divergent slots ══════════════════════════════════
print("═══ LANE 1 — chip-vs-prose divergent slots ═══")
lane1 = []
unknown = Counter()          # lane-3 feed: b:no-match names (chip order)
unknown_sample = {}
multi_slots = Counter()      # lane-4 feed: multi-referent unbound name -> slots
multi_refs = defaultdict(set)
for r in rows:
    bk = er.book_num(r["book"])
    raw_chip = r["english_head"] or r["english"] or ""
    raw_prose = r["english"] or r["english_head"] or ""
    n1 = extract_proper_name(pn_click_name(raw_chip))
    c1 = classify(n1, bk, r["ch"], r["vs"])
    if raw_prose != raw_chip:
        n2 = extract_proper_name(pn_click_name(raw_prose))
        c2 = classify(n2, bk, r["ch"], r["vs"])
        if c1.split(":")[0] != c2.split(":")[0]:
            lane1.append((r["book"], r["ch"], r["vs"], r["position"],
                          raw_chip, n1, c1, raw_prose, n2, c2))
    if c1 == "b:no-match":
        nm = er.norm_name(n1)
        unknown[nm] += 1
        unknown_sample.setdefault(nm, f'{r["book"]} {r["ch"]}:{r["vs"]}')
    if not c1.startswith("bound") and n1:
        nm = er.norm_name(n1)
        if nm and name_is_multi_referent(n1):
            multi_slots[nm] += 1
            multi_refs[nm].add(r["book"])

print(f"divergent slots: {len(lane1)}")
chip_bound = sum(1 for x in lane1 if x[6] == "bound")
prose_bound = sum(1 for x in lane1 if x[9] == "bound")
print(f"  chip-order lands BOUND : {chip_bound}")
print(f"  prose-order lands BOUND: {prose_bound}")
print("  (whichever order agrees with the verified bind more often is the right raw)")
print("  book ch:vs pos | chip_raw -> name -> class | prose_raw -> name -> class")
for b, ch, vs, pos, rc, n1, c1, rp, n2, c2 in lane1:
    print(f"  {b} {ch}:{vs} p{pos} | {rc!r} -> {n1 or '-'} -> {c1} | {rp!r} -> {n2 or '-'} -> {c2}")

# ═══ LANE 2 — no-words-row slots ═════════════════════════════════════════════
print("\n═══ LANE 2 — identity slots with no words row (diagnosis only) ═══")
nw = [r for r in rows if r["english"] is None and r["english_head"] is None]
print(f"total: {len(nw)}")
by_book, by_src, by_cause = Counter(), Counter(), Counter()
samples = []
for r in nw:
    by_book[r["book"]] += 1
    by_src[r["source"] or "?"] += 1
    x = conn.execute("SELECT count(*) AS n, max(position) AS mx FROM words "
                     "WHERE verse_id = ?", (r["verse_id"],)).fetchone()
    if x["n"] == 0:
        cause = "verse-has-NO-words-rows"
    elif r["position"] > (x["mx"] if x["mx"] is not None else -1):
        cause = "position-beyond-last-word"
    else:
        cause = "position-hole-inside-verse"
    by_cause[cause] += 1
    if len(samples) < 12:
        samples.append((r["book"], r["ch"], r["vs"], r["position"],
                        r["source"], x["n"], x["mx"], cause))
print("by cause :", dict(by_cause))
print("by source:", dict(by_src))
print("by book  :", dict(by_book.most_common(15)))
print("samples (book ch:vs pos source verse-words max-pos cause):")
for s in samples:
    print("  ", s)

# ═══ LANE 3 — unknown names, top 50 pre-classified ═══════════════════════════
print("\n═══ LANE 3 — b:no-match names, top 50 by occurrence ═══")
# compact map of every metaV name+alias for the near-miss test
compact_names = {}
for tbl, col, kind in (("metav_people","name","person"), ("metav_people_aliases","alias","person"),
                       ("metav_places","name","place"), ("metav_place_aliases","alias","place")):
    for r in conn.execute(f"SELECT {col} AS n FROM {tbl} WHERE {col} IS NOT NULL"):
        compact_names.setdefault(compact(r["n"]).lower(), (r["n"], kind))
print(f"distinct unknown names: {len(unknown):,} · total slots: {sum(unknown.values()):,}")
print("class: a=alias-gap candidate (compact match to a metaV name/alias) · g=gentilic/group · c=absent")
print(f"{'name':22s} {'slots':>5s}  cls  match/sample")
for nm, n in unknown.most_common(50):
    cm = compact_names.get(compact(nm).lower())
    if cm:
        cls, extra = "a", f"metaV {cm[1]} '{cm[0]}'"
    elif er.is_people_group(nm):
        cls, extra = "g", ""
    else:
        cls, extra = "c", ""
    print(f"{nm:22s} {n:5,d}   {cls}   {extra}  [{unknown_sample[nm]}]")
cls_tot = Counter()
for nm, n in unknown.items():
    cm = compact_names.get(compact(nm).lower())
    cls_tot["a" if cm else ("g" if er.is_people_group(nm) else "c")] += n
print(f"slot totals by class: {dict(cls_tot)}")

# ═══ LANE 4 — Jacob-class scope refresh ══════════════════════════════════════
print("\n═══ LANE 4 — multi-referent unbound names (scope refresh, no builds) ═══")
print(f"census definition (identity slots, metaV+TIPNR multi test): "
      f"{len(multi_slots)} names / {sum(multi_slots.values())} slots")
# the 2026-07-11 Jacob-class definition: is_pn words, metaV-multi only
person_ids = defaultdict(set)
for r in conn.execute("SELECT person_id, name FROM metav_people WHERE name IS NOT NULL"):
    person_ids[er.norm_name(r["name"])].add(r["person_id"])
for r in conn.execute("SELECT person_id, alias FROM metav_people_aliases WHERE alias IS NOT NULL"):
    person_ids[er.norm_name(r["alias"])].add(r["person_id"])
amb_old = {n for n, ids in person_ids.items() if len(ids) > 1}
jc = 0
for r in conn.execute("""
    SELECT v.book AS book, v.chapter AS ch, v.verse AS vs,
           COALESCE(NULLIF(w.english_head,''), w.english) AS label
    FROM words w JOIN verses v ON v.id = w.verse_id WHERE w.is_pn = 1"""):
    nm = er.norm_name(r["label"])
    bk = er.book_num(r["book"])
    if not nm or bk is None:
        continue
    if (bk, r["ch"], r["vs"], nm) not in bound and nm in amb_old:
        jc += 1
print(f"2026-07-11 definition re-run tonight (is_pn words, metaV-only multi): {jc} slots")
print("(the 694 vs 624 gap = definitional: word-set + which multi test — both shown above)")
print(f"\ntop 20 by unbound slots (mv=metaV candidates, tp=TIPNR person entities, "
      f"books=distinct books, ONE-BOOK flag = zero-research-resolvable HINT, not a ruling):")
print(f"{'name':16s} {'slots':>5s} {'mv':>3s} {'tp':>3s} {'books':>5s}  flag")
for nm, n in multi_slots.most_common(20):
    mv, tp = person_candidates(nm)
    nb = len(multi_refs[nm])
    flag = "ONE-BOOK" if nb == 1 else ""
    print(f"{nm:16s} {n:5,d} {mv:3d} {tp:3d} {nb:5d}  {flag}")
