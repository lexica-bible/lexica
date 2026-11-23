set +H
D=~/edition_upgrade_runs/kjv_shift_long_20261123
if [ -e "$D/started" ]; then echo "KJV LONG: STOP - already ran, log kept: $D"; else
mkdir -p "$D"
A="$D/try_$(date -u +%H%M%S).log"
( set -uo pipefail
  REF=77f1b903
  XP=6499bdf4b826157a4a64622cb1e66ddfdb8f8c0ba14746809fc6d62573506379
  P=scripts/apply_kjv_shift_20261123.py
  export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
  echo "KJV LONG - 21 verses, 405 rows - REF $REF - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
  cd ~/bible-db || { echo "KJV LONG: STOP - no ~/bible-db"; exit 1; }
  t=$(date -u +%H%M)
  if [ "$((10#$t))" -ge 1230 ] && [ "$((10#$t))" -lt 1430 ]; then echo "KJV LONG: STOP - too near the 13:00-14:30 UTC window; nothing written"; exit 1; fi
  git merge-base --is-ancestor "$REF" HEAD || { echo "KJV LONG: STOP - PA does not have $REF (run deploy.sh); nothing written"; exit 1; }
  git diff --quiet "$REF" HEAD -- scripts tests || { echo "KJV LONG: STOP - scripts or tests changed since $REF; nothing written"; exit 1; }
  s=$(sha256sum "$P"); s=${s%% *}
  [ "$s" = "$XP" ] || { echo "KJV LONG: STOP - the program is not the cleared file ($s); nothing written"; exit 1; }
  echo "=== 1 CHECK (read-only) ==="
  python3 -u "$P" check || { echo "KJV LONG RESULT: STOP at check - nothing written"; exit 1; }
  : > "$D/started"
  echo "=== 2 APPLY (one all-or-nothing step) ==="
  python3 -u "$P" apply || { echo "KJV LONG RESULT: STOP at apply - nothing saved"; exit 1; }
  echo "=== 3 AFTER (read-only) ==="
  python3 -u "$P" after || { echo "KJV LONG RESULT: CHECK - written, the after-read is not clean; run nothing else, log to the ruling chat. Way back: python3 $P undo"; exit 1; }
  echo "way back, if ruled: cd ~/bible-db && python3 $P undo"
  echo "KJV LONG RESULT: DONE"
) 2>&1 | tee "$A"; echo "exit=${PIPESTATUS[0]}"
fi
