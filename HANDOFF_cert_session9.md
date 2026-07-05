# ABP Corpus Certification — Session 9 handoff (CANONICAL S9 charter)

**Seat: HIGH from the start.** Session 9 *is* the rebuild session — the whole point is a full
words rebuild carrying FIVE fixes at once (was seven; the old a/c/d merged into (P) 2026-07-05 after the
diagnosis landed). Don't open it on the low/medium census seat.

**This is the SINGLE canonical S9 charter — the one source of truth.** It now fully absorbs the
reassembly-diff arc (findings, adjudication, rebuild plan) that used to live in
`AUDIT_reassembly_rebuild.md`. That file is **SUPERSEDED** (kept for its raw diagnosis history only;
its header points here). Everything you need to run the rebuild is in THIS file.

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

**The charter's old prime suspect was BACKWARDS.** "`_split_compounds` article-fronting" was the *stale*
part (already fixed, cured free by rebuild). The 208 SURVIVORS are one different family: a **personal
pronoun / short word packed onto a neighbour's slot** (of 208: I 46, you 29, he 28, it 25, they 21, we 11,
+ him/she/us/them/your/their; "same" ×7; verb-particle "up" ×4; a few clause swaps). This is the
`_split_compounds` **carry path** — the branch the code deliberately keeps OFF (`carry=False`) because
turning it on regresses ~85 other verses (its own comment).

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

### (P) pronoun / short-word slotting — MERGES old (a)+(c)+(d) (one mechanism)
**The core S9 code fix.** A personal pronoun or short word (I/you/he/it/they/we/…, "same", possessives,
verb-particle "up") is packed onto a neighbour's slot; the prose splits + orders it right, `build_words`
does not. **208 verses survive a clean build** (source-adjudicated words-wrong, every one — see the S9
DIAGNOSIS RESULT block), on top of the Path-C pronoun mistags (Daniel ≥170) and the Door-3 subject folds.
All the same slots, same `_split_compounds` carry path.

- **Root:** `_split_compounds` keeps its carry branch OFF (`carry=False`) because turning it on regresses
  ~85 OTHER verses (article/copula garbles the leaky lexicon gate can't avoid — its own comment). The 208
  are what `carry=False` leaves unfixed. The fix is to make the carry path SAFE (target the pronoun/
  short-word case without the article/copula over-reach), not to flip the flag.
- **⚠ REGRESSION GUARD (your condition, 2026-07-05):** the fix must PROVE it doesn't break the ~85 that
  `carry=False` currently protects. Build a control set of those ~85 verses FIRST (their correct order,
  pinned), and the fix is not trusted until it leaves all ~85 clean AND drives the 208 to zero. This is a
  named gate item below.
- **Path-C sub-part (old (a)):** where Rahlfs can't align, read the number off `abp_surface`'s form (closed
  pronoun set σου→4675, αυτου→846, υμων→5216, ημων→2257,…). Per-slot sanity gate: only write where the
  form-class fits the slot's english (or english is blank/fold), else skip + log. Blank-form slots (Dan
  4:33 kind) carry no form → stay source-app reads. Do NOT trust the corpus 3,577 as a target — it's VOID
  (real mistags + fold companions, proportions unknown); the per-slot pass produces the real split.
- **Door-3 sub-part (old (c)):** the 7 uncertified reorder passes (`_split_numbered`,
  `_redistribute_pronoun_compounds`, `_fix_backwards_pairing`, `_split_pn_article_lump`,
  `_funcword_noun_relocate`, `_lord_subject_split`, `_lord_oath_fix`) are the fold-slot producers. Two
  durable known-positives for the census control (must FIRE before any zero is trusted): `Num 20:9 pos 2`
  (Μωυσής, blank english, 1473) and `1Sa 18:6 pos 8` (Δαυίδ, blank english, 1473). Full-verse dump query:
  `SELECT …, w.position, w.english, w.strongs, w.bracket_id, s.form FROM words w JOIN verses v … LEFT JOIN
  abp_surface s ON s.verse_id=w.verse_id AND s.position=w.position WHERE (book,ch,vs)=… ORDER BY w.position;`
- **Per-column attribution inside (P):** form→number write = `strongs`/`strongs_base`; carry/subject write
  = `english`/position. Pre-register each fold row's two columns to their sub-mechanism.

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
- (e)/(f) scoped, ready; (g) conditional on (P) covering it as one mechanism.
- Reassembly-diff tools committed (READ-ONLY): `audit_reassembly_diff.py` (v1 bag + v2 order-aware,
  `--controls`/`--list`), `reorder_english.py` (+ `tests/test_reorder_port.py`, proven byte-equal to the JS
  on 137 fixtures), `check_draw_citations.py`, `dump_family_source.py` (+ `--scan-brackets` + **`--survivors`**:
  the independent from-scratch source-order deriver that produced the 208/0/0 split; `--survivors --controls`
  proves the detector fires BOTH verdicts — the 5 words-wrong known cases AND the Mat 21:19 prose-wrong case —
  before any zero is trusted; survivor ref list = `AUDIT_reassembly_survivors.txt`).
- After the rebuild+swap: re-run the dependent builders in order (import_tipnr → build_abp_surface →
  build_abp_translit → entity binding → dotted_lexicon → rendering-norm → two-ending), re-pin the invariant
  row counts ONLY in the deliberate-rebuild commit after compare_words passed, and re-run `cert_invariants.py`.

## Gate block (must all pass before the swap)
- `compare_words.py` reviewed (pre-registered per-column diffs only, per the batching contract)
- `cert_invariants.py` 7/7 + `--controls` all fire; row pins re-pinned in the rebuild commit
- L9 split lint = 0
- `tests/test_reorder_port.py` green (the port is the v2 arbiter — prove it FIRST)
- **(P) ~85-regression control set** (your condition, 2026-07-05): pin the correct order of the ~85 verses
  `carry=False` currently protects; the (P) fix must leave ALL ~85 clean AND drive the 208 to zero. Not
  trusted until both hold — build this control set BEFORE writing the carry fix.
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
- **Re-run `dump_family_source.py --survivors --controls`** (control fires first): with v2 at zero
  (rows == prose) AND this confirming prose == source on the survivor set, the 208 went to zero AGAINST
  SOURCE, not merely against prose. This is the control-test half of the source-adjudication — same
  production detector, never a second copy.

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
