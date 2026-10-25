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
