#!/usr/bin/env python3
"""
stress_lexica_rare.py — STEP 2/3 of the rare-word stress test: build the lexica_def engine over a
set of RARE words and read the two manufacturing detectors, so we can find the frequency cutoff.

THE QUESTION. The verse-grounded dictionary is human-reviewed at common-to-mid frequency. Before
building it out top-down by frequency, we need to know: does the engine stay HONEST when STARVED?
On a word with 1-3 total occurrences, does it stay honestly short, or does it MANUFACTURE senses to
fill the dictionary template? Manufactured senses are freight sourced from thinness instead of
tradition — the same failure, one layer down.

WHAT IT DOES. For each target word it runs the SAME production pipeline as build_lexica_def
(select_spread -> the FROZEN VERSE_PROMPT engine -> splitter -> citation gate -> fork append) by
calling build_lexica_def's own helpers verbatim, N times per word (default 3 — one build is a draw,
and manufacturing flickers run to run). It reads three detectors off each draw:

  (a) CITATION REAL-MISS  — entry.audit.real. A manufactured sense reaches for a verse that does
      not contain the lemma, so the citation gate's REAL bucket climbs. (tagging / no-verse buckets
      are DATA gaps, not hallucination — reported separately, not counted as manufacturing.)
  (b) ENGINE SELF-FLAG    — entry.coverage (the prompt emits it ONLY when "the supplied occurrences
      are too few or too clustered"), plus any thin-evidence language in gloss_notes. The engine
      flagging its own thinness is the honest signal (it did this on cheir: "sense 4 rests on a
      single occurrence ... sparse").
  (c) SENSES > OCCURRENCES — a structural padding flag needing no judgment: a word with k
      occurrences can ground at most k distinct senses (each needs a verse). A draw with more senses
      than the word has occurrences has at least one sense with nothing behind it = manufactured.

Plus, per word, the SENSE-COUNT SPREAD across the draws (e.g. {1:2, 2:1}) vs the occurrence count —
the padding tell, reported as the spread (NOT an average; the count lies when averaged).

SAFETY / SCOPE.
  * PA-ONLY (bible.db + the model key live there).
  * READ-ONLY on bible.db: opens it ?mode=ro, so it CANNOT write lexica_def or words/verses. These
    are TEST builds — they must never serve to users. Nothing is written to any database.
  * The frozen engine is UNTOUCHED: it calls build_lexica_def.model_prose / .assemble directly, so
    VERSE_PROMPT and the whole pipeline are byte-identical to production. It prints the prompt stamp
    so you can see it is the live frozen prompt.
  * Every draw (full card + detectors) is dumped to a scratch folder OUTSIDE the repo (~/lexica_stress
    by default) as JSON + readable .txt, so you can read every card by eye and re-read free later.

  workon bible-env
  export ANTHROPIC_API_KEY=$(grep -oE "sk-ant-[A-Za-z0-9_-]+" /var/www/www_lexica_bible_wsgi.py)
  python scripts/stress_lexica_rare.py                 # the 18-word approved set, 3 draws each (~$1.60)
  python scripts/stress_lexica_rare.py --word G898     # one word
  python scripts/stress_lexica_rare.py --runs 5        # more draws per word
"""

import argparse, datetime, json, os, re, sqlite3, sys
from collections import Counter

# reuse the FROZEN, proven engine + helpers verbatim — same import trick as lexica_agreement.py,
# so a "sense", the evidence, the splitter, and the citation gate are EXACTLY the card's.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_lexica_def as B

# ── the approved test set (Step 1). Spread across the thin end; labels are for the report only —
# the real lemma/translit come from the lexicon at run time (lex_head). CONTROLS read FIRST. ──────
TARGETS = [
    # occ = 1  (starved, single-sense — any 2nd sense is manufactured)
    "G74", "G54", "G250", "G201", "G238",
    # occ = 2
    "G898", "G699", "G88", "G431", "G1379",
    # occ = 3
    "G3201", "G2594", "G3713", "G1240",
    # occ = 5
    "G2299", "G1167", "G4267", "G1142",
]
CONTROLS = {"G898": "genuine 2-sense control", "G2299": "homograph control"}
ROLE = {
    "G74": "starved 1-sense", "G54": "starved 1-sense", "G250": "starved concrete",
    "G201": "starved concrete", "G238": "starved 1-sense verb",
    "G898": "GENUINE 2 senses (control)", "G699": "2 words / 1 job", "G88": "inflection fold",
    "G431": "concrete fold", "G1379": "inflection fold",
    "G3201": "clean verb", "G2594": "clean verb", "G3713": "literal/figurative tempter",
    "G1240": "concrete noun",
    "G2299": "HOMOGRAPH trap (control)", "G1167": "flavor-split tempter",
    "G4267": "doctrinal-freight tempter", "G1142": "clean control",
}

