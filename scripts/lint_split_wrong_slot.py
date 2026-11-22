#!/usr/bin/env python3
"""
lint_split_wrong_slot.py — full-corpus wrong-slot certification for _split_compounds.

The 60-verse spread said FREEZE (0 content-word wrong-slot). This lint proves the
other ~12,632 split-affected verses the sample didn't touch: a content word landing
on the wrong Strong's number is the phrase-boundary poison class — it corrupts the
"renders as" data every consumer reads. This flags exactly that, corpus-wide.

SCOPE = the split's RECIPIENTS only. The lint checks the slots _split_compounds actually
moved a word INTO (captured by diffing english_head per number around the real split),
NOT every content slot in an affected verse. Auditing whole verses drowned the signal in
ABP's OWN parking — a verb parked on οὐ/σοῦ/νύξ that the split never touched. Those are
the accepted head-word caveat, not a split error, so they are out of scope by construction.

READ-ONLY: opens bible.db read-only (unused beyond a handle check), reads the ABP
source + bh_scrape.db, writes nothing to any table. Reuses build_words_from_abp's
real split (no re-implementation, can't drift).

── Reference = the corpus's OWN attested renderings (not a lexicon) ──
First try used the split's KJV-based lexicon as the reference. Its CONTROL FAILED (4
false flags on a known-good verse): ABP does not speak KJV's vocabulary — ὀσμή/3744 is
"savour/odour" in KJV but ABP renders it "scent"; ἔπω/2036 is "say" but ABP renders
"said". A correctly-placed word was flagged just for being ABP's wording. Any external
lexicon (KJV or Dodson) has this vocabulary gap and drowns the signal.

So the reference is ABP itself: {strongs_base -> how often each english_head renders
it, across the WHOLE corpus}. A wrong-slot word is a RARE rendering of an otherwise
FREQUENT number — "kissed" on 3744 (rendered "scent" everywhere else) stands out;
"scent" on 3744 does not, because it is the number's normal rendering. This speaks
ABP's vocabulary because it IS ABP's vocabulary.

SELF-VALIDATION GUARD (frequency floor). The reference counts the very row under test,
so a mere "does this rendering exist for this number" check would pass every leak by
construction — a wrong "scent" landing once enters 3744's profile and validates itself.
Worse, a leak that fired TWICE would look like a recurring rendering. So a rendering
must recur at least VALIDATE_MIN=3 times on a number to VALIDATE a slot; 1 or 2
occurrences FLAG. A per-verse leak is idiosyncratic (rare on that number); a legit
rendering recurs. This catches the one-off AND the fired-twice leak.

CIRCULARITY LIMIT (stated so a clean run isn't misread): a mis-placement repeated
>= VALIDATE_MIN times would make its wrong rendering look legit and hide it — a
SYSTEMATIC error is a different audit. The independent leg is the 60-verse BibleHub
cross-check; this is the completeness leg over the ~12,632 the sample missed.

The of-on-pronoun softness (a bare function word on a pronoun/article slot) is an
ACCEPTED limit (parse_abp.SPLIT_FUNCWORD_SLOT_CAVEAT), invisible here by construction:
english_head is None for an all-function gloss, and only content-head slots are checked.

Run on PA:
    python3 scripts/lint_split_wrong_slot.py bible.db bh_scrape.db --control   # must pass
    python3 scripts/lint_split_wrong_slot.py bible.db bh_scrape.db             # full pass
"""
import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_words_from_abp as B

_PUNCT = re.compile(r"[^\w]")

VALIDATE_MIN = 3   # a rendering must recur >= this many times on a number to validate a slot
MIN_FREQ     = 8   # ...and only numbers used at least this often are judged (else rare != wrong)


def _fold(w):
    """One rendering key per english_head: lowercase, strip punctuation, and collapse regular
    inflections (plural + verb tense) so a Greek word's varied renderings share a key —
    smell/smelled/smelling -> "smell". Without this a frequent verb's renderings fragment
    across tenses and NONE reaches the frequency floor, so a correct rare spelling ('smelled',
    2x) gets flagged. Short words are guarded (bed/led/was keep their -ed/-s). A wrong word
    still stems to a form the number never renders (kissed->kiss on αὐτός = 0)."""
    w = _PUNCT.sub("", (w or "").lower())
    if not w:
        return w
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3 and not w.endswith("ss"):
            return w[:-len(suf)]
    return w


