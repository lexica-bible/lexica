# HANDOFF — ABP source material (helps + app HTML) → next lane

Written 2026-10-24 from JP's notes. Everything under "What JP verified" was checked by JP
OUTSIDE CC; this session did not open these files. Re-verify any detail a step leans on.

## What JP verified (2026-10-24)
1. **Purchased** from apostolicbible.com, order EC9378: *Analytical Lexicon* (419 pp),
   *Lexical Concordance* (366 pp), *English-Greek Index* (90 pp). Free: NT 4th ed. PDF, OT 3rd
   ed. PDF. The files are on JP's machine, **NOT in the repo**. Licensing basis: the author's
   email of 2026-07-03 — no grants issued to anyone, intent to release to the public domain,
   proceed with attribution + a "not an endorsement" line. **CREDITS.md line 12 is still the
   placeholder** ("finalize after the licensing conversation") — wording not written yet;
   it's the open item under TODO "Licensing / attributions".
2. **PDF text layer.** The three helps use a symbol font ("Newport"): Greek typed as Latin
   keystrokes, no Unicode map. The mapping is fixed one-to-one (a→α … w→ω, V→ς, q→θ, c→χ,
   y→ψ, x→ξ, h→η). Accents are separate glyphs and are LOST. *Analytical Lexicon* layout: a
   POS + number line OPENS each entry ("NOUN masculine .... 60.1"), then "headword...gloss",
   then one line per inflected form with its parsing. JP's prototype parser on page 5 gives
   clean rows: number, lemma, POS, gloss, forms + parsing. The NT 4th ed. PDF uses real
   Unicode fonts and extracts as Greek directly.
3. **apostolicbibleapp.com** (the official ABP app — already the standing witness for
   source-reading calls, per build_abp_corrections.py): static HTML, one file per chapter at
   `/Chapters/<Book> <n>.html` (book names from `chapters.js`, e.g. "1 Kings 11"). Each word
   is `<td class="d">` with children `.s` (Strong's; `*` for names; compounds as separate `.s`
   spans joined by "-"), `.g` (Greek), `.e` (English). One verse per `<table class="tbl">` row.
   **Known source defect:** some Greek uses Latin look-alike letters — Gen 25:15 "Cολδάδ" for
   Χολδάδ, "Qεμάν" for Θεμάν. **Glued slots exist in the source too** (1Ki 11:21
   "2036-* / είπεν Αδάρ / Hadad said").

