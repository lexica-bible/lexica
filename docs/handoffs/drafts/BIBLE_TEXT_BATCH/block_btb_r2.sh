set +H
D=~/bible_text_batch_20261122
L=$D/run_r2.log
if [ -e "$L" ]; then echo "BTB BLOCK: STOP - already ran, log kept: $L"; else
mkdir -p "$D"
( set -uo pipefail
  REF=1440ea4a
  XP=e7504c883a22b3fbb8f4744ba6fd9d036195d29e7351f50b5e2b73157b9e5340
  P=scripts/apply_bible_text_batch_20261122.py
  cd ~/bible-db || { echo "BTB BLOCK: STOP - no ~/bible-db"; exit 1; }
  echo "BTB BLOCK - REF $REF - PA HEAD $(git log -1 --format=%h) - $(date -u +%FT%TZ)"
  t=$(date -u +%H%M)
  if [ "$((10#$t))" -ge 1230 ] && [ "$((10#$t))" -lt 1430 ]; then echo "BTB BLOCK: STOP - too near the 13:00-14:30 UTC window; nothing written"; exit 1; fi
  git merge-base --is-ancestor "$REF" HEAD || { echo "BTB BLOCK: STOP - PA does not have $REF (run deploy.sh); nothing written"; exit 1; }
  git diff --quiet "$REF" HEAD -- scripts tests || { echo "BTB BLOCK: STOP - scripts or tests changed since $REF; nothing written"; exit 1; }
  s=$(cut -d' ' -f1 <<< "$(sha256sum "$P")")
  [ "$s" = "$XP" ] || { echo "BTB BLOCK: STOP - the program is not the cleared file ($s); nothing written"; exit 1; }
  export PYTHONIOENCODING=utf-8
  echo "=== 1 CHECK (read-only) ==="
  python3 -u "$P" check || { echo "BTB BLOCK RESULT: STOP at check - nothing written"; exit 1; }
  echo "=== 2 APPLY (one all-or-nothing step) ==="
  python3 -u "$P" apply || { echo "BTB BLOCK RESULT: STOP at apply - nothing saved"; exit 1; }
  echo "=== 3 AFTER (read-only) ==="
  python3 -u "$P" after || { echo "BTB BLOCK RESULT: CHECK - written, the after-read is not clean; run nothing else, log to the ruling chat"; exit 1; }
  echo "BTB BLOCK RESULT: DONE"
) 2>&1 | tee "$L"
fi