# ── Triage: the raw flag list is a CANDIDATE GENERATOR, not a verdict ──────────────
# At corpus scale the heuristic's precision collapses — OT free vocabulary means legit
# singleton renderings of a frequent number are common (3,442 flags vs the 0/60 externally
# verified sample can't both be true). These three filters each use a reference where it is
# STRONG (a lexicon that failed as a certification yardstick is fine as a noise filter), to
# strip the known false-positive classes so a small residue can be BibleHub-sampled.

_NUM_STEMS = {_fold(w) for w in (
    "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety "
    "hundred thousand ten-thousand myriad first second third fourth fifth sixth seventh eighth "
    "ninth tenth eleventh twelfth").split()}


def _load_dodson(conn):
    """{bare_base: set(gloss words)} from word_gloss (Dodson/Strong's-Hebrew plain glosses)."""
    d = {}
    try:
        cur = conn.execute("SELECT strongs, gloss FROM word_gloss")
    except Exception:
        return d
    for strongs, gloss in cur:
        base = (strongs or "").lstrip("GH").split(".")[0]
        if base:
            d.setdefault(base, set()).update(_PUNCT.sub(" ", (gloss or "").lower()).split())
    return d


def _triage(flags, counts, lex, dodson):
    """Sort raw flags into buckets. residue = what survives all three filters — the real
    wrong-slot candidates to sample. lex = split's Strong's/KJV set; dodson = word_gloss."""
    gcache = {}

    def gstems(base):
        if base not in gcache:
            s = {_fold(w) for w in lex.get(base, ())} | {_fold(w) for w in dodson.get(base, ())}
            gcache[base] = {x for x in s if x}
        return gcache[base]

    buckets = {"numeral": [], "in_lexicon": [], "stump": [], "residue": []}
    for fl in flags:
        _ref, _pos, F, base = fl
        g = gstems(base)
        if g & _NUM_STEMS:                                  # the NUMBER itself is a numeral
            buckets["numeral"].append(fl); continue
        if F in g:                                          # word IS in this number's gloss (odd wording)
            buckets["in_lexicon"].append(fl); continue
        stump = False                                       # F is a truncated form of a word the number carries
        for R, c in counts[base].items():
            if (c >= VALIDATE_MIN and R != F and len(F) >= 4 and len(R) >= 4
                    and abs(len(F) - len(R)) <= 3 and (R.startswith(F) or F.startswith(R))):
                stump = True; break
        buckets["stump" if stump else "residue"].append(fl)
    return buckets


def _content_slots(rows):
    """Yield (position, english_head, strongs_base) for every content slot — a slot with a
    real content english_head on a numbered Greek word. Function-only slots (head None),
    '*' and blank bases are skipped, so the of-on-pronoun softness never reaches here."""
    for r in rows:
        head, base = r[2], r[4]
        if not head or not base or not base[0].isdigit():
            continue
        hf = _fold(head)
        if hf:
            yield r[0], hf, base


def _flag_recips(recips, counts, totals, ref):
    """Flag a split RECIPIENT (position, head, base) whose rendering is rare on a well-attested
    number. recips carry the raw english_head; fold it here to key against the reference."""
    out = []
    for pos, head, base in recips:
        hf = _fold(head)
        if not hf or not base or not base[0].isdigit():
            continue
        if totals.get(base, 0) >= MIN_FREQ and counts[base].get(hf, 0) < VALIDATE_MIN:
            out.append((ref, pos, hf, base))
    return out


