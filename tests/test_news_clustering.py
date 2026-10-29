#!/usr/bin/env python3
"""News cards from FROZEN real rows — the clustering fixtures (ruled JP 2026-10-25).

Cards come from two layers: (1) the AI labeler (scripts/news/group_news.py) names each article's
event; (2) views_news._group puts same-label rows on one card, split at a >14-day gap. Inputs:
tests/fixtures/news_clustering/frozen.json (1,134 rows copied off PA 2026-10-29 by
freeze_sample.py) and expected.json (every row hand-judged into its real-world happening, plus
PINS: the labeler mistakes those frozen labels carry, recorded by id).

What this test can and can't see: the labels are frozen, so it tests LAYER 2 on real data, and
pins what layer 1 got wrong. It cannot tell whether the labeler has improved or drifted — that's
relabel_check.py in the same folder (real AI, by hand, before any clustering change).

  1. MERGE — the rows labeled in the one June-29 regroup pass: the encyclical's main label makes
     ONE card (hundreds of outlets), no other label joins it, every encyclical row on that label
     inside its date span is on it. Encyclical rows the labeler put on OTHER labels, and other
     stories it put ON the encyclical's label, must match the pins exactly.
  2. SPLIT — Sunday-law headlines: no card fuses two different happenings, except the pinned
     one. (A happening scattered over several cards is reported, not failed: that's case 3.)
  3. CROSS-NIGHT — replays the REAL group_news.main() night by night on a scratch db, for every
     sample, with the AI swapped for a stand-in that (a) never confuses two stories, (b) reuses a
     label it is SHOWN for the same story, else (c) uses the exact wording the real labeler gave
     that row. So the only way it can split a story is the night boundary: group_news.py starts
     each run with an EMPTY list of known labels. The rows labeled in the June regroup count as
     one night. Every story labeled in ONE pass is the control (must pass).
     **KNOWN FAILURE today** for the real-nights replay — reported, not counted. When the
     relabeling fix lands it passes, and the test then FAILS until it is taken off KNOWN_FAILING.

No database, no network, no AI: runs offline in CI + pre-commit.
"""
import io
import os
import sqlite3
import sys
import tempfile
from contextlib import redirect_stdout

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "fixtures", "news_clustering"))

import fixture_lib as fx  # noqa: E402
from scripts.news import group_news  # noqa: E402

# Strict: a case listed here that PASSES fails the run, so the list can't go stale.
KNOWN_FAILING = {f"cross-night: {c}, real nights" for c in fx.CASES}


# ---------------------------------- 1. merge ----------------------------------

def june_rows(frozen):
    return [r for r in fx.case_rows(frozen, "merge_encyclical")
            if fx.labeling_night(r) == fx.JUNE_REGROUP_NIGHT]


def check_merge(results, frozen, expected):
    label = "merge: encyclical stays one card (June regroup labels)"
    allrows = fx.case_rows(frozen, "merge_encyclical")
    story_of, judged, problems = fx.judgment(expected, "merge_encyclical", allrows)
    if problems:
        results.append((label, False, problems))
        return
    rows = june_rows(frozen)
    ok, lines = merge_verdict(rows, fx.cards_of(rows), expected)
    results.append((label, ok, lines))


def merge_verdict(rows, cards, expected):
    m = fx.merge_picture(rows, cards, expected)
    pins = expected["merge_encyclical"]["pins"]
    lines, ok = [], True
    by = {r["id"]: r for r in rows}

    if len(m["target_labels"]) != 1:                         # layer 2 never fuses two labels
        ok = False
        lines.append(f"the encyclical card mixes labels: {m['target_labels']}")
    main = m["target_labels"][0]
    span = sorted((by[i]["published"] or "")[:10] for i in m["target"])
    inside = {r["id"] for r in rows if r["id"] in m["core_on"] | m["core_off"]
              and r["event"] == main and span[0] <= (r["published"] or "")[:10] <= span[-1]}
    if inside - m["target"]:
        ok = False
        lines.append(f"{len(inside - m['target'])} encyclical rows on its own label, inside its date "
                     f"span, are NOT on the card (the card shattered):")
        lines += fx.describe(inside - m["target"], rows)
    for key, got in (("core_off_card", m["core_off"]), ("not_on_card", m["not_on"])):
        want = {int(k) for k in pins[key]}
        if got != want:
            ok = False
            lines.append(f"pin {key} no longer matches: newly {sorted(got - want)}, "
                         f"gone {sorted(want - got)}")
            lines += fx.describe((got - want) | (want - got), rows)
    outlets = len({by[i]["source"] for i in m["target"]})
    lines.append(f"(card: {len(m['target'])} rows from {outlets} outlets, {span[0]}..{span[-1]}; "
                 f"{len(m['core_on'])} of {m['core_total']} encyclical rows on it; pinned labeler "
                 f"mistakes: {len(m['core_off'])} encyclical rows elsewhere, {len(m['not_on'])} "
                 f"other stories on it)")
    return ok, lines


