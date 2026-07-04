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
    holder = {"recips": [], "nrecip": 0}

    def wrapped(rows, lexicon, carry=False):
        before_ne = sum(1 for r in rows if (r[1] or "").strip())
        # heads present per base BEFORE the split (the source slots' own words)
        before = defaultdict(Counter)
        for r in rows:
            if r[2]:
                before[r[4]][r[2]] += 1
        real_split(rows, lexicon, carry)
        after_ne = sum(1 for r in rows if (r[1] or "").strip())
        # TOTAL recipient slots the split filled (incl function words) — reconciles with the
        # sizing script's net-non-empty-increase count (~18,339).
        holder["nrecip"] = max(0, after_ne - before_ne)
        # CONTENT recipients: a head now present on a base BEYOND its before-count. A function
        # word ("of"/"and") lands with head None, so it is excluded here by construction — the
        # accepted caveat, out of the wrong-slot audit but still counted in nrecip above.
        seen = defaultdict(Counter)
        recips = []
        for r in rows:
            if not r[2]:
                continue
            base, head = r[4], r[2]
            seen[base][head] += 1
            if seen[base][head] > before[base].get(head, 0):
                recips.append((r[0], head, base))
        holder["recips"] = recips
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
        rows = B.build_verse_words(abp_words, bh_rows, lex)
        yield f"{abbrev} {ch}:{vs}", rows, holder["recips"], holder["nrecip"]


def _build_counts_and_stash(bh_index, lex, rahlfs, tagnt):
    """One pass: tally every number's renderings across the WHOLE corpus (the reference —
    all slots), and stash the split RECIPIENTS of affected verses (what we certify)."""
    counts = defaultdict(Counter)
    totals = Counter()
    affected = []
    recon = {"total_recip": 0, "verses_any": 0}      # reconciliation vs the sizing script
    for ref, rows, recips, nrecip in _iter_built(bh_index, lex, rahlfs, tagnt, want_affected=True):
        for _pos, hf, base in _content_slots(rows):
            counts[base][hf] += 1
            totals[base] += 1
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
    args = ap.parse_args()

    import sqlite3
    ro = sqlite3.connect(f"file:{args.bible_db}?mode=ro", uri=True)
    lex = B.load_lexicon(ro)                        # used by the split's own passes + the triage noise filter
    dodson = _load_dodson(ro)                       # word_gloss (Dodson/Strong's-Hebrew) for the noise filter
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

    print("building corpus rendering reference + stashing affected verses …")
    counts, totals, affected, recon = _build_counts_and_stash(bh_index, lex, rahlfs, tagnt)
    print(f"  numbers with renderings: {len(totals):,}")
    print(f"  RECONCILE vs sizing script: {recon['total_recip']:,} total recipient slots across "
          f"{recon['verses_any']:,} verses (sizing: 18,339 / 12,692)")
    content_recips = sum(len(r) for _ref, r in affected)
    print(f"  content-word recipients: {content_recips:,} across {len(affected):,} verses "
          f"(the audited subset; the rest moved function words = accepted caveat)")

    if args.control:
        sys.exit(0 if run_control(counts, totals, affected) else 1)

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


if __name__ == "__main__":
    main()
