#!/usr/bin/env python3
"""dump_family_source.py — READ-ONLY. The ABP SOURCE line is the arbiter.

For each exemplar verse, print four lines side by side so you can read off which
parser deviated (not judge taste):
  1. SOURCE  — the raw abp_texts line, brackets + order digits + G-numbers as stored
  2. PROSE   — verses.text (what load_abp_prose.clean_verse produced) [the trusted side]
  3. RECHECK — clean_verse(SOURCE) recomputed here, to CONFIRM verses.text == the parser
  4. WORDS   — the reader's reassembly (reorder_english port over the word rows)

A family self-adjudicates when the source is unambiguous (each bracket has distinct
digits, no nesting). AMBIGUOUS is flagged when a bracket repeats a digit or nests —
those need a printed-ABP tiebreak.

Usage (on PA, from ~/bible-db — needs abp_texts/ + bible.db):
  python3 scripts/dump_family_source.py bible.db
  python3 scripts/dump_family_source.py bible.db "Jer 48:1" "Mat 21:19"   # custom refs
  python3 scripts/dump_family_source.py --scan-brackets                   # unmatched-bracket scan

Survivor-set source adjudication (LOCAL, feed-only, no DB) — the certified 208/0/0 split:
  python3 scripts/dump_family_source.py --survivors --controls   # prove the detector fires BOTH verdicts
  python3 scripts/dump_family_source.py --survivors              # adjudicate AUDIT_reassembly_survivors.txt
  python3 scripts/dump_family_source.py --survivors <list.txt>   # custom "Book ch:v"-per-line list
"""
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_abp_prose import VERSE_RE, clean_verse, ABP_DIRS, G_NUM_RE
from reorder_english import get_english_order_words

# one exemplar per family (from the v2 --list), + the two named verses
DEFAULT = [
    ("Jer 48:1",  "forces + doubled-the (the arbiter case)"),
    ("Jer 19:15", "forces family"),
    ("Mat 16:16", "the-Christ family"),
    ("Rom 9:17",  "same family"),
    ("Gen 7:1",   "pronoun-fronting family"),
    ("Mat 26:16", "verb-particle 'up X' family"),
    ("Heb 10:8",  "paren-edge family"),
    ("Mat 21:19", "content-other apparatus leak (cited by G1096)"),
]

_DIGIT = re.compile(r"^\s*(\d+)")


def source_line(book, ch, vs):
    """Return the raw abp_texts text for a ref (the part after '(Book ch:v) '), or None."""
    for d in ABP_DIRS:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.txt")):
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    m = VERSE_RE.match(line.strip())
                    if m and m.group(1) == book and int(m.group(2)) == ch and int(m.group(3)) == vs:
                        return m.group(4)
    return None


def ambiguity(raw):
    """Flag a bracket group whose source notation can't self-adjudicate."""
    flags = []
    for grp in re.findall(r"\[([^\]]*)\]", raw or ""):
        if "[" in grp:
            flags.append("nested bracket")
        digits = [int(d.group(1)) for it in re.split(r"\s+(?=\d)", grp.strip())
                  if (d := _DIGIT.match(it))]
        dup = {x for x in digits if digits.count(x) > 1}
        if dup:
            flags.append(f"duplicate digit {sorted(dup)}")
    return flags


def words_reassembly(conn, book, ch, vs):
    row = conn.execute("SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
                       (book, ch, vs)).fetchone()
    if not row:
        return None
    words = [dict(r) for r in conn.execute(
        "SELECT english, bracket_id, greek_pos, position FROM words "
        "WHERE verse_id=? ORDER BY position", (row[0],))]
    seq = " ".join((w.get("english") or "") for w in get_english_order_words(words))
    return re.sub(r"\s+", " ", seq).strip()


def scan_brackets():
    """READ-ONLY. Every abp_texts source line whose brackets don't balance — an
    unmatched ']' is the malformed shape that leaks order digits into verses.text
    (Mat 21:19 class). Reports ref + the raw line so the leak class is fully known."""
    print("== unmatched-bracket scan of abp_texts (READ-ONLY) ==\n")
    n = 0
    for d in ABP_DIRS:
        if not d.exists():
            print(f"  ({d} not found)")
            continue
        for f in sorted(d.glob("*.txt")):
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    m = VERSE_RE.match(line.strip())
                    if not m:
                        continue
                    raw = m.group(4)
                    if raw.count("[") != raw.count("]"):
                        n += 1
                        print(f"  {m.group(1)} {m.group(2)}:{m.group(3)}  "
                              f"([={raw.count('[')} ]={raw.count(']')})")
                        print(f"    {raw}")
    print(f"\n  {n} verses with unmatched brackets.")


