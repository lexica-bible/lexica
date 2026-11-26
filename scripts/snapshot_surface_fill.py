#!/usr/bin/env python3
"""
snapshot_surface_fill.py — rebuild-trap fix, part (a) first half (CHARTER_rebuild_trap_fix.md §2a):
freeze the 2026-10-25 abp_surface fill as the 4,411-row diff, BEFORE /rebuild-words step 9 drops it.

READ-ONLY on every database (each is opened read-only). Writes exactly two files: the frozen
snapshot (--out, a TSV) and its checksum beside it (<out>.sha256, `sha256sum -c` format).

What a snapshot row carries (one per fill slot, 4,411):
  the slot          verse_id, book, chapter, verse, position
  the fill write    action (insert/update), cls, form, translit — as the source file holds them
  the old value     old_form, old_translit — the pre-fill copy's row (updates only; the restore's
                    precondition: write only where the builder's value still equals it)
  the OLD words row strongs, strongs_base, english, english_head, is_pn — the slot's word as it
                    stood before the rebuild (after the swap it exists only in the rollback copy)
  the key-2 ordinal k2_ordinal (this slot is the k-th, from 0, carrying its full strongs in the
                    verse) and k2_count (how many slots carry it) — key 2 needs the old verse
Order: by (verse_id, position). Text: UTF-8, LF, tab-separated, a missing value written as \\N.
A value holding a tab, a newline, or the text \\N is refused (it could not be read back exactly).
Same inputs -> byte-identical file (and so the same checksum).

Controls before anything is written (any failure STOPS, no file written):
  G0  source minus pre-fill copy = 4,411 / 538 rows, = the approved CSV (dryrun_rekey_fill.g0 —
      the ONE copy of that check)
  O   every fill slot has exactly one word row in the source (no orphan, no duplicate position)
  R   the file read back = the rows written, value for value

REFUSES the live database and any file named bible.db (dryrun_rekey_fill.is_live). Run it on a
COPY of live taken before the rebuild (or the step-1 rollback copy) — it must hold the fill AND the
old word positions.

  PYTHONIOENCODING=utf-8 python3 scripts/snapshot_surface_fill.py \\
      --src ~/rekey/old3.db --prefill ~/bible.db.pre-surface-fill-20261025 \\
      --csv ~/abp_surface_fill_dryrun.csv \\
      --out ~/bible-db/tests/fixtures/rebuild_trap/abp_surface_fill_20261025.tsv

The edition-upgrade re-freeze (2026-11-15, DESIGN 9.120 F3 / 9.133; STEP9C-FREEZE) made the file now
pinned, from the upgraded copy after 9a: --src <built> --prefill <the pre-9a copy of its abp_surface>
--from-restore <the 9a apply report> --out .../abp_surface_fill_20261115.tsv.

--amend (DESIGN 9.269, the form-cell lane): a small pinned fill-amendment file laid over --from-restore,
for slots a ruled lane changed on live after the report (insert / update / change / drop / remove; see
read_amend). A `remove` row is a builder row the fill result does not hold: action remove, form \\N,
old_form = the builder's form; the restore deletes exactly that row. Pinned as AMEND_SHA256 in
restore_surface_fill.py; once set, --check must name the file.

The snapshot holds ABP text (printed Greek forms + ABP English): it stays OUT of the public repo
(.gitignore) — PA keeps it in the fixture folder; a second copy goes to the local fixture folder.

--check  (the /rebuild-words step 1a mode, added 2026-10-25, charter §9): the frozen file already
exists — verify it, write NOTHING. Its .sha256 must match, it must be the snapshot pinned in
restore_surface_fill.py (SNAPSHOT_SHA256), and re-deriving the rows from --src (a fresh copy of live)
must give the frozen file BYTE FOR BYTE. With --from-restore, the report must also match its
.sha256 and be the report pinned in restore_surface_fill.py (REPORT_SHA256, R1). Pass -> "SNAPSHOT CURRENT". Anything else -> STOPPED: STALE
SNAPSHOT, naming the slots that differ; the file is never overwritten (a re-freeze is a ruling,
--replace without --check). A missing file under --check also stops (copy the second copy back).
"""
import argparse
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dryrun_rekey_fill as dr          # noqa: E402  (is_live, ro, real, g0, Stop, say)

