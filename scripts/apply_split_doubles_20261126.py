#!/usr/bin/env python3
"""apply_split_doubles_20261126.py - split double rows (DESIGN 9.280): one Greek word, one numbered row.

The rows are docs/handoffs/drafts/SPLIT_DOUBLES/rows_split_doubles_20261125.tsv (sha-pinned; shape, keeper
rule and file accepted by DESIGN 9.280 (1)-(2); no write cleared by it). For each of the 506 words:
  - every row of the word except the kept one: strongs and strongs_base -> '' (english, english_head,
    greek_pos, bracket_id untouched), and each of those two cells registered as an abp_corrections row
    (applied_at 'ingest', ledger SPLIT-DOUBLE), so a words rebuild re-applies it at finish step 7;
  - the printed form goes with the number: a row that loses its number loses its abp_surface row; when the
    kept row has none, a new row puts the same form there (its Latin spelling = build_abp_translit's rule on
    the kept row's dictionary word, which is the same word, so the spelling the dropped row carried).
The 3 held words (polarity B) are not written.

  python3 scripts/apply_split_doubles_20261126.py check   READ-ONLY: every before-value + every gate
  python3 scripts/apply_split_doubles_20261126.py apply   the write: one all-or-nothing step
  python3 scripts/apply_split_doubles_20261126.py after   READ-ONLY: every after-value + every gate
  python3 scripts/apply_split_doubles_20261126.py undo    the way back, from the before-values
  add --db <copy> to run any mode on a copy (the re-measure, DESIGN 9.280 (e)); live is the default.

apply and undo each: refuse 12:30-14:30 UTC; take the write hold; re-read every starting value; write; read
every result back; count the changes; check that no other words number cell and no other abp_surface row
moved; save only if all of that held.

What check prints for the ruling chat (DESIGN 9.280 (c), (d)): 2Sa 3:35 @5 as live holds it (its
before-value came from the build, not a live read); every existing active correction and every lane-3 op on
a written (verse, position) - both must be 0; the frozen fill slots inside the written words (information:
the fill is re-frozen after this write, its own package).
What the write moves, each read by `after`: abp_corrections_active 406 -> 1,430 (members
abp_corrections_active_live_20261124.txt -> ..._live_20261126.txt); abp_surface 395,018 -> 394,553 (the
health floor moves in its own commit after `after` passes, the same day, before the 13:30 UTC nightly;
DESIGN 9.280 (a)). Not moved, read by check and after: words 626,309 / verses 31,237, every English cell,
the word-order check (601 punct members), the phrase-gloss gate (<= 747; the figure is printed).
The pins in cert_invariants.py and health_check.py move in their own commit AFTER `after` passes.
"""
import argparse
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import apply_bible_text_batch_20261122 as B       # noqa: E402  (_rows, _ref, _one, sha, Stop, check_members, ...)

Stop = B.Stop
ROWS = ROOT / "docs" / "handoffs" / "drafts" / "SPLIT_DOUBLES" / "rows_split_doubles_20261125.tsv"
ROWS_SHA = "c95b2722e33bee20aa2bb3beb413bb70c255beaed8a2f670dbc2c49321d177e0"      # DESIGN 9.280 (2) file + the 2Sa 3:35 @5 form line
FIX = ROOT / "tests" / "fixtures" / "corrections"
ACTIVE_OLD = FIX / "abp_corrections_active_live_20261124.txt"
ACTIVE_OLD_SHA = "1f5cec8fbae5b8326c289b8d272a912fcff77f29375c9368d76ac825b42b54f0"   # the 406 on live since 11/26
ACTIVE_NEW = FIX / "abp_corrections_active_live_20261126.txt"
ACTIVE_NEW_SHA = "19966d016cfec5266ae44e7304859771800c43715daaf42ae2f7e23a3f6cc3bf"   # 406 + 1,024 (member_lines)
FILL = ROOT / "tests" / "fixtures" / "rebuild_trap" / "abp_surface_fill_20261126.tsv"
FILL_SHA = None   # restore_surface_fill.SNAPSHOT_SHA256, read from there (never a copy)
PUNCT, PUNCT_SHA, PUNCT_N = B.PUNCT_NEW, B.PUNCT_NEW_SHA, B.PUNCT_AFTER          # 601, frozen 11/22
ACTIVE_BEFORE = 406
WORDS_N, SURFACE_N, ROWS_N, HELD_N = 506, (482, 17), 512, 3
SURFACE_BEFORE = 395018
SURFACE_AFTER = SURFACE_BEFORE - SURFACE_N[0] + SURFACE_N[1]                     # 394,553
LEDGER = "SPLIT-DOUBLE"
CREATED = "2026-11-26"
REASON = ("split double row, DESIGN 9.280: one Greek word cut into rows by the build; "
          "the number stays on the kept row @{keep} '{keep_eng}'")
