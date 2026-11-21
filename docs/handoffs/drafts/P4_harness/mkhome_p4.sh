# P4 tests: one test home = a clone at d34d6723 + the made-up copies + the "built =" guard folder + the uploaded check
# program (TEST copy: only LIVESRC's two digests and STEP4's three counts swapped for the made-up copies') + the block (XCHK filled).
# usage: mkhome_p4.sh <home> [plant]   (WSL only)
set -euo pipefail
T=/mnt/c/Users/JP/AppData/Local/Temp/claude/375bfdbef9aafd6e/cfce0c4f-7b18-4f6d-afde-d8ca6329f7ec/scratchpad/p4
H=$1; PL=${2:-none}
rm -rf "$H"; mkdir -p "$H/edition_upgrade_runs"
git clone -q ~/gate4/repo "$H/bible-db"
cd "$H/bible-db"
[ "$(git log -1 --format=%h)" = d34d6723 ] || { echo "clone is not d34d6723"; exit 1; }
export HOME="$H" PYTHONDONTWRITEBYTECODE=1
DG=$(python3 "$T/mkdbs_p4.py" "$H/bible-db" "$PL")
WD=$(awk '$1=="words"{print $3}' <<< "$DG"); VD=$(awk '$1=="verses"{print $3}' <<< "$DG")
WN=$(awk '$1=="words"{print $2}' <<< "$DG"); VN=$(awk '$1=="verses"{print $2}' <<< "$DG")
B=$H/bible-db/bible_edupg_test_built_20261102.db
R=$H/edition_upgrade_runs
if [ "$PL" = nosumv ] || [ "$PL" = sb ]; then
  # the guard folder must describe built AS MADE (the planted change is part of it), so prep after mkdbs
  :
fi
python3 scripts/eu_step.py pre --tag TESTPREP --ref d34d6723 --dir "$R/step4_headfix2_20261116" --db "$B" | tail -1
python3 scripts/eu_step.py prep --tag TESTPREP --built "$B" --dir "$R/step4_headfix2_20261116" --copy words,abp_corrections --save abp_corrections | tail -1
sed -e "s/\"words\": \[626309, \"1ce75b22[0-9a-f]*\"\]/\"words\": [$WN, \"$WD\"]/" \
    -e "s/\"verses\": \[31237, \"5717b045[0-9a-f]*\"\]/\"verses\": [$VN, \"$VD\"]/" \
    -e 's/STEP4 = {"strongs": 20, "strongs_base": 26, "is_pn": 12}/STEP4 = {"strongs": 2, "strongs_base": 3, "is_pn": 1}/' \
    "$T/p4_check.py" > "$R/p4_check_20261121.py"
diff "$T/p4_check.py" "$R/p4_check_20261121.py" | grep -c '^>' | sed 's/^/test-copy lines changed: /' || true
XC=$(sha256sum < "$R/p4_check_20261121.py" | cut -d' ' -f1)
XS=$(sha256sum < "$H/bible-db/bible_edupg_test_20261101.db" | cut -d' ' -f1)
sed -e "s/__XCHK__/$XC/" -e "s/^XS=[0-9a-f]*/XS=$XS/" -e "s/^XHOME_MAX=[0-9]*/XHOME_MAX=999999999/" "$T/block_p4.sh" > "$H/block.sh"
diff "$T/block_p4.sh" "$H/block.sh" | grep -c '^>' | sed 's/^/block lines changed: /' || true
echo "home ready: $H"
