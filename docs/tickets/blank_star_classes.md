# Blank star-row classes — the 477 rows, classified (2026-07-16)

Generated from the live-db dump (blank English on a `strongs='*'` row) plus the cell
immediately before each. Classification per `REVIEW_rc2_rereview.md`; reviewer-approved
dispositions:

- **CAP (148 rows)** — capitalized non-roster name LEADS the previous cell. FIXED by the
  RC-2 capitalized-lead fallback in `fix_pn_subject_merge.py` at the next rebuild; this
  list is the RECONCILIATION BASELINE (dry-run capfall count must reconcile against it,
  shortfall itemized, before --apply).
- **MID (64 rows)** — name buried mid-phrase in the previous cell. NOT batch-fixed
  (reordering judgment); deferred to the audit session per reviewer ruling.
- **NOCAP (40 rows)** — no name in the English at all (ABP renders the name as a pronoun
  or folds it away; e.g. 1Ch 10:13 `he askedG1905 G*` = LXX "Saul asked", English "he").
  CORRECT AS BLANK — expected residue class, source-verified.
- **EMPTY (225 rows)** — the previous cell is ALSO empty (bare article+name Greek slot
  pairs the English never voices; e.g. 1Ki 1:43 `...to reign.G936 G3588 G*`,
  Gen 11:21 `his procreatingG1080 G*` = Greek repeats "Reu", English says "his").
  CORRECT AS BLANK — same disposition.

Source spot-checks are quoted from `abp_texts/` (diagnosis-grade pre-build source).
Whether NOCAP/EMPTY rows should carry a Strong's number with no English is an
audit-session ruling, not a build fix.

## R-1 run outcome (2026-07-16, reviewer-cleared gate 2; AMENDED same day after the
## gate-5 sweep) — CAP resolves 137 + 11

The head-word rebuild's in-build split fixes **137** of the CAP 148 (capfall count;
2,299 old-mechanism + 137 = an expected build total of **2,436**). The remaining
**11 stay blank by design** — CAP-classified on look (capitalized lead) but not
mergeable in shape. The 11th, found by the gate-5 sweep on the second build:
**Isa 41:14 | 4** — the previous cell is "O Israel, very few in number!"; the lead
is the VOCATIVE "O", not a name, and the one-token peel put "O" on the name slot.
"o" added to `_FUNCTION_LEAD` (fix_pn_subject_merge.py) so the row stays merged =
live's exact state; a vocative-aware peel is a parked improvement.
Verified per-row against the code + ABP source (`check_blank_star_residue.py` is the
measuring tool; control-tested on live: 148/0/0/0):

- **Single-word cells (8)** — no verb merged on, nothing to split; the splitter's
  candidate rule requires two words. Name already visible; only the neighbor
  placeholder is blank (same audit-session question as NOCAP/EMPTY):
  Gen 22:21 | 1 (Huz) · 2Sa 12:9 | 14 (Uriah) · 2Sa 23:1 | 8 (Trustworthy) ·
  Gen 26:20 | 21 (Injustice) · Gen 26:21 | 17 (Hatred) · Gen 26:22 | 17 (Expanse) ·
  Gen 31:48 | 20 (Hill) · Mat 20:22 | 3 (Jesus). (Gen 26:20–22 / 31:48 are ABP's
  TRANSLATED well/place names — no roster form can exist.)
- **Bracketed (1)** — 1Sa 24:5 | 7 ("[2struck 1David's heart]"): capfall runs only on
  the clean unbracketed shape; also possessive, not subject. Manual-look class.
- **_NOT_SUBJECT guard (1)** — Gen 41:12 | 7 ("Hebrew servant"): adjective+noun, the
  guard added 2026-06-26 doing its job.

**GATE-5 EXPECTATION (formal, as amended): blank star-row residue on the rebuilt
copy = 340 = 11 CAP-remainder + 64 MID + 40 NOCAP + 225 EMPTY** — plus, at the
ROSTER level, the documented leave-list piles (`alias_leave_list.txt` A/B/P/R +
decisions rejects/cautions), the head-resolves multi-word-cell class, and the five
empty-head rows PINNED BY REF in `check_gate5_sweep.py`. Any other residue = STOP.
(History: first cut said 339/10; the second build's gate-5 sweep found Isa 41:14
mispeeled — see above — and the sweep checker + this expectation were re-pinned.)

Format: ref | word position | previous cell's English

