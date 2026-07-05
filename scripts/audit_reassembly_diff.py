#!/usr/bin/env python3
"""audit_reassembly_diff.py — READ-ONLY reassembly-diff invariant (cert-style).

THE IDEA
  verses.text is the clean, correct English prose. The word rows should carry the
  SAME words (each token parked on some slot). Reassemble a verse from its word
  rows and compare the bag of tokens against verses.text. Any difference = a
  word-row defect (verses.text is trusted; the words table is on trial).

WHY A BAG (multiset), NOT an ordered string
  ABP bracket groups are stored in Greek order and reordered into English at read
  time (56-library-order-logic.jsx). So a plain position-order string does NOT
  equal verses.text on bracket-reordered verses — it would false-positive on every
  one of them. The two real defect classes the user found are both BAG differences,
  immune to ordering:
    - dup-gloss   (Jer 48:1 "of the the forces") -> an EXTRA copy of a word
    - punct-shift (Jer 48:1 ";" parked one slot early) -> same words, the
                   punctuation moved to a different token
  Pure word-ORDER mistakes (a stranded determiner) are NOT caught here on purpose —
  those have their own invariant (split-flip, cert_invariants check 2).

TWO TIERS so reorder + systematic formatting can't hide the real count
  - CONTENT tier (EVERY verse, reorder-immune): compare bare words (punctuation
    stripped, lowercased). A miss = a word genuinely missing/duplicated/wrong.
    dup-gloss lives here. This is the trustworthy count.
  - PUNCT tier (NON-bracketed verses ONLY): bare words match but the full tokens
    differ -> a mark is attached to the wrong token. On a BRACKETED verse this
    can't be judged from the bag: reorder legitimately relocates a clause-final
    mark (John 1:1 rows store "...the word." in Greek order; prose reads
    "...was God."), so those verses are EXCLUDED from the punct count and the
    exclusion is reported (no silent cap). On a plain verse source order == English
    order, so a shifted mark IS a real defect (the Jer 48:1 ";" class, when the
    slots involved are non-bracketed).

Usage (on PA, from ~/bible-db):
  python3 scripts/audit_reassembly_diff.py bible.db            # corpus report
  python3 scripts/audit_reassembly_diff.py bible.db --verse "Jer 48:1"
  python3 scripts/audit_reassembly_diff.py --controls          # proof-of-fire (no db)

READ-ONLY: opens the db mode=ro; never writes. No fixes — this only counts.
"""
import re
import sqlite3
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

# ── tokenizing ────────────────────────────────────────────────────────────────

# Apparatus that can ride in stored text but is not a word: bracket marks, ABP's
# superscript order digits never live in `english` (separate column) but strip any
# stray just in case. The em-dash class is normalized so "--" == "—".
_BRACKETS = str.maketrans({"[": " ", "]": " "})
_WS = re.compile(r"\s+")
# leading/trailing punctuation to peel for the bare-word form (keep internal ' and -)
_EDGE = re.compile(r"^[^\w']+|[^\w']+$")


def _norm_text(s: str) -> str:
    if not s:
        return ""
    s = s.translate(_BRACKETS)
    s = s.replace("--", "—")
    return _WS.sub(" ", s).strip()


def tokens(s: str):
    """Whitespace tokens of a normalized string (full tokens, punctuation kept)."""
    n = _norm_text(s)
    return n.split(" ") if n else []


def bare(tok: str) -> str:
    """A token with edge punctuation peeled + lowercased. '' if pure punctuation."""
    return _EDGE.sub("", tok).lower()


# ── the core diff for one verse ────────────────────────────────────────────────

