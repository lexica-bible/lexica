#!/usr/bin/env python3
"""audit_pn_card_census.py — READ-ONLY census of PN-card verification state
(TODO.md "PN-card verification census", reviewer-briefed 2026-07-29).

Universe = every row of pn_greek_identity (the PN slot set, expected 32,479).
For each slot it mirrors the live card decision (30-detail-panel.jsx +
views_metav.py) and splits the slots into:

  BOUND            — a verse-verified pn_binding render=1 pair owns the card
                     ("Matched to this verse")
  bin (a) LABEL    — unbound, but the name-path metaV lookup serves a person or
                     place card labeled "Matched by name — not checked against
                     this verse"
  bin (b) NO CARD  — unbound and no person/place card at all (AI blurb or bare
                     Strong's card only)

plus bin (c): per-name AMBIGUITY ranking over the unbound slots — names borne
by multiple TIPNR/metaV people (mirrors _name_is_multi_referent), ranked by
occurrence count (the several-Jeremiahs risk).

Controls (certification rule — the tool ABORTS if any fails):
  C1  bracket re-derive: pn_greek_identity / pn_binding(render=1) counts printed;
      mismatch vs the 2026-07-29 live read (32,479 / 14,898) is flagged loudly.
  C2  known BOUND positive: Judah @ Jer 36:1 must classify BOUND.
  C3  known bin-(a) positive: Jerusalem @ Jer 15:5 must classify LABEL.
  C4  ranking positive: jeremiah or shimei must appear in the ambiguity ranking.

Name extraction mirrors the frontend (pnClickPayload + extractProperName); the
chip path (english_head || english) is primary, and the prose path
(english || english_head) is re-run as a sensitivity check — the count of slots
where the two orders classify differently is printed. Per-bin sample slots are
printed for the live-card spot-check (condition: bulk numbers are not trusted
until samples are checked against live cards).

READ-ONLY: opens the db in read-only mode; writes nothing.
Usage: python3 scripts/audit_pn_card_census.py [bible.db]
"""
import sys, os, re, sqlite3
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import entity_resolution as er

DB = sys.argv[1] if len(sys.argv) > 1 else "bible.db"
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

# EXPECT_BINDS = render=1 rows (what serves cards) — the banked bracket 2026-07-29.
# The earlier 14,898 read counted the whole table (14,830 render + 68 hot).
EXPECT_SLOTS, EXPECT_BINDS = 32479, 14830

# ── frontend mirrors ─────────────────────────────────────────────────────────
_PN_STOP = {"And","But","Or","The","A","An","In","Of","To","For","With","From",
            "By","At","His","Her","Its","Their","My","Your","Our","O"}
_DIVINE_SKIP = {"LORD","Lord","YHWH","Yahweh","Jehovah","Holy"}

def pn_click_name(raw):
    """pnClickPayload: capitalize a single-word raw (english_head is lowercased)."""
    raw = raw or ""
    if raw and " " not in raw:
        raw = raw[0].upper() + raw[1:]
    return raw

def extract_proper_name(gloss):
    """00-core.jsx extractProperName, byte-for-byte semantics."""
    if not gloss:
        return ""
    clean = re.sub(r"[^a-zA-Z\s'\-]", "", gloss).strip()
    for w in re.split(r"\s+", clean):
        if w and w[0].isupper() and w not in _PN_STOP:
            return w
    return ""

def compact(s):
    return (s or "").replace("-", "").replace(" ", "")

# ── the two-sided bracket, re-derived live ───────────────────────────────────
n_slots = conn.execute("SELECT count(*) FROM pn_greek_identity").fetchone()[0]
n_binds = conn.execute("SELECT count(*) FROM pn_binding WHERE render=1").fetchone()[0]
n_bind_pairs = conn.execute(
    "SELECT count(*) FROM (SELECT DISTINCT book,chapter,verse,name "
    "FROM pn_binding WHERE render=1)").fetchone()[0]

