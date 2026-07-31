#!/usr/bin/env python3
"""build_pn_greek_identity.py — R-2 stage 1: Greek identity ADDED ALONGSIDE Hebrew.

For every ABP proper-noun word (is_pn=1) computes a GREEK identity per the ruled design
(docs/DESIGN_greek_name_identity.md), layered:
  abp-tag    the word's own strongs_base is already a G-number (mostly NT names)
  tipnr      the word's TIPNR entity carries a Greek number (renderable via step_lexicon)
  lemma-only no Greek number in any scheme; the word's own Greek lemma is the identity
             and the card will show the honest no-number state (Q3)

Stage-1 contract: writes ONLY its own table `pn_greek_identity` keyed (verse_id,
position); words/verses untouched; Hebrew strongs_base stays authoritative and is
snapshotted per word as the future cross-reference (Q2 side-table ruling). No live
code reads the table until the stage-2 flip.

Entity resolution reuses the PRODUCTION paths: pn_binding rows (the binder's verdicts)
first, then import_tipnr's parsed lookup for unbound words — never a re-implementation.

Usage (PA):
  python3 scripts/build_pn_greek_identity.py ~/bible-db/bible_test.db          # dry-run
  python3 scripts/build_pn_greek_identity.py ~/bible-db/bible_test.db --apply
"""
import os
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))
import import_tipnr                      # parse_tipnr (the loader-fixed roster)
import entity_resolution as er           # norm_name (the binder's normalizer)

from build_abp_surface import ABBREV_TO_SLUG   # the ONE ABP-abbrev -> scrape-slug map

DB = next((a for a in sys.argv[1:] if not a.startswith("--")),
          os.path.expanduser("~/bible-db/bible.db"))
APPLY = "--apply" in sys.argv
BH = next((sys.argv[i + 1] for i, a in enumerate(sys.argv)
           if a == "--bh" and i + 1 < len(sys.argv)),
          os.path.expanduser("~/bible-db/bh_scrape.db"))


# ── Greek-header discipline (DRILL_greek_header_backfill.md, JP-ruled 2026-07-30) ──

# = audit_order_mismatch.is_nominative VERBATIM (that file executes at import time so
# it cannot be imported here; if a third user appears, extract to a shared module).
def is_nominative(morph):
    m = (morph or "").strip()
    if not m:
        return False
    if "." in m:
        return m.split(".", 1)[1].lstrip("123")[:1] == "N"
    parts = m.split("-")
    return len(parts) >= 2 and parts[1].lstrip("123")[:1] == "N"


# Stray-breathing repair (reviewer-final fix shape): a value stored as a DETACHED
# mark + space ("΄ Αδερ") becomes the combined rough breathing on the first vowel,
# NFC-composed. Applies to stored header values only — transliterations and the
# abp_surface table are untouched (the gate's byte-unchanged post-check).
_DETACHED_MARKS = "΄´ʼʽʹ᾽᾿῾‘’'`"
# Live-data identification 2026-07-30: the stray prefix is U+0384 (Greek tonos)
# + U+00A0 (non-breaking space). The first repair pass required a plain space
# and fixed 0 rows; the separator now accepts both space kinds.
_SEPARATORS = "  "
_GREEK_VOWELS = "αεηιουωΑΕΗΙΟΥΩ"

def fix_detached_breathing(s):
    if not s or len(s) < 3 or s[0] not in _DETACHED_MARKS or s[1] not in _SEPARATORS:
        return s
    rest = s[2:]
    for i, ch in enumerate(rest):
        if ch in _GREEK_VOWELS:
            return unicodedata.normalize("NFC", rest[:i + 1] + "̔" + rest[i + 1:])
    return rest


def accent_fold(s):
    """Comparison key only (display always keeps ABP bytes): lowercase, accents off."""
    return "".join(ch for ch in unicodedata.normalize("NFD", (s or "").lower())
                   if not unicodedata.combining(ch))


# ── Strict name-match inheritance (JP-signed predicate 2026-07-31,
# docs/tickets/PREDICATE_g707_name_match.md — the G707 fix) ──────────────────
# TIPNR files multi-named entities as one record but puts each number on its own
# row WITH the printed names that number belongs to. A slot may inherit a Greek
# number ONLY if its own printed name is one TIPNR attaches to that number.

