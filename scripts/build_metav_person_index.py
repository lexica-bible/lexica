#!/usr/bin/env python3
"""
build_metav_person_index.py — distill MetaV's per-word index down to two slim
person tables, WITHOUT loading its ~790K-row MainIndex into bible.db.

MetaV anchors every KJV word to a person + a verse (MainIndex.csv: PersonID +
BookID/Chapter/VerseNum + WordID) and every word to a Strong's number
(StrongsIndex.csv: WordID -> StrongsID). Grouping those by PersonID gives us
exactly what the entity->metaV person cross-link needs:

    metav_person_strongs(person_id, strongs_id, count)   -- which Strong's a person is tagged with
    metav_person_verses (person_id, book_id, chapter, verse)  -- the person's real verse set

Both are written to a STANDALONE staging file (default metav_index.db), NOT bible.db.
The link builder reads this staging file read-only. Nothing touches bible.db here.

The ~790K MainIndex rows stay on PA as CSV; only these two distilled tables exist,
and only the link builder's --apply step (a separate, checkpoint-gated script) ever
proposes loading them into bible.db.

Run on PythonAnywhere:
    python3 scripts/build_metav_person_index.py            # build staging metav_index.db + report
    python3 scripts/build_metav_person_index.py --csv /home/appssanding720/MetaV/CSV \
                                                --out  /home/appssanding720/bible-db/metav_index.db

NOTE (handoff): MainIndex carries PlaceID per word too, so the IDENTICAL distill
yields metav_place_strongs / metav_place_verses. Not built here (persons-only
scope), but it means E's parked place cross-link is reachable without OpenBibleInfo
— revisit that parking decision with this in hand.
"""
import csv, os, re, sqlite3, sys
from collections import defaultdict

CSV_DIR = "/home/appssanding720/MetaV/CSV"
OUT_DB  = "/home/appssanding720/bible-db/metav_index.db"
for i, a in enumerate(sys.argv):
    if a == "--csv" and i + 1 < len(sys.argv):
        CSV_DIR = sys.argv[i + 1]
    if a == "--out" and i + 1 < len(sys.argv):
        OUT_DB = sys.argv[i + 1]

# csv can hand us very long fields; lift the limit so MainIndex never trips it
csv.field_size_limit(10 * 1024 * 1024)


def norm_strong(raw, book_id):
    """Normalize a MetaV StrongsID to our house form: 'H2148' / 'G4151', zero-stripped.
    Prefixed input ('H02148') keeps its letter; BARE input ('2148') is prefixed by
    testament from the book number (<=39 OT -> H, else NT -> G) — the only sane guess
    when the source omits the letter."""
    raw = (raw or "").strip().strip('"')
    m = re.match(r"([GgHh]?)0*(\d+)", raw)
    if not m:
        return ""
    letter, num = m.group(1).upper(), m.group(2)
    if not letter:
        letter = "H" if book_id <= 39 else "G"
    return f"{letter}{int(num)}"


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        yield from csv.DictReader(fh)


def main():
    main_csv = os.path.join(CSV_DIR, "MainIndex.csv")
    strong_csv = os.path.join(CSV_DIR, "StrongsIndex.csv")
    for p in (main_csv, strong_csv):
        if not os.path.exists(p):
            print(f"MISSING {p}")
            sys.exit(2)

    # WordID -> StrongsID (raw); only tagged words appear
    print("reading StrongsIndex ...")
    strong_by_word = {}
    for r in read_rows(strong_csv):
        strong_by_word[r["WordID"]] = r["StrongsID"]
    print(f"  {len(strong_by_word):,} words carry a Strong's number")

    # walk MainIndex once: collect person->verses and person->strongs(count)
    print("reading MainIndex ...")
    pv = set()                                  # (person_id, book, ch, vs)
    ps = defaultdict(int)                        # (person_id, strongs) -> count
    n_rows = n_person = 0
    raw_strong_samples = []
    for r in read_rows(main_csv):
        n_rows += 1
        pid = (r.get("PersonID") or "").strip()
        if not pid:
            continue
        n_person += 1
        pid = int(pid)
        book = int(r["BookID"])
        pv.add((pid, book, int(r["Chapter"]), int(r["VerseNum"])))
        raw = strong_by_word.get(r["WordID"])
        if raw:
            if len(raw_strong_samples) < 10:
                raw_strong_samples.append((raw, book))
            s = norm_strong(raw, book)
            if s:
                ps[(pid, s)] += 1
    print(f"  {n_rows:,} rows, {n_person:,} word-tags on a person")

    persons = {p for (p, *_ ) in pv}
    print(f"  {len(persons):,} distinct people occur in the text")
    print("  sample raw StrongsID -> normalized (verify the format is read right):")
    for raw, bk in raw_strong_samples[:6]:
        print(f"    {raw!r:>12}  (book {bk})  ->  {norm_strong(raw, bk)}")

    # write the two slim tables to the STAGING db (never bible.db)
    if os.path.exists(OUT_DB):
        os.remove(OUT_DB)
    w = sqlite3.connect(OUT_DB)
    try:
        w.execute("CREATE TABLE metav_person_strongs(person_id INT, strongs_id TEXT, count INT)")
        w.execute("CREATE TABLE metav_person_verses(person_id INT, book_id INT, chapter INT, verse INT)")
        w.executemany("INSERT INTO metav_person_strongs VALUES(?,?,?)",
                      [(p, s, c) for (p, s), c in ps.items()])
        w.executemany("INSERT INTO metav_person_verses VALUES(?,?,?,?)",
                      [(p, b, c, v) for (p, b, c, v) in pv])
        w.execute("CREATE INDEX ix_mps ON metav_person_strongs(person_id)")
        w.execute("CREATE INDEX ix_mpv ON metav_person_verses(person_id)")
        w.commit()
    finally:
        w.close()
    print(f"\nWrote {OUT_DB}")
    print(f"  metav_person_strongs : {len(ps):,} (person,strongs) rows")
    print(f"  metav_person_verses  : {len(pv):,} (person,verse) rows")
    print("\nStaging file only — add metav_index.db to .gitignore; it never joins bible.db")
    print("until the link builder's checkpoint-gated --apply.")


if __name__ == "__main__":
    main()
