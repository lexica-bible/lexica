# TIPNR57 tests - every case on a fresh WSL test home (mkhome57.sh); the block run as written (only XCHK, XS, XP swapped).
set -uo pipefail
T=/mnt/c/Users/JP/AppData/Local/Temp/claude/375bfdbef9aafd6e/4dc3eda8-b926-40ce-bd60-50e27a92e45e/scratchpad/t57
G=~/gate57
L=edition_upgrade_runs/tipnr57_read_20261119.log
hd() { echo; echo "=============== $* ==============="; }
mk() { bash "$T/mkhome57.sh" "$1" "${2:-none}" > "$1.mk" 2>&1 || { cat "$1.mk"; exit 1; }; }
run() { ( cd "$1" && HOME="$1" bash "$1/block.sh" ) 2>&1 | grep -v '^$' ; }
echo "# TIPNR57 tests ($(date -u +%FT%TZ)); check program sha256 $(sha256sum < $T/tipnr57_check.py | cut -d' ' -f1); block sha256 (with __XCHK__ filled) below"
hd "T1 clean (the block as written)"; mk $G/h1; run $G/h1
hd "T2 re-paste on T1's home -> STOP, log exists"; run $G/h1 | tail -2
hd "T3 damaged upload (one line break added inside a string) -> STOP before any read"
mk $G/h3; python3 - "$G/h3/edition_upgrade_runs/tipnr57_check_20261119.py" <<'PY'
import sys
p = sys.argv[1]; t = open(p, encoding="utf-8").read()
t = t.replace("the figures and lists above go", "the figures and lists\nabove go", 1)
open(p, "w", encoding="utf-8", newline="\n").write(t)
PY
run $G/h3 | grep -E "check.py sha256|RESULT|exit="; echo "run folder holds: $(ls $G/h3/edition_upgrade_runs/tipnr57_read_20261119)"
hd "T4 KNOWN POSITIVE (tipnr): built's tipnr table one row short + one row changed (planted before the guard) -> FINDING"
mk $G/h4 tipnr; grep planted $G/h4.mk; run $G/h4 | sed -n '/=== (2)/,/=== (3)/p;/RESULT/p;/^exit=/p'
hd "T5 built changed after the guard (one name cell's English) -> CHECK FAIL, STOP, nothing read"
mk $G/h5; python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute(\"UPDATE words SET english='Aaronx' WHERE english='Aaron'\"); c.commit()" $G/h5/bible-db/bible_edupg_test_built_20261102.db
run $G/h5 | grep -E "written table words|CHECK|RESULT|exit="
hd "T6 pre_8b not the recorded copy (one cell changed) -> STOP at its sha"
mk $G/h6; python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute(\"UPDATE words SET english='Pharaohx' WHERE english='Pharaoh'\"); c.commit()" $G/h6/bible-db/bible_edupg_test_built_pre_8b_20261106.db
run $G/h6 | grep -E "sha256:|RESULT|exit="
hd "T7 tipnr/TIPNR.txt edited in the checkout -> STOP (git guard)"
mk $G/h7; echo "x" >> $G/h7/bible-db/tipnr/TIPNR.txt; run $G/h7 | grep -E "RESULT|exit="
hd "T8 the tail v3 log missing -> STOP"
mk $G/h8; rm $G/h8/edition_upgrade_runs/stageC_tail3_20261104.log; run $G/h8 | grep -E "RESULT|exit="
hd "T9 BSTD finish.out missing -> READ, the two last terms printed as one"
mk $G/h9; rm $G/h9/edition_upgrade_runs/step4_b_standard_20261117/finish.out; run $G/h9 | sed -n '/=== (6)/,$p'
hd "T10 the CONTROL fires on a broken matcher: the check program alone (block's launcher not used) on a scratch repo whose import_tipnr drops the 'of ' prefix strip -> CONTROL MISSED, STOP exit 2"
rm -rf $G/r10; cp -a $G/h1/bible-db $G/r10; sed -i 's/"land of ", "of the ", "of ", "to ",/"land of ", "of the ", "to ",/' $G/r10/scripts/import_tipnr.py
git -C $G/r10 diff --stat | tail -1
mkdir -p $G/r10out; ( cd /tmp && python3 $T/tipnr57_check.py S=$G/h1/bible-db/bible_edupg_test_20261101.db B=$G/h1/bible-db/bible_edupg_test_built_20261102.db P=$G/h1/bible-db/bible_edupg_test_built_pre_8b_20261106.db D=$G/r10out REPO=$G/r10 TL=$G/h1/edition_upgrade_runs/stageC_tail3_20261104.log OL=$G/h1/bible-db/finish_pnstar2.log BL=x XTIP=1a3b7d7df5cfa1e96eefa07dec92900bea278370c6788fadb5d036f3223b637c ); echo "exit $?"
hd "T11 size: the check program alone on the 626,309-row STEP6AUD test copies (~/gate6/dbs; no tipnr table there, 13 name cells) - time and memory"
mkdir -p $G/r11out; /usr/bin/time -f "elapsed %e s, max RSS %M KB" python3 $T/tipnr57_check.py S=$HOME/gate6/dbs/bible_edupg_test_20261101.db B=$HOME/gate6/dbs/bible_edupg_test_built_20261102.db P=$HOME/gate6/dbs/bible_edupg_test_20261101.db D=$G/r11out REPO=$G/h1/bible-db TL=$G/h1/edition_upgrade_runs/stageC_tail3_20261104.log OL=$G/h1/bible-db/finish_pnstar2.log BL=x XTIP=1a3b7d7df5cfa1e96eefa07dec92900bea278370c6788fadb5d036f3223b637c 2>&1 | grep -E "words .* name cells|TIPNR57 CHECK|elapsed"
hd "T1b T1's checkout after the run: no Python cache folder anywhere (expect none)"
find $G/h1/bible-db -name __pycache__ -type d | wc -l
hd "T12 KNOWN POSITIVE for the cache guard: the block's before/after lines around a plain import of scripts/tipnr_alias_variants WITHOUT the no-cache setting -> NO"
( cd $G/h1/bible-db && unset PYTHONDONTWRITEBYTECODE
  pc0=$(find $G/h1/bible-db -name __pycache__ -type d | sort | xargs -r ls -la --time-style=+%s 2>/dev/null | sha256sum | cut -c1-16)
  python3 -c "import sys; sys.path.insert(0, 'scripts'); import tipnr_alias_variants"
  pc1=$(find $G/h1/bible-db -name __pycache__ -type d | sort | xargs -r ls -la --time-style=+%s 2>/dev/null | sha256sum | cut -c1-16)
  echo "Python cache folders in the checkout before = after: $([ "$pc1" = "$pc0" ] && echo yes || echo NO) ($pc0 / $pc1)"; ls scripts/__pycache__ )
