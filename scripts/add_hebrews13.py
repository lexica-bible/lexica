#!/usr/bin/env python3
"""
add_hebrews13.py — additive repair: insert the missing Hebrews 13 into bible.db.

WHY THIS EXISTS
  Hebrews 13 was absent from the corpus. Root cause: the ABP source file
  abp_texts/abp_nt_texts/abp_hebrews.txt was missing chapter 13 (a copy-paste
  gap), so no Heb 13 verse rows were ever created — and because the words table
  is built by hanging the BibleHub scrape onto EXISTING verse rows, the Heb 13
  scrape words were skipped for want of a verse to attach to. One missing thing
  (the verse rows) cascaded into the whole chapter. Nothing else is affected;
  the per-verse parser reads explicit "(Heb 13:N)" headers, so a drop shows up
  as a missing verse, never a mangled one.

  The source file now contains ch 13 (appended + committed separately). This
  script adds ONLY Heb 13 — the 25 verse rows + their word rows — reusing the
  canonical build_words_from_abp pipeline per verse (TAGNT pronoun correction,
  bracket/greek_pos, morph/lemma, the folded fixers) so the new rows match the
  rest of the corpus exactly.

SAFE BY DESIGN
  --dry-run (DEFAULT): writes NOTHING to the live db. It snapshots the live db
    to a throwaway copy (read-only open of live → .backup; the live file is
    never opened for writing), then IN THE COPY:
      * captures the current live Heb 12 word rows as a reference,
      * deletes + regenerates Heb 12 through THIS script's build path,
      * inserts the 25 Heb 13 verse rows and builds Heb 13 the same way,
      * runs the same dependent steps the real flow uses (the folded post-fixers
        + import_tipnr name resolution),
      * DIFFS the regenerated Heb 12 against the captured live Heb 12 — expect
        EMPTY. An empty diff proves this path reproduces the canonical machine,
        so the Heb 13 rows from the SAME run are trustworthy by the same proof.
      * prints every Heb 13 verse row + word row,
      * spot-checks that the TAGNT pronoun correction actually FIRED (a Heb 13
        pronoun carries its real number, not the raw G1473).
    The copy is deleted at the end. The live db is untouched.

  --apply: performs ONLY additive inserts on the LIVE db — 25 verse rows + the
    Heb 13 word rows (then the same folded post-fixers, which only touch the new
    rows). It NEVER deletes or rewrites an existing row, and refuses if Heb 13 is
    already present. Reversible: delete the 25 Heb 13 verse rows + their words.
    After --apply, run the standard post-words builders (printed at the end):
    import_tipnr, build_abp_surface, build_abp_translit, build_dotted_lexicon,
    build_entity_binding, build_two_ending.

Run on PythonAnywhere:
  python3 scripts/add_hebrews13.py ~/bible-db/bible.db ~/bible-db/bh_scrape.db --dry-run
  python3 scripts/add_hebrews13.py ~/bible-db/bible.db ~/bible-db/bh_scrape.db --apply
"""

import argparse
import subprocess
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Reuse the canonical build's own per-verse machinery — same functions the full
# rebuild calls, so the rows are produced identically.
from build_words_from_abp import (
    iter_verses, _abp_sources, ABBREV_TO_SLUG,
    load_bh_verse_index, load_lexicon, build_verse_words,
    apply_pronoun_corrections, _prefix_base, TAGNT_FILES,
)
from load_abp_prose import clean_verse, VERSE_RE as PROSE_VERSE_RE

# Pronoun-correction source (NT). Imported the same way build_words_from_abp does.
try:
    from build_words_from_abp import TAGNTSource, correct_verse
except ImportError:
    TAGNTSource = correct_verse = None

# The whole-table folded fixers the canonical build runs after insert. Optional;
# a missing one just prints a note (matches build_words_from_abp's own guards).
try:
    from fill_blank_strongs import apply_blank_strongs_fills
except ImportError:
    apply_blank_strongs_fills = None
try:
    from fix_pn_subject_merge import run as apply_pn_subject_split
except ImportError:
    apply_pn_subject_split = None
try:
    from fix_italic_heads import run as apply_italic_heads
except ImportError:
    apply_italic_heads = None

ABBREV = "Heb"
NEW_CH = 13
PROOF_CH = 12