# bound lookup structures (norm_name-keyed, + per-verse lists for the
# hyphen-blind retry the entity endpoint does)
bound = set()
verse_binds = defaultdict(list)
for r in conn.execute("SELECT book, chapter, verse, name FROM pn_binding WHERE render=1"):
    k = (r["book"], r["chapter"], r["verse"])
    bound.add(k + (r["name"],))
    verse_binds[k].append(r["name"])

# ── metaV name-path lookups, computed once per distinct name ────────────────
def person_row_exists(name):
    """metav_person: exact name/alias match, then the fuzzy prefix fallback.
    (Superseded by best_person_card below — kept for the control path.)"""
    r = conn.execute("""
        SELECT 1 FROM (
            SELECT p.person_id, p.birth_year, p.death_year FROM metav_people p
            WHERE p.name = ? COLLATE NOCASE
            UNION
            SELECT p.person_id, p.birth_year, p.death_year FROM metav_people p
            JOIN metav_people_aliases a ON a.person_id = p.person_id
            WHERE a.alias = ? COLLATE NOCASE) LIMIT 1""", (name, name)).fetchone()
    if r:
        return True, False
    if len(name) >= 5:
        prefix = name[:max(5, len(name) - 2)]
        r = conn.execute("""
            SELECT 1 FROM (
                SELECT p.person_id FROM metav_people p
                WHERE p.name LIKE ? COLLATE NOCASE AND length(p.name) BETWEEN ? AND ?
                UNION
                SELECT p.person_id FROM metav_people p
                JOIN metav_people_aliases a ON a.person_id = p.person_id
                WHERE a.alias LIKE ? COLLATE NOCASE AND length(a.alias) BETWEEN ? AND ?
            ) LIMIT 1""", (f"{prefix}%", len(name)-2, len(name)+2,
                           f"{prefix}%", len(name)-2, len(name)+2)).fetchone()
        if r:
            return True, True
    return False, False

def best_person_card(name):
    """The row metav_person would serve (exact, then hyphen-blind compact, then
    fuzzy — 2026-07-29 lane-1/3 fix mirrored), for the personOk gate. Returns
    (row, guard_name): the multi-referent guard runs on the MATCHED canonical
    spelling for a compact hit, on the requested name otherwise."""
    guard_name = name
    row = conn.execute("""
        SELECT * FROM (
            SELECT p.person_id, p.name, p.birth_year, p.death_year FROM metav_people p
            WHERE p.name = ? COLLATE NOCASE
            UNION
            SELECT p.person_id, p.name, p.birth_year, p.death_year FROM metav_people p
            JOIN metav_people_aliases a ON a.person_id = p.person_id
            WHERE a.alias = ? COLLATE NOCASE)
        ORDER BY (birth_year IS NOT NULL) DESC, (death_year IS NOT NULL) DESC
        LIMIT 1""", (name, name)).fetchone()
    if not row:
        cn = compact(name)
        if cn:
            row = conn.execute("""
                SELECT * FROM (
                    SELECT p.person_id, p.name, p.birth_year, p.death_year FROM metav_people p
                    WHERE REPLACE(REPLACE(p.name,'-',''),' ','') = ? COLLATE NOCASE
                    UNION
                    SELECT p.person_id, p.name, p.birth_year, p.death_year FROM metav_people p
                    JOIN metav_people_aliases a ON a.person_id = p.person_id
                    WHERE REPLACE(REPLACE(a.alias,'-',''),' ','') = ? COLLATE NOCASE)
                ORDER BY (birth_year IS NOT NULL) DESC, (death_year IS NOT NULL) DESC
                LIMIT 1""", (cn, cn)).fetchone()
            if row:
                guard_name = row["name"]
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
    return row, guard_name

_multi_cache = {}
def name_is_multi_referent(name):
    """views_metav._name_is_multi_referent, mirrored."""
    if name in _multi_cache:
        return _multi_cache[name]
    _multi_cache[name] = _multi_referent_raw(name)
    return _multi_cache[name]

