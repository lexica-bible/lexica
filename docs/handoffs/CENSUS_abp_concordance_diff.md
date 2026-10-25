# CENSUS — ABP Lexical Concordance verse lists vs our words table (2026-10-25)

Read-only lane. Nothing was written to any database. Source: JP's `lexical_concordance.pdf`
(Downloads, not in the repo). Ours: the PA export `~/abp_words_by_verse_20261025.csv` (copied to
`abp_helps/`, git-ignored), one row per number per verse:
`SELECT w.strongs, v.book, v.chapter, v.verse, COUNT(*) FROM words w JOIN verses v ON v.id = w.verse_id
WHERE w.strongs GLOB '[0-9]*' GROUP BY v.id, w.strongs` → 434,812 rows. Book codes = `abp_texts`
codes (66, checked on the export's first rows); Psalm verse 0 present (659 rows); name rows (`*`)
excluded — all 32,478 `is_pn` rows are `*`, none carries a number (checked on a known positive).

Tools (committed): `scripts/parse_abp_concordance.py` (PDF → entries + verse refs),
`scripts/concordance_handmap.tsv` (18 hand-ruled print-error fixes), `scripts/diff_concordance_verses.py`
(export vs Concordance; also the export-vs-`abp_texts` row gap). Outputs in `abp_helps/` (git-ignored):
`concordance_entries.tsv`, `concordance_refs.tsv`, `concordance_failures.tsv`,
`concordance_diff_live20261025_{numbers,rows,gap}.tsv`.

Census scope notes + counts: TODO "Concordance verse-list diff" item (commit d14a24ff).

## 1. The 14,922-row gap (export 434,812 vs `abp_texts` 419,890 number-verse pairs)
= 33,219 pairs only in the export − 18,297 only in `abp_texts`. Every gap pair is under a number the
Concordance has; split by whether that number has a verse list there:

| Book | Net | Export-only: has list / no list / not in Conc. | `abp_texts`-only: has list / no list / not in Conc. |
|---|---|---|---|
| Psa | +1,275 | 0 / 2,663 / 0 | 0 / 1,388 / 0 |
| Gen | +991 | 0 / 1,965 / 0 | 0 / 974 / 0 |
| Deu | +961 | 0 / 1,630 / 0 | 0 / 669 / 0 |
| Jer | +918 | 1 / 1,707 / 0 | 1 / 789 / 0 |
| Eze | +911 | 0 / 1,683 / 0 | 0 / 772 / 0 |
| other 61 books | +9,866 | 9 / 23,561 / 0 | 0 / 14,704 / 0 |
| **Total** | **+14,922** | **10 / 33,209 / 0** | **1 / 18,296 / 0** |

(All 66 books: `concordance_diff_live20261025_gap.tsv`.)

**Cause: pronoun numbering.** `abp_texts` (the pre-build source) files every personal pronoun under
ABP's raw 1473 (18,293 of its 18,297 extra pairs). The live table files them under their own numbers —
αὐτός 846 (15,357 pairs), σου 4675 (3,240), μου 3450 (2,866), ὑμῶν 5216, με 3165, σε 4571, σοι 4671,
ὑμῖν 5213… — and one 1473 in a verse often becomes 2–3 different numbers. All of these are "Far &
wide" entries with NO verse list, so the gap never touches the diff. Only 11 gap pairs sit under
numbers that have a list: export-only 4674 σός ×5 (1Ki 21:4, 1Sa 22:15, 2Sa 15:34, Isa 4:1,
Pro 4:21), 1475.3 1Sa 6:11, 165 Jer 49:13 (abp_texts has 166 there), 2334 Heb 7:4, 241.2 Mal 3:6,
2753 Act 24:8.

## 2. Parse coverage
- 364 content pages (365 back title, 366 blank) · **9,257 entries** · 9,258 number keys (Levi
  `3017,18` = two) · 14 bracketed second numbers.
- 9,257 = the census's 9,255 + two entries with NO headword the census had glued onto the entry
  before: a bare `2717` ("An unused word in The Apostolic Bible") and `3203–3302` ("These numbers
  were omitted in Strong's").
- **245,437 verse refs parsed · 0 failed lines.** No gloss line still holds a `ch:vs`.
- Classes: has verses 8,532 · proper name 474 · proper title 88 · far & wide 50 · see-pointer 49 ·
  included-in 46 · unused word 14 · other no-verse 4.
- **Hand-map, 18 rows, all used, every one checked against `abp_texts`:** 3 double commas · 4 letter
  l for 1 · 2 space for comma · 1 period for comma · 3 bad book names (`Jdg.`, `1SA`, `Gal,`) · 1
  dropped wrap comma (κριός, `29:2,3,8,9,13` / `14*,…` = Num 29) · 1 lost chapter digit
  (`1:title–15` → `11:title–15`) · 3 footnote refs (`Ezr 6:3ftnt`, `Ezr 9:1ftnt.`, `Neh 13:31ft.` —
  the word is in that verse's footnote, not its text; kept OUT of the disagreement counts).
  The census's "39 print-error refs" shrank to these 18: 14 were Psalm `title` forms the title rule
  reads, 6 were tails of notes ("Included in 1437 & / 3361"), 2 were the headword-less entries.
- **RULE CORRECTION — `Ps 2:title–9` = the superscriptions of Psalms 2 THROUGH 9** (a chapter range of
  titles), not verses 0–9. Every such range (ψαλμός 5568: 2–9, 11–15, 19–35, 46–51, 61–69, 75–77,
  82–85, 108–110, 138–141; ᾠδή 5603: 65–69, 125–134) matches the Psalms whose superscription carries
  the word in `abp_texts`. Verse-0 refs overall: 379 of 381 land on a superscription carrying the word
  (misses: ᾠδή 5603 Ps 69 · ἀπολύω 630 cites a "title" in Num 33, which our text does not have).
- Print quirks read correctly, listed: 9 entries print refs out of Bible order (e.g. θερισμός 2326
  "2Sa 21:9*,10 · Rt 2:23*"); 5 verses are listed twice inside one entry (1Ki 16:8 ×2 in 1501.10;
  Ps 116:4 and 116:17 in 1941; Rt 2:23 plain + starred in 2326; Ps 77 title in 5568 via "75:title–77"
  + "77:title") — one verse, starred if either copy is.
- Controls (all PASS): 10.3 ἅβρα = Gen 24:61 · Exo 2:5* · Est 2:9, 4:4, 4:16; the lane-(2) five
  2241/5411/303/1047/4577 = 1/24/14/7/5 verses with 4 stars; entry 1 alpha = Rev 1:8, 21:6, 22:13;
  Levi = two keys. Guide words agree on 362/364 pages (274, 328 = two-spelling headwords); printed page
  number = PDF page on all 364; no number on two headings.

## 3. The diff (8,532 entries with verse lists; matching on the FULL number, bracket/second numbers together)

**7,902 of 8,532 entries match exactly** (same verses, same stars).

| | Verses |
|---|---|
| Concordance verses | 245,429 |
| Our verses (same numbers) | 245,322 |
| Shared | 245,065 |
| Only in the Concordance | 364 (206 entries) |
| Only in ours | 257 (161 entries) |
| Concordance `*`, ours has it once | 18 |
| Ours has it 2+ times, no `*` | 651 |
| Footnote refs (kept apart) | 3 |

Export rows outside the compared entries: 189,423 under numbers with no Concordance verse list ·
67 under numbers the Concordance never prints (all sibling dotted numbers: 2827.2 ×16, 4761.2 ×13,
4951.5 ×11, 1458.5 ×7, 5557.2 ×5, 3864.3 ×4, 1772.2 ×2, + 9 singles).

Patterns (not adjudicated):
- **Number-label disagreements (~92 of the 364 Concordance-only):** ἔνθεν — the Concordance has 1759.2
  in 28 verses, ours files them under 1759.3 (= the Concordance's ἐνθρονίζω, whence its 28 ours-only);
  κλοιός — Concordance 2828.1 vs our 2827.2 (16); 48 more where our same verse carries a sibling
  dotted number the Concordance never prints (4761.1/.2 13 · 4951.4/.5 11 · 1458.4/.5 7 · 5557.1/.2 5 ·
  3864.2/.3 4 · 1772.1/.2 2 · 6 singles).
- **11 Concordance refs to verses not in our text** (e.g. Ps 77:41 under ἅγιος 39 — pairs with our
  Ps 78:41; Num 33 "title").
- **The 651 "2+ no `*`" are mostly ours:** in 628 of them `abp_texts` also has the word ONCE in that
  verse — our table has 2+ word rows carrying the number where the source tags it once (cause not
  traced; the export has no per-row columns). Only 23 are 2+ in `abp_texts` too.

Top 20 entries by disagreement:

| No. | Headword | Conc. | Ours | Conc.-only | Ours-only | `*` once | 2+ no `*` |
|---|---|---|---|---|---|---|---|
| 1759.3 | ἐνθρονίζω | 1 | 28 | 1 | 28 | 0 | 0 |
| 1759.2 | ἔνθεν | 28 | 0 | 28 | 0 | 0 | 0 |
| 1096 | γίνομαι | 2,238 | 2,238 | 3 | 3 | 0 | 19 |
| 1510.8.3 | ἔσται | 1,177 | 1,178 | 1 | 2 | 0 | 14 |
| 2828.1 | κλοιός | 16 | 0 | 16 | 0 | 0 | 0 |
| 4951.4 | συσκοτάζω | 11 | 3 | 11 | 3 | 0 | 0 |
| 4222 | ποτίζω | 73 | 73 | 0 | 0 | 0 | 13 |
| 4761.1 | στρεπτός | 13 | 0 | 13 | 0 | 0 | 0 |
| 1325 | δίδωμι | 1,890 | 1,889 | 2 | 1 | 1 | 8 |
| 2007 | ἐπιτίθημι | 271 | 270 | 1 | 0 | 0 | 10 |
| 1125 | γράφω | 388 | 388 | 0 | 0 | 0 | 10 |
| 2036 | ἔπω | 3,910 | 3,909 | 3 | 2 | 0 | 5 |
| 2212 | ζητέω | 346 | 347 | 3 | 4 | 0 | 3 |
| 2980 | λαλέω | 1,260 | 1,257 | 4 | 1 | 0 | 5 |
| 4160 | ποιέω | 2,931 | 2,929 | 2 | 0 | 2 | 6 |
| 2983 | λαμβάνω | 1,259 | 1,261 | 0 | 2 | 1 | 6 |
| 1458.4 | ἐγκατάλειμμα | 7 | 1 | 7 | 1 | 0 | 0 |
| 1490 | εἰ δὲ μή | 24 | 31 | 0 | 7 | 0 | 1 |
| 2380 | θύω | 125 | 131 | 1 | 7 | 0 | 0 |
| 3745 | ὅσος | 578 | 574 | 5 | 1 | 0 | 2 |

**The 18 "`*` but once":** 207.2 Pro 5:7 · 516.3 2Ki 6:18 · 608 1Sa 23:11 · 1074 Jer 50:39 ·
1325 1Sa 18:19 · 1855 Eze 42:7 · 1921 2Pe 2:21 · 2033 Jos 6:4 · **2588 καρδία Ecc 7:22** · 2983 2Ki 12:8 ·
3140 1Jn 5:7 · 3379 Exo 34:12 · 4160 Exo 37:15, 37:16 · 4434 Hab 3:14 · 5207 1Ch 24:25 ·
5495 Jer 34:1, 34:2.

## 4. Ecc 7:22 καρδία (2588) — the census's one star exception
Stands on live: the Concordance stars it; our table has 1 occurrence (same as `abp_texts`).

## 5. Bucket (a) classified — split renderings (2026-10-25)
Bucket (a) = the 628 of the 651 "2+ rows, no `*`" verses where `abp_texts` tags the word ONCE.
Across all 628 no other number in the verse lost a row (an added row, not a renumbering); in 594
the tagged word sits in or right after an ABP bracket group.

**20-verse PA row read** (every words row carrying the number, with `abp_surface` form/translit):
**20/20 split renderings · 0 exact duplicates · 0 glued splits.** Each verse = two neighbouring
rows, same number, same Greek form on both (one Greek word, e.g. `δώσι` on both Gen 24:41 rows),
two different English pieces; morph + lemma sit on exactly one of the two in 12 verses, on neither in 8 (Lev 14:39, Jdg 19:22, 2Sa 14:25, Est 2:17, Ecc 5:6, Jer 49:14, Eze 41:15, Hos 10:13).
Two shapes, 10 each in the sample:

| Shape | Sample verses (piece 1 \| piece 2) |
|---|---|
| Outside-bracket: first piece has no bracket and no Greek position; next row opens the bracket (the helper audit's polarity-A fingerprint) | Lev 14:39 `if \| was diffused` · Jdg 19:22 `were doing \| good` · 2Sa 14:25 `as \| praiseworthy` · 2Ki 11:16 `they put \| upon` · Ecc 5:6 `to lead \| into sin` · Eze 41:15 `columned \| porch` · Hos 10:13 `you pass over \| in silence` · Mic 7:1 `a cluster of \| grapes` · Hag 2:10 `in the \| year` · Mal 3:15 `declare \| blessed` |
| Both-inside-bracket: each piece has its own Greek position | Gen 24:41 `they should \| give her` · Deu 4:10 `let \| hear` · Ezr 6:3 `Let \| be built` · Est 2:17 `loved \| passionately` · Psa 115:17 `shall \| praise` · Jer 49:14 `he sent \| , saying,` · 2Co 2:11 `we are \| ignorant.` · Joh 11:50 `should \| perish.` · Mar 14:4 `has \| taken place?` · Rom 15:2 `let \| please` |

**Helper audit vs the 628** (`scripts/audit_helper_double_tag.py`, live PA run 2026-10-25, read-only;
its A-review list = 362 pairs). Its three original A controls FAILED because they are cured (the 7/9
fix blanked them — 607 empty-strongs_base rows); the list was validated instead on the sample: 10/10
outside-bracket verses listed, 0/10 both-inside-bracket verses listed.

| | Pairs |
|---|---|
| In the 628 AND on the audit's A-review list (outside-bracket) | 174 |
| In the 628, NOT listed (both-inside-bracket — no detector) | 454 |
| On the A-review list but outside the 628 | 183 (mostly function words — 3588, 3756, 3361 — with no Concordance verse list or a different star status) |

**Verdict:** one class (one Greek word, two tagged rows), but the helper audit covers only 174/628
(28%) → its own lane, the helper audit a partial detector. JP ruled it a counting defect
2026-10-25 (TODO "Split-rendering double rows"); a fix changes word rows → checkpoint first.
List: `abp_helps/split_rendering_628.tsv`. The audit's A controls were replaced with three live
positives from the 174 (2Ki 11:16 G2007 · Psa 69:21 G4222 · Act 13:19 G2624; B control Rth 2:16 kept).

## 6. Adjudication pass (2026-10-25) — buckets (c), (b), (d)
Read-only. Witnesses: the ABP app slot file (PA `abp_app_html/abp_app_slots.tsv`, copied to
`abp_helps/abp_app_slots_full.tsv`, 577,994 slots), loaded/folded/Psalm-shifted with the lane-(a)
audit's own code; the Analytical Lexicon form lists. Tool: `scripts/adjudicate_concordance_diff.py`
(outputs `abp_helps/adj_b_pairs.tsv`, `adj_b_verses.tsv`, `adj_d_rows.tsv`). After the bucket-(c)
hand-map rows: **7,905 of 8,532 entries match exactly**; Concordance-only 356 · ours-only 252.

### (c) 11 refs to verses not in our text — 8 placed, 3 unplaced
Placed by 5 new hand-map rows (`scripts/concordance_handmap.tsv`, now 23 rows):

| Entry | Printed | Fix | Evidence |
|---|---|---|---|
| ἅγιος 39 | `77:41` | → `78:41` | Ps 77 has 20 verses; our only unmatched ἅγιος verse is Ps 78:41 |
| ἐπεί 1893 | `118:136` | → `119:136` | Ps 118 has 29 verses; Ps 119:136 unmatched in ours |
| νεανίας 3494 | `17:56,58` under 2Sa | dropped (2 refs) | repeat of `1Sa 17:56,58` already in the entry; 2Sa 17 has 29 verses |
| παραλαμβάνω 3880 | `32:7` / `49:1*,2` after `So 8:2` | → `Jer 32:7` (49:1,2 follow) | book name missing; our unmatched rows = Jer 32:7, 49:1, 49:2 |
| υἱός 5207 | `26:1,20,22–25` | → `22–24` | Jer 26 ends at verse 24 |

Unplaced (no unmatched verse of ours anywhere in the chapter): ἀπολύω 630 "Nm 33:title" ·
οἶκος 3624 Hos 6:14 · υἱός 5207 2Ch 1:43.

### (b) Number-label disagreements — 212 verses in 102 pairs (not ~92)
Pairing: a Concordance-only verse (number N) whose verse holds exactly ONE number M of ours that the
Concordance does not account for there (3 more verses had 2+ candidates and stay in (d)). Ruling rule
(JP): the Lexicon decides — the app's Greek form at the slot carrying N or M, folded, must sit in the
Lexicon's form list for one side only. The app's own number at that slot is reported beside it.

| Verdict | Verses | Pairs | Destination |
|---|---|---|---|
| Concordance right (matches the Lexicon) | **152** (86 in 18 repeating pairs + 66 singles) | 84 | candidate corrections → TODO held "540 + 13" item |
| Ours right (matches the Lexicon) | **44** (42 in 5 repeating pairs + 2 singles) | 7 | Concordance print inconsistency |
| Hold | **16** (7 in 2 repeating pairs + 9 single-verse, unsettled) | 11 | held |

Repeating pairs (2+ verses):

| Conc. N [Lexicon] | Ours M [Lexicon] | Verses | Verdict | App's number at the slot |
|---|---|---|---|---|
| 1759.2 ἔνθεν | 1759.3 ἐνθρονίζω | 28 | Concordance right | M ×28 (app = ours) |
| 2828.1 (no Lexicon entry) | 2827.2 κλοιός | 16 | ours right | N ×16 (app = Conc.) |
| 4761.1 στρεπτός | 4761.2 (no entry) | 13 | Concordance right | N ×13 |
| 4951.4 σύσκιος | 4951.5 συσκοτάζω | 11 | ours right | M ×11 |
| 1458.4 ἐγκατάλειμμα | 1458.5 (no entry) | 7 | Concordance right | N 4 / M 3 |
| 1490.1 (no entry) | 1490 εἰ δὲ μή | 7 | ours right | N ×7 (app = Conc.) |
| 241.2 ἀλλοιόω | 241.3 ἀλλοίωσις | 7 | Concordance right | N ×7 |
| 4951.2 σύσκηνος | 4951.3 συσκιάζω | 5 | ours right | M ×5 |
| 5557.1 χρυσοτορευτός | 5557.2 χρυσοχόος | 5 | hold (4 favour ours by form; 1 verse has no app slot) | N 4 / neither 1 |
| 3864.2 παράθεσις | 3864.3 (no entry) | 4 | Concordance right | N ×4 |
| 4951.3 συσκιάζω | 4951.4 σύσκιος | 3 | ours right | M ×3 |
| 4992 σωτήριον | 4991 σωτηρία | 3 | Concordance right | N ×3 |
| 1371.2 δίψα | 1373 δίψος | 2 | Concordance right | N ×2 |
| 1510.2.3 ἐστίν | 1510.8.3 ἔσται | 2 | Concordance right | N ×2 |
| 1510.7.3 ἦν | 1510.7.1 ἤμην | 2 | Concordance right | N ×2 |
| 1536 εἴ τις | 1487 εἰ | 2 | Concordance right | N ×2 |
| 1772.1 ἐννοσσεύω | 1772.2 (no entry) | 2 | Concordance right | N ×2 |
| 2046 ἐρέω | 2036 ἔπω | 2 | Concordance right | N ×2 |
| 2117 εὐθύς | 2112.3 εὐθής | 2 | Concordance right | N ×2 |
| 2545 καίω | 1572 ἐκκαίω | 2 | hold (1 Conc. right; 1 verse has no app slot) | N 1 / neither 1 |
| 3494 νεανίας | 3495 νεανίσκος | 2 | Concordance right | N ×2 |
| 4405 πρωΐα | 4404 πρωΐ | 2 | Concordance right | N ×2 |
| 5117.1 τορευτός | 5557.1 χρυσοτορευτός | 2 | Concordance right | N ×2 |
| 5552 χρύσεος | 5557.1 χρυσοτορευτός | 2 | Concordance right | N ×2 |
| 975 βιβλίον | 976 βίβλος | 2 | Concordance right | N ×2 |

Sample verses (app's printed Greek → Lexicon): ἔνθεν Exo 26:13 / 32:15 / 38:15 `ένθεν και ένθεν` →
1759.2 · κλοιός Gen 41:42 / Deu 28:48 `κλοιόν`, Jdg 8:26 `κλοιών` → 2827.2 · συσκοτάζω 1Ki 18:45
`συνεσκότασε`, Jer 4:28 `συσκοτασάτω`, Jer 13:16 `συσκοτάσαι` → 4951.5 · ἀλλοιόω Dan 4:23
`αλλοιωθώσιν`, Dan 5:6 / 5:9 `ηλλοιώθη` → 241.2 · χρυσοχόος Isa 40:19 `χρυσοχόος`, 46:6
`χρυσοχόον`, Jer 10:9 `χρυσοχόων` → 5557.2. Full per-verse evidence: `adj_b_verses.tsv`.

Notes:
- **The 4951 family is a one-step shift in the Concordance:** it prints 4951.2 / .3 / .4 where the
  Lexicon, the app and ours all use .3 / .4 / .5 (συσκιάζω / σύσκιος / συσκοτάζω).
- **The publisher's own materials disagree on three pairs:** κλοιός (2828.1 in the Concordance and
  the app; 2827.2 in the Lexicon and ours), εἰ δὲ μήγε (1490.1 in the Concordance and the app; the
  Lexicon files the form under 1490, as ours), ἔνθεν (1759.2 in the Concordance and the Lexicon;
  1759.3 in the app and ours). Ruled by the Lexicon as instructed.
- For the 66 Concordance-right SINGLES the app + Lexicon prove the Concordance's number at that verse;
  which of our rows carries the word there is NOT proven (a one-verse pairing could be coincidence) —
  a row read comes before any correction.
- Single-verse, unsettled (9): 1521 / 5557.1 Exo 37:7 (no app slot) · 2289.1 / 2311.2 Neh 12:38 ·
  2633.1 / 1458.4 Amo 9:3 · 3441 / 3440 2Ch 18:30 (form in both lists) · 4325.5 / 1096 Lev 20:2 ·
  4628.1 / 4629.2 Exo 36:14 · 5046 / 4134 2Ch 16:9 · 518 / 312 Eze 37:18 · 5581.1 / 5579 Jer 29:21
  (no app slot).

### (d) Residue — 292 rows, every row classified, 0 unexplained

| Kind | Cause | Rows |
|---|---|---|
| Concordance-only (141) | Concordance print: not in source (neither the app nor ours has the number in that verse) | 51 |
| | number disagreement missed by (b) (the app has it; ours carries a number the app lacks there, often a no-verse-list word, e.g. ἀποτίνω 661 Exo 22:11 → ours 3756 οὐ) | 30 |
| | Concordance print: verse offset (the number sits unclaimed in ours 1–2 verses away) | 20 |
| | our slot error (the app has it; its English is in our verse text, but our number is missing) | 16 |
| | verse-text difference (the app has the word; our text does not, e.g. γῆ 1Pe 3:12, 1Jn 5:7) | 15 |
| | versification (Hab 3:14 ×8, Jer 10:5 ×1 — chapters the app orders in LXX sequence; JP-ruled no renumber) | 9 |
| Ours-only (110) | Concordance omission (the app has the number there too) | 51 |
| | Concordance print: verse offset (the other side of the 20 above) | 20 |
| | verse-text difference (ours has the word; the app has neither it nor a replacement number) | 21 |
| | number disagreement missed by (b) (the app carries a number ours lacks there) | 18 |
| `*` but ours once (18) | our slot error (the app has it 2+ as separate words, e.g. αορασία 2Ki 6:18 slots 14 + 18) | 9 |
| | Concordance star error (the app has it once too) | 6 |
| | Concordance print: verse merge (the 2nd occurrence is in our next/previous verse) | 3 |
| 2+ with no `*` (23) | Concordance star error (the app has 2+ separate words, e.g. υἱός ×5 1Ch 26:25) | 13 |
| | split rendering missed by (a) (the app has ONE slot; ours and `abp_texts` carry two) | 10 |

- **Ecc 7:22 καρδία — the census's one star exception — is a verse merge, not a star error.** From
  about v.17 the Concordance's Ecc 7 numbers run one ahead of ours (its 7:18 = our 7:17 for
  ἀποθνῄσκω and ἀσεβέω; its 7:22 = our 7:21 for ἀκούω); its starred 7:22 for καρδία = our 7:21 + 7:22,
  one each. The other two merges: λαμβάνω 2Ki 12:8 (+12:9), μαρτυρέω 1Jn 5:7 (+5:8). Ecc 7 (10) and Son 6 (6)
  account for most of the 20 verse-offset pairs.
- App split renderings are counted ONCE (neighbouring slots, same number + Greek, different English)
  — the bucket-(a) shape exists in the app too. Caveat: Pro 5:7 ἄκυρος 207.2 — the app also tags
  `μη` with 207.2, so that one "app has it 2+" rests on an app tagging slip.
- Every row: `abp_helps/adj_d_rows.tsv` (kind · cause · number · verse · stars · counts · app Greek ·
  the other number).
