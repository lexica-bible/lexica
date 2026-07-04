#!/usr/bin/env python3
"""
backup_db.py - safe, rotating, VERIFIED backups of every live SQLite database on PA.

Why this exists: the live databases are NOT in git (too large) and are managed directly
on PA. A careless session has blanked bible.db before. This is the floor: a daily,
verified copy of every db, kept OUTSIDE the repo folder so a session that nukes
~/bible-db can't take the backups with it.

WHAT IT BACKS UP: every *.db in the source dir (default ~/bible-db) - bible.db, notes.db,
study.db (hand-authored argument graphs - NOT replayable from any build script, the single
most irreplaceable file), esv/niv/heb/news.db, bh_scrape.db. Auto-discovered, so a new db
is covered automatically. Skips the .bak/.new/.blank/-wal/-shm sidecars.

HOW (no torn copies): uses SQLite's online backup (Connection.backup) - consistent even
while the web app is writing, and it folds in the WAL. NEVER a plain cp (which would miss
-wal/-shm and give a torn file). Each fresh copy is then VERIFIED with PRAGMA quick_check;
a copy that isn't "ok" is deleted and the last good one is KEPT (a bad backup never rotates
out a good one). Verified copies are gzipped (except the newest, kept raw for instant
restore), set read-only (chmod 0444) as cheap hardening against deletion/overwrite, and a
tiny <name>.<stamp>.info manifest (date, WAL mode, quick_check, table row counts) is written
beside each so `list` is instant without decompressing.

USAGE:
  python3 scripts/backup_db.py                 # back up all dbs (default)
  python3 scripts/backup_db.py --list          # show every kept backup + row counts
  python3 scripts/backup_db.py --keep 14       # how many to keep per db (default 14)
  python3 scripts/backup_db.py --src ~/bible-db --out ~/db_backups
  python3 scripts/backup_db.py --raw 2         # how many newest kept uncompressed (default 1)

RESTORE (under stress, the short version):
  python3 scripts/backup_db.py --list          # pick the stamp you want
  gunzip -c ~/db_backups/bible.db.<stamp>.db.gz > ~/bible-db/bible.db.new   # (or cp if raw)
  cd ~/bible-db && mv bible.db bible.db.bak-$(date +%F) && rm -f bible.db-wal bible.db-shm \\
      && mv bible.db.new bible.db && touch /var/www/www_lexica_bible_wsgi.py

PA scheduled task (daily, same idea as health_check):
  cd ~/bible-db && python3 scripts/backup_db.py >> ~/db_backups/backup.log 2>&1
"""
import argparse
import gzip
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# sidecars / transient files that are never a "live db" to back up
_SKIP_SUFFIX = (".bak", ".new", ".blank")
_SKIP_CONTAIN = ("-wal", "-shm", "-journal")


def discover_dbs(src: Path) -> list[Path]:
    out = []
    for p in sorted(src.glob("*.db")):
        n = p.name
        if any(n.endswith(s) for s in _SKIP_SUFFIX):
            continue
        if any(c in n for c in _SKIP_CONTAIN):
            continue
        out.append(p)
    return out


