# Greek-header hand-table — batch 1 record (JP-approved 2026-07-30)

Six names upgraded from per-verse forms to one ABP-cited headword via
scripts/greek_header_nominatives.tsv. Classification verified against the
bh_scrape name-slot rows (full per-verse dump pasted in-session): every
alternate form is the SAME stem declined, every headword is printed on ABP's
own pages — inside ruling (b), nothing imported, nothing majority-voted.

| name | headword | headword's own verses | other forms (same stem) |
|---|---|---|---|
| ahaziah | Οχοζίας | 1Ki 22:40,48,50 · 2Ki 8:24,8:25,8:26,9:16,9:21,9:27 · 2Ch 22:1,22:2,22:6 · 1Ch 3:11 | Οχοζίου (gen), Οχοζίαν (acc), Οχοζία |
| antilebanon | Αντιλίβανον | Jos 1:4 · Deu 1:7 · Deu 3:25 | Αντιλιβάνου (Deu 11:24), Αντιλιβάνω (Jos 9:1) |
| arabia | Αραβία | Eze 27:21 · Gal 4:25 | Αραβίαν ×3, Αραβίας ×7 |
| ashkelon | Ασκαλών | Zec 9:5 · Zep 2:4 | Ασκάλωνος/Ασκαλώνα case forms ×7 |
| ashtoreth | Αστάρτη | 1Ki 11:33 · 2Ki 23:13 · 2Ch 24:18 | Αστάρτης (1Ki 11:5) |
| azaziah | Οζίας | 1Ch 15:21 · 2Ch 31:13 | Οζίου (1Ch 27:20) |

## Recorded conditions + flags (reviewer verdict, verbatim intent)
1. **2Ki 1:3 byte check** (pre-apply condition): JP's console paste showed
   garbled characters mid-Οχοζίου; hex check against the stored bytes required
   before the batch lands. Result recorded below when run.
2. **2Ch 22:11 accent typo, documented not silent:** the page prints Οχοζιόυ
   (misplaced accent). The headword Οχοζίας replaces it in the HEADER; the
   page form stays what it is. This is the one header-vs-page divergence in
   the batch and it is deliberate and recorded here.
3. **azaziah/uzziah shared surface (non-blocking, pre-filed answer):** ABP
   renders Azaziah with the same Greek surface form (Οζίας) it uses for
   Uzziah. Fine at the header layer — headers are display, identity is the
   xref — but if a future question asks why two different men share a
   headword, this is the answer, recorded in advance.

## Byte-check result
2Ki 1:3 = `1|Οχοζίου` (run by JP 2026-07-30): stored bytes CLEAN — the garbling
was console-side. Condition 1 satisfied.

## Control note
The shipped hadad control now PASSES on live, so it can no longer fire as a
control. This batch's fresh detector control = the six batch pins added to
greek_header_pins.txt: they must FAIL on live-vs-live (no surface rows for
these names yet) and PASS on the scratch.

## Apply chain (standing)
Hand table rows landed in git → JP byte check → scratch rebuild
(build_pn_greek_identity on a copy) → gate_greek_header CONTROL FIRST (gate
untouched this batch, pins untouched — the built-in hadad/zion/abner controls
must fire; if the gate script is ever edited mid-arc, the checker-edited rule
adds a fresh control re-run) → JP checkpoint → swap (bible.db.rollback,
single-name rule) → deploy reload → served spot-check on an upgraded header
(ahaziah 2Ki 1:3 "of Ahaziah" should head Οχοζίας).
