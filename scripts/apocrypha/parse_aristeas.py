#!/usr/bin/env python3
"""Parse the Letter of Aristeas (H.T. Andrews, in R.H. Charles' APOT 1913) into
aristeas_english.json {"1.section": text} + empty headings/tagged files.

Source: raw/aristeas.html — the Wesley Center Online (NNU) copy of Andrews' public-domain
translation. The Letter is one continuous work cited by SECTION number (1..322), so it is
loaded as a single chapter (chapter 1) whose "verses" are the section numbers. Section
numbers appear as inline integers running through the prose; the body is joined and split
on a sequential token stream (a digit is the next section only when it is just ahead of
the last one, so the few numeric quantities in the prose can't masquerade as sections).
Sections whose number the transcription never prints (15 of them) fold into the preceding
section, exactly as the source reads — no text is lost.
"""
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "raw" / "aristeas.html"
GAP_TOL = 4


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


def split_sections(body):
    toks = body.split()
    out, cur, buf, last = {}, None, [], 0

    def flush():
        if cur is not None:
            seg = clean(" ".join(buf))
            if seg:
                out[cur] = (out[cur] + " " + seg) if cur in out else seg

    for tok in toks:
        m = re.fullmatch(r"(\d{1,3})[.,]?", tok)
        val = int(m.group(1)) if m else None
        if val is not None and last < val <= last + GAP_TOL:
            flush()
            cur, buf, last = val, [], val
        else:
            buf.append(tok)
    flush()
    return out


def main():
    lines = to_lines(RAW.read_text(encoding="utf-8", errors="replace"))
    si = next(i for i, l in enumerate(lines) if l.startswith("SINCE I have collected"))
    ei = next(i for i, l in enumerate(lines) if l.startswith("Scanned and Edited"))
    body = "1 " + " ".join(lines[si:ei])      # the first paragraph is section 1 (unnumbered)

    english = {f"1.{sec}": text for sec, text in split_sections(body).items()}
    (HERE / "aristeas_english.json").write_text(
        json.dumps(english, ensure_ascii=False, indent=0), encoding="utf-8")
    (HERE / "aristeas_headings.json").write_text("{}", encoding="utf-8")
    (HERE / "aristeas_tagged_full.json").write_text("[]", encoding="utf-8")

    secs = sorted(int(k.split(".")[1]) for k in english)
    print(f"Letter of Aristeas: wrote {len(english)} sections (1.{secs[0]}..1.{secs[-1]})")
    gaps = [n for n in range(1, secs[-1] + 1) if n not in secs]
    print(f"  {len(gaps)} section numbers not printed in the source (folded into the prior "
          f"section, no text lost): {gaps}")


if __name__ == "__main__":
    main()
