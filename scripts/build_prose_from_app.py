#!/usr/bin/env python3
"""
build_prose_from_app.py — DERIVATION B of the edition upgrade: English prose (verses.text)
from the frozen ABP app feed (docs/handoffs/DESIGN_q2_build.md §2, §9.3, §9.7, §9.8,
§9.48–§9.57).

WHAT IT DOES, per verse that A's eligible_<date>.tsv marks eligible (§9.48 — A owns
eligibility; B never reads A's rows or text, only that keys file):
  * reads the feed itself through abp_app_feed (sha + size pin), via AppTransplant's own
    feed read and normalizations (§9.49 — shared CODE, not output): end-of-cell " -" -> " --"
    (pinned 4,248) and space folding (pinned 12,480);
  * joins the verse's feed English cells in slot order and runs load_abp_prose.clean_verse
    UNCHANGED (§9.3 reorder_bracket; §9.54) — counting each cleanup rule's fires on feed text;
  * compares with the copy's current verses.text AFTER the step-5 em-dash swap ("--" -> "—",
    fix_emdash.py:49), and writes ONLY where they differ (§9.55). It writes the "--" form;
    finish_rebuild step 5 swaps it like every other prose dash.
Ineligible verses keep their old prose untouched (the reason is A's, carried in the TSV).

SAFETY:
  * the target is a db COPY given explicitly; the live path (~/bible-db/bible.db) is refused
    outright, as is a missing or empty path (§9.57). No default.
  * §9.8: the 33 cured correction rows are retired on the copy BEFORE B runs. An ACTIVE
    verses.text correction row on an eligible verse = STOP (a cured row not retired) — with ONE
    exception (§9.79): the row's source_value is EXACTLY the text B writes on that verse (the
    edition-upgrade EU- rows, keyed to B's own output and applied after it at finish_rebuild
    step 4b). Exact means byte-for-byte; a whitespace-only difference still stops. Matched rows
    are counted on the summary line. The 6 still-present verses are ineligible in A (§9.51).
  * before anything is written, B re-checks every eligible verse against its own decide()
    on the same frozen inputs; a verse A marked eligible that decide() rejects = STOP
    (the eligible file came from different inputs).
  * journal_mode=DELETE + busy_timeout on the write connection (CLAUDE.md: never WAL on PA).

MODES:
  python3 scripts/build_prose_from_app.py --eligible E.tsv --dry-run COPY_DB [--out DIR]
      read-only (mode=ro), writes nothing; counts + prose_<date>.tsv to --out.
  python3 scripts/build_prose_from_app.py --eligible E.tsv --dry-run-nodb [--out DIR]
      LOCAL: no db; "old" = load_abp_prose.clean_verse over abp_texts/ + the em-dash swap
      (a proxy for the copy's text: no corrections) — NOT the build's figures.
  python3 scripts/build_prose_from_app.py --eligible E.tsv --apply COPY_DB [--out DIR]
      writes verses.text on the COPY for the differing eligible verses.
Exit 0 = done; 1 = STOP (reason printed).
"""
import argparse
import collections
import contextlib
import csv
import io
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import load_abp_prose as P                                          # noqa: E402
from build_words_from_abp import AppTransplant, abp_source_texts   # noqa: E402
from abp_app_feed import FeedError                                  # noqa: E402

LIVE_DB = Path.home() / "bible-db" / "bible.db"
_BRACKET = re.compile(r'\[([^\]]+)\](?:G[\d.]+\*?)?')               # load_abp_prose.py:49
_STRAY_G = re.compile(r'G(?![A-Za-z\d*])\.?')                       # load_abp_prose.py:55
_LEAK = re.compile(r'(?<!\w)\d+(?=[A-Za-z])')                       # load_abp_prose.py:59


def emdash(text):
    """finish_rebuild step 5's swap (fix_emdash.py:49), for like-for-like comparison."""
    return (text or "").replace("--", "—")


