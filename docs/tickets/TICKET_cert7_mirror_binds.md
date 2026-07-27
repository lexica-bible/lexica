# TICKET — cert check #7: four place-as-person mirror binds (pre-existing on live)

Opened 2026-07-26 per the reviewer's candidate-3 battery disposition. Evidence of
pre-existence: check #7 fails IDENTICALLY on the untouched pre-rebuild copy
(bible_pre_r2c3_2026-07-25.db) — same four names, same counts — so live carried
this before the retirement and the rebuild neither caused nor touched it.

## The finding (cert_invariants.py check 7, both-directions form)

A name must not render a FUZZY match to one section AND an EXACT match to the
other. Four names trip the place-as-person direction (fuzzy-PERSON + exact-PLACE):

    ebal    1 fuzzy-person  /  5 exact-place
    jeshua  10 fuzzy-person /  1 exact-place
    judah   1 fuzzy-person  /  1 exact-place
    uzza    5 fuzzy-person  /  2 exact-place

Defining query (verbatim from cert_invariants.py check 7, the production detector —
the four names are the rows where fpe > 0 AND epl > 0):

    WITH r AS (SELECT b.name, b.kind, e.section
               FROM pn_binding b JOIN tipnr_entities e ON e.uniq = b.entity_uniq
               WHERE b.render = 1)
    SELECT name,
           SUM(kind='fuzzy' AND section='place')  AS fp,
           SUM(kind='exact' AND section='person') AS ep,
           SUM(kind='fuzzy' AND section='person') AS fpe,
           SUM(kind='exact' AND section='place')  AS epl
    FROM r GROUP BY name
    HAVING (fp > 0 AND ep > 0) OR (fpe > 0 AND epl > 0)

## Why this shape is suspicious, not proven wrong

The Cushi precedent (cert Session 4) was this pattern's mirror: the FUZZY bind
was the wrong one (a man rendering a place card). But the reverse inference is
not automatic here — e.g. jeshua's 10 fuzzy-person binds may be REAL people
(Jeshua the priest via a spelling variant) coexisting legitimately with the
place Jeshua (Neh 11:26). The check flags coexistence; it does not adjudicate it.

## Proposed handling (for reviewer ruling BEFORE any build)

1. **Evidence pass first (read-only):** dump the four names' fuzzy-person render
   rows (book ch:vs, entity bound, stored number) + the exact-place rows, and
   check each fuzzy-person bind against TIPNR at the attested verse — is the
   bound person entity the right referent there? Per-row verdicts, no sampling.
2. **Candidate fix if rows prove wrong:** the SYMMETRIC guard —
   entity_resolution.py's fuzzy path already skips a PLACE candidate when an
   exact-spelling PERSON entity carries the same stored number
   (`person_same_num`, the Cushi fix, :749–753); mirror it: skip a PERSON
   fuzzy-candidate when an exact-spelling PLACE entity carries the same number.
   Same safe direction (can only floor, never mis-bind). Blast radius = at most
   the 17 fuzzy-person rows above.
3. **If rows prove RIGHT:** the fix is a check-7 refinement (an allowlist with
   per-name reasons, or a sharper predicate), not a binder change — a green
   check must mean something, so today's standing red can't just be accepted.

Binder changes are trial-then-apply (dry-run must reproduce current counts
except the itemized rows); cert #7 must go green (or be sharpened) either way.

## Ruling (reviewer, 2026-07-26, forwarded by JP) — APPROVED AS WRITTEN

Evidence pass first, read-only, per-row against TIPNR, no sampling — then fork on
the verdicts: rows wrong → mirror the Cushi guard (`person_same_num` symmetric,
entity_resolution.py :749–753 shape); rows right → sharpen check 7 with per-name
allowlist reasons. Trial-then-apply on any binder change: dry-run reproduces
today's counts except the itemized rows; check 7 green or sharpened either way.

**Added condition:** each per-row verdict must CITE the TIPNR entity at the verse,
not just a yes/no — so if the outcome is the allowlist, the reasons are already
written.

## Evidence pass (2026-07-27) — all 17 fuzzy-person rows RIGHT

Full binding dump pulled from live PA (read-only, every render row for the four
names). All 17 fuzzy-person rows adjudicated against the pinned tipnr/TIPNR.txt,
per-row, entity cited (reviewer condition):

| Rows | Bound entity | TIPNR citation | Verdict |
|---|---|---|---|
| ebal 1Ch 1:22 | Obal@Gen.10.28-1Ch | line 18510: Spelled-row "Obal =ESV,NIV; Ebal =KJV", ref 1Ch.1.22 | RIGHT |
| jeshua Ezr 2:2, 3:2, 3:8, 4:3; Neh 7:7, 12:1, 12:7, 12:10, 12:26 | Joshua@Ezr.2.2-Zec | line 14256: Named-row "Jeshua =ESV,KJV", refs list = exactly these nine | RIGHT |
| jeshua Ezr 5:2 | Joshua@Ezr.2.2-Zec | line 14257: Aramaic-row, ref Ezr.5.2 | RIGHT |
| judah Mrk 6:3 | Jude@Mat.13.55-Jud | line 14542: same-form row "Judas =ESV,NIV; Juda =KJV", ref Mrk.6.3 | RIGHT |
| uzza 1Ch 6:29 | Uzzah@1Ch.6.29 | line 24043: Named-row "Uzzah =ESV,NIV; Uzza =KJV", ref 1Ch.6.29 | RIGHT |
| uzza 1Ch 13:7, 9, 10, 11 | Uzzah@2Sa.6.3-1Ch | line 24051: Named-row, refs = exactly these four | RIGHT |

The exact-place partners are all real places (Mount Ebal, the village
Jeshua@Neh.11.26, Judea@Ezr.9.9-1Th, the garden Uzza@2Ki.21.18) — genuine
person-and-place coexistence, zero mis-binds. Binder untouched per the ruling.

## Outcome: check 7 sharpened (option 3)

`_MIRROR_ADJUDICATED` in scripts/cert_invariants.py: the four names allowlisted
for the mirror direction only, PINNED to the audited counts (1/5, 10/1, 1/1,
5/2) with the per-row reasons above — any NEW bind for one of these names
re-fires the check with a counts-MOVED note. Control 7b proves the allowlist
can't blind: an allowlisted name at moved counts FIRES, at audited counts stays
quiet; the cushi/zorahite positives still fire. --controls run green locally.

Status: FIXED pending live green — JP runs check 7 on PA; ticket closes on a
7/7 green run.
