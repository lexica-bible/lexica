# DRILL SHEET — Lane C doctrine round (303 multi-candidate witness slots)

Status: **REVIEWER VERDICT LANDED 2026-07-30 — approved with hardenings:**
1. The chapter filter is candidacy ONLY, structurally: no slot lands on the filter
   alone; the per-name run audit is the identity step, the filter just orders work.
2. Type sanity is BIDIRECTIONAL + compound-aware: candidate type must match token
   usage AND the slot must have no unexamined compound adjacency (1Ch 10:12 gilead
   is a Jabesh-gilead fragment — route compound fragments to the compound lane;
   Lane C must not eat them).
3. Per-name audit sampling: long-run narrative names land as runs after a Lane-B
   style sample; names whose slots cross books/genres (jacob-the-man vs Isaiah's
   Jacob-the-nation) get EVERY slot eyeballed — metonymic uses are where
   one-candidate-in-chapter lies. Genre-crossing flag goes in the census.
4. Card sentence DISTINCT from Lane A (different evidence, different sentence),
   reviewer-proposed: "ABP's Greek text reads {Name} here. Several people share
   this name; the identification follows the surrounding passage, where only this
   {person/place} appears." Served under kind='witness', tag context-run.
5. The 5 multi-in-chapter slots (two Joashes, Azariah genealogy) = named residue
   with the word-position class; don't force them.
Build order: hardened screen (Gilboa known-negative must FAIL first) -> per-name
census with genre-crossing flags -> audit plan -> JP checkpoint -> build.
Parent: DRILL_witness_divergence.md (lane order verdict) + LANE_B_adjudication.md.

## The pile
303 slots / 95 names where ABP attests the name, no TIPNR candidate covers the
verse, and the name has SEVERAL candidates (jesus 38, judah 21, jacob 16,
elijah 15, gilead 13, joseph 11, pharaoh 9, saul 8 …). The question is not
witness (settled in Lane A's doctrine) but WHICH candidate.

## Sizing screen (2026-07-30, production matcher, full population)
Rule screened: "exactly one of the name's candidates has TIPNR coverage
somewhere in the SAME CHAPTER."
- unique-in-chapter: **212 slots**
- zero-in-chapter but unique-in-book: **24**
- multiple candidates in the chapter: **5** (azariah 1Ch 6 genealogy, joash
  2Ch 25:20 both kings, benaiah, harim — genuinely hard, park)
- neither: **62** (incl. the batch-3 jabish residue — already routed)

## THE EXHIBIT — why unique-in-chapter alone is NOT evidence (pre-registered
known-negative for any future screen)
gilead 1Ch 10:12 screens to **Gilboa_Mount@Jdg.7.3-1Ch** — the only "gilead"-
matching candidate with coverage in 1Ch 10 (Saul's death at Mount Gilboa). But
the verse's token is "Jabesh-gilead" (the men of Jabesh retrieving the bodies) —
binding it to a MOUNTAIN would be flatly wrong. Same shape at 1Sa 31:11.
Candidacy-in-context is still candidacy; today's Lane-A lesson applies at
chapter grain exactly as it did at verse grain. **Any Lane C screen must FAIL
this exhibit before its passes count.**

## Proposed evidence standard (for verdict)
A Lane C slot binds only when ALL of:
1. **Unique-in-chapter** (the screen above) — the candidate filter.
2. **Type sanity** — the candidate's TIPNR section (person/place) must match the
   token's usage in the verse; kills Gilboa-for-Jabesh-gilead shapes where the
   token sits inside a compound or place phrase (cross-check against the batch-3
   adjacency dump for compound partners).
3. **Per-name run audit** — slots group into narrative runs (elijah = 1Ki 17–19,
   jacob = Gen 29–48, jesus = gospels); each NAME's full slot list is eyeballed
   as a unit with its proposed entity before landing, sample-audited by the
   reviewer like Lane B pile 1 (a name is the audit unit, not a slot).
4. Evidence tag: own class (proposal: `context-run`), kind='witness' (these are
   still witness-attested verses — TIPNR lacks the verse), card sentence = the
   approved Lane A sentence (it claims only bound facts, so it holds here).
   OPEN QUESTION for the reviewer: does a context-run bind deserve a weaker or
   identical sentence vs the sole-entity Lane A binds?

## Expected yield if the standard holds
~200 of the 212, dominated by the famous names (jesus 38 — NT narrative, one
Jesus-of-Nazareth candidate active per chapter; jacob/joseph/elijah/saul
narrative runs). The 5 multi-in-chapter + 62 neither + screen failures stay
residue with routes.

## Out of scope
Word-position lane (~118) · contested readings (pile 3) · chip-merge display ·
any build before the verdict + JP checkpoint on the standard.
