# HAND-OFF 2026-07-31 → next CC session — 509 ARTICLE-SLOT RE-SWEEP (charter seed)

Read `CLAUDE.md` first, then this file, then
`docs/tickets/TICKET_detector_gap.md` (the close-out that produced this charter) and
`docs/audits/AUDIT_pn_star_verb_merge.md` (superseded 145 list + the 509 list, both flagged
at the top as not-to-be-fixed-against).

Paths below are POST-REORG (`b914be98`) and cited as they now stand.

---

## THE CHARTER

Build a control-fired detector for the **509 article-slot population**, by the same method
that closed the star-verb gap. The model to copy is `scripts/audit_pn_star_verb_merge.py`
— read it before writing anything; the shape of that script IS the spec.

Required properties, all of them:

1. **Predicate written down in the header, in full.** Not "the rule is obvious from the
   code." The whole reason this ticket exists is that the previous sweep's predicate was
   never committed and turned out to be unrecoverable.
2. **Read-only, source-side.** Reads `abp_texts/`, never the database. CC cannot query
   `bible.db`; live confirmation is a JP step (paste-ready `sqlite3` one-liners at the end).
3. **At least three controls, including both a known MISS and a known HIT** (below). A
   count printed without every control firing is void.
4. **Red-first proof, both directions.** Show the OLD anchoring goes silent on the known
   miss, and show the new predicate fires on it.
5. **HALT path proven live, not assumed.** Break a control on purpose, watch it halt, record
   the output. (Standing rule: fire a detector on a known positive before trusting a zero.)

## CONTROLS TO USE

| Verse | Shape | Role |
|---|---|---|
| `Act 19:4` "Jesus the" | in the old 509 list | **known HIT** — proves the probe reaches the right population |
| `Mat 20:22` "JesusG3588 G* said,G2036" | Jesus on the article slot, star blank | **known MISS** — absent from the 509 |
| `2Sa 12:9` "Uriah" | same shape | known MISS |
| `Gen 22:21` "Huz" | same shape | known MISS |

`Mat 20:22` is confirmed live on PA: slot 2 `G3588` carries "Jesus", slot 3 is the star,
blank. Clicking "Jesus" there serves the article's card — the exact defect the 509 exists to
catalogue.

## THE THING YOU MUST RESOLVE EXPLICITLY

The old sweep's stated rule was "adjacent-empty-slot cases (the build redistribution class)
are EXCLUDED". That rule:

- drops **3,564** article slots carrying English, wholesale; and
- **was not applied consistently** — `Act 19:4` has an adjacent blank star and survived it.

So the exclusion is neither principled nor honoured. The new predicate must **either** take
that population in, with the rationale written down, **or** bin it as a reported class with
a count. Nothing silently dropped, and no cap applied without logging what it cut.

---

## GATE BEFORE ANY FIX WORK

Revised article-slot count declared, controls green, halt proven. Only then does the fix
session open — and it runs against **all three lists together**, once all are final:

    class A          2,237
    class B1         2,668     (subtotal 4,905)
    revised 509      TBD by this session

B2's 91 roster-silent rows need an eyeball pass; it can ride along with the fix session or
precede it, your call — but they are a reported class, not a residue to quietly drop.

---

## STANDING INVARIANTS — do not relearn these the hard way

- **Never diff against the superseded 145.** It is one orientation of a two-orientation
  class, from a predicate that no longer exists and that dropped structurally identical rows
  inconsistently (`'this Moses'` out, `'these Galileans'` in). It has no baseline value.
- **The inheritance gate is REMOVAL-ONLY** — it may retire an inherited number, never mint
  one. Fall-through to a later lane is how that broke before (sheba@1Ki.10.4, judah@Ezr.9.9).
- **The frozen `pn_hebrew_xref` snapshot is the canonical restore path.** `import_tipnr`
  fills only `strongs_base='*'` rows and re-breaks hand fixes (Cushi H3569→H3570).
- **A gate test on a retired copy proves nothing** — `build_pn_greek_identity` there runs in
  re-run mode and re-reads its own old numbers (0-refused false-clean).
- **Adjacency is not a merge discriminator.** `Gen 23:19 "Abraham entombedG2290 G* SarahG*"`
  is directly adjacent and IS a genuine merge. Whether the carrier holds a name is the
  discriminator. A guard built on adjacency was written and reverted this session — don't
  rebuild it.
- **A source-side scan is not live state.** Confirm on PA before claiming served behaviour.

---

## DOWNSTREAM QUEUE (after the fix session — do not fold any of these in)

1. **7/30 reclassification catch-up.** The Greek-header rebuild ran but the retirement
   copy-step never did, so live still serves the older classification. Needs the
   retirement-script count re-declaration (declare once, from the final shape — JP ruling)
   plus the **9 held-out gainers**: saul ×8 → G4549, zacharias ×1 (Luk 3:2) → G2197. Held
   out of the G707 ship by the removal-only rule. Own session, own red-first gates.
2. **Same-name / renamed allowlist design** — 358 slots, Group B of
   `docs/tickets/G707_diff_report.md`. Ruled correct-to-drop text-first but carrying a
   defensible link (edom/Esau, horeb/Sinai, lod/Lydda…). Cert-#7-style curated machinery,
   JP-checkpointed.
3. **WAL-crumb cleanup** — small, zero-risk. Orphan 0-byte `-wal`/`-shm` files in
   `~/bible-db`; no script opens WAL, so they are historical. Check dates, delete.
4. **Possible second reorg pass** — ~11 root files were out of the first pass's scope
   (`CHARTER_*`, `DESIGN_*`, `REVIEW_*`, `RELAY_v11_build_open.md`, `STATE.md`,
   `V9_PILE.md`, `V111_CONSULT.md`, `JP_QUICKREF_lexica.md`, `FEATURES.md`, `CREDITS.md`,
   `entity_resolution_rebuild.md`). `entity_resolution_rebuild.md` looks orphaned —
   lowercase, no family. Also open: the pre-existing broken pointer
   `docs/tickets/DRILL_greek_header_backfill.md` → `docs/tickets/greek_header_split.txt`
   (that file never existed at any commit).

---

## PA COMMANDS FOR JP (read-only, if this session needs live confirmation)

```bash
sqlite3 ~/bible-db/bible.db "SELECT w.position, w.strongs, w.strongs_base, w.is_pn, w.english FROM words w JOIN verses v ON v.id=w.verse_id WHERE v.book='Mat' AND v.chapter=20 AND v.verse=22 ORDER BY w.position;"
```

```bash
sqlite3 ~/bible-db/bible.db "SELECT w.position, w.strongs, w.strongs_base, w.is_pn, w.english FROM words w JOIN verses v ON v.id=w.verse_id WHERE v.book='2Sa' AND v.chapter=12 AND v.verse=9 ORDER BY w.position;"
```

`verses.book` is the 3-letter abbreviation (`Mat`, `2Sa`, `Gen`), not a number.
