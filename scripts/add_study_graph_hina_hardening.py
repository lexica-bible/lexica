#!/usr/bin/env python3
"""Add the ἵνα / HARDENING-OF-ISAIAH-6 argument GRAPH into study.db (PA-only).

Same shape + tooling as add_study_graph.py — a shared pool of CLAIMS joined by per-reading
LINKS (see argmap.py). This is the graph the live ἵνα structural card (structural.py G2443)
already points OUT to: the card states a contested grammatical question and says it is mapped
"in an argument graph"; this builds what that pointer points to.

    workon bible-env
    python scripts/add_study_graph_hina_hardening.py             # DRY RUN: stress test + resolve verses
    python scripts/add_study_graph_hina_hardening.py --apply     # write it to study.db

The stress-test verdict needs NO database (pure logic); verse text resolves from bible.db the
same way the Study tab does. Re-running REPLACES the same graph (stable id).

WHAT THIS GRAPH MUST EARN (not assume) — the build rule for this one:
  The graph MAPS the contest; it does not resolve it. All three readings come out contested —
  nobody wins, the seam is mapped, not closed. The key correction (from the 2026-06-29 review,
  Fix B): the upstream thesis "ἵνα transmits the question, it does not create it" is ITSELF the
  contested claim, not a settled finding — the purpose camp denies that exact sentence (their
  strong form: "there is no fork to transmit; it is purpose throughout, and the tension is
  manufactured"). So:
    - The two sense-readings each route THROUGH the contested ἵνα-grammar joint ("here ἵνα =
      purpose" / "here ἵνα = result"), so the engine returns DEPENDS for both.
    - The "fork predates ἵνα" thesis ALSO returns DEPENDS. The two underlying FACTS are
      both-camps-grant (Hebrew imperatives recast as a Greek passive clause, c_form_shift; the
      evangelists frame the citation three ways, c_divergence) — but the INFERENCE from those
      facts to "predates ἵνα / does not create it" is exactly what the purpose camp denies, so
      BOTH supporting edges are CONTESTED. (The first build rated them solid; that relocated the
      contest from a labeled node into two edge-strength labels and forced a false STANDS — the
      sophisticated form of seating. "The fact is shared" is NOT "the inference from the fact is
      shared".)
    - The STRONGER claim — that the LXX clause is itself open between aim and outcome
      (c_ambiguity_seeded) — stays ON THE BOARD, also CONTESTED (the purpose camp reads μήποτε as
      purposive, "to prevent").
  Net: all three theses DEPEND on contested steps. The honest finding is "even the upstream
  framing is contested", consistent with how every other reading resolves. This is COMPUTED by
  argmap, not authored — confirm it in the stress output before --apply.

STRENGTH RUBRIC (audited for even-handedness across the three readings):
  solid     = the text states it directly, or BOTH camps grant it (the form shift; the three
              renderings exist; ἵνα's default force is purpose; μήποτε's lexical range)
  contested = a disputed inference or a disputed application of a real range (which sense ἵνα
              bears HERE; whether the LXX clause is itself "open"; whether Matthew's ὅτι proves
              anything about Mark)
  weak      = (not needed here)

A NOTE ON SCOPE (deliberate omission, available if JP wants it): the strongest scholarly form
of "older than ἵνα" pushes the ambiguity back further still, to the Aramaic Targum substratum
(Jeremias: Mark's ἵνα reflecting the Aramaic particle d-). That layer is left OUT — the Targum
is not in our corpus (can't be grounded/clicked), the Targum-dependence of Mark is itself
contested, and the brief scoped the chain as Hebrew -> LXX -> the Synoptics. Add it later as a
contested supporting node if desired.
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
GRAPH_ID = "hina_hardening"
TITLE = "ἵνα and the hardening of Isaiah 6 — purpose, or result?"
INTRO = ("When Jesus quotes Isaiah 6 to explain the parables, Mark writes ἵνα — 'so that' — "
         "and it can be read two ways: the parables are given IN ORDER TO blind outsiders "
         "(purpose), or the parables are given and the OUTCOME is that they do not perceive "
         "(result). Whole doctrines of divine hardening ride on which one ἵνα means here. This "
         "lays out the strongest case for each reading — and then asks an older question: did "
         "Mark's ἵνα create this fork, or only inherit it? Follow where each chain actually "
         "load-bears. The graph maps the reasoning; it does not settle the doctrine.")
PUBLISHED = False   # land as a draft; flip to True AFTER JP's review (graphs are admin-only anyway)

# Claims: the shared pool. Verse claims carry a `ref` (resolves to text, clickable in the
# reader); claims about the Hebrew / about a lexical range carry no ref. provenance: text/lexicon
# are GROUNDED in the source; observation/inference/conclusion are reached through links, not assumed.
CLAIMS = {
    # ── grounded source texts ──
    # NOTE: the Hebrew node has NO ref on purpose — our reader's Isaiah is ABP (LXX-based English),
    # so a click on "Isaiah 6:10" would show the LXX form, not the Hebrew. The caption carries the
    # Hebrew; the LXX node owns the clickable Isaiah 6:10.
    "v_heb_isa610": {"provenance": "text", "label": "Hebrew: 'make the heart fat'",
                     "text": "Hebrew Isaiah 6:10 gives three causative imperatives to the prophet — "
                             "make this people's heart fat, make their ears heavy, shut their eyes — "
                             "'lest (pen) they see, hear, understand, and turn and be healed.'"},
    "v_lxx_isa6":   {"provenance": "text", "ref": "Isaiah 6:10", "label": "LXX: 'the heart has grown fat'",
                     "text": "The Greek Old Testament (LXX — the text ABP follows) recasts it: 'this "
                             "people's heart HAS GROWN FAT... and they shut their OWN eyes — lest "
                             "(mēpote) they should see and turn, and I heal them.' A command becomes "
                             "a description of a people already dull."},
    "v_mark412":    {"provenance": "text", "ref": "Mark 4:12", "label": "Mark: ἵνα ('so that')",
                     "text": "Mark 4:12 fronts the Isaiah quote with ἵνα: '...so that (hina) seeing "
                             "they may see and not perceive... lest (mēpote) they should turn and be "
                             "forgiven.'"},
    "v_matt1313":   {"provenance": "text", "ref": "Matthew 13:13", "label": "Matthew: ὅτι ('because')",
                     "text": "Matthew 13:13 reframes it with hoti: 'I speak to them in parables BECAUSE "
                             "(hoti) seeing they do not see' — then quotes the LXX in full (13:14-15)."},
    "v_john1240":   {"provenance": "text", "ref": "John 12:40", "label": "John: 'He has blinded'",
                     "text": "John 12:40 renders it a third way: 'He has BLINDED their eyes and "
                             "hardened their heart, lest (hina mē) they see... and turn, and I heal "
                             "them' — direct divine action."},

    # ── grounded lexical ranges ──
    "lex_hina_telic":   {"provenance": "lexicon", "label": "ἵνα: default is purpose",
                         "text": "ἵνα's standard, default force is telic — it marks purpose ('in order "
                                 "that'). This is the ordinary reading unless context pulls against it."},
    "lex_hina_disputed":{"provenance": "lexicon", "label": "ἵνα result-sense: disputed",
                         "text": "Whether ἵνα ever marks pure RESULT (the 'ekbatic' use — outcome, not "
                                 "aim) is a long-standing grammatical dispute: some hold Koine ἵνα can "
                                 "be result, others deny it."},
    "lex_mepote":       {"provenance": "lexicon", "label": "mēpote: 'lest' — itself open",
                         "text": "mēpote + subjunctive marks a negative purpose-or-apprehension clause. "
                                 "Its own range spans 'so as to prevent' (aim) and 'for fear that / as "
                                 "may happen' (outcome) — the openness is a property of the word."},

    # ── observations (derived from the texts; both camps grant them) ──
    "c_form_shift": {"provenance": "observation", "label": "Command → description",
                     "text": "Between the Hebrew and the Greek OT, the dulling-clause changes form: "
                             "causative imperatives addressed to the prophet become a passive statement, "
                             "with the people closing their own eyes."},
    "c_divergence": {"provenance": "observation", "label": "Three framings, one citation",
                     "text": "The evangelists frame the same Isaiah 6 citation differently — Mark with "
                             "ἵνα, Matthew with ὅτι (then the full LXX), John with direct divine blinding."},

    # ── interpretive claims ──
    "c_heb_causative":     {"provenance": "inference", "label": "Hebrew = divine intent",
                            "text": "Read straight, the Hebrew imperatives make the dulling something "
                                    "God commands — the blinding is purposed."},
    "c_lxx_stative":       {"provenance": "inference", "label": "LXX = a condition",
                            "text": "The LXX's passive 'has grown fat' and 'they shut their own eyes' "
                                    "describe a condition the people are already in, not a fresh command."},
    "c_matt_causal":       {"provenance": "inference", "label": "Matthew read it causally",
                            "text": "Matthew's ὅτι ('because') shows an early reader taking the clause "
                                    "causally — parables MEET an existing blindness rather than cause it."},
    "c_ambiguity_seeded":  {"provenance": "inference", "label": "The clause is already open",
                            "text": "Under the LXX's passive + mēpote, whether the not-turning is the "
                                    "AIM of the dulling or its OUTCOME is already left open — before any "
                                    "Gospel writes ἵνα. (The purpose camp resists this: they read mēpote "
                                    "as 'to prevent.')"},
    "c_hina_sense_purpose":{"provenance": "inference", "label": "Here ἵνα = purpose",
                            "text": "In Mark 4:12 ἵνα carries its telic force: the parables are given in "
                                    "order that outsiders not perceive."},
    "c_hina_sense_result": {"provenance": "inference", "label": "Here ἵνα = result",
                            "text": "In Mark 4:12 ἵνα marks result: parables are given, with the outcome "
                                    "that outsiders do not perceive."},

    # ── objections ──
    "obj_heb_unambiguous": {"provenance": "text", "label": "But the Hebrew is a command",
                            "text": "The Hebrew imperatives are a plain command to dull — taken on their "
                                    "own, the source shows no purpose/result fork at all."},
    "obj_matt_softened":   {"provenance": "text", "ref": "Matthew 13:13", "label": "But Matthew chose ὅτι",
                            "text": "Matthew, an early reader, used ὅτι ('because') instead of a purpose "
                                    "connective — a sign the purpose reading was not felt to be the only "
                                    "one possible."},
    "obj_hina_created":    {"provenance": "inference", "label": "Maybe ἵνα created it",
                            "text": "The counter-claim: the LXX passive is just idiomatic Greek for the "
                                    "Hebrew and adds no ambiguity; without Mark's ἵνα there is no purpose "
                                    "reading to debate — so the fork is born AT ἵνα, not before."},

    # ── conclusions ──
    "t_telic":    {"provenance": "conclusion", "label": "Purpose: the blinding is intended",
                   "text": "The hardening is divinely purposed — ἵνα means 'in order that'; the parables "
                           "are given to blind."},
    "t_ekbatic":  {"provenance": "conclusion", "label": "Result: the blinding is the outcome",
                   "text": "The hardening is the described outcome — ἵνα marks result; the parables meet "
                           "a blindness already there."},
    "t_upstream": {"provenance": "conclusion", "label": "The fork predates ἵνα",
                   "text": "The purpose-vs-result question is older than the Greek conjunction. It is "
                           "rooted in the Hebrew→LXX recasting and shows up in how the evangelists "
                           "frame the citation — Mark's ἵνα, Matthew's ὅτι, John's wording are three "
                           "handlings of an already-shifted clause. ἵνα transmits the question; it does "
                           "not create it."},
}

OVERLAYS = [
    {
        "tradition": "Purpose (telic) reading",
        "thesis": "t_telic",
        "rejects": ["c_hina_sense_result"],
        "links": [
            {"from": "v_heb_isa610", "to": "c_heb_causative", "relation": "supports", "strength": "solid",
             "why": "The Hebrew uses causative imperatives addressed to the prophet — read straight, that is a command to dull."},
            {"from": "c_heb_causative", "to": "t_telic", "relation": "supports", "strength": "contested",
             "why": "The Hebrew's command-force has to carry across the LXX's passive recasting to reach Mark's clause — a step the LXX itself blurs."},
            {"from": "lex_hina_telic", "to": "c_hina_sense_purpose", "relation": "supports", "strength": "contested",
             "why": "ἵνα's default IS purpose; but the parallel with Matthew's ὅτι and the LXX softening keep the sense from being forced here."},
            {"from": "v_mark412", "to": "c_hina_sense_purpose", "relation": "supports", "strength": "contested",
             "why": "Mark wrote ἵνα; reading it telically is the natural default — contested only by the surrounding context."},
            {"from": "v_john1240", "to": "c_hina_sense_purpose", "relation": "supports", "strength": "contested",
             "why": "John's 'He has blinded their eyes... lest they see' makes the divine-purpose reading explicit — strong corroboration, still a reading of the same disputed clause."},
            {"from": "c_hina_sense_purpose", "to": "t_telic", "relation": "supports", "strength": "solid",
             "why": "Granting the purpose sense, the conclusion is immediate."},
            {"from": "obj_matt_softened", "to": "t_telic", "relation": "undercuts", "strength": "contested",
             "why": "Matthew's ὅτι is suggestive that purpose wasn't felt as the only reading — but it is Matthew's framing, not decisive about Mark's intent. Raised, not decisive."},
        ],
    },
    {
        "tradition": "Result (ekbatic) reading",
        "thesis": "t_ekbatic",
        "rejects": ["c_hina_sense_purpose"],
        "links": [
            {"from": "v_lxx_isa6", "to": "c_lxx_stative", "relation": "supports", "strength": "solid",
             "why": "The LXX's passive 'has grown fat' and 'they shut their own eyes' state a condition — that is on the page."},
            {"from": "c_lxx_stative", "to": "c_hina_sense_result", "relation": "supports", "strength": "contested",
             "why": "If the clause describes a condition, ἵνα is naturally read as the resulting state — but that rests on the result-sense being available at all."},
            {"from": "lex_hina_disputed", "to": "c_hina_sense_result", "relation": "requires", "strength": "contested",
             "why": "The ekbatic reading REQUIRES that ἵνα can mark result — the disputed grammar. If it can't, this reading has no footing."},
            {"from": "v_matt1313", "to": "c_matt_causal", "relation": "supports", "strength": "solid",
             "why": "Matthew wrote ὅτι ('because') — an early causal framing, on the page."},
            {"from": "c_matt_causal", "to": "t_ekbatic", "relation": "supports", "strength": "contested",
             "why": "Matthew's causal framing supports an outcome reading, but it is Matthew's rendering — not proof about Mark's ἵνα."},
            {"from": "c_hina_sense_result", "to": "t_ekbatic", "relation": "supports", "strength": "solid",
             "why": "Granting the result sense, the conclusion follows."},
            {"from": "obj_heb_unambiguous", "to": "t_ekbatic", "relation": "undercuts", "strength": "contested",
             "why": "The Hebrew command cuts against 'merely an outcome' — but it does not decisively kill the GREEK result reading, because the LXX changed the form (the upstream point). Raised, not decisive."},
        ],
    },
    {
        "tradition": "The fork predates ἵνα (Berean)",
        "thesis": "t_upstream",
        "rejects": [],
        "links": [
            # SOLID SPINE — routes around the ἵνα-sense question, on facts both camps grant.
            {"from": "v_heb_isa610", "to": "c_form_shift", "relation": "supports", "strength": "solid",
             "why": "The Hebrew has causative imperatives — on the page."},
            {"from": "v_lxx_isa6", "to": "c_form_shift", "relation": "supports", "strength": "solid",
             "why": "The LXX has a passive statement with the people closing their own eyes — on the page. The change of form is plain."},
            {"from": "c_form_shift", "to": "t_upstream", "relation": "supports", "strength": "contested",
             "why": "The form shifted — both grant that. But reading the recasting as having SEEDED the purpose/result question (rather than a clean rendering that is still purpose) is exactly the step the purpose camp denies. The fact is shared; this inference from it is not."},
            {"from": "v_mark412", "to": "c_divergence", "relation": "supports", "strength": "solid"},
            {"from": "v_matt1313", "to": "c_divergence", "relation": "supports", "strength": "solid"},
            {"from": "v_john1240", "to": "c_divergence", "relation": "supports", "strength": "solid"},
            {"from": "c_divergence", "to": "t_upstream", "relation": "supports", "strength": "contested",
             "why": "The three framings exist — both grant that. But reading the divergence as the SOURCE generating the framings (rather than three authors making independent choices — Matthew softening on his own) is the contested move. The fact is shared; this inference from it is not."},
            # DEEPER (contested) support — on the board per check 2, NOT load-bearing.
            {"from": "lex_mepote", "to": "c_ambiguity_seeded", "relation": "supports", "strength": "contested",
             "why": "mēpote's range bears both aim and outcome; whether THIS clause is therefore open, or fixed to purpose by context, is the step the purpose camp disputes."},
            {"from": "c_form_shift", "to": "c_ambiguity_seeded", "relation": "supports", "strength": "contested",
             "why": "That the form changed is plain; that the change OPENS the aim/outcome question is the interpretive step the purpose camp resists."},
            {"from": "c_ambiguity_seeded", "to": "t_upstream", "relation": "supports", "strength": "contested",
             "why": "The stronger claim — the LXX clause is itself open — deepens the thesis, but the thesis already stands without it on the form-shift and the divergence."},
            {"from": "obj_hina_created", "to": "t_upstream", "relation": "undercuts", "strength": "contested",
             "why": "The purpose camp may answer that ἵνα DID create the reading — but Matthew's independent ὅτι over the same source, and the mēpote already in the LXX, are not ἵνα's doing, so this objection doesn't rest on solid ground the way the textual divergence does. Raised, not decisive."},
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
    print("  Source texts leaned on by more than one reading: %s" % (shared or "(none)"))
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
    ap = argparse.ArgumentParser(description="Add the ἵνα/hardening argument graph to study.db.")
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
