#!/usr/bin/env python3
"""
group_news.py — let the AI (MODEL, below) group the scored articles by the real-world EVENT.

Word-matching can't tell that "Pope Leo urges AI disarmament", "Magnifica Humanitas
discussion", and "42,000-word letter on AI" are the SAME encyclical — they share no
distinctive words. So here the AI reads the headlines together and tags each with a
short canonical event label. The tab then collapses everything sharing a label into
ONE card. The AI sees the running list of labels it's already used, so the same event
gets the same label across batches (that's what keeps it consistent).

Re-runnable: only fills articles that don't have an event yet, so a nightly run just
labels whatever the last gather/score added. Pairs with gather_news + score_news.

USAGE
  python3 scripts/news/group_news.py              # label scored, unlabeled articles
  python3 scripts/news/group_news.py --min 5      # only score >=5 (default; saves cost)
  python3 scripts/news/group_news.py --batch 40   # headlines per AI call (default 40)
  python3 scripts/news/group_news.py --dry-run    # show labels, save nothing
  python3 scripts/news/group_news.py --regroup    # redo ALL (after a prompt change)

The key comes from ~/bible-db/.env (same as score_news.py).
"""
import os
import re
import sys
import json
import time
import sqlite3
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB = os.path.join(REPO_ROOT, "news.db")


def _load_env_file(path):
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip(); v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass


_load_env_file(os.path.join(REPO_ROOT, ".env"))

DRY_RUN = "--dry-run" in sys.argv
REGROUP = "--regroup" in sys.argv


def _arg(flag, default, cast=str):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
            return cast(sys.argv[i + 1])
    return default


MIN = _arg("--min", 5, int)
BATCH = _arg("--batch", 40, int)
DB_PATH = _arg("--db", DEFAULT_DB)
# THE labeler model — the one place to change it (nightly, --regroup and relabel_check.py all
# read it). The request settings follow from it in _call_settings, so a switch is this one line.
# 2026-10-29/30: Sonnet ("claude-sonnet-5-5") was tried for cross-night attempt 1b and FAILED the
# live check (numbers at NIGHTLY_SEED below); back on Haiku, the measured nightly baseline.
MODEL = "claude-haiku-4-5-20251001"
# The REUSE CHECK's model (confirm_reuse, below) — separate on purpose (attempt 5, 2026-10-30):
# Haiku's yes/no failed live both ways, so the check runs on Sonnet while the labeler stays on
# Haiku. Only used when NIGHTLY_SEED is on. Settings follow from _call_settings like MODEL's.
CHECK_MODEL = "claude-sonnet-5-5"


def _call_settings(model):
    """Request settings for the labeler model.
    Haiku 4.5: exactly the old call (temperature 0, max_tokens 1600).
    Anything newer (Sonnet 5.5): temperature 0 is refused by the API there (only the default is
    accepted), so it samples at the default — two runs can differ slightly. It thinks before
    answering, effort "medium": the failure being measured is a judgment call (same happening vs
    same theme). Thinking counts toward max_tokens, so the cap leaves room for it + the reply."""
    if model.startswith("claude-haiku-4-5"):
        return {"max_tokens": 1600, "temperature": 0}
    return {"max_tokens": 16000, "output_config": {"effort": "medium"}}

