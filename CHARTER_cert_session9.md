# ABP Corpus Certification — Session 9 CHARTER (canonical)

**Seat: HIGH from the start.** Session 9 *is* the rebuild session — the whole point is a full
words rebuild carrying FIVE fixes at once (was seven; the old a/c/d merged into (P) 2026-07-05 after the
diagnosis landed). Don't open it on the low/medium census seat.

**This is the SINGLE canonical S9 charter — the one source of truth.** It consolidates the TWO prior
docs into one file:
- `HANDOFF_cert_session9.md` — the prior canonical S9 handoff (Session 8 scope + the 2026-07-05
  merged diagnosis). This charter is that document, carried forward verbatim, plus the consolidation
  layer below. **SUPERSEDED → pointer only.**
- `AUDIT_reassembly_rebuild.md` — the reassembly-diff raw diagnosis + rebuild plan (2026-07-04); its
  findings/counts/family-table/render-trace/rebuild plan are folded in here as diffs (P)/(e)/(f)/(g).
  **SUPERSEDED → pointer only** (kept for raw diagnosis history).

**Which side wins where the two disagree (READ THIS):** the newer diagnosis wins, NOT the older
reassembly memo. The reassembly memo's "prime suspect = `_split_compounds` article-fronting" was
DISPROVEN by the 2026-07-05 full-build diagnosis (it was the *stale* half of the 364; the real
splitter is `_redistribute_pronoun_compounds`). See **killed suspects** below — do not resurrect it.
The reassembly memo's older framing ("seven passes", "13 leaks", "6 word-order families", "364
defects") is superseded by the merged numbers ("five fixes", "11 leaks", "156 stale + 208 survivors").
Everything you need to run the rebuild is in THIS file.

## Frame (unchanged, governs all audit sessions)
Two-tier standard. **Tier A** = ingest-faithfulness. **Tier B** = source defects as a versioned overlay
(`abp_corrections`, 18 rows). Certification COMPLETE since Session 3; every session extends the perimeter,
never re-opens it. Full record: `AUDIT_abp_certification.md`. Standing witness for source readings = the
official ABP app (apostolicbibleapp.com).

## Architecture A — PINNED (the oracle stays independent)
Decision locked 2026-07-04, non-negotiable for this rebuild:
- **`verses.text` stays INDEPENDENTLY DERIVED.** It is the witness that caught the whole word-order
  class — it is the ORACLE. Do NOT derive it from the word rows (that was "Architecture B" — rejected;
  it makes the cross-check trivial and destroys the independent oracle).
- Both stores rebuild from the ONE pinned feed (`abp_texts/`); neither is synced from the other
  (standing rule). `build_words` is fixed to MATCH `load_abp_prose`'s source order; v2 stays as the
  independent cross-check and is then wired into `cert_invariants.py` at zero so the two stores can
  never silently drift again.

## Root cause of the (d)-(g) arc (verified, so nobody re-diagnoses it)
`verses.text` and the word rows come from the **same** ABP source (`abp_texts/`) but through **two
independent bracket-reorder parsers**:
- `load_abp_prose.py` `reorder_bracket()` → `verses.text`
- `build_words_from_abp.py` tokenizer + the reader's `getEnglishOrderWords` → word rows

Where the two reorders diverge, they disagree. The tool FINDS the disagreement; it does NOT by itself
prove which side is right — that's why every family is source-adjudicated (table below). Two directions:
- **word-order (364 live → 208 after a clean build):** the WORDS side is wrong. The 156 stale ones were
  article-fronting (Jer 48:1's 2nd `the`), already fixed in code. The 208 survivors are pronoun/short-word
  mis-slots (see the S9 DIAGNOSIS RESULT block below — all source-adjudicated words-wrong).
- **content-other (13 → 11):** the PROSE side is wrong — `load_abp_prose` leaked order digits (`1let`,
  `4dried`) or a stray Strong's `G` (`AndG.`) on a MALFORMED source bracket. Word rows are clean here.

So "trust `verses.text`" is NOT universal — the 13 prove it can be the wrong side. Each word-order
family is checked against the ABP source before its fix is trusted.

## The reassembly count (31,237 verses, v2 order-aware)
| class | count | meaning | side that's wrong |
|---|---:|---|---|
| word-order | 364 | a real word sits in the wrong slot | WORDS (fix d) |
| punct-position | 261 | a comma / em-dash landed on a neighbor (cosmetic) | frozen allowlist |
| content-other | 13 | `verses.text` carries baked apparatus (`1let`, `AndG.`) | PROSE (fix f) |
| dup-gloss | 0 | — | — |

Spread tracks **book size**, not LXX-renumbered books (renumbering hypothesis is dead). Defects recur in
**phrase-families** — one root cause per family, not 364 unique bugs.

## S9 DIAGNOSIS RESULT (2026-07-05) — the 364 split; (d) re-aimed; (a)/(c)/(d) merged
A fresh full build on PA into `bible.db.new` (Path-C ran — Rahlfs + TAGNT both loaded), then
`audit_reassembly_diff.py bible.db.new --v2`, settled the whole arc:

| class | live (stale db) | fresh build | reading |
|---|---:|---:|---|
| word-order | 364 | **208** | **156 were STALE** — article-fronting; the current build already fixes them. A clean rebuild cures them with ZERO code change. |
| content-other | 13 | **11** | prose-side leaks; 2 cured incidentally, 11 remain = fix (f), untouched by the words rebuild. |
| punct-position | 261 | 261 | unchanged → freeze as allowlist. |

**The 208 SURVIVORS are one family: a personal pronoun / short word packed onto a neighbour's slot** (of
208: I 46, you 29, he 28, it 25, they 21, we 11, + him/she/us/them/your/their; "same" ×7; verb-particle
"up" ×4; a few clause swaps).

