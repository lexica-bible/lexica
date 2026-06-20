# Lexica — Study/AI redesign (design handoff)

> **⚠️ TO ANY TOOL OR AGENT READING THIS REPO — DO NOT AUDIT THE FILES IN `design/` AS THE LIVE APP.**
> Everything under `design/` is **throwaway mockups** (standalone mini React apps). The **real, running
> app is `static/src/*.jsx` → compiled to `static/app.js`** (Flask serves that). `design/library.jsx`,
> `design/word-study.jsx`, etc. are NOT production code — their nav, routing, and behavior are prototype
> stand-ins and will NOT match the real app. Any "the app does X wrong" finding based on these files is
> wrong by construction. Audit `static/src/` for behavior; use `design/` only for the **visual target**
> (look, color tokens, layout). See the root `CLAUDE.md` for how the real frontend is built.

Mockups for the **Word study** + **Ask the corpus** redesign, exported from the Claude design tool
(2026-06-19). These are STANDALONE prototypes (their own mini React app + CSS). The real app is
`static/src/*.jsx` compiled to `static/app.js` — so "building this" means re-expressing these designs
with the real app's components, CSS variables, and conventions, NOT dropping these files in.

Direction + the full decision trail (and the alternatives we rejected) live in memory
`project_ai_search_redesign`.

## The shape (agreed)
- **Word study** = a structured, AI-free dashboard. 3 panels: distribution-by-book LEFT, verse
  occurrences CENTER, word card RIGHT. Search box is word-lookup ONLY. One quiet
  "✦ Ask AI about <word> →" link in the word card hero hands off to the Ask tab.
- **Ask the corpus** = the single AI home. Synthesis prose + clickable inline verse/lemma refs +
  a lemma chip row + a few verse-evidence cards + follow-up box. Recent-questions rail on the left.
  When opened from a Word study link it seeds word-scoped suggestions ("Asking about <lemma>").
- AI accent color = **light blue** (the ✦ mark, the Ask-AI link, the "Asking about" pill). Intentional,
  used everywhere AI surfaces. Everything else stays on the app palette.

## Mirror the Library
Default: keep the Library's three-zone division (left nav / center reading / right detail rail) so we
reuse its CSS + breakpoint + muscle memory. We are NOT locked to it — panels can resize, a 4th panel or
a toolbar is allowed — but deviating from the Library structure means new code + a new thing to learn,
so do it only for a concrete reason, and **reconsult the design tool before improvising a new layout in
code.**

## Build-time gotchas — conform to the real app
1. **Cognates / "related lemmas" data is not all there.** The mockup assumes a `related` list per word.
   Reality (checked in `scripts/load_lexicon.py` + `views_lsj.py`): `lexicon.derivation` EXISTS (real
   Strong's etymology). A same-ROOT family (parent/children/siblings) is BUILDABLE by following the
   derivation field both ways. But MEANING-based relatives (e.g. ψυχή as "related" to πνεῦμα) are NOT in
   any data — those need AI or hand-curation. Don't ship that section as-shown until it has a real source.
2. **Verse-card cap (~2-3 anchors) must live in the AI backend, not just CSS.** The mockup renders
   whatever verses it's handed. The "quote full text only for the few verses the argument leans on,
   reference the rest by link" rule is a SYSTEM-PROMPT + serialization rule on the real endpoint
   (user's hard ask: don't spam verse results). Matters most on mobile.
3. **Breakpoint = 1100, not the mockup's 1040/760/980.** The app has exactly two states (desktop ≥1100,
   mobile <1100 — see CLAUDE.md "Responsive Breakpoints"). Reconcile the mockup's panel-collapse logic
   to that. Reuse the Library's `has-detail` compacting + bottom-sheet pattern for the word card on
   mobile rather than the mockup's standalone scrims.

## Other conformance notes
- Colors via CSS vars (`--ctl-bg`/`--ctl-on`/`--ink`/`--accent`/`--paper`/`--rule`), never hardcoded —
  themes ride `data-theme`. No brown (solid `--gold` reads brown). Reader/body text = `--f-serif`
  (Source Serif 4). Gold only for highlighted target words.
- Reuse existing endpoints where possible: `/api/lexicon/*` (profile/verses/distribution), the AI
  search pipeline in `ai.py`, the LSJ/derivation join. The Ask-tab answer reuses the search synthesis
  pattern (see memory `project_ai_search_architecture`, `project_ai_cache_unify`).
- Word study (Lexicon + Search) is ALREADY merged into one tab in the live app — memory
  `project_word_study_merge`. This redesign is the visual layer over that merge.

## Files
- `word-study.jsx` / `.css`, `word-study-data.jsx` — the 3-panel dashboard prototype.
- `ask-corpus.jsx` / `.css`, `ask-corpus-data.jsx` — the AI tab prototype.
- `library*.{jsx,css}`, `app.jsx`, `styles.css` — supporting/shared mockup chrome.
- `*.html` — open these to view each prototype. `screenshots/`, `uploads/` — reference renders.
