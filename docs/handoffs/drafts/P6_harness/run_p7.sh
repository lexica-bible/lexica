# P7 tests (the read-only check after the swap). Test homes: mkhome_p7.sh (the state P6C DONE leaves, made by hand; the made-up
# pair gives exactly the real expected G5 figures) - and one home made by the real P6 blocks (mkhome_p6.sh), case A3.
# cert_invariants / health_check are the stand-in p7_standin.py (the made-up files lack the tables the real two read); H5 runs the
# REAL health_check.py to show the block's floor-line text is the real one.   usage (WSL): bash run_p7.sh > tests_p7.out
set -uo pipefail
T=/mnt/c/Users/JP/projects/bible-db/docs/handoffs/drafts/P6_harness
G=~/gatep7; mkdir -p $G
hd() { echo; echo "=============== $* ==============="; }
mk() { bash "$T/mkhome_p7.sh" "$1" "${2:-none}" "${3:-2}" > "$1.mk" 2>&1 || { cat "$1.mk"; exit 1; }; }
run() { ( cd "$1" && HOME="$1" bash "$1/${2:-p7}.sh" ) 2>&1 | grep -v '^$'; }
sha() { sha256sum < "$1" | cut -c1-16; }
keep() { grep -E "RESULT|^exit=|NOT AS EXPECTED|FINDING|: NO|STOP|CHECK:|--- run|locked|waiting"; }
echo "# P7 tests ($(date -u +%FT%TZ)); block $(sha $T/block_p7.sh) program $(sha $T/p7_check.py)"

hd "A1 clean -> DONE (the whole log shown); a second paste -> STOP; nothing leaked; both files' bytes unchanged"
H=$G/a1; mk $H; tail -1 $H.mk
L0=$(sha $H/bible-db/bible.db); R0=$(sha $H/bible-db/bible_pre_edition_upgrade_20261122.db)
run $H
run $H | tail -2
echo "leak grep (planted verse / word text in the log and the run folder): $(cat $H/edition_upgrade_runs/p7_after_swap_*.log $H/edition_upgrade_runs/p7_after_swap/*.out | grep -c SECRET)"
echo "bible.db bytes unchanged: $([ "$(sha $H/bible-db/bible.db)" = "$L0" ] && echo yes || echo NO); rollback file bytes unchanged: $([ "$(sha $H/bible-db/bible_pre_edition_upgrade_20261122.db)" = "$R0" ] && echo yes || echo NO); files in ~/bible-db beside the two: $(ls $H/bible-db | grep -c -e '-journal' -e '-wal' -e '-shm')"
echo "git status of the checkout (tracked files): $(cd $H/bible-db && git status --porcelain --untracked-files=no | wc -l) changed"

hd "A2 the 60 s wait as printed in the block (WAIT=60) -> waits, then DONE"
H=$G/a2; mk $H none 60; t0=$(date +%s); run $H | keep; echo "took $(( $(date +%s) - t0 )) s"

hd "A3 a home made by the REAL P6A -> P6R -> P6B -> P6C; then P7 with the REAL program (no line changed): the guards pass on P6's own log and rollback.txt; the made-up files are not the real figures -> FINDINGS"
H=$G/a3; bash "$T/mkhome_p6.sh" $H > $H.mk 2>&1 || { cat $H.mk; exit 1; }
for b in p6a p6r p6b; do run $H $b | tail -1; done
cp $H/deploy_standin.sh $H/bible-db/scripts/deploy.sh; run $H p6c | tail -1; ( cd $H/bible-db && git checkout -q scripts/deploy.sh )
mkdir -p $H/standin; cp $T/p7_standin.py $H/standin/cert.py; cp $T/p7_standin.py $H/standin/health.py; cp $T/p7_check.py $H/edition_upgrade_runs/p7_check_20261121.py
sed -e "s/__XP7__/$(sha256sum < $T/p7_check.py | cut -d' ' -f1)/" -e "s|^CERT=.*|CERT=$H/standin/cert.py|" -e "s|^HC=.*|HC=$H/standin/health.py|" -e "s/^WAIT=60 /WAIT=2 /" $T/block_p7.sh > $H/p7.sh
run $H | grep -E "PA's code|content differs|rollback file|uploaded check|check.py sha|rows changed|RESULT|^exit=|P7 CHECK"

for p in xrefkey count slot wordsdig notable verseid; do
  hd "F-$p planted in the made-up pair -> FINDINGS"
  H=$G/f_$p; mk $H $p; run $H | keep
done

