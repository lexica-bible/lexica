# Trace P4's abp_corrections delta (src -> live) against the frozen active-member files. Local, read-only.
import ast, csv, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
csv.field_size_limit(10**9)
D = r"C:\Users\JP\edition_upgrade_runs\pa\delta_live_vs_src.tsv"
F = r"C:\Users\JP\projects\bible-db\tests\fixtures\corrections"
def load(p):
    return [tuple(l.rstrip("\n").split("\t")) for l in open(p, encoding="utf-8") if l.strip()]
live_act = set(load(F + r"\abp_corrections_active_live_20261031.txt"))
built_act = set(load(F + r"\abp_corrections_active_built_20261106.txt"))
print("member files: live active %d, built/src active %d; both %d, live only %d, built only %d"
      % (len(live_act), len(built_act), len(live_act & built_act), len(live_act - built_act), len(built_act - live_act)))
COLS = None
removed, changed = [], []
for r in csv.reader(open(D, encoding="utf-8", newline=""), delimiter="\t"):
    if r[0] != "abp_corrections":
        continue
    kind, key, cols, before, after = r[1], r[2], r[3], r[4], r[5]
    if kind == "REMOVED":
        rows = ast.literal_eval(before)
        assert len(rows) == 1, rows
        removed.append(rows[0])
    elif kind == "CHANGED":
        changed.append((ast.literal_eval(key)[0], cols, ast.literal_eval(before), ast.literal_eval(after)))
print("delta: REMOVED %d, CHANGED %d" % (len(removed), len(changed)))
# REMOVED row layout = the table's columns + _n (eu_step table_delta: sel = columns; by_id adds 1 AS _n)
# columns per build_abp_corrections.py :49-62: id, book, chapter, verse, position, field, source_value, corrected_value, reason,
# ledger_ref, applied_at, status, created
lens = Counter(len(x) for x in removed); print("REMOVED row lengths: %s (expect 14 = 13 columns + _n)" % dict(lens))
rk = Counter()
keys = set()
for x in removed:
    _id, book, ch, v, pos, field, _sv, _cv, _rs, led, _ap, status, _cr, _n = x
    rk[status] += 1
    keys.add((book, str(ch), str(v), str(pos), field, led or ""))
print("REMOVED by status on src: %s" % dict(rk))
bo = built_act - live_act
print("REMOVED keys (book, ch, v, pos, field, ledger_ref) = the 346 built-active-only member lines: %s (removed %d, members %d, in both %d)"
      % ("yes" if keys == bo else "NO", len(keys), len(bo), len(keys & bo)))
if keys != bo:
    for k in sorted(keys - bo)[:20]: print("  removed, not a built-only member:", k)
    for k in sorted(bo - keys)[:20]: print("  built-only member, not removed:", k)
ch = Counter((c, repr(b), repr(a)) for _i, c, b, a in changed)
print("CHANGED (src -> live): %s" % ", ".join("%s %s -> %s: %d" % (c, b, a, n) for (c, b, a), n in sorted(ch.items())))
print("CHANGED ids: %s" % ",".join(str(i) for i, *_ in sorted(changed)))
