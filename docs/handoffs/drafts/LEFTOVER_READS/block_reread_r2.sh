set +H
D=~/edition_upgrade_runs/split_reread_r2_20261123
Z=~/edition_upgrade_runs/split_reread_r2_20261123.tgz
if [ -e "$D/started" ]; then echo "REREAD R2: STOP - already ran, kept in $D"; else
mkdir -p "$D"
A="$D/run_$(date -u +%H%M%S).log"
( set -uo pipefail
  REF=77f1b903
  PY=$HOME/.virtualenvs/bible-env/bin/python
  export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
  echo "GATE REF ${REF} - split re-read r2 + Hebrew notes count, read-only - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
  cd ~/bible-db || exit 1
  git merge-base --is-ancestor "$REF" HEAD || { echo "REREAD R2: STOP - PA has not pulled $REF (run deploy.sh); nothing read"; exit 1; }
  git diff --quiet "$REF" HEAD -- scripts tests core.py || { echo "REREAD R2: STOP - scripts/tests/core differ from $REF; nothing read"; exit 1; }
  [ -z "$(git status --porcelain --untracked-files=no -- scripts tests core.py)" ] || { echo "REREAD R2: STOP - uncommitted changes on PA; nothing read"; exit 1; }
  t=$(date -u +%H%M)
  if [ "$((10#$t))" -ge 1230 ] && [ "$((10#$t))" -lt 1430 ]; then echo "REREAD R2: STOP - too near the nightly (12:30-14:30 UTC); nothing read"; exit 1; fi
  [ -x "$PY" ] || { echo "REREAD R2: STOP - no site Python at $PY; nothing read"; exit 1; }
  : > "$D/started"
  echo "=== A SPLIT RENDERINGS ==="
  "$PY" -u scripts/audit_split_rendering.py --out "$D"; a=$?
  echo "=== B HEBREW EDITOR'S NOTES ==="
  "$PY" -u scripts/read_heb_notes_20261123.py --out "$D"; b=$?
  echo "exits: split $a, notes $b"
  ls -l "$D"
  if [ "$a" -eq 0 ] && [ "$b" -eq 0 ]; then r=0; echo "REREAD R2 RESULT: DONE - nothing written to any database"
  else r=2; echo "REREAD R2 RESULT: CHECK - a control failed or a read did not finish; nothing written to any database"; fi
  exit "$r"
) 2>&1 | tee "$A"; echo "exit=${PIPESTATUS[0]}"
if [ -e "$D/started" ] && [ ! -e "$Z" ]; then tar czf "$Z" -C ~/edition_upgrade_runs split_reread_r2_20261123 && echo "PACKED: $Z"; fi
fi
