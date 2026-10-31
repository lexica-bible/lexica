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
8. **§9.4 rulings (JP, 2026-10-30, verbatim):** "Tail classification accepted. Boundary-move pairs are a unit:
   if a later lane takes one half it takes both." · "v2 word-order on live non-zero (Joh 14:26): read as a live
   defect until the member list says otherwise. §9.5 (a) counts it; if >0 after review, its own TODO line —
   the 10/25 rebuild is the suspect, check pre-swap copy for the same hit." · "Cert pin 30→51: fix as its own
   commit (pin + member list), not in the upgrade lane. Deploy rides the next deploy." · "Gen 52–55: 0b waits on
   §9.5 (b)." · "§9.5 cleared, read-only."
9. **§9.5 rulings (JP, 2026-10-30, verbatim):** "Joh 14:26: live defect, own TODO line; fixed in the upgrade
   rebuild as a declared row, not a live patch. (a) dates it." · "Punct 260: never a member list, so never a real
   gate. The 241 live members become the first frozen member file; retire the 260 pin with a note. Not a
   defect." · "Gen 52–55: move aside, not delete. Re-parse hashes must match before 0b step (1). Show 0b (1)
   output before the manifest code change." · "§9.6 cleared."
10. **§9.6/9.7 rulings (JP, 2026-10-31, verbatim):** "Joh 14:26 dating accepted (7/06–10/25 window, untraced);
   declared row stands. Punct 260 retired, 241 member file frozen. Feed hash 7bd77385 pinned." · "§9.7
   cleared: 0b (1) writes the .sha256; no database touched. After (a) shows OK, the manifest change as its
   own commit; show diff before JP pulls."
