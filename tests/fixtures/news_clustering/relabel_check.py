#!/usr/bin/env python3
"""relabel_check.py — BY-HAND check of the AI event labeler (layer 1) on the frozen samples.
Run it BEFORE any clustering change (group_news.py prompt or logic), and again after: the CI
test (tests/test_news_clustering.py) can't see the labeler, its labels are frozen.

It re-labels the frozen headlines with the REAL labeler — group_news.label_batch + its SYSTEM
prompt, imported, not copied — then builds cards with the real card code (views_news._group) and
reads them against the hand judgment in expected.json, with the same checks the CI test uses:
  merge_encyclical  the encyclical card: how many encyclical rows are on it, how many sit
                    elsewhere, and which clearly-other stories joined it (borderline rows ignored)
  split_sunday      cards fusing two different happenings; happenings scattered over cards
  cross_night       stories scattered over cards / fused together
Two runs per case:
  ONE PASS     every row in one run, from an empty label list (= a --regroup)
  REAL NIGHTS  the real nightly code: group_news.main() run night by night on a scratch db (rows
               labeled in the June-29 regroup = one night), so it measures whatever main()
               does: the bounded past-label list (pick_known) + reuse check while
               group_news.NIGHTLY_SEED is on (shipped 2026-10-31), an EMPTY list each night when
               off (~/news_seed_off present). The live run of 2026-10-29 with it ON on
               Haiku failed on fusion (TODO.md); so did attempt 1b, the same list on Sonnet
               (2026-10-30).
Both runs use the labeler model group_news.MODEL (printed at the top of the output); with
--list-on the reuse check runs on group_news.CHECK_MODEL.
FUSIONS are shown in two columns (ruled JP 2026-10-30): THROUGH REUSE — a row put on an earlier
night's label about a different story (fixture_lib.reuse_joiners), the cross-night fix's own
decision, scored; SAME-NIGHT — different stories given one label inside one labeler run, the
labeler's own, reported only. A STORED row (the nightly's own labels, no calls) is the baseline.
Plus LABEL DRIFT vs the labels stored at freeze time: how many different labels each judged
story got, then vs now.

It NEVER writes: not news.db, not frozen.json, not expected.json. If a new picture is better
than the stored one, that's a reviewed, by-hand edit to expected.json — never automatic.

Costs labeler calls on group_news.MODEL (needs ANTHROPIC_API_KEY — see group_news.py's OPS note). Without --run it only
prints how many calls it WOULD make.
  ~/.virtualenvs/bible-env/bin/python tests/fixtures/news_clustering/relabel_check.py
  ... relabel_check.py --run                          # all cases, both runs
  ... relabel_check.py --run --case split_sunday      # one case
  ... relabel_check.py --run --one-pass               # skip the (bigger) real-nights runs
  ... relabel_check.py --run --list-on                # real nights WITH the past-label list +
                                                      # reuse check (scratch db only; the nightly
                                                      # itself is untouched)
  ... relabel_check.py --run --list-on --nights-only  # same, without the one-pass runs (for
                                                      # repeat runs measuring run-to-run variance)
"""
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import fixture_lib as fx  # noqa: E402
from scripts.news import group_news  # noqa: E402

RUN = "--run" in sys.argv
ONE_PASS_ONLY = "--one-pass" in sys.argv
# --list-on: REAL NIGHTS runs with the past-label list + reuse check switched on (NIGHTLY_SEED)
# in its scratch db only — the shipped nightly stays as it is. How a design is checked live
# without the 06:00 UTC nightly ever running it (attempt 4, 2026-10-30).
LIST_ON = "--list-on" in sys.argv
# --nights-only: skip the ONE PASS runs (the --regroup path — no past labels, no reuse check, so it
# says nothing about the check; ~30 calls saved per run). For repeat runs that measure how much
# the reuse check varies run to run (attempt 7, 2026-10-31). The free STORED row stays.
NIGHTS_ONLY = "--nights-only" in sys.argv
ONLY = sys.argv[sys.argv.index("--case") + 1] if "--case" in sys.argv else None
# rows the reuse check's prompt uses as worked examples (group_news.CONFIRM_EXAMPLES, attempt 6):
# a fusion involving one is flagged — those rows overlap the scored samples (TODO.md)
EXAMPLE_IDS = {i for e in group_news.CONFIRM_EXAMPLES for i in (e[0], e[3])}
FOLDER = sys.argv[sys.argv.index("--fixtures") + 1] if "--fixtures" in sys.argv else HERE