# thin-evidence language in a gloss note (coverage being non-empty is itself the flag, by prompt
# design; this catches a thinness admission that lands in gloss_notes instead).
THIN_RE = re.compile(
    r"\b(single occurrence|one occurrence|sole occurrence|only (one|two|a single|this|these|in)|"
    r"too few|too clustered|few occurrences|sparse|limited evidence|insufficient|"
    r"cannot (characteri[sz]e|determine)|one (verse|context)|a single (verse|use|context))\b", re.I)


def gather_evidence(conn, sid, budget, has_surface):
    """The SAME deterministic evidence production sees (verbatim from build_lexica_def.main)."""
    pred, params = B.abp_filter(conn, sid)
    gset = B.gloss_set(conn, pred, params)
    occs = B.occurrences(conn, pred, params)
    sample = B.select_spread(occs, budget)
    ctx = B.fetch_context(conn, sample, has_surface)
    lemma, translit = B.lex_head(conn, sid)
    ot = sum(1 for c in ctx if c[0] not in B.NT_BOOKS)
    return {"lemma": lemma, "translit": translit, "gset": gset, "ctx": ctx,
            "occ": len(occs), "fed": len(ctx), "ot": ot, "renderings": len(gset)}


# Count senses TOLERANTLY. A sense header is a line that starts with an optional bold marker then
# "N." or "N)". The LIVE engine splitter (build_lexica_def._HEADLINE_RE) only recognizes BOLD
# "**N.**", so when a draw numbers its senses plainly (no bold) sense_headlines comes back EMPTY —
# which is why the first summary read bathmos/thea as 0 senses. We count the real headers here for
# the STRESS measurement; we do NOT touch the frozen engine. (The bold-vs-plain mismatch is itself a
# finding: in production a plain-numbered draw fails validate_entry and the word would be refused.)
_SENSE_HDR = re.compile(r'(?m)^[ \t]*(?:\*{1,2}\s*)?(\d+)[.)]\s+')


def parse_senses(senses_block):
    """Split the Senses prose into [{headline, refs}] at every numbered header (bold OR plain). The
    refs are pulled from each sense's own chunk so grounding can be checked per sense."""
    block = senses_block or ""
    marks = list(_SENSE_HDR.finditer(block))
    out = []
    for i, m in enumerate(marks):
        start = m.start()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(block)
        chunk = block[start:end]
        first = next((ln for ln in chunk.splitlines() if ln.strip()), "")
        headline = re.sub(r'^[ \t]*(?:\*{1,2}\s*)?\d+[.)]\s*', '', first)
        headline = re.sub(r'\*+', '', headline).strip()
        out.append({"headline": headline, "refs": B.cited_refs(chunk)})
    return out


def analyze(conn, sid, ev, entries):
    """Compute the detectors across the draws. Returns a dict the report + summary both read."""
    occ = ev["occ"]
    present = B.loose_keyset(conn, sid)           # verses where the word genuinely appears, any form
    senses = [parse_senses(e["senses_block"]) for e in entries]   # tolerant: bold OR plain headers
    counts = [len(s) for s in senses]
    spread = dict(sorted(Counter(counts).items()))
    real = [e["audit"]["real"] for e in entries]
    tagging = [e["audit"]["tagging"] for e in entries]
    noverse = [e["audit"]["noverse"] for e in entries]
    cov_flag = [bool((e["coverage"] or "").strip()) for e in entries]
    thin_gloss = [bool(THIN_RE.search(e["gloss_notes"] or "")) for e in entries]
    # padding flags, two tiers:
    #   HARD = senses > occ — mathematically impossible to ground each sense on its own occurrence.
    #   SOFT = occ/2 < senses <= occ (and >=2 senses) — possible but at least one sense rests on a
    #          single verse; a read-trigger, NOT a fail. bathmos (2 occ / 2 senses) lands here and is
    #          the honest case — the point is to see whether a TEMPTER lands here too.
    senses_gt_occ = [c > occ for c in counts]
    soft_pad = [(c >= 2 and c <= occ and 2 * c > occ) for c in counts]
    # the sharp identifier: which sense(s) in each draw rest on NO real occurrence (named headlines),
    # so we can see if the same invented job repeats across draws (prompt-induced) or flickers (noise).
    grounding = [[{"headline": s["headline"], "refs": len(s["refs"]),
                   "grounded": sum(1 for r in s["refs"] if r in present)} for s in sl]
                 for sl in senses]
    ungrounded = [[g["headline"] for g in gl if g["grounded"] == 0] for gl in grounding]
    return {
        "occ": occ, "fed": ev["fed"],
        "counts": counts, "spread": spread, "max_senses": max(counts), "min_senses": min(counts),
        "real": real, "real_max": max(real), "real_total": sum(real),
        "tagging": tagging, "noverse": noverse,
        "passtotal": [f"{e['audit']['pass']}/{e['audit']['total']}" for e in entries],
        "cov_flag": cov_flag, "cov_flag_n": sum(cov_flag),
        "thin_gloss": thin_gloss, "thin_gloss_n": sum(thin_gloss),
        "senses_gt_occ": senses_gt_occ, "senses_gt_occ_n": sum(senses_gt_occ),
        "soft_pad": soft_pad, "soft_pad_n": sum(soft_pad),
        "grounding": grounding,
        "ungrounded": ungrounded, "ungrounded_n": sum(1 for u in ungrounded if u),
    }


