set +H
( set -uo pipefail
export TZ=UTC LC_ALL=C GIT_OPTIONAL_LOCKS=0
B=~/db_backups
XNOT_BEFORE=202611221500                       # 15:00 UTC 11/22 - well after the 13:30 tasks finish
D=2026-11-22                                   # the first 13:30 UTC nightly after the swap (11/21 20:21Z)
XW=626309; XV=31237; XS=395014                 # the new live: words, verses, abp_surface (P7's read; DESIGN 9.235)
XOLD=395003                                    # abp_surface on the pre-swap live (the old floor) - the control
echo "P9 - the first 13:30 UTC nightly after the swap (DESIGN 9.235, 9.238) - READ-ONLY: reads files in ~/db_backups and git's HEAD; opens no database; runs no backup and no health check; writes no file"
NOW=$(date -u +%Y%m%d%H%M); echo "now UTC: $NOW"
if [ "$NOW" -lt "$XNOT_BEFORE" ]; then echo "P9 RESULT: STOP - too early; paste after 15:00 UTC on 11/22 (nothing read)"; exit 1; fi
echo "PA HEAD: $(git -C ~/bible-db rev-parse --short=8 HEAD 2>&1)"
bad=0
ok() { if [ "$2" = "$3" ]; then echo "$1: $2 - yes"; else echo "$1: $2 - NO (expected $3)"; bad=1; fi; }
cnt() { grep -E "^  $2: " "$1" | sed -E 's/^.*: //'; }
echo "--- 1. the success stamp (written only on a fully clean backup run)"
S=$(head -c 40 "$B/last_success.txt" 2>&1 | tr -d '\n'); echo "last_success.txt: $S"
case "$S" in "${D}T13:"*|"${D}T14:"*) echo "stamp from the 11/22 13:30 run: yes";; *) echo "stamp from the 11/22 13:30 run: NO"; bad=1;; esac
echo "--- 2. backup.log, its last run (from the last 'Backing up' line to the end)"
R=$(awk '/^Backing up /{b=""} {b=b $0 "\n"} END{printf "%s", b}' "$B/backup.log")
printf '%s\n' "$R" | sed 's/^/  | /'
ok "XX lines in the last run" "$(grep -c 'XX' <<< "$R")" 0
ok "the last run's final line" "$(grep -v '^[[:space:]]*$' <<< "$R" | tail -1)" "All backups verified ok."
ok "bible.db line 'OK  bible.db: ok (delete), ...' in the last run" "$(grep -c -E '^  OK  bible\.db: ok \(delete\), ' <<< "$R")" 1
echo "--- 3. the bible.db copies kept"
LL=$(ls -l --time-style=+%Y-%m-%dT%H:%MZ "$B"); grep -E ' bible\.db\.' <<< "$LL" | sed 's/^/  | /'
LN=$(ls "$B"); ST=$(grep -E '^bible\.db\.[0-9]{8}-[0-9]{6}\.db(\.gz)?$' <<< "$LN" | sed -E 's/^bible\.db\.([0-9-]+)\.db(\.gz)?$/\1/' | sort -u)
ok "bible.db copies kept (bible.db keeps 3)" "$(grep -c . <<< "$ST")" 3
NS=$(tail -1 <<< "$ST"); PS=$(tail -2 <<< "$ST" | head -1)
case "$NS" in 20261122-1[34]*) echo "newest copy $NS from the 11/22 13:30 run: yes";; *) echo "newest copy $NS from the 11/22 13:30 run: NO"; bad=1;; esac
if [ -f "$B/bible.db.$NS.db" ]; then echo "newest copy kept uncompressed: yes"; else echo "newest copy kept uncompressed: NO"; bad=1; fi
echo "--- 4. the newest copy's check file, bible.db.$NS.info (its head lines; it lists every table)"
I="$B/bible.db.$NS.info"
grep -E '^(db|when|journal_mode|quick_check|size_bytes):' "$I" | sed 's/^/  | /'
ok "  quick_check" "$(grep -E '^quick_check: ' "$I" | sed 's/^quick_check: //')" ok
ok "  journal_mode of live" "$(grep -E '^journal_mode: ' "$I" | sed 's/^journal_mode: //')" delete
ok "  words" "$(cnt "$I" words)" "$XW"
ok "  verses" "$(cnt "$I" verses)" "$XV"
ok "  abp_surface (the new edition)" "$(cnt "$I" abp_surface)" "$XS"
echo "  tables listed: $(grep -c '^  ' "$I")"
echo "--- 5. control: the copy before it, bible.db.$PS (pre-swap live) must read the OLD figure"
J="$B/bible.db.$PS.info"
grep -E '^when:' "$J" | sed 's/^/  | /'
if [[ "$PS" < "20261121-2021" ]]; then echo "  copy made before the swap (11/21 20:21Z): yes"; else echo "  copy made before the swap (11/21 20:21Z): NO"; bad=1; fi
ok "  abp_surface on the pre-swap copy" "$(cnt "$J" abp_surface)" "$XOLD"
if [ "$bad" = 0 ]; then echo "P9 BACKUP RESULT: PASS - the 11/22 nightly copied the new live and its check read ok"
else echo "P9 BACKUP RESULT: CHECK - a line above reads NO; nothing was changed; to the ruling chat as printed"; fi
)
