# P9 tests (the first nightly after the swap - read-only). Made-up homes: ~/db_backups with a backup.log, last_success.txt,
# three bible.db copies + their .info files, and a git repo at ~/bible-db.   usage (WSL): bash run_p9.sh > tests_p9.out
# Every home's block copy has XNOT_BEFORE moved to 202601010000 (one line) so it runs before 11/22; B5 keeps the printed value.
set -uo pipefail
T=/mnt/c/Users/JP/projects/bible-db/docs/handoffs/drafts/P6_harness
G=~/gatep9; rm -rf $G; mkdir -p $G
hd() { echo; echo "=============== $* ==============="; }
info() {  # file when jm qc words verses surface
  printf 'db: bible.db\nwhen: %s\njournal_mode: %s\nquick_check: %s\nsize_bytes: 452063232\ncounts:\n  abp_corrections: 404\n  abp_surface: %s\n  verses: %s\n  words: %s\n' \
    "$2" "$3" "$4" "$7" "$6" "$5" > "$1"; }
runlog() {  # one backup run's lines; $1 = bible.db line, $2 = final line
  printf 'Backing up 3 db(s) -> /home/x/db_backups\n  free space 50.1 GB; live dbs total 0.50 GB\n\n%s\n  OK  notes.db: ok (delete), 4 tables, ~12 rows in largest, 0.1 MB\n  OK  study.db: ok (delete), 9 tables, ~300 rows in largest, 0.2 MB\n\n%s\n' "$1" "$2"; }
OKB='  OK  bible.db: ok (delete), 150 tables, ~790,000 rows in largest, 452.1 MB'
mk() {  # clean home: copies 11/20 (gz), 11/21 (gz) = old live; 11/22 (raw) = new live
  H=$1; mkdir -p $H/db_backups $H/bible-db
  git -C $H/bible-db init -q && git -C $H/bible-db -c user.email=t@t -c user.name=t commit -q --allow-empty -m x
  B=$H/db_backups
  : > $B/bible.db.20261120-133004.db.gz; info $B/bible.db.20261120-133004.info "2026-11-20 13:30:04" delete ok 626309 31237 395003
  : > $B/bible.db.20261121-133002.db.gz; info $B/bible.db.20261121-133002.info "2026-11-21 13:30:02" delete ok 626309 31237 395003
  : > $B/bible.db.20261122-133003.db;    info $B/bible.db.20261122-133003.info "2026-11-22 13:30:03" delete ok 626309 31237 395014
  : > $B/notes.db.20261122-133003.db; : > $B/notes.db.20261122-133003.info
  { runlog "$OKB" "All backups verified ok."; runlog "$OKB" "All backups verified ok."; } > $B/backup.log
  echo "2026-11-22T13:41:17" > $B/last_success.txt
  sed 's/^XNOT_BEFORE=202611221500 /XNOT_BEFORE=202601010000 /' $T/block_p9.sh > $H/p9.sh
}
run() { ( cd $1 && HOME=$1 bash $1/p9.sh ) 2>&1; }
snap() { (cd $1 && find . -path ./bible-db/.git -prune -o -type f -printf '%p %s %T@\n' | sort | sha256sum | cut -c1-16); }
echo "# P9 tests ($(date -u +%FT%TZ)); block $(sha256sum < $T/block_p9.sh | cut -c1-16); the only line changed in each test copy:"
diff <(cat $T/block_p9.sh) <(sed 's/^XNOT_BEFORE=202611221500 /XNOT_BEFORE=202601010000 /' $T/block_p9.sh)

hd "A1 clean -> PASS (whole output); nothing in the home changed"
H=$G/a1; mk $H; S0=$(snap $H); run $H; echo "home unchanged by the block: $([ "$(snap $H)" = "$S0" ] && echo yes || echo NO)"

hd "A2 an XX line in an OLDER run only (the last run clean) -> PASS (only the last run is read)"
H=$G/a2; mk $H; { runlog "  XX  bible.db: backup FAILED (disk I/O error) - last good copy kept." "!!  1 db(s) failed to back up cleanly - see above. Exit 1."; cat $H/db_backups/backup.log; } > $H/x; mv $H/x $H/db_backups/backup.log
run $H | grep -E "XX lines|final line|RESULT"

hd "B1 an XX line in the last run (another db) -> CHECK"
H=$G/b1; mk $H; sed -i '$d' $H/db_backups/backup.log; printf '  XX  news.db: quick_check = %s - copy discarded, last good kept.\n\n!!  1 db(s) failed to back up cleanly - see above. Exit 1.\n' "'bad'" >> $H/db_backups/backup.log
run $H | grep -E "NO|RESULT"

hd "B2 the 11/22 run did not finish clean: stamp still 11/21, the log's last run ends without 'All backups verified ok.' -> CHECK"
H=$G/b2; mk $H; echo "2026-11-21T13:40:55" > $H/db_backups/last_success.txt; sed -i '$d' $H/db_backups/backup.log; sed -i '$d' $H/db_backups/backup.log
run $H | grep -E "NO|RESULT"

hd "B3 the newest copy reads the OLD abp_surface (the nightly copied the old file) -> CHECK"
H=$G/b3; mk $H; info $H/db_backups/bible.db.20261122-133003.info "2026-11-22 13:30:03" delete ok 626309 31237 395003
run $H | grep -E "NO|RESULT"

hd "B4 no 11/22 copy (the nightly did not run): newest = 11/21, gz -> CHECK"
H=$G/b4; mk $H; rm $H/db_backups/bible.db.20261122-133003.*; echo "2026-11-21T13:40:55" > $H/db_backups/last_success.txt
run $H | grep -E "NO|RESULT"

hd "B5 before 15:00 UTC 11/22 (the printed block, unchanged) -> STOP, nothing read"
H=$G/b5; mk $H; cp $T/block_p9.sh $H/p9.sh; run $H

hd "B6 the copy's check file: quick_check not ok and live in wal mode -> CHECK"
H=$G/b6; mk $H; info $H/db_backups/bible.db.20261122-133003.info "2026-11-22 13:30:03" wal "*** in database main ***" 626309 31237 395014
run $H | grep -E "NO|RESULT"

hd "B7 the control cannot tell the two apart (the copy before also reads 395014) -> CHECK"
H=$G/b7; mk $H; info $H/db_backups/bible.db.20261121-133002.info "2026-11-21 13:30:02" delete ok 626309 31237 395014
run $H | grep -E "NO|RESULT"

hd "B8 four bible.db copies kept (rotation did not trim) -> CHECK"
H=$G/b8; mk $H; : > $H/db_backups/bible.db.20261119-133001.db.gz
run $H | grep -E "NO|RESULT"

hd "B9 words / verses counts off -> CHECK"
H=$G/b9; mk $H; info $H/db_backups/bible.db.20261122-133003.info "2026-11-22 13:30:03" delete ok 626308 31236 395014
run $H | grep -E "NO|RESULT"

hd "B10 the bible.db line missing from the last run -> CHECK"
H=$G/b10; mk $H; sed -i '/OK  bible.db/d' $H/db_backups/backup.log
run $H | grep -E "NO|RESULT"

hd "B11 newest copy only gzipped (no raw) -> CHECK"
H=$G/b11; mk $H; mv $H/db_backups/bible.db.20261122-133003.db $H/db_backups/bible.db.20261122-133003.db.gz
run $H | grep -E "NO|RESULT"
