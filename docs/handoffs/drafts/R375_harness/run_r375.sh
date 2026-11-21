set -uo pipefail
T=/mnt/c/Users/JP/AppData/Local/Temp/claude/375bfdbef9aafd6e/cfce0c4f-7b18-4f6d-afde-d8ca6329f7ec/scratchpad/p5
G=~/gater375; mkdir -p $G
XP=$(sha256sum < $T/dump375.py | cut -d' ' -f1)
mk() { rm -rf "$1"; mkdir -p "$1"; git clone -q ~/gate4/repo "$1/bible-db"; python3 $T/mk_r375.py "$1" "${2:-none}"; cp $T/dump375.py "$1/edition_upgrade_runs/dump375_20261121.py"
  XB=$(sha256sum < "$1/bible-db/bible_edupg_test_built_20261102.db" | cut -d' ' -f1)
  sed -e "s/__XP__/$XP/" -e "s/^XB=[0-9a-f]*/XB=$XB/" $T/block_r375.sh > "$1/block.sh"; }
run() { ( cd "$1" && HOME="$1" bash "$1/block.sh" ) 2>&1 | grep -v '^$'; }
echo "# R375 tests; block sha256 $(sha256sum < $T/block_r375.sh | cut -d' ' -f1); program sha256 $XP"
echo "== F1 clean -> OK, the file = the local derivation"; mk $G/f1; run $G/f1
echo "file vs local derivation: $(cmp $G/f1/edition_upgrade_runs/repin375_20261121/abp_corrections_active_built_20261121.txt $T/abp_corrections_active_built_20261121.local.txt && echo identical)"
echo "== F2 re-paste -> STOP"; run $G/f1 | tail -2
echo "== F3 one extra active row on built -> STOP, nothing written"; mk $G/f3 extra; run $G/f3 | grep -E "active ingest|NEW|REPIN375|R375|exit="; ls $G/f3/edition_upgrade_runs/repin375_20261121/
echo "== F4 retired 22 -> STOP"; mk $G/f4 retired; run $G/f4 | grep -E "retired total|REPIN375|R375 RESULT|exit="
echo "== F5 the 374 file altered -> STOP before the read"; mk $G/f5 oldfile; run $G/f5 | grep -E "374-row|REPIN375|R375 RESULT|exit="
echo "== F6 program changed one byte -> STOP, nothing read"; mk $G/f6; echo "# x" >> $G/f6/edition_upgrade_runs/dump375_20261121.py; run $G/f6 | tail -3
echo "== F7 built not the P4 copy (sha) -> STOP"; mk $G/f7; sed -i 's/^XB=[0-9a-f]*/XB=0000/' $G/f7/block.sh; run $G/f7 | tail -3
echo "== F8 a -journal beside built -> STOP"; mk $G/f8; touch $G/f8/bible-db/bible_edupg_test_built_20261102.db-journal; run $G/f8 | tail -2
echo "== F9 scripts differ from REF (a test file edited, uncommitted) -> STOP before anything"; mk $G/f9; echo "# x" >> $G/f9/bible-db/tests/test_reorder_port.py; run $G/f9 | tail -2
echo "== F10 the checkout is not at a descendant of REF -> STOP"; mk $G/f10; (cd $G/f10/bible-db && git checkout -q d34d6723~1 2>/dev/null); run $G/f10 | tail -2
