set +H
L=~/edition_upgrade_runs/p8_snapshot_check_$(date -u +%Y%m%d).log
if [ -e "$L" ]; then echo "P8 RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=7bb92e10
export TZ=UTC
export LC_ALL=C
export PYTHONIOENCODING=utf-8
export PYTHONDONTWRITEBYTECODE=1
export GIT_OPTIONAL_LOCKS=0
echo "GATE REF ${REF} - P8 - the 9c snapshot's --check against a fresh copy of the swapped live (charter 6 :340; DESIGN 9.235, 9.236) - WRITES: a fresh copy of live in the run folder (sqlite backup; live opened read-only by that step only), REMOVED by this block on PASS only; the run folder; this log. src and the pre-fill copy only read - site UP - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "P8 RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
LIVE=~/bible-db/bible.db
S=~/bible-db/bible_edupg_test_20261101.db                                 # src: the 11/1 copy of pre-upgrade live (the old layout) - the control that must read STALE, as STEP9C-CHECK's (DESIGN 9.134 (ii), 9.137)
PF=~/abp_surface_prefill_20261115.db
FX=tests/fixtures/rebuild_trap
SNAP=$FX/abp_surface_fill_20261115.tsv
REP=$FX/restore_report_20261115.tsv
D=~/edition_upgrade_runs/p8_snapshot_check
LC=~/edition_upgrade_runs/p8_snapshot_check/live_copy.db
XS=d025cc086cd7f325bafe3c89655c778f8cdc57f67ba127061a3edfd2192472ff       # the frozen snapshot = SNAPSHOT_SHA256 (restore_surface_fill.py :81; DESIGN 9.133, 9.137)
XR=e154d8d4991aa02d49380d473c22b511d7c5a7be4c7239873b0bfe19ebc4748a       # the restore report = REPORT_SHA256 (restore_surface_fill.py :85)
XB4=ea6c54c34a86539929bee354f4b3390d7aadbdba081f5010233381e0fd4e7273      # the pre-fill copy (DESIGN 9.128, 9.134; STEP9C-CHECK's XB4)
XSRC=5da9bb95c4b1337054dd8dd82ec3cbbb5ac97790c151ee56b33fdac0caf57e01     # src full sha256 (DESIGN 9.168 (1), 9.181; P6A read it 11/21)
XW="626309 d95acb5d4be4"                                                   # the copy's words: rows + digest head = P7's read of live (DESIGN 9.235)
XA="395014 219a3ebe7075"                                                   # the copy's abp_surface = P7's read of live (DESIGN 9.235)
XHOME_MAX=8400000                                                          # KB: STOP before the copy above this (DESIGN 9.236 (2))
h() { cut -d' ' -f1 <<< "$(sha256sum < "$1")"; }
inwin() { hm=$(date -u +%H%M); echo "UTC time $hm (STOP inside 1300-1430)"; [ "$hm" -ge 1300 ] && [ "$hm" -le 1430 ]; }
pcf() { find ~/bible-db \( -name __pycache__ -type d -o -path '*/__pycache__/*' \) -printf '%M %u %g %s %T@ %p\n' 2>/dev/null | sort | sha256sum | cut -c1-16; }   # DESIGN 9.209
ck() { python3 scripts/snapshot_surface_fill.py --check --src "$1" --prefill "$PF" "$2" "$3" --out "$SNAP" > "$4" 2>&1; }
# --- before the copy: every miss is STOP; nothing written but the log ---
git merge-base --is-ancestor "$REF" HEAD && git diff --quiet "$REF" HEAD -- scripts tests ai.py && [ -z "$(git status --porcelain --untracked-files=no -- scripts tests ai.py)" ] || { echo "P8 RESULT: STOP - PA's scripts / tests / ai.py are not $REF (the swap commit); nothing copied"; exit 1; }
echo "repo guards: $REF in HEAD's history, scripts / tests / ai.py = $REF, nothing uncommitted there: yes"
inwin && { echo "P8 RESULT: STOP - inside the 13:00-14:30 UTC backup / health window; nothing copied"; exit 1; }
[ -e "$D" ] && { echo "P8 RESULT: STOP - the run folder already exists (an earlier run? it is kept as is): $D; nothing copied"; exit 1; }
for f in "$LIVE" "$S" "$PF" "$SNAP" "$SNAP.sha256" "$REP" "$REP.sha256"; do [ -s "$f" ] || { echo "P8 RESULT: STOP - missing or empty: $f; nothing copied"; exit 1; }; done
for f in "$S" "$PF"; do [ -e "$f-journal" ] && { echo "P8 RESULT: STOP - side file $f-journal; nothing copied"; exit 1; }; done
k=$(h "$SNAP"); echo "snapshot $SNAP: sha256 $k (expect $XS)"; [ "$k" = "$XS" ] || { echo "P8 RESULT: STOP - not the pinned snapshot; nothing copied"; exit 1; }
k=$(h "$REP"); echo "report $REP: sha256 $k (expect $XR)"; [ "$k" = "$XR" ] || { echo "P8 RESULT: STOP - not the pinned report; nothing copied"; exit 1; }
k=$(h "$PF"); echo "pre-fill copy $PF: sha256 $k (expect $XB4)"; [ "$k" = "$XB4" ] || { echo "P8 RESULT: STOP - not the recorded pre-fill copy; nothing copied"; exit 1; }
k=$(h "$S"); echo "src $S: sha256 $k (expect $XSRC)"; [ "$k" = "$XSRC" ] || { echo "P8 RESULT: STOP - src is not the 11/1 copy as recorded; nothing copied"; exit 1; }
dk0=$(cut -f1 <<< "$(du -sk ~ 2>/dev/null)"); echo "home in use before: $dk0 KB (STOP above $XHOME_MAX KB; the copy adds about 442,000 KB after this check)"
[ -n "$dk0" ] && [ "$dk0" -le "$XHOME_MAX" ] || { echo "P8 RESULT: STOP - home is above the ruled bound (or du gave nothing); nothing copied; read the dashboard and the ruling chat first"; exit 1; }
stat -c 'live before: %s bytes, last write %y (printed only; the site is up)' "$LIVE"
for x in -journal -wal -shm; do echo "beside live: bible.db$x $([ -e "$LIVE$x" ] && echo present || echo absent) (printed only)"; done
st0=$(stat -c '%s %Y' "$S" "$PF" | tr '\n' ' '); fx0=$(ls -l --time-style=+%s "$FX" | sha256sum | cut -d' ' -f1); pc0=$(pcf)
inwin && { echo "P8 RESULT: STOP - the reads ran into the 13:00-14:30 UTC window; nothing copied"; exit 1; }
mkdir "$D" || { echo "P8 RESULT: STOP - cannot make the run folder $D"; exit 1; }
# --- the write: the fresh copy (live opened read-only by sqlite's backup; the copy set to journal_mode=DELETE) - P4's step ---
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
print("copy triggers: %d" % c.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0])
c.close()
print("copy: %d bytes" % os.path.getsize(dst))
PY
rc=$?; cat "$D/copy.out"
echo "copy exit $rc (expect 0) - end $(date -u +%FT%TZ)"
[ "$rc" = 0 ] && [ -s "$LC" ] || { echo "P8 RESULT: STOP - the copy did not finish (anything made is left in $D for the ruling chat)"; exit 1; }
for x in -journal -wal -shm; do [ -e "$LC$x" ] && { echo "P8 RESULT: STOP - a side file beside the copy: $LC$x (left as is)"; exit 1; }; done
stat -c 'live after the copy: %s bytes, last write %y (printed only)' "$LIVE"
for x in -journal -wal -shm; do echo "beside live after the copy: bible.db$x $([ -e "$LIVE$x" ] && echo present || echo absent) (printed only; -wal / -shm are never expected)"; done
grep -qx "live journal mode (read): delete" "$D/copy.out" || { echo "P8 RESULT: STOP - live's journal mode is not delete (line above); the check NOT run (the copy kept in $D) - TO THE RULING CHAT NOW"; exit 1; }
grep -qx "copy quick_check: ok" "$D/copy.out" && grep -qx "copy triggers: 0" "$D/copy.out" || { echo "P8 RESULT: STOP - the copy's quick_check is not ok or it carries a trigger (the copy kept in $D)"; exit 1; }
# --- the copy = what P7 read on live, for the two tables the check reads beside verses: else STOP before the check ---
dg=$(python3 - "$LC" "$HOME/bible-db" <<'PY'
import os, sys
sys.path[0] == "" and sys.path.pop(0)
sys.path.insert(0, os.path.join(sys.argv[2], "scripts"))
import eu_step as E
c = E.ro(sys.argv[1])
for t in ("words", "abp_surface"):
    n, d = E.digest(c, t)
    print("%s %d %s" % (t, n, d[:12]))
c.close()
PY
); rg=$?
echo "$dg"
gw=$(sed -n 's/^words //p' <<< "$dg"); ga=$(sed -n 's/^abp_surface //p' <<< "$dg")
echo "the copy's words = P7's read of live ($XW): $([ "$gw" = "$XW" ] && echo yes || echo NO); abp_surface ($XA): $([ "$ga" = "$XA" ] && echo yes || echo NO); digest exit $rg"
[ "$rg" = 0 ] && [ "$gw" = "$XW" ] && [ "$ga" = "$XA" ] || { echo "P8 RESULT: STOP - the copy's words or abp_surface is not what P7 read on live; the check NOT run (the copy kept in $D)"; exit 1; }
FL=""
# --- 1. the check (the rebuild-words 1a command, --src = the copy): must read SNAPSHOT CURRENT ---
echo "=== 1. --check on the fresh copy of the swapped live (rebuild-words 1a, :74) ==="
ck "$LC" --from-restore "$REP" "$D/check_live.out"; r=$?
cat "$D/check_live.out"; echo "check exit $r (expect 0)"
chk() { case "$(cat "$D/check_live.out")" in *"$2"*) echo "  $1: yes";; *) echo "  $1: NO (expected text: $2)"; FL="$FL $3";; esac; }
echo "--- vs the declared figures (STEP9C-CHECK's nine lines, DESIGN 9.137):"
chk "frozen file = its .sha256 and the pin" "PASS — checksum file matches, = the pin in restore_surface_fill.py" pin
chk "report = its .sha256" "restore report sha256 $XR = its .sha256" report-file
chk "report = the pin (R1)" "restore report = the pin in restore_surface_fill.py" report-pin
chk "G0 = the report, 4,411 = 3,873 + 538" "PASS — 4,411 = 3,873 insert + 538 update = the restore report" g0
chk "re-derived = the frozen file byte for byte" "PASS — 4,411 rows, identical bytes" bytes
chk "rows 4,411" "rows                    4,411 | 4,411" rows
chk "inserts / updates 3,873 / 538" "inserts / updates       3,873 / 538 | 3,873 / 538" split
chk "sha256 pin | file" "sha256                  $XS | $XS" sha
chk "SNAPSHOT CURRENT" "RESULT: SNAPSHOT CURRENT" current
[ "$r" = 0 ] || FL="$FL exit"
# --- 2. control (the check must be able to fail today): --src = src, the old layout -> must read STALE ---
echo "=== 2. control: --check with --src = src (the 11/1 copy, the old layout) - must read STALE (as STEP9C-CHECK's control, DESIGN 9.137) ==="
ck "$S" --from-restore "$REP" "$D/check_src.out"; rc1=$?
cut -c1-300 <<< "$(grep -E '^STOPPED|^RESULT' "$D/check_src.out")"; echo "control exit $rc1 (expect 1)"
[ "$rc1" = 1 ] && grep -q "STALE SNAPSHOT" "$D/check_src.out" && [ "$(grep -c "SNAPSHOT CURRENT" "$D/check_src.out")" = 0 ] || FL="$FL control-src"
# --- nothing else written ---
st1=$(stat -c '%s %Y' "$S" "$PF" | tr '\n' ' '); fx1=$(ls -l --time-style=+%s "$FX" | sha256sum | cut -d' ' -f1); pc1=$(pcf)
echo "src and the pre-fill copy: size and time before = after: $([ "$st1" = "$st0" ] && echo yes || echo NO); fixture folder listing before = after: $([ "$fx1" = "$fx0" ] && echo yes || echo NO); the checkout's cache folders unchanged: $([ "$pc1" = "$pc0" ] && echo yes || echo NO)"
[ "$st1" = "$st0" ] && [ "$fx1" = "$fx0" ] && [ "$pc1" = "$pc0" ] || FL="$FL changed-during-run"
for x in -journal -wal -shm; do [ -e "$LC$x" ] && { echo "side file beside the copy after the check: $LC$x"; FL="$FL copy-side-file"; }; done
if [ -n "$FL" ]; then
  echo "the copy is KEPT: $LC ($(stat -c %s "$LC") bytes); home in use: $(cut -f1 <<< "$(du -sk ~ 2>/dev/null)") KB"
  echo "P8 RESULT: CHECK -$FL (lines above; outputs and the copy in $D) - nothing on live is changed by this; to the ruling chat as printed; the 10/25 pre-fill copy and snapshot stay"; exit 1
fi
# --- PASS only: the block removes its own copy, named by its full fixed path (DESIGN 9.236 (3)) ---
echo "the copy's sha256 before it is removed: $(h "$LC") ($(stat -c %s "$LC") bytes)"
rm -- ~/edition_upgrade_runs/p8_snapshot_check/live_copy.db; rr=$?
still=no; [ -e ~/edition_upgrade_runs/p8_snapshot_check/live_copy.db ] && still=yes
[ "$rr" = 0 ] && [ "$still" = no ] && echo "the copy removed: yes" || { echo "the copy removed: NO (rm exit $rr; still there: $still)"; echo "P8 RESULT: CHECK - the check passed but the copy could not be removed; to the ruling chat as printed"; exit 1; }
dk1=$(cut -f1 <<< "$(du -sk ~ 2>/dev/null)"); echo "home in use after: $dk1 KB (before $dk0 KB)"
echo "P8 RESULT: PASS - $(date -u +%FT%TZ) - SNAPSHOT CURRENT on a fresh copy of the swapped live (4,411 rows, byte for byte; snapshot + report = their pins); the src control read STALE; the copy removed; this log to the ruling chat by cat. The 10/25 pre-fill copy and snapshot stay until a removal is ruled"; exit 0
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
