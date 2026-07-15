#!/usr/bin/env python3
"""Grounded-naming context feed — design pass, reviewer-ruled 2026-07-15.

THE DEFECT (G2374 + G5088 parks, 2026-07-14): on narrative-dense words the model named
referents its fed text did not contain (Corinth for Ephesus, Elizabeth for Mary at the manger
verse, Hazah — a name this corpus does not carry). Root cause on the bytes: VERSE_PROMPT
promised "a verse with surrounding context" while fetch_context fed ONE bare verse — the model
honored a false promise, supplying the missing context from training. The ban at the
constraints block bound SENSES, never referents.

THE FIX (option (c), ±2, reviewer-receipted): fetch_context feeds up to CONTEXT_SPAN verses
either side (same chapter, missing neighbors OMITTED — the "None" feed-lie class), labeled
read-only/never-cite; the prompt's promise is made TRUE and a referent rule is added; probe-2
grounds a name against the cited occurrence's OWN fed context (per-occurrence, never pooled).

Three reviewer-required controls, each proven red-first against the pre-change behavior:
  1. a context-grounded name passes probe-2 (control: same call WITHOUT context still warns)
  2. a context-only verse, if cited, fails the citation gate (bucket "real")
  3. a missing neighbor's line is omitted entirely — never blank, never the text "None"
"""
import os, sqlite3, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import build_lexica_def as B


# ── fixture: a small 2Ki 4 with a deliberate GAP at 4:3 and the name Elisha in 4:2 only ──────
# Occurrence verses (lemma tagged): 4:1 and 4:4. Context-only verse: 4:2 (exists, no tag).
_VERSES = [
    (1, "2Ki", 4, 1, "And one woman of the sons of the prophets yelled out, saying, My husband is dead."),
    (2, "2Ki", 4, 2, "And Elisha said to her, What shall I do for you?"),
    # 4:3 deliberately MISSING — the gap a real corpus can carry; its line must be OMITTED
    (4, "2Ki", 4, 4, "And you shall enter and lock the door after you and after your sons."),
    (5, "2Ki", 4, 5, "And she went from him, and locked the door for herself."),
    (6, "2Ki", 4, 6, "And it came to pass when the receptacles were filled."),
]


def _db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, "
                 "verse INT, text TEXT)")
    conn.execute("CREATE TABLE words (verse_id INT, position INT, strongs TEXT, "
                 "strongs_base TEXT, english_head TEXT, english TEXT, italic_words TEXT)")
    conn.executemany("INSERT INTO verses VALUES (?,?,?,?,?)", _VERSES)
    for vid in (1, 4):   # the lemma occurs at 4:1 and 4:4 only — 4:2 is context-only
        conn.execute("INSERT INTO words VALUES (?,?,?,?,?,?,?)",
                     (vid, 3, "2374", "G2374", "door", "door", ""))
    return conn


def _ctx(conn):
    pred, params = B.abp_filter(conn, "G2374")
    occs = B.occurrences(conn, pred, params)
    return B.fetch_context(conn, occs, has_surface=False)


def test_context_is_same_chapter_span_with_gap_omitted():
    """±CONTEXT_SPAN same-chapter neighbors ride the ctx tuple; the missing 4:3 is OMITTED,
    not padded. The tuple is 9 long (was 8 — the pre-change shape, red-first proof: the old
    unpack raised ValueError on this)."""
    ctx = _ctx(_db())
    assert [len(c) for c in ctx] == [9, 9], [len(c) for c in ctx]
    occ_41, occ_44 = ctx
    # 4:1 (chapter start): no verse 0 or -1 exists; 4:3 missing → only 4:2 survives
    assert [(ch, vs) for ch, vs, _ in occ_41[8]] == [(4, 2)], occ_41[8]
    # 4:4: 4:2 present, 4:3 GAP omitted, 4:5 and 4:6 present — exactly these, in order
    assert [(ch, vs) for ch, vs, _ in occ_44[8]] == [(4, 2), (4, 5), (4, 6)], occ_44[8]


