#!/usr/bin/env python3
"""
parse_abp_analytical_lexicon.py — the ABP *Analytical Lexicon* (purchased PDF, on
JP's machine, NOT in the repo) -> one TSV row per inflected form. READ-ONLY: it
reads the PDF and writes a TSV; it never opens a database. Lane (b) of
docs/handoffs/HANDOFF_abp_source_material.md.

TEXT LAYER (checked 2026-10-24): a symbol font ("Newport") — Greek typed as Latin
keystrokes, no Unicode map. Mapping (one-to-one): a α · b β · g γ · d δ · e ε · z ζ ·
h η · q θ · i ι · k κ · l λ · m μ · n ν · x ξ · o ο · p π · r ρ · s σ · V ς · t τ ·
u υ · f φ · c χ · y ψ · w ω; capitals likewise. Accents and breathings are separate
glyphs and are LOST — the place an accent sat shows as byte 0xA2, sometimes followed
by a stray space ("a\xa2 gra" = ἄγρα); both are removed. So every lemma/form here is
UNACCENTED: it matches our Greek only after folding, never byte-exact.

LAYOUT: two columns per page, read left column then right; entries run on across
columns and pages. Per entry:
    NOUN masculine . . . . . . . . 60.1          <- POS + number OPENS the entry
    agorasmo\xa2V...a purchase.                  <- headword...gloss
    agorasmoiV dat. pl.                           <- one line per form + parsing
The number is the ABP number (Strong's, with ABP's dotted extensions: 70.4).
Columns are split at the blank gutter, found per page (the column where the right
column's text starts); a page where left-column text runs into that column is
reported, never silently cut.

CROSS-CHECK: pdftotext -raw reads the columns in order on its own; its count of
entry-opening lines per page must equal ours, page by page (two derivations).

OUTPUT TSV (UTF-8, LF): ab_number, lemma, pos, gloss, form, parsing
  plus lemma_keys / form_keys (the raw symbol-font text) for audit.

CONTROLS (exit non-zero on a miss):
  "agcisteuw" -> 70.4, lemma folds to ἀγχιστεύω, POS VERB
  "agorasmoV" -> 60.1, lemma folds to ἀγορασμός, POS NOUN masculine
  page 5 opens exactly 20 entries

Needs pdftotext (xpdf/poppler) on PATH. Run locally:
  python scripts/parse_abp_analytical_lexicon.py "C:/Users/JP/Downloads/analyticallexicon.pdf"
  # -> abp_helps/analytical_lexicon.tsv (gitignored)
"""
import argparse
import os
import re
import subprocess
import sys
import unicodedata
from collections import Counter

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
OUT_DIR = os.path.join(REPO, "abp_helps")

LOWER = dict(zip("abgdezhqiklmnxoprsVtufcyw", "αβγδεζηθικλμνξοπρσςτυφχψω"))
UPPER = dict(zip("ABGDEZHQIKLMNXOPRSTUFCYW", "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"))
SYMBOL = {**UPPER, **LOWER}          # 'V' must stay final sigma (LOWER wins)

ACCENT = "\xa2"
# Entry line: word type (may itself hold dots/digits/&: "NOUN masculine feminine with acc. sg.",
# "PARTICLE compound 3778 & 1510.2.3"), a dot leader (". . . "), then the number — or two
# numbers "5484, 85" (= 5484 and 5485), kept verbatim.
NUMS = r"\d+(?:\.\d+)*(?:,\s*\d+(?:\.\d+)*)*"
HEADER_RE = re.compile(r"^(?P<pos>[A-Z].*?)\s*(?:\.\s?){3,}[\s.]*(?P<num>" + NUMS + r")\s*$")
# Independent detector for the -raw cross-check: ANY line ending in a dot leader + number(s).
LEADER_RE = re.compile(r"(?:\.\s*){4,}" + NUMS + r"\s*$")
HEADER_NONUM_RE = re.compile(r"^(?P<pos>[A-Z][A-Za-z ,/()\-]*?)\s*(?:\.\s*){4,}\s*$")
HEAD_RE = re.compile(r"^(?P<head>[^.]+?)\.{2,}(?P<gloss>.*)$")
FORM_RE = re.compile(r"^(?P<form>[A-Za-z]+)(?:\s+(?P<parse>.+))?$")

