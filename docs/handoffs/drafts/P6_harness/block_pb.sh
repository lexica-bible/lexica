set +H
L=~/edition_upgrade_runs/pb_putback_window.log
if [ -e "$L" ]; then echo "PB RESULT: STOP - log already exists (already ran? it is kept as is): $L - leave the web app as it is; to the ruling chat now"; else
( set -uo pipefail
export TZ=UTC
export GIT_OPTIONAL_LOCKS=0
REF=d34d6723                                                               # the pre-swap code: P6A / P6R / P6B hold PA's scripts + tests to it; ai.py is the same there
echo "PB - PUT-BACK, FILE ONLY (DESIGN 9.229 (1); only if the ruling chat rules it; for when PA is NOT on the swap commit). The web app is DISABLED: still disabled after P6B, or JP has just DISABLED it after a P6C failure. Still-file hold, then the pre-swap file back as bible.db - WRITES: at most two renames in ~/bible-db + this log; NO deploy - WINDOW START (this paste) $(date -u +%FT%TZ) - PA HEAD $(git -C ~/bible-db log -1 --format=%h)"
stop() { echo "PB RESULT: STOP - $1; nothing moved - leave the web app as it is (no Enable, no Disable); to the ruling chat now"; exit 1; }
cd ~/bible-db || stop "cannot cd to ~/bible-db"
LIVE=~/bible-db/bible.db
B=~/bible-db/bible_edupg_test_built_20261102.db
R=~/edition_upgrade_runs
D=$R/p6_swap
XB=d2c8603b4700d6dce089b688c5e00e8a3fdec879eea96bef5a6ce7cd09ca1523       # built full sha256 = P6's pin (DESIGN 9.222 (1)); printed for the record only
HOLD_N=7; HOLD_S=5                                                         # the same still-file hold as P6B and RB1 (DESIGN 9.228)
h() { cut -d' ' -f1 <<< "$(sha256sum < "$1")"; }
gone() { [ -e "$1" ] && return 1; return 0; }                              # true when nothing at all sits at the path
nofile() { [ -s "$1" ] && return 1; return 0; }                            # true when the file is missing or empty (no bang in a pasted block)
inwin() { hm=$(date -u +%H%M); echo "UTC time $hm (STOP inside 1300-1430)"; [ "$hm" -ge 1300 ] && [ "$hm" -le 1430 ]; }
sidef() { sf=""; for x in -journal -wal -shm; do [ -e "$1$x" ] && sf="$sf $x"; done; echo "$sf"; }
# --- guards: P6B ran and wrote its rollback note; PA is NOT on the swap commit ---
[ -s "$R/p6b_swap_window.log" ] || stop "P6B has not run: there is nothing to put back"
p=$(grep '^P6B RESULT:' "$R/p6b_swap_window.log" | tail -1); echo "P6B's result line: ${p:-none (P6B did not finish)}"
[ -e "$R/p6c_swap_deploy.log" ] && { p=$(grep '^P6C RESULT:' "$R/p6c_swap_deploy.log" | tail -1); echo "P6C's result line: ${p:-none (P6C did not finish)}"; }
[ -s "$D/rollback.txt" ] || stop "$D/rollback.txt is missing: P6B stopped before its first rename"
RB=$(sed -n 1p "$D/rollback.txt"); X0=$(sed -n 2p "$D/rollback.txt")   # the rollback file P6B named, and live's sha just before the swap
case "$RB" in "$HOME"/bible-db/bible_pre_edition_upgrade_*.db) ;; *) stop "unexpected rollback name: $RB";; esac
case "$X0" in *[^0-9a-f]*) stop "rollback.txt line 2 is not a sha256";; esac
[ "${#X0}" = 64 ] || stop "rollback.txt line 2 is not a sha256"
echo "rollback.txt: $RB / $X0"
s=$(git log -1 --format=%s); echo "PA HEAD subject: $s"
[ -n "$s" ] || stop "git gave no HEAD subject: the code PA is on cannot be read"
case "$s" in "edition upgrade: THE SWAP COMMIT"*) stop "PA is ON the swap commit: this block is file-only; that case is RB0 / RB1 / RB2 (roll both or neither, charter 7)";; esac
a=no; git merge-base --is-ancestor "$REF" HEAD && a=yes
d=no; git diff --quiet "$REF" HEAD -- scripts tests ai.py && d=yes
us=$(git status --porcelain --untracked-files=no -- scripts tests ai.py); rs=$?; u=$(grep -c . <<< "$us")
echo "PA's code against the pre-swap code $REF (the same three tests PB0 made before the swap): $REF is in HEAD's history: $a; scripts / tests / ai.py same as $REF: $d; git status exit $rs, uncommitted changes in them: $u (expect yes, yes, 0, 0)"
[ "$a" = yes ] && [ "$d" = yes ] && [ "$rs" = 0 ] && [ "$u" = 0 ] || stop "PA's scripts / tests / ai.py are NOT the pre-swap code $REF (the line above says which test missed): a file-only put-back would roll one and not both (charter 7)"
echo "PA is NOT on the swap commit, and its scripts / tests / ai.py = the pre-swap code $REF: yes"
OUT=~/bible-db/bible_pre_edition_upgrade_putback_$(date -u +%Y%m%d).db   # what sits at bible.db is KEPT; a bible_pre_* name, so the nightly backup skips it (backup_db.py :63; reviewer D1 on RB1)
[ "$RB" = "$OUT" ] && stop "the rollback name and the keep name are the same"
[ -e "$OUT" ] && stop "$OUT exists"
inwin && stop "inside the 13:00-14:30 UTC backup / health window"
# --- what is on disk ---
haveL=0; [ -e "$LIVE" ] && haveL=1
haveR=0; [ -s "$RB" ] && haveR=1
echo "on disk: bible.db $([ "$haveL" = 1 ] && echo present || echo ABSENT); the rollback file $([ "$haveR" = 1 ] && echo present || echo ABSENT); the built path $([ -e "$B" ] && echo present || echo absent)"
[ -e "$RB" ] && [ "$haveR" = 0 ] && stop "an EMPTY file sits at the rollback name"
[ -n "$(sidef "$RB")" ] && stop "side file beside the rollback file:$(sidef "$RB")"
[ "$haveL" = 0 ] && [ -n "$(sidef "$LIVE")" ] && stop "no bible.db, but a side file sits beside its name:$(sidef "$LIVE")"
if [ "$haveR" = 0 ]; then
  [ "$haveL" = 0 ] && stop "NEITHER bible.db NOR the rollback file is there - NOT IN PLACE"
  [ "$(h "$LIVE")" = "$X0" ] && stop "there is no rollback file and bible.db is ALREADY the pre-swap file (sha = rollback.txt line 2): nothing to put back"
  stop "there is no rollback file and bible.db is NOT the pre-swap file"