def diff_verse(word_english_list, verse_text, has_bracket=False):
    """word_english_list = the `english` cell of each word row (position order).
    has_bracket = does the verse contain any bracket group (reorder relocates
    clause marks, so the punct tier is not judgeable from the bag on these).
    Returns None if the verse reassembles clean, else a dict describing the hit:
      {klass, content_extra, content_missing, tok_extra, tok_missing}
    klass in {'dup-gloss', 'content-other', 'punct-shift'}.
    """
    w_toks = []
    for e in word_english_list:
        w_toks.extend(tokens(e or ""))
    t_toks = tokens(verse_text or "")

    full_w, full_t = Counter(w_toks), Counter(t_toks)
    if full_w == full_t:
        return None  # perfect reassembly

    # bare-word bags (punctuation-immune, drop pure-punct tokens)
    bare_w = Counter(b for b in (bare(t) for t in w_toks) if b)
    bare_t = Counter(b for b in (bare(t) for t in t_toks) if b)

    content_extra = bare_w - bare_t        # words in rows but not text
    content_missing = bare_t - bare_w      # words in text but not rows
    tok_extra = full_w - full_t
    tok_missing = full_t - full_w

    if not content_extra and not content_missing:
        # bare words match -> a punctuation-attachment difference only.
        if has_bracket:
            return None                    # reorder relocation, not judgeable — exclude
        klass = "punct-shift"              # plain verse: source order == English order
    elif not content_missing and content_extra and \
            all(bare_t[w] > 0 for w in content_extra):
        klass = "dup-gloss"                # every extra word is a repeat of one already present
    else:
        klass = "content-other"            # genuine missing / wrong / added word

    return {
        "klass": klass,
        "content_extra": dict(content_extra),
        "content_missing": dict(content_missing),
        "tok_extra": dict(tok_extra),
        "tok_missing": dict(tok_missing),
    }


# ── corpus scan (importable, cert-style like find_flips) ───────────────────────

def reassembly_hits(conn, stats=None):
    """READ-ONLY. One dict per verse that fails to reassemble. Shared by the CLI
    here and (once proven) cert_invariants.py so the two can't drift.
    stats (optional dict) is filled with {'bracket_punct_excluded': N} — bracketed
    verses whose ONLY difference was a punct-attachment the reorder explains."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT v.id AS vid, v.book, v.chapter, v.verse, v.text AS vtext,
                  w.position, w.english, w.bracket_id
           FROM verses v JOIN words w ON w.verse_id = v.id
           ORDER BY v.id, w.position"""
    ).fetchall()

    by_verse = defaultdict(list)
    has_bracket = defaultdict(bool)
    meta = {}
    for r in rows:
        by_verse[r["vid"]].append(r["english"])
        if r["bracket_id"] is not None:
            has_bracket[r["vid"]] = True
        meta.setdefault(r["vid"], (r["book"], r["chapter"], r["verse"], r["vtext"]))

    hits = []
    excluded = 0
    for vid, engs in by_verse.items():
        book, ch, vs, vtext = meta[vid]
        d = diff_verse(engs, vtext, has_bracket[vid])
        if d:
            d["ref"] = f"{book} {ch}:{vs}"
            d["book"] = book
            hits.append(d)
        elif has_bracket[vid]:
            # bracketed + returned clean: could be truly clean OR a reorder-relocated
            # mark we excluded. Re-test with has_bracket=False to tell them apart.
            if diff_verse(engs, vtext, False):
                excluded += 1
    if stats is not None:
        stats["bracket_punct_excluded"] = excluded
    return hits


# ── v2: ORDER-AWARE reassembly (reader English order vs verses.text) ───────────
# v1 (above) compares BAGS, so it is blind to a bag-neutral misplacement (Jer 48:1's
# "the" pulled a slot forward) and to bracket-internal punct shifts. v2 reassembles
# the verse in the reader's OWN English reading order (the proven-equivalent port of
# getEnglishOrderWords) and diffs the token SEQUENCE against verses.text. It is a
# SUPERSET of v1: every bag defect still shows, plus displacements. Trustworthy only
# because reorder_english is proven byte-equal to the JS (tests/test_reorder_port.py)
# AND 135/136 clean fixture verses reassemble exactly to prose.
import difflib
from reorder_english import get_english_order_words


def reassemble_ordered(words):
    """Token sequence of the verse in the reader's English reading order."""
    seq = " ".join((w.get("english") or "") for w in get_english_order_words(words))
    return tokens(seq)


