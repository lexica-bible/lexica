"""
test_lexica_glossset_fold.py — gloss_set merges case-variant renderings.

Regression lock for the οὐρανός "Heaven" defect (2026-07-07): the gloss set kept "Heaven" (3×) as a
rendering distinct from "heaven" (636×). Feeding that split as if it were two renderings made the engine
fabricate a rationale for the capital in gloss_notes ("an editorial decision imported by the translation")
— a false claim about the translation, across two prompt generations. Fix: gloss_set folds case-variants
of the same rendering, keeping the most-frequent surface form and summing counts.

Fixtures mirror the two real sweep hits (G3772 heaven/Heaven, G39 holy/Holy) in a tiny in-memory corpus
(no bible.db). The CONTROL test proves the raw table genuinely holds the case-split, so the fold assertion
can't pass for the wrong reason (old code = 2 rows, new gloss_set = 1 merged rendering).
"""
import os
import sqlite3
import sys

_SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, _SCRIPTS)
import build_lexica_def as B          # noqa: E402


def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE words (strongs_base TEXT, strongs TEXT, english_head TEXT)")

    def add(base, head, n):
        for _ in range(n):
            c.execute("INSERT INTO words (strongs_base, strongs, english_head) VALUES (?,?,?)",
                      (base, base[1:], head))
    # G3772: dominant lowercase 'heaven', artifact capital 'Heaven', a distinct rendering 'sky',
    # and a multi-word head that must stay filtered out.
    add("G3772", "heaven", 6); add("G3772", "Heaven", 3); add("G3772", "sky", 2)
    add("G3772", "from heaven", 4)
    # G39: 'holy' dominant, 'Holy' artifact.
    add("G39", "holy", 5); add("G39", "Holy", 2)
    c.commit()
    return c


def _gs(conn, sid):
    return dict(B.gloss_set(conn, *B.abp_filter(conn, sid)))


def test_control_fixture_really_has_the_case_split():
    """Known-positive fire: the raw table holds 'heaven' AND 'Heaven' as separate rows — the exact split
    that broke it. If this stops being two rows, the fold assertions below test nothing."""
    conn = _conn()
    raw = conn.execute("SELECT english_head FROM words WHERE strongs_base='G3772' "
                       "AND english_head IN ('heaven','Heaven') GROUP BY english_head").fetchall()
    assert len(raw) == 2


def test_glossset_folds_case_variants():
    gs = _gs(_conn(), "G3772")
    assert "Heaven" not in gs           # the capital artifact is gone as a separate rendering
    assert gs.get("heaven") == 9        # 6 + 3, merged
    assert gs.get("sky") == 2           # a genuinely distinct rendering is untouched
    assert "from heaven" not in gs      # multi-word heads still excluded


def test_fold_label_is_most_frequent_surface_form():
    gs = _gs(_conn(), "G39")
    assert "Holy" not in gs
    assert gs.get("holy") == 7          # 5 + 2, label is the dominant lowercase form


if __name__ == "__main__":       # runnable as a plain script for the CI / pre-commit lists (no pytest)
    test_control_fixture_really_has_the_case_split()
    test_glossset_folds_case_variants()
    test_fold_label_is_most_frequent_surface_form()
    print("test_lexica_glossset_fold: ok")
