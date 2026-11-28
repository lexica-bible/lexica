set +H
D=~/edition_upgrade_runs/split_apply_20261127
Z=~/edition_upgrade_runs/split_apply_20261127.tgz
if [ -e "$D/started" ]; then echo "SPLIT APPLY: STOP - already ran, kept in $D"; else
mkdir -p "$D"
A="$D/apply_$(date -u +%H%M%S).log"
( set -uo pipefail
  REF=7e0a61fb
  XP=ddc339ebf265ec3c5d3db962534c1ad1f3359a3b1681f40d775c1b12c86a5ceb   # apply_split_doubles_20261126.py (9.281; run on two copies, 9.284 / 9.286)
  XH=51aa5d0797d674e794dea918b3bc060326bd3847249d913007c96ab50dce1936   # health_check.py with the floor at 394553 (9.281 (b))
  P=scripts/apply_split_doubles_20261126.py
  H=scripts/health_check.py
  LIVE=~/bible-db/bible.db
  export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
  h() { cut -d' ' -f1 <<< "$(sha256sum < "$1")"; }
  echo "SPLIT APPLY - the split double rows write on LIVE (DESIGN 9.280-9.287) - REF $REF - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
  cd ~/bible-db || { echo "SPLIT APPLY: STOP - no ~/bible-db"; exit 1; }
  t=$(date -u +%H%M)
  if [ "$((10#$t))" -ge 1130 ] && [ "$((10#$t))" -lt 1430 ]; then echo "SPLIT APPLY: STOP - too near the 13:30 UTC nightly (11:30-14:30); nothing written"; exit 1; fi
  git merge-base --is-ancestor "$REF" HEAD || { echo "SPLIT APPLY: STOP - PA does not have $REF (run deploy.sh); nothing written"; exit 1; }
  git diff --quiet "$REF" HEAD -- scripts tests docs/handoffs/drafts/SPLIT_DOUBLES/rows_split_doubles_20261125.tsv || { echo "SPLIT APPLY: STOP - scripts, tests or the rows file changed since $REF; nothing written"; exit 1; }
  [ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "SPLIT APPLY: STOP - uncommitted changes in scripts/tests on PA; nothing written"; exit 1; }
  for x in "$P:$XP" "$H:$XH"; do
    f=${x%%:*}; want=${x##*:}
    [ -s "$f" ] || { echo "SPLIT APPLY: STOP - missing or empty: $f; nothing written"; exit 1; }
    k=$(h "$f"); [ "$k" = "$want" ] || { echo "SPLIT APPLY: STOP - $f is not the pinned file ($k); nothing written"; exit 1; }
  done
  grep -qx "SURFACE_FLOOR = 394553" "$H" || { echo "SPLIT APPLY: STOP - the health floor on PA is not 394553; nothing written"; exit 1; }
  echo "pinned files: program and health check as pinned; health floor 394553"
  echo "live: $(stat -c %s "$LIVE") bytes, last write $(TZ=UTC date -r "$LIVE" +%FT%TZ); home in use: $(cut -f1 <<< "$(du -sk ~ 2>/dev/null)") KB"
  echo "=== 1 CHECK on live (read-only) - $(date -u +%FT%TZ) ==="
  python3 -u "$P" check || { echo "SPLIT APPLY RESULT: STOP at check - nothing written"; exit 1; }
  : > "$D/started"
  echo "=== 2 APPLY on live (one all-or-nothing step: 512 rows' number cells, 1,024 correction rows, 482 forms off, 17 on) - $(date -u +%FT%TZ) ==="
  python3 -u "$P" apply || { echo "SPLIT APPLY RESULT: STOP at apply - nothing saved; log to the ruling chat"; exit 1; }
  echo "=== 3 AFTER on live (read-only) - $(date -u +%FT%TZ) ==="
  python3 -u "$P" after || { echo "SPLIT APPLY RESULT: CHECK - written, the after-read is not clean; run nothing else, log to the ruling chat. Way back: cd ~/bible-db && python3 $P undo"; exit 1; }
  echo "way back, if ruled: cd ~/bible-db && python3 $P undo"
  echo "=== 4 the health floor on live (read-only scan; backup and disk checks skipped) - $(date -u +%FT%TZ) ==="
  python3 -u "$H" "$LIVE" --no-backup-check --no-disk-check > "$D/health.out" 2>&1; r=$?
  grep "abp_surface rows BELOW floor" "$D/health.out"; tail -n 2 "$D/health.out"; echo "health_check exit $r"
  grep -qE "\[OK  \] abp_surface rows BELOW floor 394553.*: 0" "$D/health.out" || { echo "SPLIT APPLY RESULT: CHECK - written and read back clean, but the floor line is not OK at 0 (health.out kept); log to the ruling chat"; exit 1; }
  echo "live after: $(stat -c %s "$LIVE") bytes, last write $(TZ=UTC date -r "$LIVE" +%FT%TZ)"
  echo "SPLIT APPLY RESULT: DONE - written on live and read back; abp_surface 394,553; floor OK; the pins move in the next commit"
) 2>&1 | tee "$A"; echo "exit=${PIPESTATUS[0]}"
if [ -e "$D/started" ] && [ -z "$(ls "$Z" 2>/dev/null)" ]; then tar czf "$Z" -C ~/edition_upgrade_runs split_apply_20261127 && echo "PACKED: $Z ($(stat -c %s "$Z") bytes)"; fi
fi
