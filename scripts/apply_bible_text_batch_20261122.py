#!/usr/bin/env python3
"""apply_bible_text_batch_20261122.py - the Bible-text batch (DESIGN 9.246, 9.247).

Writes the 50 cleared cells to bible.db and registers the ABP ones in abp_corrections, so the next
words rebuild re-applies them. The row list is the sha-pinned file the ruling chat cleared, plus one
sha-pinned added-row file (Joh 7:1 "him" = G846).

  python3 scripts/apply_bible_text_batch_20261122.py check   READ-ONLY: every before-value + every gate
  python3 scripts/apply_bible_text_batch_20261122.py apply   the write: one all-or-nothing database step
  python3 scripts/apply_bible_text_batch_20261122.py after   READ-ONLY: every after-value + every gate
  python3 scripts/apply_bible_text_batch_20261122.py undo    the way back, from the before-values

apply and undo each: refuse 13:00-14:30 UTC; take the write hold; re-read every starting value; write;
read every result back; count the changes (76); and save only if all of that held. Any miss = nothing
saved. No copy of the database is made: the row files hold every before-value.

What this write moves, each read by `after`:
  cert pin abp_corrections_active 375 -> 403 (members: abp_corrections_active_live_20261122.txt)
  frozen punct list 607 -> 601 (punct_members_live_20261122.txt: 6 verses leave, 4 change)
What it does not move, each read: words 626,309, verses 31,237, the phrase-gloss gate (<= 747),
and the frozen abp_surface fill (no written word slot is a fill slot).
The pin in cert_invariants.py moves in its own commit AFTER `after` passes, so the code never
claims 403 while live holds 375.
"""
import argparse
import collections
import contextlib
import csv
import hashlib
import io
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

BATCH = ROOT / "docs" / "handoffs" / "drafts" / "BIBLE_TEXT_BATCH"
CLEARED = BATCH / "rows_20261122.tsv"
CLEARED_SHA = "1f8905b5185d967abcede734061312c693fd9a52e2e286ee793d63c2717b446f"
ADDED = BATCH / "rows_added_20261122.tsv"
ADDED_SHA = "e580b703d453e11982b5abea392c0d877185ef6eeb90141b917f4e6dd055c5ba"
PUNCT_OLD = ROOT / "tests" / "fixtures" / "reassembly" / "punct_members_built_20261115.txt"
PUNCT_OLD_SHA = "0cc4d4288f7a35576b40063b5f1e1b4ff9d21642cef80f4d7bcec02f6dfa7056"
PUNCT_NEW = ROOT / "tests" / "fixtures" / "reassembly" / "punct_members_live_20261122.txt"
PUNCT_NEW_SHA = "b6b0b2e1e8d28bf7bb075e5f9fdc1086032e7b0c10e7f63f48e836202b98008e"
ACTIVE_OLD = ROOT / "tests" / "fixtures" / "corrections" / "abp_corrections_active_built_20261121.txt"
ACTIVE_OLD_SHA = "005da9f3be151340ed81624303cb8388fcfa727983feb990a0e0e6abbd633048"
ACTIVE_NEW = ROOT / "tests" / "fixtures" / "corrections" / "abp_corrections_active_live_20261122.txt"
ACTIVE_NEW_SHA = "1d727333e1656dc8417fbd1aac4cd590f1e6239e54b8277601d8fead3148a8b3"
FILL = ROOT / "tests" / "fixtures" / "rebuild_trap" / "abp_surface_fill_20261115.tsv"
FILL_SHA = "d025cc086cd7f325bafe3c89655c778f8cdc57f67ba127061a3edfd2192472ff"     # restore_surface_fill.py
ELIGIBLE = Path("~/edition_upgrade_runs/eligible_20261031.tsv").expanduser()
ELIGIBLE_SHA = "e540d34d422b86dab2fa7d28f9f86c322bad3d5ea6808f42c6a3bab64d42580f"  # DESIGN 9.160, 9.169
LIVE = Path("~/bible-db/bible.db").expanduser()

ACTIVE_BEFORE, ACTIVE_AFTER = 375, 403
PUNCT_BEFORE, PUNCT_AFTER = 607, 601
WORDS, VERSES = 626309, 31237
PHRASE_GATE = 747
CHANGES = 76     # 15 verses + 14 words + 28 new rows + 1 changed row + 18 KJV tag moves (1 off, 16 moved, 1 on)
EXISTING_PROSE = ("2Ki", 14, 28)     # already has an active prose row: changed, never doubled
KJV_BOOK, KJV_CH, KJV_VS = 43, 7, 1  # Joh 7:1 (core._KJV_BOOK_ID)
CREATED = "2026-11-22"


