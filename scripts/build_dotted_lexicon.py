#!/usr/bin/env python3
"""build_dotted_lexicon.py — corrected headword lemma + romanization for the ABP
dotted Strong's numbers that are a genuinely different word from their base.

Background: scripts/audit_dotted_lemmas.py shows ~3049 dotted numbers (e.g. 180.2
ἀκατασκεύαστος) whose card headword wrongly resolves to the BASE number's word
(G180 ἀκατάπαυστος) because strongs_base drops the ".N". The correct word is the
headword of the number's OWN abp_ext dictionary entry. This builds a side table,
`dotted_lexicon`, keyed by the full dotted number, so the card can later show the
right word. It touches NOTHING else: not words, not lexicon, and it skips the
[ABP] form-notes (1510.x = forms of εἰμί, where the base lemma is already right).

  python3 scripts/build_dotted_lexicon.py            # DRY RUN: print proposed rows, write nothing
  python3 scripts/build_dotted_lexicon.py --apply    # create + fill dotted_lexicon (that table only)

Reuses the verified Greek extraction from audit_dotted_lemmas.py and the romanizer
from build_abp_translit.py. Reads abp_ext/lexicon/words; writes ONLY dotted_lexicon.
"""
import os
import re
import sqlite3
import sys
import unicodedata

from audit_dotted_lemmas import bare, clean_text, first_greek
from build_abp_translit import romanize

DB = os.path.expanduser("~/bible-db/bible.db")

# ABP spells some numbers as Greek numeral LETTERS, parked at a dotted Strong's whose
# base is an unrelated word (so the auto-derivation below skips/misreads them). Pin the
# correct numeral letter here so the chip's Greek line shows χ/ξ/ϛ, not φωτισμός/νῶτος/ἕως.
# (e.g. 666 in Rev 13:18 = χ ξ ϛ.) lemma = the letter, translit = its name.
NUMERAL_OVERRIDES = {
    "5462.1": ("χ", "chi"),      # 600
    "3577.2": ("ξ", "xi"),       # 60
    "2193.2": ("ϛ", "stigma"),   # 6
}

# LSJ headwords carry vowel-length marks (breve/macron, e.g. τραυμᾰτίας); strip them
# so the stored lemma reads clean like the rest of the dictionary (τραυματίας). These
# are the only Greek uses of combining breve (0x306) / macron (0x304); real accents
# (tonos/perispomeni/breathing) are untouched.
def strip_length_marks(s: str) -> str:
    d = unicodedata.normalize("NFD", s or "")
    d = "".join(c for c in d if c not in (chr(0x306), chr(0x304)))
    return unicodedata.normalize("NFC", d)


def collect(conn):
    rows = conn.execute(
        "SELECT strongs AS num, COUNT(*) AS uses FROM words "
        "WHERE strongs LIKE '%.%' GROUP BY strongs"
    ).fetchall()
    fixes = []
    abp_fixes = []                               # [ABP] different-words newly promoted (for --summary)
    skipped = {"form_note": 0, "no_entry": 0, "unreadable": 0, "already_ok": 0}
    for r in rows:
        num = r["num"]
        base = "G" + num.split(".")[0]
        shown = conn.execute(
            "SELECT lemma FROM lexicon WHERE strongs_g = ?", (base,)
        ).fetchone()
        shown_lemma = shown["lemma"] if shown else ""
        ext = conn.execute(
            "SELECT def_html FROM abp_ext WHERE trim(strongs)=? OR trim(strongs)=?",
            (num, "G" + num),
        ).fetchone()
        if not ext:
            skipped["no_entry"] += 1
            continue
        # Skip ONLY genuine ABP form-notes — the εἰμί family ("[ABP] εστίν, ... Strong
        # G2076"), which point to the real Strong's number, so the BASE lemma is the right
        # card headword. The marker is the literal "Strong G####" pointer. A "[ABP]" entry
        # that is a DIFFERENT word (G4521.2 σαβέκ "thicket" vs base G4521 σάββατον) carries
        # no such pointer (at most a "See G####" cross-ref) — it must flow through and get
        # its own row. (The old blanket "[ABP]" skip hid ~hundreds of real different-words —
        # σαβέκ, γόμορ, ιωβήλ, γαυριόω ... 2026-06-21.)
        txt = clean_text(ext["def_html"])
        if re.search(r"Strong\s+G\d", txt):
            skipped["form_note"] += 1
            continue
        correct = first_greek(ext["def_html"])
        if not correct:
            skipped["unreadable"] += 1
            continue
        if bare(correct) == bare(shown_lemma):
            skipped["already_ok"] += 1           # LSJ entry that already matches the base
            continue
        correct = strip_length_marks(correct)
        row_fix = (num, shown_lemma, correct, romanize(correct, correct), r["uses"])
        fixes.append(row_fix)
        if txt.lstrip().startswith("[ABP]"):     # a "[ABP]" word that's NOT a form-note
            abp_fixes.append(row_fix)
    # Pin the Greek-numeral letters (override any auto-derived row for the same number).
    fixes = [f for f in fixes if f[0] not in NUMERAL_OVERRIDES]
    for num, (letter, tr) in NUMERAL_OVERRIDES.items():
        base = conn.execute(
            "SELECT lemma FROM lexicon WHERE strongs_g = ?", ("G" + num.split(".")[0],)
        ).fetchone()
        uses = conn.execute(
            "SELECT COUNT(*) FROM words WHERE strongs = ?", (num,)
        ).fetchone()[0]
        fixes.append((num, base["lemma"] if base else "", letter, tr, uses))
    fixes.sort(key=lambda t: -t[4])
    abp_fixes.sort(key=lambda t: -t[4])
    return fixes, skipped, abp_fixes


def main():
    do_apply = "--apply" in sys.argv
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    fixes, skipped, abp_fixes = collect(conn)

    if not do_apply:
        if "--summary" in sys.argv:
            print(f"[dry-run] {len(fixes)} corrections proposed; "
                  f"{len(abp_fixes)} of them [ABP] different-words newly promoted; "
                  f"skipped {skipped}.")
            print("\nSample of the newly-promoted [ABP] words (most-used first):")
            print("dotted | shown now (base) | corrected lemma | romanization | uses")
            for num, shown, correct, tr, uses in abp_fixes[:25]:
                print(f"{num} | {shown} | {correct} | {tr} | {uses}")
            print("\n(Add --apply to write the table; drop --summary for the full list.)")
            conn.close()
            return
        print("dotted | shown now (base) | corrected lemma | romanization | uses")
        for num, shown, correct, tr, uses in fixes:
            print(f"{num} | {shown} | {correct} | {tr} | {uses}")
        print(f"\n[dry-run] {len(fixes)} corrections proposed "
              f"({len(abp_fixes)} of them [ABP] different-words); skipped {skipped}.")
        print("Nothing written. Re-run with --apply to fill the dotted_lexicon table.")
        conn.close()
        return

    conn.execute("DROP TABLE IF EXISTS dotted_lexicon")
    conn.execute(
        "CREATE TABLE dotted_lexicon (strongs TEXT PRIMARY KEY, lemma TEXT, translit TEXT)"
    )
    conn.executemany(
        "INSERT OR REPLACE INTO dotted_lexicon(strongs, lemma, translit) VALUES (?,?,?)",
        [("G" + num, correct, tr) for num, _shown, correct, tr, _uses in fixes],
    )
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM dotted_lexicon").fetchone()[0]
    conn.close()
    print(f"Filled dotted_lexicon with {n} corrected headwords (that table only; "
          f"nothing else touched).")


if __name__ == "__main__":
    main()
