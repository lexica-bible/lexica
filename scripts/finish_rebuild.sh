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
set -uo pipefail
DB="${1:-bible_test.db}"
cd "$(dirname "$0")/.."

run() { echo; echo "── $* ──"; "$@"; }

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

# 5) Em-dash swap ('--' -> '—' in words.english + verses.text) — MUST stay the very
#    LAST step: split_merge_fixes.json carries a '--' precondition ("you think not --")
#    that would stop matching if this ran before fix_split_merges. Folded here
#    2026-07-03 (cert Session 1): kills the manual re-run step and its whole
#    expected-delta class in the certification harness.
run python3 scripts/fix_emdash.py            "${DB}" --apply

echo
echo "== finish_rebuild done. Next: audits + compare_words.py vs live, THEN swap. =="
