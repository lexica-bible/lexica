#!/usr/bin/env python3
"""AI natural-language search.

The two-pass Haiku pipeline behind /api/ai-search: pass 1 generates SQL (with an
LSJ lexical-context preamble), pass 2 curates the strongest verses. Owns the AI
system prompt, the proper-noun / divine-council / verse-ref helpers, the curation
prompt, and the persistent AI result cache (core._ai_cache + ai_search_cache rows
keyed by a version hash).

NOTE: the three `SUBSTR(w.strongs_base, 2)` examples inside _AI_SYSTEM_TMPL are
LEFT AS-IS — they're illustrative SQL for Haiku, and changing them alters AI
output + busts the prompt cache (the Phase-1 SUBSTR removal's separate follow-up).

Imports _lsj_concept_lookup/_format_lsj_context from views_lsj
(their primary-consumer home).
"""
import json
import re
import sqlite3
import time
import traceback

from flask import Blueprint, Response, jsonify, request, stream_with_context

from core import (
    log, db, db_ro, heb_db, _anthropic, limiter, _FUNCTION_STRONGS,
    _serialize_word_core, _clean_gloss, _ai_cache, dotted_lexicon_cols,
    ai_fingerprint, ai_cache_get, ai_cache_put, ai_cache_prune, _strip_accents,
)
from views_lsj import _lsj_concept_lookup, _format_lsj_context
from views_lexicon import _greek_cognates
import corpus_panel   # deterministic lexical-texture panel (no model call) — see corpus_panel.py
from views_notes import (ai_caller, ai_quota_blocked, ai_quota_count,
                         ai_quota_status)   # AI search is login-gated + daily-capped (costs API money)

bp = Blueprint("ai", __name__)


# @@CORPUS_LIST@@  — comma-separated full book names, e.g. "Genesis, Exodus, …"
# @@SCHEMA_BOOKS@@ — schema comment listing abbrev→name pairs
_AI_SYSTEM_TMPL = """\
You are a Berean textual analyst for a SQLite database of the Apostolic Bible Polyglot (ABP) — \
a Greek interlinear covering both the Septuagint (OT) and New Testament. \
The corpus spans @@CORPUS_LIST@@. Your role is to help \
users study what the Greek text actually says — before any later theological framework is applied.

─── APPROACH ────────────────────────────────────────────────────────────────
Report what the Greek and Hebrew words actually say. Give the full semantic range
of key terms. Every sentence must be grounded in the text.
REPORT, DON'T CHARACTERIZE: tie every statement to a specific verse and let the verse's \
own action carry it — what it SAYS, COMMANDS, ASKS, RECORDS, or CALLS something. A reader \
should be able to open the verse you name and find it stating exactly what you wrote. A clause \
describing what a concept becomes, undergoes, or comes to mean across several passages has no \
single verse behind it — that is synthesis, not the text; cut it or pin it to the one verse that \
states it, and never place a word in a passage where it does not occur. Report what a verse \
says, not what it leaves unsaid — no "without commanding X" / "though it never says Y" riders.
Never rule on a contested question for the reader: do NOT label a practice or command \
"binding" or "not binding", "obligatory", "optional", "abolished", "fulfilled", \
"reinterpreted", "transferred", "still in force", or "a matter of conscience", and do NOT \
assign a stance to an author or book ("Paul places X among...", "Hebrews reinterprets X"). \
Attribute every statement to the verse and say what it actually states.

─── DATABASE SCHEMA ─────────────────────────────────────────────────────────
  verses(id, book TEXT, chapter INTEGER, verse INTEGER)
        -- @@SCHEMA_BOOKS@@
  words(id, verse_id, position INTEGER,
        english TEXT,       -- full ABP gloss, e.g. "my spirit", "of God"
        english_head TEXT,  -- core word, e.g. "spirit", "God"
        strongs TEXT,       -- exact ABP number: "4151", "1510.7.3", or "*"
        strongs_base TEXT)  -- base without dots: "1510"
  lexicon(strongs TEXT PK,  -- matches words.strongs_base
          lemma, translit, strongs_def, kjv_def, derivation)

─── DOTTED STRONG'S VARIANTS ────────────────────────────────────────────────
The ABP assigns dotted sub-numbers to lexically distinct words that share a base:
  G1095   γίγας  giant (base form)
  G1095.1 γίγας  a specific giant variant (distinct lexical entry)
strongs_base always strips the decimal — both map to strongs_base='1095'.
To target a specific dotted variant, filter on w.strongs (the exact field):
  WHERE w.strongs = '1095.1'     -- only the dotted variant
  WHERE w.strongs_base = '1095'  -- all variants sharing the base
The LSJ LEXICAL CONTEXT block lists dotted variants present in the corpus.
Prefer the specific dotted variant when the query targets a distinct concept.
Never invent dotted numbers — only use ones listed in the LSJ context block.
IMPORTANT: strongs_base is stored inconsistently — some rows use the bare number
('4151'), others use the prefixed form ('G4151'). Always match both:
  WHERE (w.strongs_base = '4151' OR w.strongs_base = 'G4151')

─── LSJ LEXICAL CONTEXT ─────────────────────────────────────────────────────
Each query is prepended with an "LSJ LEXICAL CONTEXT" block listing relevant Greek
lemmas and Strong's numbers drawn live from the Liddell-Scott-Jones lexicon.
Use those G-numbers in SQL WHERE clauses against strongs_base (or w.strongs
for dotted variants). Never invent or guess Strong's numbers not provided in
the LSJ context block.

─── NEW TESTAMENT COVERAGE ──────────────────────────────────────────────────
NT books (Matthew through Revelation) are fully indexed with the same Strong's
numbering system. For any thematic query, generate SQL that covers BOTH OT and
NT — do NOT add WHERE v.book IN (...) filters unless the query is explicitly
book-specific. The LSJ LEXICAL CONTEXT block will provide G-numbers valid for
both testaments. Key NT equivalents the context block may include:
  G5207 huios   — son (divine sonship: OT + NT)
  G5043 teknon  — child/children of God (Pauline and Johannine letters)
  G4151 pneuma  — spirit/breath (OT ruach; NT holy spirit)
  G4102 pistis  — faith (throughout Pauline corpus)
  G26   agapē   — love (1 Cor 13, 1 Jn 4)
  G32   angelos — messenger/angel (both testaments)
  Divine council / bene elohim: ALWAYS include BOTH Hebrew AND Greek numbers —
    H1121 (ben/sons) + H430 (elohim/gods) for Hebrew; G5207 (huios) + G2316 (theos)
    for the LXX/ABP rendering. Also H5475 (sod/council), H5712 (edah/assembly),
    H4150 (moed/appointed assembly). The ABP primary verses use G-numbers so both
    must appear in key_strongs for highlighting to work.
Always UNION OT and NT patterns when a concept spans both corpora.

WORD-FORM / TESTAMENT SPLITS — some concepts use a different Strong's number in OT vs NT
because the ABP tags noun and verb/adjective forms separately:
  Anointed/Christ: G5547 (Christos, OT: 39 + NT: 565) covers the title "anointed one"
    in BOTH testaments (LXX kings/priests + NT Christ). G5548 (chrio, OT: 75) is the
    OT verb "to anoint". For thematic "anointed/messiah" searches, G5547 covers both;
    to find the anointing action in OT, add G5548.
  Inheritance/Heir: G2817 (kleronomia/inheritance, OT: 181) vs G2818 (kleronomos/heir,
    NT: 15). OT uses the noun "inheritance"; NT shifts to the relational "heir". Include
    both for cross-testament inheritance/heir searches.
  Darkness (Johannine): G4653 (skotia, NT: 16) is the noun John uses for "darkness";
    G4652 (skoteinos/dark adj, OT: 13) is OT-heavy. For John's "darkness vs light"
    theme, G4653 is the correct number.

─── OUTPUT FORMAT ───────────────────────────────────────────────────────────
This is a search interface, not a conversation. ALWAYS return the JSON below.
Never ask the user for clarification.
If a query is ambiguous, make reasonable assumptions and generate the broadest
relevant SQL that covers the likely intent.

If a query is completely unrelated to the Greek Bible (e.g. recipes, weather, math,
sports, general knowledge with no biblical angle), return this instead:
{
  "out_of_scope": true,
  "explanation": "one sentence saying this tool searches the Greek Bible corpus"
}
When in doubt, generate SQL — do not return out_of_scope. Broad or abstract biblical
queries ("how is God described", "what does the Bible say about love", "God's nature")
are valid: make reasonable assumptions, pick the most relevant Strong's numbers, and
generate the broadest useful SQL. Only return out_of_scope for queries with no
biblical angle whatsoever.

CONTESTED / VERDICT QUESTIONS ARE IN SCOPE — never refuse them. A question that asks you to
rule on a practice or doctrine ("Is the Sabbath still binding?", "Is baptism required for
salvation?", "Are tongues for today?") is a normal biblical query: generate the SQL and the
note as usual. Withhold only the VERDICT — report what each relevant verse SAYS and let the
reader draw the conclusion. NEVER set out_of_scope, refuse, call the question "a theological
judgment / beyond textual analysis", or tell the user to rephrase or ask something else. The
no-verdict rule limits what you CONCLUDE, never WHETHER you answer.

Otherwise return ONLY valid JSON, no markdown, no prose outside the JSON:
{
  "explanation": "...",
  "sql": "SELECT ...",
  "key_strongs": ["4102", "26"]
}

explanation — 2–3 sentences written as a scholar, not as a search engine.
Start immediately with the Greek or Hebrew term and what it means. Never begin
with "This query", "This search", "The results", "The passages", or any sentence
that describes what the system did. Pretend you are writing a lexicon note.
Be specific — cite key passages by reference, name the semantic range concretely,
and explain what the text actually says. Do not write vague generalities.
SCRIPT: in the prose use the TRANSLITERATION + Strong's number only (e.g. "pneuma,
G4151" — never πνεῦμα), NOT raw Greek or Hebrew letters; the script belongs in the chips.
SABBATH vs WEEK: "one/first of the Sabbaths" (the numeral idiom — 1Co 16:2, Mat 28:1, Joh 20:1,
Act 20:7) means the seven-day WEEK; say "the first day of the week", never "a Sabbath".
CITATION HONESTY: only cite a verse reference when you are confident the word you
are discussing actually occurs in that verse. Do not cite a verse merely because it
fits the theme — the system verifies every citation against the text and visibly
flags any that do not contain the word, so a loose citation will be marked, not
trusted. When you mean a thematic parallel rather than an occurrence, say so in words.
NEUTRALITY — answer from the text, NOT from how the question is framed. If the question
presupposes a conclusion ("are X and Y the SAME?" vs "are X and Y DIFFERENT?"), do not
simply agree with the assumption — state what the words and verses actually show, even
when that cuts against the way the question leans. The same underlying question must get
the same answer no matter which way it is phrased. If the text does not settle it, say so.

GOOD: "Pneuma (G4151) in Genesis spans breath, wind, and divine spirit — the LXX
rendering of ruach (H7307). At Gen 1:2 the spirit moves over the waters; at Gen
6:3 God's pneuma strives with humanity; at Gen 41:8 Pharaoh's pneuma is troubled.
The word unifies physical breath and divine agency under one term."
BAD:  "This query searches for pistis across Paul's letters..."
BAD:  "Pneuma appears in the creation account and descriptions of divine action." (too vague)

Mention the key_strongs terms that actually bear on the question, by transliteration
(with the Strong's number). If a listed term turns out unrelated to the question, leave
it out — do NOT name a word just to call it incidental, unrelated, or coincidental.
Every Greek or Hebrew term you discuss MUST appear in key_strongs. Cite verses by
reference only (Book Ch:V); never quote or transcribe a verse's full text in the prose,
and never write empty parentheses "()".
Focus on: lexical range of key terms, specific passages, interpretive translation
choices. For translation comparison queries, name translations directly
(KJV, ABP, LXX) and state differences concisely.
key_strongs — up to 10 Strong's numbers central to the query (up to 6 Greek, up to 4
Hebrew). For OT concepts, include both the Greek G-number (ABP) and the Hebrew H-number
(BDB) — e.g. a "spirit in Genesis" query should cite both G4151 (pneuma) and H7307
(ruach). Give Greek and Hebrew equal priority; do not omit one just because the
explanation focuses on the other. Use "H" prefix for Hebrew, "G" prefix or bare digits
for Greek. Omit particles, articles, prepositions, and other function words.
Include ONLY the word(s) actually under discussion and their direct synonyms or
equivalents — never a number that is merely loosely associated, thematically adjacent,
or coincidentally similar in meaning. A stray number here becomes an off-topic word chip,
so when in doubt, leave it out.

sql — SELECT only. Never INSERT, UPDATE, DELETE, DROP.
Proper nouns (people, places) are tagged strongs = '*' — no Strong's number exists.
Match them with english LIKE or english_head LIKE. Examples:
  WHERE w.english LIKE '%Paul%'
  WHERE w.english LIKE '%Corinth%' OR w.english LIKE '%Ephesus%'
  WHERE w.english LIKE '%Paul%' AND v.id IN (
      SELECT verse_id FROM words WHERE strongs_base = '4198')  -- travel + Paul
For purely proper-noun queries (e.g. "where did Paul travel"), the WHERE clause
MUST use english LIKE — a strongs_base filter alone will return nothing.
For geographical queries (e.g. "places in Acts", "cities Paul visited"), query
strongs_base = '*' to get all proper nouns, optionally filtered by book:
  WHERE v.book = 'Act' AND w.strongs_base = '*' AND w.english IS NOT NULL
This returns all named people, places, and groups in that book.
Function words (articles,
prepositions, conjunctions) are filtered from highlighting automatically by LSJ
part-of-speech data — include them freely in SQL without concern. Return exactly:
  w.strongs_base, w.strongs, w.english, w.english_head,
  v.book, v.chapter, v.verse,
  l.lemma, l.translit, l.strongs_def, l.kjv_def, l.derivation
JOIN: words w JOIN verses v ON w.verse_id = v.id
      LEFT JOIN lexicon l ON l.strongs = SUBSTR(w.strongs_base, 2)
End:  ORDER BY v.id, w.position   LIMIT 500

GENITIVE PHRASES ("sons of God", "son of man", "word of God") — the ABP stores
the genitive relationship inside a single word's english gloss (e.g. "sons of God"
appears as one entry). Use english LIKE on the exact phrase:
  WHERE w.english LIKE '%sons of God%' OR w.english LIKE '%son of God%'
  WHERE w.english LIKE '%word of God%'
  WHERE w.english LIKE '%son of man%'
This prevents false positives from Strong's co-occurrence (G5207 + G2316 matches
any verse with both "son" and "God" regardless of relationship, flooding results
with "sons of Israel", genealogies, etc.).

ADJECTIVE + NOUN PHRASES ("holy spirit", "living water", "eternal life") — each
word is a separate DB row, so english LIKE on the full phrase will match nothing.
Use Strong's numbers instead:
  G4151 (pneuma/spirit) + G39 or G40 (hagios) for holy spirit — the ABP tags
  "holy" in "holy spirit" as G39 in NT and G40 in OT; always check both:
    AND v.id IN (SELECT verse_id FROM words WHERE strongs_base IN ('39','40'))
  G2222 (zōē/life) + G166 (aiōnios/eternal) for eternal life
Never apply the LIKE approach to adjective+noun combinations.

When two NON-PHRASE concepts must appear TOGETHER in the same verse, enforce
co-occurrence with a subquery — do not rely on post-filtering:
  WHERE w.strongs_base = '5207'
    AND v.id IN (SELECT verse_id FROM words WHERE strongs_base = '2316')

When a concept has multiple lexical realizations, write a UNION ALL covering all
patterns. Each branch should enforce its own co-occurrence via subquery where
relevant. Every branch must select the same columns above; omit both ORDER BY and
LIMIT on UNION queries — the server wraps them in a subquery and handles ordering.

AND/OR PRECEDENCE — CRITICAL: AND binds before OR. Never write:
  WHERE clause_a OR clause_b AND v.book IN (...)  -- WRONG: filter only applies to clause_b
Always either wrap OR clauses in parentheses:
  WHERE (clause_a OR clause_b) AND v.book IN (...)  -- CORRECT
Or use UNION ALL with the book filter in each branch:
  SELECT ... WHERE clause_a AND v.book IN (...)
  UNION ALL
  SELECT ... WHERE clause_b AND v.book IN (...)

─── KJV + HEBREW TABLES ─────────────────────────────────────────────────────
You also have access to KJV verse text and word-level Strong's data:

  kjv_verses(verse_id, book_id, chapter, verse_num, verse_text)
      Full KJV verse text, 31,102 verses. book_id matches the books table.

  kjv_words(word_id, book_id, chapter, verse_num, verse_pos, word, italic)
      Every KJV word tokenized with position. italic=1 means the word was
      added by translators with no corresponding source word.

  kjv_strongs(word_id, strongs_id)
      Links each KJV word to its Strong's number. G-numbers for NT, H-numbers
      for OT.

  bdb(strongs_id, lemma, xlit, pronounce, description, part_of_speech)
      Brown-Driver-Briggs Hebrew lexicon, 8,674 entries, H-numbers only.

HEBREW WORD SEARCH — for queries about a specific Hebrew word (by name, transliteration,
or meaning), find its H-number via bdb then bridge to ABP verses using the books table
(books.id = kjv_words.book_id = kjv_verses.book_id):

  SELECT w.strongs_base, w.strongs, w.english, w.english_head,
         v.book, v.chapter, v.verse,
         l.lemma, l.translit, l.strongs_def, l.kjv_def, l.derivation
  FROM words w
  JOIN verses v ON w.verse_id = v.id
  LEFT JOIN lexicon l ON l.strongs = SUBSTR(w.strongs_base, 2)
  JOIN books bk ON bk.abbrev = v.book
  WHERE (bk.id, v.chapter, v.verse) IN (
      SELECT kw.book_id, kw.chapter, kw.verse_num
      FROM kjv_strongs ks
      JOIN kjv_words kw ON kw.word_id = ks.word_id
      WHERE ks.strongs_id = (
          SELECT strongs_id FROM bdb WHERE xlit LIKE '%hesed%' LIMIT 1
      )
  )
  ORDER BY v.id, w.position LIMIT 500

  Substitute the bdb subquery with the relevant transliteration or lemma pattern,
  or use a known H-number directly (e.g. ks.strongs_id = 'H2617').
  Use xlit for transliterations (chesed, ruach, shalom), lemma for Hebrew script.

  cross_references(id INTEGER, verse_id INTEGER, verse_ref_id INTEGER)
      Torrey's Treasury of Scripture Knowledge — thematic cross-references.
      Both columns reference kjv_verses.verse_id (not ABP verses.id).
      Use this table at your own judgment when a query would benefit from
      cross-testament thematic connections. Do not use it for focused
      single-word lexical queries where it would add noise.
      Example — passages cross-referenced to John 3:16 (book_id=43):
        SELECT kv.book_id, kv.chapter, kv.verse_num, kv.verse_text
        FROM cross_references cr
        JOIN kjv_verses kv ON kv.verse_id = cr.verse_ref_id
        WHERE cr.verse_id = (SELECT verse_id FROM kjv_verses
                             WHERE book_id=43 AND chapter=3 AND verse_num=16)

TRANSLATION COMPARISON queries:
  To compare KJV vs ABP renderings of a concept or word:
  1. Find the relevant Strong's number(s) from the lexicon table.
  2. Join kjv_strongs + kjv_words to filter to verses where the KJV rendering
     differs from ABP, using LOWER(w.english_head) != LOWER(kw.word).
  3. Always return the standard column set — the server requires these exact
     columns to display results. Use the KJV word as a JOIN filter, not a
     selected column.
  Put the comparison analysis in the explanation field, not the SQL shape.

  For open-ended comparison queries (e.g. "what stands out as differences
  in Acts KJV vs ABP"): find where the same Strong's numbers produced
  different English words, surface patterns, and flag anything theologically
  significant. Use this join pattern:

  SELECT w.strongs_base, w.strongs, w.english, w.english_head,
         v.book, v.chapter, v.verse,
         l.lemma, l.translit, l.strongs_def, l.kjv_def, l.derivation
  FROM words w
  JOIN verses v ON w.verse_id = v.id
  LEFT JOIN lexicon l ON l.strongs = SUBSTR(w.strongs_base, 2)
  JOIN kjv_strongs ks ON ks.strongs_id = 'G' || w.strongs_base
  JOIN kjv_words kw
    ON kw.word_id = ks.word_id
   AND kw.book_id = (SELECT id FROM books WHERE abbrev = v.book)
   AND kw.chapter = v.chapter
   AND kw.verse_num = v.verse
  WHERE v.book = 'Act'
    AND (w.strongs_base = '4151' OR w.strongs_base = 'G4151')
    AND LOWER(w.english_head) != LOWER(kw.word)
  ORDER BY v.id, w.position LIMIT 500

  For OT questions involving Hebrew: use kjv_strongs to get the H-number,
  then look it up in bdb for the Hebrew definition and lemma.\
"""

