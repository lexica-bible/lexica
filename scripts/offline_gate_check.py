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

# Live fragility watch. Reuse the gate's OWN band edges (single source of truth) so the helper
# and the meta:v5 in-band demote can never drift apart. The helper FLAGS every in-band span but
# does NOT classify -- known-residual vs NEW is the reading step's call.
BAND_LO, BAND_HI = B.NEARMATCH_BAND_LO, B.NEARMATCH_BAND_HI


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


def write_path_checks(db_path, card, raw, vt):
    """Run the WRITE PATH's checks against this card, and NAME every one that can't run here
    (ENGINE_LESSONS #69(i); scope ruled (b), 2026-07-14). Before this, the harness ran ONE
    production detector (probe1_verbatim) out of the eleven the write path runs — so a readiness
    pass could certify a card on 1-of-11 and read as COVERED. That is how the Eph 4:8
    rendering-claim fire reached a live row (#69(a)): the lint only ever fired in assemble.

    Everything here is READ-ONLY and reuses the PRODUCTION detectors (never a copy), same rule as
    the rest of this file. Report, not gate: this tool's exit contract is unchanged (0 = report
    printed, 2 = recoverability precondition failed). The apply path remains the thing that
    blocks; the harness's job is that a human never certifies past a check nobody ran."""
    uri = "file:%s?mode=ro" % os.path.abspath(db_path)
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    conn.create_function("strip_accents", 1, B.strip_accents)
    sid = card.get("strongs", "?")
    fields = B.split_definition(raw)
    refs = B.cited_refs(raw)
    fired = 0

    def report(label, items, fmt=str):
        nonlocal fired
        if items:
            fired += len(items)
            print("  [RAN]  %-18s %d fire(s):" % (label, len(items)))
            for it in items:
                print("      - " + fmt(it))
        else:
            print("  [RAN]  %-18s clean" % label)

    print("\n--- write-path checks (assemble's audit block + validate_entry probes) ---")

    cg = B.run_citation_gate(conn, sid, refs)
    bad = [m for m in cg["misses"] if m["bucket"] in ("real", "noverse")]
    print("  [RAN]  %-18s %d/%d pass | tagging %d | real %d | no-verse %d%s"
          % ("citation gate", cg["pass"], cg["total"], cg["tagging"], cg["real"], cg["noverse"],
             ("  <-- BLOCKS at apply" if bad else "")))
    fired += len(bad)

    report("dangling", B.dangling_book_refs(conn, raw))
    report("noncanon", B.noncanon_book_refs(conn, raw))
    report("double_shelved", B.double_shelved(fields["senses_block"]))
    # THE Eph 4:8 CLASS — the rendering-claim lint. Fires when a gloss-note's italic label is not
    # the lemma's ACTUAL rendering at the ref it cites.
    report("gloss_claims", B.gloss_note_claims(conn, sid, fields.get("gloss_notes", "")),
           fmt=lambda c: "[%s] gloss *%s* vs corpus rendering %r at %s"
                         % (c.get("kind"), c.get("gloss"), c.get("rend"), c.get("ref")))
    report("hedged", B.hedged_citations(fields["senses_block"]))
    report("subuse_overload", B.subuse_overload(fields["senses_block"]))
    report("registry_verses", B.registry_verse_hits(refs))

    # probe1 already ran above (the gate verdict section) — named here so the enumeration is
    # complete and a reader can see it was not skipped.
    print("  [RAN]  %-18s see the verbatim-quote gate verdict section above" % "probe1")
    p2w, p2nr = B.probe2_names(raw, vt,
                               extra_whitelist=(card.get("lemma"), card.get("translit")),
                               known_names=B._p2_corpus_names(conn))
    # A dead name-guard is a NOT-RUN and must surface HERE too (DESIGN_p2_guard_loudness.md,
    # reviewer-ruled in scope): without it this report would list probe2's findings as if
    # demotion had run, claiming coverage it does not have — the exact defect this fixes.
    # Silence reads as covered, #69(i) — the same rule this file's output contract below states.
    guard_nr = B._p2_guard_notrun(conn)
    report("probe2", ([guard_nr] if guard_nr else []) + p2w + p2nr)
    report("scan3", B.scan3_identity(raw, vt))
    conn.close()

    # A SEPARATE HEADING ON PURPOSE (reviewer-ruled 2026-07-14). This detector is NOT a write-path
    # check, so listing it above would claim the build gates on it — false. Omitting it would leave
    # the report SILENT on the class, and silence reads as covered (#69(i)). Both are falsifications
    # of the output contract, in opposite directions; its own honest heading is the only shape that
    # is true both ways. Its fires deliberately do NOT enter `fired` — that count is reported as
    # "write-path check fires", which these are not.
    print("\n--- report-only detectors (NOT run by the write path · gate nothing) ---")
    bp = B.leading_boilerplate(raw)
    if bp:
        print("  [RAN]  %-18s %d fire(s):" % ("boilerplate", len(bp)))
        for h in bp:
            print("      - [%s] %r" % (h["kind"], h["text"][:100]))
    else:
        print("  [RAN]  %-18s clean" % "boilerplate")
    # REMOVE THIS CLAUSE in the SAME commit that lands the green known-positive fixture — not
    # before, not after (reviewer condition). Until then this report must not read as certifying
    # boilerplate coverage.
    print("  ⚠ boilerplate ZEROS ARE NOT TRUSTED YET: the known-positive control (G162's archived "
          "draw, PA-only) has NOT run. Boundary logic is proven; a 'clean' above is UNPROVEN.")

    # OUTPUT CONTRACT, not comments (reviewer condition, 2026-07-14): a reader of this REPORT must
    # see what the report does not cover. Silence reads as covered — #69(i).
    print("\n--- checks that CANNOT run offline (named, never silent) ---")
    print("  [SKIPPED] coverage gate     : needs the FED SAMPLE. fed_uncited is stamped at the "
          "call site (the one place the fed list exists); an archived-card pass has no fed list. "
          "Runs at apply.")
    print("  [SKIPPED] floor-match       : needs the floor draws file (load_floor). Runs at "
          "apply/build.")
    print("  [SKIPPED] #30 membership    : needs the path-(c) roster. Runs at apply/build.")
    print("  [SKIPPED] #55 sense-count   : needs the roster/floor sense counts. Runs at "
          "apply/build.")
    print("  (These four are NOT covered by this report. A card is not ship-ready on this "
          "output alone.)")
    return fired


