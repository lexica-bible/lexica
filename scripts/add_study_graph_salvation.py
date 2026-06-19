#!/usr/bin/env python3
"""Add the SALVATION argument GRAPH ("How are we saved?") into study.db (PA-only).

Same shape + tooling as add_study_graph.py (the Baptism graph) — a shared pool of CLAIMS
joined by per-tradition LINKS (see argmap.py). This graph maps ONE axis only: the GROUND of
justification — faith alone vs faith + (grace-wrought) works. Other salvation fights (can it
be lost? who does God save?) are separate graphs.

    workon bible-env
    python scripts/add_study_graph_salvation.py             # DRY RUN: stress test + resolve verses
    python scripts/add_study_graph_salvation.py --apply     # write it to study.db (published)

The stress-test verdict needs NO database (pure logic); verse text resolves from bible.db the
same way the Study tab does. Re-running REPLACES the same graph (stable id).

DESIGN NOTES (the four fairness fixes folded in, from the Claude-chat review 2026-06-18):
  1. TENSE AXIS. Final-judgment verses (Rom 2:6-7,13, Matt 25, Matt 7:21) feed a SHARED node
     "judged according to works at the last day" that BOTH sides grant (solid). Only the leap
     to "works ground INITIAL justification" is the contested thesis. Pulling a final-tense
     verse back to the ground of initial justification is the tense-axis stretch -> rated weak.
     (Same split as the Baptism graph's two conclusion boxes.)
  2. THREE SENSES of dikaioo on the board, not two: declare-righteous (forensic, tradition) /
     make-righteous (infused, tradition) / show-vindicate (demonstrative, a real lexical sense).
     Plus the pistis split: living trust vs bare assent (James 2:19 — demons "believe" and
     shudder), feeding "James's dead faith is not Paul's faith." The demonstrative-dikaioo and
     living-pistis nodes are what the Berean overlay attaches to, so they go in now.
  3. FAITH+WORKS is the real position, not the caricature. Its backbone is GRACE-INITIATED
     cooperation (Trent: unmerited initial grace; Gal 5:6 / Phil 2:13 "God works in you" =
     Spirit-wrought works), NOT "salvation by autonomous human effort."
  4. ONE shared pool, NO pre-sorting verses into camps. Gal 5:6 and Phil 2:12-13 are SHARED
     contested nodes both overlays pull opposite ways (the pinned-box flip). James 2:24 is NOT
     a clean mirror of Rom 4 -> rated weak: 2:23 quotes the same Gen 15:6 Paul leans on and
     calls Abraham's obedience its "fulfillment" (internal counter-evidence, against-the-grain).

STRENGTH RUBRIC (audited for even-handedness across overlays):
  solid     = the text states it directly, or both sides grant it
  contested = a disputed inference / a contested definition (forensic vs infused; works=all vs
              pre-grace merit; love forms faith)
  weak      = a real stretch even granting charity (James 2:24 read at face value against its
              own 2:23 context; a final-tense verse used for the ground of INITIAL justification)
"""
import argparse
import json
import os
import sys
import time

# scripts/ live one level below the app root, where argmap.py / core.py / views_study.py sit.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argmap   # pure logic, no database — safe to import anywhere

# ── The graph to add — edit this block ───────────────────────────────────────
GRAPH_ID = "salvation_how"
TITLE = "Salvation — how are we saved?"
INTRO = ("Faith alone, or faith plus works? Two traditions read the same Paul and the same "
         "James and reach opposite conclusions. This lays out each chain and shows that the "
         "real fight is not the verses but two buried definitions — what 'justify' means, and "
         "what 'works' Paul excludes — pulled onto the board so you can see where each side "
         "actually load-bears. (A third 'Narrow road' overlay is a stub, for hand-shaping.)")
PUBLISHED = True

