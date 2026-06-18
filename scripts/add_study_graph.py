#!/usr/bin/env python3
"""Add a hand-authored argument GRAPH straight into study.db (PA-only).

A graph is a pool of CLAIMS joined by per-tradition LINKS (see argmap.py). Each claim is
tagged with a provenance — text/lexicon are GROUNDED in the source; tradition/conjecture/
inference are NOT. Each link carries a strength (solid/contested/weak). The stress test
asks, for each tradition: is the conclusion reachable from grounded claims on solid links
alone? If not, it names the load-bearing joint.

    workon bible-env
    python scripts/add_study_graph.py             # DRY RUN: stress test + resolve verses, write nothing
    python scripts/add_study_graph.py --apply     # write it to study.db (published)

The stress-test verdict needs NO database (pure logic); the verse text resolves from
bible.db the same way the Study tab does. Re-running REPLACES the same graph (stable id),
so it's safe to tweak and run again. To author another graph, copy this file and edit the
block below.
"""
import argparse
import json
import os
import sys
import time

# scripts/ live one level below the app root, where argmap.py / core.py / views_study.py sit.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argmap   # pure logic, no database — safe to import anywhere

# ── The graph to add — edit this block ───────────────────────────────────────
GRAPH_ID = "baptism_who"             # stable id; re-running replaces this graph
TITLE = "Baptism — who should be baptized?"
INTRO = ("Both traditions read the same New Testament and reach opposite conclusions. "
         "This lays out each side's chain and asks where it actually load-bears.")
PUBLISHED = True                     # admin-only either way for now; True = ready to show when graphs go public

# Claims: the shared pool. Verse claims carry a `ref` (resolves to text, clickable in the
# reader); interpretive claims have no ref. provenance: text/lexicon grounded; the rest not.
CLAIMS = {
    # grounded source verses
    "v_acts2_38":  {"provenance": "text", "ref": "Acts 2:38",
                    "text": "Peter pairs baptism with repentance — 'repent and be baptized'"},
    "v_acts8_12":  {"provenance": "text", "ref": "Acts 8:12",
                    "text": "Samaritans were baptized after they believed Philip's preaching"},
    "v_mark16_16": {"provenance": "text", "ref": "Mark 16:16",
                    "text": "'Whoever believes and is baptized will be saved'"},
    "v_acts2_39":  {"provenance": "text", "ref": "Acts 2:39",
                    "text": "'The promise is to you and to your children'"},
    "v_households":{"provenance": "text", "ref": "Acts 16:33",
                    "text": "Whole households were baptized (Lydia, the jailer, Stephanas)"},
    "v_col2":      {"provenance": "text", "ref": "Colossians 2:11-12",
                    "text": "Baptism set beside circumcision — 'buried with him in baptism'"},
    "v_gen17":     {"provenance": "text", "ref": "Genesis 17:12",
                    "text": "Circumcision given to Abraham's household, infants included, as the covenant sign"},

    # interpretive claims (not grounded)
    "c_belief_first":     {"provenance": "inference",
                           "text": "In every baptism the New Testament narrates, the person first professed faith"},
    "c_covenant_kids":    {"provenance": "tradition",
                           "text": "Believers' children stay inside the covenant community, so the covenant sign still belongs to them"},
    "c_baptism_for_circ": {"provenance": "tradition",
                           "text": "Baptism is the new-covenant replacement for circumcision, so it goes to the same recipients — infants included"},
    "c_household_infants":{"provenance": "conjecture",
                           "text": "Those baptized households included infants"},

    # the two conclusions
    "t_credo": {"provenance": "conclusion",
                "text": "Therefore baptism is for those who personally profess faith"},
    "t_paedo": {"provenance": "conclusion",
                "text": "Therefore the infant children of believers should be baptized"},
}

OVERLAYS = [
    {
        "tradition": "Credobaptist (believer's baptism)",
        "thesis": "t_credo",
        "links": [
            {"from": "v_acts2_38",  "to": "c_belief_first", "relation": "supports", "strength": "solid"},
            {"from": "v_acts8_12",  "to": "c_belief_first", "relation": "supports", "strength": "solid"},
            {"from": "v_mark16_16", "to": "c_belief_first", "relation": "supports", "strength": "solid"},
            {"from": "c_belief_first", "to": "t_credo",     "relation": "supports", "strength": "solid"},
            {"from": "c_household_infants", "to": "t_credo", "relation": "undercuts", "strength": "contested",
             "note": "'Only believers' leans on silence — the household baptisms may have included children."},
        ],
    },
    {
        "tradition": "Paedobaptist (infant baptism)",
        "thesis": "t_paedo",
        "links": [
            {"from": "v_gen17",      "to": "c_covenant_kids", "relation": "supports", "strength": "contested"},
            {"from": "v_acts2_39",   "to": "c_covenant_kids", "relation": "supports", "strength": "contested"},
            {"from": "v_households", "to": "c_covenant_kids", "relation": "supports", "strength": "weak"},
            {"from": "c_covenant_kids",  "to": "c_baptism_for_circ", "relation": "supports", "strength": "contested"},
            {"from": "v_col2",           "to": "c_baptism_for_circ", "relation": "supports", "strength": "contested"},
            {"from": "c_baptism_for_circ", "to": "t_paedo",   "relation": "supports", "strength": "weak"},
        ],
    },
]
# ─────────────────────────────────────────────────────────────────────────────


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _build_json():
    return {"intro": INTRO, "claims": CLAIMS, "overlays": OVERLAYS, "notes": "", "related": []}


