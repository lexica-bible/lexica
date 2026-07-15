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

import argparse, datetime, difflib, hashlib, html, json, os, re, sqlite3, sys, unicodedata
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

# ── GROUNDED-NAMING context span (design pass, reviewer-ruled 2026-07-15). Each fed occurrence
# carries up to this many surrounding verses EITHER SIDE, same chapter only, labeled as read-only
# context — so a narrative subject's name is GROUNDED in text the model can see instead of
# RECALLED from training (the G2374 Corinth/Hazah + G5088 Elizabeth park cause). ±2 was ruled
# over ±1 on the read fact: it additionally grounds Elisha's widow (2Ki 4:2 for 4:4) and Mary at
# the manger verse (Luk 2:5 for 2:7), leaving exactly the accepted residual (Solomon complex,
# Paul-as-author). Same-chapter only: chapter-crossing would rest on an unverified verse-row
# ordering, and every read-fact rescue case was same-chapter.
CONTEXT_SPAN = 2

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
# reviewer. KEEP IN SYNC with lexica_agreement.V5_PROMPT (the reviewer soft-asserts they match). ───
VERSE_PROMPT = """\
You define a biblical lemma from its own attested use. You are given:
- the lemma (Strong's number, original-language form, transliteration)
- the translation gloss set: the English words a translation used to render
  this lemma, with frequencies
- a set of occurrences: each a verse where this lemma appears, with the
  inflected form marked, plus surrounding context verses (lines marked
  "context") supplied for reading only

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
- Name a person or place only if that name appears in the supplied text - the
  occurrence's verse or its context lines. If the supplied text does not name
  the referent, do not name it, even if you know the narrative: describe by
  role instead (a woman, the author, the city). Context lines exist to ground
  names; they are never citations and never count as occurrences.
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
- COVERAGE IS TOTAL. Every supplied occurrence must appear as a citation under one
  of your senses. Do not choose representative examples - an occurrence you leave
  uncited is a defect, exactly like a fabricated one, even when the sense analysis
  is otherwise right. Before you finish, re-scan the supplied occurrences top to
  bottom and confirm every reference appears in your senses.
- QUOTES ARE VERBATIM. Any wording you place inside quotation marks and attribute
  to a verse must match that verse's stored text word for word; mark any omission
  with an ellipsis (…). When several verses share a refrain or formula, quote ONE
  verse and name it - never write a blended wording, and never claim the members
  are worded identically unless they are.
- REFERENCES NAME VERSES ONE BY ONE. Never write a span of verses as a reference
  range. "Rev 19:1-6" asserts every verse between its endpoints, including any
  that do not carry this lemma - list the verses you actually mean, separated by
  commas ("Rev 19:1, 19:6"). This governs REFERENCES only; the Range section,
  which states how far the word's meaning stretches, is unaffected.

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

NT_BOOKS = {"Mat","Mar","Luk","Joh","Act","Rom","1Co","2Co","Gal","Eph","Php","Col",
            "1Th","2Th","1Ti","2Ti","Tit","Phm","Heb","Jas","1Pe","2Pe","1Jn","2Jn","3Jn","Jud","Rev"}

# ── THE CONTESTED-WORD FAIRNESS GATE — the hand-authored fork register. Moved to
# contested_register.py (repo root) 2026-07-01 so the build, the serving route (views_lexica.py:
# the serve-time fork backstop + the G5485 alias), and the rigs all read ONE copy.
# _CONTESTED_BY_SID kept as a module name: lexica_agreement.py reads B._CONTESTED_BY_SID.
# The path insert: `python scripts/build_lexica_def.py` starts its module search in scripts/,
# and the shared register lives one level up at the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from contested_register import CONTESTED, CONTESTED_BY_SID, CONTESTED_VERSES
from draw_hints import DRAW_HINTS
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
    """The 'renders as' set: single-word english_head renderings with counts.
    Case-variants of the SAME rendering are MERGED case-insensitively — a capital like "Heaven",
    "Earth", "Holy" is a sentence-initial / naming / quote-initial artifact of the translation, not a
    distinct rendering. Feeding the split ("heaven" 636 + "Heaven" 3) as two renderings made the engine
    fabricate a rationale for the capital in gloss_notes (the οὐρανός defect, 2026-07-07: two prompt
    generations, two fabrications, one upstream stimulus). We keep the MOST FREQUENT surface form as the
    label (rows arrive count-DESC, so the first variant seen wins) and sum the counts. Referent-carrying
    case pairs (God/god, Lord/lord, Spirit/spirit) never reach here — those live on CONTESTED-register
    lemmas excluded from the rollout (verified by a full-population sweep 2026-07-07: the only rollout
    case-splits were Earth/Heaven/Holy, all artifact-class; Luk 1:35 "Holy spirit" examined individually
    under the spirit-frame bar and ruled artifact — the frame attaches to the noun/phrase, not the
    adjective). This folds the EVIDENCE SUMMARY only — citation verse text stays verbatim."""
    rows = conn.execute(f"""
        SELECT w.english_head AS g, COUNT(*) AS c
        FROM words w
        WHERE {pred} AND w.english_head IS NOT NULL AND w.english_head != ''
        GROUP BY w.english_head ORDER BY c DESC
    """, params).fetchall()
    merged = OrderedDict()          # lower(head) -> [label, total]; first-seen label is most frequent
    for r in rows:
        g = r["g"]
        if " " in g:                # multi-word renderings stay excluded (unchanged)
            continue
        key = g.lower()
        if key in merged:
            merged[key][1] += r["c"]
        else:
            merged[key] = [g, r["c"]]
    return sorted(((lbl, tot) for lbl, tot in merged.values()), key=lambda t: t[1], reverse=True)


def occurrences(conn, pred, params):
    """Each occurrence row now carries the slot's FULL ABP phrase gloss (`phrase` = words.english)
    and its translator-addition list (`ital` = words.italic_words) alongside the one-token head
    (`rend` = english_head). The head stays the render KEY everywhere (phantom protection — see
    parse_abp.HEAD_WORD_TAIL_CAVEAT + tests/test_render_head_no_phantom.py); the phrase is CONTEXT
    so no consumer reasons from a fragment (the 2Ch 4:13 'latticed work' finding, 2026-07-12)."""
    return conn.execute(f"""
        SELECT v.book AS book, v.chapter AS ch, v.verse AS vs,
               w.english_head AS rend, w.english AS phrase, w.italic_words AS ital,
               w.verse_id AS vid, w.position AS pos
        FROM verses v JOIN words w ON w.verse_id = v.id
        WHERE {pred}
        ORDER BY v.id, w.position
    """, params).fetchall()


def _phrase_clean(s):
    """Comparison form of a phrase/gloss: outer punctuation stripped per token, whitespace
    collapsed. Case is PRESERVED (case-awareness is load-bearing in the claim lint)."""
    toks = [t.strip("\"'.,;:!?()[]—-") for t in (s or "").split()]
    return " ".join(t for t in toks if t)


def _phrase_minus_italics(phrase, ital):
    """The slot's own-render phrase: the full ABP phrase with translator-addition words
    (italic_words, comma-joined in the db) removed. 'latticed works;' minus 'works' -> 'latticed'."""
    skip = {w.strip().lower() for w in (ital or "").split(",") if w.strip()}
    toks = [t for t in _phrase_clean(phrase).split() if t.lower() not in skip]
    return " ".join(toks)


def phrase_map(occs):
    """head(lower) -> list of (display_phrase, count) for heads that NEVER occur as a single-word
    gloss — the fragment-risk class (the head is always a piece of a longer ABP phrase, so any
    consumer seeing only the head is reasoning from a fragment). Heads that ever stand alone are
    left unannotated. Phrase counts keyed punctuation-stripped; most frequent surface form wins."""
    per_head = {}
    for o in occs:
        head = (o["rend"] or "").strip()
        if not head:
            continue
        phr = _phrase_clean(o["phrase"])
        per_head.setdefault(head.lower(), []).append(phr)
    out = {}
    for head, phrases in per_head.items():
        if any(len(p.split()) <= 1 for p in phrases):
            continue                       # head stands alone somewhere — not fragment-risk
        c = Counter(phrases)
        out[head] = c.most_common(3)
    return out


def lex_head(conn, sid):
    """(lemma, translit) for a G-number from the lexicon. Falls back to (sid, '')."""
    r = conn.execute("SELECT lemma, translit FROM lexicon WHERE strongs_g = ?", (sid,)).fetchone()
    if not r:
        return sid, ""
    return (r["lemma"] or sid), (r["translit"] or "")


def dynamic_budget(occ_count):
    """V7 fed-sample curve (JP-ruled 2026-07-08, the fed-40 retro item). At 40 occurrences or
    fewer the WHOLE corpus evidence is fed — the entire fed-gap defect family (ENGINE_LESSONS
    #8/#19, both failure modes) is impossible by construction. Measured split 2026-07-08:
    4,017 of 5,254 Greek lemmas (76%) sit at <=40. Above 40 the curve scales MODESTLY — raw
    size is not the fix (every batch-2 collocation flag was a WHICH-verses miss, never a
    how-many miss); the load-bearing half is reserve_collocation_slots below. Cost across the
    corpus: PROJECTION (roughly flat — the tail gets cheaper, the ~24% over-40 words costlier),
    not a measurement."""
    if occ_count <= 40:
        return occ_count
    if occ_count <= 100:
        return 40
    if occ_count <= 500:
        return 60
    return 80


def reserve_collocation_slots(conn, sid, occs, sample, top_n=10):
    """Collocation-aware slot reservation (ENGINE_LESSONS #8 option (b) + #19; JP-ruled at the
    V7 window). Each of the word's top-N PMI neighbors is GUARANTEED at least one verse in the
    fed sample: an unfed high-PMI family is exactly how a whole job stays invisible to a stable
    floor (ὀφθαλμός disposition region) or a shipped sense gets silently narrowed (θυγάτηρ
    paternal headline). Reuses the production scanner (lexica_coverage.scan_collocations — the
    one copy, reuse rule) and ADDS on top of the spread sample, never displacing a pick. This
    closes the fed gap at GENERATION; the step-1.5 eyeball of any remaining MISSED warnings
    stays law."""
    try:
        import lexica_coverage as _cov
        sample_vids = {o["vid"] for o in sample}
        findings = _cov.scan_collocations(conn, sid, occs, sample_vids)
    except Exception as e:
        print(f"  (collocation slot reserve skipped: {e})", file=sys.stderr)
        return sample
    by_ref = {}
    for o in occs:
        by_ref.setdefault(f'{o["book"]} {o["ch"]}:{o["vs"]}', o)
    have = {o["vid"] for o in sample}
    added = []
    for f in findings[:top_n]:
        if f["in_draw"]:
            continue
        o = next((by_ref[r] for r in f["examples"] if r in by_ref and by_ref[r]["vid"] not in have), None)
        if o is not None:
            sample.append(o)
            have.add(o["vid"])
            added.append(f'{f["translit"]} → {o["book"]} {o["ch"]}:{o["vs"]}')
    if added:
        print(f"  collocation slots reserved (+{len(added)}): {'; '.join(added)}")
    return sorted(sample, key=lambda o: o["vid"])


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
        # GROUNDED-NAMING context (2026-07-15): up to CONTEXT_SPAN verses either side, same
        # chapter. A missing neighbor is OMITTED entirely — never printed blank or as a
        # placeholder (the "None" feed-lie class, G3464 canary: the feed must never assert
        # something that isn't there).
        ch0, vs0 = int(o["ch"]), int(o["vs"])
        neigh = []
        for nv in range(vs0 - CONTEXT_SPAN, vs0 + CONTEXT_SPAN + 1):
            if nv == vs0:
                continue
            r = conn.execute("SELECT text FROM verses WHERE book=? AND chapter=? AND verse=?",
                             (o["book"], ch0, nv)).fetchone()
            if r and r["text"]:
                neigh.append((ch0, nv, r["text"]))
        out.append((o["book"], o["ch"], o["vs"], o["rend"], form, prose,
                    (o["phrase"] or ""), (o["ital"] or ""), neigh))
    return out


def _phrase_tag_part(rend, phrase, ital):
    """The here-tag's phrase addition: shown only when ABP prints a multi-word phrase on this slot
    (otherwise the head IS the render and the tag stays as before). Translator additions named."""
    phr = _phrase_clean(phrase)
    if len(phr.split()) <= 1 or phr.lower() == (rend or "").lower():
        return ""
    part = f'; phrase here: "{phrase.strip()}"'
    added = [w.strip() for w in (ital or "").split(",") if w.strip()]
    if added:
        part += f" (added words: {', '.join(added)})"
    return part


def _occ_lines(ctx):
    """The per-occurrence feed lines — ONE format, shared by the draw user message and the
    V10 repair message (the design requires the repair feed to match the original feed
    shape byte-for-byte, so this must never fork into two copies)."""
    out = []
    for book, ch, vs, rend, form, prose, phrase, ital, neigh in ctx:
        if (rend or "").strip():
            tag = (f'[here: "{rend}"' + _phrase_tag_part(rend, phrase, ital)
                   + (f"; form: {form}" if form else "") + "]")
        else:
            # BLANK HEAD — english_head is None BY DESIGN when ABP's gloss on this slot carries no
            # content word (parse_abp.py:135/:144 — head = last non-function word; _head_word
            # returns None for an all-function gloss). ~45% of Greek rows, correctly: articles and
            # particles. This branch exists because the old f-string printed that absence as the
            # TEXT "None" — NOT visibly distinct from a real rendering, so the model believed it,
            # wrote 'the occurrence tagged "None"' into the card, and the verbatim-quote gate
            # rightly killed the draw for quoting a word no verse contains (G3464 canary,
            # 2026-07-14, a live model call). The gate was right; the FEED was lying.
            # The replacement states the absence EXPLICITLY (#69(i) — silence invites inference)
            # and UNQUOTABLY: no quote character, so there is nothing for the model to lift and
            # nothing for the gate to match. The slot's function-word gloss (e.g. a genitive "of"
            # parked here by _split_compounds) is deliberately NOT named — presenting it would
            # invite the next fabrication, a card claiming the lemma "is rendered of".
            tag = ("[no content-word rendering on this slot — the English for this occurrence is "
                   "carried by the surrounding phrase"
                   + (f"; form: {form}" if form else "") + "]")
        out.append(f"  {book} {ch}:{vs} {tag}")
        out.append(f"     {prose}")
        # GROUNDED-NAMING context lines (2026-07-15). Label states the contract on the line
        # itself: read-only, not an occurrence, never a citation. ASCII only (matches the feed's
        # existing style; nothing here for the quote gate to reason about).
        for nch, nvs, ntext in neigh:
            out.append(f"     ~ context {book} {nch}:{nvs} (read only; NOT an occurrence - "
                       f"never cite it): {ntext}")
    return out


def _roster_lines(roster):
    """PATH (c) ROSTER injection (PATH (c) DESIGN — CLOSED, AUDIT 2026-07-13). Soft-explicit draw
    context: the floor's OWN repeated-review consensus — how many senses, and which verses group —
    read BACK to the draw (never hand-invented; see DESIGN_hint_tooling.md's roster class). Rides
    the user message after the occurrences (and any STRUCTURE/CONSTRAINT CHECK); frozen V9 prompt
    untouched. Fixes count + grouping only; the seam verses fold into their ruled home group. The
    closing boundary sentence is RULED VERBATIM — do not reword it."""
    groups = [list(g) for g in roster["groups"]]
    for s in roster.get("seams", []):
        gi = s["group"] - 1
        if 0 <= gi < len(groups) and s["ref"] not in groups[gi]:
            groups[gi].append(s["ref"])
    out = ["",
           "ROSTER (floor consensus, pre-registered): repeated independent review of this lemma's "
           "FULL occurrence set settled the sense STRUCTURE below — how many senses, and which "
           "verses group together. Match it:",
           f"  {roster['count']} senses."]
    for i, g in enumerate(groups, 1):
        out.append(f"  Group {i} keeps together: " + ", ".join(g))
    if roster.get("float"):
        out.append("  Either-home (may sit in either group; do not force a split): "
                   + ", ".join(roster["float"]))
    if roster.get("excluded"):
        out.append("  Not this lemma's sense here (do not cite under any sense): "
                   + ", ".join(roster["excluded"]))
    out.append("Still name each sense and write its meaning from the occurrences above — this "
               "fixes only how many senses and which verses group, from the consensus, never the "
               "wording.")
    return out


def verse_user_msg(sid, translit, gset, ctx, hint=None, pmap=None, constraints=None, roster=None):
    lines = [f"LEMMA: {sid}  ({translit})", ""]
    lines.append("TRANSLATION GLOSS SET (one translation's renderings, with counts):")
    pmap = pmap or {}
    gparts = []
    for g, c in gset[:25]:
        anno = pmap.get(g.lower())
        if anno:
            gparts.append(f"{g} ({c}; always inside a phrase: "
                          + ", ".join(f'"{p}"' + (f" {n}x" if n > 1 else "") for p, n in anno) + ")")
        else:
            gparts.append(f"{g} ({c})")
    lines.append("  " + "; ".join(gparts))
    lines.append("")
    lines.append(f"OCCURRENCES ({len(ctx)}) - context is the primary evidence; rendered-here word in [ ]. "
                 "Where ABP prints a MULTI-WORD phrase on this word's slot, the tag also shows that full "
                 "phrase: analyze the phrase as the rendering, never the bare [here] token alone. "
                 "'added words' are translator additions with no Greek behind them; a phrase can also "
                 "carry words belonging to NEIGHBORING Greek words - the [here] token is this lemma's own. "
                 "Lines marked '~ context' are surrounding verses supplied so names and referents are "
                 "grounded in text you can see; they are NOT occurrences - never cite a context "
                 "reference, and every citation must be one of the occurrence references:")
    lines.extend(_occ_lines(ctx))
    if hint:
        # STRUCTURE-HINT CHANNEL (escalation mechanism, ruled 2026-07-07). Rides in the user message as a
        # CHECK, never in the frozen system prompt. The hint is a prior independent review's stable-jobs list
        # (its own 10-run output = certified ground truth, not a preferred outcome); it names JOBS only, not
        # their wording/count/internal sub-uses, so granularity-as-drawn still governs. Placed AFTER the
        # occurrences so the contexts stay the primary evidence and this reads as a final grouping check.
        lines.append("")
        lines.append("STRUCTURE CHECK (from an independent review of this lemma's FULL occurrence set, not just "
                     "the sample above): repeated review found these STABLE, DISTINCT senses — jobs the lemma "
                     "does that did not merge across draws:")
        for i, job in enumerate(hint, 1):
            lines.append(f"  {i}. {job}")
        lines.append("Use this ONLY as a check that your grouping has not MERGED or BURIED one of these distinct "
                     "jobs (e.g. filed a distinct evaluative or figurative job as a sub-use of the physical "
                     "organ). Still reason from the supplied occurrences and name each job by what the verses "
                     "show. The review names the JOBS, not their wording, count, or internal sub-uses — "
                     "granularity and carving remain yours to draw from the evidence.")
    if constraints:
        # CONSTRAINT-HINT CHANNEL (DESIGN_hint_tooling.md, JP-ruled 2026-07-12). Pre-registered
        # one-line constraints from a parked word's ruling record (draw_hints.py, provenance-cited).
        # Rides in the user message AFTER the occurrences (and after any STRUCTURE CHECK) — frozen
        # system prompt untouched. Fact/discipline/ceiling only, NEVER a preferred sense, count,
        # carve, or any sentence of a prior draft (the incumbent-comparison line, drawn in the
        # design doc and ruled).
        lines.append("")
        lines.append("CONSTRAINT CHECK (pre-registered): independent verification of this lemma's texts "
                     "banked the following one-line constraints BEFORE this draw. Each states a verse's "
                     "own wording, a citation rule, or an attribution ceiling. They are CHECKS, not "
                     "answers — the occurrences above remain the primary evidence; senses, wording, and "
                     "carving remain yours to draw from it:")
        for i, c in enumerate(constraints, 1):
            lines.append(f"  {i}. {c}")
    if roster:
        # ROSTER CHANNEL (path (c)): the floor's consensus sense count + verse groups, injected as
        # soft-explicit context AFTER the occurrences and any other CHECK. Frozen prompt untouched.
        lines.extend(_roster_lines(roster))
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


# ── #28 TAIL EXPANSION (2026-07-12, batch-5 s1; ENGINE_LESSONS #28 / lesson #44). The model
# legally writes citation tails the bare Book-ch:vs catcher cannot see — "Job 42:7–8",
# "Rom 1:1, 4", "Lev 21:10, 21:12" — so tail verses escaped the citation gate, the coverage
# read, AND the double-shelf detector (banked exhibits across five words: χριστός 4/4 draws,
# εἰρηνικός ×5, δόμα ×6, καταπέτασμα ×3, G227 3/3 hinted draws with 42:8 never counted).
# ref_spans() consumes chained tail units after every full match:
#   "–N" / "-N" / "—N"   verse range on the current chapter, enumerated INCLUSIVELY (13–17
#                        yields 13,14,15,16,17 — a range asserts its interior)
#   ", N"                another verse in the current book+chapter
#   ",|; N:M"            another chapter:verse in the current book (semicolon accepted here
#                        only — "; 16:15" is a citation shape; a bare "; 8" is likelier prose)
# TRADE-OFF, accepted on the record: a prose number after a ref-comma ("Gen 41:32, 14 of
# which…") would be swallowed as a phantom citation. The reverse miss has 6+ banked exhibit
# sets; the phantom shape has zero known instances, and the citation gate verse-checks every
# ref so a phantom impossible verse fails LOUDLY. Range spans cap at 30 verses — a wilder
# "range" stops expanding rather than guessing.
# Every numeric tail unit must be a COMPLETE number — digits followed by a letter are the
# start of a NUMBERED BOOK NAME, not a verse ("Jas 1:12, 1Pe 1:6": the ", 1" is 1Peter's
# digit, and swallowing it invented "Jas 1:1"). Caught by the first live resweep run
# (2026-07-12: phantom :1/:2 deltas across the high-frequency cards); control test pins it.
# A BRACKETED ANNOTATION between a ref and its tail must not END the walk (G2787, 2026-07-14).
# The model annotates a verse carrying two occurrences — "Exo 25:14 [x2], 25:15" — because the
# FEED lists one line per OCCURRENCE, so a twice-occurring verse appears twice and the model says
# so. The prose is TRUE and unprompted (VERSE_PROMPT has no such convention). Before this, the
# bracket stopped the tail walker and EVERY ref after it in the chain vanished SILENTLY: G2787's
# coverage gate named 9 absentees of which FIVE WERE CITED IN THE CARD. Not merely a gate-report
# bug — ref_spans feeds build_verses, so a dropped ref never gets its verse attached, and where
# that ref is not also FED nothing fires and the card ships short. That is the silent-undercount
# class this scanner must never recreate (see the docstring).
# SKIP-ONLY, and the scope is load-bearing: the walker may STEP OVER "[...]"; it may NEVER read or
# count what is inside one. Everything the scanner counts, and every conservatism above, is
# unchanged — a digit-bearing bracket ("[see 2:3]") still contributes nothing, and the
# numbered-book guard ("; 2Ch") still holds because that branch never matches a book digit.
_TAIL_UNIT_RE = re.compile(
    r"\s*(?:\[[^\]]*\]\s*)?(?:"                              # step OVER an annotation, never into it
    r"(?P<dash>[–—-])\s*(?P<end>\d+)(?!\d*[A-Za-z:])"        # verse range end
    r"|[,;]\s*(?P<tch>\d+):(?P<tvs>\d+)(?!\d*[A-Za-z:])"     # ", 21:12" / "; 16:15" — new ch:vs
    r"|,\s*(?P<tv>\d+)(?!\d*[A-Za-z:])"                      # ", 4" — same chapter, new verse
    r")")


def ref_spans(text, refusals=None):
    """Every (book, ch, vs) the prose cites, TAILS EXPANDED — the ONE ref scanner behind the
    citation gate, coverage, per-sense counts, LXX provenance, and the double-shelf detector
    (two-derivations rule: they must all see the same refs). Not de-duped; order preserved.
    A refused range (backwards, or span > 30) stops expansion AND, when a `refusals` list is
    passed, records itself — refusals must surface loudly (reviewer condition at merge,
    2026-07-12), never recreate the silent-undercount class at a new threshold. The gate
    report prints them via refused_tails()."""
    out = []
    for m in _REF_RE.finditer(text or ""):
        bk = _norm_book(m.group(1))
        ch, vs = int(m.group(2)), int(m.group(3))
        out.append((bk, ch, vs))
        pos = m.end()
        while True:
            t = _TAIL_UNIT_RE.match(text, pos)
            if not t:
                break
            if t.group("end") is not None:
                end = int(t.group("end"))
                if not (vs < end <= vs + 30):
                    if refusals is not None:
                        refusals.append(f"{bk} {ch}:{vs}{t.group('dash')}{end}")
                    break
                out.extend((bk, ch, v) for v in range(vs + 1, end + 1))
                vs = end
            elif t.group("tch") is not None:
                ch, vs = int(t.group("tch")), int(t.group("tvs"))
                out.append((bk, ch, vs))
            else:
                vs = int(t.group("tv"))
                out.append((bk, ch, vs))
            pos = t.end()
    return out


def refused_tails(text):
    """Range tails ref_spans REFUSED to expand (backwards / span > 30) — the loud channel.
    Same walker, collector flag on; printed at the gate report and by audit_range_tails.py."""
    r = []
    ref_spans(text, refusals=r)
    return r


def cited_refs(text):
    """Pull verse refs (book, ch, vs) out of generated prose — de-duped, in order.
    Tail forms (ranges, comma/semicolon shorthand) expand via ref_spans (#28)."""
    seen, out = set(), []
    for key in ref_spans(text):
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def coverage_gate(fed_refs, senses_block):
    """V9 COVERAGE GATE (JP-ruled 2026-07-12, DESIGN_v9_lines.md): every FED occurrence must
    appear as a citation in the SENSES block — trimming is a ship defect (floor-legal only,
    never ship license; the G2805 clarification moved into code). Scanned by the production
    ref_spans (never a copy), so range-interior and comma/semicolon tail refs count (#28).
    Ref-level: a verse fed twice (Amo 5:5 ×2 class) is covered by one citation. Range/
    gloss-note appearances do NOT count — 'cited under a sense' is the ruled bar.
    Returns the uncited fed refs as 'Book c:v' strings, fed order, de-duped ([] = clean)."""
    cited = set(ref_spans(senses_block or ""))
    out, seen = [], set()
    for key in fed_refs:
        if key in seen:
            continue
        seen.add(key)
        if key not in cited:
            out.append(f"{key[0]} {key[1]}:{key[2]}")
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
# The label's trailing junk is eaten BOUNDED (spaces/colons, at most one closing bold pair, spaces/
# colons) — the old greedy class `[\s:*]*` also swallowed the OPENING asterisk of a body that starts
# with an italic term ("**Gloss notes:** *Calamus* ..." → body "Calamus* ...", G2563 2026-07-08:
# one splitter bite, seven downstream lint artifacts). Known bounded-eater edge, pinned by test:
# a PLAIN label whose body opens bold ("Gloss notes: **term**") still loses that opening pair —
# no draft has produced the shape; the bold-label case ("**Gloss notes:** **term**") is safe because
# the label's own closing pair is consumed first.
_SECTION_RE = re.compile(r'^\s*\*{0,2}\s*(senses|range|gloss notes?|coverage)\b[\s:]*\*{0,2}[\s:]*(.*?)\s*$', re.I)
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
# ONE-SENSE HEADLINE FALLBACK (G2168 εὐχαριστέω 2026-07-10): a genuinely one-job word drawn
# in the V8 house shape numbers nothing — single bold headline, organizing paragraph,
# Sub-uses — so both numbered finders come back empty and the card scored 0 senses (7/10
# reviewer draws). Fires ONLY when neither numbered form exists AND the block OPENS with a
# bold span; a numbering botch on a multi-sense card cannot reach it silently because every
# fallback parse is printed loudly (sense_split_mode) in floor + dry-run output.
_LONE_HEADLINE_RE = re.compile(r'\A\s*\*\*\s*([^*]+?)\s*\*\*')


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
    if out:
        return out
    m = _LONE_HEADLINE_RE.match(block)
    if m:
        return [(m.group(1).strip(), block[m.end():])]
    return []


def sense_split_mode(block):
    """How the senses split: 'bold' | 'plain' | 'headline' (one-sense fallback) | 'none'.
    Display-only probe — never changes a parse; it is the ONE source of the loud
    '[1 sense — headline fallback]' marker the floor and dry-run outputs print."""
    block = block or ""
    if _HEADLINE_RE.search(block):
        return "bold"
    if _PLAIN_HDR.search(block):
        return "plain"
    if _LONE_HEADLINE_RE.match(block):
        return "headline"
    return "none"


def split_definition(prose):
    """Split the engine's prose into fields at the parts that are STABLE across words: the bold
    section headers and the bold numbered sense headlines. Each section's body is kept VERBATIM
    for the full view; only the headlines are pulled out for the glance. We never peel refs off a
    sense, so a formatting quirk can at worst show a little extra on the glance — never mis-file a
    ref under the wrong sense."""
    lines = (prose or "").splitlines()
    sections = OrderedDict()
    cur = None
    preamble = []                                 # lines BEFORE the first section header
    for ln in lines:
        m = _SECTION_RE.match(ln)
        if m:
            cur = m.group(1).lower()
            # "Gloss note:" SINGULAR (G2168 draws 2026-07-10): a legal label variant the plural-only
            # pattern missed — the note leaked into Range (reader-facing) and gloss_notes came back
            # empty. Normalize the captured name so both spellings file to the same field.
            if cur == "gloss note":
                cur = "gloss notes"
            sections.setdefault(cur, [])
            rest = m.group(2).strip()
            if re.fullmatch(r'\(.*?\)\s*:?', rest):   # a lone "(ordered ...):" tail — not body text
                rest = ""
            if rest:                                  # label AND text shared one line — keep the text
                sections[cur].append(rest)
            continue
        (sections[cur] if cur is not None else preamble).append(ln)

    def body(title):
        out = "\n".join(sections.get(title, [])).strip()
        out = re.sub(r'^-{3,}\s*', '', out)      # drop a leading --- rule
        out = re.sub(r'\s*-{3,}\s*$', '', out)   # drop a trailing --- rule
        # A `---` rule LINE BETWEEN senses is neither leading nor trailing, so the two edge-strips
        # above miss it (ἔργον 2026-07-08: the model put `---` between sense 1 and sense 2; the
        # ὄρος fix `9a1dca9` only covered the leading/title case). Drop any standalone hr line
        # anywhere in the block, then collapse the blank run the cut leaves behind.
        out = re.sub(r'(?m)^[ \t]*-{3,}[ \t]*$', '', out)
        out = re.sub(r'\n{3,}', '\n\n', out)
        return out.strip()

    # Some drafts OMIT the "Senses:" header and dive straight into bold-numbered senses (sometimes
    # after a title line the prompt asked them not to write). Fall back to the pre-section text, but
    # ONLY when it actually holds numbered sense headlines — so a stray preamble sentence is never
    # mistaken for senses, and there is zero change when a proper "Senses" header IS present.
    if not sections.get("senses"):
        pre = "\n".join(preamble).strip()
        # Such a draft often opens with a TITLE line and/or a --- rule the prompt asked it NOT to
        # write. The old leading-`---` strip missed them when the title came FIRST (ὄρος 2026-07-07:
        # `**G3735 ὄρος (óros)**` then `---` leaked into senses_block). Drop everything before the
        # first numbered-sense headline so nothing pre-sense survives.
        m = re.search(r'^\s*\*\*\s*\d+\.', pre, re.M)
        if m:
            pre = pre[m.start():]
        pre = re.sub(r'\s*-{3,}\s*$', '', pre).strip()   # trailing rule (leading cut handles the rest)
        if _sense_spans(pre):
            sections["senses"] = [pre]

    senses_block = body("senses")
    headlines = [lead for lead, _ in _sense_spans(senses_block)]
    return {
        "sense_headlines": headlines,
        "senses_block":    senses_block,
        "range":           body("range"),
        "gloss_notes":     body("gloss notes"),
        "coverage":        body("coverage"),
    }


# A line that is ENTIRELY one bold span — a draft's title/lemma restatement ("**G3735 ὄρος (óros)**").
# The negative lookahead keeps the SENSE-headline shape (**1. ...**) out: those are the card itself.
_LONE_TITLE_LINE_RE = re.compile(r'\A\s*\*\*\s*(?!\d+\.)[^*]+?\s*\*\*\s*\Z')
_HR_LINE_RE = re.compile(r'\A\s*-{3,}\s*\Z')


def leading_boilerplate(prose):
    """REPORT-ONLY detector (G162 preamble-leak ticket, reviewer-ruled BUILD 2026-07-14): surface
    the prose a draft puts BEFORE its card.

    WHY IT EXISTS — A SILENT DISCARD. Both prompts forbid this text (VERSE_PROMPT: "No preamble, no
    restating the lemma, no closing summary"; the repair prompt's card-only contract at :1896) and
    NOTHING checked it — verified against the full detector enumeration in offline_gate_check.py.
    split_definition DROPS this text in EVERY path, so a draw that breached the output contract read
    gate-clean (G162's archived card: a working note leaked into the body, warns 0, gate-invisible).
    The leak never reaches a reader (split_definition drops it; views_lexica.py pops `raw`) — so this
    buys a DRAW-HEALTH signal, not reader protection. Containment lowers the stakes, not the
    obligation: the Silent-Fallback Rule forbids leaving the discard silent.

    THE CUT MIRRORS split_definition (never re-derived): text before the first section header, cut
    again at the first bold-numbered headline so the headerless-senses fallback shape never has its
    own senses called boilerplate. Blank lines and `---` rules drop out — formatting noise, not a
    claim. What survives is a contract breach, tagged:
      meta  — working-note prose ("Here is the corrected definition ..."). THE kill class.
      title — a bare lemma/title restatement. Known-benign shape (ὄρος 2026-07-07: the splitter
              already handles it), still a breach, tagged APART so the two classes can be SIZED
              separately before any block rule is written.

    REPORT-ONLY, deliberately: NO block rule, NO stored field, no caller may refuse a card on this.
    An open warn blocks apply (the probe2/scan3 rule), so a day-one block would stop a rebuild of
    every live card carrying a leak. The block decision is its own reviewed step, sized off a sweep
    (meta:v5 blast-radius precedent).
    """
    pre = []
    for ln in (prose or "").splitlines():
        if _SECTION_RE.match(ln):
            break
        pre.append(ln)
    text = "\n".join(pre)
    m = re.search(r'^\s*\*\*\s*\d+\.', text, re.M)   # the headerless-senses fallback's own cut
    if m:
        text = text[:m.start()]

    fires, meta = [], []

    def flush():
        if meta:
            fires.append({"kind": "meta", "text": "\n".join(meta).strip()})
            meta.clear()

    for ln in text.splitlines():
        if not ln.strip() or _HR_LINE_RE.match(ln):
            continue
        if _LONE_TITLE_LINE_RE.match(ln):
            flush()                                  # keep appearance order between the two kinds
            fires.append({"kind": "title", "text": ln.strip()})
        else:
            meta.append(ln.strip())                  # consecutive prose = ONE fire, so a count sizes
    flush()                                          # the CLASS, not the line breaks in it
    return fires


def sense_provenance(senses_block):
    """Per-sense LXX provenance, ALIGNED to sense_headlines order. Splits the Senses prose at the
    same bold '**N. …**' markers the headlines come from, counts each sense's grounding refs by
    testament (OT = Septuagint / NT = Koine), and decides whether the subordinate LXX note fires
    (high + well-attested OT share). Derived from the stored citations only — no model. Returns
    [{ot, nt, lxx}], one per sense, in headline order, so the card can hang the note per sense."""
    out = []
    for lead, bodytext in _sense_spans(senses_block or ""):
        seen, ot, nt = set(), 0, 0
        for bk, ch, vs in ref_spans(bodytext):        # #28: tails expanded
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
        for bk, ch, vs in ref_spans(body):            # #28: tails expanded
            key = (bk, ch, vs)
            if key not in seen:
                seen.add(key)
                refs.append(key)
        out.append({"headline": lead, "refs": refs})
    return out


_PAREN_INNER_RE = re.compile(r"\(([^()]*)\)")


def _grounding_refs(text):
    """Refs from CITATION-LIST parentheticals only: parens whose content is refs (+ separators,
    ×N occurrence marks, 'LXX'). A paren carrying prose words is a MENTION per the house
    convention (legal cross-reference form), not a grounding citation — the G162 d3 Amo 1:6
    false double-shelve warn (prose-mention-counted-as-citation noise class, fixed on the record
    2026-07-12). Coverage still reads ALL refs (sense_specs unchanged) — fail-open there, so a
    mention can never HIDE a coverage gap; only the double-shelve flag narrows to grounding lists."""
    refs = []
    for m in _PAREN_INNER_RE.finditer(text or ""):
        inner = m.group(1)
        found = ref_spans(inner)                      # #28: tails expanded
        if not found:
            continue
        leftover = _CHAP_ONLY_RE.sub(" ", _REF_RE.sub(" ", inner))
        words = re.findall(r"[A-Za-z]+", leftover)
        if all(w.lower() in ("lxx", "x") for w in words):   # 'x2' occurrence marks split to 'x'
            refs.extend(found)
    return refs


def double_shelved(senses_block):
    """FLAG-ONLY detector: any verse GROUNDING-CITED under MORE THAN ONE sense in the same draft.
    Reads the same splitter (_sense_spans) + ref regex (_REF_RE) + book normalizer (_norm_book) as
    the rest of the build, but counts only citation-list parentheticals (_grounding_refs) — a bare
    prose mention of another sense's verse is the convention's legal cross-reference, not a second
    shelving. NOT a gate: double-shelving is sometimes legitimate (a genuinely bridging verse), so
    it becomes a conscious per-word adjudication in the audit output, never an automatic reject.
    Returns [{ref, senses:[1-based sense numbers]}] in a stable order (first sense, then ref)."""
    where = {}   # (book, ch, vs) -> set of 1-based sense numbers it's cited under
    for i, (lead, body) in enumerate(_sense_spans(senses_block or ""), 1):
        for key in _grounding_refs(f"{lead}\n{body}"):
            where.setdefault(key, set()).add(i)
    out = []
    for (bk, ch, vs), senses in where.items():
        if len(senses) > 1:
            out.append({"ref": f"{bk} {ch}:{vs}", "senses": sorted(senses)})
    out.sort(key=lambda d: (d["senses"][0], d["ref"]))
    return out


# ── V7 flag-only detector suite (window walk, 2026-07-08). Same design family as double_shelved:
# every one is a FLAG, never a gate — a fire is a conscious per-word adjudication in the audit
# output. Each was born from an archived defect and control-fires on it (tests/test_lexica_detectors.py).

_GNOTE_BULLET_RE = re.compile(r"(?:^|\n)\s*-\s+")
_GNOTE_GLOSS_RE = re.compile(r"\*([^*\n]+)\*")


def _gnote_claims(gloss_notes):
    """Parse gloss_notes into checkable rendering claims: each bullet's *italic gloss(es)* + the
    refs in its head parenthetical (the shipped-corpus bullet shape, '- *gloss* (Ref; Ref): ...').
    Bullets without that shape are SKIPPED — this parser deliberately under-catches; the standing
    manual rule (gloss-note assertion spot-check) remains the authority."""
    claims = []
    for bullet in _GNOTE_BULLET_RE.split(gloss_notes or ""):
        if not bullet.strip():
            continue
        head = bullet.split("):", 1)[0]          # the claim head: up to the close of the ref paren
        # Glosses are read ONLY from before the ref paren opens ('- *gloss* (Refs):'). Italics
        # further in are EMPHASIS, not rendering claims — the G162 d1 *perform* false warn
        # (emphasis-italics-as-gloss noise class, fixed on the record 2026-07-12).
        glosses = _GNOTE_GLOSS_RE.findall(head.split("(", 1)[0])
        refs = ref_spans(head)                        # #28: tails expanded
        if glosses and refs:
            claims.append({"glosses": [g.strip() for g in glosses], "refs": refs})
    return claims


def check_rendering_claim(glosses, rends, verse_text="", phrases=None):
    """PURE core of the rendering-claim lint (ENGINE_LESSONS #24 machine-check; two archived
    control fires: οὐρανός capitalization, ἁμαρτία 2Co 5:21). Compares a note's claimed gloss(es)
    against the lemma's ACTUAL per-verse rendering(s) (words-table english_head) — NOT the verse
    prose, because a claimed 'sin' is a substring of the true 'sin offering' and prose containment
    would pass exactly the archived defect.

    CASE-AWARENESS IS LOAD-BEARING — do not 'clean up' the case-sensitive compare or the
    sentence-position probe. The οὐρανός fire is the reason: the fabricated note claimed
    capitalized 'Heaven' was an editorial/theological marker; the rendering really IS capitalized
    at the cited refs, and only the POSITION check (sentence-initial capitalization is mechanical
    English, not editorial intent) exposes the false premise. A case-folded compare reads that
    card as clean.

    Returns a list of fire dicts ({} entries absent = clean):
      kind='rendering-mismatch'  claimed gloss is not the rendering at this ref (ἁμαρτία class)
      kind='case-mismatch'       matches only after case-folding (claimed 'Heaven', rend 'heaven')
      kind='positional-cap'      claim matches a capitalized rend, but the gloss sits
                                 sentence-initial in the verse prose (οὐρανός class) — the
                                 capitalization may be positional, adjudicate the note's rationale

    PHRASE-AWARENESS (2026-07-12 fragment-rendering fix): `phrases` = the slot's full ABP phrase
    gloss(es) at this ref, each as (phrase, italic_words). A claim is ALSO clean when it equals the
    FULL phrase or the phrase minus its translator additions — 'latticed work' claimed where the
    head keeps only 'work' (2Ch 4:13) is a true rendering claim, not a mismatch. Equality is
    WHOLE-string (punctuation-stripped): a claim that is merely CONTAINED in the phrase still fires
    (the archived ἁμαρτία 'sin' vs 'sin offering' defect — containment must never pass).
    Punctuation-stripped comparison also kills the identical-string noise class ('exchange,' vs
    'exchange' read as a mismatch, G236 exhibits)."""
    fires = []
    rends = [r for r in (rends or []) if r]
    if not rends:
        return fires                              # ref carries no rendering row — nothing checkable
    # Candidate render strings, comparison-form: the heads, plus each full phrase and each
    # phrase-minus-additions. Case preserved throughout (case-awareness above).
    cands = [_phrase_clean(r) for r in rends]
    for phr, ital in (phrases or []):
        full = _phrase_clean(phr)
        if len(full.split()) > 1:
            cands.append(full)
            own = _phrase_minus_italics(phr, ital)
            if own and own != full:
                cands.append(own)
    cands = [c for c in cands if c]
    for g in glosses:
        gq = _phrase_clean(g)
        exact = [c for c in cands if c == gq]
        folded = [c for c in cands if c.lower() == gq.lower()]
        if exact:
            if gq[:1].isupper() and verse_text:
                for m in re.finditer(re.escape(gq), verse_text):
                    before = verse_text[:m.start()].rstrip()
                    if not before or before[-1] in ".!?;":
                        fires.append({"kind": "positional-cap", "gloss": g})
                        break
        elif folded:
            fires.append({"kind": "case-mismatch", "gloss": g, "rend": folded[0]})
        else:
            near = [c for c in cands if gq.lower() in c.lower() or c.lower() in gq.lower()]
            fires.append({"kind": "rendering-mismatch", "gloss": g,
                          "rend": (near[0] if near else " / ".join(sorted(set(cands))[:4]))})
    return fires


def _claim_fires(glosses, per_ref):
    """V11.1 ticket 5 (ruled 2026-07-12) — per-bullet SET semantics for one gloss-note claim,
    superseding every-gloss-at-every-ref (the G236 d1 six-coarse-fires class: a bullet listing
    several glosses across several refs means 'distributed across', never 'each at every').
    per_ref = ordered {refkey: (rends, verse_text, phrases)}, refs limited to the lemma's own
    verses (the wrapper's job). Rules, each fixture-pinned in test_lexica_detectors.py:
      · each claimed gloss must be clean at ≥1 ref; clean NOWHERE = ONE fire (case-mismatch
        preferred over plain mismatch as the reported kind — the more informative defect);
      · positional-cap flags at exact-match refs always survive (the οὐρανός class);
      · a ref no claimed gloss matches fires once — but only when some other gloss DID match
        somewhere, so the single-gloss/single-ref anchor (Psa 106:20 class) keeps exactly one
        fire, never a double count.
    Composes the UNCHANGED check_rendering_claim core (its pins all stand)."""
    out = []
    matched_refs, any_gloss_matched = set(), False
    for g in glosses:
        results = []
        for key, (rends, vtext, phrases) in per_ref.items():
            results.append((key, check_rendering_claim([g], rends, vtext, phrases)))
        clean = [(k, f) for k, f in results if not f]
        poscap = [(k, f) for k, f in results
                  if f and all(x["kind"] == "positional-cap" for x in f)]
        if clean or poscap:
            any_gloss_matched = True
            matched_refs.update(k for k, _ in clean + poscap)
            for k, f in poscap:
                out.extend({**x, "ref": f"{k[0]} {k[1]}:{k[2]}"} for x in f)
        else:
            k, f = next(((k, f) for k, f in results
                         if any(x["kind"] == "case-mismatch" for x in f)), results[0])
            x = next((y for y in f if y["kind"] == "case-mismatch"), f[0])
            out.append({**x, "ref": f"{k[0]} {k[1]}:{k[2]}"})
    if any_gloss_matched:
        for key, (rends, _v, _p) in per_ref.items():
            if key not in matched_refs:
                out.append({"kind": "rendering-mismatch", "gloss": "(no claimed gloss)",
                            "rend": " / ".join(sorted({r for r in rends if r})),
                            "ref": f"{key[0]} {key[1]}:{key[2]}"})
    return out


def gloss_note_claims(conn, sid, gloss_notes):
    """FLAG-ONLY production wrapper: every parseable gloss-note rendering claim checked against the
    lemma's real per-verse renderings + verse prose, under _claim_fires' per-bullet set semantics
    (V11.1 ticket 5). Degrades to [] on any error (report, not gate)."""
    out = []
    claims = _gnote_claims(gloss_notes)
    if not claims:
        return out
    try:
        pred, params = abp_filter(conn, sid)
        occs = occurrences(conn, pred, params)
    except Exception:
        return out
    rend_at, phrase_at = {}, {}
    for o in occs:
        key = (_norm_book(o["book"]), o["ch"], o["vs"])
        rend_at.setdefault(key, []).append((o["rend"] or "").strip())
        phrase_at.setdefault(key, []).append(((o["phrase"] or ""), (o["ital"] or "")))
    for c in claims:
        per_ref = {}
        for key in c["refs"]:
            if key not in rend_at:
                continue                          # note ref isn't one of this lemma's verses — not a rendering claim
            row = conn.execute("SELECT text FROM verses WHERE book=? AND chapter=? AND verse=?",
                               key).fetchone()
            per_ref[key] = (rend_at[key], (row["text"] if row else "") or "",
                            phrase_at.get(key))
        if per_ref:
            out.extend(_claim_fires(c["glosses"], per_ref))
    return out


# Membership-hedging phrases (standing rule 7c's machine assist). DELIBERATELY NON-EXHAUSTIVE —
# a draw can hedge in words this list lacks. A lint PASS is NOT 7c satisfied; only a FIRE is
# meaningful. The human read of each sense's prose remains the standing authority.
_HEDGE_PHRASES = ("may overlap", "might overlap", "without reducing to", "could belong",
                  "may belong", "may straddle", "arguably under", "perhaps under",
                  "does not quite reduce")


def hedged_citations(senses_block):
    """FLAG-ONLY: a sense's own prose hedging a citation's membership (rule 7c; control fire =
    the archived δύναμις pull-2 Neh 9:6 hedge). Invisible to the citation gate (ref real) and the
    freight scan (nothing loaded) — this is the coherence check ENGINE_LESSONS #25a asked for."""
    out = []
    for i, (lead, body) in enumerate(_sense_spans(senses_block or ""), 1):
        low = f"{lead} {body}".lower()
        for h in _HEDGE_PHRASES:
            if h in low:
                out.append({"sense": i, "hedge": h})
    return out


def subuse_overload(senses_block, max_ok=3):
    """FLAG-ONLY: any sense carrying 4+ Sub-uses gets a merge-review flag (pile item 11, window
    walk). NO hard ceiling by design — forcing merges is the #14 silent-facet-drop path (πολύς);
    a fire means a human asks the 7b-style question, never an automatic reject. Control positive:
    ῥῆμα G4487 sense 1 shipped at exactly 4 Sub-uses (a ruled-legitimate card — the flag marks
    'look', not 'wrong')."""
    out = []
    for i, (lead, body) in enumerate(_sense_spans(senses_block or ""), 1):
        n = len(re.findall(r"\bSub-use:", body))
        if n > max_ok:
            out.append({"sense": i, "subuses": n})
    return out


# ── #30 floor-vs-ship placement diff (ENGINE_LESSONS #30, un-parked at close-out step 4,
# 2026-07-10). Born γόνυ (invented sub-use moved Luk 5:8 + 2Ki 1:13 off their 3/3 floor homes,
# every other gate green), confirmed νίπτω (unanimous Psalms cluster broken onto an invented
# sense), hardest class κατανοέω hint-1 (one 0/10 placement inside an otherwise-PASSING draw).
# Both structures — the floor's per-verse company and the ship draw's shelves — exist as
# artifacts at gate time; this diffs them. FLAG-ONLY, same family as double_shelved: a fire is
# a conscious per-word adjudication. Fire CLASSES and their count consequences get DEFINED at
# the step-5 control fire, before the final-10 window opens (banked build note, step-4 opener);
# until then fires are judgment-class under the ruled taxonomy, and an adjudicated-noise fire
# must not disqualify a count ship (the ὑπομονή precedent extends only to recognition-class).

_FLOOR_REF_RE = re.compile(r"(\S+)\s+(\d+):(\d+)")


def _floor_ref_key(s):
    """'Luk 5:8' -> ('Luk', 5, 8); None on a malformed ref (dropped — mirrors the reviewer's own
    unknown-book filter, which already keeps model typos out of the floor's company math)."""
    m = _FLOOR_REF_RE.match((s or "").strip())
    return (_norm_book(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def load_floor(path, sid=None):
    """Read a saved lexica_agreement run (agreement_<SID>_<prompt>_<ts>.json) into the shape
    floor_ship_diff eats: per draw, a list of senses, each a set of (book, ch, vs). Hard-errors
    on a strongs mismatch — diffing a word against another word's floor is never meaningful.
    Freshness is the operator's call (a corpus data fix INVALIDATES a saved floor — the free
    re-read is only valid while the data under it is unchanged), so the meta rides along and is
    printed at the gate for the audit record."""
    with open(os.path.expanduser(path), encoding="utf-8") as f:
        p = json.load(f)
    if sid and p.get("strongs") != sid:
        sys.exit(f"  ✗ --floor {path}: file is for {p.get('strongs')}, not {sid} — wrong floor, "
                 f"not diffed.")
    draws = []
    for d in p.get("draws", []):
        senses = []
        for s in d.get("senses", []):
            refs = {k for k in (_floor_ref_key(r) for r in s.get("refs", [])) if k}
            if refs:
                senses.append(refs)
        draws.append(senses)
    return {"draws": draws,
            "meta": {"file": os.path.basename(path), "strongs": p.get("strongs"),
                     "prompt": p.get("prompt"), "runs": p.get("runs", len(draws))}}


def consensus_pairs(floor_draws, majority=None):
    """Unordered verse-pair -> #floor draws sharing a sense, MAJORITY pairs only (default:
    strict majority, N//2+1). Extracted from floor_ship_diff so the floor-subsample checker
    (scripts/floor_subsample.py) reuses the SAME pair logic — one copy ever, never a second
    scan/transform implementation (ENGINE_LESSONS #6)."""
    n = len(floor_draws)
    if not n:
        return {}
    if majority is None:
        majority = n // 2 + 1
    same = Counter()                      # unordered verse pair -> #floor draws sharing a sense
    for senses in floor_draws:
        pairs = set()
        for refs in senses:
            sv = sorted(refs)
            for i in range(len(sv)):
                for j in range(i + 1, len(sv)):
                    pairs.add((sv[i], sv[j]))
        for pr in pairs:
            same[pr] += 1
    return {pr: c for pr, c in same.items() if c >= majority}


def floor_ship_diff(floor_draws, ship_senses, majority=None):
    """PURE core of the #30 flag. The mechanical check is CLUSTER MEMBERSHIP, not sense count
    (the νίπτω ruling): a verse pair that shared a sense in >= `majority` floor draws (default:
    strict majority, N//2+1) is a CONSENSUS PAIR, and the flag fires when the ship draw SPLITS
    such a pair across different senses. Merging two floor clusters into one ship sense never
    fires — hierarchy demotion is not a cluster break (δίκτυον's fold was ruled LEGAL; it is
    this flag's clean negative). Either-home migrators flip draw-to-draw, so their cross-pole
    company sits below any strict majority and they stay silent by construction.

    floor_draws: per floor draw, a list of senses, each a set of (book, ch, vs).
    ship_senses: sense_specs()-shaped [{headline, refs:[(book,ch,vs)]}] for the ship draw.

    Fires report the MOVER side of each break — the verse that lost at least as many consensus
    partners as it kept — so one break reads once (its stationary partners keep most of their
    company and stay suppressed). A double-shelved ship verse counts as "with" a partner if ANY
    shelf is shared, the floor's own company convention. Returns
    [{ref, ship_senses, kept:[refs], broken:[{ref, same, n, ship_senses}]}], ship-ref order."""
    n = len(floor_draws)
    if not n:
        return []
    if majority is None:
        majority = n // 2 + 1
    consensus = {}                        # verse -> {partner: same-count}, majority pairs only
    for (a, b), c in consensus_pairs(floor_draws, majority).items():
        consensus.setdefault(a, {})[b] = c
        consensus.setdefault(b, {})[a] = c
    ship_at = {}                          # verse -> set of 1-based ship sense numbers
    for i, s in enumerate(ship_senses, 1):
        for key in s["refs"]:
            ship_at.setdefault(key, set()).add(i)
    fmt = lambda k: f"{k[0]} {k[1]}:{k[2]}"
    fires = []
    for v in sorted(ship_at):
        present = {w: c for w, c in consensus.get(v, {}).items() if w in ship_at}
        if not present:
            continue
        kept = sorted(w for w in present if ship_at[v] & ship_at[w])
        broken = sorted(w for w in present if not (ship_at[v] & ship_at[w]))
        if broken and len(broken) >= len(kept):
            fires.append({"ref": fmt(v), "ship_senses": sorted(ship_at[v]),
                          "kept": [fmt(w) for w in kept],
                          "broken": [{"ref": fmt(w), "same": present[w], "n": n,
                                      "ship_senses": sorted(ship_at[w])} for w in broken]})
    return fires


def floor_diff_record(floor, senses_block, majority=None):
    """Assemble the #30 audit record for a draft: the fires PLUS the floor-unseen ship citations.
    #30 has no floor data on a verse the floor never cited — those stay the σελήνη-class manual
    check (verify against the occurrence table), and they are listed so an empty fires list can
    never read as 'every citation checked'."""
    specs = sense_specs(senses_block)
    n = len(floor["draws"])
    maj = majority if majority is not None else n // 2 + 1
    floor_seen = set()
    for senses in floor["draws"]:
        for refs in senses:
            floor_seen |= refs
    ship_refs = {k for s in specs for k in s["refs"]}
    return {"file": floor["meta"]["file"], "prompt": floor["meta"]["prompt"], "runs": n,
            "majority": maj, "fires": floor_ship_diff(floor["draws"], specs, maj),
            "floor_unseen": [f"{b} {c}:{v}" for b, c, v in sorted(ship_refs - floor_seen)]}


def roster_count_diff(roster, senses_block):
    """#55 SENSE-COUNT GUARD (PATH (c) DESIGN — CLOSED, 2026-07-13). The roster fixes HOW MANY
    senses the floor's consensus carries; this guard fires when the ship draw lands a DIFFERENT
    count — a collapse (G1390 died 2→1) or a split. It closes the blindness the pair-membership
    #30 check has when a whole pole VANISHES: no consensus pair is split (nothing to fire on),
    yet the structure is wrong. PART of path (c)'s definition, not optional hardening.

    Returns {floor, roster_count, ship_count, ok}; ok=False is a FIRE (count mismatch). The ship
    count is the number of numbered senses the splitter found (sense_specs, the same parse #30
    and coverage read), so this sees exactly the card's own sense structure."""
    ship = len(sense_specs(senses_block))
    rc = roster["count"]
    return {"floor": roster.get("floor"), "roster_count": rc, "ship_count": ship, "ok": ship == rc}


def registry_verse_hits(refs):
    """CONTESTED-VERSE REGISTRY routing (ENGINE_LESSONS #24 ῥῆμα refinement; JP-ruled 2026-07-08).
    Any cited ref that sits in contested_register.CONTESTED_VERSES comes back with its fork note
    and dossier bar. NOT a flag to adjudicate away: a hit means every descriptive claim touching
    that verse gets verse-text verification MANDATORILY before gate time, and the word leaves the
    zero-read tier. Routing is by list membership — never by auditor smell."""
    out = []
    for key in refs or []:
        e = CONTESTED_VERSES.get(tuple(key) if not isinstance(key, tuple) else key)
        if e:
            out.append({"ref": f"{key[0]} {key[1]}:{key[2]}", **e})
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


def draw_signature(sid, translit, gset, ctx, hint=None, pmap=None, constraints=None, roster=None):
    """Hash of the EXACT model input — system prompt + the full user message + the model id. Any
    change to the prompt, the fed verse sample (a words rebuild moving select_spread, a --budget
    change), the verse prose, the gloss set, or the model produces a DIFFERENT signature. A stored
    draw can only count as a hit when it was drawn from byte-identical input, so a stale draw can
    never silently apply. (OCC_MIN/MAX_TOKENS are deliberately out — OCC_MIN only gates whether a
    word builds; MAX_TOKENS is out for the same reason it's out of synth_ver.)

    SIGNATURE-FOLD (path (c), mandatory): the roster rides in the user message, so a roster-anchored
    draw hashes DIFFERENTLY from an unanchored one — it can never key-collide with, and silently
    reuse, a draw drawn without its floor-consensus context."""
    user = verse_user_msg(sid, translit, gset, ctx, hint, pmap, constraints, roster)
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


def archive_draw(sid, new_sig, new_prose_sha):
    """V11.2 DRAW-CACHE HISTORY (ruling 5, 2026-07-12): a superseded draw is MOVED into
    draws/history/, never overwritten — a repair mechanism that rewrites raws makes preserved
    draw history load-bearing (the ELEVATED evidence-cost record: V11.1 paid for its absence
    twice, the d1 raws unrecoverable). A byte-identical refresh (same sig AND same prose_sha)
    is not a supersession and is not archived. An UNREADABLE old file is archived too —
    evidence is never discarded on a parse error. history/ rides draws/' gitignore."""
    p = draw_path(sid)
    if not os.path.exists(p):
        return
    old = load_draw(sid)                    # None = unreadable; still archived below
    if old and old.get("sig") == new_sig and old.get("prose_sha") == new_prose_sha:
        return
    hdir = os.path.join(DRAWS_DIR, "history")
    os.makedirs(hdir, exist_ok=True)
    created = re.sub(r"[^0-9T]", "", (old or {}).get("created", "") or "") or "undated"
    base = f"{sid}_{created}_{((old or {}).get('sig') or 'unreadable')[:8]}"
    dest = os.path.join(hdir, base + ".json")
    n = 1
    while os.path.exists(dest):
        n += 1
        dest = os.path.join(hdir, f"{base}_{n}.json")
    os.replace(p, dest)
    # ASCII arrow on purpose: this line runs inside CI'd tests (test_draw_history) and the
    # Windows console is cp1252 — a '→' here would crash the suite, not just look plain.
    print(f"  superseded draw archived -> {dest}")


def bank_refused_repair(sid, kind, rec):
    """V11.2 ticket 1 (design-review prerequisite): a repair the guard REFUSED (or that
    capped out) has its discarded output written to draws/history/ as evidence — the
    0-for-3 review can't tell prompt-failure from guard-overstrictness without the bytes.
    Evidence ONLY: never re-read as a draw, never shipped (NO-APPLY-EVER covers the dir),
    and a write failure NEVER changes the DEAD outcome (wrapped, print-and-continue).
    The `_refused_` infix keeps these nominally distinct from archived draw cards.
    Returns the dest path, or None (nothing to bank / write skipped)."""
    if not rec or "refused_post" not in rec:
        return None
    try:
        hdir = os.path.join(DRAWS_DIR, "history")
        os.makedirs(hdir, exist_ok=True)
        key = ((load_draw(sid) or {}).get("sig") or "unkeyed")[:8]
        base = f"{sid}_{kind}_refused_{key}"
        dest = os.path.join(hdir, base + ".json")
        n = 1
        while os.path.exists(dest):
            n += 1
            dest = os.path.join(hdir, f"{base}_{n}.json")
        with open(dest, "w", encoding="utf-8") as f:
            json.dump({"strongs": sid, "kind": kind, "key": key,
                       "fails": rec.get("fails", []), "pre": rec.get("pre", ""),
                       "refused_post": rec["refused_post"],
                       "prompt_ver": rec.get("prompt_ver", "")},
                      f, ensure_ascii=False, indent=2)
        # ASCII arrow on purpose (cp1252 CI console, per archive_draw).
        print(f"  refused repair banked -> {dest}")
        return dest
    except Exception as e:
        print(f"  (refused-repair bank skipped: {e})", file=sys.stderr)
        return None


def save_draw(sid, lemma, translit, gset, ctx, raw, forced=None, hint=None,
              pmap=None, constraints=None, no_hints_reason=None, repair=None,
              qrepair=None, roster=None):
    """Write (or refresh) the reviewed draw. Called ONLY by the ro pass and --force — an unreviewed
    fresh apply must never leave a draw file that would later look reviewed. Atomic replace so a
    crash mid-write can't leave a torn file. `forced` = any --force-verse refs added to the fed
    sample (coverage override); `hint` = any --structure-hint stable-jobs list injected as draw
    context (escalation mechanism). Both recorded so the draw self-documents why it was fed/framed."""
    os.makedirs(DRAWS_DIR, exist_ok=True)
    sig = draw_signature(sid, translit, gset, ctx, hint, pmap, constraints, roster)
    rec = {
        "strongs":   sid,
        "lemma":     lemma,
        "translit":  translit,
        "model":     MODEL_SONNET,
        "synth_ver": synth_ver(),
        "fed":       len(ctx),
        "forced":    forced or [],  # --force-verse refs (coverage override, FLOW step 1.5); [] = pure sampler
        "forced_why": ("post-floor coverage-completeness: MISSED-collocation idiom/job the deterministic "
                       "sampler skipped (not steering)") if forced else "",
        "structure_hint": hint or [],  # --structure-hint stable-jobs list (escalation mechanism); [] = no hint
        "structure_hint_why": ("escalation mechanism (cap-out): a prior review's certified stable-jobs list "
                               "passed as draw CONTEXT to prevent burying/merging a distinct job; frozen "
                               "prompt untouched, names jobs not carving") if hint else "",
        # CONSTRAINT hints (--hints; DESIGN_hint_tooling.md, JP-ruled 2026-07-12). The exact lines
        # injected + their register provenance, so the draw self-documents what it saw. Part of
        # sig (they ride in the user message), so a hint change forces a fresh draw.
        "draw_hints": constraints or [],
        "draw_hints_provenance": (DRAW_HINTS.get(sid, {}).get("provenance", "") if constraints else ""),
        "draw_hints_why": ("pre-registered constraint hints (parked-word re-entry): fact/discipline/"
                           "ceiling lines from the park ruling record, injected as draw CONTEXT after "
                           "the occurrences; frozen prompt untouched, never names a preferred sense "
                           "or carve") if constraints else "",
        # PATH (c) ROSTER (--roster; PATH (c) DESIGN — CLOSED, 2026-07-13). The floor-consensus
        # structure this draw was anchored to (count + verse groups), so the draw self-documents
        # its anchor. Part of sig (rides the user message), so a roster change forces a fresh draw.
        "roster": roster or {},
        "roster_why": ("path (c) floor-consensus roster injected as soft-explicit draw context "
                       "(sense count + verse groups from the word's saved floor); frozen prompt "
                       "untouched, fixes count/grouping only, never the wording") if roster else "",
        # --no-hints override on a registered word (ruling 1's logged escape hatch); "" = normal run.
        "no_hints_reason": no_hints_reason or "",
        # V10 REPAIR PASS stamps (DESIGN_v10_repair.md): a repaired draw is visibly repaired
        # everywhere the record is read. [] / 0 / "" = the draw never needed repair.
        "repaired":          (repair or {}).get("refs", []),
        "repair_rounds":     (repair or {}).get("rounds", 0),
        "repair_prompt_ver": (repair or {}).get("prompt_ver", ""),
        "repair_why": ("coverage repair pass (DESIGN_v10_repair.md): the coverage gate's named "
                       "absentees fed back with their verse texts in ONE bounded repair call; "
                       "structure guard held (headlines unchanged, citations superset); every "
                       "gate re-ran fresh on the repaired card") if repair else "",
        # V11.2 QUOTE-REPAIR PASS stamps (ruling 1): same visibility contract as V10's.
        "quote_repaired":          (qrepair or {}).get("fails", []),
        "quote_repair_rounds":     (qrepair or {}).get("rounds", 0),
        "quote_repair_prompt_ver": (qrepair or {}).get("prompt_ver", ""),
        "quote_repair_why": ("quote repair pass (V11.2 ruling 1): the verbatim-quote gate's own "
                             "fail lines fed back with every card-cited verse's stored bytes in "
                             "ONE bounded repair call (cap 1); the spans-only guard held (nothing "
                             "outside quotation marks changed); every gate re-ran fresh on the "
                             "repaired card, full hand battery owed as if new (lesson #50 b)")
                            if qrepair else "",
        # RULING 4 (2026-07-13): the quoted spans the repair CHANGED, each re-gated to the ref it
        # now matches, so the reviewer byte-confirms the introduced wording at ship (never silent).
        "quote_repair_introduced": (qrepair or {}).get("repair_introduced", []),
        "sig":       sig,           # input signature — the live-recompute guard at apply
        "prose_sha": _sha1(raw),    # prose bytes — the edited-since-review guard at apply
        "raw":       raw,
        "created":   datetime.datetime.now(datetime.timezone.utc).replace(
                         tzinfo=None).isoformat(timespec="seconds"),
    }
    archive_draw(sid, sig, rec["prose_sha"])   # V11.2 ruling 5 — history before overwrite
    tmp = draw_path(sid) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    os.replace(tmp, draw_path(sid))
    return sig


# ══════════════════════════════════════════════════════════════════════════════════════════════
# V10 COVERAGE REPAIR PASS (DESIGN_v10_repair.md, CLOSED at d04b6e6; JP-ruled wording under the
# standing delegation 2026-07-12). On a coverage-gate failure at the REVIEW pass (--dry-run
# --repair), ONE bounded repair call feeds the card its own gate refusal: the named absentees,
# each with its verse text in the SAME feed shape as the original occurrences (_occ_lines — one
# copy, never a fork). The repaired raw replaces the draw and re-runs EVERYTHING fresh — no gate
# sees it as anything but a new card. Cap: TWO rounds, then the draw is dead. The structure guard
# draws the SAME line as the prompt (the reviewer-required headline clause): sense headlines
# unchanged, no existing citation removed — a breach kills the draw, it is never re-repaired.
# This is NOT the edited-draw class: the MODEL writes, every machine gate re-runs from zero, and
# the human hand-checks run on the final card before apply (review-what-ships intact).
# The frozen V9 verse prompt is untouched; this block is versioned separately (repair_prompt_ver).
# ══════════════════════════════════════════════════════════════════════════════════════════════
REPAIR_PROMPT = """\
The definition below is complete except that these fed occurrences are not yet cited under a sense:

{occurrences}

Integrate each into the sense where its text belongs — add citations (and the minimum prose needed to house them) WITHOUT changing the sense structure or the sense headlines, removing any existing citation, or altering any existing quotation.

Output the corrected definition and nothing else — no preamble, no explanation, no list of what you changed, no "Here is the corrected definition" line. Your entire reply must be the card itself, from its first line to its last.

{card}"""


def repair_prompt_ver():
    # Identity of the repair INSTRUCTION BLOCK (the template — per-word refs excluded), same
    # scheme as synth_ver / the hint signature. Stamped on every repaired draw + entry audit.
    return "repair:" + hashlib.sha1(REPAIR_PROMPT.encode("utf-8")).hexdigest()[:12]


def repair_user_msg(absentee_ctx, raw):
    """The one repair message: the ruled wording with the absentees (verse texts, original feed
    shape) and the full card substituted in. .replace not .format — card prose may contain braces."""
    occ = "\n".join(_occ_lines(absentee_ctx))
    return REPAIR_PROMPT.replace("{occurrences}", occ).replace("{card}", (raw or "").strip())


def repair_guard(pre_raw, post_raw):
    """THE STRUCTURE GUARD — the detector that proves the repair-prompt line holds (red-first
    proven on a dropped-sense mock, tests/test_repair_pass.py). Splitter-diff, per the design:
    sense_headlines must be UNCHANGED and the pre-repair citation set preserved superset-style.
    Any finding = the draw is DEAD (adjudication rule: dead, not re-repaired).
    Returns problems ([] = the repair stayed inside its lines)."""
    pre, post = split_definition(pre_raw), split_definition(post_raw)
    if not post["sense_headlines"]:
        return ["repaired card has no parseable sense headlines — parse failure; draw dead"]
    problems = []
    if pre["sense_headlines"] != post["sense_headlines"]:
        changed = [f"'{a}' → '{b}'" for a, b in
                   zip(pre["sense_headlines"], post["sense_headlines"]) if a != b]
        problems.append(
            f"sense structure/headlines changed ({len(pre['sense_headlines'])} sense(s) → "
            f"{len(post['sense_headlines'])}"
            + (f"; reworded: {'; '.join(changed)}" if changed else "")
            + ") — the repair prompt forbids exactly this; the prompt and this guard draw "
              "the same line (reviewer-ruled headline clause)")
    lost = [k for k in cited_refs(pre["senses_block"])
            if k not in set(cited_refs(post["senses_block"]))]
    if lost:
        problems.append("existing citation(s) removed: "
                        + ", ".join(f"{b} {c}:{v}" for b, c, v in lost))
    return problems


def coverage_repair(raw, fed_keys, ctx, call_model, max_rounds=2):
    """The bounded repair loop. Returns (final_raw, record, problems):
      record   = {"refs": [...integrated...], "rounds": N, "prompt_ver": ...} — None when the
                 card was already clean (repair never fired).
      problems = [] on success; non-empty = the DRAW IS DEAD (guard breach or cap-out) and
                 final_raw is the last GOOD card (a refused raw never leaks out; the caller
                 must not save or ship on problems — the cached draw stays untouched).
    Coverage is re-checked per round by the PRODUCTION coverage_gate (never a copy); the full
    gate battery re-runs downstream on the final card exactly as for any fresh draw."""
    absent = coverage_gate(fed_keys, split_definition(raw)["senses_block"])
    if not absent:
        return raw, None, []
    cur, integrated = raw, []
    for rnd in range(1, max_rounds + 1):
        print(f"  REPAIR PASS round {rnd} — integrating: {', '.join(absent)}")
        absent_set = set(absent)
        actx = [c for c in ctx if f"{c[0]} {c[1]}:{c[2]}" in absent_set]
        new = call_model(repair_user_msg(actx, cur))
        probs = repair_guard(cur, new)
        if probs:
            return cur, {"refs": integrated + absent, "rounds": rnd,
                         "prompt_ver": repair_prompt_ver()}, \
                   ["structure guard REFUSED the repair output (draw DEAD, not re-repaired):"] + probs
        integrated += [a for a in absent if a not in integrated]
        cur = new
        absent = coverage_gate(fed_keys, split_definition(cur)["senses_block"])
        if not absent:
            return cur, {"refs": integrated, "rounds": rnd,
                         "prompt_ver": repair_prompt_ver()}, []
    return raw, {"refs": integrated, "rounds": max_rounds,
                 "prompt_ver": repair_prompt_ver()}, \
           [f"repair cap-out: still uncited after {max_rounds} round(s): {', '.join(absent)} — "
            f"a card that can't integrate its absentees in two tries has a real problem; "
            f"the draw is dead (design rule)"]


# ══════════════════════════════════════════════════════════════════════════════════════════════
# V11.2 QUOTE-REPAIR PASS (DESIGN_v11_acceptance.md V11.2 ruling 1, RULED 2026-07-12; prompt +
# choices reviewer-receipted at the quote-repair build session). On a verbatim-quote-gate REFUSE
# at the review pass, ONE bounded model repair call — never a hand edit (the edited-draw refusal
# is untouched), never a deterministic byte-splice (rejected: surrounding prose can claim things
# about the quote's wording; a splice can't see that). Fed: the raw + the gate's own fail lines +
# the stored verse bytes of EVERY card-cited ref (ruled: all-cited feed — deterministic, zero new
# ref-parsing surface). Guard rule = fix the quoted spans ONLY, change nothing else — enforced
# byte-strict by skeleton equality. Cap: ONE round (ruling 1; no rounds knob on purpose — the cap
# lives in the ruling and the body). After a repair the FULL battery re-runs as if the card were
# new (lesson #50 rule b) — machine gates this pass, hand-check battery at the run session.
# OUTPUT CONTRACT (F1/F2, 2026-07-13, ENGINE_LESSONS #57): the prompt now demands the CARD
# ONLY — no preamble, no reasoning — and gives an explicit no-op channel (return the card
# unchanged when nothing is fixable). This closes the 0-for-3 failure where the model's
# narration, not its fix, tripped the spans-only guard. The guard itself is UNCHANGED (it
# was vindicated 3-for-3); the fix lives in the prompt, never the guard.
# The frozen V9 verse prompt is untouched; this block is versioned separately (qrepair stamp).
# ══════════════════════════════════════════════════════════════════════════════════════════════
QUOTE_REPAIR_PROMPT = """\
The definition below fails a verbatim-quote check. Every span inside quotation marks must match the stored text of the verse it is attributed to, word for word (an ellipsis … may mark an omitted stretch; the quoted segments must stay in the verse's own order). The failed findings:

{findings}

The stored verse texts:

{verses}

Correct ONLY the wording inside quotation marks so each failed quoted span matches its verse's stored text. Change NOTHING outside the quotation marks: every word of prose, every sense headline, every citation, and the number and position of the quotations must stay exactly as they are. Do NOT remove the quotation marks from a span: if a quoted phrase is the card's own wording rather than a scripture quotation, leave it and its quotation marks exactly as they are. If a quotation cannot be made to match its verse without also changing the surrounding prose, leave that quotation exactly as it is.

Three moves are forbidden even when one of them looks like the fix:
- Do not change any word of prose outside the quotation marks, even to match a look-alike word inside a nearby quote.
- Do not add, remove, move, or split any citation; a quoted span whose only possible correction is to change which verse it is attributed to must be left exactly as it is.
- If the only way to make a quoted span match its verse is to change something outside its own quotation marks, leave that span unchanged.

If, after checking, nothing can be corrected inside the quotation marks this way, return the card exactly as given, unchanged.

Output the corrected definition and nothing else — no preamble, no explanation, no list of what you changed, no "Here is the corrected definition" line. Your entire reply must be the card itself, from its first line to its last.

{card}"""


def quote_repair_prompt_ver():
    # Identity of the quote-repair INSTRUCTION BLOCK (the template — per-card content excluded),
    # same scheme as repair_prompt_ver / synth_ver. Stamped on every quote-repaired draw + audit.
    return "qrepair:" + hashlib.sha1(QUOTE_REPAIR_PROMPT.encode("utf-8")).hexdigest()[:12]


def quote_repair_user_msg(fails, vt, raw):
    """The one repair message: the gate's fail lines verbatim, every available cited verse's
    stored bytes, the full card. .replace not .format — card prose may contain braces."""
    findings = "\n".join("- " + f for f in fails)
    verses = "\n".join(f"{b} {c}:{v} — {t}" for (b, c, v), t in sorted(vt.items()) if t)
    return (QUOTE_REPAIR_PROMPT.replace("{findings}", findings)
            .replace("{verses}", verses).replace("{card}", (raw or "").strip()))


def quote_skeleton(raw):
    """The card with every quoted span's CONTENT collapsed to a placeholder. Two cards with
    equal skeletons differ only inside quotation marks."""
    return _QUOTE_SPAN_RE.sub('"§"', raw or "")


def quote_repair_guard(pre_raw, post_raw):
    """THE SPANS-ONLY GUARD — byte-strict (red-first proven, tests/test_quote_repair.py):
    everything outside the quotation marks, and the number/position of the quotations
    themselves, must be IDENTICAL pre vs post. Any drift (a word of prose, a headline, a
    citation, an added/removed/moved quotation) = the draw is DEAD (cap 1, never re-repaired).
    Returns problems ([] = the repair stayed inside its lines)."""
    if quote_skeleton(pre_raw) != quote_skeleton(post_raw):
        return ["text outside the quotation marks changed, or a quotation was added/removed/"
                "moved — the quote-repair prompt forbids exactly this; the prompt and this "
                "guard draw the same line (spans-only rule, V11.2 ruling 1)"]
    return []


def quote_repair(raw, vt, call_model):
    """The bounded quote-repair call — cap ONE round (V11.2 ruling 1; deliberately no rounds
    parameter). vt = {(book,ch,vs): text-or-None} for EVERY card-cited ref, built by the caller
    with its own live lookups (the probe-1 convention). Returns (final_raw, record, problems):
      record   = {"fails": [...gate lines...], "rounds": 1, "prompt_ver": ...} — None when the
                 gate was clean (repair never fired).
      problems = [] on success; non-empty = the DRAW IS DEAD (guard breach or cap-out) and
                 final_raw is the last GOOD card (a refused raw never leaks out; the caller
                 must not save or ship on problems — the cached draw stays untouched).
    NOTE: gate fails and NOT-RUNs are mutually exclusive in probe1_verbatim (any missing text
    turns every unmatched span into a NOT-RUN, and NOT-RUN must never become a repair path) —
    so a fire here always has the full texts in hand. The gate re-check runs the PRODUCTION
    probe1_verbatim, never a copy.
    DETERMINISTIC PRE-ROUTING (#61 + meta:v4/#63): the gate emits three fail kinds; only the
    fixable WORDING kind (no verbatim match but a near-match target exists) ever reaches the
    model. An ANCHORING-rule fail (right words, wrong ref) and an UNSOURCED fail (own paraphrase
    with no near-match target, attribution-anchored) are both unfixable inside the quotes by
    construction (the only fix moves a ref or invents wording, which the spans-only guard forbids),
    so neither is ever fed. A card whose ONLY fails are anchoring and/or unsourced = deterministic
    no-op (the model is not called at all, zero breach surface) and parks. A mixed card feeds its
    wording fails, and the held-back anchoring/unsourced fails resurface on the re-run as a clean
    cap-out park — same ship outcome as before, breach surface removed."""
    kinds = []
    fails, _ = probe1_verbatim(raw, vt, notes=[], fail_kinds=kinds)
    if not fails:
        return raw, None, []
    wording   = [f for f, k in zip(fails, kinds) if k == "wording"]
    anchoring = [f for f, k in zip(fails, kinds) if k == "anchoring"]
    unsourced = [f for f, k in zip(fails, kinds) if k == "unsourced"]   # meta:v4, held like anchoring
    held = anchoring + unsourced
    rec = {"fails": fails, "rounds": 1, "prompt_ver": quote_repair_prompt_ver()}
    if not wording:
        # Deterministic no-op: nothing the model can safely fix (anchoring = right words/wrong ref;
        # unsourced = own paraphrase with no near-match target). No model call, no refused_post
        # (nothing existed to bank — bank_refused_repair no-ops on rec). anchoring_only kept for
        # back-compat; unsourced_held is additive.
        if anchoring:
            rec["anchoring_only"] = anchoring
        if unsourced:
            rec["unsourced_held"] = unsourced
        reasons = ((["anchoring-rule (right words, wrong ref)"] if anchoring else [])
                   + (["unsourced (own paraphrase, no near-match target)"] if unsourced else []))
        return raw, rec, ["quote-repair declined deterministically: the only fail(s) are "
                          + " and ".join(reasons) + ", unfixable inside the quotes — the card "
                          "parks and the model was not called: " + " | ".join(held)]
    print(f"  QUOTE-REPAIR PASS round 1 — {len(wording)} fixable wording span(s)"
          + (f"; {len(anchoring)} anchoring-rule fail(s) held back" if anchoring else "")
          + (f"; {len(unsourced)} unsourced fail(s) held back" if unsourced else "")
          + (" (never fed)" if held else ""))
    new = call_model(quote_repair_user_msg(wording, vt, raw))   # ONLY wording fails fed
    probs = quote_repair_guard(raw, new)
    if probs:
        rec["pre"] = raw            # ticket 1: pre-repair card (the gate's input)
        rec["refused_post"] = new   # ticket 1: the discarded output, banked as review evidence
        return raw, rec, ["spans-only guard REFUSED the repair output (draw DEAD, not "
                          "re-repaired):"] + probs
    still, _ = probe1_verbatim(new, vt, notes=[])
    if still:
        rec["pre"] = raw            # ticket 1: cap-out output preserved too
        rec["refused_post"] = new
        return raw, rec, [f"quote-repair cap-out: {len(still)} span(s) still fail after the "
                          f"single ruled round — the draw is dead (V11.2 cap 1): "
                          + " | ".join(still)]
    # RULING 4 (rides Ruling 1, success path only, no gate logic): record every quoted span
    # the repair CHANGED, tagged with the ref it now matches, so a human byte-confirms the
    # introduced wording against the live verse at ship (never a silent substitution).
    rec["repair_introduced"] = _repair_introduced_spans(raw, new, vt)
    return new, rec, []


def _repair_introduced_spans(pre_raw, post_raw, vt):
    """RULING 4 (2026-07-13, ENGINE_LESSONS #21 + silent-fallback rule): the quoted spans the
    repair CHANGED (content differs pre vs post), each tagged with the ref it now MATCHES under
    the ruled allowances. The spans-only guard has already proven the skeletons identical, so
    pre/post quoted spans align 1:1 in order. Read-only report — surfaced at apply so the human
    reads the live verse before shipping; changes no gate logic. vt = the same live-lookup dict
    the gate used, so the MATCH is re-gated against the exact texts, not re-parsed refs."""
    pre = [s for s, _, _ in _quote_spans(pre_raw)]
    post = [s for s, _, _ in _quote_spans(post_raw)]
    normed = {k: probe_norm(v) for k, v in vt.items() if v}
    out = []
    for before, after in zip(pre, post):
        if before == after:
            continue
        qn = probe_norm(_EMPH_MARK_RE.sub("", after))
        ref = next((f"{k[0]} {k[1]}:{k[2]}" for k, vn in normed.items()
                    if _match_quote(qn, vn)), "no cited verse")
        out.append({"before": before, "after": after, "matched": ref})
    return out


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
                       "double_shelved": double_shelved(fields["senses_block"]),
                       # V7 flag-only suite (window walk 2026-07-08) — fires adjudicated per word.
                       "gloss_claims": gloss_note_claims(conn, sid, fields.get("gloss_notes", "")),
                       "hedged": hedged_citations(fields["senses_block"]),
                       "subuse_overload": subuse_overload(fields["senses_block"]),
                       # ROUTING (not adjudicable): registered contested verses cited by this card.
                       "registry_verses": registry_verse_hits(refs)},
        "raw":        raw,                # kept so an improved splitter can re-split, no model call
    }
    return entry


# ══════════════════════════════════════════════════════════════════════════════════════════════
# V11 PROSE-DEFECT DETECTORS (DESIGN_v11_acceptance.md, ruled 2026-07-12).
# Probe 1 = verbatim-quote GATE (blocks; --force-gate-bypass = the adjudicated bypass).
# Probe 2 = named-subject WARN (adjudication; an open warn blocks apply).
# Scanner 3 = identity-claim WARN (same open-warn rule).
# All three read the CARD; they never shape a draw. Versioned surfaces stamped on the record.
# ══════════════════════════════════════════════════════════════════════════════════════════════

NORM_VER = "norm:v2"            # ruled normalization table rows 1-4 + 7 (edge punct) + row 8
                                # (V11.1 ticket 3, ruled 2026-07-12): markdown emphasis marks
                                # stripped from the CARD side of quote comparison only —
                                # verses.text carries zero '*' (live count, session record).
P2_WHITELIST_VER = "p2wl:v2"    # probe-2 whitelist + common-word filter + sentence-starter
                                # demotion, one versioned surface. v2 (V11.1 ticket 1, ruled
                                # 2026-07-12): label/sentence-start demotion behind the
                                # corpus-name guard; list adds english/greek/peoples.
SCAN3_PATTERNS_VER = "scan3:v2" # scanner-3 pattern list; grows by exhibit, changes ruled
META_VER = "meta:v6"            # metalinguistic-mention exemption. v2 (F3, ruled 2026-07-13):
                                # the ≤2-word cap is RETIRED, replaced by the ANCHOR WALL.
                                # v3 (Ruling 2, 2026-07-13): ADDITIVE own-word class on top of
                                # v2's cue path (untouched) — a single-word own-vocabulary
                                # scare-quote, NOT attribution-anchored, is exempt (the cue-less
                                # emphasis-quote gap #59). cue list grows by exhibit.
                                # v4 (own-paraphrase, 2026-07-14, ENGINE_LESSONS #63/#64): ADDITIVE
                                # target-exists split in the no-match branch (below the v2/v3
                                # paths, which are UNTOUCHED). A span with no verbatim match AND no
                                # target — COMBINED max(char-window, token-set) < NEARMATCH_THRESHOLD
                                # — that is NOT attribution-anchored and HAS a cited set to compare
                                # against is the writer's own paraphrase -> EXEMPT (LOUD note).
                                # Attribution-anchored, OR an empty cited set -> FAIL kind
                                # `unsourced` (held from the model like anchoring, parks).
# A quoted span is a METALINGUISTIC MENTION (exempt from the quote gate, LOUD note, never
# silent — lesson #47) only when ALL THREE hold: matches no cited verse · it carries NO local
# ref anchor (_local_refs returns []) · a rendering-talk cue sits within the context window.
# The NO-ANCHOR test is the non-word-count discriminator (ENGINE_LESSONS #56/#57): a smuggled
# misquote always attaches a ref, so an unanchored span makes no scripture claim to be
# unfaithful to, while a real misquote-with-a-ref (the "riding sense-of" laundering channel)
# stays anchored and FAILS regardless of length or cue. This is what lets the ≤2-word cap go
# and reaches the multi-word labels it never could ("matches the facts", "counts as adequate
# under the applicable rule.", "speak what is true" — G227 d3 real bytes). Real-byte exhibits:
# "reliable" (G227 d2), "captivating" (G162 d2). "other item" stays UNEXEMPTED here (no cue
# reaches scare-quotes-around-a-concept); under meta:v4 it is handled by the target-exists layer
# below (combined 0.706 >= threshold -> fed -> cap-out -> parks; never exempted — ruled must-refuse).
# LEDGERED RISK (raised 2026-07-13) — CLOSED by the FOURTH WALL (v5 built it, v6 sharpened it):
# a genuine misquote sitting unanchored in gloss-notes territory with a cue in its window used to
# launder through as an exemption (the anchor wall only catches spans that ATTACH a ref).
# v5 (scope-b): after the three walls exempt, an IN-BAND combined near-match score (0.62–0.75)
#   DEMOTES the exemption to an adjudicate-required WARN that blocks apply. But an in-band score
#   fires on the benign gloss<->own-inflection overlap too (a lemma's gloss resembles its own
#   inflected forms in its own verses) — the live sweep flagged 12/79 cards, all benign.
# v6 (scope-b (b), ENGINE_LESSONS #67): the CONTENT-TOKEN DISCRIMINATOR. In-band cue exemption
#   WARNS only when the span reproduces a verse-word RUN (>= 2 distinct content tokens present in
#   a cited verse — see _verse_run_content); a single lemma-gloss inflection (run <= 1) stays a
#   NOTE. DOCUMENTED BOUNDARY (Option A, ruled): a FULL-token reorder scores ~1.0 -> out of band
#   -> stays a note; defended by the own-paraphrase branch (non-cue reorders) + the anchor wall
#   (ref-carrying reorders). Out-of-band exemptions untouched; exemptions and warns both LOUD.
META_PATTERNS = ("render", "gloss", "the word", "the lemma", "reads as", "sense of", "so-called")

# TARGET-EXISTS test (meta:v4 / ENGINE_LESSONS #63) — the direct "is there a snap-to target
# anywhere?" check that decides unfixable-in-quote directly instead of taxonomizing what unfixable
# spans look like. The score is the COMBINED signal (ruled 2026-07-14, re-open after the char-only
# rule waved a real reorder defect through): max of two legs, because neither subsumes the other —
#   • char-ratio best sliding window (order-SENSITIVE) — catches near-verbatim edits + inflection
#     (e.g. "changing over" 0.833, where token-set alone would flip a ruled fed-case to no-target);
#   • token-SET containment best cited verse (order-INSENSITIVE) — catches reorders/swaps (e.g. the
#     real G227 defect-6 reorder "bring forth judgment to validity" 0.690 char but 1.000 token-set).
# NEARMATCH_THRESHOLD is a pinned BYTE, not a run-time tunable: 0.664 = midpoint of the fully-
# enumerated near-match no-target RESIDUAL pair on PA (G227 "quenched/crushed" 0.621 EXEMPT; G236
# "other item" 0.706 must-refuse). Two must-refuse mechanisms ride this pin and MUST NOT be
# silently overturned (reviewer written rulings, 2026-07-14):
#   (1) an EMPTY cited-verse set never exempts as own-paraphrase (exemption requires a comparison
#       to have occurred) — covers the degenerate empty-set case (probe test 1v);
#   (2) 0.664 <= 0.706: "other item" stays >= threshold so it is FED -> cap-out -> parks (never
#       shipped); raising the threshold above 0.706 overturns a standing must-refuse verdict.
# FRAGILITY (binding): any future span scoring in the 0.62–0.75 band (anchored to the residual
# squeeze 0.621 / 0.706 / 0.750) is a MANDATORY re-open byte — re-rule on the enlarged set, never a
# run-time call. Changes to this surface are ruled + red-first (stamped NEARMATCH_VER).
NEARMATCH_VER = "nearmatch:v2"           # v2 = combined char+token-set signal; threshold 0.664
NEARMATCH_THRESHOLD = 0.664
_TOKENSET_PUNC = ".,;:!?'\"()"           # per-token trim for token-set containment (internal / kept)

# meta:v5 FRAGILITY BAND (scope-b ruling, 2026-07-14): a metalinguistic-cue exemption whose
# COMBINED near-match score lands IN this band is DEMOTED from a non-blocking note to an
# adjudicate-required WARN (blocks apply, same class as the named-subject warns). This is the
# fourth wall on the cue exemption — the laundering vector the anchor wall misses (an unanchored
# span textually near a cited verse). The three walls still decide EXEMPT-vs-not; the score
# decides only whether that exemption needs human sign-off. Band edges are the ruled residual
# squeeze (0.621/0.706/0.750) — NOT threshold math; t stays NEARMATCH_THRESHOLD.
NEARMATCH_BAND_LO, NEARMATCH_BAND_HI = 0.62, 0.75
# Enumerated ADJUDICATED in-band residuals: a cue exemption already human-adjudicated + UPHELD
# does NOT re-warn at its RULED score. Keyed by the probe_norm'd span; the value is the ruled
# score(s) to 3 dp. Match is on round(score, 3), so float noise < 0.0005 still suppresses while
# any real drift re-warns (ruling: "score drift re-warns"). Grows one entry per adjudication.
_META_ADJUDICATED = {
    "this [is] true [that] you have said": (0.638,),   # G227, upheld 2026-07-14 (Joh 4:18 display)
    "Heaven/heavens": (0.720,),                        # G3772, upheld 2026-07-14 (gloss-notes label;
                                                       # slash-split of ONE gloss's two number-forms,
                                                       # both in a "heaven of heavens" verse — the run
                                                       # is an artifact, not verse-wording reproduction)
}

# meta:v6 DISCRIMINATOR (scope-b (b) ruling, 2026-07-14): an in-band cue exemption WARNS only
# when the span reproduces a RUN of the verse's own words (the laundering shape), NOT when the
# in-band score is a single lemma-gloss inflection (the benign gloss<->own-inflection signature
# that fired on 12/79 live cards under v5). The FROZEN closed English function-word set below is a
# DESIGN ELEMENT, not a maintenance list — changing it is a design re-open, never an "as-
# encountered" edit. Its only job: strip words that carry no run signal so the ">= 2 distinct
# content tokens present = a verse-word RUN" bar is meaningful.
_ENGLISH_FUNCTION = frozenset("""
a an the this that these those
and or but nor so yet for
of to in on at by with from into unto up out over under as than
he she it they we you i him her them us me his hers its their our your my mine
who whom whose which what
is are was were be been being am do does did have has had
shall will would should may might can could must
not no if then when where while because though although
before after upon about against among amongst between betwixt through throughout during without within
""".split())


def _content_tokens(span):
    """meta:v6: the span's DISTINCT content tokens — lowercased, punctuation-trimmed
    (_TOKENSET_PUNC), slash-compound split ('assign/give' -> assign, give), minus the FROZEN
    English function set. These are the words that carry a verse-word-RUN signal."""
    out = set()
    for w in span.lower().replace("/", " ").split():
        t = w.strip(_TOKENSET_PUNC)
        if t and t not in _ENGLISH_FUNCTION:
            out.add(t)
    return out


def _verse_run_content(qn, normed):
    """meta:v6 DISCRIMINATOR: the MAX over cited verses of how many of the span's DISTINCT content
    tokens appear verbatim in that verse. >= 2 => the span reproduces a RUN of verse words (the
    laundering shape) -> WARN; <= 1 => the in-band score is a single lemma-gloss inflection
    (char-similar, not a run) -> stays a NOTE. PRESENCE, NOT ADJACENCY, on purpose: a REORDERED
    laundered quote still counts (reorder killed G227 once) — do NOT 'fix' this into an adjacency
    test, it would silently bless reorders. Max over ALL cited verses, not only the char-best-match
    verse (strictly safer). A span with < 2 content tokens can never reach the bar (short-circuit).
    DOCUMENTED BOUNDARY (Option A, ruled): a FULL-token reorder scores ~1.0 on the token leg -> OUT
    of band -> never reaches this check -> stays a note. Named risk, see ENGINE_LESSONS."""
    ct = _content_tokens(qn)
    if len(ct) < 2:
        return len(ct)                       # single content token can't be a run — short-circuit
    best = 0
    for vn in normed.values():
        vt = {t for t in (w.strip(_TOKENSET_PUNC) for w in vn.lower().split()) if t}
        best = max(best, len(ct & vt))
    return best

# Row 1 (curly=straight quotes/apostrophes) + row 4 (en dash -> em dash; "--" in probe_norm).
_NORM_CHARS = {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "—"}


def probe_norm(s):
    """The RULED normalization (DESIGN_v11_acceptance.md table): quotes/apostrophes (row 1),
    whitespace collapse (row 2), '...' == '…' (row 3), en/em/double-hyphen dashes equal (row 4).
    Anything not listed = strict byte match. Applied to BOTH sides of every comparison."""
    for _a, _b in _NORM_CHARS.items():
        s = s.replace(_a, _b)
    s = s.replace("--", "—")
    s = s.replace("...", "…")
    return re.sub(r"\s+", " ", s).strip()


_QUOTE_SPAN_RE = re.compile(r'[“"]([^“”"]+)[”"]')

# norm:v2 row 8 — markdown emphasis marks are formatting, not wording; stripped from the
# CARD side only (the Gen 35:2 bold-inside-quote artifact class). Marks only: a changed
# WORD under bold still fails (teeth pinned by fixture).
_EMPH_MARK_RE = re.compile(r"\*{1,3}")


def _quote_spans(raw):
    """Every quotation-marked span in the card (senses, Range, gloss notes — no exemptions,
    per the gloss-notes-inside standing sub-rule). Yields (text, start, end) in card order."""
    for m in _QUOTE_SPAN_RE.finditer(raw):
        yield m.group(1), m.start(), m.end()


def _match_quote(qnorm, vnorm):
    """Ruled allowances ONLY: leading ellipsis; interior ellipsis marked … (segments must appear
    in order); the quote's INITIAL letter case-exempt (interior alteration never); one trailing
    punctuation mark at the span's very end (row 7 — edge only). Everything else strict."""
    segs = [s.strip() for s in qnorm.split("…") if s.strip()]
    if not segs:
        return True
    if segs[-1][-1] in ",.;:!?":                        # row 7 — edge only, never interior
        segs[-1] = segs[-1][:-1].rstrip()
        if not segs[-1]:
            segs.pop()
    if not segs:
        return True
    variants = [segs]
    s0 = segs[0]
    if s0[0].isalpha():                                 # initial-letter case exemption
        variants.append([s0[0].swapcase() + s0[1:]] + segs[1:])
    for var in variants:
        pos, ok = 0, True
        for seg in var:
            i = vnorm.find(seg, pos)
            if i < 0:
                ok = False
                break
            pos = i + len(seg)
        if ok:
            return True
    return False


# Window size for the _local_refs lead-in fallback scan, NAMED so a drift trips the #68 window
# pin (test_quote_repair). _coordinate_leadin deliberately uses NO fixed window — it walks the
# adjacent coordinate run and cannot see fewer refs than this bound.
_LOCAL_REF_WINDOW = 48


def _local_refs(raw, qs, qe):
    """The quote's own local ref list (anchoring rule): a trailing parenthetical within a few
    chars of the closing quote; else refs already named inside the enclosing parenthetical
    before the quote; else an inline 'Psa 68:18 reads'-style lead-in just before it.
    Ordered — first ref = the primary anchor. Returns (refs, trailing) so the caller can
    apply the paired-quote rule to the trailing-bracket branch only.
    V11.1 ticket 2 (ruled): the two LEAD-IN branches return refs NEAREST-FIRST — in prose
    written before the quote ('2Sa 19:42 asks whether "…"', '… while Mat 7:11 says "…"')
    the nearest ref is the attributed one. The trailing-bracket branch keeps document
    order (first listed = primary; defect 5's teeth, fixture-pinned)."""
    tail = raw[qe:qe + 100]
    m = re.match(r"[^()\n]{0,12}\(", tail)
    if m:
        close = tail.find(")", m.end())
        if close > 0:
            refs = ref_spans(tail[m.end():close])
            if refs:
                return refs, True
    head = raw[:qs]
    oi, ci = head.rfind("("), head.rfind(")")
    if oi > ci:                                         # quote sits inside a parenthetical
        seg = head[oi + 1:]
        # List-paren convention (Ref1: "q1"; Ref2: "q2"; …): the quote's own refs are the
        # CURRENT list item's — after the last semicolon — never the whole list (the G2168
        # control caught the whole-list reading as 20 false anchoring fails).
        si = seg.rfind(";")
        item_refs = ref_spans(seg[si + 1:]) if si >= 0 else []
        if item_refs:
            return list(reversed(item_refs)), False    # nearest-first (lead-in prose)
        refs = ref_spans(seg)
        if refs:
            return list(reversed(refs)), False         # nearest-first (lead-in prose)
    return list(reversed(ref_spans(head[-_LOCAL_REF_WINDOW:]))), False  # nearest-first (lead-in prose)


# V11.1 ticket 2: the connector gap between paired quotes sharing one trailing bracket —
# '"q1" and "q2" (Ref1, Ref2)'. Deliberately tight: bare and/or (optional comma), nothing
# else, so ordinary prose between quotes never triggers pairing.
_PAIR_GAP_RE = re.compile(r"\s*(?:,\s*)?(?:and|or)\s+$|\s*,\s*$")

# Coordinate ref-list / range lead-in (anchoring calibration, ENGINE_LESSONS #68, ruled
# 2026-07-14): a lead-in that names its refs as a bare list or range — "Job 42:7 and Job 42:8:",
# "Ezra 6:11-12" — assigns NO primary; the quote is correctly anchored to whichever listed ref
# its wording matches. The tell is COORDINATE GLUE between the ref matches: whitespace/comma + an
# optional and/or, nothing else. We WALK OUT from the ref nearest the quote and STOP at the first
# clause gap, so the run is exactly the adjacent citation — a fixed char window over-reaches into
# a prior sentence's trailing-bracket ref (caught red-first on the grafted mixed card). The run's
# text is expanded by ref_spans, so a range ("6:11-12", one _REF_RE match) still counts its two
# verses; a lone ref expands to one -> not a list -> nearest-first still governs. A sequential
# lead-in ("Mat 7:11 says '..' while Luk 11:13 says '..'") has clause words between the matches,
# so the walk stops immediately and the run is a single ref -> fires. Lead-ins ONLY; the
# trailing-bracket paired-swap rule (defect-5 teeth) is a separate branch and is untouched.
_COORD_GLUE_RE = re.compile(r"\s*(?:,\s*)?(?:and|or)?\s*")
def _coordinate_leadin(raw, qs):
    head = raw[:qs]
    ms = list(_REF_RE.finditer(head))
    if not ms:
        return False
    lo = len(ms) - 1                                    # the ref nearest the quote
    while lo > 0 and _COORD_GLUE_RE.fullmatch(head[ms[lo - 1].end():ms[lo].start()]):
        lo -= 1                                         # extend left while gaps stay coordinate glue
    return len(ref_spans(head[ms[lo].start():])) >= 2   # the adjacent run names >= 2 verses

# meta:v3 (Ruling 2) — the ATTRIBUTION lead-in posture: a ref immediately followed by an
# attribution verb, right before the open quote ("Psa 68:18 reads", "Num 3:9 says:").
_ATTR_LEADIN_RE = re.compile(r"\d+:\d+\s+(?:reads?|says?|states?|writes?)\s*[:,]?$")


def _attribution_anchored(raw, qs, qe):
    """meta:v3 (Ruling 2) — is the quote in an ATTRIBUTION position (a claimed source)?
    True when a ref sits in a trailing parenthetical right at the close (reuses
    _local_refs' OWN trailing-bracket branch via its `trailing` flag — not a re-derived
    copy), or an immediate 'Book C:V reads/says[:]' lead-in precedes the open quote. A
    clause ref elsewhere in the sentence is NOT an attribution and does NOT count — that
    discriminator is what lets an own-word emphasis quote through while a smuggled
    single-word misquote (which the card would attribute) stays failing. Used ONLY by the
    own-word exemption; the gate's anchoring rule keeps using _local_refs unchanged."""
    refs, trailing = _local_refs(raw, qs, qe)
    if refs and trailing:
        return True
    return bool(_ATTR_LEADIN_RE.search(raw[:qs].rstrip()))


def _own_word_exempt(raw, qn, qs, qe):
    """meta:v3 (Ruling 2): a SINGLE-word scare-quote that is the card's OWN vocabulary
    (the same word appears UNQUOTED elsewhere in the card — the tell it is the writer's
    emphasis, not a scripture claim) and is NOT attribution-anchored. Disjoint from the
    cue path (single-word only), so the multi-word must-fails (they changed their gods,
    other item) never reach it. Returns the word when exempt, else None. Base variant
    (own-prose recurrence); a gloss-match tightening is HELD for a future exhibit."""
    w = qn.strip()
    if not w or " " in w:                               # single token only
        return None
    w = w.strip(".,;:!?'\"").lower()
    if not w.isalpha() or _attribution_anchored(raw, qs, qe):
        return None                                     # a claimed source -> keep failing
    if re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", _strip_quoted(raw).lower()):
        return w                                        # appears unquoted in the card's own prose
    return None


def _nearmatch_best(qn, normed):
    """TARGET-EXISTS score (meta:v4 / ENGINE_LESSONS #63): the best sliding-window character
    similarity of a no-match span against every cited verse's stored text — the direct test for
    "is there a snap-to target anywhere?" that replaces taxonomizing what unfixable spans look
    like (a shape list invites a fourth shape). qn = the span already through probe_norm (the
    gate's own emphasis-stripped card-side value); normed = {ref: probe_norm(verse)} the gate
    already built (the PRODUCTION normalizer, never a copy — so measurement and enforcement can't
    drift). Both sides lowercased; window = the span's word count ±1 (clamped ≥1); difflib ratio,
    fully deterministic, no run-time tunable. Returns the best ratio in [0.0, 1.0] (0.0 when no
    cited text is available). Called ONLY from probe1_verbatim's no-match branch — a span that
    matches a cited verse verbatim never reaches it."""
    span = qn.lower()
    n = len(span.split())
    if n == 0:
        return 0.0
    sizes = sorted({w for w in (n - 1, n, n + 1) if w >= 1})
    sm = difflib.SequenceMatcher(a=span)
    best = 0.0
    for vn in normed.values():
        words = vn.lower().split()
        for w in sizes:
            for i in range(len(words) - w + 1):
                sm.set_seq2(" ".join(words[i:i + w]))
                r = sm.ratio()
                if r > best:
                    best = r
    return best


def _tokenset_containment(qn, normed):
    """meta:v4 ORDER-INSENSITIVE leg (ruled SET semantics, 2026-07-14): the largest fraction of
    the span's DISTINCT tokens that appear in a single cited verse's token set. SET (not multiset)
    — word multiplicity is not a defect signal in the corpus, and set is the simpler claim ("does
    every distinct word in the span exist in a cited verse"). Per-token punctuation trimmed
    (_TOKENSET_PUNC); an internal '/' is kept, so "quenched/crushed" stays one token and scores 0
    against a verse that only holds "crushed" separately. Reuses the gate's probe_norm'd values —
    qn is already normed; normed = {ref: probe_norm(verse)}. Catches the reorder/swap class that
    char-ratio is blind to (all right words, wrong order → containment ~1.0)."""
    st = {t for t in (w.strip(_TOKENSET_PUNC) for w in qn.lower().split()) if t}
    if not st:
        return 0.0
    best = 0.0
    for vn in normed.values():
        vt = {t for t in (w.strip(_TOKENSET_PUNC) for w in vn.lower().split()) if t}
        c = len(st & vt) / len(st)
        if c > best:
            best = c
    return best


def _target_exists_score(qn, normed):
    """meta:v4 TARGET-EXISTS score (ruled 2026-07-14): max of the order-sensitive char-similarity
    window and the order-insensitive token-set containment. Neither leg subsumes the other — the
    OR is load-bearing (char carries near-verbatim/inflection like "changing over" 0.833 where
    token-set is only 0.500; token-set carries reorders like the defect-6 "bring forth judgment to
    validity" 1.000 where char is only 0.690). >= NEARMATCH_THRESHOLD → a snap-to target exists
    (fixable, fed). Both legs reuse the production normalizer via the gate's normed dict, so
    measurement and enforcement cannot drift."""
    return max(_nearmatch_best(qn, normed), _tokenset_containment(qn, normed))


def probe1_verbatim(raw, verse_texts, notes=None, fail_kinds=None, warns=None):
    """PROBE 1 — verbatim-quote GATE (V11; the defect-5/6 class, G236 Dan-trio, G162 d2,
    G2805 ×3). Every quoted span must match verses.text of a verse cited on the card under
    the ruled allowances; a span matching exactly one ref of a multi-ref local list must be
    anchored on that ref FIRST. verse_texts = {(book,ch,vs): text-or-None} for EVERY
    card-cited ref (own live lookups at the call site — the fed sample can never cover
    Range/gloss/repair-integrated refs). A span matching nothing while any cited text is
    unavailable is NOT-RUN (loud, and it blocks apply) — never a pass, never a silent fail.
    Returns (fails, notruns).
    FAIL-KIND TAGGING (Ruling 1 / ENGINE_LESSONS #61 + #63): if a list is passed as fail_kinds,
    each fail is tagged AT SOURCE — index-parallel to fails — as "wording" (matches no cited
    verse but a near-match target exists, fixable in-quote), "anchoring" (right words, wrong ref,
    unfixable in-quote), or "unsourced" (meta:v4 — no verbatim match AND no near-match target,
    but attribution-anchored so it can't exempt; unfixable in-quote). The tag is emitted by the
    SAME branch that emits the fail, so the two can never drift; the quote-repair pass routes on
    it (only wording fails ever reach the model — anchoring and unsourced are held back). Same
    optional out-param shape as notes — every existing caller that omits it is unaffected."""
    fails, notruns = [], []
    missing = [k for k, v in verse_texts.items() if v is None]
    normed = {k: probe_norm(v) for k, v in verse_texts.items() if v}
    prev_qe = None                                      # previous quote span's end (pairing)
    for span, qs, qe in _quote_spans(raw):
        gap = raw[prev_qe:qs] if prev_qe is not None else None
        prev_qe = qe
        qn = probe_norm(_EMPH_MARK_RE.sub("", span))    # norm:v2 row 8, card side only
        if not re.search(r"[A-Za-z]", qn):
            continue
        label = qn if len(qn) <= 60 else qn[:57] + "..."
        matched = [k for k, vn in normed.items() if _match_quote(qn, vn)]
        if not matched:
            # meta:v2 (F3): metalinguistic-mention exemption — matches no cited verse AND
            # carries no local ref anchor AND a rendering-talk cue sits in the window. The
            # no-anchor test replaces meta:v1's ≤2-word cap as the structural laundering
            # wall (a real misquote-with-a-ref stays anchored and falls through to FAIL).
            # LOUD note, never silent.
            m_local, _ = _local_refs(raw, qs, qe)
            if not m_local:
                ctx = raw[max(0, qs - 80):qe + 40].lower()
                pat = next((p for p in META_PATTERNS if p in ctx), None)
                if pat:
                    # meta:v6 (scope-b (b) ruling, 2026-07-14): the three walls have decided
                    # EXEMPT. An IN-BAND cue exemption is DEMOTED to an adjudicate-required WARN
                    # ONLY when the span reproduces a verse-word RUN (>= 2 distinct content tokens
                    # present in a cited verse) — the laundering shape. A single lemma-gloss
                    # inflection (run <= 1) stays a NOTE (the v5 blast radius: gloss resembles its
                    # own inflected form). Out-of-band stays a note (documented full-reorder
                    # boundary). Enumerated adjudicated residuals do not re-warn at their score.
                    ms = _target_exists_score(qn, normed)
                    in_band = NEARMATCH_BAND_LO <= ms <= NEARMATCH_BAND_HI
                    run = _verse_run_content(qn, normed) if in_band else 0
                    if (in_band and run >= 2
                            and round(ms, 3) not in _META_ADJUDICATED.get(qn, ())):
                        if warns is not None:
                            warns.append(
                                f'quote "{label}" metalinguistic-mention exemption ({META_VER} '
                                f'cue "{pat}", no verse match, no ref anchor) reproduces a RUN of '
                                f'{run} verse content token(s) at near-match {ms:.3f} (in band '
                                f'[{NEARMATCH_BAND_LO}-{NEARMATCH_BAND_HI}]) — ADJUDICATE (in-band '
                                f'metalinguistic class): confirm the span DISPLAYS a rendering, '
                                f'not a laundered near-quote')
                        continue
                    if notes is not None:
                        if not in_band:
                            tag = f'near-match {ms:.3f} out of band'
                        elif run >= 2:                       # registered adjudicated-upheld residual
                            tag = f'IN band run {run}, adjudicated-upheld residual {ms:.3f}'
                        else:
                            tag = f'IN band, single lemma-gloss inflection (run {run} < 2)'
                        notes.append(
                            f'quote "{label}" EXEMPTED as metalinguistic mention ({META_VER} '
                            f'cue "{pat}", no verse match, no ref anchor, {tag}) — '
                            f'non-blocking note')
                    continue
            # meta:v3 (Ruling 2): own-word emphasis mention — a single word that is the
            # card's own out-of-quote vocabulary and is NOT attribution-anchored. Additive
            # to the cue path above; disjoint (single-word only), so a multi-word misquote
            # never reaches it. LOUD note, never silent (lesson #47).
            ow = _own_word_exempt(raw, qn, qs, qe)
            if ow:
                if notes is not None:
                    notes.append(
                        f'quote "{label}" EXEMPTED as own-word emphasis mention ({META_VER} '
                        f'single word "{ow}" in the card\'s own prose, no verse match, not '
                        f'attribution-anchored) — non-blocking note')
                continue
            if missing:
                notruns.append(
                    f'quote "{label}" — NOT RUN: no match among available texts and '
                    f'{len(missing)} cited verse text(s) unavailable')
                continue
            # meta:v4 (own-paraphrase, ENGINE_LESSONS #63): the TARGET-EXISTS test. Does a snap-to
            # target for this span sit in ANY cited verse? COMBINED score = max(char-window,
            # token-set containment) — order-sensitive OR order-insensitive, so a reordered real
            # quote is recognized as fixable, not mistaken for own notation. >= threshold -> a real
            # misquote the model can fix (wording, fed). Below -> no target: split THREE ways —
            #   • EMPTY cited set (no comparison possible) -> never exempt; FAIL (unsourced). Ruled
            #     must-refuse mechanism (1): exemption requires a comparison to have occurred.
            #   • attribution-anchored (a claimed source with no verbatim existence) -> FAIL
            #     (unsourced), held from the model, parks.
            #   • unanchored own notation -> EXEMPT with a LOUD note (lesson #47).
            # Runs ONLY here in the no-match branch; a verbatim match never reaches it.
            score = _target_exists_score(qn, normed)
            if score >= NEARMATCH_THRESHOLD:
                fails.append(
                    f'quote "{label}" matches NO cited verse under the ruled allowances '
                    f'(verbatim-quote gate)')
                if fail_kinds is not None:
                    fail_kinds.append("wording")
            elif not normed:
                fails.append(
                    f'quote "{label}" matches NO cited verse and NO cited verse text was available '
                    f'to test for a target — cannot be exempted as own-paraphrase (empty-set rule); '
                    f'unsourced')
                if fail_kinds is not None:
                    fail_kinds.append("unsourced")
            elif _attribution_anchored(raw, qs, qe):
                fails.append(
                    f'quote "{label}" matches NO cited verse and no target exists in any cited '
                    f'verse (best {score:.3f} < {NEARMATCH_THRESHOLD}); the card attributes a '
                    f'source for wording with no verbatim existence (unsourced)')
                if fail_kinds is not None:
                    fail_kinds.append("unsourced")
            elif notes is not None:
                notes.append(
                    f'quote "{label}" EXEMPTED as own-paraphrase ({META_VER} no verse match, best '
                    f'target {score:.3f} < {NEARMATCH_THRESHOLD}, not attribution-anchored — the '
                    f"writer's own notation, no scripture claim) — non-blocking note")
            continue
        local, trailing = _local_refs(raw, qs, qe)
        if len(local) >= 2:
            hit = [k for k in local if k in matched]
            # Coordinate-list / range lead-in (ENGINE_LESSONS #68, ruled 2026-07-14): a lead-in
            # naming its refs as a bare list/range assigns no primary, so a quote matching ANY
            # listed ref is correctly anchored. Lead-ins ONLY (the trailing-bracket paired-swap
            # teeth below are a separate branch, untouched). `hit` vouches the matched ref is
            # cited; every listed ref is cited by construction (cited_refs sweeps the whole card).
            coord_pass = bool(hit) and not trailing and _coordinate_leadin(raw, qs)
            if not coord_pass:
                # V11.1 ticket 2, paired-quote rule: '"q1" and "q2" (Ref1, Ref2)' — the
                # bracket-adjacent quote pairs with the LAST ref. Trailing brackets only;
                # a swapped pair still fires (teeth pinned by the swap fixture).
                expected = (local[-1] if trailing and gap is not None
                            and _PAIR_GAP_RE.fullmatch(gap) else local[0])
                if len(hit) == 1 and expected != hit[0]:
                    fails.append(
                        f'quote "{label}" carries the wording of {hit[0][0]} {hit[0][1]}:{hit[0][2]} '
                        f'but is anchored primary on {expected[0]} {expected[1]}:{expected[2]} '
                        f'(anchoring rule)')
                    if fail_kinds is not None:
                        fail_kinds.append("anchoring")
    return fails, notruns


# Probe-2 whitelist (VERSIONED — P2_WHITELIST_VER; changes ruled, stamp on the draw record):
# God/LORD per the design; the headword's lemma/translit join per-card at the call site.
_P2_WHITELIST = {"god", "lord"}
# Capitalized non-names (sentence-starts, card furniture). Same versioned surface.
_P2_COMMON = {
    "a", "an", "and", "all", "any", "are", "as", "at", "be", "been", "being", "both", "but",
    "by", "did", "do", "does", "each", "english", "even", "every", "first", "for", "from",
    "gloss", "greek", "grounding", "having", "he", "her", "his", "him", "here", "how", "i",
    "if", "in", "is", "peoples",
    "it", "its", "let", "marking", "my", "no", "nor", "not", "o", "of", "on", "one", "or",
    "our", "range", "second", "sense", "senses", "she", "so", "some", "sub", "take", "that",
    "the", "their", "then", "there", "these", "those", "third", "this", "to", "two",
    "was", "we", "were", "what", "when", "where", "who", "whom", "why", "with", "you", "your",
}


def _strip_quoted(raw):
    """Quoted spans blanked — names inside a verbatim quote are probe 1's territory."""
    return _QUOTE_SPAN_RE.sub(" ", raw)


# Book names are whitelisted by the ruled design; the closed canonical-code set is derived
# from the SAME _BOOK_ALT table the ref scanner uses (never a private copy).
_P2_BOOKS = {b.lower() for b in _BOOK_ALT.split("|")}


# p2wl:v2 sentence/label boundary (ruled 2026-07-12, byte-forced set): paragraph/chunk
# start · . ! ? · "Sub-use:" label · "- "/"* " list start · "**" label close. Semicolon and
# bare colon are EXPLICITLY not boundaries — the banked Korah (after ";") and Sabean (after
# "):") warn classes ride on that exclusion; do not widen.
_P2_BOUNDARY_RE = re.compile(r"(?:^|[.!?]|\bSub-use:|^\s*[-*]|\*\*)\s*$")


def _p2_known(low, known_names):
    """Guard membership with cheap singular/plural loosening — loosening only ADDS warns
    (toward the human), never removes one."""
    return (low in known_names or low + "s" in known_names
            or (low.endswith("s") and low[:-1] in known_names))


def _proper_names(chunk, whole_body, known_names=None):
    """Proper names = capitalized tokens (possessive stripped) that are NOT card furniture,
    NOT book codes / citation text (refs stripped first), and are consistently capitalized
    across the card (a token also appearing lowercase is ordinary prose, not a name).
    p2wl:v2 demotion: a non-possessive token sitting at a sentence/label boundary is card
    furniture, not a name — UNLESS the corpus-name guard knows it (a real name like Laban
    or Solomon at a sentence start keeps its warn). known_names=None = guard unavailable =
    NO demotion; every boundary token stays a candidate (fail toward the human)."""
    chunk = _REF_RE.sub(" ", chunk)                     # citations are not prose claims
    body_lower = set(re.findall(r"(?<![A-Za-z])([a-z]+)\b", whole_body))
    out = []
    for m in re.finditer(r"\b([A-Z][a-z]+)(['’]s)?\b", chunk):
        tok, poss = m.group(1), m.group(2)
        low = tok.lower()
        if low in _P2_COMMON or low in _P2_WHITELIST or low in _P2_BOOKS or low in body_lower:
            continue
        if (known_names is not None and not poss
                and _P2_BOUNDARY_RE.search(chunk[:m.start()])
                and not _p2_known(low, known_names)):
            continue                                    # p2wl:v2 sentence-starter demotion
        if tok not in out:
            out.append(tok)
    return out


def _cite_chunks(body):
    """Prose split into claim chunks, each ending at a parenthetical close (the list-item
    structure the cards use); a chunk's refs = every ref inside it, inline or parenthesized.
    Chunks with no refs carry no checkable claim and are skipped by the caller."""
    for para in body.split("\n"):
        last = 0
        for m in re.finditer(r"\)", para):
            chunk = para[last:m.end()]
            refs = ref_spans(chunk)
            if refs:
                yield chunk, refs
                last = m.end()
        tail = para[last:]
        refs = ref_spans(tail)
        if refs:
            yield tail, refs


def probe2_names(raw, verse_texts, extra_whitelist=(), known_names=None, context_texts=None):
    """PROBE 2 — named-subject check (V11; the Jehoiada/Eliphaz/Jer 3:21 misattribution class).
    WARN, not block — the standing kill sub-rule is a HUMAN rule; the machine's job is making
    sure the human never misses the candidate. Every proper name in a claim must appear in at
    least one of the claim's cited verse texts. A missing verse text = NOT-RUN for that name
    (loud, blocks apply) — never a pass. known_names = the p2wl:v2 corpus-name guard set
    (lowercased); None disables sentence-starter demotion entirely. Returns (warns, notruns).
    context_texts (grounded-naming, 2026-07-15) = {ref: [context verse texts]} for FED
    occurrences only — a name grounded in a cited occurrence's OWN fed context verses passes
    (the model was shown that text). Scoped per-occurrence, never pooled card-wide; None (e.g.
    a resplit pass, which has no fed sample) = strict as before, failing toward the human."""
    extra = {str(w).lower() for w in extra_whitelist if w}
    body = _strip_quoted(raw)
    warns, notruns = [], []
    for chunk, refs in _cite_chunks(body):
        texts = {k: verse_texts.get(k) for k in refs}
        avail = [probe_norm(t).lower() for t in texts.values() if t]
        if context_texts:
            avail.extend(probe_norm(t).lower()
                         for k in refs for t in context_texts.get(k, ()) if t)
        missing = [k for k, t in texts.items() if t is None]
        for name in _proper_names(chunk, body, known_names):
            if name.lower() in extra:
                continue
            if any(re.search(rf"\b{re.escape(name.lower())}\b", t) for t in avail):
                continue
            reflist = ", ".join(f"{b} {c}:{v}" for b, c, v in refs)
            if missing:
                notruns.append(f'"{name}" ({reflist}) — NOT RUN: cited verse text(s) unavailable')
            else:
                warns.append(f'named subject "{name}" absent from cited text(s) {reflist} '
                             f'— adjudicate (misattribution class)')
    return warns, notruns


# p2wl:v2 corpus-name guard source: the words table's name-marked renderings (is_pn=1
# english_head, set by import_tipnr.py — see docs/claude/data-model.md). Loaded once per
# connection. Control-tested live 2026-07-12 (session record): korah/solomon/laban/jesus/
# peter present, votive/active/applying absent. Any failure → None → NO demotion (the
# guard degrading must always fail toward the human, never silently widen demotion).
#
# LOUDNESS (DESIGN_p2_guard_loudness.md, reviewer-ruled 2026-07-14). The degrade stays — the
# FAILURE DIRECTION IS UNCHANGED and must stay unchanged — but it no longer happens in silence.
# The defect it cures: the loader's ERROR and probe2_names' LEGITIMATE `known_names=None`
# ("demotion off by choice") were the SAME BYTE, so a dead guard arrived wearing the contract's
# clothes and was handled as if someone had chosen it. A guard-load failure is a NOT-RUN — the
# demotion check did not run — so it rides the RULED probe2_notrun class (loud on stderr,
# stored on the audit, BLOCKS apply via open_probe_warns). No new tier, no new field.
# Guard-ABSENT needs nothing here: no connection is already loud one layer up in validate_entry
# and never reaches this loader, so a None from HERE can only ever mean the read FAILED.
# The reason rides in the SAME cache entry — a second dict would double the id(conn) key
# surface flagged in the design note (never-evicting; revival trigger = any long-running
# multi-connection caller).
_P2_PN_CACHE = {}          # id(conn) -> (names_or_None, error_text)


def _p2_load_guard(conn):
    key = id(conn)
    if key not in _P2_PN_CACHE:
        try:
            rows = conn.execute("SELECT DISTINCT lower(english_head) FROM words "
                                "WHERE is_pn=1 AND english_head != ''").fetchall()
            _P2_PN_CACHE[key] = ({r[0] for r in rows}, "")
        except Exception as exc:
            _P2_PN_CACHE[key] = (None, f"{type(exc).__name__}: {exc}")
    return _P2_PN_CACHE[key]


def _p2_corpus_names(conn):
    """The guard set, or None if it could not be loaded (contract UNCHANGED — None still means
    no demotion, still fails toward the human). Callers that report coverage must ALSO call
    _p2_guard_notrun, or their silence reads as covered (#69(i))."""
    return _p2_load_guard(conn)[0]


def _p2_guard_notrun(conn):
    """The NOT-RUN line when the guard failed to load against a LIVE connection, else "" (a
    healthy load says nothing — a not-run on every good run is noise that trains blindness).
    Fold into probe2_notrun at the call site: that class already blocks apply."""
    err = _p2_load_guard(conn)[1]
    if not err:
        return ""
    return (f"p2wl:v2 corpus-name guard FAILED to load — sentence-starter demotion did NOT run, "
            f"so every boundary token stayed a candidate: the probe-2 warns below are UNGUARDED "
            f"and some MAY be over-firing. They are still real candidates — adjudicate them on "
            f"their own texts, but do NOT write them off as the is_pn-incompleteness class (#72): "
            f"that explanation does not apply when the guard never loaded. Fix the guard "
            f"read first ({err})")


# Scanner-3 pattern list (VERSIONED — SCAN3_PATTERNS_VER; grows by exhibit, changes ruled).
SCAN3_PATTERNS = ("worded identically", "identical wording", "verbatim parallel",
                  "phrasing is identical")   # v2: G227 V11-run d1 exhibit, ruled 2026-07-12


def scan3_identity(raw, verse_texts):
    """SCANNER 3 — identity-claim check (V11; the false Mat 22:16↔Mar 12:14 exhibit). A prose
    claim that two refs are worded identically → string-compare the two stored texts under the
    ruled normalization; unequal = WARN. Can't resolve exactly two refs, or a text unavailable
    = WARN too (fail toward the human). Returns warns."""
    warns = []
    low = raw.lower()
    for pat in SCAN3_PATTERNS:
        for m in re.finditer(re.escape(pat), low):
            head = raw[:m.start()]
            oi, ci = head.rfind("("), head.rfind(")")
            if oi > ci:                                  # claim sits inside a parenthetical
                close = raw.find(")", m.end())
                ctx = raw[oi:close if close > 0 else m.end() + 120]
            else:                                        # else a sentence-sized window
                ctx = raw[max(0, m.start() - 150):m.end() + 150]
            refs = []
            for k in ref_spans(ctx):
                if k not in refs:
                    refs.append(k)
            if len(refs) != 2:
                warns.append(f'identity claim "{pat}" — could not resolve exactly two refs '
                             f'(found {len(refs)}) — adjudicate')
                continue
            ta, tb = verse_texts.get(refs[0]), verse_texts.get(refs[1])
            if ta is None or tb is None:
                warns.append(f'identity claim "{pat}" ({refs[0][0]} {refs[0][1]}:{refs[0][2]} vs '
                             f'{refs[1][0]} {refs[1][1]}:{refs[1][2]}) — NOT RUN: text unavailable')
            elif probe_norm(ta) != probe_norm(tb):
                warns.append(f'prose claims {refs[0][0]} {refs[0][1]}:{refs[0][2]} and '
                             f'{refs[1][0]} {refs[1][1]}:{refs[1][2]} are worded identically but '
                             f'the stored texts DIFFER — adjudicate (false-identity class)')
    return warns


def open_probe_warns(entry):
    """The open-warn-blocks-apply rule (GATE CONDITION): any probe-1 in-band cue warn (meta:v5)
    OR probe-2/scanner-3 warn OR any probe NOT-RUN item (amendment 1 — a missing verse text must
    never become a ship path) without an adjudication stamp refuses the ship. Returns the blocking
    items ([] = clear)."""
    a = entry.get("audit") or {}
    blocking = ((a.get("probe1_warns") or []) + (a.get("probe2_warns") or [])
                + (a.get("scan3_warns") or [])
                + (a.get("probe1_notrun") or []) + (a.get("probe2_notrun") or []))
    return [] if (not blocking or a.get("warns_adjudicated")) else blocking


def _warn_set(audit):
    """The EXACT five lists open_probe_warns blocks on, in a stable comparable form. Read from the
    same place the gate reads (never a second list) — if the gate ever blocks on a sixth thing,
    this must gain it or the carry below would silently ignore it."""
    a = audit or {}
    return tuple(sorted((a.get("probe1_warns") or []) + (a.get("probe2_warns") or [])
                        + (a.get("scan3_warns") or [])
                        + (a.get("probe1_notrun") or []) + (a.get("probe2_notrun") or [])))


def carry_adjudication(old_entry, new_audit, is_resplit):
    """Carry a stored adjudication across a --resplit, or return None (reviewer-ruled 2026-07-14).

    WHY IT EXISTS: --resplit rebuilds the entry from scratch, so `warns_adjudicated` vanishes and
    open_probe_warns REFUSES every card that shipped with an adjudicated warn. That made the
    zero-spend remediation of the 31 verse-short live cards partial — and partial WEARING A CLEAN
    FACE, since the other cards report success (the #69(i) shape at batch level).

    WHY CARRYING IS SAFE HERE AND NOWHERE ELSE: a resplit re-derives from the SAME STORED PROSE —
    no model call, not one word of the card changes. The claims the human ruled on are therefore
    byte-unchanged. If the WARN SET is byte-identical too, the ruling still covers exactly what it
    covered when it was made. Change either and the carry refuses.

    THE TRUST TRANSFER IS A DECISION, NOT A DEFAULT (reviewer + JP, on the record): a batch resplit
    ships carried adjudications on a byte comparison rather than a fresh human pass, because that
    comparison is strictly more reliable than a human re-reading 31 unchanged warn sets — hand
    re-adjudication at that volume IS rubber-stamping with extra steps. The carry is stamped
    VISIBLY on the row (`warns_adjudication_carried`) so the trail never reads as a fresh ruling.
    """
    if not is_resplit:
        return None                      # a fresh draw has NEW prose; no prior ruling can cover it
    new = _warn_set(new_audit)
    if not new:
        return None                      # nothing to adjudicate — never plant a stale note
    old = (old_entry or {}).get("audit") or {}
    note = old.get("warns_adjudicated")
    if not note:
        return None                      # invent nothing
    return note if _warn_set(old) == new else None


def validate_entry(entry, conn=None, fed_ctx=None):
    """Tell a LEGITIMATELY-empty field from a PARSE FAILURE wearing the same blank. The fields here
    are the ones where empty is NEVER legitimate, so an empty one means the splitter couldn't read
    the model's output — a loud error that must refuse to write the row, not a silent blank that
    reads as clean at scale (the numbered-book lesson). Range / gloss_notes / coverage are NOT here
    on purpose: empty is a fine graceful degrade for those scholar fields. Returns problems ([]=ok).
    fed_ctx (grounded-naming, 2026-07-15) = {(book,ch,vs): [context verse texts]} for the FED
    occurrences, passed on draw/apply passes only — probe-2 grounds a name against a cited
    occurrence's own fed context. None (resplit: no fed sample) = probe-2 strict as before."""
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
    # V9 COVERAGE GATE (JP-ruled 2026-07-12): fed_uncited is stamped at the call site — the
    # one place the fed sample exists. None = not checked this pass (resplit re-splits stored
    # prose with no fed sample; the call site prints that loudly, never skips silently).
    # Bypass rides the SAME --force-gate-bypass path as the citation gate — no new surface.
    uncited = a.get("fed_uncited")
    if uncited:
        if a.get("bypass_reason"):
            print(f"  ⚠ coverage gate BYPASSED for {entry['strongs']} ({len(uncited)} fed "
                  f"occurrence(s) uncited: {', '.join(uncited)}) — reason stored: "
                  f"{a['bypass_reason']}", file=sys.stderr)
        else:
            problems.append(
                f"coverage gate FAILED — {len(uncited)} fed occurrence(s) never cited under a "
                f"sense: {', '.join(uncited)}. Every fed occurrence must appear in the senses "
                f"block (trimming is a defect — V9 ruling 2026-07-12). Fix the raw, or pass "
                f"--force-gate-bypass \"reason\".")
    # V11 PROSE PROBES (DESIGN_v11_acceptance.md, ruled 2026-07-12). Own live lookups for
    # EVERY card-cited ref — never the fed sample (it cannot cover Range/gloss-note/repair-
    # integrated refs). No connection = loud NOT RUN, the coverage-gate convention.
    raw = entry.get("raw") or ""
    if conn is None:
        print(f"  ⚠ V11 prose probes NOT RUN for {entry['strongs']} — no DB connection on "
              f"this pass; verbatim-quote gate, named-subject check, identity scanner all "
              f"UNCHECKED.", file=sys.stderr)
    elif raw:
        if not a:
            a = entry["audit"] = {}                    # (amendment 2: bind writes to the entry)
        vt = {}
        for b, c, v in cited_refs(raw):
            row = conn.execute("SELECT text FROM verses WHERE book=? AND chapter=? AND verse=?",
                               (b, c, v)).fetchone()
            vt[(b, c, v)] = (row["text"] if row and row["text"] else None)
        p1_notes, p1_warns = [], []
        p1_fails, p1_nr = probe1_verbatim(raw, vt, notes=p1_notes, warns=p1_warns)
        p2_warns, p2_nr = probe2_names(raw, vt,
                                       extra_whitelist=(entry.get("lemma"), entry.get("translit")),
                                       known_names=_p2_corpus_names(conn),
                                       context_texts=fed_ctx)
        # A dead guard is a NOT-RUN, never a silent degrade (DESIGN_p2_guard_loudness.md).
        # Rides the existing class: printed below, stored, and blocks apply. "" when healthy.
        guard_nr = _p2_guard_notrun(conn)
        if guard_nr:
            p2_nr = [guard_nr] + p2_nr
        s3_warns = scan3_identity(raw, vt)
        a["probe_vers"] = {"norm": NORM_VER, "p2wl": P2_WHITELIST_VER,
                           "scan3": SCAN3_PATTERNS_VER, "meta": META_VER,
                           "nearmatch": NEARMATCH_VER}
        a["probe1_notrun"], a["probe2_warns"] = p1_nr, p2_warns
        a["probe2_notrun"], a["scan3_warns"] = p2_nr, s3_warns
        a["probe1_notes"] = p1_notes                    # metalinguistic exemptions — LOUD, on record
        a["probe1_warns"] = p1_warns                    # meta:v5 in-band cue demotions — BLOCK apply
        for line in p1_notes:
            print(f"  ℹ V11 meta-exemption ({entry['strongs']}): {line}", file=sys.stderr)
        for line in p1_nr + p2_nr:
            print(f"  ⚠ V11 probe NOT RUN item ({entry['strongs']}): {line}", file=sys.stderr)
        for line in p1_warns + p2_warns + s3_warns:
            print(f"  ⚠ V11 WARN ({entry['strongs']}): {line} — an open warn BLOCKS apply "
                  f"until adjudicated", file=sys.stderr)
        if p1_fails:
            if a.get("bypass_reason"):
                print(f"  ⚠ verbatim-quote gate BYPASSED for {entry['strongs']} "
                      f"({len(p1_fails)}) — reason stored: {a['bypass_reason']}",
                      file=sys.stderr)
            else:
                problems.append(
                    f"verbatim-quote gate FAILED — {len(p1_fails)} quoted span(s): "
                    + " | ".join(p1_fails)
                    + " Fix the raw, or pass --force-gate-bypass \"reason\".")
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


def model_prose(client, sid, translit, gset, ctx, hint=None, pmap=None, constraints=None, roster=None):
    msg = client.messages.create(
        model=MODEL_SONNET, max_tokens=MAX_TOKENS, system=VERSE_PROMPT,
        messages=[{"role": "user",
                   "content": verse_user_msg(sid, translit, gset, ctx, hint, pmap, constraints, roster)}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def show_entry(entry):
    """Print the assembled fields so a human can eyeball the split before --apply writes."""
    a = entry["audit"]
    print(f"\n  lemma: {entry['lemma']}  ({entry['translit']})   stamp {entry.get('synth_ver','')}")
    if entry.get("pinned_core"):
        print(f"  PINNED CORE (leads the card; the senses below read as attested uses):")
        print(f"     → {entry['pinned_core']}")
    if sense_split_mode(entry.get("senses_block")) == "headline":
        print(f"  [1 sense — headline fallback]  (no numbered sense in the draw; the opening bold "
              f"headline was taken as the single sense — inspect, per the banked loud-marker rule)")
    print(f"  sense_headlines ({len(entry['sense_headlines'])}) — the glance list:")
    for i, h in enumerate(entry["sense_headlines"], 1):
        print(f"     {i}. {h}")
    prov = entry.get("sense_prov") or []
    hits = [str(i + 1) for i, p in enumerate(prov) if p.get("lxx")]
    print(f"  LXX provenance note fires on sense(s): {', '.join(hits) if hits else '(none)'}")
    print(f"  senses_block ({len(entry['senses_block'])} chars) — full prose, PROOFREAD IT (gate step):")
    for _ln in (entry['senses_block'] or "(empty)").splitlines():
        print(f"    | {_ln}")
    print(f"  range:       {entry['range'] or '(empty)'}")
    print(f"  gloss_notes ({len(entry['gloss_notes'])} chars) — full, PROOFREAD IT (gate step):")
    for _ln in (entry['gloss_notes'] or "(empty)").splitlines():
        print(f"    | {_ln}")
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
    if a.get("repair"):
        r = a["repair"]
        print(f"  REPAIRED card (V10 repair pass, round(s): {r['rounds']}, {r['prompt_ver']}) — "
              f"integrated: {', '.join(r['refs'])}")
    if a.get("quote_repair"):
        r = a["quote_repair"]
        print(f"  QUOTE-REPAIRED card (V11.2 quote-repair pass, round(s): {r['rounds']}, "
              f"{r['prompt_ver']}) — {len(r['fails'])} span(s) repaired; FULL battery owed "
              f"as if new (lesson #50 b)")
    print(f"  citation gate: {a['pass']}/{a['total']} pass" +
          (f"  (misses — tagging {a['tagging']} / real {a['real']} / no-verse {a['noverse']})" if a['total']-a['pass'] else ""))
    if a.get("dangling"):
        print(f"  ⚠ dangling book refs (no ch:vs — flag only): {', '.join(a['dangling'])}")
    for rt in refused_tails(entry.get("raw", "")):
        print(f"  ⚠ REFUSED-TAIL: range '{rt}' not expanded (backwards or span > 30) — "
              f"the tail verses are NOT counted as cited; adjudicate by hand")
    # LEADING-BOILERPLATE — REPORT-ONLY (G162 preamble-leak ticket, reviewer-ruled 2026-07-14).
    # Computed from raw at print time and NOT stored, exactly like refused_tails above: no audit
    # field, no def_json shape change, and NOTHING refuses a card on it. It reports a broken output
    # CONTRACT (the draft wrote prose before its card), not a broken card — split_definition drops
    # this text and the reader never sees it. Printing it is the whole point: the discard was
    # SILENT, so a contract-breaching draw read gate-clean. Block rule is a separate reviewed step,
    # sized off a sweep — see the AUDIT entry. ZEROS FROM THIS ARE NOT YET TRUSTED: the
    # known-positive control (G162's archived draw, PA-only) has not run.
    for bp in leading_boilerplate(entry.get("raw", "")):
        print(f"  ⚠ LEADING-BOILERPLATE [{bp['kind']}] — the draft wrote this BEFORE its card, "
              f"breaching the output contract (report-only, blocks nothing; the splitter drops it "
              f"so no reader sees it): {bp['text'][:120]!r}")
    if a.get("noncanon"):
        print(f"  ✗ non-canonical book label(s) — HARD REJECT: {', '.join(a['noncanon'])}")
    for d in (a.get("double_shelved") or []):
        print(f"  ⚠ double-shelved: {d['ref']} in senses {d['senses']}")
    for g in (a.get("gloss_claims") or []):
        print(f"  ⚠ gloss-note claim [{g['kind']}] at {g['ref']}: claimed *{g['gloss']}*"
              + (f" — corpus renders \"{g['rend']}\"" if g.get("rend") else
                 " — sentence-initial capitalization; adjudicate the note's rationale"))
    for h in (a.get("hedged") or []):
        print(f"  ⚠ hedged citation (rule 7c): sense {h['sense']} prose contains \"{h['hedge']}\" — "
              f"a lint PASS is not 7c satisfied, only a fire is meaningful")
    for s in (a.get("subuse_overload") or []):
        print(f"  ⚠ sub-use overload: sense {s['sense']} carries {s['subuses']} Sub-uses — "
              f"merge-review (flag only, no ceiling; #14 forbids forced folds)")
    fd = a.get("floor_diff")
    if fd:
        head = (f"  #30 floor-diff vs {fd['file']} "
                f"(N={fd['runs']} draws, consensus = pairs together in ≥{fd['majority']})")
        if fd["fires"]:
            print(head + f" — {len(fd['fires'])} verse(s) OFF their floor consensus home:")
            for f in fd["fires"]:
                who = ", ".join(f"{b['ref']} {b['same']}/{b['n']}" for b in f["broken"][:6])
                more = f" (+{len(f['broken']) - 6} more)" if len(f["broken"]) > 6 else ""
                kept = f"; kept {', '.join(f['kept'])}" if f["kept"] else "; kept none"
                print(f"  ⚠ #30: {f['ref']} (ship sense {'/'.join(map(str, f['ship_senses']))}) "
                      f"split from {who}{more}{kept}")
            print("     flag only — adjudicate per the ruled taxonomy; fire classes are defined "
                  "at the step-5 control fire, never mid-count.")
        else:
            print(head + " — no consensus pair split (clean)")
        if fd["floor_unseen"]:
            print(f"     floor-unseen citation(s), NOT covered by this diff — table-verify them "
                  f"(σελήνη procedure): {', '.join(fd['floor_unseen'])}")
    rc = a.get("roster_count")
    if rc:
        if rc["ok"]:
            print(f"  #55 sense-count guard vs roster ({rc['floor']}): ship {rc['ship_count']} = "
                  f"roster {rc['roster_count']} — count matches (clean)")
        else:
            print(f"  ⚠ #55 sense-count guard vs roster ({rc['floor']}): ship {rc['ship_count']} ≠ "
                  f"roster {rc['roster_count']} — floor consensus COLLAPSED or SPLIT (apply refused)")
    for r in (a.get("registry_verses") or []):
        print(f"  ‼ CONTESTED-VERSE REGISTRY HIT: {r['ref']} — {r['fork']}\n"
              f"     BAR ({r['source']}): {r['bar']}\n"
              f"     Every descriptive claim touching this verse gets verse-text verification "
              f"BEFORE gate time. This is routing, not a flag to adjudicate away.")
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
    ap.add_argument("--adjudicate-warns", metavar="NOTE",
                    help="V11 (DESIGN_v11_acceptance.md): record the reviewer adjudication for "
                         "OPEN probe-2/scanner-3 warns and probe NOT-RUN items; without it an "
                         "apply with open items is REFUSED. Stamped into audit.warns_adjudicated "
                         "so a shipped row self-documents the ruling.")
    ap.add_argument("--all", action="store_true",
                    help="target EVERY built word in lexica_def (use with --resplit to roll a "
                         "derivation change — e.g. the LXX provenance note — across the whole batch, "
                         "no model call)")
    ap.add_argument("--from-draw", metavar="KEY8",
                    help="ship the reviewed draw for --word whose key (sig[:8]) == KEY8 by bypassing the "
                         "synth_ver up-to-date skip; requires a cache HIT, NEVER re-rolls. Use after a prose "
                         "fix the draw signature can't detect: find affected cards with check_draw_citations.py, "
                         "regenerate with --dry-run --force + review, then ship the reviewed bytes with this.")
    ap.add_argument("--budget", type=int, default=None,
                    help="fed-sample size override; default = dynamic_budget curve "
                         "(<=40 occ feeds all; 40/60/80 tiers above)")
    ap.add_argument("--force-verse", action="append", default=[], metavar="REF",
                    help="force a verse into the fed sample (e.g. 'Deu 13:8'), repeatable. SCOPE: a "
                         "post-floor coverage-completeness override for a MISSED-collocation idiom/job the "
                         "deterministic sampler skipped (FLOW step 1.5) — NOT general draw-shopping. Adds "
                         "beyond budget, never drops an auto-pick; hard-errors if the word does not occur "
                         "there. The forced refs + intent are logged on the draw record.")
    ap.add_argument("--floor", metavar="JSON",
                    help="saved lexica_agreement run (agreement_<SID>_*.json) to diff this word's "
                         "draw placements against — the #30 floor-vs-ship placement flag, FLAG-ONLY "
                         "at the dry-run gate. One word only; refuses a file whose strongs does not "
                         "match --word. Absent on a draw pass → the gate prints that the diff was "
                         "NOT run (an unchecked blind spot must not look like a pass).")
    ap.add_argument("--roster", metavar="JSON",
                    help="PATH (c) re-entry: anchor this word's draw to its banked FLOOR-CONSENSUS "
                         "roster (draw_hints.py 'roster') — inject the consensus sense count + "
                         "verse groups as soft-explicit draw context AND run the #55 sense-count "
                         "guard (ship count must equal roster count). Value = the word's saved "
                         "agreement_<SID>_*.json, i.e. the floor the roster was read from. Per-word "
                         "(needs --word, refuses --all); refuses a word with no roster (no "
                         "floor-drift record), and refuses a floor whose strongs isn't this word "
                         "or whose file isn't the roster's declared floor.")
    ap.add_argument("--structure-hint", action="append", default=[], metavar="JOB",
                    help="ESCALATION MECHANISM (post cap-out only, per the trigger ruling): pass one stable "
                         "sense/job (repeatable) from a prior review's certified stable-jobs list. Injected "
                         "into the draw CONTEXT (user message) as a check against burying/merging a distinct "
                         "job — the frozen prompt is untouched. Names jobs only, not carving; granularity "
                         "stays as-drawn. Logged on the draw record. Do NOT use as routine steering.")
    ap.add_argument("--hints", action="store_true",
                    help="inject the word's pre-registered CONSTRAINT hints (draw_hints.py) into the "
                         "draw context as a CONSTRAINT CHECK after the occurrences — parked-word "
                         "re-entry mechanism (DESIGN_hint_tooling.md, JP-ruled 2026-07-12). Frozen "
                         "prompt untouched; lines + provenance logged on the draw; part of the draw "
                         "signature. Refuses a word with no register entry.")
    ap.add_argument("--repair", action="store_true",
                    help="V10 COVERAGE REPAIR PASS (DESIGN_v10_repair.md): on a coverage-gate "
                         "failure, feed the card its own named absentees (verse texts, original "
                         "feed shape) in ONE bounded repair call; the repaired raw replaces the "
                         "draw and re-runs every gate fresh. Cap 2 rounds; structure guard "
                         "(headlines + citation superset) kills a breach, never re-repairs. "
                         "REVIEW pass only (--dry-run) — the repaired draw is cached for review "
                         "and a later --apply ships those reviewed bytes.")
    ap.add_argument("--quote-repair", action="store_true",
                    help="V11.2 QUOTE-REPAIR PASS (DESIGN_v11_acceptance.md ruling 1): on a "
                         "verbatim-quote-gate failure, feed the card the gate's own fail lines "
                         "plus every card-cited verse's stored bytes in ONE bounded repair call "
                         "(cap 1 round). Spans-only guard: anything changed outside quotation "
                         "marks kills the draw, never re-repairs. REVIEW pass only (--dry-run) — "
                         "the repaired draw is cached for review and the FULL battery re-runs as "
                         "if the card were new; a later --apply ships those reviewed bytes.")
    ap.add_argument("--no-hints", metavar="REASON",
                    help="run a REGISTERED word (draw_hints.py) deliberately WITHOUT its banked hints. "
                         "A registered word run without --hints refuses by default (ruling 1 — "
                         "forgetting the banked notes is almost certainly an operator mistake); this "
                         "is the logged override. The reason is stored on the draw record.")
    args = ap.parse_args()

    if not args.dry_run and not args.apply:
        sys.exit("Pass --dry-run (show, no write) or --apply (write).")
    if args.hints and args.no_hints:
        sys.exit("--hints and --no-hints contradict each other — pass one.")
    if (args.hints or args.no_hints) and args.all:
        sys.exit("--hints/--no-hints are per-word (the register is per-word) — use with --word, "
                 "never --all.")
    if args.from_draw and (not args.word or not args.apply or args.force or args.all or args.dry_run):
        sys.exit("--from-draw ships one reviewed draw: use as --apply --word G#### --from-draw KEY8 "
                 "(no --force / --all / --dry-run — it ships specific reviewed bytes, it never rolls).")
    if args.repair and (not args.dry_run or args.apply or args.resplit or args.all):
        sys.exit("--repair runs on the REVIEW pass only: --dry-run --word G#### (never with "
                 "--apply/--resplit/--all). The repaired draw is cached for human review; a "
                 "later --apply ships those reviewed bytes (review-what-ships).")
    if args.quote_repair and (not args.dry_run or args.apply or args.resplit or args.all):
        sys.exit("--quote-repair runs on the REVIEW pass only: --dry-run --word G#### (never "
                 "with --apply/--resplit/--all). The repaired draw is cached for human review; "
                 "a later --apply ships those reviewed bytes (review-what-ships).")
    if args.floor and (not args.word or args.all):
        sys.exit("--floor diffs ONE word against ITS OWN saved floor: use with --word G#### and "
                 "never --all (a floor is a per-word artifact).")
    if args.roster and (not args.word or args.all):
        sys.exit("--roster anchors ONE word to its OWN banked roster: use with --word G#### and "
                 "never --all (a roster is a per-word artifact).")
    if args.roster and args.resplit:
        sys.exit("--roster is a DRAW-time anchor (it steers the model draw); --resplit re-splits "
                 "stored prose with no model call. Nothing to anchor — drop one.")

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
        roster = None   # PATH (c): set + validated in the model branch; read by the #55 gate below

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
            # V7 dynamic budget: --budget still overrides explicitly; default = the ruled curve.
            budget = args.budget if args.budget is not None else dynamic_budget(len(occs))
            sample = select_spread(occs, budget)
            # V7 slot reservation: top-PMI neighbors guaranteed fed (adds, never displaces).
            sample = reserve_collocation_slots(conn, sid, occs, sample)
            if args.force_verse:
                # Post-floor coverage override (FLOW step 1.5): add MISSED-collocation idiom/job verses the
                # deterministic sampler skipped. Add-beyond-budget, never drop an auto-pick; refuse a ref the
                # word does not occur in (can't fabricate evidence). Logged on the draw record.
                have = {f"{o['book']} {o['ch']}:{o['vs']}" for o in sample}
                for ref in args.force_verse:
                    if ref in have:
                        continue
                    row = next((o for o in occs if f"{o['book']} {o['ch']}:{o['vs']}" == ref), None)
                    if row is None:
                        sys.exit(f"  ✗ --force-verse {ref!r}: {sid} does not occur there. Not forced.")
                    sample.append(row)
                sample.sort(key=lambda o: o["vid"])
                print(f"  forced into sample: {', '.join(args.force_verse)} "
                      f"(coverage override, FLOW step 1.5)")
            _colloc_warn(conn, sid, occs, sample)   # PIECE A: advisory only — never alters the draw
            ctx = fetch_context(conn, sample, has_surface)
            lemma, translit = lex_head(conn, sid)
            ot = sum(1 for c in ctx if c[0] not in NT_BOOKS)
            print(f"  occurrences {len(occs)} | {len(gset)} renderings | fed {len(ctx)} ({ot} OT / {len(ctx)-ot} NT)")

            # ── CONSTRAINT-HINT REGISTER (draw_hints.py; DESIGN_hint_tooling.md, JP-ruled
            # 2026-07-12). Refuse-when-forgotten is the DEFAULT (ruling 1): a registered word
            # re-entering without its banked hints is almost certainly an operator mistake.
            pmap = phrase_map(occs)
            reg = DRAW_HINTS.get(sid) or {}
            constraints = None
            if args.hints:
                if not reg.get("hints"):
                    print(f"  ✗ --hints: {sid} has no entry in draw_hints.py — nothing to inject. "
                          f"NOT run.", file=sys.stderr)
                    failures.append(sid); continue
                constraints = reg["hints"]
                print(f"  CONSTRAINT hints injected ({len(constraints)} line(s), register provenance: "
                      f"{reg.get('provenance', '(none)')}) — the draw will see, verbatim:")
                for i, c in enumerate(constraints, 1):
                    print(f"    {i}. {c}")
            elif reg.get("hints"):
                if args.no_hints:
                    print(f"  ⚠ {sid} IS REGISTERED in draw_hints.py ({len(reg['hints'])} banked "
                          f"line(s)) — running WITHOUT them by --no-hints override; reason logged "
                          f"on the draw: {args.no_hints}")
                else:
                    print(f"  ✗ {sid} is REGISTERED in draw_hints.py ({len(reg['hints'])} banked "
                          f"hint line(s)) but --hints was not passed. A parked word re-entering "
                          f"without its banked hints is refused by default (JP ruling 1, "
                          f"2026-07-12). Pass --hints, or override with --no-hints REASON. "
                          f"NOT run.", file=sys.stderr)
                    failures.append(sid); continue
            eff_jobs = args.structure_hint or (reg.get("jobs") if args.hints else None) or None
            if eff_jobs:
                print(f"  structure-hint (escalation mechanism, {len(eff_jobs)} jobs) injected "
                      f"into draw context — frozen prompt untouched, logged on the draw")
            # ── PATH (c) ROSTER (--roster; PATH (c) DESIGN — CLOSED, 2026-07-13). Anchor the draw
            # to the word's banked floor-consensus roster (soft-explicit context) + arm the #55
            # sense-count guard. Per-word opt-in; refuses a word with no roster, or a wrong floor.
            if args.roster:
                roster = reg.get("roster")
                if not roster:
                    print(f"  ✗ --roster: {sid} has no roster in draw_hints.py (no floor-drift "
                          f"record to anchor to). NOT run.", file=sys.stderr)
                    failures.append(sid); continue
                # The passed file must BE this word's floor: strongs match (load_floor sys.exits
                # otherwise) AND the roster's OWN declared floor file — no anchoring to a stray floor.
                load_floor(args.roster, sid)
                passed = os.path.basename(os.path.expanduser(args.roster))
                if passed != roster.get("floor"):
                    print(f"  ✗ --roster: {sid}'s roster was read from {roster.get('floor')!r}, but "
                          f"--roster names {passed!r} — wrong floor. NOT run.", file=sys.stderr)
                    failures.append(sid); continue
                print(f"  ROSTER injected (path (c)): {roster['count']} senses, "
                      f"{len(roster['groups'])} group(s) from {roster['floor']} — soft-explicit "
                      f"draw context; #55 sense-count guard armed. Frozen prompt untouched.")
            # ── DRAW CACHE. Recompute the current input signature live; consult the cached draw.
            sig = draw_signature(sid, translit, gset, ctx, eff_jobs, pmap, constraints, roster)
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
                raw = model_prose(client, sid, translit, gset, ctx, eff_jobs, pmap, constraints, roster)
                if args.dry_run or args.force:
                    # ro (review pass) and --force write/refresh the draw so apply ships THIS prose.
                    save_draw(sid, lemma, translit, gset, ctx, raw,
                              forced=args.force_verse, hint=eff_jobs,
                              pmap=pmap, constraints=constraints, no_hints_reason=args.no_hints,
                              roster=roster)
                    tag = " (forced — cache refreshed)" if args.force else ""
                    print(f"  cached draw → {draw_path(sid)} (key {sig[:8]}){tag}")
                elif args.apply:
                    # permissive single-word apply on a miss: fresh + loud, NO draw file written
                    # (an unreviewed draw must not later masquerade as reviewed).
                    print(f"  ⚠ UNREVIEWED — no cached draw for {sid}; this write was NOT reviewed.",
                          file=sys.stderr)
                    unreviewed.append(sid)

        # ── REPAIR PASSES (--repair / --quote-repair, review pass only — the CLI refusals
        # above guarantee ctx exists here). Both run BEFORE assemble so the entry below is
        # built from the FINAL raw: splitter, citation gate, coverage gate, #30 floor-diff,
        # and every checker warn all re-run on the repaired card exactly as on any fresh
        # draw (the lesson-#50-b mechanism). ONE shared model closure — never two copies.
        rrec = qrec = None
        if args.repair or args.quote_repair:
            def _live_repair(msg):
                nonlocal client
                if client is None:
                    client = make_client()
                m = client.messages.create(model=MODEL_SONNET, max_tokens=MAX_TOKENS,
                                           messages=[{"role": "user", "content": msg}])
                return "".join(b.text for b in m.content
                               if getattr(b, "type", "") == "text").strip()

        # ── V10 COVERAGE REPAIR PASS.
        if args.repair:
            rep_fed = [(c[0], c[1], c[2]) for c in ctx]
            raw2, rrec, rprobs = coverage_repair(raw, rep_fed, ctx, _live_repair)
            if rprobs:
                print("  ✗ REPAIR PASS — draw DEAD (cached draw untouched):", file=sys.stderr)
                for p in rprobs:
                    print("      - " + p, file=sys.stderr)
                failures.append(sid)
                continue
            if rrec:
                raw = raw2
                save_draw(sid, lemma, translit, gset, ctx, raw,
                          forced=args.force_verse, hint=eff_jobs, pmap=pmap,
                          constraints=constraints, no_hints_reason=args.no_hints,
                          repair=rrec, roster=roster)
                print(f"  REPAIRED draw cached → {draw_path(sid)} (round(s): {rrec['rounds']}, "
                      f"integrated: {', '.join(rrec['refs'])}, {rrec['prompt_ver']}) — "
                      f"review THIS card below; a later --apply ships these bytes.")
            else:
                print("  --repair: coverage already clean — repair did not fire.")

        # ── V11.2 QUOTE-REPAIR PASS (after coverage repair, so the quote gate sees the
        # final coverage-repaired prose). vt = own live lookups for EVERY card-cited ref
        # (the probe-1 convention — the fed sample can never cover Range/gloss/repair refs).
        if args.quote_repair:
            qvt = {}
            for b, c, v in cited_refs(raw):
                row = conn.execute("SELECT text FROM verses WHERE book=? AND chapter=? "
                                   "AND verse=?", (b, c, v)).fetchone()
                qvt[(b, c, v)] = (row["text"] if row and row["text"] else None)
            raw3, qrec, qprobs = quote_repair(raw, qvt, _live_repair)
            if qprobs:
                print("  ✗ QUOTE-REPAIR PASS — draw DEAD (cached draw untouched):",
                      file=sys.stderr)
                for p in qprobs:
                    print("      - " + p, file=sys.stderr)
                bank_refused_repair(sid, "quote", qrec)   # ticket 1: bank before dropping qrec
                failures.append(sid)
                continue
            if qrec:
                raw = raw3
                save_draw(sid, lemma, translit, gset, ctx, raw,
                          forced=args.force_verse, hint=eff_jobs, pmap=pmap,
                          constraints=constraints, no_hints_reason=args.no_hints,
                          repair=rrec, qrepair=qrec, roster=roster)
                print(f"  QUOTE-REPAIRED draw cached → {draw_path(sid)} "
                      f"(round(s): {qrec['rounds']}, {qrec['prompt_ver']}) — review THIS "
                      f"card below (FULL battery owed as if new, lesson #50 b); a later "
                      f"--apply ships these bytes.")
                # RULING 4: surface every repair-CHANGED span loud, so the reviewer reads the
                # live verse and byte-confirms the introduced wording before it ships.
                for ch in qrec.get("repair_introduced", []):
                    print(f"    repair-introduced; re-gated MATCH vs {ch['matched']}: "
                          f'"{ch["before"]}" → "{ch["after"]}" — byte-confirm vs the live verse.')
            else:
                print("  --quote-repair: quote gate clean — quote repair did not fire.")

        entry = assemble(conn, sid, lemma, translit, raw)
        entry["synth_ver"] = stamp
        # V10/V11.2: a repaired card's audit carries the same stamps as its draw record.
        if args.repair and rrec:
            entry["audit"]["repair"] = rrec
        if args.quote_repair and qrec:
            entry["audit"]["quote_repair"] = qrec
        # V9 coverage gate input — the fed sample only exists on draw/apply passes.
        if args.resplit:
            entry["audit"]["fed_uncited"] = None
            fed_ctx = None   # no fed sample on a resplit — probe-2 runs strict (fails toward the human)
            print("  ⚠ coverage gate NOT RUN — resplit re-splits stored prose; no fed sample "
                  "on this pass.")
        else:
            fed_keys = [(c[0], c[1], c[2]) for c in ctx]
            # grounded-naming: each fed occurrence's context verse texts, keyed by its ref,
            # handed to probe-2 so a name the model was SHOWN (in context) doesn't warn.
            fed_ctx = {(c[0], c[1], c[2]): [t for _, _, t in c[8]] for c in ctx}
            entry["audit"]["fed_uncited"] = coverage_gate(fed_keys, entry["senses_block"])
            n_fed = len(set(fed_keys))
            print(f"  coverage gate: {n_fed - len(entry['audit']['fed_uncited'])}/{n_fed} "
                  f"fed refs cited under a sense.")
        # Bypass ordering: stamped AFTER assemble (so the audit buckets exist), BEFORE
        # validate_entry reads it — and ONLY on a word whose gate actually failed (either
        # gate: citation misses OR uncited fed refs — a pure widening, no term removed),
        # so a clean word in the same batch never carries a stale bypass note.
        if args.force_gate_bypass and (
                any(m["bucket"] in ("real", "noverse") for m in entry["audit"]["misses"])
                or entry["audit"].get("fed_uncited")):
            entry["audit"]["bypass_reason"] = args.force_gate_bypass
        # #30 floor-vs-ship placement diff (flag-only). The record lands in the entry (and so on
        # an applied row) ONLY when a floor was diffed; a resplit pass never nags about it.
        if args.floor:
            entry["audit"]["floor_diff"] = floor_diff_record(load_floor(args.floor, sid),
                                                             entry["senses_block"])
        # #55 SENSE-COUNT GUARD (path (c)): compare the ship sense count to the roster count.
        # Record lands on the entry (and so on an applied row) ONLY when a roster was anchored.
        if args.roster and roster:
            entry["audit"]["roster_count"] = roster_count_diff(roster, entry["senses_block"])
        show_entry(entry)
        if not args.floor and not args.resplit:
            print("  ⚠ #30 floor-diff NOT RUN — no --floor <agreement json> on this pass; the "
                  "placement blind spot is UNCHECKED (the insurance clause gates count ships on "
                  "#30 live).")

        problems = validate_entry(entry, conn, fed_ctx=fed_ctx)
        if problems:
            print("  ✗ PARSE FAILURE — NOT written (a load-bearing field came back empty):")
            for p in problems:
                print("      - " + p)
            failures.append(sid)
            continue                              # never write an incomplete row

        # #55 SENSE-COUNT GUARD (path (c), GATE CONDITION): the ship sense count MUST equal the
        # roster count. A mismatch means the floor consensus was collapsed (a pole vanished — the
        # #30 pair-membership check can't see that) or split; it is part of path (c)'s definition,
        # not a soft flag, so an --apply is REFUSED. The review pass prints it loud for the reviewer.
        rcd = entry["audit"].get("roster_count")
        if rcd and not rcd["ok"]:
            if args.apply:
                print(f"  ✗ NOT written — #55 sense-count guard: shipped {rcd['ship_count']} "
                      f"sense(s) but the roster fixes {rcd['roster_count']} (floor {rcd['floor']}). "
                      f"The floor consensus was collapsed or split — re-draw or PARK.",
                      file=sys.stderr)
                failures.append(sid)
                continue
            print(f"  ⚠ #55 sense-count guard FIRES: shipped {rcd['ship_count']} sense(s), roster "
                  f"fixes {rcd['roster_count']} — an apply will be REFUSED (collapse/split).",
                  file=sys.stderr)

        # V11 open-warn-blocks-apply (GATE CONDITION). Adjudication is a reviewer ruling
        # relayed as --adjudicate-warns "note"; the note ships in the row (self-documents).
        if args.adjudicate_warns and (entry["audit"].get("probe1_warns")
                                      or entry["audit"].get("probe2_warns")
                                      or entry["audit"].get("scan3_warns")
                                      or entry["audit"].get("probe1_notrun")
                                      or entry["audit"].get("probe2_notrun")):
            entry["audit"]["warns_adjudicated"] = args.adjudicate_warns
        elif args.resplit:
            # A resplit re-derives from the SAME stored prose, so a stored ruling still covers the
            # same claims — carried ONLY when the warn set is byte-identical (carry_adjudication
            # holds the reasoning and the refusals). An explicit --adjudicate-warns above always
            # wins. Without this, a batch resplit refuses every adjudicated card while reporting
            # success on the rest.
            _old = json.loads(existing["def_json"]) if (existing and existing["def_json"]) else None
            _carried = carry_adjudication(_old, entry["audit"], True)
            if _carried:
                entry["audit"]["warns_adjudicated"] = _carried
                entry["audit"]["warns_adjudication_carried"] = True   # VISIBLE — never silent
                print("  ⚠ adjudication CARRIED from the stored row (warn set byte-identical, "
                      "prose unchanged by a resplit) — NOT a fresh human ruling; stamped "
                      "warns_adjudication_carried on the row.")
        blocked = open_probe_warns(entry)
        if blocked:
            if args.apply:
                print(f"  ✗ NOT written — {len(blocked)} OPEN V11 item(s) (probe-1 in-band cue "
                      f"warns, probe-2/scanner-3 warns, or probe NOT-RUNs) with no adjudication; "
                      f"after the reviewer rules them, re-run with --adjudicate-warns \"ruling\":",
                      file=sys.stderr)
                for w in blocked:
                    print("      - " + w, file=sys.stderr)
                failures.append(sid)
                continue
            print(f"  ⚠ {len(blocked)} OPEN V11 item(s) — an apply will be REFUSED until "
                  f"adjudicated (--adjudicate-warns).", file=sys.stderr)

        # V11: warns land on the DRAW RECORD too (review pass), so the run-session record
        # carries them where the adjudication happens. Atomic rewrite, raw untouched.
        if not args.apply and not args.resplit and os.path.exists(draw_path(sid)):
            drec = load_draw(sid)
            if drec is not None:
                drec["probe_warns"] = {
                    "probe1": entry["audit"].get("probe1_warns", []),
                    "probe2": entry["audit"].get("probe2_warns", []),
                    "scan3": entry["audit"].get("scan3_warns", []),
                    "notrun": (entry["audit"].get("probe1_notrun", [])
                               + entry["audit"].get("probe2_notrun", [])),
                    "vers": entry["audit"].get("probe_vers", {}),
                }
                _tmp = draw_path(sid) + ".tmp"
                with open(_tmp, "w", encoding="utf-8") as f:
                    json.dump(drec, f, ensure_ascii=False, indent=1)
                os.replace(_tmp, draw_path(sid))

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
