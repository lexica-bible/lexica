# Candidate-3 sizing — Hebrew retirement rebuild (G4 pre-work, enumerated from code)

Opened 2026-07-25 on the reviewer's go, under the G3 Option-B ruling and its
conditions. Every site below was found by grep and read at the cited lines in the
working tree (post-G2, commit ed28b2ff) — enumerated from code, not assumed.
No code changed. Standing constraints on record: changed builder → trial-then-apply,
roster gate, own backup + pre-rebuild known-good kept, unfindability count gate.

## 1. Affected row classes (the rebuild's write set, from the stage-1 identity table)

| Class | Rows | words.strongs_base today | After retirement |
|---|---|---|---|
| abp-tag | 3,518 | already the Greek number | UNCHANGED (no-op — the rebuild must prove this, not assume it) |
| tipnr | 10,731 | Hebrew stopgap (H90…) | the served Greek number — real G or STEP G9xxx |
| lemma-only | 14,850 | Hebrew stopgap | CLEARED per Option B (see C3-Q2 below for the cleared value) |
| none | 3,380 | Hebrew stopgap | **OPEN — C3-Q1, reviewer ruling needed** |
| (all classes) | 32,479 | — | Hebrew number moves to the Q2 cross-ref home |

**New fact surfaced by this sizing (changes the join math):** after retirement,
`words.strongs_base` will hold STEP-extended G9xxx values for most tipnr rows. The
core lexicon join `l.strongs_g = w.strongs_base` misses G9xxx → NULL lemma — so
every feed that joins `lexicon` needs the `step_lexicon` COALESCE (design layer 3
predicted this; the sizing confirms exactly where — class A below). G9xxx also
passes the strongs_base GLOB invariant (starts with 'G') — the invariant check
stays valid unchanged.

## 2. Must-touch list (serving sites, enumerated)

**A. Library feeds — views_library.py**
- Verse feed `:61–92` + chapter feed `:228–276`: `LEFT JOIN lexicon l ON
  l.strongs_g = w.strongs_base` (`:68`, `:237`) misses G9xxx → add the
  step_lexicon COALESCE (same pattern as dotted_lexicon).
- `LEFT JOIN tipnr t ON t.strongs = w.strongs_base` (`:70`, `:239`): the `tipnr`
  table keys HEBREW numbers; post-retirement the join matches nothing for tipnr-
  class rows → PN type badges lost unless the join goes through the Q2 home (or
  import_tipnr also writes Greek keys into `tipnr`).
- The `g_id` feed field + `READER_GREEK_FLIPS` gating: post-retirement the tag
  fallback prints Greek from strongs_base even with the switch OFF — the G5
  switch-semantics change, record not fix.

**B. Word study — views_lexicon.py**
- `_abp_strongs_filter` `:291+` — carries the G4-MUST-TOUCH marker (`:324`): the
  pn_greek_identity union + peek become redundant for numbered rows (base
  predicate serves G9xxx natively post-retirement); repoint/retire per charter.
- The SAME predicate serves H-number profiles (Hebrew words' ABP branch,
  `_abp_book_counts` :1163ish, gloss rows, verse lists): after retirement an
  H-key query over `words` returns ZERO ABP PN rows → the H-number "ABP
  occurrences" path must read the Q2 home instead. This is the biggest
  unfindability surface (feeds the S2-Q4 "nothing findable becomes unfindable"
  gate).
- Profile step_lexicon fallback + STEP tag: already live from G2, unchanged.

