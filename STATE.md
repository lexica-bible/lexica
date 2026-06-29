# LEXICA — CURRENT STATE (ground truth)

Reference snapshot for an external reviewer who knows the project history but needs
present facts. Pulled from the repo, not memory. Database row counts are flagged
`[PA]` (the live databases are PythonAnywhere-only and not in git). Every item is
marked **LIVE / PARKED / NOT BUILT**; items where the truth differs from what an older
session would assume are flagged ⚠️.

Last refreshed: 2026-06-28 (repo tip at write time: `e10c1c6`).

---

## 1. STACK & LAYOUT
- **Backend** Flask + SQLite; **frontend** React 18 UMD, JSX in `static/src/*.jsx` → Babel → `static/app.js` (committed). **Host** PythonAnywhere, live at **www.lexica.bible** ⚠️ (the old `appssanding720.pythonanywhere.com` base now 404s).
- **Repo** `bible-db` (GitHub `lexica-bible/lexica`, public).
- **Databases** (PA-only, none in git):
  - `bible.db` — ABP words/verses, KJV, BSB, lexicons (`lexicon`/`lsj`/`bdb`/`abp_ext`), `cross_references` (TSK), `metav_*`, side tables (`word_gloss`, `lexica_def`, `dotted_lexicon`, `abp_surface`, `pn_binding`, `tipnr_entities`/`_refs`, `pericopes`), non-canon `<book>_words`/`_verses`.
  - `notes.db` — accounts/roles, notes/highlights/journals, `visits`, `password_resets`, `corpus`, `ai_usage`.
  - `study.db` — authored Study entries (topics + argument graphs). **The one irreplaceable file** (no rebuild script).
  - `heb.db` — **public** Hebrew OT interlinear (STEP TAHOT), OT-only.
  - `esv.db` / `niv.db` — berean-gated texts. `news.db` — admin news tool. `bh_scrape.db` — ABP scrape source.
- **Backend modules**: `core.py`, `ai.py`, `structural.py`, `entity_resolution.py`, `argmap.py`, + 19 `views_*.py` blueprints.
- **Frontend**: 22 `static/src/*.jsx` (00-core … 90-app). Key: `30-detail-panel` (word card), `60-library` (reader), `80-lexicon` (Word study), `52-ask-corpus` (AI), `55-study`, `20-shared-components` (LexicaBody / LsjBody / StructuralBody).
- **Backups**: `scripts/backup_db.py` — daily PA task 13:30 UTC, verified rotating backups → `~/db_backups`.

## 2. REFERENCE WORKS

**Word dictionaries**
- **LSJ** (`lsj`) — **LIVE, display-only.** "Full entry" toggle; Haiku "definition" blurb; **6 hand-written "Lexica" overrides** (`_LSJ_OVERRIDES`, views_lsj.py:72): ἐκκλησία, λειτουργία, βαπτίζω, χάρις, λόγος, πνεῦμα. αἰώνιος/δικαιόω overrides **HELD** (superseded by the Lexica dictionary fork).
- **BDB** (`bdb`) — **LIVE** (Hebrew word cards).
- **Strong's** (`lexicon` Greek / `bdb` Hebrew) — **LIVE** (lemma join key `lexicon.strongs_g`).
- **Dodson / TBESG / TBESH** — **LIVE**, baked into the `word_gloss` side table (the plain-meaning line on every word card + Word study). Not separate live tables.
- **"Lexica" overrides** — **LIVE** (the 6 above).
- **Verse-grounded Lexica dictionary** (`lexica_def`) — **LIVE + PUBLIC** (see §3).

**Cross-ref / people-places**
- **TSK** (`cross_references`, 386,518 rows) — **LIVE** (verse-number cross-ref panel: Haiku pick → Sonnet synthesis).
- **MetaV + TIPNR** — **LIVE** (see §6).
- **Study tab** (`study.db`) — **LIVE** (topics public, graphs admin-only).

