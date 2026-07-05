#!/usr/bin/env python3
"""
build_person_metav_link.py — cross-link each TIPNR PERSON entity to its metaV
person record, so a bound thin card (Judah: one line + kin) can render the rich
metaV card (David: badges, born/died, kin, Nave's) while TIPNR stays the spine.

Writes kind='person' rows into the SAME table the place edition uses:
    tipnr_metav_link(uniq TEXT, kind TEXT, metav_id INTEGER)   -- metav_id = metav_people.person_id
(the place builder owns kind='place'; --apply here replaces ONLY the person rows.)

THREE-TIER match (a wrong link renders the wrong person's family as fact, so ambiguity
FLOORS to a hand-list rather than guessing):

  Tier 1  Strong's-direct : among same-name metaV people, the one whose Strong's set
          (metav_person_strongs) contains the entity's own base. Deterministic — it lands
          on the exact key TIPNR entities are bound to, no threshold to defend. Unique -> LINK.
  Tier 2  verse-overlap   : tiebreaker when several same-name people SHARE that Strong's
          number (many Zechariahs, all H2148). CONTAINMENT of the entity's refs in the
          metaV person's verse set (asymmetric on purpose — TIPNR refs are a subset of
          metaV's fuller list), a clear unique winner above a floor -> LINK.
  else    residual         : ambiguous, no clear winner -> hand-list, ranked by traffic.

Traffic = the entity's render count in pn_binding (every place a reader can click that
name-in-verse and land on this entity) — the honest proxy for card views, and it dodges
the OT H-base vs ABP-Greek occurrence tangle entirely.

DRY-RUN BY DEFAULT: reads bible.db + the staging metav_index.db READ-ONLY, prints bucket
counts + the traffic-coverage number, writes the residual to a file. Writes NOTHING to
bible.db without --apply, and even then only kind='person' rows in tipnr_metav_link.

Run on PythonAnywhere (build the index first):
    python3 scripts/build_metav_person_index.py
    python3 scripts/build_person_metav_link.py                       # dry-run report
    python3 scripts/build_person_metav_link.py --apply               # after review
"""
import os, re, sqlite3, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import entity_resolution as er

BIBLE = "/home/appssanding720/bible-db/bible.db"
INDEX = "/home/appssanding720/bible-db/metav_index.db"
for i, a in enumerate(sys.argv):
    if a == "--bible" and i + 1 < len(sys.argv):
        BIBLE = sys.argv[i + 1]
    if a == "--index" and i + 1 < len(sys.argv):
        INDEX = sys.argv[i + 1]
APPLY = "--apply" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))

CONTAIN_FLOOR = 0.5     # tier-2 winner must contain at least half the entity's refs


def key(s):
    """Compact match key: drop a trailing '_N', letters only. 'Bethel_1'->'bethel'."""
    s = re.sub(r"_\d+$", "", (s or ""))
    return re.sub(r"[^a-z]", "", s.lower())