def _iter_built(bh_index, lex, rahlfs, tagnt, want_affected):
    """Run the real per-verse pipeline over the whole corpus. Yields (ref, rows, recips) for
    every verse; `recips` = the (position, english_head, base) slots _split_compounds actually
    MOVED a word into — captured by diffing english_head per base around the real split. This
    scopes the audit to the split's own output, not every word ABP parked in the verse."""
    real_split = B._split_compounds
    holder = {"recips": [], "nrecip": 0, "fnwords": []}

    def wrapped(rows, lexicon, carry=False):
        before_ne = sum(1 for r in rows if (r[1] or "").strip())
        # heads present per base BEFORE the split (the source slots' own words)
        before = defaultdict(Counter)
        before_fn = defaultdict(Counter)          # head-None (function) slots that already had text
        for r in rows:
            if r[2]:
                before[r[4]][r[2]] += 1
            elif (r[1] or "").strip():
                before_fn[r[4]][(r[1] or "").strip().lower()] += 1
        real_split(rows, lexicon, carry)
        after_ne = sum(1 for r in rows if (r[1] or "").strip())
        # TOTAL recipient slots the split filled (incl function words) — reconciles with the
        # sizing script's net-non-empty-increase count (~18,339).
        holder["nrecip"] = max(0, after_ne - before_ne)
        # CONTENT recipients: a head now present on a base BEYOND its before-count. A function
        # word ("of"/"and") lands with head None, so it is excluded here by construction — the
        # accepted caveat, out of the wrong-slot audit but still counted in nrecip above.
        seen = defaultdict(Counter)
        seen_fn = defaultdict(Counter)
        recips, fnwords = [], []
        for r in rows:
            if r[2]:
                base, head = r[4], r[2]
                seen[base][head] += 1
                if seen[base][head] > before[base].get(head, 0):
                    recips.append((r[0], head, base))
            elif (r[1] or "").strip():
                # a newly-filled head-None slot: the function-word text the split moved. Collected
                # so we can EYEBALL the ~17k function-recipient vocabulary for a content word that
                # a hand-curated function-word list mis-swallowed (which would exit the audit silently).
                base, w = r[4], (r[1] or "").strip().lower()
                seen_fn[base][w] += 1
                if seen_fn[base][w] > before_fn[base].get(w, 0):
                    fnwords.append(w)
        holder["recips"] = recips
        holder["fnwords"] = fnwords
    B._split_compounds = wrapped

    for abbrev, ch, vs, abp_words in B.iter_verses(*B._abp_sources()):
        slug = B.ABBREV_TO_SLUG.get(abbrev)
        bh_rows = bh_index.get((slug, ch, vs), []) if slug else []
        src = bnum = None
        if rahlfs and rahlfs.booknum(abbrev):
            src, bnum = rahlfs, rahlfs.booknum(abbrev)
        elif tagnt and tagnt.booknum(abbrev):
            src, bnum = tagnt, tagnt.booknum(abbrev)
        if src:
            corrs = B.correct_verse([w[1] for w in abp_words],
                                    src.verse(bnum, ch, vs), [w[0] for w in abp_words])
            abp_words = B.apply_pronoun_corrections(abp_words, corrs, [], f"{abbrev} {ch}:{vs}")
        holder["recips"] = []
        holder["nrecip"] = 0
        holder["fnwords"] = []
        rows = B.build_verse_words(abp_words, bh_rows, lex)
        yield f"{abbrev} {ch}:{vs}", rows, holder["recips"], holder["nrecip"], holder["fnwords"]


# ── --app-feed: L9 on the app-edition words (edition upgrade, DESIGN §9.214, §9.239) ──────────
# Built's English is the app-feed transplant: per verse the build makes the OLD rows (the old
# text, every pass) and then AppTransplant.apply builds the FEED rows (the feed's English, the
# same pipeline, so _split_compounds runs a SECOND time) and composes the two
# (build_words_from_abp.run :2788-2793; apply :2400-2470). The default mode above replays the OLD
# text only, so on built it measures a split the live rows no longer carry (DR "### L9 on built -
# the code answer"). This mode replays the build's own path - OLD rows with ren= and names= as
# run() passes them, then app.apply - and takes the recipients from the COMPOSED rows only: a
# split recipient counts where its own run supplied the composed cell (english + english_head
# equal to that run's final row at that position). A merge-pair restore (§9.73) and an edge
# split's blank row (§9.75: the piece IS the old English, with the old head) equal the OLD cell
# and are OLD's; an edge split's neighbour whose rest is not its old English is neither run's
# and carries no split recipient. Positions are the build's position values (r[0]), which
# the split itself permutes (build_words_from_abp.py :623-625), never list indexes.

def _owners(calls, rows, old_rows):
    """{position: the build_verse_words call that supplied the composed cell, or None}. rows IS
    old_rows when apply kept the OLD set (any outcome but a pass): then only call 0 (the OLD run)
    owns cells, even when apply built a FEED set and refused it (passdiff)."""
    if rows is old_rows:
        return {r[0]: calls[0] for r in rows}
    if len(calls) != 2:
        raise RuntimeError(f"composed verse with {len(calls)} build_verse_words calls (expected 2)")
    old_c, feed_c = calls
    oc = {r[0]: (r[1], r[2]) for r in old_c["rows"]}
    fc = {r[0]: (r[1], r[2]) for r in feed_c["rows"]}
    out = {}
    for r in rows:
        cell = (r[1], r[2])
        out[r[0]] = feed_c if fc.get(r[0]) == cell else old_c if oc.get(r[0]) == cell else None
    return out


