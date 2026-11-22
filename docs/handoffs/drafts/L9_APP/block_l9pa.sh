# L9 PA LEG (DESIGN 9.239-9.241, 9.244) - READ-ONLY on live. Opens bible.db read-only for
# seconds; reads bh_scrape.db; writes ONLY its own files into a NEW run folder in ~.
# Before pasting: deploy.sh has run, so PA has the L9 code (2bdf3a62). Not 13:00-14:30 UTC.
# Last line: "L9 PA RESULT: PASS ..." (bring that one line) or "... CHECK/STOP" (bring all).
REF=2bdf3a62
D=~/l9_app_$(date -u +%Y%m%d_%H%M%S)
mkdir "$D" && cd "$D" && echo "run folder: $(pwd)" || echo "L9 PA RESULT: STOP - cannot make the run folder"
l9pa() {
  [ "$(pwd)" = "$D" ] || { echo "L9 PA RESULT: STOP - not in the new run folder"; return 1; }
  hm=$(date -u +%H%M); echo "UTC now: $(date -u +%FT%TZ)"
  if [ "$hm" -ge 1300 ] && [ "$hm" -lt 1430 ]; then echo "L9 PA RESULT: STOP - 13:00-14:30 UTC (backups + health check); run later"; return 1; fi
  P=~/bible-db/scripts; B=~/bible-db/bible.db; BH=~/bible-db/bh_scrape.db
  ( cd ~/bible-db && git merge-base --is-ancestor "$REF" HEAD ) || { echo "L9 PA RESULT: STOP - PA does not have $REF yet (run deploy.sh first)"; return 1; }
  ( cd ~/bible-db && git diff --quiet "$REF" HEAD -- scripts tests abp_app_html ) || { echo "L9 PA RESULT: STOP - scripts/tests/feed differ from $REF"; return 1; }
  k=$(cd ~/bible-db && git status --porcelain --untracked-files=no -- scripts tests abp_app_html)
  [ -z "$k" ] || { echo "L9 PA RESULT: STOP - scripts/tests/feed changed in the checkout: $k"; return 1; }
  echo "code: PA HEAD $(cd ~/bible-db && git rev-parse --short HEAD); scripts, tests, feed = $REF"
  [ -s "$B" ] || { echo "L9 PA RESULT: STOP - missing or empty: $B"; return 1; }
  [ -s "$BH" ] || { echo "L9 PA RESULT: STOP - missing or empty: $BH (a missing one would be CREATED empty)"; return 1; }
  [ -d ~/LXX-Rahlfs-1935 ] || { echo "L9 PA RESULT: STOP - Rahlfs not found: ~/LXX-Rahlfs-1935"; return 1; }
  for f in ~/TAGNT_Mat-Jhn.txt ~/TAGNT_Act-Rev.txt; do [ -s "$f" ] || { echo "L9 PA RESULT: STOP - TAGNT not found: $f"; return 1; }; done
  echo "inputs present: bible.db, bh_scrape.db ($(stat -c %s "$BH") B), Rahlfs, TAGNT x2"
  run() { n=$1; shift; echo "=== $n - start $(date -u +%T)"; PYTHONIOENCODING=utf-8 python3 "$@" < /dev/null > "$D/$n.out" 2>&1; r=$?; echo "    exit $r, $(wc -l < "$D/$n.out") lines, end $(date -u +%T)"; return $r; }
  nf() { if grep -q "NOT found" "$D/$1.out"; then echo "L9 PA RESULT: STOP - Rahlfs or TAGNT NOT found in $1:"; grep "NOT found" "$D/$1.out"; return 1; fi; }
  run c0_control_default "$P/lint_split_wrong_slot.py" "$B" "$BH" --control || { tail -5 "$D/c0_control_default.out"; echo "L9 PA RESULT: STOP - default-mode control failed"; return 1; }
  nf c0_control_default || return 1
  grep -q "CONTROL PASSED" "$D/c0_control_default.out" || { echo "L9 PA RESULT: STOP - no CONTROL PASSED line (default)"; return 1; }
  run c1_control_app "$P/lint_split_wrong_slot.py" "$B" "$BH" --app-feed --control || { tail -5 "$D/c1_control_app.out"; echo "L9 PA RESULT: STOP - --app-feed control failed"; return 1; }
  nf c1_control_app || return 1
  grep -q "CONTROL PASSED" "$D/c1_control_app.out" || { echo "L9 PA RESULT: STOP - no CONTROL PASSED line (--app-feed)"; return 1; }
  run l9_lint "$P/lint_split_wrong_slot.py" "$B" "$BH" --app-feed
  r1=$?; nf l9_lint || return 1
  run l9_size "$P/size_split_compounds.py" "$B" "$BH" --app-feed
  r2=$?; nf l9_size || return 1
  if grep -q "^STOP" "$D/l9_lint.out" "$D/l9_size.out"; then grep "^STOP" "$D/l9_lint.out" "$D/l9_size.out"; echo "L9 PA RESULT: STOP - a script stopped (line above)"; return 1; fi
  echo "=== lint output (key lines)"
  grep -E "words table:|RECONCILE|replayed verses|AMBIGUOUS|CHANGED after|content-word recipients|match:|DIFFER:|row count differs|split recipients:|UNADJUDICATED|RAW FLAGS:|RESIDUE|RESULT" "$D/l9_lint.out"
  echo "=== sizer output (key lines)"
  grep -E "recipient slots filled|verses affected|AMBIGUOUS|transplant tally" "$D/l9_size.out"
  res=$(grep "L9 --app-feed RESULT" "$D/l9_lint.out")
  [ -n "$res" ] && [ "$r1" = 0 ] && [ "$r2" = 0 ] || { echo "L9 PA RESULT: CHECK - lint exit $r1, sizer exit $r2, or no RESULT line (outputs in $D)"; return 1; }
  num() { printf '%s\n' "$res" | sed -n "s/.*$1 \([0-9,]*\).*/\1/p" | tr -d ,; }
  N=$(num recipients); V=$(printf '%s\n' "$res" | sed -n 's/.* in \([0-9,]*\) verses.*/\1/p' | tr -d ,)
  R=$(num RESIDUE); A=$(num ambiguous); DF=$(num DIFFER); CH=$(num "changed after split"); EM=$(num emptied)
  SN=$(sed -n 's/.*recipient slots filled by split: *\([0-9,]*\).*/\1/p' "$D/l9_size.out" | tr -d ,)
  SV=$(sed -n 's/.*verses affected: *\([0-9,]*\).*/\1/p' "$D/l9_size.out" | tr -d ,)
  SA=$(sed -n 's/.*AMBIGUOUS Greek-side groups: *\([0-9,]*\).*/\1/p' "$D/l9_size.out" | tr -d ,)
  line="lint N/V $N/$V, sizer N/V $SN/$SV; RESIDUE $R; ambiguous lint $A / sizer $SA; DIFFER $DF; changed $CH, emptied $EM"
  if [ "$N" = "$SN" ] && [ "$V" = "$SV" ] && [ "$R" = 0 ] && [ "$A" = 0 ] && [ "$SA" = 0 ] && [ "$DF" = 0 ] && [ -n "$N" ]; then
    echo "L9 PA RESULT: PASS - $line"
  else
    echo "L9 PA RESULT: CHECK - $line (outputs in $D)"
  fi
}
[ "$(pwd)" = "$D" ] && l9pa 2>&1 | tee "$D/block.log"