**TWO killed suspects — do NOT re-diagnose either (both cost a trace, both wrong):**
- **article-fronting** (`_split_compounds`, the original charter suspect) → it was the *STALE* half of the
  364: the current build already fixes it, a clean rebuild cures the 156 free. Not a code target.
- **the `_split_compounds` carry path** (the second charter suspect) → **RED HERRING: it never fires on the
  208.** Traced 2026-07-05: at `carry=False` the leading-run rule leaves the phrase whole (no split), and
  `carry=True` changes nothing on these shapes. The real splitter is `_redistribute_pronoun_compounds` (see
  (P)). The ~85/`carry=False`/`split_merge_fixes.json` regression is REAL HISTORY (commit 1887f5d) but is
  **NOT the guard for (P)** — it belongs to a pass (P) doesn't touch.

**Source-adjudicated, not prose-diffed (2026-07-05).** v2 only proves the two stores DISAGREE, not which
is right. All 208 survivors were adjudicated against the pinned source feed directly (local, no DB) with an
**INDEPENDENT from-scratch source-order deriver** — a second tokenizer that reads the source's own notation
(non-bracket text verbatim, bracket items ordered by their leading digit), NOT a reuse of
`load_abp_prose.reorder_bracket`, validated on all 5 known cases first. Comparing its word order to the
prose per verse:

| verdict | count | meaning |
|---|---:|---|
| WORDS-WRONG | **208** | independent source word-order == prose; v2 says rows ≠ prose → rows ≠ source |
| PROSE-WRONG | **0** | no survivor has prose deviating from source (no leak, no malformation) |
| AMBIGUOUS | **0** | every source line balanced + distinct digits → order self-determining |

So the prose is source-faithful for the WHOLE survivor set; the word ROWS are the wrong side on every one.
(The pronoun-packed glosses — "I beheld you", "this same thing", "he should deliver him up" — are all
NON-bracket in source, so `clean_verse` copies them verbatim; no parser convention invents an order.) The
rows side itself lives on PA (pronoun families need Path-C), but v2 already established rows ≠ prose, so
prose == source closes it to rows ≠ source without a local rebuild.

**Consequence — (a), (c), (d) are ONE fix.** Path-C pronoun mistags (a), the subject-fold slots (c), and
these 208 (d) are the same mechanism (a pronoun/short word slotted wrong, same carry path, same slots).
Merge the FIX; **keep the audit trail separable** — per-column attribution still holds ((a) writes
`strongs`/`strongs_base`, (d) writes `english`/position), and the batching contract already covers a row
carrying deltas from both.

## The Session-9 job: ONE rebuild, FIVE fixes (was seven; a/c/d merged 2026-07-05)
All remaining doors + the reassembly-diff fixes are rebuild work, so they share **one physical rebuild** —
the discipline is what keeps it safe. **No fix ships alone.** The clean rebuild ALSO cures the 156 stale
article-fronting word-order defects + 2 leaks for free — that's the baseline, not a diff.