def _multi_referent_raw(name):
    n = conn.execute("""
        SELECT COUNT(*) FROM (
            SELECT person_id FROM metav_people        WHERE name  = ? COLLATE NOCASE
            UNION
            SELECT person_id FROM metav_people_aliases WHERE alias = ? COLLATE NOCASE
        )""", (name, name)).fetchone()[0]
    if n > 1:
        return True
    n = conn.execute(
        "SELECT COUNT(*) FROM tipnr_entities WHERE section='person' "
        "AND (head = ? COLLATE NOCASE OR uniq LIKE ?)",
        (name, name + "@%")).fetchone()[0]
    return n > 1

def place_card_exists(name):
    hit = conn.execute("""
        SELECT 1 FROM metav_places p WHERE p.name = ? COLLATE NOCASE
        UNION
        SELECT 1 FROM metav_places p
        JOIN metav_place_aliases a ON a.place_id = p.place_id
        WHERE a.alias = ? COLLATE NOCASE LIMIT 1""", (name, name)).fetchone() is not None
    if hit:
        return True
    cn = compact(name)  # hyphen-blind fallback, mirrored from the place endpoint
    if not cn:
        return False
    return conn.execute("""
        SELECT 1 FROM metav_places p
        WHERE REPLACE(REPLACE(p.name,'-',''),' ','') = ? COLLATE NOCASE
        UNION
        SELECT 1 FROM metav_places p
        JOIN metav_place_aliases a ON a.place_id = p.place_id
        WHERE REPLACE(REPLACE(a.alias,'-',''),' ','') = ? COLLATE NOCASE
        LIMIT 1""", (cn, cn)).fetchone() is not None

def rel_count(pid):
    return conn.execute(
        "SELECT COUNT(*) FROM metav_people_relationships WHERE person_id=?",
        (pid,)).fetchone()[0]

_card_cache = {}
def name_card(name):
    """Card outcome for an UNBOUND click on `name`:
    'person' / 'place' (bin a), or '' (bin b). Mirrors the metaV effect:
    divine skip; personOk = bio bar AND not multi-referent; place = any row."""
    if name in _card_cache:
        return _card_cache[name]
    out = ""
    if name and len(name) >= 2 and name not in _DIVINE_SKIP:
        prow, guard_name = best_person_card(name)
        person_ok = False
        if prow is not None and not name_is_multi_referent(guard_name):
            person_ok = bool(prow["birth_year"] or prow["death_year"]
                             or rel_count(prow["person_id"]) >= 2)
        if person_ok:
            out = "person"
        elif place_card_exists(name):
            out = "place"
    _card_cache[name] = out
    return out

# ── walk every slot ──────────────────────────────────────────────────────────
rows = conn.execute("""
    SELECT g.verse_id, g.position, v.book AS book, v.chapter AS ch, v.verse AS vs,
           w.english, w.english_head
    FROM pn_greek_identity g
    JOIN verses v ON v.id = g.verse_id
    LEFT JOIN words w ON w.verse_id = g.verse_id AND w.position = g.position
""").fetchall()

n_walked = len(rows)
n_no_word = sum(1 for r in rows if r["english"] is None and r["english_head"] is None)

bins = Counter()          # bound / a / b
a_sub = Counter()         # bin-a person vs place
b_sub = Counter()         # bin-b sub-reasons
amb_names = Counter()     # unbound slots per multi-referent name
uni_names = Counter()     # unbound slots per single/zero-referent name
samples = defaultdict(list)
sens_diff = 0
c2 = c3 = False
jer36 = er.book_num("Jer")