N_ROWS = 4411
NULL = "\\N"
COLUMNS = ("verse_id", "book", "chapter", "verse", "position", "action", "cls", "form", "translit",
           "old_form", "old_translit", "strongs", "strongs_base", "english", "english_head",
           "is_pn", "k2_ordinal", "k2_count")
INT_COLUMNS = {"verse_id", "chapter", "verse", "position", "is_pn", "k2_ordinal", "k2_count"}

Stop, say, real = dr.Stop, dr.say, dr.real


# ── the file format (THE reader + writer; restore_surface_fill.py imports both) ──────────────
def _cell(col, v):
    if v is None:
        return NULL
    s = str(v)
    if s == NULL or "\t" in s or "\n" in s or "\r" in s:
        raise Stop(f"value in column {col} cannot be written exactly: {s!r}")
    return s


def render(rows):
    """[dict] -> bytes. Rows sorted by (verse_id, position); every column in COLUMNS order."""
    rows = sorted(rows, key=lambda r: (r["verse_id"], r["position"]))
    lines = ["\t".join(COLUMNS)]
    lines += ["\t".join(_cell(c, r[c]) for c in COLUMNS) for r in rows]
    return ("\n".join(lines) + "\n").encode("utf-8")


def parse(data):
    """bytes -> [dict], the exact inverse of render()."""
    text = data.decode("utf-8")
    if not text.endswith("\n"):
        raise Stop("snapshot does not end with a newline — truncated?")
    lines = text[:-1].split("\n")
    if tuple(lines[0].split("\t")) != COLUMNS:
        raise Stop(f"snapshot header is not {COLUMNS}")
    out = []
    for n, line in enumerate(lines[1:], 2):
        cells = line.split("\t")
        if len(cells) != len(COLUMNS):
            raise Stop(f"snapshot line {n}: {len(cells)} cells, expect {len(COLUMNS)}")
        r = {}
        for c, s in zip(COLUMNS, cells):
            r[c] = None if s == NULL else (int(s) if c in INT_COLUMNS else s)
        out.append(r)
    return out


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_snapshot(path):
    """-> (rows, hex). Verifies the .sha256 file beside it first."""
    p = real(path)
    if not os.path.isfile(p):
        raise Stop(f"snapshot {path}: no such file")
    with open(p, "rb") as f:
        data = f.read()
    side = p + ".sha256"
    if not os.path.isfile(side):
        raise Stop(f"checksum file {side} missing — the snapshot cannot be trusted without it")
    with open(side, encoding="utf-8") as f:
        want = f.read().split()[0]
    got = sha256(data)
    if got != want:
        raise Stop(f"snapshot checksum {got} != {want} in {os.path.basename(side)} — file changed")
    return parse(data), got


# ── building the rows ─────────────────────────────────────────────────────────
def word_rows(con, vids):
    """verse_id -> [(position, strongs, strongs_base, english, english_head, is_pn)] by position."""
    out = {}
    for v, p, s, sb, e, eh, pn in con.execute(
            "SELECT verse_id, position, strongs, strongs_base, english, english_head, is_pn "
            "FROM words"):
        if v in vids:
            out.setdefault(v, []).append((p, s, sb, e, eh, pn))
    for v in out:
        out[v].sort(key=lambda r: r[0])
    return out


AMEND_HEADER = ("book", "chapter", "verse", "position", "action", "cls", "form", "old_form", "note")
AMEND_ACTIONS = ("insert", "update", "change", "drop", "remove")


