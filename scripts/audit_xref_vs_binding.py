#!/usr/bin/env python3
"""audit_xref_vs_binding.py — READ-ONLY census: name slots whose stored Hebrew number
is not one of their bound person's/place's own numbers (JP rulings 2026-10-24).

Found by: Gen 25:15 "Hadar" (Χολδάδ, Ishmael's son) — pn_binding has the RIGHT
entity (Hadad@Gen.25.15-1Ch, bases H2301,H2316; KJV tags H2316), but the stored
Hebrew number is H1908 (the Edomite Hadad). 1Ch 1:30 is the same man, same fault
(stored H1908, KJV H2301). First run (10/24): 369 slots, control OK — but several
different kinds, so every row now gets a CLASS before any fix is chosen.

WHICH SLOTS. For every ABP word that has BOTH
  * a stored Hebrew number — pn_hebrew_xref.hebrew_base, else words.strongs_base
    when it is an H-number (the binder's guard-number precedence,
    build_entity_binding.occ_base_parts), and
  * a pn_binding row (render=1 — the rows the identity builder consumes), matched
    on the binder's own key: (entity_resolution.book_num(book), chapter, verse,
    entity_resolution.norm_name(english_head or english)),
it reports the slot when the stored number (entity_resolution.norm_base) is not
among the bound entity's tipnr_entities.bases.

CLASSES — every row gets exactly one, first match wins (JP precedence):
  1 NT-SLOT                 the slot is in a NT book (book 40-66).
  2 NO-HEBREW-ENTITY        the bound entity's bases hold no H-number (Paul).
  3 COMPOUND                a two-part name links the two sides, and no TIPNR
                            entity on the stored side shares the bound entity's
                            head: the stored number's entity head is one part of
                            a multi-part name of the bound entity (Obed on
                            Obed-edom, Gilead on Ramoth-gilead, Hadad on
                            Ben-hadad), or the bound head is one part of a
                            multi-part name of the stored side. `printed_as`:
                            one-slot = this slot's own English name carries the
                            whole compound ("Obed-edom"); split = it carries one
                            part ("Hadad" in "son of Hadad").
  4 SAME-NAME-OTHER-REFERENT  a TIPNR entity carrying the stored number has the
                            same head as the bound entity (Shechem, Sheba, Hadad).
  5 VARIANT-NUMBER          heads differ, but TIPNR lists a shared spelling on
                            both sides, or the binder's own alias map
                            (entity_resolution.name_variants) links them.
  6 PRINTED-NAME-DIFFERS    ABP's own English name for the slot is not one of
                            the bound entity's TIPNR spellings, nor alias-linked
                            (Artaxerxes printed, Ahasuerus bound). NOTE: TIPNR's
                            production parse keeps English spellings only (no
                            Greek), so this compares ABP's English, not its Greek;
                            the Greek form is shown in its own column.
  7 OTHER                   anything left — printed in full in the summary.

TIPNR names come from the production parse (entity_resolution.parse_tipnr) of the
pinned tipnr/TIPNR.txt — the file the binder builds from. Spellings like
'hadar|hadad' split on '|'; translation tags (niv/esv/kjv) are dropped. Entities
missing from the parse fall back to tipnr_entities.head.

KJV's number: the KJV words in the same verse whose cleaned word equals the slot's
cleaned name; if they carry exactly one H-number, that one ("name"). Otherwise the
verse's KJV H-numbers that are among the entity's bases, if exactly one ("bases").
Otherwise blank ("ambiguous" / "none" / "no-kjv-verse"). "KJV-backed" = KJV's
number is one of the bound entity's.

CONTROL (certification rule — a detector must fire on a known positive): Gen 25:15
(stored H1908 vs H2301/H2316) and 1Ch 1:30 (stored H1908 vs H2301) must both be
found AND both land in class 4. They print first; otherwise exit 2, count VOID.

KNOWN BLIND SPOT (JP-filed 10/24, no lane): slots with a stored number but no
render=1 binding (14,141 on the first run) are not checked at all.

Never writes the database (opened read-only). Writes two lists, outside the repo:
  ~/audit_xref_vs_binding.tsv          (the first run's columns, unchanged)
  ~/audit_xref_vs_binding_classed.tsv  (+ class, printed_as, slot name, Greek form,
                                        stored-side heads, KJV-backed)

Usage (PA):
  python3 scripts/audit_xref_vs_binding.py ~/bible-db/bible.db
  python3 scripts/audit_xref_vs_binding.py ~/bible-db/bible.db --tsv /path/out.tsv \
      [--tipnr /path/TIPNR.txt]
Exit: 0 = control found in class 4 (count valid) · 2 = control missing or
      misclassed (count VOID) · 3 = a required table or the TIPNR file is absent.
"""
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
import entity_resolution as er   # the binder's own helpers — never copies

