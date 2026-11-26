set +H
D=~/edition_upgrade_runs/split_proof_20261127
Z=~/edition_upgrade_runs/split_proof_20261127.tgz
if [ -e "$D/started" ]; then echo "SPLIT PROOF: STOP - already ran, kept in $D"; else
mkdir -p "$D"
A="$D/proof_$(date -u +%H%M%S).log"
( set -uo pipefail
  REF=655965a8
  XP=ddc339ebf265ec3c5d3db962534c1ad1f3359a3b1681f40d775c1b12c86a5ceb   # apply_split_doubles_20261126.py (as cleared, 9.281)
  XT=56b6e9b6af63618d80ccc883e4ee7146998c69321a273c8c09696e9885ed4cf1   # split_doubles_proof_20261126.py
  XF=3cc35e7d9fcfdc5c7d47da25ba1ba3785cdde504868e3e64cfde8aab4308fe28   # the frozen fill (9.272)
  XB4=ea6c54c34a86539929bee354f4b3390d7aadbdba081f5010233381e0fd4e7273  # the 11/15 pre-fill table (9.128, 9.134)
  XHOME_MAX=8300000                                                     # KB: STOP before the copy above this
  P=scripts/apply_split_doubles_20261126.py
  T=scripts/split_doubles_proof_20261126.py
  FILL=tests/fixtures/rebuild_trap/abp_surface_fill_20261126.tsv
  LEX=abp_helps/analytical_lexicon.tsv
  PF=~/abp_surface_prefill_20261115.db
  BH=~/bible-db/bh_scrape.db
  LIVE=~/bible-db/bible.db
  C=$D/proof.db
  export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
  h() { cut -d' ' -f1 <<< "$(sha256sum < "$1")"; }
  n() { python3 -c "import sqlite3,sys; print(sqlite3.connect('file:'+sys.argv[1]+'?mode=ro', uri=True).execute('SELECT count(*) FROM abp_surface').fetchone()[0])" "$1"; }
  echo "SPLIT PROOF - on a whole-file copy only, nothing written to live - REF $REF - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
  cd ~/bible-db || { echo "SPLIT PROOF: STOP - no ~/bible-db"; exit 1; }
  t=$(date -u +%H%M)
  if [ "$((10#$t))" -ge 1130 ] && [ "$((10#$t))" -lt 1430 ]; then echo "SPLIT PROOF: STOP - too near the 13:30 UTC nightly (11:30-14:30); nothing done"; exit 1; fi
  git merge-base --is-ancestor "$REF" HEAD || { echo "SPLIT PROOF: STOP - PA does not have $REF (run deploy.sh); nothing done"; exit 1; }
  git diff --quiet "$REF" HEAD -- scripts tests docs/handoffs/drafts/SPLIT_DOUBLES/rows_split_doubles_20261125.tsv || { echo "SPLIT PROOF: STOP - scripts, tests or the rows file changed since $REF; nothing done"; exit 1; }
  [ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "SPLIT PROOF: STOP - uncommitted changes in scripts/tests on PA; nothing done"; exit 1; }
  for x in "$P:$XP" "$T:$XT" "$FILL:$XF" "$PF:$XB4"; do
    f=${x%%:*}; want=${x##*:}
    [ -s "$f" ] || { echo "SPLIT PROOF: STOP - missing or empty: $f; nothing done"; exit 1; }
    k=$(h "$f"); [ "$k" = "$want" ] || { echo "SPLIT PROOF: STOP - $f is not the pinned file ($k); nothing done"; exit 1; }
  done
  [ -s "$LEX" ] && [ -s "$BH" ] || { echo "SPLIT PROOF: STOP - missing $LEX or $BH; nothing done"; exit 1; }
  echo "pinned files: program, proof tool, frozen fill, 11/15 pre-fill table: all as pinned; lexicon file and bh_scrape.db present"
  [ "$(basename "$C")" = proof.db ] && [ "$C" != "$LIVE" ] || { echo "SPLIT PROOF: STOP - the copy path is wrong; nothing done"; exit 1; }
  dk0=$(cut -f1 <<< "$(du -sk ~ 2>/dev/null)"); echo "home in use before: $dk0 KB (STOP above $XHOME_MAX KB; the copy adds about 442,000 KB, the two saved tables and the tgz about 100,000 more)"
  [ -n "$dk0" ] && [ "$dk0" -le "$XHOME_MAX" ] || { echo "SPLIT PROOF: STOP - home is above the bound (or du gave nothing); nothing done"; exit 1; }
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
    && grep -qx "copy abp_surface: 395018" "$D/copy.out" || { echo "SPLIT PROOF RESULT: STOP at the copy (kept in $D); log to the ruling chat"; exit 1; }
  echo "=== 2 the write, on the COPY only (check / apply / after with --db) - $(date -u +%FT%TZ) ==="
  for m in check apply after; do
    python3 -u "$P" "$m" --db "$C" || { echo "SPLIT PROOF RESULT: STOP at $m on the copy (kept in $D); log to the ruling chat"; exit 1; }
  done
  echo "=== 3 the written table, saved (the target the re-freeze must give back) ==="
  python3 -u "$T" save "$C" "$D/written.db" || { echo "SPLIT PROOF RESULT: STOP at saving the written table (copy kept)"; exit 1; }
  echo "=== 4 rebuild-words step 9's builders, on the COPY only - $(date -u +%FT%TZ) ==="
  python3 -u scripts/build_abp_surface.py "$C" --bh "$BH" > "$D/s9_build.out" 2>&1; r=$?; tail -4 "$D/s9_build.out"; echo "build_abp_surface exit $r; table $(n "$C") - $(date -u +%T)"
  [ "$r" = 0 ] || { echo "SPLIT PROOF RESULT: STOP in step 9 (copy kept)"; exit 1; }
  python3 -u scripts/backfill_abp_surface.py "$C" --bh "$BH" --apply > "$D/s9_backfill.out" 2>&1; r=$?; tail -4 "$D/s9_backfill.out"; echo "backfill_abp_surface exit $r; table $(n "$C") - $(date -u +%T)"
  [ "$r" = 0 ] || { echo "SPLIT PROOF RESULT: STOP in step 9 (copy kept)"; exit 1; }
  python3 -u scripts/backfill_pn_surface.py "$C" --bh "$BH" --apply > "$D/s9_pn.out" 2>&1; r=$?; tail -4 "$D/s9_pn.out"; echo "backfill_pn_surface exit $r; table $(n "$C") - $(date -u +%T)"
  [ "$r" = 0 ] || { echo "SPLIT PROOF RESULT: STOP in step 9 (copy kept)"; exit 1; }
  python3 -u scripts/build_abp_translit.py "$C" > "$D/s9_translit.out" 2>&1; r=$?; tail -3 "$D/s9_translit.out"; echo "build_abp_translit exit $r - $(date -u +%T)"
  [ "$r" = 0 ] || { echo "SPLIT PROOF RESULT: STOP in step 9 (copy kept)"; exit 1; }
  NB=$(n "$C"); echo "NEW BUILDER BASE: $NB (the 11/15 base was 391,141)"
  echo "=== 5 the new builder table, saved (the candidate pre-fill table) ==="
  python3 -u "$T" save "$C" "$D/builder.db" || { echo "SPLIT PROOF RESULT: STOP at saving the builder table (copy kept)"; exit 1; }
  echo "=== 6 the new builder table against the 11/15 pre-fill table (read-only) ==="
  python3 -u "$T" compare "$D/builder.db" "$PF" --verses "$C" --out "$D/builder_vs_prefill.tsv" || { echo "SPLIT PROOF RESULT: STOP at the compare (copy kept)"; exit 1; }
  echo "=== 7 restore DRY RUN of the frozen fill on the copy's builder table (writes only its report) - $(date -u +%FT%TZ) ==="
  python3 -u scripts/restore_surface_fill.py "$C" --snapshot "$FILL" --lexicon "$LEX" --base "$NB" --report "$D/restore_dry.tsv" > "$D/restore_dry.out" 2>&1; r=$?
  sed -n '/^SUMMARY/,$p' "$D/restore_dry.out"; echo "restore dry run exit $r (0 = every slot placed, 1 = slots listed as unplaced; both are a measurement)"
  grep -q "RESULT: DRY RUN COMPLETE" "$D/restore_dry.out" || { echo "SPLIT PROOF RESULT: STOP - the dry run did not complete (copy kept)"; exit 1; }
  echo "every unplaced slot, with its reason, is listed in restore_dry.out and restore_dry.tsv (both packed)"
  echo "=== 8 the copy removed ==="
  rm -- ~/edition_upgrade_runs/split_proof_20261127/proof.db && [ ! -e "$C" ] && echo "the copy removed: yes" || { echo "SPLIT PROOF RESULT: CHECK - measured, but the copy could not be removed"; exit 1; }
  ls -la "$D" | grep -v "^total"
  echo "home in use after: $(cut -f1 <<< "$(du -sk ~ 2>/dev/null)") KB (before $dk0 KB)"
  echo "SPLIT PROOF RESULT: DONE - measured on a copy; nothing written to live"
) 2>&1 | tee "$A"; echo "exit=${PIPESTATUS[0]}"
if [ -e "$D/started" ] && [ ! -e "$D/proof.db" ] && [ -z "$(ls "$Z" 2>/dev/null)" ]; then tar czf "$Z" -C ~/edition_upgrade_runs split_proof_20261127 && echo "PACKED: $Z ($(stat -c %s "$Z") bytes)"; fi
fi
