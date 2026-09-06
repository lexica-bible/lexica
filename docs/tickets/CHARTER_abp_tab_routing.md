# CHARTER — ABP-tab routing (opened 2026-09-06)

Opener: `docs/handoffs/HANDOFF_abp_tab_routing.md`. Standing law: verdict gate ·
audit-tools-must-fail · visual changes need JP's yes · word-study.md is the routed doc.

## The mechanism (code read 9/6, views_lexicon.py)
- `has_abp` (`:1421`) asks the production ABP predicate (`_abp_strongs_filter`) whether
  any `words` row carries the number. Galilee's 73 ABP rows are starred, no number → 0 →
  tab greys, and the profile's corpus fallback (`:1290`) silently lands on KJV.
- The by-form door `_pn_lemma_rows` (`:1140`) matches `greek_lemma = ?` byte-exact with
  `greek_strongs IS NULL`. Post-fold every galilee row stores Γαλιλαία (source
  `surface`), so the door NOW returns 73 for that key — the trap is closed for folded
  names and still open for unfolded ones (per-verse forms, source `lemma-only`).
- Nothing in the data links G1056 to the header Γαλιλαία. The only candidate bridge is
  the number's own dictionary lemma, folded the way `lemma_plain` is (`_norm_lemma`:
  accents off, lowercase, final-sigma folded), against the folded stored header.
- Hebrew-keyed names (hadad H1908, abishai H52) already reach ABP through
  `h_abp_predicate` (words rows + pn_hebrew_xref). This lane is the GREEK-number case.
- The tipnr union inside `_abp_strongs_filter` is skipped once `pn_hebrew_xref` exists
  (live), so the audit's off-app run matches the served predicate.

## Pre-registered (before any code)
1. Galilee's ABP tab shows **73**, from identity rows under the folded header, never
   from one printed form. Pin: G1056 → BRIDGE-SURFACE, 1 stored value, 73 rows.
2. Unfolded names stay grey. A number whose lemma reaches only `lemma-only` rows
   (class LEMMA-ONLY-ONLY) is NOT routed — a one-form count presented as a total is
   the failure this lane exists to prevent. Their count = a follow-up hand-table queue.
3. KJV 63 and ABP 73 are different layers; the tab that is ON says which count it is.
4. Served check set: galilee 73 · zion (count from the audit) · hadad 1Ki 11 (Hebrew
   route, already open — confirm 12) · abishai (Hebrew route, 3 forms — confirm count).
5. Presentation = JP's call. Proposal below; nothing ships on it without his yes.
6. **Detector control (must fire before any number is trusted):** the audit runs on
   LIVE (galilee → BRIDGE-SURFACE 73/1) AND on the pre-fold 9/6 backup (galilee →
   LEMMA-ONLY-ONLY, 6 stored values, 13 under Γαλιλαία). Both, same script.
   → **TRIPWIRE: the 9/6 pre-swap backup is load-bearing until this control has run.**
   Retention is 3 copies; do not let a manual backup run rotate it out first.

## Step 1 — measurement (JP-run, read-only, both dbs)
    PYTHONIOENCODING=utf-8 python3 ~/bible-db/scripts/audit_abp_tab_bridge.py ~/bible-db/bible.db
    PYTHONIOENCODING=utf-8 python3 ~/bible-db/scripts/audit_abp_tab_bridge.py <9/6 pre-swap backup>
Expected picture, live: G1056 pin OK · MIXED = 0 · COLLISION = 0 (any non-zero of those
is its own finding and stops the design until ruled: MIXED = a tab that opens today with
a SHORT count; COLLISION = two numbers claiming one header, must be labeled or refused).
Class sizes are unknown — reported as fact, not guessed. Zion's class is a read, not a pin.