def diff_verse_v2(words, verse_text):
    """Ordered token diff of reader-order reassembly vs verses.text.
    Returns None if identical, else {klass, ops, content_extra, content_missing}.
    klass: 'dup-gloss' / 'content-other' (bag differs) or 'displaced' (bag equal,
    order/punct differs — the Jer 48:1 class)."""
    w_seq = reassemble_ordered(words)
    t_seq = tokens(verse_text or "")
    if w_seq == t_seq:
        return None

    bare_w = Counter(b for b in (bare(t) for t in w_seq) if b)
    bare_t = Counter(b for b in (bare(t) for t in t_seq) if b)
    content_extra = bare_w - bare_t
    content_missing = bare_t - bare_w

    if not content_extra and not content_missing:
        # Same bag of words -> a pure re-ordering. Split it: if the BARE-word
        # sequences (punctuation + pure-mark tokens dropped) are identical, only
        # punctuation moved to a neighbor (cosmetic, the em-dash/comma family);
        # if they differ, a real WORD sits in the wrong slot (the Jer 48:1 class).
        bw = [b for b in (bare(t) for t in w_seq) if b]
        bt = [b for b in (bare(t) for t in t_seq) if b]
        klass = "punct-position" if bw == bt else "word-order"
    elif not content_missing and content_extra and \
            all(bare_t[w] > 0 for w in content_extra):
        klass = "dup-gloss"
    else:
        klass = "content-other"

    # a compact human-readable diff of what moved (rows -> text)
    ops = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, w_seq, t_seq).get_opcodes():
        if tag == "equal":
            continue
        ops.append(f"{tag}: rows[{' '.join(w_seq[i1:i2])}] -> "
                   f"text[{' '.join(t_seq[j1:j2])}]")
    return {"klass": klass, "ops": ops,
            "content_extra": dict(content_extra), "content_missing": dict(content_missing)}


def reassembly_hits_v2(conn):
    """READ-ONLY. One dict per verse whose reader-order reassembly != verses.text."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT v.id AS vid, v.book, v.chapter, v.verse, v.text AS vtext,
                  w.position, w.english, w.bracket_id, w.greek_pos
           FROM verses v JOIN words w ON w.verse_id = v.id
           ORDER BY v.id, w.position"""
    ).fetchall()
    by_verse = defaultdict(list)
    meta = {}
    for r in rows:
        by_verse[r["vid"]].append({"english": r["english"], "bracket_id": r["bracket_id"],
                                    "greek_pos": r["greek_pos"], "position": r["position"]})
        meta.setdefault(r["vid"], (r["book"], r["chapter"], r["verse"], r["vtext"]))
    hits = []
    for vid, ws in by_verse.items():
        book, ch, vs, vtext = meta[vid]
        d = diff_verse_v2(ws, vtext)
        if d:
            d["ref"] = f"{book} {ch}:{vs}"
            d["book"] = book
            hits.append(d)
    return hits


def run_report_v2(db, list_all=False):
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    hits = reassembly_hits_v2(conn)
    total = conn.execute("SELECT count(*) FROM verses").fetchone()[0]
    conn.close()
    by_class = Counter(h["klass"] for h in hits)
    by_book = Counter(h["book"] for h in hits)
    print(f"== reassembly-diff V2 (order-aware) on {db} (READ-ONLY) ==")
    print(f"   verses scanned : {total:,}")
    print(f"   total hits     : {len(hits):,}\n")
    print("   by class:")
    for k in ("dup-gloss", "content-other", "word-order", "punct-position"):
        print(f"     {k:<15} {by_class.get(k, 0):>6,}")
    print("\n   by book (all, canonical-ish by count):")
    for book, n in by_book.most_common():
        print(f"     {book:<6} {n:>6,}")
    if list_all:
        print("\n   every hit:")
        for h in hits:
            print(f"     [{h['klass']:<13}] {h['ref']:<12} {' ; '.join(h['ops'])}")
    else:
        print("\n   sample (first 4 of each class; --list for all):")
        shown = Counter()
        for h in hits:
            if shown[h["klass"]] >= 4:
                continue
            shown[h["klass"]] += 1
            print(f"     [{h['klass']:<13}] {h['ref']:<12} {' ; '.join(h['ops'])}")
    return len(hits)