hd "C1 cert check 4 red -> FINDINGS";             H=$G/c1; mk $H; echo fail4 > $H/standin/cert.mode; run $H | keep
hd "C2 cert green but a second spent row noted -> FINDINGS"; H=$G/c2; mk $H; echo spent2 > $H/standin/cert.mode; run $H | keep
hd "H1 health: the floor short by 3,873 -> FINDINGS"; H=$G/h1; mk $H; echo floor > $H/standin/health.mode; run $H | keep
hd "H2 health: one other warning -> FINDINGS";    H=$G/h2; mk $H; echo warn > $H/standin/health.mode; run $H | keep
hd "H3 health: 'database is locked' on the first read only -> read again after 30 s -> DONE"; H=$G/h3; mk $H; echo locked1 > $H/standin/health.mode; run $H | keep
hd "H4 health: 'database is locked' on all three reads -> FINDINGS"; H=$G/h4; mk $H; echo locked > $H/standin/health.mode; run $H | keep
hd "H5 the REAL health_check.py (the swap commit's) on a made-up file with 395,014 abp_surface rows: the block's two grep texts against the real output"
H=$G/h5; mk $H; python3 - $H/h5.db <<'PY'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1]); c.execute("CREATE TABLE abp_surface (a)")
c.executemany("INSERT INTO abp_surface VALUES (?)", ((i,) for i in range(395014))); c.commit(); c.close()
PY
( cd $H/bible-db && PYTHONDONTWRITEBYTECODE=1 python3 scripts/health_check.py $H/h5.db --no-backup-check --no-disk-check > $H/h5.out 2>&1 )
echo "real floor line: $(grep -F 'abp_surface rows BELOW' $H/h5.out | cut -c1-120)"
echo "block's floor text matches it: $(grep -cF '[OK  ] abp_surface rows BELOW floor 395014  [fill or a backfill missing?]: 0 ' $H/h5.out) (expect 1)"
echo "real tally line: '$(grep -E 'warning\(s\)' $H/h5.out)' - the block's form '  N warning(s), M error(s).': $(grep -cE '^  [0-9]+ warning\(s\), [0-9]+ error\(s\)\.$' $H/h5.out) (expect 1)"

hd "C3 cert: 'database is locked' on the first read only -> read again after 30 s -> DONE"; H=$G/c3; mk $H; echo locked1 > $H/standin/cert.mode; run $H | keep
hd "K1 a Python cache folder appears in the checkout during the run -> CHECK"
H=$G/k1; mk $H; echo pyc > $H/standin/cert.mode; run $H | keep

hd "S1 P6C's log without a DONE line -> STOP";    H=$G/s1; mk $H; echo "P6C RESULT: CHECK - lines above" > $H/edition_upgrade_runs/p6c_swap_deploy.log; run $H | tail -2
hd "S2 no P6C log -> STOP";                       H=$G/s2; mk $H; rm $H/edition_upgrade_runs/p6c_swap_deploy.log; run $H | tail -2
hd "S3 PA not on the swap commit (HEAD = d34d6723) -> STOP"; H=$G/s3; mk $H; ( cd $H/bible-db && git checkout -q -B main d34d6723 ); run $H | tail -4
hd "S4 a commit on top of the swap commit pulled -> STOP"; H=$G/s4; mk $H; ( cd $H/bible-db && git checkout -q -B main origin/ontop ); run $H | tail -3
hd "S5 an uncommitted edit in ai.py -> STOP";     H=$G/s5; mk $H; echo "# x" >> $H/bible-db/ai.py; run $H | tail -4
hd "S6 the rollback file missing -> STOP";        H=$G/s6; mk $H; rm $H/bible-db/bible_pre_edition_upgrade_20261122.db; run $H | tail -2
hd "S7 the rollback file not the pre-swap bytes -> STOP"; H=$G/s7; mk $H; printf x >> $H/bible-db/bible_pre_edition_upgrade_20261122.db; run $H | tail -3
hd "S8 a -journal beside the rollback file -> STOP"; H=$G/s8; mk $H; touch $H/bible-db/bible_pre_edition_upgrade_20261122.db-journal; run $H | tail -2
hd "S9 the uploaded program not the pinned file -> STOP"; H=$G/s9; mk $H; echo "# x" >> $H/edition_upgrade_runs/p7_check_20261121.py; run $H | tail -3
hd "S10 the uploaded program missing -> STOP";    H=$G/s10; mk $H; rm $H/edition_upgrade_runs/p7_check_20261121.py; run $H | tail -2
hd "S11 rollback.txt names a file elsewhere / line 2 not a sha -> STOP"
H=$G/s11; mk $H; printf '/tmp/elsewhere.db\n%064d\n' 0 > $H/edition_upgrade_runs/p6_swap/rollback.txt; run $H | tail -2
H=$G/s11b; mk $H; printf '%s\nnotasha\n' "$H/bible-db/bible_pre_edition_upgrade_20261122.db" > $H/edition_upgrade_runs/p6_swap/rollback.txt; run $H | tail -2
hd "S12 bible.db missing -> STOP";                H=$G/s12; mk $H; rm $H/bible-db/bible.db; run $H | tail -2
hd "S14 the run folder already there (a later-day second paste) -> STOP, nothing overwritten"; H=$G/s14; mk $H; mkdir -p $H/edition_upgrade_runs/p7_after_swap; echo keepme > $H/edition_upgrade_runs/p7_after_swap/cert_1.out; run $H | tail -2; cat $H/edition_upgrade_runs/p7_after_swap/cert_1.out
hd "S15 the seven names right but one file's content not the cleared bytes (a commit titled as the swap commit) -> STOP"
H=$G/s15; mk $H; ( cd $H/bible-db && git reset -q --soft HEAD~1 && echo "# x" >> scripts/health_check.py && git -c user.email=t@t -c user.name=t commit -q -am "edition upgrade: THE SWAP COMMIT - other content" ); run $H | tail -5
hd "S13 the swap commit's file list is not the seven (a test file changed in a commit titled as the swap commit) -> STOP"
H=$G/s13; mk $H; ( cd $H/bible-db && echo "# x" >> tests/test_strongs_join.py && git -c user.email=t@t -c user.name=t commit -q -am "edition upgrade: THE SWAP COMMIT - with one more file" ); run $H | tail -4
