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
        files += [(str(p.relative_to(BASE_DIR)), p) for p in sorted(d.glob("*.txt"))]
    n_abp = len(files)
    if n_abp != 66:
        sys.exit(f"ERROR: expected 66 ABP files, found {n_abp} — wrong tree?")

    bh = BASE_DIR / "bh_scrape.db"
    if not bh.is_file():
        sys.exit(f"ERROR: {bh} not found (run on PA).")
    files.append(("bh_scrape.db", bh))

    if not RAHLFS_DIR.is_dir():
        sys.exit(f"ERROR: Rahlfs dir missing: {RAHLFS_DIR} — feed required for the cert.")
    files += [(f"rahlfs/{p.name}", p) for p in sorted(RAHLFS_DIR.iterdir()) if p.is_file()]

    for p in TAGNT_FILES:
        if not p.is_file():
            sys.exit(f"ERROR: TAGNT file missing: {p} — feed required for the cert.")
        files.append((f"tagnt/{p.name}", p))
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
    print(f"\nPinned {len(entries)} files -> {MANIFEST}")


def cmd_verify():
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
