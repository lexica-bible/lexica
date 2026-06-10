#!/usr/bin/env python3
"""compare_words.py — READ-ONLY. Proves two bible.db copies hold the SAME words.

Built for the single-pass rebuild: build the OLD way (current build + the full
fix_*.py chain) into one copy, build the NEW way (single self-correcting pass) into
another, and compare. IDENTICAL = the fold faithfully reproduced the old end state.

It fingerprints every word by its VERSE COORDINATES + position (not the row id, which
differs between independent builds) over all display columns. bracket_id is NORMALISED
to a per-verse first-appearance rank, so a different internal bracket NUMBER with the
same GROUPING compares equal (a real grouping change still shows up as a rank change).

Usage:
  python3 scripts/compare_words.py bible.db                  # one fingerprint + row count
  python3 scripts/compare_words.py old.db --compare new.db   # full diff, exit 1 if differ
  python3 scripts/compare_words.py old.db --compare new.db --limit 40
"""
import hashlib
import sqlite3
import sys

ARGS = sys.argv[1:]
DB = next((a for a in ARGS if not a.startswith("--")), "bible.db")
OTHER = None
if "--compare" in ARGS:
    i = ARGS.index("--compare")
    rest = [a for a in ARGS[i + 1:] if not a.startswith("--")]
    OTHER = rest[0] if rest else None
LIMIT = 30
if "--limit" in ARGS:
    j = ARGS.index("--limit")
    if j + 1 < len(ARGS):
        LIMIT = int(ARGS[j + 1])

# Display columns that define the word (id excluded — it's not content).
_COLS = ("english", "english_head", "strongs", "strongs_base", "greek_pos",
         "italic", "italic_words", "smcap_words", "morph", "lemma", "is_pn")


def load(db):
    """{(book,chapter,verse,position): (col-tuple, bracket_rank)} for the whole table.
    bracket_rank = order of first appearance of the word's bracket within its verse
    (None outside a bracket) — id-independent grouping signature."""
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cols = {r[1] for r in conn.execute("PRAGMA table_info(words)")}
    sel = ", ".join(c if c in cols else f"NULL AS {c}" for c in _COLS)
    rows = conn.execute(
        f"SELECT v.book, v.chapter, v.verse, w.position, w.bracket_id, {sel} "
        f"FROM words w JOIN verses v ON v.id = w.verse_id "
        f"ORDER BY v.book, v.chapter, v.verse, w.position"
    ).fetchall()
    conn.close()

    out = {}
    rank_in_verse = {}     # (book,ch,vs) -> {bracket_id: rank}
    for r in rows:
        vkey = (r["book"], r["chapter"], r["verse"])
        bid = r["bracket_id"]
        brank = None
        if bid is not None:
            seen = rank_in_verse.setdefault(vkey, {})
            if bid not in seen:
                seen[bid] = len(seen) + 1
            brank = seen[bid]
        key = (r["book"], r["chapter"], r["verse"], r["position"])
        out[key] = (tuple(r[c] for c in _COLS), brank)
    return out


def fingerprint(data):
    h = hashlib.md5()
    for key in sorted(data, key=lambda k: (str(k[0]), k[1], k[2], k[3])):
        h.update(repr((key, data[key])).encode("utf-8"))
    return h.hexdigest()


def refstr(key):
    return f"{key[0]} {key[1]}:{key[2]} pos{key[3]}"


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    a = load(DB)
    if OTHER is None:
        print(f"words fingerprint [{DB}]: {fingerprint(a)}")
        print(f"rows: {len(a)}")
        return 0

    b = load(OTHER)
    fa, fb = fingerprint(a), fingerprint(b)
    print(f"OLD [{DB}]   rows={len(a)}  fingerprint={fa}")
    print(f"NEW [{OTHER}] rows={len(b)}  fingerprint={fb}")
    if fa == fb:
        print("\n[IDENTICAL] the single pass reproduces the old end state exactly.")
        return 0

    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    common = set(a) & set(b)
    diff = [k for k in common if a[k] != b[k]]
    diff.sort(key=lambda k: (str(k[0]), k[1], k[2], k[3]))

    print(f"\n[DIFFERENT]")
    print(f"  rows only in OLD: {len(only_a)}")
    print(f"  rows only in NEW: {len(only_b)}")
    print(f"  rows that differ: {len(diff)}\n")

    def show(label, keys):
        if not keys:
            return
        print(f"-- {label} (first {min(LIMIT, len(keys))} of {len(keys)}) --")
        for k in keys[:LIMIT]:
            print(f"  {refstr(k)}")
            if k in a and k in b:
                ca, cb = a[k], b[k]
                for name, va, vb in zip(_COLS, ca[0], cb[0]):
                    if va != vb:
                        print(f"      {name}: OLD={va!r}  NEW={vb!r}")
                if ca[1] != cb[1]:
                    print(f"      bracket_rank: OLD={ca[1]}  NEW={cb[1]}")
        print()

    show("only in OLD", only_a)
    show("only in NEW", only_b)
    show("differing rows", diff)
    return 1


if __name__ == "__main__":
    sys.exit(main())
