# DRAFT — `/rebuild-words` step 12: the three side-table builders (for the ruling chat, before stage E)

Status: **DRAFT, not in the procedure.** JP ruled 2026-11-07 that `/rebuild-words` should include the three
builders the docs say get re-run after a rebuild. This is the drafted step — which builders, where in the
order, what each reads and writes — for review before stage E. Nothing here has run. All facts below were
read from the scripts at `a57c6317`.

## Why a step is needed
The build copies the whole db (`rebuild-words.md` step 9 note), so all three tables arrive on `<built>` as
**live's old copies**. They never go missing — they go **stale**: each is keyed off what the build changes.

| Table (builder) | Keyed off | What a stale copy does |
|---|---|---|
| `dotted_lexicon` (`build_dotted_lexicon.py`) | the dotted numbers present in `words.strongs` | a NEW dotted number has no row → its card headword falls back to the BASE number's word, and `build_lexica_def.py` (excludes dotted rows via this table) lets its rows into the base word's evidence |
| `word_gloss` (`build_word_gloss.py`) | `words.strongs_base` (G set) + `dotted_lexicon` | new numbers get no header gloss; dotted glosses keyed to old lemmas |
| `tipnr_metav_link` person rows (`build_person_metav_link.py`) | `tipnr_entities` / `tipnr_entity_refs` (re-imported by import_tipnr) + `pn_binding` render counts (rebuilt at 8b.3) | links/ranks reflect the pre-rebuild entities and bindings |

## Where in the order
`... 8b.3 → 11 → 10 → **12a → 12b → 12c** → 9 → 9a → 9b → 4–7 → 8 swap`
- **After 8b.3:** 8b.2 rewrites `strongs_base` (12b reads it) and 8b.3 rebuilds `pn_binding` (12c reads it).
- **Before step 9:** step 9's own builders READ `dotted_lexicon` (`build_abp_surface.py:179`,
  `backfill_abp_surface.py:59`) — a stale table would feed step 9 too. So 12a must land first.
