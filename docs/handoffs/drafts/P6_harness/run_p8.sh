# P8 tests (the snapshot check on a fresh copy of the swapped live). Homes: mkhome_p8.sh - the REAL snapshot_surface_fill.py and
# restore_surface_fill.py (pins set to the made-up files' by one test commit), a made-up 4,411-slot fill.   usage (WSL): bash run_p8.sh > tests_p8.out
set -uo pipefail
T=/mnt/c/Users/JP/projects/bible-db/docs/handoffs/drafts/P6_harness
G=~/gatep8; mkdir -p $G
hd() { echo; echo "=============== $* ==============="; }
mk() { bash "$T/mkhome_p8.sh" "$1" "${2:-none}" > "$1.mk" 2>&1 || { cat "$1.mk"; exit 1; }; }
run() { ( cd "$1" && HOME="$1" bash "$1/p8.sh" ) 2>&1 | grep -v '^$'; }
sha() { sha256sum < "$1" | cut -c1-16; }
state() { echo "copy in the run folder: $([ -e $1/edition_upgrade_runs/p8_snapshot_check/live_copy.db ] && echo KEPT || echo absent); bible.db bytes unchanged: $([ "$(sha $1/bible-db/bible.db)" = "$2" ] && echo yes || echo NO); side files in ~/bible-db: $(ls $1/bible-db | grep -c -e '-journal' -e '-wal' -e '-shm')"; }
echo "# P8 tests ($(date -u +%FT%TZ)); block $(sha $T/block_p8.sh)"

hd "A1 clean -> PASS, the copy removed (whole log shown); a second paste -> STOP; no planted text in the log or outputs"
H=$G/a1; mk $H; tail -1 $H.mk; L0=$(sha $H/bible-db/bible.db)
run $H
run $H | tail -2
echo "leak grep (planted verse / word text): $(cat $H/edition_upgrade_runs/p8_snapshot_check_*.log $H/edition_upgrade_runs/p8_snapshot_check/*.out | grep -c SECRET)"
state $H $L0; echo "run folder holds: $(ls $H/edition_upgrade_runs/p8_snapshot_check | tr '\n' ' ')"
echo "fixture files unchanged (sha256sum -c): $(cd $H/bible-db/tests/fixtures/rebuild_trap && sha256sum -c --quiet *.sha256 && echo yes)"

hd "B1 a fill slot's word changed on live after the freeze -> the check reads STALE on the copy -> CHECK, the copy KEPT"
H=$G/b1; mk $H stale; L0=$(sha $H/bible-db/bible.db); run $H | grep -E "slot \(|STOPPED|: NO|RESULT|^exit=|KEPT"; state $H $L0
hd "B2 the copy's words digest is not P7's -> STOP before the check, the copy KEPT"
H=$G/b2; mk $H; L0=$(sha $H/bible-db/bible.db); sed -i 's/^XW="[^"]*"/XW="626309 d95acb5d4be4"/' $H/p8.sh; run $H | tail -3; state $H $L0; echo "check output made: $(ls $H/edition_upgrade_runs/p8_snapshot_check | grep -c check_)"
hd "B3 home above the bound -> STOP, nothing copied"
H=$G/b3; mk $H; L0=$(sha $H/bible-db/bible.db); sed -i 's/^XHOME_MAX=8300000/XHOME_MAX=1      /' $H/p8.sh; run $H | tail -3; state $H $L0; echo "run folder made: $([ -e $H/edition_upgrade_runs/p8_snapshot_check ] && echo yes || echo no)"
hd "B4 inside the 13:00-14:30 window (TEST copy: the window moved to bracket now) -> STOP, nothing copied"
H=$G/b4; mk $H; NOW=$(date -u +%H%M); LO=$(printf %04d $((10#$NOW - 1))); HI=$(printf %04d $((10#$NOW + 1)))
sed -i "s/-ge 1300 \] \&\& \[ \"\$hm\" -le 1430/-ge $LO ] \&\& [ \"\$hm\" -le $HI/" $H/p8.sh; run $H | tail -3
hd "B5 the run folder already there -> STOP, nothing copied"
H=$G/b5; mk $H; mkdir -p $H/edition_upgrade_runs/p8_snapshot_check; run $H | tail -2
hd "B6 the frozen snapshot not the pinned bytes -> STOP, nothing copied"
H=$G/b6; mk $H; printf 'x\n' >> $H/bible-db/tests/fixtures/rebuild_trap/abp_surface_fill_20261115.tsv; run $H | tail -3
hd "B7 the pre-fill copy not the recorded one -> STOP, nothing copied"
H=$G/b7; mk $H; sed -i 's/^XB4=[0-9a-f]*/XB4=0000/' $H/p8.sh; run $H | tail -3
hd "B8 an uncommitted edit under scripts -> STOP, nothing copied"
H=$G/b8; mk $H; echo "# x" >> $H/bible-db/scripts/health_check.py; run $H | tail -2
hd "B9 the control cannot fail (src made the same as live) -> CHECK control-src, the copy KEPT"
H=$G/b9; mk $H srcsame; L0=$(sha $H/bible-db/bible.db); run $H | grep -E "control|RESULT|^exit=|KEPT"; state $H $L0
hd "B10 the report's .sha256 missing -> STOP, nothing copied"
H=$G/b10; mk $H; rm $H/bible-db/tests/fixtures/rebuild_trap/restore_report_20261115.tsv.sha256; run $H | tail -2
hd "B11 src not the recorded 11/1 copy -> STOP, nothing copied"
H=$G/b11; mk $H; sed -i 's/^XSRC=[0-9a-f]*/XSRC=0000/' $H/p8.sh; run $H | tail -3
hd "B12 the window reached between the first time check and the copy (TEST copy: only the SECOND check's window moved to bracket now) -> STOP, nothing copied"
H=$G/b12; mk $H; NOW=$(date -u +%H%M); LO=$(printf %04d $((10#$NOW - 1))); HI=$(printf %04d $((10#$NOW + 1)))
sed -i "s/^inwin \&\& { echo \"P8 RESULT: STOP - the reads ran/hm2() { hm=\$(date -u +%H%M); echo \"UTC time \$hm (second check)\"; [ \"\$hm\" -ge $LO ] \&\& [ \"\$hm\" -le $HI ]; }; hm2 \&\& { echo \"P8 RESULT: STOP - the reads ran/" $H/p8.sh; run $H | tail -3; echo "run folder made: $([ -e $H/edition_upgrade_runs/p8_snapshot_check ] && echo yes || echo no)"
# not tested: the "copy could not be removed" ending (a watcher that made the run folder read-only lost the race on a first try; no deterministic way without changing the tested line)
