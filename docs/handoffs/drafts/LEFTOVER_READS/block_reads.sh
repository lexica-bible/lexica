set +H
D=~/edition_upgrade_runs/leftover_reads_20261122
Z=~/edition_upgrade_runs/leftover_reads_20261122.tgz
if [ -e "$D/started" ]; then echo "LEFTOVER READS: STOP - already ran, kept in $D"; else
mkdir -p "$D"
A="$D/run_$(date -u +%H%M%S).log"
( set -uo pipefail
  REF=d4790da0
  XT=10db2a9ad233b4527dabddb12496ab860808cd94ef092a118893d64363e78721
  PY=$HOME/.virtualenvs/bible-env/bin/python
  P=scripts/read_leftovers_20261122.py
  T=docs/handoffs/drafts/PA_tidy/block_list.sh
  export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
  echo "GATE REF ${REF} - leftover reads, read-only - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
  cd ~/bible-db || exit 1
  git merge-base --is-ancestor "$REF" HEAD || { echo "LEFTOVER READS: STOP - PA has not pulled $REF (run deploy.sh); nothing read"; exit 1; }
  git diff --quiet "$REF" HEAD -- scripts tests || { echo "LEFTOVER READS: STOP - scripts/tests differ from $REF; nothing read"; exit 1; }
  git diff --quiet "$REF" HEAD -- short_meaning.py views_lexicon.py core.py app.py number_fold.py contested_register.py || { echo "LEFTOVER READS: STOP - the header code differs from $REF; nothing read"; exit 1; }
  [ -z "$(git status --porcelain --untracked-files=no -- scripts tests short_meaning.py views_lexicon.py core.py app.py number_fold.py contested_register.py)" ] || { echo "LEFTOVER READS: STOP - uncommitted changes on PA; nothing read"; exit 1; }
  t=$(date -u +%H%M)
  if [ "$((10#$t))" -ge 1230 ] && [ "$((10#$t))" -lt 1430 ]; then echo "LEFTOVER READS: STOP - too near the nightly (12:30-14:30 UTC); nothing read"; exit 1; fi
  [ -x "$PY" ] || { echo "LEFTOVER READS: STOP - no site Python at $PY; nothing read"; exit 1; }
  s=$(sha256sum "$T"); s=${s%% *}
  [ "$s" = "$XT" ] || { echo "LEFTOVER READS: STOP - the tidy listing is not the reviewed file ($s); nothing read"; exit 1; }
  : > "$D/started"
  r=0
  echo "=== A HEADERS, OVERRIDES, KJV SHIFT, DICTIONARY PROSE (several minutes; progress prints) ==="
  "$PY" -u "$P" --out "$D"; a=$?
  echo "reads exit: $a"
  if [ "$a" -ne 0 ] && [ "$a" -ne 2 ]; then echo "LEFTOVER READS RESULT: STOP at A - nothing written to any database"; exit 1; fi
  [ "$a" -eq 0 ] || r=2
  echo "=== B HELPER AUDIT CONTROLS (expect 4 PASS) ==="
  "$PY" -u scripts/audit_helper_double_tag.py > "$D/helper.txt" 2>&1; echo "helper audit exit: $?"
  grep -E '\[(PASS|FAIL)\]|-> control|^=== POLARITY' "$D/helper.txt"
  grep -qF -- '-> control PASSED' "$D/helper.txt" || r=2
  echo "=== C NAVE'S ROWS IN study.db (type, deleted, count) ==="
  sqlite3 -readonly "$HOME/bible-db/study.db" "SELECT type, deleted, count(*) FROM entries GROUP BY type, deleted" || r=2
  echo "=== D PA TIDY LISTING AND WAL CRUMBS (full list in tidy.txt) ==="
  bash "$T" > "$D/tidy.txt" 2>&1; echo "tidy listing exit: $?; lines: $(wc -l < "$D/tidy.txt")"
  sed -n '/^=== B/,$p' "$D/tidy.txt"
  grep -qF 'PA TIDY LIST DONE' "$D/tidy.txt" || r=2
  echo "=== FILES ==="
  ls -l "$D"
  if [ "$r" -eq 0 ]; then echo "LEFTOVER READS RESULT: DONE - nothing written to any database"
  else echo "LEFTOVER READS RESULT: CHECK - a control failed or a read did not finish; nothing written to any database"; fi
  exit "$r"
) 2>&1 | tee "$A"; echo "exit=${PIPESTATUS[0]}"
if [ -e "$D/started" ] && [ ! -e "$Z" ]; then tar czf "$Z" -C ~/edition_upgrade_runs leftover_reads_20261122 && echo "PACKED: $Z"; fi
fi