def _c(cid):
    c = CLAIMS.get(cid) or {}
    return c.get("text", cid)


def stress():
    """Print the stress-test verdict for every overlay — pure logic, no database."""
    out = argmap.analyze(CLAIMS, OVERLAYS)
    for ov, v in zip(OVERLAYS, out["verdicts"]):
        print("\n== %s ==" % ov["tradition"])
        print("  Conclusion: %s" % _c(ov["thesis"]))
        if v["grounded"]:
            print("  VERDICT: STANDS — reachable from the text on solid links alone.")
        elif v["gap"]:
            print("  VERDICT: INCOMPLETE — a step is missing; unreachable even granting every link.")
        else:
            print("  VERDICT: DEPENDS ON NON-SOLID JOINTS.")
            for l in v["load_bearing"]:
                print("    >>> load-bearing joint [%s]:" % l["strength"])
                print("        %s" % _c(l["from"]))
                print("          -> %s" % _c(l["to"]))
        for l in v["objections"]:
            print("    (open objection) %s" % (l.get("note") or (_c(l["from"]) + " attacks " + _c(l["to"]))))
    diff = out["diff"]
    print("\n== Where they part ==")
    print("  Verses both lean on: %s" % (", ".join(diff["shared_verses"]) or "(none — they cite different verses)"))


def dry_run():
    """Stress test (no db) + resolve every verse reference (from bible.db). Returns True if
    all references found text."""
    print("STRESS TEST  (no database needed)")
    print("=" * 70)
    stress()
    print("\n\nVERSE RESOLUTION  (from bible.db)")
    print("=" * 70)
    from views_study import _resolve_ref, _parse_ref   # imported here so the stress test runs without a db
    bad = []
    for cid, c in CLAIMS.items():
        ref = c.get("ref")
        if not ref:
            continue
        if not _parse_ref(ref):
            print("  [BAD REF]  %s  (%s)" % (ref, cid))
            bad.append(ref)
            continue
        hits = _resolve_ref(ref)
        text = " ".join(h["text"] for h in hits) if hits else ""
        if not text:
            print("  [NO TEXT]  %s  (%s)" % (ref, cid))
            bad.append(ref)
        else:
            print("  %s — %s" % (ref, text[:110] + ("..." if len(text) > 110 else "")))
    print("\n%d claims, %d verse refs, %d with a problem." %
          (len(CLAIMS), sum(1 for c in CLAIMS.values() if c.get("ref")), len(bad)))
    if bad:
        print("Fix these before --apply: %s" % ", ".join(bad))
    return not bad


def apply():
    from core import study_db
    conn = study_db()
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS entries ("
            " id TEXT PRIMARY KEY, type TEXT NOT NULL, title TEXT NOT NULL,"
            " json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft',"
            " created TEXT NOT NULL, updated TEXT NOT NULL,"
            " deleted INTEGER NOT NULL DEFAULT 0)"
        )
        now = _now()
        status = "published" if PUBLISHED else "draft"
        payload = json.dumps(_build_json(), ensure_ascii=False)
        existing = conn.execute("SELECT created FROM entries WHERE id=?", (GRAPH_ID,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE entries SET type='graph', title=?, json=?, status=?, updated=?, deleted=0"
                " WHERE id=?",
                (TITLE, payload, status, now, GRAPH_ID),
            )
            print("Updated existing graph '%s' (%s)." % (GRAPH_ID, status))
        else:
            conn.execute(
                "INSERT INTO entries (id, type, title, json, status, created, updated, deleted)"
                " VALUES (?, 'graph', ?, ?, ?, ?, ?, 0)",
                (GRAPH_ID, TITLE, payload, status, now, now),
            )
            print("Inserted new graph '%s' (%s)." % (GRAPH_ID, status))
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Add a hand-authored argument graph to study.db.")
    ap.add_argument("--apply", action="store_true", help="write to study.db (default is a dry run only)")
    args = ap.parse_args()

    ok = dry_run()
    if not args.apply:
        print("\n(dry run only — re-run with --apply once it looks right)")
        sys.exit(0)
    if not ok:
        print("\nRefusing to --apply while references have problems. Fix them first.")
        sys.exit(1)
    apply()
    print("\nDone. Open the Study tab -> Graphs -> %s to see it." % TITLE)