fi
r0=$(h "$RB"); echo "the rollback file's sha256 = live's just before the swap: $([ "$r0" = "$X0" ] && echo yes || echo NO) ($r0)"
[ "$r0" = "$X0" ] || stop "the rollback file is not the pre-swap live"
n0=""
if [ "$haveL" = 1 ]; then
  echo "=== still-file hold on bible.db: $HOLD_N reads, $HOLD_S s apart - size + last write unchanged, no -journal / -wal / -shm ==="
  st0=$(stat -c '%s %Y' "$LIVE"); ok=1
  for i in $(seq 1 "$HOLD_N"); do
    st=$(stat -c '%s %Y' "$LIVE"); sf=$(sidef "$LIVE")
    echo "  read $i $(date -u +%T): size+time $st${sf:+ - SIDE FILE$sf}"
    [ "$st" = "$st0" ] && [ -z "$sf" ] || ok=0
    [ "$i" -lt "$HOLD_N" ] && sleep "$HOLD_S"
  done
  [ "$ok" = 1 ] || stop "bible.db is still being written (size/time moved or a side file) - is the web app disabled?"
  echo "bible.db held still for the whole hold: yes"
  n0=$(h "$LIVE"); echo "what sits at bible.db now: sha256 $n0 ($(stat -c '%s bytes, last write %y' "$LIVE")) - built's pinned bytes: $([ "$n0" = "$XB" ] && echo yes || echo 'no (expected once the site has written to it)')$([ -s "$LIVE" ] || echo ' - an EMPTY file: kept all the same')"
  [ "$n0" = "$X0" ] && stop "bible.db is ALREADY the pre-swap file while the rollback file is also there"
  [ "$(stat -c '%s %Y' "$LIVE")" = "$st0" ] || stop "bible.db changed during the read"
  [ -n "$(sidef "$LIVE")" ] && stop "side file beside bible.db:$(sidef "$LIVE")"
