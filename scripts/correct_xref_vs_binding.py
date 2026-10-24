#!/usr/bin/env python3
"""correct_xref_vs_binding.py — the reviewed correction for name slots whose stored
Hebrew number is not their bound person's/place's (JP rulings 2026-10-24).

DRY RUN BY DEFAULT. Nothing writes without --apply, and --apply is not to be run
until JP has seen the dry run (ruling).

It reuses the census (scripts/audit_xref_vs_binding.py) — same slot set, same KJV
resolution, same classifier — so what is counted and what is fixed can never drift
apart. Every mismatched slot gets one decision; the first rule that fires wins:

  GUARD   KJV's number == the stored number  -> LEAVE, whatever TIPNR says
          (hard guard, before any other rule: Daniel H1840, Zep 1:1 Cushi H3570 …)
  R1      class NO-HEBREW-ENTITY (NT slots judged by binding, like OT) -> REMOVE
  R2      class PRINTED-NAME-DIFFERS and a ruled LEAVE pair -> LEAVE
          (Esther: ABP prints Αρταξέρξης; stored H783 says what ABP says)
  R3      KJV-backed (KJV's number is one of the bound entity's) and class
          COMPOUND / SAME-NAME / VARIANT / PRINTED-NAME-DIFFERS -> SWAP to KJV's
  R4      KJV gives a THIRD number (not stored, not the entity's) -> SWAP to KJV's
          (1Ki 10:4 Sheba -> H7614, Psa 87:4 Rahab -> H7294)
  R5      class OTHER -> HOLD (no ruling yet)
  R6      class VARIANT-NUMBER, not KJV-backed -> LEAVE
  R7      anything else -> HOLD ("no KJV witness" / "not KJV-backed")

NT slots: no blanket removal — judged by binding like OT (classifier run with the
NT class switched off). KJV's NT has no Hebrew numbers, so a NT slot can only be
REMOVED (R1) or HELD, never swapped.

WHAT A CHANGE WRITES (one transaction; every UPDATE must hit exactly the rows the
plan predicts, or the whole thing is rolled back):
  SWAP    pn_hebrew_xref.hebrew_base old -> new
          pn_greek_identity.hebrew_base old -> new        (the frozen copy)
          words.strongs_base old -> new  ONLY where the word itself carries the old
          number (the kept-Hebrew 'none' slots — the third copy)
  REMOVE  pn_hebrew_xref.hebrew_base -> NULL (the ROW IS KEPT, class untouched)
          pn_greek_identity.hebrew_base -> NULL
          words.strongs_base old -> '*' where the word carries it
  NOTE on REMOVE: the ruling said "delete the pn_hebrew_xref row". This keeps the
  row with an empty number instead, because (1) the next words rebuild re-creates one
  xref row per identity row (retire_hebrew_identity), so a deleted row comes back
  with an empty number anyway — the kept-empty row IS that state; and (2) the binder
  reads this row for its guard number (build_entity_binding.occ_base_parts): a
  'tipnr'-class word with NO xref row presents its new Greek number to the binder,
  which the 7/25 ruling excludes (novel binds); with the row kept and empty it
  presents '*'. JP to confirm before --apply.

DRY-RUN OUTPUT
  * CONTROL: Gen 25:15 SWAP H1908->H2316, 1Ch 1:30 SWAP H1908->H2301, Zep 1:1 Cushi
    LEAVE by the guard. Any other outcome -> exit 2, plan VOID.
  * every row it would change or hold, with before/after per copy and the rule
  * counts by decision and rule; per-class x decision
  * ABP occurrence count before/after for every Hebrew number touched, from the
    site's own count (core.h_abp_predicate); the after figure is predicted from the
    plan and, on --apply, re-read and compared
  * HIDDEN-DIVERGENCE list: every BOUND slot (agreeing ones too) where KJV's number
    and TIPNR's differ — (A) KJV's number is not one of the entity's TIPNR numbers;
    (B) the stored number is one of the entity's, but KJV picks a different one
  Lists (outside the repo): ~/correct_xref_vs_binding_plan.tsv,
  ~/correct_xref_vs_binding_divergence.tsv

--rebuild-step (rebuild copy only; lands in /rebuild-words WITH the live apply, not
before): reads the stored number from words.strongs_base alone (import_tipnr's
fresh write; the xref copy is stale there) and, on --apply, writes words only —
keyed by verse + name through the binding, never by position (the Cushi lesson), so
restore_frozen_pn then finds no drift on these slots.

Usage (PA — the site's venv, which has what core.py imports):
  ~/.virtualenvs/bible-env/bin/python scripts/correct_xref_vs_binding.py ~/bible-db/bible.db
  … --apply           (only after JP has read the dry run; copy bible.db first)
  … --rebuild-step    (rebuild copy; see above)
Exit: 0 = plan valid / applied · 1 = apply refused (a count did not match;
      nothing written) · 2 = CONTROL failed (plan VOID) · 3 = missing input.
"""
import os
import sqlite3
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))
import audit_xref_vs_binding as audit   # the census: slot set, KJV, classifier
import entity_resolution as er

