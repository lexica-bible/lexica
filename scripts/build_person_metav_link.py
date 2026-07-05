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
    tier2_audit = []   # (uniq, name_key, win_pid, win_name, score, margin, n_pool)

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

        refs = ent_refs.get(uniq, set())

        if len(pool) == 1:
            # a lone name-mate Strong's couldn't confirm. RETIRED rule -> demote to
            # residual (unconfirmed; coverage is not quality). Carry a diagnostic so we
            # can eyeball whether any deserve rescuing.
            c = pool[0]
            cont = (len(refs & mp_verses.get(c, set())) / len(refs)) if refs else 0.0
            buckets["name_only"].append(
                (uniq, c, name_of.get(c, "?"), len(refs), len(mp_verses.get(c, set())),
                 bool(mp_strongs.get(c)), cont))
            continue

        # ── Tier 2: verse-overlap containment ──────────────────────────────────
        scored = []
        if refs:
            for c in pool:
                inter = len(refs & mp_verses.get(c, set()))
                scored.append((inter / len(refs), c))
            scored.sort(reverse=True)
        top = scored[0][0] if scored else 0.0
        runner = scored[1][0] if len(scored) > 1 else 0.0
        r_pid = scored[1][1] if len(scored) > 1 else None
        if scored and top >= CONTAIN_FLOOR and (len(scored) == 1 or top > runner):
            win_pid = scored[0][1]
            buckets["overlap"].append((uniq, win_pid, "overlap"))
            tier2_audit.append((uniq, key(disp), win_pid, name_of.get(win_pid, "?"),
                                top, top - runner, len(pool), r_pid,
                                name_of.get(r_pid, "-"), runner))
        else:
            reason = ("no_refs" if not refs else
                      "tie" if top == runner and top > 0 else "below_floor")
            buckets["residual"].append((uniq, pool, top, reason))

    # ── the links we'll actually write, each with its rule + confidence ──────────
    #     name_only is DEMOTED (retired rule, unconfirmed) — not linked.
    link_meta = [(u, pid, "strongs", 1.0, 1.0) for (u, pid, _r) in buckets["strongs"]]
    for (u, _k, pid, _n, score, margin, *_rest) in tier2_audit:
        link_meta.append((u, pid, "overlap", score, margin))
    linked_uniq = {m[0] for m in link_meta}

    with_cand = set()
    for b in ("strongs", "overlap", "name_only", "residual"):
        for row in buckets[b]:
            with_cand.add(row[0])
    all_person_traffic = sum(traffic[u] for u in traffic)
    cand_traffic = sum(traffic[u] for u in with_cand)
    linked_traffic = sum(traffic[u] for u in linked_uniq)

    def pct(a, b):
        return f"{100*a/b:4.1f}%" if b else "  n/a"

    print("=" * 70)
    print("build_person_metav_link — DRY-RUN three-tier report")
    print(f"  Tier 1 Strong's-direct : {len(buckets['strongs']):>5}  (linked)")
    print(f"  Tier 2 verse-overlap   : {len(buckets['overlap']):>5}  (linked)")
    print(f"  name-only DEMOTED->resid: {len(buckets['name_only']):>5}  (not linked)")
    print(f"  RESIDUAL (hand-list)   : {len(buckets['residual']):>5}")
    print(f"  no metaV record        : {len(buckets['no_metav']):>5}")
    total = sum(len(v) for v in buckets.values())
    print(f"  ------ {total} TIPNR person entities;  {len(link_meta)} LINKED")
    print()
    print("  traffic coverage (render-count proxy for card views):")
    print(f"    linked / all rendered person entities   : "
          f"{linked_traffic:,} / {all_person_traffic:,}  ({pct(linked_traffic, all_person_traffic)})")
    print(f"    linked / entities with a metaV candidate : "
          f"{linked_traffic:,} / {cand_traffic:,}  ({pct(linked_traffic, cand_traffic)})")

    # ── tier-2 confidence audit ──────────────────────────────────────────────────
    band = {"1.0 (all refs found)": 0, "0.8-0.99": 0, "0.65-0.8": 0, "0.5-0.65": 0}
    thin = []
    lowband = []
    for row in tier2_audit:
        score, margin = row[4], row[5]
        if score >= 0.999:
            band["1.0 (all refs found)"] += 1
        elif score >= 0.8:
            band["0.8-0.99"] += 1
        elif score >= 0.65:
            band["0.65-0.8"] += 1
        else:
            band["0.5-0.65"] += 1
            lowband.append(row)
        if margin < 0.15:
            thin.append(row)
    print("\n  tier-2 containment score distribution:")
    for k, v in band.items():
        print(f"    {k:<22}: {v:>5}")

    def show(row):
        u, _k, pid, wname, score, margin, npool, r_pid, r_name, r_score = row
        print(f"    {u:<26} -> {pid}:{wname:<12} score {score:.2f} margin {margin:.2f} "
              f"(of {npool})  runner {r_pid}:{r_name} {r_score:.2f}")

    print(f"\n  ** LOW-CONFIDENCE picks you asked to eyeball (move any wrong one to residual) **")
    print(f"  thin margin (<0.15 over runner-up): {len(thin)}")
    for row in sorted(thin):
        show(row)
    print(f"  score band 0.5-0.65: {len(lowband)}")
    for row in sorted(lowband):
        show(row)

    # hard-name eyeball (unchanged watchlist)
    watch = ("simon", "james", "mary", "herod", "joseph")
    a_by_key = defaultdict(list)
    for row in tier2_audit:
        a_by_key[row[1]].append(row)
    print("\n  tier-2 picks for a few hard names:")
    for nm in watch:
        for row in sorted(a_by_key.get(nm, [])):
            show(row)

    t2path = os.path.join(HERE, "person_metav_link_tier2.txt")
    with open(t2path, "w", encoding="utf-8") as fh:
        fh.write("# uniq\twin_pid\twin_name\tscore\tmargin\tpool\trunner_pid\trunner_score\n")
        for row in sorted(tier2_audit):
            u, _k, pid, wname, score, margin, npool, r_pid, _rn, r_score = row
            fh.write(f"{u}\t{pid}\t{wname}\t{score:.3f}\t{margin:.3f}\t{npool}\t{r_pid}\t{r_score:.3f}\n")
    print(f"  full tier-2 dump -> scripts/person_metav_link_tier2.txt")

    # ── name-only (demoted) detail — justify or leave demoted ────────────────────
    print(f"\n  name-only demoted picks (7 expected) — refs / metaV-verses / has# / containment:")
    for (u, pid, pname, nrefs, nvers, has_s, cont) in sorted(buckets["name_only"]):
        print(f"    {u:<26} -> {pid}:{pname:<14} refs {nrefs:>3} mvers {nvers:>4} "
              f"has# {has_s}  contain {cont:.2f}")

    # ── residual, ranked by traffic, WITH the reason it failed ───────────────────
    res = sorted(buckets["residual"], key=lambda x: -traffic[x[0]])
    path = os.path.join(HERE, "person_metav_link_residual.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# uniq\ttraffic\treason\tbest_score\tcandidates\n")
        for uniq, cands, best, reason in res:
            names = [f"{c}:{name_of.get(c,'?')}" for c in cands]
            fh.write(f"{uniq}\t{traffic[uniq]}\t{reason}\t{best:.2f}\t{names}\n")
    print(f"\n  residual -> scripts/person_metav_link_residual.txt ({len(res)} to hand-resolve)")
    print("  top 15 residual by traffic (reason = why overlap didn't settle it):")
    for uniq, cands, best, reason in res[:15]:
        print(f"    {traffic[uniq]:>4}  {uniq:<24} {len(cands):>2} cands  "
              f"best {best:.2f}  [{reason}]")

    if not APPLY:
        conn.close()
        print("\n[DRY-RUN] No table written. Review the eyeball lists, then --apply.")
        return

    conn.close()
    w = sqlite3.connect(BIBLE)
    try:
        cols = {r[1] for r in w.execute("PRAGMA table_info(tipnr_metav_link)")}
        if not cols:
            w.execute("CREATE TABLE tipnr_metav_link("
                      "uniq TEXT, kind TEXT, metav_id INTEGER, rule TEXT, score REAL, margin REAL)")
        else:  # place edition may have made a 3-col table first — widen it
            for c, t in (("rule", "TEXT"), ("score", "REAL"), ("margin", "REAL")):
                if c not in cols:
                    w.execute(f"ALTER TABLE tipnr_metav_link ADD COLUMN {c} {t}")
        w.execute("DELETE FROM tipnr_metav_link WHERE kind='person'")   # leave place rows intact
        w.executemany("INSERT INTO tipnr_metav_link(uniq,kind,metav_id,rule,score,margin) "
                      "VALUES(?,'person',?,?,?,?)",
                      [(u, pid, rule, score, margin) for (u, pid, rule, score, margin) in link_meta])
        w.execute("CREATE INDEX IF NOT EXISTS ix_tipnr_metav_link ON tipnr_metav_link(uniq)")
        w.commit()
        print(f"\nWrote {len(link_meta)} kind='person' rows into tipnr_metav_link "
              f"(rule/score/margin recorded).")
    finally:
        w.close()


if __name__ == "__main__":
    main()