else
  echo "no file at bible.db: no hold to make, nothing to keep"
fi
inwin && stop "the reads ran into the 13:00-14:30 UTC window"
# --- the put-back: at most two renames on one device; a miss on the second puts the first one back ---
echo "=== the put-back - $(date -u +%T) ==="
if [ "$haveL" = 1 ]; then
  mv -n "$LIVE" "$OUT"; m1=$?
  if [ "$m1" != 0 ] || [ -e "$LIVE" ] || gone "$OUT"; then
    [ -e "$LIVE" ] || { [ -e "$OUT" ] && mv -n "$OUT" "$LIVE"; }
    echo "PB RESULT: STOP - the first rename did not land cleanly (mv exit $m1); bible.db is $([ -e "$LIVE" ] && [ "$(h "$LIVE")" = "$n0" ] && echo 'what sat there before, in place' || echo 'NOT what sat there before') - leave the web app as it is (no Enable, no Disable); to the ruling chat now"; exit 1
  fi
  echo "1. what sat at bible.db renamed to $OUT (kept)"
else
  echo "1. (nothing sat at bible.db)"
fi
mv -n "$RB" "$LIVE"; m2=$?
if [ "$m2" != 0 ] || nofile "$LIVE" || [ -e "$RB" ]; then
  [ -e "$LIVE" ] || { [ "$haveL" = 1 ] && mv -n "$OUT" "$LIVE"; }
  if [ "$haveL" = 1 ]; then w=$([ -e "$LIVE" ] && [ "$(h "$LIVE")" = "$n0" ] && echo 'the first was put back: bible.db is what sat there before' || echo 'bible.db is NOT what sat there before'); else w=$([ -e "$LIVE" ] && echo 'bible.db is NOT as it was (a file is there now)' || echo 'bible.db is absent, as before'); fi
  [ -s "$LIVE" ] && [ "$(h "$LIVE")" = "$X0" ] && w="bible.db IS the pre-swap file (sha = rollback.txt line 2): the rename landed although it did not report clean; the rollback name $([ -e "$RB" ] && echo 'still exists' || echo 'is gone')"
  echo "PB RESULT: STOP - the second rename did not land cleanly (mv exit $m2); $w - leave the web app as it is (no Enable, no Disable); to the ruling chat now"; exit 1
fi
echo "2. the pre-swap file renamed back to $LIVE - $(date -u +%T)"
# --- after: every miss = CHECK (the files stay as they are) ---
bad=0
x1=$(h "$LIVE"); echo "bible.db sha256 = live's just before the swap (rollback.txt line 2): $([ "$x1" = "$X0" ] && echo yes || echo NO) ($x1)"; [ "$x1" = "$X0" ] || bad=1
if [ "$haveL" = 1 ]; then o1=$(h "$OUT"); echo "the kept file's sha256 = what sat at bible.db before the put-back: $([ "$o1" = "$n0" ] && echo yes || echo NO)"; [ "$o1" = "$n0" ] || bad=1; fi
[ -e "$RB" ] && { echo "CHECK: the rollback name still exists"; bad=1; }
for f in "$LIVE" "$OUT"; do [ -n "$(sidef "$f")" ] && { echo "CHECK: side file beside $f:$(sidef "$f")"; bad=1; }; done
echo "the built path after: $([ -e "$B" ] && echo present || echo 'absent (a new swap needs a ruled block first)')"
[ "$bad" = 0 ] || { echo "PB RESULT: CHECK - lines above; the site stays disabled; to the ruling chat before anything else"; exit 1; }
[ "$haveL" = 1 ] && echo "What sat at bible.db, with anything the site wrote into it, stays in $OUT (kept on disk; not in live)."
echo "PB RESULT: DONE - the pre-swap file is back as bible.db at $(date -u +%FT%TZ); JP: ENABLE the web app, then RELOAD it. Do NOT run deploy.sh: no deploy until CC has pushed the revert of the swap commit and the ruling chat has ruled. This log to the ruling chat now"; exit 0
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
