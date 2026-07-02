"""
test_lexica_coverage.py — PIECE A (collocation pre-check) unit tests.

Builds its own in-memory word/verse fixture (no bible.db) and proves the collocation detector:
  - finds an adjacent-lemma pattern across an intervening article (the "son of man" shape),
  - counts DISTINCT verses,
  - flags a collocation the fed draw missed, and NOT one it represented,
  - honors the floor and the ordinal window,
  - stop-lists function words (article/kai) so they never flood.

Imports only lexica_coverage (stdlib-only) — adds no CI dependency.
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lexica_coverage as C


HUIOS, ANTHROPOS, ARTICLE, THEOS, LEGO = "G5207", "G444", "G3588", "G2316", "G3004"


def _conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT);
        CREATE TABLE words (verse_id INT, position INT, strongs TEXT, strongs_base TEXT, english_head TEXT);
        CREATE TABLE lexicon (strongs_g TEXT, lemma TEXT, translit TEXT);
    """)
    conn.executemany("INSERT INTO lexicon VALUES (?,?,?)", [
        (HUIOS, "υἱός", "huios"),
        (ANTHROPOS, "ἄνθρωπος", "anthrōpos"),
        (ARTICLE, "ὁ", "ho"),
        (THEOS, "θεός", "theos"),
        (LEGO, "λέγω", "legō"),
    ])
    return conn


def _add_verse(conn, vid, book, ch, vs, tokens):
    """tokens = list of (strongs_base, english_head); positions assigned in order."""
    conn.execute("INSERT INTO verses VALUES (?,?,?,?,?)", (vid, book, ch, vs, "…"))
    for pos, (base, head) in enumerate(tokens):
        conn.execute("INSERT INTO words VALUES (?,?,?,?,?)",
                     (vid, pos, base[1:], base, head))


def _occs(conn, sid):
    """The target's occurrence rows, shaped like build_lexica_def.occurrences()."""
    rows = conn.execute("""
        SELECT v.book AS book, v.chapter AS ch, v.verse AS vs, w.english_head AS rend,
               w.verse_id AS vid, w.position AS pos
        FROM verses v JOIN words w ON w.verse_id = v.id
        WHERE w.strongs_base = ? ORDER BY v.id, w.position""", (sid,)).fetchall()
    return [dict(r) for r in rows]


FILLER = "G9999"   # a background word, present in neither lexicon nor near the target


def _son_of_man_fixture(article=True):
    """A corpus where 'son of man' is a TIGHT phrase and 'son said' is a LOOSE-but-frequent pair:
      - 12 'son of man' verses: huios + [article] + anthrōpos   (anthrōpos appears ONLY here → tight)
      - 12 'son said'   verses: huios + [article] + legō        (legō is everywhere → loose)
      - 300 background verses with legō alone                    (makes legō common)
      - 200 filler verses                                        (inflate the corpus size Nv)
    So anthrōpos scores high (rarely seen except beside huios) and legō scores ~0 (common)."""
    conn = _conn()
    vid = 1

    def mid():
        return [(ARTICLE, "the")] if article else []

    for _ in range(12):                                    # son-of-man (vids 1..12) — tight
        _add_verse(conn, vid, "Mat", vid, 1, [(HUIOS, "son")] + mid() + [(ANTHROPOS, "man")])
        vid += 1
    for _ in range(12):                                    # son-said (vids 13..24) — loose/frequent
        _add_verse(conn, vid, "Mar", vid, 1, [(HUIOS, "son")] + mid() + [(LEGO, "said")])
        vid += 1
    for _ in range(300):                                   # legō everywhere else
        _add_verse(conn, vid, "Luk", vid, 1, [(LEGO, "said"), (FILLER, "x")])
        vid += 1
    for _ in range(200):                                   # pure filler, inflate Nv
        _add_verse(conn, vid, "Joh", vid, 1, [(FILLER, "x"), (FILLER, "y")])
        vid += 1
    return conn


# vid ranges for the fixture above
SOM_VIDS = set(range(1, 13))       # son-of-man verses
SAID_VIDS = set(range(13, 25))     # son-said verses


