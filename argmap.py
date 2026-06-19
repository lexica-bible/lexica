#!/usr/bin/env python3
"""Argument-map stress test engine — pure logic, no Flask, no database.

An argument is CLAIMS (boxes) joined by LINKS (arrows). Two tags make it Berean:
  - a claim's provenance:  text | lexicon  are GROUNDED in the source;
    tradition | conjecture | inference | observation | conclusion are NOT (they must be
    reached through links, not assumed).
  - a link's strength:  solid | contested | weak.

THE STRESS TEST: starting only from grounded claims and walking only SOLID links, can you
reach the conclusion? If yes, it stands on grounded ground. If not, name the LOAD-BEARING
link — the joint that, if cut, severs the conclusion.

OBJECTIONS ('undercuts' links) cut the other way. A grounded, SOLID objection knocks its
target claim out of the picture — if that target is the conclusion, the chain is OVERTURNED.
Contested/weak objections are raised but never decisive (the mirror of support: only solid
grounded steps move the verdict, in either direction).

ONE claim pool, MANY overlays (one per tradition). Each overlay brings its OWN links over
the shared claims and aims at its OWN conclusion. Comparing two overlays shows exactly
where they part.

It maps REASONING, not TRUTH: a chain can be solid by its own lights and still rest on a
reading you reject. The point is to make the structure inspectable.

Shapes (plain dicts, JSON-friendly — the same thing stored in a study entry):
  claims  = { "<id>": {"text": str, "provenance": str, "ref": str(optional)} }
  overlay = {"tradition": str, "thesis": "<claim id>", "links": [link, ...]}
  link    = {"from": "<id>", "to": "<id>", "relation": str, "strength": str, "note": str?}

Used by views_study.py (the Study tab's graph kind); covered by tests/test_argmap.py.
"""
from collections import Counter

GROUNDED = frozenset({"text", "lexicon"})           # provenance tags that stand on the source
CARRY = frozenset({"supports", "requires"})          # links that pass proof forward
RELATIONS = frozenset({"supports", "requires", "undercuts"})
STRENGTHS = frozenset({"solid", "contested", "weak"})
PROVENANCE = frozenset({"text", "lexicon", "tradition", "conjecture",
                        "inference", "observation", "conclusion"})
_ALL = STRENGTHS


def established(claims, links, allowed, blocked=frozenset()):
    """The claim ids you can stand on: start from the grounded claims, then walk only the
    links whose strength is in `allowed`, growing the set until it stops changing. A claim in
    `blocked` (knocked out by a decisive objection) is never added — proof can neither land on
    it nor pass through it."""
    est = {cid for cid, c in claims.items()
           if (c or {}).get("provenance") in GROUNDED and cid not in blocked}
    carry = [l for l in links if l.get("relation") in CARRY and l.get("strength") in allowed]
    changed = True
    while changed:
        changed = False
        for l in carry:
            if l.get("from") in est and l.get("to") not in est and l.get("to") not in blocked:
                est.add(l.get("to"))
                changed = True
    return est


def _knockouts(claims, links, standing):
    """Objections that BITE. An 'undercuts' link knocks its target claim out only if it clears
    the SAME bar a support must clear to prove something: the link is SOLID and its source
    itself stands on solid grounded ground (`standing`). A knock-down is as well-founded as a
    proof — the symmetry is the point. Contested/weak objections are raised but never decisive,
    exactly as a contested/weak support never establishes anything. Returns (defeated claim
    ids, the firing links)."""
    fired = [l for l in links
             if l.get("relation") == "undercuts" and l.get("strength") == "solid"
             and l.get("from") in standing]
    return {l.get("to") for l in fired}, fired


def stress_test(claims, overlay):
    """Findings for one overlay. Returns a plain dict:
      overturned   — the conclusion itself is knocked out by a decisive (grounded+solid) objection
      grounded     — the conclusion is reachable on grounded + solid links alone
      gap          — unreachable even granting EVERY link (a step is missing)
      load_bearing — non-solid links that are single points of failure (cut one, it falls)
      soft_steps   — the first non-solid links leaving the grounded+solid frontier
      defeated     — claim ids knocked out by a decisive objection (struck through in the chart)
      objections   — links tagged 'undercuts' (the full list; decisive ones populate `defeated`)
    """
    links = overlay.get("links") or []
    thesis = overlay.get("thesis")
    # Judge which objections bite against the solid frontier BEFORE any knockout, so a defeat
    # rests on solidly grounded ground — then re-establish with the knocked-out claims removed.
    standing = established(claims, links, {"solid"})
    defeated, _fired = _knockouts(claims, links, standing)
    solid = established(claims, links, {"solid"}, blocked=defeated)
    full = established(claims, links, _ALL, blocked=defeated)
    res = {
        "overturned": thesis in defeated,
        "grounded": (thesis in solid) and (thesis not in defeated),
        "gap": (thesis not in full) and (thesis not in defeated),
        "load_bearing": [],
        "soft_steps": [],
        "defeated": sorted(defeated),
        "objections": [l for l in links if l.get("relation") == "undercuts"],
    }
    if res["overturned"] or res["grounded"] or res["gap"]:
        return res
    carry = [l for l in links if l.get("relation") in CARRY]
    res["soft_steps"] = [l for l in carry if l.get("strength") != "solid" and l.get("from") in solid]
    for l in carry:
        if l.get("strength") == "solid":
            continue
        without = [x for x in carry if x is not l]
        if thesis not in established(claims, without, _ALL, blocked=defeated):
            res["load_bearing"].append(l)
    return res


def diff_overlays(claims, overlays):
    """Where the overlays part. Returns:
      shared_verses — grounded verses leaned on by >=2 sides (same verse, opposite pulls)
      private       — each side's own interpretive claims no other side touches
      seams         — a claim one side LEANS ON and another EXPLICITLY REJECTS (the
                      smuggled-claim exposure): [{claim, body, provenance, used_by, rejected_by}]
    """
    touched, rejects = [], []
    for ov in overlays:
        ids = set()
        for l in (ov.get("links") or []):
            if l.get("relation") in CARRY:          # "leans on" = supports/requires, not objections
                ids.add(l.get("from"))
                ids.add(l.get("to"))
        ids.discard(None)
        touched.append(ids)
        rejects.append(set(ov.get("rejects") or []))
    counts = Counter(c for ids in touched for c in ids)

    def prov(c):
        return (claims.get(c) or {}).get("provenance")

    shared_verses = sorted(c for c, n in counts.items() if n >= 2 and prov(c) in GROUNDED)
    private = {}
    for i, ids in enumerate(touched):
        private[i] = sorted(
            c for c in ids
            if counts[c] == 1 and prov(c) not in GROUNDED
        )
    seams = []
    candidates = set(counts) | (set().union(*rejects) if rejects else set())
    for cid in sorted(candidates):
        used_by = [overlays[i].get("tradition", "") for i, ids in enumerate(touched) if cid in ids]
        rejected_by = [overlays[i].get("tradition", "") for i, rej in enumerate(rejects) if cid in rej]
        if used_by and rejected_by:
            seams.append({
                "claim": cid, "body": (claims.get(cid) or {}).get("text", ""),
                "provenance": prov(cid), "used_by": used_by, "rejected_by": rejected_by,
            })
    return {"shared_verses": shared_verses, "private": private, "seams": seams}


def analyze(claims, overlays):
    """The single entry point the app calls: a verdict per overlay + the parting diff."""
    return {
        "verdicts": [stress_test(claims, ov) for ov in (overlays or [])],
        "diff": diff_overlays(claims, overlays or []),
    }