SYSTEM = """You group news headlines by the real-world EVENT each one is about, so that
duplicate coverage of one event collapses into a single item.

Rules:
- Headlines about the SAME event get the SAME label — even when worded completely
  differently (e.g. "Pope Leo urges AI disarmament", "Magnifica Humanitas discussion",
  and "Pope's 42,000-word letter on AI" are all the same encyclical → one label).
- An EVENT is ONE specific happening — a particular bill, lawsuit, report, ruling,
  meeting, document, or announcement, with its own who / what / where. A broad THEME
  ("Sunday laws", "ecumenism", "AI ethics") is NOT an event.
- SPLIT by happening: same-theme headlines about DIFFERENT happenings get DIFFERENT
  labels. Poland's Sunday trading ban, a New Jersey mall Sunday lawsuit, and a New
  York Chick-fil-A Sunday bill are THREE events, never one "Sunday Laws" label; a WCC
  visit, King Charles praying with the Pope, and the 1054 anathema being lifted are
  THREE events, never one "Ecumenical Outreach" label.
- MERGE by phase: a single happening keeps ONE label across every phase of its own
  life — its announcement, launch, release, the reporting on its contents, reactions,
  hearings, votes, rulings, delays, and follow-ups. A launch or release is NOT a
  separate event from the thing being launched. So the encyclical's CONTENTS coverage
  and its LAUNCH coverage are ONE label, not two; and every phase of the New Jersey
  American Dream / Paramus Sunday-trading lawsuit (filing, opening, hearing, ruling
  delay, deadline) is ONE label, not one per court date.
- MERGE by outlet: same-happening coverage is ONE label no matter how many outlets
  carry it — a 130- or 400-outlet event is still one label. Many outlets is NOT a
  reason to split.
- REUSE an existing label (you'll be given the ones already in use) whenever a headline
  is about that SAME happening — including a NEW PHASE of it — not merely the same
  theme. Only invent a new label when the headline is a genuinely different happening.
- NEVER label with a THEME or CATEGORY. A label that ends in an abstract noun — e.g.
  "...Phenomena", "...Movement", "...Growth", "...Decline", "...Legacy", "...Concerns",
  "...Analysis", "...Dialogue", "...Work", "...Trend", "...Crisis", "...Outreach" — names a
  topic, not a happening, and is FORBIDDEN. Banning the suffix is not enough: every label
  MUST positively pin the ONE happening by its distinctive WHERE (place/object/institution)
  and WHO/WHAT, and — whenever this kind of event recurs across time — its WHEN (year). If two
  headlines describe the same THEME at a different place, object, or year, they are DIFFERENT
  events and MUST get different labels. A label generic enough to fit a story from another city
  or another year has failed — make it more specific.
    * weeping-icon reports → "Weeping Icon Chicago 2019", "Weeping Icon Homer Glen 2016",
      "Weeping Icon France 2010" as SEPARATE labels — never one "Weeping Icons Phenomena"
      (each city/icon/year is its own event)
    * a parish/diocese conversion story → "St Mary Ohio Parish Converts 2025", NOT "Catholic
      Conversion Growth"
    * a specific theology meeting → "Vatican-Orthodox Nicaea Talks 2025", NOT "Catholic-
      Orthodox Theological Dialogue"
    * a particular AI-ethics statement → name its document/speaker/venue + year, NOT "Vatican
      AI Ethics Concerns".
- A label is SHORT (3-6 words), Title Case, and names the event concretely, e.g.
  "Pope Leo AI Encyclical", "Pentagon-Vatican Meeting Clash", "Trump-Pope Leo Tension".

Return ONLY a JSON array, one object per headline, keys exactly: id, event."""

_FENCE = re.compile(r"^```(?:json)?|```$", re.MULTILINE)


def build_client():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ANTHROPIC_API_KEY not set. Put it in ~/bible-db/.env or export it.")
    import anthropic
    return anthropic.Anthropic(api_key=key)


