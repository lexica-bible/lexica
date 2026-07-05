#!/usr/bin/env python3
"""
build_tipnr_metav_link.py — DRAFT (checkpoint-gated) for the entity->metaV join.

Purpose: a bound card knows its TIPNR entity (uniq) but pins/enriches by NAME today, so a
multi-referent name (Bethel, Eden) can't pick the right metav_places row. This builds a
link table so the card resolves by ENTITY:

    tipnr_metav_link(uniq TEXT, kind TEXT, metav_id INTEGER)     -- kind = 'place' | 'person'

Serves both editions (places now; the queued person-panel cross-link reuses the same table).

DRY-RUN BY DEFAULT: opens bible.db READ-ONLY, matches, prints counts + an ambiguity rate,
and writes the RESIDUAL (unmatched / ambiguous) to scripts/tipnr_metav_link_residual.txt for
hand review. It writes NOTHING to the database without --apply, and even then only its own
table. DO NOT --apply until the match logic + residual list are reviewed.

Match rules (conservative — a wrong link is worse than no link, so ambiguity FLOORS):
  places : 1) unique metav_places row of the same (compacted) name        -> CONFIDENT
           2) several same-name rows, disambiguated by TIPNR area/descr == -> CONFIDENT (by-area)
              metav_places.root  (Bethel_2 area 'Tribe of Simeon' == root)
           3) otherwise                                                     -> RESIDUAL
  persons: unique metav_people row of the same name                        -> CONFIDENT
           (no root to disambiguate persons; anything ambiguous is RESIDUAL)

Run on PythonAnywhere:
    python3 scripts/build_tipnr_metav_link.py            # dry-run, report + residual file
    python3 scripts/build_tipnr_metav_link.py --apply    # write the table (after review)
"""
import os, re, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import entity_resolution as er

DB = next((a for a in sys.argv[1:] if not a.startswith("--")),
          "/home/appssanding720/bible-db/bible.db")
APPLY = "--apply" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))


def key(s):
    """Compact match key: lowercase, drop a trailing '_N' id, keep letters only.
    'Bethel_1' -> 'bethel', 'Beth-el' -> 'bethel'."""
    s = re.sub(r"_\d+$", "", (s or ""))
    return re.sub(r"[^a-z]", "", s.lower())


def tokens(s):
    return {t for t in re.split(r"[^a-z0-9]+", (s or "").lower()) if len(t) > 2}


def main():
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    have = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
        "('tipnr_entities','metav_places','metav_people')")}
    if {"tipnr_entities", "metav_places", "metav_people"} - have:
        print("MISSING tables — need tipnr_entities + metav_places + metav_people.")
        sys.exit(2)

    # metaV indexes by compacted name
    places = {}
    for r in conn.execute("SELECT place_id, name, root FROM metav_places"):
        places.setdefault(key(r["name"]), []).append(r)
    people = {}
    for r in conn.execute("SELECT person_id, name FROM metav_people"):
        people.setdefault(key(r["name"]), []).append(r)

    links, residual = [], []          # links: (uniq, kind, metav_id, how)
    n_place = n_person = 0

    for e in conn.execute("SELECT uniq, section, area, descr FROM tipnr_entities"):
        disp = e["uniq"].split("@")[0]
        k = key(disp)
        if e["section"] == "place":
            n_place += 1
            cand = places.get(k, [])
            if len(cand) == 1:
                links.append((e["uniq"], "place", cand[0]["place_id"], "name"))
            elif len(cand) > 1:
                # disambiguate by TIPNR area/descr overlapping the metav 'root'
                want = tokens(e["area"]) | tokens(e["descr"])
                hit = [c for c in cand if want & tokens(c["root"])]
                if len(hit) == 1:
                    links.append((e["uniq"], "place", hit[0]["place_id"], "by-area"))
                else:
                    residual.append(("place", e["uniq"], e["area"] or e["descr"] or "",
                                     [(c["place_id"], c["root"]) for c in cand]))
            # 0 candidates: no metav row -> no link, card declines the map (fine, not residual)
        elif e["section"] == "person":
            n_person += 1
            cand = people.get(k, [])
            if len(cand) == 1:
                links.append((e["uniq"], "person", cand[0]["person_id"], "name"))
            elif len(cand) > 1:
                residual.append(("person", e["uniq"], "",
                                 [(c["person_id"], c["name"]) for c in cand]))

    place_links = [l for l in links if l[1] == "place"]
    person_links = [l for l in links if l[1] == "person"]
    by_area = sum(1 for l in place_links if l[3] == "by-area")
    place_res = [r for r in residual if r[0] == "place"]
    person_res = [r for r in residual if r[0] == "person"]

    print("=" * 68)
    print("tipnr_metav_link — DRAFT match report")
    print(f"  PLACES : {len(place_links):>5} confident ({by_area} by-area) "
          f"| {len(place_res)} ambiguous (residual) | of {n_place} place entities")
    print(f"  PERSONS: {len(person_links):>5} confident (unique name) "
          f"| {len(person_res)} ambiguous (residual) | of {n_person} person entities")
    amb = len(place_res) / (len(place_links) + len(place_res)) if (place_links or place_res) else 0
    print(f"  place ambiguity rate (of name-matched): {amb:.1%}")

    with open(os.path.join(HERE, "tipnr_metav_link_residual.txt"), "w", encoding="utf-8") as fh:
        for kind, uniq, hint, cands in sorted(residual):
            fh.write(f"{kind}\t{uniq}\t[{hint}]\t{cands}\n")
    print(f"  residual written -> scripts/tipnr_metav_link_residual.txt "
          f"({len(residual)} rows to hand-resolve)")

    conn.close()
    if not APPLY:
        print("\n[DRY-RUN] No table written. Review the logic + residual, then --apply.")
        return

    w = sqlite3.connect(DB)
    try:
        w.execute("DROP TABLE IF EXISTS tipnr_metav_link")
        w.execute("CREATE TABLE tipnr_metav_link(uniq TEXT, kind TEXT, metav_id INTEGER)")
        w.executemany("INSERT INTO tipnr_metav_link VALUES(?,?,?)",
                      [(u, k, i) for (u, k, i, _how) in links])
        w.execute("CREATE INDEX ix_tipnr_metav_link ON tipnr_metav_link(uniq)")
        w.commit()
        print(f"\nWrote tipnr_metav_link: {len(links)} rows.")
    finally:
        w.close()


if __name__ == "__main__":
    main()
