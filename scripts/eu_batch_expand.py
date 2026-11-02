#!/usr/bin/env python3
"""eu_batch_expand.py - READ-ONLY expansion of the edition-upgrade corrections batch (DESIGN 9.68/9.72/
9.74/9.76). Re-runs derivation A as a dry run on the PA copy, takes the built rows of the batch verses,
runs the real fix_bracket_punct + fix_emdash on a throwaway db of just those rows (the two tail steps
that rewrite english before the step-7 corrections), and writes the proposed correction rows - word,
headword, and one verse-text row per verse (built with B's own clean_counted, as B writes it, before
the em-dash swap) - to ~/edition_upgrade_runs/eu_batch_20261102/eu_batch_rows.tsv. Never writes the
copy or live. Spec: tests/fixtures/edition_upgrade/eu_corrections_spec_20261102.tsv.

    python3 scripts/eu_batch_expand.py
"""
import ast, collections, contextlib, csv, io, json, os, sqlite3, subprocess, sys
from pathlib import Path
LOCAL = os.environ.get("PREA_LOCAL") == "1"
H = os.path.expanduser("~")
REPO = os.environ.get("PREA_REPO", H + "/bible-db")
COPY = REPO + "/bible_edupg_test_20261101.db"
RUNS = os.environ.get("PREA_RUNS", H + "/edition_upgrade_runs")
OUT = Path(RUNS) / "eu_batch_20261102"
SPEC = Path(REPO) / "tests/fixtures/edition_upgrade/eu_corrections_spec_20261102.tsv"
sys.path.insert(0, REPO + "/scripts")
os.chdir(REPO)
import build_words_from_abp as W
import build_prose_from_app as BP
import load_abp_prose as P

def key(s):
    b, cv = s.rsplit(" ", 1); c, v = cv.split(":"); return (b, int(c), int(v))
spec = list(csv.DictReader(open(SPEC, encoding="utf-8", newline=""), delimiter="\t", quoting=csv.QUOTE_NONE))
TARGET = {key(r["verse"]) for r in spec}
REC, APP = {}, {}
orig = W.AppTransplant.apply
def wrapped(self, k, raw_words, corrs, old_rows, *a, **kw):
    out = orig(self, k, raw_words, corrs, old_rows, *a, **kw)
    APP["app"] = self
    if k in TARGET:
        REC[k] = ([W._prefix_base(r) for r in old_rows], [W._prefix_base(r) for r in out], self.verdict.get(k))
    return out
W.AppTransplant.apply = wrapped
OUT.mkdir(parents=True, exist_ok=True)
sys.argv = ["build_words_from_abp.py", "bible.db", "bh_scrape.db", "--out", str(OUT / "a")] + (
    ["--dry-run-nodb"] if LOCAL else ["--dry-run", COPY])
with contextlib.redirect_stdout(io.StringIO()) as quiet:
    W.main()
summary = [ln for ln in quiet.getvalue().splitlines() if "transplanted" in ln or "merge_pairs" in ln
           or "edge_splits" in ln or "list: MATCHES" in ln or "DIFFERS" in ln or "SKIPPED" in ln]
app = APP["app"]

# verse ids + current prose on the copy (read-only)
if LOCAL:
    vid = {k: i + 1 for i, k in enumerate(sorted(TARGET))}
    src = W.abp_source_texts()
    with contextlib.redirect_stderr(io.StringIO()):
        prev = {k: BP.emdash(P.clean_verse(src[k], ref=str(k))) for k in TARGET}
else:
    con = sqlite3.connect(f"file:{COPY}?mode=ro", uri=True)
    vid, prev = {}, {}
    for i, b, c, v, t in con.execute("SELECT id, book, chapter, verse, text FROM verses"):
        if (b, c, v) in TARGET:
            vid[(b, c, v)], prev[(b, c, v)] = i, t
    con.close()

# the two tail steps that rewrite english before the step-7 corrections, RUN for real on a throwaway db
COLS = ("position", "english", "english_head", "strongs", "strongs_base", "greek_pos", "bracket_id",
        "italic", "italic_words", "smcap_words", "morph", "lemma")
