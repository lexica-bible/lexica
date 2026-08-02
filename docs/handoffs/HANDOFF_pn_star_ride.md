# HANDOFF — lane ②: PN-star merged-verb fix session (the Mat 27/28 class)

Written 2026-08-02 at the close of the ruling-10 ride. Read CLAUDE.md first, then
TODO.md item ② (the charter — both session-open rulings already JP-confirmed),
then `docs/tickets/TICKET_detector_gap.md` + `docs/tickets/TICKET_509_article_slot_resweep.md`
§6j–§6l (the article-slot precedent this lane inherits).

## What this session is

Fix the name-slot merge class: ABP attaches a verb/content word's English to the
adjacent proper-noun star chunk (or the reverse) — `Mat 27:26 "scourging Jesus"`
(class A, star carries it) / `Mat 26:1 "Jesus finished"` (class B, the number
carries it, star blank). **Revised count 4,996** (A 2,237 · B 2,759 = B1
roster-pinned 2,668 + B2 roster-silent 91). Detector
`scripts/audit_pn_star_verb_merge.py` — controls proven, `--lanes` landed.
③ (the B2 91-row eyeball) rides along or precedes. The superseded old 145 list
is never a baseline.

## Hard sequencing (both rulings on record)

- **One change, one rebuild, a full detector run between.** This fix gets its
  OWN rebuild ride after the fix session; it never folds with the article-slot
  pass (which is now LIVE — the 8/1 ride).
- Fix = build-side redistribution for star slots + rebuild; regression pin
  `tests/test_pn_star_verb_merge.py` flips to the split shape when the fix lands.
- ⑤ (38 bracketed article-slot rows) stays out — own cycle, own bracket-ordering
  ruling.

## Inherit from the 8/1 ride (paid for four times — do not rediscover)

1. **Any figure about a post-correction artifact derives THROUGH the correction
   layer** (Rahlfs/TAGNT + lexicon + BH — the build's real inputs), derivation
   command committed with the figure. Four pre-registered numbers broke in one
   ride measured bare.
2. **Counts are tripwires; the member set rules.** The swap condition pattern is
   `--predict-vs`-style member set-equality with a NAMED tail allowance (the
   finish-tail patches legally edit rows the per-verse prediction can't model —
   on 8/1 that was idios ×13 + blank-G fills ×2; this lane's pass may have its
   own list, derive it, name every member).
3. **A bare aggregate wears an arbitrary label** — GROUP BY every declaration
   read, commit the query text.
4. Counting basis: the build counts per DECISION, a plan may count per SLOT —
   print both bases in any sizing instrument.
5. The rebuild ride procedure = `/rebuild-words` as amended 8/1 (restore_frozen_pn
   declared 6 → retire --fresh-rebuild with the five-class split → identity →
   binder → gates; serving deltas from the 8/1 ride are now IN live, so the next
   ride's retirement deltas vs live should be ≈0 — pre-register that).
6. Tee every long run; the confirm prompt hides behind a pipe (`echo rebuild |`).
7. PA quota is 10 GB now; the build still wants ~1 GB free for its copies.

## Standing invariants (from the ②/G707 records)

- Adjacency is NOT the merge discriminator — whether the carrier holds a name is
  (`Gen 23:19` is adjacent AND genuine). A guard built on adjacency was already
  written and reverted once.
- The article-slot class MIXES origins — some rows are ABP-attested supplied
  English, not drops; sort display-vs-data per spot. Same-family non-star case
  `Mat 28:13 "His disciples"` — "His" is real Greek, not an italic.
- Roster frozen: any import_tipnr/TIPNR.txt change → `check_roster_regression.py`
  CLEAN first.
- CC never queries bible.db — paste-ready sqlite3 one-liners, JP runs, verdict
  gates on every dry-run→apply.

## Paste block for the reviewer chat

> Lexica, lane ② — the PN-star merged-verb class (Mat 27:26 "scourging Jesus" /
> Mat 26:1 "Jesus finished"; 4,996 rows: A 2,237 · B1 2,668 · B2 91 eyeball).
> Charter = TODO ②, both session-open rulings JP-confirmed 7/31; detector
> proven with lanes + halt paths. Sequencing: fix session now, its OWN rebuild
> ride after (one change, one rebuild, detector run between — the article-slot
> pass shipped 8/1 and is live). The session inherits the 8/1 ride's traps:
> true-layer derivation for every pre-registered figure, member set-equality
> with a named tail allowance as the swap condition, GROUP BY'd declaration
> reads, both counting bases printed. First deliverable before any code: the
> fix's predicate written down in full, red-first controls on both
> orientations, and a pre-registered member-level expected picture derived
> through the correction layer.