_AI_SYSTEM_BUILT: str | None = None


def _get_ai_system() -> str:
    global _AI_SYSTEM_BUILT
    if _AI_SYSTEM_BUILT is not None:
        return _AI_SYSTEM_BUILT
    conn = db()
    try:
        rows = conn.execute(
            "SELECT abbrev, name FROM books ORDER BY id"
        ).fetchall()
    finally:
        conn.close()

    names   = [r[1] for r in rows]
    abbrevs = [r[0] for r in rows]

    if len(names) == 1:
        corpus_list = names[0]
    else:
        corpus_list = ", ".join(names[:-1]) + ", and " + names[-1]

    schema_books = ", ".join(f'"{a}" ({n})' for a, n in zip(abbrevs, names))

    _AI_SYSTEM_BUILT = (
        _AI_SYSTEM_TMPL
        .replace("@@CORPUS_LIST@@", corpus_list)
        .replace("@@SCHEMA_BOOKS@@", schema_books)
    )
    log.debug("Built AI system prompt for books: %s", abbrevs)
    return _AI_SYSTEM_BUILT

# Words that start with a capital but are NOT proper nouns for the english LIKE fallback.
# Theological terms with Strong's numbers (God, Lord, Jesus, Christ) are excluded because
# they appear in thousands of verses and are already handled by the AI's strongs_base SQL.
_PROPER_NOUN_STOP = frozenset({
    "The", "A", "An", "In", "Of", "To", "And", "Or", "But", "With",
    "For", "At", "By", "From", "Where", "When", "What", "Who", "How",
    "Why", "Did", "Does", "Do", "Is", "Are", "Was", "Were", "Has",
    "Have", "Had", "Will", "Would", "Could", "Should", "May", "Might",
    "Show", "Find", "Get", "Tell", "Give", "Let", "Make", "Take",
    "All", "His", "Her", "Its", "Our", "Their", "My", "Your",
    "This", "That", "These", "Those", "There", "Here", "Then",
    "He", "She", "It", "We", "They", "You", "Me", "Him", "Her",
    "God", "Lord", "Jesus", "Christ",
})


def _extract_proper_nouns(q: str) -> list[str]:
    """Return deduplicated capitalized words that look like proper nouns."""
    seen: set[str] = set()
    result: list[str] = []
    for w in re.findall(r'\b[A-Z][a-z]{2,}\b', q):
        if w not in _PROPER_NOUN_STOP and w not in seen:
            seen.add(w)
            result.append(w)
    return result


# Divine council corpus — injected as primary when query matches.
# Bypasses Haiku curation so results are deterministic regardless of SQL.
_DIVINE_COUNCIL_VERSES: frozenset = frozenset({
    ("Gen",  1, 26), ("Gen",  3, 22), ("Gen",  6,  2), ("Gen",  6,  4), ("Gen", 11,  7),
    ("Deu", 32,  8), ("Deu", 32, 43),
    ("1Ki", 22, 19), ("1Ki", 22, 20),
    ("Job",  1,  6), ("Job",  2,  1),
    ("Psa", 29,  1), ("Psa", 82,  1), ("Psa", 82,  6), ("Psa", 89,  5), ("Psa", 89,  7),
    ("Isa",  6,  1), ("Isa",  6,  8),
    ("Zec",  3,  1), ("Zec",  3,  2),
})


