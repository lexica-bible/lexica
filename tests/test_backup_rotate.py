#!/usr/bin/env python3
"""backup_db.py compression guard — the 2026-10-25 damaged-backup lesson.

On 10/25 the account hit its disk quota while the nightly was gzipping the 10/24
bible.db copy. The old code left a cut-short .gz under the real backup name, kept
quiet about it (one log line), and stamped the run a success. Same thing had
happened 7/2 and 7/6. This file locks the fix, using the REAL backup_db code:

  1. normal compression: .gz reads back byte-identical, raw removed, no .part left
  2. disk full mid-compression: raw kept, NO .gz and NO .part left, failure counted
  3. a whole backup run with disk full mid-compression FAILS (exit 1, no success
     stamp -> the freshness alarm fires); a clean run still passes and stamps
  4. a raw + cut-short .gz pair left by the old code (today's PA state): the raw
     wins, gets compressed again, and the bad .gz is replaced by a good one
  5. a .part left by a killed run is never treated as a backup, and is cleared
  6. aging out a stamp removes every file of it (raw, .gz, .info)

Pure stdlib, temp folders only — never touches a real backup folder.
Run:  python tests/test_backup_rotate.py
"""
import builtins
import errno
import gzip
import io
import os
import shutil
import sqlite3
import stat
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import backup_db  # noqa: E402

fails = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok ' if ok else 'FAIL'}  {label}: {got!r}" + ("" if ok else f" (want {want!r})"))
    if not ok:
        fails.append(label)


def gz_reads_clean(p: Path) -> bool:
    """The health_check sweep's own read: stream the whole file."""
    try:
        with gzip.open(p, "rb") as f:
            while f.read(1 << 20):
                pass
        return True
    except Exception:
        return False


class _QuotaFile:
    """A file that runs out of room after `limit` bytes (errno 122, as on PA)."""
    def __init__(self, f, limit):
        self._f, self._n, self._limit = f, 0, limit

    def write(self, b):
        self._n += len(b)
        if self._n > self._limit:
            raise OSError(errno.EDQUOT, "Disk quota exceeded")
        return self._f.write(b)

    def __getattr__(self, a):
        return getattr(self._f, a)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._f.close()


class disk_full:
    """Make backup_db's compression writes hit 'Disk quota exceeded' part-way."""
    def __init__(self, limit=50_000):
        self.limit = limit

    def __enter__(self):
        # patch the builtin itself, so the fault fires however the code opens the
        # file (gzip.open uses builtins.open too) - the old code is caught by it
        self.real = real = builtins.open

        def fake_open(p, mode="r", *a, **k):
            f = real(p, mode, *a, **k)
            if "w" in mode and str(p).endswith((".gz", ".part")):
                return _QuotaFile(f, self.limit)
            return f
        builtins.open = fake_open
        return self

    def __exit__(self, *exc):
        builtins.open = self.real


