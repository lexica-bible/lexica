# CENSUS — abp_surface FILL, step 1 (read-only)

2026-10-24. JP ruling: lane (1) abp_surface FILL is go; lane (2) waits until the fill is live.
Read-only step: no writes, no fix code, no dry run. Inputs: `HANDOFF_abp_source_material.md`.

**Where each number comes from.** A and C ran locally on `abp_helps/missing_forms_resolved.tsv`
(the lane (b) join of the 4,058-row `missing_printed_forms.tsv` PA wrote on 10/24) against
`abp_helps/analytical_lexicon.tsv`. B and D need `abp_surface` itself, which is PA-only — they
wait on the PA commands at the bottom. Both inputs are gitignored (third-party text).

## Control rows

| | Row | Result |
|---|---|---|
| **C2** missing-form set | Gen 4:8 pos 1 · our number 2036 · V.AAI3S · no abp_surface row, reader shows ἔπω · app prints **είπε** ("Cain said") · Lexicon **2036 επω** VERB, form ειπε listed ("2aor. act. ind. 3sg.", p.163) · join level A | **PASS** — resolves exactly as stated |
| **C1** glued set | 1Sa 17:57 "χειρί αυτού" | **NOT YET RESOLVED — PA needed, and a doubt (below)** |

**C1, what is known so far.**
- Lexicon side resolves: `χειρι` → **5495 χειρ** NOUN fem., "dat. sg." (p.410); `αυτου` → **1473 εγω**
  PRONOUN personal, "masc-neut. gen. 3sg." (p.112). ABP files every αὐτός form under its raw
  1473; our build stores that family as 846, so the αυτού side resolves only through the
  pronoun rule (same as the 69 pronoun rows in C).
- **The doubt:** the ABP source text (`abp_texts/abp_ot_texts/abp_1samuel.txt` line 463,
  diagnosis-grade) ends the verse `... was inG1722 G3588 his hand.G5495` — "his hand" is ONE
  slot carrying only 5495. There is no 846 slot for αυτού. If the built words table matches,
  the proposed split has nowhere to put its second token: splitting into two slots would mean a
  new words row (not a fill), and the clean fill would be "χειρί" on the 5495 slot with αυτού
  dropped from the form. Whether pos 22 is that slot, and what the app does with αυτού, needs
  PA command 1. **Per the ruling, if command 1 confirms one slot, C1 does not resolve as stated
  and B stops for a ruling.**
- Stored value (byte-exact) — not in hand; PA command 1.

## Counts

| | Bucket | Count | Notes |
|---|---|---:|---|
| **A** | Missing printed form, total | **4,058** | matches handoff (OT 3,687 · NT 371) |
| | → exactly one lemma | **3,793** | OT 3,446 · NT 347. = 3,722 form listed + 2 form is the headword + 69 pronoun via 1473 |
| | → more than one lemma (ambiguous) | **0** | no (number, folded form) pair in the Lexicon carries two lemmas. Check fired on a planted second lemma (319 hits) before this 0 was trusted. Est 3:12 pos 13 sits on 2004, a number the book prints on two entries — the form picks ἐπιτάσσω, one lemma |
| | → none | **265** | 191 names (book has no names) · 33 unlisted · 28 English-in-Greek · 8 form found only under another number · 5 dotted neighbour (same base, other suffix) |
| | (info) resolved rows whose form, number ignored, maps to >1 lemma | 101 | the slot's number is what settles these — a fill must key on number + form, never form alone |
| **B** | Glued NBSP values, total | **pending PA** | handoff: 544 (audit class "our value is a two-word NBSP value", surface target) |
| | → splits cleanly, every token in Lexicon | pending PA | |
| | → ≥1 token unresolved | pending PA | |
| | → token count disagrees with slot numbering | pending PA | C1 suggests this bucket is real (one slot, two tokens) |
| **C** | 33 unlisted | **33** ✔ | rows in CSV |
| | 28 English-in-Greek | **28** ✔ | rows in CSV |
| | 69 pronouns under 1473 | **69** ✔ | rows in CSV |
| | Drift vs handoff | **none** | all three match |
| **D** | Rows in both A and B (same slot) | **0 by construction** | A = slots with no abp_surface row; B = abp_surface rows. The real overlap question is a glued value whose second word is the NEXT slot's missing form — counted once B's list is in (PA command 2 carries both neighbours) |

