#!/usr/bin/env python3
"""Ask-corpus provenance-rail PAYLOAD CONTRACT — pinned from the PRODUCING side.

The desktop rail (ProvenancePanel / _acWordGroups in the frontend) is a pure render of the
/api/ai-search payload. It badges words on three fields the backend stamps and nothing else
tests from the producer end:

  * grounded    — is the answer backed by a REAL occurrence, or just model knowledge?
  * contested   — does this in-scope word sit in the CONTESTED fork register?
  * alias_note  — the standard<->ABP numbering crosswalk ("· standard G2411"), or None.

If a refactor renames or drops one, or flips the grounding logic, the rail silently loses a
badge or shows a false one — a reader would never know. These lock the field NAMES + values
against the real producers (ai._compute_grounded / ai._stamp_rail_fields, the exact helpers
_assemble_payload calls). Pure — `import ai` needs no bible.db, no model. Run from repo root:
    python tests/test_rail_payload_contract.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ai
import contested_register


# ── grounded: the four branches, named exactly `grounded` on the payload ──

def test_grounded_no_results_is_false():
    # Nothing retrieved → not grounded, whatever the other signals say.
    assert ai._compute_grounded([], True, True, ["G4442"], lambda w: False) is False


def test_grounded_live_hit_is_true():
    results = [{"words": []}]
    # A real SQL hit grounds it.
    assert ai._compute_grounded(results, True, False, ["G4442"], lambda w: True) is True
    # A phrase hit grounds it.
    assert ai._compute_grounded(results, False, True, ["G4442"], lambda w: True) is True
    # A broad question (no target word) is grounded by having any verse at all.
    assert ai._compute_grounded(results, False, False, [], lambda w: True) is True


def test_grounded_falls_to_thematic_check():
    # No live hit, but there IS a target word: grounded only if some verse is non-thematic
    # (actually contains a target word). The stub reports every verse thematic → not grounded.
    results = [{"words": ["x"]}]
    assert ai._compute_grounded(results, False, False, ["G4442"], lambda w: True) is False
    # One verse non-thematic → grounded.
    assert ai._compute_grounded(results, False, False, ["G4442"], lambda w: not w) is True


# ── contested + alias_note: stamped from the ONE register, keyed by the real field names ──

def test_stamp_sets_both_field_names():
    data = [{"strongs": "G2316"}]           # theos — a fork word in the register
    ai._stamp_rail_fields(data)
    assert "contested" in data[0] and "alias_note" in data[0]   # the exact keys the rail reads


def test_contested_flag_matches_register():
    data = [{"strongs": "G2316"}, {"strongs": "G2962"}, {"strongs": "G4442"}]  # theos, kyrios, fire
    ai._stamp_rail_fields(data)
    assert data[0]["contested"] is True    # theos in CONTESTED_BY_SID
    assert data[1]["contested"] is True    # kyrios in CONTESTED_BY_SID
    assert data[2]["contested"] is False   # plain fire is not
    # No hard-coded list — it IS register membership.
    assert data[0]["contested"] == ("G2316" in contested_register.CONTESTED_BY_SID)


def test_alias_note_is_the_crosswalk_or_none():
    data = [{"strongs": "G5484"}, {"strongs": "G2413"}, {"strongs": "G4442"}]  # charis, temple, fire
    ai._stamp_rail_fields(data)
    assert data[0]["alias_note"]["standard"] == ["G5485"]   # charis: ABP G5484 -> standard G5485
    assert data[1]["alias_note"]["standard"] == ["G2411"]   # temple: ABP G2413 -> standard G2411
    assert data[2]["alias_note"] is None                    # plain fire: no crosswalk


def test_contested_and_alias_are_independent():
    # dikaioo G1344 is CONTESTED but NOT aliased — the two fields don't imply each other.
    data = [{"strongs": "G1344"}]
    ai._stamp_rail_fields(data)
    assert data[0]["contested"] is True
    assert data[0]["alias_note"] is None


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")


if __name__ == "__main__":
    _run()
