#!/usr/bin/env python3
"""Local, read-only: draft the rows file for the split-rendering double rows (TODO "Split-rendering
double rows"; DESIGN 9.274(3), 9.275). Touches no database.

Input: classify_split_pairs.py's output for the detector's 11/23 PA run (pairs.tsv, 784 pairs).
Only the pairs classified "split" (one tagged source word cut into two or three rows by the build)
are drafted. Each such Greek word keeps its number on ONE row; every other row of the word loses
strongs + strongs_base (english, english_head, greek_pos and bracket_id stay, so the reading order
and the printed English do not move - the same shape the build already gives a peeled helper word,
build_words_from_abp._strip_helper_double_tag). The printed Greek form goes with the number: a row
that loses its number loses its abp_surface form; when the kept row has none, the form moves there.

Which row keeps the number:
  1. Drop pieces that are only helper words (scaffold: may, let, shall, will, I, they, ...), a
     translator connective (", no.", ", saying,", ", and", "that", "was of", "do."), or English the
     translator added with no Greek behind it (Isa 1:6 "inflamed | are healed;": no verb for "healed").
  2. A prefixed verb keeps the piece that renders the root verb ("cast | out" -> cast;
     "have carried | away" -> have carried; "put | upon it" -> put).
  2b. A simple verb or adjective followed by a piece that only renders its manner, degree or a
     supplied object keeps the verb / adjective ("loved | passionately", "seizing | by force",
     "uttering | sounds,", "strong | enough", "they cast | in a furnace;").
  3. A verb built on a noun or adjective keeps the piece carrying that stem ("made | desolate" ->
     desolate; "give | to drink" -> to drink; "treat | with contempt" -> with contempt).
  4. Where two pieces render one simple verb between them, the piece holding the head word the build
     would give the joined English decides (how every unsplit occurrence is counted).
Rule 1 alone settles a word when exactly one piece is not a helper/connective (AUTO); when every
piece is a helper word ("let | be", "may | not") the verb's own word is the last piece (AUTO-LAST);
everything else is a hand pick, listed in HAND below with the English of the kept piece.
HELD: three words whose second piece is the English of the NEXT, blank Greek word parked on a
function word (splitter polarity B, its own lane): Exo 33:3, Eze 28:3, Eze 36:14.

  python scripts/draft_split_double_rows.py CLASSIFIED_TSV ROWS_OUT
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from classify_split_pairs import source_verses, tokens  # noqa: E402
from build_words_from_abp import SCAFFOLD_WORDS  # noqa: E402

CONNECTIVES = {", no.", ", saying,", ", and", "and", "that", "was of", "do.", "so."}

# (verse, strongs) -> the live English of the piece that keeps the number. None = the piece whose
# English contains "put" (1Ki 18:23 has two such words: "put | upon it!" and "will I put | upon it.").
HAND = {
    # rule 1 where the auto pass mis-reads a word as content ("to", "there", "if")
    ("Gen 44:26", "3361"): "is not", ("1Sa 20:26", "1510.1"): "be;", ("Job 12:6", "1510.8.3"): "be.",
    ("Jas 3:1", "1096"): "be,", ("Act 27:10", "1510.9"): "to be", ("1Sa 20:2", "3778"): "This",
    ("Num 27:3", "1096"): "born", ("Heb 8:7", "2212"): "be sought", ("Tit 3:2", "987"): "blaspheme,",
    ("Act 2:2", "4157"): "breath", ("1Ki 18:27", "96.2"): "meditation", ("Job 4:16", "3444"): "an appearance",
    ("2Sa 14:14", "2983"): "take", ("Pro 28:13", "2137"): "be prospered;", ("Jer 24:2", "1520"): "one",
    ("Jer 24:2", "2087"): "other", ("Isa 1:6", "5392.1"): "inflamed", ("Deu 4:38", "2478"): "stronger",
    ("Eze 14:19", "1883.4"): "I should send", ("Job 6:10", "5574"): "I lied", ("Act 27:33", "4355"): "having taken",
    # rule 2b: simple verb / adjective + a manner, degree or supplied-object piece -> the verb / adjective
    ("Luk 16:3", "2480"): "strong", ("Est 2:17", "2037.1"): "loved", ("Eze 22:25", "726"): "seizing",
    ("Jer 10:14", "5560.9"): "they cast", ("2Pe 2:18", "5350"): "uttering",
    ("Heb 5:1", "2525"): "is established", ("Pro 3:15", "514"): "worth", ("Psa 21:3", "4399"): "beforehand",
    # rule 2: prefixed verb -> the root verb's piece
    ("Exo 5:21", "1929"): "give", ("Exo 12:39", "1544"): "cast", ("Exo 14:3", "4788"): "has closed",
    ("Exo 16:34", "659"): "put", ("Deu 32:8", "1266"): "divided", ("Jos 4:23", "633.3"): "to dry up",
    ("Jos 5:1", "633.3"): "to dry up", ("2Sa 3:35", "4018.4"): "to eat", ("1Ki 18:23", "2007"): None,
    ("1Ki 18:25", "2007"): "put", ("2Ch 9:18", "5294"): "he placed", ("Job 3:4", "327"): "search",
    ("Job 3:6", "667"): "have carried", ("Job 36:19", "1578"): "turn", ("Psa 10:13", "3949"): "to anger",
    ("Jer 7:19", "3949"): "to anger,", ("Pro 4:11", "1688"): "I put", ("Isa 5:2", "4060"): "I put",
    ("Jer 12:15", "1544"): "casting", ("Lam 2:16", "1272"): "opened", ("Eze 32:18", "2601"): "shall bring",
    ("1Co 8:8", "3936"): "stand", ("1Ti 2:12", "2010"): "I commit", ("1Ti 3:4", "4291"): "standing",
    ("2Co 4:15", "4052"): "to abound", ("Act 5:19", "1806"): "leading", ("Act 9:8", "5496"): "leading",
    ("Act 19:6", "2007"): "having put", ("Luk 4:40", "2007"): "having placed", ("Luk 19:43", "4016"): "shall put",
    ("Mat 19:13", "2007"): "he should place", ("Rom 10:6", "2609"): "to lead", ("Heb 4:8", "2664"): "rest,",
    ("Job 23:15", "2686.5"): "seriously;",
    # rule 3: verb built on a noun / adjective -> that stem's piece
    ("Lev 14:48", "2511"): "cleansed", ("Deu 24:6", "1757.2"): "for security.", ("Jdg 20:35", "5159.1"): "to flight",
    ("1Sa 15:33", "815.1"): "childless", ("Job 22:7", "4222"): "to drink,", ("1Co 3:2", "4222"): "to drink,",
    ("Rev 14:8", "4222"): "to drink", ("Job 40:12", "4595"): "to rot", ("Psa 73:20", "1847"): "with contempt.",
    ("1Th 5:20", "1848"): "with contempt!", ("Luk 23:11", "1848"): "with contempt", ("Psa 79:7", "2049"): "desolate.",
    ("Isa 11:15", "2049"): "desolate", ("Eze 19:7", "1830.2"): "quite desolate;", ("Psa 105:22", "4679"): "wise.",
    ("Pro 26:10", "5492"): "by a storm", ("Isa 9:16", "3106"): "blessed", ("Isa 10:23", "4932"): "concise",
    ("1Co 8:13", "4624"): "to stumble.", ("Gal 5:2", "5623"): "benefit.", ("Luk 13:7", "2673"): "useless?",
    # rule 4: two pieces render one simple verb -> the joined English's head word
    ("Pro 7:21", "635"): "astray", ("2Pe 3:5", "2990"): "notice", ("Col 2:18", "2603"): "of due reward!",
}
# A word the detector caught only in part: its first piece is a helper the build peels out in front of
# the bracket and keeps tagged (helper_ok refuses it), the shape the detector skips by design.
# (verse, strongs) -> (live position, source English). Not in pairs.tsv, so not read on live: the
# before-value is the build's, and the guarded apply's check reads it first.
EXTRA = {("2Sa 3:35", "4018.4"): (5, "to cause")}
HELD = {("Exo 33:3", "3361"), ("Eze 28:3", "3756"), ("Eze 36:14", "3756")}
HELD_WHY = "held: the second piece is the English of the next, blank Greek word (splitter polarity B)"


def kind(eng):
    w = re.sub(r"[^\w\s]", " ", eng.lower()).split()
    if eng.strip() in CONNECTIVES or not w:
        return "P"
    return "S" if all(x in SCAFFOLD_WORDS for x in w) else "C"


def canon(ref):
    from audit_abp_app_vs_surface import BOOK_ORDER
    book, cv = ref.split(" ")
    ch, vs = cv.split(":")
    return BOOK_ORDER.index(book), int(ch), int(vs)


def base(st):
    return "G" + st.split(".")[0]


def words_from(classified):
    """Group the 'split' pairs into Greek words: (verse, source tag index) -> rows."""
    src = source_verses()
    with open(classified, encoding="utf-8", newline="") as f:
        pairs = [r for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE) if r["class"] == "split"]
    out = {}
    for r in pairs:
        v, p = r["verse"], int(r["position"])
        t = tokens(src[v])
        w = out.setdefault((v, t[p][2]), {"verse": v, "strongs": r["strongs"], "src": t[p][3], "rows": {}})
        w["rows"][p] = (r["english_1"], r["form_1"])
        w["rows"][p + 1] = (r["english_2"], r["form_2"])
    for w in out.values():
        x = EXTRA.get((w["verse"], w["strongs"]))
        if x:
            if x[0] in w["rows"] or x[0] != min(w["rows"]) - 1:
                raise SystemExit(f"EXTRA {w['verse']} @{x[0]} does not sit just before the word")
            w["rows"][x[0]] = (x[1], "")
            w["extra"] = x[0]
    return list(out.values()), len(pairs)


def pick(w):
    key = (w["verse"], w["strongs"])
    rows = sorted(w["rows"].items())
    if key in HELD:
        return None, "held"
    if key in HAND:
        want = HAND[key]
        hit = [p for p, (e, _) in rows if ("put" in e.split() if want is None else e == want)]
        if len(hit) != 1:
            raise SystemExit(f"hand pick {key} {want!r} matches {len(hit)} rows: {rows}")
        return hit[0], "hand"
    content = [p for p, (e, _) in rows if kind(e) == "C"]
    if len(content) == 1:
        return content[0], "auto"
    if not content:
        return rows[-1][0], "auto-last"
    raise SystemExit(f"no pick for {key}: {rows}")


def main():
    classified, out_path = sys.argv[1], sys.argv[2]
    words, npairs = words_from(classified)
    words.sort(key=lambda w: canon(w["verse"]) + (min(w["rows"]),))
    seen_hand = set()
    tally = Counter()
    lines = []
    for n, w in enumerate(words, 1):
        keep, how = pick(w)
        tally[how] += 1
        if how == "hand":
            seen_hand.add((w["verse"], w["strongs"]))
        rows = sorted(w["rows"].items())
        pieces = " | ".join(e for _, (e, _f) in rows)
        if keep is None:
            lines.append((w["verse"], n, "held", min(w["rows"]), "", "", f"{pieces} ({w['strongs']}); {HELD_WHY}"))
            continue
        ke, kf = w["rows"][keep]
        note = f"one Greek word, one source tag: {w['src']}; keeps the number: @{keep} '{ke}' ({how})"
        lines.append((w["verse"], n, "keeps", keep, w["strongs"], w["strongs"], note))
        moved = False
        for p, (e, f) in rows:
            if p == keep:
                continue
            tail = (" - NOT READ ON LIVE (a peeled helper the detector skips); before-value from the build;"
                    " any printed form here is unread too" if p == w.get("extra") else "")
            lines.append((w["verse"], n, "words.strongs", p, w["strongs"], "", f"'{e}'{tail}"))
            lines.append((w["verse"], n, "words.strongs_base", p, base(w["strongs"]), "", f"'{e}'{tail}"))
            if f:
                if not kf and not moved:
                    lines.append((w["verse"], n, "abp_surface.form", keep, "", f, f"the form moves to the kept row '{ke}'"))
                    moved = True
                    tally["form moved"] += 1
                else:
                    tally["form removed"] += 1
                lines.append((w["verse"], n, "abp_surface.form", p, f, "", f"'{e}' loses its form"))
        tally["rows losing the number"] += len(rows) - 1
    unused = set(HAND) - seen_hand
    if unused:
        raise SystemExit(f"hand picks not used: {sorted(unused)}")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("verse\tword\tcell\tposition\tbefore\tafter\tread\n")
        for x in lines:
            f.write("\t".join(str(c) for c in x) + "\n")
    print(f"split pairs {npairs} -> Greek words {len(words)}")
    for k in ("auto", "auto-last", "hand", "held", "rows losing the number", "form removed", "form moved"):
        print(f"  {k}: {tally[k]}")
    print(f"lines written: {len(lines)}")


if __name__ == "__main__":
    main()
