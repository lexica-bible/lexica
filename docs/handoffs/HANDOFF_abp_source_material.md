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
- **(b) Analytical Lexicon → a table**, using the symbol map, with a locked test. CONTROL:
  "agcisteuw" → 70.4 ἀγχιστεύω.
- **(c) Lexical Concordance → number → verse counts**, diffed against the ABP tab's totals.
  This answers routing follow-up (c), the MIXED 47.
- **(d) English-Greek Index** last.

## Tripwires to carry in (from memory / CLAUDE.md)
- **Dotted numbers:** the helps number entries like 60.1 / 70.4. Audit on the FULL dotted
  number by default; a "count = 0" must check dotted variants first (CLAUDE.md audit rule).
- **NBSP:** in our tables, two-word name values are joined by U+00A0, not a space
  (`LIKE '% %'` reads 0 on rows you can see). The app's glued slots will meet this; fire
  the check on 1Ki 11:17 slot 2 first (word-study.md tripwire).
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
Baal 1Ch 5:23 (H1179) · routing follow-up (h) · the stale 'none'-label cleanup (rides the
next identity rebuild). Record of the 10/24 correction:
`docs/tickets/RECORD_xref_vs_binding_fix_20261024.md`.