# Parsing check: the parsing text is kept VERBATIM, but to tell a form line from
# anything else, every piece of it must be a known parsing term. Pieces = the text
# split on spaces, dots and hyphens, with a glued "or" cut off ("inf.or", "3plor").
# Terms grown from the data; an unknown piece leaves the line "unparsed" (reported).
PARSE_ATOMS = {
    "nom", "gen", "dat", "acc", "voc", "sg", "pl", "du",
    "masc", "fem", "neut", "or",
    "pres", "imprf", "impf", "fut", "aor", "2aor", "prf", "perf", "2prf", "plprf", "2plprf",
    "act", "mid", "pass", "m", "p",
    "ind", "subj", "sub", "opt", "impv", "inf", "ptcp",
    "1sg", "2sg", "3sg", "1pl", "2pl", "3pl", "1du", "2du", "3du",
    "indecl", "superl", "comp", "compar", "2fut", "contr", "dual",
    "1", "2", "3",                      # person ranges: "1-3sg", "1sg-3pl"
    "plpf",
}
# Short notes the book prints after some forms (kept verbatim, counted).
NOTE_ATOMS = {"alternate", "spelling", "contraction", "adverb", "personal", "pronoun",
              "before", "a", "consonant", "vowel", "indeclinable"}   # "acri before a consonant"
NOTE_HITS = Counter()
# Misprints in the book itself: accepted so the form is kept, parsing kept verbatim,
# and counted on their own line (never corrected).
SOURCE_TYPOS = {"imf", "pes", "3g", "non", "netu", "3sp", "pref", "fen", "imprv", "sub",
                "impfr", "2pref", "pf", "pre", "imperf", "press", "inmp", "3p", "ins", "sep",
                "aol", "noml", "inc", "nd", "3pll", "aot", "prees", "impef", "mas", "agg", "pers"}
TYPO_HITS = Counter()
UNKNOWN_ATOMS = Counter()


def atoms(parse):
    out = []
    for piece in re.split(r"[\s.\-]+", parse):
        if not piece:
            continue
        m = re.fullmatch(r"(.+?)or", piece)
        m2 = re.fullmatch(r"(\d)or(\d(?:sg|pl))", piece)
        if m2:
            out += [m2.group(1), "or", m2.group(2)]
        elif m and piece not in PARSE_ATOMS and m.group(1) in PARSE_ATOMS:
            out += [m.group(1), "or"]
        else:
            out.append(piece)
    return out


def parse_tokens_ok(parse, count=False):
    at = atoms(parse)
    bad = [a for a in at if a not in PARSE_ATOMS and a not in SOURCE_TYPOS and a not in NOTE_ATOMS]
    if count:
        UNKNOWN_ATOMS.update(bad)
    elif not bad:
        TYPO_HITS.update(a for a in at if a in SOURCE_TYPOS)
        NOTE_HITS.update(a for a in at if a in NOTE_ATOMS)
    return not bad


def unaccent(s):
    """Drop the accent placeholder and the stray space that can follow it."""
    return re.sub(ACCENT + r" ?", "", s)


def to_greek(s):
    return "".join(SYMBOL.get(c, c) for c in s)


def fold(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s or "") if not unicodedata.combining(c))
    return "".join(c for c in s.lower().replace("ς", "σ") if c.isalpha())


def pdftotext(pdf, mode):
    r = subprocess.run(["pdftotext", mode, "-eol", "unix", pdf, "-"],
                       capture_output=True)
    if r.returncode != 0:
        sys.exit(f"FATAL: pdftotext {mode} failed: {r.stderr.decode('latin-1')[:300]}")
    return r.stdout.decode("latin-1")          # 0xA2 accent placeholder stays one char


def page_lines(page):
    out = []
    for ln in page.split("\n"):
        if ln.strip() in ("", "ANALYTICAL LEXICON") or re.fullmatch(r"\s*\d+\s*", ln):
            continue
        out.append(ln.rstrip())
    return out


def split_columns(lines):
    """-> (left_lines, right_lines, collisions). The right column starts at the most
    common indent of text that follows a run of >= 3 spaces past the page middle."""
    width = max((len(l) for l in lines), default=0)
    starts = Counter()
    for l in lines:
        for m in re.finditer(r" {3,}(?=\S)", l):
            if m.end() > 0.35 * width:
                starts[m.end()] += 1
                break
    if not starts:
        return [l.strip() for l in lines], [], []
    R = starts.most_common(1)[0][0]
    left, right, coll = [], [], []
    for l in lines:
        if len(l) > R - 1 and l[R - 1] != " " and l[:R].strip() and l[R - 1:R + 1].strip():
            # text runs across the gutter: try the nearest gap of >= 2 spaces
            m = None
            for g in re.finditer(r" {2,}(?=\S)", l):
                if abs(g.end() - R) <= 8:
                    m = g
            if m is None:
                coll.append(l)
                left.append(l.strip())
                continue
            cut = m.end()
        else:
            cut = R
        if l[:cut].strip():
            left.append(l[:cut].strip())
        if l[cut:].strip():
            right.append(l[cut:].strip())
    return left, right, coll


