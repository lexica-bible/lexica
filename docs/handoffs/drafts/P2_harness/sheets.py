# P2 sheets (11/20): built vs src vs the app feed at the 20 moved rows (10 verses).
# Reads local files only; opens no database; writes nothing but its own printout.
# Built's ENGLISH READING ORDER at a pair = the reader's rule (scripts/reorder_english.py :24-27,
# :30-72): rows in one bracket group read by greek_pos ascending (missing -> 999), ties stay in
# position order (stable sort); rows outside brackets read in position order.
import csv
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
REPO = r"C:\Users\JP\projects\bible-db"
PA = r"C:\Users\JP\edition_upgrade_runs\pa"
FEED = REPO + r"\abp_app_html\abp_app_slots_italic.tsv"
APP = {"2Ki": "2 Kings", "Est": "Esther", "Eze": "Ezekiel", "Gen": "Genesis", "Jdg": "Judges",
       "Jos": "Joshua", "Rom": "Romans"}

moved = list(csv.DictReader(open(PA + r"\words_moved.tsv", encoding="utf-8", newline=""), delimiter="\t"))
verses = []
for m in moved:
    k = (m["book"], int(m["chapter"]), int(m["verse"]))
    if k not in verses:
        verses.append(k)

cells = {}
for r in csv.DictReader(open(PA + r"\words_cells.tsv", encoding="utf-8", newline=""), delimiter="\t"):
    k = (r["book"], int(r["chapter"]), int(r["verse"]))
    if k in verses:
        cells[(k, int(r["position"]), r["column"])] = (r["a"], r["b"])

feed = {}
for r in csv.DictReader(open(FEED, encoding="utf-8", newline=""), delimiter="\t"):
    for k in verses:
        if r["book"] == APP[k[0]] and int(r["chapter"]) == k[1] and int(r["verse"]) == k[2]:
            feed.setdefault(k, []).append(r)


def lit(s):
    if s is None or s == "None":
        return None
    if s[:1] in "'\"":
        return eval(s)
    return int(s) if s.lstrip("-").isdigit() else s


EQ = "same-on-both-unlisted"


def built_val(k, rows, p, col, side0="built"):
    """built's value of `col` at position p, from the delta. A cell not in words_cells is equal on
    both copies; follow the moved rows until a listed value is found, else EQ (all equal)."""
    # Nodes (copy, position). Known: a words_cells line gives src@p (a) and built@p (b).
    # Equal: no line at p -> built@p == src@p; a moved row with col not in its differing
    # columns -> built@(b) == src@(a). Search the equal-links from built@p to a known value.
    from collections import deque
    start = (side0, p)
    seen, todo = {start}, deque([start])
    while todo:
        side, q = todo.popleft()
        if (k, q, col) in cells:
            return lit(cells[(k, q, col)][1 if side == "built" else 0])
        nxt = [("src" if side == "built" else "built", q)]          # no line at q
        for r in rows:
            if col not in r["differs"]:
                if side == "built" and r["b"] == q:
                    nxt.append(("src", r["a"]))
                if side == "src" and r["a"] == q:
                    nxt.append(("built", r["b"]))
        for n in nxt:
            if n not in seen:
                seen.add(n)
                todo.append(n)
    return EQ + ":" + "/".join("%s@%d" % n for n in sorted(seen))


def occ(text, e):
    ws = re.findall(r"[A-Za-z']+", e or "")
    if not ws:
        return []
    pat = r"(?<![A-Za-z])" + r"[^A-Za-z]+".join(re.escape(w) for w in ws) + r"(?![A-Za-z])"
    return [m.start() for m in re.finditer(pat, text)]


