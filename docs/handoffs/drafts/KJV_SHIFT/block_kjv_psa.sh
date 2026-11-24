set +H
D=~/edition_upgrade_runs/kjv_shift_psa_20261124
if [ -e "$D/started" ]; then echo "KJV PSA: STOP - already ran, log kept: $D"; else
mkdir -p "$D"
A="$D/try_$(date -u +%H%M%S).log"
( set -uo pipefail
  REF=048133f0
  XP=056d2215fc10e014f4c37f40089841a8ab7b987a346da3caf069d6cca372ab31
  P=scripts/apply_kjv_shift_short_20261124.py
  export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
  echo "KJV PSA - Psa 7:1, 6 rows - REF $REF - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
  cd ~/bible-db || { echo "KJV PSA: STOP - no ~/bible-db"; exit 1; }
  t=$(date -u +%H%M)
  if [ "$((10#$t))" -ge 1230 ] && [ "$((10#$t))" -lt 1430 ]; then echo "KJV PSA: STOP - too near the 13:00-14:30 UTC window; nothing written"; exit 1; fi
  git merge-base --is-ancestor "$REF" HEAD || { echo "KJV PSA: STOP - PA does not have $REF (run deploy.sh); nothing written"; exit 1; }
  git diff --quiet "$REF" HEAD -- scripts tests || { echo "KJV PSA: STOP - scripts or tests changed since $REF; nothing written"; exit 1; }
  [ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "KJV PSA: STOP - uncommitted changes in scripts/tests on PA; nothing written"; exit 1; }
  s=$(sha256sum "$P"); s=${s%% *}
  [ "$s" = "$XP" ] || { echo "KJV PSA: STOP - the program is not the cleared file ($s); nothing written"; exit 1; }
  echo "=== 1 CHECK (read-only) ==="
  python3 -u "$P" check psa || { echo "KJV PSA RESULT: STOP at check - nothing written"; exit 1; }
  : > "$D/started"
  echo "=== 2 APPLY (one all-or-nothing step) ==="
  python3 -u "$P" apply psa || { echo "KJV PSA RESULT: STOP at apply - nothing saved"; exit 1; }
  echo "=== 3 AFTER (read-only) ==="
  python3 -u "$P" after psa || { echo "KJV PSA RESULT: CHECK - written, the after-read is not clean; run nothing else, log to the ruling chat. Way back: python3 $P undo psa"; exit 1; }
  echo "way back, if ruled: cd ~/bible-db && python3 $P undo psa"
  echo "KJV PSA RESULT: DONE"
) 2>&1 | tee "$A"; echo "exit=${PIPESTATUS[0]}"
fi
