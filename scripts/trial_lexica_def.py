#!/usr/bin/env python3
"""
trial_lexica_def.py  —  BAKE-OFF for the "Lexica dictionary" idea (throwaway test rig).

FINAL design (2026-06-24): ONE engine — verse-grounded (Sonnet) defines EVERY word from its own
attested use (VERSE_PROMPT). LSJ is display-only, never a source. The old LSJ-source ROUTER
(length pre-filter + "bears-out" check + Haiku LSJ-source engine) is the KILLED approach, kept
below ONLY as the record — don't port it. Why it died: freight LSJ canonizes as its LEAD sense
(aionios -> "eternal") leaves no gap for any compare-to-LSJ check to catch. See memory
project_lexica_dictionary.

THE CONTESTED-WORD FAIRNESS GATE (this file's current job, chat design 2026-06-24):
a word on the hand-authored CONTESTED list is, by MEMBERSHIP ALONE, read more than one way.
After its verse def is written, the gate appends a hand-authored fork block: the attested core,
then each live reading named with its tradition, then a "full map" pointer ONLY where a real
argument graph maps the split. NO model, NO detector, NO second pass — we distrust the model's
fork CONTENT enough to hand-author it, so we distrust its fork DETECTION too (and the dikaioo
collapse was invisible from the output anyway: nothing to detect, no surface to fool). "Catch"
(the dikaioo HOLD condition) = surface the fork INLINE; it does NOT mean "link to a graph".
graph_ref is nullable — 4 of 5 are null today, and the links light up per-word as argument
graphs get authored. Edit the CONTESTED block to tune the forks.

Throwaway. Read-only on bible.db. The verse engine runs on PA (bible.db + the model key live
there); the fairness gate is pure Python (no db, no model), so `--show-forks` runs ANYWHERE.

  workon bible-env
  export ANTHROPIC_API_KEY=$(grep -oE "sk-ant-[A-Za-z0-9_-]+" /var/www/www_lexica_bible_wsgi.py)
  python scripts/trial_lexica_def.py --show-forks                       # the fork blocks, FREE (no db/model)
  python scripts/trial_lexica_def.py --dry-run --verses --word G1344    # inspect inputs + the fork it'd append
  python scripts/trial_lexica_def.py --word G1344                       # define dikaioo + append its fork
  python scripts/trial_lexica_def.py --engine verse                     # the whole set, one verse engine

Iterating: edit VERSE_PROMPT (the definition) or CONTESTED (the forks) below and re-run.
"""

import argparse, html, json, os, re, sqlite3, sys, unicodedata
from collections import OrderedDict, Counter

# ══════════════════════════════════════════════════════════════════════════════
# PROMPT 1 — THE ROUTER's verse-bears-out check (Sonnet). Runs ONLY on SHORT entries;
# long / missing entries skip it and go straight to verse-grounding.
# Reframed v2 (2026-06-23): the v1 "does the usage FIT LSJ" test was blind to freight LSJ
# itself canonizes as its lead sense (aionios -> LSJ leads "eternal" AND files the biblical
# verses under it, so "fits" was trivially yes). v2 inverts it: derive the sense from the
# bare contexts first, then ask whether LSJ's LEAD gloss claims MORE than the contexts require.
# ══════════════════════════════════════════════════════════════════════════════
BEARS_OUT_PROMPT = """\
You decide whether a Greek word should be defined from its classical dictionary entry (LSJ) or
from its own biblical usage. The danger you guard against: LSJ's leading gloss sometimes claims
MORE than the biblical contexts actually establish, and defining from LSJ would then load the
word with meaning the text does not carry.

You are given:
- the word's LSJ entry
- a sample of biblical occurrences: each a verse with the word's rendering marked

Method:
1. First, IGNORING both LSJ's glosses and the English renderings, read the occurrences and decide
   what the bare contexts actually require the word to mean - the least that must be true for the
   word to fit every verse.
2. Then look at LSJ's LEADING gloss (its primary, first-listed sense).
3. Compare. The word is DIVERGENT if EITHER:
   a) LSJ's leading gloss claims MORE than the contexts require - more abstract, more absolute,
      more metaphysical, or more theologically loaded than the bare verses establish (e.g. LSJ
      says "eternal, timeless" where the contexts only require "lasting for an age, perpetual,
      or ancient"). Defining from LSJ would over-read the text.
   b) the usage carries a sense LSJ does not have at all.
   Otherwise the word is CLEAN: LSJ's leading gloss matches what the contexts require, so LSJ
   is a safe source to define from.

Do not flag a word just because LSJ also lists extra MINOR senses the Bible doesn't use - that
is normal. The test is LSJ's LEADING gloss versus what the contexts require.

Return JSON only, nothing else:
{"verdict": "clean" | "divergent",
 "context_requires": "the bare sense the verses establish, one phrase",
 "lsj_lead": "LSJ's leading gloss, one phrase",
 "overread": "how LSJ's lead exceeds the contexts, or empty string if it does not",
 "reason": "one sentence"}
"""