class Stop(Exception):
    """Any miss: nothing is saved."""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def _ref(v):
    book, cv = v.split(" ")
    ch, vs = cv.split(":")
    return book, int(ch), int(vs)


def _tag(cell, word_id):
    m = re.fullmatch(r"(\S+): (G\d+|\(none\))", cell)
    if not m:
        raise Stop(f"word {word_id}: cannot read the cell {cell!r}")
    return m.group(1), None if m.group(2) == "(none)" else m.group(2)


def load_plan():
    """The sha-pinned rows -> {prose, words, kjv}."""
    for p, want in ((CLEARED, CLEARED_SHA), (ADDED, ADDED_SHA)):
        got = sha(p)
        if got != want:
            raise Stop(f"{p.name}: sha {got}, cleared {want}")
    rows = _rows(CLEARED)
    added = {r["position_or_word_id"]: r for r in _rows(ADDED)}
    if len(rows) != 50 or list(added) != ["680991"]:
        raise Stop("the row files are not 50 cleared rows + the one added row")
    plan = {"prose": [], "words": [], "kjv": []}
    for r in rows:
        if r["cell"] == "verses.text":
            plan["prose"].append({"key": _ref(r["verse"]), "before": r["before"], "after": r["after"], "read": r["read"]})
        elif r["cell"] == "words.english":
            plan["words"].append({"key": _ref(r["verse"]), "pos": int(r["position_or_word_id"]),
                                  "before": r["before"], "after": r["after"], "read": r["read"]})
        elif r["cell"] == "kjv_strongs.strongs_id":
            wid = r["position_or_word_id"]
            after = r["after"]
            if wid in added:
                if added[wid]["before"] != r["before"]:
                    raise Stop(f"added row {wid}: its before-value is not the cleared one")
                after = added[wid]["after"]
            word, before_tag = _tag(r["before"], wid)
            word2, after_tag = _tag(after, wid)
            if word != word2:
                raise Stop(f"word {wid}: {word!r} vs {word2!r}")
            plan["kjv"].append({"id": int(wid), "word": word, "before": before_tag, "after": after_tag})
        else:
            raise Stop(f"unknown cell {r['cell']!r}")
    if (len(plan["prose"]), len(plan["words"]), len(plan["kjv"])) != (15, 14, 21):
        raise Stop("row counts are not 15 / 14 / 21")
    return plan


def new_rows(plan):
    """The 28 abp_corrections rows. Prose source_value = B's text, the form the rebuild holds at finish
    step 4b: the live text with em-dashes back as '--'. corrected_value = final form (DESIGN 9.80)."""
    out = []
    for r in plan["prose"]:
        if r["key"] != EXISTING_PROSE:
            out.append((*r["key"], -1, "verses.text", r["before"].replace("—", "--"), r["after"], r["read"]))
    for r in plan["words"]:
        out.append((*r["key"], r["pos"], "english", r["before"], r["after"], r["read"]))
    return out


def kjv_moves(plan):
    """-> (deletes, moves, inserts). Each tag moves one word left; G2532 comes off; G846 goes on."""
    before = {r["id"]: r["before"] for r in plan["kjv"]}
    after = {r["id"]: r["after"] for r in plan["kjv"]}
    moves, used = [], set()
    inserts = []
    for wid in sorted(after):
        tag = after[wid]
        if tag is None:
            continue
        if before.get(wid + 1) == tag:
            moves.append((tag, wid + 1, wid))
            used.add(wid + 1)
        else:
            inserts.append((tag, wid))
    deletes = [(before[w], w) for w in sorted(before) if before[w] and w not in used]
    if (len(deletes), len(moves), len(inserts)) != (1, 16, 1):
        raise Stop(f"KJV plan is not 1 off / 16 moved / 1 on: {len(deletes)} / {len(moves)} / {len(inserts)}")
    return deletes, moves, inserts


def _one(conn, sql, args, what):
    hits = conn.execute(sql, args).fetchall()
    if len(hits) != 1:
        raise Stop(f"{what}: {len(hits)} rows, expected exactly 1")
    return hits[0]


