# ABP Corpus Certification — Audit Log

Two-tier standard: **Tier A** = faithful ingest (DB matches source; re-parse + diff certifies; can reach done).
**Tier B** = source defect (never fixed in place; goes in a versioned correction table).
Control-test rule: every detection pattern fires at a known positive before its zero is trusted.

---

## Ledger

### L9 — `_split_compounds` gloss redistribution — **CERTIFIED (Tier A, freeze-as-declared-overlay)**

**What it does.** `_split_compounds` (in `scripts/build_words_from_abp.py`) takes a multi-word ABP gloss
parked on one slot ("God made" on ποιέω) and redistributes words onto adjacent empty Greek slots
("God" onto θεός), using lexicon evidence, then fronts them in source-English order. It fills
**18,339 empty slots across 12,692 verses** — **918** get a content word, the rest get function words
(of/and/the/his/she…).

**Verdict.** The content-word placements are faithful corpus-wide. Freeze it as a declared overlay
(it earns its place; retreating to ABP-native would discard 918 correct content placements + 17k
function moves to avoid a cosmetic function-word softness).

**Evidence — four independent legs:**
1. **Full census, 0 wrong-slot.** All 918 content recipients audited by `scripts/lint_split_wrong_slot.py`;
   9 raw flags, all 9 were words that appear in their own number's gloss (odd wording, not wrong-slot);
   residue 0.
2. **Exact reconciliation.** The lint's recipient capture matches the independent
   `scripts/size_split_compounds.py` sizing count exactly (18,339 / 12,692) — both harnesses agree on
   what the split moved, so the scope is trustworthy.
3. **External sample, 0/60.** A 60-verse spread hand-read against **BibleHub**'s tagged ABP (Gen 27:27,
   Psa 78:49 etc.) — every content word on the correct Greek word.
4. **Excluded-set sweep.** The 154 distinct words the audit excludes (function-word recipients) are all
   true function words + "vain"×4 (a correct placement). Nothing content-shaped hides in the excluded set.

**Reference limit — which leg carries which claim.** The lint's yardstick is the corpus's OWN renderings
with a frequency floor (a rendering must recur ≥3× on a ≥8-use number to validate a slot). This proves no
**idiosyncratic** wrong-slot (a one-off or fired-twice leak). The **systematic** failure mode — the same
wrong word recurring on the same number ≥3× — would look legit to the lint and is carried by the
**independent BibleHub leg (#3)**, not the lint. The two legs together close both failure modes.

**Accepted limit.** A bare function word can land on a pronoun/article slot ("of" onto σοῦ). This never
reaches "renders as": `_head_word` returns None for an all-function gloss, so a function word never
becomes `english_head`, and every renders-as counter reads `english_head`. Logged as
`parse_abp.SPLIT_FUNCWORD_SLOT_CAVEAT`, beside `HEAD_WORD_TAIL_CAVEAT`.

**Scope boundary — this certifies `_split_compounds` ONLY.** The other redistribution passes in
`build_words_from_abp.py` — `_split_numbered`, `_redistribute_pronoun_compounds`, `_fix_backwards_pairing`,
`_split_pn_article_lump`, `_funcword_noun_relocate`, `_lord_subject_split`, `_lord_oath_fix` — are
**uncertified** and remain Session 1 invariant candidates. "The split is certified" must NOT inflate to
"redistribution is certified."

**Session 1 decision #1 = CLOSED.**

---

## Standing gates (invariant suite)

- **`scripts/lint_split_wrong_slot.py --control` must run GREEN** as a precondition of any future ABP
  re-ingest or any change to `_split_compounds`. Known-good verse = 0 flags; injected wrong recipient
  fires. It builds its own reference from source + bh_scrape, no committed fixture needed.
- **`scripts/size_split_compounds.py`** is the reconciliation partner: a split change that moves a
  different number of slots than the lint reports means the two harnesses disagree on scope — resolve
  before trusting any zero.

Both are READ-ONLY (open bible.db read-only; write only scratch TSVs). PA-only (need bh_scrape.db +
Rahlfs/TAGNT).

---

## Session log — control-test rule paid for itself

Four control failures during L9, each a real bug caught before a trusted zero:
1. Reference = split's own KJV lexicon → 4 false flags on a known-good verse (ABP renders words
   differently from KJV: ὀσμή "scent" not "savour"). Fix: reference = corpus's own renderings.
2. Hand-broken swap was a no-op ('him'↔'him'). Fix: inject a word onto a number that never renders it.
3. Frequency floor ≥3 condemned rare *spellings* of frequent words ('smelled', a tense fragment). Fix:
   collapse inflections into one rendering key (the ≥8 usage gate was already present — the diagnosis
   "gate missing" was wrong; the cause was tense fragmentation).
4. Recipient capture recorded only content recipients → 872 verses, Gen 27:27 (function-word recipient)
   vanished from the control set. Fix: count all recipients for reconciliation, audit the content subset.

Also surfaced (Session 0 deliverables, separate from L9): source-issues report, ingest pipeline
inventory, consumer blast-radius map, seeded known-defect ledger. See the Session 0 handoff report.
