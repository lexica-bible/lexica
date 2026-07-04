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

---

# Session 1 — invariant enumeration + re-parse harness + correction-table proposal (2026-07-03)

**Deliverables landed this session:**
- **Invariant catalog** → `AUDIT_abp_invariants.md` (S1–S17 structural + P1–P21 per-pass, each with
  check sketch, known-positive control, tier, and status; existing gates folded in, accepted limits
  fenced off). Runnable suite = Session 2.
- **Feed-pin manifest tool** → `scripts/cert_manifest.py` (`build` refuses while L1-class lines exist;
  `verify` re-hashes all feeds vs `cert_manifest.json` and exits 1 on drift). Read-only except the
  manifest file. NOT YET RUN — waits on the L1 cleanup go (checkpoint Q1) and the manifest-schema OK (Q2).
- **Tier A re-parse harness** → `scripts/cert_reparse_harness.py`. Full production path (manifest
  verify → feed prechecks that ABORT on any silent skip → `build_words_from_abp.py` into `bible.db.new`
  → `finish_rebuild.sh` tail → row diff vs live via the production comparator `compare_words.load`,
  is_pn excluded, bracket-id rank-normalised). Reconciles every count against an independent
  measurement before trusting the diff (comparator size vs COUNT(*), partition arithmetic). Writes
  ONLY the scratch + `cert_report_summary.txt` + `cert_deltas.tsv`; never deletes anything; refuses to
  run over an existing `bible.db.new`. Running it to completion + adjudicating deltas = Session 2.