def read_amend(path):
    """The fill-amendment file (DESIGN 9.269): the slots a ruled lane changes on top of the restore
    report, at their CURRENT positions. One row per slot:
      insert  a new fill slot: the pre-fill table has no row; --src holds `form`
      update  a new fill slot over a builder row: the pre-fill row is `old_form`; --src holds `form`
      change  a slot the report placed: its form was `old_form`, --src now holds `form`
      drop    a slot the report placed (form `old_form`) leaves the fill: --src = the pre-fill table there
      remove  the pre-fill row `old_form` is not in the fill result: --src holds no row there
    -> [dict]; any malformed line stops before a database is read."""
    with open(real(path), encoding="utf-8", newline="") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]
    if not lines or tuple(lines[0].split("\t")) != AMEND_HEADER:
        raise Stop(f"--amend {path}: header must be {AMEND_HEADER}")
    out, seen = [], set()
    for n, ln in enumerate(lines[1:], 2):
        c = ln.split("\t")
        if len(c) != len(AMEND_HEADER) or not all(x.isdigit() for x in c[1:4]) or c[4] not in AMEND_ACTIONS:
            raise Stop(f"--amend {path}: line {n} is not {AMEND_HEADER} with an action in {AMEND_ACTIONS}")
        r = dict(zip(AMEND_HEADER, c))
        r.update(chapter=int(r["chapter"]), verse=int(r["verse"]), position=int(r["position"]))
        k = (r["book"], r["chapter"], r["verse"], r["position"])
        if k in seen:
            raise Stop(f"--amend {path}: {k} listed twice")
        seen.add(k)
        needs_form = r["action"] in ("insert", "update", "change")
        needs_old = r["action"] in ("update", "change", "drop", "remove")
        if bool(r["form"]) != needs_form or bool(r["old_form"]) != needs_old or (needs_form and not r["cls"]):
            raise Stop(f"--amend {path}: line {n} ({r['action']}): form / old_form / cls do not fit the action")
        out.append(r)
    return out


