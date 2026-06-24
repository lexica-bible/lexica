#!/usr/bin/env python3
"""
trial_lexica_def.py  —  BAKE-OFF for the "Lexica dictionary" idea (throwaway test rig).

For a handful of Greek lemmas it:
  1. pulls the lemma's FULL ABP breadth from bible.db — every rendering with counts
     (the "renders as" set) + every occurrence (LXX Old Testament + Greek New Testament),
  2. picks a SPREAD of verses across the rendering range — NOT top-N. Every distinct
     rendering, including the rare/edge ones, is guaranteed a seat, because that is where
     the sense boundaries show. The dominant gloss is capped so it can't eat the sample.
  3. hands the gloss set + the verses (context = the PRIMARY evidence) to Sonnet with the
     definition prompt below,
  4. prints, per word, side by side:   renders-as  ·  current override  ·  grounded def.

NOT the feature — a test to see what the approach actually produces before we build anything.
Read-only on bible.db. Runs on PA (bible.db + the model key live there).

  workon bible-env
  # key: copy from the WSGI  (grep ANTHROPIC /var/www/www_lexica_bible_wsgi.py)  OR add it to ~/bible-db/.env
  export ANTHROPIC_API_KEY=...
  python scripts/trial_lexica_def.py --dry-run --verses --word G5485   # eyeball the spread, FREE (no model)
  python scripts/trial_lexica_def.py --word G5485                      # one word, real run
  python scripts/trial_lexica_def.py                                   # all 12

Iterating the prompt: edit SYSTEM_PROMPT below and re-run. Nothing else to touch.
"""

import argparse, math, os, sqlite3, sys
from collections import OrderedDict, Counter

# ══════════════════════════════════════════════════════════════════════════════
# THE PROMPT — edit this block, re-run.  (from chat, 2026-06-23)
# ══════════════════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """\
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

MODEL      = "claude-sonnet-4-6"   # Sonnet: discrimination under resistance, not compression
BUDGET     = 40                    # verses fed to the model per word
MAX_TOKENS = 1500

# The dozen: (G-number, transliteration, note). Greek-only this round (Hebrew side next).
WORDS = [
    ("G5484", "charin",     "favor, kindness, + 'for the sake of'   <- the one (ABP tags it G5484, not 5485)"),
    ("G4151", "pneuma",     "spirit / breath / ghost"),
    ("G3056", "logos",      "word / account / reason"),
    ("G1577", "ekklesia",   "assembly / church (LSJ classical blind spot)"),
    ("G907",  "baptizo",    "immerse / baptize"),
    ("G3009", "leitourgia", "service / ministry"),
    ("G166",  "aionios",    "eternal / age-long  (override pending)"),
    ("G1344", "dikaioo",    "justify / make righteous  (held)"),
    ("G4102", "pistis",     "faith / trust"),
    ("G5590", "psyche",     "soul / life"),
    ("G4561", "sarx",       "flesh"),
    ("G740",  "artos",      "bread  (easy control)"),
]

# Current hand-written overrides (verbatim from views_lsj.py _LSJ_OVERRIDES), by G-number,
# for the side-by-side. Words not listed have no override today.
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


def table_exists(conn, name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (name,)).fetchone() is not None


def abp_filter(conn, sid):
    """WHERE predicate (sql, params) for a clean base G-number, mirroring
    views_lexicon._abp_strongs_filter: exclude dotted different-words parked under the base."""
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
    """Light row per occurrence (no prose yet) so sampling doesn't haul thousands of verse texts."""
    return conn.execute(f"""
        SELECT v.book AS book, v.chapter AS ch, v.verse AS vs,
               w.english_head AS rend, w.verse_id AS vid, w.position AS pos
        FROM verses v JOIN words w ON w.verse_id = v.id
        WHERE {pred}
        ORDER BY v.id, w.position
    """, params).fetchall()


