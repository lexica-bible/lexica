#!/usr/bin/env python3
"""
dryrun_abp_surface_fill.py — READ-ONLY dry run of the abp_surface FILL (lane 1).
Census + rulings: docs/handoffs/CENSUS_abp_surface_fill.md. Opens bible.db mode=ro and
writes NOTHING to any database: it only lists the writes an apply WOULD make.
The matching rules are imported from scripts/census_abp_surface_glued.py (the one copy).

TWO ROUTES, both write abp_surface only (never words, never pn_greek_identity):
  A-route  slots with NO abp_surface row where the app prints a form (the 4,058 list):
           fill_resolved (Lexicon: form listed / = headword) · fill_pronoun (via ABP 1473) ·
           fill_unlisted (form not in the Lexicon; lemma held) — INSERT the app's form.
           Held: E2 English typed in Greek letters · C/D number disagreements (13) ·
           F name slots (out of lane, except where a ruled name split reaches them).
  B-route  the 544 glued NBSP values the lane (a) audit flagged:
           split_trim (receiver already holds the word) · split_keep + split_receive /
           split_receive_name (receiver empty: UPDATE the glued slot, INSERT the receiver) ·
           normalize (UPDATE: NBSP -> one plain space; a doubled NBSP collapses).
           Held: split-conflict (4) · split-ambiguous (1). The 1,420 unflagged: no action.
  D        a split receiver that is also an A-route row: ONE write; both sources must agree.

APP LETTERS (A-route forms come from the app): the JP-ruled DEFECT_MAP (C Q H O U R П +)
plus ἡ -> ή — the app never prints ή (U+03AE) and prints ἡ (U+1F21) where ή belongs, mostly
mid-word where no breathing can stand. That one extra letter is a PROPOSAL riding this dry run
(control E1 below measures it on every compared slot); it is not in DEFECT_MAP.
LEMMA: no lemma is written anywhere. abp_surface has no lemma column; the reader's lemma comes
from the lexicon by number; words.lemma is a words-table column read by audits and the name
builder. The CSV reports the served lemma, words.lemma and the Lexicon's lemma side by side.

Run on PA from ~/bible-db (needs abp_helps/analytical_lexicon.tsv uploaded — gitignored):
  PYTHONIOENCODING=utf-8 python3 scripts/dryrun_abp_surface_fill.py ~/bible-db/bible.db \\
      --dump ~/abp_app_dump.tsv --out ~/abp_surface_fill_dryrun.csv > ~/abp_surface_fill_dryrun.txt
"""
import argparse
import csv
import os
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_abp_app_vs_surface import DEFECT_MAP, english_font
from census_abp_surface_glued import (NB, Lexicon, agree, clean, fold, is_name, plan_glued,
                                      resolve_level)

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
ETA_FIX = {"ἡ": "ή"}           # ἡ -> ή  (proposal; see docstring)

# Pre-registered expected picture (CENSUS_abp_surface_fill.md + the 10/24 PA exports).
# Any line that differs is a FAIL to report, not a number to adopt.
# fill_resolved 3,724 / fill_unlisted 33 in the census; 3 of them carry an app character with no
# ruling (Num 12:3 'πρα=ς', Pro 14:30 'πρα=θυμος', Psa 60:0 pos 22 'Ἰωάβ' on a 1473 slot) -> held.
# JP's "3,793 + 69 + 33" counts the 69 pronouns twice: 3,793 already includes them.
EXPECT = {
    "fill_resolved": 3722, "fill_pronoun": 69, "fill_unlisted": 32, "held_unmapped_letter": 3,
    "held_english_in_greek": 28, "held_number_disagreement": 13, "out_of_lane_name": 191,
    "split_trim": 92, "split_keep": 89, "split_receive": 68, "split_receive_name": 21,
    "normalize": 357, "held_split_conflict": 4, "held_split_ambiguous": 1, "held_D_disagree": 1,
    "D": 45, "D_agree": 44, "D_with_A_route_fill": 39, "D_name": 6, "unflagged_glued": 1420,
    # Deu 4:45 pos 11 (name split): ours Μωυσης vs app Μωυσής -> that split held (keep + receiver).
    # slots written: A-route alone 3,823 - 39 merged = 3,784 inserts + 89 receivers = 3,873
    # inserts; 92 trim + 89 keep + 357 normalize = 538 updates; 4,411 slots in all.
    "writes_insert": 3873, "writes_update": 538, "writes_total": 4411,
}