def g0_report(csrc, cpre, report_path, amend_path=None):
    """G0 for a re-freeze after an edition upgrade (DESIGN 9.120, F3): the fill = --src minus the
    pre-fill table, and it must be EXACTLY the slots restore_surface_fill.py's --report placed
    (key-2-listed included, leave-listed never), at their NEW positions, form for form. Action
    and cls come from the report; the counts are the report's, never the 10/25 constants.
    With --amend (DESIGN 9.269) the amendment file's rows are laid over the report first. A
    `remove` slot (from the amendment file, or a report placed with action remove) is a pre-fill
    row that --src does not hold.
    -> the same tuple as dryrun_rekey_fill.g0, plus the remove slots {slot: cls}."""
    say("G0  the fill diff vs the restore report" + (" + the amendment file" if amend_path else ""))
    s_src, s_pre = dr.surface(csrc), dr.surface(cpre)
    new_side = {k: v for k, v in s_src.items() if s_pre.get(k) != v}
    old_side = {k: v for k, v in s_pre.items() if s_src.get(k) != v}
    vold = dr.verses(csrc)
    vkey = {(b, c, v): i for i, (b, c, v) in vold.items()}
    with open(real(report_path), encoding="utf-8", newline="") as f:
        lines = [ln.rstrip("\n").split("\t") for ln in f if ln.strip()]
    need = {"book", "chapter", "verse", "old_position", "new_position", "action", "cls", "form", "result"}
    if not lines or not need <= set(lines[0]):
        raise Stop(f"G0 {report_path} is not a restore_surface_fill.py --report (columns {sorted(need)})")
    head = lines[0]
    writes, removes = {}, {}
    for cells in lines[1:]:
        r = dict(zip(head, cells))
        if r["result"] != "placed":
            continue
        vid = vkey.get((r["book"], int(r["chapter"]), int(r["verse"])))
        if vid is None:
            raise Stop(f"G0 report verse {r['book']} {r['chapter']}:{r['verse']} is not in --src")
        k = (vid, int(r["new_position"]))
        if k in writes or k in removes:
            raise Stop(f"G0 report places two snapshot rows on slot {k}")
        if r["action"] == "remove":
            removes[k] = r["cls"]
        else:
            writes[k] = dict(action=r["action"], cls=r["cls"], new_form=r["form"])
    if amend_path:
        for a in read_amend(amend_path):
            vid = vkey.get((a["book"], a["chapter"], a["verse"]))
            if vid is None:
                raise Stop(f"G0 amendment verse {a['book']} {a['chapter']}:{a['verse']} is not in --src")
            k, act, where = (vid, a["position"]), a["action"], f"{a['book']} {a['chapter']}:{a['verse']} @{a['position']}"
            if act in ("change", "drop"):
                if k not in writes or writes[k]["new_form"] != a["old_form"]:
                    raise Stop(f"G0 amendment {act} {where}: the report does not place {a['old_form']!r} there")
                if act == "drop":
                    del writes[k]
                else:
                    writes[k] = dict(writes[k], cls=a["cls"], new_form=a["form"])
                continue
            if k in writes or k in removes:
                raise Stop(f"G0 amendment {act} {where}: the report already places that slot")
            if act == "remove":
                if s_pre.get(k, (None,))[0] != a["old_form"]:
                    raise Stop(f"G0 amendment remove {where}: the pre-fill row is {s_pre.get(k)!r}, not {a['old_form']!r}")
                removes[k] = a["cls"]
            else:
                if act == "update" and s_pre.get(k, (None,))[0] != a["old_form"]:
                    raise Stop(f"G0 amendment update {where}: the pre-fill row is {s_pre.get(k)!r}, not {a['old_form']!r}")
                writes[k] = dict(action=act, cls=a["cls"], new_form=a["form"])
    say(f"    placed {len(writes):,} + removed {len(removes):,} · src-not-in-prefill {len(new_side):,} · "
        f"prefill-not-in-src {len(old_side):,}")
    if set(writes) != set(new_side):
        raise Stop(f"G0 the report places {len(writes):,} slots, the diff holds {len(new_side):,} "
                   f"({len(set(writes) ^ set(new_side)):,} differ, e.g. "
                   f"{sorted(set(writes) ^ set(new_side))[:3]}) — something else changed abp_surface")
    bad = [k for k, w in writes.items() if w["new_form"] != new_side[k][0]]
    if bad:
        raise Stop(f"G0 {len(bad)} report form(s) differ from the stored form, e.g. {bad[:3]}")
    ins = {k for k, w in writes.items() if w["action"] == "insert"}
    upd = {k for k, w in writes.items() if w["action"] == "update"}
    if len(ins) + len(upd) != len(writes) or any(k in s_pre for k in ins) \
            or set(old_side) != upd | set(removes) or any(k in s_src for k in removes):
        raise Stop("G0 insert/update/remove split does not match the pre-fill table (an insert slot was "
                   "filled, or the changed pre-fill rows are not exactly the updates and removes)")
    if removes or amend_path:
        say(f"    PASS — {len(writes) + len(removes):,} = {len(ins):,} insert + {len(upd):,} update + "
            f"{len(removes):,} remove = the restore report" + (" + the amendment file" if amend_path else ""))
    else:
        say(f"    PASS — {len(writes):,} = {len(ins):,} insert + {len(upd):,} update = the restore report")
    return new_side, old_side, writes, ins, upd, vold, removes


