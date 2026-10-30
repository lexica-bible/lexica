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
     that row. So the only way it can split a story is the night boundary. The rows labeled in
     the June regroup count as one night. Every story labeled in ONE pass is the control.
     The replay runs the nightly with the past-label list (group_news.pick_known) AND the reuse
     check (group_news.check_reuse) switched ON, whatever the shipped switch NIGHTLY_SEED says —
     it stays OFF in the nightly until relabel_check.py --run --list-on passes on PA. The reuse
     check's stand-in answers from expected.json's judgment, so it is always right: the replay
     proves the mechanism, not the live AI's answers. With the list alone (attempts 1/1b) the
     three passed here and FAILED live on fusion; with the list off they fail here (each night
     starts empty). Also checked: the cap, the rules of pick_known on made-up pools, and that no
     clearly-other story lands on the encyclical card (+ how many were SHOWN its label — the
     fusion exposure only the live run can judge). Call counts are printed per sample.
  4. THEME PAIRS — the 12 same-theme rows (11 after the 15419 ruling, +1 live attempt-5 miss) the live labeler fused: the labeler stand-in is made to
     take the earlier label whenever it's shown (what the live AI did); the reuse check must turn
     every one down. Built-in known positive: with the check answering yes, all 12 must fuse —
     and relabel_check.py's two-column fusion count must read all 12 as THROUGH REUSE.
  5. FUSION SPLIT — the other side of that count: the stored labels' pinned fusions (made inside
     the one June-29 pass) must read as SAME-NIGHT, none as through-reuse.

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
# Restored 2026-10-30: the bounded label list (group_news.pick_known) flips all three in the
# replay, but failed the LIVE fusion check on Haiku AND on Sonnet, so group_news.NIGHTLY_SEED is OFF.
# Emptied 2026-10-30 (attempt 4): with the past-label list + reuse check on, the three real-nights
# cases and the theme-pairs check pass in the replay. The shipped switch (group_news.NIGHTLY_SEED)
# stays OFF until relabel_check.py --run --list-on passes on PA; the replay tests the design.
KNOWN_FAILING = set()


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

_B36 = "0123456789abcdefghijklmnopqrstuvwxyz"