def clean_counted(raw, ref, fires):
    """load_abp_prose.clean_verse(raw) - the production function, unchanged - plus a count of
    which of its cleanup rules (:55 stray G, :59 leaked digit, :63-65 stray bracket) fired.
    The staged count is checked against clean_verse's own output, so it cannot drift."""
    t = _BRACKET.sub(P.reorder_bracket, raw)
    t = P.G_NUM_RE.sub("", t)
    if _STRAY_G.search(t):
        fires["stray_G"] += 1
    t = _STRAY_G.sub("", t)
    if _LEAK.search(t):
        fires["leaked_digit"] += 1
    t = _LEAK.sub("", t)
    if "[" in t or "]" in t:
        fires["stray_bracket"] += 1
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        out = P.clean_verse(raw, ref=ref)
    staged = re.sub(r"\s+", " ", re.sub(r"[\[\]]", "", t)).strip()
    if staged != out:
        raise FeedError(f"{ref}: staged cleanup count drifted from clean_verse")
    return out


def feed_text(app, key, fires=None):
    """B's text for one eligible verse key (before the em-dash swap): the verse's feed English
    cells, normalized by AppTransplant, joined in slot order, through clean_counted. The ONE place
    this is computed - run() uses it, and so does eu_retired_check.py (§9.81)."""
    ka = app.pairs[key]
    joined = " ".join(app.norm[(ka[0], ka[1], ka[2], s["slot_index"])] for s in app.feed[ka])
    return clean_counted(joined, f"{key[0]} {key[1]}:{key[2]}",
                         fires if fires is not None else collections.Counter())


