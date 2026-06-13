#!/usr/bin/env python3
"""
Build the chronological reading list the Library uses for "Chronological" order.

INPUT  (both in this folder):
  - source_oneyear.txt  : the passage sequence in event order, with "# ERA:" headers.
  - verse_counts.json   : per-chapter verse counts (facts only) for clean labels.
OUTPUT:
  - ../../static/chronological.json : { eras:[...], passages:[...] } the browser loads.

The passages are just pointers (book + verse range) into the reader's existing
ABP/KJV/BSB text — no Bible text is copied here. Run locally; it never touches
bible.db. Re-run after editing source_oneyear.txt:  python build_chronological.py
"""
import argparse
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source_oneyear.txt")
COUNTS = os.path.join(HERE, "verse_counts.json")
OUT = os.path.join(HERE, "..", "..", "static", "chronological.json")

EN_DASH = "–"

# Full book name (normalized: lowercased, spaces/dots stripped) -> the app's book code
# (the same codes the verses tables and 00-core.jsx use, e.g. Mark -> "Mar").
NAME_TO_CODE = {
    "genesis": "Gen", "exodus": "Exo", "leviticus": "Lev", "numbers": "Num",
    "deuteronomy": "Deu", "joshua": "Jos", "judges": "Jdg", "ruth": "Rth",
    "1samuel": "1Sa", "2samuel": "2Sa", "1kings": "1Ki", "2kings": "2Ki",
    "1chronicles": "1Ch", "2chronicles": "2Ch", "ezra": "Ezr", "nehemiah": "Neh",
    "esther": "Est", "job": "Job", "psalm": "Psa", "psalms": "Psa",
    "proverbs": "Pro", "ecclesiastes": "Ecc",
    "songofsolomon": "Son", "songofsongs": "Son", "song": "Son",
    "isaiah": "Isa", "jeremiah": "Jer", "lamentations": "Lam", "ezekiel": "Eze",
    "daniel": "Dan", "hosea": "Hos", "joel": "Joe", "amos": "Amo", "obadiah": "Oba",
    "jonah": "Jon", "micah": "Mic", "nahum": "Nah", "habakkuk": "Hab",
    "zephaniah": "Zep", "haggai": "Hag", "zechariah": "Zec", "malachi": "Mal",
    "matthew": "Mat", "mark": "Mar", "luke": "Luk", "john": "Joh", "acts": "Act",
    "romans": "Rom", "1corinthians": "1Co", "2corinthians": "2Co",
    "galatians": "Gal", "ephesians": "Eph", "philippians": "Php",
    "colossians": "Col", "1thessalonians": "1Th", "2thessalonians": "2Th",
    "1timothy": "1Ti", "2timothy": "2Ti", "titus": "Tit", "philemon": "Phm",
    "hebrews": "Heb", "james": "Jas", "1peter": "1Pe", "2peter": "2Pe",
    "1john": "1Jn", "2john": "2Jn", "3john": "3Jn", "jude": "Jud",
    "revelation": "Rev", "revelationofjohn": "Rev",
}

