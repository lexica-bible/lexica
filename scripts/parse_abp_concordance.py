"""ABP Lexical Concordance PDF -> per-number verse lists (read-only, local).

Reads JP's lexical_concordance.pdf (NOT in the repo) through `pdftotext -raw`, which follows the
page's 7 columns in reading order (checked: guide words + every entry's refs come out in Bible
order). Writes ONLY into abp_helps/ (gitignored). Never touches a database.

Rules come from the 2026-10-25 census (TODO "Concordance verse-list diff" notes):
  * headings: "headword NUM", number on its own line, number glued on, headword split at the
    accent mark or hyphen-split across lines, variant endings ("-ssw" / "-omai NUM"), a bracketed
    second number "39 (40)", two numbers on one heading ("3017,18" Levi -> 3017 + 3018).
  * symbol font: Lexicon letter map; 0xA2 = accent mark (dropped), '+' = ϊ, '=' = ϋ; 0xAD = dash.
  * refs: book abbreviation on a run's first ref only; "ch:v,v,v"; dash ranges (may wrap across a
    line); '*' = the word 2+ times in that verse; title/tit = verse 0; "Ps 2:title–9" = the
    superscriptions of Psalms 2 THROUGH 9 (a chapter range of titles, not verses 0..9).
  * no-verse-list entries are classified and set aside (names, proper titles, Far & wide, See /
    Included pointers, unused words, other).
  * print-error ref lines are fixed ONLY through scripts/concordance_handmap.tsv (one hand-ruled
    row per raw line). A line that does not parse and is not in that table is a FAILURE, listed.

Usage:  python scripts/parse_abp_concordance.py <lexical_concordance.pdf>
Out:    abp_helps/concordance_entries.tsv · concordance_refs.tsv · concordance_failures.tsv
"""
import argparse
import csv
import os
import re
import subprocess
import sys
import unicodedata
from collections import Counter

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
OUT_DIR = os.path.join(REPO, "abp_helps")
HANDMAP = os.path.join(REPO, "scripts", "concordance_handmap.tsv")

ACC, DASH = "\xa2", "\xad"
RH = "L E X I C A L C O N C O R D A N C E"
CONTENT_PAGES = 364
LOWER = dict(zip("abgdezhqiklmnxoprsVtufcyw", "αβγδεζηθικλμνξοπρσςτυφχψω"))
UPPER = dict(zip("ABGDEZHQIKLMNXOPRSTUFCYW", "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"))
SYMBOL = {**UPPER, **LOWER, "+": "ϊ", "=": "ϋ"}

# Concordance abbreviation -> abp_texts / verses.book code (67 -> 66 books; census 2026-10-25).
BOOKS = {"Gen": "Gen", "Ex": "Exo", "Lev": "Lev", "Nm": "Num", "Dt": "Deu", "Jos": "Jos",
         "Jdg": "Jdg", "Rt": "Rth", "1Sa": "1Sa", "2Sa": "2Sa", "1Ki": "1Ki", "2Ki": "2Ki",
         "1Ch": "1Ch", "2Ch": "2Ch", "Ezr": "Ezr", "Neh": "Neh", "Est": "Est", "Job": "Job",
         "Ps": "Psa", "Pr": "Pro", "Ecc": "Ecc", "So": "Son", "Is": "Isa", "Jer": "Jer",
         "Lam": "Lam", "Eze": "Eze", "Dan": "Dan", "Hos": "Hos", "Jl": "Joe", "Am": "Amo",
         "Ob": "Oba", "Jon": "Jon", "Mi": "Mic", "Nah": "Nah", "Hab": "Hab", "Zep": "Zep",
         "Hag": "Hag", "Zec": "Zec", "Mal": "Mal", "Mt": "Mat", "Mk": "Mar", "Lk": "Luk",
         "Jn": "Joh", "Act": "Act", "Acts": "Act", "Rm": "Rom", "1Co": "1Co", "2Co": "2Co",
         "Gal": "Gal", "Eph": "Eph", "Phi": "Php", "Col": "Col", "1Th": "1Th", "2Th": "2Th",
         "1Ti": "1Ti", "2Ti": "2Ti", "Tit": "Tit", "Plm": "Phm", "Heb": "Heb", "Js": "Jas",
         "1P": "1Pe", "2P": "2Pe", "1Jn": "1Jn", "2Jn": "2Jn", "3Jn": "3Jn", "Jde": "Jud",
         "Rev": "Rev"}
