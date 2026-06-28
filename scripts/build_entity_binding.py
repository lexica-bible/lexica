#!/usr/bin/env python3
"""
build_entity_binding.py — Issue 2 rebuild: run the binder over the corpus and (on
--apply) write the entity-binding side tables. DRY-RUN BY DEFAULT — it opens bible.db
READ-ONLY and reports counts; it writes NOTHING without --apply, and even then it only
ever creates/replaces its OWN three side tables (it never touches words/verses).

The binding logic lives in entity_resolution.py (the shared engine, unit-tested). This
script is the DB glue: scope-tiering from metaV + the report + the table writes.

SCOPE (build order step 3): bind Tier 1 (ambiguous names) + Tier 2 (unambiguous, NO
metaV row). LEAVE Tier 3 (unambiguous WITH a metaV row) on the working name-path — it
is skipped entirely, so the runtime falls through to today's card for those. Tiers are
DERIVED from the live metaV tables every run (re-tier-on-load, step 6) — never cached.

Render rule (the spine): a binding RENDERS only when the clicked verse corroborates the
bound entity. Number-only links and same-name multis FLOOR (the latter tagged HOT for
hand-check). Floors store no row -> the runtime shows Fix A (the permanent floor).

Tables written on --apply:
  tipnr_entities(uniq PK, head, section, gender, area, descr, summary, bases)
  tipnr_entity_refs(uniq, book, chapter, verse)            -- the entity's own refs
  pn_binding(book, chapter, verse, name, entity_uniq, kind, rule, render, hot, tier)
                                                           -- keyed by (book,ch,vs,name)

Usage (on PythonAnywhere):
  python3 scripts/build_entity_binding.py                       # dry-run, report only
  python3 scripts/build_entity_binding.py --tipnr /path/tipnr.txt   # reuse a local copy
  python3 scripts/build_entity_binding.py --apply              # write the tables
"""

import os
import sys
import sqlite3
import urllib.request
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import entity_resolution as er

DB = next((a for a in sys.argv[1:] if not a.startswith("--")),
          "/home/appssanding720/bible-db/bible.db")
APPLY = "--apply" in sys.argv
TIPNR_LOCAL = next((sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == "--tipnr"
                    and i + 1 < len(sys.argv)), None)

TIPNR_URL = (
    "https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/"
    "Proper%20Nouns/TIPNR%20-%20Translators%20Individualised%20Proper%20Names"
    "%20with%20all%20References%20-%20STEPBible.org%20CC%20BY.txt"
)


def load_tipnr():
    if TIPNR_LOCAL:
        print(f"TIPNR: {TIPNR_LOCAL}")
        return open(TIPNR_LOCAL, encoding="utf-8-sig").read().splitlines()
    print("Downloading TIPNR...")
    with urllib.request.urlopen(TIPNR_URL) as r:
        return r.read().decode("utf-8-sig").splitlines()


def metav_maps(conn):
    """norm(name|alias) -> {id} for places and people, from the live metaV tables."""
    place_ids, person_ids = defaultdict(set), defaultdict(set)
    for r in conn.execute("SELECT place_id, name FROM metav_places WHERE name IS NOT NULL"):
        place_ids[er.norm_name(r["name"])].add(r["place_id"])
    for r in conn.execute("SELECT place_id, alias FROM metav_place_aliases WHERE alias IS NOT NULL"):
        place_ids[er.norm_name(r["alias"])].add(r["place_id"])
    for r in conn.execute("SELECT person_id, name FROM metav_people WHERE name IS NOT NULL"):
        person_ids[er.norm_name(r["name"])].add(r["person_id"])
    for r in conn.execute("SELECT person_id, alias FROM metav_people_aliases WHERE alias IS NOT NULL"):
        person_ids[er.norm_name(r["alias"])].add(r["person_id"])
    place_ids.pop("", None); person_ids.pop("", None)
    return place_ids, person_ids


