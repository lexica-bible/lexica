#!/usr/bin/env python3
"""Read-only, local: classify the split-rendering candidates (audit_split_rendering.py's
pairs.tsv) against the ABP source in abp_texts/.

A real split double = the two word rows come from ONE tagged source word: one `G<number>`
tag in the source whose English the build cut into two rows (the helper peel or the
numbered-slot split in build_words_from_abp._emit_words). Two separate tags with the same
number are two real Greek words (Gen 7:2 "seven G2033 by seven G2033"; Gen 3:16 "In
multiplying G4129 I will multiply G4129") and are not a split.

The live row positions are matched to the source by re-running the build's own
tokenisation (parse_abp_line, which goes through _emit_words): one emitted source word per
word row, in order. A pair is only classified when both live rows line up with source
words that carry the pair's number; anything else is named "unmatched" for a hand read.

  python scripts/classify_split_pairs.py PAIRS_TSV OUT_TSV
  python scripts/classify_split_pairs.py --source-scan PAIRS_TSV CLASSIFIED_TSV OUT_TSV

Touches no database. Writes OUT_TSV only.
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_words_from_abp import (_STRONGS_RE, _emit_words, _VERSE_RE,  # noqa: E402
                                  ABP_OT_DIR, ABP_NT_DIR)

# The pronoun retag rewrites G1473 slots to the σύ / αὐτός / ἡμεῖς / ὑμεῖς numbers at build.
PRONOUN_FAMILY = {"1473", "4771", "846", "2249", "5210", "1438", "848", "4572", "1683"}


def source_verses():
    out = {}
    for d in (ABP_OT_DIR, ABP_NT_DIR):
        for txt in sorted(Path(d).glob("*.txt")):
            for line in txt.read_text(encoding="utf-8", errors="replace").splitlines():
                m = _VERSE_RE.match(line.strip())
                if m:
                    out[f"{m.group(1)} {m.group(2)}:{m.group(3)}"] = m.group(4)
    return out


def tokens(text):
    """-> [(english, strongs_bare, chunk_index, raw_chunk_text)], one per emitted word,
    in the same order and count as parse_abp_line (so index = word row position)."""
    parts = _STRONGS_RE.split(text)
    out, k, i = [], 0, 0
    while i < len(parts) - 1:
        tag = parts[i + 1]
        bare = "*" if tag == "G*" else tag[1:]
        for w in _emit_words(parts[i], tag):
            out.append((w[0], bare, k, parts[i].strip() + tag))
        k += 1
        i += 2
    if parts and parts[-1].strip():
        for w in _emit_words(parts[-1], None):
            out.append((w[0], "", k, parts[-1].strip()))
    return out


APP_SLOTS = HERE.parent / "abp_helps" / "abp_app_slots_full.tsv"


def app_verses():
    """The ABP app's own slots (abp_helps/abp_app_slots_full.tsv): one slot per Greek word
    (or a few joined, '305-*'), with the English the app prints for it. An independent
    second reading of the same question."""
    from audit_abp_app_vs_surface import APP_TO_ABBREV
    out = {}
    with open(APP_SLOTS, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            k = f"{APP_TO_ABBREV[r['book']]} {r['chapter']}:{r['verse']}"
            nums = [x.split(".")[0] if x != "*" else "*" for x in (r["strongs"] or "").split("-")]
            full = (r["strongs"] or "").split("-")
            out.setdefault(k, []).append((full, nums, words(r["english"])))
    return out


def words(s):
    return sorted(w for w in re.sub(r"[^a-z\s]", " ", (s or "").lower()).split())


def app_reading(slots, strongs, e1, e2):
    """'one-slot' = one app slot carrying the number prints both pieces' English;
    'two-slots' = two app slots carrying the number print one piece each; else 'unclear'."""
    if slots is None:
        return "no app verse"
    base = strongs.split(".")[0]
    cand = [i for i, (full, nums, _) in enumerate(slots)
            if strongs in full or any(same_num(n, base) for n in nums)]
    w1, w2 = words(e1), words(e2)
    if any(slots[i][2] == sorted(w1 + w2) for i in cand):
        return "one-slot"
    i1 = [i for i in cand if slots[i][2] == w1]
    i2 = [j for j in cand if slots[j][2] == w2]
    if any(i != j for i in i1 for j in i2):
        return "two-slots"
    return "unclear"


def same_num(a, b):
    return a == b or (a in PRONOUN_FAMILY and b in PRONOUN_FAMILY)


def classify(src, verse, strongs, pos):
    text = src.get(verse)
    if text is None:
        return "unmatched", "verse not in abp_texts", "", ""
    toks = tokens(text)
    if pos + 1 >= len(toks):
        return "unmatched", f"source has {len(toks)} words, pair at {pos}", "", ""
    a, b = toks[pos], toks[pos + 1]
    if not (same_num(a[1], strongs) and same_num(b[1], strongs)):
        return ("unmatched", f"source numbers at {pos},{pos + 1} = {a[1] or '-'},{b[1] or '-'}",
                a[0] or "", b[0] or "")
    if a[2] == b[2]:
        return "split", f"one tag: {a[3]}", a[0] or "", b[0] or ""
    return "two-words", f"two tags: {a[3]} | {b[3]}", a[0] or "", b[0] or ""


def cut_words(text, strongs):
    """How many source tags with this number the build cuts into 2+ rows, and how many tags carry it.
    No cut tag in the verse = every row with the number comes from its own tag (two Greek words),
    whatever later build step moved English between the rows."""
    per = Counter(k for _, s, k, _ in tokens(text) if same_num(s, strongs))
    return sum(1 for n in per.values() if n >= 2), len(per)


# Two Greek words whose source tag on one of them is the wrong number (found in passing; label lane).
MISLABEL = {
    ("Jos 18:22", "2532"): "Beth-el is tagged G2532 (and) in the source; a name, G*",
    ("1Ch 6:62", "575"): "'and' is tagged G575 (from) in the source; the printed form is και, G2532",
    ("Jer 50:39", "2532"): "'generation.' is tagged G2532 in the source; the word is γενεάς, G1074",
    ("Dan 1:2", "2532"): "'of the LORD.' is tagged G2532 in the source; the word is κυρίου, G2962",
}


def verdict(src, r, cls):
    v, st = r["verse"], r["strongs"]
    if cls == "split":
        return "SPLIT: one Greek word on two rows"
    cut, tags = cut_words(src.get(v, ""), st)
    if cut:
        return f"CHECK BY HAND: {cut} cut tag(s) with this number in the verse"
    why = MISLABEL.get((v, st))
    if why:
        return f"NOT A SPLIT: two Greek words ({tags} tags); label error: {why}"
    if cls == "unmatched":
        return (f"NOT A SPLIT: two Greek words ({tags} tags, none cut); a build step swapped row "
                "positions (_split_compounds), so the rows no longer line up with the source by position")
    return f"NOT A SPLIT: two Greek words ({tags} tags, none cut)"


def source_scan(pairs_path, classified_path, out_path):
    """The other direction: every source tag the build cuts into 2+ rows, canon-wide (name tags G*
    left out, as the detector does), that the detector did not list as a split pair. A cut whose
    first piece is a helper peeled out in front of a bracket the build itself strips
    (build_words_from_abp._strip_helper_double_tag / helper_ok) is counted, not listed."""
    from build_words_from_abp import helper_ok
    frozen = HERE.parent / "tests" / "fixtures" / "split_rendering" / "list_628_20261025.tsv"
    with open(frozen, encoding="utf-8", newline="") as f:
        f628 = {(f"{r['book']} {r['chapter']}:{r['verse']}", r["strongs"]): r["shape"]
                for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)}
    with open(classified_path, encoding="utf-8", newline="") as f:
        found = {(r["verse"], int(r["position"])) for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
                 if r["class"] == "split"}
    tally, out = Counter(), []
    for v, text in source_verses().items():
        parts, i, pos = _STRONGS_RE.split(text), 0, 0
        while i < len(parts) - 1:
            tag = parts[i + 1]
            em = _emit_words(parts[i], tag)
            if len(em) >= 2 and tag != "G*":
                bare = tag[1:]
                lead = em[0][2] is None and not em[0][3] and not em[0][4] and (em[1][3] or em[1][2] is not None)
                shape = ("lead" if lead else "num") + "+" + "+".join(
                    "trail" if (w[2] is None and j == len(em) - 1) else "num" for j, w in enumerate(em[1:], 1))
                stripped = lead and helper_ok(em[0][0], bare)
                # every neighbouring pair that still shares the tag after the build's own strip
                want = [j for j in range(1 if stripped else 0, len(em) - 1)]
                got = [j for j in want if (v, pos + j) in found]
                hit = bool(want) and len(got) == len(want)
                where = ("detector" if hit else "detector, in part (first piece missed)" if got else
                         "10/25 list: " + f628[(v, bare)] if (v, bare) in f628 else "no list")
                tally[(shape, "build strips the helper" if stripped else "kept", where)] += 1
                if want and not hit:
                    out.append((v, bare, pos, shape, " | ".join(w[0] or "" for w in em), where,
                                 "build strips the helper" if stripped else ""))
            pos += len(em)
            i += 2
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("verse\tstrongs\tsource_position\tshape\tpieces\tlisted\tnote\n")
        for x in out:
            f.write("\t".join(str(c) for c in x) + "\n")
    print("cut source tags, canon-wide (shape, helper, where):")
    for k in sorted(tally):
        print(f"  {k}: {tally[k]}")
    print(f"not found by the detector, listed: {len(out)}")


def main():
    if sys.argv[1] == "--source-scan":
        source_scan(*sys.argv[2:5])
        return
    pairs_path, out_path = sys.argv[1], sys.argv[2]
    src = source_verses()
    app = app_verses()
    with open(pairs_path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    tally = Counter()
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        cols = list(rows[0].keys()) + ["class", "app", "src_eng_1", "src_eng_2", "evidence", "verdict"]
        f.write("\t".join(cols) + "\n")
        verdicts = Counter()
        for r in rows:
            cls, ev, e1, e2 = classify(src, r["verse"], r["strongs"], int(r["position"]))
            ar = app_reading(app.get(r["verse"]), r["strongs"], r["english_1"], r["english_2"])
            vd = verdict(src, r, cls)
            tally[(cls, ar)] += 1
            verdicts[vd.split(":")[0] + (" (label error)" if "label error" in vd else "")
                     + (" (positions swapped)" if "swapped" in vd else "")] += 1
            f.write("\t".join([r[c] for c in rows[0].keys()] + [cls, ar, e1, e2, ev.replace("\t", " "), vd])
                    + "\n")
    print(f"pairs read: {len(rows)}")
    for k in sorted(tally):
        print(f"  source {k[0]:10} app {k[1]:13} {tally[k]}")
    print("verdicts:")
    for k in sorted(verdicts):
        print(f"  {k}: {verdicts[k]}")


if __name__ == "__main__":
    main()
