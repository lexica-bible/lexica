#!/usr/bin/env python3
"""
lexica_agreement.py  —  the AGREEMENT REVIEWER for the Lexica dictionary engine.

WHY THIS EXISTS (read once).
The verse engine's output is a DRAW. Run the same word on the same evidence twice and the
sense STRUCTURE wobbles: psyche came back 4 senses one batch, then a different 4, then 2 — same
prompt, same verses. Step 1 tried to cure that with a better prompt and it did NOT cure: the
residual wobble is the MEDIUM, not a tuning bug. So the safety mechanism is not a perfect prompt;
it is THIS — build a word several times and let the draws VOTE. A sense (a distinct JOB the lemma
does) that is present in some draws and absent in others is the flag.

WHAT THE COUNT MISSES (the finding that forced this rig to exist).
Sense COUNT lies. psyche clustered at 4 — but the runs hit 4 by DIFFERENT senses (some had the
inner self, one dropped it entirely; four leaked "appetite" back as its own sense). The citation
gate is blind to it too: it checks that every cited verse is REAL (a verse exists), never that a
SENSE dropped. Every cheap automatic gate reads PRESENCE, never SIGNIFICANCE. This reviewer reads
presence ACROSS DRAWS (the vote), which IS automatable. The SIGNIFICANCE call — does a varied
sense MATTER (a real hole) or not (a fine fold) — is left to human eyes, by design, for now.
(Whether a model can ever carry significance is Step 4, named and deferred.)

────────────────────────────────────────────────────────────────────────────────────────────────
THE HOLE-vs-FOLD PROCEDURE  (how to read the output — this is the actual gate)
────────────────────────────────────────────────────────────────────────────────────────────────
  1. Read the PER-DRAW SENSES. That is the ground truth; everything below it is an aid.
  2. Find the CONSENSUS structure: the jobs that appear in (nearly) every draw. Those are stable.
  3. Find the WOBBLES: any job present in some draws, absent in others. The rig surfaces these two
     ways, neither of which is a verdict —
       • JOB CLUSTERS — senses grouped across draws by a shared grounding verse. ROUGH (a fold
         draw can bridge two real jobs into one cluster; a job grounded on different verses can
         split). Use it to PROPOSE candidates, then check by eye.
       • PER-VERSE SUPPORT — how many draws cite each grounding verse. This is the clean presence
         skeleton: a verse cited in every draw is stable; a verse that loses support in some draws
         is exactly where a sense may be holing.
  4. Call each wobble HOLE or FOLD — THIS is the judgment, and it is YOURS:
       FOLD (benign): in the draws that "lack" the job, its meaning is still there — tucked under a
         neighbouring sense. Its grounding verses are still cited; the broader sense's wording
         covers the sub-use. Only the seam moved. Per the scenario-2 calibration, IGNORE folds
         (e.g. life-at-stake under the animating-life principle; appetite under the inner self).
       HOLE (disqualifying): in the draws that lack the job, the meaning is GONE — its verses drop
         out (per-verse support falls in those draws) or land under a sense that does not cover that
         meaning, and nothing else in the draw carries the job. A reader of that draw would never
         learn the word carries that sense.
     THE TEST that separates them: take the wobble job's grounding verses; in a draw WITHOUT the
     job's own sense, are those verses STILL CITED under a fair neighbour (FOLD) or DROPPED /
     mis-housed (HOLE)? Per-verse support is the quick read — a job whose verses keep full support
     across draws is folding; a job whose verses lose support in some draws is holing.
  5. VERDICT for the word:
       no wobbles, or every wobble is a fold  ->  STABLE.  Safe to ship from a single draw.
       any wobble is a hole                   ->  UNSTABLE. Do NOT ship a blind single draw — the
         engine sometimes drops a real sense. The ship target becomes the CONSENSUS structure,
         realised by a draw the reviewer has confirmed carries every stable job with no hole.
         (Selecting/writing that specific reviewed draw is Step 3 wiring, NOT built here.)

  CALIBRATION (scenario-2, locked): trust the engine; ignore near-duplicate folds; flag only the
  VANISH-OR-RESURRECT of a whole job. Don't nitpick wording — senses are worded differently every
  run by design, which is why this rig never string-matches them.

────────────────────────────────────────────────────────────────────────────────────────────────
SCOPE / SAFETY
────────────────────────────────────────────────────────────────────────────────────────────────
  • PA-ONLY (bible.db + the model key live there). READ-ONLY on bible.db — never writes lexica_def,
    never touches words/verses. It only reads evidence and calls the model.
  • Reuses build_lexica_def's FROZEN helpers verbatim (sampler / evidence / splitter / citation
    gate) so a sense is counted EXACTLY the way the card counts it.
  • Does NOT touch the live engine. The v3 candidate prompt is carried here as a frozen copy for
    review; it is promoted into build_lexica_def.VERSE_PROMPT only AFTER the six pass this reviewer
    (a separate, deliberate step).
  • The fork block on a contested word is deterministic (membership-only, model-free), so it is
    CONSTANT across draws and is excluded from the agreement question — this reviews the SENSES.
  • Each run is saved to a JSON (raw of every draw + parsed senses) so the review needs the model
    ONCE: re-read it free with --from-json, and Step 3 can pick a reviewed draw's raw to ship.

  workon bible-env
  export ANTHROPIC_API_KEY=$(grep -oE "sk-ant-[A-Za-z0-9_-]+" /var/www/www_lexica_bible_wsgi.py)
  python scripts/lexica_agreement.py --word G5590 --runs 10           # the canary (psyche), ~$0.30
  python scripts/lexica_agreement.py --runs 10                        # all six under v3, ~$1.80
  python scripts/lexica_agreement.py --word G5590 --prompt live --runs 10   # compare the live engine
  python scripts/lexica_agreement.py --from-json <saved.json>         # re-read a run, FREE (no model)
"""