# ══════════════════════════════════════════════════════════════════════════════
# PROMPT 2 — LSJ-AS-SOURCE definition (Haiku), for CLEAN words.
# (verbatim from views_lsj.py _LSJ_SYNTHESIS_SYSTEM)
# ══════════════════════════════════════════════════════════════════════════════
LSJ_SOURCE_PROMPT = """\
Define the Greek word below from the dictionary entry provided. Open with the meaning itself \
— your first words are the definition, with no preface (not the word, not "this word means," \
not "it refers to"). State its central, everyday meaning — the common Koine sense, not \
specialized classical-era detail — plus the one or two other senses the entry clearly draws. \
Prefer everyday words over specialized religious vocabulary (e.g. χάρις is favor or goodwill, \
not grace; πνεῦμα is spirit or breath, not ghost). Do not organize the senses by where the \
word appears or name the texts it appears in; give what the word means, not where it is used. \
Add nothing from doctrine, theology, or your own knowledge beyond what the entry gives. \
Ignore the entry's citations, source references, and grammatical notes. Write one short \
paragraph of plain prose, no markdown.\
"""

# ══════════════════════════════════════════════════════════════════════════════
# PROMPT 3 — VERSE-GROUNDED definition (Sonnet), for DIVERGENT words.  (from chat)
# ══════════════════════════════════════════════════════════════════════════════
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
2. Group occurrences into the distinct senses the contexts actually require. Two
   occurrences share a sense only if the contexts, not the glosses, put them
   together.
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
- Do not narrate the word's later doctrinal or ecclesiastical career. No "came to
  mean," no "in later usage." Attested biblical use only.
- Define the word; do not adjudicate what doctrine rests on it.

Output (compact, dictionary-entry style):
- Senses: each a short gloss-free characterization with grounding references in
  parentheses, ordered by frequency in the supplied set.
- Range: one line on how far the word stretches and what moves it.
- Gloss notes: only where a gloss narrows, loads, or diverges from what the
  contexts support. Name the gloss and the divergence. Omit the line if nothing
  to flag.
- Coverage: if the supplied occurrences are too few or too clustered to
  characterize the range, say so in one line. Omit if coverage is adequate.

