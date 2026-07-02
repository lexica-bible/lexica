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


HUIOS, ANTHROPOS, ARTICLE, THEOS = "G5207", "G444", "G3588", "G2316"


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
        SELECT v.book AS book, v.chapter AS ch, v.verse AS vs, w.verse_id AS vid, w.position AS pos
        FROM verses v JOIN words w ON w.verse_id = v.id
        WHERE w.strongs_base = ? ORDER BY v.id, w.position""", (sid,)).fetchall()
    return [dict(r) for r in rows]


def _son_of_man_fixture(article=True):
    """12 'son of man' verses + 3 'son of God' verses. huios is the target; anthrōpos/theos the
    content neighbors; the article sits between (function word, must be stop-listed)."""
    conn = _conn()
    vid = 1
    for ch in range(1, 13):                      # 12 son-of-man verses (vids 1..12)
        toks = [(HUIOS, "son")]
        if article:
            toks.append((ARTICLE, "the"))
        toks.append((ANTHROPOS, "man"))
        _add_verse(conn, vid, "Mat", ch, 1, toks)
        vid += 1
    for ch in range(1, 4):                        # 3 son-of-God verses (vids 13..15)
        _add_verse(conn, vid, "Joh", ch, 1, [(HUIOS, "son"), (ARTICLE, "the"), (THEOS, "God")])
        vid += 1
    return conn


def test_finds_collocation_across_article_and_flags_missed():
    conn = _son_of_man_fixture(article=True)
    occs = _occs(conn, HUIOS)
    # draw picked only the son-of-God verses — son-of-man is entirely absent
    sample_vids = {13, 14, 15}
    stop = C.function_bare_strongs(conn)          # no lsj table → override set (has the article)
    findings = C.scan_collocations(conn, HUIOS, occs, sample_vids, stop=stop, floor=10, window=2)

    by = {f["neighbor"]: f for f in findings}
    assert ANTHROPOS in by, "huios+anthrōpos must be detected across the intervening article"
    assert by[ANTHROPOS]["verses"] == 12
    assert by[ANTHROPOS]["in_draw"] == 0
    assert by[ANTHROPOS]["missed"] is True
    assert by[ANTHROPOS]["lemma"] == "ἄνθρωπος"
    # article is a function word → never a collocation; theos is under floor (3 < 10)
    assert ARTICLE not in by
    assert THEOS not in by
    assert [f["neighbor"] for f in C.missed_collocations(findings)] == [ANTHROPOS]


def test_not_missed_when_draw_represents_it():
    conn = _son_of_man_fixture(article=True)
    occs = _occs(conn, HUIOS)
    sample_vids = {1, 2, 13}                       # draw DID include two son-of-man verses
    findings = C.scan_collocations(conn, HUIOS, occs, sample_vids, floor=10, window=2)
    by = {f["neighbor"]: f for f in findings}
    assert by[ANTHROPOS]["in_draw"] == 2
    assert by[ANTHROPOS]["missed"] is False
    assert C.missed_collocations(findings) == []


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