EXTRA = {("2Sa", 3, 35, 5)}          # before-value from the build, not a live read (DESIGN 9.280 (c))
_QUOTED = re.compile(r"^'(.*)'(?: - NOT READ ON LIVE.*)?$")


# ── the plan ────────────────────────────────────────────────────────────────────
def load_plan(rows_path=ROWS, rows_sha=ROWS_SHA):
    """-> list of words: {key3, keep, keep_eng, number, base, strip: [{pos, eng, form}], move: form|None}."""
    got = B.sha(rows_path)
    if rows_sha and got != rows_sha:
        raise Stop(f"{Path(rows_path).name}: sha {got}, pinned {rows_sha}")
    words, held = {}, 0
    for r in B._rows(rows_path):
        cell, n = r["cell"], int(r["word"])
        if cell == "held":
            held += 1
            continue
        key3 = B._ref(r["verse"])
        w = words.setdefault(n, {"key3": key3, "strip": {}, "move": None, "keep": None})
        if w["key3"] != key3:
            raise Stop(f"word {n}: two verses")
        pos = int(r["position"])
        if cell == "keeps":
            if w["keep"] is not None or r["before"] != r["after"]:
                raise Stop(f"word {n}: a second or changed keeps line")
            m = re.search(r"keeps the number: @(\d+) '(.*)' \((auto|auto-last|hand)\)$", r["read"])
            if not m or int(m.group(1)) != pos:
                raise Stop(f"word {n}: cannot read the keeps line")
            w.update(keep=pos, keep_eng=m.group(2), number=r["before"])
        elif cell in ("words.strongs", "words.strongs_base"):
            if r["after"] != "":
                raise Stop(f"word {n} @{pos}: {cell} after-value {r['after']!r}, expected ''")
            m = _QUOTED.match(r["read"])
            if not m:
                raise Stop(f"word {n} @{pos}: cannot read the English in {r['read']!r}")
            s = w["strip"].setdefault(pos, {"pos": pos, "eng": m.group(1), "form": None})
            if s["eng"] != m.group(1):
                raise Stop(f"word {n} @{pos}: two English values")
            s[cell.split(".")[1]] = r["before"]
        elif cell == "abp_surface.form":
            if r["before"] and not r["after"]:
                w["strip"].setdefault(pos, {"pos": pos, "eng": None, "form": None})["form"] = r["before"]
            elif r["after"] and not r["before"]:
                if w["move"] is not None:
                    raise Stop(f"word {n}: two moved forms")
                w["move"] = (pos, r["after"])
            else:
                raise Stop(f"word {n} @{pos}: a form line that is neither a removal nor an addition")
        else:
            raise Stop(f"word {n}: unknown cell {cell!r}")
    plan = []
    for n, w in sorted(words.items()):
        if w["keep"] is None:
            raise Stop(f"word {n}: no keeps line")
        if w["move"] and w["move"][0] != w["keep"]:
            raise Stop(f"word {n}: the moved form does not land on the kept row")
        if w["keep"] in w["strip"]:
            raise Stop(f"word {n}: the kept row is also stripped")
        for s in w["strip"].values():
            if s.get("strongs") != w["number"] or s.get("strongs_base") != "G" + w["number"].split(".")[0]:
                raise Stop(f"word {n} @{s['pos']}: number cells {s.get('strongs')!r} / {s.get('strongs_base')!r} "
                           f"do not match the kept number {w['number']}")
        if w["move"] and w["move"][1] not in {s["form"] for s in w["strip"].values()}:
            raise Stop(f"word {n}: the moved form is not a form the word's rows carry")
        w["strip"] = [w["strip"][p] for p in sorted(w["strip"])]
        w["n"] = n
        plan.append(w)
    nrows = sum(len(w["strip"]) for w in plan)
    nform = sum(1 for w in plan for s in w["strip"] if s["form"])
    nmove = sum(1 for w in plan if w["move"])
    cells = [(w["key3"], s["pos"]) for w in plan for s in w["strip"]] + [(w["key3"], w["keep"]) for w in plan]
    if len(cells) != len(set(cells)):
        raise Stop("a (verse, position) appears twice in the plan")
    if (len(plan), (nform, nmove), nrows, held) != (WORDS_N, SURFACE_N, ROWS_N, HELD_N) and rows_sha:
        raise Stop(f"plan is {len(plan)} words / {nform} forms off, {nmove} moved / {nrows} rows / {held} held; "
                   f"pinned {WORDS_N} / {SURFACE_N} / {ROWS_N} / {HELD_N}")
    return plan


