# LANE ③ — B2 eyeball dispositions (100 rows / 98 verses)

Adjudicated 2026-08-03 against `abp_texts/` source lines (evidence file:
`LANE3_b2_sources.txt`, one raw source line per row; list file: `LANE3_b2_list.txt`,
extracted verbatim from `audit_pn_star_verb_merge.py --class B --list`, B2 block).
No writes made from this lane. Every repair candidate below is hand-per-row,
JP-checkpointed, per the ticket (`docs/tickets/TICKET_pn_star_fix.md`).

`abp_texts/` is diagnosis-grade (pre-build source); anything byte-exact for an
actual repair comes from a PA dump of the built rows, not from these lines.

## Dispositions used

- **MERGE-gentilic** — real class-B merge the roster can't see: a people-word
  ("Romans", "Sadducees", "Israelitish") rides the carrier's number, the adjacent
  star is empty. Genuine repair candidate.
- **MERGE-name** — same defect, the name is a roster-silent spelling/variant
  (Michaiah, Helkiah, Bezaleel, Enos, Adoni-bezek…). Genuine repair candidate.
- **MERGE-possessive** — same defect via possessive tokenization ("Pharaoh's",
  "Lot's" — the apostrophe-s form never matches the roster). Repair needs an
  English-order call per row (the moved word reads "X's", not "X").
- **ARTIFACT-own-star** — NOT a defect: the name IS printed on its own star in
  the same clause (the 1Sa 25:42 class); the flagged empty star carries no
  English and nothing on the carrier is a name. Live state stands.
- **ARTIFACT-no-name** — NOT a repairable merge: no name word appears in the
  English of the clause at all (ABP left the word untranslated or used a
  pronoun); there is nothing to move. Live state stands.
- **RULED-ARTIFACT** — was flagged as a judgment call; ruled by JP (see the row).

## Tally

| Disposition | Rows |
|---|---|
| MERGE-gentilic | 22 |
| MERGE-name | 41 |
| MERGE-possessive | 8 |
| ARTIFACT-own-star | 13 |
| ARTIFACT-no-name | 15 |
| RULED-ARTIFACT (Gen 35:18, JP-ruled 2026-08-03) | 1 |
| **Total** | **100** |

Repair candidates total **71 rows / 69 verses** (2Ch 34:15 and Num 25:8 carry two
rows each). All 71 go to the hand-review lane; none are auto-writes.

## Per-row table

Row numbers match `LANE3_b2_sources.txt`. "Evidence" quotes the source line's
relevant span.

