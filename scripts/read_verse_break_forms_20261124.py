#!/usr/bin/env python3
"""read_verse_break_forms_20261124.py - READ-ONLY (DESIGN 9.266 (3)): every place where the app edition's
verse break differs from live, and how many printed forms did not follow the words across it.

The build pairs app verses with ours by number only (abp_app_feed.pair_keys: same verse, plus the Psalm-title
shift), so a word the app prints at the end of verse 7 and we hold at the start of verse 8 (1Jn 5:7/8) was
never tracked. How this read finds them:
  1. each live verse is lined up with its own app partner (the audit's align_verse: in order by Strong's
     number, then swapped order). A verse with no word left over on either side is CLEAN.
  2. for every two neighbouring live verses where either is not clean (and everywhere in the four
     versification-class chapters), the two live verses are lined up as ONE stretch against the app verses
     between their two partners, the same way. A live word lined up with an app word from another verse is
     a MOVED word.
For each moved word, its printed form:
  followed        live shows a printed form there
  not needed      the app's Greek is the dictionary word's own letters (no form line: the builder's rule)
  DID NOT FOLLOW  the app's Greek differs from the dictionary word and live shows no form
  glued           the app cell holds several numbers and its Greek does not split one word per number
  font            the app cell has English typed in the Greek font (read by eye)
A moved run is EDGE when it touches an edge of its live verse and an edge of its app verse (the verse-break
shape); otherwise INNER (a slip or a reorder, read by eye, not counted as a verse break).
Limit: words moved across a CHAPTER break are not looked for (the four class chapters are the known ones).

Controls (the run is CHECK unless both hold): 1Jn 5:8 @2, @3, @4, @6, @7 are EDGE and DID NOT FOLLOW
(the known positive, DESIGN 9.266); Psa 3:0 @1 (τω, paired through the Psalm-title shift) is not moved.

Opens the database read-only; writes only its --out folder (moved.tsv, runs.tsv, summary.txt).
  python3 scripts/read_verse_break_forms_20261124.py --out <dir> [--db ~/bible-db/bible.db]
"""
import argparse
import collections
import os
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import abp_app_feed as F                                                                    # noqa: E402
from audit_abp_app_vs_surface import NOTE_RE, align_verse, english_font, expand_app, strip_marks   # noqa: E402

LIVE = Path("~/bible-db/bible.db").expanduser()
POSITIVE = {("1Jn", 5, 8, p) for p in (2, 3, 4, 6, 7)}
NEGATIVE = ("Psa", 3, 0, 1)
VERDICTS = ("DID NOT FOLLOW", "followed", "not needed", "glued", "font")


def load_live(con):
    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    dl_sel, dl_join = ("dl.lemma", "LEFT JOIN dotted_lexicon dl ON dl.strongs = 'G' || w.strongs") \
        if "dotted_lexicon" in have else ("NULL", "")
    rows = con.execute(f"""SELECT v.book, v.chapter, v.verse, w.position, COALESCE(w.strongs, ''), COALESCE(w.is_pn, 0),
                                  COALESCE({dl_sel}, l.lemma, ''), COALESCE(s.form, '')
                           FROM verses v JOIN words w ON w.verse_id = v.id
                           LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base
                           {dl_join}
                           LEFT JOIN abp_surface s ON s.verse_id = w.verse_id AND s.position = w.position
                           ORDER BY v.book, v.chapter, v.verse, w.position""").fetchall()
    out = collections.defaultdict(list)
    for b, c, v, pos, s, pn, lem, form in rows:
        out[(b, c)].append({"verse": v, "pos": pos, "s": s, "pn": pn, "lemma": lem, "form": form})
    keys = {(b, c, v) for b, c, v in con.execute("SELECT book, chapter, verse FROM verses")}
    return out, keys