def test_flags_tight_pair_missed_but_not_loose_one():
    conn = _son_of_man_fixture(article=True)
    occs = _occs(conn, HUIOS)
    sample_vids = set()                           # empty draw — BOTH pairs are "0 in draw"
    stop = C.function_bare_strongs(conn)          # no lsj table → override set (has the article)
    findings = C.scan_collocations(conn, HUIOS, occs, sample_vids, stop=stop,
                                   floor=10, window=2, pmi_min=4.0)

    by = {f["neighbor"]: f for f in findings}
    assert ANTHROPOS in by, "huios+anthrōpos must be detected across the intervening article"
    assert by[ANTHROPOS]["verses"] == 12
    assert by[ANTHROPOS]["missed"] is True
    assert by[ANTHROPOS]["flagged"] is True, "a TIGHT pair the draw missed must be flagged"
    assert by[ANTHROPOS]["lemma"] == "ἄνθρωπος"
    # legō is frequent-but-loose: also 0 in draw, but below the tightness bar → NOT flagged
    assert by[LEGO]["missed"] is True
    assert by[LEGO]["flagged"] is False, "a LOOSE frequent pair must not be flagged, even if missed"
    # article stop-listed; filler never sits by the target
    assert ARTICLE not in by
    assert FILLER not in by
    assert [f["neighbor"] for f in C.missed_collocations(findings)] == [ANTHROPOS]


def test_not_flagged_when_draw_represents_it():
    conn = _son_of_man_fixture(article=True)
    occs = _occs(conn, HUIOS)
    sample_vids = {1, 2}                           # draw DID include two son-of-man verses
    findings = C.scan_collocations(conn, HUIOS, occs, sample_vids, floor=10, window=2, pmi_min=4.0)
    by = {f["neighbor"]: f for f in findings}
    assert by[ANTHROPOS]["in_draw"] == 2
    assert by[ANTHROPOS]["missed"] is False
    assert by[ANTHROPOS]["flagged"] is False
    assert C.missed_collocations(findings) == []


def test_tightness_ranks_fixed_above_frequent():
    conn = _son_of_man_fixture(article=True)
    occs = _occs(conn, HUIOS)
    findings = C.scan_collocations(conn, HUIOS, occs, set(), floor=10, window=2)
    by = {f["neighbor"]: f for f in findings}
    # same co-occurrence count (12 each), but the fixed phrase must score far higher
    assert by[ANTHROPOS]["verses"] == by[LEGO]["verses"] == 12
    assert by[ANTHROPOS]["score"] > by[LEGO]["score"]
    assert by[ANTHROPOS]["score"] >= 4.0
    assert by[LEGO]["score"] < 1.0
    # findings come back sorted by score → the tight pair leads
    assert findings[0]["neighbor"] == ANTHROPOS


def test_floor_gates_low_count():
    conn = _son_of_man_fixture(article=True)
    occs = _occs(conn, HUIOS)
    findings = C.scan_collocations(conn, HUIOS, occs, set(), floor=13, window=2)
    # 12 son-of-man verses is below a floor of 13 → nothing reported
    assert findings == []


def test_window_boundary():
    """Two articles between huios and anthrōpos (ordinal distance 3) is outside a window of 2."""
    conn = _conn()
    for ch in range(1, 13):
        _add_verse(conn, ch, "Mat", ch, 1,
                   [(HUIOS, "son"), (ARTICLE, "the"), (ARTICLE, "the"), (ANTHROPOS, "man")])
    occs = _occs(conn, HUIOS)
    w2 = {f["neighbor"] for f in C.scan_collocations(conn, HUIOS, occs, set(), floor=10, window=2)}
    w3 = {f["neighbor"] for f in C.scan_collocations(conn, HUIOS, occs, set(), floor=10, window=3)}
    assert ANTHROPOS not in w2, "distance-3 neighbor must be outside window 2"
    assert ANTHROPOS in w3, "window 3 should reach it"


def test_stop_list_has_common_flooders():
    conn = _conn()
    stop = C.function_bare_strongs(conn)
    for n in ("3588", "2532", "1161", "1722", "846"):   # article, kai, de, en, autos
        assert n in stop


