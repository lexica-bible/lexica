#!/usr/bin/env python3
"""
dryrun_rekey_fill.py — DRY RUN of the rebuild-trap re-key (CHARTER_rebuild_trap_fix.md §2b/§3).

Question it answers: if the words table is rebuilt, where does each of the 4,411 abp_surface fill
rows (2026-10-25) belong in the REBUILT words table? It reports placed / unplaced per reason and
per key. It WRITES NOTHING to any database: every database is opened read-only, and the only file
written is the --out report (a TSV).

REFUSES to open the live database: any path that is (or points at) ~/bible-db/bible.db, and any
file named bible.db anywhere. Every path must be given explicitly — there are no defaults.

Inputs (all explicit):
  --old      a COPY of live taken before the rebuild: holds the fill AND the old word positions
  --prefill  ~/bible.db.pre-surface-fill-20261025 (the table as the builders left it)
  --built    the rebuilt copy: /rebuild-words build + finish_rebuild.sh done, step 9 NOT run
  --csv      ~/abp_surface_fill_dryrun.csv (the approved per-row fill list — each row's class)
  --lexicon  abp_helps/analytical_lexicon.tsv
  --out      the per-slot report (TSV; must not be a database)

Keys (JP ruling 2026-10-26):
  key 2 (primary)  verse_id + full strongs + ordinal (k-th slot with that number in the verse)
  key 1 (check)    verse_id + full strongs + english (exact bytes)
  placed = key 2 finds one slot and key 1 confirms it — agree-strong (key 1 finds exactly that
  slot) or agree-weak (key 1 finds several slots, key 2's among them: the verse repeats the same
  number + English; JP ruling 2026-10-26) — and, where the row's class is Lexicon-backed, number +
  form agree at that slot (the apply's own rule; see the charter §6 on why this cannot differ from
  the old slot under these keys).

Reasons (charter §2b closed list): 1 no slot (key 2 found none) · 2 ambiguous · 3 and 4 NOT
EVALUATED here (they need the step-9 builder output, which this dry run deliberately lacks) ·
5 number + form disagree at the new slot · 6 cross-check (key 1) found none, or several that
do not include key 2's slot · 7 key conflict (both found one slot, different slots).
Every unplaced row is listed (first 100) with its old and built English.

Controls, run first; a failed control STOPS before any result is printed:
  G0   copy-of-live diff = 4,411 rows / 538 rows vs the pre-fill copy, and = the approved CSV
  V    verses identical in --old and --built (verse_id is the one key part assumed stable)
  C1   identity: re-keying --old onto itself puts every row on its own slot (key 2), with no
       unplaced reason at all — so the Lexicon witness passes every covered row at its own slot
  C2   the witness can say no: a covered form tested against a neighbouring number must fail

Run on PA only with the reviewed command sequence (CHARTER_rebuild_trap_fix.md §6).
"""
import argparse
import csv
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

LIVE = os.path.expanduser("~/bible-db/bible.db")
EXPECT_DIFF_NEW, EXPECT_DIFF_OLD = 4411, 538
N_INSERT, N_UPDATE = 3873, 538

REASONS = {
    1: "no slot (key 2 found none)",
    2: "ambiguous",
    5: "number + form disagree at the new slot",
    6: "key 1 none / several without key 2's slot",
    7: "key conflict",
}


class Stop(Exception):
    pass


def say(msg=""):
    print(msg, flush=True)


def real(path):
    return os.path.realpath(os.path.expanduser(path))


# ── the live-path gate ───────────────────────────────────────────────────────
def is_live(path, live=LIVE):
    """True when `path` is the live database, points at it (symlink / hard link / same file),
    or is any file named bible.db."""
    p = real(path)
    if os.path.basename(p) == "bible.db" or os.path.basename(os.path.expanduser(path)) == "bible.db":
        return True
    lv = real(live)
    if p == lv:
        return True
    try:
        return os.path.exists(lv) and os.path.exists(p) and os.path.samefile(p, lv)
    except OSError:
        return True                     # cannot tell -> treat as live


