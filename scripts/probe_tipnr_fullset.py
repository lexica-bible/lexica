#!/usr/bin/env python3
"""
probe_tipnr_fullset.py — READ-ONLY. The full-ambiguous-set feasibility numbers
for Issue 2, reporting THREE rates separately (they fail independently):

  RATE 1  verse -> TIPNR-entity bind  (the identity number; decides the rebuild —
          it's what kills the AI-blurb verse-fabrication class). Matched by verse
          across ALL entities, linked by name-spelling OR base Strong's, so a
          surface word filed under a different headword (Cushi -> the "Cush"
          place's "Cushite" group) still lands. Misses split into:
            soft  = versification/locality (a candidate entity has refs in the
                    SAME book+chapter; an offset, not truly unbound)
            hard  = no linked entity anywhere in that book.
  RATE 2  TIPNR person -> metaV person bridge  (relationship-keyed).
  RATE 3  TIPNR place  -> metaV place  bridge  (name-only; expected poor — we
          just report how many places even have a usable map row).

Why split: TIPNR carries its own bio/refs/descriptions, so identity+content come
from TIPNR (rate 1). metaV is only needed for coords/dates (rates 2/3), and a
place that can't bridge still binds and renders fine — it just gets no pin, which
Fix A already handles. Rate 1 is the one that matters.

Runs over the whole 724-name ambiguous set, then dumps Cushi/Eden/Judah/Joseph.
Opens bible.db read-only; only SELECTs.

Usage (on PythonAnywhere):
    python3 scripts/probe_tipnr_fullset.py
    python3 scripts/probe_tipnr_fullset.py bible.db /path/to/tipnr.txt
"""

import re
import sys
import sqlite3
import urllib.request
from collections import defaultdict, Counter

DB = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else \
    "/home/appssanding720/bible-db/bible.db"
TIPNR_LOCAL = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None

TIPNR_URL = (
    "https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/"
    "Proper%20Nouns/TIPNR%20-%20Translators%20Individualised%20Proper%20Names"
    "%20with%20all%20References%20-%20STEPBible.org%20CC%20BY.txt"
)
PROBE_NAMES = ["cushi", "eden", "judah", "joseph"]

_BOOK_VARIANTS = [
    (1, "gen"), (2, "exo exod"), (3, "lev"), (4, "num"), (5, "deu deut"),
    (6, "jos josh"), (7, "jdg judg"), (8, "rth rut ruth"), (9, "1sa 1sam"),
    (10, "2sa 2sam"), (11, "1ki 1kgs"), (12, "2ki 2kgs"), (13, "1ch 1chr"),
    (14, "2ch 2chr"), (15, "ezr ezra"), (16, "neh"), (17, "est esth"), (18, "job"),
    (19, "psa psalm pss"), (20, "pro prov"), (21, "ecc eccl"), (22, "son sng sos song"),
    (23, "isa"), (24, "jer"), (25, "lam"), (26, "eze ezk ezek"), (27, "dan"),
    (28, "hos"), (29, "joe jol joel"), (30, "amo amos"), (31, "oba obad"),
    (32, "jon jonah"), (33, "mic"), (34, "nah nam nahum"), (35, "hab"), (36, "zep zeph"),
    (37, "hag"), (38, "zec zech"), (39, "mal"), (40, "mat matt"), (41, "mar mrk mark"),
    (42, "luk luke"), (43, "joh jhn john"), (44, "act acts"), (45, "rom"),
    (46, "1co 1cor"), (47, "2co 2cor"), (48, "gal"), (49, "eph"), (50, "php phil"),
    (51, "col"), (52, "1th 1thess"), (53, "2th 2thess"), (54, "1ti 1tim"),
    (55, "2ti 2tim"), (56, "tit titus"), (57, "phm phlm"), (58, "heb"),
    (59, "jas james"), (60, "1pe 1pet"), (61, "2pe 2pet"), (62, "1jn 1jo 1john"),
    (63, "2jn 2jo"), (64, "3jn 3jo"), (65, "jud jude"), (66, "rev"),
]
BOOKNUM = {}
for _n, _abbrs in _BOOK_VARIANTS:
    for _a in _abbrs.split():
        BOOKNUM[_a] = _n


