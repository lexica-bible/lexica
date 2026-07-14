#!/usr/bin/env python3
"""Offline archived-card gate check -- reviewer-approved replacement for the live parked-word
re-run (2026-07-14, ruling b). READ-ONLY end to end: an archived card JSON goes in, bible.db
is opened read-only for verse text, and there is NO write, NO model call, and NO redraw.

Why it exists: a parked word's required --hints rides the model context, so it is part of the
draw input key -- re-running the word moves the key and forces a fresh redraw, and a redraw is
a DIFFERENT card than the one a byte-pinned prediction was computed from. So a live re-run can
never test "does this card match the prediction" (ENGINE_LESSONS, 2026-07-14). This helper
feeds the ON-RECORD archived card bytes straight through the production gate instead -- fully
deterministic, repeatable, zero spend.

Reuses the PRODUCTION detectors from build_lexica_def (never a copy): probe1_verbatim (the
authoritative verdict + fail-kind routing), probe_norm / _quote_spans / _match_quote (the span
walk), and _target_exists_score (the combined near-match score). The score walk only SURFACES
the gate's own number for the fragility-band watch -- it is a measurement, not a second verdict.

Usage (run on PA by JP):
  python scripts/offline_gate_check.py \
      --card draws/history/G227_20260714T035653_8258771a.json \
      --expect "quenched/crushed"

Exit 0 = recoverability precondition passed and the report printed.
Exit 2 = recoverability precondition FAILED (the predicted span is not in the archived card):
         that word STOPS (per-word precondition binding, ruling b).
"""
import argparse
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_lexica_def as B  # noqa: E402  (production detectors -- reused, never copied)

# Live fragility watch (reviewer-bound on this helper's output). The known residual squeeze
# (0.621 / 0.706 / 0.750) sits inside this band; the helper FLAGS every in-band span but does
# NOT classify -- known-residual vs NEW is the reading step's call (a NEW in-band span is the
# mandatory re-open).
BAND_LO, BAND_HI = 0.62, 0.75


def load_verse_texts(db_path, refs):
    """Read-only verse-text lookup for every cited ref (the probe-1 convention: own live
    lookups, since a card cites Range/gloss refs no fed sample would cover). Opens bible.db
    with mode=ro so the process cannot write, period."""
    uri = "file:%s?mode=ro" % os.path.abspath(db_path)
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    vt = {}
    try:
        for b, c, v in refs:
            row = conn.execute(
                "SELECT text FROM verses WHERE book=? AND chapter=? AND verse=?",
                (b, c, v)).fetchone()
            vt[(b, c, v)] = (row["text"] if row and row["text"] else None)
    finally:
        conn.close()
    return vt


