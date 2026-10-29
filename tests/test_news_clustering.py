#!/usr/bin/env python3
"""News cards from FROZEN real rows — the clustering fixtures (ruled JP 2026-10-25).

Cards come from two layers: (1) the AI labeler (scripts/news/group_news.py) names each
article's event; (2) views_news._group puts same-label rows on one card, split at a >14-day
gap. This test runs the REAL layer-2 code on rows frozen off PA (tests/fixtures/news_clustering/
frozen.json, copied by freeze_sample.py) and checks the cards against the hand-judged answer
(expected.json). Layer 1 is an AI call, so it is NOT run here — its check is the by-hand
relabel_check.py in the same folder, run before any clustering change.

  1. MERGE  — the Pope Leo AI encyclical coverage, hundreds of outlets, stays one card.
  2. SPLIT  — Sunday-law headlines about different happenings (Poland trade ban, NJ mall
              lawsuit, NY Chick-fil-A bill, ...) land on separate cards, not one theme bucket.
  3. CROSS-NIGHT — one story whose coverage came in over two nights must still be one card.
     group_news.py starts every run with an EMPTY list of known labels, so the second night
     can't reuse the first night's label. This runs the REAL group_news.main() night by night
     on a scratch copy, with the AI swapped for a stand-in that (a) is perfectly consistent
     inside one call and (b) reuses any label it is SHOWN for the same story, else uses the
     wording the real labeler actually gave that row. So the only way it can fail is the
     night boundary itself. A one-night run of the same rows is the control (must pass).
     **KNOWN FAILURE today** (no clustering fix yet) — reported, not counted. When the fix
     lands this case passes and the test then FAILS until it is taken off KNOWN_FAILING.

No database, no network, no AI: runs offline in CI + pre-commit.
  python tests/test_news_clustering.py              (uses tests/fixtures/news_clustering/)
  python tests/test_news_clustering.py <folder>     (another frozen.json + expected.json)
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
import views_news  # noqa: E402
from scripts.news import group_news  # noqa: E402

# Cases expected to fail until the cross-night relabeling fix lands. Strict: a case listed
# here that PASSES fails the run, so the list can't go stale.
KNOWN_FAILING = {"cross_night: two nights"}


def cards_of(rows):
    """The card grouping exactly as the feed builds it (views_news._group, labels on)."""
    return [{a["id"] for a in c["arts"]} for c in views_news._group(rows, True)]


def night_of(row):
    return (row.get("first_seen") or "")[:10]


# ---------- cross-night: real group_news.main(), night by night, AI stood in ----------

def _stand_in(story_of, story_labels, stored):
    """label_batch replacement. Inside one call every row of a story gets ONE label; that label
    is a known label of the same story if the labeler was shown one, else the wording the real
    labeler gave the first such row. Records what it was shown, for the sanity checks."""
    shown = []

    def label_batch(client, batch, known):
        shown.append(list(known))
        out, this_call = {}, {}
        for r in batch:
            s = story_of[r["id"]]
            if s not in this_call:
                reuse = next((k for k in known if k in story_labels[s]), None)
                this_call[s] = reuse or stored[r["id"]]
            out[r["id"]] = this_call[s]
        return out

    return label_batch, shown


def simulate(rows, expected, nights):
    """Insert each night's rows into a scratch news.db, run group_news.main() after each night
    (unlabeled rows only — the nightly mode), then build cards from the labels it wrote.
    `nights` maps id -> night key; one key for every row = the one-night control."""
    story_of, story_labels, stored = {}, {}, {}
    for name, members in fx.expected_cards(expected, "cross_night"):
        for i in members:
            story_of[i] = name
    for r in rows:
        stored[r["id"]] = r["event"] or f"(unlabeled #{r['id']})"
        story_labels.setdefault(story_of[r["id"]], set()).add(stored[r["id"]])

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    stub, shown = _stand_in(story_of, story_labels, stored)
    saved = {k: getattr(group_news, k) for k in
             ("DB_PATH", "REGROUP", "DRY_RUN", "MIN", "BATCH", "build_client", "label_batch")}
    saved_sleep = group_news.time.sleep
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
            c.executemany(
                "INSERT INTO items (id, title, source, published, first_seen, score) "
                "VALUES (?,?,?,?,?,?)",
                [(r["id"], r["title"], r["source"], r["published"], r["first_seen"], r["score"])
                 for r in rows if nights[r["id"]] == night])
            c.commit()
            with redirect_stdout(io.StringIO()):
                group_news.main()
        c.row_factory = sqlite3.Row
        out = [dict(x) for x in c.execute("SELECT * FROM items")]
        c.close()
    finally:
        for k, v in saved.items():
            setattr(group_news, k, v)
        group_news.time.sleep = saved_sleep
        os.remove(path)
    return out, shown


# ---------------------------------- the checks ----------------------------------

def check_detector_fires(results, frozen, expected):
    """The comparison must catch a wrong grouping before its 'pass' means anything: fuse the
    split case into one card, cut the merge case's biggest card in half."""
    rows = fx.case_rows(frozen, "split_sunday")
    cards = fx.expected_cards(expected, "split_sunday")
    ok1, lines1 = fx.compare([{r["id"] for r in rows}], cards)
    big = max(fx.expected_cards(expected, "merge_encyclical"), key=lambda c: len(c[1]))
    half = sorted(big[1])
    others = [m for n, m in fx.expected_cards(expected, "merge_encyclical") if m != big[1]]
    ok2, lines2 = fx.compare([set(half[::2]), set(half[1::2])] + others,
                             fx.expected_cards(expected, "merge_encyclical"))
    fired = (len(cards) < 2 or (not ok1 and any("OVER-MERGE" in x for x in lines1))) and \
            (len(half) < 2 or (not ok2 and any("SPLIT" in x for x in lines2)))
    results.append(("detector fires on a known-wrong grouping", fired,
                    [] if fired else ["comparison passed a deliberately wrong grouping"]))