for r in rows:
    bk = er.book_num(r["book"])
    raw_chip = r["english_head"] or r["english"] or ""
    # lane-1 fix 2026-07-29: pnClickPayload now uses english_head-first too, so the
    # prose mirror matches production and the sensitivity count certifies 0.
    raw_prose = r["english_head"] or r["english"] or ""
    name = extract_proper_name(pn_click_name(raw_chip))

    def classify(nm, bkey):
        if not nm or len(nm) < 2 or bk is None:
            return "b:no-name"
        k = (bk, r["ch"], r["vs"])
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

    cls = classify(name, er.norm_name(name))
    # sensitivity: would the prose-mode click classify differently?
    if raw_prose != raw_chip:
        nm2 = extract_proper_name(pn_click_name(raw_prose))
        if classify(nm2, er.norm_name(nm2)).split(":")[0] != cls.split(":")[0]:
            sens_diff += 1

    top = cls.split(":")[0]
    bins[top] += 1
    if top == "b":
        b_sub[cls] += 1
    elif top == "a":
        a_sub[cls] += 1
    if top == "bound":
        if (er.norm_name(name) == "judah" and bk == jer36
                and r["ch"] == 36 and r["vs"] == 1):
            c2 = True
    else:
        nm_norm = er.norm_name(name)
        if nm_norm:
            (amb_names if name_is_multi_referent(name) else uni_names)[nm_norm] += 1
        if top == "a" and nm_norm == "jerusalem" and bk == jer36 \
                and r["ch"] == 15 and r["vs"] == 5:
            c3 = True
    if len(samples[cls]) < 6:
        samples[cls].append((r["book"], r["ch"], r["vs"], r["position"], name or "(none)"))

c4 = ("jeremiah" in amb_names) or ("shimei" in amb_names)

# ── report ───────────────────────────────────────────────────────────────────
print("=== PN-card verification census (read-only) ===")
print(f"C1 bracket re-derive: pn_greek_identity rows = {n_slots:,} "
      f"(expected {EXPECT_SLOTS:,}) {'OK' if n_slots == EXPECT_SLOTS else '*** MISMATCH ***'}")
print(f"                      pn_binding render=1 rows = {n_binds:,} "
      f"(expected {EXPECT_BINDS:,}) {'OK' if n_binds == EXPECT_BINDS else '*** MISMATCH ***'}")
print(f"                      distinct verified (book,ch,vs,name) pairs = {n_bind_pairs:,}")
print(f"slots walked = {n_walked:,} (slots with no matching words row: {n_no_word:,})")
print()
print(f"C2 bound control  (Judah @ Jer 36:1 BOUND):        {'PASS' if c2 else 'FAIL'}")
print(f"C3 bin-a control  (Jerusalem @ Jer 15:5 LABEL):    {'PASS' if c3 else 'FAIL'}")
print(f"C4 ranking control (jeremiah/shimei in ranking):   {'PASS' if c4 else 'FAIL'}")
if not (c2 and c3 and c4):
    print("\nCONTROL FAILED — numbers below are NOT trustworthy. Aborting.")
    sys.exit(1)
print()
print("── census ──")
print(f"BOUND (verse-verified card)        : {bins['bound']:,}")
print(f"bin (a) label card ('Matched by name'): {bins['a']:,}")
for k, n in sorted(a_sub.items()):
    print(f"    {k:12s} {n:,}")
print(f"bin (b) no person/place card       : {bins['b']:,}")
for k, n in sorted(b_sub.items()):
    print(f"    {k:12s} {n:,}")
print(f"\nname-extraction sensitivity: {sens_diff:,} slots classify differently "
      f"chip-order vs prose-order raw")
print()
tot_amb, tot_uni = sum(amb_names.values()), sum(uni_names.values())
print("── bin (c): ambiguity over the unverified slots ──")
print(f"unbound slots bearing a MULTI-referent name : {tot_amb:,}")
print(f"unbound slots bearing a single/zero-referent name: {tot_uni:,}")
print(f"distinct multi-referent names: {len(amb_names):,}")
print("\ntop 30 multi-referent names by unbound occurrence count:")
for nm, n in amb_names.most_common(30):
    print(f"  {nm:20s} {n:,}")
print()
print("── spot-check samples (verify each against the LIVE card before trusting bulk) ──")
for cls in sorted(samples):
    print(f"  [{cls}]")
    for bkx, ch, vs, pos, nm in samples[cls]:
        print(f"    {bkx} {ch}:{vs} pos {pos}  name={nm}")
