# P4 tests - each case on a WSL test home made by mkhome_p4.sh; the block as written (only XCHK, XS, XHOME_MAX swapped).
set -uo pipefail
T=/mnt/c/Users/JP/AppData/Local/Temp/claude/375bfdbef9aafd6e/cfce0c4f-7b18-4f6d-afde-d8ca6329f7ec/scratchpad/p4
G=~/gatep4
mkdir -p $G
hd() { echo; echo "=============== $* ==============="; }
mk() { bash "$T/mkhome_p4.sh" "$1" "${2:-none}" > "$1.mk" 2>&1 || { cat "$1.mk"; exit 1; }; }
run() { ( cd "$1" && HOME="$1" bash "$1/block.sh" ) 2>&1 | grep -v '^$' ; }
CASE=${1:-all}
echo "# P4 tests ($(date -u +%FT%TZ)); block sha256 $(sha256sum < $T/block_p4.sh | cut -d' ' -f1); check sha256 $(sha256sum < $T/p4_check.py | cut -d' ' -f1)"
hd "D1 clean (the expected picture: live differs only in ai_search_cache + lsj) -> DONE, every line printed"
H=$G/d1; mk $H; tail -4 $H.mk; run $H
echo "leak grep (planted AI text / definitions / summary in the log): $(grep -c 'SECRET' $H/edition_upgrade_runs/p4_live_tables_20261121.log)"
echo "...the same in the run folder's delta file (allowed there): $(grep -c 'SECRET' $H/edition_upgrade_runs/p4_live_tables_20261121/delta_live_vs_src.tsv)"
echo "cache folders in the checkout after: $(find $H/bible-db -name __pycache__ -type d | wc -l)"
[ "$CASE" = all ] || exit 0
hd "D2 live words differ from src -> FINDING (live words not LIVESRC's; words outside the three)"
H=$G/d2; mk $H livewords; run $H | grep -E "words on the live copy|outside|FINDING|RESULT|^exit="
hd "D3 live differs from src in books -> FINDING (outside the three, to JP with its count)"
H=$G/d3; mk $H books; run $H | grep -E "outside|FINDING|RESULT|^exit="
hd "D4 a table on live only -> FINDING"
H=$G/d4; mk $H extra; run $H | grep -E "one side only|FINDING|RESULT|^exit="
hd "D5 built has one strongs_base cell more than declared -> FINDING"
H=$G/d5; mk $H sb; run $H | grep -E "strongs_base cells|name-slot|FINDING|RESULT|^exit="
hd "D6 built lacks lsj.summary_v -> printed NO in (3) (a read-out, not a finding)"
H=$G/d6; mk $H nosumv; run $H | grep -E "lsj.summary_v|RESULT|^exit="
hd "D7 re-paste on D1's home -> STOP, log exists"
run $G/d1 | tail -2
hd "D8 the uploaded check program changed by one byte -> STOP before the copy (nothing copied)"
H=$G/d8; mk $H; echo "# x" >> $H/edition_upgrade_runs/p4_check_20261121.py; run $H | grep -E "sha256|check exit|RESULT|^exit="; ls $H/edition_upgrade_runs/p4_live_tables_20261121/
hd "D9 built changed after the guard folder was made -> STOP at the built guard, before the copy"
H=$G/d9; mk $H
python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute(\"UPDATE words SET english='x' WHERE id=1\"); c.commit()" $H/bible-db/bible_edupg_test_built_20261102.db
run $H | grep -E "written table words|copy\)|RESULT|^exit="; ls $H/edition_upgrade_runs/p4_live_tables_20261121/
hd "D10 home above the bound -> STOP before the copy"
H=$G/d10; mk $H; sed -i 's/^XHOME_MAX=[0-9]*/XHOME_MAX=1/' $H/block.sh; run $H | grep -E "home in use|copy\)|RESULT|^exit="
hd "D11 src not the recorded copy -> STOP"
H=$G/d11; mk $H; sed -i 's/^XS=[0-9a-f]*/XS=0000/' $H/block.sh; run $H | grep -E "src sha256|RESULT|^exit="
hd "D12 a cache file appears in scripts/__pycache__ while the block runs -> CHECK at the cache line"
H=$G/d12; mk $H
( F=$H/edition_upgrade_runs/p4_live_tables_20261121/check.py
  for i in $(seq 1 600); do [ -e "$F" ] && break; sleep 0.02; done
  mkdir -p $H/bible-db/scripts/__pycache__; echo z > $H/bible-db/scripts/__pycache__/late.cpython-312.pyc ) & BG=$!
run $H | grep -E "cache folders and their contents|RESULT|^exit="; wait $BG 2>/dev/null
hd "D13 built's verse ids differ from src's (one verse row renumbered on built) -> FINDING (rows not all matched)"
H=$G/d13; mk $H verseid; run $H | grep -E "matched|FINDING|RESULT|^exit="
hd "D14 built's verse id 5 names another verse (Gen 1:9 instead of 1:5) -> FINDING (verse ids)"
H=$G/d14; mk $H verserow; run $H | grep -E "verse id names|FINDING|RESULT|^exit="