# App code -> the display name shown in labels (matches 00-core.jsx BOOK_LABELS).
CODE_TO_DISPLAY = {
    "Gen": "Genesis", "Exo": "Exodus", "Lev": "Leviticus", "Num": "Numbers",
    "Deu": "Deuteronomy", "Jos": "Joshua", "Jdg": "Judges", "Rth": "Ruth",
    "1Sa": "1 Samuel", "2Sa": "2 Samuel", "1Ki": "1 Kings", "2Ki": "2 Kings",
    "1Ch": "1 Chronicles", "2Ch": "2 Chronicles", "Ezr": "Ezra", "Neh": "Nehemiah",
    "Est": "Esther", "Job": "Job", "Psa": "Psalms", "Pro": "Proverbs",
    "Ecc": "Ecclesiastes", "Son": "Song of Solomon", "Isa": "Isaiah",
    "Jer": "Jeremiah", "Lam": "Lamentations", "Eze": "Ezekiel", "Dan": "Daniel",
    "Hos": "Hosea", "Joe": "Joel", "Amo": "Amos", "Oba": "Obadiah", "Jon": "Jonah",
    "Mic": "Micah", "Nah": "Nahum", "Hab": "Habakkuk", "Zep": "Zephaniah",
    "Hag": "Haggai", "Zec": "Zechariah", "Mal": "Malachi", "Mat": "Matthew",
    "Mar": "Mark", "Luk": "Luke", "Joh": "John", "Act": "Acts", "Rom": "Romans",
    "1Co": "1 Corinthians", "2Co": "2 Corinthians", "Gal": "Galatians",
    "Eph": "Ephesians", "Php": "Philippians", "Col": "Colossians",
    "1Th": "1 Thessalonians", "2Th": "2 Thessalonians", "1Ti": "1 Timothy",
    "2Ti": "2 Timothy", "Tit": "Titus", "Phm": "Philemon", "Heb": "Hebrews",
    "Jas": "James", "1Pe": "1 Peter", "2Pe": "2 Peter", "1Jn": "1 John",
    "2Jn": "2 John", "3Jn": "3 John", "Jud": "Jude", "Rev": "Revelation",
}


