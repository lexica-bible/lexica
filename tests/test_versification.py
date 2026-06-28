#!/usr/bin/env python3
"""Engine tests for entity_resolution.py — pure logic, no database (like the other
invariant tests). Locks the WS1 documented versification map + the shared book/name
helpers so a future edit can't silently change which references the binder will test.

Run:  python -m pytest tests/test_versification.py   (or)   python tests/test_versification.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import entity_resolution as er


# ── book / name / ref helpers ───────────────────────────────────────────────
def test_book_num_abp_and_tipnr_spellings_agree():
    # ABP spellings and TIPNR spellings must resolve to the SAME canonical number.
    assert er.book_num("Psa") == 19 and er.book_num("psalm") == 19
    assert er.book_num("Num") == 4
    assert er.book_num("Mal") == 39
    assert er.book_num("Eze") == er.book_num("Ezk") == 26   # ABP vs TIPNR
    assert er.book_num("Joe") == er.book_num("Jol") == 29
    assert er.book_num("Mar") == er.book_num("Mrk") == 41
    assert er.book_num("Rth") == er.book_num("Rut") == 8
    assert er.book_num("nope") is None and er.book_num("") is None


def test_norm_name_strips_trailing_punctuation_and_lowers():
    assert er.norm_name("Eden,") == "eden"
    assert er.norm_name("  Beth-el. ") == "beth-el"   # internal hyphen kept
    assert er.norm_name("CUSHI") == "cushi"
    assert er.norm_name("") == "" and er.norm_name(None) == ""


def test_norm_base_prefixed_and_zero_padded():
    assert er.norm_base("H0175A") == "H175"
    assert er.norm_base("G0002") == "G2"
    assert er.norm_base("H3569") == "H3569"
    assert er.norm_base("") == "" and er.norm_base("*") == ""


def test_parse_ref_handles_lxx_letters_and_unknown_books():
    assert er.parse_ref("Ezk.31.18a") == (26, 31, 18)     # letter suffix -> start
    assert er.parse_ref("LXX Psa.3.2") == (19, 3, 2)       # LXX prefix stripped
    assert er.parse_ref("Gen.2.13") == (1, 2, 13)
    assert er.parse_ref("Foo.1.1") is None                 # unknown book
    assert er.parse_ref("Gen.1") is None                   # not enough parts


# ── WS1 versification map ────────────────────────────────────────────────────
def test_psalms_superscription_plus_one():
    assert er.documented_remaps(19, 3, 1) == [(19, 3, 2, "Psa:superscription")]
    assert er.documented_remaps(19, 51, 5) == [(19, 51, 6, "Psa:superscription")]


def test_numbers_16_17_korah_both_directions():
    # English 16:36-50 == Hebrew 17:1-15
    assert er.documented_remaps(4, 17, 1) == [(4, 16, 36, "Num16/17")]
    assert er.documented_remaps(4, 17, 15) == [(4, 16, 50, "Num16/17")]
    # a Numbers-17 verse past v15 maps back to English 17:(v-15)
    assert er.documented_remaps(4, 17, 16) == [(4, 17, 1, "Num16/17")]
    # other Numbers chapters carry no offset
    assert er.documented_remaps(4, 16, 1) == []


def test_malachi_3_4():
    assert er.documented_remaps(39, 3, 19) == [(39, 4, 1, "Mal3/4")]
    assert er.documented_remaps(39, 3, 18) == []   # below the split point


def test_floor_class_books_have_no_documented_offset():
    # Lev / Est / Lam carry NO clean verse-offset rule -> floored by design.
    for bk in (3, 17, 25):           # Leviticus, Esther, Lamentations
        assert er.documented_remaps(bk, 1, 1) == []
    # an ordinary narrative book too
    assert er.documented_remaps(1, 2, 13) == []    # Genesis


# ── WS2 name normalization ───────────────────────────────────────────────────
def test_gentilic_roots_strip_endings():
    # the root we need must be among the candidates; extra safe candidates (e.g.
    # 'cushites' also yields 'cushite' via -s) are fine — number-guarded downstream.
    assert "cush" in er.gentilic_roots("Cushites")
    assert er.gentilic_roots("cushite") == {"cush"}
    assert er.gentilic_roots("Cushi") == {"cush"}        # the -i Hebrew gentilic
    assert er.gentilic_roots("Moabite") == {"moab"}
    assert "israel" in er.gentilic_roots("Israelites")
    # short fragments are not produced (no 1-2 char roots)
    assert "e" not in er.gentilic_roots("Eli")


def test_name_variants_hits_the_brief_canaries():
    # the four named WS2/WS3 transliteration canaries
    assert "perez" in er.name_variants("Pharez")
    assert "jehoiachin" in er.name_variants("Jeconiah")
    assert "shealtiel" in er.name_variants("Salathiel")
    assert "egypt" in er.name_variants("Mizraim")
    # cushi reaches cush by stem (the runner — still number-guarded + needs step 4)
    assert "cush" in er.name_variants("Cushi")
    # irregular gentilic via stem -> alias chain
    assert "heth" in er.name_variants("Hittites")


def test_name_variants_excludes_the_exact_name():
    # the exact normalized name is the binder's UNGUARDED tier-1 path, never a
    # fuzzy variant — so it must not appear in the fuzzy candidate set.
    assert "judah" not in er.name_variants("Judah")
    assert er.name_variants("Zogwxyz") == set()   # nothing matches -> empty


# ── The binder + global render rule ──────────────────────────────────────────
def _fixture():
    """Hand-built TIPNR entities (no parsing) so the binder logic is explicit.
    e0 Cush (place, the Cushite numbers), e1 Cushi (person, the mis-stored H3570),
    two same-verse Edens (e2/e3, the multi case), e4 Asaph (Psalms superscription)."""
    ents = [
        {"head": "cush", "section": "place",
         "spellings": {"cush", "cushite", "cushites"}, "bases": {"H3568", "H3569"},
         "refs": {(1, 2, 13), (10, 18, 21)}},                       # Gen 2:13, 2Sa 18:21
        {"head": "cushi", "section": "person",
         "spellings": {"cushi"}, "bases": {"H3570"}, "refs": {(36, 1, 1)}},  # Zep 1:1
        {"head": "eden", "section": "place",
         "spellings": {"eden"}, "bases": {"H5731"}, "refs": {(1, 2, 8)}},
        {"head": "eden", "section": "person",
         "spellings": {"eden"}, "bases": {"H5729"}, "refs": {(1, 2, 8), (13, 4, 17)}},
        {"head": "asaph", "section": "person",
         "spellings": {"asaph"}, "bases": {"H623"}, "refs": {(19, 50, 2)}},
    ]
    name_idx, base_idx = er.build_indexes(ents)
    return ents, name_idx, base_idx


def _bind(name, bk, ch, vs, base):
    ents, name_idx, base_idx = _fixture()
    return er.bind_occurrence(ents, name_idx, base_idx, name, bk, ch, vs, base)


def test_exact_name_verse_renders_number_is_metadata():
    b = _bind("Cush", 1, 2, 13, "H3568")
    assert b.render and b.kind == "exact" and b.entity == 0
    # a WRONG/polluted number on an exact name+verse hit is ignored — still renders.
    b2 = _bind("Cush", 1, 2, 13, "H9999")
    assert b2.render and b2.kind == "exact" and b2.entity == 0


def test_number_only_never_renders():
    # name matches nothing at the verse, but the stored number does -> confident-wrong
    # path, must FLOOR (the disease the rebuild kills).
    b = _bind("Zzz", 36, 1, 1, "H3570")
    assert not b.render and b.kind == "number_only" and b.candidates == [1]


def test_multi_same_name_at_one_verse_floors_hot():
    b = _bind("Eden", 1, 2, 8, "H5731")
    assert not b.render and b.kind == "multi" and b.hot and b.candidates == [2, 3]


def test_versification_recovers_psalms_superscription():
    # Asaph printed at Psa 50:1; entity lists 50:2 (Hebrew +1). The map recovers it.
    b = _bind("Asaph", 19, 50, 1, "H623")
    assert b.render and b.kind == "versification" and b.rule == "Psa:superscription" \
        and b.entity == 4


def test_no_corroboration_floors():
    b = _bind("Nobody", 5, 5, 5, "")
    assert not b.render and b.kind == "none" and b.entity is None


def test_cushi_runner_needs_the_by_verse_number_fix():
    # The WS2 canary: 'Cushi' at 2Sa 18:21 stems to Cush, which lists the verse.
    # BEFORE step 4 the stored number is H3570 (not in Cush's cluster) -> fuzzy's
    # second key fails -> floor (honest, no wrong card).
    pre = _bind("Cushi", 10, 18, 21, "H3570")
    assert not pre.render
    # AFTER the by-verse fix (H3569, the Cushite form, IS in Cush's cluster) -> the
    # number agrees, so it binds & renders by name+verse.
    post = _bind("Cushi", 10, 18, 21, "H3569")
    assert post.render and post.kind == "fuzzy" and post.entity == 0


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  ok   {fn.__name__}")
        except Exception:
            failed += 1
            print(f"  FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
