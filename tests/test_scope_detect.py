"""Language/testament scope detection (ai._detect_scope + ai._scope_directive).

The #20B scope directive keeps a scoped answer ("fire in the OT") in the right
language/testament. The trap: a COMPARISON ("compare the OT and NT view of the
Sabbath", "charis in greek and hebrew") names two competing values on one axis —
the old first-match detector collapsed that to a single scope and told the model to
drop half the answer. Mixed signals on an axis must go UNSET, never first-match.
These are the permanent #20B acceptance cases (static, no bible.db).
"""
import ai


# ── single-signal scope still works (Fix 1 must not break this) ──

def test_single_testament_scope():
    s = ai._detect_scope("fire in the OT")
    assert s == {"lang": None, "testament": "ot"}
    assert ai._scope_directive(s)                      # non-empty directive


def test_single_language_scope():
    s = ai._detect_scope("sheol in hebrew")
    assert s == {"lang": "hebrew", "testament": None}
    assert ai._scope_directive(s)


def test_septuagint_maps_to_greek():
    assert ai._detect_scope("mercy in the Septuagint")["lang"] == "greek"
    assert ai._detect_scope("in the LXX")["lang"] == "greek"


def test_both_axes_one_value_each():
    s = ai._detect_scope("fire in the greek OT")
    assert s == {"lang": "greek", "testament": "ot"}


def test_same_axis_value_repeated_is_still_scoped():
    # "old testament" and "ot" both mean ot — one value, still scoped.
    s = ai._detect_scope("the old testament — OT usage of fire")
    assert s["testament"] == "ot"


# ── mixed signals on one axis → unset, never first-match ──

def test_mixed_testament_never_collapses():
    s = ai._detect_scope("Compare the OT and NT view of the Sabbath")
    assert s["testament"] is None                      # NOT "ot"
    assert ai._scope_directive(s) == ""                # no single-scope directive


def test_mixed_language_never_collapses():
    s = ai._detect_scope("charis in greek and hebrew")
    assert s["lang"] is None                           # NOT "hebrew"
    assert ai._scope_directive(s) == ""


def test_trace_ot_to_nt_suggestion_not_collapsed():
    # A stock suggestion button that used to trigger the bug.
    s = ai._detect_scope("Trace atonement from the Old Testament to the New Testament")
    assert s["testament"] is None


# ── Fix 5: periods (O.T. / N.T.) ──

def test_dotted_testament_abbreviations():
    assert ai._detect_scope("fire in the O.T.")["testament"] == "ot"
    assert ai._detect_scope("grace in the N.T.")["testament"] == "nt"


# ── no false positives ──

def test_unscoped_query_has_no_directive():
    s = ai._detect_scope("what does grace mean")
    assert s == {"lang": None, "testament": None}
    assert ai._scope_directive(s) == ""


def test_book_hebrews_does_not_trigger_language():
    assert ai._detect_scope("rest in Hebrews 4")["lang"] is None