- **Pre-registered expected deltas** (the decommission-blocking list starts here, don't be surprised):
  (a) `fix_emdash.py` footprint — live has `—`, a fresh build has `--`; the harness hint-tags these
  `emdash`. (b) `fix_cushi_strongs.py` — 6 slots in 2Sa 18, live H3569 vs rebuilt H3570. Both scripts
  live OUTSIDE the build+tail path, which is exactly why they show up.

## Ledger additions

### L10 — Mal 3:6 trailing bare "G" — NEW (Tier B candidate, needs JP's source eyes)
The numberless-G census (invariant S2) fired 7× and reconciled: 5 = the known blank-"G." set the
build already fills; 1 = L2 (1Sa 6:11); **1 new = Mal 3:6**: source line ends
`I change not.G3756 G` — a bare "G" with no number, which the parser emits as a stray trailing
word. Same class as L2. Queued for the correction table alongside L2/L5 once JP recovers the
intended reading (BibleHub check, like L2). Control status: detector fired at both known positives
before the new find was trusted.

## Correction-table schema — PROPOSAL ONLY (checkpoint, no writes)

One row = one field-level correction to what a faithful parse produces:

```
CREATE TABLE abp_corrections (
    id              INTEGER PRIMARY KEY,
    book            TEXT NOT NULL,      -- ABP abbrev ('1Sa') — survives rebuilds
    chapter         INTEGER NOT NULL,
    verse           INTEGER NOT NULL,
    position        INTEGER NOT NULL,   -- words.position at authoring time
    field           TEXT NOT NULL,      -- words column ('strongs_base', 'english', …)
    source_value    TEXT,               -- what the faithful parse yields — PRECONDITION
    corrected_value TEXT,
    reason          TEXT NOT NULL,
    ledger_ref      TEXT,               -- 'L2', 'L5', 'L10'
    applied_at      TEXT NOT NULL CHECK (applied_at IN ('ingest','read')),
    status          TEXT NOT NULL DEFAULT 'active',   -- active | retired | superseded
    created         TEXT NOT NULL
);
```

Design calls (the mechanics, not the entries):
- **Keyed by (book, chapter, verse, position, field)** — book/ch/vs, not verse_id, so a correction
  reads meaningfully in a report and survives any verses-table surgery. Positions DO shift when the
  build changes (the fix_split_merges lesson), so **source_value is a hard precondition**: apply only
  when the target cell currently equals source_value; a non-match is a LOUD skip report, never a
  silent write. That converts position drift from silent corruption into a visible regraft task.
- **applied_at = 'ingest' recommended as the default.** Corrections run as the FINAL build step
  (after all passes, inside the scratch copy), so: the serving tier is untouched (no read-time
  overlay in every consumer per the Session 0 blast-radius map), the corrected value is visible to
  every audit/harness run, and the live DB equals source + parser + table. 'read' stays in the
  schema for a future case that genuinely can't wait for a rebuild.
- **Harness interaction:** corrections apply to the scratch AFTER parse, BEFORE diff — so a certified
  DB diffs zero and an unexplained delta can never hide behind the table. The harness gains a
  `--no-corrections` flag (Session 2) for attribution runs, mirroring `--no-tail`.
- **First queued entries (NOT written):** L2 (1Sa 6:11 blank-Strong's — number being recovered from
  BibleHub), L5 (9 null-form rows — needs JP's source eyes), L10 (Mal 3:6, above). The Cushi fix
  (6 rows) and the Cyrus/kyrios mistags (3) are prime migrations from script form.

**Checkpoint — ANSWERED by JP 2026-07-03, all four approved:**
1. **L1 cleanup: YES — DONE same day.** The 4 artifact lines deleted (diff verified = exactly
   those 4, census re-run = 0 non-verse lines across all 66 files).
2. **Manifest shape: YES.** `cert_manifest.json` at repo root, committed after the first PA run.
3. **Correction table: YES — rebuild-time (ingest-final), not read-time.** JP's reasoning matches
   the design note (read-time touches every serving consumer; audits would see uncorrected values).
   **Conditional on Flag 2 (JP clarified 2026-07-04, CC had misread it):** the re-parse harness
   MUST apply the correction table to the scratch BEFORE diffing against live — otherwise every
   corrected cell becomes a permanent false delta in every certification run once corrections
   exist. HARD Session 2 requirement: the `abp_corrections` build step and the harness's
   apply-corrections-then-diff wiring land TOGETHER (plus `--no-corrections` for attribution
   runs), never table-first.
4. **Keying + source_value precondition with loud skip: YES** — "the fix_split_merges lesson
   turned into mechanism."

**Rahlfs pin gap — CAUGHT BY JP on the first PA run (2026-07-04), FIXED same day.** The v1
manifest tool swept the Rahlfs folder's top level, which holds only SUBFOLDERS — it pinned 69
files (66 ABP + bh_scrape + 2 TAGNT) and ZERO Rahlfs files, with no floor to notice. Detector
that couldn't fail, again. Fix: the exact file list the build reads now lives as ONE constant in
`lxx_align.py` (`RAHLFS_FILES_REQUIRED` — strongs/morph/lexemes/versification, all four change
the built corpus if absent; + the optional surface file, pinned when present), the manifest
imports it, hard-errors if any required file is missing, enforces a ≥73-file floor, and prints a
per-feed count line. **The 2026-07-04 pin is INVALID — JP must re-pin** (`build` then `verify`;
expect 73–74 files with a Rahlfs count showing). Cheap now, poisonous after Session 2
adjudicated deltas against the wrong baseline.

**RE-PIN DONE (JP, PA, 2026-07-04): 74 files — ABP 66 · bh_scrape 1 · Rahlfs 5 (incl. the
optional surface file) · TAGNT 2; verify = intact. THIS is the cert baseline for Session 2.**

**Em-dash sequencing (JP: take it) — DONE 2026-07-03:** `fix_emdash.py` now takes a db argument
and runs as the very LAST step of `finish_rebuild.sh` (order is load-bearing:
split_merge_fixes.json carries a "--" precondition, "you think not --", that must match BEFORE
the swap). A rebuild now reproduces the em-dashes; the manual re-run step and the harness's
`emdash` expected-delta class are both gone. The harness's hint-tagger stays (a hit now means
the tail step regressed). Cushi stays a delta on purpose — it migrates to `abp_corrections`
in Session 2, where a manual data fix belongs.

## Rebuild-script reclassification (deliverable 5 — the decommission plan)

Home key: **A-folded** = already inside the build (standalone twin stays as audit/re-applier;
dies when the harness proves 0 unexplained deltas) · **A-foldable** = deterministic rule that
belongs in the build but still runs by hand · **B→table** = per-verse correction; migrates to
`abp_corrections` · **post-build overlay** = separate ingest from its own source; out of words-cert
scope but feed-pinned.

| Script | Home | Note |
|---|---|---|
| fix_bracket_punct | A-folded (+tail re-run) | twin re-run settles to 0 |
| fix_g1473_gloss | A-folded | |
| fix_lord_subject | A-folded | |
| fix_funcword_subject | A-folded | |
| fix_lord_oath | A-folded | |
| fix_greek_pos_gaps | A-folded | |
| fix_abp_numerals | A-folded | |
| fill_blank_strongs | A-folded (declared overlay over 5 Tier-B source slots) | |
| fix_pn_subject_merge | A-folded (post-insert) | |
| fix_italic_heads | A-folded (post-insert) | |
| fix_split_flip | A-folded (root fix) + one-time live cleanup done | |
| fix_hab314_dupes / dedup_words | A-folded (source fixed; dedup = 0-expect safety net) | |
| fix_emdash | **A-folded 2026-07-03** — now the LAST step of finish_rebuild.sh (must stay last: split_merge_fixes.json "--" precondition); manual re-run step + harness delta class both gone | |
| fix_idios_own | **A-foldable** — corpus-wide shape rule (adjective orphan the noun fold skips); candidate to join the folds | |
| fix_subject_reorder (20) | **B→table** | hand-listed per-verse rewrites |
| fix_mat25_37 (1) | **B→table** | |
| fix_supplied_attach (5) | **B→table** | |
| fix_theos_filler_tags (2) | **B→table** | |
| fix_kyrios_mistags (3) | **B→table** | source mistags (Cyrus) |
| fix_merge_misses (1) | **B→table** | |
| fix_split_merges (237) | **B→table** — THE priority migration: absolute-position patch whose silent-skip drift class the table's precondition mechanism is built for | |
| fix_cushi_strongs (6) | **B→table** | today it lapses on every rebuild until re-run by hand |
| import_tipnr | post-build overlay (TIPNR feed) — pin the TIPNR source file in a manifest v2 | |
| build_abp_surface / build_abp_translit / build_rendering_norm / build_two_ending / build_dotted_lexicon / build_word_gloss / build_entity_binding | post-build overlay — own tables, words-cert out of scope | |
| fix_bracket_gaps / fix_bracket_gaps_absorb / fix_bracket_merge / fix_bracket_misplacements / fix_multipos_gaps / fix_orphan_greek_pos / fix_subject_reorder predecessors | **status unknown — not in the live build/tail path.** Fits neither home until proven either superseded (delete) or a hidden manual edit whose live effect the harness will surface as a delta. Flagged per the frame; adjudicate in Session 2 with the delta report in hand | |
| fix_article_noun_swaps | retired/deleted (replaced by _fix_backwards_pairing) — no action | |

Also flagged: `_sort_brackets` in build_words_from_abp.py is dead code (defined, never called
since ee84aa0) — delete or mark it (invariant P21).

## Run doc — what JP runs on PA (in order, after the checkpoint answers)

```bash
# 0) DONE 2026-07-03 (L1 lines removed + pushed) — just pull on PA first (normal deploy or git pull)
# 1) pin the feeds (refuses if any artifact line remains):
cd ~/bible-db && python3 scripts/cert_manifest.py build
# 2) confirm the pin verifies:
python3 scripts/cert_manifest.py verify
# 3) (Session 2, ~a normal rebuild's runtime; safe: live db is read-only throughout)
python3 scripts/cert_reparse_harness.py
#    reports land in ~/bible-db/cert_report_summary.txt + cert_deltas.tsv
#    scratch stays at ~/bible-db/bible.db.new — delete after reading: rm ~/bible-db/bible.db.new
```

One read-only check worth running now (confirms L10's footprint in the live db):
```bash
sqlite3 ~/bible-db/bible.db "SELECT v.book, v.chapter, v.verse, w.position, w.english, w.strongs FROM words w JOIN verses v ON v.id=w.verse_id WHERE v.book='Mal' AND v.chapter=3 AND v.verse=6 ORDER BY w.position;"
```

# Session 2 — harness run + delta adjudication, first pass (2026-07-04)

**Harness ran to completion on PA.** live 626,305 = scratch 626,305, **zero rows added or
dropped** — the ingest path is row-faithful. 2,261 cell deltas = **413 distinct rows in 193
verses**, and the whole worklist collapses into three causes (reconciliation: 364 swap rows +
49 others = 413 ✓; 186 flip verses + 5 Cushi + 2 aiōn = 193 ✓):

**Class 1a — article/name order flips, 175 verses (196 pairs), the bulk.** Adjacent mirror-swaps
where LIVE reads correctly ("the Kenites") and the FRESH BUILD reads flipped ("Kenites the") —
158/158 directional on the 'the'-leading pairs, zero exceptions. CROSS-CONFIRMED by the
independent detector: `audit_split_flip.py` on the scratch flagged exactly these 175 verses,
a strict subset of the harness set (0 audit-only). Cause: the 2026-06-28 live cleanup fixed 283
flip verses in place, but the build-side root fix (source-order fronting in `_split_compounds`)
only covers THAT pass's flips — these 175 come from a second producer (mostly proper-noun/'*'
slots, which `_split_compounds` skips). Tier A build gap. **Fix: fold `fix_split_flip.py` into
the finish_rebuild.sh tail** (evidence-driven toward verses.text, loops to convergence, already
proven on live) — closes 1a exactly, since its detector shape IS this class.

**Class 1b — function-word pair swaps, 11 verses.** Same mirror-swap shape on μέν/γάρ
("indeed/For"), τε/γάρ, οὗτος/ὁ ("this/to"), ἐκεῖνος/ὁ, ὁ/μηδείς — OUTSIDE audit_split_flip's
determiner+noun scope by design (that's the whole 175-vs-186 gap, fully enumerated). Direction
is REVERSED vs 1a: scratch has the natural source-English order, live has the stale one.
Working hypothesis (NOT yet verified — needs a code-trace): the `_split_compounds`
source-order-fronting fix changed these pairs' output after live's last full rebuild; the live
in-place cleanup skipped them (wrong shape for its detector). If confirmed: scratch is RIGHT,
live is stale — no build change needed, the class dissolves at the next swap. Verse list:
1Co 5:3, 1Co 12:8, 1Ki 12:9, Ezr 6:8, Heb 2:11, Heb 7:21, Jdg 8:5, Job 21:6, Psa 81:14,
Rom 3:2, Rom 5:16.

**Class 2 — Cushi, 6 rows (2Sa 18).** Pre-registered, located exactly (strongs_base only,
H3569 live vs H3570 rebuilt). → correction-table entry #1.

**Class 3 — the aiōn retag, 2 rows (Hab 3:6 pos19, Jer 49:13 pos28).** Live G165, rebuilt
G166 — the old hand-applied retag, never folded. → correction-table entry #2 + new ledger
line **L11**.

Em-dash class: ABSENT from the deltas — the tail fold worked (fix_emdash swapped 2,591 cells
inside the scratch build; zero survived to the diff).

**Session 2 remaining fix list (in order):**
1. Code-trace Class 1b to confirm the fronting-fix story (single-verse test build on Rom 3:2).
2. Fold `fix_split_flip.py` into finish_rebuild.sh (before the em-dash step); re-run harness →
   expected residue = exactly 1b (if confirmed stale-live) + Cushi 6 + aiōn 2.
3. Create `abp_corrections` (approved design) + entries for Cushi/L2/L5/L10/L11; wire the
   harness apply-before-diff (Flag 2) + `--no-corrections`; re-run → expected ZERO unexplained.
4. Runnable invariant suite; delete dead `_sort_brackets`.
Scratch bible.db.new stays on PA until adjudication closes (it's the evidence base).

## Recommended Session 2 scope
1. Run the harness to completion on PA; adjudicate every delta into: build-reproducible (0 action),
   pre-registered script footprint (emdash/cushi), correction-table candidate, or genuine Tier A bug.
2. Wire the QUERY/SWEEP invariants from the catalog into one runnable suite
   (`scripts/cert_invariants.py`), each with its control test, both directions.
3. On JP's checkpoint answers: create `abp_corrections`, migrate the B→table scripts (starting with
   fix_split_merges + fix_cushi_strongs), add `--no-corrections` to the harness, re-run, and retire
   the first decommissioned scripts.
4. Small cleanups: delete `_sort_brackets`; fold `fix_emdash` (kills its delta class before the
   Session 2 harness run if done first).
