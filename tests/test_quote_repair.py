"""V11.2 QUOTE-REPAIR PASS controls (DESIGN_v11_acceptance.md V11.2 ruling 1, RULED
2026-07-12; built under JP's standing delegation, reviewer receipt in the session
record). All db-free and model-free (the model is a mock — CI never calls the API):

  1. FIVE FIRE controls, one per banked V11-run quote-fidelity kill class:
       K1 Pro 18:16 interior semicolon dropped        (G1390 d2, never-exempt class)
       K2 1Jn 2:8 quote rewritten                     (G227 d2 — see provenance note)
       K3 Isa 14:2 "them" dropped mid-quote, no …     (G162 d2, never-exempt class)
       K4 1Ki 20:25 halves swapped inside the quote   (G236 d2)
       K5 Jer 2:11 question recast as a statement     (G236 d2)
  2. SPANS-ONLY GUARD teeth: a repair output that (a) rewords adjacent prose,
     (b) drops a citation, (c) adds a quotation — each REFUSED, exactly one model
     call, original raw preserved.
  3. NO-OP control: a clean card never fires repair (the mock raises if called).
  4. CAP-OUT control: a guard-clean output whose quote still fails = draw dead
     after exactly ONE round (the ruled cap — V11.2 ruling 1).
  5. NOT-RUN control: an unavailable cited text yields probe-1 NOT-RUNs, never
     fails — repair must NOT fire (NOT-RUN blocks apply; it is never a repair path).

FIXTURE PROVENANCE (the test_coverage_gate/test_repair_pass precedent): verse texts
are REAL verses.text bytes, JP live reads 2026-07-12 (raw sqlite3 output in the
session record; Pro 18:16 bytes already banked in test_v11_probes.py from the V11.1
ticket-2 live reads). Card-side quote spans K1/K5 are REAL surviving-d2-raw bytes
(JP grep, same session); K2/K3/K4 are LABELED RECONSTRUCTIONS to the banked kill
class shape (ruled-acceptable fallback, receipt on record). K2 provenance note: the
live 1Jn 2:8 bytes read "Again, a new commandment I write to you…" — the park
entry's stored-wording parenthetical ("a commandment, a new one") does not match
the live verse bytes; the fixture keeps the CLASS (quote rewritten vs stored) built
against the live bytes, and the discrepancy is flagged in the session record.

Red-first: this file was run BEFORE the quote-repair hook existed and failed loudly
(AttributeError on quote_repair) — the controls provably fire before any green is
trusted (audit-tools-must-fail).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import build_lexica_def as B


# ── Verse texts: REAL verses.text bytes (JP live reads, 2026-07-12) ─────────────────
VT = {
    ("Pro", 18, 16): "A gift of a man widens him; and sits him by monarchs.",
    ("1Jn", 2, 8): "Again, a new commandment I write to you, which is true in him, and in you, because the darkness passes away, and the true light already shines forth.",
    ("Isa", 14, 2): "And nations shall take them, and bring them into their place; and they shall inherit them, and they shall be multiplied upon the land of God for manservants and maidservants; and the ones capturing them shall be captives; and they shall dominate the ones dominating them.",
    ("1Ki", 20, 25): "And you exchange according to the force falling from you — even horse for horse, and chariots for chariots. And we will wage war against them in the straight plains, and we will power over them. And he hearkened to their voice, and did thus.",
    ("Jer", 2, 11): "if nations changed their gods, and these are not gods! But my people changed their glory by which they do not derive benefit.",
}


def sub(*keys):
    return {k: VT[k] for k in keys}


# ── K1 (G1390 d2, REAL card bytes): Pro 18:16's interior semicolon dropped. ─────────
K1_RAW = ('A gift opens the way for its giver: "a gift of a man widens him and sits him '
          'by monarchs" (Pro 18:16), access purchased by the thing given.')
K1_FIX = K1_RAW.replace("widens him and sits", "widens him; and sits")

# ── K2 (G227 d2 class, RECONSTRUCTION — see header): 1Jn 2:8 quote rewritten. ───────
K2_RAW = ('The lemma attaches to the commandment itself: "a commandment, a new one" '
          '(1Jn 2:8) is called true in him and in you.')
K2_FIX = K2_RAW.replace("a commandment, a new one",
                        "Again, a new commandment I write to you")

# ── K3 (G162 d2 class, RECONSTRUCTION): Isa 14:2 "them" dropped mid-quote, no
# ellipsis (the never-exempt interior-alteration class). ─────────────────────────────
K3_RAW = ('The reversal is explicit: "the ones capturing shall be captives" (Isa 14:2), '
          'captor and captive trading places.')
K3_FIX = K3_RAW.replace("the ones capturing shall", "the ones capturing them shall")

# ── K4 (G236 d2 class, RECONSTRUCTION): 1Ki 20:25 halves SWAPPED inside the quote. ──
K4_RAW = ('The exchange is like-for-like: "chariots for chariots, and horse for horse" '
          '(1Ki 20:25), force replaced in kind.')
K4_FIX = K4_RAW.replace("chariots for chariots, and horse for horse",
                        "horse for horse, and chariots for chariots")

# ── K5 (G236 d2, REAL card-span bytes): Jer 2:11's question recast as a statement. ──
K5_RAW = ('Israel\'s apostasy is framed as an exchange no nation makes: "they changed '
          'their gods" (Jer 2:11), though these are not gods.')
K5_FIX = K5_RAW.replace("they changed their gods", "if nations changed their gods")

KILLS = [
    ("K1 Pro 18:16 dropped semicolon", K1_RAW, K1_FIX, ("Pro", 18, 16)),
    ("K2 1Jn 2:8 rewritten quote", K2_RAW, K2_FIX, ("1Jn", 2, 8)),
    ("K3 Isa 14:2 dropped word", K3_RAW, K3_FIX, ("Isa", 14, 2)),
    ("K4 1Ki 20:25 swapped halves", K4_RAW, K4_FIX, ("1Ki", 20, 25)),
    ("K5 Jer 2:11 recast question", K5_RAW, K5_FIX, ("Jer", 2, 11)),
]

# ── Guard-teeth outputs (built on K1): each fixes the quote but breaks the
# spans-only line in one ruled way. ──────────────────────────────────────────────────
BAD_PROSE = K1_FIX.replace("access purchased", "access that is purchased")
BAD_CITE = K1_FIX.replace(" (Pro 18:16),", ",")
BAD_ADDED = K1_FIX + ' The verse adds "sits him by monarchs" again.'
# Guard-clean but the quote is STILL wrong (cap-out shape).
STILL_BAD = K1_RAW.replace("widens him and sits", "enlarges him and seats")


class Mock:
    """A scripted call_model: returns its outputs in order, records every message."""
    def __init__(self, *outputs):
        self.outputs, self.msgs = list(outputs), []
    def __call__(self, msg):
        self.msgs.append(msg)
        if not self.outputs:
            raise AssertionError("call_model called more times than scripted")
        return self.outputs.pop(0)


class ContractMock:
    """A call_model that behaves like a model HONORING the repair prompt's output
    contract only when the contract instruction is actually present in the message —
    `compliant` when `trigger` is in the message, `noncompliant` (a narration-wrapped
    reply, the real 0-for-3 failure shape) otherwise. This lets F1/F2 be proven
    red-first model-free: the OLD prompt lacks the trigger → the mock narrates → the
    guard breaches; the NEW prompt carries it → the mock returns the bare card."""
    def __init__(self, trigger, compliant, noncompliant):
        self.trigger, self.compliant, self.noncompliant = trigger, compliant, noncompliant
        self.msgs = []
    def __call__(self, msg):
        self.msgs.append(msg)
        return self.compliant if self.trigger in msg else self.noncompliant


def main():
    # ── 1. FIVE FIRE controls (must-fail-first): each banked kill class fires the
    # repair, the mock's spans-only correction passes the guard and the re-run gate.
    for name, raw, fixed, ref in KILLS:
        vt = sub(ref)
        fails, _ = B.probe1_verbatim(raw, vt)
        assert fails, f"{name}: the kill fixture does not fire the quote gate"
        mock = Mock(fixed)
        final, rec, probs = B.quote_repair(raw, vt, mock)
        assert probs == [], f"{name}: clean repair refused: {probs!r}"
        assert final == fixed, name
        assert rec is not None and rec["rounds"] == 1, (name, rec)
        assert rec["fails"] == fails, (name, rec)
        assert rec["prompt_ver"].startswith("qrepair:"), (name, rec)
        # the repaired card passes the PRODUCTION gate (never a copy)
        f2, n2 = B.probe1_verbatim(final, vt)
        assert f2 == [] and n2 == [], (name, f2, n2)
        # the one message carried the gate's findings, the stored verse bytes, and
        # the full card
        msg = mock.msgs[0]
        assert "verbatim-quote check" in msg, name
        assert ("- " + fails[0]) in msg, f"{name}: the gate's fail line missing from the feed"
        assert VT[ref] in msg, f"{name}: stored verse bytes missing from the feed"
        assert raw.strip() in msg, name

    # ── 2. SPANS-ONLY GUARD teeth (red-first on the mocks): each breach = draw DEAD,
    # exactly one model call (cap 1 — dead, never re-repaired), original raw kept.
    for bad, what in ((BAD_PROSE, "reworded prose"),
                      (BAD_CITE, "dropped citation"),
                      (BAD_ADDED, "added quotation")):
        mock = Mock(bad, K1_FIX)            # a second round would consume output 2
        final, rec, probs = B.quote_repair(K1_RAW, sub(("Pro", 18, 16)), mock)
        assert probs, f"guard did NOT refuse a {what}"
        assert any("spans-only" in p for p in probs), (what, probs)
        assert len(mock.msgs) == 1, f"{what}: a guard breach was re-repaired"
        assert final == K1_RAW, f"{what}: a guard-refused raw leaked out"
        # ticket 1: the discarded repair output is banked on rec (evidence for the review)
        assert rec["refused_post"] == bad, f"{what}: refused output not banked on rec"
        assert rec["pre"] == K1_RAW, f"{what}: pre-repair card not banked on rec"
    # direct guard reads, for the record
    assert B.quote_repair_guard(K1_RAW, K1_FIX) == []
    assert B.quote_repair_guard(K1_RAW, BAD_PROSE)
    assert B.quote_repair_guard(K1_RAW, BAD_CITE)
    assert B.quote_repair_guard(K1_RAW, BAD_ADDED)

    # ── 3. NO-OP control: a clean card never fires (model never called) — both a
    # matching quote and a quoteless card.
    def never(_msg):
        raise AssertionError("quote repair fired on a clean card")
    clean = 'The verse reads "A gift of a man widens him; and sits him by monarchs" (Pro 18:16).'
    assert B.quote_repair(clean, sub(("Pro", 18, 16)), never) == (clean, None, [])
    quoteless = "A gift opens the way for its giver (Pro 18:16)."
    assert B.quote_repair(quoteless, sub(("Pro", 18, 16)), never) == (quoteless, None, [])

    # ── 4. CAP-OUT: guard-clean output, quote still wrong → dead after exactly ONE
    # round (V11.2 ruling 1's cap), original raw preserved.
    mock = Mock(STILL_BAD, K1_FIX)
    final, rec, probs = B.quote_repair(K1_RAW, sub(("Pro", 18, 16)), mock)
    assert probs and any("cap" in p.lower() for p in probs), probs
    assert len(mock.msgs) == 1, f"cap is 1 round, ran {len(mock.msgs)}"
    assert final == K1_RAW
    assert rec["refused_post"] == STILL_BAD and rec["pre"] == K1_RAW

    # ── 5. NOT-RUN control: an unavailable cited text = probe-1 NOT-RUNs, no fails;
    # repair must NOT fire (NOT-RUN blocks apply downstream, never becomes a repair
    # path — reviewer-endorsed assertion, kept loud).
    vt_missing = {("Pro", 18, 16): None}
    fails, notruns = B.probe1_verbatim(K1_RAW, vt_missing)
    assert notruns and not fails, (fails, notruns)
    assert B.quote_repair(K1_RAW, vt_missing, never) == (K1_RAW, None, [])

    # ── 6. BANK the refused bytes to a temp history dir (ticket 1: evidence, not a
    # draw — never re-read as a card, never shipped; NO-APPLY-EVER covers the dir).
    import json as _json, tempfile
    old_dir = B.DRAWS_DIR
    try:
        B.DRAWS_DIR = tempfile.mkdtemp()
        mock = Mock(BAD_PROSE, K1_FIX)
        _, rec, probs = B.quote_repair(K1_RAW, sub(("Pro", 18, 16)), mock)
        assert probs
        d1 = B.bank_refused_repair("G1390", "quote", rec)
        assert d1 and os.path.exists(d1)
        got = _json.load(open(d1, encoding="utf-8"))
        assert got["refused_post"] == BAD_PROSE and got["pre"] == K1_RAW
        assert got["fails"] == rec["fails"]
        d2 = B.bank_refused_repair("G1390", "quote", rec)   # never overwrites
        assert d2 != d1 and os.path.exists(d2)
        # a record with no refused_post banks nothing (clean/success path)
        assert B.bank_refused_repair("G1390", "quote", {"fails": []}) is None
    finally:
        B.DRAWS_DIR = old_dir

    # ── 7. F1 CARD-ONLY CONTRACT (output-contract fix, ENGINE_LESSONS #57): a model
    # that narrates its work OUTSIDE the card (the real 0-for-3 shape — a preamble that
    # quotes the spans it is fixing) breaches the spans-only guard even though the fix
    # underneath is correct. With the contract in force the model returns the bare card
    # and the correct fix survives. Proven red-first: against the OLD prompt (no "and
    # nothing else") the mock narrates → guard breach; the NEW prompt recovers it.
    assert "and nothing else" in B.QUOTE_REPAIR_PROMPT, "F1 output contract missing from prompt"
    narrated = ('I need to fix the quote "they changed their gods".\n\nHere is the '
                'corrected definition:\n\n' + K5_FIX)
    cm = ContractMock("and nothing else", K5_FIX, narrated)
    final, rec, probs = B.quote_repair(K5_RAW, sub(("Jer", 2, 11)), cm)
    assert probs == [], f"F1: contract-honoring repair still refused: {probs!r}"
    assert final == K5_FIX, "F1: the correct fix did not survive the contract"
    assert len(cm.msgs) == 1
    # the narration path really would have breached (documents the failure the contract closes)
    assert B.quote_repair_guard(K5_RAW, narrated), "F1: narration control did not breach the guard"

    # ── 8. F2 NO-OP CHANNEL: when nothing can be corrected inside the quotation marks,
    # the model returns the card unchanged instead of narrating a decline in-band. The
    # unchanged reply passes the guard and dies cleanly on the cap-out (a real defect the
    # repair can't reach), NOT on a guard breach. Proven red-first: the OLD prompt (no
    # no-op channel) makes the mock narrate the decline → guard breach ("spans-only");
    # the NEW prompt makes it return byte-identical → clean cap-out ("cap").
    NOOP_PHRASE = "return the card exactly as given, unchanged"
    assert NOOP_PHRASE in B.QUOTE_REPAIR_PROMPT, "F2 no-op channel missing from prompt"
    narrated_decline = ('I cannot fix "a gift of a man widens him and sits him by monarchs" '
                        'without changing the prose.\n\n' + K1_RAW)
    cm2 = ContractMock(NOOP_PHRASE, K1_RAW, narrated_decline)
    final2, rec2, probs2 = B.quote_repair(K1_RAW, sub(("Pro", 18, 16)), cm2)
    assert final2 == K1_RAW, "F2: no-op reply should leave the card untouched"
    assert probs2 and any("cap" in p.lower() for p in probs2), (probs2,)
    assert not any("spans-only" in p for p in probs2), f"F2: no-op path breached the guard: {probs2!r}"
    assert len(cm2.msgs) == 1

    # ── 9. RULING 1 (#61) DETERMINISTIC PRE-ROUTING: the quote gate emits two fail
    # kinds and only the fixable WORDING kind reaches the model; the unfixable
    # ANCHORING kind (right words, wrong ref) is held back — the model never sees a
    # fail whose only fix is out-of-quote. Real G236 mixed-card bytes (banked key
    # 59667b81, F1-F3 RE-RUN): "changes this word" (Ezr 6:11-on-6:12, anchoring) +
    # "changing over" (matches no verse, wording). Verse bytes = JP live reads
    # 2026-07-13. Red-first: before the split the old quote_repair fed BOTH lines. ──
    G236MIX_VT = {
        ("Ezr", 6, 11): "And from me was rendered a decree, that every man who ever changes this word the timber of his house shall be demolished, and a stake being straight up he shall be pitched upon it, and his house will be for ravaging.",
        ("Ezr", 6, 12): "And the God of whom encamps with his name there, he shall eradicate every king and people who should stretch out his hand to change and remove from view the house of God, that one in Jerusalem. I Darius rendered the decree. Carefully let it become!",
        ("Dan", 4, 32): "And from men they shall banish you, and with wild beasts your dwelling shall be, and grass as an ox they shall feed you, and seven seasons shall change over you, until of which time you shall know that the highest dominates the kingdom of men, and to whom ever it seems good to give it.",
    }
    G236MIX = ('Ezra threatens anyone who "changes this word" (Ezr 6:12; Ezr 6:11). '
               'The repeated seasons "changing over" the king mark successive intervals '
               '(Dan 4:32).')
    fails, _ = B.probe1_verbatim(G236MIX, G236MIX_VT)
    assert len(fails) == 2, fails                            # the mixed card fires both kinds
    assert any("anchored primary" in f for f in fails) and any("matches NO" in f for f in fails), fails

    # the mock fixes ONLY the wording span (changing over -> Dan 4:32's own words);
    # the anchoring span it must NEVER be asked to touch.
    G236MIX_FIX = G236MIX.replace('"changing over"', '"seven seasons shall change over you"')

    class RouteMock:
        """Records every findings block it was fed; returns the wording-fixed card."""
        def __init__(self, out):
            self.out, self.msgs = out, []
        def __call__(self, msg):
            self.msgs.append(msg)
            return self.out

    rm = RouteMock(G236MIX_FIX)
    final, rec, probs = B.quote_repair(G236MIX, G236MIX_VT, rm)
    assert len(rm.msgs) == 1, rm.msgs
    assert "changing over" in rm.msgs[0], "the wording fail was not fed to the model"
    assert "anchored primary" not in rm.msgs[0], "the anchoring fail LEAKED to the model"
    # outcome: the held-back anchoring fail resurfaces on the re-run -> clean cap-out
    # park, NOT a guard breach; the cached card is untouched (same ship outcome as the
    # old breach-park, breach surface removed).
    assert probs and any("cap" in p.lower() for p in probs), probs
    assert not any("spans-only" in p for p in probs), ("routed to a breach, not a park", probs)
    assert final == G236MIX

    # ── 10. ANCHORING-ONLY card: nothing fixable in-quote -> the model is NEVER
    # called (deterministic no-op), the card parks with no refused_post to bank
    # (nothing existed). Real G236 anchoring span alone. Red-first: the old code fed
    # the anchoring fail to the model, so `never2` would have raised. ──
    G236ANCHOR = 'Ezra threatens anyone who "changes this word" (Ezr 6:12; Ezr 6:11).'
    G236ANCHOR_VT = {k: G236MIX_VT[k] for k in (("Ezr", 6, 11), ("Ezr", 6, 12))}

    def never2(_msg):
        raise AssertionError("model called on an anchoring-only card")

    final, rec, probs = B.quote_repair(G236ANCHOR, G236ANCHOR_VT, never2)
    assert final == G236ANCHOR and probs, probs
    assert any("anchoring" in p.lower() for p in probs), probs
    assert rec and rec.get("anchoring_only") and "refused_post" not in rec, rec
    assert B.bank_refused_repair("G236", "quote", rec) is None      # nothing to bank

    # ── 11. CHECKPOINT 3 (prompt-sharpen, 2026-07-14): QUOTE_REPAIR_PROMPT now NAMES the
    # three forbidden-but-tempting moves — edit unquoted prose for a look-alike word / add,
    # move or split a ref / only-fix-is-outside -> leave unchanged. Each maps to a real
    # observed breach shape (#58 look-alike prose edit; the ref-move in G236 bank 9bf3f7ef;
    # the "only fix is outside" rationalization verbatim in G227 bank d65ed578). It is
    # belt-and-suspenders: CP1's router already keeps the anchoring kind away from the
    # model, and the spans-only guard independently catches a breach. No gate logic moves.
    # Red-first, model-free: the instruction phrase must be in the prompt AND reach the fed
    # message; a ContractMock keyed on it returns the clean fix WITH the instruction and the
    # #58 unquoted-prose breach shape WITHOUT it. ──
    assert "look-alike" in B.QUOTE_REPAIR_PROMPT, "CP3 forbidden-moves instruction missing from prompt"
    cm3 = ContractMock("look-alike", K1_FIX, BAD_PROSE)
    final, rec, probs = B.quote_repair(K1_RAW, sub(("Pro", 18, 16)), cm3)
    assert probs == [], f"CP3: contract-honoring repair refused: {probs!r}"
    assert final == K1_FIX and len(cm3.msgs) == 1
    assert "look-alike" in cm3.msgs[0], "CP3: the instruction did not reach the fed message"
    # the breach control genuinely breaches (documents what the instruction backs up)
    assert B.quote_repair_guard(K1_RAW, BAD_PROSE), "CP3: breach control did not breach the guard"
    # the qrepair stamp MOVED with the prompt (placement check, reviewer 2026-07-14): the
    # sharpened paragraph sits inside the hashed template, so the version differs from BOTH
    # banked prompt versions the four parked cards were built under.
    assert B.quote_repair_prompt_ver() not in ("qrepair:1e8c9c383df6", "qrepair:b90d5287ca16"), \
        B.quote_repair_prompt_ver()

    # ══════════════════════════════════════════════════════════════════════════════════════
    # OWN-PARAPHRASE NEAR-MATCH GATE (meta:v4 / ENGINE_LESSONS #63/#64, RULED across the
    # 2026-07-14 checkpoint chain: BUILD-halt on the char-only rule -> DESIGN re-open -> combined
    # signal + threshold pin). A no-match span gets a TARGET-EXISTS test: COMBINED score =
    # max(char-window best-similarity, token-SET containment best cited verse), both sides through
    # production probe_norm. >= 0.664 -> wording (fed). < 0.664 -> `unsourced`: EMPTY cited set or
    # attribution-anchored -> FAIL + park (never fed); unanchored WITH a cited set -> meta:v4
    # own-paraphrase EXEMPT (LOUD note). Threshold 0.664 = midpoint of the enumerated residual pair
    # (quenched/crushed 0.621 EXEMPT / other-item 0.706 must-refuse); two must-refuse mechanisms
    # ride it (empty-set rule; t <= 0.706). Verse bytes = REAL verses.text (JP live reads on PA
    # 2026-07-14); card spans + cue-free context = REAL banked-card bytes (draws/history/
    # G227_..._8258771a_2.json, G236_..._59667b81_2.json). The three reviewer-named must-land
    # outcomes are fixtures 18 (reorder->wording), 19 (other-item real-card fed->cap->park), 20
    # (empty-VT->unsourced fail). Red-first: against the char-only pre-pin code, the combined-signal
    # pins (fixture 12) and the reorder/other-item routing all fail loudly.
    # ──────────────────────────────────────────────────────────────────────────────────────
    NM_ISA423 = "A reed being crushed he will not break, and smoking flax he will not extinguish; but to validity he will bring forth judgment."
    NM_JOB427 = "And it came to pass after the LORD speaking all these words to Job, the LORD said to Eliphaz the Temanite, You sinned and your two friends, for you spoke not anything before me true, as my attendant Job."
    NM_JOB428 = "And now, take seven calves, and seven rams, and go to my attendant Job! and he shall offer a yield offering for you, for in no way shall I receive of his face, for but on account of him I would have destroyed you. For you did not speak true concerning my attendant Job."
    NM_DAN416 = "His heart shall be changed from the ones of men, and the heart of a wild beast shall be given to him; and seven times shall change over him."
    NM_GEN317 = "But your father cheated me, and bartered my wage for the ten lambs. And the God of my father did not give to him the power to do evil against me."

    # ── 12. SCORE PINS (reviewer condition 2, both legs + combined): the PRODUCTION scorer
    # reproduces the ruled residual bytes exactly. char leg — "changing over" 0.833 @ Dan 4:16;
    # "quenched/crushed" 0.621 @ Isa 42:3. token-set leg — "changing over" 0.500 (only "over"
    # matches), "quenched/crushed" 0.000 (slash keeps it one token). Combined = the gate's value;
    # threshold 0.664 sits strictly between. A normalizer/window/token change that shifts any of
    # these trips HERE. ──
    _pn = B.probe_norm
    _dan = {("Dan", 4, 16): _pn(NM_DAN416)}
    _isa = {("Isa", 42, 3): _pn(NM_ISA423)}
    assert round(B._nearmatch_best(_pn("changing over"), _dan), 3) == 0.833
    assert round(B._nearmatch_best(_pn("quenched/crushed"), _isa), 3) == 0.621
    assert round(B._tokenset_containment(_pn("changing over"), _dan), 3) == 0.500
    assert round(B._tokenset_containment(_pn("quenched/crushed"), _isa), 3) == 0.000
    s236 = B._target_exists_score(_pn("changing over"), _dan)
    s227 = B._target_exists_score(_pn("quenched/crushed"), _isa)
    assert round(s236, 3) == 0.833 and round(s227, 3) == 0.621, (s236, s227)
    assert s227 < B.NEARMATCH_THRESHOLD < s236, (s227, B.NEARMATCH_THRESHOLD, s236)
    assert B.NEARMATCH_THRESHOLD == 0.664, B.NEARMATCH_THRESHOLD

    # ── 13. FIXTURE 1 — real G227 8258771a_2: "quenched/crushed" is the card's own paraphrase
    # of Isa 42:3 with NO attribution -> meta:v4 EXEMPT (note); the Job anchoring span holds ->
    # ZERO feedable spans -> the model is NEVER called and the card parks. ──
    G227CARD = ('Sub-use: a reported thing turns out to match what happened. '
                'Job 42:7 and Job 42:8: Eliphaz and friends "spoke not anything before me true," '
                'while Job did. Nothing in the verse establishes a legal setting; the move is '
                'from "quenched/crushed" to genuine outcome.')
    G227VT = {("Job", 42, 7): NM_JOB427, ("Job", 42, 8): NM_JOB428, ("Isa", 42, 3): NM_ISA423}
    notes, kinds = [], []
    fails, nr = B.probe1_verbatim(G227CARD, G227VT, notes=notes, fail_kinds=kinds)
    assert kinds == ["anchoring"], (fails, kinds)             # only the Job anchoring fail
    assert not any("quenched/crushed" in f for f in fails), fails
    assert any("quenched/crushed" in n and "own-paraphrase" in n and "meta:v6" in n for n in notes), notes

    def never227(_msg):
        raise AssertionError("model called on a card with no feedable (wording) span")
    final, rec, probs = B.quote_repair(G227CARD, G227VT, never227)
    assert final == G227CARD and probs, probs
    assert any("anchoring" in p.lower() for p in probs), probs
    assert rec and rec.get("anchoring_only") and "unsourced_held" not in rec, rec
    assert B.bank_refused_repair("G227", "quote", rec) is None    # nothing to bank

    # ── 14. FIXTURE 2 — real G236 59667b81_2: "changing over" keeps a near-match target (Dan
    # 4:16 "change over", 0.833 >= threshold) -> stays `wording`, fed, fixed, clean. The fed
    # path is unchanged from today. ──
    G236CLEAN = 'In Daniel the seasons "changing over" the king mark successive intervals (Dan 4:16).'
    G236CLEAN_VT = {("Dan", 4, 16): NM_DAN416}
    kinds = []
    fails, nr = B.probe1_verbatim(G236CLEAN, G236CLEAN_VT, notes=[], fail_kinds=kinds)
    assert kinds == ["wording"], (fails, kinds)
    G236CLEAN_FIX = G236CLEAN.replace('"changing over"', '"seven times shall change over him"')
    mock = Mock(G236CLEAN_FIX)
    final, rec, probs = B.quote_repair(G236CLEAN, G236CLEAN_VT, mock)
    assert probs == [], probs
    assert final == G236CLEAN_FIX and len(mock.msgs) == 1
    assert "matches NO cited verse" in mock.msgs[0], "the wording finding was not fed"
    f2, n2 = B.probe1_verbatim(final, G236CLEAN_VT)
    assert f2 == [] and n2 == [], (f2, n2)

    # ── 15. FIXTURE 3 — grafted mixed card (G236 wording span + G227 held spans): the model is
    # fed ONLY the wording finding; the anchoring finding AND the own-paraphrase note are both
    # held back; on the re-check the anchoring span caps out -> park, NOT a guard breach. ──
    GRAFT = ('The seasons "changing over" the king mark intervals (Dan 4:16). '
             'Job 42:7 and Job 42:8: friends "spoke not anything before me true," while Job did. '
             'Nothing sets a legal frame; the move is from "quenched/crushed" to genuine outcome.')
    GRAFTVT = {("Dan", 4, 16): NM_DAN416, ("Job", 42, 7): NM_JOB427,
               ("Job", 42, 8): NM_JOB428, ("Isa", 42, 3): NM_ISA423}
    notes, kinds = [], []
    fails, nr = B.probe1_verbatim(GRAFT, GRAFTVT, notes=notes, fail_kinds=kinds)
    assert sorted(kinds) == ["anchoring", "wording"], (fails, kinds)   # quenched/crushed = NOTE
    assert any("quenched/crushed" in n and "meta:v6" in n for n in notes), notes
    GRAFT_FIX = GRAFT.replace('"changing over"', '"seven times shall change over him"')
    rm = RouteMock(GRAFT_FIX)
    final, rec, probs = B.quote_repair(GRAFT, GRAFTVT, rm)
    assert len(rm.msgs) == 1, rm.msgs
    assert "matches NO cited verse" in rm.msgs[0], "the wording finding was not fed"
    assert "anchored primary" not in rm.msgs[0], "the anchoring finding LEAKED to the model"
    assert probs and any("cap" in p.lower() for p in probs), probs
    assert not any("spans-only" in p for p in probs), ("routed to a breach, not a park", probs)
    assert final == GRAFT

    # ── 16. FIXTURE 4 (TEETH) — the SAME paraphrase span WITH a trailing (Isa 42:3) ref is
    # attribution-anchored: it FAILS as `unsourced` (a claimed source for words that exist
    # verbatim nowhere) and PARKS, never fed. Non-laundering proof — attribution cannot turn a
    # no-target span into a feedable one, nor launder it into an exemption. ──
    TEETH = 'The servant is gentle: "quenched/crushed" (Isa 42:3) is the picture.'
    TEETHVT = {("Isa", 42, 3): NM_ISA423}
    notes, kinds = [], []
    fails, nr = B.probe1_verbatim(TEETH, TEETHVT, notes=notes, fail_kinds=kinds)
    assert kinds == ["unsourced"], (fails, kinds)
    assert any("unsourced" in f and "quenched/crushed" in f for f in fails), fails
    assert not any("EXEMPTED" in n for n in notes), notes         # attribution blocks the exemption

    def neverT(_msg):
        raise AssertionError("model called on an attribution-anchored unsourced span")
    final, rec, probs = B.quote_repair(TEETH, TEETHVT, neverT)
    assert final == TEETH and probs, probs
    assert any("unsourced" in p.lower() for p in probs), probs
    assert rec and rec.get("unsourced_held") and "anchoring_only" not in rec, rec

    # ── 17. REGRESSION — a real misquote WITH a near-match target stays feedable `wording`.
    # K5 "they changed their gods" (a recast of Jer 2:11 "if nations changed their gods") keeps
    # a target (0.857 >= threshold) -> wording, fed. The near-match gate does not swallow the
    # existing K1-K5 fire controls. ──
    kinds = []
    fails, nr = B.probe1_verbatim(K5_RAW, sub(("Jer", 2, 11)), notes=[], fail_kinds=kinds)
    assert kinds == ["wording"], (fails, kinds)

    # ── 18. NAMED MUST-LAND #1 — the defect-6 REORDER (real G227 bytes) that the char-only rule
    # waved through. "bring forth judgment to validity" scrambles Isa 42:3's own words: char 0.690
    # (below), token-set 1.000 (all words present, order-blind) -> COMBINED 1.000 >= 0.664 ->
    # wording, FED to the repair model. The combined signal is what recovers it; char alone
    # exempted it as own-paraphrase and shipped the defect. ──
    REORDER = ('- validity (Isa 42:3): the translation maps it onto the process, '
               '"bring forth judgment to validity", a reordering of the verse.')
    assert round(B._tokenset_containment(_pn("bring forth judgment to validity"), _isa), 3) == 1.000
    kinds = []
    fails, nr = B.probe1_verbatim(REORDER, {("Isa", 42, 3): NM_ISA423}, notes=[], fail_kinds=kinds)
    assert kinds == ["wording"], (fails, kinds)

    # ── 19. NAMED MUST-LAND #2 — "other item" in its REAL cited context (unanchored, no cue): its
    # combined score is 0.706 (char 0.706 @ Gen 31:7, the score-driving verse from the full G236
    # cited set; token-set 0.000) -> >= 0.664 -> wording -> FED. The model cannot fix a concept to
    # a verse, so it returns the card unchanged -> cap-out -> PARKS. Never exempted: this is how the
    # ruled must-refuse verdict holds under meta:v4 (t <= 0.706, mechanism 2). ──
    OTHERITEM = ('the two are distinguished by whether an "other item" is explicitly placed '
                 'in the position vacated.')
    OI_VT = {("Gen", 31, 7): NM_GEN317}
    assert round(B._target_exists_score(_pn("other item"), {("Gen", 31, 7): _pn(NM_GEN317)}), 3) == 0.706
    kinds = []
    fails, nr = B.probe1_verbatim(OTHERITEM, OI_VT, notes=[], fail_kinds=kinds)
    assert kinds == ["wording"], (fails, kinds)
    mock = Mock(OTHERITEM)                      # model can't fix a concept -> returns card unchanged
    final, rec, probs = B.quote_repair(OTHERITEM, OI_VT, mock)
    assert len(mock.msgs) == 1, "other-item must be FED once"
    assert final == OTHERITEM and probs and any("cap" in p.lower() for p in probs), probs
    assert not any("spans-only" in p for p in probs), probs

    # ── 20. NAMED MUST-LAND #3 — "other item" with an EMPTY cited set: nothing to be a paraphrase
    # OF, so the empty-set rule (mechanism 1) blocks the exemption -> it FAILS (unsourced), never
    # exempts. Mirrors probe test 1v. ──
    kinds, notes = [], []
    fails, nr = B.probe1_verbatim(OTHERITEM, {}, notes=notes, fail_kinds=kinds)
    assert kinds == ["unsourced"] and "other item" in fails[0], (fails, kinds)
    assert notes == [], notes                   # no exemption note — the empty-set rule blocks it

    # ── 21. TOKEN-LEG GUARD (reviewer-approved 2026-07-14) — a SYNTHETIC adversarial scramble of
    # the REAL Isa 42:3 words: order destroyed, every word kept. It exists ONLY to lock the
    # order-insensitive token-set leg against silent deletion: char-window 0.640 (BELOW 0.664, so a
    # char-only scorer would EXEMPT this and SHIP the reorder), token-set 1.000, COMBINED 1.000 ->
    # wording, FED. Proven red against a char-only scorer this session. NOT a calibration point and
    # NOT an R2-a instrument: it specifies required behavior, not measured system state, so it is
    # EXCLUDED from every threshold / fragility-band computation (those use real bytes only). ──
    SCRAMBLE = ('A heavier scramble keeps every word but destroys the order: '
                '"judgment to validity forth bring he will".')
    _isa_only = {("Isa", 42, 3): _pn(NM_ISA423)}
    _scr = _pn("judgment to validity forth bring he will")
    assert round(B._nearmatch_best(_scr, _isa_only), 3) == 0.640            # char alone: below t
    assert round(B._tokenset_containment(_scr, _isa_only), 3) == 1.000      # every word present
    assert round(B._target_exists_score(_scr, _isa_only), 3) == 1.000       # combined recovers it
    kinds = []
    fails, nr = B.probe1_verbatim(SCRAMBLE, {("Isa", 42, 3): NM_ISA423}, notes=[], fail_kinds=kinds)
    assert kinds == ["wording"], (fails, kinds)

    # ── 22-26. meta:v6 CONTENT-TOKEN DISCRIMINATOR (scope-b (b) ruling, 2026-07-14): an in-band
    # cue exemption WARNS only when the span reproduces a verse-word RUN (>= 2 distinct content
    # tokens present in a cited verse); a single lemma-gloss inflection (run <= 1) stays a NOTE;
    # out-of-band stays a note (documented full-reorder boundary). Spans + scores are SYNTHETIC,
    # non-calibration (fixture-21 status); the 13 live sweep spans are evidence, never fixtures. ──
    # 22. MUST-WARN (i) -- lemma inflection ("arising") PLUS a verse-word RUN ("vain women").
    #     in-band 0.727, run 2 -> WARN. Lemma inclusion does not buy a pass-through.
    W1_CARD = 'Here the lemma "vain women arising" is my rendering of the phrase.'
    W1_VT = {("Neh", 1, 1): "the vain women were led about here"}
    assert 0.62 <= round(B._target_exists_score(_pn("vain women arising"),
                         {k: _pn(v) for k, v in W1_VT.items()}), 3) <= 0.75
    assert B._verse_run_content(_pn("vain women arising"),
                                {k: _pn(v) for k, v in W1_VT.items()}) >= 2
    notes, warns = [], []
    B.probe1_verbatim(W1_CARD, W1_VT, notes=notes, warns=warns)
    assert warns and "RUN" in warns[0] and "vain women arising" in warns[0], (warns, notes)
    assert notes == [], notes

    # 23. MUST-WARN (ii) -- PARTIAL reorder (tokens present, scrambled): women+vain present,
    #     skyward absent. in-band 0.667, run 2 -> WARN. Presence-not-adjacency (a reorder warns).
    W2_CARD = 'By the word "women vain skyward" I gloss the sense loosely.'
    W2_VT = {("2Ti", 3, 6): "capturing the vain women heaped with sins being led"}
    assert B._verse_run_content(_pn("women vain skyward"),
                                {k: _pn(v) for k, v in W2_VT.items()}) == 2
    notes, warns = [], []
    B.probe1_verbatim(W2_CARD, W2_VT, notes=notes, warns=warns)
    assert warns and "women vain skyward" in warns[0], (warns, notes)

    # 24. MUST-NOTE -- single lemma-gloss inflection: "arising" char-close to "arise" in the verse
    #     but NOT a run (1 content token). in-band 0.667, run 1 -> NOTE. This is the v5 blast
    #     radius (12 live cards), now correctly cleared to note.
    N_CARD = 'The lemma "arising" renders the verb here in its plain sense.'
    N_VT = {("Joh", 5, 8): "when they shall arise from the dead at the last day here"}
    assert 0.62 <= round(B._target_exists_score(_pn("arising"),
                         {k: _pn(v) for k, v in N_VT.items()}), 3) <= 0.75
    notes, warns = [], []
    B.probe1_verbatim(N_CARD, N_VT, notes=notes, warns=warns)
    assert warns == [], warns
    assert notes and "arising" in notes[0] and "run 1 < 2" in notes[0], notes

    # 25. CLOSURE FIXTURE -- a pure function-word span has 0 content tokens, so it can NEVER reach
    #     the >= 2 run bar (locks the FROZEN function set's closure). No warn.
    assert B._content_tokens("and the of that these") == set()
    C_CARD = 'The word "and the of that" is bare scaffolding, my own phrasing.'
    C_VT = {("Act", 1, 1): "and the report was carried across the whole region of that land"}
    notes, warns = [], []
    B.probe1_verbatim(C_CARD, C_VT, notes=notes, warns=warns)
    assert warns == [], warns

    # 26. BOUNDARY PIN (Option A, documented) -- a FULL-token reorder (every content word present,
    #     scrambled) scores ~1.0 on the token leg -> OUT of band -> never reaches the run check ->
    #     stays a NOTE. If a future change flips this boundary, this fixture reddens (not silent).
    B_CARD = 'Here the word "sins women vain heaped" is my scrambled shorthand.'
    B_VT = {("2Ti", 3, 6): "capturing the vain women heaped with sins being led"}
    assert round(B._target_exists_score(_pn("sins women vain heaped"),
                 {k: _pn(v) for k, v in B_VT.items()}), 3) > 0.75
    notes, warns = [], []
    B.probe1_verbatim(B_CARD, B_VT, notes=notes, warns=warns)
    assert warns == [], warns                    # out of band -> never reaches the run check
    assert notes and "out of band" in notes[0], notes

    print("test_quote_repair: ok")


if __name__ == "__main__":
    main()