def load_eligible(path):
    p = Path(path)
    if not p.is_file():
        raise FeedError(f"eligible file not found: {p}")
    out = {}
    with open(p, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            out[(r["book"], int(r["chapter"]), int(r["verse"]))] = (r["eligible"] == "1", r["reason"])
    return out


def check_target(path):
    """The copy path: explicit, existing, never the live db (§9.57)."""
    if not path:
        raise FeedError("a copy db path is required (no default)")
    p = Path(path).expanduser()
    if not p.is_file():
        raise FeedError(f"copy db not found: {p}")
    if p.resolve() == LIVE_DB.resolve():
        raise FeedError(f"refusing the LIVE db {LIVE_DB} - B only ever writes a copy")
    return p


def run(eligible_path, copy=None, apply=False, out_dir=None, stamp="20261031", app=None, src=None):
    """-> (counts, rows). copy=None = local no-db mode (old text = clean_verse over abp_texts)."""
    eligible = load_eligible(eligible_path)
    src = src if src is not None else abp_source_texts()
    app = app if app is not None else AppTransplant(src)
    # the eligible file must agree with decide() on these same frozen inputs
    for k, (ok, _r) in eligible.items():
        if ok and app.decide(k)[0] != "compose":
            raise FeedError(f"{k}: eligible in A's file but decide() rejects it - inputs differ")
    old, active = {}, collections.defaultdict(list)    # verse -> [(source_value, ledger_ref)]
    if copy is not None:
        con = sqlite3.connect(f"file:{copy}?mode=ro", uri=True)
        try:
            old = {(b, c, v): t for b, c, v, t in con.execute("SELECT book, chapter, verse, text FROM verses")}
            if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='abp_corrections'").fetchone():
                for b, c, v, src_val, ref in con.execute(
                        "SELECT book, chapter, verse, source_value, ledger_ref FROM abp_corrections "
                        "WHERE status='active' AND field='verses.text'"):
                    active[(b, c, v)].append((src_val, ref))
        finally:
            con.close()
    counts, fires = collections.Counter(), collections.Counter()
    rows, writes = [], []
    for k, (ok, reason) in eligible.items():       # A's file order (canonical book order)
        if not ok:
            counts["kept_old:" + reason] += 1
            rows.append((k, "kept_old", reason, "", "", ""))
            continue
        new = feed_text(app, k, fires)
        if copy is not None:
            if k not in old:
                raise FeedError(f"{k}: eligible verse has no verses row on the copy")
            prev = old[k]
        else:
            with contextlib.redirect_stderr(io.StringIO()):
                prev = emdash(P.clean_verse(src[k], ref=str(k)))
        if k in active:
            # §9.79: allowed ONLY when B writes this verse and every active row's source_value is
            # exactly B's text (a correction keyed to B's own output); anything else is a cured
            # row that was never retired (§9.8) - STOP, as before.
            writes_it = emdash(new) != (prev or "")
            if not writes_it or any(sv != new for sv, _ref in active[k]):
                raise FeedError(f"{k}: an ACTIVE verses.text correction row on a verse B would write "
                                f"whose source_value is not exactly B's text (sec 9.8 / 9.79: cured "
                                f"rows must be retired before B)")
            counts["corrections:matched_written"] += len(active[k])
            counts["corrections:matched_written_eu"] += sum(1 for _sv, ref in active[k]
                                                            if (ref or "").startswith("EU-"))
        if emdash(new) == (prev or ""):
            counts["unchanged"] += 1
            rows.append((k, "unchanged", "", len(prev or ""), len(new), "no"))
        else:
            counts["written"] += 1
            rows.append((k, "written", "", len(prev or ""), len(new), "yes"))
            writes.append((new, k[0], k[1], k[2]))
    counts.update({f"fires:{x}": fires[x] for x in ("stray_G", "leaked_digit", "stray_bracket")})
    counts["corrections:active_prose_rows_on_copy"] = len(active)
    counts["corrections:carveout_kept"] = sum(1 for ok, r in eligible.values() if r == "correction")
    if apply:
        con = sqlite3.connect(str(copy))
        try:
            con.execute("PRAGMA journal_mode=DELETE")
            con.execute("PRAGMA busy_timeout=5000")
            con.executemany("UPDATE verses SET text = ? WHERE book = ? AND chapter = ? AND verse = ?", writes)
            con.commit()
        finally:
            con.close()
        counts["applied"] = len(writes)
    if out_dir:
        d = Path(out_dir).expanduser()
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"prose_{stamp}.tsv"
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("book\tchapter\tverse\toutcome\treason\told_len\tnew_len\tchanged\n")
            for (b, c, v), o, r, ol, nl, ch in rows:
                f.write(f"{b}\t{c}\t{v}\t{o}\t{r}\t{ol}\t{nl}\t{ch}\n")
        counts["_tsv"] = str(p)
    return counts, rows


def report(counts, label):
    print(f"-- derivation B prose ({label}) --")
    print(f"  written {counts['written']:,} - unchanged (identical after em-dash swap) {counts['unchanged']:,}")
    kept = {k.split(':', 1)[1]: n for k, n in counts.items() if k.startswith("kept_old:")}
    print(f"  kept old {sum(kept.values()):,}: " + " - ".join(f"{r} {n:,}" for r, n in sorted(kept.items())))
    print(f"  clean_verse cleanup fires on feed text: stray_G {counts['fires:stray_G']} - "
          f"leaked_digit {counts['fires:leaked_digit']} - stray_bracket {counts['fires:stray_bracket']}"
          f" (expected 0 / - / 0, sec 9.54)")
    print(f"  corrections: carve-out kept {counts['corrections:carveout_kept']} - active prose rows "
          f"on the copy {counts['corrections:active_prose_rows_on_copy']} (none may sit on a written verse "
          f"unless its source_value is exactly B's text, sec 9.79)")
    print(f"  EU rows matched on written verses: {counts['corrections:matched_written_eu']:,} - other "
          f"active prose rows matched: {counts['corrections:matched_written'] - counts['corrections:matched_written_eu']:,}")
    if "applied" in counts:
        print(f"  APPLIED: {counts['applied']:,} verses.text rows written")
    if "_tsv" in counts:
        print(f"  per-verse list -> {counts['_tsv']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Derivation B: verses.text from the app feed.")
    ap.add_argument("--eligible", required=True, help="A's eligible_<date>.tsv")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", metavar="COPY_DB", help="read-only against a db copy")
    g.add_argument("--dry-run-nodb", action="store_true", help="LOCAL: no db, abp_texts proxy for old text")
    g.add_argument("--apply", metavar="COPY_DB", help="write verses.text on the db COPY")
    ap.add_argument("--out", default="~/edition_upgrade_runs")
    a = ap.parse_args(argv)
    try:
        if a.dry_run_nodb:
            counts, _ = run(a.eligible, None, False, a.out)
            report(counts, "LOCAL no-db: old text = clean_verse(abp_texts) + em-dash; NOT the build's figures")
        elif a.dry_run is not None:
            copy = check_target(a.dry_run)
            counts, _ = run(a.eligible, copy, False, a.out)
            report(counts, f"DRY RUN, read-only: {copy}")
        else:
            copy = check_target(a.apply)
            counts, _ = run(a.eligible, copy, True, a.out)
            report(counts, f"APPLY on the copy {copy}")
    except FeedError as e:
        print(f"STOP: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
