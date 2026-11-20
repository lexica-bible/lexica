# CACHE57 tests - each case on a WSL test home made by mkhome57.sh + one TIPNR57 run (its log gives the window); block as written.
set -uo pipefail
T=/mnt/c/Users/JP/AppData/Local/Temp/claude/375bfdbef9aafd6e/4dc3eda8-b926-40ce-bd60-50e27a92e45e/scratchpad/t57
G=~/gatec57
mkdir -p $G
hd() { echo; echo "=============== $* ==============="; }
mk() { bash "$T/mkhome57.sh" "$1" > "$1.mk" 2>&1 || { cat "$1.mk"; exit 1; }; ( cd "$1" && HOME="$1" bash "$1/block.sh" ) > "$1.t57" 2>&1; grep -q "TIPNR57 RESULT: READ" "$1.t57" || { echo "TIPNR57 setup run not READ"; tail -3 "$1.t57"; exit 1; }; }
run() { ( cd "$1" && HOME="$1" bash "$T/cache57_block.sh" ) 2>&1 | grep -v '^$' ; }
win() { # TIPNR57 header time of the home's log, epoch
  date -d "$(grep -m1 '^GATE REF' "$1/edition_upgrade_runs/tipnr57_read_20261119.log" | grep -oE '[0-9]{4}-[0-9-]{5}T[0-9:]{8}Z$')" +%s; }
fp() { find "$1/bible-db" -name __pycache__ -type d | sort | xargs -r ls -la --time-style=+%s 2>/dev/null | sha256sum | cut -c1-16; }
echo "# CACHE57 tests ($(date -u +%FT%TZ)); block sha256 $(sha256sum < $T/cache57_block.sh | cut -d' ' -f1)"

hd "C1 planted: two cache folders; one file + the checkout folder timed INSIDE the run window, the rest before -> READ, WINDOW lines named"
H=$G/c1; mk $H; S0=$(win $H)
mkdir -p $H/bible-db/__pycache__ $H/bible-db/scripts/__pycache__
echo a > $H/bible-db/__pycache__/app.cpython-310.pyc; echo b > $H/bible-db/scripts/__pycache__/eu_step.cpython-310.pyc; echo c > $H/bible-db/zz_window.txt
touch -d @$((S0-7200)) $H/bible-db/__pycache__/app.cpython-310.pyc $H/bible-db/__pycache__ $H/bible-db/scripts
touch -d @$((S0+5)) $H/bible-db/scripts/__pycache__/eu_step.cpython-310.pyc $H/bible-db/zz_window.txt
touch -d @$((S0-7200)) $H/bible-db/scripts/__pycache__
touch -d @$((S0+10)) $H/bible-db
echo "pipeline fingerprint before the block (C6: must equal the block's 'fingerprint now'): $(fp $H)"
run $H

hd "C2 KNOWN POSITIVE for section (5): once the start listing is written, an outside job moves the checkout folder's time (the '..' line) and adds a cache file -> both lines in the diff"
H=$G/c2; mk $H; mkdir -p $H/bible-db/__pycache__; echo a > $H/bible-db/__pycache__/app.cpython-310.pyc
( F=$H/edition_upgrade_runs/tipnr57_cacheread_20261120/cache_folders.txt
  for i in $(seq 1 400); do [ -e "$F" ] && break; sleep 0.02; done
  echo z > $H/bible-db/__pycache__/late.cpython-310.pyc; touch -d @$(( $(date +%s) + 500 )) $H/bible-db ) & BG=$!
run $H | sed -n '/=== (5)/,$p'; wait $BG 2>/dev/null

hd "C3 built changed (one cell) -> guard FAIL -> FINDING"
H=$G/c3; mk $H
python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute(\"UPDATE words SET english='Aaronx' WHERE english='Aaron'\"); c.commit()" $H/bible-db/bible_edupg_test_built_20261102.db
run $H | grep -E "written table words|CHECK|built = HEADFIX2|RESULT|^exit="

hd "C4 re-paste on C1's home -> STOP, log exists"
run $G/c1 | tail -2

hd "C5 TIPNR57 log missing -> STOP"
H=$G/c5; mk $H; rm $H/edition_upgrade_runs/tipnr57_read_20261119.log; run $H | grep -E "RESULT|^exit="

hd "C7 one cache folder only (ls prints no folder header) -> the folder still named on its lines"
H=$G/c7; mk $H; mkdir -p $H/bible-db/tests/__pycache__; echo x > $H/bible-db/tests/__pycache__/t.pyc; S0=$(win $H); touch -d @$((S0+3)) $H/bible-db/tests/__pycache__/t.pyc
run $H | sed -n '/=== (1)/,/=== (2)/p'

hd "C8 no cache folder -> 0 folders, READ; no cache folder made by the block"
H=$G/c8; mk $H; run $H | grep -E "cache folders:|listing lines|RESULT|^exit="; echo "cache folders after: $(find $H/bible-db -name __pycache__ -type d | wc -l)"

hd "C9 the checkout's index file is not rewritten by the block (a tracked file touched so plain git status WOULD rewrite it)"
H=$G/c9; mk $H; touch $H/bible-db/README.md 2>/dev/null || touch $H/bible-db/app.py; sleep 1.1
i0=$(stat -c %Y.%s $H/bible-db/.git/index); run $H | grep -E "RESULT|^exit="; i1=$(stat -c %Y.%s $H/bible-db/.git/index)
echo "index before = after the block: $([ "$i0" = "$i1" ] && echo yes || echo NO) ($i0 / $i1)"
git -C $H/bible-db status --porcelain > /dev/null; i2=$(stat -c %Y.%s $H/bible-db/.git/index)
echo "known positive - plain git status afterwards rewrites it: $([ "$i2" != "$i1" ] && echo yes || echo NO) ($i2)"