# ---- which past labels the NIGHTLY run shows the AI (fix for cross-night splits, 2026-10-29) ----
# Before: every run started from an EMPTY list, so a story whose coverage came in over several
# nights got fresh wording each night = several cards (fixture case 3, tests/test_news_clustering.py).
# Showing ALL past labels over-fuses (the 2026-10-29 baseline: 53 other stories joined the
# encyclical's card in one big pass). So the list is BOUNDED, per batch of headlines:
#   1. REACH — only labels with an article published within REACH_DAYS of a headline in the batch.
#      The card code (views_news._group) keeps one label's rows together only across gaps of
#      <= 14 days (WINDOW_DAYS), so reusing a label from further away can't put the headline on
#      the same card — showing it would only add fusion risk. Keyed on PUBLISHED dates, not pull
#      nights: Google re-surfaces old stories (one Dec-2023 bill was pulled on 11 nights).
#   2. RANK — labels sharing words with the batch's headlines first (label + its best headlines,
#      2+ shared significant words per headline), then the most recent, then the biggest.
#   3. CAP — at most SEED_MAX labels, each shown with one headline it was given to, so the AI
#      judges "same happening?" by content, not by how close the label's wording sounds.
# --regroup is unchanged: it starts empty and shows every label made in that run (one pass).
#   4. REUSE CHECK (attempt 4, 2026-10-30) — when ON, every reuse of an earlier night's label is
#      confirmed by a second call (check_reuse / confirm_reuse, below); a "no" gets a fresh label.
#
# STATUS: ON since 2026-10-31 (attempt 7 — see the switch below; rollback = ~/news_seed_off).
# History of the attempts, oldest last:
# Attempt 5 (2026-10-30) = attempt 4 with the reuse check on CHECK_MODEL (Sonnet),
# labeler still Haiku. Its bar (JP): only fusions THROUGH a reused earlier-night label are
# scored — 0 of them — same-night fusions reported apart (relabel_check.py, TODO.md). FAILED live
# twice: run 1 encyclical 1, Sunday 2 (11 checks lost to a reply-reading bug, since fixed —
# _read_array); rerun encyclical 0, Sunday 3. Merge/split/cross-night met the bar both times. The
# misses are mostly next-event pairs (same theme, a new statement days later) — the floor here.
# Attempt 6 (2026-10-30): same design, the check's prompt hardened (SYSTEM_CONFIRM: later-vs-
# reaction rule, CONFIRM_EXAMPLES, a reason before each answer). FAILED live (encyclical 1,
# Sunday 2 through reuse) but no next-event pair fused and the held-out Alliance pair held; the
# misses are 2 judgment edges + 1 different event naming the earlier one (TODO.md).
# Attempt 7 (2026-10-31): + the new-event-naming-the-old rule and its example (8967); measured
# over 3 live runs for run-to-run variance.
# Attempt 4 (list + reuse check, all Haiku) passed the replay incl. the 12 live-fused theme rows
# but FAILED the live check (`relabel_check.py --run --list-on`, Haiku): encyclical 421/623 with 16
# other stories (bar <=13), Sunday 6 fused cards (bar <=1) — the Haiku yes/no approved next-event
# pairs and turned down real encyclical coverage (TODO.md). Earlier, the list ALONE failed too:
#   Haiku (2026-10-29): fixed the splitting (encyclical 511/623 on one card vs 341, Sunday splits
#     13 -> 1) but reused shown labels for DIFFERENT happenings of the same theme — 23 other stories
#     on the encyclical card (was 13), Sunday 8 fused cards (was 1).
#   Sonnet (2026-10-30, attempt 1b): better both ways but still fuses — encyclical 578/623, 14
#     other stories (was 13), Sunday 5 fused cards (was 1), Sunday splits 1, cross-night clean.
#   (Attempt 2, a distinctive-words match, was stopped in the replay — TODO_ARCHIVE.)
# With it off the nightly run is exactly the old behavior (labels made earlier the same night only).
# SHIPPED ON 2026-10-31 after attempt 7's 3 live runs (no next-event or clear-miss fusion in any
# run, with the rulings recorded in TODO_ARCHIVE). ROLLBACK without a code or data change: create
# the file ~/news_seed_off (`touch ~/news_seed_off`) — the next nightly runs the old way (labels
# made the same night only, no reuse check); delete it to turn the list back on. Labels already
# written while ON stay as they are.
SEED_OFF_FILE = os.path.expanduser("~/news_seed_off")
NIGHTLY_SEED = not os.path.exists(SEED_OFF_FILE)
# one line per real nightly run (live news.db only — never a test or check db): reuse drift
REUSE_LOG = os.path.expanduser("~/news_reuse.log")
REACH_DAYS = 14          # KEEP IN SYNC with views_news.WINDOW_DAYS
SEED_MAX = 40            # labels shown per call: room for one best match per headline of a
                         # default 40-headline batch (295 unbounded was the over-fusing case)
LOOSE_MAX = 10           # of those, at most this many weak matches (< 2 shared words)
_HEADS_PER_LABEL = 3     # headlines per label used for the word match (best-scored)

