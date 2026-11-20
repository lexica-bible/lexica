# STEP7A tests: one test home = a clone at d34d6723 + the made-up copies + DELTA2 stand-ins + the real prose / eligible files
# + the "built =" guard folder + the uploaded check program + the block with ONLY XCHK (filled), XS, XWC, XVC swapped.
# usage: mkhome_s7a.sh <home> [plant]   (WSL only)
set -euo pipefail
T=/mnt/c/Users/JP/AppData/Local/Temp/claude/375bfdbef9aafd6e/4dc3eda8-b926-40ce-bd60-50e27a92e45e/scratchpad/s7a
P=/mnt/c/Users/JP/edition_upgrade_runs/pa
H=$1; PL=${2:-none}
rm -rf "$H"; mkdir -p "$H/edition_upgrade_runs"
git clone -q ~/gate4/repo "$H/bible-db"
cd "$H/bible-db"
[ "$(git log -1 --format=%h)" = d34d6723 ] || { echo "clone is not d34d6723"; exit 1; }
R=$H/edition_upgrade_runs
PYTHONDONTWRITEBYTECODE=1 python3 "$T/mkdbs_s7a.py" "$H/bible-db" "$R" "$P/prose_20261031.tsv" "$P/eligible_20261031.tsv" "$PL"
B=$H/bible-db/bible_edupg_test_built_20261102.db
export HOME="$H" PYTHONDONTWRITEBYTECODE=1
python3 scripts/eu_step.py pre --tag TESTPREP --ref d34d6723 --dir "$R/step4_headfix2_20261116" --db "$B" | tail -1
python3 scripts/eu_step.py prep --tag TESTPREP --built "$B" --dir "$R/step4_headfix2_20261116" --copy words,abp_corrections --save abp_corrections | tail -1
cp "$T/step7a_check.py" "$R/step7a_check_20261120.py"
XC=$(sha256sum < "$T/step7a_check.py" | cut -d' ' -f1)
XS=$(sha256sum < "$H/bible-db/bible_edupg_test_20261101.db" | cut -d' ' -f1)
XW=$(sha256sum < "$R/step4_delta2_20261116/delta/words_cells.tsv" | cut -d' ' -f1)
XV=$(sha256sum < "$R/step4_delta2_20261116/delta/verses_cells.tsv" | cut -d' ' -f1)
sed -e "s/__XCHK__/$XC/" -e "s/^XS=[0-9a-f]*/XS=$XS/" -e "s/^XWC=[0-9a-f]*/XWC=$XW/" -e "s/^XVC=[0-9a-f]*/XVC=$XV/" "$T/block.sh" > "$H/block.sh"
diff "$T/block.sh" "$H/block.sh" | grep '^[<>]' | cut -c1-90 || true
echo "home ready: $H"
