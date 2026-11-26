# TODO

Open work only. Finished and scrapped items (with the why + lessons) are in [TODO_ARCHIVE.md](TODO_ARCHIVE.md).
Each item may end with a small `code:` pointer for Claude to find the right spot — you can skip those lines.

**How this file is laid out (consolidated 2026-11-07):** the first four sections are the work that is
open NOW (the ~20–30 the /wrap limit counts). Everything under **Parked** waits for JP to raise it —
banked, not scheduled, never pre-pitched. **Ideas** = nothing committed.

---

## Active lane — ABP edition upgrade (English line → the app's edition)
- **STATE 11/22: THE UPGRADE IS LIVE AND STEP 8 IS CLOSED.** Live = the app edition since the 11/21 20:21 UTC swap (`7bb92e10`, DESIGN §9.235). P9, the first nightly after it, passed (§9.244). L9 on the new words closed as run (§9.245). Rulings = `docs/handoffs/DESIGN_q2_build.md` §9. Opener = the top of `docs/handoffs/HANDOFF_edition_upgrade_stageE.md`.
- **Rollback copy `bible_pre_edition_upgrade_20261121.db`: REMOVED 11/26 04:35Z (§9.279; home 8,233,516 → 7,783,960 KB). The rollback blocks RB0, RB1, RB2 and PB are SPENT (§9.279); none is run or re-drafted.** Also kept on PA until a ruled removal: the P4 live copy, src, pre_8b, the 10/25 pre-fill copy, the 9a before.db. The 11/15 and 10/25 frozen fill files: removed locally 11/26 and on PA by JP 11/26 (§9.275). The pre-fill table ~/abp_surface_prefill_20261115.db stays (step 1a and 9a read it).
- **KJV tag repair: CLOSED as found 11/25 (§9.265).** Done on live: Joh 7:1, the 21 long verses, the 31 short, Psa 7:1, 1Co 5:13 + Mar 7:11, and 89 relative-word verses ("whosoever[G302] shall[G3739]" joined onto "whosoever"). Rows and blocks: `docs/handoffs/drafts/KJV_SHIFT/`. **Recorded limits, not ordered:** a relative word and its particle more than one word apart were not searched; a single misplaced tag cannot fire the shift detector; the 16 phrase-tagged verses were judged on counts, not against the KJV tagging source.
- **Dictionary quotes: DONE and live 11/22 (§9.246).** Cards serve today's verse text by ref. **Card prose, sorted 11/23 (§9.257):** of 104 card-and-verse places, **88 really carry old-edition wording, in 36 cards**, and 16 were coincidence (`docs/handoffs/drafts/DICTIONARY_PROSE/places_20261123.tsv`). The rewrite waits for JP with the dictionary work (listed under the Lexica engine below).
- **Exo 2:11 "old er" -> "older": DONE and live 11/26 02:00Z (§9.258, 9.266-9.268).** Verse text, the word's English, head word and finder key, plus 3 abp_corrections rows (EU-Exo2:11) so a rebuild re-applies them; cert 8/8 at 406, pin moved after the after-read. The only such split in the app feed.
- **`/rebuild-words` on the app edition: DONE 11/22** (`--app-feed`, the prose step 2b, Split 84, import_tipnr 31,592). Its figures were read on the pre-swap copy; no rebuild has run from the swapped live yet, so the first one reads every figure before it trusts it.
- **Carried by name, not work orders unless JP raises them:** Split +4 (§9.205) · import_tipnr −57 (§9.210) · Mark 1:9 τῆς slot, verse text reads right (§9.210) · the C4 joined-slot rows and NO-EVIDENCE 2,140 · Jdg 11:7 1473 vs 5210 and built's Strong's numbers against the feed (§9.217-9.218) · the L9 carried set: 14 ambiguous filled-slot pairings, the 10-slot lint/sizer gap, 4 row-count-differs verses, 34 changed-after-split recipients (§9.245) · the declared-list lines for Est 5:9 @13, Jos 5:15 @27 and the five MOVED verses (§9.210) · `/rebuild-words` step 8's 10/25 G5 figures to mark as 10/25-only (§9.227).
- HOLD (JP 10/30, not this lane): after the upgrade, does the app feed take over the Greek/Strong's role
  from `abp_texts/` + `bh_scrape.db`? Decide after the English-line upgrade lands (charter §3).
- FOLLOW-UP LANE (JP 11/1, §9.62, not this lane): **tag-placement reconciliation** — 604 verses where the
  lexicon-gated passes place Strong's under different words on old vs feed English (keep old rows this
  lane). Members = the `passdiff` rows of PA `~/edition_upgrade_runs/strict_fail_20261031.tsv` (local
  copy `C:\Users\JP\edition_upgrade_runs\pa\passdiff_pa_only_604.tsv`). **The PA file name is a FIXED
  stamp in code (`build_words_from_abp.py`, `report()`) — a re-run of A (dry run OR a full `--app-feed` build) with the default `--out` overwrites it; keep the local copy.**

## Owed checks (read-only — JP on PA, or an eyeball)
- **One-minute failure of the site's database reads, about 05:50 UTC 11/23 (§9.259); no cause asserted.** `/api/books`, `/api/chapter`, verse, KJV and word-profile routes returned 500 after about 5 seconds each; the home page stayed up; reads were back by 05:51:21. What ran around it: JP's deploy of 0b2f7434, then the read-only split re-read (05:47:49 to about 05:48), then CC's paced read-only API calls to the site. If it recurs, note what was running.
- **Nave's retirement — the data was NOT removed (read 11/23, §9.255); ruled: left until Study returns (§9.257).**
  The name-path sidebar section is GONE (2026-07-16; `30-detail-panel.jsx:589`) and Nave's is not on `/credits`,
  but study.db still holds **696 `type='name'` rows, none marked deleted**. study.db is the one irreplaceable file,
  so any removal is its own ruled step. The admin-gated `/api/study/for-name` route rides Study's return too.
- **JP read-only sweeps (from 7/31):** bible-wide count of name chips still with NO Greek after the 11/22 fallback
  (no card Greek either) · bible-wide `,,` count on `verses.text` (class or
  one-off — feeds the Van der Pool errata list).
- **Eyeballs (verification debt, nothing blocks on them):** Ask-corpus mobile, both states (numbers verified
  at 375px; the VISUAL was never certified — the screenshot tool timed out) · Ask-corpus #20B acceptance
  checks 1–5 + the two mixed-signal cases in `tests/test_scope_detect.py` ("compare the OT and NT view of
  the Sabbath", "charis in greek and hebrew") · post-deploy click-through of Word study / Library on desktop
  + phone (the mobile sheets are the one thing the parity gates can't run locally) · Hebrew "bolder
  English": chip mode + Interlinear OFF should match prose exactly (the dimming while Interlinear is on is
  deliberate; if too strong on his phone = a design-tweak ruling, not a bug).
- **Mobile sheet ledger (never measured):** News' selected why-head inside its sheet (expect ~42.4 per the
  band-with-control ruling) · Day-intro card (needs chronological mode in the harness — inference only) ·
  keyboard-lift (a SHELL-level ruling for all cards; needs a real phone). Spec: `docs/claude/frontend.md`
  → "THE MOBILE SHEET CONTRACT".
- **30 seconds, never done: map the REST of the PN card's outbound links.** Only the occurrence links were
  checked (all go to Word study, `30-detail-panel.jsx:1383-1505`). Read-only.

## Before / with the next words rebuild
- **Rebuild order: the name-header build reads abp_surface before step 9 rebuilds it.** `/rebuild-words`
  8b.3 runs `build_pn_greek_identity.py`, which takes name-slot forms from `abp_surface` joined on
  (verse_id, position) (`build_pn_greek_identity.py:292-305`); step 9 rebuilds that table later — so the
  headers come from the PRE-rebuild surface table matched to the NEW positions (and, while the fill is
  live, from fill forms too — 2 headers already equal a fill form, census §5 Q7). Same shape as the 8/8
  glued-header incident (`HANDOFF_form_lane.md:25`). Read-only census first (which headers would change,
  by member) before any reorder.
