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


# ── report ─────────────────────────────────────────────────────────────────────

def _fmt_counter(c):
    return ", ".join(f"{k!r}×{v}" if v > 1 else f"{k!r}" for k, v in c.items())


def print_verse(conn, ref):
    conn.row_factory = sqlite3.Row
    parts = ref.split()
    book = " ".join(parts[:-1])
    ch, vs = parts[-1].split(":")
    row = conn.execute("SELECT id, text FROM verses WHERE book=? AND chapter=? AND verse=?",
                       (book, int(ch), int(vs))).fetchone()
    if not row:
        print(f"  {ref}: verse not found")
        return
    engs = [r["english"] for r in conn.execute(
        "SELECT english FROM words WHERE verse_id=? ORDER BY position", (row["id"],))]
    print(f"  === {ref} ===")
    print(f"  verses.text : {row['text']!r}")
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


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--controls" in args:
        sys.exit(run_controls())
    db = next((a for a in args if not a.startswith("--")), "bible.db")
    if "--verse" in args:
        ref = args[args.index("--verse") + 1]
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        print_verse(conn, ref)
        conn.close()
        sys.exit(0)
    run_report(db)