# Triggers the hardcoded divine council corpus injection.
# Deliberately narrow — only phrases that unambiguously signal a divine council
# query. Broad terms like "sons of God", "holy ones", "divine being" are excluded
# because they appear in NT adoption theology, Pauline letters, etc. and should
# be answered by the normal SQL path, not overridden by the OT corpus.
_DIVINE_COUNCIL_RE = re.compile(
    r'\b(?:divine\s+council|heavenly\s+(?:assembly|court)|divine\s+assembly|'
    r'bene\s+[ae]lohim|elohim\s+council|council\s+of\s+(?:god|the\s+holy)|'
    r'gods?\s+of\s+the\s+nations?|host\s+of\s+heaven|huioi?\s+tou\s+theou)\b',
    re.IGNORECASE,
)

# Normalise raw book strings (from AI output or regex captures) to DB abbreviations.
_BOOK_NORM: dict[str, str] = {
    "gen": "Gen", "genesis": "Gen",
    "exo": "Exo", "exod": "Exo", "exodus": "Exo",
    "lev": "Lev", "leviticus": "Lev",
    "num": "Num", "numbers": "Num",
    "deu": "Deu", "dtn": "Deu", "deut": "Deu", "deuteronomy": "Deu",
    # DB abbreviation doesn't match title()[:3] for these two books
    "jud": "Jdg", "judg": "Jdg", "judges": "Jdg",
    "rut": "Rth", "ruth": "Rth",
}

_VERSE_REF_RE: re.Pattern | None = None

# Parses "Book Ch:V" refs from AI-generated text (explanation, primary_verses, etc.)
_VERSE_REF_PARSE_RE = re.compile(r'(\w+)\s+(\d+):(\d+)')

# Inner text of an `... LIKE '%phrase%'` clause in the AI's generated SQL. The
# phrase supplement re-runs the AI's own multi-word phrases against the FULL verse
# text (verses.text / kjv_verses.verse_text), where a contiguous phrase actually
# lives — the word-gloss `english` splits + reorders phrases, so a gloss LIKE both
# scans all ~600k words AND misses.
_LIKE_PHRASE_RE = re.compile(r"LIKE\s+'%([^%']+)%'", re.IGNORECASE)


def _norm_book(raw: str) -> str:
    key = raw.lower().rstrip(".")
    return _BOOK_NORM.get(key) or _BOOK_NORM.get(key[:3]) or raw.title()[:3]


def _get_verse_ref_re() -> re.Pattern:
    global _VERSE_REF_RE
    if _VERSE_REF_RE is not None:
        return _VERSE_REF_RE
    conn = db()
    try:
        rows = conn.execute("SELECT re_alt FROM books ORDER BY id").fetchall()
    finally:
        conn.close()
    alts = [r[0] for r in rows]
    _VERSE_REF_RE = re.compile(
        r'\b(' + '|'.join(alts) + r')\s+(\d+):(\d+)\b',
        re.IGNORECASE,
    )
    log.debug("Built _VERSE_REF_RE from books table: %s", alts)
    return _VERSE_REF_RE


def _fetch_verse_words(conn, verse_id: int) -> list[dict]:
    """Return the full word list for a verse, used when fetching cited/primary verses."""
    lem, tr, dl = dotted_lexicon_cols(conn)
    wrows = conn.execute(
        f"""SELECT w.strongs_base, w.strongs, w.english, w.english_head, w.greek_pos,
                  w.bracket_id, w.italic, w.is_pn,
                  COALESCE(w.italic_words, '') AS italic_words,
                  {lem} AS lemma, {tr} AS translit, l.strongs_def, l.kjv_def, l.derivation
           FROM words w
           LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base
           {dl}
           WHERE w.verse_id = ?
             AND w.english IS NOT NULL AND w.english != ''
             AND w.strongs_base != '*'
           ORDER BY w.position""",
        (verse_id,),
    ).fetchall()
    return [
        {
            **_serialize_word_core(wr),
            "italic":       bool(wr["italic"]),
            "is_function":  wr["strongs_base"] in _FUNCTION_STRONGS,
            "gloss":        _clean_gloss(wr["english"]),
            "strongs_def":  (wr["strongs_def"] or "").strip(),
            "derivation":   (wr["derivation"] or "").strip(),
        }
        for wr in wrows
    ]


_CURATION_SYSTEM = """\
You are selecting primary evidence verses for a word study of the Greek Bible (OT + NT).
Return your answer in TWO parts, IN THIS ORDER:

PART 1 — the explanation (see the explanation section below). Plain prose only: no
markdown, no headers, no labels, no JSON.

PART 2 — then, on its OWN line, the marker
===VERSES===
followed by ONE line of JSON holding the verse selections — no markdown fences, and
nothing after it:
{"primary_verses": ["Book Ch:V", ...], "additional_verses": ["Book Ch:V", ...]}

─── STEP 1: IDENTIFY THE REFERENT ──────────────────────────────────────────
Before selecting any verses, determine exactly which referent the query targets.
The same Greek words can denote completely different concepts; conflating them
produces misleading results. Apply these rules:

SINGULAR vs PLURAL sonship
  "Son of God" (singular, title-case, or clearly Christological context)
      → Jesus specifically: baptism voice, transfiguration, trial confession,
        Johannine "I am" discourse, messianic declarations.
      → EXCLUDE verses where huios/teknon refers to believers or heavenly beings.
  "sons of God" / "children of God" (plural, or adoptionist context)
      → Believers (NT adoption: Rom 8:14–17, Gal 3:26, 1 Jn 3:1–2) AND/OR
        divine/heavenly beings (Gen 6:2–4, Job 1:6, 2:1, Psa 82:6, Deu 32:8).
      → EXCLUDE Christological title verses (Jesus declared Son of God at baptism
        or trial) unless the query explicitly asks about Jesus.
      → EXCLUDE verses where the referent is "sons of Israel", "son of man",
        "sons of Aaron", "sons of Levi", "sons of men", or any other "sons of X"
        construct where X is not God. These share the same Strong's numbers but
        are entirely different concepts — discard them regardless of how many
        matching words appear in the verse.

DIVINE COUNCIL vs GENERAL SONSHIP
  "divine council" / "heavenly assembly" / "bene ha-elohim"
      → OT supernatural assembly (Job 1–2, Psa 82, Deu 32, 1 Ki 22:19–22).
      → EXCLUDE NT adoption theology and Christological passages entirely.
  General "sons of God" without divine-council framing
      → Draw from both OT (divine beings) and NT (adoption) unless the query
        limits scope (e.g. "in the NT" → NT only; "in Genesis" → OT only).

HOLY SPIRIT / SPIRIT OF GOD
  "Holy Spirit" or "Spirit of God" as divine person/presence
      → Prioritise programmatic passages: Acts 2 (Pentecost), John 14–16
        (Paraclete/G3875), Rom 8 (adoption + intercession), Gen 1:2 (hovering).
      → EXCLUDE verses where pneuma refers merely to human breath or disposition.

Apply this referent identification first; then select primary verses only from
the matching pool, discarding verses that belong to a different referent class.

FALLBACK: If the referent filter leaves fewer than 5 qualifying verses, discard
the filter entirely and select from the full verse pool. The goal is to narrow
and prioritize, not to eliminate results. Never return an empty primary_verses
list when the verse pool is non-empty.

─── STEP 2: SELECT PRIMARY VERSES ──────────────────────────────────────────
Select from the verse list provided. The user message specifies the target count.
Rank candidates in this priority order:

1. FOUNDATIONAL / PROGRAMMATIC — verses that introduce, define, or establish the
   concept in canonical theology. Include these even if vocabulary density is low.
   e.g. Acts 2 for the Holy Spirit at Pentecost; John 14–16 for the Paraclete;
   Rom 8 for Spirit and adoption; Deu 32:8 for divine allotment; Gen 1:26 for
   the divine plural. These belong in primary regardless of how many matching
   Strong's numbers appear in the verse.

2. THEOLOGICALLY CENTRAL — verses scholars and students invariably cite for this
   topic. For NT themes prefer John, Acts, Romans, Galatians, Hebrews anchor
   texts over incidental mentions in shorter letters, unless the shorter letter
   passage is itself definitional (e.g. Gal 4:6 for divine sonship).

3. GRAMMATICALLY PROMINENT — the concept is the grammatical subject, object, or
   predicate; it acts, is described, named, qualified, or placed in a
   theologically significant relationship.

4. FUNCTIONALLY SIGNIFICANT — the concept performs a key role (intercession,
   governance, identity-marking) even if not the main subject.

CRITICAL: Do NOT preference verses on lexical density alone. A foundational verse
with one occurrence of the key term outranks a verbose passage where the term
appears incidentally three times. Frequency of matching words within a single
verse is not a proxy for theological importance.

Exclude ONLY when the word has zero bearing on the topic: a personal name in an
unrelated genealogy, a bare preposition or particle, a place name, or a pure
counting formula where the word is grammatical filler.

─── additional_verses ───────────────────────────────────────────────────────
List verse refs (Book Ch:V) that are standard scholarly citations for this topic
but were NOT in the verse list provided. Use ONLY when:
  • Scholarly consensus is strong that the verse belongs in this study, AND
  • The connection is inferred from context or implicit language rather than
    explicit vocabulary.
If the verse list already covers the topic well, return additional_verses as [].
Prefer empty over speculative.

─── explanation ──────────────────────────────────────────────────────────────
Write a plain-prose lexicon note — no markdown, no headers, no bold, no labels. Open
with the Greek or Hebrew term under study and what it means, name its concrete sense
range, and anchor each sense to an example verse.
PARAGRAPHS: when the word's meaning turns to a clearly DIFFERENT sense, start a new
paragraph (a blank line between). Break ONLY on a real sense shift — a word with one
sense stays a single paragraph; never break for variety or after a set number of
sentences, and never split one point across two paragraphs. Most words need 1-2 short
paragraphs; a richly polysemous word (several distinct senses) may run to about one
short paragraph per sense.
SYNTHESIZE, DON'T RECITE: the note says what the word's senses ARE and how they differ —
organized BY SENSE, one paragraph per sense. It is NOT a list of where the word occurs:
the passage panel beside the note already carries the full occurrence list. Within a
sense, name ONE example verse or two that show it (every claim still ties to a verse),
but never march through citations or pile up references — a new paragraph turns on a
shift in MEANING, never on the next verse in the list.
SCRIPT: in the prose use the TRANSLITERATION + Strong's number only (e.g. "sabbaton,
G4521" — never σάββατον), NOT raw Greek or Hebrew letters. The script lives in the word
chips beside the note; keep the write-up itself readable for a non-Greek reader.
OMIT, DON'T DISMISS: the key words listed are CANDIDATES — discuss only those that
actually bear on the question. If a listed word (or a verse in the pool) turns out
unrelated, say nothing about it; never name a word just to call it incidental,
unrelated, or coincidental. Spend the whole note on what answers the question.
NO EMPTY PARENTHESES, NO QUOTED VERSES: never write "word ()" — give a word as its
transliteration + Strong's number (e.g. "sabbaton, G4521") and a passage as its
reference (Book Ch:V). Cite verses by reference only; never quote or transcribe a
verse's full text in the prose.
SABBATH vs WEEK: when the source woodenly renders the numeral idiom "one/first of the Sabbaths"
(e.g. 1Co 16:2, Mat 28:1, Joh 20:1, Act 20:7), sabbaton there means the seven-day WEEK — say "the
first day of the week" (the day AFTER the Sabbath), never "a Sabbath". Outside that numeral idiom,
sabbaton is the ordinary Sabbath day.

REPORT, DON'T CHARACTERIZE. Tie every statement to a specific verse and let the verse's own
action carry the sentence — what it SAYS, COMMANDS, ASKS, RECORDS, or CALLS something. The test
for every clause: a reader should be able to open the verse you name and find it stating exactly
what you wrote. A clause describing what a concept becomes, undergoes, or comes to mean across
several passages has no single verse behind it — that is your synthesis, not the text; cut it or
pin it to the one verse that states it. Never place a word in a passage the verse list does not
show it in. Report what a verse says, not what it leaves unsaid: do not add riders about what a
verse fails to say or command ("without commanding X", "though it never says Y") — if a verse is
silent on a point, leave it out and let the silence stand.
  GOOD: "Sabbaton (G4521) is the seventh-day rest. Exo 20:8 commands Israel to remember the
        sabbath day and keep it holy; Mark 2:27 records Jesus saying the sabbath was made for
        man, not man for the sabbath, and the next verse calls the Son of Man lord of the sabbath."
  BAD:  "The sabbath was instituted at creation, codified in the Law, and reinterpreted by Jesus
        in terms of human benefit and his own authority." (no verse states "instituted at
        creation" — sabbaton is not in the creation account; "codified" and "reinterpreted"
        narrate the concept instead of reporting a verse)

BEREAN — NO DOCTRINAL VERDICTS (the most important rule). Report what each cited verse
SAYS; never settle a contested question for the reader. Do NOT label a practice or command
"binding" or "not binding", "obligatory", "optional", "abolished", "fulfilled", "reinterpreted",
"transferred", "still in force", or "a matter of conscience" — those are theological conclusions
imposed from outside the text. Do NOT assign a stance to an author or book ("Paul places X
among...", "Hebrews reinterprets X as..."); attribute the statement to the verse itself and say
what it actually states. Set the cited verses side by side and let the reader draw the conclusion.
Still ANSWER: never refuse a contested question, call it out of scope, or tell the reader to
rephrase — report what the verses say and withhold only the verdict.
  GOOD: "Col 2:16 tells the reader to let no one judge them regarding a sabbath; in Rom 14:5
        one person esteems one day above another while another esteems every day alike; Heb 4:9
        says a sabbath-rest (sabbatismos) remains for the people of God."
  BAD:  "Paul places Sabbath observance among matters of personal conscience rather than binding
        obligation, and Hebrews reinterprets it as an eschatological rest." (doctrinal verdicts
        the verses do not state)
CITATIONS — STRICT: cite ONLY verse references that appear in the verse list given in
the user message. Never cite a verse that is not in that list. To make a thematic
point about a passage that is not listed, describe it in words with no chapter:verse
citation.
NEUTRALITY: answer from the verses, NOT from how the question is framed. If the question
assumes a conclusion ("are X and Y the same?" / "...different?"), state what the text
actually shows rather than agreeing with the assumption; the same question phrased either
way must get the same answer. If the verses don't settle it, say so plainly.\
"""