def _table_counts(db: Path) -> dict:
    """Return {table: rowcount} for a db copy. Read-only open."""
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        counts = {}
        for (name,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall():
            try:
                counts[name] = conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            except sqlite3.Error:
                counts[name] = -1
        return counts
    finally:
        conn.close()


def _online_backup(src: Path, dest: Path) -> str:
    """Consistent copy of a live db via SQLite's backup API (folds in the WAL).
    Returns the SOURCE db's journal mode (so the manifest records whether the LIVE
    db is WAL). Flips the copy to rollback-journal mode so it leaves no -wal/-shm
    litter in the backup dir."""
    s = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    d = sqlite3.connect(str(dest))
    try:
        src_jm = s.execute("PRAGMA journal_mode").fetchone()[0]
        s.backup(d)                              # snapshot - safe even while the app writes
        d.execute("PRAGMA journal_mode=DELETE")  # backups don't need WAL; no -wal/-shm sidecars
        return src_jm
    finally:
        d.close()
        s.close()


def _force_unlink(p: Path) -> None:
    """Delete a file even if we set it read-only (chmod 0444 above)."""
    try:
        os.chmod(p, 0o644)
    except OSError:
        pass
    try:
        p.unlink()
    except OSError:
        pass


def _quick_check(db: Path) -> str:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        return conn.execute("PRAGMA quick_check").fetchone()[0]
    finally:
        conn.close()


def _write_manifest(info: Path, db_name: str, when: str, jm: str, qc: str,
                    size: int, counts: dict) -> None:
    lines = [f"db: {db_name}", f"when: {when}", f"journal_mode: {jm}",
             f"quick_check: {qc}", f"size_bytes: {size}", "counts:"]
    for t, c in sorted(counts.items()):
        lines.append(f"  {t}: {c}")
    info.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _stamps_for(out: Path, stem: str) -> list[tuple[str, Path]]:
    """All kept backups for a db stem, newest first: (stamp, path-to-.db-or-.db.gz)."""
    found = {}
    for p in out.glob(f"{stem}.*.db*"):
        if p.suffix == ".info" or "-wal" in p.name or "-shm" in p.name:
            continue                                  # never treat a sidecar as a backup
        # name = <stem>.<stamp>.db  or  <stem>.<stamp>.db.gz
        rest = p.name[len(stem) + 1:]
        stamp = rest.split(".db")[0]
        found[stamp] = p
    return sorted(found.items(), key=lambda kv: kv[0], reverse=True)


def _chmod_ro(p: Path) -> None:
    try:
        os.chmod(p, 0o444)
    except OSError:
        pass


def backup_all(src: Path, out: Path, keep: int, raw: int) -> int:
    out.mkdir(parents=True, exist_ok=True)
    dbs = discover_dbs(src)
    if not dbs:
        print(f"No databases found in {src}")
        return 1

    free = shutil.disk_usage(out).free
    total = sum(p.stat().st_size for p in dbs)
    print(f"Backing up {len(dbs)} db(s) -> {out}")
    print(f"  free space {free/1e9:.1f} GB; live dbs total {total/1e9:.2f} GB\n")
    if free < total * 2:
        print("  !!  low free space for a full rotation - older copies are gzipped, "
              "but check `du -sh` if this warns repeatedly.\n")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    when = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bad = 0
    for srcdb in dbs:
        stem = srcdb.name                      # keep ".db" in the stem (bible.db.<stamp>.db)
        dest = out / f"{stem}.{stamp}.db"
        try:
            jm = _online_backup(srcdb, dest)
            qc = _quick_check(dest)
            counts = _table_counts(dest)
        except sqlite3.Error as e:
            print(f"  XX  {stem}: backup FAILED ({e}) - last good copy kept.")
            if dest.exists():
                _force_unlink(dest)
            bad += 1
            continue

        if qc != "ok":
            print(f"  XX  {stem}: quick_check = {qc!r} - copy discarded, last good kept.")
            _force_unlink(dest)
            bad += 1
            continue

        size = dest.stat().st_size
        _write_manifest(out / f"{stem}.{stamp}.info", stem, when, jm, qc, size, counts)
        key = max(counts.values()) if counts else 0
        print(f"  OK  {stem}: ok ({jm}), {len(counts)} tables, ~{key:,} rows in largest, "
              f"{size/1e6:.1f} MB")
        _chmod_ro(dest)
        _rotate(out, stem, keep, raw)

    print()
    if bad:
        print(f"!!  {bad} db(s) failed to back up cleanly - see above. Exit 1.")
        return 1
    # Success stamp — the loudness guard. The nightly task can die silently (disk-full,
    # Jul 2-4 2026); this file only updates on a FULLY clean run, and cert_manifest.py
    # verify complains when it goes stale (>25h), somewhere JP actually looks.
    (out / "last_success.txt").write_text(
        datetime.now().isoformat(timespec="seconds") + "\n", encoding="utf-8")
    print("All backups verified ok.")
    return 0


def _rotate(out: Path, stem: str, keep: int, raw: int) -> None:
    """Keep the newest `keep` backups for this db; gzip all but the newest `raw`;
    delete the rest (with their manifests). The newest good copy is never deleted."""
    items = _stamps_for(out, stem)
    # gzip older verified copies (skip the newest `raw`, skip already-gz)
    for idx, (st, path) in enumerate(items):
        if idx < raw or path.suffix == ".gz":
            continue
        gz = path.with_suffix(path.suffix + ".gz")
        try:
            with open(path, "rb") as fi, gzip.open(gz, "wb") as fo:
                shutil.copyfileobj(fi, fo)
            _force_unlink(path)
            _chmod_ro(gz)
        except OSError as e:
            print(f"    (gzip skipped for {path.name}: {e})")
    # delete beyond `keep`
    items = _stamps_for(out, stem)
    for st, path in items[keep:]:
        for p in (path, out / f"{stem}.{st}.info"):
            if p.exists():
                _force_unlink(p)


def list_backups(out: Path) -> int:
    if not out.is_dir():
        print(f"No backup dir yet at {out}")
        return 1
    infos = sorted(out.glob("*.info"))
    if not infos:
        print(f"No backups in {out}")
        return 0
    print(f"Backups in {out}:\n")
    by_db: dict[str, list] = {}
    for info in infos:
        meta = {}
        counts = {}
        in_counts = False
        for ln in info.read_text(encoding="utf-8").splitlines():
            if ln == "counts:":
                in_counts = True
                continue
            if in_counts and ln.startswith("  "):
                k, v = ln.strip().split(":", 1)
                counts[k] = v.strip()
            elif ":" in ln:
                k, v = ln.split(":", 1)
                meta[k] = v.strip()
        by_db.setdefault(meta.get("db", "?"), []).append((meta, counts, info))
    for db in sorted(by_db):
        print(f"  {db}")
        for meta, counts, info in sorted(by_db[db], key=lambda x: x[0].get("when", ""), reverse=True):
            gz = (info.with_suffix(".db.gz").exists())
            tag = "gz" if gz else "raw"
            # headline count: verses for bible, else the biggest table
            head = counts.get("verses") or (max(counts.items(), key=lambda kv: int(kv[1] or 0))[1] if counts else "?")
            print(f"      {meta.get('when','?'):<20} {tag:>3}  {meta.get('quick_check','?'):>3}  "
                  f"{int(meta.get('size_bytes',0))/1e6:>7.1f} MB  key-rows {head}")
        print()
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(Path.home() / "bible-db"), help="dir holding the live dbs")
    ap.add_argument("--out", default=str(Path.home() / "db_backups"), help="backup dir (outside the repo)")
    ap.add_argument("--keep", type=int, default=14, help="backups to keep per db")
    ap.add_argument("--raw", type=int, default=1, help="newest N kept uncompressed for instant restore")
    ap.add_argument("--list", action="store_true", help="list kept backups + row counts")
    args = ap.parse_args()

    out = Path(args.out).expanduser()
    if args.list:
        sys.exit(list_backups(out))
    sys.exit(backup_all(Path(args.src).expanduser(), out, args.keep, args.raw))


if __name__ == "__main__":
    main()
