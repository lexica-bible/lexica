"""Batch C — the follow-up thread skeleton (ai._skeleton_directive).

A follow-up answer used to restate senses the thread already covered, because the
reader-facing synthesis (pass 2) was written blind to the conversation. The fix hands
pass 2 a compact digest of what EARLIER answers covered plus a 'don't restate' directive.
The digest is assembled client-side (52-ask-corpus.jsx) from the stored turns and injected
here, per-request, only on a follow-up — a first turn's prompt stays byte-identical.

These lock the injection contract: present-only, capped, blank → nothing. (The client-side
notice/loading/error exclusion + the recent-6 slice ride the SAME ctxTurns filter that
builds the pass-1 context weave — not re-tested here; this is the server floor.)
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ai


def _fake_db():
    """A throwaway in-memory db with just enough verses/words for _curation_prompt's
    verse-text lookup, so the two prompt-shape tests run with NO bible.db (CI rule).
    Freshly built each call — the code closes what db_ro() hands it."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript(
        "CREATE TABLE verses(id INTEGER, book TEXT, chapter INT, verse INT);"
        "CREATE TABLE words(verse_id INT, english TEXT, position INT);"
        "INSERT INTO verses VALUES (1,'Joh',1,1);"
        "INSERT INTO words VALUES (1,'In',1),(1,'beginning',2),(1,'Word',3);"
    )
    return c


class _patch_db:
    """with _patch_db(): ... — swap ai.db_ro for the fake, restore after."""
    def __enter__(self):
        self._real = ai.db_ro
        ai.db_ro = _fake_db
    def __exit__(self, *a):
        ai.db_ro = self._real


# ── injected only when a skeleton is present ──

def test_empty_skeleton_no_directive():
    assert ai._skeleton_directive("") == ""
    assert ai._skeleton_directive(None) == ""
    assert ai._skeleton_directive("   \n  \n ") == ""   # blank lines only → nothing


def test_present_skeleton_emits_directive():
    d = ai._skeleton_directive("Turn 1: pur G4442 — physical and eschatological fire.")
    assert d                                            # non-empty
    assert "already covered" in d
    assert "Do NOT restate" in d
    assert "pur G4442" in d                             # the digest text is carried in


def test_directive_allows_a_new_word():
    # The topic-switch escape hatch must be present so 'what about water' isn't forced
    # into false continuity with an earlier fire thread.
    d = ai._skeleton_directive("Turn 1: pur G4442 — fire.")
    assert "DIFFERENT word" in d
    assert "never forces continuity" in d


# ── caps: a long thread can't blow up the curate prompt ──

def test_turn_cap_respected():
    many = "\n".join(f"Turn {i}: word{i} — sense {i}." for i in range(1, 12))  # 11 lines
    d = ai._skeleton_directive(many)
    assert "Turn 6:" in d          # first 6 kept
    assert "Turn 7:" not in d      # 7th+ dropped
    assert "Turn 11:" not in d


def test_char_budget_respected():
    huge = "\n".join(f"Turn {i}: " + ("x" * 500) for i in range(1, 4))
    d = ai._skeleton_directive(huge)
    # The digest body is clamped; the whole directive stays bounded (body budget + the
    # fixed wrapper), never the raw ~1500-char input pasted in whole.
    assert len(d) < 1600
    assert d.count("x") <= ai._SKELETON_MAX_CHARS


def test_blank_lines_are_skipped_not_counted():
    s = "Turn 1: a — x.\n\n\nTurn 2: b — y.\n\n"
    d = ai._skeleton_directive(s)
    assert "Turn 1: a" in d and "Turn 2: b" in d


# ── first-turn prompt is byte-identical to before the feature ──

def test_first_turn_prompt_unchanged():
    # A first turn passes skeleton="" — _curation_prompt must build the same user_msg as
    # calling it with no skeleton at all (default). Uses a tiny result pool so no DB
    # subsampling/scoring runs; the verse-text lookup is exercised the same way in both.
    results = [{"book": "Joh", "chapter": 1, "verse": 1, "ref": "Joh 1:1"}]
    ks = [{"strongs": "G4442", "lemma": "πῦρ"}]
    with _patch_db():
        base, _ = ai._curation_prompt("fire", results, ks)
        with_empty, _ = ai._curation_prompt("fire", results, ks, "")
    assert base == with_empty


def test_followup_prompt_adds_the_block():
    results = [{"book": "Joh", "chapter": 1, "verse": 1, "ref": "Joh 1:1"}]
    ks = [{"strongs": "G4442", "lemma": "πῦρ"}]
    with _patch_db():
        base, _ = ai._curation_prompt("how does it differ from eleos", results, ks)
        withskel, _ = ai._curation_prompt(
            "how does it differ from eleos", results, ks,
            "Turn 1: pur G4442 — fire, judgment, testing.",
        )
    assert withskel != base
    assert "already covered" in withskel
    assert "pur G4442" in withskel


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")


if __name__ == "__main__":
    _run()
