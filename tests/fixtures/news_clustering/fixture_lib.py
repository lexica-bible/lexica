"""Shared pieces for the news clustering fixtures — used by tests/test_news_clustering.py (CI test of
the card grouping) and relabel_check.py (by-hand check of the AI labeler). One loader, one set of
checks, so the two can never disagree about what "right" means.

Files in this folder:
  frozen.json    the rows exactly as freeze_sample.py copied them off PA (never hand-edited)
  expected.json  the hand judgment of EVERY frozen row: which real-world happening it is about
                 (see its _about block for the rule and the classes), plus the pins: labeler
                 mistakes the frozen labels carry, recorded by id so any change is visible.

A "story" below = one judged happening. Rows the judgment doesn't assert (merge: not/border;
split/cross: singles/unsure) are each their own one-row story, so they can never be counted as
"the same" as anything else.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))     # the repo
sys.path.insert(0, ROOT)
import views_news  # noqa: E402

CASES = ("merge_encyclical", "split_sunday", "cross_night")
ENCYCLICAL = "Magnifica Humanitas (2026 AI encyclical)"

# Every row first pulled on or before this night was labeled in ONE pass: the by-hand
# `group_news.py --regroup` of 2026-06-29 (memory project_news_watch). Rows after it were labeled by
# the nightly run, one night at a time, each night starting from an empty label list.
JUNE_REGROUP_NIGHT = "2026-06-29"


def load(folder=HERE):
    with open(os.path.join(folder, "frozen.json"), encoding="utf-8") as f:
        frozen = json.load(f)
    with open(os.path.join(folder, "expected.json"), encoding="utf-8") as f:
        expected = json.load(f)
    return frozen, expected


def case_rows(frozen, case):
    """The case's rows, shaped like the feed's own rows (what views_news._group reads)."""
    return [dict(r) for r in frozen[case]]


def labeling_night(row):
    """Which labeler run named this row: the June regroup pass, or its own first-pull night."""
    n = (row.get("first_seen") or "")[:10]
    return JUNE_REGROUP_NIGHT if n <= JUNE_REGROUP_NIGHT else n


def judgment(expected, case, rows):
    """-> (story_of {id: story}, judged {story names that are asserted}, problems [str]).
    Problems = the judgment doesn't cover every frozen row exactly once (a row left out would
    let a wrong grouping of it pass silently)."""
    e = expected[case]
    story_of, judged, problems, seen = {}, set(), [], {}

    def put(i, story, where):
        i = int(i)
        if i in seen:
            problems.append(f"id {i} judged twice ({seen[i]} and {where})")
        seen[i] = where
        story_of[i] = story

    if case == "merge_encyclical":
        judged.add(ENCYCLICAL)
        for i in e["core"]:
            put(i, ENCYCLICAL, "core")
        for k in ("not", "border"):
            for i in e[k]:
                put(i, f"{k}:{i}", k)
    else:
        for h in e["happenings"]:
            judged.add(h["name"])
            for i in h["ids"]:
                put(i, h["name"], h["name"])
        for i in e["singles"]:
            judged.add(f"single:{i}")
            put(i, f"single:{i}", "singles")
        for i in e["unsure"]:
            put(i, f"unsure:{i}", "unsure")
    ids = {r["id"] for r in rows}
    if len(ids) != len(rows):
        problems.append("frozen rows repeat an id")
    missing, extra = sorted(ids - set(story_of)), sorted(set(story_of) - ids)
    if missing:
        problems.append(f"{len(missing)} frozen rows not judged: {missing[:20]}")
    if extra:
        problems.append(f"{len(extra)} judged ids not in the frozen rows: {extra[:20]}")
    return story_of, judged, problems


def cards_of(rows):
    """The card grouping exactly as the feed builds it (views_news._group, labels on)."""
    return [frozenset(a["id"] for a in c["arts"]) for c in views_news._group(rows, True)]


def expected_pieces(rows, story_of):
    """The cards a PERFECT labeler would produce: each story on one label, then the feed's own
    14-day split (views_news._split_by_window — a deliberate, separately ruled rule, not this
    fixture's subject). -> list of (story, frozenset ids)."""
    by = {}
    for r in rows:
        by.setdefault(story_of[r["id"]], []).append(r)
    out = []
    for s, arts in by.items():
        for piece in views_news._split_by_window(arts):
            out.append((s, frozenset(a["id"] for a in piece)))
    return out


def overmerged(produced, story_of, judged):
    """Cards holding rows of two or more DIFFERENT asserted stories. Unasserted rows are ignored."""
    out = []
    for p in produced:
        stories = {story_of[i] for i in p if story_of[i] in judged}
        if len(stories) > 1:
            out.append(p)
    return out


def scattered(produced, pieces, judged):
    """Asserted stories whose window piece is spread over 2+ cards -> [(story, piece, sizes)]."""
    out = []
    for s, piece in pieces:
        if s not in judged or len(piece) < 2:
            continue
        hit = [p & piece for p in produced if p & piece]
        if len(hit) > 1:
            out.append((s, piece, sorted((len(h) for h in hit), reverse=True)))
    return out


def reuse_joiners(rows, night_of, story_of, asserted):
    """Rows that JOINED an earlier night's label as a different story -> set of ids.
    A row counts when (a) its label already existed from an EARLIER labeling night (night_of =
    {id: the night that row was labeled}) and (b) its story is asserted and is not one that label
    carried on any earlier night. That is a fusion made THROUGH a reused earlier-night label —
    the decision the cross-night fix owns. Different stories given one label on the label's own
    first night are the labeler's same-night fusion: no past label is involved, so that is not
    this fix's to score (ruled JP 2026-10-30). Unlabeled rows are skipped."""
    by_label = {}
    for r in rows:
        if r.get("event"):
            by_label.setdefault(r["event"], []).append(r)
    out = set()
    for rs in by_label.values():
        first = min(night_of[r["id"]] for r in rs)
        seen = set()
        for n in sorted({night_of[r["id"]] for r in rs}):
            tonight = [r for r in rs if night_of[r["id"]] == n]
            if n > first:
                out |= {r["id"] for r in tonight
                        if story_of[r["id"]] in asserted and story_of[r["id"]] not in seen}
            seen |= {story_of[r["id"]] for r in tonight}
    return out


# JUDGMENT EDGES not yet ruled: fusions here are reported in their own column so the picture with
# and without them is visible — the BAR still counts them. Each edge = (row, a row of the other
# story). EMPTY since 2026-10-31: both were ruled (delegated by JP) — 17505/17040 the SAME story
# (now one happening in expected.json), 17366 an edge excluded from scoring (now `unsure`).
JUDGMENT_EDGES = ()


def edge_only(card, story_of, asserted, edges=JUDGMENT_EDGES):
    """True if a fused card's asserted stories are exactly ONE edge's two stories (nothing else
    fused on it). A card that also fuses any other story is a full miss, edge or not."""
    stories = {story_of[i] for i in card if story_of.get(i) in asserted}
    return any(stories <= {story_of.get(a), story_of.get(b)} for a, b in edges)


def split_fusions(cards_fused, joiners):
    """Over-merged cards -> (through_reuse, same_night_only). A card holding any reuse joiner
    counts as through-reuse (the reuse added a fusion, whatever else is on it); the rest were
    fused on one night by the labeler alone."""
    via = [p for p in cards_fused if p & joiners]
    return via, [p for p in cards_fused if not p & joiners]


def merge_picture(rows, produced, expected):
    """The merge case read off a set of cards: the TARGET card = the one holding the most
    encyclical rows. Returns a dict of plain sets so callers can assert or just print."""
    e = expected["merge_encyclical"]
    core = set(e["core"])
    nots = {int(k) for k in e["not"]}
    target = max(produced, key=lambda p: len(p & core))
    label = {r["id"]: (r.get("event") or "") for r in rows}
    return {
        "target": target,
        "target_labels": sorted({label[i] for i in target}),
        "core_total": len(core & {r["id"] for r in rows}),
        "core_on": target & core,
        "core_off": (core & {r["id"] for r in rows}) - target,
        "not_on": target & nots,
    }


def describe(ids, rows, limit=8):
    by = {r["id"]: r for r in rows}
    out = []
    for i in sorted(ids)[:limit]:
        r = by[i]
        out.append(f"    id {i} {(r.get('published') or '')[:10]} [{r.get('event') or ''}] "
                   f"{(r.get('title') or '')[:80]}")
    if len(ids) > limit:
        out.append(f"    ... and {len(ids) - limit} more")
    return out
