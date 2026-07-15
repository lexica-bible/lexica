#!/usr/bin/env python3
"""
fix_lexica_raw.py — surgical correction of a stored Lexica entry's RAW model prose, then
re-assemble the entry from the corrected text (NO model call).

For one-off artifacts in the model's own output — a doubled reference, a malformed citation —
that aren't worth a full re-generation, and that we explicitly do NOT want to re-generate
because regenerating would replace proven, reviewed prose with a fresh (unreviewed) draft.

CERTIFICATION BOUNDARY (what this tool may and may NOT touch — precedent: τόπος + ἔργον, 2026-07-08).
Certification attaches to the entry's CLAIMS and their grounding (the senses carved, the verses cited,
the citation gate passing, review-what-ships). This tool preserves the stamp — a surgical edit is not a
new generation — ONLY while it stays inside that boundary:
  ALLOWED (stamp preserved): prose-level swaps that leave the SENSES and CITED VERSES unchanged —
    de-freighting a word, deleting an unverified claim, fixing a typo/jargon. Every swap STILL runs its
    own dry-run → full proofread → apply gate (that is what keeps review-what-ships intact). The meaning
    should move toward corpus-faithful, never away.
  FORBIDDEN (this UN-certifies — REDRAW instead, do not use this tool): adding / merging / re-carving a
    sense; changing which verses a sense cites; asserting anything about the corpus the machine has not
    verified; any change that skips the dry-run→proofread→apply gate.

It does an EXACT string replacement on the stored raw (the text must occur exactly once, or it
aborts), then runs the canonical assemble() from build_lexica_def — which re-splits the display
fields, rebuilds verses[], and re-runs the citation gate — shows the result, and on --apply
writes the one row back. The engine stamp (synth_ver) is preserved: a surgical edit of the raw
is not a new generation, so the entry's identity is unchanged.

PA-ONLY (bible.db lives on PA). Reads words / verses for the citation gate; WRITES ONLY its own
row in lexica_def. --dry-run is the DEFAULT — pass --apply to write.

  # charis G5484 sense-6: the model wrote "1Ti—" (no verse) for 1 Timothy's grace+peace greeting,
  # which is 1Ti 1:2; it also used a comma where the list uses semicolons.
  python scripts/fix_lexica_raw.py --word G5484 \
      --old "2Th 1:2; 1Ti—, Gal 1:3" --new "2Th 1:2; 1Ti 1:2; Gal 1:3"            # show, no write
  python scripts/fix_lexica_raw.py --word G5484 \
      --old "2Th 1:2; 1Ti—, Gal 1:3" --new "2Th 1:2; 1Ti 1:2; Gal 1:3" --apply    # write
"""
import argparse, datetime, json, os, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_lexica_def as B


# The V11 warn surfaces open_probe_warns() gates on — the set an adjudication rules over.
_WARN_KEYS = ("probe1_warns", "probe2_warns", "scan3_warns", "probe1_notrun", "probe2_notrun")


def canon_warns(audit):
    """CANONICAL form of the warn set, for the identical-set carry test (reviewer ruling
    2026-07-14). Stable ordering + stable serialization — NOT raw string equality of whatever
    the audit block happens to emit: warns are plain strings appended in SCAN ORDER
    (build_lexica_def.py, probe2_names et al), never sorted, so a surgical edit that moves text
    reorders identical warns. Comparing raw would force a spurious refusal on a benign reorder —
    which is exactly what invites a 'just carry it' workaround later."""
    a = audit or {}
    return json.dumps({k: sorted(a.get(k) or []) for k in _WARN_KEYS},
                      ensure_ascii=False, sort_keys=True)


