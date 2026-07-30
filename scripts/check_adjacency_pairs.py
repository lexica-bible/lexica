#!/usr/bin/env python3
"""check_adjacency_pairs.py — LOCAL cross-check for rulings batch 3 (adjacency
compounds). Consumes the PA dump from dump_adjacency_ctx.py + the pinned
tipnr/TIPNR.txt. Applies the pre-registered bar (TICKET_supplied_subject_binds.md,
approved 2026-07-30) exactly:

  CLEAN  = every occurrence of the census name in the verse sits in a text-order
           token pair that equals a TIPNR "combined" form's own two tokens
           (same entity for all occurrences), AND that entity's full TIPNR
           reference union covers the verse.
  RESIDUE = anything needing looser matching (no adjacent pair, pair not an
           attested combined form, refs don't cover, occurrences disagree,
           no verse/token match). Every residue line is NAMED with its reason.

Outputs: ready-to-append TSV rows for pn_hand_rulings.tsv, the named residue,
and the chip-merge candidate list (partner token is itself a PN slot).

Usage: python scripts/check_adjacency_pairs.py <adjacency_ctx.txt>
"""
import os, re, sys, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import entity_resolution as er


def norm_tok(t):
    return re.sub(r"^[^A-Za-z]+|[^A-Za-z]+$", "", t).lower()


# ── parse pinned TIPNR: combined forms + per-entity ref union ────────────────
pair_index = {}        # (tok1, tok2) -> set of entity uniqs
entity_refs = collections.defaultdict(set)   # uniq -> {(booknum, ch, vs)}
cur_uniq = None
for ln in open(os.path.join(HERE, "tipnr", "TIPNR.txt"), encoding="utf-8"):
    parts = ln.rstrip("\n").split("\t")
    if not parts[0].startswith("–"):
        # top-level entity record: uniq=code before '=' in column 0
        m = re.match(r"^([^\t=]+@[^\t=]+)=", parts[0])
        cur_uniq = m.group(1).strip() if m else None
        continue
    if cur_uniq is None or len(parts) < 6:
        continue
    sig = parts[0].lstrip("–").strip().lower()
    unique = parts[1].strip()
    uniq = unique.split("|")[1].strip() if "|" in unique else cur_uniq
    for tok in parts[5].split(";"):
        ref = er.parse_ref(tok)
        if ref:
            entity_refs[uniq].add(ref)
    if "combined" in sig and "@" in unique:
        # form|Entity@... (alias form) OR Form@... (the compound IS the head)
        form = unique.split("|")[0].split("@")[0].strip()
        toks = [norm_tok(t) for t in re.split(r"[-\s/_]+", form) if norm_tok(t)]
        if len(toks) == 2:
            pair_index.setdefault(tuple(toks), set()).add(uniq)

print(f"TIPNR combined two-token forms indexed: {len(pair_index)} "
      f"(entities with refs: {len(entity_refs)})\n")

# ── walk the dump, grouped by slot ───────────────────────────────────────────
slots = collections.defaultdict(list)
for ln in open(sys.argv[1], encoding="utf-8"):
    if ln.startswith("#") or not ln.strip():
        continue
    f = ln.rstrip("\n").split("|")
    slots[(f[0], f[1], f[2], f[3])].append(f[4:])

clean, residue, chip_merge = [], [], []
for (nm, bk, ch, vs), occs in sorted(slots.items()):
    key = f"{nm} {bk} {ch}:{vs}"
    if occs[0][0] in ("NO-VERSE-ROW", "NO-TOKEN-MATCH"):
        residue.append((key, occs[0][0]))
        continue
    per_occ = []   # per occurrence: set of (uniq, partner, partner_is_pn) matches
    for occ in occs:
        _, prev, nxt, prev_pn, nxt_pn = occ
        m = set()
        for uniqs, partner, pn in ((pair_index.get((prev, nm)), prev, prev_pn),
                                   (pair_index.get((nm, nxt)), nxt, nxt_pn)):
            for u in (uniqs or ()):
                m.add((u, partner, pn == "1"))
        per_occ.append(m)
    common = set.intersection(*[{u for u, _, _ in m} for m in per_occ]) if all(per_occ) else set()
    if not common:
        why = ("no adjacent attested-compound pair" if not any(per_occ)
               else "occurrences disagree on entity / partial match")
        residue.append((key, why + f" (ctx: {['|'.join(o) for o in occs]})"))
        continue
    ref = (er.book_num(bk), int(ch), int(vs))
    covered = [u for u in common if ref in entity_refs.get(u, ())]
    if not covered:
        residue.append((key, f"pair attested ({sorted(common)}) but entity refs "
                             f"do NOT cover the verse"))
        continue
    if len(covered) > 1:
        residue.append((key, f"MULTIPLE covering entities {sorted(covered)} — hand look"))
        continue
    u = covered[0]
    partners = {(p, pn) for m in per_occ for (uu, p, pn) in m if uu == u}
    for p, pn in partners:
        if p == nm:
            residue.append((key, "partner token equals the slot name — key clash"))
            break
    else:
        partner_txt = ", ".join(p for p, _ in sorted(partners))
        clean.append((nm, bk, ch, vs, u, partner_txt))
        for p, pn in partners:
            if pn:
                chip_merge.append(f"{key}: partner '{p}' is a PN slot (chip-merge candidate)")

print(f"CLEAN (bar met): {len(clean)} | RESIDUE (named): {len(residue)} "
      f"| chip-merge candidates: {len(chip_merge)}\n")
print("── TSV rows (append to pn_hand_rulings.tsv after JP checkpoint) ──")
for nm, bk, ch, vs, u, partner in clean:
    print(f"{nm}\t{bk}\t{ch}\t{vs}\t{u}\tadjacency-compound\t"
          f"verse text reads '{partner}'+'{nm}' adjacent in text order = TIPNR "
          f"attested combined form of {u}; entity refs cover the verse\t")
print("\n── NAMED RESIDUE (not the batch) ──")
for k, why in residue:
    print(f"  {k}: {why}")
print("\n── CHIP-MERGE CANDIDATES (both tokens PN) ──")
for c in chip_merge:
    print(f"  {c}")