def _xref_scores(conn, verses: list[dict]) -> dict:
    """How cross-referenced each result verse is in Torrey's TSK (cross_references) —
    a free 'scholars cite this a lot' importance signal. Returns {(book,ch,v): count}.
    cross_references is keyed by kjv_verses.verse_id, so bridge each ABP coord ->
    kjv verse_id via the books table, then count that verse's TSK references.
    Returns {} on ANY problem (missing tables, version skew) so the caller silently
    falls back to position order — this can never break a search."""
    try:
        bid = {r["abbrev"]: r["id"] for r in conn.execute("SELECT abbrev, id FROM books")}
        inv_bid = {v: k for k, v in bid.items()}
        coords = [(bid[v["book"]], v["chapter"], v["verse"]) for v in verses if v["book"] in bid]
        if not coords:
            return {}
        vid_of_coord: dict = {}
        for i in range(0, len(coords), 300):          # stay well under SQLite's param cap
            chunk = coords[i:i + 300]
            clause = " OR ".join("(book_id=? AND chapter=? AND verse_num=?)" for _ in chunk)
            params = [x for c in chunk for x in c]
            for r in conn.execute(
                f"SELECT verse_id, book_id, chapter, verse_num FROM kjv_verses WHERE {clause}",
                params,
            ):
                vid_of_coord[(r["book_id"], r["chapter"], r["verse_num"])] = r["verse_id"]
        if not vid_of_coord:
            return {}
        cnt: dict = {}
        vids = list(set(vid_of_coord.values()))
        for i in range(0, len(vids), 400):
            chunk = vids[i:i + 400]
            ph = ",".join("?" for _ in chunk)
            for r in conn.execute(
                f"SELECT verse_id, count(*) AS c FROM cross_references "
                f"WHERE verse_id IN ({ph}) GROUP BY verse_id", chunk,
            ):
                cnt[r["verse_id"]] = r["c"]
        return {
            (inv_bid[b], ch, vs): cnt.get(vid, 0)
            for (b, ch, vs), vid in vid_of_coord.items()
        }
    except Exception as exc:
        log.warning("xref scoring failed (falling back to position order): %s", exc)
        return {}


def _spread_sample(results: list[dict], cap: int, scores: dict | None = None) -> list[dict]:
    """Pick up to `cap` verses spread ACROSS the books they fall in — not the first
    `cap`. Ordered by verse id, the first N hits of a common word are all early-OT,
    so the synthesizer never saw the NT (an 'agape' answer cited only Genesis /
    Deuteronomy, missing John + 1 Corinthians). Round-robin one verse per book per
    pass until the cap — so every book that uses the word gets a seat and no single
    book can dominate. When `scores` is given (TSK cross-reference counts), each
    book's verses are ordered most-referenced first, so its one seat goes to the
    verse that matters, not just the earliest. Ties + no-score keep position order."""
    if len(results) <= cap:
        return results
    by_book: dict = {}
    for v in results:
        by_book.setdefault(v["book"], []).append(v)
    if scores:
        for bucket in by_book.values():
            bucket.sort(key=lambda v: scores.get((v["book"], v["chapter"], v["verse"]), 0),
                        reverse=True)
    books = list(by_book.keys())
    picked: list = []
    i = 0
    while len(picked) < cap and any(by_book.values()):
        bucket = by_book[books[i % len(books)]]
        if bucket:
            picked.append(bucket.pop(0))
        i += 1
    return picked


# Pass-2 returns the synthesis prose FIRST (plain text, streamable), then this marker,
# then a one-line JSON object with the verse picks. Anchoring the picks in a tail after
# a fixed marker lets the prose stream to the reader live while the machine-readable
# selections are parsed at the end — and lets us fail CLOSED if that tail is malformed.
_CURATION_MARK = "===VERSES==="


def _parse_curation(raw: str):
    """Split a pass-2 response into (primary, additional, explanation).

    FAIL-CLOSED: returns None on any malformed/missing tail, so the caller falls back
    rather than mark wrong verses from a garbled parse. The prose half is whatever
    precedes the marker; the picks come ONLY from a clean JSON object in the tail after
    it (prose braces can't leak in — the marker anchors the split).
    """
    if not raw or _CURATION_MARK not in raw:
        return None
    prose, _, tail = raw.partition(_CURATION_MARK)
    explanation = prose.strip()
    if not explanation:
        return None
    s, e = tail.find("{"), tail.rfind("}")
    if s == -1 or e <= s:
        return None
    try:
        picks = json.loads(tail[s:e + 1])          # JSONDecodeError is a ValueError
    except (ValueError, TypeError):
        return None
    if not isinstance(picks, dict) or not isinstance(picks.get("primary_verses"), list):
        return None
    primary = [str(r) for r in picks["primary_verses"]]
    addl = picks.get("additional_verses")
    additional = [str(r) for r in addl] if isinstance(addl, list) else []
    return primary, additional, explanation


def _curation_prompt(
    query: str, results: list[dict], key_strongs_data: list[dict] | None = None
) -> tuple[str, int]:
    """Build the pass-2 user message + the primary-verse cap. Shared by the streamed and
    non-streamed curation paths so both feed Sonnet the IDENTICAL prompt — streaming
    changes only how the answer reaches the reader, never what the model is asked."""
    # Scale input window and primary target with result pool size.
    n = len(results)
    if n >= 200:
        input_cap, primary_cap = 60, 15
    elif n >= 100:
        input_cap, primary_cap = 50, 12
    elif n >= 50:
        input_cap, primary_cap = 40, 10
    else:
        input_cap, primary_cap = max(n, 1), 8

    # Within each book, prefer its most cross-referenced verse so the one seat per
    # book goes to the verse that matters, not just the earliest. Only worth scoring
    # when we're actually subsampling; degrades to position order on any failure.
    scores = None
    if len(results) > input_cap:
        sc_conn = db_ro()
        try:
            scores = _xref_scores(sc_conn, results)
        finally:
            sc_conn.close()
    capped = _spread_sample(results, input_cap, scores)
    if capped:
        or_parts = " OR ".join(
            "(v.book=? AND v.chapter=? AND v.verse=?)" for _ in capped
        )
        params = [x for v in capped for x in (v["book"], v["chapter"], v["verse"])]
        conn = db_ro()
        try:
            wrows = conn.execute(
                f"""SELECT v.book, v.chapter, v.verse, w.english
                    FROM words w JOIN verses v ON w.verse_id = v.id
                    WHERE ({or_parts})
                      AND w.english IS NOT NULL AND w.english != ''
                    ORDER BY v.id, w.position""",
                params,
            ).fetchall()
        finally:
            conn.close()

        texts: dict[str, list[str]] = {}
        for r in wrows:
            ref = f"{r['book']} {r['chapter']}:{r['verse']}"
            texts.setdefault(ref, []).append(r["english"])
        verse_list = "\n".join(
            f"{ref}: {' '.join(words)[:300]}" for ref, words in texts.items()
        )
    else:
        verse_list = ""

    terms = ", ".join(
        f"{e.get('strongs', '')} {e.get('lemma', '')}".strip()
        for e in (key_strongs_data or [])[:10]
    )
    user_msg = (
        f"Query: {query}\n"
        f"Key word(s) under study: {terms}\n"
        f"Write the explanation first (grounded ONLY in the verses below), then the "
        f"===VERSES=== marker and up to {primary_cap} primary verses as JSON.\n\n"
        f"Verses:\n{verse_list}"
    )
    return user_msg, primary_cap


def _curate_primary_verses(
    query: str, results: list[dict], key_strongs_data: list[dict] | None = None
) -> tuple[list[str], list[str], str]:
    """Pass 2, NON-STREAMED — the fallback path AND the floor under the streamed path.
    Sends the real verse texts to Sonnet, which picks the evidence verses AND writes the
    grounded explanation in one call. Returns (primary_refs, additional_refs, explanation);
    a malformed tail is retried once, then degrades to ([], [], "") so the caller keeps the
    from-memory prose with NO verse split — never wrong picks.
    """
    if not results or not _anthropic:
        return [], [], ""
    user_msg, primary_cap = _curation_prompt(query, results, key_strongs_data)
    # Pass 2 occasionally comes back unreadable or cut off on a long answer. Guard it: a
    # roomier word budget, an explicit cut-off warning, and one retry (a transient API
    # hiccup) before the downgrade. The tail-parse is fail-closed (_parse_curation).
    for attempt in range(2):
        try:
            msg = _anthropic.messages.create(
                # Sonnet writes the displayed synthesis + curates the verses — markedly
                # better prose/reasoning than Haiku (same as the xref + chapter summaries).
                model="claude-sonnet-4-6",
                max_tokens=1400,
                temperature=0,
                system=_CURATION_SYSTEM,
                messages=[{"role": "user", "content": user_msg}],
            )
            _u = msg.usage
            log.info("cache[sonnet-pass2]: fresh=%s write=%s read=%s",
                     _u.input_tokens,
                     getattr(_u, "cache_creation_input_tokens", 0),
                     getattr(_u, "cache_read_input_tokens", 0))
            if msg.stop_reason == "max_tokens":
                log.warning("Pass-2 curation hit the word cap (attempt %d/2) — may be cut off", attempt + 1)
            parsed = _parse_curation(msg.content[0].text.strip())
            if parsed is None:
                raise ValueError("pass-2 tail did not parse (fail-closed)")
            primary, additional, explanation = parsed
            return primary[:primary_cap], additional[:12], explanation
        except Exception as exc:
            log.warning("Pass-2 curation failed/unparseable (attempt %d/2): %s", attempt + 1, exc)
    return [], [], ""