def _order(rows):
    """group_news.main's order: score DESC, published DESC."""
    return sorted(rows, key=lambda r: ((r["score"] or 0), (r["published"] or "")), reverse=True)


def _calls(n):
    return (n + group_news.BATCH - 1) // group_news.BATCH


def _nights(rows):
    out = {}
    for r in rows:
        out.setdefault(fx.labeling_night(r), []).append(r)
    return out


def relabel(client, rows):
    """One labeler run over rows from an EMPTY label list, exactly as group_news.main does it.
    Returns {id: label}; a row the AI skipped stays unlabeled, as it would on PA."""
    known, known_set, out = [], set(), {}
    rows = _order(rows)
    for i in range(0, len(rows), group_news.BATCH):
        batch = rows[i:i + group_news.BATCH]
        try:                         # same as main(): a failed batch is reported, not fatal
            labels = group_news.label_batch(client, batch, known)
        except Exception as e:
            print(f"  ERR  one-pass batch at {i}: {str(e)[:80]}")
            continue
        for r in batch:
            ev = labels.get(r["id"])
            if not ev:
                continue
            if ev not in known_set:
                known_set.add(ev)
                known.append(ev)
            out[r["id"]] = ev
    return out


def nightly(rows):
    """REAL NIGHTS = the real nightly code: group_news.main() run night by night on a scratch db
    (never news.db), so whatever main() shows the labeler — today the bounded past-label list,
    group_news.pick_known — is exactly what gets measured. Returns ({id: label}, notes)."""
    import io
    import sqlite3
    import tempfile
    from contextlib import redirect_stdout
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    keep = {k: getattr(group_news, k) for k in ("DB_PATH", "REGROUP", "DRY_RUN", "MIN",
                                                "NIGHTLY_SEED")}
    notes = []
    night_of = {}                        # {id: the night it was LABELED} (a skipped row retries)
    try:
        c = sqlite3.connect(path)
        c.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, title TEXT, source TEXT, "
                  "published TEXT, first_seen TEXT, score INTEGER, event TEXT)")
        c.commit()
        group_news.DB_PATH, group_news.REGROUP, group_news.DRY_RUN = path, False, False
        group_news.MIN = 5
        if LIST_ON:
            group_news.NIGHTLY_SEED = True
        for night, nrows in sorted(_nights(rows).items()):
            c.executemany("INSERT INTO items (id, title, source, published, first_seen, score) "
                          "VALUES (?,?,?,?,?,?)",
                          [(r["id"], r["title"], r["source"], r["published"], r["first_seen"],
                            r["score"]) for r in nrows])
            c.commit()
            buf = io.StringIO()
            with redirect_stdout(buf):
                group_news.main()
            for line in buf.getvalue().splitlines():
                if ("ERR" in line or "past labels shown" in line or line.startswith("calls:")
                        or "left unlabeled" in line):
                    notes.append(f"{night}: {line.strip()}")
            for (i,) in c.execute("SELECT id FROM items WHERE event IS NOT NULL AND event != ''"):
                night_of.setdefault(i, night)
        labels = {r[0]: r[1] for r in c.execute("SELECT id, event FROM items") if r[1]}
        c.close()
    finally:
        for k, v in keep.items():
            setattr(group_news, k, v)
        os.remove(path)
    return labels, notes, night_of


