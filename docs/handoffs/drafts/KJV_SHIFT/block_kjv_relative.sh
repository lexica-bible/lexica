set +H
D=~/edition_upgrade_runs/kjv_shift_relative_20261125
if [ -e "$D/started" ]; then echo "KJV RELATIVE: STOP - already ran, log kept: $D"; else
mkdir -p "$D"
A="$D/try_$(date -u +%H%M%S).log"
( set -uo pipefail
  REF=9d32ae0f
  XP=f984616408a01b0af737f3da478fee678bf9e88cdcc195108fd5c8fba4d0e9a3
  P=scripts/apply_kjv_shift_short_20261124.py
  export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
  echo "KJV RELATIVE - 89 verses, 200 rows - REF $REF - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
  cd ~/bible-db || { echo "KJV RELATIVE: STOP - no ~/bible-db"; exit 1; }
  t=$(date -u +%H%M)
  if [ "$((10#$t))" -ge 1230 ] && [ "$((10#$t))" -lt 1430 ]; then echo "KJV RELATIVE: STOP - too near the 13:00-14:30 UTC window; nothing written"; exit 1; fi
  git merge-base --is-ancestor "$REF" HEAD || { echo "KJV RELATIVE: STOP - PA does not have $REF (run deploy.sh); nothing written"; exit 1; }
  git diff --quiet "$REF" HEAD -- scripts tests || { echo "KJV RELATIVE: STOP - scripts or tests changed since $REF; nothing written"; exit 1; }
  [ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "KJV RELATIVE: STOP - uncommitted changes in scripts/tests on PA; nothing written"; exit 1; }
  s=$(sha256sum "$P"); s=${s%% *}
  [ "$s" = "$XP" ] || { echo "KJV RELATIVE: STOP - the program is not the cleared file ($s); nothing written"; exit 1; }
  echo "=== 1 CHECK (read-only) ==="
  python3 -u "$P" check relative || { echo "KJV RELATIVE RESULT: STOP at check - nothing written"; exit 1; }
  : > "$D/started"
  echo "=== 2 APPLY (one all-or-nothing step) ==="
  python3 -u "$P" apply relative || { echo "KJV RELATIVE RESULT: STOP at apply - nothing saved"; exit 1; }
  echo "=== 3 AFTER (read-only) ==="
  python3 -u "$P" after relative || { echo "KJV RELATIVE RESULT: CHECK - written, the after-read is not clean; run nothing else, log to the ruling chat. Way back: python3 $P undo relative"; exit 1; }
  echo "way back, if ruled: cd ~/bible-db && python3 $P undo relative"
  echo "KJV RELATIVE RESULT: DONE"
) 2>&1 | tee "$A"; echo "exit=${PIPESTATUS[0]}"
fi