def main():
    ap = argparse.ArgumentParser(description="ABP Analytical Lexicon PDF -> TSV (read-only).")
    ap.add_argument("pdf")
    ap.add_argument("--out", default=os.path.join(OUT_DIR, "analytical_lexicon.tsv"))
    ap.add_argument("--show-unparsed", type=int, default=40)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    layout = pdftotext(args.pdf, "-layout").split("\f")
    raw = pdftotext(args.pdf, "-raw").split("\f")

    entries = []        # dicts: num, pos, head, gloss, forms[(form, parse)], page
    cur = None
    state = None        # 'header' (expect headword) | 'forms'
    unparsed = []       # (page, line, why)
    collisions = []
    per_page_ours = Counter()
    wrapped = [0]
    gloss_wrapped = [0]
    two_word = [0]
    for pno, page in enumerate(layout, 1):
        lines = page_lines(page)
        if not lines:
            continue
        left, right, coll = split_columns(lines)
        collisions += [(pno, c) for c in coll]
        for ln in left + right:
            m = HEADER_RE.match(ln)
            if m:
                cur = {"num": m.group("num"), "pos": m.group("pos").strip(), "head": None,
                       "gloss": "", "forms": [], "page": pno}
                entries.append(cur)
                per_page_ours[pno] += 1
                state = "header"
                continue
            if HEADER_NONUM_RE.match(ln):
                unparsed.append((pno, ln, "entry line with no number"))
                cur, state = None, None
                continue
            if state == "header":
                m = HEAD_RE.match(ln)
                if m:
                    cur["head"] = unaccent(m.group("head")).strip()
                    cur["gloss"] = m.group("gloss").strip()
                    state = "forms"
                else:
                    unparsed.append((pno, ln, "expected headword...gloss"))
                continue
            if re.fullmatch(r"\d+", ln):
                if int(ln) != pno:
                    unparsed.append((pno, ln, "bare number that is not this page's number"))
                continue                      # the page number, landed in a column
            if state == "forms":
                t = unaccent(ln)
                m = FORM_RE.match(t)
                if m and (m.group("parse") is None or parse_tokens_ok(m.group("parse"))):
                    cur["forms"].append((m.group("form"), (m.group("parse") or "").strip()))
                    continue
                if (" " in (cur["head"] or "") and re.fullmatch(r"[A-Za-z]+ [A-Za-z]+", t.strip())
                        and t.strip().count(" ") == cur["head"].count(" ")):
                    cur["forms"].append((t.strip(), ""))   # two-word headword, two-word form ("duw duw")
                    two_word[0] += 1
                    continue
                if not cur["forms"] and not (m and m.group("parse") and parse_tokens_ok(m.group("parse"))):
                    cur["gloss"] = (cur["gloss"] + " " + ln.strip()).strip()   # gloss wrapped
                    gloss_wrapped[0] += 1
                    continue
                m2 = re.match(r"^(?P<form>[A-Za-z]+ [A-Za-z]+)\s+(?P<parse>.+)$", t)
                if m2 and parse_tokens_ok(m2.group("parse")):
                    cur["forms"].append((m2.group("form"), m2.group("parse").strip()))
                    two_word[0] += 1                   # "kateqlasa autouV" = verb + pronoun
                    continue
                if not m and cur["forms"] and parse_tokens_ok(t):
                    f_, p_ = cur["forms"][-1]          # parsing wrapped onto its own line
                    cur["forms"][-1] = (f_, (p_ + " " + t.strip()).strip())
                    wrapped[0] += 1
                    continue
                if m and m.group("parse"):
                    parse_tokens_ok(m.group("parse"), count=True)
                unparsed.append((pno, ln, "not a form line"))
                continue
            unparsed.append((pno, ln, "outside any entry"))

    # cross-check: entry-opening lines per page from -raw
    per_page_raw = Counter()
    for pno, page in enumerate(raw, 1):
        for ln in page.split("\n"):
            if LEADER_RE.search(ln.strip()):
                per_page_raw[pno] += 1
    page_diff = [(p, per_page_ours[p], per_page_raw[p])
                 for p in sorted(set(per_page_ours) | set(per_page_raw))
                 if per_page_ours[p] != per_page_raw[p]]

    nforms = 0
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write("ab_number\tlemma\tpos\tgloss\tform\tparsing\tlemma_keys\tform_keys\tpage\n")
        for e in entries:
            lemma = to_greek(e["head"] or "")
            if not e["forms"]:
                f.write(f"{e['num']}\t{lemma}\t{e['pos']}\t{e['gloss']}\t\t\t{e['head'] or ''}\t\t{e['page']}\n")
            for form, parse in e["forms"]:
                nforms += 1
                f.write(f"{e['num']}\t{lemma}\t{e['pos']}\t{e['gloss']}\t{to_greek(form)}\t{parse}"
                        f"\t{e['head'] or ''}\t{form}\t{e['page']}\n")

    print(f"pages {len([p for p in layout if p.strip()])} · entries {len(entries)} · forms {nforms}"
          f" · entries with no headword {sum(1 for e in entries if not e['head'])}"
          f" · entries with no forms {sum(1 for e in entries if not e['forms'])}")
    print(f"cross-check vs -raw: pages whose entry count differs: {len(page_diff)}"
          + (" -> " + ", ".join(f"p{p} ours {a} raw {b}" for p, a, b in page_diff[:20]) if page_diff else ""))
    print(f"gutter collisions (left text ran into the right column): {len(collisions)}")
    for p, c in collisions[:10]:
        print(f"   p{p}: {c[:150]}")
    print(f"parsing lines wrapped onto the next line (joined to their form): {wrapped[0]}")
    print(f"gloss lines wrapped onto the next line (joined to the gloss): {gloss_wrapped[0]}")
    print("misprinted parsing terms in the book (kept verbatim): "
          + "  ".join(f"{k!r}×{v}" for k, v in TYPO_HITS.most_common()))
    print("notes after a form (kept verbatim): " + "  ".join(f"{k!r}×{v}" for k, v in NOTE_HITS.most_common()))
    print(f"two-word forms (verb + pronoun): {two_word[0]}")
    print(f"entries with two numbers (e.g. '5484, 85'): {sum(1 for e in entries if ',' in e['num'])}"
          + "".join(f"  [{e['num']} {e['head']}]" for e in entries if ',' in e['num']))
    nums = Counter(e["num"] for e in entries)
    print("numbers the book prints on two entries (kept as printed; likely misprints): "
          + "  ".join(f"{n} [{', '.join(e['head'] for e in entries if e['num'] == n)}]"
                      for n, k in sorted(nums.items()) if k > 1))
    print(f"forms with no parsing: {sum(1 for e in entries for f_, p_ in e['forms'] if not p_)}")
    print("unknown parsing pieces on unparsed form-shaped lines: "
          + "  ".join(f"{k!r}×{v}" for k, v in UNKNOWN_ATOMS.most_common(30)))
    why = Counter(w for _, _, w in unparsed)
    print(f"unparsed lines: {len(unparsed)}  " + "  ".join(f"{k}={v}" for k, v in why.most_common()))
    for p, ln, w in unparsed[:args.show_unparsed]:
        print(f"   p{p} [{w}] {ln[:140]!r}")
    print(f"wrote {args.out}")

    # ── controls ─────────────────────────────────────────────────────────────
    fails = []
    def find(head):
        return [e for e in entries if e["head"] == head]
    for head, num, want, pos in (("agcisteuw", "70.4", "ἀγχιστεύω", "VERB"),
                                 ("agorasmoV", "60.1", "ἀγορασμός", "NOUN masculine")):
        hits = find(head)
        ok = len(hits) == 1 and hits[0]["num"] == num and \
            fold(to_greek(head)) == fold(want) and hits[0]["pos"] == pos
        print(f"CONTROL {head}: " + (f"{hits[0]['num']} {to_greek(head)} {hits[0]['pos']!r} "
                                     f"forms={len(hits[0]['forms'])}" if hits else "NOT FOUND")
              + f" (want {num} {want} {pos}) -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            fails.append(head)
    ok5 = per_page_ours[5] == 20
    print(f"CONTROL page 5 entries: {per_page_ours[5]} (want 20) -> {'PASS' if ok5 else 'FAIL'}")
    if not ok5:
        fails.append("page5")
    if fails:
        sys.exit(1)


if __name__ == "__main__":
    main()
