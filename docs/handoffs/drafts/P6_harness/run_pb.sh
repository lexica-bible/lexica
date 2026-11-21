# PB tests (the file-only put-back, DESIGN 9.229 (1)). Same test homes as run_p6.sh (mkhome_p6.sh); block_pb.sh is copied into each
# home with XB swapped for the made-up built copy's sha (taken from the home's p6b.sh). WSL only.
set -uo pipefail
T=/mnt/c/Users/JP/projects/bible-db/docs/handoffs/drafts/P6_harness
G=~/gatepb; mkdir -p $G
hd() { echo; echo "=============== $* ==============="; }
sha() { [ -e "$1" ] && { sha256sum < "$1" | cut -c1-16; } || echo ABSENT; }
full() { sha256sum < "$1" | cut -d' ' -f1; }
run() { ( cd "$1" && HOME="$1" bash "$1/$2.sh" ) 2>&1 | grep -v '^$'; }
standin() { cp "$1/deploy_standin.sh" "$1/bible-db/scripts/deploy.sh"; }
mk() { bash "$T/mkhome_p6.sh" "$1" "${2:-none}" > "$1.mk" 2>&1 || { cat "$1.mk"; exit 1; }
       cp "$T/block_pb0.sh" "$1/pb0.sh"
       XBT=$(grep -m1 '^XB=' "$1/p6b.sh" | cut -d= -f2 | cut -d' ' -f1); sed "s/^XB=[0-9a-f]*/XB=$XBT/" "$T/block_pb.sh" > "$1/pb.sh"
       L0=$(sha "$1/bible-db/bible.db"); B0=$(sha "$1/bible-db/bible_edupg_test_built_20261102.db"); }
ready() { run "$1" p6a | tail -1; run "$1" p6r | tail -1; }
RBN() { echo "$1/bible-db/bible_pre_edition_upgrade_$(date -u +%Y%m%d).db"; }
KEEP() { echo "$1/bible-db/bible_pre_edition_upgrade_putback_$(date -u +%Y%m%d).db"; }
# state (a), the plain case: P6B's two renames land, then its after-check ends CHECK (the test copy of P6B is given a wrong built pin)
a1() { mk "$1"; ready "$1" > /dev/null; sed -i 's/^XB=[0-9a-f]*/XB=0000/' "$1/p6b.sh"; run "$1" p6b | tail -2 | head -1; }
facts() { echo "FACTS: bible.db $(sha "$1/bible-db/bible.db") (old live $L0, built $B0); rollback file $(sha "$(RBN "$1")"); kept file $(sha "$(KEEP "$1")"); built path $(sha "$1/bible-db/bible_edupg_test_built_20261102.db"); bible_pre_* files: $(ls "$1/bible-db" | grep -c '^bible_pre_')"; }
echo "# PB tests ($(date -u +%FT%TZ)); block_pb.sh $(full $T/block_pb.sh)"

hd "T1 state (a): P6B ends CHECK after the renames -> PB DONE (old live back, built kept under the putback name); a second paste -> STOP"
H=$G/t1; a1 $H; facts $H; run $H pb; facts $H
echo "old live back: $([ "$(sha $H/bible-db/bible.db)" = "$L0" ] && echo yes || echo NO); kept = built's bytes: $([ "$(sha "$(KEEP $H)")" = "$B0" ] && echo yes || echo NO)"
run $H pb | tail -2

hd "T2 state (a): 'NOT IN PLACE' (first rename made, no bible.db; hand-made) -> PB DONE with one rename, nothing to keep"
H=$G/t2; mk $H; ready $H; printf '%s\n%s\n' "$(RBN $H)" "$(full $H/bible-db/bible.db)" > $H/edition_upgrade_runs/p6_swap/rollback.txt
mv $H/bible-db/bible.db "$(RBN $H)"; echo "P6B RESULT: STOP - the first rename did not land cleanly (mv exit 1); live is NOT IN PLACE - TO THE RULING CHAT NOW" > $H/edition_upgrade_runs/p6b_swap_window.log
facts $H; run $H pb; facts $H; echo "old live back: $([ "$(sha $H/bible-db/bible.db)" = "$L0" ] && echo yes || echo NO)"