CANON = ["Gen", "Exo", "Lev", "Num", "Deu", "Jos", "Jdg", "Rth", "1Sa", "2Sa", "1Ki", "2Ki",
         "1Ch", "2Ch", "Ezr", "Neh", "Est", "Job", "Psa", "Pro", "Ecc", "Son", "Isa", "Jer",
         "Lam", "Eze", "Dan", "Hos", "Joe", "Amo", "Oba", "Jon", "Mic", "Nah", "Hab", "Zep",
         "Hag", "Zec", "Mal", "Mat", "Mar", "Luk", "Joh", "Act", "Rom", "1Co", "2Co", "Gal",
         "Eph", "Php", "Col", "1Th", "2Th", "1Ti", "2Ti", "Tit", "Phm", "Heb", "Jas", "1Pe",
         "2Pe", "1Jn", "2Jn", "3Jn", "Jud", "Rev"]
RANK = {b: i for i, b in enumerate(CANON)}

NUMS = r"\d+(?:\.\d+)*(?:,\s*\d+(?:\.\d+)*)*"
L = r"A-Za-z+=" + ACC
HEAD_RE = re.compile(r"^(?P<head>[" + L + r"](?:[" + L + r" ,'()\-]*?[" + L + r"\-])?)\s*(?P<num>"
                     + NUMS + r"),?(?:\s*\((?P<alt>" + NUMS + r")\))?$")
HWLIKE_RE = re.compile(r"^[" + L + r"][" + L + r" ,'\-]*[" + L + r"\-]$|^[A-Za-z]$")
NUMONLY_RE = re.compile(r"^(?:" + NUMS + r"),?(?:\s*\((?:" + NUMS + r")\))?$")
HEADLESS_RE = re.compile(r"^\d+(?:\.\d+)*(?:" + DASH + r"\d+)?$")   # "2717", "3203–3302"
HEADLESS = "HEADLESS "
TYPO_REF_RE = re.compile(r"^[1-3]?[A-Za-z]+\.?\s*,?\s*\d+:")      # "Jdg. 14:9", "1SA 18:4", "Gal, 4:4"
VARIANT_TAIL_RE = re.compile(r"^-[" + L + r"]+\s*" + NUMS + r"$")
NOT_HEAD = ("Strong", "See", "see", "Heb", "Aram", "Included")
ENGLISH = {"of", "about", "in", "the", "and", "measure", "see", "Included", "Strong"}
BOOK_RE = re.compile(r"^(?P<bk>[1-3]?[A-Z][a-z]{0,4})\s+(?P<ch>\d+):(?P<vs>.*)$")
CHAP_RE = re.compile(r"^(?P<ch>\d+):(?P<vs>.*)$")
CONT_RE = re.compile(r"^[\d,*" + DASH + r"]+$")
VITEM = r"(?:\d+|title|tit)\*?(?:" + DASH + r"\d+\*?)?"
VLIST_RE = re.compile(r"^" + VITEM + r"(?:," + VITEM + r")*,?$")


def to_greek(s):
    return "".join(SYMBOL.get(c, c) for c in s.replace(ACC, ""))


def keys(num):
    """'3017,18' -> ['3017','3018']; '5484, 85' -> ['5484','5485']; '1510.2.3' -> itself."""
    parts = [p.strip() for p in num.split(",") if p.strip()]
    out = [parts[0]]
    for p in parts[1:]:
        if len(p) < len(parts[0]) and "." not in p and "." not in parts[0]:
            p = parts[0][: len(parts[0]) - len(p)] + p
        out.append(p)
    return out


def is_ref_line(l):
    return bool(BOOK_RE.match(l) or CHAP_RE.match(l) or CONT_RE.match(l))


def clean_page(text):
    """-> (printed page number, guide word, content lines)."""
    ls = [l.strip() for l in text.split("\n") if l.strip()]
    pnum = ls.pop() if ls and re.fullmatch(r"\d+", ls[-1]) else None
    joined, buf = [], ""
    for l in ls:
        if l.endswith(ACC) or l == ACC:              # headword split at the accent mark
            buf += l; continue
        if re.fullmatch(r"[" + L + r"]+-", l):        # hyphen-split headword
            buf += l[:-1]; continue
        joined.append(buf + l if buf else l); buf = ""
    if buf:
        joined.append(buf)
    guide, out = None, []
    for l in joined:
        if RH in l:
            guide = l.replace(RH, "").strip(); continue
        out.append(l)
    return pnum, guide, out


