set -uo pipefail
T=/mnt/c/Users/JP/AppData/Local/Temp/claude/375bfdbef9aafd6e/cfce0c4f-7b18-4f6d-afde-d8ca6329f7ec/scratchpad/p4
G=~/gatep4b; mkdir -p $G
run() { ( cd "$1" && HOME="$1" bash "$T/block_p4b.sh" ) 2>&1 | grep -v '^$'; }
echo "# P4B tests; block sha256 $(sha256sum < $T/block_p4b.sh | cut -d' ' -f1)"
echo "== E1 clean (2 of 5 live ids retired on src; 3 new on src)"; rm -rf $G/e1; python3 $T/mk_p4b.py $G/e1; run $G/e1
echo "leak grep: $(grep -c SECRET $G/e1/edition_upgrade_runs/p4b_corrections_ids_20261121.log)"
echo "== E2 re-paste -> STOP"; run $G/e1 | tail -2
echo "== E3 built lacks the columns -> STOP"; rm -rf $G/e3; python3 $T/mk_p4b.py $G/e3 nocol; run $G/e3 | tail -4
echo "== E4 the live copy missing -> STOP"; rm -rf $G/e4; python3 $T/mk_p4b.py $G/e4; rm $G/e4/edition_upgrade_runs/p4_live_tables_20261121/live_copy_20261121.db; run $G/e4 | tail -2
echo "== E5 a -journal beside src -> STOP"; rm -rf $G/e5; python3 $T/mk_p4b.py $G/e5; touch $G/e5/bible-db/bible_edupg_test_20261101.db-journal; run $G/e5 | tail -2
echo "== E6 copies unchanged by E1: $(cd $G/e1 && python3 -c 'print(1)' >/dev/null; sha256sum $G/e1/bible-db/*.db | cut -c1-12 | tr '\n' ' ')"