def fix_draw(sid, args):
    """DRAW-FILE MODE (reviewer-ruled 2026-07-15, G5088 second quote-repair cap-out): the same
    surgical edit, applied to the CACHED DRAW of a word that has never passed the gates into
    lexica_def — the table mode can't reach it (no stored row), and a hand edit of the file is
    hard-refused at apply by the 'edited' guard (by design: reviewed bytes must equal shipped
    bytes). This mode IS the sanctioned edit: it updates the stored prose fingerprint so the
    builder accepts the bytes, banks the pre-fix draw to draws/history/, and stamps the fix
    (old/new/why) into the record so the edit is visible forever — a silent hand edit still
    refuses exactly as before.

    Same certification boundary as table mode (header above): byte-grounded quote fixes and
    deletions of unverified claims ONLY; never a re-carve. VALIDATION DOES NOT HAPPEN HERE —
    this mode edits and stamps, then the builder's own review pass re-runs the FULL battery on
    the fixed bytes (the production gates, never a copy; and only the builder has the fed
    sample for coverage + probe-2 context grounding). Ship path after fixing:
        build_lexica_def.py --dry-run [--hints] --word <sid>   (full battery, review)
        build_lexica_def.py --apply  [--hints] --word <sid>    (ships the reviewed bytes)"""
    rec = B.load_draw(sid)
    if rec is None:
        sys.exit(f"no cached draw for {sid} ({B.draw_path(sid)})")
    raw = rec.get("raw", "")
    if rec.get("prose_sha") != B._sha1(raw):
        sys.exit("draw prose does not match its stored fingerprint — the file was edited OUTSIDE "
                 "this tool. Refusing (the 'edited' guard exists for exactly this); restore the "
                 "file from draws/history/ first.")
    if args.show_raw:
        print(f"\n===== {sid}  {rec.get('lemma','')} — cached draw raw prose =====\n")
        print(raw)
        return
    if args.apply:
        sys.exit("--apply is not a draw-mode action: the fix is written to the draw file "
                 "immediately, and SHIPPING stays with build_lexica_def.py --apply after its "
                 "own dry-run review of the fixed bytes.")
    if args.old is None or args.new is None:
        sys.exit("pass --old AND --new (exact text to replace), or --show-raw to dump the raw.")
    if not (args.why or "").strip():
        sys.exit("--why is REQUIRED in draw mode (ruling condition 4, 2026-07-15): the fix "
                 "provenance is stamped into the draw record.")
    n = raw.count(args.old)
    if n != 1:
        sys.exit(f"--old must match the draw raw EXACTLY ONCE; found {n}. Aborting (nothing changed).")
    raw2 = raw.replace(args.old, args.new)
    new_sha = B._sha1(raw2)
    print(f"\n{sid}  {rec.get('lemma','')}  (draw {rec.get('sig','')[:8]})")
    print(f"  -  {args.old}")
    print(f"  +  {args.new}")
    B.archive_draw(sid, rec.get("sig"), new_sha)     # bank the pre-fix bytes to history first
    rec["raw"] = raw2
    rec["prose_sha"] = new_sha                       # sig UNCHANGED — the draw input never moved
    rec.setdefault("raw_fixes", []).append({
        "old": args.old, "new": args.new, "why": args.why,
        "when": datetime.datetime.now(datetime.timezone.utc)
                        .replace(tzinfo=None).isoformat(timespec="seconds"),
    })
    tmp = B.draw_path(sid) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    os.replace(tmp, B.draw_path(sid))
    print(f"  fixed draw written -> {B.draw_path(sid)} ({len(rec['raw_fixes'])} raw fix(es) on record)")
    print("  NEXT: re-run the builder's --dry-run for the FULL gate battery on these bytes; "
          "only its --apply ships them.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"))
    ap.add_argument("--word", required=True, help="G/H number, e.g. G5484")
    ap.add_argument("--old", help="exact text in the stored raw to replace (must occur once)")
    ap.add_argument("--new", help="replacement text")
    ap.add_argument("--draw", action="store_true",
                    help="operate on the word's CACHED DRAW file instead of the lexica_def row — "
                         "for a word that has never passed the gates into the table (see fix_draw)")
    ap.add_argument("--why", help="draw mode: REQUIRED one-line provenance for the fix "
                                  "(stamped into the draw record's raw_fixes)")
    ap.add_argument("--draws-dir", dest="draws_dir",
                    help="override the draws directory (tests only)")
    ap.add_argument("--show-raw", action="store_true", dest="show_raw",
                    help="print the stored raw prose and exit — to craft an exact --old/--new edit")
    ap.add_argument("--adjudicate-warns", metavar="NOTE", dest="adjudicate_warns",
                    help="record the reviewer adjudication for OPEN V11 warns on the CORRECTED "
                         "entry — needed when the edit CHANGES the warn set (the prior ruling "
                         "never saw the new items, so it is not carried). Same surface as "
                         "build_lexica_def.py --adjudicate-warns; stamped into "
                         "audit.warns_adjudicated so the row self-documents the ruling.")
    ap.add_argument("--apply", action="store_true", help="write the row (default: dry-run, show only)")
    args = ap.parse_args()

    sid = args.word.upper()
    if sid[:1] not in ("G", "H"):
        sid = "G" + sid
    if args.draws_dir:
        B.DRAWS_DIR = args.draws_dir
    if args.draw:
        fix_draw(sid, args)
        return

    # Read-only unless we're actually writing the row (--apply); a dry-run / --show-raw must never
    # be able to touch the live file (audit C3, 2026-07-01 — same invariant as build_lexica_def.py).
    if args.apply:
        conn = sqlite3.connect(args.db)
    else:
        conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.create_function("strip_accents", 1, B.strip_accents)

    row = conn.execute("SELECT def_json, synth_ver FROM lexica_def WHERE strongs=?", (sid,)).fetchone()
    if not row or not row["def_json"]:
        sys.exit(f"no stored Lexica row for {sid}")
    e = json.loads(row["def_json"])
    raw = e.get("raw", "")
    # The prior reviewer ruling + the warn set it ruled OVER — captured BEFORE assemble(), which
    # rebuilds `audit` fresh from the prose and does NOT carry warns_adjudicated (gap 2).
    prior_audit = e.get("audit") or {}
    prior_adj = prior_audit.get("warns_adjudicated")
    prior_warns = canon_warns(prior_audit)
    if args.show_raw:
        print(f"\n===== {sid}  {e.get('lemma','')} — stored raw prose =====\n")
        print(raw)
        conn.close()
        return
    if args.old is None or args.new is None:
        sys.exit("pass --old AND --new (exact text to replace), or --show-raw to dump the raw.")
    # --new "" is a legitimate CUT (delete the matched text), not a missing arg — so test for
    # None, not falsiness. The exact-once guard below still protects against a bad --old.
    n = raw.count(args.old)
    if n != 1:
        sys.exit(f"--old must match the stored raw EXACTLY ONCE; found {n}. Aborting (nothing changed).")

    raw2 = raw.replace(args.old, args.new)
    print(f"\n{sid}  {e.get('lemma','')}")
    print(f"  -  {args.old}")
    print(f"  +  {args.new}")

    entry = B.assemble(conn, sid, e.get("lemma") or sid, e.get("translit") or "", raw2)
    entry["synth_ver"] = row["synth_ver"] or B.synth_ver()   # surgical edit ≠ new generation: keep the stamp
    B.show_entry(entry)

    # GAP 1 (ENGINE_LESSONS #69, third instance): `conn` MUST be passed — without it
    # validate_entry prints "prose probes NOT RUN" and SKIPS the verbatim-quote gate, the
    # named-subject probe and the identity scanner. This path WRITES, so it runs every check
    # the main write path runs (build_lexica_def.py, the validate_entry(entry, conn) call site).
    problems = B.validate_entry(entry, conn)
    if problems:
        print("  ✗ PARSE FAILURE — not written:")
        for p in problems:
            print("     - " + p)
        sys.exit(1)

    # GAP 2 — CARRY RULE (reviewer-ruled 2026-07-14, standing for this tool). A ruling
    # adjudicated the warns that existed WHEN IT WAS MADE. Carry it across a surgical edit ONLY
    # when the new warn set is identical over the CANONICAL form; if the set changed, the old
    # ruling never saw the new items — do NOT carry (that would stamp "reviewed" on items no
    # reviewer saw = a falsified record). SILENT CARRY-FORWARD IS BANNED: every branch prints.
    # CHANGED SET => FULL REOPEN, NO PARTIAL CARRY (ruled 2026-07-14): every warn goes back to
    # the reviewer, including ones a prior ruling covered. Keeping the "same" items and reopening
    # only the new ones would make the TOOL decide which prior items are same-enough — machine
    # adjudication, which the ruling reserves for a reviewer. The review cost is paid only when an
    # edit actually moves the warn set, which is rare and is itself worth a fresh look.
    new_warns = canon_warns(entry.get("audit"))
    has_warns = json.loads(new_warns) != json.loads(canon_warns({}))
    if prior_adj and new_warns == prior_warns:
        entry["audit"]["warns_adjudicated"] = prior_adj
        print(f"  ✓ warn set UNCHANGED by this edit — prior adjudication carried: {prior_adj}")
    elif args.adjudicate_warns and has_warns:
        entry["audit"]["warns_adjudicated"] = args.adjudicate_warns
        print(f"  ✓ adjudication recorded for the corrected entry: {args.adjudicate_warns}")
    elif prior_adj:
        print("  ⚠ this edit CHANGED the warn set — the prior adjudication is NOT carried "
              "(it never saw the new items). Prior ruling, for the reviewer:", file=sys.stderr)
        print(f"      {prior_adj}", file=sys.stderr)

    # GAP 3 — the open-warn refusal the main write path enforces. Created by fixing gap 1: once
    # the probes actually run here they emit warns, and with no gate this tool would write
    # exactly the rows build_lexica_def refuses.
    # Same CONVENTION as the main path, not just the same check: a dry-run WARNS (it exists to
    # preview the correction), only --apply refuses.
    blocked = B.open_probe_warns(entry)
    if blocked:
        if args.apply:
            print(f"  ✗ NOT written — {len(blocked)} OPEN V11 item(s) with no adjudication; after "
                  f"the reviewer rules them, re-run with --adjudicate-warns \"ruling\":",
                  file=sys.stderr)
            for w in blocked:
                print("      - " + w, file=sys.stderr)
            sys.exit(1)
        print(f"  ⚠ {len(blocked)} OPEN V11 item(s) — an apply will be REFUSED until "
              f"adjudicated (--adjudicate-warns).", file=sys.stderr)

    if args.apply:
        conn.execute(
            "INSERT OR REPLACE INTO lexica_def (strongs, lemma, translit, def_json, synth_ver, updated) "
            "VALUES (?,?,?,?,?,?)",
            (sid, entry["lemma"], entry["translit"], json.dumps(entry, ensure_ascii=False),
             entry["synth_ver"],
             datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")))
        conn.commit()
        print("  → written to lexica_def.")
    else:
        print("  [dry run — not written]")
    conn.close()


if __name__ == "__main__":
    main()