def trunc(s, n=150):
    s = (s or "").strip().replace("\n", " ")
    return s if len(s) <= n else s[:n - 1] + "…"


def render_word(sid, ev, entries, det):
    """The per-word report: detector summary, then every draw's full card for the eye-read."""
    L = []
    def w(s=""):
        L.append(s)

    tag = f"   [{CONTROLS[sid]}]" if sid in CONTROLS else ""
    w("=" * 92)
    w(f"{sid}  {ev['lemma']} ({ev['translit']})   role: {ROLE.get(sid,'')}{tag}")
    w(f"  occurrences: {det['occ']} (fed {det['fed']}: {ev['ot']} OT / {det['fed']-ev['ot']} NT)"
      f"   |  renderings: {ev['renderings']}")
    w(f"  SENSE-COUNT spread across {len(entries)} draws: "
      + "{" + ", ".join(f"{k}:{v}" for k, v in det["spread"].items()) + "}"
      + f"   [occ={det['occ']}]  — the padding tell (read as a spread, not an average)")
    if det["senses_gt_occ_n"]:
        w(f"  !! HARD padding flag: senses > occurrences in {det['senses_gt_occ_n']}/{len(entries)} "
          f"draw(s) — a sense with no occurrence to stand on")
    if det["soft_pad_n"]:
        w(f"  ~  soft padding flag (READ the card, not a fail): occ/2 < senses ≤ occ in "
          f"{det['soft_pad_n']}/{len(entries)} draw(s) — at least one sense rests on a single verse "
          f"(bathmos lands here honestly)")
    if det["ungrounded_n"]:
        w(f"  !! UNGROUNDED sense(s) — rest on NO real occurrence (same job across draws = "
          f"prompt-induced invention; different each draw = noise):")
        for j, u in enumerate(det["ungrounded"], 1):
            if u:
                w(f"       draw{j}: " + "  ;  ".join(u))
    w(f"  citation gate (pass/total): " + " | ".join(
        f"draw{i+1} {pt} (real {r})" + (f" tag {t}" if t else "") + (f" noverse {nv}" if nv else "")
        for i, (pt, r, t, nv) in enumerate(zip(det["passtotal"], det["real"], det["tagging"], det["noverse"]))))
    if det["real_max"]:
        w(f"     ^^ REAL citation miss present — a cited verse lacks the lemma (the hallucination signal)")
    w(f"  coverage self-flag: " + " | ".join(
        f"draw{i+1} " + (f'"{trunc(e["coverage"],110)}"' if (e["coverage"] or "").strip() else "(none)")
        for i, e in enumerate(entries)))
    if det["thin_gloss_n"]:
        w(f"  thin-evidence language in gloss_notes: {det['thin_gloss_n']}/{len(entries)} draw(s)")

    for i, e in enumerate(entries, 1):
        w("")
        c = det["counts"][i - 1]
        gt = "  !! senses > occ" if c > det["occ"] else ""
        w(f"  ----- DRAW {i}  [{c} senses]  audit "
          f"{e['audit']['pass']}/{e['audit']['total']}{gt} -----")
        if e["senses_block"]:
            for ln in e["senses_block"].splitlines():
                if ln.strip():
                    w(f"    {ln.rstrip()}")
        else:
            w("    (no senses_block — parse break)")
        g = det["grounding"][i - 1]
        if g:
            w(f"    sense grounding (real-occ refs / cited refs): "
              + ", ".join(f"{s['grounded']}/{s['refs']}" for s in g))
            ung = [s["headline"] for s in g if s["grounded"] == 0]
            if ung:
                w(f"    !! UNGROUNDED: " + "  ;  ".join(ung))
        if (e["range"] or "").strip():
            w(f"    Range: {trunc(e['range'], 300)}")
        if (e["gloss_notes"] or "").strip():
            w(f"    Gloss notes: {trunc(e['gloss_notes'], 300)}")
        if (e["coverage"] or "").strip():
            w(f"    Coverage: {trunc(e['coverage'], 300)}")
        vs = e.get("verses") or []
        w(f"    Verses cited & found in ABP ({len(vs)}):")
        for v in vs:
            w(f"      {v['ref']:<12} {trunc(v['text'], 110)}")
        ms = e["audit"].get("misses") or []
        if ms:
            w(f"    Citation misses: " + ", ".join(f"{m['ref']}[{m['bucket']}]" for m in ms))
    return L


