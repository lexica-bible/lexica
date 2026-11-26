set +H
( set -uo pipefail
export TZ=UTC LC_ALL=C GIT_OPTIONAL_LOCKS=0
B=~/db_backups
XAFTER=20261122-133027                          # the 11/22 nightly's stamp (P9, DESIGN 9.244): count runs after it
XDAYS="20261123 20261124 20261125"              # the 13:30 UTC nightlies since; 11/23 + 11/24 are the two to rule on
XW=626309; XV=31237; XS=395014                  # live at each of those three nightlies (the form cells came 11/26 02:40Z)
echo "NIGHTLIES - the 11/23 and 11/24 nightlies (DESIGN 9.274 (3)) - READ-ONLY: reads files in ~/db_backups and git's HEAD; opens no database; runs no backup and no health check; writes no file"
echo "now UTC: $(date -u +%FT%TZ); PA HEAD: $(git -C ~/bible-db rev-parse --short=8 HEAD 2>&1)"
[ "$(date -u +%Y%m%d%H%M)" -lt 202611261300 ] || { echo "NIGHTLIES RESULT: STOP - the 11/26 nightly is due or done; this block's figures are for the 11/23-11/25 runs only (nothing read; it comes back re-drafted)"; exit 1; }
[ "$(date -u +%Y%m%d%H%M)" -ge 202611251500 ] || { echo "NIGHTLIES RESULT: STOP - before the 11/25 nightly finished (nothing read)"; exit 1; }
bad=0
ok() { if [ "$2" = "$3" ]; then echo "$1: $2 - yes"; else echo "$1: $2 - NO (expected $3)"; bad=1; fi; }
cnt() { grep -E "^  $2: " "$1" | sed -E 's/^.*: //'; }
echo "--- 1. every backup run since the 11/22 nightly, from the check files' stamps (small dbs keep 7, so none has rotated out)"
ALL=$(ls "$B" | grep -E '\.[0-9]{8}-[0-9]{6}\.info$' | sed -E 's/^.*\.([0-9]{8}-[0-9]{6})\.info$/\1/' | sort -u)
NEW=$(awk -v a="$XAFTER" '$0 > a' <<< "$ALL"); echo "$NEW" | sed 's/^/  | stamp /'
ok "runs since 11/22" "$(grep -c . <<< "$NEW")" 3
ok "their days" "$(cut -c1-8 <<< "$NEW" | tr '\n' ' ' | sed 's/ $//')" "$XDAYS"
for s in $NEW; do case "$s" in ????????-13[0-5]*) echo "  $s at 13:00-13:59 UTC (the nightly): yes";; *) echo "  $s at 13:00-13:59 UTC (the nightly): NO"; bad=1;; esac; done
echo "--- 2. the last three runs in backup.log = those three (from the third-last 'Backing up' line to the end)"
NDB=$(grep -E '^Backing up [0-9]+ db' "$B/backup.log" | tail -1 | sed -E 's/^Backing up ([0-9]+) db.*/\1/')
echo "dbs per run (the last run's own line): $NDB"
for k in 3 2 1; do
  R=$(awk -v k="$k" '/^Backing up /{n++} {a[n]=a[n] $0 "\n"} END{printf "%s", a[n-k+1]}' "$B/backup.log")
  s=$(sed -n "$((4-k))p" <<< "$NEW")
  echo "  run $((4-k)) of 3 (stamp $s):"
  ok "    XX lines" "$(grep -c 'XX' <<< "$R")" 0
  ok "    OK lines (= dbs)" "$(grep -c -E '^  OK  ' <<< "$R")" "$NDB"
  ok "    its final line" "$(grep -v '^[[:space:]]*$' <<< "$R" | tail -1)" "All backups verified ok."
  ok "    bible.db line 'OK  bible.db: ok (delete), ...'" "$(grep -c -E '^  OK  bible\.db: ok \(delete\), ' <<< "$R")" 1
  ok "    check files written with this stamp (= dbs)" "$(ls "$B" | grep -c -E "\.$s\.info\$")" "$NDB"
done
S=$(head -c 40 "$B/last_success.txt" 2>&1 | tr -d '\n'); echo "last_success.txt: $S"
case "$S" in 2026-11-25T13:*|2026-11-25T14:*) echo "  success stamp from the 11/25 13:30 run: yes";; *) echo "  success stamp from the 11/25 13:30 run: NO"; bad=1;; esac
echo "--- 3. the bible.db copy of each: its check file"
for s in $NEW; do
  I="$B/bible.db.$s.info"
  if [ ! -s "$I" ]; then echo "  bible.db.$s.info: MISSING"; bad=1; continue; fi
  echo "  bible.db.$s:"; grep -E '^(when|journal_mode|quick_check|size_bytes):' "$I" | sed 's/^/    | /'
  ok "    quick_check" "$(grep -E '^quick_check: ' "$I" | sed 's/^quick_check: //')" ok
  ok "    journal_mode of live" "$(grep -E '^journal_mode: ' "$I" | sed 's/^journal_mode: //')" delete
  ok "    words" "$(cnt "$I" words)" "$XW"
  ok "    verses" "$(cnt "$I" verses)" "$XV"
  ok "    abp_surface" "$(cnt "$I" abp_surface)" "$XS"
done
echo "--- 4. the copies kept"
ls -l --time-style=+%Y-%m-%dT%H:%MZ "$B" | grep -E ' bible\.db\.' | sed 's/^/  | /'
ok "bible.db copies kept (bible.db keeps 3)" "$(ls "$B" | grep -E '^bible\.db\.[0-9]{8}-[0-9]{6}\.db(\.gz)?$' | sed -E 's/^bible\.db\.([0-9-]+)\.db(\.gz)?$/\1/' | sort -u | grep -c .)" 3
echo "--- 5. the rollback copy the three nightlies were for (printed only; nothing touched)"
ls -l --time-style=+%Y-%m-%dT%H:%MZ ~/bible-db/bible_pre_edition_upgrade_20261121.db 2>&1 | sed 's/^/  | /'
if [ "$bad" = 0 ]; then echo "NIGHTLIES RESULT: PASS - the 11/23, 11/24 (and 11/25) nightlies ran clean and copied live as it stood; paste the health task's 11/23 and 11/24 log lines from the PA Tasks tab with this"
else echo "NIGHTLIES RESULT: CHECK - a line above reads NO; nothing was changed; to the ruling chat as printed"; fi
)
