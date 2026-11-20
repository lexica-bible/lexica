set +H
L=~/edition_upgrade_runs/tipnr57_read_20261119.log
if [ -e "$L" ]; then echo "TIPNR57 RESULT: STOP - log already exists (already ran? it is kept as is): $L"; else
( set -uo pipefail
REF=d34d6723
export TZ=UTC
export PYTHONDONTWRITEBYTECODE=1                                           # no Python cache files written anywhere, the checkout included (reviewer, 11/20)
pc0=$(find ~/bible-db -name __pycache__ -type d | sort | xargs -r ls -la --time-style=+%s 2>/dev/null | sha256sum | cut -c1-16)
echo "GATE REF ${REF} - TIPNR57 - the import_tipnr -57 read (DESIGN 9.204: list / attribute the 57 lost import_tipnr matches, 10/25 31,649 -> built 31,592, and compare the tipnr table built vs src) - READ-ONLY: src, built and pre_8b opened mode=ro; the unchanged import_tipnr runs on an in-memory database only; writes only its run folder and this log; no database copy - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
cd ~/bible-db || { echo "TIPNR57 RESULT: STOP - cannot cd to ~/bible-db"; exit 1; }
B=~/bible-db/bible_edupg_test_built_20261102.db
S=~/bible-db/bible_edupg_test_20261101.db
P=~/bible-db/bible_edupg_test_built_pre_8b_20261106.db
R=~/edition_upgrade_runs
DH=$R/step4_headfix2_20261116
D=$R/tipnr57_read_20261119
U=$R/tipnr57_check_20261119.py                                             # the check program as JP uploaded it through PA's Files page; outside the repo
TL=$R/stageC_tail3_20261104.log                                            # built's import: tail v3 (HANDOFF_edition_upgrade_stageC_tail.md :57, 31,592 / 734 (687))
OL=~/bible-db/finish_pnstar2.log                                           # the 10/25-equivalent tail log (stageC_tail :55-57, 31,649 / 683 (648); rebuild-words :129-131)
BL=$R/step4_b_standard_20261117/finish.out                                 # BSTD's tail output (T_b = pre_8b, DESIGN 9.173) - a read-out; missing is printed, not a STOP
XS=5da9bb95c4b1337054dd8dd82ec3cbbb5ac97790c151ee56b33fdac0caf57e01       # src full sha256: HANDOFF_edition_upgrade_stageE.md :111
XP=a4faa4d8503296b18ba8368db1cd7d643783e9c5f15ea6b035cb9d4864ef0107       # pre_8b full sha256: DR "BSTD ran" :12384-12385 (DESIGN 9.173)
XTIP=1a3b7d7df5cfa1e96eefa07dec92900bea278370c6788fadb5d036f3223b637c     # tipnr/TIPNR.txt: cert_manifest.json :305-306 at d34d6723
XCHK=__XCHK__     # sha256 of the check program (DR: the TIPNR57 check program, CC's tested file); any other file STOPs
EU() { PYTHONIOENCODING=utf-8 python3 "$@"; }
h() { cut -d' ' -f1 <<< "$(sha256sum < "$1")"; }
# --- before the read: every miss is STOP ---
EU scripts/eu_step.py pre --tag TIPNR57 --ref "$REF" --dir "$D" --db "$S" --db "$B" --db "$P" || { echo "TIPNR57 RESULT: STOP - pre (line above); nothing read"; exit 1; }
git diff --quiet "$REF" HEAD -- tipnr cert_manifest.json || { echo "TIPNR57 RESULT: STOP - tipnr/ or cert_manifest.json differ from $REF"; exit 1; }
k=$(git status --porcelain -- tipnr cert_manifest.json); [ -z "$k" ] || { echo "TIPNR57 RESULT: STOP - tipnr/ or cert_manifest.json changed or added in the checkout: $k"; exit 1; }
echo "tipnr/, cert_manifest.json: = $REF, nothing changed or added in the checkout"
for f in "$U" "$TL" "$OL"; do [ -s "$f" ] || { echo "TIPNR57 RESULT: STOP - missing or empty: $f"; exit 1; }; done
echo "=== built = what HEADFIX2 left (eu_step check; read-only; DESIGN 9.156 (3)) ==="
EU scripts/eu_step.py check --tag TIPNR57 --built "$B" --dir "$DH" --written words,abp_corrections || { echo "TIPNR57 RESULT: STOP - built is not HEADFIX2's result (lines above)"; exit 1; }
k=$(h "$S"); echo "src sha256: $k (expect $XS)"; [ "$k" = "$XS" ] || { echo "TIPNR57 RESULT: STOP - src is not the 11/1 copy as recorded"; exit 1; }
k=$(h "$P"); echo "pre_8b sha256: $k (expect $XP)"; [ "$k" = "$XP" ] || { echo "TIPNR57 RESULT: STOP - pre_8b is not the 11/6 copy as recorded"; exit 1; }
st0=$(stat -c '%s %Y %n' "$S" "$B" "$P")
cp "$U" "$D/check.py" || { echo "TIPNR57 RESULT: STOP - cannot copy the uploaded check program into the run folder"; exit 1; }
k=$(h "$D/check.py"); echo "check.py sha256 (the uploaded file, as copied into the run folder): $k (expect $XCHK)"
[ "$k" = "$XCHK" ] || { echo "TIPNR57 RESULT: STOP - the uploaded check program is not the file CC wrote and tested"; exit 1; }
echo "=== the read - start $(date -u +%FT%TZ) ==="
# check.py is read ONCE; those bytes are hashed and those same bytes are run (DESIGN 9.190 (5) b)
EU -c 'import hashlib, sys
p, x = sys.argv[1], sys.argv[2]
b = open(p, "rb").read()
h = hashlib.sha256(b).hexdigest()
print("check.py sha256 as run: %s (expect %s)" % (h, x), flush=True)
h == x or sys.exit(4)
sys.path[0] == "" and sys.path.pop(0)
sys.argv = [p] + sys.argv[3:]
exec(compile(b, p, "exec"), {"__name__": "__main__"})' "$D/check.py" "$XCHK" \
  "S=$S" "B=$B" "P=$P" "D=$D" "REPO=$HOME/bible-db" "TL=$TL" "OL=$OL" "BL=$BL" "XTIP=$XTIP" < /dev/null > "$D/check.out" 2>&1; r2=$?
cat "$D/check.out"; echo "check exit $r2 (expect 0; 3 = findings; 2 = a STOP inside the read; 4 = check.py not the pinned bytes) - end $(date -u +%FT%TZ)"
# --- after: copies unchanged (read-only run) ---
st1=$(stat -c '%s %Y %n' "$S" "$B" "$P")
echo "src, built, pre_8b: size and time before = after: $([ "$st1" = "$st0" ] && echo yes || echo NO)"
pc1=$(find ~/bible-db -name __pycache__ -type d | sort | xargs -r ls -la --time-style=+%s 2>/dev/null | sha256sum | cut -c1-16)
echo "Python cache folders in the checkout before = after: $([ "$pc1" = "$pc0" ] && echo yes || echo NO) ($pc0 / $pc1)"
[ "$pc1" = "$pc0" ] || { echo "TIPNR57 RESULT: STOP - a Python cache file appeared or changed in the checkout - report this as printed"; exit 1; }
EU scripts/eu_step.py check --tag TIPNR57 --built "$B" --dir "$DH" --written words,abp_corrections > "$D/check_after.out" 2>&1; r3=$?
tail -n 1 "$D/check_after.out"; echo "built = HEADFIX2's result after: exit $r3 (expect 0)"
[ "$st1" = "$st0" ] && [ "$r3" = 0 ] || { echo "TIPNR57 RESULT: STOP - a copy changed during a read-only run - report this as printed"; exit 1; }
case "$r2" in
  0) echo "TIPNR57 RESULT: READ - $(date -u +%FT%TZ) - the figures and lists above go to the ruling chat as printed"; exit 0 ;;
  3) echo "TIPNR57 RESULT: FINDING - $(date -u +%FT%TZ) - the findings above (and $D/check.out) go to the ruling chat as printed; read-only, nothing to restore"; exit 1 ;;
  *) echo "TIPNR57 RESULT: STOP - the read stopped or did not finish (exit $r2; $D/check.out)"; exit 1 ;;
esac
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
