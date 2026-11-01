# DESIGN — Q2 build: English rows + English prose from the frozen app feed, two derivations

**Status: DESIGN, 2026-10-31. No code. Nothing on PA. Nothing deployed.** Charter:
`docs/handoffs/CHARTER_edition_upgrade.md` (every ruling below is quoted from §0 there). Every
file:line here was read from the committed tree at `c07288d6`, not from the charter's description.

## Rulings this design answers (word for word, charter §0.6 / §0.8 / §0.10)
- **Q2:** "Q2 keep two derivations; if the build can't produce them independently from one feed,
  report, don't collapse."
- **Q3:** "Q3 re-parse cached HTML on PA for the <i> flag, add an italic column to the TSV before
  0b; no refetch." — DONE (§9.2, §9.6 (b)); the feed carries `italic` + `italic_words`.
- **Q4:** "Q4 English only."
- **Q7:** "Q7 deferred to the dry-run verdict; PA read sizes it first." Then, recorded in §3 (charter
  line 130, CC's record of the ruling, not in the §0 verbatim list): "**Q7 RULED (JP 2026-10-30):
  (i)** — the 1,849 keep the OLD text in this rebuild, censused as a member list, taken in a
  follow-up lane. The |delta| ≥ 5 tail (40 verses) is censused separately".
- **§9.4 ruling on the tail:** "Tail classification accepted. Boundary-move pairs are a unit: if a
  later lane takes one half it takes both."
- **0b facts (charter §2 "PINNED HASH", §9.8 RESULT):** feed = `abp_app_html/abp_app_slots_italic.tsv`,
  sha256 `7bd77385a80de3c3a762b9427658dfec4163d4882f5a3ea56be10ff61436cf63`, 25,526,878 bytes, 9
  columns; `cert_manifest.json` 76 files (entry at `cert_manifest.json:273-276`); punct member list
  241 lines at `tests/fixtures/reassembly/punct_members_live_20261030.txt` (+ `.sha256`).

## 1. Current state — how the build derives English rows, prose, Greek/Strong's today

### 1.1 English rows (`words.english`, `english_head`, `italic`, `greek_pos`, `bracket_id`)
Script: `scripts/build_words_from_abp.py` (2,341 lines). Entry: `run()` at
[build_words_from_abp.py:2024](../../scripts/build_words_from_abp.py#L2024), argv = `bible.db`
(the copy) + `bh_scrape.db` ([:2311-2321](../../scripts/build_words_from_abp.py#L2311)).
- **Source files:** `abp_texts/abp_ot_texts/*.txt` + `abp_texts/abp_nt_texts/*.txt`
  ([:90-91](../../scripts/build_words_from_abp.py#L90), zip fallback [:302-307](../../scripts/build_words_from_abp.py#L302)).
  Each line is `(Abbrev ch:vs) english...Gnnnn [2word 1word]...` — English with Strong's INLINE
  and bracket-order digits inline.
- **Verse iteration:** `iter_verses()` [:309-331](../../scripts/build_words_from_abp.py#L309) →
  `parse_abp_line()` [:234-259](../../scripts/build_words_from_abp.py#L234) splits each line on
  `_STRONGS_RE` [:121](../../scripts/build_words_from_abp.py#L121) (`G*`, `G\d+(.\d+)*`) and feeds
  each (gloss, Strong's) chunk through `_emit_words()` [:194](../../scripts/build_words_from_abp.py#L194)
  (helper-word peel + `bracket_info()` [:147](../../scripts/build_words_from_abp.py#L147) for the
  ABP position digit and the `[`/`]` flags; `_split_numbered()` [:168](../../scripts/build_words_from_abp.py#L168)
  for a gloss carrying more than one digit).
- **Verse keying:** the build loads `verse_map` from the COPY's existing `verses` rows
  [:2070-2072](../../scripts/build_words_from_abp.py#L2070) and SKIPS any source verse with no row
  ([:2117-2121](../../scripts/build_words_from_abp.py#L2117), counted as `Verses skipped`). It never
  creates verse rows (that is `parse_abp.py:318-320`, the first-ever build) — the Hebrews-13 rule.
- **Per-verse build:** `build_verse_words()` [:1854](../../scripts/build_words_from_abp.py#L1854):
  Strong's come from the inline tag (`strongs = raw_strongs[1:]`, base = before the dot,
  [:1895-1896](../../scripts/build_words_from_abp.py#L1895)); `greek_pos` = the source bracket digit
  where one exists, else BibleHub's ([:1904-1905](../../scripts/build_words_from_abp.py#L1904));
  `bracket_id` from the `[`/`]` state machine ([:1908-1918](../../scripts/build_words_from_abp.py#L1908)).
  Then the folded passes (`_split_compounds` [:470](../../scripts/build_words_from_abp.py#L470),
  article-slot [:1067](../../scripts/build_words_from_abp.py#L1067), PN-star [:1223](../../scripts/build_words_from_abp.py#L1223),
  punct float [:1427](../../scripts/build_words_from_abp.py#L1427), g1473 [:1528](../../scripts/build_words_from_abp.py#L1528),
  LORD-subject [:1577](../../scripts/build_words_from_abp.py#L1577), func-word [:1661](../../scripts/build_words_from_abp.py#L1661),
  oath [:1737](../../scripts/build_words_from_abp.py#L1737), numeral [:1775](../../scripts/build_words_from_abp.py#L1775),
  greek_pos backfill [:1786](../../scripts/build_words_from_abp.py#L1786), italic-head strip
  [:1815](../../scripts/build_words_from_abp.py#L1815), star heads [:1837](../../scripts/build_words_from_abp.py#L1837)).
  Insert at [:2154-2160](../../scripts/build_words_from_abp.py#L2154) via `_prefix_base()`
  [:1997](../../scripts/build_words_from_abp.py#L1997) (re-applies the `G` prefix on `strongs_base`).
- **BibleHub overlay (`bh_scrape.db`):** `load_bh_verse_index()` [:334-352](../../scripts/build_words_from_abp.py#L334)
  reads `bh_words` (strongs, english, italic_words, smcap_words, greek_pos); `bh_lookup()`
  [:355-366](../../scripts/build_words_from_abp.py#L355) pairs by (bare Strong's base, normalised
  English) then by base alone, and supplies ONLY `greek_pos` (for non-bracketed slots),
  `italic_words`, `smcap_words`. **`words.italic` today = "the display word is in BibleHub's
  italic_words list"** (`_italic_flag()` [:1420-1425](../../scripts/build_words_from_abp.py#L1420);
  the insert-time rule in `build_verse_words` reads the same way).
- **Pronoun / morph / lemma:** Rahlfs (OT) + TAGNT (NT) via `lxx_align.correct_verse` + `apply_pronoun_corrections`
  ([:2132-2136](../../scripts/build_words_from_abp.py#L2132), [:772](../../scripts/build_words_from_abp.py#L772)).
  Not English-line work; unchanged by this lane (Q4).

### 1.2 English prose (`verses.text`)
**The build does not write `verses.text` at all** (no `UPDATE verses` anywhere in
`build_words_from_abp.py`; the only writers in `scripts/` are `load_abp_prose.py:109`, `fix_emdash.py:46`,
`add_hebrews13.py:194`, and `apply_abp_corrections.py --only verses`). The prose derivation is
`scripts/load_abp_prose.py`: `parse_file()` [:71-82](../../scripts/load_abp_prose.py#L71) reads the
SAME `abp_texts/` files with its OWN regex (`VERSE_RE` [:24](../../scripts/load_abp_prose.py#L24)),
`clean_verse()` [:47](../../scripts/load_abp_prose.py#L47) reorders each `[...]` group by its digits
(`reorder_bracket()` [:28-44](../../scripts/load_abp_prose.py#L28)), strips `G`-numbers, and `main()`
[:85-115](../../scripts/load_abp_prose.py#L85) does `UPDATE verses SET text = ?` per verse.
**`/rebuild-words` never runs it** (`.claude/commands/rebuild-words.md` has no `prose` / `load_abp_prose`
line; the chain at [rebuild-words.md:52-55](../../.claude/commands/rebuild-words.md#L52) is
0 → 1 → 1a → 2 build → 3 finish → 8b… → 9… → 4 → 5 → 6 → 7 → 8). On a same-text rebuild the copy keeps
live's `verses.text` and `finish_rebuild.sh` only patches it (step 4b prose corrections
[finish_rebuild.sh:58-67](../../scripts/finish_rebuild.sh#L58), step 5 em-dash [:69-73](../../scripts/finish_rebuild.sh#L69));
its own comment says "safe even on a build that skipped load_abp_prose" ([:61-62](../../scripts/finish_rebuild.sh#L61)).
So TODAY the two derivations exist (rows: `parse_abp_line` + passes; prose: `clean_verse`), both
read `abp_texts/`, neither reads the other — but the prose side is not in the rebuild chain.
**FACT (code, not charter): the rebuild chain never regenerates prose today.** `scripts/load_abp_prose.py`
is not called by `build_words_from_abp.py` (no `UPDATE verses` in it), not by `finish_rebuild.sh`
(its steps are [finish_rebuild.sh:33-96](../../scripts/finish_rebuild.sh#L33); 4b only PATCHES
`verses.text`), and not by any step of `.claude/commands/rebuild-words.md` (chain at
[:52-55](../../.claude/commands/rebuild-words.md#L52), steps 2-3 at [:78](../../.claude/commands/rebuild-words.md#L78)
and [:118](../../.claude/commands/rebuild-words.md#L118)). Charter §6 step 2 describes prose "through the
prose loader on the same feed" as part of the build; the code has no such step. **Ruling 7 (§9) adds
it as its own step before step 3.**

### 1.3 Greek forms and Strong's
- **Strong's numbers** = the inline `G`-tags in `abp_texts/` (1.1). Nothing from the app feed.
- **Greek forms** are not in `words` at all: `abp_surface` is rebuilt by `/rebuild-words` step 9 on
  the copy and the 10/25 fill restored by 9a ([rebuild-words.md:277](../../.claude/commands/rebuild-words.md#L277)).
  Out of scope here (charter §3).

### 1.4 Where rows and prose are compared today
`scripts/audit_reassembly_diff.py --v2`: `reassembly_hits_v2()` [:228-252](../../scripts/audit_reassembly_diff.py#L228)
reads `verses.text` + the word rows, `reassemble_ordered()` [:182-185](../../scripts/audit_reassembly_diff.py#L182)
puts the rows in the READER's English order via `reorder_english.get_english_order_words`
(the proven port of `static/src/56-library-order-logic.jsx` getEnglishOrderWords; gate
`tests/test_reorder_port.py`), and `diff_verse_v2()` [:188-225](../../scripts/audit_reassembly_diff.py#L188)
classifies each mismatch as dup-gloss / content-other / word-order / punct-position. Live 10/30:
31,237 scanned · word-order 1 (Joh 14:26) · content-other 0 · punct-position 241 (charter §9.5 (a)).

## 2. Target — two derivations of the app feed, Greek/Strong's untouched

| derivation | input | code path | output |
|---|---|---|---|
| **A. English rows** | frozen feed (§3 reader) → per-verse list of (english, strongs, abp_pos, opens, closes, italic, italic_words) | the existing bracket parser `_emit_words`/`bracket_info`/`_split_numbered` over the feed's `english` cell, then `build_verse_words` + every folded pass, unchanged | `words.english`, `english_head`, `greek_pos`, `bracket_id`, `italic`, `italic_words` |
| **B. English prose** | the same frozen feed, read a second time by the prose side | a prose reorder of the feed's per-slot English (`load_abp_prose.clean_verse` applied to the verse's joined English cells, or its equivalent over slots — see Q 7.3; RULED §9.3: `reorder_bracket`) | `verses.text` |
| **Greek / Strong's** | `abp_texts/` + `bh_scrape.db` as today | unchanged (1.1, 1.3) | `strongs`, `strongs_base`, `morph`, `lemma`, `abp_surface` chain |

**B is a NEW step in the chain, not a change to an existing one** (1.2: no step regenerates prose
today). Per ruling §9.7 it is a separate script with its own feed read and its own process, run as its
own `/rebuild-words` step after step 2 and before step 3 (finish_rebuild's 4b prose corrections and
6 split-flip both read `verses.text` as their oracle, so B must precede them).

**"Independent", operationally:** derivation A never reads `verses.text` or anything B wrote;
derivation B never reads `words` or anything A wrote; each reads the feed through its own parser
(A: the bracket parser over the `english` cell; B: the prose reorder over the `english` cells).
They share exactly one thing — the frozen bytes of the feed (sha `7bd77385…`) — and nothing else.
This is the charter's own test (§4.3): "if both come from one flattening step the gate measures
nothing."

**Where A and B are compared:** the EXISTING reassembly v2 (1.4), run on `<built>` after step 3,
with the gate per charter §4.3 (RULED §0.9): "zero word-order + zero content-other", and for
punct-position "The gate for this lane = member diff against that file, nothing numeric" — the
file being `tests/fixtures/reassembly/punct_members_live_20261030.txt`. No new comparison
script; the member diff against the frozen file is a new RUN MODE of the existing audit (nothing
reads that file today — `grep` finds only its own `.sha256`).

**What A keeps from `abp_texts/` and what it takes from the feed — the pairing (1:1 by slot):**
Q4 says English only. A still needs, per word row, the Strong's number, the Greek order and the
morph/lemma — all from `abp_texts/` + Rahlfs/TAGNT today. So derivation A is a per-slot
TRANSPLANT: the `abp_texts/` row stream stays the spine (Strong's, position, bracket digits where
the feed has none), and the feed supplies the English cell + italic for the paired slot. The
pairing rule is the charter's §3 "all-or-nothing": a verse is taken from the app only where every
slot pairs 1:1 by (position, Strong's) after the split-flip swap rule; otherwise the verse keeps
the old text (Q7 (i)). The existing aligner is `audit_abp_app_vs_surface.align_verse()`
[:288-315](../../scripts/audit_abp_app_vs_surface.py#L288) (same-count → index pairing with
`agree()`; else LCS + nearest-reorder). Whether the BUILD reuses that aligner or the "same count +
same Strong's per index" rule alone is Q 7.1.

## 3. Feed reader — interface

New module `scripts/abp_app_feed.py` (name proposed; nothing exists). Read-only toward every
database; opens no database at all.

**Inputs**
1. `feed_path` — `abp_app_html/abp_app_slots_italic.tsv` (gitignored; PA + local second copy).
2. `manifest_path` — `cert_manifest.json` (committed). **The sha pin is asserted here:** the reader
   hashes the feed file and refuses to yield a single row unless the hash equals
   `manifest["files"]["abp_app_html/abp_app_slots_italic.tsv"]["sha256"]`
   (`cert_manifest.json:273-276` = `7bd77385…`) AND the byte size matches (25,526,878). Same
   check `cert_manifest.py cmd_verify()` does ([:190-213](../../scripts/cert_manifest.py#L190)),
   done again at read time so a build cannot run on a feed the manifest does not pin. The literal
   hash is NOT duplicated in the reader; the manifest is the one pin (charter §2, §9.8).
3. `book_map` — `audit_abp_app_vs_surface.APP_TO_ABBREV` [:86-104](../../scripts/audit_abp_app_vs_surface.py#L86)
   imported, never copied (the audit exits FATAL on an unmapped app book name, [:243-244](../../scripts/audit_abp_app_vs_surface.py#L243); the reader does the same).

**Not an input: the punct member list.** The brief lists it as a reader input; the charter does not
(§4.3: it is the v2 GATE's member file on the built copy, consumed AFTER the build — see §6). The
reader has no use for it and must not read it (it is derived from live, not from the feed).

**Outputs** — one record per feed slot, in file order, keyed `(abbrev, chapter, verse, slot_index)`:
`strongs` (verbatim, dash-joined compounds kept), `greek` (verbatim; NOT used by this lane),
`english` (verbatim: bracket digits and `[`/`]` inline, exactly `abp_texts/` notation — charter §2
"the existing bracket parser applies"), `italic` (0/1), `italic_words` (verbatim italic text, `''`
when 0 — `reparse_abp_app_italic.py:12-15`). Plus a per-verse grouping helper yielding, for each
`(abbrev, chapter, verse)`, the ordered slot list — the unit both derivations consume. Column
names and meanings are those of the feed header (`abp_app_slots_italic.tsv` line 1).

**How the Q3 italics attach (derivation A):** today `italic` = display word ∈ BibleHub
`italic_words` (`_italic_flag`, 1.1). On a transplanted slot the reader's `italic_words` replaces
the BibleHub string in the row tuple (idx 8 `iw`) BEFORE `build_verse_words` runs, and `italic`
is derived by the same `_italic_flag` rule from it; `_strip_italic_heads` [:1815](../../scripts/build_words_from_abp.py#L1815)
then reads the feed's italics the same way it reads BibleHub's. Where the feed says `italic=1`
with an `italic_words` that is not the display word (a multi-word cell whose italic part is not
the head), the row's `italic` stays 0 and `italic_words` carries the words — the same shape
BibleHub produces today. Non-transplanted verses (Q7 (i)) keep BibleHub italics unchanged.
**Derivation B ignores italics** (prose carries no italic marking today; `verses.text` is plain).

## 4. Joins — feed verses ↔ `abp_texts/` verses ↔ `verses` rows

**Key:** `(abbrev, chapter, verse)` on both sides after `APP_TO_ABBREV`. Three classes, ruled:
1. **Plain pairing** (everything not below): same key both sides.
2. **Psalm titles** — "our Psalm titles are verse 0 = the app's verse 1 (~~146~~ 147 chapters — corrected 2026-10-31, §9.14)" (charter
   §2): our `(Psa, ch, v)` pairs with feed `(Psa, ch, v+1)` for every chapter where our side has
   a verse 0. That is exactly the audit's rule ([audit_abp_app_vs_surface.py:12-14](../../scripts/audit_abp_app_vs_surface.py#L12),
   `psa_shift` at [:420-424](../../scripts/audit_abp_app_vs_surface.py#L420); the census reuses it,
   [census_count_differs.py:39-44](../../scripts/census_count_differs.py#L39)).
3. **Pro 16 (reordered), Pro 24, Jer 10, Hab 3** — charter §2: "**JP-ruled: NO renumber on our
   side** — the English is taken by the per-verse map from the audit's run output, our verse keys
   stay." **The audit has no such map in code**: it pairs these chapters by the PLAIN key and only
   PRINTS the best whole-chapter shift and per one-sided verse its best match
   ([audit_abp_app_vs_surface.py:15-17](../../scripts/audit_abp_app_vs_surface.py#L15)); no map file
   is committed (searched `scripts/`, `tests/fixtures/`). The 28 versification members of the
   |delta|≥5 tail (Pro 16 ×5, Pro 24 ×11, Jer 10 ×7, Hab 3 ×5 — charter §9.4 (c)) are "alignment
   failure by construction" under the plain key. **Under Q7 (i) they are count-differs members and
   keep the old text in this rebuild**, so the build needs no map for them now; the map is the
   follow-up lane's input (Q 7.4 asks where it is pinned).

**Known limitation — glued notes (§9.41, 2026-10-31).** The glue census
(`tests/fixtures/edition_upgrade/feed_glue_census_20261031.tsv`) finds a glued alternate rendering only
where the feed word is NOT an `abp_texts/` word and splits into an old word of the SAME slot plus a
known word, in a verse whose chunk count matches. It cannot see (a) a glue that happens to form a real
word, or (b) a glue in a cell with no old partner. Neither is measured; both would pass the strict test.

**A feed verse with no `verses` row (feed-only):** skipped and COUNTED, like the build's own
`Verses skipped` ([build_words_from_abp.py:2117-2121](../../scripts/build_words_from_abp.py#L2117)),
and the count is declared (charter §4.1: `verses` 31,237 exact, no renumber; the feed has 31,238
verses vs our 31,237 — the census read "ours-only 9" and the feed side's extras come from the
Psalm shift and the four versification chapters). Expected feed-only after the Psalm shift: the
one-sided verses of class 3 only; any other feed-only verse = STOP (a book-map or key defect).
**Our verse with no feed verse (ours-only, census: 9):** keeps its `abp_texts/` English (both
derivations fall back to `abp_texts/` for that verse — the same text they produce today), listed by
member in the run log. Neither case ever drops a verse row or a word row (Hebrews-13 rule).

**Count-differs verses (Q7 (i), 1,849 = OT 1,451 · NT 398):** both derivations take the verse from
`abp_texts/` (today's text), so A and B stay two derivations of ONE source per verse — never A
from the feed and B from `abp_texts/` (that would make every count-differs verse a v2 hit by
construction). The member list is `~/count_differs_members.tsv` on PA (charter §3), NOT in the
tree; the build must be given it as a file, pinned (Q 7.2). The 40-verse tail inside it (28
versification + 10 boundary-move pairs as units + 2 real edits: 1Sa 17:55, 1Pe 3:12 — §9.4 (c))
keeps the old text with the rest; the pairs stay units (§0.8).

## 5. Declared rows — Joh 14:26 and Mark 1:9

Charter §4.10 (RULED §0.9/§0.10): Joh 14:26 "fixed in the upgrade rebuild as a DECLARED ROW (Joh
14:26, the πνεῦμα/ἅγιον pair), never a live patch" with the declared outcome "v2 word-order 0 with
Joh 14:26 clean … if the built copy still shows the hit, the lane STOPS on it"; Mark 1:9 "of the"
(τῆς, G3588) "old `english` "of the", new per the app edition (blank or the app's value). Appears in
the compare_words diff by name."

**How they are carried:** both are ENGLISH-ROW outcomes, checked by two existing gates — v2 (§4.3)
for Joh 14:26 and step-4 `compare_words` (charter §6 step 4: "`english` / `english_head` /
`verses.text` rows = the declared 29% set + Mark 1:9") for Mark 1:9. The `--declared` fixture
(`gate_greek_header.py --declared`, landed `c07288d6`) covers gate A/B tables only — `pn_binding`,
`tipnr_entities`, `abp_surface`, `words`/`verses` COUNTS, `pn_greek_identity` keys — and has no
English-row section (`tests/fixtures/rebuild_trap/declared_deltas_20261025.json`, the only
instance). So the design carries the two rows as **named members in this lane's declaration
file** (`tests/fixtures/edition_upgrade/declared_deltas.json`, §6) under a section the gate does
not read (`english_rows`, informational), AND as the two gates' own expected members: Joh 14:26 →
v2 word-order member list must be EMPTY (the row is the one live hit, so "0" is only true if it
left); Mark 1:9 → present by name in the compare_words `english` diff, value = the app's cell.
Whether the gate schema grows an `english_rows` section it actually CHECKS is a new-field
checkpoint (memory `feedback_new_fields_checkpoint`) — Q 7.5.

## 6. Gates on the copy build — in order, existing scripts, "before" figures from the charter

Run on `<built>` (= `<src>.new` renamed, [rebuild-words.md:56-58](../../.claude/commands/rebuild-words.md#L56)),
read-only, each control fired first. "Before" = live 2026-10-30 as the charter records it.

| # | when | script | gate | before (charter) |
|---|---|---|---|---|
| 1 | after step 3 | `scripts/cert_invariants.py <built>` | 7/7; pins re-declared: `verses` 31,237 exact, `words` declared (§4.1), **`abp_corrections_active` 51** (pin `6e9d2df8`; re-adjudicated per §4.7 before the swap commit, Q 7.6) | 6/7 live with check 4 red on the old 30 — now 51 pinned |
| 2 | 8b.3 | `scripts/gate_greek_header.py <src> <built> --declared tests/fixtures/edition_upgrade/declared_deltas.json` (`c07288d6`; [rebuild-words.md:261](../../.claude/commands/rebuild-words.md#L261)) | A/B as declared, C PASS; run BEFORE step 9 | 10/25 worked example: 3 Michaiah rows |
| 3 | after step 3 (and again after 9a) | `scripts/audit_reassembly_diff.py <built> --v2` (+ `--controls --v2` first; `tests/test_reorder_port.py` green first) | word-order 0 · content-other 0 · punct-position = MEMBER DIFF vs `tests/fixtures/reassembly/punct_members_live_20261030.txt` (241); no new member | word-order 1 (Joh 14:26) · content-other 0 · punct 241 (§9.5 (a)) |
| 4 | step 6 | `scripts/audit_phrase_gloss_underdist.py <built>` | control Psa 39:1 FIRED; member list of newly flagged / newly cleared vs live; "a NEW flagged row that is not an app-edition wording change = stop" (§4.4) | FLAGGED 693 · beyond allowlist 662 (gate ≤ 671) · NO-EVIDENCE 1,814 (§4.4) |
| 5 | step 6 | `scripts/census_count_differs.py <built> <feed> --out …` | the count-differs set on `<built>` EQUALS the pinned member list (Q7 (i): nothing taken) — member diff, not a count | 1,849 (OT 1,451 · NT 398); ours-only 9 (§3) |
| 6 | step 3 / step 6 | `scripts/apply_abp_corrections.py` (finish_rebuild 4b + 7) then `cert_invariants` check 4 | every active row HOLDS (per-row) and the count = the §4.7 re-adjudication (33 retire / 12 re-author / 6 re-check — Q 7.6) | 51 active, all holding (§9.4 (i)); member file `tests/fixtures/corrections/abp_corrections_active_live_20261031.txt` |

Then the standing chain gates (step 4 compare_words per column, 5 strongs_base 0, 6 the §4.8
re-declared floors, 7 spot-check incl. Gen 1:21 and Mark 1:9) and the step-9 chain (9 → 9a → 9b →
9c re-freeze). The brief's six "before" figures all match the charter (693/662, 1,849, 51, 241,
`7bd77385`, 76 files); no mismatch to report.

## 7. Open questions for ruling

1. **Slot pairing rule for the transplant (§2).** Charter §3 says "every slot pairs 1:1 by
   (position, Strong's) after the split-flip swap rule". The only committed aligner is
   `audit_abp_app_vs_surface.align_verse()` ([:288-315](../../scripts/audit_abp_app_vs_surface.py#L288)),
   which also pairs by LCS and "reorder:<distance>" when counts differ, and expands dash-joined
   app compounds into sub-slots ([:210-224](../../scripts/audit_abp_app_vs_surface.py#L210)). Does
   derivation A pair with that function (one aligner, never a second copy — the census's own rule,
   [census_count_differs.py:5-6](../../scripts/census_count_differs.py#L5)), or with the stricter
   "same slot count AND same Strong's at every index" rule the charter sentence states?
2. **The count-differs member list is on PA only** (`~/count_differs_members.tsv`, charter §3 line
   129) and the build needs it as input under Q7 (i). Is it frozen into the tree like the punct and
   corrections lists (`tests/fixtures/<lane>/count_differs_members_20261030.tsv` + `.sha256`), and
   is it re-read from `<src>` at build time and diffed against the frozen copy before the build runs?
3. **Prose derivation B's reorder.** Today's prose reorder is `load_abp_prose.reorder_bracket()`
   ([:28-44](../../scripts/load_abp_prose.py#L28), sorts a `[...]` group by its digits); the reader's
   reorder is `reorder_english.py` (JS port, sorts by `greek_pos`), used by v2. If B uses
   `load_abp_prose` over the feed's joined English cells, B stays the independent derivation it is
   today; if B were built from the JS port it would share the reader's logic with the v2 gate
   itself. Which reorder is B? (Charter §4.3 says only "prose via a reorder of the app slots per
   verse".)
4. **The per-verse versification map** for Pro 16 / Pro 24 / Jer 10 / Hab 3 (charter §2: "taken by
   the per-verse map from the audit's run output") exists nowhere in the tree — the audit prints
   best-match lines, it keeps no map ([audit_abp_app_vs_surface.py:15-17](../../scripts/audit_abp_app_vs_surface.py#L15)).
   Under Q7 (i) these 28 verses keep the old text now. Does the follow-up lane own the map, and is
   it to be pinned from the audit's printed lines or hand-ruled?
5. **Declared English rows in the `--declared` schema (§5).** The landed fixture shape has no
   English-row section; Joh 14:26 and Mark 1:9 are checked by v2 and compare_words. Does the
   declaration file gain an `english_rows` section the gate CHECKS (new field = checkpoint), or
   stay informational with the two gates as the check?
6. **Corrections re-adjudication timing (§6 row 6).** Charter §4.7: "`cert_invariants` pin: 30 →
   the post-build active count, in the swap commit" and the 33/12/6 verdicts ruled §0.7. The
   `finish_rebuild.sh` corrections steps (4b, 7) apply rows by precondition and LOUD-skip a
   mismatch ([finish_rebuild.sh:58-67](../../scripts/finish_rebuild.sh#L58), [:88-96](../../scripts/finish_rebuild.sh#L88));
   `build_abp_corrections.py` seeds all 57 ENTRIES ([:184-354](../../scripts/build_abp_corrections.py#L184)).
   Do the 33 retire / 12 re-author land as a seed-script change BEFORE the copy build (so the
   copy's table is the post-upgrade table and check 4 reads the new count), or as status updates on
   the copy after step 3?
7. **`load_abp_prose` is not in `/rebuild-words`** (§1.2). Charter §6 step 2 says the build takes
   "`verses.text` through the prose loader on the same feed, independently". Does derivation B
   become a step inside `build_words_from_abp.py run()` (one script, two code paths), or a separate
   script run as its own step (2b) before step 3 — and in either case, does the Q2 ruling
   ("produce them independently from one feed") require they not share a process?
8. **Which verses B writes.** Under Q7 (i), count-differs verses keep `abp_texts/` prose; all other
   paired verses get feed prose. The 18 active `verses.text` correction rows (charter §9.4 (a)) are
   today applied AFTER prose (finish_rebuild 4b). Of those 18, §4.7 says 12 prose rows are CURED
   upstream and 6 STILL PRESENT. Is B's output for a cured verse the feed text with the row retired,
   or the feed text with the row still applied (which would LOUD-skip on precondition)?
9. **`verses` 31,237 exact vs feed 31,238** (charter §4.1 vs §2). The one-verse difference is not
   attributed in the charter. Which feed verse is it (a Psalm-shift artefact, or one of the four
   versification chapters), and is "feed-only = STOP unless in class 3" (§4) the rule?

## 8. Out of scope — stated
- **The feed taking over the Greek / Strong's role from `abp_texts/`** — HELD, later lane
  (TODO "HOLD (JP 10/30, not this lane)"; charter §3 "This charter does not take the app's Greek or
  numbers"). Derivation A's spine stays `abp_texts/`. **Includes rebuilding the ruling-10 attestation
  map (`build_attestation_map`, harvested from `abp_texts/`) from the feed — §9.31, 2026-10-31.**
- **Tier B 12 re-author** (the 12 STILL-PRESENT rows' new `source_value`, §4.7) — its own change,
  Q 7.6 only fixes WHEN it lands relative to the copy build.
- **Step 7 re-scope** (the spot-check list) — unchanged beyond the charter's two added verses.
- The Q6 post-swap redraw pass, the 9c re-freeze mechanics, and the follow-up lane for the 1,849.

## 9. Rulings 2026-10-31 (JP, verbatim; numbered to match §7)
1. Strict pairing: same count + same Strong's at every index after split-flip. Fail → Q7 (i). align_verse is census tooling, not called by the build.
2. count_differs_members frozen into the tree (live dump + .sha256, punct precedent); ~~reader re-derives from the source copy at build time, diffs against frozen, any difference = stop.~~ **AMENDED by §9.10 (2026-10-31):** the re-derive-and-diff is a separate gated census step on the copy before the build (`census_count_differs.py` vs the frozen file); the reader only verifies the frozen file's .sha256 and loads it. Dump is a later gated PA step.
3. Derivation B uses load_abp_prose.reorder_bracket. The JS port (reorder_english.py) stays the v2 gate's; B shares no logic with the gate.
4. Versification map (Pro 16 / Pro 24 / Jer 10 / Hab 3): follow-up lane; Q7 (i) holds them on old text here.
5. Declared English rows stay informational; no english_rows section; v2 + compare_words check them.
6. Corrections re-adjudication = status updates on the copy ~~after step 3~~ **before B (AMENDED by §9.50, 2026-10-31: §9.8 wins)**; seed script untouched this lane; pin moves in the swap commit per §4.7.
7. B is a separate script, its own step in /rebuild-words before step 3, own process, own feed read. Independent = neither reads the other's output. **AMENDED by §9.48 (2026-10-31):** "neither reads the other's derived TEXT" — the eligibility decision is shared (A emits it, B consumes it); the text derivations are not.
8. Order on the copy: retire the 33 cured → B writes feed text → finish_rebuild applies remaining active. A cured row still active that loud-skips = stop, not skip.
9. 31,237 vs 31,238 attributed on the reader's first dry run on the copy before any write; feed-only verse = stop unless in the versification class.

### Feed-reader plan rulings 2026-10-31 (JP, verbatim; numbered to match the plan's Q1–Q7)
10. Reader opens no DB, never re-derives. Re-derive-and-diff = separate gated census step on the copy before the build (census_count_differs.py vs frozen file; align_verse allowed there, it's census tooling). Reader only verifies the frozen file's .sha256 and loads it. Amend §9.2's wording to this.
11. Versification class frozen: tests/fixtures/edition_upgrade/versification_class.json, chapters only, sourced to CHARTER:78-80 in the file. Not hardcoded.
12. Same-count strict-rule failures: keep old text, census as strict_fail list, count reported at dry run. Not a stop.
13. Frozen count-differs dump must be run on the pinned italic TSV on the copy (that is the §9.2 step). 1,849 remains the "before". Seven-column identity check is not a substitute. **AMENDED by §9.18 (2026-10-31):** the frozen count-differs set the BUILD uses is the chunk-level set, generated locally from the frozen feed + committed abp_texts — no PA dump. 1,849 stays the Q7 "before" for the post-build census.
14. Psalm-title chapters = 147 (measured, committed abp_texts). Correct CHARTER:78 with a dated note in this commit.
15. No committed feed slice (third-party text, rebuild_trap precedent). Tests use a synthetic feed + synthetic manifest; real-TSV tests skip when the file is absent.
16. ops.md:189 "74 files" → docs wrap commit, not this one.

**Landed with these rulings:** `scripts/abp_app_feed.py` (shared library + `--check` / `--attribute <copy>`),
`tests/fixtures/edition_upgrade/versification_class.json`, `tests/test_abp_app_feed.py` (in ci.yml + pre-commit).
Local `--check` on the real TSV 2026-10-31: pin OK (`7bd77385…`, 25,526,878 bytes) · 577,994 slots · 31,238
verses · 66 books · keyed vs `abp_texts/` 31,237: Psalm shift 147 · paired 31,228 · ours-only 9 · feed-only 10
(Pro 16 ×7, Pro 24 ×1, Jer 10 ×1, Hab 3 ×1) · outside the class 0. This is against `abp_texts/`, NOT the §9.9
attribution (that is `--attribute` on the copy, a later gated PA step). `--attribute <copy>` opens the copy
read-only (accepted 2026-10-31); `<copy>` is mandatory, no default, an empty or missing path = stop. The §9.12
strict_fail list is NOT in the reader — it stays with derivation A's dry run (ruled 2026-10-31).

### Derivation A plan rulings 2026-10-31 (JP, verbatim; numbered to match the A plan's Q1–Q9)
17. Pair at chunk level on the abp_texts Strong's spine, before _emit_words.
18. Frozen count-differs for the build = chunk-level set, generated locally by the dry run from frozen feed + committed abp_texts, committed as keys only (tests/fixtures/edition_upgrade/count_differs_chunk_<date>.tsv + .sha256). No PA dump. 1,849 remains the Q7 "before" for the post-build census. Chunk-level/frozen disagreement = stop (inputs drifted).
19. Check order: frozen → versification → strict → strict_fail.
20. Neighbour swaps → strict_fail, reason swap. Old text.
21. Carry old and feed English. Greek-side passes (bh_lookup greek_pos, _fix_backwards_pairing, any pass deciding Strong's/morph/lemma from English) read OLD English. English-editing passes (_split_compounds, pronoun correction) run on feed English for strict-pass verses. BEFORE coding: classify every pass in run() into those two bins, file:line each, and report.
22. greek_pos/bracket_id changes allowed (English-reassembly metadata). Dry run counts verses where either changed.
23. italic flag transplants now; italic_words HELD pending a gated read of bh_scrape.db format. Dry run reports italic_words unchanged.
24. Strict = full dotted number. Reason tag dotted.
25. strict_fail TSV key: book, chapter, verse, first_diff_pos, ours_strongs, feed_strongs, reason ∈ {swap, dotted, footnote, untagged, other}. Path ~/edition_upgrade_runs/.
(v) closed: 1Pe 3:12 → old text, reason footnote; the untagged trailing-gloss verse → old text, reason untagged — name that verse in your report.
— The untagged verse is **Mal 3:6** (`abp_texts/abp_ot_texts/abp_malachi.txt`: the line ends `I change not.G3756 G`, a bare `G` with no number; the feed's last slot is `3756-241.2`).

### Pass-classification rulings 2026-10-31 (JP, verbatim; numbered to match the classification Q1–Q7)
26. Pronoun correction = Group 2, old English.
27. _split_compounds runs on both English values; if the resulting positions differ, the verse → strict_fail reason split, old text. Positions never change on a strict-pass verse. Dry run counts it.
28. _split_pn_article_lump decides on old English (Group 2); the English move is mirrored onto feed English. If the decision on feed English would differ → strict_fail reason lump.
29. bh_lookup matches on old English; its greek_pos, italic_words and smcap_words are all kept as today (italic_words held per §9.23).
30. Confirmed: _strip_helper_double_tag and _g1473_gloss_retag read old English.
31. Attestation map stays harvested from abp_texts this lane. Rebuilding it from the feed belongs to the held "feed takes over Greek role" lane — add to §8 out of scope.
32. Yes: add the second English column (row 13→14) and the build_verse_words parameter. New-field checkpoint: fixtures committed + test lands with the change.
Reason set is now {swap, dotted, footnote, untagged, split, lump, other}. Mal 3:6 recorded as the untagged verse.
**§9.32 SUPERSEDED by §9.33 (2026-10-31)** — no 14th column; build_verse_words is called twice, not re-parameterized.

### Mechanism + dash rulings 2026-10-31 (JP, verbatim)
33. §9.32 superseded. Mechanism: two complete, independent row-set builds per verse — the OLD set exactly as today (all passes, old English), and the FEED set with the same pipeline on feed English. Compose at the end, row-aligned by position: Greek-side columns (strongs, strongs_base, morph, lemma, position, smcap_words) from the OLD set; English-side (english, english_head, italic, greek_pos, bracket_id) from the FEED set; italic_words from OLD (held). No per-step interleaving. Row counts differ or any row's Strong's/position disagrees between the sets → strict_fail, old text. This replaces the 14th column; build_verse_words is called twice, not re-parameterized.
34. New reason: rows. Covers the 120 and any compose-time misalignment. Reason set: {swap, dotted, footnote, untagged, split, lump, rows, other}.
35. The " -" cells are the ABP clause dash with one hyphen lost in the fetch. (a) Run the §4.6 dash check on the pinned feed first as a full scan: list every cell matching bare " -" at cell end, and separately any bare " - " mid-cell or other dash shape; commit the scan as tests/fixtures/edition_upgrade/feed_dash_census_<date>.tsv (keys + shape only, no English text) + .sha256, and report counts. (b) If every hit is end-of-cell " -", the transplant step (not the reader — reader stays verbatim) normalizes " -" → " --" so fix_emdash handles it, with the count 4,248 pinned as an assertion. Any other shape → report before ruling, don't normalize it.
   — (a) RESULT 2026-10-31 (`scripts/census_feed_dash.py`, full scan, 577,994 cells): end_space_hyphen 4,248 (each the cell's only shape) · mid_space_hyphen 34 · double_hyphen 3 · other_hyphen 12 · en/em dash 0 → 49 non-end cells, so (b) was not applied before ruling.

### Dash + markup rulings 2026-10-31 (JP, verbatim)
36. The 49 non-end dash cells: verse → strict_fail, old text, new reason dash. No per-shape cleanup this lane.
37. Yes, full markup census: scripts/census_feed_markup.py, same shape as the dash scanner (pin check, no DB, keys + marker class only, no English text) → tests/fixtures/edition_upgrade/feed_markup_census_<date>.tsv + .sha256. Marker classes: backslash code (name the code), digit+Latin-transliteration in English, anything else non-English you find — report the class list before freezing. Those verses → strict_fail, old text, reason markup. 1Pe 3:12 moves from footnote to markup; footnote reason retired. Charter §4.6 "one footnote" gets a dated correction with the count.
38. Yes: (b) applies to the 4,248 end-of-cell cells alone — normalize " -" → " --" in the transplant step, count pinned at 4,248, assertion fails on any other number.
39. Yes: both scanners get a synthetic-cell test per shape, added to CI and pre-commit, one commit with both census files.
Reason set: {swap, dotted, untagged, split, lump, rows, dash, markup, other}.

### Census-freeze rulings 2026-10-31 (JP, verbatim)
40. Marker class list frozen as found (11 classes incl. greek_letter=0). Freeze feed_markup_census_20261031.tsv + .sha256 from it. Charter §4.6 corrected: 21 backslash cells / 46 marked cells, dated.
41. The 50 unmarked glues: freeze as their own file, tests/fixtures/edition_upgrade/feed_glue_census_20261031.tsv + .sha256, columns key + feed_word + verdict ∈ {glued, wording, unclear}. Your reading stands as the verdict: the 19 "look glued" = glued; the wording-change list = wording; 2Ki 9:8 = unclear. glued and unclear → strict_fail reason markup; wording → eligible to pass (new readings are the point of the upgrade). Record the detection gap (glue forming a real word, or no old partner) as a known limitation in DESIGN §4.
42. Double spaces: check whether any existing pass or the insert already collapses whitespace (file:line). If yes, report and do nothing. If no, the transplant step folds runs of spaces to one, count pinned at 12,480 cells.
   — Checked 2026-10-31: NO general collapse. `clean_english` (`build_words_from_abp.py:139-144`) strips ends only; the insert (:2153-2158) writes english as built. Only slots a pass REWRITES get single-spaced (e.g. `_split_compounds` :609/:613 via `" ".join(...)`). So the transplant step folds runs of spaces to one, 12,480 cells pinned.

### Compose rulings 2026-10-31 (JP, verbatim)
43. One optional keyword on build_verse_words (e.g. bh_match_english=None): when given, bh_lookup matches on those old-English rows instead of the set's own English; all other behavior unchanged. §9.33 "not re-parameterized" amended to "one optional keyword, default preserves today's behavior". Default-path test must prove today's output is byte-identical.
44. italic flag from the OLD set until the §9.23 held read. §9.23 amended: nothing italic-related transplants this lane.
45. Yes: pronoun correction runs once on the old set; the same corrections are applied to the feed set by row index; count mismatch → rows.
46. Merge split and lump into one reason: passdiff. No hooks inside build_verse_words. Reason set: {swap, dotted, untagged, dash, markup, rows, passdiff, other}.
47. Gaps 5–7 as proposed: check order frozen → versification → untagged → markup → dash → Strong's test (swap → dotted → other) → compose (rows → passdiff); first fire takes the reason; TSV columns for non-Strong's reasons as you described.
**Amendments:** §9.33 "build_verse_words is called twice, not re-parameterized" → "called twice; one optional keyword (`bh_match_english`), default preserves today's behavior" (§9.43). §9.23 "italic flag transplants now" → nothing italic-related transplants this lane (§9.44). Reasons `split` / `lump` (§9.27/§9.28) → merged as `passdiff` (§9.46).

### Derivation B plan rulings 2026-10-31 (JP, verbatim; numbered to match the B plan's Q1–Q10)
48. A owns eligibility. A's dry run emits the eligible-verse set as a keys-only artifact (eligible_<date>.tsv in --out, with reason for ineligible); B consumes it. §9.7 amended: "neither reads the other's derived TEXT" — the eligibility decision is shared, the text derivations are not. B does not run A's row build.
49. Yes, B may import shared code from build_words_from_abp (normalizers, decide if needed). Code, not output.
50. §9.8 wins: retire the 33 cured rows on the copy before B runs. §9.6 amended from "after step 3" to "before B".
51. The 6 still-present prose verses: carve-out on BOTH sides — A keeps old rows, B keeps old prose, reason correction. Re-author stays out of scope.
52. Punct-position members on the copy build: v2 reports the member diff vs the frozen 241 instead of failing on new members; new members on transplanted verses are listed for ruling before swap; any new member on a NON-transplanted verse = fail.
53. Yes: full bracket-shape census on the feed (scripts/census_feed_brackets.py, same pattern, frozen + .sha256), those verses → strict_fail reason bracket in A's checks too. A's check change + recount is its own commit before B.
54. clean_verse runs unchanged on feed text; B's dry run counts each cleanup rule's fires on feed text (stray-G and stray-bracket expected 0).
55. Write only where new prose differs; identical verses counted as unchanged, not written.
56. Dry-run TSV path and columns as proposed.
57. No separate backup — the copy is the throwaway. B requires an explicit path and refuses the live path (~/bible-db/bible.db) outright.
Reason set: {swap, dotted, untagged, dash, markup, bracket, correction, rows, passdiff, other}.
— **Landed with §9.51/§9.53 (step 1 of the B order, 2026-10-31):** `scripts/census_feed_brackets.py` (control: fires
4/4 on the known `abp_texts/` positives Mat 21:19, 1Ch 22:15, Job 24:19, Zec 10:3) → frozen
`tests/fixtures/edition_upgrade/feed_bracket_census_20261031.tsv` (59 feed verses / 62 rows: duplicate_digit 29 ·
digit_gap 26 · unclosed 5 · item_without_digit 1 · open_while_open 1 · close_without_open 0 · digit_outside 0).
The §9.51 carve-out is a frozen keys file sourced to charter §4.7 (`correction_carveout_20261031.tsv`, 6 verses) so
A's checks stay database-free. **Placement (CC's, not in the rulings):** `correction` right after versification (so
the 6 always read "correction" — all 6 also carry feed bracket defects), `bracket` right after dash. A's dry run now
also writes `eligible_<date>.tsv` (book, chapter, verse, eligible 0/1, reason). Local recount (no db, lexicon/map/
BibleHub/Rahlfs off): transplanted 29,623 · count_differs 704 · versification 32 · ours-only 9 · strict_fail 869
(other 464 · rows 111 · passdiff 73 · dotted 61 · markup 60 · bracket 50 · dash 37 · swap 7 · correction 6 ·
untagged 0) — sums to 31,237; the 59 census verses = bracket 50 + correction 6 + count_differs 2 + markup 1.
— **§9.19 order RATIFIED (JP 2026-10-31, with the step-1 commit `e4c0afe3`):** frozen → versification → correction →
untagged → markup → dash → bracket → Strong's → compose.

### PA sequence rulings 2026-11-01 (JP, via the ruling chat)
58. `pn_binding.rule` blank = `''` (text, length 0), never NULL — charter §9.4 (g) "blank" means `''`. Read on the copy `bible_edupg_test_20261101.db` (step 4, log `~/edition_upgrade_runs/step4_michaiah_20261101.log`): the 3 Michaiah rows (2Ki 22:12, 2Ch 17:7, Neh 12:41) read `''` / text / length 0, and no `rule` cell in the table is NULL. The 3 rows are NOT entered in `tests/fixtures/edition_upgrade/declared_deltas.json` — live fuzzy/`''` = rebuild fuzzy/`''` (binder default `entity_resolution.py:658`, :760), so they are unchanged and a declared-but-unchanged row fails gate A (`gate_greek_header.py:102-104`); they stay in the 10/25 fixture only.
