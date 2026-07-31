# Ask the corpus — full audit (2026-07-02, read-only)

Decision document from the end-to-end audit of the AI search path (prompts, retrieval,
synthesis, cache, threads, citations, cost, UX). Nothing was fixed in the audit session.
JP approves batches; implementation happens in later scoped sessions (Opus medium unless
marked otherwise). Findings marked OBSERVED were reproduced offline against the exact code
logic; INFERRED were reasoned from code, not reproduced. No live queries were run.

## Banner verdict
"Under construction" comes down after **Batch A + Batch B** ship and their live checks pass
(plus the already-owed #20B acceptance tests 1–5, extended with A's mixed-signal cases).
Nothing beyond B is required — C/D/E are quality, not roughness.

## Findings

| ID | Sev | Effort | Basis | Finding |
|----|-----|--------|-------|---------|
| F1 | P0/P1 | S | OBSERVED | Scope detector collapses mixed signals to the FIRST matching term ([ai.py](ai.py) `_detect_scope` `_first`): "Compare the OT and NT view of the Sabbath" → testament=ot → directive says "cite no NT verses". Both stock suggestions "Compare the OT and NT…" (`_AC_BROAD[1]`) and "Trace X from the OT to the NT" (acScopeSuggestions) trigger it; "greek and hebrew" → Hebrew-only. Repro: both-axes queries return one side. |
| F2 | P1 | S | OBSERVED | Verse-pick parsing (`_VERSE_REF_PARSE_RE` + `_norm_book` title()[:3] fallback) mangles full-name numbered books: "1 John 3:1" → **John 3:1 fetched + displayed as evidence** (mis-attribution); "1 Corinthians"/"Philippians"(→Phi≠Php)/"James"(→Jam≠Jas)/"Song of Solomon" silently dropped. Exposure mostly `additional_verses` (model knowledge, favors full names — `_CURATION_SYSTEM` itself models "1 Jn" style). Fix: parse picks with the books-table regex `_get_verse_ref_re()` (already used for the explanation) or widen `_BOOK_NORM`. |
| F3 | P1 | M | OBS prompt / INF impact | `_AI_SYSTEM_TMPL` describes `strongs_base` as bare + "stored inconsistently" (live invariant: always G/H-prefixed) and its own examples use bare-only filters (`IN ('39','40')`, `= '5207'`, `= '4198'`); the KJV-comparison example joins `'G' || w.strongs_base` = "GG4151", can never match. Models copy examples over rules → zero-row co-occurrence subqueries, masked by the broaden-retry + supplements (thinner pools + wasted ~5s). Header note (ai.py:10-12) knowingly deferred this; it now costs result quality. Fix: rewrite schema section + every example to prefixed single-match; fingerprint auto-busts cache; verify with ~5 canned live queries after deploy (co-occurrence phrase, KJV-comparison, Hebrew word, name, broad theme). |
| F4 | P2 | S | OBSERVED | Scope directive reaches only pass-2; the small-pool path (≤8 verses, pass-1 prose cites no verse) displays pass-1 prose, which never sees the directive → scoped rare-word queries show unscoped prose. Fix: when `_detect_scope` returns anything, always run pass-2. |
| F5 | P2 | M | OBSERVED — **SETTLED-VS-ACTUAL** | **No thread skeleton exists** (the audit brief listed it as shipped; no commit, no code). Actual: frontend sends last-6 "Asked: q / Key words: lemmas" lines (questions only); backend weaves them into terms + SQL-gen prompts only. `_curation_prompt` takes no context — **the displayed synthesis never sees the thread**, so follow-ups can restate and "how does it differ" depends on pass-1's SQL resolving the reference. Fix: pass capped context into the curate prompt + a short don't-restate line (follow-ups are never cached — no cache interaction). Price as NEW work. |
| F6 | P2 | S | OBSERVED | Inspect-rail drill shows raw Strong's definition prose unlabeled ([52-ask-corpus.jsx](static/src/52-ask-corpus.jsx) `target.definition` at AcWordLayer + AcOccurrenceCard; fed from ai.py key_strongs `definition: strongs_def`). Violates plain-meaning rule (reads "grace"-style). Already in TODO (parked A3/A4 rail note). Fix: carry `word_gloss` instead. |
| F7 | P2 | S | INFERRED | A stream that ends with no `done`/`error` frame leaves the turn stuck `streaming:true` → composer locked (`busy`); only New Thread recovers. Fix: client stall timeout → error turn. |
| F8 | P2 | S | INFERRED | Client disconnect mid-stream: tokens spent, answer NOT cached, quota NOT counted (`ai_quota_count` + cache write sit at the generator tail). Decide policy (count up front vs accept user-favoring). |
| F9 | P3 | S | OBSERVED | "O.T."/"N.T." (with periods) never trigger testament scope. |
| F10 | P3 | S | OBSERVED | Known "Greek/Hebrew as topic" false-trigger confirmed rare; "Hebrews" (the book) does NOT trigger (word boundary holds). |
| F11 | P3 | S | OBSERVED | Mid-stream failure shows readers "Internal server error — see console for details" (dev-speak). |
| F12 | P3 | S | INFERRED | Typed Strong's number ("G4442") collides with the prompt rule "never use numbers not in the LSJ block" — behavior untested. |
| F13 | P3 | S | OBSERVED | Follow-up context includes local notice-turns ("you already asked that") as real "Asked:" lines (ctxTurns filter misses `t.local`). |
| F14 | P3 | S | OBSERVED | A pinned Greek-script query still pays terms + LSJ + SQL-gen (~6s + Haiku cost) then overrides the output. Cheap win: short-circuit for pinned queries. |
| F15 | P3 | S | OBSERVED | Pass-1 context preamble says "the previous turn"; frontend sends up to 6. Cosmetic. |
| F16 | P3 | — | INFERRED | Model-named Psalm refs can land one off where ABP versification differs (Psa 24:7 class); thematic flag softens to "Additional references". Belongs to the known corpus-fix item, not this surface. |

## Clean lanes (audited, no findings)
- **Panel/family** (corpus_panel.py): matches the settled discipline exactly; prefix proposer,
  short-root gloss-anchored fallback, deadline watchdog + 250ms lock-wait all correct. Bad/empty
  heads degrade to no panel. ("proto_corpus_panel/proto_family_assembly" in the brief = the
  scripts/ protos; live engine is corpus_panel.py — naming drift only.)
- **Pick-parse floor**: 10 tests cover current formats (scope/skeleton change inputs, not the
  output contract). Citation grade is softer than the definition engine's write-blocker and that
  is CORRECT for a generative surface (strict-cite prompting + thematic flag + frontend seatbelt).
- **Cache/threads**: scope is structurally in the cache key (key = normalized query; detection is
  a pure function of it — no collision path); follow-ups never cached; `_CACHE_CODE_VER`
  discipline documented (at 41); contested re-stamp handles the one known stale class; no
  cross-thread bleed. Cosmetic: cached payloads embed the panel → counts stale after a data
  rebuild until any version bump.

## Cost (lane 6 numbers)
Measured: SQL-gen system ≈ 4.7k tokens (prompt-cached); curate system ≈ 2.8k tokens (NOT cached
— now over Sonnet's 2048 floor, but traffic too sparse for the 5-min window; still not worth it).
Fresh search ≈ 3.5–4.5¢ (Sonnet pass-2 ≈ 75%). Hard ceiling at site cap: 50/day ≈ $66/month;
realistic non-admin spend $6–18/month + unmetered admin use (`grep -F 'cache[' *.log` on PA is
ground truth). Curate input bounded (60 verses × 300 chars) — no creep found.

## Batches (JP approves; implement in scoped sessions)
- **A — Scope & citation correctness** (F1, F2, F13, optionally F9) — S, Opus medium. SHIP FIRST.
  Add mixed-signal cases to the #20B acceptance list (as written, tests 1–5 pass while F1 is broken).
- **B — SQL-gen prompt truth-up** (F3, F12, F15) — M, Opus medium + JP live spot-checks after deploy.
- **C — Thread & synthesis consistency** (F5 context→pass-2 + don't-restate; F4 always-curate-when-
  scoped) — M, Opus medium; agree directive wording first. F4 is one line.
- **D — Rail + failure UX** (F6, F7, F8 policy, F11) — S–M, Opus medium.
- **E — Cost & cache** (Tier 1 filler-strip normalizer importing the scope constants — never strip
  scope words; F14 pinned short-circuit; TODO #4 parallelize cognate+Hebrew loops) — M, Opus medium.
- **Order:** A → deploy + acceptance tests → B → D → C → E.

## Parked-item pricing
- **Tier 2 semantic cache: NO-GO** at current volume (saving < the complexity + scope-collapse risk;
  Tier 1 captures the realistic duplication). Revisit if usage nears the site cap.
- **Hebrew verification strip**: M–L and effectively blocked — needs the Greek↔Hebrew mapping that IS
  the LXX-seam work. Seam first or not at all.
- **Unscoped divergence auto-bridge**: S–M; over-detection risk real; defer until a user misses a
  sheol/hadēs note in the wild.
- **bdb lemma_plain rebuild**: one PA command (JP-run); until then the Hebrew-script exact pin is
  silently inactive (guarded; model path covers). Blocks nothing else here.

## Explicitly NOT recommended (settled — don't re-raise)
Greek-first default + Greek-only unscoped panel heads; weakening the pick-parse floor or the A3/A4
keys-only wall; per-sense panel counts / listing borderline family; caching follow-ups; auto-show
HEB; prompt-caching the curate system at this traffic; verse-marching; moving Ask-corpus toward the
front door; Sonnet→Haiku for pass-2 (reverses the neutrality fix).
