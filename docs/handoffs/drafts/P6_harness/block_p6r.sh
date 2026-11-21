set +H
L=~/edition_upgrade_runs/p6r_swap_ready.log
if [ -e "$L" ]; then echo "P6R RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=d34d6723
export TZ=UTC
export GIT_OPTIONAL_LOCKS=0
echo "GATE REF ${REF} - P6R - the swap, READY: the checks that must come after CC's push and before JP's Disable (DESIGN 9.228: everything readable before Disable is read before it) - READ-ONLY; site UP; writes only this log - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "P6R RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db
LIVE=~/bible-db/bible.db
R=~/edition_upgrade_runs
D=$R/p6_swap
XB=d2c8603b4700d6dce089b688c5e00e8a3fdec879eea96bef5a6ce7cd09ca1523       # built full sha256 = P6's pin (DESIGN 9.222 (1))
h() { cut -d' ' -f1 <<< "$(sha256sum < "$1")"; }
grep -qx "P6A RESULT: DONE - CC pushes the swap commit next (PA does NOT pull it); then JP pastes P6R" "$R/p6a_swap_pre.log" || { echo "P6R RESULT: STOP - P6A has not finished DONE"; exit 1; }
[ -s "$D/src_digests.json" ] && [ -s "$D/check.py" ] || { echo "P6R RESULT: STOP - P6A's run folder is incomplete"; exit 1; }
git merge-base --is-ancestor "$REF" HEAD && git diff --quiet "$REF" HEAD -- scripts tests && [ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "P6R RESULT: STOP - PA's scripts/tests are not $REF (was the swap commit pulled early?)"; exit 1; }
echo "repo guards: scripts/tests = $REF (the swap commit NOT pulled yet): yes"
for f in "$LIVE" "$B"; do [ -s "$f" ] || { echo "P6R RESULT: STOP - missing or empty: $f"; exit 1; }; done
rb=$(find ~/bible-db -maxdepth 1 -name 'bible_pre_edition_upgrade_*' | wc -l); echo "existing bible_pre_edition_upgrade_* files: $rb (expect 0)"
[ "$rb" = 0 ] || { echo "P6R RESULT: STOP - a rollback-named file already exists"; exit 1; }
b0=$(h "$B"); echo "built sha256: $b0 (expect $XB)"; [ "$b0" = "$XB" ] || { echo "P6R RESULT: STOP - built is not the pinned copy"; exit 1; }
for x in -journal -wal -shm; do [ -e "$B$x" ] && { echo "P6R RESULT: STOP - side file $B$x"; exit 1; }; done
hm=$(date -u +%H%M); echo "UTC time $hm - P6B must run outside 1300-1430 (it checks again, twice)"
echo "P6R RESULT: DONE - JP: DISABLE the web app now, then paste P6B"; exit 0
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
