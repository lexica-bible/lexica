#!/usr/bin/env python3
"""cert_manifest.py — pin the three ABP-certification feeds by SHA-256.

The Tier A certification claim is "this DB is certified against THESE sources on
PA" — this manifest is what "these" means. It hashes every input file the words
build reads:
  * the 66 ABP source .txt files (abp_texts/, in git)
  * bh_scrape.db (PA-only)
  * the Rahlfs-1935 data files (~/LXX-Rahlfs-1935, PA-only)
  * the two TAGNT files (~, PA-only)

Usage (on PA, from ~/bible-db):
    python3 scripts/cert_manifest.py build     # write cert_manifest.json
    python3 scripts/cert_manifest.py verify    # re-hash + diff; exit 1 on any drift

`build` REFUSES to run while any ABP source file contains a non-verse line
(the L1 editing-artifact class) — the pin happens only on clean sources, per the
Session 0 ordering decision. `verify` is the gate every future session runs
before trusting the cert baseline.

READ-ONLY on every source; writes only cert_manifest.json.
"""
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
# Reuse the build's OWN constants + verse regex — never a second copy of the
# paths or the line format (a stale copy is how a scan lies).
from build_words_from_abp import (
    _VERSE_RE, ABP_OT_DIR, ABP_NT_DIR, RAHLFS_DIR, TAGNT_FILES, BASE_DIR,
)
# The exact Rahlfs files the build reads — the ONE list, owned by the loader
# itself (lxx_align.py), so the pin can't drift from what the build consumes.
# (v1 of this tool swept RAHLFS_DIR's top level, which holds only SUBFOLDERS, and
# silently pinned zero Rahlfs files — the pin-gap JP caught 2026-07-04. The
# explicit list + the count floor below make that failure impossible to miss.)
from lxx_align import RAHLFS_FILES_REQUIRED, RAHLFS_FILE_SURFACE

MANIFEST = BASE_DIR / "cert_manifest.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def feed_files():
    """Every input file of the words build, as (label, Path). Missing feeds are
    a hard error — a manifest that silently pins fewer files certifies nothing."""
    files = []
    for d in (ABP_OT_DIR, ABP_NT_DIR):
        if not d.is_dir():
            sys.exit(f"ERROR: ABP source dir missing: {d}")
        files += [(p.relative_to(BASE_DIR).as_posix(), p) for p in sorted(d.glob("*.txt"))]
    n_abp = len(files)
    if n_abp != 66:
        sys.exit(f"ERROR: expected 66 ABP files, found {n_abp} — wrong tree?")

    bh = BASE_DIR / "bh_scrape.db"
    if not bh.is_file():
        sys.exit(f"ERROR: {bh} not found (run on PA).")
    files.append(("bh_scrape.db", bh))

    if not RAHLFS_DIR.is_dir():
        sys.exit(f"ERROR: Rahlfs dir missing: {RAHLFS_DIR} — feed required for the cert.")
    for rel in RAHLFS_FILES_REQUIRED:
        p = RAHLFS_DIR / rel
        if not p.is_file():
            sys.exit(f"ERROR: Rahlfs feed file missing: {p} — required for the cert "
                     "(its absence changes the built corpus).")
        files.append((f"rahlfs/{rel}", p))
    p = RAHLFS_DIR / RAHLFS_FILE_SURFACE
    if p.is_file():                       # optional for the WORDS build; pinned when present
        files.append((f"rahlfs/{RAHLFS_FILE_SURFACE}", p))

    for p in TAGNT_FILES:
        if not p.is_file():
            sys.exit(f"ERROR: TAGNT file missing: {p} — feed required for the cert.")
        files.append((f"tagnt/{p.name}", p))

    # Count floor — a manifest that pins fewer files than the build reads certifies
    # nothing. 66 ABP + bh_scrape + 4 required Rahlfs + 2 TAGNT = 73 minimum.
    if len(files) < 73:
        sys.exit(f"ERROR: only {len(files)} feed files found (< 73 floor) — a feed "
                 "is missing; refusing to pin/verify a partial baseline.")
    return files


