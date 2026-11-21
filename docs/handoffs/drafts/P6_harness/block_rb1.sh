set +H
L=~/edition_upgrade_runs/rb1_rollback_window.log
if [ -e "$L" ]; then echo "RB1 RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
export TZ=UTC
echo "RB1 - ROLLBACK, part 1, INSIDE ITS OWN WINDOW (JP has just DISABLED the web app after RB0 DONE): still-file hold, then two renames back (charter 7; DESIGN 9.213 (ii), 9.228) - WRITES: two renames in ~/bible-db + this log - WINDOW START (this paste) $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "RB1 RESULT: STOP - cannot cd to ~/bible-db; nothing moved"; exit 1; }
LIVE=~/bible-db/bible.db
D=~/edition_upgrade_runs/p6_swap
HOLD_N=7; HOLD_S=5                                                         # the same still-file hold as P6B (DESIGN 9.228)
h() { cut -d' ' -f1 <<< "$(sha256sum < "$1")"; }
nofile() { [ -s "$1" ] && return 1; return 0; }                            # true when the file is missing or empty (no bang in a pasted block)
inwin() { hm=$(date -u +%H%M); echo "UTC time $hm (STOP inside 1300-1430)"; [ "$hm" -ge 1300 ] && [ "$hm" -le 1430 ]; }
# --- guard: RB0 finished (every other pre-Disable read is RB0's) ---
grep -q "^RB0 RESULT: DONE" ~/edition_upgrade_runs/rb0_rollback_ready.log || { echo "RB1 RESULT: STOP - RB0 has not finished DONE; nothing moved"; exit 1; }
RB=$(sed -n 1p "$D/rollback.txt"); X0=$(sed -n 2p "$D/rollback.txt")   # read and checked by RB0
OUT=~/bible-db/bible_pre_edition_upgrade_backedout_$(date -u +%Y%m%d).db  # the swapped-in file is KEPT; a bible_pre_* name, so the nightly backup skips it (backup_db.py :63; reviewer D1)
inwin && { echo "RB1 RESULT: STOP - inside the 13:00-14:30 UTC window; nothing moved"; exit 1; }
echo "=== still-file hold on live: $HOLD_N reads, $HOLD_S s apart ==="
st0=$(stat -c '%s %Y' "$LIVE"); ok=1
for i in $(seq 1 "$HOLD_N"); do
  st=$(stat -c '%s %Y' "$LIVE"); sf=""; for x in -journal -wal -shm; do [ -e "$LIVE$x" ] && sf="$sf $x"; done
  echo "  read $i $(date -u +%T): size+time $st${sf:+ - SIDE FILE$sf}"
  [ "$st" = "$st0" ] && [ -z "$sf" ] || ok=0
  [ "$i" -lt "$HOLD_N" ] && sleep "$HOLD_S"
done
[ "$ok" = 1 ] || { echo "RB1 RESULT: STOP - live is still being written; nothing moved - is the web app disabled?"; exit 1; }
n0=$(h "$LIVE"); echo "the swapped-in live sha256 before the move back: $n0 ($(stat -c '%s bytes, last write %y' "$LIVE"))"
[ -e "$OUT" ] && { echo "RB1 RESULT: STOP - $OUT exists; nothing moved"; exit 1; }
inwin && { echo "RB1 RESULT: STOP - the reads ran into the 13:00-14:30 UTC window; nothing moved"; exit 1; }
echo "=== the move back - $(date -u +%T) ==="
mv -n "$LIVE" "$OUT"; m1=$?
if [ "$m1" != 0 ] || [ -e "$LIVE" ] || nofile "$OUT"; then
  [ -e "$LIVE" ] || { [ -s "$OUT" ] && mv -n "$OUT" "$LIVE"; }
  echo "RB1 RESULT: STOP - the first rename did not land cleanly (mv exit $m1); live is $([ -s "$LIVE" ] && echo 'in place' || echo 'NOT IN PLACE - TO THE RULING CHAT NOW')"; exit 1
fi
echo "1. the swapped-in live renamed to $OUT (kept)"
mv -n "$RB" "$LIVE"; m2=$?
if [ "$m2" != 0 ] || nofile "$LIVE" || [ -e "$RB" ]; then
  [ -e "$LIVE" ] || mv -n "$OUT" "$LIVE"
  echo "RB1 RESULT: STOP - the second rename did not land cleanly (mv exit $m2); the first was put back: live is $([ "$(h "$LIVE")" = "$n0" ] && echo 'the swapped-in file again' || echo 'NOT the swapped-in file - TO THE RULING CHAT NOW')"; exit 1
fi
echo "2. the pre-swap file renamed back to $LIVE - $(date -u +%T)"
bad=0
x1=$(h "$LIVE"); echo "bible.db sha256 = live's just before the swap: $([ "$x1" = "$X0" ] && echo yes || echo NO)"; [ "$x1" = "$X0" ] || bad=1
o1=$(h "$OUT"); echo "the kept swapped-in file's sha256 = before the move back: $([ "$o1" = "$n0" ] && echo yes || echo NO)"; [ "$o1" = "$n0" ] || bad=1
for x in -journal -wal -shm; do for f in "$LIVE" "$OUT"; do [ -e "$f$x" ] && { echo "CHECK: side file $f$x"; bad=1; }; done; done
[ "$bad" = 0 ] || { echo "RB1 RESULT: CHECK - lines above; the site stays disabled; to the ruling chat before anything else"; exit 1; }
echo "Rows the site wrote into the swapped-in bible.db since P6B stay in $OUT (charter 7: lost to live by a rollback; kept on disk)."
echo "RB1 RESULT: DONE - rolled back at $(date -u +%FT%TZ); JP: ENABLE the web app, then RELOAD it, then paste RB2"; exit 0
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