No preamble, no restating the lemma, no closing summary.
"""

MODEL_HAIKU  = "claude-haiku-4-5-20251001"   # LSJ-source definition (clean words)
MODEL_SONNET = "claude-sonnet-4-6"           # verse-bears-out check + verse-grounded definition
BUDGET         = 40                          # verses fed to the verse engine / bears-out check
LONG_THRESHOLD = 2500                        # LSJ entry >= this many chars -> straight to verse (no check)
STUB_FLOOR     = 80                          # entry < this = a cross-ref stub ("v. χάρις"), not a real entry
MAX_TOKENS     = 1500

# Sequence: easy confirmation words first, then a known CALQUE early to validate the branch
# (psyche/doxa SHOULD route divergent). Then the rest.
WORDS = [
    ("G740",  "artos",      "bread  -- easy control (expect CLEAN -> Haiku/LSJ)"),
    ("G3056", "logos",      "word / account / reason  -- maps to LSJ (expect CLEAN-ish)"),
    ("G5590", "psyche",     "soul / life  -- CALQUE TEST (expect DIVERGENT -> Sonnet/verse)"),
    ("G1391", "doxa",       "glory / opinion  -- CALQUE TEST (LSJ leads 'opinion')"),
    ("G5484", "charin",     "favor, kindness  -- (ABP tags charis as G5484, not 5485)"),
    ("G4151", "pneuma",     "spirit / breath / ghost"),
    ("G1577", "ekklesia",   "assembly / church (LSJ classical blind spot)"),
    ("G907",  "baptizo",    "immerse / baptize"),
    ("G3009", "leitourgia", "service / ministry"),
    ("G166",  "aionios",    "eternal / age-long  (override pending)"),
    ("G1344", "dikaioo",    "justify / make righteous  (held)"),
    ("G4102", "pistis",     "faith / trust"),
    ("G4561", "sarx",       "flesh"),
]

# Current hand-written overrides (verbatim from views_lsj.py _LSJ_OVERRIDES), for the side-by-side.
OVERRIDES = {
    "G1577": "assembly, congregation; a gathered body convened for a common purpose",
    "G3009": "service, ministry; the performance of a public duty or sacred service - and so priestly or religious ministration",
    "G907":  "to dip, immerse, or plunge; to submerge or be overwhelmed; and as a religious act, to immerse - a ritual washing",
    "G5484": "favor, goodwill, or kindness; thanks or gratitude; the charm or elegance that pleases; and, used adverbially, for the sake of or because of",
    "G3056": "a word, statement, or message - what is said or spoken; also an account or reckoning, and the reason or ground behind something",
    "G4151": "breath or wind; the breath of life; and so spirit - the immaterial part of a person, or a spiritual being",
}

# ══════════════════════════════════════════════════════════════════════════════
# THE CONTESTED-WORD FAIRNESS GATE — the hand-authored fork register (chat design 2026-06-24).
# A word in here is, by MEMBERSHIP ALONE, flagged "read more than one way": after its verse def
# is written, render_fork() appends the block below verbatim. NO model, NO detector — we distrust
# the model's fork CONTENT enough to hand-author it, so we distrust its fork DETECTION too.
#
# Each entry: core = the attested sense both/all sides grant; frames = the live readings, each
# (label, tradition, gloss); graph_ref = "<study_id>:<claimid>|<claimid>" pointing at the
# argument graph that maps the split, or None until one is authored (4 of 5 are None today).
#
# DATA NOTES (deliberately diverge from the chat spec — source/corpus beats the chat on data):
#   - charis: ABP tags it G5484 (the form χάριν), NOT the textbook G5485 (whose lexicon/LSJ entry
#     is an empty stub). The corpus words carry G5484, so the gate MUST fire on G5484 or it never
#     triggers on charis. Keyed under G5484 (+ G5485 as an alias).
#   - the baptism graph's study id is "baptism_who" (not "baptism"); claim ids
#     def_grace_infused / obj_grace_charis are verbatim from scripts/add_study_graph.py.
# ══════════════════════════════════════════════════════════════════════════════
CONTESTED = OrderedDict([
    ("G1344", {
        "lemma": "dikaioō", "gloss": "justify",
        "core": "to deem, treat, or pronounce just; to set right, hold to be in the right",
        "frames": [
            ("forensic / imputed", "Reformation",
             "a legal verdict — righteous status declared, not moral change"),
            ("transformative / infused", "Catholic / Trent",
             "actually made righteous; the -oō verb as factitive (James 2)"),
            ("covenant-membership", "New Perspective",
             "declarative, but about who belongs to God's people — not imputed moral righteousness"),
        ],
        "note": "forensic and covenant-membership share the declarative mechanism; "
                "they split on content, not declare-vs-make",
        "graph_ref": None,
    }),
    ("G166", {
        "lemma": "aionios", "gloss": "eternal / age-long",
        "core": "pertaining to an age; long-lasting, ancient",
        "frames": [
            ("unending duration", "—", "everlasting, without end"),
            ("of-the-coming-age / qualitative", "inaugurated-eschatology",
             "belonging to the age to come; a quality of life, not only its length"),
        ],
        "graph_ref": None,
    }),
    ("G5484", {
        "lemma": "charis", "gloss": "favor / grace",
        "aliases": ["G5485"],   # textbook number; G5484 is the one ABP actually tags
        "core": "favor, goodwill, gift",
        "frames": [
            ("unmerited favor by faith", "Reformed",
             "God's gracious disposition, received by faith"),
            ("infused grace", "sacramental", "a quality imparted by a rite"),
        ],
        "graph_ref": "baptism_who:def_grace_infused|obj_grace_charis",
    }),
    ("G4561", {
        "lemma": "sarx", "gloss": "flesh",
        "core": "body, human being, mortal nature",
        "frames": [
            ("embodied humanity", "—", "the physical/human, morally neutral"),
            ("sin-principle", "—",
             "the disposition opposed to the Spirit; NIV 'sinful nature' — itself a contested gloss"),
        ],
        "graph_ref": None,
    }),
    ("G1577", {
        "lemma": "ekklesia", "gloss": "assembly / church",
        "core": "an assembly; a convened gathering or congregation",
        "etymology_note": "ek-kaleō, 'called out' — etymologizing gloss, not a sense felt in "
                          "usage; flag, don't seat in core",
        "frames": [
            ("local congregation", "—", "a particular gathered body in a place"),
            ("universal body of believers", "invisible-church",
             "all believers across time; visible institution not implied"),
            ("institutional Church", "hierarchical / sacramental",
             "the visible, structured Church as an entity"),
        ],
        "graph_ref": None,
    }),
])

# membership index: every Strong's number (primary + aliases) -> its entry
_CONTESTED_BY_SID = {}
for _sid, _e in CONTESTED.items():
    _CONTESTED_BY_SID[_sid] = _e
    for _a in _e.get("aliases", []):
        _CONTESTED_BY_SID[_a] = _e

NT_BOOKS = {"Mat","Mar","Luk","Joh","Act","Rom","1Co","2Co","Gal","Eph","Php","Col",
            "1Th","2Th","1Ti","2Ti","Tit","Phm","Heb","Jas","1Pe","2Pe","1Jn","2Jn","3Jn","Jud","Rev"}

# PROOF set: the verses a verse-grounded definition cited, (ref, sense#), so --audit can confirm
# each one really contains the target word in ABP and print the text to check it supports its sense.
# Seeded with the psyche (G5590) run from 2026-06-23.
AUDIT = {
    "G5590": [
        ("Deu 10:22", 1), ("Exo 12:15", 1), ("Num 19:18", 1), ("Rom 2:9", 1), ("Rev 16:3", 1),
        ("Jos 9:24", 2), ("1Ki 1:12", 2), ("Jdg 5:18", 2), ("Jas 5:20", 2), ("1Jn 3:16", 2),
        ("Php 2:30", 2), ("Act 20:10", 2), ("Luk 9:56", 2), ("1Th 2:8", 2), ("Mar 8:36", 2), ("Mat 10:28", 2),
        ("Gen 1:30", 3), ("Lev 11:46", 3), ("Gen 2:7", 3), ("1Co 15:45", 3),
        ("1Sa 1:10", 4), ("2Sa 3:21", 4), ("Job 21:8", 4), ("2Ki 2:2", 4), ("1Ch 12:38", 4),
        ("Pro 2:10", 4), ("Col 3:23", 4), ("Eph 6:6", 4), ("2Co 1:23", 4), ("2Pe 2:8", 4),
        ("3Jn 1:2", 4), ("1Pe 2:11", 4), ("Psa 19:7", 4), ("Heb 4:12", 4), ("Rth 4:15", 4),
        ("Est 7:3", 4), ("Joh 10:24", 4),
        ("Isa 5:14", 5),
    ],
}


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
             "or add a line to ~/bible-db/.env, then re-run. (Or use --dry-run for no model calls.)")


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


def parse_json(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def table_exists(conn, name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (name,)).fetchone() is not None


def abp_filter(conn, sid):
    """WHERE predicate for a clean base G-number, mirroring views_lexicon._abp_strongs_filter."""
    if table_exists(conn, "dotted_lexicon"):
        return ("w.strongs_base = ? AND 'G' || w.strongs NOT IN (SELECT strongs FROM dotted_lexicon)", [sid])
    return ("w.strongs_base = ?", [sid])


def gloss_set(conn, pred, params):
    """The 'renders as' set: single-word english_head renderings with counts, like the live line."""
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


def lsj_entry(conn, sid):
    """(lemma, full-entry-text) for a Strong's number: lexicon maps number->lemma, lsj holds the
    full entry. Accent-stripped fallback mirrors views_lsj. Returns (lemma, None) if no entry."""
    r = conn.execute("SELECT lemma FROM lexicon WHERE strongs_g = ?", (sid,)).fetchone()
    if not r or not r["lemma"]:
        return None, None
    lemma = r["lemma"]
    row = conn.execute("SELECT def_html FROM lsj WHERE key = ?", (lemma,)).fetchone()
    if not row:
        plain = strip_accents(lemma).lower().replace("-", "")
        row = conn.execute(
            "SELECT def_html FROM lsj WHERE lower(strip_accents(replace(key,'-',''))) = ? "
            "AND key NOT LIKE '-%'", (plain,)).fetchone()
    if not row or not row["def_html"]:
        return lemma, None
    return lemma, strip_html(row["def_html"])


def select_spread(occs, budget):
    """Sample that surfaces the SENSE range, not just the commonest use: per-rendering floor +
    proportional fill, balancing TESTAMENT (OT/NT) then book within each rendering."""
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


def render_fork(entry):
    """The fairness block appended to a contested word's definition. Model-free: lays out the
    hand-authored fork verbatim — core, then each live reading (label, tradition, gloss), then a
    pointer to the argument graph that maps the split. In the APP the pointer line is shown ONLY
    when graph_ref is set; here we print "(none authored yet)" so the trial shows the real state."""
    L = ["", "── CONTESTED WORD — the definition above does not settle this ──",
         f"Core (attested): {entry['core']}"]
    if entry.get("etymology_note"):
        L.append(f"  (etymology flag: {entry['etymology_note']})")
    L.append("Read more than one way:")
    for label, tradition, gloss in entry["frames"]:
        trad = "" if tradition in ("", "—") else f" [{tradition}]"
        L.append(f"  • {label}{trad}: {gloss}")
    if entry.get("note"):
        L.append(f"Note: {entry['note']}")
    ref = entry.get("graph_ref")
    L.append(f"Full argument map: {ref}" if ref else "Full argument map: (none authored yet)")
    return "\n".join(L)


def model_text(client, model, system, user, max_tokens=MAX_TOKENS):
    msg = client.messages.create(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def route(client, entry, long_threshold, verse_msg):
    """Length pre-filter + verse-bears-out check:
       - no entry / LONG entry  -> divergent (verse-ground), no model call
       - SHORT entry            -> Sonnet bears-out check decides."""
    if not entry or len(entry) < STUB_FLOOR:
        why = "no LSJ entry" if not entry else f"stub/cross-ref entry ({len(entry)} chars)"
        return {"verdict": "divergent", "reason": f"{why} - verse-ground by default"}
    if len(entry) >= long_threshold:
        return {"verdict": "divergent",
                "reason": f"long LSJ entry ({len(entry)} chars >= {long_threshold}) - auto verse-ground, no check"}
    user = f"LSJ ENTRY:\n{entry}\n\nBIBLICAL OCCURRENCES:\n{verse_msg}"
    txt = model_text(client, MODEL_SONNET, BEARS_OUT_PROMPT, user, max_tokens=700)
    v = parse_json(txt)
    if not v:
        return {"verdict": "divergent", "reason": "bears-out check unparseable: " + txt[:160]}
    return v


def audit(conn, sid):
    """Prove a verse-grounded definition's citations: for each verse it cited, confirm the
    verse actually carries the target word in ABP (PASS), and print the ABP text so the
    sense it was assigned to can be checked. A MISS = the verse has no G-number occurrence
    (a bad citation OR ABP versification drift — the printed text tells which)."""
    refs = AUDIT.get(sid)
    if not refs:
        print(f"(no audit set embedded for {sid})")
        return
    pred, params = abp_filter(conn, sid)
    keyset = {(o["book"], int(o["ch"]), int(o["vs"])) for o in occurrences(conn, pred, params)}
    npass = 0
    for ref, sense in refs:
        book, cv = ref.rsplit(" ", 1)
        ch, vs = (int(x) for x in cv.split(":"))
        present = (book, ch, vs) in keyset
        npass += present
        row = conn.execute("SELECT text FROM verses WHERE book=? AND chapter=? AND verse=?",
                           (book, ch, vs)).fetchone()
        text = row["text"] if row else "(verse not found in ABP)"
        print(f"[{'PASS' if present else 'MISS'}] sense {sense}  {ref}")
        print(f"        {text}")
    print(f"\n{npass}/{len(refs)} cited verses actually contain {sid} in ABP.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"))
    ap.add_argument("--word", help="run a single G-number, e.g. G5590")
    ap.add_argument("--dry-run", action="store_true", help="show inputs; NO model calls (free)")
    ap.add_argument("--verses", action="store_true", help="also print the fed occurrences")
    ap.add_argument("--budget", type=int, default=BUDGET)
    ap.add_argument("--engine", choices=["auto", "verse", "lsj"], default="auto",
                    help="force an engine instead of letting the router decide")
    ap.add_argument("--long", type=int, default=LONG_THRESHOLD,
                    help="LSJ entry >= this many chars routes straight to verse-grounding")
    ap.add_argument("--audit", action="store_true",
                    help="prove a definition's citations: check each cited verse really contains the word (no model)")
    ap.add_argument("--show-forks", action="store_true",
                    help="print every contested word's fairness fork block; NO db, NO model (runs anywhere)")
    args = ap.parse_args()

    if args.show_forks:
        for sid, e in CONTESTED.items():
            extra = (" (+" + ", ".join(e["aliases"]) + ")") if e.get("aliases") else ""
            print("\n" + "=" * 78)
            print(f'{sid}{extra}  {e["lemma"]}  "{e["gloss"]}"  -- graph_ref: {e.get("graph_ref")}')
            print(render_fork(e))
        return

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.create_function("strip_accents", 1, strip_accents)
    has_surface = table_exists(conn, "abp_surface")

    client = None
    if not args.dry_run and not args.audit:
        import anthropic
        client = anthropic.Anthropic(api_key=get_key())

    if args.word:
        target = args.word.upper()
        if target[:1] not in ("G", "H"):
            target = "G" + target
        match = [w for w in WORDS if w[0].upper() == target]
        words = match if match else [(target, "?", "ad-hoc")]
    else:
        words = WORDS

    if args.audit:
        for sid, translit, note in words:
            print("\n" + "=" * 78)
            print(f"{sid}  {translit}  ({note})  -- citation audit")
            audit(conn, sid)
        conn.close()
        return

    for sid, translit, note in words:
        pred, params = abp_filter(conn, sid)
        gset = gloss_set(conn, pred, params)
        occs = occurrences(conn, pred, params)
        sample = select_spread(occs, args.budget)
        ctx = fetch_context(conn, sample, has_surface)
        lemma, entry = lsj_entry(conn, sid)
        ot = sum(1 for c in ctx if c[0] not in NT_BOOKS)
        nt = len(ctx) - ot

        print("\n" + "=" * 78)
        print(f"{sid}  {translit}  ({note})")
        print(f"occurrences: {len(occs)} total | {len(gset)} renderings | fed {len(ctx)}  ({ot} OT / {nt} NT)")
        print("renders as: " + ", ".join(f"{g} {c}" for g, c in gset[:12]) + (" ..." if len(gset) > 12 else ""))
        print(f"LSJ: {lemma or '(no lexicon lemma)'}  " +
              (f"[entry {len(entry)} chars]" if entry else "[NO LSJ ENTRY]"))
        ov = OVERRIDES.get(sid)
        print("current override: " + (ov if ov else "(none today)"))
        print("-" * 78)

        if args.dry_run:
            if not entry:
                lr = "VERSE (no LSJ entry)"
            elif len(entry) < STUB_FLOOR:
                lr = f"VERSE (stub/cross-ref entry, {len(entry)} chars)"
            elif len(entry) >= args.long:
                lr = f"VERSE (long entry, {len(entry)} >= {args.long})"
            else:
                lr = f"SHORT ({len(entry)} chars) -> bears-out check would decide"
            print(f"length-route: {lr}")
            if args.verses:
                print(verse_user_msg(sid, translit, gset, ctx))
                print("-" * 78)
            ce = _CONTESTED_BY_SID.get(sid)
            if ce:
                print("contested word -> fork the gate would append:")
                print(render_fork(ce))
            print("[dry run - model calls skipped]")
            continue

        if args.engine == "auto":
            vmsg = verse_user_msg(sid, translit, gset, ctx)
            verdict = route(client, entry, args.long, vmsg)
            v = (verdict.get("verdict") or "").lower()
            print(f"ROUTER: {v.upper()} - {verdict.get('reason','')}")
            for k, label in (("context_requires", "context requires"),
                             ("lsj_lead", "LSJ lead"),
                             ("overread", "over-read")):
                if verdict.get(k):
                    print(f"  {label}: {verdict[k]}")
            engine = "lsj" if (v == "clean" and entry) else "verse"
        else:
            verdict = {}
            engine = "verse" if (args.engine == "lsj" and not entry) else args.engine
            print(f"ENGINE forced -> {engine}")

        if engine == "lsj":
            print("ENGINE: Haiku (LSJ-source)")
            out = model_text(client, MODEL_HAIKU, LSJ_SOURCE_PROMPT, entry[:8000])
            print("definition:\n" + out)
        else:
            print("ENGINE: Sonnet (verse-grounded)")
            if args.verses:
                print(verse_user_msg(sid, translit, gset, ctx))
                print("- - -")
            out = model_text(client, MODEL_SONNET, VERSE_PROMPT, verse_user_msg(sid, translit, gset, ctx))
            print("definition:\n" + out)
            flags = []
            if verdict.get("overread"):
                flags.append("LSJ over-reads: " + verdict["overread"])
            print("PROVENANCE: " + ("; ".join(flags) if flags else "(verse-grounded; mark senses not in LSJ 'attested in usage, not in LSJ')"))

        # FAIRNESS GATE — membership-triggered, model-free: a contested word ALWAYS gets its
        # hand-authored fork appended, regardless of what the definition above said.
        ce = _CONTESTED_BY_SID.get(sid)
        if ce:
            print(render_fork(ce))

    conn.close()


if __name__ == "__main__":
    main()