REQUIRED = ("words", "verses", "pn_binding", "tipnr_entities", "pn_hebrew_xref")
TIPNR_PINNED = os.path.join(_HERE, "..", "tipnr", "TIPNR.txt")

NT, NOHEB, COMPOUND, SAME, VARIANT, PRINTED, OTHER = (
    "1 NT-SLOT", "2 NO-HEBREW-ENTITY", "3 COMPOUND", "4 SAME-NAME-OTHER-REFERENT",
    "5 VARIANT-NUMBER", "6 PRINTED-NAME-DIFFERS", "7 OTHER")
CLASSES = (NT, NOHEB, COMPOUND, SAME, VARIANT, PRINTED, OTHER)

# (book, chapter, verse, stored number, entity uniq) — the known positives, class 4.
CONTROLS = (
    ("Gen", 25, 15, "H1908", "Hadad@Gen.25.15-1Ch"),
    ("1Ch", 1, 30, "H1908", "Hadad@Gen.25.15-1Ch"),
)

COLS = ("book", "chapter", "verse", "position", "english", "stored_h", "entity",
        "entity_bases", "kjv_h", "kjv_how", "frozen_h")
CLASSED_COLS = COLS + ("class", "printed_as", "slot_name", "greek_form",
                       "stored_heads", "kjv_backed")

_TAGS = {"niv", "esv", "kjv", "nasb", "nrsv", "nkjv"}
_LEAD = re.compile(r"^(?:(?:of|the|and|to|from|in|son|sons|daughter)\s+)+")


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _bases(text):
    return {er.norm_base(b) for b in (text or "").split(",") if er.norm_base(b)}


def _clean(name):
    return er.norm_name(name or "").replace("_", " ").strip()


def _names_of(ent):
    """TIPNR spellings of one parsed entity, '|'-split, tags dropped, + its head."""
    out = {_clean(ent["head"])}
    for s in ent["spellings"]:
        for p in s.split("|"):
            n = _clean(p)
            if n and n not in _TAGS and re.match(r"^[a-z][a-z' -]*$", n):
                out.add(n)
    out.discard("")
    return out


def _parts(name):
    return [p for p in re.split(r"[-\s]+", name) if p]


def _slot_name(label):
    return _LEAD.sub("", _clean(label)).strip()


class Tipnr:
    """Head/spelling lookups over the production TIPNR parse + the db fallback."""

    def __init__(self, ents, db_heads, db_bases):
        self.by_uniq = {e["uniq"]: e for e in ents}
        self.by_base = defaultdict(list)
        for e in ents:
            for b in e["bases"]:
                self.by_base[b].append(e)
        self.db_heads, self.db_bases = db_heads, db_bases

    def bound(self, uniq):
        e = self.by_uniq.get(uniq)
        if e:
            return {_clean(e["head"])}, _names_of(e)
        h = _clean(self.db_heads.get(uniq, ""))
        return ({h}, {h}) if h else (set(), set())

    def stored(self, base):
        es = self.by_base.get(base, [])
        heads = {_clean(e["head"]) for e in es}
        names = set().union(*[_names_of(e) for e in es]) if es else set()
        if not es:   # fall back to the db's own entity rows carrying the number
            for u, bs in self.db_bases.items():
                if base in bs and self.db_heads.get(u):
                    h = _clean(self.db_heads[u])
                    heads.add(h)
                    names.add(h)
        heads.discard("")
        return heads, names


def _compact_set(names):
    return {er._compact(n) for n in names if n}


def _alias_linked(a_names, b_names):
    for a in a_names:
        if er.name_variants(a) & b_names:
            return True
    for b in b_names:
        if er.name_variants(b) & a_names:
            return True
    return False