# Claims: the shared pool. Verse claims carry a `ref` (resolves to text, clickable in the
# reader) + a short `label` for the chart box; interpretive claims have no ref.
# provenance: text/lexicon are GROUNDED; tradition/conjecture/inference/conclusion are not.
CLAIMS = {
    # ── grounded source verses (one shared pool — NOT pre-sorted into camps) ──
    "v_eph2_8":   {"provenance": "text", "ref": "Ephesians 2:8-9", "label": "grace through faith, not works",
                   "text": "'By grace you have been saved through faith... not of works, lest anyone boast'"},
    "v_rom3_28":  {"provenance": "text", "ref": "Romans 3:28", "label": "justified by faith apart from works",
                   "text": "'A man is justified by faith apart from works of the law'"},
    "v_rom4_4":   {"provenance": "text", "ref": "Romans 4:4-5", "label": "faith counted, not working",
                   "text": "'To the one who does not work but believes... his faith is counted as righteousness'"},
    "v_gen15_6":  {"provenance": "text", "ref": "Genesis 15:6", "label": "Abraham believed, counted righteous",
                   "text": "'Abraham believed God, and it was counted to him as righteousness' — quoted by BOTH Paul (Rom 4) and James (2:23)"},
    "v_gal2_16":  {"provenance": "text", "ref": "Galatians 2:16", "label": "not by works of the law",
                   "text": "'A person is not justified by works of the law but through faith in Jesus Christ'"},
    "v_titus3_5": {"provenance": "text", "ref": "Titus 3:5", "label": "not by works of righteousness",
                   "text": "'Not by works done in righteousness, but according to his mercy he saved us'"},
    "v_rom11_6":  {"provenance": "text", "ref": "Romans 11:6", "label": "if by grace, not of works",
                   "text": "'If by grace, then it is no longer on the basis of works'"},
    "v_eph2_10":  {"provenance": "text", "ref": "Ephesians 2:10", "label": "created for good works",
                   "text": "'We are his workmanship, created in Christ Jesus for good works' — works as the result of salvation"},
    "v_james2_17":{"provenance": "text", "ref": "James 2:17", "label": "faith without works is dead",
                   "text": "'Faith by itself, if it does not have works, is dead'"},
    "v_james2_19":{"provenance": "text", "ref": "James 2:19", "label": "the demons believe, and shudder",
                   "text": "'You believe that God is one; you do well. Even the demons believe — and shudder!'"},
    "v_james2_21":{"provenance": "text", "ref": "James 2:21-23", "label": "Abraham justified by works (Isaac)",
                   "text": "'Was not Abraham justified by works when he offered Isaac?'... and the Scripture (Gen 15:6) was 'fulfilled'"},
    "v_james2_24":{"provenance": "text", "ref": "James 2:24", "label": "justified by works, not faith only",
                   "text": "'A person is justified by works and not by faith alone'"},
    "v_gal5_6":   {"provenance": "text", "ref": "Galatians 5:6", "label": "faith working through love",
                   "text": "'Faith working through love' (pistis di' agapes energoumene) — SHARED: fruit, or love forming faith?"},
    "v_phil2_12": {"provenance": "text", "ref": "Philippians 2:12-13", "label": "work out salvation, God works in you",
                   "text": "'Work out your own salvation... for it is God who works in you' — SHARED: grace producing fruit, or real cooperation?"},
    "v_rom2_6":   {"provenance": "text", "ref": "Romans 2:6-7", "label": "according to his works (final)",
                   "text": "'He will render to each one according to his works' — at the day of judgment"},
    "v_rom2_13":  {"provenance": "text", "ref": "Romans 2:13", "label": "doers of the law justified (final)",
                   "text": "'The doers of the law will be justified' — final tense, at judgment"},
    "v_matt25":   {"provenance": "text", "ref": "Matthew 25:31-46", "label": "sheep and goats, by deeds (final)",
                   "text": "The sheep and goats divided at the last judgment by what they did"},
    "v_matt7_21": {"provenance": "text", "ref": "Matthew 7:21", "label": "not 'Lord, Lord' but does the will (final)",
                   "text": "'Not everyone who says to me Lord, Lord... but the one who does the will of my Father'"},

    # ── lexical senses (grounded in the lexicon — a real range of the words) ──
    "def_dikaioo_demonstrate": {"provenance": "lexicon", "label": "dikaioo = show / vindicate righteous",
                   "text": "dikaioo also bears the demonstrative sense 'show / vindicate to be righteous' (cf. Luke 7:35; Rom 3:4) — not only 'declare' or 'make'"},
    "def_pistis_living": {"provenance": "lexicon", "label": "pistis = living trust / allegiance",
                   "text": "pistis is trust / faithful allegiance — an inherently active fidelity, not bare intellectual assent"},

    # ── the two contested DEFINITIONS pulled onto the board (the real fight) ──
    "def_dikaioo_forensic": {"provenance": "tradition", "label": "justify = declare righteous (forensic)",
                   "text": "'Justify' = God DECLARES the sinner righteous, a legal verdict, righteousness imputed and received by faith"},
    "def_dikaioo_infused":  {"provenance": "tradition", "label": "justify = make righteous (infused)",
                   "text": "'Justify' = God MAKES the sinner righteous, a real inward change (righteousness infused) that the believer's works share in"},
    "def_works_paul_all":   {"provenance": "tradition", "label": "Paul's 'works' = every work",
                   "text": "The 'works' Paul excludes = every human work, even grace-wrought ones — so works never ground justification"},
    "def_works_paul_premerit": {"provenance": "tradition", "label": "Paul's 'works' = pre-grace merit",
                   "text": "The 'works' Paul excludes = works done apart from grace to earn the first grace; grace-wrought works of love still genuinely justify"},

    # ── interpretive claims ──
    "c_through_faith":  {"provenance": "inference", "label": "Justified through faith",
                   "text": "We are justified through faith (both sides grant this much — the dispute is over 'alone')"},
    "c_faith_counted":  {"provenance": "inference", "label": "Faith counted apart from works",
                   "text": "Faith itself is counted as righteousness, apart from prior works (Abraham, Gen 15:6)"},
    "c_dead_faith_not_saving": {"provenance": "inference", "label": "James's dead faith isn't Paul's faith",
                   "text": "The 'faith' James calls dead — bare assent, which the demons have (2:19) — is not the living faith Paul means; the two differ"},
    "c_works_evidence": {"provenance": "inference", "label": "Works are fruit, not the ground",
                   "text": "Works are the necessary fruit and evidence of saving faith, never its ground"},
    "c_final_works":    {"provenance": "inference", "label": "Judged by works at the last day",
                   "text": "At the final judgment God judges according to works (final tense) — BOTH sides grant this"},
    "c_grace_initiated":{"provenance": "inference", "label": "Salvation begins in unmerited grace",
                   "text": "Justification begins in unmerited grace (initial grace), not earned — both sides grant this (Trent affirms it too)"},
    "c_grace_cooperation": {"provenance": "tradition", "label": "Grace-wrought works cooperate",
                   "text": "The believer cooperates with grace; Spirit-wrought works of love are part of HOW one is justified, not merely its fruit"},
    # Convergence nodes: each sub-argument funnels through ONE contested joint, so the chart and
    # the route-printout show the real load path (NOT parallel edges that hide a shared premise).
    "c_faith_excludes_works": {"provenance": "inference", "label": "Faith excludes works as ground",
                   "text": "Scripture ties justification to faith and sets it against works — so works are excluded as the GROUND (the positive faith-alone case, before James is even raised)"},
    "c_james_works_ground": {"provenance": "inference", "label": "James: works justify (as ground)",
                   "text": "James says a person is justified by works — read as works being part of the GROUND of justification"},

    # ── conclusions (theses) ──
    "t_faith_alone":  {"provenance": "conclusion", "label": "Faith alone (works are fruit)",
                   "text": "We are justified by faith alone; works are the necessary fruit, never the ground"},
    "t_works_ground": {"provenance": "conclusion", "label": "Grace-wrought works share the ground",
                   "text": "Grace-wrought works of love are part of the ground of justification, not merely its fruit"},
    "t_berean":       {"provenance": "conclusion", "label": "Living faith — works demonstrate (STUB)",
                   "text": "[STUB — to hand-shape with chat] Saved by faith alone, but never a faith that stays alone: living faith works, and works DEMONSTRATE (dikaioo) righteousness rather than grounding it"},
}

