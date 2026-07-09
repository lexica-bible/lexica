# CHARTER — words-table splitter double-tag fix (dedicated session)

**STATUS: CLOSED 2026-07-09 — polarity A SHIPPED (607 helper rows untagged, live + folded into
the builder); polarity B DEFERRED to its own ticket per reviewer Ruling 8 (878-case evidence
list, hand-review-only). All acceptance checks passed; record in AUDIT_lexica_rollout.md
(splitter-fix session entry) + TODO.md ticket. Calibration UNPAUSED.**

**CORRECTION (2026-07-09, reviewer Ruling 23): the G977 acceptance target below reads "37
verses" — that was a miscount at ticket-writing time; correct is 38 verses / 39 occ. No fix
path reaches 37: Job 18:13 keeps a genuine G977 row under both the A-strip and any future
B-fix. The G2008 37-verse figure was correct and is likewise B-independent (Rth 2:16's blank
G2008 row was already counted in it).**

**Opened from batch-3 session 3 (2026-07-09).** This session does ONE job: fix the splitter
double-tag defect class in the words table. Calibration is PAUSED until this charter's acceptance
checks pass — do not draw, floor, or ship any dictionary word from this session.

## The defect (verified, three exhibits)
ABP two-word verb renderings spanning a helper word mis-store in the words table. TWO polarities:
- **Tag-duplication:** helper row AND verb row both carry the verb's Strong's.
  - Jud 1:9: "May"|2008 + "reproach"|2008 (eSword tags only "reproach"; ABP app shows one chunk
    "May [2reproach" — verified 2026-07-09, BUILD artifact, not source).
  - Job 18:13: "And may"|977 + "be devoured"|977.
- **English-pooled-on-wrong-row:** the whole English chunk sits on the FIRST word's row, the
  verb's row is blank.
  - Rth 2:16: pos 14 "you shall not reproach"|3756 (οὐκ, the negation) + pos 15 ""|2008 (the verb).

Sizing (NOT an audit): 731 adjacent same-tag pairs where the first row's English is one of
may/shall/will/did/do/does/let. The Rth shape (blank-verb-row) is NOT in that count and needs its
own sweep. Some of the 731 may be LEGITIMATE (a genuine two-word rendering fairly carrying the tag
on both halves) — the discriminator must separate them.

## NO-WRITE GATE (JP-ruled, hard)
1. Propose a patch discriminator that distinguishes: (a) tag-duplication → strip the helper row's
   tag; (b) English-pooled → re-align English to the verb row; (c) legitimate split rendering →
   LEAVE ALONE. It must handle BOTH exhibit polarities.
2. Dry-run it on ALL THREE exhibits + a hand-audited sample of the 731 (and a blank-row sweep
   sample for the Rth shape). Show JP the dry-run output; he confirms before any write.
3. **If the sample turns up a third polarity, or legitimate renderings the rule can't cleanly
   separate: STOP and report. Do not write.** A partial confident subset may be proposed, but
   that is JP's call, not the session's.
4. Standing rules apply in full: CC proposes exact commands, JP runs them on PA; checkpoint
   approval before any write; NEVER DELETE FROM words/verses; patch = UPDATE of identified rows
   only; verses.text is untouched (the defect is word-row level; the prose column is correct).
   Take a fresh backup before the write (scripts/backup_db.py or a manual copy).

## ACCEPTANCE CHECKS (all required, in order)
1. Post-patch: the three exhibit words' word rows correct (Jud 1:9 one 2008 row; Job 18:13 one
   977 row; Rth 2:16 English on the verb row).
2. Render check on all three words: **no helper-word chips** in "ABP RENDERS AS", search-result
   highlighting lights only the verb, occurrence counts correct (G2008: 37 verses/38 occ, sole
   double Zec 3:2 · G977: 37 verses/39 occ, sole double Isa 51:8).
3. Cert invariants green: strongs_base GLOB check = 0; tests/test_strongs_join.py +
   test_build_invariants.py pass; spot-verify a handful of untouched verses unchanged.
4. **Fold the rule into the build script** (build_words_from_abp.py splitter — cf. the af8e296
   splitter fix pattern) so the next rebuild doesn't regress. Both polarities, one root:
   phrase-to-slot assignment for multi-word English spanning two Greek words.
5. THEN the two stale gloss bullets get delete-class swaps via fix_lexica_raw (dry-run → diff →
   apply, per the established gate):
   - G977 bullet 2 (the "may (Job 18:13)" bullet — whole bullet deletes).
   - G2008 bullet 3 (the "may (Jud 1:9)" bullet — whole bullet deletes).
   Re-render both cards; screenshot pass.
6. Update the TODO.md ticket (mark fixed, keep the exhibits as history) + one line in the batch-3
   handoff that the pause is lifted.

## Context pointers
- Ticket (full history, 3 exhibits, detection heuristic, downstream surfaces):
  TODO.md "Helper-word double-tag class".
- Session-3 log + audit entries for G2008/G977 (occ corrections): HANDOFF_lexica_rollout.md +
  AUDIT_lexica_rollout.md.
- eSword verification precedent: confirm any surprising layout against eSword/ABP app only
  (2026-06-07 Act 19:4 lesson; memory feedback_confirm_source_never_guess).
- 731-pair sizing query is in the batch-3 session-3 chat log; rebuild it from the ticket text.

## After this session
Calibration resumes at: **3 shipped this session (ἐπιτιμάω, διανοίγω, βιβρώσκω) · count PENDING
JP's ruling on βιβρώσκω (options in the audit doc G977 entry; CC recommended 3/15 + intervention-
tally data point) · streak 0 · next-word decision travels with the ruling (κατανοέω vs a RED seed
— περιτομή G4061 / σκληρύνω G4645, one more routing exercise still owed eventually).**