## The next lane — JP's pre-registered order
**No writes until (a) is in hand.**
- **(a) App-HTML diff** vs `abp_surface` + `pn_greek_identity`, read-only, slot by slot.
  CONTROL: Gen 25:15 must show the Latin-C defect; 1Ki 11:14 pos 7 must match Αδάρ. **The
  first thing the diff must report is edition drift** (OT 3rd ed. vs the app vs NT 4th ed.).
  **Status 2026-10-24: tools written, numbers NOT in yet** — `scripts/fetch_abp_app.py`
  (→ `abp_app_html/abp_app_slots.tsv`, gitignored) + `scripts/audit_abp_app_vs_surface.py`
  (read-only, JP runs on PA). Seen in a 13-chapter test fetch (CC-run, both controls PASS):
  Latin letters go BEYOND C/Q — H (Hσαύ Esau), O (Oνήσιμον), R (Rαύλος = Παῦλος, so not a
  look-alike); only C→Χ Q→Θ are mapped, the rest are censused with our letter at that spot ·
  † variant footnotes are `.g` spans with a hover title (kept OUT of the Greek, written to
  `abp_app_slots_notes.tsv`) · English notes typed in the Greek font ("εποίησε - σερvεδ.") ·
  stray "> 2532" number cells (Oba 1:14/18/21) · chapters.js lists the five one-chapter
  books as 0 (page is still "<Book> 1.html") · Psalm titles: our verse 0 = the app's verse 1
  (the audit's versification probe reports the shift; main numbers keep the plain key).
  · The site SPELL-CORRECTS missing pages ("Genesis 51" → 301 to Genesis 15; "Genesis 56" →
  300): the fetch never follows a redirect and checks every page's own title, cached ones too.
  **First full run 2026-10-24 (JP, PA; controls C1–C3 PASS; C3 moved to the 27 pinned
  compound names — the 1Ki 11:17 glued row is cured).** Fetch: 1,189 pages, 31,238 verses,
  577,994 slots, 10 † notes, 0 parser anomalies. Readout (CC, not yet reviewed):
  - EDITION DRIFT: English words differ in 11,142 / 31,081 verses (35.9%; OT 39.4%, NT
    25.6%). Psalms (2,433) is the title shift, not wording — ex-Psalms ≈ 30%. Spot-checked
    vs abp_texts: Gen 1:20 lives/souls, 1:21 whales/sea monsters, and "God beheld that it
    was good" in 1:13 (ours) vs 1:12 (app) are ALREADY in our source text → an edition
    difference upstream of our build, for those samples. Not every row is that (ours-only
    "he"/"the ones" look like build additions — unverified). Versification: Psalm titles
    (ours v0 = app v1, 146 chapters, ~96% under the shift), Pro 16 / 24:8, Jer 10, Hab 3.
  - ALIGNMENT 90.2% overall, ≈ 94% ex-Psalms. 34,289 "same slot, different number" pairs
    are mostly MIRROR swaps (3588↔2962 517/507, 2250↔1565 229/229, 1161↔3588) = same
    words in a different order on one side — cause NOT checked; v1 counts them unaligned.
  - GREEK vs abp_surface: exact 86.4%, after fold 97.7%, + C/Q 0.3%. Identity: 89.3% after
    fold (header/dictionary forms differ by design). 506 abp_surface forms hold an NBSP.
  - MORE APP FONT DEFECTS than C/Q, all evidence-backed by our letter at the same spot:
    H→η 792, O→ο 614, U→υ 4, R→π 6; Cyrillic П (U+041F) for Π (Пέτρος, Пαύλος ~300+);
    '+' for ϊ (Εφρα+μ, Αδωνα+, πρω+ ~600+); lower-case Latin = English typed in the Greek
    font ("τηε λιvινγ"). v1 maps only C/Q, so these sit in the mismatch counts.
  - Dictionary-word fallback rows: 97.9% after fold; the misses are inflected verbs with
    no abp_surface row (είπε/ἔπω 541, εποίησε/ποιέω, έλαβε/λαμβάνω …) = interlinear shows
    the dictionary word where ABP prints a form.
  **Audit v2 written (JP ruling 2026-10-24), numbers NOT in yet:** defect map C/Q/H/O/U/R/
  П/+ each on its own line; lower-case-Latin cells = "English in the Greek font", excluded;
  Psalms paired with the title shift (our v = app v+1) and reported on own lines (control
  C4); Pro 16/24, Jer 10, Hab 3 listed with a shift only if it lines up >= 90% (in a
  14-chapter test Pro 16 is REORDERED, not shifted — per-verse lines map it); swapped-
  order slots = own group under the split-flip ruling (same-count verses only;
  count-differs leftovers reported apart as "out-of-sequence"); missing printed forms →
  `abp_app_html/missing_printed_forms.tsv` with word type from words.morph (articles and
  pronouns are in it too, not only verbs); OT/NT headline at the top.
  **v2 full run 2026-10-24 (JP, PA; C1–C4 PASS) — lane (a) numbers in hand:**
  - HEADLINE app Greek vs abp_surface: OT exact 87.16% · after accents 98.71% · after
    defect map 99.63% (302,095 slots, Psalms shifted incl.); NT 89.07 / 98.94 / 99.75%
    (87,091). Names (pn_greek_identity): OT 53.17 / 90.57 / 99.00%, NT 36.63 / 83.20 / 98.06%.
  - Alignment 99.52% of our 626,309 slots (in place 94.02% + swapped 5.33% + out-of-seq
    1,055). Swaps: 32,608 of 33,364 moved ONE place (split-flip ruling; still unverified
    row by row). Same slot, different number left: 540. Psalms under the shift: 99.28%.
    **HELD (JP 2026-10-24): the 540 + 13 number disagreements from the fill census**,
    excluded from the abp_surface fill (verse · pos · our number · app form → Lexicon has it under):
    dotted neighbour — Dan 5:10 · 32 · 241.3 · αλλοιούσθω → 241.2 · Exo 26:13 · 27, Exo 32:15 · 25,
    Exo 38:15 · 6, Jos 8:33 · 16 · 1759.3 · ένθεν και ένθεν → 1759.2 · other number — 1Sa 19:3 · 27 ·
    302 · εάν → 1437 · **Isa 39:8 · 1 · * (Ἐζεκίας) · είπεν → 2036 — SUSPECTED SLOT MISALIGNMENT** ·
    Job 1:1 · 16 · 444 · ανἡρ → 435 · Lev 22:22 · 20 and Lev 22:23 · 15 · 3756 · ο → 3588/3739 ·
    Pro 24:13 · 8 · 4675 · ση → 4674 · Pro 24:27 · 6 · 4675 · σον → 4674 · Pro 24:27 · 15 · 3450 ·
    σοις → 4674. Source: `CENSUS_abp_surface_fill.md`.
  - Edition drift: English words differ in 9,157 / 31,228 paired verses (29.3%; OT 30.6,
    NT 25.6, Psalms 17.2); order-only 3,191.
  - Defect map matched: + 2,195 · C 1,287 · П 913 · H 898 · O 608 · Q 550 · R 6 · U 4
    (still differs ≤ 34 per letter). English-in-Greek-font cells: 17. No unmapped letters.
  - Versification: Pro 16 is REORDERED (ours 16:27–33 = app 16:20–26; app 16:2–9 = ours
    16:5…16); Pro 24, Jer 10 partial one-verse offsets (best −1 = 82% / 74%); Hab 3: app 3:20
    = ours 3:19. Per-verse map is in the run output.
  - MISSING PRINTED FORM (no abp_surface row, app prints another form): 4,058 slots →
    `abp_app_html/missing_printed_forms.tsv` (PA). verb 2,037 · no morph 1,582 · name 192
    (incl. Δαυίδ vs dictionary Δαβίδ 128 — a spelling, not a missing form) · article 99 ·
    pronoun 69 · noun 44 · other 28 · adjective 7. Top: είπε/είπεν vs ἔπω 557.
  - NEW, OUR SIDE: 544 abp_surface forms are GLUED two-word values (NBSP) where the app
    has one word — 'χειρί αυτού' (1Sa 17:57 pos 22), 'είπε Δαυίδ', 'ο δε', 'προσέχεε
    Μωυσής'. Same family as the cured identity glued rows. Cause not checked. No lane yet.
  - Remaining surface mismatches 751 + identity 291 (identity: app inflected vs our
    header/nominative — Γαλιλαίας/Γαλιλαία — by design). A few pronoun pairs differ
    (εγώ/με/μου, Gen 18:27, Job 6:24) — not checked.
- **(b) Analytical Lexicon → a table**, using the symbol map, with a locked test. CONTROL:
  "agcisteuw" → 70.4 ἀγχιστεύω.
  **Lane (b) numbers 2026-10-24 (CC, local; the PDF is JP's, output gitignored under
  `abp_helps/`):** parser `scripts/parse_abp_analytical_lexicon.py` — 8,584 entries,
  39,539 forms, 0 unparsed lines, 419/419 pages match an independent -raw entry count,
  controls PASS (agcisteuw 70.4 VERB · agorasmoV 60.1 NOUN masculine · page 5 = 20).
  Book misprints kept verbatim + counted (~30 parsing typos; 4 numbers printed on two
  entries — 2004 ζέω and 2114 ζήτησις look like misprints of Strong's 2204/2214; 4828.2,
  5072.1 unchecked). One entry carries two numbers ("5484, 85" χάρις = 5484 and 5485).
  The lexicon has NO proper names, and files ALL personal-pronoun forms (αὐτός's too)
  under ABP's raw 1473.
  Join `scripts/audit_lexicon_vs_missing_forms.py` vs the 4,058 missing printed forms:
  resolved under the same number 3,724 (91.77%); + under ABP's pronoun number 1473: 69 →
  3,793 (93.47%); ex-names (book has none) 3,793 / 3,866 = 98.1%. By type: verb 99.8 ·
  article 99.0 · noun 97.7 · adjective 100 · pronoun 92.8 · no-morph 97.4 · name 0 (191).
  Left: dotted neighbour 5 · other number 8 · clean word not listed 33 (some look like
  app typos — ανέστραπτεν, επίβλεψεν — unchecked) · 28 app cells that are English notes
  typed ENTIRELY in Greek letters ("δαγγερ" = dagger, "- Φορ τηε ενδ." = For the end) —
  the app audit's English-font check only catches cells with a Latin letter, so these
  slipped into the missing list (audit gap, 28 cells). Per-row result:
  `abp_helps/missing_forms_resolved.tsv` (local).
- **(c) Lexical Concordance → number → verse counts**, diffed against the ABP tab's totals.
  This answers routing follow-up (c), the MIXED 47.
- **(d) English-Greek Index** last.

## Tripwires to carry in (from memory / CLAUDE.md)
- **Dotted numbers:** the helps number entries like 60.1 / 70.4. Audit on the FULL dotted
  number by default; a "count = 0" must check dotted variants first (CLAUDE.md audit rule).
- **NBSP:** in our tables, two-word name values are joined by U+00A0, not a space
  (`LIKE '% %'` reads 0 on rows you can see). The app's glued slots will meet this; fire
  the check on the 27 pinned compound names first (word-study.md tripwire) — 1Ki 11:17
  slot 2 was cured and no longer works as a control.
- **Accents are lost** in the helps' text layer, so a helps lemma can only match ours after
  folding accents — never byte-exact. Byte-exact Greek comes from a PA dump of the built
  table, never from a PDF or `abp_texts/` (CLAUDE.md).
- **Latin look-alikes:** a diff that compares raw bytes will flag the app's Latin-C/Q forms;
  classify them as a source defect, never "fix" ours toward them.
- **Witness discipline:** word-order / Strong's / name-slot questions are settled against
  the source (memory `feedback_confirm_source_never_guess`); this app is now a machine-
  readable copy of that source — the diff is a two-derivations oracle, resolve each
  mismatch against the source, not by preference.
- Every detector fires on a known positive before a zero is trusted (the CONTROLs above).
- PA has `~/bible.db.pre-xref-fix-20261024` (the 10/24 rollback). Keep it until a nightly
  postdates the 22:41 apply, then it can go.

## Also open from 10/24 (no lane)
Baal 1Ch 5:23 (H1179) · **HELD: pn_greek_identity has 30 NBSP names vs the 27 pinned**
(audit C3 still PASSES — it checks the 27 are present; extras seen: Act 12:19 pos 0 'Ηρώδης δε',
Act 13:1 pos 24 'Μαναήν τε'; the third was cut off by `head -8` in the 10/24 paste — re-read the
full `~/abp_app_audit_rerun.txt` C3 block) · routing follow-up (h) · the stale 'none'-label cleanup (rides the
next identity rebuild). Record of the 10/24 correction:
`docs/tickets/RECORD_xref_vs_binding_fix_20261024.md`.