# ---------------------------------- 2. split ----------------------------------

def check_split(results, frozen, expected):
    label = "split: Sunday-law happenings stay on separate cards"
    rows = fx.case_rows(frozen, "split_sunday")
    story_of, judged, problems = fx.judgment(expected, "split_sunday", rows)
    if problems:
        results.append((label, False, problems))
        return
    ok, lines = split_verdict(rows, fx.cards_of(rows), expected)
    results.append((label, ok, lines))


def split_verdict(rows, cards, expected):
    story_of, judged, _ = fx.judgment(expected, "split_sunday", rows)
    got = {frozenset(p) for p in fx.overmerged(cards, story_of, judged)}
    want = {frozenset(c["ids"]) for c in expected["split_sunday"]["pins"]["overmerged_cards"]}
    lines, ok = [], got == want
    for p in got - want:
        lines.append("NEW over-merged card (two different happenings on one card):")
        lines += fx.describe(p, rows)
    for p in want - got:
        lines.append(f"pinned over-merged card is gone (re-review the pin): {sorted(p)}")
    sc = fx.scattered(cards, fx.expected_pieces(rows, story_of), judged)
    lines.append(f"({len(cards)} cards; {len(want)} pinned over-merge; {len(sc)} happenings scattered "
                 f"over several cards — not failed here, that's the cross-night case)")
    return ok, lines


# --------------- the checks must catch a known-wrong grouping before a pass means anything ---------------

def check_detectors_fire(results, frozen, expected):
    """Feed the merge + split verdicts doctored cards built from the REAL rows: the encyclical card
    cut in half, the encyclical card fused with another label's card, two Sunday happenings fused.
    Each must fail. (Cross-night fires on its own: the real-nights replay is a known positive.)"""
    misses = []
    rows = june_rows(frozen)
    cards = fx.cards_of(rows)
    target = fx.merge_picture(rows, cards, expected)["target"]
    rest = [c for c in cards if c != target]
    half = sorted(target)
    if merge_verdict(rows, rest + [frozenset(half[::2]), frozenset(half[1::2])], expected)[0]:
        misses.append("merge verdict passed the encyclical card cut in half")
    other = max(rest, key=len)
    if merge_verdict(rows, [c for c in rest if c != other] + [target | other], expected)[0]:
        misses.append("merge verdict passed the encyclical card fused with another label's card")
    srows = fx.case_rows(frozen, "split_sunday")
    scards = fx.cards_of(srows)
    hs = expected["split_sunday"]["happenings"]
    a, b = set(hs[0]["ids"]), set(hs[1]["ids"])
    fused = [c for c in scards if not (c & (a | b))] + [frozenset(a | b)]
    if split_verdict(srows, fused, expected)[0]:
        misses.append("split verdict passed two different happenings fused on one card")
    results.append(("the checks fire on known-wrong groupings", not misses, misses))


# ------------------- 3. cross-night: real group_news.main(), night by night -------------------

def _stand_in(story_of, stored):
    """label_batch replacement: never confuses two stories (each label carries its story); inside
    one call a story gets one label; a known label of the same story is reused if shown, else the
    real labeler's own wording for that row."""
    shown = []

    def label_batch(client, batch, known):
        shown.append(len(known))
        out, this_call = {}, {}
        for r in batch:
            s = story_of[r["id"]]
            if s not in this_call:
                reuse = next((k for k in known if k.startswith(s + " || ")), None)
                this_call[s] = reuse or f"{s} || {stored[r['id']]}"
            out[r["id"]] = this_call[s]
        return out

    return label_batch, shown


