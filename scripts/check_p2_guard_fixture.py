"""check_p2_guard_fixture.py — THE single source of the probe-2 guard fixture claim, plus the
drift check that keeps it honest.

WHY THIS FILE EXISTS (JP ruling 2026-07-14, checkpoint cleared: "move the eight-word claim to ONE
file the drift check owns; the test imports it. Verification date rides with it. No third copy,
ever."). The claim below was VERIFIED ONCE against a live control run on PA on 2026-07-12 and was
never re-checked — it lived hard-typed inside a test function (test_v11_probes.py) and restated in
a comment (build_lexica_def.py): two copies, one verification, and no way to notice drift. That is
the #71 class (a fixture string is a CLAIM). Writing the words into a checker as well would have
made a THIRD copy — so instead this file OWNS them and everyone else reads from here.

WHAT IT PROTECTS. build_lexica_def's p2wl:v2 sentence-starter demotion asks the corpus "is this
capitalized token a real name?" via the words table's name-marked heads. The test's fixture stands
in for that corpus read (CI has no bible.db by ruling — test_v11_probes.py's header condition), so
the fixture is a promise ABOUT the corpus that only PA can keep.

THE DANGEROUS DIRECTION. If a name loses its marking, production drops it from the guard, a real
name at a sentence start is DEMOTED, and its warn is EATEN — silently — while the test, holding
the name hard-coded, still says green.

WHERE IT RUNS. Chained into import_tipnr.py — the VERIFIED sole writer of is_pn=1 (:610 UPDATE …
is_pn=1 WHERE rowid=?, :615 UPDATE … WHERE strongs_base='*'); the build CLEARS is_pn
(build_words_from_abp.py:1635) and everything else in scripts/ only READS it. So the single writer
of the marking is the single hook, and it fires whether import_tipnr runs inside
finish_rebuild.sh's tail or standalone (which CLAUDE.md mandates after ANY words rebuild).

SEVERITY — JP-RULED 2026-07-14: a mismatch must NOT fail or abort the rebuild. THE REBUILD IS NOT
WRONG; THE FIXTURE IS STALE. The flag's job is to make a human re-verify or re-rule the claim. It
blocks finish_rebuild.sh's "done" line (that wrapper collects per-step problems and refuses to
declare success) and says DO NOT SWAP — the same "named gate, don't-swap consequence" convention
the rebuild checklist already uses for audit_split_flip.py. No new tier.

NEVER A COPY: the membership test below is build_lexica_def's OWN production read + its OWN
membership helper, imported, not reimplemented (feedback_audit_tools_must_fail — reuse the
production detector).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── THE CLAIM — single source. Verified against a live PA control run on this date. ────────────
# To UPDATE: re-verify on PA and PASTE the emitted values here — never retype from memory, never
# infer from a neighbouring assertion's shape (#71; the fixture-string rule).
FIXTURE_VERIFIED = "2026-07-12"

# These MUST be name-marked heads in the words table (real names the guard has to know).
GUARD_NAMES_PRESENT = frozenset({"korah", "solomon", "laban", "jesus", "peter"})

# These MUST NOT be (ordinary prose the demotion tests use as card-furniture candidates).
# NOTE: this half was COMMENT-ONLY until 2026-07-14 — the test used the tokens but never asserted
# the corpus lacks them. The check below is the first thing to actually test it.
GUARD_NAMES_ABSENT = frozenset({"votive", "active", "applying"})


def check_guard_fixture(conn):
    """Compare the claim above against the LIVE corpus. Returns (ok, lines).

    ok=False means the corpus no longer matches the fixture — the fixture is stale, NOT the
    rebuild. Lines are ready to print; the caller decides the exit code (JP ruling: flag, never
    abort)."""
    import build_lexica_def as B

    names = B._p2_corpus_names(conn)
    if names is None:
        return False, [
            "!! PROBE-2 GUARD FIXTURE CHECK — NOT RUN: the guard read itself failed.",
            "   " + B._p2_guard_notrun(conn),
            "   The fixture was NOT checked — this is not a pass. DO NOT SWAP.",
        ]

    # PRODUCTION's own membership test (_p2_known — it loosens singular/plural), never a copy:
    # what matters is what the live guard would ACTUALLY treat as known, not raw set membership.
    missing = sorted(w for w in GUARD_NAMES_PRESENT if not B._p2_known(w, names))
    intruded = sorted(w for w in GUARD_NAMES_ABSENT if B._p2_known(w, names))

    if not missing and not intruded:
        return True, [f"  [OK] probe-2 guard fixture still matches the corpus "
                      f"({len(GUARD_NAMES_PRESENT)} name(s) marked, {len(GUARD_NAMES_ABSENT)} "
                      f"non-name(s) unmarked; baseline verified {FIXTURE_VERIFIED})."]

    lines = ["", "=" * 78,
             "!! PROBE-2 GUARD FIXTURE DRIFT — DO NOT SWAP",
             "=" * 78,
             f"   The words table's name-marking no longer matches the claim the probe-2 test",
             f"   fixture depends on (baseline verified {FIXTURE_VERIFIED}, never re-checked until",
             f"   now). THE REBUILD IS NOT WRONG — THE FIXTURE IS STALE.",
             ""]
    if missing:
        lines += [f"   LOST their name-marking (the DANGEROUS direction — production would DEMOTE",
                  f"   these at a sentence start and EAT their warns, while the test still passes):",
                  "     " + ", ".join(missing), ""]
    if intruded:
        lines += [f"   GAINED a name-marking they should not have (demotion would stop firing on",
                  f"   them, so probe 2 goes quieter than the test asserts):",
                  "     " + ", ".join(intruded), ""]
    lines += ["   WHAT TO DO: decide whether the corpus change is legitimate. If it is, UPDATE",
              "   scripts/check_p2_guard_fixture.py by PASTING this run's findings (never retype",
              "   from memory — #71), re-date FIXTURE_VERIFIED, and re-run the probe-2 tests. If it",
              "   is not, the rebuild changed name-marking it should not have — investigate before",
              "   swapping.",
              "   This does NOT mean import_tipnr failed: its work is committed and complete.",
              "=" * 78, ""]
    return False, lines
