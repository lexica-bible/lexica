# TODO

Open work only. Finished and scrapped items (with the gory details) are in [TODO_ARCHIVE.md](TODO_ARCHIVE.md).

Each item ends with a small `code:` line — that's just a pointer for Claude to find the right
spot. You can skip those lines.

---

## Code health / cleanup

The big rework is finished — all six phases are done and live (see the memory notes
`project_redesign` / `project_architecture_rework`). Done: Strong's plumbing centralized +
the fragile join gone (Phase 1); shared word-building code de-duplicated (Phase 2); the giant
`app.py` split into one tidy file per feature (Phase 3); the front end split up and the word pop-up's
tangle of on/off switches replaced with a "decide once, render simply" model (Phase 4); first-paint
speed-ups (Phase 5); and the person/place database quirk fixed so a shared name keeps both types
(Phase 6). A security pass and a code-health pass also ran (2026-06-07): flood protection added, a
minor info leak closed, dead code removed, an unbounded cache capped, an endpoint hardened.

Still open:

1. **More automated checks (mostly done).** The test net now covers broken pages (snapshot harness) and
   the dangerous data invariants (strongs prefix, tipnr type-set, the build's guards). 2026-06-07 added
   the automation layer: GitHub auto-runs the tests + frontend build-check on every push (CI), a
   pre-commit hook runs the same checks locally, `scripts/deploy.sh` is a one-command tested deploy, and
   Dependabot watches outside packages. The nightly `health_check.py --email --only-warn` email on PA is
   now DONE too (2026-06-16; daily scheduled task at 23:53 UTC, mails only on a real failure).
   Also note (flagged by the 2026-06-10 code read): CI itself auto-runs only the data-invariant
   tests; the endpoint snapshot harness + browser click-through are MANUAL (run against a DB copy
   during dev), so web routes / click behavior aren't checked on every push. That's the main
   test-coverage gap if you ever want to close it.
   `code: scripts/health_check.py, scripts/snapshot_endpoints.py, tests/, .github/, scripts/githooks/, scripts/deploy.sh`
2. **Unify the AI prompt STYLE into one shared "house style" snippet.** (The cache-fingerprint half
   of this item is DONE 2026-06-09 — see TODO_ARCHIVE.md. This is the leftover paired half.) CORRECTED 2026-06-09 (see memory project_ai_synthesis_quality): the original plan — drop sentence-count
   caps and let LENGTH FIT THE CONTENT (adaptive) everywhere — is only right for SONNET. Haiku does NOT
   honor a soft adaptive cap: on a maximal chapter (Sibylline Bk 1) it marched every section and overran
   the token ceiling (got chopped mid-word). New rule: share the VOICE only (plain language, short
   one-idea sentences, no run-ons, no jargon, no moralizing) in one core.py snippet; keep LENGTH control
   split by MODEL — HARD sentence-counts on the Haiku prompts, SOFT adaptive (~Nw ceiling) on the Sonnet
   ones. DONE: xref write-up and chapter summary both moved to adaptive length AND onto Sonnet (33742e8;
   b98517f then 5f38d25); the AI-search xref enrichment is on Sonnet too (21aa95a). STILL OPEN: (a) the
   shared VOICE snippet in core.py was never built — xref/chapter carry their own wording; (b) person/place
   (`_PN_SYSTEM`, Haiku, "1-2 sentences") is CORRECT as a hard cap — leave it, do NOT convert to adaptive;
   (c) LSJ word-study blurb REWRITTEN 2026-06-23 — now a Haiku "definition" prompt (open with the
   meaning; Koine anchor, no book-naming; one short paragraph; the asks were emptied) + per-word
   "Lexica" overrides shown directly. The old 2-3-sentence cap is gone. Full record: memory
   `project_lsj_overrides` (+ the override follow-ups under "New features").
   (d) Book-blurb AUTHOR work DONE 2026-06-13: added the two textually-named scribes (Jeremiah/Baruch,
   Paul/Tertius). Tried folding metaV's traditional names for the anonymous books (Job=Moses etc.) —
   REVERTED: forcing Haiku to name a disputed author made it over-assert. See archive. OPEN, optional:
   1 Peter "by Silvanus" (1Pe 5:12) as a scribe? Debated (scribe vs letter-carrier); left out.
   (e) FRAMING-OVER-PROHIBITION quality pass DONE 2026-06-14 (separate from length/house-style): killed
   three output leaks — LSJ citing Homer/Iliad, "Moses wrote" opening every Pentateuch chapter, and the
   xref write-up self-referencing "these passages"/"thematic thread" — by fixing the FRAME + the worked
   EXAMPLE rather than adding blacklists. LSJ also moved to fingerprint-cache (`_synth_ver`) so it
   self-refreshes like the others; chapter summary's author is now book-blurb-only. Full record: memory
   `project_ai_synthesis_quality` (+ TODO_ARCHIVE). OPEN backstop (only if LSJ still cites Homer once live):
   strip the obvious classical author names out of the LSJ entry text BEFORE the model sees it — no rule,
   just don't feed it. User reviewing live; may follow up in another thread.
   NOTE: changing these prompts is exactly what the
   new fingerprint scheme watches, so each edit will lazily refresh that category's cache (expected).
   `code: shared snippet in core.py; views_crossref.py system prompts; views_metav.py _PN_SYSTEM;
   views_summary.py _SUMMARY_SYSTEM/_*_TMPL; ai.py LSJ prompt in views_lsj.py`
3. **Remove the now-dead ABP "bracket column" CSS.** After the reader's brackets went INLINE (2026-06-16,
   `.lib-iw-brk` inside the chip's english cell) and the Search/Lexicon result lists went prose, nothing
   renders the old bracket-COLUMN classes anymore: `.lib-bracket`, `.lib-bracket-unit`, `.lib-bracket-glyph`,
   `.lib-bracket-trail` (+ the `:first-child` / `:last-child` / `:has(+ .lib-bracket-trail)` rules). Only
   `.lib-bracket-group` (`display:contents`) is still emitted. Safe to delete the rest — grep `static/src/`
   first to confirm no `.jsx` still emits them. Pure tidy-up, low priority. `code: static/styles.css bracket
   section (~line 1956)`
4. **Word study tab folded dotted-different-words into the BASE number — DONE + LIVE 2026-06-21 (commit
   550faa1, user-confirmed working).** The dotted-headword fix already covered the reader card, SEO `/read`, AI
   verse-word context, and Search (per-word via `core.dotted_lexicon_cols`, 2026-06-17). The **Word study /
   Lexicon** tab was the last surface — it grouped AND clicked through by the BASE number. Fixed in
   `views_lexicon.py` via `_abp_strongs_filter` (a full dotted different-word matches its own `w.strongs`; a base
   EXCLUDES `'G'||w.strongs IN dotted_lexicon`), wired into profile/books/verses/english + `_top_glosses_abp`;
   `lexicon_lookup` finds them by lemma; KJV side off + definition from the existing `/api/lsj` abp_ext path.
   Frontend `citedStrongs`/VerseRow highlight the full number; derivation zero-pad stripped (H07676→H7676). Search
   parsing + reader click already carried the full `G###.N` (the fold was 100% backend). Verify after deploy:
   G4521.2 → σαβέκ "thicket" 1× Gen 22:13; G4521 σάββατον drops thicket/glory + count; click σαβέκ → σαβέκ.
   `code: views_lexicon.py, static/src/80-lexicon.jsx, static/src/50-corpus-results.jsx`

---

## Where it's behind vs other Bible apps (2026-06-10 assessment — revisit later)

We play in the FREE serious-study niche — against Blue Letter Bible, STEP Bible, e-Sword, Bible Hub.
NOT Logos (paid library) or YouVersion (reading + social reach); those aren't the target. Honest
gaps, worst-first:

1. ~~**No true Hebrew OT interlinear — the one real scholarly gap.**~~ **BUILT + LIVE + PUBLIC 2026-06-11.**
   Real Hebrew OT word-by-word, right-to-left, all 39 books, from **STEP TAHOT** (CC BY): clean contextual
   glosses + real surface pronunciation + decoded grammar (on the detail card), click → BDB. Own `heb.db`
   (PUBLIC route `views_heb.py`), `scripts/load_hebrew.py`, `renderHebVerse`. The single biggest gap, CLOSED
   and now public for everyone — no login (`hebPickable` gates on `hebAvail`, not the old owner flag). Full
   record: memory `project_hebrew_ot_interlinear`.
2. **Fewer translations** — a handful (ABP/KJV/BSB + owner ESV/NIV) vs BLB's dozens / YouVersion's
   hundreds. Cheap win: add public-domain ones (ASV, YLT, Darby, Geneva) — see "More texts".
3. **No reading plans / devotionals / social.** That's YouVersion's whole world — deliberately NOT
   our target. Chronological reading mode is the closest we have; reading plans could ride on
   accounts later if wanted.
4. **Reach / awareness is the REAL gap — not features.** One-person app on a small box; the feature
   set punches far above that, but almost nobody knows it exists, and each feature is a strong v1,
   not battle-tested at scale. The missing piece is marketing/discoverability, not code.

Deliberate NON-targets (listed so we don't mistake them for gaps): no paid commentary library
(Logos), no social feed (YouVersion), no imposed systematic theology (Berean by design).

---

## Logos base-tier gaps — two real ones (2026-06-16)

We can't touch Logos's full paid library, but on the core word-study loop we already match it — and
beat it on the lexicons (LSJ + BDB are free here, paid add-ons there). Two things their BASE study
tools have that we don't yet. Saved here, NOT being worked — revisit on your own schedule.

1. **Grammar search.** Search the grammar tags themselves — e.g. "show every aorist participle of
   this verb" across the whole text. We already STORE the tags on the words (~78% of ABP Greek, the
   Hebrew OT in full); what's missing is the engine to search them. This is Logos's real muscle at
   every tier, and the single biggest thing between us and their base word-study feel.
   `code: morph column on words + heb_words; needs a new search route + UI`
2. **Dedicated people/places module + timelines.** We HAVE people/places and maps already (metaV —
   the person/place cards, coordinates, the map). What we DON'T have: (a) a dedicated browsable
   module/hub for them (Logos's "Factbook"), instead of cards that only open on a word click, and
   (b) timelines. The "Map tab" idea further down is the maps half; this is the broader
   browse-the-people/places half + a time axis.
   `code: metav_* tables + sidebar (today click-only); see "Map tab" below; memory project_metav_expansion`

---

## New features

- **LSJ "Lexica" overrides — DONE + LIVE 2026-06-23; a few words still open.** The LSJ word-study
  blurb is now a Haiku "definition" prompt for the bulk + per-word hand-written **"Lexica" overrides**
  shown directly (no model call) for the loaded lemmas LSJ leads classical on. 6 seeded (ekklesia,
  leitourgia, βαπτίζω, χάρις/χάριν, λόγος, πνεῦμα). Mechanism + the whole story: memory
  `project_lsj_overrides`. OPEN:
  1. **αἰώνιος G166** override — word the gloss (lead with the age-long sense, "eternal" as one reading
     not the headline) and add one line to `_LSJ_OVERRIDES`.
  2. **δικαιόω G1344** — borderline; decide whether to pin it (chat would, CC cleared it).
     **2026-06-23: #1 and #2 are now folded into the "Lexica dictionary" item below — for a CONTESTED word,
     verse-ground it + run the fairness check; do NOT hand-write an asserting override. HOLD δικαιόω.**
  3. **Strong's-fallback loaded words** (no LSJ entry → raw Strong's def, MORE loaded than LSJ): keep
     Strong's for now, curate later. Plus the deferred preference: for fallback words, show **nothing**
     rather than a DUPLICATE of the headword gloss.
  4. Adding a word later = one line in `_LSJ_OVERRIDES` (no mechanism change). Could grow into a
     curated "Lexica dictionary" over time — the audit method (run Haiku, the loaded word leads with
     Athens/grace, write one line) is sustainable.
  `code: views_lsj.py _LSJ_OVERRIDES/_ovkey + lsj_summary; static/src/30-detail-panel.jsx + 80-lexicon.jsx (Lexica badge); 20-shared-components.jsx LsjBody`

- **Two-tier word entry — Summary = the gloss, Expanded = the EVIDENCE (idea — parked 2026-06-23).**
  Builds on the existing Summary | Full-entry tabs. The governing rule: the summary asserts the meaning;
  the expanded tier only earns its place if it shows the reader something they can CHECK, not more words
  to take on authority. **Anything that makes the reader trust us more is bloat; anything that lets the
  reader verify us is value.** What goes in each tier:
  - **Summary tier** — the gloss as it is now (Koine sense first, plain words, "Lexica"-tagged on overrides).
  - **Expanded tier — three things, all auditable:**
    1. **Render breakdown as PERCENTAGES of the word's own usage**, with the rare senses linked to their
       actual verses — "in this corpus it lands as favor 94%, gratitude 2%, favorable <1%." We already own
       this data (the distribution rail: 243 occurrences, favor 229 / favors 7 / gratitude 5); the move is
       to make it PART of the entry, not a sidebar. Tells the reader how load-bearing each sense really is —
       no published lexicon does this. Highest-value, mostly wiring data we already have.
    2. **One worked-example verse per distinct sense** — the actual line where favor fires, the actual line
       where gratitude fires, inline. Turns a gloss from an assertion into a demonstration. Cheap (pick from
       the occurrences we have); the judgment is which verse cleanest shows each sense.
    3. **A one-line provenance "seam" on the LOADED words ONLY** (χάρις, ekklesia, βαπτίζω — the override
       set) — where the common English gloss came from and why we didn't use it ("commonly rendered 'grace';
       attested range is favor/goodwill/thanks, the theological sense developing later"). This is the Berean
       contribution distilled. RESTRAINT is the value: most words get clean gloss + evidence, full stop; only
       the loaded dozen earn the seam-note. On every word it becomes editorializing noise.
  - **HARD don'ts (this is where "add value" goes wrong — all rebuild the systematic-theology web the method
    rejects):** NO etymology as a headline (root ≠ meaning — the biggest word-study fallacy; bury it in
    Expanded, explicitly labeled history-not-meaning, or leave it out); NO "related theological concepts"
    cross-refs (χάρις → see justification/faith/salvation) — word relationships come from the TEXT (TSK-style
    verse links) not a doctrinal schema; NO our-own commentary on what the word "really means" theologically
    (show the range + usage, the reader does the theology — same humility as the argument graph). The wrong
    value (more glosses, etymology, theological cross-refs, commentary) makes the entry both more complex AND
    less trustworthy; the right value (usage data, worked examples, the labeled seam) makes it richer AND more
    honest because all of it points back to the text. Add depth ONLY along the axis of "let the reader check."
  - **WHERE it goes (2026-06-23):** mostly **Word study**, summary shared.
    - **Summary (gloss)** → BOTH cards (they already share the same `.detail-*`/`.sec` classes).
    - **Expanded evidence (percentages + worked-example verses + seam)** → **Word study tab**, because the
      distribution data is ALREADY on screen there (the rail) — folding it into the entry is mostly wiring
      data that's already loaded. The Library reader card stays the quick in-flow lookup (gloss only); the
      percentages/examples would crowd it, especially the mobile bottom sheet.
    - **The one-line seam on loaded words** → Word study for sure; OPTIONALLY a single line in the Library
      card too (it's small, and the reader meets χάρις etc. in context right there).
    - **CAUTION:** the two cards share LOCKED CSS — any expanded section must be scoped to `.wd` so it can't
      leak into the Library word card (the user's locked it). Another reason the heavy tier lives in Word study.
  `code: views_lsj.py (Summary|Full-entry, _LSJ_OVERRIDES for the seam); static/src/80-lexicon.jsx (distribution data already there) + 30-detail-panel.jsx`

- **"Lexica dictionary" — verse-grounded word definitions (LIVE admin-only on 6 words 2026-06-24; card review + surgical field fixes 2026-06-24/25).**
  Our own word definitions written from the Bible's OWN usage, replacing LSJ's classical glosses as the
  word-card / word-study MEANING source. **ONE engine: verse-ground EVERY def (Sonnet)** — feed the model the
  word's renderings + a spread of its real occurrences, define FROM the usage under the plain-meaning rule.
  **LSJ becomes DISPLAY-ONLY** (full entry behind the toggle, never generative). The size/concreteness ROUTER
  + the cheap LSJ-source path were SCRAPPED: bundled freight (aionios — LSJ leads "lasting for an age, perpetual,
  ETERNAL" in one breath) is uncatchable by ANY compare-to-LSJ check, and LSJ-source only ever helped concrete
  words where verse-grounding gives the same answer. Trial proved psyche / aionios / bread. Full why + the spec:
  memory `project_lexica_dictionary`. Artifact `scripts/trial_lexica_def.py` (`--engine verse` = the final mode;
  the router / bears-out / LSJ-source code in it is the KILLED approach, kept only as the record).
  **BUILT THIS SESSION (2026-06-24, trial rig — commits 8c4777c / 5af239d / 061cd37):**
  - ✅ **Contested-word FAIRNESS GATE** — membership-triggered + MODEL-FREE: a word on the 5-frozen list
    (dikaioō, aionios, charis, sarx, ekklesia) ALWAYS gets a hand-authored fork block appended (no detector,
    no second pass — we distrust the model's fork DETECTION as much as its content; the dikaioō collapse was
    invisible from the output anyway). Surfaces the fork inline; `graph_ref` nullable (links light up per word).
    **dikaioō OFF HOLD** — its 3-way fork shows inline, wired to the live `salvation_how` graph; charis wired to
    `baptism_who`. Data fix: charis fires on G5484, not the textbook stub G5485.
  - ✅ **Citation gate** — audit-time pass (can't break the engine), every cited verse must contain the lemma by
    the Strong's TAG (inflection-proof), misses split TAGGING (data bug — caught via a looser bare-number check)
    vs REAL (hallucination) + no-verse (bad ref / versification drift → REMAP; esp. Psalms, ABP uses Greek/LXX
    numbering). Reproduced psychē 38/38 on PA. (`--audit` was the seed; now the real gate, runs on every word's
    citations; the ref parser caught + fixed a numbered-book bug, 1Jn/1Co were being dropped.)
  **REMAINING:**
  - ✅ **Wire the engine + both gates into the app** — DONE 2026-06-24: `build_lexica_def.py` + the `lexica_def`
    table + `views_lexica.py` + the `LexicaBody` card, LIVE admin-only on the 6 words (`LEXICA_ADMIN_ONLY` flips
    it public). Surgical raw fixes via `scripts/fix_lexica_raw.py`; `MAX_TOKENS` raised 1500→3000 (was truncating).
  - ~~**VERSE_PROMPT sense-count fix**~~ → **DISSOLVED 2026-06-24 — the fix didn't prove out, and that's the finding.**
    A throwaway distribution rig (`scripts/trial_lexica_prompt.py`) ran the live prompt vs a v3 candidate (sub-use
    test reframed on **same-job vs different-job**, symmetric no-over-split/no-over-merge, dropped the "few and broad"
    thumb) N times on psychē, same evidence. v3 is tighter (mode 4 not 5, no format breaks, no hallucinated verses)
    and is FROZEN IN THE RIG, but NOT promoted (live engine untouched). LESSON: **no achievable prompt stabilizes the
    sense STRUCTURE** — the count clusters at 4 but the runs hit it by DIFFERENT senses (appetite leaks back; inner-self
    dropped once), and the count metric can't see that. The citation gate can't either — it PASSED the run missing a
    sense (real verses, dropped sense). Through-line: **every automatic gate sees PRESENCE, not SIGNIFICANCE.** So
    safety isn't a better prompt, it's a REVIEWER. Full record: memory `project_lexica_dictionary` (PROMPT SESSION block).
  - **NEXT (cold start): stand up the AGREEMENT REVIEWER on the 6 pilot words (Plan A, scenario-2).** Build a word a few
    times; **a sense present in SOME draws but absent in others is the flag** (draws voting, no answer key → scales to
    the tail). Trust the engine, IGNORE near-duplicate folds (the life-cluster fold is fine), flag only vanish-or-resurrect
    of a whole sense. Settle hole-vs-fold as a procedure (judge = your eyes via the rig's `--all-headlines`), THEN
    promote v3 + rebuild the six THROUGH the check together (never a blind single-draw rebuild). (Plan B — hand-curate
    sense lists — REJECTED: contradicts "trust the engine," re-imports BDAG-authority, doesn't scale.)
  - **OPEN for Step 4 — the significance judge.** Pure voting sees that something varied, not whether it MATTERS (a real
    hole and a fine fold both vary). Human eyes now; at scale a model pass OR spot-check-is-the-ceiling — unproven either
    way. Same blind spot as the citation gate, one layer up.
  - **Depth-then-compress display:** the card already has Meaning / Full entry / LSJ; the open call is the density
    TRIM (glance vs full — the fork block + grounding verses compress LAST). Pick up after the reviewer above.
  - Follow-up (small, not blocking): the fork gate names a covenant-membership/NPP reading for dikaioō that
    `salvation_how` has no node for — add one to that graph (via add_study_graph_salvation.py) so the link lands.
  - Follow-up (hardening, not blocking — 2026-06-24 card review): the citation gate only sees refs shaped
    `Book ch:vs`. A malformed ref with no chapter:verse (the charis `1Ti—` the model wrote for 1Ti 1:2) is
    INVISIBLE to it — neither pass nor miss, so it slips through silently. Add a lint that flags a book-abbrev
    token in the prose NOT followed by `chapter:verse`. (`cited_refs` / `_REF_RE` in build_lexica_def.py.)
  This SUPERSEDES the αἰώνιος / δικαιόω open items under "LSJ 'Lexica' overrides" above — don't hand-write an
  asserting override for a contested word; verse-ground it + the fork gate. The 6 live overrides stay until this ships.
  `code: scripts/trial_lexica_def.py (spec); future views_lsj.py / a new def side table; static/src/30-detail-panel.jsx + 80-lexicon.jsx; argument graphs in study.db / views_study.py; memory project_lexica_dictionary`

- **"Learn" section — plain-language glossary / FAQ (idea — parked 2026-06-22).** The audience needs no
  Greek/Hebrew training, so a reader who hits H7307 vs H7308, a dotted number, a letter-suffixed
  homograph, or four different per-source counts has no in-app way to make sense of it. Add a "Learn" tab
  (FAQ/accordion, text-first) covering: what a Strong's number is (G vs H); the texts here
  (ABP · KJV · BSB · Hebrew OT) and why their counts differ; Hebrew vs Aramaic (the H7307/H7308 case); why
  some numbers carry a letter (homographs — folded under the base) or a dot (ABP added words — split to
  their own card); what the per-source counts mean; brackets `[ ]` and italics in the text; Word study vs
  Ask the corpus. Mostly WRITING (plain, accurate, Berean) not code. Best built server-rendered like the
  `/read` pages (views_seo.py pattern) so Google indexes "what is a Strong's number" etc. — free
  discovery. Several entries already drafted themselves in the 2026-06-22 chat (Hebrew/Aramaic, homographs,
  dotted, per-source counts). Decide: own tab vs under About; one component vs a server template.
  `code: views_seo.py + templates/seo/ (crawlable pattern), static/src/90-app.jsx (nav/tab), or an About sub-page`

- **"Loaded terms" word-study SERIES — authored content layer (idea — parked 2026-06-22).** Turn the
  propitiation study into a repeatable (e.g. weekly) series. Every entry follows a fixed SEVEN-SLOT
  skeleton (maps onto the standing word-study method):
  1. **Loaded English term + its etymology** — where the freight comes from before any Greek (propitiation
     → Latin *propitiatio*, pagan Roman appeasement).
  2. **Underlying lexeme(s) + Strong's + root** (*hilaskomai* / *hilasmos* / *hilastērion* ← *hileōs*; plus
     the Hebrew it renders, *kipper*).
  3. **Attested semantic range**, theology stripped off.
  4. **THE SEAM** — where the loading entered; the heart of each entry and what makes it a study not a
     dictionary gloss (propitiation: the LXX conscripting *hilask-* to carry *kipper*, object shifting from
     deity to sin).
  5. **Symmetric audit** — the competing replacement gloss held to the same standard, its own motive and
     freight included (expiation, and Dodd's discomfort with wrath).
  6. **Case-by-case usage** — one row per occurrence: verse + grammar + which sense the text forces
     (Heb 2:17 object = sins; Heb 9:5 furniture; Rom 3:25 contested; 1 John initiator problem).
  7. **Most defensible rendering** — the verdict, often "not a single English word."

  CADENCE (the hard part of any series) is largely solved: the lexical work is already done on a stack —
  *charis* (favor, not infused grace), *baptizō* (immerse, medium-neutral), *metanoia* (change of mind),
  *ekklesia* (assembly), *hamartia* (missing the mark) — each slots into the seven frames, so ~6 entries
  are bankable before writing anything new (runway to launch and stay ahead).

  This is a CURATED authored layer, not generated data, so it needs storage the generated word-study path
  doesn't. The note proposed two new tables — `word_study` (slug/title/term/etymology/lexeme_refs/
  semantic_range/seam/symmetric_audit/verdict/publish_date/series_tag) + `study_occurrence` (study_id/
  verse_ref/lexeme_form/sense_analysis/contested). BUT `study.db` already stores authored entries (json
  body + `type` + draft/published `status` — the Study tab's Topics/Graphs), so the real first question is
  **reuse study.db with a new entry type vs. new tables.** Reuses the 3-zone Word-study layout: occurrences
  in the center, verdict/audit in the right card, the series index in the left rail (replacing the
  book-distribution chart on these pages).

  **THE ONE FORK to settle before any schema:** a standalone **Studies** section you navigate to (cleaner
  editorially, better for a subscribe-able weekly drop) vs. a "featured study" overlay that surfaces inside
  Word study when a searched lexeme happens to have one authored (deepens the existing tool, rewards
  exploration). Not exclusive — but whichever is the FRONT DOOR changes the routing and the data model's
  emphasis.
  `code: study.db / views_study.py + static/src/55-study.jsx (authored-entry pattern); static/src/80-lexicon.jsx (3-zone reuse); or new word_study/study_occurrence tables + a Studies route`

- **Ask-corpus DAILY SPEND CAPS + follow-up limits — BUILT + PUSHED (commit c558abd; awaiting deploy).**
  Stops a logged-in user (or the whole site) running up the Anthropic bill on the paid corpus search.
  Per account/UTC-day: user 3 / berean 10 / admin unlimited (admin also NOT counted toward the site total;
  user tier lowered 5→3 on 2026-06-23);
  whole-site ceiling ~50/day ≈ $2 (`AI_SITE_DAILY`); 3 follow-ups per conversation; a repeated question in a
  thread doesn't fire. All server-enforced in `ai_search` before any model runs; counts in notes.db
  `ai_usage`; cached/reopened answers never count. Knobs = `AI_DAILY_LIMITS`/`AI_SITE_DAILY` atop
  views_notes.py. Frontend: composer locks mid-search + "N left today" counter. Full record: memory
  `project_ai_spend_caps`.
  AFTER DEPLOY, verify on a NON-admin throwaway account (admin is exempt + sees no counter): (1) the composer
  shows "3 of 3 left today" and counts down; (2) the 4th question is refused with the "you've used all your
  free searches" notice and NO model call; (3) a 4th follow-up in one thread is blocked ("start a new thread");
  (4) re-asking the same thing in a thread doesn't fire; (5) reopening a saved conversation / a cache-hit
  re-ask does NOT decrement the counter. DONE 2026-06-24: the cap nudge (`.ac-upsell`/`.ac-quota-link`) now
  links **Ko-fi** ("Become a Berean — subscribe on Ko-fi"; was the `bereans@` email on 06-23). Donations are
  now LIVE via Ko-fi and the donate buttons shipped — see the Ko-fi archive entry + memory
  `project_payments_donations`.
  `code: ai.py ai_search; views_notes.py (AI_DAILY_LIMITS/AI_SITE_DAILY, ai_caller/ai_quota_*); static/src/52-ask-corpus.jsx`

- **Ko-fi / Berean upgrades — manual for now (2026-06-24).** Donations are live via Ko-fi (full record in
  TODO_ARCHIVE + memory `project_payments_donations`). Becoming a Berean is a MANUAL admin grant: the
  subscriber emails `bereans@` from their account address → admin flips the role on the Admin page.
  - USER-SIDE owed: set up the monthly **"Berean" membership tier** on Ko-fi + put the claim instructions in
    its welcome message (the cap CTA points people there; without the tier the link still works for one-off tips).
  - OPEN (optional, low priority): a Ko-fi webhook → auto-set the berean role so there's no email-claim step.
  - Berean daily cap stays **10** (`AI_DAILY_LIMITS`); user declined a bump to 15, "revisit later".
  `code: views_notes.py (role grant / AI_DAILY_LIMITS); a new Ko-fi webhook endpoint if automated`

- **Post-deploy spot-checks for recent shipped commits — condensed 2026-06-23.** Detailed "verify after
  deploy" checklists used to sit here for: Ask-corpus + Hebrew word-study fixes; KJV demote + BSB xref;
  BSB-in-Ask-corpus + Hebrew L→R prose; Ask-corpus tuning. The done-records + the exact steps live in
  TODO_ARCHIVE + memories `project_ai_search_architecture` / `project_hebrew_source_swap` /
  `project_hebrew_ot_interlinear` / `project_ai_search_redesign`. ONE genuinely-actionable leftover on PA:
  re-baseline the stale `snapshot_endpoints.py` golden `api__cross-references__Joh__3__16.json` with
  `--update` (field `kjv_text`→`text`, now BSB).

- ~~**Hebrew OT prose mode (parked 2026-06-16).**~~ **DONE 2026-06-22 (fd27b57).** Flavor chosen = the
  interlinear chips flipped LEFT-TO-RIGHT (word order L→R, letters still RTL) — NOT a translit/gloss prose.
  See TODO_ARCHIVE + memory `project_hebrew_ot_interlinear`.

- ~~**Notes feature.**~~ **DONE 2026-06-09** (notes + highlights + bookmarks + accounts). Study
  notes, color highlights, and bookmarks in the Library (drag-select, or a verse-number menu);
  Notes tab with search + filters + sort + collapsible group-by-book + Export/Import backup.
  Browser-local first, with **opt-in accounts (email/password OR Google) for cross-device sync** —
  the first server-write path, in its own `notes.db` (NOT bible.db). See TODO_ARCHIVE + memory
  `project_notes_highlights`. Open follow-ups: word-level highlights in **KJV** (BSB got per-word
  2026-06-15 — see the BSB chip-mode item below), Apple sign-in (if wanted). (Password reset +
  set-password DONE 2026-06-16 via SMTP/Resend; cross-translation highlight paint DONE 2026-06-09.)

- **Notes — next-session follow-ups (one place to start from).** Memory `project_notes_highlights`
  has the full design + gotchas.
  1. ~~**Email / SMTP on PA — PARKED until a custom domain.**~~ **DONE 2026-06-16** — lexica.bible
     landed, so it got built: Resend SMTP via `mailer.py`, password reset + set-password endpoints, and
     the nightly health-check email — all live. Moved to TODO_ARCHIVE; full record memory
     `project_email_smtp`. (Email campaigns / reading-plan mailings remain a future "reach" item.)
  2. **Highlight paint reach** — cross-translation DONE 2026-06-09 (a highlight now shows in ABP/KJV/BSB;
     exact words in its home text, rounds up to whole verse elsewhere). BSB got per-WORD highlights
     2026-06-15 (bsb_words; see the BSB chip-mode item). STILL OPEN (optional, lower value): word-level
     highlights *within* KJV (it still paints whole-verse; kjv_words has positions so the BSB
     `renderBsbVerse` pattern could close it). Also, in
     the new multi-text COMPARE view a highlight paints WHOLE-VERSE in every column (even its home text) —
     intentional for now; exact-word paint in compare would need the column's own translation id threaded
     into `hiForWord` (today it reads the global `translation`, which is "parallel" in compare).
  3. ~~**Small UI follow-ups offered 2026-06-10.**~~ **BOTH DONE 2026-06-10:** (a) the Notes-TAB list now
     shows the per-item type marker (ribbon `Icon.Bookmark` / pencil `Icon.Note` / color dot), matching
     the reader (`.notes-item-type` in 35-notes.jsx); (b) the Library remembers book/chapter (+ translation
     + open non-canon text) across reloads via `localStorage` `lexica.lib.v1`, restoring instead of
     Genesis 1 (a `nav.book` jump still overrides). UPDATE 2026-06-13: order/chrono/compare + the
     chip/prose/Strong's/interlinear toggles now persist AND restore synchronously too — see the
     chronological DONE block below + memory `project_refresh_persistence`.

---

## Library in-text search — eSword-style + find-bar polish, DONE 2026-06-13

The reader's magnifying-glass search got the eSword upgrade: canonical order, "X verses, Y matches",
book range (preset groups + from/to), any/all/phrase (default Any), whole-word/case/exclude, auto
re-run on setting change, and an in-memory result cache. **Find-bar polish + mobile Enter fix DONE
2026-06-13** — on mobile it's now a full-width bar that drops flush under the top tab bar (not a
floating popup; kept top-anchored on purpose, since a bottom sheet would sit under the phone keyboard),
both desktop/mobile slide in, and the on-screen keyboard now DROPS after the search runs (the box +
the Exclude box are each in a tiny `<form>`; the submit handler blurs the input so the soft keyboard
retracts instead of sitting over the results). Full record: memory `project-esword-reference`.
Open:
- Optional, only if first-search latency ever bugs you: a real full-text index (FTS5) for speed —
  but it changes the "match inside a word" behavior (default substring he likes) and needs a one-time
  build on PA. Parked. `code: /api/text-search in views_search.py; panel in static/src/60-library.jsx`

---

## Word click-targets — article/verb wrong-slot cleanup — essentially DONE (2026-06-14…18)
A precision upgrade (which word you land on when you click), NOT a bug — every verse reads correctly.
DONE + LIVE: the "noun behind 'the'" leaks (audit-clean 0, handled by the build's `funcword_subject`
pass); the ἴδιος "own" split (`fix_idios_own.py`, 13 verses); split verbs that wrap the subject
(`_split_numbered` in build_words_from_abp.py, 308 verses, memory `project_verb_split_slots`). Full
records: TODO_ARCHIVE + that memory. LEFT ON PURPOSE (low value): ~25 article-slot adjective/adverb cases
(several defensible Greek, e.g. κατὰ μόνας = "alone") + the 1Co 3:8 second "his own"; and an optional
cosmetic — the split-verb helper half repeats the Greek lemma (hide only if it reads oddly).
`code: scripts/fix_idios_own.py, scripts/audit_funcword_wrongslot.py`

---

## Word study + Ask the corpus — REDESIGNED (2026-06-19, under development)

(Word-card lemma gloss itself — KJV/BSB/Hebrew + Word study + the Hebrew byform fix — is DONE + LIVE
2026-06-23; full record in TODO_ARCHIVE.md + memory `project_word_card_gloss`.)

The Word-study / AI experience was rebuilt to the Claude-design mockups (in `design/`). LIVE but the
header still shows an "Under development" badge on these two tabs. Full record: memory
`project_ai_search_redesign`. What landed (all 4 phases + extras, pushed to master):
- **Ask the corpus** is now its OWN tab (`static/src/52-ask-corpus.jsx`) — AI no longer renders inside
  Word study. Landing + Q&A thread + recent-questions rail; word-scoped handoff from Word study.
- **Word study** is a 3-pane layout (distribution rail / occurrences / word card) in 80-lexicon.jsx.
- New `--ai` steel-blue theme token for the AI accent; `lexicon_profile` now returns `derivation` +
  `related` (cognates, derived on the fly from the lexicon `derivation` text — no extra table).
- Inline citations in AI answers (verse→reader, Strong's→Word study); Hebrew key_strongs chip bug fixed.

**Still open (parked — pick up later):**
1. **Visual fidelity gaps.** Desktop Word study DONE (2026-06-19b). **Mobile Word study REBUILT
   2026-06-19c** to the handoff: icon-only top nav, ONE shared bar height `--bar-h` (48px) for every mobile
   chrome bar, the word card FOLDED onto the Library card's shared `.detail-*`/`.sec` styles (word-study
   tweaks scoped to `.wd` so they can't touch the LOCKED Library card), sheets via `useSwipeToDismiss`,
   `.occ-link` action links steel-blue `--ai`, results filters → underline `.tg` tabs. REMAINING: the
   **Ask the corpus** tab vs its mockup (desktop + mobile). Reference: `design/_mobile_preview/`. Memory
   `project_ai_search_redesign`.
   **Desktop polish 2026-06-20b (DONE, live):** definition always shows (Full-entry toggle removed), the
   occurrences fill the center at Library width, the search bar is left-justified with "Ask AI about <word>"
   moved BESIDE it (out of the card; mobile keeps its Views-sheet "Go deeper"), and result-list gold hugs the
   matched word's `english_head` only — no longer rides onto ABP's glued-in helper words ("is love"→"love",
   "his love"→"love"); the reader is unchanged. WATCH (accepted trade-off): a VERB whose one Greek word
   glosses to several English words ("we should love") now golds only the head in result lists — refine only
   if it bugs you. Full record + the leftover-`setShowDef` crash lesson: memory `project_ai_search_redesign`.
   **Library-mirror shell 2026-06-20c (DONE, live):** desktop Word study now mirrors the Library three-zone
   shell — the right word card floats fixed over the navy header (card head = header height so the divider
   runs unbroken across, empty state too), columns match the Library (224 rail / 460 card), Strong's size
   back to the shared 18px, account pill shifted clear (`.app.view-lexicon .hdr-right`). Dist rail: header
   band height = the search box (lines align), "All books" box removed. **Per-book bar scaling = DEAD END**
   (behind-text shade / sqrt / power all tried; the 46px track is too narrow to read a curve change — user
   deployed each and saw no difference; reverted to the original linear). Memory `project_ai_search_redesign`.
2. **AI curation hard-tune + likely full redesign** — verse selection / "don't spam" / answer shape on
   Ask the corpus. Current = primary/see-all + inline links; adequate, not the end state. Touches ai.py
   prompts + caching. `code: ai.py; memory project_ai_search_architecture`
   - **Thread-style verse list reads spammy (2026-06-20, user-flagged, bigger job):** the evidence verses
     stacked in the chat thread pile up fast. Rework how occurrences are presented in the thread (collapse /
     summarize / cap-with-see-all) so a turn isn't a wall of verses. Part of the answer-shape redesign above.
   - **Cleanup-session plan (2026-06-22) — BUILT + PUSHED (commit 24f3ed3, master; awaiting his deploy/live-verify). Frontend-only, `static/src/52-ask-corpus.jsx` + one CSS rule; `CorpusResults`/Search untouched, no backend change. All 3 below done — memory `project_ai_search_redesign` has the as-built detail. (1) DONE: rail = "Recent conversations", saved to localStorage (last 15), reopen via `setThread` = zero model calls. (2) DONE: see-all dump killed (`showAll` pinned false on the Ask-corpus side); the per-word lemma chips are the Word-study doorways (a single "see in Word study" link was tried + scrapped, dd67baa — one link can't represent a multi-word answer); turns keep only displayed verses + a separate `verified` ref list for the seatbelt. (3) CONFIRMED: primary_cap tiers + buckets map cleanly, no backend change. Original plan kept below for the reasoning:**
     1. **History rail → save & REOPEN whole conversations (not re-run a question).** Today a "Recent
        questions" click calls `ask(h)` (`52-ask-corpus.jsx:287`), which reuses the FOLLOW-UP path: it glues
        the old question onto the current thread AND sends thread context → the backend treats it as a
        follow-up, which is never result-cached → re-runs all 3 models. Confirmed live (ctx=253 on a repeat
        of "Is hell the same as sheol?", models fired again instead of the cached answer). FIX: rail becomes
        "Recent CONVERSATIONS" — one entry per thread (title = first question), click REOPENS the saved turns
        (`setThread` to saved state); nothing re-runs → free + instant, and the bug is moot. "New thread"
        already exists. Browser-local, keep last ~10–15, drop oldest. CHOSEN OVER the cheap interim fix
        (recall = fresh standalone search); skip the interim — this supersedes it.
        **ACCEPTANCE CHECK:** reopening a saved conversation must make ZERO model calls — confirm the
        `cache[…]` log meter stays SILENT on reopen (today a recall fires all 3 calls; the fix should fire
        none). A typed follow-up still re-running is correct (context = a different question, not cached).
     2. **Kill the "see all 156" inline dump.** The 156 = the full VERSE list behind the 12 curated KEY
        PASSAGES. Redundant: the per-word chips already jump to Word study (the real full-occurrence browser —
        distribution + filters), and the synth only samples a few verses, it never needs all 156 shown. DROP
        the inline expand; keep at most a quiet "156 occurrences · see in Word study" link. Bonus: this is
        what makes saving whole conversations (item 1) cheap — ~12 verses/turn instead of 156.
     3. **Re-confirm verse curation maps onto the new capped display BEFORE building it.**
        `_curate_primary_verses` was read 2026-06-22 = consistent with the 2026-06-21 design (spread sample +
        xref-weighted seats + Sonnet pass-2 + citation guard); nothing looked off. Session task: re-confirm the
        primary_cap tiers (8/10/12/15) and the is_primary / is_additional / "other" buckets still map cleanly
        after the recent synth tweaks (Sonnet move, seatbelt, spread, xref weighting). NOTE: the "Additional
        references" block only renders when the AI adds OFF-corpus verses — not on every answer (absent on the
        hadēs/sheol query the user was looking at). `code: ai.py _curate_primary_verses + _CURATION_SYSTEM;
        static/src/52-ask-corpus.jsx; static/src/50-corpus-results.jsx`
4. **Auto-open the top word on an English search** (mockup does it; left as "pick a word"). Small, user's call.
   - **Book distribution now lands on "All books" (DONE 2026-06-20, commit 62f1b48).** A word search no
     longer auto-opens the busiest book + dumps its verses (`_topBook`/`_openTopBook` removed). Trade-off the
     user accepted: the center verse column is then empty ("pick a book"). (Reverted once mid-session by
     mistake, then reapplied — KEEP it.)
     - **Empty-center landing CLOSED 2026-06-24 (commits fbcf6f1 + e7d7ef2).** "All books" now LISTS every
       occurrence across the Bible (new `book="all"` path + `_all_books_verses()` in views_lexicon.py, all
       four sources, `?testament=` filter, capped 6000 w/ `truncated`); the occurrence list pages **50 at a
       time with "See more" (+50)** (`visibleCount` in 80-lexicon.jsx). Book rail / OT-NT tabs / rendering
       chips narrow it. Lazy `VerseRow` keeps it light. `code: views_lexicon.py, static/src/80-lexicon.jsx,
       static/src/00-core.jsx (lexiconVerses testament arg), static/styles.css (.occ-more/.occ-trunc)`
   - **"All" on the Word-study ABP/KJV toggle = PARKED.** Not an oversight: a merged All double-counts the NT
     (ABP + KJV both tag the same NT verses); backend `lexicon_profile` deliberately collapses `corpus=all`.
     Needs a rule for counting the NT before building. Memory `project_ai_search_redesign`.
5. **Ask-the-corpus MOBILE viewport — DONE 2026-06-20 (commit aca7b91).** `.ac` was `100vh - hdr - 56px`
   (overshot the screen → page drifted every direction + a big gap under the pinned input). Now `100dvh -
   --bar-h - safe-top` + `overflow:hidden` (only the inner chat scrolls), `.app.view-corpus .main` bottom pad
   zeroed, safe-area moved onto the composer. Rule: full-screen mobile tab = 100dvh minus the chrome bars,
   never 100vh + a header offset.
6. **Verse-result rows clickable end-to-end — DONE 2026-06-19 (commit 45c7a43).** The whole `.corpus-verse`
   row is now the tap target → clean tap/click jumps to the verse (`onReadInContext`); the ref stays a real
   `<button>` (`stopPropagation`) for keyboard/screen-reader users. Drag-to-select / active text selection
   does NOT jump (move-threshold + `window.getSelection()` guard, `downRef`). Desktop hover (scoped to
   `@media (hover: hover)`) tints the row + lifts the ref to `--accent` + shows the pointer. Covers Search,
   Word study occurrences, and Ask-corpus evidence (shared `VerseRow`).
   NOT done (deliberate): per-word "tap the gold word → study it" — the words in these lists aren't
   individually clickable (model strips per-word click; the row→reader is how you study). Tapping the gold
   word jumps to the verse like the rest of the row. Revisit only if the designer wants the word to open
   Word study directly. `code: static/src/50-corpus-results.jsx, static/styles.css`

7. **Mobile sheet HEIGHT/gap unification (open — needs the user's eye).** 2026-06-19 unified every bottom
   sheet's animation/scrim/chrome + dropped the X on mobile (done — memory `project_mobile_gestures`), but
   the HEIGHTS still differ (detail sheets cap at `100dvh - bar-h` / `- bar-h*2` in library; `.wm-sheet`
   62%/90%; `.msheet` `100dvh - 64px`). They all leave *a* gap but of different sizes. Held off blanket-
   changing heights to avoid regressing the carefully-rebuilt word-study mobile — waiting on the user to
   point at the SPECIFIC sheet whose gap looks wrong, then match it. `code: static/styles.css`

> Note: you revisit these on your own schedule — Claude shouldn't keep pitching them as "next steps."

---

## AI trust + reference depth (2026-06-20 brainstorm — user + outside-Claude review)

A batch of ideas about making the AI prose trustworthy and deepening the free reference shelf.
Ranked: #1 first (cheap, highest-leverage), #2 next (best feature add), #3 is a real wiring job.

1. **AI-prose trust — Ask-corpus path heavily reworked 2026-06-21; the OPEN items below are the
   "corpus tuning" thread handoff.** Retrieval is NOT embeddings — the model writes SQL keyed off
   Strong's, so OCCURRENCE lists come from the DB and can't be wrong; the leak was only in the PROSE.
   SHIPPED this round (full record: memory `project_ai_search_architecture` + `project_ai_search_redesign`):
   - Citation guard: an off-word verse the model names/adds is tagged `is_thematic` → "Additional
     references" (kept, labeled, never primary). Regime-aware (no target word ⇒ no flag).
   - Grounded explanation FOLDED INTO pass-2 (separate pass-3 DELETED — the old perf/cutoff bullets
     here are now moot). Pass-1 prose is written from memory before retrieval (wrong verse numbers
     possible — wrote 2Th 3:3 for 2:3), so the DISPLAYED note is ALWAYS the pass-2 grounded one
     whenever the answer names a verse, even short ones; pass-2 cites ONLY from the real verse list.
   - Honest empty-state: payload `grounded:false` when no real occurrence was found → pale-amber
     "no direct occurrences" caveat on the frontend (`.ac-ungrounded`).
   - NEUTRALITY in BOTH explanation prompts (`_AI_SYSTEM_TMPL` + `_CURATION_SYSTEM`): answer from the
     text, not the question's framing ("same?"/"different?" must match). Killed the parrot-the-framing
     contradiction the user caught on son-of-perdition.
   - Speed: retry is last-resort (only when SQL + cheap fallbacks all empty); pass-2 ranking skipped
     for a small pool that cites no verse; timing instrument left ON (server log).
   - Follow-ups carry the last 6 thread turns (`context` param, woven into term+SQL prompts) + a
     "New thread" reset button (rail). Follow-ups never cache.
   - TRIED + REVERTED: an SQL-prompt "steer" to prefer Strong's co-occurrence over slow `english LIKE`
     phrase scans (commit 15f9606 → revert 487f3fb). It made Haiku botch the co-occurrence SUBQUERY
     (`w.english` referencing the OUTER alias) → 0 rows. LESSON: don't tune SQL CONSTRUCTION blind —
     the real win is a text index, not a prompt nudge.

   SHIPPED 2026-06-21 (cont.) — corpus-tuning thread mostly CLOSED (commits 1b952a4 … 8e2a2b9; full
   record: memory `project_ai_search_architecture`):
   - **Seatbelt — DONE** (frontend): the synthesis prose only LINKS a `Book C:V` actually in the
     retrieved results; an unverified ref the model named renders as plain text. (Chose "don't linkify"
     over grammar-risky stripping.)
   - **Phrase search — DONE in code, not FTS:** a phrase supplement re-runs the AI's own multi-word
     phrases against the FULL verse text (`verses.text` + `kjv_verses`, ~31k rows); a phrase-only query
     SKIPS the 600k gloss scan. Cut "son of perdition" 15→9s. A real FTS index is now OPTIONAL (31k LIKE
     is fast) — keep it parked under "Library in-text search".
   - **Synthesis → SONNET** + the verses fed to it are a SPREAD across books (was OT-only for common
     words) + cross-reference WEIGHTING (each book's hub verse wins its seat). The "say ABP not LXX"
     wording fixed ITSELF once the sample spanned both testaments (data-fix > prompt rule). Proper-noun
     name-scan gated to thin results (a capitalized common word like "Sabbath" was burning ~7s).
   - **No-doctrinal-verdict ban (3c6dbb3 + 7329302):** the write-up was RULING on contested practice
     ("Paul places Sabbath observance among matters of personal conscience rather than binding obligation").
     Added an explicit verdict-ban + GOOD/BAD worked example to `_CURATION_SYSTEM` (the shown pass-2 note)
     and mirrored it into `_AI_SYSTEM_TMPL`. Now reports what each verse SAYS, lets the reader conclude.
     Load-bearing — don't soften. Memory `project_ai_synthesis_quality`.
   - **Same-root cognates fed into the search context (3807228):** the LSJ context block now lists each
     Greek word's parent/child family (reusing `views_lexicon._greek_cognates`, the Word study "related"
     finder) so the model can include relatives it never saw — e.g. σαββατισμός G4520 under σάββατον G4521
     (the Heb 4:9 word a "Sabbath" query was missing). General, no per-word lists. GREEK ONLY (BDB has no
     etymology) and SEMANTIC synonyms still uncovered → both wait on #2 (Trench/Girdlestone). Bumped
     `_CACHE_CODE_VER` 33→34 (the context format isn't in the search fingerprint, so cached rows needed it).
   - **Deterministic cognate supplement + tightening (fea21ef, c0a0bbc):** feeding cognates into the
     context couldn't FORCE the model to search them, so AFTER the SQL runs each GREEK target's same-root
     family is pulled in deterministically — the relative's verses + a chip, only if it actually occurs
     (σαββατισμός G4520/Heb 4:9 under σάββατον). `_cognate_is_tight` keeps stem-initial derivatives, drops
     buried-root drift (εἰλικρινής off κρίνω). Greek only (Hebrew waits on #2). `_CACHE_CODE_VER`→36.
   - **Script out of the synth prose (78d998d):** the note reads in transliteration + Strong's number,
     never raw Greek/Hebrew letters (script stays in the chips). Both prompts. Matches the xref convention.
   - **Contested questions IN SCOPE — don't refuse (04f8a41):** the verdict ban had over-corrected into
     REFUSING "Is the Sabbath still binding?" as out-of-scope (returned no verses). Now: answer, withhold
     only the verdict; never deflect/rephrase. LESSON: a fuzzy boundary reads as "don't touch it" — draw
     it precisely.
   - **Report-don't-characterize + 2 sub-fixes (d743066 + 8721341) — DONE, tested live:** post-verdict the
     synth still CHARACTERIZED ("the sabbath instituted at creation", "Jesus reinterpreted the sabbath").
     Fixed via the FRAME + a GOOD/BAD worked example (the exact Sabbath failure) in `_CURATION_SYSTEM` +
     mirror — NOT a blacklist. Two clean live answers (no characterizing verbs, prose not choppy). Same
     round: a SABBATH-vs-WEEK lexical note (σάββατον = the WEEK in "first/one of the sabbaths" — 1Co 16:2
     etc., overrides ABP's wooden gloss) + a "no what-the-verse-doesn't-do riders" line.
     Memory `project_ai_synthesis_quality`.

   STILL OPEN — corpus-tuning thread:
   - **Label thematic verses in the answer (frontend — formatting session):** a wordless cross-ref (Rom 14:5
     on a Sabbath query — hēmera, no σάββατον) is correctly tagged thematic in the backend, but the
     ask-corpus tab lumps primary + additional into one "KEY PASSAGES" list with no "related" marker, so it
     reads like an occurrence. Give additional/thematic hits a label or sub-group — DON'T drop them (Gen 1:26
     for divine council relies on the same path). `code: static/src/52-ask-corpus.jsx acDisplayedResults; static/src/50-corpus-results.jsx`
   - ~~**Term-pick drags in unrelated words (live 2026-06-22, "giant hunter").**~~ **TRACED + MITIGATED
     2026-06-23 (e1f1713).** A temp diagnostic log proved the cognate EXPANDER is clean — the stray words
     are the MODEL over-reaching in `key_strongs` on a vague question (the "what's the Greek equivalent?"
     follow-up surfaced doorkeeper/burning). Fixed by tightening the `key_strongs` instruction to the word
     + direct equivalents only (reduces, not 100% model noise; a frontend chip relevance-gate was offered +
     DECLINED as over-build for a rare cosmetic thing). The γίγας→γηράσκω "collision" theory was NOT the
     cause. Full record: TODO_ARCHIVE + memory `project_ai_search_redesign`.
   - **Stream verses first** (perceived speed): show matched verses the moment the SQL runs, fill the
     Sonnet write-up in after (~12s of model calls is the floor). Frontend only. DECLINED for now — user
     wants synthesis quality over perceived-speed tricks; pick up only if the wait annoys real users.
     (NOTE: verses are ALREADY capped — Sonnet reads a spread sample of ≤60, shows ≤15; the big `rows=N`
     in the timing log is just the raw found count, it doesn't all reach the model. So this is the only
     real speed lever; tighter caps won't help.)
   - **Ask-corpus RIGHT panel (3-panel parity) — IDEAS parked 2026-06-23.** Word study has 3 panels
     (distribution · verses · word card); Ask-corpus has only the left rail + center. Add a fixed right
     panel. RECOMMENDED = a key-word CARD rail: the answer's lemma chips as full dictionary cards
     (definition, count, "open in Word study"), and clicking a chip focuses it there instead of leaving
     the tab — reuses `/api/lexicon/profile` + the word-card render. Alts: a book-spread "where it lands",
     or follow-up questions + cross-refs. Full record: memory `project_ai_search_redesign`.
     `code: static/src/52-ask-corpus.jsx`
   - **Broad / thematic-topic answers:** sharp on word/phrase queries, thin on broad questions ("how is
     the temple reimagined in the NT") because retrieval is word-based. The bigger answer-shape work.
     User's idea, parked — revisit on his timeline.
   - **Cross-ref weighting picks the GENERAL hub verse, not the query-specific one** (John 3:16 over John
     21 for an agapao/phileo contrast). Sonnet still names the specific anchor from its own knowledge, so
     low priority — sharpen only if it bugs him.
   - **Residual framing lean:** neutrality stopped the flat contradiction, but the two framings still
     close on slightly different emphases. Acceptable; tighten only if it bugs the user.
   - **Answer-shape / curation redesign** is the same thread — see "Word study + Ask the corpus" #2
     (spammy thread verse list + verse-selection tuning).
   - **LSJ word blurb** (views_lsj.py) was NOT given the citation after-check — low risk (sees the
     entry + the one on-screen verse); add only if a bad cite shows up.
   `code: ai.py (_is_thematic + pass-2/grounding block + grounded flag + context param + NEUTRALITY in
   _AI_SYSTEM_TMPL/_CURATION_SYSTEM); static/src/52-ask-corpus.jsx (context, newThread, .ac-ungrounded);
   static/src/50-corpus-results.jsx; views_lsj.py (untouched)`
2. **Feed public-domain reference works into the synthesis engine — the "clean a messy free source into
   prose" move we already do for LSJ/BDB works on the whole pre-1929 shelf.** Best picks:
   - **Trench (NT synonyms) + Girdlestone (OT synonyms)** — the STANDOUT. Grounds the very synonym answers
     the AI was improvising; authoritative, zero license cost. Pairs with #1. (Same-root GREEK cognates are
     already wired into the search — 3807228; the remaining value HERE is SEMANTIC synonyms + the HEBREW
     side, which has no etymology data to walk.)
   - Thayer's, Vine's, Strong's own defs, Gesenius — more lexicon depth, easy adds.
   - PD COMMENTARIES (Matthew Henry, Barnes, Gill, Clarke, JFB, Pulpit) — a "what the tradition says"
     layer, synthesized like LSJ. CAUTION: a commentary layer is IMPORTED interpretation — exactly what
     the Berean text-first rule keeps OUT. Only worth doing walled-off + clearly labeled "tradition, not
     the text" (same provenance discipline as the argument graphs); never let it bleed into the neutral
     answers.
   - LICENSE caution (real — we've been bitten): some old works have free TEXT wrapped in a not-free
     database license (hit us on the morphology sources). Grab original scans / known-free digitizations
     (CCEL, pre-1929 Internet Archive printings, openly-licensed morphology projects), not a random
     repackaging. `code: synthesis pattern in views_lsj.py / ai.py; would need a loader + side table per source`
3. ~~**Swap the OT Hebrew reference from KJV's Strong's tags to the real Hebrew OT (heb.db).**~~ **DONE +
   PUSHED 2026-06-22** (commits aa159eb…13184c9; awaiting deploy). heb.db is now the Hebrew-WORD evidence
   source across Word study + Ask-corpus + SEO /word + the reader rail; BSB added as a 4th word-study source
   (toggles ABP·HEB·KJV·BSB). Verified vs the bridge FIRST (`scripts/compare_heb_source.py`: counts match
   ~99.8%, versification aligns, 150 byform/Aramaic/name numbers fall back to KJV). KJV-as-text untouched.
   The old `/api/search` Search tab was found DEAD (no UI caller) — not switched. Full record: memory
   `project_hebrew_source_swap` + TODO_ARCHIVE. **STILL OPEN (Phase 2 / next session):**
   - **Ask-corpus has NO Hebrew DISPLAY toggle** — evidence is heb.db now but it still SHOWS verses in ABP
     (Greek LXX). Add an ABP/KJV/HEB text toggle to Ask the corpus (`VerseRow` already supports `heb`).
   - The English-word finder's **"All"** view still finds + counts Hebrew via KJV (heb.db only kicks in under
     the new HEB filter); switch All's Hebrew discovery/count to heb.db if the count metric matters.
   - The user has **"small tweaks"** to the new Word-study UI he was holding until everything shipped — collect.

---

## Non-canonical texts — library DONE + LIVE; a few open scraps

The whole non-canonical library is built, loaded, and live: Septuagint Apocrypha, Pseudepigrapha,
and the Testaments of the Twelve Patriarchs (all English-only), plus the 14 Apostolic Fathers with
full Greek interlinear. The full build record — pipeline, sources, per-book quirks, the Didache/Enoch
details, and the lessons learned — lives in memory `project_noncanonical_texts` and TODO_ARCHIVE.
Only the genuinely open items are kept below.
- **Possible NEXT** (not started): Book of Jasher (Moses Samuel 1840 — beware the pseudo-Jasher);
  4 Baruch (Paraleipomena Jeremiou); Apocalypse of Zephaniah; Joseph and Aseneth.
- Headings: most books have section headings (harvested from source); the rest could get hand-written
  ones if wanted (later).

**Open: wire non-canonical texts into the Lexicon + Search tabs.**
The non-canon word panel USED to show an "In the [book]" count + an LXX cross-link, but both were
HIDDEN 2026-06-11 because they dead-ended (`!entry.isExtra` added to abpOcc; the `extraOcc` push
commented out in 30-detail-panel.jsx). The Lexicon/Search tabs only know the Bible corpus. To let
people browse every Didache (or future-book) verse where a word appears, teach those tabs about the
`<book>_words` tables — best done once, generically, as a "non-canonical corpus" option rather than
per book. Re-show those occurrence links here once it's wired.
`code: views_lexicon.py + LexiconView (80-lexicon.jsx); views_search.py + Search (70-search.jsx)`

### KNOWN GAP — Hebrew/Aramaic interlinear for a non-canonical text

The extra-text **interlinear** is hard-wired to Greek: the endpoint joins `lexicon` on a G-number
(`l.strongs_g = w.strongs`), and the reader's word click routes to LSJ. English-only loads are
language-agnostic (Enoch's source is Ge'ez and it loaded fine — we only store English + headings),
so the source language ONLY matters if we want a word-by-word original. For a Hebrew interlinear
(e.g. Ben Sira/Sirach, which has real Hebrew; or Jubilees' Qumran Hebrew fragments) we'd need: BDB
join on H-numbers in `/api/extra`, BDB/Hebrew routing + right-to-left chips in the reader. Not urgent
— no Hebrew non-canonical is queued, and any of them can ship English-only today.

## Detail-rail restyle + chronological views — BOTH DONE (2026-06-14), nothing open
Right-side detail rail + chronological views (Days/Eras/marker/Reading-intro) + the xref panel all share
one design language (navy accent, gold only where it earns a spotlight, tiered badges, subject-title
headers). Full records: memories `project_side_panel_rail` + `project_chronological_tab` + TODO_ARCHIVE.

## Random redesign ideas (2026-06-09 brainstorm — pick any, nothing committed)

Loose look-and-feel ideas, parked here so they're not lost. None are scoped yet — grab whichever appeals.

**Reading experience**
- ~~**Focus mode**~~ — **DONE + LIVE 2026-06-11** (see TODO_ARCHIVE + memory `project_focus_mode`).
  Tap blank space to strip the chrome. Mobile hides everything; desktop darkens the surround and floats
  the text as a centered "book page" with big ‹ › side arrows. Esc/tap exits.
- ~~**Parchment / dark themes**~~ — **DONE + LIVE 2026-06-11** (memory `project_reader_appearance`).
  Light · Sepia · Dark toggle in the reader's Aa menu (desktop) + the mobile reading-options sheet;
  whole-app re-skin via `data-theme` on `<html>`, remembered across reloads. Buttons are now driven by
  `--ctl-bg`/`--ctl-on` vars (add a new button with those, not `#fff`). The navy header stays brand
  navy in every theme.
- ~~**Greek-friendly typography**~~ — **TRIED + SCRAPPED 2026-06-11.** Shipped a reader font picker
  (Cardo/Gentium beside the default Source Serif), then reverted — the alt serifs looked worse than the
  existing Source Serif on Windows, and the reader was already a good serif, so there's no real win.
  Don't re-add a serif picker. See TODO_ARCHIVE + memory `project_reader_appearance`.

**Layout**
- **Word detail as a floating card** — instead of the fixed right sidebar, the lexicon info pops up
  right next to the word you clicked. `code: detail panel in 90-app.jsx (today it's the right sidebar)`
- **Collapsing toolbar** — shrink the desktop lib-bar to one compact pill that expands when you reach
  for it, giving the text more room. `code: lib-bar in 60-library.jsx + styles.css`

**Navigation**
- ~~**Real start screen**~~ — **DECLINED 2026-06-10.** A home/landing sitting between the user and
  the text would repeat BLB's mistake (reading buried behind chrome). Landing straight in the text is
  a feature — keep it. First-time orientation is already covered by the existing tutorial welcome page.
  `code: initial view in 90-app.jsx`
- **Chronological timeline scrubber** — a draggable era timeline across the top of the chronological
  READING MODE (it's a reading mode, NOT a tab) for jumping around the sequence.
  `code: chronological reading-mode UI; memory project_chronological_tab`

**Search**
- **One smart box** — merge the Lexicon and AI search inputs into a single field that detects what you
  typed (Strong's vs Greek vs plain question) and routes it. `code: Search tab inputs in 70-search.jsx`

## Bigger features (someday / ideas)

### Advanced desktop workspace
An opt-in multi-panel layout for wide screens (mobile and normal desktop stay exactly as they are).
Picture: book list on the left, the reading text in the middle, and a right column split into
cross-refs/search/notes on top and the word study (LSJ/BDB/MetaV) on the bottom — all live, no
pop-ups, with draggable dividers that remember their sizes. Full mockup and panel-by-panel spec
kept below.

<details><summary>Full workspace spec</summary>

**Three modes:** Mobile (unchanged) · Desktop basic (unchanged, default) · Desktop advanced
(opt-in toggle in the header, only above ~1100px wide, resizable panels).

```
┌─────────┬──────────────────────────┬────────────────────────┐
│ Books   │                          │  Cross-refs / Search / │
│ (left)  │   Library (center)       │  Notes  (top right)    │
│         │                          ├────────────────────────┤
│         │                          │  Word Study            │
│         │                          │  LSJ / BDB / MetaV     │
│         │                          │  (bottom right)        │
└─────────┴──────────────────────────┴────────────────────────┘
```

- **Left — book/chapter navigator:** always-visible book list (replaces the dropdown); click a book
  to expand its chapters inline (one open at a time); collapsible to reclaim width; on mobile stays
  the current dropdown.
- **Center — Library:** ABP/KJV/Parallel toggle and all current chip/interlinear controls. Word
  click updates the word-study panel in place; verse-number click opens cross-refs in the top-right.
  Chip mode and prose mode (dense, eSword-style inline Strong's superscripts). Parallel mode auto-
  collapses the left nav for width.
- **Top-right — tabs:** Cross-refs (the current TSK panel, today a pop-up) · Search (lexicon + AI
  combined) · Notes (per-verse study notes — future, needs a `notes` table). Default tab: Cross-refs.
- **Bottom-right — word study:** always live, updates on word click; LSJ/BDB/MetaV; replaces the
  pop-up sidebar in this mode.
- **Resizing:** draggable dividers between all panels; sizes saved in the browser.
- **Toggle:** header button switches basic/advanced, remembered in the browser, only shown on wide screens.
</details>

### Highlighting + notes (Logos-style) — DONE 2026-06-09, one paint follow-up open
Notes + highlights + bookmarks LIVE, plus opt-in accounts/sync (see archive + memory
`project_notes_highlights`). Non-canon notes, Notes-tab filters/sort/group, Export/Import all DONE.
- **Cross-translation paint — DONE 2026-06-09.** A highlight made in any text shows in ABP/KJV/BSB:
  exact words in its home text, rounds up to the whole verse elsewhere.
- **Word-level highlights — DONE for ABP + BSB; open for KJV.** BSB got per-word anchoring 2026-06-15
  (`data-note-pos` on its chips, via bsb_words — see the BSB chip-mode item). KJV still anchors the whole
  verse; kjv_words has positions, so the same `renderBsbVerse` pattern could close it.

### Free user accounts — DONE 2026-06-09 (reset added 2026-06-16)
LIVE: email/password + Google sign-in, opt-in, syncing notes across devices via `notes.db`
(see archive + memory). App stays fully usable with no account.
**Account ROLES added 2026-06-11 (LIVE): nologin / user / berean / admin** — `role` column on
notes.db users; ESV/NIV = berean+, Stats + an in-app Admin page (About → Admin) = admin, AI search
= any login. Owner email is always admin. Full record: memory `project_user_roles`.
**Password reset + set-password DONE 2026-06-16** via SMTP/Resend (a Google-only account can now add
a password). Full record: memory `project_email_smtp`.
**Account-panel polish DONE 2026-06-20:** optional display name (`users.name`, shown instead of email),
type-"delete" account removal, header account opens a dropdown in place (no tab jump; plain-text label).
Full record: memory `project_notes_highlights`. STILL OPEN:
- **Apple sign-in** — only if wanted (needs a paid Apple Developer account; heavier than Google).
- Email campaign / reading plans (the original "reach" payoff) — now that mail is proven.

### Mobile reading cockpit redesign — DONE 2026-06-20 (design ZIP handoff)
Five equal-width icon slots `[Search][Play][Abbr Ch][Info][Options]`; book slot shows the 3-letter
abbreviation, right slot is the sliders Icon.Modes. Full record: memory `project_reader_appearance`.
STILL OPEN (small, user's call): switch the cockpit Play/Pause from the filled media icons to thin
outlines to match the mockup exactly — left filled for now.

### Broader AI search — meaning-based passage search
Logos feels "broader" for two reasons: it reads their whole paid library (commentaries, dictionaries),
and it blends exact-word search with meaning-based search. We deliberately stay text-first (bible +
lexicons only), so we won't copy the library part. But we *can* add meaning-based search over the bible
text itself — find verses that are *about* a concept even when they don't use the word — which gives the
"broad" feel while staying inside scripture. `code: Search tab + /api/search; would need a concept index`

### Topic browser
Browse by concept (Atonement, Covenant, Resurrection, Holy Spirit…) as an alternative to AI search —
a good starting point when you don't know what to search. Use an existing topic list only for the
category *names* (renamed to drop loaded framing); generate the actual verses and summaries ourselves,
Berean-style. Build a quick proof-of-concept with the off-the-shelf topic→verse mappings first to see
if people use it, then swap in our own verse selection. Could be a new tab or a mode inside Search.

### Study modules — Study tab (LIVE 2026-06-12/13; **PUBLIC 2026-06-16**; full record: memory project_study_modules)
**Study** tab: Topics (sectioned browse) · **Graphs** (argument maps — added 2026-06-18, REPLACED the old
Denominations/Arguments claim editors). Published Topics + the metaV name-topics are PUBLIC (no login); graphs
+ drafts + all editing stay admin-only. Graphs = a shared claim pool + per-tradition overlays (provenance +
strength tagged), stress-tested by `argmap.py`, drawn as a per-tradition SVG chart; authored via
`add_study_graph.py` (read-only in-app). Earlier this round (all DONE + LIVE, see TODO_ARCHIVE + memory):
two-way study↔reader links; the ~13s→~1s topic-open speedup; the verse-add POST fix; `add_study_topic.py`;
`publish_topics.py --names`.
Baptism graph honesty/fairness pass DONE 2026-06-18 (commits 56d79f7 / f4b8548 / 2e08c87 / 6c582ff /
d536daa; full lessons in memory project_study_modules): trimmed the baptizō lexical sub-argument off the
Berean pledge branch; routed "sealed before baptism" through a contested timing joint (was a false-solid
back-door); split the Berean conclusion into "outward pledge" (stands) + "not the instrument" (the thesis,
depends) so it no longer reads as the lone winner; collapsed the duplicate inference boxes. Two general
fixes came out of it (both live on a code deploy, no `--apply`): the chart now packs disconnected branches
(no dead gap), and the "where they part" diff lists each side's conclusion nodes.
OPEN:
- **Unpublish the imported Nave's/Torrey's CONCEPT topics (2026-06-24, user's call) — PENDING his PA run.**
  He wants the MetaV-imported concept topics OUT of the public Topics list (recycled topical-index content,
  not his text-first voice; argument graphs + Lexica dictionary + hand-authored studies are the real value).
  KEEP: person/place name-topics (`metavn_`) + hand-authored topics (Divine Council). Tooling shipped:
  `publish_topics.py --imported` (+ `--dry-run`), commit 91e13be — hides ONLY `metav_` concepts (drops them to
  admin-only DRAFT, NOT deleted; undo = `--imported`). HE runs on PA: `git pull` →
  `publish_topics.py --unpublish --imported --dry-run` (eyeball the list) → `--unpublish --imported` → touch
  the wsgi. Full record: memory project_study_modules.
- **Mobile graph = narrate a traversal, not a shrunk 2D chart (design note, 2026-06-20; LOW urgency —
  graphs are admin-only).** The shared-claim-pool + per-tradition-overlay structure means the graph is
  just one rendering of the data. On a phone, walk the same nodes vertically as argument STEPS (grounded
  verses → the inference they feed → the contested joint → the conclusion + "where they part"), so
  vertical position means "next step" instead of fighting the 2D layout. Alt: horizontal scroll with the
  conclusion column PINNED preserves the "converges to a conclusion" feel. HARDEST thing to preserve:
  the CONTESTED edges — if dashed lines vanish or read solid at phone density, the map quietly becomes
  the verdict machine we avoid. On mobile carry "contested" as an explicit colored TAG/label, not fine
  dashes. `code: static/src/55-study.jsx graph SVG render; memory project_study_modules`
- Drop the place "Sin" entry (Sin (1)/(2) — one is the Wilderness of Sin) from the `_COMMON` list.
- **Foundational-words strip / lexeme panel (NEW, 2026-06-18).** The baptizō "medium-neutral" insight was
  trimmed out of the baptism graph on the understanding it belongs in a per-study foundational-words strip
  (a lexical fact about the key word the argument turns on). That strip is SPECCED but NOT BUILT — until it
  exists the insight is dropped from the UI. Build the strip (and a Strong's deep-link from it / from a graph
  lexeme node, which folds in the deferred item below).
- Graph CUT 2: undercut scoring + the graph "In studies" verse back-reference are DONE 2026-06-18
  (objections score on a grounded+solid bar → knockout/overturned; graphs feed `for_verse`, admin-gated).
  STILL deferred: an in-app graph editor (user DECLINED — he authors via the script through CC) + a React
  Flow drag canvas + a **Strong's deep-link from a graph node** (a lexicon claim like baptizō/G907 should
  open the Lexicon tab on click; today graph boxes only deep-link verse refs to the reader, 2026-06-18).
`code: argmap.py + views_study.py + static/src/55-study.jsx; scripts/{add_study_topic,add_study_graph,load_study_topics,generate_topic_intros,publish_topics,find_topics,find_topic_dupes,merge_the_dupes}.py; memory project_study_modules`

### Let study results shape AI search answers — divine council is the test case (idea, 2026-06-17)
AI search is deliberately neutral — text first, no imported theology. But for ONE topic, the divine
council, we've already hand-wired the answer in code: `ai.py` carries a fixed list of ~20 verses
(`_DIVINE_COUNCIL_VERSES`), a trigger-phrase matcher (`_DIVINE_COUNCIL_RE`), and a fixed set of 6
Greek/Hebrew word chips (`dc_strongs`). When a question matches, those verses are forced into the
results as "primary" no matter what the AI's own search found. Every line of it is specific to divine
council — a true one-off.

We ALSO already have a hand-authored "Divine Council" study TOPIC in `study.db` (via
`add_study_topic.py`) carrying the SAME verse list (plus Psalm 58:1). So the same curated answer
lives in two places — which is exactly what makes this a clean test.

The idea: have AI search notice when a question matches a published study topic, pull that topic's
verses straight from the study, and force them in as primary — exactly what the hardcode does now, but
driven by the study instead of by code. Prove it on divine council, confirm it matches today's
behavior, then DELETE the one-off. The payoff: it generalizes — any topic you author later shapes
search the same way, with zero new code per topic.

What the divine-council study would need to gain to fully retire the hardcode:
- **Trigger phrases.** Today the code's narrow regex decides when to fire ("divine council",
  "heavenly assembly", "bene elohim"…). A study only has its title. Add a small list of match phrases
  to a topic (or match the question against the title + an aliases field).
- **The 6 word chips.** The study has verses + section headings but not the Strong's word list the
  card shows. Either add a key-terms field to a topic, or pull the chips from the verses' own words.

GUARDRAIL (the Berean rule): only PUBLISHED, text-first TOPICS may feed an answer — NOT denominations
or arguments, which take sides on purpose. Divine council is a topic, so it qualifies.

One practical note: answers get saved and reused. If a study feeds an answer, the saved-answer key has
to include that study's verse list, or editing the study later wouldn't refresh the saved answer.
`code: ai.py (_DIVINE_COUNCIL_VERSES / _DIVINE_COUNCIL_RE / dc_strongs — the one-off to delete);
scripts/add_study_topic.py + study.db topic; views_study.py (read a topic's verses); memory
project_study_modules + project_ai_search_architecture`

### Chronological reading mode + 365-day plan — DONE + LIVE (2026-06-09…13)
Reading-ORDER toggle (Canonical | Chronological), any version; static `chronological.json` (1,102
passages, 13 eras; `scripts/chronological/build_chronological.py`, no DB); exact-range trims + spans
chapters; every passage shows a chapter heading with verse range (`withMarks`). 365-day "Days" plan
(`Eras|Days` toggle; `58-dayplan.jsx`, click-to-check, per-text progress `lexica.plan.v1`, follows your
spot). Refresh-persistence of order/position/compare/toggles (synchronous, no flash). DECIDED: keep the
source's verse-level interleaving. Full records: memories `project_chronological_tab` +
`project_refresh_persistence`. DEFERRED (user "looks good for now"): account-sync of plan progress; a
stitched single-scroll "today's reading"; deeper per-tab last-state + within-chapter scroll persistence.

**Daily "Reading intro" panel — DONE + LIVE 2026-06-13** (restyled to the rail; the xref panel was matched
in the 2026-06-14 rail pass). ESV-style per-reading card (mobile = the ⓘ sheet): AI Berean title+summary +
the era's dated timeline + the day's passages. Backend `views_chrono.py` (`GET /api/chrono/intro/<day>`,
Haiku, cached category `chrono`); frontend `59-dayintro.jsx`. Dates are APPROXIMATE "c." on purpose. Full
record: memory `project_chronological_tab`. PHASE 2 (deferred): exact hand-curated per-reading dates;
sub-eras (Saul/David/Solomon) finer timelines; milestone labels ON the timeline track (v1 lists them below).

**Mobile toolbar reload "flash":** FONT half FIXED (Google-Fonts `display=swap`→`display=optional`, commit
1164e5f — KEEP it). CHRONO half DEFERRED (low value): the button shows the canonical label for one beat
before `chronological.json` loads; if ever wanted, cache `curPassage.label` in `lexica.lib.v1` and show it
until chrono loads. `code: templates/index.html (fonts); 60-library.jsx .mbar-loc + curPassage`

### Read-along audio — DONE + LIVE (BSB + KJV public, ESV owner-only)
Per-chapter audio on KJV/BSB/ESV (ABP has none): BSB public openbible.com mp3s, KJV public
audiotreasure.com (both hotlinked, no key), ESV via Crossway's own API (`ESV_API_TOKEN`, FCBH NT-only
fallback). Play/pause icon + draggable scrubber; mobile docks at the bottom above the cockpit and is
scroll-aware in chrono (auto-advances). Per WHOLE chapter (no per-verse timing). Full record: memory
`project_esv_audio` + TODO_ARCHIVE. STILL OPEN: a **dramatized** KJV (multi-voice FCBH — rides the same
pending Bible Brain key as ESV; self-hosting archive.org copies is off the table, FCBH owns it);
**verse-by-verse karaoke** (needs per-verse timing — parked).
`code: views_bsb.bsb_audio + views_esv.esv_audio; audio player in 60-library.jsx`

### Map tab
Biblical geography as its own tab. Three angles: follow the current chapter and show its places;
search a place and pin every verse that mentions it; or a free-explore world map where clicking a
city opens the MetaV sidebar. The neat version ties maps to the text (e.g. plot every place in Paul's
letters across his journeys) — nobody does this well. Coordinates and the map library are already in
place for the existing place sidebar, so this is smaller than it looks.

### More texts + word grammar (morphology)
- **Word grammar everywhere:** plain-English part-of-speech/tense/case per word. **DONE for the Hebrew OT**
  (2026-06-11, via STEP TAHOT — shown on the detail card; `decode_morph` in load_hebrew.py) and partly for
  ABP Greek (~78% morph). Could extend to fuller Greek coverage (CATSS for the LXX OT, macula-greek for the
  NT). **The ABP-native morph fill was INVESTIGATED + SCRAPPED 2026-06-15** (memory `project_abp_morph_gap`):
  the real gap is ~70k inflected OT words — the other ~65k missing-morph are proper names + indeclinables, both
  correctly blank — and the only ABP-keyed source is Van der Pool's *Analytical Lexicon*, a $5 426-page PDF
  (extraction + nom/acc ambiguity), not worth it for a side-panel detail. STEPBible's **ABGk/abpgrk** isn't an
  upgrade either (same ABP text; single-dot accent, no breathing, no inline morph; Van der Pool copyright, not
  CC-BY). `code: morph column on words; decode_morph in scripts/load_hebrew.py`
- **Textus Receptus Greek NT:** add as a second NT text next to ABP. Same Strong's numbering, so it
  plugs in easily, and showing where the two Greek texts differ is genuinely rare and useful.
- **Multi-text COMPARE — DONE + LIVE 2026-06-10** (memory `project_pericopes_parallel`). The old 2-column
  "Parallel" is now a picker for **2–4 of ABP/KJV/BSB/ESV/NIV** side by side (desktop columns, mobile stacked
  labeled lines); notes/highlights shared across columns. This is the vehicle for comparison texts.
- **More English translations** (ASV, YLT, Darby, Geneva) — all public domain; would slot straight into
  the Compare picker as new toggles + their own loader/db (like BSB). Not started.
- **BSB chip mode + Strong's — DONE + LIVE 2026-06-15.** Loaded on PA: 386,063 words / 381,948 Strong's /
  66 books (dry-run rebuilt bsb_verses exactly — 31,047 exact + 55 spacing-only + 0 mismatch). `bsb_words` +
  `bsb_strongs` (mirror `kjv_words`/`kjv_strongs`) built from the Berean Bible project's Strong's-tagged
  tables (`bereanbible.com/bsb_tables.tsv`, public domain) by `scripts/load_bsb_words.py` (one-time PA load,
  has a `--dry-run` gate). Word endpoints in `views_bsb.py` (chapter-with-words, verse, verse_words,
  strongs-count); chip wiring + word-level highlights in `static/src/59c-library-render.jsx`
  (`renderBsbVerse`) + `60-library.jsx` (BSB un-prose-locked, `bsbWordMode`) + `30-detail-panel.jsx`
  (`isBsb` path). Chip mode + clickable word study + per-word highlights all landed together (BSB anchors
  per word like ABP; cross-text notes round up to whole-verse). Memory `project_bsb_words`. NOTE: closes the
  KJV/BSB word-level-highlight gap FOR BSB only — KJV still anchors whole-verse (kjv_words has positions, so
  the same `renderBsbVerse` pattern could enable KJV word-level later if wanted).
- **Inflected-form side-card line — DONE + LIVE for Hebrew + BSB + ABP 2026-06-15 (KJV impossible).** Moved to
  [TODO_ARCHIVE.md](TODO_ARCHIVE.md) with the full trail. Two follow-ups it left behind, both PARKED:
- ~~**ABP surface TRANSLIT — PARKED.**~~ **DONE + SHIPPED 2026-06-15.** The ABP "in this verse" line now carries
  a romanization like Hebrew/BSB. Built `scripts/build_abp_translit.py` — NOT the feared throwaway map: a proper
  Greek→Latin romanizer matched to the lexicon's own SBL headword style (keeps accents, eta→ē / omega→ō, ch/th/ph,
  rough breathing→h read from the dictionary form, initial rho→rh, upsilon y-vs-u), tested on real words. Fills
  `abp_surface.translit` (348,935 forms) read-only; re-run after a position-shifting rebuild. Full trail:
  TODO_ARCHIVE + memory `project_bsb_words`. (transliteration-search can reuse this converter later.)
  code: scripts/build_abp_translit.py
- **Parsed Greek OT as a 2nd parallel text — PARKED idea (NOT ABP's surface line).** A CATSS-lineage Rahlfs LXX
  (Eliran Wong's LXX-Rahlfs-1935 is most turnkey — surface + lemma + morph + SBL translit already paired, 100%
  native, no alignment guessing) would be its OWN parallel Greek OT alongside ABP (like ESV / the Hebrew),
  NOT a patch to ABP's number; its translit covers THAT text, not ABP's. LICENSING FLAG: CATSS/CCAT is NOT MIT
  (user-declaration requirement) — read the downstream repo's terms before shipping in a donation-taking app.
  code: new views_* + own db, modeled on views_heb
- **ESV — PERSONAL, LOGIN-GATED — DONE + LIVE 2026-06-10** (memory `project_esv_audio`). Owner-only ESV
  reader, server-gated via the shared `views_notes.is_owner()` (`OWNER_EMAIL` live; toggle shows for the
  owner). Text LOADED on PA (`load_esv.py` → `esv.db` = 31,104 verses, all 66 books). ESV AUDIO now
  LIVE too (2026-06-13, `ESV_API_TOKEN` set — see audio item). Nothing open here.
- **NIV — PERSONAL, OWNER-ONLY — DONE + LIVE 2026-06-10** (memory `project_esv_audio`). Mirrors ESV exactly:
  `views_niv.py`, own `niv.db`, NIV toggle. TEXT-ONLY (FCBH has no NIV audio). Loaded by `scripts/load_niv.py
  ~/Bible-niv ~/bible-db/niv.db` from aruljohn/Bible-niv. No WSGI change needed.
- **Extra-biblical texts** referenced in scripture (1 Enoch, cited in Jude; Dead Sea Scrolls variants)
  as a separate "Apocrypha" section, never mixed into the canon. Research good digital sources first.

### Dead Sea Scrolls — wanted, but the hardest one (why it's still not done)
Deliberately skipped so far, not an oversight. The blockers are real:
- **No public-domain English exists.** The readable translations everyone cites (Vermes,
  Wise-Abegg-Cook, García Martínez) are all modern and copyrighted — nothing free to drop in the way
  Charles/Lightfoot/Brenton were. What IS free is photos + academic transcriptions (Leon Levy digital
  library), not a ready-to-read English text.
- **The scrolls are mostly Hebrew/Aramaic fragments** — broken, gap-ridden, not a clean verse-by-verse
  book. And our interlinear is wired for Greek (G-numbers); a Hebrew original-language view needs the
  BDB / H-number / right-to-left plumbing flagged as the known gap above.
- **The realistic angle isn't "another book to read" — it's a compare view.** The Great Isaiah Scroll
  (1QIsaa) is complete and famous, and its value is showing WHERE it differs from the standard Hebrew
  (Masoretic) text. That's a side-by-side "variants vs the MT" feature, bigger and different from the
  apocrypha plumbing. Best first step if/when we tackle it. `code: would need a clean PD/licensed
  transcription + a verse-aligned variant layer, not the load_extra path`
