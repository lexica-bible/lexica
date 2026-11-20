# TIPNR57 tests: one test home = a clone at d34d6723 + the made-up copies + logs + the "built =" guard folder + the
# uploaded check program + the block with ONLY XCHK (filled), XS and XP (the test copies' shas) swapped.
# usage: mkhome57.sh <home> [plant]   (WSL only)
set -euo pipefail
T=/mnt/c/Users/JP/AppData/Local/Temp/claude/375bfdbef9aafd6e/4dc3eda8-b926-40ce-bd60-50e27a92e45e/scratchpad/t57
H=$1; PL=${2:-none}
rm -rf "$H"; mkdir -p "$H/edition_upgrade_runs"
git clone -q ~/gate4/repo "$H/bible-db"
cd "$H/bible-db"
[ "$(git log -1 --format=%h)" = d34d6723 ] || { echo "clone is not d34d6723"; exit 1; }
R=$H/edition_upgrade_runs
python3 "$T/mkdbs57.py" "$H/bible-db" "$H/bible-db" "$R" "$PL"
B=$H/bible-db/bible_edupg_test_built_20261102.db
export HOME="$H"
python3 scripts/eu_step.py pre --tag TESTPREP --ref d34d6723 --dir "$R/step4_headfix2_20261116" --db "$B" | tail -1
python3 scripts/eu_step.py prep --tag TESTPREP --built "$B" --dir "$R/step4_headfix2_20261116" --copy words,abp_corrections --save abp_corrections | tail -1
cp "$T/tipnr57_check.py" "$R/tipnr57_check_20261119.py"
XC=$(sha256sum < "$T/tipnr57_check.py" | cut -d' ' -f1)
XS=$(sha256sum < "$H/bible-db/bible_edupg_test_20261101.db" | cut -d' ' -f1)
XP=$(sha256sum < "$H/bible-db/bible_edupg_test_built_pre_8b_20261106.db" | cut -d' ' -f1)
sed -e "s/__XCHK__/$XC/" -e "s/^XS=[0-9a-f]*/XS=$XS/" -e "s/^XP=[0-9a-f]*/XP=$XP/" "$T/block.sh" > "$H/block.sh"
diff "$T/block.sh" "$H/block.sh" | grep '^[<>]' | cut -c1-80 || true
echo "home ready: $H"