**Batching contract (verbatim, non-negotiable):** one physical rebuild, **five separately pre-registered
diffs** — **(P)** the pronoun/short-word slotting fix (MERGES old (a) Path-C fallback + (c) Door-3 subject
folds + (d) build_words carry path — one mechanism, see below), **(b)** `import_tipnr` apply, **(e)** reorder
float adds `)`, **(f)** the 11 digit leaks (Tier B + tolerant `load_abp_prose`), **(g)** phrase-gloss
under-distribution fix (ONLY if the trace confirms it's the same step — else drop to a follow-up).
Each delta must be attributable to exactly one fix. **Attribution stays PER-COLUMN, not per-row — the
merge does NOT merge the audit trail.** Inside (P), a fold slot still takes edits from two sub-mechanisms:
the form→number write touches `strongs`/`strongs_base`, the carry/subject write touches `english`/position.
Pre-register every such row by (row, column) with WHICH sub-mechanism owns each column, exactly as the old
(a)↔(d) binding required. **If any delta can't be pinned to exactly one (fix, column) → fall back to
sequential rebuilds.** A combined diff that comes back as one undifferentiated blob with something
unexplained is stop-condition 2 with no way to localize.

## The five fixes

### (P) pronoun / short-word slotting — MERGES old (a)+(c)+(d); TWO sub-fixes (P1)+(P2)
**The core S9 code fix. Written 2026-07-05, verified against the isolation harness; awaiting the full-build
gate.** The 208 survivors split by mechanism (proven via `enumerate_redistributions.py` overlap: 204 fire on
the pronoun pass, 4 do not):
- **(P1) = 204 verses** — `_redistribute_pronoun_compounds` (traced + reproduced; NOT the `_split_compounds`
  carry path, which never fires — see killed suspects).
- **(P2) = 4 verses** — a spaced-slot-digit bug in `_split_numbered` (Dan 4:1 / Isa 10:23 / Luk 8:28 /
  Pro 3:15). Different pass, registered separately below.

**(P1):** the pass moves a verb bundled onto a pronoun slot to the empty neighbour and **hard-coded the
order: moved verb FIRST (greek_pos 1), kept pronoun SECOND (greek_pos 2).** Right when the pronoun follows
the verb in source; WRONG when it precedes — it flipped them.

Two shapes, one pass (reproduced through the pass + reader port):
- **adjacent-swap** ("his hand" → "hand his", ~38): kept pronoun is contiguous, entirely BEFORE the moved
  word. Fix: order the two bracket slots by SOURCE position (keep-before → keep=gpos1/move=gpos2), instead
  of hard-coding move-first. Preserves Gen 3:15 (keep-after → move=gpos1/keep=gpos2, unchanged).
- **straddle** ("I **beheld** you", "he … deliver **him** up", "this **same** thing", ~170): the pronoun's
  words sit on BOTH sides of the moved verb; one slot can't hold both positions. Fix: **don't split — leave
  the phrase whole on the pronoun slot** (verb slot stays blank). Reads exactly as source/prose. Safe by
  construction (a whole phrase always matches source).

**Design (skip-straddle + source-order):** in `_redistribute_pronoun_compounds`, compute each gloss word's
source index; if kept words straddle the moved run → SKIP; if contiguous → set the two greek_pos by side.
- **Per-column attribution:** the pass "touches english / english_head / greek_pos / bracket_id ONLY —
  never strongs" (its own docstring). So (P) is cleanly the **(d)-type** side (english/greek_pos/bracket_id).
  The **(a)-type** side (`strongs`/`strongs_base`) is Path-C, UNTOUCHED — and this pass only fires on
  post-Path-C numbers (`_PRONOUN_BASES` = 846/4571/… never raw 1473), which IS the (a)↔(d) binding,
  confirmed at the mechanism level. Pre-register any row carrying both a Path-C number delta and a (P)
  english/gpos delta by (row, column).
- **⚠ REGRESSION GUARD (your condition, re-scoped 2026-07-05):** the ~85/`carry=False` set is NOT the guard
  for this fix (wrong pass — see killed suspects). The real control = **every verse
  `_redistribute_pronoun_compounds` currently fires on and gets RIGHT** (the Gen 3:15 class) — must stay
  byte-identical. Enumerated by `scripts/enumerate_redistributions.py` (read-only, PA; obeys the control
  rule — it must FIRE on Gen 3:15 AND Gen 7:1 or it's declared broken). Fix is not trusted until:
  (firings − 208) readings are byte-identical pre/post-fix (plain `diff`) AND the (P1) 204 go to zero. The
  4 (P2) verses are NOT firings, so they're covered by v2 + `--survivors`, not the enumerator diff.
- **Blank-verb-slot pre-registration:** the straddle-skip leaves ~170 verb slots blank-english (their
  natural source state — bare Greek tokens, `parse_abp.py:271`, a shape the corpus already carries in the
  thousands). NOT a new shape, moves NO pinned count (row totals unchanged; coverage reads `english_head`,
  already blank-agnostic) and does NOT collide with the (a) fold census (which keys on the 1473 number; the
  straddle verb keeps its OWN number). Recorded here so the shift is expected, not a surprise finding.

**(P2) — `_split_numbered` spaced-slot-digit fix (4 verses, PRE-REGISTERED to the row).** `_NUM_PIECE`
required the ABP position digit to touch its word (`\d+(?=[A-Za-z])`); the 4 have a SPACE ("3 be
multiplied"), so `_split_numbered` missed the 2nd position and collapsed a shared gloss onto one slot,
mis-ordering the interleaved word. Fix = allow an optional space (`\d+(?=\s*[A-Za-z])`). **A corpus scan
proves the regex splits EXACTLY these 4 chunks and no other in 31,237 verses — but that's a claim about the
SCAN; the BUILD proof is the gate.** Expected full-build delta, per (row, column) — an unexpected 5th change
ANYWHERE is an automatic STOP, not a shrug:

| verse | the one row that splits (strongs, gloss) | → two rows (english / greek_pos) |
|---|---|---|
| Dan 4:1 | G4129 "may  be multiplied" | "may"@1 + "be multiplied"@3 |
| Isa 10:23 | G4932 "is the one rendering concise" | "is the one rendering"@2 + "concise"@4 |
| Luk 8:28 | G928 "that you should torment" | "that you should"@1 + "torment"@3 |
| Pro 3:15 | G514 "equal worth" | "equal"@3 + "worth"@5 |

- **Per-column:** each split rewrites the source row's `english` + `greek_pos` and ADDS one new row (SAME
  `strongs`/`strongs_base`, new `position`/`greek_pos`). **No strongs change** — strongs_base invariant
  untouched. Columns touched: `english`/`english_head`/`greek_pos` + a row insert. Bracket_id unchanged
  (both pieces stay in the existing bracket).
- **Row-count pin moves +4** (626,30N → +4; each split gloss becomes two rows). Re-pinned in the rebuild
  commit after `compare_words`. This is the ONLY (P2) count change; anything else = stop.
- Verified against the live module 2026-07-05: `_split_numbered` now returns the two pieces for all 4;
  the isolation harness reads each verse in source order.

### (b) `import_tipnr` apply — Door 2's fix (code DONE, just re-import)
Fix is committed + dry-run-proven (commit 96bb662): `import_tipnr.parse_tipnr` now types each entity from
its own col-8 ({Place,Male,Female}, identical to entity_resolution) not the block header; raises on an
unrecognized type in a PERSON+PLACE block. `scripts/dryrun_tipnr_typefix.py` (parse-only) is GREEN:
**10** mixed-block places flip person→place (Beth-gader/Eshtemoa/Etam/Gedor/Gibeon/Ir-nahash/Keilah/
Shechem/Tekoa/Zanoah — Judah founder-towns), mirror 0/0, raise both directions. **Pre-registered Door-2
delta = exactly those 10 entities' type change in the `tipnr` table**, nothing else. Just re-run
import_tipnr on the rebuilt copy.

### (c) and (d) — FOLDED into (P) above (2026-07-05)
The old (c) Door-3 passes and (d) build_words slotting are the SAME mechanism as the Path-C pronoun fix,
so they now live in **(P)** above. The diagnosis that merged them:
- **The 364 were two classes.** The **article-fronting** families (forces/Jer 48:1, the-Christ/Mat 16:16)
  were STALE — a fresh isolation build through the whole pass chain reproduces them CORRECTLY, so the live
  db was just old. 156 of the 364 vanish on a clean rebuild, no code. The old "prime suspect
  `_split_compounds` article-fronting" was pointing at the already-fixed part.
- **The 208 survivors are pronoun/short-word mis-slots** — the real code work, now (P). Source-adjudicated
  words-wrong (all 208 balanced+unambiguous in source; pronoun glosses non-bracket = prose copies verbatim).
- **Historical family table (kept for reference; verdicts now settled):**

| family (exemplar) | fresh-build verdict |
|---|---|
| forces (Jer 48:1), the-Christ (Mat 16:16) | STALE — rebuild cures, no code |
| same (Rom 9:17), pronoun-fronting (Gen 7:1), verb-particle (Mat 26:16) | SURVIVE → (P), pronoun carry path |
| paren-edge (Heb 10:8) | fix (e) |
| Mat 21:19 leak | fix (f) |

  (The old ⚠ Mat 26:16 "up he him" exemplar was loose but NOT a typo: the live rows are "he him" on the
  pronoun slot 846 + "should deliver up." on 3860, bracket-reordered to "…deliver up he him". The `he` is
  real — ABP packs it onto the pronoun. Source/prose = "he should deliver him up".)

### (e) reorder float adds `)` — paren-edge
The English-order float (`getEnglishOrderWords` + its Python port `reorder_english.py`, and the chip lift)
moves a trailing clause mark past a reordered group, but only for `. , ; : ! ? ·` — NOT `)`. Heb 10:8
class ("…the law)" renders "…offered) …law"). Add `)` to the float set (shared prose + reader). Small.

### (f) the 11 digit leaks → Tier B + tolerant parser
`load_abp_prose` choked on a MALFORMED source bracket (a `]` with no `[`, Mat 21:19 shape) and leaked the
order digits into `verses.text` ("1let", "4dried") or a stray Strong's `G` ("AndG.", Mal 3:6 `G`). The
fresh build reads **11** (was 13; 2 cured incidentally). Run `dump_family_source.py --scan-brackets` FIRST
to get the full set + confirm the shape. Van der Pool source defect → log each as a **Tier B
`abp_corrections` entry** AND make `load_abp_prose` TOLERATE an unmatched bracket (don't leak). This is
verses.text-side (11 rows), untouched by the words rebuild.

### (g) phrase-gloss under-distribution — CONDITIONAL (trace confirmed the shared gate)
Psa 39:1 "to not sin" parked entirely on G3361 (μή), neighbor G264 (ἁμαρτάνειν) blank — should distribute
(same class as the G846 "jesus 2" finding). `_split_compounds` is the distributor, and the S9 trace
CONFIRMED the (P) survivors live in that same distributor's carry path — so the "one leaky lexicon-evidence
gate misfires both ways" hypothesis is now the leading read. **This class is v2- AND v1-INVISIBLE**
(order- and bag-neutral) → the gate block needs its OWN detector regardless. Ship (g) in THIS rebuild only
if the (P) fix cleanly covers it as one mechanism; else it's a follow-up. Either way the gate block gains
the phrase-gloss detector (below).

### Already LIVE (NOT a rebuild diff)
The chip clause-mark lift fix (the "the word. was God" bug) shipped Session 8 in the frontend — reader
render only, no corpus change. Do not carry it as a diff.

## Dotted-numbers policy — PRE-REGISTERED before the rebuild (standing rule, applied to S9)
CLAUDE.md's dotted-blindness rule (cost two false positives 2026-07-02) governs EVERY census/audit/diff
query in this rebuild. Pinned so no S9 detector re-earns it:
- Any Strong's census/count/detector in S9 operates on the **FULL dotted `strongs`** by default (e.g.
  `G1246.2`). Grouping/counting on `strongs_base` (which strips `.N`) is allowed ONLY with a stated reason.
- Any **"count = 0"** or **"orphan / contaminated rows"** finding MUST check dotted variants BEFORE it
  counts as a finding. A base number saying 0 says NOTHING about its dotted neighbours.
- The (a) form→Strong's table is the **closed, NON-dotted pronoun set** (σου/αυτου/υμων/ημων/…) — it writes
  bare base numbers only; it never touches a dotted slot. Dotted content words (G303.1 ἀνὰ μέσον, G1246.x
  διὰ κενῆς) are OUT of (a)'s scope by construction.
- The reassembly diff ((P)'s carry-path/(f)) is text-vs-text (english order), not Strong's-keyed, so it's
  dot-agnostic — but (P)'s form→number + fold-slot censuses ARE Strong's-keyed and MUST honour the rule above.

## User-facing blast radius (verified — corrects the earlier "self-heal" guess)
`scripts/check_draw_citations.py`: 36 shipped citations quote a flagged verse (1 content-other, 21
word-order, 14 punct-position; all `lexica_def`, draw cache has 1 file). **Render trace:** the Lexica card
renders the verse text **frozen** from `def_json` (`LexicaBody` → `v.text`, 20-shared-components.jsx:195),
copied from `verses.text` at build time (`build_lexica_def.py:295/684`) — NOT a live fetch. So:
- word-order collisions (35) drew from `verses.text`, which is the **correct** side for that class — the
  card already shows good prose. NOT user-facing, no redraw.
- only the content-other case makes `verses.text` itself dirty, and exactly one is cited: **Mat 21:19 in
  the `G1096` entry.** That is the ONLY redraw.
- the main **reader** (chip/prose) DOES render all 364 word-order defects — it reassembles from the word
  rows via `getEnglishOrderWords`. That surface is fixed by the words rebuild, not a redraw.

## The 8-vs-10 explanation (so it doesn't resurface as a phantom conflict)
`import_tipnr`'s twin flips **10** mixed-block places; `entity_resolution` (Session 6) flipped **8**. These
are TWO parsers with different line-skipping strictness legitimately counting different sets — **NOT a stale
doc, NOT a discrepancy**. The Session-8 dry-run's independent line-scan settled it by enumeration (it
couldn't have if either number were hardcoded — which is exactly why the line-scan design was right).

## State entering Session 9
- `cert_invariants.py` 7/7 green; `abp_corrections` 18 rows (pin 18); manifest 75 files. CERTIFIED STATE
  HOLDS — the five fixes are ADDITIVE, gated behind the rebuild's pre-registered diffs.
- **Diagnosis DONE (2026-07-05):** fresh full build on PA + `--v2` diff + local source-adjudication settled
  (d)/(c). The 364 = 156 stale (rebuild cures) + 208 pronoun/short-word survivors (all source-adjudicated
  words-wrong); (a)/(c)/(d) merged into (P). The (P) CODE fix (safe carry path, no ~85 regression) is the
  one piece still to WRITE — everything else is scoped.
- Door 1 CLOSED (census); Door 2 code DONE + proven (not applied); (P) code = the open work.
- **(P) TRACED + WRITTEN 2026-07-05, awaiting the full-build gate:** two sub-fixes in
  `build_words_from_abp.py` — **(P1)** `_redistribute_pronoun_compounds` skip-straddle + source-order (204
  verses) and **(P2)** `_NUM_PIECE` spaced-slot-digit (`\s*`, 4 verses, +4 rows). Both verified against the
  isolation harness; carry path stays killed. Control sets: `enumerate_redistributions.py` firing baseline
  (791, on PA) for (P1); the pre-registered 4-row split table for (P2).
- (e)/(f) scoped, ready; (g) conditional on (P) covering it as one mechanism.
- Reassembly-diff tools committed (READ-ONLY): `audit_reassembly_diff.py` (v1 bag + v2 order-aware,
  `--controls`/`--list`), `reorder_english.py` (+ `tests/test_reorder_port.py`, proven byte-equal to the JS
  on 137 fixtures), `check_draw_citations.py`, `dump_family_source.py` (+ `--scan-brackets` + **`--survivors`**:
  the independent from-scratch source-order deriver that produced the 208/0/0 split; `--survivors --controls`
  proves the detector fires BOTH verdicts — the 5 words-wrong known cases AND the Mat 21:19 prose-wrong case —
  before any zero is trusted; survivor ref list = `AUDIT_reassembly_survivors.txt`),
  `enumerate_redistributions.py` ((P) control set: every `_redistribute_pronoun_compounds` firing + reading,
  Path-C replayed, self-controls on Gen 3:15 + Gen 7:1; PA, read-only).
- After the rebuild+swap: re-run the dependent builders in order (import_tipnr → build_abp_surface →
  build_abp_translit → entity binding → dotted_lexicon → rendering-norm → two-ending), re-pin the invariant
  row counts ONLY in the deliberate-rebuild commit after compare_words passed, and re-run `cert_invariants.py`.

## Gate block (must all pass before the swap)
- `compare_words.py` reviewed (pre-registered per-column diffs only, per the batching contract). For (P)
  the expected diff = **204 (P1) verses' column deltas + Mat 12:14** (`english`/`english_head`/`greek_pos`/
  `bracket_id` on the redistribute rows; Mat 12:14 = the registered content-other overlap, above) **PLUS 4
  (P2) verses' splits** (+4 new rows, `english`/`greek_pos`, no strongs), each attributed. NOT "+4 only".
  Anything outside those sets = stop.
- `cert_invariants.py` 7/7 + `--controls` all fire; row pins re-pinned in the rebuild commit
- L9 split lint = 0
- `tests/test_reorder_port.py` green (the port is the v2 arbiter — prove it FIRST)
- **(P1) firing control set** (re-scoped 2026-07-05): `scripts/enumerate_redistributions.py bible.db.new
  bh_scrape.db` (controls FIRE on Gen 3:15 + Gen 7:1 first) → the readings of every firing (baseline = 791).
  **The straddle branch now `continue`s, so those verses DISAPPEAR from the firing set — the delta is a
  MIX of removed + changed, not modified-in-place.** Pre-registered as a SET invariant (stronger than
  count-matching, which passes even if the wrong verses moved):
  - **added == ∅** — no ref in post-fix that wasn't in baseline.
  - **{removed} ∪ {changed-reading} == the 204 (P1) survivor refs PLUS `Mat 12:14`** (survivors = the 208
    minus the 4 (P2) = `AUDIT_reassembly_survivors.txt` minus Dan 4:1/Isa 10:23/Luk 8:28/Pro 3:15). Every
    one of the 204 must move; nothing else EXCEPT Mat 12:14.
    **Mat 12:14 registered exception (VERIFIED 2026-07-05, run: 185 removed + 20 changed = 205 = 204+1):**
    it's a **content-other** verse (prose leak `theG.`, one of the 11 → fixed by (f)) that ALSO carries a
    pronoun straddle (`they should destroy him`), so v2 bucketed it under content-other, NOT word-order —
    (P1) legitimately fixes its order (removed = straddle-skip). NOT a regression, NOT a v2 word-order gap:
    (P1) fixes the order, (f) fixes the leak, and v2's word-order stays clean for it even in a P-only build
    (order now matches; only the `theG.` differs). The general rule: (P1) touches ALL straddle/keep-before
    firings = the 204 word-order survivors + any verse v2 filed elsewhere that also had the shape; the
    exhaustive set-check proved Mat 12:14 is the ONE such case.
  - partition RULE (not itself the gate): straddle → removed, keep-before → reading changed, keep-after →
    untouched. N (changed) + M (removed) = 204, derived by the check, not pre-guessed.
  PA check: `comm`/`diff` baseline vs post-fix firing refs for removed/added; a keyed reading-compare for
  changed; assert the union equals the 204 set. (The old ~85/`carry=False` set is NOT this guard.)
- **(P2) row-diff** (pre-registered to the row, 2026-07-05): the full-build word-row diff (`compare_words.py`
  bible.db.new-pre vs -post) must show **EXACTLY the 4 splits** in the (P2) table (+4 rows, `english`/
  `greek_pos` on those rows, no strongs) and **nothing else**. An unexpected 5th changed row ANYWHERE = an
  automatic STOP. The corpus scan (regex splits exactly 4 chunks) is the design proof; this diff is the
  BUILD proof.
- **v1 AND v2 reassembly at CRITERION** (`--controls` + `--controls --v2` fire first):
  **zero word-order + zero content-other + NO NEW punct-position.** punct-position stays but is pinned as a
  FROZEN ALLOWLIST — the fresh build cured NONE (still 261), so freeze all 261 as the allowlist; any new
  punct hit fails the gate.
- **phrase-gloss under-distribution detector** (multi-word gloss on a function-word tag + adjacent blank
  content slot) — build read-only, control-test it FIRES on Psa 39:1, drive to an agreed floor. Required in
  the gate whether or not (g) ships this rebuild.
- THEN wire v2 into `cert_invariants.py` as a standing invariant (the word rows and `verses.text` can never
  silently drift again).

## Post-rebuild verifications (after the swap, corpus clean)
- **Redraw only `G1096` (Mat 21:19)** — the single content-other citation. No other draw redraws.
- **Concrete self-heal proof — TWO cards, one per class:** (1) a STALE verse (Jer 48:1 / Mat 16:16) to
  confirm the rebuild-baseline cure, and (2) a (P) SURVIVOR (Gen 7:1 "I beheld you" / Mat 26:16) to confirm
  the carry-path fix. Pull the live reader chip/prose for each and show it now reassembles in source order —
  a real before/after, not a claim. (The frozen Lexica cards were already correct; this confirms the READER
  surface healed.)
- Re-run `cert_invariants.py` 7/7 + `--controls`; v2 wired in reads zero.
- **Secondary render paths need their OWN post-rebuild smoke check (2026-07-05 observation).** The reader
  chip/prose surface is the one we prove healed above — but the Study **topic-page** verse render showed
  DENSE displaced-word artifacts ("said And the LORD", "answered And all the people") on a tonight
  screenshot, far heavier than the ~2% corpus rate. That surface likely reads raw word rows WITHOUT the
  reader's punct-float / bracket-heal pass. After the rebuild, pull a topic page (and any other secondary
  verse-render path — SEO `/read`, xref panel, Study graph verses) and eyeball it the same way, since the
  words rebuild only guarantees the rows, not each surface's reassembly. NOT this session's task to
  investigate — logged for S9 so the smoke net covers more than the main reader.
- **Re-run `dump_family_source.py --survivors --controls`** (control fires first): with v2 at zero
  (rows == prose) AND this confirming prose == source on the survivor set, the 208 went to zero AGAINST
  SOURCE, not merely against prose. This is the control-test half of the source-adjudication — same
  production detector, never a second copy.

## Consolidation layer (added 2026-07-05 when the two docs merged into this charter)
Everything above is the prior canonical handoff verbatim. The items below were folded in from
`AUDIT_reassembly_rebuild.md` (the tool explainer) or resolved fresh during consolidation.

### What the audit tools measure (from the reassembly memo — keep for a fresh reader)
- `scripts/audit_reassembly_diff.py` rebuilds each verse from its word rows and diffs against
  `verses.text`. **v1** = bag-of-words (reorder-immune). **v2** = order-aware, using a Python port of the
  reader's own `getEnglishOrderWords` (`scripts/reorder_english.py`, proven byte-equal to the JS on 137
  fixtures — `tests/test_reorder_port.py`). v2 supersedes v1 and is the count of record. v2 only proves
  the two stores DISAGREE, not which side is right — that's why every family is source-adjudicated.
