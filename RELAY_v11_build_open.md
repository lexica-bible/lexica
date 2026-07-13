# V11 BUILD SESSION — OPEN PACKAGE (CC → reviewer, via JP relay; 2026-07-12)
# CC proposes only. Nothing below is ruled until the reviewer rules it. R1-b: reviewer
# please confirm receipt ("received, N lines") before adjudicating.

## A. Opening checks (ran clean)
- `git log --oneline -1` → 35dfe67 (WRAP corrective-commit close-out — descendant of 4962c32). PASS.
- `python tests/test_repair_pass.py` → "test_repair_pass: ok". PASS.
- `python tests/test_coverage_gate.py` → "test_coverage_gate: all assertions passed". PASS.
- Required reads done in order: DESIGN_v11_acceptance.md in full (STATUS + true sequence
  first), audit CORRECTION entry + CORRECTIVE-COMMIT CLOSED entry + V10 ACCEPTANCE TEST
  entry, ENGINE_LESSONS #48–#50.

## B. The two standing-rule candidates (banked at the corrective close — rule at this open)
CC recommendation: ADOPT BOTH as written.
1. **Affirmed-texts-to-disk:** any text a successor session must copy exactly (commit
   messages, handoff blocks, ruled wording) is written to DISK at affirmation time — a
   file or the handoff doc — never left only in chat relay. Rationale: the corrective
   session's gate-3 near-miss (affirmed commit text not on disk; CC correctly held).
2. **Commit-message shape:** every commit-message proposal carries a short subject line
   + blank line + body, at proposal time. Rationale: two one-paragraph messages
   (a9d518b, 4962c32) break `--oneline` readability; cheap to fix at the source.
This package itself follows candidate 1 (it is on disk at RELAY_v11_build_open.md).

## C. STEP-2 CODE-READ GATE — probe-1 code claims verified against
## scripts/build_lexica_def.py ON DISK (head 35dfe67). Raw findings:

**Claim 1 — "the coverage gate holds fed KEYS, not texts": CONFIRMED.**
`coverage_gate(fed_refs, senses_block)` at line 708 takes (book,ch,vs) keys only; the
call site at 2277 builds `fed_keys = [(c[0], c[1], c[2]) for c in ctx]`. No verse text
enters the gate.

**Claim 2 — "fed texts exist only on draw/apply passes": CONFIRMED, with a precision.**
`ctx` (from `fetch_context`, 469–482) carries each FED verse's prose at tuple index 5,
and ctx exists only on draw/apply (a --resplit pass has no fed sample; lines 2271–2275
print the loud NOT-RUN). Precision: even on draw/apply, ctx holds only the FED sample's
texts — a card cites refs beyond the fed set (Range, gloss notes, repair-integrated
refs), so ctx alone could never feed probe 1. The design's own-lookups choice is not
just conservative, it is REQUIRED.

**Claim 3 — "SELECT-text-FROM-verses at lines 472/1208/1427": CONFIRMED, all three.**
- 472: `fetch_context` — by verse id (fed sample).
- 1208: gloss-claim checker — by book/chapter/verse.
- 1427: `build_verses` — by book/chapter/verse, cited refs → texts. This is exactly
  probe 1's needed pattern.

**Claim 4 — "connection already in hand at the call site": CONFIRMED at the CALL SITE,
NOT inside validate_entry.** `validate_entry(entry)` (1741) takes no DB connection; but
at its one call site (2301) `conn` is in scope (used at 2266 `assemble(conn, ...)`).

**NEW FINDING the design should weigh (probe-1 data source):** `assemble` already stores
`entry["verses"] = build_verses(conn, refs)` (line 1722) — live verses.text for EVERY
ref cited anywhere in the raw, fetched fresh each build/resplit. So probe 1 has two
compliant data paths:
  (i) read `entry["verses"]` inside validate_entry — no signature change, data is the
      same live lookups; CAVEAT: build_verses SILENTLY SKIPS refs the DB doesn't carry
      (1429–1430), so a quote citing a skipped ref would see no candidate text — probe 1
      must treat a cited-but-absent ref as NOT-RUN-loudly for that quote, never a pass.
  (ii) pass conn into validate_entry (signature widens: `validate_entry(entry, conn=None)`;
      `conn is None` → probe announces NOT RUN loudly, the coverage-gate convention).
