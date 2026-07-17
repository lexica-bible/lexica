# Provenance Contract — entity cards & sourced content

Status: **DRAFT — awaiting JP review. No code changes derive from this until it's committed.**
Scope: every section of the word/entity detail card (`static/src/30-detail-panel.jsx`), the
book/chapter summary panel, and every data source that feeds them. Companion tickets:
`docs/tickets/TICKET_gentilic_binding.md`, `docs/tickets/TICKET_missing_strongs_pn.md`.

## 1. The one rule everything else derives from

**Every field on a card is labeled by the source it actually came from.** Cross-referencing
never changes attribution: if a fact was read out of TIPNR, its label says TIPNR even where
MetaV was used to find or corroborate it (e.g. the tier-3 re-tiering that consults MetaV, or
`tipnr_metav_link` used to locate a record). The label answers "who asserts this fact," not
"how did we find it."

When one visible section blends fields from two sources, the **section badge is combined**
("MetaV/TIPNR") and **per-field attribution stays available** on hover/tap (see §5). A blended
section may never carry a single-source badge.

## 2. Source registry (the canonical list)

This registry is the single description of each source. The UI tooltip text (§5) is generated
from it — never duplicated per page.

| Source key | Badge text | What it is | Tables / origin |
|---|---|---|---|
| `tipnr` | TIPNR | Tyndale Individualised Proper Names with References — the identity spine: one record per distinct person/place, with description, kin, region, reference list | `tipnr_entities`, `tipnr_entity_refs`, `pn_binding`, `tipnr` (per-Strong's types) |
| `metav` | metaV | MetaV / Viz.Bible relational dataset — rich biographical enrichment (birth/death, relationships, groups, place coords) | `metav_people` (+aliases/groups/relationships), `metav_places` (+aliases), `tipnr_metav_link` |
| `strongs` | Strong's | Strong's dictionary entries (the `bdb` table is Strong's Hebrew, NOT Brown-Driver-Briggs) | `bdb`, lexicon/dotted_lexicon lemma data |
| `lsj` | LSJ | Liddell-Scott-Jones Greek lexicon | `lsj` tables |
| `lexica` | Lexica | Our own verse-grounded dictionary (AI-drafted, hand-gated) | `lexica_def` |
| ~~`naves`~~ | ~~Nave's~~ | **REMOVED 2026-07-16 (JP): Nave's data deleted from PA; dead frontend code removed under the render charter** | — |
| `corpus` | ABP / KJV / BSB | The texts themselves: occurrence counts, verse quotes, in-verse English | `words`, `verses`, `kjv_verses`, `bsb_verses`, heb.db |
| `ai` | AI | Synthesized content, generated per request and cached — not a human-curated source | AI cache: `pn:` descriptions (Haiku), `summary` book/chapter (Sonnet/Haiku), LSJ blurbs |

Any NEW source added later gets a registry row before it gets a card section.

## 3. Per-section rules (current card, top to bottom)

| Card section (jsx) | Source label | Verse-match state (§4) | Notes |
|---|---|---|---|
| Hero headword + Strong's head band | none needed — it IS the word from the text being read | n/a | Corpus-derived; no badge |
| Bound entity card `.pnbound` | TIPNR; **MetaV/TIPNR when the rich `MetavPersonBody` is folded in** (today it shows only TIPNR — a violation of §1) | REQUIRED — this is the verse-bound path; keep "Matched to this verse" | Facts rows (Lineage/Region) = TIPNR; born/died/relationships = MetaV. Per-field attribution per §5 |
| Name-path metaV card | metaV | REQUIRED to state the opposite: "matched by name, not checked against this verse" (today it shows nothing — a violation of §4) | Only renders when no bind exists |
| AI description (`aidesc`) | AI | Already states "not verse-checked" — keep; wording may unify with the name-path line | Verse-SCOPED but not verse-CORROBORATED; the label must not imply corroboration |
| Nave's topical | Nave's | Name-keyed, not verse-matched — same "matched by name" state | |
| Strong's Hebrew (`bdb`) | Strong's | n/a (dictionary, not an identity claim) | Keep the "all its meanings" caveat under a bound entity |
| Definition block (Lexica/LSJ/Grammar/Idiom/ABP-EXT) | per existing badge | n/a | Lexica entries are AI-drafted + gated → the tooltip for the Lexica badge says so |
| Occurrence counts / verse quote / frequency | corpus (existing ABP/KJV/BSB badges) | n/a | |
| Book & chapter summary (`SummaryPanel`) | **AI — tag REINSTATED (JP ruling; it was removed, decision reversed)** | n/a | Every synthesized block sitewide carries the AI tag; no exceptions for "it reads well" |

## 4. Verse-corroboration state

Three states exist in the data; the UI must say which one the reader is looking at:

1. **Verse-matched** — a `pn_binding` render row ties this exact book/chapter/verse to the
   entity (`kind` exact/fuzzy/versification). UI: "Matched to this verse" (exists today on
   `.pnbound`). The backend already sends `tier` and `kind`; the frontend receives and ignores
   them — the contract does not require rendering the tier number, but the badge must only
   appear on genuinely bound rows.
2. **Name-matched** — looked up by surface name only (name-path metaV card, Nave's). UI must
   say so explicitly ("matched by name — not checked against this verse"). **Currently missing
   on the metaV card; this contract makes it required.**
3. **Synthesized** — AI content, verse-scoped but not corroborated. UI keeps the existing
   "not verse-checked" caveat plus the AI tag.

No section may show identity content with none of the three states visible.

## 5. Tag interactivity — one component, one registry

Every source badge is hoverable AND tappable (mobile has no hover). Backed by:
- **ONE shared tooltip component** — the existing badges (`bdb-badge`, `lsj-badge` variants)
  are static spans today; they converge on one interactive element. On mobile it opens via the
  shared `Sheet`/Menu machinery per the mobile sheet contract — no new per-card surface.
- **ONE registry of descriptions** — a single frontend map keyed by the §2 source keys. Any
  page that shows a badge reads the registry; per-page duplicated description strings are a
  contract violation.

The tooltip text states: what the source is (one sentence from §2), and the §4 state of the
section it sits on.

## 6. Name-display rule (TIPNR/MetaV section)

**A render rule, not per-record data:**
- If the entity's canonical name (TIPNR head / MetaV name) is the same as the card's hero
  headword (case/punct-insensitive), the section does NOT repeat it — the hero carries it.
- If it differs (variant spelling, gentilic → ancestor, alias), the section DOES show the
  canonical name — that's disambiguation the reader needs ("you clicked Ashchenaz; the entity
  is Ashkenaz").
Today the thin `.pnbound` variant already drops the echo while the full variant always repeats
it (`pnbound-name`, jsx ~888) — the full variant adopts the same equality check.

## 7. Entity types — the taxonomy the contract must cover

The contract covers ALL entity types, not just person and place. What the code knows today:

- `tipnr_entities.section` ∈ person | place | other (TIPNR source blocks also carry types we
  currently EXCLUDE at parse time: languages, titles, "monsters" — see `parse_tipnr`).
- `tipnr.entity_types` — per-Strong's SET, e.g. `person,place` (Adam/Canaan class).
- MetaV: type is the table (`metav_people` vs `metav_places`); `metav_people_groups` carries
  tribe/group membership tags; no deity/festival typing.
- **People groups are display-time only**: `is_people_group` (curated word list + -ites/-ians/
  -eans suffix) flips the bound card to "People / Clan" — there is NO people-group node type in
  the data; TIPNR models peoples as their eponymous-ancestor PERSON (Hittites→Heth, ~819 binds,
  ruled 2026-07-05).

Per-type rules:

| Entity type | Populated by | Label | Verse-match rule | Name rule |
|---|---|---|---|---|
| Person | TIPNR (spine) + MetaV (rich) | TIPNR or MetaV/TIPNR per §1 | §4 in full | §6 |
| Place | TIPNR + metav_places (coords) | same | §4 in full; map pin only with confident coords (existing rule) | §6 |
| People group / clan / tribe | TIPNR person node (eponymous ancestor) rendered as "People / Clan" | TIPNR | §4 in full | §6, plus the "Descended from X" line stays |
| person,place doubles (Adam, Canaan…) | tipnr.entity_types set | per the tab shown | §4 per tab | §6 per tab |

**Open items (flagged, not silently omitted):**
- **OI-1** — TIPNR's excluded blocks (languages, titles, "monsters"/creatures): currently never
  imported, so never rendered. If they're ever admitted, they need registry rows + per-type
  rules first. Titles partially exist already via per-referent links (the seven pharaohs) —
  those follow the Person row.
- **OI-2** — deities/idols, festivals/events, dynasties/houses: no dedicated typing found in
  TIPNR/MetaV tables or render code. If the inventory queries below surface them (e.g. inside
  `tipnr_entities.section='other'`), each gets a rule before it gets a card treatment.
- **OI-3** — whether a true people-group NODE should exist (vs. the ancestor-person render) is
  raised by the gentilic ticket; the contract takes no position until that ticket resolves.

### Inventory queries — JP runs these on PA (read-only), results ground the taxonomy

```
sqlite3 ~/bible-db/bible.db "SELECT section, count(*) FROM tipnr_entities GROUP BY section;"
sqlite3 ~/bible-db/bible.db "SELECT entity_types, count(*) FROM tipnr GROUP BY entity_types ORDER BY 2 DESC;"
sqlite3 ~/bible-db/bible.db "SELECT uniq, head, descr FROM tipnr_entities WHERE section NOT IN ('person','place') LIMIT 40;"
sqlite3 ~/bible-db/bible.db "SELECT kind, count(*) FROM pn_binding WHERE render=1 GROUP BY kind;"
sqlite3 ~/bible-db/bible.db "SELECT count(*) FROM metav_people; SELECT count(*) FROM metav_places;"
sqlite3 ~/bible-db/bible.db "SELECT group_name, count(*) FROM metav_people_groups GROUP BY group_name ORDER BY 2 DESC LIMIT 30;"
```
The third query is the important one: whatever lives in `section='other'` is the unknown
taxonomy. Anything it surfaces without a row in the table above becomes a new open item.

## 8. Audit checklist (defines "correct"; the sweep is a follow-up session)

For EVERY card section × every entity type that can render it:

| # | Check |
|---|---|
| A | Source label present? |
| B | Label correct per §1 (says who asserts the fact, combined badge where blended)? |
| C | §4 state visible (matched / name-only / synthesized) where the section makes an identity claim? |
| D | Badge interactive — shared tooltip, registry text, works on tap? |
| E | Name-display follows §6 (no echo on equality, shown on difference)? |
| F | AI content carries the AI tag (incl. book/chapter summaries)? |

Known failures going in (so the sweep starts honest): `.pnbound` shows TIPNR-only while
rendering MetaV fields (B); name-path metaV card shows no §4 state (C); no badge anywhere is
interactive (D); summary panel has no AI tag (F); `.pnbound` full variant always echoes the
name (E).
