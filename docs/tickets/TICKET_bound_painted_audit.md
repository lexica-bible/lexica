# TICKET — Bound-painted audit lane (opened 2026-08-08)

Follow-on of the word-position binding lane (CLOSED 8/8 — TICKET_wordpos_binding.md).
Class: verses where a verse-grain render bind EXISTS and 2+ same-name slots sit in the
verse — the ONE bind paints every same-name slot, and wrong paints hide here.
Last sizing: 1,470 slots / 713 groups (separate bucket of census_wordpos_multi.py).
R2 ruling (banked 8/7): these are BOUND — users see something today, possibly wrong;
a change can break a working display. Risk posture is therefore stricter than the 96.

## Charter
- **Worklist = a FRESH run of `scripts/census_wordpos_multi.py` on PA** (separate
  "bound-PAINTED" bucket). No prior list is reused — the list changes with bind batches.
  Census controls (malchiah bucket-C / mary in-lane / jesus absent) must print OK;
  exit 2 = stop and look, the output is not trustworthy.
- **Discovery-time carve-out in force** (rider 3): any wrongly-painted neighbor found
  while adjudicating a group is recorded HERE, in that group's verdict row, at that
  moment — never re-derived later. (Zero carve-out entries were banked from the wordpos
  lane — prereg close block says "none are bound-painted carve-outs".)
- **OUT of scope, do not touch:**
  - Elnatham Ezr 8:16 p15 — held as in-verse variant-spelling APPENDIX candidate only.
  - Chapter-grain 5 (azariah/joash/benaiah/harim) — parked; per R3 any fold-in
    RETURNS TO THE REVIEWER, never automatic.

## Inherited guards (every slot, every batch — from the wordpos lane, unchanged)
- **Precedence** — slot rows land only where they are needed; a collision with an
  existing slot row = stop-and-look, never overwrite.
- **Stale-name check** — TSV `name` = the printed english_head AT the slot; a mismatch
  vs the live words row = refuse (rebuild-moves-positions tripwire).
- **Referent-kind check** — rows may point at PLACE/group entities (Cushi = the land
  Cush; Judah = the people via the patriarch); never assume "two referents = two people".
- **Shared contiguity classifier** — `scripts/bracket_contiguity.py`, imported, never
  re-implemented; bracket-adjacent groups get per-mode display evidence (chip order,
  not prose — prose passing proves nothing about chip mode).
- **Evidence classes PINNED** (DESIGN_wordpos_binding.md), including
  `source-order-filing` valid ONLY at its three conditions. Cross-verse parallel-list
  inference stays BANNED (jeiel precedent) without a new ruling.
- **Candidate rosters MANDATORY per group, near-match** — exact/prefix/near-0.80,
  never exact-only (4 misses in the wordpos lane). **No write without the roster
  attached to the group's record.**
- **Codicil 2** — automated gates are position-integrity only; entity correctness has
  exactly one gate: the reviewer's per-row verdict.
- **paint-override marker (STANDING RULE, reviewer conditions 1+2, 2026-08-08):**
  a slot-ruling row may land OVER an existing verse-grain bind ONLY when flagged
  `paint-override`, and the marker is valid ONLY on a row whose ruling entry
  references a banked reviewer verdict — never on CC's own authority. Every
  override prints a loud OVERRIDE line naming old paint -> new entity, so the
  pasted dry-run output is self-auditing. Default G3 behavior (refuse on
  collision) is unchanged for unflagged rows.

## Refusal discipline
Anything that trips a guard or lands ambiguous goes on the **loud-refusal list** below
for JP/reviewer review — never a best-guess write. Verdict gate applies throughout:
JP-run dry-run paste → verdict (expected beside actual) → apply.

## Status
- [x] Fresh census run on PA (JP, 2026-08-08) — all 3 controls OK; counts match the
      parked sizing exactly (1,470 slots / 713 groups; lane figure 96/47/46/28
      unchanged, so the 8/8 apply moved nothing). Bucket C = the malchiah pair only.