def report(case, title, rows, new_labels, expected, night_of):
    """Print the picture for one run. Returns a one-line verdict for the summary.
    Fusions are counted in TWO columns (ruled JP 2026-10-30): THROUGH REUSE = a row put on a
    label from an EARLIER night, about a different story (fx.reuse_joiners) — the cross-night
    fix's own decision, scored; SAME NIGHT = different stories given one label inside a single
    labeler run — the labeler's own, reported, not scored against the fix. night_of = {id: the
    night it was labeled}; a one-pass run is all one night, so everything there is same-night."""
    story_of, judged, _ = fx.judgment(expected, case, rows)
    relabeled = [dict(r, event=new_labels.get(r["id"], "")) for r in rows]
    cards = fx.cards_of(relabeled)
    print(f"\n== {case} — {title}: {len(cards)} cards")
    if case == "merge_encyclical":
        asserted = {s for s in story_of.values() if not s.startswith("border:")}
        joiners = fx.reuse_joiners(relabeled, night_of, story_of, asserted)
        m = fx.merge_picture(relabeled, cards, expected)
        via, same = m["not_on"] & joiners, m["not_on"] - joiners
        print(f"   encyclical card: {len(m['target'])} rows, labels {m['target_labels'][:4]}")
        print(f"   encyclical rows on it: {len(m['core_on'])} of {m['core_total']}; "
              f"elsewhere: {len(m['core_off'])}; clearly-other stories on it: {len(m['not_on'])} "
              f"= {len(via)} through reuse + {len(same)} same-night")
        if via:
            print("   joined THROUGH a reused earlier-night label (scored) — every one listed:")
            print("\n".join(fx.describe(via, relabeled, len(via))))
        if same:
            print("   joined on the label's own night (labeler, not scored):")
            print("\n".join(fx.describe(same, relabeled, 15)))
        ex = via & EXAMPLE_IDS
        if ex:
            print(f"   (of the through-reuse rows, these are in the check's own prompt examples: "
                  f"{sorted(ex)})")
        verdict = (f"{len(m['core_on'])}/{m['core_total']} encyclical rows on one card; other "
                   f"stories on it: {len(via):3d} through reuse | {len(same):3d} same-night"
                   + (f"\n{'':30s}through-reuse ids {sorted(via)}" if via else "")
                   + (f"  [{len(ex)} of the through-reuse are prompt-example rows]" if ex else ""))
    else:
        multi = {s for s in judged if sum(1 for i in story_of if story_of[i] == s) > 1}
        om = fx.overmerged(cards, story_of, judged)
        joiners = fx.reuse_joiners(relabeled, night_of, story_of, judged)
        via, same = fx.split_fusions(om, joiners)
        sc = fx.scattered(cards, fx.expected_pieces(rows, story_of), multi)
        for kind, ps in (("THROUGH REUSE (scored)", via), ("SAME NIGHT (labeler, not scored)", same)):
            for p in ps:
                j = sorted(p & joiners)
                ex = sorted(p & EXAMPLE_IDS)
                print(f"   OVER-MERGE, {kind} — one card, different happenings"
                      + (f"; joined via an earlier-night label: ids {j}" if j else "")
                      + (f"; prompt-example rows on it: {ex}" if ex else "") + ":")
                print("\n".join(fx.describe(p, relabeled, 10)))
        via_ex = sum(1 for p in via if p & EXAMPLE_IDS)
        for s, piece, sizes in sc:
            print(f"   SPLIT: {s!r} ({len(piece)} rows) over {len(sizes)} cards, sizes {sizes[:10]}")
        edge = [p for p in via if fx.edge_only(p, story_of, judged)]
        joined = sorted(i for p in via for i in p & joiners)
        verdict = (f"over-merged cards: {len(via):3d} through reuse | {len(same):3d} same-night; "
                   f"{len(sc)} split happenings"
                   + (f"\n{'':30s}through-reuse joiner ids {joined}; of the cards: "
                      f"{len(edge)} are judgment edges only -> {len(via) - len(edge)} without "
                      f"the edges" if via else "")
                   + (f"  [{via_ex} of the through-reuse cards hold prompt-example rows]"
                      if via_ex else ""))

    # label drift: different labels per judged multi-row story, stored vs new
    drift = []
    present = {r["id"] for r in rows}
    for s in sorted({story_of[r["id"]] for r in rows}):
        ids = [i for i in present if story_of[i] == s]
        if s not in judged or len(ids) < 2:
            continue
        old = Counter(r["event"] for r in rows if r["id"] in ids)
        new = Counter(new_labels.get(i, "(none)") for i in ids)
        if len(old) != len(new) or len(new) > 1:
            drift.append(f"   {s[:60]!r}: stored {len(old)} labels -> now {len(new)} "
                         f"(top now: {new.most_common(1)[0][0]!r})")
    if drift:
        print("   label drift (labels per story, stored -> now):")
        print("\n".join(drift[:20]))
    unl = [r["id"] for r in rows if not new_labels.get(r["id"])]
    if unl:
        print(f"   {len(unl)} rows got NO label this run: {unl[:20]}")
    return verdict


