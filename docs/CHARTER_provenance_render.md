# CHARTER — Provenance-contract render work

**STATUS: CLOSED COMPLETE 2026-07-16** (reviewer receipt, screenshot-verified) — except
item 4 (tappable badge tooltips + shared registry), which stands chartered FORWARD as its
own session, gated on the mobile sheet contract. Shipped: items 1/2/3/5/6 (commits
`6288c5c` range) + the chip-line consistency fix on the new card types (`c3c0cdd`, found
in reviewer verification). Verification receipts (reviewer-confirmed screenshots, JP):
Shaul Gen 46:10 (combined badge + own-line chip + no echo) · Gen 1 overview (AI tags) ·
Baal (plain-TIPNR negative case, then own-line chip) · Pharisee ("Group") · David Mat 1:6
(name-path caveat line, plain metaV badge).

Chartered 2026-07-16 off the audit (`AUDIT_provenance_sweep.md`); JP picked it as next.
Spec of record: `docs/PROVENANCE_CONTRACT.md`. Scope = DISPLAY code only
(`static/src/30-detail-panel.jsx` + `views_summary.py` for the AI tag payload if needed);
no binder, no tables, no data changes. Each item lands as its own commit; JP screenshots
for the reviewer per the usual flow.

## Update going in: Nave's is GONE (JP, 2026-07-16)
The Nave's data was removed ("nuked") on PA — the card section can never render. Charter
therefore: (a) the audit's C-finding on Nave's is MOOT; (b) the dead Nave's code in
30-detail-panel.jsx (state, fetch, section, ~13 refs) is REMOVED as part of this pass —
dead code that pretends to be a live source is exactly what the contract exists to stop;
(c) the `naves` row in the contract §2 registry gets struck.

## Work items (from the audit's confirmed failures)

1. **B — combined badge.** `.pnbound` rich variant shows MetaV fields under a TIPNR-only
   badge → header badge becomes "MetaV/TIPNR" when `richPerson` (metav body folded in);
   stays "TIPNR" on thin/facts-only cards.
2. **C — "matched by name" state line.** Name-path metaV card (person AND place tabs)
   gains the §4 line: "matched by name — not checked against this verse." Wording may
   unify with the AI block's existing caveat style.
3. **A+F — summary panel label.** Book/chapter summary gets the AI tag (it currently has
   NO label at all). Every synthesized block sitewide carries the AI tag — JP ruling
   already on record (§3 row: reinstated).
4. **D — interactive badges.** ONE shared tooltip component (tap + hover) + ONE frontend
   registry keyed by contract §2 source keys; the three per-page `title` strings
   (Idiom/Grammar/Lexica) migrate into it. Mobile opens via the shared Sheet/Menu
   machinery per the sheet contract — no new per-card surface.
5. **'Other'-type card headings.** 216 live cards headed "Identity" (Pharisee 93, Baal 67,
   Sadducee 13, + deities/months/constellations/objects/Satan/Leviathan singles). Needs
   the per-type rulings below BEFORE code.
6. **Nave's removal** (see above).

## Rulings needed from JP (with recommendations — delegation rule applies)

R1. Group records (Pharisee, Sadducee, Herodian, Stoic, Epicurean, Nicolaitans, scribal
    groups): **recommend** heading "Group" with the TIPNR descr line ("Religious group in
    the New Testament") doing the explaining — the People/Clan treatment minus the
    "Descended from" line (no ancestor exists).
R2. Deities/idols (Baal, Artemis, Tammuz, …): **recommend** heading "Deity (pagan)" — the
    reader must never mistake an idol card for a person card; TIPNR's own descr already
    says "A male deity…".
R3. Months (Bul, Chislev, Elul, Shebat), constellations (Orion, Pleiades), objects
    (Jachin the pillar), Alamoth (musical term): **recommend** heading "Reference" —
    they're real TIPNR records with verse matches, just not identities.
R4. Satan ("an angel") and Leviathan ("a monster"): **recommend** "Reference" as well —
    the text-first rule says don't editorialize a category; TIPNR's descr line carries it.
R5. Combined-badge wording: **recommend** "MetaV/TIPNR" (contract §1's own example).

## Order of work
Items 3 → 2 → 1 → 6 first (small, independent, each screenshot-checkable), then 5 once
rulings land, then 4 last (the tooltip component is the only one touching shared
machinery + the mobile sheet contract).