def _filled(before, after):
    """-> (positions the split FILLED, ambiguous groups). The split rewrites the rows it uses,
    permutes their positions (:623-625) and SORTS the list (:627), so a row is followed by what
    the split never changes - its Greek side (strongs, strongs_base, italic, italic_words,
    smcap_words, morph, lemma; idx 3, 4, 7, 8, 9, 11, 12). A row left untouched (same tuple at
    the same position) is not filled. The changed rows pair up by that Greek side; a slot is
    filled when it had no English before and has English after. A Greek side shared by changed
    rows that were not all empty, or all filled, before cannot be paired for certain: counted
    as ambiguous (expected 0; a non-zero is printed, not guessed past)."""
    gk = lambda r: (r[3], r[4], r[7], r[8], r[9], r[11], r[12])   # noqa: E731
    bpos = {r[0]: r for r in before}
    same = {r[0] for r in after if bpos.get(r[0]) == r}
    bgroups, agroups = defaultdict(list), defaultdict(list)
    for r in before:
        if r[0] not in same:
            bgroups[gk(r)].append(r)
    for r in after:
        if r[0] not in same:
            agroups[gk(r)].append(r)
    filled, ambiguous = [], 0
    for k, arows in agroups.items():
        empty_before = {not (r[1] or "").strip() for r in bgroups.get(k, [])}
        if len(empty_before) > 1 or len(bgroups.get(k, [])) != len(arows):
            ambiguous += 1
            continue
        if empty_before == {True}:
            filled += [r[0] for r in arows if (r[1] or "").strip()]
    return filled, ambiguous


def _iter_built_app(bh_index, lex, rahlfs, tagnt, app, ren, names, verse_keys, stash, amb=None,
                    changes=None):
    """Yields (ref, rows, recips, nrecip, fnwords) like _iter_built, from the COMPOSED rows.
    verse_keys = the db's verses (run() skips a verse with no row, :2764-2767). stash[key] =
    {position: (english_head, strongs_base)} of the composed rows, for the words-table check.
    nrecip = the slots the split FILLED (empty before, text after) in the run that owns them.

    JUDGED ON THE COMPOSED CELL (§9.240 (1)). Passes after the split inside build_verse_words
    (:1982-1999) never move a position but can change a filled slot's Strong's number
    (_fix_backwards_pairing :714-717, _split_pn_article_lump :763-767, _g1473_gloss_retag :1551,
    _strip_helper_double_tag :467), its english / head (_split_pn_article_lump, _lord_subject_split
    :1612-1616, _lord_oath_fix :1757-1758, _strip_italic_heads :1834, _star_name_heads :1851;
    punctuation only :1468), or empty it (_funcword_noun_relocate :1723). So each owned filled
    slot is classed by its COMPOSED row - a content head -> a content recipient judged as
    (position, composed head, composed base); text with no head -> a function word; no text ->
    emptied - and every one whose split-time (head, base) is not the composed (head, base), or
    that is emptied, is appended to `changes` (ref, position, class, split english / head / base,
    composed english / head / base), class 'changed' or 'emptied'. A punctuation-only english
    move (:1468) is not listed. Nothing is judged on a pair live does not carry."""
    real_split, real_bvw = B._split_compounds, B.build_verse_words
    calls, cur = [], {}

    def wrapped(rows, lexicon, carry=False):
        snap = list(rows)
        real_split(rows, lexicon, carry)
        filled, n_amb = _filled(snap, rows)
        if amb is not None and n_amb:
            amb.append((cur["ref"], n_amb))
        # the FILLED slots themselves, with their split-time cell. (_iter_built's count-beyond-
        # before per base+head credits the LAST row of a repeated word - "God madeG4160 G2316
        # andG2532 GodG2316" credits the source's own 'God' at 3, not the filled slot 0 -
        # harmless there, wrong once ownership is by position.)
        at = {r[0]: r for r in rows}
        cur["filled"] = {p: (at[p][1], at[p][2], at[p][4]) for p in filled}

    def wrapped_bvw(*a, **k):
        ref = cur.get("ref")
        cur.clear()
        cur.update(filled={}, ref=ref)
        out = real_bvw(*a, **k)
        calls.append(dict(cur, rows=out))
        return out

    B._split_compounds, B.build_verse_words = wrapped, wrapped_bvw
    try:
        for abbrev, ch, vs, raw_words in B.iter_verses(*B._abp_sources()):
            key = (abbrev, ch, vs)
            if key not in verse_keys:
                continue
            slug = B.ABBREV_TO_SLUG.get(abbrev)
            bh_rows = bh_index.get((slug, ch, vs), []) if slug else []
            words, corrs = B._pronoun_corrections(abbrev, ch, vs, raw_words, rahlfs, tagnt, [])
            calls.clear()
            cur["ref"] = f"{abbrev} {ch}:{vs}"
            old_rows = B.build_verse_words(words, bh_rows, lex, ren=ren, article_refusals=[],
                                           names=names, pn_star_refusals=[])
            rows = app.apply(key, raw_words, corrs, old_rows, bh_rows, lex, ren=ren, names=names)
            own = _owners(calls, rows, old_rows)
            comp = {r[0]: r for r in rows}
            recips, fnwords, nrecip = [], [], 0
            for c in calls:
                for p, (e_s, h_s, b_s) in sorted(c["filled"].items()):
                    if own.get(p) is not c:
                        continue
                    nrecip += 1
                    r = comp[p]
                    text = (r[1] or "").strip()
                    if r[2]:
                        recips.append((p, r[2], r[4]))
                    elif text:
                        fnwords.append(text.lower())
                    if changes is not None and ((h_s, b_s) != (r[2], r[4]) or not text):
                        changes.append((cur["ref"], p, "changed" if text else "emptied",
                                        e_s, h_s, b_s, r[1], r[2], r[4]))
            stash[key] = {r[0]: (r[2], r[4]) for r in rows}
            yield f"{abbrev} {ch}:{vs}", rows, recips, nrecip, fnwords
    finally:
        B._split_compounds, B.build_verse_words = real_split, real_bvw


