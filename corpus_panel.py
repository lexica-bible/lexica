#!/usr/bin/env python3
"""corpus_panel.py — the deterministic "lexical-texture" panel for Ask the corpus.

Computed STRUCTURE that sits ABOVE the AI note: per word-family, the distribution of
the query's words across the corpus — counts only (fact), with a visible boundary.
It is the LIVE form of two proven read-only protos (scripts/proto_corpus_panel.py +
scripts/proto_family_assembly.py, chat design 2026-06-29). NO model call: the heads are
the `key_strongs` ai.py already got from the model, so this is pure database work.

THE DISCIPLINE (unchanged from the protos — this is why we proved it cheap first)
  * Bucket BY WORD. Every occurrence is one Strong's number = computed fact, zero
    classification. The panel NEVER sub-sorts a word's hits into senses (presence /
    judgment / purification) — that is the model-judgment-as-count trap, a received
    theology grid laid over a workhorse noun. It counts words; it does not read them.
  * Family = STEM proposes, GLOSS disposes. A candidate is proposed by ONE signal only
    (shared stem / Hebrew root); the gloss then CONFIRMS or denies it (literal whole-word
    overlap, never semantic). CORE (the head) + INCLUDE (stem + gloss agree) are the
    family the reader sees. BORDERLINE (stem only — a false friend like "fever" under
    "fire", OR a real but differently-glossed member) is NOT listed to a lay reader; it
    is only COUNTED ("N related forms set aside"). That is JP's call 2026-06-29 —
    "confident family + a count": keep the boundary visible without dumping unreviewed
    words on a non-scholar.
  * Count is the FULL occurrence set by Strong's (a direct count over words / heb_words),
    never ai.py's sampled result pool (which flattens distribution by design).

SAFETY (live, in the paid request path)
  Built AFTER the answer is assembled, behind a wall-clock deadline, and DROPPED on any
  miss — it must never slow or break the paid answer. `build_panel` opens its OWN
  read-only connections and arms a SQLite progress handler that aborts any query running
  past the deadline; the caller wraps the whole thing in try/except → None. The work is
  indexed counts + two small bounded table scans (lexicon ~5.6k, bdb ~8.6k) per head, so
  it normally finishes in well under the deadline; the guard only bites on real DB
  contention.

DEGRADATION (the real work of wiring a clean proto into messy live traffic)
  * No usable head (broad question, model returned no key word) → no panel.
  * A head that doesn't occur in the corpus (count 0) → its group is dropped.
  * Several unrelated heads (ambiguous query) → one small family per head; never a grid.
  * A head with no word_gloss → shown with a blank range, never invented.
  * A short Hebrew root (≤2 consonants, e.g. אש) → too ambiguous to propose on; falls back
    to gloss-anchored (matches the proto), so the family stays honest instead of flooding.
  * Every one of these resolves to "show less", never "manufacture more".

The LXX seam (Hebrew→Greek word mapping) is deliberately NOT here — it is the separate
range-preservation follow-on (corpus-enrichment memory, REMAINING item #2).
"""
import re
import sys
import time
import unicodedata

try:
    import core
except Exception:  # pragma: no cover - core is always importable in the app
    core = None


# How many word-family groups the panel will show, and how many rows inside one group's
# expandable table. Bounds the payload + the work on a query with many key_strongs.
_MAX_GROUPS = 4
_MAX_FAMILY = 12
# Default wall-clock ceiling for the whole panel build (seconds). Generous vs the typical
# sub-200ms run; only a contended DB ever approaches it, and then we drop the panel.
_DEADLINE_S = 2.0


# ── text helpers (ported verbatim from the proven protos — do NOT "improve") ──────────
_STOP = {"a", "an", "the", "of", "to", "by", "am", "is", "be", "or", "and", "in", "on",
         "for", "with", "from", "as", "at", "it", "that", "this", "one", "esp", "fig",
         "lit", "etc", "all", "any", "his", "her", "its"}

_HEB_FINALS = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}  # final → medial