def norm_name(s):
    if not s:
        return ""
    return re.sub(r"[\s,.:;!?'\"–\-]+$", "", s.strip()).lower()


def norm_base(s):
    m = re.match(r"^([GH])0*(\d+)", (s or "").strip())
    return f"{m.group(1)}{int(m.group(2))}" if m else ""


def parse_ref(tok):
    tok = re.sub(r"^LXX\s*", "", tok.strip())
    if not tok:
        return None
    parts = tok.split(".")
    if len(parts) < 3:
        return None
    book = BOOKNUM.get(parts[0].strip().lower())
    if book is None:
        return None
    cm = re.match(r"\d+", parts[1].strip())
    vm = re.match(r"\d+", parts[2].strip())
    if not cm or not vm:
        return None
    return (book, int(cm.group()), int(vm.group()))


def parse_tipnr(lines):
    """Each entity keeps: headword name, ALL spellings (headword + sub UniqueNames
    + ESV/KJV/NIV translated-name tokens), ALL base Strong's, section, parents/
    offspring names, and the exhaustive reference set."""
    ents = []
    section = "other"
    cur = None

    def close(c):
        if c:
            ents.append(c)

    for line in lines:
        if line.startswith("$=========="):
            close(cur); cur = None
            low = line.lower()
            section = "person" if "person" in low else "place" if "place" in low else "other"
            continue
        if not line.strip():
            continue
        stripped = line.lstrip()
        if stripped[:1] in ("=", "‖", "#", "*", "@") or stripped.startswith("UnifiedName") \
                or stripped.startswith("UniqueName"):
            continue
        is_sub = line[0] in (" ", "\t") or stripped.startswith("–")
        parts = line.split("\t")

        if not is_sub:
            close(cur); cur = None
            f0 = parts[0].strip()
            if "@" not in f0:
                continue
            head = norm_name(f0.split("@")[0])
            if not head:
                continue
            cur = {
                "head": head, "uniq": f0.split("=")[0].strip(), "section": section,
                "spellings": {head}, "bases": set(), "refs": set(),
                "parents": parts[2].strip() if len(parts) > 2 else "",
                "offspring": parts[5].strip() if len(parts) > 5 else "",
            }
            b = norm_base(f0.split("=", 1)[1]) if "=" in f0 else ""
            if b:
                cur["bases"].add(b)
        else:
            if not cur:
                continue
            # sub-record: col1 = UniqueName (AltName@..), col2 = dStrong«eStrong,
            # col3 = translated name (ESV,KJV,NIV). Mine spellings + base + refs.
            if len(parts) > 1 and "@" in parts[1]:
                cur["spellings"].add(norm_name(parts[1].split("@")[0]))
            if len(parts) > 2 and "«" in parts[2]:
                b = norm_base(parts[2].split("«")[0])
                if b:
                    cur["bases"].add(b)
            if len(parts) > 3 and parts[3].strip():
                for tok in re.split(r"[,/()]", parts[3]):
                    w = norm_name(tok)
                    if w and re.match(r"^[a-z][a-z' -]+$", w):
                        cur["spellings"].add(w)
            ref_blob = None
            for i, f in enumerate(parts):
                if "reference=" in f:
                    ref_blob = parts[i + 1] if i + 1 < len(parts) else f.split("reference=", 1)[1]
                    break
            if ref_blob:
                for tok in ref_blob.split(";"):
                    r = parse_ref(tok)
                    if r:
                        cur["refs"].add(r)
    close(cur)
    return ents