SWAP, REMOVE, LEAVE, HOLD = "SWAP", "REMOVE", "LEAVE", "HOLD"
CHANGES = (SWAP, REMOVE)

# R2 — ruled LEAVE pairs (stored number, bound entity), JP 2026-10-24.
RULED_LEAVE = {("H783", "Ahasuerus@Ezr.4.6-Dan"):
               "ruled: ABP prints Artaxerxes (Αρταξέρξης) — stored H783 says what ABP says"}

# (book, chapter, verse, stored, expected decision, expected new number or None)
CONTROLS = (
    ("Gen", 25, 15, "H1908", SWAP, "H2316"),
    ("1Ch", 1, 30, "H1908", SWAP, "H2301"),
    ("Zep", 1, 1, "H3570", LEAVE, None),
)

PLAN_COLS = ("book", "chapter", "verse", "position", "english", "entity", "census_class",
             "rule_class", "decision", "rule", "stored_h", "new_h", "kjv_h", "kjv_how",
             "xref_before", "xref_after", "frozen_before", "frozen_after",
             "word_before", "word_after")
DIV_COLS = ("kind", "book", "chapter", "verse", "position", "english", "entity",
            "entity_bases", "stored_h", "kjv_h", "kjv_how", "agree")


def decide(r, rclass):
    """(decision, new number or None, rule text). First match wins (module doc)."""
    kjv, stored = r["kjv_h"], r["stored_h"]
    if kjv and kjv == stored:
        return LEAVE, None, "GUARD: KJV's number = stored number — never changed"
    if rclass == audit.NOHEB:
        return REMOVE, None, "R1 no-Hebrew entity: remove the Hebrew number"
    if rclass == audit.PRINTED and (stored, r["entity"]) in RULED_LEAVE:
        return LEAVE, None, "R2 " + RULED_LEAVE[(stored, r["entity"])]
    if r["kjv_backed"] == "yes" and rclass in (audit.COMPOUND, audit.SAME,
                                               audit.VARIANT, audit.PRINTED):
        return SWAP, kjv, f"R3 KJV-backed swap ({rclass})"
    if kjv and kjv not in r["_bases"] and rclass != audit.OTHER:
        return SWAP, kjv, "R4 KJV gives a third number"
    if rclass == audit.OTHER:
        return HOLD, None, "R5 class 7 OTHER — no ruling yet"
    if rclass == audit.VARIANT:
        return LEAVE, None, "R6 variant number, not KJV-backed — leave"
    return HOLD, None, ("R7 no KJV witness" if not kjv else "R7 not KJV-backed")


