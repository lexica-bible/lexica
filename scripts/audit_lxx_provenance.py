#!/usr/bin/env python3
"""
audit_lxx_provenance.py — READ-ONLY census of LXX vs Koine citation provenance across the
built Lexica dictionary cards. Answers the scope question: across the built cards, how many
SENSES rest mostly or entirely on Septuagint (Greek-OT) citations vs native NT (Koine) ones?

WHY: ABP's OT half IS the Septuagint, so every OT citation under a Greek card is LXX-Greek
(rendering a Hebrew word, usually). The build feeds every Greek word a testament-balanced
spread (~half OT / half NT, availability permitting), so a both-testament word's senses can
quietly blend LXX and Koine. This tells us how widespread that is — is pneuma an outlier, or
the rule? It does NOT change anything; it only reads lexica_def and counts.

  workon bible-env
  python scripts/audit_lxx_provenance.py                 # every built card
  python scripts/audit_lxx_provenance.py --word G4151    # one word (pneuma)
  python scripts/audit_lxx_provenance.py --refs          # also list each sense's refs

Reuses the live engine's own splitter + ref regex (build_lexica_def) so a "sense" is counted
exactly the way the card shows it. Read-only: only SELECTs, never writes.
"""
import argparse, json, os, re, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lexica_def import NT_BOOKS, split_definition, _HEADLINE_RE, _REF_RE


def sense_chunks(senses_block):
    """Split the Senses prose into (headline, body) per sense, at the bold '**N. …**' markers —
    the same markers the card's glance list is built from. Each sense's grounding refs live in
    its body."""
    ms = list(_HEADLINE_RE.finditer(senses_block or ""))
    out = []
    for i, m in enumerate(ms):
        start = m.end()
        end = ms[i + 1].start() if i + 1 < len(ms) else len(senses_block)
        headline = re.sub(r"^\d+\.\s*", "", m.group(1)).strip()
        out.append((headline, senses_block[start:end]))
    return out


def classify(body):
    """(ot, nt) ref counts for a sense body, de-duped, by book testament."""
    seen, ot, nt = set(), 0, 0
    for bk, ch, vs in _REF_RE.findall(body or ""):
        key = (bk, ch, vs)
        if key in seen:
            continue
        seen.add(key)
        if bk in NT_BOOKS:
            nt += 1
        else:
            ot += 1
    return ot, nt


def verdict(ot, nt):
    if ot and not nt:
        return "ENTIRELY LXX"
    if ot > nt:
        return "mostly LXX"
    if ot == nt and ot:
        return "split"
    if nt and not ot:
        return "entirely NT"
    return "mostly NT"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"))
    ap.add_argument("--word", help="one G-number, e.g. G4151")
    ap.add_argument("--refs", action="store_true", help="list each sense's refs")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    has = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='lexica_def'"
    ).fetchone()
    if not has:
        sys.exit("lexica_def not built on this db.")

    q = "SELECT strongs, lemma, def_json FROM lexica_def"
    params = ()
    if args.word:
        sid = args.word.upper()
        if sid[:1] not in ("G", "H"):
            sid = "G" + sid
        q += " WHERE strongs = ?"
        params = (sid,)
    rows = conn.execute(q + " ORDER BY strongs", params).fetchall()
    conn.close()
    if not rows:
        sys.exit("no matching built cards.")

    tot_senses = lxx_resting = split_senses = 0
    words_with_lxx_core = []   # word leads (sense 1) on LXX

    for r in rows:
        try:
            d = json.loads(r["def_json"])
        except Exception:
            print(f"{r['strongs']}: bad def_json, skipped")
            continue
        # re-derive senses from the stored raw so this matches the card exactly
        sb = split_definition(d.get("raw", "")).get("senses_block", "") or d.get("senses_block", "")
        chunks = sense_chunks(sb)
        print(f"\n{'='*70}\n{r['strongs']}  {r['lemma']}   ({len(chunks)} senses)")
        for i, (hl, body) in enumerate(chunks, 1):
            ot, nt = classify(body)
            v = verdict(ot, nt)
            tot_senses += 1
            if v in ("ENTIRELY LXX", "mostly LXX"):
                lxx_resting += 1
                if i == 1:
                    words_with_lxx_core.append(f"{r['strongs']} {r['lemma']}")
            if v == "split":
                split_senses += 1
            flag = "  <<< LXX-resting" if v in ("ENTIRELY LXX", "mostly LXX") else ""
            print(f"   {i}. OT {ot:2d} / NT {nt:2d}  [{v}]{flag}  — {hl[:60]}")
            if args.refs:
                refs = [f"{bk} {ch}:{vs}" for bk, ch, vs in
                        dict.fromkeys(_REF_RE.findall(body))]
                print(f"        {', '.join(refs)}")

    print(f"\n{'='*70}\nTOTALS across {len(rows)} card(s):")
    print(f"   senses total:        {tot_senses}")
    print(f"   mostly/entirely LXX: {lxx_resting}  ({100*lxx_resting//max(tot_senses,1)}%)")
    print(f"   even split OT=NT:    {split_senses}")
    print(f"   cards whose LEAD sense rests on LXX: {len(words_with_lxx_core)}")
    for w in words_with_lxx_core:
        print(f"        {w}")


if __name__ == "__main__":
    main()
