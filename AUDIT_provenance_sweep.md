# AUDIT — Provenance sweep + R-1 hand-check rows (2026-07-16)

Chartered AUDIT ONLY (contract §8). No fixes shipped from this session except the
pre-existing card-nits ticket (E, commit `3ee0d18`, JP-confirmed, reviewer-accepted).
Inputs: `docs/PROVENANCE_CONTRACT.md`, `docs/tickets/TICKET_gentilic_binding.md`,
PA inventory queries (JP-run 2026-07-16), `scripts/pn_binding_hot.txt` (110 rows) +
`scripts/pn_binding_numonly.txt` (1,200 rows) fetched from PA via static/ fallback
(public copies DELETED after fetch — logged per reviewer note 2).

## 1. Render sweep — checks A–F, every card section (code-verified, line cites)

| Check | Verdict | Evidence |
|---|---|---|
| A label present | PASS everywhere EXCEPT the book/chapter summary panel, which has **no label at all** | `SummaryPanel`, 30-detail-panel.jsx ~125–144: "About"/"This chapter" AI text, no badge |
| B label correct | **FAIL** on `.pnbound` rich variant: MetaV fields (born/died/kin) render under a TIPNR-only badge | jsx ~891 `richPerson ? <MetavPersonBody…` under `bdb-badge TIPNR` header ~894; confirmed live (Shaul, Gen 46:10) |
| C §4 state visible | **FAIL** on the name-path metaV card (person AND place tabs) and Nave's — identity claims, no "matched by name" line. AI block has its caveat (jsx ~993). Bind gating itself is clean: nothing name-based renders under a bind (jsx 738–743) | jsx ~905–958 (metav), ~959–984 (Nave's) |
| D badges interactive | **FAIL** sitewide: all badges static spans. Idiom/Grammar/Lexica carry hover-only `title` text with per-page wording (jsx ~1036–1042) — itself a §5 violation (no single registry, no tap) | |
| E name echo (§6) | **FIXED** 2026-07-16, commit `3ee0d18` — full `.pnbound` variant drops the echo on case-insensitive equality, keeps it on difference | verified live on Shaul/David/Christians |
| F AI tag | **FAIL**: summary panel (see A). `aidesc` block correctly tagged AI | |

No new failure classes beyond the contract's known-failures list; one upgrade (summary
panel fails A outright, not just F). All fixes = the already-ticketed render work
(TODO "Provenance-contract RENDER items unchartered") — nothing new to charter.

## 2. Taxonomy inventory (PA, JP-run) — grounds contract §7

- `tipnr_entities.section`: person 1,822 · place 339 · **other 34**.
- `tipnr.entity_types`: person 1,777 · place 847 · other 117 · person,place 112 ·
  other,person 5 · other,place 3 · other,person,place 1.
- Binds: exact 13,436 + fuzzy 1,054 + versification 40 = **14,530** — matches the R-1
  record exactly, zero drift.
- metav_people 3,086 · metav_places 1,276; groups table = 12 tribes + Genealogy of Jesus.

**OI-2 resolved as an inventory** — `section='other'` (34 entities) breaks down as:
deities/idols (Baal, Bel, Tammuz, Artemis, Ashtaroth, …), calendar months (Bul, Chislev,
Elul, Shebat), NT/OT groups (Pharisee, Sadducee, Herodian, Epicurean, Stoic, Nicolaitans,
Shimeathite, Tirathite, Tarpelite), temple pillars (Jachin), Leviathan ("a monster"),
constellations (Orion, Pleiades), Satan ("an angel"), Alamoth (musical term).

**These DO render today**: 216 live verse-matched rows on 'other' entities — Pharisee 93,
Baal 67, Sadducee 13, Artemis 5, the rest 1–3. The card labels every one of them
**"Identity"** (the fallback branch, jsx ~807). Matches look legitimate; the label is the
gap. Recommendation (for the render-work charter, per-type ruling before treatment per
contract §7): deities → "Deity (pagan)" or similar wording JP rules on; groups →
these are exactly the People/Clan display class (Pharisee card should read like the
Christians card, not "Identity"); months/constellations/objects → likely "Reference" or
no entity card at all (a month is not an identity claim); Satan/Leviathan → JP ruling.

