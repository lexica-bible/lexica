set +H
D=~/edition_upgrade_runs/split_refreeze_20261127
Z=~/edition_upgrade_runs/split_refreeze_20261127.tgz
if [ -e "$D/started" ]; then echo "SPLIT REFREEZE: STOP - already ran, kept in $D"; else
mkdir -p "$D"
A="$D/refreeze_$(date -u +%H%M%S).log"
( set -uo pipefail
  REF=fa798be1
  XP=ddc339ebf265ec3c5d3db962534c1ad1f3359a3b1681f40d775c1b12c86a5ceb   # apply_split_doubles_20261126.py (9.281)
  XT=6db3294af662b782209ed89683c13b794124d428090df1e417cadf5b9968460d   # split_doubles_proof_20261126.py (save / compare / restore)
  XN=eaeee80750e658290c49f05866b9a69f954e2807515e4b82caf3285df5dbf228   # snapshot_surface_fill.py (the freeze)
  XRS=88844099ff65c0c4dcc6dee0ce96c476cdae446e46b710f578dc5dabebcb60ce  # restore_surface_fill.py
  XAM=98bfb3508555c664a560cb085c70dab91508df30313f4c8c6c4e37c4ed247b41  # the 2-row amendment file
  XR=a15bd77e3d1481fb40cc68a2fb4cc9e1ae6ee67511b21ed533f14d5148e12d2f   # the proof's restore report (9.284)
  XBD=c739a168a067e290f341ea84c58cf606b1f2393d0e4ed245cdebb2560b7b2ec7  # the proof's builder table (391,142)
  XWD=301e7caf2986dcf45881fe1534f3a760e0133eb7be8da97142c03c26ad503448  # the proof's written table (394,553)
  XHOME_MAX=8300000                                                     # KB: STOP before the copy above this
  P=scripts/apply_split_doubles_20261126.py
  T=scripts/split_doubles_proof_20261126.py
  N=scripts/snapshot_surface_fill.py
  RS=scripts/restore_surface_fill.py
  AM=tests/fixtures/surface_amend/abp_surface_amend_split_20261127.tsv
  PR=~/edition_upgrade_runs/split_proof_20261127
  REP=$PR/restore_dry.tsv
  BD=$PR/builder.db
  WD=$PR/written.db
  LEX=abp_helps/analytical_lexicon.tsv
  BH=~/bible-db/bh_scrape.db
  LIVE=~/bible-db/bible.db
  C=$D/refreeze.db
  NEW=$D/abp_surface_fill_20261127.tsv
  export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
  h() { cut -d' ' -f1 <<< "$(sha256sum < "$1")"; }
  n() { python3 -c "import sqlite3,sys; print(sqlite3.connect('file:'+sys.argv[1]+'?mode=ro', uri=True).execute('SELECT count(*) FROM abp_surface').fetchone()[0])" "$1"; }
  same() { grep -qE "inside +the plan's verses: same [0-9,]+ / only new 0 / only old 0 / differs 0" "$1" \
           && grep -qE "outside the plan's verses: same [0-9,]+ / only new 0 / only old 0 / differs 0" "$1"; }
  echo "SPLIT REFREEZE - on a whole-file copy only, nothing written to live - REF $REF - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
  cd ~/bible-db || { echo "SPLIT REFREEZE: STOP - no ~/bible-db"; exit 1; }
  t=$(date -u +%H%M)
  if [ "$((10#$t))" -ge 1130 ] && [ "$((10#$t))" -lt 1430 ]; then echo "SPLIT REFREEZE: STOP - too near the 13:30 UTC nightly (11:30-14:30); nothing done"; exit 1; fi
  git merge-base --is-ancestor "$REF" HEAD || { echo "SPLIT REFREEZE: STOP - PA does not have $REF (run deploy.sh); nothing done"; exit 1; }
  git diff --quiet "$REF" HEAD -- scripts tests docs/handoffs/drafts/SPLIT_DOUBLES/rows_split_doubles_20261125.tsv || { echo "SPLIT REFREEZE: STOP - scripts, tests or the rows file changed since $REF; nothing done"; exit 1; }
  [ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "SPLIT REFREEZE: STOP - uncommitted changes in scripts/tests on PA; nothing done"; exit 1; }
  for x in "$P:$XP" "$T:$XT" "$N:$XN" "$RS:$XRS" "$AM:$XAM" "$REP:$XR" "$BD:$XBD" "$WD:$XWD"; do
    f=${x%%:*}; want=${x##*:}
    [ -s "$f" ] || { echo "SPLIT REFREEZE: STOP - missing or empty: $f; nothing done"; exit 1; }
    k=$(h "$f"); [ "$k" = "$want" ] || { echo "SPLIT REFREEZE: STOP - $f is not the pinned file ($k); nothing done"; exit 1; }
  done
  [ "$(cut -d' ' -f1 "$AM.sha256")" = "$XAM" ] || { echo "SPLIT REFREEZE: STOP - the amendment file's .sha256 is not $XAM; nothing done"; exit 1; }
  [ -s "$LEX" ] && [ -s "$BH" ] || { echo "SPLIT REFREEZE: STOP - missing $LEX or $BH; nothing done"; exit 1; }
  echo "pinned files: program, proof tool, freeze, restore, amendment file (+ its .sha256), the proof's report, builder and written tables: all as pinned; lexicon file and bh_scrape.db present"
  [ "$(basename "$C")" = refreeze.db ] && [ "$C" != "$LIVE" ] || { echo "SPLIT REFREEZE: STOP - the copy path is wrong; nothing done"; exit 1; }
  dk0=$(cut -f1 <<< "$(du -sk ~ 2>/dev/null)"); echo "home in use before: $dk0 KB (STOP above $XHOME_MAX KB; the copy adds about 442,000 KB, three saved tables about 56,000 more)"
  [ -n "$dk0" ] && [ "$dk0" -le "$XHOME_MAX" ] || { echo "SPLIT REFREEZE: STOP - home is above the bound (or du gave nothing); nothing done"; exit 1; }
  : > "$D/started"
  echo "=== 1 a whole-file copy of live (sqlite backup; live opened read-only) - $(date -u +%FT%TZ) ==="
  python3 - "$LIVE" "$C" > "$D/copy.out" 2>&1 <<'PY'
import os, sqlite3, sys
sys.path[0] == "" and sys.path.pop(0)
live, dst = sys.argv[1], sys.argv[2]
s = sqlite3.connect("file:%s?mode=ro" % live, uri=True, timeout=60)
print("live journal mode (read): %s" % s.execute("PRAGMA journal_mode").fetchone()[0])
d = sqlite3.connect(dst)
s.backup(d)
d.execute("PRAGMA journal_mode=DELETE")
d.close()
s.close()
c = sqlite3.connect("file:%s?mode=ro" % dst, uri=True)
print("copy quick_check: %s" % c.execute("PRAGMA quick_check").fetchone()[0])
print("copy abp_surface: %d" % c.execute("SELECT count(*) FROM abp_surface").fetchone()[0])
c.close()
print("copy: %d bytes" % os.path.getsize(dst))
PY
  rc=$?; cat "$D/copy.out"; echo "copy exit $rc (expect 0)"
  [ "$rc" = 0 ] && grep -qx "live journal mode (read): delete" "$D/copy.out" && grep -qx "copy quick_check: ok" "$D/copy.out" \
    && grep -qx "copy abp_surface: 395018" "$D/copy.out" || { echo "SPLIT REFREEZE RESULT: STOP at the copy (kept in $D); log to the ruling chat"; exit 1; }
  echo "=== 2 the write, on the COPY only (check / apply / after with --db) - $(date -u +%FT%TZ) ==="
  for m in check apply after; do
    python3 -u "$P" "$m" --db "$C" || { echo "SPLIT REFREEZE RESULT: STOP at $m on the copy (kept in $D); log to the ruling chat"; exit 1; }
  done
  echo "=== 3 the written table = the proof's written table (read-only) ==="
  python3 -u "$T" save "$C" "$D/w2.db" && python3 -u "$T" compare "$D/w2.db" "$WD" --verses "$C" --out "$D/w2_vs_proof.tsv" | tee "$D/w2_vs_proof.out" \
    && same "$D/w2_vs_proof.out" || { echo "SPLIT REFREEZE RESULT: STOP - the written table is not the proof's (copy kept)"; exit 1; }
  echo "written table = the proof's, every slot: yes"
  echo "=== 4 RE-FREEZE from the written copy (read-only on both databases; writes $NEW + .sha256 only) - $(date -u +%FT%TZ) ==="
  python3 -u "$N" --src "$C" --prefill "$BD" --from-restore "$REP" --amend "$AM" --out "$NEW" > "$D/freeze.out" 2>&1; r=$?
  cat "$D/freeze.out"; echo "freeze exit $r (expect 0)"
  FL=""
  chk() { if grep -qE "$2" "$D/freeze.out"; then echo "  $1: yes"; else echo "  $1: NO (expected: $2)"; FL="$FL $3"; fi; }
  chk "report sha printed" "restore report sha256 $XR" report
  chk "amendment file = its .sha256" "amendment file sha256 $XAM = its .sha256" amend
  chk "G0 3,952 = 3,412 + 539 + 1" "PASS — 3,952 = 3,412 insert \+ 539 update \+ 1 remove = the restore report \+ the amendment file" g0
  chk "rows 3,952" "rows +3,952 \| 3,952" rows
  chk "inserts / updates 3,412 / 539" "inserts / updates +3,412 / 539 \| 3,412 / 539" split
  chk "removes 1" "removes +1 \| 1" removes
  chk "SNAPSHOT WRITTEN" "RESULT: SNAPSHOT WRITTEN" written
  [ "$r" = 0 ] || FL="$FL exit"
  [ -z "$FL" ] || { echo "SPLIT REFREEZE RESULT: STOP - the re-freeze did not read as declared:$FL (copy kept)"; exit 1; }
  XNEW=$(h "$NEW"); [ "$(cut -d' ' -f1 "$NEW.sha256")" = "$XNEW" ] || { echo "SPLIT REFREEZE RESULT: STOP - the new file's .sha256 does not match it (copy kept)"; exit 1; }
  echo "new frozen file: $NEW sha256 $XNEW ($(stat -c %s "$NEW") bytes)"
  echo "=== 5 rebuild-words step 9's builders on the COPY; the result must be the proof's builder table - $(date -u +%FT%TZ) ==="
  python3 -u scripts/build_abp_surface.py "$C" --bh "$BH" > "$D/s9_build.out" 2>&1; r=$?; echo "build_abp_surface exit $r; table $(n "$C") - $(date -u +%T)"
  [ "$r" = 0 ] || { echo "SPLIT REFREEZE RESULT: STOP in step 9 (copy kept)"; exit 1; }
  python3 -u scripts/backfill_abp_surface.py "$C" --bh "$BH" --apply > "$D/s9_backfill.out" 2>&1; r=$?; echo "backfill_abp_surface exit $r; table $(n "$C") - $(date -u +%T)"
  [ "$r" = 0 ] || { echo "SPLIT REFREEZE RESULT: STOP in step 9 (copy kept)"; exit 1; }
  python3 -u scripts/backfill_pn_surface.py "$C" --bh "$BH" --apply > "$D/s9_pn.out" 2>&1; r=$?; echo "backfill_pn_surface exit $r; table $(n "$C") - $(date -u +%T)"
  [ "$r" = 0 ] || { echo "SPLIT REFREEZE RESULT: STOP in step 9 (copy kept)"; exit 1; }
  python3 -u scripts/build_abp_translit.py "$C" > "$D/s9_translit.out" 2>&1; r=$?; tail -1 "$D/s9_translit.out"; echo "build_abp_translit exit $r - $(date -u +%T)"
  [ "$r" = 0 ] || { echo "SPLIT REFREEZE RESULT: STOP in step 9 (copy kept)"; exit 1; }
  NB=$(n "$C"); echo "builder base: $NB (expect 391142)"
  python3 -u "$T" save "$C" "$D/b2.db" && python3 -u "$T" compare "$D/b2.db" "$BD" --verses "$C" --out "$D/b2_vs_proof.tsv" | tee "$D/b2_vs_proof.out" \
    && same "$D/b2_vs_proof.out" && [ "$NB" = 391142 ] || { echo "SPLIT REFREEZE RESULT: STOP - the builder table is not the proof's (copy kept)"; exit 1; }
  echo "builder table = the proof's, every slot: yes"
  echo "=== 6 RESTORE the NEW frozen file onto the copy (--apply; the restore's pins set for this run only) - $(date -u +%FT%TZ) ==="
  python3 -u "$T" restore --sha "$XNEW" --counts 3952,3412,539,1 --base 391142 -- "$C" --snapshot "$NEW" --lexicon "$LEX" \
    --prefill "$BD" --report "$D/restore_new.tsv" --apply > "$D/restore_new.out" 2>&1; r=$?
  head -1 "$D/restore_new.out"; sed -n '/^SUMMARY/,$p' "$D/restore_new.out"; echo "restore exit $r (expect 0)"
  [ "$r" = 0 ] && grep -q "RESULT: RESTORED, ALL CHECKS PASS (on a copy)" "$D/restore_new.out" \
    && grep -qE "unplaced +0 \| 0" "$D/restore_new.out" && grep -qE "G1 table after +394,553 \| 394,553" "$D/restore_new.out" \
    || { echo "SPLIT REFREEZE RESULT: STOP - the new frozen file did not restore clean (copy kept)"; exit 1; }
  echo "=== 7 the restored table = the written table, every slot (read-only) ==="
  python3 -u "$T" save "$C" "$D/r2.db" && python3 -u "$T" compare "$D/r2.db" "$WD" --verses "$C" --out "$D/r2_vs_written.tsv" | tee "$D/r2_vs_written.out" \
    && same "$D/r2_vs_written.out" || { echo "SPLIT REFREEZE RESULT: STOP - the restored table is not the written table (copy kept)"; exit 1; }
  echo "the re-freeze gives back the written table, every slot: yes"
  echo "=== 8 the copy and the three saved tables removed ==="
  rm -- ~/edition_upgrade_runs/split_refreeze_20261127/refreeze.db ~/edition_upgrade_runs/split_refreeze_20261127/w2.db \
        ~/edition_upgrade_runs/split_refreeze_20261127/b2.db ~/edition_upgrade_runs/split_refreeze_20261127/r2.db \
    && [ ! -e "$C" ] && echo "the copy and saved tables removed: yes" || { echo "SPLIT REFREEZE RESULT: CHECK - all passed but the copy could not be removed"; exit 1; }
  ls -la "$D" | grep -v "^total"
  echo "home in use after: $(cut -f1 <<< "$(du -sk ~ 2>/dev/null)") KB (before $dk0 KB)"
  echo "SPLIT REFREEZE RESULT: DONE - new frozen file $XNEW, 3,952 rows, restores to the written table exactly; nothing written to live"
) 2>&1 | tee "$A"; echo "exit=${PIPESTATUS[0]}"
if [ -e "$D/started" ] && [ ! -e "$D/refreeze.db" ] && [ -z "$(ls "$Z" 2>/dev/null)" ]; then tar czf "$Z" -C ~/edition_upgrade_runs split_refreeze_20261127 && echo "PACKED: $Z ($(stat -c %s "$Z") bytes)"; fi
fi