**Reading texts** — all **LIVE**: ABP (primary), KJV, BSB (all word-level Strong's/chips), **Hebrew OT** (public, OT-only), **ESV** + **NIV** (berean-gated).

**Named in code but NOT loaded** ⚠️
- **MM (Moulton-Milligan)** — **NOT BUILT.** Was a single stray word in a `structural.py` comment, scrubbed 2026-06-28 (commit `3c062ed`). No table, no data, never wired.
- Trench/Girdlestone, Thayer's, Vine's, Gesenius, PD commentaries — **NOT BUILT** (TODO ideas only).

## 3. DEFINITION ENGINE (Lexica dictionary)
- **Gate `LEXICA_ADMIN_ONLY = False`** (views_lexica.py:25) — ⚠️ **PUBLIC since 2026-06-25**, served to everyone incl. logged-out. A word with no entry 404s → normal LSJ card.
- **How many / which** — **~18–20 live** per project notes; **authoritative list = `lexica_def` on PA** `[PA: SELECT strongs FROM lexica_def]`. Code names the **6 PILOT** (`PILOT`, build_lexica_def.py:38 — psyche G5590, dikaioō G1344, charis G5484, aionios G166, sarx G4561, ekklesia G1577) + batch-1 nouns (logos G3056, Christos G5547, pneuma G4151, …) + theos G2316 / kyrios G2962.
- **Pipeline (as it runs):** evidence gather → **sampler** `select_spread` (BUDGET = **40** occurrences) → **engine** Sonnet `claude-sonnet-4-6` on `VERSE_PROMPT` (MAX_TOKENS **3000**) → **splitter** `split_definition` (SPLIT_VER "split2") → **citation gate** (every cited verse must contain the lemma by Strong's tag; audit-time) → **fork append** from `CONTESTED` (membership-triggered, **model-free**) → **`pin_core`** lifts the neutral core to `pinned_core` (lead) for frame-leakers → **`sense_provenance`** LXX flag (≥80% OT AND ≥4 OT refs; no model).
- **VERSE_PROMPT — FROZEN** (v3, promoted 2026-06-25; build_lexica_def.py:64). Synced with `lexica_agreement.V3_PROMPT`. **Not re-proven since promotion**; the agreement reviewer is a prompt-stability gate and is **optional per run** now the prompt is diff-locked — the `--apply` citation gate guards a written entry.
- **Fairness-gate fork-words LIVE (9 in `CONTESTED`):**

| Strong's | lemma | pin_core | frames | graph_ref |
|---|---|---|---|---|
| G1344 | dikaioō | yes | forensic (Reformation) / infused (Trent) / covenant-membership (NPP) | **salvation_how** (live) |
| G166 | aionios | yes | unending duration / of-the-coming-age (qualitative) | none |
| G5484 (alias G5485) | charis | yes | unmerited favor by faith (Reformed) / infused grace (sacramental) | **baptism_who** (live) |
| G4561 | sarx | no | embodied humanity / sin-principle | none |
| G1577 | ekklesia | no | local / universal / institutional | none |
| G4151 | pneuma | yes | divine person (Nicene) / mode (modalist) / power (Unitarian) — divine-Spirit use only | none |
| G2316 | theos | no | shared nature (Harner) / identity (modalist) / subordinate god (Arian) — John 1:1c only | none |
| G2962 | kyrios | no | shared identity / delegated lordship / one-Lord-manifested — YHWH-title-transfer set only | none |

⚠️ **theos + kyrios forked 2026-06-27** (membership-only, no pin_core) — newer than most session memory.

## 4. STRUCTURAL / GRAMMAR CARDS (`structural.py`, `STRUCTURAL_ADMIN_ONLY = False` = PUBLIC)
All entries **LIVE**, provenance `GRAMMAR`, verse lines verbatim ABP. **Inventory COMPLETE — 46 lemmas:**
- **Copula** εἰμί (G1510) + ~7,800 dotted conjugates (decoded to a parse, not separate entries).
- **17 prepositions** διά, κατά, μετά, περί, ὑπέρ, ὑπό, ἐπί, παρά, ἐν, εἰς, ἐκ, ἀπό, πρό, σύν, ἀντί, ἀνά, πρός.
- **Conjunctions** typology ὅτι/ὡς/εἰ + ἐάν + 12 connectives (καί, δέ, γάρ, οὖν, ἀλλά, μέν, ὥστε, ὅτε, ὅπως, διό, ἤ, τε).
- **ἵνα** (G2443) — purpose; result/ekbatic debate flagged as a **grammatical** contest (`scope_contested`), glance/full; exemplar Mark 3:14.
- **Particles** ἄν (G302, underspecification finding), δή (G1211), γε (G1065).
- **Negatives** οὐ (G3756) / μή (G3361) mechanism cut, both with the Matt 5:17 minimal-pair cross-ref; compounds οὐδέ, μηδέ, οὔτε, μήτε, οὐχί (each names base + twin).
- **Article** ὁ (G3588) — definite-marker + substantivizer + "not English 'the'" finding.
- **Idiom** ἀνὰ μέσον (G303.1) in `_IDIOMS`, one-line content note (`kind:"idiom"`).
- **PARKED / NOT BUILT:**
  - **Demonstrative/pronoun "referent" card** ("step b": touto, autos, ὁ δέ, ἰδού, οὐδείς, μηδείς) — **NOT BUILT** (ὁ's pronominal straddle points to it).
  - **ἵνα's hardening argument-graph (Isaiah 6)** + the 3 verse-pointers (Mark 4:12 / Matt 13:13ff / John 12:40) — **NOT BUILT.**

## 5. ARGUMENT GRAPHS (`study.db`, admin-only in-app)
- **Referenced live in code:** `salvation_how` (dikaioō fork link), `baptism_who` (charis fork link).
- **Authoring scripts:** `add_study_graph.py` (Baptism graph), `add_study_graph_salvation.py` (`GRAPH_ID = "salvation_how"`, `--apply` writes published).
- **Actual published set = `study.db` on PA** `[PA: SELECT title FROM entries WHERE type='graph']`. Baptism graph had an honesty/fairness pass (2026-06-18). Stress-tested by `argmap.py` (grounded-claim reachability + load-bearing-joint + overturn).
- **Status:** salvation_how + baptism_who = **LIVE** (referenced + scripts present).

## 6. ENTITY RESOLUTION (proper nouns) — LIVE
- A PN click first calls `GET /api/metav/entity/<name>?book=&chapter=&verse=` (views_metav.py:265) → `pn_binding` (render=1) for the verse-correct TIPNR entity.
- **Bound** → leads the rail with a sourced `.pnbound` card (canonical name + TIPNR description + kin + region + "Matched to this verse" badge) + **one** occurrence control keyed to the entity's own number, **only for the active reading text** (ABP count via `?by=base`, since these carry bare `strongs='*'`). A bind **gates** the whole name-based metaV fetch.
- **404 (unbound)** → old name-path + **Fix A** floor (Haiku 1–2-sentence verse-scoped description), byte-same, deploy-safe.
- **Engine** `entity_resolution.py` (pure logic); tables built by `scripts/build_entity_binding.py --apply`. **Re-run after any words rebuild.**
- **Counts:** ~14,817 binds, zero confident-wrong `[PA: SELECT count(*) FROM pn_binding WHERE render=1]`.
- **Enrichment state:** map pin stays **hidden** on an ambiguous bound place (e.g. Eden) — **Fix A's guard working, not a bug.** OT names key to **Hebrew** on purpose (TIPNR's Greek form G9827 isn't in our lexicon); **no "pure-Greek re-key"** path. The old TIPNR "Appears N×" ref-list was **removed** (real occurrence controls supersede it).

## 7. OPEN / PARKED

**Definition-engine deploy run** (prompt fix → rare-word gate → cutoff → batch-build → public):
- Prompt fix (v3 promote) — **DONE.**
- Agreement gate (`lexica_agreement.py`) — **BUILT + PROVEN**; reviewer run now optional.
- LXX-provenance cutoff (80% / min-4) — **LIVE** but **tuned on ~18 words; re-check at scale = OPEN** (`audit_lxx_provenance.py`).
- Batch-1 build (12 nouns) — **DONE.** Public flip — **DONE.**
- **Batch-2 pre-sort / pipeline driver — NOT BUILT** (scoped only: sort a G-list into 3 tiers by freq + fork-membership + polysemy + loaded-referent). Verbs + Hebrew first-batches — **NOT BUILT.**
- **Step-4 "significance judge"** — **NOT BUILT.**
- **No-verse lint** (malformed ref with no chapter:verse slips the citation gate) — **NOT BUILT.**

**Corpus-tag fixes flagged by the reviewer** ⚠️ **NOT BUILT** (no fix script exists; the G166/G165 hits in `build_word_gloss.py` are gloss definitions, not corrections):
- **Jer 49:13 G166→G165** (aionios vs aion mis-tag) — **NOT BUILT.** `[PA: verify the live words tag]`
- **Psa 24:7 numbering** — **NOT BUILT.** `[PA: verify]`
- Both need a scoped, dry-run-first fix script + re-verify.

**PN enrichment** — bound cards lacking maps/info ride Fix A; broader people/places **browse hub + timelines** = **NOT BUILT.**

**Other open:**
- **Grammar search** (search the morph tags) — **NOT BUILT.**
- Wire non-canon texts into Word study / Lexicon occurrence lookups — **PARKED.**
- Ask-corpus Hebrew **display** toggle + right-panel parity + thematic-verse labeling — **PARKED.**
- Snapshot golden **re-baseline** — ran `--update` 2026-06-28; commit `tests/snapshots` to close.
- KJV word-level highlights (BSB/ABP done) — **PARKED.**
- Unpublished Nave's/Torrey's concept topics — already drafted/hidden; physical delete from `study.db` = optional, **NOT done.**
