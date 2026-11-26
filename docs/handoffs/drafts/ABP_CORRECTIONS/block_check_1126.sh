set +H
L=~/edition_upgrade_runs/check_1126_$(date -u +%Y%m%d).log
if [ -e "$L" ]; then echo "CHECK1126 RESULT: STOP - log already exists (already ran? kept as is): $L"; else
( set -uo pipefail
REF=36b32377
export TZ=UTC LC_ALL=C PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
echo "GATE REF ${REF} - CHECK1126 - rebuild-words 1a on a fresh copy of live after the form-cell lane (DESIGN 9.272 (4)) - WRITES: a fresh copy of live in the run folder (sqlite backup; live opened read-only), REMOVED on PASS only; the run folder; this log - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "CHECK1126 RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
LIVE=~/bible-db/bible.db
PF=~/abp_surface_prefill_20261115.db
FX=tests/fixtures/rebuild_trap
SNAP=$FX/abp_surface_fill_20261126.tsv
OLD=$FX/abp_surface_fill_20261115.tsv
REP=$FX/restore_report_20261115.tsv
AM=tests/fixtures/surface_amend/abp_surface_amend_20261126.tsv
D=~/edition_upgrade_runs/check_1126
LC=~/edition_upgrade_runs/check_1126/live_copy.db
XS=3cc35e7d9fcfdc5c7d47da25ba1ba3785cdde504868e3e64cfde8aab4308fe28       # the 11/26 frozen file = SNAPSHOT_SHA256 (DESIGN 9.272)
XR=e154d8d4991aa02d49380d473c22b511d7c5a7be4c7239873b0bfe19ebc4748a       # the 11/15 report = REPORT_SHA256
XAM=acf9342309e043a806e25f0faf1cf35aa0cf935aec25b68a1400eb41429a7cd8      # the amendment file = AMEND_SHA256
XB4=ea6c54c34a86539929bee354f4b3390d7aadbdba081f5010233381e0fd4e7273      # the pre-fill table
XN=eaeee80750e658290c49f05866b9a69f954e2807515e4b82caf3285df5dbf228                                                                  # snapshot_surface_fill.py
XRS=88844099ff65c0c4dcc6dee0ce96c476cdae446e46b710f578dc5dabebcb60ce                                                                # restore_surface_fill.py (holds the pins)
XHOME_MAX=8400000                                                          # KB: STOP before the copy above this (DESIGN 9.236 (2))
h() { cut -d' ' -f1 <<< "$(sha256sum < "$1")"; }
inwin() { hm=$(date -u +%H%M); echo "UTC time $hm (STOP inside 1230-1430)"; [ "$hm" -ge 1230 ] && [ "$hm" -le 1430 ]; }
ck() { python3 scripts/snapshot_surface_fill.py --check --src "$LC" --prefill "$PF" --from-restore "$REP" "$@"; }
# --- before the copy: every miss is STOP; nothing written but the log ---
git merge-base --is-ancestor "$REF" HEAD && git diff --quiet "$REF" HEAD -- scripts tests && [ -z "$(git status --porcelain --untracked-files=no -- scripts tests)" ] || { echo "CHECK1126 RESULT: STOP - PA's scripts / tests are not $REF (run deploy.sh); nothing copied"; exit 1; }
echo "repo guards: $REF in HEAD's history, scripts / tests = $REF, nothing uncommitted there: yes"
inwin && { echo "CHECK1126 RESULT: STOP - inside the 12:30-14:30 UTC window; nothing copied"; exit 1; }
[ -e "$D" ] && { echo "CHECK1126 RESULT: STOP - the run folder already exists (kept as is): $D; nothing copied"; exit 1; }
for x in "$SNAP:$XS" "$SNAP.sha256:" "$OLD:" "$REP:$XR" "$REP.sha256:" "$AM:$XAM" "$AM.sha256:" "$PF:$XB4" "scripts/snapshot_surface_fill.py:$XN" "scripts/restore_surface_fill.py:$XRS"; do
  f=${x%%:*}; want=${x##*:}
  [ -s "$f" ] || { echo "CHECK1126 RESULT: STOP - missing or empty: $f; nothing copied"; exit 1; }
  if [ -n "$want" ]; then k=$(h "$f"); [ "$k" = "$want" ] || { echo "CHECK1126 RESULT: STOP - $f is not the pinned file ($k); nothing copied"; exit 1; }; fi
done
echo "files: the 11/26 frozen file, the report, the amendment file, the pre-fill table, both programs: as pinned; the 11/15 file present"
dk0=$(cut -f1 <<< "$(du -sk ~ 2>/dev/null)"); echo "home in use before: $dk0 KB (STOP above $XHOME_MAX KB; the copy adds about 442,000 KB)"
[ -n "$dk0" ] && [ "$dk0" -le "$XHOME_MAX" ] || { echo "CHECK1126 RESULT: STOP - home is above the ruled bound (or du gave nothing); nothing copied"; exit 1; }
fx0=$(ls -l --time-style=+%s "$FX" tests/fixtures/surface_amend | sha256sum | cut -d' ' -f1)
mkdir "$D" || { echo "CHECK1126 RESULT: STOP - cannot make the run folder $D"; exit 1; }
# --- the fresh copy (live opened read-only by sqlite's backup) ---
echo "=== (copy) sqlite backup of live into the run folder - start $(date -u +%FT%TZ) ==="
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
rc=$?; cat "$D/copy.out"; echo "copy exit $rc (expect 0) - end $(date -u +%FT%TZ)"
[ "$rc" = 0 ] && grep -qx "live journal mode (read): delete" "$D/copy.out" && grep -qx "copy quick_check: ok" "$D/copy.out" \
  && grep -qx "copy abp_surface: 395018" "$D/copy.out" || { echo "CHECK1126 RESULT: STOP - the copy is not right (lines above; anything made is in $D)"; exit 1; }
FL=""
# --- 1. the rebuild-words 1a command, on the copy: must read SNAPSHOT CURRENT ---
echo "=== 1. --check with --amend (rebuild-words 1a) ==="
ck --amend "$AM" --out "$SNAP" > "$D/check.out" 2>&1; r=$?
cat "$D/check.out"; echo "check exit $r (expect 0)"
chk() { case "$(cat "$D/check.out")" in *"$2"*) echo "  $1: yes";; *) echo "  $1: NO (expected text: $2)"; FL="$FL $3";; esac; }
echo "--- vs the declared figures (DESIGN 9.272):"
chk "frozen file = its .sha256 and the pin" "PASS — checksum file matches, = the pin in restore_surface_fill.py" pin
chk "report = its .sha256" "restore report sha256 $XR = its .sha256" report-file
chk "report = the pin" "restore report = the pin in restore_surface_fill.py" report-pin
chk "amendment file = its .sha256" "amendment file sha256 $XAM = its .sha256" amend-file
chk "amendment file = the pin" "amendment file = the pin in restore_surface_fill.py" amend-pin
chk "G0 4,418 = 3,878 + 539 + 1" "PASS — 4,418 = 3,878 insert + 539 update + 1 remove = the restore report + the amendment file" g0
chk "re-derived = the frozen file byte for byte" "PASS — 4,418 rows, identical bytes" bytes
chk "rows 4,418" "rows                    4,418 | 4,418" rows
chk "inserts / updates 3,878 / 539" "inserts / updates       3,878 / 539 | 3,878 / 539" split
chk "removes 1" "removes                 1 | 1" removes
chk "sha256 pin | file" "sha256                  $XS | $XS" sha
chk "SNAPSHOT CURRENT" "RESULT: SNAPSHOT CURRENT" current
[ "$r" = 0 ] || FL="$FL exit"
# --- 2. control: without --amend the check must STOP (the amendment file is pinned) ---
echo "=== 2. control: --check without --amend - must STOP ==="
ck --out "$SNAP" > "$D/check_noamend.out" 2>&1; rc1=$?
grep -E '^STOPPED|^RESULT' "$D/check_noamend.out" | cut -c1-300; echo "control exit $rc1 (expect 1)"
[ "$rc1" = 1 ] && grep -q -- "--check needs --amend" "$D/check_noamend.out" && [ "$(grep -c "SNAPSHOT CURRENT" "$D/check_noamend.out")" = 0 ] || FL="$FL control-noamend"
# --- 3. control: the 11/15 file is no longer the pinned one - must read STALE ---
echo "=== 3. control: --check on the 11/15 frozen file - must read STALE ==="
ck --amend "$AM" --out "$OLD" > "$D/check_old.out" 2>&1; rc2=$?
grep -E '^STOPPED|^RESULT' "$D/check_old.out" | cut -c1-300; echo "control exit $rc2 (expect 1)"
[ "$rc2" = 1 ] && grep -q "STALE SNAPSHOT" "$D/check_old.out" && [ "$(grep -c "SNAPSHOT CURRENT" "$D/check_old.out")" = 0 ] || FL="$FL control-old"
# --- 4. the health floor on the copy ---
echo "=== 4. health floor on the copy (395,018 since DESIGN 9.272) ==="
python3 scripts/health_check.py "$LC" --no-backup-check --no-disk-check > "$D/health.out" 2>&1
hl=$(grep "abp_surface rows BELOW floor" "$D/health.out"); echo "$hl"
case "$hl" in *"[OK  ] abp_surface rows BELOW floor 395018"*": 0 "*) echo "  floor line OK, shortfall 0: yes";; *) echo "  floor line OK, shortfall 0: NO"; FL="$FL floor";; esac
# --- nothing else written ---
fx1=$(ls -l --time-style=+%s "$FX" tests/fixtures/surface_amend | sha256sum | cut -d' ' -f1)
echo "fixture folders listing before = after: $([ "$fx1" = "$fx0" ] && echo yes || echo NO)"; [ "$fx1" = "$fx0" ] || FL="$FL fixtures-changed"
for x in -journal -wal -shm; do [ -e "$LC$x" ] && { echo "side file beside the copy: $LC$x"; FL="$FL copy-side-file"; }; done
if [ -n "$FL" ]; then
  echo "the copy is KEPT: $LC ($(stat -c %s "$LC") bytes); home in use: $(cut -f1 <<< "$(du -sk ~ 2>/dev/null)") KB"
  echo "CHECK1126 RESULT: CHECK -$FL (lines above; outputs and the copy in $D) - nothing on live changed; to the ruling chat as printed"; exit 1
fi
rm -- ~/edition_upgrade_runs/check_1126/live_copy.db; rr=$?
[ "$rr" = 0 ] && [ ! -e ~/edition_upgrade_runs/check_1126/live_copy.db ] && echo "the copy removed: yes" || { echo "CHECK1126 RESULT: CHECK - passed but the copy could not be removed; to the ruling chat"; exit 1; }
echo "home in use after: $(cut -f1 <<< "$(du -sk ~ 2>/dev/null)") KB (before $dk0 KB)"
echo "CHECK1126 RESULT: PASS - $(date -u +%FT%TZ) - SNAPSHOT CURRENT on a fresh copy of live (4,418 rows = 3,878 + 539 + 1, byte for byte; frozen file, report and amendment file = their pins); without --amend it STOPS; the 11/15 file reads STALE; floor 395,018 OK; the copy removed. The 11/15 file and the pre-fill table stay until this is ruled"; exit 0
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