def scope_tier(name, ambiguous, person_ids, place_ids):
    """1 = ambiguous; 2 = unambiguous with NO metaV row; 3 = unambiguous WITH a row."""
    if name in ambiguous:
        return 1
    if name in person_ids or name in place_ids:
        return 3
    return 2


def main():
    print(f"{'[APPLY] ' if APPLY else '[DRY-RUN] '}build_entity_binding -> {DB}\n")
    ents = er.parse_tipnr(load_tipnr())
    name_idx, base_idx, compact_idx = er.build_indexes(ents)
    print(f"Parsed {len(ents):,} TIPNR entities, {len(name_idx):,} distinct spellings\n")

    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    place_ids, person_ids = metav_maps(conn)
    ambiguous = ({n for n, ids in place_ids.items() if len(ids) > 1}
                 | {n for n, ids in person_ids.items() if len(ids) > 1}
                 | {n for n in place_ids if n in person_ids})

    has_pn = "is_pn" in {r[1] for r in conn.execute("PRAGMA table_info(words)")}
    pn_where = "w.is_pn = 1" if has_pn else "w.strongs_base = '*'"
    occ_rows = conn.execute(f"""
        SELECT v.book AS book, v.chapter AS ch, v.verse AS vs,
               COALESCE(NULLIF(w.english_head,''), w.english) AS label,
               w.strongs_base AS base
        FROM words w JOIN verses v ON v.id = w.verse_id
        WHERE {pn_where}
          AND COALESCE(NULLIF(w.english_head,''), w.english) IS NOT NULL
          AND COALESCE(NULLIF(w.english_head,''), w.english) != ''
    """).fetchall()
    print(f"Proper-noun occurrences in the text: {len(occ_rows):,}\n")

    # ── bind every Tier-1/Tier-2 occurrence, group to (book,ch,vs,name) ─────────
    # A binding is decided per occurrence; we then collapse to one row per
    # (book,ch,vs,name): a render survives only if every word of that name+verse
    # agrees on the SAME entity (else it's a conflict -> floor/HOT).
    stat = {t: defaultdict(int) for t in (1, 2, 3)}     # tier -> kind -> count
    group = {}                                           # (bk,ch,vs,name) -> binding state
    versification = defaultdict(int)
    numonly_dump, hot_dump, tier3_vers = [], [], []

    for r in occ_rows:
        nm = er.norm_name(r["label"])
        if not nm:
            continue
        bk = er.book_num(r["book"])
        tier = scope_tier(nm, ambiguous, person_ids, place_ids)
        if bk is None:
            stat[tier]["bookmiss"] += 1
            continue
        # Bind EVERY tier for the stats (so WS1 versification is counted across all
        # tiers — most superscription recoveries are Tier-3 names like David/Asaph),
        # but only Tier 1/2 results are written to the binding tables below.
        b = er.bind_occurrence(ents, name_idx, base_idx, compact_idx, nm, bk, r["ch"], r["vs"], r["base"])
        stat[tier][b.kind] += 1
        if b.kind == "versification":
            versification[b.rule] += 1
        if tier == 3:
            stat[3]["skipped"] += 1            # left on the name-path, not bound
            # the WS1 recoveries we DON'T bind: prove they RENDER (binder said so) AND
            # sit on an unambiguous name (so the live name-path returns the right one),
            # vs. silently landing in a floor bucket (which would be the ordering bug).
            if b.kind == "versification":
                np = len(person_ids.get(nm, ())); npl = len(place_ids.get(nm, ()))
                tier3_vers.append((nm, r["book"], r["ch"], r["vs"],
                                   ents[b.entity]["uniq"], np, npl))
            continue
        key = (bk, r["ch"], r["vs"], nm)
        prev = group.get(key)
        if b.render:
            ent = ents[b.entity]
            cur = ("render", ent["uniq"], b.kind, b.rule, tier)
            if prev is None or prev[0] != "render":
                group[key] = cur
            elif prev[1] != ent["uniq"]:
                group[key] = ("hot", None, "conflict", "", tier)   # two names disagree
        else:
            if prev is None:
                group[key] = ("hot" if b.hot else "floor", None, b.kind, b.rule, tier)
            if b.kind == "number_only":
                heads = sorted({ents[i]["head"] for i in b.candidates})
                numonly_dump.append((nm, r["book"], r["ch"], r["vs"], er.norm_base(r["base"]), heads))
            if b.hot:
                heads = sorted({ents[i]["head"] for i in b.candidates})
                hot_dump.append((nm, r["book"], r["ch"], r["vs"], heads))

    # ── report ──────────────────────────────────────────────────────────────
    def report_tier(t, title):
        s = stat[t]
        occ = sum(v for k, v in s.items() if k not in ("skipped", "bookmiss"))
        render = s["exact"] + s["fuzzy"] + s["versification"]
        floor = s["multi"] + s["number_only"] + s["none"]
        print("=" * 72)
        print(title)
        if t == 3:
            print(f"  occurrences LEFT on the name-path (not bound): {s['skipped']:,}")
            return
        if not occ:
            print("  (no occurrences)"); return
        pct = lambda n: f"{100*n/occ:.1f}%"
        print(f"  occurrences (binder-considered)      : {occ:,}")
        print(f"  RENDER (corroborated bind)           : {render:,}  ({pct(render)})")
        print(f"     exact / fuzzy / versification     : {s['exact']:,} / {s['fuzzy']:,} / {s['versification']:,}")
        print(f"  FLOOR                                : {floor:,}  ({pct(floor)})")
        print(f"     number-only (confident-wrong kill): {s['number_only']:,}")
        print(f"     multi same-name (HOT hand-check)  : {s['multi']:,}")
        print(f"     no corroboration                  : {s['none']:,}")
        if s["bookmiss"]:
            print(f"  (unmapped book token, skipped)       : {s['bookmiss']:,}")

    report_tier(1, "TIER 1 — ambiguous names (bind, verse-primary)")
    report_tier(2, "TIER 2 — unambiguous, NO metaV row (bind; was a bare AI blurb)")
    report_tier(3, "TIER 3 — unambiguous WITH a metaV row (LEFT on name-path)")

    print("\n" + "=" * 72)
    print("WS1 versification recoveries (documented + landed)")
    in_scope = stat[1]["versification"] + stat[2]["versification"]
    print(f"  ALL tiers : {sum(versification.values()):,}   (expect ~117: 116 Psa + 1 Num)")
    print(f"  in-scope (Tier 1+2, actually bound): {in_scope:,}")
    print(f"  Tier 3 (already handled by the name-path): {stat[3]['versification']:,}")
    for rule, n in sorted(versification.items(), key=lambda kv: -kv[1]):
        print(f"     {rule:22} {n:5}")
    # The Tier-3 share is "good news" ONLY if those occurrences RENDER on the existing
    # name-path, not sit in a floor. Every one here was classed versification => the
    # binder RENDERS it (a floor would show in number_only/none instead). And each is
    # an UNAMBIGUOUS name (<=1 person, <=1 place), so the live name-path returns that
    # one entity. Prove both; flag any exception loudly.
    if tier3_vers:
        ambl = [t for t in tier3_vers if t[5] > 1 or t[6] > 1 or (t[5] and t[6])]
        names = sorted({t[0] for t in tier3_vers})
        print(f"\n  Tier-3 WS1 recoveries — render-not-floor check: {len(tier3_vers)} occ, "
              f"{len(names)} names")
        print(f"     all classed 'versification' => binder RENDERS them (0 floored here)")
        print(f"     on an ambiguous name (name-path could pick wrong): {len(ambl)} "
              f"{'<- INVESTIGATE' if ambl else '(none — name-path is safe)'}")
        print(f"     names: {', '.join(names[:16])}{' ...' if len(names) > 16 else ''}")
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "pn_tier3_versification.txt"), "w", encoding="utf-8") as fh:
            for nm, bk, ch, vs, uniq, np, npl in sorted(tier3_vers):
                fh.write(f"{nm}\t{bk} {ch}:{vs}\t-> {uniq}\tperson_rows={np} place_rows={npl}\n")

    # collapse the grouped per-(name,verse) decisions
    g_render = sum(1 for v in group.values() if v[0] == "render")
    g_hot = sum(1 for v in group.values() if v[0] == "hot")
    print("\n" + "=" * 72)
    print("PER (book,chapter,verse,name) BINDINGS (what pn_binding will hold)")
    print(f"  render rows (a card will change)      : {g_render:,}")
    print(f"  HOT rows (floor; hand-check, step 5)  : {g_hot:,}")
    print(f"  number-only floors (suspects)         : {len(numonly_dump):,}")

    # write the hand-check dumps next to the script (read-only artifacts)
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "pn_binding_numonly.txt"), "w", encoding="utf-8") as fh:
        for nm, bk, ch, vs, B, heads in sorted(numonly_dump):
            fh.write(f"{nm}\t{bk} {ch}:{vs}\t#{B}\t{heads}\n")
    with open(os.path.join(here, "pn_binding_hot.txt"), "w", encoding="utf-8") as fh:
        for nm, bk, ch, vs, heads in sorted(hot_dump):
            fh.write(f"{nm}\t{bk} {ch}:{vs}\t{heads}\n")
    print("  wrote scripts/pn_binding_numonly.txt + scripts/pn_binding_hot.txt "
          "(hand-check residual)")

    conn.close()

    if not APPLY:
        print("\n[DRY-RUN] No tables written. Re-run with --apply once the counts look right.")
        return

    # ── --apply: write the three side tables (never touch words/verses) ────────
    print("\nWriting side tables...")
    used = {v[1] for v in group.values() if v[0] == "render"}
    by_uniq = {e["uniq"]: e for e in ents}
    w = sqlite3.connect(DB)
    try:
        w.execute("DROP TABLE IF EXISTS pn_binding")
        w.execute("DROP TABLE IF EXISTS tipnr_entity_refs")
        w.execute("DROP TABLE IF EXISTS tipnr_entities")
        w.execute("""CREATE TABLE tipnr_entities(
            uniq TEXT PRIMARY KEY, head TEXT, section TEXT, gender TEXT,
            area TEXT, descr TEXT, summary TEXT, bases TEXT)""")
        w.execute("""CREATE TABLE tipnr_entity_refs(
            uniq TEXT, book INTEGER, chapter INTEGER, verse INTEGER)""")
        w.execute("""CREATE TABLE pn_binding(
            book INTEGER, chapter INTEGER, verse INTEGER, name TEXT,
            entity_uniq TEXT, kind TEXT, rule TEXT, render INTEGER, hot INTEGER,
            tier INTEGER)""")
        for u in sorted(used):
            e = by_uniq[u]
            w.execute("INSERT OR REPLACE INTO tipnr_entities VALUES(?,?,?,?,?,?,?,?)",
                      (u, e["head"], e["section"], e["gender"], e["area"],
                       e["desc"], e["summary"], ",".join(sorted(e["bases"]))))
            w.executemany("INSERT INTO tipnr_entity_refs VALUES(?,?,?,?)",
                          [(u, bk, ch, vs) for (bk, ch, vs) in sorted(e["refs"])])
        for (bk, ch, vs, nm), (state, uniq, kind, rule, tier) in group.items():
            if state == "floor":
                continue
            w.execute("INSERT INTO pn_binding VALUES(?,?,?,?,?,?,?,?,?,?)",
                      (bk, ch, vs, nm, uniq, kind, rule,
                       1 if state == "render" else 0, 1 if state == "hot" else 0, tier))
        w.execute("CREATE INDEX ix_pn_binding ON pn_binding(book, chapter, verse, name)")
        w.execute("CREATE INDEX ix_tipnr_refs ON tipnr_entity_refs(uniq)")
        w.commit()
        print(f"  tipnr_entities  : {len(used):,}")
        print(f"  pn_binding      : render {g_render:,} + HOT {g_hot:,}")
        print("Done.")
    finally:
        w.close()


if __name__ == "__main__":
    main()
