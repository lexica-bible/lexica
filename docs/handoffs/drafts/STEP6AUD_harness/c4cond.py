# STEP6AUD C4, DESIGN 9.202 conditions (1) + (3), run on the v2 account (c4rows.py v2 output). Read-only, local files.
# §9.202 conditions (1) + (3): read-only, local files.
# (1) for the 101 rows whose english goes to blank on built (the account's 100 "orphan ... -> None" + Joh 10:37 pos 2): every
#     STEP4-DELTA2 cell at that (verse, position), all columns; and whether the row is one of the moved pairs.
# (3) verses.text on built for those verses: STEP4-DELTA2 verses_cells (built value), else unchanged from src.
import ast, collections, hashlib, io, re
D = r"C:\Users\JP\edition_upgrade_runs\pa\step4_delta_20261115\delta"
ACC = r"C:\Users\JP\projects\bible-db\docs\handoffs\drafts\STEP6AUD_C4_account_20261119.txt"

acc = io.open(ACC, encoding="utf-8").read()
new = acc.split("# NEWLY CLEARED")[0]
blocks = re.split(r"\n(?=c4_phrase_built\.out:)", new)[1:]
rows = []   # (ref, orphan pos, host pos or None, gloss, dump line)
for b in blocks:
    m = re.match(r"c4_phrase_built\.out:(\d+)  (\S+ \d+:\d+)\s*\|.*?\| '(.*)'\s*\| orphan", b.split("\n")[0])
    gl = b.split("\n")[0].split("|")[3].strip()
    o = re.search(r"^      orphan\*? +pos (\d+) +english (.+?) -> (None|'')(  \(.*\))?$", b, re.M)   # v2 account: Joh 10:37 carries a note
    h = re.search(r"^      host +pos (\d+) ", b, re.M)
    if o:
        rows.append((m.group(2), int(o.group(1)), int(h.group(1)) if h else None, ast.literal_eval(gl), b.split("\n")[0]))
print("rows whose english goes to blank on built:", len(rows))

raw = io.open(D + r"\words_cells.tsv", encoding="utf-8", newline="").read().split("\n")
keep = [ln for ln in raw if not ln.startswith("Joh\t19\t18\t10\t")]
assert hashlib.sha256("\n".join(keep).encode()).hexdigest().startswith("86e44c58")
cells = collections.defaultdict(list)
for ln in keep[1:]:
    if ln:
        f = ln.split("\t"); cells[("%s %s:%s" % (f[0], f[1], f[2]), int(f[3]))].append((f[4], f[5], f[6], f[7]))
moved = set()
for ln in io.open(D + r"\words_moved.tsv", encoding="utf-8").read().split("\n")[1:]:
    if ln:
        f = ln.split("\t"); moved.add("%s %s:%s" % (f[0], f[1], f[2]))
print("words_moved sha:", hashlib.sha256(open(D + r"\words_moved.tsv", "rb").read()).hexdigest()[:8])

colcount = collections.Counter(); other = []
for ref, op, hp, gl, line in rows:
    cs = cells[(ref, op)]
    cols = tuple(sorted(c[0] for c in cs))
    colcount[cols] += 1
    for c in cs:
        if c[0] not in ("english", "english_head", "english_head_norm"):
            other.append((ref, op, c))
    if ref in moved:
        other.append((ref, op, ("verse is a moved-pair verse",)))
print("\n(1) column sets changed at the 101 rows:")
for k, v in colcount.most_common():
    print("  %3d  %s" % (v, k))
print("  columns other than english / english_head / english_head_norm:", other if other else "NONE")
# what english_head / english_head_norm become
eh = collections.Counter()
for ref, op, hp, gl, line in rows:
    for c in cells[(ref, op)]:
        if c[0] != "english":
            eh[(c[0], "src blank" if c[1] in ("None", "''") else "src filled", c[2])] += 1
print("  head cells:", dict(eh))

# (3) verses.text
vraw = io.open(D + r"\verses_cells.tsv", encoding="utf-8").read().split("\n")
print("\nverses_cells sha:", hashlib.sha256(open(D + r"\verses_cells.tsv", "rb").read()).hexdigest()[:8], "header:", vraw[0])
vt = {}
for ln in vraw[1:]:
    if ln:
        f = ln.split("\t"); vt["%s %s:%s" % (f[0], f[1], f[2])] = (ast.literal_eval(f[-2]), ast.literal_eval(f[-1])) if len(f) >= 5 else f

def norm(s):
    return " ".join(re.sub(r"[^\w\s']", " ", (s or "").replace("\u2014", " ")).lower().split())

stat = collections.Counter(); miss = []
for ref, op, hp, gl, line in rows:
    if ref not in vt:
        stat["verse text unchanged (not in verses_cells)"] += 1; miss.append((ref, gl, "unchanged")); continue
    a, b = vt[ref]
    if norm(gl) in norm(b):
        stat["built verses.text holds the phrase"] += 1
    else:
        stat["built verses.text does NOT hold the phrase as printed"] += 1; miss.append((ref, gl, b))
print("\n(3)", dict(stat))
for m in miss:
    print("   ", m)
