#!/usr/bin/env python3
"""confirm_numbered_ref_fix.py — READ-ONLY check for the spaced-numbered-book parser fix.

Proves the fix and proves it didn't move anything that already worked. Writes NOTHING (opens
bible.db ?mode=ro). PA-only (bible.db lives there).

    workon bible-env
    python scripts/confirm_numbered_ref_fix.py

What it shows:
  1. TARGETED — the two diadochos (G1240) refs the stress draws dropped, parsed + run through the
     citation gate the OLD way vs the NEW way. Expect: OLD logs them no-verse; NEW resolves them to
     2Ch 26:11 / 1Ch 18:17 and passes 2/2.
  2. GAINS — every stored lexica_def entry that now recovers a verse the old parser dropped, with the
     exact refs. These are the fix working — report them as gains, not regressions.
  3. INVARIANT — asserts NO citation that already resolved changes its book or testament (so an
     LXX-note OT/NT split can't silently flip). A clean run prints "no currently-resolving citation
     moved"; any violation is printed loudly and the script exits non-zero.
"""
import json, os, re, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_lexica_def as B

DB = os.path.expanduser("~/bible-db/bible.db")

# The OLD parser, frozen here for the before/after diff (the pre-2026-06-28 behavior: no normalize).
_OLD_RE = re.compile(r"\b(\d[A-Z][a-z]|[A-Z][a-z]{2})\s+(\d+):(\d+)")


def old_refs(text):
    seen, out = set(), []
    for bk, ch, vs in _OLD_RE.findall(text or ""):
        k = (bk, int(ch), int(vs))
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def testament(book):
    return "NT" if book in B.NT_BOOKS else "OT"


def main():
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    # ── 1. TARGETED: the two refs the diadochos stress draws dropped ────────────────────────────
    print("=" * 78)
    print("1. TARGETED — G1240 διάδοχος, the two refs the stress draws wrote spaced")
    print("=" * 78)
    sample = "The deputy (διάδοχος) appears in 2 Chr 26:11; compare 1 Chr 18:17."
    old = old_refs(sample)
    new = B.cited_refs(sample)
    og = B.run_citation_gate(conn, "G1240", old)
    ng = B.run_citation_gate(conn, "G1240", new)
    print(f"  prose: {sample}")
    print(f"  OLD parser refs: {[f'{b} {c}:{v}' for b, c, v in old]}")
    print(f"     gate: {og['pass']}/{og['total']} pass   (no-verse {og['noverse']}, real {og['real']})")
    print(f"  NEW parser refs: {[f'{b} {c}:{v}' for b, c, v in new]}")
    print(f"     gate: {ng['pass']}/{ng['total']} pass   (no-verse {ng['noverse']}, real {ng['real']})")
    ok = [f"{b} {c}:{v}" for b, c, v in new] == ["2Ch 26:11", "1Ch 18:17"] and ng["pass"] == 2
    print(f"  EXPECT 2Ch 26:11 / 1Ch 18:17, 2/2 pass  ->  {'OK' if ok else '**FAILED**'}")

    # ── 2. + 3. Sweep every stored entry: gains + the no-move invariant ─────────────────────────
    rows = conn.execute("SELECT strongs, lemma, def_json FROM lexica_def").fetchall()
    gains, violations = [], []
    for r in rows:
        sid = r["strongs"]
        if not sid.startswith("G"):          # gate keysets are Greek-tagged; skip any H entry
            continue
        try:
            raw = (json.loads(r["def_json"]).get("raw") or "")
        except Exception:
            continue
        if not raw:
            continue
        strict = B.strict_keyset(conn, sid)
        loose = B.loose_keyset(conn, sid)
        resolves = lambda ref: ref in strict or ref in loose
        old = old_refs(raw)
        new = B.cited_refs(raw)
        old_set = set(old)

        # GAINS: a ref that resolves now and was NOT present (verbatim) under the old parser.
        recovered = [ref for ref in new if resolves(ref) and ref not in old_set]
        if recovered:
            gains.append((sid, r["lemma"], recovered))

        # INVARIANT: every ref that ALREADY resolved (old parser) must be unchanged by the
        # normalizer — same book, therefore same testament. If not, it would move; flag it.
        for ref in old:
            if resolves(ref):
                b = ref[0]
                if B._norm_book(b) != b:
                    violations.append((sid, f"{b} {ref[1]}:{ref[2]}",
                                       f"{b}/{testament(b)} -> {B._norm_book(b)}"))

    print()
    print("=" * 78)
    print(f"2. GAINS — entries that recover a dropped verse ({len(gains)} entr{'y' if len(gains)==1 else 'ies'})")
    print("=" * 78)
    if not gains:
        print("  (none — no stored entry cited a spaced/long numbered ref)")
    for sid, lemma, recovered in gains:
        print(f"  {sid} {lemma}: +{len(recovered)}  ->  " +
              ", ".join(f"{b} {c}:{v}" for b, c, v in recovered))

    print()
    print("=" * 78)
    print("3. INVARIANT — nothing that already resolved may change book/testament")
    print("=" * 78)
    if not violations:
        print("  OK — no currently-resolving citation moved (OT/NT splits unchanged everywhere).")
    else:
        print(f"  **{len(violations)} VIOLATION(S)** — these already resolved and would move:")
        for sid, ref, change in violations:
            print(f"    {sid}: {ref}   {change}")

    conn.close()
    sys.exit(1 if (violations or not ok) else 0)


if __name__ == "__main__":
    main()