hd "T3 state (a): 'NOT the pre-swap file' (a partial file at bible.db, built still at its path; hand-made) -> PB DONE, the partial file kept"
H=$G/t3; mk $H; ready $H; printf '%s\n%s\n' "$(RBN $H)" "$(full $H/bible-db/bible.db)" > $H/edition_upgrade_runs/p6_swap/rollback.txt
mv $H/bible-db/bible.db "$(RBN $H)"; head -c 4096 $H/bible-db/bible_edupg_test_built_20261102.db > $H/bible-db/bible.db; J0=$(sha $H/bible-db/bible.db)
echo "P6B RESULT: STOP - the second rename did not land cleanly (mv exit 1); the first was put back: live is NOT the pre-swap file - TO THE RULING CHAT NOW" > $H/edition_upgrade_runs/p6b_swap_window.log
facts $H; run $H pb; facts $H; echo "old live back: $([ "$(sha $H/bible-db/bible.db)" = "$L0" ] && echo yes || echo NO); kept = the partial file: $([ "$(sha "$(KEEP $H)")" = "$J0" ] && echo yes || echo NO)"

hd "T4 state (a): P6B cut off after the renames, no result line in its log -> PB DONE"
H=$G/t4; mk $H; ready $H; run $H p6b | tail -1; sed -i '/^P6B RESULT/d' $H/edition_upgrade_runs/p6b_swap_window.log
run $H pb | grep -E "result line|on disk|RESULT|^exit="; facts $H; echo "old live back: $([ "$(sha $H/bible-db/bible.db)" = "$L0" ] && echo yes || echo NO)"

hd "T5 state (b): P6B DONE, P6C's deploy fails at the pull (origin unreachable), the site has written to the new bible.db -> PB DONE; then the revert deploys clean"
H=$G/t5; mk $H; ready $H; run $H p6b | tail -1
( cd $H/bible-db && git remote set-url origin /nonexistent/origin.git ); run $H p6c | tail -4
python3 -c 'import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute("create table putback_site_write(x)"); c.execute("insert into putback_site_write values (1)"); c.commit(); c.close()' $H/bible-db/bible.db
W0=$(sha $H/bible-db/bible.db); facts $H; run $H pb; facts $H
echo "old live back: $([ "$(sha $H/bible-db/bible.db)" = "$L0" ] && echo yes || echo NO); kept = the site-written file: $([ "$(sha "$(KEEP $H)")" = "$W0" ] && echo yes || echo NO); kept differs from built: $([ "$W0" = "$B0" ] && echo NO || echo yes)"
( cd $H/bible-db && git remote set-url origin $H/origin.git && git branch -q --set-upstream-to=origin/reverttest main ); standin $H
( cd $H && HOME=$H bash $H/bible-db/scripts/deploy.sh ) 2>&1 | tail -2; ( cd $H/bible-db && git checkout -q scripts/deploy.sh; echo "after CC's revert is deployed: HEAD '$(git log -1 --format=%s | cut -c1-48)'; scripts/tests = d34d6723: $(git diff --quiet d34d6723 HEAD -- scripts tests && echo yes || echo NO); cert pin 374: $(grep -c '"abp_corrections_active": 374,' scripts/cert_invariants.py)" )

hd "T6 PA is ON the swap commit (the swap and P6C went through) -> PB STOP, nothing moved"
H=$G/t6; mk $H; ready $H; run $H p6b | tail -1; standin $H; run $H p6c | tail -1; ( cd $H/bible-db && git checkout -q scripts/deploy.sh )
run $H pb | tail -2; facts $H

