#!/usr/bin/env python3
"""Engine tests for argmap.py — pure logic, no database (like the other invariant tests).

Run:  python -m pytest tests/test_argmap.py     (or)     python tests/test_argmap.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argmap

# A tiny synthetic graph: two grounded verses, one interpretive claim, one conclusion.
CLAIMS = {
    "v1": {"text": "verse one", "provenance": "text"},
    "v2": {"text": "verse two", "provenance": "text"},
    "c1": {"text": "an interpretive bridge", "provenance": "tradition"},
    "t":  {"text": "the conclusion", "provenance": "conclusion"},
}

# A: grounded verse --solid--> conclusion. Stands on solid ground.
OV_PASS = {"tradition": "A", "thesis": "t", "links": [
    {"from": "v1", "to": "t", "relation": "supports", "strength": "solid"},
]}

# B: only reachable through a contested then a weak link. Depends on non-solid joints.
OV_DEPENDS = {"tradition": "B", "thesis": "t", "links": [
    {"from": "v1", "to": "c1", "relation": "supports", "strength": "contested"},
    {"from": "c1", "to": "t",  "relation": "supports", "strength": "weak"},
]}

# C: a missing step — nothing links to the conclusion at all.
OV_GAP = {"tradition": "C", "thesis": "t", "links": [
    {"from": "v1", "to": "c1", "relation": "supports", "strength": "solid"},
]}


def test_grounded_passes():
    r = argmap.stress_test(CLAIMS, OV_PASS)
    assert r["grounded"] is True
    assert r["gap"] is False
    assert r["load_bearing"] == []


def test_depends_finds_load_bearing():
    r = argmap.stress_test(CLAIMS, OV_DEPENDS)
    assert r["grounded"] is False          # not reachable on solid alone
    assert r["gap"] is False               # but reachable once non-solid links count
    assert r["load_bearing"]               # at least one single-point-of-failure joint
    # the final weak joint into the conclusion must be flagged
    assert any(l["to"] == "t" and l["strength"] == "weak" for l in r["load_bearing"])


def test_gap_detected():
    r = argmap.stress_test(CLAIMS, OV_GAP)
    assert r["gap"] is True
    assert r["grounded"] is False


def test_diff_separates_shared_and_private():
    d = argmap.diff_overlays(CLAIMS, [OV_PASS, OV_DEPENDS])
    assert "v1" in d["shared_verses"]      # both overlays lean on v1
    assert "c1" in d["private"][1]         # the interpretive bridge is unique to overlay B
    assert d["private"][0] == []           # overlay A introduces no interpretive claim


def test_seams_from_rejects():
    # B leans on the tradition claim c1; A explicitly rejects it -> a seam.
    a = dict(OV_PASS, rejects=["c1"])
    d = argmap.diff_overlays(CLAIMS, [a, OV_DEPENDS])
    assert any(s["claim"] == "c1" and s["rejected_by"] == ["A"] and "B" in s["used_by"]
               for s in d["seams"])


def test_analyze_bundles_everything():
    out = argmap.analyze(CLAIMS, [OV_PASS, OV_DEPENDS, OV_GAP])
    assert len(out["verdicts"]) == 3
    assert out["verdicts"][0]["grounded"] is True
    assert out["verdicts"][2]["gap"] is True
    assert "diff" in out


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("ok  -", fn.__name__)
    print("\nAll %d argmap tests passed." % len(fns))
