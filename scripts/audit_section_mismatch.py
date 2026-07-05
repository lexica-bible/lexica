#!/usr/bin/env python3
"""
audit_section_mismatch.py — READ-ONLY detector for PN bindings whose bound TIPNR
entity is the wrong TYPE for the clicked word (Issue: Ioudas "Jews" -> person Judah).

It opens bible.db READ-ONLY and writes nothing. It flags every render=1 binding whose
bound entity is a PERSON while the clicked word is really a PEOPLE-GROUP / gentilic, plus
the supporting "the word's Strong's number is not in the entity's bases" cross-class
(split OT/NT because TIPNR's Greek bases are STEP-extended and won't match a plain ABP
Greek number — that half is noisy, shown for eyeballing only).

CERT RULE: the detector must FIRE on the known positive (Mat 2:2 Ioudas -> Judah) before
any count is trusted. If it does not, the script exits non-zero and prints LOUDLY — a
zero from a detector that can't catch the one bug we know about is worthless.

Run on PythonAnywhere:
    python3 scripts/audit_section_mismatch.py
"""
import os, re, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import entity_resolution as er

DB = next((a for a in sys.argv[1:] if not a.startswith("--")),
          "/home/appssanding720/bible-db/bible.db")

# People-group / gentilic signal on the clicked gloss. Suffix rules cover the long tail
# (-ites/-ians/-im); the curated set catches the irregulars a suffix can't (Jews, Greeks).
_PEOPLE_SUFFIX = re.compile(r"(ites?|ians?|im|eans?)$", re.I)
_PEOPLE_WORDS = {
    "jews", "jew", "greeks", "greek", "gentiles", "gentile", "egyptians", "philistines",
    "chaldeans", "romans", "hebrews", "canaanites", "moabites", "edomites", "midianites",
    "amalekites", "hittites", "amorites", "jebusites", "perizzites", "hivites",
}
def is_people_group(label):
    n = er.norm_name(label)
    return bool(n) and (n in _PEOPLE_WORDS or bool(_PEOPLE_SUFFIX.search(n)))

NT_MIN = 40   # book number: >=40 is NT


def main():
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    have = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
        "('pn_binding','tipnr_entities','words','verses')")}
    if {"pn_binding", "tipnr_entities", "words", "verses"} - have:
        print("MISSING tables — build pn_binding first (build_entity_binding.py --apply).")
        sys.exit(2)

    ent = {r["uniq"]: r for r in conn.execute(
        "SELECT uniq, section, head, bases FROM tipnr_entities")}

    # Index every proper-noun word occurrence by (booknum, ch, vs, norm_name) so a
    # binding row (keyed the same way) can recover the clicked word's number + gloss.
    has_pn = "is_pn" in {r[1] for r in conn.execute("PRAGMA table_info(words)")}
    pn_where = "w.is_pn = 1" if has_pn else "w.strongs_base = '*'"
    occ = {}
    for r in conn.execute(f"""
        SELECT v.book AS book, v.chapter AS ch, v.verse AS vs,
               COALESCE(NULLIF(w.english_head,''), w.english) AS label,
               w.strongs_base AS base
        FROM words w JOIN verses v ON v.id = w.verse_id
        WHERE {pn_where}
          AND COALESCE(NULLIF(w.english_head,''), w.english) != ''"""):
        bk = er.book_num(r["book"])
        if bk is None:
            continue
        key = (bk, r["ch"], r["vs"], er.norm_name(r["label"]))
        occ.setdefault(key, []).append((r["label"], er.norm_base(r["base"])))

    people_person = []   # CLASS A: people-group gloss bound to a PERSON entity
    num_cross_ot = []    # CLASS B(OT): word number not in entity bases (OT — should be clean)
    num_cross_nt = []    # CLASS B(NT): same, NT (noisy — extended Greek bases)

    for b in conn.execute(
        "SELECT book,chapter,verse,name,entity_uniq,kind,tier FROM pn_binding WHERE render=1"):
        e = ent.get(b["entity_uniq"])
        if not e:
            continue
        bases = set(filter(None, (e["bases"] or "").split(",")))
        words = occ.get((b["book"], b["chapter"], b["verse"], b["name"]), [])
        labels = [w[0] for w in words]
        wbases = {w[1] for w in words if w[1]}

        if e["section"] == "person" and any(is_people_group(l) for l in labels):
            people_person.append((b, e, labels))

        # number cross: the word carries a real number that the entity doesn't list
        cross = wbases and not (wbases & bases)
        if cross:
            row = (b, e, sorted(wbases), e["bases"])
            (num_cross_nt if b["book"] >= NT_MIN else num_cross_ot).append(row)

    # ── CONTROL: the known positive must be flagged ──────────────────────────
    def hit(rows):
        return any(x[0]["book"] == 40 and x[0]["chapter"] == 2 and x[0]["verse"] == 2 for x in rows)
    control_ok = hit(people_person) or hit(num_cross_nt) or hit(num_cross_ot)
    print("=" * 70)
    print("CONTROL — Mat 2:2 Ioudas -> person Judah must be flagged:",
          "FLAGGED ✓" if control_ok else "*** NOT FLAGGED — detector is blind, count untrusted ***")
    b22 = list(conn.execute(
        "SELECT * FROM pn_binding WHERE book=40 AND chapter=2 AND verse=2"))
    for r in b22:
        e = ent.get(r["entity_uniq"], {})
        print(f"   pn_binding: name={r['name']!r} -> {r['entity_uniq']!r} "
              f"section={e['section'] if e else '?'} kind={r['kind']} render={r['render']} "
              f"bases={e['bases'] if e else '?'}")
        print(f"   clicked words: {occ.get((40,2,2,r['name']), '(none matched)')}")

    def dump(title, rows, n=25):
        print("\n" + "=" * 70)
        print(f"{title}: {len(rows)}")
        for b, e, *extra in sorted(rows, key=lambda x: (x[0]['book'], x[0]['chapter'], x[0]['verse']))[:n]:
            print(f"   {b['book']:>2} {b['chapter']}:{b['verse']:<3} name={b['name']!r:20} "
                  f"-> {e['uniq']!r} ({e['section']}) kind={b['kind']}  {extra}")
        if len(rows) > n:
            print(f"   … +{len(rows)-n} more")

    dump("CLASS A — people-group gloss bound to a PERSON entity (confident-wrong)", people_person)
    dump("CLASS B(OT) — word number not in entity bases (should be near-zero if clean)", num_cross_ot)
    dump("CLASS B(NT) — word number not in entity bases (NOISY: extended Greek bases)", num_cross_nt)

    conn.close()
    if not control_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
