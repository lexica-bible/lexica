# CENSUS — abp_surface FILL, step 1 (read-only) — COMPLETE

2026-10-24. JP ruling: lane (1) abp_surface FILL is go; lane (2) waits until the fill is live.
Read-only step: no writes, no fix code, no dry run. Inputs: `HANDOFF_abp_source_material.md`.

**Sources.** A and C: local `abp_helps/missing_forms_resolved.tsv` (lane (b) join of PA's
4,058-row `missing_printed_forms.tsv`) vs `abp_helps/analytical_lexicon.tsv`. B and D: two PA
exports, 10/24 (`abp_app_html/nbsp_surface_rows.tsv` = every abp_surface form holding an NBSP
with both neighbour slots; `abp_app_html/nbsp_544.tsv` = the lane (a) audit's slot dump, surface
target, class "our value is a two-word NBSP value"), run through
`scripts/census_abp_surface_glued.py` (read-only, opens no database). All inputs gitignored.

## JP rulings on this census (2026-10-24)
1. **Split rule:** split a glued value ONLY where its words map onto EXISTING adjacent slots.
   No new word rows. No receiving slot → NBSP becomes a plain space and the form stays on its one
   slot. The governing partition for the 544 is split-eligible vs normalize-only.
2. **Fill matches on number + form, never form alone** — a GATE ASSERTION for the dry run.
3. A's 191 name rows are out of scope for this lane.
4. The 13 number disagreements (5 dotted neighbour, 8 other number) are EXCLUDED from the fill
   and held with the 540 same-slot list in the handoff; Isa 39:8 pos 1 = suspected slot
   misalignment.
5. The 1,420 glued forms the audit did not flag: report only, no action.
6. Plain-space wrap: dry-run note only. 7. The 30-vs-27 glued names: held (handoff).

## Control rows
| | Row | Result |
|---|---|---|
| **C1** glued set | 1Sa 17:57 pos 22 · 5495 · "his hand." · stored `χειρί αυτού` (hex …CEAF **C2A0** CEB1…, one NBSP) · last slot of the verse; the slot before is 3588 τη · app cell `5495-1473` "χειρί αυτού" "his hand." (one cell, two numbers) · Lexicon χειρι → 5495 χειρ, αυτου → 1473 εγω | **PASS (normalize-only)** — no receiving slot; becomes `χειρί αυτού` with a plain space, on 5495 |
| **C2** missing-form set | Gen 4:8 pos 1 · 2036 · V.AAI3S · no abp_surface row, reader shows ἔπω · app **είπε** · Lexicon **2036 επω**, ειπε listed (p.163) | **PASS** |

## Counts
| | Bucket | Count | Notes |
|---|---|---:|---|
| **A** | Missing printed form | **4,058** | no drift: PA re-run list = 4,059 lines incl. header |
| | → exactly one lemma | **3,793** | 3,722 form listed + 2 form = headword + 69 pronoun via 1473 |
| | → more than one lemma | **0** | check fired on a planted second lemma first |
| | → none | **265** | 191 names (out of scope) · 33 unlisted · 28 English-in-Greek · **13 excluded** (5 dotted neighbour + 8 other number — ruling 4) |
| **B** | Glued NBSP values flagged by the audit | **544** | all 544 are in the table-wide list (1,964) |
| | → **split-eligible** | **182** | OT 176 · NT 6 — breakdown below |
| | → split-conflict (receiver holds a different form) | **4** | listed below — hold |
| | → split-ambiguous (two neighbours could take it) | **1** | Isa 41:14 pos 3 ολιγοστός Ισραήλ (both neighbours are name slots) — hold |
| | → **normalize-only** | **357** | 350 no receiving slot (incl. C1) · 6 three-word values · 1 whole value is one Lexicon form (Eze 23:47 pos 6 κατακέντει αυτάς — the book prints that two-word phrase as a form line under 2621.2). 26 of the 357 hold a word not in the Lexicon |
| **C** | 33 unlisted / 28 English-in-Greek / 69 pronouns under 1473 | **33 / 28 / 69** | no drift; rows in `abp_surface_fill_census_leftovers.csv` |
| **D** | Split-eligible rows whose receiving slot is also an A row | **45** | every one hands over the SAME word A has for that slot (27 pronoun, 12 other, 6 name) — the fill must write each slot once |

