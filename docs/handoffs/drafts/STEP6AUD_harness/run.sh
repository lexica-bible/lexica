# run.sh <home> <tag> [KEY=VALUE overrides for mktest]: make the test block for <home>, run it AS WRITTEN with HOME=<home>,
# keep its screen output in ~/gate6/<tag>.out
set -uo pipefail
S6=/mnt/c/Users/JP/AppData/Local/Temp/claude/375bfdbef9aafd6e/2c800d5c-aa55-4d34-b144-23d87cfc5ca6/scratchpad/s6
H=$1; T=$2; shift 2
python3 "$S6/mktest.py" "$S6/block.sh" ~/gate6/block_$T.sh "$H" "$@" > ~/gate6/$T.diff || { cat ~/gate6/$T.diff; exit 1; }
start=$(date +%s)
BF=~/gate6/block_$T.sh; OF=~/gate6/$T.out
( export HOME="$H"; cd "$H"; bash "$BF" ) > "$OF" 2>&1
echo "ran $T in $(( $(date +%s) - start )) s"
