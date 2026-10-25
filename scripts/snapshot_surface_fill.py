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

The snapshot holds ABP text (printed Greek forms + ABP English): it stays OUT of the public repo
(.gitignore) — PA keeps it in the fixture folder; a second copy goes to the local fixture folder.

--check  (the /rebuild-words step 1a mode, added 2026-10-25, charter §9): the frozen file already
exists — verify it, write NOTHING. Its .sha256 must match, it must be the snapshot pinned in
restore_surface_fill.py (SNAPSHOT_SHA256), and re-deriving the rows from --src (a fresh copy of live)
must give the frozen file BYTE FOR BYTE. Pass -> "SNAPSHOT CURRENT". Anything else -> STOPPED: STALE
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


def build_rows(csrc, cpre, csv_path):
    new_side, old_side, writes, ins, upd, vold = dr.g0(csrc, cpre, csv_path)
    vids = {v for v, _ in new_side}
    words = word_rows(csrc, vids)
    say("O   every fill slot has exactly one word row in --src")
    rows, orphans, dupes = [], [], []
    for (vid, pos), (form, translit) in sorted(new_side.items()):
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
        w = writes[(vid, pos)]
        old = old_side.get((vid, pos))           # updates only (an insert slot had no row)
        if (w["action"] == "update") != (old is not None):
            raise Stop(f"slot {(vid, pos)}: action {w['action']} but pre-fill row {old!r}")
        b, c, v = vold[vid]
        rows.append(dict(verse_id=vid, book=b, chapter=c, verse=v, position=pos,
                         action=w["action"], cls=w["cls"], form=form, translit=translit,
                         old_form=old[0] if old else None, old_translit=old[1] if old else None,
                         strongs=s, strongs_base=sb, english=e, english_head=eh, is_pn=pn,
                         k2_ordinal=same.index(pos), k2_count=len(same)))
    if orphans or dupes:
        raise Stop(f"{len(orphans)} fill slot(s) with no word row (e.g. {orphans[:3]}), "
                   f"{len(dupes)} on a duplicate position (e.g. {dupes[:3]})")
    say(f"    PASS — {len(rows):,} slots, each on one word row")
    return rows, len(ins), len(upd)


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
    csrc, cpre = dr.ro(a.src), dr.ro(a.prefill)
    try:
        try:
            rows, n_ins, n_upd = build_rows(csrc, cpre, a.csv)
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
    say("\nRECEIPT (expected | actual)")
    say(f"  rows                    {N_ROWS:,} | {len(rows):,}")
    say(f"  inserts / updates       {dr.N_INSERT:,} / {dr.N_UPDATE:,} | {n_ins:,} / {n_upd:,}")
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
    if not os.path.isfile(real(a.csv)):
        raise Stop(f"--csv {a.csv}: no such file")
    out = real(a.out)
    if out.endswith(".db") or out in (real(a.src), real(a.prefill), real(a.csv)):
        raise Stop(f"--out {a.out} must be a new .tsv file, not a database or an input")
    if not out.endswith(".tsv"):
        raise Stop(f"--out {a.out} must end in .tsv")
    if a.check and a.replace:
        raise Stop("--check and --replace cannot be used together")
    if a.check:
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
    csrc, cpre = dr.ro(a.src), dr.ro(a.prefill)
    try:
        rows, n_ins, n_upd = build_rows(csrc, cpre, a.csv)
    finally:
        csrc.close()
        cpre.close()
    if len(rows) != N_ROWS:
        raise Stop(f"{len(rows):,} rows, expect {N_ROWS:,}")

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
    say(f"  rows                    {N_ROWS:,} | {len(rows):,}")
    say(f"  inserts / updates       {dr.N_INSERT:,} / {dr.N_UPDATE:,} | {n_ins:,} / {n_upd:,}")
    say(f"  distinct slots          {N_ROWS:,} | {len({(r['verse_id'], r['position']) for r in rows}):,}")
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
    for flag in ("--src", "--prefill", "--csv", "--out"):
        ap.add_argument(flag, required=True)
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
