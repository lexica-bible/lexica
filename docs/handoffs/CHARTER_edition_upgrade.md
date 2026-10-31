# CHARTER — edition upgrade: Lexica's English line → the ABP app edition (DRAFT)

**Status: DRAFT, §8 RULED 2026-10-30 (§0.6). Nothing applied on PA; step 3 = PA read block + italic re-parse + --declared draft.**
Scoping record: step 1 findings (chat, 2026-10-30) + the lane (a) numbers in
`docs/handoffs/HANDOFF_abp_source_material.md`. Supersedes nothing yet; when ruled, it becomes the
one charter for the next full words rebuild.

## §0 Rulings carried in (JP, 2026-10-30, as given)
1. **Target text = the ABP app's current text, named "app edition" everywhere.** No "4th edition" /
   "3rd ed." labels — no file, page or PDF in hand carries an edition statement (step 1). The handoff's
   "3rd ed." / "4th ed." labels are struck as unsourced (done in this change).
2. **Mark 1:9 "Nazareth of the of Galilee" = our-side defect.** Held; fixed inside this rebuild (it is
   in the 29% and the app edition reads "Nazareth of Galilee"; the NT PDF agrees). Declared as a row.
3. **Gates A/B re-scope:** every rebuild lane pre-declares its expected count deltas (words, verses,
   abp_surface, header keys); the gates check against the declaration, not against "unchanged".
   Drafted in §4.5; NOT applied.
4. **Snapshot re-freeze moves AFTER the upgrade build, on the copy; "before" side = pre-upgrade
   live.** Recorded here as the resolution of the "snapshot staleness" blocker (TODO held item; charter
   rebuild-trap §8 "Open, for the edition-upgrade lane"). §6 step 9c.
5. **S9 merges into the upgrade: one rebuild, one gate block.** `HANDOFF_cert_session9.md` and
   `docs/audits/AUDIT_reassembly_rebuild.md` fold in here. **Reading to confirm (open Q1):** the S9 five
   fixes already landed — S11 ran the combined rebuild, passed the charter gate and swapped live on
   2026-07-06 (words pin 626,309; memory `project_abp_certification`). So what merges is S9's GATE
   BLOCK (discipline + current pins) and its parked items, not its fixes.

6. **§8 rulings (JP, 2026-10-30, verbatim):** "Q1 confirmed. Q2 keep two derivations; if the build can't
   produce them independently from one feed, report, don't collapse. Q3 re-parse cached HTML on PA for
   the <i> flag, add an italic column to the TSV before 0b; no refetch. Q4 English only. Q5 freeze
   10/24. Q6 redraw only the 29% set, own post-swap pass. Q7 deferred to the dry-run verdict; PA read
   sizes it first. Q8 land --declared before the rebuild, own checkpoint."

## §1 What this lane changes, in one line
The English words Lexica prints for ABP (per-slot `words.english` / `english_head`, and the clean
prose `verses.text`) move from the BibleHub scrape text (May–June 2026; BibleHub still prints it) to
the ABP app's text as fetched 2026-10-24. The Greek, Strong's numbers, names and positions are NOT the
target (§3). Everything else in the rebuild is the standing `/rebuild-words` procedure.