def app_to_ours(g):
    """App printed form -> our letters: defect map + ἡ fix, NFC, whitespace to one space."""
    s = "".join(DEFECT_MAP.get(c, ETA_FIX.get(c, c)) for c in (g or ""))
    s = unicodedata.normalize("NFC", s)
    return " ".join(s.split())


def style_problems(s):
    """Characters a written form must not carry (our table: monotonic Greek, no breathings)."""
    bad = set()
    for ch in s:
        if "Ͱ" <= ch <= "Ͽ" or ch in "'’ ":
            continue
        bad.add(ch)
    return bad


def main():
    ap = argparse.ArgumentParser(description="READ-ONLY dry run of the abp_surface fill.")
    ap.add_argument("db")
    ap.add_argument("--lexicon", default=os.path.join(REPO, "abp_helps", "analytical_lexicon.tsv"))
    ap.add_argument("--missing", default=os.path.join(REPO, "abp_app_html", "missing_printed_forms.tsv"))
    ap.add_argument("--dump", required=True, help="lane (a) audit --dump file (all compared slots)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    for p in (a.lexicon, a.missing, a.dump):
        if not os.path.exists(p):
            sys.exit(f"FATAL: input missing: {p}")
    lex = Lexicon(a.lexicon)

    con = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    con.execute("PRAGMA busy_timeout=30000")
    vkey, vref = {}, {}
    for vid, b, ch, vs in con.execute("SELECT id, book, chapter, verse FROM verses"):
        vkey[(b, str(ch), str(vs))] = vid
        vref[vid] = (b, str(ch), str(vs))
    words = {}
    for vid, pos, s, wl in con.execute(
            "SELECT verse_id, position, COALESCE(strongs,''), COALESCE(lemma,'') FROM words"):
        words[(vid, pos)] = (s.strip(), wl)
    surf = {(v, p): (f or "", t or "") for v, p, f, t in con.execute(
        "SELECT verse_id, position, form, translit FROM abp_surface")}
    n_surface = len(surf)
    lexl = {sg: l for sg, l in con.execute("SELECT strongs_g, lemma FROM lexicon") if sg}
    dotted = {}
    if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='dotted_lexicon'").fetchone():
        dotted = {s: l for s, l in con.execute("SELECT strongs, lemma FROM dotted_lexicon") if s}
    n_ident = con.execute("SELECT count(*) FROM pn_greek_identity").fetchone()[0]
    con.close()                                     # nothing below touches the database

    def served_lemma(num):
        n = clean(num)
        if "." in n and ("G" + n) in dotted:
            return dotted["G" + n]
        return lexl.get("G" + n.split(".")[0], "") if n and not is_name(n) else ""

    def ref(vid, pos):
        b, ch, vs = vref[vid]
        return b, ch, vs, pos

    writes = {}          # (vid, pos) -> write dict      (one per slot — G3)
    rows = []            # every CSV row (writes + holds + no-action)
    touched = Counter()
    held_slots = set()
    fails = []

    def emit(vid, pos, cls, action, old_form, new_form, num, note="", extra=None):
        b, ch, vs, _ = ref(vid, pos)
        wl = words.get((vid, pos), ("", ""))[1]
        r = dict(book=b, chapter=ch, verse=vs, position=pos, number=num, cls=cls, action=action,
                 old_form=old_form, new_form=new_form, old_lemma_served=served_lemma(num),
                 words_lemma=wl, lexicon_lemma="", new_lemma="(no lemma write)",
                 old_translit=surf.get((vid, pos), ("", ""))[1], app_form_raw="", note=note)
        if extra:
            r.update(extra)
        rows.append(r)
        if action in ("insert", "update"):
            touched[(vid, pos)] += 1
            writes[(vid, pos)] = r
        elif action == "hold":
            held_slots.add((vid, pos))
        return r

    # ── A-route ───────────────────────────────────────────────────────────────
    A = {}
    cls_of = {"A": "fill_resolved", "B": "fill_resolved", "P": "fill_pronoun", "E": "fill_unlisted",
              "E2": "held_english_in_greek", "C": "held_number_disagreement",
              "D": "held_number_disagreement", "F": "out_of_lane_name"}
    with open(a.missing, encoding="utf-8", newline="") as f:
        mrows = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    for m in mrows:
        vid = vkey.get((m["book"], m["chapter"], m["verse"]))
        pos = int(m["position"])
        lvl, lemma = resolve_level(lex, m["strongs"], m["app_printed_form"])
        live = words.get((vid, pos)) if vid else None
        A[(vid, pos)] = dict(m=m, lvl=lvl, lemma=lemma, live=live,
                             new=app_to_ours(m["app_printed_form"]))
    if len(A) != len(mrows):
        fails.append(f"G3 the A list names {len(mrows) - len(A)} slot(s) twice (or a verse is missing live)")
    a_drift = Counter()

    # ── B-route: glued values, re-derived LIVE ────────────────────────────────
    d544 = {}
    eta = Counter()
    with open(a.dump, encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 12:
                continue
            app_g, tgt, ours, cl = p[7], p[8], p[10], p[11]
            if tgt == "surface" and cl == "mm_ours_nbsp":
                d544[(p[0], p[1], p[2], int(p[3]))] = p
            # E1 evidence for ἡ -> ή: on surface pairs with the SAME letters (fold match), what
            # does OUR form hold at each spot where the app has ἡ? (our letter = the evidence,
            # the method the defect map was ruled on)
            if tgt == "surface" and cl in ("exact", "nfc", "fold", "defect"):
                if "ή" in unicodedata.normalize("NFC", app_g):
                    eta["app spots with ή (U+03AE)"] += unicodedata.normalize("NFC", app_g).count("ή")
                if "ἡ" in app_g:
                    am = unicodedata.normalize("NFC", "".join(DEFECT_MAP.get(c, c) for c in app_g))
                    om = unicodedata.normalize("NFC", ours)
                    if len(am) != len(om):
                        eta["ἡ pairs not same length (skipped)"] += 1
                        continue
                    for i, ch in enumerate(am):
                        if ch == "ἡ":
                            eta["app ἡ spots"] += 1
                            eta["ours at that spot: " + om[i]] += 1

    glued = []
    for (vid, pos), (form, _t) in surf.items():
        if NB in form:
            r = dict(strongs=words.get((vid, pos), ("", ""))[0], form=form, position=pos,
                     prev_strongs=words.get((vid, pos - 1), ("", ""))[0] if (vid, pos - 1) in words else "",
                     prev_form=surf.get((vid, pos - 1), ("", ""))[0],
                     next_strongs=words.get((vid, pos + 1), ("", ""))[0] if (vid, pos + 1) in words else "",
                     next_form=surf.get((vid, pos + 1), ("", ""))[0])
            glued.append((vid, pos, r))
    in544 = {(vkey.get(k[:3]), k[3]) for k in d544}

    D_rows = []
    d_merge = set()      # A-route slots written by the split instead
    d_hold = set()       # D receivers held because the two sources disagree
    for vid, pos, r in sorted(glued):
        g = plan_glued(lex, r)
        num = r["strongs"]
        if (vid, pos) not in in544:
            later = g["part"] in ("split-eligible", "split-ambiguous", "split-conflict")
            emit(vid, pos, "unflagged_glued", "hold" if later else "none", r["form"], "", num,
                 "held for a later pass" if later else "no action (ruling)")
            continue
        p = g["plan"]
        if g["part"] == "split-conflict":
            emit(vid, pos, "held_split_conflict", "hold", r["form"], "", num, g["why"])
            continue
        if g["part"] == "split-ambiguous":
            emit(vid, pos, "held_split_ambiguous", "hold", r["form"], "", num, g["why"])
            continue
        if g["part"] == "normalize-only":
            emit(vid, pos, "normalize", "update", r["form"], " ".join(g["toks"]), num, g["why"])
            continue
        own_tok, extra_tok, rnum, recv_agree, state = p[1], p[2], p[3], p[6], p[7]
        rpos = g["recv_pos"]
        app = d544.get(ref(vid, pos))
        if app and fold(app[7]) != fold(own_tok):
            fails.append(f"G1 split keeps {own_tok!r} but the app prints {app[7]!r} at {ref(vid, pos)}")
        if state == "receiver already holds it":
            emit(vid, pos, "split_trim", "update", r["form"], own_tok, num, f"receiver pos {rpos} holds it")
            continue
        rcls = "split_receive_name" if recv_agree == "name" else "split_receive"
        note = ""
        if (vid, rpos) in A:
            ar = A[(vid, rpos)]
            same = ar["new"] == unicodedata.normalize("NFC", extra_tok)
            D_rows.append((vid, rpos, ar["lvl"], same, ar["new"], extra_tok))
            if not same:
                # the two sources must agree (ruling); they don't -> hold the WHOLE split and
                # the receiver's A-route fill. Loud: listed in the report and the CSV.
                d_hold.add((vid, rpos))
                held_slots.add((vid, rpos))
                emit(vid, pos, "held_D_disagree", "hold", r["form"], "", num,
                     f"receiver pos {rpos}: split gives {extra_tok!r}, app/A-route gives {ar['new']!r}")
                continue
            note = f"D: also A-route ({ar['lvl']}); sources agree"
            if ar["lvl"] in ("A", "B", "P", "E"):
                d_merge.add((vid, rpos))
        emit(vid, pos, "split_keep", "update", r["form"], own_tok, num, f"receiver pos {rpos}")
        if (vid, rpos) in surf:
            fails.append(f"G-recv receiver {ref(vid, rpos)} already has an abp_surface row")
        emit(vid, rpos, rcls, "insert", "", extra_tok, rnum, note)

    # A-route rows now (after D merge is known)
    for (vid, pos), ar in sorted(A.items(), key=lambda kv: (kv[0][0] or 0, kv[0][1])):
        m, lvl = ar["m"], ar["lvl"]
        cls = cls_of[lvl]
        extra = dict(lexicon_lemma=ar["lemma"], app_form_raw=m["app_printed_form"])
        if vid is None or ar["live"] is None:
            a_drift["no live verse/word"] += 1
            emit(vid or 0, pos, "held_drift", "hold", "", "", m["strongs"], "no live word row", extra) if vid else None
            continue
        if clean(ar["live"][0]) != clean(m["strongs"]):
            a_drift["number changed"] += 1
            emit(vid, pos, "held_drift", "hold", "", "", ar["live"][0],
                 f"list number {m['strongs']} != live", extra)
            continue
        if (vid, pos) in d_hold:            # its split was held: no fill by either route
            emit(vid, pos, cls, "hold", "", "", m["strongs"], "held: D sources disagree", extra)
            continue
        if not cls.startswith("fill_"):
            if (vid, pos) in touched:
                if cls == "out_of_lane_name":     # a ruled name split reached this F slot: allowed
                    writes[(vid, pos)]["note"] += f" · A-route class {cls}"
                    continue
                fails.append(f"G4 split writes {ref(vid, pos)}, a held A-route row ({cls})")
            emit(vid, pos, cls, "hold", "", "", m["strongs"], "", extra)
            continue
        if (vid, pos) in d_merge:
            writes[(vid, pos)].update(lexicon_lemma=ar["lemma"], app_form_raw=m["app_printed_form"])
            writes[(vid, pos)]["note"] += f" · counted in {cls}"
            rows.append(dict(writes[(vid, pos)], cls=cls, action="merged-into-split",
                             note="written once by the split row"))
            continue
        if (vid, pos) in surf:
            a_drift["now has a form"] += 1
            emit(vid, pos, "held_drift", "hold", surf[(vid, pos)][0], "", m["strongs"],
                 "abp_surface row exists now", extra)
            continue
        new = ar["new"]
        bad = style_problems(new)
        if bad or english_font(m["app_printed_form"]):
            emit(vid, pos, "held_unmapped_letter", "hold", "", new, m["strongs"],
                 "unmapped: " + " ".join(f"U+{ord(c):04X}{c}" for c in sorted(bad)), extra)
            continue
        if cls in ("fill_resolved", "fill_pronoun"):
            ag = agree(lex, ar["live"][0], new)
            if ag not in ("full", "pron"):
                fails.append(f"G1 {cls} {ref(vid, pos)} live number {ar['live'][0]} + form {new!r} -> {ag}")
        emit(vid, pos, cls, "insert", "", new, m["strongs"],
             "lemma held" if cls == "fill_unlisted" else "", extra)

    # ── gates ────────────────────────────────────────────────────────────────
    twice = [k for k, n in touched.items() if n > 1]
    if twice:
        fails.append(f"G3 {len(twice)} slot(s) written twice: {[ref(*k) for k in twice[:5]]}")
    on_held = [k for k in writes if k in held_slots]
    if on_held:
        fails.append(f"G4 {len(on_held)} write(s) on a held slot: {[ref(*k) for k in on_held[:5]]}")
    for k, w in writes.items():
        if NB in w["new_form"] or "ἡ" in w["new_form"] or style_problems(w["new_form"]):
            fails.append(f"G6 written form breaks letter style at {ref(*k)}: {w['new_form']!r}")
        if w["action"] == "insert" and k in surf:
            fails.append(f"G6 insert onto an existing row {ref(*k)}")
        if w["action"] == "update" and k not in surf:
            fails.append(f"G6 update of a missing row {ref(*k)}")
        if k not in words:
            fails.append(f"G5 write on a slot with no word row {ref(*k)} (no new word rows)")

    # ── report ───────────────────────────────────────────────────────────────
    # A-route classes count every A row of that class (written alone OR merged into a split);
    # out_of_lane_name counts all F rows (held, or reached by a ruled name split).
    C = Counter(r["cls"] for r in rows)
    cnt = Counter()
    for r in rows:
        cnt[r["cls"]] += 1
    cnt["out_of_lane_name"] += sum(1 for w in writes.values() if "A-route class out_of_lane_name" in w["note"])
    cnt["D"] = len(D_rows)
    cnt["D_with_A_route_fill"] = sum(1 for d in D_rows if d[2] in ("A", "B", "P", "E"))
    cnt["D_name"] = sum(1 for d in D_rows if d[2] == "F")
    cnt["D_agree"] = sum(1 for d in D_rows if d[3])
    cnt["writes_insert"] = sum(1 for w in writes.values() if w["action"] == "insert")
    cnt["writes_update"] = sum(1 for w in writes.values() if w["action"] == "update")
    cnt["writes_total"] = len(writes)

    print("=" * 78)
    print("abp_surface FILL — DRY RUN (read-only; bible.db opened mode=ro; nothing written)")
    print("=" * 78)
    print(f"live: abp_surface {n_surface} rows · glued (NBSP) {len(glued)} · 544 list {len(d544)} "
          f"(found live {len(in544 & {(v, p) for v, p, _ in glued})}) · A list {len(mrows)} · "
          f"pn_greek_identity {n_ident} rows (read only to report; never written)")
    print(f"A-route drift vs the 10/24 list: {dict(a_drift) or 'none'}")

    print("\nCONTROLS")
    def find(b, ch, vs, pos, cls=None):
        vid = vkey.get((b, ch, vs))
        return [r for r in rows if r["book"] == b and r["chapter"] == ch and r["verse"] == vs
                and r["position"] == pos and (cls is None or r["cls"] == cls)]
    for label, (b, ch, vs, pos), want_cls, want in (
            ("C1 1Sa 17:57 pos 22", ("1Sa", "17", "57", 22), "normalize", "χειρί αυτού"),
            ("C2 Gen 4:8 pos 1   ", ("Gen", "4", "8", 1), "fill_resolved", "είπε"),
            ("C3 Gen 5:32 pos 1  ", ("Gen", "5", "32", 1), "split_trim", "ην")):
        got = find(b, ch, vs, pos)
        ok = bool(got) and got[0]["cls"] == want_cls and got[0]["new_form"] == want
        print(f"   {label} expect {want_cls} {want!r} -> got "
              f"{(got[0]['cls'], got[0]['new_form']) if got else None} {'PASS' if ok else 'FAIL'}")
        if not ok:
            fails.append(f"control {label.strip()}")
    spots = eta["app ἡ spots"]
    e1_ok = spots > 0 and eta["app spots with ή (U+03AE)"] == 0 and \
        eta["ours at that spot: ἡ"] == 0 and eta["ours at that spot: ή"] >= 0.99 * spots
    print(f"   E1 ἡ -> ή evidence (same-letter surface pairs): {dict(eta)} -> {'PASS' if e1_ok else 'FAIL'}"
          f"  [expect: app never prints ή · ours never ἡ · ours ή at >= 99% of the app's ἡ spots]")
    if not e1_ok:
        fails.append("E1 ἡ->ή evidence")

    print("\nCOUNTS (expected | actual)")
    for k, v in EXPECT.items():
        got = cnt.get(k, 0)
        flag = "" if got == v else "   <-- DIFFERS"
        print(f"   {k:28} {v:6} | {got:6}{flag}")
        if got != v:
            fails.append(f"count {k}: expected {v}, got {got}")
    others = {k: v for k, v in C.items() if k not in EXPECT}
    print(f"   other classes: {others or 'none'}")
    ins = sum(1 for w in writes.values() if w["action"] == "insert")
    upd = sum(1 for w in writes.values() if w["action"] == "update")
    eta_rows = sum(1 for w in writes.values() if "ἡ" in w.get("app_form_raw", ""))
    stale = sum(1 for w in writes.values() if w["action"] == "update" and w["old_translit"])
    print(f"\nWRITES: {len(writes)} slots · insert {ins} · update {upd} · abp_surface after = "
          f"{n_surface + ins} (now {n_surface}) · forms using the ἡ->ή fix {eta_rows}")
    print(f"   translit: {stale} updated rows carry a now-stale translit, {ins} new rows have none "
          f"-> the apply must re-run scripts/build_abp_translit.py")
    lemma_same = sum(1 for r in rows if r["cls"] in ("fill_resolved", "fill_pronoun") and r["lexicon_lemma"]
                     and any(fold(x) == fold(r["old_lemma_served"]) for x in r["lexicon_lemma"].split(" / ")))
    nfill = sum(1 for r in rows if r["cls"] in ("fill_resolved", "fill_pronoun") and r["action"] != "hold")
    print(f"   lemma: no lemma write. Lexicon lemma = served lemma (letters) on {lemma_same} of {nfill} "
          f"fill_resolved/pronoun rows; words.lemma empty on "
          f"{sum(1 for w in writes.values() if not w['words_lemma'])} written slots")

    print("\nGATES")
    for g, lbl in (("G1", "number + form on every Lexicon-backed write (live number)"),
                   ("G2", "D rows: every WRITTEN one has both sources giving the same bytes (a disagreeing one is held)"),
                   ("G3", "no slot written twice"), ("G4", "no write on a held slot"),
                   ("G5", "writes only to abp_surface, only on existing word slots; 0 name-table writes"),
                   ("G6", "written forms: no NBSP, no ἡ, monotonic Greek only; insert/update shape")):
        bad = [f for f in fails if f.startswith(g)]
        print(f"   {g} {lbl}: {'PASS' if not bad else 'FAIL (' + str(len(bad)) + ')'}")
        for f in bad[:8]:
            print(f"        {f}")
    with open(a.out, "w", encoding="utf-8", newline="") as f:
        cols = ["book", "chapter", "verse", "position", "number", "cls", "action", "old_form",
                "new_form", "old_lemma_served", "words_lemma", "lexicon_lemma", "new_lemma",
                "old_translit", "app_form_raw", "note"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "old_form": r["old_form"].replace(NB, "␣")})   # ␣ marks an NBSP
    print(f"\nwrote {len(rows)} rows -> {a.out}  (␣ in old_form = an NBSP)")
    print("\nRESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL line(s) — see above")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
