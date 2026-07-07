#!/usr/bin/env python3
"""
build_lexica_def.py — build the Lexica dictionary entries (verse-grounded word definitions).

Productized from the proven trial rig (scripts/trial_lexica_def.py). For each target word it
runs the FROZEN verse engine (VERSE_PROMPT + Sonnet) over a testament-balanced spread of the
word's real occurrences, splits the resulting prose into display fields, runs the citation gate,
appends the contested-word fork (membership-only, model-free), and writes ONE row per word into
the `lexica_def` side table in bible.db.

PA-ONLY (bible.db lives on PA). Reads words / verses / abp_surface / lexicon for the evidence;
WRITES ONLY its own table `lexica_def` (CREATE IF NOT EXISTS + INSERT OR REPLACE) — it never
touches words or verses. Safe to re-run: a row is rebuilt only when the prompt/splitter stamp
changed, or with --force. The raw model output is stored alongside the fields, so an improved
splitter can re-split from the stored text with NO new model call (--resplit).

  workon bible-env
  export ANTHROPIC_API_KEY=$(grep -oE "sk-ant-[A-Za-z0-9_-]+" /var/www/www_lexica_bible_wsgi.py)
  python scripts/build_lexica_def.py --dry-run --word G5590     # generate + split, SHOW the fields, no write
  python scripts/build_lexica_def.py --dry-run                  # both pilot words, show fields, no write
  python scripts/build_lexica_def.py --apply                    # generate + WRITE the pilot words
  python scripts/build_lexica_def.py --apply --word G1344       # one word
  python scripts/build_lexica_def.py --resplit --apply          # re-split stored raw into fields, no model call

The engine (VERSE_PROMPT, select_spread, the citation gate, the CONTESTED fork register) is a
verbatim lift of the trial rig — the proven parts. The NEW code here is split_definition()
(prose -> fields), the verses[]/fork assembly, and the table write.

DRAW CACHE (review-what-ships): --dry-run saves the model's prose to ~/bible-db/draws/G####.json;
--apply reads that file (no model call) so the reviewed prose is the shipped prose, byte-for-byte.
Keyed on a hash of the exact model input (prompt + fed sample + model), recomputed live at apply —
a stale draw (input moved) is ignored, an edited draw (prose changed since review) is hard-refused.
--require-cache refuses a word with no reviewed draw (default ON under --all; opt out with
--allow-unreviewed). --force always draws fresh and refreshes the cache. The split/gate/validate
chain runs identically on cached prose — the cache changes WHAT is gated, never WHETHER.
"""

import argparse, datetime, hashlib, html, json, os, re, sqlite3, sys, unicodedata
from collections import OrderedDict, Counter

# ── build set: psyche (control, fork-absent) + the 5 frozen contested forks. psyche + dikaioo are
# already built (they skip on a stamp match); charis (G5484 — the number ABP actually tags, second
# live graph baptism_who), aionios, sarx, ekklesia are the four remaining forks — already audited +
# frozen, so building them is pure pipe-exercise: the splitter and the loud-fail guard get their
# first run on words they weren't tuned on, with zero new authoring risk.
PILOT = ["G5590", "G1344", "G5484", "G166", "G4561", "G1577"]

MODEL_SONNET = "claude-sonnet-4-6"   # the verse-grounded definition engine
BUDGET       = 40                    # occurrences fed to the engine
MAX_TOKENS   = 3000                  # output ceiling. Was 1500 — too low: it cut psyche's last gloss
                                     # note off mid-sentence (a 5-sense, ref-dense entry runs long).
                                     # Deliberately NOT in synth_ver(), so raising it does NOT
                                     # force-regenerate entries that came back complete — re-run a
                                     # truncated word on its own with --force.
SPLIT_VER    = "split3"              # which split_definition() wrote a row (stored for traceability; NOT in the skip-stamp).
                                     # split3: sense headers parsed bold OR plain-numbered (was bold-only;
                                     # a plain-numbered draw produced an empty glance -> validate refused).

OCC_MIN = 2   # verse-grounded entries need a real distribution to characterize a range; a hapax
              # (1×) has none, so it's left to the LSJ card. No CLI bypass — building one means
              # editing this constant on purpose (audit A1, 2026-07-01).

# ── Option B — LXX provenance flag. A Greek card's OT citations are all Septuagint (ABP's OT IS
# the LXX), so a sense grounded heavily in OT verses is resting on translation-Greek, not native
# Koine. We flag that with a subordinate "rests on Septuagint usage" note so a reader doesn't read
# NT behavior into a sense the LXX carries. PURE DERIVATION from the stored citations (each ref's
# book = OT or NT) — no model, no new data, recomputed every build/--resplit. Fires only on a HIGH,
# well-attested OT share, set against the real census (2026-06-25): >= 80% OT AND >= 4 OT refs.
# The 4-ref floor drops thin 3/0 senses where "rests on the LXX" would over-claim on too few
# verses (the count-lies rule) — it cost one real thin Hebraism (logos "matter", dabar) on purpose.
LXX_THRESHOLD = 80   # a sense's cited verses must be at least this % OT (Septuagint)
LXX_MIN_OT    = 4    # AND carry at least this many OT refs, so the claim isn't made on a thin sample

