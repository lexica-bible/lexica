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

    print("test_quote_repair: ok")


if __name__ == "__main__":
    main()