## §2 Source — the app edition
**Pages.** `https://www.apostolicbibleapp.com/Chapters/<Book> <n>.html`, one page per chapter, book
names from `/chapters.js` (the five one-chapter books listed as 0; page still "<Book> 1.html").
1,189 pages · 31,238 verses · 577,994 slots · 10 † footnotes (fetch of 2026-10-24, JP on PA).
**How fetched.** `scripts/fetch_abp_app.py` — read-only toward every database; never follows a redirect
(the site spell-corrects missing pages to a real chapter); checks every page's own `<title>`, cached
pages too; completeness probe requests chapter N+1 and requires a 404; two parser controls must pass
or it exits non-zero (Gen 25:15 "Cολδάδ" with Latin C survives verbatim; 1Ki 11:14 Αδάρ); one request
per second with a lexica.bible user agent. Output: `abp_app_html/abp_app_slots.tsv` (book, chapter,
verse, slot_index, strongs, greek, english — verbatim text, tabs/newlines folded). Third-party text:
gitignored, on PA and in the local checkout (`abp_helps/abp_app_slots_full.tsv` locally).
**Pinned hash: NONE YET.** The 10/24 TSV has no `.sha256` and is not in `cert_manifest.json`. This
charter requires, before the build: freeze the feed as `abp_app_slots_<date>.tsv` + `.sha256` (same
pattern as the fill snapshot), and add it to the certification manifest as a feed file. The manifest
pins the 66 `abp_texts/` files today; the app feed joins them (or replaces the English role of
`bh_scrape.db` — open Q2).
**Known properties of the source that the build must handle (all from lane (a), ruled where noted):**
- Numbering: our Psalm titles are verse 0 = the app's verse 1 (146 chapters). Pro 16 is REORDERED
  (ours 16:27–33 = app 16:20–26; app 16:2–9 = ours 16:5…16); Pro 24, Jer 10 partial one-verse
  offsets; Hab 3: app 3:20 = ours 3:19. **JP-ruled: NO renumber on our side** — the English is taken
  by the per-verse map from the audit's run output, our verse keys stay.
- Greek-side font defects (C→Χ Q→Θ H→Η O→Ο U→Υ R→Π П→Π +→ϊ; `DEFECT_MAP` in the audit): Greek is
  out of scope here, but 17–28 cells are English notes typed in the Greek font ("δαγγερ" = dagger,
  "- Φορ τηε ενδ.") and 28 English-in-Greek cells slipped past a Latin-letter check. The English
  column is clean of this class as far as read; a full-column check is a pre-build gate (§4.6).
- Glued slots exist in the source too (1Ki 11:21 "2036-* / είπεν Αδάρ / Hadad said"); compound
  Strong's come dash-joined ("4160-3588-2316 / εποίησεν ο θεός / God made").
- Bracket-order digits are kept verbatim in the English ("[3bring forth", "1the", "2waters]") —
  the same notation `abp_texts/` uses, so the existing bracket parser applies.
- Translator additions are `<i>…</i>` in the page; the fetch keeps the text but the italic flag is
  not a TSV column today (open Q3 — `words.italic` is served; a rebuild from the app must carry it).

## §3 Scope — English line only, with the Greek residual named
**In scope:** `words.english`, `words.english_head` (and its derived `english_head_norm`, step 11),
`verses.text`, the Mark 1:9 defect, and every artifact DERIVED from those (bracket ids / positions
where an English change adds or drops a slot — see the slot-count question below).
**Out of scope (stays as built from bh_scrape / abp_texts):** Greek forms, Strong's numbers,
`strongs_base`, names and the binding, `abp_surface` content (rebuilt by the standing chain, then the
fill restored), `pn_greek_identity` content.
**The Greek residual, so nobody reads "99.6%" as "the Greek needs upgrading too":** app Greek vs our
printed form (`abp_surface`) after accents + the defect map = OT 99.63% (302,095 slots) / NT 99.75%
(87,091). The remaining 0.37% / 0.25% is already censused and HELD in named buckets, none of them
"wrong Greek on our side":
- 4,058 slots where the app prints an inflected form and we show the dictionary word (no
  `abp_surface` row; 93.5% resolvable from the Analytical Lexicon — that is the fill lane, 4,411
  writes LIVE 10/25, and its leftovers);
- 751 surface mismatches + 291 identity rows where the app is inflected and our header is the
  nominative — by design (header vs page form);
- 544 our-side GLUED two-word forms (NBSP) where the app has one word — censused, no lane yet;
- 60 plain-η spots (app ἡ, ours η) — HELD, outside the fill;
- 540 + 13 same-slot NUMBER disagreements (incl. Isa 39:8 pos 1 suspected slot misalignment) —
  HELD, read-by-hand list; 152 Concordance-diff candidates alongside.
