#!/usr/bin/env python3
"""audit_xref_vs_binding.py — READ-ONLY census: name slots whose stored Hebrew number
is not one of their bound person's/place's own numbers (JP ruling 2026-10-24).

Found by: Gen 25:15 "Hadar" (Χολδάδ, Ishmael's son) — pn_binding has the RIGHT
entity (Hadad@Gen.25.15-1Ch, bases H2301,H2316; KJV tags H2316), but the stored
Hebrew number is H1908 (the Edomite Hadad). 1Ch 1:30 is the same man, same fault
(stored H1908, KJV H2301). This counts the whole class before any fix is chosen.

For every ABP word that has BOTH
  * a stored Hebrew number — pn_hebrew_xref.hebrew_base, else words.strongs_base
    when it is an H-number (the same precedence as the binder's guard number,
    build_entity_binding.occ_base_parts), and
  * a pn_binding row (render=1 — the rows the identity builder consumes), matched
    on the binder's own key: (entity_resolution.book_num(book), chapter, verse,
    entity_resolution.norm_name(english_head or english)),
it reports the slot when the stored number (entity_resolution.norm_base) is not
among the bound entity's tipnr_entities.bases.

Columns: book, chapter, verse, position, english, stored H, bound entity, entity
bases, KJV's H at that verse-word (+ how it was resolved), and
pn_greek_identity.hebrew_base (the frozen copy).

KJV's number: the KJV words in the same verse whose cleaned word equals the
slot's cleaned name; if they carry exactly one H-number, that one ("name").
Otherwise, the verse's KJV H-numbers that are among the entity's bases, if exactly
one ("bases"). Otherwise blank ("ambiguous" / "none" / "no-kjv-verse").

CONTROL (certification rule — a detector must fire on a known positive before a
count means anything): Gen 25:15 (stored H1908 vs H2301/H2316) and 1Ch 1:30
(stored H1908 vs H2301) must both be found. They print first; if either is
missing the script exits 2 and the count is VOID.

Never writes the database (opened read-only). Writes the full list to a TSV
(default: <db dir>/audit_xref_vs_binding.tsv) so nothing is lost to scrollback.

Usage (PA):
  python3 scripts/audit_xref_vs_binding.py ~/bible-db/bible.db
  python3 scripts/audit_xref_vs_binding.py ~/bible-db/bible.db --tsv /path/out.tsv
Exit: 0 = control found (count valid) · 2 = control missing (count VOID) ·
      3 = a required table is absent.
"""
import os
import sqlite3
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
import entity_resolution as er   # the binder's own book_num / norm_name / norm_base

REQUIRED = ("words", "verses", "pn_binding", "tipnr_entities", "pn_hebrew_xref")

# (book, chapter, verse, stored number, entity uniq) — the known positives.
CONTROLS = (
    ("Gen", 25, 15, "H1908", "Hadad@Gen.25.15-1Ch"),
    ("1Ch", 1, 30, "H1908", "Hadad@Gen.25.15-1Ch"),
)

COLS = ("book", "chapter", "verse", "position", "english", "stored_h", "entity",
        "entity_bases", "kjv_h", "kjv_how", "frozen_h")


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _bases(text):
    return {er.norm_base(b) for b in (text or "").split(",") if er.norm_base(b)}


def find_mismatches(conn):
    """Return (mismatch rows, stats). Read-only."""
    have = _tables(conn)
    binds, dup_keys = {}, 0
    for b in conn.execute("SELECT book, chapter, verse, name, entity_uniq "
                          "FROM pn_binding WHERE render=1"):
        k = (b[0], b[1], b[2], b[3])
        if k in binds and binds[k] != b[4]:
            dup_keys += 1
        binds[k] = b[4]
    ents = {u: (bases, _bases(bases)) for u, bases in
            conn.execute("SELECT uniq, bases FROM tipnr_entities")}

    frozen_sql = ("LEFT JOIN pn_greek_identity g ON g.verse_id = w.verse_id "
                  "AND g.position = w.position" if "pn_greek_identity" in have else "")
    frozen_col = "g.hebrew_base" if "pn_greek_identity" in have else "NULL"
    slots = conn.execute(f"""
        SELECT v.book, v.chapter, v.verse, w.position, w.english,
               COALESCE(NULLIF(w.english_head,''), w.english) AS label,
               x.hebrew_base AS xh, w.strongs_base AS sb, {frozen_col} AS fh
        FROM words w JOIN verses v ON v.id = w.verse_id
        LEFT JOIN pn_hebrew_xref x ON x.verse_id = w.verse_id AND x.position = w.position
        {frozen_sql}
        WHERE x.hebrew_base IS NOT NULL OR w.strongs_base LIKE 'H%'
        ORDER BY w.verse_id, w.position
    """).fetchall()

    stats = Counter(slots_with_h=len(slots), dup_bind_keys=dup_keys)
    out = []
    for book, ch, vs, pos, eng, label, xh, sb, fh in slots:
        stored = er.norm_base(xh) if xh else (er.norm_base(sb) if (sb or "").startswith("H") else "")
        if not stored:
            continue
        bk = er.book_num(book)
        nm = er.norm_name(label or "")
        uniq = binds.get((bk, ch, vs, nm)) if bk is not None else None
        if not uniq:
            stats["no_binding"] += 1
            continue
        stats["bound"] += 1
        if uniq not in ents:
            stats["entity_missing"] += 1
            continue
        raw_bases, bases = ents[uniq]
        if stored in bases:
            stats["agree"] += 1
            continue
        out.append({"book": book, "chapter": ch, "verse": vs, "position": pos,
                    "english": eng, "stored_h": stored, "entity": uniq,
                    "entity_bases": raw_bases, "frozen_h": fh or "",
                    "_bk": bk, "_nm": nm, "_bases": bases})
    _attach_kjv(conn, have, out)
    stats["mismatch"] = len(out)
    return out, stats


