# DRILL SHEET — Greek-header backfill (source='none' lane) + breathing cleanup

Status: DRAFT 2026-07-30, JP pre-rulings baked in (JP is the reviewer of record for
this lane). ONE open item below; everything else is ruled and a quick confirm.
Sizing (live, JP-run 2026-07-30): pn_greek_identity source='none' = 3,380 tokens;
**2,587 have a Greek surface in the same verse** (israel 495, egypt 96, jerusalem 85,
bethel 61, levites 49 …), all H-numbered — R-2 residue (H-tokens with no STEP Greek
mapping stayed on the Hebrew path). Plus 288 numberless Αἰγύπτιος-class tokens.

## PRE-RULED (JP 2026-07-30 — not up for review)
1. **Header form = nominative lemma in ABP's OWN orthography.** Dictionary shape
   heads the card (Αἴγυπτος, never Αίγυπτον); the verse's inflected form stays the
   "IN THIS VERSE" slot's job — the convention already live (Ἰησοῦς / Ιησου).
2. **Indeclinables ride free.** Ἰσραήλ/Μωάβ-class Hebrew names don't change shape;
   for them verse form = headword. This covers the bulk of the 2,587 with zero new
   data. Mechanical split proposed below.
3. **ABP's spelling wins, always.** Known divergences from standard transliteration
   (Σωμορών for Samaria, Βηρσαβεαί for Beersheba) are ABP's forms — the header must
   match the verse's own text, never a normalized/imported spelling, or the card
   contradicts the page it sits on.
4. **No guessed forms.** A token no lemma source covers keeps its English header.
   English fallback is honest; a constructed nominative is not.
5. **Gentilic question is IN the sheet** (open item 2): the 288 Αἰγύπτιος-class
   tokens are adjectives ("Egyptian"), not proper names — include or exclude from
   the lane before the build, not during.
6. **Gate shape: count-only delta on the presentation table.** This lane touches
   pn_greek_identity ONLY (header/presentation source). Zero pn_binding changes,
   zero tipnr_entities changes, zero words/verses changes — any identity delta is
   an automatic stop. Max 2,587 new Greek headers (fewer after exclusions). The
   90-form breathing cleanup rides the SAME builder run with its own pre-registered
   list (transform: detached mark + space → combined rough breathing, NFC; its
   post-check: transliterations byte-unchanged).

## Proposed mechanics (for confirm)
- **Indeclinable detection is mechanical:** group the 2,587 by name; a name whose
  Greek surface is IDENTICAL across every occurrence (accent-folded compare, ABP
  bytes kept for display) = indeclinable → that form IS the headword. Names with
  varying surfaces = the declinable minority → open item 1.
- New identity-builder layer `source='surface'` (4th layer, below tipnr/lemma-only,
  above none), rebuilt through the existing table-drop path; detector control =
  Hadad 1Ki 11:14ff must flip English→Greek, and one pinned indeclinable +
  one pinned declinable land their expected exact forms.

## OPEN ITEM 1 (the actual question): lemma source for the declinable minority
Where does the nominative come from for Αἴγυπτος/Σαῦλος-type names once the
mechanical split isolates them (expected: dozens of names, not hundreds)?
Options, in proposed order:
  a. **Pre-registered hand table** — small, per-name, cited from ABP's own text
     where a nominative occurrence exists anywhere in the corpus (preferred: the
     corpus itself supplies ABP-orthography nominatives for most declinables —
     e.g. Σαύλος appears nominative in Samuel narrative);
  b. corpus-derived: pick the name's own nominative-case occurrence automatically
     (morph column where populated) with the hand table only for names never
     appearing in the nominative;
  c. reject: any external lexicon spelling (violates pre-ruling 3).
Recommendation: (b) with (a) as its residue — the corpus is the source, the hand
table is the leftovers, both ABP-spelled by construction.

## OPEN ITEM 2: the 288 Αἰγύπτιος gentilics
Adjectives, not names; no Strong's number on the token. Include (they'd head
Αἰγύπτιος and readers meet them constantly) or exclude (not proper nouns; keep
English until the gentilic doctrine says otherwise)? Recommendation: EXCLUDE from
this lane — same posture as the gentilic guard elsewhere (gentilics are their own
class); revisit as its own micro-lane if wanted.

## Out of scope
Chip-merge display pass (separate charter) · word-position lane · any bind change.
