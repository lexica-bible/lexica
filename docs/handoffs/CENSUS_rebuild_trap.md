# CENSUS — rebuild trap: a words rebuild loses the abp_surface fill (read-only)

2026-10-25. Lane: rebuild-trap fix (gates the English-line edition upgrade). **Census only** — no
script, no runnable PA command, no proposal. Every claim in §1–3 is cited to the repo file:line it
was read from (repo at `760a297e`). Anything the repo cannot show is in §5 as a PA read.
Background: the 2026-10-25 fill (`apply_abp_surface_fill.py`, 4,411 writes, abp_surface 391,130 →
395,003; record `CENSUS_abp_surface_fill.md`).

## Headline (what the code says)
1. **The words rebuild itself does NOT destroy the fill.** It copies the WHOLE database
   (abp_surface included) into `<db>.new` and then clears and refills only `words`. The fill rows
   survive in the copy — but they stay keyed to the OLD word positions.
2. **The destroying step is /rebuild-words step 9**: `build_abp_surface.py` runs `DROP TABLE` then
   `CREATE TABLE` then inserts its own rows. The two backfills that follow add only rows they can
   re-derive from the scrape; nothing re-derives the fill (its source is the ABP app dump + the
   Analytical Lexicon, which no builder reads).
3. **Word identity does not survive a rebuild.** `words.id` is regenerated; the only cross-rebuild
   key any table uses is `(verse_id, position)`, which is only as stable as the build's slot layout.
4. **Nothing would catch the loss.** The health-check floor (389,244) sits below the pre-fill
   count (391,130), so a rebuilt table without the fill passes it.

---
## 1. build_abp_surface.py

**Execution order** (the `--bh` path is the one /rebuild-words step 9 uses — `.claude/commands/rebuild-words.md:218`):

| # | Action | Table / source | Cite |
|---|---|---|---|
| 1 | opens the target db, plain connect (no `journal_mode`/`busy_timeout` set) | — | `scripts/build_abp_surface.py:164` |
| 2 | READ dictionary lemmas | `lexicon (strongs_g, lemma)` | `:175-178` |
| 3 | READ dotted lemmas, only if the table exists | `dotted_lexicon (strongs, lemma)` | `:179-181` |
| 4 | READ every ABP word, verse by verse, in position order | `verses ⨝ words` (id, book, ch, vs, position, strongs_base, strongs) | `:135-151`, called `:183` |
| 5 | READ the scrape's Greek per verse | `bh_scrape.db bh_words (strongs, greek)` ordered by position | `:122-132`, `:192` |
| 6 | (dry run stops here, writes nothing) | — | `:292-295` |
| 7 | **DROP** | `abp_surface` | `:297` |
| 8 | **CREATE** `abp_surface(verse_id, position, form, translit, PRIMARY KEY(verse_id, position))` | `abp_surface` | `:298-302` |
| 9 | INSERT OR REPLACE its rows; commit | `abp_surface` | `:303-304` |

It never writes words/verses (docstring `:10-12`, and no other write statement in the file).
No truncate/DELETE — it is DROP + CREATE (whole-table replace).

**What it keys on.** Rows are `(verse_id, position)` taken straight from the CURRENT `words` rows
(`:149`, `:226`). The form is chosen by aligning the verse's words to the scrape tokens by Strong's
number (`:195-203`), with every pronoun number folded to one bucket so ABP's raw G1473 matches the
corrected numbers (`_norm`, `:90-95`, applied `:200-201`). A pairing is kept only if the folded
numbers agree (`:214`). Slots with a blank or `'*'` number are skipped (`:209`) — that is why name
slots need their own backfill. A form identical to the dictionary lemma once marks are stripped is
not stored (`:223-225`).

