# TICKET — Synthesis prose writes Greek as bare transliteration, not Greek script

Status: OPEN — located 2026-07-16, DO NOT BUILD until reviewed. Known-bad example:
the Gen 1:1 arche thread — synthesis body says "arche", "archegos", "thea" (bare
transliteration, no Greek script, no accents) while the words-in-scope chips on the
same answer correctly render ἀρχή / θεός (accented Greek script from the DB).

## Diagnosis (JP + screenshot, 2026-07-16)
The defect is the AI SYNTHESIS PATH, not storage: the DB carries fully accented
lemmas (the chips prove it, rendered by Strong's number). The synthesis model emits
transliteration in its prose and the frontend displays it verbatim. Head-word lesson
applies: the value is made at generation time — fixing display alone can't restore
what the model never wrote.

## Preferred direction (JP)
Render the Greek/Hebrew form FROM THE DB, keyed on the Strong's number the synthesis
already cites, rather than trusting model-emitted transliteration — the same
provenance philosophy as everywhere else: display values come from data, not
generation. Candidate shape: the synthesis already writes inline refs (G746); the
prose renderer already resolves those to links — extend it to show the DB lemma
(script + accents) alongside/instead of the model's transliteration. Alternative
(prompt the model to emit Greek script) is WEAKER — same unenforced-instruction
pattern as the highlight ticket's Door 1, and a model-typo'd Greek word would be
worse than a transliteration.

## Cautions before building
- AI-synthesis-quality rules apply: any prompt change stales caches per the cache
  fingerprint design, and prompt edits must not regress the model (memory
  `project_ai_synthesis_quality`). The render-from-DB direction avoids prompt
  changes entirely — another point in its favor.
- Scope: ALL corpus-reply surfaces (synthesis body, follow-ups, LSJ blurbs?) — sweep
  where model-emitted lexemes display, don't fix one spot (grep before sizing).
- Hebrew side: same question for transliterated Hebrew in prose; the DB carries
  pointed Hebrew.

## Acceptance sketch
The Gen 1:1 thread (cached or re-drawn) shows ἀρχή with accents wherever the prose
names the word; the transliteration may remain as the parenthetical, per design
choice at build time.