def sweep(db_path):
    """meta:v5 BLAST-RADIUS SWEEP (scope-b ruling, 2026-07-14): run the gate over EVERY live
    card's stored raw and report every in-band cue-exemption WARN (span + score). Live cards =
    lexica_def rows; a card's raw is def_json['raw'] (the same field a rebuild re-reads). Verse
    text comes from the SAME read-only connection. No write, no model, no redraw. Output is
    EVIDENCE (non-calibration): each warn is a live card that would BLOCK on rebuild/apply under
    meta:v5 until its span is adjudicated. Registry earns entries one adjudication at a time."""
    uri = "file:%s?mode=ro" % os.path.abspath(db_path)
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row

    def verse(b, c, v):
        r = conn.execute("SELECT text FROM verses WHERE book=? AND chapter=? AND verse=?",
                         (b, c, v)).fetchone()
        return r["text"] if r and r["text"] else None

    rows = conn.execute("SELECT strongs, def_json FROM lexica_def ORDER BY strongs").fetchall()
    print("=== meta:v5 live-card sweep: %d card(s) ===" % len(rows))
    flagged, total = 0, 0
    for row in rows:
        try:
            raw = (json.loads(row["def_json"]) or {}).get("raw", "")
        except Exception as e:
            print("  ! %s: def_json unreadable (%s) -- skipped" % (row["strongs"], e))
            continue
        if not raw:
            continue
        vt = {(b, c, v): verse(b, c, v) for b, c, v in B.cited_refs(raw)}
        warns = []
        B.probe1_verbatim(raw, vt, warns=warns)
        if warns:
            flagged += 1
            total += len(warns)
            print("\n%s -- %d in-band cue warn(s):" % (row["strongs"], len(warns)))
            for w in warns:
                print("  - " + w)
    conn.close()
    print("\n--- sweep summary ---")
    print("cards swept: %d | cards with in-band cue warns: %d | total warns: %d"
          % (len(rows), flagged, total))
    print("(EVIDENCE, non-calibration. Each warn = a live card that would BLOCK on a future "
          "rebuild/apply under meta:v5 until its span is adjudicated. Registry earns entries one "
          "receipted adjudication at a time -- never batch-populated.)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--card",
                    help="archived draw JSON -- the card of record for this word")
    ap.add_argument("--expect",
                    help="predicted span that MUST be present in the card (recoverability "
                         "precondition); the word STOPS if absent")
    ap.add_argument("--sweep", action="store_true",
                    help="blast-radius mode: run the meta:v5 gate over EVERY live card "
                         "(lexica_def) and report in-band cue warns; ignores --card/--expect")
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"),
                    help="bible.db path (opened read-only)")
    args = ap.parse_args()

    if args.sweep:
        sweep(args.db)
        return
    if not args.card or not args.expect:
        sys.exit("single-card mode needs --card and --expect (or pass --sweep for the "
                 "blast-radius run).")

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

    notes, fail_kinds, warns = [], [], []
    fails, notruns = B.probe1_verbatim(raw, vt, notes=notes, fail_kinds=fail_kinds, warns=warns)

    print("\n--- verbatim-quote gate verdict (production probe1_verbatim) ---")
    if notes:
        print("EXEMPT / non-blocking notes:")
        for n in notes:
            print("  - " + n)
    if warns:
        print("WARNS (meta:v5 in-band cue demote -- BLOCKS apply until adjudicated):")
        for w in warns:
            print("  - " + w)
    if fails:
        print("FAILS (kind in brackets; wording = fed to model, anchoring/unsourced = held):")
        for msg, kind in zip(fails, fail_kinds):
            print("  [%s] %s" % (kind, msg))
    if notruns:
        print("NOT RUN (blocks apply):")
        for nr in notruns:
            print("  - " + nr)
    if not (notes or warns or fails or notruns):
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

    lint_fires = write_path_checks(args.db, card, raw, vt)

    print("\n--- summary ---")
    print("fails: %d | warns: %d | exempt/notes: %d | not-run: %d | in-band spans: %d | "
          "write-path check fires: %d"
          % (len(fails), len(warns), len(notes), len(notruns), len(band_hits), lint_fires))
    if band_hits:
        print("IN-BAND spans present -> classify each: known residual (already ruled) vs NEW. "
              "Any NEW in-band span = mandatory re-open, STOP the card, report before it "
              "proceeds.")
    print("(scores are EVIDENCE, not calibration: no threshold or band moves off this output; "
          "t <= 0.706 ceiling and fixture-21 non-calibration status stand.)")


if __name__ == "__main__":
    main()
