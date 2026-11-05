#!/usr/bin/env python3
"""
eu_repair_restore_digits.py — DESIGN §9.88: the scoped repair of the edition-upgrade BUILT copy's
merge-pair (§9.73) and edge-split (§9.75) rows.

Why: A's two restores put back the OLD English on a restored row but left the feed's bracket digits,
so the restored word (the "not"+verb split, or "of" before a name) lost its place in the reading
order — gate 3's 111 word-order hits (CHECK 4, 11/5). The build is fixed at the rule
(build_words_from_abp._join_neighbour_group); this script applies THAT SAME FUNCTION to the rows
already on the built copy, so build and repair are one rule. It touches bracket_id / greek_pos only,
and only on the verses named in the frozen merge-pair / edge-split lists.

MODES (the copy path is explicit; the live path ~/bible-db/bible.db is refused in every mode):
  --dry-run COPY --out PLAN.tsv [--live LIVE]
        read-only. For every listed verse, in the build's order (merge pairs, then edge splits),
        runs the rule over the copy's rows and writes every cell whose digits would change to
        PLAN.tsv (role: restored = the restored row itself, shifted = a group member moved up one).
        With --live (opened read-only) each cell also shows live's digits, and the "item-2" set
        (CHECK 4: a restored-list cell where live has a digit and the copy has none) is reported:
        how many are in the plan, and every one that is NOT.
  --apply COPY --rollback ROLLBACK --plan PLAN.tsv
        writes the plan on the COPY. Refuses unless ROLLBACK exists and is byte-identical to COPY,
        and the plan recomputed now is byte-identical to PLAN.tsv (the dry run is the figure).
        Receipt: plan cells matching their "before" digits (must be all), then "after" (must be
        all), and a digest of (id, greek_pos, bracket_id) over every OTHER words row, before and
        after (must be equal) — nothing outside the plan moves.
  --verify COPY --plan PLAN.tsv [--residue "Ref,Ref,..."]
        read-only, after --apply. v2 reassembly vs verses.text for every verse in the plan, one
        line each, plus a count over all listed verses; then each --residue verse printed in full
        (rows vs text, the audit's own print_verse).

Summary lines (grep these labels): "RESTORE-DIGITS PLAN:", "RESTORE-DIGITS APPLY:",
"RESTORE-DIGITS VERIFY:". Exit 0 = done; 1 = STOP (reason printed).
"""
import argparse
import collections
import csv
import hashlib
import io
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_words_from_abp as B                                    # noqa: E402  (the ONE rule)
from abp_app_feed import verify_sidecar                             # noqa: E402
from audit_abp_app_vs_surface import BOOK_ORDER                     # noqa: E402
from audit_reassembly_diff import diff_verse_v2, print_verse        # noqa: E402

LIVE_DB = Path.home() / "bible-db" / "bible.db"
FIX = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "edition_upgrade"
MERGE_PAIRS = FIX / "merge_pairs_20261102.tsv"
EDGE_SPLITS = FIX / "edge_splits_20261102.tsv"
PLAN_HEADER = ("book", "chapter", "verse", "position", "word_id", "strongs", "english", "role",
               "before_greek_pos", "before_bracket_id", "after_greek_pos", "after_bracket_id")
_RANK = {b: i for i, b in enumerate(BOOK_ORDER)}


class Stop(Exception):
    pass


def _key(r):
    return (r["book"], int(r["chapter"]), int(r["verse"]))


def _order(keys):
    return sorted(keys, key=lambda k: (_RANK.get(k[0], 99), k[1], k[2]))


def _ref(k):
    return f"{k[0]} {k[1]}:{k[2]}"


def _bare(sb):
    """words.strongs_base as the build held it before insert (the frozen lists' form): 'G3756' -> '3756'."""
    sb = sb or ""
    return sb[1:] if sb[:1] == "G" and sb[1:2].isdigit() else sb


def _n(v):
    return "" if v is None else str(v)


def check_target(path, what="copy"):
    if not path:
        raise Stop(f"a {what} db path is required (no default)")
    p = Path(path).expanduser()
    if not p.is_file():
        raise Stop(f"{what} db not found: {p}")
    if LIVE_DB.is_file() and p.resolve() == LIVE_DB.resolve():
        raise Stop(f"refusing the LIVE db {LIVE_DB} as the {what} - this repair runs on the built copy only")
    return p