def main():
    sys.stdout.reconfigure(errors="replace")     # headlines on a Windows console (cp1252)
    frozen, expected = fx.load(FOLDER)
    cases = [c for c in fx.CASES if not ONLY or c == ONLY]
    if not cases:
        sys.exit(f"--case must be one of {fx.CASES}")

    total = 0
    print(f"labeler: {group_news.MODEL}, batches of {group_news.BATCH}; real nights: past-label "
          f"list + reuse check {'ON (--list-on)' if LIST_ON or group_news.NIGHTLY_SEED else 'OFF'}"
          + (f"; reuse check on {group_news.CHECK_MODEL} — its calls + the fresh-label calls "
             f"come on top (the frozen-sample replay: ~0.6x the real-nights labeler calls; "
             f"counted live below)" if LIST_ON else ""))
    for case in cases:
        rows = fx.case_rows(frozen, case)
        _, _, problems = fx.judgment(expected, case, rows)
        if problems:
            sys.exit(f"{case}: expected.json doesn't cover the frozen rows — fix it first:\n  "
                     + "\n  ".join(problems))
        one = 0 if NIGHTS_ONLY else _calls(len(rows))
        nights = 0 if ONE_PASS_ONLY else sum(_calls(len(v)) for v in _nights(rows).values())
        total += one + nights
        print(f"  {case:17s} one pass {one:3d} calls"
              + ("" if ONE_PASS_ONLY else f", real nights {nights:3d} calls "
                                          f"({len(_nights(rows))} nights)"))
    print(f"  total             {total} AI calls")
    if not RUN:
        print("\n(no calls made — add --run to do it)")
        return

    import logging
    logging.getLogger("httpx").setLevel(logging.WARNING)   # one INFO line per AI call = noise
    client = group_news.build_client()
    summary = []
    for case in cases:
        rows = fx.case_rows(frozen, case)
        # baseline, no AI calls: the labels the live nightly (switch off) stored at freeze time
        summary.append((case, "stored", report(
            case, "STORED (the live nightly's own labels, switch off — no calls)", rows,
            {r["id"]: r["event"] for r in rows if r["event"]}, expected,
            {r["id"]: fx.labeling_night(r) for r in rows})))
        if not NIGHTS_ONLY:
            summary.append((case, "one pass", report(case, "ONE PASS", rows, relabel(client, rows),
                                                      expected, {r["id"]: "one" for r in rows})))
        if ONE_PASS_ONLY:
            continue
        labels, notes, night_of = nightly(rows)   # the real group_news.main(), night by night
        errs = [n for n in notes if "ERR" in n]
        most = max((int(n.rsplit(" ", 1)[1].rstrip(")")) for n in notes
                    if "past labels shown" in n), default=0)
        print(f"\n   (real nights: most past labels shown in one call {most}"
              + (f"; {len(errs)} failed batches: {errs[:3]}" if errs else "") + ")")
        tot = [0, 0, 0, 0]
        for n in notes:
            m = re.search(r"labeler (\d+), reuse checks (\d+) \((\d+) reuses turned down\), "
                          r"fresh-label calls (\d+)", n)
            if m:
                tot = [a + int(b) for a, b in zip(tot, m.groups())]
        unl = sum(1 for n in notes if "left unlabeled" in n)
        if LIST_ON:
            print(f"   (real nights calls: labeler {tot[0]}, reuse checks {tot[1]}, reuses turned "
                  f"down {tot[2]}, fresh-label {tot[3]}; left unlabeled {unl})")
        summary.append((case, "real nights", report(case, "REAL NIGHTS (current nightly code)",
                                                     rows, labels, expected, night_of)))
    print("\nSUMMARY  (fusions: THROUGH REUSE = via an earlier night's label, scored | SAME-NIGHT "
          "= inside one labeler run, reported only)")
    for case, mode, verdict in summary:
        print(f"  {case:17s} {mode:11s} {verdict}")
    print("\nBAR for the list + reuse check (TODO.md), on the REAL NIGHTS rows: through-reuse "
          "fusions 0 on every case (stored labels: 0); encyclical rows on its card above 341/623; "
          "Sunday split happenings below 13; cross_night 0 split. Same-night fusions are "
          "the labeler's, not scored here.")


if __name__ == "__main__":
    main()