def _load_words(conn):
    """{(book, chapter, verse): {position: (english_head, strongs_base)}} from the words table."""
    out = defaultdict(dict)
    for b, c, v, pos, head, sb in conn.execute(
            "SELECT v.book, v.chapter, v.verse, w.position, w.english_head, w.strongs_base "
            "FROM words w JOIN verses v ON v.id = w.verse_id"):
        out[(b, c, v)][pos] = (head, sb)
    return out


def _vs_words(affected, stash, live):
    """Each content recipient's composed cell against the words table at the same verse and
    position: the replay speaks for live only where they agree. -> (match, differ_rows,
    verses_rowcount_differs). strongs_base compared G-prefixed (_prefix_base)."""
    match, differ = 0, []
    for ref, recips in affected:
        ab, cv = ref.split(" ")
        ch, vs = (int(x) for x in cv.split(":"))
        key = (ab, ch, vs)
        for pos, head, base in recips:
            ch_head, ch_base = stash[key][pos]
            want = (ch_head, "G" + ch_base if ch_base and ch_base[0].isdigit() else ch_base)
            got = live.get(key, {}).get(pos)
            if got == want:
                match += 1
            else:
                differ.append((ref, pos, head, base, want[0], want[1],
                               "" if got is None else got[0], "(no row)" if got is None else got[1]))
    rc = sum(1 for k, cells in stash.items() if len(live.get(k, {})) != len(cells))
    return match, differ, rc


def _build_counts_and_stash(bh_index, lex, rahlfs, tagnt, it=None):
    """One pass: tally every number's renderings across the WHOLE corpus (the reference —
    all slots), and stash the split RECIPIENTS of affected verses (what we certify).
    it = another verse iterator (the --app-feed one); None = the default replay."""
    counts = defaultdict(Counter)
    totals = Counter()
    affected = []
    recon = {"total_recip": 0, "verses_any": 0, "fnvocab": Counter()}   # reconciliation vs sizing
    if it is None:
        it = _iter_built(bh_index, lex, rahlfs, tagnt, want_affected=True)
    for ref, rows, recips, nrecip, fnwords in it:
        for _pos, hf, base in _content_slots(rows):
            counts[base][hf] += 1
            totals[base] += 1
        recon["fnvocab"].update(fnwords)
        recon["total_recip"] += nrecip
        if nrecip:
            recon["verses_any"] += 1
        if recips:
            affected.append((ref, recips))
    return counts, totals, affected, recon


