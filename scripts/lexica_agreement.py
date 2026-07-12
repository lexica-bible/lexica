#!/usr/bin/env python3
"""
lexica_agreement.py  —  the AGREEMENT REVIEWER for the Lexica dictionary engine.

WHY THIS EXISTS (read once).
The verse engine's output is a DRAW. Run the same word on the same evidence twice and the sense
STRUCTURE wobbles: psyche came back 4 senses one batch, then a different 4, then 2 — same prompt,
same verses. Step 1 tried to cure that with a better prompt and it did NOT cure: the residual
wobble is the MEDIUM, not a tuning bug. So the safety mechanism is not a perfect prompt; it is
THIS — build a word several times and let the draws VOTE. A sense (a distinct JOB the lemma does)
that is present in some draws and absent in others is the flag.

WHAT THE COUNT MISSES (the finding that forced this rig to exist).
Sense COUNT lies. psyche clustered at 4 — but the runs hit 4 by DIFFERENT senses (some had the
inner self, one dropped it entirely; four leaked "appetite" back as its own sense). The citation
gate is blind to it too: it checks that every cited verse is REAL (a verse exists), never that a
SENSE dropped. Every cheap automatic gate reads PRESENCE, never SIGNIFICANCE. This reviewer reads
presence ACROSS DRAWS (the vote), which IS automatable. The SIGNIFICANCE call — does a varied
sense MATTER (a real hole) or not (a fine fold) — is left to human eyes, by design, for now.
(Whether a model can ever carry significance is Step 4, named and deferred.)

WHY SUPPORT COUNT ALONE IS NOT ENOUGH (the second trap, same shape as the first).
"How many draws cite this verse" looks like the whole answer and is not. A verse can stay fully
cited while MIGRATING to a different sense; and a droppable sub-use can sit at FULL support while a
core sense holes BELOW it — so support count alone can rank a fold ABOVE a hole. The fix is a
second column, per verse: not just how often it is cited, but WHO it keeps company with — which
other verses share its sense across the draws. A verse that keeps support and merely regroups is
folding; a verse that loses support, or whose core partner stops travelling with it, is holing.
(Company is counted ONCE PER DRAW — a pair sharing a sense, or both being cited, counts a single
draw no matter what the engine does inside it — so a stuttered draw that repeats a sense can't push
a count past the draw total; a draw's near-duplicate senses are also collapsed by verse set first.)

────────────────────────────────────────────────────────────────────────────────────────────────
THE HOLE-vs-FOLD PROCEDURE  (how to read the output — this is the actual gate)
────────────────────────────────────────────────────────────────────────────────────────────────
  1. Read the PER-DRAW SENSES. That is the ground truth; everything below it is a summary of it.
  2. Find the CONSENSUS structure: the jobs that appear in (nearly) every draw. Those are stable.
  3. Find the WOBBLES with the two columns the rig prints, neither of which is a verdict:
       • PER-VERSE SUPPORT — how many draws cite each grounding verse. A verse cited in every draw
         is present; a verse that loses support in some draws is where a sense may be holing.
       • PER-VERSE COMPANY — WHO each verse shares a sense with across the draws. This is the column
         support alone can't give you: a verse can stay fully cited while MIGRATING to another sense,
         and a sub-use can sit at FULL support while a core sense holes below it. The company tells
         a regroup (fold) apart from a defection (hole).
  4. Call each wobble HOLE or FOLD — THIS is the judgment, and it is YOURS. The discriminator:
       FOLD (benign): the meaning never leaves — its verses keep (near-)full support across draws,
         they just REGROUP (the same verses sit under their own sense some runs, tucked under a
         neighbour other runs). Only the seam moved. Per scenario-2, IGNORE folds (e.g. appetite
         under the inner self; life-at-stake under the animating-life principle).
       HOLE (disqualifying): the meaning actually leaves — its verses LOSE support in some draws,
         or its core pair DISSOLVES (one verse drops, the other defects to an unrelated sense), and
         nothing in those draws carries the job. A reader of that draw would never learn the word
         carries that sense.
     THE TEST: take the wobble's grounding verses. Do they keep support and merely regroup (FOLD),
     or does their support fall / the pair break apart (HOLE)? Read SUPPORT for the drop and COMPANY
     for regroup-vs-defect — a verse that drops while its partner stays cited is re-shelved (fold). A
     verse that drops while its main partner ALSO drops is a BACK-CHECK flag, NOT an auto-hole: a small
     MARGINAL sub-sense that drops as a unit looks identical on the counts, and that is a fine fold. Go
     to the per-draw lists and ask whether a whole DISTINCT job vanished (hole) or only a marginal
     sub-sense folded away (fine). The flag finds candidates; the per-draw lists make the call.
  5. VERDICT for the word:
       no wobbles, or every wobble is a fold  ->  STABLE.  Safe to ship from a single draw.
       any wobble is a hole                   ->  UNSTABLE. Do NOT ship a blind single draw — the
         engine sometimes drops a real sense. The ship target becomes the CONSENSUS structure,
         realised by a draw the reviewer has confirmed carries every stable job with no hole.
         (Selecting/writing that specific reviewed draw is Step 3 wiring, NOT built here.)

  READ IT COLD. The honest test of this reviewer is whether the split is FORCED by the numbers, not
  read in from what you already expect. Cover the expectation; if a hole is real it shows as a
  support drop whose partner also leaves — derivable from the columns without a prior. That is the
  whole point: at the rare-word tail you will have no prior.

  CALIBRATION (scenario-2, locked): trust the engine; ignore near-duplicate folds; flag only the
  VANISH-OR-RESURRECT of a whole job. Don't nitpick wording — senses are worded differently every
  run by design, which is why this rig never string-matches them (it aligns on grounding verses).

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
  • KEEP THE PER-DRAW LISTS IN THE REPORT — PERMANENTLY. They are the audit layer FOR the company
    column, not redundant with it. The self-check only screams on VISIBLE corruption (a count above the
    draw total — the >10 bug). A silent mis-merge that produces sane-LOOKING company numbers has nothing
    to catch it except a human dropping to the per-draw layer (which is exactly how the >10 bug was
    caught). The day the lists are stripped is the day a plausible-but-wrong company number has nothing
    to check it against. Same presence-vs-significance lesson: the column says verses travel together,
    the per-draw lists are the only place to confirm the company count was COMPUTED right.

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
# engine). "v7" = a SELF-CONTAINED frozen copy of that engine prompt, carried here so the reviewer
# survives the throwaway trial_lexica_prompt.py being deleted, and so every saved run records the
# exact prompt bytes it drew under. It MUST stay byte-identical to B.VERSE_PROMPT (the reviewer
# measures the LIVE engine); _check_prompt_sync asserts that. v3 was promoted into build_lexica_def
# 2026-06-25; V4 (2026-07-07) added the Formatting block (no-slash headlines etc.); V5 (2026-07-07)
# added the term-of-art line; V6 (2026-07-07) added the translation-freight line (the 4th freight
# axis, ENGINE_LESSONS #18) + the Sub-use whitespace line. V7 (2026-07-08, the window walk): line→
# entry, two-directional gloss flag, headline scope marker, Sub-use placement rule (files by JOB —
# the ὀφθαλμός wall; two-way placement watch pre-registered), house-shape organizing paragraph,
# gloss-note sense anchors (permissive — no forced anchor). All bumps STYLE/FRAMING-ONLY except the
# placement rule, which steers sub-use filing (control fire = ὀφθαλμός at requeue). V8 PROMOTED
# 2026-07-10 (step-5 control fire, G2665; JP KEEP ruling): four pure-insertion edits — sub-use
# named-by-job (#40), uncited-grouping check, attribution register (#29), tail-list disjointness
# (#37). v8 below is now the FROZEN COPY OF THE LIVE ENGINE (the sync check compares it); v7 is
# the previous engine, kept for historical floors. ─────────────────────────────────────────────
V7_PROMPT = """\
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
narrower or broader, more or less loaded, or more doctrinally specific than the
context supports, name the gap. A gloss that imports a sense the surrounding text does not
establish is a freight flag, not a definition.

