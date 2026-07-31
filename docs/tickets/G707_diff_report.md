# G707 ship — slot-level diff report (scratch vs live, 2026-07-31)

Source: `g707_leavers.txt` generated on PA from the gated scratch (G3 receipt,
524 slots, sums verified). Every slot below currently serves a Greek number on
live and flips to the honest no-number state; Hebrew stays reachable through
the cross-ref (unchanged bytes). Flagged-record count everywhere: **43**.
Removal-only census: **0** (no slot changes to a different number — D1's two
attempts were caught and fixed before ship). Identity-table diffs outside this
set: **0**.

## Group A — cross-name conflations (the bug class proper) — 166 slots

| name | number it loses | slots |
|---|---|---|
| jehoiada | G914 (Barachiah) | 52 |
| sheba | G3558 ("the South") | 30 |
| mizpah | G707 (Arimathea) | 17 |
| ramah | G707 (Arimathea) — reviewer-ruled drop | 16 |
| mizpeh | G707 (Arimathea) | 14 |
| megiddo + magiddo | G717 (Armageddon) | 9 + 2 |
| greeks / greek | G1484 / G1673 | 8 / 6 |
| baalpeor | G896 (Baal) | 5 |
| put | G3033 (Libya) | 2 |
| jehoshaphat | G2748 (Kidron) | 2 |
| pekod, gazite, ashurites | G897 / G1048 / G768 | 1 each |

Already clean on live (no slots to fix, recorded honestly, not as a fired
detector): **Caphtor→G2914** (record carries two Greek numbers — the rule
never touched it) and **Sepharad→G4554** (slot never entered the
number-inheritance path).

## Group B — same-name / renamed / alternate-name drops, ticket-referred — 358 slots

Ruled correct to drop today (text-first: the number reflects what the verse
prints); each name goes verbatim to the open same-name/renamed ticket, which
decides any future allowlist. Sub-groups:

**Alternate names of the same person:** edom→G2269 Esau (117), abram→G11
Abraham (67), azariah→G3604 Uzziah (49), shallum→G2423 Jehoiachin (29),
jerubbaal + jerubbesheth→G1066 Gideon (14+1), belteshazzar→G1158 Daniel (10),
sheshbazzar→G2216 Zerubbabel (4), jedidiah→G4672 Solomon (1).

**Renamed / same place, two names:** ashdod→G108 Azotus (19) + ashdodite (1),
horeb→G4614 Sinai (17), ephrath→G965 Bethlehem (4), lod→G3069 Lydda (3),
jetur→G2484 Ituraea (2), on→G9829 Heliopolis (2), rakkath→G5085 Tiberias (1),
shiloah→G4611 Siloam (1), judah→G2449 Judea (1).

**Spelling variants not in the variant table:** molech→G3434 Moloch (6),
kanah→G2580 Cana (2), babel + babylonia + babylonian→G897 (3),
ezrahite + izrahite→G2196 Zerah forms (3), gehenna→G1067 (1).

## Notes

- The two blank-name slots under G9829 are the **On (Heliopolis)** pair — the
  slots carry no head label in the dump; not corruption.
- Group totals: A 166 + B 358 = **524** = the pinned ship population.
- The 9 would-be gainers (saul ×8 → G4549, zacharias ×1 → G2197) are HELD OUT
  (removal-only rule) — named in the 7/30 reclassification catch-up ticket.
- Cushi note for the record: the scratch holds the hand-fix value H3569
  (snapshot-restored); a fresh import writes H3570 — the snapshot is the
  canonical restore path, import re-breaks hand fixes.
