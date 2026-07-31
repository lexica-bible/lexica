# HANDOFF — LANE A FILL (article slot), the arc's first write path

Opened 2026-07-31. Prior sessions: `docs/tickets/TICKET_509_article_slot_resweep.md`
(§6a/§6b rulings, JP-confirmed; §6c the `--lanes` flag). Read that ticket cold, top to
bottom, before anything else. Read `TODO.md` item ② too — this session and the PN-star
merged-verb fix both edit build-side slot assignment.

**This is the first session in the whole arc that writes.** Everything before it was
counting and certifying. Act accordingly.

## The target — pre-registered, not discovered as you go

```
python3 scripts/audit_article_slot_carrier.py --lanes
```

**LANE A = 1,325 rows** (bin D 276 + bin R 1,049). A carrier row is lane A when a blank
slot sits directly beside it already holding a real number (1,317) or a star (8). The
word's own number is already in the verse with an empty slot, so the repair is to hand the
English back to it. **That list is the target set. Generate it from the detector at session
open and pin it before writing a predicate** — do not re-derive it by hand, and do not
widen it mid-session.

**LANE B (1,363 rows) IS NOT IN SCOPE.** No pass runs there, ever. It closes row by row,
by ruling or by curated write, in a different session.

## The gate — the count itself is the audit

Lane A's ceiling is 1,325. **A write set above 1,325 means lane-B rows got swept in without
review — halt, do not ship.** Build the ceiling check into the fix script as a hard stop,
not a printed warning.

## Expected picture after the fix — state it BEFORE running anything

The detector re-runs the PRODUCTION build, so a working build-side fix moves lane-A rows
out of D/R and into **bin P** (the build repairs it). Pre-register this:

```
  before                     after a correct fix
  bin P      1               ~1,326   (1 + the 1,325 lane A rows)
  bin R  1,049               ~0
  bin D  1,639               ~1,363   (lane B only, untouched)
  lane A 1,325               ~0
  lane B 1,363               1,363    UNCHANGED - if this moves, the pass overreached
```

**Lane B holding at exactly 1,363 is the real gate.** A pass that "fixes" 1,400 rows has
eaten rows it was never allowed to touch.

## ⚠ THE CONTROLS FLIP — expect it, do not "repair" it wrongly

Three bin controls are lane A rows: `Mat 20:22 'Jesus'`, `2Sa 12:9 'Uriah'`,
`Gen 22:21 'Huz'`. A successful fix moves them from bin D to bin P, so the detector will
HALT on its own controls. **That halt is the fix working.** Flip those three to `want P` in
the SAME commit as the build change, with a note saying which commit repaired them — never
by loosening the predicate, never by deleting a control.

Must NOT move: `1Ki 9:26 'the city'` stays D (lane B), `1Co 1:28 'the things'` stays S,
`Act 19:4 'Jesus the'` stays P, and the old-predicate replay stays 951 raw / 509 filtered.
The six lane controls stay green throughout. `--prove-halt` and `--prove-halt-lanes` must
still exit 1.

## Open calls this session has to make (settle before the predicate, per the last session)

1. **What moves** — the whole English on the slot, or only the residue past the article's
   own words? `Act 20:15 'and'` is a whole-slot move; a row like `'and the'` is not — "the"
   is the article's own and must stay. Rule it, write it down, control it.
2. **Direction** — the blank slot can sit either side. Decide whether both directions are
   in, and prove each with its own control row.
3. **The 8 star rows** — same shape, star target. Ruled in for now (`Gen 22:21 'Huz'` is a
   lane control), but confirm the star target is safe to write to given the PN-star work
   running beside this. **Lesson pinned in TODO ②: adjacency is NOT the discriminator for
   star false positives — whether the carrier holds a name is.**

## Hard rules for the write

- Scratch build first. The rebuild never touches the live database — it builds into
  `bible.db.new`, swapped by hand, one reversible move. Follow `/rebuild-words`; do not
  improvise it.
- CC cannot read `bible.db`. Every check is a read-only line JP runs. Dry run and verdict
  before any `--apply` — the expected picture goes up BEFORE the command.
- After the swap, the live sizing count in ticket §4b should fall from **~2,662 to ~1,363**
  (lane B only). That is JP's read, and it is the live proof the fix landed.
- Re-run `import_tipnr.py` and check the strongs_base rule after any words rebuild.
- `tests/test_pn_star_verb_merge.py` and the roster regression check are pins that ride
  along — green before and after.

## Sequencing with item ②

The PN-star merged-verb fix (4,905 rows) and this lane-A fill both redistribute English
between slots at build time, and both touch star slots. **Land them one at a time with a
full detector run between**, so a bin that moves can be attributed to one change. Do not
fold them into one rebuild.
