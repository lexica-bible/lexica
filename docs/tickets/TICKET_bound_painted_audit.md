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

## Loud-refusal list
- **1Ki 4:13 gilead p[4, 12]** — p4 sits inside the compound place name "Ramoth
  Gilead" (the city) while p12 is the REGION Gilead; both painted
  Gilead@Gen.31.21-Zec (region). RULED (reviewer + JP, 2026-08-08): p4's paint is
  wrong, but do NOT one-off it — tagged as a known member of the COMPOUND-NAME
  class; the fix ships with the compound-number/chip-merge lane (TODO.md, JP
  raises) so the fix shape stays uniform. Stays flagged, no write here.

## Resolved flags (batch 1)
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
