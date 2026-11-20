# P2 (2): parse the 9 freshly fetched app pages with the repo's OWN parser (the one that made the
# feed: reparse_abp_app_italic.parse_cached_page -> fetch_abp_app.ChapterParser, title check
# included) and compare the 10 verses to the frozen feed, every slot, all 9 columns.
import csv
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
REPO = r"C:\Users\JP\projects\bible-db"
sys.path.insert(0, os.path.join(REPO, "scripts"))
import reparse_abp_app_italic as R  # noqa: E402

PAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fresh_pages")
FEED = os.path.join(REPO, "abp_app_html", "abp_app_slots_italic.tsv")
TEN = [("2 Kings", 23, 35), ("Esther", 5, 9), ("Ezekiel", 20, 14), ("Genesis", 5, 25), ("Genesis", 5, 26),
       ("Genesis", 34, 4), ("Judges", 11, 7), ("Joshua", 2, 4), ("Joshua", 5, 15), ("Romans", 9, 29)]
COLS = ["book", "chapter", "verse", "slot_index", "strongs", "greek", "english", "italic", "italic_words"]

h = hashlib.sha256(open(FEED, "rb").read()).hexdigest()
print("feed sha256 %s (pin 7bd77385a80de3c3a762b9427658dfec4163d4882f5a3ea56be10ff61436cf63): %s"
      % (h, "OK" if h == "7bd77385a80de3c3a762b9427658dfec4163d4882f5a3ea56be10ff61436cf63" else "MISMATCH - STOP"))
if not h.startswith("7bd77385"):
    sys.exit(1)

feed = {}
for r in csv.DictReader(open(FEED, encoding="utf-8", newline=""), delimiter="\t"):
    k = (r["book"], int(r["chapter"]), int(r["verse"]))
    if k in TEN:
        feed.setdefault(k, []).append(tuple(r[c] for c in COLS))

fresh = {}
for book, ch in sorted({(b, c) for b, c, _v in TEN}):
    path = os.path.join(PAGES, "%s %d.html" % (book, ch))
    body = open(path, "rb").read()
    print("page %-12s %7d B sha256 %s title %r" % ("%s %d" % (book, ch), len(body), hashlib.sha256(body).hexdigest(),
                                                  R.page_title(body)))
    rows, anomalies = R.parse_cached_page(book, ch, path)     # STOPs on a title mismatch
    if anomalies:
        print("  parser anomalies: %r" % anomalies)
    for row in rows:
        k = (row[0], row[1], row[2])
        if k in TEN:
            fresh.setdefault(k, []).append(tuple(str(x) for x in row))

CONTROL = "--control" in sys.argv
if CONTROL:   # plant one known difference: Genesis 5:25 slot 1 English "Mathusala lived" -> "lived Mathusala"
    k = ("Genesis", 5, 25)
    r = list(fresh[k][1])
    r[6] = "lived Mathusala"
    fresh[k][1] = tuple(r)
    print("CONTROL: planted Genesis 5:25 slot 1 english -> 'lived Mathusala'; expect exactly that verse NO")
alls = True
for k in TEN:
    f, n = feed.get(k, []), fresh.get(k, [])
    diffs = []
    for i in range(max(len(f), len(n))):
        a = f[i] if i < len(f) else None
        b = n[i] if i < len(n) else None
        if a != b:
            diffs.append((i, a, b))
    same = not diffs
    alls = alls and same
    print("%-12s feed slots %2d - fresh slots %2d - identical (all 9 columns, every slot): %s"
          % ("%s %d:%d" % k, len(f), len(n), "YES" if same else "NO"))
    for i, a, b in diffs:
        print("    slot %d  feed  %r\n            fresh %r" % (i, a, b))
print("ALL 10 fresh = feed: %s" % ("YES" if alls else "NO"))
