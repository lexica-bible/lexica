set +H
L=~/edition_upgrade_runs/rb0_rollback_ready.log
if [ -e "$L" ]; then echo "RB0 RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
export TZ=UTC
export GIT_OPTIONAL_LOCKS=0
echo "RB0 - ROLLBACK, READY (only if the ruling chat rules a rollback; CC has pushed the revert of the swap commit; PA must NOT pull it yet): the checks before JP's Disable (DESIGN 9.228) - READ-ONLY; site UP; writes only this log - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "RB0 RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
LIVE=~/bible-db/bible.db
D=~/edition_upgrade_runs/p6_swap
h() { cut -d' ' -f1 <<< "$(sha256sum < "$1")"; }
grep -q "^P6B RESULT: DONE" ~/edition_upgrade_runs/p6b_swap_window.log || { echo "RB0 RESULT: STOP - there is no finished swap to roll back (P6B not DONE)"; exit 1; }
[ -s "$D/rollback.txt" ] || { echo "RB0 RESULT: STOP - $D/rollback.txt missing"; exit 1; }
RB=$(sed -n 1p "$D/rollback.txt"); X0=$(sed -n 2p "$D/rollback.txt")   # the rollback file P6B made, and live's sha just before the swap
case "$RB" in "$HOME"/bible-db/bible_pre_edition_upgrade_*.db) ;; *) echo "RB0 RESULT: STOP - unexpected rollback name: $RB"; exit 1;; esac
s=$(git log -1 --format=%s); echo "PA HEAD subject: $s"
case "$s" in "edition upgrade: THE SWAP COMMIT"*) echo "PA is on the swap commit (the revert NOT pulled yet): yes";; *) echo "RB0 RESULT: STOP - PA's HEAD is not the swap commit (the revert pulled early, or the swap never deployed) - roll both or neither (charter 7)"; exit 1;; esac
for f in "$LIVE" "$RB"; do [ -s "$f" ] || { echo "RB0 RESULT: STOP - missing or empty: $f"; exit 1; }; done
for x in -journal -wal -shm; do [ -e "$RB$x" ] && { echo "RB0 RESULT: STOP - side file $RB$x"; exit 1; }; done
r0=$(h "$RB"); echo "the rollback file's sha256 = live's just before the swap: $([ "$r0" = "$X0" ] && echo yes || echo NO) ($r0)"
[ "$r0" = "$X0" ] || { echo "RB0 RESULT: STOP - the rollback file is not the pre-swap live"; exit 1; }
n=$(find ~/bible-db -maxdepth 1 -name 'bible_pre_edition_upgrade_backedout_*' | wc -l); echo "existing bible_pre_edition_upgrade_backedout_* files: $n (expect 0)"
[ "$n" = 0 ] || { echo "RB0 RESULT: STOP - a backed-out file already exists"; exit 1; }
hm=$(date -u +%H%M); echo "UTC time $hm - RB1 must run outside 1300-1430 (it checks again, twice)"
echo "RB0 RESULT: DONE - JP: DISABLE the web app now, then paste RB1"; exit 0
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