def new_rows(plan):
    """The abp_corrections rows: two per stripped row (strongs, strongs_base), source = today's cell."""
    out = []
    for w in plan:
        why = REASON.format(keep=w["keep"], keep_eng=w["keep_eng"])
        for s in w["strip"]:
            out.append((*w["key3"], s["pos"], "strongs", s["strongs"], "", why))
            out.append((*w["key3"], s["pos"], "strongs_base", s["strongs_base"], "", why))
    return out


def member_lines(conn_rows, plan):
    """The active member list text (B.active_sha's format) after the write."""
    rows = list(conn_rows) + [(b, c, v, p, f, LEDGER) for b, c, v, p, f, _s, _c, _r in new_rows(plan)]
    rows = sorted(rows, key=lambda x: (x[0], int(x[1]), int(x[2]), int(x[3]), x[4]))
    return "".join("\t".join(str(c) for c in r) + "\n" for r in rows)


# ── reads ───────────────────────────────────────────────────────────────────────
def verse_ids(conn, plan):
    want = {w["key3"] for w in plan}
    got = {}
    for vid, b, c, v in conn.execute("SELECT id, book, chapter, verse FROM verses"):
        if (b, c, v) in want:
            if (b, c, v) in got:
                raise Stop(f"verse {(b, c, v)}: two rows")
            got[(b, c, v)] = vid
    miss = want - set(got)
    if miss:
        raise Stop(f"{len(miss)} verse(s) not found, e.g. {sorted(miss)[:3]}")
    return got


def word_cells(conn, vids):
    """(verse_id, position) -> (english, strongs, strongs_base) for the verses of the plan."""
    out = {}
    q = ",".join("?" * len(vids))
    for vid, pos, e, s, sb in conn.execute(
            f"SELECT verse_id, position, english, strongs, strongs_base FROM words WHERE verse_id IN ({q})", list(vids)):
        if (vid, pos) in out:
            raise Stop(f"words ({vid}, {pos}): two rows")
        out[(vid, pos)] = (e, s, sb)
    return out


def surface_cells(conn, vids):
    q = ",".join("?" * len(vids))
    out = {}
    for vid, pos, f, t in conn.execute(
            f"SELECT verse_id, position, form, translit FROM abp_surface WHERE verse_id IN ({q})", list(vids)):
        if (vid, pos) in out:
            raise Stop(f"abp_surface ({vid}, {pos}): two rows")
        out[(vid, pos)] = (f, t)
    return out