- Architecture (A) vs (B), for the record: **(A)** keep both builds, fix `build_words` to match
  `load_abp_prose`'s source order, keep v2 as the independent cross-check — **CHOSEN/PINNED**. **(B)**
  derive `verses.text` from the fixed word rows — REJECTED (destroys the independent oracle). See
  "Architecture A — PINNED" above and Out of scope.

### Tooling inventory — all committed (verified 2026-07-05), referenced by path
Read-only unless noted. All present in git:
- `scripts/audit_reassembly_diff.py` — v1 bag + v2 order-aware (`--controls` / `--controls --v2` / `--list`)
- `scripts/reorder_english.py` (+ `tests/test_reorder_port.py`) — the v2 arbiter; prove it green FIRST
- `scripts/check_draw_citations.py` — draw-cache collision checker (the 36-citation blast radius)
- `scripts/dump_family_source.py` — source dump; `--scan-brackets` (the 11 leaks) + `--survivors` (the
  independent from-scratch source-order deriver that produced the 208/0/0 split; `--survivors --controls`
  fires BOTH verdicts before any zero is trusted). Survivor ref list = `AUDIT_reassembly_survivors.txt`.
- `scripts/enumerate_redistributions.py` — (P1) firing control set (self-controls on Gen 3:15 + Gen 7:1)
- `scripts/dryrun_tipnr_typefix.py` — Door-2 parse-only dry-run (the 10-place flip)
- `scripts/cert_invariants.py` — the 7-invariant suite + `--controls` (**note the path: it lives under
  `scripts/`, not repo root** — earlier drafts wrote it bare as `cert_invariants.py`)
