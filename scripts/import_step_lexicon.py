#!/usr/bin/env python3
"""import_step_lexicon.py — R-2 stage 1: the STEP extended Greek lexicon as a side table.

Builds `step_lexicon` from the SAME TBESG file build_word_gloss.py already uses
(STEPBible-Data, CC BY 4.0 — credit line already in CREDITS.md), but keeps the FULL
entry per extended Strong's number (eStrong like G9827) instead of only a gloss fill:
number, Greek lemma, transliteration, brief gloss. This is what makes TIPNR's Greek
name numbers renderable (R2-Q1, ruled yes 2026-07-24).

Reuses build_word_gloss's production reader/parser helpers — never a re-implementation.
Writes ONLY its own table (DROP+CREATE step_lexicon); words/verses untouched. Additive:
no live code reads the table until the stage-2 flip.

Usage (PA):
  python3 scripts/import_step_lexicon.py ~/bible-db/bible_test.db            # dry-run report
  python3 scripts/import_step_lexicon.py ~/bible-db/bible_test.db --apply
Optional: --tbesg <path-or-url> to override the pinned download URL.
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_word_gloss import TBESG, _read_source  # production source + reader

DB = next((a for a in sys.argv[1:] if not a.startswith("--")),
          os.path.expanduser("~/bible-db/bible.db"))
APPLY = "--apply" in sys.argv


def parse_full(src):
    """Full TBESG rows keyed by eStrong, FIRST row per number wins (the file is
    base-sense-first, same rule as build_word_gloss.parse_tbesg). Column indexes are
    read from the file's own header line, never assumed."""
    lines = _read_source(src).splitlines()
    hdr_i = next((i for i, ln in enumerate(lines)
                  if ln.split("\t")[0].strip().rstrip("#") == "eStrong" and "Gloss" in ln), None)
    if hdr_i is None:
        raise SystemExit(f"could not find the data header in {src}")
    hdr = [h.strip().rstrip("#") for h in lines[hdr_i].split("\t")]
    col = {name: hdr.index(name) for name in hdr if name}
    need = [k for k in ("eStrong", "Greek", "Gloss") if k not in col]
    if need:
        raise SystemExit(f"TBESG header lacks expected column(s) {need}: {hdr}")
    i_num, i_lem, i_gloss = col["eStrong"], col["Greek"], col["Gloss"]
    i_translit = col.get("Transliteration", col.get("Translit"))

    out = {}
    for ln in lines[hdr_i + 1:]:
        if not ln.strip() or ln.startswith("$"):
            continue
        c = ln.split("\t")
        if len(c) <= i_gloss or not c[i_num].strip().startswith("G"):
            continue
        num = c[i_num].strip()
        gloss = c[i_gloss].strip()
        if not gloss:
            continue
        translit = c[i_translit].strip() if i_translit is not None and len(c) > i_translit else ""
        out.setdefault(num, (c[i_lem].strip(), translit, gloss))
    return out


def base_int(estrong):
    """'G9827' / 'G0007G' -> 9827 / 7 (digits only, disambiguator letter dropped)."""
    digits = "".join(ch for ch in estrong[1:] if ch.isdigit())
    return int(digits) if digits else None


def main():
    print(f"{'[APPLY] ' if APPLY else '[DRY-RUN] '}import_step_lexicon -> {DB}\n")
    rows = parse_full(TBESG)
    ext = {n for n in rows if (base_int(n) or 0) >= 6000}
    print(f"TBESG entries: {len(rows):,}  (extended G6000+ numbers: {len(ext):,})")

    # Coverage control: how many of TIPNR's Greek numbers does TBESG carry?
    # (The gap count feeds Q3's lemma-only state — counted, never papered.)
    import import_tipnr
    tipnr_lines = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                                    "tipnr", "TIPNR.txt"), encoding="utf-8-sig").read().splitlines()
    lookup, _ = import_tipnr.parse_tipnr(tipnr_lines)
    tipnr_g = {e["g"] for e in lookup.values() if e.get("g")}
    step_bases = {base_int(n) for n in rows}
    covered = {g for g in tipnr_g if int(g[1:]) in step_bases}
    missing = sorted(tipnr_g - covered, key=lambda s: int(s[1:]))
    print(f"TIPNR Greek numbers: {len(tipnr_g):,}  covered by TBESG: {len(covered):,}  "
          f"missing: {len(missing):,}")
    if missing:
        print("  missing (first 20):", ", ".join(missing[:20]))
    print()

    if not APPLY:
        print("Dry-run only — nothing written. Re-run with --apply.")
        return

    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("DROP TABLE IF EXISTS step_lexicon")
    conn.execute("""
        CREATE TABLE step_lexicon (
            estrong  TEXT PRIMARY KEY,   -- as in TBESG, e.g. 'G9827', 'G0007G'
            base     INTEGER,            -- numeric base, e.g. 9827 (indexable join key)
            lemma    TEXT,
            translit TEXT,
            gloss    TEXT
        )
    """)
    conn.executemany(
        "INSERT INTO step_lexicon(estrong, base, lemma, translit, gloss) VALUES(?,?,?,?,?)",
        [(n, base_int(n), lem, tr, gl) for n, (lem, tr, gl) in sorted(rows.items())],
    )
    conn.execute("CREATE INDEX idx_step_lexicon_base ON step_lexicon(base)")
    conn.commit()
    n = conn.execute("SELECT count(*) FROM step_lexicon").fetchone()[0]
    print(f"Wrote step_lexicon: {n:,} rows.")


if __name__ == "__main__":
    main()
