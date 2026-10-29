# TODO

Open work only. Finished and scrapped items (with the gory details) are in [TODO_ARCHIVE.md](TODO_ARCHIVE.md).
Each item may end with a small `code:` pointer for Claude to find the right spot — you can skip those lines.

Consolidated 2026-07-01 and again 2026-10-25: the DONE/SHIPPED write-ups live in the archive + memory;
this file holds genuinely-open work and parked ideas only.

---

## ABP source material — open (opener: `docs/handoffs/HANDOFF_abp_source_material.md`, status block)
Closed 10/25 → TODO_ARCHIVE: lane (1) abp_surface FILL (live 03:08, 4,411 writes, 391,130 → 395,003) ·
lane (2) MIXED 47 · the Hebrew-ABP reversal lane (withdrawn 10/24) · **the Concordance verse-list diff
lane** (read-only; 7,905 / 8,532 entries exact; record `docs/handoffs/CENSUS_abp_concordance_diff.md`,
parser reference notes in its appendix). No open writes.

- **NEXT SESSION, first candidate — the rebuild-trap fix** (the "fill does not survive a words
  rebuild" item below): its own session, census first.
- **Three WRITE-CLASS items came out of the Concordance diff — all DECIDED, not scheduled; each is its
  own checkpoint lane and starts with a PA row read** (which row carries the word, what it holds):
  (1) **152 label corrections** → filed under the held "540 + 13" item (Held list below);
  (2) **Concordance residue, our side: 25 slot errors + 10 split renderings** (item below);
  (3) **Split-rendering double rows, 628** (item below).
- Concordance leftovers, HELD, no action queued: 44 Concordance print inconsistencies (ours matches the
  Lexicon — κλοιός 2828.1/2827.2 16 · the 4951 family one dotted step low 19 · εἰ δὲ μήγε 1490.1/1490 7
  · 2 singles) · 16 label holds (5557.1/.2 5 · 2545/1572 2 · 9 single-verse, unsettled) · 3 unplaced
  refs (ἀπολύω 630 "Nm 33:title" · οἶκος 3624 Hos 6:14 · υἱός 5207 2Ch 1:43) · the Concordance-side
  residue classes (print errors, omissions, star errors, verse offsets — CENSUS §6).
- **Helper audit controls refreshed 10/25 but NOT yet re-run on PA.** The next run of
  `scripts/audit_helper_double_tag.py` should show 4 PASS: 2Ki 11:16 G2007 · Psa 69:21 G4222 ·
  Act 13:19 G2624 (A-review) · Rth 2:16 (B). Any FAIL = read before trusting its counts.
- (d) **English-Greek Index** — last of the purchased helps; not started.
- DECIDED, not scheduled — WRITE CLASS, checkpoint lane — **Concordance residue, our side: 25 slot
  errors + 10 split renderings.** 16 verses where the app has the number and its English is in our
  verse text but none of our rows carries the number · 9 starred verses where the app has the word 2+
  times as separate words and ours has 1 (Pro 5:7 ἄκυρος doubtful — the app also tags `μη` with
  207.2) · 10 "2+ with no `*`" verses where the app has ONE slot and ours (and `abp_texts`) carry two —
  the split-rendering shape; fold into that item at its census. **Precondition: PA row read of all 35
  before any write.** Rows: `abp_helps/adj_d_rows.tsv` (causes "our slot error…" / "split rendering
  (missed by a)").
- DECIDED, not scheduled — WRITE CLASS, full checkpoint lane — **Split-rendering double rows.** 628
  Concordance-verified verses where one Greek word carries two words rows with the same number (two
  English pieces, e.g. 2Ki 11:16 `they put | upon` G2007; Gen 24:41 `they should | give her` G1325).
  **174 outside-bracket** (first piece outside the bracket, no Greek position — on the helper audit's
  A-review list) · **454 both-inside-bracket** (each piece has its own Greek position — NO detector;
  the helper audit skips this shape by design). Counts inflate occurrences and the ≥2 check.
  **JP ruled a counting defect 2026-10-25** (the 7/9 polarity-A record had left split renderings
  alone as legitimate). A fix changes word rows → checkpoint before anything is written. List:
  `abp_helps/split_rendering_628.tsv` (git-ignored; columns book · chapter · verse · strongs ·
  headword · live_rows · shape · helper_audit_line). Evidence: `docs/handoffs/CENSUS_abp_concordance_diff.md`
  §5. The helper audit's controls were refreshed the same day (cured A exhibits retired).
  **Precondition: PA row read of all 628** (the 20-verse read was a sample) **+ a detector for the
  454 both-inside-bracket shape** (none exists) before any write. Plus the 10 residue verses above.
- CLOSED 2026-10-25 — **after the 2026-10-25 live rebuild: step 11 CLOSED (354,946 normed, finder check
  PASS) · step 10 CLOSED (IDENTICAL, unchanged) · step 7 CLOSED (items 1–3 on data, JP-accepted; 1Ch
  13:10 seen by JP in Chip + Interlinear view) — receipts charter §10a.** (Archive at next /wrap.) Original note: The rebuild
  swapped live at 18:06 (rebuild-trap fix proven — TODO_ARCHIVE 2026-10-25; receipts charter §10;
  rollback `~/bible-db/bible_pre_trapwire_swap.db`). Step 7 = served spot-checks (Eze 31:9, 1Chr 1:1,
  1Ch 13:10; also Jer 51:41 Σεσάκ). Step 10 = `build_two_ending.py` paste + local app.js rebuild.
  **Step 11 = `build_rendering_norm.py` — live-relevant:** the build never writes `english_head_norm`
  (`build_words_from_abp.py:2154-2157`) and the finder only checks the column exists
  (`views_lexicon.py:100-108`), so by code trace the ABP English finder matches NOTHING until it runs
  (predicted 0 / 626,309; live read pending). **JP RULED (charter §10a):** order this run 11 → 7 → 10;
  step 11 never within 60 s of a reload; step 10 diffed vs `00b-two-ending.jsx` first (identical → no
  paste/deploy, record "unchanged"). Steps 10 + 11 RE-HOMED onto the copy in `/rebuild-words` (after
  8b, before 9) — this run is the recorded exception. Opener lines added to `build_rendering_norm.py`.
  Start at `docs/handoffs/HANDOFF_rebuild_trap_fix.md` (held items 9, 11–13).
- CLOSED 2026-10-25 — **reader deep-link request loop — LIVE DEFECT, dated + reproduced; FIX DEPLOYED
  10/25 19:48 (`0d5ea43a`); JP's `?b=` private-window test landed on 1Ch 13 and stayed — lane closed
  (JP).** (Archive at next /wrap.) Found during step 7 (charter §10a): `/?b=1Ch&c=13&t=abp` on live
  had the browser attempt 56,000+ `/api/chapter` requests (1Ch/13 ↔ Gen/1) until the tab closed — most
  failed inside the browser and never reached PA (see the access-log read below).
  **Reproduced locally, no database** (scratch harness modeled on `tests/mobile_harness.js`: real
  committed bundle per git rev, fetch stubbed in-page, books = Gen/Exo/1Ch/Mat; each case alone in an
  iframe from a blank page, 2.5 s): first visit, no link → 1 chapter request · returning visitor + link
  → 2 · **first visit + link → 14,685 (phone width) / 9,171 (desktop) — loop** · bundle at
  `bc47330c^` + link → 2 · bundle at `bc47330c` + link → 14,483 — loop. Live serves the tested bundle
  (`static/app.js` unchanged `a1998f0e..HEAD`).
  **DATE: introduced by `bc47330c` (2026-06-28, "keep the reader's panels + marker in step with
  navigation") — NOT the 10/25 swap.** The loop's only inputs are the bundle, the book list and the
  browser's saved state; the swap changed only bible.db (the book list is not rebuilt).
  **Trigger:** a browser with no saved book list (`lexica.books.v1` — a first-ever visit) arriving
  on a `?b=…&c=…` link — i.e. a new visitor clicking "Open in the interactive reader" on a crawlable
  `/read/` page (`views_seo.py:_reader_link`). Returning visitors don't loop. Width doesn't matter.
  **Mechanism (code trace, matches the repro's Gen/1 ↔ 1Ch/13 pattern):** with no cached list the
  reader starts with no book; when `/api/books` lands it defaults to Genesis 1 (`60-library.jsx:240`)
  in the same render where the jump effect (`:380-429`) sets 1Ch 13. The position report
  (`:439-442`) tells App "Gen 1"; App's `handleReaderPos` (`90-app.jsx:188-192`) sees it doesn't
  match the jump and REPLACES the jump marker with Gen 1; the jump effect follows the marker back to
  Gen 1 while the report of 1Ch 13 replaces the marker again — each side chases the other one
  render behind, forever, one chapter fetch per swing. Returning visitors are safe because the
  reader reports its saved spot BEFORE App sets the jump (child effects run first), so the jump
  arrives last and wins.
  **Impact read (JP, PA, 19:35, read-only — any IP-minute with ≥100 `/api/chapter` requests over ≤2
  chapters, counts only):** PA keeps logs back to **16/Oct only** (files .1 → .9.gz; no .8), so
  June–mid-Oct is unmeasurable. Hits: **20/Oct — 1 visitor, 2 minutes, 423 requests · 25/Oct — 1
  visitor, 1 minute, 242 requests** (the latter very likely CC's own step-7 test). Per-visitor server
  volume is far below the browser's attempt count (the browser runs out of request slots first).
  Not confirmed: that the 20/Oct visitor was this loop (chapters/referrer/agent not yet read).
  **Fix (JP gate cleared 10/25; committed with this entry):** `60-library.jsx` — while a jump lands, the
  position report skips the spot it is leaving (`jumpFromRef`); harness: every first-visit + link case
  2 requests (phone/desktop, book list fast or 600 ms late), returning/no-link unchanged, page turns
  after landing normal; 10/10 Node gates pass.
  **Deploy receipt (JP, PA, 19:48–19:59):** deploy.sh 7b4b5e95 → `0d5ea43a`, invariant tests passed,
  API reload, sweep 200 ×5 · health_check after the 60 s wait: 0 errors, 1 warning = the damaged
  10/24 backup (own item below; unrelated) — no "locked" lines · **bundle sha256 on PA disk AND as
  served by `/assets/app.js` = `f939f4d0…8ce5e1` = the committed blob (CC, `git cat-file`) — MATCH.**
  Still owed: JP's navigation-only check in a fresh private window, then his `?b=` link test in a
  private window (cleared to run on the hash match). Rulings: fix ships in the same deploy as step 10's paste
  (if any); never reproduce against live; `docs/claude/frontend.md` "jump's translation is ONE-TIME"
  section names this deep link as one of the two `libNav` producers. Step 10 came back IDENTICAL
  (10/25) — no step-10 deploy exists, so a fix deploys on its own.
- CLOSED 2026-10-28 (found 2026-10-25, post-deploy health_check) — **a bible.db nightly backup was DAMAGED:**
  `[WARN] backup DAMAGED (gz): bible.db.20261024-133029.db.gz` — "Compressed file ended before the
  end-of-stream marker was reached" (the .gz is cut short). Sweep: 62 backups checked, this 1 damaged
  (the newest nightly passes; the swap rollback `bible_pre_trapwire_swap.db` is a separate file).
  bible.db keeps only 3 nightlies (`backup_db.py` `KEEP_OVERRIDE`), so one of the three is unusable.
  **DIAGNOSED 10/25 (side lane, JP PA read):** the 10/25 13:30 nightly ran out of quota while
  gzipping the 10/24 copy (`backup.log:1776` `gzip skipped … [Errno 122] Disk quota exceeded`; the
  .gz is 107 MB vs 10/23's 147 MB, stamped 10/25 13:33, still writable = the failed path). It could
  not predate 10/25 — the newest copy stays uncompressed until the next run. A one-off, not every
  run: `_rotate` only cut a file short when the write itself failed, then left the stub, kept the raw,
  and stamped success (same on 7/2 + 7/6 — log lines 112, 181). **The uncompressed
  `bible.db.20261024-133029.db` is present and good** (quick_check ok, verses 31,237 = its .info) —
  JP ruling: it stands as the 10/24 backup. **Fix `61cc9bdb` DEPLOYED 10/25 (JP, PA 20:11–20:23):**
  deploy.sh tests passed, API reload, sweep 200 ×5, HEAD 61cc9bdb; the new test passed on PA's own
  Python; health_check: freshness OK, the one expected damaged-gz WARN, 62 swept / 1 damaged. The fix:
  `backup_db.py` compresses to `.gz.part`, forces it to disk, reads it back in full,
  then renames; a failure removes the partial, keeps the raw, and FAILS the run (no success stamp →
  freshness alarm); a raw + .gz pair for one stamp now picks the raw. Test
  `tests/test_backup_rotate.py` (both test lists): 25/25 on the fix, 12 FAIL on the old code.
  **OWED after the 10/26 13:30 UTC nightly (JP ruling: no manual delete, the nightly replaces it):**
  read-only check — 10/24 .gz present, read-only (`-r--r--r--`), ~140–150 MB, dated 10/26 13:3x, 10/24
  raw gone, 10/23 gone, `last_success` 10/26, log `All backups verified ok.` with no `XX`, sweep
  `all intact`. Then update the keep-list line that calls the 10/24 nightly damaged, and check the
  `~/rekey/pre_rebuild.db` condition (a nightly after the 18:06 swap passing the sweep). 10/27
  nightly ages the 10/24 stamp out (keep 3).
  **CLOSED — JP PA read-only check 10/29 02:56 UTC** (run after the 10/28 nightly, so the 10/26
  picture above was overtaken; the 10/24 copies have aged out, so they can't be checked directly).
  On disk: `20261026` .gz 147,705,483 B stamped 10/27 13:34 and `20261027` .gz 147,707,480 B stamped
  10/28 13:34, both `-r--r--r--`; `20261028` raw 443,256,832 B; no raw left beside either .gz; no
  10/23–10/25. That is the fixed compress step working on two nights in a row, full size (the damaged
  one was 107 MB). `last_success` 2026-10-28T13:34:38; log `OK  bible.db … 443.3 MB` +
  `All backups verified ok.`, no `XX`; health_check `backups swept … 61 (all intact)`, no DAMAGED.
  **Alert email proven end-to-end (JP inbox, 10/29):** the nightly `--email --only-warn` mail for
  10/25 23:53 UTC carried `[WARN] backup DAMAGED (gz): bible.db.20261024-133029.db.gz` (+ the disk
  line, 83% then) — the only nightly that could see that file. Detection, mail-on-warn, delivery all
  work, so a silent night = clean. (Its sweep count read 55 vs 62 at the 20:2x manual run; cause not
  traced — the count is just files present, does not touch the proof.)
- HELD (JP 2026-10-25) — **re-scope `/rebuild-words` step 7**: it is written as a rendered-site check;
  mark which items are data-checkable (Eze 31:9 binding, 1Chr 1:1 identity H121 + metaV bind, Sheshach
  headers — all read through the site's read-only endpoints on 10/25) and which must be SEEN (1Ch 13:10:
  Library, ABP — **Chip view reads "the LORD was enraged"** (English order, no bracket marks/digits since
  2026-07-04 `9ff47f00` + `7b7fc505`); **Interlinear view reads "[²was enraged ¹the LORD]"** (ABP's
  printed order + marks). Both SEEN by JP 10/25. CC first wrote this backwards from a pre-July build
  comment without reading the renderer (`59c-library-render.jsx:360-395` chip, `:834` interlinear) —
  checklist line + build comment corrected 10/25). Also: say "card shows H121", not "→ H121" (the word row is G76
  since R-2), and never reach the reader through a `?b=…&c=…` link until the deep-link loop is fixed.
- HELD (JP 2026-10-25) — **`build_rendering_norm.py` loose ends** (census of steps 7/10/11):
  (a) its "recomputed N" line counts rows TOUCHED, not changed — a re-run never reads "0 to do";
  (b) the printed undo `ALTER TABLE <t> DROP COLUMN <c>` (`:17`, `:111`) does not work — SQLite refuses
  to drop an indexed column (`idx_words_ehnorm`); fix the text; (c) `--stats` has no change preview
  (counts only); (d) the finder caches "column exists" per worker (`views_lexicon.py:97-108`) — after
  any column drop, a reload is needed or the finder errors; (e) step 11 must always be given an
  explicit path — default is `bible.db` in the current folder, and a bad path creates a new empty file.
- HELD (reviewer 2026-10-25) — **header gate A/B re-scope for full rebuilds.** `gate_greek_header.py`
  A/B were built for the 7/30 header-only lane and ABORT on any full rebuild. Overridden for the
  10/25 run ONLY; the next full rebuild needs its own ruling, member by member, until re-scoped.
- HELD (reviewer 2026-10-25) — **`surface` vs `lemma-only` header label.** The 2 Sheshach rows went
  surface → lemma-only at the swap (accepted). Trace what the label changes on the card, and whether a
  header that matches the page should carry `surface`.
- HELD — **snapshot staleness:** a restore that moves slots makes the frozen fill snapshot stale for
  the next rebuild; a re-freeze needs a "before" side other than the 10/25 pre-fill copy (which stays
  on PA until one exists). Gates the edition-upgrade lane.
- RECORD — reason 5 unreachable under the re-key's current keys (rebuild-trap charter §6).
- SMALL — `health_check.py` gives false "database is locked" in the minutes after a deploy (5 s
  default wait; workers' warm-up writes the AI cache — ops.md) · the build's closing text calls its
  source "live" (with a copy as source, its printed swap command would move the copy and reload the
  site) · two old `bible_pre_pnstar_*` copies (~824 MB) beyond ops.md retention rule 1.
- HELD (leftover, not a gate) — **header landing `->surface` 461 vs its receipt's 451 (10 rows).**
  The 2026-09-06 Greek-header landing moved 461 identity rows into class `surface` (lemma-only→surface
  421 + none→surface 40; JP-run read 2026-10-25, 9/6 formlane vs hdrlane backups in `~/db_backups`),
  but `docs/handoffs/HANDOFF_gateB_enumeration.md` §"Expected picture" receipts `->surface` 451. The
  class totals reconcile exactly; the 10 rows are unattributed against that receipt. Read the members
  against the handoff when the header lane is next touched.
- OPEN — **rebuild order: the name-header build reads abp_surface before step 9 rebuilds it.**
  `/rebuild-words` 8b.3 runs `build_pn_greek_identity.py`, which takes name-slot forms from
  `abp_surface` joined on (verse_id, position) (`build_pn_greek_identity.py:292-305`, `:374-378`);
  step 9 rebuilds that table later. So on a rebuild the headers come from the PRE-rebuild surface
  table matched to the NEW positions (and, while the fill is live, from fill forms too — 2 headers
  already equal a fill form at their slot, census §5 Q7). Same shape as the 8/8 glued-header
  incident (`HANDOFF_form_lane.md:25`). Filed out of the rebuild-trap charter by JP ruling 10/25.
  Read-only census first (which headers would change, by member) before any reorder.
- DECIDED, not scheduled — **edition upgrade to the app's English** (English words differ
  in 29% of paired verses). No charter yet. Gated on the rebuild-trap fix above (JP 10/25) — its
  own item, not part of that fix. **That gate CLEARED 2026-10-25** (trap fix proven on the live
  rebuild). Still gating it: the snapshot re-freeze (a slot-moving restore makes the frozen fill
  stale) and the header gate A/B re-scope. First scoping step (JP 10/25 close): date the app's edition.
- **Rollback copies:** `~/bible.db.pre-surface-fill-20261025` + `~/bible.db.pre-xref-fix-20261024`
  stay until a nightly bible.db copy in `~/db_backups` is stamped after 2026-10-25 03:08 and
  verified (`ls -lh ~/db_backups | grep bible`; nightly ~13:30 UTC). Then the older copy can go.
  **Condition MET 10/29** (10/26, 10/27, 10/28 nightlies all pass the sweep) — `~/bible.db.pre-xref-fix-20261024`
  **DELETED by JP 10/29 03:06 UTC** (423M, `rm -v` confirmed; home now 6.0G by `du`).
  **The fill copy stays until a re-freeze exists** — it is the frozen snapshot's only "before" side
  (rotation/single-rollback rule does not apply to it). Also on PA (10/25 live rebuild):
  `~/rekey/pre_rebuild.db` — **condition MET 10/29, DELETED by JP 10/29 03:06 UTC (423M)**: three nightlies
  dated after the 10/25 18:06 swap (10/26, 10/27, 10/28) all pass the backup sweep (JP ruling 10/25
  required a PASS, not just a later date; the damaged 10/24 copy has since aged out) ·
  `bible_pre_trapwire_swap.db` = the rollback of record · two `bible_pre_pnstar_*` (~824 MB)
  deletable as their own step.
- **Held list** — read-by-hand, no writes queued. Full rows: the handoff (lane (a)'s "Same slot,
  different number" entry + "Also open from 10/24") and `docs/handoffs/CENSUS_abp_surface_fill.md`.
  - **540 + 13 same-slot number disagreements** (app vs ours, after swaps; the 13 are from the fill
    census; **Isa 39:8 pos 1 = suspected slot misalignment**). The 540 still need the audit to write
    them to a TSV. **+ 152 candidate corrections from the Concordance diff (b), 2026-10-25:** verses
    where the Concordance's number matches the Lexicon and ours doesn't (18 repeating pairs = 86
    verses, incl. ἔνθεν 1759.3 → 1759.2 ×28 — four of which are already in the 13 — + 66 singles whose
    row is not yet proven). List: `abp_helps/adj_b_pairs.tsv` / `adj_b_verses.tsv` (verdict
    "concordance-right"). **DECIDED, not scheduled; checkpoint lane; precondition: PA row read of all
    152** (which of our rows carries the word — unproven for the 66 singles) before any write.
  - **191 name slots with no printed form** — the Analytical Lexicon carries no proper names, so it
    resolves none of them (lane (b) join: name 0 of 191).
  - **30 vs 27 glued names** — pn_greek_identity has 30 NBSP names vs the 27 pinned (audit C3 still
    PASSES: it checks the 27 are present). Extras seen: Act 12:19 pos 0 'Ηρώδης δε', Act 13:1 pos 24
    'Μαναήν τε'; the third was cut off by `head -8` in the 10/24 paste — re-read the full
    `~/abp_app_audit_rerun.txt` C3 block.
  - **Baal 1Ch 5:23 (H1179).**
  - **28 English-in-Greek cells** — English notes typed ENTIRELY in Greek letters ("δαγγερ" =
    dagger, "- Φορ τηε ενδ.") pass the app audit's English-font check (it looks for a Latin letter).
    The 10/25 fill HELD all 28 (class E2), so nothing wrong was written — but **the audit check
    itself still has the gap; fix it before the list feeds another write.**
  - **33 unlisted forms** — filled, LEMMA held (some look like app typos — ανέστραπτεν,
    επίβλεψεν — unchecked).
  - **3 app letters with no ruling** — Num 12:3 pos 5 · Pro 14:30 pos 0 ('=' for ΰ) · **Psa 60:0
    pos 22 (app prints Ἰωάβ on a 1473 slot — suspected slot misalignment).**
  - **4 split conflicts** — 2Ki 20:12 pos 19 · Jon 1:17 pos 9 · **Eze 7:4 pos 13 + Dan 9:5 pos 14
    (suspected slot errors — Dan 9:5's 4675 slot holds the article 'των')** — **+ Isa 41:14 pos 3**
    split-ambiguous.
  - **Deu 4:45 pos 10/11** — the two sources disagree (ours Μωυσης, app Μωυσής).
  - **60 plain-η spots** where the app prints ἡ and our form has η with no accent (control E1 —
    outside the fill; likely the article ἡ / ἡμ- words, not checked; the rows are in
    `~/abp_app_dump.tsv`, not pulled yet).
  - **23 + 3 unflagged glued splits** — of the 1,420 unflagged glued values: 23 split-eligible + 3
    two-word names (Ezr 10:30, Neh 10:14 Φαάθ Μωάβ; Jer 39:3 Νήργελ Σαρασάρ) held for a later pass;
    the rest no action.
  - **1,823 written slots with an empty words.lemma** (no lemma write in the fill lane).
  - **(h) `/api/lexicon/books` not bridged** — full entry under "ABP-tab routing follow-ups" below.
  - **MIXED 42 names** (from the answered MIXED 47) — HELD: the Concordance has no verse lists for
    names; need another source.
- Left open, no lane: the stale 'none'-label cleanup (rides the next identity rebuild — R-2
  residue below).

## Greek header / form lane — leftover follow-ups (arc CLOSED 9/6 → TODO_ARCHIVE)
- **20 glued-blanked rows** (ruling 3, 8/24): they previously showed a (garbage) word-hint and now
  show English — decide downstream whether any deserve a real header (hand-table door). Members =
  the 13 + 7 in the 8/24 session record (`docs/handoffs/HANDOFF_gateB_enumeration.md`).
- Teach `audit_surface_coverage.py`'s stored-vs-live control the backfill sum (its MISMATCH
  warning is now a permanent false alarm on any backfilled table).
- Gentilic `is_pn` check: Gen 39:17 & 41:12 "hebrew" slots — joins the 8/7 gentilic follow-up.
  **8/24 add: "midianitish" (Num 25:15) is a people-word `er.is_people_group` does not
  recognize** — predicate gap, fix belongs to that follow-up (changing it changes builder output,
  so never mid-lane).
- Mat 9:35 scrape typo `Ισηούς` → corrections-lane citation; Mar 2:8 / Mar 14:66 variant forms =
  hand-table door candidates.
- **PA disk housekeeping (small):**
  - Disk thinning filed 8/23: `bible_test.db` (Aug 4 — JP rules), one of the two in-repo
    pre_pnstar copies (evidence twins stay in `~/db_evidence/`); `~/bible-db/bible_hdrlane.db`
    was kept for diagnosis at 8/23.
  - WAL crumbs (zero-risk): orphan 0-byte -wal/-shm companion files sit in ~/bible-db
    (bible_test.db-wal, bible_test_scratch.db-*, proseonly.db-* — two with no parent file). Repo
    grep 2026-07-31: NO script opens WAL (all hits are the anti-WAL guards), so the crumbs are
    historical/ad-hoc; check their file dates, then delete.

## ABP corpus certification audit — ARC CLOSED (Tier A certified + live)
S1–S11 record → docs/audits/AUDIT_abp_certification.md + docs/CHARTER_cert_session9.md + docs/audits/AUDIT_entity_seam.md +
memory project_abp_certification + TODO_ARCHIVE 2026-07-31 consolidation. Open leftovers only:
- **verify_prose_leak.py "Tier B applied" mode** — parser-only check FAILs-that-isn't on the 5
  Tier-B prose verses when run against a finished scratch; next rebuild shouldn't re-derive this.
- **lint_split_wrong_slot.py stale label** — hardcoded `RECONCILE … (sizing: 18,339/12,692)`;
  bump to 18,384/12,718 (the real post-S11 scope; both harnesses agree).
- **Phrase-gloss under-distribution (671, fix (g) deferred):** adjudicate a sample of the
  "not+verb" class vs the ABP app (defect vs ABP negation convention), then distribute true
  defects dual-ordering-style. Detector = scripts/audit_phrase_gloss_underdist.py.
- **Trailing-clause float set copy-pasted in 6 live places** (build + 4 render + port) — unify
  to one shared definition so they can't drift. Repo hygiene.
- **Stump filter leak** (low): lint_split_wrong_slot's stemmer stump filter misses sibling forms
  with count <3 (sid/com/rott); fix if the filter is reused at scale.

## R-2 residue (ticketed at close, 2026-07-26 — none blocking, JP raises)
- **Gentilic/people-class Greek backfill** — the named candidate that retires the kept-Hebrew
  ('none'-class) rows in pn_hebrew_xref (C3-Q1 condition b; 3,380 at the 7/26 close, 2,454
  at the 8/6 re-declaration — of which 498 are stale-label, item below). Adjacent to pile U.
  Related but distinct: the 2,358 PN printed-Greek residue (TICKET_pn_lemma_residue.md,
  stamped 2026-07-28 — scrape-based recovery CLOSED by ruling; needs a new source).
- **Frozen 'none' class gone stale after the 8/23 form lane (found 2026-10-24, JP-run
  read-only).** pn_hebrew_xref's class was set by `retire_hebrew_identity.py` (last run 8/6,
  copying `pn_greek_identity.source`); identity was rebuilt after the form lane refilled
  printed forms, the retirement was not. Frozen 'none' vs identity now: none→none **1,956**
  words / 279 numbers · none→lemma-only **458** / 100 · none→surface **40** / 7. Total 2,454 =
  the 8/6 declared 'none' count exactly (control). So **498 words** sit in a state the rule
  no longer gives them: words still carry the H-number, xref still says 'none'. Example:
  H1908 Hadad 1Ki 11:18/19/21@22/25, 1Ch 1:47/51 (identity lemma-only, forms Αδάρ/Αδάδ).
  Not traced: what (if anything) a reader sees from it; after lane (f) all such rows light
  either way. Catch-up = re-run the retirement on a copy; its declared split will no longer
  match, so it halts and needs a re-declaration (precedent: RECLASS_catchup_declaration.md,
  8/1). Live data write → full checkpoint lane, own cycle. **JP 10/24: rides the next identity
  rebuild, no lane before then.** Don't fold with the gentilic
  backfill above (that retires the genuine none→none people-class rows).
- **Binder Greek-key bases extension — PARKED BY RULING** (would fire novel binds; own gates
  when raised). Record: PLAN_r2_stage3.md charter amendment.
- **Lexica-minted PN numbers — DEFERRED by ruling** (TICKET_lexica_pn_numbers.md): revisit
  only if a concrete need survives a few weeks of lemma-keyed Word study.

## Lane-③ close-out residue (2026-08-07, reviewer-queued — own cycles, JP raises)
- **②-pass gap census (chip/interlinear ordering):** the PN-star pass's 194 cross-blank
  B-writes left the interior blank slot OUTSIDE the new bracket; chip/interlinear group
  only consecutive same-bracket runs, so those verses likely mis-order there today
  (lane-③'s gap-fix proved the mechanism + the one-column fix; prose unaffected).
  Needs a read-only census, dry-run, reviewer ruling.
  code: scripts/lane3_star_gapfix.json (the fix shape) · groupForGreekMode in
  static/src/56-library-order-logic.jsx (the grouping rule)
- **Possessive PN card header shows the head-form ("Davids"):** the card's form-name line
  title-cases `english_head` — a normalized lookup key (lowercased, punctuation stripped),
  not display text — so `David's` renders "Davids". Verse text + bio panel are correct;
  fix is display-layer only: render the PN entry's canonical name (person card → "David")
  or re-title-case the raw english, never the head. Words-table data is correct and closed.
- **Gentilic PN cards read as places:** MetaV name-match maps a people-word to its region
  (Assyrians → Assyria map pin). Reviewer-ruled keep, but the card should say
  "people of [region]" rather than presenting as a place. Polish, not a defect.

## Library translation-tab sync + Word-study ABP-tab routing — open residue
Tab sync SHIPPED + VERIFIED LIVE 2026-08-09; ABP-tab routing SHIPPED 2026-09-06 (record
`docs/tickets/CHARTER_abp_tab_routing.md`). Both full records are in TODO_ARCHIVE; the standing
nav invariant is `docs/claude/frontend.md` → "Navigation / jumps". Only the open residue stays here:
- **QUEUED, own session (reviewer-approved 2026-08-09): the consumed-jump refactor.** Treat a
  jump's `translation` as a one-time instruction that is CONSUMED once applied, so no later
  re-send from anywhere can re-assert it. That is the real cure for all three sites (search
  jump, page turn, version switch), each of which currently strips by hand at its own emit
  point. Kept out of the papercut fix on purpose — it touches the load-bearing nav effect.
- **LOW-PRIORITY UI LEGIBILITY (JP decides if/when):** unselected translation tabs read as
  disabled. `.seg-b`'s selected state is a white pill, so the others look greyed beside it —
  it fooled JP AND the reviewer in the same session, so it will fool a visitor. Wanted:
  unselected tabs that still read as clickable. **Do NOT "fix" it by graying for real**, and
  it is a visual change, so it needs JP's yes on the specific change.
  code: static/src/59b-library-nav.jsx:178
- **OPEN, 30 seconds, never done: map the REST of the PN card's outbound links.** Today only
  the occurrence links were checked (all go to Word study, `30-detail-panel.jsx:1383-1505`).
  Nobody has confirmed where the others go. Read-only.
- **ABP-tab routing follow-ups** (routing routes a grey Greek number through its folded header only
  when the header lane vetted it — Galilee 73 · Damascus 63 · Arabia 12 · Salem 4 · Euroclydon 1 ·
  Abaddon 1; one held name, Israel, still grey; f, g closed 10/24 → TODO_ARCHIVE):
  (a) Zion 168+1 and Aram 12+5 — header lane folds the lemma-only residual, then they route with no
  code change; (b) Israel 2,584 / Jerusalem 753 — HELD, route only via the header lane's `surface`
  class, never a lemma-only door (reviewer-refused 9/6); (c) MIXED 47 — ANSWERED 10/25 → TODO_ARCHIVE;
  the 42 held names sit on the ABP held list at the top of this file; (d) collisions γαζα
  G1047/G1048 · ηλι G2241/G2242 refused by rule;
  (e) **Word-study results sidebar lists only ONE KJV rendering** (galilee shows 62, the card's
  "galilee, for" line and the KJV tab say 63) — display finding, own item;
  (h) **`/api/lexicon/books` has no bridge branch** (JP-spotted 10/24, predates tonight): for the
  6 bridged names its ABP answer is empty. The page's book list comes from the profile (which
  IS bridged), so nothing wrong shows; but clicking a rendering chip calls this endpoint to
  narrow the books, gets nothing, and quietly shows the unnarrowed list. Fix shape: the same
  `_bridge_if_grey` → `_pn_lemma_rows` door the verses endpoint uses. Low stakes — a bridged
  name has essentially one rendering. **JP-checked 10/24:** `books/G1056?corpus=kjv` IS populated
  (John 17, Matthew 16, Luke 15 …); only ABP and the no-corpus default come back empty — (h)
  stands as filed, nothing extra.
- **The `PN:<form>` name-form lane sends one list entry per hit** (filed 10/24, NOT lane (f)), so a
  verse where the name appears twice shows as two rows with the same key
  (`_pn_lemma_rows` → `lexicon_verses` PN branch; the bridged All-books/one-book branches share
  it). Fix shape when raised: one row per verse carrying all its slots, as lane (f) did.

## PN entity-data follow-ons (2026-08-09, from the panel-ticket eyeball — data, not display)
- **Joram/Israel is TIPNR-only** — the card is honest and now correctly shaped, just thin
  (no MetaV kin/tribe). Candidate for the entity-data backfill bucket, explicitly OUT of
  scope of the display tickets by ruling.
- **Israel place-entity question:** the person card serves nation/land mentions. Same bucket;
  related to the eponym both-senses work already banked below.

## Open word-study / data issues (low priority, none gating)
- **Greek text search over the ABP Greek line — FEATURE QUESTION (JP hit it 2026-07-29
  searching κύριε in Library).** The Library in-text search is English-only by design
  (views_search.py, verses.text); a Greek query can never hit — not a defect, a missing
  door. If ever built: (a) it MUST compare accent-insensitively both sides (greekFold /
  the abp_surface stripped-Greek characteristic, docs/tickets/accent_divergence.txt) or
  it inherits the 4,250-row false-miss class; (b) related but separate: Word-study search
  doesn't resolve INFLECTED forms to their headword (κύριε -> κύριος). This was merged
  (reviewer 2026-08-09) with the Word Study greyed-ABP ticket as one "fold first, route second"
  ticket; the Galilee/names half SHIPPED (header lane 9/6 + ABP-tab routing, record in
  TODO_ARCHIVE). **The κύριε half is still open and has its own door:** ABP's own printed forms
  already sit under G2962 (κύριε 663 · κυρίου 2422 · κυρίω 832 · κύριον 591), so it needs no
  form-stripper — but matching MUST ignore accents both ways (reuse the existing normalizer,
  don't write a second one; accent-variant rows like κυριω are in the data). The wider
  multi-form-name class rides the Greek-header hand-table polish item below. Neither is queued;
  JP raises. (c) Cheap UX honesty fix, independent of
  both: when the Library search box is handed GREEK characters it returns a bare
  "No matches" — which reads as "this word isn't in the Bible" rather than "this search
  is English-only." It should say so (reviewer-ruled note 2026-07-29).
- **Bracket-digit sweep: 2 PARKED verses, own rulings owed** (lane otherwise CLOSED
  2026-07-28/29, record docs/tickets/bracket_digit_sweep.txt + TODO_ARCHIVE): Act 10:28
  (official app splits the clause into TWO bracket groups vs our one — structural remap) ·
  Num 19:2 (our gloss 'is not' vs app 'has not' — no clean digit mapping). The Van der Pool
  errata list compiles from that ticket once these two are ruled or formally deferred.
  Template note: the marker-permutation sweep, if ever run, inherits the sweep pattern
  (precondition-pinned rows, intent evidence per flagged group, same door).
- **25-name disambiguation-candidate lane (PARKED, banked from the TIPNR widening close-out
  2026-07-30).** These 25 names each have ONE metaV person but 2+ real TIPNR people, so the
  guard now correctly declines their unbound card ({"ambiguous":true}) — source-verified
  genuinely distinct people (Nahum the prophet vs Nahum in Luke 3:25's line, two Salomes,
  two Achsahs…). They are the natural first customers of a future multi-entity card
  treatment (same territory as Elijah's 4): Achsah, Alemeth, Asriel, Calcol, Eder, Hakkoz,
  Hanniel, Harbona, Hotham, Ishmaiah, Izhar, Jaasiel, Jekamiah, Joiada, Joshaphat, Mahlah,
  Mehetabel, Nahum, Palti, Rab-saris, Salome, Sharezer, Shemer, Zattu, Zerubbabel.
  Wait for JP to raise it.
- **AI blurb verse-check cert (SCOPED, not started — JP + reviewer 2026-07-30):** make
  "verse-checked" a state a blurb can EARN. Ticket with the check design, two open doctrine
  questions (cross-reference attestation; failure policy) and the cert template:
  docs/tickets/TICKET_blurb_verse_check.md. Sequenced BEHIND the Lexica-dictionary batch
  work (borrows its tooling); waits for JP to raise it. Interim reword SHIPPED same day:
  caveat now reads "AI-written summary — claims not verified against the verse text"
  (rides next deploy).
- **340 identity slots with no words row (lane-2 2026-07-29, DIAGNOSED, fix DEFERRED by
  reviewer ruling).** All 340: source class 'none', position-hole INSIDE an otherwise
  normal verse — NOT the 345 no-name slots. Reads as none-class rows stamped from a stale
  position map. RULING: cert territory — scratch-db + pre-registered gates when picked up,
  NEVER a live patch. Clue: NT-heavy skew (Joh 73, Act 33, Mat 30). Tool:
  scripts/audit_pn_lanes.py lane 2.
- **"Field" oddity (flag only):** capitalized common word 'field' (Isa 29:17 al.) serves a
  metaV PLACE card via name match — pre-existing quirk surfaced by the lane-1 dump.
- **Star-slot G-number question (vocative-O residue, own ruling owed):** the served identity
  for star name slots like Jer 15:5 Ιερουσαλήμ is lemma-only/no-number while a real Greek
  number (G2419) exists in the lexicon — an R-2 identity-rules question, NOT display.
  FINDING line in docs/tickets/vocative_head_words.txt.
- **Word-study profile slow on mega-frequency Greek words (pre-existing, ticketed out of R-2 stage 3
  per reviewer ruling 2026-07-25).** **BASELINE TO BEAT (reviewer condition): the LIVE numbers —
  6.5s / 155KB on G2316** (3× curl-verified post-fix 2026-07-25; console figures below are diagnosis
  context only, production is the bar). Measured ~4s in a console
  process with READER_GREEK_FLIPS fully OFF, so NOT a stage-3 cost (the flip's own path is 0.3s —
  G9826 — after the indexed-union + zero-tipnr-peek fixes, commits 2eb2d710 + 0c22ecba). The cost is
  the profile building everything in one round-trip for a 4,500-occurrence word: ~8 ABP aggregate
  passes + the 6,000-cap default verse list + a 155KB JSON ship. Fix directions when picked up:
  trim default_verses for mega-words (first N + lazy rest), collapse the aggregate passes into one
  grouped read, or cache hot profiles. Hebrew feels faster because heb.db is smaller and H-numbers
  skip half the passes. code: views_lexicon.py lexicon_profile / _all_books_verses.
- **Jacob-class name cards — OPEN LANES ONLY.** Shipped arcs 2026-07-29/31 (easy pile 81 binds,
  middle-pile null, census itemization, rulings batches 2–3 +163, witness lanes A/B/C, pile-3
  residue zero, chip-merge) are recorded in TODO_ARCHIVE + memory project_pn_card_confidence +
  docs/tickets/LANE_C_adjudication.md + docs/tickets/DRILL_witness_divergence.md — do NOT
  re-derive from here. Census denominator COMMITTED: 591 word-slots / 156 names (2026-07-29).
  Still open:
  - **Follow-on lanes from the CLOSED word-position binding + bound-painted audit lanes (8/8;
    records TODO_ARCHIVE + docs/tickets/TICKET_bound_painted_audit.md):**
    - **1Ki 4:13 gilead p4** — ruled wrong-paint (Ramoth-Gilead compound component
      painted as the region) but ships ONLY with the compound-name/chip-merge lane,
      no one-off (reviewer+JP 8/8).
    - **Elnatham Ezr 8:16 p15** — in-verse variant-spelling appendix candidate
      (bucket-C pattern; found at wordpos adjudication).
    - **Chapter-grain 5** (azariah/joash/benaiah/harim) — per R3, any fold-in RETURNS
      TO THE REVIEWER; never automatic.
  - **Jabish spelling ruling** — 9 "Jabish Gilead" verses (ABP spells Jabish; the token already
    carries H3003 and serves the Jabesh-gilead card; only the Gilead half unruled) + gilead
    1Ch 10:12 / 2Ch 18:3 ("of Gilead" phrasing). Consistency fix, not coverage.
  - **Chip-merge banked tickets (JP raises): (1) compound-number DATA admission** — Strong's
    Hebrew has real compound entries (H6100 Ezion-geber, H7433 Ramoth-gilead); verify vs pages +
    xref layer, land as recorded links with receipts, THEN chips/cards wear them. SCOPE (JP
    2026-07-31): card-level number for EVERY merged pair, Greek side too (Dibon Gad G1045);
    TIPNR has NO distinct Dibon-gad entity — a distinct identity arrives only through this door.
    **(2) Pair co-occurrence count** — the honest count-line for merged cards; lands with the
    next touch of the identity-serving code.
  - Blurb specimen #3 (Num 33:45 Γάδ tribal blurb vs Dibon-gad bind) banked in
    docs/tickets/TICKET_blurb_verse_check.md.
  - **DRILL (standing):** candidate count is a property of the NAME; slot class is a property of
    the VERSES — dump the verses before assuming the failure mode. Mutual-exclusivity pre-flight
    (any verse claimed by 2+ candidates → un-partitionable, pre-flag) is PERMANENT (fired on mary).
- **Greek-header hand-table polish (backfill arc SHIPPED 2026-07-30/31 — record TODO_ARCHIVE +
  docs/tickets/DRILL_greek_header_backfill.md; batch receipts greek_header_batch1.md /
  greek_header_batch2.md).** 857 UNRESOLVED names remain (receipt file greek_header_split.txt is
  PA-only, regenerated each build — pull candidates by paste). Batch discipline proven:
  declension-only names with a page-attested dictionary form; real spelling variance stays
  per-verse (ruling b); abner/absalom + EGYPT PINNED verse-form (page-attestation is never
  ratio-dependent; egypt has 2 gentilic-printed rows). BANKED: per-row-exclusion hand-table
  mechanism (own scoped proposal; would recover egypt ~1,189 + adonijah 38 + artaxerxes).
  DISCOVERY: the split file caps each name's form list (~6) — big-name admission needs the
  bh_scrape census, not the split line. Next batches same flow, no deadline.
- **Adonai-card residue (items 1+4 closed 2026-07-30 — record in TODO_ARCHIVE, incl.
  the Isa 7:14 Immanuel-heads-as-Jesus pre-filed answer):** (2) UPSTREAM NOTE: adonai
  (H136, divine title) rides the proper-noun lane (is_pn=1) while its own AI blurb
  calls it "a title for God" — leave in-lane per the header ruling, revisit as an
  is_pn classification question. (3) PROVENANCE SEAM (long-term, provenance-contract
  lane): AI-authored summary sits directly above verified TIPNR/METAV data in one
  visual register — the disclaimer carries the whole load.
- **Hiram 1Ki 9:27: no Greek above the chip in ABP chip view (JP sighting
  2026-07-31, morning queue).** SCREENSHOT REFINEMENT: the card header serves
  Χειράμ (identity layer HAS a form) while the chip's Greek line is blank — so
  likely NOT a scrape gap: chip Greek reads w.lemma||w.inflected, and
  abp_surface skips name slots (the documented 30,126-slot gap); the identity
  form may simply not reach the chip render lane. DIAGNOSE BEFORE TOUCHING:
  confirm bh_scrape row + words/abp_surface for that verse-position, then
  whether other Greek-headed name chips show Greek in chip mode (if none do,
  it's a lane-wide render gap, not a Hiram bug). Page-attested-empty = a
  documented finding, not a fix. MORNING SWEEP (JP): bible-wide count of
  PN chips with NO Greek line in chip mode (read-only), so the fix scopes to
  the class, not the sighting.
- **Double comma "of his servants,," 1Ki 9:27 — SOURCE-ATTESTED (JP checked
  eSword 2026-07-31): ABP itself prints the double comma.** Our text is
  faithful; NOT a build artifact, NOT a fix on our side without a ruling
  (fidelity doctrine — we match the page). Disposition: Van der Pool errata
  candidate — goes on the errata list the dataset-publication ticket compiles
  (alongside the accent-typo + stray-mark classes). If JP ever wants it
  normalized in OUR text, that's an abp_corrections ruling, source-attested
  deviation class, not a silent cleanup. MORNING SWEEP (JP): bible-wide `,,`
  count (one read-only sqlite line on verses.text) — class or one-off — feeds
  the errata list either way.
- **Highlight span boundaries wrong in translation text modes (BANKED 2026-07-31,
  JP served review H7307 BSB — PRE-EXISTING class, deferred by JP's call; check
  KJV too).** Three observations, diagnose before fixing: (1) punctuation bleed —
  Gen 6:3 highlights `"My Spirit` incl. the opening quote; NOTE the renderer puts
  trailing punctuation INSIDE the span by construction (50-corpus-results.jsx
  `{w.word}{w.punc}` inside the highlighted span) — likely the mechanism, sweep
  quotes/commas/periods at span edges. (2) suspect span targets — Gen 7:22
  highlights only `of` ("the breath of life", content words unlit): diagnose
  whether BSB word-alignment data is off for that verse or the renderer picks the
  wrong slot; same check for Gen 26:35 `they brought` (if alignment genuinely
  maps רוח there, document, don't "fix"). (3) multi-word spans ("in the breeze",
  "the breath") plausibly correct full-phrase renderings — verify vs alignment
  data, not presumed defects. Render-layer, no data writes expected.
- *(Provenance-seal arc + "Matched by name" pill + tag hover-warrant standard: CLOSED/SHIPPED
  2026-07-31 — records in TODO_ARCHIVE; standing rules docs/claude/frontend.md. Deferred by
  ruling, JP raises: hedged name-match pill conversion · Contested fork-header hover (ruled no) ·
  Study-tab tags (wait for Study) · ac-prov-contested left title-only.)*
- **Hebrew "bolder English" — root-caused (record in TODO_ARCHIVE), pending JP's
  one-tap confirm:** chip mode + Interlinear OFF should match prose exactly (the
  effect was the deliberate English dimming while Interlinear is on). If the dimming
  reads too strong on his phone, that's a design-tweak ruling, not a bug.
- **Place-card raw fields (cosmetic, flagged + SIZED at batch-2 close-out, non-blocking):**
  `area: ">"` on **959 place records** (JP-counted 2026-07-30) — a place-parser CLASS:
  TIPNR place rows use a different column layout than person rows and the area read
  lands on a structural '>' marker, not text. Affects any served place card that prints
  area (Ezion-geber the found case; also desc=name on places — TIPNR places carry no
  person-style era line). **PERSON-SIDE COUNTERPART MEASURED 2026-08-09** (see
  TODO_ARCHIVE, PN-panel display tickets): person rows' `area` is ~1,150 "Tribe of X"
  vs ~400 regions/periods (Early Patriarch, Edom, Egypt, Sinai…) — i.e. the column is
  mixed by design on the person side too, not just broken on the place side. The card
  no longer labels those "Tribe"; a parser pass should treat both sides as one
  question. Fix directions when picked up: parser-side (read the right
  column for section='place' in entity_resolution.parse_tipnr, then re-run the widened
  --apply through the gate arc) AND/OR display fallback (suppress non-alphabetic area,
  lean on summary). Check FIRST how long-bound place cards (pre-widening) have rendered
  area — if the reader already suppresses it, this may be invisible today. JP eyeball of
  Geber 1Ki 9:26 rendered = the screenshot.
- **Dataset publication with receipts (BANKED 2026-07-31, JP-raised — future
  project, post-completion of the Greek PN work; no build, no scoping yet;
  nothing on any queue moves).** When the Greek name/place/group work completes,
  publish the corpus as likely the most accurate full-Greek-Bible proper-name
  dataset in existence — the cert chain is the credibility asset, not just the
  data. Framing recorded now: (1) LAYERED LICENSING — original work (bind
  tables, identity xrefs, corrections, cert receipts, admission briefs)
  publishes freely, likely CC BY-SA where derived from TIPNR/MetaV (both
  CC BY-SA); ABP text is Van der Pool's (permission pending) so the default
  shape is STANDOFF annotation — verse address + word position + our data,
  keyed to the text without shipping the text; publication does NOT block on
  ABP permission, shape upgrades if it lands. (2) ERRATA FILED UPSTREAM,
  separately — MetaV/TIPNR/Tyndale corrections as issues/PRs against their
  sources (Tyndale STEP data is on GitHub), each already receipted; ABP
  scrape-vs-print findings (accent-typo class, stray-mark class) compile as a
  Van der Pool errata list. (3) REPO SHAPE: data + receipts/ (cert briefs,
  batch admission files, ruling records — much already exists as ticket/brief
  markdown) + a methodology doc; the batch-1/2 admission rules and the
  verdict-gate discipline are its draft. (4) TRIGGER: JP raises when the PN
  work is done or ABP permission resolves, whichever makes the shape decision
  live.
- **Genealogy-of-Jesus map (BANKED 2026-07-30, JP-raised — future feature, no
  build/design yet; nothing on the current queue moves for this).** The
  "Genealogy of Jesus" attribute tag on person cards becomes clickable,
  navigating to a lineage map: Adam → David → Jesus as a walkable graph, each
  node linking to its PN card. Data likely already present via MetaV/TIPNR
  parent/child relations. Design questions named now, resolved at scoping:
  (1) the Matthew 1 / Luke 3 fork after David — the map must show BOTH attested
  lines over the shared ancestor pool (structurally an argument-graph-shaped
  artifact); (2) edge receipts — each parent→child link cites its attesting
  verse(s) (1Ch genealogies, Mat 1, Luk 3), same receipt discipline as the rest
  of the site; (3) taxonomy note — the tag converts datum → NAVIGATING under
  the recorded warrant rule, so any warrant lives on the destination page, not
  a tooltip. Own design proposal when JP raises it.
- **Eponym both-senses card upgrade (banked candidate — JP option (b), 2026-07-11).** Shipped fix
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
  Standing acceptance rule (carried from the polarity-A fix, 2026-07-09): any related fix re-checks
  "no helper-word chips" on the exhibit words (Jud 1:9, Rth 2:16, Job 18:13 — chips + search
  highlighting read the words table), not just the corrected rows.
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
  resolve steps are in `docs/handoffs/HANDOFF_metav_person_link.md`; pick the person_id + write it into the residual notes.
- **Badge / verification-token unification (design backlog).** Two families — provenance badges (metaV/
  TIPNR/"Matched to this verse") vs verification marks ("✓ N/N verified"); rule now in `docs/design.md`.
  Converge instances opportunistically, no sweep.
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
  (The 9 null-form "this/these" candidates were resolved in cert Session 7 → TODO_ARCHIVE; not part
  of this retag.) The ου-/αυ-initial forms (οὗτος/αὕτη) are excluded on purpose — `ουτ*` collides
  with οὕτως G3779, `αυτ*` with αὐτός G846.
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
  8. **Sub-use paragraph styling (banked 2026-07-08, batch-3 session, JP):** "Sub-use:" paragraphs inside a
     senses_block render as plain prose, visually undifferentiated from the main sense body (confirmed on the
     live G1119 card). Wanted: a light visual indicator — indent, smaller type, or left rule, frontend's call,
     within the quiet-design rules (no boxes). Display-only; no engine/prompt/stored-data impact. JP schedules.
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
- **Hebrew-OT word finder is NOT number-folded** (KNOWN GAP) — the singular/plural fold is live on
  ABP/KJV/BSB but NOT the `corpus=heb` discovery branch (it matches a token inside a multi-word gloss
  phrase, so the precomputed `*_norm` column doesn't fit). A real fold needs BOTH a normalized-token
  side-index in heb.db AND a looser `gloss LIKE` prefilter. Don't ship a half-fix (folds one direction,
  reintroduces the asymmetry). Hebrew search stays number-exact until both land. Memory
  `project_lexicon_finders`.

---

## Three-zone shell — remaining consumers
The shared frame (`Shell` + `RightStack`, `static/src/22-shell.jsx`) is done; Ask-corpus, Notes,
Seam index, News all shipped on it. Seam index is OFFSTAGE (rides the hidden Study tab). Record:
memory `project_three_zone_shell`.

**MOBILE SHEET CONTRACT — COMPLETE 2026-07-16** (spec `docs/claude/frontend.md` → "THE MOBILE SHEET
CONTRACT"; story + the News-fixture and `.filters-sep` write-ups → TODO_ARCHIVE). Small open ledger
(verification debt, not scheduled work):
- News' selected why-head inside its sheet — never measured (expect ~42.4 per the
  band-with-control ruling).
- Day-intro card — needs chronological mode in the harness (shares the chapter-overview code path;
  inference, not measurement).
- Keyboard-lift — if a sheet should ever rise above the on-screen keyboard, that's a SHELL-level
  ruling for all cards; needs a real phone.

**Shell's MOBILE collapse: News + Ask-corpus + Notes shipped; Study is the last consumer and is
DEPRIORITIZED (JP ruling 2026-07-15) — copy the three landed commits IF it ever returns; do NOT
queue it.** Gotchas live in `docs/claude/frontend.md` → "Shell's MOBILE collapse". Opener
`docs/handoffs/HANDOFF_study_mobile.md` stays banked.
- **PARKED (JP 2026-07-15, not released) — swap the DESKTOP Ask-corpus strip's hand-inlined plus to
  `Icon.Plus`.** `Icon.Plus` was added 2026-07-15 for the mobile bar and retired the mobile inline
  copy; the desktop strip (`52-ask-corpus.jsx`, the `.ac-strip-new` button) still draws its own by
  hand at a different stroke width. It's the "reference the system, never a local copy" rule, so it
  should land eventually — but swapping it MOVES DESKTOP PIXELS, which is why it stayed out of a
  mobile-scoped commit. Needs its own desktop-scoped pass + JP's eye. code: static/src/52-ask-corpus.jsx
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
- **R-2 parked candidates (the migration itself is COMPLETE + LIVE 2026-07-26 — memory
  project_entity_resolution_rebuild; the old "open from docs/handoffs/HANDOFF_r2_greek_names.md" opener is
  SPENT).** Reviewer-parked, pull not push, recorded in docs/tickets/alias_leave_list.txt pile
  comments: gentilic Group rows binding their own Group entities (hittites pile U) · per-reign
  Pharaoh link disambiguation (pile V) · ladder possessive-strip ("Aaron's," class, pile P) ·
  vocative-aware peel (Isa 41:14 "O Israel") · josua/shapan/meramoth micro alias batch · the 178
  lookup H/G fill-gains reverted for byte-identity (NT name words still ride the Hebrew fallback —
  a real future improvement, per-word review needed).
- **pn_binding — 352 spelling-variant rows (abia→abijah class)** queue into R-2's variant batch,
  per-pair eyeball + roster-freeze check required. (The class-level hand-check of all 1,310 rows
  is DONE 2026-07-16, reviewer-accepted — `docs/audits/AUDIT_provenance_sweep.md` §4 +
  TODO_ARCHIVE; everything else stays floored by ruling.)
- **Provenance render — tappable badge tooltips** (the rest of the provenance render work CLOSED
  2026-07-16 → TODO_ARCHIVE + `docs/CHARTER_provenance_render.md`): ONE shared component + ONE
  registry keyed by contract §2; own session, gated on the mobile sheet contract.
- **5 known-red tests on clean master, unticketed** — tests/test_lexica_draw_cache.py fails 5
  tests on any machine without the live DB (sqlite: no such table). Confirmed on clean master
  2026-07-16 (twice). Either the tests gain a skip-without-DB guard or a fixture; unticketed
  known-red is rot. NOT in the pre-commit/CI curated lists (those pass), so no gate is lying —
  it's pytest-full-suite noise that trains people to ignore failures.
- **Ask-corpus words-in-scope counts should be search-relevant** (JP standing gripe, logged
  2026-07-16) — the rail's chips + the "N occurrences" line show TOTAL-Bible counts (theos 4,557);
  they should show occurrences within THIS search's verse pool. Needs backend work: the payload
  doesn't carry per-word pool counts — compute per key word over the pinned pool, ship in the
  payload, do NOT approximate from the curated key passages. Same pass: give the `hasCount:false`
  rows a visibly-distinct "no count" state instead of a minimum-width bar (silent-fallback rule).
  code: ai.py (payload), static/src/52-ask-corpus.jsx + 51-corpus-logic.jsx (render)
- **News beast-arm badge** (authored follow-up) — a per-thread "which beast/arm" tag in the why-rail.
  Not built on purpose: the thread→arm map isn't 1:1 (several threads serve BOTH arms), so it's
  hand-authored content JP will sit with, then it drops into the why-section. code: views_news.py map,
  static/src/84-news.jsx

**Owed eyeball checks (post-deploy, JP — verification debt, not scheduled; nothing blocks on them):**
- **Ask-corpus mobile** (both states: the landing, and a thread's follow-up box). The numbers
  are verified at an asserted 375px — bar 3 slots @22px, quota
  landing-only and above the input, follow-up field restored to its pre-pass 339px, desktop untouched
  at 1400px — but **the VISUAL was never certified: the screenshot tool timed out on both passes**
  (no page errors, tool-side). Nothing blocks on it; it's the last unverified surface of that work.
- **Post-deploy click-through** of News / Word study / Library on desktop + phone
  (the mobile sheets are the one thing the parity gates can't run locally); confirm the News tab shows in
  the mobile bottom nav (admin) + the News inspect looks balanced without cramping the `.news-bar` row.
  (The Ask-corpus provenance rail was checked in Chrome 2026-07-01 — fine.)
- **News shipped arcs** (copy-shortlist resolution · paywall-aware face + 🔒 badge · Copy/Export
  formats — SHIPPED 2026-07-01/02; records in memory project_news_watch):
  - Copy shortlist pastes clean article links (not news.google wrappers); a card title click lands on
    the real outlet; archive backfill self-terminates — investigate only a stable failing remainder.
  - Paywall spot-check: a mixed cluster shows the FREE outlet as card face, 🔒 on the paywalled
    source, stable across windowed ↔ Max presets.

---

## News watch — account gate (Pass 1 SHIPPED 2026-07-15 `69a7156`; record + the KEEPS-ARE-INERT
proof in memory project_news_watch; gates locked by tests/test_news_gate.py)
Open tickets:
- **Grayed Keep/Dismiss costs too much row on a phone** — first Pass-2 item under News-on-mobile.
- **FLAGGED, NOT SCHEDULED — admin's LIVE Keep/Dismiss squeeze the headline on a phone** (Kept rows worst:
  "Back to Inbox" + "Dismiss" side by side push the headline to ~148px / 5 lines). Pre-existing, NOT a
  regression, and item 1's ruling protects it — **a control that works earns its row**. But JP is the admin,
  so it's his own triage view. Fix would be stacking the actions under the headline on mobile; that's a
  design call on LIVE controls, so it waits for JP. code: static/src/84-news.jsx (NewsStory `.news-actions`)
- **Reader bookmarks (small, not scheduled):** the review table is already per-person and keeps
  feed nothing (inert) — giving a plain account its own id is close to the whole feature.
  code: views_news.py `_reviewer()` + `set_status`
- **Shareable News deep link (`/?view=news`, ideally per-story) that survives signup** — own
  ticket, NOT Pass 2. code: static/src/90-app.jsx (`?news=`/`?b=`/`?lex=` pattern to copy)
- Share key (`/?news=<key>`, one holder = Tudor) untouched; retirement not ticketed.
- **APPLIED 2026-10-25 (258 rows merged, 0 sets left; nightly merge now ON) — OPEN: step (4)
  `--fill-links` for the 2,283 unlinked Google rows scored 5+, then re-report + apply. Rollback copy
  `~/db_backups/news.db.pre-merge-2026-10-25`; 20 review clashes all agreed (same mark both rows).
  Google repeats slip past the "already have this
  link" check.** Google hands out a NEW redirect link for the same article on a later pull, so
  `items.url` (INSERT OR IGNORE on url) never matches and the same article is stored twice —
  e.g. ids 22825/23963, 5665/19745, 24147/24487 (two different Google dates, 2024-11-21 vs
  2021-02-18), and NewsNation "Catholic AI task force announced by US bishops" (two Inbox cards,
  JP 2026-10-25). Two rows of one article show as two cards when the labeler gives them different
  event labels (see the third clustering case below). FIX: same article = same REAL address
  (`scripts/news/dedupe.py`: resolved_url for Google rows / the url for RSS rows, cleaned of
  tracking junk, www, AMP tail). Title + outlet is NOT a merge key (recurring headlines; Google
  dates unreliable) — `merge_dups.py` only reports title matches, as the check on the address key.
  `merge_dups.py` merges each set into one survivor (RSS > page-verified date > scored > labeled >
  earliest), moves Keep/Dismiss marks, copies the removed row into NEW table `items_merged`
  (rollback copy + the ingest skip list in gather_news/pull_rss), deletes it from items. Nightly
  step in daily.sh after resolve_new_faces; it does nothing until the first by-hand `--apply`
  creates items_merged. Locked by tests/test_news_dedupe.py (CI + pre-commit).
  PA steps: (1) `inspect_rows.py "catholic ai task force" --resolve` — DONE 2026-10-25, pair
  confirmed (26816/27449); (2) `merge_dups.py --pages` report → verdict; (3) copy news.db, then
  `merge_dups.py --apply --pages`; (4) `--fill-links N` in chunks, re-report, apply again.
  First report (2026-10-25, every set read): A = 207 sets / 209 rows, all correct. Found + fixed
  before any apply: (a) the survivor kept its OWN score — 21 articles would have dropped out of the
  5+ Inbox (RSS copy scored lower than the Google copy) → survivor now takes the highest-scored
  copy's AI reading + label; (b) B1 address clean-up gaps → rules from real pairs (MSN page id +
  render switches, cnn/edition.cnn, bbc.com/.co.uk, qa.philstar, AMP viewer codes, /amp/,
  /index.php/, .html, ?action=share) — 24 more sets, all verified same-article; (c) moved articles
  (EWTN/Crux/Angelus section moves) → `--pages` merges when a page's own canonical tag names the
  other row's address (tag pointing anywhere else is ignored). Report headline check no longer
  trims " - June 26" off dated issues. Known gap (section C): 2,283 Google rows scored 5+ have no
  real link (mostly older than the 60-day page-date backfill) → `--fill-links`.
  Second report `--pages` (2026-10-25, every set read): A = 251 sets / 258 rows — the 207 from
  report 1 unchanged (same survivors), +32 from the new address rules, +13 from the page check
  (each: one page's own tag names the other row's address; ucanews' off-site tag correctly
  ignored); 97 survivors take a higher score. VERDICT: PASS for --apply. Left unmerged on purpose
  (B1, 39 sets): ~25 are different articles (each page names itself — numbered/weekly posts,
  LifeSite video vs article, regional pages); 6 are EWTN slug renames ("pope-leo-xiv-…" →
  "pope-leo-…") whose old address now 404s, so nothing can confirm them; ~8 have both pages
  unreachable. Side note: LifeSite's RSS feed leaks CMS junk rows ("?p=…&post_type=acf-field",
  score 0) — harmless, unticketed.
- **PARKED (2026-10-25, no code): corroboration as a rank input — Aug 14 ruling, layer 3.** At equal
  score, a card whose articles span multiple outlets ranks above a single-outlet card. Reuses the
  existing card grouping; no scorer change. GATED behind the two mandatory clustering fixtures.
  Layers 1 (outlet cap) and 2 (downward-only rank_score) are live; this would slot into the same
  Inbox Top-stories order (83-news-logic.jsx / 84-news.jsx viewListAll). Context: 28 of Advent
  Messenger's 31 recent articles sat on cards no other outlet shared (2026-10-24 count).
  **STATUS 2026-10-29 — fixtures RUNNABLE + GATED (CI + pre-commit); expected picture awaits JP's
  verdict.** Frozen 2026-10-29 03:47 UTC off PA (`freeze_sample.py`, read-only): 918 encyclical /
  175 Sunday / 41 cross-night rows (score >= 5). `news.db.pre-regroup` is gone, so the June bucket
  itself couldn't be pulled — the Sunday sample is by headline/label words. EVERY row hand-judged
  into its happening in `expected.json` (house rule = group_news.py SYSTEM; applied under JP's
  standing delegation): encyclical 623 core / 189 clearly other / 106 borderline (never asserted);
  Sunday 15 multi-row happenings + 95 singles + 6 unsure; cross-night 4 happenings + 2 unsure.
  FINDING — against that judgment ALL THREE fail on the current LABELS (layer 1), never on the card
  code: (1) the encyclical's 623 rows carry 53 different labels (corrected 10-29; "~100" first
  written counted the whole 918-row sample, 107) — only the June-29 regroup pass kept it on one label;
  every nightly label after is new wording; (2) the June pass itself left a theme label ("European
  Work-Free Sunday Campaign", 26 rows 2012-2026) and fused 6 other stories onto the encyclical label
  (AMECEA, Carney meeting, synodality speech, ...) while putting 13 encyclical rows elsewhere (the 5
  Vance reactions, ...); (3) the replay shows the labeler is shown 0 known labels at the start of
  EVERY night. So the test is built per layer:
    - merge (June-pass rows): the main label = ONE card (401 rows, 230 outlets), no other label
      joins it — passes; the June labeler's mistakes are PINNED by id (13 + 6).
    - split: no card fuses two happenings except the PINNED one (Utah law + a Belgium explainer,
      12 days apart on the theme label) — passes.
    - cross-night: real `group_news.main()` replayed night by night, AI stood in (never confuses
      stories, reuses a label it's shown, else the real labeler's own wording). One-pass control
      passes for all 3 samples; real nights = **KNOWN FAILURE** x3 (encyclical 64 cards, death
      penalty 5, 14 Sunday happenings split). Strict: when it passes, the test fails until
      KNOWN_FAILING is cleared. PROVEN to flip: an in-memory fix (seed `known` from the db's
      labels) turned all 3 to PASS; group_news.py untouched.
    - every check fired on a doctored wrong grouping (card cut in half / fused) before trusting it.
  **LAYER-1 BASELINE — RECORDED 2026-10-29** (JP ran `relabel_check.py --run` on PA after deploying
  10cad8ab: 221 Haiku calls, one run, nothing written). Stored = the frozen labels through the same
  report on the same rows. Fresh labels drift on nearly every row (new wording everywhere); what
  matters is the grouping:
    | sample      | measure                         | stored | fresh one pass | fresh real nights |
    | encyclical  | encyclical rows on one card     | 374/623 | 593/623       | 341/623           |
    | encyclical  | other stories on that card      | 6      | 53             | 13                |
    | encyclical  | labels on the encyclical rows   | 53     | 4              | 27                |
    | Sunday      | over-merged cards               | 1      | 2              | 1                 |
    | Sunday      | happenings split over cards     | 16     | 7              | 13                |
    | Sunday      | 15 multi-row happenings on ONE label | 0 | 8             | 2                 |
    | cross-night | over-merged / split             | 0 / 3  | 1 / 0          | 0 / 2             |
  Read: (1) the nightly split is real on the live labeler too (one pass 4 labels -> nights 27; the
  death-penalty statement 1 label in one pass, 5 cards night by night). (2) ONE PASS OVER-MERGES:
  53 other stories joined the encyclical card — all 6 June pins again (100, 296, 949, 2083, 2921,
  3087) plus the May study-group/commission rows (109, 144, 663, 734, 789, 2717, 2961, 2967, 5443 seen;
  output listed only the first 15 of 53). A fix that shows the labeler more past labels must be
  checked for this, not just for the split. (3) Over-merges flagged vs the judgment — JUDGMENT CALLS,
  open for JP: Palm Sunday Mass + "Pizzaballa blocked ... as Pope Leo denounces war" (15317; headline
  carries both — candidate for `unsure`); two "Sunday Law Update with Dr. O" episodes Oct 3 + Oct 9
  (judged separate episodes); Sunday Alliance + a Dr. O episode, same day Oct 3 (real nights);
  Cardinal Parolin Oct 9 + the pope's Oct 10 statement (one pass; judged different speakers/days).
  The pinned Utah + Belgium over-merge did NOT recur. (4) Fresh labels get YEARS wrong ("North Dakota
  House Bill 1150" for the 2018-19 repeal, "Poland ... 2023" for 2018, "Palm Sunday Mass 2025" for
  2026) — the prompt's ask for a year is guessed; relevant to the fix prompt. One run only: temperature
  0 is not guaranteed repeatable, so treat single-row differences as noise, the table as the shape.
  Expected picture: JP will not review rows by hand (2026-10-29) — the judgment STANDS as written,
  incl. the 4 calls above (kept as judged: Pizzaballa's police incident, separate Dr. O episodes,
  Parolin vs the pope are different happenings). Logged under the standing delegation.
  **CROSS-NIGHT FIX — SHIPPED 2026-10-29 (code; live measurement PENDING).** `group_news.py` nightly
  runs now show the labeler a BOUNDED list of past labels, chosen per batch by `pick_known`:
    1. REACH — only labels with an article PUBLISHED within 14 days (REACH_DAYS = views_news
       WINDOW_DAYS) of a headline in the batch: the card code joins a label's rows only across
       <= 14-day gaps, so a further label can't merge cards, only fuse. Published, not pull night
       (the Dec-2023 Chick-fil-A bill was re-pulled on 11 nights over 3 months).
    2. PER-HEADLINE MATCH — each headline's best label first (most shared words, 2+, label + its 3
       best-scored headlines), then other 2+-word matches, then at most LOOSE_MAX = 10 weak ones.
       First version ranked against the whole batch and crowded single-headline needs out (it
       split the encyclical 5 ways, broke the Sunday one-pass control); the seed-rules check fails
       on that version.
    3. CAP SEED_MAX = 40 (one best match per headline of a 40-headline batch; vs 295 unbounded),
       each label shown WITH one example headline so the AI judges sameness by content.
    `--regroup` is unchanged: same prompt, byte for byte (checked against the old code).
  Replay (stand-in AI, all frozen samples): all 3 real-nights cases PASS — encyclical 622/623 on
  one card (the 623rd is the Jan-dated aleteia row, its own window piece by design), death penalty
  1 card, every Sunday happening whole; KNOWN_FAILING emptied (strict, still armed). Merge + split
  unchanged (frozen labels). Fusion with the stand-in: 0 clearly-other rows on the encyclical card
  (incl. the 6 CI-pinned June mistakes) — but the stand-in CAN'T fuse by construction; the real
  number is EXPOSURE: 177 of 189 clearly-other encyclical-sample rows were SHOWN an encyclical label
  when labeled (same words + dates). Whether the live AI resists is exactly what the PA run decides.
  relabel_check.py REAL NIGHTS now runs the real `group_news.main()` night by night on a scratch db
  (it re-implemented the old empty-list loop before, so it would have measured the OLD code).
  PENDING — the live run, compared to the 10-29 baseline table above: `deploy.sh`, then
  `relabel_check.py --run` (221 calls). Pass = real nights keeps the encyclical together (baseline:
  341/623, 27 labels) WITHOUT more clearly-other stories on its card than the baseline real nights
  (13); Sunday split/fused and cross-night split down, fused not up. If fusion rises, revert
  group_news.py before the next nightly. TIMING: daily.sh pulls ~06:00 UTC and the deploy makes
  that night use the new code — measure first. Already-stored labels are untouched (only new rows
  use the list); old split cards stay split. A `--regroup` would rewrite them but its unbounded
  one-pass list over-fused in the baseline (53) — not run, needs its own measured decision.
  **GAP in the standing rule (searched 2026-10-25): the two fixtures are NOT runnable tests.**
  tests/ has no test of the grouping code at all (views_news `_group` / `_cluster` /
  `_split_by_window` / `_pick_face`, scripts/news/group_news.py); the only news tests are
  test_news_gate.py (who may read/write) and test_news_bulk.py (bulk triage). The closest match
  is the two checks run BY HAND on a live `group_news.py --regroup` on 2026-06-29 (labeler rewrite
  0d7387f; record in memory project_news_watch):
    1. MERGE — the Pope Leo AI encyclical stays ONE card across hundreds of outlets (541/276 then);
    2. SPLIT — topic buckets ("Sunday Rest Laws Debate", "Vatican Ecumenical Outreach") break into
       their separate happenings (Poland trade ban / NJ mall lawsuit / NY Chick-fil-A bill / …).
  They matter here because corroboration rewards multi-outlet cards: an over-merged topic bucket
  would read as falsely well-corroborated. No written copy of the rule itself was found in the
  repo or memory either. Before this can be built: turn both checks into runnable fixtures
  and wire them into CI + pre-commit. **Own session (JP 2026-10-25), fresh handoff.**
  RULED (JP 2026-10-25): BOTH layers — layer (2) gets a normal runnable test (CI + pre-commit);
  layer (1) gets a by-hand re-label check on the frozen samples, run before ANY clustering change.
  Background: cards come from TWO layers: (1) the AI labeler
  (group_news.py, Haiku) names each article's event — the June merge/split checks were testing
  THIS layer; (2) views_news `_group` puts same-label rows on one card, split by date —
  deterministic, easy to test from frozen labeled rows. A frozen-rows test covers only (2); (1)
  is an AI call, so its fixture is a re-label run on the frozen samples compared to expected
  cards (as done by hand in June). Corroboration reads the cards, so a (2)-only test would pass
  even if the labeler drifted back to theme-lumping. Needs from PA: a frozen sample of the AI
  encyclical coverage and of the Sunday-laws bucket; both checks must pass against the CURRENT
  code before they mean anything.
    3. CROSS-NIGHT MERGE (added 2026-10-25, JP report; no code changed; CONFIRMED 2026-10-29
       from the freeze: the statement got 6 labels over 6 nights, the Holy See UN call 2 over 2 —
       the KNOWN FAILURE in tests/test_news_clustering.py) — Pope Leo XIV says the
       death penalty is "inadmissible": two cards for one event, National Catholic Register
       2026-10-11 (4 sources) and EWTN News (CNA) 2026-10-10 (4 sources). Expected: ONE card.
       Read from the code: NOT the 14-day window (1 day apart) and NOT headline wording (the
       word-overlap grouping only runs on UNLABELED rows) — two cards from dated rows a day apart
       means the rows carry two different event labels, i.e. layer (1). Likely why:
       group_news.py starts every run with an EMPTY list of labels (`known = []` in main), so it
       only reuses labels it made earlier in the SAME night. A story whose coverage arrives over
       two nights gets labeled twice from scratch, and any wording difference ("Pope Leo Death
       Penalty Inadmissible" vs "Pope Leo XIV Death Penalty Statement") = two cards. The June
       merge/split checks ran as ONE `--regroup` pass, so they never exercised this. Confirm on
       PA: `inspect_rows.py "death penalty"` — the members' labels and first-pull nights. Frozen
       sample needed: these 8 rows with their first-pull nights, labeled in two separate runs.
       CONFIRMED for the NewsNation repeat pair (PA 2026-10-25): ids 26816 (first pulled 10-21,
       label "US Bishops AI Task Force") and 27449 (first pulled 10-24, label "US Bishops Catholic
       AI Task Force") — same article, two nights, two labels, two cards.
- **Page-date backfill — APPLIED 2026-10-25.** 1,828 Google rows (score >= 5, last 60 days): page
  date 1,392 (33 flagged >30d off Google — every one verified against the real page / a printed
  byline / a known event before apply), unverified 436 (show "~"), RSS 8,864 untouched. The four
  known misdates (26533/23285/23286/23784) corrected; Radar.am 26633 → 2026-05-18 (its "Pope
  Francis" headline is the outlet's error — the text is Pope Leo XIV). The nightly check in
  resolve_new_faces.py now runs on new pulls. Reader guards added during the dry runs (each from a
  real page that broke it): self-contradicting pages, ambiguous <time> lists, dates after the pull,
  a tag vs its own printed text, ambiguous day/month (01/07/2026). Records: commits 5109c1f7..0ea8dcd1.
- **DONE 2026-10-25 — Google redirect lookup now has a hard time stop everywhere.** PA's
  googlenewsdecoder 0.1.7 takes no timeout (its requests calls had none), so `gnews_resolve.resolve()`
  — the one function every caller uses (Copy shortlist `/api/news/resolve`, nightly face-fill,
  backfills, page-date check) — now runs the call under `scripts/news/deadline.with_deadline`
  (RESOLVE_LIMIT 20s; past it, None). Library pinned `googlenewsdecoder==0.1.7` in requirements.txt.
  Locked by tests/test_gnews_resolve_deadline.py (fails on the old code: it hung the full stub wait).
  Not changed (noted only): /api/news/resolve still resolves up to 300 links one after another per
  request, so a request with many dead links can still run long — each is capped at 20s.

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
  διώκω G1377, δόξα G1391. Mirrored in `docs/handoffs/HANDOFF_lexica_rollout.md`.
- **Inverse-direction audit** — nobody has checked the existing dotted_lexicon the OTHER way: dotted
  rows that ARE on the list but map to the wrong entry, or bare rows that should have been dotted in
  the source. dotted_lexicon precedent says this direction has had defects.
- **Homonym heuristic** — same-spelling-different-sense (wrist-under-fruit καρπός G2590.1) is invisible
  to any comparator; it only surfaces the way ὄρος did (a floor grows a bad sense). A gloss-divergence
  grep sweep is the candidate detector.
- **2 blank abp_surface `form` cells** (Isa 19:2, Eze 40:12) — surface-alignment gaps, note-only.
- **Draw-cache archive question** — `--force` overwrites a rejected draw under the same key (ὄρος draw-1
  2-sense reject lives only in chat). Consider archiving rejected draws so the audit trail lives in the
  machine, not the transcript.
- CLOSED 2026-10-25 — **Backup-script rewrite (carry-forward, root-caused 2026-07-07):** a
  compression failure logged a "good" backup. Fixed with the damaged-10/24-backup lane (see that
  entry): a failed compression now fails the run; `tests/test_backup_rotate.py`.
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
Merges with the parked ὀρ-collision retro sweep (step-0 mostly absorbed it). δίδωμι G1325 SHIPPED carries
a 1-row leak (1325.1 "mortgaged", Neh 5:3) — verified NOT cited in the live card, stands with a provenance
note; re-ship only if the no-entry remedy changes it. code: scripts/build_dotted_lexicon.py, audit_dotted_lemmas.py

---

## Word cards / lexicon — open items

- **PN DEFINITION ENGINE (banked 2026-07-31 issue-log session — no work yet).** Lexica-style
  AI blurb for all places, people, and groups, in the context of the verse being viewed —
  same verse-grounded discipline as the word definition engine. Scope AFTER the current
  def-engine calibration completes.

- **Geometry-aware unfindability mode (reviewer-ruled OBLIGATION, before the next ride
  that MOVES name slots):** audit_unfindability.py needs identity-level matching (the
  attribute_unfindability.py v4 logic) — position-keyed, it fails on exactly the moved
  class (2,049 on the ②-ride, all attributed, 0 real). Named pre-req in /rebuild-words.

- **split_merges JSON: 29 superseded keys (small, next regen).** The PN-star pass now
  fixes 29 of the 237 patch verses upstream (they skip on precondition; all 30 content-
  adjudicated DISPLAY-EQUAL to live, split_skips4.log). A future graft/regen can retire
  those keys; harmless meanwhile. code: scripts/split_merge_fixes.json

- **UNPARKED by the 8/1 rebuild (were waiting on it; own session when JP raises):** the
  **carrier-gap attribution** + the **pass-disabled replay** — both only mean something
  measured against the NOW-LIVE ruling-10 pass. Context: ticket §6j; the leftover defect
  set of record = `--predict-vs` (2,520 rows, member-derivable any time).

- **⑤ BRACKETED ARTICLE-SLOT ROWS (38) — OPEN RULING, own cycle, own controls.** Sized
  2026-07-31 and deliberately NOT folded into ④. 20 are whole-slot moves where the word
  takes the emptied slot's own position (cheap); **18 are partial moves that need a NEW
  position inside an ordering that already exists** — `1Pe 4:2` is the witness, an 11-slot
  bracket group whose positions run to 9. That is a second ruling about bracket ordering
  stacked on the first, so the class is not contained whatever the code diff looks like.
  **Do not split off the easy 20** — a rule that fires on half a class for positional
  convenience is one nobody can restate later. Motivating exhibit: `1Co 3:8` repairs one
  `'his own'` onto G2398 and leaves its bracketed twin, inconsistent within one verse.

- **③ HAND-REPAIR LANE — 71 adjudicated candidates (eyeball pass DONE 2026-08-03;
  record `docs/audits/LANE3_b2_dispositions.md`).** 71 genuine repairs (gentilic 22 ·
  roster-silent name 41 · possessive 8; possessive keeps apostrophe-s as printed,
  JP-ruled) + 29 artifacts closed. **Mat 27:26 belongs to this hand lane too** (legal
  A/unattested refusal, φραγελλόω too rare for page evidence). Every repair is
  hand-per-row, JP-checkpointed; waits for JP to raise.

- **SAME-NAME / RENAMED DROPS (opened 2026-07-31 at the G707 ship — allowlist design
  question, own session).** 358 slots ruled correct-to-drop today (text-first) but carrying
  a defensible same-name/renamed link; verbatim list = docs/tickets/G707_diff_report.md
  Group B. Names: edom(Esau), abram(Abraham), azariah(Uzziah), shallum(Jehoiachin),
  jerubbaal+jerubbesheth(Gideon), belteshazzar(Daniel), sheshbazzar(Zerubbabel),
  jedidiah(Solomon) · ashdod(Azotus), horeb(Sinai), ephrath(Bethlehem), lod(Lydda),
  jetur(Ituraea), on(Heliopolis), rakkath(Tiberias), shiloah(Siloam), judah(Judea) ·
  spelling variants molech(Moloch), kanah(Cana), babel/babylonia/babylonian,
  ezrahite/izrahite(Zerah), gehenna(G1067). Acco/Ptolemais never served (nothing dropped).
  Any allowlist = cert-#7-style curated machinery, JP-checkpointed, red-first gates.

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

- **Lexica dictionary — verse-grounded word defs (Sonnet engine; LSJ display-only).** Public since
  the pilot; live cards 85 (DB-counted — the table is the count). **Current law + queue =
  `docs/handoffs/HANDOFF_lexica_rollout.md` (RULING LIST + ROADMAP + Queue); authority = `docs/audits/AUDIT_lexica_rollout.md`;
  design backlog = `ENGINE_LESSONS.md`. The batch chronicle (phases, batch 3–5 sessions, V8
  promotion, δίκτυον/δόμα rulings, N=6-7, count 7/15, draw-cache ship) lives in those docs +
  TODO_ARCHIVE 2026-07-31 consolidation — do NOT re-derive it from here.**
  NEXT = εὐχαριστέω screens → eight queued words, straight-to-10, #30 live → GREEN activation.
  PENDING JP one-liner: add ναί/ὁμοίως/ποτέ to the ranker's STRUCT_BACKFILL list (flag-only).
  JP's hours variable — batch decisions when he's away, work normally when present; silence =
  pending.
  Open sub-items (standing):
  - Point `lexica_agreement.per_sense` at the new `_sense_spans` (still bold-only → a plain draw
    reads as a phantom sense-count wobble at batch scale).
  - Re-check the 80% / min-4 LXX-provenance cutoff at scale (tuned on 18 words).
  - Step-4 significance judge — voting sees THAT something varied, not whether it MATTERS; human
    eyes now, a model pass unproven.
  - Verbs + Hebrew first-batches = separate tracks.
  - **Seam next-stage ("Build A") — feed design undecided:** does anything besides a hand-forked
    word ever propose a seam (engine candidates into a triage queue), or does the register stay
    the only gate? JP rules before any build.
  - Small: the fork gate names a covenant-membership/NPP reading for dikaioō that `salvation_how`
    has no node for — add one via add_study_graph_salvation.py.
  - Coverage engine follow-ups (pieces A/B SHIPPED; flag gate tuned 163→73,
    scripts/audit_lexica_flags.py): wire `coverage_audit` to the card UI (stored-only today);
    eyeball G166 sense 4 (flagged thin); piece A could FORCE a missed collocation into the draw
    (warn-only today). Piece C (stratified sampling) DEFERRED — first evidence: huios+anthrōpos
    OT-generic vs NT-title conflation.
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
- **FULL AUDIT DONE 2026-07-02 — decision doc = `docs/audits/AUDIT_ask_corpus.md` (repo root).** Order = A → deploy +
  acceptance → B → D → C → E. Batches A (559283f), B (7b55783) and C (df60d22) SHIPPED → TODO_ARCHIVE.
  **Banner comes down after batches A+B verified live.**
  - **Owed (JP, post-deploy):** the #20B acceptance checks 1–5 PLUS the two mixed-signal cases baked
    into `tests/test_scope_detect.py` ("compare the OT and NT view of the Sabbath", "charis in greek
    and hebrew"). Batch B's live spot-checks were 4/5; the failing KJV-comparison case is the
    whole-book card below (Batch B didn't break it, it never worked).
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
- **Tier 1 cache — optional filler-strip normalizer** (fold "what does X mean" → "X"). (The scope
  fold SHIPPED 2026-07-03, `_CACHE_CODE_VER`→47, `tests/test_cache_key_scope.py`; **Tier 2 = NO-GO**
  at current volume, see docs/audits/AUDIT_ask_corpus.md.) The normalizer MUST reuse
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

## Licensing / attributions (page LIVE 2026-07-03; ABP wording DONE 2026-10-24 → TODO_ARCHIVE)
Full record — source→license map, the BY-SA share-alike bucket, the bdb-is-Strong's-Hebrew lesson:
memory `project_licensing_attributions`. `/credits` + CREDITS.md are LIVE, linked from the App About
page + the crawlable SEO footer. **The live page is `templates/seo/credits.html`, NOT CREDITS.md —
two copies, keep them in step.**
- **OPTIONAL courtesy:** a thank-you note to OpenBible.info (geo place-coords) — CC BY doesn't require it.

---

## abp_surface backfill arc — DONE 2026-07-11 (13,851 recovered printed forms, delta exact vs
pre-registration; record → TODO_ARCHIVE consolidation; design bank docs/RENDERING_OVERRIDES.md).
Open:
- **Versification map for the 148 off-by-one verses** (989 verse_missing slots) — GATED on eyeball
  review of neighbor content (a wrong map stores real-looking Greek from the WRONG verse). Slow path.
- **ἔπω-class tag-synonym rulings table** — the "absent" residual is hotspot-shaped (G2036 ἔπω =
  457 of 2,494); each synonym pair (ἔπω↔λέγω etc.) = ONE JP ruling applied corpus-wide via an
  explicit mapping table — NEVER fuzzy matching. One ruling ≈ 18% of residual.

## Reader display layers — ABP overrides + divine name — FUTURE LANE (parked)
RECOVERED 2026-07-28 from the 2026-07-12 design chat ("Creating an improved Greek LXX/NT
translation") — design was developed, never ticketed. Supersedes the same-day reconstructed
two-toggle sketch.
**Mechanism:** ONE shared span-override table; stored ABP text NEVER edited; every override
hand-ruled and auditable, tagged by class so the toggles operate independently.
1. **Toggle 1 — Lexica corrections (sense overrides).** Spans where ABP is arguably WRONG or
   inconsistent, not merely literal. Could arguably default ON someday — JP's ruling at build time.
2. **Toggle 2 — smooth reading (readability overrides). ABP ONLY.** Off by default, literal
   always one tap away. Grammar-class driven, not ad hoc: articular infinitives ("in the to be
   him" → "while he was"), substantival participles ("the ones being sick" → "those who were
   sick"), stacked genitive chains, δέ rendered as endless "And…", Greek-order fronted objects,
   plus the added-English-filler subclass ("son being twenty and three years old" → "son of
   twenty and three years" — subtraction beats ABP's paraphrase; "old" has no lemma behind it).
   Workflow: JP rules a PATTERN once → CC generates the spans mechanically (each still stored
   individually) → JP spot-checks a sample. **Hard bar: zero lemma loss — every English word on
   screen maps to a Greek word.** Design caveat preserved: ABP's woodenness IS its concordance
   transparency; smoothing is a mode, never a replacement.
3. **Toggle 3 — divine name display.** Show "Yahweh" where the text carries the name (tag-driven,
   H3068 vs H136 Adonai). Separate thread from 1–2 in the record (July 24 discussion). Related
   regardless of this toggle: AI-synthesis prose drifts Yahweh/YHWH/LORD and needs one ruled
   convention (already banked under "AI verse synthesis revisit").
Details re-ruled before build. Parked BEHIND batch one + the FRAME-0 audit; nothing waits on it.

## Lexica def-engine — small open tickets
- **Legacy redraw order — next dip = the 24 VERSE-SHORT cards.** The 3 `"None"`-marker cards
  (G2588/G4172/G3624) are DONE 2026-07-15 (cards 85→88, zero spend — record in
  `docs/audits/AUDIT_lexica_rollout.md`, top entry). Rules unchanged from JP's 2026-07-14 ruling: lazily, a few
  per session at most, development first, full current gate battery, no shortcuts.
  **GATE on the REMAINDER dips (reviewer-promoted 2026-07-27, batch-one re-verify):** before the
  first batch drawn from the remainder, RE-RANK the occ≥2 target list — it was computed pre-R-2;
  name slots now wear Greek numbers, so counts moved. The re-rank must EXCLUDE PN/name numbers
  (incl. any STEP G9xxx; PN-card minting is its own deferred ticket). Not blocking the verse-short
  dip.
  **G1484 (ἔθνος) FLOOR MOVED (2026-07-27 re-verify, pasted PA output):** 23 "greeks" name
  slots now share its pool — 6 OT slots CERTAIN-new (ex-H1471), 17 NT star slots pre-R-2 state
  unproven (xref lists ALL name slots, so listing ≠ changed); exact delta = the floor-diff at
  redraw. Only live card affected; join soundness 32,479=32,479 and OT coverage 10,462=10,462
  both proven on pasted output. The #30 floor-diff NOT-RUN waiver is DEAD for G1484 — any
  redraw of it reads the actual floor-diff, per-word ruling owed at that time.
  **BATCH ONE (verse-short dip) CLEARED TO SEND — reviewer's conditions met on pasted output
  2026-07-27:** check 1 fired (G1484 only), join 32,479=32,479, coverage 10,462=10,462, check 2
  empty with fire-proof covering all 85 rows (live cards = 85, DB-counted; "88" was a docs
  tally slip, closed record in TODO_ARCHIVE + memory + ENGINE_LESSONS #90). Unchanged prompt,
  stamp `lexica:f8c77bf889f6`, full gate battery, few per session.
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