## Step 2 — design (only after step 1 verdicts)
Backend, `lexicon_profile` + `lexicon_verses` + `_all_books_verses`, Greek numbers only:
when the production predicate finds no words row AND the number's folded lemma reaches
exactly ONE `surface` header key, the ABP branch is served from `_pn_lemma_rows(header)`
— the SAME derivation the PN: page and the card's static count use (parity test
`test_pn_lemma_wordstudy.py` extends to cover it). `has_abp` becomes true, corpus
fallback to KJV stops firing, occurrence rows carry `position` for the highlighter (the
PN: lane's mechanism). The profile carries a new flag naming the route (name-form bridge)
so the frontend can label the count honestly — **new field = JP checkpoint before it
lands**. LEMMA-ONLY-ONLY and NONE: unchanged (grey).
Frontend: the ABP tab enables; the state line under the count says the occurrences are
ABP's printed name-form under one header (wording to JP). No new chrome.
Locked test: fixture with a surface-bridged number (73-shaped), a lemma-only-only number
(must stay grey), a mixed number, a collision pair (must refuse) — fires on the positive
first.

## Step 3 — served checks (JP, after deploy)
galilee → ABP tab ON, 73, KJV tab 63 · zion per audit · hadad 12 · abishai per audit ·
one LEMMA-ONLY-ONLY member stays grey.

## Step 1 RESULT + RULINGS (2026-09-06, JP-run census, reviewer-ruled)
Live: galilee PIN OK (73, 1 value) · greyed Greek numbers 187 · BRIDGE-SURFACE 8 ·
LEMMA-ONLY-ONLY 23 (Israel 2,584, Jerusalem 753 among them) · MIXED 47 · COLLISION 2
(γαζα G1047/G1048 · ηλι G2241/G2242). Pre-fold copy: galilee LEMMA-ONLY-ONLY, 13 rows,
1 value — the census CANNOT see the other 60 rows; the split-form trap is handled by
REFUSING lemma-only routing, not by detecting splits. Hadad 45 / Abishai 26 via the
Hebrew route (already open).
1. **Routable set = 6**: Galilee 73 · Damascus 63 · Arabia 12 · Salem 4 · Euroclydon 1 ·
   Abaddon 1. Condition per number, locked in the test: folded lemma reaches ONLY
   `surface` rows (lemma-only = 0), ONE stored value, key owned by exactly ONE lexicon
   number. Zion (168+1) and Aram (12+5) FAIL lemma-only = 0 → header-lane follow-up folds
   their residuals, then they route by the same rule with no code change.
2. **Israel / Jerusalem: HELD, extension REFUSED.** Their signature is identical to
   pre-fold Galilee's; "indeclinable" is knowledge from outside the census. Any future
   routing goes through the header lane (vetted `surface` class), never a lemma-only door.
3. **COLLISION refused** (key with >1 number never bridges) — locked in the test.
4. **MIXED = separate follow-up** (this census is the inventory); the same-header
   numberless-pull ruling is deferred to that lane.
5. Housekeeping: scratch copies deleted before the nightly landed (bounded: live holds
   the post-swap state, the 15:39 copy is the swap rollback, builder reproduces the
   copy). The 15:39 copy stays the rollback until a post-swap nightly lands; manual
   backup hold lifts then. It is no longer load-bearing for this lane.

## Step 2 DESIGN (field checkpoint — awaiting JP's OK before it lands)
- Backend helper `_header_bridge(conn, snum)` → the stored header or None, applying
  rule 1 exactly (production `_norm_lemma`, `lexicon.lemma_plain` uniqueness for the
  collision refusal). Used in `lexicon_profile`, `lexicon_verses`, `_all_books_verses`
  for Greek numbers only, only when the production ABP predicate finds no words row.
- When it bridges: the ABP branch (book counts, occurrence rows with `position`, total)
  = `_pn_lemma_rows(header)` — the PN: page's own derivation, so the number's ABP tab and
  the PN: page agree by construction (parity test extended). `has_abp` true; the silent
  KJV fallback stops firing for these six. ABP renderings list stays empty (starred rows
  have no English head to fold) — as on the PN: page.
- **ONE new profile field: `abp_header` = the Greek header string**, present only when
  bridged (absent = today's behaviour, so no other consumer changes). It drives the
  frontend state line and nothing else.
- Frontend (`80-lexicon.jsx`, both desktop and mobile card): tab enables via `has_abp`
  as today; under the count, when `abp_header` is set and the ABP tab is on, one
  `.detail-morph` line in the PN: lane's existing style — wording proposed to JP:
  "ABP prints this name without a Strong's number — listing its 73 occurrences under
  the header Γαλιλαία. KJV counts are KJV's own tagging." (pre-reg 3). No new chrome.
- Locked test (fixture, fires on the positive first): bridged 73-shaped number routes ·
  lemma-only residual refuses · collision pair refuses · MIXED number untouched ·
  parity with `_pn_lemma_rows`. Added to BOTH CI lists.

## BUILT 2026-09-06 (field `abp_header` JP-approved; wording JP-ruled)
`views_lexicon._header_bridge` + `_bridge_if_grey`; profile/verses/all-books wired;
state line in `80-lexicon.jsx` (shared card body → desktop + mobile). Locked
`tests/test_abp_tab_bridge.py` (positive first, every refusal, parity) in both CI lists.
Served check (JP, after deploy): galilee ABP tab ON = 73 with the state line, KJV tab 63 ·
damascus 63 · Israel stays grey · a MIXED name (Nathanael) unchanged.

## Served check round 1 (JP, 2026-09-06) + rulings
Galilee 73 + state line PASS (KJV tab 63 = receipt; the sidebar's "galilee 62" is KJV's
second rendering "for" ×1 not listed — display finding, OUTSIDE this lane, filed in TODO) ·
Damascus 63 PASS · Israel grey PASS (H3478 carries ABP = Hebrew route, expected) ·
Nathanael 6 unchanged (follow-up c) · Hadad 45 PASS.
**Ruling: the results card must agree with the page.** G1056's card showed no ABP line
while the page said 73 (starred rows have no renderings to fold). Fixed: `_bridge_line`
(same header + `_pn_lemma_rows` count) feeds both emitters (English finder, Greek
lookup) as `abp_header` + `abp_total`; both cards render "ABP Γαλιλαία 73" in the
existing line style. Absent field = card unchanged. Locked in the test.
**Hadad lighting (finding, NOT this lane):** on the H1908 page only some verse rows
light the name; the Αδάρ name-form page lights all 12. This lane's diff never enters
a Hebrew path (`_bridge_if_grey` returns None on `is_heb` before any read; every new
branch is gated on that result) — so the pattern predates the deploy. Hypothesis to
test, not a verdict: the numbered All-books view carries no slot, so the verse row
lights by matching H1908 on the words it fetches; rows whose Hebrew number was retired
into pn_hebrew_xref no longer carry it on the word, so the LIST finds them (predicate
union) but the ROW can't light them. Filed under the hadad hard case in TODO.