def _ascii(s):
    """Lowercase, accents stripped, non-letters dropped: 'pŷr'->'pyr'."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", s.lower())


def _heb_root(s):
    """Consonant skeleton of a Hebrew lemma: drop niqqud/cantillation, keep Hebrew letters
    only, fold final forms to medial. 'אֵשׁ'->'אש', 'מִשְׁבָּת'->'משבת'."""
    if not s:
        return ""
    out = []
    for ch in unicodedata.normalize("NFKD", s):
        if unicodedata.combining(ch):
            continue
        if "א" <= ch <= "ת":
            out.append(_HEB_FINALS.get(ch, ch))
    return "".join(out)


def _heb_rootify(cons):
    """Approximate the triliteral root by stripping ONE trailing affix (fem -ה, plural
    -ות/-ים): 'אהבה'->'אהב'. Matching is by containment, which already absorbs a leading
    preformative, so only the trailing affix is handled here."""
    if len(cons) >= 4 and cons.endswith(("ות", "ים")):
        return cons[:-2]
    if len(cons) >= 4 and cons.endswith("ה"):
        return cons[:-1]
    return cons


def _norm_word(w):
    """Lowercase + a light plural fold so 'trials' matches 'trial'. NOT a stemmer — it does
    not bridge fire/fiery (that swap is a human call, left to the borderline tier)."""
    w = w.lower()
    if len(w) > 3 and w.endswith("s"):
        w = w[:-1]
    return w


def _gloss_terms(gloss):
    """The head gloss's meaning-words, whole-word + plural-folded: 'fire, trials' ->
    {'fire','trial'}."""
    out = set()
    for w in re.findall(r"[A-Za-z]+", gloss or ""):
        if len(w) >= 3 and w.lower() not in _STOP:
            out.add(_norm_word(w))
    return out


def _gloss_confirms(gloss, terms):
    """True if a candidate's gloss shares a meaning-word with the head's terms (literal
    whole-word overlap, plural-folded — never semantic, so no thesaurus leak)."""
    if not terms:
        return False
    for w in re.findall(r"[A-Za-z]+", gloss or ""):
        if len(w) >= 3 and _norm_word(w) in terms:
            return True
    return False


# ── DB lookups ────────────────────────────────────────────────────────────────────────
def _has_table(conn, name):
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())


def _wg(conn, prefixed):
    """The plain attested range for a fully-prefixed Strong's ('G4442'/'H784') from the
    word_gloss side table — the bucket label. '' if the table or row is absent."""
    if not _has_table(conn, "word_gloss"):
        return ""
    r = conn.execute("SELECT gloss FROM word_gloss WHERE strongs=?", (prefixed,)).fetchone()
    return (r["gloss"] or "").strip() if r else ""


def _greek_occ(conn, base):
    return conn.execute(
        "SELECT count(*) c FROM words WHERE strongs_base=?", (f"G{base}",)).fetchone()["c"]


def _heb_occ(hconn, base):
    if hconn is None:
        return 0
    try:
        return hconn.execute(
            "SELECT count(*) c FROM heb_words WHERE strongs=? OR strongs GLOB ?",
            (f"H{base}", f"H{base}[A-Za-z]")).fetchone()["c"]
    except Exception:
        return 0


def _greek_head(conn, base):
    """(lemma, translit, gloss-for-display, terms-for-matching) for a Greek head. The
    display range is word_gloss only (blank if absent — never the KJV-flavored fallback);
    the MATCHING terms may fall back to the raw lexicon gloss so a head always has terms."""
    r = conn.execute(
        "SELECT lemma, translit, strongs_def, kjv_def FROM lexicon WHERE strongs_g=? OR strongs=?",
        (f"G{base}", base)).fetchone()
    if not r or not (r["lemma"] or "").strip():
        return None
    wg = _wg(conn, f"G{base}")
    terms_src = wg or (r["kjv_def"] or "") or (r["strongs_def"] or "")
    return (r["lemma"] or "", r["translit"] or "", wg, _gloss_terms(terms_src))


def _heb_head(conn, base):
    """(lemma, xlit, root, gloss-for-display, terms-for-matching) for a Hebrew head."""
    r = conn.execute(
        "SELECT lemma, xlit, description FROM bdb WHERE strongs_id=?", (f"H{base}",)).fetchone()
    if not r or not (r["lemma"] or "").strip():
        return None
    wg = _wg(conn, f"H{base}")
    terms_src = wg or (r["description"] or "")
    root = _heb_rootify(_heb_root((r["lemma"] or "").strip()))
    return (r["lemma"] or "", r["xlit"] or "", root, wg, _gloss_terms(terms_src))


# Common Greek prepositional prefixes (romanized, as they read after _ascii). A compound
# like prosabbaton = pro + sabbaton hides the root stem behind a prefix, so a strict
# "translit starts with the stem" proposer misses it (prosabbaton is a real Sabbath-family
# time-word, not a false friend). We let the stem also match right after a known prefix.
# This WIDENS only what the PROPOSER sees — the gloss gate is untouched, so a prefixed
# false friend (propyretos "fever") still lands in the counted-but-not-shown boundary.
_GK_PREFIXES = (
    "amphi", "anti", "apo", "ana", "dia", "eis", "epi", "ek", "ex", "en",
    "kata", "kat", "meta", "met", "para", "peri", "pros", "pro",
    "syn", "sym", "hyper", "hypo",
)


def _stem_proposes(t, stem):
    """True if a candidate translit `t` carries the head stem at its start, or directly
    after a known Greek prefix (so prosabbaton = pro + sabbaton is proposed)."""
    if not (t and stem):
        return False
    if t.startswith(stem):
        return True
    return any(t.startswith(p) and t[len(p):].startswith(stem) for p in _GK_PREFIXES)


# ── family assembly (STEM proposes, GLOSS disposes; the boundary is COUNTED) ───────────
def _greek_family(conn, head_base, stem, terms):
    """Greek family near a head: lexicon rows whose translit carries the head's stem at the
    start OR after a known prefix (STEM), each kept as INCLUDE when its gloss confirms, else
    counted toward set_aside. Returns (include_rows, set_aside_count) with script + range."""
    include, set_aside, seen = [], 0, {head_base}
    for r in conn.execute("SELECT strongs_g, strongs, translit, lemma FROM lexicon"):
        t = _ascii(r["translit"])
        if not _stem_proposes(t, stem):
            continue
        base = (r["strongs_g"] or ("G" + (r["strongs"] or ""))).lstrip("G")
        if not base or base in seen:
            continue
        seen.add(base)
        occ = _greek_occ(conn, base)
        if occ == 0:
            continue                       # dead — never chipped (proto rule)
        gloss = _wg(conn, f"G{base}")
        if _gloss_confirms(gloss, terms):
            include.append({"strongs": f"G{base}", "lemma": r["lemma"] or "",
                            "translit": r["translit"] or "", "gloss": gloss, "count": occ})
        else:
            set_aside += 1                 # stem only — the visible boundary, counted
    return include, set_aside


def _hebrew_family(conn, hconn, head_base, root, terms):
    """Hebrew family near a head, root-anchored by CONTAINMENT. A SHORT root (≤2 consonants)
    is too ambiguous to propose on its own, so there the gloss MUST also confirm
    (gloss-anchored — matches the proto). Returns (include_rows, set_aside_count)."""
    if not root:
        return [], 0
    short = len(root) < 3
    include, set_aside, seen = [], 0, {head_base}
    for r in conn.execute("SELECT strongs_id, xlit, lemma FROM bdb"):
        if root not in _heb_root(r["lemma"]):
            continue
        base = (r["strongs_id"] or "").lstrip("H")
        if not base or base in seen:
            continue
        seen.add(base)
        gloss = _wg(conn, f"H{base}")
        confirms = _gloss_confirms(gloss, terms)
        if short and not confirms:
            continue                       # short root: root signal alone is meaningless
        occ = _heb_occ(hconn, base)
        if occ == 0:
            continue
        if confirms:
            include.append({"strongs": f"H{base}", "lemma": r["lemma"] or "",
                            "translit": r["xlit"] or "", "gloss": gloss, "count": occ})
        else:
            set_aside += 1
    return include, set_aside


def _build_group(conn, hconn, lang, base):
    """One word-family group for a head, or None if the head can't anchor one (not in the
    lexicon, or zero occurrences). lang is 'G' or 'H'."""
    if lang == "G":
        head = _greek_head(conn, base)
        if not head:
            return None
        lemma, translit, gloss, terms = head
        count = _greek_occ(conn, base)
        if count == 0:
            return None
        stem = _ascii(translit)[:4] or _ascii(translit)
        include, set_aside = _greek_family(conn, base, stem, terms)
        label = "Greek (NT / Greek OT)"
    else:
        if hconn is None:
            return None                    # heb.db absent — no honest Hebrew count
        head = _heb_head(conn, base)
        if not head:
            return None
        lemma, translit, root, gloss, terms = head
        count = _heb_occ(hconn, base)
        if count == 0:
            return None
        include, set_aside = _hebrew_family(conn, hconn, base, root, terms)
        label = "Hebrew (OT)"

    core_row = {"strongs": f"{lang}{base}", "lemma": lemma, "translit": translit,
                "gloss": gloss, "count": count, "core": True}
    # CORE leads (the word the reader asked about); INCLUDE follows, most-frequent first.
    include.sort(key=lambda r: -r["count"])
    family = [core_row] + [dict(r, core=False) for r in include[:_MAX_FAMILY - 1]]
    return {
        "lang": lang,
        "label": label,
        "family": family,
        "max": max(r["count"] for r in family),   # bars scale WITHIN the group's language
        "set_aside": set_aside,
    }


# ── public entry points ───────────────────────────────────────────────────────────────
def build_groups(conn, hconn, heads, deadline=None):
    """Assemble the panel's groups from prefixed heads (['G4442','H784']). Pure +
    testable: takes open connections. Stops early when `deadline` (monotonic seconds)
    passes. Dedupes — a head already shown inside an earlier group's family is skipped."""
    groups, covered = [], set()
    for h in heads:
        if len(groups) >= _MAX_GROUPS:
            break
        if deadline is not None and time.monotonic() > deadline:
            break
        m = re.match(r"^([GH])(\d+)", str(h).strip(), re.IGNORECASE)
        if not m:
            continue
        lang, base = m.group(1).upper(), m.group(2)
        if base in covered:
            continue                       # already inside a prior family — don't repeat it
        try:
            grp = _build_group(conn, hconn, lang, base)
        except Exception:
            grp = None                     # a bad head can't sink the whole panel
        if not grp:
            continue
        for row in grp["family"]:
            covered.add(row["strongs"].lstrip("GH"))
        groups.append(grp)
    return groups