## CAP — capfall fixes these (reconciliation baseline) (148)

```
1Ch 1:49 | 2 | Shaul died,
1Ch 18:5 | 2 | Syria came
1Ch 19:12 | 4 | Syria should strengthen
1Ch 19:17 | 23 | Syria deployed
1Ki 1:15 | 2 | Bath-sheba entered
1Ki 1:16 | 2 | Bath-sheba bowed,
1Ki 1:31 | 2 | Bath-sheba bowed
1Ki 2:18 | 2 | Bath-sheba said,
1Ki 2:19 | 2 | Bath-sheba entered
1Ki 11:22 | 2 | Pharaoh said
1Ki 11:30 | 2 | Ahijah took hold of
1Ki 14:6 | 4 | Ahijah heard
1Ki 15:8 | 2 | Abijam slept
1Ki 20:20 | 8 | Syria fled,
1Ki 20:28 | 15 | Syria said,
1Sa 24:5 | 7 | David's heart
2Ch 13:1 | 8 | Abijah took reign
2Ch 13:3 | 2 | Abijah deployed for
2Ch 13:4 | 2 | Abijah rose up
2Ch 13:19 | 2 | Abijah pursued
2Ch 13:21 | 2 | Abijah grew strong,
2Ch 14:1 | 2 | Abijah slept
2Ch 18:13 | 2 | Michaiah said,
2Ch 18:16 | 2 | Michaiah said,
2Ch 18:18 | 2 | Michaiah said,
2Ch 18:24 | 2 | Michaiah said,
2Ch 18:27 | 2 | Michaiah said,
2Ch 34:15 | 2 | Helkiah responded
2Ch 34:15 | 18 | Helkiah gave
2Ch 34:22 | 2 | Helkiah went,
2Ki 7:15 | 19 | Syrians tossed
2Ki 10:15 | 43 | Jehonadab said,
2Ki 22:9 | 2 | Shapan entered
2Sa 3:15 | 2 | Ishbosheth sent,
2Sa 6:6 | 8 | Uzzah stretched out
2Sa 10:11 | 4 | Syria should strengthen
2Sa 10:14 | 7 | Syria has fled.
2Sa 10:15 | 2 | Syria beheld
2Sa 10:16 | 2 | Hadarezer sent,
2Sa 10:17 | 18 | Syria deployed
2Sa 10:18 | 2 | Syria fled
2Sa 10:19 | 21 | Syria feared
2Sa 12:9 | 14 | Uriah
2Sa 23:1 | 8 | Trustworthy
2Sa 24:20 | 2 | Araunah looked,
2Sa 24:20 | 16 | Araunah went forth,
2Sa 24:21 | 2 | Araunah said,
2Sa 24:22 | 2 | Araunah said
2Sa 24:23 | 3 | Araunah gave
2Sa 24:23 | 8 | Araunah said
Dan 4:19 | 32 | Belteshazzar answered
Est 4:12 | 2 | Hatach reported
Est 9:6 | 7 | Jews killed
Est 9:12 | 8 | Jews destroyed
Exo 5:2 | 2 | Pharaoh said,
Exo 5:5 | 2 | Pharaoh said,
Exo 8:8 | 2 | Pharaoh called
Exo 8:12 | 19 | Pharaoh arranged.
Exo 8:28 | 2 | Pharaoh said,
Exo 8:32 | 2 | Pharaoh was oppressed
Exo 10:24 | 2 | Pharaoh called
Exo 10:28 | 2 | Pharaoh says,
Exo 12:30 | 2 | Pharaoh rose up
Exo 12:31 | 2 | Pharaoh called
Exo 13:17 | 3 | Pharaoh sent out
Exo 14:3 | 2 | Pharaoh will say
Exo 33:8 | 26 | Moses' going away
Exo 36:1 | 2 | Bezaleel prepared,
Exo 37:1 | 2 | Bezaleel made
Eze 26:2 | 4 | Sor said
Ezr 1:11 | 13 | Sheshbazzar led up
Ezr 2:63 | 2 | Tirshatha spoke
Gen 5:9 | 2 | Enos lived
Gen 5:10 | 2 | Enos lived
Gen 5:15 | 2 | Mahalaleel lived
Gen 5:16 | 2 | Mahalaleel lived
Gen 11:12 | 2 | Arphaxad lived
Gen 11:13 | 2 | Arphaxad lived
Gen 11:14 | 2 | Salah lived
Gen 11:15 | 2 | Salah lived
Gen 12:4 | 2 | Abram went
Gen 12:5 | 2 | Abram took
Gen 12:6 | 2 | Abram traveled through
Gen 12:9 | 2 | Abram departed;
Gen 12:10 | 8 | Abram went down
Gen 12:11 | 4 | Abram approached
Gen 12:11 | 9 | Abram said
Gen 12:14 | 4 | Abram entered
Gen 12:20 | 2 | Pharaoh charged
Gen 14:19 | 6 | Abram, a blessing
Gen 15:3 | 2 | Abram said,
Gen 15:6 | 2 | Abram trusted
Gen 16:15 | 8 | Abram called
Gen 17:3 | 2 | Abram fell
Gen 22:21 | 1 | Huz
Gen 26:20 | 21 | Injustice,
Gen 26:21 | 17 | Hatred.
Gen 26:22 | 17 | Expanse,
Gen 31:48 | 20 | Hill
Gen 40:2 | 2 | Pharaoh was provoked to anger
Gen 40:13 | 5 | Pharaoh will remember
Gen 40:19 | 5 | Pharaoh will remove
Gen 41:12 | 7 | Hebrew servant
Gen 41:38 | 2 | Pharaoh said
Gen 41:42 | 2 | Pharaoh removing
Gen 41:45 | 2 | Pharaoh called
Gen 47:3 | 2 | Pharaoh said
Gen 47:5 | 2 | Pharaoh said
Gen 47:11 | 27 | Pharaoh assigned.
Gen 50:6 | 2 | Pharaoh said
Gen 50:23 | 18 | Joseph's thighs.
Isa 19:2 | 2 | Egyptians shall be roused
Isa 31:8 | 2 | Assyria shall fall;
Isa 33:5 | 8 | Zion shall be filled up
Isa 41:14 | 4 | O Israel, very few in number!
Isa 49:14 | 1 | Zion said,
Jer 20:1 | 2 | Pashur heard
Jer 20:3 | 6 | Pashur led out
Jer 22:28 | 1 | Coniah is disgraced
Jer 24:5 | 16 | Jews being resettled
Jer 26:21 | 19 | Urijah heard
Jer 48:41 | 1 | Kerioth was taken,
Jer 49:1 | 19 | Milcom inherit
Jer 51:1 | 12 | Chaldeans dwelling there
Jer 51:24 | 8 | Chaldeans dwelling there
Jer 51:41 | 2 | Sheshach is captured,
Job 1:15 | 2 | Sabeans fell upon
Job 42:10 | 26 | Job's before,
Jos 5:15 | 27 | Josua did
Jdg 7:1 | 2 | Jerubbaal rose early
Lam 1:3 | 1 | Judea was displaced
Lam 1:17 | 1 | Zion opened and spread out
Neh 3:21 | 4 | Meramoth repaired,
Neh 7:65 | 2 | Arthasastha said
Num 7:89 | 3 | Moses' entering
Rth 1:4 | 4 | Moabite wives;
Act 1:25 | 11 | Judas violated
Act 2:10 | 16 | Romans emigrating here,
Act 7:28 | 10 | Egyptian yesterday?
Act 14:2 | 3 | Jews having resisted persuasion,
Luk 1:12 | 2 | Zacharias was disturbed
Luk 1:18 | 2 | Zacharias said
Luk 11:32 | 1 | Men of Nineveh
Luk 17:32 | 3 | Lot's wife!
Mar 12:18 | 2 | Sadducees came
Mar 14:43 | 6 | Judas comes,
Mat 12:41 | 1 | Ninevite men
Mat 20:22 | 3 | Jesus
```