- [x] Worklist frozen: docs/tickets/boundpainted_worklist_20260808.txt (713 lines,
      1,470 slots — counts re-verified against the header). PENDING: JP's byte-level
      diff of the repo file vs his PA census file (transcription check).
- Batch plan: file order, 100 groups per batch (batch 8 = 13). Checkpoint to JP
  after each batch; verdict gate on anything that would write.
- Evidence dump per batch: scripts/dump_boundpainted_batch.py (read-only; prose +
  slot rows + the paint row w/ referent kind + existing slot binds + near-match
  roster per group).
- [ ] Batch adjudication (rosters attached per group)
- [ ] Loud-refusal list → review
- [ ] Dry-run → verdicts → apply → deploy → 3-mode verification

## Batch 1 — ADJUDICATED 2026-08-08 (groups 1-100, 1Ch 1:18 → 1Ki 15:18 asa)
Evidence + rosters: receipts_boundpainted_batch1.txt (JP-run dump, 100 groups,
0 red flags from the script; byte-verified vs PA). Verdict: **98 KEEP / 2 FLAGGED,
zero writes** — no slot binds proposed, so no dry-run/apply cycle for this batch.
- KEEP basis: every kept group's slots are the same referent repeated in one verse
  (genealogy chains "X fathered N, and N fathered Y"; narrative repeats of one
  actor; tribe/kingdom refs riding the patriarch entity per the eponym doctrine).
  Notable correct pairs where TWO entities of one name exist and the verse-grain
  binds already picked the right one per verse: the two Amariahs (1Ch 6:7 vs 6:11),
  the two Zadok lines (6:8 vs 6:12), Hiram the king (1Ki 5:1/9:11) vs Hiram the
  craftsman (7:40), Levite Kish 1Ch 24:29 (not Saul's father).
- KEEP-WITH-NOTE (no action, recorded): 1Ch 16:38 obed — a two-Obed-edom reading
  exists (musician vs gatekeeper son of Jeduthun) but TIPNR carries ONE entity, so
  no rival candidate; TIPNR equation stands. · 1Ki 4:5 nathan — traditional reading
  is the same Nathan fathering both officers; no positive evidence of two. ·
  1Ki 11:18/11:20 pharaoh — per-reign Pharaoh disambiguation is the PARKED pile V
  (out-of-scope flag line only; both slots same referent within each verse).

## Batch 2 — ADJUDICATED 2026-08-08 (groups 101-200, 1Ki 15:22 → 1Ti 1:1)
Evidence + rosters: receipts_boundpainted_batch2.txt (JP-run dump, 100 groups, 0 red
flags; verified 100/0 on PA and local). Verdict: **100 KEEP / 0 flagged, zero writes.**
- All groups are one referent repeated: narrative repeats (Saul ×~40, Jonathan,
  Ahab/Elijah/Obadiah/Jehoshaphat runs, Agag, Michal, Ahimelech, Eliab, Jesus ×5),
  tribe refs on the patriarch entity (1Sa 9:1 benjamin), Baal the deity twice in
  one verse (1Ki 16:32, 18:26 — kind 'other', correct).
- KEEP-WITH-NOTE: 1Ki 20:33 hadad — ABP prints Ben-hadad as "son of Hadad"; both
  slots are that one compound reference, painted Ben-hadad@1Ki.15.18-Jer. TIPNR
  carries ONE Ben-hadad entity spanning the Asa-era and Ahab-era kings (the I/II
  split is a scholarly question TIPNR doesn't make), so no rival candidate —
  TIPNR equation stands, same class as the batch-1 Obed-edom note.

## Batch 3 — ADJUDICATED 2026-08-08 (groups 201-300, 2Ch 4:11 → 2Ki 22:8)
Evidence + rosters: receipts_boundpainted_batch3.txt (JP-run dump, 100 groups, 0 red
flags; verified 100/0). Verdict: **95 KEEP / 5 WRONG-PAINT groups (7 slots) —
proposals below, NO writes until reviewer verdict + dry-run (Codicil 2 + verdict gate).**
- KEEP basis: same-referent repeats (Hezekiah ×7, Elijah, Jehu, Baal ×6, Jezreel the
  city ×4, Judah kingdom folds, Shaphan, Jehoiada, Ahaziah-of-JUDAH ×6 incl. 2Ki 9:23
  and 10:13). The verse-grain binder was referent-aware where a verse holds only ONE
  of the two same-named kings: 2Ch 22:5/22:7, 2Ki 8:28, 9:14, 9:16, 9:21 all correctly
  carry Joram-of-ISRAEL; 2Ch 4:11 correctly the craftsman Hiram; Joash 2Ki 13:13/13:25
  correctly Israel's Joash; urijah→Uriah is the accepted name-equation class.
- The 5 wrong-paint groups are all MIXED verses — both Jehorams present, one paint:

### PROPOSED slot binds (batch 3) — awaiting reviewer per-row verdict, then dry-run
Entities: JUDAH = Jehoram@1Ki.22.50-Mat (son of Jehoshaphat) · ISRAEL =
Joram@2Ki.1.17-2Ch (son of Ahab). Evidence class throughout: kin-in-verse
(the epithet printed adjacent to the slot). Rosters: in the batch-3 receipt.
1. **2Ch 22:6 jehoram p[2,28,34]** painted JUDAH. Propose: p2 → ISRAEL (the king
   wounded at Ramoth, treated in Jezreel — continues 22:5's Israel narrative);
   p28 KEEP JUDAH ("Ahaziah son of Jehoram, king of Judah"); p34 → ISRAEL
   ("Jehoram son of Ahab in Jezreel").
2. **2Ki 1:17 jehoram p[11,27]** painted JUDAH. Propose: p11 → ISRAEL ("Jehoram
   the brother of Ahaziah reigned instead of him" — TIPNR first-names this entity
   at this very verse); p27 KEEP JUDAH ("Jehoram son of Jehoshaphat king of Judah").
3. **2Ki 8:16 jehoram p[4,10]** painted JUDAH. Propose: p4 → ISRAEL ("Jehoram son
   of Ahab king of Israel"); p10 KEEP JUDAH ("Jehoram son of Jehoshaphat king of
   Judah reigned").
4. **2Ki 8:25 jehoram p[4,12]** painted JUDAH. Propose: p4 → ISRAEL ("Jehoram son
   of Ahab king of Israel"); p12 KEEP JUDAH ("Ahaziah son of Jehoram king of Judah").
5. **2Ki 8:29 jehoram p[4,31,38]** painted JUDAH. Propose: p4 → ISRAEL ("king
   Jehoram returned to be treated in Jezreel" — the Ramoth-wounded king; parallel
   of 2Ch 22:6); p31 KEEP JUDAH ("Ahaziah son of Jehoram king of Judah");
   p38 → ISRAEL ("Jehoram son of Ahab in Jezreel").
Fallback per row if refused: floor stays as-is (verse-grain paint), never a second
guess in-flight.

**REVIEWER VERDICT (2026-08-08, banked verbatim — all 7 changes + all 5 keeps
APPROVED):** "Row 1 — 2Ch 22:6 p2 → ISRAEL: APPROVED. The role clause stands on its
own, but it's also corroborated inside the same verse: the wounded king being visited
is named at p34 as 'Jehoram son of Ahab... for he was infirm.' … Row 4 — 2Ki 1:17
p11 → ISRAEL: APPROVED. … the verse's whole point is that these are two different
Jehorams. TIPNR first-naming the Israel entity at this exact verse seals it. …
Row 6 — 2Ki 8:16 p4 → ISRAEL: APPROVED. This one's actually patronym+title on the
slot itself … All 7 changes approved, all 5 explicit keeps approved. Fallback
accepted as stated for any row that fails at apply time — floor, no second guess."
CORRECTION per reviewer: the role-clause pair is 2Ch 22:6 p2 and **2Ki 8:29 p4**
(2Ki 8:16 p4 carries a patronym on the slot itself) — labels above and in the TSV
rationale now match the ruling.
STAGED: 7 rows appended to scripts/pn_slot_rulings.tsv (KEEP slots get no row per
lane doctrine — verse-grain paint already serves Judah correctly there).

**APPLIED + LIVE-VERIFIED 2026-08-08 — batch-3 fixes CLOSED.**
Dry-run arc: run 1 FAIL (G3 refused all 7 — guard chartered for unbound verses;
this lane corrects bound ones) → paint-override mechanism designed, reviewer
APPROVED with conditions 1+2 (banked above) → run 2 FAIL (G4 same-entity pairs
unflagged; flags grounded in the verdict's own one-referent finding) → run 3
PASS (7 OVERRIDE lines, 102/0). JP backup taken (bible.db.pre_boundpainted_b3)
→ --apply: 7 OVERRIDEs, `pn_slot_binding written: 102 rows` → table read shows
exactly the 7 jehoram rows → LIVE serve verified via API: 2Ki 8:16 pos4 =
Joram@2Ki.1.17-2Ch "king of Northern Israel, son of Ahab and Jezebel"
(slot-ruled), pos10 = Jehoram of Judah rich card (verse-grain, byte-same path);
Mary Mat 27:61 pos3/pos9 both slot-ruled to their own entities — no regression.
No deploy needed (serve path live since the wordpos lane; data-only change).

## Batch 4 — ADJUDICATED 2026-08-08 (groups 301-400, 2Ki 22:8 → Est 3:3)
Evidence + rosters: receipts_boundpainted_batch4.txt (JP-run dump, 100 groups, 0 red
flags; verified 100/0). Verdict: **100 KEEP / 0 flagged, zero writes.**
- Same-referent narrative repeats throughout (Joab ×~15, Amnon, Uriah ×5, Daniel ×7,
  Shaphan, Mephibosheth, Saul-of-Gibeah runs, Jesus ×5, Judah/Benjamin/Levi/Gad
  patriarch folds, Hebron/Shechem places). 2Ki 23:35 pharaoh ×3 correctly carries the
  per-reign Neco@2Ki.23.29-Jer entity. 2Sa 18:21 joab sits beside the wordpos lane's
  cushi slot-binds with no collision.
- KEEP-WITH-NOTE (accepted name-equation class, both slots one man in each):
  Act 9:4/22:7/26:14 "Saul, Saul" → Paul@Act.7.58-2Pe · Act 7:8 jacob →
  Israel@Gen.25.26-Rev · Est 1:1 artaxerxes (LXX name) → Ahasuerus@Ezr.4.6-Dan.

## Batch 5 — ADJUDICATED 2026-08-08 (groups 401-500, Est 3:4 → Gen 45:27)
Evidence + rosters: receipts_boundpainted_batch5.txt (JP-run dump, 100 groups, 0 red
flags; verified 100/0). Verdict: **100 KEEP / 0 flagged, zero writes.**
- Same-referent throughout: Mordecai, Jacob runs (Israel entity fold), Joseph runs,
  Sarah ×5, Noah ×3, Gen 36 Edomite genealogies (aholibamah→Oholibamah equation;
  Anah verses consistent with the wordpos Dishon ruling's parent chain).
- Verified referent-aware verse-grain work: Pharaohs PER-REIGN correct (Exo 2:15
  oppression-era @Exo.1.11 · Exo 7-18 exodus @Exo.3.10 · Gen 12:15 Abraham's ·
  Gen 40-45 Joseph's @Gen.37.36 · Eze 32:31 Hophra) · Cain-line vs Seth-line Enoch
  (Gen 4:17 vs 5:22) and Lamech split correctly · Haran person (Gen 11:27) vs Haran
  the city (Gen 11:32, place kind) · Gen 34:26 Shechem the MAN (@Gen.33.19-).
- NOTE (no action): Gog @Ezk.38.2-Rev carries referent kind 'place' — TIPNR's own
  filing (binds may point at non-person entities, standing tripwire); both slots
  one referent either way.

## Batch 6 — ADJUDICATED 2026-08-08 (groups 501-600, Gen 46:2 → Joh 1:42)
Evidence + rosters: receipts_boundpainted_batch6.txt (JP-run dump, 100 groups, 0 red
flags; verified 100/0). Verdict: **99 KEEP / 1 flagged (below), zero writes.**
- Same-referent keeps: Jacob/Joseph/Pharaoh Gen 46-50 runs, "Jacob, Jacob!" doubles,
  Jeremiah/Baruch/Job runs, Judah kingdom folds, Jdg 9 Shechem-the-city groups
  (9:6/9:20/9:23/9:26), Gilead region groups (Jdg 10-12). Referent-aware wins
  verified: Abimelech = Gideon's son @Jdg.8.31-2Sa (not the Gerar kings) · Joash =
  Gideon's father @Jdg.6.11- · Micah = the Judges figure @Jdg.17.1- · Ishmael
  Jer 41:9 = the assassin @2Ki.25.23-Jer (not Abraham's son) · Seraiah @Jer.51.59
  own entity · pashur→Pashhur accepted equation. Gen 46:20 manasseh sits beside the
  wordpos Machir slot-binds with no collision.

## Batch 7 — ADJUDICATED 2026-08-08 (groups 601-700, Joh 4:50 → Num 23:23)
Evidence + rosters: receipts_boundpainted_batch7.txt (JP-run dump, 100 groups, 0 red
flags; verified 100/0). Verdict: **100 KEEP / 0 flagged, zero writes.**
- NT narrative repeats (Jesus ×~14, Peter, John the Baptist, Herod = Antipas
  @Mat.14.1-Act on all three verses, James = Zebedee's), Joshua ×~20, Numbers-2
  tribal camps + Mic/Mal/Num Jacob-Judah nation folds, Miriam/Abiram/Eleazar.
- Mat 1 genealogy pairs all correct royal-line entities — its joram = the JUDAH
  Jehoram@1Ki.22.50-Mat (consistent with the batch-3 slot fixes), abia→Abijah,
  salathiel→Shealtiel, late-genealogy names on their own Mat.1.x entities.
- Jos 17:1 manasseh sits beside the wordpos person-vs-region gilead slot binds
  (p16 Gilead@Num.26.29 the man / p23 the region) — no collision.
- KEEP-WITH-NOTE (accepted equation class): Neh 12:11 jonathan →
  Johanan@Neh.12.11- (TIPNR files the high-priest line under Johanan).

## Batch 8 — ADJUDICATED 2026-08-08 (groups 701-713, Num 26:12 → Zep 2:7)
Evidence + rosters: receipts_boundpainted_batch8.txt (JP-run dump, 13 groups, 0 red
flags). Verdict: **13 KEEP / 0 flagged, zero writes.** Census tribal lists +
Jesus ×3 + Judah folds. Per-verse referent care confirmed again: Ard@Num.26.40
(Bela's son — distinct from Gen.46.21's Ard, Benjamin's son) · Naaman@Num.26.40-1Ch
(not the Syrian) · Jair@Num.32.41 (not the judge) · Ram@Rut.4.19 (not Jerahmeel's
brother). Machir group beside two Gilead slot-binds, no collision.

## ═══ AUDIT PHASE COMPLETE 2026-08-08 — all 713 groups adjudicated ═══
**Final tally (post Jdg 9:28 ruling, LANE FULLY CLOSED 2026-08-08): 707 KEEP ·
5 groups FIXED (7 slots, applied + live-verified, batch 3's mixed-Jehoram verses) ·
1 flag PARKED with the compound-name lane (1Ki 4:13 gilead).** Every batch receipt archived
(receipts_boundpainted_batch1-8.txt) with rosters attached per group; every
batch checkpointed to JP; zero best-guess writes. Elnatham Ezr 8:16 p15 appendix
candidate and the chapter-grain 5 remain PARKED per charter (untouched).
Mechanism legacy: the paint-override marker (reviewer conditions 1+2) is now a
standing part of the slot-binding guard stack.

## Loud-refusal list
- **1Ki 4:13 gilead p[4, 12]** — p4 sits inside the compound place name "Ramoth
  Gilead" (the city) while p12 is the REGION Gilead; both painted
  Gilead@Gen.31.21-Zec (region). RULED (reviewer + JP, 2026-08-08): p4's paint is
  wrong, but do NOT one-off it — tagged as a known member of the COMPOUND-NAME
  class; the fix ships with the compound-number/chip-merge lane (TODO.md, JP
  raises) so the fix shape stays uniform. Stays flagged, no write here.

## LESSONS BANKED AT CLOSE (reviewer-authored 2026-08-08 — standing law for
## future correction lanes; also in memory feedback_correction_lane_lessons)
1. **Expected pictures walk EVERY guard, not just the new logic.** Both dry-run
   fails were rows predicted on their merits without simulating the full guard
   stack (G3's opposite-lane assumption; G4's missing flag). Walk each row
   through every guard on paper before posting the picture.
2. **Correction lanes invert creation-lane assumptions — audit inherited guards
   for the inversion AT CHARTER TIME.** Any lane correcting existing data opens
   with: which standing guards assume the data is absent?
3. **Run the referent authority's per-token ref-list test BEFORE escalating a
   flag** — it ruled Elkanah and Shechem, once each direction, by grep. The flag
   paste arrives with that evidence attached (the Shechem paste is the template).
4. **Negative-space verification is evidence.** Confirming the single-Jehoram
   neighbor verses were already right bounded the blast radius — belongs in
   every fix proposal.
5. **Overrides: loud, marked, externally authorized — never default.** The
   paint-override shape (explicit marker + structurally-required banked reviewer
   verdict + self-auditing output line) is the reusable pattern for any
   guard-bypass mechanism.

## Resolved flags
- **Jdg 9:28 shechem p[12, 30] — KEEP the city paint with contested-reading note
  (reviewer verdict 2026-08-08, evidence-ruled by the Elkanah-standard ref-list
  test).** TIPNR files BOTH tokens of this verse (Jdg.9.28a + 9.28b) on the CITY's
  ref list (Shechem@Gen.12.6-Act, TIPNR.txt:33477); the MAN's list
  (Shechem@Gen.33.19-, :21560) covers Gen 33:19 + Gen 34 only. The Hamor record
  (:8514) faced the exact ambiguity and distinguishes "father of H7927H [the man];
  founder of H7927G [the city]" — 9:28 filed under founder-of-city. CONTESTED
  ALTERNATIVE on record: Gaal's speech as Hivite-ancestry rhetoric pointing at the
  Genesis man (the reviewer's literary lean, overruled by the source's own filing,
  applied symmetrically with Elkanah). Actionable if TIPNR ever refiles; no write.
- **1Ch 6:26 elkanah p[0, 1] — KEEP with contested-reading note (evidence-ruled
  2026-08-08, reviewer's roster test).** TIPNR carries TWO Elkanahs in the
  neighborhood but files exactly ONE at verse 6:26: Elkanah@1Ch.6.26- (H0511J,
  son of Ahimoth, father of Zophai; refs 6:26+6:35 — TIPNR.txt:6932). The
  neighboring Elkanah@1Ch.6.25- (H0511I, son of Shaul, father of Amasai) lists
  refs 6:25+6:36 — verse 26 NOT among them. So the source reads the doubled name
  resumptively (KJV "As for Elkanah: the sons of Elkanah — Zophai"), not as a
  father-son chain: one referent, both slots, current paint correct. The chain
  reading stays recorded here as the contested alternative; revisit only if the
  referent authority changes.

## Carve-outs discovered this lane
(none yet — batch 1 surfaced no wrongly-painted neighbors outside its own groups)