def verify(conn, plan, side):
    """Every planned cell must hold its `side` value. Returns the problem list."""
    bad = []
    try:
        vid = verse_ids(conn, plan)
        wc = word_cells(conn, set(vid.values()))
        sc = surface_cells(conn, set(vid.values()))
        for w in plan:
            v = vid[w["key3"]]
            base = "G" + w["number"].split(".")[0]
            k = wc.get((v, w["keep"]))
            if k is None or (k[0], k[1], k[2]) != (w["keep_eng"], w["number"], base):
                bad.append(f"{w['key3']} @{w['keep']} kept row: reads {k!r}, expected "
                           f"({w['keep_eng']!r}, {w['number']!r}, {base!r})")
            for s in w["strip"]:
                got = wc.get((v, s["pos"]))
                want = (s["strongs"], s["strongs_base"]) if side == "before" else ("", "")
                if got is None or (got[1], got[2]) != want or got[0] != s["eng"]:
                    bad.append(f"{w['key3']} @{s['pos']}: reads {got!r}, expected english {s['eng']!r} + {want!r}")
                f = sc.get((v, s["pos"]))
                if side == "before":
                    if (f[0] if f else None) != s["form"]:
                        bad.append(f"{w['key3']} @{s['pos']} form: reads {f!r}, expected {s['form']!r}"
                                   + (" (no row)" if not s["form"] else ""))
                elif f is not None:
                    bad.append(f"{w['key3']} @{s['pos']} form: reads {f!r}, expected no row")
            kf = sc.get((v, w["keep"]))
            if w["move"]:
                want = None if side == "before" else w["move"][1]
                if (kf[0] if kf else None) != want:
                    bad.append(f"{w['key3']} @{w['keep']} kept row form: reads {kf!r}, expected "
                               f"{'no row' if want is None else repr(want)}")
        n = conn.execute("SELECT count(*) FROM abp_corrections WHERE status='active' AND applied_at='ingest'").fetchone()[0]
        want_n = ACTIVE_BEFORE if side == "before" else ACTIVE_BEFORE + len(new_rows(plan))
        if n != want_n:
            bad.append(f"active correction rows: {n}, expected {want_n}")
        mine = conn.execute("SELECT count(*) FROM abp_corrections WHERE ledger_ref=?", (LEDGER,)).fetchone()[0]
        if mine != (0 if side == "before" else len(new_rows(plan))):
            bad.append(f"{LEDGER} rows: {mine}")
        if side == "after":
            have = {(b, c, v, p, f): (s, cv, st, ap) for b, c, v, p, f, s, cv, st, ap in conn.execute(
                "SELECT book, chapter, verse, position, field, source_value, corrected_value, status, applied_at "
                "FROM abp_corrections WHERE ledger_ref=?", (LEDGER,))}
            for b, c, v, p, f, s, cv, _r in new_rows(plan):
                if have.get((b, c, v, p, f)) != (s, cv, "active", "ingest"):
                    bad.append(f"correction row {b} {c}:{v} @{p} {f}: {have.get((b, c, v, p, f))!r}")
        n = conn.execute("SELECT count(*) FROM abp_surface").fetchone()[0]
        want_n = SURFACE_BEFORE if side == "before" else SURFACE_AFTER
        if n != want_n:
            bad.append(f"abp_surface {n:,} rows, expected {want_n:,}")
    except Stop as e:
        bad.append(str(e))
    return bad


def check_structure(conn):
    trig = [r[0] for r in conn.execute("""SELECT name FROM sqlite_master WHERE type='trigger'
                                          AND tbl_name IN ('words','abp_surface','abp_corrections')""")]
    if trig:
        raise Stop(f"triggers on the written tables: {trig}")
    mode = (conn.execute("PRAGMA journal_mode").fetchone()[0] or "").lower()
    if mode != "delete":
        raise Stop(f"journal_mode is {mode!r}, must be delete")
    w, v = (conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("words", "verses"))
    if (w, v) != (B.WORDS, B.VERSES):
        raise Stop(f"words {w:,} / verses {v:,}, expected {B.WORDS:,} / {B.VERSES:,}")
    print(f"structure: no triggers on words / abp_surface / abp_corrections; journal delete; "
          f"words {w:,}; verses {v:,}")


def check_extra(conn, plan):
    """DESIGN 9.280 (c): the one row whose before-value came from the build, printed as live holds it."""
    vid = verse_ids(conn, plan)
    for key in sorted(EXTRA):
        v = vid[key[:3]]
        w = conn.execute("SELECT english, english_head, strongs, strongs_base, greek_pos, bracket_id FROM words "
                         "WHERE verse_id=? AND position=?", (v, key[3])).fetchall()
        s = conn.execute("SELECT form, translit FROM abp_surface WHERE verse_id=? AND position=?", (v, key[3])).fetchall()
        print(f"read for the ruling chat, {key[0]} {key[1]}:{key[2]} @{key[3]} (before-value from the build): "
              f"words {w!r}; abp_surface {s!r}")