def nonverse_lines():
    """The L1-class census: non-blank ABP source lines that are not verse headers.
    Control: fired on exactly the 4 known artifact lines before the L1 cleanup."""
    bad = []
    for d in (ABP_OT_DIR, ABP_NT_DIR):
        for p in sorted(d.glob("*.txt")):
            for n, line in enumerate(
                p.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                if line.strip() and not _VERSE_RE.match(line.strip()):
                    bad.append((p.name, n, line.strip()[:60]))
    return bad


def cmd_build():
    bad = nonverse_lines()
    if bad:
        print(f"REFUSING to pin: {len(bad)} non-verse line(s) in the ABP sources "
              "(L1 class). Clean them first, then re-run build:")
        for name, n, txt in bad:
            print(f"  {name}:{n}  {txt}")
        sys.exit(1)
    entries = {}
    for label, path in feed_files():
        entries[label] = {"sha256": _sha256(path), "bytes": path.stat().st_size}
        print(f"  {label}")
    doc = {
        "created": date.today().isoformat(),
        "note": "ABP certification feed pin (Tier A). Verify with: "
                "python3 scripts/cert_manifest.py verify",
        "files": entries,
    }
    MANIFEST.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    # Per-feed reconciliation line — the reader should see all three feeds counted,
    # not just a total (a missing feed must be visible at a glance).
    n_abp = sum(1 for k in entries if k.startswith("abp_texts"))
    n_rah = sum(1 for k in entries if k.startswith("rahlfs/"))
    n_tag = sum(1 for k in entries if k.startswith("tagnt/"))
    print(f"\nPinned {len(entries)} files -> {MANIFEST}")
    print(f"  feeds: ABP {n_abp} · bh_scrape 1 · Rahlfs {n_rah} · TAGNT {n_tag}")


def backup_guard_message(stamp: Path | None = None) -> str | None:
    """The ONE copy of the backup-staleness detection (nightly backup failed
    SILENTLY Jul 2-4 2026, disk-full). backup_db.py stamps last_success.txt on a
    fully clean run. Returns a warning string, or None when fresh. Shared by
    verify below (WARN-only) and cert_invariants.py (a hard FAIL there)."""
    if stamp is None:
        stamp = Path.home() / "db_backups" / "last_success.txt"
    try:
        if not stamp.is_file():
            return ("no success stamp at ~/db_backups/last_success.txt — the nightly "
                    "backup has not completed cleanly since the guard landed. "
                    "Check ~/db_backups/backup.log.")
        from datetime import datetime
        age = datetime.now() - datetime.fromisoformat(stamp.read_text().strip())
        hours = age.total_seconds() / 3600
        if hours > 25:
            return (f"last clean backup was {hours:.0f}h ago (>25h) — the nightly "
                    "task is failing. Check ~/db_backups/backup.log + disk space.")
    except (OSError, ValueError) as e:
        return f"could not read the success stamp ({e})."
    return None


def _backup_staleness_check():
    """WARN-ONLY wrapper for verify — never changes verify's exit code (that stays
    about feed drift). The invariant suite makes the same message a hard failure."""
    msg = backup_guard_message()
    if msg:
        print("!! BACKUP GUARD: " + msg)


def cmd_verify():
    _backup_staleness_check()
    if not MANIFEST.is_file():
        sys.exit(f"ERROR: {MANIFEST} not found — run 'build' first.")
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pinned = doc["files"]
    current = {label: path for label, path in feed_files()}
    problems = []
    for label, meta in pinned.items():
        p = current.pop(label, None)
        if p is None:
            problems.append(f"MISSING  {label} (pinned, not on disk)")
            continue
        h = _sha256(p)
        if h != meta["sha256"]:
            problems.append(f"CHANGED  {label}")
    for label in current:
        problems.append(f"EXTRA    {label} (on disk, not pinned)")
    if problems:
        print(f"BASELINE DRIFT — {len(problems)} problem(s) vs {doc['created']} pin:")
        for x in problems:
            print("  " + x)
        sys.exit(1)
    print(f"Baseline intact: {len(pinned)} files match the {doc['created']} pin.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "build":
        cmd_build()
    elif cmd == "verify":
        cmd_verify()
    else:
        sys.exit("usage: cert_manifest.py build|verify")