hd "T7 P6B never ran -> STOP; P6B stopped before its first rename (no rollback.txt) -> STOP"
H=$G/t7; mk $H; run $H pb | tail -2; rm -f $H/edition_upgrade_runs/pb_putback_window.log
run $H p6a | tail -1; run $H p6b | tail -1; run $H pb | tail -2; facts $H

hd "T8 bible.db written during the hold -> STOP, nothing moved"
H=$G/t8; a1 $H; ( for i in 1 2 3 4 5 6 7 8 9 10; do sleep 3; touch $H/bible-db/bible.db; done ) & BG=$!
run $H pb | grep -E "read [0-9]|RESULT|^exit="; wait $BG; facts $H

hd "T9 a -journal file beside bible.db -> STOP, nothing moved"
H=$G/t9; a1 $H; touch $H/bible-db/bible.db-journal; run $H pb | grep -E "read 1 |RESULT|^exit="; facts $H

hd "T10 the rollback file is not the pre-swap bytes -> STOP before the hold, nothing moved"
H=$G/t10; a1 $H; echo x >> "$(RBN $H)"; run $H pb | tail -3; echo "kept files: $(ls $H/bible-db | grep -c putback)"

hd "T11 the renames cannot be made (~/bible-db read-only) -> STOP at the first rename, bible.db in place"
H=$G/t11; a1 $H; chmod a-w $H/bible-db; run $H pb | tail -3; chmod u+w $H/bible-db; facts $H

hd "T12 the keep name already exists -> STOP"
H=$G/t12; a1 $H; touch "$(KEEP $H)"; run $H pb | tail -2

