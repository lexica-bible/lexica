#!/usr/bin/env python3
"""
test_pn_surface_backfill.py — locks backfill_pn_surface.py (Phase-6 PN printed
Greek) BEFORE it ever touches PA. Fixture tables mirror the REAL builders'
CREATE TABLE shapes (words: build_words_from_abp via the vetted c3_dormant
mirror; abp_surface: build_abp_surface.py:299; bh_words: scrape_biblehub_abp.py:164
— the fixture-shape lesson from the R-2 receipt-2 defect).

Covers the four pairing rules + both refusal controls + the never-overwrite
guard + the closing arithmetic. Controls MUST fire: a zero-refusal run on the
seeded ambiguity would void the suite.
"""
import os
import sqlite3
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "backfill_pn_surface.py")

# Spawned script prints Greek; Windows pipes default to cp1252 — force UTF-8
# (same fix as test_retire_builder / test_c3_instruments, 2026-07-26).
_ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def _make_bible(path):
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT,
                             verse INT, text TEXT);
        CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, position INT,
                            english TEXT, english_head TEXT, strongs_base TEXT,
                            strongs TEXT, is_pn INT, italic INT DEFAULT 0,
                            italic_words TEXT, greek_pos TEXT, bracket_id INT,
                            morph TEXT, smcap_words TEXT, lemma TEXT);
        CREATE TABLE abp_surface (
          verse_id INTEGER, position INTEGER, form TEXT, translit TEXT,
          PRIMARY KEY (verse_id, position));

        -- v1 Mat 1:2 shape: TWO Isaacs (identical printed form) + one Judah.
        INSERT INTO verses VALUES (1,'Mat',1,2,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (1,3,'Isaac,','Isaac','G2464','G2464',1),
                 (1,4,'and Isaac','Isaac','G2464','G2464',1),
                 (1,13,'Judah','Judah','G2455','G2455',1),
                 (1,0,'begat','','G1080','G1080',0);          -- non-PN: must never gain a row

        -- v2: order-pairing (two same-token slots, DIFFERENT forms, counts equal).
        INSERT INTO verses VALUES (2,'Mat',1,16,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (2,1,'Jacob','Jacob','G2384','G2384',1),
                 (2,4,'of Jacob','Jacob','G2384','G2384',1);

        -- v3: ambiguity refusal control (2 scrape hits, differing forms, 1 slot).
        INSERT INTO verses VALUES (3,'Mat',2,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (3,2,'Herod','Herod','G2264','G2264',1);

        -- v4: edge-trim case — scrape form carries leading accent-mark dirt.
        INSERT INTO verses VALUES (4,'Mat',3,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (4,1,'Zorobabel','Zorobabel','*','*',1);

        -- v6: no-match refusal control (name absent from scrape).
        INSERT INTO verses VALUES (6,'Mat',5,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (6,1,'Melchizedek','Melchizedek','*','*',1);

        -- v7: cause-A recovery — David exists in scrape only as a NUMBERED row.
        INSERT INTO verses VALUES (7,'Mat',6,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (7,1,'David','David','G1138','*',1);

        -- v8: cause-C hyphen — our cell 'Tubalcain', scrape 'Tubal-cain' name row.
        INSERT INTO verses VALUES (8,'Mat',7,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (8,1,'Tubalcain','Tubalcain','*','*',1);

        -- v9: cause-B blank label — must refuse as blank-label, never pair.
        INSERT INTO verses VALUES (9,'Mat',8,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (9,1,NULL,NULL,'*','*',1);

        -- v10: name row WINS over numbered row for the same token (pool order).
        INSERT INTO verses VALUES (10,'Mat',9,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (10,1,'Moses','Moses','G3475','*',1);

        -- v11: compound numbered cell — slot must get the bare name word.
        INSERT INTO verses VALUES (11,'Mat',10,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (11,1,'and Judah','Judah','G2455','*',1);

        -- v12: two-capitals compound — must refuse (no guessing the name word).
        INSERT INTO verses VALUES (12,'Mat',11,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (12,1,'Jesus','Jesus','G2424','*',1);

        -- v13: fold class (cause B) — LABEL-LESS name slot pairs with the
        -- verse's star-compound row ('Cain fretted' = 3076-3588-*), in order.
        INSERT INTO verses VALUES (13,'Mat',12,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (13,2,NULL,NULL,'*','*',1);

        -- v14: fold count-mismatch control — TWO blank slots, ONE star row:
        -- both must refuse (order-pairing needs equal counts).
        INSERT INTO verses VALUES (14,'Mat',13,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (14,1,NULL,NULL,'*','*',1),
                 (14,4,NULL,NULL,'*','*',1);

        -- v15: dual-role star row — its token matches a LABELED slot, so the
        -- labeled slot wins it via the token phase and the blank slot refuses
        -- (the 286-slot regression control, 2026-07-28 dry-run catch).
        INSERT INTO verses VALUES (15,'Mat',14,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (15,1,'and Judah','Judah','G2455','*',1),
                 (15,5,NULL,NULL,'*','*',1);

        -- BRIDGE RULE CONTROLS (2026-08-13, reviewer-signed; charter
        -- CHARTER_form_table_rebuild.md). The 8/8 wordpos lane filled blank
        -- labels, moving ~172 slots off the blank-label path; a LABELED slot may
        -- now take a glued star cell's name word only when a same-book standalone
        -- cell attests form -> label.
        -- v15 POSITIVE (1Ki 7:48 shape): labeled 'Solomon', glued 'made=Σολομών',
        --     standalone Σολομών/Solomon elsewhere in the book -> ADD.
        INSERT INTO verses VALUES (16,'Mat',15,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (16,3,'Solomon','Solomon','*','*',1);
        -- v16 NEGATIVE (Gen 4:8 shape): TWO 'Cain' slots, two glued cells -> the
        --     rule must not order-guess: bridge-ambiguous, NO rows.
        INSERT INTO verses VALUES (17,'Mat',16,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (17,2,'Cain','Cain','*','*',1),
                 (17,22,'Cain','Cain','*','*',1);
        -- v17 BRIDGE-NEGATIVE: labeled 'Abel', glued cell carries Καϊν (a real
        --     name, attested in-book, but NOT this slot's label) -> bridge-fail.
        --     Same-verse presence must never stand in for agreement.
        INSERT INTO verses VALUES (18,'Mat',17,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (18,5,'Abel','Abel','*','*',1);
        -- v18 ONE-CLAIM: a LABEL-LESS slot and a labeled 'Seth' slot share one
        --     glued 'said=Αδάμ' cell. Αδάμ bridges to 'adam', not 'seth', so the
        --     bridge declines; the blank path then takes the row ONCE. Seth refuses
        --     (bridge-fail). The two paths never both claim a slot or a row.
        INSERT INTO verses VALUES (19,'Mat',18,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (19,4,'','','*','*',1),
                 (19,9,'Seth','Seth','*','*',1);

        -- v5: never-overwrite guard (surface row already present for the slot).
        INSERT INTO verses VALUES (5,'Mat',4,1,'...');
        INSERT INTO words (verse_id,position,english,english_head,strongs_base,strongs,is_pn)
          VALUES (5,1,'David','David','G1138','G1138',1);
        INSERT INTO abp_surface VALUES (5,1,'PRE-EXISTING','');
    """)
    c.commit()
    c.close()


def _make_scrape(path):
    c = sqlite3.connect(path)
    c.executescript("""
        CREATE TABLE bh_words (
            id INTEGER PRIMARY KEY, book TEXT NOT NULL, chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL, position INTEGER NOT NULL, strongs TEXT,
            greek TEXT, english TEXT, italic_words TEXT NOT NULL DEFAULT '',
            smcap_words TEXT NOT NULL DEFAULT '', greek_pos INTEGER);
        -- Mat 1:2 — two Isaac name rows, SAME form; one Judah; a numbered row
        -- that must be ignored (name pairing reads blank-Strong's rows only).
        INSERT INTO bh_words (book,chapter,verse,position,strongs,greek,english) VALUES
          ('matthew',1,2,1,NULL,'Ισαακ','Isaac'),
          ('matthew',1,2,3,NULL,'Ισαακ','and Isaac'),
          ('matthew',1,2,7,NULL,'Ιουδαν','Judah'),
          ('matthew',1,2,0,'1080','εγεννησε','begat'),
          -- Mat 1:16 — two Jacob rows, DIFFERENT forms (nominative then genitive):
          ('matthew',1,16,0,NULL,'Ιακωβ','Jacob'),
          ('matthew',1,16,2,NULL,'Ιακωβου','of Jacob'),
          -- Mat 2:1 — two Herod rows, DIFFERENT forms, but only ONE slot: refuse.
          ('matthew',2,1,1,NULL,'Ηρωδου','Herod'),
          ('matthew',2,1,5,NULL,'Ηρωδης','Herod'),
          -- Mat 4:1 — David row for the never-overwrite slot; leading scrape
          -- dirt (standalone accent + space, the live '΄ Αχαζ' case) must be
          -- edge-trimmed even though this slot ends up an 'already' skip.
          ('matthew',4,1,1,NULL,'Δαυιδ','David'),
          -- Mat 3:1 — dirt-trim assertion target: Zorobabel gets a dirty form
          -- (was the no-match control; that control moved to Mat 5:1).
          ('matthew',3,1,1,NULL,'΄ Ζοροβαβελ ','Zorobabel'),
          -- Mat 6:1 — David as a NUMBERED row only (cause-A recovery) + a
          -- numbered common word that must never enter the name pools.
          ('matthew',6,1,1,'1138','Δαβίδ','David'),
          ('matthew',6,1,2,'1080','εγεννησε','begat'),
          -- Mat 7:1 — hyphen variant name row.
          ('matthew',7,1,1,NULL,'Θοβέλ','Tubal-cain'),
          -- Mat 8:1 — a perfectly good scrape row; the blank-label slot must
          -- still refuse (control: blank never pairs even when a row exists).
          ('matthew',8,1,1,NULL,'Καϊν','Cain'),
          -- Mat 9:1 — BOTH a name row and a numbered row for Moses with
          -- different forms; the name row must win.
          ('matthew',9,1,1,NULL,'Μωυσής','Moses'),
          ('matthew',9,1,2,'3475','Μωυσέως','Moses'),
          -- Mat 10:1 — compound numbered cell: only the capitalized name word
          -- is stored, never the connector (the 'Ιούδας δε' live catch).
          ('matthew',10,1,1,'2455','Ιούδας δε','And Judah'),
          -- Mat 11:1 — compound with TWO capitalized words: skipped, refuses.
          ('matthew',11,1,1,'2424','Ιησούς Χριστός','Jesus Christ'),
          -- Mat 12:1 — star-compound row (the fold class): '*' in the tag,
          -- one capitalized word to extract.
          ('matthew',12,1,1,'3076-3588-*','ελύπησε τον Καϊν','Cain fretted'),
          -- Mat 13:1 — ONE star row for a two-blank-slot verse: count mismatch.
          ('matthew',13,1,1,'2036-*','είπεν Αδάμ','Adam said'),
          -- Mat 14:1 — dual-role star row: token 'judah' matches the labeled slot.
          ('matthew',14,1,1,'*-1161','Ιούδας δε','And Judah'),
          -- BRIDGE controls: glued star cells whose English is the VERB.
          ('matthew',15,1,1,'4160-*','εποίησε Σολομών','Solomon made'),
          ('matthew',16,1,1,'2036-*','είπε Καϊν','Cain said'),
          ('matthew',16,1,2,'305-*','ανέβη Καϊν','Cain rose up'),
          ('matthew',17,1,1,'615-*','απέκτεινε Καϊν','Cain killed'),
          ('matthew',18,1,1,'2036-*','είπεν Αδάμ','Adam said'),
          -- same-book STANDALONE attestations the bridge reads (Mat 8:1 already
          -- attests Καϊν/Cain); verses 20-21 have no words rows on purpose.
          ('matthew',20,1,1,NULL,'Σολομών','Solomon'),
          ('matthew',21,1,1,NULL,'Αδάμ','Adam');
    """)
    c.commit()
    c.close()


def _run(dbp, bhp, *extra):
    return subprocess.run(
        [sys.executable, SCRIPT, dbp, "--bh", bhp, *extra],
        capture_output=True, text=True, encoding="utf-8", cwd=ROOT, env=_ENV)


def main() -> int:
    fails = []

    def check(desc, got, want):
        if got != want:
            fails.append(f"  FAIL: {desc}\n        got {got!r}, want {want!r}")
        else:
            print(f"  ok: {desc}")

    tmp = tempfile.mkdtemp()
    dbp = os.path.join(tmp, "bible.db")
    bhp = os.path.join(tmp, "bh.db")
    _make_bible(dbp)
    _make_scrape(bhp)

    # dry-run writes nothing
    r = _run(dbp, bhp)
    check("dry-run exit 0", r.returncode, 0)
    check("dry-run announces itself", "DRY RUN" in r.stdout, True)
    c = sqlite3.connect(dbp)
    check("dry-run wrote nothing",
          c.execute("SELECT count(*) FROM abp_surface").fetchone()[0], 1)
    c.close()
    # 26 PN slots total: 14 new + 11 refused + 1 already (bridge controls added 6 slots, 2026-08-13) (v5 pairs but its slot
    # is already present -> counted 'already', not new). Arithmetic must close.
    check("arithmetic line closes on the slot total",
          "= 26 (must equal 26)" in r.stdout.replace(",", ""), True)
    # blank-label = 4: the no-star control (v9) + both count-mismatch slots
    # (v14) + the dual-role verse's blank (v15, its star row consumed by token).
    check("blank-label controls FIRE (no-star + count-mismatch + consumed)",
          "blank-label: 4" in r.stdout, True)
    # extracted = 9: the Judah compound + three star rows + five bridge-control glued cells.
    check("compound extraction + skip both counted",
          "compound name-word extracted 9" in r.stdout
          and "compound skipped 1" in r.stdout, True)
    check("blank-label control FIRES", "blank-label" in r.stdout, True)
    check("edge-trim counter reports the dirty form",
          "edge-trimmed 1" in r.stdout, True)
    check("ambiguity control FIRES", "ambiguous : 1" in r.stdout.replace("  ", " "), True)
    # no-match = 2: the Melchizedek control + the two-capitals compound (its
    # skipped row leaves the Jesus slot with nothing to match).
    check("no-match control FIRES", "no-match : 2" in r.stdout.replace("  ", " "), True)
    flat = r.stdout.replace("  ", " ")
    check("bridge: positive counted as an add", "bridge adds (glued cell, same-book attested): 1" in r.stdout, True)
    check("bridge-ambiguous control FIRES (two Cains)", "bridge-ambiguous: 2" in r.stdout, True)
    check("bridge-fail control FIRES (Abel/Kain + Seth/Adam)", "bridge-fail: 2" in r.stdout, True)

    # apply
    r = _run(dbp, bhp, "--apply")
    check("apply exit 0", r.returncode, 0)
    c = sqlite3.connect(dbp)
    rows = dict(((vid, pos), form) for vid, pos, form, _t in
                c.execute("SELECT * FROM abp_surface"))
    check("both Isaacs got the (identical) form",
          (rows.get((1, 3)), rows.get((1, 4))), ("Ισαακ", "Ισαακ"))
    check("Judah paired", rows.get((1, 13)), "Ιουδαν")
    check("order-pairing: k-th slot to k-th printed form",
          (rows.get((2, 1)), rows.get((2, 4))), ("Ιακωβ", "Ιακωβου"))
    check("ambiguous slot got NO row", (3, 2) in rows, False)
    check("dirty form stored TRIMMED", rows.get((4, 1)), "Ζοροβαβελ")
    check("no-match slot got NO row", (6, 1) in rows, False)
    check("existing row NOT overwritten", rows.get((5, 1)), "PRE-EXISTING")
    check("non-PN slot untouched", (1, 0) in rows, False)
    check("cause-A: numbered-row David recovered", rows.get((7, 1)), "Δαβίδ")
    check("cause-C: hyphen-blind Tubalcain paired", rows.get((8, 1)), "Θοβέλ")
    check("cause-B: blank-label slot got NO row", (9, 1) in rows, False)
    check("name row WINS over numbered row", rows.get((10, 1)), "Μωυσής")
    check("compound cell stores the bare name word", rows.get((11, 1)), "Ιούδας")
    check("two-capitals compound refused, NO row", (12, 1) in rows, False)
    check("fold class: blank slot gets the star row's name word",
          rows.get((13, 2)), "Καϊν")
    check("fold count-mismatch: both blank slots refused, NO rows",
          ((14, 1) in rows, (14, 4) in rows), (False, False))
    check("dual-role star row: LABELED slot wins it via token match",
          rows.get((15, 1)), "Ιούδας")
    check("dual-role verse: blank slot refused, star row consumed",
          (15, 5) in rows, False)
    check("BRIDGE positive: Solomon took the glued cell's name word",
          rows.get((16, 3)), "Σολομών")
    check("BRIDGE negative: neither Cain slot got a row", (17, 2) in rows or (17, 22) in rows, False)
    check("BRIDGE bridge-negative: Abel did NOT take Kain", (18, 5) in rows, False)
    check("ONE-CLAIM: blank slot took the star row via the blank path", rows.get((19, 4)), "Αδάμ")
    check("ONE-CLAIM: Seth refused, row not claimed twice", (19, 9) in rows, False)
    check("total rows = 1 pre-existing + 14 new", len(rows), 15)
    c.close()

    if fails:
        print("\n".join(fails))
        return 1
    print("\nAll PN-surface backfill checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