def main():
    if not os.path.exists(INDEX):
        print(f"MISSING {INDEX} — run build_metav_person_index.py first.")
        sys.exit(2)
    conn = sqlite3.connect(f"file:{BIBLE}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute(f"ATTACH DATABASE 'file:{INDEX}?mode=ro' AS mx")

    need = {"tipnr_entities", "tipnr_entity_refs", "metav_people", "pn_binding"}
    have = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if need - have:
        print(f"MISSING tables in bible.db: {sorted(need - have)}")
        sys.exit(2)

    # metaV people indexed by compact name
    people_by_name = defaultdict(list)          # key -> [person_id, ...]
    name_of = {}
    for r in conn.execute("SELECT person_id, name FROM metav_people"):
        people_by_name[key(r["name"])].append(r["person_id"])
        name_of[r["person_id"]] = r["name"]

    # metaV person -> Strong's set, and -> verse set (from the staging index)
    mp_strongs = defaultdict(set)
    for r in conn.execute("SELECT person_id, strongs_id FROM mx.metav_person_strongs"):
        mp_strongs[r["person_id"]].add(r["strongs_id"])
    mp_verses = defaultdict(set)
    for r in conn.execute("SELECT person_id, book_id, chapter, verse FROM mx.metav_person_verses"):
        mp_verses[r["person_id"]].add((r["book_id"], r["chapter"], r["verse"]))

    # entity refs (verse set) + traffic (render count in pn_binding)
    ent_refs = defaultdict(set)
    for r in conn.execute("SELECT uniq, book, chapter, verse FROM tipnr_entity_refs"):
        ent_refs[r["uniq"]].add((r["book"], r["chapter"], r["verse"]))
    traffic = defaultdict(int)
    for r in conn.execute(
            "SELECT entity_uniq, COUNT(*) c FROM pn_binding WHERE render=1 "
            "GROUP BY entity_uniq"):
        traffic[r["entity_uniq"]] = r["c"]

    buckets = {"strongs": [], "overlap": [], "name_only": [], "residual": [], "no_metav": []}
    # each linked entry: (uniq, person_id, rule); residual: (uniq, [cands])

    for e in conn.execute("SELECT uniq, head, bases FROM tipnr_entities WHERE section='person'"):
        uniq = e["uniq"]
        disp = e["head"] or uniq.split("@")[0]
        cands = people_by_name.get(key(disp), [])
        if not cands:
            buckets["no_metav"].append(uniq)
            continue

        bases = {er.norm_base(b) for b in (e["bases"] or "").split(",") if b.strip()}
        strong_hits = [c for c in cands if bases & mp_strongs.get(c, set())]

        # ── Tier 1: unique Strong's-direct match ───────────────────────────────
        if len(strong_hits) == 1:
            buckets["strongs"].append((uniq, strong_hits[0], "strongs"))
            continue

        # candidate pool for verse-overlap: Strong's-matched if any, else all name-mates
        pool = strong_hits if strong_hits else cands

        if len(pool) == 1:
            # a lone name-mate that Strong's couldn't confirm (missing/mismatched number)
            buckets["name_only"].append((uniq, pool[0], "name"))
            continue

        # ── Tier 2: verse-overlap containment ──────────────────────────────────
        refs = ent_refs.get(uniq, set())
        scored = []
        if refs:
            for c in pool:
                inter = len(refs & mp_verses.get(c, set()))
                scored.append((inter / len(refs), c))
            scored.sort(reverse=True)
        if scored and scored[0][0] >= CONTAIN_FLOOR and (
                len(scored) == 1 or scored[0][0] > scored[1][0]):
            buckets["overlap"].append((uniq, scored[0][1], "overlap"))
        else:
            buckets["residual"].append((uniq, pool))

    # ── traffic-coverage ───────────────────────────────────────────────────────
    linked = buckets["strongs"] + buckets["overlap"] + buckets["name_only"]
    linked_uniq = {u for (u, *_ ) in linked}
    # denominator: person entities that HAVE a metaV candidate (a link is even possible)
    with_cand = set()
    for b in ("strongs", "overlap", "name_only", "residual"):
        for row in buckets[b]:
            with_cand.add(row[0])
    all_person_traffic = sum(traffic[u] for u in traffic)  # every rendered person entity
    cand_traffic = sum(traffic[u] for u in with_cand)
    linked_traffic = sum(traffic[u] for u in linked_uniq)

    def pct(a, b):
        return f"{100*a/b:4.1f}%" if b else "  n/a"

    print("=" * 70)
    print("build_person_metav_link — DRY-RUN three-tier report")
    print(f"  Tier 1 Strong's-direct : {len(buckets['strongs']):>5}")
    print(f"  Tier 2 verse-overlap   : {len(buckets['overlap']):>5}")
    print(f"  name-only (unique, no # confirm): {len(buckets['name_only']):>5}")
    print(f"  RESIDUAL (hand-list)   : {len(buckets['residual']):>5}")
    print(f"  no metaV record        : {len(buckets['no_metav']):>5}")
    total = sum(len(v) for v in buckets.values())
    print(f"  ------ {total} TIPNR person entities")
    print()
    print("  traffic coverage (render-count proxy for card views):")
    print(f"    linked / all rendered person entities   : "
          f"{linked_traffic:,} / {all_person_traffic:,}  ({pct(linked_traffic, all_person_traffic)})")
    print(f"    linked / entities with a metaV candidate : "
          f"{linked_traffic:,} / {cand_traffic:,}  ({pct(linked_traffic, cand_traffic)})")

    # residual hand-list, ranked by traffic (top of this list is where eyeballs pay off)
    res = sorted(buckets["residual"], key=lambda x: -traffic[x[0]])
    path = os.path.join(HERE, "person_metav_link_residual.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# uniq\ttraffic\tcandidate metaV person_ids (name)\n")
        for uniq, cands in res:
            names = [f"{c}:{name_of.get(c,'?')}" for c in cands]
            fh.write(f"{uniq}\t{traffic[uniq]}\t{names}\n")
    print(f"\n  residual -> scripts/person_metav_link_residual.txt "
          f"({len(res)} to hand-resolve, top-traffic first)")
    print("  top 15 residual by traffic:")
    for uniq, cands in res[:15]:
        print(f"    {traffic[uniq]:>4}  {uniq}  ({len(cands)} same-name metaV people)")

    if not APPLY:
        conn.close()
        print("\n[DRY-RUN] No table written. Review buckets + residual, then --apply.")
        return

    conn.close()
    w = sqlite3.connect(BIBLE)
    try:
        w.execute("CREATE TABLE IF NOT EXISTS tipnr_metav_link(uniq TEXT, kind TEXT, metav_id INTEGER)")
        w.execute("DELETE FROM tipnr_metav_link WHERE kind='person'")   # leave place rows intact
        w.executemany("INSERT INTO tipnr_metav_link VALUES(?,'person',?)",
                      [(u, pid) for (u, pid, _rule) in linked])
        w.execute("CREATE INDEX IF NOT EXISTS ix_tipnr_metav_link ON tipnr_metav_link(uniq)")
        w.commit()
        print(f"\nWrote {len(linked)} kind='person' rows into tipnr_metav_link.")
    finally:
        w.close()


if __name__ == "__main__":
    main()
