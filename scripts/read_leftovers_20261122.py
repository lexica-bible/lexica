#!/usr/bin/env python3
"""One read-only pass over the leftovers the ruling chat named 11/22 (DESIGN 9.254).

  1. every word-card header, through the site's own route         -> headers.tsv
  2. the hand overrides in word_gloss against build_word_gloss.py -> printed
  3. KJV verses whose Strong's tags sit one word off              -> kjv_shift.tsv
  4. dictionary-card prose that still carries the old English     -> prose_hits.tsv

Every database is opened read-only (mode=ro), so nothing here can change one. It writes only the
report files in --out. Each detector proves itself on a known case in the same run.

  python3 -u read_leftovers_20261122.py --out DIR [--repo ~/bible-db] [--old ROLLBACK.db]
"""
import argparse
import ast
import importlib.util
import json
import os
import re
import sqlite3
import sys
import time
from collections import Counter

# ---- the KJV shift rule (pure) ------------------------------------------------------------------

_WORD = re.compile(r"[^a-z0-9]+")
FIT_MIN = 2             # a word and a tag "fit" when seen together at least twice, and...
FIT_TAG_SHARE = 0.02    # ...that is 2% of the tag's uses, or
FIT_WORD_SHARE = 0.10   # ...10% of the word's tagged uses
STRONG_RUN = 3          # 3+ tags in a row that fit the next-door word and not their own


def kjv_key(w):
    return _WORD.sub("", (w or "").lower())


class Fit:
    """How often each English word carries each tag across the whole KJV."""

    def __init__(self):
        self.pair, self.tag, self.word = Counter(), Counter(), Counter()

    def add(self, w, tags):
        for t in tags:
            self.pair[(w, t)] += 1
            self.tag[t] += 1
            self.word[w] += 1

    def fits(self, w, t):
        n = self.pair.get((w, t), 0)
        if n < FIT_MIN:
            return False
        return n / self.tag[t] >= FIT_TAG_SHARE or n / self.word[w] >= FIT_WORD_SHARE


def shift_runs(tokens, fit):
    """tokens = [(word key, [tags])] in reading order. -> [(direction, how many tags, first index,
    last index)]. A run is a stretch of tagged words none of which fits its own tag; it is counted
    by how many of them fit the word just before (late) or just after (early)."""
    out = []
    late = early = 0
    first = last = None

    def close():
        nonlocal late, early, first, last
        if first is not None and max(late, early) >= 2:
            out.append(("late" if late >= early else "early", max(late, early), first, last))
        late = early = 0
        first = last = None

    for i, (w, tags) in enumerate(tokens):
        if not tags:
            continue
        if any(fit.fits(w, t) for t in tags):
            close()
            continue
        first = i if first is None else first
        last = i
        if i > 0 and any(fit.fits(tokens[i - 1][0], t) for t in tags):
            late += 1
        if i + 1 < len(tokens) and any(fit.fits(tokens[i + 1][0], t) for t in tags):
            early += 1
    close()
    return out


# ---- the old-English prose rule (pure) ----------------------------------------------------------

_REF = re.compile(r"\b([1-3]?[A-Z][a-z]{1,2}) (\d+):(\d+)")
_QUOTE = re.compile(r"“([^”]{1,200})”|‘([^’]{1,200})’|\"([^\"]{1,200})\"")
NEAR = 120              # a quoted word belongs to a verse cited within this many characters
MIN_RUN = 3             # words in a row shared with the old text of a cited verse


def prose_norm(s):
    s = (s or "").lower().replace("’", "'")
    return " ".join(re.sub(r"[^a-z0-9']+", " ", s).split())


def _has(hay, phrase):
    return f" {phrase} " in hay


def old_only_runs(prose, old, new):
    """Runs of MIN_RUN+ words in the prose that are in the verse's old text and not its new text."""
    words = prose_norm(prose).split()
    o, n = f" {prose_norm(old)} ", f" {prose_norm(new)} "
    hits, i = [], 0
    while i < len(words):
        j = i
        while j < len(words) and _has(o, " ".join(words[i:j + 1])):
            j += 1
        if j - i >= MIN_RUN:
            phrase = " ".join(words[i:j])
            if not _has(n, phrase):
                hits.append(phrase)
                i = j
                continue
        i += 1      # a run still in today's text can overlap an old-only one: step one word only
    return hits