def build_plan(conn, tip, words_only=False):
    bound, stats = audit.collect_bound(conn, words_only=words_only)
    plan = []
    for r in bound:
        if r["_agree"]:
            continue
        r["census_class"] = audit.classify(r, tip)                  # as the census reports
        rclass = audit.classify(r, tip, nt_first=False)              # judged by binding
        r["rule_class"] = rclass
        dec, new, rule = decide(r, rclass)
        r["decision"], r["new_h"], r["rule"] = dec, new or "", rule
        # per-copy before/after
        word_has = r["_sb"] == r["stored_h"]
        new_word = (new if dec == SWAP else "*") if (dec in CHANGES and word_has) else None
        r["xref_before"] = "" if words_only else (r["_xh"] or "")
        r["frozen_before"] = r["_fh"] or ""
        r["word_before"] = r["_sb"]
        if dec in CHANGES and not words_only:
            after = new if dec == SWAP else "NULL"
            r["xref_after"] = after if r["_xh"] else "-"
            r["frozen_after"] = after
        else:
            r["xref_after"] = r["frozen_after"] = "-"
        r["word_after"] = new_word if new_word is not None else "-"
        # safety holds — a change whose copies don't line up is not made
        if dec in CHANGES and not words_only:
            if not r["_xh"]:
                r["decision"], r["rule"] = HOLD, "SAFETY: no pn_hebrew_xref row to change"
            elif r["_fh"] != r["stored_h"]:
                r["decision"], r["rule"] = HOLD, (f"SAFETY: frozen copy {r['_fh']!r} "
                                                  f"!= stored {r['stored_h']!r}")
        if dec in CHANGES and words_only and not word_has:
            r["decision"], r["rule"] = HOLD, "SAFETY: word does not carry the stored number"
        if r["decision"] == HOLD and dec in CHANGES:
            r["xref_after"] = r["frozen_after"] = r["word_after"] = "-"
            r["new_h"] = ""
        plan.append(r)
    return bound, plan, stats


def divergence(bound):
    out = []
    for r in bound:
        k = r["kjv_h"]
        if not k:
            continue
        if k not in r["_bases"]:
            kind = "A kjv-not-in-tipnr"
        elif r["_agree"] and k != r["stored_h"]:
            kind = "B stored-vs-kjv-within-tipnr"
        else:
            continue
        out.append(dict(r, kind=kind, agree="yes" if r["_agree"] else "no"))
    return out


def abp_count(conn, sid):
    import core   # the site's own count (needs the site venv)
    pred, params = core.h_abp_predicate(conn, sid)
    return conn.execute(f"SELECT count(*) FROM words w WHERE {pred}", params).fetchone()[0]


def predicted_counts(conn, plan):
    """{number: (before, predicted after)} for every number a change touches."""
    moves = Counter()
    for r in plan:
        if r["decision"] == SWAP:
            moves[r["stored_h"]] -= 1
            moves[r["new_h"]] += 1
        elif r["decision"] == REMOVE:
            moves[r["stored_h"]] -= 1
    return {sid: (b := abp_count(conn, sid), b + d) for sid, d in sorted(moves.items())}


def apply_plan(conn, plan, words_only):
    """One transaction; every UPDATE must hit exactly the predicted rows."""
    todo = [r for r in plan if r["decision"] in CHANGES]
    try:
        conn.execute("BEGIN")
        for r in todo:
            vid, pos, old = r["_vid"], r["position"], r["stored_h"]
            new = r["new_h"] if r["decision"] == SWAP else None
            if not words_only:
                n = conn.execute("UPDATE pn_hebrew_xref SET hebrew_base=? WHERE verse_id=? "
                                 "AND position=? AND hebrew_base=?", (new, vid, pos, old)).rowcount
                if n != 1:
                    raise RuntimeError(f"xref {r['book']} {r['chapter']}:{r['verse']}@{pos}: {n} rows")
                n = conn.execute("UPDATE pn_greek_identity SET hebrew_base=? WHERE verse_id=? "
                                 "AND position=? AND hebrew_base=?", (new, vid, pos, old)).rowcount
                if n != 1:
                    raise RuntimeError(f"identity {r['book']} {r['chapter']}:{r['verse']}@{pos}: {n} rows")
            if r["word_after"] != "-":
                n = conn.execute("UPDATE words SET strongs_base=? WHERE verse_id=? AND position=? "
                                 "AND strongs_base=?", (r["word_after"], vid, pos, old)).rowcount
                if n != 1:
                    raise RuntimeError(f"words {r['book']} {r['chapter']}:{r['verse']}@{pos}: {n} rows")
        conn.execute("COMMIT")
        return len(todo), None
    except Exception as e:
        conn.execute("ROLLBACK")
        return 0, str(e)