Method:
1. Read each occurrence in context. Ask what the lemma is doing there - what it
   refers to, what role it plays - independent of the English chosen.
2. Group occurrences into senses, one sense per distinct job the lemma does. Before
   opening a new sense, apply the sub-use test: is the lemma doing the SAME job here
   as in a sense you already have, differing only in what it is applied to or the
   circumstance it stands in? If so, it is a SUB-USE - keep it under that sense (you
   may note the variation within that sense's entry), do not give it its own number.
   A Sub-use files under the sense whose job it shares - the same test as opening a
   sense - not under the sense whose imagery or objects its verses happen to mention.
   Open a new sense only when the lemma's meaning itself shifts - it is doing a different
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
  notable sub-use, note it within that sense's entry, not as a separate sense. The
  headline is not a bare gloss; a gloss word the context supports may appear in the
  elaboration.
- Range: one line on how far the word stretches and what moves it.
- Gloss notes: only where a gloss narrows, loads, or diverges from what the
  contexts support. Name the gloss and the divergence. Omit the line if nothing
  to flag. Where a gloss note bears on a particular sense, name that sense by
  number; notes with no sense to anchor stay unanchored.
- Coverage: if the supplied occurrences are too few or too clustered to
  characterize the range, say so in one line. Omit if coverage is adequate.

Formatting (senses and range - how to lay them out and word them, not which senses to give):
- Each sense headline is one capitalized head phrase; where it needs an elaboration,
  set the elaboration off with an em-dash, as in "Senior in age — the older or prior
  of two." Commit to one phrasing per headline: join a real grammatical pair with
  "and" or a parenthesis (e.g. "greater (comparative and superlative)"), never a
  slash or a slash-apposition ("set apart / belonging to").
- Prefer descriptive vocabulary with no life as a term of art in theological debate;
  where a plain word carries the sense, use it (e.g. "applied to a group" rather than
  "corporate").
- Name each sense by what the verses show the lemma doing, not by an English or Latin
  category that carves a domain the Greek does not. The test is not whether a word is
  loaded (all are) but whether its English meaning tracks the Greek or overrides it:
  avoid a word whose ordinary sense has drifted from the lemma it translates, or that
  imports a conceptual domain the text does not carve (e.g. "moral" for a disposition —
  name the attested quality the verses show instead). Do not hunt for a freight-free
  word; describe the lemma's own carving.
- Introduce any sub-use with one consistent lead-in, "Sub-use:", not a mix of lead-ins.
  Each Sub-use begins on its own line, with a blank line before it.
- Where one sense covers several recurring constructions, open it with a brief
  organizing paragraph naming them, then give each construction or Sub-use as its own
  labeled item on its own line. Keep flowing prose where prose is describing; use
  labeled own-line items where citations cluster.
- Put each sense's grounding refs in parentheses; where an example phrase clarifies,
  pair it with its own ref inline - "(1Co 13:13: the greatest of these)" - in
  preference to a long semicolon chain of bare refs.
- Keep Range as one paragraph in this shape: the most concrete use first, then the
  most extended, then the contextual feature that moves the word between them.

No preamble, no restating the lemma, no closing summary.
"""

# ── V8 DRAFT (step 4, 2026-07-10) — a CANDIDATE, not the engine. DRAFTED, NOT FIRED: the live
# default everywhere stays v7 until JP's step-4 ruling list returns and the step-5 control fire
# runs (close-plan sequencing). Four edits over V7, each traceable to a ruled pile item (the
# per-edit table is banked in AUDIT_lexica_rollout.md, STEP-4 entry):
#   A (#29) attribution register — attribute-not-adjudicate pass-shape for disputed verses
#     (ἁμαρτία: 7 pulls, containment worked / generation never did; dossier pass-shape codified)
#   B (#40) sub-use architecture freight — name sub-uses by job in the verses' own terms, never
#     by an unattested quality/attitude; verse description must match the verse text
#     (κατανοέω p2 devotional sub-use + hint-1 misdescriptions)
#   C (#37) cite-where-the-prose-grounds — no comprehensive per-sense tail lists re-listing
#     verses (βέλος 4-point gradient: prose-cites drew 0 doubles, comprehensive tails drew 5)
#   D (σκληρύνω watch) uncited-category — a group the prose asserts must cite a member
# Deliberate NON-edits (WS3 amended scoping — noise families are TOOLING fixes, never prompt
# edits): #28 citation shorthand · dangling-ref prose noise · quote-strip artifact ·
# disclaimer-as-cite. Divergence evidence (ταμεῖον) carries no wording candidate — the hint
# mechanism + the #30 flag are the levers. ─────────────────────────────────────────────────────
V8_DRAFT_PROMPT = """\
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
narrower or broader, more or less loaded, or more doctrinally specific than the
context supports, name the gap. A gloss that imports a sense the surrounding text does not
establish is a freight flag, not a definition.

Method:
1. Read each occurrence in context. Ask what the lemma is doing there - what it
   refers to, what role it plays - independent of the English chosen.
2. Group occurrences into senses, one sense per distinct job the lemma does. Before
   opening a new sense, apply the sub-use test: is the lemma doing the SAME job here
   as in a sense you already have, differing only in what it is applied to or the
   circumstance it stands in? If so, it is a SUB-USE - keep it under that sense (you
   may note the variation within that sense's entry), do not give it its own number.
   A Sub-use files under the sense whose job it shares - the same test as opening a
   sense - not under the sense whose imagery or objects its verses happen to mention.
   Name a sub-use by the shared job in the verses' own terms, never by a quality,
   attitude, or tone the verse text does not state; and the sentence describing a
   verse within a sub-use must match what that verse shows happening, not what the
   grouping suggests.
   Open a new sense only when the lemma's meaning itself shifts - it is doing a different
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
- Any grouping the entry asserts inside a sense - a passive use, a self-directed
  use, a class of subjects - must cite at least one supplied verse that belongs to
  it. A grouping whose members are all uncited is not shown to the reader: cite a
  member or drop the claim.
- Do not narrate the word's later doctrinal or ecclesiastical career. No "came to
  mean," no "in later usage." Attested biblical use only.
- Define the word; do not adjudicate what doctrine rests on it.
- Where a cited verse's reading is genuinely disputed - where traditions or
  translations divide over what the word does there - attribute rather than
  adjudicate: state what this translation does and what it follows, and leave which
  reading is right unstated. The shape that passes: "ABP renders with the
  sacrificial sense, following the LXX use." Asserting the disputed meaning as the
  verse's settled sense and asserting its denial are the same failure.

Output (compact, dictionary-entry style):
- Senses: each a short gloss-free characterization with grounding references in
  parentheses, ordered by frequency in the supplied set. Where a sense carries a
  notable sub-use, note it within that sense's entry, not as a separate sense. The
  headline is not a bare gloss; a gloss word the context supports may appear in the
  elaboration.
- Range: one line on how far the word stretches and what moves it.
- Gloss notes: only where a gloss narrows, loads, or diverges from what the
  contexts support. Name the gloss and the divergence. Omit the line if nothing
  to flag. Where a gloss note bears on a particular sense, name that sense by
  number; notes with no sense to anchor stay unanchored.
- Coverage: if the supplied occurrences are too few or too clustered to
  characterize the range, say so in one line. Omit if coverage is adequate.

Formatting (senses and range - how to lay them out and word them, not which senses to give):
- Each sense headline is one capitalized head phrase; where it needs an elaboration,
  set the elaboration off with an em-dash, as in "Senior in age — the older or prior
  of two." Commit to one phrasing per headline: join a real grammatical pair with
  "and" or a parenthesis (e.g. "greater (comparative and superlative)"), never a
  slash or a slash-apposition ("set apart / belonging to").
- Prefer descriptive vocabulary with no life as a term of art in theological debate;
  where a plain word carries the sense, use it (e.g. "applied to a group" rather than
  "corporate").
- Name each sense by what the verses show the lemma doing, not by an English or Latin
  category that carves a domain the Greek does not. The test is not whether a word is
  loaded (all are) but whether its English meaning tracks the Greek or overrides it:
  avoid a word whose ordinary sense has drifted from the lemma it translates, or that
  imports a conceptual domain the text does not carve (e.g. "moral" for a disposition —
  name the attested quality the verses show instead). Do not hunt for a freight-free
  word; describe the lemma's own carving.
- Introduce any sub-use with one consistent lead-in, "Sub-use:", not a mix of lead-ins.
  Each Sub-use begins on its own line, with a blank line before it.
- Where one sense covers several recurring constructions, open it with a brief
  organizing paragraph naming them, then give each construction or Sub-use as its own
  labeled item on its own line. Keep flowing prose where prose is describing; use
  labeled own-line items where citations cluster.
- Put each sense's grounding refs in parentheses; where an example phrase clarifies,
  pair it with its own ref inline - "(1Co 13:13: the greatest of these)" - in
  preference to a long semicolon chain of bare refs.
- Cite where the prose grounds: each verse appears at the sense whose entry places
  it. Do not close a sense with a comprehensive reference list that re-lists verses
  already cited elsewhere; a verse that genuinely carries two senses is named in the
  prose as carrying both, not silently listed twice.
- Keep Range as one paragraph in this shape: the most concrete use first, then the
  most extended, then the contextual feature that moves the word between them.

No preamble, no restating the lemma, no closing summary.
"""

PROMPTS = {"live": B.VERSE_PROMPT, "v7": V7_PROMPT, "v8": V8_DRAFT_PROMPT}


def _check_prompt_sync():
    """Loud if our frozen copy of the LIVE engine has drifted from build_lexica_def.VERSE_PROMPT.
    This is the invariant that matters: the reviewer must draw under the SAME prompt the build
    ships, or it isn't measuring the live engine. The frozen copy is v8 since the 2026-07-10
    promotion (KEEP ruling, step-5 control fire); v7 is historical and intentionally differs."""
    if V8_DRAFT_PROMPT.strip() != B.VERSE_PROMPT.strip():
        print("WARNING: the v8 copy here has DRIFTED from build_lexica_def.VERSE_PROMPT — they must "
              "be byte-identical so the reviewer measures the live engine. Re-sync before trusting "
              "a run.", file=sys.stderr)


# ══════════════════════════════════════════════════════════════════════════════════════════════
# One draw, and the per-sense parse (the alignment skeleton).
# ══════════════════════════════════════════════════════════════════════════════════════════════
def draw_once(client, system, sid, translit, gset, ctx, pmap=None):
    """One generation. Mirrors build_lexica_def.model_prose EXACTLY (same model, max_tokens, no
    temperature override) — the only thing that varies between draws is the model's own sampling,
    which is the wobble we are measuring. pmap = the phrase-context annotation the build feeds
    (2026-07-12 fragment-rendering fix) — the mirror invariant covers it like the rest."""
    msg = client.messages.create(
        model=B.MODEL_SONNET, max_tokens=B.MAX_TOKENS, system=system,
        messages=[{"role": "user", "content": B.verse_user_msg(sid, translit, gset, ctx, pmap=pmap)}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def per_sense(senses_block):
    """Split the senses prose into [{headline, refs}] PER numbered sense. Reuses the production
    splitter B._sense_spans (bold headers, OR a plain / number-outside-bold fallback) so a draw that
    formats its senses the drift way parses HERE exactly as it does in the ship engine — refs pulled
    from each sense's own chunk (the fingerprint we align on, never the wording).
    NOTE: this used to keep its OWN bold-only copy (B._HEADLINE_RE) of the split — a batch-one
    reuse-rule violation that silently 0'd 5/10 μέγας draws whose senses were numbered '1. **text**'
    (number outside the bold). Reusing _sense_spans is the fix; the ship path was never at risk."""
    return [{"headline": lead, "refs": B.cited_refs(chunk)}
            for lead, chunk in B._sense_spans(senses_block or "")]


DEDUP_JACCARD = 0.6   # within ONE draw, two senses whose grounding-verse sets overlap at least this
                      # much are the SAME job stuttered (the engine sometimes repeats a sense under a
                      # reworded headline). Wide margin: true stutters overlap ~0.85+, genuinely
                      # distinct senses in a draw overlap <0.3, so the exact value is not load-bearing.


def _jaccard(a, b):
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def merge_near_dup_senses(senses):
    """Within ONE draw, collapse senses that are the same job stuttered (near-identical grounding
    verses) into one. Left alone a stutter (a) inflates the sense count and (b) made a verse-pair
    'share a sense' more than once in a single draw, pushing company counts ABOVE the draw total
    (psyche draw 9 came back '9 senses', really ~5 — and produced impossible '13/10' numbers). We merge
    by VERSE SET, never by headline text (text varies every run by design). The company math is also
    fixed independently (a pair counts once per draw), so this dedup makes the COUNT honest and surfaces
    the stutter — it is NOT what keeps company in range. Returns (merged, n_before, n_after); each merged
    sense = {headlines:[...], refs:[...]}."""
    items = []
    for s in senses:
        hl = s.get("headlines") or ([s["headline"]] if s.get("headline") else [])
        items.append({"headlines": list(hl), "refs": list(s["refs"]),
                      "set": set(tuple(r) for r in s["refs"])})
    merged = []
    for it in items:
        hit = next((m for m in merged if _jaccard(it["set"], m["set"]) >= DEDUP_JACCARD), None)
        if hit:
            hit["headlines"] += it["headlines"]
            hit["set"] |= it["set"]
            have = set(hit["refs"])
            for r in it["refs"]:
                if r not in have:
                    hit["refs"].append(r)
                    have.add(r)
        else:
            merged.append(it)
    return [{"headlines": m["headlines"], "refs": m["refs"]} for m in merged], len(senses), len(merged)


def parse_draw(conn, sid, raw):
    """raw prose -> {raw, senses[], count, raw_count, audit}. senses[] carries each sense's headlines +
    refs for the cross-draw vote, with a stuttered draw's near-duplicate senses collapsed by verse set;
    count = the DISTINCT-job count (raw_count = what the engine emitted; raw_count > count ⇒ a stutter);
    audit is the free hallucination guard."""
    fields = B.split_definition(raw)
    senses, n_before, n_after = merge_near_dup_senses(per_sense(fields["senses_block"]))
    refs = B.cited_refs(raw)
    return {
        "raw": raw,
        "senses": senses,
        "count": n_after,
        "raw_count": n_before,
        # LOUD marker source (banked condition, G2168 2026-07-10): 'headline' = the one-sense
        # fallback fired — printed on the per-draw line so every fallback parse is inspectable.
        "split_mode": B.sense_split_mode(fields["senses_block"]),
        "audit": B.run_citation_gate(conn, sid, refs),
    }


# ══════════════════════════════════════════════════════════════════════════════════════════════
# The cross-draw view — PRESENCE + COMPANY, never a significance verdict.
# ══════════════════════════════════════════════════════════════════════════════════════════════
def verse_company(draws, valid_books=None):
    """Per grounding verse: how many draws cite it (SUPPORT) and WHO it shares a sense with across
    those draws (COMPANY). Support alone misleads — a droppable sub-use can sit at full support while
    a core sense holes below it — so the company is the second column: a verse that keeps support AND
    merely regroups is folding; one that loses support or whose core partner stops travelling with it
    is holing. Label-free, threshold-free. A verse-pair is counted AT MOST ONCE PER DRAW (whether they
    share a sense, and whether both are cited), so a stuttered draw repeating a sense can never push a
    count past the draw total — same_sense <= co_cited <= n, always. A ref whose book is not in
    valid_books (a model typo like '2Ko' for '2Co') is dropped here so it can't spawn a phantom
    low-support verse. Returns (support, same_sense, co_cited, cite_draws, n)."""
    def ok(r):
        return valid_books is None or r[0] in valid_books
    n = len(draws)
    support = Counter()            # v -> #draws citing v anywhere
    cite_draws = {}                # v -> set(draw idx) citing v
    same_sense = {}                # v -> Counter(w -> #draws v,w share a sense)  (<= n)
    co_cited = {}                  # v -> Counter(w -> #draws both v,w cited)     (<= n)
    for di, d in enumerate(draws):
        sense_sets = [set(tuple(r) for r in s["refs"] if ok(tuple(r))) for s in d["senses"]]
        all_v = sorted(set().union(*sense_sets)) if sense_sets else []
        for v in all_v:
            support[v] += 1
            cite_draws.setdefault(v, set()).add(di)
        # co-cited: each unordered pair once per draw
        for i in range(len(all_v)):
            for j in range(i + 1, len(all_v)):
                v, x = all_v[i], all_v[j]
                co_cited.setdefault(v, Counter())[x] += 1
                co_cited.setdefault(x, Counter())[v] += 1
        # same-sense: a pair once per draw if it shares ANY sense (a set, so a stutter or a sub-use
        # double-citation cannot inflate it past the draw total)
        same_pairs = set()
        for ss in sense_sets:
            sv = sorted(ss)
            for i in range(len(sv)):
                for j in range(i + 1, len(sv)):
                    same_pairs.add((sv[i], sv[j]))
        for a, b in same_pairs:
            same_sense.setdefault(a, Counter())[b] += 1
            same_sense.setdefault(b, Counter())[a] += 1
    return support, same_sense, co_cited, cite_draws, n


# ══════════════════════════════════════════════════════════════════════════════════════════════
# Report — readable when pasted; the same text is saved next to the JSON.
# ══════════════════════════════════════════════════════════════════════════════════════════════
def fmt_ref(r):
    return f"{r[0]} {int(r[1])}:{int(r[2])}"


def render_report(sid, lemma, translit, prompt_name, ev, draws, valid_books=None):
    """Build the human report (a list of lines). PRESENCE + COMPANY are computed; SIGNIFICANCE is
    left blank for the reader to fill — every word ends with a 'YOUR CALL' line, per the procedure."""
    L = []
    def w(s=""):
        L.append(s)

    def bad_book(r):
        return valid_books is not None and r[0] not in valid_books

    n = len(draws)
    w("=" * 92)
    w(f"{sid}  {LABELS.get(sid, lemma)}   ({translit})    prompt: {prompt_name.upper()}"
      + ("   (the live engine)" if PROMPTS[prompt_name] == B.VERSE_PROMPT
         else "   ** candidate, NOT the live engine **"))
    w(f"  evidence: {ev['total']} occurrences | {ev['renderings']} renderings | "
      f"fed {ev['fed']} ({ev['ot']} OT / {ev['fed'] - ev['ot']} NT)   .   N = {n} draws")
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
        w(f"  !! {len(zero)} draw(s) parsed to 0 senses (format break — inspect raw): {zero}")
    bad = [(i + 1, d["audit"]["real"]) for i, d in enumerate(draws) if d["audit"]["real"]]
    if bad:
        w(f"  !! citation real-miss (possible hallucinated verse) in draw(s): "
          + ", ".join(f"#{i}({r})" for i, r in bad))
    stut = [(i + 1, d["raw_count"], d["count"]) for i, d in enumerate(draws)
            if d.get("raw_count", d["count"]) > d["count"]]
    if stut:
        w(f"  !! v3 STUTTER rate {len(stut)}/{n} — engine repeated a sense under a reworded headline, "
          f"collapsed by verse set (a RISING rate on a word = the engine can't hold a stable sense list "
          f"for it — a finding, not just noise): " + ", ".join(f"draw {i} {a}->{b}" for i, a, b in stut))
    typos = [(i + 1, fmt_ref(r)) for i, d in enumerate(draws)
             for s in d["senses"] for r in s["refs"] if bad_book(r)]
    if typos:
        w("  !! unknown-book refs — dropped from the company math so they can't spawn a phantom verse "
          "(likely model typos; check the draw): "
          + ", ".join(f"{ref} [draw {i}]" for i, ref in typos))

    # 1 — PER-DRAW SENSES: the ground truth
    w("")
    w("  -- PER-DRAW SENSES (headline -- grounding verses) -- THE GROUND TRUTH --")
    for i, d in enumerate(draws, 1):
        extra = f", collapsed from {d['raw_count']}" if d.get("raw_count", d["count"]) > d["count"] else ""
        fb = " — headline fallback" if d.get("split_mode") == "headline" else ""
        w(f"  draw {i:>2}  [{d['count']} senses{extra}{fb}]")
        for j, s in enumerate(d["senses"], 1):
            head = " / ".join(s.get("headlines") or [s.get("headline", "")])
            refs = ", ".join(fmt_ref(r) + ("(?)" if bad_book(r) else "") for r in s["refs"]) \
                or "(no refs cited)"
            w(f"      {j}. {head}")
            w(f"           {refs}")

    # 2 — PER-VERSE SUPPORT + COMPANY: support shows the drop, company tells fold from hole
    support, same_sense, co_cited, cite_draws, _ = verse_company(draws, valid_books)
    worst = max((c for cc in same_sense.values() for c in cc.values()), default=0)
    if worst > n:
        w(f"  !! INTERNAL: a company count hit {worst} > N={n} — a draw still repeats a pair across")
        w(f"     senses (dedup missed a stutter); the numbers below are NOT trustworthy. Fix before use.")
    w("")
    w("  -- PER-VERSE SUPPORT + COMPANY -- support shows a drop; company tells fold from hole --")
    w("     \"with: REF a/b\" = shared a sense in a of the b draws that cite both; a < b means it migrates.")
    w("     (a sub-use can sit at FULL support while a core sense holes below it -- read BOTH columns.)")
    order = sorted(support, key=lambda v: (-support[v], fmt_ref(v)))
    for v in order:
        miss = sorted(set(range(n)) - cite_draws.get(v, set()))
        drop = f"   <-- drops in draws {[m + 1 for m in miss]}" if miss else ""
        sm, cc = same_sense.get(v, Counter()), co_cited.get(v, Counter())
        parts = [f"{fmt_ref(pw)} {a}/{cc.get(pw, a)}" for pw, a in sm.most_common(4)]
        comp = ("  with: " + ", ".join(parts)) if parts else "  (stood alone in its own sense)"
        w(f"      {fmt_ref(v):<13} {support[v]}/{n}{comp}{drop}")

    # 3 — WOBBLES: drive the call off a support-drop, with a fold/hole LEAN from the partners
    drops = [v for v in order if set(range(n)) - cite_draws.get(v, set())]
    w("")
    w("  -- WOBBLES TO JUDGE (apply HOLE-vs-FOLD; full procedure at the top of this file) --")
    if not drops:
        w("  no verse loses support -- every cited meaning holds across all draws. Looks STABLE.")
        w("  (Skim the company column: a once-tight pair that splits -- a/b well below 1 -- is a")
        w("   dissolving sense even without a drop; otherwise migration is just a fold/seam, fine.)")
    else:
        w("  these verses leave some draws -- for each, is the meaning RE-SHELVED under a surviving")
        w("  sense (FOLD, fine) or GONE (HOLE, flag)? The hint below is from the partners; it is a")
        w("  FLAG TO BACK-CHECK against the per-draw lists, NOT a verdict — it over-calls on a small")
        w("  marginal sub-sense that drops as a unit (that looks identical to a hole on the counts):")
        for v in drops:
            miss = sorted(set(range(n)) - cite_draws.get(v, set()))
            sm = same_sense.get(v, Counter())
            lean = ""
            if sm:
                pw = sm.most_common(1)[0][0]
                pmiss = sorted(set(range(n)) - cite_draws.get(pw, set()))
                shared = sorted(set(miss) & set(pmiss))
                if shared:
                    lean = (f" -- its main partner {fmt_ref(pw)} ALSO leaves draws "
                            f"{[m + 1 for m in shared]}: pair drops together -> BACK-CHECK the draws "
                            f"(a whole distinct job gone = hole; a marginal sub-sense folding away = fine)")
                else:
                    lean = (f" -- its main partner {fmt_ref(pw)} stays cited: the meaning is "
                            f"re-shelved -> fold")
            w(f"      {fmt_ref(v):<13} {support[v]}/{n}, absent in {[m + 1 for m in miss]}{lean}")
    w("")
    w(f"  => YOUR CALL for {LABELS.get(sid, sid)}:  STABLE (ship from one draw)  |  "
      f"UNSTABLE-HOLE (name the dropped job)")
    return L


def evidence_summary(conn, sid, budget, has_surface):
    """Gather the SAME deterministic evidence every draw sees. MIRROR INVARIANT (V7): budget +
    slot reservation must match the engine exactly — a floor fed differently from the draw
    certifies the stability of the WRONG inventory (ENGINE_LESSONS #19, at the tool level).
    budget=None → the engine's dynamic_budget curve, same as the build."""
    pred, params = B.abp_filter(conn, sid)
    gset = B.gloss_set(conn, pred, params)
    occs = B.occurrences(conn, pred, params)
    if budget is None:
        budget = B.dynamic_budget(len(occs))
    sample = B.select_spread(occs, budget)
    sample = B.reserve_collocation_slots(conn, sid, occs, sample)
    ctx = B.fetch_context(conn, sample, has_surface)
    lemma, translit = B.lex_head(conn, sid)
    ot = sum(1 for c in ctx if c[0] not in B.NT_BOOKS)
    return {"lemma": lemma, "translit": translit, "gset": gset, "ctx": ctx,
            "pmap": B.phrase_map(occs),
            "total": len(occs), "renderings": len(gset), "fed": len(ctx), "ot": ot}


def save_run(save_dir, sid, prompt_name, ev, draws, report_lines, valid_books=None):
    """Persist the whole run so the review needs the model ONCE: re-read free with --from-json,
    and Step 3 can lift a reviewed draw's raw to ship. JSON holds raw + parsed senses per draw, plus
    the valid-book set so a --from-json re-read applies the same typo filter with no db."""
    ts = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).strftime("%Y%m%d-%H%M%S")
    base = os.path.join(os.path.expanduser(save_dir), f"agreement_{sid}_{prompt_name}_{ts}")
    payload = {
        "strongs": sid, "lemma": ev["lemma"], "translit": ev["translit"],
        "prompt": prompt_name, "prompt_sha1": hashlib.sha1(PROMPTS[prompt_name].encode()).hexdigest()[:12],
        "runs": len(draws), "valid_books": sorted(valid_books) if valid_books else None,
        "evidence": {k: ev[k] for k in ("total", "renderings", "fed", "ot")},
        "draws": [{"raw": d["raw"], "count": d["count"], "raw_count": d.get("raw_count", d["count"]),
                   "split_mode": d.get("split_mode", ""),
                   "audit": d["audit"],
                   "senses": [{"headlines": s.get("headlines") or [s.get("headline", "")],
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
    """Re-read a saved run and re-render the report — FREE, no model. Re-applies the CURRENT splitter
    rules (the within-draw stutter collapse) to the stored draws, so an OLD run saved before a fix is
    re-analysed correctly without paying for generation again. Handles both the new senses shape
    ({headlines:[...]}) and the old one ({headline:...})."""
    with open(os.path.expanduser(path), encoding="utf-8") as f:
        p = json.load(f)
    def to_tuple(s):
        m = re.match(r'(\S+)\s+(\d+):(\d+)', s)
        return (m.group(1), int(m.group(2)), int(m.group(3))) if m else (s, 0, 0)
    draws = []
    for d in p["draws"]:
        loaded = [{"headlines": s.get("headlines") or ([s["headline"]] if s.get("headline") else []),
                   "refs": [to_tuple(x) for x in s["refs"]]} for s in d["senses"]]
        senses, nb, na = merge_near_dup_senses(loaded)
        draws.append({"raw": d.get("raw", ""), "count": na, "raw_count": nb,
                      "split_mode": d.get("split_mode", ""),
                      "audit": d["audit"], "senses": senses})
    ev = {"lemma": p["lemma"], "translit": p["translit"], "renderings": p["evidence"]["renderings"],
          "total": p["evidence"]["total"], "fed": p["evidence"]["fed"], "ot": p["evidence"]["ot"]}
    vb = set(p["valid_books"]) if p.get("valid_books") else None
    print("\n".join(render_report(p["strongs"], p["lemma"], p["translit"], p["prompt"], ev, draws, vb)))


def main():
    ap = argparse.ArgumentParser(description="Agreement reviewer for the Lexica dictionary engine.")
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"))
    ap.add_argument("--word", help="one G-number, e.g. G5590 (default: the six pilot words)")
    ap.add_argument("--prompt", choices=list(PROMPTS), default="v8",
                    help="which engine to review: v8 (frozen copy of the LIVE engine, default; "
                         "promoted 2026-07-10), v7 (previous engine, historical), or live "
                         "(build's VERSE_PROMPT)")
    ap.add_argument("--runs", type=int, default=10, help="draws per word (10 reproduces the canary)")
    ap.add_argument("--budget", type=int, default=None,
                    help="override; default mirrors the engine's dynamic_budget curve")
    ap.add_argument("--save-dir", default="~/bible-db", help="where the per-run JSON/txt land")
    ap.add_argument("--no-save", action="store_true", help="print only, do not write the run files")
    ap.add_argument("--from-json", help="re-render a saved run, FREE (no model) — pass its .json")
    args = ap.parse_args()

    if args.from_json:
        from_json(args.from_json)
        return

    _check_prompt_sync()
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
    valid_books = {row["book"] for row in conn.execute("SELECT DISTINCT book FROM verses")}

    import anthropic
    client = anthropic.Anthropic(api_key=B.get_key())

    stutter_rates = []   # (label, n_stuttered_draws, runs) — banked + summarised across the set
    for sid in targets:
        ev = evidence_summary(conn, sid, args.budget, has_surface)
        if not ev["ctx"]:
            print(f"\n{sid}: no occurrences — skip.")
            continue
        print(f"\n{sid} {LABELS.get(sid, '')}: drawing {args.runs}x …", flush=True)
        draws = []
        for k in range(args.runs):
            raw = draw_once(client, system, sid, ev["translit"], ev["gset"], ev["ctx"], ev.get("pmap"))
            draws.append(parse_draw(conn, sid, raw))
            fb = " — headline fallback" if draws[-1].get("split_mode") == "headline" else ""
            print(f"   draw {k + 1}/{args.runs}: {draws[-1]['count']} senses{fb}", flush=True)
        report = render_report(sid, ev["lemma"], ev["translit"], args.prompt, ev, draws, valid_books)
        print("\n".join(report))
        nst = sum(1 for d in draws if d.get("raw_count", d["count"]) > d["count"])
        stutter_rates.append((LABELS.get(sid, sid), nst, len(draws)))
        if not args.no_save:
            base = save_run(args.save_dir, sid, args.prompt, ev, draws, report, valid_books)
            print(f"\n  saved: {base}.json  (+ .txt)")

    if len(stutter_rates) > 1:
        print("\n" + "=" * 92)
        print("STUTTER RATE across the set (a word that stutters MORE = the engine struggles to hold a")
        print("stable sense list for it — a tail signal worth reading, not just dedupe noise):")
        for label, nst, runs in sorted(stutter_rates, key=lambda r: -r[1] / r[2]):
            print(f"   {label:10} {nst}/{runs}")

    conn.close()


if __name__ == "__main__":
    main()
