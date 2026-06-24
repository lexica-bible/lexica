#!/usr/bin/env python3
"""
trial_lexica_def.py  —  BAKE-OFF for the "Lexica dictionary" idea (throwaway test rig).

DIVERGENCE-ROUTED design (per chat review, 2026-06-23):

  For each Greek lemma, a ROUTER picks the engine (chat design, 2026-06-23):
    - LSJ entry MISSING or LONG (multi-sense, where classical freight hides) -> verse-grounded
      def (Sonnet), with NO routing model call. (psyche's 13k-char entry lands here.)
    - SHORT LSJ entry -> a Sonnet "bears-out" check: does the biblical usage actually carry
      LSJ's senses, and is LSJ's LEAD sense used?
        clean     -> LSJ-as-source def (Haiku)   (bread: short entry, usage = LSJ)
        divergent -> verse-grounded def (Sonnet) + provenance flag
  Verse-grounded senses get a PROVENANCE flag ("attested in usage, not in LSJ"); never
  silently merged into LSJ's list.

  No BDAG / NT lexicon (it bakes the theology call into the lexeme). Hebrew is out -
  Greek defined from Greek.

  Calibrate the long/short cutoff cheaply: `--dry-run` prints each word's entry length and
  which branch it takes, no model calls. Set --long from that before spending on a full run.

Throwaway. Read-only on bible.db. Runs on PA (bible.db + the model key live there).

  workon bible-env
  export ANTHROPIC_API_KEY=$(grep -oE "sk-ant-[A-Za-z0-9_-]+" /var/www/www_lexica_bible_wsgi.py)
  python scripts/trial_lexica_def.py --dry-run --verses --word G5590   # inspect inputs, FREE (no model)
  python scripts/trial_lexica_def.py --word G5590                      # one word: route + define
  python scripts/trial_lexica_def.py                                   # the whole set, in sequence

Iterating prompts: edit the three blocks below (BEARS_OUT_PROMPT / LSJ_SOURCE_PROMPT /
VERSE_PROMPT) and re-run. Nothing else to touch.
"""

import argparse, html, json, os, re, sqlite3, sys, unicodedata
from collections import OrderedDict, Counter

# ══════════════════════════════════════════════════════════════════════════════
# PROMPT 1 — THE ROUTER's verse-bears-out check (Sonnet). Runs ONLY on SHORT entries;
# long / missing entries skip it and go straight to verse-grounding.
# ══════════════════════════════════════════════════════════════════════════════
BEARS_OUT_PROMPT = """\
You decide whether a Greek word's BIBLICAL USAGE matches its classical dictionary entry, or has
diverged from it.

You are given:
- the word's full LSJ entry
- a sample of occurrences from the Greek Bible: each a verse with the word's rendering marked

Work from the occurrences, not from outside knowledge of the word.

Check two things:
1. Does the usage carry a sense the LSJ entry does NOT have? (the word gained a sense)
2. Does the LSJ entry LEAD with a sense (its first / primary sense) that the usage does NOT
   bear out? (the word was repurposed - a calque)

LSJ carrying extra MINOR senses the Bible simply doesn't use is NOT divergence - a concrete word
naturally uses only part of its range. Flag an unused LSJ sense only when it is the entry's
PRIMARY / leading sense.

Return JSON only, nothing else:
{"verdict": "clean" | "divergent",
 "lsj_lead_not_used": ["short sense", ...],
 "uses_not_in_lsj": ["short description", ...],
 "reason": "one sentence"}

Use "clean" only when the usage sits within the entry's senses AND the entry's lead sense is
used. Otherwise "divergent".
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


def model_text(client, model, system, user, max_tokens=MAX_TOKENS):
    msg = client.messages.create(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def route(client, entry, long_threshold, verse_msg):
    """Length pre-filter + verse-bears-out check:
       - no entry / LONG entry  -> divergent (verse-ground), no model call
       - SHORT entry            -> Sonnet bears-out check decides."""
    if not entry:
        return {"verdict": "divergent", "reason": "no LSJ entry - verse-ground by default"}
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
    args = ap.parse_args()

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
            elif len(entry) >= args.long:
                lr = f"VERSE (long entry, {len(entry)} >= {args.long})"
            else:
                lr = f"SHORT ({len(entry)} chars) -> bears-out check would decide"
            print(f"length-route: {lr}")
            if args.verses:
                print(verse_user_msg(sid, translit, gset, ctx))
                print("-" * 78)
            print("[dry run - model calls skipped]")
            continue

        if args.engine == "auto":
            vmsg = verse_user_msg(sid, translit, gset, ctx)
            verdict = route(client, entry, args.long, vmsg)
            v = (verdict.get("verdict") or "").lower()
            print(f"ROUTER: {v.upper()} - {verdict.get('reason','')}")
            for k, label in (("lsj_lead_not_used", "LSJ lead sense not used"),
                             ("uses_not_in_lsj", "uses not in LSJ")):
                if verdict.get(k):
                    print(f"  {label}: " + ", ".join(verdict[k]))
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
            if verdict.get("uses_not_in_lsj"):
                flags.append("uses not in LSJ: " + ", ".join(verdict["uses_not_in_lsj"]))
            if verdict.get("lsj_lead_not_used"):
                flags.append("LSJ lead sense abandoned: " + ", ".join(verdict["lsj_lead_not_used"]))
            print("PROVENANCE: " + ("; ".join(flags) if flags else "(verse-grounded; mark senses not in LSJ 'attested in usage, not in LSJ')"))

    conn.close()


if __name__ == "__main__":
    main()