def verify(conn, plan, side):
    """Every cell must hold its `side` value ('before' / 'after'). Returns the problem list."""
    bad = []
    def cell(what, got, want):
        if got != want:
            bad.append(f"{what}: reads {got!r}, expected {want!r}")
    try:
        for r in plan["prose"]:
            got = _one(conn, "SELECT text FROM verses WHERE book=? AND chapter=? AND verse=?", r["key"],
                       f"verse {r['key']}")[0]
            cell(f"{r['key']} verses.text", got, r[side])
        for r in plan["words"]:
            got = _one(conn, """SELECT w.english FROM words w JOIN verses v ON v.id = w.verse_id
                                WHERE v.book=? AND v.chapter=? AND v.verse=? AND w.position=?""",
                       (*r["key"], r["pos"]), f"word {r['key']} @{r['pos']}")[0]
            cell(f"{r['key']} @{r['pos']} english", got, r[side])
        for r in plan["kjv"]:
            w = _one(conn, "SELECT word, book_id, chapter, verse_num FROM kjv_words WHERE word_id=?", (r["id"],),
                     f"KJV word {r['id']}")
            cell(f"KJV word {r['id']}", tuple(w), (r["word"], KJV_BOOK, KJV_CH, KJV_VS))
            tags = sorted(x[0] for x in conn.execute("SELECT strongs_id FROM kjv_strongs WHERE word_id=?", (r["id"],)))
            cell(f"KJV word {r['id']} ({r['word']}) tags", tags, [r[side]] if r[side] else [])
        n = conn.execute("SELECT count(*) FROM abp_corrections WHERE status='active' AND applied_at='ingest'").fetchone()[0]
        cell("active correction rows", n, ACTIVE_BEFORE if side == "before" else ACTIVE_AFTER)
        ex = next(r for r in plan["prose"] if r["key"] == EXISTING_PROSE)
        got = _one(conn, """SELECT corrected_value, source_value FROM abp_corrections WHERE book=? AND chapter=? AND verse=?
                            AND position=-1 AND field='verses.text' AND status='active' AND applied_at='ingest'""",
                   EXISTING_PROSE, "the existing 2Ki 14:28 prose row")
        cell("2Ki 14:28 prose row corrected_value", got[0], ex[side])
        if "belonging to to Judah" not in (got[1] or ""):
            bad.append("2Ki 14:28 prose row: its source_value is not B's text")
        for b, c, v, pos, fld, src, cor, _read in new_rows(plan):
            hits = conn.execute("""SELECT source_value, corrected_value, status, applied_at FROM abp_corrections
                                   WHERE book=? AND chapter=? AND verse=? AND position=? AND field=?""",
                                (b, c, v, pos, fld)).fetchall()
            what = f"correction row {b} {c}:{v} @{pos} {fld}"
            if side == "before":
                cell(what + " (any status)", len(hits), 0)
            elif len(hits) != 1:
                bad.append(f"{what}: {len(hits)} rows, expected 1")
            else:
                cell(what, tuple(hits[0]), (src, cor, "active", "ingest"))
    except Stop as e:
        bad.append(str(e))
    return bad


def check_structure(conn):
    """Things that would make the write do more than the plan says."""
    cols = sorted(r[1] for r in conn.execute("PRAGMA table_info(kjv_strongs)"))
    if cols != ["strongs_id", "word_id"]:
        raise Stop(f"kjv_strongs columns are {cols}, expected word_id + strongs_id")
    trig = [r[0] for r in conn.execute("""SELECT name FROM sqlite_master WHERE type='trigger'
                                          AND tbl_name IN ('verses','words','kjv_strongs','abp_corrections')""")]
    if trig:
        raise Stop(f"triggers on the written tables: {trig}")
    mode = (conn.execute("PRAGMA journal_mode").fetchone()[0] or "").lower()
    if mode != "delete":
        raise Stop(f"journal_mode is {mode!r}, must be delete")
    w, v = (conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("words", "verses"))
    if (w, v) != (WORDS, VERSES):
        raise Stop(f"words {w:,} / verses {v:,}, expected {WORDS:,} / {VERSES:,}")
    print(f"structure: kjv_strongs = word_id + strongs_id; no triggers; journal delete; words {w:,}; verses {v:,}")


