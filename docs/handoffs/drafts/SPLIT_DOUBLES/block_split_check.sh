set +H
D=~/edition_upgrade_runs/split_doubles_check_20261126
mkdir -p "$D"
A="$D/check_$(date -u +%H%M%S).log"
( set -uo pipefail
  REF=f295a88a
  XP=ddc339ebf265ec3c5d3db962534c1ad1f3359a3b1681f40d775c1b12c86a5ceb
  P=scripts/apply_split_doubles_20261126.py
  export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
  echo "SPLIT DOUBLES CHECK - read-only, nothing written to any database - REF $REF - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
  cd ~/bible-db || { echo "SPLIT CHECK: STOP - no ~/bible-db"; exit 1; }
  git merge-base --is-ancestor "$REF" HEAD || { echo "SPLIT CHECK: STOP - PA does not have $REF (run deploy.sh)"; exit 1; }
  git diff --quiet "$REF" HEAD -- scripts tests docs/handoffs/drafts/SPLIT_DOUBLES/rows_split_doubles_20261125.tsv || { echo "SPLIT CHECK: STOP - scripts, tests or the rows file changed since $REF"; exit 1; }
  [ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "SPLIT CHECK: STOP - uncommitted changes in scripts/tests on PA"; exit 1; }
  s=$(sha256sum "$P"); s=${s%% *}
  [ "$s" = "$XP" ] || { echo "SPLIT CHECK: STOP - the program is not the reviewed file ($s)"; exit 1; }
  echo "=== CHECK (read-only) ==="
  python3 -u "$P" check || { echo "SPLIT CHECK RESULT: STOP - nothing written; log to the ruling chat"; exit 1; }
  echo "SPLIT CHECK RESULT: DONE - nothing written"
) 2>&1 | tee "$A"; echo "exit=${PIPESTATUS[0]}"
