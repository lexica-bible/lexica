# Greek-header hand-table — batch 2 record (SHIPPED 2026-07-31)

**SHIPPED 2026-07-31, full chain receipted:** control run FAILED on exactly the
seven batch-2 pins vs live (`got []` ×7; hadad/zion/abner + all six batch-1
pins PASS — the fresh control) → scratch build (`hand-table nominatives
loaded: 13`) → gates A/B/C PASS (`->surface (headword) 134`, all else 0; all
16 pins PASS) → pre-swap scope proof: the 134 flipped rows are EXACTLY the
seven headwords (Δαμασκός 63 · Δαρείος 24 · Κύρος 24 · Δίνα 10 · Βαραχίας 8 ·
Ιεχονίας 3 · Χωνενίας 2), all source=surface → swap (rollback =
bible.db.rollback) → deploy reload 5×200 → served captures (post-reload, API):
Ezr 1:1 cyrus pos 5 + 19 = lemma Κύρος source=surface H3566 intact; Act 9:2
damascus pos 5 = Δαμασκός source=surface H1834 intact. UNRESOLVED pool now
857 (was 864).

**METHOD REFINEMENT (JP-ruled at verdict):** flip counts land BELOW the raw
census because numbered slots are already Greek-headed by abp-tag/tipnr and
gate-B-barred from the hand table — future batches predict size from a
NUMBERLESS-slot count, not the raw census (batch-1 names matched their census
only because they had no numbers anywhere).

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
4. **EGYPT HELD — JP-RULED 2026-07-31, final for this batch.** The refined dump
   surfaced TWO rows where ABP's page prints the GENTILIC (a different word, not
   a case form) under an "Egypt" label: Deu 28:27 Αιγυπτίω · Isa 19:23 Αιγύπτιοι.
   Ruling: hold — the adonijah precedent (rejected at 38/40 clean) applies a
   fortiori; admitting egypt would make the admission standard ratio-dependent.
   The standard is PAGE-ATTESTATION, never "what the entity is" (that reframe
   was proposed and rejected). Nonconforming-row documentation for the future
   mechanism (11 rows):
   - typo class (7): `΄ Αιγυπτος` 1Sa 6:6 · 1Sa 12:8 · Nah 3:9; Αίγυπτου
     Heb 11:27; Αιγύπτον Jer 46:2; Αιγύπτωου Jer 44:12; Αιγύπου Gen 41:30
   - clean vocative (1, no issue): Αίγυπτε Psa 135:9
   - different-word gentilic rows (2, the blockers): Deu 28:27 · Isa 19:23
   - remaining rows: clean Αίγυπτος/Αιγύπτου/Αίγυπτον/Αιγύπτω declensions
   **BANKED MECHANISM (JP 2026-07-31, own scoped proposal when raised):
   per-row exclusion in the hand table — name admitted, listed slots excepted,
   exceptions receipted with addresses. Would recover egypt (~1,189 rows),
   adonijah (38), artaxerxes on the same terms. Not this batch.**
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
