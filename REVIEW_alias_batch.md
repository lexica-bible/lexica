# REVIEW PAYLOAD — alias batch: TIPNR loader root-cause fix + variant map + leave-list

Third pre-run payload for the rebuild (charter `docs/REBUILD_SCOPE_headword.md`, item 3).
Nothing here is wired in yet; the data/docs files exist in the repo as proposed material.
Gate zero is CLEARED (JP paste: 1.1 GB free). Reviewer note honored: fragment caution list
documented; every ACCEPT carries its reason.

## Root-cause finding (changes the shape of this batch)

The plan was a hand map for ~1,690 variant spellings. Investigating why TIPNR's roster
lacked them found the real cause: **the loader has never read TIPNR's alternate-spelling
records at all.** `import_tipnr.parse_tipnr` treats a line as a sub-record only if it
starts with whitespace; in the pinned `tipnr/TIPNR.txt`, **10,127 sub-record lines start
with an en-dash ("– Named…")** and only 96 with whitespace. Verified by direct test:
`'elias'`, `'sabta'`, `'zephi'`, `'ashchenaz'` are all absent from the parsed roster —
the existing hand `ALIASES` (elias→elijah etc.) has been silently compensating. A second
casualty: sub-record Strong's extraction never ran either, so **175 entities are missing
numbers** the file carries (measured: 2,687 → 2,862 numbered entities after the fix).

Because sub-record lines don't start with a tab, their columns are also shifted one left
vs what the dead code expects: significance is in column 0 (after the dash), the
alternate name in column 1, the Strong's field in column 2, the per-version display form
("Ashkenaz =ESV,NIV; Ashchenaz =KJV") in column 3, references in column 5.

## Proposed change 1 — fix `parse_tipnr` sub-record reading (`scripts/import_tipnr.py`)

a. Sub-record detection: `is_sub = line[0] in (" ", "\t") or line.startswith("–")`.
b. Column map per the real format: `significance = parts[0].lstrip("–").strip()`,
   alternate name from `parts[1]`, Strong's from `parts[2]`, display forms from
   `parts[3]`, with the existing validation (name-shaped, length > 1).
c. Harvest significances: the existing set (Named / Spelled / Spelled combined /
   Name combined / Aramaic / Greek) plus `(same form as previous)`, **`Group`**,
   `(same ref[s] with Variant)`, `LXX addition`. `Group` rows are the gentilics and
   carry their OWN Strong's (Christian → G5546, not the parent Jesus entry) — harvested
   keys prefer the row-level number over the entity's.
d. Display-form keys are added ONLY if absent from the primary roster (zero regression
   to existing resolution) and dropped when the same spelling appears under entities
   with different numbers (**149 ambiguous keys dropped**, measured).
e. The F1 person/place typing logic (row col-8 beats block header) is untouched.

Measured effect (full simulation on the pinned file + the live-db name dump):
- roster keys 2,824 → **4,331**
- numbered entities 2,687 → **2,862**
- of the 1,296 distinct unresolved proper-noun spellings in the dump, the fixed loader
  alone resolves **603** where today's ladder resolves 217.

## Proposed change 2 — variant map module (`scripts/tipnr_alias_variants.py`, NEW FILE)

**399 hand-checked entries** (`VARIANT_ALIASES`), consulted at ladder step 7 alongside
the existing hand `ALIASES` (which wins on overlap; the step only fires when the roster
misses, so a redundant entry is inert). New-file checkpoint: flagged per standing rule —
the alternative is ~400 lines appended to the inline dict; the module keeps the generated,
audited data separate from the hand-curated one.

Verification standard per entry (recorded per-line in
`docs/tickets/alias_decisions.txt`, the audit trail — every ACCEPT has its reason):
- 356 from the verse-constrained candidate sheet: entity identity at the attested verse
  (TIPNR identity line + reference), hand-read line by line. 16 REJECTS (wrong-sibling
  traps like gezrites≠Geshurites; LXX transliterations of common nouns — masek,
  chabratha — where mapping would be fabrication; junk keys from bad head picks).
  2 CAUTIONS: `shemesh` and `ramath` — name fragments that could denote 2–3 different
  places; parked for the audit session, not mapped (fragment uniqueness was checked
  corpus-wide for every fragment key; only unique ones were accepted).
- 43 TIPNR form-hits verified by exact reference match whose source rows sit under
  categories the loader fix intentionally does not harvest.

## Leave-list (`docs/tickets/alias_leave_list.txt`) — documented, spot-checkable

- Pile A (10): common-word keys from bad head picks — RC-1 re-heads those rows;
  never mapped.
- Pile B (209): LXX-only forms / research tail — no TIPNR form and no verse-constrained
  candidate. NOT force-mapped (R-2 rule: honest unmapped state; wrong > missing). Waits
  for the Greek-name migration or item-by-item research; the hand-check rejects are
  routed here.

## Count reconciliation (`docs/tickets/alias_final_counts.txt`)

1,296 distinct names in the dump → **1,075 resolvable** after loader fix + map;
**221 left**, every one in a documented pile (leave A/B, rejects, cautions);
**unexplained: 0** (measured with a full replica of the lookup ladder).

## Controls (fire before trusting, per standing rule)

- Ashchenaz @ 1Ch 1:6 → H813 (the original ticket control; TIPNR's own display column
  carries "Ashchenaz =KJV" with both refs — covered by change 1 alone).
- Christian (Act 11:26) → G5546 via the Group row's own number, NOT Jesus' G2424.
- Elias resolves from the roster natively (today it only survives via hand ALIASES).
- Negative: an ambiguous display form (one of the 149 dropped) must NOT resolve.
- Post-rebuild: double-star re-audit expects residue = the 221 documented leaves
  (+ the classes in blank_star_classes.md); anything else = STOP.

## Blast radius, stated plainly

The tipnr roster and its numbered-entity set grow. That feeds the proper-noun backfill,
PN surface/translit, and entity binding — all already re-run in the rebuild's dependent
chain, where the binding re-apply closes its own arithmetic (charter). This batch lands
WITH the rebuild, not as a live patch.

Verdict requested: approve changes 1 + 2, the new-file checkpoint, and the leave-list
dispositions.