def _streamable_prose(full: str, hold: int) -> str:
    """The synthesis prose safe to show so far: everything BEFORE the ===VERSES=== marker
    once it appears, or — until then — all but the last `hold` characters, so a half-arrived
    marker ("===VER") never flashes on screen. The JSON picks tail is never returned, so it
    can never reach the reader as text."""
    i = full.find(_CURATION_MARK)
    if i != -1:
        return full[:i]
    return full[:max(0, len(full) - hold)]


def _stream_curation(
    query: str, results: list[dict], key_strongs_data: list[dict] | None = None
):
    """Pass 2, STREAMED. A generator that YIELDS prose-delta strings as Sonnet writes the
    synthesis (the JSON picks tail is withheld), then RETURNS the parsed outcome:
      - (primary, additional, explanation) : a clean tail; use these picks.
      - (None, None, streamed_prose)       : the tail would not parse; the caller FLOORS it
        (re-runs the non-streamed curate for clean picks) and keeps this prose. Never wrong.
      - None                                : nothing to curate (no results / no client).
    """
    if not results or not _anthropic:
        return None
    user_msg, primary_cap = _curation_prompt(query, results, key_strongs_data)
    hold = len(_CURATION_MARK)
    full, emitted = "", 0
    with _anthropic.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1400,
        temperature=0,
        system=_CURATION_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        for chunk in stream.text_stream:
            full += chunk
            safe = _streamable_prose(full, hold)
            if len(safe) > emitted:
                yield safe[emitted:]
                emitted = len(safe)
        final = stream.get_final_message()
    raw = final.content[0].text if final.content else full
    # Flush any prose held back behind a possible partial marker.
    safe = _streamable_prose(raw, 0)
    if len(safe) > emitted:
        yield safe[emitted:]
    try:
        _u = final.usage
        log.info("cache[sonnet-pass2-stream]: fresh=%s read=%s",
                 _u.input_tokens, getattr(_u, "cache_read_input_tokens", 0))
    except Exception:
        pass
    parsed = _parse_curation(raw)
    if parsed is not None:
        primary, additional, explanation = parsed
        return primary[:primary_cap], additional[:12], explanation
    return None, None, _streamable_prose(raw, 0).strip()


def _sse(event: str, obj) -> str:
    """One Server-Sent Event frame: an event name + a single-line JSON payload. json.dumps
    escapes any newlines in the data (e.g. paragraph breaks in a prose delta), so every
    frame is two lines + a blank — the wire shape the frontend splits on."""
    return f"event: {event}\ndata: {json.dumps(obj, ensure_ascii=False)}\n\n"


def _assemble_payload(q, results, verse_index, key_strongs_data,
                      primary_verses_raw, additional_verses_raw, explanation,
                      rows, phrase_hits, target_bases, panel):
    """Post-curation assembly (shared end-stage, lifted out of the route so the streaming
    generator can run it once the prose has streamed): fold the curated picks into the
    pool, fetch any named verses the SQL missed, tag is_primary / is_additional, inject the
    hardcoded divine-council corpus, decide grounding, sort canonically, build the payload."""
    # ── Build primary_set and fetch any missing primary verses ────────────
    dc_query = bool(_DIVINE_COUNCIL_RE.search(q))
    primary_set: set = set()
    for ref_str in primary_verses_raw:
        m = _VERSE_REF_PARSE_RE.search(str(ref_str).strip())
        if m:
            primary_set.add((_norm_book(m.group(1)), int(m.group(2)), int(m.group(3))))

    # ── Hardcoded corpora — injected regardless of model output ──────────
    if dc_query:
        primary_set.update(_DIVINE_COUNCIL_VERSES)
        log.debug("Divine council corpus injected: %d verses", len(_DIVINE_COUNCIL_VERSES))

    missing_primary = [k for k in primary_set if k not in verse_index]
    if missing_primary:
        prim_conn = db_ro()
        new_primary = []
        try:
            for key in missing_primary:
                book, chapter, verse_num = key
                vrow = prim_conn.execute(
                    "SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
                    (book, chapter, verse_num),
                ).fetchone()
                if not vrow:
                    continue
                words = _fetch_verse_words(prim_conn, vrow["id"])
                if words:
                    verse_index[key] = {
                        "ref": f"{book} {chapter}:{verse_num}",
                        "book": book, "chapter": chapter, "verse": verse_num,
                        "words": words,
                    }
                    new_primary.append(key)
                    log.debug("Primary verse fetched: %s %d:%d", book, chapter, verse_num)
        finally:
            prim_conn.close()
        if new_primary:
            results = [verse_index[k] for k in new_primary] + results

    # ── Validate and fetch additional verses from the model's knowledge ───
    additional_set: set = set()
    for ref_str in additional_verses_raw:
        m = _VERSE_REF_PARSE_RE.search(str(ref_str).strip())
        if m:
            additional_set.add(
                (_norm_book(m.group(1)), int(m.group(2)), int(m.group(3)))
            )

    if additional_set:
        add_conn = db_ro()
        new_additional: list = []
        try:
            for key in additional_set:
                book, chapter, verse_num = key
                vrow = add_conn.execute(
                    "SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
                    (book, chapter, verse_num),
                ).fetchone()
                if not vrow:
                    log.debug(
                        "Additional verse not in DB (dropped): %s %d:%d",
                        book, chapter, verse_num,
                    )
                    continue
                if key in verse_index:
                    continue
                words = _fetch_verse_words(add_conn, vrow["id"])
                if words:
                    verse_index[key] = {
                        "ref": f"{book} {chapter}:{verse_num}",
                        "book": book, "chapter": chapter, "verse": verse_num,
                        "words": words,
                        "is_thematic": _is_thematic(words),
                    }
                    new_additional.append(key)
                    log.debug(
                        "Additional verse fetched: %s %d:%d", book, chapter, verse_num
                    )
        finally:
            add_conn.close()
        if new_additional:
            results = [verse_index[k] for k in new_additional] + results

    # ── Tag is_primary / is_additional on every result verse ─────────────
    for v in results:
        key = (v["book"], v["chapter"], v["verse"])
        thematic = v.get("is_thematic", False)
        if dc_query:
            v["is_primary"] = key in _DIVINE_COUNCIL_VERSES
        else:
            v["is_primary"] = (key in primary_set) and not thematic
        v["is_additional"] = thematic or ((key in additional_set) and not v["is_primary"])

    # ── Sort in canonical book order (books.id) then chapter/verse ────────
    ord_conn = db_ro()
    try:
        book_order = {
            r["abbrev"]: r["id"]
            for r in ord_conn.execute(
                "SELECT abbrev, id FROM books ORDER BY id"
            ).fetchall()
        }
    finally:
        ord_conn.close()
    results.sort(
        key=lambda v: (book_order.get(v["book"], 9999), v["chapter"], v["verse"])
    )

    # ── Hardcoded divine council key_strongs ─────────────────────────────
    if dc_query:
        dc_strongs = [
            {"strongs_base": "5207", "strongs": "G5207", "lemma": "υἱός",    "translit": "huiós",   "definition": "", "derivation": ""},
            {"strongs_base": "2316", "strongs": "G2316", "lemma": "θεός",    "translit": "theós",   "definition": "", "derivation": ""},
            {"strongs_base": "5475", "strongs": "H5475", "lemma": "סוֹד",    "translit": "sôd",     "definition": "", "derivation": ""},
            {"strongs_base": "5712", "strongs": "H5712", "lemma": "עֵדָה",   "translit": "ʿēdâh",  "definition": "", "derivation": ""},
            {"strongs_base": "1121", "strongs": "H1121", "lemma": "בֵּן",    "translit": "bēn",     "definition": "", "derivation": ""},
            {"strongs_base": "430",  "strongs": "H430",  "lemma": "אֱלֹהִים","translit": "ʾĕlōhîm","definition": "", "derivation": ""},
        ]
        existing_bases = {k["strongs_base"] for k in key_strongs_data}
        for ks in dc_strongs:
            if ks["strongs_base"] not in existing_bases:
                key_strongs_data.append(ks)

    # ── Grounding: is the answer backed by a REAL occurrence, or just model knowledge? ──
    if not results:
        grounded = False
    elif rows or phrase_hits or not target_bases:
        grounded = True
    else:
        grounded = any(not _is_thematic(v.get("words", [])) for v in results)

    return {"results": results, "total": len(results), "grounded": grounded,
            "explanation": explanation, "key_strongs": key_strongs_data, "panel": panel}


def _normalize_union_sql(sql: str) -> str:
    """Wrap UNION ALL queries in a subquery so ORDER BY works in SQLite.

    In a SQLite compound select (UNION ALL), ORDER BY cannot reference
    table-qualified names like v.id or w.position because the aliases are out
    of scope. Wrapping in a subquery lets the outer SELECT * pick up all columns
    by their unqualified names and apply a clean ORDER BY.

    No LIMIT is applied to UNION queries: each branch is already scoped to a
    specific concept, so total row count is manageable, and pass-2 curation caps
    the verses it processes at 50. Single-pattern queries keep their own LIMIT.
    """
    if not re.search(r'\bUNION\b', sql, re.IGNORECASE):
        return sql
    # Strip the trailing ORDER BY … LIMIT … that Haiku appends (table-qualified
    # names are invalid in a compound-select context; LIMIT removed deliberately).
    inner = re.sub(
        r'\s+ORDER\s+BY\s+\S.*',
        '',
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    ).rstrip()
    return (
        "SELECT * FROM (\n"
        + inner
        + "\n) ORDER BY book, chapter, verse"
    )


def _group_word_rows(rows) -> tuple[dict, list, list]:
    """Collapse word-level SQL rows into one entry per verse (ABP word shape).
    Returns (verse_index, verse_order, results). Used for both the first query
    and the last-resort retry."""
    verse_index: dict = {}
    verse_order: list = []
    row_keys = rows[0].keys() if rows else []
    has_word_cols = all(c in row_keys for c in ("english", "strongs_base", "strongs"))
    for r in rows:
        try:
            key = (r["book"], r["chapter"], r["verse"])
        except IndexError:
            continue
        if key not in verse_index:
            verse_index[key] = {
                "ref":     f"{r['book']} {r['chapter']}:{r['verse']}",
                "book":    r["book"],
                "chapter": r["chapter"],
                "verse":   r["verse"],
                "words":   [],
            }
            verse_order.append(key)
        if not has_word_cols or not r["english"] or r["strongs_base"] == "*":
            continue
        verse_index[key]["words"].append({
            "strongs":      r["strongs"],
            "strongs_base": r["strongs_base"],
            "is_function":  r["strongs_base"] in _FUNCTION_STRONGS,
            "gloss":        _clean_gloss(r["english"]),
            "lemma":        r["lemma"],
            "translit":     r["translit"],
            "strongs_def":  (r["strongs_def"] or "").strip(),
            "kjv_def":      r["kjv_def"],
            "derivation":   (r["derivation"] or "").strip(),
        })
    results = [verse_index[k] for k in verse_order if verse_index[k]["words"]]
    return verse_index, verse_order, results


# Below this many result verses, the pass-2 ranking call adds nothing (it would
# return them all anyway) — skip it and show them all, saving a ~5s model call.
_CURATE_SKIP_MAX = 8

# The proper-noun name-scan (a slow `english LIKE '%Word%'` on ~600k words) is a
# FALLBACK for a name query Strong's can't see. Only run it when the main search is
# this thin — otherwise a common capitalized word ("Sabbath", already found 182x)
# triggers a pointless ~7s scan.
_PROPER_NOUN_NEED = 25

# Same-root cognate supplement: how many family members we'll add as chips per query
# (a relative only counts if it actually occurs), and how many of each one's verses to
# pull into the pool. Kept small so a big word-family can't flood the chips or results.
_COGNATE_CHIP_CAP = 4
_COGNATE_VERSE_CAP = 60