# ── PROMPT — VERSE-GROUNDED definition (Sonnet). v3 (promoted 2026-06-25, after the 3 frame-leaker
# cores were hand-pinned): adds the sub-use test (same-job vs different-job) + a symmetric
# no-over-split/no-over-merge constraint. Proven 0/10 format stutter across the six in the agreement
# reviewer. KEEP IN SYNC with lexica_agreement.V3_PROMPT (the reviewer soft-asserts they match). ───
VERSE_PROMPT = """\
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

NT_BOOKS = {"Mat","Mar","Luk","Joh","Act","Rom","1Co","2Co","Gal","Eph","Php","Col",
            "1Th","2Th","1Ti","2Ti","Tit","Phm","Heb","Jas","1Pe","2Pe","1Jn","2Jn","3Jn","Jud","Rev"}

# ── THE CONTESTED-WORD FAIRNESS GATE — the hand-authored fork register. Moved to
# contested_register.py (repo root) 2026-07-01 so the build, the serving route (views_lexica.py:
# the serve-time fork backstop + the G5485 alias), and the rigs all read ONE copy.
# _CONTESTED_BY_SID kept as a module name: lexica_agreement.py reads B._CONTESTED_BY_SID.
# The path insert: `python scripts/build_lexica_def.py` starts its module search in scripts/,
# and the shared register lives one level up at the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from contested_register import CONTESTED, CONTESTED_BY_SID
import lexica_coverage
_CONTESTED_BY_SID = CONTESTED_BY_SID


# ══════════════════════════════════════════════════════════════════════════════════════════════
# Proven helpers — VERBATIM from the trial rig (evidence gathering, sampler, citation gate).
# ══════════════════════════════════════════════════════════════════════════════════════════════
def get_key():
    k = os.environ.get("ANTHROPIC_API_KEY")
    if k:
        return k
    env = os.path.expanduser("~/bible-db/.env")
    if os.path.exists(env):
        for line in open(env):
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("No ANTHROPIC_API_KEY. Export it (copy from /var/www/www_lexica_bible_wsgi.py) "
             "or add a line to ~/bible-db/.env, then re-run. (Or use --resplit to skip the model.)")


def strip_accents(s):
    if s is None:
        return s
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def strip_html(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def table_exists(conn, name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (name,)).fetchone() is not None


def abp_filter(conn, sid):
    """WHERE predicate for a clean base G-number (excludes dotted variants)."""
    if table_exists(conn, "dotted_lexicon"):
        return ("w.strongs_base = ? AND 'G' || w.strongs NOT IN (SELECT strongs FROM dotted_lexicon)", [sid])
    return ("w.strongs_base = ?", [sid])


def gloss_set(conn, pred, params):
    """The 'renders as' set: single-word english_head renderings with counts."""
    rows = conn.execute(f"""
        SELECT w.english_head AS g, COUNT(*) AS c
        FROM words w
        WHERE {pred} AND w.english_head IS NOT NULL AND w.english_head != ''
        GROUP BY w.english_head ORDER BY c DESC
    """, params).fetchall()
    return [(r["g"], r["c"]) for r in rows if " " not in r["g"]]


def occurrences(conn, pred, params):
    return conn.execute(f"""
        SELECT v.book AS book, v.chapter AS ch, v.verse AS vs,
               w.english_head AS rend, w.verse_id AS vid, w.position AS pos
        FROM verses v JOIN words w ON w.verse_id = v.id
        WHERE {pred}
        ORDER BY v.id, w.position
    """, params).fetchall()


def lex_head(conn, sid):
    """(lemma, translit) for a G-number from the lexicon. Falls back to (sid, '')."""
    r = conn.execute("SELECT lemma, translit FROM lexicon WHERE strongs_g = ?", (sid,)).fetchone()
    if not r:
        return sid, ""
    return (r["lemma"] or sid), (r["translit"] or "")


def select_spread(occs, budget):
    """Sample that surfaces the SENSE range: per-rendering floor + proportional fill, balancing
    testament (OT/NT) then book. VERBATIM from the trial rig."""
    groups = OrderedDict()
    for o in occs:
        groups.setdefault((o["rend"] or "").lower(), []).append(o)
    by_freq = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    n = len(by_freq)
    if n == 0:
        return []
    counts = {rend: len(g) for rend, g in by_freq}
    used_t = Counter()
    used_b = Counter()
    taken_ids = set()
    taken = Counter()
    selected = []

    def tm(o):
        return "NT" if o["book"] in NT_BOOKS else "OT"

    def pick(g):
        rem = [o for o in g if id(o) not in taken_ids]
        if not rem:
            return None
        return min(rem, key=lambda o: (used_t[tm(o)], used_b[o["book"]]))

    def add(rend, o):
        taken_ids.add(id(o)); taken[rend] += 1
        used_t[tm(o)] += 1; used_b[o["book"]] += 1; selected.append(o)

    if n > budget:
        order, lo, hi = [], 0, n - 1
        while lo <= hi and len(order) < budget:
            order.append(by_freq[hi]); hi -= 1
            if lo <= hi and len(order) < budget:
                order.append(by_freq[lo]); lo += 1
        for rend, g in order:
            o = pick(g)
            if o is not None:
                add(rend, o)
    else:
        floor = max(1, min(3, budget // (2 * n)))
        for rend, g in by_freq:
            for _ in range(min(floor, counts[rend])):
                if len(selected) >= budget:
                    break
                o = pick(g)
                if o is not None:
                    add(rend, o)

    while len(selected) < budget:
        cand = [(rend, g) for rend, g in by_freq if taken[rend] < counts[rend]]
        if not cand:
            break
        rend, g = max(cand, key=lambda rg: counts[rg[0]] / (taken[rg[0]] + 1))
        o = pick(g)
        if o is None:
            counts[rend] = taken[rend]
            continue
        add(rend, o)
    return sorted(selected, key=lambda o: o["vid"])


def fetch_context(conn, occs, has_surface):
    out = []
    for o in occs:
        row = conn.execute("SELECT text FROM verses WHERE id=?", (o["vid"],)).fetchone()
        prose = (row["text"] if row else "") or ""
        form = ""
        if has_surface:
            s = conn.execute("SELECT form, translit FROM abp_surface WHERE verse_id=? AND position=?",
                             (o["vid"], o["pos"])).fetchone()
            if s and s["form"]:
                form = s["form"] + (f" ({s['translit']})" if s["translit"] else "")
        out.append((o["book"], o["ch"], o["vs"], o["rend"], form, prose))
    return out


def verse_user_msg(sid, translit, gset, ctx):
    lines = [f"LEMMA: {sid}  ({translit})", ""]
    lines.append("TRANSLATION GLOSS SET (one translation's renderings, with counts):")
    lines.append("  " + "; ".join(f"{g} ({c})" for g, c in gset[:25]))
    lines.append("")
    lines.append(f"OCCURRENCES ({len(ctx)}) - context is the primary evidence; rendered-here word in [ ]:")
    for book, ch, vs, rend, form, prose in ctx:
        tag = f'[here: "{rend}"' + (f"; form: {form}" if form else "") + "]"
        lines.append(f"  {book} {ch}:{vs} {tag}")
        lines.append(f"     {prose}")
    return "\n".join(lines)


# ── Book-label → canonical verses.book code. EXACT-STRING LOOKUP ONLY — NO FALLBACK OF ANY KIND.
# "Jud" is the canonical code for Jude, but it is also the natural three-letter prefix of "Judges"
# (code Jdg); any prefix, first-N-letters, or fuzzy fallback would silently file a Judges citation
# under Jude. So every accepted spelling is an explicit key mapping to exactly one code, an
# unrecognized label resolves to nothing and is rejected, and a code is never guessed from a partial
# match. Keys are looked up after lowercasing + removing internal spaces (so "1 Chronicles",
# "1Chronicles", "1chr" all reach one key) — that is key canonicalization, not fallback; no partial
# or approximate match ever succeeds. Covers ALL 66 verses.book codes explicitly (replaced the old
# 3-letter-only _REF_RE + numbered-only _NUM_STEM, which missed every spelled-out book name — the
# "Ruth"→Rth reject, 2026-07-03).
_BOOK_CODE, _BOOK_SURFACES = {}, []
def _reg(code, *labels):
    for s in (code,) + labels:
        _BOOK_CODE[re.sub(r"\s+", "", s).lower()] = code
        _BOOK_SURFACES.append(s)

_reg("Gen","Genesis");            _reg("Exo","Exodus","Exod");        _reg("Lev","Leviticus")
_reg("Num","Numbers");            _reg("Deu","Deuteronomy","Deut");   _reg("Jos","Joshua","Josh")
_reg("Jdg","Judges","Judg");      _reg("Rth","Ruth");                 _reg("1Sa","1 Samuel","1 Sam")
_reg("2Sa","2 Samuel","2 Sam");   _reg("1Ki","1 Kings","1 Kgs");      _reg("2Ki","2 Kings","2 Kgs")
_reg("1Ch","1 Chronicles","1 Chron","1 Chr"); _reg("2Ch","2 Chronicles","2 Chron","2 Chr")
_reg("Ezr","Ezra");               _reg("Neh","Nehemiah");             _reg("Est","Esther")
_reg("Job");                      _reg("Psa","Psalms","Psalm","Ps","Pss"); _reg("Pro","Proverbs","Prov")
_reg("Ecc","Ecclesiastes","Eccl"); _reg("Son","Song","Song of Songs","Song of Solomon","SoS","Canticles")
_reg("Isa","Isaiah");             _reg("Jer","Jeremiah");             _reg("Lam","Lamentations")
_reg("Eze","Ezekiel","Ezek");     _reg("Dan","Daniel");               _reg("Hos","Hosea")
_reg("Joe","Joel");               _reg("Amo","Amos");                 _reg("Oba","Obadiah","Obad")
_reg("Jon","Jonah");              _reg("Mic","Micah");                _reg("Nah","Nahum")
_reg("Hab","Habakkuk");           _reg("Zep","Zephaniah","Zeph");     _reg("Hag","Haggai")
_reg("Zec","Zechariah","Zech");   _reg("Mal","Malachi")
_reg("Mat","Matthew","Matt","Mt"); _reg("Mar","Mark","Mk");           _reg("Luk","Luke","Lk")
_reg("Joh","John","Jn","Jhn");    _reg("Act","Acts");                 _reg("Rom","Romans")
_reg("1Co","1 Corinthians","1 Cor"); _reg("2Co","2 Corinthians","2 Cor"); _reg("Gal","Galatians")
_reg("Eph","Ephesians");          _reg("Php","Philippians");          _reg("Col","Colossians")
_reg("1Th","1 Thessalonians","1 Thess"); _reg("2Th","2 Thessalonians","2 Thess")
_reg("1Ti","1 Timothy","1 Tim");  _reg("2Ti","2 Timothy","2 Tim");    _reg("Tit","Titus")
_reg("Phm","Philemon","Phlm");    _reg("Heb","Hebrews");              _reg("Jas","James")
_reg("1Pe","1 Peter","1 Pet");    _reg("2Pe","2 Peter","2 Pet");      _reg("1Jn","1 John","1 Jn")
_reg("2Jn","2 John","2 Jn");      _reg("3Jn","3 John","3 Jn");        _reg("Jud","Jude")
_reg("Rev","Revelation","Apoc","Apocalypse")
# Deliberate omissions (ambiguous — require the fuller spelling): bare "Jud" stays Jude (Judges must
# be "Judges"/"Jdg"); bare "Phil" is left unmapped (Philippians vs Philemon); "Jam" is not a key.

# The citation catcher: one of the KNOWN labels (a closed set) followed by ch:vs. Longest-first so
# "Genesis" wins over "Gen" and "1 Corinthians" over "1Co". CASE-SENSITIVE on purpose — a citation
# is always capitalized, so lowercase prose ("act 3:4") can never match, and the closed alternation
# can't grab an arbitrary capitalized word either.
_BOOK_ALT = "|".join(re.escape(s) for s in sorted(set(_BOOK_SURFACES), key=len, reverse=True))
_REF_RE = re.compile(rf"(?<![A-Za-z0-9])({_BOOK_ALT})\s+(\d+):(\d+)")


def _norm_book(label):
    """Parsed book label -> stored verses.book code, by EXACT lookup in _BOOK_CODE (no fallback).
    A known spelling ('Ruth', '1 Chronicles', 'Ps', 'Gen') maps to its code ('Rth', '1Ch', 'Psa',
    'Gen'); an unknown label returns unchanged so the valid-code check downstream rejects it. See
    the _BOOK_CODE header for why there is no prefix/fuzzy fallback (the Judges/Jude collision)."""
    return _BOOK_CODE.get(re.sub(r"\s+", "", label).lower(), label.strip())


def cited_refs(text):
    """Pull verse refs (book, ch, vs) out of generated prose — de-duped, in order."""
    seen, out = set(), []
    for bk, ch, vs in _REF_RE.findall(text or ""):
        key = (_norm_book(bk), int(ch), int(vs))
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


_VALID_BOOKS = None
def _valid_books(conn):
    global _VALID_BOOKS
    if _VALID_BOOKS is None:
        _VALID_BOOKS = {r[0] for r in conn.execute("SELECT DISTINCT book FROM verses")}
    return _VALID_BOOKS


# A book name written with NO following ch:vs = a DANGLING reference the gate can't bind (e.g.
# "Ruth—" or "1Ti—" with nothing after it). _REF_RE only matches a complete Book ch:vs, so these
# slip past silently. SAME closed book-label table as the catcher (2026-07-03) — a dangling "Ruth"
# is now flagged, not just numbered books. TRADE-OFF, accepted deliberately (fail-closed): a bare
# book name the model uses in prose without a ref ("throughout Genesis") now also flags and forces a
# cheap redraw — better than a dangling Ruth shipping silently, and these compact entries essentially
# never name a book without citing it. Complete refs are stripped first, so only a truly ch:vs-less
# name remains to flag.
_DANGLING_BOOK_RE = re.compile(rf"(?<![A-Za-z0-9])({_BOOK_ALT})(?![A-Za-z])")

# CHAPTER-level refs (book + chapter, no verse — "Psa 82", "Rom 8") are a legitimate way to cite a
# whole chapter's argument, not a botched citation. Stripped WITH the ch:vs refs before the dangling
# scan, so "Psa 82's gods" doesn't read as a dangling "Psa". Only a book with NO number at all
# ("Col — implicit") is a true dangling. KNOWN SOFT SPOT (accepted 2026-07-03): a chapter-ref dropped
# inside a citation list now also passes silently — we can't cheaply tell it from discursive prose.
_CHAP_ONLY_RE = re.compile(rf"(?<![A-Za-z0-9])(?:{_BOOK_ALT})\s+\d+")

# Ambiguous BARE surfaces — labels that are also everyday English or common person names, so a bare
# prose mention ("the Son", "endurance of Job", "Nehemiah's confrontation") is almost never a
# citation. Skipped in the BARE-word dangling scan ONLY (the ch:vs catcher is untouched). Ruled per
# word from the 2026-07-03 triage. CODES ARE NEVER LISTED — prose never writes "Rth"/"Jos"/"Col", so
# a bare code always flags (the πατήρ "Col — implicit" case). The two exceptions "job"/"son" are the
# ONLY book codes that are also English words (Job; Son = Song of Songs); because the chapter-strip
# above runs FIRST, every real Job/Song citation carries a number and is already consumed, so a bare
# leftover "Job"/"Son" is always the word. test_lexica_book_norm names those two as the only overlap.
_DANGLING_SOFT = {"joshua", "john", "nehemiah", "exodus", "mark", "daniel", "ruth", "esther",
                  "job", "son"}

def dangling_book_refs(conn, text):
    """Book names the model wrote but anchored to no number at all — not a complete ch:vs, not a
    chapter-level ref. Bare English/name surfaces (_DANGLING_SOFT) are skipped; a bare CODE flags."""
    stripped = _CHAP_ONLY_RE.sub("  ", _REF_RE.sub("  ", text or ""))   # drop ch:vs AND chapter refs
    valid, hits = _valid_books(conn), []
    for m in _DANGLING_BOOK_RE.finditer(stripped):
        if re.sub(r"\s+", "", m.group(1)).lower() in _DANGLING_SOFT:
            continue
        code = _norm_book(m.group(1))
        if code in valid and code not in hits:
            hits.append(code)
    return hits


# A CITATION-SHAPED ref — a (maybe-numbered) capitalized book label directly before "ch:vs". This
# is BROADER than _REF_RE on purpose: _REF_RE's plain branch is EXACTLY Cap+2-lower ("Gen"/"Mat"),
# so a 2-letter abbreviation ("Ps", "Jn", "Mt") or a spelled-out name ("Matthew 5:17") slips past it
# ENTIRELY — the ref is never verse-checked, never lands in verses[], and the sense reads grounded
# while it isn't (the "Ps 2:7" hole, 2026-07-02). This scans the whole citation shape and, via
# _norm_book + _valid_books, flags any label that isn't a real verses.book code — a HARD reject at
# write time (canonical codes only: Psa not Ps, Joh not Jn, Mat not Mt). Numbered books written
# spaced/spelled-out ("2 Chr 26:11", "1 John 1:5") normalize to their glued code and are NOT flagged.
_CITE_SHAPE_RE = re.compile(r'(?<![A-Za-z0-9])(\d?\s*[A-Z][A-Za-z]+)\s+\d+:\d+')

def noncanon_book_refs(conn, text):
    """Citation-shaped refs whose book label doesn't resolve to a canonical verses.book code — the
    invisible-to-_REF_RE class (2-letter abbrevs, spelled-out names). Returns the offending labels,
    in order. Every valid ref (a real code, or a numbered book _norm_book can re-glue) is skipped."""
    valid, bad = _valid_books(conn), []
    for m in _CITE_SHAPE_RE.finditer(text or ""):
        label = m.group(1).strip()
        if _norm_book(label) not in valid and label not in bad:
            bad.append(label)
    return bad


def strict_keyset(conn, sid):
    """Verses containing the lemma by the engine's own rule (target Strong's tag, dotted excluded)."""
    pred, params = abp_filter(conn, sid)
    return {(o["book"], int(o["ch"]), int(o["vs"])) for o in occurrences(conn, pred, params)}


def loose_keyset(conn, sid):
    """Verses where the bare number shows up in ANY form — a cited verse that misses strict but hits
    this is a TAGGING gap (the number IS there), not a hallucination."""
    num = sid[1:]
    rows = conn.execute("""
        SELECT DISTINCT v.book AS book, v.chapter AS ch, v.verse AS vs
        FROM verses v JOIN words w ON w.verse_id = v.id
        WHERE w.strongs = ? OR w.strongs LIKE ? OR w.strongs_base = ? OR w.strongs_base = ?
    """, (num, num + ".%", sid, num)).fetchall()
    return {(r["book"], int(r["ch"]), int(r["vs"])) for r in rows}


def verse_exists(conn, book, ch, vs):
    return conn.execute("SELECT 1 FROM verses WHERE book=? AND chapter=? AND verse=?",
                        (book, ch, vs)).fetchone() is not None


def run_citation_gate(conn, sid, refs):
    """THE CITATION GATE (audit-time). Every cited verse must contain the lemma by Strong's tag.
    Returns the bucketed result {pass,total,tagging,real,noverse,misses[]} — stored in the entry
    so the card can show a 'verified' badge. Tagging/real split: a tagging gap is a DATA bug, a
    real miss is the hallucination the gate exists to catch."""
    strict = strict_keyset(conn, sid)
    loose = loose_keyset(conn, sid)
    tally = Counter()
    misses = []
    for book, ch, vs in refs:
        key = (book, ch, vs)
        if key in strict:
            verdict = "pass"
        elif key in loose:
            verdict = "tagging"
        elif verse_exists(conn, book, ch, vs):
            verdict = "real"
        else:
            verdict = "noverse"
        tally[verdict] += 1
        if verdict != "pass":
            misses.append({"ref": f"{book} {ch}:{vs}", "bucket": verdict})
    total = sum(tally.values())
    return {
        "pass": tally["pass"], "total": total,
        "tagging": tally["tagging"], "real": tally["real"], "noverse": tally["noverse"],
        "misses": misses,
    }


# ══════════════════════════════════════════════════════════════════════════════════════════════
# NEW — split the engine's prose into display fields, build verses[], assemble the entry.
# ══════════════════════════════════════════════════════════════════════════════════════════════
# A section header line: one of the stable section titles at the line start, bold or not, with the
# rest of the line (if any) captured as the section's first body line. Case-insensitive, tolerant
# of trailing ":" / "**" / a "(ordered ...)" tail. Handles every header shape seen so far:
#   "**SENSES**"                              (dikaioo, caps, header alone)
#   "**Senses** (ordered by frequency...):"   (psyche, title case + parenthetical)
#   "**Range:** The word stretches from ..."  (label AND text on one line — was being dropped)
#   "Range:"                                  (un-bolded label)
# This (plus the bold numbered sense headlines below) is the ONLY structure we depend on across
# words, so a formatting quirk degrades gracefully — never a ref mis-filed under the wrong sense.
_SECTION_RE = re.compile(r'^\s*\*{0,2}\s*(senses|range|gloss notes|coverage)\b[\s:*]*(.*?)\s*$', re.I)
# A sense headline: a bold span starting with "N." — **1. ...**. The elaboration after it (whether
# on the same line behind a dash, dikaioo-style, or on the next line, psyche-style) is NOT captured.
_HEADLINE_RE = re.compile(r'\*\*\s*(\d+\.[^*]+?)\s*\*\*')
# A PLAIN (un-bolded) numbered sense header — a line that starts with "N." / "N)". Some draws number
# their senses plainly instead of bold (more often on rare words); the bold-only _HEADLINE_RE missed
# them, the glance came back empty, and validate_entry REFUSED the word. We accept plain headers as a
# FALLBACK — only when NO bold header is present in the block, so a bold entry parses EXACTLY as before
# (zero drift on every existing card). For a plain sense the whole description sits on the line, so the
# glance is the lead clause: cut at the first em-dash, sentence end, or citation; refs stripped.
_PLAIN_HDR = re.compile(r'(?m)^[ \t]*(\d+)[.)]\s+(.+)$')


def _plain_glance(text):
    """The short glance headline for a plain (un-bolded) sense line."""
    t = re.sub(r'\*+', '', text or '').strip()
    cut = len(t)
    for pat in (r'\s+—\s+', r'\.\s', r'\s+\('):       # em-dash, sentence end, or a (citation)
        m = re.search(pat, t)
        if m:
            cut = min(cut, m.start())
    return t[:cut].strip().rstrip('.,;')


def _sense_spans(block):
    """Per sense: (glance_headline, body_chunk). Uses BOLD headers when any are present — parsed
    EXACTLY as the old code did, so existing bold cards don't drift — otherwise falls back to PLAIN
    numbered headers. body_chunk is the sense's own text, used for per-sense ref counting."""
    block = block or ""
    bold = list(_HEADLINE_RE.finditer(block))
    if bold:
        out = []
        for i, m in enumerate(bold):
            lead = re.sub(r'^\d+\.\s*', '', m.group(1)).strip()
            start, end = m.end(), (bold[i + 1].start() if i + 1 < len(bold) else len(block))
            out.append((lead, block[start:end]))
        return out
    out = []
    plain = list(_PLAIN_HDR.finditer(block))
    for i, m in enumerate(plain):
        lead = _plain_glance(m.group(2))
        start, end = m.start(), (plain[i + 1].start() if i + 1 < len(plain) else len(block))
        out.append((lead, block[start:end]))
    return out


