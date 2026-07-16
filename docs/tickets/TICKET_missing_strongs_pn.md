# TICKET — Missing Strong's on proper-noun spelling variants (Ashchenaz → H813)

Status: OPEN. No code changes until the provenance contract (`docs/PROVENANCE_CONTRACT.md`)
is reviewed and committed; Strong's labeling on the card follows the contract's §2/§3 rules.

## Symptom
Ashchenaz (1Ch 1:6) has no Strong's number on its card. Expected H813 — Ashchenaz is the KJV
spelling variant of Ashkenaz (Gen 10:3 carries H813).

## Where it lives
Strong's numbers for TIPNR-backfilled proper nouns are **surface-keyed**:
`scripts/import_tipnr.py` matches the in-verse English (`row["english"]`) through
`find_entry`'s 8-step ladder — exact → strip trailing punct → strip leading particle →
de-hyphen → singular → `ALIASES` map (~line 411) → `DIRECT` name→Strong's map (~286), each
candidate validated against bdb/lexicon before it sticks. A spelling variant that isn't in
`ALIASES`/`DIRECT` and doesn't normalize to the canonical form falls off the ladder →
`strongs_base` stays empty → the card shows no Strong's and the occurrence sections stay
gated.

At runtime the lexicon join is number-keyed (`l.strongs_g = w.strongs_base`), so the fix is
entirely at import/backfill time — get the right base onto the word row and everything
downstream lights up.

## Root cause
Confirmed surface-keyed (see ladder above); the question the ticket answers is not "is it
surface-keyed" but "how do variants get onto the ladder."

Two candidate fixes:

- **A. Variant map (recommended).** Extend the existing `ALIASES` map in import_tipnr.py with
  variant→canonical spellings (ashchenaz→ashkenaz, etc.), populated from the audit below. Fits
  the ladder's existing shape, zero new machinery, every entry hand-checked against Strong's —
  matches the 100%-accuracy bar better than an algorithm.
- **B. Lemma-keyed lookup.** Key the lookup on the TIPNR entity's own Strong's bases
  (`tipnr_entities.bases`) rather than the English surface: if the occurrence verse-binds to an
  entity (pn_binding) and that entity carries exactly one base, take it. More general, but adds
  a dependency ordering problem (binding is built AFTER the backfill today) and inherits any
  binding mistake (see the gentilic ticket). Viable as a second pass for what A leaves.

Recommendation: A now (small, verifiable), reassess B only if the audit shows a long tail no
map should hand-carry.

## Sweep — scope the class
Zero-Strong's proper nouns cluster where variant spellings cluster: genealogies —
1Ch 1–9, Gen 5 / 10 / 11, Mt 1, Lk 3.

Detection (JP runs on PA — CC cannot query the db; read-only):

```
sqlite3 ~/bible-db/bible.db "SELECT v.book, v.chapter, v.verse, COALESCE(w.english_head, w.english) AS name
  FROM words w JOIN verses v ON v.id = w.verse_id
  WHERE w.strongs='*' AND w.strongs_base='*'
    AND v.book IN ('1Ch','Gen','Mat','Luk')
  ORDER BY v.book, v.chapter, v.verse LIMIT 200;"

sqlite3 ~/bible-db/bible.db "SELECT COALESCE(w.english_head, w.english) AS name, count(*)
  FROM words w
  WHERE w.strongs='*' AND w.strongs_base='*'
  GROUP BY 1 ORDER BY 2 DESC LIMIT 100;"

sqlite3 ~/bible-db/bible.db "SELECT count(*) FROM words WHERE strongs='*' AND strongs_base='*';"
```

Notes on the queries — GROUND-TRUTHED against the live row 2026-07-16: `strongs='*'` is the
TIPNR proper-noun marker (backfill writes the real number to `strongs_base` and leaves
`strongs` bare-starred on purpose — see data-model.md, "Bound-card occurrences"). **A missed
backfill leaves `strongs_base='*'` as well — NOT NULL/empty** (verified: the Ashchenaz row is
`strongs='*', strongs_base='*'`; the NULL/empty predicate returned a false zero). Book and
chapter live on `verses`, so the sweep joins `words.verse_id → verses.id`. Control test: the
query set MUST surface ashchenaz @ 1Ch 1:6 — a detector that misses the known positive proves
nothing (standing rule).

For each hit, the proposed canonical Strong's is looked up by hand (Strong's / TIPNR bases),
never guessed from spelling similarity alone — a wrong number is worse than a missing one.

## Sweep results (PA run, 2026-07-16) — the class is scoped
Control PASSED (ashchenaz @ 1Ch 1:6 surfaced). **2,203 double-star rows total**, in five
distinct piles that need different treatments:

1. **Variant spellings** (the core class) — the 1Ch 1–9 genealogy flood: sabta, zephi,
   alian, shimma, henoch… Hundreds of rows. Fix A (ALIASES map) applies.
2. **LXX-only forms** — oumasphae, aisi, ephradabak, esamathim, emasaraim…: ABP/LXX Greek
   spellings with NO KJV canonical form. A variant→canonical map may have no target;
   needs its own ruling (own Strong's? unnumbered by design?). Do NOT force-map these.
3. **Blank names — 477 rows** (the single biggest bucket): starred word, no English at all.
   Different bug class entirely; sample query below, root-cause before any fix.
4. **Common words starred** — saying (13), said, woman, field, man, area: the star is on
   non-names → mis-marking upstream, not a lookup miss.
5. **Possessives / frequent names** — jacobs, aarons; jesus/moses/david missing 8–9× each.
   Verse-specific (punctuation/compounds); eyeball, don't blind-map.

Follow-up sampling (JP runs; piles 3 and 4):
```
sqlite3 ~/bible-db/bible.db "SELECT v.book, v.chapter, v.verse, w.position, w.english, w.english_head
  FROM words w JOIN verses v ON v.id = w.verse_id
  WHERE w.strongs='*' AND w.strongs_base='*' AND COALESCE(w.english_head, w.english, '')=''
  LIMIT 30;"
sqlite3 ~/bible-db/bible.db "SELECT v.book, v.chapter, v.verse, w.english
  FROM words w JOIN verses v ON v.id = w.verse_id
  WHERE w.strongs='*' AND w.strongs_base='*' AND lower(COALESCE(w.english_head, w.english)) IN ('saying','said','woman','field','man','area')
  LIMIT 30;"
```

## Acceptance
- Ashchenaz @ 1Ch 1:6 carries H813 on `strongs_base`; card shows the Strong's head and the
  occurrence sections un-gate.
- Audit list driven to zero or each residual individually justified (some starred rows may be
  legitimately unnumberable).
- After any fix run, re-verify the standing invariant:
  `SELECT count(*) FROM words WHERE strongs_base GLOB '[0-9]*'` must be 0.
- Any `--apply` follows dry-run + JP review; re-run the dependent PN chain
  (import_tipnr → surface → translit) per the settled build order.