_STOP = set((
    "the a an of to in on for and or with at by from as is are was were be been "
    "his her its their our your s it that this these those new over amid into "
    "after before about out up down off than then but not no will would can could"
).split())


def _tokens(text):
    """Significant words of a headline or label (drops a trailing ' - Outlet')."""
    t = re.sub(r"\s+-\s+[^-]+$", "", (text or "").lower())
    return {w for w in re.findall(r"[a-z0-9]+", t) if len(w) >= 3 and w not in _STOP}


def _day(published):
    try:
        return datetime.date.fromisoformat((published or "")[:10]).toordinal()
    except ValueError:
        return None


def pool_add(pool, label, title, published, score, rid=None):
    """Remember one labeled article under its label (in memory, for picking what to show).
    heads = its best-scored (score, title, published, id): the example shown with the label and
    the stored headlines the reuse check (confirm_reuse) compares a new headline against."""
    p = pool.setdefault(label, {"days": [], "heads": [], "n": 0})
    d = _day(published)
    if d is not None:
        p["days"].append(d)
    p["heads"].append(((score or 0), title or "", published or "", rid))
    p["heads"].sort(key=lambda h: -h[0])
    del p["heads"][_HEADS_PER_LABEL:]
    p["n"] += 1
    p.pop("toks", None)


def load_pool(conn):
    """Every labeled article already in the db, grouped by label."""
    pool = {}
    for r in conn.execute("SELECT event, title, published, score, id FROM items "
                          "WHERE event IS NOT NULL AND event != ''"):
        pool_add(pool, r[0], r[1], r[2], r[3], r[4])
    return pool


def pick_known(pool, batch, cap=SEED_MAX, days=REACH_DAYS):
    """The bounded list of past labels to show for this batch -> (labels, {label: example headline}).
    Matched PER HEADLINE, so a label one headline needs can't be crowded out by labels that suit
    many: (1) every headline's single best match (most shared words, 2+), strongest first; (2) the
    other 2+-word matches, strongest first; (3) only if room is left, labels in reach that share
    fewer words, most recent first — a same-story headline can be worded completely differently.
    A label counts for a headline only if one of its articles is within `days` of THAT headline."""
    heads = []
    for r in batch:
        d = _day(r["published"])
        if d is not None:                # undated headlines each get their own card anyway
            heads.append((d, _tokens(r["title"])))
    if not heads:
        return [], {}
    lo, hi = min(d for d, _ in heads) - days, max(d for d, _ in heads) + days
    best, other, loose = [], [], {}
    for label, p in pool.items():
        near = [d for d in p["days"] if lo <= d <= hi]
        if not near:
            continue
        if "toks" not in p:
            p["toks"] = _tokens(label).union(*(_tokens(h[1]) for h in p["heads"]))
        last = max(p["days"])
        for hi_, (hd, ht) in enumerate(heads):
            if not any(abs(d - hd) <= days for d in near):
                continue
            s = len(ht & p["toks"])
            if s >= 2:
                other.append((s, last, p["n"], label, hi_))
            else:
                loose[label] = max(loose.get(label, (0, 0)), (last, p["n"]))
    other.sort(key=lambda c: (-c[0], -c[1], -c[2], c[3]))
    seen_head = set()
    for c in other:                      # (1) each headline's best match
        if c[4] not in seen_head:
            seen_head.add(c[4])
            best.append(c[3])
    shown = []
    for label in best + [c[3] for c in other]:
        if len(shown) >= cap:
            break
        if label not in shown:
            shown.append(label)
    weak = 0
    for label, _ in sorted(loose.items(), key=lambda kv: (-kv[1][0], -kv[1][1], kv[0])):
        if len(shown) >= cap or weak >= LOOSE_MAX:
            break
        if label not in shown:
            shown.append(label)
            weak += 1
    return shown, {k: pool[k]["heads"][0][1] for k in shown}