# ── report ─────────────────────────────────────────────────────────────────────

def _fmt_counter(c):
    return ", ".join(f"{k!r}×{v}" if v > 1 else f"{k!r}" for k, v in c.items())


def print_verse(conn, ref, v2=False):
    conn.row_factory = sqlite3.Row
    parts = ref.split()
    book = " ".join(parts[:-1])
    ch, vs = parts[-1].split(":")
    row = conn.execute("SELECT id, text FROM verses WHERE book=? AND chapter=? AND verse=?",
                       (book, int(ch), int(vs))).fetchone()
    if not row:
        print(f"  {ref}: verse not found")
        return
    wrows = conn.execute("SELECT english, bracket_id, greek_pos, position FROM words "
                         "WHERE verse_id=? ORDER BY position", (row["id"],)).fetchall()
    words = [dict(r) for r in wrows]
    engs = [w["english"] for w in words]
    print(f"  === {ref}{' (V2 order-aware)' if v2 else ''} ===")
    print(f"  verses.text : {row['text']!r}")
    if v2:
        print(f"  reassembled : {' '.join(reassemble_ordered(words))!r}")
        d = diff_verse_v2(words, row["text"])
        if not d:
            print("  RESULT: clean reassembly (no hit)")
            return
        print(f"  RESULT: HIT [{d['klass']}]")
        for op in d["ops"]:
            print(f"    {op}")
        return
    print(f"  row tokens  : {tokens(' '.join(e or '' for e in engs))}")
    d = diff_verse(engs, row["text"])
    if not d:
        print("  RESULT: clean reassembly (no hit)")
        return
    print(f"  RESULT: HIT [{d['klass']}]")
    if d["content_extra"]:
        print(f"    content extra (in rows, not text)   : {_fmt_counter(Counter(d['content_extra']))}")
    if d["content_missing"]:
        print(f"    content missing (in text, not rows) : {_fmt_counter(Counter(d['content_missing']))}")
    if d["tok_extra"]:
        print(f"    token extra                         : {_fmt_counter(Counter(d['tok_extra']))}")
    if d["tok_missing"]:
        print(f"    token missing                       : {_fmt_counter(Counter(d['tok_missing']))}")


def run_report(db):
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    stats = {}
    hits = reassembly_hits(conn, stats)
    total_verses = conn.execute("SELECT count(*) FROM verses").fetchone()[0]
    conn.close()

    by_class = Counter(h["klass"] for h in hits)
    by_book = Counter(h["book"] for h in hits)

    print(f"== reassembly-diff on {db} (READ-ONLY) ==")
    print(f"   verses scanned : {total_verses:,}")
    print(f"   total hits     : {len(hits):,}\n")
    print("   by class:")
    for k in ("dup-gloss", "content-other", "punct-shift"):
        print(f"     {k:<14} {by_class.get(k, 0):>6,}")
    print(f"\n   bracketed verses excluded from the punct tier "
          f"(reorder relocates the mark, not judgeable from the bag): "
          f"{stats.get('bracket_punct_excluded', 0):,}")
    print("\n   by book (top 25 by hit count):")
    for book, n in by_book.most_common(25):
        print(f"     {book:<6} {n:>6,}")

    print("\n   sample hits (first 3 of each class):")
    shown = Counter()
    for h in hits:
        if shown[h["klass"]] >= 3:
            continue
        shown[h["klass"]] += 1
        bits = []
        if h["content_extra"]:
            bits.append(f"+content {_fmt_counter(Counter(h['content_extra']))}")
        if h["content_missing"]:
            bits.append(f"-content {_fmt_counter(Counter(h['content_missing']))}")
        if not h["content_extra"] and not h["content_missing"]:
            bits.append(f"punct +{_fmt_counter(Counter(h['tok_extra']))} "
                        f"-{_fmt_counter(Counter(h['tok_missing']))}")
        print(f"     [{h['klass']:<11}] {h['ref']:<12} {' | '.join(bits)}")
    return len(hits)


