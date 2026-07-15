# TODO

Open work only. Finished and scrapped items (with the gory details) are in [TODO_ARCHIVE.md](TODO_ARCHIVE.md).
Each item may end with a small `code:` pointer for Claude to find the right spot — you can skip those lines.

Consolidated 2026-07-01: the DONE/SHIPPED write-ups were moved to the archive + memory; this file now
holds genuinely-open work and parked ideas only.

---

## ABP corpus certification audit — TIER A CERTIFIED END TO END (full record `AUDIT_abp_certification.md` + memory `project_abp_certification`)
Sessions 1-3 DONE 2026-07-03/04. Live bible.db IS pinned source (74-file hash manifest) + faithful parser
(re-parse+diff certified) + versioned correction table (`abp_corrections`, 18 rows) + invariant suite green
(`cert_invariants.py`, 7/7, each with a proof-of-fire control). Session 3 rebuilt+swapped live (old file
retained `bible_pre_certswap_20260704.db`), erasing the 11-verse residue; dead `_sort_brackets` deleted.
Session 4 DONE: Cushi person-as-place binding floored (see archive), check 7 added, render count reconciled.
Session 5 DONE: TIPNR pinned (manifest 75, binder proven byte-identical); nightly backup damage-check +
durable self-test; L2/L10 correction rows landed (source-attested via the official ABP app, table 8->16,
suite green at pin 16); two-source seam doc written (`AUDIT_entity_seam.md`).
Session 6 DONE 2026-07-04: 97-card section-label defect FIXED + live (`parse_tipnr` types each entity from
its OWN row, not the block header — 8 places flipped person→place, 3 EXCLUDED entities stopped binding,
net −13 render, loud-fail raise on unknown type under a mixed header); mirror census re-run on clean labels
(P1=0, valid); check 7 hardened to BOTH directions (mirror leg + control); L5 discrepancy explained
(closure a, no drift). Cert 7/7 green, pin 16. Full record `AUDIT_entity_seam.md` + `HANDOFF_session7.md`.
Session 7 DONE 2026-07-04: **L5 CLOSED** — all 9 candidates read vs the ABP app (JP verse-pasted): 8 clean
(αὐτός/ἐγώ/οὕτως legitimately render "this/these"), 1 real mistag fixed — Dan 4:33 pos 1 αὐτῇ (αὐτός)
mis-numbered as ἐγώ, corrected G1473→G846 (decided by dative agreement with ὥρᾳ + αυτ- spelling, not a
breathing eyeball; escaped Path C = blank-lemma unanchored, Daniel-4 OG/Theod. divergence). Two `abp_corrections`
rows added via the L2/L10 door (table 16→18), applied live, **pin bumped 16→18, cert 7/7 green**. Luke 23:38
carry-forward closed (language reference = binder artifact, no row). Full record in `AUDIT_abp_certification.md`
L5 batch-two entry.
Carry-forwards:
**Session 8 DONE 2026-07-04: Door 1 (Path-C census) CLOSED + Door 2 (import_tipnr twin) FIXED+proven.
Both queued for one Session-9 rebuild. Full charter = `CHARTER_cert_session9.md`
(consolidates the old `HANDOFF_cert_session9.md` + `AUDIT_reassembly_rebuild.md`, both now superseded).**
**PRE-REBUILD FIXES COMMITTED 2026-07-05: (P) gated green (ddffb0f); (b) dry-run-proven (96bb662);
(e) paren float shipped (6e1deed); (f) content-other parser (b62ab8f) + 5 Tier B rows staged
(`AUDIT_tierB_f_proposed.json`); (g) DEFERRED, detector floor 671 in gate (a76df6a). SESSION 9 PROPER
opens as its OWN fresh session: first step = assemble the combined-rebuild plan → JP approves → build.**

