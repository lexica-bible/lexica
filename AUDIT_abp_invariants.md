# ABP Certification — Invariant Catalog (Session 1)

Machine-checkable properties over the source feeds, the ~18 judgment passes in
`scripts/build_words_from_abp.py`, and the post-insert/tail chain. Each entry:
**statement · check sketch · known-positive control · tier it detects · status**.
Control-test rule applies to every entry: the check must FIRE at its known positive
(or a hand-broken row) before any zero it reports is trusted. No lint code ships in
this session unless the check is a one-line query — the runnable suite is Session 2.

Tiers: **A** = our ingest bug (parser/pass unfaithful to source). **B** = source
defect (goes to the correction table, never fixed in place). **H** = hygiene
(input-file cleanliness before pinning).

Status keys: `GATE` = already a standing script/test in the rebuild checklist;
`QUERY` = expressible as a paste-able SQL one-liner (Session 2 wires it into a suite);
`SWEEP` = needs a small Python pass (re-parse assertion); `CENSUS` = measure the
residue on PA first, then decide the assertion level.

---

## S — Structural invariants (the source format forces these, no pass involved)

**S1. Every non-blank source line is a verse header.**
Any other line is an editing artifact the parser silently drops (L1 class).
Check: `_VERSE_RE` census over all 66 files — now built into
`scripts/cert_manifest.py build` (refuses to pin dirty sources).
Control: fired on exactly the 4 known L1 lines this session (deu:960, exo:1214,
lev:860, num:1289). Tier H. Status: GATE (new, manifest-embedded).
**L1 CLEANUP DONE 2026-07-03** (JP's go; diff = exactly the 4 lines, census re-run = 0).

**S2. Every `G` token in the source carries digits or `*`.**
A numberless `G` never matches `_STRONGS_RE` (build:120), so its text leaks into a
neighbouring english cell. Check (source side):
`grep -P 'G(?![\d*A-Za-z])'` over the 66 files.
Control: fired 7× this session and RECONCILES: 5 = the known blank-"G." set already
repaired in-build by `apply_blank_strongs_fills` (Zec 9:11, 1Pe 3:13, Act 24:8,
Heb 7:4, Mat 12:14); 1 = L2 (1Sa 6:11 "buttocks.G"); 1 = **NEW: Mal 3:6 trailing
bare "G"** ("I change not.G3756 G") — proposed ledger entry **L10**, same class as
L2, correction-table candidate. Tier B. Status: QUERY (source-side; DB-side residue
check is S2b below).

**S2b. No stray Strong's-fragment in `words.english`.**
DB footprint of S2: an english cell that is exactly "G" or ends ".G".
Check: `SELECT ... WHERE english = 'G' OR english LIKE '%.G'` (JP runs on PA; Mal 3:6
should show the stray row — that's the control). Tier B. Status: QUERY.

**S3. Verse-key completeness (three-way).**
Every (book,ch,vs) in the source exists in `verses`, every `verses` row has ≥1
`words` row, and the build reports `Verses skipped: 0`. A missing verses row
SILENTLY drops its words (the Heb 13 lesson). Check: source-count vs
`SELECT count(*) FROM verses` + anti-join `verses LEFT JOIN words … WHERE words.id
IS NULL`. The harness now aborts on a non-zero "Verses skipped".
Control: Heb 13 pre-restore (whole chapter absent); hand-delete one scratch verse's
words. Tier A. Status: QUERY + harness GATE.

**S4. No duplicate (verse_id, position).**
Check: `GROUP BY verse_id, position HAVING count(*)>1` → 0.
Control: the historic Hab 3:14 source dup (now fixed at source; `dedup_words.py`
in the tail is the safety net whose expected count is 0). Tier A. Status: QUERY
(also inside `health_check.py`).

**S5. Position contiguity per verse.** min(position)=0, max=count−1, no gaps.
Check: `SELECT verse_id FROM words GROUP BY verse_id HAVING min(position)!=0 OR
max(position)!=count(*)-1`. Control: hand-shift one scratch row. Tier A.
Status: QUERY.

**S6. Bracket contiguity.** Rows sharing a bracket_id within a verse occupy
consecutive positions. Check: per (verse_id, bracket_id):
`max(position)-min(position)+1 = count(*)`. Control: hand-move one member.
Tier A. Status: QUERY.

**S7. No bracket residue in english.** `clean_english` strips `[`/`]`; any survivor
is a parse leak. Check: `english LIKE '%[%' OR english LIKE '%]%'` → 0.
Control: hand-inject. Tier A. Status: QUERY.

**S8. No position-number residue in english.** An ABP reorder digit glued to a
letter ("2day") must never survive `clean_english` / `_split_numbered` (build:163).
Check: `english GLOB '*[0-9][a-zA-Z]*'` → enumerate; legitimate digits (the numeral
fills "600", verse-internal numbers) are standalone. Control: hand-inject "2day".
Tier A. Status: CENSUS first (legit digit-letter strings like "1st" may exist),
then QUERY with the vetted exclusion list.

**S9. strongs_base fully G/H-prefixed.** `strongs_base GLOB '[0-9]*'` → 0.
Control: the 2026-06-03 592k regression class; test-locked in
`tests/test_strongs_join.py` + `test_build_invariants.py` (`_prefix_base`,
build:1350). Tier A. Status: GATE (fold in unchanged).

**S10. `strongs` stays bare.** Only digits/dots, `*`, or ''. Check:
`strongs GLOB '[GH]*'` → 0. Control: hand-inject. Tier A. Status: QUERY.

**S11. strongs_base derivable from strongs — with an enumerated exception list.**
Where `strongs NOT IN ('*','')`: `strongs_base = 'G' || <strongs before first dot>`.
Known, documented deviations: import_tipnr PN resolutions (strongs='*', real
G/H base), the Cushi fix (H3569 on 6 slots), the Cyrus mistags (H3566), any
g1473 retags (both columns move together, so they don't deviate). The exception
list must be ENUMERABLE and each member must map to a ledger/correction entry —
an unexplained deviation is a finding. Control: the Cushi rows themselves (the
check must list them). Tier A/B split per deviation. Status: SWEEP.

**S12. greek_pos only inside brackets.** `greek_pos IS NOT NULL AND bracket_id IS
NULL` → 0 (`_prefix_base` guard 2, build:1364). Control: hand-inject; the orphan
class `fix_orphan_greek_pos.py` used to repair. Tier A. Status: QUERY (also in
health_check).

**S13. Bracketed, displayed words carry a greek_pos (post `_greek_pos_backfill`,
build:1195).** A bracket where NO member ever had a number can legitimately stay
NULL — measure before asserting. Check: census `bracket_id NOT NULL AND english
NOT NULL AND greek_pos IS NULL`, classify by whether the bracket has any numbered
member. Control: pre-backfill state (the fix_greek_pos_gaps class). Tier A.
Status: CENSUS.

**S14. italic recomputable.** `italic = 1` iff the display word (english_head, or a
single-word english) is in the row's italic_words set (build:1310–1313).
Check: Python sweep re-deriving the flag from stored columns. Control: hand-flip
one flag. Tier A. Status: SWEEP.

**S15. english_head recomputable.** `english_head = _head_word(english,
italic_set)` under the two accepted caveats (`HEAD_WORD_TAIL_CAVEAT`,
`SPLIT_FUNCWORD_SLOT_CAVEAT` — NOT re-opened). Check: Python sweep importing the
production `_head_word` (never a re-implementation). Control: hand-break one head.
Tier A. Status: SWEEP.

**S16. τοῦτο-paradigm (L4).** Every `abp_surface.form GLOB 'τούτ*'/'ταύτ*'` row
joins to strongs_base='G3778'. KNOWN failing by exactly the 15 enumerated strays
(+9 null-form candidates pending JP's source eyes) — the invariant ships with that
exception list until the parked retag lands. Control: 3401 hits on G3778 (certified
2026-07-03); the GLOB must be on the FORM column with real accents (the γῆ-class
lesson). Tier B (source mistag). Status: QUERY + exception list.

**S17. No `--` clause-dash residue.** **FOLDED 2026-07-03** — `fix_emdash.py` now
runs as the LAST step of `finish_rebuild.sh` (order load-bearing: a "--"
precondition in split_merge_fixes.json must match first). Check: `english LIKE
'%--%'` on words + verses.text → 0 on live AND on a full-path scratch; the
harness's `emdash` hint-tag now firing means the tail step regressed. Control:
any pre-fix source line with `--` (1Ch 1:5 above). Tier A. Status: QUERY.

---

## P — Per-pass invariants (self-correcting build ⇒ each pass's own trigger
shape finds ZERO rows in the finished DB; where a standalone twin script exists,
"re-run finds 0 to do" IS the check — build:815–822 states this design)

**P1. `parse_abp_line` / `_emit_words` helper-peel (build:189).** No english cell
both opens a bracket and carries pre-bracket words (peel exhaustive). Covered by
S7 residue + `audit_bracket_order.py` (GATE: genuine ≈ 2 known Jon 4:9 twin-bracket
FPs). Control: the pre-peel Psa 21:8 class. Tier A. Status: GATE.

**P2. `_split_numbered` (build:163).** A single Greek word spread over N reorder
slots yields N rows sharing one Strong's; no skipped bracket number. Check: within
a bracket, the set of greek_pos values has no gap that a multi-number source chunk
should have filled — concretely, re-parse assertion: source token count per verse
(via `iter_source_tokens`, build:256, the SHARED tokenizer) equals pre-redistribution
row count. Control: Jas 2:21 / Job 3:4 (the 321-chunk class). Tier A. Status: SWEEP
(harness-adjacent; iter_source_tokens is already shared so it can't drift).

**P3. `bh_lookup` metadata overlay (build:350).** italic_words / smcap_words tokens
should refer to words present in the row's english cell. Redistribution passes move
english but not always iw — residue is possible and is a REAL finding class, not
noise. Check: Python sweep, tokens ⊆ english (case-folded). Control: hand-attach a
bogus iw. Tier A. Status: CENSUS first (measure residue scale on PA).

**P4. `apply_pronoun_corrections` (build:717, Rahlfs/TAGNT).** Feed-presence is the
invariant: the harness ABORTS if Rahlfs/TAGNT are missing (a silent skip builds a
different corpus). Flag-file volume ~6,880 stable across rebuilds (checklist
number). Control: rename the Rahlfs dir → harness must refuse. Tier A (run
validity). Status: GATE (harness precheck).

**P5. `_redistribute_pronoun_compounds` (build:761).** Trigger shape empty:
no unbracketed slot with base in `_PRONOUN_BASES`, multi-word english, whose next
slot is empty + real-Strong's + non-article + unbracketed. Check: SQL over
adjacent positions. Control: Gen 3:15 pre-fix shape, hand-rebuilt in scratch
(`tests/test_folded_fixes.py` already exercises the fold on synthetic verses).
Tier A. Status: QUERY.

**P6. `_split_compounds` (build:386).** CERTIFIED (L9) — standing gates
`lint_split_wrong_slot.py --control` GREEN + `size_split_compounds.py`
reconciliation (18,339/12,692). Fold in as-is; do NOT re-open. Tier A. Status: GATE.

**P7. `_fix_backwards_pairing` (build:599).** Trigger fingerprint empty: no
function-word slot (article/prep set) whose head is a content noun found in an
adjacent slot's lexicon def while that adjacent slot shows only a connector.
Check: `scan_strongs_cross.py` FUNCTION-anchor = 0 (existing checklist gate).
Control: 1Sa 5:2 / Rom 8:34 pre-fix. Tier A. Status: GATE.

**P8. `_split_pn_article_lump` (build:645).** No unbracketed G3588 slot with
"<Name> the" english beside an empty `*` slot. Control: Act 19:4 pre-fix (the only
corpus case — thin but real; also hand-inject in scratch). Tier A. Status: QUERY.

**P9. `_bracket_punct_float` (build:837) + tail `fix_bracket_punct.py`.**
No non-final displayed bracket member carrying trailing clause punctuation.
Twin re-run settles to 0 (checklist: ~202 cells then 0). Control: pre-float state.
Tier A. Status: GATE (twin re-run).

**P10. `_g1473_gloss_retag` (build:938).** No residual G1473 row whose gloss's last
word buckets 2P/3P with a parseable pronoun morph — the ~48 reflexive/no-morph
skips are the documented exclusion set (TODO), not failures. Twin
`fix_g1473_gloss.py` re-run = 0. Control: hand-inject a "you" gloss on a 1473 row
with a clean morph. Tier A. Status: GATE (twin) + exception list.

**P11. `_lord_subject_split` (build:987).** Trigger empty; twin
`fix_lord_subject.py` = 0. Control: the ~795-verse pre-fold class. Tier A.
Status: GATE (twin).

**P12. `_funcword_noun_relocate` (build:1070).** Twin `fix_funcword_subject.py`
= 0 AND `audit_funcword_wrongslot.py --preps` REPAIRABLE-NOUN ≈ 0 (existing gate).
Tier A. Status: GATE.

**P13. `_lord_oath_fix` (build:1146).** No κύριος/2962 slot english "As" whose
next slot is ζάω/2198 matching "the LORD …". Twin `fix_lord_oath.py` = 0.
Control: the 29-verse class. Tier A. Status: QUERY.

**P14. `_numeral_gloss_fill` (build:1184).** The three dotted numeral codes
(5462.1/3577.2/2193.2) never have blank english. Check: 3-row query.
Control: Rev 13:18 pre-fill. Tier A. Status: QUERY.

**P15. `_strip_italic_heads` (build:1224) + post-insert `apply_italic_heads`.**
No english_head that is an italic (translator-added) word of its own cell when a
non-italic content word exists. Twin `fix_italic_heads.py --all` = 0.
Control: the 4,409-row 2026-06-25 class ("take favor"→λαμβάνω under "favor").
Tier A. Status: GATE (twin).

**P16. `_prefix_base` (build:1350).** = S9 + S12. Test-locked
(`tests/test_build_invariants.py`). Status: GATE.

**P17. `apply_blank_strongs_fills` (post-insert, build:1498).** The 5 named verses
carry their assigned numbers (table in `fill_blank_strongs.py`); count per verse
exact. Control: the fill table itself. Tier B handled as declared overlay.
Status: QUERY.

**P18. `apply_pn_subject_split` (post-insert, build:1507).** Residual merge shape =
0 outside documented skips: `audit_pn_verb_merge.py` + `audit_eimi_subject_merge.py`
(existing read-only audits). Control: Gen 11:30 Sarai / Zep 2:6 Crete pre-peel.
Tier A. Status: GATE.

**P19. `import_tipnr` (tail).** ~27,965 matched stable; every is_pn=1 row has a
real G/H strongs_base; unresolved `*` share ~8% stable. Control: run the tail
without import_tipnr in scratch → the check must light up everywhere. Tier A
(ingest-final overlay from the TIPNR source). Status: QUERY.

**P20. Tail pinned patches (fix_subject_reorder 20 · fix_mat25_37 1 ·
fix_supplied_attach 5 · fix_theos_filler_tags 2 · fix_split_merges 237 ·
fix_kyrios_mistags 3 · fix_merge_misses 1 · fix_idios_own 13).** Invariant: each
patch reports FULL application, 0 skipped — a skip means build drift shifted its
absolute positions (the fix_split_merges precondition class) and the patch is
silently lapsing. Check: each script's own dry-run/skip report. Control: the
2026-06-14/18 peel/verb-split shifts that DID skip entries until regrafted.
Tier B (these ARE correction-table entries in script form — see reclassification).
Status: GATE (scripts' own reports), destination = correction table.

**P21. `_sort_brackets` (build:688) is DEAD CODE** — defined, never called since
ee84aa0 (verified by grep this session). Invariant it would have owned (bracket
members stay in source order) is carried by `audit_bracket_order.py` +
`audit_reorder_vs_source.py`. Action: delete the function or mark it, so a future
reader can't think it runs. Status: cleanup note, not a check.

---

## Existing standing gates folded in unchanged
`health_check.py` (14 checks, 0 warnings) · `audit_bracket_order.py` (genuine ≈ 2
known FPs) · `scan_strongs_cross.py` (FUNCTION-anchor 0) · `audit_lord_strongs.py`
(WRONG-SLOT REPAIRABLE 0) · `audit_funcword_wrongslot.py --preps` (≈0) ·
`scan_content_filler_tags.py` (G2316 0) · `audit_split_flip.py` (**0**, hard gate) ·
`audit_corpus_tier1.py` (A1 ≈ 176) · `audit_corpus_tier2.py` (~92%) ·
`lint_split_wrong_slot.py --control` (GREEN) · `size_split_compounds.py`
(reconciliation partner) · `tests/test_build_invariants.py`,
`test_strongs_join.py`, `test_folded_fixes.py` (CI).

## Accepted limits — NOT defects, never re-open
`HEAD_WORD_TAIL_CAVEAT` · `SPLIT_FUNCWORD_SLOT_CAVEAT` (both in parse_abp.py) ·
the ~48 g1473 reflexive/no-morph skips · the ~150 heb.db byform fallbacks ·
the 92% tier-2 agreement target (edition differences, not errors).