CC recommendation: **(ii)** — own lookups per the affirmed design, conn=None default
keeps every existing caller/test valid, and the NOT-RUN convention falls out naturally.
(i) stays on record as the fallback. Reviewer rules.

## D. Dash-expansion CHECK-FIRST — code side ANSWERED, raw side needs one PA read.
The range-tail walker's dash class at line 647 is `[–—-]` — en dash, em dash, AND
hyphen all match. So `ref_spans`' #28 expansion is NOT blind to the typographic dash;
the code-blindness hypothesis is dead on the code read. Why G162 d2's "Isa 49:24–25"
left 49:25 uncited therefore needs the cached raw: either the span sat OUTSIDE the
senses block (Range/gloss notes don't count for coverage — ruled), or the raw's exact
bytes broke the match some other way. One read-only PA look settles it (command in F).

## E. NORMALIZATION TABLE — DRAFT for ruling (probe 1's matcher; ruled before red-first;
## anything not listed = strict byte match). Each row tagged.
| # | Both-sides treatment | Basis |
|---|---|---|
| 1 | Curly ↔ straight quotes/apostrophes treated equal (’='  “”=") | conservative-safe: pure typography; a card quote must not fail on apostrophe style. No meaning carried. |
| 2 | Whitespace runs collapse to one space; leading/trailing trimmed | conservative-safe: line-wrap artifacts. |
| 3 | `…` = `...` (three dots) as the ellipsis marker | conservative-safe: the ruled allowance is "marked ellipsis"; both spellings mark it. |
| 4 | Em dash — = en dash – = ` -- ` | CHECK-FIRST (PA): verses.text convention is `--`→`—` (fix_emdash); confirm on real rows before ruling. Until confirmed: strict. |
| 5 | Translator-addition brackets in verses.text: `[word]` compares equal to `word` (brackets stripped on the VERSE side only; card-side brackets never stripped) | CHECK-FIRST (PA): confirm verses.text actually carries brackets inline. G162 d2 exhibit rides this row if the dropped "into the height" sat near a bracket. Until confirmed: strict. |
| 6 | Initial-letter case exempt; interior alteration never | already RULED (standing sub-rule) — restated for completeness, not a new row. |
NOT proposed (stays strict): any word-level change, punctuation removal beyond the rows
above, unicode folding beyond the listed marks. Rows 4–5 get their bytes from the PA
reads in F, then the reviewer rules the table as a whole.

## F. PA reads for JP (all read-only; one paste-ready block). This is also the ONCE
## read-only cache consult the fixture rule allows — fixture texts come from these bytes.
```bash
cd ~/bible-db
# 1. G162 d2 cached raw — the dash question + the "into the height" quote bytes
python - <<'EOF'
import json,glob
for p in glob.glob('lexica_draws/G162*'):
    print('==',p)
    d=json.load(open(p))
    raw=d.get('raw','')
    import re
    for m in re.finditer(r'.{60}49:2[45].{60}', raw, re.S): print(repr(m.group(0)))
    for m in re.finditer(r'.{80}height.{80}', raw, re.S): print(repr(m.group(0)))
EOF
# 2. Verse bytes for the six-defect fixtures + normalization rows 4-5
sqlite3 -readonly bible.db "SELECT book,chapter,verse,text FROM verses WHERE (book='2Ch' AND chapter=21 AND verse=3) OR (book='Job' AND chapter=5 AND verse=12) OR (book='Job' AND chapter=42 AND verse IN (7,8)) OR (book='Isa' AND chapter=42 AND verse=3) OR (book='Mat' AND chapter=22 AND verse=16) OR (book='Mar' AND chapter=12 AND verse=14) OR (book='2Sa' AND chapter=19 AND verse=42) OR (book='Eph' AND chapter=4 AND verse=8);"
# 3. Dash + bracket conventions in verses.text (rows 4-5 evidence)
sqlite3 -readonly bible.db "SELECT count(*) FROM verses WHERE text LIKE '%—%'; SELECT count(*) FROM verses WHERE text LIKE '%--%'; SELECT count(*) FROM verses WHERE text LIKE '%[%';"
# 4. The two dead repaired cards' raws (fixture card-side bytes; READ-ONLY, no apply)
python - <<'EOF'
import json,glob
for p in glob.glob('lexica_draws/G227*')+glob.glob('lexica_draws/G1390*'):
    print('==',p); d=json.load(open(p)); print(d.get('raw','')[:200],'...[len',len(d.get('raw','')),']')
EOF
```
(If the draw-cache filenames differ, `ls lexica_draws/ | grep -E 'G162|G227|G1390'`
first and I'll adjust. Full raws of G227/G1390 needed eventually for fixture quotes —
if the 200-char preview isn't enough I'll ask for a full dump to files.)

## H. F-BYTES FINDINGS (CC → reviewer, second relay; PA output received 2026-07-12)

**H1 — G162 dash question: the d2 raw NO LONGER EXISTS.** The cache keeps one file per
word, refreshed each draw; G162.json holds a later draw (no "49:24–25" span anywhere in
it — only a plain "Isa 49:24:" cite). Code side already established the range walker
accepts en dash, em dash, and hyphen alike (line 647 `[–—-]`). CC recommendation:
CLOSE the CHECK-FIRST as unresolvable-no-evidence-of-bug — code handles all three
dashes; the one raw that could show otherwise is gone; if the class recurs, capture the
raw at that moment. (Also noted: the file's key is `sig`, not `signature` — my probe
printed "?" for that reason; not a data problem.)

**H2 — Table row 4 (dashes): ADOPT, now exhibit-backed.** verses.text carries 2,291
em-dash rows, zero `--`, and one fixture verse (2Ch 21:3 "many gifts — silver, and
gold") has the em dash inside a span a card would quote. A draw could plausibly emit
`--` or en dash for it. Proposed row: em dash = en dash = ` -- ` on both sides.

**H3 — Table row 5 (brackets): DROP.** verses.text contains ZERO `[` characters
(SQLite LIKE treats `[` literally, so the zero is real). Nothing to normalize;
strict stands with no row needed.

**H4 — Final table for ruling:** rows 1–3 as adopted (curly/straight quotes ·
whitespace collapse · `…`=`...`) + row 4 per H2 + row 6 restated ruled sub-rule.
Row 5 deleted. Everything else strict byte match.

**H5 — Fixture bytes verified against the six defects (all fire as specced):**
- Defect 1 (probe 2): G1390 card says "Jehoiada's father… (2Ch 21:3)"; the verse names
  only "their father" and Jehoram. Fires.
- Defect 2 (probe 2): G227 card says "Eliphaz's schemes… (Job 5:12…)"; verse subject is
  "clever ones". Fires.
- Defect 4 (scanner 3): G227 card "the parallel affirmation at Mar 12:14 is worded
  identically"; the two stored texts differ in order and connectives. Fires. Pattern
  list seed: "worded identically" / "identical wording" / "verbatim parallel".
- Defect 5 (probe 1 anchoring): G227 card quotes "did not speak true" anchored
  "(Job 42:7; also Job 42:8…)"; the wording is 42:8's exactly, 42:7 reads "you spoke
  not anything before me true". Fires on the anchoring rule.
- Defect 6 (probe 1 verbatim): G227 gloss note quotes "bring forth judgment to
  validity"; stored Isa 42:3 is "to validity he will bring forth judgment". Fires,
  gloss-notes-inside rule.
- BONUS, as the design footnote predicted: defect 3's sentence (G1390, "David receiving
  provisions from his kin… 2Sa 19:42") names David; the stored verse says only "the
  king". Probe 2 would incidentally flag it — the predicted bonus fire, never relied on.
  Worth a fixture as a documented-bonus case, not a spec obligation.

**H6 — One more small PA read needed for the PASS fixtures + no-op control (reviewer
to sanction — the once-rule covered the two KILLED caches, both now spent correctly;
G2168 is a shipped card, different bucket):** G2168.json raw (the no-op control needs
its quoted spans + their verse texts embedded) + verse texts for Psa 68:18, Num 3:9,
Gen 41:32 (pass-case candidates already quoted in the raws in hand: a marked-ellipsis
quote, an initial-cap quote).

## G. Sequence from here (no code yet — gates in order)
1. Reviewer receipt-confirms this package, rules B (two candidates), C (probe-1 data
   source, my rec = conn param), and the code-read gate itself (claims verified).
2. JP runs F; bytes come back; rows 4–5 resolve; reviewer rules the normalization table.
3. Then and only then: probes 1+2 + scanner 3 coded in/around validate_entry, shown IN
   FULL in chat before any commit; controls red-first from the banked defects;
   embedded-text fixtures; both CI lists; neighbor tests green.