def check_overlap(conn, plan):
    """DESIGN 9.280 (d): no existing correction and no lane-3 op on a written (verse, position)."""
    from lane3_spent import Lane3Ops
    written = {(*w["key3"], p) for w in plan for p in [w["keep"]] + [s["pos"] for s in w["strip"]]}
    hits = [r for r in conn.execute("SELECT book, chapter, verse, position, field, ledger_ref FROM abp_corrections "
                                     "WHERE status='active'") if (r[0], int(r[1]), int(r[2]), int(r[3])) in written]
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        ops = Lane3Ops().ops
    lane3 = sorted(k for k in ops if k in written)
    print(f"overlap: active corrections on a written (verse, position): {len(hits)} {hits[:5]}; "
          f"lane-3 ops on one: {len(lane3)} {lane3[:5]}")
    if hits or lane3:
        raise Stop("a written row already carries a correction or a lane-3 op")


def fill_note(conn, plan):
    """Information: the frozen fill's slots inside the written words (the fill is re-frozen after this write)."""
    import restore_surface_fill as rs
    if B.sha(FILL) != (FILL_SHA or rs.SNAPSHOT_SHA256):
        raise Stop(f"{FILL.name} is not the pinned frozen fill")
    keep, strip, nums = set(), set(), set()
    for w in plan:
        keep.add((*w["key3"], w["keep"]))
        strip.update((*w["key3"], s["pos"]) for s in w["strip"])
        nums.add((*w["key3"], w["number"]))
    on_strip = on_keep = same_num = 0
    for r in B._rows(FILL):
        k = (r["book"], int(r["chapter"]), int(r["verse"]), int(r["position"]))
        if k in strip:
            on_strip += 1
        elif k in keep:
            on_keep += 1
        elif (*k[:3], r["strongs"]) in nums:
            same_num += 1
    print(f"frozen fill (information; re-frozen after this write): slots on a row that loses its number {on_strip}, "
          f"on a kept row {on_keep}, elsewhere on the same number in the verse {same_num}")


def check_translit(conn, plan):
    """Each moved form's Latin spelling: the rule on the kept row's dictionary word, = the dropped row's spelling."""
    from build_abp_translit import romanize
    vid = verse_ids(conn, plan)
    out = {}
    for w in plan:
        if not w["move"]:
            continue
        v = vid[w["key3"]]
        lem = conn.execute("""SELECT COALESCE(l.lemma,'') FROM words w LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base
                              WHERE w.verse_id=? AND w.position=?""", (v, w["keep"])).fetchone()[0]
        src = [s for s in w["strip"] if s["form"] == w["move"][1]][0]
        t = conn.execute("SELECT translit FROM abp_surface WHERE verse_id=? AND position=?", (v, src["pos"])).fetchone()
        rule = romanize(w["move"][1], lem)
        if t is not None and t[0] != rule:
            raise Stop(f"{w['key3']} @{w['keep']}: the rule gives {rule!r}, the dropped row carries {t[0]!r}")
        out[w["n"]] = rule
    print(f"moved forms: {len(out)}, each Latin spelling = build_abp_translit's rule on the kept row's dictionary word")
    return out


def _gates(db):
    B.check_members(db, PUNCT, [], PUNCT_N)
    B.phrase_gloss(db)


def _pins(after=False):
    for p, want in ((PUNCT, PUNCT_SHA), (ACTIVE_OLD, ACTIVE_OLD_SHA)) + (((ACTIVE_NEW, ACTIVE_NEW_SHA),) if after else ()):
        if want is None or B.sha(p) != want:
            raise Stop(f"{p.name} is not the pinned file")


# ── modes ───────────────────────────────────────────────────────────────────────
def do_read(db, side):
    plan = load_plan()
    _pins(after=side == "after")
    conn = B._ro(db)
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        check_structure(conn)
        bad = verify(conn, plan, side)
        if bad:
            raise Stop(f"{len(bad)} {side}-value(s) differ:\n  " + "\n  ".join(bad[:60])
                       + (f"\n  ... {len(bad) - 60} more" if len(bad) > 60 else ""))
        print(f"{side}-values: {len(plan)} words, {ROWS_N} rows {'carrying' if side == 'before' else 'without'} "
              f"the number, every kept row and every English cell as planned; abp_surface "
              f"{SURFACE_BEFORE if side == 'before' else SURFACE_AFTER:,}")
        n, h = B.active_sha(conn)
        if side == "before":
            if (n, h) != (ACTIVE_BEFORE, ACTIVE_OLD_SHA):
                raise Stop(f"active row list {n} / {h} is not the pinned {ACTIVE_BEFORE}")
            check_extra(conn, plan)
            check_overlap(conn, plan)
            fill_note(conn, plan)
            check_translit(conn, plan)
        elif (n, h) != (ACTIVE_BEFORE + len(new_rows(plan)), ACTIVE_NEW_SHA):
            raise Stop(f"active row list {n} / {h} is not the new pinned list")
        import restore_surface_fill as rs
        k = len(rs.translit_would_change(conn))
        if k:
            raise Stop(f"build_abp_translit.py's rule would change {k} row(s) (expect 0)")
        print("translit rule over the whole table: 0 rows would change"
              + (" (so undo can put every dropped row's spelling back by the rule)" if side == "before" else ""))
        print(f"active corrections: {n}, member list sha {h}")
    finally:
        conn.close()
    _gates(db)
    if side == "after":
        run_cert(db)
    else:
        print(f"plan: {ROWS_N} rows lose strongs + strongs_base ({2 * ROWS_N} cells) + {2 * ROWS_N} new correction "
              f"rows ({LEDGER}) + {SURFACE_N[0]} forms removed + {SURFACE_N[1]} moved = {changes(plan)} changes")