# ── PIECE B — coverage_audit ─────────────────────────────────────────────────────────────────
def test_contest_verse_parsing():
    vset, cset = C._parse_contest(["Rom 10:13", "Php 2:9-11", "Jas 2", "Psa 82:1"])
    assert ("Rom", 10, 13) in vset
    assert ("Php", 2, 9) in vset and ("Php", 2, 10) in vset and ("Php", 2, 11) in vset
    assert ("Psa", 82, 1) in vset
    assert ("Jas", 2) in cset          # chapter-level, no verse
    assert not any(bk == "Jas" for (bk, _c, _v) in vset)


def _spec(headline, refs):
    return {"headline": headline, "refs": refs}


def test_self_only_circular_vs_thin_verse_level():
    conn = _son_of_man_fixture()
    occs = _occs(conn, HUIOS)
    # sense 1 cites ONLY the disputed passage (Psa 82) → circular; sense 2 reaches outside → not
    specs = [
        _spec("gods are superhuman", [("Psa", 82, 1), ("Psa", 82, 6)]),
        _spec("with outside support", [("Psa", 82, 6), ("Deu", 32, 8)]),
    ]
    cov = C.coverage_audit(conn, HUIOS, occs, entry_refs=[], sense_specs=specs,
                           contest_verses=["Psa 82:1", "Psa 82:6", "Psa 82:7"], is_contested=True)
    by = {s["sense"]: s for s in cov["senses"]}
    assert by[1]["self_only"] is True, "all support inside the disputed passage → circular"
    assert by[2]["self_only"] is False, "one ref outside (Deu 32:8) → independent support, not circular"
    assert any(f == "sense 1 circular" for f in cov["flags"])


def test_self_only_chapter_level():
    conn = _son_of_man_fixture()
    occs = _occs(conn, HUIOS)
    specs = [
        _spec("faith-works, James only", [("Jas", 2, 24), ("Jas", 2, 26)]),   # all inside Jas 2
        _spec("reaches Romans", [("Jas", 2, 24), ("Rom", 4, 3)]),             # outside → not circular
    ]
    cov = C.coverage_audit(conn, HUIOS, occs, entry_refs=[], sense_specs=specs,
                           contest_verses=["Jas 2"], is_contested=True)
    by = {s["sense"]: s for s in cov["senses"]}
    assert by[1]["self_only"] is True
    assert by[2]["self_only"] is False


def test_self_only_inert_without_locus():
    conn = _son_of_man_fixture()
    occs = _occs(conn, HUIOS)
    specs = [_spec("some sense", [("Psa", 82, 1)])]
    # contested word but NO contest_verses → self_only never fires (thin still counts)
    cov = C.coverage_audit(conn, HUIOS, occs, entry_refs=[], sense_specs=specs,
                           contest_verses=[], is_contested=True)
    assert cov["senses"][0]["self_only"] is False
    assert cov["senses"][0]["support_refs"] == 1
    assert cov["thin_senses"], "a 1-ref sense is still thin even when self_only can't fire"


def test_collocation_cited_or_not():
    conn = _son_of_man_fixture()
    occs = _occs(conn, HUIOS)
    # entry that cites a son-of-man verse (vid 1) → anthrōpos collocation is 'cited'
    cov_cited = C.coverage_audit(conn, HUIOS, occs, entry_refs=[("Mat", 1, 1)],
                                 sense_specs=[], contest_verses=[], is_contested=False)
    anth = [c for c in cov_cited["collocations"] if c["neighbor"] == ANTHROPOS]
    assert anth and anth[0]["cited"] is True

    # entry that cites nothing → anthrōpos uncited → shows up in flags
    cov_bare = C.coverage_audit(conn, HUIOS, occs, entry_refs=[],
                                sense_specs=[], contest_verses=[], is_contested=False)
    anth2 = [c for c in cov_bare["collocations"] if c["neighbor"] == ANTHROPOS]
    assert anth2 and anth2[0]["cited"] is False
    assert any("uncited" in f for f in cov_bare["flags"])