These stay their own lanes. **This charter does not take the app's Greek or numbers.** If JP wants
the Greek too, that is a different rebuild (the app's slot structure becomes ours) — open Q4.
**The real scope risk — slot counts.** English-only transplant needs the app's slot k to be our slot
k. Lane (a): 99.52% of our 626,309 slots align (in place 94.02% + swapped-one-place 5.33% +
out-of-sequence 1,055); the audit also reports "count-differs leftovers" (verses where the app has
a different number of slots) — their size is NOT in the handoff. A verse whose English change ADDS
or DROPS a word changes the slot count on the app side. Rule to pre-register (needs the PA read,
§5): the per-verse transplant is all-or-nothing — a verse is taken from the app only where every
slot pairs 1:1 by (position, Strong's) after the split-flip swap rule; count-differs verses are
listed, counted, and either (i) kept on the old text and censused, or (ii) taken with a declared
slot change. JP picks (i) or (ii) at the dry-run verdict; (ii) means positions move in those
verses, which the fill re-key and the header build already tolerate (reason 6 / geometry mode).

## §4 Gate block — one block, every gate pre-registered
Standing rule for every number below: a figure asserted about the built copy is derived THROUGH the
build with the same inputs, and the derivation is committed beside the number (rebuild-words 8b.2
TRAP). Controls fire on a known positive before any zero is trusted (CLAUDE.md certification rule).
### 4.1 The 7 certification invariants (`cert_invariants.py`, re-pinned in the swap commit)
1 row pins — **words will CHANGE** if (ii) in §3 is chosen; declared as a delta, not "unchanged";
`verses` 31,237 exact (no renumber); `abp_corrections_active` 30 → re-adjudicated (§4.7) · 2 split-flip
0 · 3 em-dash 0 (the app text's `--`/`—` handling is a pre-build check) · 4 corrections overlay intact
· 5 manifest = the NEW feed set (app feed added; §2) · 6 backup alive · 7 person/place binding. Plus
`--controls` all fire.
### 4.2 L9 split lint = 0 (`_split_compounds` redistribution)
Scope figures 18,384 / 12,718 (post-S11) are declared stale by construction: the English changes.
Re-derive on the built copy with the two harnesses agreeing on the SAME copy (S11 lesson), then
declare. The lint itself must still read 0.
### 4.3 Word-order — reassembly v1 AND v2 at criterion
`audit_reassembly_diff.py` (`--controls`, `--controls --v2` fire first; `tests/test_reorder_port.py`
green first — the port is the arbiter): **zero word-order + zero content-other + no NEW
punct-position.** The frozen punct allowlist (260 since S11) describes the OLD prose; new prose = a
new allowlist. Pre-register: re-count on the built copy, publish added/removed vs 260 as a member
list, freeze the new set in the swap commit. **This gate also decides open Q2:** `verses.text` and the
word rows must still be TWO derivations of the app feed (prose via a reorder of the app slots per
verse; rows via the build) so the diff stays an oracle — if both come from one flattening step the
gate measures nothing.
### 4.4 Phrase-gloss under-distribution — floor
`audit_phrase_gloss_underdist.py`: control Psa 39:1 FIRED first; FLAGGED beyond
`AUDIT_phrase_gloss_allowlist.txt` ≤ 671. The class is English-shaped, so the app edition can move it
both ways (the app edition may distribute phrases ABP's older text parked). Pre-register: the count
on the built copy, member list of newly flagged and newly cleared vs live; a NEW flagged row that is
not an app-edition wording change = stop. The deferred (g) FIX stays deferred (own pass, post-upgrade).
### 4.5 Declared-delta gates (the A/B re-scope — DRAFT, not applied)
Today `gate_greek_header.py` gate A demands `pn_binding`, `tipnr_entities`, `abp_surface`
byte-identical and `words`/`verses` counts unchanged; gate B demands `pn_greek_identity` keep the
same keys. Both ABORT on any full rebuild by design (10/25 overridden once). Draft change:
- A declaration file per lane, committed before the build and named in the run log:
  `tests/fixtures/<lane>/declared_deltas.json` holding: `words` (exact count, or `old + N` with N and
  its derivation), `verses` (exact), `abp_surface` (builder-chain total AND post-restore total),
  `pn_greek_identity` (key-set delta: rows whose (verse_id, position) key moves, with the member
  list file; the per-row SHAPE rule of gate B still applies to every surviving key), `pn_binding` and
  `tipnr_entities` (byte-identical stays the default; a lane that touches them declares members).
- The gate takes `--declared <file>`; without it, it behaves exactly as today (header-only lane).
  With it: each table's actual delta must EQUAL the declaration (count AND member list where one is
  declared); anything undeclared = FAIL, same wording as today. "Unchanged" is just a declaration of
  0. The 10/25 run's figures (3 Michaiah relabels, 21 header rows, 519 / 501 G5) become the first
  worked example of a declaration.
- **New file + new flag = JP checkpoint before landing** (memory `feedback_new_fields_checkpoint`).
  Not applied in this change.
### 4.6 Pre-build source checks (before step 2; on the feed, not the db)
- English column: 0 cells with Greek letters or the Greek-font classes (the 17–28 English-in-Greek
  cells are Greek-column; confirm the English column is clean — full column, not a sample).
- `--` / em-dash and bracket-digit shapes match the parser's grammar (count of `[`, `]`, digits
  per verse balanced; the S9 (f) class — a `]` with no `[` — counted and listed before the build,
  Tier B rows written for genuine source defects, never silently tolerated).
- † footnote cells excluded (they are `.g` spans; kept in `abp_app_slots_notes.tsv`).
- Versification map applied and printed per verse (Psalms shift, Pro 16 map, Pro 24 / Jer 10 /
  Hab 3) — the count of mapped verses must equal the lane (a) figures.
### 4.7 Tier B overlay re-adjudication
`abp_corrections` has 30 active rows; several correct ENGLISH-side source defects in the OLD text
(S9-f prose ×5, Jer 9:23 order-digit typo ×2, the bracket-order rows). Each is re-read against the
app edition before the build: cured upstream → retire (count declared); still present → stays; new
app-edition defects → new Tier B rows, pre-registered. The overlay is never bypassed.
### 4.8 The standing chain figures that MUST be re-declared (not assumed)
`finish_rebuild.sh` import_tipnr matched 31,649 · `Words inserted` 626,305 + 4 · `Split 80 merged
subject-name(s)` · PN-star A 1,505 + B 2,552 · restore_frozen_pn 8 · five-class identity split
3,671 / 10,236 / 12,182 / 4,412 / 1,977 · serving deltas +9 / 2,190 / 1,523 · lane-3 step PASS ·
G5 519 / 501 · CHIP genuine 3 · A1 177 · tier-2 ~92% · abp_surface builder chain 391,130 · restore
placed 4,411 (4,057 strong / 354 weak), unplaced 0 · G1 395,003 · health floor 395,003. Every one
of these was pinned on a same-text rebuild. An English-line change can move the English-keyed ones
(anything that reads `english`: the subject-name split, PN-star B, the fill's key 1, the floor). The
rule: each is re-derived on the built copy and the difference attributed member by member before
the swap; none is forced.
### 4.9 The fill restore under new English (step 9a)
Re-key ruling 10/25: key 2 (verse_id + ordinal of Strong's in verse) primary, key 1 (verse_id +
Strong's + english) cross-check; "a slot whose English changes cannot pass key 1 … on the
English-line edition upgrade it is the 29% case" (charter rebuild-trap §3). So on this lane the
restore's **reason 6 is expected to be large, and `--prefill` (G1b) is dropped** (rebuild-words 9a).
Pre-register: the dry run's placed / agree-strong / agree-weak / reason-6 split is read as a
MEMBER list against the 29% verse set — a reason-6 slot OUTSIDE a changed-English verse is a real
miss, inside one is expected. Decision for JP at the dry-run verdict: restore by key 2 alone on
reason-6 slots inside changed verses (declared), or leave them to the Analytical-Lexicon fill as a
follow-up. Then the re-freeze (§6 9c).
### 4.10 Mark 1:9
Declared row: Mark 1:9 slot "of the" (τῆς, G3588) — old `english` "of the", new per the app
edition (blank or the app's value). The row appears in the compare_words diff by name.

## §5 Pre-registered figures — what is known now vs what needs a PA read
**Predictable now (local TSV + lane (a) run records):**
| figure | value | source |
|---|---:|---|
| app pages / verses / slots | 1,189 / 31,238 / 577,994 | fetch 10/24 |
| verses with different English words | 9,157 / 31,228 paired (29.3%; OT 30.6, NT 25.6, Psalms 17.2) | audit v2 10/24 |
| of which order-only | 3,191 | audit v2 |
| our slots aligning | 99.52% of 626,309 (in place 94.02 · swapped 5.33 · out-of-seq 1,055) | audit v2 |
| Psalm-title shift chapters | 146 | audit v2 |
| versification exceptions | Pro 16 (reorder), Pro 24, Jer 10, Hab 3 | audit v2, ruled |
| English-in-Greek-font cells | 17 (Latin-letter check) + 28 (all-Greek-letter notes) | audit v2 / lexicon join |
| † footnotes | 10 | fetch |
| proxy drift vs `abp_texts/` (local, ex-Psalms) | 8,605 / 28,295 = 30.4% | step 1 |
| 20-verse census | 19 wording / 1 our-side defect (Mark 1:9) / 0 app-format | step 1, spot check |
**Need a PA read (all read-only, before any build):**
- count-differs verses and their slot delta (the §3 all-or-nothing set) — the audit prints it, the
  handoff did not keep it;
- live `verses.text` vs `abp_texts/` prose agreement (the step-1 proxy assumed they match; the
  manifest pins the files, so a 0 here is expected but must be read);
- the current reassembly counts on live (v2 word-order 0 / content-other 0 / punct 260 expected);
- phrase-gloss FLAGGED on live (702 raw / 671 beyond allowlist expected);
- `abp_corrections` rows whose target text the app edition changes (§4.7 list);
- the fill restore dry run's reason-6 size on an English-changed copy (§4.9) — can only come from a
  copy build;
- `pn_greek_identity` keys whose (verse_id, position) would move under (ii) — the header-build
  geometry census the TODO already owes (8b.3 ordering item);
- `lexica_def` / summaries / AI cache rows quoting ABP verse text (the frozen-text blast radius, §7).

## §6 Ordering — the `/rebuild-words` checklist with this lane's changes
Step numbers are the checklist's labels; arrows are the run order.
0 git pull on PA + prove the build code is in the file →
**0b (NEW) freeze the app feed:** hash the fetched TSV, write `.sha256`, add to the manifest; the
fetch is NOT re-run at build time unless JP rules a refresh (open Q5) →
1 rollback copy `bible_pre_edition_upgrade_<date>.db` + `<src>` copy of live →
1a snapshot check on `<src>` — must print SNAPSHOT CURRENT (proves live's fill is what we froze;
unchanged by this lane) →
**1b (NEW) pre-build source checks (§4.6) + Tier B re-adjudication (§4.7), both read-only** →
2 build from the NEW feed into `<built>` (the build takes the app English through the standing
bracket parser; `verses.text` through the prose loader on the same feed, independently — §4.3) →
3 finish_rebuild (tail) — `done` line or no swap →
8b.0 → 8b.1 → 8b.2 → 8b.2a → 8b.3 (header gate run with `--declared`, §4.5 — until that lands,
A/B abort here and need a member-by-member ruling, as 10/25) →
11 rendering norm (copy) → 10 two-ending read (copy) →
9 surface rebuild on `<built>` (builder-chain total re-declared, not 391,130) →
9a fill restore WITHOUT `--prefill`; dry run → verdict on the reason-6 member list (§4.9) → apply →
9b health floor (floor re-declared from the new chain total + the restored inserts) →
**9c (NEW, resolves the staleness blocker) RE-FREEZE on `<built>`:** `snapshot_surface_fill.py`
in replace mode by ruling, source = `<built>` after 9a, "before" side = `<src>` (pre-upgrade live).
New frozen file + `.sha256`; pin updated in `restore_surface_fill.py` in the same change; the 10/25
pre-fill copy is released from its load-bearing role once the new freeze passes its own `--check`
against a fresh copy of the swapped live (then rotation rules apply to it again) →
4 compare_words vs live — per-COLUMN attribution: `english` / `english_head` / `verses.text` rows =
the declared 29% set + Mark 1:9; ANY `strongs` / `strongs_base` / `position` / `morph` delta outside
the declared (ii) set = stop →
5 strongs_base invariant 0 →
6 audits (all floors re-declared per §4.8) + the S9 block (§4.1–4.4) →
7 spot-check (1Ch 13:10 chip order, Eze 31:9, 1Chr 1:1; add Gen 1:21 "sea monsters", Mark 1:9) →
8 swap + deploy.sh — the only live action; G5 recorded; then cert_invariants on live, pins +
manifest + allowlists + the new snapshot all re-pinned in the ONE swap commit.

## §7 Rollback
- File: `mv bible_pre_edition_upgrade_<date>.db bible.db` + deploy.sh reload (G2 rule). Keeps the
  receipted name (ops.md retention item 1) until three nightlies postdate the swap AND pass.
- Code: the swap commit re-pins everything (cert pins, manifest, punct allowlist, phrase-gloss
  allowlist, L9 scope, health floor, snapshot sha). Rolling the file back without reverting that
  commit leaves every gate red; roll both or neither.
- The 10/25 pre-fill copy and the 10/25 frozen snapshot are NOT deleted before 9c's new freeze has
  passed `--check` against the swapped live — until then they are the only working restore path.
- AI cache rows written between the copy and the swap are dropped by the swap (record the count).
- **Frozen verse text in `lexica_def` / summaries:** the Lexica card renders verse text frozen from
  `def_json`, copied from `verses.text` at build (S9 render trace). After the swap every card quotes
  the OLD edition until redrawn. This is a blast-radius item, not a rollback item — §8 Q6.

## §8 Open questions — RULED 2026-10-30 (see §0.6); struck
~~1. **S9 reading:** confirm "S9 merges" means its gate block + parked items (phrase-gloss fix,~~
~~v2 wired into cert_invariants, punct allowlist) ride this rebuild — the five fixes landed S11.~~
~~2. **Two derivations:** keep `verses.text` as an independent derivation of the app feed (prose via~~
~~its own reorder of the slots) so v2 stays an oracle — or accept one flattening and lose the gate?~~
~~Recommendation: keep two.~~
~~3. **Italics:** the fetch does not keep the `<i>` flag as a column. Add it to the TSV (a refetch, or~~
~~re-parse the cached HTML — the pages are on PA) before the build, since `words.italic` is served.~~
~~4. **Scope:** English only (this charter), or the app's slot structure too (Greek + numbers)? The~~
~~count-differs set (§3) decides how clean "English only" can be; read it first.~~
~~5. **Feed refresh:** build from the 10/24 fetch as frozen, or refetch at build time? (The app has~~
~~no version marker; a refetch can silently move the target.) Recommendation: freeze 10/24.~~
~~6. **Frozen quotes:** redraw policy for `lexica_def` / summaries quoting ABP verses after the swap —~~
~~all, only the 29%, or none (cards keep the old wording until their next natural redraw)?~~
~~7. **Count-differs verses:** rule (i) keep old text + census, or (ii) take with declared slot moves?~~
~~8. **Order of landing:** the A/B `--declared` change (§4.5) is a code change with a new file; land it~~
~~before this rebuild (own checkpoint), or ride the 10/25-style member-by-member override once more?~~

## §9 Step 3 (2026-10-30) — the PA read block, the italic re-parse, the --declared draft
### 9.1 ONE read-only PA block (JP runs; every tool given the live path; nothing writes bible.db)
Paste in order from `~/bible-db` after `git pull`. Expected values beside each; a different figure is
READ, never forced. Outputs land in `~/` (small text files), not in the repo.
```
cd ~/bible-db && git pull && git log --oneline -1
# (a) count-differs verses + slot delta  — expected: unknown (the audit printed a per-book
#     column on 10/24 but no total); records the §3 set. Member TSV -> ~/count_differs_members.tsv
python3 scripts/census_count_differs.py ~/bible-db/bible.db abp_app_html/abp_app_slots.tsv --out ~/count_differs_members.tsv 2>&1 | tee ~/edition_a_count_differs.log | tail -80
# (b) live verses.text vs the pinned feed through load_abp_prose — expected: RESULT: AGREE, 0 diffs
#     (any DIFF line = the step-1 proxy was off for that verse; read every line)
python3 scripts/compare_prose_feed.py ~/bible-db/bible.db 2>&1 | tee ~/edition_b_prose_agree.log | tail -40
# (c) reassembly on live — controls first (must FIRE), then the corpus report
#     expected: word-order 0 · content-other 0 · punct-position 260 (the frozen S11 allowlist) · dup-gloss 0
python3 scripts/audit_reassembly_diff.py --controls 2>&1 | tail -12
python3 scripts/audit_reassembly_diff.py --controls --v2 2>&1 | tail -12
python3 scripts/audit_reassembly_diff.py ~/bible-db/bible.db 2>&1 | tee ~/edition_c_reassembly.log | tail -40
# (d) phrase-gloss under-distribution on live — expected: CONTROL: FIRED · FLAGGED 702 raw ·
#     FLAGGED BEYOND allowlist 671 (S11 figures; the 10/25 rebuild may have moved them — record)
python3 scripts/audit_phrase_gloss_underdist.py ~/bible-db/bible.db 2>&1 | tee ~/edition_d_phrase_gloss.log | tail -30
# (e) the Tier B rows the app edition can touch — expected: 30 active rows; this lists every
#     active row with its verse, slot, column, source value and corrected value (CC diffs each
#     against the app TSV locally — the TSV is in the local checkout)
sqlite3 -header -separator $'\t' ~/bible-db/bible.db "SELECT id, book, chapter, verse, position, field, source_value, corrected_value, ledger_ref, applied_at FROM abp_corrections WHERE status='active' ORDER BY book, chapter, verse, position" | tee ~/edition_e_corrections.tsv
sqlite3 ~/bible-db/bible.db "SELECT status, count(*) FROM abp_corrections GROUP BY status"
# (f) frozen-quote blast radius — expected: unknown, record. lexica_def rows (every card quotes
#     verse text frozen from verses.text at build), AI cache rows by category (ver_key prefix)
sqlite3 ~/bible-db/bible.db "SELECT count(*), sum(def_json LIKE '%\"text\"%') FROM lexica_def"
sqlite3 ~/bible-db/bible.db "SELECT CASE WHEN instr(ver_key,':')>0 THEN substr(ver_key,1,instr(ver_key,':')-1) ELSE ver_key END AS category, count(*) FROM ai_search_cache GROUP BY 1 ORDER BY 2 DESC"
# (g) the REAL pn_binding values behind the --declared worked example (Q8 prep) — the 3 Michaiah
#     binds, pre-swap copy vs live. pn_binding.book is a NUMBER (memory tripwire) — filter by name.
#     expected: 3 rows each side, same entity, rule differs (pre: the ruled/spelling value; live: fuzzy)
ls -l ~/bible-db/bible_pre_trapwire_swap.db
sqlite3 -header -separator $'\t' ~/bible-db/bible_pre_trapwire_swap.db "SELECT book, chapter, verse, name, entity_uniq, kind, rule, render, hot, tier FROM pn_binding WHERE name LIKE '%ichaiah%' ORDER BY book, chapter, verse" | tee ~/edition_g_michaiah_pre.tsv
sqlite3 -header -separator $'\t' ~/bible-db/bible.db "SELECT book, chapter, verse, name, entity_uniq, kind, rule, render, hot, tier FROM pn_binding WHERE name LIKE '%ichaiah%' ORDER BY book, chapter, verse" | tee ~/edition_g_michaiah_live.tsv
# (h) the italic re-parse — CLEARED for the full run (JP 2026-10-30). No network, no db.
#     expected: 1,189 pages · 577,994 slots · SELF-CHECK PASS · italic rate near the 7.01% local sample
python3 scripts/reparse_abp_app_italic.py --tsv abp_app_html/abp_app_slots.tsv --out abp_app_html/abp_app_slots_italic.tsv 2>&1 | tee ~/edition_h_italic.log | tail -20
```
**JP clearances (2026-10-30, verbatim):** "§9.1 read block: cleared as written. (a)/(b) are first runs of
new scripts — any surprise there is read as script behavior first, data second; say which before
recording." · "Italic re-parse: cleared for the full PA run. Expect SELF-CHECK PASS; record the italic
count and rate against the 7.01% local sample. 0b freezes the new TSV, not the 10/24 one." ·
"--declared draft: read, not ruled yet. Before I rule: read the real pn_binding from-values off the
10/25 copies on PA … then bring the four checkpoint points to me."
Read-only proof: `census_count_differs.py`, `compare_prose_feed.py`, `audit_reassembly_diff.py`,
`audit_phrase_gloss_underdist.py` all open the db with `mode=ro`; the `sqlite3` lines are SELECTs.
`compare_prose_feed.py` and `census_count_differs.py` are NEW read-only tools (this change), reusing
the production parser / loaders — not yet run anywhere (no local db); their first run is this one.
What CC does with the output: (a) sizes Q7 and the §3 rule; (b) confirms or retires the step-1 proxy;
(c)/(d) become the "live before" column in §4.3 / §4.4; (e) each row gets an app-edition verdict
(cured / still present / not applicable) in §4.7; (f) sizes the Q6 post-swap redraw pass.
### 9.2 Italic re-parse (Q3) — `scripts/reparse_abp_app_italic.py`, NEW, no network, no db
Re-parses the cached pages under `abp_app_html/` with the fetch's own parser (subclassed only to see
`<i>…</i>` inside the English cell) and writes `abp_app_slots_italic.tsv` = the seven 10/24 columns +
`italic` (0/1) + `italic_words`. Refuses to write unless the seven columns match the 10/24 TSV on
every slot (keys and bytes), the controls pass (Gen 25:1 "was", Gen 25:3 "the", Psa 3 "to" ×2 italic;
Gen 25:15 Hadar not italic), and no flag sits on an empty English cell. **Dry run 2026-10-30, local,
on the 18 cached chapters the local checkout has (7,898 slots, same pages PA holds): SELF-CHECK PASS,
554 italic slots (7.01%), 0 anomalies.** The full run is PA's (1,189 pages). Then 0b freezes the
NEW TSV (with the column), not the 10/24 one.
### 9.3 `--declared` gate (Q8) — DRAFT at `docs/handoffs/drafts/DRAFT_gate_declared.patch.md`
Proposed diff + the first declaration file (the 10/25 run as the worked example). Not applied;
checkpoint. The example's `pn_binding` from-values are quoted from charter prose and must be read from
the 10/25 copies before the file is committed.
