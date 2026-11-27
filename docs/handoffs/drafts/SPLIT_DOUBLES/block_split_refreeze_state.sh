set +H
R=~/edition_upgrade_runs/split_state_20261127
mkdir -p "$R"
A="$R/state_$(date -u +%H%M%S).log"
( set -uo pipefail
  D=~/edition_upgrade_runs/split_refreeze_20261127
  C=$D/refreeze.db
  echo "SPLIT REFREEZE STATE - read-only: lists, reads and prints; removes, restores and re-runs nothing - $(date -u +%FT%TZ) - host $(hostname)"
  [ -d "$D" ] || { echo "SPLIT STATE: the run folder $D is not there"; exit 1; }
  echo "=== 1 the run folder, every file with its size and last write (UTC) ==="
  TZ=UTC ls -la --time-style=+%FT%TZ "$D"
  echo "tgz beside it: $(TZ=UTC ls -la --time-style=+%FT%TZ ~/edition_upgrade_runs/split_refreeze_20261127.tgz 2>/dev/null || echo none)"
  echo "=== 2 the tee'd log(s): the last 25 lines of each ==="
  for f in "$D"/refreeze_*.log; do [ -e "$f" ] || { echo "(no refreeze_*.log)"; break; }; echo "--- $f ($(stat -c %s "$f") bytes)"; tail -n 25 "$f"; done
  echo "=== 3 step 6's own output ==="
  if [ -e "$D/restore_new.out" ]; then echo "restore_new.out: $(stat -c %s "$D/restore_new.out") bytes, $(wc -l < "$D/restore_new.out") lines; the last 60:"; tail -n 60 "$D/restore_new.out"
  else echo "restore_new.out: not there"; fi
  echo "restore_new.tsv (the restore's per-slot report): $( [ -e "$D/restore_new.tsv" ] && echo "$(stat -c %s "$D/restore_new.tsv") bytes, $(wc -l < "$D/restore_new.tsv") lines" || echo "not there")"
  echo "=== 4 the copy ==="
  for x in "$C" "$C-journal" "$C-wal" "$C-shm"; do
    if [ -e "$x" ]; then echo "$(basename "$x"): $(stat -c %s "$x") bytes, last write $(TZ=UTC date -r "$x" +%FT%TZ)"; else echo "$(basename "$x"): not there"; fi
  done
  if [ -e "$C-journal" ]; then echo "copy NOT opened: a -journal file is beside it (an unfinished write); it is left exactly as it is"
  elif [ -e "$C" ]; then
    python3 - "$C" <<'PY'
import sqlite3, sys
sys.path[0] == "" and sys.path.pop(0)
try:
    c = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True, timeout=5)
    print("copy abp_surface (opened read-only, 5 s wait): %d rows" % c.execute("SELECT count(*) FROM abp_surface").fetchone()[0])
    c.close()
except sqlite3.Error as e:
    print("copy not read: %s" % e)
PY
  else echo "copy: not there, nothing to open"; fi
  echo "=== 5 processes of this account on THIS console's server (a console on another server is not seen here) ==="
  PS="$(ps -u "$(id -un)" -o pid,ppid,lstart,etime,stat,args 2>/dev/null)"
  M="$(grep -E "python|split_|refreeze|restore_surface|snapshot_surface|build_abp|backfill_" <<< "$PS" | grep -v -E "grep -E")"
  head -n 1 <<< "$PS"
  if [ -n "$M" ]; then echo "$M"; else echo "(none matching)"; fi
  echo "=== 6 home in use ==="
  echo "home in use: $(cut -f1 <<< "$(du -sk ~ 2>/dev/null)") KB"
  echo "SPLIT STATE RESULT: READ - nothing changed"
) 2>&1 | tee "$A"; echo "exit=${PIPESTATUS[0]}"