**C. Identity endpoints — views_metav.py**
- `:542–556 /api/strongs-count/<n>?by=base` — the H-keyed ABP count for
  backfilled PNs (the card's old Hebrew ABP line + frontend `abpBaseCount`)
  returns 0 post-retirement → Q2-home repoint.
- `:625–631 hebrew_count` in `_greek_identity_payload` — counts
  `words.strongs_base = <H>`; silently zeroes post-retirement (the §6 collision
  from the evidence pass) → Q2-home repoint. Note `pn_greek_identity.hebrew_base`
  itself still serves the cross-ref NUMBER correctly (frozen snapshot).
- `:114 pn_count` (english_head where strongs_base='*') — affected by C3-Q2's
  cleared-value choice (see below).

**D. SEO pages — views_seo.py**
- `:516`, `:546`, `:581` — H-number /word pages list ABP refs by base → lose PN
  rows post-retirement (Q4-note said mixed-keyed SEO is tolerated; now it's not
  mixed, it's MISSING → repoint via Q2 home or accept with a ruling).
- `:632` enumerates `strongs_base LIKE 'G%'` for the page list → G9xxx numbers
  ENTER the SEO surface (new /word/G9xxx pages; their lemma needs step_lexicon).

**E. Ask-corpus / AI — ai.py**
- Mechanism is value-agnostic (serves whatever strongs_base holds), but two
  classes need touching: (1) Hebrew-keyed ABP evidence pulls for OT names
  (e.g. `:2167`, `:2255` area) stop matching PN rows → same Q2 class as B/C;
  (2) `_AI_SYSTEM_TMPL` documents strongs_base semantics to the SQL model
  (`:76–101`) — needs a factual update. ⚠ Prompt edit = cache refresh for its
  category + the no-regression memory rule applies.

**F. Shared serializers — core.py**
- `word_gloss_cols` `:438` — `wgb.strongs = strongs_base`: Hebrew word_gloss
  entries (H-keys) stop resolving for retired rows; Greek/STEP gloss needs the
  step_lexicon or Q2 path. Marginal for names but enumerated.

**G. Frontend (45 H-prefix checks across 3 files — behavior flips BY DATA)**
- `30-detail-panel.jsx` (30 hits): `isHebrewWord = entry.strongs.startsWith("H")`
  and everything keyed on it (BDB section, heb/kjv/bsb count lines) flips off for
  retired rows — mostly the INTENDED demotion, but each branch gets verified at
  build time, not assumed (the G5 re-receipt covers the visible result).
- `59c-library-render.jsx` (9): tag fallback + `pnClickPayload`/`clickable`
  gates read strongs_base — see C3-Q2: the cleared value decides whether
  14,850 words stay clickable.
- `80-lexicon.jsx` (6): `isHeb = profile.strongs[0]==="H"` — profile-driven, safe.

**H. Builders/gates in the run itself**
- `import_tipnr.py:719` — THE rewrite site (`UPDATE words SET strongs_base=…`);
  roster-freeze gate fires (any import_tipnr change → check_roster_regression
  CLEAN before import).
- `build_pn_greek_identity.py` — `hebrew_base` snapshot semantics: a re-run must
  source Hebrew from the Q2 home, not the rewritten column.
- `entity_resolution.py` + `build_entity_binding.py` — `tipnr_entities.bases`
  must include the Greek keys or the fuzzy number-guard floors ABP-side binds
  (design layer 5); Cushi verse-scoped logic re-checked after the re-run.
- Gates that ride: cert_invariants, health_check, compare_words (every differing
  row itemized to zero unexplained), gate_stage2_counts/audit_two_derivations
  (read the identity table — still valid), the new **unfindability gate**
  (mandatory, G3 condition 1): enumerate the 14,850 before (H-keyed) and after
  (Q2 home + lemma), zero findable-before/unfindable-after.
- The Q2 cross-ref home itself: NEW TABLE = JP checkpoint before it lands.

## 3. Open rulings needed before the charter freezes (reviewer)

- **C3-Q1 — the 3,380 'none'-bucket cells.** No Greek identity of ANY kind (no
  number, no lemma — Havilah-class rows are lemma-only; these are the refused
  residue + gentilics). Options: (a) KEEP the Hebrew number — they were never in
  flip scope; the reviewer's own G1 note called them a coverage boundary, and
  clearing them destroys their whole card/click path for zero honesty gain;
  (b) clear like lemma-only — pure column semantics, heavy reader cost.
  *Recommendation: (a) keep Hebrew, documented as the coverage boundary; revisit
  when the gentilic-identity backfill (the parked future candidate) exists.*
- **C3-Q2 — the cleared value for lemma-only rows.** Recommend `'*'` — the
  EXISTING numberless-PN convention: click gates (`strongs_base !== '*' ||
  english`), tag hiding, and the `pn_count` name-path all already handle `'*'`
  correctly, so Option B costs zero frontend special-casing. A NULL/empty value
  would need every gate re-audited.
- **C3-Q3 — SEO surfaces.** H-pages losing ABP refs (repoint or accept) and new
  G9xxx pages appearing (serve with step_lexicon lemma or exclude) — needs a
  ruling either way; today's behavior can't continue unchanged.

## 4. Proposed run shape (stage-1 pattern; not final until the rulings land)

Copy → roster gate → import_tipnr (rewrites strongs_base per class table +
writes/feeds the Q2 home) → build_pn_greek_identity re-run (Q2-sourced snapshot)
→ build_entity_binding --apply (extended bases) → gates: strongs_base GLOB,
health_check, compare_words itemized, unfindability gate, two-derivations
re-run → reviewer receipt → swap (one reversible move; pre-file kept) →
serving-code deploy for the A–F repoints (dashboard Reload + sweep) → G5
re-receipt of both flips against the rewritten tables + the switch-semantics
record.

Sizing note: the serving repoints (A–F) are a CODE deploy that must land
atomically with the swap or the H-keyed paths serve zeros in the gap — run
shape must sequence "swap then immediate deploy" or gate the repoints on a
table-presence check (deploy-safe pattern, preferred: code first, dormant until
the Q2 table exists).