## MID — deferred to audit session (64)

```
1Ch 2:34 | 12 | there was an Egyptian servant,
1Ch 11:2 | 7 | in Saul being
1Ki 7:14 | 14 | was a Tyrian man,
1Ki 11:17 | 6 | the Edomite men
1Ki 14:16 | 13 | led Israel into sin.
1Ki 15:30 | 7 | led Israel into sin,
1Ki 15:34 | 21 | led Israel into sin.
1Ki 16:13 | 13 | led Israel into sin,
1Ki 16:19 | 29 | led Israel into sin.
1Ki 16:26 | 16 | led Israel into sin,
1Sa 14:50 | 4 | of Saul's wife
1Sa 20:33 | 24 | to put David to death.
1Sa 30:11 | 3 | an Egyptian man
2Ch 2:14 | 10 | is a Tyrian man,
2Ch 14:12 | 12 | the Ethiopians fled.
2Ch 32:30 | 21 | the way of Hezekiah was prospered
2Ki 19:10 | 20 | should Jerusalem be delivered up
2Ki 21:16 | 23 | led Judah into sin,
2Sa 7:20 | 3 | shall David add
2Sa 17:17 | 23 | to king David,
Amo 6:1 | 3 | treating Zion with contempt,
Dan 11:1 | 6 | of Cyrus
Deu 22:19 | 17 | an Israelite virgin,
Deu 33:6 | 1 | Let Reuben live
Deu 33:7 | 2 | this for Judah,
Exo 2:11 | 26 | an Egyptian man
Exo 2:19 | 4 | An Egyptian man
Exo 9:8 | 17 | let Moses strew it
Exo 35:4 | 14 | the LORD ordered,
Gen 9:27 | 14 | let Canaan become
Gen 35:18 | 16 | of my Grief;
Gen 38:2 | 6 | of a Canaanite man,
Gen 39:1 | 15 | an Egyptian man,
Gen 39:14 | 15 | a Hebrew servant
Gen 41:34 | 2 | let Pharaoh make
Gen 46:26 | 20 | of Jacob's sons —
Gen 49:17 | 2 | let Dan become
Isa 19:13 | 11 | they shall cause Egypt to wander
Isa 19:14 | 8 | they caused Egypt to wander
Isa 29:22 | 23 | shall Israel change.
Isa 30:31 | 6 | the Assyrians shall be vanquished,
Isa 37:10 | 21 | shall Jerusalem be delivered up
Isa 46:13 | 19 | to Israel
Jer 50:16 | 12 | of the Grecian sword.
Jer 51:64 | 4 | shall Babylon descend,
Lev 24:10 | 4 | of an Israelitish woman,
Num 12:1 | 17 | an Ethiopian woman
Num 20:24 | 1 | Let Aaron be added
Oba 1:6 | 2 | was Esau searched out,
Psa 52:0 | 20 | that David went
Psa 106:16 | 2 | they provoked Moses to anger
Psa 108:7 | 10 | I shall divide Shechem into parts;
Psa 130:7 | 1 | Let Israel hope
Psa 149:2 | 1 | Let Israel be glad
Zec 2:4 | 14 | shall Jerusalem be inhabited
Zec 8:23 | 22 | of a Jewish man,
Act 8:27 | 6 | there was an Ethiopian man,
Act 13:24 | 1 | Which John having publicly proclaimed
Act 16:9 | 11 | of Macedonia was
Act 22:25 | 14 | a Roman man
Heb 11:24 | 8 | of Pharaoh's daughter,
Joh 4:9 | 17 | a Samaritan woman?
Luk 4:26 | 5 | was Elijah sent,
Mat 15:22 | 3 | a Canaanite woman
```