- **Geometry-aware unfindability — OBLIGATION before the next ride that MOVES name slots.**
  `audit_unfindability.py` needs identity-level matching (the `attribute_unfindability.py` v4 logic) —
  position-keyed, it fails on exactly the moved class (2,049 on the ②-ride, all attributed, 0 real).
  Named pre-req in `/rebuild-words`.
- **Header receipt order is not repeatable** (found 11/7, 8B3c): `build_pn_greek_identity.py:520-521` sorts
  each name's forms by count only, so tied forms print in row order — two builds of the SAME table wrote
  receipts differing on 9 lines (RDIFF8B3C). Add the form as a second sort key; receipt-only change, run a
  local fingerprint first.
- **The build's closing text calls its source "live"** (`build_words_from_abp.py:2826-2828`): with a copy as
  source, its printed swap command would move the COPY and reload the site. Never run it as printed.
- **`build_rendering_norm.py` loose ends:** (a) "recomputed N" counts rows TOUCHED, not changed — a re-run
  never reads "0 to do"; (b) the printed undo `ALTER TABLE <t> DROP COLUMN <c>` (`:17`, `:113`) fails —
  SQLite refuses to drop an indexed column (`idx_words_ehnorm`); fix the text; (c) `--stats` has no change
  preview; (d) the finder caches "column exists" per worker (`views_lexicon.py:97-108`) — after any column
  drop, reload or the finder errors; (e) always give step 11 an explicit path — the default is `bible.db`
  in the current folder (`:96`) and a bad path creates a new empty file.
- **Re-scope `/rebuild-words` step 7** (JP-held 10/25): mark which items are data-checkable (Eze 31:9
  binding, 1Chr 1:1 identity + metaV bind, Sheshach headers — all readable through the site's read-only
  endpoints) and which must be SEEN (1Ch 13:10: Chip view "the LORD was enraged", Interlinear
  "[²was enraged ¹the LORD]"). Say "card shows H121", not "→ H121" (the word row is G76 since R-2). Lesson
  kept: CC once wrote the chip reading backwards from a pre-July build comment without reading the
  renderer (`59c-library-render.jsx` chip vs interlinear paths).
- **Stale frozen 'none' class in pn_hebrew_xref — rides the next identity rebuild (JP 10/24), no lane before
  then.** The class was set by `retire_hebrew_identity.py` (last run 8/6); identity was rebuilt after the
  8/23 form lane, the retirement wasn't. Now: none→none 1,956 words / 279 numbers · none→lemma-only 458 /
  100 · none→surface 40 / 7 (total 2,454 = the 8/6 declared count — control). **498 words** carry the
  H-number while xref still says 'none' (e.g. H1908 Hadad 1Ki 11:18…, 1Ch 1:47/51). Reader impact not
  traced. Catch-up = re-run the retirement on a copy; its declared split will no longer match, so it halts
  and needs a re-declaration (precedent `docs/tickets/RECLASS_catchup_declaration.md`). Live write → full
  checkpoint lane. **Don't fold with the gentilic none→none backfill** (Parked → names).
- **split_merges JSON: 29 superseded keys** — the PN-star pass fixes 29 of the 237 patch verses upstream
  (they skip on precondition; all 30 adjudicated DISPLAY-EQUAL, split_skips4.log). Retire at the next
  regen; harmless meanwhile. code: scripts/split_merge_fixes.json
- **Header-lane leftovers (read when the header lane is next touched):** the 9/6 landing moved 461 identity
  rows into `surface` (lemma-only→surface 421 + none→surface 40) vs the 451 receipted in
  `docs/handoffs/HANDOFF_gateB_enumeration.md` "Expected picture" — class totals reconcile, 10 rows
  unattributed · `surface` vs `lemma-only` label (reviewer 10/25): the 2 Sheshach rows went surface →
  lemma-only at the swap (accepted) — trace what the label changes on the card, and whether a header that
  matches the page should carry `surface`.