def score_no_match_spans(raw, normed):
    """Combined near-match score for every quoted span that matches no cited verse -- the same
    _target_exists_score the gate's own no-match branch uses. Mirrors the gate's span guard
    (alphabetic content; skip spans that DO match a cited verse) so the reported set lines up
    with what the gate actually scored. Verdict-neutral."""
    out = []
    for span, qs, qe in B._quote_spans(raw):
        qn = B.probe_norm(B._EMPH_MARK_RE.sub("", span))
        if not re.search(r"[A-Za-z]", qn):
            continue
        if any(B._match_quote(qn, vn) for vn in normed.values()):
            continue  # matches a cited verse -> never reaches the near-match branch
        out.append((qn, B._target_exists_score(qn, normed)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", required=True,
                    help="archived draw JSON -- the card of record for this word")
    ap.add_argument("--expect", required=True,
                    help="predicted span that MUST be present in the card (recoverability "
                         "precondition); the word STOPS if absent")
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"),
                    help="bible.db path (opened read-only)")
    args = ap.parse_args()

    with open(args.card, encoding="utf-8") as f:
        card = json.load(f)
    raw = card.get("raw", "")
    sid = card.get("strongs", "?")
    sig = (card.get("sig") or "")[:8]
    print("=== offline gate check: %s  (card sig %s, %s) ==="
          % (sid, sig, os.path.basename(args.card)))
    print("raw chars: %d | created: %s" % (len(raw), card.get("created", "")))

    # Per-word precondition (ruling b): the predicted span must be recoverable in THIS card.
    if args.expect not in raw:
        print('RECOVERABILITY: predicted span "%s" NOT in card -> FAIL. Word STOPS '
              "(this is not the prediction card)." % args.expect)
        sys.exit(2)
    print('RECOVERABILITY: predicted span "%s" present -> PASS' % args.expect)

    refs = B.cited_refs(raw)
    vt = load_verse_texts(args.db, refs)
    missing = [r for r, t in vt.items() if t is None]
    normed = {k: B.probe_norm(v) for k, v in vt.items() if v}
    print("cited refs: %d | verse text available: %d | unavailable: %d"
          % (len(refs), len(normed), len(missing)))
    if missing:
        print("  unavailable refs (a no-match span here reports NOT-RUN, never exempt): "
              + ", ".join("%s %d:%d" % (b, c, v) for b, c, v in missing))

    notes, fail_kinds = [], []
    fails, notruns = B.probe1_verbatim(raw, vt, notes=notes, fail_kinds=fail_kinds)

    print("\n--- verbatim-quote gate verdict (production probe1_verbatim) ---")
    if notes:
        print("EXEMPT / non-blocking notes:")
        for n in notes:
            print("  - " + n)
    if fails:
        print("FAILS (kind in brackets; wording = fed to model, anchoring/unsourced = held):")
        for msg, kind in zip(fails, fail_kinds):
            print("  [%s] %s" % (kind, msg))
    if notruns:
        print("NOT RUN (blocks apply):")
        for nr in notruns:
            print("  - " + nr)
    if not (notes or fails or notruns):
        print("  gate clean -- no quoted span flagged.")

    print("\n--- combined near-match score, every no-match span "
          "(fragility band %.2f-%.2f) ---" % (BAND_LO, BAND_HI))
    band_hits = []
    for qn, score in score_no_match_spans(raw, normed):
        rel = ">= t" if score >= B.NEARMATCH_THRESHOLD else "<  t"
        in_band = BAND_LO <= score <= BAND_HI
        flag = "   <-- IN BAND" if in_band else ""
        if in_band:
            band_hits.append((qn, score))
        label = qn if len(qn) <= 55 else qn[:52] + "..."
        print('  %.3f  %s  "%s"%s' % (score, rel, label, flag))
    print("  threshold t = %.3f" % B.NEARMATCH_THRESHOLD)
    # THRESHOLD POSITION ONLY -- this table is NOT a fate. A span's ACTUAL verdict is in the
    # gate section above: an upstream rule (metalinguistic cue / own-word) can exempt a span
    # BEFORE the near-match test runs, so a score here does not by itself mean fed-as-wording
    # or own-paraphrase. Only a span that survives the upstream exemptions is decided by t.
    # The band watch still lists every in-band score -- a cue-exempted span sitting in-band is
    # exactly the "is the exemption masking a near-quote?" case worth a human look.
    print("  (threshold position only; cross-read each span against the gate verdict above --\n"
          "   an upstream exemption can decide a span regardless of its score here.)")

    print("\n--- summary ---")
    print("fails: %d | exempt/notes: %d | not-run: %d | in-band spans: %d"
          % (len(fails), len(notes), len(notruns), len(band_hits)))
    if band_hits:
        print("IN-BAND spans present -> classify each: known residual (already ruled) vs NEW. "
              "Any NEW in-band span = mandatory re-open, STOP the card, report before it "
              "proceeds.")
    print("(scores are EVIDENCE, not calibration: no threshold or band moves off this output; "
          "t <= 0.706 ceiling and fixture-21 non-calibration status stand.)")


if __name__ == "__main__":
    main()
