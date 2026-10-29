#!/usr/bin/env python3
"""relabel_check.py — BY-HAND check of the AI event labeler (layer 1) on the frozen samples.
Run it BEFORE any clustering change (group_news.py prompt/logic), and again after.

It re-labels the frozen headlines with the REAL labeler (group_news.label_batch + its SYSTEM
prompt — imported, not copied), the same way the nightly run does (score order, batches of 40,
running list of labels), then reports:
  - CARDS vs the hand-judged answer (expected.json) — the real pass/fail. The new labels go
    through the real card grouping (views_news._group), so this is what a reader would see.
  - LABEL DRIFT vs the labels stored at freeze time — rows that changed group, and how many
    labels only changed wording. Report only.
It NEVER writes: not news.db, not frozen.json, not expected.json. Stored labels are never
updated from a run — if the new picture is right and the old one wrong, that's a by-hand,
reviewed edit to expected.json.

Cases:
  merge_encyclical, split_sunday   one pass over the case's rows, like a --regroup
  cross_night                      run twice: ONE night (control — all rows in one pass) and
                                   REAL nights (each first-pull night its own pass, each
                                   starting from an EMPTY label list, exactly as group_news.py
                                   does today). Expected today: the two-night run FAILS.

Costs Haiku calls (needs ANTHROPIC_API_KEY; see group_news.py). Without --run it only prints
how many calls it WOULD make.
  ~/.virtualenvs/bible-env/bin/python tests/fixtures/news_clustering/relabel_check.py
  ... relabel_check.py --run                    # all cases
  ... relabel_check.py --run --case split_sunday
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import fixture_lib as fx  # noqa: E402
import views_news  # noqa: E402
from scripts.news import group_news  # noqa: E402

RUN = "--run" in sys.argv
ONLY = sys.argv[sys.argv.index("--case") + 1] if "--case" in sys.argv else None
FOLDER = sys.argv[sys.argv.index("--fixtures") + 1] if "--fixtures" in sys.argv else HERE


def _order(rows):
    """group_news.main's order: score DESC, published DESC."""
    return sorted(rows, key=lambda r: ((r["score"] or 0), (r["published"] or "")), reverse=True)


def _calls(n):
    return (n + group_news.BATCH - 1) // group_news.BATCH


def relabel(client, rows):
    """One labeler pass over rows, from an EMPTY label list (= one nightly run). Returns
    {id: label}. A row the AI skipped stays unlabeled, as it would on PA."""
    known, known_set, out = [], set(), {}
    rows = _order(rows)
    for i in range(0, len(rows), group_news.BATCH):
        batch = rows[i:i + group_news.BATCH]
        labels = group_news.label_batch(client, batch, known)
        for r in batch:
            ev = labels.get(r["id"])
            if not ev:
                continue
            if ev not in known_set:
                known_set.add(ev)
                known.append(ev)
            out[r["id"]] = ev
    return out


def report(name, rows, new_labels, cards):
    """Print the cards verdict + label drift. Returns True when the cards match expected."""
    title = {r["id"]: r["title"] or "" for r in rows}
    relabeled = [dict(r, event=new_labels.get(r["id"], "")) for r in rows]
    produced = [{a["id"] for a in c["arts"]} for c in views_news._group(relabeled, True)]
    ok, lines = fx.compare(produced, cards, title.get)
    print(f"\n== {name}: {'CARDS MATCH expected' if ok else 'CARDS DIFFER from expected'} "
          f"({len(produced)} cards made, {len(cards)} expected)")
    for x in lines:
        print(f"   {x}")

    stored = fx.partition_by_label(rows)
    fresh = fx.partition_by_label(relabeled)
    same_groups = {frozenset(v) for v in stored.values()} & {frozenset(v) for v in fresh.values()}
    print(f"   label drift vs stored: {len(stored)} stored labels -> {len(fresh)} new labels; "
          f"{len(same_groups)} groups unchanged")
    stored_owner = {i: k for k, v in stored.items() for i in v}
    for k, v in sorted(fresh.items(), key=lambda kv: -len(kv[1])):
        olds = sorted({stored_owner[i] for i in v})
        if frozenset(v) in same_groups:
            if olds != [k]:
                print(f"   wording only: {olds[0]!r} -> {k!r} ({len(v)} rows)")
            continue
        print(f"   regrouped: new {k!r} ({len(v)} rows) <- from stored "
              + ", ".join(f"{o!r} ({len(v & stored[o])})" for o in olds))
    unl = [r["id"] for r in rows if not new_labels.get(r["id"])]
    if unl:
        print(f"   {len(unl)} rows got NO label this run: {unl[:20]}")
    return ok


def main():
    sys.stdout.reconfigure(errors="replace")     # headlines on a Windows console (cp1252)
    frozen, expected = fx.load(FOLDER)
    cases = [c for c in fx.CASES if not ONLY or c == ONLY]
    if not cases:
        sys.exit(f"--case must be one of {fx.CASES}")

    plan = []
    for case in cases:
        rows = fx.case_rows(frozen, case)
        if case == "cross_night":
            per_night = {}
            for r in rows:
                per_night.setdefault((r["first_seen"] or "")[:10], []).append(r)
            plan.append((case, _calls(len(rows)) + sum(_calls(len(v))
                                                       for v in per_night.values())))
        else:
            plan.append((case, _calls(len(rows))))
        problems = fx.check_expected_complete(rows, fx.expected_cards(expected, case))
        if problems:
            sys.exit(f"{case}: expected.json is incomplete — fix it first:\n  "
                     + "\n  ".join(problems))
    total = sum(n for _, n in plan)
    print(f"labeler: {group_news.MODEL}, batches of {group_news.BATCH}")
    for case, n in plan:
        print(f"  {case:17s} {n} AI calls")
    print(f"  total             {total} AI calls")
    if not RUN:
        print("\n(no calls made — add --run to do it)")
        return

    client = group_news.build_client()
    verdict = {}
    for case in cases:
        rows = fx.case_rows(frozen, case)
        cards = fx.expected_cards(expected, case)
        if case != "cross_night":
            verdict[case] = report(case, rows, relabel(client, rows), cards)
            continue
        verdict["cross_night: one night (control)"] = report(
            "cross_night: ONE night (control)", rows, relabel(client, rows), cards)
        per_night = {}
        for r in rows:
            per_night.setdefault((r["first_seen"] or "")[:10], []).append(r)
        labels = {}
        for night in sorted(per_night):                 # each night starts from an empty list
            labels.update(relabel(client, per_night[night]))
        verdict["cross_night: real nights"] = report(
            f"cross_night: REAL nights {sorted(per_night)} (known failure expected today)",
            rows, labels, cards)

    print("\nSUMMARY")
    for k, ok in verdict.items():
        note = ""
        if k == "cross_night: real nights":
            note = ("  <- known failure reproduced" if not ok
                    else "  <- now PASSES: the cross-night split did not happen this run")
        print(f"  {'MATCH ' if ok else 'DIFFER'}  {k}{note}")


if __name__ == "__main__":
    main()