def classify(r, tip):
    """Exactly one class per row (module doc). Sets r['class'], r['printed_as'],
    r['stored_heads']."""
    r["printed_as"], r["stored_heads"] = "", ""
    if r["_bk"] is not None and r["_bk"] >= 40:
        return NT
    if not any(b.startswith("H") for b in r["_bases"]):
        return NOHEB
    b_heads, b_names = tip.bound(r["entity"])
    s_heads, s_names = tip.stored(r["stored_h"])
    r["stored_heads"] = ",".join(sorted(s_heads))
    same_head = bool(_compact_set(s_heads) & _compact_set(b_heads))
    if not same_head:
        comp = None
        for n in b_names:                       # stored part of a bound compound
            if len(_parts(n)) >= 2 and set(_parts(n)) & s_heads:
                comp = n
                break
        if comp is None:
            for n in s_names:                   # bound part of a stored compound
                if len(_parts(n)) >= 2 and set(_parts(n)) & b_heads:
                    comp = n
                    break
        if comp is not None:
            sn = r["slot_name"]
            whole = len(_parts(sn)) >= 2 or er._compact(sn) == er._compact(comp)
            r["printed_as"] = "one-slot" if whole else "split"
            return COMPOUND
    if same_head:
        return SAME
    if (_compact_set(s_names) & _compact_set(b_names)) or _alias_linked(s_names, b_names):
        return VARIANT
    sn = r["slot_name"]
    if sn and er._compact(sn) not in _compact_set(b_names) \
            and not (er.name_variants(sn) & b_names):
        return PRINTED
    return OTHER


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
    form_sql = ("LEFT JOIN abp_surface s ON s.verse_id = w.verse_id "
                "AND s.position = w.position" if "abp_surface" in have else "")
    form_col = "s.form" if "abp_surface" in have else "NULL"
    slots = conn.execute(f"""
        SELECT v.book, v.chapter, v.verse, w.position, w.english,
               COALESCE(NULLIF(w.english_head,''), w.english) AS label,
               x.hebrew_base AS xh, w.strongs_base AS sb, {frozen_col} AS fh,
               {form_col} AS gf
        FROM words w JOIN verses v ON v.id = w.verse_id
        LEFT JOIN pn_hebrew_xref x ON x.verse_id = w.verse_id AND x.position = w.position
        {frozen_sql}
        {form_sql}
        WHERE x.hebrew_base IS NOT NULL OR w.strongs_base LIKE 'H%'
        ORDER BY w.verse_id, w.position
    """).fetchall()

    stats = Counter(slots_with_h=len(slots), dup_bind_keys=dup_keys)
    out = []
    for book, ch, vs, pos, eng, label, xh, sb, fh, gf in slots:
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
                    "slot_name": _slot_name(label), "greek_form": gf or "",
                    "class": "", "printed_as": "", "stored_heads": "",
                    "_bk": bk, "_nm": nm, "_bases": bases})
    _attach_kjv(conn, have, out)
    for r in out:
        r["kjv_backed"] = "yes" if r["kjv_h"] and r["kjv_h"] in r["_bases"] else "no"
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


def _line(r, cols=COLS):
    return "\t".join(str(r[c]) for c in cols)


