set +H
L=~/edition_upgrade_runs/p6a_swap_pre.log
if [ -e "$L" ]; then echo "P6A RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=d34d6723
export TZ=UTC
export PYTHONDONTWRITEBYTECODE=1
export GIT_OPTIONAL_LOCKS=0
pcf() { find ~/bible-db \( -name __pycache__ -type d -o -path '*/__pycache__/*' \) -printf '%M %u %g %s %T@ %p\n' 2>/dev/null | sort | sha256sum | cut -c1-16; }   # DESIGN 9.209
pc0=$(pcf)
echo "GATE REF ${REF} - P6A - the swap, part A: every check that can run with the site UP (DESIGN 9.213 P6, 9.228) - READ-ONLY: src + built opened read-only; live only stat'd; writes only the run folder (src's table digests) and this log - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "P6A RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
S=~/bible-db/bible_edupg_test_20261101.db
B=~/bible-db/bible_edupg_test_built_20261102.db
LIVE=~/bible-db/bible.db
R=~/edition_upgrade_runs
DH=$R/step4_headfix2_20261116                                              # the HEADFIX2 guard folder (DESIGN 9.156 (3))
D=$R/p6_swap                                                               # one run folder for P6A / P6B / P6C (one swap)
U=$R/p6_check_20261121.py                                                  # the check program as JP uploaded it through PA's Files page
XS=5da9bb95c4b1337054dd8dd82ec3cbbb5ac97790c151ee56b33fdac0caf57e01       # src full sha256 (DESIGN 9.168 (1), 9.181)
XB=d2c8603b4700d6dce089b688c5e00e8a3fdec879eea96bef5a6ce7cd09ca1523       # built full sha256 = P6's pin (DESIGN 9.222 (1))
XP=__XP__                                                                  # sha256 of the check program CC wrote and tested; any other file STOPs
NEWF="tests/fixtures/corrections/abp_corrections_active_built_20261121.txt tests/fixtures/corrections/abp_corrections_active_built_20261121.txt.sha256"   # the swap commit's two NEW paths (DESIGN 9.227 (2))
EU() { PYTHONIOENCODING=utf-8 python3 "$@"; }
h() { cut -d' ' -f1 <<< "$(sha256sum < "$1")"; }
EU scripts/eu_step.py pre --tag P6A --ref "$REF" --dir "$D" --db "$S" --db "$B" || { echo "P6A RESULT: STOP - pre (line above); nothing written but the run folder"; exit 1; }
for f in "$U" "$LIVE"; do [ -s "$f" ] || { echo "P6A RESULT: STOP - missing or empty: $f"; exit 1; }; done
k=$(h "$U"); echo "uploaded check program sha256: $k (expect $XP)"
[ "$k" = "$XP" ] || { echo "P6A RESULT: STOP - the uploaded check program is not the file CC wrote and tested"; exit 1; }
echo "=== built = what HEADFIX2 left (eu_step check; read-only; DESIGN 9.156 (3)) ==="
EU scripts/eu_step.py check --tag P6A --built "$B" --dir "$DH" --written words,abp_corrections || { echo "P6A RESULT: STOP - built is not HEADFIX2's result (lines above)"; exit 1; }
s0=$(h "$S"); echo "src sha256: $s0 (expect $XS)"; [ "$s0" = "$XS" ] || { echo "P6A RESULT: STOP - src is not the 11/1 copy as recorded"; exit 1; }
b0=$(h "$B"); echo "built sha256: $b0 (expect $XB)"; [ "$b0" = "$XB" ] || { echo "P6A RESULT: STOP - built is not the copy P4 read"; exit 1; }
for f in "$LIVE" "$B" "$S"; do for x in -journal -wal -shm; do [ -e "$f$x" ] && { echo "P6A RESULT: STOP - side file present: $f$x (left as is)"; exit 1; }; done; done
echo "no -journal / -wal / -shm beside live, built or src: yes"
dl=$(stat -c %d "$LIVE"); db=$(stat -c %d "$B"); echo "live and built on the same device (so mv is a rename): $([ "$dl" = "$db" ] && echo yes || echo NO) ($dl / $db)"
[ "$dl" = "$db" ] || { echo "P6A RESULT: STOP - live and built are on different devices"; exit 1; }
rb=$(find ~/bible-db -maxdepth 1 -name 'bible_pre_edition_upgrade_*' | wc -l); echo "existing bible_pre_edition_upgrade_* files: $rb (expect 0)"
[ "$rb" = 0 ] || { echo "P6A RESULT: STOP - a rollback-named file already exists"; exit 1; }
for p in $NEWF; do [ -e "$p" ] && { echo "P6A RESULT: STOP - the swap commit's new path already exists in PA's checkout: $p (a pull would refuse it)"; exit 1; }; done
echo "the swap commit's two new paths absent in PA's checkout: yes"
stat -c 'live now: %s bytes, last write %y (printed only)' "$LIVE"
cp "$U" "$D/check.py" || { echo "P6A RESULT: STOP - cannot copy the program into the run folder"; exit 1; }
# check.py is read ONCE; those bytes are hashed and those same bytes are run (DESIGN 9.190 (5)(b); TIPNR57's launcher, DR :15775-15785)
EU -c 'import hashlib, sys
p, x = sys.argv[1], sys.argv[2]
b = open(p, "rb").read()
h = hashlib.sha256(b).hexdigest()
print("check.py sha256 as run: %s (expect %s)" % (h, x), flush=True)
h == x or sys.exit(4)
sys.path[0] == "" and sys.path.pop(0)
sys.argv = [p] + sys.argv[3:]
exec(compile(b, p, "exec"), {"__name__": "__main__"})' "$D/check.py" "$XP" "MODE=pre" "S=$S" "B=$B" "D=$D" "REPO=$HOME/bible-db" < /dev/null; r=$?
echo "check exit $r (expect 0; 2 = a STOP inside; 4 = not the pinned bytes)"
[ "$r" = 0 ] || { echo "P6A RESULT: STOP - the pre-read stopped (lines above)"; exit 1; }
s1=$(h "$S"); [ "$s1" = "$s0" ] || { echo "P6A RESULT: CHECK - src changed during the read"; exit 1; }
pc1=$(pcf); echo "the checkout's cache folders and their contents unchanged: $([ "$pc1" = "$pc0" ] && echo yes || echo NO)"; [ "$pc1" = "$pc0" ] || { echo "P6A RESULT: CHECK - cache folders changed"; exit 1; }
h0=$(date -u +%H%M); echo "UTC now $h0 - P6B must start outside 13:00-14:30 UTC (DESIGN 9.215, 9.228)"
echo "P6A RESULT: DONE - CC pushes the swap commit next (PA does NOT pull it); then JP pastes P6R"; exit 0
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