# ── Survivor-set source adjudication (the 208 word-order survivors) ────────────
# An INDEPENDENT source-order deriver: a second, from-scratch tokenizer that reads
# the source's OWN notation (non-bracket text verbatim; bracket items ordered by
# their leading digit), NOT a reuse of load_abp_prose.reorder_bracket. Same RULE,
# different code — so agreement CROSS-CHECKS the prose parser instead of assuming it.
# This is the tool that produced the certified 208/0/0 split (charter S9 DIAGNOSIS
# RESULT). Post-rebuild the gate re-runs it: with v2 at zero (rows==prose) AND this
# confirming prose==source, the 208 went to zero AGAINST SOURCE, not just prose.

_WS = re.compile(r"\s+")
# a stray order digit or lone Strong's 'G' left in prose = apparatus leak (prose-wrong)
_LEAK = re.compile(r"(?<!\w)\d|G(?=[\s.]|$)")
# repo-root default survivor list (one "Book ch:v" per line)
_SURVIVORS_DEFAULT = Path(__file__).resolve().parent.parent / "AUDIT_reassembly_survivors.txt"


def _strip_g(s):
    return G_NUM_RE.sub("", s)


def source_order(raw):
    """Independent derivation of source English reading order (no reorder_bracket)."""
    out, i, n = [], 0, len(raw)
    while i < n:
        if raw[i] == "[":
            j = raw.find("]", i)
            if j == -1:                       # malformed: no closing bracket
                out.append(_strip_g(raw[i + 1:]))
                break
            items = re.split(r"\s+(?=\d)", raw[i + 1:j].strip())
            parsed = []
            for it in items:
                m = re.match(r"(\d+)(.*)", it.strip())
                if m:
                    w = _strip_g(m.group(2)).strip()
                    if w:
                        parsed.append((int(m.group(1)), w))
            parsed.sort(key=lambda x: x[0])
            out.append(" ".join(w for _, w in parsed))
            i = j + 1
        else:
            k = raw.find("[", i)
            if k == -1:
                k = n
            out.append(_strip_g(raw[i:k]))
            i = k
    return _WS.sub(" ", " ".join(out)).strip()


def _words_only(s):                           # word ORDER only — ignore punctuation + spacing
    return re.findall(r"[a-z]+", s.lower())


def adjudicate(raw):
    """WORDS-WRONG | PROSE-WRONG | AMBIGUOUS for one source line. Returns (verdict, src, prose, why)."""
    balanced = raw.count("[") == raw.count("]")
    amb = ambiguity(raw)
    prose = clean_verse(raw)
    src = source_order(raw)
    if amb:
        return "AMBIGUOUS", src, prose, "; ".join(amb)
    if not balanced:
        return "PROSE-WRONG", src, prose, "unbalanced source brackets"
    if _LEAK.search(prose):
        return "PROSE-WRONG", src, prose, "apparatus left in prose"
    if _words_only(src) != _words_only(prose):
        return "PROSE-WRONG", src, prose, "independent source word-order != prose"
    return "WORDS-WRONG", src, prose, ""


# control set — the detector must FIRE on BOTH verdicts (a detector that only ever
# says WORDS-WRONG is the void-zero trap: reuse the production adjudicate(), no copy).
_SURV_CONTROLS = [
    ("Jer 48:1",  "WORDS-WRONG", "the LORD of the forces, the God of Israel"),
    ("Mat 16:16", "WORDS-WRONG", "the Christ, the son of the living God"),
    ("Gen 7:1",   "WORDS-WRONG", "I beheld you"),
    ("Rom 9:17",  "WORDS-WRONG", "this same thing"),
    ("Mat 26:16", "WORDS-WRONG", "he should deliver him up"),
    ("Mat 21:19", "PROSE-WRONG", None),   # malformed source bracket → the leak class MUST fire
]