import argparse, datetime, hashlib, json, os, re, sqlite3, sys
from collections import Counter, OrderedDict

# reuse the FROZEN, proven helpers (sampler, evidence, splitter, citation gate) verbatim — same
# import trick the other rigs use, so a "sense" here is exactly what the card stores.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_lexica_def as B

# ── the six pilot words: psyche (control, no fork) + the 5 frozen contested forks. ───────────────
PILOT = ["G5590", "G1344", "G5484", "G166", "G4561", "G1577"]
LABELS = {"G5590": "psyche", "G1344": "dikaioo", "G5484": "charis",
          "G166": "aionios", "G4561": "sarx", "G1577": "ekklesia"}

# ── PROMPTS the reviewer can run. "live" = whatever build_lexica_def currently ships (the frozen
# engine). "v3" = the candidate from the prompt session — same-job/different-job sub-use test,
# symmetric no-over-split/no-over-merge. It is carried here as a SELF-CONTAINED frozen copy so the
# reviewer survives the throwaway trial_lexica_prompt.py being deleted; if that rig is still present
# we soft-assert the two copies have not drifted. v3 is promoted into build_lexica_def only after
# the six pass review — until then the live engine is untouched. ───────────────────────────────────
V3_PROMPT = """\
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

PROMPTS = {"live": B.VERSE_PROMPT, "v3": V3_PROMPT}


def _check_v3_sync():
    """Loud if our frozen v3 copy has drifted from the trial rig's; silent if that rig is gone."""
    try:
        import trial_lexica_prompt as _TP
        if _TP.NEW_PROMPT.strip() != V3_PROMPT.strip():
            print("WARNING: V3_PROMPT here has DRIFTED from trial_lexica_prompt.NEW_PROMPT — "
                  "they should be identical until v3 is promoted.", file=sys.stderr)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════════════════════