def build_rows(csrc, cpre, csv_path, report=None, amend=None):
    """-> (rows, inserts, updates, removes)."""
    if report:
        new_side, old_side, writes, ins, upd, vold, removes = g0_report(csrc, cpre, report, amend)
    else:
        new_side, old_side, writes, ins, upd, vold = dr.g0(csrc, cpre, csv_path)
        removes = {}
    vids = {v for v, _ in new_side} | {v for v, _ in removes}
    words = word_rows(csrc, vids)
    say("O   every fill slot has exactly one word row in --src")
    rows, orphans, dupes = [], [], []
    slots = [(k, writes[k]["action"], writes[k]["cls"], new_side[k]) for k in new_side] + \
            [(k, "remove", cls, (None, None)) for k, cls in removes.items()]
    for (vid, pos), action, cls, (form, translit) in sorted(slots):
        vrows = words.get(vid, [])
        mine = [r for r in vrows if r[0] == pos]
        if not mine:
            orphans.append((vid, pos))
            continue
        if len(mine) > 1:
            dupes.append((vid, pos))
            continue
        _, s, sb, e, eh, pn = mine[0]
        same = [r[0] for r in vrows if r[1] == s]
        old = old_side.get((vid, pos))           # updates + removes only (an insert slot had no row)
        if (action in ("update", "remove")) != (old is not None):
            raise Stop(f"slot {(vid, pos)}: action {action} but pre-fill row {old!r}")
        b, c, v = vold[vid]
        rows.append(dict(verse_id=vid, book=b, chapter=c, verse=v, position=pos,
                         action=action, cls=cls, form=form, translit=translit,
                         old_form=old[0] if old else None, old_translit=old[1] if old else None,
                         strongs=s, strongs_base=sb, english=e, english_head=eh, is_pn=pn,
                         k2_ordinal=same.index(pos), k2_count=len(same)))
    if orphans or dupes:
        raise Stop(f"{len(orphans)} fill slot(s) with no word row (e.g. {orphans[:3]}), "
                   f"{len(dupes)} on a duplicate position (e.g. {dupes[:3]})")
    say(f"    PASS — {len(rows):,} slots, each on one word row")
    return rows, len(ins), len(upd), len(removes)


def pinned():
    """THE pin lives in restore_surface_fill.py (SNAPSHOT_SHA256) — read it from there."""
    import restore_surface_fill as rs
    return rs.SNAPSHOT_SHA256


def stale_slots(frozen, fresh):
    """-> [(slot, what differs)] between two row lists, keyed by (verse_id, position)."""
    a = {(r["verse_id"], r["position"]): r for r in frozen}
    b = {(r["verse_id"], r["position"]): r for r in fresh}
    out = []
    for k in sorted(set(a) | set(b)):
        if k not in b:
            out.append((k, "in the frozen file only"))
        elif k not in a:
            out.append((k, "in --src only"))
        else:
            cols = [c for c in COLUMNS if a[k][c] != b[k][c]]
            if cols:
                out.append((k, "differs in " + ", ".join(cols)))
    return out


def pinned_report():
    """R1 (DESIGN 9.121 / 9.133): the restore report's pin lives in restore_surface_fill.py
    (REPORT_SHA256), beside the snapshot pin — read it from there."""
    import restore_surface_fill as rs
    return rs.REPORT_SHA256


def report_pin(report_path, required):
    """The restore report is one of the three pinned inputs once a re-freeze is made from it
    (DESIGN 9.120 F3): <report>.sha256 beside it must match. Required under --check, where the
    report must also be the one pinned in code (REPORT_SHA256, R1); under a re-freeze it is
    verified when present and the report's sha is printed for pinning."""
    with open(real(report_path), "rb") as f:
        hexd = sha256(f.read())
    pin = real(report_path) + ".sha256"
    if os.path.isfile(pin):
        with open(pin, encoding="utf-8") as f:
            want = (f.read().split() or [""])[0]
        if want != hexd:
            raise Stop(f"--from-restore {report_path}: sha256 {hexd[:16]}… != its .sha256 "
                       f"{(want or '(empty file)')[:16]}…")
        say(f"    restore report sha256 {hexd} = its .sha256")
    elif required:
        raise Stop(f"--from-restore {report_path}: no .sha256 beside it — the report is a pinned input "
                   "under --check")
    else:
        say(f"    restore report sha256 {hexd} (no .sha256 beside it yet — pin it with the new freeze)")
    if required:
        code = pinned_report()
        if code is not None and hexd != code:
            raise Stop(f"--from-restore {report_path}: sha256 {hexd[:16]}… is not the pinned report "
                       f"{code[:16]}… (REPORT_SHA256 in restore_surface_fill.py)")
        say("    restore report = the pin in restore_surface_fill.py" if code
            else "    (no report pin set in restore_surface_fill.py)")
    return hexd