def replay(rows, story_of, nights):
    """Insert each night's rows into a scratch news.db and run group_news.main() after each one
    (nightly mode: unlabeled rows only), then read back the labels it wrote."""
    stored = {r["id"]: r["event"] or f"(unlabeled #{r['id']})" for r in rows}
    stub, shown = _stand_in(story_of, stored)
    firsts = []                    # labels the labeler was shown at the FIRST call of each night
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    keep = {k: getattr(group_news, k) for k in
            ("DB_PATH", "REGROUP", "DRY_RUN", "MIN", "BATCH", "build_client", "label_batch")}
    keep_sleep = group_news.time.sleep
    try:
        c = sqlite3.connect(path)
        c.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, title TEXT, source TEXT, "
                  "published TEXT, first_seen TEXT, score INTEGER, event TEXT)")
        c.commit()
        group_news.DB_PATH, group_news.REGROUP, group_news.DRY_RUN = path, False, False
        group_news.MIN, group_news.BATCH = 5, 40
        group_news.build_client = lambda: None
        group_news.label_batch = stub
        group_news.time.sleep = lambda s: None
        for night in sorted(set(nights.values())):
            first_call = len(shown)
            c.executemany(
                "INSERT INTO items (id, title, source, published, first_seen, score) "
                "VALUES (?,?,?,?,?,?)",
                [(r["id"], r["title"], r["source"], r["published"], r["first_seen"], r["score"])
                 for r in rows if nights[r["id"]] == night])
            c.commit()
            with redirect_stdout(io.StringIO()):
                group_news.main()
            if len(shown) > first_call:
                firsts.append(shown[first_call])
        c.row_factory = sqlite3.Row
        out = [dict(x) for x in c.execute("SELECT * FROM items")]
        c.close()
    finally:
        for k, v in keep.items():
            setattr(group_news, k, v)
        group_news.time.sleep = keep_sleep
        os.remove(path)
    return out, firsts


def _judge(produced, rows, story_of, judged):
    pieces = fx.expected_pieces(rows, story_of)
    want = {p for s, p in pieces if s in judged}
    lines = []
    for s, piece, sizes in fx.scattered(produced, pieces, judged):
        lines.append(f"SPLIT: {s!r} ({len(piece)} rows) over {len(sizes)} cards, sizes {sizes[:12]}"
                     f"{' ...' if len(sizes) > 12 else ''}")
    for p in fx.overmerged(produced, story_of, judged):
        lines.append(f"OVER-MERGE: one card fuses {sorted({story_of[i] for i in p})}")
    whole = {p for p in produced if any(p == w for w in want)}
    return whole == want and not lines, lines


def check_cross_night(results, frozen, expected):
    for case in fx.CASES:
        rows = fx.case_rows(frozen, case)
        story_of, judged, problems = fx.judgment(expected, case, rows)
        if problems:
            results.append((f"cross-night: {case}, one pass (control)", False, problems))
            results.append((f"cross-night: {case}, real nights", False, problems))
            continue
        # stories the replay asserts = the judged happenings with 2+ rows (singles can't split)
        multi = {s for s in judged if sum(1 for i in story_of if story_of[i] == s) > 1}
        labeled, _ = replay(rows, story_of, {r["id"]: "one" for r in rows})
        ok, lines = _judge(fx.cards_of(labeled), rows, story_of, multi)
        results.append((f"cross-night: {case}, one pass (control)", ok, lines))

        nights = {r["id"]: fx.labeling_night(r) for r in rows}
        spans = [s for s in multi if len({nights[i] for i in story_of if story_of[i] == s}) > 1]
        if not spans:
            results.append((f"cross-night: {case}, real nights", False,
                            ["no story spans two labeling nights — the case tests nothing"]))
            continue
        labeled, firsts = replay(rows, story_of, nights)
        ok, lines = _judge(fx.cards_of(labeled), rows, story_of, multi)
        lines.append(f"({len(spans)} stories span several labeling nights; {len(set(nights.values()))} "
                     f"nights replayed; most labels the labeler was shown at the start of any "
                     f"night: {max(firsts, default=0)})")
        results.append((f"cross-night: {case}, real nights", ok, lines))


def main():
    sys.stdout.reconfigure(errors="replace")     # headlines on a Windows console (cp1252)
    folder = sys.argv[1] if len(sys.argv) > 1 else fx.HERE
    frozen, expected = fx.load(folder)
    results = []
    check_detectors_fire(results, frozen, expected)
    check_merge(results, frozen, expected)
    check_split(results, frozen, expected)
    check_cross_night(results, frozen, expected)

    failed = []
    for label, ok, lines in results:
        known = label in KNOWN_FAILING
        if ok and known:
            failed.append(label)
            print(f"FAIL  {label} — now PASSES: take it off KNOWN_FAILING (and update TODO.md)")
        elif ok:
            print(f"ok    {label}")
        elif known:
            print(f"KNOWN FAILURE (expected today)  {label}")
        else:
            failed.append(label)
            print(f"FAIL  {label}")
        for x in lines:
            if not ok or x.startswith("("):
                print(f"        {x}")
    if failed:
        print(f"FAIL test_news_clustering ({len(failed)} failing)")
        sys.exit(1)
    print("OK test_news_clustering")


if __name__ == "__main__":
    main()