Leftover row lists: `docs/handoffs/abp_surface_fill_census_leftovers.csv` (130 rows: bucket,
verse, position, our number, word type, morph, what the reader shows now, app form, app English,
Lexicon lemma). "Stored value" for these is empty by definition — no abp_surface row; the
reader falls back to the dictionary word, which is the column shown.

## PA commands (all read-only — sqlite3 opened `-readonly`; the audit opens the db read-only)

```bash
cd ~/bible-db
# 1. C1: every slot of 1Sa 17:57 with its stored form, plus the app's slots for the verse
sqlite3 -readonly -header -separator $'\t' ~/bible-db/bible.db "SELECT w.position, w.strongs, w.english, w.morph, s.form, hex(s.form) FROM verses v JOIN words w ON w.verse_id=v.id LEFT JOIN abp_surface s ON s.verse_id=v.id AND s.position=w.position WHERE v.book='1Sa' AND v.chapter=17 AND v.verse=57 ORDER BY w.position"
awk -F'\t' '$1=="1 Samuel" && $2==17 && $3==57' abp_app_html/abp_app_slots.tsv
# 2. B (table-wide): every abp_surface form holding an NBSP, with both neighbour slots
sqlite3 -readonly -header -separator $'\t' ~/bible-db/bible.db "SELECT v.book, v.chapter, v.verse, s.position, w.strongs, w.english, w.morph, s.form, wp.strongs AS prev_strongs, wp.english AS prev_english, sp.form AS prev_form, wn.strongs AS next_strongs, wn.english AS next_english, sn.form AS next_form FROM abp_surface s JOIN verses v ON v.id=s.verse_id LEFT JOIN words w ON w.verse_id=s.verse_id AND w.position=s.position LEFT JOIN words wp ON wp.verse_id=s.verse_id AND wp.position=s.position-1 LEFT JOIN abp_surface sp ON sp.verse_id=s.verse_id AND sp.position=s.position-1 LEFT JOIN words wn ON wn.verse_id=s.verse_id AND wn.position=s.position+1 LEFT JOIN abp_surface sn ON sn.verse_id=s.verse_id AND sn.position=s.position+1 WHERE instr(s.form, char(160)) > 0 ORDER BY s.verse_id, s.position" > ~/nbsp_surface_rows.tsv && wc -l ~/nbsp_surface_rows.tsv
# 3. negative-space check: NBSP vs ordinary-space forms vs all rows
sqlite3 -readonly ~/bible-db/bible.db "SELECT sum(instr(form,char(160))>0), sum(instr(form,' ')>0), count(*) FROM abp_surface"
# 4. the exact 544: re-run the lane (a) audit with its slot dump (the existing missing list is left alone)
PYTHONIOENCODING=utf-8 python3 scripts/audit_abp_app_vs_surface.py ~/bible-db/bible.db abp_app_html/abp_app_slots.tsv --missing-out ~/mpf_rerun.tsv --dump ~/abp_app_dump.tsv > ~/abp_app_audit_rerun.txt; head -8 ~/abp_app_audit_rerun.txt; awk -F'\t' '$9=="surface" && $12=="mm_ours_nbsp"' ~/abp_app_dump.tsv > ~/nbsp_544.tsv && wc -l ~/nbsp_544.tsv ~/mpf_rerun.tsv
```

Then: paste the output of 1, 3 and the `wc` lines, and download `~/nbsp_surface_rows.tsv` +
`~/nbsp_544.tsv` (PA Files tab) into the local `abp_app_html/` (gitignored). B and D are then
computed locally against the Lexicon. `~/mpf_rerun.tsv` at 4,059 lines (header + 4,058) confirms
A has not drifted since 10/24.