- `scripts/compare_words.py` — the per-column word-row diff the gate block reviews

### Bridge: the "seven uncertified build-reorder passes" (original S9 scope) → now inside (P)
The original Session-8 scope listed Door-3 as "seven uncertified build-reorder passes, two banked
known-positive controls." The 2026-07-05 diagnosis folded that work into **(P)**: the passes that
touch pronoun/short-word slotting resolve through `_redistribute_pronoun_compounds`, and their two
banked positives are **Gen 3:15 + Gen 7:1** — the exact self-controls `enumerate_redistributions.py`
must fire on before any zero downstream is trusted. So "certify the seven passes" is executed as
"(P)'s firing-set gate + the enumerator controls," not as a separate door. **⚠ AMBIGUITY for JP to
confirm:** MEMORY.md still lists "Door 3 (7 uncertified passes)" as OPEN and distinct; the handoff
folds it into (P). If any pass-certification work is NOT covered by (P)'s control set, name it before
S9 opens — otherwise this charter treats Door 3 as subsumed by (P).

### Fold-in diagnostic — David / H1732 in the raw TIPNR source (read-only, does NOT gate the rebuild)
Ran while `import_tipnr.py` is on the bench for the (b) twin-bug patch. **RESULT: David is PRESENT in
the source, so he is IMPORTER-DROPPED, not source-absent.**
- His own entity row exists: `tipnr/TIPNR.txt` **line 5451** — `David@Rut.4.17-Rev=H1732`, a normal
  well-formed row (type col = `Male`; parents Jesse + Nahash; full children list; `Tribe of Judah`).
  H1732 appears 45× in the file, mostly as a relative in OTHER rows; line 5451 is David's OWN row.