def split_definition(prose):
    """Split the engine's prose into fields at the parts that are STABLE across words: the bold
    section headers and the bold numbered sense headlines. Each section's body is kept VERBATIM
    for the full view; only the headlines are pulled out for the glance. We never peel refs off a
    sense, so a formatting quirk can at worst show a little extra on the glance — never mis-file a
    ref under the wrong sense."""
    lines = (prose or "").splitlines()
    sections = OrderedDict()
    cur = None
    for ln in lines:
        m = _SECTION_RE.match(ln)
        if m:
            cur = m.group(1).lower()
            sections.setdefault(cur, [])
            rest = m.group(2).strip()
            if re.fullmatch(r'\(.*?\)\s*:?', rest):   # a lone "(ordered ...):" tail — not body text
                rest = ""
            if rest:                                  # label AND text shared one line — keep the text
                sections[cur].append(rest)
            continue
        if cur is not None:
            sections[cur].append(ln)

    def body(title):
        out = "\n".join(sections.get(title, [])).strip()
        out = re.sub(r'^-{3,}\s*', '', out)      # drop a leading --- rule
        out = re.sub(r'\s*-{3,}\s*$', '', out)   # drop a trailing --- rule
        return out.strip()

    senses_block = body("senses")
    headlines = [lead for lead, _ in _sense_spans(senses_block)]
    return {
        "sense_headlines": headlines,
        "senses_block":    senses_block,
        "range":           body("range"),
        "gloss_notes":     body("gloss notes"),
        "coverage":        body("coverage"),
    }