_SUMMARY_STRONG = re.compile(r'<strong="(G\d+)[^"]*">([^<]+)</strong>')

def parse_number_forms(lines):
    """Per record: which printed names each GREEK number attaches to.
    Sources: the record's own head line, each '– Named'/'– Greek'/'– (same
    form...)' row (number in col 2, names in col 1's alt-part and col 3's
    version list; '[ ]' = the record's head name), and the summary's
    <strong="G...">Name</strong> pairs. '– Total' rows are EXCLUDED — they pool
    every name with every number, which is the conflation being fixed.
    Returns (ent_forms: uniq -> {G -> names}, glob_forms: G -> names)."""
    ent_forms, glob_forms = {}, defaultdict(set)
    cur_uniq, head = None, None
    excluded = False

    _STOP = {"of", "the", "and", "a", "an", "or"}

    def attach(g, name):
        # TIPNR decorates some names ("Sinai_Mount", "(Mount )Sinai",
        # "Sergius/ Paulus") — clean to plain words, and for a multi-word form
        # also attach each real word so the single-word slot label still
        # matches ("Sinai" ∈ "Mount Sinai"). Checker-caught 2026-07-31: without
        # this, Sinai lost its own G4614.
        if not (cur_uniq and g):
            return
        cleaned = re.sub(r"[()_/]", " ", name)
        names = {er.norm_name(cleaned)}
        toks = [t for t in cleaned.split() if er.norm_name(t) not in _STOP]
        if len(toks) > 1:
            names |= {er.norm_name(t) for t in toks if len(t) > 2}
        for nm in names:
            if nm:
                ent_forms.setdefault(cur_uniq, {}).setdefault(g, set()).add(nm)
                glob_forms[g].add(nm)

    for line in lines:
        if line.startswith("$=========="):
            excluded = "excluded" in line.lower()
            cur_uniq = None
            continue
        if not line.strip() or excluded:
            continue
        stripped = line.lstrip()
        if stripped[:1] in ("=", "‖", "#", "*", "@") \
                or stripped.startswith(("UnifiedName", "UniqueName")):
            continue
        is_sub = line[0] in (" ", "\t") or stripped.startswith("–")
        parts = line.split("\t")
        if not is_sub:
            f0 = parts[0].strip()
            head_nm = er.norm_name(f0.split("@")[0]) if "@" in f0 else ""
            if not head_nm or " " in head_nm:
                cur_uniq = None
                continue
            cur_uniq, head = f0.split("=")[0].strip(), head_nm
            b = er.norm_base(f0.split("=", 1)[1]) if "=" in f0 else ""
            if b.startswith("G"):
                attach(b, head)
            if len(parts) > 7:
                for g, nm in _SUMMARY_STRONG.findall(parts[7]):
                    attach(er.norm_base(g), nm)
        else:
            if not cur_uniq or stripped.startswith("– Total"):
                continue
            g = er.norm_base(parts[2].split("«")[0]) \
                if len(parts) > 2 and "«" in parts[2] else ""
            if not g.startswith("G"):
                continue
            if len(parts) > 1 and "@" in parts[1]:
                attach(g, parts[1].split("@")[0].split("|")[0])
            if len(parts) > 3 and parts[3].strip():
                for tok in parts[3].split(";"):
                    nmtok = tok.split("=")[0].strip()
                    if nmtok in ("[ ]", "[]"):
                        attach(g, head)
                    elif re.match(r"^[A-Za-z]", nmtok):
                        attach(g, nmtok)
    return ent_forms, glob_forms


_MK_CACHE = {}

def _match_keys(name):
    """A name's comparison keys: norm + the binder's variant/alias expansion +
    compact (hyphen/space-stripped) copies, all accent-folded."""
    if name in _MK_CACHE:
        return _MK_CACHE[name]
    n = er.norm_name(re.sub(r"[()_/]", " ", name)).strip()
    ks = {n} | er.name_variants(n)
    ks |= {k.replace("-", "").replace(" ", "") for k in set(ks)}
    r = {accent_fold(k) for k in ks if k}
    _MK_CACHE[name] = r
    return r