def select_spread(occs, budget):
    """Pick a sample that surfaces the word's SENSE range, not just its commonest use:
      - every rendering gets a floor of seats (distinct senses + rare/edge uses represented),
      - the rest is filled proportionally to frequency (the dominant sense gets due weight),
      - within a rendering, verses spread across TESTAMENT first then book, so a sense that
        hides inside the dominant rendering across OT/NT (charis = "favor" in both, the relational
        OT favor vs the NT divine favor) isn't squeezed out by book-spread alone."""
    groups = OrderedDict()
    for o in occs:
        groups.setdefault((o["rend"] or "").lower(), []).append(o)
    by_freq = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    n = len(by_freq)
    if n == 0:
        return []
    counts = {rend: len(g) for rend, g in by_freq}
    used_t = Counter()        # testament (OT/NT) usage
    used_b = Counter()        # book usage
    taken_ids = set()
    taken = Counter()
    selected = []

    def tm(o):
        return "NT" if o["book"] in NT_BOOKS else "OT"

    def pick(g):
        rem = [o for o in g if id(o) not in taken_ids]
        if not rem:
            return None
        return min(rem, key=lambda o: (used_t[tm(o)], used_b[o["book"]]))  # balance testament, then book

    def add(rend, o):
        taken_ids.add(id(o)); taken[rend] += 1
        used_t[tm(o)] += 1; used_b[o["book"]] += 1; selected.append(o)

    if n > budget:
        # more renderings than seats: interleave rarest+commonest so the edges still get in, 1 each
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

    # proportional fill of the remainder (dominant rendering gets due weight, testament-balanced)
    while len(selected) < budget:
        cand = [(rend, g) for rend, g in by_freq if taken[rend] < counts[rend]]
        if not cand:
            break
        rend, g = max(cand, key=lambda rg: counts[rg[0]] / (taken[rg[0]] + 1))
        o = pick(g)
        if o is None:
            counts[rend] = taken[rend]   # exhausted; stop reconsidering it
            continue
        add(rend, o)
    return sorted(selected, key=lambda o: o["vid"])


def fetch_context(conn, occs, has_surface):
    """Pull verse prose (+ the inflected form when abp_surface has it) for the chosen occs."""
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


def build_user_msg(sid, translit, gset, ctx):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"))
    ap.add_argument("--word", help="run a single G-number, e.g. G5485")
    ap.add_argument("--dry-run", action="store_true", help="show what we'd feed; NO model calls (free)")
    ap.add_argument("--verses", action="store_true", help="also print the fed occurrences")
    ap.add_argument("--budget", type=int, default=BUDGET)
    args = ap.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    has_surface = table_exists(conn, "abp_surface")

    client = None
    if not args.dry_run:
        import anthropic
        client = anthropic.Anthropic(api_key=get_key())

    if args.word:
        target = args.word.upper()
        if target[:1] not in ("G", "H"):
            target = "G" + target          # allow a bare number, e.g. --word 5484
        match = [w for w in WORDS if w[0].upper() == target]
        words = match if match else [(target, "?", "ad-hoc")]
    else:
        words = WORDS

    for sid, translit, note in words:
        pred, params = abp_filter(conn, sid)
        gset = gloss_set(conn, pred, params)
        occs = occurrences(conn, pred, params)
        sample = select_spread(occs, args.budget)
        ctx = fetch_context(conn, sample, has_surface)
        ot = sum(1 for c in ctx if c[0] not in NT_BOOKS)
        nt = len(ctx) - ot

        print("\n" + "=" * 78)
        print(f"{sid}  {translit}  ({note})")
        print(f"occurrences: {len(occs)} total | {len(gset)} renderings | fed {len(ctx)}  ({ot} OT / {nt} NT)")
        print("renders as: " + ", ".join(f"{g} {c}" for g, c in gset[:12]) + (" ..." if len(gset) > 12 else ""))
        print("-" * 78)
        ov = OVERRIDES.get(sid)
        print("current override: " + (ov if ov else "(none today)"))
        print("-" * 78)
        user_msg = build_user_msg(sid, translit, gset, ctx)
        if args.verses:
            print(user_msg)
            print("-" * 78)
        if args.dry_run:
            print("grounded (Sonnet): [dry run - not called]")
            continue
        msg = client.messages.create(
            model=MODEL, max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        out = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        print("grounded (Sonnet):\n" + out.strip())

    conn.close()


if __name__ == "__main__":
    main()