OVERLAYS = [
    {
        "tradition": "Faith alone (sola fide)",
        "thesis": "t_faith_alone",
        "rejects": ["c_grace_cooperation"],
        "links": [
            # ── ROUTE 1: the POSITIVE case. All the faith-not-works verses converge on ONE node,
            #    which crosses ONE contested joint — the erga-scope reading (def_works_paul_all).
            #    Cut that joint and the whole positive case is severed: it IS a load-bearing joint
            #    for this route (not parallel edges hiding a shared premise).
            {"from": "v_eph2_8",  "to": "c_through_faith", "relation": "supports", "strength": "solid"},
            {"from": "v_rom3_28", "to": "c_through_faith", "relation": "supports", "strength": "solid"},
            {"from": "v_gal2_16", "to": "c_through_faith", "relation": "supports", "strength": "solid"},
            {"from": "v_titus3_5", "to": "c_through_faith", "relation": "supports", "strength": "solid"},
            {"from": "v_rom11_6", "to": "c_through_faith", "relation": "supports", "strength": "solid"},
            {"from": "v_rom4_4",  "to": "c_faith_counted", "relation": "supports", "strength": "solid"},
            {"from": "v_gen15_6", "to": "c_faith_counted", "relation": "supports", "strength": "solid"},
            {"from": "c_through_faith", "to": "c_faith_excludes_works", "relation": "supports", "strength": "solid"},
            {"from": "c_faith_counted", "to": "c_faith_excludes_works", "relation": "supports", "strength": "solid"},
            # THE ERGA JOINT — the single contested step the entire positive case must cross.
            {"from": "c_faith_excludes_works", "to": "t_faith_alone", "relation": "supports", "strength": "contested",
             "why": "ERGA-SCOPE JOINT. 'Justified through faith' is common ground; 'faith ALONE — no work grounds it' rests on reading Paul's excluded 'works' as EVERY work (incl. grace-wrought). If 'works' = boundary-markers / pre-grace merit, the positive case does not reach faith-alone."},
            {"from": "def_works_paul_all", "to": "c_faith_excludes_works", "relation": "requires", "strength": "contested",
             "why": "The erga-scope premise, named explicitly: Paul's excluded 'works' = all works. Faith+works disputes exactly this."},
            {"from": "def_dikaioo_forensic", "to": "c_faith_excludes_works", "relation": "requires", "strength": "contested",
             "why": "Also leans on 'justify' = DECLARE righteous (imputed); if it = MAKE righteous, inward change and its works are part of it."},

            # ── ROUTE 2: the JAMES rebuttal. A SEPARATE route to the same thesis, crossing a
            #    DIFFERENT contested joint — the dikaioo-sense / living-pistis reading. This is why
            #    there is no SINGLE chokepoint: two routes, two distinct definitional joints.
            {"from": "v_james2_19", "to": "c_dead_faith_not_saving", "relation": "supports", "strength": "contested",
             "why": "Demons 'believe' and shudder — the faith James calls dead is bare assent, not the living trust Paul means."},
            {"from": "def_pistis_living", "to": "c_dead_faith_not_saving", "relation": "supports", "strength": "contested",
             "why": "If pistis is by nature living/active fidelity, a 'dead faith' is not faith in Paul's sense at all."},
            {"from": "def_dikaioo_demonstrate", "to": "c_works_evidence", "relation": "supports", "strength": "contested",
             "why": "If James's 'justified by works' = SHOWN/vindicated righteous (a real lexical sense), works prove faith without grounding it."},
            {"from": "v_james2_24", "to": "c_works_evidence", "relation": "supports", "strength": "weak",
             "why": "Faith-alone must read 'justified by works... not by faith alone' as vindicated-before-others; the plain wording resists that, and 2:23 quotes the same Gen 15:6 Paul uses — its own context fights this use (weak)."},
            {"from": "c_dead_faith_not_saving", "to": "c_works_evidence", "relation": "supports", "strength": "contested",
             "why": "If the dead faith isn't Paul's faith, James's works show LIVING faith — i.e. works as evidence, not ground."},
            # The tense axis: final-judgment verses -> shared 'final works' node (solid, both grant)
            {"from": "v_rom2_6",   "to": "c_final_works", "relation": "supports", "strength": "solid"},
            {"from": "v_rom2_13",  "to": "c_final_works", "relation": "supports", "strength": "solid"},
            {"from": "v_matt25",   "to": "c_final_works", "relation": "supports", "strength": "solid"},
            {"from": "v_matt7_21", "to": "c_final_works", "relation": "supports", "strength": "solid"},
            {"from": "c_final_works", "to": "c_works_evidence", "relation": "supports", "strength": "contested",
             "why": "Both sides grant judgment 'according to' works at the last day (final tense); faith-alone reads 'according to' as the EVIDENCE assessed, not the GROUND of the verdict."},
            # Shared flip nodes (faith+works pulls these the other way)
            {"from": "v_gal5_6",  "to": "c_works_evidence", "relation": "supports", "strength": "contested",
             "why": "'Faith working through love' read as faith that PRODUCES love — works as fruit; faith+works reads love as completing/forming faith."},
            {"from": "v_phil2_12", "to": "c_works_evidence", "relation": "supports", "strength": "contested",
             "why": "'Work out your salvation, God works in you' read as grace PRODUCING the believer's works (fruit), not cooperation that contributes."},
            {"from": "v_eph2_10", "to": "c_works_evidence", "relation": "supports", "strength": "contested",
             "why": "'Created for good works' — works as the designed RESULT of salvation; faith+works reads them as the goal we're saved INTO, part of the saving purpose."},
            # THE DIKAIOO/PISTIS JOINT — the single contested step the James rebuttal must cross.
            {"from": "c_works_evidence", "to": "t_faith_alone", "relation": "supports", "strength": "contested",
             "why": "DIKAIOO-SENSE JOINT. If works are only fruit/evidence, faith alone is the ground — but reading James's 'justified by works' as vindication (demonstrative dikaioo) rather than ground is the disputed step this whole route rests on."},
        ],
    },
    {
        "tradition": "Faith + works (Catholic / Orthodox)",
        "thesis": "t_works_ground",
        "rejects": ["c_works_evidence"],
        "links": [
            # ── ROUTE A: grace-INITIATED cooperation (NOT autonomous effort). Crosses ONE joint —
            #    the erga-premerit + infused reading at the cooperation step.
            {"from": "v_eph2_8", "to": "c_grace_initiated", "relation": "supports", "strength": "solid"},
            {"from": "c_grace_initiated", "to": "c_grace_cooperation", "relation": "supports", "strength": "contested",
             "why": "From unmerited initial grace (granted by all) to grace-empowered cooperation that CONTRIBUTES — the synergistic step faith-alone denies."},
            {"from": "v_gal5_6", "to": "c_grace_cooperation", "relation": "supports", "strength": "contested",
             "why": "'Faith working through love' (pistis di' agapes energoumene) read as love FORMING/completing faith — the works of love are how faith justifies, not mere fruit."},
            {"from": "v_phil2_12", "to": "c_grace_cooperation", "relation": "supports", "strength": "contested",
             "why": "'Work out your salvation, for God works in you' read as real Spirit-enabled cooperation that contributes to final salvation."},
            {"from": "c_grace_cooperation", "to": "t_works_ground", "relation": "supports", "strength": "contested",
             "why": "ERGA-PREMERIT / INFUSED JOINT. If Spirit-wrought works of love are part of how one is justified, works share the ground. Rests on 'justify' = MAKE righteous and on Paul's excluded 'works' = pre-grace merit only."},
            {"from": "def_dikaioo_infused", "to": "c_grace_cooperation", "relation": "requires", "strength": "contested",
             "why": "Needs 'justify' = God MAKES righteous (infused), a real change works participate in; if it = DECLARES (forensic/imputed), works can't be part of the ground."},
            {"from": "def_works_paul_premerit", "to": "c_grace_cooperation", "relation": "requires", "strength": "contested",
             "why": "Needs Paul's excluded 'works' to mean pre-grace/meritorious works (done to earn the first grace); grace-wrought works of love then still genuinely justify."},
            # ── ROUTE B: James read at face value. A SEPARATE route, funneled through ONE node so its
            #    joint (dikaioo = made/declared, not demonstrated) is visible — not parallel edges.
            {"from": "v_james2_24", "to": "c_james_works_ground", "relation": "supports", "strength": "weak",
             "why": "'Justified by works, not by faith alone' read plainly — but the same context quotes Gen 15:6 (Paul's faith-text) and calls Abraham's obedience its 'fulfillment' (2:23), and dikaioo may mean VINDICATED. Carries its own counter-evidence — weak."},
            {"from": "v_james2_17", "to": "c_james_works_ground", "relation": "supports", "strength": "contested",
             "why": "'Faith without works is dead' — faith-alone grants this but reads dead works as proof of dead (non-saving) faith, not works as the ground."},
            {"from": "v_james2_21", "to": "c_james_works_ground", "relation": "supports", "strength": "contested",
             "why": "'Abraham justified by works when he offered Isaac' — faith+works reads dikaioo here as 'made righteous'; faith-alone reads 'shown righteous' (demonstrative)."},
            {"from": "c_james_works_ground", "to": "t_works_ground", "relation": "supports", "strength": "contested",
             "why": "DIKAIOO-SENSE JOINT. James's 'justified by works' counts toward the GROUND only if dikaioo here = made/declared righteous, not 'shown/vindicated' (the demonstrative sense)."},
            # ── ROUTE C: the tense axis. The shared final-works node, pulled (weakly) back to the
            #    GROUND of INITIAL justification — the tense stretch, rated weak.
            {"from": "v_rom2_6",   "to": "c_final_works", "relation": "supports", "strength": "solid"},
            {"from": "v_rom2_13",  "to": "c_final_works", "relation": "supports", "strength": "solid"},
            {"from": "v_matt25",   "to": "c_final_works", "relation": "supports", "strength": "solid"},
            {"from": "v_matt7_21", "to": "c_final_works", "relation": "supports", "strength": "solid"},
            {"from": "c_final_works", "to": "t_works_ground", "relation": "supports", "strength": "weak",
             "why": "Judgment 'according to works' is FINAL-tense and BOTH sides grant it; pulling it back to the GROUND of INITIAL justification crosses the tense axis — weak (these verses are about the last day, not how one first stands righteous)."},
            # Faith-alone's counters, raised on this overlay (contested -> not decisive)
            {"from": "v_rom4_4",  "to": "t_works_ground", "relation": "undercuts", "strength": "contested",
             "why": "'To the one who does NOT work but believes, his faith is counted' — Paul explicitly separates the counting from working; faith-alone's counter."},
            {"from": "v_rom3_28", "to": "t_works_ground", "relation": "undercuts", "strength": "contested",
             "why": "'Justified by faith apart from works of the law' — the direct faith-alone counter."},
        ],
    },
    {
        # ── STUB OVERLAY — minimal honest spine, to hand-shape with Claude chat. ──
        # Attaches to the demonstrative-dikaioo + living-pistis + dead-faith nodes (per the
        # chat review: that's the Berean read's home). Verdict will compute to DEPENDS; expand
        # the thesis + links once the position is nailed down.
        "tradition": "Narrow road (Berean) — STUB",
        "thesis": "t_berean",
        "rejects": [],
        "links": [
            {"from": "v_gen15_6", "to": "c_faith_counted", "relation": "supports", "strength": "solid"},
            {"from": "v_rom4_4",  "to": "c_faith_counted", "relation": "supports", "strength": "solid"},
            {"from": "c_faith_counted", "to": "t_berean", "relation": "supports", "strength": "contested",
             "why": "Faith counted righteous apart from works — the faith-alone base the Berean read keeps."},
            {"from": "def_pistis_living", "to": "c_dead_faith_not_saving", "relation": "supports", "strength": "contested"},
            {"from": "v_james2_19", "to": "c_dead_faith_not_saving", "relation": "supports", "strength": "contested",
             "why": "Demons 'believe' and shudder — dead assent is not living faith."},
            {"from": "c_dead_faith_not_saving", "to": "t_berean", "relation": "supports", "strength": "contested",
             "why": "Living faith inevitably works; the 'faith' that doesn't is not saving faith — so 'faith alone' and 'faith that works' aren't rivals."},
            {"from": "def_dikaioo_demonstrate", "to": "t_berean", "relation": "requires", "strength": "contested",
             "why": "The Berean read takes James's 'justified by works' as SHOWN/vindicated (demonstrative dikaioo), dissolving the Paul/James tension without works grounding salvation."},
            {"from": "v_james2_24", "to": "t_berean", "relation": "supports", "strength": "weak",
             "why": "Read as vindication, not ground (same weak rating as elsewhere — 2:23's Gen 15:6 'fulfillment' context)."},
        ],
    },
]
# ─────────────────────────────────────────────────────────────────────────────


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _build_json():
    return {"intro": INTRO, "claims": CLAIMS, "overlays": OVERLAYS, "notes": "", "related": []}


