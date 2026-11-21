"""P6 check program (edition-upgrade step 8, the swap; DESIGN 9.213, 9.221-9.228). READ-ONLY on every database it opens.

Two modes, run by blocks P6a and P6b through the read-once launcher (DESIGN 9.190 (5)(b)); arguments KEY=value:
  MODE=pre    S=<src> B=<built> D=<run folder> REPO=<checkout>
      site UP. Every table of src: rows + eu_step.digest, saved to D/src_digests.json (src is sha-pinned by the block),
      so the window only has to read live. Prints the table count.
  MODE=live   LIVE=<live bible.db> B=<built> D=<run folder> REPO=<checkout>
      site DISABLED (inside the window). Reads live in place, read-only:
        - words + verses digests = LIVESRC's (DESIGN 9.181; re-shown at the swap, 9.222 (2)) - else STOP
        - every table of live vs the saved src digests: tables on one side only = STOP; tables that differ must be among
          ai_search_cache, lsj, abp_ext, abp_corrections (9.224: "any table beyond ... differing at that read = STOP")
        - what the swap drops, live -> built, for ai_search_cache, lsj, abp_ext: eu_step.run_delta(built -> live), counts and
          changed-column names only (values only in D/delta_built_vs_live.tsv)
The log gets table names, counts, digests, column names - never a cached AI text, summary, definition or query string.
Exit 0 = all held; 2 = STOP (the block stops before any rename).
"""
import json
import os
import sys

args = dict(a.split("=", 1) for a in sys.argv[1:])
MODE, D, REPO = args["MODE"], args["D"], args["REPO"]
sys.path.insert(0, os.path.join(REPO, "scripts"))
import eu_step as E  # noqa: E402  (the lane's own reader + digest + row delta)

LIVESRC = {"words": [626309, "1ce75b22fd302e368f1bfca1bcb9e0fdccdce9e3658af4534f258f5fd3b25b26"],
           "verses": [31237, "5717b0451ba5e1b044a1c3f1a3cf718c15d23e3a669a605b9c3d5502d1f721ae"]}   # DESIGN 9.181, 9.222 (2)
ALLOWED = ("ai_search_cache", "lsj", "abp_ext", "abp_corrections")      # DESIGN 9.224 (P6 terms)
DROPPED = ("ai_search_cache", "lsj", "abp_ext")
KEYS = {"ai_search_cache": "query", "lsj": "key", "abp_ext": "strongs"}  # app.py :359-364; parse_lsj.py :56-61; load_abp_ext.py :6-11
SAVED = os.path.join(D, "src_digests.json")


def stop(msg):
    print("P6 CHECK: STOP - %s" % msg)
    sys.exit(2)


try:
    if MODE == "pre":
        c = E.ro(args["S"])
        tabs, virt = E.plain_tables(c)
        dig = {t: E.digest(c, t) for t in tabs}
        c.close()
        if virt:
            stop("src has virtual tables %s" % virt)
        if os.path.exists(SAVED):
            stop("already exists: %s" % SAVED)
        with open(SAVED, "w", encoding="utf-8", newline="\n") as f:
            json.dump(dig, f, sort_keys=True)
        for t, (rows, dg) in LIVESRC.items():
            ok = dig.get(t) == [rows, dg]
            print("src %s: %s (= LIVESRC's: %s)" % (t, "%d/%s" % tuple(dig[t]) if t in dig else "-", "yes" if ok else "NO"))
            if not ok:
                stop("src %s is not LIVESRC's" % t)
        print("src: %d tables digested, saved to %s" % (len(dig), SAVED))
        print("P6 CHECK: PRE OK")
    elif MODE == "live":
        if not os.path.exists(SAVED):
            stop("no saved src digests (run P6a first): %s" % SAVED)
        src = json.load(open(SAVED, encoding="utf-8"))
        c = E.ro(args["LIVE"])
        tabs, virt = E.plain_tables(c)
        if virt:
            stop("live has virtual tables %s" % virt)
        dig = {t: E.digest(c, t) for t in tabs}
        c.close()
        for t, (rows, dg) in LIVESRC.items():
            ok = dig.get(t) == [rows, dg]
            print("live %s: %s (expect %d/%s, LIVESRC): %s" % (t, "%d/%s" % tuple(dig[t]) if t in dig else "-", rows, dg,
                                                             "yes" if ok else "NO"))
            if not ok:
                stop("live %s is not LIVESRC's - live = src does not hold at the swap" % t)
        one = sorted(set(dig) ^ set(src))
        print("tables on one side only (live vs src): %s" % (", ".join(one) or "none"))
        if one:
            stop("table(s) on one side only: %s" % one)
        diff = sorted(t for t in dig if dig[t] != src[t])
        print("tables that differ, live vs src (%d): %s" % (len(diff), ", ".join(diff) or "none"))
        other = [t for t in diff if t not in ALLOWED]
        print("differing tables outside %s: %s" % ("/".join(ALLOWED), ", ".join(other) or "none"))
        if other:
            stop("live differs from src in %s - outside the ruled four (9.224)" % other)
        print("=== what the swap drops: built -> live, row delta (eu_step.run_delta; values in the run folder only) ===")
        specs = ["%s:%s" % (t, KEYS[t]) for t in DROPPED]
        total, sha = E.run_delta(args["B"], args["LIVE"], specs, os.path.join(D, "delta_built_vs_live.tsv"), 0)
        print("delta_built_vs_live.tsv: %d difference lines, sha256 %s" % (total, sha))
        print("(read: 'added' = rows live has and built does not - dropped by the swap; 'changed' = live's row differs from built's)")
        print("P6 CHECK: LIVE OK")
    else:
        stop("unknown MODE %r" % MODE)
except E.Stop as e:
    stop(str(e))
