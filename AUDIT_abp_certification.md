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

## Standing adjudication instrument (Session 5)

The **official ABP app** (apostolicbibleapp.com) — the living, authoritative Van der Pool text — is
the reference witness for ALL source-reading adjudications going forward. Neither of our stored feeds
(abp_texts, bh_scrape) is a check on the other when BOTH inherit the same upstream defect; the app is
the tie-breaker that carries ABP's own decimal-extended numbers (e.g. G241.2) that standard BibleHub
Strong's cannot. First use: L2 + L10 below closed from reconstruction to **source-attested
restoration**. L5 will go through the same door once its list is re-derived (Session 6).

## Ledger additions

### L2 + L10 — RESOLVED Session 5 (source-attested, restoration not reconstruction)
Both are the same class: the ABP source dropped a Strong's number, leaving a bare "G" the build turned
into reader-visible junk. Confirmed against the official ABP app and written to `abp_corrections`
(4 cells each — strongs / strongs_base / english / english_head; table 8 -> 16, invariant pin bumped
in the same commit). UNLIKE the Cushi/Jer seeds these were never hand-fixed on live, so the fix is a
two-step: `build_abp_corrections.py --apply` (adds the rows) THEN `apply_abp_corrections.py --apply`
(cleans the live cells).
- **L2 — 1Sa 6:11 pos 21:** `1473` -> `1475.3`, `G1473` -> `G1475`, `of their buttocks.G` -> `of their
  buttocks.`, head `buttocksg` -> `buttocks`. App: `1475.3-1473` (edron auton); corroborated 3x
  same-chapter (5:9 / 5:12 / 6:5).
- **L10 — Mal 3:6 pos 7:** the stray verb slot `(blank)`/`G` -> `241.2` / `G241`, english `G` ->
  blank, head `g` -> blank (verb elloiomai; ouk G3756 stays correct on pos 6). App: `241.2` — a
  decimal extension no standard-Strong's source could have supplied.

### L5 — DISCREPANCY RESOLVED Session 6 (closure a, recorded-in-error; NOT drift)
The "9 null-form this/these rows" reproduced EXACTLY — re-derived corpus-wide, 9 rows, one per
recorded verse. TWO recorded errors, both corrected:
1. The Session-5 "regen found 0" used a FORM-based detector (the τοῦτο `form GLOB`); a form-GLOB
   structurally cannot match a form-NULL row → 0 by construction.
2. The ledger meta-claim "recorded list was never committed" was ALSO wrong — the list sat in
   TODO.md line 55 (the S16 exception list) the whole time, 28 lines from the note that said no
   evidence existed. This is the MORE dangerous error: a ledger that says "no evidence exists"
   trains re-derivation instead of reconstruction. Caught only because we went looking anyway.

AUTHORITATIVE DEFINITION (saved verbatim — form-null demonstrative under the three mistag-candidate
numbers; form-null ALONE is common + benign, so the english + number scoping is load-bearing):
```
SELECT v.book, v.chapter, v.verse, w.position, w.strongs_base, w.english
FROM words w
JOIN verses v ON v.id = w.verse_id
LEFT JOIN abp_surface s ON s.verse_id = w.verse_id AND s.position = w.position
WHERE w.strongs_base IN ('G1473','G3779','G846')
  AND s.verse_id IS NULL
  AND (lower(w.english) LIKE '%this%' OR lower(w.english) LIKE '%these%')
ORDER BY v.id, w.position;
```
The 9 (each a CANDIDATE, not a confirmed mistag — αὐτός/ἐγώ can legitimately render "this/same";
needs ABP-app source eyes before any correction row): 2Ki 18:9 p9 · 2Ki 18:10 p12 · 2Ki 25:8 p9
(G846 "this is") · 1Ch 27:6 p0 · Ezr 7:6 p0 (G846 "This") · Dan 4:33 p1 · Eze 36:32 p4
(G1473 "this"/"I do this") · 1Co 1:24 p1 (G846 "to these") · Mat 3:15 p9 (G3779 "for to this").
NEXT: JP reads each vs apostolicbibleapp.com; real mistags → correction rows via the L2/L10 door.