summary = []
for k in verses:
    fs = feed[k]
    print("=" * 110)
    print("%s %d:%d   feed slots %d" % (k[0], k[1], k[2], len(fs)))
    print("  feed: " + " | ".join("%s:%s[%s]" % (r["slot_index"], r["english"], r["strongs"]) for r in fs))
    text, owner = "", []
    for r in fs:
        t = r["english"] + " "
        text += t
        owner += [int(r["slot_index"])] * len(t)
    rows = []
    for m in moved:
        if (m["book"], int(m["chapter"]), int(m["verse"])) != k:
            continue
        rows.append(dict(ident=eval(m["identity"]), a=int(m["a_position"]), b=int(m["b_position"]),
                         differs=set(lit(m["other_columns_differing"]).split(",")) - {""}))
    for r in rows:
        r["eng"] = built_val(k, rows, r["b"], "english")
        r["gp"] = built_val(k, rows, r["b"], "greek_pos")
        r["br"] = built_val(k, rows, r["b"], "bracket_id")
        eb = cells.get((k, r["b"], "english"))
        r["src_at_b"] = lit(eb[0]) if eb else r["eng"]
    rows.sort(key=lambda r: r["b"])
    if "--control" in sys.argv and k == ("Gen", 34, 4):   # plant: swap built English of the pair
        rows[0]["eng"], rows[1]["eng"] = rows[1]["eng"], rows[0]["eng"]
        print("  CONTROL: planted swap of built English at Gen 34:4 @1/@2; expect NO here")
    for r in rows:
        print("  built @%-2d (from src @%-2d) strongs %-7s english %-28r greek_pos %-5s bracket %-5s | src @%-2d english %r"
              % (r["b"], r["a"], r["ident"][0], r["eng"], r["gp"], r["br"], r["b"], r["src_at_b"]))
    lo, hi = rows
    unl = lambda v: isinstance(v, str) and v.startswith(EQ)
    if lo["br"] == hi["br"] and (lo["gp"] == hi["gp"]):
        rd = rows
        how = "same bracket value and same greek_pos on both rows (listed or linked equal): position order"
    elif lo["br"] == hi["br"] and lo["br"] is not None and not unl(lo["gp"]) and not unl(hi["gp"]):
        gk = lambda r: (999 if r["gp"] is None else r["gp"], r["b"])
        rd = sorted(rows, key=gk)
        how = "one bracket group (%s): greek_pos then position" % lo["br"]
    elif lo["br"] is None and hi["br"] is None:
        rd = rows
        how = "outside brackets: position order"
    else:
        rd = rows
        how = "MIXED bracket membership - position order shown, not decided"
    first, second = rd
    # src's reading order at the same two positions (old edition)
    sr = []
    for pos in (lo["b"], hi["b"]):
        sr.append(dict(b=pos, eng=built_val(k, rows, pos, "english", "src"),
                       gp=built_val(k, rows, pos, "greek_pos", "src"), br=built_val(k, rows, pos, "bracket_id", "src")))
    if sr[0]["br"] == sr[1]["br"] and sr[0]["gp"] == sr[1]["gp"]:
        srd, show = sr, "position order"
    elif sr[0]["br"] == sr[1]["br"] and sr[0]["br"] is not None and all(isinstance(x["gp"], int) or x["gp"] is None for x in sr):
        srd, show = sorted(sr, key=lambda x: (999 if x["gp"] is None else x["gp"], x["b"])), "bracket %s by greek_pos" % sr[0]["br"]
    elif sr[0]["br"] is None and sr[1]["br"] is None:
        srd, show = sr, "position order"
    else:
        srd, show = sr, "MIXED - position order shown"
    print("  src reading order (%s): %s" % (show, " then ".join("@%d %r (gp %s, br %s)" % (x["b"], x["eng"], x["gp"], x["br"]) for x in srd)))
    print("  built reading order (%s): %r then %r" % (how, first["eng"], second["eng"]))
    if first["eng"] is None or second["eng"] is None:
        one = first if first["eng"] else second
        blank = second if first["eng"] else first
        hits = occ(text, one["eng"])
        slot = fs[owner[hits[0]]] if hits else None
        if slot:
            seq = slot["strongs"].split("-")
            s1, s2 = str(one["ident"][0]), str(blank["ident"][0])
            ok = s1 in seq and s2 in seq and (seq.index(s1) < seq.index(s2)) == (one["b"] < blank["b"])
            print("  feed slot %s %r [%s]: ONE joined English for both numbers; built carries it on %s @%d, %s @%d blank"
                  % (slot["slot_index"], slot["english"], slot["strongs"], s1, one["b"], s2, blank["b"]))
            verdict = "YES (row order = the slot's number order %s)" % slot["strongs"] if ok else "NO"
        else:
            verdict = "NO - English not found in the feed"
    else:
        best = None
        for i in occ(text, lo["eng"]):
            for j in occ(text, hi["eng"]):
                if i != j and (best is None or abs(i - j) < abs(best[0] - best[1])):
                    best = (i, j)
        if best is None:
            verdict = "NO - a built word not found in the feed text"
        else:
            i, j = best
            w0, w1 = min(i, j), max(i, j)
            slots = sorted({owner[w0], owner[w1]})
            print("  feed slot(s) %s: %s" % (slots, " | ".join("%r [%s]" % (fs[s]["english"], fs[s]["strongs"]) for s in slots)))
            feed_first = lo["eng"] if i < j else hi["eng"]
            verdict = "YES" if feed_first == first["eng"] else "NO"
            print("  feed English order: %r first" % feed_first)
    print("  BUILT = FEED (English reading order): %s" % verdict)
    summary.append(("%s %d:%d" % k, verdict))
print("=" * 110)
for ref, v in summary:
    print("  %-10s %s" % (ref, v))
print("ALL 10: %s" % ("YES" if all(v.startswith("YES") for _r, v in summary) else "NO"))
