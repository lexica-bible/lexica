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