- **Path-C pronoun residue (cert ledger L12, OPEN — Door 1 census closed, FIX not built).** Daniel = **170**
  source-attested pronoun mistags (αὐτός/σύ/ὑμεῖς/ἡμεῖς still numbered G1473), read off `abp_surface`. Census
  surface = Path C's `pronoun_review.tsv` (flagged on raw 1473, so a rebuild re-flags it); control
  `grep '^Dan 4:33' pronoun_review.tsv` must fire before trusting any zero. Corpus-wide raw 3,577 is VOID as
  a mistag count (mixes genuine mistags with blank-english subject/possessive FOLD slots). Queued fix = give
  Path C an `abp_surface` fallback: where Rahlfs can't align, read the number off the ABP form via a fixed
  form→Strong's table for the closed pronoun set (σου→4675, αυτου→846, υμων→5216, ημων→2257 …), WITH a
  per-slot form/english sanity gate (skip a slot whose form isn't pronoun-shaped). Then rebuild — a rebuild,
  not an `abp_corrections` batch (wrong tool at this volume). If batched with other fixes: separately
  pre-registered diff, attribution per (row, column). S9's (P) fix left the Path-C number side untouched.
  Record: `docs/audits/AUDIT_abp_certification.md` §L12 + Door 1 disposition.
- **Cert-lane tool labels:** `verify_prose_leak.py` needs a "Tier B applied" mode (its parser-only check
  FAILs-that-aren't on the 5 Tier-B prose verses against a finished scratch — next rebuild shouldn't
  re-derive this) · `lint_split_wrong_slot.py:555` (the plain, non-feed mode only) still prints "sizing: 18,339 / 12,692" → 18,384 / 12,718
  (the post-S11 scope; both harnesses agree; the app-feed figures of record are 17,452 / 12,128 / 893, §9.245) · `audit_surface_coverage.py`'s stored-vs-live control
  needs the backfill sum (its MISMATCH warning is a permanent false alarm on any backfilled table).

## Small fixes, ready when wanted
- **PA checkout: several hundred untracked files in ~/bible-db** (seen in CCTL's `git status`, 11/17): old agreement_*/VOID_*
  draft files, logs, and stray files named like single words or book codes ("0", "1Sa", "Checking", "Done.", "Pulling",
  "Running", "Warming" — likely a mis-pasted command's output written as files). Not urgent. Keep pronoun_review.tsv /
  unmatched_pn.txt (builds write them). **Step 1 ran 11/23 (§9.255): 284 untracked files, 278 at the top level**, listed in PA
  `~/edition_upgrade_runs/leftover_reads_20261122/tidy.txt`. **Step 2 ran 11/24 (§9.261):** 51 files (21 empty strays + 30 old run logs) moved to `~/pa_tidy_hold_20261123`, nothing deleted. 227 stay: the 194 dictionary `agreement_*` files (`floor_subsample.py` reads them), anything named in code or docs, correction logs, the study.db backup.
- **Trailing-clause float set copy-pasted in 6 live places** (build + 4 render + port) — unify to one shared
  definition so they can't drift.

---

## Parked — JP raises (banked, not scheduled)

### ABP text & data lanes
Write-class items are each a checkpoint lane that starts with a PA row read. Opener:
`docs/handoffs/HANDOFF_abp_source_material.md`; Concordance record `docs/handoffs/CENSUS_abp_concordance_diff.md`.
- **Label corrections — 540 + 13 + 152.** 540 + 13 same-slot number disagreements (app vs ours; Isa 39:8
  pos 1 = suspected slot misalignment; the 540 still need the audit to write a TSV) + 152 Concordance
  candidates (Concordance number matches the Lexicon, ours doesn't: 18 repeating pairs = 86 verses incl.
  ἔνθεν 1759.3 → 1759.2 ×28, 4 already in the 13, + 66 singles). List `abp_helps/adj_b_pairs.tsv` /
  `adj_b_verses.tsv`. Precondition: PA row read of all 152 (the 66 singles' rows are unproven).
- **Concordance residue, our side: 25 slot errors + 10 split renderings.** 16 verses where the app has the
  number and its English but none of our rows carries it · 9 starred verses with the word 2+ times in the
  app vs 1 here (Pro 5:7 ἄκυρος doubtful — the app also tags `μη` 207.2) · 10 one-slot-vs-two (the
  split-rendering shape; fold into the next item at its census). Rows `abp_helps/adj_d_rows.tsv`.
  Precondition: PA row read of all 35.
- **Split-rendering double rows, 628** (JP ruled a counting defect 10/25 — the 7/9 polarity-A record had
  left them as legitimate): one Greek word carries two word rows with the same number (2Ki 11:16 `they put
  | upon` G2007; Gen 24:41 `they should | give her` G1325). 174 outside-bracket (on the helper audit's
  A-review list) · **454 both-inside-bracket — NO detector** (the helper audit skips this shape by design).
  Why it matters: the double rows inflate occurrence counts and the ≥2 check. List `tests/fixtures/split_rendering/list_628_20261025.tsv`; evidence CENSUS §5. **Detector built 11/23 (§9.257):** `scripts/audit_split_rendering.py` finds the both-inside shape and re-reads the 628 on today's table; its PA run is the next read. The fix is group 3: a rows file for clearance, after the KJV batch.
  **11/26: the detector's 784 pairs classified against abp_texts + the app slots (`docs/handoffs/drafts/SPLIT_DOUBLES/`, scripts `classify_split_pairs.py`, `draft_split_double_rows.py`):** 514 pairs = 509 real split words; 270 are two Greek words (41 of them with row positions swapped by `_split_compounds`; 4 carry a wrong source label: Jos 18:22, 1Ch 6:62, Jer 50:39, Dan 1:2 — label lane). Rows file `rows_split_doubles_20261125.tsv` brought to the ruling chat: 506 words keep the number on one row, 512 rows lose it, 481 printed forms off (17 moved to the kept row); 3 held for splitter polarity B (Exo 33:3, Eze 28:3, Eze 36:14). The fix also moves the frozen surface fill (476 of its 4,418 rows sit in these words) — re-freeze + pins with the apply program. **Still open:** 229 cut tags the detector never lists (`not_detected_20261125.tsv`: 173 of the 628's outside-bracket half + Amo 3:4 G2192 from its both-inside half + 55 on no list; the 174th outside entry, 2Sa 3:35, is in the rows file) need a read-only PA read of their rows, then their own rows file. **§9.280 (11/26): shape, keeper rule and rows file ACCEPTED; next = the apply program (check / apply / after / undo + surface amendment + floor), no write before JP's yes on the visible change.** **§9.281-9.282 (11/26): the apply program (`scripts/apply_split_doubles_20261126.py`, test `tests/test_split_doubles.py`) and the amended rows file (c95b2722…, 482 forms off, after 394,553) accepted; the live check read DONE (every figure as expected). Next = the copy-proof block (apply on a whole-file copy, step-9 builders, restore dry run, re-freeze shown equal; the 476 fill account settled there), then the floor commit (394,553, BEFORE the write, §9.281 (b)), the live write after JP's yes, then the active / fill / base pins.**
- **Purchased-helps list, ruled 11/23 (§9.257); full rows in the handoff + `CENSUS_abp_surface_fill.md`. Every figure dates from 10/25, before the swap.**
  **DO, group 3, each a rows file for clearance after the KJV batch:** the 628 fix (above) · 16 label holds · 23 + 3 unflagged
  glued splits · the single-verse holds (Baal 1Ch 5:23, Deu 4:45, Isa 41:14, 4 split conflicts, 3 app letters).
  **HOLD:** 1,823 empty-lemma slots (reader effect not on file) · 30 vs 27 glued names (re-read the full `~/abp_app_audit_rerun.txt` C3 block).
  **DONE 11/23:** the English-in-Greek audit check now catches all-Greek-letter English ("δαγγερ"). **The English-in-Greek / double-space / font-form items: CLOSED 11/26 (§9.266-9.274).** Of the 28 held cells, 27 needed nothing (same letters as the dictionary word, so no form line by the builder's rule); the 10 form cells (Psa 2:0 τω; 1Sa 7:13 ψου->του; 1Ki 8:44 οφ ης->ης; Zec 3:5 ανδ and Mat 6:13 ότιδαγγερ removed; the five 1Jn 5:8 forms that did not follow the app's verse break) are LIVE (abp_surface 395,014 -> 395,018) and ride a rebuild: the fill was re-frozen (abp_surface_fill_20261126.tsv, 4,418 = 3,878 insert + 539 update + 1 remove, with the amendment file tests/fixtures/surface_amend/abp_surface_amend_20261126.tsv), the floor is 395,018, and step 1a read CURRENT on a fresh copy 11/26 03:09Z. Verse-break read (11/25): outside the four class chapters only 1Jn 5:8's 5 forms had not followed. **Open:** the 11/15 frozen file and the pre-fill table can be brought for removal (§9.274 (2)).
  **CLOSED, not worth doing (§9.257):** 44 print inconsistencies (the Concordance's error; ours is right) · 3 unplaced refs (Concordance refs with no matching verse) · 33 unlisted forms (the form already shows) · 60 plain-η spots (no reader effect worth a Bible-data write) · MIXED 42 names (the Concordance has no name lists to check against) · 191 name slots (the 11/22 fallback shows the card's Greek where the card has one) · (d) English-Greek Index (no reader problem on file; the PDF stays available as a witness).
- **Phrase-gloss under-distribution (671, fix (g) deferred):** adjudicate a sample of the "not+verb" class
  vs the ABP app (defect vs ABP negation convention), then distribute true defects dual-ordering-style.
  Detector `scripts/audit_phrase_gloss_underdist.py`.
- **Splitter polarity B — English pooled on a function word** (hand-review only, filed 7/9, reviewer Ruling
  8). 878-case evidence frozen in `scripts/splitter_b_evidence.txt` (finder `audit_helper_double_tag.py`).
  Dominant shape "did/shall not X" on the negation with the verb row blank. Notes for the discriminator:
  Job 18:13 pos 3–4 pools on the PRONOUN (hosts widen beyond negations; both polarities in one verse) · the
  B screen matches only the pooled phrase's LAST word (misses mid-phrase content words) · **Zec 3:2 negative
  control** — pooled English on a CONTENT word's own row is legitimate · fix = a hand-verified re-runnable
  patch in the rebuild path (split_merge_fixes precedent), NOT the auto-splitter; every case adjudicated,
  no batch approval. Standing acceptance rule: re-check "no helper-word chips" on Jud 1:9, Rth 2:16,
  Job 18:13 (chips + search highlighting read the words table).
- **⑤ Bracketed article-slot rows (38) — open ruling, own cycle, own controls.** 20 whole-slot moves
  (cheap) + 18 partial moves needing a NEW position inside an existing ordering (`1Pe 4:2`, an 11-slot
  group whose positions run to 9). **Do not split off the easy 20** — a rule that fires on half a class
  can't be restated later. Exhibit `1Co 3:8` (one `'his own'` repaired, its bracketed twin not).
- **③ Hand-repair lane — 71 candidates** (eyeball DONE 8/3, `docs/audits/LANE3_b2_dispositions.md`):
  gentilic 22 · roster-silent name 41 · possessive 8 (keeps apostrophe-s, JP-ruled) + Mat 27:26.
  Hand-per-row, JP-checkpointed.
- **②-pass gap census (chip/interlinear ordering):** the PN-star pass's 194 cross-blank B-writes left the
  interior blank OUTSIDE the new bracket; chip/interlinear group only consecutive same-bracket runs, so
  those verses likely mis-order there (prose unaffected). Read-only census → dry-run → reviewer. code:
  scripts/lane3_star_gapfix.json · groupForGreekMode in static/src/56-library-order-logic.jsx
- **Carrier-gap attribution + pass-disabled replay** (unparked by the 8/1 rebuild): both only mean something
  against the now-live ruling-10 pass. Ticket §6j; defect set of record = `--predict-vs` (2,520 rows).
- **Bracket-digit sweep — 2 parked verses** (lane closed 7/28–29, `docs/tickets/bracket_digit_sweep.txt`):
  Act 10:28 (app splits into TWO bracket groups) · Num 19:2 ('is not' vs 'has not'). The Van der Pool
  errata list compiles from that ticket once these are ruled or deferred. Template note: the
  marker-permutation sweep, if ever run, inherits the sweep pattern (precondition-pinned rows, intent
  evidence per flagged group, same door).
- **340 identity slots with no words row** (DIAGNOSED 7/29, fix deferred): all 'none'-class position holes
  inside normal verses, NT-heavy (Joh 73, Act 33, Mat 30) — NOT the 345 no-name slots; reads as none-class
  rows stamped from a stale position map. Cert territory — scratch db + pre-registered
  gates, NEVER a live patch. Tool `scripts/audit_pn_lanes.py` lane 2.
- **~48 G1473 (ἐγώ) cells reading reflexives** ("himself/themselves") with a blank lemma — by-design skips of
  the cautious G1473→G846 retag. Future cleanup only.
- **τοῦτο-paradigm mistags — 15 confirmed strays** (enumerated 7/3; retag PARKED; real number G3778):
  G1473 ×11 (Deu 6:25, Ezr 9:14, Hag 2:18, Eze 45:16, Jer 7:1, 8:12, 11:3, 33:4, 44:23, Mat 24:2, Luk 22:51) ·
  G3779 ×2 (Jos 11:16, Jer 5:23) · G846 (Jos 19:8) · G1438 (Rev 19:20). **Match the stored reality:** the
  `form` column is accent-only, circumflex→tonos (τοῦτο→τούτο) — a bare `τουτ*` GLOB misses (a translit
  control read 13, not 3,401, until switched to `τούτ*`/`ταύτ*` on form). ου-/αυ-initial forms excluded on
  purpose (collide with οὕτως / αὐτός). G1438 αυτού/υμάς rows = a separate reflexive class. When run:
  dry-run → ~15-row write, the αἰών-fix pattern.
- **G2455 Jew/Judas split** (ABP crams Ἰουδαῖος ~177 + Ἰούδας ~41 on one number) and **G4119 πλείων merged
  into G4183** — data-surgery (re-tag), NOT alias folds. Low urgency.
- **Versification map for the 148 off-by-one verses** (989 verse_missing slots) — gated on eyeball review of
  neighbor content (a wrong map stores real-looking Greek from the WRONG verse).
- **ἔπω-class tag-synonym rulings table** — the abp_surface "absent" residual is hotspot-shaped (G2036 = 457
  of 2,494); each pair = ONE JP ruling applied via an explicit mapping table, NEVER fuzzy matching.
- **Doubled-mark residual (Jer 46:15 class)** — 11 verses where lifted punctuation accumulated two marks;
  since the 7/11 chip fix they render together (parity with prose). Decide dedupe/keep-first. List with
  `python3 scripts/audit_chip_trail_drop.py bible.db --list`.
- **Double comma 1Ki 9:27 is SOURCE-ATTESTED** (JP checked eSword 7/31) — we match the page; goes on the Van
  der Pool errata list. Normalizing our text = an abp_corrections ruling, never a silent cleanup.
- 2 blank abp_surface `form` cells (Isa 19:2, Eze 40:12) — note-only · stemmer stump filter in
  `lint_split_wrong_slot` misses sibling forms with count <3 — fix only if reused at scale.

### Names, places, entities (R-2 · PN · MetaV)
- **Gentilic cluster:** (1) people-class Greek backfill — retires the genuine none→none rows in
  pn_hebrew_xref (C3-Q1 condition b), adjacent to pile U; related: the 2,358 PN printed-Greek residue
  (`docs/tickets/TICKET_pn_lemma_residue.md` — scrape recovery CLOSED, needs a new source) · (2) `is_pn`
  gaps: Gen 39:17 & 41:12 "hebrew" slots; "midianitish" (Num 25:15) not recognized by
  `er.is_people_group` (changes builder output — never mid-lane) · (3) gentilic PN cards read as places
  (Assyrians → Assyria pin) — reviewer-ruled keep; card should say "people of [region]".
- **R-2 parked (pull, not push; `docs/tickets/alias_leave_list.txt` pile comments):** gentilic Group rows
  binding own Group entities (pile U) · per-reign Pharaoh links (pile V) · ladder possessive-strip (pile P) ·
  vocative-aware peel (Isa 41:14) · josua/shapan/meramoth micro alias batch · the 178 lookup H/G fill-gains
  reverted for byte-identity (per-word review) · binder Greek-key bases extension (PARKED BY RULING; record
  `docs/PLAN_r2_stage3.md`) · Lexica-minted PN numbers (DEFERRED, `TICKET_lexica_pn_numbers.md`).
- **pn_binding — 352 spelling-variant rows (abia→abijah)** → R-2's variant batch; per-pair eyeball +
  roster-freeze check (class hand-check of all 1,310 DONE 7/16, `docs/audits/AUDIT_provenance_sweep.md` §4).
- **Entity data thin spots:** Joram/Israel is TIPNR-only (honest, thin) · the person card serves Israel
  nation/land mentions — both in the entity-data backfill bucket, out of the display tickets by ruling.
- **25-name disambiguation lane** (banked 7/30): one metaV person but 2+ real TIPNR people, so the guard
  declines the card — first customers of a future multi-entity card: Achsah, Alemeth, Asriel, Calcol, Eder,
  Hakkoz, Hanniel, Harbona, Hotham, Ishmaiah, Izhar, Jaasiel, Jekamiah, Joiada, Joshaphat, Mahlah,
  Mehetabel, Nahum, Palti, Rab-saris, Salome, Sharezer, Shemer, Zattu, Zerubbabel.
- **Jacob-class name cards — open lanes only** (shipped arcs in TODO_ARCHIVE + memory
  `project_pn_card_confidence`; census denominator 591 slots / 156 names): 1Ki 4:13 gilead p4 (wrong-paint;
  ships ONLY with the compound-name lane) · Elnatham Ezr 8:16 p15 (variant-spelling appendix) · chapter-grain
  5 (azariah/joash/benaiah/harim — any fold-in RETURNS TO THE REVIEWER) · Jabish ruling (9 "Jabish Gilead"
  verses + gilead 1Ch 10:12 / 2Ch 18:3) · chip-merge (1) compound-number DATA admission (H6100, H7433; card
  number for EVERY merged pair, Greek side too — Dibon Gad G1045; order: verify vs pages + xref layer, land as
  recorded links with receipts, THEN chips/cards wear them) (2) pair co-occurrence count line.
- **Greek-header hand-table polish** — 857 UNRESOLVED names (receipt `greek_header_split.txt` is PA-only,
  regenerated each build). Batch discipline: declension-only names with a page-attested dictionary form;
  real spelling variance stays per-verse; abner/absalom + EGYPT PINNED verse-form. BANKED: per-row-exclusion
  mechanism (egypt ~1,189 + adonijah 38 + artaxerxes). The split file caps each form list (~6) — big names
  need the bh_scrape census. Record `docs/tickets/DRILL_greek_header_backfill.md`.
- **Header leftovers:** 20 glued-blanked rows (ruling 3, 8/24 — now show English; any deserve a real header?
  members in `HANDOFF_gateB_enumeration.md`) · Mat 9:35 scrape typo `Ισηούς` → corrections-lane citation ·
  Mar 2:8 / Mar 14:66 variant forms = hand-table candidates.
- **Same-name / renamed drops (358 slots, opened 7/31 at the G707 ship)** — ruled correct-to-drop (text-first)
  but each carries a defensible link (edom/Esau, horeb/Sinai, molech/Moloch, gehenna…); verbatim list
  `docs/tickets/G707_diff_report.md` Group B. Any allowlist = cert-#7-style machinery, red-first gates.
- **Star-slot G-number (vocative-O residue, own ruling):** Jer 15:5 Ιερουσαλήμ serves lemma-only/no-number
  while G2419 exists — an R-2 identity-rules question (FINDING in `docs/tickets/vocative_head_words.txt`).
- **"Field" oddity** — capitalized 'field' (Isa 29:17 al.) serves a metaV PLACE card via name match (flag only).
- **David spelling on name chips (listed, ruling chat 11/22, §9.248):** our Greek reads Δαβίδ at 1Sa 24:5 and 1Ch 21:9; the ABP app prints Δαυίδ there (Mat 22:42: both Δαβίδ). We keep ours; the Greek side of the feed is the HELD question in the active lane.
- **Place-card raw fields:** `area: ">"` on 959 place records — TIPNR place rows use a different column layout
  (the read lands on a '>' marker); person-side `area` is mixed by design too (~1,150 "Tribe of X" vs ~400
  regions/periods). Parser pass (section='place' in `entity_resolution.parse_tipnr`) and/or display
  fallback; check FIRST whether the reader already suppresses it.
- **Place-map pin = interim plurality heuristic** (`_pin_from_rows`, views_metav.py:388): failure mode is
  no-pin, never a misplaced pin, but distinct-point referents never get a pin. Real fix = an entity-level
  join. **Try the MetaV `MainIndex.csv` place distill FIRST** (PlaceID + verse per word — likely solves the 86
  HAND-RESOLVE places from the `scripts/build_tipnr_metav_link.py` dry run, no new source/licensing); fall back
  to OpenBibleInfo (licensing check BEFORE ingest). Shares `tipnr_metav_link` (kind='place').
- **BSB entity-resolution coverage** (wrong-identity risk class): Ephraimites/Num 2:18 (BSB `bene-X`) reaches
  only H1121. First step: Levites Neh 11:3 on BSB — fires = construct-phrase gap; doesn't = cards ABP-only.
- **Dan 1:6 trio** (Azariah/Hananiah/Mishael) — hand-resolve the alias-record residual (steps in
  `docs/handoffs/HANDOFF_metav_person_link.md`).
- **Adonai-card residue:** (2) adonai (H136) rides the PN lane while its blurb calls it "a title for God" —
  revisit as an is_pn classification question · (3) PROVENANCE SEAM: AI summary sits directly above verified
  TIPNR/METAV data in one visual register — the disclaimer carries the whole load.
- **Eponym both-senses upgrade** (JP option (b), 7/11): per-occurrence sense from an explicit JP-ruled pattern
  list on neighbor words ("king of", "land of", "tribe of" → territorial) — never fuzzy guessing; sub-candidate:
  person-vs-territory TALLY for H3063/H3478 ("most" kept meanwhile). code: 30-detail-panel.jsx EPONYM_LINES
- **ABP-tab routing follow-ups** (record `docs/tickets/CHARTER_abp_tab_routing.md`): (a) Zion 168+1, Aram 12+5 —
  header lane folds the lemma-only residual, then they route with no code change · (b) Israel 2,584 /
  Jerusalem 753 — route only via the header lane's `surface` class, never a lemma-only door (reviewer-refused
  9/6) · (d) collisions γαζα G1047/G1048, ηλι G2241/G2242 refused by rule.
- **Deferred by ruling (provenance arc, closed 7/31):** hedged name-match pill conversion · Contested fork-header
  hover (ruled no) · Study-tab tags (wait for Study) · ac-prov-contested left title-only.

### Reader / Library
- **QUEUED, own session (reviewer-approved 8/9): the consumed-jump refactor** — treat a jump's `translation`
  as CONSUMED once applied so no re-send can re-assert it; the real cure for all three hand-stripped sites
  (search jump, page turn, version switch). Touches the load-bearing nav effect. Rule + producers:
  `docs/claude/frontend.md` → "Navigation / jumps".
- **Unselected translation tabs read as disabled** (`.seg-b`'s selected state is a white pill) — fooled JP AND
  the reviewer in one session. **Do NOT "fix" it by graying for real**; a visual change needs JP's yes.
  code: static/src/59b-library-nav.jsx:178
- **Highlight span boundaries in translation text modes** (banked 7/31, H7307 BSB; check KJV too) — diagnose
  first: (1) punctuation bleed (Gen 6:3 `"My Spirit`) — the renderer puts trailing punctuation INSIDE the span
  by construction (`50-corpus-results.jsx` `{w.word}{w.punc}`); (2) suspect targets (Gen 7:22 lights only `of`;
  Gen 26:35) — if alignment genuinely maps רוח there, document, don't "fix"; (3) multi-word spans are plausibly
  correct. Render-layer, no data writes expected.
- **Word-level highlights in KJV** (optional) — kjv_words has positions; the BSB `renderBsbVerse` per-word
  pattern could close it (Compare paints whole-verse in every column on purpose).
- **Badge / verification-token unification** — provenance badges vs "✓ N/N verified" marks (rule in
  `docs/design.md`); converge opportunistically, no sweep.
- **Reader display layers (ABP overrides + divine-name display)** — FUTURE LANE, parked behind batch one +
  FRAME-0. Design: `docs/RENDERING_OVERRIDES.md` ("Reader display layers" section).

### Word study & lexicon
- **Word-card short meaning: all 14,770 count-built headers read 11/23 (§9.255); 1,113 more kept by name.** Left open: **17 word pages pool different Greek words** (G131 G151 G1303 G1314 G1315 G1316 G1326 G1333 G1335 G1337 G1356 G1357 G1368 G1371 G1377 G1393 G1759, with 45 dotted numbers that have no entry of their own; G1393 Dorcas lists spear 38), so neither the counts nor the stored meaning is right for all their verses; the same shape exists on 47 base numbers in all, the other 30 not flagged as misleading · **15 words have a misleading header and no stored meaning** (G40 G640.2 G1350.1 G1610.2 G2468 G2674.2 G2711.1 G2926 G2982 G3386 G3785 G4339.5 G4896 G4921.2 G5315) · 133 flagged headers were left on the counts because the stored meaning was no better; a few of those (G3439, G4282, H8438) need a better stored meaning.
- **Greek text search / inflected-form lookup** (JP hit it 7/29 searching κύριε): Library in-text search is
  English-only by design (views_search.py). If built, it MUST compare accent-insensitively both sides (reuse
  the existing normalizer — `docs/tickets/accent_divergence.txt`; never write a second one) or it inherits the
  4,250-row false-miss class. The κύριε half has its own door: ABP's printed forms already sit under G2962
  (κύριε 663 · κυρίου 2422 · κυρίω 832 · κύριον 591). (The English-only message is under Small fixes.)
- **Word-study profile slow on mega-frequency Greek words** — BASELINE TO BEAT = LIVE 6.5 s / 155 KB on G2316
  (curl-verified 7/25). Not a stage-3 cost. Directions: trim default_verses (first N + lazy rest), one grouped
  aggregate read, or cache hot profiles. code: views_lexicon.py lexicon_profile / _all_books_verses
- **Hebrew-OT word finder is NOT number-folded** (known gap) — needs BOTH a normalized-token side-index in heb.db
  AND a looser `gloss LIKE` prefilter. Don't ship a half-fix (folds one direction, reintroduces the asymmetry).
- **English finder "All" view** still finds/counts Hebrew via KJV (heb.db only under HEB) — switch if the count
  matters · the "All" merged ABP/KJV toggle stays PARKED (double-counts the shared NT; needs a counting rule) ·
  collect JP's held "small tweaks" to the Word-study UI.
- **Search LABEL verb+tail** (low) — "went forth" labels on "forth"; needs a POS rule. code: scripts/parse_abp.py _head_word
- **Root / family word search — needs a real stem field first** (`lexicon` has only free-text `derivation`;
  translit substring leaks — euthéōs matches "theos"). Never build on substring.
- **Structural cards: live-case HIGHLIGHT for prepositions** — light the case-row matching the object's case
  from morph. code: structural.py, views_lexica.py, 20-shared-components.jsx
- **Provenance render — tappable badge tooltips** (rest CLOSED 7/16, `docs/CHARTER_provenance_render.md`): ONE
  shared component + ONE registry keyed by contract §2; own session.
- **LSJ "Lexica" overrides** — contested words (αἰώνιος, δικαιόω) go through the dictionary's fairness fork —
  HOLD δικαιόω, don't hand-write. Strong's-fallback loaded words: curate later; preference = show nothing
  rather than duplicate the headword gloss. code: views_lsj.py _LSJ_OVERRIDES
- **(optional) 46 dotted scholarly-prose hapax have no word_gloss** — they show the LSJ section instead
  (accepted 2026-06-23); hand-finish one-liners only if 100% header coverage is wanted.
- **Dotted-number full audit** (sized 7/7; the FOLD class is FIXED, `2ff5f7d`): no-entry class ~86 numbers (mostly
  δ-cluster) — triage same-word forms (1510.x, 1391, 1364, 133) from foreign leaks (1392, 1377, 1303.x, 1393.2
  ×46, 137.1 ×74); remedy design is its own conversation · **⚠ HOLD-OUT FLAGS — do NOT floor δοξάζω G1392,
  διώκω G1377, δόξα G1391 before the remedy lands or a manual hold-out is placed** (mirrored in
  HANDOFF_lexica_rollout) · inverse-direction audit (dotted rows mapped to the wrong entry) · homonym heuristic
  (καρπός G2590.1 "wrist"; a gloss-divergence grep is the candidate detector) · draw-cache archive for rejected
  draws (`--force` overwrites them). δίδωμι G1325 carries a 1-row leak (1325.1 "mortgaged", Neh 5:3) — not cited
  in the live card. code: scripts/build_dotted_lexicon.py, audit_dotted_lemmas.py
- Ideas, parked: **BDB as Hebrew LSJ-analog** (OpenScriptures BDB, PD 1906; slice per H-number, NOT per root
  article; BDB provenance tag, never LEXICA) · **two-tier word entry** (Summary = the gloss, Expanded = checkable
  EVIDENCE — usage percentages with rare senses linked to their verses, one worked-example verse per sense, a
  one-line provenance seam on loaded words only; NO etymology headline, NO "related concepts", NO our-own commentary; scope to `.wd`) · **"Learn"
  plain-language FAQ** (server-rendered like `/read`) · **PN definition engine** (verse-grounded blurbs for
  people/places/groups — after def-engine calibration).

### Lexica definition engine — law + queue = `docs/handoffs/HANDOFF_lexica_rollout.md`
- **Dictionary card prose: rewrite the 88 places that still carry old-edition wording, in 36 cards (waits for JP, §9.258).** List: `docs/handoffs/drafts/DICTIONARY_PROSE/places_20261123.tsv`.
Authority `docs/audits/AUDIT_lexica_rollout.md`; design backlog `ENGINE_LESSONS.md`. Live cards 85 (DB-counted —
the table is the count). NEXT = see the HANDOFF top pointer (never restated here).
- **Display-layer window — 8 banked tickets** (gloss-note sense anchors · note ordering · V6-era style alignment ·
  LXX ⓘ + multi-sense footnote · header-gloss provenance, 3 sightings · RANGE/Coverage serif gap · marker at the
  citation · sub-use styling) + the **verse-aware gloss-note flag** scoping — full text in the HANDOFF
  "DISPLAY-LAYER WINDOW" section. Window opening UNRULED.
- **Engine: refuse-by-default** — `--require-cache` is now default under `--all` (opt out `--allow-unreviewed`);
  single-word `--apply` stays permissive with a warning (confirm that's the ruling). Still open: pin the reviewed
  draft by a CONTENT hash alongside the input key (three different drafts carried key 1f20c1b1 in one session;
  ENGINE_LESSONS #15/#31).
- **Checker residue** (flag-layer, legal any time; keep `tests/test_lexica_detectors.py` controls green —
  case-awareness is load-bearing, never case-fold): prose-form rendering claims are invisible (the parser reads
  only quoted-gloss-plus-ref bullets — ἁμαρτία pull 2's fabrication went unflagged; ENGINE_LESSONS #24) · the
  gloss × ref cross-pairing within a bullet (document or fix) · dangling-book-ref false fires on tribe/place/prose
  tokens ("daughters of Dan", "Gal", "Gospel/Acts", "in Leviticus") — require adjacency to a ch:vs or exclude
  tribe/place names · (a) δίκτυον *work* bullet analyzed the fragment "work" for the true render "latticed work" —
  needs a fresh draw under the new shape · (b) re-check the "tagging error" speculations in the G1093/G3962/G435
  gloss notes (likely parked-phrase artifacts; JP PA read). code: scripts/build_lexica_def.py
- **Def-engine audit — parked by JP's scope call (7/1):** Ask-corpus inspect card `strongs_def` fallback (Ask
  section) · pinned_core presentation labeling (audit B4 — hand-authored core under the "✓ verified" badge with no
  marker) · **vocabulary watchlist lint** (advisory, read-only; seed: moral, ethical, transcendent, ontological,
  person/personhood, Trinity, unmerited, sacrament, ordinance, hypostasis) + its first run = a one-time sweep of
  frozen definitions · **VERSE_PROMPT vocabulary rule** — queued behind the next controlled re-prove cycle, NOT a
  one-off edit.
- **Open sub-items:** point `lexica_agreement.per_sense` at `_sense_spans` (bold-only reads as phantom wobble) ·
  re-check the 80% / min-4 LXX-provenance cutoff at scale (tuned on 18 words) · step-4 significance judge (human
  eyes now) · verbs + Hebrew first-batches = separate tracks · seam "Build A" feed design (JP rules first) · add a
  covenant-membership/NPP node to `salvation_how` (add_study_graph_salvation.py) · coverage engine: wire
  `coverage_audit` to the card UI, eyeball G166 sense 4, piece A could FORCE a missed collocation into the draw
  (warn-only today), piece C (stratified sampling) DEFERRED — its first evidence: huios+anthrōpos OT-generic vs
  NT-title conflation.
- **FOUR-WORD RE-RUN (G162/G227/G236/G1390, opened 7/14) — may be spent; check AUDIT_lexica_rollout** (its later
  entry reads "parked-word queue COMPLETE — four words characterized, one shipped", G1390 live). If still open:
  JP-gated, real spend; fragility-band watch 0.62–0.75 = stop and report; `t <= 0.706` constraint in code;
  authority = HANDOFF top pointer + ENGINE_LESSONS #63–#65.
- **Some word cards render "loading" only** (JP 7/10) — same cards every time → bad/missing per-word data, not
  timing. First card JP names becomes the repro case. Not mid-calibration.
- `STRUCT_BACKFILL` (`scripts/rank_lexica_candidates.py:69`) — add ναί/ὁμοίως/ποτέ (pending JP one-liner, flag-only).
- **Prose-economy design ticket** — JP's own inquiry; zero-spend, fresh-head design work. Not pre-decided, not
  pre-pitched.

### Ask the corpus & AI synthesis
Decision doc `docs/audits/AUDIT_ask_corpus.md` (order A → B → D → C → E; A `559283f`, B `7b55783`, C `df60d22`
shipped; the "Under construction" banner came down with `ffdd966f`). The 7/2–3 "Batch D/E" alias work in
TODO_ARCHIVE is a separate ad-hoc batch — the audit's D and E below are still open.
- **Batch D/E** — rail + failure UX (F6/F7/F8/F11) · cost + cache: Tier 1 filler-strip normalizer ("what does X
  mean" → "X"; MUST reuse `_LANG_SCOPE_TERMS`/`_TESTAMENT_SCOPE_TERMS` as the never-collapse boundary and inherit
  Batch A's mixed-signal rule; Tier 2 = NO-GO at current volume) · F14 pinned short-circuit · #4 parallelize the
  cognate + Hebrew loops (multi-head queries only; needs an identical-output diff; don't touch the model SQL).
- **Words-in-scope counts should be search-relevant** (JP standing gripe) — rail chips show TOTAL-Bible counts;
  compute per key word over THIS search's pinned pool and ship in the payload — never approximate from curated key
  passages; `hasCount:false` rows get a visibly distinct "no count" state (silent-fallback rule).
  code: ai.py, 52-ask-corpus.jsx + 51-corpus-logic.jsx
- **Ask-corpus inspect card: `strongs_def` fallback (remaining half of audit A3/A4)** — the SQL-gen half is FIXED
  (LSJ context is keys-only via `ai._retrieval_context`; locked by `tests/test_synthesis_no_leak.py`). Still open:
  with no Lexica entry, the inspect card shows `target.definition` = `strongs_def` (ai.py `row["strongs_def"]`;
  `.ac-insp-gloss` in 52-ask-corpus.jsx) unlabeled — the Strong's paraphrase the word card was moved OFF of.
- **Polish leftovers:** the occurrence card's target word = the answer's PRIMARY key word (should be the exact word
  in THAT verse) · recreate the CSS parity gate with a WIDENED prop set (width, max-width, flex-basis, overflow-x/y
  — the old gate missed the News-width + scrollbar bugs) · possible: snippet clamp can hide the match.
- **Whole-book KJV/ABP comparison** ("acts kjv vs abp" returns the nudge) — the naive `english_head != kw.word`
  join floods (two translations rarely match), so decide FIRST which differences are worth surfacing (same Strong's
  with clearly different English families; cap to N; or a curated loaded-word set). Design before code.
- **Hebrew-word SQL-gen misses the ABP words table** (a Hebrew number against Greek `words` = guaranteed 0; heb.db
  + cognate supplements carry the answer). Fix = query the LXX counterpart — ONE card with the LXX seam work; don't
  build a throwaway H→G map, wait for the seam.
- **Lexical-texture panel follow-ups:** LXX seam range-preservation (does the Greek keep esh's range at ~8%
  divergence?) · re-run `scripts/add_lemma_plain.py` so the Hebrew exact-match fast-path goes live again.
- **Curation / answer-shape redesign** — evidence list reads spammy; label thematic verses (Rom 14:5 on a Sabbath
  query) — DON'T drop them (Gen 1:26 divine council relies on that path); broad topics are thin. Small residuals
  (only if they bug JP): hub-verse weighting, residual framing lean, LSJ blurb has no citation after-check.
- **Shared AI "house style" voice snippet** — ONE core.py snippet with the VOICE only; LENGTH stays split by model
  (HARD sentence counts on Haiku, SOFT on Sonnet — Haiku overran the ceiling on a maximal chapter); do NOT convert
  `_PN_SYSTEM`'s hard cap. A prompt edit refreshes that category's cache (expected).
- **AI verse-synthesis revisit (umbrella, bank only — exhibits verbatim in `docs/claude/ai.md`):**
  1. **Divine-name drift** ("Yahweh"/"YHWH" vs ABP's "the LORD", Jer 46:25 exhibit) — JP rules ONE convention,
     then a prompt line PLUS a post-generation check (prompt-only drifts). Pairs with the voice snippet.
  2. **Unhedged contested assertion** — the 1Co 8:5 Connection panel states the Psa 82 "human rulers" reading flat.
     The HARD variant: it adjudicated a CITED passage, so a caution list keyed to the panel's own passage misses
     it. Open questions: contested-topics prompt instruction; hand-curated caution list; auditability (panels
     regenerate, exhibits vanish). **Start by diffing views_summary.py vs views_crossref.py prompts** — the Psa 82
     chapter summary hedged right.
  3. **Nimrod fidelity watch** — the synth READS ABP, so Gen 10:9 should keep ABP/LXX's "giant hunter", not KJV's
     "mighty hunter". Test live; if it says "mighty hunter", fix with a POSITIVE line in `_CURATION_SYSTEM` (+ mirror
     `_AI_SYSTEM_TMPL`) to use the supplied verses' wording — not a blacklist. Memory `project_ai_synthesis_quality`.
- **AI blurb verse-check cert** (SCOPED, not started) — make "verse-checked" a state a blurb can EARN;
  `docs/tickets/TICKET_blurb_verse_check.md` (incl. specimen #3, Num 33:45). Behind the Lexica batch tooling.
- **PD reference works** — Trench (NT synonyms) + Girdlestone (OT synonyms) are the standout; Thayer/Vine/Gesenius
  easy adds. PD commentaries = IMPORTED interpretation — only walled off + labeled "tradition, not the text".
  License caution: free text inside a not-free database wrapper — use original scans / known-free digitizations.

### Study tab — ON HOLD (deprioritized, JP 7/15; waits for JP to raise it)
- Study-on-mobile shell (Topics/Graphs/Seams still on the old `.study-mobile` branch; copy the three landed
  News/Ask/Notes commits; opener `docs/handoffs/HANDOFF_study_mobile.md`) · per-item inspect DETAIL (right
  inspect is ZoneEmpty everywhere; spec: Topics = clicked verse in context, Graphs = clicked claim/node's
  grounding, Seams = clicked fork's grounding). code: static/src/55-study.jsx
- **Study graphs bits:** mobile graph = narrate a traversal, NOT a shrunk chart — carry CONTESTED edges as a
  colored TAG, not fine dashes, or the map becomes a verdict machine · per-study lexeme strip · Strong's deep-link
  from a lexeme node · drop "Sin (1)/(2)" from `_COMMON`. code: argmap.py, views_study.py
- **Pointer click-through** — the ἵνα `contest_graph` breadcrumb + dikaioō `graph_ref` are plain text; thread an
  onOpenGraph callback (the `studyPending`/`openEntry` plumbing exists).
- **Published study topics shape AI-search answers** (divine council = test case: retire the hardcoded
  `_DIVINE_COUNCIL_*` one-off once a topic reproduces it). GUARDRAIL: only PUBLISHED text-first TOPICS feed an
  answer, never arguments; saved answers key on the topic's verse list.
- **"Loaded terms" series** (seven-slot skeleton; charis, baptizō, metanoia, ekklesia, hamartia, propitiation) —
  settle standalone Studies vs featured-in-Word-study first · **topic browser** (category names only, our own
  verses + summaries).
- `/api/study/for-name` route survival — separate decision from the Nave's data (see Owed checks).

### News — ON HOLD (JP 2026-10-31)
- **OPEN step (4) of the dedupe lane: `--fill-links`** for the 2,283 unlinked Google rows scored 5+ (mostly older
  than the 60-day page-date backfill), then re-report + apply. Rollback copy `~/db_backups/news.db.pre-merge-2026-10-25`.
  Left unmerged on purpose: 39 B1 sets (~25 different articles, 6 EWTN slug renames now 404, ~8 unreachable).
- **PARKED — re-enable the nightly archive backfill (`resolve_backfill_all.py`)?** Commented out of daily.sh since
  it crashed mid write-back on 2026-07-05 and corrupted news.db (`d6b8c310`). The journal-mode root cause is fixed
  (`bbbe0963`: every news opener uses DELETE), but turning the step back on was never decided. Until then
  Google-wrapper faces older than the 50h forward-fill window stay wrappers (still clickable). code:
  scripts/news/daily.sh, scripts/news/resolve_backfill_all.py
- **OPEN, look at when there is a gap (JP raised it again 11/23; not a work order, News stays on hold) — News page load is 70–150 s (measured 11/8, PA access log, Nov 6–8).** `/api/news/all` sends the
  WHOLE scored archive regardless of the page's 30-day default (30,207 rows, every score incl. below the 5 floor,
  with summaries): 53 MB of JSON, 10.7 MB on the wire (PA's front end already gzips — the access-log byte count
  is the gzipped size). Same-worker repeat 3.7 s; two loads abandoned by the browser (499). `_ALL_CACHE` is per
  worker and busts on every nightly pull. Not caused by any change since 10/31 (only request-path commits:
  Admin Stats, `d6df215e`/`dc2be0c0`).
  **Timed 11/8 on PA (console, live code, read-only):** card build 55.2 s = lexical `_cluster` on the 22,834
  unlabeled rows **51.4 s** (each row vs every group so far; 15,219 word-matched cards) + db reads 2.6 + the rest
  1.2; JSON encode 0.7 s. Grows faster than the archive: grouping only rows from the last 30d / 90d / 365d / all =
  1.6 / 9.0 / 28.0 / 55 s. Last 30 days = 2,503 cards, 4,105 articles, 3,403 of them below 5; sending that slice
  = 7.3 MB of JSON (1.2 MB if 5+ only).
  Options (scoped, not chosen): A) same-result faster `_cluster` (compare a headline only against groups that
  share words with it; gate = full card list identical before/after on PA + the frozen fixture) · B) build the
  cards once per nightly into a file all workers read (fallback: live build) · C) send only the chosen date
  range (reverses the one-fetch design; below-5 rows are 83% of the 30d slice — they feed the "buried" readout
  and the All-score filter). Timing script used: the 11/8 session's `~/news_timing.py` on PA.
  **Ruling (JP 11/8): parked, not opened. When it opens: A first; C for phones.**
- **PARKED — one story split across labels; the design has no merge step (11/8 one-week check).** The pope's
  mail-in midterm vote sits on TWO cards: "Pope Leo XIV US Election Vote 2026" (153 articles, made 10/31, the first
  night with the reuse check on) and "Pope Leo XIV US Midterm Ballot Request" (21, made 10/30, before it). Both still
  take new articles; the 11/6 "proud to be an American" remarks landed on both. Leo's AI encyclical is spread over
  ~7 labels (…AI Encyclical · …AI Encyclical Magnifica Humanitas · …Magnifica Humanitas AI Encyclical — same words,
  other order · …Magnifica Humanitas Encyclical Release · Pope Leo AI Encyclical 2025 · …Disarming · …Encyclical
  Quotes Release). The reuse check only blocks a wrong reuse; nothing joins two labels that already exist.
  Smaller likely twins: the two "Pakistan Blasphemy Laws…", the two "Young People Catholic…", "Pentagon UFO Files
  Release 2025" vs "…Skinwalker Files Release". Related: a refused article can get a misnamed fresh label — a 2015
  CNN piece on Francis's encyclical (id 30322) and a 2020 bishops'-conference video (29697) now carry "Pope Leo XIV
  … Encyclical" labels. The 153-article card itself was read in full: one event (the vote + coverage + reactions),
  not a catch-all. code: scripts/news/group_news.py
- **PARKED — a blank or partial AI reply in the nightly labeler is logged as a plain "no".** `_ask` returns an
  empty list when a reply holds no array, and `confirm_reuse` counts any headline missing from the reply as "not
  the same"; neither prints an ERR line (only a thrown error does). `fresh_labels` likewise leaves a headline
  unlabeled without saying why. So the nightly log can't tell a real refusal from an empty answer. Suspected case:
  11/6 — 13 reuses refused, all 13 left with no label, incl. six South America trip articles that later nights put
  on the trip card. Nov 1–8 log: zero ERR lines. Fix idea: count and print empty/short replies (no change to
  behavior). code: group_news.py `_ask`, `_read_array`, `confirm_reuse`, `fresh_labels` Web-log reads: PA writes the real client IP as a quoted field before `response-time=` — filter with
  `sed -E 's/^[^ ]+ //; s/"[^"]*" (response-time=)/\1/; s/key=[^ &"]*/key=HIDDEN/g'`.
  code: views_news.py `_all_cards` / `_cluster` / `all_news`
- **Corroboration as a rank input** (Aug 14 ruling, layer 3) — stays parked until labeler fusion is measurably down
  (`relabel_check.py --run`); otherwise it rewards falsely "well-corroborated" fused cards.
- **Admin's LIVE Keep/Dismiss squeeze the headline on a phone** (Kept rows ~148px / 5 lines) — pre-existing; "a
  control that works earns its row"; stacking actions under the headline = a design call on live controls.
  code: static/src/84-news.jsx `.news-actions`
- **Reader bookmarks** (review table is per-person, keeps feed nothing) · **shareable News deep link** (`/?view=news`,
  ideally per-story, survives signup; copy the `?news=`/`?b=`/`?lex=` pattern in 90-app.jsx) · **beast-arm badge**
  (thread→arm map isn't 1:1 — hand-authored by JP; code: views_news.py map, 84-news.jsx).
- Eyeballs when News returns: copy shortlist pastes clean links; a card title click lands on the real outlet ·
  paywall spot-check (FREE outlet as card face, 🔒 on the paywalled source, stable across presets) · News tab in the
  mobile bottom nav (admin) + News inspect balance vs the `.news-bar` row.

### Accounts, Ko-fi, licensing, non-canon, tests
- **Notes:** Apple sign-in (needs a paid Apple Developer account) · email campaigns / reading-plan mailings.
- **Ko-fi:** USER-SIDE — set up the monthly "Berean" tier + claim instructions in its welcome message · OPTIONAL —
  Ko-fi webhook → auto-set the berean role (cap stays 10). code: views_notes.py
- **Licensing:** the live page is `templates/seo/credits.html`, NOT CREDITS.md — keep both in step · optional
  thank-you note to OpenBible.info.
- **Non-canon:** possible next books (Jasher 1840 — beware the pseudo-Jasher; 4 Baruch; Apocalypse of Zephaniah;
  Joseph and Aseneth) · wire the `<book>_words` tables into the Lexicon/Search tabs once, generically (the
  "In the [book]" count + LXX link are HIDDEN since 6/11 because they dead-ended) · KNOWN GAP: no Hebrew/Aramaic
  interlinear for a non-canon text (G-number join + LSJ routing are hard-wired).
- **Web-route test coverage** — endpoint snapshot harness (`scripts/snapshot_endpoints.py`) + browser click-through
  are MANUAL, so routes/clicks aren't checked per push. The main test gap if you ever want to close it.

### Future projects (banked — JP raises; framing in memory)
- **Remove most em dashes from the site, except the Bible text (JP 11/23; not a work order).** In scope: page wording,
  labels, dictionary cards, AI answers and any other site-written text. Out of scope: the verse text and its `--` to `—`
  build form, which stay as they are.
- **Dataset publication with receipts** — after the Greek PN work completes (or ABP permission resolves): standoff
  annotation + receipts + errata upstream. Framing: memory `project_licensing_attributions`.
- **Genealogy-of-Jesus map** — the person-card tag navigates to a walkable lineage (both Mat 1 / Luk 3 lines, edge
  receipts). Framing: memory `project_metav_expansion`.
- **Grammar search** (search the morph tags — ~78% of ABP Greek, the Hebrew OT in full; engine + UI missing) — the
  biggest gap vs Logos base tier.
- **People/places hub + timelines** — a browsable "Factbook" (cards open only on a word click today) + timelines.

---

## Ideas / someday (nothing committed — grab whichever appeals)
- **Reach is the real gap, not features** — a one-person app few people know about; the missing piece is marketing.
- **Reader / layout:** word detail as a floating card · collapsing toolbar (lib-bar → one compact pill) ·
  chronological timeline scrubber · one smart search box (Word study + Ask, routes by what you typed).
- **Chrono Phase 2 — PARKED (JP wants eventually, not queued):** exact hand-curated per-reading dates; SUB-ERAS
  (Saul / David / Solomon — a range or a point); milestone labels ON the timeline track; a stitched single-scroll
  "today's reading". code: static/src/59-dayintro.jsx, 58-dayplan.jsx, 60-library.jsx
- **LXX transliterated-phrase pseudo-names** (Jer 46:17 "Saon Esbeie Moed") — no entity can ever bind; a
  hand-curated note table (likely a dozen cases) instead of the AI shrug. First step: enumerate unbound PN clicks
  with no TIPNR/metaV candidate. code: Fix-A fallback in views_metav.py
- **Map tab** (coordinates + map library already in place) · **meaning-based passage search** (needs a concept index).
- **More texts:** Textus Receptus NT (same numbering; showing where two Greek texts differ) · PD translations (ASV,
  YLT, Darby, Geneva) into Compare · Rahlfs LXX as its OWN parallel Greek OT, never a patch to ABP (LICENSE FLAG:
  CATSS/CCAT is not MIT) · fuller Greek morphology from CATSS / macula-greek (the ABP-native fill was SCRAPPED) ·
  dramatized KJV audio + verse-by-verse karaoke · extra-biblical texts as a separate section, never mixed into canon.
- **Dead Sea Scrolls** — wanted, hardest: no PD English, mostly Hebrew/Aramaic fragments (needs the H-number/RTL
  plumbing). Realistic first step: a 1QIsaa vs Masoretic variants COMPARE view.