def _c(cid):
    c = CLAIMS.get(cid) or {}
    return c.get("text", cid)


def stress():
    """Print the stress-test verdict for every overlay — pure logic, no database."""
    out = argmap.analyze(CLAIMS, OVERLAYS)
    for ov, v in zip(OVERLAYS, out["verdicts"]):
        print("\n== %s ==" % ov["tradition"])
        print("  Conclusion: %s" % _c(ov["thesis"]))
        if v.get("overturned"):
            print("  VERDICT: OVERTURNED — a grounded, solid objection knocks out the conclusion.")
        elif v["grounded"]:
            print("  VERDICT: STANDS — reachable from the text on solid links alone.")
        elif v["gap"]:
            print("  VERDICT: INCOMPLETE — a step is missing; unreachable even granting every link.")
        elif v["load_bearing"]:
            print("  VERDICT: DEPENDS ON A NON-SOLID JOINT.")
            for l in v["load_bearing"]:
                print("    >>> load-bearing joint [%s]: %s -> %s" % (l["strength"], _c(l["from"]), _c(l["to"])))
        else:
            print("  VERDICT: DEPENDS ON CONTESTED STEPS (reachable only through non-solid links; no single joint).")
        if v.get("defeated"):
            print("  Knocked out by a grounded objection: %s" % ", ".join(_c(c) for c in v["defeated"]))
        if ov.get("rejects"):
            print("  Rejects: %s" % ", ".join(_c(c) for c in ov["rejects"]))
    diff = out["diff"]
    print("\n== Where they part ==")
    shared = ", ".join((CLAIMS.get(c) or {}).get("ref", c) for c in diff["shared_verses"])
    print("  Verses leaned on by more than one side: %s" % (shared or "(none)"))
    for s in diff.get("seams", []):
        print("  Seam: %s [%s] — held by %s; rejected by %s"
              % (_c(s["claim"]), s["provenance"], ", ".join(s["used_by"]), ", ".join(s["rejected_by"])))


