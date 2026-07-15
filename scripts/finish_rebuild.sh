#!/usr/bin/env bash
# finish_rebuild.sh — the post-build TAIL of the single-pass words rebuild.
#
# The build (build_words_from_abp.py) now SELF-CORRECTS: the six former cleanup
# scripts (bracket_punct, g1473_gloss, lord_subject, funcword_subject, lord_oath,
# greek_pos_gaps) are folded into the build pass. This script runs only what is
# left: restore proper nouns, then apply the SMALL pinned data-patches that cannot
# fold (each only touches its own named verses, and would regress others if made
# a general rule). All steps are targeted + re-runnable — no DELETE, no swap.
#
# COPY-FIRST: run on a COPY (e.g. bible_test.db), never on the live bible.db.
# Run AFTER:  python3 scripts/build_words_from_abp.py <copy.db> bh_scrape.db
#
# Usage:  bash scripts/finish_rebuild.sh bible_test.db
#
# THE VERDICT IS HONEST (JP-ruled 2026-07-14). This chain deliberately does NOT `set -e`: every
# step is independently targeted and re-runnable, and aborting mid-way would leave a half-patched
# copy that is harder to reason about than a finished one with named failures. But until now
# run() also never LOOKED at an exit code — so ANY failing step (import_tipnr included) scrolled
# past under the steps after it and the script still printed "done". A failure degrading into a
# green-looking finish is exactly the silent-fallback class this repo keeps paying for.
# So: keep going, COLLECT what went wrong, and REFUSE to declare success.
set -uo pipefail
DB="${1:-bible_test.db}"
cd "$(dirname "$0")/.."

PROBLEMS=()
run() { echo; echo "── $* ──"; if ! "$@"; then PROBLEMS+=("$*"); fi; }

echo "== finish_rebuild on ${DB} =="

# 1) Proper nouns: the build clears is_pn + PN Strong's; restore them.
run python3 scripts/import_tipnr.py "${DB}"

# 2) The pinned data-patches (NOT folded — per-verse corrections / source mistags).
#    Order mirrors the CLAUDE.md checklist (minus the six now folded into the build).
run python3 scripts/fix_subject_reorder.py   "${DB}"
run python3 scripts/fix_mat25_37.py          "${DB}"
run python3 scripts/fix_supplied_attach.py   "${DB}"
run python3 scripts/fix_theos_filler_tags.py "${DB}" --apply
run python3 scripts/fix_split_merges.py      "${DB}" --apply
run python3 scripts/fix_kyrios_mistags.py    "${DB}" --apply
run python3 scripts/fix_merge_misses.py      "${DB}" --apply
# idios "own" click-targets: 'his/their/its own' parked on the article slot ->
# relocate onto the empty G2398 slot. Adjective orphan, so the noun fold skips it.
run python3 scripts/fix_idios_own.py         "${DB}"

# 3) Safety net: drop any byte-identical duplicate rows (normally 0 now that the
#    Hab 3:14 source dup is fixed).
run python3 scripts/dedup_words.py           "${DB}"

# 4) Final punctuation float — runs after the patches so it also tidies the
#    LORD-subject (and any other) brackets created/modified above: a trailing comma
#    left on the verb floats to the last chip shown ('said · the LORD,'). ~202 cells;
#    re-run settles to 0.
run python3 scripts/fix_bracket_punct.py     "${DB}"

# 4b) S9 (f): prose (verses.text) corrections — the FIRST of the two abp_corrections points.
#     MUST precede fix_split_flip (step 6 compares words to verses.text as its oracle) and stays
#     verses-only; word-cell corrections apply at step 7. Guarded: a cell that is not its recorded
#     before-value is a LOUD skip (e.g. prose not regenerated), so it is safe even on a build that
#     skipped load_abp_prose. Same NO_CORRECTIONS gate as step 7.
if [ "${NO_CORRECTIONS:-0}" = "1" ]; then
  echo; echo "── prose abp_corrections SKIPPED (NO_CORRECTIONS=1 attribution run) ──"
else
  run python3 scripts/apply_abp_corrections.py "${DB}" --apply --only verses
fi

# 5) Em-dash swap ('--' -> '—' in words.english + verses.text) — the LAST step that
#    edits english TEXT: split_merge_fixes.json carries a '--' precondition ("you
#    think not --") that would stop matching if this ran before fix_split_merges.
#    Folded 2026-07-03 (cert Session 1). Only position/field-scoped steps may follow.
run python3 scripts/fix_emdash.py            "${DB}" --apply

# 6) Split-flip repair — the "Kenites the" stranded-determiner class from the
#    proper-noun slot producer (_split_compounds' source-order fix doesn't cover it;
#    cert run 1: 175 verses / 196 pairs regenerate on every rebuild). Swaps POSITION
#    values only, never text, looping to convergence. ORDER IS LOAD-BEARING: after
#    ALL pinned patches (fix_split_merges targets absolute positions) and after
#    fix_emdash (the detector compares words to verses.text — dash tokens must
#    agree). Folded 2026-07-04 (cert Session 2). Gate: audit_split_flip.py must
#    read 0 on the finished copy.
run python3 scripts/fix_split_flip.py        "${DB}" --apply

# 7) abp_corrections guarded apply — the TRUE final step (corrections are keyed by
#    position, so nothing may move positions after this). Each row fires only if the
#    cell still equals its recorded source_value; any mismatch is a LOUD skip.
#    Skippable for cert attribution runs (harness --no-corrections sets this).
if [ "${NO_CORRECTIONS:-0}" = "1" ]; then
  echo; echo "── abp_corrections SKIPPED (NO_CORRECTIONS=1 attribution run) ──"
else
  run python3 scripts/apply_abp_corrections.py "${DB}" --apply --only words
fi

echo
if [ "${#PROBLEMS[@]}" -ne 0 ]; then
  echo "=============================================================================="
  echo "!! finish_rebuild did NOT finish clean — ${#PROBLEMS[@]} step(s) reported a problem:"
  for p in "${PROBLEMS[@]}"; do echo "     - ${p}"; done
  echo
  echo "!! DO NOT SWAP. Read each step's own output above — a step that reported a"
  echo "   problem may have FAILED, or may have completed and flagged something for a"
  echo "   human (the probe-2 guard fixture drift check is the second kind: the rebuild"
  echo "   is fine, the fixture is stale). Fix or re-rule, then re-run this script."
  echo "=============================================================================="
  exit 1
fi
echo "== finish_rebuild done. Next: audits + compare_words.py vs live, THEN swap. =="
echo "   (positions moved in step 6 — after a real swap, re-run build_abp_surface.py"
echo "    + build_abp_translit.py per the rebuild checklist)"