def _ask(client, system, user, model=None):
    """One call on `model` (default MODEL) -> the JSON array it returns. A refusal or a cut-off
    reply raises (loud, never half-read: the caller prints ERR)."""
    model = model or MODEL
    msg = client.messages.create(
        model=model, system=system, messages=[{"role": "user", "content": user}],
        **_call_settings(model),
    )
    if msg.stop_reason in ("refusal", "max_tokens"):
        raise RuntimeError(f"{model} stopped early ({msg.stop_reason})")
    # read the reply by block type: a thinking model's reply starts with a (thinking) block
    text = "".join(b.text for b in (msg.content or []) if b.type == "text").strip() or "[]"
    return _read_array(_FENCE.sub("", text).strip())


def _read_array(text):
    """The JSON array in a reply. A note the model writes after it is ignored; a reply holding TWO
    arrays raises (two answers — never pick one); no array at all -> [].
    Fixed 2026-10-30: the old fallback grabbed from the first '[' to the LAST ']', so any ']' in
    a trailing note broke the read ("Extra data") — 11 Sonnet reuse checks in the attempt-5 live
    run were lost that way and counted as no."""
    try:
        return json.loads(text)
    except ValueError:
        pass
    dec, found = json.JSONDecoder(), []
    i = text.find("[")
    while i >= 0:
        try:
            data, end = dec.raw_decode(text, i)
        except ValueError:
            i = text.find("[", i + 1)
            continue
        if isinstance(data, list):
            found.append(data)
        i = text.find("[", end)
    if len(found) > 1:
        raise ValueError(f"reply holds {len(found)} answers")
    return found[0] if found else []


def label_batch(client, rows, known, examples=None, avoid=None):
    """avoid = labels the reuse check just turned down for these headlines (the nightly's
    fresh-label call only); without it the request is exactly the old one."""
    if known and examples:
        known_txt = "\n".join(f'  - {k}   (e.g. "{examples.get(k, "")[:90]}")' for k in known)
        head = "Existing labels already in use (each with one headline it was given to):\n"
    else:
        known_txt = ("\n".join(f"  - {k}" for k in known)) if known else "  (none yet)"
        head = "Existing labels already in use:\n"
    if avoid:
        known_txt += ("\n\nThese labels were checked against these headlines and name a "
                      "DIFFERENT happening — do NOT use them:\n" +
                      "\n".join(f"  - {k}" for k in avoid))
    lines = [f'id={r["id"]} | {r["title"]}' for r in rows]
    user = (head + known_txt +
            "\n\nGroup these headlines. Reuse a label above when it fits.\n\n" +
            "\n".join(lines))
    data = _ask(client, SYSTEM, user)
    out = {}
    for d in data:
        try:
            vid = int(d["id"])
        except Exception:
            continue
        ev = (d.get("event") or "").strip()[:80]
        if ev:
            out[vid] = ev
    return out