def check_paths(a, live=LIVE):
    dbs = {"--old": a.old, "--prefill": a.prefill, "--built": a.built}
    for flag, p in dbs.items():
        if is_live(p, live):
            raise Stop(f"{flag} {p} is the live database (or a file named bible.db) — refused. "
                       "This dry run only reads explicit COPIES.")
        if not os.path.isfile(real(p)):
            raise Stop(f"{flag} {p}: no such file")
    reals = [real(p) for p in dbs.values()]
    if len(set(reals)) != 3:
        raise Stop("--old, --prefill and --built must be three different files")
    for flag, p in (("--csv", a.csv), ("--lexicon", a.lexicon)):
        if not os.path.isfile(real(p)):
            raise Stop(f"{flag} {p}: no such file")
    out = real(a.out)
    if out.endswith(".db") or out in reals or out in (real(a.csv), real(a.lexicon)) \
            or is_live(a.out, live):
        raise Stop(f"--out {a.out} must be a new report file, not a database or an input")


def ro(path):
    """Read-only connection: SQLite refuses every write on it."""
    return sqlite3.connect(f"{Path(real(path)).as_uri()}?mode=ro", uri=True)


# ── loading ──────────────────────────────────────────────────────────────────
def surface(con):
    return {(v, p): (f, t) for v, p, f, t in con.execute(
        "SELECT verse_id, position, form, translit FROM abp_surface")}


def verses(con):
    return {i: (b, c, v) for i, b, c, v in con.execute("SELECT id, book, chapter, verse FROM verses")}


def words_for(con, vids):
    """verse_id -> [(position, strongs, english, is_pn), ...] by position, fill verses only."""
    out = defaultdict(list)
    for v, p, s, e, pn in con.execute(
            "SELECT verse_id, position, strongs, english, is_pn FROM words"):
        if v in vids:
            out[v].append((p, s, e, pn))
    for v in out:
        out[v].sort(key=lambda r: r[0])
    return out