def tail(which):
    p = OUT / f"tail_{which}.db"
    if p.exists():
        p.unlink()
    con = sqlite3.connect(p)
    con.execute("CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT)")
    con.execute("CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, " + ", ".join(COLS) + ")")
    for k, (old, new, _v) in REC.items():
        con.execute("INSERT INTO verses VALUES (?,?,?,?,?)", (vid[k], k[0], k[1], k[2], ""))
        for r in (old if which == "old" else new):
            con.execute("INSERT INTO words (verse_id, " + ", ".join(COLS) + ") VALUES (?" + ",?" * len(COLS) + ")",
                        (vid[k], *r))
    con.commit(); con.close()
    for cmd in (["scripts/fix_bracket_punct.py", str(p)], ["scripts/fix_emdash.py", str(p), "--apply"]):
        r = subprocess.run([sys.executable] + cmd, capture_output=True, text=True, encoding="utf-8")
        if r.returncode:
            sys.exit(f"STOP: {cmd[0]} failed on the throwaway db: {r.stderr[-300:]}")
    con = sqlite3.connect(p)
    got = {}
    for v_id, pos, eng, head, sb, bid in con.execute(
            "SELECT verse_id, position, english, english_head, strongs_base, bracket_id FROM words"):
        got[(v_id, pos)] = (eng, head, sb, bid)
    con.close()
    return got
POST_NEW, POST_OLD = tail("built"), tail("old")

# verses the other tail patches / lane-3 / re-keys touch (flag only)
S = Path(REPO) / "scripts"
def literal(fname, name):
    for n in ast.parse((S / fname).read_text(encoding="utf-8")).body:
        if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == name for t in n.targets):
            return ast.literal_eval(n.value)
PATCHED = collections.defaultdict(set)
for f in literal("fix_subject_reorder.py", "FIXES"): PATCHED[(f[1], f[2], f[3])].add("subject_reorder")
for f in literal("fix_supplied_attach.py", "FIXES"): PATCHED[(f[0], f[1], f[2])].add("supplied_attach")
for f in literal("fix_merge_misses.py", "MISSES"): PATCHED[(f[0], f[1], f[2])].add("merge_misses")
for v in json.loads((S / "split_merge_fixes.json").read_text(encoding="utf-8")): PATCHED[key(v)].add("split_merges")
for fn in ("lane3_star_fixes.json", "lane3_star_gapfix.json", "lane3_star_fixes2.json"):
    d = json.loads((S / fn).read_text(encoding="utf-8")); d.pop("_comment", None)
    for v in d: PATCHED[key(v)].add("lane3")
for v in (("Mat", 25, 37),): PATCHED[v].add("mat25_37")
for v in (("Lam", 3, 16), ("1Pe", 1, 23)): PATCHED[v].add("theos_filler")
for v in (("Dan", 4, 19),): PATCHED[v].add("kyrios")

rows_out, problems, flags = [], [], collections.Counter()
def ref(k): return f"{k[0]} {k[1]}:{k[2]}"
def ledger(k): return f"EU-{k[0]}{k[1]}:{k[2]}"
by_verse = collections.defaultdict(list)
for it in spec:
    by_verse[key(it["verse"])].append(it)