# ---- the reuse check (cross-night attempt 4, 2026-10-30) ----
# What failed live three times: shown a past label, the labeler reuses it for the NEXT happening of
# the same theme (two Dr. O episodes; a union's fine proposal, then its enforcement campaign). So
# every time a nightly run puts a headline on a label from an EARLIER run, a second, narrow call
# asks only that: same happening, or a different one on the same theme? Shown: the label's best
# stored headlines WITH publish dates (the Dr. O episodes have word-for-word the same headline —
# only the dates tell them apart). "yes" -> the reuse stands; "no" (or no answer, or a failed
# call) -> the headline gets a fresh label the way the nightly always did (fresh_labels).
# One call per reused label per batch, covering every headline in the batch that took it, each
# answered on its own; on CHECK_MODEL (Sonnet since attempt 5 — attempt 4 ran it on the labeler's
# Haiku and it failed live both ways).
# Attempt 6 (2026-10-30): the prompt asks "same announcement or event", states that a LATER
# statement / follow-up action / new document by the same or another actor is DIFFERENT and that
# coverage + reactions are SAME, carries worked examples (CONFIRM_EXAMPLES), and asks for one short
# reason before each answer. What it kept failing on: next-event pairs on Sunday.
#
# CONFIRM_EXAMPLES — real judged rows from tests/fixtures/news_clustering (expected.json):
# (earlier id, earlier headline, its date, new id, new headline, its date, SAME?, why).
# THEY OVERLAP THE SCORED SAMPLES on purpose (JP's brief, 2026-10-30): a pass on these rows is
# weaker evidence than a pass on rows NOT here. Held out ON PURPOSE: the Alliance pair (27299
# manifesto onto 24079 demand, the miss in both attempt-5 runs) and the 17040/17505 edge — the
# clean test of whether the rule, not the examples, is what the check learned.
CONFIRM_EXAMPLES = (
    (13476, "Labor Unions and Churches Vow to Fight to Keep Sunday Work-Free", "2026-08-03",
     14621, "Pope Leo XIV: Attendance at Sunday Mass cannot be replaced by virtual participation",
     "2026-08-13", False,
     "the pope's own new statement days later; it does not report or respond to the unions' vow"),
    (24082, "Sunday Law Update with Dr. O", "2026-10-03",
     24909, "Sunday Law Update with Dr. O", "2026-10-09", False,
     "same show, same title, a new episode six days later"),
    (16144, "Polish Trade Union Calls for a $1 Million Złoty Fine (US$271,172) and a 15-Year Ban "
            "for Businesses that Operate on Sunday", "2026-08-21",
     19923, "Trade Unions Launch Nationwide Enforcement Campaign to Report Businesses Violating "
            "Sunday Closing Laws", "2026-09-04", False,
     "a follow-up action (a campaign), not coverage of the fine proposal"),
    (10368, "Roman Catholics Renew the Call for Legally Protected Sunday Rest", "2026-07-14",
     12472, "Militant Nationwide Strike in Greece Calls for Legal Protection of Sunday as the Day "
            "of Rest", "2026-07-27", False,
     "another actor in another place, its own action on the same theme"),
    (2718, "Pope Leo XIV signs his first encyclical, responds to the AI era", "2026-05-25",
     17143, "Pope Leo XIV warns against entrusting human-life decisions to machines", "2026-08-28",
     False, "a new message by the same pope three months later, not the encyclical"),
    # attempt 7 (2026-10-31): the new-event-naming-the-old miss of attempt 6 (8967, live)
    (2718, "Pope Leo XIV signs his first encyclical, responds to the AI era", "2026-05-25",
     8967, "Brown: The encyclical “Magnifica Hūmānitās” crystalizes Pope Leo XIV as the 2026 "
           "awardee of the Liberty Medal on July 3rd at The National Constitution Center",
     "2026-07-06", False,
     "the news is a new event (an award ceremony); the encyclical is only named as the reason"),
    (14756, "Pope Leo XIV Calls for Sunday to be Sanctified and Urges Workers to Attend Mass on "
            "that Day", "2026-08-13",
     15419, "Pope Leo’s Call to Sanctify Sunday is Stirring Catholic Labor Unions in Europe to "
            "Secure “Material Conditions” for Sunday Rest", "2026-08-18", True,
     "the unions' reaction to that very call"),
    (2718, "Pope Leo XIV signs his first encyclical, responds to the AI era", "2026-05-25",
     607, "Anglicans respond to ‘Magnifica Humanitas’, the new encyclical by Pope Leo XIV",
     "2026-06-12", True, "a reaction to the encyclical, weeks later"),
    (2718, "Pope Leo XIV signs his first encyclical, responds to the AI era", "2026-05-25",
     22593, "Peter Thiel slams pope’s AI encyclical as gift to Chinese Communist Party",
     "2026-09-24", True, "a reaction to the encyclical; months later is still the same event"),
)


def _examples_text(examples=CONFIRM_EXAMPLES):
    out = []
    for _, old, od, _, new, nd, same, why in examples:
        out.append(f'Earlier: "{old}" ({od})\nNew:     "{new}" ({nd})\n'
                   f'-> {"SAME" if same else "DIFFERENT"}: {why}')
    return "\n\n".join(out)


