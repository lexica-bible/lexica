# Graveyard — decommissioned rebuild scripts (cert Session 2, 2026-07-04)

These scripts are RETIRED, not deleted. The certification final run (626,305 = 626,305
rows; residue = exactly the 11 pre-registered live-stale verses, nothing else) proved
that a full rebuild — `build_words_from_abp.py` + `finish_rebuild.sh` + the
`abp_corrections` table — reproduces the live corpus without any of them. Do NOT run
them against the live db; they are kept only as historical reference for how each fix
was first worked out. Full record: AUDIT_abp_certification.md.

Why each one is here:

**Folded into the build** (build_words_from_abp.py has the fold; the standalone twin is dead):
- `fix_g1473_gloss.py` — residual ἐγώ/G1473 mis-tags
- `fix_lord_subject.py` — LORD-subject dual-ordering (pilot #1)
- `fix_funcword_subject.py` — function-word noun relocate (rounds 1–3)
- `fix_lord_oath.py` — "As the LORD lives" oath formula
- `fix_greek_pos_gaps.py` — bracketed NULL greek_pos backfill
- `fix_abp_numerals.py` — Greek-numeral digit fill
- `fix_hab314_dupes.py` — Hab 3:14 source dup (source fixed; dedup_words stays in the
  tail as the 0-expect safety net)

**Migrated to the abp_corrections table** (guarded apply, finish_rebuild.sh step 7):
- `fix_cushi_strongs.py` — the 6 Cushi slots in 2Sa 18 (H3570→H3569); table rows
  ledger_ref 'Class2-cushi'

**Adjudicated dead code** (cert final run showed ZERO unexplained deltas — whatever these
once fixed is either reproduced by the build or was long since superseded; never part of
the live build/tail path):
- `fix_bracket_gaps.py`
- `fix_bracket_gaps_absorb.py`
- `fix_bracket_merge.py`
- `fix_bracket_misplacements.py`
- `fix_multipos_gaps.py`
- `fix_orphan_greek_pos.py`

(`fix_article_noun_swaps.py` was already deleted earlier — replaced by
`_fix_backwards_pairing` in the build.)