- This confirms (by name AND by H1732, bases H-prefixed) what memory already recorded: David is absent
  from the built `tipnr_entities` table. Source has him → the importer drops him.
- **Candidate drop signature (UNPROVEN — needs a PA run of the importer):** his ref span
  `Rut.4.17-Rev` crosses into the NT (`-Rev`); worth checking whether the importer's ref/book parse
  chokes on an OT-name row whose span reaches a NT book, and whether that shape matches the 103
  no-metaV bucket. **Cannot be pinned here** (the importer builds against bible.db on PA; CC can't run it).
- **SCOPE FLAG:** diagnosis only. Any fix beyond a trivial importer bug belongs to the
  entity-resolution pass AFTER S9 — it is NOT one of the five S9 fixes and must not be folded into the
  rebuild. Logged here so the post-S9 entity work starts from "in source, importer-dropped, span-into-NT
  candidate," not from zero.

## Standing rules (all inherited, none weakened this session)
Checkpoint rule; CC can't query bible.db (JP runs every query on PA); control-test rule (fire on a known
positive, reuse the production detector never a second copy); new-finding rule; verify-before-sizing;
query-preservation (every ledger count carries its defining query verbatim); loud-fails are the guard
working; corrections are two cells (`strongs` + `strongs_base`); diff joins use `IS` on nullable columns;
dotted-numbers policy (above); DB writes are proposed to JP + run by him on PA after checkpoint approval —
CC never writes bible.db or abp_corrections. Accepted limits, do not re-open: `HEAD_WORD_TAIL_CAVEAT`,
`SPLIT_FUNCWORD_SLOT_CAVEAT`.