WORD_INSERT = (
    "INSERT INTO words"
    " (verse_id, position, english, english_head, strongs, strongs_base,"
    "  greek_pos, bracket_id, italic, italic_words, smcap_words, morph, lemma)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)

# Columns compared for the Heb 12 proof (the full word row, minus the auto id).
CMP_COLS = ("position", "english", "english_head", "strongs", "strongs_base",
            "greek_pos", "bracket_id", "italic", "italic_words", "smcap_words",
            "morph", "lemma", "is_pn")


# ── ABP source for Hebrews 13 / 12 ──────────────────────────────────────────────

def abp_chapter_verses(chapters):
    """Yield (chapter, verse, abp_words, raw_text) for Hebrews in `chapters`,
    straight from the (now-complete) ABP source file via the canonical parser."""
    # raw verse text (for verses.text prose) keyed by (ch, vs)
    raw = {}
    for d in (_abp_sources()):
        p = Path(d)
        if p.is_dir():
            f = p / "abp_hebrews.txt"
            if f.is_file():
                for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                    m = PROSE_VERSE_RE.match(line.strip())
                    if m and m.group(1) == ABBREV and int(m.group(2)) in chapters:
                        raw[(int(m.group(2)), int(m.group(3)))] = m.group(4)
    out = []
    for abbrev, ch, vs, words in iter_verses(*_abp_sources()):
        if abbrev == ABBREV and ch in chapters:
            out.append((ch, vs, words, raw.get((ch, vs), "")))
    return out


def _tagnt():
    if TAGNTSource and all(Path(p).is_file() for p in TAGNT_FILES):
        return TAGNTSource([str(p) for p in TAGNT_FILES])
    return None


def build_words_for(con, scrape, chapters, tagnt):
    """Build Hebrews `chapters` word rows through the canonical per-verse path and
    INSERT them into `con` (which already has the verse rows). Returns count."""
    verse_map = {(b, c, v): vid for vid, b, c, v in
                 con.execute("SELECT id, book, chapter, verse FROM verses")}
    lex = load_lexicon(con)
    bh_index = load_bh_verse_index(scrape)
    slug = ABBREV_TO_SLUG[ABBREV]
    bnum = tagnt.booknum(ABBREV) if tagnt else None

    n = 0
    for ch, vs, abp_words, _raw in abp_chapter_verses(chapters):
        verse_id = verse_map.get((ABBREV, ch, vs))
        if not verse_id:
            print(f"  !! no verse row for {ABBREV} {ch}:{vs} — skipped", file=sys.stderr)
            continue
        bh_rows = bh_index.get((slug, ch, vs), [])
        if tagnt and bnum and correct_verse:
            corrs = correct_verse([w[1] for w in abp_words],
                                  tagnt.verse(bnum, ch, vs),
                                  [w[0] for w in abp_words])
            abp_words = apply_pronoun_corrections(abp_words, corrs, [], f"{ABBREV} {ch}:{vs}")
        word_rows = build_verse_words(abp_words, bh_rows, lex)
        con.executemany(WORD_INSERT, [(verse_id, *_prefix_base(w)) for w in word_rows])
        n += len(word_rows)
    con.commit()
    return n


def run_post_fixers(con):
    if apply_blank_strongs_fills:
        apply_blank_strongs_fills(con, apply=True, log=lambda _m: None); con.commit()
    if apply_pn_subject_split:
        try:
            apply_pn_subject_split(con, apply=True, log=lambda *_a: None); con.commit()
        except Exception as e:
            print(f"  (subject-name split skipped: {e})")
    if apply_italic_heads:
        try:
            apply_italic_heads(con, apply=True, log=lambda *_a: None); con.commit()
        except Exception as e:
            print(f"  (italic-head re-clean skipped: {e})")


def insert_verse_rows(con):
    """INSERT the 25 Heb 13 verse rows (book/chapter/verse + clean prose text).
    Additive: INSERT OR IGNORE on the (book,chapter,verse) uniqueness."""
    n = 0
    for ch, vs, _words, raw in abp_chapter_verses((NEW_CH,)):
        con.execute(
            "INSERT OR IGNORE INTO verses (book, chapter, verse, text) VALUES (?,?,?,?)",
            (ABBREV, ch, vs, clean_verse(raw)))
        n += 1
    con.commit()
    return n


def read_chapter_words(con, chapter):
    """Full word rows for Hebrews `chapter`, ordered, for byte-compare/printing."""
    cols = ", ".join("w." + c for c in CMP_COLS)
    return con.execute(
        f"SELECT v.verse, {cols} FROM verses v JOIN words w ON w.verse_id = v.id"
        f" WHERE v.book=? AND v.chapter=? ORDER BY v.verse, w.position",
        (ABBREV, chapter)).fetchall()


# ── Dry-run: prove Heb 12 reproduces, show Heb 13, confirm the pronoun fix ───────

def dry_run(bible_db, scrape_db):
    target = bible_db + ".heb13dry"
    for sc in (target, target + "-wal", target + "-shm"):
        if Path(sc).exists():
            Path(sc).unlink()

    print(f"Snapshotting live {bible_db} → {target} (live opened READ-ONLY) …")
    live_ro = sqlite3.connect(f"file:{bible_db}?mode=ro", uri=True)
    copy = sqlite3.connect(target)
    try:
        live_ro.backup(copy)
    finally:
        live_ro.close()
    print("Snapshot done — live db untouched from here on.\n")

    scrape = sqlite3.connect(f"file:{scrape_db}?mode=ro", uri=True)
    tagnt = _tagnt()
    print("TAGNT (NT pronoun correction): " + ("LOADED" if tagnt else "NOT FOUND — pronoun fix would be SKIPPED"))

    # 0) reference: the live Heb 12 rows, captured from the pristine copy
    live_heb12 = read_chapter_words(copy, PROOF_CH)
    print(f"Live Heb {PROOF_CH} word rows captured: {len(live_heb12)}\n")

    # 1) regenerate Heb 12 through this path (delete + rebuild in the copy)
    copy.execute(
        "DELETE FROM words WHERE verse_id IN"
        " (SELECT id FROM verses WHERE book=? AND chapter=?)", (ABBREV, PROOF_CH))
    copy.commit()

    # 2) add Heb 13 verse rows, then build Heb 12 + Heb 13 words
    insert_verse_rows(copy)
    nbuilt = build_words_for(copy, scrape, (PROOF_CH, NEW_CH), tagnt)
    print(f"Rebuilt Heb {PROOF_CH} + Heb {NEW_CH}: {nbuilt} word rows.")

    # 3) same dependent steps the real flow uses, so the compare is apples-to-apples
    run_post_fixers(copy)
    copy.close()
    print("Running import_tipnr on the copy (restores proper-noun numbers + is_pn) …")
    r = subprocess.run([sys.executable, str(Path(__file__).parent / "import_tipnr.py"), target],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("  import_tipnr FAILED:\n" + r.stdout[-2000:] + r.stderr[-2000:])
    copy = sqlite3.connect(target)

    # ── Proof 1: Heb 12 diff (expect EMPTY) ─────────────────────────────────────
    new_heb12 = read_chapter_words(copy, PROOF_CH)
    print("\n================ PROOF 1 — Heb 12 byte-diff (expect EMPTY) ================")
    if live_heb12 == new_heb12:
        print(f"  ✅ IDENTICAL — {len(new_heb12)} rows match byte-for-byte.")
        print("     This path reproduces the canonical build; Heb 13 below is trustworthy.")
    else:
        print(f"  ❌ DIFFERENCES: live={len(live_heb12)} rows, rebuilt={len(new_heb12)} rows")
        ref = {(r[0], r[1]): r for r in live_heb12}   # (verse, position) -> row
        new = {(r[0], r[1]): r for r in new_heb12}
        keys = sorted(set(ref) | set(new))
        shown = 0
        for k in keys:
            a, b = ref.get(k), new.get(k)
            if a != b:
                print(f"    {ABBREV} 12:{k[0]} pos{k[1]}")
                print(f"      live :{a}")
                print(f"      built:{b}")
                shown += 1
                if shown >= 40:
                    print("    … (more) …"); break

    # ── Heb 13 rows ─────────────────────────────────────────────────────────────
    print("\n================ Heb 13 — verse rows ================")
    for vs, txt in copy.execute(
            "SELECT verse, text FROM verses WHERE book=? AND chapter=? ORDER BY verse",
            (ABBREV, NEW_CH)):
        print(f"  Heb 13:{vs:<2}  {txt}")

    heb13 = read_chapter_words(copy, NEW_CH)
    print(f"\n================ Heb 13 — word rows ({len(heb13)}) ================")
    print("  (verse pos | strongs strongs_base | english | head | gpos bid ital | morph | lemma | is_pn)")
    for r in heb13:
        (verse, position, english, head, strongs, sbase, gpos, bid,
         ital, iw, sw, morph, lemma, is_pn) = r
        print(f"  13:{verse:<2} {position:<3} | {str(strongs):>7} {str(sbase):>7} |"
              f" {str(english):<22} | {str(head):<14} |"
              f" g={gpos} b={bid} i={ital} | {morph or '-':<10} | {lemma or '-':<14} | pn={is_pn or 0}")

    # ── Proof 2: TAGNT pronoun correction fired on Heb 13 ───────────────────────
    print("\n================ PROOF 2 — pronoun fix fired on Heb 13 ================")
    # Heb 13 carries many ABP G1473 pronouns. After correction the 1st/2nd-person
    # forms keep 1473 (ἐγώ/σύ family) but 3rd-person ones flip to 846 (αὐτός) etc.
    # Show every Heb 13 slot whose number is in the pronoun family, with its gloss.
    pron_bases = {"G1473", "G846", "G4771", "G5210", "G2249", "G4771"}
    found = [r for r in heb13 if r[5] in pron_bases]
    if not found:
        print("  (no pronoun-family slots found — unexpected; inspect the rows above)")
    for r in found:
        verse, position, english, head, strongs, sbase = r[0], r[1], r[2], r[3], r[4], r[5]
        tag = "  <-- corrected off raw G1473" if sbase != "G1473" else "  (1st/2nd person — stays 1473)"
        print(f"  13:{verse:<2} pos{position:<3} {str(sbase):>6}  '{english}'{tag}")
    any_corrected = any(r[5] != "G1473" for r in found)
    print("\n  " + ("✅ correction FIRED (≥1 slot moved off raw G1473)." if any_corrected
                    else "⚠️  no slot moved off G1473 — verify TAGNT loaded and Heb 13 has 3rd-person pronouns."))

    copy.close()
    for sc in (target, target + "-wal", target + "-shm"):
        if Path(sc).exists():
            Path(sc).unlink()
    print(f"\nDry-run complete. Throwaway copy deleted. Live {bible_db} never written.")


# ── Apply: additive insert into the live db ─────────────────────────────────────

def apply(bible_db, scrape_db):
    con = sqlite3.connect(bible_db)
    have = con.execute(
        "SELECT COUNT(*) FROM verses WHERE book=? AND chapter=?", (ABBREV, NEW_CH)).fetchone()[0]
    if have:
        print(f"REFUSING: Heb {NEW_CH} already has {have} verse row(s). Nothing to do.")
        con.close()
        return

    scrape = sqlite3.connect(f"file:{scrape_db}?mode=ro", uri=True)
    tagnt = _tagnt()
    if not tagnt:
        print("ABORT: TAGNT not found — the pronoun correction would be skipped, so the\n"
              "       rows would NOT match the corpus. Fix the TAGNT path and retry.")
        con.close(); scrape.close()
        return

    nv = insert_verse_rows(con)
    nw = build_words_for(con, scrape, (NEW_CH,), tagnt)
    run_post_fixers(con)
    con.close(); scrape.close()
    print(f"Inserted {nv} verse rows + {nw} word rows for Heb {NEW_CH} (additive; no existing row touched).")
    print("\nNEXT — dependent re-runs (resolve names, surface forms, etc.):")
    print(f"  python3 scripts/import_tipnr.py {bible_db}")
    print(f"  python3 scripts/build_abp_surface.py {bible_db} --bh {scrape_db}")
    print(f"  python3 scripts/build_abp_translit.py {bible_db}")
    print(f"  python3 scripts/build_dotted_lexicon.py {bible_db}        # Heb 13 has dotted G3766.2 / G1510.6")
    print(f"  python3 scripts/build_entity_binding.py {bible_db} --apply")
    print(f"  python3 scripts/build_two_ending.py {bible_db}")
    print(f"  touch /var/www/www_lexica_bible_wsgi.py")
    print("\nUndo (reversible): delete the 25 Heb 13 verse rows + their words.")


def main():
    ap = argparse.ArgumentParser(description="Additively add Hebrews 13 to bible.db.")
    ap.add_argument("bible_db", nargs="?", default="bible.db")
    ap.add_argument("scrape_db", nargs="?", default="bh_scrape.db")
    ap.add_argument("--apply", action="store_true", help="write to the live db (default is a dry-run)")
    args = ap.parse_args()
    for p in (args.bible_db, args.scrape_db):
        if not Path(p).exists():
            print(f"ERROR: {p} not found."); sys.exit(1)
    if args.apply:
        apply(args.bible_db, args.scrape_db)
    else:
        dry_run(args.bible_db, args.scrape_db)


if __name__ == "__main__":
    main()
