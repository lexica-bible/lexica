# Cache-guard scope test (11/20, CC; DESIGN 9.209 point 1). Scratch folder only; run with bash from any folder.
# OLD = TIPNR57's fingerprint (ls -la: each cache folder's '.' and '..' lines included).
# NEW = one line per cache folder (itself) and per entry inside it - type+permissions, owner, group, size, time
#       (to the fraction of a second the file system keeps), path - and nothing above the cache folders.
set -u
W=$(mktemp -d); cd "$W" || exit 1
mkdir -p bd/scripts/__pycache__ bd/__pycache__ && echo a > bd/__pycache__/a.pyc && echo b > bd/scripts/__pycache__/b.pyc
touch -d @1700000000 bd/__pycache__/a.pyc bd/scripts/__pycache__/b.pyc bd/__pycache__ bd/scripts/__pycache__ bd/scripts bd
fpN() { find bd \( -name __pycache__ -type d -o -path '*/__pycache__/*' \) -printf '%M %u %g %s %T@ %p\n' 2>/dev/null | sort | sha256sum | cut -c1-16; }
fpOld() { find bd -name __pycache__ -type d | sort | xargs -r ls -la --time-style=+%s 2>/dev/null | sha256sum | cut -c1-16; }
echo "what NEW lists here:"; find bd \( -name __pycache__ -type d -o -path '*/__pycache__/*' \) -printf '  %M %u %g %s %T@ %p\n' | sort
b=$(fpN); o=$(fpOld)
echo x > bd/notes.db-journal; rm bd/notes.db-journal
echo x > bd/scripts/other.txt; rm bd/scripts/other.txt
echo "N1 the folders the cache folders sit in change (a file made and removed in bd and in bd/scripts): NEW holds: $([ "$(fpN)" = "$b" ] && echo yes || echo NO) - OLD holds: $([ "$(fpOld)" = "$o" ] && echo yes || echo NO)"
b=$(fpN); echo t > bd/__pycache__/tmp.123; rm bd/__pycache__/tmp.123; echo "P0 a temp file made and removed INSIDE a cache folder (same listing after): NEW moves: $([ "$(fpN)" != "$b" ] && echo yes || echo NO)"
b=$(fpN); echo n > bd/scripts/__pycache__/new.pyc; echo "P1 new cache file: NEW moves: $([ "$(fpN)" != "$b" ] && echo yes || echo NO)"
b=$(fpN); rm bd/scripts/__pycache__/new.pyc; echo "P2 cache file removed: NEW moves: $([ "$(fpN)" != "$b" ] && echo yes || echo NO)"
b=$(fpN); echo ab > bd/__pycache__/a.pyc; echo "P3 cache file rewritten, same size, no wait: NEW moves: $([ "$(fpN)" != "$b" ] && echo yes || echo NO)"
b=$(fpN); chmod 600 bd/__pycache__/a.pyc; echo "P3b cache file permissions changed: NEW moves: $([ "$(fpN)" != "$b" ] && echo yes || echo NO)"
b=$(fpN); mkdir -p bd/tests/__pycache__; echo "P4 new empty cache folder: NEW moves: $([ "$(fpN)" != "$b" ] && echo yes || echo NO)"
b=$(fpN); rmdir bd/tests/__pycache__; rm -rf bd/__pycache__; echo "P5 one of two cache folders removed: NEW moves: $([ "$(fpN)" != "$b" ] && echo yes || echo NO)"
b=$(fpN); rm -rf bd/scripts/__pycache__; echo "P6 last cache folder removed: NEW moves: $([ "$(fpN)" != "$b" ] && echo yes || echo NO)"
b=$(fpN); mkdir -p bd/x/__pycache__; echo "P7 none, then one cache folder made: NEW moves: $([ "$(fpN)" != "$b" ] && echo yes || echo NO)"
cd /; rm -rf "$W"
