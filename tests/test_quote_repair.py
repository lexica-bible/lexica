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

    print("test_quote_repair: ok")


if __name__ == "__main__":
    main()