def run_cert(db):
    import cert_invariants as C
    old = C.PINS["abp_corrections_active"]
    C.PINS["abp_corrections_active"] = ACTIVE_BEFORE + 2 * ROWS_N   # this read only; the code's pin moves after
    try:
        rc = C.run_suite(str(db))
    finally:
        C.PINS["abp_corrections_active"] = old
    if rc:
        raise Stop(f"cert_invariants did not read all green at {ACTIVE_BEFORE + 2 * ROWS_N}")


def changes(plan):
    """sqlite total_changes for the step: one per words row updated, per correction row, per abp_surface row."""
    return ROWS_N + len(new_rows(plan)) + SURFACE_N[0] + SURFACE_N[1]


def _write(conn, plan, forward, translit):
    vid = verse_ids(conn, plan)
    for w in plan:
        v = vid[w["key3"]]
        for s in w["strip"]:
            if forward:
                c = conn.execute("UPDATE words SET strongs='', strongs_base='' WHERE verse_id=? AND position=? "
                                 "AND strongs=? AND strongs_base=?", (v, s["pos"], s["strongs"], s["strongs_base"]))
            else:
                c = conn.execute("UPDATE words SET strongs=?, strongs_base=? WHERE verse_id=? AND position=? "
                                 "AND strongs='' AND strongs_base=''", (s["strongs"], s["strongs_base"], v, s["pos"]))
            if c.rowcount != 1:
                raise Stop(f"{w['key3']} @{s['pos']}: {c.rowcount} words rows written")
        for s in w["strip"]:
            if not s["form"]:
                continue
            if forward:
                c = conn.execute("DELETE FROM abp_surface WHERE verse_id=? AND position=? AND form=?",
                                 (v, s["pos"], s["form"]))
            else:
                t = translit["strip"][(w["n"], s["pos"])]
                c = conn.execute("INSERT INTO abp_surface (verse_id, position, form, translit) VALUES (?,?,?,?)",
                                 (v, s["pos"], s["form"], t))
            if c.rowcount != 1:
                raise Stop(f"{w['key3']} @{s['pos']} form: {c.rowcount} abp_surface rows written")
        if w["move"]:
            if forward:
                c = conn.execute("INSERT INTO abp_surface (verse_id, position, form, translit) VALUES (?,?,?,?)",
                                 (v, w["keep"], w["move"][1], translit["move"][w["n"]]))
            else:
                c = conn.execute("DELETE FROM abp_surface WHERE verse_id=? AND position=? AND form=?",
                                 (v, w["keep"], w["move"][1]))
            if c.rowcount != 1:
                raise Stop(f"{w['key3']} @{w['keep']} moved form: {c.rowcount} abp_surface rows written")
    for b, ch, vs, pos, fld, s, cor, why in new_rows(plan):
        if forward:
            conn.execute("""INSERT INTO abp_corrections (book, chapter, verse, position, field, source_value, corrected_value,
                            reason, ledger_ref, applied_at, status, created) VALUES (?,?,?,?,?,?,?,?,?,'ingest','active',?)""",
                         (b, ch, vs, pos, fld, s, cor, why, LEDGER, CREATED))
        else:
            c = conn.execute("""DELETE FROM abp_corrections WHERE book=? AND chapter=? AND verse=? AND position=? AND field=?
                                AND source_value=? AND corrected_value=? AND ledger_ref=? AND created=? AND status='active'""",
                             (b, ch, vs, pos, fld, s, cor, LEDGER, CREATED))
            if c.rowcount != 1:
                raise Stop(f"correction row {b} {ch}:{vs} @{pos} {fld}: {c.rowcount} rows removed")


