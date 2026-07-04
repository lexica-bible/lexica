#!/usr/bin/env python3
"""cert_reparse_harness.py — Tier A re-parse harness (ABP certification, Session 1).

Runs the FULL production build path from the pinned feeds into a scratch copy,
then diffs the scratch words table against the live one row-by-row. Every
mismatch is either our bug (Tier A) or the footprint of a rebuild script whose
effect isn't reproducible from source — the decommission-blocking list.

What it does, in order:
  1. Verifies the feed pin (cert_manifest.py verify) — abort on drift.
  2. Pre-checks the feeds the build would otherwise silently skip
     (Rahlfs + TAGNT + the three folded finishing modules). A run without them
     is INVALID, not "partial".
  3. Runs the production build (build_words_from_abp.py) — it snapshots the
     live db into <live>.new and rebuilds words there. The live file is opened
     READ-ONLY throughout; only the .new copy is written.
  4. Runs the production tail (finish_rebuild.sh) on the copy, unless --no-tail.
  5. Diffs live vs copy using compare_words.load (the proven production
     comparator — same key, same bracket normalisation), is_pn excluded
     (set later by import_tipnr per the Session 0 decision; with the tail on
     it matches anyway, but the exclusion keeps --no-tail runs comparable).
  6. Reconciles its own counts against independent measurements before
     trusting the diff, then writes cert_report_summary.txt + cert_deltas.tsv.

Usage (on PA, from ~/bible-db; expect normal-rebuild runtime):
    python3 scripts/cert_reparse_harness.py                # full path
    python3 scripts/cert_reparse_harness.py --no-tail      # parser-only scratch
    python3 scripts/cert_reparse_harness.py --diff-only    # re-diff an existing .new
    python3 scripts/cert_reparse_harness.py --keep-scratch # don't remind to delete

Writes ONLY: <live>.new (the scratch), cert_report_summary.txt, cert_deltas.tsv.
Exit 0 = zero deltas; exit 1 = deltas found (see the reports); exit 2 = invalid run.
"""
import sqlite3
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from compare_words import load, _COLS                      # the production comparator
from build_words_from_abp import RAHLFS_DIR, TAGNT_FILES, BASE_DIR

LIVE    = str(BASE_DIR / "bible.db")
SCRATCH = LIVE + ".new"
BH      = str(BASE_DIR / "bh_scrape.db")
SUMMARY = BASE_DIR / "cert_report_summary.txt"
DELTAS  = BASE_DIR / "cert_deltas.tsv"

# Diff columns = the production comparator's set minus is_pn (Session 0 decision).
DIFF_COLS = [c for c in _COLS if c != "is_pn"]
_IPN = _COLS.index("is_pn")


def die(msg, code=2):
    print(f"INVALID RUN: {msg}")
    sys.exit(code)


def sh(cmd, **kw):
    print(f"\n── {' '.join(cmd)} ──", flush=True)
    return subprocess.run(cmd, cwd=BASE_DIR, text=True, **kw)


def precheck():
    # Manifest gate
    r = sh([sys.executable, "scripts/cert_manifest.py", "verify"])
    if r.returncode != 0:
        die("feed pin drifted — re-baseline deliberately or find what changed.")
    # Feeds the build silently skips (a skip = a differently-built corpus)
    if not RAHLFS_DIR.is_dir():
        die(f"Rahlfs dir missing: {RAHLFS_DIR}")
    for p in TAGNT_FILES:
        if not p.is_file():
            die(f"TAGNT file missing: {p}")
    for mod in ("lxx_align", "fill_blank_strongs", "fix_pn_subject_merge",
                "fix_italic_heads"):
        try:
            __import__(mod)
        except ImportError as e:
            die(f"build finishing module not importable ({mod}): {e}")
    for f in (LIVE, BH):
        if not Path(f).is_file():
            die(f"{f} not found (run on PA)")


def build(no_tail):
    if Path(SCRATCH).exists():
        die(f"{SCRATCH} already exists — a rebuild may be staged. Remove it "
            "yourself if it's disposable, then re-run (the harness never deletes it).")
    # The production build: snapshots live -> SCRATCH, rebuilds words there.
    r = sh([sys.executable, "scripts/build_words_from_abp.py", LIVE, BH],
           input="rebuild\n", capture_output=True)
    sys.stdout.write(r.stdout or "")
    sys.stderr.write(r.stderr or "")
    if r.returncode != 0:
        die("build failed — see output above.")
    out = r.stdout or ""
    if ("⚠️" in out or "split skipped" in out or "re-clean skipped" in out):
        die("build skipped a feed or finishing step (see the warning above) — "
            "the scratch is not the production corpus.")
    # The build must also see every source verse: "Verses skipped: 0" (a skipped
    # verse = a (book,ch,vs) in the source with no verses row — the Heb 13 class).
    for line in out.splitlines():
        if line.strip().startswith("Verses skipped:"):
            if line.split(":")[1].strip() != "0":
                die(f"build reported {line.strip()} — source verses with no "
                    "verses row (Heb 13 class); fix before certifying.")
    if no_tail:
        print("\n(--no-tail: skipping finish_rebuild.sh — parser-only scratch; "
              "expect large PN/patch deltas by design.)")
        return
    r = sh(["bash", "scripts/finish_rebuild.sh", SCRATCH])
    if r.returncode != 0:
        die("finish_rebuild.sh failed on the scratch.")


