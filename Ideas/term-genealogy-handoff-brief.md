# Term Genealogy — handoff brief for spec

**Status:** idea stage. Proposed as a *distinct* Lexica card type (fourth, alongside word / structural / argument-graph). Not scheduled, not a batch prereq. This brief is the seed; the spec is the deliverable.

**For:** whoever builds the spec doc. Assume the reader knows the Lexica architecture but is cold to this specific idea.

---

## 1. The idea

A module that takes a **received theological abstraction** — "Trinity," "monotheism," "incarnation," "omniscience," etc. — and excavates it downward through layers: the modern label, the moment its meaning diverged from attested usage, and the actual biblical lexeme(s) it claims to summarize. The output shows the *gap* between what the text attests and what the label now silently asserts, without pronouncing a verdict on whether the label is legitimate.

It is the label-audit analog of the definition engine: audit the received *term* with the same rigor Lexica already applies to a received *gloss*.

## 2. Why it's a distinct type (the load-bearing insight)

Every existing Lexica card type is anchored to a lexeme with attested occurrences:

- **word card** — a lexeme and its verse-grounded senses
- **structural card** — a closed-class lemma
- **argument graph** — a proposition with positions reasoning to conclusions over a shared claim pool

These terms are **headword-less**. "Trinity," "monotheism," "incarnation" have *zero* biblical occurrences as terms. They're abstractions laid over *constellations* of lexemes. That's not a defect to route around — it *is* the subject. The module's whole job is to connect a headword-less modern abstraction *downward* to the scattered real lexemes it claims to compress, and expose the gap.

That's why it can't be a word card (no headword) and isn't quite an argument graph (it models a word's *descent through time*, not sides reasoning to a conclusion). The reader's question is different: an argument graph answers "how do the sides reason?"; this answers "what is this word smuggling?"

## 3. Anatomy — four layers, each with a gate/contract

Read top-down as an excavation (surface = youngest, bedrock = oldest — which is also chronologically correct):

1. **Surface term.** Headword-less metadata: coiner, year, lag-from-apostolic. Near-mechanical; could be engine-drafted. (Trinity → Tertullian, ~200, +170yr. Monotheism → Henry More, 1660s, +1600yr.)

2. **Substrate (bedrock).** Which real lexemes does the label claim to summarize? These are **read-only pointers into existing word cards / the draw cache** — *not* re-authored. This is the most important build decision: the substrate is a join, so the genealogy can never silently drift from certified lexeme data. If a source card gets a correction, the genealogy inherits it. Same discipline as "reviewed drafts ship verbatim."

3. **Fault line.** The datable moment attested meaning and technical meaning slip apart. This is the one genuinely *new authored* layer, and it is a **citeable historical claim** — it routes through the existing citation gate exactly like a definition. No source → fails loud. (Trinity's fault: Nicaea 325 lists *hypostasis*/*ousia* as synonyms → Cappadocians pry them into a general/particular pair in the 370s–380s.)

4. **Ledger (fairness rail, not a stratum).** The "absent vocabulary ≠ absent reality" layer. Holds what the received term is *legitimately* trying to capture (for Trinity: the worship directed at Christ, the Spirit as an agent who can be lied to, the unqualified oneness texts). Structurally identical to a CONTESTED-list entry or an argument-graph overlay: the fork the module **refuses to resolve**. Without this rail the module is a debunking machine; with it, it's an audit.

## 4. Integration surface (constraints the spec must honor)

- **Draw-cache join** for the substrate layer — define the join contract (what a genealogy entry stores vs. what it dereferences at render).
- **Citation gate** — fault-line assertions inherit the definition engine's Strong's-tag-style loud-fail citation discipline.
- **CONTESTED machinery** — the ledger reuses the fairness-gate / fork-surfacing apparatus rather than inventing a parallel one.
- **One-pool/many-overlays** — the substrate is a shared lexeme pool; different terms draw different subsets, same as the argument-graph architecture in study.db. Worth checking whether it can share that pool.
- **argument-graph-review five checks** — the grounding-and-fairness checks likely transplant almost unchanged onto the fault-line and ledger layers.

## 5. Methodology constraints (non-negotiable — Berean stance)

- Text speaks first. The bedrock (attested lexeme) is the ground; the label is the thing on trial.
- Surface the fork; do not resolve it. The module *audits*, it does not *rule*.
- Audit the critique with the same rigor as the inherited term — the ledger is what enforces this. Guard against the etymological fallacy in reverse ("the word is late, therefore the idea is false"). Late vocabulary ≠ absent reality.
- No auto-asserted fault lines. A plausible-but-wrong divergence date is exactly the failure mode; the fault line needs a human hand and a citation.

## 6. Worked example (the concrete instance to build the schema against)

**Term:** Trinity (formula: *mia ousia, treis hypostaseis*)

- **Surface:** headword-less. Formula crystallized by the Cappadocians, 370s–380s; term *trinitas* coined by Tertullian ~200.
- **Substrate (bedrock, from word cards):**
  - ὑπόστασις — attested: support / foundation / confidence. 2 Cor 9:4; Heb 11:1; Heb 1:3 (closest to technical). Never "person."
  - οὐσία — attested: estate / property. Luke 15:12–13 (prodigal). Never "essence."
- **Fault line:** at Nicaea (325) the two words are listed *as equivalents* ("of a different hypostasis or ousia"). The Cappadocians then stipulatively split them: *ousia* = the shared "what," *hypostasis* = the particular "who." Divergence is engineered, ~340–360 yrs post-apostolic. (Secondary fault: the Latin calque *hypostasis → substantia* broke the distinction in translation, generating the tritheism/modalism cross-accusations East↔West.)
- **Ledger:** the formula is trying to hold real data — worship directed at Christ, the Spirit as personal agent (Acts 5:3–4), the unqualified oneness texts. The module records this and declines to adjudicate.

## 7. Open questions for the spec to resolve

- **Where it lives.** New top-level study type with its own entry point, or slotted under the Study tab beside argument graphs (shared substrate pool)? Current lean: distinct type + own entry point, because the reader's question is different (see §2).
- **Generated vs. authored.** Surface metadata and the substrate join are mechanical (engine-safe). Fault lines are historical-theological judgment calls (human + citation + spot-check protocol like the batch build). Spec should draw this line explicitly and specify the spot-check protocol.
- **Render shape.** The stratigraphy stack (surface → fault → bedrock) reads well for one term. Does it hold for terms with many substrate lexemes, or does it need an overview/detail split?

## 8. What the spec should deliver

1. The data model for a genealogy entry (fields, the draw-cache join contract, how the ledger references CONTESTED entries).
2. The four layers formalized with their gates.
3. The generated-vs-authored boundary + spot-check protocol for fault lines.
4. Placement decision (§7) with rationale.
5. A **second fully-worked example** (incarnation or monotheism) to prove the template generalizes past the one term it was reverse-engineered from. This is the real test of whether the module is a genuine type or just fits this one case.
