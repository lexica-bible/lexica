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
     A bounded past-label list (group_news.pick_known, switch NIGHTLY_SEED) flips all three real-
     nights cases here, but FAILED the live fusion check on PA on Haiku (2026-10-29) and on Sonnet
     (2026-10-30), so the switch is OFF: each night starts from an EMPTY label list and the three
     are **KNOWN FAILURES**. When a fix passes BOTH, these pass and the test then FAILS until
     they're taken off KNOWN_FAILING. Also checked: the rules of pick_known on made-up pools, the cap
     (when on), and that no clearly-other story lands on the encyclical card (+ how many were
     SHOWN its label — the fusion exposure only relabel_check.py on PA can judge).

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

_B36 = "0123456789abcdefghijklmnopqrstuvwxyz"


def story_tag(story_of, story):
    """A 2-character tag for a story, appended to the stand-in's labels as ' ~xx'. Two characters
    on purpose: group_news's word match ignores words under 3 letters, so the tag can't help or
    hurt which labels get shown — the label reads, to the matcher, as the real labeler's wording."""
    order = sorted(set(story_of.values()))
    n = order.index(story)
    return " ~" + _B36[n // 36] + _B36[n % 36]


def _stand_in(story_of, stored):
    """label_batch replacement: never confuses two stories (each label carries its story's tag);
    inside one call a story gets one label; a known label of the same story is reused if shown,
    else the real labeler's own wording for that row (+ the tag)."""
    shown = []
    tag = {s: story_tag(story_of, s) for s in set(story_of.values())}

    def label_batch(client, batch, known, examples=None):
        shown.append(len(known))
        calls.append(([r["id"] for r in batch], list(known)))
        out, this_call = {}, {}
        for r in batch:
            s = story_of[r["id"]]
            if s not in this_call:
                reuse = next((k for k in known if k.endswith(tag[s])), None)
                this_call[s] = reuse or f"{stored[r['id']]}{tag[s]}"
            out[r["id"]] = this_call[s]
        return out

    calls = []                     # (batch ids, labels shown) per call, for the fusion check
    label_batch.calls = calls
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
    replay.last_calls = stub.calls
    replay.most_shown = max(shown, default=0)
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
        if group_news.NIGHTLY_SEED and replay.most_shown > group_news.SEED_MAX:
            ok = False
            lines.append(f"a nightly call was shown {replay.most_shown} past labels — over the "
                         f"cap of {group_news.SEED_MAX}")
        lines.append(f"({len(spans)} stories span several labeling nights; {len(set(nights.values()))} "
                     f"nights replayed; most labels shown at the start of a night: "
                     f"{max(firsts, default=0)}; most in any call: {replay.most_shown} "
                     f"(cap {group_news.SEED_MAX}))")
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
    for ids, known in calls:
        if any(k.endswith(enc) for k in known):
            exposed |= nots & set(ids)
    lines.append(f"(encyclical card: {len(m['core_on'])} of {m['core_total']} encyclical rows; "
                 f"clearly-other rows on it: {len(m['not_on'])}, of the 6 CI-pinned June "
                 f"mistakes: {len(m['not_on'] & pinned)}; clearly-other rows SHOWN an encyclical "
                 f"label at labeling time: {len(exposed)} of {len(nots)} — the live AI's fusion "
                 f"exposure, measured on PA by relabel_check.py)")
    results.append(("fusion: shown labels put no other story on the encyclical card", ok, lines))


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
    results.append(("AI call: one model setting, Sonnet-safe request, reply read by type",
                    not misses, misses))


def main():
    sys.stdout.reconfigure(errors="replace")     # headlines on a Windows console (cp1252)
    folder = sys.argv[1] if len(sys.argv) > 1 else fx.HERE
    frozen, expected = fx.load(folder)
    results = []
    check_detectors_fire(results, frozen, expected)
    check_seed_rules(results)
    check_ai_call(results)
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
