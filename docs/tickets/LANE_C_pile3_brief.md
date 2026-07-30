# Lane C pile-3 closure brief (for reviewer verdict, 2026-07-30)

**VERDICT LANDED 2026-07-30 (pasted reviewer text, verbatim):**
> **jair 1Ch 2:53 — demotion stands, final.** Compound place-name fragment; TIPNR
> covers the verse under Kiriath-jearim. Person bind was never live.
> **gilead Jos 22:11 — unbound, approved.** Contested reading; no evidence forces
> one referent. Unbound is the honest state.
> **eleazar Ezr 8:16 — unbound, approved.** TIPNR declines the bind itself ("only
> mentioned at 8:33"). Binding would import a claim the source doesn't make —
> exactly what the standing rulings forbid.
> **bunni Neh 10:14 — unbound, approved.** Verse-seam sits between two distinct
> TIPNR men and the page can't discriminate. Sole-spelling is candidacy, not
> identity — CC applied the rule correctly.
> **hodijah Neh 10:12 — bind approved, with the new class ruled narrowly.** The
> evidence chain is complete: same name, TIPNR coverage, KJV spelling match, and a
> mechanical one-verse offset rather than an identity judgment. Class definition
> I'm ruling in: *one-verse-offset witness — bind permitted only where the ABP
> token and the Hebrew record are the same TIPNR entity displaced by exactly one
> verse seam, with no competing candidate on either side of the seam.* Bunni fails
> that last clause; hodijah passes it. The class does not generalize to multi-verse
> offsets or to seams with two candidates — those come back individually.
> Condition: since this adds a pinned evidence class, the gate's class list gets
> the new row before the build, and the gate's control re-runs before its PASS
> counts (checker-edited-mid-arc rule applies).
> Then the standing chain: JP checkpoint, scratch build, control-first gates,
> swap, reload, served-layer capture on hodijah's card.

**SHIPPED 2026-07-30, full chain receipted:** control re-run first (gate A
FAILed on exactly the hodijah key vs live — checker-edit condition met) →
scratch build (`Witness verse-offset: 1 new render binds`, all other lanes
re-landed identically) → gates A/B/C PASS (newly added 1, nothing else moved) →
swap (rollback = bible.db.rollback under the new single-name rule; pre_greekhdr
retained as deep rollback until a nightly postdates the evening ships) →
deploy.sh reload (5×200) → served capture: /api/metav/entity/hodijah at
Neh 10:12 returns uniq=Hodiah@Neh.10.13, kind=witness, rule=verse-offset.
Card sentence + Strong's-fallback header label JP-approved and live in the same
deploy. LANE C RESIDUE = ZERO; word-position lane (~118) unparks per JP's
2026-07-30 ordering.

Context: Lane C shipped 2026-07-30 (201 context-run witness rows live, gates A/B/C
passed, served checks 6/6). Four held slots remain, each pre-routed in
LANE_C_adjudication.md pile 3. This brief asks for a final ruling on each so the
lane closes to zero. One Lane B leftover (hodijah) is included because the ticket
itself says to rule it with bunni (same versification-offset shape).

All evidence below re-verified this session against the ABP page text
(abp_texts/ dump) and TIPNR's raw records (line numbers cited).

## 1. jair 1Ch 2:53 — propose: finalize demotion to compound lane, no bind
ABP: "OumasphaeG* the cityG4172 of Jair.G*" — the token is a fragment of the
place-name Kiriath-jearim rendered as a phrase (the Gilboa shape). TIPNR's
Kiriath-jearim@Jos.9.17-Jer (TIPNR.txt:31185) lists 1Ch.2.53 in its own verse
coverage. The key is already hard-excluded from Lane C and the DRAFT-TSV
generator. Proposed ruling: demotion is final; the slot waits in the compound/
adjacency lane queue (with the Gilboa pair) and is CLOSED for Lane C.

## 2. gilead Jos 22:11 — propose: unbound permanent, contested-reading class
ABP: "at Gilead of Jordan, on the other side of the sons of Israel" where the
Hebrew reads geliloth ("districts of the Jordan"); the verse itself places the
altar on the Canaan side, arguing against region-Gilead. The only candidate
entity is not forced by the passage. Proposed ruling: no bind, recorded as
contested-reading honest state.

## 3. eleazar Ezr 8:16 — propose: unbound permanent, unresolved-identification
TIPNR's only Ezra-era candidate is Eleazar@Ezr.8.33 (TIPNR.txt:6106), whose own
record says "only mentioned at Ezr.8.33" (son of Phinehas, a priest receiving
the vessels). Equating him with the 8:16 messenger is an identification claim
TIPNR does not make. Proposed ruling: no bind.

## 4. bunni Neh 10:14 — propose: unbound permanent (AMBIGUOUS, stronger than
the ticket's original offset routing)
ABP Neh 10:14 ends "...Elam, and Zatthu, sons of Bunni"; ABP 10:15 is "Azgad,
Bebai". The Hebrew list has BANI closing v14 and BUNNI opening v15 — two
different TIPNR men (Bunni@Neh.10.15 = TIPNR.txt:4865, "only mentioned at
Neh.10.15"; Bani is a separate record). ABP's token sits exactly on the seam:
it could be Hebrew-Bani rendered "Bunni" by the LXX, or Hebrew-Bunni pulled up
a verse. The page cannot pick the man (sole-spelling = candidacy, never
identity). Proposed ruling: no bind, ambiguity recorded.

## 5. hodijah Neh 10:12 (Lane B leftover, same class) — propose: LAND as a
narrow versification-offset witness → Hodiah@Neh.10.13
ABP Neh 10:12: "Zaccur, Sherebiah, Shebaniah, and Hodijah" — the Hebrew list
has Zaccur/Sherebiah/Shebaniah at its v13 and Hodijah opening the NEXT Hebrew
verse; ABP folds him into v12. Unlike bunni there is NO competing neighbor
name: the token's spelling matches TIPNR's record exactly (Hodiah@Neh.10.13,
TIPNR.txt:10000, "Hodijah =KJV") and no other Hodiah/Bani-style rival sits at
the seam. Proposed evidence class if approved: "versification-offset" — bind
cites the neighbor-verse coverage explicitly; class definition limited to
list-genre verses where (a) TIPNR covers the adjacent verse, (b) the spelling
matches a named form, (c) no different name occupies the seam on the Hebrew
side. This is a NEW evidence class, so it lands only with your verdict and a
gate_pn_rulings update; if you decline the class, hodijah stays unbound like
the others and the lane still closes.

## Ask
One verdict line per slot (1–5). Anything approved lands via the standing
procedure: JP checkpoint → scratch build → gate_pn_rulings control-first →
swap → worker reload → served capture. Rollback stays bible.db.pre_laneC.