def dry_run():
    """Stress test (no db) + resolve every verse reference (from bible.db). Returns True if
    all references found text."""
    print("STRESS TEST  (no database needed)")
    print("=" * 70)
    stress()
    print("\n\nVERSE RESOLUTION  (from bible.db)")
    print("=" * 70)
    from views_study import _resolve_ref, _parse_ref   # imported here so the stress test runs without a db
    bad = []
    for cid, c in CLAIMS.items():
        ref = c.get("ref")
        if not ref:
            continue
        if not _parse_ref(ref):
            print("  [BAD REF]  %s  (%s)" % (ref, cid))
            bad.append(ref)
            continue
        hits = _resolve_ref(ref)
        text = " ".join(h["text"] for h in hits) if hits else ""
        if not text:
            print("  [NO TEXT]  %s  (%s)" % (ref, cid))
            bad.append(ref)
        else:
            print("  %s — %s" % (ref, text[:110] + ("..." if len(text) > 110 else "")))
    print("\n%d claims, %d verse refs, %d with a problem." %
          (len(CLAIMS), sum(1 for c in CLAIMS.values() if c.get("ref")), len(bad)))
    if bad:
        print("Fix these before --apply: %s" % ", ".join(bad))
    return not bad


def apply():
    from core import study_db
    conn = study_db()
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS entries ("
            " id TEXT PRIMARY KEY, type TEXT NOT NULL, title TEXT NOT NULL,"
            " json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft',"
            " created TEXT NOT NULL, updated TEXT NOT NULL,"
            " deleted INTEGER NOT NULL DEFAULT 0)"
        )
        now = _now()
        status = "published" if PUBLISHED else "draft"
        payload = json.dumps(_build_json(), ensure_ascii=False)
        existing = conn.execute("SELECT created FROM entries WHERE id=?", (GRAPH_ID,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE entries SET type='graph', title=?, json=?, status=?, updated=?, deleted=0"
                " WHERE id=?",
                (TITLE, payload, status, now, GRAPH_ID),
            )
            print("Updated existing graph '%s' (%s)." % (GRAPH_ID, status))
        else:
            conn.execute(
                "INSERT INTO entries (id, type, title, json, status, created, updated, deleted)"
                " VALUES (?, 'graph', ?, ?, ?, ?, ?, 0)",
                (GRAPH_ID, TITLE, payload, status, now, now),
            )
            print("Inserted new graph '%s' (%s)." % (GRAPH_ID, status))
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Add the salvation argument graph to study.db.")
    ap.add_argument("--apply", action="store_true", help="write to study.db (default is a dry run only)")
    args = ap.parse_args()

    ok = dry_run()
    if not args.apply:
        print("\n(dry run only — re-run with --apply once it looks right)")
        sys.exit(0)
    if not ok:
        print("\nRefusing to --apply while references have problems. Fix them first.")
        sys.exit(1)
    apply()
    print("\nDone. Open the Study tab -> Graphs -> %s to see it." % TITLE)