def load_app(slots, pairs):
    back = {feed: ours for ours, feed in pairs.items()}
    out = collections.defaultdict(list)
    for s in sorted(slots, key=lambda r: (r["abbrev"], r["chapter"], r["verse"], r["slot_index"])):
        fk = (s["abbrev"], s["chapter"], s["verse"])
        cell = s["greek"] or ""
        m = NOTE_RE.search(cell)
        font = english_font(cell[:m.start()] if m else cell)
        for p, g, _note, kind in expand_app(s["strongs"], s["greek"]):
            out[(s["abbrev"], s["chapter"])].append({
                "feed": fk, "ours": back.get(fk), "slot": s["slot_index"], "s": p, "g": g, "kind": kind,
                "cell": cell, "font": font})
    return out


def verdict(a, w):
    if w["form"]:
        return "followed"
    if a["font"]:
        return "font"
    if a["g"] is None:
        return "glued"
    if w["lemma"] and strip_marks(a["g"]).lower() == strip_marks(w["lemma"]).lower():
        return "not needed"
    return "DID NOT FOLLOW"


def read(con, slots, vclass):
    live, our_keys = load_live(con)
    feed_keys = {(s["abbrev"], s["chapter"], s["verse"]) for s in slots}
    pairs = F.pair_keys(our_keys, feed_keys, vclass)["pairs"]
    app = load_app(slots, pairs)
    moved, n = {}, collections.Counter()
    for ch_key in sorted(live):
        ours, theirs = live[ch_key], app.get(ch_key, [])
        if not theirs:
            continue
        n["chapters"] += 1
        by_feed, by_live = collections.defaultdict(list), collections.defaultdict(list)
        for i, a in enumerate(theirs):
            by_feed[a["feed"][2]].append(i)
        for j, w in enumerate(ours):
            by_live[w["verse"]].append(j)
        vs = sorted(by_live)
        partner = {v: (pairs[(*ch_key, v)][2] if (*ch_key, v) in pairs else None) for v in vs}
        clean = set()
        for v in vs:
            ai = by_feed.get(partner[v], []) if partner[v] is not None else []
            _p, _same, la, lo = align_verse([theirs[i] for i in ai], [ours[j] for j in by_live[v]])
            if not la and not lo and ai:
                clean.add(v)
        n["live verses"] += len(vs)
        n["clean verses"] += len(clean)
        every = ch_key in vclass
        for v, v2 in zip(vs, vs[1:]):
            if not every and v in clean and v2 in clean:
                continue
            nums = [p for p in (partner[v], partner[v2]) if p is not None] or [v, v2]
            lo_n, hi_n = min(nums), max(nums)
            ai = [i for f in sorted(by_feed) if lo_n <= f <= hi_n for i in by_feed[f]]
            wj = by_live[v] + by_live[v2]
            prs, _same, _la, _lo = align_verse([theirs[i] for i in ai], [ours[j] for j in wj])
            n["stretches read"] += 1
            for i, j, _how in prs:
                a, w = theirs[ai[i]], ours[wj[j]]
                if a["ours"] is None or a["ours"][2] != w["verse"]:
                    moved.setdefault((ch_key, wj[j]), (a, w))     # the first stretch to claim a word keeps it
    runs, cur = [], None
    for (ch_key, j), (a, w) in sorted(moved.items(), key=lambda x: x[0]):
        tag = (ch_key, w["verse"], a["feed"])
        if cur and cur["tag"] == tag and cur["j"][-1] == j - 1:
            cur["j"].append(j)
            cur["items"].append((a, w))
        else:
            cur = {"tag": tag, "j": [j], "items": [(a, w)]}
            runs.append(cur)
    for r in runs:
        ch_key, lv, fk = r["tag"]
        words = [w for w in live[ch_key] if w["verse"] == lv]
        app_verse = [a for a in app[ch_key] if a["feed"] == fk]
        (fa, fw), (la_, lw) = r["items"][0], r["items"][-1]
        r["edge"] = (fw is words[0] or lw is words[-1]) and \
            any(x is app_verse[0] or x is app_verse[-1] for x, _w in r["items"])
    return n, runs