SYSTEM_CONFIRM = """You check one grouping decision in a news feed. Each new headline below was
put under an existing event label. For each one, decide: is it about the SAME announcement or
event as the label's earlier headlines, or a DIFFERENT one on the same theme? Every headline
carries its publish date — use the dates.

SAME: coverage of that one announcement or event — the same bill, lawsuit, ruling, document,
report, speech, statement or meeting — including its later phases (its release, reporting on its
contents, hearings, votes, delays), the same article re-published or carried by another outlet,
and REACTIONS to it (people or groups responding to, praising, criticizing or acting on THAT
announcement), even weeks or months later.
DIFFERENT: a LATER statement, a follow-up action, or a NEW document — by the same actor or by
another actor — on the same theme: another speech, message, manifesto, campaign, proposal,
strike, or episode of a recurring show; another place or another year. A headline announcing
its own new statement or action is DIFFERENT unless it is responding to the earlier
announcement. A headline reporting a NEW event — an award, appointment, ruling, anniversary,
ceremony — that mentions the earlier announcement only as background or as the reason for it is
DIFFERENT: it is about the new event. Same people, same topic and close dates are not enough.

Examples:

""" + _examples_text() + """

Return ONLY a JSON array, one object per new headline, keys in this order: id, reason, same.
reason = ONE short line, written before you decide: what the new headline announces, and whether
it is coverage of or a reaction to the earlier announcement. same = true or false."""


def confirm_reuse(client, label, stored, rows):
    """-> {id: True if that headline is the same happening as the label's stored headlines}.
    stored = the label's best-scored (score, title, published, id), as kept by pool_add;
    rows = the new headlines that took the label. An id missing from the reply counts as no.
    The reply's per-headline "reason" (attempt 6) is there to make the model reason first; only
    "same" is read."""
    def when(p):
        return (p or "")[:10] or "date unknown"
    seen = "\n".join(f'  - "{h[1][:120]}" ({when(h[2])})' for h in stored)
    new = "\n".join(f'id={r["id"]} | {r["title"]} ({when(r["published"])})' for r in rows)
    user = (f"Label: {label}\nIts earlier headlines:\n{seen}\n\n"
            f"New headlines given this label:\n{new}")
    out = {}
    for d in _ask(client, SYSTEM_CONFIRM, user, CHECK_MODEL):
        try:
            out[int(d["id"])] = d.get("same") is True
        except Exception:
            continue
    return out


def check_reuse(client, batch, labels, pool, earlier):
    """Run the reuse check on one batch's labels -> (ids turned down {id: label}, calls made).
    earlier = labels that existed before this run (a label made tonight needs no check; one
    from an earlier night does — whether it was on the shown list or the AI happened to write
    the same words, which is how today's nightly already fuses some stories)."""
    took = {}
    for r in batch:
        ev = labels.get(r["id"])
        if ev in earlier:
            took.setdefault(ev, []).append(r)
    no, calls = {}, 0
    for label, rs in took.items():
        calls += 1
        try:
            ans = confirm_reuse(client, label, pool[label]["heads"], rs)
        except Exception as e:
            print(f"  ERR  reuse check on {label[:40]!r}: {str(e)[:80]} — treated as no")
            ans = {}
        for r in rs:
            if not ans.get(r["id"]):
                no[r["id"]] = label
    return no, calls