def _line(r, cols):
    return "\t".join(str(r.get(c, "")) for c in cols)


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
    apply_ = "--apply" in argv
    words_only = "--rebuild-step" in argv
    db = next((a for i, a in enumerate(argv[1:], 1)
               if not a.startswith("--") and argv[i - 1] not in ("--out", "--tipnr")), None)
    if not db:
        print(__doc__)
        return 3
    outdir = argv[argv.index("--out") + 1] if "--out" in argv else os.path.expanduser("~")
    tipnr_path = argv[argv.index("--tipnr") + 1] if "--tipnr" in argv else audit.TIPNR_PINNED
    if not os.path.isfile(tipnr_path):
        print(f"HALT: TIPNR file not found: {tipnr_path}")
        return 3
    if apply_:
        conn = sqlite3.connect(os.path.abspath(db), isolation_level=None)
        conn.execute("PRAGMA journal_mode=DELETE")     # never WAL on PA (hard rule)
        conn.execute("PRAGMA busy_timeout=10000")
    else:
        conn = sqlite3.connect(f"file:{os.path.abspath(db)}?mode=ro", uri=True)
    missing = [t for t in audit.REQUIRED + ("pn_greek_identity",) if t not in audit._tables(conn)]
    if missing:
        print(f"HALT: required table(s) absent: {', '.join(missing)}")
        return 3

    with open(tipnr_path, encoding="utf-8-sig") as f:
        parsed = er.parse_tipnr(f.read().splitlines())
    db_heads, db_bases = {}, {}
    for u, h, b in conn.execute("SELECT uniq, head, bases FROM tipnr_entities"):
        db_heads[u], db_bases[u] = h or "", audit._bases(b)
    tip = audit.Tipnr(parsed, db_heads, db_bases)
    bound, plan, stats = build_plan(conn, tip, words_only=words_only)

    mode = "REBUILD-STEP (words only)" if words_only else "LIVE (xref + frozen copy + word)"
    print(f"[{'APPLY' if apply_ else 'DRY RUN — nothing written'}] correct_xref_vs_binding "
          f"-> {db}\nmode: {mode}\nTIPNR: {tipnr_path} ({len(parsed):,} entities)\n")

    print("== CONTROL (must all hold, or the plan is VOID) ==")
    ok = True
    for book, ch, vs, h, want_dec, want_new in CONTROLS:
        hit = [r for r in plan if (r["book"], r["chapter"], r["verse"], r["stored_h"])
               == (book, ch, vs, h)]
        good = [r for r in hit if r["decision"] == want_dec and (r["new_h"] or None) == want_new]
        if good:
            for r in good:
                print(f"  OK    {book} {ch}:{vs} {h} -> {r['decision']} {r['new_h']}  [{r['rule']}]")
        else:
            ok = False
            got = ", ".join(f"{r['decision']} {r['new_h']} [{r['rule']}]" for r in hit) or "not in plan"
            print(f"  FAIL  {book} {ch}:{vs} {h}: want {want_dec} {want_new or ''}, got {got}")
    if not ok:
        print("\nCONTROL FAILED — PLAN VOID. Nothing below is trustworthy; nothing will be written.")

    print("\n== PLAN — every mismatched slot, its decision and per-copy before/after ==")
    print("\t".join(PLAN_COLS))
    for r in plan:
        print(_line(r, PLAN_COLS))
    div = divergence(bound)
    _write(os.path.join(outdir, "correct_xref_vs_binding_plan.tsv"), plan, PLAN_COLS)
    _write(os.path.join(outdir, "correct_xref_vs_binding_divergence.tsv"), div, DIV_COLS)

    print("\n== SUMMARY ==")
    print(f"  mismatched slots in plan : {len(plan):,}   (bound slots checked {stats['bound']:,};"
          f" unbound {stats['no_binding']:,} not checked — known blind spot)")
    dec = Counter(r["decision"] for r in plan)
    print("  by decision              : " + " · ".join(f"{d} {dec.get(d, 0):,}"
                                                     for d in (SWAP, REMOVE, LEAVE, HOLD)))
    print("  by rule:")
    for rule, n in sorted(Counter(r["rule"] for r in plan).items()):
        print(f"    {n:5,}  {rule}")
    print("  class (judged by binding) x decision:")
    for c in audit.CLASSES:
        cr = [r for r in plan if r["rule_class"] == c]
        if cr:
            cd = Counter(r["decision"] for r in cr)
            print(f"    {c:28} {len(cr):5,}  " +
                  " · ".join(f"{d} {cd[d]}" for d in (SWAP, REMOVE, LEAVE, HOLD) if cd[d]))
    nt = [r for r in plan if r["census_class"] == audit.NT]
    if nt:
        ntd = Counter(r["decision"] for r in nt)
        print(f"  NT slots ({len(nt)}): " + " · ".join(f"{d} {n}" for d, n in sorted(ntd.items())))
    words_n = sum(1 for r in plan if r["word_after"] != "-")
    print(f"  of the changes, slots whose WORD also carries the number (third copy): {words_n:,}")

    counts = {}
    if not words_only:
        counts = predicted_counts(conn, plan)
        print("\n  ABP occurrence count per Hebrew number touched (site's own count):")
        print("    number   before → predicted after")
        for sid, (b, a) in counts.items():
            print(f"    {sid:8} {b:6,} → {a:,}")

    kinds = Counter(r["kind"] for r in div)
    print(f"\n== HIDDEN DIVERGENCE — bound slots where KJV's number and TIPNR's differ ==")
    print("  " + " · ".join(f"{k} {n:,}" for k, n in sorted(kinds.items())) if kinds else "  none")
    top = Counter((r["kind"][0], r["entity"], r["stored_h"], r["kjv_h"]) for r in div)
    print("  top 25 (kind, entity, stored, KJV) by slots:")
    for (k, u, s, kj), n in top.most_common(25):
        print(f"    {n:5,}  {k}  {u}  stored {s}  KJV {kj}")

    holds = [r for r in plan if r["decision"] == HOLD]
    print(f"\n== HELD — all {len(holds)} (no write; each needs a ruling) ==")
    for r in holds:
        print(f"  {r['book']} {r['chapter']}:{r['verse']}@{r['position']} {r['english']!r} "
              f"{r['stored_h']} bound {r['entity']} KJV {r['kjv_h'] or '-'}  [{r['rule']}]")

    print(f"\nlists written to {os.path.join(outdir, 'correct_xref_vs_binding_plan.tsv')}"
          f"\n             and {os.path.join(outdir, 'correct_xref_vs_binding_divergence.tsv')}")
    if not ok:
        print("CONTROL FAILED — PLAN VOID.")
        return 2
    if not apply_:
        print("CONTROL OK — plan valid. DRY RUN: nothing written.")
        return 0

    n, err = apply_plan(conn, plan, words_only)
    if err:
        print(f"\nAPPLY REFUSED — rolled back, nothing written: {err}")
        return 1
    print(f"\nAPPLIED {n:,} changes in one transaction.")
    if counts:
        bad = 0
        for sid, (b, want) in counts.items():
            got = abp_count(conn, sid)
            flag = "" if got == want else "   <-- DIFFERS FROM PLAN"
            bad += got != want
            print(f"    {sid:8} {b:6,} → {got:,} (planned {want:,}){flag}")
        if bad:
            print(f"  {bad} count(s) differ from the plan — STOP and look before deploy.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