7. **Step-3b rulings (JP, 2026-10-30, verbatim):** "Corrections verdicts accepted (33 retire / 12 re-author /
   6 re-check). 30-vs-51 pin: item (i) reads it; if cert_invariants is red on live today, log as its own TODO
   line — a live gate failure." · "--declared checkpoints: all four as recommended (tight key; pinned before
   step 9; fixtures committed; three-case test with the change). Build the draft after (g); still not
   applied." · "Four extra pages: name them before 0b." · "§9.4 block cleared, read-only, same terms as 9.1.
   (b) v2 on live: expected word-order 0, content-other 0, punct 260."

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
**PINNED HASH (0b step (1) done 2026-10-31 03:41 on PA):** the frozen feed is
`abp_app_html/abp_app_slots_italic.tsv` (25,526,878 bytes; 9 columns = the 10/24 seven + italic + italic_words),
**sha256 `7bd77385a80de3c3a762b9427658dfec4163d4882f5a3ea56be10ff61436cf63`**, written beside it as
`abp_app_slots_italic.tsv.sha256` (104 bytes). Two independent re-parses of the cache produced that same
hash (one with the 4 stale files present, one with the cache clean). Step (2) = `cert_manifest.py` lists it
as a required feed (commit 6d60a466); step (3) the json re-pin on PA (§9.8); step (4) = this line. A second
copy of TSV + `.sha256` goes to the local checkout by scp (read-only touchpoint).
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
slot change.
**MEASURED 2026-10-30 (PA, `census_count_differs.py`, first run; it reuses the audit's own loaders):**
paired 31,228 · ours-only 9 · **count-differs 1,849 (OT 1,451 · NT 398)** = 619 where the English words
also differ + 1,230 same-words (split/merge shape, not wording) · delta −1: 1,197 · +1: 437 · ±2: 149 ·
|delta| ≥ 5: 40 verses (18 negative, down to −45; 22 positive, up to +24) · our slots left unpaired in
these verses 2,325 · app sub-slots unpaired 1,290 · members `~/count_differs_members.tsv` (PA). Top books:
Psa 182, Job 122, Eze 118, Isa 108, Jer 90, Pro 81, Lam 81.
**Q7 RULED (JP 2026-10-30): (i)** — the 1,849 keep the OLD text in this rebuild, censused as a member list,
taken in a follow-up lane. The |delta| ≥ 5 tail (40 verses) is censused separately: alignment failure vs
real edit — 10 read by hand first (§9.4 (c)).

## §4 Gate block — one block, every gate pre-registered
Standing rule for every number below: a figure asserted about the built copy is derived THROUGH the
build with the same inputs, and the derivation is committed beside the number (rebuild-words 8b.2
TRAP). Controls fire on a known positive before any zero is trusted (CLAUDE.md certification rule).
### 4.1 The 7 certification invariants (`cert_invariants.py`, re-pinned in the swap commit)
1 row pins — **words will CHANGE** if (ii) in §3 is chosen; declared as a delta, not "unchanged";
`verses` 31,237 exact (no renumber); `abp_corrections_active` **51 on live (read 2026-10-30; the suite's PIN still says 30 — §9.4 (i))** → re-adjudicated (§4.7) · 2 split-flip
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
punct-position.** The punct "allowlist" was frozen as a NUMBER only (S9 pre-registered 260; the S9 build
OBSERVED 240 — "OPEN TENSION, do NOT treat 240 as a failure", `CHARTER_cert_session9.md:67`); no member
file exists in the repo. **Live 2026-10-30 reads 241.** Pre-register for this lane: the live 241 members
are dumped and FROZEN AS A FILE before the build (the first member list this class ever had), the built
copy's set is diffed against it member by member, and the new set is frozen in the swap commit.
**RULED 2026-10-30 (§0.9): the 260 pin is RETIRED — it was never a member list, so never a real gate; not a
defect. The 241 live members (`~/punct_members_live_20261030.txt`, PA, 241 lines; pre-swap copy reads the same
241) are the first frozen member file: committed as `tests/fixtures/reassembly/punct_members_live_20261030.txt`
once copied down (§9.7 (b)). The gate for this lane = member diff against that file, nothing numeric.** **Live before (2026-10-30):** v1 bag report on live = 0 hits
(dup-gloss 0 · content-other 0 · punct-shift 0; 12,611 bracketed verses excluded from the punct tier); both
control sets FIRED. **The v2 order-aware run on live was NOT in the block — my omission, not data; §9.4 (b).**
**This gate also decides open Q2:** `verses.text` and the
word rows must still be TWO derivations of the app feed (prose via a reorder of the app slots per
verse; rows via the build) so the diff stays an oracle — if both come from one flattening step the
gate measures nothing.
### 4.4 Phrase-gloss under-distribution — floor
`audit_phrase_gloss_underdist.py`: control Psa 39:1 FIRED first; FLAGGED beyond
`AUDIT_phrase_gloss_allowlist.txt` ≤ 671. The class is English-shaped, so the app edition can move it
both ways (the app edition may distribute phrases ABP's older text parked). Pre-register: the count
on the built copy, member list of newly flagged and newly cleared vs live; a NEW flagged row that is
not an app-edition wording change = stop. The deferred (g) FIX stays deferred (own pass, post-upgrade).
**Live before (2026-10-30):** CONTROL Psa 39:1 FIRED · FLAGGED 693 · FLAGGED BEYOND allowlist 662 (gate ≤ 671)
· NO-EVIDENCE 1,814. S11 recorded 702 / 671 / 1,785: the 10/25 rebuild moved 9 flagged rows out and 29 into
no-evidence — cause not read; the member diff is owed before this lane re-baselines the floor (§9.4 (h)).
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
  **Run locally 2026-10-30 on the full 10/24 TSV (577,994 cells): Greek-letter cells 0 · footnote-marker
  leaks 1 — 1Pe 3:12 slot 19 reads `the earth\dagger\cvnote3:10-12 See Ps. 34:12-16..` (the footnote
  typed INLINE in the English cell, so the fetch's title-based † skip could not see it). Pre-registered
  cleanup: strip `\dagger\cvnote…` to the end of the cell, exactly this one slot, declared by member; a
  second such cell anywhere = stop and re-scan.**
- `--` / em-dash and bracket-digit shapes match the parser's grammar (count of `[`, `]`, digits
  per verse balanced; the S9 (f) class — a `]` with no `[` — counted and listed before the build,
  Tier B rows written for genuine source defects, never silently tolerated).
- † footnote cells excluded (they are `.g` spans; kept in `abp_app_slots_notes.tsv`).
- Versification map applied and printed per verse (Psalms shift, Pro 16 map, Pro 24 / Jer 10 /
  Hab 3) — the count of mapped verses must equal the lane (a) figures.
### 4.7 Tier B overlay re-adjudication
**Live read 2026-10-30: 51 active rows (not 30), 6 superseded** — 24 pre-BD rows (S9-f prose ×5, S10 Act 7:3 ×4
+ Mat 20:29 ×1, L2 ×4, L5 ×2, L10 ×4, L11 ×2, JER9:23 ×2) + 27 `BD-*` bracket-digit rows (13 verses, landed
after the pin). **Per-row app-edition verdict (CC, 2026-10-30, every row against the 10/24 app TSV; prose rows
through the production bracket reorder; Psa 116:1 read at the app's 116:2 under the title shift):**
| verdict | rows | members |
|---|---:|---|
| CURED upstream — the app already reads the corrected text / digits / number | 33 | prose 12: 1Ch 22:15, 1Sa 17:8, 1Sa 21:11, 2Sa 16:18, Job 24:18, Job 24:19, Job 39:13, Mar 16:17, Mat 20:29, Mat 21:19, Mic 1:13, Psa 116:1 · greek_pos 11: their BD siblings + Exo 32:3 ×3 (app digits 1–7 = our corrected 5/7/6) + S10-mat2029 · slots 10: L2 ×4 (app slot = 1475.3 "of their buttocks."), L10 ×4 (app = 3756-241.2), L11 ×2 (app = 165) |
| STILL PRESENT — the app repeats the defect (duplicate / missing bracket digit) | 12 | prose 6 + greek_pos 6: 1Sa 9:3 (6…6), 2Ch 10:13 (2…2), Jer 3:7 (1…1), Jer 9:23 (2…2; app also reads "wise one"), Neh 12:43 ("with great" carries no digit), Rev 11:1 (2…2) |
| N/A — a Lexica-side ruling, not a source defect the app could cure | 6 | L5 Dan 4:33 ×2 (app files αὐτός under 1473, ABP's convention; our 846 stands) · S10 Act 7:3 ×4 (our split slots; the app has ONE compound slot 302-1473-1166 "I will show to you!") |
**Consequence for the build (pre-registered):** every row's `source_value` is a PRECONDITION written against the
OLD text. On the app feed: the 33 cured rows must be RETIRED by member (a silent precondition skip is not
acceptable); the 12 still-present rows must be RE-AUTHORED with the app-edition `source_value` (wording may
differ — Jer 9:23 "wise one"), same `corrected_value` where the fix still applies; the 6 N/A rows keep their
precondition only if the build still produces the same slot (Act 7:3's split, Dan 4:33's 1473) — checked on
the copy. New app-edition defects → new rows, pre-registered. The overlay is never bypassed. `cert_invariants`
pin: 30 → the post-build active count, in the swap commit.
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
### 4.10 Declared single rows — Mark 1:9 and John 14:26
- Mark 1:9 slot "of the" (τῆς, G3588) — old `english` "of the", new per the app edition (blank or the app's
  value). Appears in the compare_words diff by name.
- **John 14:26 (added 2026-10-30, §0.9):** the live word-order hit — rows read `spirit holy,` (Greek order,
  no bracket digits) where the prose reads `the holy spirit,`. Declared outcome on the built copy: v2
  word-order 0 with Joh 14:26 clean (either the app edition's slots carry the digits, or the build's pair
  handling places them); if the built copy still shows the hit, the lane STOPS on it — it is not carried
  forward as "known". Member-level, not a count.

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
**PA read 2026-10-30 (block §9.1) — recorded in §3 (a), §4.3/4.4 (c)(d), §4.7 (e); (b) and (f) here:**
- (b) live `verses.text` vs `abp_texts/`: DIFFER — the 13 visible verses are ALL active correction verses
  (S9-f / BD-*): live is the corrected text, the feed is the raw source. **JP ruling: abp_texts/ RETIRED as
  the live stand-in for live-vs-app comparison; record, no action.** My block's `tail -40` cut the header
  and any earlier lines (13 × 3 lines + RESULT = exactly 40) — the block, not the data; 18 prose rows are
  active, so about 5 more DIFF lines sit above the cut. Full count: §9.4 (a).
- (f) frozen-quote scope (Q6 redraw pass): `lexica_def` 85 rows, all 85 carry verse text; `ai_search_cache`
  by category: summary 1,249 · xref 608 · pn 345 · chrono 136 · search 18. Which categories embed ABP verse
  text is a code read not yet done (summaries certainly; xref / pn / chrono / search unknown).
**Originally listed as needing a PA read:**
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
**0b (NEW) freeze the app feed** = `abp_app_html/abp_app_slots_italic.tsv` (the 9-column TSV from the
italic re-parse — JP 10/30: "0b freezes the new TSV, not the 10/24 one"; Q5: no refetch). Steps, SHOWN for
the gate, NOT run (§9.3): (1) on PA `sha256sum abp_app_html/abp_app_slots_italic.tsv >
abp_app_html/abp_app_slots_italic.tsv.sha256`, a second copy of both in the local checkout; (2) a CODE
change, own small commit: `cert_manifest.py` `feed_files()` gains one entry after the bh_scrape line —
`files.append(("abp_app_html/abp_app_slots_italic.tsv", BASE_DIR / "abp_app_html" / "abp_app_slots_italic.tsv"))`,
missing file = hard error like the others; (3) on PA `python3 scripts/cert_manifest.py build` — expected
75 → 76 files, the 75 old hashes UNCHANGED (diff the json before/after), the TSV's hash = (1)'s; (4) pin that
hash here. Before (1): the 1,193-vs-1,189 page question (§9.3) is answered →
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
554 italic slots (7.01%), 0 anomalies.** **FULL PA RUN 2026-10-30 03:00 (JP): 1,193 pages re-parsed ·
577,994 slots (= the 10/24 TSV, every key and byte) · 0 anomalies · 4 controls PASS · italic 38,004 / 577,994
= 6.58% (local sample 7.01%) · SELF-CHECK PASS → `abp_app_html/abp_app_slots_italic.tsv` written.**
**1,193 pages vs the fetch's 1,189:** the fetch caches ONLY a page whose own title matches its file name
(`get_chapter`), so the 4 extra files are real chapters, not spell-corrected redirects. The fetch's
completeness probe requests chapter N+1 after each book and, when the page exists, fetches, caches and
PARSES it into the same rows (the "count gap" it reports). Hypothesis: 4 chapters that `chapters.js`
undercounts, already inside the 577,994 slots. A hypothesis until §9.4 (d) names the 4 files. The re-parse
should have printed them itself: it gains a "page files beyond chapters.js" line (anomaly-grade, not a stop)
in the same change as the 0b code.
### 9.3 `--declared` gate (Q8) — DRAFT at `docs/handoffs/drafts/DRAFT_gate_declared.patch.md`
Proposed diff + the first declaration file (the 10/25 run as the worked example). Not applied;
checkpoint. The example's `pn_binding` from-values are quoted from charter prose and must be read from
the 10/25 copies before the file is committed.

### 9.4 Next PA block (read-only; nothing writes bible.db) — after `git pull` from `~/bible-db`
Every item below is either a figure my §9.1 block failed to capture (a, b: my omissions) or a read the
10/30 rulings ask for. Expected values beside each; a different figure is read, never forced.
```
cd ~/bible-db && git pull && git log --oneline -1
# (a) the FULL prose-compare picture — expected: 18 DIFF lines (one per active verses.text row), 0 only-live/only-feed
head -3 ~/edition_b_prose_agree.log; grep -c "^  DIFF" ~/edition_b_prose_agree.log; grep "^  DIFF" ~/edition_b_prose_agree.log
# (b) reassembly v2 (order-aware) on live — expected: word-order 0 · content-other 0 · punct-position 260
python3 scripts/audit_reassembly_diff.py ~/bible-db/bible.db --v2 2>&1 | tee ~/edition_c2_reassembly_v2.log | tail -40
# (c) the |delta| >= 5 tail of the count-differs census — expected: 40 rows
awk -F'\t' 'NR==1 || ($7 >= 5 || $7 <= -5)' ~/count_differs_members.tsv | tee ~/count_differs_tail.tsv
# (d) the 4 page files beyond chapters.js — expected: 4 lines, each a "<Book> <n>.html" whose n exceeds the book's chapter count in chapters.js
python3 - <<'PY'
import os, re
names = re.findall(r"\['[^']*',\s*'([^']*)',\s*(\d+)\]", open('abp_app_html/chapters.js', encoding='utf-8').read())
cnt = {n: int(c) for n, c in names}
for fn in sorted(os.listdir('abp_app_html')):
    m = re.match(r'^(.*\S) (\d+)\.html$', fn)
    if m and m.group(2) and int(m.group(2)) > max(cnt.get(m.group(1), 0), 1):
        print('beyond chapters.js:', fn, '(listed', cnt.get(m.group(1)), ')')
print('html files:', sum(1 for f in os.listdir('abp_app_html') if f.endswith('.html')))
PY
# (g) the REAL pn_binding values for the --declared example — unchanged from §9.1 (g); run if not yet run
ls -l ~/bible-db/bible_pre_trapwire_swap.db
sqlite3 -header -separator $'\t' ~/bible-db/bible_pre_trapwire_swap.db "SELECT book, chapter, verse, name, entity_uniq, kind, rule, render, hot, tier FROM pn_binding WHERE name LIKE '%ichaiah%' ORDER BY book, chapter, verse" | tee ~/edition_g_michaiah_pre.tsv
sqlite3 -header -separator $'\t' ~/bible-db/bible.db "SELECT book, chapter, verse, name, entity_uniq, kind, rule, render, hot, tier FROM pn_binding WHERE name LIKE '%ichaiah%' ORDER BY book, chapter, verse" | tee ~/edition_g_michaiah_live.tsv
# (h) phrase-gloss member list on live (for the 702 -> 693 diff vs S11) — expected: 693 FLAGGED refs
python3 scripts/audit_phrase_gloss_underdist.py ~/bible-db/bible.db --dump-all > ~/edition_d_phrase_gloss_all.txt 2>&1; grep -c "" ~/edition_d_phrase_gloss_all.txt
# (i) the certification suite on live, read-only — expected per the LOCAL pin: a RED on check 1
#     ("51 active correction row(s), pinned 30") and 6/7 green; if it reads 7/7 the pin was moved on PA (say where)
python3 scripts/cert_invariants.py ~/bible-db/bible.db 2>&1 | tail -25
```
**RESULTS (JP ran 2026-10-30; recorded here, rulings in §0.7/§0.8):**
- **(a) 18 DIFF lines = exactly the 18 active `verses.text` correction verses**, nothing else. So live
  `verses.text` == the pinned feed through the parser for every verse EXCEPT the 18 corrected ones. That
  re-admits `abp_texts/` as the live stand-in for any verse not in that list (used for (c) below); the
  three `WARN stray bracket` lines are the known S9-(f) malformed-source verses (Mat 21:19, 1Ch 22:15,
  Job 24:18), loud by design.
- **(b) v2 on live — headline CUT by my `tail -40` again** (per-book tail + samples only). What is visible:
  the per-book hit list and **a `[word-order] Joh 14:26` sample (`comforter,` displaced)** — i.e. live v2
  word-order is NOT 0. The S11 certification left it at 0; the 10/25 rebuild is the only change since.
  Headline + member list = §9.5 (a). Not recorded as a count until read.
- **(c) the |delta| ≥ 5 tail = 40 verses, classified (12 read by hand, app vs the re-admitted feed):**
  · **28 = versification pairing, not edits**: Pro 16 ×5, Pro 24 ×11, Jer 10 ×7, Hab 3 ×5 — the census pairs
    by verse NUMBER and these chapters are the ruled no-renumber mismatches, so every pair compares two
    different verses (Pro 16:5 −45 etc.). Alignment failure by construction; the follow-up lane takes them
    through the audit's per-verse map, not by number.
  · **10 = verse-boundary moves (5 pairs, equal and opposite deltas)**: text moved across a verse break in
    the app edition — Gen 1:12/13 ("And God beheld that it was good" 13→12), Num 36:11/12 ("of the people of
    Manasseh … became wives" 12→11), 1Ki 15:5/6 ("except in the matter of Uriah the Hittite" 6→5),
    Eze 6:4/5 ("And I shall offer the corpses…" 4→5), 1Jn 5:7/8 ("And three are the ones witnessing upon
    the earth" 8→7). Real edition changes of the verse boundary; our verse keys stay (no renumber), so each
    pair is a two-verse unit in the follow-up lane.
  · **2 = real edits**: 1Sa 17:55 ("I do not know" → "I know not"; the +6 is compound sub-slot expansion on
    the app side, 31 app slots vs our 32 tokens) · 1Pe 3:12 (app ADDS "to utterly destroy them from the
    earth" and carries the inline footnote leak above; "the righteous" → "just ones").
  Verdict: no alignment failure outside the 28 known-versification chapters; the hand read found nothing
  unexplained. Members: `~/count_differs_tail.tsv` (PA).
- **(d) the 4 pages beyond `chapters.js` are `Genesis 52–55.html`.** Genesis has 50 chapters, so these
  cannot be real chapters; yet the fetch caches only a page whose own `<title>` matched its name, and the
  re-parse keyed their verses by the label inside the page and still landed on exactly 577,994 slots. So
  they are pages the site served with a matching title whose verse labels name an existing chapter (or
  empty pages). **Unknown until read — 0b WAITS (JP ruling: name them before 0b). §9.5 (b) reads their
  title, verse labels and size.** Whatever they are, the frozen TSV must not carry rows from them twice.
- **(g) real `pn_binding` values (both copies read):** the 3 Michaiah rows (book 12 = 2Ki 22:12, 14 = 2Ch 17:7,
  16 = Neh 12:41) changed TWO columns at the 10/25 swap — `kind` `ruled` → `fuzzy` AND `rule`
  `spelling-equiv` → blank; `entity_uniq`, `render`, `hot`, `tier` unchanged. The other 10 Michaiah rows
  were already `fuzzy`/blank on both sides. The charter prose "`ruled / spelling-equiv` → `fuzzy`" was two
  columns written as one. Draft example rebuilt on these (DRAFT_gate_declared.patch.md).
- **(h)** 2,521-line dump captured on PA (`~/edition_d_phrase_gloss_all.txt`); members read on request.
- **(i) `cert_invariants` on live: 6/7 green, check 4 RED — "51 active correction row(s), pinned 30".** Every
  row still HOLDS its corrected value (the per-row part passed; only the count pin failed). Logged as its own
  TODO line (live gate failure, JP ruling) — the fix is the pin in `cert_invariants.py`, re-pinned with the
  BD-* landing's receipt, not part of this lane.

### 9.5 PA block (read-only; cleared) — RUN 2026-10-30, results below the commands
```
cd ~/bible-db && git pull && git log --oneline -1
# (a) v2 headline + the word-order members — expected per S11: word-order 0 / content-other 0 / punct 260;
#     the Joh 14:26 sample says word-order >= 1 — read the list, don't force the 0
grep -nE "verses scanned|total hits|word-order|content-other|punct-position|dup-gloss" ~/edition_c2_reassembly_v2.log | head -12
python3 scripts/audit_reassembly_diff.py ~/bible-db/bible.db --v2 --list 2>&1 | grep -E "^\s*\[word-order|^\s*\[content-other" | tee ~/edition_c2_word_order.txt
# (b) what the 4 Genesis 52-55 pages ARE — expected: title, first/last verse label, byte size, verse-row count per file
for n in 52 53 54 55; do f="abp_app_html/Genesis $n.html"; echo "== $f  $(stat -c %s "$f") bytes  tables: $(grep -o '<table class="tbl">' "$f" | wc -l)"; grep -o '<title>[^<]*' "$f"; grep -o 'class="verse"[^>]*>[^<]*' "$f" | sed -n '1p;$p'; done
```
**RESULTS:**
- **(a) v2 on live: 31,237 scanned · total hits 242 · dup-gloss 0 · content-other 0 · word-order 1 ·
  punct-position 241.** The one word-order member: **Joh 14:26 — `comforter,` sits on the wrong slot**
  (rows vs prose). S11 certified word-order 0; the 10/25 rebuild is the only change since → **live defect
  until the pre-swap copy says otherwise (JP ruling); own TODO line; §9.6 (a) reads the pre-swap copy.**
  Punct 241 vs the S9 pre-registered 260 / observed 240 = the recorded open tension (§4.3), one more than
  S9 observed — not a gate figure, recorded.
- **(b) `Genesis 52–55.html` are STALE CACHE FILES, not chapters:** their own titles read Genesis 25, 35, 45
  and 5 (34 / 29 / 28 / 32 verse tables; the site's spell-correction of a bad chapter number). The fetch
  would never have cached them with today's title check, so they date from the 2026-10-24 13-chapter TEST
  fetch, before that check existed; the production fetch never requests chapter 52+ (the probe stops at
  51's 301), so they were never cleaned. Effect on the 10/24 TSV: none (the fetch only parses planned +
  probe pages). Effect on the italic re-parse: it read all four, keyed their verses by the label inside the
  page, so they overwrote Gen 25/35/45/5 with identical rows — the 577,994 total is exact, but the TSV
  was produced from a cache with 4 stale files in it. **Pre-registered fix before 0b (§9.6 (b)):** move the
  4 files out of the cache (JP's step; a cache file, no database), re-run the italic re-parse on 1,189 pages
  → the new TSV must be BYTE-IDENTICAL to the current one (sha256 both). The script now STOPS on any cached
  page whose title is not its file name (self-check 4, added 2026-10-30). Then 0b.

### 9.6 Next PA block (read-only toward every database; one cache-file move, JP's step) — after `git pull`
```
cd ~/bible-db && git pull && git log --oneline -1
# (a) the Joh 14:26 word-order hit on the PRE-SWAP copy (10/25 rollback of record) — expected: if the 10/25
#     rebuild introduced it, the copy reads word-order 0 and no Joh 14:26 line; if the copy has it too, it predates 10/25
python3 scripts/audit_reassembly_diff.py ~/bible-db/bible_pre_trapwire_swap.db --v2 2>&1 | grep -nE "verses scanned|total hits|word-order|content-other|punct-position|dup-gloss" | head -8
python3 scripts/audit_reassembly_diff.py ~/bible-db/bible_pre_trapwire_swap.db --v2 --list 2>&1 | grep -E "^\s*\[word-order" ; echo "(end word-order list, pre-swap)"
python3 scripts/audit_reassembly_diff.py ~/bible-db/bible.db --verse "Joh 14:26" 2>&1 | tail -20
# (a2) the live punct-position MEMBER list — the first frozen member file this class gets (§4.3) — expected: 241 lines
python3 scripts/audit_reassembly_diff.py ~/bible-db/bible.db --v2 --list 2>&1 | grep -E "^\s*\[punct-position" > ~/punct_members_live_20261030.txt; wc -l ~/punct_members_live_20261030.txt
# (b) stale-page cleanup, then the re-parse again — JP's step (cache files only, no database):
mkdir -p ~/abp_app_html_stale && for n in 52 53 54 55; do mv -v "abp_app_html/Genesis $n.html" ~/abp_app_html_stale/; done; ls abp_app_html/*.html | wc -l     # expected 1189
sha256sum abp_app_html/abp_app_slots_italic.tsv; mv -v abp_app_html/abp_app_slots_italic.tsv ~/abp_app_slots_italic_run1.tsv
python3 scripts/reparse_abp_app_italic.py 2>&1 | tail -12          # expected: 1,189 pages · 577,994 · SELF-CHECK PASS · 38,004 italic
sha256sum abp_app_html/abp_app_slots_italic.tsv ~/abp_app_slots_italic_run1.tsv   # expected: IDENTICAL hashes
```
If (b)'s two hashes match, 0b's step (1) may run next (the `sha256sum … > .sha256` line, §6) — still SHOW the
output before step (2), which is the manifest code change.
**RESULTS (JP ran 2026-10-30 03:35):**
- **(a) the pre-swap copy (`bible_pre_trapwire_swap.db`, 10/25 13:40) reads the SAME: word-order 1 (Joh 14:26),
  content-other 0, punct 241, total 242.** So the 10/25 rebuild did NOT introduce the hit; it predates the
  swap. S11 certified word-order 0 on 2026-07-06, so it entered between 7/06 and 10/25 (the 7/16 head-word
  rebuild, the 8/5 lane-② ride, the 8/8 ride, the 9/6 header landing are the rebuilds in that window — not
  read here). The verse read: rows carry `the comforter, spirit holy,` where the prose reads `the comforter,
  the holy spirit,` — an adjective/noun pair stored in Greek order with no bracket digits to reorder it, the
  comma riding on the flipped word. **JP ruling: fixed in the upgrade rebuild as a DECLARED ROW (Joh 14:26,
  the πνεῦμα/ἅγιον pair), never a live patch.** Pre-registered in §4.10 below.
- **(a2) 241 punct members dumped** on PA; same 241 on the pre-swap copy (the count line). Frozen per §4.3.
- **(b) stale files moved to `~/abp_app_html_stale/` (kept, not deleted — ruling); cache = 1,189 pages. Re-parse
  on the clean cache: 1,189 pages · 577,994 slots · 0 anomalies · 4 controls PASS · 38,004 italic (6.58%) ·
  SELF-CHECK PASS. sha256 of the re-parse output = sha256 of the first run =
  `7bd77385a80de3c3a762b9427658dfec4163d4882f5a3ea56be10ff61436cf63` — IDENTICAL, as pre-registered.**
  → 0b step (1) is unblocked (§9.7 (a)). **That hash is the pinned app-feed hash of this charter** (§2 "Pinned
  hash"), to be confirmed by the `.sha256` file and the manifest entry.

### 9.7 Next PA block — 0b step (1) + the punct member file. Read-only toward every database.
```
cd ~/bible-db && git pull && git log --oneline -1
# (a) 0b step (1): write the feed's .sha256 beside it, then prove it — expected: the 7bd77385… hash, "OK"
sha256sum abp_app_html/abp_app_slots_italic.tsv > abp_app_html/abp_app_slots_italic.tsv.sha256 && cat abp_app_html/abp_app_slots_italic.tsv.sha256 && (cd abp_app_html && sha256sum -c abp_app_slots_italic.tsv.sha256)
ls -l abp_app_html/abp_app_slots_italic.tsv abp_app_html/abp_app_slots_italic.tsv.sha256 ~/abp_app_slots_italic_run1.tsv
# (b) the punct member file + a sha for it (PA side); the local checkout gets a copy by scp (read-only touchpoint) and commits it
sha256sum ~/punct_members_live_20261030.txt; head -3 ~/punct_members_live_20261030.txt
```
After (a)'s output is shown: 0b step (2) = the `cert_manifest.py` code change (own small commit, CC writes it,
JP pulls), then step (3) `cert_manifest.py build` on PA (expected 75 → 76 files, 75 hashes unchanged), step (4)
the hash pinned in §2. The feed TSV + `.sha256` also get a second copy in the local checkout (scp, read-only).
**RESULTS (JP ran 2026-10-31 03:41):**
- **(a) `.sha256` WRITTEN: `7bd77385…  abp_app_html/abp_app_slots_italic.tsv` (104 bytes).** The `sha256sum -c`
  line then FAILED to open the file — my block's fault, not the file's: it `cd`'d into `abp_app_html/` and
  the hash file names the path WITH that folder prefix, so the check looked for `abp_app_html/abp_app_html/…`.
  The check belongs at the repo root (§9.8 (a)); expected `OK`. Sizes: run-1 copy and the frozen TSV both
  25,526,878 bytes.
- **(b) punct member file: 241 lines, sha256 `2b0f4cc43efc6dd423d934d4633727f69fcb6f45f894727b3a634265b68a941f`**
  (`~/punct_members_live_20261030.txt`, PA). Comes down by scp and is committed as
  `tests/fixtures/reassembly/punct_members_live_20261030.txt` (+ `.sha256`) — §9.8 (c).
- **0b step (2) DONE as its own commit: `6d60a466`** — `scripts/cert_manifest.py` lists
  `abp_app_html/abp_app_slots_italic.tsv` as a REQUIRED feed (missing = hard error, "copy it back from its
  second copy, never re-fetch"), floor 74 → 75; docstring bullet added. Diff shown to JP before the pull.
  **READ BEFORE PULLING:** `verify` compares the feed list on disk against `cert_manifest.json`; from the pull
  until `build` re-pins, verify prints `EXTRA abp_app_html/abp_app_slots_italic.tsv (on disk, not pinned)` and
  exits 1, which makes `cert_invariants` check 5 RED. So pull and build in the SAME sitting (§9.8), and
  the rewritten `cert_manifest.json` must come back to git (PA is pull-only: scp the json down, CC commits it).

### 9.8 Next PA block — 0b steps (1-check) and (3). `build` rewrites ONE file: `cert_manifest.json` (a text pin, not a database).
```
cd ~/bible-db && git pull && git log --oneline -1
# (a) prove the .sha256 from the repo root — expected: "abp_app_html/abp_app_slots_italic.tsv: OK"
sha256sum -c abp_app_html/abp_app_slots_italic.tsv.sha256
# (b) 0b step (3): re-pin the manifest. BEFORE: keep the old json; expected build output: 76 files pinned.
cp cert_manifest.json ~/cert_manifest_75.json && python3 scripts/cert_manifest.py build 2>&1 | tail -8
# then prove: 75 old hashes unchanged, exactly one new entry, and verify green
python3 - <<'PY'
import json
old = json.load(open('/home/appssanding720/cert_manifest_75.json'))['files']
new = json.load(open('cert_manifest.json'))['files']
same = sum(1 for k in old if k in new and old[k]['sha256'] == new[k]['sha256'])
print('old entries', len(old), '· new entries', len(new), '· old hashes unchanged', same,
      '· changed', [k for k in old if k in new and old[k]['sha256'] != new[k]['sha256']],
      '· dropped', [k for k in old if k not in new], '· added', [k for k in new if k not in old])
print('app feed sha256 in manifest:', new.get('abp_app_html/abp_app_slots_italic.tsv', {}).get('sha256'))
PY
python3 scripts/cert_manifest.py verify 2>&1 | tail -3
python3 scripts/cert_invariants.py ~/bible-db/bible.db 2>&1 | tail -12      # expected: still 6/7 — check 4 (the 30→51 pin, own TODO) red, check 5 GREEN
# (c) bring three files to the local checkout (JP, from the LOCAL machine; read-only toward PA):
#   scp PA:~/bible-db/cert_manifest.json  ./cert_manifest.json            -> CC commits (the 76-file pin)
#   scp PA:~/bible-db/abp_app_html/abp_app_slots_italic.tsv{,.sha256} ./abp_app_html/   (second copy; gitignored)
#   scp PA:~/punct_members_live_20261030.txt ./tests/fixtures/reassembly/  -> CC adds .sha256 + commits
```
Expected picture for (b): `old entries 75 · new entries 76 · old hashes unchanged 75 · changed [] · dropped []
· added ['abp_app_html/abp_app_slots_italic.tsv']`, the manifest sha = `7bd77385…`, verify `Baseline intact: 76
files`. Any other picture = stop and read; `cp ~/cert_manifest_75.json cert_manifest.json` puts the old pin back.

**Cleared by JP 2026-10-30 (§0.7).** Order of what follows the output: (d) names the 4 pages → 0b may
proceed; (g) → the `--declared` draft is built on the real values with the four checkpoint rulings
(tight key = book + chapter + verse + name; gate pinned to run before step 9; declaration files committed
under `tests/fixtures/<lane>/`; three-case test lands with the change) — still NOT applied; (i) red →
its own TODO line (a live gate failure), not folded into this lane.