| # | Ref | Carrier | English on carrier | Disposition | Evidence / note |
|---|---|---|---|---|---|
| 1 | Act 2:10 | G1927 | Romans emigrating here, | MERGE-gentilic | `Romans emigrating here,G1927 G*` — star = Ῥωμαῖοι slot |
| 2 | Act 14:2 | G544 | Jews having resisted persuasion, | MERGE-gentilic | `Jews having resisted persuasion,G544 G*` |
| 3 | Heb 11:24 | G2364 | of Pharaoh's daughter, | MERGE-possessive | `of Pharaoh's daughter,G2364 G*` — star = Φαραώ |
| 4 | Luk 1:12 | G5015 | Zacharias was disturbed | MERGE-name | `Zacharias was disturbedG5015 G*` |
| 5 | Luk 1:18 | G2036 | Zacharias said | MERGE-name | `Zacharias saidG2036 G*` |
| 6 | Luk 17:32 | G1135 | Lot's wife! | MERGE-possessive | `Lot's wife!G1135 G*` |
| 7 | Mar 12:18 | G2064 | Sadducees came | MERGE-gentilic | `Sadducees cameG2064 G*` |
| 8 | Mat 9:11 | G1492,G3588 | the Pharisees seeing, | MERGE-gentilic | `the Pharisees seeing,G1492 G3588 G*` — "Pharisees" moves, "the"+"seeing" stay |
| 9 | Mat 12:41 | G435 | Ninevite men | MERGE-gentilic | `Ninevite menG435 G*` — star = Νινευῖται |
| 10 | 1Ch 1:50 | G599 | Baal-hanan died, | MERGE-name | `Baal-hanan died,G599 G*` — hyphen form, roster-silent |
| 11 | 1Ch 10:13 | G1905 | he asked | ARTIFACT-no-name | `he askedG1905 G*` — no name in English; nothing to move |
| 12 | 1Ch 19:7 | G4172 | their cities, | ARTIFACT-no-name | `their cities,G4172 G*` — no name in English |
| 13 | 1Ch 21:9 | G3708,G3588 | David's seer, | MERGE-possessive | `Gad,G* G3588 David's seer,G3708 G3588 G*` — Gad has its own star; the empty star = Δαυίδ |
| 14 | 1Ki 15:8 | G2837 | Abijam slept | MERGE-name | `Abijam sleptG2837 G*` |
| 15 | 1Ki 15:29 | G1401 | of his servant | ARTIFACT-own-star | `of his servantG1401 G* AhijahG*` — Ahijah printed on its own star |
| 16 | 1Ki 19:6 | G1914 | he looked. | ARTIFACT-no-name | `he looked.G1914 G*` — no name in English |
| 17 | 1Sa 11:15 | G2165 | was glad | ARTIFACT-own-star | `[2was gladG2165 G* 3thereG1563 1Saul]G*` — Saul on its own star |
| 18 | 1Sa 14:50 | G1135 | of Saul's wife | MERGE-possessive | `of Saul's wifeG1135 G*` |
| 19 | 1Sa 24:5 | G2588 | David's heart | MERGE-possessive | `[2struckG3960 1David's heart]G2588 G*` |
| 20 | 1Sa 24:17 | G2036 | he said | ARTIFACT-no-name | `he saidG2036 G* toG4314 David` — subject name untranslated in English |
| 21 | 1Sa 25:42 | G450 | rose up | ARTIFACT-own-star | `4rose upG450 G* 1Abigail],G*` — the handoff's named example |
| 22 | 2Ch 14:12 | G5343 | the Ethiopians fled. | MERGE-gentilic | `the Ethiopians fled.G5343 G*` |
| 23 | 2Ch 15:8 | G2722 | he took control of | ARTIFACT-no-name | `he took control ofG2722 G*` — no name in English |
| 24 | 2Ch 18:13 | G2036 | Michaiah said, | MERGE-name | `Michaiah said,G2036 G*` — roster-silent spelling |
| 25 | 2Ch 18:16 | G2036 | Michaiah said, | MERGE-name | same pattern |
| 26 | 2Ch 18:18 | G2036 | Michaiah said, | MERGE-name | same pattern |
| 27 | 2Ch 18:24 | G2036 | Michaiah said, | MERGE-name | same pattern |
| 28 | 2Ch 18:27 | G2036 | Michaiah said, | MERGE-name | same pattern |
| 29 | 2Ch 31:5 | G4121 | were superabundant | ARTIFACT-own-star | `[4were superabundantG4121 G* 1theG3588 2sonsG5207 3of Israel]G*` — Israel on own star |
| 30 | 2Ch 32:25 | G467 | he recompensed | ARTIFACT-own-star | `7he recompensedG467 G* 8to himG1473 1Hezekiah]G*` — Hezekiah on own star |
| 31 | 2Ch 34:15 | G611 | Helkiah responded | MERGE-name | `Helkiah respondedG611 G*` |
| 32 | 2Ch 34:15 | G1325 | Helkiah gave | MERGE-name | `Helkiah gaveG1325 G*` — second row, same verse |
| 33 | 2Ch 34:22 | G4198 | Helkiah went, | MERGE-name | `Helkiah went,G4198 G*` |
| 34 | 2Ki 7:15 | G4495,G3588 | the Syrians tossed | MERGE-gentilic | `the Syrians tossedG4495 G3588 G*` |
| 35 | 2Ki 18:16 | G4792.1 | cut off | ARTIFACT-own-star | `[4cut offG4792.1 G* 1HezekiahG*` — Hezekiah on own star |
| 36 | 2Ki 22:9 | G1525 | Shapan entered | MERGE-name | `Shapan enteredG1525 G*` — variant spelling |
| 37 | 2Sa 3:15 | G649 | Ishbosheth sent, | MERGE-name | `Ishbosheth sent,G649 G*` |
| 38 | 2Sa 10:16 | G649 | Hadarezer sent, | MERGE-name | `Hadarezer sent,G649 G*` |
| 39 | 2Sa 14:4 | G1135,G3588 | Tekoahite woman | MERGE-gentilic | `[3enteredG1525 1theG3588 2Tekoahite woman]G1135 G3588 G*` |
| 40 | 2Sa 15:30 | G2776 | his head | ARTIFACT-no-name | `his headG2776 G* being covered over,` — no name in English |
| 41 | 2Sa 19:37 | G5207 | my son | ARTIFACT-own-star | `ChimhamG* G3588 my sonG5207 G*` — Chimham on own star |
| 42 | Est 4:12 | G518 | Hatach reported | MERGE-name | `Hatach reportedG518 G*` |
| 43 | Est 9:6 | G615,G3588 | the Jews killed | MERGE-gentilic | `the Jews killedG615 G3588 G*` |
| 44 | Est 9:12 | G622,G3588 | The Jews destroyed | MERGE-gentilic | `The Jews destroyedG622 G3588 G*` — only "Jews" moves; capital 'The' stays |
| 45 | Exo 36:1 | G4160 | Bezaleel prepared, | MERGE-name | `Bezaleel prepared,G4160 G*` |
| 46 | Exo 37:1 | G4160 | Bezaleel made | MERGE-name | `Bezaleel madeG4160 G*` |
| 47 | Eze 23:5 | G1608,G3588 | Aholah fornicated | MERGE-name | `Aholah fornicatedG1608 G3588 G*` |
| 48 | Eze 26:2 | G2036 | Sor said | MERGE-name | `Sor saidG2036 G*` — Sor (Tyre), roster-silent |
| 49 | Eze 35:5 | G1096 | you became | ARTIFACT-no-name | `you becameG1096 G*` — no name in English |
| 50 | Ezr 2:63 | G2036 | Tirshatha spoke | MERGE-name | `Tirshatha spokeG2036 G*` — title printed as a name |
| 51 | Gen 5:9 | G2198 | Enos lived | MERGE-name | `Enos livedG2198 G*` |
| 52 | Gen 5:10 | G2198 | Enos lived | MERGE-name | same pattern |
| 53 | Gen 5:15 | G2198 | Mahalaleel lived | MERGE-name | `Mahalaleel livedG2198 G*` |
| 54 | Gen 5:16 | G2198 | Mahalaleel lived | MERGE-name | same pattern |
| 55 | Gen 11:14 | G2198 | Salah lived | MERGE-name | `Salah livedG2198 G*` |
| 56 | Gen 11:15 | G2198 | Salah lived | MERGE-name | same pattern |
| 57 | Gen 11:21 | G1080 | his procreating | ARTIFACT-no-name | `his procreatingG1080 G* G3588 SerugG*` — parallel verses put G1473 here; no name English on carrier; Serug has own star |
| 58 | Gen 26:20 | G91 | for they wronged | ARTIFACT-own-star | `Injustice,G93 G* for they wrongedG91 G1063` — the name (translated "Injustice") sits with its own star |
| 59 | Gen 35:18 | G3601 | of my Grief; | RULED-ARTIFACT | `SonG5207 of my Grief;G3601 G*` — JP ruling 2026-08-03 (applied per standing delegation): artifact, no repair. ABP translates the name Ben-oni rather than transliterating it; no roster-shaped token exists to move, and moving the translated phrase would invent a rendering the source never printed. Kin to ARTIFACT-no-name. Transliterating translated names would be a new feature lane, not this defect. |
| 60 | Gen 46:26 | G5207 | of Jacob's sons -- | MERGE-possessive | `of Jacob's sons --G5207 G*` |
| 61 | Gen 50:23 | G3382 | Joseph's thighs. | MERGE-possessive | `Joseph's thighs.G3382 G*` |
| 62 | Isa 19:2 | G1892 | Egyptians shall be roused | MERGE-gentilic | `Egyptians shall be rousedG1892 G*` |
| 63 | Isa 30:31 | G2274 | the Assyrians shall be vanquished, | MERGE-gentilic | `the Assyrians shall be vanquished,G2274 G*` |
| 64 | Jer 20:1 | G191 | Pashur heard | MERGE-name | `Pashur heardG191 G*` |
| 65 | Jer 20:3 | G1806 | Pashur led out | MERGE-name | `Pashur led outG1806 G*` |
| 66 | Jer 22:28 | G821 | Coniah is disgraced | MERGE-name | `Coniah is disgracedG821 G*` |
| 67 | Jer 24:5 | G599.3 | Jews being resettled | MERGE-gentilic | `Jews being resettledG599.3 G*` |
| 68 | Jer 26:21 | G191 | Urijah heard | MERGE-name | `Urijah heardG191 G*` |
| 69 | Jer 30:9 | G935 | their king | ARTIFACT-own-star | `[2DavidG* 3their kingG935 G* 1I will raise up]` — David on own star |
| 70 | Jer 38:8 | G1831 | Ebed-melech went forth | MERGE-name | `Ebed-melech went forthG1831 G*` |
| 71 | Jer 38:11 | G2983 | Ebed-melech took | MERGE-name | `Ebed-melech tookG2983 G*` |
| 72 | Jer 43:6 | G2641 | left behind | ARTIFACT-own-star | `[4left behindG2641 G* 1Nabuzar-adanG*` — name on own star |
| 73 | Jer 49:1 | G3880 | Milcom inherit | MERGE-name | `Milcom inheritG3880 G* G3588 Gad,G*` — Gad has own star; empty star = Milcom |
| 74 | Jer 49:3 | G3643.4 | Ai was destroyed. | MERGE-name | `Ai was destroyed.G3643.4 G*` |
| 75 | Jer 50:16 | G3162 | of the Grecian sword. | MERGE-gentilic | `of the Grecian sword.G3162 G*` |
| 76 | Jer 51:1 | G2730 | Chaldeans dwelling there | MERGE-gentilic | `Chaldeans dwelling there G2730 G*` |
| 77 | Jer 51:24 | G2730 | Chaldeans dwelling there | MERGE-gentilic | same pattern |
| 78 | Jer 51:41 | G234.1 | Sheshach is captured, | MERGE-name | `Sheshach is captured,G234.1 G*` |
| 79 | Job 1:15 | G1968 | Sabeans fell upon | MERGE-gentilic | `Sabeans fell uponG1968 G*` |
| 80 | Job 42:10 | G1715 | Job's before, | MERGE-possessive | `wasG1510.7.3 Job's before,G1715 G*` |
| 81 | Jos 5:15 | G4160 | Josua did | MERGE-name | `Josua didG4160 G*` — variant spelling |
| 82 | Jos 13:8 | G1473 | to them | ARTIFACT-own-star | `[2gaveG1325 G* 3to themG1473 1Moses]G*` — Moses on own star |
| 83 | Jos 22:34 | G2028 | he named | ARTIFACT-no-name | `he namedG2028 G*` — subject name untranslated in English |
| 84 | Jdg 1:6 | G5343 | Adoni-bezek fled; | MERGE-name | `Adoni-bezek fled;G5343 G*` |
| 85 | Jdg 1:7 | G2036 | Adoni-bezek said, | MERGE-name | `Adoni-bezek said,G2036 G*` |
| 86 | Jdg 5:26 | G4973.2 | with a hammer | ARTIFACT-own-star | `she struck [2with a hammerG4973.2 G* 1Sisera];G*` — Sisera on own star |
| 87 | Jdg 8:15 | G3854 | he came | ARTIFACT-no-name | `he cameG3854 G*` — subject name untranslated |
| 88 | Jdg 9:21 | G80 | his brother. | ARTIFACT-own-star | `of AbimelechG* G3588 his brother.G80 G*` — Abimelech on own star |
| 89 | Jdg 10:9 | G2346 | they afflicted | ARTIFACT-no-name | `they afflictedG2346 G*` — no name in English |
| 90 | Jdg 11:16 | G306.1 | their ascending | ARTIFACT-no-name | `their ascendingG306.1 G*` — no name in English |
| 91 | Jdg 16:19 | G2838.1 | she rested | ARTIFACT-no-name | `she restedG2838.1 G* him` — subject name untranslated |
| 92 | Lev 24:10 | G1135 | of an Israelitish woman, | MERGE-gentilic | `of an Israelitish woman],G1135 G*` |
| 93 | Neh 3:21 | G2902 | Meramoth repaired, | MERGE-name | `Meramoth repaired,G2902 G*` |
| 94 | Neh 7:65 | G2036 | Arthasastha said | MERGE-name | `Arthasastha saidG2036 G*` |
| 95 | Num 22:30 | G3688 | your donkey, | ARTIFACT-no-name | `your donkey,G3688 G*` — no name in English |
| 96 | Num 25:8 | G444,G3588 | Israelitish man | MERGE-gentilic | `Israelitish manG444 G3588 G*` — first occurrence |
| 97 | Num 25:8 | G444,G3588 | Israelitish man, | MERGE-gentilic | second occurrence, same verse |
| 98 | Num 25:14 | G444,G3588 | Israelitish man | MERGE-gentilic | `Israelitish manG444 G3588 G*` |
| 99 | Num 25:15 | G1135,G3588 | of the Midianitish woman | MERGE-gentilic | `of the Midianitish womanG1135 G3588 G*` |
| 100 | Psa 115:1 | G1656 | your mercy | ARTIFACT-no-name | `your mercyG1656 G*` — no name in English |

## LIVE-STATE RE-SCOPE (2026-08-06, reviewer-accepted — supersedes the 71-row lane size)

The 71 candidates above were adjudicated against SOURCE lines. Diffing the list
against the LIVE table (dump_lane3_rows.py, all 70 verses, pasted 2026-08-06)
showed **55 of the 71 rows already repaired in live** — the name sits on its own
star slot, the carrier keeps only its own English, no bracket. Mechanism
attributed: the **subject-name fold** (`scripts/fix_pn_subject_merge.py`, the
settled Subj-fold arc folded into the build), whose write shape (name on the
lower position, no bracket) matches all 55 exactly. Eliminations receipted: the
②-pass REFUSED these rows (committed plan file, e.g. `B 2Ch 18:13 no-name`) and
always writes brackets; `_split_compounds` refuses star targets;
`restore_frozen_pn` touches numbers only. Belt-and-braces receipt: the same dump
against `bible_pre_pnstar_20260803.db` (5-verse sample — 2Ch 18:13, Act 14:2,
Luk 1:12, Gen 5:9, Act 2:10) shows the same splits pre-ride, so this predates
the ②-ride.

**Reconciliation (reviewer-required):** closed 55 = gentilic 12 + name 40 +
possessive 3; still-merged 16 = gentilic 10 + name 1 + possessive 5;
55 + 16 = 71 ✓ (22/41/8 by class ✓).

**CLOSED — already repaired by the subject-name fold, verified against the live
dump 2026-08-06 + rollback sample:**
- Gentilic (12): Act 2:10 · Act 14:2 · Mar 12:18 · Mat 12:41 · 2Ki 7:15 ·
  Est 9:6 · Est 9:12 · Isa 19:2 · Jer 24:5 · Jer 51:1 · Jer 51:24 · Job 1:15
- Name (40): Luk 1:12 · Luk 1:18 · 1Ch 1:50 · 1Ki 15:8 · 2Ch 18:13 · 2Ch 18:16 ·
  2Ch 18:18 · 2Ch 18:24 · 2Ch 18:27 · 2Ch 34:15 (both rows) · 2Ch 34:22 ·
  2Ki 22:9 · 2Sa 3:15 · 2Sa 10:16 · Est 4:12 · Exo 36:1 · Exo 37:1 · Eze 26:2 ·
  Ezr 2:63 · Gen 5:9 · Gen 5:10 · Gen 5:15 · Gen 5:16 · Gen 11:14 · Gen 11:15 ·
  Jer 20:1 · Jer 20:3 · Jer 22:28 · Jer 26:21 · Jer 38:8 · Jer 38:11 · Jer 49:1 ·
  Jer 49:3 · Jer 51:41 · Jos 5:15 · Jdg 1:6 · Jdg 1:7 · Neh 3:21 · Neh 7:65
- Possessive (3): Luk 17:32 · Gen 50:23 · Job 42:10

**STILL MERGED IN LIVE — the hand lane's real scope (16 rows / 15 verses):**
- Gentilic (10): Mat 9:11 · 2Ch 14:12 · 2Sa 14:4 · Isa 30:31 · Jer 50:16 ·
  Lev 24:10 · Num 25:8 (×2) · Num 25:14 · Num 25:15
- Name (1): Eze 23:5
- Possessive (5): Heb 11:24 · 1Ch 21:9 · 1Sa 14:50 · 1Sa 24:5 · Gen 46:26

The survivors are exactly the shapes the fold cannot reach: name mid-cell, an
intervening blank article slot, inside an existing bracket, or possessive
("X's") wording. Mat 27:26 stays its own separate item (A/unattested).

## REPAIR LEDGER (2026-08-07 — the hand lane EXECUTED, reviewer verdict-gated per row)

All 16 survivors + Mat 27:26 repaired live via the pinned re-runnable patches
(`scripts/fix_lane3_star_merges.py` + three fixes files; house 2-slot/bracket
shape, english/english_head/greek_pos/bracket_id only, numbers and positions
never touched; every apply preceded by a pasted dry-run with prose-render and
contiguity checks, reviewer verdict per row):

1. `lane3_star_fixes.json` — the 10 gentilics (9 verses; Num 25:8 ×2). Applied
   2026-08-07, 0 skipped.
2. `lane3_star_gapfix.json` — follow-up: the gentilic batch left interior blank
   slots OUTSIDE four verses' brackets; chip/interlinear group only CONSECUTIVE
   same-bracket runs (`groupForGreekMode`), so those verses mis-ordered there
   (prose unaffected — it groups across gaps). JP's app check caught it; five
   gap slots got the bracket mark (the build's own interior-blank-member shape).
   The dry-run now carries a standing CONTIGUITY CHECK so the class is caught
   mechanically.
3. `lane3_star_fixes2.json` — Eze 23:5 + the 5 possessives (apostrophe-s as
   printed) + Mat 27:26 ('scourging' → G5417; per-row page evidence Mar 15:15,
   quoted verbatim in the file's header). Applied 2026-08-07, 0 skipped.

Re-run order after any future words rebuild: fixes → gapfix → fixes2 (each is
state-guarded; a skip means already-applied or state drifted — read the reason).

**Queued out of this lane (reviewer-ruled):**
- ②-pass gap census: the pass's 194 cross-blank B-writes share the unmarked
  interior-blank geometry, so those live verses likely mis-order in
  chip/interlinear today. Own census + dry-run + ruling; same one-column fix.
- Gentilic PN cards read as places (Assyrians → Assyria map); polish to
  "people of [region]" wording. TODO item, not a defect.

## Notes for the repair lane (all JP-checkpointed, hand-per-row)

1. **The 71 repair candidates split three ways** and probably want three passes of
   hand review: gentilics (22 — the cleanest: one capitalized people-word moves to
   the star), roster-silent names (41 — same shape as gentilics), possessives
   (8 — each needs an English-wording call: the star would read "Pharaoh's" /
   "Lot's", which is how ABP itself prints possessive names elsewhere, e.g.
   `Ephraim'sG*` in Gen 50:23).
   **Possessive wording default (JP, 2026-08-03): the moved word keeps the
   apostrophe-s exactly as printed** — source fidelity, no made-up base form.
   Decided once; the per-row checkpoint only overrides exceptions.
2. **Row 59 (Gen 35:18)** — ruled artifact, no repair (see the row for the
   reason). Closed.
3. The ARTIFACT rows (28) confirm the handoff's expectation: the empty star either
   sits beside a name that already has its own star, or beside a clause where ABP
   never printed the name in English. Nothing to repair; import_tipnr fills the
   star's identity as always.