def main():
    print(f"READ-ONLY TIPNR full-set probe -> {DB}\n")
    if TIPNR_LOCAL:
        lines = open(TIPNR_LOCAL, encoding="utf-8-sig").read().splitlines()
        print(f"TIPNR: {TIPNR_LOCAL} ({len(lines):,} lines)")
    else:
        print("Downloading TIPNR...")
        with urllib.request.urlopen(TIPNR_URL) as r:
            lines = r.read().decode("utf-8-sig").splitlines()
        print(f"  {len(lines):,} lines")

    ents = parse_tipnr(lines)
    name_idx = defaultdict(set)     # spelling -> {entity idx}
    base_idx = defaultdict(set)     # base strongs -> {entity idx}
    chap_idx = defaultdict(set)     # entity idx -> {(book,chap)}  for soft check
    for i, e in enumerate(ents):
        for s in e["spellings"]:
            name_idx[s].add(i)
        for b in e["bases"]:
            base_idx[b].add(i)
        chap_idx[i] = {(bk, ch) for (bk, ch, _v) in e["refs"]}
    print(f"Parsed {len(ents):,} entities\n")

    def classify(name, bk, ch, vs, base):
        """-> one of clean / variant / strongs / soft / hard."""
        V = (bk, ch, vs)
        name_cands = name_idx.get(name, set())
        base_cands = base_idx.get(base, set()) if base else set()
        # bound by NAME (verse in a same-name entity)
        nm_hit = [i for i in name_cands if V in ents[i]["refs"]]
        if nm_hit:
            return "clean" if any(ents[i]["head"] == name for i in nm_hit) else "variant"
        # bound by base STRONG'S across headwords (the Cushi->Cush case)
        if any(V in ents[i]["refs"] for i in base_cands):
            return "strongs"
        # soft: a candidate entity has refs in the same book+chapter (offset)
        if any((bk, ch) in chap_idx[i] for i in (name_cands | base_cands)):
            return "soft"
        return "hard"

    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    # ── Ambiguous name set (mirrors audit_entity_resolution: >1 person, >1 place,
    #    or both), intersected with names that occur in the text ────────────────
    place_ids, person_ids = defaultdict(set), defaultdict(set)
    for r in conn.execute("SELECT place_id, name FROM metav_places WHERE name IS NOT NULL"):
        place_ids[norm_name(r["name"])].add(r["place_id"])
    for r in conn.execute("SELECT place_id, alias FROM metav_place_aliases WHERE alias IS NOT NULL"):
        place_ids[norm_name(r["alias"])].add(r["place_id"])
    for r in conn.execute("SELECT person_id, name FROM metav_people WHERE name IS NOT NULL"):
        person_ids[norm_name(r["name"])].add(r["person_id"])
    for r in conn.execute("SELECT person_id, alias FROM metav_people_aliases WHERE alias IS NOT NULL"):
        person_ids[norm_name(r["alias"])].add(r["person_id"])
    place_ids.pop("", None); person_ids.pop("", None)
    ambiguous = ({n for n, ids in place_ids.items() if len(ids) > 1}
                 | {n for n, ids in person_ids.items() if len(ids) > 1}
                 | {n for n in place_ids if n in person_ids})

    has_pn = "is_pn" in {r[1] for r in conn.execute("PRAGMA table_info(words)")}
    pn_where = "w.is_pn = 1" if has_pn else "w.strongs_base = '*'"
    occ_rows = conn.execute(f"""
        SELECT v.book AS book, v.chapter AS ch, v.verse AS vs,
               COALESCE(NULLIF(w.english_head,''), w.english) AS label,
               w.strongs_base AS base
        FROM words w JOIN verses v ON v.id = w.verse_id
        WHERE {pn_where}
          AND COALESCE(NULLIF(w.english_head,''), w.english) IS NOT NULL
          AND COALESCE(NULLIF(w.english_head,''), w.english) != ''
    """).fetchall()

    # ── RATE 1 — run the binder over EVERY occurring proper-noun name, split
    #    into the AMBIGUOUS set (what C binds) and the UNAMBIGUOUS set (what C
    #    fast-paths on name only). The unambiguous bind rate is the B-vs-C decider:
    #    if it's ~as good as the ambiguous set, B (bind everyone, name-path as the
    #    fallback) regresses nobody and deletes C's scoping machinery. The
    #    unambiguous set is split again: names WITH a metaV row (a working name-card
    #    -> a bind miss is a regression risk) vs names with NO metaV row (today they
    #    get a bare AI blurb -> binding is pure upside, no card to regress). ─────
    G = {k: defaultdict(int) for k in ("amb", "unamb", "unamb_meta", "unamb_nometa")}
    per_name = defaultdict(lambda: defaultdict(int))
    names_seen = {"amb": set(), "unamb": set()}
    for r in occ_rows:
        nm = norm_name(r["label"])
        if not nm:
            continue
        grp = "amb" if nm in ambiguous else "unamb"
        names_seen[grp].add(nm)
        bk = BOOKNUM.get((r["book"] or "").lower())
        cat = "hard" if bk is None else classify(nm, bk, r["ch"], r["vs"], norm_base(r["base"]))
        G[grp][cat] += 1
        per_name[nm][cat] += 1
        if grp == "unamb":
            G["unamb_nometa" if (nm not in person_ids and nm not in place_ids)
              else "unamb_meta"][cat] += 1

    def report(title, b):
        tot = sum(b.values())
        print("=" * 72)
        print(title)
        if not tot:
            print("  (no occurrences)"); return
        bound = b["clean"] + b["variant"] + b["strongs"]
        print(f"  occurrences                           : {tot:,}")
        print(f"  BOUND                                 : {bound:,}  ({100*bound/tot:.1f}%)")
        print(f"     clean / variant / strongs(by #)    : {b['clean']:,} / {b['variant']:,} / {b['strongs']:,}")
        print(f"  soft miss (versification/locality)    : {b['soft']:,}  ({100*b['soft']/tot:.1f}%)")
        print(f"  HARD unbindable                       : {b['hard']:,}  ({100*b['hard']/tot:.1f}%)")

    report(f"RATE 1 — AMBIGUOUS set ({len(names_seen['amb']):,} names) — what C binds",
           G["amb"])
    report(f"RATE 1 — UNAMBIGUOUS set ({len(names_seen['unamb']):,} names) — *** the B-vs-C decider ***",
           G["unamb"])
    report("   - unambiguous WITH a metaV row (regression-risk group if bind misses)",
           G["unamb_meta"])
    report("   - unambiguous with NO metaV row (today = bare AI blurb; binding = upside)",
           G["unamb_nometa"])

    # ── RATE 2 — people bridge (relationship-keyed) over ambiguous persons ───
    def rel_names(pid):
        return {(x["name"] or "").lower() for x in conn.execute(
            "SELECT p.name FROM metav_people_relationships r "
            "JOIN metav_people p ON p.person_id=r.related_to WHERE r.person_id=?", (pid,))}

    amb_person_ents = [e for e in ents if e["section"] == "person" and e["head"] in ambiguous]
    p_unique = p_norel = p_nomatch = p_multi = 0
    for e in amb_person_ents:
        R = set()
        for blob in (e["parents"], e["offspring"]):
            for tok in re.split(r"[,+]", blob):
                nm = norm_name(tok.split("@")[0])
                if nm:
                    R.add(nm)
        if not R:
            p_norel += 1; continue
        rows = conn.execute("SELECT person_id FROM metav_people WHERE name=? COLLATE NOCASE",
                            (e["head"],)).fetchall()
        hits = [r["person_id"] for r in rows if R & rel_names(r["person_id"])]
        if len(hits) == 1:
            p_unique += 1
        elif len(hits) == 0:
            p_nomatch += 1
        else:
            p_multi += 1
    npe = len(amb_person_ents) or 1
    print("\n" + "=" * 72)
    print(f"RATE 2 — TIPNR person -> metaV person bridge (relationship-keyed)")
    print(f"  ambiguous-set TIPNR person entities   : {len(amb_person_ents):,}")
    print(f"  bridged to a UNIQUE metaV row         : {p_unique:,}  ({100*p_unique/npe:.1f}%)")
    print(f"  could not bridge — entity has no kin  : {p_norel:,}")
    print(f"  could not bridge — no metaV match     : {p_nomatch:,}")
    print(f"  ambiguous bridge (>1 metaV row)       : {p_multi:,}")

    # ── RATE 3 — places: do they even have a usable metaV map row? ───────────
    amb_place_names = {e["head"] for e in ents if e["section"] == "place" and e["head"] in ambiguous}
    pl_withmap = pl_rowonly = pl_none = 0
    for nm in amb_place_names:
        rows = conn.execute("""
            SELECT lat, lon FROM metav_places WHERE name=? COLLATE NOCASE
            UNION SELECT p.lat, p.lon FROM metav_places p
              JOIN metav_place_aliases a ON a.place_id=p.place_id WHERE a.alias=? COLLATE NOCASE
        """, (nm, nm)).fetchall()
        if not rows:
            pl_none += 1
        elif any(r["lat"] is not None and r["lon"] is not None for r in rows):
            pl_withmap += 1
        else:
            pl_rowonly += 1
    npl = len(amb_place_names) or 1
    print("\n" + "=" * 72)
    print(f"RATE 3 — TIPNR place -> metaV place (name-only; coords coverage)")
    print(f"  ambiguous-set TIPNR place names       : {len(amb_place_names):,}")
    print(f"  have a metaV place row WITH coords    : {pl_withmap:,}  ({100*pl_withmap/npl:.1f}%)")
    print(f"  metaV row exists but NO coords        : {pl_rowonly:,}")
    print(f"  no metaV place row at all             : {pl_none:,}")

    # ── 4-name dump ─────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("FOUR-NAME DUMP (bucket split + bridges)")
    for nm in PROBE_NAMES:
        d = per_name.get(nm, {})
        tot = sum(d.values())
        print(f"\n  {nm}  (occurrences={tot})")
        print(f"     clean={d.get('clean',0)} variant={d.get('variant',0)} "
              f"strongs/headword-catch={d.get('strongs',0)} "
              f"versification(soft)={d.get('soft',0)} hard={d.get('hard',0)}")

    # ── NUMBER-DISAGREEMENT + CORROBORATION (over the BOUND set) ─────────────
    # How is each bound occurrence supported? name+verse is solid (the stored
    # number is just metadata there); number+verse-ONLY rests on the stored
    # Strong's, which is first-wins-polluted -> the fragile binds. We MEASURE the
    # pollution on the name+verse binds (true entity known) and read that rate
    # across the number-only binds as the confident-wrong risk.
    nv = nv_disagree = nv_hasnum = 0
    num_only = 0
    nv_nm = nv_dis_nm = numonly_nm = 0      # restricted to the NO-metaV tier
    for r in occ_rows:
        nm = norm_name(r["label"])
        if not nm:
            continue
        bk = BOOKNUM.get((r["book"] or "").lower())
        if bk is None:
            continue
        V = (bk, r["ch"], r["vs"])
        B = norm_base(r["base"])
        nometa = (nm not in person_ids and nm not in place_ids)
        name_hits = [i for i in name_idx.get(nm, set()) if V in ents[i]["refs"]]
        if name_hits:
            nv += 1
            if nometa:
                nv_nm += 1
            if B:
                nv_hasnum += 1
                true_bases = set().union(*(ents[i]["bases"] for i in name_hits))
                if B not in true_bases:
                    nv_disagree += 1
                    if nometa:
                        nv_dis_nm += 1
        elif B and any(V in ents[i]["refs"] for i in base_idx.get(B, set())):
            num_only += 1
            if nometa:
                numonly_nm += 1
    print("\n" + "=" * 72)
    print("NUMBER-DISAGREEMENT + CORROBORATION (bound occurrences)")
    print(f"  name+verse binds (solid; number is metadata): {nv:,}")
    print(f"     stored number DISAGREES with that entity : {nv_disagree:,}"
          + (f"  ({100*nv_disagree/nv_hasnum:.1f}% of {nv_hasnum:,} that carry a number)"
             if nv_hasnum else ""))
    print(f"  number+verse-ONLY binds (no name link)      : {num_only:,}  <- rest on the polluted number")
    if nv_hasnum:
        rate = nv_disagree / nv_hasnum
        print(f"  -> est. confident-wrong among those         : ~{num_only*rate:,.0f}"
              f"  (number-only x pollution {100*rate:.1f}%)")
    print(f"  NO-metaV tier: name+verse {nv_nm:,} (real) vs number-only {numonly_nm:,} (number-reliant)"
          + (f"; pollution {100*nv_dis_nm/nv_nm:.1f}%" if nv_nm else ""))

    # ── CUSHI 2Sa RUNNER — Workstream-2 proof ───────────────────────────────
    # Descent into the – Group sub-record already works; the floor cause is the
    # stored NUMBER (not H3569) + the surface "Cushi" not matching Cush's "Cushite".
    print("\n" + "=" * 72)
    print("CUSHI 2Sa RUNNER — Workstream-2 proof (cause of the 6 hard misses)")
    cush = next((e for e in ents if e["head"] == "cush" and e["section"] == "place"), None)
    print(f"  Cush@Gen.2.13 carries 2Sa.18.21 (Group descent works)? "
          f"{bool(cush and (10, 18, 21) in cush['refs'])}")
    print(f"  Cush bases={sorted(cush['bases']) if cush else '-'}   "
          f"'cushi' among Cush spellings? {('cushi' in cush['spellings']) if cush else '-'}")
    for r in conn.execute(f"""
            SELECT v.chapter AS ch, v.verse AS vs, w.english_head AS h, w.strongs_base AS b
            FROM words w JOIN verses v ON v.id = w.verse_id
            WHERE {pn_where} AND v.book='2Sa' AND lower(w.english_head) LIKE 'cushi%'
            ORDER BY v.chapter, v.verse""").fetchall():
        reaches = bool(cush and norm_base(r["b"]) in cush["bases"])
        print(f"     2Sa {r['ch']}:{r['vs']}  head={r['h']!r}  stored={r['b']!r}  "
              f"reaches Cush by #? {reaches}")
    # WS2 add: footprint of H3570 — proves the correction must target the 6 2Sa
    # slots BY VERSE, not a global number swap (Jer 36:14 Cushi is correctly H3570).
    n3570 = conn.execute(f"""SELECT v.book AS book, COUNT(*) AS c
        FROM words w JOIN verses v ON v.id=w.verse_id
        WHERE {pn_where} AND w.strongs_base='H3570' GROUP BY v.book""").fetchall()
    print(f"  H3570 footprint (number we'd correct FROM): "
          + (", ".join(f"{r['book']}={r['c']}" for r in n3570) or "none"))
    print("  -> fix the 6 2Sa slots BY VERSE; a global H3570->H3569 swap would clobber Jer.")

    # ── WS1 — PER-CHAPTER DOCUMENTED versification map ──────────────────────
    # DERIVE the offset from documented Hebrew/Greek-vs-English differences only;
    # the deltas merely VALIDATE (a documented remap must LAND on a same-name
    # entity's ref to count). A rule encoded wrong simply won't land -> floors,
    # never a false recovery. Everything with no documented rule floors as the
    # 'referent-known, not-named' class. Documented rules (verified, not recalled):
    #   Psa  : superscription -> body verse is +1 vs English (data: 121/123 at -1).
    #   Num  : English 16:36-50 = Hebrew 17:1-15  (Korah chapters).
    #   Mal  : English 4:1-6    = Hebrew 3:19-24.
    # Lev / Est carry NO clean verse-offset rule (Esther's diffs are content
    # additions, not a shift) -> floored, as directed.
    def doc_remaps(book, ch, vs):
        out = []                                   # (esv_ch, esv_vs, rule)
        if book == "Psa":
            out.append((ch, vs + 1, "Psa:superscription"))
        elif book == "Num":
            if ch == 17 and vs <= 15:  out.append((16, vs + 35, "Num16/17"))
            elif ch == 17:             out.append((17, vs - 15, "Num16/17"))
        elif book == "Mal":
            if ch == 3 and vs >= 19:   out.append((4, vs - 18, "Mal3/4"))
        return out

    recovered = defaultdict(int)                   # rule -> count
    floored_total = 0
    floored_deltas = defaultdict(list)             # (book,ch) -> [nearest same-ch delta]
    for r in occ_rows:
        nm = norm_name(r["label"])
        if not nm:
            continue
        bk = BOOKNUM.get((r["book"] or "").lower())
        if bk is None:
            continue
        V = (bk, r["ch"], r["vs"])
        B = norm_base(r["base"])
        if [i for i in name_idx.get(nm, set()) if V in ents[i]["refs"]]:
            continue                               # name+verse bound
        if B and any(V in ents[i]["refs"] for i in base_idx.get(B, set())):
            continue                               # number+verse bound
        ncands = name_idx.get(nm, set())
        hit = next((rule for (ec, ev, rule) in doc_remaps(r["book"], r["ch"], r["vs"])
                    if any((bk, ec, ev) in ents[i]["refs"] for i in ncands)), None)
        if hit:
            recovered[hit] += 1
            continue
        floored_total += 1
        cvs = [v2 for i in ncands for (b2, c2, v2) in ents[i]["refs"]
               if b2 == bk and c2 == r["ch"]]
        if cvs:
            floored_deltas[(r["book"], r["ch"])].append(
                r["vs"] - min(cvs, key=lambda x: abs(x - r["vs"])))

    print("\n" + "=" * 72)
    print("WS1 — PER-CHAPTER DOCUMENTED MAP (offset-recoverable vs floor)")
    print(f"  offset-recoverable (documented + landed): {sum(recovered.values()):,}")
    for rule, n in sorted(recovered.items(), key=lambda kv: -kv[1]):
        print(f"     {rule:22} {n:5}")
    print(f"  floored ('referent-known' class)        : {floored_total:,}")
    print("  Lev / Est: no documented offset rule -> floored (as directed).")
    # Safety net: a FLOORED chapter with a consistent non-zero delta may be a hidden
    # shift. FLAG it for documented-rule lookup — never auto-recover (that's fitting).
    flags = []
    for (book, ch), ds in floored_deltas.items():
        if len(ds) >= 3:
            md, mn = Counter(ds).most_common(1)[0]
            if md != 0 and mn / len(ds) >= 0.6:
                flags.append((mn, len(ds), book, ch, md))
    if flags:
        print("  --- hidden-offset FLAGS (verify vs documented table, don't auto-add) ---")
        for mn, tot, book, ch, md in sorted(flags, reverse=True)[:15]:
            print(f"     {book} {ch}: delta {md:+d} on {mn}/{tot} floored misses")
    else:
        print("  no floored chapter shows a consistent hidden offset.")

    # ── WS3 — residual dump: number-only binds (suspicion-ranked) + ordered-multi ──
    nv_slots = defaultdict(int)            # (name, verse) -> #word-slots of that name
    for r in occ_rows:
        nm = norm_name(r["label"])
        bk = BOOKNUM.get((r["book"] or "").lower())
        if nm and bk is not None:
            nv_slots[(nm, (bk, r["ch"], r["vs"]))] += 1

    numonly, ordmulti = [], []
    for r in occ_rows:
        nm = norm_name(r["label"])
        if not nm:
            continue
        bk = BOOKNUM.get((r["book"] or "").lower())
        if bk is None:
            continue
        V = (bk, r["ch"], r["vs"])
        B = norm_base(r["base"])
        nh = [i for i in name_idx.get(nm, set()) if V in ents[i]["refs"]]
        if nh:
            if len(nh) >= 2 and nv_slots[(nm, V)] == len(nh):
                ordmulti.append((nm, r["book"], r["ch"], r["vs"],
                                 sorted({ents[i]["head"] for i in nh})))
            continue
        if B:
            bh = [i for i in base_idx.get(B, set()) if V in ents[i]["refs"]]
            if bh:
                heads = sorted({ents[i]["head"] for i in bh})
                shared = len(base_idx.get(B, set())) >= 2
                nostem = all(h[:3] != nm[:3] for h in heads)
                numonly.append((nm, r["book"], r["ch"], r["vs"], B, heads, shared, nostem))

    flagged = [x for x in numonly if x[6] or x[7]]
    print("\n" + "=" * 72)
    print("WS3 — RESIDUAL DUMP (the binds resting on the polluted number)")
    print(f"  number-only binds total                : {len(numonly):,}")
    print(f"  flagged (shared-# OR no-stem) HAND-CHECK: {len(flagged):,}")
    print(f"  ordered-multi binds (positional) HOT    : {len(ordmulti):,}")
    print("  --- flagged number-only (first 30) ---")
    for nm, bk, ch, vs, B, heads, shared, nostem in flagged[:30]:
        fl = " ".join([t for t, on in (("shared#", shared), ("no-stem", nostem)) if on])
        print(f"     {nm:14} {bk} {ch}:{vs:<3} #{B:6} -> {heads}  [{fl}]")
    if ordmulti:
        print("  --- ordered-multi HOT (first 15) ---")
        for nm, bk, ch, vs, heads in ordmulti[:15]:
            print(f"     {nm:14} {bk} {ch}:{vs:<3} -> {heads}")

    conn.close()
    print("\nDone. (read-only — nothing was changed)")


if __name__ == "__main__":
    main()
