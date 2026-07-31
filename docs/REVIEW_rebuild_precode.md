# REVIEW PAYLOAD — rebuild pre-run code changes (RC-1, RC-2, backup retention)

Context: this is the words-table rebuild session chartered in `docs/REBUILD_SCOPE_headword.md`
(R-1: batch everything into one run). Per the charter, the code changes are submitted for
review BEFORE anything is edited or run. Nothing below has been applied yet. The reviewer has
no repo access, so existing code is quoted inline.

The rebuild itself follows the `/rebuild-words` procedure (copy-first, build into a test copy,
audit gates, JP swaps by hand). These three changes ride that run.

---

## Change 1 — RC-1: name-aware head pick, scoped to star/PN slots only

**Problem (pile 4 of the 2,203 double-star sweep):** a proper-noun slot whose English is a
phrase like `"Hezekiah said,"` or `"Bashan area."` gets its search head from the LAST
non-function word (`said` / `area`), so the Strong's backfill looks up "said" and misses.
The name never gets its number.

**Scope rule (JP-ruled 2026-07-16):** the name-preference applies ONLY where the slot's tag is
the proper-noun star (`strongs == '*'`). A blanket rule was measured against 14,938 rows and
proved wrong — `"the LORD said"` on a verb slot correctly heads `said`.

**Existing code** — `scripts/parse_abp.py`, `_head_word` (the head picker; picks the last
non-function token, lowercased unless a preserved theological term):

```python
def _head_word(text: str, italic_words=None) -> str | None:
    if not text:
        return None
    raw_tokens = text.split()
    skip_italic = {w.strip().lower() for w in italic_words} if italic_words else None

    def _pick(drop_italic):
        for raw_tok in reversed(raw_tokens):
            clean = re.sub(r"[^\w]", "", raw_tok)
            if not clean:
                continue
            lower = clean.lower()
            if lower in _FUNCTION_WORDS or lower in _HEAD_STOP:
                continue
            if drop_italic and skip_italic and lower in skip_italic:
                continue
            if clean.endswith("'s") or clean.endswith("s'"):
                clean = re.sub(r"'s$|s'$", "", clean)
                lower = clean.lower()
            return clean if clean in _PRESERVE_CASE else lower
        return None

    if skip_italic:
        head = _pick(True)
        if head is not None:
            return head
    return _pick(False)
```

**Proposed change 1a** — add an opt-in `prefer_name` branch (default off, so every existing
caller is byte-identical):

```python
def _head_word(text: str, italic_words=None, prefer_name=False) -> str | None:
    if not text:
        return None
    raw_tokens = text.split()
    skip_italic = {w.strip().lower() for w in italic_words} if italic_words else None

    if prefer_name:
        # Star/PN slots only (RC-1): the head should be the NAME, not a trailing
        # common word ("Hezekiah said," -> hezekiah, not said). Last capitalized
        # content token wins; if none, fall through to the normal pick.
        for raw_tok in reversed(raw_tokens):
            clean = re.sub(r"[^\w]", "", raw_tok)
            if not clean or not clean[0].isupper():
                continue
            lower = clean.lower()
            if lower in _FUNCTION_WORDS or lower in _HEAD_STOP:
                continue
            return clean if clean in _PRESERVE_CASE else lower

    def _pick(drop_italic):
        ...unchanged...
```

**Proposed change 1b** — one new final pass in `build_verse_words`
(`scripts/build_words_from_abp.py`), added at the END of the per-verse repair chain (after
`_strip_italic_heads`), so it covers every star row no matter which earlier pass wrote its
English — instead of chasing the ~10 individual `_head_word` call sites:

```python
def _star_name_heads(rows: list) -> None:
    """RC-1: a star/PN slot's search head prefers the capitalized NAME over a
    trailing common word ("Hezekiah said," -> hezekiah). Scoped to strongs='*'
    ONLY — content slots keep the existing last-word pick (JP-ruled 2026-07-16;
    a blanket rule rewrites correct heads). Runs LAST so it sees the final
    English of every star row. Touches english_head (idx 2) only."""
    for i, r in enumerate(rows):
        if r[3] != "*" or not r[1] or " " not in r[1]:
            continue
        new_head = _head_word(r[1], prefer_name=True)
        if new_head and new_head != r[2]:
            rows[i] = r[:2] + (new_head,) + r[3:]
```