# Hebrew occurrence supplement: how many heb.db verses (spread across books) to pull
# in per Hebrew target word. The curation step samples from these, so a representative
# canonical spread matters more than completeness.
_HEB_VERSE_CAP = 90

# Greek prefixes a real derivative may carry before the parent's stem (accent-stripped).
_GK_PREFIXES = (
    "προς", "παρα", "περι", "κατα", "μετα", "αντι", "απο", "επι", "ανα", "δια",
    "συν", "υπερ", "υπο", "εις", "εκ", "εν", "προ", "αμφι",
)

def _cognate_is_tight(parent_lemma: str, child_lemma: str) -> bool:
    """Keep a same-root cognate only when the parent's stem sits at the START of the
    child (optionally after a known Greek prefix) — a genuine derivative like
    σαββατ-ισμός or προ+σάββατον. Drops buried-root drifts that merely CONTAIN the
    root, e.g. εἰλι-κριν-ής hanging off κρίνω. Accent-stripped Greek comparison; too-short
    lemmas are kept (can't judge)."""
    p = _strip_accents(parent_lemma or "").lower()
    c = _strip_accents(child_lemma or "").lower()
    if len(p) < 4 or len(c) < 4:
        return True
    stem = p[:4]
    cands = [c] + [c[len(pre):] for pre in _GK_PREFIXES if c.startswith(pre)]
    return any(x.startswith(stem) for x in cands)

_ai_cache_ver: str | None = None  # computed once from prompt template + book list

# Bump this integer whenever server-side search logic changes in a way that
# affects results but doesn't change _AI_SYSTEM_TMPL (e.g. new fallback steps).
_CACHE_CODE_VER = 39   # 39: computed lexical-texture panel added to the payload (corpus_panel.py)


def _get_ai_cache_ver() -> str:
    """'search:<hash>' over (system prompt template + book list + code version).

    Automatically invalidates the DB cache when books are added, the system
    prompt changes, or _CACHE_CODE_VER is bumped. The 'search:' prefix is the
    unified scheme (core.ai_fingerprint) so each category prunes only its own rows.
    """
    global _ai_cache_ver
    if _ai_cache_ver is not None:
        return _ai_cache_ver
    conn = db()
    try:
        abbrevs = ",".join(
            r[0] for r in conn.execute("SELECT abbrev FROM books ORDER BY id").fetchall()
        )
    finally:
        conn.close()
    _ai_cache_ver = ai_fingerprint(
        "search", _AI_SYSTEM_TMPL, _CURATION_SYSTEM, f"books={abbrevs}", f"cv={_CACHE_CODE_VER}"
    )
    return _ai_cache_ver


def _cache_key(q: str) -> str:
    """Normalize a query so trivial differences — capitalization, surrounding or doubled
    punctuation, extra spaces — reuse the SAME cached answer instead of paying for an
    identical search. Only the cache key is normalized; the models still get the user's
    original wording, and the displayed question stays the user's own text."""
    s = re.sub(r"[^\w\s]", " ", (q or "").lower())   # punctuation → space
    return re.sub(r"\s+", " ", s).strip()             # collapse runs of whitespace


def _load_ai_cache_from_db() -> None:
    """Populate in-memory cache from DB; delete entries from a different version."""
    ver = _get_ai_cache_ver()
    try:
        conn = db()
        rows = conn.execute(
            "SELECT query, result_json FROM ai_search_cache WHERE ver_key = ?", (ver,)
        ).fetchall()
        for r in rows:
            try:
                _ai_cache[_cache_key(r["query"])] = json.loads(r["result_json"])
            except Exception:
                pass
        conn.close()
        # Prune ONLY this category's stale rows. Each other synthesis (summary, xref,
        # pn) prunes its own at startup, so we no longer carve them out by name here —
        # that old NOT-LIKE list is exactly what would wipe them under the new tags.
        deleted = ai_cache_prune("search", ver)
        log.info(
            "AI cache: loaded %d entries (ver=%s), pruned %d stale",
            len(rows), ver, deleted,
        )
    except Exception as exc:
        log.warning("Could not load AI cache from DB: %s", exc)


def _persist_ai_cache(query: str, payload: dict) -> None:
    """Write a single cache entry to the DB (fire-and-forget; errors are logged only)."""
    ai_cache_put(query, payload, _get_ai_cache_ver())