def merge_lines(lines):
    """Heading on two lines (headword / number) and variant tails ('-omai 4909.1')."""
    merged, i = [], 0
    while i < len(lines):
        l = lines[i]
        if (i + 1 < len(lines) and HWLIKE_RE.match(l) and NUMONLY_RE.match(lines[i + 1])
                and l.split()[0] not in NOT_HEAD):
            merged.append(l + " " + lines[i + 1]); i += 2; continue
        if merged and merged[-1].endswith("&") and NUMONLY_RE.match(l):
            merged[-1] += " " + l; i += 1; continue           # note tail: "Strong 2077 &" / "2468"
        if (HEADLESS_RE.match(l) and i + 1 < len(lines) and not is_ref_line(lines[i + 1])
                and not TYPO_REF_RE.match(lines[i + 1]) and not heading(lines[i + 1])
                and merged and not merged[-1].endswith((",", "&", DASH))):
            merged.append(HEADLESS + l); i += 1; continue     # entry with no headword: "2717" / "An unused word…"
        if (merged and VARIANT_TAIL_RE.match(l) and merged[-1].endswith(",")
                and HWLIKE_RE.match(merged[-1].rstrip(","))):
            merged[-1] += " " + l; i += 1; continue
        merged.append(l); i += 1
    return merged


def heading(l):
    m = HEAD_RE.match(l)
    if not m or is_ref_line(l):
        return None
    toks = m.group("head").replace(",", " ").split()
    if toks[0] in NOT_HEAD or any(t in ENGLISH for t in toks):
        return None
    return m


def entry_class(gloss, has_refs):
    g = " ".join(gloss)
    if re.match(r"Proper (place )?name", g): return "proper name"
    if g.startswith("Proper title"): return "proper title"
    if "Far & wide" in g: return "far & wide"
    if re.search(r"[Uu]nused word", g): return "unused word"
    if has_refs: return "has verses"
    if re.search(r"\b[Ss]ee\b", g): return "see-pointer"
    if "Included" in g: return "included-in"
    return "no-verse other"


def load_handmap():
    hm = {}
    if not os.path.exists(HANDMAP):
        return hm
    with open(HANDMAP, encoding="utf-8") as f:
        for row in csv.DictReader((l for l in f if not l.startswith("#")), delimiter="\t"):
            row["raw"] = row["raw"].replace("–", DASH)
            row["mapped"] = row["mapped"].replace("–", DASH)
            hm[(int(row["page"]), row["entry"], row["raw"])] = row
    return hm


def parse_vlist(vs, bk, ch, page, num, raw, refs, src):
    for part in vs.rstrip(",").split(","):
        star = "*" in part
        part = part.replace("*", "")
        a, _, b = part.partition(DASH)
        if a in ("title", "tit") and b:
            # "Ps 2:title–9" = the SUPERSCRIPTIONS of Psalms 2 through 9 (verse 0 of each chapter),
            # not verses 0..9 — checked 2026-10-25: every such range matches abp_texts' titles.
            for c in range(ch, int(b) + 1):
                refs.append(dict(book=bk, ch=c, vs=0, star=int(star), src=src or "title-range"))
            continue
        a = 0 if a in ("title", "tit") else int(a)
        b = int(b) if b else a
        for v in range(a, b + 1):
            refs.append(dict(book=bk, ch=ch, vs=v, star=int(star),
                             src=src or ("range" if b != a else ("title" if v == 0 else ""))))