def load_pairs(merge=None, edge=None):
    """-> {verse: [(blank_pos, neighbor_pos, blank_strongs, neighbor_strongs), ...]} in the build's
    order: the verse's merge pairs (file order), then its edge splits (file order)."""
    out = collections.defaultdict(list)
    for path in (merge or MERGE_PAIRS, edge or EDGE_SPLITS):
        verify_sidecar(path)
        with open(path, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
                out[_key(r)].append((int(r["blank_pos"]), int(r["neighbor_pos"]),
                                     r["blank_strongs"], r["neighbor_strongs"]))
    return out


def _rows(con, key, schema=""):
    return con.execute(
        f"SELECT w.id, w.position, w.english, w.greek_pos, w.bracket_id, w.strongs, w.strongs_base FROM {schema}words w "
        f"JOIN {schema}verses v ON w.verse_id = v.id WHERE v.book = ? AND v.chapter = ? AND v.verse = ? "
        "ORDER BY w.position", key).fetchall()


def same_word(frozen, strongs, strongs_base):
    """Is the copy's row at a listed position still the word the frozen list names? The list holds
    the BUILD-time strongs_base (bare). Later chain steps rewrite Strong's on some rows — import_tipnr
    binds a proper noun's strongs_base '*' to its H-number and leaves `strongs` as '*'
    (import_tipnr.py:719) — so the row matches if the frozen value equals its bare strongs_base, its
    strongs, or its strongs without a dotted suffix."""
    s = strongs or ""
    return frozen in (_bare(strongs_base), s, s.split(".")[0])


def plan(con, pairs):
    """-> [plan row tuples in PLAN_HEADER order]. The rule is build_words_from_abp's own. Every listed
    position is checked first; any row that is not the listed word is named (all of them) and the
    plan STOPs before anything is computed."""
    out, bad = [], []
    for key in _order(pairs):
        rows = _rows(con, key)
        idx = {r[1]: i for i, r in enumerate(rows)}
        for b, n, bs, ns in pairs[key]:
            for p, f in ((b, bs), (n, ns)):
                if p not in idx:
                    bad.append(f"{_ref(key)} p{p}: no row on the copy (list says {f})")
                elif not same_word(f, rows[idx[p]][5], rows[idx[p]][6]):
                    r = rows[idx[p]]
                    bad.append(f"{_ref(key)} p{p}: copy strongs {r[5]!r} / strongs_base {r[6]!r} "
                               f"english {r[2]!r} - list says {f}")
    if bad:
        for line in bad:
            print(f"   NOT THE LISTED WORD: {line}")
        raise Stop(f"{len(bad)} listed position(s) do not hold the listed word - named above; no plan written")
    for key in _order(pairs):
        rows = _rows(con, key)
        idx = {r[1]: i for i, r in enumerate(rows)}
        cur = [(r[1], r[2], None, r[5], r[5], r[3], r[4]) for r in rows]   # build tuple layout
        start = list(cur)
        restored = set()
        for b, n, _bs, _ns in pairs[key]:
            cur = B._join_neighbour_group(cur, idx[b], idx[n])
            restored.add(idx[b])
        for i, (s, c) in enumerate(zip(start, cur)):
            if (s[5], s[6]) != (c[5], c[6]):
                r = rows[i]
                out.append((key[0], key[1], key[2], r[1], r[0], r[5] or "", (r[2] or "").replace("\t", " "),
                            "restored" if i in restored else "shifted", s[5], s[6], c[5], c[6]))
    return out


def plan_bytes(rows):
    buf = io.StringIO(newline="")
    buf.write("\t".join(PLAN_HEADER) + "\n")
    for r in rows:
        buf.write("\t".join(_n(x) for x in r) + "\n")
    return buf.getvalue().encode("utf-8")


def load_plan(path):
    p = Path(path).expanduser()
    if not p.is_file():
        raise Stop(f"plan file not found: {p}")
    with open(p, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    return p, rows


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dry_run(copy, out, live=None):
    con = sqlite3.connect(f"file:{copy}?mode=ro", uri=True)
    try:
        pairs = load_pairs()
        rows = plan(con, pairs)
        Path(out).expanduser().write_bytes(plan_bytes(rows))
        roles = collections.Counter(r[7] for r in rows)
        verses = {r[:3] for r in rows}
        print(f"== plan: {len(rows)} cells in {len(verses)} verses (restored {roles['restored']} - shifted "
              f"{roles['shifted']}) over {len(pairs)} listed verses -> {out}")
        print("   per cell: p<position> 'english' r(estored)/s(hifted) bracket_id/greek_pos before -> after"
              " (live bracket_id/greek_pos) - the order CHECK 4 printed")
        livemap = {}
        if live:
            con.execute("ATTACH DATABASE ? AS L", (f"file:{live}?mode=ro",))
        by_verse = collections.defaultdict(list)
        for r in rows:
            by_verse[r[:3]].append(r)
        item2, in_plan = set(), {(r[0], r[1], r[2], r[3]) for r in rows}
        if live:
            for key in _order(pairs):
                lv = {x[1]: x for x in _rows(con, key, "L.")}
                cv = {x[1]: x for x in _rows(con, key)}
                for b, n, _bs, _ns in pairs[key]:
                    for p in (b, n):
                        c, l = cv.get(p), lv.get(p)
                        if c and l and c[5] == l[5]:
                            livemap[key + (p,)] = (l[3], l[4])
                            if (l[4] is not None and c[4] is None) or (l[3] is not None and c[3] is None):
                                item2.add(key + (p,))
        for key in _order(by_verse):
            cells = " ; ".join(
                f"p{r[3]} {r[6]!r} {r[7][0]} {_n(r[9]) or '-'}/{_n(r[8]) or '-'} -> {_n(r[11]) or '-'}/{_n(r[10]) or '-'}"
                + (f" (live {_n(livemap[key + (r[3],)][1]) or '-'}/{_n(livemap[key + (r[3],)][0]) or '-'})"
                   if key + (r[3],) in livemap else "")
                for r in by_verse[key])
            print(f"   {_ref(key):11} {cells}")
        if live:
            missing = _order({k[:3] for k in item2 - in_plan})
            print(f"   item-2 cells (live has a digit, copy has none, on a listed cell): {len(item2)} in "
                  f"{len({k[:3] for k in item2})} verses - in the plan {len(item2 & in_plan)} - NOT in the plan "
                  f"{len(item2 - in_plan)}" + (f": {', '.join(_ref(k[:3]) + ' p' + str(k[3]) for k in sorted(item2 - in_plan))}" if missing else ""))
            print(f"   plan cells outside the item-2 set: {len(in_plan - item2)} in {len({k[:3] for k in in_plan - item2})} verses")
        print(f"RESTORE-DIGITS PLAN: {len(rows)} cells / {len(verses)} verses - restored {roles['restored']} - "
              f"shifted {roles['shifted']} - plan sha256 {_sha(Path(out).expanduser())[:8]}")
    finally:
        con.close()


def _outside_digest(con, plan_ids):
    h = hashlib.sha256()
    n = 0
    for wid, gp, bid in con.execute("SELECT id, greek_pos, bracket_id FROM words ORDER BY id"):
        if wid in plan_ids:
            continue
        h.update(f"{wid}\t{_n(gp)}\t{_n(bid)}\n".encode())
        n += 1
    return n, h.hexdigest()


def apply(copy, rollback, plan_path):
    rb = check_target(rollback, "rollback")
    if Path(rollback).expanduser().resolve() == Path(copy).expanduser().resolve():
        raise Stop("the rollback copy and the copy are the same file")
    if _sha(copy) != _sha(rb):
        raise Stop(f"rollback {rb} is not byte-identical to {copy} - make it right before the apply")
    p, _rows_ = load_plan(plan_path)
    con = sqlite3.connect(str(copy), timeout=30)
    try:
        con.execute("PRAGMA journal_mode=DELETE")
        con.execute("PRAGMA busy_timeout=30000")
        rows = plan(con, load_pairs())
        if plan_bytes(rows) != p.read_bytes():
            raise Stop(f"the plan recomputed now differs from {p} - re-run the dry run")
        ids = {r[4] for r in rows}
        n0, d0 = _outside_digest(con, ids)
        before = sum(1 for r in rows if con.execute(
            "SELECT greek_pos IS ? AND bracket_id IS ? FROM words WHERE id = ?", (r[8], r[9], r[4])).fetchone()[0])
        if before != len(rows):
            raise Stop(f"only {before} of {len(rows)} plan cells hold their 'before' digits")
        con.executemany("UPDATE words SET greek_pos = ?, bracket_id = ? WHERE id = ?",
                        [(r[10], r[11], r[4]) for r in rows])
        con.commit()
        after = sum(1 for r in rows if con.execute(
            "SELECT greek_pos IS ? AND bracket_id IS ? FROM words WHERE id = ?", (r[10], r[11], r[4])).fetchone()[0])
        n1, d1 = _outside_digest(con, ids)
    finally:
        con.close()
    ok = after == len(rows) and (n0, d0) == (n1, d1)
    print(f"RESTORE-DIGITS APPLY: {'APPLIED' if ok else 'STOP - receipt mismatch'} {len(rows)} cells - before-match "
          f"{before}/{len(rows)} - after-match {after}/{len(rows)} - other rows {n1:,} digest "
          f"{d0[:8]} -> {d1[:8]} ({'unchanged' if (n0, d0) == (n1, d1) else 'CHANGED'})")
    if not ok:
        raise Stop("receipt mismatch - restore the rollback copy")


def verify(copy, plan_path, residue=()):
    _p, prow = load_plan(plan_path)
    con = sqlite3.connect(f"file:{copy}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        pairs = load_pairs()
        pv = _order({_key(r) for r in prow})
        res, kinds = {}, collections.Counter()
        for key in _order(pairs):
            v = con.execute("SELECT id, text FROM verses WHERE book = ? AND chapter = ? AND verse = ?", key).fetchone()
            words = [dict(r) for r in con.execute(
                "SELECT english, bracket_id, greek_pos, position FROM words WHERE verse_id = ? ORDER BY position",
                (v["id"],))]
            d = diff_verse_v2(words, v["text"])
            res[key] = d
            kinds["clean" if not d else d["klass"]] += 1
        print(f"== per-verse v2 vs verses.text, the {len(pv)} plan verses")
        for key in pv:
            d = res[key]
            print(f"   {_ref(key):11} " + ("clean" if not d else f"{d['klass']}  " + " ; ".join(d.get("ops", []))))
        wo = [k for k in _order(pairs) if res[k] and res[k]["klass"] == "word-order"]
        print(f"   all {len(pairs)} listed verses: {dict(kinds)}" + (f" - word-order: {', '.join(map(_ref, wo))}" if wo else ""))
        for ref in residue:
            print_verse(con, ref.strip(), v2=True)
        print(f"RESTORE-DIGITS VERIFY: plan verses {len(pv)} - clean "
              f"{sum(1 for k in pv if not res[k])} - word-order on listed verses {len(wo)}")
    finally:
        con.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description="§9.88 repair of the built copy's restored-row digits.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", metavar="COPY")
    g.add_argument("--apply", metavar="COPY")
    g.add_argument("--verify", metavar="COPY")
    ap.add_argument("--out", help="plan TSV to write (dry run)")
    ap.add_argument("--live", help="live db, opened read-only, for the item-2 comparison (dry run)")
    ap.add_argument("--rollback", help="pre-repair copy, byte-identical to COPY (apply)")
    ap.add_argument("--plan", help="the dry run's plan TSV (apply, verify)")
    ap.add_argument("--residue", default="", help="comma-separated refs to print in full (verify)")
    a = ap.parse_args(argv)
    try:
        if a.dry_run is not None:
            copy = check_target(a.dry_run)
            if not a.out:
                raise Stop("--dry-run needs --out PLAN.tsv")
            live = None
            if a.live:
                live = Path(a.live).expanduser()
                if not live.is_file():
                    raise Stop(f"live db not found: {live}")
            dry_run(copy, a.out, live)
        elif a.apply is not None:
            copy = check_target(a.apply)
            if not a.rollback or not a.plan:
                raise Stop("--apply needs --rollback and --plan")
            apply(copy, a.rollback, a.plan)
        else:
            copy = check_target(a.verify)
            if not a.plan:
                raise Stop("--verify needs --plan")
            verify(copy, a.plan, [r for r in a.residue.split(",") if r.strip()])
    except Stop as e:
        print(f"RESTORE-DIGITS STOP: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
