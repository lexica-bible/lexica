# Greek-header hand-table — batch 2 record (JP-approved 2026-07-31, apply chain pending)

Seven names admitted from the UNRESOLVED slice 151–300 (JP paste 2026-07-31) under
the batch-1 rule: every printed form the SAME stem declined, headword printed on
ABP's own pages. Classification verified against the full bh_scrape per-verse dump
(pasted in-session, both commands run by JP on PA). Slice 1–150 was a verified
NULL (all spelling-variance / accent-only / gentilic-mixed — record in the session;
adonijah + artaxerxes near-misses blocked by page-attested variant rows).

| name | headword | headword's own verses (scrape) | other forms (same stem) |
|---|---|---|---|
| cyrus | Κύρος | 2Ch 36:23 · Ezr 1:2,1:7,1:8,4:3,5:13,5:14,6:3 | Κύρου (gen, incl. lowercase κύρου Dan 1:21 — typo class), Κύρω (dat, Isa 44:28/45:1) |
| damascus | Δαμασκός | Eze 27:18 · Gen 15:2 · Isa 17:1 · Zep 2:9 · Isa 7:8 | Δαμασκού / Δαμασκώ / Δαμασκόν case forms, OT+NT |
| darius | Δαρείος | Dan 5:31,6:9,6:25 · Ezr 6:1,6:12,6:13 | Δαρείου (gen), Δαρείω (dat), Δαρείε (voc — see flag 2) |
| dinah | Δίνα | Gen 30:21 · 34:1 · 34:13 | Δίναν (acc ×4), Δίνας (gen ×3) — exact 20-row match to the split census |
| berechiah | Βαραχίας | 1Ch 9:16 · 1Ch 15:23 · 2Ch 28:12 | Βαραχία (1Ch 3:20, 15:17), Βαραχίου (Zec 1:1, 1:7, Neh 6:18) |
| coniah | Ιεχονίας | Jer 22:24 | Ιεχονίου (Jer 37:1) |
| cononiah | Χωνενίας | 2Ch 31:12 | Χωνενίου (2Ch 31:13) |

## Recorded conditions + flags
1. **κύρου Dan 1:21 lowercase** — same word, lowercase first letter; documented
   typo class (batch-1 Οχοζιόυ precedent). Header Κύρος; page form stays.
2. **Δαρείε (voc ×1 in the split census) absent from the scrape dump** — the split
   file counts words-table rows; that form's carrier row evidently reaches the
   census via a non-scrape source. The form itself is a clean vocative of the one
   stem, so admission stands; LOCATE the carrier row during the gate run and
   record its verse here before swap.
3. **Shared surfaces (azaziah/uzziah precedent, headers are display, identity is
   the xref):** cononiah + chenaniah both print Χωνενίας (chenaniah stays
   per-verse — its own forms vary); coniah + jeconiah share the Ιεχον- forms
   (jeconiah is its own UNRESOLVED key, later slice).
4. **EGYPT HELD — its admission condition failed as stated.** JP's ruling admitted
   egypt conditional on the form census showing "no seventh form hiding". It did:
   beyond the split line's six forms the scrape shows Αίγυπτε ×1 (clean vocative)
   plus four damaged singletons (Αίγυπτου, Αιγύπτον, Αιγύπτωου, Αιγύπου) and the
   stray-mark shape `΄ Αιγυπτος` ×3. All same stem — likely still typo-class —
   but that is a re-ruling, not a met condition. Await JP's call on the refined
   dump (command in session).
5. **DISCOVERY (standing, affects future batches):** greek_header_split.txt CAPS
   its per-name form list (~6 forms). For high-count names the split line is NOT
   the full form inventory — admission needs the bh_scrape census (egypt is the
   proof: 4 singleton forms invisible in the split line). Low-count names where
   listed forms sum to the row count are unaffected.

## Apply chain (standing, unchanged from batch 1)
Hand table rows landed in git (this commit) → scratch rebuild
(build_pn_greek_identity on a copy) → gate_greek_header CONTROL FIRST (batch-2
pins must FAIL on live-vs-live, PASS on scratch; batch-1 pins now pass on live
and can no longer fire) → pre-swap name-scope proof (flipped rows = exactly
these seven headwords) → JP checkpoint → swap (bible.db.rollback, single-rollback
rule) → deploy reload → served spot-check on an upgraded header (cyrus Ezr 1:1
"of Cyrus" should head Κύρος).
