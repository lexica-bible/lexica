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

GROUNDED = frozenset({"text", "lexicon"})           # provenance tags that stand on the source
CARRY = frozenset({"supports", "requires"})          # links that pass proof forward
RELATIONS = frozenset({"supports", "requires", "undercuts"})
STRENGTHS = frozenset({"solid", "contested", "weak"})
PROVENANCE = frozenset({"text", "lexicon", "tradition", "conjecture",
                        "inference", "observation", "conclusion"})
_ALL = STRENGTHS


def established(claims, links, allowed):
    """The claim ids you can stand on: start from the grounded claims, then walk only the
    links whose strength is in `allowed`, growing the set until it stops changing."""
    est = {cid for cid, c in claims.items() if (c or {}).get("provenance") in GROUNDED}
    carry = [l for l in links if l.get("relation") in CARRY and l.get("strength") in allowed]
    changed = True
    while changed:
        changed = False
        for l in carry:
            if l.get("from") in est and l.get("to") not in est:
                est.add(l.get("to"))
                changed = True
    return est


def stress_test(claims, overlay):
    """Findings for one overlay. Returns a plain dict:
      grounded     — the conclusion is reachable on grounded + solid links alone
      gap          — unreachable even granting EVERY link (a step is missing)
      load_bearing — non-solid links that are single points of failure (cut one, it falls)
      soft_steps   — the first non-solid links leaving the grounded+solid frontier
      objections   — links tagged 'undercuts' (noted, not yet scored)
    """
    links = overlay.get("links") or []
    thesis = overlay.get("thesis")
    solid = established(claims, links, {"solid"})
    full = established(claims, links, _ALL)
    res = {
        "grounded": thesis in solid,
        "gap": thesis not in full,
        "load_bearing": [],
        "soft_steps": [],
        "objections": [l for l in links if l.get("relation") == "undercuts"],
    }
    if res["grounded"] or res["gap"]:
        return res
    carry = [l for l in links if l.get("relation") in CARRY]
    res["soft_steps"] = [l for l in carry if l.get("strength") != "solid" and l.get("from") in solid]
    for l in carry:
        if l.get("strength") == "solid":
            continue
        without = [x for x in carry if x is not l]
        if thesis not in established(claims, without, _ALL):
            res["load_bearing"].append(l)
    return res


def diff_overlays(claims, overlays):
    """Where the overlays part: the grounded verses they ALL lean on, and each overlay's
    OWN interpretive claims (non-grounded, non-conclusion) the others never touch.
    Returns {"shared_verses": [id...], "private": {overlay_index: [id...]}}."""
    touched = []
    for ov in overlays:
        ids = set()
        for l in (ov.get("links") or []):
            ids.add(l.get("from"))
            ids.add(l.get("to"))
        ids.discard(None)
        touched.append(ids)
    shared = set.intersection(*touched) if touched else set()
    shared_verses = sorted(c for c in shared if (claims.get(c) or {}).get("provenance") in GROUNDED)
    private = {}
    for i, ids in enumerate(touched):
        others = set().union(*[t for j, t in enumerate(touched) if j != i]) if len(touched) > 1 else set()
        private[i] = sorted(
            c for c in ids
            if c not in others
            and (claims.get(c) or {}).get("provenance") not in GROUNDED
            and (claims.get(c) or {}).get("provenance") != "conclusion"
        )
    return {"shared_verses": shared_verses, "private": private}


def analyze(claims, overlays):
    """The single entry point the app calls: a verdict per overlay + the parting diff."""
    return {
        "verdicts": [stress_test(claims, ov) for ov in (overlays or [])],
        "diff": diff_overlays(claims, overlays or []),
    }
