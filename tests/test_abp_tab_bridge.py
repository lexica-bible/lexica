#!/usr/bin/env python3
"""Locked test — ABP-tab routing bridge (docs/tickets/CHARTER_abp_tab_routing.md,
reviewer-ruled 2026-09-06). Drives the production helpers on a real-shape fixture:

  * POSITIVE FIRST (audit-tools-must-fail): a Galilee-shaped number (starred rows, one
    'surface' header, one lexicon owner) BRIDGES, and its All-books list == the PN:
    page's own rows (PARITY, position carried).
  * lemma-only residual (Zion/Aram shape: surface + 1 lemma-only) -> REFUSED
  * lemma-only only (Israel/Jerusalem shape) -> REFUSED
  * two stored values folding to one key -> REFUSED
  * collision (two lexicon numbers own one folded key) -> REFUSED, both sides
  * MIXED (number has a words row AND a same-header surface row) -> bridge never
    consulted (tab opens today, count untouched)
  * a dotted key never bridges; tables absent -> None (deploy-safe)

Pure stdlib + in-memory SQLite. Run:  python tests/test_abp_tab_bridge.py
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _fixture():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript("""
        CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT);
        CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT,
                            strongs TEXT, strongs_base TEXT, english TEXT);
        CREATE TABLE lexicon (strongs TEXT PRIMARY KEY, lemma TEXT, lemma_plain TEXT);
        CREATE TABLE pn_greek_identity (
            verse_id INT, position INT, greek_strongs TEXT, greek_lemma TEXT,
            source TEXT, hebrew_base TEXT, PRIMARY KEY (verse_id, position));
        INSERT INTO verses VALUES (1,'Mat',4,15),(2,'Mat',4,23),(3,'Jos',20,7),(4,'Luk',3,23),(5,'Mar',15,34);
        INSERT INTO lexicon VALUES
            ('1056','Γαλιλαία','γαλιλαια'),      -- bridges
            ('4622','Σιών','σιων'),              -- surface + residual -> refused
            ('2474','Ἰσραήλ','ισραηλ'),          -- lemma-only only -> refused
            ('4540','Σαμάρεια','σαμαρεια'),      -- two stored values -> refused
            ('2241','ἠλί','ηλι'), ('2242','Ἡλί','ηλι'),   -- collision -> refused
            ('1802','Ἐνώχ','ενωχ');              -- MIXED: has a words row
        INSERT INTO words VALUES (1, 4, 3, '1802', 'G1802', 'Enoch');
        INSERT INTO pn_greek_identity VALUES
            (3, 2, NULL, 'Γαλιλαία', 'surface', NULL),
            (1, 5, NULL, 'Γαλιλαία', 'surface', NULL),
            (2, 4, NULL, 'Γαλιλαία', 'surface', NULL),
            (1, 7, NULL, 'Σιών', 'surface', NULL),
            (2, 7, NULL, 'Σιών', 'lemma-only', NULL),
            (1, 8, NULL, 'Ισραήλ', 'lemma-only', NULL),
            (1, 9, NULL, 'Σαμάρεια', 'surface', NULL),
            (2, 9, NULL, 'Σαμαρεία', 'surface', NULL),
            (5, 2, NULL, 'Ηλί', 'surface', NULL),
            (4, 9, NULL, 'Ενώχ', 'surface', NULL);
    """)
    return c


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    from views_lexicon import (_header_bridge, _bridge_if_grey, _pn_lemma_rows, _all_books_verses,
                               _bridge_line)

    c = _fixture()
    fails = []

    def check(desc, got, want):
        if got != want:
            fails.append(f"  FAIL: {desc}\n        got {got!r}, want {want!r}")
        else:
            print(f"  ok: {desc}")

    # positive first
    check("POSITIVE: Galilee-shaped number bridges to its stored header",
          _header_bridge(c, "1056"), "Γαλιλαία")
    check("bridge consulted only when the tab is grey (G1056 has no words row)",
          _bridge_if_grey(c, "1056", "1056", "G1056", False), "Γαλιλαία")
    rows, trunc = _all_books_verses(c, "abp", "1056", "1056", "G1056", False, False, "", "all",
                                    6000, abp_header="Γαλιλαία")
    pn = _pn_lemma_rows(c, "Γαλιλαία")
    check("PARITY: bridged All-books list == PN: page rows (count)", len(rows), len(pn))
    check("PARITY: same keys, canonical order, slot carried",
          [(r["book"], r["chapter"], r["verse"], r["position"]) for r in rows],
          [(r["book"], r["chapter"], r["verse"], r["position"]) for r in pn])
    check("canonical order: Jos before Mat", [r["book"] for r in rows], ["Jos", "Mat", "Mat"])
    check("testament narrows the bridged list",
          len(_all_books_verses(c, "abp", "1056", "1056", "G1056", False, False, "", "nt",
                                6000, abp_header="Γαλιλαία")[0]), 2)
    check("a rendering filter matches nothing on starred rows",
          _all_books_verses(c, "abp", "1056", "1056", "G1056", False, False, "galilee", "all",
                            6000, abp_header="Γαλιλαία"), ([], False))

    # results card (reviewer ruling 9/6): same header + same count as the study page
    check("CARD: bridged number's ABP line = (header, study-page count)",
          _bridge_line(c, "G1056"), ("Γαλιλαία", len(pn)))
    check("CARD: refused number gets no line", _bridge_line(c, "G4622"), None)
    check("CARD: MIXED number gets no line (its own rows count)", _bridge_line(c, "G1802"), None)
    check("CARD: Hebrew / dotted keys never", (_bridge_line(c, "H1056"), _bridge_line(c, "G1056.2")), (None, None))

    # refusals
    check("REFUSED: surface + lemma-only residual (Zion/Aram shape)", _header_bridge(c, "4622"), None)
    check("REFUSED: lemma-only only (Israel/Jerusalem shape)", _header_bridge(c, "2474"), None)
    check("REFUSED: two stored values fold to one key", _header_bridge(c, "4540"), None)
    check("REFUSED: collision, first owner", _header_bridge(c, "2241"), None)
    check("REFUSED: collision, second owner", _header_bridge(c, "2242"), None)
    check("MIXED: tab opens today -> bridge never consulted",
          _bridge_if_grey(c, "1802", "1802", "G1802", False), None)
    check("dotted key never bridges", _bridge_if_grey(c, "1056.2", "1056", "G1056", False), None)
    check("Hebrew number never bridges", _bridge_if_grey(c, "1056", "1056", "H1056", True), None)
    check("unknown number -> None", _header_bridge(c, "9999"), None)

    # the collision refusal must not depend on lemma_plain being built
    c.execute("ALTER TABLE lexicon RENAME COLUMN lemma_plain TO lp_gone")
    import views_lexicon as vl
    vl._LEMMA_PLAIN_OK.clear()
    check("collision refused with lemma_plain absent (Python fold)", _header_bridge(c, "2241"), None)
    check("positive still bridges with lemma_plain absent", _header_bridge(c, "1056"), "Γαλιλαία")

    bare = sqlite3.connect(":memory:")
    bare.row_factory = sqlite3.Row
    check("tables absent -> None (deploy-safe)", _header_bridge(bare, "1056"), None)

    if fails:
        print("\n".join(fails))
        return 1
    print("\nAll ABP-tab bridge checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