def parse_refs(e, handmap, failures, hm_used):
    """Turn an entry's ref lines into verse refs. Wrapped lines are joined first."""
    lines = []
    for l in e["reflines"]:
        if lines and (lines[-1].endswith(",") or lines[-1].endswith(DASH)) and CONT_RE.match(l):
            lines[-1] += l; continue
        lines.append(l)
    refs, bk, ch = [], None, None
    for raw in lines:
        src = ""
        hk = (e["page"], e["num"], raw)
        line = raw
        if hk in handmap:
            hm_used.add(hk)
            row = handmap[hk]
            if row["mapped"] == "DROP":
                continue
            line, src = row["mapped"], ("footnote" if row["kind"] == "footnote" else "handmap")
        m = BOOK_RE.match(line)
        if m:
            if m.group("bk") not in BOOKS:
                failures.append((e["page"], e["num"], raw, "unknown book")); continue
            bk, ch, vs = BOOKS[m.group("bk")], int(m.group("ch")), m.group("vs")
        else:
            m = CHAP_RE.match(line)
            if m:
                ch, vs = int(m.group("ch")), m.group("vs")
            else:
                failures.append((e["page"], e["num"], raw, "not a reference")); continue
        if bk is None:
            failures.append((e["page"], e["num"], raw, "no book yet")); continue
        if not VLIST_RE.match(vs):
            failures.append((e["page"], e["num"], raw, "verse list unreadable")); continue
        parse_vlist(vs, bk, ch, e["page"], e["num"], raw, refs, src)
    return refs


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pdf")
    args = ap.parse_args()
    r = subprocess.run(["pdftotext", "-raw", "-eol", "unix", args.pdf, "-"], capture_output=True)
    if r.returncode:
        sys.exit("FATAL: pdftotext failed: " + r.stderr.decode("latin-1")[:300])
    pages = r.stdout.decode("latin-1").split("\f")[:CONTENT_PAGES]
    handmap = load_handmap()

    entries, stray, pinfo = [], [], {}
    for pno, text in enumerate(pages, 1):
        pnum, guide, lines = clean_page(text)
        here = []
        for l in merge_lines(lines):
            if l.startswith(HEADLESS):
                e = dict(page=pno, head="", num=l[len(HEADLESS):], alt="", gloss=[], reflines=[])
                entries.append(e); here.append(e); continue
            m = heading(l)
            if m:
                e = dict(page=pno, head=m.group("head"), num=m.group("num"), alt=m.group("alt") or "",
                         gloss=[], reflines=[])
                entries.append(e); here.append(e); continue
            if re.fullmatch(r"[A-Z] ?[a-z]", l):          # section letter "A a"
                continue
            if not entries:
                stray.append((pno, l)); continue
            e = entries[-1]
            if is_ref_line(l):
                e["reflines"].append(l)
            elif TYPO_REF_RE.match(l):
                e["reflines"].append(l)                    # ref with a typo'd book ("Jdg.", "1SA")
            else:
                (e.setdefault("after", []) if e["reflines"] else e["gloss"]).append(l)
        pinfo[pno] = dict(pnum=pnum, guide=guide, first=here[0]["head"] if here else None,
                          last=here[-1]["head"] if here else None, n=len(here))

    failures, hm_used = [], set()
    for e in entries:
        e["refs"] = parse_refs(e, handmap, failures, hm_used)
        e["cls"] = entry_class(e["gloss"], bool(e["refs"]))

    # ---- checks
    norm = lambda s: (s or "").replace(ACC, "").replace(" ", "")
    gw_bad, carry = [], None
    for p in sorted(pinfo):
        i = pinfo[p]; g = norm(i["guide"])
        ok = (g == norm(i["last"] or carry)) if p % 2 else g in (norm(carry or i["first"]), norm(i["first"]))
        if not ok: gw_bad.append(p)
        if i["last"]: carry = i["last"]
    pn_bad = [p for p, i in pinfo.items() if i["pnum"] != str(p)]
    kc = Counter(k for e in entries for k in keys(e["num"]))
    dup = sorted(k for k, c in kc.items() if c > 1)
    order_bad = []
    for e in entries:
        seq = [(RANK[x["book"]], x["ch"], x["vs"]) for x in e["refs"]]
        if any(b < a for a, b in zip(seq, seq[1:])):
            order_bad.append((e["page"], e["num"]))
    hm_unused = [k for k in handmap if k not in hm_used]
    lost = [(e["page"], e["num"], t) for e in entries for t in e["gloss"] + e.get("after", [])
            if re.search(r"\d+:\d+", t)]
    dupv = []
    for e in entries:
        c = Counter((x["book"], x["ch"], x["vs"]) for x in e["refs"])
        dupv += [(e["page"], e["num"], k) for k, n in c.items() if n > 1]

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "concordance_entries.tsv"), "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["page", "num", "keys", "alt_keys", "headword_raw", "headword", "class", "verses",
                    "starred", "gloss"])
        for e in entries:
            w.writerow([e["page"], e["num"], " ".join(keys(e["num"])),
                        " ".join(keys(e["alt"])) if e["alt"] else "", e["head"].replace(ACC, "´"),
                        to_greek(e["head"]), e["cls"], len(e["refs"]),
                        sum(x["star"] for x in e["refs"]), " ".join(e["gloss"])[:120]])
    with open(os.path.join(OUT_DIR, "concordance_refs.tsv"), "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["num", "keys", "alt_keys", "book", "chapter", "verse", "star", "src", "page"])
        for e in entries:
            for x in e["refs"]:
                w.writerow([e["num"], " ".join(keys(e["num"])), " ".join(keys(e["alt"])) if e["alt"] else "",
                            x["book"], x["ch"], x["vs"], x["star"], x["src"], e["page"]])
    with open(os.path.join(OUT_DIR, "concordance_failures.tsv"), "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["page", "entry", "raw", "why"])
        for x in failures:
            w.writerow([x[0], x[1], x[2].replace(DASH, "–").replace(ACC, "´"), x[3]])

    # ---- controls (census + lane (2) live-confirmed verse counts)
    by = {}
    for e in entries:
        for k in keys(e["num"]):
            by[k] = e
    ctl = []
    abra = by.get("10.3")
    ctl.append(("10.3 ἅβρα = Gen 24:61 · Exo 2:5* · Est 2:9, 4:4, 4:16",
                abra and [(x["book"], x["ch"], x["vs"], x["star"]) for x in abra["refs"]] ==
                [("Gen", 24, 61, 0), ("Exo", 2, 5, 1), ("Est", 2, 9, 0), ("Est", 4, 4, 0), ("Est", 4, 16, 0)]))
    for k, nv in (("2241", 1), ("5411", 24), ("303", 14), ("1047", 7), ("4577", 5)):
        got = len(by[k]["refs"]) if k in by else None
        ctl.append((f"{k} verse list = {nv} verses (got {got})", got == nv))
    stars5 = sum(x["star"] for k in ("2241", "5411", "303", "1047", "4577") if k in by for x in by[k]["refs"])
    ctl.append((f"the 5 words carry 4 starred verses (got {stars5})", stars5 == 4))
    ctl.append(("entry 1 (A, alpha) parsed with Rev 1:8, 21:6, 22:13",
                "1" in by and [(x["book"], x["ch"], x["vs"]) for x in by["1"]["refs"]] ==
                [("Rev", 1, 8), ("Rev", 21, 6), ("Rev", 22, 13)]))
    ctl.append(("Levi 3017,18 = two keys", "3017" in by and "3018" in by and by["3017"] is by["3018"]))

    refs_all = [x for e in entries for x in e["refs"]]
    print(f"pages {CONTENT_PAGES} · entries {len(entries)} · number keys {len(kc)} · "
          f"bracket second numbers {sum(1 for e in entries if e['alt'])}")
    print("classes:", dict(Counter(e["cls"] for e in entries)))
    print(f"verse refs {len(refs_all)} · starred {sum(x['star'] for x in refs_all)} · "
          f"from ranges {sum(1 for x in refs_all if x['src'] == 'range')} · title (verse 0) "
          f"{sum(1 for x in refs_all if x['vs'] == 0)} · via hand-map {sum(1 for x in refs_all if x['src'] == 'handmap')}")
    print(f"ref lines that failed: {len(failures)} · hand-map rows {len(handmap)} used {len(hm_used)} unused {len(hm_unused)}")
    for x in failures:
        print("   FAIL", x[0], x[1], repr(x[2].replace(DASH, "–")), "-", x[3])
    for k in hm_unused:
        print("   HANDMAP ROW NOT USED", k)
    print(f"checks: guide-word mismatches {len(gw_bad)} {gw_bad} · page-number mismatches {len(pn_bad)} · "
          f"numbers on 2+ headings {len(dup)} {dup[:5]} · entries whose refs go out of Bible order {len(order_bad)} {order_bad[:8]}")
    print(f"stray lines before entry 1: {len(stray)} · headless entries {[e['num'].replace(DASH, '–') for e in entries if not e['head']]}")
    print(f"text lines that still hold a ch:vs (possible lost refs): {len(lost)}")
    for x in lost:
        print("   LOST?", x[0], x[1], repr(x[2].replace(ACC, "´")))
    print(f"verses listed twice inside one entry: {len(dupv)}", dupv)
    for name, ok in ctl:
        print(("   PASS " if ok else "   FAIL ") + name)


if __name__ == "__main__":
    main()
