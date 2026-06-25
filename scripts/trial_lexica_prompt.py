#!/usr/bin/env python3
"""
trial_lexica_prompt.py — DISTRIBUTION TEST for the VERSE_PROMPT sense-count fix (Step 1).

The live engine over-splits: it gives a separate numbered sense to what is really a
contextual flavor of an existing sense. A fresh psyche re-ran 4 -> 6 senses; charis came
back at 7. The cause is that VERSE_PROMPT never says where one sense ENDS vs where a
sub-use begins, so the model promotes every context difference to its own sense.

This rig compares the FROZEN prompt (OLD) against a candidate (NEW) that adds a sub-use
test. Because the model output is a draw, ONE run proves nothing — so it runs each prompt
N times per word on the SAME evidence (select_spread is deterministic, so old and new see
identical verses; the only variable is the prompt) and prints the DISTRIBUTION of sense
counts. psyche's vetted 4-sense version is the measuring stick.

It reuses the live engine's own helpers verbatim (import build_lexica_def) so the sense
count is taken exactly the way the card takes it (split_definition -> sense_headlines).
It also runs the citation gate each run as a free guard: the sub-use rule must not start
the model hallucinating verses (real-miss should stay ~0 on these well-attested words).

THROWAWAY. PA-ONLY (bible.db + the model key live there). READ-ONLY on bible.db — never
writes lexica_def. Nothing here is the live engine; the live prompt only changes once this
proves out, and then by hand into build_lexica_def.py (which re-freezes the stamp).

  workon bible-env
  export ANTHROPIC_API_KEY=$(grep -oE "sk-ant-[A-Za-z0-9_-]+" /var/www/www_lexica_bible_wsgi.py)
  python scripts/trial_lexica_prompt.py --show-prompts            # OLD vs NEW diff, FREE (no db/model)
  python scripts/trial_lexica_prompt.py --word G5590 --runs 6     # drill psyche only
  python scripts/trial_lexica_prompt.py                           # all 6 words x5 each = ~60 calls (~$2)
  python scripts/trial_lexica_prompt.py --show-defs               # also print a full NEW definition per word
"""

import argparse, difflib, os, sqlite3, sys
from collections import Counter

# reuse the FROZEN, proven helpers (sampler, evidence, splitter, citation gate) verbatim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_lexica_def as B

# ── OLD = whatever is currently frozen in the live engine. NEW = the candidate. ──────────────
OLD_PROMPT = B.VERSE_PROMPT

# The change is surgical and targets ONLY the sense/sub-use boundary (three touch-points,
# marked >>> below). Output format is unchanged (still numbered senses), so the splitter the
# card depends on is untouched. No named worked example, to avoid teaching to the psyche test.
NEW_PROMPT = """\
You define a biblical lemma from its own attested use. You are given:
- the lemma (Strong's number, original-language form, transliteration)
- the translation gloss set: the English words a translation used to render
  this lemma, with frequencies
- a set of occurrences: each a verse with surrounding context where this lemma
  appears, with the inflected form marked

Build the definition from what the lemma does across the supplied occurrences.
Reason from the contexts, not from prior knowledge of the word and not from the
gloss set.

Treat the gloss set as evidence, not as the definition. It records how one
translation disambiguated the word - a set of decisions, not the meaning. Where
a gloss matches what the context supports, you may use it. Where a gloss is
narrower, more loaded, or more doctrinally specific than the context requires,
name the gap. A gloss that imports a sense the surrounding text does not
establish is a freight flag, not a definition.

Method:
1. Read each occurrence in context. Ask what the lemma is doing there - what it
   refers to, what role it plays - independent of the English chosen.
2. Group occurrences into senses, one sense per distinct job the lemma does. Before
   opening a new sense, apply the sub-use test: is the lemma doing the SAME job here
   as in a sense you already have, differing only in what it is applied to or the
   circumstance it stands in? If so, it is a SUB-USE - keep it under that sense (you
   may note the variation in the sense's line), do not give it its own number. Open
   a new sense only when the lemma's meaning itself shifts - it is doing a different
   job, not the same job on a different object. A difference in the kind of thing
   referred to is not by itself a split or a merge; judge by whether the job is the
   same.
3. For each sense, cite the occurrences that ground it.
4. State the attested range: from the most concrete use to the most extended,
   with the contextual feature that shifts it.

Constraints:
- Reason only from the supplied occurrences. Do not import senses the supplied
  verses do not show, even if you know the word carries them elsewhere. If you
  reach for a sense and cannot point to a supplied verse, drop it.
- If the gloss set contains a sense none of the supplied occurrences exhibit, do
  not define it. Note that the gloss list includes it but the occurrences do not
  attest it. Do not invent context to cover it.
- Give as many senses as the lemma has distinct jobs, and no more. Do not split one
  job into several senses because it appears in several settings or is applied to
  several kinds of thing; do not merge two different jobs because they are related
  or share a setting.
- Do not narrate the word's later doctrinal or ecclesiastical career. No "came to
  mean," no "in later usage." Attested biblical use only.
- Define the word; do not adjudicate what doctrine rests on it.

Output (compact, dictionary-entry style):
- Senses: each a short gloss-free characterization with grounding references in
  parentheses, ordered by frequency in the supplied set. Where a sense carries a
  notable sub-use, note it within that sense's line, not as a separate sense.
- Range: one line on how far the word stretches and what moves it.
- Gloss notes: only where a gloss narrows, loads, or diverges from what the
  contexts support. Name the gloss and the divergence. Omit the line if nothing
  to flag.
- Coverage: if the supplied occurrences are too few or too clustered to
  characterize the range, say so in one line. Omit if coverage is adequate.

No preamble, no restating the lemma, no closing summary.
"""

