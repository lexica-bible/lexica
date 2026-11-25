set +H
D=~/edition_upgrade_runs/verse_break_20261124
Z=~/edition_upgrade_runs/verse_break_20261124.tgz
if [ -e "$D/started" ]; then echo "VERSE BREAK: STOP - already ran, kept in $D"; else
mkdir -p "$D"
A="$D/run_$(date -u +%H%M%S).log"
( set -uo pipefail
  REF=8ab5e307
  XP=d72220d745a8249906c454da1a81ebc5b87d22308fa1b4a15b0fc1717182f3a6
  P=scripts/read_verse_break_forms_20261124.py
  PY=$HOME/.virtualenvs/bible-env/bin/python
  export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
  echo "GATE REF ${REF} - verse-break read, read-only - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
  cd ~/bible-db || exit 1
  git merge-base --is-ancestor "$REF" HEAD || { echo "VERSE BREAK: STOP - PA has not pulled $REF (run deploy.sh); nothing read"; exit 1; }
  git diff --quiet "$REF" HEAD -- scripts tests core.py || { echo "VERSE BREAK: STOP - scripts/tests/core differ from $REF; nothing read"; exit 1; }
  [ -z "$(git status --porcelain --untracked-files=no -- scripts tests core.py)" ] || { echo "VERSE BREAK: STOP - uncommitted changes on PA; nothing read"; exit 1; }
  t=$(date -u +%H%M)
  if [ "$((10#$t))" -ge 1230 ] && [ "$((10#$t))" -lt 1430 ]; then echo "VERSE BREAK: STOP - too near the nightly (12:30-14:30 UTC); nothing read"; exit 1; fi
  [ -x "$PY" ] || { echo "VERSE BREAK: STOP - no site Python at $PY; nothing read"; exit 1; }
  s=$(sha256sum "$P"); s=${s%% *}
  [ "$s" = "$XP" ] || { echo "VERSE BREAK: STOP - the program is not the reviewed file ($s); nothing read"; exit 1; }
  : > "$D/started"
  "$PY" -u "$P" --out "$D"; r=$?
  echo "read exit: $r"
  ls -l "$D"
  if [ "$r" -eq 0 ]; then echo "VERSE BREAK RESULT: DONE - nothing written to any database"
  else r=2; echo "VERSE BREAK RESULT: CHECK - a control failed or the read did not finish; nothing written to any database"; fi
  exit "$r"
) 2>&1 | tee "$A"; echo "exit=${PIPESTATUS[0]}"
if [ -e "$D/started" ] && [ -z "$(ls "$Z" 2>/dev/null)" ]; then tar czf "$Z" -C ~/edition_upgrade_runs verse_break_20261124 && echo "PACKED: $Z"; fi
fi
