set +H
L=~/edition_upgrade_runs/split_removal_$(date -u +%Y%m%d).log
if [ -e "$L" ]; then echo "SPLITREMOVE RESULT: STOP - log already exists (already ran? kept as is): $L"; else
( set -uo pipefail
export TZ=UTC LC_ALL=C GIT_OPTIONAL_LOCKS=0
echo "SPLITREMOVE - removes the three superseded fill files (DESIGN 9.291): each sha checked first; fixed paths, no wildcard - PA HEAD $(git -C ~/bible-db log -1 --format=%h) - $(date -u +%FT%TZ)"
F1=~/bible-db/tests/fixtures/rebuild_trap/abp_surface_fill_20261126.tsv
R1=~/bible-db/tests/fixtures/rebuild_trap/restore_report_20261115.tsv
P1=~/abp_surface_prefill_20261115.db
X1=3cc35e7d9fcfdc5c7d47da25ba1ba3785cdde504868e3e64cfde8aab4308fe28   # the 11/26 frozen fill (DESIGN 9.272)
XR=e154d8d4991aa02d49380d473c22b511d7c5a7be4c7239873b0bfe19ebc4748a   # the 11/15 report (DESIGN 9.133)
XP=ea6c54c34a86539929bee354f4b3390d7aadbdba081f5010233381e0fd4e7273   # the 11/15 pre-fill table (DESIGN 9.128, 9.134)
h() { cut -d' ' -f1 <<< "$(sha256sum < "$1")"; }
t=$(date -u +%H%M); if [ "$((10#$t))" -ge 1130 ] && [ "$((10#$t))" -lt 1430 ]; then echo "SPLITREMOVE RESULT: STOP - too near the 13:30 UTC nightly (11:30-14:30); nothing removed"; exit 1; fi
# --- the new pinned set must be in place before anything old goes ---
for f in ~/bible-db/tests/fixtures/rebuild_trap/abp_surface_fill_20261127.tsv ~/bible-db/tests/fixtures/rebuild_trap/restore_report_20261127.tsv ~/abp_surface_prefill_20261127.db; do
  [ -s "$f" ] || { echo "SPLITREMOVE RESULT: STOP - the new pinned file is missing: $f; nothing removed"; exit 1; }
done
echo "the 11/27 frozen file, report and pre-fill table: present"
# --- every sha first; any miss is STOP and nothing is removed ---
for x in "$F1:$X1" "$R1:$XR" "$P1:$XP"; do
  f=${x%%:*}; want=${x##*:}
  [ -s "$f" ] || { echo "SPLITREMOVE RESULT: STOP - missing or empty: $f; nothing removed"; exit 1; }
  k=$(h "$f"); [ "$k" = "$want" ] || { echo "SPLITREMOVE RESULT: STOP - $f is not the pinned file ($k); nothing removed"; exit 1; }
  echo "  $f: $(stat -c %s "$f") bytes, sha256 = $want"
done
for x in "$F1.sha256:$X1" "$R1.sha256:$XR"; do
  f=${x%%:*}; want=${x##*:}
  [ -s "$f" ] && [ "$(cut -d' ' -f1 "$f")" = "$want" ] || { echo "SPLITREMOVE RESULT: STOP - $f is missing or does not name $want; nothing removed"; exit 1; }
  echo "  $f: names $want"
done
for x in -journal -wal -shm; do [ -e "$P1$x" ] && echo "  side file beside the pre-fill table (printed, not removed): $P1$x"; done
dk0=$(cut -f1 <<< "$(du -sk ~ 2>/dev/null)"); echo "home in use before: $dk0 KB"
# --- the removal: five fixed paths ---
rm -- ~/bible-db/tests/fixtures/rebuild_trap/abp_surface_fill_20261126.tsv ~/bible-db/tests/fixtures/rebuild_trap/abp_surface_fill_20261126.tsv.sha256 \
      ~/bible-db/tests/fixtures/rebuild_trap/restore_report_20261115.tsv ~/bible-db/tests/fixtures/rebuild_trap/restore_report_20261115.tsv.sha256 \
      ~/abp_surface_prefill_20261115.db; rr=$?
echo "rm exit $rr (expect 0)"
left=""; for f in "$F1" "$F1.sha256" "$R1" "$R1.sha256" "$P1"; do [ -e "$f" ] && left="$left $f"; done
echo "still there: ${left:- none}"
echo "fixture folder now:"; ls -la ~/bible-db/tests/fixtures/rebuild_trap | grep -v "^total"
echo "home in use after: $(cut -f1 <<< "$(du -sk ~ 2>/dev/null)") KB (before $dk0 KB)"
[ "$rr" = 0 ] && [ -z "$left" ] || { echo "SPLITREMOVE RESULT: STOP - not every file was removed (lines above)"; exit 1; }
echo "SPLITREMOVE RESULT: DONE - the 11/26 fill, the 11/15 report (each + .sha256) and the 11/15 pre-fill table removed"
) 2>&1 | tee "$L"; echo "exit=${PIPESTATUS[0]}"; fi
