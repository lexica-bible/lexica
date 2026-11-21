set +H
L=~/edition_upgrade_runs/p6b_swap_window.log
if [ -e "$L" ]; then echo "P6B RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
export TZ=UTC
export PYTHONDONTWRITEBYTECODE=1
echo "P6B - the swap, part B, INSIDE THE WINDOW (JP has just DISABLED the web app): still-file hold, live read in place, the two renames (DESIGN 9.213 P6, 9.224, 9.228) - WRITES: two renames in ~/bible-db (live -> the rollback name, built -> bible.db) + the run folder + this log - WINDOW START (this paste) $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "P6B RESULT: STOP - cannot cd to ~/bible-db; nothing moved"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db
LIVE=~/bible-db/bible.db
R=~/edition_upgrade_runs
D=$R/p6_swap
XB=d2c8603b4700d6dce089b688c5e00e8a3fdec879eea96bef5a6ce7cd09ca1523       # built full sha256 = P6's pin (DESIGN 9.222 (1)); read in P6R before Disable
XP=__XP__                                                                  # sha256 of the check program (the same file P6A ran)
HOLD_N=7; HOLD_S=5                                                         # still-file hold: 7 reads 5 s apart = 30 s (DESIGN 9.228; CC's figure)
EU() { PYTHONIOENCODING=utf-8 python3 "$@"; }
h() { cut -d' ' -f1 <<< "$(sha256sum < "$1")"; }
nofile() { [ -s "$1" ] && return 1; return 0; }                            # true when the file is missing or empty (no bang in a pasted block)
inwin() { hm=$(date -u +%H%M); echo "UTC time $hm (STOP inside 1300-1430)"; [ "$hm" -ge 1300 ] && [ "$hm" -le 1430 ]; }
# --- guard: P6R finished (every other pre-Disable read is P6R's) ---
grep -q "^P6R RESULT: DONE" "$R/p6r_swap_ready.log" || { echo "P6B RESULT: STOP - P6R has not finished DONE; nothing moved"; exit 1; }
inwin && { echo "P6B RESULT: STOP - inside the 13:00-14:30 UTC backup / health window; nothing moved"; exit 1; }
case "$(git log -1 --format=%s)" in "edition upgrade: THE SWAP COMMIT"*) echo "P6B RESULT: STOP - PA has already pulled the swap commit (no deploy may run between P6R and the swap); nothing moved"; exit 1;; esac
echo "=== still-file hold on live: $HOLD_N reads, $HOLD_S s apart - size + last write unchanged, no -journal / -wal / -shm ==="
st0=$(stat -c '%s %Y' "$LIVE"); ok=1
for i in $(seq 1 "$HOLD_N"); do
  st=$(stat -c '%s %Y' "$LIVE"); sf=""; for x in -journal -wal -shm; do [ -e "$LIVE$x" ] && sf="$sf $x"; done
  echo "  read $i $(date -u +%T): size+time $st${sf:+ - SIDE FILE$sf}"
  [ "$st" = "$st0" ] && [ -z "$sf" ] || ok=0
  [ "$i" -lt "$HOLD_N" ] && sleep "$HOLD_S"