def pinned_amend():
    """DESIGN 9.269: the amendment file's pin lives in restore_surface_fill.py (AMEND_SHA256), beside
    the snapshot and report pins — read it from there."""
    import restore_surface_fill as rs
    return rs.AMEND_SHA256


def amend_pin(amend_path, required):
    """The amendment file is a pinned input once a freeze is made from it: <file>.sha256 beside it
    must match; under --check it must also be AMEND_SHA256 in restore_surface_fill.py."""
    with open(real(amend_path), "rb") as f:
        hexd = sha256(f.read())
    pin = real(amend_path) + ".sha256"
    if os.path.isfile(pin):
        with open(pin, encoding="utf-8") as f:
            want = (f.read().split() or [""])[0]
        if want != hexd:
            raise Stop(f"--amend {amend_path}: sha256 {hexd[:16]}… != its .sha256 {(want or '(empty file)')[:16]}…")
        say(f"    amendment file sha256 {hexd} = its .sha256")
    elif required:
        raise Stop(f"--amend {amend_path}: no .sha256 beside it — the amendment file is a pinned input under --check")
    else:
        say(f"    amendment file sha256 {hexd} (no .sha256 beside it yet)")
    if required:
        code = pinned_amend()
        if code is not None and hexd != code:
            raise Stop(f"--amend {amend_path}: sha256 {hexd[:16]}… is not the pinned amendment file "
                       f"{code[:16]}… (AMEND_SHA256 in restore_surface_fill.py)")
        say("    amendment file = the pin in restore_surface_fill.py" if code
            else "    (no amendment pin set in restore_surface_fill.py)")
    return hexd


def expected_counts(a, n_ins, n_upd, n_rem=0):
    """(rows, inserts, updates, removes) the receipt expects: the 10/25 constants with --csv; with
    --from-restore, the report's own counts (+ the amendment file's; G0 already proved they are the diff's)."""
    if a.from_restore:
        return n_ins + n_upd + n_rem, n_ins, n_upd, n_rem
    return N_ROWS, dr.N_INSERT, dr.N_UPDATE, 0


def check_current(a, out):
    """--check: the frozen file must equal what --src yields today, byte for byte. Writes nothing."""
    say("=" * 78)
    say("snapshot_surface_fill --check — READ-ONLY on every database; writes NO file")
    for flag, p in (("--src", a.src), ("--prefill", a.prefill)):
        say(f"  {flag:9} {real(p)}  ({os.path.getsize(real(p)):,} bytes)")
    say(f"  frozen    {out}")
    say("=" * 78)
    say("F   the frozen file")
    frozen, hexd = read_snapshot(out)                 # its .sha256 must match first
    say(f"    sha256 {hexd}")
    pin = pinned()
    if pin is not None and hexd != pin:
        raise Stop(f"STALE SNAPSHOT — {out} is not the pinned snapshot (sha256 {hexd[:16]}… != "
                   f"pinned {pin[:16]}…) — nothing overwritten")
    say("    PASS — checksum file matches" + (", = the pin in restore_surface_fill.py" if pin
                                               else " (no pin set)"))
    with open(out, "rb") as f:
        frozen_bytes = f.read()
    if a.from_restore:
        try:
            report_pin(a.from_restore, required=True)
            if a.amend:
                amend_pin(a.amend, required=True)
        except Stop as e:
            raise Stop(f"STALE SNAPSHOT — {e} — nothing overwritten") from None
    csrc, cpre = dr.ro(a.src), dr.ro(a.prefill)
    try:
        try:
            rows, n_ins, n_upd, n_rem = build_rows(csrc, cpre, a.csv, a.from_restore, a.amend)
        except Stop as e:
            raise Stop(f"STALE SNAPSHOT — --src no longer yields the frozen fill ({e}) — "
                       "nothing overwritten") from None
    finally:
        csrc.close()
        cpre.close()
    data = render(rows)
    say("C   --src re-derived vs the frozen file, byte for byte")
    if data != frozen_bytes:
        diffs = stale_slots(frozen, rows)
        for k, what in diffs[:20]:
            say(f"    slot {k}: {what}")
        raise Stop(f"STALE SNAPSHOT — {len(diffs):,} slot(s) differ between --src and the frozen "
                   "file" + ("" if diffs else " (every row matches, the bytes do not)") +
                   " — nothing overwritten. A re-freeze is a ruling, never a way past this")
    say(f"    PASS — {len(rows):,} rows, identical bytes")
    x_rows, x_ins, x_upd, x_rem = expected_counts(a, n_ins, n_upd, n_rem)
    say("\nRECEIPT (expected | actual)")
    say(f"  rows                    {x_rows:,} | {len(rows):,}")
    say(f"  inserts / updates       {x_ins:,} / {x_upd:,} | {n_ins:,} / {n_upd:,}")
    if a.amend or n_rem:
        say(f"  removes                 {x_rem:,} | {n_rem:,}")
    say(f"  sha256                  {pin or '(no pin)'} | {hexd}")
    say("RESULT: SNAPSHOT CURRENT — the frozen file matches --src byte for byte; nothing written")
    return 0