def _ref_parts(ref):
    parts = ref.split()
    return " ".join(parts[:-1]), *(int(x) for x in parts[-1].split(":"))


def run_survivor_controls():
    print("== --survivors CONTROLS (adjudicator must fire BOTH verdicts) ==")
    ok = True
    for ref, want, frag in _SURV_CONTROLS:
        book, ch, vs = _ref_parts(ref)
        raw = source_line(book, ch, vs)
        if raw is None:
            print(f"  [MISS] {ref}: source line not found"); ok = False; continue
        verdict, src, prose, why = adjudicate(raw)
        good = verdict == want and (frag is None or frag in src)
        ok = ok and good
        print(f"  [{'FIRED' if good else 'FAIL '}] {ref}: got {verdict}, want {want}"
              + (f"  (expect ~'{frag}')" if frag else f"  ({why})"))
    print("  CONTROLS PASSED." if ok else "  CONTROLS FAILED — do not trust any survivor zero.")
    return 0 if ok else 1


def run_survivors(refs_file):
    path = Path(refs_file)
    if not path.exists():
        sys.exit(f"survivor list not found: {path}")
    refs = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    buckets = {"WORDS-WRONG": [], "PROSE-WRONG": [], "AMBIGUOUS": []}
    notfound = []
    for ref in refs:
        book, ch, vs = _ref_parts(ref)
        raw = source_line(book, ch, vs)
        if raw is None:
            notfound.append(ref); continue
        verdict, src, prose, why = adjudicate(raw)
        buckets[verdict].append((ref, why, src, prose))
    print(f"== survivor source-adjudication ({len(refs)} refs, from {path.name}) -- READ-ONLY ==")
    print(f"  WORDS-WRONG : {len(buckets['WORDS-WRONG'])}")
    print(f"  PROSE-WRONG : {len(buckets['PROSE-WRONG'])}")
    print(f"  AMBIGUOUS   : {len(buckets['AMBIGUOUS'])}")
    print(f"  not found   : {len(notfound)}")
    for tag in ("PROSE-WRONG", "AMBIGUOUS"):
        if buckets[tag]:
            print(f"\n-- {tag} (inspect each) --")
            for ref, why, src, prose in buckets[tag]:
                print(f"  {ref}  [{why}]\n     SRC  : {src}\n     PROSE: {prose}")
    if notfound:
        print("\nNOT FOUND:", ", ".join(notfound))


def main():
    args = sys.argv[1:]
    if "--scan-brackets" in args:
        scan_brackets()
        return
    if "--survivors" in args:
        if "--controls" in args:
            sys.exit(run_survivor_controls())
        # optional custom list path after --survivors
        idx = args.index("--survivors")
        nxt = args[idx + 1] if idx + 1 < len(args) and not args[idx + 1].startswith("--") else None
        run_survivors(nxt or _SURVIVORS_DEFAULT)
        return
    db = next((a for a in args if not a.startswith("--")), "bible.db")
    custom = [a for a in args[1:] if not a.startswith("--")]
    refs = [(r, "custom") for r in custom] if custom else DEFAULT

    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    print("== family source dump (READ-ONLY) — SOURCE line is the arbiter ==\n")
    for ref, label in refs:
        parts = ref.split()
        book = " ".join(parts[:-1])
        ch, vs = (int(x) for x in parts[-1].split(":"))
        raw = source_line(book, ch, vs)
        vt = conn.execute("SELECT text FROM verses WHERE book=? AND chapter=? AND verse=?",
                          (book, ch, vs)).fetchone()
        vt = vt[0] if vt else None
        print(f"=== {ref}   [{label}] ===")
        if raw is None:
            print("  SOURCE : (not found in abp_texts — check book abbrev / versification)\n")
            continue
        print(f"  SOURCE : {raw}")
        print(f"  PROSE  : {vt}")
        recheck = clean_verse(raw)
        flag = " (differs from verses.text!)" if recheck != vt else ""
        print(f"  RECHECK: {recheck}{flag}")
        print(f"  WORDS  : {words_reassembly(conn, book, ch, vs)}")
        amb = ambiguity(raw)
        print(f"  ARBITER: {'AMBIGUOUS -> printed-ABP tiebreak: ' + '; '.join(amb) if amb else 'self-adjudicates (unambiguous source)'}")
        print()
    conn.close()


if __name__ == "__main__":
    main()
