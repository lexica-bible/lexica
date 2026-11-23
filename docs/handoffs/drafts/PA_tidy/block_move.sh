set +H
H=~/pa_tidy_hold_20261123
if [ -e "$H" ]; then echo "PA TIDY: STOP - the holding folder already exists: $H"; else
A=~/edition_upgrade_runs/pa_tidy_move_$(date -u +%Y%m%d_%H%M%S).log
( set -uo pipefail
  XL=a3a67c9be609af12bb0cb23b1b5d5fea6a40b65e539b4a6b0769bd22dad76966
  N=51
  F=docs/handoffs/drafts/PA_tidy/move_list_20261123.tsv
  export GIT_OPTIONAL_LOCKS=0
  echo "PA TIDY - moves $N old files out of ~/bible-db into $H; deletes nothing - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
  cd ~/bible-db || exit 1
  [ -f "$F" ] || { echo "PA TIDY: STOP - no list file (run deploy.sh); nothing moved"; exit 1; }
  s=$(sha256sum "$F"); s=${s%% *}
  [ "$s" = "$XL" ] || { echo "PA TIDY: STOP - the list is not the cleared file ($s); nothing moved"; exit 1; }
  n=0; bad=0
  while IFS=$'\t' read -r f z; do
    n=$((n+1))
    if [ -L "$f" ] || [ ! -f "$f" ]; then echo "  not a plain file here: $f"; bad=$((bad+1)); continue; fi
    [ "$(stat -c %s -- "$f")" = "$z" ] || { echo "  size changed: $f"; bad=$((bad+1)); }
    if git ls-files --error-unmatch -- "$f" >/dev/null 2>&1; then echo "  tracked by git: $f"; bad=$((bad+1)); fi
  done < "$F"
  echo "checked: $n files, $bad problems"
  { [ "$n" -eq "$N" ] && [ "$bad" -eq 0 ]; } || { echo "PA TIDY RESULT: STOP - nothing moved"; exit 1; }
  mkdir "$H" || exit 1
  while IFS=$'\t' read -r f z; do
    mv -n -- "$f" "$H/"
    { [ -e "$H/$f" ] && [ ! -e "$f" ]; } || { echo "PA TIDY RESULT: STOP at $f - some files moved; way back below"; echo "cd $H && for f in *; do mv -n -- \"\$f\" ~/bible-db/; done"; exit 1; }
  done < "$F"
  m=$(find "$H" -maxdepth 1 -type f | wc -l)
  [ "$m" -eq "$N" ] || { echo "PA TIDY RESULT: CHECK - $m files in the holding folder, expected $N"; exit 1; }
  echo "moved: $m files"
  echo "way back: cd $H && for f in *; do mv -n -- \"\$f\" ~/bible-db/; done"
  echo "PA TIDY RESULT: DONE - no database touched, nothing deleted"
) 2>&1 | tee "$A"; echo "exit=${PIPESTATUS[0]}"
fi