def run(a, live=dr.LIVE):
    for flag, p in (("--src", a.src), ("--prefill", a.prefill)):
        if dr.is_live(p, live):
            raise Stop(f"{flag} {p} is the live database (or a file named bible.db) — refused. "
                       "Snapshot from a COPY.")
        if not os.path.isfile(real(p)):
            raise Stop(f"{flag} {p}: no such file")
    if real(a.src) == real(a.prefill):
        raise Stop("--src and --prefill must be two different files")
    if bool(a.csv) == bool(a.from_restore):
        raise Stop("give exactly one of --csv (the 10/25 approved list) or --from-restore (a "
                   "restore_surface_fill.py --report, DESIGN 9.120)")
    fill_src = a.csv or a.from_restore
    if not os.path.isfile(real(fill_src)):
        raise Stop(f"{'--csv' if a.csv else '--from-restore'} {fill_src}: no such file")
    out = real(a.out)
    if out.endswith(".db") or out in (real(a.src), real(a.prefill), real(fill_src)):
        raise Stop(f"--out {a.out} must be a new .tsv file, not a database or an input")
    if not out.endswith(".tsv"):
        raise Stop(f"--out {a.out} must end in .tsv")
    if a.check and a.replace:
        raise Stop("--check and --replace cannot be used together")
    if a.amend:
        if not a.from_restore:
            raise Stop("--amend goes with --from-restore (it is laid over a restore report)")
        if not os.path.isfile(real(a.amend)):
            raise Stop(f"--amend {a.amend}: no such file")
        if real(a.amend) in (out, real(a.from_restore)):
            raise Stop(f"--amend {a.amend} must be its own file, not --out or the report")
    if a.check:
        if not a.amend and pinned_amend() is not None:
            # DESIGN 9.269: the pinned snapshot was frozen with an amendment file, so its --check must name it
            raise Stop("--check needs --amend: the pinned snapshot was frozen with an amendment file "
                       "(AMEND_SHA256 in restore_surface_fill.py)")
        if not a.from_restore and pinned_report() is not None:
            # DESIGN 9.134 (reviewer finding 3): the pinned snapshot was made from a restore report
            # (R1), so its --check must name that report — a --csv check would skip the report pin
            raise Stop("--check needs --from-restore: the pinned snapshot was frozen from a restore "
                       "report (REPORT_SHA256 in restore_surface_fill.py)")
        if not os.path.isfile(out):
            raise Stop(f"--check: no frozen snapshot at --out {a.out} — nothing to verify. Copy the "
                       "second copy back; never re-freeze to get past this")
        return check_current(a, out)
    if os.path.exists(out) and not a.replace:
        raise Stop(f"--out {a.out} already exists — a frozen file is not overwritten "
                   "(pass --check to verify it against --src; --replace only to re-freeze by ruling)")

    say("=" * 78)
    say("snapshot_surface_fill — READ-ONLY on every database; writes only the snapshot + .sha256")
    for flag, p in (("--src", a.src), ("--prefill", a.prefill)):
        say(f"  {flag:9} {real(p)}  ({os.path.getsize(real(p)):,} bytes)")
    say("=" * 78)
    if a.from_restore:
        report_pin(a.from_restore, required=False)
        if a.amend:
            amend_pin(a.amend, required=False)
    csrc, cpre = dr.ro(a.src), dr.ro(a.prefill)
    try:
        rows, n_ins, n_upd, n_rem = build_rows(csrc, cpre, a.csv, a.from_restore, a.amend)
    finally:
        csrc.close()
        cpre.close()
    x_rows, x_ins, x_upd, x_rem = expected_counts(a, n_ins, n_upd, n_rem)
    if len(rows) != x_rows:
        raise Stop(f"{len(rows):,} rows, expect {x_rows:,}")

    data = render(rows)
    say("R   read-back control")
    if parse(data) != sorted(rows, key=lambda r: (r["verse_id"], r["position"])):
        raise Stop("R  the rendered file does not read back to the same rows")
    if render(parse(data)) != data:
        raise Stop("R  render(parse(file)) != file")
    say("    PASS — the file reads back value for value")

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(data)
    hexd = sha256(data)
    with open(out + ".sha256", "w", encoding="utf-8", newline="\n") as f:
        f.write(f"{hexd}  {os.path.basename(out)}\n")
    if read_snapshot(out)[0] != parse(data):
        raise Stop("R  the file on disk does not read back to the same rows")

    cls = {}
    for r in rows:
        cls[r["cls"]] = cls.get(r["cls"], 0) + 1
    say("\nRECEIPT (expected | actual)")
    say(f"  rows                    {x_rows:,} | {len(rows):,}")
    say(f"  inserts / updates       {x_ins:,} / {x_upd:,} | {n_ins:,} / {n_upd:,}")
    if a.amend or n_rem:
        say(f"  removes                 {x_rem:,} | {n_rem:,}")
    say(f"  distinct slots          {x_rows:,} | {len({(r['verse_id'], r['position']) for r in rows}):,}")
    say(f"  on name slots (is_pn=1) — | {sum(1 for r in rows if r['is_pn'] == 1):,}")
    say(f"  slots whose number repeats in the verse (k2_count > 1) — | "
        f"{sum(1 for r in rows if r['k2_count'] > 1):,}")
    say(f"  by class                {dict(sorted(cls.items()))}")
    say(f"  file   {out}  ({len(data):,} bytes)")
    say(f"  sha256 {hexd}")
    say("RESULT: SNAPSHOT WRITTEN — no database was written")
    return 0


def main(argv=None, live=dr.LIVE):
    ap = argparse.ArgumentParser(description="Freeze the abp_surface fill (read-only on databases).")
    for flag in ("--src", "--prefill", "--out"):
        ap.add_argument(flag, required=True)
    ap.add_argument("--csv", help="the 10/25 approved fill list (G0 vs the old slots)")
    ap.add_argument("--from-restore", metavar="REPORT",
                    help="a restore_surface_fill.py --report: G0 = the slots it placed, at their NEW "
                         "positions, counts from the report (DESIGN 9.120; the edition-upgrade re-freeze)")
    ap.add_argument("--amend", metavar="TSV",
                    help="a fill-amendment file laid over --from-restore (DESIGN 9.269): insert / update / "
                         "change / drop / remove rows at current positions; pinned as AMEND_SHA256")
    ap.add_argument("--replace", action="store_true",
                    help="overwrite an existing snapshot (re-freeze by ruling only)")
    ap.add_argument("--check", action="store_true",
                    help="verify the existing frozen file against --src; write nothing "
                         "(/rebuild-words step 1a)")
    a = ap.parse_args(argv)
    try:
        return run(a, live)
    except Stop as e:
        say(f"\nSTOPPED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