def name_matches(slot_name, forms):
    """True when the slot's printed name is one TIPNR attaches to the number."""
    sk = _match_keys(slot_name)
    return any(sk & _match_keys(f) for f in forms)


def _name_token(s):
    """A word's name label reduced to a bare lowercase token ('of Raamah,' -> 'raamah')."""
    s = re.sub(r"[^a-z' -]", " ", (s or "").lower())
    toks = [t for t in s.split() if t not in
            ("of", "the", "and", "to", "in", "for", "with", "a", "an", "o")]
    return toks[-1] if toks else ""


def main():
    print(f"{'[APPLY] ' if APPLY else '[DRY-RUN] '}build_pn_greek_identity -> {DB}\n")

    tipnr_lines = open(os.path.join(_HERE, "..", "tipnr", "TIPNR.txt"),
                       encoding="utf-8-sig").read().splitlines()
    lookup, _ = import_tipnr.parse_tipnr(tipnr_lines)

    # Entity -> its own Greek number, from the binder's parse (sub-records included —
    # import_tipnr's lookup deliberately carries main-line numbers only, which misses
    # the Greek sub-record numbers OT names carry, incl. the STEP-extended ones).
    # Rule: exactly ONE Greek base on the entity -> that's its Greek identity; two or
    # more -> no guess (wrong > missing), the word falls to the lemma-only state.
    ents = er.parse_tipnr(tipnr_lines)
    ent_g, multi_g = {}, 0
    for e in ents:
        gs = sorted(b for b in e["bases"] if b.startswith("G"))
        if len(gs) == 1:
            ent_g[e["uniq"]] = gs[0]
        elif len(gs) > 1:
            multi_g += 1
    print(f"entities with exactly one Greek number: {len(ent_g):,} "
          f"(multi-Greek entities, no guess: {multi_g:,})")

    ent_forms, glob_forms = parse_number_forms(tipnr_lines)
    print(f"per-number name rows parsed: {len(glob_forms):,} Greek numbers "
          f"across {len(ent_forms):,} records (strict name-match gate ON)")

    # UNBOUND words (incl. the binder's deliberate name-path tier: David, Moses...):
    # the name's own Greek number, IF every entity carrying that spelling agrees on
    # exactly one (David -> 1 entity, G1138; Mary -> 6 entities, all G3137). Mixed or
    # absent -> no guess. (The G1 control caught the gap: import_tipnr's lookup holds
    # main-line numbers only, and David's G1138 sits on a sub-record.)
    name_idx, _bi, _ci = er.build_indexes(ents)
    name_g = {}
    for nm_key, idxs in name_idx.items():
        union = {g for i in idxs for g in ents[i]["bases"] if g.startswith("G")}
        if len(union) == 1:
            name_g[nm_key] = next(iter(union))
    print(f"name spellings with one agreed Greek number: {len(name_g):,}")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA busy_timeout=10000")

    have_binding = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE name='pn_binding'").fetchone()[0]
    binds = {}
    if have_binding:
        # keyed exactly like the binder keys its rows: (book#, ch, vs, norm name);
        # value = the bound entity's uniq (the key into ent_g above).
        for r in conn.execute("SELECT book, chapter, verse, name, entity_uniq "
                              "FROM pn_binding WHERE render=1"):
            binds[(r["book"], r["chapter"], r["verse"], r["name"])] = r["entity_uniq"]
    print(f"pn_binding render rows loaded: {len(binds):,}"
          + ("" if have_binding else "  (table absent — layer 'tipnr' via lookup only)"))

    # The printed-Greek side table is the lemma fallback for name words — words.lemma
    # is mostly blank on proper nouns (the dry-run control that caught this: 26,867
    # 'none' rows on the first pass, 2026-07-24).
    have_surface = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE name='abp_surface'").fetchone()[0]
    surf_join = ("LEFT JOIN abp_surface s ON s.verse_id = w.verse_id "
                 "AND s.position = w.position") if have_surface else ""
    surf_col = "s.form" if have_surface else "NULL"
    words = conn.execute(f"""
        SELECT w.verse_id, w.position, w.strongs_base, w.lemma, w.morph,
               {surf_col} AS surface_form,
               COALESCE(NULLIF(w.english_head,''), w.english) AS label,
               v.book, v.chapter, v.verse
        FROM words w JOIN verses v ON v.id = w.verse_id
        {surf_join}
        WHERE w.is_pn = 1
    """).fetchall()
    print(f"proper-noun words: {len(words):,}\n")

    # Printed-Greek source for name slots: the scrape (bh_words), where a NAME row has
    # a blank number and the Greek form in `greek` (abp_surface skips name slots — the
    # documented 30,126-slot gap; second dry-run control catch, 2026-07-24). Pairing is
    # by the NAME within the verse, never by position (the build splits slots, so
    # positions drift): exactly one name-slot row whose English carries the word's name
    # token, else REFUSE and count.
    scrape = {}
    if os.path.isfile(BH):
        bh = sqlite3.connect(f"file:{BH}?mode=ro", uri=True)
        for b, c, v, greek, english in bh.execute(
                "SELECT book, chapter, verse, greek, english FROM bh_words "
                "WHERE (strongs IS NULL OR strongs='') AND greek IS NOT NULL AND greek != ''"):
            scrape.setdefault((b, c, v), []).append((_name_token(english), greek))
        bh.close()
        print(f"scrape name-slot rows loaded: {sum(len(v) for v in scrape.values()):,} "
              f"across {len(scrape):,} verses")
    else:
        print(f"NOTE: scrape db not found at {BH} — lemma layer limited to words.lemma/abp_surface")

    # (per-verse scrape picking retired 2026-07-30 — the scrape now feeds the
    # per-NAME headword inventory below instead; raw per-verse forms are inflected
    # and may no longer become headers directly, per the JP-ruled discipline.)

    # Candidate-3 (docs/PLAN_r2_c3_rebuild.md): after the retirement rewrite,
    # words.strongs_base no longer carries the Hebrew snapshot (it moved to
    # pn_hebrew_xref) and tipnr-class rows carry their Greek number natively —
    # so a re-run must source Hebrew AND the abp-tag/tipnr distinction from the
    # Q2 home, not re-derive them from the rewritten column (a rewritten G9xxx
    # row misread as native abp-tag would falsify the classification of record).
    # Pre-retirement (table absent): empty map, behavior byte-identical.
    xref = {}
    if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                    "AND name='pn_hebrew_xref'").fetchone():
        for r in conn.execute("SELECT verse_id, position, hebrew_base, class "
                              "FROM pn_hebrew_xref"):
            xref[(r["verse_id"], r["position"])] = (r["hebrew_base"], r["class"])
        print(f"pn_hebrew_xref loaded (post-retirement re-run): {len(xref):,} rows")

    # ── Headword discipline pre-pass (JP-ruled 2026-07-30, DRILL_greek_header_backfill) ─
    # Per NAME, one nominative headword in ABP's own orthography, or nothing:
    #   indeclinable  every attested form BYTE-identical -> that form is the headword
    #   declinable    forms vary -> the nominative-morph occurrences must agree on ONE
    #                 byte-exact form (populated morph only); disagreement or accent
    #                 variance NEVER auto-picks (no majority vote) -> hand table
    #   hand table    scripts/greek_header_nominatives.tsv (pre-registered, ABP-cited)
    #   UNRESOLVED    stays English (fallback is honest; a guessed form is not)
    # Inventory sources: abp_surface + the bh scrape (both ABP's own printed text).
    hand = {}
    hand_path = os.path.join(_HERE, "greek_header_nominatives.tsv")
    if os.path.isfile(hand_path):
        for ln in open(hand_path, encoding="utf-8"):
            if ln.startswith("#") or not ln.strip():
                continue
            nm_h, form_h = ln.rstrip("\n").split("\t")[:2]
            hand[er.norm_name(nm_h)] = form_h
    print(f"hand-table nominatives loaded: {len(hand)}")

    inv = defaultdict(list)          # norm name -> [(form bytes, morph-or-None)]
    _valid_key = re.compile(r"^[a-z]").match   # kills label-fragment leaks (", no")
    for w in words:
        nm = er.norm_name(w["label"] or "")
        if nm and _valid_key(nm) and w["surface_form"]:
            inv[nm].append((fix_detached_breathing(w["surface_form"]), w["morph"]))
    for (b, c, v), slots in scrape.items():
        for tok, greek in slots:
            if tok and _valid_key(tok):
                inv[tok].append((fix_detached_breathing(greek), None))

    _hw_cache = {}
    def headword(nm):
        """-> (form|None, class) for a name; cached."""
        if nm in _hw_cache:
            return _hw_cache[nm]
        occ = inv.get(nm)
        if not occ:
            r = (None, "no-surface")
        else:
            forms = {f for f, _ in occ}
            if len(forms) == 1:
                r = (next(iter(forms)), "indeclinable")
            elif len({accent_fold(f) for f in forms}) == 1:
                r = (hand[nm], "hand-table") if nm in hand else (None, "UNRESOLVED-accent-variance")
            else:
                noms = {f for f, m in occ if m and is_nominative(m)}
                if len(noms) == 1:
                    r = (next(iter(noms)), "declinable-morph")
                elif nm in hand:
                    r = (hand[nm], "hand-table")
                else:
                    r = (None, "UNRESOLVED-nom-disagree" if noms else "UNRESOLVED-no-nominative")
        _hw_cache[nm] = r
        return r

    rows, split = [], {"abp-tag": 0, "tipnr": 0, "lemma-only": 0, "surface": 0, "none": 0}
    excluded_gentilic = 0
    gated = defaultdict(int)         # per-name tally of inheritances the gate refused
    breathing_fixed = {}             # old value -> new value (receipt)

    def norm_lemma(val):
        fixed = fix_detached_breathing(val)
        if val and fixed != val:
            breathing_fixed[val] = fixed
        return fixed
    for w in words:
        base = w["strongs_base"] or ""
        xr = xref.get((w["verse_id"], w["position"]))
        heb = xr[0] if xr else (base if base.startswith("H") else None)
        greek, source = None, None
        lemma = norm_lemma(w["lemma"] or w["surface_form"])  # numbered rows: as before (+breathing fix)
        if base.startswith("G") and xr and xr[1] == "tipnr":
            greek, source = base, "tipnr"         # retirement wrote the served number
        elif base.startswith("G"):
            greek, source = base, "abp-tag"
        else:
            nm = er.norm_name(w["label"] or "")
            bk = er.book_num(w["book"])
            uniq = binds.get((bk, w["chapter"], w["verse"], nm)) if bk is not None else None
            # Candidate numbers in the original preference order, each behind the
            # strict name-match gate: the number only lands if TIPNR attaches it
            # to the slot's own printed name (bound lane checks the entity's own
            # rows; the two fallback lanes check the corpus-wide map).
            cands = []
            if uniq and uniq in ent_g:
                cands.append((ent_g[uniq], ent_forms.get(uniq, {}).get(ent_g[uniq], ())))
            if nm and nm in name_g:                     # unbound word: the name's own number
                cands.append((name_g[nm], glob_forms.get(name_g[nm], ())))
            if nm and lookup.get(nm, {}).get("g"):
                cands.append((lookup[nm]["g"], glob_forms.get(lookup[nm]["g"], ())))
            for g_cand, forms in cands:
                if name_matches(nm, forms):
                    greek, source = g_cand, "tipnr"
                    break
                gated[f"{nm}→{g_cand}"] += 1
            if greek is None:
                if w["lemma"]:
                    lemma = norm_lemma(w["lemma"])   # a REAL dictionary lemma stands
                    source = "lemma-only"
                else:
                    # No number, no dictionary lemma: the DISCIPLINED headword or
                    # nothing (JP pre-rulings 1/2/4). Gentilic-class tokens are
                    # EXCLUDED via the PRODUCTION people-group predicate
                    # (er.is_people_group — never a base-number proxy: the first
                    # dry-run proved 'numberless' sweeps in ~15k legit names).
                    if er.is_people_group(nm) or er.is_people_group(w["label"] or ""):
                        if w["surface_form"]:
                            excluded_gentilic += 1
                        lemma, source = None, "none"
                    else:
                        hw, _cls = headword(nm)
                        if hw:
                            lemma, source = hw, "surface"
                        elif w["surface_form"]:
                            # Ruling (b), JP 2026-07-30: an UNRESOLVED name keeps
                            # today's behavior — the verse's OWN printed form heads
                            # the card (always ABP-attested, never contradicts the
                            # page; per-name uniformity arrives via hand-table rows
                            # incrementally, no deadline).
                            lemma, source = norm_lemma(w["surface_form"]), "lemma-only"
                        else:
                            lemma, source = None, "none"  # no Greek anywhere — English
        split[source] += 1
        rows.append((w["verse_id"], w["position"], greek, lemma, source, heb))

    print("identity split:")
    for k in ("abp-tag", "tipnr", "lemma-only", "surface", "none"):
        print(f"  {k:10} {split[k]:,}")
    print(f"  (gentilic tokens excluded from the surface lane: {excluded_gentilic:,} "
          f"— people-group ruling; breathing-repaired stored values: {len(breathing_fixed):,})")
    print(f"name-match gate refused {sum(gated.values()):,} slot inheritances "
          f"across {len(gated):,} name→number pairs:")
    for pair, n in sorted(gated.items(), key=lambda t: -t[1]):
        print(f"  GATED {pair} ×{n}")
    print()

    # ── RECEIPT (written on EVERY run, before any write): the per-name split +
    # breathing list, for the audit's spot-check (JP-required 2026-07-30).
    receipt = os.path.join(_HERE, "..", "docs", "tickets", "greek_header_split.txt")
    with open(receipt, "w", encoding="utf-8", newline="\n") as f:
        f.write("# greek_header_split.txt — headword-discipline receipt "
                "(generated by build_pn_greek_identity.py; regenerate, don't edit)\n"
                "# name | class | occurrences | chosen headword ('' = stays English) | "
                "morph-tagged count | distinct forms (top 6, ×count)\n")
        for nm in sorted(_hw_cache):
            hw, cls = _hw_cache[nm]
            occ = inv.get(nm, [])
            fc = {}
            for form, _m in occ:
                fc[form] = fc.get(form, 0) + 1
            det = " ".join(f"{form}×{c}" for form, c in
                           sorted(fc.items(), key=lambda t: -t[1])[:6])
            morphn = sum(1 for _f, m in occ if m)
            f.write(f"{nm}|{cls}|{len(occ)}|{hw or ''}|morph:{morphn}|{det}\n")
        f.write("\n# breathing repairs (old -> new), stored header values only:\n")
        for old, new in sorted(breathing_fixed.items()):
            f.write(f"# {old} -> {new}\n")
    n_unres = sum(1 for hw, cls in _hw_cache.values() if cls.startswith("UNRESOLVED"))
    print(f"receipt written: {receipt}  (names classified: {len(_hw_cache):,}, "
          f"UNRESOLVED: {n_unres:,} — candidates for the hand table)")
    print()

    if not APPLY:
        print("Dry-run only — nothing written. Re-run with --apply.")
        return

    conn.execute("DROP TABLE IF EXISTS pn_greek_identity")
    conn.execute("""
        CREATE TABLE pn_greek_identity (
            verse_id      INTEGER NOT NULL,
            position      INTEGER NOT NULL,
            greek_strongs TEXT,      -- 'G1138' / 'G9827' / NULL (lemma-only or none)
            greek_lemma   TEXT,
            source        TEXT NOT NULL,  -- abp-tag | tipnr | lemma-only | none
            hebrew_base   TEXT,      -- the stage-1 stopgap number, frozen as cross-ref
            PRIMARY KEY (verse_id, position)
        )
    """)
    conn.executemany(
        "INSERT INTO pn_greek_identity VALUES (?,?,?,?,?,?)", rows)
    conn.execute("CREATE INDEX idx_pngi_greek ON pn_greek_identity(greek_strongs)")
    conn.execute("CREATE INDEX idx_pngi_heb ON pn_greek_identity(hebrew_base)")
    conn.commit()
    n = conn.execute("SELECT count(*) FROM pn_greek_identity").fetchone()[0]
    print(f"Wrote pn_greek_identity: {n:,} rows.")


if __name__ == "__main__":
    main()
