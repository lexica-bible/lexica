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
SPLIT_VER    = "split2"              # which split_definition() wrote a row (stored for traceability; NOT in the skip-stamp)

# ── PROMPT — VERSE-GROUNDED definition (Sonnet). VERBATIM from the trial rig. FROZEN. ────────
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

NT_BOOKS = {"Mat","Mar","Luk","Joh","Act","Rom","1Co","2Co","Gal","Eph","Php","Col",
            "1Th","2Th","1Ti","2Ti","Tit","Phm","Heb","Jas","1Pe","2Pe","1Jn","2Jn","3Jn","Jud","Rev"}

# ── THE CONTESTED-WORD FAIRNESS GATE — the hand-authored fork register. VERBATIM from the trial
# rig (chat design 2026-06-24). Membership alone triggers it; no model, no detector. Stored as a
# structured field so the card draws it natively and graph_ref deep-links into the Study graph.
# DATA: charis is tagged G5484 in ABP (not the textbook G5485 stub) — keyed under G5484 + alias.
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
        "graph_ref": "salvation_how:def_dikaioo_forensic|def_dikaioo_infused|def_dikaioo_demonstrate",
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
        "aliases": ["G5485"],
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
_CONTESTED_BY_SID = {}
for _sid, _e in CONTESTED.items():
    _CONTESTED_BY_SID[_sid] = _e
    for _a in _e.get("aliases", []):
        _CONTESTED_BY_SID[_a] = _e


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


# A verse ref as the engine emits it. Numbered book = digit+Cap+lower (1Jn); unnumbered = Cap+2-lower.
_REF_RE = re.compile(r"\b(\d[A-Z][a-z]|[A-Z][a-z]{2})\s+(\d+):(\d+)")


def cited_refs(text):
    """Pull verse refs (book, ch, vs) out of generated prose — de-duped, in order."""
    seen, out = set(), []
    for bk, ch, vs in _REF_RE.findall(text or ""):
        key = (bk, int(ch), int(vs))
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


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
    headlines = [re.sub(r'^\d+\.\s*', '', h).strip()
                 for h in _HEADLINE_RE.findall(senses_block)]
    return {
        "sense_headlines": headlines,
        "senses_block":    senses_block,
        "range":           body("range"),
        "gloss_notes":     body("gloss notes"),
        "coverage":        body("coverage"),
    }


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
    }
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


def assemble(conn, sid, lemma, translit, raw):
    """raw model prose -> the full stored entry (the frozen field shape)."""
    fields = split_definition(raw)
    refs = cited_refs(raw)
    entry = {
        "strongs":  sid,
        "lemma":    lemma,
        "translit": translit,
        **fields,
        "fork":       fork_field(sid),
        "verses":     build_verses(conn, refs),
        "provenance": "verse-grounded · LEXICA",
        "split_ver":  SPLIT_VER,
        "audit":      run_citation_gate(conn, sid, refs),
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


def model_prose(client, sid, translit, gset, ctx):
    msg = client.messages.create(
        model=MODEL_SONNET, max_tokens=MAX_TOKENS, system=VERSE_PROMPT,
        messages=[{"role": "user", "content": verse_user_msg(sid, translit, gset, ctx)}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def show_entry(entry):
    """Print the assembled fields so a human can eyeball the split before --apply writes."""
    a = entry["audit"]
    print(f"\n  lemma: {entry['lemma']}  ({entry['translit']})   stamp {entry.get('synth_ver','')}")
    print(f"  sense_headlines ({len(entry['sense_headlines'])}) — the glance list:")
    for i, h in enumerate(entry["sense_headlines"], 1):
        print(f"     {i}. {h}")
    print(f"  senses_block: {len(entry['senses_block'])} chars (full prose, kept verbatim)")
    print(f"  range:       {entry['range'] or '(empty)'}")
    print(f"  gloss_notes: {(entry['gloss_notes'][:400] + ' …') if len(entry['gloss_notes'])>400 else (entry['gloss_notes'] or '(empty)')}")
    print(f"  coverage:    {entry['coverage'] or '(empty/adequate)'}")
    print(f"  verses:      {len(entry['verses'])} cited, with text")
    print(f"  citation gate: {a['pass']}/{a['total']} pass" +
          (f"  (misses — tagging {a['tagging']} / real {a['real']} / no-verse {a['noverse']})" if a['total']-a['pass'] else ""))
    if entry["fork"]:
        f = entry["fork"]
        print(f"  FORK (contested): core = {f['core']}")
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
    ap.add_argument("--force", action="store_true", help="rebuild even if the stamp matches")
    ap.add_argument("--budget", type=int, default=BUDGET)
    args = ap.parse_args()

    if not args.dry_run and not args.apply:
        sys.exit("Pass --dry-run (show, no write) or --apply (write).")

    targets = [args.word.upper()] if args.word else list(PILOT)
    targets = [("G" + t if t[:1] not in ("G", "H") else t) for t in targets]

    # read-write (we create + write ONLY lexica_def); the evidence reads are on the same handle
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    conn.create_function("strip_accents", 1, strip_accents)
    if args.apply:
        ensure_table(conn)
    has_surface = table_exists(conn, "abp_surface")
    stamp = synth_ver()

    client = None
    if not args.resplit:
        import anthropic
        client = anthropic.Anthropic(api_key=get_key())

    failures = []
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
            if existing and existing["synth_ver"] == stamp and not args.force:
                print(f"  up to date (stamp {stamp}); skip. (--force to rebuild)")
                continue
            pred, params = abp_filter(conn, sid)
            gset = gloss_set(conn, pred, params)
            occs = occurrences(conn, pred, params)
            if not occs:
                print(f"  no occurrences for {sid} — skip.")
                continue
            sample = select_spread(occs, args.budget)
            ctx = fetch_context(conn, sample, has_surface)
            lemma, translit = lex_head(conn, sid)
            ot = sum(1 for c in ctx if c[0] not in NT_BOOKS)
            print(f"  occurrences {len(occs)} | {len(gset)} renderings | fed {len(ctx)} ({ot} OT / {len(ctx)-ot} NT)")
            print("  calling the verse engine (Sonnet)…")
            raw = model_prose(client, sid, translit, gset, ctx)

        entry = assemble(conn, sid, lemma, translit, raw)
        entry["synth_ver"] = stamp
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
                 datetime.datetime.utcnow().isoformat(timespec="seconds")))
            conn.commit()
            print("  → written to lexica_def.")
        else:
            print("  [dry run — not written]")

    conn.close()
    if failures:
        sys.exit(f"\n{len(failures)} word(s) FAILED to parse and were NOT written: "
                 f"{', '.join(failures)}  (fix the splitter, then re-run --resplit --apply)")


if __name__ == "__main__":
    main()
