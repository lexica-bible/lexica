#!/usr/bin/env python3
"""
fix_g1473_gloss.py — repair the residual G1473 pronoun mis-tags surfaced by the
Tier-2 audit (bucket a): slots numbered G1473 (ἐγώ "I", 1st-singular) whose ABP
English gloss is a DIFFERENT person ("he/him/it/them" = 3rd, "you" = 2nd, "we/us"
= 1st-plural). These are the un-fixed tail of the αὐτός→G1473 corruption — the
slots the 2026-06-04 pronoun fix could not confidently align to Rahlfs/TAGNT.

PRINCIPLE: ABP is the primary text, so its OWN gloss decides the PERSON; the
independently-built `morph` column gives CASE + NUMBER. Together they yield the
correct case-split Strong's (the same convention lxx_align produced):
  3rd person  → αὐτός  G846                (every case; lemma αὐτός)
  2nd person  → σύ / ὑμεῖς  (by morph num) (lemma σύ)
  1st plural  → ἡμεῖς        (by morph case)(lemma ἐγώ)
Only G1473 slots whose gloss CONTRADICTS 1st-singular are touched. A gloss of
"I/me/my" (consistent) or a reflexive "-self/-selves" (ambiguous/intensive) is
left untouched. A 1P/2P slot with no parseable morph case+number is SKIPPED
(reported as needs-manual) — never guessed.

Touches ONLY strongs_base, strongs, lemma. morph is left as-is (already correct).
strongs_base stays G-prefixed (invariant preserved); strongs stays bare.

SAFE BY DEFAULT: --dry-run (read-only, mode=ro) unless --apply is given.
Idempotent: re-running after --apply finds 0 contradictions.

COPY-FIRST PROTOCOL (run on PythonAnywhere — bible.db is PA-only):
  cd ~/bible-db
  cp bible.db bible_pre_g1473gloss_$(date +%Y%m%d).db        # rollback point
  python3 scripts/fix_g1473_gloss.py bible.db                # DRY RUN (review!)
  python3 scripts/fix_g1473_gloss.py bible.db --apply        # write
  python3 scripts/health_check.py bible.db                   # expect 0 warnings
  sqlite3 bible.db "SELECT count(*) FROM words WHERE strongs_base GLOB '[0-9]*'"  # 0
  python3 scripts/audit_corpus_tier2.py bible.db --rahlfs ~/LXX-Rahlfs-1935 --tagnt ~/TAGNT_*.txt
  # then: git pull && touch wsgi   (deploy)
"""
import os
import sys
import sqlite3
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lxx_align as L   # _EN_BUCKET, _last_en_word

ARGS = sys.argv[1:]
APPLY = "--apply" in ARGS
DB = next((a for a in ARGS if not a.startswith("--")), "bible.db")

# ── case-split targets (bare Strong's) — the lxx_align convention ─────────────
SU_SING = {"N": "4771", "V": "4771", "G": "4675", "D": "4671", "A": "4571"}   # σύ
SU_PLUR = {"N": "5210", "G": "5216", "D": "5213", "A": "5209"}                # ὑμεῖς
HEMEIS  = {"N": "2249", "G": "2257", "D": "2254", "A": "2248"}                # ἡμεῖς
# lemma collapse convention already in the DB (verified via Tier-1 A1):
LEMMA = {"αὐτός": "αὐτός", "σύ": "σύ", "ἐγώ": "ἐγώ"}


def parse_case_num(morph):
    """(case, number) from a pronoun morph. CATSS dotted 'RP.GS'/'RD.GSM' →
    tail after '.', case=tail[0] num=tail[1]. Robinson 'P-2GS'/'P-1GP' → seg[1],
    strip a leading person digit, then case/number. Returns (case|None, num|None)."""
    if not morph:
        return (None, None)
    m = morph.strip()
    if "." in m:
        tail = m.split(".", 1)[1]
    elif "-" in m:
        seg = m.split("-")
        tail = seg[1] if len(seg) > 1 else ""
        if tail[:1] in "123":
            tail = tail[1:]
    else:
        return (None, None)
    case = tail[0] if tail and tail[0] in "NVGDA" else None
    num = tail[1] if len(tail) > 1 and tail[1] in "SPD" else None
    return (case, num)


def is_pronoun_morph(morph):
    """True if the morph denotes a pronoun (CATSS R*, Robinson P-/F-/S-)."""
    if not morph:
        return None        # unknown
    m = morph.strip()
    if "." in m:
        return m[0] == "R"
    if "-" in m:
        return m[0] in "PFS"
    return m and m[0] in "RPFS"