**Split-eligible 182, by what the receiving slot holds now:**
| Receiving slot | Count | What the split does | Evidence |
|---|---:|---|---|
| name slot already holding the same name | 92 | trims the glued slot only (removes a visible duplicate: "ην Νώε" + "Νώε") | receiver's own stored form |
| empty pronoun slot | 48 | trims + gives the pronoun slot its form | Lexicon number + form (via 1473) |
| empty other slot | 20 | trims + gives that slot its form | Lexicon number + form |
| empty name slot | 22 | trims + gives the name slot its first Greek form — **visible change:** its Greek line moves from the English name ("Joseph") to Ιωσήφ | NOT Lexicon-provable (no names); 6 of the 22 are A's name rows |

Of the 68 empty non-name receivers, 39 are on A's list (same word) and 29 are not — why the
audit didn't list those 29 is not checked.

**Cross-check, all 186 split/conflict rows:** the word we keep on the glued slot = the app's Greek
for that slot (186/186). **Slot order:** 33 of the 186 receivers sit on the opposite side from
the Greek word order ("γυναικί αυτού" pos 22 → the 846 slot is pos 21, "his wife") — ABP
positions follow the English order, so both sides are tried. The first pass missed these.

**The 4 conflicts:** 2Ki 20:12 pos 19 ηρρώστησεν+Εζεκίας → pos 20 holds Εζεκίαν · Jon 1:17 pos 9
ην+Ιωνάς → pos 10 holds Ιωνάν · Eze 7:4 pos 13 επί+σε → pos 12 (1473) holds σου · Dan 9:5 pos 14
κριμάτων+σου → pos 13 (4675) holds **των** (an article form on a pronoun slot — looks misplaced).

**The 1,420 not flagged (report only):** normalize-only 1,394 (1,315 of them are ONE Lexicon entry
spelled as two words — ου μη 3766.2, ου δε μη 3762.1 …) · split-eligible 23 · ambiguous 3 (Φαάθ
Μωάβ ×2, Νήργελ Σαρασάρ — two-word names).

## Notes for the dry run
- **Gate assertion (ruling 2):** every written form matches the slot's number + form in the
  Lexicon (or the receiver's own stored form); never form alone. 101 of A's resolved forms would
  match more than one lemma if the number were ignored.
- **Plain-space wrap:** abp_surface today has 1,964 NBSP forms and 0 plain-space forms. Nothing in
  the reader reads the NBSP; the only change is that a normalized two-word form can wrap.
- **28 values hold a doubled NBSP** (all OT, e.g. Exo 23:18 'θυσιάσματος␣␣μου'): a straight swap
  would leave two spaces.
- The 22 empty-name-slot splits change what the reader shows on a name slot — flag them in the
  dry-run expected picture.

## Files
- `abp_surface_fill_census_glued.csv` — all 1,964 glued rows: partition, kept word, receiving
  slot (position, number, current form), app number + Greek, both neighbours, `receiver_in_A`.
- `abp_surface_fill_census_leftovers.csv` — C's 130 rows.

---

# Step 2 — DRY RUN (read-only) — script ready, PA run pending

JP rulings on the census (2026-10-24): A 3,793 → fill; 69 pronouns → fill; 33 unlisted → form
only, lemma held; 28 English-in-Greek → held; names + the 13 → out of lane. B 182 splits go
(the 22 name splits as their own class — app is the authority for names); 357 normalize go
(doubled NBSP → one space); 4 conflicts + Isa 41:14 held (Dan 9:5, Eze 7:4 suspected slot
errors); D 45 written once, both sources must agree. 1,420 unflagged: no action. Gate: dry run
only — no copy, no apply.

Script: `scripts/dryrun_abp_surface_fill.py` (opens bible.db read-only; writes only its own CSV +
report; matching rules imported from `census_abp_surface_glued.py`, the one copy — refactor
proved byte-identical census output, and its level logic matches the lane (b) join on 4,058/4,058).

## Three things the dry run settles differently from the ruling text — each is the verdict's call
1. **Reconciliation total.** "3,793 + 69 + 33" counts the 69 pronouns twice — 3,793 already
   includes them (3,722 + 2 + 69). A-route fills = 3,724 + 69 + 33 = 3,826, of which 3 are held
   (item 3), so **3,823**.
2. **No lemma write.** abp_surface has no lemma column; the reader's lemma comes from the lexicon
   by the slot's number; the only lemma column is `words.lemma` (a words-table column read by audits
   and the name builder, not by the reader). The Lexicon's lemma is also unfit to store: no accents,
   and on 296 of 3,793 rows it is not the headword we serve (ἀποκρίνω for ἀποκρίνομαι, "εσται" as
   1510.8.3's headword, "ειδω,ειδεω,οιδα" lists, misprints like "προστασσα"; the 69 pronouns all read
   εγω). The CSV shows served lemma / words.lemma / Lexicon lemma side by side; no new column.