# One draw, and the per-sense parse (the alignment skeleton).
# ══════════════════════════════════════════════════════════════════════════════════════════════
def draw_once(client, system, sid, translit, gset, ctx):
    """One generation. Mirrors build_lexica_def.model_prose EXACTLY (same model, max_tokens, no
    temperature override) — the only thing that varies between draws is the model's own sampling,
    which is the wobble we are measuring."""
    msg = client.messages.create(
        model=B.MODEL_SONNET, max_tokens=B.MAX_TOKENS, system=system,
        messages=[{"role": "user", "content": B.verse_user_msg(sid, translit, gset, ctx)}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def per_sense(senses_block):
    """Split the senses prose into [{headline, refs}] PER numbered sense. Reuses the live splitter's
    own headline regex so the sense boundaries match the card exactly; each sense's grounding refs
    are pulled from its own chunk (the parenthetical citations after the headline). The refs are the
    text-independent fingerprint we align on — never the wording, which changes every run."""
    block = senses_block or ""
    marks = list(B._HEADLINE_RE.finditer(block))
    out = []
    for i, m in enumerate(marks):
        start = m.start()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(block)
        chunk = block[start:end]
        headline = re.sub(r'^\d+\.\s*', '', m.group(1)).strip()
        out.append({"headline": headline, "refs": B.cited_refs(chunk)})
    return out


def parse_draw(conn, sid, raw):
    """raw prose -> {raw, senses[], count, audit}. count is taken the card's way (split_definition);
    senses[] carries each sense's refs for the cross-draw vote; audit is the free hallucination guard."""
    fields = B.split_definition(raw)
    senses = per_sense(fields["senses_block"])
    refs = B.cited_refs(raw)
    return {
        "raw": raw,
        "senses": senses,
        "count": len(fields["sense_headlines"]),
        "audit": B.run_citation_gate(conn, sid, refs),
    }


# ══════════════════════════════════════════════════════════════════════════════════════════════
# The two cross-draw views — both PRESENCE only, never a significance verdict.
# ══════════════════════════════════════════════════════════════════════════════════════════════
def cluster_jobs(draws):
    """ROUGH job clusters. Every sense (from every draw) is a node; two senses are linked if they
    share a grounding verse; connected components are candidate 'jobs'. Caveats baked in: a single
    draw contributing 2+ senses to one cluster means the cluster BRIDGED a real split (over-merge) —
    flagged so the reader distrusts it. Senses with no refs can't be aligned and stay singletons.
    This PROPOSES wobbles; it never decides hole vs fold. Returns clusters sorted by support."""
    nodes = []   # (draw_idx, sense_idx, headline, frozenset(refs))
    for di, d in enumerate(draws):
        for si, s in enumerate(d["senses"]):
            nodes.append((di, si, s["headline"], frozenset(tuple(r) for r in s["refs"])))
    parent = list(range(len(nodes)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    by_ref = {}
    for idx, (_, _, _, refs) in enumerate(nodes):
        for r in refs:
            by_ref.setdefault(r, []).append(idx)
    for idxs in by_ref.values():
        for k in range(1, len(idxs)):
            union(idxs[0], idxs[k])

    comps = OrderedDict()
    for idx in range(len(nodes)):
        comps.setdefault(find(idx), []).append(nodes[idx])

    clusters = []
    for members in comps.values():
        per_draw = Counter(m[0] for m in members)
        clusters.append({
            "headlines": [m[2] for m in members],
            "draws_present": sorted(per_draw),
            "support": len(per_draw),
            "bridged": max(per_draw.values()),     # >1 ⇒ a draw put 2+ senses here ⇒ over-merge
            "refless": all(not m[3] for m in members),
        })
    clusters.sort(key=lambda c: (-c["support"], -len(c["headlines"])))
    return clusters


def verse_support(draws):
    """For each grounding verse, how many draws cite it (anywhere). The clean presence skeleton:
    a verse cited in every draw is stable; a verse that loses support in some draws is where a
    sense may be holing. No clustering, no labels, no verdict. Returns {ref_tuple: count}."""
    cnt = Counter()
    for d in draws:
        seen = set()
        for s in d["senses"]:
            for r in s["refs"]:
                seen.add(tuple(r))
        for r in seen:
            cnt[r] += 1
    return cnt


# ══════════════════════════════════════════════════════════════════════════════════════════════
# Report — readable when pasted; the same text is saved next to the JSON.
# ══════════════════════════════════════════════════════════════════════════════════════════════
def fmt_ref(r):
    return f"{r[0]} {int(r[1])}:{int(r[2])}"


def render_report(sid, lemma, translit, prompt_name, ev, draws):
    """Build the human report (a list of lines). PRESENCE is computed; SIGNIFICANCE is left blank
    for the reader to fill — every word ends with a 'YOUR CALL' line, per the procedure up top."""
    L = []
    def w(s=""):
        L.append(s)

    n = len(draws)
    w("=" * 92)
    w(f"{sid}  {LABELS.get(sid, lemma)}   ({translit})    prompt: {prompt_name.upper()}"
      + ("   ⚠ candidate, NOT the live engine" if prompt_name == "v3" else "   (the live engine)"))
    w(f"  evidence: {ev['total']} occurrences | {ev['renderings']} renderings | "
      f"fed {ev['fed']} ({ev['ot']} OT / {ev['fed'] - ev['ot']} NT)   ·   N = {n} draws")
    if sid in B._CONTESTED_BY_SID:
        w("  (contested word: its fork block is deterministic + constant across draws — not reviewed here)")

    # count distribution — necessary, NOT sufficient (the count lies; see WHY at the top)
    dist = Counter(d["count"] for d in draws)
    dist_s = "{" + ", ".join(f"{k}:{dist[k]}" for k in sorted(dist)) + "}"
    mean = sum(d["count"] for d in draws) / n
    w("")
    w(f"  SENSE-COUNT spread: {dist_s}  mean {mean:.1f}   "
      f"— a clustered count is necessary but NOT sufficient; the structure is the read.")
    zero = [i + 1 for i, d in enumerate(draws) if d["count"] == 0]
    if zero:
        w(f"  ⚠ {len(zero)} draw(s) parsed to 0 senses (format break — inspect raw): {zero}")
    bad = [(i + 1, d["audit"]["real"]) for i, d in enumerate(draws) if d["audit"]["real"]]
    if bad:
        w(f"  ⚠ citation real-miss (possible hallucinated verse) in draw(s): "
          + ", ".join(f"#{i}({r})" for i, r in bad))

    # 1 — PER-DRAW SENSES: the ground truth
    w("")
    w("  ── PER-DRAW SENSES (headline — grounding verses) — THE GROUND TRUTH ──")
    for i, d in enumerate(draws, 1):
        w(f"  draw {i:>2}  [{d['count']} senses]")
        for j, s in enumerate(d["senses"], 1):
            refs = ", ".join(fmt_ref(r) for r in s["refs"]) or "(no refs cited)"
            w(f"      {j}. {s['headline']}")
            w(f"           {refs}")

    # 2 — JOB CLUSTERS (rough aid)
    clusters = cluster_jobs(draws)
    w("")
    w("  ── JOB CLUSTERS (rough — grouped by a shared grounding verse; verify by eye) ──")
    for ci, c in enumerate(clusters):
        tag = chr(ord('A') + ci) if ci < 26 else f"#{ci}"
        absent = [k + 1 for k in range(n) if k not in c["draws_present"]]
        flag = "" if c["support"] == n else f"   ◄ WOBBLE (absent in draws {absent})"
        note = ""
        if c["bridged"] > 1:
            note = "   [bridges 2+ senses within a draw — likely over-merged, read by eye]"
        if c["refless"]:
            note = "   [no refs — could not be aligned; read by eye]"
        w(f"  cluster {tag}   support {c['support']}/{n}{flag}{note}")
        seen, reps = set(), []
        for h in c["headlines"]:
            key = h.lower()
            if key not in seen:
                seen.add(key)
                reps.append(h)
        for h in reps[:4]:
            w(f"        · {h}")
        if len(reps) > 4:
            w(f"        · … and {len(reps) - 4} more wordings")

    # 3 — PER-VERSE SUPPORT: the clean presence skeleton
    cnt = verse_support(draws)
    w("")
    w("  ── PER-VERSE SUPPORT (draws citing each grounding verse) — the presence skeleton ──")
    full = sorted([r for r, c in cnt.items() if c == n], key=fmt_ref)
    w(f"  full support ({n}/{n}) — stable skeleton ({len(full)} verses):")
    if full:
        w("      " + ", ".join(fmt_ref(r) for r in full))
    partial = sorted([(r, c) for r, c in cnt.items() if c < n], key=lambda rc: (rc[1], fmt_ref(rc[0])))
    w(f"  presence wobble (<{n}/{n}) — inspect the sense each anchors ({len(partial)} verses):")
    for r, c in partial:
        miss = [k + 1 for k in range(n) if r not in
                {tuple(x) for d in [draws[k]] for s in d["senses"] for x in s["refs"]}]
        w(f"      {fmt_ref(r):<14} {c}/{n}   missing in draws {miss}")

    # 4 — WOBBLE summary + the call the reader must make
    wob = [c for c in clusters if 1 <= c["support"] < n and not c["refless"]]
    w("")
    w("  ── WOBBLES TO JUDGE (apply HOLE-vs-FOLD; the procedure is at the top of this file) ──")
    if not wob and not partial:
        w("  none — every job and every grounding verse holds across all draws. Looks STABLE.")
    else:
        for ci, c in enumerate(clusters):
            if c in wob:
                tag = chr(ord('A') + ci) if ci < 26 else f"#{ci}"
                absent = [k + 1 for k in range(n) if k not in c["draws_present"]]
                rep = c["headlines"][0] if c["headlines"] else "(?)"
                w(f"  • cluster {tag} \"{rep}\" — support {c['support']}/{n}, absent in draws {absent}.")
                w(f"      In those draws: is this FOLDED under a neighbour (fine) or a HOLE (flag)?")
        if partial and not wob:
            w("  • only per-verse citation jitter (no whole job vanished) — usually fold/noise; "
              "skim the low-support verses above to be sure.")
    w("")
    w(f"  => YOUR CALL for {LABELS.get(sid, sid)}:  STABLE (ship from one draw)  |  "
      f"UNSTABLE-HOLE (name the dropped job)")
    return L


def evidence_summary(conn, sid, budget, has_surface):
    """Gather the SAME deterministic evidence every draw sees (select_spread is fixed)."""
    pred, params = B.abp_filter(conn, sid)
    gset = B.gloss_set(conn, pred, params)
    occs = B.occurrences(conn, pred, params)
    sample = B.select_spread(occs, budget)
    ctx = B.fetch_context(conn, sample, has_surface)
    lemma, translit = B.lex_head(conn, sid)
    ot = sum(1 for c in ctx if c[0] not in B.NT_BOOKS)
    return {"lemma": lemma, "translit": translit, "gset": gset, "ctx": ctx,
            "total": len(occs), "renderings": len(gset), "fed": len(ctx), "ot": ot}


def save_run(save_dir, sid, prompt_name, ev, draws, report_lines):
    """Persist the whole run so the review needs the model ONCE: re-read free with --from-json,
    and Step 3 can lift a reviewed draw's raw to ship. JSON holds raw + parsed senses per draw."""
    ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    base = os.path.join(os.path.expanduser(save_dir), f"agreement_{sid}_{prompt_name}_{ts}")
    payload = {
        "strongs": sid, "lemma": ev["lemma"], "translit": ev["translit"],
        "prompt": prompt_name, "prompt_sha1": hashlib.sha1(PROMPTS[prompt_name].encode()).hexdigest()[:12],
        "runs": len(draws),
        "evidence": {k: ev[k] for k in ("total", "renderings", "fed", "ot")},
        "draws": [{"raw": d["raw"], "count": d["count"], "audit": d["audit"],
                   "senses": [{"headline": s["headline"],
                               "refs": [fmt_ref(r) for r in s["refs"]]} for s in d["senses"]]}
                  for d in draws],
        "report": "\n".join(report_lines),
    }
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    with open(base + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")
    return base


def from_json(path):
    """Re-read a saved run and re-render the report — FREE, no model. Lets the reader (or a better
    report) re-analyse the SAME draws without paying for generation again."""
    with open(os.path.expanduser(path), encoding="utf-8") as f:
        p = json.load(f)
    # rebuild the in-memory draw shape the renderer expects (refs back to tuples)
    def to_tuple(s):
        m = re.match(r'(\S+)\s+(\d+):(\d+)', s)
        return (m.group(1), int(m.group(2)), int(m.group(3))) if m else (s, 0, 0)
    draws = [{"raw": d.get("raw", ""), "count": d["count"], "audit": d["audit"],
              "senses": [{"headline": s["headline"], "refs": [to_tuple(x) for x in s["refs"]]}
                         for s in d["senses"]]} for d in p["draws"]]
    ev = {"lemma": p["lemma"], "translit": p["translit"], "renderings": p["evidence"]["renderings"],
          "total": p["evidence"]["total"], "fed": p["evidence"]["fed"], "ot": p["evidence"]["ot"]}
    print("\n".join(render_report(p["strongs"], p["lemma"], p["translit"], p["prompt"], ev, draws)))


def main():
    ap = argparse.ArgumentParser(description="Agreement reviewer for the Lexica dictionary engine.")
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"))
    ap.add_argument("--word", help="one G-number, e.g. G5590 (default: the six pilot words)")
    ap.add_argument("--prompt", choices=list(PROMPTS), default="v3",
                    help="which engine to review: v3 (candidate, default) or live (frozen engine)")
    ap.add_argument("--runs", type=int, default=10, help="draws per word (10 reproduces the canary)")
    ap.add_argument("--budget", type=int, default=B.BUDGET)
    ap.add_argument("--save-dir", default="~/bible-db", help="where the per-run JSON/txt land")
    ap.add_argument("--no-save", action="store_true", help="print only, do not write the run files")
    ap.add_argument("--from-json", help="re-render a saved run, FREE (no model) — pass its .json")
    args = ap.parse_args()

    if args.from_json:
        from_json(args.from_json)
        return

    _check_v3_sync()
    system = PROMPTS[args.prompt]
    targets = [args.word.upper()] if args.word else list(PILOT)
    targets = [("G" + t if t[:1] not in ("G", "H") else t) for t in targets]

    calls = len(targets) * args.runs
    print(f"prompt: {args.prompt.upper()}   {len(targets)} word(s) x {args.runs} draws = {calls} "
          f"Sonnet calls (~${calls * 0.03:.2f}).")

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.create_function("strip_accents", 1, B.strip_accents)
    has_surface = B.table_exists(conn, "abp_surface")

    import anthropic
    client = anthropic.Anthropic(api_key=B.get_key())

    for sid in targets:
        ev = evidence_summary(conn, sid, args.budget, has_surface)
        if not ev["ctx"]:
            print(f"\n{sid}: no occurrences — skip.")
            continue
        print(f"\n{sid} {LABELS.get(sid, '')}: drawing {args.runs}× …", flush=True)
        draws = []
        for k in range(args.runs):
            raw = draw_once(client, system, sid, ev["translit"], ev["gset"], ev["ctx"])
            draws.append(parse_draw(conn, sid, raw))
            print(f"   draw {k + 1}/{args.runs}: {draws[-1]['count']} senses", flush=True)
        report = render_report(sid, ev["lemma"], ev["translit"], args.prompt, ev, draws)
        print("\n".join(report))
        if not args.no_save:
            base = save_run(args.save_dir, sid, args.prompt, ev, draws, report)
            print(f"\n  saved: {base}.json  (+ .txt)")

    conn.close()


if __name__ == "__main__":
    main()