**CLOSED CLEAN — the 3 G846 "this" candidates (Session 7, JP read vs apostolicbibleapp.com):**
2Ki 25:8 p9 · Ezr 7:6 p0 · 1Co 1:24 p1. The app shows the LEMMA **αὐτός** at every slot
(αυτός / αυτός / αυτοίς-δε) — NOT a demonstrative (οὗτος/ἐκεῖνος). αὐτός legitimately renders
"this / this is / to these" in intensive/anaphoric use, so G846 is the RIGHT number and the
rendering is clean. **Not mistags → no correction rows.** The app displays these under ABP's
own number **G1473** (ἐγώ's number); that is the SAME pronoun mis-numbering the certified Path C
fix corrected corpus-wide (αὐτός → G846, the dictionary-join-correct value per the strongs_base
invariant, CLAUDE.md). Our data holds the corrected G846; the app still shows ABP's pre-Path-C
1473. **Path C record (not asserted from memory):** memory `project_pronoun_fix_path_c` —
rebuilds #2–#7 (2026-06-03/05), source = Rahlfs LXX (OT) + STEPBible TAGNT (NT), live count
αὐτός/G846 24,781→25,304, app-confirmed each rebuild (e.g. Jer 50 "her" → αὐτός/G846). Expected +
explained, no action — the app naming the lemma αὐτός is itself the confirmation. **L5 candidates 9 → 6 remaining:**
2Ki 18:9 p9 · 2Ki 18:10 p12 · 1Ch 27:6 p0 · Dan 4:33 p1 · Eze 36:32 p4 (G1473) · Mat 3:15 p9 (G3779).
Defining read query (verbatim): the AUTHORITATIVE DEFINITION query above; per-verse context pulled
with `SELECT v.book||' '||v.chapter||':'||v.verse, w.position, w.strongs_base, w.english FROM words w
JOIN verses v ON v.id=w.verse_id WHERE (book,ch,verse) IN {2Ki 25:8, Ezr 7:6, 1Co 1:24} ORDER BY v.id, w.position`.

**BATCH TWO — the remaining 6 read (Session 7, JP verse-pasted the whole verse from apostolicbibleapp.com;
our-data pulled with the per-verse read above extended to the 5 books). 5 clean + 1 real mistag:**
- **2Ki 18:9 p9** — our G846; app lemma **αὐτός** "this is." Clean (αὐτός family, as batch one).
- **2Ki 18:10 p12** — our G846; app **αὐτός** "this is." Clean.
- **1Ch 27:6 p0** — our G846; app **αὐτός** "This." Clean.
- **Eze 36:32 p4** — our G1473; app **ἐγώ** (app "εγώ ποιώ" = "I do") → genuine first person, G1473 CORRECT. Clean.
- **Mat 3:15 p9** — our G3779; app **οὕτω(ς)** ("ούτω γαρ" = "for thus/so," rendered "for to this") → the adverb, not a demonstrative pronoun. G3779 correct. Clean.
- **Dan 4:33 p1 — REAL MISTAG (first Tier B candidate of Session 7).** Our data **G1473 (ἐγώ)**; app word
  is **αυτ-** ("αυτἡ," rendered "In this hour"), a feminine dative agreeing with ὥρᾳ. ἐγώ is IMPOSSIBLE
  ("I" has no feminine form), so G1473 is wrong. Correct number hinges on the breathing mark: smooth
  **αὐτῇ** = αὐτός → **G846**; rough **αὕτη** = οὗτος → **G3778**. The spelling starts αυτ- (not ταυτ-),
  and the construction "ἐν αὐτῇ τῇ ὥρᾳ / αὐτῇ τῇ ὥρᾳ" (= "in that very hour") is a stock LXX/Theodotion
  idiom → points to **αὐτῇ / G846**. PENDING: (a) JP confirms the breathing on the app (if unresolvable,
  the grammar argument above stands as the cited reading; a genuinely ambiguous glyph = "can't cite source"
  → row waits); (b) census — is this a lone stray or a Path C coverage gap? **First census query FAILED
  its own control** (returned EMPTY; `WHERE strongs_base='G1473' AND lemma='αὐτός'` MUST return Dan 4:33 p1
  or the detector is broken — it did not, so the stored lemma is null/inflected/accent-variant, likely the
  very reason Path C missed the slot). CONFIRMED by the full-row inspect (`SELECT w.* FROM words w JOIN
  verses v … WHERE Dan 4:33 position=1`): lemma **BLANK** (also morph/greek_pos/english_head blank);
  row = `english='this', strongs='1473', strongs_base='G1473'`, nothing else. So the row was NEVER
  anchored by Path C's alignment — Daniel 4 is an OG-vs-Theodotion divergence zone, so the ABP word
  likely had no matching Rahlfs word → no lemma → escaped as raw G1473. CENSUS VERDICT: the escaped
  class carries no Greek form AND no lemma in our data, so no our-data detector exists (lemma census is
  dead; an english-render census is too noisy — "her"↔"there" etc.). Within the L5 class (form-blank,
  "this/these") all 9 are read and Dan 4:33 is the LONE αὐτός mistag → a stray, not a visible cluster.
  Sizing the broader "did Path C leave a Daniel-4 gap" needs Path C's own flag file `pronoun_review.tsv`
  or an alignment re-run = **a Session-8 census, parked** (method noted, not forced). Dan 4:33 itself is
  isolated + confirmed → a Tier-B `abp_corrections` overlay (source mis-numbers αὐτῇ as ἐγώ's 1473;
  flip strongs/strongs_base to the αὐτός number), PENDING the breathing confirm to fix G846 vs G3778.

STANDING-RULE CANDIDATE (propose in Session 7 handoff): **any count that lands in a ledger or audit
doc carries its defining query verbatim.** Four unsaved ad-hoc probes this arc → four wrong claims
(37/39 prose · ×4/14 Greek · L5-regen · L5-provenance). Same earned promotion as verify-before-sizing.

### L10 — Mal 3:6 trailing bare "G" — SUPERSEDED (see "L2 + L10 — RESOLVED Session 5" above)
_Original find note, kept for the trail:_
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

**Class 1b VERDICT — CONFIRMED live-side drift (2026-07-04, source-line evidence, no code-run
needed).** Five of the 11 checked against the ABP source: every one is the parked-phrase shape
("For indeed IG1473 G3303 G1063" — English phrase in source order, then a run of numbers in
Greek order). The 2026-06-28 fronting fix makes the build order the spread words by the SOURCE
PHRASE ("For" then "indeed") — the scratch matches the printed ABP English exactly; live holds
the pre-fix Greek-slot order. Live's TAGS are correct (each word owns its number) — only display
order is stale, cosmetic severity, serving since June. Resolution: the next rebuild+swap fixes
live automatically; NO correction entry; the final harness run before a swap expects exactly
these 11 verses as residue (they vanish the moment live is replaced).

**Flip-fold ordering rules (item locked before the fold lands, like the em-dash constraint):**
`fix_split_flip` swaps POSITION values only — never english — so it cannot break the 237
patches' text preconditions; but `fix_split_merges` targets ABSOLUTE positions, so the flip fold
must run AFTER every pinned patch. It also compares words to verses.text, so it runs AFTER
fix_emdash (dash tokens agree). New tail order: … → fix_bracket_punct → fix_emdash (last
english-TEXT edit) → **fix_split_flip (last step, position-only)**. And `abp_corrections`
(Session 2) is keyed by position, so corrections apply AFTER split_flip — the true final step.
Standing invariant already exists: checklist step 6's `audit_split_flip = 0 MUST` gate — known
positive = THIS scratch (196 pairs); after the fold it must read 0 on every built copy.

**aiōn (L11) sanity check — the two verses SPLIT (JP's check caught it):**
- Jer 49:13 CONFIRMED: source prints "intoG1519 eon.G3588 G166" — English "eon" is the NOUN
  (αἰών G165); ABP printed the adjective's number. Live G165 = the certified reading.
  Correction entry: source_value G166 → corrected_value G165. Write it.
- Hab 3:6 RULED 2026-07-04 (live row inspected): pos19 = "eternal —" on the HILLS clause
  (βουνοὶ αἰώνιοι, adjective) — G166 is the honest tag; the June retag over-reached and live's
  165 is WRONG. Clincher: pos22, the same word "eternal" in the same verse, correctly kept 166.
  NOT a correction entry — live gets reverted to 166 (a one-cell live fix, or it self-heals at
  the next rebuild+swap; until then live serves a wrong dictionary link on that one word).
  The correction table nearly enshrined a defect as a correction — the entries-only-after-
  adjudication gate exists for exactly this.

**PRE-REGISTERED EXPECTATION for the final Session 2 harness run (exact, nothing else):**
residue = the 11 Class-1b live-stale verses ONLY (Hab 3:6 pos19 was hand-reverted to 166 on
live 2026-07-04, verified — both "eternal" slots now read 166, so it produces no delta).
Cushi + Jer 49:13 vanish behind the correction table; the 175 flip verses vanish behind the
tail fold. ANY other delta is a finding.

## Session 2b — flip fold + correction machinery LANDED (2026-07-04, code only, no db writes)

All local code, committed; every live-db step below waits on JP's runs + checkpoint go:
- **Flip fold DONE:** `fix_split_flip.py --apply` is now finish_rebuild.sh **step 6**, per the
  locked ordering (after all pinned patches + fix_emdash; before corrections). Convergence loop
  untouched. Ordering constraint documented in the script, the tail, AND fix_emdash.py (whose
  "must stay last" claim was corrected to "last english-TEXT edit").
- **Correction machinery DONE (Flag 2 honored — lands as one unit):**
  `scripts/build_abp_corrections.py` (creates the approved table + 7 seed entries: Cushi ×6 +
  Jer 49:13 L11; dry-run doubles as live validation — every entry should read "cell=corrected"
  on live) and `scripts/apply_abp_corrections.py` (guarded apply, finish_rebuild.sh **step 7**,
  the true final step: fires only on exact source_value match, LOUD skip otherwise, stdout +
  `<db>.corrections.log`, no-table = clean no-op so pre-table copies stay deploy-safe).
  **Control-tested both directions** on a throwaway mini-db (6 passes: no-op / dry-run classify /
  apply-fires / mismatch-untouched-loud / idempotent re-run / log written).
- **Harness wiring DONE:** `--no-corrections` attribution flag (env NO_CORRECTIONS=1 through the
  tail; --no-tail implies source-value expectations), the visible **"corrections reconciliation:
  N active, N verified, 0 mismatched — ok"** line (stdout + summary report), and a
  `correction-unapplied` hint tag on any delta at a correction cell.
- **Backup loudness guard DONE:** backup_db.py stamps `~/db_backups/last_success.txt` on a fully
  clean run; `cert_manifest.py verify` complains (warn-only) when the stamp is missing/older than
  25h. First nightly run after deploy writes the stamp — until then the missing-stamp warning is
  expected noise.
- **Node fixture tests:** verified ALREADY wired in both ci.yml and the pre-commit hook — the
  handoff item was stale; nothing to do.
- Deferred on purpose: `_sort_brackets` deletion (edits the build file between run 1 and the
  final run — do it after the final run passes, with the decommission).

**Checkpoint confirmations (JP's TSV paste, 2026-07-04):**
- **Cushi direction confirmed from evidence** (not CC's inference): all 6 rows read live=H3569 /
  scratch=H3570 → the correction is H3570→H3569, as shipped. The Session-2 handoff's
  "H3569→H3570" was live-vs-rebuilt phrasing, now settled from the delta TSV itself.
- **Jer 49:13 pos 28 is TWO cells, not one:** the June retag corrected BOTH `strongs_base`
  (G166→G165) AND the bare `strongs` (166→165). An 8th seed entry (field `strongs`) added —
  without it the final run would have carried one leftover Jer delta. Seed total: **8 entries**
  (Cushi ×6 + Jer ×2).
- **Schema "drift" ruled a non-event:** the shipped CREATE TABLE matches the Session-1 approved
  proposal above byte-for-byte (book/chapter/verse/position keying, `created`, the applied_at
  CHECK). The `verse_id`/`date` wording lived only in the Session-2 handoff's paraphrase.
  Recorded here so the handoff text doesn't read as an unapproved change later.
- **New pre-final-run check (cheap insurance):** JP's Hab 3:6 revert must have covered BOTH
  columns too — verify pos 19 + 22 read strongs='166' AND strongs_base='G166' before the final
  run, else Hab shows up as a residue delta.

## Session 2 FINAL RUN — PASS (2026-07-04) + decommission executed

**The final harness run matched the pre-registered expectation EXACTLY.** Report:
626,305 = 626,305 rows, 0 dropped/added. **corrections reconciliation (applied): 8 active,
8 verified, 0 mismatched — ok.** 110 cell deltas, ALL inside exactly the 11 pre-registered
Class-1b live-stale verses (11 verses × 2 swapped slots × their english/english_head/
strongs/strongs_base/morph/lemma columns; direction everywhere = scratch matches source
order, live stale — the run-1 verdict re-confirmed). Per-class: **flips 0** (the fold proved
itself; control test on the same scratch went 196 → tail → 0), **Cushi 0 + Jer 0** (the
table proved itself), **em-dash 0**, **Hab 3:6 0** (the two-column revert held). Zero
unexplained. Tier A ingest-faithfulness stands certified against the 74-file pin, with the
8-row Tier-B overlay applied and reconciled. The 11-verse residue self-heals at the
Session 3 rebuild+swap.

**Decommission EXECUTED (per the Session 1 reclassification):** 14 scripts moved to
`scripts/graveyard/` (kept, not deleted; per-script notes in `graveyard/README.md`):
- Build-folded twins, now proven redundant by the 0-unexplained run: fix_g1473_gloss ·
  fix_lord_subject · fix_funcword_subject · fix_lord_oath · fix_greek_pos_gaps ·
  fix_abp_numerals · fix_hab314_dupes (dedup_words STAYS in the tail as the safety net).
- Table-captured: fix_cushi_strongs (→ abp_corrections rows 'Class2-cushi').
- The six unclassified bracket/gap scripts ADJUDICATED DEAD: fix_bracket_gaps ·
  fix_bracket_gaps_absorb · fix_bracket_merge · fix_bracket_misplacements ·
  fix_multipos_gaps · fix_orphan_greek_pos — the final run had ZERO unexplained deltas,
  so nothing in live depends on a hidden manual edit from any of them; no new ledger lines.
- fix_article_noun_swaps was already deleted (pre-session).
STILL IN SERVICE (not graveyard): everything in the live build/tail path — the 7 pinned
patch scripts awaiting B→table migration (fix_subject_reorder, fix_mat25_37,
fix_supplied_attach, fix_theos_filler_tags, fix_split_merges, fix_kyrios_mistags,
fix_merge_misses), fix_idios_own, fix_bracket_punct, fix_emdash, fix_split_flip,
dedup_words, and the build modules (fill_blank_strongs, fix_pn_subject_merge,
fix_italic_heads). CLAUDE.md's script sections updated to match.

**Session 2 remaining fix list (in order):**
1. ~~Code-trace Class 1b~~ DONE — confirmed live-stale (above).
2. Fold `fix_split_flip.py` into finish_rebuild.sh AFTER fix_emdash (ordering rules above);
   re-run harness → expected residue = exactly 1b's 11 verses + Cushi 6 + aiōn (1 or 2 rows
   pending the Hab 3:6 ruling).
3. JP rules Hab 3:6 (query above); Jer 49:13 correction confirmed for the table.
4. Create `abp_corrections` (approved design) + entries for Cushi/L2/L5/L10/L11-as-ruled; wire
   the harness apply-before-diff (Flag 2) + `--no-corrections`; re-run → expected residue =
   ONLY the 11 live-stale verses, each pre-explained; zero unexplained.
5. Runnable invariant suite; delete dead `_sort_brackets`.
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

# Session 8 — Door 1: Path C divergence-zone pronoun residue, CENSUSED (2026-07-04)

### L12 — Path C pronoun residue (σύ/αὐτός/ὑμεῖς/ἡμεῖς still numbered G1473) — CLUSTER, MEASURED
**Scope question answered.** Dan 4:33 is NOT a lone stray. It is one of a large, source-attested
cluster: pronoun slots ABP's BibleHub source mis-numbered G1473 (ἐγώ) that Path C could not correct
because its Rahlfs aligner (a foreign text) can't reach the OG-vs-Theodotion divergence zones. The
known "accepted, safe, flagged" Path-C residual — now SIZED, and shown fixable from a source Path C
never used.

**Census surface (control-verified).** Path C's own flag file `pronoun_review.tsv` (written pre-
correction on the raw ABP base 1473, so every rebuild re-flags it — durable). Mandatory known-positive
control fired: `grep -P '^Dan 4:33\t' pronoun_review.tsv` → `Dan 4:33  In this  gap`. Detector sees the
defect on the reconstructed defective row, not by asking `abp_corrections` whether the fix landed.

**Better detector than the flag file — `abp_surface` (ABP's OWN printed Greek).** The Rahlfs alignment
reasons (`non-pron:3778` = "Rahlfs says οὗτος") are divergence-zone NOISE — an early 12-row οὗτος proof
batch collapsed: 8 of 12 verses had no live G1473 slot at all (the flagged english was a pre-split
gloss fragment), and the 4 that did were σου/μοι/αυτου, not οὗτος. `abp_surface` (same text as `words`,
so it aligns where Rahlfs doesn't) gives the correct number directly: σου→G4675, αυτου→G846, etc.
**This REFINES the Session-7 handoff claim "escaped rows carry no lemma → no our-data detector exists":
TRUE only for the blank-form slots (Dan 4:33 itself has a blank `abp_surface` form). Form-bearing slots
ARE detectable from our own data via `abp_surface`.**

**DANIEL count (solid — divergence zone, clean forms, σου/αυτου spot-verified):**
```
sqlite3 bible.db "SELECT CASE
    WHEN s.form GLOB 'αυτ*' THEN '1_autos->846'  WHEN s.form GLOB 'σ*' THEN '2_su->4675fam'
    WHEN s.form GLOB 'υμ*' THEN '3_humeis->5216' WHEN s.form GLOB 'ημ*' THEN '4_hemeis->2257'
    WHEN s.form GLOB 'εμ*' OR s.form GLOB 'μ*' THEN '5_ego 1st-sing CORRECT'
    WHEN s.form GLOB 'τ*' OR s.form GLOB 'εκειν*' THEN '6_article/ekeinos'
    ELSE '9_other:'||s.form END AS bucket, COUNT(*)
  FROM words w JOIN verses v ON v.id=w.verse_id
  JOIN abp_surface s ON s.verse_id=w.verse_id AND s.position=w.position
  WHERE v.book='Dan' AND w.strongs_base='G1473' AND s.form<>'' GROUP BY bucket ORDER BY bucket;"
```
→ αὐτός 97 · σύ 61 · ὑμεῖς 6 · ἡμεῖς 6 = **170 form-attested mistags** · ἐγώ(correct) 60 · article/ἐκεῖνος 7.
PLUS the blank-form residue (Dan 4:33's own kind — no `abp_surface` form, so `abp_surface` can't see it;
those stay source-app reads).

**CORPUS-WIDE count (same query, no book filter) — UPPER BOUND, contamination flagged:**
→ αὐτός 1779 · σύ 1212 · ὑμεῖς 297 · ἡμεῖς 289 = 3,577 pronoun-shaped rows · ἐγώ 1313.
**Do NOT carry this number into any Session-9 scope statement as a mistag count.** ROOT CAUSE INSPECTED
(5 cells: Num 20:9 + Num 31:42 `Μωυσής`, 1Sa 18:6 `Δαυίδ`, Gen 1:25 `αὐτῶν` — verb-subject Greek order
confirms each form sits on its OWN word): **the surface join is NOT misaligned — placement is reliable;
the defect is WORDS-SIDE numbering.** My earlier "abp_surface misaligns ~91%" read is RETRACTED. The
`9_other` names (`Δαυίδ`/`Μωυσής`/…) are SUBJECT-NAME slots whose english was folded onto the adjacent
VERB ("Moses took"/"David returned" ride the verb slot), leaving the name slot blank-english + numbered
1473 — a subject/possessive-fold artifact. So the 3,577 mixes ≥2 words-side classes: **(a) genuine
pronoun mistags** (a pronoun form on a 1473 slot → number should be 846/4675/…) and **(b) fold slots**
(blank english, pronoun/name form as a companion to a neighbor content word). Both overlap Door 3's
subject passes heavily. **PROPORTIONS UNKNOWN** — one non-random (lowest-id) sample per bucket can't
split them; the Session-9 per-slot pass produces the real split. Visible-defect discriminator =
HAS-ENGLISH (reader clicks "yours"/"him", gets 1473 — the misleading kind, Daniel-style) vs BLANK-ENGLISH
(fold companion, low-visibility); both are mis-numbered, only the first misleads a reader. **~91%
re-interpreted:** placement reliable ⇒ the missing ~9% is BLANK-FORM slots (Dan 4:33's kind), not
misplacement — which STRENGTHENS the fallback rule "form present → trust the form's number." (Corpus
paste was truncated mid-row at `όστρακα|1`.)

**DISPOSITION — Door 1 CLOSED as "cluster, measured."** No fix this session. The fix is a REBUILD, not
an `abp_corrections` batch (wrong tool at this volume — 170 in Daniel; corpus size UNKNOWN until the
detector is de-contaminated): give Path C an `abp_surface` fallback — where Rahlfs can't align, read the
number off the ABP form via a fixed form→Strong's table for the closed pronoun set (σου→4675, αυτου→846,
υμων→5216, ημων→2257, …), WITH a position-misalignment gate (skip any slot whose form isn't pronoun-
shaped; the name contamination is the control — and the misalignment ROOT must be understood first, see
below). Then rebuild. **= Session-9 doored item, HIGH seat, own checkpoint + throwaway-copy + pre-
registered diff. Batchable with Door 2 (import_tipnr) + Door 3 (7 reorder passes) — one PHYSICAL rebuild,
but THREE separately pre-registered diffs (Path-C fallback / import_tipnr / reorder-pass), each delta
attributable to exactly one fix; any delta that can't be cleanly attributed → fall back to sequential
rebuilds. ATTRIBUTION IS PER-COLUMN, NOT PER-ROW: a fold slot is changed by BOTH the Path-C number fix
(its `strongs`/`strongs_base`) AND a subject pass (its `english`), so the same row legitimately shows two
deltas from two fixes — pre-register by (row, column), or the overlap reads as unattributable.**

**INSPECTED (Session 8, 5 cells) — NOT misalignment, a fold class.** The name-on-1473 rows are
correctly-placed subject/possessive-fold slots (Num 20:9 + Num 31:42 `Μωυσής`, 1Sa 18:6 `Δαυίδ`,
Gen 1:25 `αὐτῶν`): the english folded onto the adjacent verb/noun, the slot left blank + numbered 1473.
`abp_surface` placement is RELIABLE. This IS Door-3 territory (the subject passes `_lord_subject_split`/
`_funcword_noun_relocate`), so the fold slots are a live seam to probe when Door 3 opens — the pronoun-
number fix and the subject passes touch the SAME slots (hence the per-column diff attribution above).

### Door 2 — `import_tipnr` twin bug FIXED, dry-run-proven (2026-07-04, commit 96bb662)
The header-first typing twin of the `entity_resolution` bug (`import_tipnr.parse_tipnr`) is fixed: an
entity's OWN col-8 type ({Place,Male,Female} — set IDENTICAL to `entity_resolution`, checked) beats the
block header; an unrecognized type inside a PERSON+PLACE block raises (same loud fail). Proven by
`scripts/dryrun_tipnr_typefix.py` (parse-only, NO DB) against a pinned INDEPENDENT expectation (a
line-scan, not the parser under test):
- **FLIP SET: expected 10 == actual 10, MATCH.** The 10 mixed-block places flip person→place —
  Beth-gader, Eshtemoa, Etam, Gedor, Gibeon, Ir-nahash, Keilah, Shechem, Tekoa, Zanoah (Judah-genealogy
  founder-towns TIPNR lists as both person and place).
- **MIRROR:** 0 flips outside a mixed block; 0 overrides that aren't person→place.
- **RAISE control both directions:** raises in a mixed block, does not in a single-PERSON block.
Doc count RESOLVED: the twin's mistyped set is **10** (TODO/handoff figure confirmed). `entity_resolution`'s
Session-6 "8" is a DIFFERENT parser with stricter skips — two legitimate counts, not a conflict.
**NOT APPLIED** — the `tipnr` re-import is the Session-9 rebuild's Door-2 step; its pre-registered delta =
exactly these 10 entities' type change (per-column, per the batching condition above).