def target_for(gloss_word, eb, morph):
    """Given an ABP gloss person bucket (eb) that contradicts 1st-singular, plus
    the slot's morph, return (new_base_bare, lemma, note) or (None, None, reason)."""
    case, num = parse_case_num(morph)
    if eb == "3P":                                  # → αὐτός, all cases
        return ("846", "αὐτός", "3P→αὐτός")
    if eb == "2P":                                  # → σύ (sing) / ὑμεῖς (plur)
        if case is None or num is None:
            return (None, None, "2P no-morph-case/num")
        tbl = SU_PLUR if num == "P" else SU_SING
        n = tbl.get(case)
        return (n, "σύ", f"2P→{'ὑμεῖς' if num == 'P' else 'σύ'}") if n else (None, None, "2P bad-case")
    if eb == "1P":                                  # → ἡμεῖς
        if case is None:
            return (None, None, "1P no-morph-case")
        n = HEMEIS.get(case)
        return (n, "ἐγώ", "1P→ἡμεῖς") if n else (None, None, "1P bad-case")
    return (None, None, f"unexpected-bucket:{eb}")


# ── read G1473 slots ──────────────────────────────────────────────────────────
uri = f"file:{DB}?mode=ro" if not APPLY else DB
conn = sqlite3.connect(uri, uri=not APPLY)
conn.row_factory = sqlite3.Row
rows = conn.execute(
    """SELECT w.rowid AS rid, w.strongs_base AS sb, w.morph AS morph, w.english AS eng,
              v.book AS book, v.chapter AS ch, v.verse AS vs
       FROM words w JOIN verses v ON v.id = w.verse_id
       WHERE w.strongs_base = 'G1473'""").fetchall()

total = len(rows)
plan = []                       # (rid, new_base, lemma, note, ref, eng)
skip_consistent = skip_self = skip_nocue = 0
skip_reason = defaultdict(int)  # needs-manual reasons
bucket_count = defaultdict(int) # note -> count
nonpron_morph = 0

for r in rows:
    eng = r["eng"] or ""
    gw = L._last_en_word(eng)
    if gw.endswith("self") or gw.endswith("selves"):
        skip_self += 1
        continue
    eb = L._EN_BUCKET.get(gw)
    if eb is None:
        skip_nocue += 1
        continue
    if eb == "1S":                                  # consistent with ἐγώ → leave
        skip_consistent += 1
        continue
    # contradiction. Safety: if morph is present and NOT a pronoun, skip (suspect).
    pm = is_pronoun_morph(r["morph"])
    if pm is False:
        nonpron_morph += 1
        skip_reason["morph-not-pronoun"] += 1
        continue
    new_base, lemma, note = target_for(gw, eb, r["morph"])
    ref = f"{r['book']} {r['ch']}:{r['vs']}"
    if new_base is None:
        skip_reason[note] += 1
        continue
    plan.append((r["rid"], new_base, lemma, note, ref, gw))
    bucket_count[note] += 1

# ── report ────────────────────────────────────────────────────────────────────
print(f"\n=== fix_g1473_gloss · {'APPLY' if APPLY else 'DRY-RUN'} · {DB} ===")
print(f"  G1473 slots total            : {total}")
print(f"  → leave: gloss consistent 1S : {skip_consistent}")
print(f"  → leave: reflexive '-self'   : {skip_self}")
print(f"  → leave: no pronoun gloss cue: {skip_nocue}")
print(f"  → SKIP (needs manual)        : {sum(skip_reason.values())}  {dict(skip_reason)}")
print(f"\n  PLANNED CORRECTIONS          : {len(plan)}")
for note in sorted(bucket_count, key=lambda k: -bucket_count[k]):
    print(f"     {note:<14} : {bucket_count[note]}")

# per-target-number tally + samples
by_target = defaultdict(list)
for rid, nb, lemma, note, ref, gw in plan:
    by_target[(nb, lemma)].append((ref, gw))
print("\n  by new Strong's:")
for (nb, lemma), items in sorted(by_target.items(), key=lambda kv: -len(kv[1])):
    sample = "  ".join(f"{ref}('{gw}')" for ref, gw in items[:4])
    print(f"     G1473 → G{nb} ({lemma}) ×{len(items)}    e.g. {sample}")

# per-book spread
by_book = defaultdict(int)
for rid, nb, lemma, note, ref, gw in plan:
    by_book[ref.split()[0]] += 1
print("\n  by book:", dict(sorted(by_book.items(), key=lambda kv: -kv[1])))

if not APPLY:
    print("\n  DRY-RUN — no changes written. Re-run with --apply (after cp backup) to commit.\n")
    conn.close()
    sys.exit(0)

# ── apply ─────────────────────────────────────────────────────────────────────
cur = conn.cursor()
n = 0
for rid, nb, lemma, note, ref, gw in plan:
    cur.execute(
        "UPDATE words SET strongs_base=?, strongs=?, lemma=? WHERE rowid=?",
        (f"G{nb}", nb, lemma, rid))
    n += cur.rowcount
conn.commit()
# verify invariant
bad = conn.execute("SELECT count(*) FROM words WHERE strongs_base GLOB '[0-9]*'").fetchone()[0]
left = conn.execute(
    "SELECT count(*) FROM words WHERE strongs_base='G1473'").fetchone()[0]
conn.close()
print(f"\n  APPLIED: {n} rows updated.")
print(f"  strongs_base bare-number invariant (must be 0): {bad}")
print(f"  G1473 slots remaining (the legit ἐγώ + skipped): {left}")
print("  Next: health_check.py → re-run audit_corpus_tier2.py → deploy.\n")