def _rm_tree(d):
    def onerr(func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    shutil.rmtree(d, onerror=onerr)


def _names(d: Path):
    return sorted(p.name for p in d.iterdir())


def _seed_raw(out: Path, stem: str, stamp: str, data: bytes) -> Path:
    p = out / f"{stem}.{stamp}.db"
    p.write_bytes(data)
    (out / f"{stem}.{stamp}.info").write_text("x\n", encoding="utf-8")
    return p


def test_normal_and_disk_full():
    print("1-2. compression: normal, then disk full part-way")
    stem = "bible.db"
    data = os.urandom(400_000)          # random = barely compresses, so writes are real
    d = Path(tempfile.mkdtemp())
    try:
        _seed_raw(d, stem, "20261024-133029", data)
        _seed_raw(d, stem, "20261025-133030", data)
        with redirect_stdout(io.StringIO()):
            failed = backup_db._rotate(d, stem, 3, 1)
        gz = d / f"{stem}.20261024-133029.db.gz"
        check("normal: failures", failed, 0)
        check("normal: raw removed", (d / f"{stem}.20261024-133029.db").exists(), False)
        check("normal: .gz byte-identical", gzip.open(gz).read() == data, True)
        check("normal: no .part left", any(n.endswith(".part") for n in _names(d)), False)
    finally:
        _rm_tree(d)

    d = Path(tempfile.mkdtemp())
    try:
        raw = _seed_raw(d, stem, "20261024-133029", data)
        _seed_raw(d, stem, "20261025-133030", data)
        buf = io.StringIO()
        with disk_full(), redirect_stdout(buf):
            failed = backup_db._rotate(d, stem, 3, 1)
        check("disk full: failures counted", failed, 1)
        check("disk full: raw kept byte-identical", raw.read_bytes() == data, True)
        check("disk full: no .gz under the real name",
              (d / f"{stem}.20261024-133029.db.gz").exists(), False)
        check("disk full: no .part left", any(n.endswith(".part") for n in _names(d)), False)
        check("disk full: says so loudly", "compression FAILED" in buf.getvalue(), True)
    finally:
        _rm_tree(d)


def _small_db(p: Path):
    c = sqlite3.connect(str(p))
    c.execute("CREATE TABLE verses (id INTEGER PRIMARY KEY, t TEXT)")
    c.executemany("INSERT INTO verses (t) VALUES (?)", [(os.urandom(200).hex(),) for _ in range(500)])
    c.commit()
    c.close()


def test_whole_run():
    print("3. a whole backup run: disk full mid-compression must FAIL the run")
    for full in (True, False):
        src, out = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
        try:
            _small_db(src / "bible.db")
            old = _seed_raw(out, "bible.db", "20200101-000000", (src / "bible.db").read_bytes())
            buf = io.StringIO()
            with redirect_stdout(buf):
                if full:
                    with disk_full(limit=1000):
                        rc = backup_db.backup_all(src, out, 7, 1)
                else:
                    rc = backup_db.backup_all(src, out, 7, 1)
            tag = "disk full" if full else "clean"
            check(f"{tag}: exit code", rc, 1 if full else 0)
            check(f"{tag}: success stamp written", (out / "last_success.txt").exists(), not full)
            check(f"{tag}: older copy still raw", old.exists(), full)
            check(f"{tag}: older copy .gz reads clean",
                  gz_reads_clean(out / "bible.db.20200101-000000.db.gz"), not full)
        finally:
            _rm_tree(src)
            _rm_tree(out)


def test_legacy_pair_and_part():
    print("4-6. old-code leftovers: raw + cut-short .gz pair, stray .part, aging out")
    stem = "bible.db"
    data = os.urandom(300_000)
    d = Path(tempfile.mkdtemp())
    try:
        good_gz = gzip.compress(data)
        _seed_raw(d, stem, "20261025-133030", data)
        _seed_raw(d, stem, "20261024-133029", data)
        (d / f"{stem}.20261024-133029.db.gz").write_bytes(good_gz[: len(good_gz) // 3])  # cut short
        (d / f"{stem}.20261023-133031.db.gz").write_bytes(good_gz)
        (d / f"{stem}.20261023-133031.info").write_text("x\n", encoding="utf-8")
        (d / f"{stem}.20261022-133000.db.gz.part").write_bytes(b"junk")   # a killed run
        picks = dict(backup_db._stamps_for(d, stem))
        check("pair: raw wins over the cut-short .gz", picks["20261024-133029"].suffix, ".db")
        check("stray .part is never a backup", "20261022-133000" in picks, False)
        with redirect_stdout(io.StringIO()):
            failed = backup_db._rotate(d, stem, 3, 1)
        check("pair: failures", failed, 0)
        check("pair: bad .gz replaced by a good one",
              gz_reads_clean(d / f"{stem}.20261024-133029.db.gz"), True)
        check("pair: raw removed after the good .gz", (d / f"{stem}.20261024-133029.db").exists(), False)
        check("stray .part cleared", any(n.endswith(".part") for n in _names(d)), False)

        # aging out: put a raw + .gz pair at the oldest slot; keep=2 must remove all of it
        _seed_raw(d, stem, "20261020-133000", data)
        (d / f"{stem}.20261020-133000.db.gz").write_bytes(good_gz[:100])
        with redirect_stdout(io.StringIO()):
            backup_db._rotate(d, stem, 2, 1)
        left = [n for n in _names(d) if "20261020" in n or "20261023" in n]
        check("aging out removes every file of the stamp", left, [])
    finally:
        _rm_tree(d)


def main():
    test_normal_and_disk_full()
    test_whole_run()
    test_legacy_pair_and_part()
    if fails:
        print(f"\n{len(fails)} FAILURE(S): " + ", ".join(fails))
        return 1
    print("\nAll backup compression-guard checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