def sense_provenance(senses_block):
    """Per-sense LXX provenance, ALIGNED to sense_headlines order. Splits the Senses prose at the
    same bold '**N. …**' markers the headlines come from, counts each sense's grounding refs by
    testament (OT = Septuagint / NT = Koine), and decides whether the subordinate LXX note fires
    (high + well-attested OT share). Derived from the stored citations only — no model. Returns
    [{ot, nt, lxx}], one per sense, in headline order, so the card can hang the note per sense."""
    out = []
    for lead, bodytext in _sense_spans(senses_block or ""):
        seen, ot, nt = set(), 0, 0
        for bk, ch, vs in _REF_RE.findall(bodytext):
            bk = _norm_book(bk)
            key = (bk, ch, vs)
            if key in seen:
                continue
            seen.add(key)
            if bk in NT_BOOKS:
                nt += 1
            else:
                ot += 1
        tot = ot + nt
        lxx = bool(tot and ot >= LXX_MIN_OT and (100 * ot / tot) >= LXX_THRESHOLD)
        out.append({"ot": ot, "nt": nt, "lxx": lxx})
    return out


def sense_specs(senses_block):
    """PIECE B input: [{headline, refs:[(book,ch,vs)]}] per sense, in order. Reuses the SAME sense
    splitter (_sense_spans) + ref regex (_REF_RE) + book normalizer (_norm_book) the rest of the
    build uses, so the coverage check sees exactly the citations the card does. Kept here (not in
    lexica_coverage) because the splitter lives here — coverage_audit takes the parsed result."""
    out = []
    for lead, body in _sense_spans(senses_block or ""):
        seen, refs = set(), []
        for bk, ch, vs in _REF_RE.findall(body):
            key = (_norm_book(bk), int(ch), int(vs))
            if key not in seen:
                seen.add(key)
                refs.append(key)
        out.append({"headline": lead, "refs": refs})
    return out


