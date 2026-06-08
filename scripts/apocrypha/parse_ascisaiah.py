#!/usr/bin/env python3
"""Parse the Ascension of Isaiah (R.H. Charles, 1900) into ascisaiah_english.json
{"ch.vs": text} + empty headings/tagged files.

Source: raw/ascisaiah.html — earlychristianwritings.com (the same Charles family and site
as our Testaments of the Twelve Patriarchs). Layout:
  * "CHAPTER N"            -> chapter N (the text before its first "M." marker is verse 1);
  * verse numbers are "N." markers that USUALLY start a line but sometimes sit mid-line
    ("...believe in him. 8. And they..."), so each chapter is joined and split on a running
    token stream (a "N." token is the next verse only when just ahead of the last one).
The composite work is chapters 1-5 (Martyrdom of Isaiah) + 6-11 (Vision of Isaiah);
11 chapters total. Charles' square-bracket editorial words keep their text, the brackets
dropped; his round-bracket supplements ("(from)") are kept.
"""
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "raw" / "ascisaiah.html"

CHAP = re.compile(r"(?i)^chapter\s+(\d+)$")
FOOTER = "Go to the Chronological List"
GAP_TOL = 3


def to_lines(raw):
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    t = re.sub(r"(?is)<br[^>]*>", "\n", t)
    t = re.sub(r"(?is)</(p|div|h[1-6]|li)>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    return [re.sub(r"[ \t\xa0]+", " ", l).strip() for l in t.splitlines() if l.strip()]


def clean(s):
    s = s.replace("[", "").replace("]", "")
    s = re.sub(r"\s+([,.;:])", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def split_verses(body):
    """Split a chapter's joined text into {verse: text}. Verse 1 is the opening text;
    each later "N." token (just ahead of the last verse) starts verse N."""
    body = re.sub(r"^\s*1\.\s+", "", body)        # rare explicit verse-1 marker
    toks = body.split()
    verses, cur, buf, last = {}, 1, [], 1

    def flush():
        seg = clean(" ".join(buf))
        if seg:
            verses[cur] = (verses[cur] + " " + seg) if cur in verses else seg

    for tok in toks:
        m = re.fullmatch(r"(\d{1,3})\.", tok)
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
    start = next(i for i, l in enumerate(lines) if CHAP.match(l))

    chap_lines = {}
    ch = None
    for l in lines[start:]:
        if l.startswith(FOOTER):
            break
        mc = CHAP.match(l)
        if mc:
            ch = int(mc.group(1))
            chap_lines[ch] = []
            continue
        if ch is not None:
            chap_lines[ch].append(l)

    english = {}
    for ch, body_lines in chap_lines.items():
        for v, text in split_verses(" ".join(body_lines)).items():
            english[f"{ch}.{v}"] = text

    (HERE / "ascisaiah_english.json").write_text(
        json.dumps(english, ensure_ascii=False, indent=0), encoding="utf-8")
    (HERE / "ascisaiah_headings.json").write_text("{}", encoding="utf-8")
    (HERE / "ascisaiah_tagged_full.json").write_text("[]", encoding="utf-8")

    chs = sorted({int(k.split(".")[0]) for k in english})
    print(f"Ascension of Isaiah: wrote {len(english)} verses across {len(chs)} chapters "
          f"({min(chs)}..{max(chs)})")
    missing = [c for c in range(1, 12) if c not in chs]
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