# ── controls — proof-of-fire on the Jer 48:1 shape (no db needed) ──────────────

def run_controls():
    print("== reassembly-diff CONTROLS (must FIRE on defect, go QUIET on the fix) ==")
    ok = True

    # Jer 48:1 AS-IS (defective word rows). verses.text is the clean prose.
    clean_text = ("Against Moab thus said the LORD of the forces the God of Israel; "
                  "Woe to Nebo, for it was ruined; Kiriathaim was shamed, was taken "
                  "the fortification and was shamed.")
    # (a) dup-gloss: 'of the' + 'the' + 'forces,' stores 'of the the forces'
    # (b) punct-shift: ';' parked on 'fortification' instead of after 'shamed'
    bad_rows = ["Against", "Moab", "thus", "said", "the", "LORD",
                "of the", "the", "forces", "the", "God", "of", "Israel;",
                "Woe", "to", "Nebo,", "for", "it", "was", "ruined;",
                "Kiriathaim", "was", "shamed,", "was", "taken",
                "the", "fortification;", "and", "was", "shamed."]
    d = diff_verse(bad_rows, clean_text)
    fired_dup = d is not None and "the" in d["content_extra"]
    # the punct-shift hides behind the content hit above; prove it on an isolated pair
    d_punct = diff_verse(["the", "fortification;", "and", "was", "shamed."],
                         "the fortification and was shamed;")
    fired_punct = d_punct is not None and d_punct["klass"] == "punct-shift"
    print(f"  [{'FIRED' if fired_dup else 'VOID '}] dup-gloss on Jer 48:1 rows "
          f"-> extra {_fmt_counter(Counter(d['content_extra'])) if d else '(none)'}")
    print(f"  [{'FIRED' if fired_punct else 'VOID '}] punct-shift on the ';' pair "
          f"-> {d_punct['klass'] if d_punct else '(clean)'}")
    ok = ok and fired_dup and fired_punct

    # hand-corrected copy of the SAME verse must go quiet
    good_rows = ["Against", "Moab", "thus", "said", "the", "LORD",
                 "of", "the", "forces", "the", "God", "of", "Israel;",
                 "Woe", "to", "Nebo,", "for", "it", "was", "ruined;",
                 "Kiriathaim", "was", "shamed,", "was", "taken",
                 "the", "fortification", "and", "was", "shamed."]
    d_good = diff_verse(good_rows, clean_text)
    quiet = d_good is None
    print(f"  [{'QUIET' if quiet else 'STILL FIRING'}] corrected Jer 48:1 rows "
          f"-> {'clean' if quiet else d_good}")
    ok = ok and quiet

    # a bracket-reordered verse (same words, Greek order in the rows) must NOT fire.
    # The clause-final "." is relocated by the reorder (rows "...word." vs text
    # "...God."), so ONLY the has_bracket exclusion keeps it quiet — proving the gate.
    reorder_rows = ["God", "was", "the", "word."]     # Greek order
    reorder_text = "the word was God."                # English prose
    d_reorder = diff_verse(reorder_rows, reorder_text, has_bracket=True)
    reorder_quiet = d_reorder is None
    print(f"  [{'QUIET' if reorder_quiet else 'FALSE-POSITIVE'}] bracket reorder "
          f"(Greek-order rows vs English text) -> {'immune' if reorder_quiet else d_reorder}")
    ok = ok and reorder_quiet

    print(f"\n{'ALL CONTROLS PASSED — fires on defect, quiet on fix + reorder.' if ok else 'CONTROL FAILURE — do not trust this invariant.'}")
    return 0 if ok else 1