def double_shelved(senses_block):
    """FLAG-ONLY detector: any verse cited under MORE THAN ONE sense in the same draft. A plain
    set-intersection over the per-sense verse lists sense_specs() already carries — same splitter
    (_sense_spans) + ref regex (_REF_RE) + book normalizer (_norm_book) as the rest of the build, so
    it sees exactly the citations the card does. NOT a gate: double-shelving is sometimes legitimate
    (a genuinely bridging verse), so it becomes a conscious per-word adjudication in the audit
    output, never an automatic reject. Returns [{ref, senses:[1-based sense numbers]}] in a stable
    order (first sense, then ref)."""
    where = {}   # (book, ch, vs) -> set of 1-based sense numbers it's cited under
    for i, s in enumerate(sense_specs(senses_block), 1):
        for key in s["refs"]:
            where.setdefault(key, set()).add(i)
    out = []
    for (bk, ch, vs), senses in where.items():
        if len(senses) > 1:
            out.append({"ref": f"{bk} {ch}:{vs}", "senses": sorted(senses)})
    out.sort(key=lambda d: (d["senses"][0], d["ref"]))
    return out


def contest_verses(sid):
    """The word's disputed-passage locus from the register (piece B self_only), or []."""
    e = _CONTESTED_BY_SID.get(sid)
    return (e.get("contest_verses") or []) if e else []


def _colloc_warn(conn, sid, occs, sample):
    """PIECE A — collocation blind-spot check (ADVISORY). Scans ALL of the word's occurrences for a
    repeated adjacent content-lemma collocation (e.g. huios+anthrōpos "son of man") that the fed
    draw failed to represent, and prints a warning. WARN-ONLY: it never changes `sample`, so it
    cannot shift what the model sees or drift a built entry. Logic lives in lexica_coverage.py
    (repo root, already on sys.path)."""
    try:
        import lexica_coverage as _cov
        sample_vids = {o["vid"] for o in sample}
        missed = _cov.missed_collocations(_cov.scan_collocations(conn, sid, occs, sample_vids))
    except Exception as e:
        print(f"  (collocation check skipped: {e})", file=sys.stderr)
        return
    for f in missed:
        print(f"  ⚠ collocation MISSED by draw: {f['neighbor']} {f['lemma']} ({f['translit']}) — "
              f"{f['verses']} verses, 0 in the fed sample (e.g. {', '.join(f['examples'][:3])}). "
              f"A sense may be absent; eyeball before shipping.", file=sys.stderr)


def build_verses(conn, refs):
    """Cited refs -> [{ref, text}] in order, ABP prose text. Skips refs ABP doesn't carry."""
    out = []
    for book, ch, vs in refs:
        row = conn.execute("SELECT text FROM verses WHERE book=? AND chapter=? AND verse=?",
                           (book, ch, vs)).fetchone()
        if row and row["text"]:
            out.append({"ref": f"{book} {ch}:{vs}", "text": row["text"]})
    return out


def fork_field(sid):
    """The contested-word fork as a structured field, or None. Membership-only."""
    e = _CONTESTED_BY_SID.get(sid)
    if not e:
        return None
    fork = {
        "core":   e["core"],
        "frames": [{"label": l, "tradition": t, "gloss": g} for (l, t, g) in e["frames"]],
        "graph_ref": e.get("graph_ref"),
        # Seam index: the short label + the two authored axes (why they diverge; whether the lead
        # sense flips when the priors are swapped — the "different-lead" filter). Hand-set, no model.
        "gloss": e.get("gloss"),
        "divergence_type": e.get("divergence_type"),
        "lead_flip": bool(e.get("lead_flip")),
    }
    if e.get("pin_core"):
        # frame-leaker: the core is promoted to the entry's lead (pinned_core) so the definition
        # stops pre-picking a frame; don't ALSO repeat it inside the fork as "Core (all agree)".
        fork.pop("core")
    if e.get("note"):
        fork["note"] = e["note"]
    if e.get("etymology_note"):
        fork["etymology_note"] = e["etymology_note"]
    return fork


def synth_ver():
    # Identity of the MODEL output only (the prompt). Drives "skip regeneration if unchanged".
    # The splitter version is deliberately NOT in here — splitter changes are applied via --resplit
    # (no model call), so a splitter tweak must never trigger a wasteful re-generation on --apply.
    return "lexica:" + hashlib.sha1(VERSE_PROMPT.encode("utf-8")).hexdigest()[:12]


# ══════════════════════════════════════════════════════════════════════════════════════════════
# DRAW CACHE — review-what-ships. The dry-run pass (ro) saves the model's prose to a per-word file;
# --apply reads that file instead of calling the model, so the prose a human reviewed is the prose
# that ships byte-for-byte. Same split/gate/validate chain as --resplit; only the SOURCE of `raw`
# changes (a pre-write file, not the written row). Draws are throwaway working artifacts — a file
# per word, no table, no schema change. Files live beside bible.db and are gitignored.
# ══════════════════════════════════════════════════════════════════════════════════════════════
DRAWS_DIR = os.path.expanduser("~/bible-db/draws")


def _sha1(s):
    return hashlib.sha1((s or "").encode("utf-8")).hexdigest()


def draw_signature(sid, translit, gset, ctx):
    """Hash of the EXACT model input — system prompt + the full user message + the model id. Any
    change to the prompt, the fed verse sample (a words rebuild moving select_spread, a --budget
    change), the verse prose, the gloss set, or the model produces a DIFFERENT signature. A stored
    draw can only count as a hit when it was drawn from byte-identical input, so a stale draw can
    never silently apply. (OCC_MIN/MAX_TOKENS are deliberately out — OCC_MIN only gates whether a
    word builds; MAX_TOKENS is out for the same reason it's out of synth_ver.)"""
    user = verse_user_msg(sid, translit, gset, ctx)
    return _sha1(VERSE_PROMPT + "\x00" + user + "\x00" + MODEL_SONNET)


def draw_path(sid):
    return os.path.join(DRAWS_DIR, f"{sid}.json")


def load_draw(sid):
    """Read a cached draw file, or None (missing/unreadable). Never raises — a bad file degrades to
    a cache miss."""
    p = draw_path(sid)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  (cached draw unreadable, treating as miss: {e})", file=sys.stderr)
        return None


def draw_status(rec, sig):
    """Classify a found draw against the CURRENT input signature:
      'stale'  — the input moved since the draw (different signature); discard, draw fresh.
      'edited' — same input, but the prose bytes no longer match their stored hash: the file was
                 changed between review and apply. HARD REFUSE — reviewed bytes != shipped bytes.
      'hit'    — same input, prose intact: use it verbatim, no model call."""
    if rec.get("sig") != sig:
        return "stale"
    if rec.get("prose_sha") != _sha1(rec.get("raw", "")):
        return "edited"
    return "hit"


