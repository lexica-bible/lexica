#!/usr/bin/env python3
"""eu_rekey_dump.py - READ-ONLY dump of the built word rows for the re-key verses (DESIGN_q2_build
§9.65 R1, §9.66 R2, §9.67 R3), so the re-keys are written against what the build really makes.

Re-runs derivation A as a dry run on the PA copy (merge pairs + edge splits included) and, for
the 23 re-key verses, writes one line per word: the built row as the tail patches see it
(fix_subject_reorder / fix_supplied_attach / fix_split_merges run before any english rewrite),
the same row after the real fix_bracket_punct + fix_emdash passes on a throwaway db (what the
lane-3 repairs see at 8b.2a), and the old build's row. Also writes each verse's feed cells.
Never writes the copy or live.

    python3 scripts/eu_rekey_dump.py      -> ~/edition_upgrade_runs/eu_rekey_20261102/
"""
import contextlib, io, os, sqlite3, subprocess, sys
from pathlib import Path
LOCAL = os.environ.get("PREA_LOCAL") == "1"
H = os.path.expanduser("~")
REPO = os.environ.get("PREA_REPO", H + "/bible-db")
COPY = REPO + "/bible_edupg_test_20261101.db"
RUNS = os.environ.get("PREA_RUNS", H + "/edition_upgrade_runs")
OUT = Path(RUNS) / "eu_rekey_20261102"
sys.path.insert(0, REPO + "/scripts")
os.chdir(REPO)
import build_words_from_abp as W

R1 = ["Isa 28:20", "Mar 14:44"]
R2 = ["Gen 28:22", "Gen 31:49", "Exo 4:23", "Jos 2:4", "Neh 5:12", "Job 8:10", "Isa 56:10", "Act 7:3",
      "Jas 4:2", "Joh 4:22", "Joh 11:42", "Joh 13:8", "Joh 19:15", "Mat 24:44", "Mat 28:10", "Php 3:15",
      "Rom 3:4", "Rom 9:29", "Eze 20:14"]
R3 = ["Isa 30:31", "Jer 50:16"]
def key(s):
    b, cv = s.rsplit(" ", 1); c, v = cv.split(":"); return (b, int(c), int(v))
LANE = {key(v): "R1" for v in R1} | {key(v): "R2" for v in R2} | {key(v): "R3" for v in R3}

REC, APP = {}, {}
orig = W.AppTransplant.apply
def wrapped(self, k, raw_words, corrs, old_rows, *a, **kw):
    out = orig(self, k, raw_words, corrs, old_rows, *a, **kw)
    APP["app"] = self
    if k in LANE:
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

COLS = ("position", "english", "english_head", "strongs", "strongs_base", "greek_pos", "bracket_id",
        "italic", "italic_words", "smcap_words", "morph", "lemma")
p = OUT / "tail_rekey.db"
if p.exists():
    p.unlink()
con = sqlite3.connect(p)
con.execute("CREATE TABLE verses (id INTEGER PRIMARY KEY, book TEXT, chapter INT, verse INT, text TEXT)")
con.execute("CREATE TABLE words (id INTEGER PRIMARY KEY, verse_id INT, " + ", ".join(COLS) + ")")
vid = {}
for i, (k, (_old, new, _v)) in enumerate(sorted(REC.items()), 1):
    vid[k] = i
    con.execute("INSERT INTO verses VALUES (?,?,?,?,?)", (i, k[0], k[1], k[2], ""))
    for r in new:
        con.execute("INSERT INTO words (verse_id, " + ", ".join(COLS) + ") VALUES (?" + ",?" * len(COLS) + ")", (i, *r))
con.commit(); con.close()
for cmd in (["scripts/fix_bracket_punct.py", str(p)], ["scripts/fix_emdash.py", str(p), "--apply"]):
    r = subprocess.run([sys.executable] + cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        sys.exit(f"STOP: {cmd[0]} failed on the throwaway db: {r.stderr[-300:]}")
con = sqlite3.connect(p)
post = {(v, pos): (e, h) for v, pos, e, h in con.execute("SELECT verse_id, position, english, english_head FROM words")}
con.close()

def s(x): return "" if x is None else str(x)
with open(OUT / "rekey_rows.tsv", "w", encoding="utf-8", newline="\n") as f:
    f.write("lane\tverse\teligible\tposition\tstrongs_base\tgreek_pos\tbracket_id\tbuilt_english\tbuilt_head\t"
            "post_tail_english\tpost_tail_head\told_english\told_head\told_greek_pos\told_bracket_id\n")
    for k in sorted(REC, key=lambda k: (LANE[k], k)):
        old, new, verdict = REC[k]
        for o, n in zip(old, new):
            pe, ph = post[(vid[k], n[0])]
            f.write("\t".join(s(x) for x in (LANE[k], f"{k[0]} {k[1]}:{k[2]}", verdict == "", n[0], n[4], n[5], n[6],
                                             n[1], n[2], pe, ph, o[1], o[2], o[5], o[6])) + "\n")
with open(OUT / "rekey_feed.tsv", "w", encoding="utf-8", newline="\n") as f:
    f.write("lane\tverse\tslot\tstrongs\tgreek\tfeed_english\n")
    for k in sorted(REC, key=lambda k: (LANE[k], k)):
        ka = app.pairs[k]
        for sl in app.feed[ka]:
            f.write("\t".join((LANE[k], f"{k[0]} {k[1]}:{k[2]}", str(sl["slot_index"]), sl["strongs"], sl["greek"],
                               app.norm[(ka[0], ka[1], ka[2], sl["slot_index"])])) + "\n")
print("\n".join(summary))
missing = sorted(set(LANE) - set(REC))
noteli = [f"{k[0]} {k[1]}:{k[2]}" for k, (_o, _n, v) in REC.items() if v != ""]
print(f"\n==== re-key dump: {len(REC)} of {len(LANE)} verses (R1 {len(R1)}, R2 {len(R2)}, R3 {len(R3)}) ====")
print(f"  not seen: {missing}  not eligible: {noteli}")
print(f"  -> {OUT / 'rekey_rows.tsv'}  {OUT / 'rekey_feed.tsv'}")