def run_controls_v2():
    """v2 proof-of-fire. Unlike v1, v2 APPLIES the reorder, so a clean bracket verse
    goes quiet with NO exclusion, and a bag-neutral displacement FIRES."""
    print("== reassembly-diff V2 CONTROLS (order-aware) ==")
    ok = True
    # A clean John 1:1 bracket group in Greek order -> reorders to English -> quiet.
    clean_rows = [
        {"english": "God", "bracket_id": 1, "greek_pos": 4, "position": 0},
        {"english": "was", "bracket_id": 1, "greek_pos": 3, "position": 1},
        {"english": "the", "bracket_id": 1, "greek_pos": 1, "position": 2},
        {"english": "word.", "bracket_id": 1, "greek_pos": 2, "position": 3},
    ]
    d = diff_verse_v2(clean_rows, "the word was God.")
    print(f"  [{'QUIET' if d is None else 'FALSE-POSITIVE'}] clean bracket reorder "
          f"-> {'immune (reorder applied)' if d is None else d}")
    ok = ok and d is None

    # PROOF-OF-FIRE on the REAL Jer 48:1 rows (dump 2026-07-04, verse_id 20217).
    # The displaced 'the' (pos 6 belongs before 'God', sits before 'forces,') gives
    # '...of the the forces, God...' vs text '...of the forces, the God...'. NOTE the
    # bracket group (17-19) floats its ';' correctly, so that is NOT the residual hit.
    JER48_TEXT = ("To Moab, thus said the LORD of the forces, the God of Israel; "
                  "Woe unto Nebo, for it was destroyed; Kiriathaim was taken; "
                  "the fortification was shamed; it was vanquished.")

    def _r(eng, pos, bid=None, gp=None):
        return {"english": eng, "position": pos, "bracket_id": bid, "greek_pos": gp}

    jer48_rows = [
        _r("To", 0), _r("Moab,", 1), _r("thus", 2), _r("said", 3), _r("the LORD", 4),
        _r("of the", 5), _r("the", 6), _r("forces,", 7), _r("God", 8), _r("of Israel;", 9),
        _r("Woe", 10), _r("unto", 11), _r("Nebo,", 12), _r("for", 13),
        _r("it was destroyed;", 14), _r("Kiriathaim", 15), _r("was taken;", 16),
        _r("was shamed", 17, 1, 3), _r("the", 18, 1, 1), _r("fortification;", 19, 1, 2),
        _r("it was vanquished.", 20),
    ]
    dd = diff_verse_v2(jer48_rows, JER48_TEXT)
    fired = dd is not None and dd["klass"] == "word-order"
    print(f"  [{'FIRED' if fired else 'VOID '}] REAL Jer 48:1 displaced 'the' "
          f"-> {dd['klass'] if dd else '(clean)'}  {(' ; '.join(dd['ops']) if dd else '')}")
    ok = ok and fired

    # hand-corrected: move the stray 'the' (pos 6) to after 'forces,' -> matches text
    good_rows = [dict(r) for r in jer48_rows]
    good_rows[6]["english"] = "forces,"
    good_rows[7]["english"] = "the"
    dg = diff_verse_v2(good_rows, JER48_TEXT)
    print(f"  [{'QUIET' if dg is None else 'STILL FIRING'}] corrected Jer 48:1 rows -> "
          f"{'clean' if dg is None else dg}")
    ok = ok and dg is None

    print(f"\n{'V2 CONTROLS PASSED.' if ok else 'V2 CONTROL FAILURE.'}")
    print("  NOTE: the port itself is proven byte-equal to the JS in "
          "tests/test_reorder_port.py; run that FIRST.")
    return 0 if ok else 1


if __name__ == "__main__":
    args = sys.argv[1:]
    v2 = "--v2" in args
    if "--controls" in args:
        sys.exit(run_controls_v2() if v2 else run_controls())
    db = next((a for a in args if not a.startswith("--")), "bible.db")
    if "--verse" in args:
        ref = args[args.index("--verse") + 1]
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        print_verse(conn, ref, v2=v2)
        conn.close()
        sys.exit(0)
    if v2:
        run_report_v2(db, list_all="--list" in args)
    else:
        run_report(db)
