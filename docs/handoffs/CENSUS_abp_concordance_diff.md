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