## NOCAP — correct as blank (40)

```
1Ch 2:3 | 19 | was
1Ch 10:13 | 22 | he asked
1Ch 19:7 | 30 | their cities,
1Ch 20:4 | 15 | struck
1Ki 15:29 | 29 | of his servant
1Ki 19:6 | 2 | he looked.
1Sa 11:15 | 29 | was glad
1Sa 24:17 | 2 | he said
1Sa 25:42 | 4 | rose up
2Ch 15:8 | 34 | he took control of
2Ch 31:5 | 6 | were superabundant
2Ch 32:25 | 7 | he recompensed
2Ki 7:19 | 26 | said
2Ki 18:16 | 5 | cut off
2Sa 15:30 | 14 | his head
2Sa 19:37 | 29 | my son
Exo 16:34 | 9 | aside
Eze 35:5 | 3 | you became
Gen 11:21 | 6 | his procreating
Jer 30:9 | 10 | their king
Jer 41:11 | 19 | did
Jer 43:6 | 20 | left behind
Jos 13:8 | 13 | gave
Jos 22:34 | 2 | he
Jdg 5:26 | 15 | with a hammer
Jdg 8:15 | 2 | he came
Jdg 9:21 | 16 | his brother.
Jdg 10:9 | 21 | they afflicted
Jdg 11:16 | 3 | their ascending
Jdg 12:12 | 2 | died
Jdg 16:19 | 2 | she rested
Neh 3:11 | 4 | repaired
Num 4:34 | 3 | numbered
Num 22:30 | 10 | your donkey,
Psa 115:1 | 14 | your mercy
Psa 131:3 | 2 | hope
Rth 1:16 | 1 | said
1Jn 4:16 | 13 | us.
Act 9:36 | 1 | And
Joh 3:25 | 6 | disciples
```

