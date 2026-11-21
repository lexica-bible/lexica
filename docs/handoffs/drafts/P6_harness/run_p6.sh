set -uo pipefail
T=/mnt/c/Users/JP/AppData/Local/Temp/claude/375bfdbef9aafd6e/cfce0c4f-7b18-4f6d-afde-d8ca6329f7ec/scratchpad/p6
G=~/gatep6; mkdir -p $G
hd() { echo; echo "=============== $* ==============="; }
mk() { bash "$T/mkhome_p6.sh" "$1" "${2:-none}" > "$1.mk" 2>&1 || { cat "$1.mk"; exit 1; }; }
run() { ( cd "$1" && HOME="$1" bash "$1/$2.sh" ) 2>&1 | grep -v '^$'; }
standin() { cp "$1/deploy_standin.sh" "$1/bible-db/scripts/deploy.sh"; }   # only after P6B / RB1 (it changes a tracked file)
sha() { sha256sum < "$1" | cut -c1-16; }
CASE=${1:-all}
echo "# P6 tests ($(date -u +%FT%TZ)); p6a $(sha $T/block_p6a.sh) p6r $(sha $T/block_p6r.sh) p6b $(sha $T/block_p6b.sh) p6c $(sha $T/block_p6c.sh) rb0 $(sha $T/block_rb0.sh) rb1 $(sha $T/block_rb1.sh) rb2 $(sha $T/block_rb2.sh) program $(sha $T/p6_check.py)"
hd "S1 the whole swap: P6A -> P6R -> P6B -> (stand-in deploy) P6C -> DONE; then the rollback RB0 -> RB1 -> RB2 -> DONE"
H=$G/s1; mk $H; tail -3 $H.mk
L0=$(sha $H/bible-db/bible.db); B0=$(sha $H/bible-db/bible_edupg_test_built_20261102.db)
run $H p6a; run $H p6r; run $H p6b; standin $H; run $H p6c
echo "after the swap: bible.db = built's bytes: $([ "$(sha $H/bible-db/bible.db)" = "$B0" ] && echo yes || echo NO); rollback file = old live's bytes: $([ "$(sha $H/bible-db/bible_pre_edition_upgrade_*.db)" = "$L0" ] && echo yes || echo NO)"
echo "leak grep (planted AI text / definitions / summaries in the three logs): $(cat $H/edition_upgrade_runs/p6*_*.log | grep -c SECRET)"
( cd $H/bible-db && git checkout -q scripts/deploy.sh && git branch -q --set-upstream-to=origin/reverttest main )
run $H rb0; run $H rb1; standin $H; run $H rb2
echo "after the rollback: bible.db = old live's bytes: $([ "$(sha $H/bible-db/bible.db)" = "$L0" ] && echo yes || echo NO); kept swapped-in file = built's bytes: $([ "$(sha $H/bible-db/bible_pre_edition_upgrade_backedout_*.db)" = "$B0" ] && echo yes || echo NO)"
[ "$CASE" = all ] || exit 0
hd "S2 live written during the hold (a writer touches bible.db) -> P6B STOP, nothing moved"
H=$G/s2; mk $H; run $H p6a | tail -1; run $H p6r | tail -1
( for i in 1 2 3 4 5 6 7 8 9 10; do sleep 3; touch $H/bible-db/bible.db; done ) & BG=$!
run $H p6b | grep -E "read [0-9]|RESULT|^exit="; wait $BG; echo "rollback files: $(ls $H/bible-db | grep -c bible_pre_)"
hd "S3 the swap commit pulled early (PA's scripts differ from d34d6723) -> P6R STOP, nothing moved"
H=$G/s3; mk $H; run $H p6a | tail -1; ( cd $H/bible-db && git pull -q ); run $H p6r | tail -2
hd "S4 live differs from src in books at the swap -> P6B STOP (outside the ruled four), nothing moved"
H=$G/s4; mk $H books; run $H p6a | tail -1; run $H p6r | tail -1; run $H p6b | grep -E "outside|STOP|RESULT|^exit="; echo "rollback files: $(ls $H/bible-db | grep -c bible_pre_)"
hd "S5 inside the 13:00-14:30 window (TEST copy: the window moved to bracket now) -> P6B STOP"
H=$G/s5; mk $H; run $H p6a | tail -1; run $H p6r | tail -1; NOW=$(date -u +%H%M); LO=$(printf %04d $((10#$NOW - 1))); HI=$(printf %04d $((10#$NOW + 1)))
sed -i "s/-ge 1300 \] \&\& \[ \"\$hm\" -le 1430/-ge $LO ] \&\& [ \"\$hm\" -le $HI/" $H/p6b.sh; run $H p6b | grep -E "UTC time|RESULT|^exit="
hd "S6 the renames cannot be made (~/bible-db made read-only) -> P6B STOP at the first rename, live in place"
H=$G/s6; mk $H; run $H p6a | tail -1; run $H p6r | tail -1; chmod a-w $H/bible-db; run $H p6b | tail -3; chmod u+w $H/bible-db; ls -l $H/bible-db/bible.db | cut -c1-40
hd "S7 a new fixture path already in PA's checkout -> P6A STOP"
H=$G/s7; mk $H; touch $H/bible-db/tests/fixtures/corrections/abp_corrections_active_built_20261121.txt; run $H p6a | tail -2
hd "S8 built not the pinned copy -> P6A STOP"
H=$G/s8; mk $H; sed -i 's/^XB=[0-9a-f]*/XB=0000/' $H/p6a.sh; run $H p6a | tail -2
hd "S9 P6C without P6B DONE -> STOP, deploy.sh NOT run"
H=$G/s9; mk $H; run $H p6c | tail -2
hd "S10 P6B without P6R -> STOP"
H=$G/s10; mk $H; run $H p6a | tail -1; run $H p6b | tail -2
hd "S11 RB0 with no finished swap -> STOP; RB1 without RB0 -> STOP"
H=$G/s11; mk $H; run $H rb0 | tail -2; run $H rb1 | tail -2
hd "S12 a rollback-named file already there -> P6R STOP"
H=$G/s12; mk $H; run $H p6a | tail -1; touch $H/bible-db/bible_pre_edition_upgrade_19990101.db; run $H p6r | tail -2
hd "S13 the revert pulled early before the rollback -> RB0 STOP (roll both or neither)"
H=$G/s13; mk $H; run $H p6a | tail -1; run $H p6r | tail -1; run $H p6b | tail -1; standin $H; run $H p6c | tail -1; ( cd $H/bible-db && git checkout -q scripts/deploy.sh && git branch -q --set-upstream-to=origin/reverttest main && git pull -q ); run $H rb0 | tail -2
hd "S14 the swap commit pulled between P6R and P6B -> P6B STOP, nothing moved"
H=$G/s14; mk $H; run $H p6a | tail -1; run $H p6r | tail -1; ( cd $H/bible-db && git pull -q ); run $H p6b | tail -2; echo "rollback files: $(ls $H/bible-db | grep -c bible_pre_); rollback.txt: $([ -e $H/edition_upgrade_runs/p6_swap/rollback.txt ] && echo present || echo absent)"