**Translit.** On the `--bh` path every row is written with `translit = ''` (`:226`). (Only the
alternative Rahlfs/TAGNT path writes TAGNT's translit, `:264-268`; /rebuild-words does not use it.)
Translit is filled afterward by `build_abp_translit.py`:
- reads `abp_surface ⨝ words (verse_id, position) ⟕ lexicon (strongs_g = strongs_base)`,
  forms only (`scripts/build_abp_translit.py:85-91`);
- `UPDATE abp_surface SET translit=? WHERE verse_id=? AND position=?` (`:98`); romanizes the form,
  taking the rough-breathing 'h' from the lemma (docstring `:7-9`);
- plain connect, no `journal_mode`/`busy_timeout` set (`:83`).

**The two backfills that run after it** (/rebuild-words step 9, `rebuild-words.md:221-224`):
- `backfill_abp_surface.py` — requires the table (`:52`), reads existing keys (`:62`), re-reads
  verses⨝words + scrape the same way (`:68-75`), skips blank/'*'/H-numbered slots (`:84-85`),
  `INSERT OR IGNORE` new rows only (`:137`). Sets `journal_mode=DELETE` + `busy_timeout` (`:49-50`).
- `backfill_pn_surface.py` — requires the table (`:240`), reads existing keys (`:243`), reads
  every `words` row with `is_pn = 1` (`:260-266`) and the scrape's name/numbered/star rows
  (`:191-193`), `INSERT OR IGNORE` new rows only (`:339`). Sets the pragmas (`:238-239`).

**How the fill was keyed** (`scripts/apply_abp_surface_fill.py`): the approved CSV carries
`book, chapter, verse, position`; verse → `verse_id` through the `verses` table (`:188-193`).
538 UPDATEs, each only where the stored form still equals the CSV's old form (`:239-242`); 3,873
INSERTs into empty slots (`:245-246`). Translit computed in the same write from the lemma at the
slot (`:92-100`, `:230-236`). Its preflight refuses unless abp_surface has exactly 391,130 rows
(`:50`, `:109-110`) — so as written it **cannot re-land on any other table state** (one-shot).
Its rollback is DELETE + INSERT from the pre-fill copy (`:342-344`). Its inputs default to PA files
outside git: `~/abp_app_dump.tsv`, `~/abp_surface_fill_dryrun.{txt,csv}`,
`abp_helps/analytical_lexicon.tsv`, `abp_app_html/missing_printed_forms.tsv` (`:366-370`); the
rollback copy is `~/bible.db.pre-surface-fill-20261025` (`:48`).

---
## 2. The words rebuild path

Script: `scripts/build_words_from_abp.py`, function `run()` (`:2023`), entered from `main()`
(`:2308`, call `:2334`). Procedure: `/rebuild-words` step 2 (`rebuild-words.md:54`), tail
`scripts/finish_rebuild.sh` (step 3, `:90`), then steps 8b, 9, 10, 11.
(`scripts/build_words_from_bh.py` has the same snapshot-then-`DELETE FROM words` shape, `:283`,
`:319`, but is not the checklist's path.)

**build_words_from_abp.run(), in order:**

| # | Action | Table | Cite |
|---|---|---|---|
| 1 | READ scrape column check + count | `bh_scrape.db bh_words` | `:2026`, `:2032` |
| 2 | target = `<db>.new`; delete any old `.new` and its sidecars | file | `:2035`, `:2051-2053` |
| 3 | **copy the whole live db into `.new`** (SQLite backup — every table and index, abp_surface included) | all | `:2054-2061` |
| 4 | ALTER `words` ADD COLUMN italic_words/smcap_words/morph/lemma if missing | `words` | `:2063-2067` |
| 5 | READ verse map (never written by the build) | `verses` | `:2069-2071` |
| 6 | READ lexicon | `lexicon` | `load_lexicon` `:369-373` |
| 7 | READ scrape index | `bh_words` | `load_bh_verse_index` `:334-340` |
| 8 | **`DELETE FROM words`**; commit | `words` | `:2110-2112` |
| 9 | INSERT every word: columns `verse_id, position, english, english_head, strongs, strongs_base, greek_pos, bracket_id, italic, italic_words, smcap_words, morph, lemma` — **no `id`, no `is_pn`, no `english_head_norm`** | `words` | `:2153-2157` |
| 10 | blank-"G." fill (splits 4 slots → later positions shift) | `words` | `:2171` |
| 11 | PN subject-name split (splits slots → positions shift) | `words` | `:2181` |
| 12 | italic-head re-clean | `words` | `:2194` |

**What destroys the fill.** Not this script: it touches only `words` after the copy (rows 8–12),
so the copy still holds all 395,003 abp_surface rows, keyed to the PRE-rebuild positions. Any slot
the new build places at a different position now carries a fill form on the wrong word (or on a
position with no word). The fill is **dropped** at /rebuild-words step 9 —
`build_abp_surface.py:297` **DROP TABLE**, then **CREATE-replace** (`:298-302`) and the builder's
own rows (`:303`). It is a table drop-and-recreate, not a row DELETE, not a foreign-key cascade
(no `REFERENCES` to words exists in the repo schema and no `PRAGMA foreign_keys` is set anywhere
in the repo), and not a rowid issue (abp_surface carries no word id).

**Does word identity survive?** No.
- Repo schema: `words.id INTEGER PRIMARY KEY` (no AUTOINCREMENT) — `scripts/parse_abp.py:293-295`.
  PA confirms the same: plain `INTEGER PRIMARY KEY`, no `sqlite_sequence` table (§5 results, Q1).
- The build empties the table (`:2111`) and inserts without an `id` (`:2154-2156`), so SQLite
  hands out new ids. With this schema the numbering restarts at 1.
- Every use of `words.rowid`/`id` found in the repo is within one run (import_tipnr
  `:382`/`:719`; restore_frozen_pn `:82`/`:113`; retire_hebrew_identity `:191`/`:295`;
  apply_abp_corrections `:107`/`:122`). No table stores a word id. One exception that would break:
  `ship_g707_targeted.py:153` joins a copy to live by `rowid` — only valid on a byte copy, never on a
  rebuilt one.
- The cross-rebuild key everywhere is `(verse_id, position)` (or book/ch/vs/position). `verse_id`
  is stable (the build reads `verses`, never writes it — `:2069-2071`). `position` is whatever the
  build emits, and steps 10–11 above plus the tail (below) move positions.

**finish_rebuild.sh (step 3), in order** — all on the copy, each a targeted write to `words`
unless noted:
`import_tipnr.py` (restores `is_pn`, writes `strongs_base, is_pn` by rowid — `:33`;
`import_tipnr.py:719`) → `fix_subject_reorder` / `fix_mat25_37` / `fix_supplied_attach` (the last
two move positions — `fix_mat25_37.py:65-69`, `fix_supplied_attach.py:72-74`) →
`fix_theos_filler_tags` → `fix_split_merges` → `fix_kyrios_mistags` → `fix_merge_misses` →
`fix_idios_own` → `dedup_words` (DELETE by id, `dedup_words.py:56`) → `fix_bracket_punct` →
`apply_abp_corrections --only verses` (writes `verses.text`, `:66`) → `fix_emdash` (words.english +
verses.text, `:73`) → `fix_split_flip` (swaps positions, `:86`; `fix_split_flip.py:99-103`) →
`apply_abp_corrections --only words` (position-keyed, guarded by recorded before-value, `:95`).
`finish_rebuild.sh` lines `:37-96`. None of these touch abp_surface.

**Steps 8b → 11** (`rebuild-words.md:154-242`):
- 8b.0 `correct_xref_vs_binding.py --rebuild-step` — UPDATEs `pn_hebrew_xref`, `pn_greek_identity`,
  `words.strongs_base` keyed by verse+position (`correct_xref_vs_binding.py:250-259`).
- 8b.1 `restore_frozen_pn.py` — reads `pn_greek_identity ⟕ words ON (verse_id, position)`
  (`restore_frozen_pn.py:80-86`), UPDATEs `words.strongs_base` by rowid (`:113`).
- 8b.2 `retire_hebrew_identity.py --fresh-rebuild` — reads `pn_greek_identity ⟕ words ON
  (verse_id, position)` (`:189-195`), **DROP** `pn_hebrew_xref` (`:289`), CREATE (`:100-113`,
  run `:292`), INSERT (`:293`), UPDATE `words.strongs_base` (`:295`).
- 8b.3 `build_pn_greek_identity.py --apply` — **reads abp_surface** joined on `(verse_id,
  position)` (`build_pn_greek_identity.py:292-305`) and uses its forms as the name-header inventory
  (`:363`, `:374-378`); **DROP** + CREATE `pn_greek_identity` (`:536-547`), indexes (`:550-551`).
  Then `build_entity_binding.py --apply` — **DROP** `pn_binding`, `tipnr_entity_refs`,
  `tipnr_entities` (`build_entity_binding.py:464-466`), recreate; re-lands slot binds through
  `build_slot_binding.land` (`:509-511`), which **DROP**s + CREATEs `pn_slot_binding`
  (`build_slot_binding.py:147-152`) after a stale-name check per row (`:90`).
- 9 surface: §1 above. 10 two-ending (output pasted into the frontend). 11 `build_rendering_norm.py`
  — ALTER ADD `english_head_norm` if missing + UPDATE words + index (`build_rendering_norm.py:70-75`).

**Order fact that matters here:** 8b.3 reads abp_surface BEFORE step 9 rebuilds it. On a rebuild
copy, the header build therefore reads the snapshot's surface table (fill included) matched to the
NEW positions. (Precedent of the same shape: "The 8/8 wordpos apply re-ran the header build BEFORE
rebuilding the form table" — `docs/handoffs/HANDOFF_form_lane.md:25`.)

**Where step 9 runs is stated three different ways:** the checklist puts swap+deploy at step 8
(`rebuild-words.md:151-153`) before 9, and step 9's translit command names `bible.db` (`:229-230`);
the build's own closing text says run the surface builder against the COPY before the swap
(`build_words_from_abp.py:2224-2226`, swap `:2231-2233`); `finish_rebuild.sh:112-113` says re-run it
"after a real swap". So whether the fill is dropped on the copy or on the live file is not settled
by the docs. (Precisely: finish_rebuild says live-after-swap, the build text says copy, the
checklist named no file. **Settled 2026-10-26: live, after the swap** — `CHARTER_rebuild_trap_fix.md` §1. **Re-settled the
same day: on the copy, before the swap** — §9; step 9 has no live-only input.)

---
## 3. Other tables and indexes that depend on words

Checked each. "Position-keyed" = would point at the wrong word if a slot moves.

| Table / item | Key | Written by (rebuild step) | Left stale/orphaned by a rebuild? | Cite |
|---|---|---|---|---|
| `abp_surface` | verse_id, position | build_abp_surface + 2 backfills + translit (9) | **Yes until step 9; then rebuilt WITHOUT the fill** | §1 |
| `pn_greek_identity` (the Greek name header per slot; also the frozen record 8b.1/8b.2 read) | verse_id, position | build_pn_greek_identity (8b.3); edited by correct_xref (8b.0) | Stale in the copy until 8b.3; 8b.1/8b.2 deliberately read the OLD one as their reference. 8b.3 builds from the not-yet-rebuilt abp_surface | `build_pn_greek_identity.py:536-547`, `:292-305`; `restore_frozen_pn.py:80-86` |
| `pn_hebrew_xref` | verse_id, position | retire_hebrew_identity --fresh-rebuild (8b.2) | Stale until 8b.2 (dropped + rebuilt) | `retire_hebrew_identity.py:289-295` |
| `pn_slot_binding` | book#, ch, vs, position | build_slot_binding via build_entity_binding (8b.3) | Rebuilt; a row whose printed name no longer sits at that position is refused, not mis-bound | `build_slot_binding.py:90`, `:147-152`; `build_entity_binding.py:509-511` |
| `pn_binding`, `tipnr_entities`, `tipnr_entity_refs` | book#, ch, vs, name (not position) | build_entity_binding (8b.3) | Rebuilt | `build_entity_binding.py:464-466` |
| `abp_corrections` (ledger) | book, ch, vs, position, field | hand-authored; applied in finish_rebuild | Not rebuilt — persists; each row fires only if the cell still holds its recorded before-value, else a loud skip | `build_abp_corrections.py:49-63`; `finish_rebuild.sh:88-96` |
| `words.is_pn` | column | import_tipnr (3) | Reset to 0 after the insert (not in the column list; PA definition `is_pn INTEGER DEFAULT 0`, §5 results) until import_tipnr | `build_words_from_abp.py:2154-2156`; `import_tipnr.py:719` |
| `words.english_head_norm` + `idx_words_ehnorm` | column | build_rendering_norm (11) | Blank after the insert until step 11 (column and index survive — table emptied, not dropped) | `build_words_from_abp.py:2154-2156`; `build_rendering_norm.py:33`, `:70-75` |
| words indexes (repo ones + any PA-only ones) | — | — | Survive: the build empties the table with DELETE, never drops it; the backup copies indexes | `build_words_from_abp.py:2058`, `:2111` |
| `dotted_lexicon` | Strong's number | build_dotted_lexicon | Not orphanable (not slot-keyed); reads word counts | `build_dotted_lexicon.py:99`, `:151-166`, `:220` |
| `word_gloss` | Strong's number | build_word_gloss | Not orphanable; reads distinct numbers | `build_word_gloss.py:382`, `:530` |
| `lexica_def` | Strong's number | build_lexica_def | Not slot-keyed (cites verses) | `build_lexica_def.py:3192` |
| `tipnr_metav_link`, metav staging | entity / person id | build_person_metav_link | No direct `words` read found in the builder (grep); data-model says re-run after a rebuild | `docs/claude/data-model.md:226-227` |
| two-ending lists | n/a (pasted into `00b-two-ending.jsx`) | build_two_ending (10) | Output can drift; not a table | `rebuild-words.md:235-238` |
| **"concordance"** | — | — | **No table exists.** The concordance diff is scripts + files (`diff_concordance_verses.py` reads no `words` table — grep 0) | — |
| **"greeks_slots"** | — | — | **No table or name by that spelling anywhere in the repo** (grep 0). The per-slot Greek tables are `pn_greek_identity` (name header) and `abp_surface` (printed form). Reviewer to confirm which was meant | — |
| **"xref"** | — | — | Two things carry the name: `pn_hebrew_xref` (above, position-keyed) and `cross_references` (TSK; keyed on KJV verse ids — no words dependency, `data-model.md:399-401`) | — |
| **name-slot forms** | — | — | Three homes: abp_surface PN rows (backfill_pn_surface, step 9); `pn_greek_identity.greek_lemma` (8b.3); the pinned allowlist `docs/tickets/compound_names_allowlist.tsv` that gate F4 checks against abp_surface byte-for-byte | `backfill_pn_surface.py:260-266`, `:339`; `gate_form_lane.py:17-18`, `:44-47` |

**Guards that do or don't see the fill:**
- health_check floors abp_surface at 389,244 (`health_check.py:138-140`). Pre-fill table was 391,130
  and with the fill 395,003, so a rebuilt table without the fill still passes. **Blind to the loss.**
- `ship_g707_targeted.py:176-178` uses a stale 389,409 floor (older figure; same blindness).
- `gate_greek_header.py` gate A requires abp_surface byte-identical live vs copy (`:57-64`); in the
  checklist it runs at 8b.3 (`rebuild-words.md:206-208`), before step 9, so at that point it compares
  the snapshot with itself.
- The serving join is `abp_surface ⟕ words ON (verse_id, position)`, only if the table exists
  (`views_library.py:278-283`): a stale table serves stale forms silently; a missing table serves
  none, silently.

**Out-of-lane flag (one line, not pursued):** `fix_lane3_star_merges.py:9-10` says it "joins the
post-rebuild repair chain", but it is not called in `finish_rebuild.sh` (`:33-96`) or
`/rebuild-words`. It writes english/greek_pos/bracket_id only, never positions, so it does not move
fill keys.

---
## 4. Dependency map (list only — no design)

**Must be carried across the rebuild (no builder can re-create it):**
- the fill's 4,411 writes — their per-row record (`~/abp_surface_fill_dryrun.csv`) and their sources
  (`~/abp_app_dump.tsv`, `abp_helps/analytical_lexicon.tsv`, `abp_app_html/missing_printed_forms.tsv`)
  or the live table's rows themselves, plus the pre-fill copy as the "what the builders made" baseline;
- `abp_corrections` (already persists; position-keyed);
- `pn_greek_identity` + `pn_hebrew_xref` as they are BEFORE 8b (8b.1/8b.2 read them as the reference);
- the repo TSVs the chain re-lands from: `pn_hand_rulings.tsv`, `pn_slot_rulings.tsv`,
  `greek_header_nominatives.tsv`, `split_merge_fixes.json`, `compound_names_allowlist.tsv`.

**Must be re-run after, in the checklist's current order:**
build → finish_rebuild (import_tipnr first) → 8b.0 correct_xref → 8b.1 restore_frozen_pn →
8b.2 retire_hebrew_identity → 8b.3 build_pn_greek_identity → build_entity_binding (+ slot binds) →
gates → 9 build_abp_surface → backfill_abp_surface → backfill_pn_surface → build_abp_translit →
10 two-ending → 11 build_rendering_norm (+ metav person link, word_gloss, dotted per the checklist).

**Ordering facts any fix has to respect (from §1–3):**
- the fill's slots must be re-matched to the NEW positions — its stored keys are pre-rebuild;
- the fill can only be placed after step 9's DROP and both backfills (it overwrites 538 builder rows
  and fills 3,873 empty slots — `apply_abp_surface_fill.py:239-246`);
- translit for re-landed rows needs the new slot's lemma (`apply_abp_surface_fill.py:92-100`);
- 8b.3 (name headers) reads abp_surface, so whether it sees the fill depends on where the fill lands
  relative to 8b.3;
- the health floor would need to know the fill exists to catch its absence;
- which file step 9 runs on (copy vs live) is unsettled (§2).

---
## 5. Open questions — PA reads

All reads; nothing below changes the database. Per the lane rule these are the SQL texts only, not
packaged commands. Run against `~/bible-db/bible.db` opened read-only.

**A. Table definitions on PA (the repo schema may differ)**
```sql
-- Q1 words: is id a plain INTEGER PRIMARY KEY or AUTOINCREMENT?
SELECT sql FROM sqlite_master WHERE type='table' AND name='words';
SELECT name FROM sqlite_master WHERE name='sqlite_sequence';
-- Q2 everything attached to the tables in this census: indexes, triggers (a trigger could cascade)
SELECT type, name, tbl_name, sql FROM sqlite_master
 WHERE tbl_name IN ('words','abp_surface','pn_greek_identity','pn_hebrew_xref','pn_slot_binding','verses')
 ORDER BY tbl_name, type, name;
-- Q3 any foreign-key clause anywhere
SELECT name FROM sqlite_master WHERE sql LIKE '%REFERENCES%';
```

**B. The fill as it stands on live**
```sql
-- Q4 table size (expect 395,003) and journal mode (expect delete)
SELECT count(*) FROM abp_surface;
PRAGMA journal_mode;
-- Q5 the fill = live minus the pre-fill copy: expect 4,411 live-not-in-copy, and 538
--    copy-not-in-live (the OLD values of the 538 updated rows). First draft said 0 — wrong.
ATTACH '/home/appssanding720/bible.db.pre-surface-fill-20261025' AS cp;
SELECT count(*) FROM (SELECT * FROM main.abp_surface EXCEPT SELECT * FROM cp.abp_surface);
SELECT count(*) FROM (SELECT * FROM cp.abp_surface EXCEPT SELECT * FROM main.abp_surface);
-- Q6 how many fill rows sit on name slots (the PN split moves those). Covers only the
--    3,873 NEW slots — the 538 updated slots exist on both sides and drop out of this EXCEPT.
SELECT w.is_pn, count(*) FROM (SELECT verse_id, position FROM main.abp_surface
        EXCEPT SELECT verse_id, position FROM cp.abp_surface) f
  JOIN words w ON w.verse_id=f.verse_id AND w.position=f.position GROUP BY w.is_pn;
```
(Q5/Q6 need the pre-fill copy still on disk — its retention also needs confirming.)

**C. Baseline: nothing orphaned on live today** (each expect 0; a rebuild copy would be measured the same way)
```sql
SELECT 'abp_surface', count(*) FROM abp_surface s LEFT JOIN words w
  ON w.verse_id=s.verse_id AND w.position=s.position WHERE w.verse_id IS NULL
UNION ALL SELECT 'pn_greek_identity', count(*) FROM pn_greek_identity g LEFT JOIN words w
  ON w.verse_id=g.verse_id AND w.position=g.position WHERE w.verse_id IS NULL
UNION ALL SELECT 'pn_hebrew_xref', count(*) FROM pn_hebrew_xref x LEFT JOIN words w
  ON w.verse_id=x.verse_id AND w.position=x.position WHERE w.verse_id IS NULL;
```

**D. Does the name-header table already lean on fill forms?**
```sql
-- Q7 header values that equal a fill form at the same slot (fill rows from Q5's EXCEPT)
ATTACH '/home/appssanding720/bible.db.pre-surface-fill-20261025' AS cp;
SELECT count(*) FROM pn_greek_identity g JOIN
  (SELECT * FROM main.abp_surface EXCEPT SELECT * FROM cp.abp_surface) f
  ON f.verse_id=g.verse_id AND f.position=g.position WHERE g.greek_lemma = f.form;
```

**E. Files the fill depends on** (a directory listing, nothing opened for writing)
`~/abp_surface_fill_dryrun.csv`, `~/abp_surface_fill_dryrun.txt`, `~/abp_app_dump.tsv`,
`~/bible-db/abp_helps/analytical_lexicon.tsv`, `~/bible-db/abp_app_html/missing_printed_forms.tsv`,
`~/bible.db.pre-surface-fill-20261025` — present? sizes? dates?

### Results — JP ran all of the above on PA, 2026-10-26 (PA clock 05:53–05:55), read-only
(the SQL above, wrapped in `sqlite3 -readonly` blocks). Expected beside actual:

| Q | Expected | Actual | Reading |
|---|---|---|---|
| Q1 | plain `INTEGER PRIMARY KEY`? | `id INTEGER PRIMARY KEY`, no AUTOINCREMENT; no `sqlite_sequence` table | After the build's DELETE, new ids start at 1. `is_pn INTEGER DEFAULT 0`; `english_head_norm TEXT` (no default) |
| Q2 | any triggers / PA-only indexes? | **No triggers** on any of the 6 tables. words: the 5 repo indexes + `idx_words_ehnorm`; abp_surface: its key index only; pn tables: key index + the builders' own indexes | Nothing on these tables beyond what the repo creates |
| Q3 | anything referencing words? | REFERENCES in `words` (→ verses), `cross_references`, `metav_place_aliases`, `metav_people_aliases`, `metav_people_groups`, `metav_people_relationships`; `idx_xref_verse`/`idx_xref_ref` match only because their text names `cross_references` | **Nothing references `words` or `abp_surface`** — no cascade path |
| Q4 | 395,003 · delete | 395,003 · delete | match |
| C | 0 · 0 · 0 | 0 · 0 · 0 | No orphans on live today |
| Q5 | 4,411 · 538 | 4,411 · 538 | match (fill fully present) |
| Q6 | split of the 3,873 inserts | is_pn 0: 3,852 · is_pn 1: **21** (sum 3,873 = insert count) | 21 fill inserts sit on name slots. Which fill class they are: not checked |
| Q7 | 0? | **2** | 2 name-header values equal a fill form at the same slot. These reads don't show whether the header build ran after the fill or the values just match. Either way: on a rebuild copy, 8b.3 reads abp_surface, so fill forms would feed headers from then on |
| E | all present | all 6 present: `abp_app_dump.tsv` 41,027,879 (10/25 02:08) · `abp_surface_fill_dryrun.csv` 749,793 (02:53) · `.txt` 3,147 (02:53) · `missing_printed_forms.tsv` 317,567 (01:16) · `analytical_lexicon.tsv` 4,319,554 (02:51) · `bible.db.pre-surface-fill-20261025` 442,687,488 (03:09) | The pre-fill copy is the only record of the table as the builders left it — load-bearing for any fix; keep |

**Not answerable by a read of live** (needs a built copy, so out of this census): how many
positions a fresh build moves relative to live, and therefore how many of the 4,411 fill keys would
land on a different word. `compare_words.py` against a built copy is where that number comes from
(`rebuild-words.md:134-139`).
