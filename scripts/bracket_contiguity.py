"""bracket_contiguity.py — THE bracket-contiguity classifier (one copy).

Lifted verbatim from fix_lane3_star_merges.py's dry-run check (2026-08-07 lane
③) so the wordpos-lane controls and the repair tool share ONE classifier (the
counter-and-fix-share-the-classifier rule). Logic unchanged: chip/interlinear
(groupForGreekMode) walk CONSECUTIVE same-bracket runs, so every slot inside a
bracket's position span must carry that bracket's mark — an interior slot with
a different (or no) mark is a GAP that splits the run and mis-orders chip and
interlinear modes while prose stays correct.

rows: iterable of mappings with "position" and "bracket_id" (sqlite3.Row ok).
Returns [(bracket_id, position), ...] — empty list = contiguous = PASS.
"""


def bracket_gaps(rows):
    spans = {}
    for r in rows:
        if r["bracket_id"] is not None:
            lo, hi = spans.get(r["bracket_id"], (r["position"], r["position"]))
            spans[r["bracket_id"]] = (min(lo, r["position"]), max(hi, r["position"]))
    return [(b, r["position"]) for b, (lo, hi) in spans.items()
            for r in rows if lo < r["position"] < hi and r["bracket_id"] != b]