def check_fill(plan):
    got = sha(FILL)
    if got != FILL_SHA:
        raise Stop(f"frozen fill file sha {got}, pinned {FILL_SHA}")
    fill = {(r["book"], int(r["chapter"]), int(r["verse"]), int(r["position"])) for r in _rows(FILL)}
    hit = [(r["key"], r["pos"]) for r in plan["words"] if (*r["key"], r["pos"]) in fill]
    if hit:
        raise Stop(f"a written word slot is a frozen fill slot: {hit}")
    print(f"frozen fill: {len(fill):,} slots, sha as pinned; written word slots in it: 0")


def check_feed(conn, plan):
    """The source_value of each prose row must be EXACTLY what the rebuild's prose step writes."""
    import build_prose_from_app as BP
    from build_words_from_abp import AppTransplant, abp_source_texts
    with contextlib.redirect_stdout(io.StringIO()):
        app = AppTransplant(abp_source_texts())
    want = {(b, c, v): src for b, c, v, _p, fld, src, _c, _r in new_rows(plan) if fld == "verses.text"}
    want[EXISTING_PROSE] = _one(conn, """SELECT source_value FROM abp_corrections WHERE book=? AND chapter=? AND verse=?
                                         AND position=-1 AND field='verses.text' AND status='active'""",
                                EXISTING_PROSE, "the existing 2Ki 14:28 prose row")[0]
    for k, src in want.items():
        if app.decide(k)[0] != "compose":
            raise Stop(f"{k}: the rebuild's prose step would not write this verse")
        got = BP.feed_text(app, k, collections.Counter())
        if got != src:
            raise Stop(f"{k}: source_value is not the prose step's text")
    print(f"prose sources: {len(want)} of 15 = the rebuild's own prose text, byte for byte")


def member_read(db, frozen):
    import audit_reassembly_diff as A
    if sha(ELIGIBLE) != ELIGIBLE_SHA:
        raise Stop(f"{ELIGIBLE} is not the pinned eligible list")
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        hits = A.reassembly_hits_v2(conn)
    finally:
        conn.close()
    d = A.member_diff_v2(hits, A.load_punct_members(str(frozen)), A.load_eligible_refs(str(ELIGIBLE)))
    return {"word-order": d["word-order"], "content-other": d["content-other"], "dup-gloss": d["dup-gloss"],
            "gone": d["gone"], "new": d["new_eligible"] + d["new_not_eligible"], "changed": d["changed_ops"],
            "same": d["same"], "declared_row": d["declared_row"]}


def check_members(db, frozen, content_other, same):
    d = member_read(db, frozen)
    want = {"word-order": [], "content-other": content_other, "dup-gloss": [], "gone": [], "new": [],
            "changed": [], "same": same, "declared_row": None}
    if d != want:
        raise Stop(f"word-order check differs from the declared picture: {d}")
    print(f"word-order check: word-order 0, content-other {content_other or 0}, dup-gloss 0, gone 0, new 0, "
          f"changed 0, punct members unchanged {same}")