def _write(path, rows, cols):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write(_line(r, cols) + "\n")


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    db = next((a for i, a in enumerate(argv[1:], 1)
               if not a.startswith("--") and argv[i - 1] not in ("--tsv", "--tipnr")), None)
    if not db:
        print(__doc__)
        return 3
    # Default OUTSIDE the repo folder (bible.db sits in the PA checkout).
    tsv = argv[argv.index("--tsv") + 1] if "--tsv" in argv else \
        os.path.expanduser("~/audit_xref_vs_binding.tsv")
    root, ext = os.path.splitext(tsv)
    tsv_classed = f"{root}_classed{ext or '.tsv'}"
    tipnr_path = argv[argv.index("--tipnr") + 1] if "--tipnr" in argv else TIPNR_PINNED
    if not os.path.isfile(tipnr_path):
        print(f"HALT: TIPNR file not found: {tipnr_path}")
        return 3
    conn = sqlite3.connect(f"file:{os.path.abspath(db)}?mode=ro", uri=True)
    missing = [t for t in REQUIRED if t not in _tables(conn)]
    if missing:
        print(f"HALT: required table(s) absent: {', '.join(missing)}")
        return 3

    rows, stats = find_mismatches(conn)
    with open(tipnr_path, encoding="utf-8-sig") as f:
        parsed = er.parse_tipnr(f.read().splitlines())
    db_heads, db_bases = {}, {}
    for u, h, b in conn.execute("SELECT uniq, head, bases FROM tipnr_entities"):
        db_heads[u], db_bases[u] = h or "", _bases(b)
    tip = Tipnr(parsed, db_heads, db_bases)
    for r in rows:
        r["class"] = classify(r, tip)

    print(f"[READ-ONLY] audit_xref_vs_binding -> {db}")
    print(f"TIPNR: {tipnr_path} ({len(parsed):,} entities)\n")
    print("== CONTROL (must both be found, in class 4, or the count is VOID) ==")
    ok = True
    for book, ch, vs, h, uniq in CONTROLS:
        hit = [r for r in rows if (r["book"], r["chapter"], r["verse"], r["stored_h"],
                                   r["entity"]) == (book, ch, vs, h, uniq)]
        if not hit:
            ok = False
            print(f"  MISSING {book} {ch}:{vs} stored {h} bound {uniq}")
            # say what the binding table holds there, so a miss can be diagnosed
            for b in conn.execute("SELECT name, entity_uniq, kind, render FROM pn_binding "
                                  "WHERE book=? AND chapter=? AND verse=?",
                                  (er.book_num(book), ch, vs)):
                print(f"          binding there: name={b[0]!r} entity={b[1]} "
                      f"kind={b[2]} render={b[3]}")
        for r in hit:
            if r["class"] == SAME:
                print(f"  FOUND   [{r['class']}] " + _line(r))
            else:
                ok = False
                print(f"  MISCLASSED [{r['class']}, want {SAME}] " + _line(r))
    conn.close()
    if not ok:
        print("\nCONTROL FAILED — the detector did not fire (or class) correctly on a "
              "known positive. COUNT VOID. Nothing below is trustworthy.")

    print("\n== ALL MISMATCHED SLOTS ==")
    print("\t".join(CLASSED_COLS))
    for r in rows:
        print(_line(r, CLASSED_COLS))
    _write(tsv, rows, COLS)
    _write(tsv_classed, rows, CLASSED_COLS)

    pairs = Counter((r["stored_h"], r["entity"]) for r in rows)
    print("\n== SUMMARY ==")
    print(f"  slots with a stored Hebrew number : {stats['slots_with_h']:,}")
    print(f"    with a binding (render=1)       : {stats['bound']:,}")
    print(f"      agree (stored in bases)       : {stats['agree']:,}")
    print(f"      bound entity not in tipnr_entities: {stats['entity_missing']:,}")
    print(f"      MISMATCHED                    : {stats['mismatch']:,}")
    print(f"    no binding                      : {stats['no_binding']:,}"
          "   (known blind spot — not checked)")
    print(f"  binding keys with two entities    : {stats['dup_bind_keys']:,}")
    print(f"  distinct stored numbers           : {len({r['stored_h'] for r in rows}):,}")
    print(f"  distinct entities                 : {len({r['entity'] for r in rows}):,}")
    how = Counter(r["kjv_how"] for r in rows)
    print("  KJV number resolved by            : " +
          ", ".join(f"{k} {v:,}" for k, v in sorted(how.items())))
    print(f"  KJV number is one of the entity's : "
          f"{sum(1 for r in rows if r['kjv_backed'] == 'yes'):,}")

    print("\n  per class (slots · KJV-backed · numbers · entities):")
    for c in CLASSES:
        cr = [r for r in rows if r["class"] == c]
        kb = sum(1 for r in cr if r["kjv_backed"] == "yes")
        rate = f"{kb:,}/{len(cr):,}" + (f" ({100 * kb // len(cr)}%)" if cr else "")
        extra = ""
        if c == COMPOUND and cr:
            pa = Counter(r["printed_as"] for r in cr)
            extra = "   printed as: " + ", ".join(f"{k} {v:,}" for k, v in sorted(pa.items()))
        print(f"    {c:28} {len(cr):5,} · KJV-backed {rate:14} · "
              f"{len({r['stored_h'] for r in cr}):3,} · {len({r['entity'] for r in cr}):3,}{extra}")
    total = sum(1 for r in rows if r["class"] in CLASSES)
    print(f"    {'(every row classed once)':28} {total:5,} of {len(rows):,}")

    print("  top 20 (stored number -> bound entity) by slots:")
    for (h, u), n in pairs.most_common(20):
        cl = next(r["class"] for r in rows if (r["stored_h"], r["entity"]) == (h, u))
        print(f"    {n:5,}  {h:7} -> {u}  [{rows_bases(rows, u)}]  {cl}")

    others = [r for r in rows if r["class"] == OTHER]
    print(f"\n== CLASS 7 OTHER — all {len(others):,} in full ==")
    if others:
        print("\t".join(CLASSED_COLS))
        for r in others:
            print(_line(r, CLASSED_COLS))

    print(f"\nlists written to {tsv}\n             and {tsv_classed}")
    print("CONTROL OK — count valid." if ok else "CONTROL FAILED — COUNT VOID.")
    return 0 if ok else 2


def rows_bases(rows, uniq):
    for r in rows:
        if r["entity"] == uniq:
            return r["entity_bases"]
    return ""


if __name__ == "__main__":
    sys.exit(main(sys.argv))