def save_draw(sid, lemma, translit, gset, ctx, raw):
    """Write (or refresh) the reviewed draw. Called ONLY by the ro pass and --force — an unreviewed
    fresh apply must never leave a draw file that would later look reviewed. Atomic replace so a
    crash mid-write can't leave a torn file."""
    os.makedirs(DRAWS_DIR, exist_ok=True)
    sig = draw_signature(sid, translit, gset, ctx)
    rec = {
        "strongs":   sid,
        "lemma":     lemma,
        "translit":  translit,
        "model":     MODEL_SONNET,
        "synth_ver": synth_ver(),
        "fed":       len(ctx),
        "sig":       sig,           # input signature — the live-recompute guard at apply
        "prose_sha": _sha1(raw),    # prose bytes — the edited-since-review guard at apply
        "raw":       raw,
        "created":   datetime.datetime.now(datetime.timezone.utc).replace(
                         tzinfo=None).isoformat(timespec="seconds"),
    }
    tmp = draw_path(sid) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    os.replace(tmp, draw_path(sid))
    return sig


def _coverage_audit(conn, sid, raw, senses_block):
    """PIECE B — the coverage_audit block (no model call, recomputed every build/--resplit like
    sense_prov). Checks the FINISHED entry: do the senses cite the tight collocations + top
    renderings, and is any contested sense circular (self_only)? Reads the word's real occurrences
    read-only. Degrades to an empty-but-shaped block if anything is missing, so it never blocks a
    write. NOTE — the citation gate + validate_entry do NOT read this (it's a report, not a gate)."""
    try:
        pred, params = abp_filter(conn, sid)
        occs = occurrences(conn, pred, params)
        return lexica_coverage.coverage_audit(
            conn, sid, occs,
            entry_refs=cited_refs(raw),
            sense_specs=sense_specs(senses_block),
            contest_verses=contest_verses(sid),
            is_contested=(sid in _CONTESTED_BY_SID))
    except Exception as e:                      # report-only: never let it stop a write
        print(f"  (coverage_audit skipped: {e})", file=sys.stderr)
        return {"collocations": [], "renderings": [], "senses": [],
                "thin_senses": [], "contested": (sid in _CONTESTED_BY_SID), "flags": []}


def assemble(conn, sid, lemma, translit, raw):
    """raw model prose -> the full stored entry (the frozen field shape)."""
    fields = split_definition(raw)
    refs = cited_refs(raw)
    ce = _CONTESTED_BY_SID.get(sid)
    entry = {
        "strongs":  sid,
        "lemma":    lemma,
        "translit": translit,
        **fields,
        # Per-sense LXX provenance, aligned to sense_headlines (Option B). Derived from the stored
        # citations, recomputed on every build/--resplit — no model. Drives the subordinate
        # "rests on Septuagint usage" note on senses that lean heavily Greek-OT.
        "sense_prov": sense_provenance(fields["senses_block"]),
        # PIECE B coverage_audit — the finished-entry coverage report (collocations/renderings
        # cited-or-not + per-sense thin/circular). No model; recomputed every build/--resplit.
        "coverage_audit": _coverage_audit(conn, sid, raw, fields["senses_block"]),
        # HAND-PINNED CORE (frame-leakers only): the neutral, hand-authored core leads the card and
        # the model's framed senses sit below it as attested uses. None for every other word — the
        # model's own senses lead as usual. Lifted from CONTESTED so a --resplit (no model call)
        # applies it; nothing about the stored raw changes.
        "pinned_core": (ce["core"] if (ce and ce.get("pin_core")) else None),
        "fork":       fork_field(sid),
        "verses":     build_verses(conn, refs),
        "provenance": "verse-grounded · LEXICA",
        "split_ver":  SPLIT_VER,
        "audit":      {**run_citation_gate(conn, sid, refs),
                       "dangling": dangling_book_refs(conn, raw),
                       "noncanon": noncanon_book_refs(conn, raw),
                       # FLAG-ONLY: verses cited under more than one sense (adjudicate per word).
                       "double_shelved": double_shelved(fields["senses_block"])},
        "raw":        raw,                # kept so an improved splitter can re-split, no model call
    }
    return entry


def validate_entry(entry):
    """Tell a LEGITIMATELY-empty field from a PARSE FAILURE wearing the same blank. The fields here
    are the ones where empty is NEVER legitimate, so an empty one means the splitter couldn't read
    the model's output — a loud error that must refuse to write the row, not a silent blank that
    reads as clean at scale (the numbered-book lesson). Range / gloss_notes / coverage are NOT here
    on purpose: empty is a fine graceful degrade for those scholar fields. Returns problems ([]=ok)."""
    problems = []
    if not entry["sense_headlines"]:
        problems.append(
            f"sense_headlines empty — the splitter found no '**N. …**' headlines "
            f"(senses_block {len(entry['senses_block'])} chars). The glance has nothing to show; "
            f"this is a parse failure, not a blank field.")
    if entry["strongs"] in _CONTESTED_BY_SID and not entry["fork"]:
        problems.append(
            "contested word but fork is missing — the fairness gate would be silently dropped. "
            "Check the CONTESTED register.")
    ce = _CONTESTED_BY_SID.get(entry["strongs"])
    if ce and ce.get("pin_core") and not entry.get("pinned_core"):
        problems.append(
            "pin_core is set but pinned_core came back empty — the frame-leak core wasn't lifted, "
            "so the definition would still lead with the model's framed senses. Check CONTESTED 'core'.")
    # THE CITATION GATE now BLOCKS the write (2026-07-01; was report-only — a draw with
    # hallucinated citations wrote exactly like a clean one, badge and all). tagging = the known
    # ABP tagging-gap class (the word IS in the verse, the tag missed it): non-blocking, logged.
    # real/noverse = a cited verse that lacks the word or doesn't exist — the failure the gate
    # exists to stop. A deliberate exception needs --force-gate-bypass "reason"; the reason is
    # stamped into audit.bypass_reason BEFORE this runs (main), so a bypassed row self-documents.
    a = entry.get("audit") or {}
    # CANONICAL-ABBREVIATION assertion (2026-07-02). A citation with a non-canonical book label
    # ("Ps"/"Jn"/"Mt", or a spelled-out name) is INVISIBLE to _REF_RE, so it never even reaches the
    # citation gate above — it would ship unverified. Hard reject; there is no data-bug bucket for
    # it (unlike a tagging miss), so no bypass. Fix the raw to the canonical code and re-run.
    noncanon = a.get("noncanon") or []
    if noncanon:
        problems.append(
            f"non-canonical book label(s) in a citation: {', '.join(noncanon)} — _REF_RE can't "
            f"verse-check these, so the ref would ship UNVERIFIED. Use the canonical verses.book "
            f"code (Psa not Ps, Joh not Jn, Mat not Mt).")
    for m in a.get("misses", []):
        if m["bucket"] == "tagging":
            print(f"  ⚠ tagging miss (non-blocking) {entry['strongs']}: {m['ref']}", file=sys.stderr)
    failed = [m["ref"] for m in a.get("misses", []) if m["bucket"] in ("real", "noverse")]
    if failed:
        if a.get("bypass_reason"):
            print(f"  ⚠ citation gate BYPASSED for {entry['strongs']} ({len(failed)} failed: "
                  f"{', '.join(failed)}) — reason stored: {a['bypass_reason']}", file=sys.stderr)
        else:
            problems.append(
                f"citation gate FAILED — {len(failed)} cited verse(s) don't check out "
                f"(real {a.get('real', 0)} / no-verse {a.get('noverse', 0)}: {', '.join(failed)}). "
                f"Fix the raw with fix_lexica_raw.py, or pass --force-gate-bypass \"reason\".")
    return problems