# Test set: psyche (the vetted 4-sense baseline = the measuring stick) + the 5 contested
# forks (charis is the worst over-split at 7). Forks are model-free, so we are not testing
# whether the fork attaches (it always does) — we are testing that the NEW prompt keeps a
# clean, well-counted definition UNDER each fork.
TEST_WORDS = ["G5590", "G1344", "G5484", "G166", "G4561", "G1577"]
BASELINE = {"G5590": 4}          # psyche's vetted sense count
LABELS = {"G5590": "psyche", "G1344": "dikaioo", "G5484": "charis",
          "G166": "aionios", "G4561": "sarx", "G1577": "ekklesia"}


def show_prompts():
    """Print the OLD->NEW diff. FREE — no db, no model. Runs anywhere."""
    diff = difflib.unified_diff(
        OLD_PROMPT.splitlines(), NEW_PROMPT.splitlines(),
        fromfile="VERSE_PROMPT (OLD / frozen)", tofile="VERSE_PROMPT (NEW / candidate)",
        lineterm="")
    print("\n".join(diff))


def model_prose(client, system, sid, translit, gset, ctx):
    """Mirror build_lexica_def.model_prose EXACTLY (same model, max_tokens, no temperature
    override) — only the system prompt varies between OLD and NEW."""
    msg = client.messages.create(
        model=B.MODEL_SONNET, max_tokens=B.MAX_TOKENS, system=system,
        messages=[{"role": "user", "content": B.verse_user_msg(sid, translit, gset, ctx)}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def gather_evidence(conn, sid, budget):
    """The SAME evidence both prompts see. select_spread is deterministic, so this is one
    fixed sample per word — old vs new differ only in the prompt."""
    pred, params = B.abp_filter(conn, sid)
    gset = B.gloss_set(conn, pred, params)
    occs = B.occurrences(conn, pred, params)
    sample = B.select_spread(occs, budget)
    has_surface = B.table_exists(conn, "abp_surface")
    ctx = B.fetch_context(conn, sample, has_surface)
    lemma, translit = B.lex_head(conn, sid)
    ot = sum(1 for c in ctx if c[0] not in B.NT_BOOKS)
    return {"lemma": lemma, "translit": translit, "gset": gset, "ctx": ctx,
            "total": len(occs), "ot": ot, "nt": len(ctx) - ot}


def run_once(client, system, conn, sid, ev):
    """One generation + the two measurements: sense count (the way the card counts) and the
    citation real-miss (the free hallucination guard)."""
    raw = model_prose(client, system, sid, ev["translit"], ev["gset"], ev["ctx"])
    fields = B.split_definition(raw)
    gate = B.run_citation_gate(conn, sid, B.cited_refs(raw))
    return {"n": len(fields["sense_headlines"]),
            "headlines": fields["sense_headlines"],
            "real": gate["real"], "pass": gate["pass"], "total": gate["total"],
            "raw": raw}


def dist_line(runs):
    """A compact distribution string: sense-count -> times, mean, and total real-misses."""
    cnt = Counter(r["n"] for r in runs)
    dist = "{" + ", ".join(f"{k}:{cnt[k]}" for k in sorted(cnt)) + "}"
    mean = sum(r["n"] for r in runs) / len(runs)
    real_runs = sum(1 for r in runs if r["real"])
    return f"sense-count {dist}  mean {mean:.1f}   real-miss in {real_runs}/{len(runs)} runs"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"))
    ap.add_argument("--word", help="one G-number (default: the 6-word test set)")
    ap.add_argument("--runs", type=int, default=5, help="generations per prompt per word")
    ap.add_argument("--budget", type=int, default=B.BUDGET)
    ap.add_argument("--show-prompts", action="store_true", help="OLD->NEW diff, no db/model")
    ap.add_argument("--show-defs", action="store_true",
                    help="also print a full NEW definition (first run) per word")
    ap.add_argument("--all-headlines", action="store_true",
                    help="print EVERY run's sense headlines (see what the low-count runs merged)")
    ap.add_argument("--new-only", action="store_true",
                    help="skip the OLD control runs (OLD is already characterized) — half the calls")
    args = ap.parse_args()

    if args.show_prompts:
        show_prompts()
        return

    targets = [args.word.upper()] if args.word else list(TEST_WORDS)
    targets = [("G" + t if t[:1] not in ("G", "H") else t) for t in targets]

    calls = len(targets) * 2 * args.runs
    print(f"{len(targets)} word(s) x 2 prompts x {args.runs} runs = {calls} Sonnet calls "
          f"(~${calls * 0.03:.2f}).")

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.create_function("strip_accents", 1, B.strip_accents)

    import anthropic
    client = anthropic.Anthropic(api_key=B.get_key())

    summary = []
    for sid in targets:
        ev = gather_evidence(conn, sid, args.budget)
        label = LABELS.get(sid, sid)
        base = BASELINE.get(sid)
        print("\n" + "=" * 78)
        print(f"{sid}  {label}" + (f"   (baseline: {base} senses)" if base else ""))
        print(f"  evidence: {ev['total']} occ | {len(ev['gset'])} renderings | "
              f"fed {len(ev['ctx'])} ({ev['ot']} OT / {ev['nt']} NT)")

        old_runs = [] if args.new_only else \
            [run_once(client, OLD_PROMPT, conn, sid, ev) for _ in range(args.runs)]
        new_runs = [run_once(client, NEW_PROMPT, conn, sid, ev) for _ in range(args.runs)]
        if old_runs:
            print(f"  OLD prompt:  {dist_line(old_runs)}")
        print(f"  NEW prompt:  {dist_line(new_runs)}")

        # show WHICH senses the NEW prompt produced (guards against UNDER-splitting — losing
        # a real sense — which a count alone would hide). Pick the modal-count run.
        modal_n = Counter(r["n"] for r in new_runs).most_common(1)[0][0]
        sample = next(r for r in new_runs if r["n"] == modal_n)
        print(f"  NEW sample headlines (a {modal_n}-sense run):")
        for i, h in enumerate(sample["headlines"], 1):
            print(f"     {i}. {h}")

        if base is not None:
            hit = sum(1 for r in new_runs if r["n"] == base)
            mark = "OK" if hit >= (args.runs + 1) // 2 else "MISS"
            print(f"  baseline check: NEW hit {base} senses in {hit}/{args.runs} runs  [{mark}]")

        if args.all_headlines:
            def runs_lines(tag, runs):
                print(f"  all {tag} runs:")
                for k, r in enumerate(runs, 1):
                    hs = " | ".join((h[:55] + "…") if len(h) > 55 else h
                                    for h in r["headlines"]) or "(none — splitter found no senses)"
                    print(f"    #{k} ({r['n']}): {hs}")
            if old_runs:
                runs_lines("OLD", old_runs)
            runs_lines("NEW", new_runs)

        if args.show_defs:
            print("  --- full NEW definition (first run) ---")
            print("  " + new_runs[0]["raw"].replace("\n", "\n  "))

        om = sum(r["n"] for r in old_runs) / len(old_runs) if old_runs else None
        nm = sum(r["n"] for r in new_runs) / args.runs
        summary.append((sid, label, om, nm, base))

    conn.close()
    print("\n" + "=" * 78)
    print("SUMMARY — mean sense count, OLD -> NEW:")
    for sid, label, om, nm, base in summary:
        b = f"   (baseline {base})" if base else ""
        o = f"{om:.1f}" if om is not None else "—"
        print(f"  {sid:6} {label:10} {o} -> {nm:.1f}{b}")


if __name__ == "__main__":
    main()
