#!/usr/bin/env python3
"""audit_pn_biobar.py — READ-ONLY sizing of the Paul-class: unbound PN slots whose
name matches a metaV person exactly (or hyphen-blind) but serves NO card because the
bio quality bar rejects the skeleton entry (no birth/death year, <2 family links).

Splits every b:no-match slot (post-lane-1 logic: english_head-first name, hyphen-blind
lookups) by WHY it has no card:
    bio-bar        exact/compact person hit, single-referent, fails the bio bar
    fuzzy-bio-bar  only a fuzzy-prefix hit exists, and it fails the bar too
    multi-referent several people share the name -> deliberate decline (Jacob-class)
    gentilic       people-group surface form
    absent         no person/place row under any matching tier

For the top 20 bio-bar names: what metaV DOES hold (gender, dates, places, kin count,
groups count) + whether TIPNR has a single person entity with a real description —
the raw material any slim-card design would render. Full detail block for Paul.

Control: 'Paul' must classify bio-bar (exact metaV hit, no card) — aborts otherwise.

READ-ONLY. Usage: python3 scripts/audit_pn_biobar.py [bible.db]
"""
import sys, os, re, sqlite3
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import entity_resolution as er

DB = sys.argv[1] if len(sys.argv) > 1 else "bible.db"
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

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

_PERSON_SEL = "p.person_id, p.name, p.gender, p.birth_year, p.death_year, p.birth_place, p.death_place"

def person_lookup(name):
    """(row, tier, guard_name): tier in exact|compact|fuzzy|none. Mirrors the live
    endpoint post-lane-1."""
    row = conn.execute(f"""
        SELECT * FROM (
            SELECT {_PERSON_SEL} FROM metav_people p WHERE p.name = ? COLLATE NOCASE
            UNION
            SELECT {_PERSON_SEL} FROM metav_people p
            JOIN metav_people_aliases a ON a.person_id = p.person_id
            WHERE a.alias = ? COLLATE NOCASE)
        ORDER BY (birth_year IS NOT NULL) DESC, (death_year IS NOT NULL) DESC
        LIMIT 1""", (name, name)).fetchone()
    if row:
        return row, "exact", name
    cn = compact(name)
    if cn:
        row = conn.execute(f"""
            SELECT * FROM (
                SELECT {_PERSON_SEL} FROM metav_people p
                WHERE REPLACE(REPLACE(p.name,'-',''),' ','') = ? COLLATE NOCASE
                UNION
                SELECT {_PERSON_SEL} FROM metav_people p
                JOIN metav_people_aliases a ON a.person_id = p.person_id
                WHERE REPLACE(REPLACE(a.alias,'-',''),' ','') = ? COLLATE NOCASE)
            ORDER BY (birth_year IS NOT NULL) DESC, (death_year IS NOT NULL) DESC
            LIMIT 1""", (cn, cn)).fetchone()
        if row:
            return row, "compact", row["name"]
    if len(name) >= 5:
        prefix = name[:max(5, len(name) - 2)]
        row = conn.execute(f"""
            SELECT * FROM (
                SELECT {_PERSON_SEL} FROM metav_people p
                WHERE p.name LIKE ? COLLATE NOCASE AND length(p.name) BETWEEN ? AND ?
                UNION
                SELECT {_PERSON_SEL} FROM metav_people p
                JOIN metav_people_aliases a ON a.person_id = p.person_id
                WHERE a.alias LIKE ? COLLATE NOCASE AND length(a.alias) BETWEEN ? AND ?)
            ORDER BY (birth_year IS NOT NULL) DESC, (death_year IS NOT NULL) DESC
            LIMIT 1""", (f"{prefix}%", len(name)-2, len(name)+2,
                         f"{prefix}%", len(name)-2, len(name)+2)).fetchone()
        if row:
            return row, "fuzzy", name
    return None, "none", name