**Two rules earned fresh proof-of-value in Session 8:**
- **control-test** — the census control (`grep '^Dan 4:33' pronoun_review.tsv`) had to fire before any zero
  downstream was trusted; and Door-2's dry-run pinned its expectation with an INDEPENDENT line-scan, not the
  parser under test.
- **verify-before-sizing** — the οὗτος lead (Rahlfs `non-pron:3778`) LOOKED like a demonstrative-mistag
  cluster; inspecting the real live cells killed it (divergence-zone noise; the slots were σου/αυτου/names).
  And "abp_surface misaligns ~91%" was a wrong root-cause guess retracted by a 5-cell inspection before it
  hardened in the ledger.

## Closed + certified — DO NOT re-open
L9 · flip class · em-dash class · Cushi · Jer 49:13 · Hab 3:6 · Session-3 swap · Session-4 Cushi binding ·
Session-5 TIPNR pin · L2 · L10 · 97-card label defect · mirror census · check-7 both-directions · L5 (all 9
read) · Luke 23:38 (binder artifact) · **[Session 8] Door 1 census** (cluster, sized; the FIX is queued, the
census is closed) · **[Session 8] the abp_surface "misalignment" scare** (resolved: reliable placement,
words-side fold class) · **Architecture A** (verses.text stays the independent oracle) · the renumbering
hypothesis (dead; spread tracks book size).

## Out of scope
Re-opening anything certified in Sessions 1–8; schema changes to `abp_corrections`; treating the corpus
3,577 as a real count; deriving `verses.text` from the rows (Architecture B); any Lexica feature work. The
queued index memory-file merge is repo hygiene, not audit work.
