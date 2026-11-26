set +H
L=~/edition_upgrade_runs/rollback_removal_20261126.log
if [ -e "$L" ]; then echo "RBREMOVE RESULT: STOP - log already exists (already ran? kept as is): $L"; else
( set -uo pipefail
export TZ=UTC LC_ALL=C GIT_OPTIONAL_LOCKS=0
F=~/bible-db/bible_pre_edition_upgrade_20261121.db
XSHA=6cb558a6fa56aa91b381f80c604b470695288716facccadc8c30d02d7d8bf1e9
XSIZE=460283904
LIVE=~/bible-db/bible.db
B=~/db_backups
P4=~/edition_upgrade_runs/p4_live_tables_20261121/live_copy_20261121.db
echo "RBREMOVE - the rollback copy's removal (DESIGN 9.276, 9.277; JP's yes 11/25) - REMOVES ONE FILE: $F - nothing else written but this log - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
hm=$(date -u +%H%M); echo "UTC time $hm (STOP inside 1230-1430)"
if [ "$hm" -ge 1230 ] && [ "$hm" -le 1430 ]; then echo "RBREMOVE RESULT: STOP - inside the 12:30-14:30 UTC window; nothing removed"; exit 1; fi
echo "home in use before: $(cut -f1 <<< "$(du -sk ~ 2>/dev/null)") KB"
[ -f "$F" ] || { echo "RBREMOVE RESULT: STOP - no such file: $F; nothing removed"; exit 1; }
sz=$(stat -c %s "$F"); echo "size: $sz (expect $XSIZE)"
[ "$sz" = "$XSIZE" ] || { echo "RBREMOVE RESULT: STOP - not the recorded size; nothing removed"; exit 1; }
k=$(cut -d' ' -f1 <<< "$(sha256sum < "$F")"); echo "sha256: $k (expect $XSHA)"
[ "$k" = "$XSHA" ] || { echo "RBREMOVE RESULT: STOP - not the recorded file; nothing removed"; exit 1; }
for x in -journal -wal -shm; do echo "beside it: $(basename "$F")$x $([ -e "$F$x" ] && echo 'PRESENT (printed only; not removed)' || echo absent)"; done
echo "--- printed only, untouched by this block:"
stat -c '  live: %s bytes, last write %y' "$LIVE"
echo "  nightly copies:"; ls -l --time-style=+%Y-%m-%dT%H:%MZ "$B" | grep -E ' bible\.db\.' | sed 's/^/    | /'
lv0=$(stat -c '%s %Y' "$LIVE"); nb0=$(ls -l --time-style=+%s "$B" | sha256sum | cut -d' ' -f1)
if [ -e "$P4" ]; then stat -c "  P4's live copy: PRESENT, %s bytes, last write %y ($P4)" "$P4"; else echo "  P4's live copy: absent ($P4)"; fi
echo "=== the removal: one path, no wildcard ==="
rm -- ~/bible-db/bible_pre_edition_upgrade_20261121.db; rr=$?
echo "rm exit $rr (expect 0)"
[ -e "$F" ] && { echo "RBREMOVE RESULT: CHECK - the file is still there after rm; to the ruling chat"; exit 1; }
echo "the file is gone: yes"
lv1=$(stat -c '%s %Y' "$LIVE"); nb1=$(ls -l --time-style=+%s "$B" | sha256sum | cut -d' ' -f1)
echo "live size and last write before = after: $([ "$lv1" = "$lv0" ] && echo yes || echo 'NO (the site may have written; printed only)')"
echo "nightly copies folder listing before = after: $([ "$nb1" = "$nb0" ] && echo yes || echo NO)"
[ "$nb1" = "$nb0" ] || { echo "RBREMOVE RESULT: CHECK - the backup folder changed during the run; to the ruling chat"; exit 1; }
for x in -journal -wal -shm; do [ -e "$F$x" ] && echo "still beside where it was: $(basename "$F")$x (left as is)"; done
echo "home in use after: $(cut -f1 <<< "$(du -sk ~ 2>/dev/null)") KB"
echo "RBREMOVE RESULT: DONE - $(date -u +%FT%TZ) - the rollback copy removed (sha and size checked first); live and the nightly copies untouched"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
