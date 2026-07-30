# LANE C — per-name context-run adjudication (210 census candidates, 2026-07-30)

**STATUS: SHIPPED 2026-07-30.** Verdict signed, gates A/B/C PASS (+206 rows exactly,
roster byte-identical), swap + reload done, 6/6 served checks. Only the 4 held slots
below remain open. Rollback: bible.db.pre_laneC.

For reviewer verdict BEFORE any evidence row lands. Audit ran per the hardened
standard (DRILL_lane_c.md): the frozen census's 210 PASS-candidates, per-name run
audit as the identity step. **Every one of the 210 slots was eyeballed against the
ABP verse text** (abp_texts/ diagnosis dump; genre-crossing names required it, and
the single-genre runs were cheap to include — no sampling shortcuts taken).
Reroute claims below were each re-verified against TIPNR's own raw records.

**CONTROL RECEIPT (run 2026-07-30, this session, before verdict):** screen re-run
clean; both Gilboa known-negatives correctly FAILED as candidates
(`# CONTROL OK: gilead 1Ch 10:12 -> COMPOUND-ROUTE` · `# CONTROL OK: gilead
1Sa 31:11 -> COMPOUND-ROUTE`); the script hard-aborts if either ever passes
(screen_lane_c.py:90). Full re-run output diffed byte-identical to the frozen
census — the audit read the output of a checker whose control fires.

Result: **201 approved / 5 reroutes to Lane B spelling / 4 held (incl. jair's
demotion to the compound lane)** — matches the piles below one-for-one.

**Genre-crossing subset of the 201 (every-slot audited, per hardening 3):**
15 names / 102 slots — jesus 38 · judah 20 · jacob 16 · pharaoh 8 · joshua 5 ·
hezekiah 4 · jeroboam 2 · tamar 2 · gog 1 · simeon 1 · baal 1 · uriah 1 ·
ahaz 1 · levi 1 · manasseh 1. (heber, eleazar, gilead also carried the flag but
their flagged slots are in piles 2/3, not the 201.) The remaining 99 slots are
single-genre narrative runs — also read slot-by-slot, exceeding the
sample-per-name minimum.

## Pile 1 — approved context-runs (201 slots, 56 names) — propose: land as
kind='witness', tag context-run, approved card sentence
Full per-slot list: `scripts/lane_c_context_runs_DRAFT.tsv` (generated from the
frozen census minus the 9 exclusions; NOT consumed by anything yet).
The big runs, with the run-level finding:
- **jesus 38** — every slot is Jesus of Nazareth (gospel narrative, Acts, epistle
  formulas, Rev 14:4). No Justus/Jesus (Col 4:11 screened ZERO) and no
  Joshua-in-Hebrews slot is in the pile.
- **judah 20** — all tribe/kingdom/land uses; TIPNR files tribe and kingdom under
  the patriarch's merged record (Judah@Gen.29.35-Rev spans to Rev), so the
  metonymy lands on the right record by TIPNR's own filing.
- **jacob 16** — Gen 29–48 = the patriarch; Isa 42:1 and Mal 3:7 = the nation.
  Both land on Israel@Gen.25.26-Rev because TIPNR merges Jacob into the renamed
  record, which is also its nation record — the metonymy worry dissolves.
- **elijah 15** (1Ki 17–2Ki 2), **joseph 11** (Gen 37–50), **saul 8** (1Sa),
  **jehu 5**, and the rest of the narrative runs: single obvious referent
  throughout, contexts checked slot by slot.
- **pharaoh 8** — TIPNR keeps per-era Pharaohs; each slot matched to its own:
  Gen 41:26 → Joseph's (Gen.37.36-Act); Exo 2:6 and 2:22 → the oppressor
  (Exo.1.11-Heb; 2:22 recalls the Pharaoh Moses fled, who dies at 2:23);
  Exo 3:18–18:9 → the Exodus Pharaoh (Exo.3.10-Rom).
- Notes inside the pile (approve-with-note): **gog Eze 38:17** — TIPNR's section
  label is [place] but the record IS Ezekiel's Gog (spans Ezk.38.2-Rev); filing
  quirk, identity right. **beor Num 24:22** — ABP/LXX addresses Beor where the
  Hebrew oracle is about Kain; within ABP's own text the referent is the
  passage's Beor (Balaam's father), the bind claims no more than that.

## Pile 2 — WRONG proposed identity, correct entity found (5 slots) — these are
Lane-B-shape spelling matches: TIPNR covers the exact verse with a
differently-spelled record, and the screen's name-match picked a different man.
Propose: land as spelling-equiv rows (Lane B doctrine), NOT context-run.
- **joshua Neh 8:7 → Jeshua@Ezr.2.40-Neh** (Levite, son of Azaniah; TIPNR covers
  Neh 8:7). The screen proposed Joshua son of Nun — wrong century; the screen
  passed only because son-of-Nun has coverage at Neh 8:17 ("Jeshua son of Nun").
