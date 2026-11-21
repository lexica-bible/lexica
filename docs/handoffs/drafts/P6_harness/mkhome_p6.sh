# P6 tests: a test home = a clone at d34d6723 with a local "origin" that also carries a fake swap commit (the cleared patch applied
# on d34d6723) and its revert; the made-up copies (mkdbs_p6.py = P4's maker); the HEADFIX2 guard folder; the TEST copy of the program
# (LIVESRC's two digests swapped for the made-up copies'); the blocks with XP filled (XS / XB swapped for the made-up copies').
# usage: mkhome_p6.sh <home> [plant]   (WSL only)
set -euo pipefail
T=/mnt/c/Users/JP/projects/bible-db/docs/handoffs/drafts/P6_harness
PATCH=/mnt/c/Users/JP/projects/bible-db/docs/handoffs/drafts/SWAP_COMMIT/swap_commit_full.patch
H=$1; PL=${2:-none}
rm -rf "$H"; mkdir -p "$H/edition_upgrade_runs"
git clone -q --bare ~/gate4/repo "$H/origin.git"
git clone -q "$H/origin.git" "$H/work"
( cd "$H/work" && git checkout -q d34d6723 && git switch -q -c master-test && git apply "$PATCH" && git add -A \
  && git -c user.email=t@t -c user.name=t commit -q -m "edition upgrade: THE SWAP COMMIT - test copy" \
  && git push -q origin master-test:refs/heads/swaptest \
  && git -c user.email=t@t -c user.name=t revert --no-edit HEAD >/dev/null && git push -q origin master-test:refs/heads/reverttest )
git clone -q "$H/origin.git" "$H/bible-db"
( cd "$H/bible-db" && git checkout -q -B main d34d6723 && git branch -q --set-upstream-to=origin/swaptest main )
cd "$H/bible-db"
export HOME="$H" PYTHONDONTWRITEBYTECODE=1
DG=$(python3 "$T/mkdbs_p6.py" "$H/bible-db" "$PL")
WD=$(awk '$1=="words"{print $3}' <<< "$DG"); VD=$(awk '$1=="verses"{print $3}' <<< "$DG")
WN=$(awk '$1=="words"{print $2}' <<< "$DG"); VN=$(awk '$1=="verses"{print $2}' <<< "$DG")
B=$H/bible-db/bible_edupg_test_built_20261102.db; R=$H/edition_upgrade_runs
python3 scripts/eu_step.py pre --tag TESTPREP --ref d34d6723 --dir "$R/step4_headfix2_20261116" --db "$B" | tail -1
python3 scripts/eu_step.py prep --tag TESTPREP --built "$B" --dir "$R/step4_headfix2_20261116" --copy words,abp_corrections --save abp_corrections | tail -1
sed -e "s/\"words\": \[626309, \"1ce75b22[0-9a-f]*\"\]/\"words\": [$WN, \"$WD\"]/" \
    -e "s/\"verses\": \[31237, \"5717b045[0-9a-f]*\"\]/\"verses\": [$VN, \"$VD\"]/" "$T/p6_check.py" > "$R/p6_check_20261121.py"
XP=$(sha256sum < "$R/p6_check_20261121.py" | cut -d' ' -f1)
XS=$(sha256sum < "$H/bible-db/bible_edupg_test_20261101.db" | cut -d' ' -f1); XB=$(sha256sum < "$B" | cut -d' ' -f1)
for b in p6a p6r p6b p6c rb0 rb1 rb2; do
  sed -e "s/__XP__/$XP/" -e "s/^XS=[0-9a-f]*/XS=$XS/" -e "s/^XB=[0-9a-f]*/XB=$XB/" "$T/block_$b.sh" > "$H/$b.sh"
done
cp "$T/deploy_standin.sh" "$H/deploy_standin.sh"
echo "home ready: $H"
