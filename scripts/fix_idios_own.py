#!/usr/bin/env python3
"""
fix_idios_own.py — DUAL-ORDERING click-target cleanup, the ἴδιος "own" cluster.

THE CASE: ABP renders the pair ὁ(G3588) + ἴδιος(G2398) as "his own / their own /
its own / our own". The build parked the WHOLE phrase on the article slot (G3588)
and left the ἴδιος slot (G2398) EMPTY right beside it, so clicking "own" opens the
article ("the"), not ἴδιος. (Same family as fix_funcword_subject.py / fix_lord_subject.py,
but the orphan is the ADJECTIVE ἴδιος — which is why the noun-only fixer skips it and
audit_funcword_wrongslot.py files these under REPAIRABLE-OTHER, not REPAIRABLE-NOUN.)

THE FIX (identical safe mechanics to fix_funcword_subject.py): one of the two
adjacent slots is always empty, so we just RELOCATE the bundled English from the
article slot onto the empty ἴδιος slot and blank the article slot. The visible word
sequence is UNCHANGED — only WHICH Strong's each word is attached to changes. When
the pair sits inside a bracket the article's greek_pos is carried to ἴδιος so PROSE
(greek_pos order) still reads the phrase in the same spot. Touches english /
english_head / italic / italic_words (+ greek_pos in a bracket) ONLY — never strongs /
strongs_base / morph / lemma / position / bracket_id / is_pn.

  before:  [G3588  english="his own"] [G2398 ἴδιος  english=∅]
  after:   [G3588  english=∅]         [G2398 ἴδιος  english="his own"]

PRECISE PATTERN (corpus-wide, but unambiguous — review the dry-run before applying):
  host  = a G3588 slot with non-empty english whose words include "own"
  orphan= an ADJACENT (prefer +1: ὁ precedes ἴδιος) slot that is EMPTY, in the SAME
          bracket context as the host, and is ἴδιος (strongs_base base == '2398').
Correct renderings where "own" already sits on ἴδιος (e.g. 1Co 7:4 "her own") have a
NON-empty orphan and are left untouched. Idempotent: after a run the host is empty and
ἴδιος is non-empty, so neither is a candidate — safe to re-run.

ADD to the post-rebuild repair chain (a fresh rebuild re-bundles these; run alongside
the other pinned patches in scripts/finish_rebuild.sh).

Validate after: audit_funcword_wrongslot.py (the ἴδιος "own" lines leave REPAIRABLE-OTHER),
health_check.py (0/0), strongs_base GLOB '[0-9]*' = 0, audit_bracket_order.py (at baseline
— we create NO brackets).

Usage:
  python3 scripts/fix_idios_own.py bible.db --dry-run
  python3 scripts/fix_idios_own.py bible.db
"""
import re
import sqlite3
import sys

DB = next((a for a in sys.argv[1:] if not a.startswith("--")), "bible.db")
DRY = "--dry-run" in sys.argv

ARTICLE_BASE = "G3588"
IDIOS_BASE = "2398"        # ἴδιος, bare (compared after stripping G/H + any .suffix)
PRONOUNS = {"his", "her", "their", "its", "our", "my", "your", "thy"}


def bare(s):
    return re.sub(r"[^\w]", "", s or "").lower()


def has_own(english):
    return "own" in {bare(t) for t in (english or "").split()}


def head_of(english):
    """Content head = last word that is not a leading possessive ('his own' -> 'own',
    'with our own' -> 'own'). Falls back to the last token."""
    toks = [t for t in (english or "").split() if bare(t)]
    for tok in reversed(toks):
        if bare(tok) not in PRONOUNS and bare(tok) != "with":
            return bare(tok)
    return bare(toks[-1]) if toks else None


def base_of(strongs_base):
    return (strongs_base or "").lstrip("GH").split(".")[0]


conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row


def neighbour(verse_id, position, delta):
    return conn.execute(
        "SELECT position, english, strongs_base, bracket_id "
        "FROM words WHERE verse_id=? AND position=?",
        (verse_id, position + delta)).fetchone()


cands = conn.execute(
    "SELECT w.verse_id, w.position, w.english, w.english_head, w.greek_pos, "
    "       w.italic, w.italic_words, w.bracket_id, v.book, v.chapter, v.verse "
    "FROM words w JOIN verses v ON v.id = w.verse_id "
    "WHERE w.strongs_base = ? AND w.english IS NOT NULL AND w.english != '' "
    "ORDER BY w.verse_id, w.position", (ARTICLE_BASE,)).fetchall()

applied = 0
print(f"{'[DRY RUN] ' if DRY else ''}idios 'own' relocate fix -> {DB}\n")

for c in cands:
    if not has_own(c["english"]):
        continue
    vid, ph, host_bid = c["verse_id"], c["position"], c["bracket_id"]

    chosen = None
    for delta in (1, -1):
        nb = neighbour(vid, ph, delta)
        if not nb or (nb["english"] or "").strip() != "":
            continue
        if nb["bracket_id"] != host_bid:            # share the host's bracket context
            continue
        if base_of(nb["strongs_base"]) == IDIOS_BASE:
            chosen = (nb, delta)
            break
    if not chosen:
        continue
    nb, delta = chosen

    moved_eng = c["english"]
    new_head = head_of(moved_eng) or c["english_head"]
    in_bracket = host_bid is not None
    tag = "in-bracket" if in_bracket else ("after" if delta > 0 else "before")
    ref = f"{c['book']} {c['chapter']}:{c['verse']}"
    print(f"  {ref:12} host[{ph}]{c['strongs_base']:7} -> idios[{nb['position']}]"
          f"{nb['strongs_base']:7} ({tag})")
    print(f"      move english {moved_eng!r}  (head -> {new_head!r})")

    if not DRY:
        if in_bracket:
            conn.execute(
                "UPDATE words SET english=?, english_head=?, greek_pos=?, italic=?, "
                "italic_words=? WHERE verse_id=? AND position=?",
                (moved_eng, new_head, c["greek_pos"], c["italic"],
                 c["italic_words"] or "", vid, nb["position"]))
        else:
            conn.execute(
                "UPDATE words SET english=?, english_head=?, italic=?, italic_words=? "
                "WHERE verse_id=? AND position=?",
                (moved_eng, new_head, c["italic"], c["italic_words"] or "",
                 vid, nb["position"]))
        conn.execute(
            "UPDATE words SET english=NULL, english_head=NULL, italic=0, italic_words='' "
            "WHERE verse_id=? AND position=?",
            (vid, ph))
    applied += 1

if not DRY:
    conn.commit()
    print(f"\napplied {applied} idios 'own' relocate fixes.")
else:
    print(f"\n[DRY RUN] {applied} fixes would be applied. No changes written.")
conn.close()