def run_control(counts, totals, affected):
    """Control-test rule: fire at a known-GOOD verse (must pass) + a hand-BROKEN one (must
    flag). The zero isn't trusted until the pattern draws blood."""
    # a verse with a known CONTENT recipient: Gen 1:1 "God made" -> "God" onto θεός/2316.
    good = next((r for r in affected if r[0] == "Gen 1:1"), None) or (affected[0] if affected else None)
    if not good:
        print("CONTROL ERROR: no content-recipient verse in the affected set"); return False
    ref, recips = good
    print(f"  control verse: {ref}  recipients: " +
          ", ".join(f"{h!r}<{b}>" for _p, h, b in recips))

    good_flags = _flag_recips(recips, counts, totals, ref)
    print(f"  known-good {ref}: {len(good_flags)} flag(s)  (expect 0)  "
          f"[{len(recips)} split recipients checked]")
    for f in good_flags:                                 # show WHY: usage + top renderings
        b = f[3]
        top = ", ".join(f"{k}:{v}" for k, v in counts[b].most_common(5))
        print(f"      unexpected flag: pos {f[1]} {f[2]!r} on {b}  "
              f"(number used {totals[b]}x; renderings {top})")

    # hand-break the ACTUAL failure class: inject a recipient that puts a content word onto a
    # FREQUENT number that never renders it (a word landing on the wrong Greek word). Injecting
    # a fabricated recipient — not swapping rows — is the right shape now that we check recips.
    freq_targets = [b for b, t in totals.most_common() if t >= MIN_FREQ]
    word = next((h for _p, h, _b in recips if _fold(h)), "approaching")
    T = next((t for t in freq_targets if counts[t].get(_fold(word), 0) == 0), None)
    if T is None:
        print("CONTROL ERROR: no frequent number that never renders the test word"); return False
    broken = list(recips) + [(-1, word, T)]                 # a wrong recipient
    bad_flags = _flag_recips(broken, counts, totals, ref + " [BROKEN]")
    print(f"  hand-broken {ref}: injected recipient {word!r} onto {T} (renders it 0x, used {totals[T]}x)  "
          f"-> {len(bad_flags)} flag(s)  (expect >=1)")

    ok = (len(good_flags) == 0 and len(bad_flags) >= 1)
    print(f"\n  CONTROL {'PASSED' if ok else 'FAILED'}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bible_db", nargs="?", default="bible.db")
    ap.add_argument("scrape_db", nargs="?", default="bh_scrape.db")
    ap.add_argument("--control", action="store_true", help="run the control test and exit")
    ap.add_argument("--out", default="split_wrong_slot_flags.tsv")
    ap.add_argument("--app-feed", action="store_true",
                    help="L9 on the app-edition words: replay the build's transplant, recipients from the "
                         "COMPOSED rows, and check each one against the words table (DESIGN 9.214, 9.239)")
    ap.add_argument("--count-differs", default=str(B.APP_COUNT_DIFFERS),
                    help="with --app-feed: the frozen chunk-level count-differs file (as the build)")
    args = ap.parse_args()

    if args.app_feed:
        # every file this mode writes goes to the CURRENT folder under a fixed name: say which
        # folder, and never write over an earlier run's file (§9.240 (5))
        outs = [args.out, "split_function_recipient_vocab.tsv", "split_wrong_slot_residue.tsv",
                "split_wrong_slot_vs_words.tsv", "split_recipients_changed.tsv"]
        print(f"output folder: {Path.cwd()}")
        there = [o for o in outs if Path(o).exists()]
        if there:
            print(f"STOP: output file(s) already in this folder, not overwritten: {there}")
            sys.exit(1)

    import sqlite3
    ro = sqlite3.connect(f"file:{args.bible_db}?mode=ro", uri=True)
    lex = B.load_lexicon(ro)                        # used by the split's own passes + the triage noise filter
    dodson = _load_dodson(ro)                       # word_gloss (Dodson/Strong's-Hebrew) for the noise filter
    if args.app_feed:
        verse_keys = {(b, c, v) for b, c, v in ro.execute("SELECT book, chapter, verse FROM verses")}
        live = _load_words(ro)
        print(f"words table: {sum(len(c) for c in live.values()):,} rows in {len(live):,} verses; "
              f"verses table: {len(verse_keys):,}")
    ro.close()

    scrape = sqlite3.connect(args.scrape_db)
    bh_index = B.load_bh_verse_index(scrape)
    scrape.close()

    rahlfs = tagnt = None
    if B.RahlfsLXX and B.RAHLFS_DIR.is_dir():
        rahlfs = B.RahlfsLXX(B.RAHLFS_DIR); print("Rahlfs: loaded")
    else:
        print("Rahlfs: NOT found — OT input will differ from production")
    if B.TAGNTSource and all(p.is_file() for p in B.TAGNT_FILES):
        tagnt = B.TAGNTSource([str(p) for p in B.TAGNT_FILES]); print("TAGNT: loaded")
    else:
        print("TAGNT: NOT found — NT input will differ from production")

    it = stash = app = None
    if args.app_feed:
        from abp_app_feed import FeedError
        try:
            app = B.AppTransplant(B.abp_source_texts(), count_differs=args.count_differs)
        except FeedError as e:
            print(f"STOP: {e}")
            sys.exit(1)
        stash, amb, changes = {}, [], []
        it = _iter_built_app(bh_index, lex, rahlfs, tagnt, app, B.build_attestation_map(),
                             B.load_name_roster(), verse_keys, stash, amb, changes)
        print("mode: --app-feed (the build's transplant; recipients from the composed rows)")

    print("building corpus rendering reference + stashing affected verses …")
    counts, totals, affected, recon = _build_counts_and_stash(bh_index, lex, rahlfs, tagnt, it)
    print(f"  numbers with renderings: {len(totals):,}")
    if args.app_feed:
        print(f"  RECONCILE vs sizing script: {recon['total_recip']:,} total recipient slots across "
              f"{recon['verses_any']:,} verses (size_split_compounds.py --app-feed must print the same)")
        print(f"  replayed verses: {len(stash):,}; transplant tally: "
              + ", ".join(f"{k} {v:,}" for k, v in sorted(app.tally.items())))
        print(f"  AMBIGUOUS filled-slot pairings: {sum(n for _r, n in amb):,} in {len(amb):,} split runs "
              f"(expected 0; first: {amb[:5]})")
        n_chg = sum(1 for c in changes if c[2] == "changed")
        n_emp = len(changes) - n_chg
        print(f"  recipients CHANGED after the split by a later pass (head or Strong's): {n_chg:,}; "
              f"EMPTIED: {n_emp:,} - judged on the composed cell; listed in full in split_recipients_changed.tsv")
        # the replay IS the build's transplant only if it reproduces the frozen lists (§9.73, §9.75)
        try:
            app.check_merge_pairs("build")
        except FeedError as e:
            print(f"STOP: the replay is not the build's transplant - {e}")
            sys.exit(1)
    else:
        print(f"  RECONCILE vs sizing script: {recon['total_recip']:,} total recipient slots across "
              f"{recon['verses_any']:,} verses (sizing: 18,339 / 12,692)")
    content_recips = sum(len(r) for _ref, r in affected)
    print(f"  content-word recipients: {content_recips:,} across {len(affected):,} verses "
          f"(the audited subset; the rest moved function words = accepted caveat)")

    if args.control:
        sys.exit(0 if run_control(counts, totals, affected) else 1)

    # ── scope check: the function-recipient vocabulary (what the audit EXCLUDES) ──
    # If a content word hides in the hand-curated function-word lists it lands here silently,
    # exiting the audit. Dump the vocabulary sorted by frequency so it can be eyeballed once —
    # a clean list (of/and/the/his/she…) makes the 918 = whole-exposure claim airtight.
    fnvocab = recon["fnvocab"]
    Path("split_function_recipient_vocab.tsv").write_text(
        "word\tcount\n" + "\n".join(f"{w}\t{c}" for w, c in fnvocab.most_common()), encoding="utf-8")
    print(f"\n  function-recipient vocabulary: {len(fnvocab):,} distinct words "
          f"(full list -> split_function_recipient_vocab.tsv). Top 50 — eyeball for anything content-shaped:")
    line = "    "
    for w, c in fnvocab.most_common(50):
        chunk = f"{w}({c})  "
        if len(line) + len(chunk) > 100:
            print(line); line = "    "
        line += chunk
    if line.strip():
        print(line)

    if args.app_feed:
        # ── the words table: does each audited recipient read on live as the replay composed it? ──
        match, differ, rc = _vs_words(affected, stash, live)
        print("\n── content recipients vs the words table (same verse, same position) ──")
        print(f"  match:   {match:,}   (english_head and G-prefixed strongs_base equal)")
        print(f"  DIFFER:  {len(differ):,}   (full list -> split_wrong_slot_vs_words.tsv)")
        print(f"  replayed verses whose row count differs from the words table: {rc:,}")
        Path("split_wrong_slot_vs_words.tsv").write_text(
            "ref\tposition\tjudged_head\tjudged_base\tcomposed_head\tcomposed_base\tlive_head\tlive_base\n" +
            "\n".join("\t".join(str(x) for x in d) for d in differ), encoding="utf-8")
        for d in differ[:20]:
            print(f"    {d[0]}  pos {d[1]}  composed {d[4]!r}<{d[5]}>  live {d[6]!r}<{d[7]}>")
        Path("split_recipients_changed.tsv").write_text(
            "ref\tposition\tclass\tsplit_english\tsplit_head\tsplit_base\tcomposed_english\tcomposed_head\t"
            "composed_base\n" + "\n".join("\t".join("" if x is None else str(x) for x in c) for c in changes),
            encoding="utf-8")
        for c in changes[:20]:
            print(f"    {c[0]}  pos {c[1]}  {c[2]}: split {c[4]!r}<{c[5]}>  composed {c[7]!r}<{c[8]}>")

    flags = []
    recip_total = 0
    unadj_slots, unadj_nums = 0, set()          # recipients on numbers below the >= MIN_FREQ gate
    for ref, recips in affected:
        recip_total += len(recips)
        flags.extend(_flag_recips(recips, counts, totals, ref))
        for _pos, _head, base in recips:
            if base and base[0].isdigit() and totals.get(base, 0) < MIN_FREQ:
                unadj_slots += 1
                unadj_nums.add(base)

    print("\n── wrong-slot certification (split RECIPIENT slots only) ──")
    print(f"  verses checked:      {len(affected):,}")
    print(f"  split recipients:    {recip_total:,}  (slots the split moved a word INTO — the audit scope)")
    print(f"  UNADJUDICATED:       {unadj_slots:,} recipients on {len(unadj_nums):,} rare "
          f"(< {MIN_FREQ}-use) numbers — not judged here; covered by the 60-sample + BibleHub leg")
    print(f"  RAW FLAGS:           {len(flags):,}  (candidate generator — NOT a verdict; triaged below)")

    Path(args.out).write_text(
        "ref\tposition\trendering\tstrongs_base\n" +
        "\n".join(f"{r}\t{p}\t{h}\t{b}" for r, p, h, b in flags), encoding="utf-8")

    # ── triage: strip the known false-positive classes, leave a residue to sample ──
    b = _triage(flags, counts, lex, dodson)
    residue = b["residue"]
    print("\n── triage (each filter uses a reference where it's strong) ──")
    print(f"  dropped — numeral numbers:   {len(b['numeral']):,}")
    print(f"  dropped — word in gloss:     {len(b['in_lexicon']):,}  (odd wording, but the word means this number)")
    print(f"  dropped — stemmer stumps:    {len(b['stump']):,}  (truncated form of a word the number carries)")
    print(f"  RESIDUE (real candidates):   {len(residue):,}")

    Path("split_wrong_slot_residue.tsv").write_text(
        "ref\tposition\trendering\tstrongs_base\ttop_renderings\n" +
        "\n".join(f"{r}\t{p}\t{h}\t{bs}\t" +
                  ", ".join(f"{k}:{v}" for k, v in counts[bs].most_common(5))
                  for r, p, h, bs in residue), encoding="utf-8")
    print(f"  full flag list -> {args.out}   residue -> split_wrong_slot_residue.tsv")

    if not flags:
        print("\n  CLEAN — no content word is a rare (< 3x) rendering of a well-attested number.")
        print("  Freeze-as-overlay CERTIFIED corpus-wide (within the frequency-floor limit above).")
    elif residue:
        # even spread across the residue for an unbiased BibleHub true-positive sample
        N = 40
        step = max(1, len(residue) // N)
        print(f"\n  {min(N, len(residue))} residue samples for BibleHub check "
              f"(is the word really on the wrong Greek word? top renderings show what the number normally carries):")
        for r, p, h, bs in residue[::step][:N]:
            top = ", ".join(f"{k}:{v}" for k, v in counts[bs].most_common(4))
            print(f"    {r}  pos {p}  {h!r} on {bs}   [{bs} normally: {top}]")
        print("\n  NEXT: verify these against BibleHub, count true wrong-slots, "
              "that rate x residue = the real estimate that goes against the bar.")
    if args.app_feed:
        print(f"\n  L9 --app-feed RESULT: recipients {recon['total_recip']:,} in {recon['verses_any']:,} verses; "
              f"content {recip_total:,}; RAW FLAGS {len(flags):,}; RESIDUE {len(residue):,}; "
              f"vs words: match {match:,}, DIFFER {len(differ):,}; ambiguous {sum(n for _r, n in amb):,}; "
              f"changed after split {n_chg:,}, emptied {n_emp:,}")


if __name__ == "__main__":
    main()