def norm(s):
    s = unicodedata.normalize("NFKD", s)
    return re.sub(r"[\s.]", "", s).lower()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def load_counts():
    """app code -> { chapter:int -> verse count:int }."""
    with open(COUNTS, encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for b in data:
        code = NAME_TO_CODE.get(norm(b["book"]))
        if not code:
            continue
        out[code] = {int(c["chapter"]): int(c["verses"]) for c in b["chapters"]}
    return out


_REF_RE = re.compile(r"^(.*?)\s+(\d+(?::\d+)?(?:\s*-\s*\d+(?::\d+)?)?)\s*$")


def parse_point(s):
    if ":" in s:
        c, v = s.split(":")
        return int(c), int(v)
    return int(s), None


def parse_passage(line, counts):
    m = _REF_RE.match(line)
    if not m:
        raise ValueError("can't parse passage: %r" % line)
    code = NAME_TO_CODE.get(norm(m.group(1)))
    if not code:
        raise ValueError("unknown book: %r" % line)
    cc = counts.get(code, {})
    ref = m.group(2).replace(" ", "")
    left, _, right = ref.partition("-")
    lc, lv = parse_point(left)
    start_c, start_v = lc, (lv if lv is not None else 1)

    if not right:                       # single point
        if lv is None:                  # whole chapter "C"
            end_c, end_v = lc, cc.get(lc)
        else:                           # single verse "C:V"
            end_c, end_v = lc, lv
    elif ":" in right:                  # "C:V"
        end_c, end_v = parse_point(right)
    elif lv is None:                    # whole-chapter range "C-D"
        end_c = int(right)
        end_v = cc.get(end_c)
        start_v = 1
    else:                               # same-chapter verse range "C:V-W"
        end_c, end_v = lc, int(right)

    return code, start_c, start_v, end_c, end_v


def make_label(code, sc, sv, ec, ev, counts):
    name = CODE_TO_DISPLAY.get(code, code)
    # A single whole psalm reads "Psalm 90" (singular); a span stays "Psalms 4–6".
    if code == "Psa" and sc == ec:
        name = "Psalm"
    end_count = counts.get(code, {}).get(ec)
    whole = (sv == 1 and end_count is not None and ev == end_count)
    if whole:
        return name + (f" {sc}" if sc == ec else f" {sc}{EN_DASH}{ec}")
    if sc == ec:
        return f"{name} {sc}:{sv}{EN_DASH}{ev}"
    return f"{name} {sc}:{sv}{EN_DASH}{ec}:{ev}"


TARGET_DAYS = 365


def passage_verses(code, sc, sv, ec, ev, counts):
    """How many verses a passage spans, from the per-chapter counts (facts only).
    Returns None if a chapter count is missing (so the caller can warn)."""
    cc = counts.get(code, {})
    if sc == ec:
        end = ev if ev is not None else cc.get(sc)
        return None if end is None else max(0, end - sv + 1)
    start_count = cc.get(sc)
    if start_count is None:
        return None
    total = start_count - sv + 1            # tail of the first chapter
    for c in range(sc + 1, ec):             # whole middle chapters
        cn = cc.get(c)
        if cn is None:
            return None
        total += cn
    end = ev if ev is not None else cc.get(ec)
    if end is None:
        return None
    return total + end                      # head of the last chapter


def balanced_split(passages, k):
    """Split an ordered passage list into k contiguous, non-empty groups so the verse
    totals are as even as possible — never splitting a passage. Returns [(start, end)]
    index pairs into `passages`.

    It minimises the total SQUARED distance of each day from the ideal share (a short
    DP over cut positions). Squaring punishes a stray day hard, so a giant atomic
    passage (e.g. Psalm 119, 176 verses) still takes its own big day — unavoidable —
    but the days around it stay near-ideal instead of one being left tiny."""
    n = len(passages)
    if k <= 1:
        return [(0, n)]
    if k >= n:
        return [(i, i + 1) for i in range(n)]   # one passage per day
    pre = [0] * (n + 1)
    for i, p in enumerate(passages):
        pre[i + 1] = pre[i] + (p["verses"] or 0)
    ideal = pre[n] / k
    INF = float("inf")

    def cost(i, j):                              # squared deviation of group [i, j)
        d = (pre[j] - pre[i]) - ideal
        return d * d

    dp = [[INF] * (n + 1) for _ in range(k + 1)]
    arg = [[0] * (n + 1) for _ in range(k + 1)]
    dp[0][0] = 0.0
    for g in range(1, k + 1):
        for i in range(g, n - (k - g) + 1):      # first i passages into g groups
            best, bp = INF, g - 1
            for p in range(g - 1, i):            # previous cut; last group is [p, i)
                if dp[g - 1][p] == INF:
                    continue
                c = dp[g - 1][p] + cost(p, i)
                if c < best:
                    best, bp = c, p
            dp[g][i], arg[g][i] = best, bp

    cuts, i = [n], n                             # walk the choices back
    for g in range(k, 0, -1):
        i = arg[g][i]
        cuts.append(i)
    cuts.reverse()
    return [(cuts[t], cuts[t + 1]) for t in range(k)]


def allocate_days(era_order, era_passages, target):
    """How many days each era gets: proportional to its verse length, at least 1 and
    never more than it has passages, then nudged to sum to exactly `target`. Splitting
    per-era means a day never straddles two eras — big sections stay whole."""
    ev = {e: sum((p["verses"] or 0) for p in era_passages[e]) for e in era_order}
    npass = {e: len(era_passages[e]) for e in era_order}
    total = sum(ev.values()) or 1
    days = {e: min(npass[e], max(1, round(target * ev[e] / total))) for e in era_order}

    def cur():
        return sum(days.values())
    guard = 0
    while cur() != target and guard < 100000:
        guard += 1
        if cur() < target:
            cand = [e for e in era_order if days[e] < npass[e]]
            if not cand:
                break
            e = max(cand, key=lambda e: ev[e] / days[e])   # most-loaded era gets relief
            days[e] += 1
        else:
            cand = [e for e in era_order if days[e] > 1]
            if not cand:
                break
            e = min(cand, key=lambda e: ev[e] / days[e])   # least-loaded gives one back
            days[e] -= 1
    return days, ev, npass


def build_day_plan(eras, passages, target):
    """Bin whole passages into `target` days and stamp `day` onto each passage.
    Returns a per-day summary list."""
    era_order = [e["id"] for e in eras]
    era_passages = {e: [] for e in era_order}
    for p in passages:
        era_passages[p["era"]].append(p)
    days_alloc, era_verses, _ = allocate_days(era_order, era_passages, target)

    summary, day_no = [], 0
    for e in era_order:
        ps = era_passages[e]
        for (s, en) in balanced_split(ps, days_alloc[e]):
            day_no += 1
            grp = ps[s:en]
            for p in grp:
                p["day"] = day_no
            summary.append({
                "day": day_no, "era": e,
                "verses": sum((p["verses"] or 0) for p in grp),
                "pos": [p["pos"] for p in grp],
                "label": " · ".join(p["label"] for p in grp),
            })
    return summary, days_alloc, era_verses


def main():
    try:                                    # so en-dashes print on a Windows console
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Build chronological.json + the day-by-day plan")
    ap.add_argument("--target", type=int, default=TARGET_DAYS, help="days in the plan (default 365)")
    ap.add_argument("--full", action="store_true", help="print every day to the screen too")
    args = ap.parse_args()

    counts = load_counts()
    eras, passages = [], []
    cur_era = None
    pos = 0
    warnings = []

    with open(SRC, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("# ERA:"):
                body = line[len("# ERA:"):].strip()
                name, _, blurb = body.partition("|")
                name, blurb = name.strip(), blurb.strip()
                cur_era = slug(name)
                eras.append({"id": cur_era, "name": name, "blurb": blurb})
                continue
            if line.startswith("#"):
                continue
            try:
                code, sc, sv, ec, ev = parse_passage(line, counts)
            except ValueError as e:
                warnings.append(str(e))
                continue
            pos += 1
            pv = passage_verses(code, sc, sv, ec, ev, counts)
            if pv is None:
                warnings.append("no verse count for: %r" % line)
            passages.append({
                "pos": pos, "era": cur_era, "book": code,
                "label": make_label(code, sc, sv, ec, ev, counts),
                "start_ch": sc, "start_v": sv, "end_ch": ec, "end_v": ev,
                "verses": pv if pv is not None else 0,
            })

    days, days_alloc, era_verses = build_day_plan(eras, passages, args.target)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"eras": eras, "passages": passages, "days": days}, f,
                  ensure_ascii=False, indent=0)

    total_v = sum((p["verses"] or 0) for p in passages)
    dv = sorted(d["verses"] for d in days)
    median = dv[len(dv) // 2] if dv else 0
    print(f"eras: {len(eras)}  passages: {len(passages)}  days: {len(days)}")
    print(f"verses: {total_v}   per day -> ideal {total_v / max(1, len(days)):.0f}  "
          f"min {dv[0] if dv else 0}  median {median}  max {dv[-1] if dv else 0}")
    print("days per era:")
    for e in eras:
        eid = e["id"]
        per = era_verses[eid] / max(1, days_alloc[eid])
        print(f"  {e['name']:<26} {days_alloc[eid]:>3} days  {era_verses[eid]:>5}v  ({per:.0f}/day)")

    longest = sorted(days, key=lambda d: -d["verses"])[:8]
    shortest = sorted(days, key=lambda d: d["verses"])[:8]
    print("longest days:")
    for d in longest:
        print(f"  Day {d['day']:>3}  {d['verses']:>4}v  {d['label']}")
    print("shortest days:")
    for d in shortest:
        print(f"  Day {d['day']:>3}  {d['verses']:>4}v  {d['label']}")

    preview = os.path.join(HERE, "day_plan_preview.txt")
    with open(preview, "w", encoding="utf-8") as f:
        for d in days:
            f.write(f"Day {d['day']:>3}  [{d['era']}]  {d['verses']:>4}v  {d['label']}\n")

    if args.full:
        for d in days:
            print(f"Day {d['day']:>3}  {d['verses']:>4}v  {d['label']}")

    print(f"wrote {os.path.relpath(OUT, HERE)} + day_plan_preview.txt")
    for w in warnings:
        print("  WARN:", w)
    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())