def _count(db):
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    n = conn.execute("SELECT count(*) FROM words").fetchone()[0]
    conn.close()
    return n


def diff():
    print("\nLoading live …", flush=True)
    live = load(LIVE)
    print("Loading scratch …", flush=True)
    new = load(SCRATCH)

    # RECONCILIATION — no count is trusted until an independent measurement
    # agrees with it (the L9 discipline).
    n_live, n_new = _count(LIVE), _count(SCRATCH)
    if len(live) != n_live:
        die(f"live load dropped rows: comparator {len(live):,} vs COUNT(*) {n_live:,} "
            "(a words row whose verse_id has no verses row?)")
    if len(new) != n_new:
        die(f"scratch load dropped rows: comparator {len(new):,} vs COUNT(*) {n_new:,}")

    only_live = sorted(k for k in live if k not in new)
    only_new  = sorted(k for k in new if k not in live)
    both      = [k for k in live if k in new]
    if len(only_live) + len(both) != len(live) or len(only_new) + len(both) != len(new):
        die("partition arithmetic failed — comparator keys inconsistent.")

    changed = []          # (key, col, live_val, new_val, hint)
    by_col: dict = {}
    for k in both:
        (lc, lb), (nc, nb) = live[k], new[k]
        for ci, col in enumerate(_COLS):
            if ci == _IPN:
                continue
            if lc[ci] != nc[ci]:
                hint = ""
                if (col == "english" and lc[ci] and nc[ci]
                        and lc[ci] == nc[ci].replace("--", "—")):
                    hint = "emdash"          # fix_emdash.py footprint (not in the build)
                changed.append((k, col, lc[ci], nc[ci], hint))
                by_col[col] = by_col.get(col, 0) + 1
        if lb != nb:
            changed.append((k, "bracket_rank", lb, nb, ""))
            by_col["bracket_rank"] = by_col.get("bracket_rank", 0) + 1

    total = len(only_live) + len(only_new) + len(changed)
    lines = [
        "cert_reparse_harness report",
        f"live rows:    {n_live:,}",
        f"scratch rows: {n_new:,}",
        f"rows only in live:    {len(only_live):,}   (rebuild would DROP these)",
        f"rows only in scratch: {len(only_new):,}   (rebuild would ADD these)",
        f"cell-level changes:   {len(changed):,}",
        "",
        "changes by column:",
    ] + [f"  {c:14} {n:,}" for c, n in sorted(by_col.items(), key=lambda x: -x[1])] + [
        "",
        f"TOTAL deltas: {total:,}",
        "These deltas are the decommission-blocking list (Session 2 adjudicates);"
        " none are fixed by this harness.",
    ]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with DELTAS.open("w", encoding="utf-8") as f:
        f.write("book\tchapter\tverse\tposition\tkind\tcolumn\tlive\tscratch\thint\n")
        for k in only_live:
            f.write(f"{k[0]}\t{k[1]}\t{k[2]}\t{k[3]}\tonly_live\t\t\t\t\n")
        for k in only_new:
            f.write(f"{k[0]}\t{k[1]}\t{k[2]}\t{k[3]}\tonly_scratch\t\t\t\t\n")
        for k, col, a, b, hint in changed:
            f.write(f"{k[0]}\t{k[1]}\t{k[2]}\t{k[3]}\tchanged\t{col}\t{a}\t{b}\t{hint}\n")

    print("\n" + "\n".join(lines))
    print(f"\nReports: {SUMMARY.name} + {DELTAS.name}")
    return total


def main():
    args = sys.argv[1:]
    no_tail = "--no-tail" in args
    if "--diff-only" not in args:
        precheck()
        build(no_tail)
    elif not Path(SCRATCH).exists():
        die(f"--diff-only but {SCRATCH} not found.")
    total = diff()
    if "--keep-scratch" not in args:
        print(f"\nScratch left at {SCRATCH} — delete it when done (rm {SCRATCH}); "
              "the harness never deletes files.")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
