# Lexica

A Greek and Hebrew Bible word study app built on the **Apostolic Bible Polyglot (ABP)** interlinear. Designed for serious study without requiring prior knowledge of Greek or Hebrew.

**Live app:** [appssanding720.pythonanywhere.com](https://appssanding720.pythonanywhere.com)

---

## What You Can Do

- **Read** any book of the Bible in ABP, KJV, or side-by-side parallel — with optional Greek word order, interlinear display, and Strong's number badges
- **Search** by English gloss, Greek word (with or without accents), transliteration, or Strong's number — and see every occurrence across the corpus with gloss groupings and OT/NT filtering
- **Ask** natural language questions ("Where does hesed appear in the Psalms?") and get AI-generated SQL queries against the full interlinear database, with Hebrew and Greek citation chips
- **Explore** cross-references from Torrey's Treasury of Scripture Knowledge — AI-curated to the 8–10 most relevant passages per verse, with a thematic synthesis anchored in ABP vocabulary
- **Look up** any word in the Liddell-Scott-Jones Greek lexicon or Brown-Driver-Briggs Hebrew lexicon, with an AI-generated contextual summary

---

![Search results showing πνεῦμα with LSJ sidebar and gloss groupings](assets/screenshot-search.png)
*Lexicon search with LSJ definition and occurrence groupings*

![AI synthesis with Hebrew and Greek citation chips](assets/screenshot-ai-search.png)
*AI natural language search reasoning across Greek and Hebrew*

![Library reading view with TSK cross-reference panel](assets/screenshot-cross-reference.png)
*Cross-reference panel with AI thematic synthesis*

![Parallel interlinear view with Strong's badges](assets/screenshot-parallel.png)
*ABP and KJV parallel interlinear with Strong's numbers*

---

## Stack

- **Backend:** Python / Flask, SQLite
- **Frontend:** React 18 + Babel standalone (no build step)
- **AI:** Claude Haiku — AI search, LSJ summaries, TSK curation and synthesis
- **Hosting:** PythonAnywhere

## Lexicons & Data

| Source | Coverage |
|---|---|
| Apostolic Bible Polyglot | Greek interlinear, OT + NT |
| Liddell-Scott-Jones (LSJ) | Classical Greek lexicon |
| Brown-Driver-Briggs (BDB) | Hebrew lexicon |
| Strong's | G/H number definitions |
| Torrey's TSK | 386,518 cross-reference pairs |
| KJV | 31,102 verses with word-level Strong's tagging |