def render_summary(rows):
    """The detector table across the whole set — this is the cutoff read."""
    L = []
    def w(s=""):
        L.append(s)
    w("")
    w("=" * 92)
    w("SUMMARY — detectors vs occurrence count (the cutoff read)")
    w("  Read CONTROLS first: G898 bathmos (genuine 2 senses) + G2299 thea (homograph).")
    w("=" * 92)
    w(f"  {'word':<20} {'occ':>3}  {'sense-spread':<14} {'hard':>5} {'soft':>5} {'ungr':>5}  "
      f"{'real':>4}  {'cov':>5}  role")
    w("  " + "-" * 90)
    for r in rows:
        d = r["det"]
        n = len(d["counts"])
        spread = "{" + ",".join(f"{k}:{v}" for k, v in d["spread"].items()) + "}"
        hard = f"{d['senses_gt_occ_n']}/{n}" if d["senses_gt_occ_n"] else "-"
        soft = f"{d['soft_pad_n']}/{n}" if d["soft_pad_n"] else "-"
        ungr = f"{d['ungrounded_n']}/{n}" if d["ungrounded_n"] else "-"
        rm = f"{d['real_total']}" if d["real_total"] else "-"
        cf = f"{d['cov_flag_n']}/{n}" if d["cov_flag_n"] else "-"
        name = f"{r['lemma']} {r['sid']}"
        w(f"  {name:<20} {d['occ']:>3}  {spread:<14} {hard:>5} {soft:>5} {ungr:>5}  "
          f"{rm:>4}  {cf:>5}  {ROLE.get(r['sid'],'')}")
    w("")
    w("  hard = draws where senses > occurrences (a sense with no occurrence to ground it)")
    w("  soft = draws where occ/2 < senses ≤ occ (a sense on a single verse — read-trigger, not a fail)")
    w("  ungr = draws with a sense resting on NO real occurrence (the named manufactured sense)")
    w("  real = total citation REAL misses across draws (cited verse lacks the word)")
    w("  cov  = draws where the engine self-flagged thin/clustered coverage")
    return L


