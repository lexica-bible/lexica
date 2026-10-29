"""Shared pieces for the news clustering fixtures — used by tests/test_news_clustering.py (the CI
test of the card grouping) and relabel_check.py (the by-hand AI labeler check). One loader, one
comparison, so the two checks can never disagree about what "the expected cards" means.

Files in this folder:
  frozen.json    the rows exactly as freeze_sample.py copied them off PA (never hand-edited)
  expected.json  the hand-judged answer: for each case, which rows are ONE real-world happening
                 and so must end up on ONE card. Every frozen row is in exactly one card.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = ("merge_encyclical", "split_sunday", "cross_night")


def load(folder=HERE):
    with open(os.path.join(folder, "frozen.json"), encoding="utf-8") as f:
        frozen = json.load(f)
    with open(os.path.join(folder, "expected.json"), encoding="utf-8") as f:
        expected = json.load(f)
    return frozen, expected


def case_rows(frozen, case):
    """The case's rows, shaped like the feed's own rows (what views_news._group reads). Rows that
    were merged away (table items_merged) are kept — the cross-night pair needs both copies."""
    return [dict(r) for r in frozen[case]]


def expected_cards(expected, case):
    return [(c["name"], frozenset(c["ids"])) for c in expected[case]["cards"]]


def check_expected_complete(rows, cards):
    """The expected file must judge EVERY frozen row exactly once — a row left out would let a
    wrong grouping of it pass silently."""
    problems = []
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        problems.append("frozen rows repeat an id")
    seen = {}
    for name, members in cards:
        for i in members:
            if i in seen:
                problems.append(f"id {i} is in two expected cards: {seen[i]!r} and {name!r}")
            seen[i] = name
    missing = sorted(set(ids) - set(seen))
    extra = sorted(set(seen) - set(ids))
    if missing:
        problems.append(f"{len(missing)} frozen rows not in any expected card: {missing[:20]}")
    if extra:
        problems.append(f"{len(extra)} expected ids not in the frozen rows: {extra[:20]}")
    return problems


def compare(produced, cards, title_of=None):
    """produced = list of id-sets (one per card the code made); cards = expected (name, ids).
    Returns (ok, lines). ok only when the two groupings are identical. Lines name every
    difference in plain terms: an OVER-MERGE (one card fusing happenings that should be
    separate) or a SPLIT (one happening scattered over several cards)."""
    produced = [frozenset(p) for p in produced]
    owner = {}
    for name, members in cards:
        for i in members:
            owner[i] = name
    lines = []
    for p in produced:
        names = sorted({owner.get(i, "?") for i in p})
        if len(names) > 1:
            parts = ", ".join(f"{n} ({sum(1 for i in p if owner.get(i) == n)})" for n in names)
            lines.append(f"OVER-MERGE: one card ({len(p)} rows) fuses {parts}")
    for name, members in cards:
        hit = [p & members for p in produced if p & members]
        if len(hit) > 1:
            sizes = sorted((len(h) for h in hit), reverse=True)
            lines.append(f"SPLIT: {name!r} ({len(members)} rows) is spread over "
                         f"{len(hit)} cards, sizes {sizes}")
            if title_of:
                for h in sorted(hit, key=len)[:-1]:     # name the smaller pieces
                    for i in sorted(h)[:5]:
                        lines.append(f"    id {i}: {title_of(i)[:90]}")
    ok = set(produced) == {m for _, m in cards}
    return ok, lines


def partition_by_label(rows, label_key="event"):
    """Rows grouped by their label alone (no date split) — the labeler's own grouping."""
    out = {}
    for r in rows:
        out.setdefault((r.get(label_key) or "").strip() or f"(unlabeled #{r['id']})",
                       set()).add(r["id"])
    return out
