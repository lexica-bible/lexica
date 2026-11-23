set +H
D=~/edition_upgrade_runs/split_reread_20261123
Z=~/edition_upgrade_runs/split_reread_20261123.tgz
if [ -e "$D/started" ]; then echo "SPLIT REREAD: STOP - already ran, kept in $D"; else
mkdir -p "$D"
A="$D/run_$(date -u +%H%M%S).log"
( set -uo pipefail
  REF=68d72038
  PY=$HOME/.virtualenvs/bible-env/bin/python
  P=scripts/audit_split_rendering.py
  export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
  echo "GATE REF ${REF} - split rendering re-read, read-only - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
  cd ~/bible-db || exit 1
  git merge-base --is-ancestor "$REF" HEAD || { echo "SPLIT REREAD: STOP - PA has not pulled $REF (run deploy.sh); nothing read"; exit 1; }
  git diff --quiet "$REF" HEAD -- scripts tests || { echo "SPLIT REREAD: STOP - scripts/tests differ from $REF; nothing read"; exit 1; }
  [ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "SPLIT REREAD: STOP - uncommitted changes in scripts/tests on PA; nothing read"; exit 1; }
  t=$(date -u +%H%M)
  if [ "$((10#$t))" -ge 1230 ] && [ "$((10#$t))" -lt 1430 ]; then echo "SPLIT REREAD: STOP - too near the nightly (12:30-14:30 UTC); nothing read"; exit 1; fi
  [ -x "$PY" ] || { echo "SPLIT REREAD: STOP - no site Python at $PY; nothing read"; exit 1; }
  : > "$D/started"
  "$PY" -u "$P" --out "$D"; r=$?
  echo "check exit: $r"
  ls -l "$D"
  if [ "$r" -eq 0 ]; then echo "SPLIT REREAD RESULT: DONE - nothing written to any database"
  else echo "SPLIT REREAD RESULT: CHECK - a control failed or the read did not finish; nothing written to any database"; fi
  exit "$r"
) 2>&1 | tee "$A"; echo "exit=${PIPESTATUS[0]}"
if [ -e "$D/started" ] && [ ! -e "$Z" ]; then tar czf "$Z" -C ~/edition_upgrade_runs split_reread_20261123 && echo "PACKED: $Z"; fi
fi