_multi_cache = {}
def multi(name):
    if name not in _multi_cache:
        n = conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT person_id FROM metav_people        WHERE name  = ? COLLATE NOCASE
                UNION
                SELECT person_id FROM metav_people_aliases WHERE alias = ? COLLATE NOCASE
            )""", (name, name)).fetchone()[0]
        m = n > 1
        if not m:
            m = conn.execute(
                "SELECT COUNT(*) FROM tipnr_entities WHERE section='person' "
                "AND (head = ? COLLATE NOCASE OR uniq LIKE ?)",
                (name, name + "@%")).fetchone()[0] > 1
        _multi_cache[name] = m
    return _multi_cache[name]

def rel_count(pid):
    return conn.execute(
        "SELECT COUNT(*) FROM metav_people_relationships WHERE person_id=?",
        (pid,)).fetchone()[0]

def groups_count(pid):
    return conn.execute(
        "SELECT COUNT(*) FROM metav_people_groups WHERE person_id=?",
        (pid,)).fetchone()[0]

def place_exists(name):
    cn = compact(name)
    return conn.execute("""
        SELECT 1 FROM metav_places p
        WHERE p.name = ? COLLATE NOCASE
           OR REPLACE(REPLACE(p.name,'-',''),' ','') = ? COLLATE NOCASE
        UNION
        SELECT 1 FROM metav_places p
        JOIN metav_place_aliases a ON a.place_id = p.place_id
        WHERE a.alias = ? COLLATE NOCASE
           OR REPLACE(REPLACE(a.alias,'-',''),' ','') = ? COLLATE NOCASE
        LIMIT 1""", (name, cn, name, cn)).fetchone() is not None

# ── walk: collect the no-card slots (mirror the census classifier) ───────────
reason_slots = Counter()
name_slots = defaultdict(int)     # bio-bar names only
name_reason = {}
for r in conn.execute("""
    SELECT g.verse_id, g.position, v.book AS book, v.chapter AS ch, v.verse AS vs,
           w.english, w.english_head
    FROM pn_greek_identity g
    JOIN verses v ON v.id = g.verse_id
    LEFT JOIN words w ON w.verse_id = g.verse_id AND w.position = g.position
""").fetchall():
    bk = er.book_num(r["book"])
    name = extract_proper_name(pn_click_name(r["english_head"] or r["english"] or ""))
    if not name or len(name) < 2 or bk is None or name in _DIVINE_SKIP:
        continue
    bkey = er.norm_name(name)
    k = (bk, r["ch"], r["vs"])
    if k + (bkey,) in bound:
        continue
    if len([x for x in verse_binds.get(k, ()) if compact(x) == compact(bkey)]) == 1:
        continue
    # unbound: replay the card decision to isolate the failure reason
    row, tier, guard = person_lookup(name)
    if row is not None and not multi(guard):
        bio_ok = bool(row["birth_year"] or row["death_year"] or rel_count(row["person_id"]) >= 2)
        if bio_ok:
            continue                       # person card serves — not our class
        if place_exists(name):
            continue                       # place card serves instead
        reason = "bio-bar" if tier in ("exact", "compact") else "fuzzy-bio-bar"
    else:
        if place_exists(name):
            continue
        if row is not None:                # hit but multi-referent
            reason = "multi-referent"
        elif er.is_people_group(name):
            reason = "gentilic"
        else:
            reason = "absent"
    reason_slots[reason] += 1
    if reason == "bio-bar":
        name_slots[bkey] += 1
        name_reason[bkey] = (row, tier)

if name_slots.get("paul", 0) == 0:
    print("CONTROL FAILED: 'Paul' not in the bio-bar class — logic drifted, numbers untrustworthy.")
    sys.exit(1)
print("control OK (Paul lands in the bio-bar class)")

print("\n── no-card slots by failure reason ──")
for k, n in reason_slots.most_common():
    print(f"  {k:15s} {n:,}")

print("\n── top 20 bio-bar names: what metaV DOES hold ──")
print(f"{'name':16s} {'slots':>5s} {'sex':>3s} {'born':>5s} {'died':>5s} {'kin':>3s} {'grp':>3s}  tipnr-person / descr")
for nm, n in sorted(name_slots.items(), key=lambda kv: -kv[1])[:20]:
    row, tier = name_reason[nm]
    tp = conn.execute(
        "SELECT COUNT(*), MIN(descr) FROM tipnr_entities WHERE section='person' "
        "AND (head = ? COLLATE NOCASE OR uniq LIKE ?)",
        (row["name"], row["name"] + "@%")).fetchone()
    d = (tp[1] or "").replace("\n", " ")[:52]
    print(f"{nm:16s} {n:5,d} {row['gender'] or '-':>3s} "
          f"{str(row['birth_year'] or '-'):>5s} {str(row['death_year'] or '-'):>5s} "
          f"{rel_count(row['person_id']):3d} {groups_count(row['person_id']):3d}  "
          f"n={tp[0]} {d}")

print("\n── Paul, full detail (the mockup feed) ──")
prow, _, _ = person_lookup("Paul")
print(dict(prow))
print("groups:", [g["group_name"] for g in conn.execute(
    "SELECT group_name FROM metav_people_groups WHERE person_id=?", (prow["person_id"],))])
print("relationships:", [(g["rel_type"], g["related_to"]) for g in conn.execute(
    "SELECT rel_type, related_to FROM metav_people_relationships WHERE person_id=?",
    (prow["person_id"],))])
for t in conn.execute(
        "SELECT uniq, descr, summary FROM tipnr_entities WHERE section='person' "
        "AND (head = 'Paul' COLLATE NOCASE OR uniq LIKE 'Paul@%')"):
    print("tipnr:", t["uniq"], "|", (t["descr"] or "")[:80], "|", (t["summary"] or "")[:120])