def test_context_line_exact_and_never_none():
    """#76 — assert the EXACT emitted context line, not merely presence; and the whole feed
    carries no 'None' text and no line for the missing 4:3 (the G3464 feed-lie class)."""
    feed = "\n".join(B._occ_lines(_ctx(_db())))
    assert ("     ~ context 2Ki 4:2 (read only; NOT an occurrence - never cite it): "
            "And Elisha said to her, What shall I do for you?") in feed, feed
    assert "None" not in feed, feed
    assert "4:3" not in feed, feed


def test_header_and_prompt_carry_the_contract():
    """The user-message header names the context contract; VERSE_PROMPT's promise is now TRUE
    (context verses really are supplied) and the referent rule exists. Asserted on emitted
    bytes / the live prompt, never on a copy."""
    msg = B.verse_user_msg("G2374", "thyra", [("door", 2)], _ctx(_db()))
    assert "never cite a context reference" in msg, msg[:2000]
    assert "Name a person or place only if that name appears in the supplied text" \
        in B.VERSE_PROMPT
    assert "supplied for reading only" in B.VERSE_PROMPT


def test_probe2_context_grounding_red_first():
    """Reviewer control 1. 'Elisha' lives in 4:2 (context) only, not in the cited 4:4.
    WITHOUT context probe-2 warns (the pre-change behavior — the red control); WITH the cited
    occurrence's own context it passes; a name in NEITHER ('Hazah') still warns WITH context —
    grounding must never blanket-pass."""
    vt = {("2Ki", 4, 4): _VERSES[3][4]}
    fed_ctx = {("2Ki", 4, 4): [_VERSES[1][4]]}   # 4:2's text, keyed to the occurrence it rode with

    raw = "Elisha's widow is told to lock the door (2Ki 4:4)."
    warns, notrun = B.probe2_names(raw, vt)
    assert len(warns) == 1 and "Elisha" in warns[0] and notrun == [], (warns, notrun)  # RED
    warns, notrun = B.probe2_names(raw, vt, context_texts=fed_ctx)
    assert warns == [] and notrun == [], (warns, notrun)                               # GREEN

    raw_bad = "The people of Hazah lock the door (2Ki 4:4)."
    warns, _ = B.probe2_names(raw_bad, vt, context_texts=fed_ctx)
    assert len(warns) == 1 and "Hazah" in warns[0], warns


def test_probe2_context_is_per_occurrence_not_pooled():
    """The receipt's scoping condition: a name grounded in ANOTHER occurrence's context must
    not pass — context extends only the occurrence it was fed with."""
    vt = {("2Ki", 4, 4): _VERSES[3][4]}
    fed_ctx = {("2Ki", 4, 1): [_VERSES[1][4]]}   # Elisha's text rides occurrence 4:1, NOT the cited 4:4
    raw = "Elisha's widow is told to lock the door (2Ki 4:4)."
    warns, _ = B.probe2_names(raw, vt, context_texts=fed_ctx)
    assert len(warns) == 1 and "Elisha" in warns[0], warns


def test_citation_gate_refuses_a_context_only_ref():
    """Reviewer control 2 (the pin test — #76, exactness over trust): a verse fed only as
    context, if cited, buckets 'real' (verse exists, lemma untagged) and so BLOCKS the write;
    a genuine occurrence still passes. Pinned so a future 'context refs are fine to cite'
    loosening cannot land silently."""
    gate = B.run_citation_gate(_db(), "G2374", [("2Ki", 4, 4), ("2Ki", 4, 2)])
    assert gate["pass"] == 1 and gate["real"] == 1, gate
    assert {"ref": "2Ki 4:2", "bucket": "real"} in gate["misses"], gate["misses"]


def test_signature_moves_with_context():
    """The priced draw-signature move: the same word hashes DIFFERENTLY once context verses
    ride the feed, so every pre-change cached draw is stale — never silently reusable."""
    ctx = _ctx(_db())
    bare = [c[:8] + ([],) for c in ctx]
    assert B.draw_signature("G2374", "thyra", [("door", 2)], ctx) != \
           B.draw_signature("G2374", "thyra", [("door", 2)], bare)


if __name__ == "__main__":     # plain-script mode for CI + the pre-commit hook
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("test_context_feed: ok")
