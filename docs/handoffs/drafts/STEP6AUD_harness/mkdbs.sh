set -euo pipefail
S6=/mnt/c/Users/JP/AppData/Local/Temp/claude/375bfdbef9aafd6e/2c800d5c-aa55-4d34-b144-23d87cfc5ca6/scratchpad/s6
rm -rf ~/gate6/dbs
time python3 "$S6/mkdbs.py" ~/gate6/base ~/gate5/home3/bible-db ~/gate6/dbs
ls -la ~/gate6/dbs
