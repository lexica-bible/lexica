#!/usr/bin/env python3
"""Parse the Psalms of Solomon (G. Buchanan Gray, in R.H. Charles' APOT 1913) into
psolomon_english.json {"ch.vs": text} + psolomon_headings.json + empty tagged file.

Source: raw/psolomon.html — the Wesley Center Online (NNU) copy of Gray's public-domain
translation (same Charles family as the rest of our pseudepigrapha). Layout, one item
per physical line after tag-strip:
  * "N. A Psalm Of Solomon. ..."  -> psalm superscription (chapter heading); psalms 1
    and 3 have none;
  * "C 1 <text>"                   -> chapter C, verse 1 (the only verse written with the
    chapter number prefixed);
  * the main verse number then runs INLINE through the poetic half-lines — it can sit at
    a line start, mid-line ("...far from God, 2 my soul..."), or glued to its alternate
    ("30(26)") -- so each chapter's lines are joined and split on a running token stream,
    not per physical line;
  * Gray's DUAL versification prints an alternate number in parentheses ("(9)", "(26)",
    and bare "(13)" half-lines) -> the parenthetical alternates are dropped first so the
    main (bold) numbering surfaces cleanly; the main numbering is what we keep.
Gray's empty lacuna marks "[ ]" / "()" are dropped; supplied words "(I said)" are kept.
"""
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "raw" / "psolomon.html"

ALTNUM = re.compile(r"\(\d+\)")          # Gray's alternate verse number -> drop
EMPTY = re.compile(r"\[\s*\]|\(\s*\)")   # lacuna marks -> drop


def to_lines(raw):
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    t = re.sub(r"(?is)<br[^>]*>", "\n", t)
    t = re.sub(r"(?is)</(p|div|h[1-6]|li)>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    out = []
    for l in t.splitlines():
        l = re.sub(r"[ \t\xa0]+", " ", l).strip()
        if l:
            out.append(l)
    return out


def clean(s):
    s = ALTNUM.sub(" ", s)
    s = EMPTY.sub(" ", s)
    s = s.replace("[", "").replace("]", "")     # keep any bracketed words
    s = re.sub(r"\s+([,.;:])", r"\1", s)         # tidy spaces left before punctuation
    return re.sub(r"\s+", " ", s).strip()


GAP_TOL = 4   # tolerate a small skip if Gray gave only an alternate number there


def split_verses(body):
    """Split one chapter's joined text into {verse: text} on its running MAIN numbering.
    A bare integer token is the next verse only when it is strictly greater than the last
    and within GAP_TOL (so a stray number in the prose can't masquerade as a verse)."""
    toks = ALTNUM.sub(" ", body).split()        # drop alternates so main numbers surface
    verses, cur, buf, last = {}, None, [], 0

    def flush():
        if cur is not None:
            seg = clean(" ".join(buf))
            if seg:
                verses[cur] = (verses[cur] + " " + seg) if cur in verses else seg

    for tok in toks:
        m = re.fullmatch(r"(\d{1,3})", tok)
        val = int(m.group(1)) if m else None
        if val is not None and last < val <= last + GAP_TOL:
            flush()
            cur, buf, last = val, [], val
        else:
            buf.append(tok)
    flush()
    return verses


def main():
    lines = to_lines(RAW.read_text(encoding="utf-8", errors="replace"))
    start = next(i for i, l in enumerate(lines) if re.match(r"^1 1 I cried unto the Lord", l))
    lines = lines[start:]

    # segment into chapters: a "C 1 <text>" line (C sequential) opens chapter C;
    # "N. Title" lines are superscriptions; every other line is body for the open chapter
    chap_lines, headings = {}, {}
    cur = None
    for l in lines:
        if l.startswith("Edited and slightly"):       # Wesley footer
            break
        mc = re.match(r"^(\d+)\s+1\s+(.*)$", l)
        if mc and (cur is None or int(mc.group(1)) == cur + 1):
            cur = int(mc.group(1))
            chap_lines[cur] = ["1 " + mc.group(2)]    # keep the verse-1 marker, drop chapter no.
            continue
        mh = re.match(r"^(\d+)\.\s+(.+)$", l)
        if mh:
            headings[f"{int(mh.group(1))}.1"] = mh.group(2).strip()
            continue
        if cur is not None:
            chap_lines[cur].append(l)

    english = {}
    for ch, body_lines in chap_lines.items():
        for v, text in split_verses(" ".join(body_lines)).items():
            english[f"{ch}.{v}"] = text

    # keep only headings whose anchor verse exists
    headings = {k: t for k, t in headings.items() if k in english}

    (HERE / "psolomon_english.json").write_text(
        json.dumps(english, ensure_ascii=False, indent=0), encoding="utf-8")
    (HERE / "psolomon_headings.json").write_text(
        json.dumps(headings, ensure_ascii=False, indent=0), encoding="utf-8")
    (HERE / "psolomon_tagged_full.json").write_text("[]", encoding="utf-8")

    chs = sorted({int(k.split(".")[0]) for k in english})
    print(f"Psalms of Solomon: wrote {len(english)} verses across {len(chs)} chapters "
          f"({min(chs)}..{max(chs)}); {len(headings)} headings")
    missing = [c for c in range(1, 19) if c not in chs]
    if missing:
        print("MISSING chapters:", missing)
    report = []
    for c in chs:
        vs = sorted(int(k.split(".")[1]) for k in english if int(k.split(".")[0]) == c)
        gaps = [x for x in range(1, max(vs) + 1) if x not in vs]
        if gaps:
            report.append((c, max(vs), gaps))
    if report:
        print(f"REVIEW ({len(report)} chapters with verse gaps):")
        for c, mx, gaps in report:
            print(f"  ch {c}: max {mx} -- missing {gaps}")
    else:
        print("clean: every chapter contiguous 1..max")


if __name__ == "__main__":
    main()