for k, items in by_verse.items():
    if k not in REC:
        problems.append(f"{ref(k)}: not seen in the dry run"); continue
    old, new, verdict = REC[k]
    if verdict != "":
        problems.append(f"{ref(k)}: not eligible ({verdict}) - the build keeps the old rows"); continue
    vflag = ",".join(sorted(PATCHED.get(k, ())))
    # --- word rows
    seen = collections.Counter()
    for it in items:
        hits = [r for r in new if it["row_find"] and it["row_find"] in (POST_NEW[(vid[k], r[0])][0] or "")]
        if len(hits) > 1:
            exact = [r for r in hits if (POST_NEW[(vid[k], r[0])][0] or "").strip() == it["row_find"]]
            if not exact:
                exact = [r for r in hits if (POST_NEW[(vid[k], r[0])][0] or "").strip(" ,.;:!?") == it["row_find"]]
            same = [i for i in items if i["row_find"] == it["row_find"]]
            if len(exact) == 1 and len(same) == 1:
                hits = exact                         # Jos 19:47: the other row already read so
            elif len(same) == len(hits):
                hits = [hits[seen[it["row_find"]]]]  # Son 8:7: two fixes, two rows, in order
            seen[it["row_find"]] += 1
        if len(hits) != 1:
            problems.append(f"{ref(k)} [{it['group']}] {it['row_find']!r}: {len(hits)} built row(s) - "
                            f"{[POST_NEW[(vid[k], r[0])][0] for r in hits]}"); continue
        pos = hits[0][0]
        s_eng, s_head, sb, bid = POST_NEW[(vid[k], pos)]
        if it["row_repl"] == "<OLD>":
            o_eng, o_head, o_sb, _ob = POST_OLD[(vid[k], pos)]
            if o_sb != sb:
                problems.append(f"{ref(k)} pos {pos}: old row Strong's {o_sb} != built {sb}"); continue
            c_eng, c_head = o_eng, o_head
        else:
            c_eng = s_eng.replace(it["row_find"], it["row_repl"], 1)
            derived = s_head is not None and s_head == W._head_word(s_eng)
            c_head = W._head_word(c_eng) if derived else s_head
            if not derived and s_head and it["row_find"].lower() in s_head.lower():
                problems.append(f"{ref(k)} pos {pos}: head {s_head!r} carries the fixed word but is not "
                                f"derived from the text - rule it by hand"); continue
        if c_eng == s_eng:
            problems.append(f"{ref(k)} pos {pos}: correction would not change {s_eng!r}"); continue
        f = ",".join(x for x in (vflag, "bracketed" if bid is not None else "", "name-row" if sb == "*" else "",
                                  "dash-swapped" if "—" in (s_eng or "") else "", it["group"] if "DIFFERS" in it["group"] else "") if x)
        rows_out.append((k[0], k[1], k[2], pos, "english", s_eng, c_eng, ledger(k), it["group"], f))
        if c_head != s_head:
            rows_out.append((k[0], k[1], k[2], pos, "english_head", s_head, c_head, ledger(k), it["group"], f))
        for x in f.split(","):
            if x: flags[x] += 1
    # --- one verse-text row per verse (B's own function, before the em-dash swap, as B writes it)
    ka = app.pairs[k]
    texts = {s["slot_index"]: app.norm[(ka[0], ka[1], ka[2], s["slot_index"])] for s in app.feed[ka]}
    fixed = dict(texts)
    ok = True
    for it in items:
        si = int(it["slot"])
        if texts.get(si) != it["slot_text"]:
            problems.append(f"{ref(k)} slot {si}: feed text {texts.get(si)!r} != spec {it['slot_text']!r}"); ok = False
        fixed[si] = it["slot_new"]
    if not ok:
        continue
    joined = " ".join(texts[s["slot_index"]] for s in app.feed[ka])
    joined_fixed = " ".join(fixed[s["slot_index"]] for s in app.feed[ka])
    with contextlib.redirect_stderr(io.StringIO()):
        b_new = BP.clean_counted(joined, ref(k), collections.Counter())
        b_fixed = BP.clean_counted(joined_fixed, ref(k), collections.Counter())
    if BP.emdash(b_new) == (prev.get(k) or ""):
        problems.append(f"{ref(k)}: B leaves this verse's text unchanged - no verse-text row"); continue
    if b_fixed == b_new:
        problems.append(f"{ref(k)}: the fix does not change B's verse text"); continue
    rows_out.append((k[0], k[1], k[2], -1, "verses.text", b_new, b_fixed, ledger(k), "+".join(sorted({i["group"] for i in items})), vflag))

with open(OUT / "eu_batch_rows.tsv", "w", encoding="utf-8", newline="\n") as fh:
    fh.write("book\tchapter\tverse\tposition\tfield\tsource_value\tcorrected_value\tledger_ref\tgroup\tflags\n")
    for r in rows_out:
        fh.write("\t".join("" if x is None else str(x) for x in r) + "\n")
print("\n".join(summary))
print(f"\n==== corrections batch, expanded (spec {len(spec)} cells in {len(by_verse)} verses) ====")
c = collections.Counter(r[4] for r in rows_out)
print(f"  rows: english {c['english']} + english_head {c['english_head']} + verses.text {c['verses.text']} = {len(rows_out)}")
print(f"  flags: {dict(flags)}")
print(f"  PROBLEMS: {len(problems)}")
for p in problems:
    print("    " + p)
print(f"  -> {OUT / 'eu_batch_rows.tsv'}")