def fresh_labels(client, batch, labels, no, known, earlier):
    """Re-label the headlines the reuse check turned down, the way the nightly always did: shown
    only the labels made in THIS run (none from earlier nights), told not to use the label it
    turned down. A reply that still names an earlier night's label leaves the headline unlabeled
    tonight (it's retried next night) rather than fusing it unchecked. -> labels, updated."""
    rows = [r for r in batch if r["id"] in no]
    tonight = [k for k in known if k not in earlier]
    for i, v in labels.items():          # + labels this batch's first call made fresh
        if i not in no and v not in earlier and v not in tonight:
            tonight.append(v)
    try:
        again = label_batch(client, rows, tonight, avoid=sorted(set(no.values())))
    except Exception as e:
        print(f"  ERR  fresh labels: {str(e)[:80]}")
        again = {}
    for r in rows:
        ev = again.get(r["id"])
        if ev and ev not in earlier:
            labels[r["id"]] = ev
        else:
            labels.pop(r["id"], None)
            print(f"  left unlabeled tonight (reuse turned down, no fresh label): id {r['id']}")
    return labels


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=DELETE")   # NFS-safe, not WAL (2026-07-05 corruption)
    conn.execute("PRAGMA busy_timeout=5000")
    cols = [r[1] for r in conn.execute("PRAGMA table_info(items)")]
    if "event" not in cols:
        conn.execute("ALTER TABLE items ADD COLUMN event TEXT")
        conn.commit()

    where = "score IS NOT NULL AND score >= ?"
    if not REGROUP:
        where += " AND (event IS NULL OR event = '')"
    rows = conn.execute(
        f"SELECT id, title, published, score FROM items WHERE {where} "
        f"ORDER BY score DESC, published DESC",
        (MIN,)).fetchall()
    if not rows:
        print("nothing to group (all caught up).")
        return

    print(f"{'DRY RUN — ' if DRY_RUN else ''}grouping {len(rows)} articles "
          f"(score >= {MIN}) in batches of {BATCH}")
    client = build_client()

    known = []                       # labels made in THIS run (all of them shown on --regroup)
    known_set = set()
    seed = NIGHTLY_SEED and not REGROUP
    pool = load_pool(conn) if seed else None      # nightly + ON: past labels, BOUNDED (pick_known)
    earlier = set(pool) if seed else set()        # labels from earlier runs: reuse gets checked
    most_shown = 0
    done = 0
    calls = checks = turned_down = refreshes = 0
    offered = left_unlabeled = 0      # the nightly drift line (end of run)
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i + BATCH]
        if not seed:
            shown, examples = known, None
        else:
            shown, examples = pick_known(pool, batch)
        most_shown = max(most_shown, len(shown))
        try:
            calls += 1
            labels = label_batch(client, batch, shown, examples)
        except Exception as e:
            print(f"  ERR  batch at {i}: {str(e)[:80]}")
            continue
        if seed:                         # the reuse check, then fresh labels for the turned-down
            offered += sum(1 for r in batch if labels.get(r["id"]) in earlier)
            no, n = check_reuse(client, batch, labels, pool, earlier)
            checks += n
            if no:
                turned_down += len(no)
                refreshes += 1
                labels = fresh_labels(client, batch, labels, no, known, earlier)
                left_unlabeled += sum(1 for i in no if not labels.get(i))
        for r in batch:
            ev = labels.get(r["id"])
            if not ev:
                continue
            if ev not in known_set:
                known_set.add(ev); known.append(ev)
            if pool is not None:
                pool_add(pool, ev, r["title"], r["published"], r["score"], r["id"])
            done += 1
            if DRY_RUN:
                print(f"  {ev[:34]:34s} | {r['title'][:60]}")
            else:
                conn.execute("UPDATE items SET event = ? WHERE id = ?", (ev, r["id"]))
        if not DRY_RUN:
            conn.commit()
        time.sleep(0.4)

    conn.close()
    print(f"\n{'(dry run) ' if DRY_RUN else ''}labeled {done} articles into "
          f"{len(known)} events" + ("" if not seed else
                                    f" (past labels shown per call: at most {most_shown})"))
    if seed:
        print(f"calls: labeler {calls}, reuse checks {checks} ({turned_down} reuses turned "
              f"down), fresh-label calls {refreshes}")
    if not REGROUP:
        drift = (f"reuse check: offered {offered}, approved {offered - turned_down}, rejected "
                 f"{turned_down} (of those, no label tonight {left_unlabeled})"
                 if seed else f"reuse check: OFF ({SEED_OFF_FILE} present or switch off)")
        print(drift)
        if not DRY_RUN and os.path.abspath(DB_PATH) == os.path.abspath(DEFAULT_DB):
            try:                                # live news.db only; never fatal
                with open(REUSE_LOG, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M} UTC  "
                            f"labeled {done}  {drift}\n")
            except OSError as e:
                print(f"  (could not write {REUSE_LOG}: {e})")


if __name__ == "__main__":
    main()