def quotes_in(text):
    for m in _QUOTE.finditer(text):
        q = prose_norm(next(g for g in m.groups() if g is not None))
        if q:
            yield q, m.start()


def card_strings(node, skip=("raw", "verses", "audit", "coverage_audit")):
    """Every piece of text the card shows; never the raw model text or the stored verse copies."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, list):
        for x in node:
            yield from card_strings(x, skip)
    elif isinstance(node, dict):
        for k, v in node.items():
            if k not in skip:
                yield from card_strings(v, skip)


def prose_hits(strings, cited, old, new, old_all, new_all):
    """-> [(test, ref or '', phrase)]. `old`/`new` = {ref: verse text}; *_all = the whole Bible."""
    hits, seen = [], set()

    def add(*h):
        if h not in seen:
            seen.add(h)
            hits.append(h)

    joined = "\n".join(strings)
    for ref in sorted(cited):
        if ref in old and ref in new and prose_norm(old[ref]) != prose_norm(new[ref]):
            for s in strings:
                for phrase in old_only_runs(s, old[ref], new[ref]):
                    add("run", ref, phrase)
    for s in strings:
        refs = [(m.start(), f"{m.group(1)} {m.group(2)}:{m.group(3)}") for m in _REF.finditer(s)]
        for q, at in quotes_in(s):
            if " " in q and _has(old_all, q) and not _has(new_all, q):
                add("quote-only-in-old", "", q)
            for pos, ref in refs:
                if abs(pos - at) <= NEAR and ref in old and ref in new \
                        and _has(f" {prose_norm(old[ref])} ", q) and not _has(f" {prose_norm(new[ref])} ", q):
                    add("quote-near-ref", ref, q)
    return hits if joined else []


# ---- reading the databases ----------------------------------------------------------------------

def ro(path):
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    c.execute("PRAGMA busy_timeout = 5000")
    return c


def beat(label, n, total, every):
    if n % every == 0:
        print(f"  ... {label} {n:,} of {total:,}", flush=True)


def production_function_words(repo, core):
    """The site's own function-word set, run from app.py's own code. app.py itself is not imported:
    importing it starts the app's startup steps, and this pass must only read."""
    with open(os.path.join(repo, "app.py"), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    want = {"_LSJ_FUNC_WORD_RE", "_LSJ_FUNC_BOLD_RE", "_FUNCTION_STRONGS_OVERRIDE",
            "_is_lsj_function_word", "_compute_function_strongs_from_db"}
    ns = {"re": re, "db": core.db_ro}
    got = set()
    for n in tree.body:
        name = None
        if isinstance(n, ast.FunctionDef):
            name = n.name
        elif isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
            name = n.targets[0].id
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            name = n.target.id
        if name in want:
            exec(compile(ast.Module([n], type_ignores=[]), "app.py", "exec"), ns)
            got.add(name)
    if got != want:
        raise SystemExit(f"app.py is missing {sorted(want - got)}")
    return set(ns["_compute_function_strongs_from_db"]()) | set(ns["_FUNCTION_STRONGS_OVERRIDE"])


_ID = re.compile(r"^([GH])(\d+(?:\.\d+)*)([A-Za-z]?)$")


def card_ids(conn, core):
    """Every Strong's number a word card can open on: ABP, KJV, BSB, Hebrew."""
    ids, odd = set(), Counter()

    def take(raw, where):
        m = _ID.match((raw or "").strip())
        if not m:
            odd[where] += 1
            return
        ids.add(f"{m.group(1)}{m.group(2)}" if m.group(1) == "H" else raw.strip())

    for st, sb in conn.execute("SELECT DISTINCT strongs, strongs_base FROM words"):
        if not st or st == "*" or not sb or sb == "*":
            continue
        take((sb[0] + st) if st[0].isdigit() else st, "words")
    for t in ("kjv_strongs", "bsb_strongs"):
        try:
            for (s,) in conn.execute(f"SELECT DISTINCT strongs_id FROM {t}"):
                take(s, t)
        except sqlite3.OperationalError:
            odd[f"{t} missing"] += 1
    try:
        h = core.heb_db()
        for (s,) in h.execute("SELECT DISTINCT strongs FROM heb_words WHERE strongs GLOB 'H*'"):
            take(s, "heb_words")
        h.close()
    except sqlite3.OperationalError:
        odd["heb_words missing"] += 1
    return ids, odd


def _id_order(s):
    return (s[0], [int(x) for x in re.findall(r"\d+", s)], s)


HEADER_CONTROLS = {
    "G4151": {"short_meaning": "spirit, wind, breath"},
    "H7307": {"short_meaning": "spirit, wind, breath"},
    "H5315": {"short_meaning": "self, life, person"},
    "G4160": {"short_meaning": "do, make"},
    "G5484": {"reviewed_gloss": "favor, kindness, goodwill"},
    "G3756": {},    # a function word
    "G1138": {},    # a name
}


def section_headers(args, conn):
    print("=== 1 WORD-CARD HEADERS ===", flush=True)
    sys.path.insert(0, args.repo)
    from flask import Flask
    import core
    core.DB = args.db
    core.HEB_DB = args.heb
    import short_meaning as M
    import views_lexicon as VL
    funcs = production_function_words(args.repo, core)
    core._FUNCTION_STRONGS.clear()
    core._FUNCTION_STRONGS.update(funcs)
    if VL._FUNCTION_STRONGS is not core._FUNCTION_STRONGS:
        raise SystemExit("the function-word set is not shared")
    print(f"function words: {len(funcs):,} (the site's own rule, run read-only)")

    seen_rows, errors = [], []
    real_from_counts, real_header = M.from_counts, VL._header_meaning

    def rec_counts(rows):
        seen_rows[:] = list(rows)
        return real_from_counts(rows)

    def rec_header(*a, **k):
        try:
            return real_header(*a, **k)
        except Exception as e:      # the route hides errors as an empty answer; this run must not
            errors.append((a[1], repr(e)))
            raise

    M.from_counts, VL._header_meaning = rec_counts, rec_header
    app = Flask("leftover_reads")
    app.register_blueprint(VL.bp)
    client = app.test_client()

    def ask(sid):
        seen_rows[:] = []
        VL._MEANING_CACHE.clear()       # a remembered answer would skip the count list
        return json.loads(client.get(f"/api/lexicon/short-meaning/{sid}").get_data(as_text=True))

    bad = 0
    for sid, want in HEADER_CONTROLS.items():
        got = ask(sid)
        ok = got == want
        bad += not ok
        print(f"  [{'PASS' if ok else 'FAIL'}] control {sid}: {got}")

    stored = {r[0]: (r[1] or "") for r in conn.execute("SELECT strongs, gloss FROM word_gloss")}
    lemma = {f"G{r[0]}": r[1] for r in conn.execute("SELECT strongs, lemma FROM lexicon")}
    for sql in ("SELECT strongs, lemma FROM dotted_lexicon", "SELECT strongs_id, lemma FROM bdb"):
        try:
            lemma.update({r[0]: r[1] for r in conn.execute(sql)})
        except sqlite3.OperationalError:
            pass
    ids, odd = card_ids(conn, core)
    ordered = sorted(ids, key=_id_order)
    print(f"numbers to read: {len(ordered):,}; not a card number: {dict(odd) or 'none'}", flush=True)
    kinds = Counter()
    with open(os.path.join(args.out, "headers.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("number\tkind\tlemma\theader\tstored_gloss\ttop_renderings\n")
        for n, sid in enumerate(ordered, 1):
            got = ask(sid)
            if "short_meaning" in got:
                kind, head = "counts", got["short_meaning"]
            elif "reviewed_gloss" in got:
                kind, head = "kept", got["reviewed_gloss"]
            else:
                kind, head = "stored", ""
            kinds[kind] += 1
            top = " ".join(f"{g.replace(' ', '_')}:{c}" for g, c in seen_rows[:8])
            row = (sid, kind, lemma.get(sid) or "", head, stored.get(sid, ""), top)
            f.write("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in row) + "\n")
            beat("headers", n, len(ordered), 1000)
    M.from_counts, VL._header_meaning = real_from_counts, real_header
    print(f"headers: {dict(kinds)}; route errors: {len(errors)} {errors[:5]}")
    print(f"HEADER CONTROLS: {'ALL PASS' if not bad else str(bad) + ' FAILED - do not trust this list'}", flush=True)
    if bad or errors:
        args.failed.append("headers")


def section_overrides(args, conn):
    print("=== 2 HAND OVERRIDES IN word_gloss ===", flush=True)
    keep = sys.argv
    sys.argv = ["build_word_gloss.py"]      # its options are read from the command line on load
    try:
        spec = importlib.util.spec_from_file_location(
            "build_word_gloss_ro", os.path.join(args.repo, "scripts", "build_word_gloss.py"))
        B = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(B)
    finally:
        sys.argv = keep
    want = {}
    for d, pre in ((B.OVERRIDES, "G"), (B.HEBREW_OVERRIDES, "H"), (B.DOTTED_OVERRIDES, "G")):
        for k, v in d.items():
            want[k if k[0] in "GH" else pre + k] = v
    have = {r[0]: (r[1], r[2]) for r in conn.execute("SELECT strongs, gloss, source FROM word_gloss")}
    off = [(k, v, have.get(k)) for k, v in sorted(want.items())
           if have.get(k) is None or have[k][0] != v or have[k][1] != "override"]
    print(f"overrides in the file: {len(want)}; matching live: {len(want) - len(off)}; differing: {len(off)}")
    for k, v, h in off:
        print(f"  DIFF {k}: file {v!r} / live {h!r}")


JOH_7_1 = (43, 7, 1)    # had every tag one word late until the 11/22 batch fixed it


def verse_tokens(conn, key):
    rows = conn.execute("""SELECT w.word, GROUP_CONCAT(s.strongs_id) FROM kjv_words w
                           LEFT JOIN kjv_strongs s ON s.word_id = w.word_id
                           WHERE w.book_id = ? AND w.chapter = ? AND w.verse_num = ?
                           GROUP BY w.word_id ORDER BY w.verse_pos""", key).fetchall()
    return [(kjv_key(w), (t or "").split(",") if t else []) for w, t in rows]


def section_kjv(args, conn):
    print("=== 3 KJV ONE-WORD TAG SHIFT ===", flush=True)
    sql = """SELECT w.book_id, w.chapter, w.verse_num, w.verse_pos, w.word, GROUP_CONCAT(s.strongs_id)
             FROM kjv_words w LEFT JOIN kjv_strongs s ON s.word_id = w.word_id
             GROUP BY w.word_id ORDER BY w.book_id, w.chapter, w.verse_num, w.verse_pos"""
    fit = Fit()
    n = 0
    for _b, _c, _v, _p, w, t in conn.execute(sql):
        if t:
            fit.add(kjv_key(w), t.split(","))
        n += 1
        beat("KJV words counted", n, 800000, 200000)
    print(f"KJV words: {n:,}; tagged pairs: {len(fit.pair):,}", flush=True)

    # The control: the same rule on the old copy of Joh 7:1 must fire; on today's copy must not.
    old_runs = []
    if args.old and os.path.exists(args.old):
        oc = ro(args.old)
        old_runs = shift_runs(verse_tokens(oc, JOH_7_1), fit)
        oc.close()
        print(f"  control, Joh 7:1 before the fix: {old_runs}")
    else:
        print("  control, Joh 7:1 before the fix: NO OLD COPY")
    new_runs = shift_runs(verse_tokens(conn, JOH_7_1), fit)
    print(f"  control, Joh 7:1 today: {new_runs}")
    fired = any(d == "late" and c >= 10 for d, c, _a, _b in old_runs)
    ok = fired and not new_runs
    print(f"KJV CONTROL: {'PASS' if ok else 'FAILED - do not trust the count below'}", flush=True)
    if not ok:
        args.failed.append("kjv")

    tiers, verses_strong, verses_any = Counter(), set(), set()
    cur, toks, shown = None, [], []

    def flush(out):
        for d, c, a, b in shift_runs(toks, fit):
            tier = "strong" if c >= STRONG_RUN else "weak"
            tiers[tier] += 1
            verses_any.add(cur)
            if tier == "strong":
                verses_strong.add(cur)
            text = " ".join(f"{w}[{'+'.join(t)}]" if t else w for w, t in shown)
            out.write(f"{cur[0]}\t{cur[1]}\t{cur[2]}\t{tier}\t{d}\t{c}\t{a}\t{b}\t{text}\n")

    with open(os.path.join(args.out, "kjv_shift.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("book_id\tchapter\tverse\ttier\tdirection\ttags_in_run\tfirst_word\tlast_word\tverse_with_tags\n")
        for b, c, v, _p, w, t in conn.execute(sql):
            if (b, c, v) != cur:
                if cur:
                    flush(f)
                cur, toks, shown = (b, c, v), [], []
            tags = t.split(",") if t else []
            toks.append((kjv_key(w), tags))
            shown.append((w, tags))
        if cur:
            flush(f)
    print(f"KJV SHIFT: {len(verses_strong):,} verses with 3+ tags off by one; "
          f"{len(verses_any - verses_strong):,} more with only 2 (to be read, most will be chance)", flush=True)


def section_prose(args, conn):
    print("=== 4 DICTIONARY-CARD PROSE vs THE OLD ENGLISH ===", flush=True)
    if not (args.old and os.path.exists(args.old)):
        print("PROSE: NO OLD COPY - not checked")
        args.failed.append("prose")
        return
    def texts(c):
        return {f"{b} {ch}:{v}": t or "" for b, ch, v, t in c.execute("SELECT book, chapter, verse, text FROM verses")}
    oc = ro(args.old)
    old = texts(oc)
    oc.close()
    new = texts(conn)
    changed = {r for r in old if r in new and prose_norm(old[r]) != prose_norm(new[r])}
    print(f"verses: old {len(old):,}, today {len(new):,}, wording differs in {len(changed):,}", flush=True)
    old_all = " \n " + " \n ".join(prose_norm(t) for t in old.values()) + " \n "
    new_all = " \n " + " \n ".join(prose_norm(t) for t in new.values()) + " \n "
    cards = conn.execute("SELECT strongs, def_json FROM lexica_def").fetchall()
    total, cards_hit, control = 0, 0, None
    with open(os.path.join(args.out, "prose_hits.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("card\ttest\tref\tphrase\told_verse\tverse_today\n")
        for sid, raw in cards:
            try:
                e = json.loads(raw)
            except (TypeError, ValueError):
                print(f"  card {sid}: unreadable")
                continue
            strings = [s for s in card_strings(e) if len(s) > 2]
            cited = {v.get("ref") for v in (e.get("verses") or []) if isinstance(v, dict) and v.get("ref")}
            for s in strings:
                cited |= {f"{m.group(1)} {m.group(2)}:{m.group(3)}" for m in _REF.finditer(s)}
            if control is None:
                for r in sorted(cited & changed):
                    w = prose_norm(old[r]).split()
                    for i in range(len(w) - MIN_RUN + 1):
                        p = " ".join(w[i:i + MIN_RUN])
                        if not _has(f" {prose_norm(new[r])} ", p):
                            control = (r, p)
                            break
                    if control:
                        break
            hits = prose_hits(strings, cited, old, new, old_all, new_all)
            cards_hit += bool(hits)
            total += len(hits)
            for test, ref, phrase in hits:
                f.write("\t".join((sid, test, ref, phrase, old.get(ref, ""), new.get(ref, ""))).replace("\n", " ") + "\n")
    if control:
        r, p = control
        fires = bool(prose_hits([f"as the verse puts it, {p}, in plain words"], {r}, old, new, old_all, new_all))
        quiet = not prose_hits([new[r]], {r}, old, new, old_all, new_all)
        print(f"  control on {r}: old wording {'fired' if fires else 'DID NOT FIRE'}; "
              f"today's wording {'stayed quiet' if quiet else 'FIRED'}")
        print(f"PROSE CONTROL: {'PASS' if fires and quiet else 'FAILED - do not trust the count below'}")
        if not (fires and quiet):
            args.failed.append("prose")
    else:
        print("PROSE CONTROL: VOID - no cited verse changed")
        args.failed.append("prose")
    print(f"PROSE: {len(cards)} cards read; {cards_hit} carry a possible old wording; {total} places listed", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--repo", default=os.path.expanduser("~/bible-db"))
    ap.add_argument("--db", default=None)
    ap.add_argument("--heb", default=None)
    ap.add_argument("--old", default=os.path.expanduser("~/bible-db/bible_pre_edition_upgrade_20261121.db"))
    args = ap.parse_args()
    args.db = args.db or os.path.join(args.repo, "bible.db")
    args.heb = args.heb or os.path.join(args.repo, "heb.db")
    args.failed = []
    os.makedirs(args.out, exist_ok=True)
    conn = ro(args.db)
    for name, fn in (("headers", section_headers), ("overrides", section_overrides),
                     ("kjv", section_kjv), ("prose", section_prose)):
        t = time.time()
        fn(args, conn)
        print(f"({name}: {time.time() - t:.0f} s)", flush=True)
    conn.close()
    if args.failed:
        print(f"READS FINISHED WITH A FAILED CONTROL: {', '.join(args.failed)} - nothing was written to any database")
        sys.exit(2)
    print("READS DONE - nothing was written to any database")


if __name__ == "__main__":
    main()