## 3. Gentilic residual sweep — ticket acceptance line CLOSED

Sweep query (suffix net + `%im` added on reviewer note) returned 14 names, ALL `%im`
place names (Kirjath-jearim, Ephraim, Shittim, …) — Hebrew plural endings on genuine
places, correctly place-bound. **Zero** hits on -ite/-ites/-itess/-ians/-eans. The query
demonstrably fires (returned rows), so the zero is trustworthy. Acceptance: **no true
gentilic→place binds remain.**

## 4. Hand-check rows — bucketed, per-class recommendations

### pn_binding_numonly.txt (1,200 rows, 441 names) — number-matched, name didn't match, floored
| Rows | Class | Recommendation |
|---|---|---|
| 527 | Gentilic/group words (egyptians 110, canaanite(s) 67, persians 30, syrian(s), sidonians, …; a few -im place spellings mixed in) | **Floor stays.** This is the ruled gentilic tier discipline; group-own-entity question is parked (pile U / R-2). No action now. |
| 352 | Spelling variants, single close candidate (abia/abiah→abijah, abadon→abdon, …) | **Real recovery candidates.** Queue as a variant-map batch for the NEXT binding rebuild (R-2 or its own), each pair eyeballed first; roster-freeze tripwire applies (`check_roster_regression.py` must pass clean). Do NOT patch live. |
| 181 | Single candidate, name genuinely differs (ahijah→ahimelech, amminadab→izhar, abiasar→ebiasaph) | **Floor stays — this bucket is the guard working.** Some are legit aliases, some are flat wrong candidates (amminadab→izhar). Only pairs individually verified against TIPNR move to the variant batch; the rest never bind. |
| 130 | adonai→'lord' (divine title) | **Floor stays.** Title-of-God, not a person record match — same family as the Pharaoh title demotions (pile V). Ruling record there. |
| 10 | Genuine multi-candidate (Beth-horon upper/lower, Ephratah, Bashemath) | **Floor stays** — real ambiguity, exactly what the floor is for. |

### pn_binding_hot.txt (110 rows) — same-verse multi-candidate, floored
| Rows | Class | Recommendation |
|---|---|---|
| 60 | Same-name twins (several people share one key: azariah, joash, james, …) | Floor correct; recovery needs per-reign/per-person disambiguation = the pile-V class. Parked with it. |
| 26 | Distinct aliases in one verse (simon/peter, judah/judea, …) | Floor correct; alias-pair rulings belong to R-2's alias work. |
| 24 | Base vs compound name (mary vs mary_magdalene, sinai vs sinai_wilderness, …) | Floor correct; a "prefer the compound when the verse text carries the qualifier" rule is a possible R-2 candidate — recorded, not recommended yet. |

**Net: nothing in the 1,310 rows is a live bug.** Every floored row floors for a defensible
reason; the one genuinely recoverable class (352 spelling variants) is rebuild-gated work,
not a patch. The hand-check debt is now PAID as a class-level review; per-pair eyeballing
of the 352 happens when the variant batch is built.

## 5. Descriptor-of-individual gentilics (JP line item)

Grounding from this audit: "Canaanitess" @ 1Ch 2:3 floors (verified in the numonly file,
6 moabitess rows same class). Ticket's own ruling already covers it: descriptor uses MAY
carry the ancestor People/Clan card only where the verse-corroboration tier genuinely
supports it; otherwise floor. The numonly evidence says the tier does NOT support these
today (that's why they're in the file). **Recommendation: no binder change; revisit only
if R-2's group-entity work (pile U) creates a better target.** Ruling record stays in
TICKET_gentilic_binding.md.

## 6. Session lessons
- The contract's `%im` gap in the sweep SQL (reviewer catch): the production classifier
  (`_GENTILIC_SUFFIXES`, entity_resolution.py:257) has `im/i/s`; any SQL approximation of
  a classifier gets diffed against the classifier's own list before it runs.
- PA cannot push to GitHub; data files ride `static/` + fetch + delete (logged), and the
  stranded-commit hazard (a PA-local commit blocks the next deploy pull) is real — reset
  cleanly, verified `master...origin/master` even.
