#!/usr/bin/env python3
"""reorder_english.py — Python port of getEnglishOrderWords / orderBracketGroupWords
from static/src/56-library-order-logic.jsx.

WHY: the reassembly-diff v2 must rebuild a verse in the SAME English reading order
the reader (prose) shows, so it can catch a bag-neutral misplacement (Jer 48:1's
displaced "the") and a bracket-internal punct shift that the v1 bag pass can't see.

FIDELITY IS THE WHOLE POINT: a drifted port invents phantom hits. This is a
line-for-line port of the JS. Its proof is tests/test_reorder_port.py, which diffs
this port's output against the COMMITTED JS baseline (tests/fixtures/order/
expected.json, the `prose` arrays) for John 1, Genesis 1, 1 Chronicles 1, and the
2 Ki 23:29 anchor. Do not "improve" this file — if the JS changes, re-port + re-prove.

Word dicts here mirror the /api/chapter word objects: {bracket_id, greek_pos,
english, ...}. Only those three keys are read.
"""
import re

# JS: const TRAIL = /[.,;:!?·)]+$/;  (prose float — NO whitespace, NO dash class; ) added 2026-07-05 for paren-edge)
_TRAIL = re.compile(r"[.,;:!?·)]+$")


def order_bracket_group_words(words):
    """JS orderBracketGroupWords: sort by greek_pos ascending, missing -> 999.
    Python sorted() is stable, matching JS Array.sort stability."""
    return sorted(words, key=lambda w: w["greek_pos"] if w.get("greek_pos") is not None else 999)


def get_english_order_words(words):
    """Line-for-line port of getEnglishOrderWords (56-library-order-logic.jsx)."""
    bracket_map = {}
    for w in words:
        bid = w.get("bracket_id")
        if bid is not None:
            bracket_map.setdefault(bid, []).append(w)

    for bid, group in bracket_map.items():
        trailing = ""
        cleaned = []
        for w in group:
            eng = (w.get("english") or "").strip()
            if eng and _TRAIL.sub("", eng) == "":          # pure-punctuation token
                trailing += eng
                continue
            m = _TRAIL.search(eng)
            if m:
                trailing += m.group(0)
                nw = dict(w)
                nw["english"] = eng[:m.start()].rstrip()
                cleaned.append(nw)
            else:
                cleaned.append(w)
        cleaned = order_bracket_group_words(cleaned)
        if trailing and cleaned:
            li = len(cleaned) - 1
            while li > 0 and not (cleaned[li].get("english") or "").strip():
                li -= 1
            nw = dict(cleaned[li])
            nw["english"] = (nw.get("english") or "") + trailing
            cleaned[li] = nw
        bracket_map[bid] = cleaned

    result = []
    seen = set()
    for w in words:
        bid = w.get("bracket_id")
        if bid is None:
            result.append(w)
        elif bid not in seen:
            seen.add(bid)
            result.extend(bracket_map[bid])
    return result


def prose_sequence(words):
    """The reader's prose token sequence: english of each word in English order,
    trimmed, empties dropped — exactly what signature() in test_library_order.js
    stores as the `prose` array (the JS baseline we prove against)."""
    return [e for e in ((w.get("english") or "").strip() for w in get_english_order_words(words)) if e]
