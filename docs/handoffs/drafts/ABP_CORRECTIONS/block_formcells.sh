set +H
D=~/edition_upgrade_runs/formcells_20261126
Z=~/edition_upgrade_runs/formcells_20261126.tgz
if [ -e "$D/started" ]; then echo "FORMCELLS: STOP - already ran, kept in $D"; else
mkdir -p "$D"
A="$D/try_$(date -u +%H%M%S).log"
( set -uo pipefail
  REF=69e79319
  XP=7bc32ee4bf0d16e19bbb584a0d4329883ec8ec7e31b122273367e5af7c3a9adf                                                                  # apply_surface_formcells_20261126.py
  XN=eaeee80750e658290c49f05866b9a69f954e2807515e4b82caf3285df5dbf228                                                                  # snapshot_surface_fill.py
  XAM=acf9342309e043a806e25f0faf1cf35aa0cf935aec25b68a1400eb41429a7cd8       # the amendment file
  XR=e154d8d4991aa02d49380d473c22b511d7c5a7be4c7239873b0bfe19ebc4748a        # the 11/15 restore report = REPORT_SHA256
  XB4=ea6c54c34a86539929bee354f4b3390d7aadbdba081f5010233381e0fd4e7273       # the pre-fill table (DESIGN 9.128, 9.134)
  XHOME_MAX=8400000                                                          # KB: STOP before the copy above this (DESIGN 9.236 (2))
  P=scripts/apply_surface_formcells_20261126.py
  N=scripts/snapshot_surface_fill.py
  FX=tests/fixtures/rebuild_trap
  REP=$FX/restore_report_20261115.tsv
  AM=tests/fixtures/surface_amend/abp_surface_amend_20261126.tsv
  PF=~/abp_surface_prefill_20261115.db
  NEW=$FX/abp_surface_fill_20261126.tsv
  LC=$D/live_copy.db
  LIVE=~/bible-db/bible.db
  export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
  h() { cut -d' ' -f1 <<< "$(sha256sum < "$1")"; }
  echo "FORMCELLS - 10 printed-form cells + the re-freeze - REF $REF - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
  cd ~/bible-db || { echo "FORMCELLS: STOP - no ~/bible-db"; exit 1; }
  t=$(date -u +%H%M)
  if [ "$((10#$t))" -ge 1230 ] && [ "$((10#$t))" -lt 1430 ]; then echo "FORMCELLS: STOP - too near the 13:00-14:30 UTC window; nothing written"; exit 1; fi
  git merge-base --is-ancestor "$REF" HEAD || { echo "FORMCELLS: STOP - PA does not have $REF (run deploy.sh); nothing written"; exit 1; }
  git diff --quiet "$REF" HEAD -- scripts tests || { echo "FORMCELLS: STOP - scripts or tests changed since $REF; nothing written"; exit 1; }
  [ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "FORMCELLS: STOP - uncommitted changes in scripts/tests on PA; nothing written"; exit 1; }
  for x in "$P:$XP" "$N:$XN" "$AM:$XAM" "$REP:$XR" "$PF:$XB4"; do
    f=${x%%:*}; want=${x##*:}
    [ -s "$f" ] || { echo "FORMCELLS: STOP - missing or empty: $f; nothing written"; exit 1; }
    k=$(h "$f"); [ "$k" = "$want" ] || { echo "FORMCELLS: STOP - $f is not the pinned file ($k); nothing written"; exit 1; }
  done
  echo "pinned files: program, freeze program, amendment file, 11/15 report, pre-fill table: all as pinned"
  [ -e "$NEW" ] && { echo "FORMCELLS: STOP - $NEW already exists; nothing written"; exit 1; }
  dk0=$(cut -f1 <<< "$(du -sk ~ 2>/dev/null)"); echo "home in use before: $dk0 KB (STOP above $XHOME_MAX KB; the copy adds about 442,000 KB)"
  [ -n "$dk0" ] && [ "$dk0" -le "$XHOME_MAX" ] || { echo "FORMCELLS: STOP - home is above the ruled bound (or du gave nothing); nothing written"; exit 1; }
  echo "=== 1 CHECK (read-only) ==="
  python3 -u "$P" check || { echo "FORMCELLS RESULT: STOP at check - nothing written"; exit 1; }
  : > "$D/started"
  echo "=== 2 APPLY (one all-or-nothing step, abp_surface only) ==="
  python3 -u "$P" apply || { echo "FORMCELLS RESULT: STOP at apply - nothing saved"; exit 1; }
  echo "=== 3 AFTER (read-only) ==="
  python3 -u "$P" after || { echo "FORMCELLS RESULT: CHECK - written, the after-read is not clean; run nothing else, log to the ruling chat. Way back: python3 $P undo"; exit 1; }
  echo "way back, if ruled: cd ~/bible-db && python3 $P undo"
  echo "=== 4 a fresh copy of live (sqlite backup; live opened read-only) - start $(date -u +%FT%TZ) ==="
  python3 - "$LIVE" "$LC" > "$D/copy.out" 2>&1 <<'PY'
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
    && grep -qx "copy abp_surface: 395018" "$D/copy.out" || { echo "FORMCELLS RESULT: CHECK - written and read back clean; the copy for the re-freeze is not right (lines above; kept in $D); run nothing else, log to the ruling chat"; exit 1; }
  echo "=== 5 RE-FREEZE (read-only on both databases; writes $NEW + .sha256 only) ==="
  python3 -u "$N" --src "$LC" --prefill "$PF" --from-restore "$REP" --amend "$AM" --out "$NEW" > "$D/freeze.out" 2>&1; r=$?
  cat "$D/freeze.out"; echo "freeze exit $r (expect 0)"
  FL=""
  chk() { case "$(cat "$D/freeze.out")" in *"$2"*) echo "  $1: yes";; *) echo "  $1: NO (expected text: $2)"; FL="$FL $3";; esac; }
  chk "report = its .sha256" "restore report sha256 $XR = its .sha256" report
  chk "amendment file = its .sha256" "amendment file sha256 $XAM = its .sha256" amend
  chk "G0 4,418 = 3,878 + 539 + 1" "PASS — 4,418 = 3,878 insert + 539 update + 1 remove = the restore report + the amendment file" g0
  chk "rows 4,418" "rows                    4,418 | 4,418" rows
  chk "inserts / updates 3,878 / 539" "inserts / updates       3,878 / 539 | 3,878 / 539" split
  chk "removes 1" "removes                 1 | 1" removes
  chk "SNAPSHOT WRITTEN" "RESULT: SNAPSHOT WRITTEN" written
  [ "$r" = 0 ] || FL="$FL exit"
  if [ -n "$FL" ]; then echo "FORMCELLS RESULT: CHECK - written and read back clean; the re-freeze did not read as declared:$FL (the copy kept in $D); run nothing else, log to the ruling chat"; exit 1; fi
  echo "new frozen file: $NEW sha256 $(h "$NEW") ($(stat -c %s "$NEW") bytes); its .sha256: $(cut -d' ' -f1 "$NEW.sha256")"
  cp -- "$NEW" "$NEW.sha256" "$D/" && echo "copied into the run folder for the scp: yes"
  rm -- ~/edition_upgrade_runs/formcells_20261126/live_copy.db && [ ! -e "$LC" ] && echo "the copy removed: yes" || { echo "FORMCELLS RESULT: CHECK - all passed but the copy could not be removed; log to the ruling chat"; exit 1; }
  echo "home in use after: $(cut -f1 <<< "$(du -sk ~ 2>/dev/null)") KB (before $dk0 KB)"
  echo "FORMCELLS RESULT: DONE - 10 cells written and read back; re-frozen: 4,418 rows; the pins move in the next commit"
) 2>&1 | tee "$A"; echo "exit=${PIPESTATUS[0]}"
if [ -e "$D/started" ] && [ -z "$(ls "$Z" 2>/dev/null)" ]; then tar czf "$Z" --exclude=live_copy.db -C ~/edition_upgrade_runs formcells_20261126 && echo "PACKED: $Z"; fi
fi