(Plus: the ImportError fallback `_head_word` shim at the top of build_words_from_abp.py gets
the same `prefer_name=False` parameter, accepted and ignored, so the signature can't break.)

**Known limit, stated up front:** the picker can't see verse position, so a sentence-initial
capitalized common word inside a star slot could in principle win. Star slots are proper-noun
slots so this is rare; the post-run double-star re-audit measures whatever remains.

**Controls (from the charter, all must pass on the test copy before swap):**
- Isa 38:21 "Isaiah said" → head `isaiah` · Jos 17:1 "Bashan area." → `bashan` ·
  Deu 15:12 "Hebrew woman," → `hebrew`
- Non-regression: "God made" → `made` · "my spirit" → `spirit` · the five frozen S11
  pass-controls · `test_render_head_no_phantom.py` · strongs_base invariant = 0.

---

## Change 2 — RC-2: fill the 477 blank star rows (name pulled from the previous slot)

**Problem (pile 3):** source like `Shaul died,G599 G*` (1Ch 1:49) — one text chunk carrying
the verb's number and the name's star. The build gives the trailing `G*` its own EMPTY row;
"Shaul" rides inside the verb's cell. 477 rows canon-wide.

**What already exists:** the build already folds in a splitter for exactly this shape —
`scripts/fix_pn_subject_merge.py` (runs automatically as a finishing step of every rebuild).
It finds a multi-word cell with a real number whose first word is a capitalized name, with an
adjacent empty `*` slot, and splits: name → the lower position as a fresh `*` slot, verb →
the higher position keeping its number/lemma/morph. Proven on ~2,300 rows, dry-run first,
re-runnable, already has a conservative bracket policy.

**Why it misses the 477:** its name test requires the first word to be in the TIPNR name
roster. The genealogy flood is exactly the spelling variants that are NOT in the roster
(sabta, zephi, alian…), so `is_roster` fails and the row is skipped. It already has ONE
roster-free path — the εἰμί/copula case (`is_eimi`), gated to `G1510` + capitalized lead +
the clean unbracketed slot-after shape, with a sentence-initial function-word blocklist
(`_FUNCTION_LEAD`).

**Two implementation options:**

- **Option A (recommended): extend the existing splitter** with a third path,
  `is_capfall` — same guards as the εἰμί path but not number-restricted:
  capitalized lead, lead not in `_FUNCTION_LEAD`, not in the roster, adjacent empty `*`
  slot strictly AFTER, both slots unbracketed. Peel exactly one leading word (reuse
  `_peel_eimi`). The adjacent empty `*` is ABP's own declaration that a proper-noun word
  belongs there — the same argument that justified the εἰμί path. Reported as its own
  counter in the dry run so the full name list is eyeballed before `--apply`.

  ```python
        is_capfall = (not is_roster and not is_eimi
                      and fw.lower() not in _FUNCTION_LEAD)
        if not (is_roster or is_eimi or is_capfall):
            continue
        ...
        # capfall runs ONLY on the clean unbracketed slot-after shape, like eimi
        if (is_eimi or is_capfall) and (bracketed or not after):
            skipped_conservative += 1
            continue
        split = _peel_name(...) if is_roster else _peel_eimi(r["english"])
  ```

- **Option B (the charter's literal wording): parse-time fix in the build's emit path** —
  port the standalone parser's repair (parse_abp.py lines 205–239, the G*-with-no-English
  name swap) into `build_words_from_abp.py`. This touches the chunk parsing that is SHARED
  with the bracket audits (`iter_source_tokens` mirrors it — an audit-drift risk the shared
  helper exists to prevent), and re-implements swap logic the splitter already does with
  morph/lemma/bracket handling proven in production.

**Recommendation: A.** Same outcome (the charter's target is "kills the 477 blank-star
rows", verified by the 1Ch 1:49 control), ~15 lines in one proven script vs new parser
surgery, dry-run visibility of every affected row, and zero risk to the audit-shared
tokenizer. The charter's wording named the mechanism before the splitter's coverage gap was
understood as a roster gap; asking the reviewer to ratify the deviation.

**Interaction with RC-1/alias map:** the split mints `*` slots with the variant name as
English; the Strong's backfill (`import_tipnr`) then resolves them via the alias map
(Change 4, pending data). Order is already correct: the splitter folds into the build,
import_tipnr runs after.

**Controls:** 1Ch 1:49 → a Shaul row with real identity, no blank row. Post-run: blank-star
count (the 477) drops to ~0; any residue individually explained or STOP.

---

## Change 3 — backup retention: bible.db keeps 3

**Now:** `scripts/backup_db.py` keeps 14 backups per db (default `--keep 14`; the nightly PA
task passes no flags). bible.db copies dominate the pile.

**Charter line (JP-approved 2026-07-16):** big-file retention → 3, capping the pile ~800 MB.
Small dbs (study.db is the irreplaceable one) keep the default 14.

**Proposed:** a per-db override consulted at rotation time; the global `--keep` still works
for everything else.

```python
# Per-db retention override: bible.db copies are ~270 MB each and dominate the
# pile; JP-ruled 2026-07-16 keep 3 (never fewer — the newest good copy is never
# deleted by _rotate regardless). Small dbs keep the --keep default.
KEEP_OVERRIDE = {"bible.db": 3}
```

and in `backup_all`, the rotate call changes from
`_rotate(out, stem, keep, raw)` to
`_rotate(out, stem, min(keep, KEEP_OVERRIDE.get(stem, keep)), raw)`
(`min` so an explicit smaller `--keep` is still honored).

**Open question for the reviewer:** should `heb.db` (the Hebrew OT db) join the override?
It's rebuildable from STEP TAHOT source, so keep-3 is arguably right for it too. Recommend
yes if it's over ~100 MB; JP can read the size off `--list`.

---

## Change 4 — alias map (NOT in this payload; data-gated)

The ~1,690 variant→canonical `ALIASES` entries (`import_tipnr.py`) are hand-checked one by
one against Strong's/TIPNR before landing — wrong number is worse than missing. That curation
needs the full name list from the live db, which JP dumps (command already handed to him).
It comes back as its own review payload before it lands. LXX-only forms with no canonical
target are NOT force-mapped (they wait for the Greek-name migration, R-2).

---

## Gates before anything runs (unchanged from the charter)
1. Gate zero: JP's disk-space paste (≥600 MB free after the pre-rebuild backup exists).
2. This review's verdict on Changes 1–3 (and the Option A/B ruling).
3. Change 4 lands as its own reviewed batch.
4. Build into `bible.db.new`/test copy only; every audit gate in `/rebuild-words`; swap is
   JP's single reversible move.
