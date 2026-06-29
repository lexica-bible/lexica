#!/usr/bin/env python3
"""Regression test for the Ask-corpus lexical-texture panel (corpus_panel.build_groups).

Locks the BEHAVIOR the panel was proven on (scripts/proto_*.py, 2026-06-29) so a future
edit can't silently regress the honesty boundary — the whole point of the panel is that it
NEVER manufactures structure. Encoded as a miniature corpus:

  * fire (Greek)      — multi-word family: pyr + pyroo/pyrosis INCLUDE (gloss confirms),
                        pyretos "fever" SET ASIDE (spelling matches, meaning doesn't).
  * sabbath (Hebrew)  — flat family: shabbat + rest-words INCLUDE, mishbath "cessation"
                        SET ASIDE. One family, not invented texture.
  * esh (short root)  — a ≤2-consonant Hebrew root (אש) must NOT flood with "which" /
                        "woman" / "food offering"; it gloss-anchors and stays a lone word.
  * degradation       — no heads, a head that doesn't occur, a head absent from the
                        lexicon, and heb.db missing all resolve to "show less" (no group),
                        never a crash or a fabricated row.
  * bars scale within a language — group["max"] is the in-group max (the frontend divides
                        by it), so Hebrew never shares a scale with Greek.
  * dedupe            — a head already inside an earlier group's family isn't repeated.

Pure stdlib + in-memory SQLite — no bible.db, no heb.db, no model. Run:
    python tests/test_corpus_panel.py
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import corpus_panel


def _fixture() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript("""
        CREATE TABLE lexicon (strongs TEXT, strongs_g TEXT, translit TEXT, lemma TEXT,
                              strongs_def TEXT, kjv_def TEXT, derivation TEXT);
        CREATE TABLE bdb (strongs_id TEXT, lemma TEXT, xlit TEXT, description TEXT);
        CREATE TABLE words (id INTEGER PRIMARY KEY, strongs_base TEXT);
        CREATE TABLE heb_words (id INTEGER PRIMARY KEY, strongs TEXT);
        CREATE TABLE word_gloss (strongs TEXT, gloss TEXT);

        -- Greek 'fire' family (translit prefix 'pyr' proposes; gloss disposes).
        INSERT INTO lexicon (strongs, translit, lemma) VALUES
            ('4442','pyr','πῦρ'),
            ('4448','pyroo','πυρόω'),
            ('4451','pyrosis','πύρωσις'),
            ('4445','pyretos','πυρετός'),   -- 'fever' — false friend (stem matches, sense doesn't)
            ('5555','phantom','φάντασμα');  -- in the lexicon but never occurs (drop test)
        UPDATE lexicon SET strongs_g = 'G' || strongs;

        -- Hebrew families. 'sabbath' root שבת (3 consonants → proposes by containment);
        -- 'esh' root אש (2 consonants → SHORT → gloss-anchored).
        INSERT INTO bdb (strongs_id, lemma, xlit, description) VALUES
            ('H7676','שבת','shabbat',''),
            ('H7677','שבתון','shabbathon',''),
            ('H7673','שבת','shabath',''),
            ('H4868','משבת','mishbath',''),   -- 'cessation' — false friend
            ('H784','אש','esh',''),
            ('H801','אשה','ishsheh',''),       -- 'food offering' — shares אש, not fire
            ('H802','אשה','ishshah',''),       -- 'woman' — shares אש
            ('H834','אשר','asher','');         -- 'which' — shares אש (the flood the short rule blocks)

        INSERT INTO word_gloss (strongs, gloss) VALUES
            ('G4442','fire'),
            ('G4448','to burn; refine by fire'),
            ('G4451','a burning by fire'),
            ('G4445','fever'),
            ('G5555','an apparition'),
            ('H7676','sabbath; rest'),
            ('H7677','sabbath rest'),
            ('H7673','to cease, to rest'),
            ('H4868','cessation'),
            ('H784','fire'),
            ('H801','food offering'),
            ('H802','woman, wife'),
            ('H834','which');

        INSERT INTO words (strongs_base) VALUES
            ('G4442'),('G4442'),('G4448'),('G4451'),('G4445');  -- counts set below by repetition
    """)
    # Occurrence counts: pyr 70, pyroo 12, pyrosis 3, pyretos 6 (Greek);
    # shabbat 100, shabbathon 11, shabath 70, mishbath 3, esh 300, others large (Hebrew).
    c.execute("DELETE FROM words")
    for base, n in [("G4442", 70), ("G4448", 12), ("G4451", 3), ("G4445", 6)]:
        c.executemany("INSERT INTO words (strongs_base) VALUES (?)", [(base,)] * n)
    for sid, n in [("H7676", 100), ("H7677", 11), ("H7673", 70), ("H4868", 3),
                   ("H784", 300), ("H801", 60), ("H802", 700), ("H834", 5000)]:
        c.executemany("INSERT INTO heb_words (strongs) VALUES (?)", [(sid,)] * n)
    return c


def _strongs(group):
    return [r["strongs"] for r in group["family"]]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")   # Greek/Hebrew in output
    except Exception:
        pass
    c = _fixture()
    fails = []

    def check(desc, got, want):
        if got != want:
            fails.append(f"  FAIL: {desc}\n        got {got!r}, want {want!r}")
        else:
            print(f"  ok: {desc}")

    # ── fire (Greek): multi-word family, false friend set aside ──────────────
    g = corpus_panel.build_groups(c, c, ["G4442"])
    check("fire: one group", len(g), 1)
    if g:
        fam = g[0]
        check("fire: lang G", fam["lang"], "G")
        check("fire: family = pyr,pyroo,pyrosis (core first, then occ-desc)",
              _strongs(fam), ["G4442", "G4448", "G4451"])
        check("fire: core flagged", fam["family"][0]["core"], True)
        check("fire: head range from word_gloss", fam["family"][0]["gloss"], "fire")
        check("fire: pyretos 'fever' NOT in the family", "G4445" in _strongs(fam), False)
        check("fire: 1 form set aside (pyretos)", fam["set_aside"], 1)
        check("fire: bar scale (max) = 70, the in-group max", fam["max"], 70)

    # ── sabbath (Hebrew): flat family, 'cessation' set aside ─────────────────
    g = corpus_panel.build_groups(c, c, ["H7676"])
    check("sabbath: one group", len(g), 1)
    if g:
        fam = g[0]
        check("sabbath: lang H", fam["lang"], "H")
        check("sabbath: family = shabbat,shabath,shabbathon",
              _strongs(fam), ["H7676", "H7673", "H7677"])
        check("sabbath: mishbath 'cessation' NOT shown", "H4868" in _strongs(fam), False)
        check("sabbath: 1 form set aside (mishbath)", fam["set_aside"], 1)

    # ── esh: SHORT root must not flood with which/woman/offering ─────────────
    g = corpus_panel.build_groups(c, c, ["H784"])
    check("esh: one group", len(g), 1)
    if g:
        fam = g[0]
        check("esh: lone word (no spurious family from a 2-consonant root)",
              _strongs(fam), ["H784"])
        check("esh: nothing set aside (short root gloss-anchors, doesn't dump)",
              fam["set_aside"], 0)
        for junk in ("H834", "H801", "H802"):
            check(f"esh: {junk} not pulled in", junk in _strongs(fam), False)

    # ── dedupe: a head already inside an earlier family isn't repeated ───────
    g = corpus_panel.build_groups(c, c, ["G4442", "G4448"])
    check("dedupe: pyroo (already in pyr's family) makes no 2nd group", len(g), 1)

    # ── degradation: every bad input resolves to 'no group', never a crash ───
    check("no heads -> no groups", corpus_panel.build_groups(c, c, []), [])
    check("head absent from lexicon -> dropped", corpus_panel.build_groups(c, c, ["G9999"]), [])
    check("head that never occurs -> dropped", corpus_panel.build_groups(c, c, ["G5555"]), [])
    check("heb.db missing -> Hebrew head dropped (no honest count)",
          corpus_panel.build_groups(c, None, ["H7676"]), [])
    check("garbage head -> ignored", corpus_panel.build_groups(c, c, ["banana"]), [])

    if fails:
        print("\n".join(fails))
        print(f"\n{len(fails)} FAILED")
        return 1
    print("\nAll corpus-panel behavior holds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
