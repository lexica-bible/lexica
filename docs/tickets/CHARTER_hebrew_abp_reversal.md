# CHARTER — no ABP results for a Hebrew number (reversal, JP-ruled 2026-09-06)

**Ruling (JP):** searching an H-number must show NO ABP results. The ABP tab greys for
every Hebrew number; the reader card's "× in ABP" line for a Hebrew name goes with it.
This is a REVERSAL of behaviour JP never intended, not a new design. Process finding
(reviewer): the routing charter's hadad/abishai controls (45 / 26 "via the Hebrew route")
pinned behaviour nobody ruled in — **retired**, they validate nothing.

## Where the feed came from (git, read 9/6)
1. `79b657d4` 2026-06-02 — `import_tipnr.py`: TIPNR writes HEBREW Strong's numbers onto
   ABP's Greek-text OT name slots (the "Hebrew stopgap"). That data alone makes an
   H-number's ABP tab open: `has_abp` finds words rows carrying the number.
2. `78f44670` 2026-07-24 — reader card gains the "× in ABP" occurrence line for a name's
   Hebrew number (`hebrew_count`, views_metav).
3. `4dac41c7` 2026-07-25 — candidate 3 (Hebrew retirement) moves those numbers off the
   words rows into `pn_hebrew_xref`, then `h_abp_predicate` + the `_abp_strongs_filter`
   union bring them BACK for every H-keyed ABP read, under the "S2-Q4 bar: nothing
   findable becomes unfindable". That bar preserved a feed JP had not ruled in.

## Surfaces that serve ABP from an H-number today (all must go grey/absent)
- Word study profile/verses/All-books: `_abp_strongs_filter` H-arm union (views_lexicon
  ~:345), `has_abp`, the corpus default/fallback, `_abp_book_counts`, `_abp_gloss_rows`.
- Results cards (English finder `abp_rows`, Greek/translit lookup): any ABP line on an
  H row.
- Reader word card: `hebrew_count` line (views_metav :752) + the "× in ABP" link
  (30-detail-panel.jsx :1386/:1464); the strongs-count read at views_metav :667.
- `h_abp_predicate` (core.py) itself: after the reversal it has no ABP consumer for the
  tab — audit every caller before deleting; a rebuild-chain script may still use it.

## Pre-registered, before code
1. **Inventory (JP-run, read-only):** how many Hebrew numbers currently reach ABP, and
   how many rows —
       sqlite3 ~/bible-db/bible.db "SELECT (SELECT count(DISTINCT strongs_base) FROM words WHERE strongs_base LIKE 'H%') AS h_numbers_on_words, (SELECT count(*) FROM words WHERE strongs_base LIKE 'H%') AS h_rows_on_words, (SELECT count(DISTINCT hebrew_base) FROM pn_hebrew_xref) AS h_numbers_in_xref, (SELECT count(*) FROM pn_hebrew_xref) AS xref_rows"
   Numbers reported as fact; the design is sized on them, not guessed.
2. **Gate:** after the change, zero Hebrew numbers open the ABP tab (test drives the
   production `has_abp` path on a fixture with an H-number that has words rows AND xref
   rows — must read grey; a Greek number must still open). Served: hadad H1908 grey,
   abishai H52 grey, a Greek word unchanged, galilee still 73.
3. **Not touched:** the words table, pn_hebrew_xref, the header/identity tables, the
   Hebrew OT (heb.db) tab — the HEB tab stays the Hebrew number's home.
4. Presentation (grey vs hidden ABP tab for Hebrew) = JP's call per the gray-don't-hide
   rule; default proposal: GREY (a real feature that doesn't apply here).

Order (reviewer): the routing lane closes on its two cards first; this lane is a separate
deploy so each served check reads clean.
