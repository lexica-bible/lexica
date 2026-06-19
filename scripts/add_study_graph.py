#!/usr/bin/env python3
"""Add a hand-authored argument GRAPH straight into study.db (PA-only).

A graph is a pool of CLAIMS joined by per-tradition LINKS (see argmap.py). Each claim is
tagged with a provenance — text/lexicon are GROUNDED in the source; tradition/conjecture/
inference are NOT. Each link carries a strength (solid/contested/weak) and a `why` (why it's
rated that way — i.e. whose call it is and on what basis). An overlay may also `reject`
claims another tradition leans on. The stress test asks, per tradition: is the conclusion
reachable from grounded claims on solid links alone? If not, it names the load-bearing joint
(or flags an outright gap).

    workon bible-env
    python scripts/add_study_graph.py             # DRY RUN: stress test + resolve verses, write nothing
    python scripts/add_study_graph.py --apply     # write it to study.db (published)

The stress-test verdict needs NO database (pure logic); the verse text resolves from
bible.db the same way the Study tab does. Re-running REPLACES the same graph (stable id).

STRENGTH RUBRIC (audited for even-handedness across all overlays):
  solid     = the text states it directly, or both sides grant it
  contested = a disputed inference — BOTH arguments from silence sit here (credo's "infants
              excluded" and paedo's "households included infants" get the SAME bar), as do the
              systematic bridges (covenant continuity, baptism-replaces-circumcision, baptism-saves)
  weak      = a real stretch even granting charity
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
GRAPH_ID = "baptism_who"
TITLE = "Baptism — who, and what does it do?"
INTRO = ("Three traditions read the same New Testament and reach different conclusions. "
         "This lays out each side's chain and asks where it actually load-bears — and where "
         "two sides pull the very same verse in opposite directions.")
PUBLISHED = True

# Claims: the shared pool. Verse claims carry a `ref` (resolves to text, clickable in the
# reader); interpretive claims have no ref. provenance: text/lexicon grounded; the rest not.
CLAIMS = {
    # ── grounded source verses ──  (label = short caption for the chart boxes)
    "v_acts2_38":  {"provenance": "text", "ref": "Acts 2:38", "label": "repent and be baptized",
                    "text": "'Repent and be baptized... for the forgiveness of sins'"},
    "v_acts8_12":  {"provenance": "text", "ref": "Acts 8:12", "label": "believed, then baptized",
                    "text": "Samaritans were baptized after they believed Philip's preaching"},
    "v_mark16_16": {"provenance": "text", "ref": "Mark 16:16", "label": "believes and is baptized",
                    "text": "'Whoever believes and is baptized will be saved'"},
    "v_eph2_8":    {"provenance": "text", "ref": "Ephesians 2:8-9", "label": "grace through faith",
                    "text": "'By grace you are saved through faith... not of works'"},
    "v_1pet3_21":  {"provenance": "text", "ref": "1 Peter 3:21", "label": "baptism now saves you",
                    "text": "'Baptism now saves you'"},
    "v_john3_5":   {"provenance": "text", "ref": "John 3:5", "label": "born of water and Spirit",
                    "text": "'Unless one is born of water and the Spirit...'"},
    "v_luke23_43": {"provenance": "text", "ref": "Luke 23:43", "label": "the thief, unbaptized",
                    "text": "The thief on the cross — 'today you will be with me in Paradise', unbaptized"},
    "v_acts2_39":  {"provenance": "text", "ref": "Acts 2:39", "label": "and to your children",
                    "text": "'The promise is to you and to your children'"},
    "v_households":{"provenance": "text", "ref": "Acts 16:33", "label": "the jailer's household",
                    "text": "Acts 16:33 — the Philippian jailer's whole household was baptized"},
    "v_col2":      {"provenance": "text", "ref": "Colossians 2:11-12", "label": "baptism and circumcision",
                    "text": "Baptism set beside circumcision — 'buried with him in baptism'"},
    "v_gen17":     {"provenance": "text", "ref": "Genesis 17:12", "label": "infant circumcision sign",
                    "text": "Circumcision given to Abraham's household, infants included, as the covenant sign"},
    "v_jer31":     {"provenance": "text", "ref": "Jeremiah 31:31-34", "label": "the new covenant",
                    "text": "'They shall all know me, from the least to the greatest' — the new covenant"},
    "v_heb8":      {"provenance": "text", "ref": "Hebrews 8:10-11", "label": "all will know the Lord",
                    "text": "Hebrews 8 applies Jeremiah's new covenant — 'all shall know me'"},
    "v_lydia":     {"provenance": "text", "ref": "Acts 16:15", "label": "Lydia's household",
                    "text": "Acts 16:15 — Lydia and her household were baptized (no members described)"},
    "v_stephanas": {"provenance": "text", "ref": "1 Corinthians 1:16", "label": "Stephanas's household",
                    "text": "1 Corinthians 1:16 — Paul baptized the household of Stephanas (no members described)"},
    "obj_household_hearers": {"provenance": "text", "ref": "Acts 16:32-34", "label": "house heard + believed",
                    "text": "In the jailer's house the word is preached to all (16:32) and the rejoicing is householdwide, tied to believing (16:34) — presuming hearers who can understand"},

    # ── interpretive claims (not grounded) ──
    "c_belief_first":      {"provenance": "inference", "label": "Faith comes first",
                            "text": "In every baptism the New Testament narrates, the person first professed faith"},
    "c_faith_alone":       {"provenance": "inference", "label": "Saved by faith, not works",
                            "text": "Salvation is received by faith, not by a rite performed on a person"},
    "c_baptize_believers": {"provenance": "inference", "label": "Baptize believers",
                            "text": "Baptism is for those who profess faith (both sides grant this much)"},
    "c_regenerate_membership": {"provenance": "inference", "label": "Membership by faith, not lineage",
                            "text": "New-covenant membership is constituted by faith and regeneration, not physical descent"},
    "c_covenant_kids":     {"provenance": "tradition", "label": "Children in the covenant",
                            "text": "Believers' children stay inside the covenant community, so the covenant sign still belongs to them"},
    "c_household_infants": {"provenance": "conjecture", "label": "Households included infants",
                            "text": "Those baptized households included infants"},
    "c_baptism_for_circ":  {"provenance": "tradition", "label": "Baptism replaces circumcision",
                            "text": "Baptism is the new-covenant replacement for circumcision, so it goes to the same recipients"},
    "def_grace_infused":   {"provenance": "tradition", "label": "Grace = an infused quality",
                            "text": "Grace here is a conferred quality the rite imparts — not only God's favor exercised by faith"},
    "obj_grace_charis":    {"provenance": "text", "ref": "Ephesians 2:8", "label": "charis = favor, by faith",
                            "text": "In the NT charis is God's favor shown through faith (Eph 2:8); none of the cited baptism verses use the word charis"},
    "obj_pet_pledge":      {"provenance": "text", "ref": "1 Peter 3:21", "label": "pledge, not washing",
                            "text": "1 Peter 3:21 says baptism saves 'not as the removal of dirt from the body, but as the pledge of a good conscience toward God'"},
    "obj_mark_unbelief":   {"provenance": "text", "ref": "Mark 16:16", "label": "condemned for unbelief",
                            "text": "Mark 16:16 ties condemnation to unbelief alone, dropping baptism from the negative clause; the longer ending is textually disputed"},

    # ── conclusions ──
    "t_credo_who":  {"provenance": "conclusion", "label": "For believers only",
                     "text": "Baptism is for professing believers only — infants are excluded"},
    "t_credo_save": {"provenance": "conclusion", "label": "Baptism doesn't save",
                     "text": "Baptism does not save — it signs a salvation already received by faith"},
    "t_paedo": {"provenance": "conclusion", "label": "Baptize believers' infants",
                "text": "Baptize the infant children of believers"},
    "t_regen_grace":     {"provenance": "inference", "label": "Effects what it signifies",
                          "text": "Baptism effects what it signifies — forgiveness, new birth, salvation (the effects the texts name)"},
    "t_regen_saves":     {"provenance": "conclusion", "label": "Baptism saves",
                          "text": "Baptism saves — it does not merely signify (it effects salvation)"},
    "t_regen_necessary": {"provenance": "conclusion", "label": "Ordinarily necessary",
                          "text": "Water baptism is ordinarily necessary for salvation — the ordinary means, apart from providential hindrance (baptism of desire, the unevangelized); the qualified form most regenerationists actually hold"},

    # ── "Narrow road (Berean)" overlay — new claims (efficacy axis: what baptism does) ──
    "v_cornelius": {"provenance": "text", "ref": "Acts 10:44-47", "label": "Spirit before baptism",
                    "text": "Cornelius's household received the Holy Spirit while Peter was still speaking — before any water baptism"},
    "v_eph1":      {"provenance": "text", "ref": "Ephesians 1:13-14", "label": "Spirit = the seal",
                    "text": "'You were sealed with the promised Holy Spirit, the guarantee of our inheritance'"},
    "v_rom8_9":    {"provenance": "text", "ref": "Romans 8:9", "label": "no Spirit, not his",
                    "text": "'Anyone who does not have the Spirit of Christ does not belong to him'"},
    "v_acts11_17": {"provenance": "text", "ref": "Acts 11:17", "label": "the same gift",
                    "text": "'God gave them the same gift he gave us' — Peter defending the Gentiles' Spirit-reception"},
    "v_rom6":      {"provenance": "text", "ref": "Romans 6:3-4", "label": "buried and raised",
                    "text": "'Buried with him in baptism... raised to walk in newness of life'"},
    "c_spirit_seal":    {"provenance": "inference", "label": "Spirit = seal of salvation",
                         "text": "The Holy Spirit is the seal and guarantee of salvation"},
    "c_timing_normal":  {"provenance": "inference", "label": "The normal order, not a sign",
                         "text": "Cornelius receiving the Spirit before baptism is the normal pattern, not a one-off sign authenticating the Gentiles to the Jewish witnesses present"},
    "c_sealed_pre_bap": {"provenance": "inference", "label": "Sealed before baptism",
                         "text": "Salvation is sealed by the Spirit, received before and apart from baptism"},
    "c_not_instrument": {"provenance": "inference", "label": "Not the instrument",
                         "text": "Baptism is not the instrument of salvation"},
    "c_outward_pledge": {"provenance": "inference", "label": "Outward pledge of faith",
                         "text": "Baptism is the outward pledge of a faith already held"},
    "t_berean": {"provenance": "conclusion", "label": "Not the instrument",
                 "text": "Baptism does not save — commanded, but not the instrument of salvation"},
    "t_berean_pledge": {"provenance": "conclusion", "label": "Outward pledge",
                 "text": "Baptism is the outward pledge of a faith already held"},
}

OVERLAYS = [
    {
        "tradition": "Credobaptist (believer's baptism)",
        "thesis": "t_credo_who",
        "rejects": ["c_covenant_kids"],
        "links": [
            {"from": "v_acts2_38",  "to": "c_belief_first", "relation": "supports", "strength": "solid"},
            {"from": "v_acts8_12",  "to": "c_belief_first", "relation": "supports", "strength": "solid"},
            {"from": "v_mark16_16", "to": "c_belief_first", "relation": "supports", "strength": "contested",
             "why": "Pairs belief and baptism for salvation, but does not fix their order."},
            {"from": "c_belief_first", "to": "c_baptize_believers", "relation": "supports", "strength": "solid"},
            {"from": "c_baptize_believers", "to": "t_credo_who", "relation": "supports", "strength": "contested",
             "why": "The EXCLUSION of infants is an argument from silence — every narrated case is a first-generation adult convert, so the absence of an infant baptism doesn't settle whether infants may be baptized."},
            # The Ephesians branch argues EFFICACY (what baptism does), not recipients — it discriminates
            # against baptismal regeneration, NOT against infant baptism (a Reformed paedobaptist holds
            # faith-alone and baptizes infants). So it feeds "baptism doesn't save," not "believers only."
            {"from": "v_eph2_8",    "to": "c_faith_alone",  "relation": "supports", "strength": "solid"},
            {"from": "c_faith_alone", "to": "t_credo_save", "relation": "supports", "strength": "solid"},
            # Credo's POSITIVE, non-silence plank: the new covenant is constituted by faith/regeneration,
            # not lineage (Jer 31, Heb 8), so the sign goes to believers. Paedo contests the reading (the
            # household principle carries over), so it's contested — but as live exegesis, NOT silence.
            # This gives credo a second path to its conclusion that doesn't run through the silence joint.
            {"from": "v_jer31", "to": "c_regenerate_membership", "relation": "supports", "strength": "contested",
             "why": "Credo reads 'they shall all know me' as a regenerate membership; paedo reads it as the covenant's fullness, not a present exclusion of children — a live dispute over Jeremiah 31, not silence."},
            {"from": "v_heb8",  "to": "c_regenerate_membership", "relation": "supports", "strength": "contested",
             "why": "Hebrews 8 applies Jeremiah's new covenant; whether it redraws covenant membership now is the disputed point."},
            {"from": "c_regenerate_membership", "to": "t_credo_who", "relation": "supports", "strength": "contested",
             "why": "If new-covenant membership is by faith, the sign goes to professed believers; paedo answers that the household principle carries into the new covenant."},
            {"from": "v_households", "to": "t_credo_who", "relation": "undercuts", "strength": "contested",
             "why": "If those households included children, the 'believers only' rule already has exceptions."},
        ],
    },
    {
        "tradition": "Paedobaptist (infant baptism)",
        "thesis": "t_paedo",
        "rejects": ["c_regenerate_membership"],
        "links": [
            {"from": "v_gen17",    "to": "c_covenant_kids", "relation": "supports", "strength": "contested",
             "why": "Covenant continuity — a systematic inference the other side disputes."},
            {"from": "v_acts2_39", "to": "c_covenant_kids", "relation": "supports", "strength": "contested",
             "why": "'Your children' may mean posterity generally, not a mandate to baptize infants."},
            {"from": "v_lydia", "to": "c_household_infants", "relation": "supports", "strength": "contested",
             "why": "A baptized household with no members described — the inference to infants is genuine (clean) silence, on par with credo's exclusion step."},
            {"from": "v_stephanas", "to": "c_household_infants", "relation": "supports", "strength": "contested",
             "why": "Again a household named with no members described — clean silence, not silence against the text."},
            {"from": "v_households", "to": "c_household_infants", "relation": "supports", "strength": "weak",
             "why": "Silence, and it runs against this passage's own context: 16:32 preaches the word to all in the house and 16:34 ties the household's rejoicing to believing — presuming hearers who can understand. Weaker than credo's clean silence, not its mirror."},
            {"from": "obj_household_hearers", "to": "c_household_infants", "relation": "undercuts", "strength": "contested",
             "why": "The jailer pericope itself (16:32 hearing the word, 16:34 householdwide rejoicing tied to believing) describes comprehension and volition, which infants can't do — credo's counter on this anchor."},
            {"from": "c_household_infants", "to": "c_covenant_kids", "relation": "supports", "strength": "contested",
             "why": "The baptized households are read as evidence that children belong in the covenant community."},
            {"from": "c_covenant_kids", "to": "c_baptism_for_circ", "relation": "requires", "strength": "contested",
             "why": "The circumcision-replacement step needs covenant continuity to stand."},
            {"from": "v_col2", "to": "c_baptism_for_circ", "relation": "supports", "strength": "contested",
             "why": "Baptism is set beside circumcision, but the recipients aren't specified."},
            {"from": "c_baptism_for_circ", "to": "t_paedo", "relation": "supports", "strength": "contested",
             "why": "Baptism replaces circumcision, so it goes to the same recipients — the recipient-equivalence leap."},
            {"from": "c_belief_first", "to": "t_paedo", "relation": "undercuts", "strength": "contested",
             "why": "Every baptism the NT actually describes follows a profession of faith."},
        ],
    },
    {
        "tradition": "Baptismal regeneration (baptism saves)",
        "thesis": "t_regen_saves",
        "rejects": ["c_faith_alone"],
        "links": [
            {"from": "v_acts2_38", "to": "t_regen_grace", "relation": "supports", "strength": "contested",
             "why": "'For the forgiveness of sins' read as baptism effecting it; credo/paedo read it as a sign."},
            {"from": "v_1pet3_21", "to": "t_regen_grace", "relation": "supports", "strength": "weak",
             "why": "The verse qualifies itself: 'not the removal of dirt from the body, but the pledge of a good conscience' — Peter locates the saving in the pledge, not the washing."},
            {"from": "v_john3_5",  "to": "t_regen_grace", "relation": "supports", "strength": "contested",
             "why": "'Born of water' read as baptism — disputed."},
            {"from": "v_mark16_16", "to": "t_regen_grace", "relation": "supports", "strength": "weak",
             "why": "The verse pins condemnation to unbelief, not non-baptism ('whoever does not believe will be condemned'), and Mark's longer ending is absent from the earliest manuscripts."},
            # The verses (contested readings) support the EFFECTS inference; the thesis "Baptism saves, not
            # merely signifies" follows from it (mirrors credo's "Baptism doesn't save"). Verse→inference
            # links stay CONTESTED on purpose — regeneration's efficacy reading rests on DISPUTED verses,
            # whereas credo's base rests on a verse both sides grant; that gap should show. Don't promote them.
            {"from": "t_regen_grace", "to": "t_regen_saves", "relation": "supports", "strength": "solid",
             "why": "Granting the effects reading, 'baptism saves, not merely signifies' follows directly."},
            # NECESSITY here is the QUALIFIED form (ordinarily necessary, with providential exceptions) —
            # the strongest regenerationist version, NOT the strict Churches-of-Christ "no exceptions" claim.
            # It rides on the contested "baptism saves" premise and REQUIRES grace be an infused substance
            # (def_grace_infused + the charis objection). The thief rules out the strict sub-form, but the
            # qualified form on the board absorbs it.
            {"from": "t_regen_saves", "to": "t_regen_necessary", "relation": "supports", "strength": "contested",
             "why": "If baptism truly effects salvation it is the ordinary means, so the qualified-necessity reading follows fairly directly; the remaining weight sits on the contested 'baptism saves' premise upstream, not on an overreach to 'no exceptions'."},
            {"from": "def_grace_infused", "to": "t_regen_necessary", "relation": "requires", "strength": "contested",
             "why": "Necessity presupposes grace is an imparted substance. The cited verses speak of forgiveness, salvation and new birth — never of charis being conveyed."},
            {"from": "obj_grace_charis", "to": "def_grace_infused", "relation": "undercuts", "strength": "contested",
             "why": "If charis is favor exercised by faith (Eph 2:8), not a substance, nothing is conveyed through the rite and the necessity step loses its premise — the credo/Reformed reading."},
            {"from": "c_faith_alone", "to": "t_regen_grace", "relation": "undercuts", "strength": "contested",
             "why": "Grace through faith, not of works — cuts against baptism as the cause."},
            {"from": "obj_pet_pledge", "to": "t_regen_grace", "relation": "undercuts", "strength": "contested",
             "why": "1 Peter's own clause ('not the removal of dirt... but the pledge of a good conscience') points the saving away from the washing — so the verse undercuts its own efficacy use."},
            {"from": "obj_mark_unbelief", "to": "t_regen_grace", "relation": "undercuts", "strength": "contested",
             "why": "Mark 16:16's negative clause drops baptism (condemnation = unbelief), and the longer ending is textually disputed — so the verse undercuts its own efficacy use."},
            {"from": "v_luke23_43", "to": "t_regen_necessary", "relation": "undercuts", "strength": "contested",
             "why": "The thief was saved with no baptism — a clean counterexample to the strict 'no exceptions' form, which rules that sub-form out. The qualified form on the board (a providential exception) absorbs it: the objection constrains the position, it doesn't defeat it. Credo/Reformed raise it."},
        ],
    },
    {
        "tradition": "Narrow road (Berean)",
        "thesis": "t_berean",
        "rejects": [],
        "links": [
            # Not-the-instrument branch
            {"from": "v_eph1",   "to": "c_spirit_seal", "relation": "supports", "strength": "solid"},
            {"from": "v_rom8_9", "to": "c_spirit_seal", "relation": "supports", "strength": "solid"},
            # Timing is the disputed joint. The SEAL premise (Spirit = seal, from Eph 1 / Rom 8:9) is
            # solid and stays solid. What's contested is whether Cornelius's Spirit-before-water is the
            # NORMAL order or a one-off authenticating sign — so "sealed before baptism" is routed THROUGH
            # that contested generalization and is no longer reachable on solid links alone (the false
            # back-door of a direct solid Cornelius edge into the node is removed).
            {"from": "v_cornelius",   "to": "c_timing_normal", "relation": "supports", "strength": "contested",
             "why": "Generalizing one episode to the normal pattern is the disputed step; the regen reading takes Cornelius as an exceptional sign authenticating the Gentiles."},
            {"from": "v_acts11_17",   "to": "c_timing_normal", "relation": "supports", "strength": "contested",
             "why": "'The same gift as us' (and Acts 15:9) defends reading Cornelius as the pattern, not an exception — itself the disputed point."},
            {"from": "c_spirit_seal", "to": "c_sealed_pre_bap", "relation": "supports", "strength": "contested",
             "why": "The seal premise is solid, but moving from 'the Spirit seals' to 'sealed BEFORE baptism' assumes the timing generalization — so this edge is contested, not solid."},
            {"from": "c_timing_normal", "to": "c_sealed_pre_bap", "relation": "supports", "strength": "contested",
             "why": "Granting the timing is the norm, the sealing precedes baptism; but the timing itself is contested, so the conclusion does not stand on solid links alone."},
            {"from": "c_sealed_pre_bap", "to": "c_not_instrument", "relation": "supports", "strength": "solid"},
            # Outward-pledge branch
            {"from": "v_1pet3_21", "to": "c_outward_pledge", "relation": "supports", "strength": "solid",
             "why": "The verse's own clause locates the role in the pledge of a good conscience, not the washing."},
            {"from": "v_rom6", "to": "c_outward_pledge", "relation": "supports", "strength": "contested",
             "why": "Corroborating only — Romans 6 can also be read as baptism effecting union, so it doesn't carry solid weight alone."},
            # (Trimmed: the baptizō / 1 Cor 12:13 / Gal 3:27 lexical sub-argument was an extra stack of
            #  contested corroborators on this branch. The pledge stands on 1 Peter 3:21 alone; the
            #  "baptizō is medium-neutral" point now lives in the foundational-words strip, where a
            #  lexical fact about the key word belongs — not as a graph node.)
            # Converge — TWO sibling conclusions. An OR-only engine can't put a conjunction ("pledge AND
            # not-instrument") in one node without the whole thing reading STANDS off its easier half, so the
            # claim is split: the PLEDGE half stands on 1 Peter 3:21 (solid); the NOT-INSTRUMENT half rests on
            # the contested Spirit-timing chain. The overlay THESIS is the distinctive, contested claim
            # (not-instrument), so the verdict pill reads honestly DEPENDS — it no longer borrows the pledge
            # half's STANDS. The pledge conclusion still renders, visibly reached on solid links.
            {"from": "c_outward_pledge", "to": "t_berean_pledge", "relation": "supports", "strength": "solid"},
            {"from": "c_not_instrument", "to": "t_berean", "relation": "supports", "strength": "solid"},
            # Objections (raised, handled — off the solid spine; reused verses carry their regen strength)
            {"from": "v_luke23_43", "to": "c_not_instrument", "relation": "supports", "strength": "contested",
             "why": "The thief (saved unbaptized) confirms 'not strictly the instrument in every case' — carried at the same contested rating it has in the regeneration overlay. Confirming only, not part of the spine."},
            {"from": "v_acts2_38", "to": "c_not_instrument", "relation": "undercuts", "strength": "contested",
             "why": "'For the forgiveness of sins' is the causal/telic (eis) debate; answered by Cornelius (Spirit + forgiveness before baptism) without having to win the eis argument."},
            {"from": "v_john3_5", "to": "c_not_instrument", "relation": "undercuts", "strength": "contested",
             "why": "'Born of water' — baptism / physical birth / the word all live; parked unresolved either direction."},
            {"from": "v_mark16_16", "to": "c_not_instrument", "relation": "supports", "strength": "contested",
             "why": "The condemnation clause ties damnation to unbelief, not non-baptism — rested on the unbelief clause (not the longer ending's textual dispute), and weak-for-efficacy in the regen overlay, so contested here too."},
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
    ap = argparse.ArgumentParser(description="Add a hand-authored argument graph to study.db.")
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
