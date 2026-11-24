set +H
D=~/edition_upgrade_runs/kjv_shift_two_20261124
if [ -e "$D/started" ]; then echo "KJV TWO: STOP - already ran, log kept: $D"; else
mkdir -p "$D"
A="$D/try_$(date -u +%H%M%S).log"
( set -uo pipefail
  REF=6cdc199f
  XP=bada03a293b3d1b56f5b5bf51942d2e85015a49f1bbccd058af291f1e21316f7
  P=scripts/apply_kjv_shift_short_20261124.py
  export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
  echo "KJV TWO - 1Co 5:13 + Mar 7:11, 4 rows - REF $REF - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
  cd ~/bible-db || { echo "KJV TWO: STOP - no ~/bible-db"; exit 1; }
  t=$(date -u +%H%M)
  if [ "$((10#$t))" -ge 1230 ] && [ "$((10#$t))" -lt 1430 ]; then echo "KJV TWO: STOP - too near the 13:00-14:30 UTC window; nothing written"; exit 1; fi
  git merge-base --is-ancestor "$REF" HEAD || { echo "KJV TWO: STOP - PA does not have $REF (run deploy.sh); nothing written"; exit 1; }
  git diff --quiet "$REF" HEAD -- scripts tests || { echo "KJV TWO: STOP - scripts or tests changed since $REF; nothing written"; exit 1; }
  [ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "KJV TWO: STOP - uncommitted changes in scripts/tests on PA; nothing written"; exit 1; }
  s=$(sha256sum "$P"); s=${s%% *}
  [ "$s" = "$XP" ] || { echo "KJV TWO: STOP - the program is not the cleared file ($s); nothing written"; exit 1; }
  echo "=== 1 CHECK (read-only) ==="
  python3 -u "$P" check two || { echo "KJV TWO RESULT: STOP at check - nothing written"; exit 1; }
  : > "$D/started"
  echo "=== 2 APPLY (one all-or-nothing step) ==="
  python3 -u "$P" apply two || { echo "KJV TWO RESULT: STOP at apply - nothing saved"; exit 1; }
  echo "=== 3 AFTER (read-only) ==="
  python3 -u "$P" after two || { echo "KJV TWO RESULT: CHECK - written, the after-read is not clean; run nothing else, log to the ruling chat. Way back: python3 $P undo two"; exit 1; }
  echo "way back, if ruled: cd ~/bible-db && python3 $P undo two"
  echo "KJV TWO RESULT: DONE"
) 2>&1 | tee "$A"; echo "exit=${PIPESTATUS[0]}"
fi