- 12a before 12b: `build_word_gloss.py` reads `dotted_lexicon` (`:388-389`; its own header says "run
  build_dotted_lexicon first").
- 12c has no tie to 12a/12b; it sits last so the three run as one block.
- Same-code rebuild expectation: **all three unchanged vs live** (12a `--diff` = `+0 / -0`; 12b and 12c
  row-for-row equal). Edition upgrade: changes are DECLARED members, read before `--apply`.

## The step (as it would read in `rebuild-words.md`)
12a. **`dotted_lexicon` — on `<built>`.** ⚠ **BLOCKER: the script has NO path argument** — `DB` is hard-wired
   to `~/bible-db/bible.db` (`build_dotted_lexicon.py:28`), i.e. **LIVE**. Today the step CANNOT be run on the
   copy. Needs a code change first (checkpoint): take `<db>` as the first argument and refuse to run with none
   (the `build_two_ending.py` trap, inverted). Also: `add_hebrews13.py:383` already PRINTS
   `build_dotted_lexicon.py {bible_db}` — that path is silently ignored today and the run hits live; fix the
   print in the same change. After the fix:
   `python3 scripts/build_dotted_lexicon.py <built> --diff` (read-only: keys added/removed vs the copied
   table — compares keys only, not lemma values) → verdict → `--apply` (drops + refills that table only).
   Reads `words`, `lexicon`, `abp_ext` (all on the copy) + code-pinned overrides (`NUMERAL_` /
   `PHRASE_` / `HAND_OVERRIDES`).
12b. **`word_gloss` — on `<built>`.** `python3 scripts/build_word_gloss.py <built>` (dry run: coverage +
   residue) → verdict → `--apply` (drops + refills that table only). Path IS the first non-flag argument
   (`:34`). Reads on the copy: `words.strongs_base`, `dotted_lexicon`, `abp_ext`, `lexicon`; reads
   `~/bible-db/heb.db` read-only (`--heb` to override; heb.db is not rebuilt); reads Dodson from the repo
   (`scripts/apfathers/raw/dodson.csv`, pinned in git). ⚠ **SOURCE NOT PINNED:** TBESG + TBESH are fetched
   at run time from STEPBible's GitHub **master** (`:38-41`, `_read_source` `:152-158`) — an upstream edit
   since 2026-06-22 would silently change glosses on a "same-code" rebuild. Pin first (vendor the two files
   under `scripts/` or a fixture path and pass `--tbesg` / `--tbesh`), or at minimum record the fetched
   files' sha256 in the run log. Also writes `gloss_dotted_blank.tsv` / `gloss_dotted_abp.tsv` into the
   current folder whenever they have rows (`gloss_byform_audit.tsv` only with `--byform-audit`) — run from
   a scratch dir or accept the files. There is no `--diff` mode: the before/after
   check is a read-only compare of `<built>`'s new table vs live's (to draft with the step).
12c. **`tipnr_metav_link` person rows — on `<built>`.**
   `python3 scripts/build_person_metav_link.py --bible <built>` (dry run: opens `<built>` read-only, prints
   bucket counts + traffic coverage, writes the residual/tier-2 files into `scripts/`) → verdict →
   `--apply` (deletes + rewrites ONLY `kind='person'` rows; place rows left alone). Reads `tipnr_entities`,
   `tipnr_entity_refs`, `metav_people`, `pn_binding (render=1)` on the copy + the staging
   `~/bible-db/metav_index.db` read-only (`--index`). metav_index.db is built from the MetaV CSVs only
   (`build_metav_person_index.py`) — independent of the words table, so it is NOT rebuilt here; it must
   exist. Note: the dry run rewrites `scripts/person_metav_link_residual.txt` / `person_metav_link_tier2.txt`
   — the two untracked PA files the edition-lane standing rules say to leave alone. Point them at a scratch
   path (code change) or accept the overwrite — a ruling.

## Rulings 2026-11-07 (ruling chat, relayed by JP)
- **Placement accepted in principle:** after 8b.3 and steps 11/10, before step 9.
- **Blocker 1 → scripts change before stage E:** `build_dotted_lexicon.py` takes a db path and opens only
  that path, with a test proving it never touches live when given a copy; `add_hebrews13.py`'s printed
  command is a live-write hazard and gets fixed in the same commit.
- **Blocker 2:** pin the two STEPBible gloss files in the repo as fixtures with sha256; `build_word_gloss.py`
  reads the pinned copies (download only as an explicit flag).
- **Blocker 3:** 12c runs with its two leftover-list files copied aside and restored after, same as the
  binder dumps in 8B3 — the untracked files stay untouched.
- **Timing:** none of this goes into the procedure until the gate 2 work is done — "before stage E", not now.
  (CC note: the scripts changes also wait — the lane's gate wrapper requires `scripts tests` unchanged since
  its REF commit, so landing them mid-gate-2 would trip it.)
- Questions 1–3 below are answered by the blocker rulings above.
- **Q4 (ruled 11/7): no 12d.** Place-link rows (`kind='place'`) stay as copied. 12c gains a READ-ONLY
  orphan check: every `kind='place'` entity id in `tipnr_metav_link` resolves to a `tipnr_entities` row on
  `<built>`; **expect 0 orphans — any other count = STOP.** Drafted check (not run; `<built>` = the built
  copy's full path):
  `sqlite3 -readonly <built> "SELECT COUNT(*) FROM tipnr_metav_link l LEFT JOIN tipnr_entities e ON e.uniq = l.uniq WHERE l.kind='place' AND e.uniq IS NULL;"`
  (columns from `build_person_metav_link.py:100,112,286-293`; the place rows' `metav_id` side is not part
  of this check.)
- **Q5 (ruled 11/7): yes.** Each of 12a/12b/12c runs dry/trial on `<built>` first; the expected figures are
  DECLARED from that log by path:line; the `--apply` is then gated on those declared figures — the same
  pattern 8b.3 used.
- **Sequencing (ruled 11/7):** the scripts changes (blockers 1–3) land as ONE commit, after gate 2, before
  stage E; the step goes into `/rebuild-words` only then.

## Open questions for the ruling chat
1. 12a code change (path argument + refuse-without-path + the `add_hebrews13.py` print) — OK to make, as
   its own commit with a local test, before stage E?
2. 12b source pinning — vendor TBESG/TBESH now (gloss values then come from a fixed file), or log sha256
   only?
3. 12c residual files — redirect to scratch (code change) or accept the overwrite of the untracked PA
   files?
4. Place rows (`kind='place'`, `build_tipnr_metav_link.py`, marked DRAFT/checkpoint-gated in its header)
   are not covered by this step. Leave as copied (keyed to TIPNR entity ids, which a same-code
   import_tipnr keeps), or add a 12d?
5. Expected figures for the edition-upgrade built copy can't be stated from the repo — they come from the
   12a `--diff` / 12b / 12c dry runs on `<built>`, read member by member before any `--apply`.
