set +H
D=~/edition_upgrade_runs/abp_exo2_11_20261124
if [ -e "$D/started" ]; then echo "EXO 2:11: STOP - already ran, log kept: $D"; else
mkdir -p "$D"
A="$D/try_$(date -u +%H%M%S).log"
( set -uo pipefail
  REF=8ab5e307
  XP=66426c002d3aaed50de94601420495725332d28a2920b7aea5873ad2c94f34f0
  P=scripts/apply_abp_corrections_exo2_11_20261124.py
  export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
  echo "EXO 2:11 - old er -> older, 3 cells + 3 correction rows - REF $REF - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
  cd ~/bible-db || { echo "EXO 2:11: STOP - no ~/bible-db"; exit 1; }
  t=$(date -u +%H%M)
  if [ "$((10#$t))" -ge 1230 ] && [ "$((10#$t))" -lt 1430 ]; then echo "EXO 2:11: STOP - too near the 13:00-14:30 UTC window; nothing written"; exit 1; fi
  git merge-base --is-ancestor "$REF" HEAD || { echo "EXO 2:11: STOP - PA does not have $REF (run deploy.sh); nothing written"; exit 1; }
  git diff --quiet "$REF" HEAD -- scripts tests || { echo "EXO 2:11: STOP - scripts or tests changed since $REF; nothing written"; exit 1; }
  [ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "EXO 2:11: STOP - uncommitted changes in scripts/tests on PA; nothing written"; exit 1; }
  s=$(sha256sum "$P"); s=${s%% *}
  [ "$s" = "$XP" ] || { echo "EXO 2:11: STOP - the program is not the cleared file ($s); nothing written"; exit 1; }
  echo "=== 1 CHECK (read-only) ==="
  python3 -u "$P" check || { echo "EXO 2:11 RESULT: STOP at check - nothing written"; exit 1; }
  : > "$D/started"
  echo "=== 2 APPLY (one all-or-nothing step) ==="
  python3 -u "$P" apply || { echo "EXO 2:11 RESULT: STOP at apply - nothing saved"; exit 1; }
  echo "=== 3 AFTER (read-only) ==="
  python3 -u "$P" after || { echo "EXO 2:11 RESULT: CHECK - written, the after-read is not clean; run nothing else, log to the ruling chat. Way back: python3 $P undo"; exit 1; }
  echo "way back, if ruled: cd ~/bible-db && python3 $P undo"
  echo "EXO 2:11 RESULT: DONE"
) 2>&1 | tee "$A"; echo "exit=${PIPESTATUS[0]}"
fi