def phrase_gloss(db):
    r = subprocess.run([sys.executable, str(HERE / "audit_phrase_gloss_underdist.py"), str(db)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    err = " / ".join((r.stderr or "").strip().splitlines()[-3:])
    if r.returncode != 0:
        raise Stop(f"phrase-gloss audit: exit {r.returncode}; stderr: {err or '(none)'}")
    if "(note:" in (r.stderr or ""):     # allowlist or LSJ missing: the count is not the gated one
        raise Stop(f"phrase-gloss audit: ran without a required input: {err}")
    lines = r.stdout.splitlines()
    if not any(ln.startswith("  CONTROL Psa 39:1: FIRED") for ln in lines):
        ctl = next((ln.strip() for ln in lines if "CONTROL" in ln), "(no CONTROL line)")
        raise Stop(f"phrase-gloss audit: its control did not fire: {ctl}; stderr: {err or '(none)'}")
    m = re.search(r"FLAGGED BEYOND allowlist \(gate <= 747\):\s*([\d,]+)", r.stdout)
    if not m:
        raise Stop("phrase-gloss audit: no result line")
    n = int(m.group(1).replace(",", ""))
    if n > PHRASE_GATE:
        raise Stop(f"phrase-gloss {n} is above the gate {PHRASE_GATE}")
    print(f"phrase-gloss: {n} (gate <= {PHRASE_GATE}), control fired")
    return n


def active_sha(conn):
    rows = conn.execute("""SELECT book, chapter, verse, position, field, ledger_ref FROM abp_corrections
                           WHERE status='active' AND applied_at='ingest'""").fetchall()
    rows = sorted(rows, key=lambda x: (x[0], int(x[1]), int(x[2]), int(x[3]), x[4]))
    text = "".join("\t".join(str(c) for c in r) + "\n" for r in rows)
    return len(rows), hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_cert(db):
    import cert_invariants as C
    old = C.PINS["abp_corrections_active"]
    C.PINS["abp_corrections_active"] = ACTIVE_AFTER     # this read only; the code's pin moves after it passes
    try:
        rc = C.run_suite(str(db))
    finally:
        C.PINS["abp_corrections_active"] = old
    if rc:
        raise Stop("cert_invariants did not read all green at 403")


def in_window(now=None):
    now = now or datetime.now(timezone.utc)
    return (13, 0) <= (now.hour, now.minute) < (14, 30)


def _pins():
    for p, want in ((PUNCT_OLD, PUNCT_OLD_SHA), (PUNCT_NEW, PUNCT_NEW_SHA), (ACTIVE_OLD, ACTIVE_OLD_SHA), (ACTIVE_NEW, ACTIVE_NEW_SHA)):
        if sha(p) != want:
            raise Stop(f"{p.name} is not the pinned file")


def _ro(db):
    return sqlite3.connect(f"file:{db}?mode=ro", uri=True)


def do_check(db):
    plan = load_plan()
    _pins()
    conn = _ro(db)
    try:
        check_structure(conn)
        bad = verify(conn, plan, "before")
        if bad:
            raise Stop(f"{len(bad)} before-value(s) differ:\n  " + "\n  ".join(bad))
        print("before-values: 15 verses, 14 word cells, 21 KJV words, 375 active rows: all as cleared")
        n, h = active_sha(conn)
        if (n, h) != (ACTIVE_BEFORE, ACTIVE_OLD_SHA):
            raise Stop(f"active row list {n} / {h} is not the pinned 375")
        print(f"active corrections: {n}, member list sha {h}")
        check_feed(conn, plan)
    finally:
        conn.close()
    check_fill(plan)
    check_members(db, PUNCT_OLD, ["Job 3:3"], PUNCT_BEFORE)
    phrase_gloss(db)
    kd, km, ki = kjv_moves(plan)
    print(f"plan: {len(plan['prose'])} verses (1 existing row changed) + {len(plan['words'])} word cells + "
          f"{len(new_rows(plan))} new correction rows + KJV {len(kd)} off / {len(km)} moved / {len(ki)} on = {CHANGES} changes")


def _write(conn, plan, forward):
    src, dst = ("before", "after") if forward else ("after", "before")
    for r in plan["prose"]:
        c = conn.execute("UPDATE verses SET text=? WHERE book=? AND chapter=? AND verse=? AND text=?",
                         (r[dst], *r["key"], r[src]))
        if c.rowcount != 1:
            raise Stop(f"verse {r['key']}: {c.rowcount} rows written")
    for r in plan["words"]:
        c = conn.execute("""UPDATE words SET english=? WHERE position=? AND english=? AND verse_id=
                            (SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?)""",
                         (r[dst], r["pos"], r[src], *r["key"]))
        if c.rowcount != 1:
            raise Stop(f"word {r['key']} @{r['pos']}: {c.rowcount} rows written")
    ex = next(r for r in plan["prose"] if r["key"] == EXISTING_PROSE)
    c = conn.execute("""UPDATE abp_corrections SET corrected_value=? WHERE book=? AND chapter=? AND verse=? AND position=-1
                        AND field='verses.text' AND status='active' AND applied_at='ingest' AND corrected_value=?""",
                     (ex[dst], *EXISTING_PROSE, ex[src]))
    if c.rowcount != 1:
        raise Stop(f"the existing 2Ki 14:28 prose row: {c.rowcount} rows written")
    for b, ch, v, pos, fld, s, cor, read in new_rows(plan):
        if forward:
            conn.execute("""INSERT INTO abp_corrections (book, chapter, verse, position, field, source_value, corrected_value,
                            reason, ledger_ref, applied_at, status, created) VALUES (?,?,?,?,?,?,?,?,?,'ingest','active',?)""",
                         (b, ch, v, pos, fld, s, cor, f"app-edition slip, DESIGN 9.247: {read}", f"EU-{b}{ch}:{v}", CREATED))
        else:
            c = conn.execute("""DELETE FROM abp_corrections WHERE book=? AND chapter=? AND verse=? AND position=? AND field=?
                                AND source_value=? AND corrected_value=? AND created=? AND status='active'""",
                             (b, ch, v, pos, fld, s, cor, CREATED))
            if c.rowcount != 1:
                raise Stop(f"correction row {b} {ch}:{v} @{pos} {fld}: {c.rowcount} rows removed")
    deletes, moves, inserts = kjv_moves(plan)
    def move(tag, frm, to):
        c = conn.execute("UPDATE kjv_strongs SET word_id=? WHERE word_id=? AND strongs_id=?", (to, frm, tag))
        if c.rowcount != 1:
            raise Stop(f"KJV tag {tag} {frm} -> {to}: {c.rowcount} rows")
    def off(tag, wid):
        c = conn.execute("DELETE FROM kjv_strongs WHERE word_id=? AND strongs_id=?", (wid, tag))
        if c.rowcount != 1:
            raise Stop(f"KJV tag {tag} off {wid}: {c.rowcount} rows")
    def on(tag, wid):
        conn.execute("INSERT INTO kjv_strongs (word_id, strongs_id) VALUES (?, ?)", (wid, tag))
    if forward:
        for tag, wid in deletes:
            off(tag, wid)
        for tag, frm, to in moves:          # left to right: each target word is already empty
            move(tag, frm, to)
        for tag, wid in inserts:
            on(tag, wid)
    else:
        for tag, wid in inserts:
            off(tag, wid)
        for tag, frm, to in reversed(moves):
            move(tag, to, frm)
        for tag, wid in deletes:
            on(tag, wid)


def do_write(db, forward):
    if in_window():
        raise Stop("13:00-14:30 UTC: not started (the nightly health check and backup)")
    plan = load_plan()
    _pins()
    src, dst = ("before", "after") if forward else ("after", "before")
    conn = sqlite3.connect(str(db), isolation_level=None)
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        check_structure(conn)
        if forward:
            check_feed(conn, plan)
        conn.execute("BEGIN IMMEDIATE")
        try:
            bad = verify(conn, plan, src)
            if bad:
                raise Stop(f"{len(bad)} starting value(s) differ:\n  " + "\n  ".join(bad))
            start = conn.total_changes
            _write(conn, plan, forward)
            n = conn.total_changes - start
            if n != CHANGES:
                raise Stop(f"{n} changes, expected {CHANGES}")
            bad = verify(conn, plan, dst)
            if bad:
                raise Stop(f"{len(bad)} result(s) differ:\n  " + "\n  ".join(bad))
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()
    print(f"{'written' if forward else 'put back'}: {CHANGES} changes, every result read back")


def do_after(db):
    plan = load_plan()
    _pins()
    conn = _ro(db)
    try:
        check_structure(conn)
        bad = verify(conn, plan, "after")
        if bad:
            raise Stop(f"{len(bad)} after-value(s) differ:\n  " + "\n  ".join(bad))
        print("after-values: 15 verses, 14 word cells, 21 KJV words, 403 active rows: all as cleared")
        n, h = active_sha(conn)
        if (n, h) != (ACTIVE_AFTER, ACTIVE_NEW_SHA):
            raise Stop(f"active row list {n} / {h} is not the new pinned list")
        print(f"NEW PIN abp_corrections_active: {n}, member list sha {h}")
    finally:
        conn.close()
    check_fill(plan)
    check_members(db, PUNCT_NEW, [], PUNCT_AFTER)
    print(f"NEW FROZEN punct list: {PUNCT_AFTER} members, sha {PUNCT_NEW_SHA}")
    phrase_gloss(db)
    run_cert(db)


def main(argv=None):
    ap = argparse.ArgumentParser(description="The Bible-text batch (DESIGN 9.246, 9.247).")
    ap.add_argument("mode", choices=["check", "apply", "after", "undo"])
    ap.add_argument("--db", default=str(LIVE))
    a = ap.parse_args(argv)
    db = Path(a.db).expanduser()
    label = a.mode.upper()
    try:
        if not db.is_file():
            raise Stop(f"no database at {db}")
        print(f"BTB {label} on {db} at {datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}")
        if a.mode == "check":
            do_check(db)
        elif a.mode == "apply":
            do_write(db, True)
        elif a.mode == "undo":
            do_write(db, False)
        else:
            do_after(db)
    except Stop as e:
        print(f"BTB {label} RESULT: STOP - {e}")
        print("Nothing was saved by this step." if a.mode in ("apply", "undo") else "This step only reads.")
        return 1
    print(f"BTB {label} RESULT: DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