def _attach_kjv(conn, have, rows):
    """KJV's H-number at each mismatched slot's verse-word (see module doc)."""
    for r in rows:
        r["kjv_h"], r["kjv_how"] = "", "no-kjv-verse"
    if not rows or not {"kjv_words", "kjv_strongs"} <= have:
        return
    want = {(r["_bk"], r["chapter"], r["verse"]) for r in rows}
    toks = {}
    for bid, ch, vs, word, sid in conn.execute(
            "SELECT kw.book_id, kw.chapter, kw.verse_num, kw.word, ks.strongs_id "
            "FROM kjv_words kw JOIN kjv_strongs ks ON ks.word_id = kw.word_id "
            "WHERE ks.strongs_id LIKE 'H%'"):
        if (bid, ch, vs) in want:
            toks.setdefault((bid, ch, vs), []).append((er.norm_name(word or ""),
                                                       er.norm_base(sid)))
    for r in rows:
        vt = toks.get((r["_bk"], r["chapter"], r["verse"]))
        if not vt:
            continue
        by_name = {h for w, h in vt if w == r["_nm"] and h}
        if len(by_name) == 1:
            r["kjv_h"], r["kjv_how"] = next(iter(by_name)), "name"
            continue
        by_bases = {h for _, h in vt if h in r["_bases"]}
        if len(by_bases) == 1:
            r["kjv_h"], r["kjv_how"] = next(iter(by_bases)), "bases"
        else:
            r["kjv_how"] = "ambiguous" if (by_name or by_bases) else "none"


def _line(r):
    return "\t".join(str(r[c]) for c in COLS)


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    db = next((a for a in argv[1:] if not a.startswith("--")), None)
    if not db:
        print(__doc__)
        return 3
    # Default OUTSIDE the repo folder (bible.db sits in the PA checkout).
    tsv = argv[argv.index("--tsv") + 1] if "--tsv" in argv else \
        os.path.expanduser("~/audit_xref_vs_binding.tsv")
    conn = sqlite3.connect(f"file:{os.path.abspath(db)}?mode=ro", uri=True)
    missing = [t for t in REQUIRED if t not in _tables(conn)]
    if missing:
        print(f"HALT: required table(s) absent: {', '.join(missing)}")
        return 3

    rows, stats = find_mismatches(conn)

    print(f"[READ-ONLY] audit_xref_vs_binding -> {db}\n")
    print("== CONTROL (must both be found, or the count is VOID) ==")
    ok = True
    for book, ch, vs, h, uniq in CONTROLS:
        hit = [r for r in rows if (r["book"], r["chapter"], r["verse"], r["stored_h"],
                                   r["entity"]) == (book, ch, vs, h, uniq)]
        if hit:
            for r in hit:
                print("  FOUND   " + _line(r))
        else:
            ok = False
            print(f"  MISSING {book} {ch}:{vs} stored {h} bound {uniq}")
            # say what the binding table holds there, so a miss can be diagnosed
            for b in conn.execute("SELECT name, entity_uniq, kind, render FROM pn_binding "
                                  "WHERE book=? AND chapter=? AND verse=?",
                                  (er.book_num(book), ch, vs)):
                print(f"          binding there: name={b[0]!r} entity={b[1]} "
                      f"kind={b[2]} render={b[3]}")
    conn.close()
    if not ok:
        print("\nCONTROL FAILED — the detector did not fire on a known positive. "
              "COUNT VOID. Nothing below is trustworthy.")

    print("\n== ALL MISMATCHED SLOTS ==")
    print("\t".join(COLS))
    for r in rows:
        print(_line(r))
    with open(tsv, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(COLS) + "\n")
        for r in rows:
            f.write(_line(r) + "\n")

    pairs = Counter((r["stored_h"], r["entity"]) for r in rows)
    print("\n== SUMMARY ==")
    print(f"  slots with a stored Hebrew number : {stats['slots_with_h']:,}")
    print(f"    with a binding (render=1)       : {stats['bound']:,}")
    print(f"      agree (stored in bases)       : {stats['agree']:,}")
    print(f"      bound entity not in tipnr_entities: {stats['entity_missing']:,}")
    print(f"      MISMATCHED                    : {stats['mismatch']:,}")
    print(f"    no binding                      : {stats['no_binding']:,}")
    print(f"  binding keys with two entities    : {stats['dup_bind_keys']:,}")
    print(f"  distinct stored numbers           : {len({r['stored_h'] for r in rows}):,}")
    print(f"  distinct entities                 : {len({r['entity'] for r in rows}):,}")
    how = Counter(r["kjv_how"] for r in rows)
    print("  KJV number resolved by            : " +
          ", ".join(f"{k} {v:,}" for k, v in sorted(how.items())))
    agree_kjv = sum(1 for r in rows if r["kjv_h"] and r["kjv_h"] in r["_bases"])
    print(f"  KJV number is one of the entity's : {agree_kjv:,}")
    print("  top 20 (stored number -> bound entity) by slots:")
    for (h, u), n in pairs.most_common(20):
        print(f"    {n:5,}  {h:7} -> {u}  [{rows_bases(rows, u)}]")
    print(f"\nfull list written to {tsv}")
    print("CONTROL OK — count valid." if ok else "CONTROL FAILED — COUNT VOID.")
    return 0 if ok else 2


def rows_bases(rows, uniq):
    for r in rows:
        if r["entity"] == uniq:
            return r["entity_bases"]
    return ""


if __name__ == "__main__":
    sys.exit(main(sys.argv))