## EMPTY — correct as blank (225)

```
1Ch 11:23 | 6 | 
1Ch 19:18 | 3 | 
1Ch 21:9 | 8 | 
1Ch 21:28 | 8 | 
1Ki 1:43 | 17 | 
1Ki 7:48 | 3 | 
1Ki 11:40 | 6 | 
1Ki 15:26 | 22 | 
1Ki 21:22 | 26 | 
1Sa 7:17 | 17 | 
1Sa 11:15 | 12 | 
1Sa 19:1 | 17 | 
1Sa 19:13 | 3 | 
1Sa 22:4 | 16 | 
1Sa 24:7 | 16 | 
2Ch 15:8 | 5 | 
2Ch 21:11 | 18 | 
2Ki 3:3 | 10 | 
2Ki 10:29 | 9 | 
2Ki 10:31 | 25 | 
2Ki 13:2 | 18 | 
2Ki 13:6 | 11 | 
2Ki 13:11 | 18 | 
2Ki 14:24 | 18 | 
2Ki 15:9 | 23 | 
2Ki 15:18 | 17 | 
2Ki 15:24 | 18 | 
2Ki 15:28 | 18 | 
2Ki 19:15 | 3 | 
2Ki 23:15 | 17 | 
2Sa 3:27 | 3 | 
2Sa 14:4 | 5 | 
2Sa 18:31 | 8 | 
2Sa 18:32 | 16 | 
2Sa 23:21 | 6 | 
Est 1:16 | 3 | 
Est 1:21 | 16 | 
Est 2:11 | 6 | 
Est 5:1 | 9 | 
Est 5:2 | 36 | 
Eze 23:5 | 3 | 
Eze 25:12 | 7 | 
Eze 39:11 | 30 | 
Gen 3:12 | 3 | 
Gen 4:5 | 13 | 
Gen 13:14 | 10 | 
Gen 39:17 | 14 | 
Hos 11:9 | 13 | 
Isa 33:9 | 5 | 
Jer 14:2 | 2 | 
Jer 32:35 | 41 | 
Jer 49:17 | 3 | 
Jos 5:4 | 7 | 
Jos 8:19 | 3 | 
Jos 10:12 | 18 | 
Jos 14:14 | 4 | 
Jos 18:8 | 8 | 
Jos 24:19 | 3 | 
Jdg 1:32 | 3 | 
Jdg 9:16 | 12 | 
Neh 6:1 | 5 | 
Num 12:1 | 11 | 
Num 25:8 | 5 | 
Num 25:8 | 16 | 
Num 25:14 | 6 | 
Num 25:15 | 5 | 
Act 1:1 | 12 | 
Act 5:3 | 7 | 
Act 8:14 | 9 | 
Act 8:39 | 10 | 
Act 10:25 | 5 | 
Act 10:46 | 12 | 
Act 12:6 | 12 | 
Act 12:14 | 18 | 
Act 13:25 | 4 | 
Act 14:11 | 7 | 
Act 16:3 | 3 | 
Act 18:1 | 5 | 
Act 18:14 | 9 | 
Act 19:21 | 6 | 
Act 20:9 | 14 | 
Act 21:18 | 5 | 
Act 23:10 | 10 | 
Act 23:24 | 6 | 
Act 24:24 | 6 | 
Act 25:4 | 7 | 
Act 25:19 | 18 | 
Act 25:23 | 35 | 
Act 25:24 | 3 | 
Act 27:9 | 19 | 
Act 27:21 | 7 | 
Act 27:31 | 2 | 
Act 27:33 | 8 | 
Act 28:15 | 19 | 
Joh 1:29 | 4 | 
Joh 1:35 | 5 | 
Joh 1:47 | 2 | 
Joh 1:48 | 8 | 
Joh 2:19 | 2 | 
Joh 2:22 | 24 | 
Joh 3:3 | 2 | 
Joh 3:5 | 2 | 
Joh 3:22 | 4 | 
Joh 4:13 | 2 | 
Joh 4:54 | 6 | 
Joh 5:1 | 9 | 
Joh 6:1 | 4 | 
Joh 6:29 | 2 | 
Joh 7:1 | 3 | 
Joh 7:6 | 4 | 
Joh 7:14 | 7 | 
Joh 7:21 | 2 | 
Joh 7:37 | 11 | 
Joh 8:20 | 5 | 
Joh 9:3 | 2 | 
Joh 9:35 | 2 | 
Joh 9:39 | 3 | 
Joh 10:23 | 3 | 
Joh 11:30 | 4 | 
Joh 11:32 | 8 | 
Joh 11:35 | 2 | 
Joh 11:39 | 2 | 
Joh 11:45 | 15 | 
Joh 11:46 | 14 | 
Joh 11:51 | 16 | 
Joh 12:12 | 13 | 
Joh 12:16 | 13 | 
Joh 12:30 | 2 | 
Joh 12:35 | 4 | 
Joh 12:36 | 15 | 
Joh 13:1 | 8 | 
Joh 13:23 | 15 | 
Joh 13:26 | 2 | 
Joh 13:31 | 4 | 
Joh 14:23 | 2 | 
Joh 17:1 | 3 | 
Joh 18:2 | 13 | 
Joh 18:8 | 2 | 
Joh 18:27 | 4 | 
Joh 18:31 | 4 | 
Joh 18:35 | 2 | 
Joh 18:36 | 2 | 
Joh 18:37 | 4 | 
Joh 18:37 | 11 | 
Joh 19:1 | 4 | 
Joh 19:8 | 4 | 
Joh 19:10 | 4 | 
Joh 19:11 | 2 | 
Joh 19:12 | 4 | 
Joh 19:13 | 10 | 
Joh 19:20 | 18 | 
Joh 19:22 | 2 | 
Joh 19:28 | 4 | 
Joh 19:38 | 31 | 
Joh 20:2 | 15 | 
Joh 20:19 | 26 | 
Joh 20:24 | 16 | 
Joh 20:28 | 3 | 
Joh 20:30 | 8 | 
Joh 21:4 | 6 | 
Joh 21:7 | 8 | 
Joh 21:14 | 5 | 
Joh 21:17 | 10 | 
Joh 21:20 | 10 | 
Joh 21:25 | 8 | 
Luk 1:41 | 5 | 
Luk 3:16 | 2 | 
Luk 4:8 | 5 | 
Luk 4:14 | 3 | 
Luk 6:3 | 6 | 
Luk 8:45 | 3 | 
Luk 8:45 | 13 | 
Luk 9:33 | 10 | 
Luk 9:36 | 8 | 
Luk 9:43 | 16 | 
Luk 19:35 | 16 | 
Luk 22:55 | 12 | 
Luk 22:61 | 10 | 
Luk 24:15 | 11 | 
Luk 24:36 | 6 | 
Mar 1:14 | 8 | 
Mar 2:8 | 4 | 
Mar 2:17 | 3 | 
Mar 8:1 | 14 | 
Mar 8:27 | 3 | 
Mar 9:2 | 6 | 
Mar 10:28 | 3 | 
Mar 10:49 | 3 | 
Mar 11:6 | 7 | 
Mar 11:15 | 7 | 
Mar 12:41 | 3 | 
Mar 14:18 | 7 | 
Mar 14:22 | 5 | 
Mar 14:66 | 3 | 
Mar 14:72 | 8 | 
Mar 15:5 | 9 | 
Mar 15:34 | 7 | 
Mat 3:16 | 3 | 
Mat 4:17 | 4 | 
Mat 7:28 | 5 | 
Mat 8:13 | 3 | 
Mat 8:14 | 3 | 
Mat 9:2 | 11 | 
Mat 9:4 | 3 | 
Mat 9:11 | 3 | 
Mat 9:19 | 3 | 
Mat 9:23 | 3 | 
Mat 9:35 | 3 | 
Mat 10:5 | 5 | 
Mat 11:1 | 5 | 
Mat 11:7 | 5 | 
Mat 11:25 | 6 | 
Mat 12:1 | 6 | 
Mat 13:1 | 7 | 
Mat 13:34 | 4 | 
Mat 16:21 | 4 | 
Mat 17:1 | 6 | 
Mat 18:2 | 3 | 
Mat 19:1 | 5 | 
Mat 21:12 | 3 | 
Mat 26:1 | 5 | 
Mat 26:26 | 5 | 
Mat 26:55 | 6 | 
Mat 26:75 | 3 | 
Mat 27:46 | 7 | 
```
