"""Cache key folds in detected scope (ai._cache_key + ai._scope_tag).

The trap: _cache_key turns punctuation into spaces, but _detect_scope reads the dotted
forms O.T./N.T. specially. So "fire O.T." (testament=ot) and a literal "fire o t" (no
scope) both clean to the same base key — without the scope tag they'd serve each other
the wrong-scope answer, a rare but confidently-wrong result. The tag keeps them apart.
Static, no bible.db.
"""
import ai


def _key(q):
    return ai._cache_key(q) + ai._scope_tag(q)


# ── the collision the tag exists to prevent ──

def test_dotted_ot_vs_literal_o_t_diverge():
    # Same base text ("fire o t") but different detected scope → different answer keys.
    assert ai._cache_key("fire O.T.") == ai._cache_key("fire o t")   # base collides
    assert _key("fire O.T.") != _key("fire o t")                     # full key does not


def test_scoped_language_diverges_from_unscoped():
    assert _key("mercy in hebrew") != _key("mercy")


def test_greek_vs_hebrew_scope_diverge():
    assert _key("fire in greek") != _key("fire in hebrew")


# ── the tag must NOT change a plain (unscoped) key ──

def test_unscoped_key_unchanged():
    assert ai._scope_tag("what does grace mean") == ""
    assert _key("what does grace mean") == ai._cache_key("what does grace mean")


# ── the tag doesn't re-trigger scope off its own tokens (round-trip safety) ──

def test_tag_does_not_self_retrigger():
    # 'lhebrew'/'tot' have no word boundary a scope term matches, so feeding the tag
    # back through detection finds nothing — the stored full key stays stable.
    assert ai._scope_tag("fire in hebrew") == " scope lhebrew"
    assert ai._scope_tag(ai._scope_tag("fire in hebrew")) == ""


# ── caps / punctuation variants of the SAME scoped question still share one answer ──

def test_caps_and_punct_variants_still_share():
    assert _key("Fire in Hebrew?") == _key("fire in hebrew")