def write(out, n, runs, vclass):
    os.makedirs(out, exist_ok=True)
    tally, verses, dnf_verses, seen = collections.Counter(), set(), collections.Counter(), {}
    with open(os.path.join(out, "moved.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("live_verse\tlive_position\tnumber\tapp_verse\tapp_slot\tapp_cell\tapp_greek\tdictionary_word\t"
                "live_form\trun\tverdict\tclass_chapter\n")
        for r in runs:
            (b, c), lv, fk = r["tag"]
            shape = "EDGE" if r["edge"] else "INNER"
            if r["edge"]:
                verses.add((b, c, lv))
            for a, w in r["items"]:
                v = verdict(a, w)
                tally[(shape, v)] += 1
                seen[(b, c, lv, w["pos"])] = (shape, v)
                if shape == "EDGE" and v == "DID NOT FOLLOW":
                    dnf_verses[f"{b} {c}:{lv}"] += 1
                f.write("\t".join(str(x) for x in (
                    f"{b} {c}:{lv}", w["pos"], w["s"], f"{fk[0]} {fk[1]}:{fk[2]}", a["slot"], a["cell"], a["g"] or "",
                    w["lemma"], w["form"] or "(none)", shape, v, "yes" if (b, c) in vclass else "")) + "\n")
    with open(os.path.join(out, "runs.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("live_verse\tapp_verse\twords\tshape\tlive_positions\n")
        for r in runs:
            (b, c), lv, fk = r["tag"]
            f.write(f"{b} {c}:{lv}\t{fk[0]} {fk[1]}:{fk[2]}\t{len(r['items'])}\t{'EDGE' if r['edge'] else 'INNER'}\t"
                    f"{','.join(str(w['pos']) for _a, w in r['items'])}\n")
    pos_ok = all(seen.get(k) == ("EDGE", "DID NOT FOLLOW") for k in POSITIVE)
    neg_ok = NEGATIVE not in seen
    lines = ["read: " + "; ".join(f"{k} {v:,}" for k, v in n.items()),
             f"moved runs: {len(runs):,} ({sum(r['edge'] for r in runs):,} EDGE, {sum(not r['edge'] for r in runs):,} INNER)",
             f"EDGE: {sum(x for (s, _v), x in tally.items() if s == 'EDGE'):,} moved words in {len(verses):,} live verses"]
    for shape in ("EDGE", "INNER"):
        lines.append(f"  {shape}: " + ", ".join(f"{v} {tally[(shape, v)]:,}" for v in VERDICTS))
    lines.append(f"EDGE DID NOT FOLLOW by verse ({len(dnf_verses):,} verses): " +
                 ", ".join(f"{k} {x}" for k, x in sorted(dnf_verses.items())))
    lines.append("CONTROL 1Jn 5:8 @2,3,4,6,7 EDGE + DID NOT FOLLOW: " +
                 ("PASS" if pos_ok else "FAIL " + str({k: seen.get(k) for k in sorted(POSITIVE)})))
    lines.append(f"CONTROL Psa 3:0 @1 not moved: {'PASS' if neg_ok else 'FAIL ' + str(seen.get(NEGATIVE))}")
    text = "\n".join(lines) + "\n"
    Path(out, "summary.txt").write_text(text, encoding="utf-8")
    print(text, end="")
    return pos_ok and neg_ok


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(LIVE))
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    slots = F.read_slots()                       # the pinned feed, checked against cert_manifest.json
    vclass = F.load_versification_class()
    con = sqlite3.connect(f"file:{Path(a.db).expanduser()}?mode=ro", uri=True)
    try:
        con.execute("PRAGMA busy_timeout=30000")
        n, runs = read(con, slots, vclass)
    finally:
        con.close()
    ok = write(a.out, n, runs, vclass)
    print("VERSE BREAK READ: DONE" if ok else "VERSE BREAK READ: CHECK - a control failed")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