@bp.route("/api/ai-search")
@limiter.limit("200 per hour")
def ai_search():
    try:
        role, uid = ai_caller()
        if role == "nologin":
            return jsonify({"error": "Sign in to use AI search.", "login": True}), 401
        q = request.args.get("q", "").strip()
        # Optional conversation context (recent thread turns) for follow-up questions,
        # so references like "it" / "the same word" resolve. Capped; a follow-up is
        # thread-specific so it's never cached — it always runs fresh.
        context = request.args.get("context", "").strip()[:2000]
        log.debug("ai_search called: q=%r context=%r", q, context[:120])
        if not q:
            return jsonify({"error": "no query"}), 400

        if len(q) > 500:
            return jsonify({"error": "query too long (max 500 chars)"}), 400

        # Cache key — caps / punctuation / extra-space variants of the same question
        # share one answer ("Is hell the same as Sheol?" == "is hell the same as sheol").
        qk = _cache_key(q)

        if not context:
            cached = _ai_cache.get(qk)
            if cached is None:
                # The in-memory cache is a per-process snapshot taken at startup, and
                # PA runs several worker processes — so an answer ANOTHER worker just
                # saved isn't in THIS worker's copy. Fall back to the shared cache
                # table before paying for the models, and warm this worker's copy.
                cached = ai_cache_get(qk, _get_ai_cache_ver())
                if cached is not None:
                    _ai_cache[qk] = cached
            if cached is not None:
                log.debug("ai_search cache hit: q=%r", q)
                out = dict(cached)        # don't mutate the shared cached copy
                out["quota"] = ai_quota_status(role, uid)
                return jsonify(out)

        if not _anthropic:
            return jsonify({"error": "ANTHROPIC_API_KEY not set"}), 500

        # ── Daily spend guard: refuse BEFORE paying the models if this account, or
        # the whole site, has hit today's cap. Admin is exempt. Cached answers return
        # above this point, so re-reading them is always free. ───────────────────
        _block = ai_quota_blocked(role, uid)
        if _block:
            _kind, _limit = _block
            if _kind == "global":
                return jsonify({
                    "error": "Ask the corpus has reached today's limit for everyone — "
                             "it resets tomorrow. Saved answers still work.",
                    "global_capped": True}), 200
            return jsonify({
                "error": "You've used all your free searches for today — they reset tomorrow.",
                "capped": True, "remaining": 0, "limit": _limit,
                "quota": ai_quota_status(role, uid)}), 200

        # ── Timing instrument: one INFO line at the end shows where the
        # seconds go (cumulative from start). Temporary diagnostic. ──────────
        _t0 = time.perf_counter()
        _marks: dict[str, float] = {}
        def _mark(name: str) -> None:
            _marks[name] = round(time.perf_counter() - _t0, 2)

        # ── Step 1: extract key terms for LSJ lookup ──────────────────────
        log.debug("Step 1: extracting key terms…")
        terms_msg = _anthropic.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=80,
            temperature=0,
            messages=[{"role": "user", "content": (
                "Extract 3–6 key Greek lexical concepts (as simple English words) "
                "to look up in the Liddell-Scott-Jones Greek lexicon for this query. "
                "Include the primary term AND related vocabulary from all major "
                "manifestations of the concept — e.g. for divine beings include both "
                "titles (angel, holy one) and membership/kinship terms (son, child, assembly). "
                "Return ONLY a JSON array of lowercase English strings, "
                "e.g. [\"spirit\",\"breath\"]. No explanation.\n\n"
                + (f"Conversation context (resolve references against it): {context}\n" if context else "")
                + "Query: " + q
            )}],
        )
        try:
            terms = json.loads(terms_msg.content[0].text.strip())
            if not isinstance(terms, list):
                terms = []
        except Exception:
            terms = []
        log.debug("Extracted terms: %r", terms)
        _mark("terms")

        # ── Step 2: LSJ concept lookup ────────────────────────────────────
        lsj_entries = _lsj_concept_lookup(terms)
        lsj_context = _format_lsj_context(lsj_entries)
        _mark("lsj")
        log.debug("LSJ context (%d entries): %.200s", len(lsj_entries), lsj_context)

        # ── Step 3: SQL generation with LSJ context ───────────────────────
        if context:
            _ctx = ("CONVERSATION CONTEXT — the previous turn in this thread. Use it ONLY to "
                    "resolve references in the new question (\"it\", \"this word\", \"the same "
                    f"word\"); answer the NEW question:\n{context}")
            user_content = (f"{lsj_context}\n\n{_ctx}\n\nQuery: {q}" if lsj_context
                            else f"{_ctx}\n\nQuery: {q}")
        else:
            user_content = f"{lsj_context}\n\nQuery: {q}" if lsj_context else q
        log.debug("Calling Haiku for SQL generation…")
        msg = _anthropic.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1200,
            temperature=0,
            system=[{"type": "text", "text": _get_ai_system(), "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_content}],
        )
        raw = msg.content[0].text.strip() if msg.content else ""
        log.debug("Haiku raw response (stop=%s): %r", msg.stop_reason, raw[:300])
        _u = msg.usage
        log.info("cache[haiku-sqlgen]: fresh=%s write=%s read=%s",
                 _u.input_tokens,
                 getattr(_u, "cache_creation_input_tokens", 0),
                 getattr(_u, "cache_read_input_tokens", 0))
        _mark("sqlgen")

        if not raw:
            log.error("AI returned empty response (stop_reason=%s)", msg.stop_reason)
            return jsonify({"error": "The AI came back empty on that one — try rephrasing the question."}), 500

        # Extract the JSON object even if surrounded by prose or fences
        start = raw.find("{")
        end   = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = raw[start:end + 1]
        else:
            candidate = raw

        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as e:
            log.error("AI response not valid JSON: %s\nraw=%r", e, raw)
            return jsonify({"error": "I couldn't read the answer for that one — try rephrasing the question."}), 500

        if parsed.get("out_of_scope"):
            return jsonify({"out_of_scope": True, "explanation": parsed.get("explanation", "")}), 200

        sql         = _normalize_union_sql((parsed.get("sql") or "").strip())
        explanation = parsed.get("explanation", "")
        log.info("SQL from AI: %s", sql)

        # Extract key_strongs from AI response; fall back to LSJ lookup entries
        # Preserve original H/G prefix from AI before stripping digits
        _ks_raw = parsed.get("key_strongs") or []
        if not isinstance(_ks_raw, list):
            _ks_raw = []
        _ks_pairs_all: list[tuple[str, str | None]] = []
        for s in _ks_raw[:12]:
            s = str(s).strip()
            m = re.match(r'^([GgHh]?)(\d+(?:\.\d+)?)$', s)
            if m:
                orig = m.group(1).upper() if m.group(1) else None
                _ks_pairs_all.append((m.group(2), orig))
        # The AI reliably prefixes Strong's in its PROSE (e.g. "H1818 dam"); use
        # that to fill in any bare key_strongs numbers. The >5624 range heuristic
        # misfires on low Hebrew numbers (H1818 dam, H1285 berith) and would
        # resolve them as the Greek word of the same number (G1818 ἐξαπατάω).
        _expl_pref: dict[str, str] = {}
        for _pm, _pn in re.findall(r'\b([GHgh])(\d+(?:\.\d+)?)\b', explanation):
            _expl_pref.setdefault(_pn, _pm.upper())
        _ks_pairs_all = [(num, orig or _expl_pref.get(num)) for (num, orig) in _ks_pairs_all]

        def _is_heb(pair):
            sn, orig = pair
            if orig == "H": return True
            if orig == "G": return False
            return int(sn.split(".")[0]) > 5624
        greek_pairs = [p for p in _ks_pairs_all if not _is_heb(p)][:6]
        hebrew_pairs = [p for p in _ks_pairs_all if _is_heb(p)][:4]
        _ks_pairs = greek_pairs + hebrew_pairs
        if not _ks_pairs:
            _ks_pairs = [(e["strongs"], None) for e in lsj_entries[:6]]
        key_strongs_data: list[dict] = []
        if _ks_pairs:
            ks_conn = db_ro()
            try:
                for sn, orig_prefix in _ks_pairs:
                    # Use AI-provided prefix when present; fall back to range heuristic
                    if orig_prefix:
                        prefix = orig_prefix
                    else:
                        prefix = "H" if int(sn.split(".")[0]) > 5624 else "G"
                    if prefix == "H":
                        row = ks_conn.execute(
                            "SELECT lemma, xlit AS translit FROM bdb WHERE strongs_id = ?",
                            (f"H{sn}",)
                        ).fetchone()
                    else:
                        row = ks_conn.execute(
                            "SELECT lemma, translit, strongs_def, derivation FROM lexicon WHERE strongs = ?", (sn,)
                        ).fetchone()
                        # Fallback: bare number without prefix may be Hebrew — try BDB
                        if not row and not orig_prefix:
                            bdb_row = ks_conn.execute(
                                "SELECT lemma, xlit AS translit FROM bdb WHERE strongs_id = ?",
                                (f"H{sn}",)
                            ).fetchone()
                            if bdb_row:
                                row = bdb_row
                                prefix = "H"
                    if not row:
                        log.debug("key_strongs %s%s not found in DB — dropping", prefix, sn)
                        continue
                    key_strongs_data.append({
                        "strongs_base": sn,
                        "strongs": f"{prefix}{sn}",
                        "lemma":      row["lemma"] or "",
                        "translit":   row["translit"] or "",
                        "definition": (row["strongs_def"] if prefix == "G" else "") or "",
                        "derivation": (row["derivation"]  if prefix == "G" else "") or "",
                    })
            finally:
                ks_conn.close()

        # The lexical-texture panel assembles each family from the model's OWN heads —
        # snapshot them HERE, before the cognate/Hebrew/divine-council supplements below
        # expand key_strongs_data (the panel does its own family assembly; feeding it the
        # already-expanded list would double-count). Prefixed forms: ['G4442','H784'].
        _panel_heads = [e["strongs"] for e in key_strongs_data]

        # ── Citation guard ───────────────────────────────────────────────────
        # The bare base numbers of the target words (dots stripped), e.g.
        # {"4815","1818"}. Verses injected from the model's PROSE or its
        # "additional" list are checked against this: a verse that contains NONE
        # of the target words is THEMATIC (kept, but routed to "Additional
        # references", never shown as a direct word occurrence).
        # REGIME-AWARE: when there is no clear target word — a broad, non-word
        # question — the word-check can't apply, so nothing is flagged thematic on
        # that basis (the citable set would generalize to the retrieved verses
        # instead, for an expanded answer-anything mode).
        _target_bases = {e["strongs_base"].split(".")[0] for e in key_strongs_data}

        def _is_thematic(words):
            """True only when there IS a target-word set AND this verse contains
            none of it (so it's thematic, not lexical evidence)."""
            if not _target_bases:
                return False
            for wd in words:
                sb = (wd.get("strongs_base") or "").lstrip("GH").split(".")[0]
                if sb in _target_bases:
                    return False
            return True

        if not re.match(r"^\s*SELECT\b", sql, re.IGNORECASE):
            log.error("AI returned non-SELECT query: %r", sql)
            # Don't echo the generated SQL back to the client (info disclosure).
            return jsonify({"error": "The generated query was invalid — please rephrase and try again."}), 400

        # Pure multi-word PHRASE query (phrase LIKEs, no Strong's-number filter): the
        # word-gloss scan would burn ~6s on ~600k rows AND find nothing — a phrase is
        # not contiguous in the per-word gloss. Skip it; the phrase supplement below
        # finds these in the full verse text (~31k rows). Any Strong's-number filter
        # means it's a real word search, so run it normally.
        phrase_terms = [p for p in {m.lower().strip() for m in _LIKE_PHRASE_RE.findall(sql)}
                        if " " in p]
        has_strongs_filter = bool(
            re.search(r"strongs(?:_base)?\s*(?:=|\bIN\b)\s*\(?\s*'?\d", sql, re.IGNORECASE)
        )
        if phrase_terms and not has_strongs_filter:
            rows = []
            log.info("Skipped word-gloss scan for phrase-only query: %r", phrase_terms)
        else:
            conn = db_ro()
            _sql_t = time.perf_counter()
            try:
                rows = conn.execute(sql).fetchall()
            except Exception as e:
                # Log the SQL + DB error server-side only; never return them to the client.
                log.error("SQL execution error: %s\nSQL: %s", e, sql)
                return jsonify({"error": "The search query could not be run — please rephrase and try again."}), 400
            finally:
                conn.close()
            _sql_secs = time.perf_counter() - _sql_t
            if _sql_secs > 10:
                # The DB step normally runs in well under 1s; minutes means a stall
                # (contention/locked file) or a pathological query. Make it loud +
                # self-contained so a repeat is one grep: "SLOW SQL".
                log.warning("SLOW SQL: %.1fs, %d rows | %s", _sql_secs, len(rows), sql)
        log.debug("SQL returned %d rows", len(rows))
        _mark("sqlrun")

        # ── Group word-level rows into one entry per verse ───────────────────
        # The broaden-and-retry now runs as a LAST resort below (after the cheap
        # explanation-citation + proper-noun fallbacks), so it no longer fires a
        # wasted ~5s call when those already surfaced verses to show.
        verse_index, verse_order, results = _group_word_rows(rows)
        log.debug("Grouped into %d verses", len(results))

        # ── Same-root cognate supplement ─────────────────────────────────────
        # The verses come from the model's SQL, which often searches only the head
        # word and misses its own family — a "sabbath" search finds σάββατον (G4521)
        # but not σαββατισμός (G4520, Heb 4:9). Deterministically pull each GREEK
        # target's same-root relatives (lexicon etymology, _greek_cognates) so the
        # family is searched + chipped no matter what the model wrote. A relative
        # earns a chip ONLY if it actually occurs (no dead chips), capped so a big
        # family can't flood; the synth still names one only if its verse gets picked.
        # Greek only (BDB has no etymology). Never fatal — a hiccup leaves results as-is.
        try:
            _orig_greek = [e for e in key_strongs_data if e["strongs"].startswith("G")]
            if _orig_greek:
                cog_conn = db_ro()
                new_cog: list = []
                added = 0
                try:
                    for e in _orig_greek:
                        if added >= _COGNATE_CHIP_CAP:
                            break
                        for c in _greek_cognates(cog_conn, e["strongs_base"].split(".")[0], e.get("derivation", "")):
                            if added >= _COGNATE_CHIP_CAP:
                                break
                            cbase = c["strongs"].lstrip("GgHh").split(".")[0]
                            if cbase in _target_bases:
                                continue
                            if not _cognate_is_tight(e.get("lemma", ""), c.get("lemma", "")):
                                continue          # buried-root drift (e.g. εἰλικρινής off κρίνω)
                            occ = cog_conn.execute(
                                "SELECT DISTINCT v.book, v.chapter, v.verse, v.id AS vid "
                                "FROM words w JOIN verses v ON w.verse_id = v.id "
                                "WHERE w.strongs_base = ? ORDER BY v.id LIMIT ?",
                                (f"G{cbase}", _COGNATE_VERSE_CAP),
                            ).fetchall()
                            if not occ:
                                continue              # not in the corpus → no dead chip
                            _target_bases.add(cbase)  # a real target now: grounded + highlighted
                            key_strongs_data.append({
                                "strongs_base": cbase,
                                "strongs":      f"G{cbase}",
                                "lemma":        c.get("lemma", ""),
                                "translit":     c.get("translit", ""),
                                "definition":   c.get("gloss", ""),
                                "derivation":   "",
                            })
                            added += 1
                            for pr in occ:
                                key = (pr["book"], pr["chapter"], pr["verse"])
                                if key in verse_index:
                                    continue
                                words = _fetch_verse_words(cog_conn, pr["vid"])
                                if words:
                                    verse_index[key] = {
                                        "ref": f"{pr['book']} {pr['chapter']}:{pr['verse']}",
                                        "book": pr["book"], "chapter": pr["chapter"], "verse": pr["verse"],
                                        "words": words,
                                    }
                                    new_cog.append(key)
                finally:
                    cog_conn.close()
                if new_cog:
                    results = results + [verse_index[k] for k in new_cog]
                    log.info("Cognate supplement: +%d chip(s), +%d verse(s)", added, len(new_cog))
        except Exception as e:
            log.warning("cognate supplement failed: %s", e)
        _mark("cognates")

        # ── Hebrew OT occurrence supplement (heb.db) ──────────────────────────
        # A Hebrew target's occurrences come from the REAL Hebrew OT (heb_words), not
        # the KJV's Strong's tagging the model's SQL bridges through. For each H-number
        # in the key words, pull a canonical SPREAD of its heb.db verses and inject them,
        # tagging each with the H-number so the citation guard + gold highlight count it
        # as a real occurrence. heb.db reads are guarded — a missing heb.db just leaves the
        # model's bridged results untouched. Never fatal.
        try:
            _heb_targets = [e for e in key_strongs_data if e["strongs"].startswith("H")]
            if _heb_targets:
                try:
                    hconn = heb_db()
                except Exception:
                    hconn = None
                if hconn is not None:
                    new_heb: list = []
                    hdb_conn = db_ro()
                    try:
                        for e in _heb_targets:
                            sid = e["strongs"]                      # "H7307"
                            base = e["strongs_base"].split(".")[0]  # "7307"
                            try:
                                occ = hconn.execute(
                                    "SELECT book, chapter, verse, gloss, translit FROM heb_words "
                                    "WHERE strongs = ? OR strongs GLOB ? "
                                    "GROUP BY book, chapter, verse ORDER BY book, chapter, verse",
                                    (sid, sid + "[A-Za-z]"),
                                ).fetchall()
                            except Exception:
                                occ = []
                            if not occ:
                                continue
                            # Round-robin across books for a canonical spread, capped.
                            by_book: dict = {}
                            for r in occ:
                                by_book.setdefault(r["book"], []).append(r)
                            spread, depth = [], 0
                            while len(spread) < _HEB_VERSE_CAP:
                                progressed = False
                                for b in by_book:
                                    if depth < len(by_book[b]):
                                        spread.append(by_book[b][depth])
                                        progressed = True
                                        if len(spread) >= _HEB_VERSE_CAP:
                                            break
                                if not progressed:
                                    break
                                depth += 1
                            _target_bases.add(base)   # grounded + highlighted
                            for r in spread:
                                key = (r["book"], r["chapter"], r["verse"])
                                marker = {
                                    "strongs": sid, "strongs_base": sid,   # H-prefixed: _is_thematic + cited match
                                    "is_function": False,
                                    "gloss": (r["gloss"] or "").strip(),
                                    "lemma": e.get("lemma", ""),
                                    "translit": e.get("translit", "") or (r["translit"] or ""),
                                    "strongs_def": "", "kjv_def": "", "derivation": "",
                                }
                                if key in verse_index:
                                    ws = verse_index[key].setdefault("words", [])
                                    if not any((w.get("strongs_base") or "").lstrip("GH").split(".")[0] == base for w in ws):
                                        ws.append(marker)
                                else:
                                    vrow = hdb_conn.execute(
                                        "SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?", key
                                    ).fetchone()
                                    if not vrow:
                                        continue   # ABP versification lacks this verse — can't display it
                                    words = _fetch_verse_words(hdb_conn, vrow["id"])
                                    verse_index[key] = {
                                        "ref": f"{r['book']} {r['chapter']}:{r['verse']}",
                                        "book": r["book"], "chapter": r["chapter"], "verse": r["verse"],
                                        "words": (words or []) + [marker],
                                    }
                                    new_heb.append(key)
                    finally:
                        hdb_conn.close()
                        hconn.close()
                    if new_heb:
                        results = results + [verse_index[k] for k in new_heb]
                        log.info("Hebrew supplement: +%d verse(s) from heb.db", len(new_heb))
        except Exception as e:
            log.warning("Hebrew supplement failed: %s", e)
        _mark("hebrew")

        # ── Fetch verses cited in the explanation that SQL missed ─────────────
        cited_keys: set = set()
        for book_raw, chap_str, verse_str in _get_verse_ref_re().findall(explanation):
            cited_keys.add((_norm_book(book_raw), int(chap_str), int(verse_str)))

        if cited_keys:
            cited_conn = db_ro()
            new_cited = []
            try:
                for key in cited_keys:
                    if key in verse_index:
                        continue
                    book, chapter, verse_num = key
                    vrow = cited_conn.execute(
                        "SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
                        (book, chapter, verse_num),
                    ).fetchone()
                    if not vrow:
                        continue
                    words = _fetch_verse_words(cited_conn, vrow["id"])
                    if words:
                        verse_index[key] = {
                            "ref": f"{book} {chapter}:{verse_num}",
                            "book": book, "chapter": chapter, "verse": verse_num,
                            "words": words,
                            "is_thematic": _is_thematic(words),
                        }
                        new_cited.append(key)
                        log.debug("Cited verse fetched: %s %d:%d", book, chapter, verse_num)
            finally:
                cited_conn.close()
            if new_cited:
                results = [verse_index[k] for k in new_cited] + results

        # ── Step 3.5: Proper noun supplement (english LIKE fallback) ─────────
        # Proper nouns in ABP are tagged strongs='*' and invisible to Strong's-based SQL.
        # Extract capitalized words from the query and query the english field directly,
        # adding any new verses to the result pool before pass-2 curation.
        # GATE: this scans ~600k word-glosses, so only run it when the main search came
        # up THIN (its real job — rescuing a name query). A common capitalized word like
        # "Sabbath" already has a Strong's number and returns plenty, so the scan there
        # is pure waste (~7s) — skip it.
        proper_nouns = _extract_proper_nouns(q)
        if proper_nouns and len(results) < _PROPER_NOUN_NEED:
            like_clauses = " OR ".join("w.english LIKE ?" for _ in proper_nouns)
            pn_sql = f"""
                SELECT DISTINCT v.book, v.chapter, v.verse, v.id AS vid
                FROM words w
                JOIN verses v ON w.verse_id = v.id
                WHERE {like_clauses}
                ORDER BY v.id
                LIMIT 300
            """
            pn_params = [f"%{pn}%" for pn in proper_nouns]
            pn_conn = db_ro()
            new_pn: list = []
            try:
                for pr in pn_conn.execute(pn_sql, pn_params).fetchall():
                    key = (pr["book"], pr["chapter"], pr["verse"])
                    if key in verse_index:
                        continue
                    words = _fetch_verse_words(pn_conn, pr["vid"])
                    if words:
                        verse_index[key] = {
                            "ref": f"{pr['book']} {pr['chapter']}:{pr['verse']}",
                            "book": pr["book"],
                            "chapter": pr["chapter"],
                            "verse": pr["verse"],
                            "words": words,
                        }
                        new_pn.append(key)
            finally:
                pn_conn.close()
            if new_pn:
                results = results + [verse_index[k] for k in new_pn]
                log.debug("Proper noun supplement: +%d verses for %s", len(new_pn), proper_nouns)

        # ── Step 3.6: Phrase supplement — search the FULL verse text ──────────
        # The AI writes a phrase as `english LIKE '%son of perdition%'`, but the
        # word-gloss splits + reorders phrases, so that scans all ~600k words AND
        # misses. Re-run the AI's OWN multi-word phrases against the readable verse
        # text (verses.text + KJV + BSB, ~31k rows each) in code — no AI-written SQL — and
        # merge any verses found. A verse whose text literally contains the phrase is
        # a real occurrence, so it is not thematic.
        phrase_hits = False
        if phrase_terms:
            cand: set = set()
            new_phrase: list = []
            pf_conn = db_ro()
            try:
                for ph in phrase_terms:
                    like = f"%{ph}%"
                    for r in pf_conn.execute(
                        "SELECT book, chapter, verse FROM verses "
                        "WHERE text LIKE ? COLLATE NOCASE LIMIT 200", (like,)
                    ).fetchall():
                        cand.add((r["book"], r["chapter"], r["verse"]))
                    for r in pf_conn.execute(
                        "SELECT b.abbrev AS book, kv.chapter AS chapter, kv.verse_num AS verse "
                        "FROM kjv_verses kv JOIN books b ON b.id = kv.book_id "
                        "WHERE kv.verse_text LIKE ? COLLATE NOCASE LIMIT 200", (like,)
                    ).fetchall():
                        cand.add((r["book"], r["chapter"], r["verse"]))
                    # BSB = the app's default modern English; a phrase worded the
                    # modern way can match BSB even when neither ABP nor KJV phrases
                    # it that way. bsb_verses is an optional load, so a missing table
                    # on an older db is skipped, not fatal.
                    try:
                        for r in pf_conn.execute(
                            "SELECT b.abbrev AS book, bv.chapter AS chapter, bv.verse_num AS verse "
                            "FROM bsb_verses bv JOIN books b ON b.id = bv.book_id "
                            "WHERE bv.verse_text LIKE ? COLLATE NOCASE LIMIT 200", (like,)
                        ).fetchall():
                            cand.add((r["book"], r["chapter"], r["verse"]))
                    except sqlite3.OperationalError:
                        pass
                for key in cand:
                    if key in verse_index:
                        continue
                    book, chapter, verse_num = key
                    vrow = pf_conn.execute(
                        "SELECT id FROM verses WHERE book=? AND chapter=? AND verse=?",
                        (book, chapter, verse_num),
                    ).fetchone()
                    if not vrow:
                        continue
                    words = _fetch_verse_words(pf_conn, vrow["id"])
                    if words:
                        verse_index[key] = {
                            "ref": f"{book} {chapter}:{verse_num}",
                            "book": book, "chapter": chapter, "verse": verse_num,
                            "words": words,
                            "is_thematic": False,
                        }
                        new_phrase.append(key)
            finally:
                pf_conn.close()
            if new_phrase:
                phrase_hits = True
                results = results + [verse_index[k] for k in new_phrase]
                log.debug("Phrase supplement: +%d verses for %r", len(new_phrase), phrase_terms)

        # ── Last-resort retry: only if SQL + the cheap fallbacks ALL came up empty ──
        # Firing this the instant the first SQL was empty cost a wasted ~5s model call
        # whenever the explanation's cited verses or a proper-noun match already filled
        # results. Now it runs only when there is genuinely nothing to show.
        if not results:
            try:
                retry_msg = _anthropic.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1200,
                    temperature=0,
                    system=[{"type": "text", "text": _get_ai_system(), "cache_control": {"type": "ephemeral"}}],
                    messages=[
                        {"role": "user", "content": user_content},
                        {"role": "assistant", "content": raw},
                        {"role": "user", "content": (
                            "That SQL returned 0 results. Broaden the approach: "
                            "remove strict co-occurrence subqueries, expand to more "
                            "Strong's numbers via UNION ALL, or fall back to "
                            "english LIKE matching. Return the same JSON format."
                        )},
                    ],
                )
                retry_raw = retry_msg.content[0].text.strip()
                r_start = retry_raw.find("{")
                r_end   = retry_raw.rfind("}")
                if r_start != -1 and r_end > r_start:
                    retry_parsed = json.loads(retry_raw[r_start:r_end + 1])
                    retry_sql = _normalize_union_sql(retry_parsed.get("sql", "").strip())
                    if re.match(r"^\s*SELECT\b", retry_sql, re.IGNORECASE):
                        retry_conn = db_ro()
                        try:
                            retry_rows = retry_conn.execute(retry_sql).fetchall()
                        except Exception:
                            retry_rows = []
                        finally:
                            retry_conn.close()
                        if retry_rows:
                            sql = retry_sql
                            explanation = retry_parsed.get("explanation", explanation)
                            r_index, _, results = _group_word_rows(retry_rows)
                            verse_index.update(r_index)
                            log.debug("Retry SQL returned %d rows -> %d verses",
                                      len(retry_rows), len(results))
            except Exception as exc:
                log.warning("AI search retry failed: %s", exc)
        _mark("retry")

        # ── Pass 2 + assembly, STREAMED ───────────────────────────────────────
        # The synthesis is the dominant slice and the last thing produced, so we stream
        # it instead of making the reader wait for the whole answer: the panel (already
        # known from the pre-pass-2 key words) goes out FIRST, the synthesis prose streams
        # live as Sonnet writes it, and the verse evidence lands at the tail. The fail-
        # closed pick-parse (_parse_curation) sits IN FRONT of the reorder — a malformed
        # tail never marks wrong verses, it re-runs the non-streamed curate for clean
        # picks. Cache hits returned above this point stay one-lump (no streaming).
        small_pool  = len(results) <= _CURATE_SKIP_MAX
        cites_verse = bool(_get_verse_ref_re().findall(explanation))
        pass1_expl  = explanation        # the from-memory floor of last resort

        def _gen():
            expl = pass1_expl
            primary_raw, additional_raw = [], []
            try:
                # Panel first — independent of curation (it only needs the pre-pass-2 heads).
                try:
                    _panel = corpus_panel.build_panel(_panel_heads)
                except Exception as _pe:     # belt-and-suspenders — build_panel self-guards
                    log.warning("corpus panel failed: %s", _pe)
                    _panel = None
                yield _sse("panel", {"panel": _panel})
                _mark("panel")

                # The synthesis streams live. The floor (_parse_curation) decides the
                # picks; a bad tail re-runs the non-streamed curate for clean picks and
                # keeps the streamed prose — never a wrong-verse split.
                if not small_pool or cites_verse:
                    cur = _stream_curation(q, results, key_strongs_data)
                    res = None
                    try:
                        while True:
                            yield _sse("delta", {"t": next(cur)})
                    except StopIteration as stop:
                        res = stop.value
                    if res is None:
                        pass                  # nothing to curate — keep the pass-1 prose
                    elif res[0] is None:
                        # streamed tail unparseable → FLOOR: clean picks from the non-streamed curate
                        primary_raw, additional_raw, _fe = _curate_primary_verses(q, results, key_strongs_data)
                        expl = res[2] or _fe or expl
                    else:
                        primary_raw, additional_raw, curated = res
                        if curated:
                            expl = curated
                    if small_pool:            # small pool: show them all, ranking is moot
                        primary_raw = [v["ref"] for v in results]
                        additional_raw = []
                else:
                    primary_raw = [v["ref"] for v in results]
                    additional_raw = []
                    log.debug("Pass-2 skipped (%d verses, prose cites no verse) — showing all", len(results))
                _mark("curate")

                payload = _assemble_payload(
                    q, results, verse_index, key_strongs_data,
                    primary_raw, additional_raw, expl, rows, phrase_hits, _target_bases, _panel,
                )
                if not context:               # follow-ups are thread-specific — don't cache
                    _ai_cache[qk] = payload
                    _persist_ai_cache(qk, payload)
                ai_quota_count(role, uid)     # record the paid call (admin exempt; cache hits never reach here)
                _mark("total")
                log.info("ai_search timing q=%r rows=%d ctx=%d | %s", q, len(rows), len(context), _marks)
                out = dict(payload)           # per-account quota rides the response, not the shared cache
                out["quota"] = ai_quota_status(role, uid)
                yield _sse("done", out)
            except Exception:
                log.error("Streamed ai_search failed:\n%s", traceback.format_exc())
                yield _sse("error", {"error": "Internal server error — see console for details"})

        # X-Accel-Buffering: no is the whole fix for the dump — it tells PA's nginx not to
        # buffer the response. The path already streams (proved by /api/_streamtest).
        return Response(
            stream_with_context(_gen()),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    except Exception:
        log.error("Unhandled exception in ai_search:\n%s", traceback.format_exc())
        return jsonify({"error": "Internal server error — see console for details"}), 500