3. **App letter ἡ → ή (proposal).** The app never prints ή (U+03AE); it prints ἡ (U+1F21) in its place
   — 274 of 286 times mid-word in the 10/24 test fetch, where no breathing can stand. The audit folds
   accents away, so it never showed. 530 of the forms to fill carry it. Not in the JP-ruled
   DEFECT_MAP; the dry run applies it for the fill only and control E1 measures it on every
   same-letter surface pair (expect: app never prints ή, ours never ἡ, ours ή at ≥ 99% of the spots).

## New holds found while building it
- **Deu 4:45 pos 10/11** (name split): our glued 'ελάλησε Μωυσης' (no accent) vs the app's Μωυσής
  — the D sources disagree, so the whole split is held (G2 fired on real data).
- **3 app characters with no ruling:** Num 12:3 pos 5 'πρα=ς' and Pro 14:30 pos 0 'πρα=θυμος' ('='
  where ΰ belongs — the Lexicon's text layer has the same '='); **Psa 60:0 pos 22** — the app prints the
  name 'Ἰωάβ' on a 1473 pronoun slot (suspected slot misalignment).

## Pre-registered expected picture (the script prints expected | actual)
| Class | Expected | | Class | Expected |
|---|---:|---|---|---:|
| fill_resolved | 3,722 | | split_trim | 92 |
| fill_pronoun | 69 | | split_keep | 89 |
| fill_unlisted (lemma held) | 32 | | split_receive | 68 |
| held_unmapped_letter | 3 | | split_receive_name | 21 |
| held_english_in_greek | 28 | | normalize | 357 |
| held_number_disagreement | 13 | | held_split_conflict | 4 |
| out_of_lane_name | 191 | | held_split_ambiguous | 1 |
| D / agree / with A-route fill / name | 45 / 44 / 39 / 6 | | held_D_disagree | 1 |
| unflagged_glued (no action) | 1,420 | | **writes** | **4,411** = 3,873 insert + 538 update |

abp_surface after an apply = 391,130 + 3,873 = **395,003**. Controls: C1 1Sa 17:57 pos 22 → normalize
'χειρί αυτού' · C2 Gen 4:8 pos 1 → fill 'είπε' · C3 Gen 5:32 pos 1 → split_trim 'ην' · E1 above.
Gates: G1 number + form (live number) on every Lexicon-backed write · G2 every written D row: both
sources same bytes · G3 no slot twice (incl. a duplicate list line) · G4 no write on a held slot ·
G5 abp_surface only, existing word slots only, 0 name-table writes · G6 written forms: no NBSP, no ἡ,
monotonic Greek only. **Every check fired on a planted fault first** (stand-in db built from the
exported TSVs): drift ×2, duplicate line, E1 negative, ἡ in a written form, and forced G1/G3/G4/G5.

## For the apply (not now)
- translit: 538 updated rows keep a stale translit and 3,873 new rows have none → re-run
  `scripts/build_abp_translit.py` after.
- `build_abp_surface.py` DROPs and rebuilds its table: a later re-run would wipe the fill unless the
  fill is a re-runnable step after both backfills. The health-check floor (389,244) only rises.