def load_csv(path, vkey):
    """The approved fill CSV -> {(verse_id, position): row} for its insert/update writes."""
    from census_abp_surface_glued import NB
    writes = {}
    with open(real(path), encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["action"] not in ("insert", "update"):
                continue
            vid = vkey.get((r["book"], int(r["chapter"]), int(r["verse"])))
            if vid is None:
                raise Stop(f"CSV verse not found: {r['book']} {r['chapter']}:{r['verse']}")
            k = (vid, int(r["position"]))
            if k in writes:
                raise Stop(f"CSV lists slot {k} twice")
            r["old_form"] = r["old_form"].replace("␣", NB)     # the CSV marks NBSP as ␣
            writes[k] = r
    return writes


# ── the keys ─────────────────────────────────────────────────────────────────
def key2(old_rows, pos, new_rows):
    """-> ('one', new_pos) | ('none', None) | ('amb', None): the k-th slot carrying the same full
    strongs, k = this slot's ordinal among same-number slots in the old verse."""
    strongs = next(r[1] for r in old_rows if r[0] == pos)
    k = [r[0] for r in old_rows if r[1] == strongs].index(pos)
    cands = [r[0] for r in new_rows if r[1] == strongs]
    if k >= len(cands):
        return "none", None
    np = cands[k]
    if sum(1 for r in new_rows if r[0] == np) > 1:      # duplicate position: cannot say which row
        return "amb", None
    return "one", np


def key1(old_rows, pos, new_rows):
    """-> ('one', new_pos) | ('none', None) | ('amb', [positions]): same full strongs + English."""
    me = next(r for r in old_rows if r[0] == pos)
    cands = [r[0] for r in new_rows if r[1] == me[1] and r[2] == me[2]]
    if not cands:
        return "none", None
    if len(cands) > 1:
        return "amb", cands
    return "one", cands[0]


def decide(k2, k1):
    """-> (reason, detail); reason 0 = both keys found the same single slot."""
    (s2, p2), (s1, p1) = k2, k1
    if s2 == "amb":
        return 2, "key 2 ambiguous (duplicate position)"
    if s2 == "none":
        if s1 == "one":
            return 1, "key 2 none, key 1 one"
        if s1 == "amb":
            return 2, "key 2 none, key 1 several"
        return 1, "key 2 none, key 1 none"
    if s1 == "none":
        return 6, "key 1 none"
    if s1 == "amb":
        if p2 in p1:                    # JP ruling 2026-10-26: counts as agreement, tagged weak
            return 0, "agree-weak"
        return 6, "key 1 several, not key 2's slot"
    if p1 != p2:
        return 7, "both one slot, different"
    return 0, "agree-strong"


def rekey(fill, old_w, new_w, cls_of, lex, covered):
    """One pass over the fill slots -> list of result dicts. The Lexicon witness reads the NEW
    slot's own strongs."""
    from census_abp_surface_glued import agree
    new_strongs = {(v, r[0]): r[1] for v, rows in new_w.items() for r in rows}
    out = []
    for (vid, pos), form in sorted(fill.items()):
        old_rows, new_rows = old_w[vid], new_w.get(vid, [])
        k2, k1 = key2(old_rows, pos, new_rows), key1(old_rows, pos, new_rows)
        reason, detail = decide(k2, k1)
        cls = cls_of[(vid, pos)]
        lexres = "uncovered"
        want = covered.get(cls)
        if reason == 0 and want:
            ag = agree(lex, new_strongs.get((vid, k2[1]), ""), form)
            lexres = "pass" if ag in want else "fail"
            if lexres == "fail":
                reason, detail = 5, f"agree() -> {ag}"
        out.append(dict(vid=vid, pos=pos, cls=cls, form=form, k2=k2, k1=k1, reason=reason,
                        detail=detail, lex=lexres, new_pos=k2[1] if reason == 0 else None))
    return out


# ── main ─────────────────────────────────────────────────────────────────────
def run(a, live=LIVE):
    check_paths(a, live)
    from apply_abp_surface_fill import LEXICON_CLASSES          # the ONE class list
    from census_abp_surface_glued import Lexicon, agree         # the ONE matching rule

    say("=" * 78)
    say("dryrun_rekey_fill — READ-ONLY; writes only the --out report")
    for flag, p in (("--old", a.old), ("--prefill", a.prefill), ("--built", a.built)):
        say(f"  {flag:9} {real(p)}  ({os.path.getsize(real(p)):,} bytes)")
    say("=" * 78)
    cold, cpre, cnew = ro(a.old), ro(a.prefill), ro(a.built)
    try:
        return _run(a, cold, cpre, cnew, LEXICON_CLASSES, Lexicon, agree)
    finally:
        for c in (cold, cpre, cnew):
            c.close()


def _run(a, cold, cpre, cnew, covered, Lexicon, agree):
    # G0 — the fill = copy-of-live minus the pre-fill copy, and it equals the approved CSV
    say("G0  the fill diff")
    s_old, s_pre = surface(cold), surface(cpre)
    new_side = {k: v for k, v in s_old.items() if s_pre.get(k) != v}
    old_side = {k: v for k, v in s_pre.items() if s_old.get(k) != v}
    say(f"    old-not-in-prefill {len(new_side):,} (expect {EXPECT_DIFF_NEW:,}) · "
        f"prefill-not-in-old {len(old_side):,} (expect {EXPECT_DIFF_OLD:,})")
    if (len(new_side), len(old_side)) != (EXPECT_DIFF_NEW, EXPECT_DIFF_OLD):
        raise Stop("G0 diff counts are not the fill's — something else changed abp_surface")
    vold = verses(cold)
    vkey = {(b, c, v): i for i, (b, c, v) in vold.items()}
    writes = load_csv(a.csv, vkey)
    if set(writes) != set(new_side):
        raise Stop(f"G0 CSV writes {len(writes):,} slots, diff {len(new_side):,} "
                   f"({len(set(writes) ^ set(new_side)):,} differ)")
    bad = [k for k, w in writes.items() if w["new_form"] != new_side[k][0]]
    if bad:
        raise Stop(f"G0 {len(bad)} CSV new_form(s) differ from the stored form, e.g. {bad[:3]}")
    ins = {k for k, w in writes.items() if w["action"] == "insert"}
    upd = {k for k, w in writes.items() if w["action"] == "update"}
    if (len(ins), len(upd)) != (N_INSERT, N_UPDATE) or any(k in s_pre for k in ins) \
            or any(s_pre.get(k, ("",))[0] != writes[k]["old_form"] for k in upd):
        raise Stop("G0 insert/update split, or the update old forms, do not match the pre-fill copy")
    say(f"    PASS — {len(writes):,} = {len(ins):,} insert + {len(upd):,} update = the approved CSV")

    # V — verse ids stable between old and built
    say("V   verse table identical in --old and --built")
    vnew = verses(cnew)
    if vnew != vold:
        raise Stop(f"V  verses differ ({len(set(vnew.items()) ^ set(vold.items())):,} rows) — "
                   "verse_id is not stable across this build")
    say(f"    PASS — {len(vold):,} verses")

    fill = {k: v[0] for k, v in new_side.items()}
    vids = {v for v, _ in fill}
    old_w, new_w = words_for(cold, vids), words_for(cnew, vids)
    old_pos = {(v, r[0]): r for v, rows in old_w.items() for r in rows}
    orphans = [k for k in fill if k not in old_pos]
    if orphans:
        raise Stop(f"{len(orphans)} fill slot(s) have no word row in --old, e.g. {orphans[:3]}")
    cls_of = {k: writes[k]["cls"] for k in fill}
    say("    loading the Analytical Lexicon …")
    lex = Lexicon(real(a.lexicon))

    # C1 — identity control: old onto itself
    say("C1  identity control (re-key --old onto itself)")
    ident = rekey(fill, old_w, old_w, cls_of, lex, covered)
    k2_self = sum(1 for r in ident if r["k2"] == ("one", r["pos"]))
    hard = Counter(r["reason"] for r in ident if r["reason"])
    weak_floor = sum(1 for r in ident if r["detail"] == "agree-weak")
    say(f"    key 2 maps to itself {k2_self:,}/{len(fill):,} · any unplaced reason on identity: "
        f"{dict(hard) if hard else 0}")
    say(f"    agree-weak on identity = {weak_floor:,} (key 1 several: a verse repeats number + "
        "English — the floor agree-weak cannot go below on any build)")
    if k2_self != len(fill) or hard:
        raise Stop("C1 identity control failed — the keys or the witness do not do what they claim")
    say("    PASS")

    # C2 — the witness can say no
    say("C2  witness negative control (each covered form vs the next slot's different number)")
    tried = failed = 0
    for (vid, pos), form in fill.items():
        want = covered.get(cls_of[(vid, pos)])
        if not want:
            continue
        here = old_pos[(vid, pos)]
        nxt = [r for r in old_w[vid] if r[0] > pos and r[1] != here[1]]
        if not nxt:
            continue
        tried += 1
        if agree(lex, nxt[0][1], form) not in want:
            failed += 1
    say(f"    {failed:,} of {tried:,} covered forms FAIL against the neighbour's number")
    if tried == 0 or failed == 0:
        raise Stop("C2 the Lexicon witness never says no — it cannot be a witness")
    say("    PASS")

    # the real run
    say("\nRE-KEY  --old -> --built")
    res = rekey(fill, old_w, new_w, cls_of, lex, covered)
    placed = [r for r in res if r["reason"] == 0]
    unplaced = [r for r in res if r["reason"]]
    by_reason = Counter(r["reason"] for r in unplaced)
    say(f"  placed {len(placed):,} · unplaced {len(unplaced):,} · total {len(res):,} (must be 4,411)")
    agreement = Counter(r["detail"] for r in placed)
    say(f"    placed as agree-strong {agreement.get('agree-strong', 0):,} · "
        f"agree-weak {agreement.get('agree-weak', 0):,}")
    for n in sorted(REASONS):
        say(f"    reason {n}  {REASONS[n]:42} {by_reason.get(n, 0):,}")
    say("    reasons 3 + 4: NOT EVALUATED — they need the step-9 builder output (not run by design)")
    for (n, d), c in sorted(Counter((r["reason"], r["detail"]) for r in unplaced
                                    if r["reason"] in (1, 2, 6, 7)).items()):
        say(f"      reason {n}: {d:42} {c:,}")
    if unplaced:
        new_eng = {(v, r[0]): r[2] for v, rows in new_w.items() for r in rows}
        say(f"  UNPLACED rows (first {min(100, len(unplaced))} of {len(unplaced)}): verse · old pos · "
            "old English → built English at key 2's slot · reason")
        for r in unplaced[:100]:
            b, c, v = vold[r["vid"]]
            p2 = r["k2"][1]
            built = repr(new_eng.get((r["vid"], p2))) if p2 is not None else "(no key-2 slot)"
            say(f"    {b} {c}:{v} · pos {r['pos']} · {old_pos[(r['vid'], r['pos'])][2]!r} → "
                f"{built} (pos {p2}) · reason {r['reason']} {r['detail']} · "
                f"is_pn {old_pos[(r['vid'], r['pos'])][3]}")
    say("  per key:")
    say(f"    key 2: {dict(sorted(Counter(r['k2'][0] for r in res).items()))}")
    say(f"    key 1: {dict(sorted(Counter(r['k1'][0] for r in res).items()))}")
    matrix = Counter((r["k2"][0], r["k1"][0],
                      ("same" if r["k2"][1] == r["k1"][1] else "diff")
                      if r["k2"][0] == r["k1"][0] == "one" else "") for r in res)
    for (s2, s1, same), c in sorted(matrix.items()):
        say(f"    key 2 {s2:4} · key 1 {s1:4} {same:4}  {c:,}")
    say(f"  placed rows whose position moved: {sum(1 for r in placed if r['new_pos'] != r['pos']):,}")
    lexc = Counter(r["lex"] for r in res if r["reason"] in (0, 5))
    say(f"  Lexicon witness on candidate rows: {dict(sorted(lexc.items()))}")
    unc = Counter(r["cls"] for r in res if not covered.get(r["cls"]))
    say(f"  Lexicon-UNCOVERED group (all 4,411, by class): {sum(unc.values()):,} — "
        f"{dict(sorted(unc.items()))}")
    say(f"  unplaced on name slots (is_pn=1): "
        f"{sum(1 for r in unplaced if old_pos[(r['vid'], r['pos'])][3] == 1):,}")
    placed_ins = sum(1 for r in placed if (r["vid"], r["pos"]) in ins)
    say(f"  G1 preview: placed inserts {placed_ins:,} of {N_INSERT:,} "
        f"(G1 = 395,003 needs all {N_INSERT:,} placed and the builder chain at 391,130)")

    with open(real(a.out), "w", encoding="utf-8", newline="\n") as f:
        f.write("book\tchapter\tverse\told_position\tnew_position\tcls\taction\tis_pn\t"
                "form\tkey2\tkey1\treason\tdetail\tlexicon\tagreement\n")
        for r in res:
            b, c, v = vold[r["vid"]]
            k = (r["vid"], r["pos"])
            f.write("\t".join(str(x) for x in (
                b, c, v, r["pos"], "" if r["new_pos"] is None else r["new_pos"], r["cls"],
                writes[k]["action"], old_pos[k][3], r["form"],
                f"{r['k2'][0]}:{r['k2'][1]}", f"{r['k1'][0]}:{r['k1'][1]}",
                r["reason"] or "placed", r["detail"], r["lex"],
                r["detail"].replace("agree-", "") if not r["reason"] else "")) + "\n")
    say(f"\n  per-slot report: {real(a.out)} ({len(res):,} rows)")
    say("RESULT: DRY RUN COMPLETE — nothing written to any database")
    return 0


def main(argv=None, live=LIVE):
    ap = argparse.ArgumentParser(description="Re-key dry run for the abp_surface fill (read-only).")
    for flag in ("--old", "--prefill", "--built", "--csv", "--lexicon", "--out"):
        ap.add_argument(flag, required=True)
    a = ap.parse_args(argv)
    try:
        return run(a, live)
    except Stop as e:
        say(f"\nSTOPPED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