**★ SESSION 9 (2026-07-06) — rebuild ran, BLOCKED at the gate by split-flip over-fire. SUPERSEDED — S10 fixed it in code, S11 ran + swapped (see "SESSION 11 DONE" below). Kept only for the diagnosis history. ★**
The plan was approved and the combined rebuild built + finalized on a throwaway `bible.db.new` (live
never touched). **P1/P2/(e)/(f)/(b) all verified GREEN:** P1 drove the 208 pronoun survivors to ZERO,
content-other = 0, funcword detector trusted-zero (fired 0→93 on a pass-off build, then 0 on the real
one), invariants + audits + health all pass, five pass-controls frozen (1Ch 13:10 / Act 19:4 / 1Sa 5:2
/ Jdg 8:19 oath / Lev 10:18 funcword). **(f) shipped a NEW prose path on `abp_corrections`** (committed
b196b9a): `field='verses.text'`, `position=-1` sentinel, two apply points in finish_rebuild (prose at
step 4b before split-flip, words at step 7); `verify_prose_leak.py` is the gate check;
`cert_prose_leak_diff.json` grew 13→15 (2 live-stale caps heals, Tier A).
**BLOCKER — v2 word-order = 180, not 0.** Root cause proven: **`fix_split_flip` over-fires** — it
swaps "noun, the" → "the noun" even when the "the" belongs to the FOLLOWING noun (Jer 48:1: "…of the
forces, the God…" → wrongly "…the forces, God"). Rebuild with split-flip OFF → word-order **180→5**
(175 caused by split-flip; the 5 residual = Mat 21:19 / Mat 20:29 / Job 24:19 / 1Ch 22:15 — 4 of the
5 Tier B verses whose WORDS still need a fix — PLUS Act 7:3, a separate case never in Tier B; Job 24:18
is NOT residual, its words reassemble clean). `audit_split_flip` reads 0 because it shares the fixer's own flawed assumption; the independent
v2 oracle caught it. The charter's "a clean rebuild cures the article-fronting for free" was WRONG —
that diagnosis ran on a no-tail build. punct = 240 with AND without split-flip (split-flip is
punct-neutral; 240-vs-260 is a separate open item).
**★★ SESSION 10 DONE 2026-07-06 — the S9 blocker + the 5 residual RESOLVED IN CODE (5 commits); SHIPPED via
the S11 rebuild below.** Canonical = `CHARTER_cert_session9.md`.
- `49f09c6` split-flip SCOPED (two clean-text guards) + `audit_split_flip --control`; pre-registered to fire
  on **0** in the rebuild (all 175 were false positives) — if it fires on any, STOP + adjudicate.
- `7fe9271` Option A malformed-bracket build fix (Mat 21:19 / 1Ch 22:15 / Job 24:19); `scan_malformed_
  brackets.py` pre-registers EXACTLY 3; control green.
- `a011695` Fix A number-safe correction comparator (`cellmatch`) — needed by greek_pos rows; 18 live rows
  re-verify identically (dry-run 0 skips).
- `0ce6f06` Mat 20:29 word row (greek_pos 1→2); `9eff6da` Act 7:3 word rows (option B, reorder metadata).
**★★ SESSION 11 DONE 2026-07-06 — REBUILT + GATED + SWAPPED + CERTIFIED LIVE. ★★** The combined rebuild
ran, passed every charter gate line by its own instrument, swapped to live, re-certified 7/7, dependent
builders re-run, site reloaded. `abp_corrections` 28, words 626309, phrase-gloss allowlist 31 frozen
(`AUDIT_phrase_gloss_allowlist.txt`), punct settled at 240 (no new). Carry-forwards (Path-C residue,
import_tipnr twin, Door-3 five-pass controls) all shipped in this rebuild. Rollback = `bible_pre_cert_
s11_20260706.db`; old live = `bible_old_live_20260706.db`. Full record → memory `project_abp_certification`
(S11 banner + lessons). **The certification arc is CLOSED.**

**S11 FOLLOW-UPS — 4 of 6 CLOSED (verified 2026-07-08, see archive): `--from-draw` shipped (`c4617d0`),
G1096 redraw shipped at batch-2 open, citation-sweep rule codified in `docs/claude/ai.md`, stray worktree
pruned. Still open:**
- **`verify_prose_leak.py` needs a "Tier B applied" mode/warning** — it's a parser-only check; run against a
  finished scratch (Tier B layered on the 5 prose verses) it FAILs-that-isn't on exactly those 5. Next
  rebuild shouldn't re-derive this.
- **`lint_split_wrong_slot.py` stale label** — its `RECONCILE … (sizing: 18,339/12,692)` is a hardcoded
  literal; bump to **18,384/12,718** (the real post-S11 scope; both harnesses agree on it).
Carry-forwards (all three = ONE Session-9 HIGH-seat rebuild; three per-column-attributed diffs):
- **Path-C G1473 residue — CENSUSED + CLOSED (Session 8, ledger L12).** Dan 4:33 is NOT a lone stray:
  Daniel holds **170** source-attested pronoun mistags (αὐτός/σύ/ὑμεῖς/ἡμεῖς still numbered 1473), read off
  `abp_surface` (ABP's own Greek — refines the old "no our-data detector" claim to BLANK-form slots only).
  Corpus-wide raw ~3,577 is **VOID as a count** — a MIX of real pronoun mistags + subject/possessive FOLD
  slots (blank-english, correctly-placed but mis-numbered; NOT `abp_surface` misalignment — placement is
  RELIABLE), proportions unknown until the per-slot fix pass.
  → FIX QUEUED (Session 9): Path C `abp_surface` fallback (form→Strong's table for the closed pronoun set)
  WITH a per-slot form/english sanity gate (skip+log where they don't match; blank-form slots stay app reads).
- **import_tipnr.py twin bug — FIXED + dry-run-proven (Session 8, commit 96bb662), NOT yet applied.**
  Ported entity_resolution's col-8-own-type fix into `import_tipnr.parse_tipnr`; the **10** mixed-block
  places (Beth-gader/Eshtemoa/Etam/Gedor/Gibeon/Ir-nahash/Keilah/Shechem/Tekoa/Zanoah) flip person→place,
  independently pinned + mirror-clean + raise both ways (`scripts/dryrun_tipnr_typefix.py`). The `tipnr`
  re-import is the Session-9 rebuild step; pre-registered Door-2 delta = exactly those 10 type changes.
- **Door 3 — the 7 redistribution passes — RESOLVED 2026-07-05 (middle path).** L9 certified
  `_split_compounds`; (P) now certifies P1 `_redistribute_pronoun_compounds` + P2 `_split_numbered` via their
  gates. The OTHER 5 (`_fix_backwards_pairing`, `_split_pn_article_lump`, `_funcword_noun_relocate`,
  `_lord_subject_split`, `_lord_oath_fix`) get NO full per-pass cert but ONE banked known-positive control each
  + the output-level v1/v2-zero gate. Banked: 1Ch 13:10 (lord_subject), Act 19:4 (pn_article_lump), 1Sa 5:2
  (backwards_pairing). **STILL TO PICK ON PA before the build:** one control verse each for `_lord_oath_fix`
  (from `graveyard/fix_lord_oath.py` dry-run) + `_funcword_noun_relocate` (from `audit_funcword_wrongslot.py`).
  See CHARTER gate block "Five-pass single-control set".
- **POST-S9 follow-ups (surfaced this session, NOT part of the rebuild):**
  - Phrase-gloss under-distribution (671, fix (g) deferred): adjudicate a sample of the "not+verb" class vs
    the ABP app (defect vs ABP negation convention), then distribute the true-defect ones dual-ordering-style.
    Detector = `scripts/audit_phrase_gloss_underdist.py`.
  - Consolidate the trailing-clause float set — it's copy-pasted in 6 live places (build + 4 render + port);
    unify to one shared definition so they can't drift. Repo hygiene.
- **Stump filter leak** (noted, low priority): `lint_split_wrong_slot.py`'s stemmer stump filter misses
  sibling forms whose count is <3 (sid/com/rott). Didn't matter once recipient-scoping shrank the haystack;
  fix if the filter is reused at scale.

## Open word-study / data issues (low priority, none gating)
- **Jacob-class name cards (sized 2026-07-11): 694 occurrences (~2% of 32,002 name words) are
  unbound + ambiguous-name → AI-only fallback card** (found via Ἰακώβ Gen 29:32: several people
  share the name, the name-lookup rightly declines to guess, no verse-bind exists to break the tie,
  reader gets the unverified AI blurb with no genealogy). Low volume but high-visibility names:
  gilead 38, jesus 38, hadad 30, judah 26, jehoram 21, jacob 17, mary 16, elijah 15, joseph 12,
  saul 10 (full top-20 in the audit output). Coverage otherwise healthy: 15,893/32,002 bound.
  Fix direction when picked up: extend the binder's verse-corroboration for these names (why did
  Gen 29:32 Jacob floor? — the patriarch is TIPNR's Israel@Gen.25.26-Rev record, alias-keyed), or
  a hand-ruled disambiguation list for the famous few. Sizing tool (read-only, control-tested):
  `scripts/audit_pn_fallback_size.py`. code: build_entity_binding.py tiers; 30-detail-panel.jsx
  metav effect (the ambiguous-name decline is CORRECT — don't "fix" it by guessing).
- **Eponym card, per-verse sharpening (banked candidate — JP option (b), 2026-07-11).** Shipped fix
  (81930ee) = static both-senses opener on the 14 tribal-founder person cards (Judah, Israel, the 12
  sons + Ephraim/Manasseh), patriarch bio under a "The man" break — never wrong, never sharp. Banked
  upgrade: per-occurrence sense from a rulings-style pattern list on the neighboring words ("king of",
  "land of", "cities of", "tribe of" → territorial), so the card can lead "Kingdom of Judah — named
  for Judah, son of Jacob" on territorial verses. NOT fuzzy guessing — explicit pattern list, JP-ruled.
  Background: TIPNR deliberately folds tribe/kingdom refs into the founder entity (its place entity
  H3063N covers only "Judea"-style refs, ~2 OT verses); binding is faithful, this is presentation only.
  Sub-candidate (JP 2026-07-11): person-vs-territory occurrence TALLY for H3063/H3478 so the
  Israel/Judah "most later mentions" quantifier becomes a counted fact ("most" ruled KEPT meanwhile —
  Genesis-confined man vs kingdom-dominated Kings/Chronicles/Jeremiah; "often" would misinform).
  code: static/src/30-detail-panel.jsx EPONYM_LINES.
- **Helper-word double-tag class (periphrastic verb renderings)** (logged 2026-07-09, batch-3
  session 3, found via Jud 1:9 during G2008 ἐπιτιμάω). ABP two-word verb renderings like
  "May … reproach" store as TWO word rows both carrying the same Strong's — verified Jud 1:9
  (rows 556002 "May" + 556003 "reproach", both 2008). Sized read-only: **731 adjacent same-tag
  pairs** where the first word is may/shall/will/did/do/does/let. Effects: inflates occurrence
  counts (Jud 1:9 read as a double; real table = 37 verses / 38 occ, single true double Zec 3:2),
  and the helper word can surface as a phantom "rendering" in word-study/dictionary feeds.
  **DECIDING QUESTION ANSWERED (JP, eSword + ABP app, 2026-07-09): BUILD ARTIFACT.** eSword tags
  only "reproach" (`May [2reproachG2008` — "May" bare); the ABP app shows "May [2reproach" as ONE
  chunk under the single Greek word επιτιμήσαι. Our splitter broke the chunk into two rows and both
  inherited the tag. Fix = build-rule (splitter family, cf. af8e296), folds into the next words
  rebuild per the settled build-folded-fixes pattern; NOT a live-table patch, NOT mid-calibration.
  Sizing query in the batch-3 session-3 log context; dictionary-side guard = any
  renderings claim for an affected word is checked against real occurrences (G2008 watch banked).
  **SECOND EXHIBIT (same session, inverse shape): Rth 2:16** — "you shall not reproach" sits
  entirely on the NEGATION row (pos 14, tagged 3756 οὐκ) and the verb row is BLANK (pos 15,
  tagged 2008). Jud 1:9 = tag duplicated onto the helper; Rth 2:16 = English assigned wholly to
  the first word of a two-word span. One root: the splitter's handling of multi-word English
  spanning two Greek words. The 731-pair sweep catches the Jud shape only; the Rth shape needs
  its own sweep (blank-English rows whose PRECEDING row's English ends in a verb-phrase — or
  simply: blank-tagged rows adjacent to a multi-word chunk). Both shapes, one build-rule fix.
  **THIRD EXHIBIT (same session): Job 18:13** — "And may" + "be devoured" both tagged 977 (Jud-1:9
  shape). G977 occ table corrected to 39 uses / 37 verses (Isa 51:8 the sole true double — verified
  two genuine content renderings). **DETECTION HEURISTIC (reviewer, banked): the dictionary card's
  own gloss notes have now defused this defect class twice unprompted** (G2008 + G977 both grew a
  "may = optative grammar, not a rendering" bullet) — a gloss-note bullet flagging a bare helper
  word as a "rendering" is a free per-word detector for this ticket; grep shipped cards' gloss
  notes for helper-word bullets when the fix window opens.
  **DOWNSTREAM SURFACES (reviewer, G977 render):** the "ABP RENDERS AS" chips and the search-result
  word highlighting read straight from the words table, so they show the double-tag too ("may 1"
  chip; Job 18:13 highlights both words). Fix acceptance check must include "no helper-word chips"
  on the three exhibit words (Jud 1:9, Rth 2:16, Job 18:13), not just corrected word rows.
  **ESCALATED 2026-07-09 (JP): fix NOW in a dedicated session, not a maintenance window —
  calibration paused behind it. Charter with no-write gate + acceptance checks:
  `CHARTER_splitter_fix.md`.**
  **POLARITY A FIXED + LIVE 2026-07-09 (splitter-fix session; charter CLOSED).** 607 helper rows
  untagged (tag blanked, English kept as plain text) via `fix_helper_double_tag.py` against the
  pinned `splitter_a_expected.tsv` — a list proven by TWO independent derivations (stored table
  vs raw ABP source) diffing EMPTY under one shared screen (`helper_ok`, now IN the builder as
  `_strip_helper_double_tag`, locked by `tests/test_helper_double_tag.py` in CI + pre-commit).
  All acceptance checks passed: exhibit rows/renders clean (no helper chips, no PN mislabel),
  G2008 38 occ/37 verses + G977 39/38 (charter's "37" for G977 was a drafting miscount — see
  charter correction note), invariants green, both stale gloss bullets deleted via fix_lexica_raw.
  361 structural matches correctly LEFT ALONE (legit doubles + split renderings, the A-review
  pile). Full record: AUDIT_lexica_rollout.md splitter-fix entry.
- **Splitter polarity B — English-pooled-on-function-word rows (follow-up ticket, hand-review
  only)** (filed 2026-07-09 from the splitter-fix session, reviewer Ruling 8). The Rth 2:16 shape:
  a multi-word English phrase parked on a FUNCTION word's row while the adjacent content word's
  row sits blank. **878-case evidence list frozen in `scripts/splitter_b_evidence.txt`** (finder:
  `audit_helper_double_tag.py`, polarity-B block). Dominant shape = "did/shall not X" pooled on
  the negation with the verb row blank (e.g. Gen 11:6, 2Ki 17:35, 1Ch 22:8). Own dry-run gate;
  every case individually adjudicated before its patch line is written — no batch approval.
  Session notes for the next discriminator: (1) **named specimen Job 18:13 pos 3–4** — "the soles
  of his" pooled on the PRONOUN row (G846), noun row (G2831.2) blank: pronoun hosts widen B beyond
  negations, and it makes Job 18:13 the both-polarities-in-one-verse precedent (its A-half is
  fixed, this half inherited); (2) **tail-position gap**: the current B screen matches the pooled
  phrase's LAST word against the blank word's known renderings — misses pronoun-host cases where
  the content word sits mid-phrase ("the soles **of his**"); (3) **Zec 3:2 negative control**:
  pooled multi-word English on a CONTENT word's own row ("May the LORD reproach"|2008) is
  legitimate — only function-word hosts with an adjacent blank content row are B; (4) fix lands as
  a hand-verified re-runnable patch in the rebuild path (split_merge_fixes precedent), NOT in the
  auto-splitter.
- **Place-map pin = interim plurality heuristic** (2026-07-05). The map on a place word card
  (`_pin_from_rows` in views_metav.py) picks the coordinate the MOST metav_places rows agree on when a
  name carries several referents (Lebanon = region + Mount Hermon + a Jerusalem structure). Safe direction:
  a wrong pin needs multiple rows agreeing on the wrong point; failure mode is no-pin, never a misplaced
  pin (Eden still declines). BUT it leans on coincidental exact-coordinate duplication — a name whose
  referents are all distinct points gets no pin forever, even though the bound TIPNR entity
  (`Lebanon@Deu.1.7`) already says which referent the verse means. Real fix = an entity-level join: TIPNR
  entity → the matching metav_places row, or OpenBibleInfo coordinates (per-referent IDs native). Folds
  into the queued MetaV↔TIPNR cross-link work (same join problem as the person panels, places edition).
  memory `project_metav_expansion` / `project_entity_resolution_rebuild`.
- **OpenBibleInfo place ingest — the real fix for bound-place maps** (logged 2026-07-05, not started).
  The entity→coordinate join (E) was PARKED because `metav_places` has no per-referent key: name+root
  can auto-link only the single-referent places. The place-link dry-run (`scripts/build_tipnr_metav_link.py`,
  read-only) proved it — of 361 place entities: 241 confident (187 unique-name / 42 by-area / 12
  coord-agree), **86 HAND-RESOLVE** (genuinely different places at different coords — Bethel, Aphek, Ramah;
  these are what users notice). Hand-curating 86 ancient sites risks a wrong pin (breaks the accuracy bar).
  **2026-07-05 — a cheaper fix than OpenBibleInfo surfaced.** The old blocker ("metav has no per-referent
  verse key") was WRONG: MetaV's `MainIndex.csv` (unloaded) tags every word with PlaceID + verse, so the
  same distill that built the PERSON link (see below) gives place→verse + place→Strong's — a MetaV-native
  per-referent key that likely solves the 86 with NO new external source and NO new licensing. **Try the
  MainIndex place distill FIRST;** fall back to ingesting **OpenBibleInfo** (openbible.info/geo, per-referent
  IDs + refs + confidence + coords; `/credits` licensing check BEFORE ingest) only if the MetaV key comes up
  short. Either shares the `tipnr_metav_link` table (kind='place'). Nothing is wrong today — the interim Eden
  guard keeps the 86 SAFE, they just decline the map. memory `project_metav_person_link` /
  `project_metav_expansion` / `project_entity_resolution_rebuild`.
- **MetaV person rich-card serving — DONE + LIVE 2026-07-05** (moved to TODO_ARCHIVE). Left three parked
  follow-ups below.
- **Nave's retirement (DECIDED, scoped; own task, after S9).** Remove Nave's: study.db name-topic data +
  the name-path sidebar section (`naveTopical` + `/api/study/for-name` wiring) + the `/credits` line if
  listed. Rationale: tradition-provenance topical curation (interpretive verdicts as headings); finding-aid
  superseded by corpus occurrence links; interpretive claims belong in argument graphs where labeled +
  stress-tested. **Topic-page ROUTE survival is a SEPARATE decision — don't delete the route reflexively.**
  memory `project_metav_person_link` + `project_study_modules`.
- **BSB entity-resolution coverage (own task/review — wrong-identity risk class).** Ephraimites/Num 2:18
  (BSB `bene-X` "sons of X" construct) reached only the H1121 (`ben`) dictionary card. First step: test
  Levites Neh 11:3 on BSB — fires People/Clan = binding is cross-translation, gap is the construct-phrase
  class (maybe kin to Psa 39:1 phrase-gloss, S9 charter); doesn't fire = entity cards ABP-only today,
  document + scope from there. memory `project_metav_person_link` / `project_entity_resolution_rebuild`.
- **Dan 1:6 trio — hand-resolve the alias-record residual.** Azariah/Hananiah/Mishael @Dan.1.6 all score
  0.00 (below_floor) because MetaV tags their Daniel verses to the Babylonian-name alias records (Shadrach/
  Meshach/Abednego), not the Hebrew-name records — a known-SAFE residual, not ambiguity. Diagnosis + hand-
  resolve steps are in `HANDOFF_metav_person_link.md`; pick the person_id + write it into the residual notes.
- **Badge / verification-token unification (design backlog).** Two families — provenance badges (metaV/
  TIPNR/"Matched to this verse") vs verification marks ("✓ N/N verified"); rule now in `docs/design.md`.
  Converge instances opportunistically, no sweep.
- **Phase-6: PN Greek surface-form backfill for interlinear mode** (deferred, not a bug). In the new
  interlinear reading mode (2026-07-04) proper nouns show their capitalized English name on the Greek line
  because ABP prints Φαραώ/Νεχαώ etc. but those forms were never ingested (no lexicon join for `*` PNs → no
  `abp_surface` row). Backfill `abp_surface.form` for PN tokens so the Greek line shows the real Greek; it
  slots into the `greekLineForWord` chain at step 1 (inflected) with ZERO UI change. Needs cert-style
  position-alignment verification when it runs. Full record: memory `project_reading_modes`.
- **~48 G1473 (ἐγώ) cells reading 3rd-person reflexives** ("himself/themselves/itself") with a blank
  lemma — by-design skips of the cautious G1473→G846 retag (it refuses to guess reflexives + no-morph
  cells). Consistent with the build. Future cleanup only. code: the g1473_gloss_retag fold in
  build_words_from_abp.py / lxx_align.
- **τοῦτο-paradigm mistags** — demonstrative forms wrongly tagged; the real number is G3778 (~3,401 rows).
  **ENUMERATED + CONFIRMED 2026-07-03 (read-only), retag still PARKED** — nothing in a definition batch
  depends on it (G846/G3778 are structural cards, not `lexica_def`). The **15 confirmed strays** (all
  τ-initial forms, unambiguous — certified by control `SELECT count(*) … G3778 AND form GLOB 'τούτ*'/'ταύτ*'`
  = 3401):
  - G1473 (11): Deu 6:25, Ezr 9:14, Hag 2:18, Eze 45:16, Jer 7:1, Jer 8:12, Jer 11:3, Jer 33:4, Jer 44:23, Mat 24:2, Luk 22:51
  - G3779 (2): Jos 11:16, Jer 5:23 · G846 (1): Jos 19:8 · G1438 (1): Rev 19:20
  The **9 null-form "this/these" candidates** under G1473/G3779/G846 (Dan 4:33, Eze 36:32, Mat 3:15, 1Ch 27:6,
  1Co 1:24, 2Ki 18:9/18:10/25:8, Ezr 7:6) are **RESOLVED — L5 closed Session 7** (read vs ABP app: 8 clean,
  Dan 4:33 fixed G1473→G846; see the cert section above). The ου-/αυ-initial forms (οὗτος/αὕτη) are excluded on
  purpose — `ουτ*` collides with οὕτως G3779, `αυτ*` with αὐτός G846.
  **MATCH THE STORED REALITY:** surface `form` is accent-only, no breathing, circumflex→tonos (τοῦτο→τούτο) —
  a bare `tout*`/`τουτ*` GLOB on translit/form MISSES the accent (the γῆ #18A bug class; a translit control
  returned 13 not 3401 until switched to `τούτ*`/`ταύτ*` on the form column). When run: dry-run → ~15-row
  write to G3778, same careful pattern as the αἰών fix. code: the retag folds in build_words_from_abp.py / lxx_align.
  - Other finds parked alongside (need the ABP source, not auto-strays): G1438 has αυτού / υμάς-form rows
    (a reflexive-fold class, separate from τοῦτο). Dead lead checked + dropped: blank-english is NOT a mistag
    signature under G1473 — only 8 of ~3,322 blanks are demonstrative; the rest are ordinary ἐγώ folded into
    the verb rendering. Form-match is the only reliable finder.
  - LESSON (banked): the translit accent bug here is the #18A (γῆ) diacritic class biting an AUDIT query —
    one more argument for the normalize-both-sides fix when the Ask-corpus right-rail work starts.
- **Word-study card header — HEBREW HALF (Greek half DONE, commit `7bee235` 2026-07-06).** The Hebrew card's
  hero gloss still shows the top in-verse rendering — its `profile.definition` is the long definition paragraph,
  NOT `word_gloss`. Fix = small API change (return the Hebrew `word_gloss` in its own profile field) + one
  matching frontend line. **Own checkpoint (API change, not frontend-only).** ⚠ The sourcing comment MUST say
  **Strong's Hebrew** — the table is named `bdb` but holds Strong's Hebrew, not Brown-Driver-Briggs; this is
  exactly where a future edit would mislabel it.
- **LEXICA DISPLAY-LAYER WINDOW (banked 2026-07-08, δύναμις session; window opening UNRULED — batch-2 close vs.
  post-Session-9, JP's call when reached).** Members: the #18A diacritic normalize-both-sides fix ·
  language-scoped query drift · plus two NEW tickets:
  1. **Gloss-note sense references:** every sense mention in a gloss note gets an anchored marker (→1, →2
     superscript or equivalent) linking the sense it names, replacing bare inline prose ("sits within sense 2").
     Display-layer only — no entry data or stamp changes. Companion lint candidate: a gloss note that names NO
     sense gets flagged (cousin of the hedged-citation check, ENGINE_LESSONS #25).
  2. **Gloss-note ordering:** current order is draw-order, guaranteed by nothing. Canonical order proposed:
     by first-cited-verse's sense (notes read in the same sequence as the entry above), fallback alphabetical
     by glossed word. Renderer change only.
  3. **V6-era card style alignment (banked 2026-07-08, batch-3 session, JP):** batch-2 (V6-era) cards carry
     dense per-quote-ref styling; the ruled V7 house shape is prose + parenthesized ref clusters (diagnosed
     NOT drift — the quote line is unchanged; V7 edit 5 added the hybrid shape). Decide: cosmetic
     style-alignment pass over V6 cards vs. leave as-is until substantively redrawn. CONSTRAINT: shipped
     prose is audited — any reformat first needs a ruling on which edits are legal without re-audit
     (sibling of the fix_lexica_raw boundary). No action this batch.
  4. **LXX provenance note ⓘ + multi-sense footnote (banked 2026-07-08/09, batch-3 session, JP; two
     halves, one ticket):** (a) the "Septuagint provenance" note is terse and assumes the reader knows
     what the Septuagint is — add a hover/tap ⓘ explaining it (LXX = Greek OT translating Hebrew; senses
     resting mostly on LXX citations are translation-Greek evidence, weaker for native Greek usage than
     NT composition-Greek). (b) Meaning tab: when the note fires on MULTIPLE senses, replace the per-sense
     repeated lines with a superscript/dagger marker on each affected headline pointing to ONE footnote
     line below the sense list; the ⓘ explainer attaches to that footnote. Common case = all-senses-fire
     on OT-heavy words. Test pages: G1151 δάμαλις (all 3 fire), G4582 σελήνη (none), G2779 κῆπος (one;
     also the sub-use indent test page). Display-only, no engine change.
  5. **Header-gloss provenance (banked 2026-07-09, batch-3 session 2, JP; SYSTEMIC — 2 sightings):**
     the word-card header gloss comes from `word_gloss` (inherited TBESG/Dodson-family source,
     build_word_gloss.py), and it contradicts the verse-verified entry directly beneath it — G3900
     showed "falling away, sin" over a card proving transgression-family-only 40/40; G956 showed
     "missile", unattested in all three translations. Proposal: derive the header from top corpus
     renderings (already computed by coverage_audit); design question = top-N verbatim vs renderings +
     headline fragment. Short-term per-word hand overrides possible via the OVERRIDES dict.
     **THIRD SIGHTING 2026-07-09 (session 3): G2008 header "rebuke, chide" while the card's own gloss
     notes argue the blame-register is wrong for most sense-1 uses.**
  6. **RANGE/Coverage serif gap (banked 2026-07-09, batch-3 session 3, JP — ruled to THIS window):**
     the Range and Coverage paragraphs render in the app's sans face while the senses block and gloss
     notes get the serif style — `.lex-prose` (styles.css:1435) is missing from the Range/Coverage
     lines (20-shared-components.jsx:257, :267). Standing template gap on ALL cards, code-confirmed,
     not per-card. Two-line fix: wrap both in the serif class + rebuild. Reviewer flagged at the
     G2008 render; JP ruled: hold for the display session, don't ship mid-calibration.
  7. **Gloss-note marker AT THE CITATION (banked 2026-07-10, G4061 session 5, JP-ruled split):**
     where a gloss note names a SPECIFIC ref (G4061: "lopped" → Jer 11:16), put a small marker on
     that citation in the senses block so the note surfaces where the reader's eye already is
     (same principle as the tag-click finding; cousin of ticket #1, which anchors note→sense —
     this anchors sense-citation→note). RESTRAINT RULED: markers ONLY where a note names a
     specific ref; general commentary (G4061's senses-1-and-2 collective-noun note) gets none —
     card already carries badges/tags/×2/verified line, no chart-junk. SPLIT: rendering half =
     this window (design against V8 output, close-plan step 6); structure half = V8-PILE
     candidate (notes are free prose today; per-gloss/per-ref anchors touch what the engine
     emits — frozen until the V8 bump, close-plan step 4).
- **ENGINE TICKET (parked per batch-3 session rule; NOT display-layer): apply refuse-by-default.**
  `build_lexica_def.py --apply` currently writes an unreviewed draw with a warning when the cache key
  misses (G2563 incident, ENGINE_LESSONS #31 — an unreviewed card reached the live site). Fix = make
  `--require-cache` behavior the DEFAULT on --apply (explicit `--allow-unreviewed` to override, which
  already exists). Interim ruled procedure in force: every apply runs `--require-cache` + output read
  for "using reviewed draw" before the render step. SECOND HALF of the same ticket (JP, same session):
  the key pins the INPUT, so forced re-pulls are indistinguishable at the key level — three different
  drafts carried key 1f20c1b1 in one session; the cache held the reviewed one only by write order.
  Fix wants a CONTENT hash alongside the input key (pin the reviewed draft by what it says, not when
  written) — ENGINE_LESSONS #15's content-addressing, now with a live near-miss. JP schedules.
  5. **Sub-use paragraph styling (banked 2026-07-08, batch-3 session, JP):** "Sub-use:" paragraphs inside a
     senses_block render as plain prose, visually undifferentiated from the main sense body (confirmed on the
     live G1119 card). Wanted: a light visual indicator — indent, smaller type, or left rule, frontend's call,
     within the quiet-design rules (no boxes). Display-only; no engine/prompt/stored-data impact. JP schedules.
- **Hebrew-OT word finder is NOT number-folded** (KNOWN GAP) — the singular/plural fold is live on
  ABP/KJV/BSB but NOT the `corpus=heb` discovery branch (it matches a token inside a multi-word gloss
  phrase, so the precomputed `*_norm` column doesn't fit). A real fold needs BOTH a normalized-token
  side-index in heb.db AND a looser `gloss LIKE` prefilter. Don't ship a half-fix (folds one direction,
  reintroduces the asymmetry). Hebrew search stays number-exact until both land. Memory
  `project_lexicon_finders`.

---

## Three-zone shell — remaining consumers
The shared frame (`Shell` + `RightStack` in `static/src/22-shell.jsx`) is done; Ask-corpus, Notes, Seam
index, and News right-rail all shipped on it 2026-07-01. **Status note (JP, 2026-07-10): the Seam index
consumer is code-complete but OFFSTAGE — it rides inside the Study tab, which JP has taken down from
public (admin-gated + hidden, conceptual stage; see STATE.md Study line).** Full record: memory
`project_three_zone_shell` + `HANDOFF_corpus_shell.md`.

**Shell's MOBILE collapse has THREE consumers now: News + Ask-corpus + Notes (all 2026-07-15) —
copy them for Study, THE LAST ONE PARKED.** The gotchas they paid for (bar collision, `100dvh`
pinning, scroll-box clearance, the BARE-sheet `scrollRef` trap + the case its fallback can't rescue,
bottom-bar icon size, zones-not-verbs, the two ways to clear the bar, the doubled panel header, and
from Notes: the permanent gray, the mode-following list glyph, `.zcenter-m`'s default nested scroll
box, occlusion by hit test, the baseline A/B) are standing frontend detail, so they live in
**`docs/claude/frontend.md` → "Shell's MOBILE collapse"**, not here.

Left to do (the first two have banked session openers — paste them whole, don't re-derive:
**`HANDOFF_news_fixture.md`** then **`HANDOFF_study_mobile.md`**; the memory-index pass is
**`HANDOFF_memory_consolidate.md`**, on JP's call, independent of these two):
- **Harness: add a News feed fixture** — now the OLDEST unpaid debt here, and it has already been
  deferred through two bar/icon passes. `tests/mobile_harness.js` renders Library / Word study /
  Ask-corpus / Notes (`&notes=1`) at a phone width, but **News's mobile branch never reaches its
  `<Shell>`** without feed data, so its `.zbar` still can't be measured — both the 2026-07-15 icon pass
  AND the Notes pass had to reason about News's three bar glyphs from the shared components instead of
  seeing them. **The one bar we can't render is the one that will drift** — and it is now the only bar
  in the matrix never verified by drawn shape. Shape the fixture from the producing side
  (`views_news.py`), same rule as the others; Notes shows the adapted form when a surface has no
  server producer (frontend.md). code: tests/mobile_harness.js (FIXTURES / FIXTURE_PREFIXES)
  **DO THIS BEFORE Study's collapse (2026-07-15 ruling):** Study will cite News as its reference
  pattern, and the reference should not be the one instance nobody has verified. It is no longer
  background debt — it's the standing exception to a rule every other consumer now satisfies.
- **Close the `.filters-sep` open verification** (small, opportunistic — do it in any session that
  loads a word into Word study). The rule was promoted out of its `.ws` scope 2026-07-15 so Notes's
  strip could reuse it. Proven inert by exhaustive search (one rule for the class, no competitor), but
  NOT measured — Word study only draws its divider once a word is loaded, and the harness has no
  lexicon fixture. Measure it byte-identical (1×14, `--rule-2`) and strike the open-verification note
  in `docs/claude/frontend.md`. code: static/styles.css (`.filters-sep`)
- **FLAGGED, NOT SCHEDULED — admin's LIVE Keep/Dismiss squeeze the headline on a phone** (Kept rows worst:
  "Back to Inbox" + "Dismiss" side by side push the headline to ~148px / 5 lines). Pre-existing, NOT a
  regression, and item 1's ruling protects it — **a control that works earns its row**. But JP is the admin,
  so it's his own triage view. Fix would be stacking the actions under the headline on mobile; that's a
  design call on LIVE controls, so it waits for JP. code: static/src/84-news.jsx (NewsStory `.news-actions`)
- **Study-on-mobile shell — DEPENDENT on Study's return (JP ruling 2026-07-10): tracked, not ordered;
  its priority follows whenever Study comes back from its conceptual-stage hold, not before.** Mobile
  Topics/Graphs/Seams still run the OLD single-column branch (`.study-view .study-mobile`), not the
  shell. When taken up: shell mobile treatment (rail/inspect as sheets), same job as News-on-mobile.
  code: static/src/55-study.jsx
- **Study per-item inspect DETAIL** (deferred by design; same dependency — follows Study's return) —
  the Study tab is uniform master-detail now but the RIGHT inspect is ZoneEmpty everywhere. Wire it:
  Topics = clicked verse in context; Graphs = clicked claim/node's grounding; Seams = clicked fork's
  grounding. Each is net-new feature work. code: static/src/55-study.jsx (RightStack `push`)
- **Ask-corpus POLISH pass** (rail got a big build-out 2026-07-01/02 — per-answer selection, Key passages
  moved into the rail, ONE merged Words-in-scope list, bottom-pinned composer, contested badge via the
  served set; memory `project_three_zone_shell`). DONE 2026-07-02: empty-state hero raised + de-spinnered,
  single Inspect divider, rail dedupe/date-group/cap-10/confirm-Clear-all (display-only). STILL OPEN: the
  occurrence card's target word = the answer's PRIMARY key word (wrong-ish for a broad multi-word answer —
  should be the exact word in THAT verse); recreate the CSS parity gate with a WIDENED prop set (width,
  max-width, flex-basis, overflow-x/y — the old gate missed the News-width + scrollbar bugs). POSSIBLE
  polish: snippet clamp can hide the match (takes the first line, not a window centered on the highlighted
  word) — only if it proves common. code: static/src/52-ask-corpus.jsx, 50-corpus-results.jsx, styles.css
- **News beast-arm badge** (authored follow-up) — a per-thread "which beast/arm" tag in the why-rail.
  Not built on purpose: the thread→arm map isn't 1:1 (several threads serve BOTH arms), so it's
  hand-authored content JP will sit with, then it drops into the why-section. code: views_news.py map,
  static/src/84-news.jsx
- **Owed post-deploy human check** — click-through of News / Word study / Library on desktop + phone
  (the mobile sheets are the one thing the parity gates can't run locally); confirm the News tab shows in
  the mobile bottom nav (admin) + the News inspect looks balanced without cramping the `.news-bar` row.
  (The Ask-corpus provenance rail was checked in Chrome 2026-07-01 — fine.)

**Copy-shortlist wrapper resolution** (SHIPPED 2026-07-01, two loose ends; memory `project_news_watch`):
1. Deploy the web app (reload) so the copy-to-face button + `POST /api/news/resolve` go live.
2. Archive backfill is draining — `resolve_backfill_all.py` chunked into `daily.sh` (~1000/night under
   Google's ~1,300 clamp), ~5,700 wrappers left, self-terminates (~a week). No action unless a stable
   failing remainder persists → then the PARKED `resolve_attempts`/`resolve_failed` marker.
3. Post-deploy check: News → Kept → Copy shortlist shows "Resolving…" then pastes clean article links,
   not `news.google.com/rss/...` wrappers.

**Paywall-aware face selection + 🔒 badge** (SHIPPED 2026-07-02; memory `project_news_watch`):
1. Needs a normal CODE deploy (backend `_pick_face` penalty + `pw` per member; frontend badge).
2. Post-deploy spot-check (still OWED — no mixed cluster in the window at ship time): find a cluster
   with a paywalled outlet (WaPo/NYT/…) + a free/wire source, confirm the FREE one is the card face and
   the paywalled one shows 🔒 down in the inspect sources. Then switch presets windowed ↔ Max on that
   cluster and confirm the face stays non-paywalled in both. Unit tests cover the logic; this is the
   only human check left.

**Copy/Export shortlist + card-link formats** (SHIPPED 2026-07-02; memory `project_news_watch`):
1. Needs a normal CODE deploy — the feed read now carries `i.summary` (fills the copy "description" +
   CSV description) AND `i.resolved_url` per face/member (makes the card/article CLICK open the real
   article instead of the Google wrapper). Both degrade safely without the deploy (blank desc / wrapper
   click that still redirects).
2. Post-deploy check: News → Kept → Copy shortlist (3 formats) + Export (Markdown / CSV) download; a card
   title click lands on the real outlet, not `news.google.com/rss/...`; date window label stays put
   across refresh ("Last 7d" doesn't creep to 8d); right inspect divider lines up with the navy header
   edge when a card is selected; single-source card reads "1 source" (no "· peaked"); the scoring lens
   now lives in the ⓘ popover, not on each card.

---

**PROCESS LEDGER — News mobile Pass 2 item 1 (2026-07-15).** CC committed `3aac547` BEFORE the reviewer
receipt existed, then presented it for approval. Reviewer approved the work and named the breach:
**"branch-not-master and nothing-pushed are mitigations, not compliance."** No-crossing is POST AND STOP —
at a gated step the commit waits for the pasted receipt regardless of where it lands or whether it moved.
Disposition: no corrective commit; the review became the receipt and 3aac547 stands, merged on that same
ruling's explicit authorization. Rule record: memory `feedback_reviewer_receipt_r2b` (breach #3).

## News watch — account gate (Pass 1 SHIPPED 2026-07-15 `69a7156`, one item open)
The tab was admin-only (+ Tudor's `/?news=<key>` share link). It now reads for ANY signed-in account —
auth-only, deliberately NOT tier-based. Writes (keep/dismiss) stay admin/share-key. Audit finding folded
into the same commit: `/api/news/resolve` was a WRITE sitting on the READ gate (it caches into
`items.resolved_url` + fetches outbound) — invisible while reads were admin-only, because every reader
was also a writer; opening reads is what pulls the two gates apart. Moved to `_reviewer()` → `can_write`.
Gates locked + control-tested by `tests/test_news_gate.py` (in CI + the pre-commit hook).
- **Plain-account view CONFIRMED LIVE by JP 2026-07-15** — the `readOnly` path (grayed Keep/Dismiss) had
  never executed before this commit (every reader was also a writer, so it was dead code). Now exercised
  on the real site. Pass 1 has nothing unproven left. Follow-on: the grayed pair costs too much row on a
  phone — parked as the first Pass-2 item under News-on-mobile.
- Rulings logged: **gray, don't hide** the reader's Keep/Dismiss — reviewer ruled hide, JP superseded
  (a grayed control + "Read-only" tooltip isn't broken, it tells a reader the feed is a curated watch;
  matches `feedback_gray_dont_hide`). Kept/Dismissed tabs reading zero for a reader: **leave them**, same
  reasoning. Raw inbox to readers: **approved** (JP) — no curated/published feed build.
- **KEEPS ARE INERT — checked 2026-07-15, write it down because the intuitive story is wrong.** Nothing
  in the nightly cron reads the review rows. The scorer selects on `WHERE score IS NULL` (id/title/source/
  summary only — `scripts/news/score_news.py:207`); gather / pull_rss / group_news / resolve_new_faces
  never mention the table (`scripts/news/daily.sh` is the whole cron). The ONLY reader anywhere is
  `scripts/news/resolve_dry.py:75`, a hand-run read-only diagnostic that borrows kept stories as a
  sample — not in the cron. **So keeps train nothing. They are bookmarks.** Two consequences: (1) the
  mobile hide is a SPACE argument only — no contamination principle behind it; (2) reader keeps could not
  pollute the scorer even if readers could write them. Do not re-argue this from memory — memory will
  reach for "keeps train the scorer" because that's the intuitive story. It's wrong.
  *(How it got asked: the Pass-1 audit proved Flask can't TRIGGER scoring; that had been quietly carrying
  a second, never-checked claim that the cron CONSUMES keeps. Different claims. Memory
  `feedback_verify_before_claiming` part 8 — proven adjacent is not proven.)*
- **Reader bookmarks — small ticket, not scheduled.** Cheaper than it looks now that keeps are known
  inert: the review table is ALREADY per-person (`(item_id, reviewer)`), and `_reviewer()` already keeps
  identities structurally apart (`u<uid>` admin / `k<keytag>` share key). Giving a plain account its own
  id is close to the whole feature. Nothing feeds the scorer, so a reader's keeps stay private notes.
  code: views_news.py `_reviewer()` + `set_status`
- Share key (`/?news=<key>`, one holder = Tudor) untouched. Retirement is not ticketed.
- **Shareable News link — own ticket, NOT Pass 2** (reviewer 2026-07-15). Nothing to "fix": there is no
  News URL and no login page (the app is one page at `/`; log-in is an in-page popup), so the return-to
  problem the original prompt assumed does not exist. The funnel works — no account, no tab; make an
  account, tab appears. What's missing is a deep link (`/?view=news`, ideally per-story) that survives
  signup. Real value later; not launch-blocking, and don't bolt routing onto the mobile pass.
  code: static/src/90-app.jsx (the `?news=`/`?b=`/`?lex=` deep-link effect is the pattern to copy)

---

## Code health / cleanup
The big rework is finished (six phases + a security/code-health pass; memory `project_redesign` /
`project_architecture_rework`). Still open:
1. **Web-route test coverage.** CI auto-runs only the data-invariant tests; the endpoint snapshot harness
   (`snapshot_endpoints.py`) + browser click-through are MANUAL (run against a DB copy during dev), so web
   routes / click behavior aren't checked on every push. That's the main test gap if you ever want to
   close it. (The Joh 3:16 xref golden `kjv_text`→`text` re-baseline is DONE — committed b686073.)
   - **CI test list is an EXPLICIT set of filenames (ci.yml + pre-commit hook), NOT a `tests/*.py` glob.**
     So a bunch of real tests DON'T gate: the alias tests, `test_scope_detect`, `test_thread_skeleton`,
     `test_lexicon_lookup_bands`, `test_rail_payload_contract`, etc. Low urgency (they run locally + are
     stable), but if you want them enforced, add the filenames to both lists — or switch CI to a glob run
     (`for f in tests/test_*.py; do python "$f"; done`) once every file is import-clean from repo root.
   code: scripts/snapshot_endpoints.py, tests/, .github/
2. **Shared AI "house style" voice snippet** — the last leftover of the prompt-unify item. xref, chapter
   summary, LSJ, etc. each carry their own wording. Build ONE core.py snippet with the VOICE only (plain
   language, short one-idea sentences, no jargon/moralizing); keep LENGTH split by MODEL — HARD
   sentence-counts on Haiku prompts, SOFT adaptive on Sonnet (Haiku overran the token ceiling on a maximal
   chapter). Do NOT convert the person/place `_PN_SYSTEM` hard cap to adaptive. Editing a prompt lazily
   refreshes that category's fingerprint cache (expected). code: core.py snippet; views_crossref.py,
   views_metav.py _PN_SYSTEM, views_summary.py, views_lsj.py prompts. Memory `project_ai_synthesis_quality`.

## AI verse synthesis revisit (umbrella — JP flagged 2026-07-11; bank items here, no engine work yet)
The AI-generated prose panels (xref "Connection", chapter summary, Ask-corpus synthesis) need a proper
revisit pass. First two banked items:
1. **Divine-name rendering drifts** — synthesis prose says "Yahweh" in some panels, "YHWH" in others
   (Jer 46:25 Connection exhibit); the corpus convention it sits beside is ABP's "the LORD". JP to rule
   ONE convention (likely "the LORD" to match the reading pane), then enforce: style instruction in the
   synthesis prompts PLUS a post-generation check — prompt-only compliance will drift. Consistency/style
   class, not correctness. code: views_crossref.py synth prompt + siblings; pairs with the house-style
   voice snippet item above.
2. **Unhedged theological assertions** — a panel asserted a contested reading as settled fact. EXHIBIT
   RECOVERED from the cache 2026-07-12: the 1Co 8:5 Connection panel (row `xref_cur:1Co:8:5`, written
   2026-07-06) says "Psalm 82, quoted by Jesus in John 10, calls human rulers 'gods'" — the human-rulers
   reading stated flat; divine-council is the other major position and the dispute is live. (The Psa 82
   chapter summary is CLEAN — "divine assembly", "the gods", never adjudicates — so the class is
   panel-specific, not universal.) Same principle as the sense-header-overclaim class (stated-as-fact
   beyond what the text attests), but in free prose with NO citation gate. Banked questions: (a) a
   contested-topics prompt instruction — present positions, don't adjudicate (the CONTESTED register
   mechanism doesn't apply; synthesis is free prose over arbitrary passages); (b) a hand-curated caution
   list of known contested passages (Psa 82, Gen 6:1-4, …) fed to the prompt; (c) AUDITABILITY — panels
   regenerate and a prompt edit overwrites the category's cached rows, so exhibits vanish; ai_search_cache
   is the partial exhibit trail (this one survived because the xref prompt hasn't changed since 07-06).
   **The exhibit is the HARDER variant:** the panel is about 1 Cor 8:5 and adjudicates Psa 82 IN PASSING,
   via a cross-reference — so a contested-passage caution list keyed to the panel's OWN passage would
   miss it. Any fix must cover contested passages CITED BY a panel, not just panels ON contested passages.
   **Best diagnostic lead:** same model, same corpus, same passage — the chapter summary hedged right,
   the Connection panel didn't. Start the future window by diffing those two prompts (views_summary.py
   vs views_crossref.py), not by designing a hedging system from scratch.
   code: no-doctrinal-verdict rules in memory `project_ai_synthesis_quality`.

   EXHIBIT VERBATIM (Connection panel synthesis half, cache row `xref_cur:1Co:8:5`, 2026-07-06; the
   defect is the second paragraph's subordinate clause):
   > Deuteronomy 32 calls the LORD "God of gods and Lord of lords," and Paul's phrase in the source
   > verse echoes that title almost word for word — yet the echo sharpens a distinction. The many
   > "gods and lords" are real enough as objects of devotion, but the Deuteronomy title belongs to the
   > one who stands over all of them.
   >
   > Psalm 82, quoted by Jesus in John 10, calls human rulers "gods" — so the category is not empty.
   > The word lands on those who hold delegated authority, not on beings equal to the one who delegates.
   >
   > The Galatians passage pulls the floor out: those same "gods" are described as ones that are "not
   > by nature" gods at all — the phrase the text itself uses. Whatever reality they have is not the
   > same kind the title properly names.
   >
   > The Thessalonians passage shows where the logic can be pushed: the adversary seats himself in the
   > temple and exhibits himself as God, exploiting the very category Paul acknowledges — that things
   > are "called god." The source verse opens the door; that passage shows someone walking through it
   > wrongly.

   COUNTER-EXHIBIT VERBATIM (the clean handling — chapter summary, cache row `summary_ch:Psa:82`,
   2026-06-17; note "divine assembly" / "the gods" with no adjudication of who they are):
   > God stands in the divine assembly and confronts the gods gathered there, demanding to know how
   > long they will judge unjustly and favor sinners. He commands them to defend the orphan, the poor,
   > the humble, and the needy, and to rescue the weak from the hand of the wicked. These gods, he
   > says, have no understanding and walk in darkness, and because of this all the foundations of the
   > earth are shaken. God then reminds them of their own declared status — "You are gods, and all sons
   > of the Highest" — but warns that despite this they will die like men and fall like any ruler. The
   > psalm closes with a direct appeal for God himself to rise and judge the earth, since all nations
   > belong to him as his inheritance.

---

## Where we're behind vs other Bible apps (assessment — revisit later)
We play in the FREE serious-study niche (vs Blue Letter Bible, STEP, e-Sword, Bible Hub — NOT Logos or
YouVersion, which aren't the target). Honest gaps:
- **Fewer translations** — a handful (ABP/KJV/BSB + owner ESV/NIV) vs dozens. Cheap win: public-domain
  ASV/YLT/Darby/Geneva into the Compare picker (see "More texts" below).
- **No reading plans / devotionals / social** — deliberately not our target (chronological mode is the
  closest we have).
- **Reach / awareness is the REAL gap, not features.** One-person app on a small box; the feature set
  punches above that but almost nobody knows it exists. The missing piece is marketing, not code.

## Logos base-tier gaps — two real ones (saved, not being worked)
1. **Grammar search** — search the morph tags themselves ("every aorist participle of this verb"). We
   STORE the tags (~78% of ABP Greek, the Hebrew OT in full); what's missing is the search engine + UI.
   The single biggest thing between us and their base word-study feel. code: morph on words + heb_words.
2. **Dedicated people/places module + timelines** — we HAVE the metaV person/place cards + map, but not
   (a) a browsable "Factbook"-style hub (today cards only open on a word click) or (b) timelines. See "Map
   tab" below for the maps half. code: metav_* tables; memory project_metav_expansion.

---

## Dotted-number full audit (post-rollout ticket — sized 2026-07-07, ὄρος session)
The FOLD class is FIXED + LIVE (`build_dotted_lexicon.py` now uses `same_word()`, breathing/accent-
sensitive; commit `2ff5f7d`; dotted_lexicon rebuilt +5/−0, ὄρος draw 644→641). This ticket is the
REST of the dotted-Strong's question, none of it gating the rollout:
- **No-entry class (~86 dotted numbers, mostly the δ-cluster).** Dotted numbers with no `abp_ext`
  entry, so the builder can't recover them — they still ride the base lemma + leak into its floor.
  FIRST JOB: triage same-word forms (1510.x "being", 1391 "glory", 1364 "double", 133 "praiseworthy")
  from true foreign leaks (1392 skin/doe, 1377 aqueduct/poles, 1303.x, 1393.2 spear-under-Dorcas ×46,
  137.1 goat-under-Aenon ×74). Remedy design (stub entry? hold-out-without-entry?) = its own
  conversation (the V7 window came and went without it — still open, not forgotten).
- **⚠ HOLD-OUT FLAGS (do NOT floor before this lands or a manual hold-out is placed):** δοξάζω G1392,
  διώκω G1377, δόξα G1391. Mirrored in `HANDOFF_lexica_rollout.md`.
- **Inverse-direction audit** — nobody has checked the existing dotted_lexicon the OTHER way: dotted
  rows that ARE on the list but map to the wrong entry, or bare rows that should have been dotted in
  the source. dotted_lexicon precedent says this direction has had defects.
- **Homonym heuristic** — same-spelling-different-sense (wrist-under-fruit καρπός G2590.1) is invisible
  to any comparator; it only surfaces the way ὄρος did (a floor grows a bad sense). A gloss-divergence
  grep sweep is the candidate detector.
- **εἰμί anomaly — RESOLVED (banked):** bare G1510 base_occ=1 is real — εἰμί forms are nearly all
  dotted (1510.2.3 ×2379 etc.), not a base-extraction bug.
- **2 blank abp_surface `form` cells** (Isa 19:2, Eze 40:12) — surface-alignment gaps, note-only.
- **Draw-cache archive question** — `--force` overwrites a rejected draw under the same key (ὄρος draw-1
  2-sense reject lives only in chat). Consider archiving rejected draws so the audit trail lives in the
  machine, not the transcript.
- **Backup-script rewrite (carry-forward, root-caused 2026-07-07):** `scripts/backup_db.py` stamps
  success BEFORE the compression step, so a compression failure can log a "good" backup. Parked
  post-rollout. code: scripts/backup_db.py
- **Invariant #8 (carry-forward):** add a `journal_mode=delete` assertion to `cert_invariants.py`
  (7/7 → 8/8) so a WAL flip is caught by the suite, not just the session tripwire. code: scripts/cert_invariants.py
- **Dangling-book-ref detector — tribe/place-vs-book disambiguation (GRADUATED to defect 2026-07-07, θυγάτηρ).**
  The draw's "dangling book ref" flag false-fires on tribe/place tokens that match a book abbreviation: "daughters
  of **Dan**" (the tribe, 2Ch 2:14) reads as book Daniel. SECOND occurrence (after ὀφθαλμός's "Gal") AND reproduced
  across both θυγάτηρ draws → systematic, not draw-luck. The card text is correct; the FLAG is the false positive.
  Fix: the detector needs a tribe/place-name exclusion (or require the token to be followed by a ch:vs before
  flagging). Retires the earlier "summary-side extraction" hypothesis. Post-rollout. code: scripts/build_lexica_def.py
  - **+ prose-mention false positives (χριστός 2026-07-08):** ordinary prose phrases fire it too — "Gospel/Acts"
    flagged "Act", "in Leviticus" flagged "Lev". Same fix family (require adjacency to a ch:vs).
- **Rendering-claim lint parser fix (χριστός 2026-07-08, code-confirmed).** `_gnote_claims` in
  build_lexica_def.py captures the *italic gloss* WITH its quote marks, so a quoted gloss (`"anointed"`) never
  exactly matches the corpus rendering (`anointed`) → every quoted gloss fires "rendering-mismatch" even when
  correct (all 8 draw-1 fires on χριστός were this artifact). It also cross-pairs every gloss × every ref in
  a bullet (fires pairs the note never claimed). Fix: strip surrounding quote chars from the captured gloss;
  document (or fix) the pairing. Flag-layer only — legal any time — but the control fires in
  tests/test_lexica_detectors.py MUST stay green (case-awareness is load-bearing, don't case-fold).
  **+ SCOPE GREW (ἁμαρτία requeue 2026-07-08): prose-form blind spot.** The lint only parses
  quoted-gloss-plus-ref bullets; a rendering claim in RUNNING prose ("renders the lemma uniformly as
  'sin'… at 2Co 5:21") is invisible — ἁμαρτία pull 2's real fabrication went unflagged while 12 artifact
  fires lit pull 1. Needs a prose-form claim parser alongside the bullet parser (ENGINE_LESSONS #24 update).
  code: scripts/build_lexica_def.py `_gnote_claims`/`check_rendering_claim`
  **+ disclaimer-as-cite artifact (ὀφθαλμός 2026-07-08, ENGINE_LESSONS #11 update):** a cross-reference that
  points AWAY from its own shelf ("Eze 1:18 handled under Sense 1") counts as a cite → false double-shelf fire.
  Same family: ref scanners must distinguish citing from mentioning.
- **Comma-shorthand citation scanner (ENGINE_LESSONS #28, V8 pile — the stronger fix is detector-layer).**
  Extend the ref scanner to expand "Rom 1:1, 4" / "Lev 21:10, 21:12" tails using the preceding book+chapter,
  so the citation gate + double-shelf detector stop being blind to them (4/4 χριστός draws emitted the class;
  d1's Act 2:36 double-shelf was invisible because of it). A resweep after the fix retro-covers shipped cards.
  Batch-4 evidence keeps mounting: two more UNSEEN-REAL sets caught only by the mandatory manual tail check
  (εἰρηνικός ×5, ἀληθής Job 42:8 hiding a double-shelf behind a "42:7–8" range).
  **BATCH-5 s1 ADDS (2026-07-12, G227 hinted re-entry — 3 exhibits + a behavioral proof + the
  exposure sweep):** all three G227 draws wrote "Job 42:7–8" with 42:8 never individually counted
  (draw arithmetic 37/39 → 34/39 → 38/39, 42:8 the constant absentee), CONFIRMING from behavior that
  the citation gate excludes range-dash tails from its denominator ("N/N pass" with the tail missing).
  Draw 2 also emitted bare sub-refs "(8:14)…(8:17)" (the δόμα "At 8:16" class) — same scanner family.
  JP exposure sweep on live cards (GLOB digit–dash–digit in senses_block): **17 of 77 cards carry
  range forms** (G2962 G2983 G2992 G3624 G935 G3735 G5547 G1119 G4582 G2779 G2563 G3900 G4808 G956
  G1272 G4061 G2657) — candidates, not confirmed misses; the post-fix resweep adjudicates them.
  The fix is scanner-side only (frozen prompt untouched, no regression surface). G227's re-park
  retry-trigger = this fix landing (JP ruling pending at write time).
  **FIX BUILT (batch-5 s1, same day): `ref_spans()` tail expansion + `refused_tails()` loud-refusal
  channel (reviewer merge condition — a refused range prints REFUSED-TAIL at the gate + in the
  resweep, never silent); six consumers unified on the one scanner (gate, coverage, per-sense,
  LXX ×2, double-shelf via grounding reader, gloss-note claims); tests w/ old-scanner control
  fires in both CI lists; resweep tool = scripts/audit_range_tails.py (read-only, PA).
  FOLLOW-THROUGH OWED per JP ruling + reviewer record note: resweep output → per-card ticket
  lines, AND any card with a genuine uncited verse gets a known-issue bullet on the LIVE card
  (δίκτυον precedent), not just a ticket line. Bare "(8:14)" sub-refs stay OUT of scope
  (book-less numbers = phantom territory) — manual-check class, unchanged.
  **RESWEEP RUN ×2 (2026-07-12): run 1 caught a scanner PHANTOM (comma before a numbered book
  donated its digit — "Jas 1:12, 1Pe 1:6" invented Jas 1:1; fixed fd93d34, control test pinned).
  Run 2 CLEAN = fix ACCEPTED vs the real stored shapes (all banked exhibits recovered: εἰρηνικός
  Gen 42 chain + 1Ch 16:2, καταπέτασμα Exo 26 cluster, χριστός Rom 1:4 + Lev 21:12).
  ROSTER: 31 of 77 cards carry newly counted citations (195 refs) — G1119 G1151 G1272 G1344
  G1516 G1577 G2008 G25 G2563 G2657 G2665 G2779 G2983 G3538 G3624 G3735 G3788 G3900 G4061
  G4582 G4645 G4808 G5009 G5281 G5456 G5484 G5547 G758 G935 G956 G977. These refs were always
  READER-VISIBLE but shipped UNVERIFIED (the gate never checked them). NEXT: `--verify` pass
  (audit_range_tails.py) classifies each vs the corpus — OCC clean / NO-OCC needs eyes /
  NO-VERSE = hard problem → ticket line + live-card bullet per the ruling. Zero REFUSED-TAIL
  lines in either run.**
  **--verify ADJUDICATED (same day, reviewer-ordered before the G2805 floor): ZERO NO-VERSE
  (no fabricated refs in the shipped corpus). 8 NO-OCC, ALL range-interior sweep (διανοίγω
  2Ki 6:18-19 · καταπέτασμα Exo 26:32/36 · παράπτωμα Rom 5:19 · βασιλεύς 1Pe 2:14-16) —
  span claims, not wrong content; mention-class, NO live-card bullets (δίκτυον precedent =
  wrong content, distinct). Remaining 187 refs = clean OCC. RETRO ITEM CLOSED. G227's
  park retry-trigger (#28 fix landed + accepted) = SATISFIED, noted in the park entry.**
  code: scripts/build_lexica_def.py `_REF_RE`/`cited_refs`
- **Standing-query key-shape audit — DONE (batch-5 s1 open, 2026-07-12).** Swept every LIKE/SELECT
  template in the handoff/audit/data-model docs against the stored key shapes. ONE find: the spent
  session-6 verbatim-commands block carried the bare-prefix occ-table template (`LIKE '####%'` —
  the '227%' slip's exact shape); now annotated SUPERSEDED in place, never rewritten (historical
  record kept). All rule statements (data-model corollary, s3/batch-5 opener clauses) already carry
  the three shapes correctly; no other template misuses a key. Original ticket: three key-shape
  slips in one night (bare-prefix '227%' sweep; bare-number checks against the G-prefixed
  dotted_lexicon, twice — a DEAD check that read as clean through three words). One-time audit:
  every standing query template in the docs/procedures checked against the ACTUAL stored key
  shape of the table it reads (words = bare; dotted_lexicon = G-prefixed; lexicon.strongs_g /
  words.strongs_base = G-prefixed; kjv_strongs = prefixed). Cheap; would have caught all three.
  Sibling of the section-matcher sweep below.
- **Def-engine rendering layer — BUILT (build session 1, 2026-07-12; two follow-ups owed).**
  The fix shipped: occurrences carry `words.english` + `italic_words` alongside the head; the draw's
  here-tag shows the full slot phrase (added words named); fragment-risk heads (never standing alone)
  are phrase-annotated in the gloss set; the claim-checker accepts whole-phrase equality (containment
  still fires — ἁμαρτία protection kept); phantom protection PRESERVED (test_render_head_no_phantom
  green; 2Ch 4:13 + Isa 24:5 now control fixtures in test_lexica_detectors.py). Three checker noise
  classes fixed w/ control tests: identical-string (punctuation-stripped compare), emphasis-italics-
  as-gloss (glosses read only before the ref paren), prose-mention-counted-as-citation (double-shelve
  counts grounding-list parens only; coverage reads ALL refs, unchanged). Floor tool mirrors the new
  feed (lexica_agreement pmap). CONSEQUENCE: the user-message shape changed — every cached draw +
  saved floor predates the new shape; batch-5 charter rules fresh-floor scope.
  STILL OWED: (a) the live δίκτυον *work* bullet — analyzed the head fragment "work" as if it were
  the whole render; true render "latticed work" (pos 13, roman, JP-verified vs printed ABP). This is
  the ENGINE-PROSE instance of the fragment class (distinct from the checker false-warn instances,
  which are scanner damage and are fixed above) — needs a fresh draw under the new shape (a word
  run; batch 5); (b) re-check the "tagging error" speculations inside the G1093/G3962/G435 gloss
  notes — likely misdiagnosed parked-phrase artifacts (refusals correct); JP PA read.
  Record: audit doc FRAGMENT-RENDERING INVESTIGATION + BUILD SESSION 1 entries.
  code: scripts/build_lexica_def.py occurrences/phrase_map/check_rendering_claim/_grounding_refs
- **Section-matcher shape-conformance sweep — RUN (batch-5 s1 open, 2026-07-12).** Sweep test built:
  tests/test_section_matcher_sweep.py (in BOTH CI lists) — every handled label/sense-header variant
  pinned, plus PINNED GAPS (not endorsed, each a JP call if a draw ever produces one): singular
  "Sense:" label not a header (accepting it is NOT one-line — colon is optional, so bare "sense"
  would turn prose lines into headers) · heading/bullet label forms not headers · bold paren
  numbering "**1) x**" collapses to the loud one-sense fallback · bare-label-word-opens-section
  hazard pinned as chosen. No matcher change made (splitter edits = checkpoint-class). Original ticket: two reader
  gaps landed in ONE session on the first one-job word (#47 unnumbered one-sense card scored 0; singular
  "Gloss note:" label leaked the note into Range). Sweep `_SECTION_RE` + `_sense_spans` against every label/
  shape variant the house style permits, so the next legal variant is found by test, not by a live floor.
  code: scripts/build_lexica_def.py `_SECTION_RE`/`_sense_spans`/`sense_split_mode`
Merges with the parked ὀρ-collision retro sweep (step-0 mostly absorbed it). δίδωμι G1325 SHIPPED carries
a 1-row leak (1325.1 "mortgaged", Neh 5:3) — verified NOT cited in the live card, stands with a provenance
note; re-ship only if the no-entry remedy changes it. code: scripts/build_dotted_lexicon.py, audit_dotted_lemmas.py

---

## Word cards / lexicon — open items

- **ACCEPTANCE RUN OWED (opened 2026-07-14, zero-spend, no action until JP rebuilds anyway).**
  `finish_rebuild.sh`'s clean path has NEVER run with real steps — it was proven with stubbed steps
  only (no db, no network). JP's **next real `/rebuild-words`** is the acceptance run: the chain
  should print `== finish_rebuild done ==`, and the p2wl:v2 guard fixture drift check should fire
  automatically inside `import_tipnr` (its verified sole writer of `is_pn=1`). **`done` ⇒ the arc
  closes. A named-failures banner ⇒ DO NOT SWAP, read the step's own output.**
  **WATCH the first live run, do NOT assume it** — a wrapper that refuses to say `done` when it
  should would be a new false alarm in the highest-stakes procedure here. **Do NOT rebuild just to
  test this** — that inverts the reason for the check (JP, 2026-07-14). Full record: AUDIT "GUARD
  FIXTURE DRIFT CHECK CHAINED INTO THE REBUILD" + `DESIGN_p2_guard_drift_check.md`.

- **PROSE-ECONOMY DESIGN TICKET (JP's own inquiry, banked — zero-spend, fresh-head design work).**
  The only item on the zero-spend shelf. Not pre-decided, not pre-pitched.

- **FOUR-WORD RE-RUN (open 2026-07-14) — JP-gated checkpoint, real model spend, NOT pre-cleared.**
  The own-paraphrase near-match gate is BUILT + LIVE (`dbea202`): combined `max(char, token-SET)`,
  t=0.664, meta:v4, empty-set rule, `nearmatch:v2`. Re-run G162/G227/G236/G1390 through the fixed
  pipeline to test the lift close. Predictions on record (scoreboard reads against them): reorders fed,
  own-paraphrase exempts loud, other-item-class fed→cap→park, anchoring parks UNCHANGED and NOT breaches;
  close = no breach on any. **Fragility-band watch (0.62–0.75 combined) is LIVE mid-run — any in-band
  span = stop and report before that card proceeds.** Propose as its own checkpoint with per-word
  predicted outcomes. **Authority = HANDOFF top pointer + AUDIT "OWN-PARAPHRASE NEAR-MATCH GATE — BUILD
  LANDED" + ENGINE_LESSONS #63/#64/#65** (don't duplicate detail here). Standing constraint in code:
  `t <= 0.706` (other-item must-refuse). Parked: lead-in multi-ref anchoring (G227 Job pair / G236 Ezra
  range). code: `probe1_verbatim`/`quote_repair`.
  **~~G1390 probe-2 (revisit post-re-run, enlarged byte set)~~ — CLOSED 2026-07-15, do NOT revisit on
  a re-run.** Root = **`is_pn` is an INCOMPLETE name index** = ENGINE_LESSONS **#72**; G1390's 7 warns
  STAND (6 correct-by-spec, 1 Sabbath false positive, unfixable at current data). A bigger byte set
  cannot help — the corpus doesn't mark the names. **Revival trigger is a COMPLETE name index, NOT a
  re-run.**

- **TICKET (open, NOT-NOW — do not pull on this mid-calibration): some word cards render
  "loading" only.** JP observed cards stuck at "loading" (2026-07-10, batch-3 session 5).
  JP repro detail (2026-07-10): SAME CARDS EVERY TIME — points at bad/missing per-word data
  rather than a fetch/timing issue. JP will log specific card names as he hits them; first
  future name recorded here becomes the reproduction case. Banked by reviewer directive;
  needs a look after calibration, not during.

- **BDB as Hebrew LSJ-analog (IDEA — the app has no real BDB today; see the Licensing section).** Load
  OpenScriptures BDB (PD, 1906), display-only + Summary/Full-entry tabs matching the LSJ pattern. Synth
  pass = compression of BDB per entry (~8.6k entries): compress/drop cognate front-matter, slice per
  H-number NOT per root article (BDB nests derivatives under roots — whole-article input bleeds siblings).
  Summaries carry a BDB provenance tag, NEVER LEXICA. Independent of the Greek rollout queue. Would slot
  in as the Hebrew counterpart to LSJ (the current `bdb` table is Strong's Hebrew, not real BDB).

- **Root / family word search — PARKED (needs a real stem field first).** Word study should be able to
  surface a whole family (θεός, ἄθεος, φιλόθεος, θεοσέβεια) by the theo- ROOT. Blocker: `lexicon` has no
  structured stem/root column — only `derivation` (free-text prose). Substring on translit fakes it and
  leaks (euthéōs/βαθέως match "theos" on a letter-accident — the exact reason the 2026-07-01 translit
  lookup was split into labeled Exact/Contains bands). Don't build on substring; build a real root field
  first. Record: memory `project_lexicon_finders`.

- **Structural / function-word cards — build inventory COMPLETE + LIVE** (εἰμί + prepositions + article +
  conjunctions + particles/negatives + the referent-resolution batch + the ἀνὰ μέσον idiom). Full record +
  the locked build rules: memory `project_structural_deictic_cards`. OPEN: live-case HIGHLIGHT for
  prepositions — light the case-row matching the object's case from morph (the table already shows; wire
  it with the verse live-pull). code: structural.py, views_lexica.py, static/src/20-shared-components.jsx

- **Word-study card: numbering-crosswalk (`alias_note`) header badge** (follow-up, not blocking) — the
  Word-study card now renders the shared Lexica body (2026-07-03, fb36ac8) but does NOT show the standard↔ABP
  Strong's-number crosswalk badge the Library card shows in its header. The data is free on the same
  `/api/lexica` fetch (`d.alias_note`); only the header badge markup/placement is missing (scoped out to
  avoid creep). Match Library's `detail-strong-alias` markup. code: static/src/80-lexicon.jsx.

- **Pointer click-through** (follow-up, not blocking) — the ἵνα `contest_graph` breadcrumb and the
  dikaioō/Lexica-fork `graph_ref` are PLAIN TEXT, not click-to-open. Upgrade both together: thread an
  onOpenGraph callback 90-app → detail-panel → StructuralBody/LexicaFork that switches to the Study tab
  and opens the graph by id (the `studyPending`/`openEntry` plumbing exists for the metaV sidebar).
  code: static/src/90-app.jsx, 30-detail-panel.jsx, 20-shared-components.jsx

- **Lexica dictionary — verse-grounded word defs (Sonnet engine; LSJ display-only).** Pilot + full-build
  BATCH 1 are PUBLIC (~18 cards, `LEXICA_ADMIN_ONLY=False`); contested words hand-pinned; θεός/κύριος
  forked; the rare-word stress test is GREEN. **FREQUENCY ROLLOUT STARTED — its own BATCH ONE DONE + LIVE
  2026-07-03** (26 calibration words: top-20 content + 6 extension; ran as a checkpointed apply loop, not
  the pipeline driver). Cutoff = occ ≥ 2 (~3,954 words). Full record + the 3-tier ship-gate + frame-leak
  pre-sort rule: memory `project_lexica_dictionary`; **Batch One lessons + calibration numbers + the full
  batch-two prep list = `AUDIT_lexica_rollout.md`.**
  **STATUS (2026-07-10, step-5 session): PHASE 1 done 3/3 · BATCH-3 CLOSED 18 shipped / 2 escapes
  / 2 parked (18 RULED — the docs' earlier "19" was a propagated tally slip, audit doc FINAL-TALLY
  CORRECTION) · close steps 1–4 + audit session DONE · TWO-TIER BAR ADOPTED w/ watch tags ·
  **STEP 5 RAN + CLOSED 2026-07-10: V8 PROMOTED LIVE (JP KEEP; stamp `lexica:7ef8620328a9`;
  swap `fa18656`, re-sync `f631194`) · G2665 καταπέτασμα SHIPPED on draw 3 (draws 1–2 rejected,
  defect classes on record) · COUNT 6/15 name-true (JP BOOK) · #30 LIVE + fire classes BANKED
  (`7689884`) · first `audit.floor_diff` stored row · V9_PILE.md opened. **BATCH-4 SELECTION
  DONE 2026-07-10: roster of 10 APPROVED (διαιρέω, δόμα, εἰρηνικός, αἰχμαλωτεύω, ἡσυχάζω,
  μερίζω, παραπορεύομαι, σιωπάω, ἐκλύω, ἐπανίσταμαι) · poetry trigger retired-as-rule /
  kept-as-label · N=6-7 paper replay approved (no live change until JP sees the report) ·
  record = audit doc BATCH-4 SELECTION entry.** **WORD 1 διαιρέω PARKED (3 defect-class
  draws, pre-set rule; floor stable, defects all drafting-layer; re-openable via the
  structure-hint path; count 6/15 unchanged, nine words / nine owed, spare consumed).
  N=6-7 RAN + RULED: KEEP 10 (checker `c8d32fd` zero-cost, exact-match bar failed honestly,
  re-open = scale phase w/ pre-registered bar; audit doc N=6-7 entry). Item-5 re-open armed
  (δόμα's FRESH post-fix 3-run decides).** **CORPUS-DEFECT FIRE (audit doc entry): δόμα
  DATA-BLOCKED (no-entry dotted 1390.1; spent 3-run VOID, not an escalation) · δίκτυον
  reader-facing contamination on a counted ship (JP 4-step ruling chain owed: fix → classify
  vs source → card disposition → count membership) · fix ticket = 3 dotted_lexicon entries
  (1390.1, 1350.1, 1350.2) via the builder, CC designs / JP checkpointed · no-entry dotted =
  contaminant by default at every pre-pull · ranker occ = ceilings until the 86-number
  no-entry class is triaged (the builder's own `no_entry` bucket count; existing ticket, now
  upgraded: it bit a counted ship).**
  **εἰρηνικός SHIPPED + COUNTED → COUNT 7/15 (first zero-reject word of the calibration;
  UNSEEN-REAL ×6, manual tail check load-bearing; streak 1). δόμα PARKED (3 defect-class
  draws on clean data incl. the first live citation-gate BLOCK; 19 draws by name). ITEM 5
  re-opened + re-ruled: STRAIGHT-TO-10 for the remaining words, 3-run retired this batch.
  εὐχαριστέω G2168 enters by re-selection (7 words for 8 owed). Carve-invention = the V9
  case, ×4 with edit direction banked.**
  NEXT = εὐχαριστέω screens → eight queued words, straight-to-10, #30 live → GREEN
  activation. Item-3 tooling batch (incl. the #28 shorthand expander — load-bearing for
  #30's unseen channel, see ENGINE_LESSONS #44 — plus the structure-hint experiment)
  + /consolidate
  still green as parallel gap work. PENDING JP one-liner: add ναί/ὁμοίως/ποτέ to the ranker's
  STRUCT_BACKFILL list so they print flagged (flag-only, proposed at batch-4 selection).** JP's
  hours variable (relocation) — batch decisions when he's away, work normally when he's present
  (handoff AVAILABILITY CONSTRAINT); silence = pending.
  Current law + queue = `HANDOFF_lexica_rollout.md` (RULING LIST + ROADMAP + `## Queue`);
  authority = `AUDIT_lexica_rollout.md` (G1390 PARKED entry on top); design
  backlog = `ENGINE_LESSONS.md` (46). The paragraph below is HISTORY
  (early batch-2), kept for pointers only.**
  Batch-2 opened 2026-07-06: 4 shipped first session; **SHIP BAR
  RE-RULED to FOUR GATES** (holes/merges/completeness/granularity — NOT sense-count-match); reviewer floor
  `--runs 3`→10 on wobble; redraw cap 3; escalation trigger ARMED (3rd content-wall → mechanism decision to
  JP). Prep done that session: ranker-skips-built, ἅγιον gloss check. **Banked follow-ups (detail in the
  handoff):** (a) double-shelf detector BUILT + live in the audit path, flag-only — PA control owed
  (`--resplit --word G39 --dry-run` must fire on 1Jn 2:20 senses [1,4]) before ἔθνος; (b) word-study card
  header GREEK half DONE (`7bee235`, leads with word_gloss), HEBREW half queued (needs an API field, own
  checkpoint; the `bdb` table is Strong's Hebrew — label it so); (c) θεός G2316 sense-1 "B" — add προσκυνέω/
  λατρεύω via a Matt 4:10 citation (completeness, not a fix; CONTESTED → own checkpoint, JP's go).
  **DRAW CACHE (#1) DONE + LIVE 2026-07-03 (commit 484e226):**
  `--dry-run` saves the reviewed draw to `~/bible-db/draws/G####.json`, `--apply` ships it byte-for-byte with no
  model call (validity = hash of the full model input; stale→redraw, edited→hard refuse; `--require-cache` default
  under `--all`); kills the reviewed≠shipped class (πρόσωπον/δίδωμι/πατήρ). Tests + E2E-proven on G25. Remaining
  batch-two headline items: the **PRE-SORT / PIPELINE driver** (scoped, not built — one driver sorts a G-number
  list into the 3 tiers, runs 1-2 gate-before-build, hands 3 to JP; signals = freq + fork-membership +
  polysemy proxy + loaded-referent); **sampling rate** (100% eyeball register/loaded + SENSE STRUCTURE,
  ~1-in-5 rest); **structural backfill** (οὕτω G3779, ἕως G2193, ἰδού G2400, εἷς G1520 + the 8 oblique
  pronouns); **ἅγιον G39 gloss check** before build; ranker checks stamps upfront; ai.py↔build `_norm_book`
  cross-comments (bare "Jud" disagrees by design). (Batch One register/adjudication calls all ruled
  2026-07-03: πατήρ ships the 3-sense draw; υἱός + πατήρ no fork — see `AUDIT_lexica_rollout.md`.) Open sub-items:
  - Point `lexica_agreement.per_sense` at the new `_sense_spans` (still bold-only → a plain draw reads as
    a phantom sense-count wobble at batch scale).
  - Re-check the 80% / min-4 LXX-provenance cutoff at scale (tuned on 18 words).
  - Step 4 significance judge — voting sees that something VARIED, not whether it MATTERS (same blind spot
    as the citation gate, one layer up). Human eyes now; a model pass is unproven.
  - Verbs + Hebrew first-batches = separate tracks.
  - **Seam next-stage ("Build A") — feed design undecided.** Today's pipeline is hand-authored register →
    engine attaches forks → seams auto-display (so the shipped browse IS harvested, but its upstream is
    hand-curated — both, not either). Open question: does anything BESIDES a hand-forked word ever propose a
    seam? i.e. does engine output (freight flags, thin contested senses) generate seam CANDIDATES into a
    triage queue (harvest + Keep/Dismiss curation), or does the register stay the only gate for full forks?
    JP rules before any build. Batch One produced the first test cases either way (freight flags on plain
    words — impute, hearken/heed; λόγος sense 5 thin; the υἱός "looks like a fork, isn't one" ruling).
  - Small: the fork gate names a covenant-membership/NPP reading for dikaioō that `salvation_how` has no
    node for — add one via add_study_graph_salvation.py so the link lands.
  - **Coverage engine (piece A/B) SHIPPED 2026-07-02** (`lexica_coverage.py`; memory `project_lexica_dictionary`).
    Piece A collocation pre-check (token-level PMI, `PMI_MIN=4.0`, warn-only build hook) + piece B
    `coverage_audit` field populated on all built entries (38, via the 2026-07-03 `--resplit --all`).
    **FLAG GATE shipped 2026-07-03** (commit 967ce57; `AUDIT_lexica_rollout.md` #7): the "phrases-not-senses"
    filter for the uncited-collocation lists is DONE — the advisory flag now fires only at PMI ≥ 5.0 + a
    neighbor stoplist (οὕτω/ὅσος) + report-time mutual dedup; a share cap was tried and dropped (0 drops on
    frequent words, inverts on the rare tail). 163→73 flags across the 26; `scripts/audit_lexica_flags.py`
    inspects it. Remaining follow-ups: wire `coverage_audit` to the card UI (stored data only now); eyeball
    G166/aionios sense 4 (flagged thin); piece A could FORCE a missed collocation into the draw at build
    (warn-only today). Piece C (stratified sampling) DEFERRED — first evidence logged: huios+anthrōpos
    OT-generic vs NT-title conflation.
  (Manual CONTENT edits — batch-2 G2316 sense 4 + G5207 sense 5/believers, and batch-3 G5207 sense 6
   "Son of Man" idiom + G2316 Psa 82 into senses 3/4 — all SHIPPED + LIVE; audit A1/C3 + the θεός metaV fix
   too. Archived. See TODO_ARCHIVE + memory `project_lexica_dictionary`.)
  code: scripts/build_lexica_def.py (imports contested_register), fix_lexica_raw.py, lexica_agreement.py, views_lexica.py

- **Verse-aware gloss-note flag on word cards (design-scoping first, NO build — parked; draw cache is now done, so unblocked whenever JP wants it; not batch-two-blocking).**
  JP's idea: when a reader opens a word card FROM a specific verse in the interlinear, and that entry's
  gloss_note cites that verse, surface the note at the TOP of the card. Example: tap δίδωμι at 1Sa 22:15 →
  card leads with the impute-freight note because that verse is one of its cited occurrences. Static Library
  card view UNCHANGED — this is interlinear-entry context only. Scope in order:
  1. **Structured-refs prerequisite.** gloss_notes is stored as one prose blob; the citation catcher
     (`cited_refs`/`_REF_RE` in build_lexica_def.py) already pulls `(book,ch,vs)` from any prose (sense_provenance
     does it per-sense). Determine: is per-NOTE catch reliable off the stored blob, or does the build need a
     structured `verses:[]` field per gloss_note? If the latter → new field → JP checkpoint BEFORE anything lands.
     Also determine whether the 26 live entries can be back-parsed or need a resplit-style pass.
  2. **Precision rule.** Flag fires ONLY on exact verse match to a note's citations — never on every occurrence
     of the word. A wrong-verse flag is worse than no flag.
  3. **Design-doctrine ruling for JP (one-pill rule / emphasis budget).** Candidate: a subordinate text line at
     the card top, no new pill, no container, linking down to the note. JP rules on the visual form before build.
  4. **UI-copy principle (stated).** Flag PRESENT = a known note exists; flag ABSENT = no claim. Gloss notes are
     EXCEPTION reports over a ~40-verse sample, so absence must NEVER read as "verified clean."
  5. **Adjacency.** Relationship to the parked word-study-card provenance feature (both surface an entry's
     self-knowledge at point of reading). Scope shared card-header mechanism vs independent; don't merge without
     JP's call.
  Boundaries: scoping doc only — no schema, no UI, no build until JP reviews. Prereq facts already checked:
  gloss_notes only fires where a gloss narrows/loads/diverges, so most verses of a word carry no note (flag is
  silent by design — reinforces principle 4). code: build_lexica_def.py (`split_definition`/`cited_refs`),
  views_lexica.py (`/api/lexica`), 20-shared-components.jsx (`LexicaBody`), 30-detail-panel.jsx (fetch path).

- **Definition-engine audit — items PARKED by JP's scope call (2026-07-01).** Batch 1 (register extraction,
  blocking citation gate, G5485 alias, serve-time fork backstop, +7 gloss overrides) shipped — see memory
  `project_lexica_dictionary`. Not fixed, deliberately queued:
  - **Ask-corpus LSJ / strongs_def leakage (audit A3/A4)** — the ONE path where LSJ text + Strong's interpretive
    paraphrase reach output: `_lsj_concept_lookup` feeds LSJ semantic snippets into the Haiku SQL-gen prompt
    (steers key_strongs), and the Ask-corpus rail renders `target.definition` = `strongs_def` unlabeled
    (the field the word card was moved OFF of, per views_lsj.py:297). Fold into the Corpus right-rail work.
  - **pinned_core presentation labeling (audit B4)** — the hand-authored pinned core leads the Meaning view
    under the "✓ verified" badge with no marker distinguishing it from engine output; provenance is
    "verse-grounded · LEXICA" unconditionally. Presentation call, fold into the card review.
  - **Vocabulary watchlist lint (advisory, definition engine)** — a read-only lint that flags post-biblical
    philosophical/theological vocabulary in `lexica_def` prose. Watchlist SEED: moral, ethical, transcendent,
    ontological, person/personhood (of God/spirit), Trinity, unmerited, sacrament, ordinance, hypostasis.
    ADVISORY report, NOT a write-blocker — same spirit as the two-bucket citation miss log. Scoped 2026-07-02
    alongside the G2316 "moral authority" fix. (The corpus-search side got a prompt-rule guard in
    `_CURATION_SYSTEM`; this is the parallel lint for the frozen definitions.)
  - **One-time watchlist sweep of frozen definitions** — run the vocabulary watchlist read-only across ALL
    existing `lexica_def` prose and report hits for JP review. "Moral authority" sailed through every
    structural guard, so there may be more already frozen in. DEPENDS on the watchlist above existing — can
    be that same script's first run.
  - **VERSE_PROMPT vocabulary rule (definition engine)** — add the same corpus-vocabulary rule into
    `VERSE_PROMPT` (the build-time prompt) so freshly-generated definitions avoid the post-biblical category
    terms at the source, not just on edit. QUEUED behind the next controlled re-prove cycle (psychē-drift
    precedent — a prompt change re-proves against a frozen baseline before shipping); explicitly NOT a
    one-off edit.
  code: ai.py (_lsj_concept_lookup consumer), build_lexica_def.py (_REF_RE, VERSE_PROMPT), static/src/20-shared-components.jsx

- **LSJ "Lexica" overrides** — the blurb is a Haiku "definition" prompt + per-word hand-written overrides
  for loaded lemmas (6 seeded). Memory `project_lsj_card`. OPEN: the contested words (αἰώνιος,
  δικαιόω) are now handled by the Lexica dictionary's fairness fork, NOT a hand-written asserting override
  — HOLD δικαιόω, don't hand-write. For Strong's-fallback loaded words (no LSJ entry → raw Strong's def):
  keep Strong's for now, curate later; deferred preference = show nothing rather than a duplicate of the
  headword gloss. code: views_lsj.py _LSJ_OVERRIDES.

- **Two-tier word entry — Summary = the gloss, Expanded = the EVIDENCE** (idea, parked). Governing rule:
  the summary asserts the meaning; the expanded tier only earns its place if it shows the reader something
  they can CHECK. Expanded = (1) render breakdown as PERCENTAGES of the word's own usage with rare senses
  linked to their verses (we own this data — the distribution rail); (2) one worked-example verse per
  sense, inline; (3) a one-line provenance "seam" on the LOADED words only (where the common English gloss
  came from + why we didn't use it — distinct from the auto-derived LXX-provenance flag already shipped).
  HARD don'ts (all rebuild the systematic-theology web the method rejects): NO etymology as a headline, NO
  "related theological concepts" cross-refs, NO our-own commentary on what the word "really means." Goes
  mostly in Word study; scope any expanded section to `.wd` so it can't leak into the LOCKED Library word
  card. code: views_lsj.py; static/src/80-lexicon.jsx + 30-detail-panel.jsx.

- **"Learn" section — plain-language glossary / FAQ** (idea, parked). The audience needs no Greek/Hebrew
  training, so a reader who hits H7307 vs H7308, a dotted number, a homograph suffix, or four per-source
  counts has no in-app way to make sense of it. A text-first FAQ covering: Strong's numbers (G vs H); the
  texts + why counts differ; Hebrew vs Aramaic; letter-suffix homographs / dot = ABP added words; brackets
  + italics; Word study vs Ask the corpus. Best server-rendered like `/read` so Google indexes "what is a
  Strong's number." Mostly WRITING, not code. code: views_seo.py + templates/seo/, or an About sub-page.

- **"Loaded terms" word-study SERIES — authored content layer** (idea, parked). A repeatable series, each
  entry on a fixed SEVEN-SLOT skeleton: loaded English term + etymology → underlying lexeme(s)+Strong's →
  attested range → THE SEAM (where the loading entered — the heart of it) → symmetric audit of the rival
  gloss → case-by-case usage → most defensible rendering. ~6 entries bankable (charis, baptizō, metanoia,
  ekklesia, hamartia + propitiation). THE FORK to settle first: a standalone **Studies** section vs a
  "featured study" overlay inside Word study. Reuse study.db (json body + type + status) vs new tables.
  code: study.db / views_study.py + static/src/55-study.jsx, or new word_study tables.

---

## Ask the corpus — open items
Retrieval is Strong's-keyed SQL (occurrence lists can't be wrong); the leak was only in the prose, now
heavily guarded. Full record: memory `project_ai_search_architecture` + `project_ai_synthesis_quality`.
- **FULL AUDIT DONE 2026-07-02 — decision doc = `AUDIT_ask_corpus.md` (repo root).** Order = A → deploy +
  acceptance → B → D → C → E. **Banner comes down after batches A+B verified live.**
  - **BATCH A SHIPPED 2026-07-02 (commit 559283f, `_CACHE_CODE_VER`→42, 99 tests green).** F1 mixed-signal
    scope (both OT+NT / both greek+hebrew now answer both, not collapse to one), F2 book-aware pick-parse
    ("1 John 3:1" no longer shown as John 3:1), F4 scoped-rare-word always runs pass-2, F13 follow-up
    context drops notice-turns, F9 O.T./N.T. periods, Fix 6 divine-council hardcode removed. **JP's
    post-deploy step:** run the #20B acceptance checks 1–5 PLUS the two mixed-signal cases now baked into
    `tests/test_scope_detect.py` ("compare the OT and NT view of the Sabbath", "charis in greek and hebrew").
  - **BATCH B SHIPPED 2026-07-03 (commit 7b55783 + empty-SQL nudge).** F3 schema/examples truthed up
    (strongs_base stated as always G/H-prefixed; every example → prefixed single-match; all 3 example JOINs →
    `l.strongs_g = w.strongs_base`; KJV-comparison join `'G'||w.strongs_base`="GG4151" → `= w.strongs_base`).
    F12 user-typed Strong's numbers always permitted — a bare typed number pins like a typed word
    (`_resolve_typed_strongs` + `tests/test_typed_strongs.py`, wired into CI + pre-commit). F15 pass-1 context
    "previous turn" → "recent turns". Fingerprint auto-busted (template sha1 5446f2→45aa8c9). **Live
    spot-checks: 4/5 passed** (co-occurrence, Hebrew, typed G4442, + others). **KJV-comparison FAILED live —
    see the whole-book-comparison card below; Batch B didn't break it, it never worked.** Shipped a friendly
    empty-SQL message as the immediate patch.
  - **BATCH C (thread skeleton) — SHIPPED 2026-07-02 (commit df60d22), moved to TODO_ARCHIVE.**
  - **BATCH D/E** — rail+failure UX (F6/F7/F8/F11) and cost+cache (Tier 1 normalizer, F14 pinned
    short-circuit, #4 parallelize loops). Quality, not roughness.
- **Whole-book KJV/ABP comparison — real feature (queued, from the Batch B live-check).** "acts kjv vs abp"
  fails: no specific word, so the SQL-gen model returns empty SQL → the friendly nudge now (word-level
  works: "grace in KJV vs ABP" fires the specific-word example). Making whole-book work is NOT a prompt
  line. **CC's noise analysis (start here, don't re-derive):** the naive join `LOWER(w.english_head) !=
  LOWER(kw.word)` across a whole book matches ALMOST EVERY word — ABP and KJV are different translations, so
  their words rarely match exactly, so "differs" is true nearly everywhere → the pool floods and pass-2
  Sonnet drowns in noise. The real question the feature must answer FIRST: **which differences are worth
  surfacing?** (a meaningful rendering split, not any lexical variance). Options to weigh: cluster by
  Strong's + only surface where the SAME number gets clearly different English families; cap to N most
  frequent/most divergent; or restrict to a curated "loaded word" set per book. Design before code.
  code: ai.py comparison path + `_AI_SYSTEM_TMPL` comparison section; static/src/52-ask-corpus.jsx.
- **Hebrew-word SQL-gen misses the ABP words table — fold into the LXX-seam card (same work).** A Hebrew
  query builds `WHERE w.strongs_base = 'H7307'` against `words`, which is Greek ABP text → GUARANTEED 0
  rows; the heb.db (+90) + cognate (+21) supplements carry the whole answer (correct + full, but the "thin,
  patched downstream" shape Batch B exists to kill). Fix = teach SQL-gen to also query the Greek LXX
  counterpart (ruach H7307 ↔ pneuma G4151) so the main query searches the real ABP OT text. The H→G mapping
  "isn't always clean" — which is EXACTLY what the **LXX seam** project builds (see the LXX-seam range-
  preservation / H↔G alignment work under the lexical-texture panel follow-ups). ONE card, two payoffs: when
  the seam table exists, this SQL-gen fix becomes a lookup instead of a guess. Don't build a throwaway H→G
  map here — wait for the seam. code: ai.py `_AI_SYSTEM_TMPL` Hebrew-bridge section.
- **Tier 1 semantic cache — scope fold SHIPPED 2026-07-03 (`_CACHE_CODE_VER`→47).** The exact-repeat
  cache already existed + was free; the one hole (punctuation-strip vs O.T./N.T. scope detection collided
  "fire O.T." with "fire o t") is closed — detected scope is folded into the cache key (`_scope_tag`),
  `tests/test_cache_key_scope.py`. **Tier 2 = NO-GO** at current volume (see AUDIT_ask_corpus.md). STILL
  OPEN: the OPTIONAL filler-strip normalizer (fold "what does X mean" → "X") — MUST reuse
  `_LANG_SCOPE_TERMS`/`_TESTAMENT_SCOPE_TERMS` as the never-collapse boundary AND inherit Batch A's
  mixed-signal rule (one value per axis = scope, two = unset — never strip a scope word). code: ai.py.
- **G2455 (Jew / Judas) tagging-side split — decide if it's worth fixing** (surfaced by the Batch E task 3
  alias review, 2026-07-02). ABP crams TWO different words on G2455: Ἰουδαῖος "Jews" (~177) AND Ἰούδας
  "Judas/Judah" (~41). NOT an alias-fold candidate (folding "Jew" there would drag Judas in) — it's a
  data-surgery class: the "Jew" occurrences would need re-tagging to their own number (G2453, currently 0
  in ABP) before anything downstream is clean. Low urgency; only matters if a Jew/Judas Ask-corpus search
  reads muddy. read-only audit path: the query set in this session's transcript.
- **G4119 (πλείων "more") tagging-side merge — writeup** (surfaced by the homeless-lemma sweep, 2026-07-02).
  G4119 = 0 rows in ABP; the comparative πλείων is collapsed into its base word **G4183 πολύς "many/much"**.
  NOT an alias-fold candidate — folding "more" into G4183 drags the whole πολύς pool along (same class as
  G2455). Data-surgery: the πλείων occurrences would need re-tagging to G4119 before a "more/greater" search
  or a Lexica entry for the comparative is clean. Low urgency. Anchors that pinned it: Mat 21:36 / Heb 3:3 /
  Joh 21:15.
- **#4 parallelize the cognate + Hebrew DB loops** (follow-up, not started) — read-only independent loops
  run one-at-a-time; running them concurrently claws back seconds on MULTI-head queries only. Needs an
  identical-output before/after diff. Don't touch the model-written single SQL. code: ai.py cognate loop +
  Hebrew supplement loop.
- **Lexical-texture panel follow-ups** (the panel itself is LIVE; memory `project_corpus_enrichment`):
  (1) LXX seam range-preservation — does the Greek keep esh's range at the ~8% divergence? Doubles as the
  short-root Hebrew family fallback. (2) Rebuild bdb `lemma_plain` — re-run `scripts/add_lemma_plain.py` so
  the Hebrew word-study exact-match fast-path goes live again (guarded today, just slower). Memory
  `project_lexicon_finders`.
- **AI curation hard-tune / answer-shape redesign** — current primary/see-all + inline links is adequate,
  not the end state. Sub-items: the thread's evidence-verse list reads spammy (collapse/summarize/cap);
  label thematic verses so a wordless cross-ref (Rom 14:5 on a Sabbath query) doesn't read like an
  occurrence — DON'T drop them (Gen 1:26 for divine council relies on the same path); broad/thematic-topic
  answers are thin (retrieval is word-based — the bigger answer-shape work). code: ai.py
  _curate_primary_verses + _CURATION_SYSTEM; static/src/52-ask-corpus.jsx, 50-corpus-results.jsx.
- **Small residuals (only if they bug the user):** cross-ref weighting picks the general hub verse not the
  query-specific one (Sonnet still names the specific anchor, so low priority); residual framing lean; LSJ
  blurb was never given the citation after-check (low risk — add only if a bad cite shows up).
- **Word-study leftovers:** the English-word finder's "All" view still finds/counts Hebrew via KJV (heb.db
  only kicks in under the HEB filter) — switch All's Hebrew discovery/count to heb.db if the count matters;
  collect the user's held "small tweaks" to the new Word-study UI. The "All" merged ABP/KJV toggle stays
  PARKED (double-counts the shared NT — needs a counting rule first).
- **Word-study search LABEL — verb+tail follow-up** (low priority) — a verb followed by a NON-italic tail
  particle labels on the tail ("went forth"→forth). The italic-skip can't catch it — needs a POS rule
  (label a verb-slot on the verb via greek_pos/morph). Low value: the tail still carries the verb's sense.
  code: scripts/parse_abp.py _head_word.

---

## AI reference depth — public-domain works (idea)
Feed PD reference works into the synthesis engine the way we do LSJ/BDB. Best picks:
- **Trench (NT synonyms) + Girdlestone (OT synonyms)** — the STANDOUT. Grounds the synonym answers the AI
  was improvising; authoritative, zero license cost. (Same-root GREEK cognates are already wired in; the
  value HERE is SEMANTIC synonyms + the HEBREW side, which has no etymology to walk.)
- Thayer's, Vine's, Strong's own defs, Gesenius — more lexicon depth, easy adds.
- PD COMMENTARIES (Henry, Barnes, Gill, Clarke, JFB, Pulpit) — CAUTION: a commentary layer is IMPORTED
  interpretation, exactly what the Berean text-first rule keeps OUT. Only worth doing walled-off + clearly
  labeled "tradition, not the text"; never let it bleed into the neutral answers.
- LICENSE caution (we've been bitten): some old works have free TEXT wrapped in a not-free database
  license. Grab original scans / known-free digitizations (CCEL, pre-1929 IA printings), not a repackaging.
  code: synthesis pattern in views_lsj.py / ai.py; a loader + side table per source.

---

## Non-canonical texts — open scraps
The library is built + live (Apocrypha, Pseudepigrapha, Testaments — English; 14 Apostolic Fathers with
Greek interlinear). Full record: memory `project_noncanonical_texts`. Open:
- **Possible NEXT books** (not started): Book of Jasher (Moses Samuel 1840 — beware the pseudo-Jasher);
  4 Baruch; Apocalypse of Zephaniah; Joseph and Aseneth.
- **Wire non-canon into the Lexicon / Search tabs.** The non-canon word panel's "In the [book]" count +
  LXX cross-link were HIDDEN 2026-06-11 because they dead-ended — the Lexicon tabs only know the Bible
  corpus. Teach those tabs about the `<book>_words` tables, once, generically as a "non-canonical corpus"
  option (not per book). code: views_lexicon.py + 80-lexicon.jsx.
- **KNOWN GAP — Hebrew/Aramaic interlinear for a non-canonical text.** The extra-text interlinear is
  hard-wired to Greek (joins lexicon on a G-number; word click routes to LSJ). English-only loads are
  language-agnostic, so this only matters for a word-by-word original (e.g. Ben Sira's Hebrew): would need
  a BDB/H-number join in `/api/extra` + right-to-left chips. Not urgent — no Hebrew non-canon is queued.

---

## Notes — open follow-ups
Notes/highlights/bookmarks + opt-in accounts (email/Google) are DONE + LIVE; memory
`project_notes_highlights`. Open:
- **Word-level highlights in KJV** (optional) — KJV still anchors whole-verse; kjv_words has positions, so
  the BSB `renderBsbVerse` per-word pattern could close it. (Compare view intentionally paints whole-verse
  in every column — exact-word paint there would need the column's own translation id threaded into
  `hiForWord`.)
- **Apple sign-in** — only if wanted (needs a paid Apple Developer account; heavier than Google).
- **Email campaigns / reading-plan mailings** — the original "reach" payoff, now that mail is proven.

## Ko-fi / Berean upgrades (manual for now)
Donations are LIVE via Ko-fi; becoming a Berean is a MANUAL admin grant (subscriber emails `bereans@` →
admin flips the role). Memory `project_payments_donations`. Open:
- USER-SIDE: set up the monthly **"Berean" membership tier** on Ko-fi + put the claim instructions in its
  welcome message (the cap CTA points people there).
- OPTIONAL: a Ko-fi webhook → auto-set the berean role (no email-claim step). Berean daily cap stays 10.
  code: views_notes.py (role grant / AI_DAILY_LIMITS); a new Ko-fi webhook endpoint if automated.

---

## Licensing / attributions (page LIVE 2026-07-03; ABP wording the only open item)
Full record — source→license map, the BY-SA share-alike bucket, the bdb-is-Strong's-Hebrew lesson:
memory `project_licensing_attributions`. `/credits` + CREDITS.md are LIVE, linked from the App About
page + the crawlable SEO footer.
- **OPEN — ABP wording:** credits.html credits ABP to © Charles Van der Pool with NO permission claim
  (an HTML-comment placeholder marks the spot). Fill in the real permission/attribution line after the
  Van der Pool conversation — and keep the About "built on…" sentence un-polished until then, since his
  required wording may need to fold into/near it. ABP permission = the one real licensing exposure in the
  shipped app, a separate paid/permission question (not an attribution one).
- **OPTIONAL courtesy:** a thank-you note to OpenBible.info (geo place-coords) — CC BY doesn't require it.

---

## abp_surface backfill arc (2026-07-11) — DONE except two queued follow-ups
Pairing-rule backfill SHIPPED + verified on PA: 13,851 recovered printed forms written
(rows 345,437→359,288, delta exact vs pre-registered audit counts 13,851/4,736/62), translit
refilled (full deterministic recompute — that's the builder's design, 359,288 = all rows, not a leak).
True divergence residual ≈ 0.65% of content slots (absent 2,494 + consumed 1,483); the scary
34,103 "no partner" bucket was 30,126 Hebrew-numbered OT name slots (PN backfill's bucket).
**RULED (JP): NO fallback marker in mode-three interlinear** — residual too small; view-1 lemma
line untouched (standing non-Greek-reader rule stands). Tools: `scripts/audit_surface_coverage.py`
(read-only characterizer w/ recovery measurement + no_partner breakdown) +
`scripts/backfill_abp_surface.py` (new-rows-only, dry-run default). Design bank:
`docs/RENDERING_OVERRIDES.md`.
- **QUEUED — versification map for the 148 off-by-one verses** (989 verse_missing slots; every
  affected verse has a populated scrape neighbor). GATED on eyeball review of neighbor content —
  a wrong map stores real-looking Greek from the WRONG verse (dotted-cousin failure shape). Slow path.
- **QUEUED — ἔπω-class tag-synonym rulings table** (parked): "absent" residual is hotspot-shaped,
  G2036 ἔπω alone = 457 of 2,494; each synonym pair (ἔπω↔λέγω etc.) = ONE JP ruling applied
  corpus-wide via an explicit mapping table — NEVER fuzzy matching. One ruling ≈ 18% of residual.
- Standing: PN printed-Greek backfill (the Phase-6 `inflected`-for-PNs slot in `greekLineForWord`)
  now also owns the 30,126 Hebrew-numbered name slots + the 2,810 '*' slots.
- Rebuild note: after any `build_abp_surface.py` re-run, re-run `backfill_abp_surface.py` then
  `build_abp_translit.py` (backfill is not folded into the builder yet — fold it in if a rebuild recurs).

## Lexica def-engine — small open tickets
- **Legacy redraw order — next dip = the 24 VERSE-SHORT cards.** The 3 `"None"`-marker cards
  (G2588/G4172/G3624) are DONE 2026-07-15 (cards 85→88, zero spend — record in
  `AUDIT_lexica_rollout.md`, top entry). Rules unchanged from JP's 2026-07-14 ruling: lazily, a few
  per session at most, development first, full current gate battery, no shortcuts.
- **Repair-leg gotcha (cost a revert 2026-07-15, ENGINE_LESSONS #83):** if drafts are repaired and
  waiting to ship, SHIP THEM BEFORE committing any prompt edit — a prompt edit stales every cached
  draw at commit time and `--from-draw` refuses a stale draw. Spec-first governs authorization order,
  not commit order.
- **Gloss-note claim-checker sprays junk warnings** (seen on the G5590 fix, 2026-07-11): reports a
  MATCH as a mismatch ("claimed *breath* — corpus renders breath") and treats stray italicized words
  ("or", whole sentences) as claimed glosses — looks like the quote-extraction pattern grabbing every
  italic run. Warn-only noise, no wrong writes; fix the extractor when convenient.
  code: build_lexica_def.py gloss-note validation.

---

## Ideas / someday (nothing committed — grab whichever appeals)

**Reader / layout**
- **Doubled-mark residual (Jer 46:15 class follow-up)** — 11 verses where a bracket group's lifted
  punctuation accumulated TWO marks (`,,` / `.,` / `;,` / `—;` etc.); since the 2026-07-11 chip fix they
  render both marks together (previously invisible; prose has always shown them the same way — parity,
  not a regression). Eyeball a few, decide if the lift should dedupe/keep-first. List them with
  `python3 scripts/audit_chip_trail_drop.py bible.db --list` (the multi-char mark rows).
  code: TRAIL lift in 59c-library-render.jsx + getEnglishOrderWords in 56-library-order-logic.jsx.
- **Word detail as a floating card** — instead of the fixed right sidebar, the lexicon info pops up next
  to the clicked word. code: detail panel in 90-app.jsx.
- **Collapsing toolbar** — shrink the desktop lib-bar to one compact pill that expands on reach, giving
  the text more room. code: lib-bar in 60-library.jsx + styles.css.
- **Chronological timeline scrubber** — a draggable era timeline across the top of chronological reading
  mode for jumping around the sequence. code: chronological reading-mode UI.
- **One smart search box** — merge the Word-study and Ask-corpus inputs into a single field that detects
  what you typed (Strong's vs Greek vs plain question) and routes it.

**Word study / rail**
- **LXX transliterated-phrase pseudo-names** (Jer 46:17 "Saon Esbeie Moed") — a small class where the
  LXX transliterates a Hebrew SENTENCE as if it were a name (Heb: "a noise; he let the appointed time
  pass" — a taunt at Pharaoh; LXX read it as a proper name, ABP faithfully followed). No entity can ever
  bind (not in TIPNR — there IS no person), so these permanently hit the AI-fallback card, which
  correctly declines to invent an identity but leaves the reader with nothing. Proposed treatment: a
  hand-curated note table (likely a dozen-odd cases corpus-wide) shown instead of the AI shrug — "LXX
  transliterates the Hebrew phrase …; most translations read a taunt, not a name." Bounded, hand-ruled,
  LXX-provenance material; fits the errata/curiosity end of docs/RENDERING_OVERRIDES.md. First step when
  picked up: enumerate the class (unbound PN clicks whose name has no TIPNR/metaV candidate at all),
  then rule each by hand. code: Fix-A fallback path in views_metav.py.
- **Map tab** — biblical geography as its own tab: follow the current chapter's places; search a place +
  pin every verse; or a free-explore world map where clicking a city opens the metaV sidebar. Coordinates
  + the map library are already in place, so it's smaller than it looks.
- **Topic browser** — browse by concept (Atonement, Covenant, Resurrection…) as an alternative to AI
  search. Use an off-the-shelf topic list for the category NAMES only; generate the verses + summaries
  ourselves, Berean-style. Could ride the Study tab.
- **Broader / meaning-based passage search** — find verses ABOUT a concept even when they don't use the
  word, over the bible text itself (staying text-first, no imported library). Would need a concept index.
- **Let published study topics shape AI-search answers — divine council is the test case.** AI search
  carries a hardcoded divine-council override (`_DIVINE_COUNCIL_VERSES` / `_DIVINE_COUNCIL_RE` /
  `dc_strongs` in ai.py) AND a hand-authored "Divine Council" study topic with the same verses. The idea:
  have AI search notice a question matching a published topic, pull that topic's verses in as primary,
  prove it matches today's behavior, then DELETE the one-off — it generalizes to any authored topic. The
  study would need trigger phrases + the word chips. GUARDRAIL: only PUBLISHED text-first TOPICS may feed
  an answer, never denominations/arguments (they take sides). Saved answers must key on the topic's verse
  list so editing the study refreshes them. code: ai.py one-off; add_study_topic.py; views_study.py.
- **Study graphs — remaining bits** (graphs are admin-only). Mobile graph = narrate a traversal (argument
  STEPS vertically), NOT a shrunk 2D chart — hardest thing to preserve is the CONTESTED edges (carry
  "contested" as a colored TAG, not fine dashes, or the map quietly becomes a verdict machine). Also: a
  per-study foundational-words / lexeme strip (the baptizō "medium-neutral" insight was trimmed on the
  understanding it belongs there — specced, not built); a Strong's deep-link from a graph lexeme node
  (today boxes only deep-link verse refs); drop the place "Sin (1)/(2)" from `_COMMON`. code: argmap.py +
  views_study.py + static/src/55-study.jsx; memory project_study_modules.

**More texts + audio**
- **Textus Receptus Greek NT** — a second NT text beside ABP; same Strong's numbering, so it plugs in
  easily, and showing where two Greek texts differ is genuinely rare + useful.
- **More English translations** (ASV, YLT, Darby, Geneva) — public domain; slot into the Compare picker as
  new toggles + their own loader/db (like BSB).
- **Parsed Greek OT as a 2nd parallel text** (parked) — a CATSS-lineage Rahlfs LXX (Eliran Wong's
  LXX-Rahlfs-1935 is most turnkey — surface+lemma+morph+SBL translit paired) would be its OWN parallel
  Greek OT alongside ABP, NOT a patch to ABP's surface line. LICENSE FLAG: CATSS/CCAT is NOT MIT
  (user-declaration requirement) — read the downstream terms before shipping in a donation-taking app.
- **Fuller Greek morphology** — extend the ~78% ABP morph (CATSS for the LXX OT, macula-greek for the NT).
  The ABP-native fill was INVESTIGATED + SCRAPPED (memory `project_abp_morph_gap`) — the only ABP-keyed
  source is a paid PDF, not worth it. code: morph column on words.
- **Dramatized KJV audio** (multi-voice FCBH — rides the same pending Bible Brain key as ESV) +
  **verse-by-verse karaoke** (needs per-verse timing — parked). code: views_bsb/views_esv audio.
- **Extra-biblical texts referenced in scripture** (1 Enoch already in; Dead Sea Scrolls variants) as a
  separate section, never mixed into canon.

**Dead Sea Scrolls — wanted, the hardest one (why it's not done)**
- No public-domain English exists (Vermes / Wise-Abegg-Cook / García Martínez are all modern + copyrighted;
  what's free is photos + academic transcriptions, not a ready-to-read text).
- The scrolls are mostly broken Hebrew/Aramaic fragments — needs the H-number / RTL plumbing flagged above.
- The realistic angle isn't "another book to read" — it's a COMPARE view: the Great Isaiah Scroll (1QIsaa)
  is complete + famous, and its value is showing where it differs from the Masoretic text. A side-by-side
  "variants vs the MT" feature — bigger and different from the apocrypha plumbing. Best first step if/when.