def _snapshot(conn):
    """Every words number cell and every abp_surface row, to prove nothing outside the plan moved."""
    w = {(v, p): (s, sb) for v, p, s, sb in conn.execute("SELECT verse_id, position, strongs, strongs_base FROM words")}
    s = {(v, p): (f, t) for v, p, f, t in conn.execute("SELECT verse_id, position, form, translit FROM abp_surface")}
    return w, s


def in_window(now=None):
    now = now or datetime.now(timezone.utc)
    return (12, 30) <= (now.hour, now.minute) < (14, 30)


def do_write(db, forward):
    if in_window():
        raise Stop("12:30-14:30 UTC: not started (the nightly health check and backup)")
    plan = load_plan()
    _pins(after=True)
    src, dst = ("before", "after") if forward else ("after", "before")
    conn = sqlite3.connect(str(db), isolation_level=None)
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        check_structure(conn)
        conn.execute("BEGIN IMMEDIATE")
        try:
            bad = verify(conn, plan, src)
            if bad:
                raise Stop(f"{len(bad)} starting value(s) differ:\n  " + "\n  ".join(bad[:60]))
            vid = verse_ids(conn, plan)
            if forward:
                translit = {"move": check_translit(conn, plan)}
            else:   # the way back: each dropped row's spelling = the rule on its own (same) dictionary word
                from build_abp_translit import romanize
                lem = {w["n"]: conn.execute("""SELECT COALESCE(l.lemma,'') FROM lexicon l WHERE l.strongs_g=?""",
                                            ("G" + w["number"].split(".")[0],)).fetchone() for w in plan}
                translit = {"strip": {(w["n"], s["pos"]): romanize(s["form"], (lem[w["n"]] or ("",))[0])
                                      for w in plan for s in w["strip"] if s["form"]}}
            w0, s0 = _snapshot(conn)
            start = conn.total_changes
            _write(conn, plan, forward, translit)
            n = conn.total_changes - start
            if n != changes(plan):
                raise Stop(f"{n} changes, expected {changes(plan)}")
            bad = verify(conn, plan, dst)
            if bad:
                raise Stop(f"{len(bad)} result(s) differ:\n  " + "\n  ".join(bad[:60]))
            w1, s1 = _snapshot(conn)
            mine_w = {(vid[w["key3"]], s["pos"]) for w in plan for s in w["strip"]}
            mine_s = mine_w | {(vid[w["key3"]], w["keep"]) for w in plan if w["move"]}
            ow = [k for k in set(w0) | set(w1) if k not in mine_w and w0.get(k) != w1.get(k)]
            os_ = [k for k in set(s0) | set(s1) if k not in mine_s and s0.get(k) != s1.get(k)]
            if ow or os_:
                raise Stop(f"outside the plan: {len(ow)} words number cell(s), {len(os_)} abp_surface row(s) changed")
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()
    a, b = (SURFACE_BEFORE, SURFACE_AFTER) if forward else (SURFACE_AFTER, SURFACE_BEFORE)
    print(f"{'written' if forward else 'put back'}: {changes(plan)} changes, every result read back, nothing else "
          f"moved; abp_surface {a:,} -> {b:,}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Split double rows (DESIGN 9.280).")
    ap.add_argument("mode", choices=["check", "apply", "after", "undo"])
    ap.add_argument("--db", default=str(B.LIVE))
    a = ap.parse_args(argv)
    db = Path(a.db).expanduser()
    label = a.mode.upper()
    try:
        if not db.is_file():
            raise Stop(f"no database at {db}")
        print(f"SPLITDOUBLE {label} on {db} at {datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}")
        if a.mode in ("check", "after"):
            do_read(db, "before" if a.mode == "check" else "after")
        else:
            do_write(db, a.mode == "apply")
    except Stop as e:
        print(f"SPLITDOUBLE {label} RESULT: STOP - {e}")
        print("Nothing was saved by this step." if a.mode in ("apply", "undo") else "This step only reads.")
        return 1
    print(f"SPLITDOUBLE {label} RESULT: DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