hd "T13 inside the 13:00-14:30 window (TEST copy: the window moved to bracket now) -> STOP"
H=$G/t13; a1 $H; NOW=$(date -u +%H%M); LO=$(printf %04d $((10#$NOW - 1))); HI=$(printf %04d $((10#$NOW + 1)))
sed -i "s/-ge 1300 \] \&\& \[ \"\$hm\" -le 1430/-ge $LO ] \&\& [ \"\$hm\" -le $HI/" $H/pb.sh; run $H pb | grep -E "UTC time|RESULT|^exit="; facts $H

hd "T14 P6B's first rename missed with live in place (rollback.txt written, no rollback file; hand-made) -> STOP: already the pre-swap file"
H=$G/t14; mk $H; ready $H; printf '%s\n%s\n' "$(RBN $H)" "$(full $H/bible-db/bible.db)" > $H/edition_upgrade_runs/p6_swap/rollback.txt
echo "P6B RESULT: STOP - the first rename did not land cleanly (mv exit 1); live is in place" > $H/edition_upgrade_runs/p6b_swap_window.log; run $H pb | tail -3; facts $H

hd "T15 the revert pulled early after a finished swap (the state RB0 refuses, S13) -> PB DONE: the file follows the code back"
H=$G/t15; mk $H; ready $H; run $H p6b | tail -1; standin $H; run $H p6c | tail -1
( cd $H/bible-db && git checkout -q scripts/deploy.sh && git branch -q --set-upstream-to=origin/reverttest main && git pull -q ); run $H rb0 | tail -2
run $H pb | grep -E "result line|HEAD subject|NOT on|RESULT|^exit="; facts $H; echo "old live back: $([ "$(sha $H/bible-db/bible.db)" = "$L0" ] && echo yes || echo NO)"

hd "T16 PB's own second rename misses (TEST copy: that mv replaced by 'false') -> STOP, the first put back"
H=$G/t16; a1 $H; sed -i 's/^mv -n "\$RB" "\$LIVE"; m2=\$?/false; m2=$?/' $H/pb.sh; grep -c '^false; m2' $H/pb.sh; run $H pb | tail -3; facts $H

hd "T17 neither file there -> STOP NOT IN PLACE; an empty file at the rollback name -> STOP"
H=$G/t17; a1 $H; rm $H/bible-db/bible.db "$(RBN $H)"; run $H pb | tail -2; rm -f $H/edition_upgrade_runs/pb_putback_window.log
: > "$(RBN $H)"; run $H pb | tail -2

hd "T18 a bad rollback.txt (line 1 outside ~/bible-db; line 2 not a sha) -> STOP each time"
H=$G/t18; a1 $H; cp $H/edition_upgrade_runs/p6_swap/rollback.txt $H/rb.keep
printf '%s\n%s\n' "/tmp/elsewhere.db" "$(sed -n 2p $H/rb.keep)" > $H/edition_upgrade_runs/p6_swap/rollback.txt; run $H pb | tail -2; rm -f $H/edition_upgrade_runs/pb_putback_window.log
printf '%s\n%s\n' "$(sed -n 1p $H/rb.keep)" "notasha" > $H/edition_upgrade_runs/p6_swap/rollback.txt; run $H pb | tail -2; facts $H

hd "T19 (reviewer D1) 'NOT IN PLACE', then a task has made an EMPTY bible.db -> PB DONE: the empty file kept, old live back"
H=$G/t19; mk $H; ready $H > /dev/null; printf '%s\n%s\n' "$(RBN $H)" "$(full $H/bible-db/bible.db)" > $H/edition_upgrade_runs/p6_swap/rollback.txt
mv $H/bible-db/bible.db "$(RBN $H)"; : > $H/bible-db/bible.db; echo "P6B RESULT: STOP - the first rename did not land cleanly (mv exit 1); live is NOT IN PLACE - TO THE RULING CHAT NOW" > $H/edition_upgrade_runs/p6b_swap_window.log
run $H pb | grep -E "on disk|what sits|^1\.|^2\.|sha256 =|RESULT|^exit="; facts $H; echo "old live back: $([ "$(sha $H/bible-db/bible.db)" = "$L0" ] && echo yes || echo NO); kept file is empty: $([ -e "$(KEEP $H)" ] && [ ! -s "$(KEEP $H)" ] && echo yes || echo NO)"

hd "T20 (reviewer D2) a later commit sits on top of the swap commit and P6C pulled both (HEAD subject is NOT the swap commit) -> PB STOP, nothing moved"
H=$G/t20; mk $H; ( cd $H/work && git checkout -q -b plus HEAD~1 && git -c user.email=t@t -c user.name=t commit -q --allow-empty -m "docs only - test" && git push -q origin plus:refs/heads/swapplus )
( cd $H/bible-db && git fetch -q && git branch -q --set-upstream-to=origin/swapplus main ); ready $H; run $H p6b | tail -1; standin $H; run $H p6c | tail -2; ( cd $H/bible-db && git checkout -q scripts/deploy.sh )
run $H pb | grep -E "HEAD subject|RESULT|^exit="; facts $H

hd "T21 a -journal file beside the rollback file -> STOP, nothing moved"
H=$G/t21; a1 $H; touch "$(RBN $H)-journal"; run $H pb | tail -2; facts $H

hd "T22 no rollback file and bible.db is not the pre-swap file -> STOP, nothing moved"
H=$G/t22; a1 $H; rm "$(RBN $H)"; run $H pb | tail -2; facts $H

hd "T23 (reviewer N1 / F16) PB0 before the swap -> DONE; an uncommitted edit to ai.py on PA -> PB0 STOP before the swap; the same edit made after the swap -> PB STOP, nothing moved"
H=$G/t23; mk $H; run $H pb0 | tail -3; rm -f $H/edition_upgrade_runs/pb0_putback_ready.log; echo "# test edit" >> $H/bible-db/ai.py; run $H pb0 | tail -4
( cd $H/bible-db && git checkout -q ai.py ); a1x() { ready "$1" > /dev/null; sed -i 's/^XB=[0-9a-f]*/XB=0000/' "$1/p6b.sh"; run "$1" p6b | tail -2 | head -1; }; a1x $H
echo "# test edit" >> $H/bible-db/ai.py; run $H pb | grep -E "against the pre-swap|RESULT|^exit="; facts $H