def story_tag(story_of, story):
    """A 2-character tag for a story, appended to the stand-in's labels as ' ~xx'. Two characters
    on purpose: group_news's word match ignores words under 3 letters, so the tag can't help or
    hurt which labels get shown — the label reads, to the matcher, as the real labeler's wording."""
    order = sorted(set(story_of.values()))
    n = order.index(story)
    return " ~" + _B36[n // 36] + _B36[n % 36]


def _stand_in(story_of, stored, grab=None):
    """label_batch replacement: never confuses two stories (each label carries its story's tag);
    inside one call a story gets one label; a known label of the same story is reused if shown,
    else the real labeler's own wording for that row (+ the tag).
    grab = {row id: story tag}: for those rows ONLY, act like the live labeler did — if a label of
    that (different) story is on the list, take it. That's the theme-pairs check's fusion attempt."""
    shown = []
    tag = {s: story_tag(story_of, s) for s in set(story_of.values())}
    grab = grab or {}

    def label_batch(client, batch, known, examples=None, avoid=None):
        if avoid is None:                 # the fresh-label call isn't a labeler call of its own
            shown.append(len(known))
        else:
            label_batch.fresh += 1
        calls.append(([r["id"] for r in batch], list(known), label_batch.past))
        out, this_call = {}, {}
        for r in batch:
            took = next((k for k in known if r["id"] in grab and k.endswith(grab[r["id"]])), None)
            if took:
                label_batch.grabbed.add(r["id"])
                out[r["id"]] = took
                continue
            s = story_of[r["id"]]
            if s not in this_call:
                reuse = next((k for k in known if k.endswith(tag[s])), None)
                this_call[s] = reuse or f"{stored[r['id']]}{tag[s]}"
            out[r["id"]] = this_call[s]
        return out

    calls = []                     # (batch ids, labels shown, labels that existed before this
    label_batch.calls = calls      # night) per call — for the fusion + theme-pair checks
    label_batch.past = frozenset()
    label_batch.fresh = 0          # fresh-label calls (after a reuse was turned down)
    label_batch.grabbed = set()    # grab rows that did take the other story's label
    return label_batch, shown


def _judge_stand_in(story_of, always_yes=False):
    """confirm_reuse replacement — HONEST ABOUT WHAT IT IS: it answers from the hand judgment in
    expected.json (yes only if the new headline and the label's stored headlines are judged the
    same happening), i.e. it is always right. So a replay with it proves the MECHANISM — a "no"
    really blocks the reuse and the headline gets a fresh label; a "yes" keeps cross-night merges
    — NOT that the live AI answers right. That is what relabel_check.py --run --list-on measures
    on PA. always_yes = the reuse check doing nothing (the attempt-1 design), for known positives."""
    def confirm_reuse(client, label, stored, rows):
        confirm_reuse.calls += 1
        confirm_reuse.asked += len(rows)
        return {r["id"]: always_yes or all(story_of.get(h[3]) == story_of[r["id"]] for h in stored)
                for r in rows}
    confirm_reuse.calls = confirm_reuse.asked = 0
    return confirm_reuse


def replay(rows, story_of, nights, list_on=True, grab=None, always_yes=False):
    """Insert each night's rows into a scratch news.db and run group_news.main() after each one
    (nightly mode: unlabeled rows only), then read back the labels it wrote. list_on = the past-
    label list + reuse check switched on (NIGHTLY_SEED) for the replay, whatever the shipped
    setting: the switch stays OFF in the nightly until a live relabel_check passes, so this tests
    the design. Call counts land on replay.counts."""
    stored = {r["id"]: r["event"] or f"(unlabeled #{r['id']})" for r in rows}
    stub, shown = _stand_in(story_of, stored, grab)
    judge = _judge_stand_in(story_of, always_yes)
    firsts = []                    # labels the labeler was shown at the FIRST call of each night
    night_of = {}                  # {id: night it was labeled} — for fx.reuse_joiners
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    keep = {k: getattr(group_news, k) for k in
            ("DB_PATH", "REGROUP", "DRY_RUN", "MIN", "BATCH", "build_client", "label_batch",
             "confirm_reuse", "NIGHTLY_SEED")}
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
        group_news.confirm_reuse = judge
        group_news.NIGHTLY_SEED = list_on
        group_news.time.sleep = lambda s: None
        for night in sorted(set(nights.values())):
            first_call = len(shown)
            stub.past = frozenset(x[0] for x in c.execute(
                "SELECT DISTINCT event FROM items WHERE event IS NOT NULL AND event != ''"))
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
            for (i,) in c.execute("SELECT id FROM items WHERE event IS NOT NULL AND event != ''"):
                night_of.setdefault(i, night)    # the night it was LABELED (a skip retries later)
        c.row_factory = sqlite3.Row
        out = [dict(x) for x in c.execute("SELECT * FROM items")]
        c.close()
    finally:
        for k, v in keep.items():
            setattr(group_news, k, v)
        group_news.time.sleep = keep_sleep
        os.remove(path)
    replay.last_calls = stub.calls
    replay.most_shown = max(shown, default=0)
    replay.grabbed = stub.grabbed
    replay.night_of = night_of
    replay.counts = {"nights": len(set(nights.values())), "labeler": len(shown),
                     "checks": judge.calls, "asked": judge.asked, "fresh": stub.fresh}
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
        cards = fx.cards_of(labeled)
        ok, lines = _judge(cards, rows, story_of, multi)
        if replay.most_shown > group_news.SEED_MAX:
            ok = False
            lines.append(f"a nightly call was shown {replay.most_shown} past labels — over the "
                         f"cap of {group_news.SEED_MAX}")
        c = replay.counts
        lines.append(f"({len(spans)} stories span several labeling nights; {c['nights']} nights "
                     f"replayed; most labels shown at the start of a night: "
                     f"{max(firsts, default=0)}; most in any call: {replay.most_shown} "
                     f"(cap {group_news.SEED_MAX}); calls: labeler {c['labeler']}, reuse checks "
                     f"{c['checks']} ({c['asked']} headlines), fresh-label {c['fresh']})")
        results.append((f"cross-night: {case}, real nights", ok, lines))
        if case == "merge_encyclical":
            check_fusion(results, rows, labeled, cards, expected, replay.last_calls)


def check_fusion(results, rows, labeled, cards, expected, calls):
    """Task-4 check on the encyclical replay. The stand-in never confuses two stories, so this
    can't show whether the REAL labeler over-fuses (that's relabel_check.py on PA). What it does
    show: (a) the shown-labels mechanism itself puts no clearly-other story on the encyclical card
    — including the CI-pinned June mistakes; (b) EXPOSURE — how many clearly-other rows were
    labeled in a call that was SHOWN an encyclical label: those are the rows the live AI could
    wrongly fuse, i.e. what the PA run has to come back clean on."""
    e = expected["merge_encyclical"]
    m = fx.merge_picture(labeled, cards, expected)
    pinned = {int(k) for k in e["pins"]["not_on_card"]}
    lines, ok = [], not m["not_on"]
    if m["not_on"]:
        lines.append("clearly-other stories landed on the encyclical card:")
        lines += fx.describe(m["not_on"], labeled)
    story_of, _, _ = fx.judgment(expected, "merge_encyclical", rows)
    enc = story_tag(story_of, fx.ENCYCLICAL)
    nots = {int(k) for k in e["not"]}
    exposed = set()
    for ids, known, _ in calls:
        if any(k.endswith(enc) for k in known):
            exposed |= nots & set(ids)
    lines.append(f"(encyclical card: {len(m['core_on'])} of {m['core_total']} encyclical rows; "
                 f"clearly-other rows on it: {len(m['not_on'])}, of the 6 CI-pinned June "
                 f"mistakes: {len(m['not_on'] & pinned)}; clearly-other rows SHOWN an encyclical "
                 f"label at labeling time: {len(exposed)} of {len(nots)} — the live AI's fusion "
                 f"exposure, measured on PA by relabel_check.py)")
    results.append(("fusion: shown labels put no other story on the encyclical card", ok, lines))


# Same theme, NEXT happening: pairs the live labeler FUSED when shown the earlier row's label
# (cross-night attempt 1 on Haiku 2026-10-29, 1b on Sonnet 2026-10-30; TODO_ARCHIVE). Every row
# here is hand-judged a different happening from the earlier one (expected.json), each pair is
# within the 14-day reach and labeled on a LATER night. (later id, earlier id, what):
THEME_PAIRS = {
    "split_sunday": [
        (24909, 24082, "Dr. O 'Sunday Law Update' episode Oct 9 vs Oct 3 (same headline)"),
        (19923, 16144, "union enforcement campaign Sep 4 vs Polish union fine proposal Aug 21"),
        (27299, 24079, "Sunday Alliance manifesto Oct 14 vs Alliance free-Sundays demand Oct 3"),
        # (15419, 14756) the European unions' reaction to the pope's Aug 13 Sunday call was here:
        # ruled the SAME story by JP 2026-10-30 (a reaction = same happening, the house rule), so it
        # moved into that happening in expected.json and is no longer a fusion — 11 rows now.
        (12472, 10368, "Greece Sunday strike Jul 27 vs Roman Catholics' Sunday-rest call Jul 14"),
        # added 2026-10-30 (attempt 6): fused LIVE in the attempt-5 rerun with Sonnet checking
        (14621, 13476, "the pope's Aug 12-13 Sunday call vs the unions/churches vow Aug 3"),
    ],
}
# ...and encyclical-sample rows judged OTHER happenings that joined the encyclical's label live:
# the pope's Aug 28 machines message (Sonnet, 6 rows) and the Vatican's own AI-use guidelines
# (Haiku). Sonnet's further "Sep/Oct AI remarks" were not recorded by id, so they're not here.
THEME_ENCYCLICAL = (17063, 17071, 17131, 17143, 17162, 17315, 5251)


THEME_CHECK = "theme pairs: earlier label never KEPT on the next happening"


def check_theme_pairs(results, frozen, expected):
    """The direct test of what failed live: shown an earlier label, the AI reuses it for the next
    happening of the same theme. The labeler stand-in is made to DO exactly that for these 12 rows
    (grab: take the other story's label whenever it's on the list), with the list + reuse check
    on. Fails if the earlier label is still on the row at the end. Changed 2026-10-30 from "never
    SHOWN" (attempt 2's bar): attempt 4 shows the label on purpose and checks each reuse.
    The reuse check's stand-in answers from the hand judgment (_judge_stand_in), so a pass proves
    a "no" blocks the reuse — not that the live AI says no; relabel_check.py measures that.
    Built-in known positive: the same run with the reuse check answering yes every time (= the
    attempt-1 design) must end with ALL 12 fused, or the check can't see a fusion at all.
    A row that never got the chance to grab (label not on its list) fails as testing nothing."""
    lines, ok = [], True
    totals = {"grabbed": 0, "kept": 0, "blocked_fused": 0, "read_via": 0}
    for case in ("split_sunday", "merge_encyclical"):
        rows = fx.case_rows(frozen, case)
        by = {r["id"]: r for r in rows}
        story_of, _, problems = fx.judgment(expected, case, rows)
        if problems:
            results.append((THEME_CHECK, False, problems))
            return
        nights = {r["id"]: fx.labeling_night(r) for r in rows}
        if case == "merge_encyclical":
            enc = story_tag(story_of, fx.ENCYCLICAL)
            targets = [(i, enc, expected[case]["not"][str(i)]) for i in THEME_ENCYCLICAL]
        else:
            targets = []
            for later, earlier, what in THEME_PAIRS[case]:
                if nights[earlier] >= nights[later] or abs(
                        group_news._day(by[later]["published"])
                        - group_news._day(by[earlier]["published"])) > group_news.REACH_DAYS:
                    ok = False
                    lines.append(f"pair {later}/{earlier} tests nothing (same night or out of reach)")
                    continue
                targets.append((later, story_tag(story_of, story_of[earlier]), what))
        grab = {i: t for i, t, _ in targets}
        asserted = {s for s in story_of.values()
                    if not s.startswith(("border:", "unsure:"))}
        for always_yes in (False, True):
            labeled, _ = replay(rows, story_of, nights, grab=grab, always_yes=always_yes)
            label = {r["id"]: r["event"] or "" for r in labeled}
            grabbed = replay.grabbed
            joiners = fx.reuse_joiners(labeled, replay.night_of, story_of, asserted)
            via, _ = fx.split_fusions(fx.overmerged(fx.cards_of(labeled), story_of, asserted),
                                      joiners)
            via_ids = set().union(*via) if via else set()
            for i, t, what in targets:
                fused = label[i].endswith(t)
                if i not in grabbed:
                    ok = False
                    if not always_yes:
                        lines.append(f"id {i} ({what}): the earlier label was never on its list "
                                     f"— tests nothing")
                elif not always_yes:
                    totals["grabbed"] += 1
                    if fused:
                        ok = False
                        totals["kept"] += 1
                        lines.append(f"id {i} ({what}): KEPT {label[i]!r}")
                    elif not label[i]:
                        ok = False
                        lines.append(f"id {i} ({what}): turned down but left with NO label")
                elif fused:
                    totals["blocked_fused"] += 1
                    if i not in joiners or i not in via_ids:    # the scored column's known positive
                        ok = False
                        lines.append(f"known positive: id {i} fused THROUGH a reused label but the "
                                     f"two-column count calls it same-night")
                    else:
                        totals["read_via"] += 1
                else:
                    ok = False
                    lines.append(f"known positive: with the reuse check answering yes, id {i} "
                                 f"did NOT end fused — the check can't see this fusion")
    n = sum(len(v) for v in THEME_PAIRS.values()) + len(THEME_ENCYCLICAL)
    lines.append(f"({n} same-theme rows; {totals['grabbed']} took the earlier label, "
                 f"{totals['kept']} kept after the reuse check; known positive: "
                 f"{totals['blocked_fused']} of {n} fused with the check answering yes, "
                 f"{totals['read_via']} of them counted as through-reuse fusions)")
    results.append((THEME_CHECK, ok, lines))


def check_fusion_split(results, frozen, expected):
    """The other side of relabel_check.py's two fusion columns (through a reused earlier-night
    label = scored; same-night = the labeler's own, reported). Known positive for SAME-NIGHT: the
    stored labels' pinned fusions were all made inside one labeler run (the June-29 regroup) —
    the 6 pinned other stories on the encyclical card and the pinned Sunday over-merge must read
    as same-night, none as through-reuse. (The through-reuse side's known positive is in the
    theme-pairs check: 12 forced fusions across nights.)"""
    lines = []
    rows = fx.case_rows(frozen, "merge_encyclical")
    story_of, _, _ = fx.judgment(expected, "merge_encyclical", rows)
    night_of = {r["id"]: fx.labeling_night(r) for r in rows}
    asserted = {s for s in story_of.values() if not s.startswith("border:")}
    joiners = fx.reuse_joiners(rows, night_of, story_of, asserted)
    pinned = {int(k) for k in expected["merge_encyclical"]["pins"]["not_on_card"]}
    on = fx.merge_picture(rows, fx.cards_of(rows), expected)["not_on"]
    if not pinned or not pinned <= on:
        lines.append(f"encyclical pins not on the card in the stored labels — tests nothing: "
                     f"{sorted(pinned - on)}")
    if on & joiners:
        lines.append(f"stored same-night encyclical fusions read as through-reuse: "
                     f"{sorted(on & joiners)}")
    srows = fx.case_rows(frozen, "split_sunday")
    sstory, sjudged, _ = fx.judgment(expected, "split_sunday", srows)
    snight = {r["id"]: fx.labeling_night(r) for r in srows}
    via, same = fx.split_fusions(fx.overmerged(fx.cards_of(srows), sstory, sjudged),
                                 fx.reuse_joiners(srows, snight, sstory, sjudged))
    want = {frozenset(c["ids"]) for c in expected["split_sunday"]["pins"]["overmerged_cards"]}
    if not want or set(same) != want or via:
        lines.append(f"stored Sunday over-merge not read as same-night only: via {len(via)}, "
                     f"same-night {[sorted(p) for p in same]}, pinned {[sorted(p) for p in want]}")
    ok = not lines
    lines.append(f"(stored labels: {len(on)} other stories on the encyclical card, "
                 f"{len(on & joiners)} through reuse; Sunday {len(via) + len(same)} over-merged "
                 f"card(s), {len(via)} through reuse)")
    results.append(("fusion split: same-night fusions not scored as through-reuse", ok, lines))


def check_seed_rules(results):
    """pick_known on made-up pools, one rule at a time: (1) a label with no article within
    REACH_DAYS of a headline is never shown; (2) the cap holds; (3) weak matches (< 2 shared words)
    are limited to LOOSE_MAX; (4) a label only ONE headline needs is shown even when many labels
    match another headline better — the crowding that broke the first version; (5) an undated
    batch is shown nothing; (6) every shown label comes with its example headline."""
    g, misses = group_news, []
    near, far = "2026-05-24", "2026-01-01"
    batch = [{"id": 1, "title": "Pope Leo encyclical artificial intelligence disarm - X",
              "published": "2026-06-01"},
             {"id": 2, "title": "Bergen County judge rules on American Dream mall Sunday case - Y",
              "published": "2026-06-01"}]
    pool = {}
    g.pool_add(pool, "Far Story", "Bergen County American Dream mall Sunday", far, 9)
    for i in range(g.SEED_MAX + 10):          # many STRONG matches for headline 1 (3+ shared words)
        g.pool_add(pool, f"Encyclical Piece {i}",      # ...that also brush headline 2 (2 words)
                   "Pope Leo encyclical artificial intelligence Sunday mall", near, 9)
    g.pool_add(pool, "Bergen Mall Sunday Suit", "American Dream mall Sunday lawsuit", near, 5)
    shown, examples = g.pick_known(pool, batch)
    if "Far Story" in shown:
        misses.append("(1) a label with no article within reach was shown")
    if len(shown) != g.SEED_MAX:
        misses.append(f"(2) cap not held: {len(shown)} shown, cap {g.SEED_MAX}")
    if "Bergen Mall Sunday Suit" not in shown:
        misses.append("(4) the label only headline 2 needs was crowded out")
    if any(not examples.get(k) for k in shown):
        misses.append("(6) a shown label has no example headline")
    weak = {}
    g.pool_add(weak, "Strong", "American Dream mall Sunday lawsuit", near, 5)
    for i in range(g.LOOSE_MAX + 15):
        g.pool_add(weak, f"Weak {i}", f"unrelated filler {i}", near, 9)
    ws, _ = g.pick_known(weak, batch)
    if ws[:1] != ["Strong"] or len(ws) != 1 + g.LOOSE_MAX:
        misses.append(f"(3) weak matches not limited: {len(ws)} shown, first {ws[:1]}")
    if g.pick_known(pool, [{"id": 3, "title": "x", "published": None}])[0]:
        misses.append("(5) an undated batch was shown labels")
    results.append(("seed rules: reach, cap, weak limit, no crowding", not misses, misses))


def check_ai_call(results):
    """label_batch's request + reply reading, on a fake client (no network): (1) the model is
    group_news.MODEL; (2) Haiku 4.5 keeps exactly the old settings, a newer model sends NO
    temperature (Sonnet 5.5 refuses temperature 0) and leaves room for thinking; (3) the reply is
    read by block type — a thinking block before the text is skipped; (4) a refusal or a cut-off
    reply raises (main() prints ERR) instead of being half-read."""
    from types import SimpleNamespace as NS
    g, misses = group_news, []

    class Fake:
        def __init__(self, blocks, stop="end_turn"):
            self.sent, self.reply = None, NS(content=blocks, stop_reason=stop)
            self.messages = self

        def create(self, **kw):
            self.sent = kw
            return self.reply

    good = [NS(type="thinking", thinking=""), NS(type="text", text='[{"id": 7, "event": "X Y Z"}]')]
    batch = [{"id": 7, "title": "headline"}]
    f = Fake(good)
    if g.label_batch(f, batch, []) != {7: "X Y Z"}:
        misses.append("(3) reply after a thinking block not read")
    if f.sent["model"] != g.MODEL:
        misses.append(f"(1) model sent {f.sent['model']!r}, MODEL is {g.MODEL!r}")
    if "temperature" in f.sent and not g.MODEL.startswith("claude-haiku-4-5"):
        misses.append("(2) temperature sent to a model that refuses it")
    if g._call_settings("claude-haiku-4-5-20251001") != {"max_tokens": 1600, "temperature": 0}:
        misses.append("(2) Haiku settings changed from the old call")
    if g._call_settings("claude-sonnet-5-5").get("max_tokens", 0) < 8000:
        misses.append("(2) Sonnet max_tokens leaves no room for thinking")
    for stop in ("refusal", "max_tokens"):
        try:
            g.label_batch(Fake(good, stop), batch, [])
            misses.append(f"(4) stop_reason {stop} did not raise")
        except RuntimeError:
            pass
    # (5) the request the switch-off nightly and --regroup send is the old one, byte for byte
    old = ("Existing labels already in use:\n  (none yet)\n\nGroup these headlines. Reuse a label "
           "above when it fits.\n\nid=7 | headline")
    if f.sent["messages"] != [{"role": "user", "content": old}] or f.sent["system"] != g.SYSTEM:
        misses.append("(5) the plain labeler request changed")
    # (6) the reuse check: on CHECK_MODEL with its own settings (no temperature on Sonnet, room to
    # think), the labeler untouched on MODEL; an id left out, or anything but true, is a no
    yes_no = [NS(type="thinking", thinking=""),
              NS(type="text", text='[{"id": 7, "reason": "a reaction [to the Oct 3 call]", '
                                   '"same": true}, {"id": 8, "reason": "new episode", '
                                   '"same": "yes"}]')]
    fc = Fake(yes_no)
    ans = g.confirm_reuse(fc, "X Y Z", [(9, "old headline", "2026-10-03", 1)],
                          [{"id": i, "title": "new", "published": "2026-10-09"} for i in (7, 8, 9)])
    if ans != {7: True, 8: False}:
        misses.append(f"(6) reuse-check reply misread: {ans}")
    if fc.sent["model"] != g.CHECK_MODEL or fc.sent["system"] != g.SYSTEM_CONFIRM or any(
            fc.sent.get(k) != v for k, v in g._call_settings(g.CHECK_MODEL).items()):
        misses.append("(6) reuse check not on CHECK_MODEL + its settings")
    if "temperature" in fc.sent and not g.CHECK_MODEL.startswith("claude-haiku-4-5"):
        misses.append("(6) temperature sent to a check model that refuses it")
    if f.sent["model"] != g.MODEL or g.MODEL == g.CHECK_MODEL:
        misses.append("(6) labeler and reuse check no longer on separate model settings")
    if "2026-10-03" not in fc.sent["messages"][0]["content"] or \
            "2026-10-09" not in fc.sent["messages"][0]["content"]:
        misses.append("(6) reuse check doesn't show the publish dates")
    sc = g.SYSTEM_CONFIRM
    if "keys in this order: id, reason, same" not in sc or "Examples:" not in sc or \
            "LATER statement" not in sc or "REACTIONS" not in sc:
        misses.append("(6) check prompt lost the reason-first / examples / later-vs-reaction rule")
    # (7) a note after the answer is ignored even with a ']' in it (lost 11 live checks 10-30);
    # two answers raise; a plain answer and an empty reply read as before
    rd = g._read_array
    if rd('[{"id": 7, "same": true}]\n\nNote: id 7 [the Oct 3 piece] is a re-run.') != \
            [{"id": 7, "same": True}]:
        misses.append("(7) a trailing note with ']' broke the read")
    if rd('[{"id": 7, "event": "A"}]') != [{"id": 7, "event": "A"}] or rd("[]") != [] \
            or rd("no answer here") != []:
        misses.append("(7) plain / empty replies no longer read as before")
    try:
        rd('[{"id": 7, "same": true}]\nCorrection:\n[{"id": 7, "same": false}]')
        misses.append("(7) a reply with two answers was read instead of raising")
    except ValueError:
        pass
    results.append(("AI call: labeler + check model settings, Sonnet-safe, reply read by type",
                    not misses, misses))


# rows deliberately NOT in the check's examples (attempt 6): the scored misses that test whether the
# check learned the RULE — the Alliance pair (missed in both attempt-5 runs) and the 17040/17505 edge
HELD_OUT = {27299, 24079, 17040, 17505}


def examples_problems(examples, frozen, expected):
    """Each worked example in the reuse-check prompt must be REAL and agree with the hand judgment:
    both headlines are frozen rows (outlet suffix aside) with those publish dates, both stories are
    asserted, SAME is True exactly when expected.json puts the two rows in one story, and no
    held-out row is used. Also: every example is actually in SYSTEM_CONFIRM."""
    by, story, asserted = {}, {}, set()
    for case in fx.CASES:
        rows = fx.case_rows(frozen, case)
        s_of, judged, _ = fx.judgment(expected, case, rows)
        for r in rows:
            by[r["id"]] = r
        story.update(s_of)
        asserted |= judged | ({s for s in s_of.values() if s.startswith("not:")}
                              if case == "merge_encyclical" else set())
    out = []
    for ex in examples:
        oid, old, od, nid, new, nd, same, _ = ex
        for i, t, d in ((oid, old, od), (nid, new, nd)):
            r = by.get(i)
            if not r:
                out.append(f"example row {i} is not a frozen row")
                continue
            if not (r["title"] == t or r["title"].startswith(t + " - ")) or \
                    (r["published"] or "")[:10] != d:
                out.append(f"example row {i}: headline/date don't match frozen.json")
            if story[i] not in asserted:
                out.append(f"example row {i}: its story isn't asserted in expected.json")
            if i in HELD_OUT:
                out.append(f"example uses held-out row {i}")
        if oid in story and nid in story and (story[oid] == story[nid]) != same:
            out.append(f"example {nid} vs {oid} says {'SAME' if same else 'DIFFERENT'}, "
                       f"expected.json says the opposite")
    return out


def check_confirm_examples(results, frozen, expected):
    g = group_news
    misses = examples_problems(g.CONFIRM_EXAMPLES, frozen, expected)
    for ex in g.CONFIRM_EXAMPLES:
        if ex[1] not in g.SYSTEM_CONFIRM or ex[4] not in g.SYSTEM_CONFIRM:
            misses.append(f"example {ex[3]} vs {ex[0]} is not in the check prompt")
    # known positive: the same check must catch a flipped verdict and a held-out row
    bad = list(g.CONFIRM_EXAMPLES)
    bad[0] = bad[0][:6] + (not bad[0][6],) + bad[0][7:]
    if not examples_problems(bad, frozen, expected):
        misses.append("known positive: a flipped SAME/DIFFERENT example was not caught")
    rows = {r["id"]: r for r in fx.case_rows(frozen, "split_sunday")}
    held = (24079, rows[24079]["title"], rows[24079]["published"][:10],
            27299, rows[27299]["title"], rows[27299]["published"][:10], False, "x")
    if not examples_problems([held], frozen, expected):
        misses.append("known positive: an example using a held-out row was not caught")
    n_diff = sum(1 for e in g.CONFIRM_EXAMPLES if not e[6])
    results.append(("reuse-check examples: real rows, agree with the hand judgment, none held out",
                    not misses, misses + [f"({n_diff} DIFFERENT + {len(g.CONFIRM_EXAMPLES) - n_diff} "
                                          f"SAME examples; held out: {sorted(HELD_OUT)})"]))


def main():
    sys.stdout.reconfigure(errors="replace")     # headlines on a Windows console (cp1252)
    folder = sys.argv[1] if len(sys.argv) > 1 else fx.HERE
    frozen, expected = fx.load(folder)
    results = []
    check_detectors_fire(results, frozen, expected)
    check_seed_rules(results)
    check_ai_call(results)
    check_confirm_examples(results, frozen, expected)
    check_merge(results, frozen, expected)
    check_split(results, frozen, expected)
    check_cross_night(results, frozen, expected)
    check_theme_pairs(results, frozen, expected)
    check_fusion_split(results, frozen, expected)

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
