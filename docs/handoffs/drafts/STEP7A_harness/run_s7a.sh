# STEP7A tests - each case on a WSL test home made by mkhome_s7a.sh; the block as written (only the shas swapped).
set -uo pipefail
T=/mnt/c/Users/JP/AppData/Local/Temp/claude/375bfdbef9aafd6e/4dc3eda8-b926-40ce-bd60-50e27a92e45e/scratchpad/s7a
G=~/gates7a
mkdir -p $G
hd() { echo; echo "=============== $* ==============="; }
mk() { bash "$T/mkhome_s7a.sh" "$1" "${2:-none}" > "$1.mk" 2>&1 || { cat "$1.mk"; exit 1; }; }
run() { ( cd "$1" && HOME="$1" bash "$1/block.sh" ) 2>&1 | grep -v '^$' ; }
CASE=${1:-all}
echo "# STEP7A tests ($(date -u +%FT%TZ)); block sha256 $(sha256sum < $T/block.sh | cut -d' ' -f1); check sha256 $(sha256sum < $T/step7a_check.py | cut -d' ' -f1)"

if [ "$CASE" = all ] || [ "$CASE" = a1 ]; then
hd "A1 clean pair (the declared picture) -> READ, every line printed"
H=$G/a1; mk $H; cat $H.mk | tail -3; run $H
echo "cache folders in the checkout after: $(find $H/bible-db -name __pycache__ -type d | wc -l)"
fi
if [ "$CASE" = all ]; then
hd "A2 built Gen 1:21 @19 'types:' (one cell more than declared) -> FINDING (fresh vs declared, fresh vs DELTA2)"
H=$G/a2; mk $H extra; run $H | grep -E "FINDING|  Gen 1:21 |RESULT|^exit="
hd "A3 built 1Ch 13:10: the LORD's greek_pos above the verb's -> FINDING (chip order), src clean"
H=$G/a3; mk $H chip; run $H | grep -E "1Ch 13:10 (src|built)|FINDING|RESULT|^exit="
hd "A4 built Adam's xref H122 -> FINDING (built not H121; built != src)"
H=$G/a4; mk $H adam; run $H | grep -E "1Ch 1:1 .*(xref|Adam)|FINDING|RESULT|^exit="
hd "A5 both copies' G2206 lemma 'ζηλῶ' -> FINDING on both"
H=$G/a5; mk $H lemma; run $H | grep -E "Eze 31:9 (src|built):|FINDING|RESULT|^exit="
hd "A6 the DELTA2 stand-in lacks Mark 1:9 @13 -> FINDING (fresh vs DELTA2 differs at Mark 1:9 only)"
H=$G/a6; mk $H d2miss; run $H | grep -E "fresh [0-9]+ lines - DELTA2|FINDING|RESULT|^exit="
hd "A7 re-paste on A1's home -> STOP, log exists"
run $G/a1 | tail -2
hd "A8 the uploaded check program changed by one byte -> STOP before the check runs"
H=$G/a8; mk $H; echo "# x" >> $H/edition_upgrade_runs/step7a_check_20261120.py; run $H | grep -E "check.py sha256|RESULT|^exit="
hd "A9 built changed after the guard folder was made (one words cell) -> STOP at the built guard, nothing read"
H=$G/a9; mk $H
python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute(\"UPDATE words SET english='Seth.' WHERE english='Seth,'\"); c.commit()" $H/bible-db/bible_edupg_test_built_20261102.db
run $H | grep -E "written table words|CHECK|RESULT|^exit="
hd "A10 KNOWN POSITIVE for the cache line: a cache file appears in scripts/__pycache__ while the block runs -> STOP at the cache line"
H=$G/a10; mk $H
( F=$H/edition_upgrade_runs/step7a_spotcheck_20261120/check.py
  for i in $(seq 1 600); do [ -e "$F" ] && break; sleep 0.02; done
  mkdir -p $H/bible-db/scripts/__pycache__; echo z > $H/bible-db/scripts/__pycache__/late.cpython-312.pyc ) & BG=$!
run $H | grep -E "cache folders and their contents|RESULT|^exit="; wait $BG 2>/dev/null
hd "A11 the checkout folder itself changes while the block runs (a file made and removed in ~/bible-db) -> the cache line holds, READ"
H=$G/a11; mk $H
( F=$H/edition_upgrade_runs/step7a_spotcheck_20261120/check.py
  for i in $(seq 1 600); do [ -e "$F" ] && break; sleep 0.02; done
  echo x > $H/bible-db/zz.tmp; rm $H/bible-db/zz.tmp ) & BG=$!
run $H | grep -E "cache folders and their contents|RESULT|^exit="; wait $BG 2>/dev/null
fi
