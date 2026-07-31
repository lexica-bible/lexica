"""Regression lock for the strict name-match Greek-number inheritance
(G707 class, JP-signed predicate 2026-07-31 —
docs/tickets/PREDICATE_g707_name_match.md).

Pure-local: parses the vendored tipnr/TIPNR.txt with the PRODUCTION parser and
matcher from build_pn_greek_identity (never a copy). Pins:
  G1  the fix pair — the Mizpah record's sole Greek number G707 attaches to
      Arimathea ONLY; Mizpah/Mizpeh/Ramah/Ramathaim-zophim must NOT match.
  G2  same-name Greek dress keeps its number — Elijah G2243, Noah G3575,
      Rehoboam G4497 (if these fail the predicate got too strict).
  Control — under the old pooling (every record name treated as attached),
      mizpah WOULD match: proves the matcher can see the bug class.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, os.path.join(_HERE, "..", "scripts"))

import entity_resolution as er
from build_pn_greek_identity import parse_number_forms, name_matches

TIPNR = os.path.join(_HERE, "..", "tipnr", "TIPNR.txt")


def _load():
    lines = open(TIPNR, encoding="utf-8-sig").read().splitlines()
    return er.parse_tipnr(lines), parse_number_forms(lines)


ENTS, (ENT_FORMS, GLOB_FORMS) = _load()


def _sole_greek(uniq):
    e = next(x for x in ENTS if x["uniq"] == uniq)
    gs = sorted(b for b in e["bases"] if b.startswith("G"))
    return e, gs


def test_g1_mizpah_record_g707_is_arimathea_only():
    e, gs = _sole_greek("Mizpah@Jos.18.26-Jhn")
    assert gs == ["G707"]
    forms = ENT_FORMS[e["uniq"]]["G707"]
    assert name_matches("arimathea", forms)
    for s in ("mizpah", "mizpeh", "ramah", "ramathaim-zophim"):
        assert not name_matches(s, forms), f"{s} must not inherit G707"


def test_g2_same_name_greek_dress_keeps_its_number():
    for uniq, nm, g in (("Elijah@1Ki.17.1-Jas", "elijah", "G2243"),
                        ("Noah@Gen.5.29-2Pe", "noah", "G3575"),
                        ("Rehoboam@1Ki.11.43-Mat", "rehoboam", "G4497")):
        e, gs = _sole_greek(uniq)
        assert gs == [g], f"{uniq}: sole Greek expected {g}, got {gs}"
        assert name_matches(nm, ENT_FORMS[uniq][g]), \
            f"{uniq}: {nm} must keep {g} — predicate too strict"


def test_decorated_and_split_name_rules():
    # Sinai keeps its own number though TIPNR decorates it ("Sinai_Mount",
    # "(Mount )Sinai") — the checker-caught too-strict drop of 2026-07-31.
    assert name_matches("sinai", ENT_FORMS["Sinai@Exo.3.1-Gal"]["G4614"]), \
        "sinai must keep G4614 (decorated-name handling broke)"
    # A word split out of a multi-word form must NOT vouch for the number when
    # it is another record's own name: 'Sheba' from "Queen of Sheba" (F1
    # receipt: sheba@1Ki.10.4 would have swapped G3558->G938).
    assert not name_matches(
        "sheba", ENT_FORMS["Queen_of_Sheba@1Ki.10.1-Luk"]["G938"]), \
        "sheba must not vouch for G938 (split-token over-attach returned)"


def test_control_pooled_forms_would_match():
    e = next(x for x in ENTS if x["uniq"] == "Mizpah@Jos.18.26-Jhn")
    assert name_matches("mizpah", e["spellings"]), \
        "control dead: pooled (old-rule) forms no longer flag mizpah"


def test_worst_cross_names_gated():
    # The named worst cases from the sweep: the foreign OT name must not
    # match the record's Greek-number forms.
    for uniq, g, ot_name in (("Megiddo@Jos.12.21-Rev", "G717", "megiddo"),
                             ("Sheba@1Ki.10.1-Luk", "G3558", "sheba"),
                             ("Jehoiada@2Ki.11.4-Mat", "G914", "jehoiada"),
                             ("Sepharad@Oba.1.20-Rev", "G4554", "sepharad")):
        forms = ENT_FORMS.get(uniq, {}).get(g, set())
        assert forms, f"{uniq}: no forms parsed for {g}"
        assert not name_matches(ot_name, forms), \
            f"{uniq}: {ot_name} must not inherit {g}"


if __name__ == "__main__":
    test_g1_mizpah_record_g707_is_arimathea_only()
    test_g2_same_name_greek_dress_keeps_its_number()
    test_decorated_and_split_name_rules()
    test_control_pooled_forms_would_match()
    test_worst_cross_names_gated()
    print("test_pn_name_match: all checks passed")