done
[ "$ok" = 1 ] || { echo "P6B RESULT: STOP - live is still being written (size/time moved or a side file); nothing moved - is the web app disabled?"; exit 1; }
echo "live held still for the whole hold: yes"
echo "=== live read in place, read-only: LIVESRC digests, every table vs src, what the swap drops (the program, read once) ==="
EU -c 'import hashlib, sys
p, x = sys.argv[1], sys.argv[2]
b = open(p, "rb").read()
h = hashlib.sha256(b).hexdigest()
print("check.py sha256 as run: %s (expect %s)" % (h, x), flush=True)
h == x or sys.exit(4)
sys.path[0] == "" and sys.path.pop(0)
sys.argv = [p] + sys.argv[3:]
exec(compile(b, p, "exec"), {"__name__": "__main__"})' "$D/check.py" "$XP" "MODE=live" "LIVE=$LIVE" "B=$B" "D=$D" "REPO=$HOME/bible-db" < /dev/null; r=$?
echo "check exit $r (expect 0; 2 = a STOP inside; 4 = not the pinned bytes)"
[ "$r" = 0 ] || { echo "P6B RESULT: STOP - the live read stopped (lines above); nothing moved"; exit 1; }
st1=$(stat -c '%s %Y' "$LIVE"); [ "$st1" = "$st0" ] || { echo "P6B RESULT: STOP - live changed during the read; nothing moved"; exit 1; }
for x in -journal -wal -shm; do [ -e "$LIVE$x" ] && { echo "P6B RESULT: STOP - side file $LIVE$x; nothing moved"; exit 1; }; done
l0=$(h "$LIVE"); echo "LIVE FULL SHA256 just before the move: $l0 ($(stat -c '%s bytes, last write %y' "$LIVE"))"
RB=~/bible-db/bible_pre_edition_upgrade_$(date -u +%Y%m%d).db
[ -e "$RB" ] && { echo "P6B RESULT: STOP - $RB exists; nothing moved"; exit 1; }
inwin && { echo "P6B RESULT: STOP - the reads ran into the 13:00-14:30 UTC window; nothing moved"; exit 1; }
printf '%s\n%s\n' "$RB" "$l0" > "$D/rollback.txt" || { echo "P6B RESULT: STOP - cannot write $D/rollback.txt; nothing moved"; exit 1; }
# --- the move: two renames on one device; a miss between them puts the first one back ---
echo "=== the move - $(date -u +%T) ==="
mv -n "$LIVE" "$RB"; m1=$?
if [ "$m1" != 0 ] || [ -e "$LIVE" ] || nofile "$RB"; then
  [ -e "$LIVE" ] || { [ -s "$RB" ] && mv -n "$RB" "$LIVE"; }
  echo "P6B RESULT: STOP - the first rename did not land cleanly (mv exit $m1); live is $([ -s "$LIVE" ] && echo 'in place' || echo 'NOT IN PLACE - TO THE RULING CHAT NOW')"; exit 1
fi
echo "1. live renamed to $RB"
mv -n "$B" "$LIVE"; m2=$?
if [ "$m2" != 0 ] || nofile "$LIVE" || [ -e "$B" ]; then
  [ -e "$LIVE" ] || mv -n "$RB" "$LIVE"
  echo "P6B RESULT: STOP - the second rename did not land cleanly (mv exit $m2); the first was put back: live is $([ "$(h "$LIVE")" = "$l0" ] && echo 'the pre-swap file again' || echo 'NOT the pre-swap file - TO THE RULING CHAT NOW')"; exit 1
fi
echo "2. built renamed to $LIVE - $(date -u +%T)"
# --- after: every miss = CHECK (the files stay as they are; to the ruling chat before anything else) ---
bad=0
n1=$(h "$LIVE"); echo "bible.db sha256 = built's pin: $([ "$n1" = "$XB" ] && echo yes || echo NO) ($n1)"; [ "$n1" = "$XB" ] || bad=1
r1=$(h "$RB"); echo "the rollback file's sha256 = live's just before: $([ "$r1" = "$l0" ] && echo yes || echo NO)"; [ "$r1" = "$l0" ] || bad=1
echo "the rollback file: $(stat -c '%s bytes, last write %y' "$RB") (= live's before: $([ "$(stat -c '%s %Y' "$RB")" = "$st0" ] && echo yes || echo NO))"
[ -e "$B" ] && { echo "CHECK: the built path still exists"; bad=1; }
for x in -journal -wal -shm; do for f in "$LIVE" "$RB"; do [ -e "$f$x" ] && { echo "CHECK: side file $f$x"; bad=1; }; done; done
[ "$bad" = 0 ] || { echo "P6B RESULT: CHECK - lines above; the site stays disabled; to the ruling chat before anything else"; exit 1; }
echo "Notes made after the P3b read (11/21 05:21Z) are not covered by it (DESIGN 9.220)."
echo "P6B RESULT: DONE - swapped at $(date -u +%FT%TZ); JP: ENABLE the web app, then RELOAD it, then paste P6C"; exit 0
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