def check_case(results, frozen, expected, case, label):
    rows = fx.case_rows(frozen, case)
    cards = fx.expected_cards(expected, case)
    problems = fx.check_expected_complete(rows, cards)
    if problems:
        results.append((label, False, problems))
        return
    title = {r["id"]: r["title"] or "" for r in rows}
    ok, lines = fx.compare(cards_of(rows), cards, title.get)
    results.append((label, ok, lines))


def check_cross_night(results, frozen, expected):
    rows = fx.case_rows(frozen, "cross_night")
    cards = fx.expected_cards(expected, "cross_night")
    problems = fx.check_expected_complete(rows, cards)
    if problems:
        results.append(("cross_night: one night (control)", False, problems))
        results.append(("cross_night: two nights", False, problems))
        return
    title = {r["id"]: r["title"] or "" for r in rows}

    labeled, _ = simulate(rows, expected, {r["id"]: "one" for r in rows})
    ok, lines = fx.compare(cards_of(labeled), cards, title.get)
    results.append(("cross_night: one night (control)", ok, lines))

    nights = {r["id"]: night_of(r) for r in rows}
    spans = [n for n, m in cards if len({nights[i] for i in m}) > 1]
    if not spans:
        results.append(("cross_night: two nights", False,
                        ["no expected story spans two first-pull nights — the case tests nothing"]))
        return
    labeled, shown = simulate(rows, expected, nights)
    ok, lines = fx.compare(cards_of(labeled), cards, title.get)
    lines.append(f"(stories spanning >1 night: {len(spans)}; nights run: "
                 f"{len(set(nights.values()))}; known labels shown at the start of each "
                 f"night's first call: {[len(s) for s in shown]})")
    results.append(("cross_night: two nights", ok, lines))


def main():
    sys.stdout.reconfigure(errors="replace")     # headlines on a Windows console (cp1252)
    folder = sys.argv[1] if len(sys.argv) > 1 else fx.HERE
    frozen, expected = fx.load(folder)
    results = []
    check_detector_fires(results, frozen, expected)
    check_case(results, frozen, expected, "merge_encyclical", "merge: encyclical stays one card")
    check_case(results, frozen, expected, "split_sunday", "split: Sunday-law happenings separate")
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
        if not ok:
            for x in lines:
                print(f"        {x}")
    if failed:
        print(f"FAIL test_news_clustering ({len(failed)} failing)")
        sys.exit(1)
    print("OK test_news_clustering")


if __name__ == "__main__":
    main()