def ensure_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lexica_def (
            strongs   TEXT PRIMARY KEY,
            lemma     TEXT,
            translit  TEXT,
            def_json  TEXT,
            synth_ver TEXT,
            updated   TEXT
        )
    """)
    conn.commit()


def make_client():
    """Create the Anthropic client (lazily, on the first real model call). Isolated so a run that
    only applies cached draws never imports anthropic or needs the API key."""
    import anthropic
    return anthropic.Anthropic(api_key=get_key())


def model_prose(client, sid, translit, gset, ctx):
    msg = client.messages.create(
        model=MODEL_SONNET, max_tokens=MAX_TOKENS, system=VERSE_PROMPT,
        messages=[{"role": "user", "content": verse_user_msg(sid, translit, gset, ctx)}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def show_entry(entry):
    """Print the assembled fields so a human can eyeball the split before --apply writes."""
    a = entry["audit"]
    print(f"\n  lemma: {entry['lemma']}  ({entry['translit']})   stamp {entry.get('synth_ver','')}")
    if entry.get("pinned_core"):
        print(f"  PINNED CORE (leads the card; the senses below read as attested uses):")
        print(f"     → {entry['pinned_core']}")
    print(f"  sense_headlines ({len(entry['sense_headlines'])}) — the glance list:")
    for i, h in enumerate(entry["sense_headlines"], 1):
        print(f"     {i}. {h}")
    prov = entry.get("sense_prov") or []
    hits = [str(i + 1) for i, p in enumerate(prov) if p.get("lxx")]
    print(f"  LXX provenance note fires on sense(s): {', '.join(hits) if hits else '(none)'}")
    print(f"  senses_block: {len(entry['senses_block'])} chars (full prose, kept verbatim)")
    print(f"  range:       {entry['range'] or '(empty)'}")
    print(f"  gloss_notes: {(entry['gloss_notes'][:400] + ' …') if len(entry['gloss_notes'])>400 else (entry['gloss_notes'] or '(empty)')}")
    print(f"  coverage:    {entry['coverage'] or '(empty/adequate)'}")
    cov = entry.get("coverage_audit") or {}
    if cov:
        colls, rends = cov.get("collocations", []), cov.get("renderings", [])
        cu = [c for c in colls if not c["cited"]]
        ru = [r for r in rends if not r["cited"] and r["count"] >= 10]
        print(f"  coverage_audit: {len(colls)} tight collocations "
              f"({len(cu)} uncited), {len(rends)} top renderings ({len(ru)} uncited)")
        for c in cu:
            print(f"      · collocation UNCITED: {c['neighbor']} {c['lemma']} "
                  f"({c['translit']})  {c['verses']}v  PMI {c['score']}")
        for r in ru:
            print(f"      · rendering UNCITED: '{r['gloss']}'  {r['count']}x")
        thin = cov.get("thin_senses", [])
        circ = [t for t in thin if t["self_only"]]
        thin_only = [t for t in thin if not t["self_only"]]
        print(f"      senses: {len(cov.get('senses', []))} checked, {len(thin_only)} thin, "
              f"{len(circ)} circular" + ("" if cov.get("contested") else "  (circular check inert)"))
        for t in thin:
            kind = "CIRCULAR (self-only)" if t["self_only"] else "thin"
            badge = "" if cov.get("contested") else " [non-contested — count only]"
            print(f"      · sense {t['sense']} {kind} — {t['support_refs']} support ref(s){badge}: "
                  f"{t['headline'][:60]}")
        if cov.get("flags"):
            print(f"      flags: {'; '.join(cov['flags'])}")
    print(f"  verses:      {len(entry['verses'])} cited, with text")
    print(f"  citation gate: {a['pass']}/{a['total']} pass" +
          (f"  (misses — tagging {a['tagging']} / real {a['real']} / no-verse {a['noverse']})" if a['total']-a['pass'] else ""))
    if a.get("dangling"):
        print(f"  ⚠ dangling book refs (no ch:vs — flag only): {', '.join(a['dangling'])}")
    if a.get("noncanon"):
        print(f"  ✗ non-canonical book label(s) — HARD REJECT: {', '.join(a['noncanon'])}")
    for d in (a.get("double_shelved") or []):
        print(f"  ⚠ double-shelved: {d['ref']} in senses {d['senses']}")
    if entry["fork"]:
        f = entry["fork"]
        # core is suppressed in the fork for a pinned word (it leads above as PINNED CORE), so read
        # it safely — f['core'] is absent exactly when pinned_core carries it.
        print(f"  FORK (contested): core = {f['core']}" if f.get("core")
              else "  FORK (contested): core PINNED above (suppressed here, not repeated)")
        for fr in f["frames"]:
            trad = "" if fr["tradition"] in ("", "—") else f" [{fr['tradition']}]"
            print(f"     • {fr['label']}{trad}: {fr['gloss']}")
        print(f"     graph: {f['graph_ref'] or '(none authored yet)'}")
    else:
        print("  fork: (none — not a contested word)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"))
    ap.add_argument("--word", help="one G-number, e.g. G5590 (default: the pilot set)")
    ap.add_argument("--dry-run", action="store_true", help="generate + split + SHOW, no write")
    ap.add_argument("--apply", action="store_true", help="write the rows into lexica_def")
    ap.add_argument("--resplit", action="store_true",
                    help="re-split the STORED raw prose into fields — no model call (after a splitter change)")
    ap.add_argument("--force", action="store_true",
                    help="rebuild even if the stamp matches; ALSO ignores any cached draw and "
                         "refreshes it with a fresh model draw (a forced draw is now the reviewed one)")
    ap.add_argument("--require-cache", action="store_true",
                    help="on --apply, REFUSE any word with no valid reviewed draw instead of drawing "
                         "fresh (default ON under --all; the loud path, not the safe one, takes a flag)")
    ap.add_argument("--allow-unreviewed", action="store_true",
                    help="opt OUT of --require-cache under --all: draw fresh + write with a loud "
                         "UNREVIEWED note for a word that has no cached draw")
    ap.add_argument("--force-gate-bypass", metavar="REASON",
                    help="write DESPITE citation-gate failures (real/no-verse misses); the reason "
                         "is stored in the entry (audit.bypass_reason) so a bypassed row is "
                         "self-documenting. Only stamped on a word whose gate actually failed.")
    ap.add_argument("--all", action="store_true",
                    help="target EVERY built word in lexica_def (use with --resplit to roll a "
                         "derivation change — e.g. the LXX provenance note — across the whole batch, "
                         "no model call)")
    ap.add_argument("--from-draw", metavar="KEY8",
                    help="ship the reviewed draw for --word whose key (sig[:8]) == KEY8 by bypassing the "
                         "synth_ver up-to-date skip; requires a cache HIT, NEVER re-rolls. Use after a prose "
                         "fix the draw signature can't detect: find affected cards with check_draw_citations.py, "
                         "regenerate with --dry-run --force + review, then ship the reviewed bytes with this.")
    ap.add_argument("--budget", type=int, default=BUDGET)
    args = ap.parse_args()

    if not args.dry_run and not args.apply:
        sys.exit("Pass --dry-run (show, no write) or --apply (write).")
    if args.from_draw and (not args.word or not args.apply or args.force or args.all or args.dry_run):
        sys.exit("--from-draw ships one reviewed draw: use as --apply --word G#### --from-draw KEY8 "
                 "(no --force / --all / --dry-run — it ships specific reviewed bytes, it never rolls).")

    targets = [args.word.upper()] if args.word else list(PILOT)
    targets = [("G" + t if t[:1] not in ("G", "H") else t) for t in targets]

    # Live db handle. On --apply we create + write ONLY lexica_def, so it's read-write; otherwise
    # (--dry-run, or --resplit without --apply) we open READ-ONLY so a dry run can never touch the
    # live file (audit C3, 2026-07-01). The evidence reads run on the same handle either way.
    if args.apply:
        conn = sqlite3.connect(args.db)
    else:
        conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.create_function("strip_accents", 1, strip_accents)
    if args.all:
        if not table_exists(conn, "lexica_def"):
            sys.exit("--all needs lexica_def built already (nothing to roll across).")
        targets = [r["strongs"] for r in
                   conn.execute("SELECT strongs FROM lexica_def ORDER BY strongs").fetchall()]
        print(f"--all: targeting {len(targets)} built word(s).")
    if args.apply:
        ensure_table(conn)
    has_surface = table_exists(conn, "abp_surface")
    stamp = synth_ver()

    # Draw-cache safety: the SAFE path is the default under --all (batch runs), so shipping an
    # unreviewed word takes an explicit --allow-unreviewed. Single-word --apply stays permissive
    # (fresh draw + warning banner) unless --require-cache is asked for. --force always overrides
    # (it deliberately draws fresh and refreshes the cache).
    require_cache = (args.all or args.require_cache) and not args.allow_unreviewed

    # The API client is created LAZILY (make_client, on the first real model call) — a run that only
    # applies cached draws never touches the model, so it needs NO ANTHROPIC_API_KEY. resplit never
    # calls the model either.
    client = None

    failures = []
    unreviewed = []          # words written via --apply with NO reviewed draw (loud, tracked)
    for sid in targets:
        print("\n" + "=" * 78)
        print(f"{sid}")
        existing = conn.execute("SELECT def_json, synth_ver FROM lexica_def WHERE strongs=?",
                                (sid,)).fetchone() if table_exists(conn, "lexica_def") else None

        if args.resplit:
            if not existing or not existing["def_json"]:
                print("  (no stored row to re-split — run --apply with the model first)")
                continue
            raw = json.loads(existing["def_json"]).get("raw", "")
            if not raw:
                print("  (stored row has no raw prose — re-run --apply with the model)")
                continue
            lemma, translit = lex_head(conn, sid)
        else:
            if existing and existing["synth_ver"] == stamp and not args.force and not args.from_draw:
                print(f"  up to date (stamp {stamp}); skip. (--force to rebuild)")
                continue
            pred, params = abp_filter(conn, sid)
            gset = gloss_set(conn, pred, params)
            occs = occurrences(conn, pred, params)
            if not occs:
                print(f"  no occurrences for {sid} — skip.")
                continue
            if len(occs) < OCC_MIN:
                print(f"  ✗ {sid} occurs {len(occs)}× — below the occ≥{OCC_MIN} cutoff for a "
                      f"verse-grounded entry. A single occurrence can't show a range; the word is "
                      f"left to the LSJ card. (No bypass flag — edit OCC_MIN to build one deliberately.)")
                continue
            sample = select_spread(occs, args.budget)
            _colloc_warn(conn, sid, occs, sample)   # PIECE A: advisory only — never alters the draw
            ctx = fetch_context(conn, sample, has_surface)
            lemma, translit = lex_head(conn, sid)
            ot = sum(1 for c in ctx if c[0] not in NT_BOOKS)
            print(f"  occurrences {len(occs)} | {len(gset)} renderings | fed {len(ctx)} ({ot} OT / {len(ctx)-ot} NT)")

            # ── DRAW CACHE. Recompute the current input signature live; consult the cached draw.
            sig = draw_signature(sid, translit, gset, ctx)
            rec = None if args.force else load_draw(sid)
            status = draw_status(rec, sig) if rec else None

            if args.from_draw:
                # Ship ONE named reviewed draw past the synth_ver skip — never re-roll. The signature is
                # sample-based, so a prose fix to a non-sampled cited verse leaves sig unchanged (status
                # stays 'hit'); this is the ONLY way to ship the reviewed bytes for that case.
                key = sig[:8]
                if rec is None:
                    print(f"  ✗ --from-draw: no cached draw for {sid} — run --dry-run --force to draw + "
                          f"review first. NOT written.", file=sys.stderr)
                    failures.append(sid); continue
                if status != "hit":
                    print(f"  ✗ --from-draw: cached draw is '{status}' (input moved since it was drawn) — "
                          f"re-run --dry-run --force + re-review. NOT written.", file=sys.stderr)
                    failures.append(sid); continue
                if key != args.from_draw:
                    print(f"  ✗ --from-draw key mismatch: {sid}'s reviewed draw is '{key}', not "
                          f"'{args.from_draw}'. NOT written.", file=sys.stderr)
                    failures.append(sid); continue
                # status == 'hit' + key matches → falls through to the 'hit' branch: ships rec['raw'], no model call.

            if status == "edited":
                # Same input, but the file's prose was changed since review — the one way
                # reviewed-bytes could differ from shipped-bytes. Hard refuse; do NOT redraw.
                print(f"  ✗ cached draw {draw_path(sid)} was EDITED since review "
                      f"(prose no longer matches its stored hash). Re-run --dry-run to redraw + "
                      f"re-review. NOT written.", file=sys.stderr)
                failures.append(sid)
                continue

            if status == "hit":
                raw = rec["raw"]
                print(f"  using reviewed draw {draw_path(sid)} (key {sig[:8]}) — no model call.")
            else:
                # miss: no file, stale (input moved), or --force.
                stale = (status == "stale")
                if args.apply and require_cache and not args.force:
                    if stale:
                        print(f"  cached draw {draw_path(sid)} is STALE (input moved since it was drawn).")
                    why = "--all default" if (args.all and not args.require_cache) else "requested"
                    print(f"  ✗ no reviewed draw for {sid} and --require-cache is in effect ({why}); "
                          f"pass --allow-unreviewed to draw fresh — NOT written.", file=sys.stderr)
                    failures.append(sid)
                    continue
                if stale:
                    print(f"  cached draw {draw_path(sid)} is STALE (input moved) — redrawing.")
                print("  calling the verse engine (Sonnet)…")
                if client is None:
                    client = make_client()
                raw = model_prose(client, sid, translit, gset, ctx)
                if args.dry_run or args.force:
                    # ro (review pass) and --force write/refresh the draw so apply ships THIS prose.
                    save_draw(sid, lemma, translit, gset, ctx, raw)
                    tag = " (forced — cache refreshed)" if args.force else ""
                    print(f"  cached draw → {draw_path(sid)} (key {sig[:8]}){tag}")
                elif args.apply:
                    # permissive single-word apply on a miss: fresh + loud, NO draw file written
                    # (an unreviewed draw must not later masquerade as reviewed).
                    print(f"  ⚠ UNREVIEWED — no cached draw for {sid}; this write was NOT reviewed.",
                          file=sys.stderr)
                    unreviewed.append(sid)

        entry = assemble(conn, sid, lemma, translit, raw)
        entry["synth_ver"] = stamp
        # Bypass ordering: stamped AFTER assemble (so the audit buckets exist), BEFORE
        # validate_entry reads it — and ONLY on a word whose gate actually failed, so a clean
        # word in the same batch never carries a stale bypass note.
        if args.force_gate_bypass and any(
                m["bucket"] in ("real", "noverse") for m in entry["audit"]["misses"]):
            entry["audit"]["bypass_reason"] = args.force_gate_bypass
        show_entry(entry)

        problems = validate_entry(entry)
        if problems:
            print("  ✗ PARSE FAILURE — NOT written (a load-bearing field came back empty):")
            for p in problems:
                print("      - " + p)
            failures.append(sid)
            continue                              # never write an incomplete row

        if args.apply:
            conn.execute(
                "INSERT OR REPLACE INTO lexica_def (strongs, lemma, translit, def_json, synth_ver, updated) "
                "VALUES (?,?,?,?,?,?)",
                (sid, lemma, translit, json.dumps(entry, ensure_ascii=False), stamp,
                 datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")))
            conn.commit()
            print("  → written to lexica_def.")
        else:
            print("  [dry run — not written]")

    conn.close()
    if unreviewed:
        print(f"\n⚠ {len(unreviewed)} word(s) written with NO reviewed draw (unreviewed): "
              f"{', '.join(unreviewed)}  (run --dry-run first to review, or use --require-cache)",
              file=sys.stderr)
    if failures:
        sys.exit(f"\n{len(failures)} word(s) FAILED and were NOT written: "
                 f"{', '.join(failures)}  (parse failure, gate failure, edited draw, or "
                 f"--require-cache with no draw — see each word above)")


if __name__ == "__main__":
    main()
