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

from audit_dotted_lemmas import clean_text, first_greek
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

# A frozen multi-word idiom ABP parks at a dotted number reads as ONE chip in the reader
# (G303.1 = ἀνὰ μέσον, "in the midst of, between"). The auto-derivation glues it to the
# base neighbour (ανά + μέσος → "ανάμέσος"), so pin the phrase + its romanization VERBATIM
# here — same scheme as the converter (grave folded to acute) — so the reader interlinear
# matches the structural idiom card (structural.py _IDIOMS["G303.1"]).
PHRASE_OVERRIDES = {
    "303.1": ("ἀνὰ μέσον", "aná méson"),
}

# NO-ENTRY dotted numbers hand-classified as genuinely different words. These have NO
# abp_ext dictionary entry, so the auto-derivation above cannot recover them (the
# "no_entry" skip bucket) — and a no-entry dotted number is invisible to the engine's
# dotted exclusion, so its rows LEAK into the BASE word's evidence feed and its chips
# serve the base word's card on click (the corpus-defect fire that voided δόμα's floor,
# 2026-07-10 — audit doc BATCH-4 CORPUS-DEFECT FIRE entry). Classification basis cited
# per row; the ABP/eSword source is the final authority (confirm-source rule). Add a row
# ONLY with a classification on the record — never to silence a pre-pull flag.
HAND_OVERRIDES = {
    # Ezr 6:4 ×2, ABP English "layers"/"layer" — courses of masonry in the temple wall
    # (LXX 2Esdras 6:4 δόμοι). A different word from base G1390 δόμα "gift". Classified
    # at the batch-4 corpus-defect fire; unblocks δόμα's fresh floor.
    "1390.1": ("δόμος", "dómos"),
    # 1Ki 7:18 δεδικτυωμένοι "being made of lattice works" — perfect participle of the
    # verb δικτυόω "make into latticework". A different word from base G1350 δίκτυον
    # "net". Classified at the δίκτυον ruling chain step (b) (JP ABP-app reading,
    # 2026-07-11: source prints 1350.1 on δεδικτυωμένοι).
    "1350.1": ("δικτυόω", "diktyóō"),
    # Exo 27:4 δικτυωτῷ "a latticed [brass grate]" (+ Exo 38:4, Jdg 5:28, 2Ki 1:2,
    # Eze 41:16 — all lattice-adjectival English) — the adjective δικτυωτός "latticed".
    # Same ruling chain; the Exo 27:4 interlinear confirmed the adjective morphologically
    # (modifying ἐσχάραν ... χαλκῆν), not just the number.
    "1350.2": ("δικτυωτός", "diktyōtós"),
}

# LSJ headwords carry vowel-length marks (breve/macron, e.g. τραυμᾰτίας); strip them
# so the stored lemma reads clean like the rest of the dictionary (τραυματίας). These
# are the only Greek uses of combining breve (0x306) / macron (0x304); real accents
# (tonos/perispomeni/breathing) are untouched.
def strip_length_marks(s: str) -> str:
    d = unicodedata.normalize("NFD", s or "")
    d = "".join(c for c in d if c not in (chr(0x306), chr(0x304)))
    return unicodedata.normalize("NFC", d)


def same_word(a: str, b: str) -> bool:
    """True when two lemmas are the SAME word: case- and final-sigma-insensitive but
    breathing- and accent-SENSITIVE. Replaces the old bare() compare, which stripped ALL
    combining marks and so read near-homographs as identical — mountain ὄρος vs boundary
    ὅρος (differ only by breathing) and law νόμος vs pasture νομός (differ only by accent) —
    dropping the second word from dotted_lexicon and leaking it into the base word's evidence
    draw. Keep NFC (so combining vs precomposed accents still compare equal) but do NOT strip
    the marks."""
    na = unicodedata.normalize("NFC", (a or "")).lower().replace("ς", "σ")
    nb = unicodedata.normalize("NFC", (b or "")).lower().replace("ς", "σ")
    return na == nb


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
        # Skip genuine ABP form-notes, where the BASE lemma is the right card headword:
        #   (a) the εἰμί conjugations — the WHOLE 1510.x family ("[ABP] έσται ... will be",
        #       "[ABP] εισίν ... they are"). Only some carry a "Strong G####" pointer (the
        #       forms that have their own Strong's number, e.g. εστίν=G2076); the future/
        #       other tenses list only verses, so base==G1510 is the reliable test.
        #   (b) any other entry that points to a real Strong's via "Strong G####".
        # Everything else is a genuinely DIFFERENT word ABP parked at "nearest Strong's + a
        # dot" (G4521.2 σαβέκ "thicket" vs base G4521 σάββατον; γόμορ, ιωβήλ, γαυριόω ...) and
        # must get its own row. (Old blanket "[ABP]" skip hid ~hundreds of these. 2026-06-21.)
        txt = clean_text(ext["def_html"])
        if base == "G1510" or re.search(r"Strong\s+G\d", txt):
            skipped["form_note"] += 1
            continue
        correct = first_greek(ext["def_html"])
        if not correct:
            skipped["unreadable"] += 1
            continue
        if same_word(correct, shown_lemma):
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
    # Pin the hand-authored idiom phrases (override any glued auto-derived row).
    fixes = [f for f in fixes if f[0] not in PHRASE_OVERRIDES]
    for num, (phrase, tr) in PHRASE_OVERRIDES.items():
        uses = conn.execute(
            "SELECT COUNT(*) FROM words WHERE strongs = ?", (num,)
        ).fetchone()[0]
        fixes.append((num, "", phrase, tr, uses))
    # Pin the hand-classified no-entry words (nothing auto-derived exists to override,
    # but filter defensively so a future abp_ext addition can't double a row).
    fixes = [f for f in fixes if f[0] not in HAND_OVERRIDES]
    for num, (lemma, tr) in HAND_OVERRIDES.items():
        uses = conn.execute(
            "SELECT COUNT(*) FROM words WHERE strongs = ?", (num,)
        ).fetchone()[0]
        fixes.append((num, "", lemma, tr, uses))
    fixes.sort(key=lambda t: -t[4])
    abp_fixes.sort(key=lambda t: -t[4])
    return fixes, skipped, abp_fixes


def main():
    do_apply = "--apply" in sys.argv
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    fixes, skipped, abp_fixes = collect(conn)

    if "--diff" in sys.argv:                     # read-only: what would change vs the live table
        cur = {r[0] for r in conn.execute("SELECT strongs FROM dotted_lexicon")}
        proposed = {"G" + f[0]: f for f in fixes}
        added = sorted(set(proposed) - cur)
        removed = sorted(cur - set(proposed))
        print(f"[diff vs live dotted_lexicon]  +{len(added)} added  -{len(removed)} removed")
        print(f"  skipped buckets: {skipped}\n")
        print("ADDED (dotted | corrected word | romanization | uses):")
        for k in added:
            _num, _shown, correct, tr, uses = proposed[k]
            print(f"  {k} | {correct} | {tr} | {uses}")
        print("\nREMOVED (expected: none):")
        for k in removed:
            print(f"  {k}")
        conn.close()
        return

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