def save(save_dir, sid, lemma, translit, ev, entries, det, report_lines):
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = os.path.join(save_dir, f"stress_{sid}_{ts}")
    payload = {
        "strongs": sid, "lemma": lemma, "translit": translit, "role": ROLE.get(sid, ""),
        "occ": ev["occ"], "fed": ev["fed"], "ot": ev["ot"], "renderings": ev["renderings"],
        "detectors": {k: det[k] for k in
                      ("spread", "max_senses", "real", "real_total", "real_max", "tagging",
                       "noverse", "cov_flag", "cov_flag_n", "thin_gloss_n", "senses_gt_occ_n")},
        "draws": entries,           # full assembled cards (same shape build_lexica_def stores)
        "report": "\n".join(report_lines),
    }
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    with open(base + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")
    return base


def resummarize(save_dir, db):
    """Rebuild the summary table from the saved JSON dumps — no model, no rebuild. Re-counts senses
    with the tolerant (bold-OR-plain) parser, re-derives every sense-parse-dependent flag, and prints
    a confirmation of the two controls so the fix is visible. Read-only on bible.db (for grounding)."""
    import glob
    latest = {}
    for p in sorted(glob.glob(os.path.join(save_dir, "stress_G*.json"))):
        sid = os.path.basename(p).split("_")[1]
        latest[sid] = p                      # sorted ascending -> newest timestamp wins per word
    if not latest:
        sys.exit(f"no stress_*.json dumps found in {save_dir}")
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.create_function("strip_accents", 1, B.strip_accents)
    rows = []
    for sid, p in latest.items():
        with open(p, encoding="utf-8") as f:
            j = json.load(f)
        ev = {"occ": j["occ"], "fed": j["fed"], "ot": j.get("ot", 0),
              "renderings": j.get("renderings", 0), "lemma": j["lemma"], "translit": j["translit"]}
        det = analyze(conn, sid, ev, j["draws"])
        rows.append({"sid": sid, "lemma": j["lemma"], "det": det})
    rows.sort(key=lambda r: TARGETS.index(r["sid"]) if r["sid"] in TARGETS else 99)

    print(f"re-summarized {len(rows)} word(s) from {save_dir} (no model).\n")
    print("CONFIRM — the two controls, re-counted with the fixed parser:")
    for sid in ("G898", "G2299"):
        r = next((x for x in rows if x["sid"] == sid), None)
        if not r:
            continue
        print(f"  {sid} {r['lemma']}  counts/draw {r['det']['counts']}  spread {r['det']['spread']}")
        for k, gl in enumerate(r["det"]["grounding"], 1):
            heads = " | ".join(f"{g['headline']} ({g['grounded']}/{g['refs']})" for g in gl) or "(none)"
            print(f"     draw{k}: {heads}")
    print()
    summary = render_summary(rows)
    print("\n".join(summary))
    sp = os.path.join(save_dir, "SUMMARY_fixed_" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".txt")
    with open(sp, "w", encoding="utf-8") as f:
        f.write("\n".join(summary) + "\n")
    print(f"\nsaved: {sp}")
    conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.expanduser("~/bible-db/bible.db"))
    ap.add_argument("--word", help="one G-number (default: the 18-word approved set)")
    ap.add_argument("--runs", type=int, default=3, help="draws per word (default 3)")
    ap.add_argument("--budget", type=int, default=B.BUDGET)
    ap.add_argument("--save-dir", default="~/lexica_stress",
                    help="scratch folder OUTSIDE the repo for the dumps (default ~/lexica_stress)")
    ap.add_argument("--resummarize", action="store_true",
                    help="rebuild the summary table from the saved JSON dumps in --save-dir "
                         "(no model, no rebuild) — used after a parser fix")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    save_dir = os.path.expanduser(args.save_dir)
    os.makedirs(save_dir, exist_ok=True)

    if args.resummarize:
        resummarize(save_dir, args.db)
        return

    targets = [args.word.upper()] if args.word else list(TARGETS)
    targets = [("G" + t if t[:1] not in ("G", "H") else t) for t in targets]

    # READ-ONLY — cannot write the database. This is the whole safety story.
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.create_function("strip_accents", 1, B.strip_accents)
    has_surface = B.table_exists(conn, "abp_surface")

    calls = len(targets) * args.runs
    print(f"STRESS TEST — {len(targets)} word(s) x {args.runs} draws = {calls} Sonnet calls "
          f"(~${calls*0.03:.2f}).")
    print(f"frozen engine stamp: {B.synth_ver()}   (proves VERSE_PROMPT is the live frozen prompt)")
    print(f"read-only on {args.db}; dumps -> {save_dir}\n")

    import anthropic
    client = anthropic.Anthropic(api_key=B.get_key())

    rows = []
    for sid in targets:
        ev = gather_evidence(conn, sid, args.budget, has_surface)
        if not ev["ctx"]:
            print(f"{sid}: no occurrences — skip.")
            continue
        print(f"{sid} {ev['lemma']} ({ev['translit']}): drawing {args.runs}x …", flush=True)
        entries = []
        for k in range(args.runs):
            raw = B.model_prose(client, sid, ev["translit"], ev["gset"], ev["ctx"])
            entry = B.assemble(conn, sid, ev["lemma"], ev["translit"], raw)
            entries.append(entry)
            print(f"   draw {k+1}/{args.runs}: {len(parse_senses(entry['senses_block']))} senses, "
                  f"audit {entry['audit']['pass']}/{entry['audit']['total']} "
                  f"(real {entry['audit']['real']})", flush=True)
        det = analyze(conn, sid, ev, entries)
        report = render_word(sid, ev, entries, det)
        print("\n".join(report))
        base = save(save_dir, sid, ev["lemma"], ev["translit"], ev, entries, det, report)
        print(f"  saved: {base}.txt  (+ .json)\n")
        rows.append({"sid": sid, "lemma": ev["lemma"], "det": det})

    if len(rows) > 1:
        summary = render_summary(rows)
        print("\n".join(summary))
        sp = os.path.join(save_dir, "SUMMARY_" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".txt")
        with open(sp, "w", encoding="utf-8") as f:
            f.write("\n".join(summary) + "\n")
        print(f"\nsummary saved: {sp}")

    conn.close()


if __name__ == "__main__":
    main()