def build_panel(heads, deadline_s=_DEADLINE_S):
    """LIVE entry: build the panel dict (or None) from the model's heads. Opens its OWN
    read-only connections, arms a deadline watchdog on each, and returns None on ANY
    problem — it can never slow or break the paid answer. The caller still wraps it."""
    if core is None or not heads:
        return None
    conn = hconn = None
    deadline = time.monotonic() + max(0.25, deadline_s)

    def _watchdog():
        return 1 if time.monotonic() > deadline else 0

    try:
        conn = core.db_ro()
        # The watchdog aborts a RUNNING query past the deadline, but it can't fire while a
        # query waits on a writer's lock — so give up on a lock fast (the panel is
        # droppable; better no panel than a stalled answer). Overrides db_ro's 5s default.
        conn.execute("PRAGMA busy_timeout = 250")
        conn.set_progress_handler(_watchdog, 100000)   # abort any query past the deadline
        try:
            hconn = core.heb_db()
            hconn.execute("PRAGMA busy_timeout = 250")
            hconn.set_progress_handler(_watchdog, 100000)
        except Exception:
            hconn = None                   # heb.db not loaded — Greek heads still work
        groups = build_groups(conn, hconn, heads, deadline=deadline)
        return {"groups": groups} if groups else None
    except Exception:
        return None
    finally:
        for c in (conn, hconn):
            if c is not None:
                try:
                    c.set_progress_handler(None, 0)
                    c.close()
                except Exception:
                    pass


# Manual smoke test (PA only — bible.db + heb.db are PA-only):
#   python corpus_panel.py G4442 H784
if __name__ == "__main__":
    import json
    hs = sys.argv[1:] or ["G4442", "H784"]
    print(json.dumps(build_panel(hs), ensure_ascii=False, indent=2))