- **heber 1Ch 8:22 → Eber@1Ch.8.22** (son of Shashak; TIPNR's own line:
  "Eber =ESV,NIV; Heber =KJV"). Proposed Heber@1Ch.8.17 is a different man
  (son of Elpaal) five verses up.
- **jehiel 2Ch 35:9 → Jeiel@2Ch.35.9** and **jeiel 2Ch 35:8 → Jehiel@2Ch.35.8**
  — a SWAPPED PAIR. ABP prints the two spellings opposite to the Hebrew: ABP
  35:8 reads "Jeiel" for the house-of-God ruler TIPNR has as Jehiel@2Ch.35.8
  (only there), ABP 35:9 reads "Jehiel" for the Levite ruler TIPNR has as
  Jeiel@2Ch.35.9 (only there). The screen's chapter filter proposed each for
  the other's verse.
- **rapha 1Ch 8:37 → Raphah@1Ch.8.37** (son of Binea, Saul's line; TIPNR covers
  the verse). The screen proposed Rosh@Gen.46.21-1Ch, Benjamin's son — wrong
  man by nine generations.

## Pile 3 — CLOSED 2026-07-30 (reviewer verdict in LANE_C_pile3_brief.md)
jair = demotion final (compound lane) · gilead Jos 22:11 = unbound permanent
(contested reading) · eleazar Ezr 8:16 = unbound permanent (unresolved
identification) · bunni Neh 10:14 = unbound permanent (AMBIGUOUS — Bani-v14/
Bunni-v15 seam, fails the one-candidate clause) · hodijah Neh 10:12 (Lane B
leftover, ruled with the set) = BIND APPROVED under the new narrowly-ruled
verse-offset class (scripts/verse_offset_witness.tsv) — SHIPPED 2026-07-30,
served capture green (receipt chain in LANE_C_pile3_brief.md). Rollback naming
note: pre_laneB/pre_laneC deleted under the single-rollback rule (ops.md
item 6); current rollback = bible.db.rollback, deep = bible.db.pre_greekhdr. Original routes kept below for the record.

## Pile 3 — HELD residue (4 slots), each routed (historical)
- **jair 1Ch 2:53** — compound fragment, the Gilboa shape: ABP renders
  Kiriath-jearim as "the city of Jair"; the token is a piece of the place name,
  not Jair the Manassite (the screen's candidate). Route: compound lane
  (Kiriath-jearim@Jos.9.17-Jer covers the verse).
- **gilead Jos 22:11** — contested reading: ABP prints "Gilead of Jordan" where
  the Hebrew reads geliloth ("districts of the Jordan"), and the verse itself
  puts the altar on the Canaan side. Region-Gilead is the only candidate but
  the passage doesn't force it. Route: contested-reading class.
- **eleazar Ezr 8:16** — TIPNR's Eleazar@Ezr.8.33 is "only mentioned at
  Ezr.8.33"; equating the 8:16 messenger with the 8:33 priest is an
  identification claim TIPNR doesn't make. Route: unresolved-identification.
- **bunni Neh 10:14** — versification-offset shape (like hodijah Neh 10:12):
  ABP's "sons of Bunni" sits where the Hebrew list splits Bani (v14) / Bunni
  (v15); TIPNR's Bunni@Neh.10.15 is at the neighbor verse. Route: offset class,
  check with hodijah at ruling time.

## DEMOTED KEYS — barred from Lane C permanently (reviewer-required log)
These five slot keys are demoted out of this lane; any future Lane C pass that
proposes a context-run bind for one of them is a regression. They may only land
via the Lane B spelling flow with the entity shown:
```
joshua|Neh|8|7    -> Jeshua@Ezr.2.40-Neh   (spelling-equiv)
heber|1Ch|8|22    -> Eber@1Ch.8.22          (spelling-equiv, TIPNR: "Heber =KJV")
jehiel|2Ch|35|9   -> Jeiel@2Ch.35.9         (spelling-equiv, swapped pair)
jeiel|2Ch|35|8    -> Jehiel@2Ch.35.8        (spelling-equiv, swapped pair)
rapha|1Ch|8|37    -> Raphah@1Ch.8.37-       (spelling-equiv)
```
(jair 1Ch 2:53 is NOT a Lane B reroute — it is a demotion to the COMPOUND lane,
Gilboa class, listed in pile 3.) All six keys are also hard-excluded in the DRAFT-TSV
generator, so regeneration can never re-admit them.

## Standing state
- Census stays FROZEN; screen control (Gilboa must-fail) untouched.
- Nothing lands until: reviewer verdict on the piles → JP checkpoint → scratch
  build → gate_pn_rulings (control first) → swap → worker reload → served capture.
- Rollback on PA remains bible.db.pre_laneB only.
