# PA tidy-up, step 1 of 2 — READ-ONLY listing (TODO "Small fixes": untracked files + WAL crumbs).
# Changes nothing: only lists files. Paste into a PA bash console. Step 2 (a named removal
# block) is drafted from THIS output, never before.
cd ~/bible-db
[ "$(pwd)" = "$HOME/bible-db" ] || echo "NOT IN ~/bible-db - IGNORE EVERYTHING BELOW"
echo "=== A. untracked files git sees in ~/bible-db (top level + subfolders)"
git status --porcelain --untracked-files=all | grep '^??' | wc -l
echo "--- by folder (count, folder)"
git status --porcelain --untracked-files=all | grep '^??' | sed 's/^?? //' | awk -F/ '{print (NF>1 ? $1"/" : "(top)")}' | sort | uniq -c | sort -rn
echo "--- top-level untracked files: size, date, name"
git status --porcelain --untracked-files=all | grep '^??' | sed 's/^?? //' | grep -v / | while IFS= read -r f; do ls -ld --time-style=+%Y-%m-%d -- "$f" | awk '{printf "%10s %s ", $5, $6; for (i=7;i<=NF;i++) printf "%s ", $i; print ""}'; done
echo "=== B. -wal / -shm files anywhere under ~/bible-db: size, date, name, parent db present?"
find ~/bible-db -maxdepth 3 \( -name '*-wal' -o -name '*-shm' \) -printf '%s %TY-%Tm-%Td %p\n' | while read -r sz dt p; do base="${p%-wal}"; base="${base%-shm}"; if [ -e "$base" ]; then par=yes; else par=NO; fi; echo "$sz $dt $p parent=$par"; done
echo "=== C. is anything holding those -wal/-shm files open right now? (count of open handles)"
command -v lsof >/dev/null || echo "lsof not installed - C cannot answer"
find ~/bible-db -maxdepth 3 \( -name '*-wal' -o -name '*-shm' \) -print0 | xargs -0 -r lsof 2>/dev/null | tail -n +2 | wc -l
echo "PA TIDY LIST DONE"
